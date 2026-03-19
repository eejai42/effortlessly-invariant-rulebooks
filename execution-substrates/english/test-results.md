# Test Results: english

## Summary

| Metric | Value |
|--------|-------|
| Total Fields Tested | 146 |
| Passed | 112 |
| Failed | 34 |
| Score | 76.7% |
| Duration | 1m 11s |

## Results by Entity

### shapes

- Fields: 13/18 (72.2%)
- Computed columns: how_many_sides, is_rectangle, is_triangle, is_right_triangle, sum_of_internal_angles, max_angle, hypotenuse_length_squared, non_hypotenuse_sides_squared, pythagorean_theorem_holds

| PK | Field | Expected | Actual |
|-----|-------|----------|--------|
| shape1 | sum_of_internal_angles | 180 | 45, 45, 90 |
| shape1 | hypotenuse_length_squared | 25 | 25, ,  |
| shape1 | non_hypotenuse_sides_squared | 25 | , 16, 9 |
| shape2 | sum_of_internal_angles | 360 | 90, 90, 90, 90 |
| shape2 | pythagorean_theorem_holds | False | None |

### widgets

- Fields: 9/9 (100.0%)
- Computed columns: name_from_appuser, email_address_from_appuser, role_from_appuser

### sides

- Fields: 90/119 (75.6%)
- Computed columns: name, shape_sides, is_rectangle, is_triangle, is_right_triangle, is_hypotenuse, status_of_theorem, pythagorean_theorem_holds, length_squared, hypotenuse_length_squared, non_hypotenuse_length_squared, previous_side_length, next_length, previous_angle, next_angle, previous_label, next_label

| PK | Field | Expected | Actual |
|-----|-------|----------|--------|
| shape1-side-a | name | Shape1-Side-A | None |
| shape1-side-a | status_of_theorem | Pythagorean Theorem Holds (obv | holds |
| shape1-side-a | non_hypotenuse_length_squared | 0 | 25 |
| shape1-side-b | name | Shape1-Side-B | None |
| shape1-side-b | status_of_theorem | Pythagorean Theorem Holds (obv | holds |
| shape1-side-b | hypotenuse_length_squared | 0 | None |
| shape1-side-c | name | Shape1-Side-C | None |
| shape1-side-c | status_of_theorem | Pythagorean Theorem Holds (obv | holds |
| shape1-side-c | hypotenuse_length_squared | 0 | None |
| shape2-side-a | name | Shape2-Side-A | None |
| shape2-side-a | is_hypotenuse | False | None |
| shape2-side-a | status_of_theorem | NA | None |
| shape2-side-a | hypotenuse_length_squared | 0 | None |
| shape2-side-a | non_hypotenuse_length_squared | 0 | None |
| shape2-side-b | name | Shape2-Side-B | None |
| shape2-side-b | is_hypotenuse | False | None |
| shape2-side-b | status_of_theorem | NA | None |
| shape2-side-b | hypotenuse_length_squared | 0 | None |
| shape2-side-b | non_hypotenuse_length_squared | 0 | None |
| shape2-side-c | name | Shape2-Side-C | None |
| ... | ... | (9 more) | ... |
