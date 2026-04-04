#!/usr/bin/env python3
"""
Generate COBOL calculation program from the Effortless Rulebook.

This script reads formulas from the rulebook and generates erb_calc.cbl
with record layout and calculation paragraphs for all entities with calculated fields.
Uses GnuCOBOL free-format (-free).

Generated files:
- erb_calc.cbl - Record layout, working storage, and calculation paragraphs
- erb_copy.cpy - Record layout copybook
- erb_field_order.json - Field order per entity (for Python take-test driver)
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Set

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from orchestration.shared import (
    load_rulebook,
    handle_clean_arg,
    discover_entities,
    get_entity_schema,
    to_snake_case,
    get_calculated_fields,
    get_raw_fields,
)
from orchestration.formula_parser import (
    parse_formula,
    compile_to_cobol,
    get_field_dependencies,
    to_cobol_name,
)


# Default PIC lengths for generated COBOL
STRING_PIC_LEN = 500
INTEGER_PIC_LEN = 10
BOOLEAN_PIC_LEN = 5


def build_dag_levels(calculated_fields: List[Dict], raw_field_names: Set[str]) -> List[List[Dict]]:
    """Build DAG levels for calculated fields based on dependencies."""
    field_deps = {}
    for field in calculated_fields:
        formula = field.get("formula", "")
        try:
            expr = parse_formula(formula)
            deps = get_field_dependencies(expr)
            field_deps[field["name"]] = set(to_snake_case(d) for d in deps)
        except Exception as e:
            print(f"Warning: Failed to parse formula for {field['name']}: {e}")
            field_deps[field["name"]] = set()

    levels = []
    assigned = set(to_snake_case(name) for name in raw_field_names)
    remaining = {f["name"]: f for f in calculated_fields}

    while remaining:
        current_level = []
        for name, field in list(remaining.items()):
            deps = field_deps.get(name, set())
            if deps <= assigned:
                current_level.append(field)

        if not current_level:
            print(f"Warning: Could not resolve dependencies for: {list(remaining.keys())}")
            levels.append(list(remaining.values()))
            break

        levels.append(current_level)
        for field in current_level:
            assigned.add(to_snake_case(field["name"]))
            del remaining[field["name"]]

    return levels


def datatype_to_pic(datatype: str) -> str:
    """Convert rulebook datatype to COBOL PIC clause."""
    dt = (datatype or "string").lower()
    if dt == "boolean":
        return f"PIC X({BOOLEAN_PIC_LEN})"
    if dt == "integer":
        return f"PIC 9({INTEGER_PIC_LEN})"
    return f"PIC X({STRING_PIC_LEN})"


def generate_record_layout(schema: List[Dict], calculated_names: Set[str]) -> List[str]:
    """Generate 01 RECORD with 02 entries for each field."""
    lines = []
    lines.append("       01 RECORD.")
    for field in schema:
        name = field["name"]
        if name in calculated_names:
            continue  # will be added after raw fields
        cobol_name = to_cobol_name(name)
        pic = datatype_to_pic(field.get("datatype", "string"))
        lines.append(f"          02 {cobol_name} {pic}.")
    for field in schema:
        name = field["name"]
        if name not in calculated_names:
            continue
        cobol_name = to_cobol_name(name)
        pic = datatype_to_pic(field.get("datatype", "string"))
        lines.append(f"          02 {cobol_name} {pic}.")
    return lines


def generate_calc_paragraph(
    entity_name: str,
    field: Dict,
    record_var: str,
    field_types: Dict[str, str],
) -> List[str]:
    """Generate a paragraph that computes one calculated field into RECORD."""
    name = field["name"]
    formula = field.get("formula", "")
    cobol_name = to_cobol_name(name)
    result_var = f"{record_var}-{cobol_name}"

    try:
        expr = parse_formula(formula)
        stmts = compile_to_cobol(expr, result_var, record_var, field_types)
    except Exception as e:
        return [
            f"       CALC-{cobol_name}.",
            f"           *> ERROR: Could not parse formula: {formula[:60]}...",
            f"           MOVE \"ERROR\" TO {result_var}",
            "       .",
        ]

    lines = [f"       CALC-{cobol_name}."]
    for st in stmts:
        lines.append(f"           {st}")
    lines.append("       .")
    return lines


def generate_find_contains_paragraph() -> List[str]:
    """Generate FIND-CONTAINS helper paragraph (needle in haystack)."""
    return [
        "       FIND-CONTAINS.",
        "           MOVE \"false\" TO WS-FIND-RESULT",
        "           MOVE 1 TO WS-FIND-I",
        "           COMPUTE WS-FIND-LEN = FUNCTION LENGTH(WS-FIND-HAYSTACK)",
        "           COMPUTE WS-FIND-NLEN = FUNCTION LENGTH(WS-FIND-NEEDLE)",
        "           IF WS-FIND-NLEN = 0",
        "               MOVE \"true\" TO WS-FIND-RESULT",
        "           END-IF",
        "           PERFORM UNTIL WS-FIND-I > WS-FIND-LEN - WS-FIND-NLEN + 1",
        "               OR WS-FIND-RESULT = \"true\"",
        "               IF WS-FIND-HAYSTACK(WS-FIND-I:WS-FIND-NLEN) = WS-FIND-NEEDLE",
        "                   MOVE \"true\" TO WS-FIND-RESULT",
        "               END-IF",
        "               ADD 1 TO WS-FIND-I",
        "           END-PERFORM",
        "           .",
    ]


def generate_entity_section(
    entity_name: str,
    schema: List[Dict],
    calculated_fields: List[Dict],
    dag_levels: List[List[Dict]],
    field_types: Dict[str, str],
    record_var: str,
) -> List[str]:
    """Generate PROCEDURE DIVISION paragraphs for one entity (record is in copybook)."""
    lines = []
    lines.append(f"       *> ========== {entity_name.upper()} ==========")
    for level_idx, level_fields in enumerate(dag_levels):
        lines.append(f"       *> Level {level_idx + 1}")
        for field in level_fields:
            lines.extend(
                generate_calc_paragraph(entity_name, field, record_var, field_types)
            )
            lines.append("")
    lines.append("       COMPUTE-ALL-FIELDS.")
    for level_fields in dag_levels:
        for field in level_fields:
            cobol_name = to_cobol_name(field["name"])
            lines.append(f"           PERFORM CALC-{cobol_name}")
    lines.append("       .")
    return lines


def get_field_order(schema: List[Dict], calculated_fields: List[Dict], dag_levels: List[List[Dict]]) -> List[str]:
    """Return ordered list of field names: raw first, then calculated in DAG order."""
    calculated_names = {f["name"] for f in calculated_fields}
    order = []
    for f in schema:
        if f["name"] not in calculated_names:
            order.append(f["name"])
    for level_fields in dag_levels:
        for f in level_fields:
            order.append(f["name"])
    return order


def generate_erb_calc(rulebook: Dict) -> str:
    """Generate erb_calc.cbl with calculation paragraphs (record layout is in copybook)."""
    entities = discover_entities(rulebook)
    entity_name = None
    schema = None
    calculated_fields = None
    dag_levels = None
    field_types = None
    for en in entities:
        sch = get_entity_schema(rulebook, en)
        calcs = get_calculated_fields(sch)
        if calcs:
            entity_name = en
            schema = sch
            calculated_fields = calcs
            raw_field_names = {f["name"] for f in get_raw_fields(sch)}
            dag_levels = build_dag_levels(calculated_fields, raw_field_names)
            field_types = {f["name"]: f.get("datatype", "string") for f in schema}
            break

    if not entity_name or not calculated_fields:
        return "\n".join([
            "       *> No entities with calculated fields",
            "       IDENTIFICATION DIVISION.",
            "       PROGRAM-ID. ERBCALC.",
            "       PROCEDURE DIVISION. GOBACK.",
        ])

    lines = [
        "       *> ERB Calculation Module (GENERATED - DO NOT EDIT)",
        "       *> Generated from: effortless-rulebook/effortless-rulebook.json",
        "       *> GnuCOBOL free-format: cobc -free -m erb_calc.cbl",
        "       IDENTIFICATION DIVISION.",
        "       PROGRAM-ID. ERBCALC.",
        "       DATA DIVISION.",
        "       WORKING-STORAGE SECTION.",
        "       01 WS-FIND-NEEDLE   PIC X(500).",
        "       01 WS-FIND-HAYSTACK PIC X(500).",
        "       01 WS-FIND-RESULT   PIC X(5).",
        "       01 WS-FIND-I       PIC 9(6).",
        "       01 WS-FIND-LEN     PIC 9(6).",
        "       01 WS-FIND-NLEN    PIC 9(6).",
        "       01 WS-TEMP-1       PIC X(500).",
        "       01 WS-TEMP-2       PIC X(500).",
        "       01 WS-TEMP-3       PIC X(500).",
        "       01 WS-TEMP-4       PIC X(500).",
        "       01 WS-TEMP-5       PIC X(500).",
        "       01 WS-TEMP-6       PIC X(500).",
        "       01 WS-TEMP-7       PIC X(500).",
        "       01 WS-TEMP-8       PIC X(500).",
        "       01 WS-TEMP-9       PIC X(500).",
        "       01 WS-TEMP-10      PIC X(500).",
        "       LINKAGE SECTION.",
        "       COPY \"erb_copy\".",
        "       PROCEDURE DIVISION USING RECORD.",
        "       MAIN-CALC.",
        "           PERFORM COMPUTE-ALL-FIELDS",
        "           GOBACK.",
        "       .",
        "",
    ]

    record_var = "RECORD"
    lines.extend(
        generate_entity_section(
            entity_name,
            schema,
            calculated_fields,
            dag_levels,
            field_types,
            record_var,
        )
    )
    lines.extend(generate_find_contains_paragraph())

    return "\n".join(lines)


def generate_copybook(rulebook: Dict) -> str:
    """Generate erb_copy.cpy (record layout) for use by erb_calc.cbl."""
    lines = [
        "       *> ERB Record Layout (GENERATED - DO NOT EDIT)",
        "       *> COPY \"erb_copy\" in erb_calc.cbl",
        "       01 RECORD.",
        "",
    ]

    entities = discover_entities(rulebook)
    for entity_name in entities:
        schema = get_entity_schema(rulebook, entity_name)
        calculated = get_calculated_fields(schema)
        if not calculated:
            continue
        calculated_names = {f["name"] for f in calculated}
        for field in schema:
            if field["name"] in calculated_names:
                continue
            cobol_name = to_cobol_name(field["name"])
            pic = datatype_to_pic(field.get("datatype", "string"))
            lines.append(f"          02 {cobol_name} {pic}.")
        for field in schema:
            if field["name"] not in calculated_names:
                continue
            cobol_name = to_cobol_name(field["name"])
            pic = datatype_to_pic(field.get("datatype", "string"))
            lines.append(f"          02 {cobol_name} {pic}.")
        break  # first entity with calculated fields

    return "\n".join(lines)


def generate_field_order_json(rulebook: Dict) -> Dict[str, List[str]]:
    """Generate manifest of entity -> ordered field names for Python driver."""
    out = {}
    entities = discover_entities(rulebook)
    for entity_name in entities:
        schema = get_entity_schema(rulebook, entity_name)
        calculated_fields = get_calculated_fields(schema)
        if not calculated_fields:
            continue
        raw_field_names = {f["name"] for f in get_raw_fields(schema)}
        dag_levels = build_dag_levels(calculated_fields, raw_field_names)
        order = get_field_order(schema, calculated_fields, dag_levels)
        out[entity_name] = order
        out[to_snake_case(entity_name)] = order
    return out


def main():
    GENERATED_FILES = [
        "erb_calc.cbl",
        "erb_copy.cpy",
        "erb_field_order.json",
    ]

    if handle_clean_arg(GENERATED_FILES, "COBOL substrate: Removes generated COBOL and manifest"):
        return

    script_dir = Path(__file__).resolve().parent

    print("=" * 70)
    print("COBOL Execution Substrate - Formula to COBOL Compiler")
    print("=" * 70)
    print()

    print("Loading rulebook...")
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    entities = discover_entities(rulebook)
    print(f"Discovered {len(entities)} entities: {', '.join(entities)}")
    print()

    total_fields = 0
    for entity_name in entities:
        schema = get_entity_schema(rulebook, entity_name)
        calculated_fields = get_calculated_fields(schema)
        if calculated_fields:
            print(f"  {entity_name}: {len(calculated_fields)} calculated fields")
            for field in calculated_fields:
                print(f"    - {field['name']}")
            total_fields += len(calculated_fields)
    print()
    print(f"Total: {total_fields} calculated fields to compile")
    print()
    print("-" * 70)
    print()

    print("Generating erb_copy.cpy (record layout)...")
    copy_content = generate_copybook(rulebook)
    copy_path = script_dir / "erb_copy.cpy"
    copy_path.write_text(copy_content, encoding="utf-8")
    print(f"Wrote: {copy_path} ({len(copy_content)} bytes)")

    print("Generating erb_calc.cbl...")
    calc_content = generate_erb_calc(rulebook)
    calc_path = script_dir / "erb_calc.cbl"
    calc_path.write_text(calc_content, encoding="utf-8")
    print(f"Wrote: {calc_path} ({len(calc_content)} bytes)")

    print("Generating erb_field_order.json...")
    order_data = generate_field_order_json(rulebook)
    order_path = script_dir / "erb_field_order.json"
    order_path.write_text(json.dumps(order_data, indent=2), encoding="utf-8")
    print(f"Wrote: {order_path}")

    print()
    print("=" * 70)
    print("Generation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
