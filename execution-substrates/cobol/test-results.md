# Test Results: cobol

## Summary

| Metric | Value |
|--------|-------|
| Total Fields Tested | 3 |
| Passed | 1 |
| Failed | 2 |
| Score | 33.3% |
| Duration | < 1s |

## Results by Entity

### workflows

- Fields: 1/3 (33.3%)
- Computed columns: name, count_of_steps, has_more_than1_step

| PK | Field | Expected | Actual |
|-----|-------|----------|--------|
| production-deployment | count_of_steps | 5 | 0 |
| production-deployment | has_more_than1_step | True | False |
