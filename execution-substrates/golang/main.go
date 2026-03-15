// ERB SDK - Go Test Runner (GENERATED - DO NOT EDIT)
// =======================================================
// This file is REGENERATED every time inject-into-golang.py runs.
// It must stay in sync with erb_sdk.go and the rulebook.
//
// Tables with calculated fields: Workflows, WorkflowSteps, ApprovalGates, PrecedesSteps, Roles, Departments
// Tables with aggregations: Workflows
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

	fmt.Println("Golang substrate: Processing 6 tables with calculated fields...")
	fmt.Println("  Expected tables: Workflows, WorkflowSteps, ApprovalGates, PrecedesSteps, Roles, Departments")
	fmt.Println("")

	// Track success/failure for ALL tables
	var errors []string
	var totalRecords int

	// ─────────────────────────────────────────────────────────────────
	// Load related tables for aggregation calculations
	// ─────────────────────────────────────────────────────────────────
	workflow_stepsData, err := LoadWorkflowStepRecords(filepath.Join(blankTestsDir, "workflow_steps.json"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "Warning: Could not load WorkflowSteps for aggregations: %v\n", err)
		workflow_stepsData = nil
	}

	// ─────────────────────────────────────────────────────────────────
	// Process Workflows
	// ─────────────────────────────────────────────────────────────────
	fmt.Println("Processing Workflows...")
	workflowsInput := filepath.Join(blankTestsDir, "workflows.json")
	workflowsOutput := filepath.Join(testAnswersDir, "workflows.json")

	workflowsRecords, err := LoadWorkflowRecords(workflowsInput)
	if err != nil {
		errMsg := fmt.Sprintf("Workflows: failed to load - %v", err)
		fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
		errors = append(errors, errMsg)
	} else {
		// Compute aggregations for Workflows
		count_of_non_proposed_stepsCountMap := make(map[string]int)
		if workflow_stepsData != nil {
			for _, rel := range workflow_stepsData {
				if rel.Workflow != nil {
					count_of_non_proposed_stepsCountMap[*rel.Workflow]++
				}
			}
		}

		// Update records with aggregation values
		for i := range workflowsRecords {
			if workflowsRecords[i].WorkflowId != "" {
				count := count_of_non_proposed_stepsCountMap[workflowsRecords[i].WorkflowId]
				workflowsRecords[i].CountOfNonProposedSteps = &count
			}
		}

		var computedWorkflow []Workflow
		for _, r := range workflowsRecords {
			computedWorkflow = append(computedWorkflow, *r.ComputeAll())
		}

		if err := SaveWorkflowRecords(workflowsOutput, computedWorkflow); err != nil {
			errMsg := fmt.Sprintf("Workflows: failed to save - %v", err)
			fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
			errors = append(errors, errMsg)
		} else {
			fmt.Printf("  ✓ workflows: %d records processed\n", len(computedWorkflow))
			totalRecords += len(computedWorkflow)
		}
	}
	fmt.Println("")

	// ─────────────────────────────────────────────────────────────────
	// Process WorkflowSteps
	// ─────────────────────────────────────────────────────────────────
	fmt.Println("Processing WorkflowSteps...")
	workflow_stepsInput := filepath.Join(blankTestsDir, "workflow_steps.json")
	workflow_stepsOutput := filepath.Join(testAnswersDir, "workflow_steps.json")

	workflow_stepsRecords, err := LoadWorkflowStepRecords(workflow_stepsInput)
	if err != nil {
		errMsg := fmt.Sprintf("WorkflowSteps: failed to load - %v", err)
		fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
		errors = append(errors, errMsg)
	} else {
		var computedWorkflowStep []WorkflowStep
		for _, r := range workflow_stepsRecords {
			computedWorkflowStep = append(computedWorkflowStep, *r.ComputeAll())
		}

		if err := SaveWorkflowStepRecords(workflow_stepsOutput, computedWorkflowStep); err != nil {
			errMsg := fmt.Sprintf("WorkflowSteps: failed to save - %v", err)
			fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
			errors = append(errors, errMsg)
		} else {
			fmt.Printf("  ✓ workflow_steps: %d records processed\n", len(computedWorkflowStep))
			totalRecords += len(computedWorkflowStep)
		}
	}
	fmt.Println("")

	// ─────────────────────────────────────────────────────────────────
	// Process ApprovalGates
	// ─────────────────────────────────────────────────────────────────
	fmt.Println("Processing ApprovalGates...")
	approval_gatesInput := filepath.Join(blankTestsDir, "approval_gates.json")
	approval_gatesOutput := filepath.Join(testAnswersDir, "approval_gates.json")

	approval_gatesRecords, err := LoadApprovalGateRecords(approval_gatesInput)
	if err != nil {
		errMsg := fmt.Sprintf("ApprovalGates: failed to load - %v", err)
		fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
		errors = append(errors, errMsg)
	} else {
		var computedApprovalGate []ApprovalGate
		for _, r := range approval_gatesRecords {
			computedApprovalGate = append(computedApprovalGate, *r.ComputeAll())
		}

		if err := SaveApprovalGateRecords(approval_gatesOutput, computedApprovalGate); err != nil {
			errMsg := fmt.Sprintf("ApprovalGates: failed to save - %v", err)
			fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
			errors = append(errors, errMsg)
		} else {
			fmt.Printf("  ✓ approval_gates: %d records processed\n", len(computedApprovalGate))
			totalRecords += len(computedApprovalGate)
		}
	}
	fmt.Println("")

	// ─────────────────────────────────────────────────────────────────
	// Process PrecedesSteps
	// ─────────────────────────────────────────────────────────────────
	fmt.Println("Processing PrecedesSteps...")
	precedes_stepsInput := filepath.Join(blankTestsDir, "precedes_steps.json")
	precedes_stepsOutput := filepath.Join(testAnswersDir, "precedes_steps.json")

	precedes_stepsRecords, err := LoadPrecedesStepRecords(precedes_stepsInput)
	if err != nil {
		errMsg := fmt.Sprintf("PrecedesSteps: failed to load - %v", err)
		fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
		errors = append(errors, errMsg)
	} else {
		var computedPrecedesStep []PrecedesStep
		for _, r := range precedes_stepsRecords {
			computedPrecedesStep = append(computedPrecedesStep, *r.ComputeAll())
		}

		if err := SavePrecedesStepRecords(precedes_stepsOutput, computedPrecedesStep); err != nil {
			errMsg := fmt.Sprintf("PrecedesSteps: failed to save - %v", err)
			fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
			errors = append(errors, errMsg)
		} else {
			fmt.Printf("  ✓ precedes_steps: %d records processed\n", len(computedPrecedesStep))
			totalRecords += len(computedPrecedesStep)
		}
	}
	fmt.Println("")

	// ─────────────────────────────────────────────────────────────────
	// Process Roles
	// ─────────────────────────────────────────────────────────────────
	fmt.Println("Processing Roles...")
	rolesInput := filepath.Join(blankTestsDir, "roles.json")
	rolesOutput := filepath.Join(testAnswersDir, "roles.json")

	rolesRecords, err := LoadRoleRecords(rolesInput)
	if err != nil {
		errMsg := fmt.Sprintf("Roles: failed to load - %v", err)
		fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
		errors = append(errors, errMsg)
	} else {
		var computedRole []Role
		for _, r := range rolesRecords {
			computedRole = append(computedRole, *r.ComputeAll())
		}

		if err := SaveRoleRecords(rolesOutput, computedRole); err != nil {
			errMsg := fmt.Sprintf("Roles: failed to save - %v", err)
			fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
			errors = append(errors, errMsg)
		} else {
			fmt.Printf("  ✓ roles: %d records processed\n", len(computedRole))
			totalRecords += len(computedRole)
		}
	}
	fmt.Println("")

	// ─────────────────────────────────────────────────────────────────
	// Process Departments
	// ─────────────────────────────────────────────────────────────────
	fmt.Println("Processing Departments...")
	departmentsInput := filepath.Join(blankTestsDir, "departments.json")
	departmentsOutput := filepath.Join(testAnswersDir, "departments.json")

	departmentsRecords, err := LoadDepartmentRecords(departmentsInput)
	if err != nil {
		errMsg := fmt.Sprintf("Departments: failed to load - %v", err)
		fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
		errors = append(errors, errMsg)
	} else {
		var computedDepartment []Department
		for _, r := range departmentsRecords {
			computedDepartment = append(computedDepartment, *r.ComputeAll())
		}

		if err := SaveDepartmentRecords(departmentsOutput, computedDepartment); err != nil {
			errMsg := fmt.Sprintf("Departments: failed to save - %v", err)
			fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
			errors = append(errors, errMsg)
		} else {
			fmt.Printf("  ✓ departments: %d records processed\n", len(computedDepartment))
			totalRecords += len(computedDepartment)
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
	fmt.Printf("Golang substrate: ALL %d tables processed successfully (%d total records)\n", 6, totalRecords)
	fmt.Println("════════════════════════════════════════════════════════════════")
}