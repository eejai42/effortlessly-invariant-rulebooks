"""
ERB Calculation Library (GENERATED - DO NOT EDIT)
=================================================
Generated from: effortless-rulebook/effortless-rulebook.json

This file contains pure functions that compute calculated fields
from raw field values. Supports multiple entities.
"""

from typing import Optional, Any


# =============================================================================
# CUSTOMERS CALCULATIONS
# Table: Customers
# =============================================================================

# Level 1

def calc_customers_full_name(last_name, first_name):
    """
    Full name is computed from the first and last name of the customer
    
    Formula: ={{LastName}} & ", " & {{FirstName}}
    """
    return (str(last_name or "") + ', ' + str(first_name or ""))


def compute_customers_fields(record: dict) -> dict:
    """
    Compute all calculated fields for Customers.
    
    Table: Customers
    """
    result = dict(record)

    # Level 1 calculations
    result['full_name'] = calc_customers_full_name(result.get('last_name'), result.get('first_name'))

    # Convert empty strings to None for string fields
    for key in ['full_name']:
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

    if entity_lower == 'customers':
        return compute_customers_fields(record)
    else:
        # Unknown entity - return record unchanged (no error)
        return dict(record)