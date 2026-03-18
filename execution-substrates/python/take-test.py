#!/usr/bin/env python3
"""
Python Substrate Test Runner
=============================
Computes all calculated fields using the generated erb_calc.py library.

Supports two modes:
1. Multi-entity (--multi-entity): Processes all files in blank-tests/ -> test-answers/
2. Legacy: Processes single test-answers.json file

This script uses the shared erb_calc.py library which is generated from the
rulebook and contains all calculation functions.
"""

import argparse
import glob
import json
import os
import sys
from pathlib import Path

# Add current directory to path to allow imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Add project root to path for shared imports
sys.path.insert(0, str(Path(script_dir).parent.parent))

from erb_calc import compute_all_calculated_fields
from orchestration.shared import load_rulebook, compute_aggregations, compute_lookups


def process_entity(input_path: str, output_path: str, entity_name: str,
                   rulebook: dict = None, project_root: Path = None) -> int:
    """Process a single entity file, computing all calculated fields."""
    with open(input_path, 'r') as f:
        records = json.load(f)

    if rulebook is not None and project_root is not None:
        # Compute lookup fields first (INDEX/MATCH)
        records = compute_lookups(records, entity_name, rulebook, project_root)
        # Then compute aggregation fields (COUNTIFS, SUMIFS)
        records = compute_aggregations(records, entity_name, rulebook, project_root)

    # Compute any remaining calculated fields for each record
    computed_records = []
    for record in records:
        computed = compute_all_calculated_fields(record, entity_name)
        computed_records.append(computed)

    # Save results
    with open(output_path, 'w') as f:
        json.dump(computed_records, f, indent=2)

    return len(computed_records)


def run_multi_entity():
    """Process all entity files from shared testing/blank-tests/ directory."""
    # Use shared blank-tests directory at project root
    project_root = Path(script_dir).parent.parent
    blank_tests_dir = project_root / "testing" / "blank-tests"
    test_answers_dir = Path(script_dir) / "test-answers"

    if not blank_tests_dir.is_dir():
        print(f"Error: {blank_tests_dir} not found")
        sys.exit(1)

    # Load rulebook for aggregation computation
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"Warning: Could not load rulebook for aggregations: {e}")
        rulebook = None

    # Ensure output directory exists
    test_answers_dir.mkdir(parents=True, exist_ok=True)

    # Process each entity file (skip metadata files starting with _)
    total_records = 0
    entity_count = 0

    for input_path in sorted(glob.glob(str(blank_tests_dir / "*.json"))):
        filename = os.path.basename(input_path)

        # Skip metadata files
        if filename.startswith('_'):
            continue

        entity = filename.replace('.json', '')
        output_path = test_answers_dir / filename

        count = process_entity(input_path, str(output_path), entity, rulebook, project_root)
        total_records += count
        entity_count += 1

        print(f"  -> {entity}: {count} records")

    print(f"Python substrate: Processed {entity_count} entities, {total_records} total records")


def run_legacy():
    """Process single test-answers.json file (legacy mode)."""
    input_path = os.path.join(script_dir, "test-answers.json")
    output_path = os.path.join(script_dir, "test-answers.json")

    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found")
        sys.exit(1)

    count = process_entity(input_path, output_path)
    print(f"Python substrate: Processing {count} records...")
    print(f"Python substrate: Saved results to {output_path}")


def main():
    run_multi_entity()


if __name__ == "__main__":
    main()
