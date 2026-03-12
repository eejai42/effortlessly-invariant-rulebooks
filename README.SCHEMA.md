# Effortless Rulebook

### Generated from:

> This builds ssotme tools including those that are disabled which regenerates this file.

```
$ cd ./docs
$ ssotme -build -id
```


> Rulebook generated from Airtable base 'DEMO: Customer FullName'.

**Model ID:** ``

---

## Formal Arguments

The following logical argument establishes that "language" can be formalized as a computable classification, and demonstrates that not everything qualifies as a language under this definition.


## Execution Substrates

The following formats have been evaluated as execution substrates for this rulebook.

See the `execution-substrates/` directory for available format implementations.

---

## Table Schemas

### Table: Customers

> Table: Customers

#### Schema

| Field | Type | Data Type | Nullable | Description |
|-------|------|-----------|----------|-------------|
| `CustomerId` | raw | string | No | - |
| `Customer` | raw | string | Yes | Identifier for the customers. |
| `EmailAddress` | raw | string | Yes | Thec ustomers email address |
| `FirstName` | raw | string | Yes | First Name of the customer - used to make the full name |
| `LastName` | raw | string | Yes | Last Name of the customer - used to make the full name |
| `FullName` | calculated | string | Yes | Full name is computed from the first and last name of the customer |

**Formula for `FullName`:**
```
={{LastName}} & ", " & {{FirstName}}
```


#### Sample Data (3 records)

| Field | Value |
|-------|-------|
| `CustomerId` | cust0001 |
| `Customer` | CUST0001 |
| `EmailAddress` | jane.smith@email.com |
| `FirstName` | Jane |
| `LastName` | Smith |
| `FullName` | Smith, Jane |

---


## Metadata

**Summary:** Airtable export with schema-first type mapping: Schemas, Data, Relationships (FK links), Lookups (INDEX/MATCH), Aggregations (SUMIFS/COUNTIFS/Rollups), and Calculated fields (formulas) in Excel dialect. Field types are determined from Airtable's schema metadata FIRST (no coercion), with intelligent fallback to formula/data analysis only when schema is unavailable.

### Conversion Details

| Property | Value |
|----------|-------|
| Source Base ID | `appWrXPvXbkgQGOxt` |
| Table Count | 1 |
| Tool Version | 2.0.0 |
| Export Mode | schema_first_type_mapping |
| Field Type Mapping | checkbox→boolean, number→number/integer, multipleRecordLinks→relationship, multipleLookupValues→lookup, rollup→aggregation, count→aggregation, formula→calculated |

### Type Inference

- **Enabled:** true
- **Priority:** airtable_metadata (NO COERCION) → formula_analysis → reference_resolution → data_analysis (fallback only)
- **Airtable Type Mapping:** checkbox→boolean, singleLineText→string, multilineText→string, number→number/integer, datetime→datetime, singleSelect→string, email→string, url→string, phoneNumber→string
- **Data Coercion Hierarchy:** Only used as fallback when Airtable schema unavailable: datetime → number → integer → boolean → base64 → json → string
- **Nullable Support:** true
- **Error Value Handling:** #NUM!, #ERROR!, #N/A, #REF!, #DIV/0!, #VALUE!, #NAME? are treated as NULL

---

*Generated from effortless-rulebook.json*

