"""
Google Shopping fallback for Walmart pricing.

Used when neither SCRAPERAPI_KEY nor camoufox is available (e.g. local dev
on Windows with Microsoft Store Python, where camoufox's Firefox binary is
sandboxed and Playwright subprocesses cannot reach it).

Strategy: search Google Shopping for the product + "walmart.com", parse the
price from the JSON-LD structured data or the shopping result cards. Returns
a minimal ScrapedProduct with price, name, and OOS signal only — star rating
and review count are not available from this source.

This is explicitly a demo/dev fallback. For production use SCRAPERAPI_KEY or
deploy to Linux where camoufox works correctly.
"""

from __future__ import annotations

import json
import logging
import re
import time
import random
from typing import Optional
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from src.scrapers.base import BlockDetectedError, ParseFailureError, ScrapedProduct

logger = logging.getLogger(__name__)

# User-agent that Google accepts from bots (honest identification)
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}

_PRICE_RE = re.compile(r"\$\s*([\d,]+\.?\d*)")


def fetch_walmart_price_via_google(
    product_name: str,
    retailer_id: str,
    walmart_url: str,
    rate_limit_secs: float = 3.0,
) -> ScrapedProduct:
    """Search Google Shopping for the Walmart listing and return scraped price.

    Raises:
        BlockDetectedError: Google returned a CAPTCHA or rate-limit page.
        ParseFailureError: Price could not be extracted from results.
    """
    time.sleep(rate_limit_secs + random.uniform(0.5, 1.5))

    query = f'site:walmart.com "{product_name}"'
    search_url = (
        f"https://www.google.com/search?q={quote_plus(query)}"
        f"&tbm=shop&gl=us&hl=en"
    )

    try:
        resp = requests.get(search_url, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise ParseFailureError(f"Google Shopping request failed: {exc}")

    html = resp.text
    if "detected unusual traffic" in html.lower() or "captcha" in html.lower():
        raise BlockDetectedError("Google Shopping rate-limited this IP — try again later")

    # Try JSON-LD first (cleanest source)
    price = _extract_from_json_ld(html)

    # Fall back to regex on the rendered page text
    if price is None:
        price = _extract_price_from_text(html)

    if price is None:
        # Last resort: try the Walmart URL directly with a simple requests call
        price = _extract_from_walmart_direct(walmart_url)

    if price is None:
        raise ParseFailureError(
            f"Could not extract price for {product_name!r} from Google Shopping or Walmart"
        )

    logger.info("Google Shopping → Walmart %s: %s @ $%.2f", retailer_id, product_name, price)
    return ScrapedProduct(
        retailer="walmart",
        retailer_id=retailer_id,
        product_name=product_name,
        current_price=price,
        is_oos=False,  # cannot reliably detect OOS from Google Shopping
    )


def _extract_from_json_ld(html: str) -> Optional[float]:
    """Parse JSON-LD structured data blocks for an Offer price."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        # Could be a single object or a list
        items = data if isinstance(data, list) else [data]
        for item in items:
            price = _dig_price(item)
            if price is not None:
                return price
    return None


def _dig_price(node) -> Optional[float]:
    """Recursively look for 'price' or 'offers' in a JSON-LD node."""
    if not isinstance(node, dict):
        return None
    # Direct price field
    if "price" in node:
        try:
            return float(str(node["price"]).replace(",", ""))
        except (ValueError, TypeError):
            pass
    # Nested offers object
    for key in ("offers", "Offer"):
        child = node.get(key)
        if isinstance(child, dict):
            result = _dig_price(child)
            if result is not None:
                return result
        elif isinstance(child, list):
            for item in child:
                result = _dig_price(item)
                if result is not None:
                    return result
    return None


def _extract_price_from_text(html: str) -> Optional[float]:
    """Regex scan the page text for the first dollar-price near 'walmart'."""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    # Find all prices and return the first one that looks plausible
    matches = _PRICE_RE.findall(text)
    for m in matches:
        try:
            price = float(m.replace(",", ""))
            if 0.50 < price < 500:  # sanity bounds for a sauce/condiment
                return price
        except ValueError:
            continue
    return None


def _extract_from_walmart_direct(url: str) -> Optional[float]:
    """Last resort: try a plain requests.get to Walmart (often works for a few hits)."""
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        # Try __NEXT_DATA__ inline JSON
        match = re.search(
            r'"currentPrice"\s*:\s*\{\s*"price"\s*:\s*([\d.]+)', resp.text
        )
        if match:
            return float(match.group(1))
        # Try plain price regex
        match = re.search(r'"price"\s*:\s*([\d.]+)', resp.text)
        if match:
            price = float(match.group(1))
            if 0.50 < price < 500:
                return price
    except Exception:
        pass
    return None
