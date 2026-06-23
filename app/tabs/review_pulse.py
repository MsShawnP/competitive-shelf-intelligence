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


def _build_charts(df: pd.DataFrame) -> html.Div:
    """Two-column grid of brand cards, each with stacked star + review charts."""
    brands = sorted(df["brand_name"].unique())
    cards = []

    for brand in brands:
        brand_df = df[df["brand_name"] == brand]
        rating_fig = _rating_line(brand, brand_df)
        review_fig = _review_bar(brand, brand_df)

        cards.append(
            html.Div(
                [
                    html.H4(brand, style={
                        "fontFamily": FONT_SERIF, "fontWeight": "700",
                        "fontSize": "15px", "margin": "0 0 4px 0", "color": INK,
                    }),
                    dcc.Graph(figure=rating_fig, config={"displayModeBar": False},
                              style={"marginBottom": "0"}),
                    dcc.Graph(figure=review_fig, config={"displayModeBar": False}),
                ],
                style={
                    "backgroundColor": "#faf9f6",
                    "border": "1px solid #e8e6e1",
                    "borderRadius": "2px",
                    "padding": "12px 12px 4px",
                },
            )
        )

    return html.Div(
        cards,
        style={
            "display": "grid",
            "gridTemplateColumns": "1fr 1fr",
            "gap": "16px",
        },
    )


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
            marker=dict(size=3),
            hovertemplate="%{x}: %{y:.2f} stars<extra></extra>",
        ))
    y_min = max(1, df["avg_star_rating"].min() - 0.5)
    layout = base_chart_layout(height=160, y_title="Avg Stars", show_legend=True)
    layout["yaxis"]["range"] = [y_min, 5]
    layout["yaxis"]["autorange"] = False
    layout["yaxis"]["dtick"] = 0.5
    layout["margin"] = dict(l=36, r=8, t=28, b=28)
    layout["legend"] = dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        font=dict(size=10, family=FONT_SANS),
    )
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
    layout = base_chart_layout(height=160, y_title="Reviews", show_legend=True)
    layout["margin"] = dict(l=36, r=8, t=28, b=28)
    layout["legend"] = dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        font=dict(size=10, family=FONT_SANS),
    )
    fig.update_layout(**layout)
    return fig
