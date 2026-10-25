# FlowWise NZ — Smart Cash-Flow & Bill Forecasting

**Status: Active development · FinTech portfolio product**

[![CI](https://github.com/rsswethaa/smart-cash-flow-forecasting/actions/workflows/ci.yml/badge.svg)](https://github.com/rsswethaa/smart-cash-flow-forecasting/actions/workflows/ci.yml)

**[Live Demo](https://swethaa-flowwise-nz.onrender.com) · [Case Study](docs/CASE_STUDY.md) · [Security](SECURITY.md) · [Source](https://github.com/rsswethaa/smart-cash-flow-forecasting)**

## The problem

A student can have money in the bank today and still run short before the next pay cycle. Rent may be fortnightly, subscriptions monthly, wages irregular, and several bills can cluster in the same week. A static monthly budget hides that timing risk.

FlowWise models **when** money moves, not only how much is spent. It projects a daily cash balance, tests the effect of income/expense shocks, and explains when the balance is expected to fall below a chosen safety buffer.

## What the application actually does

- schedules weekly, fortnightly, monthly and one-off cash flows
- models NZ-style fortnightly rent and income cycles
- detects recurring payments from transaction history
- projects daily balances over a configurable horizon
- identifies the first date below a safety buffer
- calculates the reserve needed to avoid a projected shortfall
- applies expense-increase and income-reduction stress scenarios
- back-tests forecasts with MAE, RMSE and bias
- generates plain-English risk explanations
- exports forecast paths to CSV
- persists recurring items and forecast runs in SQLite
- exposes a Flask dashboard and JSON API

### Measured evidence

The current CI suite runs **10 automated tests** covering the dashboard/API, CSV export, invalid-input handling, fortnightly scheduling, recurring-payment detection, stress scenarios, reserve warnings and back-testing.

## A finance example

Suppose a student starts with **NZ$1,200**, wants to preserve a **NZ$300 safety buffer**, receives income fortnightly, and pays rent fortnightly. FlowWise generates the balance path day by day rather than averaging those cash flows into a monthly number.

That makes questions such as these testable:

- What happens if rent increases?
- What if income falls for one pay cycle?
- How much reserve is needed to stay above the buffer?
- On which date does liquidity become tight?

## Key engineering decisions

### Daily-event forecasting instead of monthly averages

The engine applies cash flows on their actual scheduled dates. That makes pay-cycle and bill-clustering effects visible.

### Deterministic rules before black-box prediction

The current product uses transparent scheduling, recurring-payment detection and scenario calculations. This is intentional: a user should be able to understand why the forecast moved.

### SQLite for the portfolio prototype

SQLite keeps local setup and testing simple. It is appropriate for a single-instance demonstration, but a multi-user production version would move persistence to PostgreSQL and introduce migrations, connection pooling and stronger concurrency controls.

### Stress scenarios, not fake probability claims

FlowWise can apply explicit income and expense shocks. It does **not** claim a statistically calibrated probability of financial distress because the current project has not been trained or validated on a representative banking dataset.

## Architecture

```text
Browser / API client
        |
        v
     Flask app
        |
        +----> recurring items + scenario inputs
        |
        v
  forecasting engine
  - schedule expansion
  - daily balance path
  - safety-buffer checks
  - stress scenarios
  - back-testing metrics
        |
        v
     SQLite audit store
```

## API

### `POST /api/forecast`

Accepts a starting balance, safety buffer, horizon, start date and optional stress percentages. Returns the projected balance path, lowest balance, ending balance, first below-buffer date and explanations.

### `GET /api/items`

Returns the active recurring cash-flow items used by the forecast.

### `GET /export/forecast.csv`

Downloads the projected balance path as CSV.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

Docker is also supported through the included `Dockerfile`.

## Implemented vs. production extension

| Area | Current implementation | Production extension |
|---|---|---|
| Forecasting | deterministic daily cash-flow projection | probabilistic forecasting after suitable data validation |
| Recurring payments | pattern detection from transaction history | bank-feed ingestion and richer merchant normalisation |
| Scenarios | explicit income/expense shocks | saved multi-scenario planning and confidence ranges |
| Persistence | SQLite | PostgreSQL + migrations |
| Identity | single-user demo | authentication, user accounts and tenancy |
| Banking | no bank connection | consent-based open-banking integration |
| Advice | decision-support prototype | regulated-advice boundaries and compliance review where applicable |

## Limitations

- bundled data is demonstration data
- there is no live bank connection
- recurring-payment detection is heuristic, not a guaranteed classifier
- forecast quality depends on the completeness of scheduled cash flows
- this is not regulated financial advice

## Why I built it

I am studying Applied Finance after a Computer Science and Business Systems background. FlowWise is designed to sit directly at that intersection: **liquidity, cash-flow timing, scenario analysis and forecast error implemented as software rather than only described in a spreadsheet.**

See [docs/CASE_STUDY.md](docs/CASE_STUDY.md) for the design reasoning, trade-offs and next steps.
