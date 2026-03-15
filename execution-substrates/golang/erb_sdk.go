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
	"strings"
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
// WORKFLOWS TABLE
// Table: Workflows
// =============================================================================

// Workflow represents a row in the Workflows table
// Table: Workflows
type Workflow struct {
	WorkflowId string `json:"workflow_id"`
	DisplayName *string `json:"display_name"`
	Title *string `json:"title"` // Human-readable title of the workflow. Maps to dct:title from Dublin Core. Example: 'Production Deployment Workflow', 'Employee Onboarding'.
	Color *string `json:"color"`
	Description *string `json:"description"` // Detailed description of the workflow's purpose and scope. Maps to dct:description from Dublin Core. Should explain what business goal the workflow achieves.
	Identifier *string `json:"identifier"` // External system identifier for cross-referencing. Maps to dct:identifier from Dublin Core. This is the join key back to document management systems, ticket systems, or other operational systems.
	Modified *string `json:"modified"` // Last modification timestamp. Maps to dct:modified from Dublin Core. Critical for answering CQ5: 'Which workflows haven't been reviewed or updated in twelve months?'
	WorkflowSteps *string `json:"workflow_steps"` // Reference to workflow steps. Represents the ntwf:hasStep relationship linking workflows to their constituent steps.
	CountOfNonProposedSteps *int `json:"count_of_non_proposed_steps"` // Calculated count of workflow steps in this workflow. Useful for workflow complexity analysis and reporting.
	Name *string `json:"name"` // Short machine-friendly name for the workflow. Used for programmatic reference and URL slug generation.
	HasMoreThan1Step *bool `json:"has_more_than1_step"`
}

// --- Individual Calculation Functions ---

// CalcName computes the Name calculated field
// Short machine-friendly name for the workflow. Used for programmatic reference and URL slug generation.
// Formula: =SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")
func (tc *Workflow) CalcName() string {
	return strings.ReplaceAll(strings.ToLower(stringVal(tc.DisplayName)), " ", "-")
}

// CalcHasMoreThan1Step computes the HasMoreThan1Step calculated field
// Formula: ={{CountOfNonProposedSteps}} > 1
func (tc *Workflow) CalcHasMoreThan1Step() bool {
	return (tc.CountOfNonProposedSteps != nil && *tc.CountOfNonProposedSteps > 1)
}

// --- Compute All Calculated Fields ---

// ComputeAll computes all calculated fields and returns an updated struct
func (tc *Workflow) ComputeAll() *Workflow {
	// Level 1 calculations
	name := strings.ReplaceAll(strings.ToLower(stringVal(tc.DisplayName)), " ", "-")
	hasMoreThan1Step := (tc.CountOfNonProposedSteps != nil && *tc.CountOfNonProposedSteps > 1)

	return &Workflow{
		WorkflowId: tc.WorkflowId,
		DisplayName: tc.DisplayName,
		Title: tc.Title,
		Color: tc.Color,
		Description: tc.Description,
		Identifier: tc.Identifier,
		Modified: tc.Modified,
		WorkflowSteps: tc.WorkflowSteps,
		CountOfNonProposedSteps: tc.CountOfNonProposedSteps,
		Name: nilIfEmpty(name),
		HasMoreThan1Step: &hasMoreThan1Step,
	}
}

// =============================================================================
// WORKFLOWSTEPS TABLE
// Table: WorkflowSteps
// =============================================================================

// WorkflowStep represents a row in the WorkflowSteps table
// Table: WorkflowSteps
type WorkflowStep struct {
	WorkflowStepId string `json:"workflow_step_id"`
	DisplayName *string `json:"display_name"`
	Workflow *string `json:"workflow"` // Foreign key to the parent workflow. Represents the inverse of ntwf:hasStep, enabling navigation from step to its containing workflow (ntwf:isStepOf).
	SequencePosition *int `json:"sequence_position"` // Integer ordinal position of the step within its workflow. Maps to ntwf:sequencePosition, declared as owl:FunctionalProperty (each step has exactly one position). Enables positional queries.
	AssignedRole *string `json:"assigned_role"` // Foreign key to the Role responsible for executing this step. Maps to ntwf:assignedRole. Critical for implementing Heuristic 2 (role-agent separation): steps point to roles, not directly to agents.
	RequiresHumanApproval *bool `json:"requires_human_approval"` // Boolean flag indicating whether a human agent must fill the assigned role. Maps to ntwf:requiresHumanApproval. Enables answering CQ3: 'Which steps require human decisions vs. AI execution?'
	ApprovalGate *string `json:"approval_gate"` // Foreign key to ApprovalGate if this step is a decision checkpoint. When populated, indicates this step blocks workflow execution until explicit authorization is given.
	PrecededBySteps *string `json:"preceded_by_steps"` // Reference to steps that must complete before this step can execute. Part of the ntwf:precedesStep transitive ordering relationship.
	Name *string `json:"name"`
}

