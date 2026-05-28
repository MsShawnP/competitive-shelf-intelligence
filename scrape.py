"""
Competitive shelf intelligence scraper CLI.

Usage:
    python scrape.py                         # scrape all retailers
    python scrape.py --retailer walmart      # Walmart only
    python scrape.py --retailer amazon       # Amazon only
    python scrape.py --dry-run               # parse pages, no DB writes
    python scrape.py --delay 3.0             # override inter-request delay

Set SCRAPERAPI_KEY in .env for Walmart (required for production).
Set DATABASE_URL in .env for DB writes (required unless --dry-run).
"""

from __future__ import annotations

import logging
import time
from datetime import date
from pathlib import Path
from typing import Optional

import click
import yaml
from dotenv import load_dotenv

load_dotenv()

from src.db import get_conn
from src.scrapers.amazon import AmazonScraper
from src.scrapers.base import (
    BlockDetectedError,
    ParseFailureError,
    RobotsDisallowedError,
    ScrapedProduct,
)
from src.scrapers.entity_resolution import resolve_product
from src.scrapers.walmart import WalmartScraper
from src.utils import parse_weight_oz

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent / "config" / "products.yaml"


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

@click.command()
@click.option(
    "--retailer",
    type=click.Choice(["amazon", "walmart", "all"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Limit scraping to one retailer.",
)
@click.option(
    "--delay",
    type=float,
    default=2.0,
    show_default=True,
    help="Minimum seconds between requests.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Fetch and parse pages but do not write to the database.",
)
def main(retailer: str, delay: float, dry_run: bool) -> None:
    """Scrape competitor product pages and store price snapshots."""
    start = time.monotonic()
    products = _load_config(retailer)

    if not products:
        click.echo(f"No products configured for retailer={retailer}. Edit config/products.yaml.")
        return

    if dry_run:
        click.echo("[dry-run] No database writes will be made.")
        _run_dry(products, delay)
        return

    with get_conn() as conn:
        run_id = _start_scrape_run(conn, retailer)
        product_count, failure_count = 0, 0
        try:
            product_count, failure_count = _run_scrape(conn, run_id, products, delay)
            _finish_scrape_run(conn, run_id, product_count, failure_count)
        except Exception:
            logger.exception("Scrape run %d crashed; marking failed", run_id)
            _mark_run_failed(conn, run_id)
            raise

    elapsed = time.monotonic() - start
    click.echo(
        f"\nDone. {product_count} scraped, {failure_count} failed, "
        f"{elapsed:.1f}s elapsed."
    )


# ------------------------------------------------------------------
# Run logic
# ------------------------------------------------------------------

def _run_scrape(conn, run_id: int, products: list[dict], delay: float) -> tuple[int, int]:
    """Iterate products, scrape each, write to DB. Returns (product_count, failure_count)."""
    product_count = 0
    failure_count = 0

    walmart_products = [p for p in products if p["retailer"] == "walmart"]
    amazon_products = [p for p in products if p["retailer"] == "amazon"]

    try:
        if walmart_products:
            with WalmartScraper(rate_limit_secs=delay) as walmart:
                for entry in walmart_products:
                    ok = _scrape_one(conn, run_id, walmart, entry)
                    if ok is None:
                        raise BlockDetectedError("Walmart blocked — stopping run.")
                    product_count += ok
                    failure_count += 1 - ok

        if amazon_products:
            with AmazonScraper(rate_limit_secs=delay) as amazon:
                for entry in amazon_products:
                    ok = _scrape_one(conn, run_id, amazon, entry)
                    if ok is None:
                        raise BlockDetectedError("Amazon blocked — stopping run.")
                    product_count += ok
                    failure_count += 1 - ok

    except BlockDetectedError as exc:
        logger.error("BLOCK DETECTED — stopping run: %s", exc)
        _log_failure(conn, run_id, None, "", str(exc), entry.get("url", ""))

    return product_count, failure_count


def _scrape_one(conn, run_id: int, scraper, entry: dict) -> Optional[int]:
    """Scrape a single product entry and write snapshot. Returns 1 (ok), 0 (fail), None (block)."""
    url = entry["url"]
    retailer_id = str(entry["retailer_id"])
    name = entry["name"]
    brand_name = entry["brand"]

    if url.startswith("REPLACE_"):
        logger.warning("Skipping %s — URL not configured", name)
        return 0

    try:
        scraped = scraper.fetch_product(
            url=url,
            retailer_id=retailer_id,
        )
    except RobotsDisallowedError as exc:
        logger.warning("robots.txt disallows %s: %s", url, exc)
        _log_failure(conn, run_id, None, retailer_id, str(exc), url)
        return 0
    except BlockDetectedError:
        return None  # signal to stop the run
    except ParseFailureError as exc:
        logger.warning("Parse failure for %s: %s", url, exc)
        _log_failure(conn, run_id, None, retailer_id, str(exc), url)
        return 0

    # Resolve canonical product + listing
    brand_id = _get_or_create_brand(conn, brand_name)
    product_id, listing_id = resolve_product(scraped, brand_id, url, conn)

    # Backfill weight after the product row exists (UPDATE is a no-op if already set)
    pack_weight_oz = parse_weight_oz(scraped.pack_size_raw)
    if pack_weight_oz is not None:
        _update_product_weight(conn, scraped.upc, scraped.product_name, pack_weight_oz)

    # Check prior price for price_drop_promo signal (R3-b)
    price_drop_promo = _check_price_drop(conn, listing_id, scraped.current_price)

    # Insert snapshot (ON CONFLICT DO NOTHING deduplicates same-day runs, R9)
    _insert_snapshot(conn, listing_id, run_id, scraped, price_drop_promo)

    logger.info("OK  %-12s %s @ $%.2f", scraped.retailer.upper(), name, scraped.current_price or 0)
    return 1


def _run_dry(products: list[dict], delay: float) -> None:
    """Dry-run: fetch + parse only, no DB writes."""
    walmart_products = [p for p in products if p["retailer"] == "walmart"]
    amazon_products = [p for p in products if p["retailer"] == "amazon"]

    try:
        if walmart_products:
            with WalmartScraper(rate_limit_secs=delay) as walmart:
                for entry in walmart_products:
                    url = entry["url"]
                    if url.startswith("REPLACE_"):
                        click.echo(f"  [skip] {entry['name']} — URL not configured")
                        continue
                    try:
                        p = walmart.fetch_product(url, str(entry["retailer_id"]))
                        click.echo(f"  [ok]   {p.product_name} @ ${p.current_price:.2f}")
                    except (ParseFailureError, BlockDetectedError) as exc:
                        click.echo(f"  [fail] {entry['name']}: {exc}")

        if amazon_products:
            with AmazonScraper(rate_limit_secs=delay) as amazon:
                for entry in amazon_products:
                    url = entry["url"]
                    if url.startswith("REPLACE_"):
                        click.echo(f"  [skip] {entry['name']} — URL not configured")
                        continue
                    try:
                        p = amazon.fetch_product(url, str(entry["retailer_id"]))
                        click.echo(f"  [ok]   {p.product_name} @ ${p.current_price:.2f}")
                    except (ParseFailureError, BlockDetectedError) as exc:
                        click.echo(f"  [fail] {entry['name']}: {exc}")
    except BlockDetectedError as exc:
        click.echo(f"  [BLOCK] {exc} — stopping dry-run.")


# ------------------------------------------------------------------
# DB helpers
# ------------------------------------------------------------------

def _start_scrape_run(conn, retailer: str) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO scrape_runs (retailer) VALUES (%s) RETURNING id",
        (retailer,),
    )
    return cur.fetchone()[0]


def _finish_scrape_run(conn, run_id: int, product_count: int, failure_count: int) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        UPDATE scrape_runs
        SET status = 'complete', completed_at = now(),
            product_count = %s, failure_count = %s
        WHERE id = %s
        """,
        (product_count, failure_count, run_id),
    )


def _mark_run_failed(conn, run_id: int) -> None:
    cur = conn.cursor()
    cur.execute(
        "UPDATE scrape_runs SET status = 'failed', completed_at = now() WHERE id = %s",
        (run_id,),
    )


def _get_or_create_brand(conn, canonical_name: str) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO brands (canonical_name) VALUES (%s)
        ON CONFLICT (canonical_name) DO UPDATE SET canonical_name = EXCLUDED.canonical_name
        RETURNING id
        """,
        (canonical_name,),
    )
    return cur.fetchone()[0]


