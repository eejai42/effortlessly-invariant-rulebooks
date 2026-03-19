"""
ERB Calculation Library (GENERATED - DO NOT EDIT)
=================================================
Generated from: effortless-rulebook/effortless-rulebook.json

This file contains pure functions that compute calculated fields
from raw field values. Supports multiple entities.
"""

from typing import Optional, Any


# =============================================================================
# SHAPES CALCULATIONS
# Table: Shapes
# =============================================================================

# Level 1

def calc_shapes_is_rectangle(how_many_sides):
    """Formula: =AND({{HowManySides}}=4)"""
    return ((how_many_sides == 4))

def calc_shapes_is_triangle(sum_of_internal_angles, how_many_sides):
    """Formula: =AND({{SumOfInternalAngles}}=180, {{HowManySides}}=3)"""
    return ((sum_of_internal_angles == 180) and (how_many_sides == 3))

def calc_shapes_is_right_triangle(is_triangle, max_angle):
    """Formula: =AND({{IsTriangle}}, {{MaxAngle}} = 90)"""
    return ((is_triangle is True) and (max_angle == 90))

def calc_shapes_pythagorean_theorem_holds(is_right_triangle, hypotenuse_length_squared, non_hypotenuse_sides_squared):
    """Formula: =AND(
  {{IsRightTriangle}},  
  {{HypotenuseLengthSquared}} = {{NonHypotenuseSidesSquared}}
)"""
    return ((is_right_triangle is True) and (hypotenuse_length_squared == non_hypotenuse_sides_squared))


def compute_shapes_fields(record: dict) -> dict:
    """
    Compute all calculated fields for Shapes.
    
    Table: Shapes
    """
    result = dict(record)

    # Level 1 calculations
    result['is_rectangle'] = calc_shapes_is_rectangle(result.get('how_many_sides'))
    result['is_triangle'] = calc_shapes_is_triangle(result.get('sum_of_internal_angles'), result.get('how_many_sides'))
    result['is_right_triangle'] = calc_shapes_is_right_triangle(result.get('is_triangle'), result.get('max_angle'))
    result['pythagorean_theorem_holds'] = calc_shapes_pythagorean_theorem_holds(result.get('is_right_triangle'), result.get('hypotenuse_length_squared'), result.get('non_hypotenuse_sides_squared'))

    return result

# =============================================================================
# SIDES CALCULATIONS
# Table: Sides
# =============================================================================

# Level 1


def calc_sides_length_squared():
    """ERROR: Could not parse formula: ={{Length}} * {{Length}}
    Error: Unexpected character '*' at position 11
    """
    raise NotImplementedError("Formula parsing failed")


# Level 2

def calc_sides_name(shape, label):
    """Formula: ={{Shape}} & "-Side-" & {{Label}}"""
    return (str(shape or "") + '-Side-' + str(label or ""))

def calc_sides_is_hypotenuse(is_triangle, length, previous_side_length, next_length):
    """
    Is this the Hypotenuse of a Right Angle Triangle?
    
    Formula: =AND(
  {{IsTriangle}},
  {{Length}} > {{PreviousSideLength}},
  {{Length}} > {{NextLength}}
)
    """
    return ((is_triangle is True) and (length > previous_side_length) and (length > next_length))

def calc_sides_status_of_theorem(is_triangle, is_right_triangle, pythagorean_theorem_holds):
    """
    Invalid if it is a Triangle with Mismatchd Edge Lengths and Angles.
    
    Formula: =IF({{IsTriangle}}, 
  IF(AND({{IsRightTriangle}}, NOT({{PythagoreanTheoremHolds}})), 
    "PYTHAGOREAN THEOREM FALSIFIED!", 
    "Pythagorean Theorem Holds (obviously)."
  ),
  "NA"
)
    """
    return (('PYTHAGOREAN THEOREM FALSIFIED!' if ((is_right_triangle is True) and (pythagorean_theorem_holds is not True)) else 'Pythagorean Theorem Holds (obviously).') if is_triangle else 'NA')

def calc_sides_hypotenuse_length_squared(is_hypotenuse, length_squared):
    """Formula: =IF({{IsHypotenuse}}, {{LengthSquared}})"""
    return (length_squared if is_hypotenuse else None)

def calc_sides_non_hypotenuse_length_squared(is_hypotenuse, is_triangle, length_squared):
    """Formula: =IF(AND(NOT({{IsHypotenuse}}), {{IsTriangle}}), {{LengthSquared}})"""
    return (length_squared if ((is_hypotenuse is not True) and (is_triangle is True)) else None)


def compute_sides_fields(record: dict) -> dict:
    """
    Compute all calculated fields for Sides.
    
    Table: Sides
    """
    result = dict(record)

    # Level 1 calculations
    result['length_squared'] = calc_sides_length_squared()

    # Level 2 calculations
    result['name'] = calc_sides_name(result.get('shape'), result.get('label'))
    result['is_hypotenuse'] = calc_sides_is_hypotenuse(result.get('is_triangle'), result.get('length'), result.get('previous_side_length'), result.get('next_length'))
    result['status_of_theorem'] = calc_sides_status_of_theorem(result.get('is_triangle'), result.get('is_right_triangle'), result.get('pythagorean_theorem_holds'))
    result['hypotenuse_length_squared'] = calc_sides_hypotenuse_length_squared(result.get('is_hypotenuse'), result.get('length_squared'))
    result['non_hypotenuse_length_squared'] = calc_sides_non_hypotenuse_length_squared(result.get('is_hypotenuse'), result.get('is_triangle'), result.get('length_squared'))

    # Convert empty strings to None for string fields
    for key in ['name', 'status_of_theorem']:
        if result.get(key) == '':
            result[key] = None

    return result

# =============================================================================
# ERBVERSIONS CALCULATIONS
# Table: ERBVersions
# =============================================================================

# Level 1

def calc_erb_versions_pk(base_id, name):
    """Formula: ={{BaseId}} & "-" & {{Name}}"""
    return (str(base_id or "") + '-' + str(name or ""))


def compute_erb_versions_fields(record: dict) -> dict:
    """
    Compute all calculated fields for ERBVersions.
    
    Table: ERBVersions
    """
    result = dict(record)

    # Level 1 calculations
    result['pk'] = calc_erb_versions_pk(result.get('base_id'), result.get('name'))

    # Convert empty strings to None for string fields
    for key in ['pk']:
        if result.get(key) == '':
            result[key] = None

    return result


# =============================================================================
# DISPATCHER FUNCTION
# =============================================================================

def compute_all_calculated_fields(record: dict, entity_name: str = None) -> dict:
    """
    Compute all calculated fields for a record.
    
    This is the main entry point for computing calculated fields.
    It routes to the appropriate entity-specific compute function.
    
    Args:
        record: The record dict with raw field values
        entity_name: Entity name (snake_case or PascalCase)
    
    Returns:
        Record dict with calculated fields filled in
    """
    if entity_name is None:
        # No entity specified - return record unchanged
        return dict(record)

    # Normalize to snake_case to support "LineItem", "line_item", "line-item"
    entity_lower = entity_name.lower().replace('-', '_')

    if entity_lower == 'shapes':
        return compute_shapes_fields(record)
    elif entity_lower == 'sides':
        return compute_sides_fields(record)
    elif entity_lower == 'erb_versions':
        return compute_erb_versions_fields(record)
    else:
        # Unknown entity - return record unchanged (no error)
        return dict(record)