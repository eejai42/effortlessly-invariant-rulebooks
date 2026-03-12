#!/usr/bin/env python3
# =============================================================================
# GENERATE-REPORT.PY
# =============================================================================
# Generates a comprehensive, self-contained HTML report from orchestration data.
# Includes all 12 substrates (11 generated + postgres as default answer-key substrate).
#
# Usage: python3 generate-report.py [--output path/to/report.html]
# =============================================================================

import argparse
import glob
import json
import os
import pickle
import re
from datetime import datetime
from html import escape

# =============================================================================
# PATHS
# =============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
TESTING_DIR = os.path.join(PROJECT_ROOT, "testing")
ANSWER_KEYS_DIR = os.path.join(TESTING_DIR, "answer-keys")
BLANK_TESTS_DIR = os.path.join(TESTING_DIR, "blank-tests")
SUBSTRATES_DIR = os.path.join(PROJECT_ROOT, "execution-substrates")
RULEBOOK_DIR = os.path.join(PROJECT_ROOT, "effortless-rulebook")
RULEBOOK_PATH = os.path.join(RULEBOOK_DIR, "effortless-rulebook.json")
POSTGRES_DIR = os.path.join(PROJECT_ROOT, "postgres")
SSOTME_JSON = os.path.join(PROJECT_ROOT, "ssotme.json")
DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, "orchestration-report.html")


# =============================================================================
# DATA COLLECTION
# =============================================================================

def load_rulebook():
    """Load the effortless-rulebook.json file"""
    if not os.path.exists(RULEBOOK_PATH):
        return {}
    with open(RULEBOOK_PATH, 'r') as f:
        return json.load(f)


def get_base_id():
    """Get the Airtable base ID from ssotme.json"""
    if not os.path.exists(SSOTME_JSON):
        return None
    try:
        with open(SSOTME_JSON, 'r') as f:
            config = json.load(f)
        for setting in config.get('ProjectSettings', []):
            if setting.get('Name') == 'baseId':
                return setting.get('Value', '')
    except Exception:
        pass
    return None


