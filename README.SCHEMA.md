# Effortless Rulebook

### Generated from:

> This builds ssotme tools including those that are disabled which regenerates this file.

```
$ cd ./docs
$ ssotme -build -id
```


> Rulebook generated from Airtable base 'Jessica's Ontology Series-v3'.

**Model ID:** ``

---

## Formal Arguments

The following logical argument establishes that "language" can be formalized as a computable classification, and demonstrates that not everything qualifies as a language under this definition.


## Execution Substrates

The following formats have been evaluated as execution substrates for this rulebook.

See the `execution-substrates/` directory for available format implementations.

---

## Table Schemas

### Table: Workflows

> Table: Workflows

#### Schema

| Field | Type | Data Type | Nullable | Description |
|-------|------|-----------|----------|-------------|
| `WorkflowId` | raw | string | No | - |
| `Title` | raw | string | Yes | Human-readable name for the workflow. Maps to dct:title per Dublin Core. |
| `Description` | raw | string | Yes | Detailed description of the workflow purpose and scope. Maps to dct:description per Dublin Core. |
| `Created` | raw | datetime | Yes | Date the workflow was created. Maps to dct:created per Dublin Core. |
| `Modified` | raw | datetime | Yes | Date the workflow was last modified. Maps to dct:modified. Used to identify stale workflows per NTWF CQ5. |
| `Identifier` | raw | string | Yes | External reference identifier (e.g., ticket number). Maps to dct:identifier. Join key to operational systems. |
| `WorkflowSteps` | relationship | string | Yes | Steps contained in this workflow. Inverse of IsStepOf. Maps to ntwf:hasStep. |
| `CountOfWorkflowSteps` | aggregation | integer | Yes | Count of steps in this workflow. Aggregation over IsStepOf relationship. |

**Formula for `CountOfWorkflowSteps`:**
```
=COUNTIFS(WorkflowSteps!{{IsStepOf}}, Workflows!{{WorkflowId}})
```


#### Sample Data (1 records)

| Field | Value |
|-------|-------|
| `WorkflowId` | production-deployment-workflow |
| `Title` | Production Deployment Workflow |
| `Description` | End-to-end workflow for deploying software releases to production, including risk analysis, legal clearance, and release approval. From Jessica Talisman's NTWF ontology article. |
| `Created` | 2026-01-15 |
| `Modified` | 2026-01-15 |
| `Identifier` | WF-PROD-001 |
| `WorkflowSteps` | legal-review, risk-assessment, release-approval |
| `CountOfWorkflowSteps` | 3 |

---

### Table: WorkflowSteps

> Table: WorkflowSteps

#### Schema

| Field | Type | Data Type | Nullable | Description |
|-------|------|-----------|----------|-------------|
| `WorkflowStepId` | raw | string | No | - |
| `Label` | raw | string | Yes | Human-readable name for the step. Maps to rdfs:label. |
| `SequencePosition` | raw | integer | Yes | Ordinal position in workflow sequence. Maps to ntwf:sequencePosition (functional). Supports positional ordering queries. |
| `RequiresHumanApproval` | raw | boolean | Yes | Whether this step requires a human agent. Maps to ntwf:requiresHumanApproval. Answers NTWF CQ3. |
| `IsStepOf` | relationship | string | Yes | Parent workflow containing this step. Inverse of WorkflowSteps. Maps to ntwf:isStepOf. |
| `AssignedRole` | relationship | string | Yes | Role responsible for this step. Maps to ntwf:assignedRole (functional). Implements role-agent separation. |
| `IsStepOfTitle` | lookup | string | Yes | Denormalized lookup of parent workflow title. |
| `IsStepOfDescription` | lookup | string | Yes | Denormalized lookup of parent workflow description. |
| `IsStepOfIdentifier` | lookup | string | Yes | Denormalized lookup of parent workflow external identifier. |
| `AssignedRoleLabel` | lookup | string | Yes | Denormalized lookup of assigned role label. |
| `AssignedRoleComment` | lookup | string | Yes | Denormalized lookup of assigned role comment/description. |
| `AssignedRoleFilledBy` | lookup | string | Yes | Denormalized lookup of agent currently filling the assigned role. |
| `PrecedesSteps` | relationship | string | Yes | - |
| `ApprovalGate` | relationship | string | Yes | Approval gate attached to this step, if any. Establishes double-typing per article. |
| `StepDurationMinutes` | raw | integer | Yes | Expected duration of the step in minutes. Maps to ntwf:stepDurationMinutes. |
| `ProducesArtifact` | relationship | string | Yes | Artifact produced by this step. Maps to ntwf:producesArtifact. Aligned with prov:generated. |
| `RequiresArtifact` | raw | string | Yes | Artifact required as input to this step. Maps to ntwf:requiresArtifact. Aligned with prov:used. |
| `ConsumesDataset` | relationship | string | Yes | Dataset consumed by this step. Maps to ntwf:consumesDataset. Answers NTWF CQ8. |

