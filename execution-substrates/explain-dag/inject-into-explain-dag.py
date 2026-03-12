#!/usr/bin/env python3
"""
ExplainDAG Injector - Generate explanation specification from the Effortless Rulebook.

This script reads formulas from the rulebook and generates:
1. explain_spec.json - static AST templates and dependency DAG for each entity
2. Used by take-test.py to produce machine-readable derivation explanations

The key insight: separate TEMPLATE (formula structure) from INSTANCE (witnessed values).
"""

import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Set, Optional
from datetime import datetime, timezone

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from orchestration.shared import (
    load_rulebook, get_candidate_name_from_cwd, handle_clean_arg,
    discover_entities, get_entity_schema, to_snake_case,
    get_calculated_fields, get_raw_fields
)
from orchestration.formula_parser import (
    parse_formula, get_field_dependencies,
    ASTNode, FieldRef, FuncCall, BinaryOp, UnaryOp, Concat,
    LiteralBool, LiteralInt, LiteralString
)


# =============================================================================
# AST TO GRAPH CONVERSION
# =============================================================================

def ast_to_graph(ast: ASTNode, field_name: str) -> Dict[str, Any]:
    """
    Convert a parsed AST into a graph representation suitable for explanations.

    Returns a dict with:
    - root_node: ID of the root node
    - nodes: dict of node_id -> node definition
    - edges: list of [source, target] pairs (inputs -> outputs)
    """
    nodes = {}
    edges = []
    node_counter = [0]  # Use list for mutable counter in nested function

    def make_node_id(prefix: str) -> str:
        node_counter[0] += 1
        return f"n_{prefix}_{node_counter[0]}"

    def visit(node: ASTNode) -> str:
        """Visit an AST node and return its graph node ID."""

        if isinstance(node, LiteralBool):
            node_id = make_node_id("const")
            nodes[node_id] = {
                "kind": "const",
                "value": node.value,
                "type": "boolean"
            }
            return node_id

        if isinstance(node, LiteralInt):
            node_id = make_node_id("const")
            nodes[node_id] = {
                "kind": "const",
                "value": node.value,
                "type": "integer"
            }
            return node_id

        if isinstance(node, LiteralString):
            node_id = make_node_id("const")
            nodes[node_id] = {
                "kind": "const",
                "value": node.value,
                "type": "string"
            }
            return node_id

        if isinstance(node, FieldRef):
            node_id = make_node_id("ref")
            nodes[node_id] = {
                "kind": "field_ref",
                "field": node.name,
                "field_snake": to_snake_case(node.name)
            }
            return node_id

        if isinstance(node, UnaryOp):
            operand_id = visit(node.operand)
            node_id = make_node_id("fn")
            nodes[node_id] = {
                "kind": "fn",
                "name": node.op,
                "args": [operand_id]
            }
            edges.append([operand_id, node_id])
            return node_id

        if isinstance(node, BinaryOp):
            left_id = visit(node.left)
            right_id = visit(node.right)
            node_id = make_node_id("op")
            nodes[node_id] = {
                "kind": "op",
                "name": node.op,
                "args": [left_id, right_id]
            }
            edges.append([left_id, node_id])
            edges.append([right_id, node_id])
            return node_id

        if isinstance(node, FuncCall):
            arg_ids = [visit(arg) for arg in node.args]
            node_id = make_node_id("fn")
            nodes[node_id] = {
                "kind": "fn",
                "name": node.name,
                "args": arg_ids
            }
            for arg_id in arg_ids:
                edges.append([arg_id, node_id])
            return node_id

        if isinstance(node, Concat):
            part_ids = [visit(part) for part in node.parts]
            node_id = make_node_id("op")
            nodes[node_id] = {
                "kind": "op",
                "name": "CONCAT",
                "args": part_ids
            }
            for part_id in part_ids:
                edges.append([part_id, node_id])
            return node_id

        raise ValueError(f"Unknown AST node type: {type(node)}")

    # Visit the AST and get the expression root
    expr_root_id = visit(ast)

    # Add the result node that wraps the expression
    result_id = f"n_result_{field_name}"
    nodes[result_id] = {
        "kind": "result",
        "field": field_name,
        "field_snake": to_snake_case(field_name),
        "in": [expr_root_id]
    }
    edges.append([expr_root_id, result_id])

    return {
        "root_node": result_id,
        "nodes": nodes,
        "edges": edges
    }


