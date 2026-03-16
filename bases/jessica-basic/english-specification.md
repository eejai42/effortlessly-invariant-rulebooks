# Specification Document for Jessica Talisman - BASIC Ontology Parts 1-3

## Overview
This document outlines the specifications for the rulebook "Jessica Talisman - BASIC Ontology Parts 1-3". It describes how to compute calculated fields based on the input fields defined in the rulebook's schema. The rulebook is structured around workflows and their associated steps, providing a comprehensive view of how to manage and analyze various business processes.

## Workflows

### Input Fields
1. **WorkflowId**
   - **Type:** String
   - **Description:** Unique identifier for the workflow.

2. **DisplayName**
   - **Type:** String
   - **Description:** Human-readable name for the workflow.

3. **Title**
   - **Type:** String
   - **Description:** Human-readable title of the workflow.

4. **Description**
   - **Type:** String
   - **Description:** Detailed description of the workflow's purpose and scope.

5. **Identifier**
   - **Type:** String
   - **Description:** External system identifier for cross-referencing.

6. **Modified**
   - **Type:** Datetime
   - **Description:** Last modification timestamp.

7. **WorkflowSteps**
   - **Type:** String
   - **Description:** Reference to workflow steps.

### Calculated Fields

#### 1. **Name**
- **Description:** This field generates a short, machine-friendly name for the workflow, which is used for programmatic reference and URL slug generation.
- **Computation:** Convert the `DisplayName` to lowercase and replace spaces with hyphens.
- **Formula:** `=SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")`
- **Example:** 
  - If `DisplayName` is "Performance Review", the computed `Name` would be "performance-review".

#### 2. **CountOfNonProposedSteps**
- **Description:** This field calculates the total number of steps associated with the workflow.
- **Computation:** Count the number of entries in `WorkflowSteps` that match the current `WorkflowId`.
- **Formula:** `=COUNTIFS(WorkflowSteps!{{Workflow}}, Workflows!{{WorkflowId}})`
- **Example:**
  - If `WorkflowSteps` contains "system-notification-sent, step-2, recwwXHLqxKPhj6Mt" for `WorkflowId` "performance-review", the computed `CountOfNonProposedSteps` would be 3.

#### 3. **HasMoreThan1Step**
- **Description:** This boolean field indicates whether the workflow contains more than one step.
- **Computation:** Check if `CountOfNonProposedSteps` is greater than 1.
- **Formula:** `={{CountOfNonProposedSteps}} > 1`
- **Example:**
  - For the workflow with `CountOfNonProposedSteps` equal to 3, `HasMoreThan1Step` would be `true`. For a workflow with `CountOfNonProposedSteps` equal to 1, it would be `false`.

## Workflow Steps

### Input Fields
1. **WorkflowStepId**
   - **Type:** String
   - **Description:** Unique identifier for the workflow step.

2. **DisplayName**
   - **Type:** String
   - **Description:** Human-readable name for the workflow step.

3. **Workflow**
   - **Type:** String
   - **Description:** Reference to the parent workflow.

4. **SequencePosition**
   - **Type:** Integer
   - **Description:** Ordinal position of the step within its workflow.

5. **AssignedRole**
   - **Type:** String
   - **Description:** Role responsible for executing this step.

6. **RequiresHumanApproval**
   - **Type:** Boolean
   - **Description:** Indicates if the step requires human approval.

7. **ApprovalGate**
   - **Type:** String
   - **Description:** Reference to the approval gate if this step is a decision checkpoint.

8. **PrecededBySteps**
   - **Type:** String
   - **Description:** Reference to steps that must complete before this step can execute.

### Calculated Fields

#### 1. **Name**
- **Description:** This field generates a machine-friendly name for the workflow step.
- **Computation:** Convert the `DisplayName` to lowercase and replace spaces with hyphens.
- **Formula:** `=SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")`
- **Example:**
  - If `DisplayName` is "Submit Request", the computed `Name` would be "submit-request".

## Approval Gates

### Input Fields
1. **ApprovalGateId**
   - **Type:** String
   - **Description:** Unique identifier for the approval gate.

2. **DisplayName**
   - **Type:** String
   - **Description:** Human-readable name for the approval gate.

3. **WorkflowSteps**
   - **Type:** String
   - **Description:** Reference to workflow steps that use this approval gate.

4. **EscalationThresholdHours**
   - **Type:** Integer
   - **Description:** Number of hours that may elapse on a pending gate before escalation activates.

### Calculated Fields

#### 1. **Name**
- **Description:** This field generates a machine-friendly name for the approval gate.
- **Computation:** Convert the `DisplayName` to lowercase and replace spaces with hyphens.
- **Formula:** `=SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")`
- **Example:**
  - If `DisplayName` is "Manager Approval", the computed `Name` would be "manager-approval".

## Conclusion
This specification document provides a detailed guide on how to compute calculated fields based on the input fields defined in the rulebook. By following the outlined steps and examples, users can accurately derive the values needed for effective workflow and step management.