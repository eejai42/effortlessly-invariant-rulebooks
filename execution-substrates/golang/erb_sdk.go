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
// APPUSERS TABLE
// Table: AppUsers
// =============================================================================

// AppUser represents a row in the AppUsers table
// Table: AppUsers
type AppUser struct {
	AppUserId string `json:"app_user_id"`
	Name *string `json:"name"`
	EmailAddress *string `json:"email_address"`
	Role *string `json:"role"`
	IsActive *bool `json:"is_active"`
	Widgets *string `json:"widgets"`
	Notes *string `json:"notes"`
}

// =============================================================================
// SHAPES TABLE
// Table: Shapes
// =============================================================================

// Shape represents a row in the Shapes table
// Table: Shapes
type Shape struct {
	ShapeId string `json:"shape_id"`
	Name *string `json:"name"`
	Sides *string `json:"sides"`
	HowManySides *int `json:"how_many_sides"`
	SumOfInternalAngles *FlexibleString `json:"sum_of_internal_angles"`
	MaxAngle *string `json:"max_angle"`
	HypotenuseLengthSquared *FlexibleString `json:"hypotenuse_length_squared"`
	NonHypotenuseSidesSquared *FlexibleString `json:"non_hypotenuse_sides_squared"`
	IsRectangle *bool `json:"is_rectangle"`
	IsTriangle *bool `json:"is_triangle"`
	IsRightTriangle *bool `json:"is_right_triangle"`
	PythagoreanTheoremHolds *bool `json:"pythagorean_theorem_holds"`
}

// --- Individual Calculation Functions ---

// CalcIsRectangle computes the IsRectangle calculated field
// Formula: =AND({{HowManySides}}=4)
func (tc *Shape) CalcIsRectangle() bool {
	return ((tc.HowManySides != nil && *tc.HowManySides == 4))
}

// CalcIsTriangle computes the IsTriangle calculated field
// Formula: =AND({{SumOfInternalAngles}}=180, {{HowManySides}}=3)
func (tc *Shape) CalcIsTriangle() bool {
	return ((tc.SumOfInternalAngles != nil && *tc.SumOfInternalAngles == 180) && (tc.HowManySides != nil && *tc.HowManySides == 3))
}

// CalcIsRightTriangle computes the IsRightTriangle calculated field
// Formula: =AND({{IsTriangle}}, {{MaxAngle}} = 90)
func (tc *Shape) CalcIsRightTriangle() bool {
	return (boolVal(tc.IsTriangle) && (tc.MaxAngle != nil && *tc.MaxAngle == 90))
}

// CalcPythagoreanTheoremHolds computes the PythagoreanTheoremHolds calculated field
// Formula: =AND(   {{IsRightTriangle}},     {{HypotenuseLengthSquared}} = {{NonHypotenuseSidesSquared}} )
func (tc *Shape) CalcPythagoreanTheoremHolds() bool {
	return (boolVal(tc.IsRightTriangle) && (boolVal(tc.HypotenuseLengthSquared) == boolVal(tc.NonHypotenuseSidesSquared)))
}

// --- Compute All Calculated Fields ---

// ComputeAll computes all calculated fields and returns an updated struct
func (tc *Shape) ComputeAll() *Shape {
	// Level 1 calculations
	isRectangle := ((tc.HowManySides != nil && *tc.HowManySides == 4))
	isTriangle := ((tc.SumOfInternalAngles != nil && *tc.SumOfInternalAngles == 180) && (tc.HowManySides != nil && *tc.HowManySides == 3))

	// Level 2 calculations
	isRightTriangle := (isTriangle && (tc.MaxAngle != nil && *tc.MaxAngle == 90))

	// Level 3 calculations
	pythagoreanTheoremHolds := (isRightTriangle && (boolVal(tc.HypotenuseLengthSquared) == boolVal(tc.NonHypotenuseSidesSquared)))

	return &Shape{
		ShapeId: tc.ShapeId,
		Name: tc.Name,
		Sides: tc.Sides,
		HowManySides: tc.HowManySides,
		SumOfInternalAngles: tc.SumOfInternalAngles,
		MaxAngle: tc.MaxAngle,
		HypotenuseLengthSquared: tc.HypotenuseLengthSquared,
		NonHypotenuseSidesSquared: tc.NonHypotenuseSidesSquared,
		IsRectangle: &isRectangle,
		IsTriangle: &isTriangle,
		IsRightTriangle: &isRightTriangle,
		PythagoreanTheoremHolds: &pythagoreanTheoremHolds,
	}
}

