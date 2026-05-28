---
title: Competitive Shelf Intelligence — Full Build Plan
created: 2026-05-28
status: active
origin: docs/brainstorms/competitive-shelf-intelligence-requirements.md
---

# Competitive Shelf Intelligence — Full Build Plan

## Problem Frame

Specialty food brands at $5M–$20M cannot afford $50K–$200K/year for syndicated data. Their
current alternative is manual: walking aisles or typing competitor names into Walmart.com by
hand. The result is no historical data, no trend lines, no alerts, and competitive intel that
only happens when someone has time.

This project closes that gap with a scraper → Postgres → Dash pipeline deployed on Fly.io.
Real artisan sauce/condiment competitor data from Amazon.com and Walmart.com, with synthetic
Cinderhaven brand data positioned at the real category median. The story is whatever the data
shows.

_(see origin: docs/brainstorms/competitive-shelf-intelligence-requirements.md §Problem Frame)_

---

## Scope

**In:**
- Python + Playwright scrapers for Amazon.com and Walmart.com
- Real artisan sauce/condiment competitor set (5–8 brands, selected during build)
- Standalone Postgres (Fly Postgres, same Fly.io org — co-located, minimal setup overhead)
- Dash dashboard: Price Positioning, Promo Activity, OOS Tracker, Assortment Monitor, Review Pulse
- Synthetic Cinderhaven data (5–8 SKUs, priced at real category median after first scrape)
- Always-on Fly.io deployment
- Manual scrape runs for v1

**Out (see origin §Scope Boundaries):**
- Lead-gen assets (separate project)
- Cinderhaven Data Platform integration
- Automated scraping schedule
- 90-day competitive audit as content piece
- Instacart, Target.com
- dbt (plain SQL views sufficient for one dashboard consumer)
- Individual review text
- Pre-engineered Cinderhaven positioning

---

## Architecture Overview

```
config/products.yaml          ← operator-maintained list of competitor URLs
        │
        ▼
scrape.py (CLI)               ← python scrape.py --retailer [amazon|walmart|all]
        │
        ├─ src/scrapers/base.py       ← rate limit, robots.txt, block detection
        ├─ src/scrapers/walmart.py    ← Playwright + __NEXT_DATA__ JSON
        └─ src/scrapers/amazon.py     ← Playwright + CSS fallback chain
                │
                ▼
        src/scrapers/entity_resolution.py   ← UPC exact match → manual map
                │
                ▼
        Fly Postgres (standalone, no CDP connection)
                │
                ▼
        app/ (Dash, follows retail-velocity-decision-tool patterns exactly)
                │
                ▼
        Fly.io (always-on, 2GB memory for Playwright)
```

The scraper and the dashboard share the same Postgres database but run independently. The
scraper is a CLI process; the dashboard is a gunicorn-served Dash app. They never run in the
same process.

---

## Key Technical Decisions

**Walmart first (POC gate)**
R2 flags Walmart as the highest unproven technical risk. The Walmart POC is the first
deliverable and is a gate: if it fails repeatedly across multiple sessions, pivot to Walmart
API or ScraperAPI before building anything else. No other implementation unit begins until the
POC succeeds.

**Playwright for both retailers**
Both Amazon and Walmart render key data (pricing, availability, ratings) via JavaScript.
Plain `requests + BeautifulSoup` will miss JS-rendered fields. Playwright with stealth args is
the baseline for both scrapers. (see origin §Dependencies / Assumptions)

**Walmart: `__NEXT_DATA__` JSON over CSS selectors**
Walmart's product pages embed pricing and OOS state in a `<script id="__NEXT_DATA__">` JSON
blob. This is far more stable than CSS selector chains. Parse `priceInfo.currentPrice.price`,
`priceInfo.wasPrice`, `priceInfo.isPriceReduced`, `availabilityStatus` from this JSON.
CSS selectors fall back to `__NEXT_DATA__`; selectors are the fallback, not the primary.

**Amazon: CSS fallback chain**
Amazon does not have an equivalent JSON blob. Use a CSS fallback chain:
price: `#priceblock_ourprice` → `#priceblock_dealprice` → `.a-price .a-offscreen`
→ `.priceToPay .a-offscreen`. OOS: `#availability span` text → Add to Cart button absent
→ `#outOfStock` element. Comment each selector with why it exists and its known failure mode.

