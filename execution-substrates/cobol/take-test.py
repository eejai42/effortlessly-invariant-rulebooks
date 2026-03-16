#!/usr/bin/env python3
"""
COBOL Substrate Test Runner

Compiles and runs the generated COBOL program to compute test answers.
1. Reads JSON from testing/blank-tests/
2. Converts to tab-delimited input
3. Compiles and runs COBOL with GnuCOBOL
4. Converts tab-delimited output back to JSON
"""

import glob
import json
import os
import subprocess
import sys
from pathlib import Path

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent


def check_gnucobol():
    """Check if GnuCOBOL is installed."""
    try:
        result = subprocess.run(
            ["cobc", "--version"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            version = result.stdout.split("\n")[0]
            print(f"  Found: {version}")
            return True
    except FileNotFoundError:
        pass
    return False


def compile_cobol():
    """Compile the COBOL main program."""
    print("Compiling erb_main.cbl...")
    result = subprocess.run(
        ["cobc", "-free", "-x", "-o", "erb_test", "erb_main.cbl"],
        capture_output=True,
        text=True,
        cwd=script_dir,
    )
    if result.returncode != 0:
        print(f"FATAL: COBOL compilation failed:")
        print(result.stderr)
        print(result.stdout)
        sys.exit(1)
    print("  Compiled successfully: erb_test")
    return True


def load_field_order():
    """Load the field order manifest."""
    order_path = script_dir / "erb_field_order.json"
    if not order_path.exists():
        print(f"FATAL: {order_path} not found. Run inject-into-cobol.py first.")
        sys.exit(1)
    with open(order_path) as f:
        return json.load(f)


def to_snake_case(name: str) -> str:
    """Convert CamelCase to snake_case."""
    import re
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def json_to_tsv(records: list, field_order: list, raw_count: int) -> str:
    """Convert JSON records to tab-delimited string (raw fields only)."""
    # Use raw_count to determine which fields are raw vs calculated
    raw_fields = field_order[:raw_count]

    lines = []
    for record in records:
        values = []
        for field in raw_fields:
            # Try camelCase, snake_case, and lowercase
            snake = to_snake_case(field)
            # Use explicit None checks to handle boolean False correctly
            val = record.get(field)
            if val is None:
                val = record.get(snake)
            if val is None:
                val = record.get(field.lower())
            # Convert booleans to "true"/"false" strings for COBOL
            if isinstance(val, bool):
                val = "true" if val else "false"
            elif val is None:
                val = ""
            else:
                val = str(val)
            values.append(val)
        lines.append("\t".join(values))
    return "\n".join(lines) + "\n" if lines else ""


def tsv_to_json(tsv_content: str, field_order: list) -> list:
    """Convert tab-delimited output back to JSON (with snake_case keys)."""
    records = []
    for line in tsv_content.strip().split("\n"):
        if not line:
            continue
        values = line.split("\t")
        record = {}
        for i, field in enumerate(field_order):
            # Use snake_case for output to match expected format
            snake = to_snake_case(field)
            if i < len(values):
                val = values[i].rstrip()  # Preserve leading spaces, strip trailing padding
                # Convert string booleans back to Python booleans
                if val.lower() == "true":
                    record[snake] = True
                elif val.lower() == "false":
                    record[snake] = False
                elif val.isdigit():
                    record[snake] = int(val)
                else:
                    record[snake] = val
            else:
                record[snake] = ""
        records.append(record)
    return records


def process_entity(input_path: Path, output_path: Path, entity_name: str, field_order: list, raw_count: int) -> int:
    """Process a single entity file using COBOL."""
    with open(input_path) as f:
        records = json.load(f)

    # Convert JSON to tab-delimited input
    tsv_input = json_to_tsv(records, field_order, raw_count)

    # Run COBOL program with stdin/stdout piping
    result = subprocess.run(
        ["./erb_test"],
        input=tsv_input,
        capture_output=True,
        text=True,
        cwd=script_dir,
    )

    if result.returncode != 0:
        print(f"FATAL: COBOL execution failed for {entity_name}:")
        print(result.stderr)
        print(result.stdout)
        sys.exit(1)

    # Parse stdout (TSV output) and stderr (messages)
    tsv_output = result.stdout
    if result.stderr:
        # Show COBOL status messages (written to stderr)
        for line in result.stderr.strip().split("\n"):
            if line:
                print(f"  COBOL: {line}")

    # Convert TSV output to JSON
    computed_records = tsv_to_json(tsv_output, field_order)

    # Write JSON output
    with open(output_path, "w") as f:
        json.dump(computed_records, f, indent=2)

    return len(computed_records)


def main():
    blank_tests_dir = project_root / "testing" / "blank-tests"
    test_answers_dir = script_dir / "test-answers"

    print("COBOL Substrate Test Runner")
    print("=" * 50)
    print()

    # Check for GnuCOBOL
    print("Checking for GnuCOBOL...")
    if not check_gnucobol():
        print("FATAL: GnuCOBOL (cobc) not found.")
        print("Install with: brew install gnucobol")
        sys.exit(1)
    print()

    # Check source files
    if not (script_dir / "erb_main.cbl").exists():
        print("FATAL: erb_main.cbl not found. Run inject-into-cobol.py first.")
        sys.exit(1)

    # Compile COBOL
    compile_cobol()
    print()

    # Load field order
    field_order_all = load_field_order()

    # Get target entity (COBOL is generated for only ONE entity type)
    target_entity = field_order_all.get("_target_entity")
    if target_entity:
        print(f"COBOL substrate targets: {target_entity}")
        print()

    if not blank_tests_dir.is_dir():
        print(f"FATAL: {blank_tests_dir} not found")
        sys.exit(1)

    test_answers_dir.mkdir(exist_ok=True)
    total_records = 0
    entity_count = 0

    print("Processing entities...")
    for input_path in sorted(blank_tests_dir.glob("*.json")):
        filename = input_path.name
        if filename.startswith("_"):
            continue
        entity = filename.replace(".json", "")

        # Only process the entity that COBOL was generated for
        if target_entity and entity != target_entity:
            print(f"  Skipping {entity} (COBOL only supports {target_entity})")
            continue

        # Get field info for this entity (new format with fields + raw_count)
        entity_info = field_order_all.get(entity) or field_order_all.get(entity.title())
        if not entity_info:
            print(f"  Skipping {entity} (no calculated fields)")
            continue

        # Handle both old format (list) and new format (dict with fields/raw_count)
        if isinstance(entity_info, list):
            field_order = entity_info
            raw_count = len(field_order)  # Assume all raw if old format
        else:
            field_order = entity_info["fields"]
            raw_count = entity_info["raw_count"]

        output_path = test_answers_dir / filename
        count = process_entity(input_path, output_path, entity, field_order, raw_count)
        total_records += count
        entity_count += 1
        print(f"  -> {entity}: {count} records")

    print()
    print("=" * 50)
    print(f"COBOL substrate: Processed {entity_count} entities, {total_records} total records")
    print("=" * 50)


if __name__ == "__main__":
    main()
