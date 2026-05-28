"""Top-level callback dispatcher — registers all tab callbacks."""

from __future__ import annotations

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
