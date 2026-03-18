#!/usr/bin/env python3
"""
Generate Python calculation library from the Effortless Rulebook.

This script reads formulas from the rulebook and generates erb_calc.py
with proper calculation functions for ALL entities with calculated fields.

Generated file is shared by Python, English, YAML, and other substrates.

================================================================================
ARCHITECTURE OVERVIEW
================================================================================

The ERB (Effortless Rulebook) pattern separates data into:
  - Raw fields: Input data stored directly (e.g., quantity, unit_price)
  - Calculated fields: Derived values computed from formulas (e.g., total = quantity * unit_price)

This injector generates Python code that computes calculated fields in the
correct dependency order using a DAG (Directed Acyclic Graph) approach.

DEPENDENCY ORDER EXAMPLE:
  Raw fields (Level 0):     quantity, unit_price
  Level 1 calculations:     line_total = quantity * unit_price
  Level 2 calculations:     tax_amount = line_total * tax_rate
  Level 3 calculations:     grand_total = line_total + tax_amount

Each level only depends on fields from previous levels, ensuring correct
computation order without circular dependencies.

GENERATED OUTPUT:
  - Individual calc_<entity>_<field>() functions for each calculated field
  - compute_<entity>_fields(record) functions to compute all fields for an entity
  - compute_all_calculated_fields(record, entity_name) dispatcher function

================================================================================
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Set

# Add project root to path for shared imports (needed for orchestration modules)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Shared utilities for loading rulebook data and working with entity schemas
from orchestration.shared import (
    load_rulebook, get_candidate_name_from_cwd, handle_clean_arg,
    discover_entities, get_entity_schema, to_snake_case,
    get_calculated_fields, get_raw_fields
)

# Formula parsing utilities to convert ERB formula syntax to Python expressions
from orchestration.formula_parser import (
    parse_formula, compile_to_python, get_field_dependencies,
    ExprNode, FieldRef, FuncCall, Concat, LiteralString
)


def build_dag_levels(calculated_fields: List[Dict], raw_field_names: Set[str]) -> List[List[Dict]]:
    """
    Build DAG (Directed Acyclic Graph) levels for calculated fields based on dependencies.

    This is the core algorithm that determines computation order. Fields are grouped
    into levels where each level only depends on fields from previous levels.

    Level 0: Raw fields (not returned, just used as the base dependency set)
    Level 1+: Calculated fields ordered by dependency depth

    ALGORITHM:
    1. Parse each formula to extract field dependencies
    2. Start with raw fields as "assigned" (available for use)
    3. Repeatedly find fields whose dependencies are all assigned
    4. Add those fields to the current level and mark them as assigned
    5. Repeat until all fields are assigned or a circular dependency is detected

    Args:
        calculated_fields: List of field definitions with 'name' and 'formula' keys
        raw_field_names: Set of raw field names that are available as inputs

    Returns:
        List of levels, where each level is a list of field definitions
        that can be computed in parallel (all dependencies satisfied)
    """
    # -------------------------------------------------------------------------
    # STEP 1: Parse all formulas and extract their field dependencies
    # -------------------------------------------------------------------------
    # field_deps maps field_name -> set of field names it depends on
    field_deps = {}
    for field in calculated_fields:
        formula = field.get('formula', '')
        try:
            # Parse the formula into an expression tree and extract referenced fields
            expr = parse_formula(formula)
            deps = get_field_dependencies(expr)
            # Normalize to snake_case for consistent comparison
            field_deps[field['name']] = set(to_snake_case(d) for d in deps)
        except Exception as e:
            print(f"Warning: Failed to parse formula for {field['name']}: {e}")
            field_deps[field['name']] = set()

    # -------------------------------------------------------------------------
    # STEP 2: Build levels using iterative dependency resolution
    # -------------------------------------------------------------------------
    levels = []

    # Start with raw fields as "assigned" - these are available without computation
    assigned = set(to_snake_case(name) for name in raw_field_names)

    # Track which fields still need to be placed in a level
    remaining = {f['name']: f for f in calculated_fields}

    while remaining:
        # Find all fields whose dependencies are fully satisfied
        # (i.e., all deps are in the 'assigned' set)
        current_level = []
        for name, field in list(remaining.items()):
            deps = field_deps.get(name, set())
            # Check if all dependencies are satisfied (deps is a subset of assigned)
            if deps <= assigned:
                current_level.append(field)

        if not current_level:
            # No progress possible - either circular dependency or missing field
            # Add remaining fields to a final level with a warning
            print(f"Warning: Could not resolve dependencies for: {list(remaining.keys())}")
            levels.append(list(remaining.values()))
            break

        # Add the current level to our result
        levels.append(current_level)

        # Mark all fields in this level as assigned (available for next level)
        for field in current_level:
            assigned.add(to_snake_case(field['name']))
            del remaining[field['name']]

    return levels


def generate_function_signature(entity_name: str, field_name: str, deps: List[str]) -> str:
    """
    Generate a Python function signature with entity-namespaced function name.

    NAMING CONVENTION:
      calc_<entity>_<field>(dep1, dep2, ...)

    Example:
      Entity: "LineItem", Field: "total", Dependencies: ["quantity", "unit_price"]
      Output: def calc_line_item_total(quantity, unit_price):

    This namespacing prevents collisions when multiple entities have
    fields with the same name (e.g., both Order and LineItem might have 'total').

    Args:
        entity_name: The entity name (e.g., "LineItem", "Order")
        field_name: The calculated field name (e.g., "total", "tax_amount")
        deps: List of field names this calculation depends on

    Returns:
        A Python function definition line (e.g., "def calc_line_item_total(quantity, unit_price):")
    """
    entity_snake = to_snake_case(entity_name)
    field_snake = to_snake_case(field_name)
    func_name = f"calc_{entity_snake}_{field_snake}"
    params = [to_snake_case(d) for d in deps]
    params_str = ", ".join(params) if params else ""
    return f"def {func_name}({params_str}):"


def generate_calc_function(entity_name: str, field: Dict) -> str:
    """
    Generate a complete Python calculation function for a single field.

    This function takes an ERB formula and produces a pure Python function
    that computes the field value from its dependencies.

    TRANSFORMATION PIPELINE:
      1. Parse the ERB formula into an expression tree
      2. Extract field dependencies from the expression tree
      3. Compile the expression tree to a Python expression
      4. Generate a function with the deps as parameters

    EXAMPLE:
      Input formula: "Quantity * UnitPrice"
      Output:
        def calc_line_item_total(quantity, unit_price):
            '''Formula: Quantity * UnitPrice'''
            return quantity * unit_price

    Args:
        entity_name: The entity this field belongs to (for namespacing)
        field: Field definition dict with 'name' and 'formula' keys

    Returns:
        Complete Python function definition as a string
    """
    name = field['name']
    formula = field.get('formula', '')
    description = field.get('Description', '')
    entity_snake = to_snake_case(entity_name)
    field_snake = to_snake_case(name)

    # -------------------------------------------------------------------------
    # Parse the formula and compile to Python
    # -------------------------------------------------------------------------
    try:
        expr = parse_formula(formula)           # Parse ERB formula
        deps = get_field_dependencies(expr)     # Extract field references
        python_expr = compile_to_python(expr)   # Convert to Python expression
    except Exception as e:
        # If parsing fails, generate a stub function that raises an error
        # This allows the generated file to still be syntactically valid
        return f'''
def calc_{entity_snake}_{field_snake}():
    """ERROR: Could not parse formula: {formula}
    Error: {e}
    """
    raise NotImplementedError("Formula parsing failed")
'''

    # -------------------------------------------------------------------------
    # Build the function definition
    # -------------------------------------------------------------------------
    lines = []

    # Function signature with dependencies as parameters
    sig = generate_function_signature(entity_name, name, deps)
    lines.append(sig)

    # Docstring preserves the original formula and description for documentation
    # (escape special characters that would break the docstring)
    formula_escaped = formula.replace('\\', '\\\\').replace('"""', "'''")
    # Prevent """" at end of docstring if formula ends with a quote
    if formula_escaped.endswith('"'):
        formula_escaped = formula_escaped + ' '

    # Build multi-line docstring if we have a description
    if description:
        desc_escaped = description.replace('\\', '\\\\').replace('"""', "'''")
        lines.append(f'    """')
        lines.append(f'    {desc_escaped}')
        lines.append(f'    ')
        lines.append(f'    Formula: {formula_escaped}')
        lines.append(f'    """')
    else:
        lines.append(f'    """Formula: {formula_escaped}"""')

    # The actual computation - just returns the compiled Python expression
    lines.append(f'    return {python_expr}')

    return '\n'.join(lines)


