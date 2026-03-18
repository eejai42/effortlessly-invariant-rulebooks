#!/usr/bin/env python3
"""
Take Test - Binary Execution Substrate

This script runs the test by:
1. Loading test data (multi-entity or legacy)
2. Packing each record into a TestAnswer struct (bytes)
3. Calling the GENERATED assembly evaluators via ctypes
4. Unpacking results back to Python
5. Saving test-answers

Supports two modes:
1. Multi-entity (--multi-entity): Processes all files in blank-tests/ -> test-answers/
2. Legacy: Processes single test-answers.json file

The ABI (ARM64 Apple Silicon):
    - Input: TestAnswer struct pointer (x0 -> saved to x19)
    - Bool functions: return 0/1 in w0
    - String functions: return (ptr, len) in (x0, x1)
"""

import argparse
import ctypes
import glob as glob_module
import json
import os
import platform
import re
import struct
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum, auto

# Add project root to path for shared imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from orchestration.shared import load_rulebook, discover_entities, get_entity_schema, to_snake_case, get_calculated_fields, compute_aggregations, compute_lookups


# =============================================================================
# DATA TYPES (must match inject-into-binary.py)
# =============================================================================

class DataType(Enum):
    BOOL = auto()
    INT = auto()
    STRING = auto()
    NULL = auto()


@dataclass
class FieldInfo:
    name: str
    datatype: DataType
    offset: int
    size: int
    json_name: str  # Original JSON field name for lookups


# =============================================================================
# FIELD NAME NORMALIZATION (must match inject-into-binary.py)
# =============================================================================

def normalize_field_name(name: str) -> str:
    """Normalize field name to snake_case format (must match compiler)."""
    return to_snake_case(name)


def json_key_to_snake(name: str) -> str:
    """Convert JSON key (snake_case) to normalized internal name."""
    return name.lower().replace(' ', '_')


# =============================================================================
# STRUCT LAYOUT COMPUTATION
# =============================================================================

def build_schema(columns: List[dict]) -> tuple:
    """
    Build schema with field offsets from column definitions.
    Must match the layout computed by inject-into-binary.py.

    Returns: (schema dict, total struct size)
    """
    schema = {}
    offset = 0

    for col in columns:
        name = col.get('name', '')
        field_name = normalize_field_name(name)
        datatype_str = col.get('datatype', 'string').lower()

        if datatype_str == 'boolean':
            dt = DataType.BOOL
            size = 1
        elif datatype_str == 'integer':
            dt = DataType.INT
            size = 8
        else:  # string
            dt = DataType.STRING
            size = 16  # ptr + len

        # Align offset (must match compiler)
        if dt == DataType.INT or dt == DataType.STRING:
            offset = (offset + 7) & ~7  # 8-byte align

        schema[field_name] = FieldInfo(
            name=field_name,
            datatype=dt,
            offset=offset,
            size=size,
            json_name=json_key_to_snake(name)
        )
        offset += size

    # Final size with alignment
    total_size = (offset + 7) & ~7
    return schema, total_size


# =============================================================================
# STRUCT PACKING
# =============================================================================

class StringTable:
    """Manages string interning for struct packing."""

    def __init__(self):
        self.strings: List[bytes] = []
        self.buffers: List[ctypes.c_char_p] = []

    def intern(self, s: str) -> tuple:
        """Intern a string, return (ptr, len)."""
        encoded = s.encode('utf-8')
        # Create a ctypes buffer that won't be garbage collected
        buf = ctypes.create_string_buffer(encoded)
        self.buffers.append(buf)
        ptr = ctypes.addressof(buf)
        return (ptr, len(encoded))


