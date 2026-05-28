"""
Walmart POC attempt 2 — native Chromium user-agent + full stealth.

The first attempt used a custom "ShelfIntelligenceBot" user-agent which
Walmart's fingerprinter catches immediately. This attempt uses the
browser's own default user-agent and applies stealth at the page level
as well as the context level.
"""

import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def main():
    url = sys.argv[1] if len(sys.argv) > 1 else (
        "https://www.walmart.com/ip/Yellowbird-Habanero-Hot-Sauce-6-7-oz/2005237659"
    )

    import re
    import json
    import time
    import random
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth

    print(f"\nFetching: {url}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-first-run",
                "--disable-extensions",
                "--disable-default-apps",
            ],
        )
        # No custom user_agent — use Chromium's default to pass fingerprinting
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            java_script_enabled=True,
            locale="en-US",
            timezone_id="America/New_York",
        )
        Stealth().apply_stealth_sync(context)

        page = context.new_page()

        # Also apply at page level for belt-and-suspenders
        Stealth().apply_stealth_sync(page)

        print("Browser UA:", page.evaluate("() => navigator.userAgent"))
        print("Webdriver:", page.evaluate("() => navigator.webdriver"))

        response = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        print(f"Status: {response.status}  Final URL: {page.url[:80]}")

        if "blocked" in page.url or response.status in (403, 429):
            print("\nBLOCKED — Walmart detected the headless browser.")
            browser.close()
            sys.exit(2)

        # Extract __NEXT_DATA__
        content = page.evaluate(
            "() => document.querySelector('script#__NEXT_DATA__')?.textContent || ''"
        )
        if not content:
            print("\nPAGE LOADED but no __NEXT_DATA__ found.")
            print("Page title:", page.title())
            browser.close()
            sys.exit(3)

        data = json.loads(content)

        # Navigate to product node
        def find_product(d, depth=0):
            if depth > 6 or not isinstance(d, dict):
                return None
            if "priceInfo" in d and ("name" in d or "productName" in d):
                return d
            for v in d.values():
                r = find_product(v, depth + 1)
                if r:
                    return r
            return None

        product = find_product(data)
        if not product:
            print("\n__NEXT_DATA__ found but product node not located.")
            print("Top-level keys:", list(data.get("props", {}).get("pageProps", {}).keys()))
            browser.close()
            sys.exit(4)

        name = product.get("name") or product.get("productName", "?")
        price = (product.get("priceInfo") or {}).get("currentPrice", {}).get("price")

        print(f"\nSUCCESS\n  Product: {name}\n  Price:   ${price}")
        browser.close()


if __name__ == "__main__":
    main()