**Anti-bot: three-tier strategy**
1. Dev/test: `playwright-stealth` + slow-scroll simulation + 2–5s jitter delay
2. Production baseline: residential proxy (provider selected during build)
3. Fallback: ScraperAPI Walmart endpoint or Oxylabs if Tier 2 is insufficient
Kill signal: repeated failures across multiple sessions → pause and reassess.

**Entity resolution: UPC exact match + manual override (v1)**
R11 specifies manual mapping in v1 — no fuzzy matching. The implementation uses:
1. UPC/GTIN exact match: UPC is available in Walmart `__NEXT_DATA__` (`product.upc`) and
   Amazon product details table. Store UPC on `products`. Match new scraped products against
   stored UPCs to link Amazon and Walmart listings to a single canonical product.
2. Manual override: a `canonical_product_map` table that the operator populates for products
   where UPC is missing or mismatched (Walmart-style pack variants, bundle ASINs, etc.).
Fuzzy matching (RapidFuzz) is deferred to v2.

**Price-per-oz at query time (not stored)**
R10 explicitly prohibits storing `price_per_oz` as a column. Store `pack_weight_oz` on
`products`. Derive `price_cents / pack_weight_oz / 100` in SQL views and pandas operations.

**Postgres hosting: Fly Postgres (same Fly.io org)**
User already uses Fly.io. Fly Postgres is co-located (lowest latency), managed via the same
`flyctl` CLI, and costs nothing for the data volumes expected (< 1M rows in v1). Data is
re-scraped if lost — loss is not catastrophic.

**Dash patterns: follow `retail-velocity-decision-tool` exactly**
All Dash app patterns copy the reference project directly: PID-aware `ThreadedConnectionPool`
in `db.py`, `@cache.memoize` in `data.py`, `base_chart_layout()` in `charts.py`,
`register_callbacks(app)` pattern in `callbacks.py`, module pattern per tab (`layout()` +
`register_callbacks()`). Do not invent new patterns without surfacing it first.

**Docker: official Playwright image**
`FROM mcr.microsoft.com/playwright/python:v1.49.0-noble`. Avoids manual `apt-get` dependency
hell. `--disable-dev-shm-usage` in all Playwright `launch()` calls (required in containers).
`tini` as ENTRYPOINT for zombie process prevention. Memory: 2GB (Playwright overhead).

**Date range filter: radio buttons**
R16 specifies predefined options (Last 30 / 60 / 90 days / Full History). Simple radio
buttons (`dcc.RadioItems`) match the spec exactly. `dcc.DatePickerRange` is overkill for
a fixed option set.

---

## Implementation Sequence

The sequence is ordered to fail fast on the highest-risk components.

```
Phase 1 (POC gate)
  IU-7   Competitor product config (1 product, Walmart)
  IU-2   Scraper base class
  IU-3a  Walmart POC (name + price for 1 product)
  ──── GATE: POC must succeed before continuing ────

Phase 2 (Schema + full scrapers)
  IU-1   Database schema + connection layer
  IU-3b  Walmart scraper (full fields, all products)
  IU-4   Amazon scraper (full fields)
  IU-5   Entity resolution
  IU-6   Scrape CLI
  IU-7   Competitor product config (full set, 5–8 brands)

Phase 3 (Synthetic data)
  ──── First real scrape run ────
  IU-8   Synthetic data loader (Cinderhaven at real median)

Phase 4 (Dashboard)
  IU-9   Dashboard app (all 5 tabs)

Phase 5 (Deployment)
  IU-10  Dockerfile + fly.toml

Phase 6 (Documentation)
  README.md (R25)
```

---

## Implementation Units

---

### IU-1: Database Schema and Connection Layer

**Covers:** R7, R8, R9, R10, R11

**Files:**
- `db/schema.sql` — DDL (tables, indexes, constraints, views)
- `src/db.py` — PID-aware connection pool (adapt from `retail-velocity-decision-tool/app/db.py`)
- `db/seed_canonical_map.sql` — empty template for manual entity mappings

**Schema design:**