def to_snake_case(name: str) -> str:
    """Convert PascalCase to snake_case.

    Also handles fields with existing underscores: Bio_HockettScore -> bio_hockett_score
    """
    # Use [^_] to avoid doubling underscores when input already has them
    s1 = re.sub('([^_])([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def discover_entities(rulebook: dict) -> list:
    """Discover all entities from the rulebook"""
    entities = []
    skip_keys = {'$schema', 'model_name', 'Description', '_meta'}
    for key, value in rulebook.items():
        if key in skip_keys:
            continue
        if isinstance(value, dict) and 'schema' in value:
            entities.append(key)
    return entities


def to_pascal_case(name: str) -> str:
    """Convert snake_case to PascalCase"""
    return ''.join(word.capitalize() for word in name.split('_'))


def get_entity_data(rulebook: dict, entity_name: str) -> dict:
    """Get full entity data including description (handles both cases)"""
    if entity_name in rulebook:
        return rulebook[entity_name]
    # Try PascalCase
    pascal = to_pascal_case(entity_name)
    if pascal in rulebook:
        return rulebook[pascal]
    return {}


def get_entity_schema(rulebook: dict, entity_name: str) -> list:
    """Get schema for an entity (handles both cases)"""
    return get_entity_data(rulebook, entity_name).get('schema', [])


def get_entity_description(rulebook: dict, entity_name: str) -> str:
    """Get description for an entity"""
    return get_entity_data(rulebook, entity_name).get('Description', '')


def get_field_description(rulebook: dict, entity_name: str, field_name: str) -> str:
    """Get description for a field within an entity"""
    schema = get_entity_schema(rulebook, entity_name)
    # field_name is snake_case, schema field names are PascalCase
    pascal_field = to_pascal_case(field_name)
    for field in schema:
        if field['name'] == field_name or field['name'] == pascal_field:
            return field.get('Description', field.get('description', ''))
    return ''


def get_field_formula(rulebook: dict, entity_name: str, field_name: str) -> str:
    """Get formula for a field within an entity"""
    schema = get_entity_schema(rulebook, entity_name)
    pascal_field = to_pascal_case(field_name)
    for field in schema:
        if field['name'] == field_name or field['name'] == pascal_field:
            formula = field.get('formula', '')
            # Strip {{ and }} from field references for cleaner display
            formula = formula.replace('{{', '').replace('}}', '')
            return formula
    return ''


def load_metadata():
    """Load testing metadata"""
    metadata_path = os.path.join(TESTING_DIR, "_metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            return json.load(f)
    return {}


def load_answer_keys():
    """Load all answer keys"""
    answer_keys = {}
    if os.path.isdir(ANSWER_KEYS_DIR):
        for file in glob.glob(os.path.join(ANSWER_KEYS_DIR, "*.json")):
            entity = os.path.basename(file).replace('.json', '')
            with open(file, 'r') as f:
                answer_keys[entity] = json.load(f)
    return answer_keys


def load_blank_tests():
    """Load all blank tests with metadata about staleness.

    Blank tests represent the "raw, unprocessed" state of data before
    computed fields are filled in. They may be stale if the ontology
    has changed - this is pedagogically valuable as it demonstrates
    a key failure mode of natural language: staleness and the time
    required to update it.
    """
    blank_tests = {}
    if os.path.isdir(BLANK_TESTS_DIR):
        for file in glob.glob(os.path.join(BLANK_TESTS_DIR, "*.json")):
            entity = os.path.basename(file).replace('.json', '')
            try:
                stat = os.stat(file)
                mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
                with open(file, 'r') as f:
                    data = json.load(f)
                blank_tests[entity] = {
                    "data": data,
                    "last_modified": mtime,
                    "file_path": file
                }
            except Exception as e:
                blank_tests[entity] = {
                    "data": [],
                    "error": str(e),
                    "file_path": file
                }
    return blank_tests


def get_substrates():
    """Get list of all substrates (11 generated + postgres)"""
    substrates = ['postgres']  # postgres is first (default answer-key substrate)
    if os.path.isdir(SUBSTRATES_DIR):
        for name in sorted(os.listdir(SUBSTRATES_DIR)):
            path = os.path.join(SUBSTRATES_DIR, name)
            if os.path.isdir(path) and not name.startswith('.'):
                substrates.append(name)
    return substrates


def load_run_metadata(substrate_name: str) -> dict:
    """Load metadata for a substrate from the CENTRAL results file in testing/"""
    central_path = os.path.join(TESTING_DIR, "_substrate_results.json")
    if os.path.exists(central_path):
        with open(central_path, 'r') as f:
            central = json.load(f)
            return central.get(substrate_name, {"last_run": None, "last_successful_run": None})
    # Fallback to old per-substrate file for migration
    metadata_path = os.path.join(SUBSTRATES_DIR, substrate_name, "_run_metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, 'r') as f:
            return json.load(f)
    return {"last_run": None, "last_successful_run": None}


def load_substrate_grades(substrate_name: str) -> dict:
    """Load grades for a substrate from pickle or reconstruct from results"""
    # Try pickle file first (exists during orchestration)
    if substrate_name == 'postgres':
        # Postgres generates the answer key - always 100% by definition
        return {
            "substrate": "postgres",
            "is_answer_key": True,
            "total_fields_tested": 0,
            "fields_passed": 0,
            "fields_failed": 0,
            "elapsed_seconds": 0.0,
            "entities": {},
            "error": None
        }

    substrate_dir = os.path.join(SUBSTRATES_DIR, substrate_name)
    grades_file = os.path.join(substrate_dir, ".grades.pkl")

    if os.path.exists(grades_file):
        with open(grades_file, 'rb') as f:
            return pickle.load(f)

    # Try to reconstruct from test-results.md
    results_file = os.path.join(substrate_dir, "test-results.md")
    if os.path.exists(results_file):
        return parse_test_results_md(results_file, substrate_name)

    return {
        "substrate": substrate_name,
        "total_fields_tested": 0,
        "fields_passed": 0,
        "fields_failed": 0,
        "elapsed_seconds": 0.0,
        "entities": {},
        "error": "No results found"
    }


def parse_test_results_md(filepath: str, substrate_name: str) -> dict:
    """Parse test-results.md to extract grades"""
    grades = {
        "substrate": substrate_name,
        "total_fields_tested": 0,
        "fields_passed": 0,
        "fields_failed": 0,
        "elapsed_seconds": 0.0,
        "entities": {},
        "error": None
    }

    with open(filepath, 'r') as f:
        content = f.read()

    # Extract summary metrics
    total_match = re.search(r'\| Total Fields Tested \| (\d+) \|', content)
    passed_match = re.search(r'\| Passed \| (\d+) \|', content)
    failed_match = re.search(r'\| Failed \| (\d+) \|', content)
    duration_match = re.search(r'\| Duration \| ([\d.]+)s \|', content)

    if total_match:
        grades["total_fields_tested"] = int(total_match.group(1))
    if passed_match:
        grades["fields_passed"] = int(passed_match.group(1))
    if failed_match:
        grades["fields_failed"] = int(failed_match.group(1))
    if duration_match:
        grades["elapsed_seconds"] = float(duration_match.group(1))

    # Extract per-entity results with failure details
    # Split content by entity sections (### entity_name)
    entity_pattern = r'### (\w+)\n\n- Fields: (\d+)/(\d+)'
    entity_matches = list(re.finditer(entity_pattern, content))

    for i, match in enumerate(entity_matches):
        entity = match.group(1)
        passed = int(match.group(2))
        total = int(match.group(3))

        # Get the section content (from this match to the next entity or end)
        start = match.end()
        end = entity_matches[i + 1].start() if i + 1 < len(entity_matches) else len(content)
        section_content = content[start:end]

        # Parse failure table rows: | pk | field | expected | actual |
        # Skip header row (PK | Field | Expected | Actual) and separator (|-----|...)
        failure_rows = re.findall(
            r'\| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|',
            section_content
        )

        failures = []
        for row in failure_rows:
            pk, field, expected, actual = [cell.strip() for cell in row]
            # Skip header and separator rows
            if pk in ('PK', '-----', '...') or field in ('Field', '-------'):
                continue
            failures.append({
                "pk": pk,
                "field": field,
                "expected": expected,
                "actual": actual
            })

        grades["entities"][entity] = {
            "fields_tested": total,
            "fields_passed": passed,
            "fields_failed": total - passed,
            "failures": failures
        }

    return grades


def load_substrate_report_content(substrate_name: str) -> dict:
    """Load and parse substrate-report.html to extract tab content.

    Returns dict with 'tabs' list of {id, label} and 'contents' dict of {id: html_content}
    """
    if substrate_name == 'postgres':
        return {"tabs": [], "contents": {}}

    report_path = os.path.join(SUBSTRATES_DIR, substrate_name, "substrate-report.html")
    if not os.path.exists(report_path):
        return {"tabs": [], "contents": {}}

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Parse tabs: <button class="tab..." data-tab="...">Label</button>
        tabs = []
        tab_pattern = r'<button[^>]*class="tab[^"]*"[^>]*data-tab="([^"]+)"[^>]*>([^<]+)</button>'
        for match in re.finditer(tab_pattern, html_content):
            tab_id = match.group(1)
            tab_label = match.group(2).strip()
            tabs.append({"id": tab_id, "label": tab_label})

        # Parse tab contents using balanced div matching
        contents = {}
        for tab in tabs:
            tab_id = tab["id"]
            # Find the start of this tab's content div
            start_pattern = rf'<div\s+id="{tab_id}"\s+class="tab-content[^"]*"[^>]*>'
            start_match = re.search(start_pattern, html_content)
            if not start_match:
                continue

            # Find the matching closing </div> by counting nesting
            start_pos = start_match.end()
            depth = 1
            pos = start_pos
            while depth > 0 and pos < len(html_content):
                # Find next <div or </div>
                next_open = html_content.find('<div', pos)
                next_close = html_content.find('</div>', pos)

                if next_close == -1:
                    break

                if next_open != -1 and next_open < next_close:
                    # Check if it's actually a div tag (not just containing "div")
                    if html_content[next_open:next_open+5] in ('<div ', '<div>'):
                        depth += 1
                    pos = next_open + 4
                else:
                    depth -= 1
                    if depth == 0:
                        contents[tab_id] = html_content[start_pos:next_close].strip()
                    pos = next_close + 6

        return {"tabs": tabs, "contents": contents}
    except Exception as e:
        print(f"Warning: Could not parse substrate report for {substrate_name}: {e}")
        return {"tabs": [], "contents": {}}


def load_substrate_test_answers(substrate_name: str) -> dict:
    """Load test answers from a substrate"""
    if substrate_name == 'postgres':
        return load_answer_keys()

    answers = {}
    answers_dir = os.path.join(SUBSTRATES_DIR, substrate_name, "test-answers")
    if os.path.isdir(answers_dir):
        for file in glob.glob(os.path.join(answers_dir, "*.json")):
            entity = os.path.basename(file).replace('.json', '')
            try:
                with open(file, 'r') as f:
                    answers[entity] = json.load(f)
            except:
                pass
    return answers


def collect_all_data():
    """Collect all data needed for the report"""
    rulebook = load_rulebook()
    metadata = load_metadata()
    answer_keys = load_answer_keys()
    substrates = get_substrates()

    # Collect schema info
    entities_schema = {}
    for entity_name in discover_entities(rulebook):
        snake_name = to_snake_case(entity_name)
        schema = rulebook.get(entity_name, {}).get('schema', [])
        entities_schema[snake_name] = {
            "pascal_name": entity_name,
            "schema": schema,
            "data": rulebook.get(entity_name, {}).get('data', [])
        }

    # Collect grades for all substrates
    all_grades = {}
    for substrate in substrates:
        grades = load_substrate_grades(substrate)

        # For postgres, calculate based on answer keys
        if substrate == 'postgres':
            total_computed = 0
            for entity, meta in metadata.items():
                computed_cols = meta.get('computed_columns', [])
                record_count = meta.get('record_count', 0)
                total_computed += len(computed_cols) * record_count
                grades["entities"][entity] = {
                    "fields_tested": len(computed_cols) * record_count,
                    "fields_passed": len(computed_cols) * record_count,
                    "fields_failed": 0,
                    "failures": [],
                    "computed_columns": computed_cols
                }
            grades["total_fields_tested"] = total_computed
            grades["fields_passed"] = total_computed

        # Load run metadata (for tracking failure/success status)
        if substrate != 'postgres':
            run_meta = load_run_metadata(substrate)
            grades["run_metadata"] = run_meta

            # Use duration from central metadata (last_successful_run) as source of truth
            last_success = run_meta.get("last_successful_run")
            if last_success and "duration_seconds" in last_success:
                grades["elapsed_seconds"] = last_success["duration_seconds"]
        else:
            grades["run_metadata"] = {"last_run": None, "last_successful_run": None}

        # Load test answers for this substrate
        grades["test_answers"] = load_substrate_test_answers(substrate)

        # Load substrate report content (tabs and their HTML)
        grades["report_content"] = load_substrate_report_content(substrate)

        all_grades[substrate] = grades

    # Build report data structure
    # Use Name from rulebook as the report title, fallback to directory name
    rulebook_name = rulebook.get("Name", os.path.basename(PROJECT_ROOT))
    report_data = {
        "meta": {
            "project_name": rulebook_name,
            "directory_name": os.path.basename(PROJECT_ROOT),
            "rulebook_path": RULEBOOK_PATH,
            "rulebook_name": rulebook_name,
            "rulebook_description": rulebook.get("Description", ""),
            "base_id": get_base_id()
        },
        "summary": {
            "total_substrates": len(substrates),
            "passing_substrates": sum(
                1 for g in all_grades.values()
                if g["fields_failed"] == 0 and g["total_fields_tested"] > 0
            ),
            "total_entities": len(metadata),
            "total_computed_columns": sum(
                len(m.get("computed_columns", []))
                for m in metadata.values()
            ),
            "total_records": sum(
                m.get("record_count", 0)
                for m in metadata.values()
            )
        },
        "entities": {},
        "substrates": all_grades,
        "answer_keys": answer_keys
    }

    # Build entity info with answer keys and descriptions
    for entity_name, meta in metadata.items():
        computed_cols = meta.get("computed_columns", [])
        # Build computed columns with formulas and descriptions
        computed_columns_info = []
        for col in computed_cols:
            computed_columns_info.append({
                "name": col,
                "formula": get_field_formula(rulebook, entity_name, col),
                "description": get_field_description(rulebook, entity_name, col)
            })

        report_data["entities"][entity_name] = {
            "primary_key": meta.get("primary_key"),
            "computed_columns": computed_cols,
            "computed_columns_info": computed_columns_info,
            "record_count": meta.get("record_count", 0),
            "schema": entities_schema.get(entity_name, {}).get("schema", []),
            "description": get_entity_description(rulebook, entity_name),
            "answer_key": answer_keys.get(entity_name, [])
        }

    # Calculate overall stats
    total_passed = sum(g["fields_passed"] for g in all_grades.values())
    total_failed = sum(g["fields_failed"] for g in all_grades.values())
    total_tested = sum(g["total_fields_tested"] for g in all_grades.values())
    total_time = sum(g.get("elapsed_seconds", 0) for g in all_grades.values())

    report_data["summary"]["overall_score"] = (
        (total_passed / total_tested * 100) if total_tested > 0 else 0
    )
    report_data["summary"]["total_runtime_seconds"] = total_time
    report_data["summary"]["total_fields_tested"] = total_tested
    report_data["summary"]["total_passed"] = total_passed
    report_data["summary"]["total_failed"] = total_failed

    return report_data


# =============================================================================
# HTML GENERATION
# =============================================================================

def generate_html(data: dict) -> str:
    """Generate self-contained HTML report"""

    # Escape data for embedding in JS
    json_data = json.dumps(data, default=str, indent=2)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(data["meta"]["project_name"])}</title>
    <style>
{get_css()}
    </style>
</head>
<body>
    <header>
        <div class="header-content">
            <h1>{escape(data["meta"]["project_name"])}</h1>
            <div class="header-meta">
                <span class="project-name">Orchestration Report</span>
            </div>
        </div>
        <div class="header-actions">
            {f'<a href="https://airtable.com/{data["meta"]["base_id"]}" target="_blank" class="airtable-link" title="Open in Airtable">Airtable &#8599;</a>' if data["meta"].get("base_id") else ''}
            <button id="theme-toggle" title="Toggle dark/light mode">
                <span class="sun">&#9728;</span>
                <span class="moon">&#9790;</span>
            </button>
        </div>
    </header>

    <nav class="tabs" id="main-tabs">
        <button class="tab active" data-tab="overview">Overview</button>
        <button class="tab" data-tab="substrates">Conformance Test Results</button>
        <button class="tab" data-tab="entities">Entities</button>
    </nav>

    <main>
        <section id="overview" class="tab-content active">
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value" id="passing-count">
                        {data["summary"]["passing_substrates"]} / {data["summary"]["total_substrates"]}
                    </div>
                    <div class="stat-label">Tests Passing</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value score-{get_score_class(data["summary"]["overall_score"])}">
                        {data["summary"]["overall_score"]:.1f}%
                    </div>
                    <div class="stat-label">Overall Score</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">
                        {data["summary"]["total_runtime_seconds"]:.1f}s
                    </div>
                    <div class="stat-label">Total Runtime</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">
                        {data["summary"]["total_entities"]}
                    </div>
                    <div class="stat-label">Entities</div>
                </div>
            </div>

            <h2>Conformance Test Results</h2>
            <div class="substrate-links">
                {generate_substrate_links(data)}
            </div>

            <h2>Conformance Test Matrix</h2>
            <div class="matrix-container">
                <table class="health-matrix" id="health-matrix">
                    <thead>
                        <tr>
                            <th>Substrate</th>
                            {generate_entity_headers(data)}
                            <th>Score</th>
                            <th>Time</th>
                            <th style="min-width: 120px;">Runtime</th>
                        </tr>
                    </thead>
                    <tbody>
                        {generate_matrix_rows(data)}
                    </tbody>
                </table>
            </div>
        </section>

        <section id="substrates" class="tab-content">
            <nav class="sub-tabs" id="substrate-tabs">
                {generate_substrate_tabs(data)}
            </nav>
            <div id="substrate-details"></div>
        </section>

        <section id="entities" class="tab-content">
            <nav class="sub-tabs" id="entity-tabs">
                {generate_entity_tabs(data)}
            </nav>
            <div id="entity-details"></div>
        </section>

    </main>

    <footer>
        <p>Generated by ERB Test Orchestrator</p>
    </footer>

    <script>
const REPORT_DATA = {json_data};

{get_javascript()}
    </script>
</body>
</html>'''

    return html


def get_score_class(score: float) -> str:
    """Get CSS class for score coloring"""
    if score >= 100:
        return "perfect"
    elif score >= 80:
        return "good"
    elif score >= 60:
        return "warning"
    else:
        return "danger"


def sorted_substrates(data: dict) -> list:
    """Sort substrates: 100% first (by time), <100% at bottom (by score desc)

    Uses 0.5s time buckets and name as tiebreaker for deterministic ordering.
    """
    def sort_key(name):
        g = data["substrates"][name]
        elapsed = g.get("elapsed_seconds", 0.0)
        # Round to 0.5s buckets for sorting stability
        elapsed_bucket = round(elapsed * 2) / 2
        p = g["fields_passed"]
        t = g["total_fields_tested"]
        score = (p / t * 100) if t > 0 else 0
        is_perfect = score >= 100.0
        # Use name as tiebreaker for deterministic ordering
        return (0 if is_perfect else 1, elapsed_bucket if is_perfect else -score, name)
    return sorted(data["substrates"].keys(), key=sort_key)


def generate_entity_headers(data: dict) -> str:
    """Generate table headers for entities with clickable links"""
    headers = []
    for entity in sorted(data["entities"].keys()):
        headers.append(f'<th class="entity-col entity-link" data-entity="{escape(entity)}">{escape(entity)}</th>')
    return '\n                            '.join(headers)


def generate_matrix_rows(data: dict) -> str:
    """Generate matrix rows for each substrate"""
    rows = []
    entities = sorted(data["entities"].keys())

    for substrate_name in sorted_substrates(data):
        grades = data["substrates"][substrate_name]
        is_answer_key = grades.get("is_answer_key", False)

        total = grades["total_fields_tested"]
        passed = grades["fields_passed"]
        score = (passed / total * 100) if total > 0 else 0
        elapsed = grades.get("elapsed_seconds", 0)

        # Check run metadata for failure status
        run_meta = grades.get("run_metadata", {})
        last_run = run_meta.get("last_run", {})
        last_success = run_meta.get("last_successful_run", {})
        has_failure = last_run.get("status") == "failure" if last_run else False
        is_restored = has_failure and last_success is not None

        row_class = "answer-key-row" if is_answer_key else ("restored-row" if is_restored else "")
        score_class = get_score_class(score)

        cells = []

        # Substrate name cell with warning badge if last run failed
        substrate_label = f"{substrate_name} (answer-key)" if is_answer_key else substrate_name
        warning_badge = ""
        if is_restored:
            error_msg = last_run.get("error_message", "Unknown error")
            warning_badge = f' <span class="warning-badge" title="Last run failed: {escape(error_msg)}">&#9888;</span>'
        cells.append(f'<td class="substrate-name substrate-row-link" data-substrate="{escape(substrate_name)}">{escape(substrate_label)}{warning_badge}</td>')

        # Entity cells
        for entity in entities:
            entity_grades = grades.get("entities", {}).get(entity, {})
            e_total = entity_grades.get("fields_tested", 0)
            e_passed = entity_grades.get("fields_passed", 0)
            e_failed = entity_grades.get("fields_failed", 0)

            if is_answer_key:
                cell_class = "cell-answer-key"
                symbol = "&#9733;"  # star
            elif e_total == 0:
                cell_class = "cell-na"
                symbol = "&mdash;"
            elif e_failed == 0:
                cell_class = "cell-pass"
                symbol = "&#10003;"  # checkmark
            else:
                cell_class = "cell-fail"
                symbol = f"{e_failed}"

            cells.append(
                f'<td class="{cell_class}" '
                f'data-substrate="{escape(substrate_name)}" '
                f'data-entity="{escape(entity)}" '
                f'title="{e_passed}/{e_total}">{symbol}</td>'
            )

        # Score cell
        if is_answer_key:
            cells.append('<td class="score-cell score-perfect">100%</td>')
        else:
            cells.append(f'<td class="score-cell score-{score_class}">{score:.1f}%</td>')

        # Time cell
        cells.append(f'<td class="time-cell">{elapsed:.1f}s</td>')

        rows.append(f'<tr class="{row_class}">{"".join(cells)}</tr>')

    return '\n                        '.join(rows)


def generate_entity_options(data: dict) -> str:
    """Generate <option> elements for entity selector"""
    options = []
    for entity in sorted(data["entities"].keys()):
        options.append(f'<option value="{escape(entity)}">{escape(entity)}</option>')
    return '\n                    '.join(options)


def generate_substrate_options(data: dict) -> str:
    """Generate <option> elements for substrate selector"""
    options = []
    for substrate in sorted_substrates(data):
        is_answer_key = data["substrates"][substrate].get("is_answer_key", False)
        label = f"{substrate} (answer-key)" if is_answer_key else substrate
        options.append(f'<option value="{escape(substrate)}">{escape(label)}</option>')
    return '\n                    '.join(options)


def generate_entity_tabs(data: dict) -> str:
    """Generate tab buttons for entity selector"""
    tabs = []
    for i, entity in enumerate(sorted(data["entities"].keys())):
        active = "active" if i == 0 else ""
        tabs.append(f'<button class="sub-tab {active}" data-entity="{escape(entity)}">{escape(entity)}</button>')
    return '\n                '.join(tabs)


def generate_substrate_tabs(data: dict) -> str:
    """Generate tab buttons for substrate selector"""
    tabs = []
    for i, substrate in enumerate(sorted_substrates(data)):
        is_answer_key = data["substrates"][substrate].get("is_answer_key", False)
        label = f"{substrate} (answer-key)" if is_answer_key else substrate
        active = "active" if i == 0 else ""
        tabs.append(f'<button class="sub-tab {active}" data-substrate="{escape(substrate)}">{escape(label)}</button>')
    return '\n                '.join(tabs)


def generate_substrate_links(data: dict) -> str:
    """Generate clickable substrate links for overview"""
    links = []
    for substrate in sorted_substrates(data):
        grades = data["substrates"][substrate]
        is_answer_key = grades.get("is_answer_key", False)
        total = grades["total_fields_tested"]
        passed = grades["fields_passed"]
        score = (passed / total * 100) if total > 0 else 0
        score_class = get_score_class(score)
        label = f"{substrate} (answer-key)" if is_answer_key else substrate
        links.append(f'<a href="#" class="substrate-link score-{score_class}" data-substrate="{escape(substrate)}">{escape(label)}: {score:.0f}%</a>')
    return '\n                    '.join(links)


def generate_failure_details(data: dict) -> str:
    """Generate failure detail cards"""
    failures = []

    for substrate_name, grades in sorted(data["substrates"].items()):
        if grades.get("is_answer_key"):
            continue

        for entity_name, entity_grades in grades.get("entities", {}).items():
            for failure in entity_grades.get("failures", []):
                failures.append({
                    "substrate": substrate_name,
                    "entity": entity_name,
                    "pk": failure.get("pk"),
                    "field": failure.get("field"),
                    "expected": failure.get("expected"),
                    "actual": failure.get("actual")
                })

    if not failures:
        return '<div class="no-failures">No failures to display</div>'

    html_parts = []
    for f in failures[:50]:  # Limit to 50 failures in initial render
        html_parts.append(f'''
            <div class="failure-card">
                <div class="failure-header">
                    <span class="failure-substrate">{escape(str(f["substrate"]))}</span>
                    <span class="failure-arrow">&rarr;</span>
                    <span class="failure-entity">{escape(str(f["entity"]))}</span>
                    <span class="failure-arrow">&rarr;</span>
                    <span class="failure-field">{escape(str(f["field"]))}</span>
                </div>
                <div class="failure-body">
                    <div class="failure-row">
                        <span class="failure-label">Record:</span>
                        <span class="failure-value">{escape(str(f["pk"]))}</span>
                    </div>
                    <div class="failure-row">
                        <span class="failure-label">Expected:</span>
                        <code class="expected">{escape(str(f["expected"]))}</code>
                    </div>
                    <div class="failure-row">
                        <span class="failure-label">Actual:</span>
                        <code class="actual">{escape(str(f["actual"]))}</code>
                    </div>
                </div>
            </div>
        ''')

    if len(failures) > 50:
        html_parts.append(
            f'<div class="more-failures">...and {len(failures) - 50} more failures</div>'
        )

    return '\n'.join(html_parts)


def get_css() -> str:
    """Return embedded CSS - Desktop optimized with compact tables"""
    return '''
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --bg-tertiary: #e9ecef;
    --text-primary: #212529;
    --text-secondary: #6c757d;
    --border-color: #dee2e6;
    --accent-color: #0d6efd;
    --success-color: #198754;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
    --answer-key-color: #6f42c1;
    --shadow: 0 2px 8px rgba(0,0,0,0.1);
    --radius: 6px;
}

[data-theme="dark"] {
    --bg-primary: #1a1a2e;
    --bg-secondary: #16213e;
    --bg-tertiary: #0f3460;
    --text-primary: #eaeaea;
    --text-secondary: #b0b0b0;
    --border-color: #3a3a5c;
    --accent-color: #4dabf7;
    --success-color: #51cf66;
    --warning-color: #fcc419;
    --danger-color: #ff6b6b;
    --answer-key-color: #b197fc;
    --shadow: 0 2px 8px rgba(0,0,0,0.3);
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg-secondary);
    color: var(--text-primary);
    line-height: 1.4;
    min-height: 100vh;
}

