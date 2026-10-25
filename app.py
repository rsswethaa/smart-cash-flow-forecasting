from __future__ import annotations

import csv
import io
import os
import sqlite3
from datetime import date
from pathlib import Path

from flask import Flask, Response, current_app, g, jsonify, render_template, request

from src.forecast import RecurringItem, apply_scenario, forecast_balance, parse_date, risk_explanation

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE = BASE_DIR / "flowwise.db"


def _connect(path):
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def bootstrap_database(db):
    db.executescript((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))
    db.executescript((BASE_DIR / "seed.sql").read_text(encoding="utf-8"))
    db.commit()


def get_db():
    if "db" not in g:
        g.db = _connect(current_app.config["DATABASE"])
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def ensure_database(app):
    path = Path(app.config["DATABASE"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(path) as db:
        exists = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='recurring_items'").fetchone()
        if exists is None:
            bootstrap_database(db)


def load_items(db):
    return [
        RecurringItem(
            row["name"], row["amount"], row["frequency"], parse_date(row["next_date"]), row["category"]
        )
        for row in db.execute("SELECT * FROM recurring_items WHERE active = 1 ORDER BY id").fetchall()
    ]


def _forecast_from_payload(payload, db):
    start = parse_date(payload.get("start_date") or date.today().isoformat())
    starting_balance = float(payload.get("starting_balance", 1200))
    safety_buffer = float(payload.get("safety_buffer", 300))
    horizon_days = int(payload.get("horizon_days", 60))
    expense_stress = float(payload.get("expense_increase_pct", 0))
    income_stress = float(payload.get("income_reduction_pct", 0))
    items = load_items(db)
    items = apply_scenario(items, expense_stress, income_stress)
    result = forecast_balance(starting_balance, items, start, horizon_days, safety_buffer)
    result["explanations"] = risk_explanation(result)
    result["scenario"] = {
        "expense_increase_pct": expense_stress,
        "income_reduction_pct": income_stress,
    }
    return result


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=Path(os.getenv("FLOWWISE_DATABASE", DEFAULT_DATABASE)),
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-flowwise-secret"),
    )
    if config:
        app.config.update(config)
    app.teardown_appcontext(close_db)
    ensure_database(app)

    @app.get("/")
    def index():
        result = _forecast_from_payload({}, get_db())
        return render_template("index.html", forecast=result, items=load_items(get_db()))

    @app.post("/api/forecast")
    def api_forecast():
        payload = request.get_json(silent=True) or {}
        try:
            result = _forecast_from_payload(payload, get_db())
        except (TypeError, ValueError) as exc:
            return jsonify({"error": str(exc)}), 400
        with get_db():
            get_db().execute(
                """
                INSERT INTO forecast_runs
                (starting_balance, safety_buffer, horizon_days, lowest_balance, ending_balance, first_below_buffer_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    result["starting_balance"], result["safety_buffer"], result["horizon_days"],
                    result["lowest_balance"], result["ending_balance"], result["first_below_buffer_date"],
                ),
            )
        return jsonify(result)

    @app.get("/api/items")
    def api_items():
        return jsonify([
            {
                "name": item.name,
                "amount": item.amount,
                "frequency": item.frequency,
                "next_date": item.next_date.isoformat(),
                "category": item.category,
            }
            for item in load_items(get_db())
        ])

    @app.get("/export/forecast.csv")
    def export_forecast():
        result = _forecast_from_payload(request.args, get_db())
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["date", "net_flow", "balance", "below_buffer", "events"])
        for row in result["rows"]:
            writer.writerow([
                row["date"], row["net_flow"], row["balance"], row["below_buffer"],
                "; ".join(f"{event['name']} ({event['amount']:+.2f})" for event in row["events"]),
            ])
        return Response(
            buffer.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=flowwise_forecast.csv"},
        )

    @app.get("/health")
    def health():
        get_db().execute("SELECT 1").fetchone()
        return jsonify({"status": "ok", "service": "flowwise-nz"})

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
