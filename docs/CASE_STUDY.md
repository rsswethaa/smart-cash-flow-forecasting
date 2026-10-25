# FlowWise NZ — Case Study

## Problem

A current bank balance does not answer the question a student actually cares about: **will I still have enough money after the next rent payment, subscription cluster and pay cycle?**

The problem is fundamentally temporal. A monthly budget can look healthy while the daily cash path briefly falls below a safe level.

## User

The primary prototype user is a student in New Zealand with a mix of fortnightly income, fortnightly rent, monthly bills, subscriptions and occasional one-off costs.

## Requirements

The first working version needed to:

1. represent recurring cash flows with different frequencies;
2. project a balance day by day;
3. make fortnightly NZ-style rent/pay cycles explicit;
4. warn when liquidity falls below a chosen safety buffer;
5. support simple stress scenarios;
6. explain outputs rather than produce an unexplained score;
7. remain testable without external financial APIs.

## Design

The core domain object is a recurring cash-flow item containing a name, signed amount, frequency, next date and category. The forecast engine expands those items across a horizon and applies them to the balance on the scheduled dates.

This design was chosen because it makes the calculation auditable: if the balance changes on a date, the user can trace that movement back to an event.

## Financial logic

### Liquidity buffer

The safety buffer is treated as a user-defined minimum cash reserve. FlowWise identifies the first forecast date below that threshold and calculates how much additional reserve would be required to keep the projected minimum at or above it.

### Stress scenarios

Two deterministic shocks are currently implemented:

- expense increase percentage;
- income reduction percentage.

This supports questions such as “what if rent and bills rise?” or “what if I earn less this fortnight?” without presenting the output as a calibrated probability.

### Forecast back-testing

The project includes MAE, RMSE and bias calculations so forecast quality can be evaluated when actual outcomes are available. These metrics are preferable to claiming accuracy without evidence.

## Recurring-payment detection

A lightweight detector looks for repeated transaction patterns and can identify regular intervals such as fortnightly payments. This is a portfolio implementation rather than a production merchant-classification system, so confidence is interpreted as a pattern signal rather than a guarantee.

## Engineering decisions

### Why Flask?

The product needed a small web/API layer around a Python finance engine. Flask keeps the boundary simple and makes it easy to test the forecasting logic independently of the UI.

### Why SQLite?

For a single-user portfolio deployment, SQLite reduces setup friction and keeps tests deterministic. It is not the intended database for a multi-user financial product. PostgreSQL with migrations would be the next persistence step.

### Why deterministic first?

A transparent rule-based engine is easier to validate and explain than a model trained on unsuitable or invented data. Statistical or ML forecasting should be added only when there is a defensible dataset and evaluation design.

## Testing

The CI suite currently runs 10 automated tests covering:

- dashboard and health endpoints;
- forecast API persistence;
- invalid API input;
- CSV export;
- fortnightly income and rent scheduling;
- non-finite balance validation;
- low-balance and reserve calculations;
- recurring-payment detection;
- stress scenarios;
- back-testing metrics.

## Result

The prototype now demonstrates an end-to-end finance product flow:

**cash-flow assumptions → schedule expansion → daily projection → liquidity warning → stress scenario → explanation → export**.

A live demo is available at https://swethaa-flowwise-nz.onrender.com.

## Limitations

- no bank-feed integration;
- no production authentication or tenant isolation;
- no probabilistic shortfall model;
- no calibrated financial-health score;
- SQLite is not designed for the intended production concurrency level;
- bundled data is demonstrative rather than personal banking data.

## Next steps

The most valuable next steps are not decorative UI changes. They are deeper finance/data capabilities:

1. PostgreSQL + migration workflow;
2. authenticated user accounts and isolated financial data;
3. richer transaction categorisation and merchant normalisation;
4. rolling savings-rate and subscription-burden metrics;
5. bill-clustering analysis;
6. saved multi-scenario comparison;
7. confidence ranges once sufficient historical data exists;
8. consent-based open-banking integration architecture;
9. portfolio-level privacy and retention controls.