header {
    background: var(--bg-primary);
    border-bottom: 1px solid var(--border-color);
    padding: 0.75rem 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    position: sticky;
    top: 0;
    z-index: 100;
    box-shadow: var(--shadow);
}

.header-content h1 { font-size: 1.25rem; font-weight: 600; }
.header-meta { display: flex; gap: 1rem; font-size: 0.8rem; color: var(--text-secondary); }
.project-name { font-weight: 500; }
.header-actions { display: flex; align-items: center; gap: 0.75rem; }
.airtable-link {
    font-size: 0.85rem;
    color: var(--text-secondary);
    text-decoration: none;
    padding: 0.35rem 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    transition: all 0.15s ease;
}
.airtable-link:hover {
    color: var(--accent-color);
    border-color: var(--accent-color);
    background: var(--bg-secondary);
}

#theme-toggle {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 50%;
    width: 32px; height: 32px;
    cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
    transition: all 0.2s;
}
#theme-toggle:hover { background: var(--accent-color); color: white; }
#theme-toggle .moon { display: none; }
[data-theme="dark"] #theme-toggle .sun { display: none; }
[data-theme="dark"] #theme-toggle .moon { display: inline; }

.tabs {
    display: flex;
    gap: 0;
    background: var(--bg-primary);
    padding: 0 1.5rem;
    border-bottom: 1px solid var(--border-color);
    overflow-x: auto;
}

.tab {
    background: none;
    border: none;
    padding: 0.6rem 1.25rem;
    cursor: pointer;
    font-size: 0.875rem;
    color: var(--text-secondary);
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
    white-space: nowrap;
}
.tab:hover { color: var(--text-primary); background: var(--bg-secondary); }
.tab.active { color: var(--accent-color); border-bottom-color: var(--accent-color); font-weight: 500; }

main {
    padding: 1rem 1.5rem;
    width: 100%;
}