```
scrape_runs
  id, retailer (amazon|walmart|all), started_at, completed_at,
  status (running|complete|failed), product_count, failure_count

brands
  id, canonical_name, created_at

products
  id, brand_id, canonical_name, pack_size_raw, pack_weight_oz (NUMERIC),
  upc (VARCHAR, nullable), created_at
  -- pack_weight_oz stored here; price_per_oz derived at query time (R10)

retailer_listings
  id, product_id, retailer, retailer_id (ASIN or Walmart item ID),
  product_url, first_seen_at, last_seen_at
  -- links canonical product to retailer-specific listing (R11)

price_snapshots
  id, listing_id, scrape_run_id, scraped_at, scraped_date (DATE),
  price_cents (INT), sale_price_cents (INT nullable),
  has_promo_badge (BOOL), sale_badge_text (VARCHAR nullable),
  price_drop_promo (BOOL),  -- true when price < prior scrape, no badge
  is_oos (BOOL), oos_signal (VARCHAR nullable),  -- 'no_cart_button'|'oos_text'
  star_rating (NUMERIC nullable), review_count (INT nullable),
  raw_html_hash (VARCHAR)
  UNIQUE (listing_id, scraped_date)  -- deduplication by product × retailer × date (R9)

canonical_product_map
  id, walmart_listing_id, amazon_listing_id, canonical_product_id,
  note (VARCHAR nullable), created_by, created_at
  -- manual override table for entity resolution (R11)

scrape_failures
  id, scrape_run_id, listing_id, retailer, url, error_message,
  failed_at
  -- every parse failure logged here (R6)
```

**Deduplication mechanism:**
Unique index on `(listing_id, scraped_date)` with `INSERT ... ON CONFLICT DO NOTHING`.
The `scraped_date` column stores `DATE(scraped_at)`. A second run on the same calendar day
produces no new rows (AE3).

**`src/db.py`:** Copy the PID-aware `ThreadedConnectionPool` pattern from
`retail-velocity-decision-tool/app/db.py`. Key points: pool keyed by `os.getpid()`, `get_conn()`
context manager with `putconn()` on exit, `DEC2FLOAT` psycopg2 typecast registered, `DATABASE_URL`
env var required.

**SQL views (no dbt in v1):**
- `v_price_per_oz` — joins `price_snapshots`, `retailer_listings`, `products`, computes
  `price_cents::float / pack_weight_oz / 100.0 AS price_per_oz`
- `v_promo_events` — rows where `has_promo_badge OR price_drop_promo`
- `v_oos_events` — rows where `is_oos = true`
- `v_latest_snapshot_per_product` — most recent snapshot per listing

**Test scenarios:**
- `test_unique_constraint_prevents_duplicate_snapshot_same_day` — insert same listing + same date twice, confirm second insert silently ignored
- `test_price_per_oz_view_computes_correctly` — known price_cents + pack_weight_oz → expected value
- `test_scrape_failure_row_inserted_on_parse_error` — failure logs all required fields (R6)
- `test_canonical_product_map_links_amazon_to_walmart_listing`

**Pattern reference:** `retail-velocity-decision-tool/app/db.py`

---

### IU-2: Scraper Base Class

**Covers:** R5, R6

**Files:**
- `src/scrapers/base.py`

**Design:**
`BaseProductScraper` holds Playwright browser lifecycle, rate limiting, robots.txt checking,
and block detection. Concrete scrapers (`WalmartScraper`, `AmazonScraper`) inherit from it.

Responsibilities:
- `check_robots(url)` — uses `urllib.robotparser.RobotFileParser`; raises `RobotsDisallowedError`
  if the path is disallowed for the scraper user-agent
- `_rate_limit()` — enforces minimum 2-second delay between requests; uses `time.sleep` with
  a small random jitter (2.0–5.0s) to reduce fingerprinting
- `fetch_page(url)` — launches Playwright `chromium` in headless mode with stealth args,
  loads URL, detects block signals before returning the `Page` object
- `_detect_block(page)` — returns `True` if HTTP status is 429, page contains CAPTCHA form
  elements, or page redirected to an access-denied URL; on True, logs + raises `BlockDetectedError`
- `log_failure(listing_id, url, scrape_run_id, error)` — inserts row into `scrape_failures`;
  scrape run continues for remaining products after failure (R6)

User-agent: identify honestly as a competitive intelligence scraper (src/CLAUDE.md convention).

**Test scenarios** (all fixture-based, no live network calls):
- `test_raises_robots_disallowed_when_path_excluded`
- `test_allows_fetch_when_robots_permits_path`
- `test_raises_block_detected_when_429_status`
- `test_raises_block_detected_when_captcha_element_present`
- `test_minimum_delay_enforced_between_fetches` — mock `time.sleep`, confirm called with ≥ 2s
- `test_failure_log_contains_required_fields` — listing_id, url, scrape_run_id, timestamp

