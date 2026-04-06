# ACME, LLC Rulebook Specification Document

## Overview
This document outlines the specifications for the rulebook generated from the Airtable base "ACME, LLC (template)". It details the structure of the Customers table, including input fields and calculated fields, along with the methods for computing the values of these fields.

## Customers Table

### Input Fields
The following are the input fields used in the Customers table:

1. **CustomerId**
   - **Type:** String
   - **Description:** A unique identifier for each customer. This field is required and cannot be null.

2. **Customer**
   - **Type:** String
   - **Description:** An identifier for the customers. This field is optional and can be null.

3. **EmailAddress**
   - **Type:** String
   - **Description:** The customer's email address. This field is optional and can be null.

4. **FirstName**
   - **Type:** String
   - **Description:** The first name of the customer, used to create the full name. This field is optional and can be null.

5. **LastName**
   - **Type:** String
   - **Description:** The last name of the customer, used to create the full name. This field is optional and can be null.

### Calculated Fields

#### FullName
- **Type:** Calculated
- **Description:** The full name of the customer is computed by concatenating the last name and first name, separated by a comma and a space.
- **Calculation Method:** To compute the FullName, take the LastName and FirstName fields, and format them as follows:
  - Combine the LastName and FirstName using the formula: `={{LastName}} & ", " & {{FirstName}}`
  
- **Example:**
  - For the customer with `FirstName` "Mary" and `LastName` "Smith":
    - **Calculation:** `="Smith" & ", " & "Mary"` results in "Smith, Mary".
  - For the customer with `FirstName` "John" and `LastName` "Doe":
    - **Calculation:** `="Doe" & ", " & "John"` results in "Doe, John".
  - For the customer with `FirstName` "Emily" and `LastName` "Jones":
    - **Calculation:** `="Jones" & ", " & "Emily"` results in "Jones, Emily".

### Summary of Calculated Field
- **FullName** is derived from the combination of the LastName and FirstName fields, formatted as "LastName, FirstName". This allows for a standardized representation of customer names, which is useful for display purposes in reports and communications.