.tab-content { display: none; }
.tab-content.active { display: block; animation: fadeIn 0.2s ease; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.stats-grid {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.stat-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    padding: 0.75rem 1.25rem;
    text-align: center;
    box-shadow: var(--shadow);
    min-width: 140px;
}

.stat-value { font-size: 1.5rem; font-weight: 700; }
.stat-label { font-size: 0.75rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em; }

.score-perfect { color: var(--success-color); }
.score-good { color: var(--success-color); }
.score-warning { color: var(--warning-color); }
.score-danger { color: var(--danger-color); }

h2 { font-size: 1rem; font-weight: 600; margin-bottom: 0.75rem; color: var(--text-primary); }

/* Matrix and table containers - horizontal scroll */
.matrix-container, .table-scroll {
    overflow-x: auto;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
}

.health-matrix {
    border-collapse: collapse;
    font-size: 0.8rem;
    white-space: nowrap;
}

.health-matrix th,
.health-matrix td {
    padding: 0.4rem 0.75rem;
    text-align: center;
    border-bottom: 1px solid var(--border-color);
}

.health-matrix th {
    background: var(--bg-tertiary);
    font-weight: 600;
    text-transform: uppercase;
    font-size: 0.7rem;
    letter-spacing: 0.05em;
    color: var(--text-secondary);
}

.health-matrix .substrate-name { text-align: left; font-weight: 500; }
.health-matrix .entity-col { min-width: 80px; }

.cell-pass { background: rgba(25, 135, 84, 0.15); color: var(--success-color); font-weight: 600; }
.cell-fail { background: rgba(220, 53, 69, 0.15); color: var(--danger-color); font-weight: 600; cursor: pointer; }
.cell-fail:hover { background: rgba(220, 53, 69, 0.25); }
.cell-na { color: var(--text-secondary); }
.cell-answer-key { background: rgba(111, 66, 193, 0.15); color: var(--answer-key-color); font-weight: 600; }
.answer-key-row { background: rgba(111, 66, 193, 0.05); }
.answer-key-row .substrate-name { color: var(--answer-key-color); }
.restored-row { background: rgba(255, 193, 7, 0.08); }
.warning-badge { color: var(--warning-color); font-size: 0.85rem; cursor: help; margin-left: 0.25rem; }
.score-cell { font-weight: 600; }
.time-cell { color: var(--text-secondary); font-family: monospace; font-size: 0.75rem; }

/* Runtime bar in health matrix */
.runtime-bar-cell {
    min-width: 100px;
    padding: 0.4rem 0.5rem;
}

/* Sub-tabs - horizontal scrolling */
.sub-tabs {
    display: flex;
    gap: 0.35rem;
    margin-bottom: 1rem;
    padding: 0.35rem;
    background: var(--bg-tertiary);
    border-radius: var(--radius);
    overflow-x: auto;
    white-space: nowrap;
}

.sub-tab {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    padding: 0.35rem 0.75rem;
    cursor: pointer;
    font-size: 0.8rem;
    color: var(--text-secondary);
    border-radius: var(--radius);
    transition: all 0.15s;
    flex-shrink: 0;
}
.sub-tab:hover { color: var(--text-primary); border-color: var(--accent-color); }
.sub-tab.active { color: var(--accent-color); border-color: var(--accent-color); font-weight: 500; }

.substrate-links {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.substrate-link {
    padding: 0.35rem 0.75rem;
    border-radius: var(--radius);
    text-decoration: none;
    font-weight: 500;
    font-size: 0.8rem;
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
    transition: all 0.15s;
}
.substrate-link:hover { transform: translateY(-1px); box-shadow: var(--shadow); }

.entity-link, .substrate-row-link { cursor: pointer; transition: all 0.15s; }
.entity-link:hover, .substrate-row-link:hover { color: var(--accent-color) !important; }

#entity-details, #substrate-details {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    padding: 1rem;
    box-shadow: var(--shadow);
}

/* Compact schema table */
.schema-table {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 1rem;
    font-size: 0.8rem;
}
.schema-table th, .schema-table td {
    padding: 0.35rem 0.5rem;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
}
.schema-table th { background: var(--bg-tertiary); font-weight: 600; }
.type-raw { color: var(--text-secondary); }
.type-calculated { color: var(--accent-color); font-weight: 500; }
.formula-cell {
    font-family: monospace;
    font-size: 0.75rem;
    color: var(--answer-key-color);
    min-width: 200px;
    max-width: 400px;
    vertical-align: top;
}
.formula-pre {
    margin: 0;
    padding: 0.25rem 0.4rem;
    background: var(--bg-tertiary);
    border-radius: 3px;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: monospace;
    font-size: 0.75rem;
}
.desc-cell {
    font-size: 0.75rem;
    color: var(--text-secondary);
    min-width: 150px;
    max-width: 350px;
    vertical-align: top;
}
.desc-text {
    display: block;
    white-space: pre-wrap;
    word-break: break-word;
}

.entity-header { margin-bottom: 0.75rem; }
.entity-header h3 { font-size: 1rem; margin-bottom: 0.25rem; }

/* Compact data table with ellipsis */
.data-table {
    border-collapse: collapse;
    font-size: 0.8rem;
}
.data-table th, .data-table td {
    padding: 0.3rem 0.5rem;
    text-align: left;
    border: 1px solid var(--border-color);
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}
.data-table th { background: var(--bg-tertiary); font-weight: 600; font-size: 0.75rem; }
.data-table .computed { background: rgba(13, 110, 253, 0.1); }

/* Blank tests section */
.blank-tests-section { margin-bottom: 1.5rem; }
.blank-tests-section h4 { margin-bottom: 0.5rem; }
.blank-tests-section h4 .subtitle { font-weight: normal; font-size: 0.85rem; color: var(--text-secondary); }
.blank-tests-intro { font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 1rem; line-height: 1.5; }
.blank-tests-intro code { background: var(--bg-tertiary); padding: 0.1rem 0.3rem; border-radius: 3px; }
.blank-test-entity { margin-bottom: 1rem; }
.blank-test-header {
    display: flex;
    gap: 1rem;
    align-items: center;
    padding: 0.5rem 0.75rem;
    background: var(--bg-secondary);
    border-radius: var(--radius);
    margin-bottom: 0.5rem;
    font-size: 0.85rem;
}
.blank-test-header.stale { background: rgba(255, 193, 7, 0.15); border-left: 3px solid var(--warning-color); }
.blank-test-header .entity-name { font-weight: 600; }
.blank-test-header .record-count { color: var(--text-secondary); }
.blank-test-header .last-modified { color: var(--text-secondary); font-size: 0.8rem; }
.blank-test-header .stale-warning { color: var(--warning-color); font-weight: 500; margin-left: auto; }
/* Stale entity styling */
.stale-entity { background: rgba(255, 193, 7, 0.1) !important; border-left: 3px solid var(--warning-color); }
.stale-entity-section { margin-top: 0.5rem; }
.stale-entity-warning {
    background: rgba(255, 193, 7, 0.15);
    border: 1px solid var(--warning-color);
    border-left: 3px solid var(--warning-color);
    border-radius: var(--radius);
    padding: 0.75rem 1rem;
    margin-bottom: 1rem;
}
.stale-entity-warning strong { color: var(--warning-color); display: block; margin-bottom: 0.5rem; }
.stale-entity-warning p { margin: 0.5rem 0; font-size: 0.85rem; line-height: 1.5; }
.stale-entity-warning code { background: var(--bg-tertiary); padding: 0.1rem 0.3rem; border-radius: 3px; }
.stale-explanation { color: var(--text-secondary); font-style: italic; }
.stale-data-table { opacity: 0.85; }
.stale-data-table .null-value { color: var(--text-secondary); font-style: italic; }

/* Warnings and failures */
.warning-banner {
    background: rgba(255, 193, 7, 0.15);
    border: 1px solid var(--warning-color);
    border-left: 3px solid var(--warning-color);
    border-radius: var(--radius);
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.75rem;
    font-size: 0.8rem;
}
.warning-banner strong { color: var(--warning-color); margin-right: 0.5rem; }
.warning-banner code { background: var(--bg-tertiary); padding: 0.1rem 0.25rem; border-radius: 3px; font-size: 0.75rem; }

.failure-card {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-left: 3px solid var(--danger-color);
    border-radius: var(--radius);
    padding: 0.5rem 0.75rem;
    margin-bottom: 0.5rem;
    font-size: 0.8rem;
}

code.expected { background: rgba(25, 135, 84, 0.15); color: var(--success-color); padding: 0.1rem 0.25rem; border-radius: 3px; }
code.actual { background: rgba(220, 53, 69, 0.15); color: var(--danger-color); padding: 0.1rem 0.25rem; border-radius: 3px; }

.no-failures, .no-results { text-align: center; padding: 1.5rem; color: var(--text-secondary); }

/* Substrate info bar */
.substrate-info { margin-bottom: 1rem; }
.substrate-info h3 { font-size: 1.1rem; margin-bottom: 0.25rem; }
.substrate-stats { display: flex; gap: 1.5rem; font-size: 0.85rem; }
.substrate-stat { display: flex; gap: 0.35rem; align-items: center; }
.substrate-stat-label { color: var(--text-secondary); }
.substrate-stat-value { font-weight: 600; }

/* Collapsible schema/formula section */
details { margin-bottom: 0.75rem; }
summary {
    cursor: pointer;
    font-weight: 500;
    font-size: 0.85rem;
    padding: 0.4rem 0.6rem;
    background: var(--bg-tertiary);
    border-radius: var(--radius);
    user-select: none;
    display: inline-block;
}
summary:hover { background: var(--bg-secondary); }
details[open] summary { margin-bottom: 0.5rem; }

footer {
    text-align: center;
    padding: 1rem;
    color: var(--text-secondary);
    font-size: 0.75rem;
    border-top: 1px solid var(--border-color);
    margin-top: 1.5rem;
}

/* Entity tabs within substrate view */
.entity-tabs-container { margin-bottom: 1rem; }
.entity-tab-content { display: none; }
.entity-tab-content.active { display: block; }

/* Graded test table - COMPACT */
.entity-test-section {
    background: var(--bg-secondary);
    border-radius: var(--radius);
    border: 1px solid var(--border-color);
    padding: 0.75rem;
}

.entity-test-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}
.entity-name { font-size: 1rem; font-weight: 600; }
.entity-score {
    font-size: 0.8rem;
    font-weight: 600;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    background: var(--bg-tertiary);
}

.entity-description {
    color: var(--text-secondary);
    font-size: 0.8rem;
    margin-bottom: 0.5rem;
    font-style: italic;
}

/* Computed columns - hidden in collapsible */
.computed-cols-info {
    font-size: 0.8rem;
    padding: 0.5rem;
    background: var(--bg-primary);
    border-radius: var(--radius);
}
.computed-cols-info ul { margin: 0.5rem 0 0 0; padding: 0; list-style: none; }
.computed-cols-info li {
    margin-bottom: 0.35rem;
    padding: 0.35rem 0.5rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    border-left: 2px solid var(--accent-color);
}
.computed-cols-info .field-name {
    font-weight: 600;
    font-family: monospace;
    font-size: 0.8rem;
    color: var(--accent-color);
}
.computed-cols-info .formula-row { display: block; margin-top: 0.25rem; }
.computed-cols-info .formula-label { color: var(--text-secondary); font-size: 0.7rem; text-transform: uppercase; margin-right: 0.35rem; }
.computed-cols-info .formula {
    font-family: monospace;
    font-size: 0.75rem;
    color: var(--answer-key-color);
    background: var(--bg-tertiary);
    padding: 0.35rem 0.5rem;
    border-radius: 3px;
    white-space: pre-wrap;
    word-break: break-word;
    display: block;
    margin-top: 0.25rem;
    line-height: 1.5;
}
.computed-cols-info .desc-row { display: block; color: var(--text-secondary); font-size: 0.75rem; font-style: italic; margin-top: 0.25rem; white-space: pre-wrap; word-break: break-word; line-height: 1.5; }

/* Graded test table - VERY COMPACT with ellipsis */
.graded-test-table {
    border-collapse: collapse;
    background: var(--bg-primary);
    font-size: 0.8rem;
}

