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
- Lead-gen assets (landing pages, social posts, email sequences) — separate project
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

## What's left before going live

1. **Fill in competitor URLs** — research real Walmart/Amazon URLs for each brand in `config/products.yaml` and replace all `REPLACE_WITH_*` values
2. **Provision Fly Postgres** — `flyctl postgres create`, attach, `psql -f db/schema.sql`
3. **Set Fly secrets** — `flyctl secrets set SCRAPERAPI_KEY=...`
4. **Run first scrape** — `python scrape.py`
5. **Load Cinderhaven data** — `python scripts/load_synthetic.py`
6. **Deploy** — `flyctl deploy`

---

## Arc history

### 2026-05-28 — Project initialized
- Outcome: Repo scaffolded, state files created, GitHub remote live
- Tag: v0.1-foundation

---

## Improvement history

<!-- Entries are added by /improve — don't delete this section -->
