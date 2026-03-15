# Specification Document for Jessica Talisman - BASIC Ontology Parts 1-3

## Overview
This document outlines the specifications for calculating fields within the "Jessica Talisman - BASIC Ontology Parts 1-3" rulebook. The rulebook is structured around workflows and their associated steps, providing a framework for managing and analyzing organizational processes. The calculated fields derive values based on raw input fields, enabling insights into workflow complexity and characteristics.

## Workflows

### Input Fields
1. **WorkflowId**
   - **Type:** String
   - **Description:** Unique identifier for the workflow.

2. **DisplayName**
   - **Type:** String
   - **Description:** Human-readable name for the workflow.

3. **CountOfNonProposedSteps**
   - **Type:** Integer
   - **Description:** Count of workflow steps in this workflow.

### Calculated Fields

#### 1. Name
- **Description:** A machine-friendly name for the workflow, used for programmatic reference and URL slug generation.
- **Calculation:** The `Name` is computed by taking the `DisplayName`, converting it to lowercase, and replacing spaces with hyphens.
- **Formula:** `=SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")`
- **Example:** For a workflow with `DisplayName` "Performance Review", the `Name` would be "performance-review".

#### 2. HasMoreThan1Step
- **Description:** Indicates whether the workflow contains more than one step.
- **Calculation:** This field is computed by checking if `CountOfNonProposedSteps` is greater than 1.
- **Formula:** `={{CountOfNonProposedSteps}} > 1`
- **Example:** If `CountOfNonProposedSteps` is 3, then `HasMoreThan1Step` would be `true`. If it is 1, then `HasMoreThan1Step` would be `false`.

## Workflow Steps

### Input Fields
1. **WorkflowStepId**
   - **Type:** String
   - **Description:** Unique identifier for the workflow step.

2. **DisplayName**
   - **Type:** String
   - **Description:** Human-readable name for the workflow step.

### Calculated Fields

#### 1. Name
- **Description:** A machine-friendly name for the workflow step, used for programmatic reference.
- **Calculation:** The `Name` is computed by taking the `DisplayName`, converting it to lowercase, and replacing spaces with hyphens.
- **Formula:** `=SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")`
- **Example:** For a step with `DisplayName` "Manager Review", the `Name` would be "manager-review".

## Approval Gates

### Input Fields
1. **ApprovalGateId**
   - **Type:** String
   - **Description:** Unique identifier for the approval gate.

2. **DisplayName**
   - **Type:** String
   - **Description:** Human-readable name for the approval gate.

### Calculated Fields

#### 1. Name
- **Description:** A machine-friendly name for the approval gate, used for programmatic reference.
- **Calculation:** The `Name` is computed by taking the `DisplayName`, converting it to lowercase, and replacing spaces with hyphens.
- **Formula:** `=SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")`
- **Example:** For an approval gate with `DisplayName` "Manager Approval", the `Name` would be "manager-approval".

## Precedes Steps

### Input Fields
1. **PrecedesStepId**
   - **Type:** String
   - **Description:** Unique identifier for the precedes step.

2. **StepNumber**
   - **Type:** Integer
   - **Description:** Ordinal sequence number for the relationship.

### Calculated Fields

#### 1. DisplayName
- **Description:** A formatted display name for the step based on its sequence number.
- **Calculation:** The `DisplayName` is computed by concatenating the string "Step-" with the `StepNumber`.
- **Formula:** `="Step-" & {{StepNumber}}`
- **Example:** If `StepNumber` is 3, then `DisplayName` would be "Step-3".

## Roles

### Input Fields
1. **RoleId**
   - **Type:** String
   - **Description:** Unique identifier for the role.

2. **DisplayName**
   - **Type:** String
   - **Description:** Human-readable name for the role.

### Calculated Fields

#### 1. Name
- **Description:** A machine-friendly name for the role, used for programmatic reference.
- **Calculation:** The `Name` is computed by converting the `DisplayName` to lowercase.
- **Formula:** `=LOWER({{DisplayName}})`
- **Example:** For a role with `DisplayName` "Administrator", the `Name` would be "administrator".

## Conclusion
This specification document provides a detailed guide on how to compute calculated fields within the "Jessica Talisman - BASIC Ontology Parts 1-3" rulebook. By following the outlined calculations and examples, users can derive the necessary values for effective workflow management and analysis.