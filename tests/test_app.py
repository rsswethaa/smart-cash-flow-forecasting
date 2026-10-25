import tempfile
import unittest
from pathlib import Path

from app import create_app


class FlowWiseAppTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.database = Path(self.tempdir.name) / "flowwise-test.db"
        self.app = create_app({"TESTING": True, "DATABASE": self.database})
        self.client = self.app.test_client()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_dashboard_and_health(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"FlowWise NZ", response.data)
        health = self.client.get("/health")
        self.assertEqual(health.get_json()["status"], "ok")

    def test_forecast_api_persists_run(self):
        response = self.client.post(
            "/api/forecast",
            json={
                "starting_balance": 900,
                "safety_buffer": 250,
                "horizon_days": 30,
                "expense_increase_pct": 10,
                "income_reduction_pct": 5,
                "start_date": "2026-10-25",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["horizon_days"], 30)
        self.assertIn("recommended_extra_reserve", payload)
        self.assertIn("explanations", payload)

    def test_csv_export(self):
        response = self.client.get("/export/forecast.csv?start_date=2026-10-25&horizon_days=14")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        self.assertIn(b"date,net_flow,balance", response.data)

    def test_invalid_forecast_returns_400(self):
        response = self.client.post("/api/forecast", json={"starting_balance": "not-a-number"})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
