# Competitive Shelf Intelligence

Competitive pricing, promo, and out-of-stock monitoring for specialty food brands.
Scrapes Walmart and Amazon to track price per oz, promotional activity, OOS events,
assortment changes, and review trends across the artisan sauce/condiment category.
Positions a synthetic Cinderhaven brand at the real category median price.

Delivers the competitive visibility that syndicated data (IRI/Nielsen) provides —
at a fraction of the cost.

## Stack

Python · Playwright · BeautifulSoup · Postgres · Dash · Plotly · Fly.io

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt
playwright install chromium

# 2. Configure environment
cp .env.example .env
# Fill in DATABASE_URL and SCRAPERAPI_KEY in .env

# 3. Create the database schema
psql $DATABASE_URL -f db/schema.sql

# 4. Add competitor product URLs
# Edit config/products.yaml — replace REPLACE_WITH_* placeholders
# with real Walmart and Amazon product URLs

# 5. Run a scrape
python scrape.py                   # all retailers
python scrape.py --retailer walmart
python scrape.py --dry-run         # verify without DB writes

# 6. Load synthetic Cinderhaven data (run once after first real scrape)
python scripts/load_synthetic.py

# 7. Start the dashboard
python app/run.py                  # dev server on localhost:8050
```

## Adding competitors

Edit `config/products.yaml`. Each entry needs:

```yaml
- name: "Brand Name Hot Sauce 12 oz"
  brand: "Brand Name"
  retailer: walmart           # or amazon
  url: "https://www.walmart.com/ip/..."
  retailer_id: "XXXXXXXX"    # Walmart item ID or Amazon ASIN
  upc: "012345678901"        # optional — helps cross-retailer linking
```

Walmart item IDs appear in the URL after `/ip/Product-Name/`.
Amazon ASINs are the 10-character code in `/dp/XXXXXXXXXX`.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | Postgres connection string |
| `SCRAPERAPI_KEY` | Yes (production) | ScraperAPI key for Walmart scraping |
| `PROXY_URL` | No | Residential proxy URL for Amazon scraping |
| `CINDERHAVEN_DAILY_REVENUE` | No | Avg daily revenue ($) — enables lost-revenue callout in OOS tab |

Sign up for ScraperAPI at scraperapi.com — 5,000 free trial credits.

## Deployment (Fly.io)

```bash
# One-time setup
flyctl postgres create --name competitive-shelf-pg --region iad
flyctl postgres attach competitive-shelf-pg --app competitive-shelf-intelligence
psql $DATABASE_URL -f db/schema.sql
flyctl secrets set SCRAPERAPI_KEY=your_key_here

# Deploy
flyctl deploy
```

## Running scrapers in production

The scraper is a CLI process, not part of the gunicorn app. SSH into the Fly machine
or run via `flyctl ssh console`:

```bash
python scrape.py --retailer all
```

Schedule with a cron job or Fly scheduled machines once you're happy with the data quality.

## Data contract

Canonical Cinderhaven conformance — 50 SKUs across 5 product lines and 6 contracted retailers.

## Tests

```bash
python -m pytest
```

All tests are fixture-based — no live network calls, no database required.

## Project structure

```
scrape.py                  CLI scraper
config/products.yaml       Competitor product list (edit to add competitors)
db/schema.sql              Postgres DDL — apply once
scripts/load_synthetic.py  Seed Cinderhaven synthetic data
src/
  scrapers/
    base.py                Rate limiting, robots.txt, block detection
    walmart.py             Walmart scraper (ScraperAPI + __NEXT_DATA__ JSON)
    amazon.py              Amazon scraper (CSS fallback chain)
    entity_resolution.py   UPC → canonical product mapping
  db.py                    DB connection pool
  utils.py                 parse_weight_oz()
app/
  run.py                   Dash entry point (gunicorn: app.run:server)
  tabs/                    One module per dashboard tab
```

---

Built by [Lailara LLC](https://lailarallc.com) — data hygiene and analytics consulting for specialty food brands scaling into national retail.