.graded-test-table th,
.graded-test-table td {
    padding: 0.3rem 0.5rem;
    text-align: left;
    border: 1px solid var(--border-color);
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.graded-test-table th {
    background: var(--bg-tertiary);
    font-weight: 600;
    font-size: 0.75rem;
    position: sticky;
    top: 0;
}

.graded-test-table .computed-col-header {
    background: rgba(13, 110, 253, 0.15);
    color: var(--accent-color);
}

.graded-test-table .record-pk {
    font-family: monospace;
    font-weight: 500;
    background: var(--bg-secondary);
    max-width: 180px;
}

.graded-test-table .cell-passed {
    background: rgba(25, 135, 84, 0.08);
}
.graded-test-table .cell-passed .check-mark {
    color: var(--success-color);
    font-weight: bold;
    margin-right: 0.25rem;
}
.graded-test-table .cell-passed code {
    font-family: monospace;
    font-size: 0.75rem;
    color: var(--text-primary);
}

.graded-test-table .cell-failed {
    background: rgba(220, 53, 69, 0.1);
}
.graded-test-table .cell-failed .expected-actual {
    display: block;
    font-size: 0.7rem;
    margin-bottom: 0.1rem;
}
.graded-test-table .cell-failed .expected-actual:last-child { margin-bottom: 0; }
.graded-test-table .expected-label, .graded-test-table .actual-label {
    font-weight: 500;
    color: var(--text-secondary);
    margin-right: 0.25rem;
}

/* Raw fact cells - no special styling, just display the value */
.graded-test-table .cell-raw {
    font-family: monospace;
    font-size: 0.75rem;
    color: var(--text-secondary);
}

/* Computed column highlighting - adds subtle accent border */
.graded-test-table td.computed {
    border-left: 2px solid var(--accent-color);
}

/* Tooltip for full text on hover */
[title] { cursor: help; }

/* Substrate view tabs */
.substrate-view { display: none; }
.substrate-view.active { display: block; }

/* Dynamic substrate content from embedded report */
.substrate-dynamic-view {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    padding: 1rem;
}
.substrate-dynamic-view pre {
    background: var(--code-bg);
    padding: 0.75rem;
    border-radius: var(--radius);
    overflow-x: auto;
    font-size: 0.8rem;
}
.substrate-dynamic-view code {
    font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace;
    font-size: 0.8rem;
}
.substrate-dynamic-view table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}
.substrate-dynamic-view th, .substrate-dynamic-view td {
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    text-align: left;
}
.substrate-dynamic-view th {
    background: var(--bg-secondary);
    font-weight: 600;
}
#substrate-dynamic-tabs {
    display: contents;
}

/* Postgres report section */
.postgres-report {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    padding: 1.5rem;
}
.postgres-report h4 {
    font-size: 1.1rem;
    margin-bottom: 0.75rem;
    color: var(--answer-key-color);
}
.postgres-intro {
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 1.25rem;
    color: var(--text-primary);
}
.postgres-details h5 {
    font-size: 0.9rem;
    margin: 1rem 0 0.5rem 0;
    color: var(--text-primary);
}
.postgres-details ul, .postgres-details ol {
    margin: 0.5rem 0 1rem 1.5rem;
    font-size: 0.85rem;
    line-height: 1.6;
}
.postgres-details li { margin-bottom: 0.4rem; }
.postgres-details p { font-size: 0.85rem; line-height: 1.6; margin-bottom: 0.75rem; }
.postgres-conclusion {
    background: rgba(111, 66, 193, 0.1);
    border-left: 3px solid var(--answer-key-color);
    padding: 0.75rem 1rem;
    border-radius: 0 var(--radius) var(--radius) 0;
    margin-top: 1rem;
}

/* Schema entity sections */
.schema-entity-section {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius);
    margin-bottom: 1rem;
    overflow: hidden;
}
.schema-entity-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1rem;
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border-color);
}
.schema-entity-name {
    font-size: 1rem;
    font-weight: 600;
    margin: 0;
    color: var(--accent-color);
}
.schema-meta {
    display: flex;
    gap: 1rem;
    font-size: 0.75rem;
}
.schema-meta-item {
    color: var(--text-secondary);
    background: var(--bg-primary);
    padding: 0.2rem 0.5rem;
    border-radius: 3px;
    border: 1px solid var(--border-color);
}
.schema-entity-desc {
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    color: var(--text-secondary);
    font-style: italic;
    border-bottom: 1px solid var(--border-color);
    background: var(--bg-secondary);
}

@media print {
    header, .tabs, footer { display: none; }
    .tab-content { display: block !important; }
    body { background: white; color: black; }
}
'''


def get_javascript() -> str:
    """Return embedded JavaScript - Desktop optimized with entity tabs"""
    return '''
// Substrate report URL - hardcoded for htmlpreview.github.io
function getSubstrateReportUrl(substrateName) {
    const localPath = `../execution-substrates/${substrateName}/substrate-report.html`;
    const onlinePath = `https://htmlpreview.github.io?https://github.com/eejai42/is-everything-really-a-language/blob/main/execution-substrates/${substrateName}/substrate-report.html`;

    // Use local path for file:// protocol, online path otherwise
    return window.location.protocol === 'file:' ? localPath : onlinePath;
}

// Runtime bars in health matrix table
function renderRuntimeBars() {
    const table = document.getElementById('health-matrix');
    if (!table || !REPORT_DATA.substrates) return;

    // Calculate max time for scaling (exclude answer-key postgres)
    const times = Object.entries(REPORT_DATA.substrates)
        .filter(([name]) => name !== 'postgres')
        .map(([name, data]) => data.elapsed_seconds || 0);
    const maxTime = Math.max(...times, 1);

    // Add bar cells to each row
    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(row => {
        const substrateCell = row.querySelector('.substrate-name');
        if (!substrateCell) return;

        const substrateName = substrateCell.dataset.substrate;
        const data = REPORT_DATA.substrates[substrateName];
        const time = data ? (data.elapsed_seconds || 0) : 0;
        const pct = (time / maxTime) * 100;
        const barColor = time > 60 ? 'var(--warning-color)' : (time < 1 ? 'var(--success-color)' : 'var(--accent-color)');

        const barCell = document.createElement('td');
        barCell.className = 'runtime-bar-cell';
        barCell.innerHTML = `
            <div style="height: 14px; background: var(--bg-tertiary); border-radius: 3px; overflow: hidden;">
                <div style="width: ${Math.max(pct, 0.5)}%; height: 100%; background: ${barColor}; border-radius: 3px;"></div>
            </div>
        `;
        row.appendChild(barCell);
    });
}

renderRuntimeBars();

// Theme toggle
const themeToggle = document.getElementById('theme-toggle');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

if (localStorage.getItem('theme') === 'dark' || (!localStorage.getItem('theme') && prefersDark)) {
    document.documentElement.setAttribute('data-theme', 'dark');
}

themeToggle.addEventListener('click', () => {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    document.documentElement.setAttribute('data-theme', isDark ? 'light' : 'dark');
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
});

// URL-BASED ROUTING
// Hash format: tab/substrate/viewTab/entity
function parseUrlHash() {
    const hash = window.location.hash.slice(1);
    if (!hash) return { tab: 'overview', item: null, viewTab: null, entity: null };
    const parts = hash.split('/');
    return {
        tab: parts[0] || 'overview',
        item: parts[1] ? decodeURIComponent(parts[1]) : null,
        viewTab: parts[2] ? decodeURIComponent(parts[2]) : null,
        entity: parts[3] ? decodeURIComponent(parts[3]) : null
    };
}

function updateUrlHash(tab, item = null, viewTab = null, entity = null) {
    let hash = tab;
    if (item) hash += '/' + encodeURIComponent(item);
    if (viewTab) hash += '/' + encodeURIComponent(viewTab);
    if (entity) hash += '/' + encodeURIComponent(entity);
    history.replaceState(null, '', `#${hash}`);
}

// Track current substrate state for URL updates
let currentSubstrateName = null;
let currentViewTab = 'data';
let currentEntityInView = null;

window.addEventListener('hashchange', () => {
    const state = parseUrlHash();
    navigateToState(state, false);
});

function navigateToState(state, updateUrl = true) {
    const { tab, item, viewTab, entity } = state;
    mainTabs.forEach(t => t.classList.remove('active'));
    tabContents.forEach(c => c.classList.remove('active'));

    const targetTab = document.querySelector(`#main-tabs .tab[data-tab="${tab}"]`);
    if (targetTab) targetTab.classList.add('active');
    document.getElementById(tab)?.classList.add('active');

    if (tab === 'entities' && item) selectEntityTabNoUrl(item);
    else if (tab === 'substrates' && item) {
        selectSubstrateTabNoUrl(item, viewTab, entity);
    }
    else if (tab === 'entities') {
        const entities = Object.keys(REPORT_DATA.entities).sort();
        if (entities.length > 0) selectEntityTabNoUrl(entities[0]);
    } else if (tab === 'substrates') {
        const substrates = Object.keys(REPORT_DATA.substrates).sort();
        if (substrates.length > 0) selectSubstrateTabNoUrl(substrates[0], viewTab, entity);
    }

    if (updateUrl) updateUrlHash(tab, item, viewTab, entity);
}

const mainTabs = document.querySelectorAll('#main-tabs .tab');
const tabContents = document.querySelectorAll('.tab-content');

mainTabs.forEach(tab => {
    tab.addEventListener('click', () => {
        const tabId = tab.dataset.tab;
        mainTabs.forEach(t => t.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tabId)?.classList.add('active');

        if (tabId === 'entities') {
            const entities = Object.keys(REPORT_DATA.entities).sort();
            if (entities.length > 0) selectEntityTab(entities[0]);
            updateUrlHash(tabId);
        } else if (tabId === 'substrates') {
            // Remember last substrate and view tab when returning to this tab
            const substrates = Object.keys(REPORT_DATA.substrates).sort();
            const substrateToShow = currentSubstrateName && substrates.includes(currentSubstrateName)
                ? currentSubstrateName
                : substrates[0];
            if (substrateToShow) {
                selectSubstrateTabNoUrl(substrateToShow, currentViewTab, currentEntityInView);
                updateUrlHash('substrates', substrateToShow, currentViewTab, currentEntityInView);
            }
        } else {
            updateUrlHash(tabId);
        }
    });
});

// Entity sub-tabs
const entityTabs = document.querySelectorAll('#entity-tabs .sub-tab');
const entityDetails = document.getElementById('entity-details');

function selectEntityTabNoUrl(entityName) {
    entityTabs.forEach(t => t.classList.remove('active'));
    const targetTab = document.querySelector(`#entity-tabs .sub-tab[data-entity="${entityName}"]`);
    if (targetTab) targetTab.classList.add('active');
    renderEntityDetails(entityName);
}

function selectEntityTab(entityName) {
    selectEntityTabNoUrl(entityName);
    updateUrlHash('entities', entityName);
}

