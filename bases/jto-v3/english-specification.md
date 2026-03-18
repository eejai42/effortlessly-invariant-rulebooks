# Specification Document for Jessica Talismans Special Solutions v1 Rulebook

## Overview
This document provides a detailed specification for the rulebook "Jessica Talismans Special Solutions v1," which outlines workflows, workflow steps, roles, agents, artifacts, and datasets. The rulebook includes calculated fields that derive values based on the relationships and data defined within the schema. This specification will guide users on how to compute these calculated fields accurately.

## Entities with Calculated Fields

### 1. Workflows

#### Input Fields
- **WorkflowId** (string): Unique identifier for the workflow.
- **WorkflowSteps** (string): Steps contained in this workflow, represented as a relationship to the WorkflowSteps entity.

#### Calculated Field
- **CountOfWorkflowSteps** (integer): 
  - **Description**: This field counts the number of steps associated with a particular workflow.
  - **Computation**: To compute this value, count the number of entries in the WorkflowSteps entity where the `IsStepOf` field matches the `WorkflowId` of the current workflow.
  - **Formula**: `=COUNTIFS(WorkflowSteps!{{IsStepOf}}, Workflows!{{WorkflowId}})`
  - **Example**: For the workflow with `WorkflowId` "production-deployment-workflow", there are three steps ("legal-review", "risk-assessment", "release-approval"). Thus, `CountOfWorkflowSteps` would be 3.

### 2. WorkflowSteps

#### Input Fields
- **WorkflowStepId** (string): Unique identifier for the workflow step.
- **IsStepOf** (string): The parent workflow containing this step, represented as a relationship to the Workflows entity.

#### Calculated Fields
- **IsStepOfTitle** (string):
  - **Description**: This field provides the title of the parent workflow for the current step.
  - **Computation**: Use the `MATCH` function to find the position of the `IsStepOf` value in the Workflow entity and then retrieve the corresponding `Title`.
  - **Formula**: `=INDEX(Workflows!{{Title}}, MATCH(WorkflowSteps!{{IsStepOf}}, Workflows!{{WorkflowId}}, 0))`
  - **Example**: For the step with `WorkflowStepId` "risk-assessment", the `IsStepOf` is "production-deployment-workflow". The title retrieved would be "Production Deployment Workflow".

- **IsStepOfDescription** (string):
  - **Description**: This field provides the description of the parent workflow for the current step.
  - **Computation**: Similar to `IsStepOfTitle`, use the `MATCH` function to find the position of the `IsStepOf` value and retrieve the corresponding `Description`.
  - **Formula**: `=INDEX(Workflows!{{Description}}, MATCH(WorkflowSteps!{{IsStepOf}}, Workflows!{{WorkflowId}}, 0))`
  - **Example**: For the step "legal-review", the description retrieved would be "End-to-end workflow for deploying software releases to production, including risk analysis, legal clearance, and release approval."

- **IsStepOfIdentifier** (string):
  - **Description**: This field provides the external identifier of the parent workflow for the current step.
  - **Computation**: Use the `MATCH` function to find the position of the `IsStepOf` value and retrieve the corresponding `Identifier`.
  - **Formula**: `=INDEX(Workflows!{{Identifier}}, MATCH(WorkflowSteps!{{IsStepOf}}, Workflows!{{WorkflowId}}, 0))`
  - **Example**: For the step "release-approval", the identifier retrieved would be "WF-PROD-001".

- **AssignedRoleLabel** (string):
  - **Description**: This field provides the label of the assigned role for the current step.
  - **Computation**: Use the `MATCH` function to find the position of the `AssignedRole` value in the Roles entity and retrieve the corresponding `Label`.
  - **Formula**: `=INDEX(Roles!{{Label}}, MATCH(WorkflowSteps!{{AssignedRole}}, Roles!{{RoleId}}, 0))`
  - **Example**: For the step "risk-assessment", the assigned role label would be "Risk Analyst".

- **AssignedRoleComment** (string):
  - **Description**: This field provides the comment or description of the assigned role for the current step.
  - **Computation**: Similar to `AssignedRoleLabel`, use the `MATCH` function to find the position of the `AssignedRole` value and retrieve the corresponding `Comment`.
  - **Formula**: `=INDEX(Roles!{{Comment}}, MATCH(WorkflowSteps!{{AssignedRole}}, Roles!{{RoleId}}, 0))`
  - **Example**: For the step "legal-review", the comment retrieved would be "Role responsible for legal and compliance review of releases."

- **AssignedRoleFilledBy** (string):
  - **Description**: This field provides the agent currently filling the assigned role for the current step.
  - **Computation**: Use the `MATCH` function to find the position of the `AssignedRole` value in the Roles entity and retrieve the corresponding `FilledBy`.
  - **Formula**: `=INDEX(Roles!{{FilledBy}}, MATCH(WorkflowSteps!{{AssignedRole}}, Roles!{{RoleId}}, 0))`
  - **Example**: For the step "release-approval", the filled by value would be "maria-gonzalez".

### 3. Roles

#### Input Fields
- **RoleId** (string): Unique identifier for the role.
- **FilledBy** (string): Agent currently filling this role, represented as a relationship to the Agents entity.

#### Calculated Field
- **CountOfWorkflowSteps** (integer):
  - **Description**: This field counts the number of workflow steps assigned to a particular role.
  - **Computation**: To compute this value, count the number of entries in the WorkflowSteps entity where the `AssignedRole` field matches the `RoleId` of the current role.
  - **Formula**: `=COUNTIFS(WorkflowSteps!{{AssignedRole}}, Roles!{{RoleId}})`
  - **Example**: For the role "release-manager", there is one step assigned ("release-approval"), so `CountOfWorkflowSteps` would be 1.

### 4. Agents

#### Input Fields
- **AgentId** (string): Unique identifier for the agent.
- **Roles** (string): Roles filled by this agent, represented as a relationship to the Roles entity.

#### Calculated Field
- **CountOfRoles** (integer):
  - **Description**: This field counts the number of roles currently filled by this agent.
  - **Computation**: To compute this value, count the number of entries in the Roles entity where the `FilledBy` field matches the `AgentId` of the current agent.
  - **Formula**: `=COUNTIFS(Roles!{{FilledBy}}, Agents!{{AgentId}})`
  - **Example**: For the agent "maria-gonzalez", there is one role filled ("release-manager"), so `CountOfRoles` would be 1.

### 5. TypesOfAgents

#### Input Fields
- **TypesOfAgentId** (string): Unique identifier for the type of agent.

#### Calculated Field
- **CountOfAgents** (integer):
  - **Description**: This field counts the number of agents of a specific type.
  - **Computation**: To compute this value, count the number of entries in the Agents entity where the `TypeOfAgent` field matches the `TypesOfAgentId` of the current type.
  - **Formula**: `=COUNTIFS(Agents!{{TypeOfAgent}}, TypesOfAgents!{{TypesOfAgentId}})`
  - **Example**: For the type "human", there are two agents ("maria-gonzalez" and "james-okafor"), so `CountOfAgents` would be 2.

## Conclusion
This specification document outlines the necessary steps to compute the calculated fields within the "Jessica Talismans Special Solutions v1" rulebook. By following the provided instructions and examples, users can accurately derive the values without needing to reference the original formulas.