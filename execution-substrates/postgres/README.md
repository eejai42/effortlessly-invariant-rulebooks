# PostgreSQL Execution Substrate

PostgreSQL is one of the **three Effortless tools** — the only substrate with **no limitations**. The `rulebook-to-postgres` tool fully supports complex aggregations, multi-table JOINs, window functions, and all formula types. All caveats about "demonstrated" or "limited" formula support apply only to the local substrates (Python, Go, etc.), not to PostgreSQL.

This substrate tests the PostgreSQL implementation of calculated fields against the
canonical answer keys derived from the rulebook.

## How It Works

1. The rulebook formulas are compiled to SQL functions (in `/postgres/02-create-functions.sql`)
2. These functions are used in views (`/postgres/03-create-views.sql`)
3. This test runner queries those views and compares results to the answer keys

## No Privileged Position

PostgreSQL is tested **equally** with all other substrates (Python, Go, binary, etc.).
The answer keys come directly from the rulebook's seed data, not from PostgreSQL.
This ensures that a bug in the Postgres implementation would be caught, just like
any other substrate.

## Prerequisites

- PostgreSQL database running
- Database initialized with `postgres/init-db.sh`
- `psycopg2` Python package installed

## Running

```bash
# Run tests
./take-test.sh

# Or directly
python3 take-test.py
```

## Output

- `test-answers/` - Contains JSON files with computed values from PostgreSQL views
- `.last-run.log` - Log from the most recent test run
