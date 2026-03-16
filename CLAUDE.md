# Effortlessly Invariant Rulesbooks (ERB)

## Architecture Overview

**Three Effortless tools** form a hub-and-spokes around Airtable: **airtable-to-rulebook**, **rulebook-to-postgres**, **rulebook-to-airtable**. The rulebook is a disposable IR. **PostgreSQL has no limitations** — it fully supports complex aggregations, JOINs, and all formula types. All other substrates in this repo are local implementations with demonstration gaps.

This repo follows a **three-layer architecture**:

```
┌─────────────────────────────────────────────────────────┐
│                    RULEBOOK (Core)                      │
│         effortless-rulebook/effortless-rulebook.json    │
│   - Single source of truth for all business logic      │
│   - Entity schemas with field types and descriptions   │
│   - Formulas for calculated fields (Excel-style)       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                  ORCHESTRATION                          │
│                  orchestration/                         │
│   - inject.py: Dispatches to all substrate injectors   │
│   - shared.py: Common utilities (load_rulebook, etc.)  │
│   - formula_parser.py: Parses Excel-style formulas     │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              EXECUTION SUBSTRATES                       │
│              execution-substrates/*/                    │
│   - postgres/: Effortless tool — no limitations        │
│   - python/: Local: Python dataclasses + calc functions│
│   - golang/: Local: Go structs + business logic        │
│   - binary/: ARM64 assembly (proof of concept)         │
│   - csv/xlsx/: Spreadsheet exports                     │
│   - uml/: PlantUML diagrams + OCL constraints          │
│   - owl/: RDF/OWL ontology                             │
│   - explain-dag/: JSON spec for derivation tracing     │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              CONFORMANCE TESTING                        │
│   - test-cases/: YAML test scenarios                   │
│   - Each substrate has take-test.py for verification   │
│   - Tests prove substrates compute identically         │
└─────────────────────────────────────────────────────────┘
```

## Key Principles

1. **Rulebook is the source of truth** - Never hardcode business logic in substrates. All formulas, types, and descriptions come from the rulebook JSON.

2. **Modify injectors, not generated files** - The `inject-into-*.py` scripts in each substrate folder generate the code. Edit those, not the output files.

3. **Formula semantics are Excel-compatible** - IF(), AND(), OR(), CONCAT(), LEFT(), RIGHT(), etc. The formula_parser.py handles parsing.

4. **Every substrate must pass the same tests** - Conformance testing ensures Python, Go, binary, etc. all produce identical results for the same inputs.

## Quick Reference

| Task | Location |
|------|----------|
| Change business logic | `effortless-rulebook/effortless-rulebook.json` |
| Change code generation | `execution-substrates/*/inject-into-*.py` |
| Add test cases | `test-cases/*.yaml` |
| Run all injectors | `orchestration/inject.py` |
| Shared utilities | `orchestration/shared.py` |

## Common Commands

```bash
# Regenerate all substrates from rulebook
python orchestration/inject.py

# Clean generated files
python orchestration/inject.py --clean

# Run tests for a specific substrate
cd execution-substrates/python && python take-test.py
```

---
Local CLAUDE.md is also in ../api.effortlessapi.com/CLAUDE.md