def pack_test_answer(record: dict, schema: Dict[str, FieldInfo],
                     total_size: int, string_table: StringTable) -> bytes:
    """
    Pack a JSON record into TestAnswer struct bytes.
    """
    # Create zeroed buffer
    buf = bytearray(total_size)

    for field_name, info in schema.items():
        # Map JSON key variations
        json_key = info.json_name

        # Try multiple key formats
        value = None
        for key in [json_key, field_name, info.json_name.replace('_', '')]:
            if key in record:
                value = record[key]
                break

        if value is None:
            # Field not in record, leave as zeros (null)
            continue

        if info.datatype == DataType.BOOL:
            bool_val = 1 if value else 0
            struct.pack_into('B', buf, info.offset, bool_val)

        elif info.datatype == DataType.INT:
            int_val = int(value) if value is not None else 0
            struct.pack_into('<q', buf, info.offset, int_val)

        elif info.datatype == DataType.STRING:
            str_val = str(value) if value is not None else ""
            ptr, length = string_table.intern(str_val)
            struct.pack_into('<Q', buf, info.offset, ptr)      # ptr
            struct.pack_into('<Q', buf, info.offset + 8, length)  # len

    return bytes(buf)


# =============================================================================
# LIBRARY LOADING AND FUNCTION CALLING
# =============================================================================

def load_library(lib_path: Path) -> ctypes.CDLL:
    """Load the generated assembly library."""
    if not lib_path.exists():
        raise FileNotFoundError(f"Library not found: {lib_path}")
    return ctypes.CDLL(str(lib_path))


def setup_function(lib: ctypes.CDLL, func_name: str, returns_string: bool):
    """Configure a function's signature."""
    try:
        func = getattr(lib, func_name)
        func.argtypes = [ctypes.c_void_p]  # TestAnswer* pointer

        if returns_string:
            # String functions return (ptr, len) in (x0, x1)
            # We can use a structure or just get x0 as pointer
            func.restype = ctypes.c_uint64  # Just get x0 for now
        else:
            # Bool functions return 0/1 in w0
            func.restype = ctypes.c_int

        return func
    except AttributeError:
        return None


class StringResult(ctypes.Structure):
    """Structure to capture both ptr (x0) and len (x1) return values."""
    _fields_ = [("ptr", ctypes.c_uint64), ("len", ctypes.c_uint64)]


def call_string_function(lib: ctypes.CDLL, func_name: str, struct_ptr: int) -> str:
    """
    Call a string-returning function.

    The ARM64 assembly returns ptr in x0, len in x1.
    We use a structure return type to capture both values.
    """
    func = getattr(lib, func_name)
    func.argtypes = [ctypes.c_void_p]
    # Use StringResult structure to capture both x0 and x1
    func.restype = StringResult

    # Call the function
    result = func(struct_ptr)

    if result.ptr == 0 or result.len == 0:
        return ""

    # Read exactly 'len' bytes from the pointer
    try:
        raw = ctypes.string_at(result.ptr, result.len)
        return raw.decode('utf-8', errors='replace')
    except Exception:
        return ""


def call_bool_function(lib: ctypes.CDLL, func_name: str, struct_ptr: int) -> bool:
    """Call a bool-returning function."""
    func = getattr(lib, func_name)
    func.argtypes = [ctypes.c_void_p]
    func.restype = ctypes.c_int

    result = func(struct_ptr)
    return bool(result)


def call_int_function(lib: ctypes.CDLL, func_name: str, struct_ptr: int) -> int:
    """Call an int-returning function."""
    func = getattr(lib, func_name)
    func.argtypes = [ctypes.c_void_p]
    func.restype = ctypes.c_int64

    result = func(struct_ptr)
    return int(result)


# =============================================================================
# CALCULATED FIELD DISCOVERY
# =============================================================================

def discover_calculated_fields(rulebook: dict, entity_name: str) -> dict:
    """
    Discover calculated fields for an entity from the rulebook.

    Returns a dict mapping field names to (function_name, return_type) tuples.
    Function names follow the pattern: eval_{entity}_{field}
    """
    schema = get_entity_schema(rulebook, entity_name)
    calc_fields = get_calculated_fields(schema)

    entity_snake = to_snake_case(entity_name)
    result = {}

    for field in calc_fields:
        field_name = to_snake_case(field['name'])
        datatype = field.get('datatype', 'string').lower()

        # Map datatype to return type
        if datatype == 'boolean':
            ret_type = 'bool'
        elif datatype == 'integer':
            ret_type = 'int'
        else:
            ret_type = 'string'

        # Function name follows pattern from inject-into-binary.py
        func_name = f"eval_{entity_snake}_{field_name}"
        result[field_name] = (func_name, ret_type)

    return result


