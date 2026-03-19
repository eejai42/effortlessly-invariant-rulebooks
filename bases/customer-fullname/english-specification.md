# Specification Document for DEMO: Customer FullName Rulebook

## Overview
This document outlines the specifications for the rulebook titled "DEMO: Customer FullName." The purpose of this rulebook is to define how to compute the full name of customers based on their first and last names. The rulebook is structured around a table containing customer data, including identifiers, email addresses, and names.

## Customers Table

### Input Fields
The following input fields are defined in the Customers table. These fields are of type "raw" and are used to compute the calculated field:

1. **CustomerId**
   - **Type:** String
   - **Description:** Unique identifier for each customer. This field is mandatory.

2. **Customer**
   - **Type:** String
   - **Description:** Identifier for the customers. This field is optional.

3. **EmailAddress**
   - **Type:** String
   - **Description:** The customer's email address. This field is optional.

4. **FirstName**
   - **Type:** String
   - **Description:** First name of the customer, used to create the full name. This field is optional.

5. **LastName**
   - **Type:** String
   - **Description:** Last name of the customer, used to create the full name. This field is optional.

### Calculated Fields

#### FullName
- **Type:** Calculated
- **Description:** The full name is computed by concatenating the first name and last name of the customer, separated by a space.
- **Formula:** `={{FirstName}} & " " & {{LastName}}`

**How to Compute:**
To compute the `FullName`, follow these steps:
1. Retrieve the values of the `FirstName` and `LastName` fields for the customer.
2. Concatenate the `FirstName` and `LastName` values with a space in between.

**Example:**
For the customer with the following data:
- **FirstName:** Mark
- **LastName:** Smith

The computation would be:
- `FullName = "Mark" & " " & "Smith"` 
- Result: `FullName = "Mark Smith"`

### Summary of Data
Here are some examples from the Customers table to illustrate the computed `FullName`:

1. **CustomerId:** cust0001
   - **FirstName:** Mark
   - **LastName:** Smith
   - **Computed FullName:** Mark Smith

2. **CustomerId:** cust0002
   - **FirstName:** John
   - **LastName:** Doe
   - **Computed FullName:** John Doe

3. **CustomerId:** cust0003
   - **FirstName:** Emily
   - **LastName:** Jones
   - **Computed FullName:** Emily Jones

This specification provides a clear and concise method for calculating the full name of customers based on their first and last names, ensuring accurate data representation in the system.