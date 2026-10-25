from __future__ import annotations

import calendar
import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from statistics import median
from typing import Iterable


VALID_FREQUENCIES = {"weekly", "fortnightly", "monthly", "once"}


@dataclass(frozen=True)
class RecurringItem:
    name: str
    amount: float
    frequency: str
    next_date: date
    category: str = "Other"

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("name is required")
        if self.frequency not in VALID_FREQUENCIES:
            raise ValueError(f"unsupported frequency: {self.frequency}")
        if not math.isfinite(float(self.amount)) or float(self.amount) == 0:
            raise ValueError("amount must be a finite non-zero number")
        if not isinstance(self.next_date, date):
            raise ValueError("next_date must be a date")


def parse_date(value) -> date:
    if isinstance(value, date):
        return value
    return datetime.fromisoformat(str(value)).date()


def _add_month(value: date) -> date:
    year = value.year + (1 if value.month == 12 else 0)
    month = 1 if value.month == 12 else value.month + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def occurrence_dates(item: RecurringItem, start_date: date, end_date: date) -> list[date]:
    current = item.next_date
    dates = []
    guard = 0
    while current < start_date and item.frequency != "once":
        current = _next_date(current, item.frequency)
        guard += 1
        if guard > 10000:
            raise RuntimeError("recurrence guard exceeded")
    if item.frequency == "once" and current < start_date:
        return []
    while current <= end_date:
        if current >= start_date:
            dates.append(current)
        if item.frequency == "once":
            break
        current = _next_date(current, item.frequency)
    return dates


def _next_date(current: date, frequency: str) -> date:
    if frequency == "weekly":
        return current + timedelta(days=7)
    if frequency == "fortnightly":
        return current + timedelta(days=14)
    if frequency == "monthly":
        return _add_month(current)
    if frequency == "once":
        return current
    raise ValueError(f"unsupported frequency: {frequency}")


def forecast_balance(
    starting_balance: float,
    items: Iterable[RecurringItem],
    start_date: date,
    horizon_days: int = 60,
    safety_buffer: float = 300.0,
) -> dict:
    starting_balance = float(starting_balance)
    safety_buffer = float(safety_buffer)
    if not math.isfinite(starting_balance):
        raise ValueError("starting_balance must be finite")
    if not math.isfinite(safety_buffer) or safety_buffer < 0:
        raise ValueError("safety_buffer must be finite and non-negative")
    if not 1 <= int(horizon_days) <= 366:
        raise ValueError("horizon_days must be between 1 and 366")

    start_date = parse_date(start_date)
    end_date = start_date + timedelta(days=int(horizon_days) - 1)
    events_by_date: dict[date, list[dict]] = {}
    for item in items:
        for event_date in occurrence_dates(item, start_date, end_date):
            events_by_date.setdefault(event_date, []).append(
                {"name": item.name, "amount": float(item.amount), "category": item.category}
            )

    rows = []
    balance = starting_balance
    for offset in range(int(horizon_days)):
        current = start_date + timedelta(days=offset)
        events = events_by_date.get(current, [])
        net_flow = sum(event["amount"] for event in events)
        balance += net_flow
        rows.append(
            {
                "date": current.isoformat(),
                "net_flow": round(net_flow, 2),
                "balance": round(balance, 2),
                "below_buffer": balance < safety_buffer,
                "events": events,
            }
        )

    lowest = min(rows, key=lambda row: row["balance"])
    below = [row for row in rows if row["below_buffer"]]
    first_below = below[0]["date"] if below else None
    reserve_needed = max(0.0, safety_buffer - float(lowest["balance"]))
    return {
        "starting_balance": round(starting_balance, 2),
        "safety_buffer": round(safety_buffer, 2),
        "horizon_days": int(horizon_days),
        "lowest_balance": float(lowest["balance"]),
        "lowest_balance_date": lowest["date"],
        "first_below_buffer_date": first_below,
        "days_below_buffer": len(below),
        "recommended_extra_reserve": round(reserve_needed, 2),
        "ending_balance": float(rows[-1]["balance"]),
        "rows": rows,
    }


