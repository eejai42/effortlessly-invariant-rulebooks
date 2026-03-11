# Customer FullName Base

**The simplest possible ERB demonstration: 1 table, 1 formula, 3 rows.**

This base is the recommended starting point for understanding the Effortless Rulebook pattern. It strips away all complexity to show the core mechanism: a single calculated field derived from raw inputs.

---

## What This Base Demonstrates

- **One entity**: `Customers`
- **One formula**: `FullName = LastName & ", " & FirstName`
- **Three rows of test data**

That's it. No relationships, no aggregations, no cross-table references. Just the purest expression of "write once, run anywhere."

---

## The Rulebook

```json
{
  "Name": "DEMO: Customer FullName",
  "Customers": {
    "schema": [
      { "name": "CustomerId", "type": "raw" },
      { "name": "FirstName", "type": "raw" },
      { "name": "LastName", "type": "raw" },
      { "name": "FullName", "type": "calculated",
        "formula": "={{LastName}} & \", \" & {{FirstName}}" }
    ],
    "data": [
      { "FirstName": "Jane", "LastName": "Smith", "FullName": "Smith, Jane" },
      { "FirstName": "John", "LastName": "Doe", "FullName": "Doe, John" },
      { "FirstName": "Emily", "LastName": "Jones", "FullName": "Jones, Emily" }
    ]
  }
}
```

---

## What Gets Generated

From this single formula, the ERB platform generates equivalent implementations in every substrate:

### PostgreSQL

```sql
-- Function (02-create-functions.sql)
CREATE OR REPLACE FUNCTION calc_customers_full_name(p_customer_id TEXT)
RETURNS TEXT AS $$
BEGIN
  RETURN CONCAT(last_name, ', ', first_name);
END;

-- View (03-create-views.sql)
CREATE OR REPLACE VIEW vw_customers AS
SELECT
  t.customer_id,
  t.first_name,
  t.last_name,
  calc_customers_full_name(t.customer_id) AS full_name
FROM customers t;
```

### Python

```python
@dataclass
class Customer:
    customer_id: str
    first_name: str
    last_name: str

    def calc_full_name(self) -> str:
        return f"{self.last_name}, {self.first_name}"
```

### Go

```go
func (c *Customer) CalcFullName() string {
    return c.LastName + ", " + c.FirstName
}
```

### Excel

Cell formula: `=B2 & ", " & A2`

---

## Conformance Results

All substrates produce identical outputs for all 3 test rows:

| Substrate | Score | Duration |
|-----------|-------|----------|
| Python | 100% | 0.11s |
| Go | 100% | 0.32s |
| PostgreSQL | 100% | (reference) |
| Excel | 100% | 0.30s |
| OWL | 100% | 0.29s |
| CSV | 100% | 0.19s |
| YAML | 100% | 0.11s |
| Binary | 100% | 0.32s |
| ExplainDAG | 100% | 0.12s |
| English | 100% | ~7.5min |

**Note**: Even for this trivial example, the English substrate takes ~450 seconds (7.5 minutes) because it uses an LLM to generate and verify prose. This is the first hint of the regeneration cost asymmetry that becomes critical in larger ontologies.

---

## Why Start Here

1. **No distractions**: One table, one formula. You can trace exactly what happens.
2. **Instant verification**: Run all substrates in <2 seconds (excluding English).
3. **Foundation for complexity**: Once you understand this, adding relationships and aggregations is incremental.

---

## Next Steps

After exploring this base, switch to **Jessica BASIC** to see:
- 9 tables with foreign key relationships
- Aggregations (COUNT, etc.)
- Role-based workflow modeling
- The cost of complexity on substrate regeneration times

---

## Files in This Directory

- `effortless-rulebook.json` - Snapshot of the rulebook for this base
- `README.md` - This file

---

*Base ID: `appWrXPvXbkgQGOxt`*