// --- Individual Calculation Functions ---

// CalcName computes the Name calculated field
// Formula: =SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")
func (tc *WorkflowStep) CalcName() string {
	return strings.ReplaceAll(strings.ToLower(stringVal(tc.DisplayName)), " ", "-")
}

// --- Compute All Calculated Fields ---

// ComputeAll computes all calculated fields and returns an updated struct
func (tc *WorkflowStep) ComputeAll() *WorkflowStep {
	// Level 1 calculations
	name := strings.ReplaceAll(strings.ToLower(stringVal(tc.DisplayName)), " ", "-")

	return &WorkflowStep{
		WorkflowStepId: tc.WorkflowStepId,
		DisplayName: tc.DisplayName,
		Workflow: tc.Workflow,
		SequencePosition: tc.SequencePosition,
		AssignedRole: tc.AssignedRole,
		RequiresHumanApproval: tc.RequiresHumanApproval,
		ApprovalGate: tc.ApprovalGate,
		PrecededBySteps: tc.PrecededBySteps,
		Name: nilIfEmpty(name),
	}
}

// =============================================================================
// APPROVALGATES TABLE
// Table: ApprovalGates
// =============================================================================

// ApprovalGate represents a row in the ApprovalGates table
// Table: ApprovalGates
type ApprovalGate struct {
	ApprovalGateId string `json:"approval_gate_id"`
	DisplayName *string `json:"display_name"`
	WorkflowSteps *string `json:"workflow_steps"` // Back-reference to workflow steps that use this approval gate. Enables finding all steps requiring this specific gate.
	EscalationThresholdHours *int `json:"escalation_threshold_hours"` // Integer number of hours that may elapse on a pending gate before the ntwf:delegatesTo chain activates. Maps to ntwf:escalationThresholdHours. Domain applies only to ApprovalGate individuals.
	Name *string `json:"name"`
}

// --- Individual Calculation Functions ---

// CalcName computes the Name calculated field
// Formula: =SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")
func (tc *ApprovalGate) CalcName() string {
	return strings.ReplaceAll(strings.ToLower(stringVal(tc.DisplayName)), " ", "-")
}

// --- Compute All Calculated Fields ---

// ComputeAll computes all calculated fields and returns an updated struct
func (tc *ApprovalGate) ComputeAll() *ApprovalGate {
	// Level 1 calculations
	name := strings.ReplaceAll(strings.ToLower(stringVal(tc.DisplayName)), " ", "-")

	return &ApprovalGate{
		ApprovalGateId: tc.ApprovalGateId,
		DisplayName: tc.DisplayName,
		WorkflowSteps: tc.WorkflowSteps,
		EscalationThresholdHours: tc.EscalationThresholdHours,
		Name: nilIfEmpty(name),
	}
}

// =============================================================================
// PRECEDESSTEPS TABLE
// Table: PrecedesSteps
// =============================================================================

// PrecedesStep represents a row in the PrecedesSteps table
// Table: PrecedesSteps
type PrecedesStep struct {
	PrecedesStepId string `json:"precedes_step_id"`
	Name *string `json:"name"` // Ordinal sequence number for the relationship. Used for sorting and display.
	WorkflowStep *string `json:"workflow_step"` // Foreign key to the step that comes BEFORE. The source of the 'precedes' relationship.
	StepNumber *int `json:"step_number"`
	DisplayName *string `json:"display_name"`
}

// --- Individual Calculation Functions ---

// CalcDisplayName computes the DisplayName calculated field
// Formula: ="Step-" & {{StepNumber}}
func (tc *PrecedesStep) CalcDisplayName() string {
	return "Step-" + intToString(tc.StepNumber)
}

// --- Compute All Calculated Fields ---

// ComputeAll computes all calculated fields and returns an updated struct
func (tc *PrecedesStep) ComputeAll() *PrecedesStep {
	// Level 1 calculations
	displayName := "Step-" + intToString(tc.StepNumber)

	return &PrecedesStep{
		PrecedesStepId: tc.PrecedesStepId,
		Name: tc.Name,
		WorkflowStep: tc.WorkflowStep,
		StepNumber: tc.StepNumber,
		DisplayName: nilIfEmpty(displayName),
	}
}

// =============================================================================
// ROLES TABLE
// Table: Roles
// =============================================================================

