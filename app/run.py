"""Dash app entry point.

Init order: load_dotenv → Dash → cache → layout → callbacks → health route.
Matches retail-velocity-decision-tool/app/run.py pattern exactly.
"""

from __future__ import annotations

import pathlib
from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")

import dash_bootstrap_components as dbc
from dash import Dash
from flask import jsonify

from app.callbacks import register_callbacks
from app.data import cache, init_cache
from app.layout import create_layout

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
)
server = app.server
init_cache(server)

app.layout = create_layout()
register_callbacks(app)


@server.route("/health")
def health():
    try:
        from app.db import get_conn
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT 1")
        return jsonify({"status": "ok"})
    except Exception:
        return jsonify({"status": "db_unavailable"}), 503


if __name__ == "__main__":
    app.run(debug=True, port=8050)
