# Specification Document for DEMO: Customer FullName Rulebook

## Overview
This document outlines the specifications for the "DEMO: Customer FullName" rulebook, which is designed to compute the full names of customers based on their first and last names. The rulebook is derived from an Airtable base and includes a schema for customer data, detailing how to derive calculated fields from raw input fields.

## Entity: Customers

### Input Fields
The following input fields are used to compute the calculated field:

1. **CustomerId**
   - **Type:** String
   - **Description:** Unique identifier for the customer. This field is mandatory and cannot be null.

2. **Customer**
   - **Type:** String
   - **Description:** Identifier for the customers. This field is optional and can be null.

3. **EmailAddress**
   - **Type:** String
   - **Description:** The customer's email address. This field is optional and can be null.

4. **FirstName**
   - **Type:** String
   - **Description:** First name of the customer, used to create the full name. This field is optional and can be null.

5. **LastName**
   - **Type:** String
   - **Description:** Last name of the customer, used to create the full name. This field is optional and can be null.

### Calculated Field

#### FullName
- **Type:** String
- **Description:** The full name is computed by combining the last name and first name of the customer in the format "LastName, FirstName". This field is optional and can be null.

#### Computation Method
To compute the **FullName**, follow these steps:
1. Retrieve the values of the **LastName** and **FirstName** fields.
2. Concatenate the **LastName** with a comma and a space, followed by the **FirstName**.
3. If either the **LastName** or **FirstName** is null, the resulting **FullName** will also be null.

#### Formula for Reference
```plaintext
={{LastName}} & ", " & {{FirstName}}
```

#### Concrete Examples
Using the data provided in the rulebook, the following examples illustrate how to compute the **FullName**:

1. **Example 1:**
   - **FirstName:** Jane
   - **LastName:** Smith
   - **Computed FullName:** 
     - Calculation: "Smith, Jane"
   
2. **Example 2:**
   - **FirstName:** John
   - **LastName:** Doe
   - **Computed FullName:** 
     - Calculation: "Doe, John"

3. **Example 3:**
   - **FirstName:** Emily
   - **LastName:** Jones
   - **Computed FullName:** 
     - Calculation: "Jones, Emily"

By following the above steps and examples, one can accurately compute the **FullName** for any customer based on their first and last names as outlined in this rulebook.