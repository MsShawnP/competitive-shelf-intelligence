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
