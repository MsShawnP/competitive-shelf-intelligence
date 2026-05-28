"""Tests for scripts/load_synthetic.py. All DB calls mocked."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock, patch, call

import pytest
from click.testing import CliRunner

from scripts.load_synthetic import (
    _compute_category_median,
    _insert_history,
    _upsert_brand,
    _upsert_listing,
    _upsert_product,
    main,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _mock_conn(*fetchone_results, fetchall_result=None):
    cur = MagicMock()
    cur.fetchone.side_effect = list(fetchone_results)
    if fetchall_result is not None:
        cur.fetchall.return_value = fetchall_result
    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn, cur


# ------------------------------------------------------------------
# _compute_category_median
# ------------------------------------------------------------------

def test_compute_category_median_returns_median_of_price_per_oz():
    conn, cur = _mock_conn()
    cur.fetchall.return_value = [(1.0,), (2.0,), (3.0,)]
    result = _compute_category_median(conn)
    assert result == pytest.approx(2.0)


def test_compute_category_median_returns_none_when_no_rows():
    conn, cur = _mock_conn()
    cur.fetchall.return_value = []
    result = _compute_category_median(conn)
    assert result is None


def test_compute_category_median_handles_even_count():
    conn, cur = _mock_conn()
    cur.fetchall.return_value = [(1.0,), (2.0,), (3.0,), (4.0,)]
    result = _compute_category_median(conn)
    assert result == pytest.approx(2.5)


# ------------------------------------------------------------------
# _upsert_brand / _upsert_product / _upsert_listing
# ------------------------------------------------------------------

def test_upsert_brand_returns_id():
    conn, cur = _mock_conn((5,))
    assert _upsert_brand(conn) == 5
    sql, params = cur.execute.call_args[0]
    assert "INSERT INTO brands" in sql
    assert "Cinderhaven" in params


def test_upsert_product_uses_on_conflict():
    conn, cur = _mock_conn((10,))
    sku = {"name": "Cinderhaven Original 8 oz", "pack_size_raw": "Cinderhaven Original 8 oz", "weight_oz": 8.0}
    product_id = _upsert_product(conn, brand_id=5, sku=sku, median_price_per_oz=1.0)
    assert product_id == 10
    sql, _ = cur.execute.call_args[0]
    assert "ON CONFLICT" in sql


def test_upsert_listing_upserts_both_retailers():
    conn_w, cur_w = _mock_conn((20,))
    conn_a, cur_a = _mock_conn((21,))

    walmart_id = _upsert_listing(conn_w, 10, "walmart", "CW001", "https://walmart.com/ip/CW001")
    amazon_id  = _upsert_listing(conn_a, 10, "amazon",  "B0CIN01", "https://amazon.com/dp/B0CIN01")

    assert walmart_id == 20
    assert amazon_id == 21


# ------------------------------------------------------------------
# _insert_history
# ------------------------------------------------------------------

def test_insert_history_inserts_correct_number_of_rows():
    conn, cur = _mock_conn()
    _insert_history(conn, listing_id=1, base_price_cents=897, days=10)
    assert cur.execute.call_count == 10


def test_insert_history_uses_on_conflict_do_nothing():
    conn, cur = _mock_conn()
    _insert_history(conn, listing_id=1, base_price_cents=897, days=5)
    for c in cur.execute.call_args_list:
        sql = c[0][0]
        assert "ON CONFLICT" in sql
        assert "DO NOTHING" in sql


def test_insert_history_is_deterministic():
    """Same listing_id + days → same OOS/promo pattern on every run."""
    conn1, cur1 = _mock_conn()
    conn2, cur2 = _mock_conn()
    _insert_history(conn1, listing_id=3, base_price_cents=1000, days=15)
    _insert_history(conn2, listing_id=3, base_price_cents=1000, days=15)
    calls1 = [str(c) for c in cur1.execute.call_args_list]
    calls2 = [str(c) for c in cur2.execute.call_args_list]
    assert calls1 == calls2


# ------------------------------------------------------------------
# CLI integration: dry-run should not call get_conn for writes
# ------------------------------------------------------------------

@patch("scripts.load_synthetic.get_conn")
def test_dry_run_shows_preview_without_db_writes(mock_get_conn):
    conn, cur = _mock_conn()
    cur.fetchall.return_value = [(1.5,), (2.0,), (2.5,)]
    mock_get_conn.return_value.__enter__ = MagicMock(return_value=conn)
    mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)

    runner = CliRunner()
    result = runner.invoke(main, ["--dry-run"])

    assert result.exit_code == 0
    assert "dry-run" in result.output
    # In dry-run mode get_conn is only called once (for median query)
    assert mock_get_conn.call_count == 1


@patch("scripts.load_synthetic.get_conn")
def test_main_exits_early_when_no_competitor_data(mock_get_conn):
    conn, cur = _mock_conn()
    cur.fetchall.return_value = []
    mock_get_conn.return_value.__enter__ = MagicMock(return_value=conn)
    mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)

    runner = CliRunner()
    result = runner.invoke(main, [])

    assert result.exit_code == 0
    assert "Run python scrape.py first" in result.output
