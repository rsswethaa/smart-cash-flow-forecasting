# FlowWise NZ — Smart Cash-Flow & Bill Forecasting

FlowWise NZ is a working student-focused personal-finance forecasting application built around a common New Zealand budgeting problem: income, fortnightly rent, subscriptions and bills arrive on different schedules, so the current bank balance alone can be misleading.

## Working implementation

- weekly, fortnightly, monthly and one-off cash-flow scheduling
- NZ-style fortnightly rent/income modelling
- recurring-payment detection from transaction history
- daily projected balances and low-buffer dates
- expense-increase / income-reduction stress scenarios
- recommended reserve needed to protect a chosen buffer
- forecast back-testing metrics (MAE, RMSE and bias)
- explainable risk messages rather than a black-box score
- CSV forecast export
- SQLite persistence for recurring items and forecast runs
- Flask dashboard + JSON API
- unit/API tests, Docker and CI

The bundled data is demonstration data. FlowWise does not connect to a bank account and does not provide regulated financial advice.

## Run

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## API

`POST /api/forecast` accepts starting balance, safety buffer, horizon, start date and optional stress-scenario percentages. `GET /export/forecast.csv` exports the projected daily balance path.

## Why this project

This project deliberately connects applied finance with software engineering: cash-flow timing, liquidity buffers, scenario analysis, forecast error and explainability are implemented as code rather than described only in documentation.