def apply_scenario(
    items: Iterable[RecurringItem],
    expense_increase_pct: float = 0.0,
    income_reduction_pct: float = 0.0,
) -> list[RecurringItem]:
    expense_factor = 1 + float(expense_increase_pct) / 100
    income_factor = 1 - float(income_reduction_pct) / 100
    if expense_factor < 0 or not 0 <= income_factor <= 1:
        raise ValueError("scenario percentages are out of range")
    adjusted = []
    for item in items:
        amount = item.amount * (income_factor if item.amount > 0 else expense_factor)
        adjusted.append(
            RecurringItem(item.name, amount, item.frequency, item.next_date, item.category)
        )
    return adjusted


def detect_recurring_payments(transactions: list[dict]) -> list[dict]:
    """Detect stable outgoing recurring payments from transaction history.

    Transactions require date, description and amount. Outgoing amounts should be
    negative. At least three occurrences are required so a single coincidence is not
    labelled recurring.
    """
    groups: dict[str, list[tuple[date, float]]] = {}
    for transaction in transactions:
        amount = float(transaction["amount"])
        if not math.isfinite(amount) or amount >= 0:
            continue
        description = str(transaction.get("description", "")).strip().lower()
        if not description:
            continue
        groups.setdefault(description, []).append((parse_date(transaction["date"]), amount))

    results = []
    for description, entries in groups.items():
        entries.sort(key=lambda value: value[0])
        if len(entries) < 3:
            continue
        gaps = [(entries[i][0] - entries[i - 1][0]).days for i in range(1, len(entries))]
        med_gap = median(gaps)
        frequency = None
        expected = None
        for candidate, days, tolerance in (
            ("weekly", 7, 2),
            ("fortnightly", 14, 3),
            ("monthly", 30, 4),
        ):
            if abs(med_gap - days) <= tolerance:
                frequency, expected = candidate, days
                break
        if frequency is None:
            continue
        amounts = [abs(value[1]) for value in entries]
        avg = sum(amounts) / len(amounts)
        max_deviation = max(abs(value - avg) for value in amounts) / avg if avg else 1.0
        gap_deviation = sum(abs(gap - expected) for gap in gaps) / (len(gaps) * expected)
        confidence = max(0.0, min(1.0, 1 - 0.6 * max_deviation - 0.4 * gap_deviation))
        if confidence < 0.65:
            continue
        results.append(
            {
                "description": description,
                "frequency": frequency,
                "average_amount": round(avg, 2),
                "occurrences": len(entries),
                "confidence": round(confidence, 3),
                "last_seen": entries[-1][0].isoformat(),
                "next_expected": _next_date(entries[-1][0], frequency).isoformat(),
            }
        )
    return sorted(results, key=lambda row: (-row["confidence"], row["description"]))


def backtest_balances(predicted: list[float], actual: list[float]) -> dict:
    if len(predicted) != len(actual) or not predicted:
        raise ValueError("predicted and actual must be non-empty and the same length")
    errors = [float(p) - float(a) for p, a in zip(predicted, actual)]
    if not all(math.isfinite(error) for error in errors):
        raise ValueError("balances must be finite")
    mae = sum(abs(error) for error in errors) / len(errors)
    rmse = math.sqrt(sum(error * error for error in errors) / len(errors))
    bias = sum(errors) / len(errors)
    return {"mae": round(mae, 2), "rmse": round(rmse, 2), "bias": round(bias, 2), "n": len(errors)}


def risk_explanation(forecast: dict) -> list[str]:
    messages = []
    if forecast["days_below_buffer"]:
        messages.append(
            f"Projected balance falls below the ${forecast['safety_buffer']:.0f} buffer on "
            f"{forecast['first_below_buffer_date']}."
        )
        messages.append(
            f"An extra reserve of about ${forecast['recommended_extra_reserve']:.2f} would keep the "
            "lowest projected balance at the chosen buffer."
        )
    else:
        messages.append("Projected balance remains above the selected safety buffer for this horizon.")
    messages.append(
        f"Lowest projected balance is ${forecast['lowest_balance']:.2f} on {forecast['lowest_balance_date']}."
    )
    return messages