# =============================================================================
# CORE PROCESSING FUNCTION
# =============================================================================

def process_records(data: List[dict], lib: ctypes.CDLL, schema: Dict[str, FieldInfo],
                    struct_size: int, available_funcs: dict) -> List[dict]:
    """Process a list of records and compute calculated fields.

    Uses multiple passes to handle dependencies between computed fields.
    Each pass re-packs the struct with latest computed values.
    """
    # Keep all string tables alive for the duration
    all_string_tables = []

    for i, record in enumerate(data):
        try:
            # Multiple passes to resolve dependencies between computed fields
            max_passes = 5
            for pass_num in range(max_passes):
                # Create string table for this pass (keep reference alive)
                string_table = StringTable()
                all_string_tables.append(string_table)

                # Pack record to struct bytes (includes previously computed values)
                struct_bytes = pack_test_answer(record, schema, struct_size, string_table)

                # Create ctypes buffer from bytes
                struct_buf = ctypes.create_string_buffer(struct_bytes, struct_size)
                struct_ptr = ctypes.addressof(struct_buf)

                # Track if any values changed this pass
                changes = False

                # Call each available function
                for field_name, (func_name, ret_type) in available_funcs.items():
                    try:
                        if ret_type == 'bool':
                            result = call_bool_function(lib, func_name, struct_ptr)
                        elif ret_type == 'int':
                            result = call_int_function(lib, func_name, struct_ptr)
                        else:  # string
                            result = call_string_function(lib, func_name, struct_ptr)

                        # Check if value changed
                        if record.get(field_name) != result:
                            changes = True
                            record[field_name] = result
                    except Exception as e:
                        print(f"  Warning: Error calling {func_name} for record {i}: {e}")
                        import traceback
                        traceback.print_exc()

                # If no changes, we've reached a fixed point
                if not changes:
                    break

        except Exception as e:
            print(f"ERROR processing record {i}: {e}")
            import traceback
            traceback.print_exc()
            continue

    return data


def load_binary_library(script_dir: Path) -> tuple:
    """Load the binary library and return (lib, lib_path)."""
    system = platform.system()
    if system == "Darwin":
        lib_name = "erb_calc.dylib"
    elif system == "Linux":
        lib_name = "erb_calc.so"
    else:
        print(f"ERROR: Unsupported platform: {system}")
        sys.exit(1)

    lib_path = script_dir / lib_name

    if not lib_path.exists():
        print(f"ERROR: Library not found at {lib_path}")
        print("Run: python inject-into-binary.py first")
        sys.exit(1)

    lib = load_library(lib_path)
    return lib, lib_path


# =============================================================================
# MULTI-ENTITY MODE
# =============================================================================

