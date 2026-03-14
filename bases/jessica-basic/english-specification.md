# Specification Document for Jessica Talisman - BASIC Ontology Parts 1-3

## Overview
This document provides a detailed specification for the rulebook "Jessica Talisman - BASIC Ontology Parts 1-3". It outlines how to compute calculated fields based on raw input fields for various entities within the rulebook. The primary focus is on the workflows and workflow steps, detailing the necessary inputs and the computation process for derived values.

---

## Workflows

### Input Fields
1. **WorkflowId**
   - **Type:** String
   - **Description:** Unique identifier for the workflow.

2. **DisplayName**
   - **Type:** String
   - **Description:** Short, human-friendly name for the workflow.

3. **CountOfNonProposedSteps**
   - **Type:** Integer
   - **Description:** Count of workflow steps that are not proposed.

### Calculated Fields

#### 1. Name
- **Description:** A machine-friendly name for the workflow, used for programmatic reference and URL slug generation.
- **Computation:** Convert the DisplayName to lowercase and replace spaces with hyphens.
- **Formula:** `=SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")`
- **Example:** 
  - If `DisplayName` is "Performance Review", then:
    - Computed `Name` = "performance-review".

#### 2. HasMoreThan1Step
- **Description:** Indicates whether the workflow has more than one non-proposed step.
- **Computation:** Check if `CountOfNonProposedSteps` is greater than 1.
- **Formula:** `={{CountOfNonProposedSteps}} > 1`
- **Example:**
  - If `CountOfNonProposedSteps` is 3, then:
    - Computed `HasMoreThan1Step` = true.

---

## Workflow Steps

### Input Fields
1. **WorkflowStepId**
   - **Type:** String
   - **Description:** Unique identifier for the workflow step.

2. **DisplayName**
   - **Type:** String
   - **Description:** Short, human-friendly name for the workflow step.

3. **Workflow**
   - **Type:** String
   - **Description:** Foreign key to the parent workflow.

### Calculated Fields

#### 1. Name
- **Description:** A machine-friendly name for the workflow step, used for programmatic reference.
- **Computation:** Convert the DisplayName to lowercase and replace spaces with hyphens.
- **Formula:** `=SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")`
- **Example:**
  - If `DisplayName` is "Submit Request", then:
    - Computed `Name` = "submit-request".

---

## Approval Gates

### Input Fields
1. **ApprovalGateId**
   - **Type:** String
   - **Description:** Unique identifier for the approval gate.

2. **DisplayName**
   - **Type:** String
   - **Description:** Short, human-friendly name for the approval gate.

### Calculated Fields

#### 1. Name
- **Description:** A machine-friendly name for the approval gate, used for programmatic reference.
- **Computation:** Convert the DisplayName to lowercase and replace spaces with hyphens.
- **Formula:** `=SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")`
- **Example:**
  - If `DisplayName` is "Manager Approval", then:
    - Computed `Name` = "manager-approval".

---

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
- **Description:** A formatted display name for the step based on its number.
- **Computation:** Concatenate "Step-" with the StepNumber.
- **Formula:** `="Step-" & {{StepNumber}}`
- **Example:**
  - If `StepNumber` is 1, then:
    - Computed `DisplayName` = "Step-1".

---

## Conclusion
This specification document provides a comprehensive guide to computing the calculated fields for the "Jessica Talisman - BASIC Ontology Parts 1-3" rulebook. By following the outlined steps and examples, users can derive the necessary values without needing access to the original formulas.