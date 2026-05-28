"""Top-level Dash layout: header + dcc.Tabs with 5 tabs."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from app.constants import CANVAS, CHICAGO, FONT_SANS, GREY_LIGHT, INK, TEXT_SEC
from app.tabs import (
    assortment_monitor,
    oos_tracker,
    price_positioning,
    promo_activity,
    review_pulse,
)


def create_layout() -> html.Div:
    return html.Div(
        style={"backgroundColor": CANVAS, "minHeight": "100vh", "fontFamily": FONT_SANS},
        children=[
            # Hidden store to trigger initial data load
            dcc.Store(id="_refresh-trigger", data=1),

            # Header
            html.Div(
                [
                    html.H1(
                        "Competitive Shelf Intelligence",
                        style={
                            "fontFamily": "'Playfair Display', Georgia, serif",
                            "fontWeight": "700",
                            "fontSize": "26px",
                            "color": INK,
                            "margin": "0 0 4px 0",
                        },
                    ),
                    html.P(
                        "Pricing · Promotions · Out-of-Stock · Assortment · Reviews",
                        style={
                            "fontFamily": FONT_SANS,
                            "fontSize": "13px",
                            "color": TEXT_SEC,
                            "letterSpacing": "0.04em",
                            "textTransform": "uppercase",
                            "margin": "0",
                        },
                    ),
                ],
                style={
                    "padding": "24px 32px 16px",
                    "borderBottom": f"1px solid {GREY_LIGHT}",
                    "backgroundColor": CANVAS,
                },
            ),

            # Tabs
            dcc.Tabs(
                id="main-tabs",
                value=price_positioning.TAB_ID,
                style={"borderBottom": f"1px solid {GREY_LIGHT}"},
                colors={"border": GREY_LIGHT, "primary": CHICAGO, "background": CANVAS},
                children=[
                    dcc.Tab(
                        label="Price Positioning",
                        value=price_positioning.TAB_ID,
                        children=price_positioning.layout(),
                        style=_tab_style(),
                        selected_style=_tab_selected_style(),
                    ),
                    dcc.Tab(
                        label="Promo Activity",
                        value=promo_activity.TAB_ID,
                        children=promo_activity.layout(),
                        style=_tab_style(),
                        selected_style=_tab_selected_style(),
                    ),
                    dcc.Tab(
                        label="OOS Tracker",
                        value=oos_tracker.TAB_ID,
                        children=oos_tracker.layout(),
                        style=_tab_style(),
                        selected_style=_tab_selected_style(),
                    ),
                    dcc.Tab(
                        label="Assortment Monitor",
                        value=assortment_monitor.TAB_ID,
                        children=assortment_monitor.layout(),
                        style=_tab_style(),
                        selected_style=_tab_selected_style(),
                    ),
                    dcc.Tab(
                        label="Review Pulse",
                        value=review_pulse.TAB_ID,
                        children=review_pulse.layout(),
                        style=_tab_style(),
                        selected_style=_tab_selected_style(),
                    ),
                ],
            ),
        ],
    )


def _tab_style() -> dict:
    return {
        "fontFamily": FONT_SANS,
        "fontSize": "14px",
        "padding": "12px 20px",
        "backgroundColor": CANVAS,
        "color": TEXT_SEC,
        "border": "none",
        "borderBottom": f"2px solid transparent",
    }


def _tab_selected_style() -> dict:
    return {
        **_tab_style(),
        "color": CHICAGO,
        "fontWeight": "600",
        "borderBottom": f"2px solid {CHICAGO}",
    }
