DROP TABLE IF EXISTS forecast_runs;
DROP TABLE IF EXISTS recurring_items;

CREATE TABLE recurring_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    amount REAL NOT NULL CHECK (amount != 0),
    frequency TEXT NOT NULL CHECK (frequency IN ('weekly','fortnightly','monthly','once')),
    next_date TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'Other',
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1))
);

CREATE TABLE forecast_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    starting_balance REAL NOT NULL,
    safety_buffer REAL NOT NULL,
    horizon_days INTEGER NOT NULL,
    lowest_balance REAL NOT NULL,
    ending_balance REAL NOT NULL,
    first_below_buffer_date TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