def generate_entity_compute_function(
    entity_name: str,
    calculated_fields: List[Dict],
    dag_levels: List[List[Dict]],
    string_fields: List[str],
    entity_description: str = ''
) -> str:
    """
    Generate a compute function that calculates ALL fields for a specific entity.

    This is the main entry point for computing an entity's calculated fields.
    It orchestrates calls to individual calc_* functions in the correct
    dependency order (by DAG level).

    GENERATED FUNCTION STRUCTURE:
        def compute_<entity>_fields(record: dict) -> dict:
            result = dict(record)  # Copy input to preserve original

            # Level 1 calculations
            result['field_a'] = calc_entity_field_a(result.get('raw_1'), ...)

            # Level 2 calculations (depends on Level 1)
            result['field_b'] = calc_entity_field_b(result.get('field_a'), ...)

            # ... more levels ...

            # Post-processing (e.g., empty string -> None)
            return result

    Args:
        entity_name: Name of the entity (e.g., "LineItem")
        calculated_fields: All calculated field definitions for this entity
        dag_levels: Fields organized by dependency level (from build_dag_levels)
        string_fields: List of string-type calculated fields (for post-processing)
        entity_description: Optional description of the entity from the rulebook

    Returns:
        Complete Python function definition as a string
    """
    entity_snake = to_snake_case(entity_name)

    lines = []
    lines.append(f'def compute_{entity_snake}_fields(record: dict) -> dict:')
    if entity_description:
        desc_escaped = entity_description.replace('\\', '\\\\').replace('"""', "'''")
        lines.append(f'    """')
        lines.append(f'    Compute all calculated fields for {entity_name}.')
        lines.append(f'    ')
        lines.append(f'    {desc_escaped}')
        lines.append(f'    """')
    else:
        lines.append(f'    """Compute all calculated fields for {entity_name}."""')

    # Start with a copy of the input record to avoid mutating the original
    lines.append('    result = dict(record)')
    lines.append('')

    # -------------------------------------------------------------------------
    # Generate calculation calls for each DAG level
    # -------------------------------------------------------------------------
    # Each level's calculations can safely reference results from previous levels
    for level_idx, level_fields in enumerate(dag_levels):
        lines.append(f'    # Level {level_idx + 1} calculations')
        for field in level_fields:
            name = field['name']
            snake_name = to_snake_case(name)

            # Re-parse formula to get dependencies for the function call
            try:
                expr = parse_formula(field.get('formula', ''))
                deps = get_field_dependencies(expr)
            except:
                deps = []

            # Generate the function call with arguments pulled from result dict
            func_name = f"calc_{entity_snake}_{snake_name}"
            if deps:
                # Pass each dependency value from the result dict
                args = [f"result.get('{to_snake_case(dep)}')" for dep in deps]
                args_str = ', '.join(args)
                lines.append(f"    result['{snake_name}'] = {func_name}({args_str})")
            else:
                # No dependencies - call with no arguments
                lines.append(f"    result['{snake_name}'] = {func_name}()")
        lines.append('')

    # -------------------------------------------------------------------------
    # Post-processing: normalize empty strings to None for string fields
    # -------------------------------------------------------------------------
    # This ensures consistent NULL handling across substrates
    if string_fields:
        lines.append('    # Convert empty strings to None for string fields')
        fields_list = ', '.join(f"'{f}'" for f in string_fields)
        lines.append(f"    for key in [{fields_list}]:")
        lines.append("        if result.get(key) == '':")
        lines.append('            result[key] = None')
        lines.append('')

    lines.append('    return result')

    return '\n'.join(lines)


