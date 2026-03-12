#!/usr/bin/env python3
# =============================================================================
# TEST ORCHESTRATOR (Generic / Domain-Agnostic)
# =============================================================================
# Generic test framework for evaluating execution substrates.
#
# This orchestrator knows NOTHING about specific domains. It only knows:
# - Views (anything named vw_* in postgres)
# - Raw fields (schema type: "raw")
# - Computed fields (schema type: "calculated" or "aggregation")
# - JSON comparison (expected vs actual)
#
# All configuration is auto-discovered from the rulebook and database.
# =============================================================================

import glob
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor

# =============================================================================
# PATHS (Generic - No Domain-Specific Names)
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
TESTING_DIR = os.path.join(PROJECT_ROOT, "testing")
ANSWER_KEYS_DIR = os.path.join(TESTING_DIR, "answer-keys")
BLANK_TESTS_DIR = os.path.join(TESTING_DIR, "blank-tests")
SUBSTRATES_DIR = os.path.join(PROJECT_ROOT, "execution-substrates")
RULEBOOK_DIR = os.path.join(PROJECT_ROOT, "effortless-rulebook")
RULEBOOK_PATH = os.path.join(RULEBOOK_DIR, "effortless-rulebook.json")
SUMMARY_PATH = os.path.join(SCRIPT_DIR, "all-tests-results.md")

# Database connection (generic - uses environment variable or inferred from init-db.sh)
DB_CONNECTION = os.environ.get("DATABASE_URL")
if not DB_CONNECTION:
    # Try to infer from init-db.sh DEFAULT_CONN line
    init_db_path = os.path.join(PROJECT_ROOT, "postgres", "init-db.sh")
    if os.path.exists(init_db_path):
        with open(init_db_path, 'r') as f:
            for line in f:
                if 'DEFAULT_CONN=' in line:
                    # Extract connection string from: DEFAULT_CONN="postgresql://..."
                    match = re.search(r'DEFAULT_CONN="([^"]+)"', line)
                    if match:
                        DB_CONNECTION = match.group(1)
                        break
    if not DB_CONNECTION:
        DB_CONNECTION = "postgresql://postgres@localhost:5432/postgres"

# =============================================================================
# ANSI Color Codes (Unchanged)
# =============================================================================

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"
SKY_BLUE_BG = "\033[48;5;117m"
DARK_TEXT = "\033[38;5;232m"
GREEN_BG = "\033[48;5;22m"
RED_BG = "\033[48;5;52m"
WHITE_TEXT = "\033[97m"
STRIKETHROUGH = "\033[9m"
DIM = "\033[2m"


def get_score_color(score: float) -> str:
    """Returns ANSI color code for a score using a red->yellow->green gradient."""
    if score >= 100:
        return "\033[38;5;46m"
    elif score >= 90:
        return "\033[38;5;82m"
    elif score >= 80:
        return "\033[38;5;118m"
    elif score >= 70:
        return "\033[38;5;154m"
    elif score >= 60:
        return "\033[38;5;190m"
    elif score >= 50:
        return "\033[38;5;226m"
    elif score >= 40:
        return "\033[38;5;220m"
    elif score >= 30:
        return "\033[38;5;214m"
    elif score >= 20:
        return "\033[38;5;208m"
    elif score >= 10:
        return "\033[38;5;202m"
    else:
        return "\033[38;5;196m"


# =============================================================================
# RUN METADATA: Track success/failure history per substrate
# =============================================================================

# Central substrate results file - THE source of truth for all substrate stats
CENTRAL_RESULTS_PATH = os.path.join(TESTING_DIR, "_substrate_results.json")


def load_central_results() -> dict:
    """Load the central _substrate_results.json from testing folder"""
    if os.path.exists(CENTRAL_RESULTS_PATH):
        with open(CENTRAL_RESULTS_PATH, 'r') as f:
            return json.load(f)
    return {}


def save_central_results(results: dict):
    """Save the central _substrate_results.json to testing folder"""
    with open(CENTRAL_RESULTS_PATH, 'w') as f:
        json.dump(results, f, indent=2, default=str)


def load_run_metadata(substrate_name: str) -> dict:
    """Load metadata for a substrate from the CENTRAL results file"""
    central = load_central_results()
    return central.get(substrate_name, {"last_run": None, "last_successful_run": None})


def save_run_metadata(substrate_name: str, metadata: dict):
    """Save metadata for a substrate to the CENTRAL results file"""
    central = load_central_results()
    central[substrate_name] = metadata
    save_central_results(central)


def update_run_metadata(substrate_name: str, grades: dict, success: bool, error_msg: str = None, preserve_timing: bool = False):
    """Update run metadata after a test run.

    IMPORTANT: Only updates last_successful_run when score is 100%.
    This preserves previous successful run data including duration.
    If substrate was skipped, does not update metadata at all.

    Args:
        substrate_name: Name of the substrate
        grades: Grading results dict
        success: Whether the take-test.sh returned exit code 0
        error_msg: Error message if run failed
        preserve_timing: If True, preserve timing from previous run (user skipped LLM but still graded)
    """
    # If substrate was skipped by user, don't update metadata
    if grades.get("skipped"):
        return

    metadata = load_run_metadata(substrate_name)
    timestamp = datetime.now().isoformat()

    # When preserve_timing is True, use the timing already in grades (which was loaded from previous run)
    # Otherwise use the newly measured elapsed time
    elapsed = grades.get("elapsed_seconds", 0.0)

    total = grades.get("total_fields_tested", 0)
    passed = grades.get("fields_passed", 0)
    failed = grades.get("fields_failed", 0)
    score = (passed / total * 100) if total > 0 else 0.0

    # When preserving timing, we still update last_run but with preserved duration
    # This allows the test results to update while keeping the meaningful timing
    run_record = {
        "status": "success" if success else "failure",
        "duration_seconds": elapsed,
        "exit_code": 0 if success else 1,
        "score": score
    }
    if error_msg:
        run_record["error_message"] = error_msg

    metadata["last_run"] = run_record

    # Only update last_successful_run on success AND 100% score
    # When preserve_timing is True and score is 100%, we update the test_results
    # but keep the duration from the previous successful run
    if success and total > 0 and score >= 100.0:
        if preserve_timing and metadata.get("last_successful_run"):
            # Keep existing duration, just update test results and timestamp
            prev_duration = metadata["last_successful_run"].get("duration_seconds", elapsed)
            metadata["last_successful_run"] = {
                "duration_seconds": prev_duration,
                "status": "success",
                "test_results": {
                    "total_fields_tested": total,
                    "fields_passed": passed,
                    "fields_failed": failed,
                    "score": score
                }
            }
        else:
            metadata["last_successful_run"] = {
                "duration_seconds": elapsed,
                "status": "success",
                "test_results": {
                    "total_fields_tested": total,
                    "fields_passed": passed,
                    "fields_failed": failed,
                    "score": score
                }
            }

    save_run_metadata(substrate_name, metadata)


