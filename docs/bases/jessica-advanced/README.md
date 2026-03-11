# Jessica Talisman's ADVANCED Ontology

**Extends BASIC with cross-entity lookups, conditional logic, and derived inferences.**

This base builds on the BASIC workflow ontology by adding business rules that span entity boundaries - demonstrating how the ERB platform handles more sophisticated calculations.

---

## What This Base Adds Over BASIC

### 1. Cross-Entity Lookups

WorkflowSteps now includes **lookup fields** that pull data from related entities:

```
AssignedRoleDepartment = INDEX(Roles!OwnedBy, MATCH(AssignedRole, Roles!RoleId, 0))
```

This gives each step direct access to which department owns its assigned role - without requiring a JOIN at query time.

```
ApprovalGateEscalationThresholdHours = INDEX(Approvals!EscalationThresholdHours, MATCH(ApprovalGate, Approvals!ApprovalId, 0))
```

This surfaces the escalation timeout directly on the step, enabling workflow engines to check timeouts without additional queries.

### 2. Conditional Logic (IF Formulas)

```
ExecutionActorType = IF(AssignedRoleDepartment = "HumanAgent", "HumanAgent",
                       IF(AssignedRoleDepartment = "AIAgent", "AIAgent",
                         IF(AssignedRoleDepartment = "AutomatedPipeline", "AutomatedPipeline", BLANK())))
```

This categorizes each step by execution actor type based on the department - demonstrating nested IF logic that compiles to equivalent CASE statements in SQL.

### 3. Renamed/Refined Entities

- `ApprovalGates` → `Approvals` (cleaner naming)
- `CountOfNonProposedSteps` → `CountOfSteps` (simplified)

---

## Generated SQL Differences

### Lookup Functions
```sql
CREATE OR REPLACE FUNCTION calc_workflow_steps_assigned_role_department(p_workflow_step_id TEXT)
RETURNS TEXT AS $$
BEGIN
  RETURN (
    SELECT owned_by::text FROM roles
    WHERE role_id = (
      SELECT assigned_role FROM workflow_steps
      WHERE workflow_step_id = p_workflow_step_id
    )
  );
END;
```

### Conditional Logic → CASE Expressions
```sql
CREATE OR REPLACE FUNCTION calc_workflow_steps_execution_actor_type(p_workflow_step_id TEXT)
RETURNS TEXT AS $$
BEGIN
  RETURN (
    CASE WHEN calc_workflow_steps_assigned_role_department(p_workflow_step_id) = 'HumanAgent'
         THEN 'HumanAgent'
    ELSE CASE WHEN calc_workflow_steps_assigned_role_department(p_workflow_step_id) = 'AIAgent'
         THEN 'AIAgent'
    ELSE CASE WHEN calc_workflow_steps_assigned_role_department(p_workflow_step_id) = 'AutomatedPipeline'
         THEN 'AutomatedPipeline'
    ELSE NULL END END END
  )::text;
END;
```

---

## Complexity Comparison

| Feature | BASIC | ADVANCED |
|---------|-------|----------|
| Tables | 9 | 9 |
| Calculated fields | 8 | 11 |
| Lookup fields | 0 | 2 |
| IF formulas | 0 | 1 |
| Cross-entity dependencies | Low | Medium |

---

## Why This Matters

The ADVANCED base demonstrates that:

1. **Lookups compile to subqueries** - The ERB platform translates INDEX/MATCH patterns to equivalent SQL subqueries, maintaining the same semantics across substrates.

2. **Conditional logic is portable** - IF/THEN/ELSE in the rulebook becomes CASE expressions in SQL, ternary operators in Python/Go, and IF() in Excel.

3. **Denormalization at the view layer** - By surfacing `AssignedRoleDepartment` on WorkflowSteps, application code doesn't need to JOIN through Roles → Departments.

---

## Potential Extensions

The ADVANCED base is a foundation for even richer business rules:

- **Validation rules**: `IsValid = AND(AssignedRole <> "", ApprovalGate <> "")`
- **Derived status**: `StepStatus = IF(RequiresHumanApproval AND NOT HasApproval, "Pending", "Ready")`
- **Aggregate inferences**: `WorkflowComplexityScore = CountOfSteps * AVG(EscalationThresholdHours)`
- **Temporal logic**: `IsOverdue = NOW() > DueDate + EscalationThresholdHours`

These patterns show how the same declarative approach scales to real enterprise workflow engines.

---

## Files in This Directory

- `effortless-rulebook.json` - Snapshot of the rulebook for this base
- `README.md` - This file

---

*Base ID: `appwN9EAp8IeIxM23`*
