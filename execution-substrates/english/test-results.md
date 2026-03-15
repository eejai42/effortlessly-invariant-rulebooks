# Test Results: english

## Summary

| Metric | Value |
|--------|-------|
| Total Fields Tested | 122 |
| Passed | 96 |
| Failed | 26 |
| Score | 78.7% |
| Duration | 3m 13s |

## Results by Entity

### roles

- Fields: 15/15 (100.0%)
- Computed columns: name

### workflow_steps

- Fields: 20/20 (100.0%)
- Computed columns: name

### workflows

- Fields: 19/45 (42.2%)
- Computed columns: name, count_of_non_proposed_steps, has_more_than1_step

| PK | Field | Expected | Actual |
|-----|-------|----------|--------|
| asset-management | count_of_non_proposed_steps | 1 | None |
| asset-management | has_more_than1_step | False | None |
| change-management | count_of_non_proposed_steps | 3 | None |
| change-management | has_more_than1_step | True | None |
| content-publishing | count_of_non_proposed_steps | 1 | None |
| content-publishing | has_more_than1_step | False | None |
| contract-review | count_of_non_proposed_steps | 1 | None |
| contract-review | has_more_than1_step | False | None |
| customer-feedback | count_of_non_proposed_steps | 1 | None |
| customer-feedback | has_more_than1_step | False | None |
| expense-reimbursement | count_of_non_proposed_steps | 1 | None |
| expense-reimbursement | has_more_than1_step | False | None |
| incident-reporting | count_of_non_proposed_steps | 1 | None |
| incident-reporting | has_more_than1_step | False | None |
| invoice-approval | count_of_non_proposed_steps | 1 | None |
| invoice-approval | has_more_than1_step | False | None |
| it-support | count_of_non_proposed_steps | 1 | None |
| it-support | has_more_than1_step | False | None |
| leave-request | count_of_non_proposed_steps | 1 | None |
| leave-request | has_more_than1_step | False | None |
| ... | ... | (6 more) | ... |

### precedes_steps

- Fields: 16/16 (100.0%)
- Computed columns: display_name

### departments

- Fields: 15/15 (100.0%)
- Computed columns: name

### approval_gates

- Fields: 11/11 (100.0%)
- Computed columns: name