function renderEntityDetails(entityName) {
    const entity = REPORT_DATA.entities[entityName];
    if (!entity) { entityDetails.innerHTML = '<p>Entity not found</p>'; return; }

    const computedCount = entity.computed_columns ? entity.computed_columns.length : 0;
    const rawCount = entity.schema.length - computedCount;

    let html = '<div class="schema-entity-section">';
    html += `<div class="schema-entity-header">`;
    html += `<h4 class="schema-entity-name">${escapeHtml(entityName)}</h4>`;
    html += `<div class="schema-meta">`;
    html += `<span class="schema-meta-item">${entity.schema.length} fields</span>`;
    html += `<span class="schema-meta-item">${computedCount} computed</span>`;
    html += `<span class="schema-meta-item">${rawCount} raw</span>`;
    html += `<span class="schema-meta-item">${entity.answer_key ? entity.answer_key.length : 0} records</span>`;
    html += `</div>`;
    html += `</div>`;
    if (entity.description) {
        html += `<p class="schema-entity-desc">${escapeHtml(entity.description)}</p>`;
    }

    // Schema table - no collapsible
    html += '<div class="table-scroll"><table class="schema-table"><thead><tr>';
    html += '<th>Field</th><th>Type</th><th>Formula</th><th>Description</th>';
    html += '</tr></thead><tbody>';
    entity.schema.forEach(field => {
        const typeClass = field.type === 'calculated' ? 'type-calculated' : 'type-raw';
        const formula = field.formula || '';
        const desc = field.Description || field.description || '';
        html += `<tr>
            <td>${escapeHtml(field.name)}</td>
            <td class="${typeClass}">${escapeHtml(field.type || 'raw')}</td>
            <td class="formula-cell"><pre class="formula-pre">${escapeHtml(formula)}</pre></td>
            <td class="desc-cell"><span class="desc-text">${escapeHtml(desc)}</span></td>
        </tr>`;
    });
    html += '</tbody></table></div></div>';

    // Answer key in collapsible
    html += '<details><summary>Answer Key Data (' + (entity.answer_key?.length || 0) + ' records)</summary>';
    if (entity.answer_key && entity.answer_key.length > 0) {
        const computedCols = entity.computed_columns || [];
        const cols = Object.keys(entity.answer_key[0]);
        html += '<div class="table-scroll"><table class="data-table"><thead><tr>';
        cols.forEach(col => {
            const isComputed = computedCols.includes(col);
            html += `<th class="${isComputed ? 'computed' : ''}">${escapeHtml(col)}</th>`;
        });
        html += '</tr></thead><tbody>';
        entity.answer_key.forEach(row => {
            html += '<tr>';
            cols.forEach(col => {
                const isComputed = computedCols.includes(col);
                const val = row[col] !== null ? String(row[col]) : 'null';
                html += `<td class="${isComputed ? 'computed' : ''}" title="${escapeHtml(val)}">${escapeHtml(val)}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody></table></div>';
    } else { html += '<p>No data</p>'; }
    html += '</details>';

    // Substrate results tabs
    html += '<h4>Substrate Results</h4>';
    html += '<nav class="sub-tabs" id="entity-substrate-tabs">';
    Object.keys(REPORT_DATA.substrates).sort().forEach((substrate, i) => {
        const grades = REPORT_DATA.substrates[substrate];
        const entityGrades = grades.entities ? grades.entities[entityName] : null;
        if (entityGrades) {
            const passed = entityGrades.fields_passed;
            const total = entityGrades.fields_tested;
            const score = total > 0 ? (passed / total * 100).toFixed(0) : 0;
            const scoreClass = getScoreClass(score);
            const active = i === 0 ? 'active' : '';
            html += `<button class="sub-tab ${active} score-${scoreClass}" data-substrate="${escapeHtml(substrate)}" data-entity="${escapeHtml(entityName)}">${escapeHtml(substrate)}: ${score}%</button>`;
        }
    });
    html += '</nav><div id="entity-substrate-details"></div>';

    entityDetails.innerHTML = html;

    document.querySelectorAll('#entity-substrate-tabs .sub-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('#entity-substrate-tabs .sub-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            renderEntitySubstrateDetails(tab.dataset.entity, tab.dataset.substrate);
        });
    });

    const firstSubstrateTab = document.querySelector('#entity-substrate-tabs .sub-tab');
    if (firstSubstrateTab) renderEntitySubstrateDetails(entityName, firstSubstrateTab.dataset.substrate);
}

function renderEntitySubstrateDetails(entityName, substrateName) {
    const container = document.getElementById('entity-substrate-details');
    if (!container) return;

    const substrate = REPORT_DATA.substrates[substrateName];
    const entity = REPORT_DATA.entities[entityName];
    const entityGrades = substrate?.entities?.[entityName];

    if (!entityGrades) { container.innerHTML = '<p class="no-results">No results.</p>'; return; }

    const computedCols = entity.computed_columns || [];
    const answerKey = entity.answer_key || [];
    const pk = entity.primary_key;

    const failureLookup = {};
    if (entityGrades.failures) {
        entityGrades.failures.forEach(f => { failureLookup[`${f.pk}|${f.field}`] = f; });
    }

    // Get all columns from the schema to preserve proper order (not from answer_key which may be unordered)
    const schemaFields = entity.schema ? entity.schema.map(f => f.name.replace(/([A-Z])/g, (m, c, i) => i > 0 ? '_' + c.toLowerCase() : c.toLowerCase())) : [];
    const allCols = schemaFields.length > 0 ? schemaFields : (answerKey.length > 0 ? Object.keys(answerKey[0]) : []);

    let html = '<div class="table-scroll"><table class="graded-test-table"><thead><tr>';
    allCols.forEach(col => {
        const isComputed = computedCols.includes(col);
        html += `<th class="${isComputed ? 'computed-col-header' : ''}">${escapeHtml(col)}</th>`;
    });
    html += '</tr></thead><tbody>';

    answerKey.forEach(record => {
        const pkVal = record[pk];
        html += '<tr>';
        allCols.forEach(col => {
            const isComputed = computedCols.includes(col);
            const val = record[col];
            const failKey = `${pkVal}|${col}`;
            const failure = failureLookup[failKey];

            if (isComputed && failure) {
                html += `<td class="cell-failed computed" title="Expected: ${escapeHtml(String(failure.expected))}&#10;Actual: ${escapeHtml(String(failure.actual))}">
                    <span class="expected-actual"><span class="expected-label">E:</span><code class="expected">${escapeHtml(String(failure.expected))}</code></span>
                    <span class="expected-actual"><span class="actual-label">A:</span><code class="actual">${escapeHtml(String(failure.actual))}</code></span>
                </td>`;
            } else if (isComputed) {
                const valStr = val !== null ? String(val) : 'null';
                html += `<td class="cell-passed computed" title="${escapeHtml(valStr)}"><span class="check-mark">&#10003;</span><code>${escapeHtml(valStr)}</code></td>`;
            } else {
                // Raw fact - just display the value without pass/fail styling
                const valStr = val !== null ? String(val) : 'null';
                html += `<td class="cell-raw" title="${escapeHtml(valStr)}">${escapeHtml(valStr)}</td>`;
            }
        });
        html += '</tr>';
    });
    html += '</tbody></table></div>';
    container.innerHTML = html;
}

if (entityTabs.length > 0 && REPORT_DATA.entities) {
    entityTabs.forEach(tab => {
        tab.addEventListener('click', () => selectEntityTab(tab.dataset.entity));
    });
}

// Substrate sub-tabs
const substrateTabs = document.querySelectorAll('#substrate-tabs .sub-tab');
const substrateDetails = document.getElementById('substrate-details');

// Shared tabs that exist on all substrates - preserve these when switching
const SHARED_VIEW_TABS = ['data', 'schema', 'dynamic-description', 'dynamic-log', 'dynamic-results'];

function isSharedViewTab(viewTab) {
    return SHARED_VIEW_TABS.includes(viewTab);
}

function selectSubstrateTabNoUrl(substrateName, viewTab = null, entity = null) {
    substrateTabs.forEach(t => t.classList.remove('active'));
    const targetTab = document.querySelector(`#substrate-tabs .sub-tab[data-substrate="${substrateName}"]`);
    if (targetTab) targetTab.classList.add('active');
    currentSubstrateName = substrateName;
    // If no viewTab specified, keep current if it's shared, otherwise default to 'data'
    if (viewTab) {
        currentViewTab = viewTab;
    } else if (!isSharedViewTab(currentViewTab)) {
        currentViewTab = 'data';
    }
    // Keep currentViewTab as-is if it's a shared tab
    currentEntityInView = entity !== null ? entity : currentEntityInView;
    renderSubstrateDetails(substrateName, currentViewTab, currentEntityInView);
}

function selectSubstrateTab(substrateName) {
    // Preserve shared view tab when switching substrates
    const viewTabToUse = isSharedViewTab(currentViewTab) ? currentViewTab : 'data';
    selectSubstrateTabNoUrl(substrateName, viewTabToUse, currentEntityInView);
    updateUrlHash('substrates', substrateName, currentViewTab, currentEntityInView);
}

function updateSubstrateUrl() {
    if (currentSubstrateName) {
        updateUrlHash('substrates', currentSubstrateName, currentViewTab, currentEntityInView);
    }
}

function getScoreClass(score) {
    if (score >= 100) return 'perfect';
    if (score >= 80) return 'good';
    if (score >= 60) return 'warning';
    return 'danger';
}

