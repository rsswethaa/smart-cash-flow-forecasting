import unittest
from datetime import date

from src.forecast import (
    RecurringItem,
    apply_scenario,
    backtest_balances,
    detect_recurring_payments,
    forecast_balance,
    occurrence_dates,
)


class ForecastEngineTests(unittest.TestCase):
    def test_fortnightly_rent_and_income(self):
        items = [
            RecurringItem("Pay", 700, "fortnightly", date(2026, 10, 30), "Income"),
            RecurringItem("Rent", -480, "fortnightly", date(2026, 10, 30), "Housing"),
        ]
        result = forecast_balance(1000, items, date(2026, 10, 25), 30, 300)
        self.assertEqual(result["ending_balance"], 1440.0)
        self.assertEqual(result["days_below_buffer"], 0)
        rent_dates = occurrence_dates(items[1], date(2026, 10, 25), date(2026, 11, 30))
        self.assertEqual(rent_dates[:3], [date(2026, 10, 30), date(2026, 11, 13), date(2026, 11, 27)])

    def test_low_balance_warning_and_reserve(self):
        items = [RecurringItem("Rent", -900, "once", date(2026, 10, 26), "Housing")]
        result = forecast_balance(1000, items, date(2026, 10, 25), 5, 300)
        self.assertEqual(result["first_below_buffer_date"], "2026-10-26")
        self.assertEqual(result["recommended_extra_reserve"], 200.0)

    def test_stress_scenario_changes_income_and_expenses(self):
        items = [
            RecurringItem("Pay", 1000, "monthly", date(2026, 11, 1), "Income"),
            RecurringItem("Rent", -500, "monthly", date(2026, 11, 1), "Housing"),
        ]
        adjusted = apply_scenario(items, expense_increase_pct=10, income_reduction_pct=20)
        self.assertEqual(adjusted[0].amount, 800)
        self.assertAlmostEqual(adjusted[1].amount, -550)

    def test_recurring_detector_finds_fortnightly_subscription(self):
        transactions = [
            {"date": "2026-09-01", "description": "Gym", "amount": -24.90},
            {"date": "2026-09-15", "description": "Gym", "amount": -24.90},
            {"date": "2026-09-29", "description": "Gym", "amount": -25.10},
            {"date": "2026-10-13", "description": "Gym", "amount": -24.90},
            {"date": "2026-10-10", "description": "One off", "amount": -80},
        ]
        detected = detect_recurring_payments(transactions)
        self.assertEqual(len(detected), 1)
        self.assertEqual(detected[0]["frequency"], "fortnightly")
        self.assertGreater(detected[0]["confidence"], .9)

    def test_backtest_metrics(self):
        metrics = backtest_balances([100, 110, 120], [90, 115, 120])
        self.assertEqual(metrics["n"], 3)
        self.assertAlmostEqual(metrics["mae"], 5.0)
        self.assertGreater(metrics["rmse"], metrics["mae"])

    def test_invalid_non_finite_balance_rejected(self):
        with self.assertRaises(ValueError):
            forecast_balance(float("nan"), [], date(2026, 10, 25))


if __name__ == "__main__":
    unittest.main()
