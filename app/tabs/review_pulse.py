"""Review Pulse tab — star rating trends and review count trends per brand."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from app.charts import base_chart_layout
from app.components import date_range_toggles, empty_state, last_scraped_indicator, register_date_range_callbacks
from app.constants import (
    CANVAS, CHART_PALETTE, DATE_RANGE_DEFAULT, DATE_RANGE_OPTIONS,
    FONT_SANS, FONT_SERIF, GREY_LIGHT, INK, TEXT_SEC,
)

_ALLOWED_DAYS = frozenset(o["value"] for o in DATE_RANGE_OPTIONS)
from app.data import get_review_trends

TAB_ID = "tab-review-pulse"
CONTAINER_ID = "review-charts-container"


def layout() -> html.Div:
    return html.Div([
        last_scraped_indicator(),
        html.P(
            "Star ratings and review count trends by brand and retailer.",
            style={"fontSize": "14px", "color": TEXT_SEC, "marginBottom": "0"},
        ),
        html.Div([
            date_range_toggles("review"),
            html.Div(id=CONTAINER_ID),
        ], style={
            "backgroundColor": "#ffffff",
            "border": f"1px solid {GREY_LIGHT}",
            "borderRadius": "2px",
            "padding": "24px",
            "marginTop": "20px",
        }),
    ], style={"paddingTop": "16px"})


def register_callbacks(app) -> None:
    register_date_range_callbacks(app, "review")

    @app.callback(
        Output(CONTAINER_ID, "children"),
        Input("review-date-range", "data"),
        Input("_refresh-trigger", "data"),
    )
    def update(days, _):
        days = int(days) if days is not None else DATE_RANGE_DEFAULT
        days = days if days in _ALLOWED_DAYS else DATE_RANGE_DEFAULT
        df = get_review_trends(days)
        if df.empty:
            return empty_state("No review data yet.")
        return _build_charts(df)


def _build_charts(df: pd.DataFrame) -> list:
    brands = sorted(df["brand_name"].unique())
    rows = []

    for brand in brands:
        brand_df = df[df["brand_name"] == brand]
        rating_fig = _rating_line(brand, brand_df)
        review_fig = _review_bar(brand, brand_df)

        rows.append(html.Div(
            [
                html.H4(
                    brand,
                    style={"fontFamily": FONT_SERIF,
                           "fontWeight": "700", "fontSize": "16px",
                           "marginBottom": "8px", "marginTop": "20px"},
                ),
                html.Div(
                    [
                        html.Div(dcc.Graph(figure=rating_fig, config={"displayModeBar": False}),
                                 style={"flex": "1"}),
                        html.Div(dcc.Graph(figure=review_fig, config={"displayModeBar": False}),
                                 style={"flex": "1"}),
                    ],
                    style={"display": "flex", "gap": "16px"},
                ),
            ]
        ))
    return rows


def _rating_line(brand: str, df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for i, (retailer, sub) in enumerate(df.groupby("retailer")):
        sub = sub.sort_values("scraped_date")
        fig.add_trace(go.Scatter(
            x=sub["scraped_date"],
            y=sub["avg_star_rating"],
            mode="lines+markers",
            name=retailer.title(),
            line=dict(color=CHART_PALETTE[i % len(CHART_PALETTE)], width=2),
            marker=dict(size=6),
            hovertemplate="%{x}: %{y:.2f} stars<extra></extra>",
        ))
    layout = base_chart_layout(height=220, y_title="Avg Stars", show_legend=True)
    layout["yaxis"]["range"] = [1, 5]
    layout["yaxis"]["autorange"] = False
    layout["margin"] = dict(l=50, r=20, t=30, b=40)
    fig.update_layout(**layout)
    return fig


def _review_bar(brand: str, df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for i, (retailer, sub) in enumerate(df.groupby("retailer")):
        sub = sub.sort_values("scraped_date")
        fig.add_trace(go.Bar(
            x=sub["scraped_date"],
            y=sub["max_review_count"],
            name=retailer.title(),
            marker_color=CHART_PALETTE[i % len(CHART_PALETTE)],
            hovertemplate="%{x}: %{y:,} reviews<extra></extra>",
        ))
    layout = base_chart_layout(height=220, y_title="Reviews", show_legend=True)
    layout["margin"] = dict(l=50, r=20, t=30, b=40)
    fig.update_layout(**layout)
    return fig