function renderSubstrateDetails(substrateName, restoreViewTab = null, restoreEntity = null) {
    const substrate = REPORT_DATA.substrates[substrateName];
    if (!substrate) { substrateDetails.innerHTML = '<p>Substrate not found</p>'; return; }

    const total = substrate.total_fields_tested;
    const passed = substrate.fields_passed;
    const failed = substrate.fields_failed;
    const score = total > 0 ? (passed / total * 100).toFixed(1) : 0;
    const elapsed = substrate.elapsed_seconds || 0;
    const isAnswerKey = substrate.is_answer_key;

    let statusText = isAnswerKey ? 'ANSWER KEY' : (failed === 0 ? 'PASS' : 'FAIL');
    let statusClass = isAnswerKey ? 'score-perfect' : (failed === 0 ? 'score-good' : 'score-danger');

    let html = '<div class="substrate-info">';
    html += `<h3>${escapeHtml(substrateName)}</h3>`;
    html += '<div class="substrate-stats">';
    html += `<div class="substrate-stat"><span class="substrate-stat-label">Status:</span><span class="substrate-stat-value ${statusClass}">${statusText}</span></div>`;
    html += `<div class="substrate-stat"><span class="substrate-stat-label">Score:</span><span class="substrate-stat-value">${score}%</span></div>`;
    html += `<div class="substrate-stat"><span class="substrate-stat-label">Runtime:</span><span class="substrate-stat-value">${elapsed.toFixed(2)}s</span></div>`;
    html += '</div></div>';

    // Warning banner
    const runMeta = substrate.run_metadata || {};
    const lastRun = runMeta.last_run || {};
    const lastSuccess = runMeta.last_successful_run || {};
    if (lastRun.status === 'failure' && lastSuccess) {
        const errorMsg = lastRun.error_message || 'Unknown error';
        html += `<div class="warning-banner"><strong>⚠ Last run failed:</strong> <code>${escapeHtml(errorMsg)}</code></div>`;
    }

    if (substrate.error) {
        html += `<div class="failure-card"><code class="actual">${escapeHtml(substrate.error)}</code></div>`;
    }

    // Unified tabs: Data, Schema, then substrate-specific tabs (loaded dynamically)
    html += '<nav class="sub-tabs" id="substrate-view-tabs">';
    html += `<button class="sub-tab active" data-view="data">Data</button>`;
    html += `<button class="sub-tab" data-view="schema">Schema</button>`;
    if (isAnswerKey) {
        html += `<button class="sub-tab" data-view="about">About</button>`;
    }
    // Substrate-specific tabs will be added dynamically after fetch
    html += '<span id="substrate-dynamic-tabs"></span>';
    html += '</nav>';

    // Tab content containers
    html += '<div id="substrate-view-content">';

    // Data tab - graded test results (now first/active)
    html += '<div id="substrate-data-view" class="substrate-view active">';

    // Get entities with results from current ontology
    const entitiesWithResults = Object.keys(REPORT_DATA.entities).sort().filter(entityName => {
        const entity = REPORT_DATA.entities[entityName];
        const computedCols = entity.computed_columns || [];
        const answerKey = entity.answer_key || [];
        return computedCols.length > 0 && answerKey.length > 0;
    });

    // Get stale entities: in substrate's test_answers but NOT in current ontology
    const testAnswers = substrate.test_answers || {};
    const staleEntities = Object.keys(testAnswers).sort().filter(entityName => {
        return !REPORT_DATA.entities[entityName];
    });

    const hasCurrentResults = entitiesWithResults.length > 0;
    const hasStaleResults = staleEntities.length > 0;

    if (!hasCurrentResults && !hasStaleResults) {
        html += '<p class="no-results">No test results available.</p>';
    } else {
        // Entity tabs within substrate view
        html += '<h4>Graded Test Results</h4>';
        html += '<nav class="sub-tabs" id="substrate-entity-tabs">';

        // Current ontology entities (with grading)
        entitiesWithResults.forEach((entityName, i) => {
            const entity = REPORT_DATA.entities[entityName];
            const entityGrades = substrate.entities ? substrate.entities[entityName] : null;
            const eTotal = entityGrades ? entityGrades.fields_tested : 0;
            const ePassed = entityGrades ? entityGrades.fields_passed : 0;
            const eScore = eTotal > 0 ? (ePassed / eTotal * 100).toFixed(0) : 0;
            const eClass = getScoreClass(eScore);
            const active = i === 0 ? 'active' : '';
            html += `<button class="sub-tab ${active} score-${eClass}" data-entity="${escapeHtml(entityName)}">${escapeHtml(entityName)} (${ePassed}/${eTotal})</button>`;
        });

        // Stale entities (from previous ontology - no grading possible)
        staleEntities.forEach((entityName, i) => {
            const active = (!hasCurrentResults && i === 0) ? 'active' : '';
            html += `<button class="sub-tab ${active} stale-entity" data-entity="${escapeHtml(entityName)}" data-stale="true">${escapeHtml(entityName)} (stale)</button>`;
        });

        html += '</nav>';
        html += '<div id="substrate-entity-content"></div>';
    }
    html += '</div>';

    // Schema tab
    html += '<div id="substrate-schema-view" class="substrate-view">';
    Object.keys(REPORT_DATA.entities).sort().forEach(entityName => {
        const entity = REPORT_DATA.entities[entityName];
        const computedCount = entity.computed_columns ? entity.computed_columns.length : 0;
        const rawCount = entity.schema.length - computedCount;
        html += '<div class="schema-entity-section">';
        html += `<div class="schema-entity-header">`;
        html += `<h4 class="schema-entity-name">${escapeHtml(entityName)}</h4>`;
        html += `<div class="schema-meta">`;
        html += `<span class="schema-meta-item">${entity.schema.length} fields</span>`;
        html += `<span class="schema-meta-item">${computedCount} computed</span>`;
        html += `<span class="schema-meta-item">${rawCount} raw</span>`;
        html += `<span class="schema-meta-item">${entity.answer_key ? entity.answer_key.length : 0} records</span>`;
        html += `</div>`;
        html += `</div>`;
        if (entity.description) {
            html += `<p class="schema-entity-desc">${escapeHtml(entity.description)}</p>`;
        }
        html += '<div class="table-scroll"><table class="schema-table"><thead><tr>';
        html += '<th>Field</th><th>Type</th><th>Formula</th><th>Description</th>';
        html += '</tr></thead><tbody>';
        entity.schema.forEach(field => {
            const typeClass = field.type === 'calculated' ? 'type-calculated' : 'type-raw';
            const formula = field.formula || '';
            const desc = field.Description || field.description || '';
            html += `<tr>
                <td>${escapeHtml(field.name)}</td>
                <td class="${typeClass}">${escapeHtml(field.type || 'raw')}</td>
                <td class="formula-cell"><pre class="formula-pre">${escapeHtml(formula)}</pre></td>
                <td class="desc-cell"><span class="desc-text">${escapeHtml(desc)}</span></td>
            </tr>`;
        });
        html += '</tbody></table></div>';
        html += '</div>';
    });
    html += '</div>';

    // About tab for postgres (answer key)
    if (isAnswerKey) {
        html += '<div id="substrate-about-view" class="substrate-view">';
        html += '<div class="postgres-report">';
        html += '<h4>PostgreSQL Reference Implementation</h4>';
        html += '<p class="postgres-intro">PostgreSQL serves as the <strong>reference implementation</strong> for this rulebook. It is not privileged or special—it is simply the most reliable and consistent answer key generator due to its mature SQL engine and deterministic calculation behavior.</p>';
        html += '<div class="postgres-details">';
        html += '<h5>Why PostgreSQL?</h5>';
        html += '<ul>';
        html += '<li><strong>Deterministic calculations</strong> — SQL functions produce consistent, reproducible results</li>';
        html += '<li><strong>Mature type system</strong> — Handles numeric precision, dates, and text reliably</li>';
        html += '<li><strong>Declarative formulas</strong> — The rulebook formulas map directly to SQL expressions</li>';
        html += '<li><strong>Battle-tested</strong> — Decades of production use ensures edge cases are handled correctly</li>';
        html += '</ul>';
        html += '<h5>The Point</h5>';
        html += '<p>All substrates should converge on the same answers. PostgreSQL generates the "answer key" not because it is authoritative, but because it is the most <em>reliable</em> substrate for computing correct values. When other substrates match PostgreSQL, it validates that:</p>';
        html += '<ol>';
        html += '<li>The rulebook formulas are unambiguous across execution environments</li>';
        html += '<li>Each substrate correctly interprets and executes the business logic</li>';
        html += '<li>The same inputs produce the same outputs—regardless of implementation language</li>';
        html += '</ol>';
        html += '<p class="postgres-conclusion"><strong>Everything ends up agreeing—that is the point.</strong> The orchestration tests prove that diverse implementations (JavaScript, Python, Go, spreadsheets, etc.) all compute identical results from the same rulebook specification.</p>';
        html += '</div>';
        html += '</div>';
        html += '</div>';
    }

    // Container for dynamically loaded substrate-specific tabs
    html += '<div id="substrate-dynamic-content"></div>';

    html += '</div>'; // end substrate-view-content

    substrateDetails.innerHTML = html;

    // Load substrate-specific tabs for non-answer-key substrates
    if (!isAnswerKey) {
        loadSubstrateTabs(substrateName);
    }

    // Attach handlers to view tabs with URL tracking
    attachViewTabHandlers();

    // Attach handlers to entity tabs with URL tracking
    document.querySelectorAll('#substrate-entity-tabs .sub-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('#substrate-entity-tabs .sub-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            currentEntityInView = tab.dataset.entity;
            renderSubstrateEntityContent(substrateName, tab.dataset.entity);
            updateSubstrateUrl();
        });
    });

    // Restore view tab from URL if provided, or fall back to 'data'
    if (restoreViewTab) {
        const viewTabBtn = document.querySelector(`#substrate-view-tabs .sub-tab[data-view="${restoreViewTab}"]`);
        if (viewTabBtn) {
            document.querySelectorAll('#substrate-view-tabs .sub-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.substrate-view').forEach(v => v.classList.remove('active'));
            viewTabBtn.classList.add('active');
            document.getElementById(`substrate-${restoreViewTab}-view`)?.classList.add('active');
            currentViewTab = restoreViewTab;
        } else {
            // Tab doesn't exist on this substrate, fall back to 'data'
            currentViewTab = 'data';
            // Data tab is already active by default from the HTML
        }
    }

    // Determine which entity to show
    let entityToShow = null;
    if (restoreEntity && entitiesWithResults.includes(restoreEntity)) {
        entityToShow = restoreEntity;
    } else if (entitiesWithResults.length > 0) {
        entityToShow = entitiesWithResults[0];
    }

    // Restore entity tab from URL or default to first
    if (entityToShow) {
        const entityTabBtn = document.querySelector(`#substrate-entity-tabs .sub-tab[data-entity="${entityToShow}"]`);
        if (entityTabBtn) {
            document.querySelectorAll('#substrate-entity-tabs .sub-tab').forEach(t => t.classList.remove('active'));
            entityTabBtn.classList.add('active');
        }
        currentEntityInView = entityToShow;
        renderSubstrateEntityContent(substrateName, entityToShow);
    }
}

