"""
Load synthetic Cinderhaven brand data into Postgres.

Run AFTER the first real scrape so real category pricing exists to compute
the median. Idempotent: safe to run multiple times.

Usage:
    python scripts/load_synthetic.py
    python scripts/load_synthetic.py --dry-run   # preview without writing
    python scripts/load_synthetic.py --days 60   # extend history window
"""

from __future__ import annotations

import logging
import random
import statistics
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import click
from dotenv import load_dotenv

load_dotenv()

from src.db import get_conn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Cinderhaven SKUs to seed (pack_size_raw used for weight parsing)
_CINDERHAVEN_SKUS = [
    {"name": "Cinderhaven Original Hot Sauce 8 oz",  "pack_size_raw": "Cinderhaven Original Hot Sauce 8 oz",  "weight_oz": 8.0,  "retailer_id_walmart": "CW001", "retailer_id_amazon": "CB001", "asin": "B0CINDER01"},
    {"name": "Cinderhaven Smoked Jalapeño Sauce 12 oz", "pack_size_raw": "Cinderhaven Smoked Jalapeño Sauce 12 oz", "weight_oz": 12.0, "retailer_id_walmart": "CW002", "retailer_id_amazon": "CB002", "asin": "B0CINDER02"},
    {"name": "Cinderhaven Roasted Habanero Sauce 5 oz",  "pack_size_raw": "Cinderhaven Roasted Habanero Sauce 5 oz",  "weight_oz": 5.0,  "retailer_id_walmart": "CW003", "retailer_id_amazon": "CB003", "asin": "B0CINDER03"},
    {"name": "Cinderhaven Chipotle Blend 10 oz",         "pack_size_raw": "Cinderhaven Chipotle Blend 10 oz",         "weight_oz": 10.0, "retailer_id_walmart": "CW004", "retailer_id_amazon": "CB004", "asin": "B0CINDER04"},
    {"name": "Cinderhaven Ghost Pepper Reserve 6 oz",    "pack_size_raw": "Cinderhaven Ghost Pepper Reserve 6 oz",    "weight_oz": 6.0,  "retailer_id_walmart": "CW005", "retailer_id_amazon": "CB005", "asin": "B0CINDER05"},
]

_SYNTHETIC_BRAND = "Cinderhaven"


@click.command()
@click.option("--dry-run", is_flag=True, default=False, help="Preview without writing to DB.")
@click.option("--days", default=90, show_default=True, help="Number of history days to generate.")
def main(dry_run: bool, days: int) -> None:
    """Seed Cinderhaven synthetic data at the real category price median."""
    with get_conn() as conn:
        median_price_per_oz = _compute_category_median(conn)

    if median_price_per_oz is None:
        click.echo(
            "No competitor price data found. Run python scrape.py first, then re-run this script."
        )
        return

    click.echo(f"Category median price/oz: ${median_price_per_oz:.4f}")

    if dry_run:
        click.echo("[dry-run] Would insert:")
        for sku in _CINDERHAVEN_SKUS:
            price = round(median_price_per_oz * sku["weight_oz"], 2)
            click.echo(f"  {sku['name']}  @ ${price:.2f} ({days} days history)")
        return

    with get_conn() as conn:
        brand_id = _upsert_brand(conn)
        for sku in _CINDERHAVEN_SKUS:
            product_id = _upsert_product(conn, brand_id, sku, median_price_per_oz)
            for retailer, retailer_id, url_prefix in [
                ("walmart", sku["retailer_id_walmart"], "https://www.walmart.com/ip/cinderhaven/"),
                ("amazon",  sku["asin"],                "https://www.amazon.com/dp/"),
            ]:
                listing_id = _upsert_listing(conn, product_id, retailer, retailer_id, url_prefix + retailer_id)
                price_cents = round(median_price_per_oz * sku["weight_oz"] * 100)
                _insert_history(conn, listing_id, price_cents, days)
                logger.info("Loaded %s (%s) — %d days history", sku["name"], retailer, days)

    click.echo(f"Done. {len(_CINDERHAVEN_SKUS)} SKUs × 2 retailers × {days} days inserted.")


# ------------------------------------------------------------------
# DB operations
# ------------------------------------------------------------------

