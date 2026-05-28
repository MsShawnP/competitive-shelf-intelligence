---
date: 2026-05-28
topic: competitive-shelf-intelligence
---

# Competitive Shelf Intelligence — Requirements

## Summary

A Dash monitoring dashboard — five tabs, deployed on Fly.io — that scrapes real artisan sauce/condiment competitors from Amazon and Walmart, stores snapshots in standalone Postgres, and surfaces price positioning, promo activity, OOS events, assortment changes, and review trends alongside synthetic Cinderhaven brand data. v1 is manual scraping; the story is whatever the real data shows.

---

## Problem Frame

Specialty food brands at $5M–$20M can't justify $50K–$200K/year for syndicated data (IRI/Nielsen/SPINS). Their current alternative is manual: walking store aisles once a month, or typing competitor names into Walmart.com by hand. The result is no historical data, no trend lines, no alerts, and competitive intel that only happens when someone has time.

The information asymmetry is structural. The retailer's category manager has real-time POS, pricing, and assortment data. The brand has anecdotes and a browser tab. Every pricing decision, every promo timing call, every category review preparation happens without competitive context.

This project makes systematic, automated competitive visibility achievable without a syndicated data budget.

---

## Actors

- A1. **Operator (Shawn)** — runs scrapers manually, manages Postgres, deploys to Fly.io
- A2. **Dashboard viewer (prospect/client)** — opens the Fly.io URL, browses the five tabs to see competitive intelligence for the artisan sauce/condiment category
- A3. **Amazon.com / Walmart.com** — the systems being scraped; publicly visible product pages only

---

## Key Flows

- F1. **Manual scrape run**
  - **Trigger:** Operator runs the scraper CLI command
  - **Actors:** A1, A3
  - **Steps:** Operator executes scrape command with optional retailer flag → scraper loads competitor URL list → fetches each product page (rate-limited) → parses price, promo signals, OOS signals, rating, review count, pack size → inserts snapshot rows (deduped by product × retailer × date) → logs failures for any pages that couldn't be parsed → records scrape-run timestamp in Postgres
  - **Outcome:** Fresh price snapshots available in Postgres; dashboard reflects new data on next page load
  - **Covered by:** R1, R2, R4, R5, R6, R7, R8, R9, R10

- F2. **Dashboard view**
  - **Trigger:** Viewer opens the Fly.io URL
  - **Actors:** A2
  - **Steps:** Viewer lands on Price Positioning tab (default) → sees horizontal price-per-oz chart with all brands, Cinderhaven highlighted → clicks other tabs to explore promo calendar, OOS history, assortment changes, review trends → optionally filters by date range → reads "Last scraped" timestamp on each tab
  - **Outcome:** Viewer has a clear picture of where the brand sits in the competitive landscape and what competitors have been doing
  - **Covered by:** R13, R14, R15, R16, R17, R18, R19, R20, R21, R22, R23, R24

---

## Requirements

**Scraping — Amazon**

- R1. The Amazon scraper extracts the following fields per tracked product: product name, current price, sale price (if present), sale badge text (if present), Add to Cart availability status, star rating, review count, pack size/weight, and ASIN.

**Scraping — Walmart**

- R2. The Walmart scraper extracts the same fields as R1 plus the Walmart item ID. A proof-of-concept confirming reliable Walmart.com data retrieval without being blocked is the first deliverable before any other component is built. Kill signal: repeated failures across multiple sessions → evaluate pivot to Walmart API or third-party scraping service (Bright Data, ScraperAPI).

**Scraping — Promo detection**

- R3. Promo detection uses two complementary methods: (a) explicit sale badge or strikethrough price is present on the product page; (b) current scraped price is lower than the prior scrape for that same product at that retailer. Either signal independently flags the product as "in promo" for that scrape run. A product showing both signals is still one promo event.

**Scraping — OOS detection**

- R4. OOS detection uses two signals: (a) Add to Cart button is absent or disabled; (b) explicit OOS text is present (e.g., "Out of Stock", "Currently Unavailable"). Either signal independently flags the product as out-of-stock for that scrape run.

**Scraping — Reliability and ethics**

- R5. Each scraper enforces a minimum 2-second delay between page requests. Robots.txt is respected. No authentication, CAPTCHA bypass, or access control circumvention. On detection of blocking (429 response, CAPTCHA wall, access-denied redirect), the scraper logs the event and stops rather than retrying in a tight loop.
- R6. If a product page fails to parse (expected fields missing or malformed), the failure is logged with product ID, retailer, URL, and scrape-run timestamp. The scrape run continues for remaining products; no partial or null rows are inserted into Postgres.

