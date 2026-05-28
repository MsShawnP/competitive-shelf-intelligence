# competitive-shelf-intelligence — Handoff Log

Session-by-session state. Updated by /log mid-session and /wrap at
session end.

For durable choices, see DECISIONS.md.
For the current work arc, see PLAN.md.
For things that didn't work, see FAILURES.md.

---

## 2026-05-28 — Project initialized

**Started from:** New project setup.

**Did:** Created repo, set up CLAUDE.md/DECISIONS.md/HANDOFF.md/PLAN.md/
FAILURES.md, configured slash commands. Tier: Heavy. Stack: TBD.

**State:** Foundation in place. Ready to run /clarify to scope the work,
then /office-hours, /plan-ceo-review, /plan-eng-review before building.

**Next:** Run /clarify to reach 95% confidence on scope and deliverables.

---

## 2026-05-28 — Full implementation shipped (IU-1 through IU-10)

**Started from:** Foundation in place. All 10 implementation units executed.

**Did:**
- IU-1: Postgres schema (`db/schema.sql`) — brands, products, retailer_listings, scrape_runs, price_snapshots (UNIQUE listing_id+scraped_date), canonical_product_map, scrape_failures, plus 4 SQL views (v_price_per_oz, v_promo_events, v_oos_events, v_latest_snapshot_per_product)
- IU-2: DB connection pool (`src/db.py`, `app/db.py`) — PID-aware ThreadedConnectionPool, DEC2FLOAT typecast, get_conn() context manager; app/db.py duplicated intentionally for gunicorn import safety
- IU-3: Walmart scraper (`src/scrapers/walmart.py`) — ScraperAPI transport for production (bot detection), `__NEXT_DATA__` JSON parsing, Playwright fallback for fixture-based tests
- IU-4: Amazon scraper (`src/scrapers/amazon.py`) — BeautifulSoup CSS fallback chain (4 selectors), OOS detection ordered: availability span → #outOfStock → missing cart, sale/promo detection via .a-text-strike
- IU-5: Entity resolution (`src/scrapers/entity_resolution.py`) — 3-tier: UPC exact match → canonical_product_map → new product insert; all ON CONFLICT safe
- IU-6: Scrape CLI (`scrape.py`) — Click CLI with --retailer, --delay, --dry-run; skips REPLACE_WITH_* URLs with warning; logs failures to scrape_failures table
- IU-7: Synthetic data loader (`scripts/load_synthetic.py`) — 5 Cinderhaven SKUs, median-priced against real competitors, deterministic history via random.seed(listing_id)
- IU-8: Dashboard data layer (`app/data.py`, `app/constants.py`) — Flask-Caching with FileSystemCache → SimpleCache fallback, 7 query functions over the 4 SQL views
- IU-9: Dashboard UI (`app/layout.py`, `app/tabs/`, `app/charts.py`, `app/components.py`, `app/callbacks.py`, `app/run.py`) — 5 tabs: price positioning, promo activity, OOS tracker, assortment monitor, review pulse; /health endpoint; Lailara Design System v2 throughout
- IU-10: Deployment (`Dockerfile`, `fly.toml`) — Playwright base image, tini init, gunicorn 1 worker; Fly.io config with always-on min_machines=1, 2GB RAM, /health check, cache volume mount

**Tests:** 100/100 passing. All fixture-based — no live network, no live DB.

**Notable fixes during build:**
- OOS signal order in amazon.py: `#outOfStock` must be checked before missing cart button (cart can be absent for non-physical items); fixed fixture `product_oos_element.html` to include cart button
- `CHART_PALETTE` was referenced in `review_pulse.py` but not exported from `app/constants.py` — added it
- `add_vline_at_date()` helper replaces `fig.add_vline()` to avoid pandas 3.x + plotly 6.x TypeError

**Git state:** Clean on main. All IU commits in. DECISIONS.md and PLAN.md updated with 6 new decision entries and updated checkboxes.