// =============================================================================
// SIDES TABLE
// Table: Sides
// =============================================================================

// Side represents a row in the Sides table
// Table: Sides
type Side struct {
	SideId string `json:"side_id"`
	ShapeSides *int `json:"shape_sides"`
	Label *string `json:"label"` // Label for this edge
	IsRectangle *bool `json:"is_rectangle"`
	IsTriangle *bool `json:"is_triangle"`
	IsRightTriangle *bool `json:"is_right_triangle"` // Is this the Hypotenuse of a Right Angle Triangle?
	PythagoreanTheoremHolds *bool `json:"pythagorean_theorem_holds"` // Does the Pythagorean Theorem Hold?
	PreviousSideLength *int `json:"previous_side_length"` // Previous Edge Length
	Length *int `json:"length"` // Length
	NextLength *int `json:"next_length"` // Next Edge Length
	PreviousAngle *int `json:"previous_angle"` // Previous Angle
	Angle *int `json:"angle"` // Internal angles for the shapes
	NextAngle *int `json:"next_angle"` // Next Angle
	PreviousSide *string `json:"previous_side"` // Previous Edge
	NextSide *string `json:"next_side"` // Next Edge
	Shape *string `json:"shape"` // Shape
	PreviousLabel *string `json:"previous_label"`
	NextLabel *string `json:"next_label"`
	Name *string `json:"name"`
	IsHypotenuse *bool `json:"is_hypotenuse"` // Is this the Hypotenuse of a Right Angle Triangle?
	StatusOfTheorem *string `json:"status_of_theorem"` // Invalid if it is a Triangle with Mismatchd Edge Lengths and Angles.
	LengthSquared *int `json:"length_squared"`
	HypotenuseLengthSquared *int `json:"hypotenuse_length_squared"`
	NonHypotenuseLengthSquared *int `json:"non_hypotenuse_length_squared"`
}

// --- Individual Calculation Functions ---

// CalcName computes the Name calculated field
// Formula: ={{Shape}} & "-Side-" & {{Label}}
func (tc *Side) CalcName() string {
	return stringVal(tc.Shape) + "-Side-" + stringVal(tc.Label)
}

// CalcIsHypotenuse computes the IsHypotenuse calculated field
// Is this the Hypotenuse of a Right Angle Triangle?
// Formula: =AND(   {{IsTriangle}},   {{Length}} > {{PreviousSideLength}},   {{Length}} > {{NextLength}} )
func (tc *Side) CalcIsHypotenuse() bool {
	return (boolVal(tc.IsTriangle) && (boolVal(tc.Length) > boolVal(tc.PreviousSideLength)) && (boolVal(tc.Length) > boolVal(tc.NextLength)))
}

// CalcStatusOfTheorem computes the StatusOfTheorem calculated field
// Invalid if it is a Triangle with Mismatchd Edge Lengths and Angles.
// Formula: =IF({{IsTriangle}},    IF(AND({{IsRightTriangle}}, NOT({{PythagoreanTheoremHolds}})),      "PYTHAGOREAN THEOREM FALSIFIED!",      "Pythagorean Theorem Holds (obviously)."   ),   "NA" )
func (tc *Side) CalcStatusOfTheorem() string {
	return func() string { if boolVal(tc.IsTriangle) { return func() string { if (boolVal(tc.IsRightTriangle) && !boolVal(tc.PythagoreanTheoremHolds)) { return "PYTHAGOREAN THEOREM FALSIFIED!" }; return "Pythagorean Theorem Holds (obviously)." }() }; return "NA" }()
}

// CalcLengthSquared computes the LengthSquared calculated field
// Formula: ={{Length}} * {{Length}}
func (tc *Side) CalcLengthSquared() int {
	return func() interface{} { panic("Formula parse error: Unexpected character '*' at position 11") }()
}

// CalcHypotenuseLengthSquared computes the HypotenuseLengthSquared calculated field
// Formula: =IF({{IsHypotenuse}}, {{LengthSquared}})
func (tc *Side) CalcHypotenuseLengthSquared() int {
	return func() string { if boolVal(tc.IsHypotenuse) { return tc.LengthSquared }; return "" }()
}

