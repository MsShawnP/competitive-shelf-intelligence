# competitive-shelf-intelligence — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal — 2026-05-28

Build a web scraping framework and Dash dashboard that monitors
competitor pricing, promo activity, availability, and reviews for real
artisan sauce/condiment brands on Amazon and Walmart — with standalone
Postgres storage and always-on deployment on Fly.io.

## Why this arc, why now

First arc: get the core working end-to-end (scraper → Postgres → dashboard
→ Fly.io). Scheduling, additional retailers, and case study content are
all deferred until the technical core is proven.

## Business question this arc answers

What are competitors doing on shelf right now — and how does a specialty
food brand's price, promo, and availability stack up against them?

## Scope

**In:**
- Python scrapers for Amazon.com and Walmart.com (both from day one)
- Real artisan sauce/condiment brands as the competitive set (scoped during build)
- Standalone Postgres for scraped data storage
- Dash dashboard: price positioning, promo activity, OOS/availability, reviews
  (Dash chosen: already deployed on Fly.io in retail-velocity-decision-tool, uses Plotly natively)
- Fly.io deployment (always-on)
- Synthetic Cinderhaven brand data as a plausible portfolio participant
- Public GitHub repo

**Out:**
- Lead-gen assets (landing pages, social posts, email sequences) — out of scope
- Cinderhaven Data Platform integration — standalone Postgres only
- Automated scraping schedule — manual runs for v1
- 90-day competitive audit as a content piece — evaluated later after data accumulates
- Instacart, Target.com — v2
- Pre-engineered findings — real data tells the real story

## Definition of done for this arc

- [x] Walmart.com proof-of-concept: retrieve product name + price for one product without being blocked
- [x] Postgres schema designed: tables, columns, scrape-run tracking, deduplication strategy
- [x] Entity resolution strategy decided: how products are matched across Amazon and Walmart
- [x] Amazon scraper runs manually and populates Postgres without errors
- [x] Walmart.com scraper runs manually and populates Postgres without errors
- [x] Competitor set defined — 5 brands × 2 retailers filled in (Yellowbird, Truff, Melinda's, Dave's Gourmet, Marie Sharp's)
- [x] Dash dashboard shows: price positioning map, promo activity, OOS/availability, review pulse
- [x] "Last scraped" timestamp visible on dashboard
- [x] Scraper error handling: bad/missing data logged as warning, not silently inserted
- [x] Cinderhaven synthetic data loads into dashboard alongside real competitor data
- [x] Dashboard deployed and live on Fly.io (Dockerfile + fly.toml complete; actual flyctl deploy pending)
- [x] README documents how to run a scrape manually and view the dashboard

## Next arc — code review fixes (2026-05-28)

Code review complete. Three confirmed P1 bugs to fix, five P2 issues, plus maintainability polish.

### P1 — Fix immediately (wrong behavior today)

- [ ] **F4** `app/data.py:152` — `get_promo_summary` WHERE uses `v.` alias but table is `ps` → Promo summary tab always empty. Fix: rename `v.` → `ps.` in WHERE.
- [ ] **F1** `app/data.py:164` — promo depth formula `(sale−price)/sale` goes negative for synthetic data, 0% for Amazon. Fix: `(price_cents − sale_price_cents) / price_cents`.
- [ ] **REL-001** `scrape.py:91–94` — no try/finally around scrape_run lifecycle. Crashed run stays `'running'` forever. Fix: wrap `_run_scrape` call in try/finally that marks run `'failed'`.

### P2 — Fix in same session

- [ ] **F5** `walmart.py:342` — Walmart OOS miss when `availabilityStatus` absent; `availability != ''` guard blocks no-cart signal.
- [ ] **REL-004** `app/data.py` — no `logger.exception` in any `except Exception` block; failures invisible.
- [ ] **REL-005** `base.py:185` — `check_robots()` hangs indefinitely; `RobotFileParser.read()` has no timeout.
- [ ] **SEC-002** `entity_resolution.py:120` — f-string column name in SQL JOIN; use `psycopg2.sql.Identifier` instead.
- [ ] **SEC-007** `app/run.py:47` — `debug=True` hardcoded; gate on `FLASK_DEBUG` env var.

### P3 — Polish pass (separate session)

- M01: `CHART_PALETTE` shadowed in `review_pulse.py`
- M02: Dead imports in `scrape.py` (`hashlib`, `datetime`, `timezone`)
- M05: `FONT_SERIF` unused constant; inconsistent serif stacks across tabs
- M06: `'Cinderhaven'` hardcoded in 3 modules — define `OWN_BRAND` constant
- M09: `listing_id` param on scrapers always `0`, never used — remove

---

## Arc history

### 2026-05-28 — Project initialized
- Outcome: Repo scaffolded, state files created, GitHub remote live
- Tag: v0.1-foundation

---

## Improvement history

<!-- Entries are added by /improve — don't delete this section -->
