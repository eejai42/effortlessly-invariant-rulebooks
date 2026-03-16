# JTO - v3 Rulebook Specification Document

## Overview
The JTO - v3 rulebook defines a schema for workflows, workflow steps, roles, and human agents. It includes specific calculations to derive certain fields based on relationships and data aggregations. This document outlines how to compute the calculated fields within the rulebook, detailing the necessary input fields and providing clear instructions for each calculation.

## Workflows

### Input Fields
1. **WorkflowId**
   - **Type:** string
   - **Description:** Unique identifier for the workflow.

2. **Title**
   - **Type:** string
   - **Description:** Title of the workflow.

3. **Description**
   - **Type:** string
   - **Description:** Description of the workflow.

4. **Created**
   - **Type:** datetime
   - **Description:** Date and time when the workflow was created.

5. **Modified**
   - **Type:** datetime
   - **Description:** Date and time when the workflow was last modified.

6. **Identifier**
   - **Type:** string
   - **Description:** An additional identifier for the workflow.

7. **WorkflowSteps**
   - **Type:** string
   - **Description:** A list of workflow step IDs associated with this workflow.

### Calculated Field
#### CountOfWorkflowSteps
- **Description:** This field counts the number of workflow steps associated with the workflow.
- **Calculation Method:** 
  - Use the `COUNTIFS` function to count the number of entries in the `WorkflowSteps` table where the `IsStepOf` field matches the `WorkflowId` of the current workflow.
- **Formula:** 
  ```plaintext
  =COUNTIFS(WorkflowSteps!{{IsStepOf}}, Workflows!{{WorkflowId}})
  ```
- **Example:** 
  For the workflow with `WorkflowId` "production-deployment-workflow", the `CountOfWorkflowSteps` is calculated as follows:
  - The `WorkflowSteps` associated with this workflow are "legal-review", "risk-assessment", and "release-approval".
  - Therefore, the count is 3.

## WorkflowSteps

### Input Fields
1. **WorkflowStepId**
   - **Type:** string
   - **Description:** Unique identifier for the workflow step.

2. **Label**
   - **Type:** string
   - **Description:** Label for the workflow step.

3. **SequencePosition**
   - **Type:** integer
   - **Description:** Position of the workflow step in the sequence.

4. **RequiresHumanApproval**
   - **Type:** boolean
   - **Description:** Indicates if the workflow step requires human approval.

5. **IsStepOf**
   - **Type:** string
   - **Description:** The workflow ID that this step is part of.

6. **AssignedRole**
   - **Type:** string
   - **Description:** The role assigned to this workflow step.

### Calculated Fields
#### IsStepOfTitle
- **Description:** Retrieves the title of the workflow that this step is part of.
- **Calculation Method:** 
  - Use the `INDEX` and `MATCH` functions to find the title in the `Workflows` table where the `WorkflowId` matches the `IsStepOf` field.
- **Formula:** 
  ```plaintext
  =INDEX(Workflows!{{Title}}, MATCH(WorkflowSteps!{{IsStepOf}}, Workflows!{{WorkflowId}}, 0))
  ```
- **Example:** 
  For the step with `WorkflowStepId` "risk-assessment", the `IsStepOfTitle` is "Production Deployment Workflow".

#### IsStepOfDescription
- **Description:** Retrieves the description of the workflow that this step is part of.
- **Calculation Method:** 
  - Similar to `IsStepOfTitle`, but retrieves the description instead.
- **Formula:** 
  ```plaintext
  =INDEX(Workflows!{{Description}}, MATCH(WorkflowSteps!{{IsStepOf}}, Workflows!{{WorkflowId}}, 0))
  ```
- **Example:** 
  For the step with `WorkflowStepId` "legal-review", the `IsStepOfDescription` is "End-to-end workflow for deploying software releases to production, including risk analysis, legal clearance, and release approval."

#### IsStepOfIdentifier
- **Description:** Retrieves the identifier of the workflow that this step is part of.
- **Calculation Method:** 
  - Similar to the previous lookups, but retrieves the identifier.
- **Formula:** 
  ```plaintext
  =INDEX(Workflows!{{Identifier}}, MATCH(WorkflowSteps!{{IsStepOf}}, Workflows!{{WorkflowId}}, 0))
  ```
- **Example:** 
  For the step with `WorkflowStepId` "release-approval", the `IsStepOfIdentifier` is "WF-PROD-001".

#### AssignedRoleLabel
- **Description:** Retrieves the label of the role assigned to this workflow step.
- **Calculation Method:** 
  - Use `INDEX` and `MATCH` to find the label in the `Roles` table where the `RoleId` matches the `AssignedRole`.