// Role represents a row in the Roles table
// Table: Roles
type Role struct {
	RoleId string `json:"role_id"`
	DisplayName *string `json:"display_name"`
	Label *string `json:"label"` // Human-readable display name. Maps to rdfs:label. Per Heuristic 6: if you cannot write a clear label, you do not yet understand the concept well enough to model it.
	Comment *string `json:"comment"` // Detailed description of the role's responsibilities and scope. Maps to rdfs:comment. Should define what the role covers, what it excludes, and how it differs from adjacent roles.
	FilledByHumanAgent *string `json:"filled_by_human_agent"`
	FilledByAIAgent *string `json:"filled_by_ai_agent"`
	FilledByAutomatedPipeline *string `json:"filled_by_automated_pipeline"`
	OwnedBy *string `json:"owned_by"` // Foreign key to the Department that owns this role. Maps to ntwf:ownedBy (owl:FunctionalProperty). Enables answering CQ7: 'Which workflows involve both Engineering and Legal?'
	DelegatesTo *string `json:"delegates_to"` // Foreign key to the fallback Role in an escalation chain. Maps to ntwf:delegatesTo. Enables answering CQ6: 'What happens when the VP of Engineering is unavailable?'
	WorkflowSteps *string `json:"workflow_steps"` // Back-reference to workflow steps assigned to this role. Inverse of WorkflowSteps.AssignedRole.
	FromDelegatesTo *string `json:"from_delegates_to"`
	Name *string `json:"name"`
}

// --- Individual Calculation Functions ---

// CalcName computes the Name calculated field
// Formula: =LOWER({{DisplayName}})
func (tc *Role) CalcName() string {
	return strings.ToLower(stringVal(tc.DisplayName))
}

// --- Compute All Calculated Fields ---

// ComputeAll computes all calculated fields and returns an updated struct
func (tc *Role) ComputeAll() *Role {
	// Level 1 calculations
	name := strings.ToLower(stringVal(tc.DisplayName))

	return &Role{
		RoleId: tc.RoleId,
		DisplayName: tc.DisplayName,
		Label: tc.Label,
		Comment: tc.Comment,
		FilledByHumanAgent: tc.FilledByHumanAgent,
		FilledByAIAgent: tc.FilledByAIAgent,
		FilledByAutomatedPipeline: tc.FilledByAutomatedPipeline,
		OwnedBy: tc.OwnedBy,
		DelegatesTo: tc.DelegatesTo,
		WorkflowSteps: tc.WorkflowSteps,
		FromDelegatesTo: tc.FromDelegatesTo,
		Name: nilIfEmpty(name),
	}
}

// =============================================================================
// DEPARTMENTS TABLE
// Table: Departments
// =============================================================================

// Department represents a row in the Departments table
// Table: Departments
type Department struct {
	DepartmentId string `json:"department_id"`
	Title *string `json:"title"` // Human-readable display name of the department. Should match organizational terminology for stakeholder communication.
	DisplayName *string `json:"display_name"` // Machine-friendly name for programmatic reference.
	Roles *string `json:"roles"` // Back-reference to roles owned by this department. Inverse of Roles.OwnedBy.
	Name *string `json:"name"` // Human-readable display name of the department. Should match organizational terminology for stakeholder communication.
}

// --- Individual Calculation Functions ---

// CalcName computes the Name calculated field
// Human-readable display name of the department. Should match organizational terminology for stakeholder communication.
// Formula: =SUBSTITUTE(LOWER({{DisplayName}}), " ", "-")
func (tc *Department) CalcName() string {
	return strings.ReplaceAll(strings.ToLower(stringVal(tc.DisplayName)), " ", "-")
}

// --- Compute All Calculated Fields ---

// ComputeAll computes all calculated fields and returns an updated struct
func (tc *Department) ComputeAll() *Department {
	// Level 1 calculations
	name := strings.ReplaceAll(strings.ToLower(stringVal(tc.DisplayName)), " ", "-")

	return &Department{
		DepartmentId: tc.DepartmentId,
		Title: tc.Title,
		DisplayName: tc.DisplayName,
		Roles: tc.Roles,
		Name: nilIfEmpty(name),
	}
}

// =============================================================================
// HUMANAGENTS TABLE
// Table: HumanAgents
// =============================================================================

// HumanAgent represents a row in the HumanAgents table
// Table: HumanAgents
type HumanAgent struct {
	HumanAgentId string `json:"human_agent_id"`
	Name *string `json:"name"` // Full name of the person. Maps to foaf:name. Note: FOAF's name property is appropriate for persons, not for software systems (which use schema:name).
	DisplayName *string `json:"display_name"`
	Mbox *string `json:"mbox"` // Email address of the person. Maps to foaf:mbox. Used for notifications and organizational directory integration.
	Roles *string `json:"roles"` // Back-reference to roles currently filled by this agent. Inverse of Roles.FilledBy_HumanAgent.
}

// =============================================================================
// AIAGENTS TABLE
// Table: AIAgents
// =============================================================================

