"""Top-level callback dispatcher — registers all tab callbacks."""

from __future__ import annotations

from dash import Input, Output, callback_context, no_update

from app.layout import TABS, nav_style
from app.tabs import (
    assortment_monitor,
    oos_tracker,
    price_positioning,
    promo_activity,
    review_pulse,
)


def register_callbacks(app) -> None:
    price_positioning.register_callbacks(app)
    promo_activity.register_callbacks(app)
    oos_tracker.register_callbacks(app)
    assortment_monitor.register_callbacks(app)
    review_pulse.register_callbacks(app)

    _register_tab_switching(app)


def _register_tab_switching(app) -> None:
    content_outputs = [Output(f"content-{tid}", "style") for _, tid in TABS]
    nav_outputs = [Output(f"nav-{tid}", "style") for _, tid in TABS]
    nav_inputs = [Input(f"nav-{tid}", "n_clicks") for _, tid in TABS]

    @app.callback(content_outputs + nav_outputs, nav_inputs)
    def switch_tab(*_n_clicks):
        ctx = callback_context
        if not ctx.triggered or ctx.triggered[0]["prop_id"] == ".":
            active = TABS[0][1]
        else:
            triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
            active = triggered_id.replace("nav-", "")

        content_styles = [
            {"display": "block"} if tid == active else {"display": "none"}
            for _, tid in TABS
        ]
        nav_styles = [nav_style(tid == active) for _, tid in TABS]
        return content_styles + nav_styles