---

### IU-3: Walmart Scraper (POC gate → full build)

**Covers:** R2, R3, R4, R5, R6

**Files:**
- `src/scrapers/walmart.py`
- `tests/scrapers/test_walmart.py`
- `tests/fixtures/walmart/` — saved HTML files for each test scenario

**Phase 1 POC scope:** fetch product name + current price for one product. Confirm Playwright
can retrieve the page without being blocked. No DB writes. Logged to stdout.

**Full build — field extraction strategy:**

Primary: parse `window.__NEXT_DATA__` JSON from `<script id="__NEXT_DATA__">` element.
Fields and JSON paths:
- `product.name` → product name
- `priceInfo.currentPrice.price` → current price
- `priceInfo.wasPrice.price` → sale/was-price (promo signal a)
- `priceInfo.isPriceReduced` → explicit promo flag (promo signal a)
- `priceInfo.priceReducedDisplay` → badge text
- `availabilityStatus` → `"IN_STOCK"` | `"OUT_OF_STOCK"` | `"NOT_AVAILABLE"` (OOS signal a)
- `product.upc` → UPC for entity resolution
- `rating.averageRating` → star rating
- `rating.numberOfReviews` → review count
- product title or `product.shortDescription` → pack size string for weight parsing

OOS signal b: `document.querySelector('[data-automation-id="add-to-cart-button"]')` absent.

Promo signal b: `priceInfo.currentPrice.price < prior_snapshot.price_cents / 100.0` — checked
in the CLI before insert, using `v_latest_snapshot_per_product`.

If `__NEXT_DATA__` is absent or the JSON structure differs, log parse failure and continue
(R6, AE5). Do not insert partial rows.

**Anti-bot (three tiers, applied in Playwright launch args):**
- `playwright-stealth` applied to browser context
- `--disable-blink-features=AutomationControlled`
- `--disable-dev-shm-usage` (container requirement)
- `window.navigator.webdriver = undefined` via `page.add_init_script()`
- Slow random scroll on page load to simulate human reading
- Jitter delay 2–5s between products
- Residential proxy URL injected via `PROXY_URL` env var (optional; if absent, runs without proxy)

**`ScrapedProduct` dataclass** (defined in `src/scrapers/base.py`):
```
product_name, current_price, sale_price, has_promo_badge, sale_badge_text,
is_oos, oos_signal, star_rating, review_count, pack_size_raw, upc,
retailer_id, retailer
```

**Test scenarios** (fixture-based):
- `test_extracts_price_from_next_data_json` — fixture: standard Walmart product page
- `test_extracts_upc_from_next_data`
- `test_detects_promo_when_is_price_reduced_true`
- `test_detects_promo_when_was_price_present`
- `test_flags_oos_when_availability_status_out_of_stock`
- `test_flags_oos_when_add_to_cart_button_absent`
- `test_logs_failure_and_returns_none_when_next_data_missing` — AE5 coverage
- `test_logs_failure_when_price_field_absent` — R6 coverage
- `test_extracts_star_rating_and_review_count`
- `test_pack_size_extracted_from_product_title`

---

### IU-4: Amazon Scraper

**Covers:** R1, R3, R4, R5, R6

**Files:**
- `src/scrapers/amazon.py`
- `tests/scrapers/test_amazon.py`
- `tests/fixtures/amazon/` — saved HTML files

**Field extraction strategy (CSS fallback chain):**

Price (try in order, stop at first match):
1. `#priceblock_ourprice` — standard price
2. `#priceblock_dealprice` — deal price when sale active
3. `.a-price .a-offscreen` — new price display format
4. `.priceToPay .a-offscreen` — alternate current-price selector

Sale price: `#priceblock_saleprice` OR presence of a strikethrough element
(`.a-text-strike`) alongside the current price. If strikethrough present, original price
is the `was` price.

OOS (either signal → `is_oos = True`):
- `#availability span` text contains "Out of Stock" or "Currently Unavailable"
- `#add-to-cart-button` element absent from DOM
- `#outOfStock` element present

Star rating: `#acrPopover` title attribute OR `span[data-hook="rating-out-of-stars"]`
Review count: `#acrCustomerReviewText` text, strip non-numeric characters

