# DEMO: Pythagorean Theorem Rulebook Specification

## Overview
This rulebook defines the structure and calculations for a system that evaluates geometric shapes, specifically focusing on the Pythagorean theorem. It includes entities for app users, shapes, sides, and their relationships, enabling the computation of various geometric properties and validations.

---

## Entities with Calculated Fields

### 1. Shapes

#### Input Fields
- **ShapeId**: `string` - Unique identifier for the shape.
- **Name**: `string` - Name of the shape.
- **Sides**: `string` - Relationship to the sides of the shape.
- **HowManySides**: `integer` - Number of sides of the shape (calculated).
- **SumOfInternalAngles**: `number` - Total sum of internal angles of the shape (calculated).
- **MaxAngle**: `number` - Maximum angle in the shape (calculated).

#### Calculated Fields
- **IsRectangle**
  - **Description**: Determines if the shape is a rectangle. A rectangle has exactly four sides.
  - **Calculation**: Check if `HowManySides` equals 4.
  - **Formula**: `=AND({{HowManySides}}=4)`
  - **Example**: For a shape with `HowManySides` = 4, `IsRectangle` would be `true`.

- **IsTriangle**
  - **Description**: Determines if the shape is a triangle. A triangle has exactly three sides and the sum of internal angles equals 180 degrees.
  - **Calculation**: Check if `SumOfInternalAngles` equals 180 and `HowManySides` equals 3.
  - **Formula**: `=AND({{SumOfInternalAngles}}=180, {{HowManySides}}=3)`
  - **Example**: For a shape with `SumOfInternalAngles` = 180 and `HowManySides` = 3, `IsTriangle` would be `true`.

- **IsRightTriangle**
  - **Description**: Determines if the triangle is a right triangle. A right triangle has a maximum angle of 90 degrees.
  - **Calculation**: Check if the shape is a triangle and if `MaxAngle` equals 90.
  - **Formula**: `=AND({{IsTriangle}}, {{MaxAngle}} = 90)`
  - **Example**: For a shape that is a triangle with `MaxAngle` = 90, `IsRightTriangle` would be `true`.

- **HypotenuseLengthSquared**
  - **Description**: Computes the sum of the squares of the lengths of the hypotenuse sides.
  - **Calculation**: Sum the squared lengths of sides identified as hypotenuses.
  - **Formula**: `=SUMIFS(Sides!{{HypotenuseLengthSquared}}, Sides!{{Shape}}, Shapes!{{ShapeId}})`
  - **Example**: If the hypotenuse side has a length of 5, then `HypotenuseLengthSquared` would be 25.

- **NonHypotenuseSidesSquared**
  - **Description**: Computes the sum of the squares of the lengths of the non-hypotenuse sides.
  - **Calculation**: Sum the squared lengths of sides that are not hypotenuses.
  - **Formula**: `=SUMIFS(Sides!{{NonHypotenuseLengthSquared}}, Sides!{{Shape}}, Shapes!{{ShapeId}})`
  - **Example**: If the non-hypotenuse sides have lengths of 3 and 4, then `NonHypotenuseSidesSquared` would be 9 + 16 = 25.

- **PythagoreanTheoremHolds**
  - **Description**: Validates if the Pythagorean theorem holds true for the shape.
  - **Calculation**: Check if the shape is a right triangle and if the square of the hypotenuse equals the sum of the squares of the non-hypotenuse sides.
  - **Formula**: `=AND({{IsRightTriangle}}, {{HypotenuseLengthSquared}} = {{NonHypotenuseSidesSquared}})`
  - **Example**: For a right triangle where `HypotenuseLengthSquared` = 25 and `NonHypotenuseSidesSquared` = 25, `PythagoreanTheoremHolds` would be `true`.

---

### 2. Sides

#### Input Fields
- **SideId**: `string` - Unique identifier for the side.
- **Name**: `string` - Name of the side.
- **Shape**: `string` - Relationship to the shape.
- **Label**: `string` - Label for the side.
- **Length**: `integer` - Length of the side.
- **Angle**: `integer` - Internal angle for the side.

#### Calculated Fields
- **LengthSquared**
  - **Description**: Computes the square of the length of the side.
  - **Calculation**: Multiply the length of the side by itself.
  - **Formula**: `={{Length}} * {{Length}}`
  - **Example**: For a side with `Length` = 5, `LengthSquared` would be 25.

- **IsHypotenuse**
  - **Description**: Determines if the side is the hypotenuse of a right triangle.
  - **Calculation**: Check if the side is part of a triangle and has a length greater than both adjacent sides.
  - **Formula**: `=AND({{IsTriangle}}, {{Length}} > {{PreviousSideLength}}, {{Length}} > {{NextLength}})`
  - **Example**: If a side has `Length` = 5, `PreviousSideLength` = 4, and `NextLength` = 3, then `IsHypotenuse` would be `true`.

- **HypotenuseLengthSquared**
  - **Description**: Computes the squared length of the hypotenuse if this side is the hypotenuse.
  - **Calculation**: If the side is identified as a hypotenuse, return its squared length.
  - **Formula**: `=IF({{IsHypotenuse}}, {{LengthSquared}})`
  - **Example**: If this side is a hypotenuse with `LengthSquared` = 25, then `HypotenuseLengthSquared` would be 25.

- **NonHypotenuseLengthSquared**
  - **Description**: Computes the squared length of the side if it is not the hypotenuse.
  - **Calculation**: If the side is part of a triangle but not the hypotenuse, return its squared length.
  - **Formula**: `=IF(AND(NOT({{IsHypotenuse}}), {{IsTriangle}}), {{LengthSquared}})`
  - **Example**: If this side has `LengthSquared` = 16 and is not the hypotenuse, then `NonHypotenuseLengthSquared` would be 16.

---

This specification provides a comprehensive guide to understanding how to compute the calculated fields in the DEMO: Pythagorean Theorem rulebook. By following the outlined calculations and examples, one can derive the necessary values without needing to reference the original formulas directly.