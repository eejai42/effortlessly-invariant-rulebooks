# Test Results: yaml

## Summary

| Metric | Value |
|--------|-------|
| Total Fields Tested | 18 |
| Passed | 9 |
| Failed | 9 |
| Score | 50.0% |
| Duration | < 1s |

## Results by Entity

### shapes

- Fields: 9/18 (50.0%)
- Computed columns: how_many_sides, is_rectangle, is_triangle, is_right_triangle, sum_of_internal_angles, max_angle, hypotenuse_length_squared, non_hypotenuse_sides_squared, pythagorean_theorem_holds

| PK | Field | Expected | Actual |
|-----|-------|----------|--------|
| shape1 | is_triangle | True | False |
| shape1 | is_right_triangle | True | False |
| shape1 | sum_of_internal_angles | 180 | 45, 45, 90 |
| shape1 | max_angle | 90 | None |
| shape1 | hypotenuse_length_squared | 25 | 25, ,  |
| shape1 | non_hypotenuse_sides_squared | 25 | , 16, 9 |
| shape1 | pythagorean_theorem_holds | True | False |
| shape2 | sum_of_internal_angles | 360 | 90, 90, 90, 90 |
| shape2 | max_angle | 90 | None |