**Formula for `IsStepOfTitle`:**
```
=INDEX(Workflows!{{Title}}, MATCH(WorkflowSteps!{{IsStepOf}}, Workflows!{{WorkflowId}}, 0))
```

**Formula for `IsStepOfDescription`:**
```
=INDEX(Workflows!{{Description}}, MATCH(WorkflowSteps!{{IsStepOf}}, Workflows!{{WorkflowId}}, 0))
```

**Formula for `IsStepOfIdentifier`:**
```
=INDEX(Workflows!{{Identifier}}, MATCH(WorkflowSteps!{{IsStepOf}}, Workflows!{{WorkflowId}}, 0))
```

**Formula for `AssignedRoleLabel`:**
```
=INDEX(Roles!{{Label}}, MATCH(WorkflowSteps!{{AssignedRole}}, Roles!{{RoleId}}, 0))
```

**Formula for `AssignedRoleComment`:**
```
=INDEX(Roles!{{Comment}}, MATCH(WorkflowSteps!{{AssignedRole}}, Roles!{{RoleId}}, 0))
```

**Formula for `AssignedRoleFilledBy`:**
```
=INDEX(Roles!{{FilledBy}}, MATCH(WorkflowSteps!{{AssignedRole}}, Roles!{{RoleId}}, 0))
```


#### Sample Data (3 records)

| Field | Value |
|-------|-------|
| `WorkflowStepId` | risk-assessment |
| `Label` | Risk Assessment |
| `SequencePosition` | 1 |
| `IsStepOf` | production-deployment-workflow |
| `AssignedRole` | risk-analyst |
| `IsStepOfTitle` | Production Deployment Workflow |
| `IsStepOfDescription` | End-to-end workflow for deploying software releases to production, including risk analysis, legal clearance, and release approval. From Jessica Talisman's NTWF ontology article. |
| `IsStepOfIdentifier` | WF-PROD-001 |
| `AssignedRoleLabel` | Risk Analyst |
| `AssignedRoleComment` | Role responsible for risk assessment. In full ontology, filled by AI agent. |
| `PrecedesSteps` | step-1-to-2 |
| `ProducesArtifact` | risk-report |
| `RequiresHumanApproval` | false |
| `AssignedRoleFilledBy` |  |
| `ApprovalGate` |  |
| `StepDurationMinutes` | 0 |
| `RequiresArtifact` |  |
| `ConsumesDataset` |  |

---

### Table: ApprovalGates

> Table: ApprovalGates

#### Schema

| Field | Type | Data Type | Nullable | Description |
|-------|------|-----------|----------|-------------|
| `ApprovalGateId` | raw | string | No | - |
| `Name` | raw | string | Yes | Display name of the approval gate. Maps to rdfs:label. |
| `Description` | raw | string | Yes | Description of what this gate approves and its criteria. |
| `WorkflowStep` | relationship | string | Yes | The workflow step that this gate is attached to. Establishes double-typing. |
| `EscalationThresholdHours` | raw | integer | Yes | Hours that may elapse before delegation chain activates. Maps to ntwf:escalationThresholdHours. |


#### Sample Data (2 records)

| Field | Value |
|-------|-------|
| `ApprovalGateId` | release-approval-gate |
| `Name` | Release Approval Gate |
| `Description` | Final approval gate before production deployment. Requires Release Manager sign-off. Step 3 in the Production Deployment Workflow. When approval is pending beyond threshold, escalates via delegation chain: Release Manager -> VP Engineering -> CTO. |
| `EscalationThresholdHours` | 24 |
| `WorkflowStep` |  |

---

### Table: Roles

> Table: Roles

#### Schema