def compute_template_hash(graph: Dict[str, Any], formula: str) -> str:
    """Compute a deterministic hash for a template graph."""
    # Create a canonical representation
    canonical = {
        "formula": formula,
        "nodes": sorted(graph["nodes"].items()),
        "edges": sorted([tuple(e) for e in graph["edges"]])
    }
    content = json.dumps(canonical, sort_keys=True)
    return f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:16]}"


# =============================================================================
# DEPENDENCY DAG BUILDING
# =============================================================================

def build_calc_order(calculated_fields: List[Dict], raw_field_names: Set[str]) -> tuple:
    """
    Build calculation order (topological sort) for calculated fields.

    Returns:
    - calc_order: list of field names in evaluation order
    - dep_edges: list of [dependency, dependent] pairs
    """
    # Parse formulas and get dependencies
    field_deps = {}
    for field in calculated_fields:
        formula = field.get('formula', '')
        try:
            ast = parse_formula(formula)
            deps = get_field_dependencies(ast)
            field_deps[field['name']] = set(deps)
        except Exception as e:
            print(f"Warning: Failed to parse formula for {field['name']}: {e}")
            field_deps[field['name']] = set()

    # Build dependency edges (sorted for deterministic output)
    dep_edges = []
    for field_name in sorted(field_deps.keys()):
        for dep in sorted(field_deps[field_name]):
            dep_edges.append([dep, field_name])

    # Topological sort
    calc_order = []
    assigned = set(raw_field_names)
    remaining = {f['name'] for f in calculated_fields}

    while remaining:
        # Find fields whose dependencies are all assigned
        ready = []
        for name in remaining:
            deps = field_deps.get(name, set())
            if deps <= assigned:
                ready.append(name)

        if not ready:
            # Circular dependency - add remaining and warn
            print(f"Warning: Possible circular dependency in: {remaining}")
            calc_order.extend(sorted(remaining))
            break

        # Add ready fields (sorted for determinism)
        for name in sorted(ready):
            calc_order.append(name)
            assigned.add(name)
            remaining.remove(name)

    return calc_order, dep_edges


# =============================================================================
# MAIN GENERATION
# =============================================================================

def generate_explain_spec(rulebook: Dict) -> Dict[str, Any]:
    """Generate the complete explain_spec.json content."""

    # Compute rulebook hash
    rulebook_content = json.dumps(rulebook, sort_keys=True)
    rulebook_hash = f"sha256:{hashlib.sha256(rulebook_content.encode()).hexdigest()[:32]}"

    spec = {
        "schema_version": "erb.explain_spec.v1",
        "rulebook": {
            "name": rulebook.get("Name", "Unknown"),
            "rulebook_hash": rulebook_hash
        },
        "semantics": {
            "profile": "excel",
            "version": "v1",
            "null_handling": "three_valued_logic",
            "boolean_coercion": "strict"
        },
        "entities": {}
    }

    # Process each entity
    entities = discover_entities(rulebook)

    for entity_name in entities:
        schema = get_entity_schema(rulebook, entity_name)
        calculated_fields = get_calculated_fields(schema)

        if not calculated_fields:
            continue  # Skip entities with no calculated fields

        # Get entity description from rulebook
        entity_data = rulebook.get(entity_name, {})
        entity_description = entity_data.get('Description', '') if isinstance(entity_data, dict) else ''

        raw_fields = get_raw_fields(schema)
        raw_field_names = {f['name'] for f in raw_fields}

        # Find ID field
        id_field = None
        for field in schema:
            if field.get('nullable') == False:
                id_field = field['name']
                break

        # Build field info with descriptions
        fields_info = {}
        for field in schema:
            field_info = {
                "datatype": field.get('datatype', 'string'),
                "nullable": field.get('nullable', True),
                "type": field.get('type', 'raw')
            }
            # Include description if available
            if field.get('Description'):
                field_info["description"] = field.get('Description')
            fields_info[field['name']] = field_info

        # Build calculation order and dependency edges
        calc_order, dep_edges = build_calc_order(calculated_fields, raw_field_names)

        # Build expression templates for each calculated field
        expr_templates = {}
        for field in calculated_fields:
            formula = field.get('formula', '')
            field_description = field.get('Description', '')
            try:
                ast = parse_formula(formula)
                graph = ast_to_graph(ast, field['name'])
                template_hash = compute_template_hash(graph, formula)

                template_info = {
                    "formula_source": formula,
                    "template_hash": template_hash,
                    "root_node": graph["root_node"],
                    "nodes": graph["nodes"],
                    "edges": graph["edges"]
                }
                # Include description if available
                if field_description:
                    template_info["description"] = field_description
                expr_templates[field['name']] = template_info
            except Exception as e:
                print(f"Warning: Failed to build template for {field['name']}: {e}")
                template_info = {
                    "formula_source": formula,
                    "template_hash": "error",
                    "error": str(e),
                    "root_node": None,
                    "nodes": {},
                    "edges": []
                }
                if field_description:
                    template_info["description"] = field_description
                expr_templates[field['name']] = template_info

        entity_spec = {
            "id_field": id_field,
            "id_field_snake": to_snake_case(id_field) if id_field else None,
            "fields": fields_info,
            "calc_order": calc_order,
            "dep_edges": dep_edges,
            "expr_templates": expr_templates
        }
        # Include entity description if available
        if entity_description:
            entity_spec["description"] = entity_description
        spec["entities"][entity_name] = entity_spec

    return spec