// CalcNonHypotenuseLengthSquared computes the NonHypotenuseLengthSquared calculated field
// Formula: =IF(AND(NOT({{IsHypotenuse}}), {{IsTriangle}}), {{LengthSquared}})
func (tc *Side) CalcNonHypotenuseLengthSquared() int {
	return func() string { if (!boolVal(tc.IsHypotenuse) && boolVal(tc.IsTriangle)) { return tc.LengthSquared }; return "" }()
}

// --- Compute All Calculated Fields ---

// ComputeAll computes all calculated fields and returns an updated struct
func (tc *Side) ComputeAll() *Side {
	// Level 1 calculations
	name := stringVal(tc.Shape) + "-Side-" + stringVal(tc.Label)
	isHypotenuse := (boolVal(tc.IsTriangle) && (boolVal(tc.Length) > boolVal(tc.PreviousSideLength)) && (boolVal(tc.Length) > boolVal(tc.NextLength)))
	statusOfTheorem := func() string { if boolVal(tc.IsTriangle) { return func() string { if (boolVal(tc.IsRightTriangle) && !boolVal(tc.PythagoreanTheoremHolds)) { return "PYTHAGOREAN THEOREM FALSIFIED!" }; return "Pythagorean Theorem Holds (obviously)." }() }; return "NA" }()
	lengthSquared := func() interface{} { panic("Formula parse error: Unexpected character '*' at position 11") }()

	// Level 2 calculations
	hypotenuseLengthSquared := func() string { if isHypotenuse { return lengthSquared }; return "" }()
	nonHypotenuseLengthSquared := func() string { if (!isHypotenuse && boolVal(tc.IsTriangle)) { return lengthSquared }; return "" }()

	return &Side{
		SideId: tc.SideId,
		ShapeSides: tc.ShapeSides,
		Label: tc.Label,
		IsRectangle: tc.IsRectangle,
		IsTriangle: tc.IsTriangle,
		IsRightTriangle: tc.IsRightTriangle,
		PythagoreanTheoremHolds: tc.PythagoreanTheoremHolds,
		PreviousSideLength: tc.PreviousSideLength,
		Length: tc.Length,
		NextLength: tc.NextLength,
		PreviousAngle: tc.PreviousAngle,
		Angle: tc.Angle,
		NextAngle: tc.NextAngle,
		PreviousSide: tc.PreviousSide,
		NextSide: tc.NextSide,
		Shape: tc.Shape,
		PreviousLabel: tc.PreviousLabel,
		NextLabel: tc.NextLabel,
		Name: nilIfEmpty(name),
		IsHypotenuse: &isHypotenuse,
		StatusOfTheorem: nilIfEmpty(statusOfTheorem),
		LengthSquared: &lengthSquared,
		HypotenuseLengthSquared: &hypotenuseLengthSquared,
		NonHypotenuseLengthSquared: &nonHypotenuseLengthSquared,
	}
}

// =============================================================================
// WIDGETS TABLE
// Table: Widgets
// =============================================================================

// Widget represents a row in the Widgets table
// Table: Widgets
type Widget struct {
	WidgetId string `json:"widget_id"`
	Name *string `json:"name"`
	Appuser *string `json:"appuser"`
	Name_from_Appuser *string `json:"name_from_appuser"`
	EmailAddress_from_Appuser *string `json:"email_address_from_appuser"`
	Role_from_Appuser *string `json:"role_from_appuser"`
	Color *string `json:"color"`
}

// =============================================================================
// ERBVERSIONS TABLE
// Table: ERBVersions
// =============================================================================

// ERBVersion represents a row in the ERBVersions table
// Table: ERBVersions
type ERBVersion struct {
	ERBVersionId string `json:"erb_version_id"`
	BaseId *string `json:"base_id"`
	Name *string `json:"name"`
	Message *string `json:"message"`
	Notes *string `json:"notes"`
	CommitDate *string `json:"commit_date"`
	IsPublished *bool `json:"is_published"`
	PK *string `json:"pk"`
}

// --- Individual Calculation Functions ---

// CalcPK computes the PK calculated field
// Formula: ={{BaseId}} & "-" & {{Name}}
func (tc *ERBVersion) CalcPK() string {
	return stringVal(tc.BaseId) + "-" + stringVal(tc.Name)
}

// --- Compute All Calculated Fields ---