| Field | Type | Data Type | Nullable | Description |
|-------|------|-----------|----------|-------------|
| `RoleId` | raw | string | No | - |
| `Label` | raw | string | Yes | Human-readable name for the role. Maps to rdfs:label. |
| `Comment` | raw | string | Yes | Description of the role's responsibilities. Maps to rdfs:comment. |
| `Department` | relationship | string | Yes | Department that owns this role. Maps to org:memberOf. |
| `FilledBy` | relationship | string | Yes | Agent currently filling this role. Maps to ntwf:filledBy. The change-management triple - update this when personnel change. |
| `WorkflowSteps` | relationship | string | Yes | Steps assigned to this role. Inverse of AssignedRole. |
| `CountOfWorkflowSteps` | aggregation | integer | Yes | Count of workflow steps assigned to this role. |
| `DelegatesTo` | relationship | string | Yes | Role to escalate to when this role's agent is unavailable. Maps to ntwf:delegatesTo. Enables delegation chain queries. |
| `DelegatesToLabel` | lookup | string | Yes | - |
| `FilledByName` | lookup | string | Yes | Denormalized lookup of agent name (foaf:name) filling this role. |
| `FilledByMBox` | lookup | string | Yes | Denormalized lookup of agent email (foaf:mbox) filling this role. |
| `DelegatedToBy` | relationship | string | Yes | Inverse of DelegatesTo. Role that delegates to this role. |

**Formula for `CountOfWorkflowSteps`:**
```
=COUNTIFS(WorkflowSteps!{{AssignedRole}}, Roles!{{RoleId}})
```

**Formula for `DelegatesToLabel`:**
```
=INDEX(Roles!{{Label}}, MATCH(Roles!{{DelegatesTo}}, Roles!{{RoleId}}, 0))
```

**Formula for `FilledByName`:**
```
=INDEX(Agents!{{Name}}, MATCH(Roles!{{FilledBy}}, Agents!{{AgentId}}, 0))
```

**Formula for `FilledByMBox`:**
```
=INDEX(Agents!{{Mbox}}, MATCH(Roles!{{FilledBy}}, Agents!{{AgentId}}, 0))
```


#### Sample Data (5 records)

| Field | Value |
|-------|-------|
| `RoleId` | release-manager |
| `Label` | Release Manager |
| `Comment` | Primary role responsible for coordinating production releases. First in delegation chain. Article CQ2: 'filled by Maria Gonzalez' |
| `FilledBy` | maria-gonzalez |
| `WorkflowSteps` | release-approval |
| `FilledByName` | Maria Gonzalez |
| `FilledByMBox` | maria.gonzalez@specialsolutions.example |
| `CountOfWorkflowSteps` | 1 |
| `DelegatesTo` | vp-engineering |
| `DelegatesToLabel` | VP Engineering |
| `Department` |  |
| `DelegatedToBy` |  |

---

### Table: Agents

> Table: Agents

#### Schema

| Field | Type | Data Type | Nullable | Description |
|-------|------|-----------|----------|-------------|
| `AgentId` | raw | string | No | - |
| `Name` | raw | string | Yes | Full name of the person. Maps to foaf:name per FOAF ontology. |
| `TypeOfAgent` | relationship | string | Yes | Agent type classification: human, ai, or automatedpipeline. Determines which NTWF subclass applies. |
| `Roles` | relationship | string | Yes | Roles filled by this agent. Inverse of FilledBy. |
| `Description` | raw | string | Yes | Description of the agent's purpose and capabilities. |
| `ModelVersion` | raw | string | Yes | AI model version string. Maps to ntwf:modelVersion. Only applicable to AIAgent type. Domain declaration means applying this to a HumanAgent would incorrectly infer AIAgent type. |
| `Mbox` | raw | string | Yes | Email address of the person. Maps to foaf:mbox per FOAF ontology. Used for contact and identity resolution. |
| `CountOfRoles` | aggregation | integer | Yes | Count of roles currently filled by this agent. |
| `ProducedArtifacts` | relationship | string | Yes | Artifacts attributed to this agent. Maps to inverse of prov:wasAttributedTo. |
| `Datasets` | relationship | string | Yes | - |
| `Artifacts` | relationship | string | Yes | - |
| `ProcessedDatasets` | raw | string | Yes | Datasets processed by this agent (for AI agents). Inverse of ProcessedBy. |

**Formula for `CountOfRoles`:**
```
=COUNTIFS(Roles!{{FilledBy}}, Agents!{{AgentId}})
```


#### Sample Data (4 records)