Pack size: product title text → regex for weight patterns (e.g., "16 oz", "1 lb", "500g").
If not found in title, check the product details table (`th:contains("Size")` adjacent `td`).

ASIN: extracted from URL (`/dp/([A-Z0-9]{10})`) — no page parsing needed.

UPC: Amazon product details table (`th:contains("UPC")` adjacent `td`). May be absent on some
listings; nullable.

Comment every selector with: (a) what it targets, (b) known alternative page layout it covers,
(c) when it was verified as working. Amazon changes layouts periodically.

**Test scenarios:**
- `test_extracts_price_from_primary_selector`
- `test_extracts_price_from_fallback_selector_when_primary_absent`
- `test_extracts_price_from_third_fallback`
- `test_detects_sale_when_strikethrough_price_present`
- `test_flags_oos_when_availability_text_says_out_of_stock`
- `test_flags_oos_when_add_to_cart_button_absent`
- `test_flags_oos_when_out_of_stock_element_present`
- `test_extracts_star_rating_correctly`
- `test_extracts_review_count_strips_non_numeric`
- `test_extracts_pack_weight_from_title_oz`
- `test_extracts_pack_weight_from_title_lb_converted_to_oz`
- `test_extracts_upc_from_product_details_table`
- `test_logs_failure_when_no_price_selector_matches` — R6 coverage
- `test_extracts_asin_from_url`

---

### IU-5: Entity Resolution

**Covers:** R11

**Files:**
- `src/scrapers/entity_resolution.py`
- `tests/scrapers/test_entity_resolution.py`

**Design:**

`resolve_product(scraped: ScrapedProduct, retailer: str, conn) -> (product_id, listing_id)`

Three-tier lookup (stop at first match):

**Tier 1 — UPC exact match:**
- Query `products` for `upc = scraped.upc` (when scraped UPC is not None)
- If found: retrieve `product_id`; check `retailer_listings` for existing `(product_id, retailer)` pair
- If listing exists: return `(product_id, listing_id)`
- If listing absent: insert new `retailer_listings` row, return new `listing_id`

**Tier 2 — Manual canonical map:**
- Query `canonical_product_map` for `(walmart_listing_id, amazon_listing_id)` matching the
  scraped `retailer_id`
- If found: return mapped `canonical_product_id`

**Tier 3 — New product:**
- No match found → insert new `products` row (using scraped name + UPC if available)
- Insert `retailer_listings` row for this retailer
- Return new `(product_id, listing_id)`

This is intentionally conservative: Tier 3 creates new canonical products rather than
guessing matches. The operator cleans up via `canonical_product_map` for cross-retailer linking.
Fuzzy matching is deferred to v2 per R11.

**Test scenarios:**
- `test_resolves_product_by_upc_when_upc_matches_existing`
- `test_creates_new_listing_for_new_retailer_when_product_exists`
- `test_applies_manual_canonical_map_when_upc_absent`
- `test_creates_new_product_when_no_match_found`
- `test_links_amazon_and_walmart_listing_to_same_canonical_product_via_upc` (cross-retailer)
- `test_handles_null_upc_gracefully`

---

### IU-6: Scrape CLI

**Covers:** F1, R1, R2, R5, R6, R8, R9

**Files:**
- `scrape.py` (project root — the "exact command" the operator runs, per R25)

**CLI interface:**
```
python scrape.py [OPTIONS]

Options:
  --retailer [amazon|walmart|all]  Default: all
  --delay FLOAT                    Seconds between requests. Default: 2.0
  --dry-run                        Parse pages but do not write to DB
```

**Run sequence:**
1. Load `config/products.yaml` — list of tracked products with URL, retailer, listing ID
2. Open DB connection; insert `scrape_runs` row (status=running)
3. For each product in list (filtered by --retailer):
   a. Call `check_robots(url)` — skip + log if disallowed
   b. Call `scraper.fetch_product(listing_id, url, scrape_run_id)`
   c. On success: resolve entity, check prior-price for promo signal b, insert `price_snapshots`
      with `ON CONFLICT DO NOTHING`
   d. On `BlockDetectedError`: log + stop entire run
   e. On `ParseFailureError`: log to `scrape_failures`, continue to next product (R6, AE5)
4. Update `scrape_runs` row (status=complete, product_count, failure_count)
5. Print summary: products scraped, failures, elapsed time