// ComputeAll computes all calculated fields and returns an updated struct
func (tc *ERBVersion) ComputeAll() *ERBVersion {
	// Level 1 calculations
	pK := stringVal(tc.BaseId) + "-" + stringVal(tc.Name)

	return &ERBVersion{
		ERBVersionId: tc.ERBVersionId,
		BaseId: tc.BaseId,
		Name: tc.Name,
		Message: tc.Message,
		Notes: tc.Notes,
		CommitDate: tc.CommitDate,
		IsPublished: tc.IsPublished,
		PK: nilIfEmpty(pK),
	}
}

// =============================================================================
// ERBCUSTOMIZATIONS TABLE
// Table: ERBCustomizations
// =============================================================================

// ERBCustomization represents a row in the ERBCustomizations table
// Table: ERBCustomizations
type ERBCustomization struct {
	ERBCustomizationId string `json:"erb_customization_id"`
	Name *string `json:"name"`
	Title *string `json:"title"`
	SQLCode *string `json:"sql_code"`
	SQLTarget *string `json:"sql_target"`
	CustomizationType *string `json:"customization_type"`
}

// =============================================================================
// MAGICLINKINTEGRATION TABLE
// Table: MagicLinkIntegration
// =============================================================================

// MagicLinkIntegration represents a row in the MagicLinkIntegration table
// Table: MagicLinkIntegration
type MagicLinkIntegration struct {
	MagicLinkIntegrationId string `json:"magic_link_integration_id"`
	Name *string `json:"name"`
	Enabled *bool `json:"enabled"`
	TenantId *string `json:"tenant_id"`
	PublicKeyPem *string `json:"public_key_pem"`
	UserTableName *string `json:"user_table_name"`
	EmailField *string `json:"email_field"`
	RoleField *string `json:"role_field"`
	IsActiveField *string `json:"is_active_field"`
	UserIdField *string `json:"user_id_field"`
	AllowedAlgorithms *string `json:"allowed_algorithms"`
	RequireTenantBinding *bool `json:"require_tenant_binding"`
	UseEmailDagPattern *bool `json:"use_email_dag_pattern"`
}

// =============================================================================
// FILE I/O FUNCTIONS (for all tables with calculated fields)
// =============================================================================

// LoadShapeRecords loads Shapes records from a JSON file
func LoadShapeRecords(path string) ([]Shape, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var records []Shape
	if err := json.Unmarshal(data, &records); err != nil {
		return nil, fmt.Errorf("failed to parse file: %w", err)
	}

	return records, nil
}

// SaveShapeRecords saves computed Shapes records to a JSON file
func SaveShapeRecords(path string, records []Shape) error {
	data, err := json.MarshalIndent(records, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal records: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write records: %w", err)
	}

	return nil
}

// LoadSideRecords loads Sides records from a JSON file
func LoadSideRecords(path string) ([]Side, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var records []Side
	if err := json.Unmarshal(data, &records); err != nil {
		return nil, fmt.Errorf("failed to parse file: %w", err)
	}

	return records, nil
}

// SaveSideRecords saves computed Sides records to a JSON file
func SaveSideRecords(path string, records []Side) error {
	data, err := json.MarshalIndent(records, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal records: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write records: %w", err)
	}

	return nil
}

// LoadWidgetRecords loads Widgets records from a JSON file
func LoadWidgetRecords(path string) ([]Widget, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var records []Widget
	if err := json.Unmarshal(data, &records); err != nil {
		return nil, fmt.Errorf("failed to parse file: %w", err)
	}

	return records, nil
}

// SaveWidgetRecords saves computed Widgets records to a JSON file
func SaveWidgetRecords(path string, records []Widget) error {
	data, err := json.MarshalIndent(records, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal records: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write records: %w", err)
	}

	return nil
}

// LoadERBVersionRecords loads ERBVersions records from a JSON file
func LoadERBVersionRecords(path string) ([]ERBVersion, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var records []ERBVersion
	if err := json.Unmarshal(data, &records); err != nil {
		return nil, fmt.Errorf("failed to parse file: %w", err)
	}

	return records, nil
}

// SaveERBVersionRecords saves computed ERBVersions records to a JSON file
func SaveERBVersionRecords(path string, records []ERBVersion) error {
	data, err := json.MarshalIndent(records, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal records: %w", err)
	}

	if err := os.WriteFile(path, data, 0644); err != nil {
		return fmt.Errorf("failed to write records: %w", err)
	}

	return nil
}