| Field | Value |
|-------|-------|
| `AgentId` | maria-gonzalez |
| `Name` | Maria Gonzalez |
| `Mbox` | maria.gonzalez@specialsolutions.example |
| `Roles` | release-manager |
| `CountOfRoles` | 1 |
| `TypeOfAgent` | human |
| `Description` | Human Release Manager |
| `ProducedArtifacts` | risk-report |
| `ModelVersion` |  |
| `Datasets` |  |
| `Artifacts` |  |
| `ProcessedDatasets` |  |

---

### Table: Artifacts

> Table: Artifacts

#### Schema

| Field | Type | Data Type | Nullable | Description |
|-------|------|-----------|----------|-------------|
| `ArtifactId` | raw | string | No | - |
| `Name` | raw | string | Yes | Display name of the artifact. Maps to rdfs:label. |
| `Description` | raw | string | Yes | Description of the artifact's content and purpose. |
| `ProducedBy` | relationship | string | Yes | Workflow step that produces this artifact. Maps to ntwf:producedBy. |
| `GeneratedBy` | relationship | string | Yes | Workflow step that produced this artifact. Maps to prov:wasGeneratedBy. |
| `AttributedTo` | relationship | string | Yes | Agent responsible for producing this artifact. Maps to prov:wasAttributedTo. |
| `DerivedFrom` | relationship | string | Yes | Upstream artifact this was derived from. Maps to prov:wasDerivedFrom. Forms provenance chain. |
| `DerivedArtifacts` | relationship | string | Yes | - |
| `SequencePosition` | raw | integer | Yes | Position in the artifact provenance chain. |
| `Title` | raw | string | Yes | Display name of the artifact. Maps to dct:title. |
| `Identifier` | raw | string | Yes | External reference identifier (document ID, ticket number). Maps to dct:identifier. Join key to document management system. |
| `Created` | raw | datetime | Yes | Date the artifact was created. Maps to dct:created. |


#### Sample Data (5 records)

| Field | Value |
|-------|-------|
| `ArtifactId` | risk-report |
| `Name` | Risk Report |
| `Description` | Automated risk assessment output produced by the RiskAnalysis-AI agent. First artifact in the provenance chain. |
| `SequencePosition` | 1 |
| `Title` | Risk Report |
| `Identifier` | DOC-RISK-2026-001 |
| `Created` | 2026-01-15T00:00:00Z |
| `GeneratedBy` | risk-assessment |
| `ProducedBy` | maria-gonzalez |
| `AttributedTo` |  |
| `DerivedFrom` |  |
| `DerivedArtifacts` |  |

---

### Table: Datasets

> Table: Datasets

#### Schema

| Field | Type | Data Type | Nullable | Description |
|-------|------|-----------|----------|-------------|
| `DatasetId` | raw | string | No | - |
| `Name` | raw | string | Yes | Display name of the dataset. Maps to dct:title. |
| `Description` | raw | string | Yes | Description of the dataset's content and source. |
| `ProcessedBy` | relationship | string | Yes | AI agent that processes this dataset. Inverse of ProcessesDatasets. |
| `Publisher` | relationship | string | Yes | Department that publishes/owns this dataset. Maps to dct:publisher. |
| `ConsumedByStep` | relationship | string | Yes | Workflow step(s) that consume this dataset. Inverse of ConsumesDataset. |
| `TimePeriod` | raw | string | Yes | Time period the dataset covers (e.g., 'Q1 2026'). |
| `Title` | raw | string | Yes | Display name of the dataset. Maps to dct:title. |
| `Modified` | raw | datetime | Yes | Date the dataset was last modified. Maps to dct:modified. |


#### Sample Data (4 records)

| Field | Value |
|-------|-------|
| `DatasetId` | dataset-risk-metrics-q1 |
| `Name` | dataset-risk-metrics-q1 |
| `Description` | Quarterly risk metrics dataset containing historical deployment data, incident reports, and risk indicators. Processed by RiskAnalysis-AI to produce Risk Report. Article CQ8 answer. |
| `TimePeriod` | Q1 2026 |
| `Title` | Q1 2026 Risk Metrics |
| `Modified` | 2026-01-10T00:00:00Z |
| `ProcessedBy` |  |
| `Publisher` |  |
| `ConsumedByStep` |  |

---

### Table: Departments

> Table: Departments

#### Schema

| Field | Type | Data Type | Nullable | Description |
|-------|------|-----------|----------|-------------|
| `DepartmentId` | raw | string | No | - |
| `Name` | raw | string | Yes | Human-readable name of the department. Maps to rdfs:label. |
| `Description` | raw | string | Yes | Description of the department's function and responsibilities. |
| `Roles` | relationship | string | Yes | Roles owned by this department. Inverse of Department on Roles. |
| `PublishedDatasets` | relationship | string | Yes | Datasets published by this department. Inverse of Publisher. |