def _compute_category_median(conn) -> Optional[float]:
    """Compute median price_per_oz across all non-synthetic competitor snapshots."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT price_cents::float / p.pack_weight_oz / 100.0 AS ppo
        FROM price_snapshots ps
        JOIN retailer_listings rl ON rl.id = ps.listing_id
        JOIN products p ON p.id = rl.product_id
        JOIN brands b ON b.id = p.brand_id
        WHERE b.canonical_name != %s
          AND p.pack_weight_oz IS NOT NULL
          AND p.pack_weight_oz > 0
          AND rl.retailer != 'synthetic'
        """,
        (_SYNTHETIC_BRAND,),
    )
    rows = cur.fetchall()
    if not rows:
        return None
    values = [r[0] for r in rows if r[0] is not None]
    return statistics.median(values) if values else None


def _upsert_brand(conn) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO brands (canonical_name) VALUES (%s)
        ON CONFLICT (canonical_name) DO UPDATE SET canonical_name = EXCLUDED.canonical_name
        RETURNING id
        """,
        (_SYNTHETIC_BRAND,),
    )
    return cur.fetchone()[0]


def _upsert_product(conn, brand_id: int, sku: dict, median_price_per_oz: float) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO products (brand_id, canonical_name, pack_size_raw, pack_weight_oz)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (brand_id, canonical_name)
            DO UPDATE SET pack_weight_oz = EXCLUDED.pack_weight_oz
        RETURNING id
        """,
        (brand_id, sku["name"], sku["pack_size_raw"], sku["weight_oz"]),
    )
    return cur.fetchone()[0]


def _upsert_listing(conn, product_id: int, retailer: str, retailer_id: str, url: str) -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO retailer_listings (product_id, retailer, retailer_id, product_url)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (retailer, retailer_id)
            DO UPDATE SET last_seen_at = now()
        RETURNING id
        """,
        (product_id, retailer, retailer_id, url),
    )
    return cur.fetchone()[0]


def _insert_history(conn, listing_id: int, base_price_cents: int, days: int) -> None:
    """Insert one snapshot per day for the last `days` days.

    Sprinkles in a plausible number of OOS days (3–5 per 90 days) and promo
    events (1–2 per 90 days) spread across the history. Not pre-engineered
    to position Cinderhaven favorably — just creates realistic-looking history.
    """
    today = date.today()
    random.seed(listing_id)  # deterministic so reruns produce same history

    oos_count = max(2, round(days * 4 / 90))
    promo_count = max(2, round(days * 4 / 90))

    all_days = [today - timedelta(days=i) for i in range(days)]
    oos_days = set(random.sample(all_days, min(oos_count, len(all_days))))
    promo_days = set(random.sample(
        [d for d in all_days if d not in oos_days],
        min(promo_count, len(all_days) - len(oos_days)),
    ))
    promo_list = sorted(promo_days)
    badge_promos = set(promo_list[: len(promo_list) * 3 // 5])
    price_drop_promos = promo_days - badge_promos

    cur = conn.cursor()
    for day in reversed(all_days):  # oldest first
        is_oos = day in oos_days
        is_promo = day in promo_days
        has_badge = day in badge_promos
        is_price_drop = day in price_drop_promos
        price = base_price_cents
        sale_price = round(base_price_cents * 0.85) if is_promo else None

        cur.execute(
            """
            INSERT INTO price_snapshots (
                listing_id, scraped_at, scraped_date,
                price_cents, sale_price_cents,
                has_promo_badge, price_drop_promo,
                is_oos, oos_signal,
                star_rating, review_count
            ) VALUES (
                %s,
                %s AT TIME ZONE 'UTC',
                %s,
                %s, %s,
                %s, %s,
                %s, %s,
                %s, %s
            )
            ON CONFLICT (listing_id, scraped_date) DO NOTHING
            """,
            (
                listing_id,
                datetime.combine(day, datetime.min.time()),
                day,
                price, sale_price,
                has_badge, is_price_drop,
                is_oos, "oos_text" if is_oos else None,
                round(random.uniform(4.1, 4.8), 1),
                random.randint(50, 500),
            ),
        )


if __name__ == "__main__":
    main()
