"""Price Positioning tab — horizontal dot chart, price per oz by brand × retailer.

One row per brand. Two markers per brand: Amazon (teal) and Walmart (navy).
Cinderhaven row uses a diamond marker shape. Economist conventions throughout.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from app.charts import base_chart_layout
from app.components import empty_state, error_card, last_scraped_indicator
from app.constants import (
    CANVAS,
    CHICAGO,
    COLOR_AMAZON,
    COLOR_WALMART,
    FONT_SANS,
    INK,
    TEXT_SEC,
)
from app.data import get_latest_price_per_oz

TAB_ID = "tab-price-positioning"
GRAPH_ID = "price-positioning-chart"


def layout() -> html.Div:
    return html.Div([
        html.H2(
            "Price Positioning",
            style={"fontFamily": f"'Playfair Display', Georgia, serif", "fontWeight": "700",
                   "fontSize": "22px", "marginBottom": "4px"},
        ),
        last_scraped_indicator(),
        html.P(
            "Current price per ounce by brand and retailer. "
            "Cinderhaven shown as diamond markers.",
            style={"fontSize": "14px", "color": TEXT_SEC, "marginBottom": "20px"},
        ),
        dcc.Graph(id=GRAPH_ID, config={"displayModeBar": False}),
    ], style={"padding": "24px"})


def register_callbacks(app) -> None:
    @app.callback(
        Output(GRAPH_ID, "figure"),
        Input("_refresh-trigger", "data"),
    )
    def update_chart(_):
        df = get_latest_price_per_oz()
        if df.empty:
            fig = go.Figure()
            fig.update_layout(
                **base_chart_layout(height=200),
                annotations=[{
                    "text": "No scrape data yet. Run python scrape.py to collect data.",
                    "xref": "paper", "yref": "paper",
                    "x": 0.5, "y": 0.5, "showarrow": False,
                    "font": {"family": FONT_SANS, "size": 14, "color": TEXT_SEC},
                }],
            )
            return fig
        return _build_figure(df)


def _build_figure(df: pd.DataFrame) -> go.Figure:
    brands = sorted(df["brand_name"].unique())
    n_brands = len(brands)
    height = max(300, n_brands * 60 + 80)

    fig = go.Figure()

    for retailer, color, symbol_base in [
        ("walmart", COLOR_WALMART, "circle"),
        ("amazon",  COLOR_AMAZON,  "circle"),
    ]:
        sub = df[df["retailer"] == retailer]
        for _, row in sub.iterrows():
            is_cinderhaven = "Cinderhaven" in str(row["brand_name"])
            symbol = "diamond" if is_cinderhaven else symbol_base
            label_weight = 700 if is_cinderhaven else 400

            fig.add_trace(go.Scatter(
                x=[row["price_per_oz"]],
                y=[row["brand_name"]],
                mode="markers+text",
                marker=dict(
                    symbol=symbol,
                    size=12 if is_cinderhaven else 10,
                    color=color,
                    line=dict(width=1, color=CANVAS),
                ),
                text=[f"${row['price_per_oz']:.2f}/oz"],
                textposition="middle right",
                textfont=dict(family=FONT_SANS, size=11, color=INK),
                name=f"{retailer.title()} — {row['brand_name']}",
                showlegend=False,
                hovertemplate=(
                    f"<b>{row['brand_name']}</b><br>"
                    f"{retailer.title()}: ${row['current_price']:.2f}<br>"
                    f"${row['price_per_oz']:.2f}/oz<extra></extra>"
                ),
            ))

    # Legend traces (one per retailer)
    for retailer, color, label in [
        ("walmart", COLOR_WALMART, "Walmart"),
        ("amazon",  COLOR_AMAZON,  "Amazon"),
    ]:
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(symbol="circle", size=10, color=color),
            name=label,
            showlegend=True,
        ))

    layout = base_chart_layout(
        height=height,
        x_title="Price per oz ($)",
        show_legend=True,
        left_margin=160,
    )
    layout["yaxis"]["autorange"] = "reversed"
    layout["xaxis"]["tickprefix"] = "$"
    layout["xaxis"]["tickformat"] = ".2f"
    layout["legend"] = dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        font=dict(family=FONT_SANS, size=12),
    )
    fig.update_layout(**layout)
    return fig
