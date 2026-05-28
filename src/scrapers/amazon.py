"""
Amazon product scraper.

Primary strategy: CSS fallback chain, because Amazon has no stable JSON blob
equivalent to Walmart's __NEXT_DATA__. Multiple selectors are tried in order;
each is annotated with what it targets and when it applies.

Price selectors (tried in order):
  1. #priceblock_ourprice        — classic standard-price block (pre-2022 layout)
  2. #priceblock_dealprice        — classic deal/sale price block
  3. .a-price .a-offscreen        — new price display (post-2022, screen-reader text)
  4. .priceToPay .a-offscreen     — "Price to Pay" block used on some category pages

OOS signals (any True → is_oos):
  (a) oos_text: #availability span text contains "out of stock" or "currently unavailable"
  (b) no_cart_button: #add-to-cart-button absent from DOM
  (c) oos_element: #outOfStock element present

Promo signals (R3):
  (a) has_promo_badge: strikethrough price present (.a-text-strike alongside current price)
  (b) price_drop_promo: set by CLI after comparing to prior snapshot; not set here

ASIN: extracted from URL — no page parsing needed.
UPC: Amazon product details table (th contains "UPC", adjacent td).
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

from src.scrapers.base import (
    BaseProductScraper,
    BlockDetectedError,  # noqa: F401 — re-exported for callers
    ParseFailureError,
    RobotsDisallowedError,  # noqa: F401 — re-exported for callers
    ScrapedProduct,
)

logger = logging.getLogger(__name__)

_ASIN_RE = re.compile(r"/dp/([A-Z0-9]{10})")

# Ordered fallback chain for current price.
# Format: (selector, attribute_or_None, description)
# When attribute is None, use .get_text(). When "text", use .get_text(strip=True).
_PRICE_SELECTORS = [
    # Classic pre-2022 standard price block
    ("#priceblock_ourprice", None, "classic standard price"),
    # Classic pre-2022 deal/sale price (when a sale is active, this shows the sale price)
    ("#priceblock_dealprice", None, "classic deal price"),
    # Post-2022 price display — screen-reader span inside .a-price
    (".a-price .a-offscreen", None, "new-style a-price offscreen"),
    # Alternate current-price block seen on some grocery/grocery-like category pages
    (".priceToPay .a-offscreen", None, "priceToPay offscreen"),
]

_ADD_TO_CART_ID = "add-to-cart-button"


class AmazonScraper(BaseProductScraper):
    """Scrapes an Amazon product page using CSS selector fallback chains.

    Produces a ScrapedProduct from either a live Playwright page (via fetch_product)
    or a saved HTML string (via parse_html, used in fixture-based tests).
    """

    def fetch_product(self, listing_id: int, url: str, retailer_id: str) -> ScrapedProduct:
        """Fetch and parse a live Amazon product page via Playwright.

        Raises:
            RobotsDisallowedError: robots.txt disallows the URL.
            BlockDetectedError: Amazon blocked the request.
            ParseFailureError: Required fields missing (R6).
        """
        self.check_robots(url)
        page = self.fetch_page(url)
        try:
            html = page.content()
        finally:
            page.close()
        product = self.parse_html(html, url, retailer_id)
        logger.info(
            "Scraped Amazon listing %s: %s @ $%.2f",
            retailer_id,
            product.product_name,
            product.current_price or 0,
        )
        return product

    # ------------------------------------------------------------------
    # Parsing helpers (also called directly in tests via saved HTML)
    # ------------------------------------------------------------------

    def parse_html(self, html: str, url: str, retailer_id: str) -> ScrapedProduct:
        """Parse a saved or fetched HTML string. Used in fixture-based tests."""
        soup = BeautifulSoup(html, "html.parser")

        asin = self._extract_asin(url)
        product_name = self._extract_product_name(soup, url)
        current_price = self._extract_price(soup, url)
        sale_price = self._extract_sale_price(soup, current_price)
        has_promo_badge = sale_price is not None
        is_oos, oos_signal = self._detect_oos(soup)
        star_rating = self._extract_star_rating(soup)
        review_count = self._extract_review_count(soup)
        pack_size_raw = product_name  # weight parsed later from title
        upc = self._extract_upc(soup)

        return ScrapedProduct(
            retailer="amazon",
            retailer_id=retailer_id or asin or "",
            product_name=product_name,
            current_price=current_price,
            sale_price=sale_price,
            has_promo_badge=has_promo_badge,
            sale_badge_text=None,  # Amazon doesn't have a stable badge text field
            is_oos=is_oos,
            oos_signal=oos_signal,
            star_rating=star_rating,
            review_count=review_count,
            pack_size_raw=pack_size_raw,
            upc=upc,
        )

    # ------------------------------------------------------------------
    # Field extractors
    # ------------------------------------------------------------------

    def _extract_asin(self, url: str) -> Optional[str]:
        """Extract ASIN from URL — no page parsing needed."""
        m = _ASIN_RE.search(url)
        return m.group(1) if m else None

    def _extract_product_name(self, soup: BeautifulSoup, url: str) -> str:
        """Extract the product title from #productTitle."""
        el = soup.find(id="productTitle")
        if el:
            return el.get_text(strip=True)
        # Fallback: og:title meta tag
        meta = soup.find("meta", property="og:title")
        if meta and meta.get("content"):
            return meta["content"].strip()
        raise ParseFailureError(f"Product name not found on Amazon page: {url}")

    def _extract_price(self, soup: BeautifulSoup, url: str) -> float:
        """Try each price selector in order; raise ParseFailureError if all fail.

        Amazon rotates layouts across categories and over time. The fallback chain
        minimises single-selector fragility. Comment each selector when verified.
        """
        for selector, _attr, description in _PRICE_SELECTORS:
            el = soup.select_one(selector)
            if el:
                raw = el.get_text(strip=True)
                price = _parse_price_string(raw)
                if price is not None:
                    logger.debug("Price %.2f extracted via selector: %s", price, description)
                    return price

        raise ParseFailureError(
            f"No price selector matched on Amazon page: {url}. "
            f"Tried: {[s for s, _, _ in _PRICE_SELECTORS]}"
        )

    def _extract_sale_price(
        self,
        soup: BeautifulSoup,
        current_price: Optional[float],
    ) -> Optional[float]:
        """Detect sale pricing via a strikethrough 'was' price element.

        Amazon shows the original price in .a-text-strike when a sale is active.
        If present alongside the current price, the current price IS the sale price.
        We store it as sale_price (the lower value) and treat the struck-through
        price as the 'was' price — but we only return the lower current_price here;
        the CLI uses this to set has_promo_badge.
        """
        strike = soup.select_one(".a-text-strike")
        if not strike:
            return None
        # Confirm the struck-through value is a higher price (i.e., a real markdown)
        raw = strike.get_text(strip=True)
        was_price = _parse_price_string(raw)
        if was_price and current_price and was_price > current_price:
            return current_price  # current price IS the sale price
        return None

    def _detect_oos(self, soup: BeautifulSoup) -> tuple[bool, Optional[str]]:
        """Check three OOS signals; return (is_oos, signal_name)."""
        # Signal (a): availability span text
        avail = soup.find(id="availability")
        if avail:
            span = avail.find("span")
            if span:
                text = span.get_text(strip=True).lower()
                if "out of stock" in text or "currently unavailable" in text:
                    return True, "oos_text"

        # Signal (b): #outOfStock element present
        if soup.find(id="outOfStock"):
            return True, "oos_text"

        # Signal (c): add-to-cart button absent
        if not soup.find(id=_ADD_TO_CART_ID):
            # Only flag as OOS when availability text doesn't say "in stock"
            # to avoid false positives on gift cards / digital items with different UI
            if not (avail and "in stock" in (avail.get_text(strip=True) or "").lower()):
                return True, "no_cart_button"

        return False, None

    def _extract_star_rating(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract star rating from #acrPopover title attribute or data-hook span."""
        # Method 1: #acrPopover has a title like "4.5 out of 5 stars"
        popover = soup.find(id="acrPopover")
        if popover:
            title = popover.get("title", "")
            m = re.search(r"([\d.]+)\s+out of", title)
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    pass

        # Method 2: span with data-hook attribute (newer layout)
        hook = soup.find("span", attrs={"data-hook": "rating-out-of-stars"})
        if hook:
            m = re.search(r"([\d.]+)\s+out of", hook.get_text())
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    pass

        return None

    def _extract_review_count(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract total review count from #acrCustomerReviewText."""
        el = soup.find(id="acrCustomerReviewText")
        if el:
            text = el.get_text(strip=True)
            # Strip non-numeric: "1,234 ratings" → 1234
            digits = re.sub(r"[^\d]", "", text)
            if digits:
                return int(digits)
        return None

    def _extract_upc(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract UPC from the product details table.

        Amazon renders product details as a <table> with <th>/<td> pairs
        or a definition list. We look for a th containing "UPC" and read
        the adjacent td.
        """
        for th in soup.find_all("th"):
            if "upc" in th.get_text(strip=True).lower():
                td = th.find_next_sibling("td")
                if td:
                    return td.get_text(strip=True) or None
        return None


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _parse_price_string(raw: str) -> Optional[float]:
    """Convert '$8.97', '8.97', '$1,234.00' etc. to float."""
    cleaned = re.sub(r"[^\d.]", "", raw.replace(",", ""))
    # Guard against empty string or bare dot
    if not cleaned or cleaned == ".":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None