// AIAgent represents a row in the AIAgents table
// Table: AIAgents
type AIAgent struct {
	AIAgentId string `json:"ai_agent_id"`
	Name *string `json:"name"` // Display name of the AI agent. Maps to schema:name (not foaf:name, which is for persons).
	Title *string `json:"title"`
	DisplayName *string `json:"display_name"`
	ModelVersion *string `json:"model_version"` // Version string of the AI model. Maps to ntwf:modelVersion. Makes AI-produced artifacts auditable at the version level. The domain declaration means this property applies only to AIAgent individuals.
	Roles *string `json:"roles"` // Back-reference to roles currently filled by this AI agent. Inverse of Roles.FilledBy_AIAgent.
}

// =============================================================================
// AUTOMATEDPIPELINES TABLE
// Table: AutomatedPipelines
// =============================================================================

// AutomatedPipeline represents a row in the AutomatedPipelines table
// Table: AutomatedPipelines
type AutomatedPipeline struct {
	AutomatedPipelineId string `json:"automated_pipeline_id"`
	Name *string `json:"name"` // Display name of the pipeline. Maps to schema:name (appropriate for software systems, unlike foaf:name which is for persons).
	Description *string `json:"description"`
	DisplayName *string `json:"display_name"`
	Roles *string `json:"roles"` // Back-reference to roles currently filled by this pipeline. Inverse of Roles.FilledBy_AutomatedPipeline.
}

// =============================================================================
// FILE I/O FUNCTIONS (for all tables with calculated fields)
// =============================================================================

// LoadWorkflowRecords loads Workflows records from a JSON file
func LoadWorkflowRecords(path string) ([]Workflow, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var records []Workflow
	if err := json.Unmarshal(data, &records); err != nil {
		return nil, fmt.Errorf("failed to parse file: %w", err)
	}

	return records, nil
}

// SaveWorkflowRecords saves computed Workflows records to a JSON file
func SaveWorkflowRecords(path string, records []Workflow) error {
	data, err := json.MarshalIndent(records, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal records: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write records: %w", err)
	}

	return nil
}

// LoadWorkflowStepRecords loads WorkflowSteps records from a JSON file
func LoadWorkflowStepRecords(path string) ([]WorkflowStep, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var records []WorkflowStep
	if err := json.Unmarshal(data, &records); err != nil {
		return nil, fmt.Errorf("failed to parse file: %w", err)
	}

	return records, nil
}

// SaveWorkflowStepRecords saves computed WorkflowSteps records to a JSON file
func SaveWorkflowStepRecords(path string, records []WorkflowStep) error {
	data, err := json.MarshalIndent(records, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal records: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write records: %w", err)
	}

	return nil
}

// LoadApprovalGateRecords loads ApprovalGates records from a JSON file
func LoadApprovalGateRecords(path string) ([]ApprovalGate, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var records []ApprovalGate
	if err := json.Unmarshal(data, &records); err != nil {
		return nil, fmt.Errorf("failed to parse file: %w", err)
	}

	return records, nil
}

// SaveApprovalGateRecords saves computed ApprovalGates records to a JSON file
func SaveApprovalGateRecords(path string, records []ApprovalGate) error {
	data, err := json.MarshalIndent(records, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal records: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write records: %w", err)
	}

	return nil
}

// LoadPrecedesStepRecords loads PrecedesSteps records from a JSON file
func LoadPrecedesStepRecords(path string) ([]PrecedesStep, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var records []PrecedesStep
	if err := json.Unmarshal(data, &records); err != nil {
		return nil, fmt.Errorf("failed to parse file: %w", err)
	}

	return records, nil
}

// SavePrecedesStepRecords saves computed PrecedesSteps records to a JSON file
func SavePrecedesStepRecords(path string, records []PrecedesStep) error {
	data, err := json.MarshalIndent(records, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal records: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write records: %w", err)
	}

	return nil
}

// LoadRoleRecords loads Roles records from a JSON file
func LoadRoleRecords(path string) ([]Role, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var records []Role
	if err := json.Unmarshal(data, &records); err != nil {
		return nil, fmt.Errorf("failed to parse file: %w", err)
	}

	return records, nil
}

// SaveRoleRecords saves computed Roles records to a JSON file
func SaveRoleRecords(path string, records []Role) error {
	data, err := json.MarshalIndent(records, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal records: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write records: %w", err)
	}

	return nil
}

// LoadDepartmentRecords loads Departments records from a JSON file
func LoadDepartmentRecords(path string) ([]Department, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var records []Department
	if err := json.Unmarshal(data, &records); err != nil {
		return nil, fmt.Errorf("failed to parse file: %w", err)
	}

	return records, nil
}

// SaveDepartmentRecords saves computed Departments records to a JSON file
func SaveDepartmentRecords(path string, records []Department) error {
	data, err := json.MarshalIndent(records, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal records: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write records: %w", err)
	}

	return nil
}
