"""
Walmart POC validation script — run this before building anything else.

Usage:
    python poc_walmart.py <walmart-product-url>

Example:
    python poc_walmart.py "https://www.walmart.com/ip/Yellowbird-Sriracha/XXXXXXXXX"

This script fetches the product page, parses __NEXT_DATA__ JSON, and prints
name + price. No database writes. If it succeeds, the Walmart scraper is viable.

Kill signal: if this fails with BlockDetectedError across multiple sessions,
pivot to ScraperAPI or Walmart's product API.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main():
    if len(sys.argv) != 2:
        print("Usage: python poc_walmart.py <walmart-product-url>")
        sys.exit(1)

    url = sys.argv[1]
    # Extract item ID from URL (last numeric segment)
    import re
    match = re.search(r"/(\d+)(?:\?|$)", url)
    retailer_id = match.group(1) if match else "unknown"

    from src.scrapers.walmart import WalmartScraper
    from src.scrapers.base import BlockDetectedError, ParseFailureError

    print(f"\nFetching: {url}")
    print("(This may take 5-10 seconds — rate limit + page load)\n")

    try:
        with WalmartScraper(rate_limit_secs=2.0) as scraper:
            product = scraper.fetch_product(
                listing_id=0,
                url=url,
                retailer_id=retailer_id,
            )
        print("SUCCESS — Walmart POC passed\n")
        print(f"  Product:  {product.product_name}")
        print(f"  Price:    ${product.current_price:.2f}")
        print(f"  On sale:  {product.has_promo_badge}")
        if product.sale_price:
            print(f"  Was:      ${product.sale_price:.2f}")
        print(f"  OOS:      {product.is_oos}")
        print(f"  Rating:   {product.star_rating} ({product.review_count} reviews)")
        print(f"  UPC:      {product.upc}")
        print(f"  Pack:     {product.pack_size_raw}")
        print()
    except BlockDetectedError as e:
        print(f"\nBLOCKED — {e}")
        print("Kill signal: if this happens repeatedly, evaluate ScraperAPI/proxy fallback.")
        sys.exit(2)
    except ParseFailureError as e:
        print(f"\nPARSE FAILURE — {e}")
        print("The page loaded but __NEXT_DATA__ structure was unexpected.")
        sys.exit(3)
    except Exception as e:
        print(f"\nERROR — {type(e).__name__}: {e}")
        sys.exit(4)


if __name__ == "__main__":
    main()
