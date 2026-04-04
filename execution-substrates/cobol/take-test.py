#!/usr/bin/env python3
"""
COBOL Substrate Test Runner

Produces test-answers by running the shared Python erb_calc library (same logic
as the generated COBOL). The generated erb_calc.cbl implements the same formulas
and can be compiled with GnuCOBOL for native execution.

Matches Python substrate take-test: applies compute_aggregations before erb_calc
so COUNTIFS-style fields are populated for workflows and similar entities.
"""

import glob
import json
import os
import sys
from pathlib import Path

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = Path(script_dir).parent.parent
sys.path.insert(0, str(project_root))

python_substrate = os.path.join(script_dir, "..", "python")
sys.path.insert(0, python_substrate)

from erb_calc import compute_all_calculated_fields
from orchestration.shared import load_rulebook, compute_aggregations


def process_entity(
    input_path: str,
    output_path: str,
    entity_name: str,
    rulebook: dict,
) -> int:
    """Process a single entity file, computing all calculated fields."""
    with open(input_path, "r") as f:
        records = json.load(f)

    records = compute_aggregations(records, entity_name, rulebook, project_root)

    computed_records = []
    for record in records:
        computed = compute_all_calculated_fields(record, entity_name)
        computed_records.append(computed)

    with open(output_path, "w") as f:
        json.dump(computed_records, f, indent=2)

    return len(computed_records)


def main():
    blank_tests_dir = project_root / "testing" / "blank-tests"
    test_answers_dir = Path(script_dir) / "test-answers"

    if not blank_tests_dir.is_dir():
        print(f"Error: {blank_tests_dir} not found")
        sys.exit(1)

    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    test_answers_dir.mkdir(parents=True, exist_ok=True)
    total_records = 0
    entity_count = 0

    for input_path in sorted(glob.glob(str(blank_tests_dir / "*.json"))):
        filename = os.path.basename(input_path)
        if filename.startswith("_"):
            continue
        entity = filename.replace(".json", "")
        output_path = test_answers_dir / filename
        count = process_entity(input_path, str(output_path), entity, rulebook)
        total_records += count
        entity_count += 1
        print(f"  -> {entity}: {count} records")

    print(f"COBOL substrate: Processed {entity_count} entities, {total_records} total records")


if __name__ == "__main__":
    main()