def _update_product_weight(conn, upc: Optional[str], canonical_name: str, weight_oz: float) -> None:
    cur = conn.cursor()
    if upc:
        cur.execute(
            "UPDATE products SET pack_weight_oz = %s WHERE upc = %s AND pack_weight_oz IS NULL",
            (weight_oz, upc),
        )
    else:
        cur.execute(
            "UPDATE products SET pack_weight_oz = %s WHERE canonical_name = %s AND pack_weight_oz IS NULL",
            (weight_oz, canonical_name),
        )


def _check_price_drop(conn, listing_id: int, current_price: Optional[float]) -> bool:
    """Return True if current price is strictly lower than the most recent snapshot price."""
    if current_price is None:
        return False
    cur = conn.cursor()
    cur.execute(
        """
        SELECT price_cents FROM price_snapshots
        WHERE listing_id = %s
        ORDER BY scraped_date DESC, scraped_at DESC
        LIMIT 1
        """,
        (listing_id,),
    )
    row = cur.fetchone()
    if not row:
        return False
    prior_price = row[0] / 100.0
    return current_price < prior_price


def _insert_snapshot(
    conn,
    listing_id: int,
    run_id: int,
    scraped: ScrapedProduct,
    price_drop_promo: bool,
) -> None:
    price_cents = round(scraped.current_price * 100) if scraped.current_price is not None else 0
    sale_price_cents = (
        round(scraped.sale_price * 100) if scraped.sale_price is not None else None
    )
    today = date.today()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO price_snapshots (
            listing_id, scrape_run_id, scraped_at, scraped_date,
            price_cents, sale_price_cents,
            has_promo_badge, sale_badge_text, price_drop_promo,
            is_oos, oos_signal,
            star_rating, review_count
        ) VALUES (
            %s, %s, now(), %s,
            %s, %s,
            %s, %s, %s,
            %s, %s,
            %s, %s
        )
        ON CONFLICT (listing_id, scraped_date) DO NOTHING
        """,
        (
            listing_id, run_id, today,
            price_cents, sale_price_cents,
            scraped.has_promo_badge, scraped.sale_badge_text, price_drop_promo,
            scraped.is_oos, scraped.oos_signal,
            scraped.star_rating, scraped.review_count,
        ),
    )


def _log_failure(
    conn,
    run_id: Optional[int],
    listing_id: Optional[int],
    retailer_id: str,
    error_message: str,
    url: str,
) -> None:
    try:
        cur = conn.cursor()
        retailer = None
        if url:
            if "amazon" in url:
                retailer = "amazon"
            elif "walmart" in url:
                retailer = "walmart"
        cur.execute(
            """
            INSERT INTO scrape_failures (scrape_run_id, listing_id, retailer, url, error_message)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (run_id, listing_id, retailer, url, error_message),
        )
    except Exception as log_exc:
        logger.error("Could not log failure to DB: %s", log_exc)


# ------------------------------------------------------------------
# Config loader
# ------------------------------------------------------------------

def _load_config(retailer_filter: str) -> list[dict]:
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    products = config.get("products", [])
    if retailer_filter != "all":
        products = [p for p in products if p["retailer"] == retailer_filter]
    return products


if __name__ == "__main__":
    main()