def clean_directory(dir_path: Path, pattern: str = "*.json") -> int:
    """Clean all files matching pattern in directory. Returns count of removed files."""
    import glob
    removed = 0
    if dir_path.exists():
        for file_path in dir_path.glob(pattern):
            try:
                file_path.unlink()
                print(f"  Removed: {file_path.name}")
                removed += 1
            except Exception as e:
                print(f"  Failed to remove {file_path.name}: {e}")
    return removed


def main():
    # Files generated by this script
    GENERATED_FILES = [
        'generated/explain_spec.json',
    ]

    # Directories with generated content (cleaned separately)
    GENERATED_DIRS = [
        ('test-answers', '*.json'),
        ('test-explanations', '*.jsonl'),
    ]

    # Handle --clean argument
    if '--clean' in sys.argv:
        script_dir = Path(__file__).resolve().parent
        print("=" * 60)
        print("CLEAN MODE: EXPLAIN-DAG")
        print("=" * 60)
        print("ExplainDAG substrate: Removes generated spec and test files")
        print()

        # Clean individual files
        for filename in GENERATED_FILES:
            file_path = script_dir / filename
            if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"  Removed: {filename}")
                except Exception as e:
                    print(f"  Failed to remove {filename}: {e}")
            else:
                print(f"  Skipped (not found): {filename}")

        # Clean directories
        for dir_name, pattern in GENERATED_DIRS:
            dir_path = script_dir / dir_name
            print(f"\nCleaning {dir_name}/...")
            removed = clean_directory(dir_path, pattern)
            if removed == 0:
                print("  No files to clean")

        return

    script_dir = Path(__file__).resolve().parent

    print("=" * 70)
    print("ExplainDAG Execution Substrate - AST Template Generator")
    print("=" * 70)
    print()

    # Load the rulebook
    print("Loading rulebook...")
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Discover entities
    entities = discover_entities(rulebook)
    print(f"Discovered {len(entities)} entities: {', '.join(entities)}")
    print()

    # Show calculated fields per entity
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
    print(f"Total: {total_fields} calculated fields to template")
    print()
    print("-" * 70)
    print()

    # Generate explain_spec.json
    print("Generating explain_spec.json...")
    spec = generate_explain_spec(rulebook)

    # Ensure generated directory exists
    generated_dir = script_dir / "generated"
    generated_dir.mkdir(exist_ok=True)

    spec_path = generated_dir / "explain_spec.json"
    spec_path.write_text(json.dumps(spec, indent=2), encoding='utf-8')
    print(f"Wrote: {spec_path}")

    # Print summary
    print()
    print("Template Summary:")
    for entity_name, entity_spec in spec["entities"].items():
        templates = entity_spec.get("expr_templates", {})
        errors = sum(1 for t in templates.values() if t.get("error"))
        print(f"  {entity_name}: {len(templates)} templates, {errors} errors")

    print()
    print("=" * 70)
    print("Generation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
