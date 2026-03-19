# Test Results: cobol

## Summary

| Metric | Value |
|--------|-------|
| Total Fields Tested | 18 |
| Passed | 4 |
| Failed | 14 |
| Score | 22.2% |
| Duration | < 1s |

## Results by Entity

### shapes

- Fields: 4/18 (22.2%)
- Computed columns: how_many_sides, is_rectangle, is_triangle, is_right_triangle, sum_of_internal_angles, max_angle, hypotenuse_length_squared, non_hypotenuse_sides_squared, pythagorean_theorem_holds

| PK | Field | Expected | Actual |
|-----|-------|----------|--------|
| shape1 | how_many_sides | 3 | 0 |
| shape1 | is_triangle | True | False |
| shape1 | is_right_triangle | True | False |
| shape1 | sum_of_internal_angles | 180 |  |
| shape1 | max_angle | 90 |  |
| shape1 | hypotenuse_length_squared | 25 |  |
| shape1 | non_hypotenuse_sides_squared | 25 |  |
| shape1 | pythagorean_theorem_holds | True | False |
| shape2 | how_many_sides | 4 | 0 |
| shape2 | is_rectangle | True | False |
| shape2 | sum_of_internal_angles | 360 |  |
| shape2 | max_angle | 90 |  |
| shape2 | hypotenuse_length_squared | 0 |  |
| shape2 | non_hypotenuse_sides_squared | 0 |  |
