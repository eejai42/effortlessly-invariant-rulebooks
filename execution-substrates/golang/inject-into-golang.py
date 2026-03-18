#!/usr/bin/env python3
"""
Generic Rulebook-to-Go transpiler.

This script reads the effortless-rulebook.json and generates a Go SDK
with structs and calculation functions for ALL tables defined in the rulebook.

Following the pattern of the xlsx generator, this script is domain-agnostic -
it reads whatever tables and schemas are defined and generates corresponding Go code.

Generated files:
- erb_sdk.go - Structs, individual Calc* methods, and ComputeAll functions
- main.go - Test runner for all tables with calculated fields
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Any, Set

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from orchestration.shared import load_rulebook, get_candidate_name_from_cwd, handle_clean_arg
from orchestration.formula_parser import (
    parse_formula, compile_to_go, get_field_dependencies,
    to_snake_case, to_pascal_case, ExprNode, FuncCall
)


# =============================================================================
# UTILITY FUNCTIONS (Domain-agnostic helpers)
# =============================================================================

def get_table_names(rulebook: Dict) -> List[str]:
    """Extract table names from the rulebook (excluding metadata keys).

    This matches the xlsx generator's approach to discovering tables.
    """
    metadata_keys = {'$schema', 'model_name', 'Description', '_meta'}
    return [key for key in rulebook.keys() if key not in metadata_keys]


def get_calculated_fields(schema: List[Dict]) -> List[Dict]:
    """Extract all calculated fields from a schema."""
    return [
        field for field in schema
        if field.get('type') == 'calculated' and field.get('formula')
    ]


def get_aggregation_fields(schema: List[Dict]) -> List[Dict]:
    """Extract all aggregation fields from a schema."""
    return [
        field for field in schema
        if field.get('type') == 'aggregation' and field.get('formula')
    ]


def get_lookup_fields(schema: List[Dict]) -> List[Dict]:
    """Extract all lookup fields from a schema (INDEX/MATCH formulas)."""
    return [
        field for field in schema
        if field.get('type') == 'lookup' and field.get('formula')
    ]


def get_all_computed_fields(schema: List[Dict]) -> List[Dict]:
    """Extract ALL fields that need computation: calculated, lookup, or aggregation."""
    return [
        field for field in schema
        if field.get('type') in ('calculated', 'lookup', 'aggregation') and field.get('formula')
    ]


def parse_countifs_formula(formula: str):
    """
    Parse a COUNTIFS formula to extract table and field references.

    Formula format: =COUNTIFS(RelatedTable!{{LookupField}}, CurrentTable!{{MatchField}})
    Example: =COUNTIFS(WorkflowSteps!{{Workflow}}, Workflows!{{WorkflowId}})

    Returns: (related_table, lookup_field, match_field) or (None, None, None) if not parseable
    """
    # Match pattern: COUNTIFS(Table!{{Field}}, Table!{{Field}})
    pattern = r'=COUNTIFS\((\w+)!\{\{(\w+)\}\},\s*\w+!\{\{(\w+)\}\}\)'
    match = re.match(pattern, formula)
    if match:
        related_table = match.group(1)  # e.g., "WorkflowSteps"
        lookup_field = match.group(2)   # e.g., "Workflow"
        match_field = match.group(3)    # e.g., "WorkflowId"
        return (related_table, lookup_field, match_field)
    return (None, None, None)


def parse_index_match_formula(formula: str):
    """
    Parse an INDEX/MATCH formula to extract the lookup components.

    Formula format: =INDEX(Table!{{FieldToReturn}}, MATCH(CurrentTable!{{KeyField}}, Table!{{PrimaryKeyField}}, 0))
    Example: =INDEX(Workflows!{{Title}}, MATCH(WorkflowSteps!{{IsStepOf}}, Workflows!{{WorkflowId}}, 0))

    Returns: (lookup_table, return_field, key_field, pk_field) or (None, None, None, None) if not parseable
    """
    # Match pattern: INDEX(Table!{{Field}}, MATCH(Table!{{Field}}, Table!{{Field}}, 0))
    pattern = r'=INDEX\((\w+)!\{\{(\w+)\}\},\s*MATCH\(\w+!\{\{(\w+)\}\},\s*(\w+)!\{\{(\w+)\}\},\s*0\)\)'
    match = re.match(pattern, formula)
    if match:
        lookup_table = match.group(1)    # e.g., "Workflows"
        return_field = match.group(2)    # e.g., "Title"
        key_field = match.group(3)       # e.g., "IsStepOf"
        # pk_table = match.group(4)      # Should match lookup_table
        pk_field = match.group(5)        # e.g., "WorkflowId"
        return (lookup_table, return_field, key_field, pk_field)
    return (None, None, None, None)


def parse_sumifs_formula(formula: str):
    """
    Parse a SUMIFS formula to extract table and field references.

    Formula format: =SUMIFS(RelatedTable!{{SumField}}, RelatedTable!{{CriteriaField}}, CurrentTable!{{MatchField}})
    Example: =SUMIFS(WorkflowSteps!{{Name}}, WorkflowSteps!{{AssignedRole}}, Roles!{{RoleId}})

    Returns: (related_table, sum_field, criteria_field, match_field) or (None, None, None, None) if not parseable
    """
    pattern = r'=SUMIFS\((\w+)!\{\{(\w+)\}\},\s*(\w+)!\{\{(\w+)\}\},\s*\w+!\{\{(\w+)\}\}\)'
    match = re.match(pattern, formula)
    if match:
        related_table = match.group(1)  # e.g., "WorkflowSteps"
        sum_field = match.group(2)      # e.g., "Name"
        # criteria_table = match.group(3) - should match related_table
        criteria_field = match.group(4) # e.g., "AssignedRole"
        match_field = match.group(5)    # e.g., "RoleId"
        return (related_table, sum_field, criteria_field, match_field)
    return (None, None, None, None)


def get_raw_fields(schema: List[Dict]) -> List[Dict]:
    """Extract all raw fields from a schema."""
    return [field for field in schema if field.get('type') == 'raw']


def get_input_fields(schema: List[Dict]) -> List[Dict]:
    """Extract all input fields from a schema (raw, aggregation, relationship, lookup).

    These are fields that serve as inputs to calculated fields - they need to be
    in the struct but don't have formulas themselves. Aggregation fields are
    counts/sums from related tables, relationship fields are FK references,
    lookup fields are values from related tables via INDEX/MATCH formulas.
    """
    input_types = {'raw', 'aggregation', 'relationship', 'lookup'}
    return [field for field in schema if field.get('type') in input_types]


def uses_string_functions(expr: ExprNode) -> bool:
    """Check if an expression uses any functions that require the strings package.

    Functions: LOWER, FIND, SUBSTITUTE
    """
    if isinstance(expr, FuncCall):
        if expr.name in ('LOWER', 'FIND', 'SUBSTITUTE'):
            return True
        return any(uses_string_functions(arg) for arg in expr.args)

    # Check recursively for other node types
    from orchestration.formula_parser import BinaryOp, UnaryOp, Concat
    if isinstance(expr, BinaryOp):
        return uses_string_functions(expr.left) or uses_string_functions(expr.right)
    if isinstance(expr, UnaryOp):
        return uses_string_functions(expr.operand)
    if isinstance(expr, Concat):
        return any(uses_string_functions(part) for part in expr.parts)

    return False


def rulebook_needs_strings_import(rulebook: Dict) -> bool:
    """Check if any formula in the rulebook uses string functions."""
    table_names = get_table_names(rulebook)
    for table_name in table_names:
        table_data = rulebook.get(table_name, {})
        if not isinstance(table_data, dict) or 'schema' not in table_data:
            continue
        for field in table_data['schema']:
            formula = field.get('formula', '')
            if formula:
                try:
                    expr = parse_formula(formula)
                    if uses_string_functions(expr):
                        return True
                except Exception:
                    pass
    return False


def build_field_types(schema: List[Dict]) -> Dict[str, str]:
    """Build a dict mapping field names to their datatypes.

    Used for type-aware code generation (e.g., intToString vs stringVal in Go).
    """
    return {field['name']: field.get('datatype', 'string') for field in schema}


def datatype_to_go(datatype: str, nullable: bool = True) -> str:
    """Convert rulebook datatype to Go type."""
    dt = datatype.lower()
    if dt == 'boolean':
        return '*bool' if nullable else 'bool'
    elif dt == 'integer':
        return '*int' if nullable else 'int'
    else:
        return '*string' if nullable else 'string'


def table_name_to_struct_name(table_name: str) -> str:
    """Convert a table name to a Go struct name.

    Examples:
        LanguageCandidates -> LanguageCandidate (singular)
        IsEverythingALanguage -> IsEverythingALanguage (unchanged)
    """
    # Simple pluralization handling - remove trailing 's' if present
    if table_name.endswith('s') and not table_name.endswith('ss'):
        return table_name[:-1]
    return table_name


def build_dag_levels(calculated_fields: List[Dict], raw_field_names: Set[str]) -> List[List[Dict]]:
    """Build DAG levels for calculated fields based on dependencies.

    This ensures fields are computed in the correct order - fields that depend
    on other calculated fields are placed in later levels.
    """
    field_deps = {}
    for field in calculated_fields:
        formula = field.get('formula', '')
        try:
            expr = parse_formula(formula)
            deps = get_field_dependencies(expr)
            field_deps[field['name']] = set(d for d in deps)
        except Exception as e:
            print(f"Warning: Failed to parse formula for {field['name']}: {e}")
            field_deps[field['name']] = set()

    levels = []
    assigned = set(raw_field_names)
    remaining = {f['name']: f for f in calculated_fields}

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
            assigned.add(field['name'])
            del remaining[field['name']]

    return levels


# =============================================================================
# CODE GENERATION FUNCTIONS
# =============================================================================

def generate_struct_field(field: Dict) -> str:
    """Generate a Go struct field definition."""
    name = field['name']
    datatype = field.get('datatype', 'string')
    nullable = field.get('nullable', True)
    description = field.get('Description', '')
    field_type = field.get('type', '')
    formula = field.get('formula', '')

    # For SUMIFS aggregation fields, use FlexibleString to handle mixed int/string JSON
    if field_type == 'aggregation' and formula.startswith('=SUMIFS'):
        go_type = '*FlexibleString' if nullable else 'FlexibleString'
    else:
        go_type = datatype_to_go(datatype, nullable)

    json_tag = to_snake_case(name)
    # Add inline comment if description is available
    if description:
        return f'\t{name} {go_type} `json:"{json_tag}"` // {description}'
    return f'\t{name} {go_type} `json:"{json_tag}"`'


def compile_formula_to_go(field: Dict, struct_var: str = 'tc', calc_vars: Dict[str, str] = None,
                          field_types: Dict[str, str] = None) -> str:
    """Compile a field's formula to a Go expression.

    Returns the Go expression string, or a panic statement if parsing fails.

    Args:
        field: The field definition with 'formula' key
        struct_var: Variable name for the struct (e.g., 'tc' for tc.FieldName)
        calc_vars: Dict mapping calculated field names to their local variable names.
                   Used to substitute struct field refs with local vars for deps.
        field_types: Dict mapping field names to their datatypes (e.g., {'OrderNumber': 'integer'})
    """
    formula = field.get('formula', '')
    try:
        expr = parse_formula(formula)
        go_expr = compile_to_go(expr, struct_var, field_types or {})

        # Substitute references to already-computed calculated fields
        # with their local variable names. Order matters - more specific patterns first.
        if calc_vars:
            for field_name, var_name in calc_vars.items():
                # Pattern 1: boolVal(tc.Field) -> var_name (already a bool)
                go_expr = go_expr.replace(f'boolVal({struct_var}.{field_name})', var_name)

                # Pattern 2: stringVal(tc.Field) -> var_name (already a string)
                go_expr = go_expr.replace(f'stringVal({struct_var}.{field_name})', var_name)

                # Pattern 3: (tc.Field != nil && *tc.Field == X) -> (var_name == boolVal(X))
                def wrap_rhs_in_boolval(match):
                    rhs = match.group(1)
                    if rhs.startswith(f'{struct_var}.'):
                        return f'({var_name} == boolVal({rhs}))'
                    return f'({var_name} == {rhs})'
                pattern = rf'\({struct_var}\.{field_name} != nil && \*{struct_var}\.{field_name} == ([^)]+)\)'
                go_expr = re.sub(pattern, wrap_rhs_in_boolval, go_expr)

                # Pattern 4: tc.Field != nil && *tc.Field (without == ) -> var_name
                go_expr = go_expr.replace(f'{struct_var}.{field_name} != nil && *{struct_var}.{field_name}', var_name)

                # Pattern 5: Any remaining tc.Field -> var_name
                go_expr = go_expr.replace(f'{struct_var}.{field_name}', var_name)

        # Fix IF conditions with pointer fields: `if tc.Field {` -> `if boolVal(tc.Field) {`
        go_expr = re.sub(rf'if ({struct_var}\.\w+) \{{', r'if boolVal(\1) {', go_expr)

        return go_expr
    except Exception as e:
        return f'func() interface{{}} {{ panic("Formula parse error: {e}") }}()'


def generate_calc_function(field: Dict, struct_name: str, struct_var: str = 'tc',
                           field_types: Dict[str, str] = None) -> List[str]:
    """Generate an individual Calc* function for a calculated field.

    This mirrors the postgres calc_* function pattern - each calculated field
    gets its own method that can be called independently.
    """
    lines = []
    name = field['name']
    datatype = field.get('datatype', 'string')
    description = field.get('Description', '')

    # Determine return type
    if datatype == 'boolean':
        return_type = 'bool'
    elif datatype == 'integer':
        return_type = 'int'
    else:
        return_type = 'string'

    # Generate the function signature with description if available
    lines.append(f'// Calc{name} computes the {name} calculated field')
    if description:
        # Wrap long descriptions to multiple comment lines
        lines.append(f'// {description}')
    lines.append(f'// Formula: {field.get("formula", "").replace(chr(10), " ").strip()}')
    lines.append(f'func ({struct_var} *{struct_name}) Calc{name}() {return_type} {{')

    # Compile the formula
    go_expr = compile_formula_to_go(field, struct_var, field_types=field_types)
    lines.append(f'\treturn {go_expr}')
    lines.append('}')

    return lines


def generate_compute_all_function(
    struct_name: str,
    input_fields: List[Dict],
    calculated_fields: List[Dict],
    dag_levels: List[List[Dict]],
    struct_var: str = 'tc',
    field_types: Dict[str, str] = None
) -> List[str]:
    """Generate the ComputeAll function that computes all calculated fields.

    This function calls each individual Calc* method in DAG order and returns
    a new struct with all fields populated.

    Args:
        input_fields: All non-calculated fields (raw, aggregation, relationship)
    """
    lines = []

    lines.append('// ComputeAll computes all calculated fields and returns an updated struct')
    lines.append(f'func ({struct_var} *{struct_name}) ComputeAll() *{struct_name} {{')

    # Generate calls to each Calc* function in DAG order
    calc_vars = {}  # Track variable names for calculated fields
    for level_idx, level_fields in enumerate(dag_levels):
        lines.append(f'\t// Level {level_idx + 1} calculations')
        for field in level_fields:
            name = field['name']
            var_name = name[0].lower() + name[1:]  # camelCase

            # For level 1, call the Calc method directly
            # For level 2+, we need to pass already-computed values
            # But since Calc* methods read from struct, we need to update struct first
            # Actually, let's compute inline for proper dependency handling
            go_expr = compile_formula_to_go(field, struct_var, calc_vars, field_types)
            lines.append(f'\t{var_name} := {go_expr}')

            calc_vars[name] = var_name
        lines.append('')

    # Generate return struct with all fields
    lines.append(f'\treturn &{struct_name}{{')
    for field in input_fields:
        name = field['name']
        lines.append(f'\t\t{name}: {struct_var}.{name},')
    for field in calculated_fields:
        name = field['name']
        var_name = calc_vars[name]
        datatype = field.get('datatype', 'string')
        # Use nilIfEmpty for string fields to return null for empty strings
        if datatype == 'string' or datatype not in ('boolean', 'integer'):
            lines.append(f'\t\t{name}: nilIfEmpty({var_name}),')
        else:
            lines.append(f'\t\t{name}: &{var_name},')
    lines.append('\t}')
    lines.append('}')

    return lines


def generate_struct_for_table(table_name: str, schema: List[Dict], entity_description: str = '') -> List[str]:
    """Generate the struct definition for a table."""
    lines = []
    struct_name = table_name_to_struct_name(table_name)

    input_fields = get_input_fields(schema)
    calculated_fields = get_calculated_fields(schema)

    # Struct needs all fields - calculated fields override input fields with same name
    calculated_names = {f['name'] for f in calculated_fields}
    all_fields = [f for f in input_fields if f['name'] not in calculated_names] + calculated_fields

    lines.append(f'// {struct_name} represents a row in the {table_name} table')
    if entity_description:
        lines.append(f'// {entity_description}')
    lines.append(f'type {struct_name} struct {{')
    for field in all_fields:
        lines.append(generate_struct_field(field))
    lines.append('}')

    return lines


def generate_table_sdk(table_name: str, table_data: Dict) -> List[str]:
    """Generate complete SDK code for a single table.

    This includes:
    - Struct definition
    - Individual Calc* functions for each calculated field
    - ComputeAll function to compute all calculated fields
    """
    lines = []
    schema = table_data.get('schema', [])
    struct_name = table_name_to_struct_name(table_name)
    entity_description = table_data.get('Description', '')

    input_fields = get_input_fields(schema)
    calculated_fields = get_calculated_fields(schema)
    input_field_names = {f['name'] for f in input_fields}

    # Build field types map for type-aware code generation
    field_types = build_field_types(schema)

    # Section header
    lines.append(f'// =============================================================================')
    lines.append(f'// {table_name.upper()} TABLE')
    if entity_description:
        lines.append(f'// {entity_description}')
    lines.append(f'// =============================================================================')
    lines.append('')

    # Struct definition
    lines.extend(generate_struct_for_table(table_name, schema, entity_description))
    lines.append('')

    if calculated_fields:
        # Build DAG for calculation ordering
        dag_levels = build_dag_levels(calculated_fields, input_field_names)

        # Individual Calc* functions
        lines.append(f'// --- Individual Calculation Functions ---')
        lines.append('')
        for field in calculated_fields:
            lines.extend(generate_calc_function(field, struct_name, field_types=field_types))
            lines.append('')

        # ComputeAll function
        lines.append(f'// --- Compute All Calculated Fields ---')
        lines.append('')
        lines.extend(generate_compute_all_function(
            struct_name, input_fields, calculated_fields, dag_levels, field_types=field_types
        ))
        lines.append('')

    return lines


def generate_erb_sdk(rulebook: Dict) -> str:
    """Generate the complete erb_sdk.go content.

    This function is domain-agnostic - it reads whatever tables are defined
    in the rulebook and generates corresponding Go code for all of them.
    """
    lines = []

    # Check if we need the strings package
    needs_strings = rulebook_needs_strings_import(rulebook)

    # Header
    lines.append('// ERB SDK - Go Implementation (GENERATED - DO NOT EDIT)')
    lines.append('// ======================================================')
    lines.append('// Generated from: effortless-rulebook/effortless-rulebook.json')
    lines.append('//')
    lines.append('// This file contains structs and calculation functions')
    lines.append('// for all tables defined in the rulebook.')
    lines.append('')
    lines.append('package main')
    lines.append('')
    lines.append('import (')
    lines.append('\t"encoding/json"')
    lines.append('\t"fmt"')
    lines.append('\t"os"')
    lines.append('\t"strconv"')
    if needs_strings:
        lines.append('\t"strings"')
    lines.append(')')
    lines.append('')

    # Helper functions
    lines.append('// =============================================================================')
    lines.append('// HELPER FUNCTIONS')
    lines.append('// =============================================================================')
    lines.append('')
    lines.append('// boolVal safely dereferences a *bool, returning false if nil')
    lines.append('func boolVal(b *bool) bool {')
    lines.append('\tif b == nil {')
    lines.append('\t\treturn false')
    lines.append('\t}')
    lines.append('\treturn *b')
    lines.append('}')
    lines.append('')
    lines.append('// stringVal safely dereferences a *string, returning "" if nil')
    lines.append('func stringVal(s *string) string {')
    lines.append('\tif s == nil {')
    lines.append('\t\treturn ""')
    lines.append('\t}')
    lines.append('\treturn *s')
    lines.append('}')
    lines.append('')
    lines.append('// nilIfEmpty returns nil for empty strings, otherwise a pointer to the string')
    lines.append('func nilIfEmpty(s string) *string {')
    lines.append('\tif s == "" {')
    lines.append('\t\treturn nil')
    lines.append('\t}')
    lines.append('\treturn &s')
    lines.append('}')
    lines.append('')
    lines.append('// intToString safely converts a *int to string, returning "" if nil')
    lines.append('func intToString(i *int) string {')
    lines.append('\tif i == nil {')
    lines.append('\t\treturn ""')
    lines.append('\t}')
    lines.append('\treturn strconv.Itoa(*i)')
    lines.append('}')
    lines.append('')
    lines.append('// boolToString converts a bool to "true" or "false"')
    lines.append('func boolToString(b bool) string {')
    lines.append('\tif b {')
    lines.append('\t\treturn "true"')
    lines.append('\t}')
    lines.append('\treturn "false"')
    lines.append('}')
    lines.append('')
    lines.append('// FlexibleString is a type that can unmarshal from both string and number JSON values')
    lines.append('// This is needed for aggregation fields that return 0 (int) when empty or string values')
    lines.append('type FlexibleString string')
    lines.append('')
    lines.append('func (f *FlexibleString) UnmarshalJSON(data []byte) error {')
    lines.append('\t// First try as string')
    lines.append('\tvar s string')
    lines.append('\tif err := json.Unmarshal(data, &s); err == nil {')
    lines.append('\t\t*f = FlexibleString(s)')
    lines.append('\t\treturn nil')
    lines.append('\t}')
    lines.append('\t// Try as number')
    lines.append('\tvar n float64')
    lines.append('\tif err := json.Unmarshal(data, &n); err == nil {')
    lines.append('\t\t// Convert number to string, but treat 0 as empty')
    lines.append('\t\tif n == 0 {')
    lines.append('\t\t\t*f = FlexibleString("0")')
    lines.append('\t\t} else {')
    lines.append('\t\t\t*f = FlexibleString(fmt.Sprintf("%v", n))')
    lines.append('\t\t}')
    lines.append('\t\treturn nil')
    lines.append('\t}')
    lines.append('\treturn fmt.Errorf("cannot unmarshal %s into FlexibleString", string(data))')
    lines.append('}')
    lines.append('')
    lines.append('// String returns the underlying string value')
    lines.append('func (f FlexibleString) String() string {')
    lines.append('\treturn string(f)')
    lines.append('}')
    lines.append('')

    # Get all table names from the rulebook (domain-agnostic discovery)
    table_names = get_table_names(rulebook)

    # Generate SDK for each table
    for table_name in table_names:
        table_data = rulebook[table_name]

        if not isinstance(table_data, dict) or 'schema' not in table_data:
            continue

        lines.extend(generate_table_sdk(table_name, table_data))

    # Find ALL tables with computed fields (calculated, lookup, or aggregation)
    tables_with_calc = []
    for table_name in table_names:
        table_data = rulebook.get(table_name, {})
        if isinstance(table_data, dict) and 'schema' in table_data:
            schema = table_data.get('schema', [])
            # Include tables with any computed fields: calculated, lookup, or aggregation
            has_computed = (get_calculated_fields(schema) or
                           get_lookup_fields(schema) or
                           get_aggregation_fields(schema))
            if has_computed:
                tables_with_calc.append(table_name)

    # Generate File I/O functions for ALL tables with computed fields
    if tables_with_calc:
        lines.append('// =============================================================================')
        lines.append('// FILE I/O FUNCTIONS (for all tables with calculated fields)')
        lines.append('// =============================================================================')
        lines.append('')

        for table_name in tables_with_calc:
            struct_name = table_name_to_struct_name(table_name)
            lines.append(f'// Load{struct_name}Records loads {table_name} records from a JSON file')
            lines.append(f'func Load{struct_name}Records(path string) ([]{struct_name}, error) {{')
            lines.append('\tdata, err := os.ReadFile(path)')
            lines.append('\tif err != nil {')
            lines.append('\t\treturn nil, fmt.Errorf("failed to read file: %w", err)')
            lines.append('\t}')
            lines.append('')
            lines.append(f'\tvar records []{struct_name}')
            lines.append('\tif err := json.Unmarshal(data, &records); err != nil {')
            lines.append('\t\treturn nil, fmt.Errorf("failed to parse file: %w", err)')
            lines.append('\t}')
            lines.append('')
            lines.append('\treturn records, nil')
            lines.append('}')
            lines.append('')
            lines.append(f'// Save{struct_name}Records saves computed {table_name} records to a JSON file')
            lines.append(f'func Save{struct_name}Records(path string, records []{struct_name}) error {{')
            lines.append('\tdata, err := json.MarshalIndent(records, "", "  ")')
            lines.append('\tif err != nil {')
            lines.append('\t\treturn fmt.Errorf("failed to marshal records: %w", err)')
            lines.append('\t}')
            lines.append('')
            lines.append('\tif err := os.WriteFile(path, data, 0644); err != nil {')
            lines.append('\t\treturn fmt.Errorf("failed to write records: %w", err)')
            lines.append('\t}')
            lines.append('')
            lines.append('\treturn nil')
            lines.append('}')
            lines.append('')

    return '\n'.join(lines)


def get_table_aggregations(rulebook: Dict, table_name: str) -> List[Dict]:
    """Get aggregation fields for a table with parsed formula info.

    Supports both COUNTIFS (counting) and SUMIFS (concatenating) formulas.
    """
    table_data = rulebook.get(table_name, {})
    if not isinstance(table_data, dict) or 'schema' not in table_data:
        return []

    agg_fields = get_aggregation_fields(table_data.get('schema', []))
    result = []
    for field in agg_fields:
        formula = field.get('formula', '')

        # Try COUNTIFS first
        related_table, lookup_field, match_field = parse_countifs_formula(formula)
        if related_table:
            result.append({
                'field': field,
                'type': 'countifs',
                'related_table': related_table,
                'lookup_field': lookup_field,
                'match_field': match_field
            })
            continue

        # Try SUMIFS
        related_table, sum_field, criteria_field, match_field = parse_sumifs_formula(formula)
        if related_table:
            # Check if this is a "distinct" aggregation
            is_distinct = 'distinct' in field.get('name', '').lower()
            result.append({
                'field': field,
                'type': 'sumifs',
                'related_table': related_table,
                'sum_field': sum_field,
                'criteria_field': criteria_field,
                'match_field': match_field,
                'is_distinct': is_distinct
            })
    return result


def get_table_lookups(rulebook: Dict, table_name: str) -> List[Dict]:
    """Get lookup fields for a table with parsed INDEX/MATCH formula info.

    Returns list of dicts with:
        - field: The field definition
        - lookup_table: Table to look up from
        - return_field: Field to return from lookup table
        - key_field: Field in current table to match
        - pk_field: Primary key field in lookup table
    """
    table_data = rulebook.get(table_name, {})
    if not isinstance(table_data, dict) or 'schema' not in table_data:
        return []

    lookup_fields_list = get_lookup_fields(table_data.get('schema', []))
    result = []
    for field in lookup_fields_list:
        formula = field.get('formula', '')
        lookup_table, return_field, key_field, pk_field = parse_index_match_formula(formula)
        if lookup_table:
            result.append({
                'field': field,
                'lookup_table': lookup_table,
                'return_field': return_field,
                'key_field': key_field,
                'pk_field': pk_field
            })
    return result


def generate_main_go(tables_with_calc: list, rulebook: Dict) -> str:
    """Generate main.go content that processes ALL tables with computed fields.

    IMPORTANT: This file is ALWAYS regenerated when inject-into-golang.py runs.
    This ensures main.go stays in sync with erb_sdk.go when the rulebook changes.

    Args:
        tables_with_calc: List of table names that have computed fields
        rulebook: The loaded rulebook for aggregation/lookup info
    """
    # Collect all related tables needed for aggregations and lookups
    all_related_tables = set()
    table_aggregations = {}
    table_lookups = {}
    for table_name in tables_with_calc:
        aggs = get_table_aggregations(rulebook, table_name)
        if aggs:
            table_aggregations[table_name] = aggs
            for agg in aggs:
                all_related_tables.add(agg['related_table'])
        lookups = get_table_lookups(rulebook, table_name)
        if lookups:
            table_lookups[table_name] = lookups
            for lookup in lookups:
                all_related_tables.add(lookup['lookup_table'])

    lines = []
    lines.append('// ERB SDK - Go Test Runner (GENERATED - DO NOT EDIT)')
    lines.append('// =======================================================')
    lines.append('// This file is REGENERATED every time inject-into-golang.py runs.')
    lines.append('// It must stay in sync with erb_sdk.go and the rulebook.')
    lines.append('//')
    lines.append(f'// Tables with computed fields: {", ".join(tables_with_calc)}')
    if table_aggregations:
        lines.append(f'// Tables with aggregations: {", ".join(table_aggregations.keys())}')
    if table_lookups:
        lines.append(f'// Tables with lookups: {", ".join(table_lookups.keys())}')
    lines.append('//')
    lines.append('// IMPORTANT: This runner processes ALL tables, not just a "primary" one.')
    lines.append('// If ANY table fails to process, the entire run fails with exit code 1.')
    lines.append('')
    lines.append('package main')
    lines.append('')

    # Check if we need strings package for SUMIFS
    has_sumifs = any(
        agg.get('type') == 'sumifs'
        for aggs in table_aggregations.values()
        for agg in aggs
    )

    # Check if we need sort package (for SUMIFS or WorkflowSteps sorting)
    needs_sort = has_sumifs or 'WorkflowSteps' in all_related_tables

    lines.append('import (')
    lines.append('\t"fmt"')
    lines.append('\t"os"')
    lines.append('\t"path/filepath"')
    if needs_sort:
        lines.append('\t"sort"')
    if has_sumifs:
        lines.append('\t"strings"')
    lines.append(')')
    lines.append('')
    lines.append('func main() {')
    lines.append('\tscriptDir, err := os.Getwd()')
    lines.append('\tif err != nil {')
    lines.append('\t\tfmt.Fprintf(os.Stderr, "FATAL: Failed to get working directory: %v\\n", err)')
    lines.append('\t\tos.Exit(1)')
    lines.append('\t}')
    lines.append('')
    lines.append('\t// Shared blank-tests directory at project root')
    lines.append('\tblankTestsDir := filepath.Join(scriptDir, "..", "..", "testing", "blank-tests")')
    lines.append('\ttestAnswersDir := filepath.Join(scriptDir, "test-answers")')
    lines.append('')
    lines.append('\t// Ensure output directory exists')
    lines.append('\tif err := os.MkdirAll(testAnswersDir, 0755); err != nil {')
    lines.append('\t\tfmt.Fprintf(os.Stderr, "FATAL: Failed to create test-answers directory: %v\\n", err)')
    lines.append('\t\tos.Exit(1)')
    lines.append('\t}')
    lines.append('')
    lines.append(f'\tfmt.Println("Golang substrate: Processing {len(tables_with_calc)} tables with calculated fields...")')
    lines.append(f'\tfmt.Println("  Expected tables: {", ".join(tables_with_calc)}")')
    lines.append('\tfmt.Println("")')
    lines.append('')
    lines.append('\t// Track success/failure for ALL tables')
    lines.append('\tvar errors []string')
    lines.append('\tvar totalRecords int')
    lines.append('')

    # Check which tables need answer-keys (for SUMIFS with computed fields)
    tables_needing_answer_keys = set()
    for table_name, aggs in table_aggregations.items():
        for agg in aggs:
            if agg.get('type') == 'sumifs':
                tables_needing_answer_keys.add(agg['related_table'])

    # If there are aggregations, load related tables first
    if all_related_tables:
        lines.append('\t// ─────────────────────────────────────────────────────────────────')
        lines.append('\t// Load related tables for aggregation calculations')
        lines.append('\t// ─────────────────────────────────────────────────────────────────')
        lines.append('\t// Note: SUMIFS loads from answer-keys (has computed fields)')
        lines.append('\t//       COUNTIFS loads from blank-tests')
        # Only declare answerKeysDir if it will be used
        if tables_needing_answer_keys:
            lines.append('\tanswerKeysDir := filepath.Join(scriptDir, "..", "..", "testing", "answer-keys")')
        lines.append('')

        for related_table in sorted(all_related_tables):
            related_snake = to_snake_case(related_table)
            related_struct = table_name_to_struct_name(related_table)
            # Use answer-keys for SUMIFS (computed fields), blank-tests for COUNTIFS
            if related_table in tables_needing_answer_keys:
                data_dir = 'answerKeysDir'
            else:
                data_dir = 'blankTestsDir'
            lines.append(f'\t{related_snake}Data, err := Load{related_struct}Records(filepath.Join({data_dir}, "{related_snake}.json"))')
            lines.append('\tif err != nil {')
            lines.append(f'\t\tfmt.Fprintf(os.Stderr, "Warning: Could not load {related_table} for aggregations: %v\\n", err)')
            lines.append(f'\t\t{related_snake}Data = nil')
            lines.append('\t}')
            # Sort WorkflowSteps by SequencePosition for proper ordering
            if related_table == 'WorkflowSteps':
                lines.append(f'\t// Sort workflow_steps by sequence_position for proper ordering')
                lines.append(f'\tif {related_snake}Data != nil {{')
                lines.append(f'\t\tsort.Slice({related_snake}Data, func(i, j int) bool {{')
                lines.append(f'\t\t\tvi, vj := 0, 0')
                lines.append(f'\t\t\tif {related_snake}Data[i].SequencePosition != nil {{')
                lines.append(f'\t\t\t\tvi = *{related_snake}Data[i].SequencePosition')
                lines.append(f'\t\t\t}}')
                lines.append(f'\t\t\tif {related_snake}Data[j].SequencePosition != nil {{')
                lines.append(f'\t\t\t\tvj = *{related_snake}Data[j].SequencePosition')
                lines.append(f'\t\t\t}}')
                lines.append(f'\t\t\treturn vi < vj')
                lines.append(f'\t\t}})')
                lines.append(f'\t}}')
        lines.append('')

    # Generate processing code for each table
    for table_name in tables_with_calc:
        struct_name = table_name_to_struct_name(table_name)
        table_snake = to_snake_case(table_name)
        aggs = table_aggregations.get(table_name, [])

        lines.append(f'\t// ─────────────────────────────────────────────────────────────────')
        lines.append(f'\t// Process {table_name}')
        lines.append(f'\t// ─────────────────────────────────────────────────────────────────')
        lines.append(f'\tfmt.Println("Processing {table_name}...")')
        lines.append(f'\t{table_snake}Input := filepath.Join(blankTestsDir, "{table_snake}.json")')
        lines.append(f'\t{table_snake}Output := filepath.Join(testAnswersDir, "{table_snake}.json")')
        lines.append('')
        lines.append(f'\t{table_snake}Records, err := Load{struct_name}Records({table_snake}Input)')
        lines.append('\tif err != nil {')
        lines.append(f'\t\terrMsg := fmt.Sprintf("{table_name}: failed to load - %v", err)')
        lines.append('\t\tfmt.Fprintf(os.Stderr, "ERROR: %s\\n", errMsg)')
        lines.append('\t\terrors = append(errors, errMsg)')
        lines.append('\t} else {')

        # If this table has aggregations, compute them first
        if aggs:
            lines.append(f'\t\t// Compute aggregations for {table_name}')

            # Separate COUNTIFS and SUMIFS
            countifs_aggs = [a for a in aggs if a.get('type') == 'countifs']
            sumifs_aggs = [a for a in aggs if a.get('type') == 'sumifs']

            # Build COUNTIFS maps
            for agg in countifs_aggs:
                field_name = agg['field']['name']
                field_snake = to_snake_case(field_name)
                related_table = agg['related_table']
                related_snake = to_snake_case(related_table)
                lookup_field = agg['lookup_field']

                lines.append(f'\t\t{field_snake}CountMap := make(map[string]int)')
                lines.append(f'\t\tif {related_snake}Data != nil {{')
                lines.append(f'\t\t\tfor _, rel := range {related_snake}Data {{')
                lines.append(f'\t\t\t\tif rel.{lookup_field} != nil {{')
                lines.append(f'\t\t\t\t\t{field_snake}CountMap[*rel.{lookup_field}]++')
                lines.append('\t\t\t\t}')
                lines.append('\t\t\t}')
                lines.append('\t\t}')
                lines.append('')

            # Build SUMIFS lookup maps (for quick access to sum_field values by PK)
            # This approach uses relationship field ordering instead of iteration order
            for agg in sumifs_aggs:
                field_name = agg['field']['name']
                field_snake = to_snake_case(field_name)
                related_table = agg['related_table']
                related_snake = to_snake_case(related_table)
                sum_field = agg['sum_field']
                criteria_field = agg['criteria_field']
                is_distinct = agg.get('is_distinct', False)

                # Determine the PK field name (TableName -> TableNameId pattern)
                struct_name_related = table_name_to_struct_name(related_table)
                pk_field = struct_name_related + 'Id'

                # Build a lookup map from PK to sum_field value (include empty values for position correspondence)
                lines.append(f'\t\t{field_snake}LookupMap := make(map[string]string)')
                lines.append(f'\t\tif {related_snake}Data != nil {{')
                lines.append(f'\t\t\tfor _, rel := range {related_snake}Data {{')
                lines.append(f'\t\t\t\tvar val string')
                lines.append(f'\t\t\t\tif rel.{sum_field} != nil {{')
                lines.append(f'\t\t\t\t\tval = fmt.Sprintf("%s", *rel.{sum_field})')
                lines.append(f'\t\t\t\t}}')
                lines.append(f'\t\t\t\t// Include all entries (even empty) to maintain position correspondence')
                lines.append(f'\t\t\t\t{field_snake}LookupMap[rel.{pk_field}] = val')
                lines.append('\t\t\t}')
                lines.append('\t\t}')
                lines.append('')

            # Update records with aggregation values
            lines.append(f'\t\t// Update records with aggregation values')
            lines.append(f'\t\tfor i := range {table_snake}Records {{')

            # COUNTIFS: set int values
            for agg in countifs_aggs:
                field_name = agg['field']['name']
                field_snake = to_snake_case(field_name)
                match_field = agg['match_field']
                lines.append(f'\t\t\tif {table_snake}Records[i].{match_field} != "" {{')
                lines.append(f'\t\t\t\tcount := {field_snake}CountMap[{table_snake}Records[i].{match_field}]')
                lines.append(f'\t\t\t\t{table_snake}Records[i].{field_name} = &count')
                lines.append('\t\t\t}')

            # SUMIFS: set FlexibleString values using relationship field ordering
            for agg in sumifs_aggs:
                field_name = agg['field']['name']
                field_snake = to_snake_case(field_name)
                related_table = agg['related_table']
                is_distinct = agg.get('is_distinct', False)

                # Find the relationship field in the current table that relates to the related_table
                # This determines the ordering of the aggregated values
                table_data = rulebook.get(table_name, {})
                relationship_field = None
                for col in table_data.get('schema', []):
                    if col.get('type') == 'relationship' and col.get('RelatedTo') == related_table:
                        relationship_field = col.get('name')
                        break

                if relationship_field:
                    # Use relationship field ordering: parse PKs from relationship field, look up each value
                    lines.append(f'\t\t\tif {table_snake}Records[i].{relationship_field} != nil && *{table_snake}Records[i].{relationship_field} != "" {{')
                    lines.append(f'\t\t\t\t// Parse relationship field to get ordered PKs')
                    lines.append(f'\t\t\t\trelPKs := strings.Split(*{table_snake}Records[i].{relationship_field}, ", ")')
                    lines.append(f'\t\t\t\tvar values []string')
                    lines.append(f'\t\t\t\tfor _, pk := range relPKs {{')
                    lines.append(f'\t\t\t\t\tpk = strings.TrimSpace(pk)')
                    lines.append(f'\t\t\t\t\tif val, ok := {field_snake}LookupMap[pk]; ok {{')
                    if is_distinct:
                        # For distinct, skip empty values and check for duplicates
                        lines.append(f'\t\t\t\t\t\t// For distinct, skip empty values and check for duplicates')
                        lines.append(f'\t\t\t\t\t\tif val != "" {{')
                        lines.append(f'\t\t\t\t\t\t\tfound := false')
                        lines.append(f'\t\t\t\t\t\t\tfor _, v := range values {{')
                        lines.append(f'\t\t\t\t\t\t\t\tif v == val {{')
                        lines.append(f'\t\t\t\t\t\t\t\t\tfound = true')
                        lines.append(f'\t\t\t\t\t\t\t\t\tbreak')
                        lines.append(f'\t\t\t\t\t\t\t\t}}')
                        lines.append(f'\t\t\t\t\t\t\t}}')
                        lines.append(f'\t\t\t\t\t\t\tif !found {{')
                        lines.append(f'\t\t\t\t\t\t\t\tvalues = append(values, val)')
                        lines.append(f'\t\t\t\t\t\t\t}}')
                        lines.append(f'\t\t\t\t\t\t}}')
                    else:
                        # For non-distinct, include empty values for position correspondence
                        lines.append(f'\t\t\t\t\t\tvalues = append(values, val)')
                    lines.append(f'\t\t\t\t\t}}')
                    lines.append(f'\t\t\t\t}}')
                    lines.append(f'\t\t\t\tif len(values) > 0 {{')
                    lines.append(f'\t\t\t\t\tjoined := FlexibleString(strings.Join(values, ", "))')
                    lines.append(f'\t\t\t\t\t{table_snake}Records[i].{field_name} = &joined')
                    lines.append(f'\t\t\t\t}} else {{')
                    if is_distinct:
                        lines.append(f'\t\t\t\t\tempty := FlexibleString("")')
                        lines.append(f'\t\t\t\t\t{table_snake}Records[i].{field_name} = &empty')
                    else:
                        lines.append(f'\t\t\t\t\tzero := FlexibleString("0")')
                        lines.append(f'\t\t\t\t\t{table_snake}Records[i].{field_name} = &zero')
                    lines.append(f'\t\t\t\t}}')
                    lines.append(f'\t\t\t}} else {{')
                    if is_distinct:
                        lines.append(f'\t\t\t\tempty := FlexibleString("")')
                        lines.append(f'\t\t\t\t{table_snake}Records[i].{field_name} = &empty')
                    else:
                        lines.append(f'\t\t\t\tzero := FlexibleString("0")')
                        lines.append(f'\t\t\t\t{table_snake}Records[i].{field_name} = &zero')
                    lines.append(f'\t\t\t}}')

            lines.append('\t\t}')
            lines.append('')

        # If this table has lookups, compute them
        lookups = table_lookups.get(table_name, [])
        if lookups:
            lines.append(f'\t\t// Compute lookups for {table_name}')
            for lookup in lookups:
                field_name = lookup['field']['name']
                field_snake = to_snake_case(field_name)
                lookup_table = lookup['lookup_table']
                lookup_table_snake = to_snake_case(lookup_table)
                return_field = lookup['return_field']
                key_field = lookup['key_field']
                pk_field = lookup['pk_field']

                # Build lookup map
                lines.append(f'\t\t{field_snake}LookupMap := make(map[string]string)')
                lines.append(f'\t\tif {lookup_table_snake}Data != nil {{')
                lines.append(f'\t\t\tfor _, rel := range {lookup_table_snake}Data {{')
                lines.append(f'\t\t\t\tif rel.{pk_field} != "" {{')
                lines.append(f'\t\t\t\t\tvar val string')
                lines.append(f'\t\t\t\t\tif rel.{return_field} != nil {{')
                lines.append(f'\t\t\t\t\t\tval = *rel.{return_field}')
                lines.append(f'\t\t\t\t\t}}')
                lines.append(f'\t\t\t\t\t{field_snake}LookupMap[rel.{pk_field}] = val')
                lines.append('\t\t\t\t}')
                lines.append('\t\t\t}')
                lines.append('\t\t}')
                lines.append('')

            # Apply lookups to records
            lines.append(f'\t\t// Apply lookup values to records')
            lines.append(f'\t\tfor i := range {table_snake}Records {{')
            for lookup in lookups:
                field_name = lookup['field']['name']
                field_snake = to_snake_case(field_name)
                key_field = lookup['key_field']

                lines.append(f'\t\t\tif {table_snake}Records[i].{key_field} != nil && *{table_snake}Records[i].{key_field} != "" {{')
                lines.append(f'\t\t\t\tif val, ok := {field_snake}LookupMap[*{table_snake}Records[i].{key_field}]; ok {{')
                lines.append(f'\t\t\t\t\t{table_snake}Records[i].{field_name} = &val')
                lines.append('\t\t\t\t}')
                lines.append('\t\t\t}')
            lines.append('\t\t}')
            lines.append('')

        # Check if this table has calculated fields (ComputeAll is only generated for those)
        table_data_for_check = rulebook.get(table_name, {})
        has_calc_fields = bool(get_calculated_fields(table_data_for_check.get('schema', [])))

        lines.append(f'\t\tvar computed{struct_name} []{struct_name}')
        lines.append(f'\t\tfor _, r := range {table_snake}Records {{')
        if has_calc_fields:
            lines.append(f'\t\t\tcomputed{struct_name} = append(computed{struct_name}, *r.ComputeAll())')
        else:
            # No calculated fields - just copy the record (lookup/aggregation already populated)
            lines.append(f'\t\t\tcomputed{struct_name} = append(computed{struct_name}, r)')
        lines.append('\t\t}')
        lines.append('')
        lines.append(f'\t\tif err := Save{struct_name}Records({table_snake}Output, computed{struct_name}); err != nil {{')
        lines.append(f'\t\t\terrMsg := fmt.Sprintf("{table_name}: failed to save - %v", err)')
        lines.append('\t\t\tfmt.Fprintf(os.Stderr, "ERROR: %s\\n", errMsg)')
        lines.append('\t\t\terrors = append(errors, errMsg)')
        lines.append('\t\t} else {')
        lines.append(f'\t\t\tfmt.Printf("  ✓ {table_snake}: %d records processed\\n", len(computed{struct_name}))')
        lines.append(f'\t\t\ttotalRecords += len(computed{struct_name})')
        lines.append('\t\t}')
        lines.append('\t}')
        lines.append('\tfmt.Println("")')
        lines.append('')

    # Final validation
    lines.append('\t// ─────────────────────────────────────────────────────────────────')
    lines.append('\t// Final validation - FAIL LOUDLY if any errors occurred')
    lines.append('\t// ─────────────────────────────────────────────────────────────────')
    lines.append('\tif len(errors) > 0 {')
    lines.append('\t\tfmt.Fprintf(os.Stderr, "\\n")')
    lines.append('\t\tfmt.Fprintf(os.Stderr, "════════════════════════════════════════════════════════════════\\n")')
    lines.append('\t\tfmt.Fprintf(os.Stderr, "FATAL: %d table(s) FAILED to process\\n", len(errors))')
    lines.append('\t\tfmt.Fprintf(os.Stderr, "════════════════════════════════════════════════════════════════\\n")')
    lines.append('\t\tfor _, e := range errors {')
    lines.append('\t\t\tfmt.Fprintf(os.Stderr, "  • %s\\n", e)')
    lines.append('\t\t}')
    lines.append('\t\tfmt.Fprintf(os.Stderr, "\\n")')
    lines.append('\t\tos.Exit(1)')
    lines.append('\t}')
    lines.append('')
    lines.append('\tfmt.Println("════════════════════════════════════════════════════════════════")')
    lines.append(f'\tfmt.Printf("Golang substrate: ALL %d tables processed successfully (%d total records)\\n", {len(tables_with_calc)}, totalRecords)')
    lines.append('\tfmt.Println("════════════════════════════════════════════════════════════════")')
    lines.append('}')

    return '\n'.join(lines)


def main():
    # Files generated by THIS script that should be cleaned
    # main.go is now ALWAYS regenerated to stay in sync with erb_sdk.go
    # Note: erb_test, test-answers/, test-results.md are build/test outputs
    GENERATED_FILES = [
        'erb_sdk.go',
        'main.go',
    ]

    # Handle --clean argument
    if handle_clean_arg(GENERATED_FILES, "Golang substrate: Removes generated erb_sdk.go"):
        return

    candidate_name = get_candidate_name_from_cwd()
    script_dir = Path(__file__).resolve().parent

    print("=" * 70)
    print("Golang Execution Substrate - Generic Rulebook Transpiler")
    print("=" * 70)
    print()

    # Load the rulebook
    print("Loading rulebook...")
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Get all table names (domain-agnostic discovery)
    table_names = get_table_names(rulebook)
    print(f"Found {len(table_names)} tables: {', '.join(table_names)}")
    print()

    # Report on computed fields per table and collect ALL tables with computed fields
    total_computed_fields = 0
    tables_with_calc = []
    for table_name in table_names:
        table_data = rulebook.get(table_name, {})
        if isinstance(table_data, dict) and 'schema' in table_data:
            schema = table_data.get('schema', [])
            calc_fields = get_calculated_fields(schema)
            lookup_fields = get_lookup_fields(schema)
            agg_fields = get_aggregation_fields(schema)
            all_computed = calc_fields + lookup_fields + agg_fields
            if all_computed:
                tables_with_calc.append(table_name)
                print(f"  {table_name}: {len(all_computed)} computed fields")
                for field in all_computed:
                    field_type = field.get('type', 'unknown')
                    print(f"    - {field['name']} ({field_type})")
                total_computed_fields += len(all_computed)

    print()
    print(f"Total computed fields to compile: {total_computed_fields}")
    print(f"Tables with computed fields ({len(tables_with_calc)}): {', '.join(tables_with_calc)}")
    print()
    print("-" * 70)
    print()

    # Generate erb_sdk.go
    print("Generating erb_sdk.go...")
    erb_sdk_content = generate_erb_sdk(rulebook)

    erb_sdk_path = script_dir / "erb_sdk.go"
    erb_sdk_path.write_text(erb_sdk_content, encoding='utf-8')
    print(f"Wrote: {erb_sdk_path} ({len(erb_sdk_content)} bytes)")

    # Generate main.go - ALWAYS regenerated to stay in sync with erb_sdk.go
    # IMPORTANT: Now processes ALL tables with calculated fields, not just one!
    main_go_path = script_dir / "main.go"
    if tables_with_calc:
        print(f"Generating main.go (processes ALL {len(tables_with_calc)} tables)...")
        main_go_content = generate_main_go(tables_with_calc, rulebook)
        main_go_path.write_text(main_go_content, encoding='utf-8')
        print(f"Wrote: {main_go_path} ({len(main_go_content)} bytes)")
    else:
        print("ERROR: No tables with calculated fields found - cannot generate main.go")
        sys.exit(1)

    print()
    print("=" * 70)
    print("Generation complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