#### Sample Data (3 records)

| Field | Value |
|-------|-------|
| `DepartmentId` | engineering |
| `Name` | Engineering |
| `Description` | Software engineering: development, deployment, technical operations. Owns Release Manager, VP Engineering, CTO, Risk Analyst, Deployment Engineer, Data Engineer roles. |
| `Roles` |  |
| `PublishedDatasets` |  |

---

### Table: TypesOfAgents

> Table: TypesOfAgents

#### Schema

| Field | Type | Data Type | Nullable | Description |
|-------|------|-----------|----------|-------------|
| `TypesOfAgentId` | raw | string | No | - |
| `Name` | raw | string | Yes | Display name of the AI agent. Maps to schema:name. |
| `Description` | raw | string | Yes | Description of the AI agent's purpose and capabilities. |
| `Agents` | relationship | string | Yes | Agents of this type. Inverse of TypeOfAgent. |
| `OntologyClass` | raw | string | Yes | Corresponding NTWF/external ontology class. |
| `Superclasses` | raw | string | Yes | Parent classes in ontology hierarchy. |
| `CountOfAgents` | aggregation | integer | Yes | - |

**Formula for `CountOfAgents`:**
```
=COUNTIFS(Agents!{{TypeOfAgent}}, TypesOfAgents!{{TypesOfAgentId}})
```


#### Sample Data (3 records)

| Field | Value |
|-------|-------|
| `TypesOfAgentId` | human |
| `Name` | Human |
| `Description` | AI agent responsible for automated risk assessment. Processes Q1 2026 Risk Metrics dataset and produces Risk Report artifact. Article CQ8 demonstrates this agent's dataset processing. |
| `Agents` | maria-gonzalez, james-okafor |
| `OntologyClass` | ntwf:HumanAgent |
| `Superclasses` | foaf:Person, prov:Agent |
| `CountOfAgents` | 2 |

---

### Table: PrecedesSteps

> Table: PrecedesSteps

#### Schema

| Field | Type | Data Type | Nullable | Description |
|-------|------|-----------|----------|-------------|
| `PrecedesStepId` | raw | string | No | - |
| `Name` | raw | string | Yes | - |
| `FromStep` | relationship | string | Yes | The step that comes BEFORE (source of the precedes edge). |
| `ToStep` | relationship | string | Yes | The step that comes AFTER (target of the precedes edge). |


#### Sample Data (3 records)

| Field | Value |
|-------|-------|
| `PrecedesStepId` | step-1-to-2 |
| `Name` | step-1-to-2 |
| `FromStep` | risk-assessment |
| `ToStep` | legal-review |

---


## Metadata

**Summary:** Airtable export with schema-first type mapping: Schemas, Data, Relationships (FK links), Lookups (INDEX/MATCH), Aggregations (SUMIFS/COUNTIFS/Rollups), and Calculated fields (formulas) in Excel dialect. Field types are determined from Airtable's schema metadata FIRST (no coercion), with intelligent fallback to formula/data analysis only when schema is unavailable.

### Conversion Details

| Property | Value |
|----------|-------|
| Source Base ID | `app6afUqa0zBTiMzM` |
| Table Count | 10 |
| Tool Version | 2.0.0 |
| Export Mode | schema_first_type_mapping |
| Field Type Mapping | checkbox→boolean, number→number/integer, multipleRecordLinks→relationship, multipleLookupValues→lookup, rollup→aggregation, count→aggregation, formula→calculated |

### Type Inference

- **Enabled:** true
- **Priority:** airtable_metadata (NO COERCION) → formula_analysis → reference_resolution → data_analysis (fallback only)
- **Airtable Type Mapping:** checkbox→boolean, singleLineText→string, multilineText→string, number→number/integer, datetime→datetime, singleSelect→string, email→string, url→string, phoneNumber→string
- **Data Coercion Hierarchy:** Only used as fallback when Airtable schema unavailable: datetime → number → integer → boolean → base64 → json → string
- **Nullable Support:** true
- **Error Value Handling:** #NUM!, #ERROR!, #N/A, #REF!, #DIV/0!, #VALUE!, #NAME? are treated as NULL

---

*Generated from effortless-rulebook.json*

