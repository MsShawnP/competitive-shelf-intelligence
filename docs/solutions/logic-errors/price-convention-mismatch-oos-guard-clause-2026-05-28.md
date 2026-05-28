---
title: Dashboard Logic Bugs from Scraper/Synthetic Data Convention Mismatch
date: 2026-05-28
category: logic-errors
module: competitive-shelf-intelligence
problem_type: logic_error
component: background_job
severity: high
symptoms:
  - Promo depth percentage renders negative (e.g. -17.6%) for all synthetic competitor data
  - Promo depth renders 0% for Amazon data even when promo badges are detected
  - Walmart products with no add-to-cart button and absent availabilityStatus show as in-stock
  - Bugs return silently wrong values with no exception thrown and no log output
root_cause: logic_error
resolution_type: code_fix
related_components:
  - database
  - tooling
tags:
  - scraper
  - promo-depth
  - oos-detection
  - naming-convention
  - guard-clause
  - sql-formula
  - synthetic-data
  - price-data
---

# Dashboard Logic Bugs from Scraper/Synthetic Data Convention Mismatch

## Problem

Two dashboard logic bugs produced silently wrong data without throwing exceptions. The promo depth formula in `get_promo_summary` gave negative percentages for all synthetic data because the synthetic loader stored `sale_price_cents` as the *discounted* price while the formula assumed it was the *original/was* price — the opposite convention used by the Walmart scraper. A second bug in Walmart OOS detection used a guard clause (`availability != ""`) that blocked detection of a real OOS signal whenever `availabilityStatus` was absent from the product JSON.

## Symptoms

- Promo depth percentage renders as negative (e.g. -17.6%) for all synthetic competitor data in the Promo Summary tab
- Promo depth renders as 0% for Amazon data even when `has_promo_badge = True`
- Walmart products with no add-to-cart button and no `availabilityStatus` field incorrectly render as in-stock
- No exception is raised by either bug — wrong values are returned silently

## What Didn't Work

- **Reading only the SQL formula in isolation.** `(sale_price_cents - price_cents) / sale_price_cents * 100` looks mathematically reasonable until you trace both data sources and find they use opposite conventions for which column holds the higher value.
- **Checking only the Walmart scraper** to understand `sale_price_cents`. The Walmart scraper stores `sale_price = wasPrice.price` (the original price, higher), which made the original formula appear correct. The bug only surfaces with synthetic data, which stores `sale_price_cents = price * 0.85` (lower).
- **Treating the OOS guard clause as an intentional safety check.** `availability != ""` was added to prevent false positives. It actually blocked a real OOS signal for the exact case it was meant to refine.
- **Detecting the broken Promo tab visually.** The tab rendered empty or wrong values with no server-side log output. All `app/data.py` query functions used a bare `except Exception: return pd.DataFrame()` pattern, making a code bug indistinguishable from "no data." (session history)
- **Detecting the broken price-per-oz chart.** Same silent swallow pattern: `get_latest_price_per_oz` queried a view for columns that did not exist on it; dashboard rendered "No scrape data yet" with zero log output until the query was inspected directly. (session history)

## Solution

**F1 — Promo depth formula** (`app/data.py`, `get_promo_summary`):

```sql
-- Before: gives negative result when sale_price_cents < price_cents (synthetic data)
THEN (ps.sale_price_cents - ps.price_cents)::float / ps.sale_price_cents * 100.0

-- After: (regular - sale) / regular = positive discount %
THEN (ps.price_cents - ps.sale_price_cents)::float / ps.price_cents * 100.0
```

**F5 — Walmart OOS guard clause** (`src/scrapers/walmart.py`):

```python
# Before: guard is False when availabilityStatus absent, missing real OOS signal
is_oos_no_cart = not has_cart_button and availability != ""

# After: no cart button = not purchasable = OOS, regardless of availability field
is_oos_no_cart = not has_cart_button
```

## Why This Works

**F1**: The canonical schema semantics for this project are `price_cents` = regular/list price (higher value), `sale_price_cents` = promotional/sale price (lower value). Promo depth is `(regular - sale) / regular`. The synthetic loader makes this explicit: `sale_price_cents = round(price * 0.85)`. The Walmart scraper stores `wasPrice` (higher) as `sale_price` — effectively misusing the column name — but the formula must reflect the schema's intended meaning. The fix aligns the formula with the schema semantics.

**F5**: When `availabilityStatus` is absent from Walmart's product JSON, `(product.get("availabilityStatus") or "").upper()` produces `""`. The guard `availability != ""` is then `False`, short-circuiting the whole expression to `False` regardless of the cart button. A product is OOS if it cannot be added to cart — the availability text field is a secondary confirmation, not a prerequisite.

## Prevention

**Document column semantics when two data sources share a schema.** Add a schema comment or a constants entry for any column whose meaning is not self-evident:

```sql
-- schema.sql
COMMENT ON COLUMN price_snapshots.price_cents IS 'Regular/list price in cents (higher value)';
COMMENT ON COLUMN price_snapshots.sale_price_cents IS 'Promotional price in cents (lower value; NULL when no promo)';
```

**Unit test formulas with sign-verified values.** A test that asserts a known positive discount percentage catches inverted formulas immediately:

```python
def test_promo_depth_formula_is_positive():
    # price_cents=1000 ($10.00), sale_price_cents=850 ($8.50) → 15% discount
    regular, sale = 1000, 850
    depth = (regular - sale) / regular * 100.0
    assert depth == pytest.approx(15.0, abs=0.01)
    # Swapped operands yield -17.6%; this catches the inversion without a database
```

**Audit guard clauses that combine a positive signal with a negative filter using `and`.** When a guard mixes a detection signal (`not has_cart_button`) with a presence filter (`availability != ""`), verify the filter cannot block the signal in the field-absent case. If the filter is absent, the signal fires correctly; if the filter is present, test what happens when the filtered field is empty.

**Add `logger.exception()` before every silent exception return.** Bare `except Exception: return empty` makes code bugs invisible:

```python
# Before: exception swallowed, dashboard shows "No data" with zero log output
except Exception:
    return pd.DataFrame()

# After: full traceback logged at ERROR level
except Exception:
    logger.exception("get_promo_summary failed")
    return pd.DataFrame()
```

This rule applies to query-layer failures where returning empty data silently is wrong. Infrastructure-level fallbacks (e.g., falling back from `FileSystemCache` to `SimpleCache`) may be silent when the fallback is safe and the caller cannot distinguish them.

**Wrap stateful DB records in try/except, not bare sequential calls (REL-001).** The scrape run lifecycle had `_run_scrape(); _finish_scrape_run()` with no error handling — a crash left `status='running'` forever. The correct pattern:

```python
product_count, failure_count = 0, 0
try:
    product_count, failure_count = _run_scrape(conn, run_id, ...)
    _finish_scrape_run(conn, run_id, product_count, failure_count)
except Exception:
    logger.exception("Scrape run %d crashed; marking failed", run_id)
    _mark_run_failed(conn, run_id)
    raise
```

Also initialize any variable that an `except` block references before the `try` begins. If a loop inside `try` assigns `entry` and `BlockDetectedError` fires on the first iteration, `entry` is unbound in the handler — producing a `NameError` or logging the wrong URL. Set `entry: dict | None = None` before the `try` and guard with `entry.get("url", "") if entry else ""`.

## Related Issues

- Same silent exception pattern masked `get_latest_price_per_oz` querying a view for non-existent columns — fixed in commit `0104df9` (session history)
- All 8 query functions in `app/data.py` were missing `logger.exception()` — fixed in the same P1/P2 batch as F1 and F5