**`config/products.yaml` format:**
```yaml
products:
  - name: "Brand Name Hot Sauce 12 oz"
    brand: "Brand Name"
    retailer: walmart
    url: "https://www.walmart.com/ip/..."
    retailer_id: "12345678"
    upc: "012345678901"  # optional, helps entity resolution
  - ...
```

Operator adds new competitors by editing this file (R25 — README must document this).

**Test scenarios:**
- `test_creates_scrape_run_record_at_start`
- `test_updates_scrape_run_status_on_completion`
- `test_continues_after_single_product_parse_failure` — AE5 coverage
- `test_stops_run_on_block_detected`
- `test_deduplication_on_same_day_second_run` — AE3 coverage; second run inserts 0 new snapshot rows
- `test_dry_run_inserts_nothing_to_db`
- `test_failure_count_reflects_parse_errors_in_run_record`

---

### IU-7: Competitor Product Config

**Covers:** R25 (operator adds competitors via this file)

**Files:**
- `config/products.yaml` — competitor product list (committed to repo, no secrets)

**First pass (POC):** 1 Walmart product. Expand to full set (5–8 brands × 2 retailers)
once POC passes and schema is in place. The full competitor set is selected during build
by researching the artisan sauce/condiment category on both retailers.

Criteria for competitor selection:
- Artisan/specialty positioning (not mass-market like Tabasco)
- Sold on both Amazon and Walmart where possible (enables cross-retailer price comparison)
- Has meaningful price variation across the category
- 5–8 brands total; 1–3 SKUs per brand is fine for v1

---

### IU-8: Synthetic Cinderhaven Data Loader

**Covers:** R12

**Files:**
- `scripts/load_synthetic.py`

**Design:**
One-time idempotent script that loads Cinderhaven synthetic data into Postgres using the
same schema as real scraped data.

Run after the first real scrape is complete. At that point:
1. Compute median `price_per_oz` across all competitors (across both retailers)
2. Define 5–8 Cinderhaven SKUs (e.g., "Cinderhaven Original Hot Sauce 8 oz", etc.)
3. Set Cinderhaven's synthetic `price_cents` so that `price_cents / pack_weight_oz / 100`
   equals (or is within a few cents of) the computed category median

Script is idempotent: `INSERT ... ON CONFLICT DO NOTHING` on `products.canonical_name`.

Cinderhaven brand is inserted as a normal `brands` row. Listings are inserted as `retailer_listings`
rows. Historical snapshots are inserted as `price_snapshots` rows with synthetic `scraped_at`
timestamps covering the same date range as real data.

OOS events and promo events for Cinderhaven are synthetic: a plausible number of OOS days
(3–5 per quarter) and promo events (1–2 per quarter) spread across the history. No
pre-engineering of where Cinderhaven lands vs. competitors — just position at the median and
let promo/OOS patterns be mild.

**Test scenarios:**
- `test_load_synthetic_is_idempotent` — run twice, confirm row counts unchanged
- `test_cinderhaven_price_per_oz_equals_category_median` — post-load query check
- `test_synthetic_snapshots_cover_full_date_range`

---

### IU-9: Dashboard App

**Covers:** R13–R23

**Files** (following `retail-velocity-decision-tool` module pattern exactly):
- `app/run.py` — init order: load_dotenv → Dash → cache → layout → callbacks → health
- `app/db.py` — PID-aware pool (from reference project)
- `app/data.py` — SQL queries + `@cache.memoize(timeout=3600)`
- `app/charts.py` — `base_chart_layout()`, chart helpers
- `app/components.py` — `metric_card()`, `last_scraped_indicator()`, `error_card()`
- `app/constants.py` — Lailara color tokens (copy from reference, add ORANGE if needed)
- `app/layout.py` — `dbc.Container → dbc.Row → dcc.Tabs` with 5 tab labels
- `app/callbacks.py` — `register_callbacks(app)` dispatcher
- `app/tabs/price_positioning.py` — layout + register_callbacks
- `app/tabs/promo_activity.py`
- `app/tabs/oos_tracker.py`
- `app/tabs/assortment_monitor.py`
- `app/tabs/review_pulse.py`

**Tab designs:**

