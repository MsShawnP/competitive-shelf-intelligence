"""Tests for src/scrapers/walmart.py — fixture-based, no live network calls."""

from pathlib import Path

import pytest

from src.scrapers.base import ParseFailureError
from src.scrapers.walmart import WalmartScraper

FIXTURES = Path(__file__).parent.parent / "fixtures" / "walmart"


def _load(filename: str) -> str:
    return (FIXTURES / filename).read_text(encoding="utf-8")


@pytest.fixture
def scraper():
    return WalmartScraper(rate_limit_secs=0, respect_robots=False)


# ---------------------------------------------------------------------------
# Price extraction
# ---------------------------------------------------------------------------


def test_extracts_price_from_next_data_json(scraper):
    html = _load("product_in_stock.html")
    product = scraper.parse_html(html, "https://www.walmart.com/ip/test/111", "111")
    assert product.current_price == pytest.approx(8.97)


def test_extracts_product_name(scraper):
    html = _load("product_in_stock.html")
    product = scraper.parse_html(html, "https://www.walmart.com/ip/test/111", "111")
    assert "Yellowbird" in product.product_name
    assert "Sriracha" in product.product_name


def test_extracts_upc_from_next_data(scraper):
    html = _load("product_in_stock.html")
    product = scraper.parse_html(html, "https://www.walmart.com/ip/test/111", "111")
    assert product.upc == "853826007254"


def test_extracts_star_rating_and_review_count(scraper):
    html = _load("product_in_stock.html")
    product = scraper.parse_html(html, "https://www.walmart.com/ip/test/111", "111")
    assert product.star_rating == pytest.approx(4.6)
    assert product.review_count == 342


def test_sets_retailer_fields_correctly(scraper):
    html = _load("product_in_stock.html")
    product = scraper.parse_html(html, "https://www.walmart.com/ip/test/99999", "99999")
    assert product.retailer == "walmart"
    assert product.retailer_id == "99999"


# ---------------------------------------------------------------------------
# Promo detection (R3)
# ---------------------------------------------------------------------------


def test_no_promo_when_is_price_reduced_false(scraper):
    html = _load("product_in_stock.html")
    product = scraper.parse_html(html, "https://www.walmart.com/ip/test/111", "111")
    assert product.has_promo_badge is False
    assert product.sale_price is None
    assert product.sale_badge_text is None


def test_detects_promo_when_is_price_reduced_true(scraper):
    html = _load("product_on_sale.html")
    product = scraper.parse_html(html, "https://www.walmart.com/ip/test/222", "222")
    assert product.has_promo_badge is True


def test_extracts_was_price_when_on_sale(scraper):
    html = _load("product_on_sale.html")
    product = scraper.parse_html(html, "https://www.walmart.com/ip/test/222", "222")
    assert product.sale_price == pytest.approx(21.99)
    assert product.current_price == pytest.approx(17.88)


def test_extracts_sale_badge_text(scraper):
    html = _load("product_on_sale.html")
    product = scraper.parse_html(html, "https://www.walmart.com/ip/test/222", "222")
    assert product.sale_badge_text == "Save $4.11"


# ---------------------------------------------------------------------------
# OOS detection (R4)
# ---------------------------------------------------------------------------


def test_flags_oos_when_availability_status_out_of_stock(scraper):
    html = _load("product_out_of_stock.html")
    product = scraper.parse_html(html, "https://www.walmart.com/ip/test/333", "333")
    assert product.is_oos is True
    assert product.oos_signal == "oos_text"


def test_not_oos_when_in_stock_with_cart_button(scraper):
    html = _load("product_in_stock.html")
    product = scraper.parse_html(html, "https://www.walmart.com/ip/test/111", "111")
    assert product.is_oos is False
    assert product.oos_signal is None


def test_flags_oos_when_add_to_cart_button_absent(scraper):
    """Signal b: availabilityStatus=IN_STOCK but no cart button in DOM (R4)."""
    html = _load("product_no_cart_button.html")
    product = scraper.parse_html(html, "https://www.walmart.com/ip/test/444", "444")
    assert product.is_oos is True
    assert product.oos_signal == "no_cart_button"


# ---------------------------------------------------------------------------
# Parse failure (R6 / AE5)
# ---------------------------------------------------------------------------


def test_raises_parse_failure_when_next_data_missing(scraper):
    html = _load("product_missing_next_data.html")
    with pytest.raises(ParseFailureError):
        scraper.parse_html(html, "https://www.walmart.com/ip/test/999", "999")


def test_raises_parse_failure_when_price_field_absent(scraper):
    """No price in __NEXT_DATA__ → ParseFailureError (R6)."""
    html = """<html><script id="__NEXT_DATA__" type="application/json">
    {"props":{"pageProps":{"initialData":{"data":{"product":{
      "name": "Test Product",
      "priceInfo": {},
      "availabilityStatus": "IN_STOCK"
    }}}}}}
    </script></html>"""
    with pytest.raises(ParseFailureError, match="Price not found"):
        scraper.parse_html(html, "https://www.walmart.com/ip/test/998", "998")


def test_raises_parse_failure_when_product_name_absent(scraper):
    html = """<html><script id="__NEXT_DATA__" type="application/json">
    {"props":{"pageProps":{"initialData":{"data":{"product":{
      "priceInfo": {"currentPrice": {"price": 8.99}},
      "availabilityStatus": "IN_STOCK"
    }}}}}}
    </script></html>"""
    with pytest.raises(ParseFailureError):
        scraper.parse_html(html, "https://www.walmart.com/ip/test/997", "997")


# ---------------------------------------------------------------------------
# price_drop_promo is set by CLI, not scraper
# ---------------------------------------------------------------------------


def test_price_drop_promo_is_always_false_from_scraper(scraper):
    """price_drop_promo is set by the CLI after comparing to prior snapshot."""
    html = _load("product_in_stock.html")
    product = scraper.parse_html(html, "https://www.walmart.com/ip/test/111", "111")
    assert product.price_drop_promo is False
