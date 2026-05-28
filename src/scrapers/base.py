"""
Scraper base class, shared data types, and custom exceptions.

All scrapers inherit from BaseProductScraper which handles:
- Playwright browser lifecycle
- Rate limiting with random jitter (R5)
- robots.txt enforcement (R5)
- Block detection: 429, CAPTCHA, access-denied (R5)
- Stealth args to reduce bot fingerprinting
"""

from __future__ import annotations

import logging
import os
import random
import time
import urllib.request
import urllib.robotparser
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
from playwright_stealth import Stealth

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data type
# ---------------------------------------------------------------------------


@dataclass
class ScrapedProduct:
    """Normalized product data returned by each scraper.

    Prices are in dollars (float). The CLI converts to cents before DB insert.
    price_drop_promo is set by the CLI after comparing to the prior snapshot —
    scrapers only populate the badge-based has_promo_badge signal.
    """

    retailer: str                       # 'amazon' | 'walmart'
    retailer_id: str                    # ASIN or Walmart item ID
    product_name: str
    current_price: Optional[float] = None
    sale_price: Optional[float] = None  # present when on sale with known original
    has_promo_badge: bool = False
    sale_badge_text: Optional[str] = None
    price_drop_promo: bool = False      # set by CLI, not scraper
    is_oos: bool = False
    oos_signal: Optional[str] = None    # 'no_cart_button' | 'oos_text'
    star_rating: Optional[float] = None
    review_count: Optional[int] = None
    pack_size_raw: Optional[str] = None  # raw scraped string; weight parsed later
    upc: Optional[str] = None


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class BlockDetectedError(Exception):
    """Anti-bot detection fired (429, CAPTCHA, or access-denied redirect).

    On this exception the scraper run stops — do not retry in a tight loop (R5).
    """


class RobotsDisallowedError(Exception):
    """robots.txt disallows fetching the requested URL (R5)."""


class ParseFailureError(Exception):
    """Required fields could not be extracted from the page (R6).

    The CLI catches this, logs to scrape_failures, and continues to the next
    product. No partial row is inserted.
    """


# ---------------------------------------------------------------------------
# Base scraper
# ---------------------------------------------------------------------------


class BaseProductScraper:
    """Playwright-based product scraper with rate limiting and block detection.

    Use as a context manager::

        with WalmartScraper(rate_limit_secs=2.0) as scraper:
            product = scraper.fetch_product(listing_id, url, scrape_run_id)
    """

    # Identify the scraper honestly per src/CLAUDE.md scraping conventions
    USER_AGENT = (
        "Mozilla/5.0 (compatible; ShelfIntelligenceBot/1.0; "
        "+https://github.com/msshawnp/competitive-shelf-intelligence)"
    )

    # Strings whose presence in page content indicates CAPTCHA / access-denied
    _BLOCK_SIGNALS = [
        'id="captcha"',
        'class="captcha"',
        "robot or human",
        "prove you are human",
        "verify you are a human",
        "g-recaptcha",
        "access denied",
        "robot check",
        "automated access",
    ]

    def __init__(self, rate_limit_secs: float = 2.0, respect_robots: bool = True):
        self.rate_limit_secs = rate_limit_secs
        self.respect_robots = respect_robots
        self._last_request_time: float = 0.0
        self._robots_cache: dict[str, Optional[urllib.robotparser.RobotFileParser]] = {}
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    # ------------------------------------------------------------------
    # Context manager — browser lifecycle
    # ------------------------------------------------------------------

    def __enter__(self) -> "BaseProductScraper":
        proxy_url = os.getenv("PROXY_URL")
        if proxy_url and not proxy_url.startswith(("http://", "https://", "socks5://")):
            raise ValueError(f"PROXY_URL must start with http://, https://, or socks5://: {proxy_url!r}")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",   # required in containers (R24)
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-extensions",
            ],
        )
        self._context = self._browser.new_context(
            user_agent=self.USER_AGENT,
            proxy={"server": proxy_url} if proxy_url else None,
            viewport={"width": 1280, "height": 900},
            java_script_enabled=True,
        )
        # Apply stealth patches to every page in this context (playwright-stealth v2 API)
        Stealth().apply_stealth_sync(self._context)
        return self

    def __exit__(self, *args) -> None:
        if self._context:
            try:
                self._context.close()
            except Exception:
                pass
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Public helpers used by concrete scrapers
    # ------------------------------------------------------------------

    def check_robots(self, url: str) -> None:
        """Raise RobotsDisallowedError if robots.txt disallows this URL (R5).

        Results are cached per origin so repeated checks don't make network calls.
        On network failure reading robots.txt, the URL is allowed (fail-open).
        """
        if not self.respect_robots:
            return
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin not in self._robots_cache:
            rp = urllib.robotparser.RobotFileParser()
            try:
                robots_url = f"{origin}/robots.txt"
                with urllib.request.urlopen(robots_url, timeout=10) as resp:
                    content = resp.read().decode("utf-8", errors="ignore")
                rp.parse(content.splitlines())
                self._robots_cache[origin] = rp
            except Exception as exc:
                logger.warning("Could not fetch robots.txt for %s: %s", origin, exc)
                self._robots_cache[origin] = None  # fail-open
        rp = self._robots_cache[origin]
        if rp is not None and not rp.can_fetch(self.USER_AGENT, url):
            raise RobotsDisallowedError(f"robots.txt disallows: {url}")

    def fetch_page(self, url: str) -> Page:
        """Load a URL with stealth patches applied. Caller must close the page.

        Raises:
            BlockDetectedError: if the response indicates anti-bot detection.
        """
        self._rate_limit()
        page = self._context.new_page()
        response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)

        if self._detect_block(response, page):
            page.close()
            raise BlockDetectedError(f"Anti-bot block detected at {url}")

        self._slow_scroll(page)
        return page

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rate_limit(self) -> None:
        """Sleep until the minimum delay (+ random jitter) since last request."""
        elapsed = time.monotonic() - self._last_request_time
        jitter = random.uniform(0.0, 1.5)
        wait = max(0.0, self.rate_limit_secs + jitter - elapsed)
        if wait > 0.0:
            time.sleep(wait)
        self._last_request_time = time.monotonic()

    def _detect_block(self, response, page: Page) -> bool:
        """Return True when the response signals the scraper has been blocked."""
        if response is None:
            return False
        status = response.status
        if status in (429, 403):
            logger.warning("HTTP %s at %s — block detected", status, response.url)
            return True
        content = page.content().lower()
        if any(sig in content for sig in self._BLOCK_SIGNALS):
            logger.warning("CAPTCHA/access-denied content at %s", response.url)
            return True
        return False

    def _slow_scroll(self, page: Page) -> None:
        """Brief human-like scroll to reduce bot fingerprinting."""
        try:
            page.evaluate("window.scrollBy(0, Math.floor(Math.random() * 300 + 100))")
            time.sleep(random.uniform(0.2, 0.6))
        except Exception:
            pass  # non-fatal