def generate_dispatcher_function(entities_with_calcs: List[str]) -> str:
    """
    Generate a dispatcher function that routes to the correct entity's compute function.

    This is a convenience function that allows callers to compute fields for any
    entity type using a single entry point, without needing to know which specific
    compute_*_fields function to call.

    GENERATED FUNCTION:
        def compute_all_calculated_fields(record: dict, entity_name: str = None) -> dict:
            entity_lower = entity_name.lower().replace('-', '_')

            if entity_lower == 'line_item':
                return compute_line_item_fields(record)
            elif entity_lower == 'order':
                return compute_order_fields(record)
            # ... etc ...
            else:
                return dict(record)  # Unknown entity, pass through

    USAGE:
        result = compute_all_calculated_fields(raw_data, "LineItem")
        result = compute_all_calculated_fields(raw_data, "line_item")  # Also works

    Args:
        entities_with_calcs: List of entity names that have calculated fields

    Returns:
        Complete Python function definition as a string
    """
    lines = []
    lines.append('def compute_all_calculated_fields(record: dict, entity_name: str = None) -> dict:')
    lines.append('    """')
    lines.append('    Compute all calculated fields for a record.')
    lines.append('    ')
    lines.append('    This is the main entry point for computing calculated fields.')
    lines.append('    It routes to the appropriate entity-specific compute function.')
    lines.append('    ')
    lines.append('    Args:')
    lines.append('        record: The record dict with raw field values')
    lines.append('        entity_name: Entity name (snake_case or PascalCase)')
    lines.append('    ')
    lines.append('    Returns:')
    lines.append('        Record dict with calculated fields filled in')
    lines.append('    """')

    # Handle case where no entity name is provided
    lines.append('    if entity_name is None:')
    lines.append('        # No entity specified - return record unchanged')
    lines.append('        return dict(record)')
    lines.append('')

    # Normalize entity name to handle various input formats
    lines.append('    # Normalize to snake_case to support "LineItem", "line_item", "line-item"')
    lines.append("    entity_lower = entity_name.lower().replace('-', '_')")
    lines.append('')

    # Generate dispatch logic using if/elif chain
    if entities_with_calcs:
        for i, entity in enumerate(entities_with_calcs):
            entity_snake = to_snake_case(entity)
            prefix = 'if' if i == 0 else 'elif'
            lines.append(f"    {prefix} entity_lower == '{entity_snake}':")
            lines.append(f"        return compute_{entity_snake}_fields(record)")

        # Fallback for unknown entities
        lines.append('    else:')
        lines.append('        # Unknown entity - return record unchanged (no error)')
        lines.append('        return dict(record)')
    else:
        # No entities with calculated fields - just return record unchanged
        lines.append('    # No entities have calculated fields in this rulebook')
        lines.append('    return dict(record)')

    return '\n'.join(lines)


