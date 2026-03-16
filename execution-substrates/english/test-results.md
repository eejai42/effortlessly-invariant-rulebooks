# Test Results: english

## Summary

| Metric | Value |
|--------|-------|
| Total Fields Tested | 27 |
| Passed | 11 |
| Failed | 16 |
| Score | 40.7% |
| Duration | 1m 23s |

## Results by Entity

### roles

- Fields: 1/6 (16.7%)
- Computed columns: name

| PK | Field | Expected | Actual |
|-----|-------|----------|--------|
| deployment-engineer | name | deployment engineer | deployment-engineer |
| legal-compliance-reviewer | name | legal compliance reviewer | legal-compliance-reviewer |
| release-manager | name | release manager | release-manager |
| risk-analysis-agent | name | risk analysis agent | risk-analysis-agent |
| vp-engineering | name | vp engineering | vp-engineering |

### workflow_steps

- Fields: 5/10 (50.0%)
- Computed columns: name, execution_actor_type

| PK | Field | Expected | Actual |
|-----|-------|----------|--------|
| deployment-execution | execution_actor_type |  | HumanAgent |
| legal-clearance | execution_actor_type |  | HumanAgent |
| post-deployment-review | execution_actor_type |  | HumanAgent |
| release-approval-gate | execution_actor_type |  | HumanAgent |
| risk-analysis | execution_actor_type |  | HumanAgent |

### workflows

- Fields: 2/3 (66.7%)
- Computed columns: name, count_of_steps, has_more_than1_step

| PK | Field | Expected | Actual |
|-----|-------|----------|--------|
| production-deployment | count_of_steps | 5 | None |

### precedes_steps

- Fields: 0/5 (0.0%)
- Computed columns: display_name

| PK | Field | Expected | Actual |
|-----|-------|----------|--------|
| step-1 | display_name | Step-32 | Legal Clearance |
| step-2 | display_name | Step-33 | Release Approval Gate |
| step-3 | display_name | Step-34 | Deployment Execution |
| step-4 | display_name | Step-35 | Post Deployment Review |
| step-5 | display_name | Step-36 | None |

### departments

- Fields: 2/2 (100.0%)
- Computed columns: name

### approvals

- Fields: 1/1 (100.0%)
- Computed columns: name
