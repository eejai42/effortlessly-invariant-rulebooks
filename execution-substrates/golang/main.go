// ERB SDK - Go Test Runner (GENERATED - DO NOT EDIT)
// =======================================================
// This file is REGENERATED every time inject-into-golang.py runs.
// It must stay in sync with erb_sdk.go and the rulebook.
//
// Tables with computed fields: Shapes, Sides, Widgets, ERBVersions
// Tables with aggregations: Shapes
// Tables with lookups: Sides, Widgets
//
// IMPORTANT: This runner processes ALL tables, not just a "primary" one.
// If ANY table fails to process, the entire run fails with exit code 1.

package main

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
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

	fmt.Println("Golang substrate: Processing 4 tables with calculated fields...")
	fmt.Println("  Expected tables: Shapes, Sides, Widgets, ERBVersions")
	fmt.Println("")

	// Track success/failure for ALL tables
	var errors []string
	var totalRecords int

	// ─────────────────────────────────────────────────────────────────
	// Load related tables for aggregation calculations
	// ─────────────────────────────────────────────────────────────────
	// Note: SUMIFS loads from answer-keys (has computed fields)
	//       COUNTIFS loads from blank-tests
	answerKeysDir := filepath.Join(scriptDir, "..", "..", "testing", "answer-keys")

	app_usersData, err := LoadAppUserRecords(filepath.Join(blankTestsDir, "app_users.json"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "Warning: Could not load AppUsers for aggregations: %v\n", err)
		app_usersData = nil
	}
	shapesData, err := LoadShapeRecords(filepath.Join(blankTestsDir, "shapes.json"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "Warning: Could not load Shapes for aggregations: %v\n", err)
		shapesData = nil
	}
	sidesData, err := LoadSideRecords(filepath.Join(answerKeysDir, "sides.json"))
	if err != nil {
		fmt.Fprintf(os.Stderr, "Warning: Could not load Sides for aggregations: %v\n", err)
		sidesData = nil
	}

	// ─────────────────────────────────────────────────────────────────
	// Process Shapes
	// ─────────────────────────────────────────────────────────────────
	fmt.Println("Processing Shapes...")
	shapesInput := filepath.Join(blankTestsDir, "shapes.json")
	shapesOutput := filepath.Join(testAnswersDir, "shapes.json")

	shapesRecords, err := LoadShapeRecords(shapesInput)
	if err != nil {
		errMsg := fmt.Sprintf("Shapes: failed to load - %v", err)
		fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
		errors = append(errors, errMsg)
	} else {
		// Compute aggregations for Shapes
		how_many_sidesCountMap := make(map[string]int)
		if sidesData != nil {
			for _, rel := range sidesData {
				if rel.Shape != nil {
					how_many_sidesCountMap[*rel.Shape]++
				}
			}
		}

		sum_of_internal_anglesLookupMap := make(map[string]string)
		if sidesData != nil {
			for _, rel := range sidesData {
				var val string
				if rel.Angle != nil {
					val = fmt.Sprintf("%s", *rel.Angle)
				}
				// Include all entries (even empty) to maintain position correspondence
				sum_of_internal_anglesLookupMap[rel.SideId] = val
			}
		}

		hypotenuse_length_squaredLookupMap := make(map[string]string)
		if sidesData != nil {
			for _, rel := range sidesData {
				var val string
				if rel.HypotenuseLengthSquared != nil {
					val = fmt.Sprintf("%s", *rel.HypotenuseLengthSquared)
				}
				// Include all entries (even empty) to maintain position correspondence
				hypotenuse_length_squaredLookupMap[rel.SideId] = val
			}
		}

		non_hypotenuse_sides_squaredLookupMap := make(map[string]string)
		if sidesData != nil {
			for _, rel := range sidesData {
				var val string
				if rel.NonHypotenuseLengthSquared != nil {
					val = fmt.Sprintf("%s", *rel.NonHypotenuseLengthSquared)
				}
				// Include all entries (even empty) to maintain position correspondence
				non_hypotenuse_sides_squaredLookupMap[rel.SideId] = val
			}
		}

		// Update records with aggregation values
		for i := range shapesRecords {
			if shapesRecords[i].ShapeId != "" {
				count := how_many_sidesCountMap[shapesRecords[i].ShapeId]
				shapesRecords[i].HowManySides = &count
			}
			if shapesRecords[i].Sides != nil && *shapesRecords[i].Sides != "" {
				// Parse relationship field to get ordered PKs
				relPKs := strings.Split(*shapesRecords[i].Sides, ", ")
				var values []string
				for _, pk := range relPKs {
					pk = strings.TrimSpace(pk)
					if val, ok := sum_of_internal_anglesLookupMap[pk]; ok {
						values = append(values, val)
					}
				}
				if len(values) > 0 {
					joined := FlexibleString(strings.Join(values, ", "))
					shapesRecords[i].SumOfInternalAngles = &joined
				} else {
					zero := FlexibleString("0")
					shapesRecords[i].SumOfInternalAngles = &zero
				}
			} else {
				zero := FlexibleString("0")
				shapesRecords[i].SumOfInternalAngles = &zero
			}
			if shapesRecords[i].Sides != nil && *shapesRecords[i].Sides != "" {
				// Parse relationship field to get ordered PKs
				relPKs := strings.Split(*shapesRecords[i].Sides, ", ")
				var values []string
				for _, pk := range relPKs {
					pk = strings.TrimSpace(pk)
					if val, ok := hypotenuse_length_squaredLookupMap[pk]; ok {
						values = append(values, val)
					}
				}
				if len(values) > 0 {
					joined := FlexibleString(strings.Join(values, ", "))
					shapesRecords[i].HypotenuseLengthSquared = &joined
				} else {
					zero := FlexibleString("0")
					shapesRecords[i].HypotenuseLengthSquared = &zero
				}
			} else {
				zero := FlexibleString("0")
				shapesRecords[i].HypotenuseLengthSquared = &zero
			}
			if shapesRecords[i].Sides != nil && *shapesRecords[i].Sides != "" {
				// Parse relationship field to get ordered PKs
				relPKs := strings.Split(*shapesRecords[i].Sides, ", ")
				var values []string
				for _, pk := range relPKs {
					pk = strings.TrimSpace(pk)
					if val, ok := non_hypotenuse_sides_squaredLookupMap[pk]; ok {
						values = append(values, val)
					}
				}
				if len(values) > 0 {
					joined := FlexibleString(strings.Join(values, ", "))
					shapesRecords[i].NonHypotenuseSidesSquared = &joined
				} else {
					zero := FlexibleString("0")
					shapesRecords[i].NonHypotenuseSidesSquared = &zero
				}
			} else {
				zero := FlexibleString("0")
				shapesRecords[i].NonHypotenuseSidesSquared = &zero
			}
		}

		var computedShape []Shape
		for _, r := range shapesRecords {
			computedShape = append(computedShape, *r.ComputeAll())
		}

		if err := SaveShapeRecords(shapesOutput, computedShape); err != nil {
			errMsg := fmt.Sprintf("Shapes: failed to save - %v", err)
			fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
			errors = append(errors, errMsg)
		} else {
			fmt.Printf("  ✓ shapes: %d records processed\n", len(computedShape))
			totalRecords += len(computedShape)
		}
	}
	fmt.Println("")

	// ─────────────────────────────────────────────────────────────────
	// Process Sides
	// ─────────────────────────────────────────────────────────────────
	fmt.Println("Processing Sides...")
	sidesInput := filepath.Join(blankTestsDir, "sides.json")
	sidesOutput := filepath.Join(testAnswersDir, "sides.json")

	sidesRecords, err := LoadSideRecords(sidesInput)
	if err != nil {
		errMsg := fmt.Sprintf("Sides: failed to load - %v", err)
		fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
		errors = append(errors, errMsg)
	} else {
		// Compute lookups for Sides
		shape_sidesLookupMap := make(map[string]string)
		if shapesData != nil {
			for _, rel := range shapesData {
				if rel.ShapeId != "" {
					var val string
					if rel.HowManySides != nil {
						val = *rel.HowManySides
					}
					shape_sidesLookupMap[rel.ShapeId] = val
				}
			}
		}

		is_rectangleLookupMap := make(map[string]string)
		if shapesData != nil {
			for _, rel := range shapesData {
				if rel.ShapeId != "" {
					var val string
					if rel.IsRectangle != nil {
						val = *rel.IsRectangle
					}
					is_rectangleLookupMap[rel.ShapeId] = val
				}
			}
		}

		is_triangleLookupMap := make(map[string]string)
		if shapesData != nil {
			for _, rel := range shapesData {
				if rel.ShapeId != "" {
					var val string
					if rel.IsTriangle != nil {
						val = *rel.IsTriangle
					}
					is_triangleLookupMap[rel.ShapeId] = val
				}
			}
		}

		is_right_triangleLookupMap := make(map[string]string)
		if shapesData != nil {
			for _, rel := range shapesData {
				if rel.ShapeId != "" {
					var val string
					if rel.IsRightTriangle != nil {
						val = *rel.IsRightTriangle
					}
					is_right_triangleLookupMap[rel.ShapeId] = val
				}
			}
		}

		pythagorean_theorem_holdsLookupMap := make(map[string]string)
		if shapesData != nil {
			for _, rel := range shapesData {
				if rel.ShapeId != "" {
					var val string
					if rel.PythagoreanTheoremHolds != nil {
						val = *rel.PythagoreanTheoremHolds
					}
					pythagorean_theorem_holdsLookupMap[rel.ShapeId] = val
				}
			}
		}

		previous_side_lengthLookupMap := make(map[string]string)
		if sidesData != nil {
			for _, rel := range sidesData {
				if rel.SideId != "" {
					var val string
					if rel.Length != nil {
						val = *rel.Length
					}
					previous_side_lengthLookupMap[rel.SideId] = val
				}
			}
		}

		next_lengthLookupMap := make(map[string]string)
		if sidesData != nil {
			for _, rel := range sidesData {
				if rel.SideId != "" {
					var val string
					if rel.Length != nil {
						val = *rel.Length
					}
					next_lengthLookupMap[rel.SideId] = val
				}
			}
		}

		previous_angleLookupMap := make(map[string]string)
		if sidesData != nil {
			for _, rel := range sidesData {
				if rel.SideId != "" {
					var val string
					if rel.Angle != nil {
						val = *rel.Angle
					}
					previous_angleLookupMap[rel.SideId] = val
				}
			}
		}

		next_angleLookupMap := make(map[string]string)
		if sidesData != nil {
			for _, rel := range sidesData {
				if rel.SideId != "" {
					var val string
					if rel.Angle != nil {
						val = *rel.Angle
					}
					next_angleLookupMap[rel.SideId] = val
				}
			}
		}

		previous_labelLookupMap := make(map[string]string)
		if sidesData != nil {
			for _, rel := range sidesData {
				if rel.SideId != "" {
					var val string
					if rel.Label != nil {
						val = *rel.Label
					}
					previous_labelLookupMap[rel.SideId] = val
				}
			}
		}

		next_labelLookupMap := make(map[string]string)
		if sidesData != nil {
			for _, rel := range sidesData {
				if rel.SideId != "" {
					var val string
					if rel.Label != nil {
						val = *rel.Label
					}
					next_labelLookupMap[rel.SideId] = val
				}
			}
		}

		// Apply lookup values to records
		for i := range sidesRecords {
			if sidesRecords[i].Shape != nil && *sidesRecords[i].Shape != "" {
				if val, ok := shape_sidesLookupMap[*sidesRecords[i].Shape]; ok {
					sidesRecords[i].ShapeSides = &val
				}
			}
			if sidesRecords[i].Shape != nil && *sidesRecords[i].Shape != "" {
				if val, ok := is_rectangleLookupMap[*sidesRecords[i].Shape]; ok {
					sidesRecords[i].IsRectangle = &val
				}
			}
			if sidesRecords[i].Shape != nil && *sidesRecords[i].Shape != "" {
				if val, ok := is_triangleLookupMap[*sidesRecords[i].Shape]; ok {
					sidesRecords[i].IsTriangle = &val
				}
			}
			if sidesRecords[i].Shape != nil && *sidesRecords[i].Shape != "" {
				if val, ok := is_right_triangleLookupMap[*sidesRecords[i].Shape]; ok {
					sidesRecords[i].IsRightTriangle = &val
				}
			}
			if sidesRecords[i].Shape != nil && *sidesRecords[i].Shape != "" {
				if val, ok := pythagorean_theorem_holdsLookupMap[*sidesRecords[i].Shape]; ok {
					sidesRecords[i].PythagoreanTheoremHolds = &val
				}
			}
			if sidesRecords[i].PreviousSide != nil && *sidesRecords[i].PreviousSide != "" {
				if val, ok := previous_side_lengthLookupMap[*sidesRecords[i].PreviousSide]; ok {
					sidesRecords[i].PreviousSideLength = &val
				}
			}
			if sidesRecords[i].NextSide != nil && *sidesRecords[i].NextSide != "" {
				if val, ok := next_lengthLookupMap[*sidesRecords[i].NextSide]; ok {
					sidesRecords[i].NextLength = &val
				}
			}
			if sidesRecords[i].PreviousSide != nil && *sidesRecords[i].PreviousSide != "" {
				if val, ok := previous_angleLookupMap[*sidesRecords[i].PreviousSide]; ok {
					sidesRecords[i].PreviousAngle = &val
				}
			}
			if sidesRecords[i].NextSide != nil && *sidesRecords[i].NextSide != "" {
				if val, ok := next_angleLookupMap[*sidesRecords[i].NextSide]; ok {
					sidesRecords[i].NextAngle = &val
				}
			}
			if sidesRecords[i].PreviousSide != nil && *sidesRecords[i].PreviousSide != "" {
				if val, ok := previous_labelLookupMap[*sidesRecords[i].PreviousSide]; ok {
					sidesRecords[i].PreviousLabel = &val
				}
			}
			if sidesRecords[i].NextSide != nil && *sidesRecords[i].NextSide != "" {
				if val, ok := next_labelLookupMap[*sidesRecords[i].NextSide]; ok {
					sidesRecords[i].NextLabel = &val
				}
			}
		}

		var computedSide []Side
		for _, r := range sidesRecords {
			computedSide = append(computedSide, *r.ComputeAll())
		}

		if err := SaveSideRecords(sidesOutput, computedSide); err != nil {
			errMsg := fmt.Sprintf("Sides: failed to save - %v", err)
			fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
			errors = append(errors, errMsg)
		} else {
			fmt.Printf("  ✓ sides: %d records processed\n", len(computedSide))
			totalRecords += len(computedSide)
		}
	}
	fmt.Println("")

	// ─────────────────────────────────────────────────────────────────
	// Process Widgets
	// ─────────────────────────────────────────────────────────────────
	fmt.Println("Processing Widgets...")
	widgetsInput := filepath.Join(blankTestsDir, "widgets.json")
	widgetsOutput := filepath.Join(testAnswersDir, "widgets.json")

	widgetsRecords, err := LoadWidgetRecords(widgetsInput)
	if err != nil {
		errMsg := fmt.Sprintf("Widgets: failed to load - %v", err)
		fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
		errors = append(errors, errMsg)
	} else {
		// Compute lookups for Widgets
		name_from_appuserLookupMap := make(map[string]string)
		if app_usersData != nil {
			for _, rel := range app_usersData {
				if rel.AppUserId != "" {
					var val string
					if rel.Name != nil {
						val = *rel.Name
					}
					name_from_appuserLookupMap[rel.AppUserId] = val
				}
			}
		}

		email_address_from_appuserLookupMap := make(map[string]string)
		if app_usersData != nil {
			for _, rel := range app_usersData {
				if rel.AppUserId != "" {
					var val string
					if rel.EmailAddress != nil {
						val = *rel.EmailAddress
					}
					email_address_from_appuserLookupMap[rel.AppUserId] = val
				}
			}
		}

		role_from_appuserLookupMap := make(map[string]string)
		if app_usersData != nil {
			for _, rel := range app_usersData {
				if rel.AppUserId != "" {
					var val string
					if rel.Role != nil {
						val = *rel.Role
					}
					role_from_appuserLookupMap[rel.AppUserId] = val
				}
			}
		}

		// Apply lookup values to records
		for i := range widgetsRecords {
			if widgetsRecords[i].Appuser != nil && *widgetsRecords[i].Appuser != "" {
				if val, ok := name_from_appuserLookupMap[*widgetsRecords[i].Appuser]; ok {
					widgetsRecords[i].Name_from_Appuser = &val
				}
			}
			if widgetsRecords[i].Appuser != nil && *widgetsRecords[i].Appuser != "" {
				if val, ok := email_address_from_appuserLookupMap[*widgetsRecords[i].Appuser]; ok {
					widgetsRecords[i].EmailAddress_from_Appuser = &val
				}
			}
			if widgetsRecords[i].Appuser != nil && *widgetsRecords[i].Appuser != "" {
				if val, ok := role_from_appuserLookupMap[*widgetsRecords[i].Appuser]; ok {
					widgetsRecords[i].Role_from_Appuser = &val
				}
			}
		}

		var computedWidget []Widget
		for _, r := range widgetsRecords {
			computedWidget = append(computedWidget, r)
		}

		if err := SaveWidgetRecords(widgetsOutput, computedWidget); err != nil {
			errMsg := fmt.Sprintf("Widgets: failed to save - %v", err)
			fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
			errors = append(errors, errMsg)
		} else {
			fmt.Printf("  ✓ widgets: %d records processed\n", len(computedWidget))
			totalRecords += len(computedWidget)
		}
	}
	fmt.Println("")

	// ─────────────────────────────────────────────────────────────────
	// Process ERBVersions
	// ─────────────────────────────────────────────────────────────────
	fmt.Println("Processing ERBVersions...")
	erb_versionsInput := filepath.Join(blankTestsDir, "erb_versions.json")
	erb_versionsOutput := filepath.Join(testAnswersDir, "erb_versions.json")

	erb_versionsRecords, err := LoadERBVersionRecords(erb_versionsInput)
	if err != nil {
		errMsg := fmt.Sprintf("ERBVersions: failed to load - %v", err)
		fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
		errors = append(errors, errMsg)
	} else {
		var computedERBVersion []ERBVersion
		for _, r := range erb_versionsRecords {
			computedERBVersion = append(computedERBVersion, *r.ComputeAll())
		}

		if err := SaveERBVersionRecords(erb_versionsOutput, computedERBVersion); err != nil {
			errMsg := fmt.Sprintf("ERBVersions: failed to save - %v", err)
			fmt.Fprintf(os.Stderr, "ERROR: %s\n", errMsg)
			errors = append(errors, errMsg)
		} else {
			fmt.Printf("  ✓ erb_versions: %d records processed\n", len(computedERBVersion))
			totalRecords += len(computedERBVersion)
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
	fmt.Printf("Golang substrate: ALL %d tables processed successfully (%d total records)\n", 4, totalRecords)
	fmt.Println("════════════════════════════════════════════════════════════════")
}