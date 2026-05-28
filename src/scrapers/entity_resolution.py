"""Entity resolution: maps a scraped product to a canonical product + listing row.

Three-tier lookup (stops at first match):

  Tier 1 — UPC exact match
    Query products.upc = scraped.upc (when UPC is not None).
    If product found, check for an existing retailer_listings row.
    Return existing listing_id, or insert a new one.

  Tier 2 — Manual canonical map
    Query canonical_product_map for the scraped retailer_id.
    Returns the mapped canonical_product_id.

  Tier 3 — New product
    No match found. Insert a new products row and a new retailer_listings row.
    Conservative by design: the operator cleans up cross-retailer links via
    canonical_product_map. Fuzzy matching deferred to v2 (R11).
"""

from __future__ import annotations

import logging
from typing import Optional

from psycopg2 import sql
from src.scrapers.base import ScrapedProduct

logger = logging.getLogger(__name__)


def resolve_product(
    scraped: ScrapedProduct,
    brand_id: int,
    product_url: str,
    conn,
) -> tuple[int, int]:
    """Map a scraped product to (product_id, listing_id), creating rows as needed.

    Args:
        scraped:     The ScrapedProduct returned by a scraper.
        brand_id:    The brands.id for this product's brand.
        product_url: The canonical URL for the retailer listing.
        conn:        An active psycopg2 connection (autocommit=True).

    Returns:
        (product_id, listing_id) — both are existing or newly inserted row IDs.
    """
    cur = conn.cursor()

    # Tier 1: UPC exact match
    if scraped.upc:
        result = _resolve_by_upc(cur, scraped, brand_id, product_url)
        if result:
            return result

    # Tier 2: manual canonical map lookup by retailer_id
    result = _resolve_by_canonical_map(cur, scraped, product_url)
    if result:
        return result

    # Tier 3: create new canonical product + listing
    return _create_new_product(cur, scraped, brand_id, product_url)


# ------------------------------------------------------------------
# Tier implementations
# ------------------------------------------------------------------

def _resolve_by_upc(
    cur,
    scraped: ScrapedProduct,
    brand_id: int,
    product_url: str,
) -> Optional[tuple[int, int]]:
    """Return (product_id, listing_id) if UPC matches an existing product."""
    cur.execute("SELECT id FROM products WHERE upc = %s LIMIT 1", (scraped.upc,))
    row = cur.fetchone()
    if not row:
        return None

    product_id = row[0]
    logger.debug("UPC match: product_id=%d for UPC %s", product_id, scraped.upc)

    listing_id = _get_or_create_listing(cur, product_id, scraped, product_url)
    return product_id, listing_id


def _resolve_by_canonical_map(
    cur,
    scraped: ScrapedProduct,
    product_url: str,
) -> Optional[tuple[int, int]]:
    """Return (product_id, listing_id) if retailer_id appears in canonical_product_map."""
    # Find an existing retailer_listings row for this retailer_id, then check
    # whether it appears in the canonical_product_map as either amazon or walmart side.
    cur.execute(
        """
        SELECT rl.product_id, rl.id AS listing_id
        FROM retailer_listings rl
        WHERE rl.retailer = %s AND rl.retailer_id = %s
        LIMIT 1
        """,
        (scraped.retailer, scraped.retailer_id),
    )
    existing = cur.fetchone()
    if existing:
        product_id, listing_id = existing
        _touch_listing(cur, listing_id)
        logger.debug(
            "Canonical map hit: retailer=%s id=%s → product_id=%d listing_id=%d",
            scraped.retailer, scraped.retailer_id, product_id, listing_id,
        )
        return product_id, listing_id

    # Check canonical_product_map directly for cross-retailer links
    col = "walmart_listing_id" if scraped.retailer == "walmart" else "amazon_listing_id"
    cur.execute(
        sql.SQL("""
        SELECT cpm.canonical_product_id
        FROM canonical_product_map cpm
        JOIN retailer_listings rl ON rl.id = cpm.{col}
        WHERE rl.retailer = %s AND rl.retailer_id = %s
        LIMIT 1
        """).format(col=sql.Identifier(col)),
        (scraped.retailer, scraped.retailer_id),
    )
    row = cur.fetchone()
    if not row:
        return None

    product_id = row[0]
    listing_id = _get_or_create_listing(cur, product_id, scraped, product_url)
    return product_id, listing_id


def _create_new_product(
    cur,
    scraped: ScrapedProduct,
    brand_id: int,
    product_url: str,
) -> tuple[int, int]:
    """Insert a new products row and a new retailer_listings row."""
    cur.execute(
        """
        INSERT INTO products (brand_id, canonical_name, pack_size_raw, upc)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (brand_id, canonical_name) DO UPDATE
            SET pack_size_raw = EXCLUDED.pack_size_raw,
                upc = COALESCE(products.upc, EXCLUDED.upc)
        RETURNING id
        """,
        (brand_id, scraped.product_name, scraped.pack_size_raw, scraped.upc or None),
    )
    product_id = cur.fetchone()[0]

    listing_id = _get_or_create_listing(cur, product_id, scraped, product_url)
    logger.debug(
        "New product created: product_id=%d listing_id=%d name=%r",
        product_id, listing_id, scraped.product_name,
    )
    return product_id, listing_id


# ------------------------------------------------------------------
# Shared helpers
# ------------------------------------------------------------------

def _get_or_create_listing(
    cur,
    product_id: int,
    scraped: ScrapedProduct,
    product_url: str,
) -> int:
    """Return existing listing_id for (retailer, retailer_id), or insert a new one."""
    cur.execute(
        """
        INSERT INTO retailer_listings (product_id, retailer, retailer_id, product_url)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (retailer, retailer_id) DO UPDATE
            SET last_seen_at = now(),
                product_url  = EXCLUDED.product_url
        RETURNING id
        """,
        (product_id, scraped.retailer, scraped.retailer_id, product_url),
    )
    return cur.fetchone()[0]


def _touch_listing(cur, listing_id: int) -> None:
    """Update last_seen_at on an existing listing."""
    cur.execute(
        "UPDATE retailer_listings SET last_seen_at = now() WHERE id = %s",
        (listing_id,),
    )
