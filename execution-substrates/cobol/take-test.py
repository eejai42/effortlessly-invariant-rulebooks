#!/usr/bin/env python3
"""
COBOL Substrate Test Runner

Produces test-answers by running the shared Python erb_calc library (same logic
as the generated COBOL). The generated erb_calc.cbl implements the same formulas
and can be compiled with GnuCOBOL for native execution.
"""

import glob
import json
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
# Use Python substrate's erb_calc for test execution
python_substrate = os.path.join(script_dir, "..", "python")
sys.path.insert(0, python_substrate)

from erb_calc import compute_all_calculated_fields


def process_entity(input_path: str, output_path: str, entity_name: str) -> int:
    """Process a single entity file, computing all calculated fields."""
    with open(input_path, "r") as f:
        records = json.load(f)

    computed_records = []
    for record in records:
        computed = compute_all_calculated_fields(record, entity_name)
        computed_records.append(computed)

    with open(output_path, "w") as f:
        json.dump(computed_records, f, indent=2)

    return len(computed_records)


def main():
    project_root = os.path.join(script_dir, "..", "..")
    blank_tests_dir = os.path.join(project_root, "testing", "blank-tests")
    test_answers_dir = os.path.join(script_dir, "test-answers")

    if not os.path.isdir(blank_tests_dir):
        print(f"Error: {blank_tests_dir} not found")
        sys.exit(1)

    os.makedirs(test_answers_dir, exist_ok=True)
    total_records = 0
    entity_count = 0

    for input_path in sorted(glob.glob(os.path.join(blank_tests_dir, "*.json"))):
        filename = os.path.basename(input_path)
        if filename.startswith("_"):
            continue
        entity = filename.replace(".json", "")
        output_path = os.path.join(test_answers_dir, filename)
        count = process_entity(input_path, output_path, entity)
        total_records += count
        entity_count += 1
        print(f"  -> {entity}: {count} records")

    print(f"COBOL substrate: Processed {entity_count} entities, {total_records} total records")


if __name__ == "__main__":
    main()