def run_multi_entity(script_dir: Path):
    """Process all entity files from shared testing/blank-tests/ directory."""
    # Use shared blank-tests directory at project root
    project_root = script_dir.parent.parent
    blank_tests_dir = project_root / "testing" / "blank-tests"
    test_answers_dir = script_dir / "test-answers"

    if not blank_tests_dir.is_dir():
        print(f"Error: {blank_tests_dir} not found")
        sys.exit(1)

    # Ensure output directory exists
    test_answers_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("Binary Execution Substrate - Multi-Entity Test Execution")
    print("=" * 70)
    print()

    # Load library
    lib, lib_path = load_binary_library(script_dir)
    print(f"Loaded library: {lib_path}")

    # Load rulebook to get schemas
    print("Loading rulebook...")
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Discover all entities
    entities = discover_entities(rulebook)
    print(f"Discovered {len(entities)} entities: {', '.join(entities)}")

    # Process each entity file (skip metadata files starting with _)
    total_records = 0
    entity_count = 0

    for input_path in sorted(glob_module.glob(str(blank_tests_dir / "*.json"))):
        filename = os.path.basename(input_path)

        # Skip metadata files
        if filename.startswith('_'):
            continue

        entity = filename.replace('.json', '')
        output_path = test_answers_dir / filename

        # Find matching rulebook entity (case-insensitive)
        rulebook_entity = None
        for e in entities:
            if to_snake_case(e) == entity:
                rulebook_entity = e
                break

        if not rulebook_entity:
            print(f"  -> {entity}: No matching entity in rulebook, copying as-is")
            with open(input_path, 'r') as f:
                data = json.load(f)
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            continue

        # Build schema for this entity
        columns = get_entity_schema(rulebook, rulebook_entity)
        schema, struct_size = build_schema(columns)
        print(f"  Schema for {entity}: {len(schema)} fields, {struct_size} bytes")

        # Discover calculated fields for this entity
        calc_fields = discover_calculated_fields(rulebook, rulebook_entity)

        # Get available functions for this entity
        available_funcs = {}
        for field_name, (func_name, ret_type) in calc_fields.items():
            try:
                func = getattr(lib, func_name)
                available_funcs[field_name] = (func_name, ret_type)
                print(f"    Found: {func_name} -> {ret_type}")
            except AttributeError:
                print(f"    Missing: {func_name}")

        # Load input data
        with open(input_path, 'r') as f:
            data = json.load(f)

        if not data:
            # Copy empty arrays as-is
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  -> {entity}: 0 records (empty)")
            continue

        # Compute lookup fields first (INDEX/MATCH)
        data = compute_lookups(data, rulebook_entity, rulebook, project_root)
        # Then compute aggregation fields (COUNTIFS, SUMIFS)
        data = compute_aggregations(data, rulebook_entity, rulebook, project_root)

        if not available_funcs:
            # No assembly functions - save with lookups/aggregations computed
            print(f"  -> {entity}: No assembly functions, saved with lookups/aggregations only")
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            total_records += len(data)
            entity_count += 1
            continue

        # Process records using entity-specific schema and functions
        processed = process_records(data, lib, schema, struct_size, available_funcs)

        # Save results
        with open(output_path, 'w') as f:
            json.dump(processed, f, indent=2)

        total_records += len(processed)
        entity_count += 1
        print(f"  -> {entity}: {len(processed)} records")

    print(f"\nBinary substrate: Processed {entity_count} entities, {total_records} total records")
    print("=" * 70)


# =============================================================================
# LEGACY MODE
# =============================================================================

def run_legacy(script_dir: Path):
    """Process single test-answers.json file (legacy mode)."""
    test_file = script_dir / "test-answers.json"

    print("=" * 70)
    print("Binary Execution Substrate - Test Execution")
    print("=" * 70)
    print()

    # Load library
    lib, lib_path = load_binary_library(script_dir)
    print(f"Loaded library: {lib_path}")

    # Load rulebook to get schema
    print("\nLoading rulebook...")
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Build schema from first entity in rulebook
    entity_name = next((k for k, v in rulebook.items()
                        if isinstance(v, dict) and 'schema' in v), None)
    if not entity_name:
        print("ERROR: No entity with schema found in rulebook")
        sys.exit(1)
    columns = rulebook[entity_name].get("schema", [])
    schema, struct_size = build_schema(columns)
    print(f"Schema built: {len(schema)} fields, struct size: {struct_size} bytes")

    # Load test data
    print(f"\nLoading test data: {test_file}")
    if not test_file.exists():
        print(f"ERROR: Test file not found: {test_file}")
        sys.exit(1)

    with open(test_file, "r") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} records")

    # Get available functions
    print("\nVerifying assembly functions...")
    available_funcs = get_available_functions(lib)
    for field_name, (func_name, ret_type) in available_funcs.items():
        print(f"  Found: {func_name} -> {ret_type}")

    if not available_funcs:
        print("ERROR: No assembly functions found!")
        sys.exit(1)

    # Process records
    print(f"\nProcessing {len(data)} records...")
    processed = process_records(data, lib, schema, struct_size, available_funcs)

    # Save results
    print(f"\nSaving results to: {test_file}")
    with open(test_file, "w") as f:
        json.dump(processed, f, indent=2)

    print("\nTest execution complete!")
    print("=" * 70)


# =============================================================================
# MAIN
# =============================================================================

def main():
    script_dir = Path(__file__).resolve().parent
    run_multi_entity(script_dir)


if __name__ == "__main__":
    main()