**Data storage — Postgres**

- R7. All scraped data lives in a standalone Postgres database with no connection to the Cinderhaven Data Platform.
- R8. The schema covers three entity types: scrape runs (timestamp, retailer, status, duration), products (canonical ID, brand name, product name, pack size/weight, retailer, retailer-specific ID), and price snapshots (price, sale price, promo flag, OOS flag, star rating, review count, per product per scrape run).
- R9. Deduplication: each price snapshot is unique by product × retailer × scrape date. Running the scraper twice on the same day for the same products produces one snapshot row, not two.
- R10. Price-per-oz is computed at query time from scraped price and pack weight. It is not stored as a column. Pack weight must be stored as a raw scraped field to enable this derivation.

**Data storage — Entity resolution**

- R11. A mapping table links retailer-specific IDs (ASIN for Amazon, item ID for Walmart) to a canonical product ID. This enables cross-retailer price comparison in the Price Positioning tab. The mapping is maintained manually in v1 — no automated fuzzy matching.

**Data storage — Cinderhaven synthetic data**

- R12. Cinderhaven synthetic data is loaded into the same Postgres schema as real scraped data, using the same tables and fields. Cinderhaven has 5–8 synthetic SKUs in the artisan sauce/condiment category. Cinderhaven's synthetic price per oz is set at the real category median after the first scrape run is complete, so Cinderhaven is positioned relative to actual market data rather than a pre-chosen narrative.

**Dashboard — General**

- R13. The dashboard is a Dash app following the conventions of `retail-velocity-decision-tool`: Lailara Design System v2 (color tokens, Playfair Display + Source Sans 3 typography), Plotly charts, AG Grid for tabular data, `dash_bootstrap_components` layout.
- R14. Navigation is a tab bar across the top with five tabs in this order: Price Positioning, Promo Activity, OOS Tracker, Assortment Monitor, Review Pulse. Price Positioning is the default tab.
- R15. Every tab displays a "Last scraped: [date]" indicator so the viewer always knows data freshness.
- R16. The dashboard is read-only. The only user inputs are tab selection and an optional date range filter (last 30 / last 60 / last 90 days, or full history).

**Dashboard — Price Positioning tab**

- R17. The Price Positioning tab shows a horizontal lollipop or dot chart. Y-axis: one row per brand. X-axis: price per oz. Each brand has two data points (Amazon, Walmart) encoded by color. Cinderhaven is visually highlighted (distinct marker or label weight). Chart follows Economist conventions: horizontal gridlines only, no decorative elements, every data point labeled with its value.

**Dashboard — Promo Activity tab**

- R18. The Promo Activity tab shows a timeline per brand: X-axis = date (scrape dates), Y-axis = each brand. Each date cell is colored when a promo was detected (either method from R3). Displays the date range selected by the filter (default: last 90 days or full history if less).
- R19. The Promo Activity tab includes a summary row per brand: total promo events in the selected date range and average promo depth as a percentage (when sale price is available; omitted when only price-drop detection fired).

**Dashboard — OOS Tracker tab**

- R20. The OOS Tracker tab shows a timeline grid: one row per tracked product, one column per scrape date. Cells are colored red when the product was flagged OOS (either signal from R4). Cinderhaven's synthetic OOS events are included alongside competitor data.
- R21. The OOS Tracker tab shows an estimated lost-revenue indicator for Cinderhaven OOS events: days OOS × a configurable average-daily-sales-rate assumption. The assumption defaults to $0 (hidden) until the operator sets it. When set, the indicator displays as a callout: "Estimated lost revenue: $X over Y days."

**Dashboard — Assortment Monitor tab**

- R22. The Assortment Monitor tab compares the most recent scrape run to the prior one and flags: products present in the most recent run but absent previously ("New Entry") and products present in prior runs but absent in the most recent run ("Possible Delist"). Displayed as a sortable table with columns: brand, product name, retailer, status, first seen, last seen.

**Dashboard — Review Pulse tab**

- R23. The Review Pulse tab shows two charts per brand: (a) star rating trend over scrape history (line chart), (b) review count trend over scrape history (bar chart). Individual review text is not scraped or displayed.

**Deployment**

- R24. The Dash app is deployed to Fly.io as an always-on service. The Dockerfile uses the `retail-velocity-decision-tool` deployment as a reference, extended to include Playwright browser binaries (~300–500 MB added to image size). Postgres credentials are passed via environment variables, never hardcoded.
- R25. A `README.md` in the repo root documents: how to run a manual scrape (the exact command), how to add a new competitor product to the tracking list, and how to view the dashboard URL.

---

## Acceptance Examples