def generate_erb_calc(rulebook: Dict) -> str:
    """
    Generate the complete erb_calc.py content for ALL entities in the rulebook.

    This is the main code generation function that produces a complete Python
    module containing:
      1. Individual calc_* functions for each calculated field
      2. compute_*_fields functions for each entity
      3. A dispatcher function for convenience

    GENERATED FILE STRUCTURE:
        '''ERB Calculation Library (GENERATED)'''

        # ========== LINEITEM CALCULATIONS ==========
        # Level 1
        def calc_line_item_subtotal(quantity, unit_price): ...

        # Level 2
        def calc_line_item_total(subtotal, tax_rate): ...

        def compute_line_item_fields(record): ...

        # ========== ORDER CALCULATIONS ==========
        # ... similar structure ...

        # ========== DISPATCHER FUNCTION ==========
        def compute_all_calculated_fields(record, entity_name): ...

    Args:
        rulebook: The loaded ERB rulebook dictionary

    Returns:
        Complete Python module content as a string
    """
    lines = []

    # -------------------------------------------------------------------------
    # File Header
    # -------------------------------------------------------------------------
    lines.append('"""')
    lines.append('ERB Calculation Library (GENERATED - DO NOT EDIT)')
    lines.append('=================================================')
    lines.append('Generated from: effortless-rulebook/effortless-rulebook.json')
    lines.append('')
    lines.append('This file contains pure functions that compute calculated fields')
    lines.append('from raw field values. Supports multiple entities.')
    lines.append('"""')
    lines.append('')
    lines.append('from typing import Optional, Any')
    lines.append('')

    # -------------------------------------------------------------------------
    # Discover and process all entities
    # -------------------------------------------------------------------------
    entities = discover_entities(rulebook)
    entities_with_calcs = []  # Track which entities have calculated fields

    for entity_name in entities:
        schema = get_entity_schema(rulebook, entity_name)
        calculated_fields = get_calculated_fields(schema)

        # Skip entities that have no calculated fields
        if not calculated_fields:
            continue

        entities_with_calcs.append(entity_name)

        # Get entity description from rulebook
        entity_data = rulebook.get(entity_name, {})
        entity_description = entity_data.get('Description', '') if isinstance(entity_data, dict) else ''

        # Get raw fields for DAG building (these are the "level 0" inputs)
        raw_fields = get_raw_fields(schema)
        raw_field_names = {f['name'] for f in raw_fields}

        # Identify string-type calculated fields for post-processing
        # (empty strings will be converted to None)
        string_fields = [
            to_snake_case(f['name'])
            for f in calculated_fields
            if f.get('datatype') == 'string'
        ]

        # Build dependency levels for this entity
        dag_levels = build_dag_levels(calculated_fields, raw_field_names)

        # ---------------------------------------------------------------------
        # Generate entity section header
        # ---------------------------------------------------------------------
        entity_snake = to_snake_case(entity_name)
        lines.append('')
        lines.append('# ' + '=' * 77)
        lines.append(f'# {entity_name.upper()} CALCULATIONS')
        if entity_description:
            lines.append(f'# {entity_description}')
        lines.append('# ' + '=' * 77)

        # ---------------------------------------------------------------------
        # Generate individual calculation functions, organized by DAG level
        # ---------------------------------------------------------------------
        for level_idx, level_fields in enumerate(dag_levels):
            lines.append('')
            lines.append(f'# Level {level_idx + 1}')

            for field in level_fields:
                lines.append('')
                lines.append(generate_calc_function(entity_name, field))

        # ---------------------------------------------------------------------
        # Generate the entity's compute function
        # ---------------------------------------------------------------------
        lines.append('')
        lines.append('')
        lines.append(generate_entity_compute_function(
            entity_name, calculated_fields, dag_levels, string_fields, entity_description
        ))

    # -------------------------------------------------------------------------
    # Generate dispatcher function (routes to correct entity compute function)
    # -------------------------------------------------------------------------
    lines.append('')
    lines.append('')
    lines.append('# ' + '=' * 77)
    lines.append('# DISPATCHER FUNCTION')
    lines.append('# ' + '=' * 77)
    lines.append('')
    lines.append(generate_dispatcher_function(entities_with_calcs))

    return '\n'.join(lines)