**Price Positioning (R17, default tab):**
- Horizontal lollipop/dot chart; Y-axis: one row per brand; X-axis: price per oz
- Two markers per brand: Amazon (Chicago navy) and Walmart (HK teal)
- Cinderhaven row highlighted: bold label weight, distinct marker shape (diamond vs circle)
- Economist conventions: horizontal gridlines only, every data point labeled with `$X.XX/oz`
- Uses `v_price_per_oz` view, most recent scrape per retailer per product
- `last_scraped_indicator()` component in header (R15)

**Promo Activity (R18–R19):**
- Heatmap/timeline grid: Y-axis = brand, X-axis = scrape date
- Cells colored when `has_promo_badge OR price_drop_promo` (R3 / AE1)
- Date range filter: `dcc.RadioItems` ["Last 30 days", "Last 60 days", "Last 90 days", "All"] (R16)
- Summary table below chart: brand, total promo events, avg promo depth % (R19)
  - Promo depth: `(sale_price - current_price) / sale_price * 100` where sale_price available
  - Omit depth column when only price-drop detection fired (no sale_price recorded)

**OOS Tracker (R20–R21):**
- Grid: Y-axis = product (brand + name), X-axis = scrape date
- Cells colored red when `is_oos = true`; Cinderhaven included alongside competitors (R20)
- Lost-revenue callout for Cinderhaven (R21): `days_oos × avg_daily_sales_rate`
  - `avg_daily_sales_rate` configured via `CINDERHAVEN_DAILY_REVENUE` env var; defaults to 0 (hidden)
  - When set: "Estimated lost revenue: $X over Y days" displayed as dark callout card

**Assortment Monitor (R22, AE4):**
- Compares most recent scrape run against prior run
- AG Grid table: brand, product name, retailer, status ("New Entry" or "Possible Delist"),
  first seen, last seen
- "New Entry": in current run, not in prior; "Possible Delist": in prior, not in current
- Sortable on all columns

**Review Pulse (R23):**
- Per brand: (a) star rating trend over history (line chart), (b) review count trend (bar chart)
- No individual review text (R23 / §Scope Boundaries)
- Both charts per row in a grid layout; one row per brand

**Date range filter state:** stored in `dcc.Store`, shared across all tabs that support it
(Promo Activity + OOS Tracker + Review Pulse). Price Positioning always shows latest.
Assortment Monitor always compares latest vs. prior — date filter not applicable.

**`last_scraped_indicator()` component:**
- Queries `scrape_runs` for the most recent completed run
- Renders: "Last scraped: May 28, 2026 (Amazon + Walmart)" or per-retailer if they differ
- Shown on every tab header (R15)

**Error/empty states:**
- No data yet: `empty_state("No scrape data yet. Run python scrape.py to collect data.")`
- DB connection failure: `error_card()` (follows reference pattern)
- Per-tab: each tab module handles its own empty/error state

**Test scenarios** (unit-testable data layer):
- `test_price_per_oz_view_returns_correct_value_for_known_product`
- `test_promo_events_query_returns_events_for_both_detection_methods` — AE1 coverage
- `test_oos_events_query_returns_events_for_both_detection_signals` — AE2 coverage
- `test_assortment_monitor_query_flags_new_entry_correctly` — AE4 coverage
- `test_assortment_monitor_query_flags_possible_delist_correctly`
- `test_last_scraped_indicator_reflects_most_recent_completed_run` — R15
- `test_date_range_filter_limits_promo_events_to_selected_window`
- `test_lost_revenue_callout_hidden_when_daily_rate_is_zero`
- `test_lost_revenue_callout_shows_correct_value_when_rate_set`

**Pattern references:**
- `retail-velocity-decision-tool/app/db.py` — connection pool
- `retail-velocity-decision-tool/app/data.py` — caching pattern
- `retail-velocity-decision-tool/app/charts.py` — `base_chart_layout()`, `add_vline_at_date()`
  (required for pandas 3.x + plotly 6.x compatibility)
- `retail-velocity-decision-tool/app/components.py` — `metric_card()`, `error_card()`, `empty_state()`
- `retail-velocity-decision-tool/app/run.py` — initialization order

---

### IU-10: Deployment

**Covers:** R24

**Files:**
- `Dockerfile`
- `fly.toml`
- `requirements.txt`

**Dockerfile:**
```
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble
# playwright chromium is pre-installed in this image; --with-deps already run

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "1",
     "--timeout", "120", "app.run:server"]
```

