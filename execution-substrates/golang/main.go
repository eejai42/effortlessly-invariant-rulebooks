// ERB SDK - Go Test Runner (GENERATED - DO NOT EDIT)
// =======================================================
// This file is REGENERATED every time inject-into-golang.py runs.
// It must stay in sync with erb_sdk.go and the rulebook.
//
// Tables with calculated fields: Customers
//
// IMPORTANT: This runner processes ALL tables, not just a "primary" one.
// If ANY table fails to process, the entire run fails with exit code 1.

package main

import (
	"fmt"
	"os"
	"path/filepath"
)

func main() {
	scriptDir, err := os.Getwd()
	if err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: Failed to get working directory: %v\n", err)
		os.Exit(1)
	}

	// Shared blank-tests directory at project root
	blankTestsDir := filepath.Join(scriptDir, "..", "..", "testing", "blank-tests")
	testAnswersDir := filepath.Join(scriptDir, "test-answers")

	// Ensure output directory exists
	if err := os.MkdirAll(testAnswersDir, 0755); err != nil {
		fmt.Fprintf(os.Stderr, "FATAL: Failed to create test-answers directory: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("Golang substrate: Processing 1 tables with calculated fields...")
	fmt.Println("  Expected tables: Customers")
	fmt.Println("")

	// Track success/failure for ALL tables
	var errors []string
	var totalRecords int

	// ─────────────────────────────────────────────────────────────────
	// Process Customers
	// ─────────────────────────────────────────────────────────────────
	fmt.Println("Processing Customers...")
	customersInput := filepath.Join(blankTestsDir, "customers.json")
	customersOutput := filepath.Join(testAnswersDir, "customers.json")

	customersRecords, err := LoadCustomerRecords(customersInput)
	if err != nil {
		errMsg := fmt.Sprintf("Customers: failed to load - %v", err)
		fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
		errors = append(errors, errMsg)
	} else {
		var computedCustomer []Customer
		for _, r := range customersRecords {
			computedCustomer = append(computedCustomer, *r.ComputeAll())
		}

		if err := SaveCustomerRecords(customersOutput, computedCustomer); err != nil {
			errMsg := fmt.Sprintf("Customers: failed to save - %v", err)
			fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
			errors = append(errors, errMsg)
		} else {
			fmt.Printf("  ✓ customers: %d records processed\n", len(computedCustomer))
			totalRecords += len(computedCustomer)
		}
	}
	fmt.Println("")

	// ─────────────────────────────────────────────────────────────────
	// Final validation - FAIL LOUDLY if any errors occurred
	// ─────────────────────────────────────────────────────────────────
	if len(errors) > 0 {
		fmt.Fprintf(os.Stderr, "\n")
		fmt.Fprintf(os.Stderr, "════════════════════════════════════════════════════════════════\n")
		fmt.Fprintf(os.Stderr, "FATAL: %d table(s) FAILED to process\n", len(errors))
		fmt.Fprintf(os.Stderr, "════════════════════════════════════════════════════════════════\n")
		for _, e := range errors {
			fmt.Fprintf(os.Stderr, "  • %s\n", e)
		}
		fmt.Fprintf(os.Stderr, "\n")
		os.Exit(1)
	}

	fmt.Println("════════════════════════════════════════════════════════════════")
	fmt.Printf("Golang substrate: ALL %d tables processed successfully (%d total records)\n", 1, totalRecords)
	fmt.Println("════════════════════════════════════════════════════════════════")
}