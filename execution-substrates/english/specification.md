# Specification Document for DEMO: Customer FullName Rulebook

## Overview
This rulebook defines a schema for managing customer data, specifically focusing on the calculation of a customer's full name based on their first and last names. The rulebook is derived from an Airtable base and includes detailed specifications for the fields involved in the computation.

## Entity: Customers

### Input Fields
The following input fields are defined for the Customers entity:

1. **CustomerId**
   - **Type:** String
   - **Description:** A unique identifier for each customer. This field is mandatory.

2. **Customer**
   - **Type:** String
   - **Description:** An identifier for the customers. This field is optional.

3. **EmailAddress**
   - **Type:** String
   - **Description:** The customer's email address. This field is optional.

4. **FirstName**
   - **Type:** String
   - **Description:** The first name of the customer, used to construct the full name. This field is optional.

5. **LastName**
   - **Type:** String
   - **Description:** The last name of the customer, used to construct the full name. This field is optional.

### Calculated Fields

#### FullName
- **Type:** Calculated
- **Description:** The full name of the customer is computed by concatenating the last name and first name, separated by a comma and a space.

##### Computation Explanation
To compute the `FullName`, follow these steps:
1. Retrieve the `LastName` of the customer.
2. Retrieve the `FirstName` of the customer.
3. Concatenate the `LastName`, a comma, a space, and the `FirstName` to form the full name.

##### Formula
```
={{LastName}} & ", " & {{FirstName}}
```

##### Example
Using the provided data from the rulebook:
- For the customer with `CustomerId` "cust0001":
  - `LastName`: "Smith"
  - `FirstName`: "Jane"
  
  The computed `FullName` would be:
  ```
  "Smith, Jane"
  ```

- For the customer with `CustomerId` "cust0002":
  - `LastName`: "Doe"
  - `FirstName`: "John"
  
  The computed `FullName` would be:
  ```
  "Doe, John"
  ```

- For the customer with `CustomerId` "cust0003":
  - `LastName`: "Jones"
  - `FirstName`: "Emily"
  
  The computed `FullName` would be:
  ```
  "Jones, Emily"
  ```

This specification provides a clear method for calculating the `FullName` field based on the `FirstName` and `LastName` fields, ensuring accurate representation of customer names in the system.