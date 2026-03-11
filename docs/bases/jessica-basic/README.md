# Jessica Talisman's BASIC Ontology

**A 9-table workflow model demonstrating relationships, aggregations, and role-based access patterns.**

This base is inspired by [Jessica Talisman's ontology modeling series](https://jessicatalisman.medium.com/), which explores how to model organizational workflows with proper separation between roles and agents.

---

## What This Base Demonstrates

- **9 interconnected tables** with foreign key relationships
- **Aggregations**: `COUNTIFS` to count related records
- **Boolean derivations**: `HasMoreThan1Step = CountOfNonProposedSteps > 1`
- **Role-agent separation**: Steps assign to Roles, not directly to people/AI
- **Delegation chains**: Roles can delegate to other roles for escalation
- **Multiple agent types**: HumanAgents, AIAgents, AutomatedPipelines

---

## Entity Model

```
Workflows
    └── WorkflowSteps (many)
            ├── AssignedRole → Roles
            ├── ApprovalGate → ApprovalGates
            └── PrecededBySteps → PrecedesSteps

Roles
    ├── FilledByHumanAgent → HumanAgents
    ├── FilledByAIAgent → AIAgents
    ├── FilledByAutomatedPipeline → AutomatedPipelines
    ├── OwnedBy → Departments
    └── DelegatesTo → Roles (self-reference)

Departments
    └── Roles (back-reference)
```

---

## Tables Overview

| Table | Records | Key Fields | Calculated Fields |
|-------|---------|------------|-------------------|
| **Workflows** | 15 | Title, Description, Identifier | `Name` (slug), `CountOfNonProposedSteps`, `HasMoreThan1Step` |
| **WorkflowSteps** | 20 | SequencePosition, RequiresHumanApproval | `Name` (slug) |
| **ApprovalGates** | 11 | EscalationThresholdHours | `Name` (slug) |
| **PrecedesSteps** | 16 | StepNumber | `DisplayName` ("Step-N") |
| **Roles** | 15 | Label, Comment | `Name` (lowercase) |
| **Departments** | 15 | Title | `Name` (slug) |
| **HumanAgents** | 15 | DisplayName, Mbox | - |
| **AIAgents** | 15 | ModelVersion, Title | - |
| **AutomatedPipelines** | 15 | Description | - |

---

## Key Formulas

### Slug Generation (used across multiple tables)
```
=SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")
```
Generates: "Performance Review" → "performance-review"

### Step Count Aggregation
```
=COUNTIFS(WorkflowSteps!{{Workflow}}, Workflows!{{WorkflowId}})
```
Counts how many steps belong to each workflow.

### Boolean Derivation
```
={{CountOfNonProposedSteps}} > 1
```
True if workflow has more than one step (enables filtering complex workflows).

### Concatenation
```
="Step-" & {{StepNumber}}
```
Generates display names like "Step-1", "Step-2", etc.

---

## Generated SQL

The rulebook generates 30+ PostgreSQL functions:

### Calculated Fields (`calc_*`)
```sql
CREATE OR REPLACE FUNCTION calc_workflows_name(p_workflow_id TEXT)
RETURNS TEXT AS $$
BEGIN
  RETURN REPLACE(LOWER(display_name), ' ', '-');
END;

CREATE OR REPLACE FUNCTION calc_workflows_count_of_non_proposed_steps(p_workflow_id TEXT)
RETURNS INTEGER AS $$
BEGIN
  RETURN (SELECT COUNT(*) FROM workflow_steps WHERE workflow = p_workflow_id);
END;

CREATE OR REPLACE FUNCTION calc_workflows_has_more_than1_step(p_workflow_id TEXT)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN calc_workflows_count_of_non_proposed_steps(p_workflow_id) > 1;
END;
```

### Relationship Aggregations
```sql
CREATE OR REPLACE FUNCTION calc_workflows_workflow_steps(p_workflow_id TEXT)
RETURNS TEXT AS $$
BEGIN
  RETURN (
    SELECT STRING_AGG(workflow_step_id::TEXT, ', ' ORDER BY workflow_step_id)
    FROM workflow_steps
    WHERE workflow = p_workflow_id
  );
END;
```

### Views (10 total)
```sql
CREATE OR REPLACE VIEW vw_workflows AS
SELECT
  t.workflow_id,
  calc_workflows_name(t.workflow_id) AS name,
  t.display_name,
  t.title,
  t.description,
  calc_workflows_workflow_steps(t.workflow_id) AS workflow_steps,
  calc_workflows_count_of_non_proposed_steps(t.workflow_id) AS count_of_non_proposed_steps,
  calc_workflows_has_more_than1_step(t.workflow_id) AS has_more_than1_step
FROM workflows t;
```

---

## Design Patterns Demonstrated

### 1. Role-Agent Separation (Heuristic 2)
Steps point to **Roles**, not directly to agents. This allows:
- Same workflow to work with different agent assignments
- Easy reassignment when people change roles
- Clear audit trail of "who filled what role"

### 2. Delegation Chains
`Roles.DelegatesTo` creates escalation paths:
```
Editor → Administrator (when editor unavailable)
Viewer → Editor → Administrator
```

### 3. Multiple Agent Types
A single Role can be filled by:
- `HumanAgent` (person)
- `AIAgent` (LLM-based)
- `AutomatedPipeline` (deterministic script)

This enables answering: "Which steps require human decisions vs. AI execution?"

### 4. Approval Gates
Steps can reference ApprovalGates with `EscalationThresholdHours` to trigger delegation chains after timeout.

---

## Complexity Comparison

| Metric | CustomerDemo | Jessica BASIC |
|--------|--------------|---------------|
| Tables | 1 | 9 |
| Relationships | 0 | 12 |
| Calculated fields | 1 | 8 |
| Aggregations | 0 | 4 |
| Generated functions | 1 | 30+ |
| Generated views | 1 | 10 |

---

## Why This Base Matters

This is a **real-world workflow ontology** that could power:
- Approval routing systems
- Org chart / RBAC implementations
- Audit logging with role-based attribution
- AI agent orchestration with human-in-the-loop gates

The ERB platform proves that all of this complexity compiles to equivalent implementations across Python, Go, SQL, Excel, and OWL - verified by conformance testing.

---

## Next Steps

- **ADVANCED**: Adds more business rules and inferences on top of this structure
- **is-everything-a-language**: Meta-ontology exploring representation itself

---

## Files in This Directory

- `effortless-rulebook.json` - Snapshot of the rulebook for this base
- `README.md` - This file

---

*Base ID: `applThn0rikpCR9C3`*
