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

def calc_customers_full_name(first_name, last_name):
    """
    Full name is computed from the first and last name of the customer
    
    Formula: ={{FirstName}} & " " & {{LastName}}
    """
    return ((((display_name or "").lower()) or "").replace(' ', '-'))

# Level 2

def calc_workflows_has_more_than1_step(count_of_steps):
    """Formula: ={{CountOfSteps}} > 1"""
    return (count_of_steps > 1)


def compute_customers_fields(record: dict) -> dict:
    """
    Compute all calculated fields for Customers.
    
    Table: Customers
    """
    result = dict(record)

    # Level 1 calculations
    result['name'] = calc_workflows_name(result.get('display_name'))

    # Level 2 calculations
    result['has_more_than1_step'] = calc_workflows_has_more_than1_step(result.get('count_of_steps'))

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

# Level 2

def calc_workflow_steps_execution_actor_type(assigned_role_department):
    """Formula: =IF({{AssignedRoleDepartment}} = "HumanAgent", "HumanAgent", IF({{AssignedRoleDepartment}} = "AIAgent", "AIAgent", IF({{AssignedRoleDepartment}} = "AutomatedPipeline", "AutomatedPipeline", BLANK())))"""
    return ('HumanAgent' if (assigned_role_department == 'HumanAgent') else ('AIAgent' if (assigned_role_department == 'AIAgent') else ('AutomatedPipeline' if (assigned_role_department == 'AutomatedPipeline') else None)))


def compute_workflow_steps_fields(record: dict) -> dict:
    """
    Compute all calculated fields for WorkflowSteps.
    
    Table: WorkflowSteps
    """
    result = dict(record)

    # Level 1 calculations
    result['name'] = calc_workflow_steps_name(result.get('display_name'))

    # Level 2 calculations
    result['execution_actor_type'] = calc_workflow_steps_execution_actor_type(result.get('assigned_role_department'))

    # Convert empty strings to None for string fields
    for key in ['name', 'execution_actor_type']:
        if result.get(key) == '':
            result[key] = None

    return result

# =============================================================================
# APPROVALS CALCULATIONS
# Table: Approvals
# =============================================================================

# Level 1

def calc_approvals_name(display_name):
    """Formula: =SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")"""
    return ((((display_name or "").lower()) or "").replace(' ', '-'))


def compute_approvals_fields(record: dict) -> dict:
    """
    Compute all calculated fields for Approvals.
    
    Table: Approvals
    """
    result = dict(record)

    # Level 1 calculations
    result['name'] = calc_approvals_name(result.get('display_name'))

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
    elif entity_lower == 'approvals':
        return compute_approvals_fields(record)
    elif entity_lower == 'precedes_steps':
        return compute_precedes_steps_fields(record)
    elif entity_lower == 'roles':
        return compute_roles_fields(record)
    elif entity_lower == 'departments':
        return compute_departments_fields(record)
    else:
        # Unknown entity - return record unchanged (no error)
        return dict(record)