- AE1. **Covers R3, R18.** Given a competitor product was scraped at $8.99 on Monday and $7.19 on Wednesday with no sale badge present, the Wednesday scrape flags the product as "in promo" via price-drop detection. The Promo Activity tab shows Wednesday as a shaded promo event for that brand.

- AE2. **Covers R4, R20.** Given a product page showed an Add to Cart button on Monday's scrape but not on Wednesday's scrape, Wednesday's scrape flags the product as OOS. The OOS Tracker shows Wednesday as a red cell for that product.

- AE3. **Covers R9.** Given the Amazon scraper runs twice on the same day for the same competitor set, Postgres contains exactly one price snapshot row per product per retailer — not two.

- AE4. **Covers R22.** Given a new competitor product appears in today's scrape but was absent in all prior scrapes, the Assortment Monitor flags it as "New Entry" with today's date as first seen. A product that was present in prior scrapes but absent today is flagged "Possible Delist."

- AE5. **Covers R6.** Given a Walmart.com product page returns malformed HTML and the price field cannot be parsed, the scraper logs the failure (product ID, URL, timestamp) and continues scraping the remaining products in the run. No null or partial row is inserted for the failed product.

---

## Success Criteria

- A portfolio prospect who opens the Fly.io URL sees real competitive pricing data for artisan sauce brands — not placeholder data, not pre-engineered findings. The data reflects the actual category as it exists on Amazon and Walmart.
- A Lailara client engagement can be scoped by pointing to this dashboard: "This is what competitive shelf intelligence looks like for your category."
- The operator can run a full scrape manually in under 10 minutes of active effort (excluding request wait time).
- Planning (`/ce:plan`) can proceed without inventing product behavior, scope boundaries, or success criteria.

---

## Scope Boundaries

- Lead-gen assets (landing pages, social posts, email sequences) — separate project
- Cinderhaven Data Platform integration — standalone Postgres only
- Automated scraping schedule — manual v1 only; scheduling deferred
- 90-day competitive audit as a published content piece — evaluated after real data accumulates
- Instacart, Target.com — v2
- dbt — plain SQL queries for v1; dbt deferred until multiple consumers exist
- Individual review text scraping — aggregate star rating and review count only
- Retailer-authenticated or paywalled pages — publicly visible product data only
- Pricing recommendations, automated alerts, or action layer — display-only dashboard
- Pre-engineered findings — Cinderhaven's story is whatever the real data shows

---

## Key Decisions

- **Dash over Streamlit:** already proven on Fly.io in `retail-velocity-decision-tool`; same Plotly foundation; no cold-start problem; consistent Lailara design system
- **dbt excluded from v1:** one dashboard consumer doesn't justify the setup overhead; plain SQL views are sufficient; add dbt when there are multiple downstream consumers
- **Walmart proof-of-concept first:** highest unproven technical risk; must be validated in session 1 before any other component is built
- **Both promo detection methods:** badge detection is more precise; price-drop fallback captures unlabeled sales; both together minimize false negatives
- **Both OOS detection methods:** broader net; "Add to Cart absent OR OOS text present" covers edge cases where only one signal fires
- **Cinderhaven at real category median:** preserves "data tells the real story" principle; avoids pre-engineering the portfolio narrative

---

## Dependencies / Assumptions

- Walmart.com may require Playwright (not just `requests`) to reliably retrieve product page data; confirmed or denied during the proof-of-concept
- Amazon product pages may require Playwright for JS-rendered fields (rating, review count); verify during build
- Pack size/weight is parseable from product page text on both retailers; required for price-per-oz normalization (R10, R17)
- The artisan sauce/condiment category on Amazon and Walmart has 5–8 real brands with meaningful price variation; confirmed during competitor-set selection in early build sessions

---

## Outstanding Questions

### Resolve Before Planning

*(None — all scope-blocking questions resolved in dialogue)*

### Deferred to Planning

- **[Affects R11][Technical]** Entity resolution implementation: UPC matching, ASIN-to-Walmart-ID linking, or a manually maintained CSV/table? Investigate during planning.
- **[Affects R1, R2][Needs research]** Which pages on Amazon and Walmart require Playwright vs. plain `requests` + BeautifulSoup? Determine during Walmart proof-of-concept and Amazon spike.
- **[Affects R7][Technical]** Postgres hosting: Fly Postgres (same Fly.io org) vs. external managed Postgres (Railway, Supabase, Neon)? Evaluate setup complexity and cost during planning.
- **[Affects R16][Technical]** Date range filter implementation: `dcc.DatePickerRange` or simple radio buttons (Last 30 / 60 / 90 days / All)? Decide during implementation based on data volume.
