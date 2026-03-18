# Specification Document for DEMO: Customer FullName Rulebook

## Overview
This specification document outlines the rules and calculations for generating customer full names based on individual first and last names. The rulebook is derived from an Airtable base and provides a structured approach to computing the `FullName` field for each customer.

## Entities and Calculated Fields

### Customers
The `Customers` entity contains the following input fields that are used to compute the `FullName`:

#### Input Fields
1. **FirstName**
   - **Type**: String
   - **Description**: The first name of the customer, used to create the full name.

2. **LastName**
   - **Type**: String
   - **Description**: The last name of the customer, used to create the full name.

#### Calculated Field
1. **FullName**
   - **Type**: String
   - **Description**: The full name is computed by concatenating the first name and last name of the customer with a space in between.
   - **Calculation Explanation**: To compute the `FullName`, take the value of the `FirstName` and append a space followed by the value of the `LastName`. If either the `FirstName` or `LastName` is missing, the full name will still be generated, but it may contain leading or trailing spaces.
   - **Formula**: `={{FirstName}} & " " & {{LastName}}`
   - **Example**: 
     - For a customer with:
       - `FirstName`: "Jane"
       - `LastName`: "Smith"
     - The computed `FullName` would be: "Jane Smith".

### Example Data
The following examples illustrate how the `FullName` is computed for each customer in the dataset:

1. **Customer 1**
   - **FirstName**: "Jane"
   - **LastName**: "Smith"
   - **Computed FullName**: "Jane Smith"

2. **Customer 2**
   - **FirstName**: "John"
   - **LastName**: "Doe"
   - **Computed FullName**: "John Doe"

3. **Customer 3**
   - **FirstName**: "Emily"
   - **LastName**: "Jones"
   - **Computed FullName**: "Emily Jones"

This specification provides a clear guide on how to compute the `FullName` for each customer based on their first and last names, ensuring consistency and accuracy in the data representation.