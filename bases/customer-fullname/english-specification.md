# Specification Document for DEMO: Customer FullName Rulebook

## Overview
This specification document outlines the rules for computing calculated fields in the "DEMO: Customer FullName" rulebook. The rulebook is derived from an Airtable base and contains a table of customers with various attributes. The primary focus is on how to compute the full name of each customer based on their first and last names.

## Customers Table

### Input Fields
The following input fields are used to compute the calculated fields in the Customers table:

1. **FirstName**
   - **Type**: String (raw)
   - **Description**: First Name of the customer - used to make the full name.

2. **LastName**
   - **Type**: String (raw)
   - **Description**: Last Name of the customer - used to make the full name.

### Calculated Fields

#### FullName
- **Type**: String (calculated)
- **Description**: The full name is computed from the first and last name of the customer.
- **Computation Method**: 
  To compute the FullName, concatenate the FirstName and LastName fields, separated by a space. This means you take the value from the FirstName field, add a space, and then add the value from the LastName field.

- **Formula**: 
  ```plaintext
  = {{FirstName}} & " " & {{LastName}}
  ```

- **Example**: 
  For a customer with the following data:
  - FirstName: "Jane"
  - LastName: "Smith"
  
  The computation would proceed as follows:
  - FullName = "Jane" & " " & "Smith" 
  - Result: "Jane Smith"

### Additional Examples
1. For a customer with:
   - FirstName: "John"
   - LastName: "Doe"
   
   The computed FullName would be:
   - FullName = "John" & " " & "Doe"
   - Result: "John Doe"

2. For a customer with:
   - FirstName: "Emily"
   - LastName: "Jones"
   
   The computed FullName would be:
   - FullName = "Emily" & " " & "Jones"
   - Result: "Emily Jones"

This specification provides a clear methodology for calculating the FullName field based on the FirstName and LastName inputs, ensuring accurate results in the customer database.