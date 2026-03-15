"""
ERB Calculation Library (GENERATED - DO NOT EDIT)
=================================================
Generated from: effortless-rulebook/effortless-rulebook.json

This file contains pure functions that compute calculated fields
from raw field values. Supports multiple entities.
"""

from typing import Optional, Any


# =============================================================================
# WORKFLOWS CALCULATIONS
# Table: Workflows
# =============================================================================

# Level 1

def calc_workflows_name(display_name):
    """
    Short machine-friendly name for the workflow. Used for programmatic reference and URL slug generation.
    
    Formula: =SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")
    """
    return ((((display_name or "").lower()) or "").replace(' ', '-'))

# Level 2

def calc_workflows_has_more_than1_step(count_of_non_proposed_steps):
    """Formula: ={{CountOfNonProposedSteps}} > 1"""
    return (count_of_non_proposed_steps > 1)


def compute_workflows_fields(record: dict) -> dict:
    """
    Compute all calculated fields for Workflows.
    
    Table: Workflows
    """
    result = dict(record)

    # Level 1 calculations
    result['name'] = calc_workflows_name(result.get('display_name'))

    # Level 2 calculations
    result['has_more_than1_step'] = calc_workflows_has_more_than1_step(result.get('count_of_non_proposed_steps'))

    # Convert empty strings to None for string fields
    for key in ['name']:
        if result.get(key) == '':
            result[key] = None

    return result

# =============================================================================
# WORKFLOWSTEPS CALCULATIONS
# Table: WorkflowSteps
# =============================================================================

# Level 1

def calc_workflow_steps_name(display_name):
    """Formula: =SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")"""
    return ((((display_name or "").lower()) or "").replace(' ', '-'))


def compute_workflow_steps_fields(record: dict) -> dict:
    """
    Compute all calculated fields for WorkflowSteps.
    
    Table: WorkflowSteps
    """
    result = dict(record)

    # Level 1 calculations
    result['name'] = calc_workflow_steps_name(result.get('display_name'))

    # Convert empty strings to None for string fields
    for key in ['name']:
        if result.get(key) == '':
            result[key] = None

    return result

# =============================================================================
# APPROVALGATES CALCULATIONS
# Table: ApprovalGates
# =============================================================================

# Level 1

def calc_approval_gates_name(display_name):
    """Formula: =SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")"""
    return ((((display_name or "").lower()) or "").replace(' ', '-'))


def compute_approval_gates_fields(record: dict) -> dict:
    """
    Compute all calculated fields for ApprovalGates.
    
    Table: ApprovalGates
    """
    result = dict(record)

    # Level 1 calculations
    result['name'] = calc_approval_gates_name(result.get('display_name'))

    # Convert empty strings to None for string fields
    for key in ['name']:
        if result.get(key) == '':
            result[key] = None

    return result

# =============================================================================
# PRECEDESSTEPS CALCULATIONS
# Table: PrecedesSteps
# =============================================================================

# Level 1

def calc_precedes_steps_display_name(step_number):
    """Formula: ="Step-" & {{StepNumber}}"""
    return ('Step-' + str(step_number or ""))


def compute_precedes_steps_fields(record: dict) -> dict:
    """
    Compute all calculated fields for PrecedesSteps.
    
    Table: PrecedesSteps
    """
    result = dict(record)

    # Level 1 calculations
    result['display_name'] = calc_precedes_steps_display_name(result.get('step_number'))

    # Convert empty strings to None for string fields
    for key in ['display_name']:
        if result.get(key) == '':
            result[key] = None

    return result

# =============================================================================
# ROLES CALCULATIONS
# Table: Roles
# =============================================================================

# Level 1

def calc_roles_name(display_name):
    """Formula: =LOWER({{DisplayName}})"""
    return ((display_name or "").lower())


def compute_roles_fields(record: dict) -> dict:
    """
    Compute all calculated fields for Roles.
    
    Table: Roles
    """
    result = dict(record)

    # Level 1 calculations
    result['name'] = calc_roles_name(result.get('display_name'))

    # Convert empty strings to None for string fields
    for key in ['name']:
        if result.get(key) == '':
            result[key] = None

    return result

# =============================================================================
# DEPARTMENTS CALCULATIONS
# Table: Departments
# =============================================================================

# Level 1

def calc_departments_name(display_name):
    """
    Human-readable display name of the department. Should match organizational terminology for stakeholder communication.
    
    Formula: =SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")
    """
    return ((((display_name or "").lower()) or "").replace(' ', '-'))


def compute_departments_fields(record: dict) -> dict:
    """
    Compute all calculated fields for Departments.
    
    Table: Departments
    """
    result = dict(record)

    # Level 1 calculations
    result['name'] = calc_departments_name(result.get('display_name'))

    # Convert empty strings to None for string fields
    for key in ['name']:
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

    if entity_lower == 'workflows':
        return compute_workflows_fields(record)
    elif entity_lower == 'workflow_steps':
        return compute_workflow_steps_fields(record)
    elif entity_lower == 'approval_gates':
        return compute_approval_gates_fields(record)
    elif entity_lower == 'precedes_steps':
        return compute_precedes_steps_fields(record)
    elif entity_lower == 'roles':
        return compute_roles_fields(record)
    elif entity_lower == 'departments':
        return compute_departments_fields(record)
    else:
        # Unknown entity - return record unchanged (no error)
        return dict(record)