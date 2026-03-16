#!/usr/bin/env python3
"""
Take Test - OWL Execution Substrate

This script uses SHACL-SPARQL reasoning to compute derived values:
1. Loads the generated ontology and SHACL rules
2. Runs pyshacl multiple passes to resolve dependencies between computed fields
3. Extracts results to test-answers/ directory

The computation happens in the SHACL reasoner, not in Python code.
This script is 100% domain-agnostic - all field names come from the rulebook.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# Auto-install dependencies if needed
def ensure_dependencies():
    """Install required packages if not present."""
    try:
        import rdflib
        import pyshacl
    except ImportError:
        print("Installing dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "rdflib", "pyshacl", "--quiet"
        ])

ensure_dependencies()

from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD
import pyshacl

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from orchestration.shared import load_rulebook

# Script directory
script_dir = Path(__file__).parent.resolve()


# =============================================================================
# NAMESPACES
# =============================================================================

ERB = Namespace("http://example.org/erb#")
SH = Namespace("http://www.w3.org/ns/shacl#")


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def field_to_property_uri(field_name: str) -> str:
    """Convert field name to property URI (camelCase) - must match injector."""
    if field_name:
        return field_name[0].lower() + field_name[1:]
    return 'unknown'


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case for output compatibility."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    # Normalize consecutive underscores to single underscore
    return re.sub('_+', '_', s2)


def rdf_value_to_python(value):
    """Convert an RDF value to Python native type."""
    if value is None:
        return None

    if isinstance(value, Literal):
        py_val = value.toPython()
        if isinstance(py_val, bool):
            return py_val
        if isinstance(py_val, (int, float)):
            return py_val
        return str(py_val)

    if isinstance(value, URIRef):
        return str(value)

    return str(value)


# =============================================================================
# SHACL REASONING
# =============================================================================

def run_shacl_reasoning(data_graph: Graph, shacl_graph: Graph, max_passes: int = 5) -> int:
    """
    Run SHACL reasoning with multiple passes to resolve dependencies.

    Some computed fields depend on other computed fields. SHACL-SPARQL rules
    don't automatically handle this in a single pass, so we run multiple passes
    until no new triples are added.

    Returns the number of passes executed.
    """
    passes = 0
    for i in range(max_passes):
        before = len(data_graph)
        pyshacl.validate(
            data_graph,
            shacl_graph=shacl_graph,
            inference='none',  # Don't use rdfs inference - it can cause incorrect property bindings
            inplace=True,
            advanced=True,
            debug=False
        )
        after = len(data_graph)
        passes += 1
        added = after - before
        print(f"   Pass {i+1}: {before} -> {after} triples ({added} added)")

        if added == 0:
            break

    return passes


def extract_entity_results(
    data_graph: Graph,
    table_name: str,
    schema: list,
    data: list
) -> list:
    """
    Extract computed results from RDF graph for a single entity type.

    Returns list of records with all fields (raw + computed) in snake_case.
    """
    records = []

    # Build field info map
    all_fields = []
    for col in schema:
        all_fields.append({
            'name': col.get('name', ''),
            'datatype': col.get('datatype', 'string'),
            'type': col.get('type', 'raw')
        })

    # Extract each individual
    for i, original_row in enumerate(data):
        ind_uri = ERB[f"{table_name}_{i}"]

        # Start with original data (snake_case keys)
        record = {}
        for key, value in original_row.items():
            snake_key = camel_to_snake(key)
            record[snake_key] = value

        # Query each field from the graph (includes computed values)
        for field_info in all_fields:
            field_name = field_info['name']
            prop_name = field_to_property_uri(field_name)
            prop_uri = ERB[prop_name]

            value = data_graph.value(ind_uri, prop_uri)

            if value is not None:
                py_value = rdf_value_to_python(value)
                snake_key = camel_to_snake(field_name)
                record[snake_key] = py_value

        # Normalize empty strings to None for all string fields
        # (matches semantic intent - empty string means "no value")
        for key, value in record.items():
            if value == "":
                record[key] = None

        records.append(record)

    return records


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("OWL Execution Substrate - SHACL Reasoning Test")
    print("=" * 70)
    print()

    # Check required files exist
    ontology_path = script_dir / "ontology.owl"
    individuals_path = script_dir / "individuals.ttl"
    rules_path = script_dir / "rules.shacl.ttl"

    for path in [ontology_path, individuals_path, rules_path]:
        if not path.exists():
            print(f"ERROR: Required file not found: {path}")
            print("Run: python inject-into-owl.py first")
            sys.exit(1)

    # Load rulebook to get schema info
    print("Loading rulebook...")
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Filter to just table definitions
    tables = {k: v for k, v in rulebook.items()
              if isinstance(v, dict) and 'schema' in v}

    # Identify which tables have computed columns
    tables_with_computed = {}
    for table_name, table_def in tables.items():
        if table_name.startswith('_') or table_name.startswith('$'):
            continue
        schema = table_def.get('schema', [])
        computed_cols = [c['name'] for c in schema if c.get('formula')]
        if computed_cols:
            tables_with_computed[table_name] = computed_cols

    print(f"Tables with computed columns: {', '.join(tables_with_computed.keys())}")

    # Load ontology + individuals into a single graph
    print("\nLoading ontology and data...")
    data_graph = Graph()
    data_graph.bind('erb', ERB)
    data_graph.bind('xsd', XSD)

    data_graph.parse(ontology_path, format='turtle')
    print(f"   Loaded: {ontology_path}")

    data_graph.parse(individuals_path, format='turtle')
    print(f"   Loaded: {individuals_path}")
    print(f"   Total triples: {len(data_graph)}")

    # Load SHACL rules
    print("\nLoading SHACL rules...")
    shacl_graph = Graph()
    shacl_graph.bind('erb', ERB)
    shacl_graph.bind('sh', SH)
    shacl_graph.parse(rules_path, format='turtle')
    print(f"   Loaded: {rules_path}")
    print(f"   Rule triples: {len(shacl_graph)}")

    # Run SHACL reasoning with multiple passes
    print("\nRunning SHACL-SPARQL reasoning...")
    print("   (Multiple passes to resolve dependencies between computed fields)")

    try:
        passes = run_shacl_reasoning(data_graph, shacl_graph)
        print(f"   Completed in {passes} passes")
        print(f"   Final triple count: {len(data_graph)}")
    except Exception as e:
        print(f"   ERROR: SHACL reasoning failed: {e}")
        sys.exit(1)

    # Extract results and save to test-answers/
    print("\nExtracting computed values...")

    test_answers_dir = script_dir / "test-answers"
    test_answers_dir.mkdir(parents=True, exist_ok=True)

    total_records = 0

    for table_name in tables_with_computed:
        table_def = tables[table_name]
        schema = table_def.get('schema', [])
        data = table_def.get('data', [])

        if not schema or not data:
            continue

        records = extract_entity_results(data_graph, table_name, schema, data)
        total_records += len(records)

        # Convert table name to snake_case for filename
        filename = camel_to_snake(table_name) + ".json"
        output_path = test_answers_dir / filename

        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(records, f, indent=2)

        computed_cols = tables_with_computed[table_name]
        print(f"   {table_name}: {len(records)} records ({len(computed_cols)} computed fields)")

    print(f"\nTotal: {total_records} records extracted")
    print(f"Output: {test_answers_dir}/")

    print("\n" + "=" * 70)
    print("SHACL reasoning complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
