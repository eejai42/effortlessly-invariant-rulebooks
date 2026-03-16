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

// FlexibleString is a type that can unmarshal from both string and number JSON values
// This is needed for aggregation fields that return 0 (int) when empty or string values
type FlexibleString string

func (f *FlexibleString) UnmarshalJSON(data []byte) error {
	// First try as string
	var s string
	if err := json.Unmarshal(data, &s); err == nil {
		*f = FlexibleString(s)
		return nil
	}
	// Try as number
	var n float64
	if err := json.Unmarshal(data, &n); err == nil {
		// Convert number to string, but treat 0 as empty
		if n == 0 {
			*f = FlexibleString("0")
		} else {
			*f = FlexibleString(fmt.Sprintf("%v", n))
		}
		return nil
	}
	return fmt.Errorf("cannot unmarshal %s into FlexibleString", string(data))
}

// String returns the underlying string value
func (f FlexibleString) String() string {
	return string(f)
}

// =============================================================================
// WORKFLOWS TABLE
// Table: Workflows
// =============================================================================

// Workflow represents a row in the Workflows table
// Table: Workflows
type Workflow struct {
	WorkflowId string `json:"workflow_id"`
	Title *string `json:"title"`
	Description *string `json:"description"`
	Created *string `json:"created"`
	Modified *string `json:"modified"`
	Identifier *string `json:"identifier"`
	WorkflowSteps *string `json:"workflow_steps"`
	CountOfWorkflowSteps *int `json:"count_of_workflow_steps"`
}

// =============================================================================
// WORKFLOWSTEPS TABLE
// Table: WorkflowSteps
// =============================================================================

// WorkflowStep represents a row in the WorkflowSteps table
// Table: WorkflowSteps
type WorkflowStep struct {
	WorkflowStepId string `json:"workflow_step_id"`
	Label *string `json:"label"`
	SequencePosition *int `json:"sequence_position"`
	RequiresHumanApproval *bool `json:"requires_human_approval"`
	IsStepOf *string `json:"is_step_of"`
	AssignedRole *string `json:"assigned_role"`
	IsStepOfTitle *string `json:"is_step_of_title"`
	IsStepOfDescription *string `json:"is_step_of_description"`
	IsStepOfIdentifier *string `json:"is_step_of_identifier"`
	AssignedRoleLabel *string `json:"assigned_role_label"`
	AssignedRoleComment *string `json:"assigned_role_comment"`
	AssignedRoleFilledBy *string `json:"assigned_role_filled_by"`
}

// =============================================================================
// ROLES TABLE
// Table: Roles
// =============================================================================

// Role represents a row in the Roles table
// Table: Roles
type Role struct {
	RoleId string `json:"role_id"`
	Label *string `json:"label"`
	Comment *string `json:"comment"`
	FilledBy *string `json:"filled_by"`
	WorkflowSteps *string `json:"workflow_steps"`
	CountOfWorkflowSteps *int `json:"count_of_workflow_steps"`
	FilledByName *string `json:"filled_by_name"`
	FilledByMBox *string `json:"filled_by_m_box"`
}

// =============================================================================
// HUMANAGENTS TABLE
// Table: HumanAgents
// =============================================================================

// HumanAgent represents a row in the HumanAgents table
// Table: HumanAgents
type HumanAgent struct {
	HumanAgentId string `json:"human_agent_id"`
	Name *string `json:"name"`
	Mbox *string `json:"mbox"`
	Roles *string `json:"roles"`
	CountOfRles *int `json:"count_of_rles"`
}
