# PostgreSQL Execution Substrate

PostgreSQL is one of the **three Effortless tools** (airtable-to-rulebook, rulebook-to-postgres, rulebook-to-airtable). It implements the rulebook's calculated fields using SQL functions and views.

**PostgreSQL has no limitations.** Unlike the local substrate implementations in this repo (Python, Go, XLSX, etc.), which are hello-world demonstrations with formula gaps, the `rulebook-to-postgres` tool fully supports complex aggregations, multi-table JOINs, window functions, and all formula types. It is production-ready.

## No Privileged Position

**The rulebook is the single source of truth.** Answer keys are generated directly from the rulebook's seed data, not from PostgreSQL. PostgreSQL is tested equally alongside all other substrates (Python, Go, binary, XLSX, etc.).

This architecture ensures:
- A bug in Postgres SQL would be caught by conformance testing
- No substrate can "define truth" — only the rulebook does
- All substrates are validated against the same canonical answer keys

## How It Works

### Generation (Injection)

The rulebook formulas are compiled to SQL:

| Artifact | Purpose |
|----------|---------|
| `01-drop-and-create-tables.sql` | Base tables with raw fields |
| `02-create-functions.sql` | `calc_*` functions implementing formulas |
| `03-create-views.sql` | `vw_*` views with computed fields |
| `04-create-policies.sql` | Row Level Security policies |
| `05-insert-data.sql` | Seed data from rulebook |
| `init-db.sh` | Database initialization script |

### Testing

PostgreSQL is tested via `execution-substrates/postgres/`:

```bash
# Initialize the database (must be done first)
cd postgres
./init-db.sh

# Run conformance tests (from execution-substrates/postgres/)
cd ../execution-substrates/postgres
./take-test.sh
```

The test queries all `vw_*` views and compares results against the answer keys.

## Technology

**PostgreSQL** is an advanced open-source relational database. Its function system allows complex calculations to be expressed declaratively.

Key characteristics:
- **SQL functions**: `CREATE FUNCTION calc_*` implements each derived field
- **Views**: Pre-computed joins that materialize all calculated fields
- **Referential integrity**: Foreign keys ensure data consistency
- **Row Level Security**: Fine-grained access control

## Files

| File | Description |
|------|-------------|
| `01-drop-and-create-tables.sql` | Drop and recreate tables with raw fields |
| `02-create-functions.sql` | Create calculation functions |
| `03-create-views.sql` | Create views with calculated fields |
| `04-create-policies.sql` | Create RLS policies |
| `05-insert-data.sql` | Insert data from rulebook |
| `init-db.sh` | Database initialization script |

## Usage

```bash
# Initialize the database
./init-db.sh

# Query the computed view
psql -d demo -c "SELECT workflow_id, name, display_name, has_more_than_1_step FROM vw_workflows"
```

## DAG Execution Order

```
Level 0: Raw fields (from tables)
Level 1: name (slug), count_of_steps (aggregation)
Level 2: has_more_than_1_step (depends on count_of_steps)
```

## Source

Generated from: `effortless-rulebook/effortless-rulebook.json`
