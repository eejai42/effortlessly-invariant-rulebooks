# Test Results: owl

## Summary

| Metric | Value |
|--------|-------|
| Total Fields Tested | 146 |
| Passed | 125 |
| Failed | 21 |
| Score | 85.6% |
| Duration | < 1s |

## Results by Entity

### shapes

- Fields: 15/18 (83.3%)
- Computed columns: how_many_sides, is_rectangle, is_triangle, is_right_triangle, sum_of_internal_angles, max_angle, hypotenuse_length_squared, non_hypotenuse_sides_squared, pythagorean_theorem_holds

| PK | Field | Expected | Actual |
|-----|-------|----------|--------|
| shape1 | is_triangle | True | False |
| shape1 | is_right_triangle | True | False |
| shape1 | pythagorean_theorem_holds | True | False |

### widgets

- Fields: 9/9 (100.0%)
- Computed columns: name_from_appuser, email_address_from_appuser, role_from_appuser

### sides

- Fields: 101/119 (84.9%)
- Computed columns: name, shape_sides, is_rectangle, is_triangle, is_right_triangle, is_hypotenuse, status_of_theorem, pythagorean_theorem_holds, length_squared, hypotenuse_length_squared, non_hypotenuse_length_squared, previous_side_length, next_length, previous_angle, next_angle, previous_label, next_label

| PK | Field | Expected | Actual |
|-----|-------|----------|--------|
| shape1-side-a | name | Shape1-Side-A | shape1-Side-A |
| shape1-side-a | non_hypotenuse_length_squared | 0 | None |
| shape1-side-b | name | Shape1-Side-B | shape1-Side-B |
| shape1-side-b | hypotenuse_length_squared | 0 | None |
| shape1-side-c | name | Shape1-Side-C | shape1-Side-C |
| shape1-side-c | hypotenuse_length_squared | 0 | None |
| shape2-side-a | name | Shape2-Side-A | shape2-Side-A |
| shape2-side-a | hypotenuse_length_squared | 0 | None |
| shape2-side-a | non_hypotenuse_length_squared | 0 | None |
| shape2-side-b | name | Shape2-Side-B | shape2-Side-B |
| shape2-side-b | hypotenuse_length_squared | 0 | None |
| shape2-side-b | non_hypotenuse_length_squared | 0 | None |
| shape2-side-c | name | Shape2-Side-C | shape2-Side-C |
| shape2-side-c | hypotenuse_length_squared | 0 | None |
| shape2-side-c | non_hypotenuse_length_squared | 0 | None |
| shape2-side-d | name | Shape2-Side-D | shape2-Side-D |
| shape2-side-d | hypotenuse_length_squared | 0 | None |
| shape2-side-d | non_hypotenuse_length_squared | 0 | None |
