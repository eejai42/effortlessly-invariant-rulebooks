# Test Results: uml

## Summary

| Metric | Value |
|--------|-------|
| Total Fields Tested | 146 |
| Passed | 109 |
| Failed | 37 |
| Score | 74.7% |
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

### widgets

- Fields: 9/9 (100.0%)
- Computed columns: name_from_appuser, email_address_from_appuser, role_from_appuser

### sides

- Fields: 91/119 (76.5%)
- Computed columns: name, shape_sides, is_rectangle, is_triangle, is_right_triangle, is_hypotenuse, status_of_theorem, pythagorean_theorem_holds, length_squared, hypotenuse_length_squared, non_hypotenuse_length_squared, previous_side_length, next_length, previous_angle, next_angle, previous_label, next_label

| PK | Field | Expected | Actual |
|-----|-------|----------|--------|
| shape1-side-a | name | Shape1-Side-A | shape1-Side-A |
| shape1-side-a | length_squared | 25 | None |
| shape1-side-a | hypotenuse_length_squared | 25 | None |
| shape1-side-a | non_hypotenuse_length_squared | 0 |  |
| shape1-side-b | name | Shape1-Side-B | shape1-Side-B |
| shape1-side-b | length_squared | 16 | None |
| shape1-side-b | hypotenuse_length_squared | 0 |  |
| shape1-side-b | non_hypotenuse_length_squared | 16 | None |
| shape1-side-c | name | Shape1-Side-C | shape1-Side-C |
| shape1-side-c | length_squared | 9 | None |
| shape1-side-c | hypotenuse_length_squared | 0 |  |
| shape1-side-c | non_hypotenuse_length_squared | 9 | None |
| shape2-side-a | name | Shape2-Side-A | shape2-Side-A |
| shape2-side-a | length_squared | 4 | None |
| shape2-side-a | hypotenuse_length_squared | 0 |  |
| shape2-side-a | non_hypotenuse_length_squared | 0 |  |
| shape2-side-b | name | Shape2-Side-B | shape2-Side-B |
| shape2-side-b | length_squared | 4 | None |
| shape2-side-b | hypotenuse_length_squared | 0 |  |
| shape2-side-b | non_hypotenuse_length_squared | 0 |  |
| ... | ... | (8 more) | ... |