**What is NOT done (next session starts here):**
1. **Fill competitor URLs** — `config/products.yaml` has `REPLACE_WITH_*` for all 10 products. Research real Walmart/Amazon URLs for each brand. Once filled, un-check this item in PLAN.md.
2. **Provision Fly Postgres** — `flyctl postgres create --name competitive-shelf-pg --region iad` → attach → `psql $DATABASE_URL -f db/schema.sql`
3. **Set Fly secrets** — `flyctl secrets set SCRAPERAPI_KEY=your_key`
4. **Run first scrape** — `python scrape.py` (or `--retailer walmart` to test one first)
5. **Load synthetic data** — `python scripts/load_synthetic.py` (run after first real scrape so median is computed from real data)
6. **Deploy** — `flyctl deploy`

**Next:** Research and fill competitor product URLs in `config/products.yaml`. That is the only manual step blocking a first real scrape.

---

## 2026-05-28 — Demo deployed and live at https://competitive-shelf-intelligence.fly.dev

**Started from:** All IUs shipped, URLs filled, Fly Postgres provisioned.

**Did:**
- Provisioned Fly Postgres (`competitive-shelf-pg`), applied schema via psycopg2 proxy (no local psql)
- Filled all competitor URLs in `config/products.yaml` (Yellowbird, Truff, Melinda's, Dave's Gourmet, Marie Sharp's)
- Discovered Walmart and Amazon both block scrapes from Fly data center IPs regardless of browser type; camoufox (Firefox stealth) also blocked at the IP layer
- Implemented camoufox + Google Shopping fallback in `src/scrapers/walmart.py`; camoufox works on Linux but fails on Windows (Microsoft Store Python UWP sandboxing); Google Shopping returns JS-only shell to plain requests → both fallbacks non-functional from data center
- Scraped 1 real Yellowbird Amazon row locally (before Amazon CAPTCHA started blocking)
- Loaded 300-row Cinderhaven synthetic history (5 SKUs × 2 retailers × 30 days) via `scripts/load_synthetic.py`
- Added `scripts/load_synthetic_competitors.py` — seeds 30-day price history for all 5 competitors at market-realistic prices (Truff $17.99, Marie Sharp's $6.99, Dave's $6.49, Yellowbird $7.49, Melinda's $4.99)
- Fixed `app/data.py` `get_latest_price_per_oz()` — was querying `v_latest_snapshot_per_product` for `brand_name`/`price_per_oz` columns that don't exist on that view; query now JOINs products+brands and computes price_per_oz inline
- Fixed `app/components.py` `strftime("%-d")` → `ts.day` (Windows cross-platform)
- Fixed `scrape.py` pack_weight_oz UPDATE-before-INSERT ordering bug
- Fixed Dockerfile: removed ENTRYPOINT tini (not in playwright image), updated base from v1.49.0 to v1.60.0, pinned playwright==1.60.0 to match
- Deployed version 4 successfully; dashboard health check passing

**DB state (Fly Postgres):**
- 600 total snapshots: 300 Cinderhaven + 60 per competitor × 5 brands
- 6 brands, 20 SKU/retailer combinations, 30-day history each
- price range: Cinderhaven/Yellowbird $0.76/oz → Truff $3.04/oz

**Dashboard live at:** https://competitive-shelf-intelligence.fly.dev
- Price Positioning tab: horizontal dot chart, all 6 brands, Walmart vs Amazon
- Promo, OOS, Assortment, Review tabs: query views that work against synthetic data

**For a paying client (production-ready scraping):**
- Walmart: residential proxy service ($30-50/month) — ScraperAPI was $49/month (no free tier)
- Amazon: residential proxy + ScraperAPI renders anti-bot headers correctly
- ScraperAPI key → set `SCRAPERAPI_KEY` in `flyctl secrets` and `src/scrapers/walmart.py` Transport 1 activates

**Next:**
- Demo is ready to show. No further work required unless a client engagement starts.
- When a client engages: obtain ScraperAPI or Bright Data residential proxy, set SCRAPERAPI_KEY secret, run `python scrape.py` on cron via `flyctl schedule` or Fly Machines scheduled tasks.

---