function renderSubstrateEntityContent(substrateName, entityName) {
    const container = document.getElementById('substrate-entity-content');
    if (!container) return;

    const substrate = REPORT_DATA.substrates[substrateName];
    const entity = REPORT_DATA.entities[entityName];

    // Check if this is a stale entity (not in current ontology)
    if (!entity) {
        renderStaleEntityContent(container, substrateName, entityName, substrate);
        return;
    }

    const entityGrades = substrate.entities ? substrate.entities[entityName] : null;
    const answerKey = entity.answer_key || [];
    const computedCols = entity.computed_columns || [];
    const computedColsInfo = entity.computed_columns_info || [];
    const pk = entity.primary_key;

    // Get substrate's actual test answers for this entity
    const substrateTestAnswers = substrate.test_answers ? substrate.test_answers[entityName] : null;
    const hasTestData = substrateTestAnswers && substrateTestAnswers.length > 0;

    // Build lookup of test answers by primary key
    const testAnswerLookup = {};
    if (hasTestData) {
        substrateTestAnswers.forEach(record => {
            const pkVal = record[pk];
            if (pkVal) testAnswerLookup[pkVal] = record;
        });
    }

    const entityDesc = entity.description || '';
    const eTotal = entityGrades ? entityGrades.fields_tested : 0;
    const ePassed = entityGrades ? entityGrades.fields_passed : 0;
    const eScore = eTotal > 0 ? (ePassed / eTotal * 100).toFixed(1) : 0;

    let html = '<div class="entity-test-section">';
    if (entityDesc) html += `<p class="entity-description">${escapeHtml(entityDesc)}</p>`;

    // Show warning if no test data
    if (!hasTestData) {
        html += '<p class="no-test-data-warning" style="color: var(--warning-color); padding: 0.5rem; background: rgba(255,193,7,0.1); border-radius: 4px; margin-bottom: 1rem;">No test answers found for this entity. The substrate has not been run or did not produce output for this entity.</p>';
    }

    // Computed columns in collapsible
    html += '<details><summary>Computed Columns (' + computedCols.length + ')</summary>';
    html += '<div class="computed-cols-info"><ul>';
    computedColsInfo.forEach(col => {
        const formula = col.formula || '';
        const desc = col.description || '';
        html += `<li><span class="field-name">${escapeHtml(col.name)}</span>`;
        if (formula) html += `<span class="formula-row"><span class="formula-label">Formula:</span><span class="formula">${escapeHtml(formula)}</span></span>`;
        if (desc) html += `<span class="desc-row">${escapeHtml(desc)}</span>`;
        html += '</li>';
    });
    html += '</ul></div></details>';

    // Build failure lookup
    const failureLookup = {};
    if (entityGrades && entityGrades.failures) {
        entityGrades.failures.forEach(f => { failureLookup[`${f.pk}|${f.field}`] = f; });
    }

    // Graded test table - show ALL columns with computed ones highlighted
    // Get all columns from the schema to preserve proper order (not from answer_key which may be unordered)
    const schemaFields = entity.schema ? entity.schema.map(f => f.name.replace(/([A-Z])/g, (m, c, i) => i > 0 ? '_' + c.toLowerCase() : c.toLowerCase())) : [];
    const allCols = schemaFields.length > 0 ? schemaFields : (answerKey.length > 0 ? Object.keys(answerKey[0]) : []);

    html += '<div class="table-scroll"><table class="graded-test-table"><thead><tr>';
    allCols.forEach(col => {
        const isComputed = computedCols.includes(col);
        html += `<th class="${isComputed ? 'computed-col-header' : ''}">${escapeHtml(col)}</th>`;
    });
    html += '</tr></thead><tbody>';

    answerKey.forEach(record => {
        const pkVal = record[pk];
        const testRecord = testAnswerLookup[pkVal] || {};
        html += '<tr>';
        allCols.forEach(col => {
            const isComputed = computedCols.includes(col);
            const expectedVal = record[col];
            const actualVal = testRecord[col];
            const failKey = `${pkVal}|${col}`;
            const failure = failureLookup[failKey];

            if (isComputed) {
                if (!hasTestData) {
                    // No test data - show expected value grayed out and crossed out
                    const valStr = expectedVal !== null && expectedVal !== undefined ? String(expectedVal) : 'null';
                    html += `<td class="cell-not-tested computed" title="Not tested - expected: ${escapeHtml(valStr)}" style="color: var(--text-secondary); background: rgba(108,117,125,0.1);"><code style="opacity: 0.5; text-decoration: line-through;">${escapeHtml(valStr)}</code></td>`;
                } else if (failure) {
                    html += `<td class="cell-failed computed" title="Expected: ${escapeHtml(String(failure.expected))}&#10;Actual: ${escapeHtml(String(failure.actual))}">
                        <span class="expected-actual"><span class="expected-label">E:</span><code class="expected">${escapeHtml(String(failure.expected))}</code></span>
                        <span class="expected-actual"><span class="actual-label">A:</span><code class="actual">${escapeHtml(String(failure.actual))}</code></span>
                    </td>`;
                } else {
                    // Passed - show actual value from test answers
                    const valStr = actualVal !== null && actualVal !== undefined ? String(actualVal) : 'null';
                    html += `<td class="cell-passed computed" title="${escapeHtml(valStr)}"><span class="check-mark">&#10003;</span><code>${escapeHtml(valStr)}</code></td>`;
                }
            } else {
                // Raw fact - display from answer key (these aren't tested, just context)
                const valStr = expectedVal !== null && expectedVal !== undefined ? String(expectedVal) : 'null';
                html += `<td class="cell-raw" title="${escapeHtml(valStr)}">${escapeHtml(valStr)}</td>`;
            }
        });
        html += '</tr>';
    });
    html += '</tbody></table></div></div>';
    container.innerHTML = html;
}

// Render stale entity content (entity from previous ontology, not in current rulebook)
function renderStaleEntityContent(container, substrateName, entityName, substrate) {
    const testAnswers = substrate.test_answers ? substrate.test_answers[entityName] : [];

    let html = '<div class="stale-entity-section">';
    html += '<div class="stale-entity-warning">';
    html += '<strong>⚠ Stale Test Data</strong>';
    html += '<p>This entity (<code>' + escapeHtml(entityName) + '</code>) is not part of the current ontology. ';
    html += 'This data is from a previous rulebook and has not been updated.</p>';
    html += '<p class="stale-explanation">This demonstrates a key failure mode of slower substrates (like English/LLM): ';
    html += 'when the ontology changes, substrates that take time to re-run retain stale data from the previous model. ';
    html += 'Unlike instant formal substrates, natural language requires effort to update.</p>';
    html += '</div>';

    if (!testAnswers || testAnswers.length === 0) {
        html += '<p class="no-results">No test answer data found for this entity.</p>';
    } else {
        // Display all data as plain text - no grading possible without schema
        const cols = Object.keys(testAnswers[0]);
        html += '<h5>Raw Test Answers (' + testAnswers.length + ' records)</h5>';
        html += '<div class="table-scroll"><table class="data-table stale-data-table"><thead><tr>';
        cols.forEach(col => {
            html += '<th>' + escapeHtml(col) + '</th>';
        });
        html += '</tr></thead><tbody>';
        testAnswers.forEach(record => {
            html += '<tr>';
            cols.forEach(col => {
                const val = record[col];
                const display = val !== null && val !== undefined ? escapeHtml(String(val)) : '<span class="null-value">null</span>';
                html += '<td>' + display + '</td>';
            });
            html += '</tr>';
        });
        html += '</tbody></table></div>';
    }

    html += '</div>';
    container.innerHTML = html;
}

// Attach view tab handlers (Data, Schema, and dynamically loaded tabs)
function attachViewTabHandlers() {
    document.querySelectorAll('#substrate-view-tabs .sub-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('#substrate-view-tabs .sub-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.substrate-view').forEach(v => v.classList.remove('active'));
            tab.classList.add('active');
            const view = tab.dataset.view;
            document.getElementById(`substrate-${view}-view`)?.classList.add('active');
            currentViewTab = view;
            updateSubstrateUrl();
        });
    });
}

// Load substrate-specific tabs from pre-loaded report_content data
function loadSubstrateTabs(substrateName) {
    const substrate = REPORT_DATA.substrates[substrateName];
    const reportContent = substrate ? substrate.report_content : null;
    const dynamicTabsContainer = document.getElementById('substrate-dynamic-tabs');
    const dynamicContentContainer = document.getElementById('substrate-dynamic-content');

    if (!dynamicTabsContainer || !dynamicContentContainer || !reportContent) return;

    const tabs = reportContent.tabs || [];
    const contents = reportContent.contents || {};

    if (tabs.length === 0) {
        // No substrate-specific tabs available
        return;
    }

    // Build tab buttons for each substrate-specific tab
    let tabButtonsHtml = '';
    tabs.forEach(tab => {
        tabButtonsHtml += `<button class="sub-tab" data-view="dynamic-${tab.id}">${escapeHtml(tab.label)}</button>`;
    });
    dynamicTabsContainer.innerHTML = tabButtonsHtml;

    // Build content containers for each substrate-specific tab
    let contentHtml = '';
    tabs.forEach(tab => {
        const tabContent = contents[tab.id] || '<p>Content not available</p>';
        contentHtml += `<div id="substrate-dynamic-${tab.id}-view" class="substrate-view substrate-dynamic-view">${tabContent}</div>`;
    });
    dynamicContentContainer.innerHTML = contentHtml;

    // Re-attach handlers to include the new tabs
    attachViewTabHandlers();
}

if (substrateTabs.length > 0 && REPORT_DATA.substrates) {
    substrateTabs.forEach(tab => {
        tab.addEventListener('click', () => selectSubstrateTab(tab.dataset.substrate));
    });
}

// Initialize from URL
const initialState = parseUrlHash();
navigateToState(initialState, false);

// Click handlers for navigation
document.querySelectorAll('.substrate-link').forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        navigateToState({ tab: 'substrates', item: link.dataset.substrate });
    });
});

document.querySelectorAll('.entity-link').forEach(header => {
    header.addEventListener('click', () => {
        navigateToState({ tab: 'entities', item: header.dataset.entity });
    });
});

document.querySelectorAll('.substrate-row-link').forEach(cell => {
    cell.addEventListener('click', () => {
        navigateToState({ tab: 'substrates', item: cell.dataset.substrate });
    });
});

document.querySelectorAll('.cell-fail, .cell-pass').forEach(cell => {
    cell.addEventListener('click', () => {
        navigateToState({ tab: 'substrates', item: cell.dataset.substrate });
    });
});

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

console.log('Orchestration Report loaded.');
'''


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Generate HTML orchestration report'
    )
    parser.add_argument(
        '--output', '-o',
        default=DEFAULT_OUTPUT,
        help=f'Output path for HTML report (default: {DEFAULT_OUTPUT})'
    )
    args = parser.parse_args()

    print("=" * 60)
    print("GENERATING ORCHESTRATION REPORT")
    print("=" * 60)
    print()

    # Collect data
    print("Collecting data from all sources...")
    data = collect_all_data()

    print(f"  - Project: {data['meta']['project_name']}")
    print(f"  - Substrates: {data['summary']['total_substrates']}")
    print(f"  - Entities: {data['summary']['total_entities']}")
    print(f"  - Overall score: {data['summary']['overall_score']:.1f}%")
    print()

    # Generate HTML
    print("Generating HTML report...")
    html = generate_html(data)

    # Write output
    output_path = args.output
    with open(output_path, 'w') as f:
        f.write(html)

    print(f"  -> Report written to: {output_path}")
    print()

    # Open in browser (reusing same tab/window when possible)
    abs_path = os.path.abspath(output_path)
    file_url = f"file://{abs_path}"
    import platform
    import subprocess
    if platform.system() == 'Darwin':
        print("Opening report in browser...")
        # Use AppleScript to reuse an existing Chrome tab with this report
        # This prevents opening a new tab every time "View Results" is clicked
        applescript = f'''
        tell application "Google Chrome"
            set found to false
            set targetURL to "{file_url}"

            -- Look for existing tab with this file
            repeat with w in windows
                repeat with t in tabs of w
                    if URL of t starts with "file://" and URL of t contains "substrate-report.html" then
                        set URL of t to targetURL
                        set active tab index of w to (index of t)
                        set index of w to 1
                        activate
                        set found to true
                        exit repeat
                    end if
                end repeat
                if found then exit repeat
            end repeat

            -- No existing tab found, open new one
            if not found then
                if (count of windows) = 0 then
                    make new window
                end if
                tell front window
                    make new tab with properties {{URL:targetURL}}
                end tell
                activate
            end if
        end tell
        '''
        result = subprocess.run(['osascript', '-e', applescript], capture_output=True)
        if result.returncode != 0:
            # Fallback to regular open if Chrome not available
            subprocess.run(['open', abs_path], check=False)
    elif platform.system() == 'Windows':
        print("Opening report in browser...")
        subprocess.run(['start', abs_path], shell=True, check=False)
    elif platform.system() == 'Linux':
        print("Opening report in browser...")
        subprocess.run(['xdg-open', abs_path], check=False)
    else:
        print(f"Open report: file://{abs_path}")

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    main()
