// ERB SDK - Go Implementation (GENERATED - DO NOT EDIT)
// ======================================================
// Generated from: effortless-rulebook/effortless-rulebook.json
//
// This file contains structs and calculation functions
// for all tables defined in the rulebook.

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strconv"
)

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

// boolVal safely dereferences a *bool, returning false if nil
func boolVal(b *bool) bool {
	if b == nil {
		return false
	}
	return *b
}

// stringVal safely dereferences a *string, returning "" if nil
func stringVal(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}

// nilIfEmpty returns nil for empty strings, otherwise a pointer to the string
func nilIfEmpty(s string) *string {
	if s == "" {
		return nil
	}
	return &s
}

// intToString safely converts a *int to string, returning "" if nil
func intToString(i *int) string {
	if i == nil {
		return ""
	}
	return strconv.Itoa(*i)
}

// boolToString converts a bool to "true" or "false"
func boolToString(b bool) string {
	if b {
		return "true"
	}
	return "false"
}

// =============================================================================
// CUSTOMERS TABLE
// Table: Customers
// =============================================================================

// Customer represents a row in the Customers table
// Table: Customers
type Customer struct {
	CustomerId string `json:"customer_id"`
	Customer *string `json:"customer"` // Identifier for the customers.
	EmailAddress *string `json:"email_address"` // Thec ustomers email address
	FirstName *string `json:"first_name"` // First Name of the customer - used to make the full name
	LastName *string `json:"last_name"` // Last Name of the customer - used to make the full name
	FullName *string `json:"full_name"` // Full name is computed from the first and last name of the customer
}

// --- Individual Calculation Functions ---

// CalcFullName computes the FullName calculated field
// Full name is computed from the first and last name of the customer
// Formula: ={{LastName}} & ", " & {{FirstName}}
func (tc *Customer) CalcFullName() string {
	return stringVal(tc.LastName) + ", " + stringVal(tc.FirstName)
}

// --- Compute All Calculated Fields ---

// ComputeAll computes all calculated fields and returns an updated struct
func (tc *Customer) ComputeAll() *Customer {
	// Level 1 calculations
	fullName := stringVal(tc.LastName) + ", " + stringVal(tc.FirstName)

	return &Customer{
		CustomerId: tc.CustomerId,
		Customer: tc.Customer,
		EmailAddress: tc.EmailAddress,
		FirstName: tc.FirstName,
		LastName: tc.LastName,
		FullName: nilIfEmpty(fullName),
	}
}

// =============================================================================
// FILE I/O FUNCTIONS (for all tables with calculated fields)
// =============================================================================

// LoadCustomerRecords loads Customers records from a JSON file
func LoadCustomerRecords(path string) ([]Customer, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var records []Customer
	if err := json.Unmarshal(data, &records); err != nil {
		return nil, fmt.Errorf("failed to parse file: %w", err)
	}

	return records, nil
}

// SaveCustomerRecords saves computed Customers records to a JSON file
func SaveCustomerRecords(path string, records []Customer) error {
	data, err := json.MarshalIndent(records, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal records: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write records: %w", err)
	}

	return nil
}