# =============================================================================
# AUTO-DISCOVERY: Views, Computed Columns, Primary Keys
# =============================================================================

def to_snake_case(name: str) -> str:
    """Convert PascalCase to snake_case: FamilyFuedQuestion -> family_fued_question

    Also handles fields with existing underscores: Bio_HockettScore -> bio_hockett_score
    """
    # Use [^_] to avoid doubling underscores when input already has them
    s1 = re.sub('([^_])([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def to_pascal_case(name: str) -> str:
    """Convert snake_case to PascalCase: user_accounts -> UserAccounts"""
    return ''.join(word.capitalize() for word in name.split('_'))


def load_rulebook() -> dict:
    """Load the effortless-rulebook.json file"""
    if not os.path.exists(RULEBOOK_PATH):
        print(f"  WARNING: Rulebook not found at {RULEBOOK_PATH}", flush=True)
        return {}
    with open(RULEBOOK_PATH, 'r') as f:
        return json.load(f)


def discover_entities(rulebook: dict) -> list:
    """
    Discover all entities from the rulebook.
    Entities are top-level keys that have a 'schema' array.
    """
    entities = []
    skip_keys = {'$schema', 'model_name', 'Description', '_meta'}

    for key, value in rulebook.items():
        if key in skip_keys:
            continue
        if isinstance(value, dict) and 'schema' in value:
            entities.append(key)

    return entities


def get_entity_schema(rulebook: dict, entity_name: str) -> list:
    """Get the schema array for an entity (handles both PascalCase and snake_case)"""
    # Try PascalCase first
    if entity_name in rulebook:
        return rulebook[entity_name].get('schema', [])

    # Try converting from snake_case
    pascal_name = to_pascal_case(entity_name)
    if pascal_name in rulebook:
        return rulebook[pascal_name].get('schema', [])

    return []


def discover_primary_key(rulebook: dict, entity_name: str) -> str:
    """
    Discover the primary key for an entity.
    First non-nullable field, or first field ending in 'Id'.
    """
    schema = get_entity_schema(rulebook, entity_name)

    # First try: find first non-nullable field
    for field in schema:
        if field.get('nullable') == False:
            return to_snake_case(field['name'])

    # Second try: find first field ending in 'Id'
    for field in schema:
        if field['name'].endswith('Id'):
            return to_snake_case(field['name'])

    # Fallback: first field
    if schema:
        return to_snake_case(schema[0]['name'])

    return None


def discover_computed_columns(rulebook: dict, entity_name: str) -> list:
    """
    Discover computed columns for an entity.
    Returns list of snake_case column names where type == "calculated" or "aggregation".
    """
    schema = get_entity_schema(rulebook, entity_name)

    computed = []
    for field in schema:
        if field.get('type') in ('calculated', 'aggregation'):
            computed.append(to_snake_case(field['name']))

    return computed


def discover_views(conn) -> list:
    """Query postgres for all vw_* views"""
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name
        FROM information_schema.views
        WHERE table_name LIKE 'vw_%'
        ORDER BY table_name
    """)
    views = [row[0] for row in cur.fetchall()]
    cur.close()
    return views


def view_to_entity_name(view_name: str) -> str:
    """Convert view name to entity name: vw_products -> products"""
    return view_name.replace('vw_', '')


# =============================================================================
# STEP 1: Generate Answer Keys from Postgres
# =============================================================================

def generate_all_answer_keys(conn, rulebook: dict) -> dict:
    """
    Query all vw_* views and export to answer-keys/{entity}.json.
    Returns dict of entity_name -> list of records.
    """
    print("Step 1: Generating answer keys from all views...", flush=True)

    # Clear and recreate answer-keys directory to remove stale files
    import shutil
    if os.path.exists(ANSWER_KEYS_DIR):
        shutil.rmtree(ANSWER_KEYS_DIR)
    os.makedirs(ANSWER_KEYS_DIR, exist_ok=True)

    views = discover_views(conn)
    print(f"  Found {len(views)} views: {', '.join(views)}", flush=True)

    all_answer_keys = {}
    first_entity_with_computed = None

    for view in views:
        entity = view_to_entity_name(view)
        pk = discover_primary_key(rulebook, entity)
        computed_cols = discover_computed_columns(rulebook, entity)

        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Order by primary key if available
        if pk:
            cur.execute(f"SELECT * FROM {view} ORDER BY {pk}")
        else:
            cur.execute(f"SELECT * FROM {view}")

        rows = cur.fetchall()
        records = [dict(row) for row in rows]
        cur.close()

        # Save to file
        output_path = os.path.join(ANSWER_KEYS_DIR, f"{entity}.json")
        with open(output_path, 'w') as f:
            json.dump(records, f, indent=2, default=str)

        all_answer_keys[entity] = records
        print(f"  -> {entity}: {len(records)} records", flush=True)

    return all_answer_keys


# =============================================================================
# STEP 2: Generate Blank Tests (null computed columns)
# =============================================================================

def generate_all_blank_tests(all_answer_keys: dict, rulebook: dict) -> dict:
    """
    Create blank tests by nulling computed columns for each entity.
    Generates testing/blank-tests/{entity}.json files and testing/_metadata.json.
    """
    print("Step 2: Generating blank tests...", flush=True)

    # Clear and recreate blank-tests directory to remove stale files
    import shutil
    if os.path.exists(BLANK_TESTS_DIR):
        shutil.rmtree(BLANK_TESTS_DIR)
    os.makedirs(BLANK_TESTS_DIR, exist_ok=True)

    all_blank_tests = {}
    entity_metadata = {}

    for entity, records in all_answer_keys.items():
        computed_cols = discover_computed_columns(rulebook, entity)
        pk = discover_primary_key(rulebook, entity)

        if not computed_cols:
            print(f"  -> {entity}: No computed columns (skipping blank test)", flush=True)
            continue

        # Create blank test by nulling computed columns
        blank_records = []
        for record in records:
            blank_record = dict(record)
            for col in computed_cols:
                if col in blank_record:
                    blank_record[col] = None
            blank_records.append(blank_record)

        # Save to file
        output_path = os.path.join(BLANK_TESTS_DIR, f"{entity}.json")
        with open(output_path, 'w') as f:
            json.dump(blank_records, f, indent=2, default=str)

        all_blank_tests[entity] = blank_records

        # Track metadata for grading context
        entity_metadata[entity] = {
            "primary_key": pk,
            "computed_columns": computed_cols,
            "record_count": len(blank_records)
        }

        print(f"  -> {entity}: Nulled {len(computed_cols)} columns: {', '.join(computed_cols)}", flush=True)

    # Generate shared entity metadata at testing/_metadata.json (not in blank-tests/)
    metadata_path = os.path.join(TESTING_DIR, "_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(entity_metadata, f, indent=2)
    print(f"  -> Entity metadata: {len(entity_metadata)} entities -> testing/_metadata.json", flush=True)

    return all_blank_tests


# =============================================================================
# STEP 3: Run Substrate Tests
# =============================================================================

def get_substrates() -> list:
    """Get list of substrate directories"""
    substrates = []
    if os.path.isdir(SUBSTRATES_DIR):
        for name in sorted(os.listdir(SUBSTRATES_DIR)):
            path = os.path.join(SUBSTRATES_DIR, name)
            if os.path.isdir(path) and not name.startswith('.'):
                substrates.append(name)
    return substrates


def prepare_substrate_for_test(substrate_name: str) -> int:
    """
    Prepare a substrate for testing by clearing its test-answers/ directory.
    Substrates now read blank-tests from the shared testing/blank-tests/ location.
    Returns number of test files that will be processed.
    """
    import shutil

    substrate_dir = os.path.join(SUBSTRATES_DIR, substrate_name)
    substrate_test_answers = os.path.join(substrate_dir, "test-answers")

    # Clear and recreate test-answers directory
    if os.path.exists(substrate_test_answers):
        shutil.rmtree(substrate_test_answers)
    os.makedirs(substrate_test_answers, exist_ok=True)

    # Count blank test files (for reporting)
    count = 0
    for filename in os.listdir(BLANK_TESTS_DIR):
        if filename.endswith('.json') and not filename.startswith('_'):
            count += 1

    return count


def run_substrate_test(substrate_name: str) -> tuple:
    """Run a substrate's take-test.sh and return (success, error, elapsed, skipped)"""
    substrate_dir = os.path.join(SUBSTRATES_DIR, substrate_name)
    script_path = os.path.join(substrate_dir, "take-test.sh")

    if not os.path.exists(script_path):
        return False, "No take-test.sh found", 0.0, False

    start_time = time.time()
    try:
        result = subprocess.run(
            ["bash", script_path],
            cwd=substrate_dir,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes for LLM substrates like english
        )
        elapsed = time.time() - start_time

        # Check if substrate was skipped by user
        if "SUBSTRATE_SKIPPED" in result.stdout:
            return True, None, elapsed, True

        if result.returncode != 0:
            return False, f"Script failed: {result.stderr[:200]}", elapsed, False

        return True, None, elapsed, False

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start_time
        return False, "Script timed out", elapsed, False
    except Exception as e:
        elapsed = time.time() - start_time
        return False, str(e), elapsed, False


def get_substrate_answers(substrate_name: str, rulebook: dict) -> dict:
    """
    Get all test-answers from a substrate.
    Returns dict of entity_name -> list of records.
    """
    substrate_dir = os.path.join(SUBSTRATES_DIR, substrate_name)
    answers_dir = os.path.join(substrate_dir, "test-answers")

    # Check for new multi-entity structure
    if os.path.isdir(answers_dir):
        answers = {}
        for file in glob.glob(os.path.join(answers_dir, "*.json")):
            entity = os.path.basename(file).replace('.json', '')
            try:
                with open(file, 'r') as f:
                    answers[entity] = json.load(f)
            except:
                pass
        if answers:
            return answers

    # Fall back to old single-file structure (test-answers.json)
    old_path = os.path.join(substrate_dir, "test-answers.json")
    if os.path.exists(old_path):
        try:
            with open(old_path, 'r') as f:
                records = json.load(f)

            if records:
                # Try to identify entity from record keys
                sample = records[0] if records else {}

                # Find first entity with computed columns that matches record keys
                for entity_file in glob.glob(os.path.join(BLANK_TESTS_DIR, "*.json")):
                    entity = os.path.basename(entity_file).replace('.json', '')
                    pk = discover_primary_key(rulebook, entity)
                    if pk and pk in sample:
                        return {entity: records}

                # Fallback: use first entity with computed columns
                for entity_file in glob.glob(os.path.join(BLANK_TESTS_DIR, "*.json")):
                    entity = os.path.basename(entity_file).replace('.json', '')
                    return {entity: records}
        except:
            pass

    return {}


# =============================================================================
# STEP 4: Grade Substrates (Generic Field-by-Field Comparison)
# =============================================================================

def compare_values(expected, actual) -> bool:
    """Compare two values, handling type differences.

    Treats empty strings and None/null as equivalent since many substrates
    cannot distinguish between 'no value' representations.
    """
    # Normalize empty/null values - treat "", None, "None", "null" as equivalent
    def normalize(val):
        if val is None:
            return ""
        s = str(val)
        if s in ("None", "null", "NULL"):
            return ""
        return s

    return normalize(expected) == normalize(actual)


def grade_substrate(substrate_name: str, all_answer_keys: dict, rulebook: dict) -> dict:
    """
    Grade a substrate's answers against all answer keys.
    Returns detailed results per entity.
    """
    results = {
        "substrate": substrate_name,
        "entities": {},
        "total_fields_tested": 0,
        "fields_passed": 0,
        "fields_failed": 0,
        "error": None,
        "elapsed_seconds": 0.0
    }

    # Get substrate's answers
    substrate_answers = get_substrate_answers(substrate_name, rulebook)

    if not substrate_answers:
        results["error"] = "No test-answers found"
        return results

    # Grade each entity the substrate attempted
    for entity, test_records in substrate_answers.items():
        if entity not in all_answer_keys:
            continue

        answer_key = all_answer_keys[entity]
        computed_cols = discover_computed_columns(rulebook, entity)
        pk = discover_primary_key(rulebook, entity)

        if not computed_cols:
            continue  # Nothing to test

        # Index test answers by primary key
        answers_by_pk = {}
        for record in test_records:
            pk_val = record.get(pk)
            if pk_val is not None:
                answers_by_pk[str(pk_val)] = record

        entity_result = {
            "total_records": len(answer_key),
            "computed_columns": computed_cols,
            "primary_key": pk,
            "fields_tested": 0,
            "fields_passed": 0,
            "fields_failed": 0,
            "failures": []
        }

        # Compare each record
        for expected_record in answer_key:
            pk_val = str(expected_record.get(pk))
            actual_record = answers_by_pk.get(pk_val, {})

            for col in computed_cols:
                entity_result["fields_tested"] += 1
                results["total_fields_tested"] += 1

                expected_val = expected_record.get(col)
                actual_val = actual_record.get(col)

                if compare_values(expected_val, actual_val):
                    entity_result["fields_passed"] += 1
                    results["fields_passed"] += 1
                else:
                    entity_result["fields_failed"] += 1
                    results["fields_failed"] += 1
                    entity_result["failures"].append({
                        "pk": pk_val,
                        "field": col,
                        "expected": expected_val,
                        "actual": actual_val
                    })

        # Skip entities with 0% (not attempted - all nulls still)
        if entity_result["fields_passed"] == 0 and entity_result["fields_failed"] > 0:
            # Check if all actuals are None (substrate didn't fill them in)
            all_none = all(
                f["actual"] is None or f["actual"] == "None"
                for f in entity_result["failures"]
            )
            if all_none:
                # Substrate didn't attempt this entity, remove from totals
                results["total_fields_tested"] -= entity_result["fields_tested"]
                results["fields_failed"] -= entity_result["fields_failed"]
                continue

        results["entities"][entity] = entity_result

    return results


def run_and_grade_all_substrates(all_answer_keys: dict, rulebook: dict) -> dict:
    """Run and grade each substrate"""
    print("Step 3: Running and grading tests for each substrate...", flush=True)
    print(flush=True)

    substrates = get_substrates()
    print(f"  Found {len(substrates)} substrates: {', '.join(substrates)}", flush=True)
    print(flush=True)

    all_grades = {}

    for i, substrate in enumerate(substrates, 1):
        print(f"  [{i}/{len(substrates)}] Testing {substrate}...", flush=True)

        # Prepare substrate for test (clear old test-answers)
        test_count = prepare_substrate_for_test(substrate)
        print(f"      Prepared {substrate} ({test_count} tests from shared testing/blank-tests/)", flush=True)

        # Run the test
        success, error, elapsed, skipped = run_substrate_test(substrate)

        # Grade the results
        grades = grade_substrate(substrate, all_answer_keys, rulebook)
        if error:
            grades["error"] = error

        # If substrate was skipped, use previous timing from metadata
        if skipped:
            print(f"      {substrate} was SKIPPED - using previous timing", flush=True)
            metadata = load_run_metadata(substrate)
            last_run = metadata.get("last_run", {})
            prev_elapsed = last_run.get("duration_seconds", 0.0)
            grades["elapsed_seconds"] = prev_elapsed
            grades["skipped"] = True
        else:
            grades["elapsed_seconds"] = elapsed
            grades["skipped"] = False

        all_grades[substrate] = grades

        # Generate report and print summary
        generate_substrate_report(substrate, grades, rulebook)
        print_substrate_test_summary(substrate, grades, rulebook)
        print("\n" * 5, flush=True)

    return all_grades


# =============================================================================
# Reporting Functions
# =============================================================================

def format_duration(seconds: float) -> str:
    """Format duration in human-readable form.

    Uses whole seconds with '< 1s' for sub-second times to reduce git diff noise.
    """
    if seconds < 1:
        return "< 1s"
    elif seconds < 60:
        return f"{int(round(seconds))}s"
    else:
        mins = int(seconds // 60)
        secs = int(round(seconds % 60))
        return f"{mins}m {secs}s"


def generate_substrate_report(substrate_name: str, results: dict, rulebook: dict):
    """Generate test-results.md for a substrate"""
    substrate_dir = os.path.join(SUBSTRATES_DIR, substrate_name)
    report_path = os.path.join(substrate_dir, "test-results.md")

    total = results["total_fields_tested"]
    passed = results["fields_passed"]
    failed = results["fields_failed"]
    score = (passed / total * 100) if total > 0 else 0
    elapsed = results.get("elapsed_seconds", 0.0)

    # Check run metadata for error banner
    run_metadata = load_run_metadata(substrate_name)
    last_run = run_metadata.get("last_run", {})
    last_success = run_metadata.get("last_successful_run", {})

    lines = [
        f"# Test Results: {substrate_name}",
        "",
    ]

    # Add error banner if latest run failed but we have prior successful results
    if last_run.get("status") == "failure" and last_success:
        error_msg = last_run.get("error_message", "Unknown error")
        failure_time = last_run.get("timestamp", "Unknown")[:19].replace("T", " ")
        success_time = last_success.get("timestamp", "Unknown")[:19].replace("T", " ")
        success_results = last_success.get("test_results", {})

        lines.extend([
            "> **WARNING: Latest Run Failed**",
            "> ",
            f"> The test run at {failure_time} failed: `{error_msg}`",
            "> ",
            f"> Showing results from last successful run ({success_time}).",
            "",
        ])

        # Use the successful run's results for display
        if success_results:
            total = success_results.get("total_fields_tested", total)
            passed = success_results.get("fields_passed", passed)
            failed = success_results.get("fields_failed", failed)
            score = success_results.get("score", score)
            elapsed = last_success.get("duration_seconds", elapsed)

    lines.extend([
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Fields Tested | {total} |",
        f"| Passed | {passed} |",
        f"| Failed | {failed} |",
        f"| Score | {score:.1f}% |",
        f"| Duration | {format_duration(elapsed)} |",
        "",
    ])

    if results.get("error"):
        lines.extend([
            "## Error",
            "",
            "```",
            results["error"],
            "```",
            "",
        ])

    # Per-entity breakdown
    if results.get("entities"):
        lines.extend([
            "## Results by Entity",
            "",
        ])

        for entity, entity_result in results["entities"].items():
            e_total = entity_result["fields_tested"]
            e_passed = entity_result["fields_passed"]
            e_score = (e_passed / e_total * 100) if e_total > 0 else 0

            lines.extend([
                f"### {entity}",
                "",
                f"- Fields: {e_passed}/{e_total} ({e_score:.1f}%)",
                f"- Computed columns: {', '.join(entity_result['computed_columns'])}",
                "",
            ])

            if entity_result["failures"]:
                lines.extend([
                    "| PK | Field | Expected | Actual |",
                    "|-----|-------|----------|--------|",
                ])
                for failure in entity_result["failures"][:20]:
                    pk = failure["pk"]
                    field = failure["field"]
                    expected = str(failure["expected"])[:30]
                    actual = str(failure["actual"])[:30]
                    lines.append(f"| {pk} | {field} | {expected} | {actual} |")

                if len(entity_result["failures"]) > 20:
                    lines.append(f"| ... | ... | ({len(entity_result['failures']) - 20} more) | ... |")
                lines.append("")

    with open(report_path, 'w') as f:
        f.write('\n'.join(lines))


def print_substrate_test_summary(substrate_name: str, grades: dict, rulebook: dict):
    """Print a per-test breakdown for a substrate to console"""
    total = grades["total_fields_tested"]
    passed = grades["fields_passed"]
    failed = grades["fields_failed"]
    execution_failed = grades.get("error") and total == 0
    score = (passed / total * 100) if total > 0 else 0
    elapsed = grades.get("elapsed_seconds", 0.0)

    # Determine status
    if execution_failed:
        status_plain = "FAILED TO COMPUTE"
    elif grades.get("error"):
        status_plain = "ERROR"
    elif failed == 0:
        status_plain = "PASS"
    else:
        status_plain = "FAIL"

    score_color = get_score_color(score)

    box_width = 60
    if execution_failed:
        header_bg = RED_BG
        header_text = WHITE_TEXT
    else:
        header_bg = SKY_BLUE_BG
        header_text = DARK_TEXT

    print(f"  {header_bg}{header_text}┌{'─' * box_width}┐{RESET}", flush=True)
    print(f"  {header_bg}{header_text}│{BOLD} {substrate_name.upper():^{box_width - 2}} {RESET}{header_bg}{header_text}│{RESET}", flush=True)

    duration_str = format_duration(elapsed)
    if execution_failed:
        score_text = f"Score: --/-- (--%) - {status_plain}"
        print(f"  {header_bg}{header_text}│ {RED}{BOLD}{score_text:^{box_width - 2}}{RESET}{header_bg}{header_text} │{RESET}", flush=True)
    else:
        score_text = f"Score: {passed}/{total} ({score:.1f}%) - {status_plain}"
        print(f"  {header_bg}{header_text}│ {score_color}{BOLD}{score_text:^{box_width - 2}}{RESET}{header_bg}{header_text} │{RESET}", flush=True)

    duration_text = f"Duration: {duration_str}"
    print(f"  {header_bg}{header_text}│ {duration_text:^{box_width - 2}} │{RESET}", flush=True)
    print(f"  {header_bg}{header_text}├{'─' * box_width}┤{RESET}", flush=True)

    # Print per-entity results
    for entity, entity_result in grades.get("entities", {}).items():
        e_total = entity_result["fields_tested"]
        e_passed = entity_result["fields_passed"]
        e_failed = entity_result["fields_failed"]
        e_score = (e_passed / e_total * 100) if e_total > 0 else 0

        if e_failed == 0:
            row_bg = GREEN_BG
            icon = "✓"
            result_str = "PASS"
            text_color = GREEN
        else:
            row_bg = RED_BG
            icon = "✗"
            result_str = f"FAIL ({e_failed}/{e_total})"
            text_color = RED

        entity_display = entity[:35] if len(entity) > 35 else entity
        row_content = f"  {icon} {entity_display:<40} {result_str:>12} "
        print(f"  {row_bg}{WHITE_TEXT}│{row_content}│{RESET}", flush=True)

        # Show per-column breakdown
        failures_by_col = {}
        for f in entity_result.get("failures", []):
            col = f["field"]
            failures_by_col[col] = failures_by_col.get(col, 0) + 1

        for col in entity_result["computed_columns"]:
            col_failures = failures_by_col.get(col, 0)
            if col_failures == 0:
                col_status = f"{GREEN}✓{RESET}"
            else:
                col_status = f"{RED}{col_failures}{RESET}"
            col_display = col[:30] if len(col) > 30 else col
            print(f"  {header_bg}{header_text}│     {col_display:<40} {col_status:>18} │{RESET}", flush=True)

    if execution_failed:
        error_msg = grades.get("error", "Unknown error")[:50]
        print(f"  {RED_BG}{WHITE_TEXT}│ ERROR: {error_msg:<{box_width - 9}} │{RESET}", flush=True)

    print(f"  {header_bg}{header_text}└{'─' * box_width}┘{RESET}", flush=True)
    print(flush=True)


def generate_summary_report(all_grades: dict, rulebook: dict):
    """Generate all-tests-results.md with summary of all substrates"""
    print("Step 4: Generating summary report...", flush=True)

    # Collect all computed columns across all entities
    all_computed_cols = set()
    for substrate_grades in all_grades.values():
        for entity_result in substrate_grades.get("entities", {}).values():
            all_computed_cols.update(entity_result.get("computed_columns", []))

    lines = [
        "# Test Orchestrator Results",
        "",
        "## Configuration",
        "",
        f"- **Rulebook:** `{RULEBOOK_PATH}`",
        f"- **Substrates Tested:** {len(all_grades)}",
        f"- **Computed Columns Tested:** {len(all_computed_cols)}",
        "",
        "## Summary by Substrate",
        "",
        "| Substrate | Passed | Failed | Total | Score | Duration | Status |",
        "|-----------|--------|--------|-------|-------|----------|--------|",
    ]

    total_passed = 0
    total_failed = 0
    total_tests = 0
    total_time = 0.0

    # Sort by: 1) 100% substrates first (sorted by time), 2) <100% substrates at bottom (sorted by score desc)
    # Use substrate name as final tiebreaker for deterministic output
    # Round elapsed times to 0.5s buckets to prevent jitter from causing re-ordering
    def sort_key(name):
        g = all_grades[name]
        elapsed = g.get("elapsed_seconds", 0.0)
        # Round to 0.5s buckets for sorting stability
        elapsed_bucket = round(elapsed * 2) / 2
        p = g["fields_passed"]
        t = g["total_fields_tested"]
        score = (p / t * 100) if t > 0 else 0
        is_perfect = score >= 100.0
        # Primary: is_perfect (True=0, False=1 - so perfect scores come first)
        # Secondary: time bucket for perfect scores, -score for imperfect (highest score first among failures)
        # Tertiary: name for deterministic ordering when times are in same bucket
        return (0 if is_perfect else 1, elapsed_bucket if is_perfect else -score, name)

    for substrate_name in sorted(all_grades.keys(), key=sort_key):
        grades = all_grades[substrate_name]

        passed = grades["fields_passed"]
        failed = grades["fields_failed"]
        total = grades["total_fields_tested"]
        score = (passed / total * 100) if total > 0 else 0
        elapsed = grades.get("elapsed_seconds", 0.0)

        total_passed += passed
        total_failed += failed
        total_tests += total
        total_time += elapsed

        if grades.get("error"):
            status = f"ERROR: {grades['error'][:30]}"
        elif failed == 0:
            status = "PASS"
        else:
            status = "FAIL"

        lines.append(f"| {substrate_name} | {passed} | {failed} | {total} | {score:.1f}% | {format_duration(elapsed)} | {status} |")

    overall_score = (total_passed / total_tests * 100) if total_tests > 0 else 0

    lines.extend([
        "",
        "## Overall Statistics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Substrates | {len(all_grades)} |",
        f"| Total Fields Tested | {total_tests} |",
        f"| Total Passed | {total_passed} |",
        f"| Total Failed | {total_failed} |",
        f"| Overall Score | {overall_score:.1f}% |",
        f"| Total Duration | {format_duration(total_time)} |",
        "",
        "---",
        "",
        "*Generated by test-orchestrator.py (generic/domain-agnostic)*",
    ])

    with open(SUMMARY_PATH, 'w') as f:
        f.write('\n'.join(lines))

    print(f"  -> Summary written to {SUMMARY_PATH}", flush=True)
    print(f"  -> Overall: {total_passed}/{total_tests} ({overall_score:.1f}%)", flush=True)

    return total_passed, total_failed, total_tests, overall_score


def print_final_summary_table(all_grades: dict, rulebook: dict):
    """Print a final summary table to console"""
    print(flush=True)
    print("=" * 80, flush=True)
    print(f"{BOLD}FINAL RESULTS SUMMARY{RESET}", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)

    # Header
    print(f"{'Substrate':<20} {'Passed':>8} {'Failed':>8} {'Total':>8} {'Score':>8} {'Duration':>10} {'Status':>12}", flush=True)
    print("-" * 80, flush=True)

    total_passed = 0
    total_failed = 0
    total_time = 0.0

    # Sort by: 1) 100% substrates first (sorted by time), 2) <100% substrates at bottom (sorted by score desc)
    # Use substrate name as final tiebreaker for deterministic output
    # Round elapsed times to 0.5s buckets to prevent jitter from causing re-ordering
    def sort_key(name):
        g = all_grades[name]
        elapsed = g.get("elapsed_seconds", 0.0)
        # Round to 0.5s buckets for sorting stability
        elapsed_bucket = round(elapsed * 2) / 2
        p = g["fields_passed"]
        t = g["total_fields_tested"]
        score = (p / t * 100) if t > 0 else 0
        is_perfect = score >= 100.0
        # Primary: is_perfect (True=0, False=1 - so perfect scores come first)
        # Secondary: time bucket for perfect scores, -score for imperfect (highest score first among failures)
        # Tertiary: name for deterministic ordering when times are in same bucket
        return (0 if is_perfect else 1, elapsed_bucket if is_perfect else -score, name)

    for substrate_name in sorted(all_grades.keys(), key=sort_key):
        grades = all_grades[substrate_name]
        passed = grades["fields_passed"]
        failed = grades["fields_failed"]
        total = grades["total_fields_tested"]
        score = (passed / total * 100) if total > 0 else 0
        elapsed = grades.get("elapsed_seconds", 0.0)

        total_passed += passed
        total_failed += failed
        total_time += elapsed

        score_color = get_score_color(score)

        if grades.get("error") and total == 0:
            status = f"{RED}FAILED{RESET}"
        elif failed == 0:
            status = f"{GREEN}PASS{RESET}"
        else:
            status = f"{YELLOW}PARTIAL{RESET}"

        print(f"{substrate_name:<20} {passed:>8} {failed:>8} {total:>8} {score_color}{score:>7.1f}%{RESET} {format_duration(elapsed):>10} {status:>12}", flush=True)

    print("-" * 80, flush=True)
    overall_total = total_passed + total_failed
    overall_score = (total_passed / overall_total * 100) if overall_total > 0 else 0
    print(f"{BOLD}{'OVERALL':<20}{RESET} {total_passed:>8} {total_failed:>8} {overall_total:>8} {BOLD}{overall_score:>7.1f}%{RESET} {format_duration(total_time):>10}", flush=True)
    print(flush=True)


# =============================================================================
# CLEANUP: Revert files with no REAL changes
# =============================================================================

def strip_timing_fields(obj, timing_fields):
    """Recursively remove timing-related fields from a JSON object."""
    if isinstance(obj, dict):
        return {k: strip_timing_fields(v, timing_fields) for k, v in obj.items()
                if k not in timing_fields}
    elif isinstance(obj, list):
        return [strip_timing_fields(item, timing_fields) for item in obj]
    return obj


def normalize_md_timing(content: str) -> str:
    """
    Normalize timing values and row order in markdown to enable comparison.

    Replaces duration values like "35s", "< 1s", "1m 23s" with a placeholder
    so that only-timing changes can be detected.

    Also sorts table rows by substrate name so that row order differences
    (caused by timing jitter affecting sort) don't register as real changes.
    """
    # Pattern for duration in table cells: | 35s | or | < 1s | or | 1m 23s |
    # Match patterns like: "35s", "< 1s", "1m 23s", "2m", etc.
    normalized = re.sub(r'\|\s*(<\s*)?\d+m?\s*\d*s?\s*\|', '| DURATION |', content)

    # Sort table rows alphabetically by first column (substrate name)
    # This ensures row order differences don't cause false positives
    lines = normalized.split('\n')
    result_lines = []
    table_rows = []
    in_table = False

    for line in lines:
        # Detect table data rows (start with | and have substrate names, not headers/separators)
        if line.startswith('|') and not line.startswith('|--') and not '| Substrate |' in line and not '| Metric |' in line:
            table_rows.append(line)
            in_table = True
        else:
            # If we were collecting table rows, sort and flush them
            if table_rows:
                table_rows.sort()
                result_lines.extend(table_rows)
                table_rows = []
            result_lines.append(line)
            in_table = False

    # Flush any remaining table rows
    if table_rows:
        table_rows.sort()
        result_lines.extend(table_rows)

    return '\n'.join(result_lines)


def revert_md_if_only_timing_changes(file_path: str) -> bool:
    """
    Check if the only changes in a markdown file are timing/duration values.
    If so, revert the file. Returns True if reverted, False otherwise.

    This is specifically for all-tests-results.md where Duration columns
    may change (e.g., "35s" -> "36s") without any real test result changes.
    """
    if not os.path.exists(file_path):
        return False

    try:
        rel_path = os.path.relpath(file_path, PROJECT_ROOT)

        # Check if file has uncommitted changes (staged or unstaged)
        result = subprocess.run(
            ['git', 'status', '--porcelain', '--', rel_path],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        if not result.stdout.strip():
            return False  # No changes

        # Load current file content
        with open(file_path, 'r') as f:
            current_content = f.read()

        # Get previous version from git
        result = subprocess.run(
            ['git', 'show', f'HEAD:{rel_path}'],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        if result.returncode != 0:
            return False  # File doesn't exist in previous commit

        previous_content = result.stdout

        # Normalize timing values in both versions
        current_normalized = normalize_md_timing(current_content)
        previous_normalized = normalize_md_timing(previous_content)

        # Compare
        if current_normalized != previous_normalized:
            # Real differences exist beyond timing values
            return False

        # All changes are timing-only - revert this file (both staged and unstaged)
        # First unstage if staged
        subprocess.run(
            ['git', 'reset', 'HEAD', '--', rel_path],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        # Then revert
        result = subprocess.run(
            ['git', 'checkout', '--', rel_path],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )

        if result.returncode == 0:
            print(f"  REVERTED (timing values only): {rel_path}", flush=True)
            return True
        return False

    except Exception as e:
        print(f"  WARNING: Error checking {file_path}: {e}", flush=True)
        return False


def revert_if_only_duration_changes(file_path: str) -> bool:
    """
    Check if the only changes in a JSON file are to timing-related fields.
    If so, revert the file. Returns True if reverted, False otherwise.

    Timing-related fields that are considered "noise" (not real changes):
    - duration_seconds: varies per run

    Algorithm:
    - Load current JSON and strip timing fields
    - Load previous commit JSON and strip timing fields
    - If they're identical after stripping, revert
    """
    # Fields that are timing-related metadata, not actual test results
    TIMING_FIELDS = {'duration_seconds'}

    if not os.path.exists(file_path):
        return False

    try:
        rel_path = os.path.relpath(file_path, PROJECT_ROOT)

        # Check if file has uncommitted changes (staged or unstaged)
        result = subprocess.run(
            ['git', 'status', '--porcelain', '--', rel_path],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        if not result.stdout.strip():
            return False  # No changes

        # Load current JSON
        with open(file_path, 'r') as f:
            current_data = json.load(f)

        # Get previous version from git
        result = subprocess.run(
            ['git', 'show', f'HEAD:{rel_path}'],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        if result.returncode != 0:
            return False  # File doesn't exist in previous commit

        previous_data = json.loads(result.stdout)

        # Strip timing fields from both
        current_stripped = strip_timing_fields(current_data, TIMING_FIELDS)
        previous_stripped = strip_timing_fields(previous_data, TIMING_FIELDS)

        # Compare
        if current_stripped != previous_stripped:
            # Real differences exist beyond timing fields
            return False

        # All changes are timing-only - revert this file (both staged and unstaged)
        # First unstage if staged
        subprocess.run(
            ['git', 'reset', 'HEAD', '--', rel_path],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        # Then revert
        result = subprocess.run(
            ['git', 'checkout', '--', rel_path],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )

        if result.returncode == 0:
            print(f"  REVERTED (timing fields only): {rel_path}", flush=True)
            return True
        return False

    except Exception as e:
        print(f"  WARNING: Error checking {file_path}: {e}", flush=True)
        return False


def xlsx_to_json(workbook) -> dict:
    """
    Export an xlsx workbook to a JSON structure containing all tabs,
    cells, values, and formulas.

    Returns a dict like:
    {
        "sheets": {
            "SheetName": {
                "dimensions": {"rows": 10, "cols": 5},
                "cells": [
                    {"row": 1, "col": 1, "value": "Header", "formula": null},
                    {"row": 2, "col": 1, "value": "=A1+B1", "formula": "=A1+B1"},
                    ...
                ]
            }
        }
    }
    """
    result = {"sheets": {}}

    for sheet_name in workbook.sheetnames:
        sheet = workbook[sheet_name]
        sheet_data = {
            "dimensions": {
                "rows": sheet.max_row or 0,
                "cols": sheet.max_column or 0
            },
            "cells": []
        }

        # Export all cells with their values/formulas
        for row in range(1, (sheet.max_row or 0) + 1):
            for col in range(1, (sheet.max_column or 0) + 1):
                cell = sheet.cell(row=row, column=col)
                cell_value = cell.value

                # Determine if it's a formula
                is_formula = isinstance(cell_value, str) and cell_value.startswith('=')

                sheet_data["cells"].append({
                    "row": row,
                    "col": col,
                    "value": cell_value,
                    "formula": cell_value if is_formula else None
                })

        result["sheets"][sheet_name] = sheet_data

    return result


def revert_xlsx_if_unchanged(file_path: str) -> bool:
    """
    Check if an xlsx file has no real content changes.
    Exports both current and previous xlsx to JSON (all tabs + formulas)
    in a temporary folder and compares them.

    If content and formulas are identical, revert the file.
    Returns True if reverted, False otherwise.

    Algorithm:
    1. Export current xlsx to JSON (all tabs + formulas)
    2. Export previous commit's xlsx to JSON (all tabs + formulas)
    3. Compare the JSON structures
    4. If identical, revert the file
    5. Clean up temp files immediately
    """
    if not os.path.exists(file_path):
        return False

    try:
        import openpyxl
        import tempfile

        # Get relative path for git commands
        rel_path = os.path.relpath(file_path, PROJECT_ROOT)

        # Check if file has uncommitted changes (staged or unstaged)
        result = subprocess.run(
            ['git', 'status', '--porcelain', '--', rel_path],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        if not result.stdout.strip():
            return False  # No changes

        # Create temp directory for our work
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_xlsx_path = os.path.join(tmp_dir, 'previous.xlsx')
            current_json_path = os.path.join(tmp_dir, 'current.json')
            previous_json_path = os.path.join(tmp_dir, 'previous.json')

            # Load current workbook and export to JSON
            try:
                current_wb = openpyxl.load_workbook(file_path, data_only=False)
            except Exception:
                return False

            current_json = xlsx_to_json(current_wb)
            with open(current_json_path, 'w') as f:
                json.dump(current_json, f, sort_keys=True, default=str)

            # Get previous version from git
            result = subprocess.run(
                ['git', 'show', f'HEAD:{rel_path}'],
                capture_output=True, cwd=PROJECT_ROOT
            )

            if result.returncode != 0:
                return False  # File doesn't exist in previous commit

            with open(tmp_xlsx_path, 'wb') as f:
                f.write(result.stdout)

            # Load previous workbook and export to JSON
            previous_wb = openpyxl.load_workbook(tmp_xlsx_path, data_only=False)
            previous_json = xlsx_to_json(previous_wb)
            with open(previous_json_path, 'w') as f:
                json.dump(previous_json, f, sort_keys=True, default=str)

            # Compare JSON structures
            if current_json != previous_json:
                return False  # Real differences exist

            # All content and formulas are identical - revert
            # First unstage if staged
            subprocess.run(
                ['git', 'reset', 'HEAD', '--', rel_path],
                capture_output=True, text=True, cwd=PROJECT_ROOT
            )
            # Then revert
            result = subprocess.run(
                ['git', 'checkout', '--', rel_path],
                capture_output=True, text=True, cwd=PROJECT_ROOT
            )

            if result.returncode == 0:
                print(f"  REVERTED (no content/formula changes): {rel_path}", flush=True)
                return True
            return False

        # TemporaryDirectory is automatically cleaned up here

    except ImportError:
        print("  WARNING: openpyxl not available for xlsx comparison", flush=True)
        return False
    except Exception as e:
        print(f"  WARNING: Error comparing {file_path}: {e}", flush=True)
        return False


def cleanup_unchanged_files():
    """
    Revert files that have no REAL changes to reduce noise in commits.

    1. _substrate_results.json - revert if only duration_seconds changed
    2. all-tests-results.md - revert if only duration values changed (e.g., 35s -> 36s)
    3. Per-substrate test-results.md - revert if only duration changed
    4. *.xlsx files - revert if content and formulas are identical to previous commit
    """
    print("=" * 60, flush=True)
    print("CLEANUP: Reverting files with no real changes", flush=True)
    print("=" * 60, flush=True)

    reverted_count = 0

    # 1. Check _substrate_results.json
    if revert_if_only_duration_changes(CENTRAL_RESULTS_PATH):
        reverted_count += 1

    # 2. Check all-tests-results.md
    if revert_md_if_only_timing_changes(SUMMARY_PATH):
        reverted_count += 1

    # 3. Find and check all changed files (staged or unstaged)
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True, text=True, cwd=PROJECT_ROOT
    )

    if result.returncode == 0:
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            # Format is: XY filename (where XY are status codes)
            rel_path = line[3:].strip()  # Skip status codes and space
            full_path = os.path.join(PROJECT_ROOT, rel_path)

            # Check xlsx files
            if rel_path.endswith('.xlsx'):
                if revert_xlsx_if_unchanged(full_path):
                    reverted_count += 1

            # Check per-substrate test-results.md files
            elif rel_path.endswith('test-results.md') and 'execution-substrates/' in rel_path:
                if revert_md_if_only_timing_changes(full_path):
                    reverted_count += 1

    if reverted_count == 0:
        print("  No files reverted (all changes are real)", flush=True)
    else:
        print(f"  Total files reverted: {reverted_count}", flush=True)

    print(flush=True)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60, flush=True)
    print("TEST ORCHESTRATOR (Generic / Domain-Agnostic)", flush=True)
    print("=" * 60, flush=True)
    print(flush=True)

    # Load rulebook
    rulebook = load_rulebook()
    entities = discover_entities(rulebook)
    print(f"Discovered {len(entities)} entities in rulebook: {', '.join(entities)}", flush=True)
    print(flush=True)

    # Connect to database
    try:
        conn = psycopg2.connect(DB_CONNECTION)
        print(f"Connected to database", flush=True)
    except Exception as e:
        print(f"ERROR: Failed to connect to database: {e}", flush=True)
        print(f"  Connection string: {DB_CONNECTION}", flush=True)
        sys.exit(1)

    print(flush=True)

    # Step 1: Generate answer keys from all views
    all_answer_keys = generate_all_answer_keys(conn, rulebook)
    print(flush=True)

    conn.close()

    # Step 2: Generate blank tests
    generate_all_blank_tests(all_answer_keys, rulebook)
    print(flush=True)

    # Step 3: Run and grade each substrate
    all_grades = run_and_grade_all_substrates(all_answer_keys, rulebook)
    print(flush=True)

    # Step 4: Generate summary report
    print("\n" * 3, flush=True)
    generate_summary_report(all_grades, rulebook)
    print(flush=True)

    # Step 5: Print final summary table
    print_final_summary_table(all_grades, rulebook)

    # Step 6: Clean up files with no real changes
    cleanup_unchanged_files()

    print("=" * 60, flush=True)
    print("DONE", flush=True)
    print("=" * 60, flush=True)


if __name__ == "__main__":
    main()
