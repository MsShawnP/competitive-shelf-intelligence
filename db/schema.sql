-- competitive-shelf-intelligence database schema
-- Apply with: psql $DATABASE_URL -f db/schema.sql
-- Idempotent: all CREATE statements use IF NOT EXISTS.

-- ============================================================
-- Core reference tables
-- ============================================================

CREATE TABLE IF NOT EXISTS brands (
    id          SERIAL PRIMARY KEY,
    canonical_name  VARCHAR(255) NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS products (
    id              SERIAL PRIMARY KEY,
    brand_id        INT NOT NULL REFERENCES brands(id),
    canonical_name  VARCHAR(500) NOT NULL,
    pack_size_raw   VARCHAR(255),          -- raw string from product title
    pack_weight_oz  NUMERIC(10, 4),        -- normalized weight; price_per_oz derived at query time (R10)
    upc             VARCHAR(20),           -- for entity resolution; nullable
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (brand_id, canonical_name)
);

CREATE TABLE IF NOT EXISTS retailer_listings (
    id              SERIAL PRIMARY KEY,
    product_id      INT NOT NULL REFERENCES products(id),
    retailer        VARCHAR(20) NOT NULL CHECK (retailer IN ('amazon', 'walmart', 'synthetic')),
    retailer_id     VARCHAR(50) NOT NULL,  -- ASIN or Walmart item ID
    product_url     TEXT NOT NULL,
    first_seen_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (retailer, retailer_id)
);

-- ============================================================
-- Scrape run tracking
-- ============================================================

CREATE TABLE IF NOT EXISTS scrape_runs (
    id              SERIAL PRIMARY KEY,
    retailer        VARCHAR(20) NOT NULL,  -- 'amazon' | 'walmart' | 'all'
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at    TIMESTAMPTZ,
    status          VARCHAR(20) NOT NULL DEFAULT 'running'
                        CHECK (status IN ('running', 'complete', 'failed')),
    product_count   INT NOT NULL DEFAULT 0,
    failure_count   INT NOT NULL DEFAULT 0
);

-- ============================================================
-- Price snapshots (one row per listing per calendar day)
-- ============================================================

CREATE TABLE IF NOT EXISTS price_snapshots (
    id                  SERIAL PRIMARY KEY,
    listing_id          INT NOT NULL REFERENCES retailer_listings(id),
    scrape_run_id       INT REFERENCES scrape_runs(id),
    scraped_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    scraped_date        DATE NOT NULL,             -- DATE(scraped_at) — dedup key
    price_cents         INT NOT NULL,
    sale_price_cents    INT,                       -- NULL when no sale price detected
    has_promo_badge     BOOL NOT NULL DEFAULT FALSE,
    sale_badge_text     VARCHAR(255),
    price_drop_promo    BOOL NOT NULL DEFAULT FALSE,  -- price < prior snapshot, no badge
    is_oos              BOOL NOT NULL DEFAULT FALSE,
    oos_signal          VARCHAR(30)                -- 'oos_text' | 'no_cart_button' | NULL
                            CHECK (oos_signal IN ('oos_text', 'no_cart_button') OR oos_signal IS NULL),
    star_rating         NUMERIC(3, 2),
    review_count        INT,
    raw_html_hash       VARCHAR(64),               -- SHA-256 of fetched HTML for change detection
    UNIQUE (listing_id, scraped_date)              -- dedup: one snapshot per product × retailer × day (R9)
);

CREATE INDEX IF NOT EXISTS idx_price_snapshots_listing_date
    ON price_snapshots (listing_id, scraped_date DESC);

CREATE INDEX IF NOT EXISTS idx_price_snapshots_scraped_date
    ON price_snapshots (scraped_date DESC);

-- ============================================================
-- Manual entity resolution override
-- ============================================================

CREATE TABLE IF NOT EXISTS canonical_product_map (
    id                      SERIAL PRIMARY KEY,
    walmart_listing_id      INT REFERENCES retailer_listings(id),
    amazon_listing_id       INT REFERENCES retailer_listings(id),
    canonical_product_id    INT NOT NULL REFERENCES products(id),
    note                    VARCHAR(500),
    created_by              VARCHAR(100) NOT NULL DEFAULT 'operator',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- Scrape failure log (R6: log and continue on parse error)
-- ============================================================

CREATE TABLE IF NOT EXISTS scrape_failures (
    id              SERIAL PRIMARY KEY,
    scrape_run_id   INT REFERENCES scrape_runs(id),
    listing_id      INT REFERENCES retailer_listings(id),
    retailer        VARCHAR(20),
    url             TEXT NOT NULL,
    error_message   TEXT NOT NULL,
    failed_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- Views (no dbt in v1 — plain SQL views)
-- ============================================================

CREATE OR REPLACE VIEW v_price_per_oz AS
    SELECT
        ps.id                           AS snapshot_id,
        ps.scraped_date,
        ps.price_cents,
        ps.sale_price_cents,
        ps.has_promo_badge,
        ps.price_drop_promo,
        ps.is_oos,
        ps.star_rating,
        ps.review_count,
        rl.retailer,
        rl.retailer_id,
        rl.product_url,
        p.id                            AS product_id,
        p.canonical_name                AS product_name,
        p.pack_weight_oz,
        b.canonical_name                AS brand_name,
        CASE
            WHEN p.pack_weight_oz IS NOT NULL AND p.pack_weight_oz > 0
            THEN ps.price_cents::FLOAT / p.pack_weight_oz / 100.0
        END                             AS price_per_oz,
        ps.scrape_run_id
    FROM price_snapshots ps
    JOIN retailer_listings rl ON rl.id = ps.listing_id
    JOIN products p ON p.id = rl.product_id
    JOIN brands b ON b.id = p.brand_id;

CREATE OR REPLACE VIEW v_promo_events AS
    SELECT *
    FROM v_price_per_oz
    WHERE has_promo_badge OR price_drop_promo;

CREATE OR REPLACE VIEW v_oos_events AS
    SELECT *
    FROM v_price_per_oz
    WHERE is_oos = TRUE;

CREATE OR REPLACE VIEW v_latest_snapshot_per_product AS
    SELECT DISTINCT ON (listing_id)
        ps.*,
        rl.retailer,
        rl.retailer_id,
        rl.product_id
    FROM price_snapshots ps
    JOIN retailer_listings rl ON rl.id = ps.listing_id
    ORDER BY listing_id, scraped_date DESC, scraped_at DESC;
