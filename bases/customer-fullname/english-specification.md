# Specification Document for DEMO: Customer FullName Rulebook

## Overview
This document outlines the specifications for the "DEMO: Customer FullName" rulebook, which is designed to compute the full names of customers based on their first and last names. The rulebook is generated from an Airtable base and includes a schema for customer data, detailing how to derive calculated fields from raw input fields.

## Customers Table

### Input Fields
The following input fields are used to compute the calculated fields in the Customers table:

1. **FirstName**
   - **Type:** String (raw)
   - **Description:** The first name of the customer, used to create the full name.

2. **LastName**
   - **Type:** String (raw)
   - **Description:** The last name of the customer, used to create the full name.

### Calculated Fields

#### FullName
- **Type:** String (calculated)
- **Description:** The full name of the customer is computed by concatenating the first name and last name with a space in between.
- **Computation Explanation:** To compute the FullName, take the value of the FirstName field and append a space followed by the value of the LastName field. If either the FirstName or LastName is missing (null), the FullName will still be computed, but it will reflect the available data.
- **Formula:** `={{FirstName}} & " " & {{LastName}}`
- **Example:**
  - For a customer with:
    - **FirstName:** "Jane"
    - **LastName:** "Smith"
  - The computed **FullName** would be:
    - **FullName:** "Jane Smith"

### Additional Examples from the Data
1. For the customer with:
   - **FirstName:** "John"
   - **LastName:** "Doe"
   - The computed **FullName** would be:
     - **FullName:** "John Doe"

2. For the customer with:
   - **FirstName:** "Emily"
   - **LastName:** "Jones"
   - The computed **FullName** would be:
     - **FullName:** "Emily Jones"

This specification provides a clear understanding of how to compute the FullName field from the FirstName and LastName fields within the Customers table of the DEMO: Customer FullName rulebook.