def main():
    """
    Main entry point for the Python substrate injector.

    WORKFLOW:
    1. Load the ERB rulebook (effortless-rulebook.json)
    2. Discover all entities and their calculated fields
    3. Generate erb_calc.py with calculation functions
    4. Write the generated file to the substrate directory

    USAGE:
        python inject-into-python.py          # Generate erb_calc.py
        python inject-into-python.py --clean  # Remove generated files

    The generated erb_calc.py can then be imported by other Python code
    or by other substrates (English, YAML, etc.) that need to compute
    calculated fields.
    """
    # -------------------------------------------------------------------------
    # Configuration: files generated by this script
    # -------------------------------------------------------------------------
    GENERATED_FILES = [
        'erb_calc.py',
    ]

    # Handle --clean argument (removes generated files and exits)
    if handle_clean_arg(GENERATED_FILES, "Python substrate: Removes generated calculation library"):
        return

    script_dir = Path(__file__).resolve().parent

    # -------------------------------------------------------------------------
    # Print banner and load rulebook
    # -------------------------------------------------------------------------
    print("=" * 70)
    print("Python Execution Substrate - Multi-Entity Formula Compiler")
    print("=" * 70)
    print()

    print("Loading rulebook...")
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # Discover entities and display summary
    # -------------------------------------------------------------------------
    entities = discover_entities(rulebook)
    print(f"Discovered {len(entities)} entities: {', '.join(entities)}")
    print()

    # Show calculated fields per entity for user visibility
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

    # -------------------------------------------------------------------------
    # Generate and write erb_calc.py
    # -------------------------------------------------------------------------
    print("Generating erb_calc.py...")
    erb_calc_content = generate_erb_calc(rulebook)

    erb_calc_path = script_dir / "erb_calc.py"
    erb_calc_path.write_text(erb_calc_content, encoding='utf-8')
    print(f"Wrote: {erb_calc_path} ({len(erb_calc_content)} bytes)")

    print()
    print("=" * 70)
    print("Generation complete!")
    print("=" * 70)


# =============================================================================
# SCRIPT ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    main()
