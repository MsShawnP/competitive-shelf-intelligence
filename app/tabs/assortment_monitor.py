"""Assortment Monitor tab — new entries and possible delists vs prior run."""

from __future__ import annotations

import pandas as pd
from dash import Input, Output, dash_table, html

from app.components import empty_state, last_scraped_indicator
from app.constants import CANVAS, FONT_SANS, GREY_LIGHT, RED, TEXT_SEC, TEAL
from app.data import get_assortment_changes

TAB_ID = "tab-assortment-monitor"
TABLE_ID = "assortment-table"


def layout() -> html.Div:
    return html.Div([
        html.H2(
            "Assortment Monitor",
            style={"fontFamily": "'Playfair Display', Georgia, serif",
                   "fontWeight": "700", "fontSize": "22px", "marginBottom": "4px"},
        ),
        last_scraped_indicator(),
        html.P(
            "Products appearing or disappearing between the two most recent scrape runs.",
            style={"fontSize": "14px", "color": TEXT_SEC, "marginBottom": "20px"},
        ),
        html.Div(id=TABLE_ID),
    ], style={"padding": "24px"})


def register_callbacks(app) -> None:
    @app.callback(
        Output(TABLE_ID, "children"),
        Input("_refresh-trigger", "data"),
    )
    def update(_):
        df = get_assortment_changes()
        if df.empty:
            return empty_state("No assortment changes detected, or fewer than two scrape runs available.")
        return _build_table(df)


def _build_table(df: pd.DataFrame) -> dash_table.DataTable:
    display = df.rename(columns={
        "brand_name": "Brand",
        "product_name": "Product",
        "retailer": "Retailer",
        "first_seen_at": "First Seen",
        "last_seen_at": "Last Seen",
        "status": "Status",
    }).copy()
    display["Retailer"] = display["Retailer"].str.title()
    for col in ["First Seen", "Last Seen"]:
        if col in display.columns:
            display[col] = pd.to_datetime(display[col]).dt.strftime("%Y-%m-%d")

    return dash_table.DataTable(
        data=display.to_dict("records"),
        columns=[{"name": c, "id": c} for c in display.columns],
        style_table={"overflowX": "auto"},
        style_cell={"fontFamily": FONT_SANS, "fontSize": "13px", "padding": "8px 12px"},
        style_header={
            "fontWeight": "600",
            "backgroundColor": CANVAS,
            "borderBottom": f"2px solid {GREY_LIGHT}",
        },
        style_data_conditional=[
            {
                "if": {"filter_query": '{Status} = "New Entry"'},
                "backgroundColor": "#e4f5f0",
                "color": TEAL,
                "fontWeight": "600",
            },
            {
                "if": {"filter_query": '{Status} = "Possible Delist"'},
                "backgroundColor": "#fce8e7",
                "color": RED,
                "fontWeight": "600",
            },
        ],
        sort_action="native",
        filter_action="native",
    )
