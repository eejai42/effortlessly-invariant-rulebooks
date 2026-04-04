# COBOL Execution Substrate

COBOL calculation program generated from the Effortless Rulebook.

## Overview

This substrate compiles rulebook formulas into GnuCOBOL free-format source. It generates a calculation module (`erb_calc.cbl`) and a record layout copybook (`erb_copy.cpy`) that implement the same logic as the shared Python `erb_calc.py`.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   inject-into-cobol.py                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   1. Load rulebook JSON (structured data)                    │
│                          ↓                                   │
│   2. Parse Excel-dialect formulas into an expression tree    │
│                          ↓                                   │
│   3. Build dependency DAG for calculation ordering           │
│                          ↓                                   │
│   4. Compile formulas to COBOL (compile_to_cobol)            │
│                          ↓                                   │
│   5. Generate erb_calc.cbl and erb_copy.cpy                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

- **DAG-Ordered Evaluation**: Calculated fields are computed in dependency order
- **CALC-* Paragraphs**: One paragraph per calculated field (mirrors calc_* pattern)
- **COMPUTE-ALL-FIELDS**: Single entry point that performs all calculations
- **GnuCOBOL Free-Format**: Uses `-free`; no column-7 restrictions
- **Test Run**: `take-test` uses the shared Python erb_calc to produce test-answers (same semantics as generated COBOL)

## Generated Files

| File | Description |
|------|-------------|
| `erb_calc.cbl` | **GENERATED** - COBOL calculation module (paragraphs and working storage) |
| `erb_copy.cpy` | **GENERATED** - Record layout copybook (01 RECORD with 02 fields) |
| `erb_field_order.json` | **GENERATED** - Field order per entity (for drivers) |
| `test-answers/` | **TEST OUTPUT** - Produced by take-test (via Python erb_calc) |
| `test-results.md` | **TEST OUTPUT** - Human-readable test report |

## Source Files (Not Cleaned)

| File | Description |
|------|-------------|
| `inject-into-cobol.py` | Compiler: parses formulas and generates COBOL |
| `inject-substrate.sh` | Regenerates Python erb_calc, then COBOL, then runs take-test |
| `take-test.sh` | Runs take-test.py and generates substrate report |
| `take-test.py` | Uses Python erb_calc to produce test-answers (runs `compute_aggregations` first, same as the Python substrate) |
| `README.md` | This documentation |

## Cleaning

To remove generated files:

```bash
python3 inject-into-cobol.py --clean
```

This removes: `erb_calc.cbl`, `erb_copy.cpy`, `erb_field_order.json`.

## Building and Running the COBOL (GnuCOBOL)

With [GnuCOBOL](https://gnucobol.sourceforge.io/) installed:

```bash
# Compile as a callable module (no main; for use by a host program)
cobc -free -m erb_calc.cbl -I.

# Or build a standalone program if you add a main that fills RECORD and calls MAIN-CALC
```

The generated code uses:

- `COPY "erb_copy"` for the record layout (ensure `erb_copy.cpy` is in the include path).
- Working storage: `WS-TEMP-1` … `WS-TEMP-10`, `WS-FIND-*` for FIND.
- Paragraphs: `MAIN-CALC`, `COMPUTE-ALL-FIELDS`, `CALC-<FIELD>`, `FIND-CONTAINS`.

## Usage (Test Run)

Test answers are produced by the shared Python calculation engine (same formulas as the COBOL):

```bash
./inject-substrate.sh
```

This regenerates Python `erb_calc.py`, generates COBOL, runs `take-test.sh` (which uses Python to compute test-answers), and generates the substrate report.

## Demo scenario: CardDemo mainframe app

A concrete next-step demo is to drive this COBOL substrate from a realistic mainframe workload such as [CardDemo](https://github.com/aws-samples/aws-mainframe-modernization-carddemo):

1. **Extract a rulebook / model**: Use the CardDemo COBOL copybooks and batch logic as a source of truth to define an `effortless-rulebook.json` for a slice of the domain (for example, interest calculation, transaction classification, or statement generation). The goal is to capture the _business rules_ (fields, datatypes, calculated fields, and their Excel-style formulas) independent of any single runtime.
2. **Generate COBOL that matches a functional demo**: Run the orchestration pipeline so that the new rulebook produces Python `erb_calc.py` and COBOL `erb_calc.cbl`/`erb_copy.cpy`. Wire the generated COBOL into a small CardDemo-inspired batch driver (or a minimal standalone program) and show that, for the same input transactions, the generated COBOL produces the same outputs as the original CardDemo programs.
3. **Generalize to other substrates**: Reuse the same rulebook to generate and test other substrates (Python, YAML, Go, CSV, English, etc.), all against the same `testing/blank-tests/` cases derived from CardDemo data. This demonstrates that the model is **substrate-agnostic**: you describe the rules once, then project them consistently into multiple execution environments, including COBOL.

## Source

Generated from: `effortless-rulebook/effortless-rulebook.json`
