#!/bin/bash

# take-test.sh for english execution substrate
# Executes the English substrate using LLM to produce test answers
#
# This substrate uses an LLM (OpenAI) to "execute" English specifications.
#
# TIMING PRESERVATION:
#   When user skips re-taking the test, we output SUBSTRATE_SKIPPED_BUT_GRADE
#   which tells the orchestrator to:
#   1. Still grade the test (using restored previous answers)
#   2. Preserve the timing from the last successful run
#
# The English substrate reads from:
#   - specification.md (calculation instructions in plain English)
# And writes test answers to:
#   - test-answers/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="$SCRIPT_DIR/.last-run.log"
LAST_RUN_ANSWERS="$SCRIPT_DIR/.last-run-answers"

# Flags to track user choices
REGENERATE_SPEC=false
RETAKE_TEST=false

# If running interactively (stdin is a tty), ask user for choices
if [[ -t 0 ]]; then
    echo ""
    echo "english: This substrate uses LLM (OpenAI) for both specification generation and test execution."
    echo ""

    # =========================================================================
    # QUESTION 1: Regenerate specification.md?
    # =========================================================================
    if [[ -f "$SCRIPT_DIR/specification.md" ]]; then
        echo "english: specification.md exists."
        read -p "english: Regenerate specification via LLM? (1-2 min) [y/N] " regen_response
        if [[ "$regen_response" =~ ^[Yy]$ ]]; then
            REGENERATE_SPEC=true
        fi
    else
        echo "english: specification.md not found - must generate."
        read -p "english: Generate specification via LLM? (1-2 min) [y/N] " regen_response
        if [[ "$regen_response" =~ ^[Yy]$ ]]; then
            REGENERATE_SPEC=true
        else
            echo "english: Cannot proceed without specification.md"
            echo "SUBSTRATE_SKIPPED"
            exit 0
        fi
    fi
    echo ""

    # =========================================================================
    # QUESTION 2: Re-take the test?
    # =========================================================================
    if [[ -d "$LAST_RUN_ANSWERS" ]] && [[ "$(ls -A "$LAST_RUN_ANSWERS" 2>/dev/null)" ]]; then
        echo "english: Previous test answers exist."
        read -p "english: Re-take English test via LLM? (2-5 min) [y/N] " test_response
        if [[ "$test_response" =~ ^[Yy]$ ]]; then
            RETAKE_TEST=true
        fi
    else
        echo "english: No previous test answers found - must take test."
        read -p "english: Take English test via LLM? (2-5 min) [y/N] " test_response
        if [[ "$test_response" =~ ^[Yy]$ ]]; then
            RETAKE_TEST=true
        else
            echo "english: No test answers available to grade"
            echo "SUBSTRATE_SKIPPED"
            exit 0
        fi
    fi
    echo ""
else
    # Non-interactive: run everything
    REGENERATE_SPEC=true
    RETAKE_TEST=true
fi

# Ensure test-answers directory exists
mkdir -p "$SCRIPT_DIR/test-answers"

# =========================================================================
# STEP 1: Regenerate specification if requested
# =========================================================================
if $REGENERATE_SPEC; then
    INJECT_START=$(date +%s)
    echo "english: Generating specification via LLM..."
    python3 "$SCRIPT_DIR/inject-into-english.py" --regenerate
    INJECT_STATUS=$?
    INJECT_END=$(date +%s)
    INJECT_DURATION=$((INJECT_END - INJECT_START))

    if [[ $INJECT_STATUS -ne 0 ]]; then
        echo "english: ERROR - specification generation failed"
        exit 1
    fi
    echo "english: Specification generated (${INJECT_DURATION}s)"
    echo ""
fi

# =========================================================================
# STEP 2: Take test OR restore previous answers
# =========================================================================
if $RETAKE_TEST; then
    # Actually run the test
    {
        echo "=== English (LLM) Substrate Test Run ==="
        echo ""

        # Run English substrate test with --no-confirm to skip per-entity prompts
        python3 "$SCRIPT_DIR/take-test.py" --no-confirm

        echo ""
    } 2>&1 | tee "$LOG_FILE"

    # Save successful answers for future skip/restore
    if [[ $? -eq 0 ]]; then
        rm -rf "$LAST_RUN_ANSWERS"
        mkdir -p "$LAST_RUN_ANSWERS"
        cp -r "$SCRIPT_DIR/test-answers/"* "$LAST_RUN_ANSWERS/" 2>/dev/null || true
    fi

    echo "english: test completed"
else
    # Restore previous answers and signal for grading with preserved timing
    echo "english: Skipping LLM test, restoring previous answers..."

    if [[ -d "$LAST_RUN_ANSWERS" ]]; then
        rm -rf "$SCRIPT_DIR/test-answers"
        mkdir -p "$SCRIPT_DIR/test-answers"
        cp -r "$LAST_RUN_ANSWERS/"* "$SCRIPT_DIR/test-answers/" 2>/dev/null || true
        echo "english: Previous answers restored"
    fi

    # Keep existing log file and substrate report from the last real run
    # Don't overwrite with "skipped" message - preserve the meaningful LLM output
    echo "english: grading with previous answers (keeping previous log and report)"

    # Signal to orchestrator: grade but preserve timing from last run
    echo "SUBSTRATE_SKIPPED_BUT_GRADE"

    # Exit early - don't regenerate substrate report when skipping
    # This preserves the previous run's log in the report
    exit 0
fi

# Generate substrate report (only when test was actually run)
python3 "$PROJECT_ROOT/orchestration/create-substrate-report.py" english --log "$LOG_FILE"
