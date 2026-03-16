# Specification Document for Jessica Talisman - ADVANCED Ontology Parts 1-3

## Overview
This document outlines the specifications for calculating fields within the "Jessica Talisman - ADVANCED Ontology Parts 1-3" rulebook. The rulebook is structured to manage workflows, workflow steps, approvals, roles, departments, and agents, providing a comprehensive framework for operational processes. The calculations are primarily based on raw data inputs and are designed to facilitate analysis and reporting.

## Workflows

### Input Fields
1. **WorkflowId**
   - **Type:** string
   - **Description:** Unique identifier for the workflow.

2. **DisplayName**
   - **Type:** string
   - **Description:** Human-readable name of the workflow.

3. **WorkflowSteps**
   - **Type:** string
   - **Description:** Reference to the steps that make up the workflow.

### Calculated Fields
1. **Name**
   - **Description:** A machine-friendly name for the workflow, used for programmatic reference and URL slug generation.
   - **Calculation:** Convert the `DisplayName` to lowercase and replace spaces with hyphens.
   - **Formula:** `=SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")`
   - **Example:** If `DisplayName` is "Production Deployment", then `Name` would be "production-deployment".

2. **CountOfSteps**
   - **Description:** The total number of steps in the workflow.
   - **Calculation:** Count the number of entries in `WorkflowSteps` that match the current `WorkflowId`.
   - **Formula:** `=COUNTIFS(WorkflowSteps!{{Workflow}}, Workflows!{{WorkflowId}})`
   - **Example:** If there are 5 steps listed under `WorkflowSteps` for `WorkflowId` "production-deployment", then `CountOfSteps` would be 5.

3. **HasMoreThan1Step**
   - **Description:** A boolean indicating whether the workflow has more than one step.
   - **Calculation:** Check if `CountOfSteps` is greater than 1.
   - **Formula:** `={{CountOfSteps}} > 1`
   - **Example:** If `CountOfSteps` is 5, then `HasMoreThan1Step` would be `true`.

---

## WorkflowSteps

### Input Fields
1. **WorkflowStepId**
   - **Type:** string
   - **Description:** Unique identifier for the workflow step.

2. **DisplayName**
   - **Type:** string
   - **Description:** Human-readable name of the workflow step.

3. **AssignedRole**
   - **Type:** string
   - **Description:** Role responsible for executing this step.

4. **AssignedRoleDepartment**
   - **Type:** string
   - **Description:** Department that owns the assigned role.

### Calculated Fields
1. **Name**
   - **Description:** A machine-friendly name for the workflow step.
   - **Calculation:** Convert the `DisplayName` to lowercase and replace spaces with hyphens.
   - **Formula:** `=SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")`
   - **Example:** If `DisplayName` is "Risk Analysis", then `Name` would be "risk-analysis".

2. **ExecutionActorType**
   - **Description:** Defines the type of actor executing the step based on the department of the assigned role.
   - **Calculation:** If `AssignedRoleDepartment` is "HumanAgent", return "HumanAgent"; if "AIAgent", return "AIAgent"; if "AutomatedPipeline", return "AutomatedPipeline"; otherwise, return blank.
   - **Formula:** `=IF({{AssignedRoleDepartment}} = "HumanAgent", "HumanAgent", IF({{AssignedRoleDepartment}} = "AIAgent", "AIAgent", IF({{AssignedRoleDepartment}} = "AutomatedPipeline", "AutomatedPipeline", BLANK())))`
   - **Example:** If `AssignedRoleDepartment` is "engineering", and the role is filled by a human agent, then `ExecutionActorType` would be "HumanAgent".

3. **ApprovalGateEscalationThresholdHours**
   - **Description:** The number of hours that may elapse on a pending gate before escalation occurs.
   - **Calculation:** Lookup the `EscalationThresholdHours` from the `Approvals` table based on the `ApprovalGate`.
   - **Formula:** `=INDEX(Approvals!{{EscalationThresholdHours}}, MATCH(WorkflowSteps!{{ApprovalGate}}, Approvals!{{ApprovalId}}, 0))`
   - **Example:** If the `ApprovalGate` is "release-approval-gate", and the corresponding `EscalationThresholdHours` is 24, then this field would return 24.

---

## Approvals

### Input Fields
1. **ApprovalId**
   - **Type:** string
   - **Description:** Unique identifier for the approval gate.

2. **DisplayName**
   - **Type:** string
   - **Description:** Human-readable name of the approval gate.

3. **WorkflowSteps**
   - **Type:** string
   - **Description:** Reference to workflow steps that use this approval gate.

### Calculated Fields
1. **Name**
   - **Description:** A machine-friendly name for the approval gate.
   - **Calculation:** Convert the `DisplayName` to lowercase and replace spaces with hyphens.
   - **Formula:** `=SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")`
   - **Example:** If `DisplayName` is "Release Approval Gate", then `Name` would be "release-approval-gate".

2. **Workflow_from_WorkflowSteps**
   - **Description:** Lookup the workflow associated with the steps that require this approval gate.
   - **Calculation:** Retrieve the `Workflow` from the `WorkflowSteps` table based on the `WorkflowSteps` reference.
   - **Formula:** `=INDEX(WorkflowSteps!{{Workflow}}, MATCH(Approvals!{{WorkflowSteps}}, WorkflowSteps!{{WorkflowStepId}}, 0))`
   - **Example:** If `WorkflowSteps` contains "release-approval-gate", it would return "production-deployment".

---

## Summary
This specification document provides a detailed guide on how to compute calculated fields within the "Jessica Talisman - ADVANCED Ontology Parts 1-3" rulebook. By following the outlined steps and examples, users can accurately derive the necessary values without needing to reference the original formulas directly.