Notes:
- `tini` is pre-installed in the Playwright base image
- 1 gunicorn worker (Playwright is not fork-safe; if scraper is in the image, never run scrapers from gunicorn workers — run as a separate CLI process)
- `--disable-dev-shm-usage` set in Playwright `launch()` calls, not in Dockerfile

**fly.toml (key settings):**
- `primary_region = "iad"` — match reference project
- `[mounts]` → `/cache` volume → Dash `FileSystemCache`
- `[[services.ports]]` → 8050 → HTTP
- `[deploy] strategy = "immediate"`
- `auto_stop_machines = "off"` + `min_machines_running = 1` (always-on, R24)
- `[vm] memory = "2gb"` — Playwright headless chromium overhead
- Health check: GET `/health` every 30s; `app/run.py` registers `/health` route returning 200

**Postgres setup:**
```
flyctl postgres create --name competitive-shelf-pg --region iad
flyctl postgres attach competitive-shelf-pg --app competitive-shelf-intelligence
```
This injects `DATABASE_URL` automatically. Never hardcode credentials (R24).

**Env vars required:**
- `DATABASE_URL` — injected by `fly postgres attach`
- `PROXY_URL` — optional; residential proxy for Walmart scraper (not in source, in Fly secrets)
- `CINDERHAVEN_DAILY_REVENUE` — optional; enables lost-revenue callout in OOS Tracker

**`requirements.txt` key packages:**
```
dash>=2.18
dash-bootstrap-components>=1.6
dash-ag-grid>=31
plotly>=5.24
pandas>=2.2
psycopg2-binary
playwright
playwright-stealth
click
flask-caching
gunicorn
python-dotenv
```

Pin all versions before deployment. Run `pip-audit` before first deploy.

---

## Risk Register

| Risk | Severity | Mitigation |
|---|---|---|
| Walmart blocks Playwright requests | HIGH | Three-tier anti-bot strategy (stealth → proxy → ScraperAPI). Kill signal: repeated failures across sessions. |
| Amazon rate-limits or CAPTCHAs | MEDIUM | 2–5s jitter delay, stealth args. Amazon is generally more tolerant of well-behaved scrapers. |
| `__NEXT_DATA__` JSON structure changes | MEDIUM | Parse failures logged immediately (R6). Fixture-based tests catch regressions. Comment path choices in code. |
| Amazon CSS selectors break | MEDIUM | Fallback chain reduces single-selector risk. Add new fixture + test when page structure changes. |
| Pack size parsing fails for unusual formats | MEDIUM | Store `pack_size_raw` string always. `pack_weight_oz` can be NULL; dashboard omits those products from price/oz chart. |
| Playwright Docker image size (~1.5–2GB) | LOW | Expected. Use official Microsoft image; layer caching keeps deploys fast after first push. |
| Fly Postgres self-managed data loss | LOW | Data is re-scraped if lost. Run manual `pg_dump` weekly once the project is live. |
| Cross-retailer entity resolution gaps | LOW | Conservative Tier 3 creates new canonical products rather than wrong matches. Operator fixes via `canonical_product_map`. |

---

## Deferred to v2

- Fuzzy product name matching (RapidFuzz) for entity resolution without UPCs (R11 explicitly defers this)
- Automated scraping schedule (cron / Fly scheduled jobs)
- Instacart, Target.com scrapers
- dbt transformations (add when dashboard has multiple downstream consumers)
- `dcc.DatePickerRange` custom date range UI
- Email or Slack alerts on promo events or OOS detection
- 90-day competitive audit content piece

---

## Open Questions (Deferred to Implementation)

- **Competitor set selection**: which 5–8 artisan sauce/condiment brands to track? Researched
  during Phase 1 of build. Both Amazon and Walmart presence preferred for cross-retailer comparison.
- **Residential proxy provider**: Bright Data, Oxylabs, or Smartproxy? Evaluate during Walmart
  scraper build based on success rate and cost. Budget ~$50/month for v1 data volumes.
- **Playwright version pinning**: verify `playwright-stealth` compatibility with the version
  bundled in `mcr.microsoft.com/playwright/python:v1.49.0-noble` before deployment.
- **`pack_weight_oz` parsing edge cases**: oz, lb, g, ml, fl oz — build a `parse_weight_oz(raw)`
  utility in `src/utils.py` that normalizes all common units. Test heavily with fixture data.