- **Formula:** 
  ```plaintext
  =INDEX(Roles!{{Label}}, MATCH(WorkflowSteps!{{AssignedRole}}, Roles!{{RoleId}}, 0))
  ```
- **Example:** 
  For the step with `AssignedRole` "risk-analyst", the `AssignedRoleLabel` is "Risk Analyst".

#### AssignedRoleComment
- **Description:** Retrieves the comment associated with the assigned role.
- **Calculation Method:** 
  - Similar to `AssignedRoleLabel`, but retrieves the comment.
- **Formula:** 
  ```plaintext
  =INDEX(Roles!{{Comment}}, MATCH(WorkflowSteps!{{AssignedRole}}, Roles!{{RoleId}}, 0))
  ```
- **Example:** 
  For the step with `AssignedRole` "legal-compliance-reviewer", the `AssignedRoleComment` is "Role responsible for legal and compliance review of releases."

#### AssignedRoleFilledBy
- **Description:** Retrieves the identifier of the human agent assigned to the role.
- **Calculation Method:** 
  - Similar to the previous lookups, but retrieves the `FilledBy` field.
- **Formula:** 
  ```plaintext
  =INDEX(Roles!{{FilledBy}}, MATCH(WorkflowSteps!{{AssignedRole}}, Roles!{{RoleId}}, 0))
  ```
- **Example:** 
  For the step with `AssignedRole` "release-manager", the `AssignedRoleFilledBy` is "maria-gonzalez".

## Roles

### Input Fields
1. **RoleId**
   - **Type:** string
   - **Description:** Unique identifier for the role.

2. **Label**
   - **Type:** string
   - **Description:** Label for the role.

3. **Comment**
   - **Type:** string
   - **Description:** Comment describing the role.

4. **FilledBy**
   - **Type:** string
   - **Description:** Identifier for the human agent filling this role.

### Calculated Fields
#### CountOfWorkflowSteps
- **Description:** Counts the number of workflow steps assigned to this role.
- **Calculation Method:** 
  - Use `COUNTIFS` to count the number of entries in the `WorkflowSteps` table where the `AssignedRole` matches the `RoleId`.
- **Formula:** 
  ```plaintext
  =COUNTIFS(WorkflowSteps!{{AssignedRole}}, Roles!{{RoleId}})
  ```
- **Example:** 
  For the role with `RoleId` "release-manager", the `CountOfWorkflowSteps` is 1, as there is one workflow step ("release-approval") assigned to this role.

#### FilledByName
- **Description:** Retrieves the name of the human agent filling this role.
- **Calculation Method:** 
  - Use `INDEX` and `MATCH` to find the name in the `HumanAgents` table where the `HumanAgentId` matches the `FilledBy` field.
- **Formula:** 
  ```plaintext
  =INDEX(HumanAgents!{{Name}}, MATCH(Roles!{{FilledBy}}, HumanAgents!{{HumanAgentId}}, 0))
  ```
- **Example:** 
  For the role with `FilledBy` "maria-gonzalez", the `FilledByName` is "Maria Gonzalez".

#### FilledByMBox
- **Description:** Retrieves the email address of the human agent filling this role.
- **Calculation Method:** 
  - Similar to `FilledByName`, but retrieves the `Mbox` field.
- **Formula:** 
  ```plaintext
  =INDEX(HumanAgents!{{Mbox}}, MATCH(Roles!{{FilledBy}}, HumanAgents!{{HumanAgentId}}, 0))
  ```
- **Example:** 
  For the role with `FilledBy` "maria-gonzalez", the `FilledByMBox` is "maria.gonzalez@specialsolutions.example".

## HumanAgents

### Input Fields
1. **HumanAgentId**
   - **Type:** string
   - **Description:** Unique identifier for the human agent.

2. **Name**
   - **Type:** string
   - **Description:** Name of the human agent.

3. **Mbox**
   - **Type:** string
   - **Description:** Email address of the human agent.

### Calculated Fields
#### CountOfRles
- **Description:** Counts the number of roles assigned to this human agent.
- **Calculation Method:** 
  - Use `COUNTIFS` to count the number of entries in the `Roles` table where the `FilledBy` field matches the `HumanAgentId`.
- **Formula:** 
  ```plaintext
  =COUNTIFS(Roles!{{FilledBy}}, HumanAgents!{{HumanAgentId}})
  ```
- **Example:** 
  For the human agent with `HumanAgentId` "maria-gonzalez", the `CountOfRles` is 1, as she fills the "release-manager" role.

This specification document provides a detailed guide on how to compute the calculated fields in the JTO - v3 rulebook, ensuring clarity and accuracy in deriving values from the defined inputs.