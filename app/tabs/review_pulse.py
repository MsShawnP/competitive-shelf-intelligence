"""Review Pulse tab — star rating trends and review count trends per brand."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from app.charts import base_chart_layout
from app.components import date_range_toggles, empty_state, last_scraped_indicator, register_date_range_callbacks
from app.constants import (
    CANVAS, CHART_PALETTE, CHICAGO, DATE_RANGE_DEFAULT, DATE_RANGE_OPTIONS,
    FONT_SANS, FONT_SERIF, GREY_LIGHT, INK, OWN_BRAND, TEXT_SEC,
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
    """Hero card for Cinderhaven + compact competitive grid for everyone else."""
    brands = sorted(df["brand_name"].unique())
    own = OWN_BRAND
    competitors = [b for b in brands if b != own]

    children = []

    # --- Hero: Cinderhaven ---
    if own in brands:
        own_df = df[df["brand_name"] == own]
        children.append(
            html.Div(
                [
                    html.Div("YOUR BRAND", style={
                        "fontSize": "10px", "fontWeight": "600",
                        "letterSpacing": "0.08em", "color": TEXT_SEC,
                        "marginBottom": "2px",
                    }),
                    html.H3(own, style={
                        "fontFamily": FONT_SERIF, "fontWeight": "700",
                        "fontSize": "20px", "color": INK, "margin": "0 0 8px 0",
                    }),
                    html.Div(
                        [
                            html.Div(
                                dcc.Graph(
                                    figure=_hero_rating(own_df),
                                    config={"displayModeBar": False},
                                ),
                                style={"flex": "1", "minWidth": "0"},
                            ),
                            html.Div(
                                dcc.Graph(
                                    figure=_hero_reviews(own_df),
                                    config={"displayModeBar": False},
                                ),
                                style={"flex": "1", "minWidth": "0"},
                            ),
                        ],
                        style={"display": "flex", "gap": "12px"},
                    ),
                ],
                style={
                    "backgroundColor": "#ffffff",
                    "border": f"1px solid {GREY_LIGHT}",
                    "borderLeft": f"4px solid {CHICAGO}",
                    "borderRadius": "2px",
                    "padding": "16px 20px 8px",
                    "marginBottom": "20px",
                    "overflow": "hidden",
                },
            )
        )

    # --- Competitors heading ---
    if competitors:
        children.append(
            html.Div("COMPETITIVE SET", style={
                "fontSize": "11px", "fontWeight": "600",
                "letterSpacing": "0.08em", "color": TEXT_SEC,
                "marginBottom": "12px",
            }),
        )

    # --- Competitor cards: 3-column grid ---
    comp_cards = []
    for brand in competitors:
        brand_df = df[df["brand_name"] == brand]
        comp_cards.append(
            html.Div(
                [
                    html.H4(brand, style={
                        "fontFamily": FONT_SERIF, "fontWeight": "700",
                        "fontSize": "14px", "color": INK,
                        "margin": "0 0 4px 0",
                    }),
                    dcc.Graph(
                        figure=_compact_rating(brand_df),
                        config={"displayModeBar": "hover", "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
                        style={"marginBottom": "0"},
                    ),
                    dcc.Graph(
                        figure=_compact_reviews(brand_df),
                        config={"displayModeBar": "hover", "modeBarButtonsToRemove": ["lasso2d", "select2d"]},
                    ),
                ],
                style={
                    "backgroundColor": "#faf9f6",
                    "border": "1px solid #e8e6e1",
                    "borderRadius": "2px",
                    "padding": "10px 10px 2px",
                    "overflow": "hidden",
                },
            )
        )

    if comp_cards:
        children.append(
            html.Div(
                comp_cards,
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr",
                    "gap": "12px",
                },
            )
        )

    return html.Div(children)


def _hero_rating(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for i, (retailer, sub) in enumerate(df.groupby("retailer")):
        sub = sub.sort_values("scraped_date")
        fig.add_trace(go.Scatter(
            x=sub["scraped_date"], y=sub["avg_star_rating"],
            mode="lines+markers", name=retailer.title(),
            line=dict(color=CHART_PALETTE[i % len(CHART_PALETTE)], width=2),
            marker=dict(size=4),
            hovertemplate="%{x}: %{y:.2f} stars<extra></extra>",
        ))
    y_min = max(1, df["avg_star_rating"].min() - 0.5)
    layout = base_chart_layout(height=240, y_title="Avg Stars", show_legend=True)
    layout["yaxis"]["range"] = [y_min, 5]
    layout["yaxis"]["autorange"] = False
    layout["yaxis"]["dtick"] = 0.5
    layout["margin"] = dict(l=36, r=8, t=28, b=32)
    layout["legend"] = dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        font=dict(size=11, family=FONT_SANS),
    )
    fig.update_layout(**layout)
    return fig


def _hero_reviews(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for i, (retailer, sub) in enumerate(df.groupby("retailer")):
        sub = sub.sort_values("scraped_date")
        fig.add_trace(go.Bar(
            x=sub["scraped_date"], y=sub["max_review_count"],
            name=retailer.title(),
            marker_color=CHART_PALETTE[i % len(CHART_PALETTE)],
            hovertemplate="%{x}: %{y:,} reviews<extra></extra>",
        ))
    layout = base_chart_layout(height=240, y_title="Reviews", show_legend=True)
    layout["margin"] = dict(l=44, r=8, t=28, b=32)
    layout["legend"] = dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        font=dict(size=11, family=FONT_SANS),
    )
    fig.update_layout(**layout)
    return fig


def _compact_rating(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for i, (retailer, sub) in enumerate(df.groupby("retailer")):
        sub = sub.sort_values("scraped_date")
        fig.add_trace(go.Scatter(
            x=sub["scraped_date"], y=sub["avg_star_rating"],
            mode="lines", name=retailer.title(), showlegend=False,
            line=dict(color=CHART_PALETTE[i % len(CHART_PALETTE)], width=1.5),
            hovertemplate="%{x}: %{y:.2f}<extra></extra>",
        ))
    y_min = max(1, df["avg_star_rating"].min() - 0.5)
    layout = base_chart_layout(height=160, y_title="Stars", show_legend=False)
    layout["yaxis"]["range"] = [y_min, 5]
    layout["yaxis"]["autorange"] = False
    layout["yaxis"]["dtick"] = 0.5
    layout["margin"] = dict(l=30, r=4, t=4, b=24)
    layout["yaxis"]["title_font"] = dict(size=10)
    layout["yaxis"]["tickfont"] = dict(size=9)
    layout["xaxis"]["tickfont"] = dict(size=9)
    fig.update_layout(**layout)
    return fig


def _compact_reviews(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for i, (retailer, sub) in enumerate(df.groupby("retailer")):
        sub = sub.sort_values("scraped_date")
        fig.add_trace(go.Bar(
            x=sub["scraped_date"], y=sub["max_review_count"],
            name=retailer.title(), showlegend=False,
            marker_color=CHART_PALETTE[i % len(CHART_PALETTE)],
            hovertemplate="%{x}: %{y:,}<extra></extra>",
        ))
    layout = base_chart_layout(height=160, y_title="Reviews", show_legend=False)
    layout["margin"] = dict(l=36, r=4, t=4, b=24)
    layout["yaxis"]["title_font"] = dict(size=10)
    layout["yaxis"]["tickfont"] = dict(size=9)
    layout["xaxis"]["tickfont"] = dict(size=9)
    fig.update_layout(**layout)
    return fig
