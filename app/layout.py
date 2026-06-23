"""Top-level Dash layout: header + custom tab navigation with 5 tabs."""

from __future__ import annotations

from dash import dcc, html

from app.constants import CANVAS, CHICAGO, FONT_SANS, FONT_SERIF, GREY_LIGHT, INK, TEXT_SEC, WHITE
from app.tabs import (
    assortment_monitor,
    oos_tracker,
    price_positioning,
    promo_activity,
    review_pulse,
)

TABS = [
    ("Price Positioning", price_positioning.TAB_ID),
    ("Promo Activity", promo_activity.TAB_ID),
    ("OOS Tracker", oos_tracker.TAB_ID),
    ("Assortment Monitor", assortment_monitor.TAB_ID),
    ("Review Pulse", review_pulse.TAB_ID),
]


def create_layout() -> html.Div:
    default_tab = TABS[0][1]
    return html.Div(
        style={"backgroundColor": CANVAS, "minHeight": "100vh", "fontFamily": FONT_SANS},
        children=[
            dcc.Store(id="_refresh-trigger", data=1),

            html.Div(
                style={"maxWidth": "1200px", "margin": "0 auto", "padding": "0 24px"},
                children=[
                    # Page title section
                    html.Div(
                        [
                            html.Div(
                                "LAILARA LLC",
                                style={
                                    "fontSize": "11px",
                                    "letterSpacing": "0.08em",
                                    "textTransform": "uppercase",
                                    "color": TEXT_SEC,
                                    "marginBottom": "4px",
                                    "fontFamily": FONT_SANS,
                                    "fontWeight": "600",
                                },
                            ),
                            html.H1(
                                "Competitive Shelf Intelligence",
                                style={
                                    "fontFamily": FONT_SERIF,
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
                            "padding": "24px 0 16px",
                            "borderBottom": f"1px solid {GREY_LIGHT}",
                        },
                    ),

                    # Tab navigation
                    html.Div(
                        [
                            html.Button(
                                label,
                                id=f"nav-{tab_id}",
                                n_clicks=0,
                                style=nav_style(tab_id == default_tab),
                            )
                            for label, tab_id in TABS
                        ],
                        style={
                            "display": "flex",
                            "gap": "24px",
                            "borderBottom": f"1px solid {GREY_LIGHT}",
                            "padding": "0",
                            "backgroundColor": WHITE,
                        },
                    ),

                    # Tab content panels
                    html.Div(
                        price_positioning.layout(),
                        id=f"content-{price_positioning.TAB_ID}",
                        style={"display": "block"},
                    ),
                    html.Div(
                        promo_activity.layout(),
                        id=f"content-{promo_activity.TAB_ID}",
                        style={"display": "none"},
                    ),
                    html.Div(
                        oos_tracker.layout(),
                        id=f"content-{oos_tracker.TAB_ID}",
                        style={"display": "none"},
                    ),
                    html.Div(
                        assortment_monitor.layout(),
                        id=f"content-{assortment_monitor.TAB_ID}",
                        style={"display": "none"},
                    ),
                    html.Div(
                        review_pulse.layout(),
                        id=f"content-{review_pulse.TAB_ID}",
                        style={"display": "none"},
                    ),
                ],
            ),
        ],
    )


def nav_style(selected: bool = False) -> dict:
    base = {
        "fontFamily": FONT_SANS,
        "fontSize": "14px",
        "fontWeight": "600" if selected else "400",
        "color": CHICAGO if selected else TEXT_SEC,
        "padding": "12px 0",
        "background": "none",
        "border": "none",
        "borderBottom": f"3px solid {CHICAGO}" if selected else "3px solid transparent",
        "cursor": "pointer",
        "outline": "none",
    }
    return base
