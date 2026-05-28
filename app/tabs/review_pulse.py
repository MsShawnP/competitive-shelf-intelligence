"""Review Pulse tab — star rating trends and review count trends per brand."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from app.charts import base_chart_layout
from app.components import empty_state, last_scraped_indicator
from app.constants import (
    CANVAS, CHART_PALETTE, DATE_RANGE_DEFAULT, DATE_RANGE_OPTIONS,
    FONT_SANS, GREY_LIGHT, INK, TEXT_SEC,
)
from app.data import get_review_trends

TAB_ID = "tab-review-pulse"
CONTAINER_ID = "review-charts-container"

# Expose a named constant so callbacks.py can reference it
CHART_PALETTE = [
    "#1f2e7a", "#0c6552", "#7e1f34", "#7a3d10", "#8e0b07",
    "#8e9ad0", "#6dcdb5", "#e68a9a",
]


def layout() -> html.Div:
    return html.Div([
        html.H2(
            "Review Pulse",
            style={"fontFamily": "'Playfair Display', Georgia, serif",
                   "fontWeight": "700", "fontSize": "22px", "marginBottom": "4px"},
        ),
        last_scraped_indicator(),
        html.Div([
            html.Span("Date range: ", style={"fontSize": "13px", "color": TEXT_SEC}),
            dcc.RadioItems(
                id="review-date-range",
                options=DATE_RANGE_OPTIONS,
                value=DATE_RANGE_DEFAULT,
                inline=True,
                style={"fontSize": "13px", "display": "inline-block", "marginLeft": "8px"},
            ),
        ], style={"marginBottom": "16px"}),
        html.Div(id=CONTAINER_ID),
    ], style={"padding": "24px"})


def register_callbacks(app) -> None:
    @app.callback(
        Output(CONTAINER_ID, "children"),
        Input("review-date-range", "value"),
        Input("_refresh-trigger", "data"),
    )
    def update(days, _):
        df = get_review_trends(days or 0)
        if df.empty:
            return empty_state("No review data yet.")
        return _build_charts(df)


def _build_charts(df: pd.DataFrame) -> list:
    """One row per brand: star rating line chart + review count bar chart."""
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
                    style={"fontFamily": "'Playfair Display', Georgia, serif",
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
