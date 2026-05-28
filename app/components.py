"""Reusable Dash components — adapted from retail-velocity-decision-tool."""

from __future__ import annotations

import os
from datetime import datetime

import dash_bootstrap_components as dbc
from dash import html

from app.constants import FONT_SANS, GREY_LIGHT, RED, TEXT_SEC


def metric_card(label: str, value: str, delta: str | None = None) -> html.Div:
    children = [
        html.Div(label, style={"fontSize": "13px", "color": TEXT_SEC, "marginBottom": "4px"}),
        html.Div(value, style={"fontSize": "28px", "fontWeight": "700", "fontFamily": FONT_SANS}),
    ]
    if delta:
        children.append(html.Div(delta, style={"fontSize": "13px", "color": TEXT_SEC}))
    return html.Div(
        children,
        style={
            "background": "#ffffff",
            "border": f"1px solid {GREY_LIGHT}",
            "borderRadius": "2px",
            "padding": "16px 20px",
            "minWidth": "140px",
        },
    )


def last_scraped_indicator() -> html.Div:
    """Shows the most recent completed scrape run timestamp (R15).

    Queries lazily at render time so it reflects the actual DB state.
    """
    from app.data import get_last_scraped
    info = get_last_scraped()
    ts = info.get("completed_at")
    retailer = info.get("retailer", "")

    if ts is None:
        text = "Last scraped: no data yet"
    else:
        if isinstance(ts, datetime):
            formatted = ts.strftime("%B %-d, %Y")
        else:
            formatted = str(ts)[:10]
        retailer_label = {
            "all": "Amazon + Walmart",
            "amazon": "Amazon",
            "walmart": "Walmart",
        }.get(str(retailer).lower(), retailer)
        text = f"Last scraped: {formatted} ({retailer_label})"

    return html.Div(
        text,
        style={"fontSize": "12px", "color": TEXT_SEC, "marginTop": "6px"},
    )


def error_card(title: str, message: str) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.H5(title, style={"color": RED, "fontWeight": "600"}),
            html.P(message, style={"color": TEXT_SEC}),
        ]),
        style={"border": f"1px solid {RED}", "borderRadius": "2px"},
    )


def empty_state(message: str) -> html.Div:
    return html.Div(
        message,
        style={
            "textAlign": "center",
            "color": TEXT_SEC,
            "padding": "60px 20px",
            "fontSize": "15px",
        },
    )
