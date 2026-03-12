#!/bin/bash
# create-substrate-report.sh - Generate substrate-report.html for English substrate

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

python3 << 'PYTHON_SCRIPT'
import html
import json
import os
import re
from pathlib import Path

SUBSTRATE_NAME = "english"
SUBSTRATE_TITLE = "English (NLG) Execution Substrate"
SUBSTRATE_ICON = "📝"

SCRIPT_DIR = Path(__file__).parent.resolve() if '__file__' in dir() else Path.cwd()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
TESTING_DIR = PROJECT_ROOT / "testing"
ANSWER_KEYS_DIR = TESTING_DIR / "answer-keys"
TEST_ANSWERS_DIR = SCRIPT_DIR / "test-answers"
METADATA_PATH = TESTING_DIR / "_metadata.json"

def read_file(path, default=""):
    try:
        with open(path, 'r') as f:
            return f.read()
    except:
        return default

def extract_log_from_existing_report():
    """Extract the log content from the existing substrate-report.html if it exists."""
    report_path = Path('substrate-report.html')
    if not report_path.exists():
        return None
    try:
        content = report_path.read_text()
        # Find the log content between <pre> tags in the log tab
        # Pattern: <div id="log" class="tab-content">...<pre>LOG_CONTENT</pre>
        import re
        match = re.search(r'<div id="log"[^>]*>.*?<pre>(.*?)</pre>', content, re.DOTALL)
        if match:
            log_html = match.group(1)
            # Unescape HTML entities
            log_text = html.unescape(log_html)
            # Don't return if it's the default "No log available" or similar
            if log_text.strip() and log_text.strip() not in ('No log available', 'No execution log captured for this run', '(No execution log captured for this run)'):
                return log_text
    except:
        pass
    return None

def load_json(path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return None

def markdown_to_html(md):
    """Simple markdown to HTML conversion"""
    lines = md.split('\n')
    html_out = []
    in_list = False
    in_code = False

    for line in lines:
        if line.startswith('```'):
            if in_code:
                html_out.append('</pre>')
                in_code = False
            else:
                html_out.append('<pre>')
                in_code = True
            continue
        if in_code:
            html_out.append(html.escape(line))
            continue
        if line.startswith('### '):
            html_out.append(f'<h4>{html.escape(line[4:])}</h4>')
        elif line.startswith('## '):
            html_out.append(f'<h3>{html.escape(line[3:])}</h3>')
        elif line.startswith('# '):
            html_out.append(f'<h2>{html.escape(line[2:])}</h2>')
        elif line.startswith('- '):
            if not in_list:
                html_out.append('<ul>')
                in_list = True
            html_out.append(f'<li>{html.escape(line[2:])}</li>')
        else:
            if in_list and line.strip() == '':
                html_out.append('</ul>')
                in_list = False
            elif line.strip():
                line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', line)
                html_out.append(f'<p>{line}</p>')
    if in_list:
        html_out.append('</ul>')
    return '\n'.join(html_out)

def generate_graded_data_html():
    """Generate HTML for the graded data tab showing all columns with pass/fail"""
    metadata = load_json(METADATA_PATH)
    if not metadata:
        return '<p class="no-data">No metadata available</p>'

    html_parts = []

    for entity_name, meta in sorted(metadata.items()):
        computed_cols = meta.get('computed_columns', [])
        pk_field = meta.get('primary_key', '')

        # Load answer key and test answers
        answer_key = load_json(ANSWER_KEYS_DIR / f"{entity_name}.json")
        test_answers = load_json(TEST_ANSWERS_DIR / f"{entity_name}.json")

        if not answer_key or not test_answers:
            continue

        # Build lookup for test answers by primary key
        test_lookup = {}
        for record in test_answers:
            pk_val = record.get(pk_field)
            if pk_val:
                test_lookup[pk_val] = record

        # Get all columns from first answer key record
        all_cols = list(answer_key[0].keys()) if answer_key else []

        html_parts.append(f'<div class="entity-section">')
        html_parts.append(f'<h3 class="entity-name">{html.escape(entity_name)}</h3>')
        html_parts.append('<div class="table-scroll"><table class="graded-table"><thead><tr>')

        # Headers
        for col in all_cols:
            is_computed = col in computed_cols
            cls = 'computed-header' if is_computed else ''
            html_parts.append(f'<th class="{cls}">{html.escape(col)}</th>')
        html_parts.append('</tr></thead><tbody>')

        # Rows
        for expected_record in answer_key:
            pk_val = expected_record.get(pk_field)
            actual_record = test_lookup.get(pk_val, {})

            html_parts.append('<tr>')
            for col in all_cols:
                is_computed = col in computed_cols
                expected_val = expected_record.get(col)
                actual_val = actual_record.get(col)

                expected_str = str(expected_val) if expected_val is not None else 'null'
                actual_str = str(actual_val) if actual_val is not None else 'null'

                if is_computed:
                    # Compare expected vs actual
                    if expected_str == actual_str:
                        html_parts.append(f'<td class="cell-passed computed" title="{html.escape(expected_str)}">')
                        html_parts.append(f'<span class="check">✓</span><code>{html.escape(expected_str)}</code></td>')
                    else:
                        html_parts.append(f'<td class="cell-failed computed" title="Expected: {html.escape(expected_str)}&#10;Actual: {html.escape(actual_str)}">')
                        html_parts.append(f'<div class="exp-act"><span class="label">E:</span><code class="expected">{html.escape(expected_str)}</code></div>')
                        html_parts.append(f'<div class="exp-act"><span class="label">A:</span><code class="actual">{html.escape(actual_str)}</code></div></td>')
                else:
                    # Raw fact - just show the value
                    html_parts.append(f'<td class="cell-raw" title="{html.escape(expected_str)}">{html.escape(expected_str)}</td>')
            html_parts.append('</tr>')

        html_parts.append('</tbody></table></div></div>')

    return '\n'.join(html_parts)

# Load content
# Preserve existing log if .last-run.log doesn't exist (tests weren't run this time)
log_file_path = Path('.last-run.log')
if log_file_path.exists():
    log_content = log_file_path.read_text()
else:
    # Try to preserve existing log from current HTML report
    existing_log = extract_log_from_existing_report()
    log_content = existing_log if existing_log else 'No log available'
test_results = read_file('test-results.md', 'No test results available')
specification = read_file('specification.md', '# No specification available')

# Parse scores
score_match = re.search(r'(\d+\.?\d*)%', test_results)
score = score_match.group(0) if score_match else "N/A"
passed_match = re.search(r'\| Passed \| (\d+)', test_results)
passed = passed_match.group(1) if passed_match else "0"
failed_match = re.search(r'\| Failed \| (\d+)', test_results)
failed = failed_match.group(1) if failed_match else "0"
total_match = re.search(r'\| Total Fields Tested \| (\d+)', test_results)
total = total_match.group(1) if total_match else "0"

score_num = float(score.replace('%', '')) if '%' in score else 0
if score_num >= 100: score_class = "score-perfect"
elif score_num >= 80: score_class = "score-good"
elif score_num >= 60: score_class = "score-warning"
else: score_class = "score-danger"

log_escaped = html.escape(log_content)
spec_html = markdown_to_html(specification)
graded_data_html = generate_graded_data_html()

html_template = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Substrate Report: {substrate_name}</title>
    <style>
:root {{
    --bg-primary: #ffffff; --bg-secondary: #f8f9fa; --bg-tertiary: #e9ecef;
    --text-primary: #212529; --text-secondary: #6c757d; --border-color: #dee2e6;
    --accent-color: #0d6efd; --success-color: #198754; --warning-color: #ffc107;
    --danger-color: #dc3545; --code-bg: #f6f8fa; --shadow: 0 2px 8px rgba(0,0,0,0.1); --radius: 6px;
}}
[data-theme="dark"] {{
    --bg-primary: #1a1a2e; --bg-secondary: #16213e; --bg-tertiary: #0f3460;
    --text-primary: #eaeaea; --text-secondary: #b0b0b0; --border-color: #3a3a5c;
    --accent-color: #4dabf7; --success-color: #51cf66; --warning-color: #fcc419;
    --danger-color: #ff6b6b; --code-bg: #0d1117; --shadow: 0 2px 8px rgba(0,0,0,0.3);
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: var(--bg-secondary); color: var(--text-primary); line-height: 1.5; min-height: 100vh; }}
header {{ background: var(--bg-primary); border-bottom: 1px solid var(--border-color); padding: 0.75rem 1rem; display: flex; justify-content: space-between; align-items: center; }}
.header-left {{ display: flex; align-items: center; gap: 0.75rem; }}
.substrate-icon {{ font-size: 1.5rem; }}
h1 {{ font-size: 1.1rem; font-weight: 600; }}
.header-stats {{ display: flex; gap: 1rem; font-size: 0.8rem; }}
.stat {{ display: flex; align-items: center; gap: 0.25rem; }}
.stat-value {{ font-weight: 600; }}
.score-perfect, .score-good {{ color: var(--success-color); }}
.score-warning {{ color: var(--warning-color); }}
.score-danger {{ color: var(--danger-color); }}
#theme-toggle {{ background: var(--bg-tertiary); border: 1px solid var(--border-color); border-radius: 50%; width: 28px; height: 28px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 0.9rem; }}
#theme-toggle:hover {{ background: var(--accent-color); color: white; }}
#theme-toggle .moon {{ display: none; }}
[data-theme="dark"] #theme-toggle .sun {{ display: none; }}
[data-theme="dark"] #theme-toggle .moon {{ display: inline; }}
.tabs {{ display: flex; background: var(--bg-primary); border-bottom: 1px solid var(--border-color); overflow-x: auto; padding: 0 0.5rem; }}
.tab {{ background: none; border: none; padding: 0.5rem 1rem; cursor: pointer; font-size: 0.8rem; color: var(--text-secondary); border-bottom: 2px solid transparent; white-space: nowrap; }}
.tab:hover {{ color: var(--text-primary); }}
.tab.active {{ color: var(--accent-color); border-bottom-color: var(--accent-color); font-weight: 500; }}
main {{ padding: 1rem; }}
.tab-content {{ display: none; }}
.tab-content.active {{ display: block; animation: fadeIn 0.2s ease; }}
@keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}
.card {{ background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 1rem; margin-bottom: 1rem; box-shadow: var(--shadow); }}
.card h2 {{ font-size: 0.9rem; font-weight: 600; margin-bottom: 0.75rem; }}
pre {{ background: var(--code-bg); border: 1px solid var(--border-color); border-radius: var(--radius); padding: 0.75rem; overflow-x: auto; font-family: 'SF Mono', Monaco, monospace; font-size: 0.75rem; line-height: 1.4; max-height: 500px; overflow-y: auto; }}
.markdown-content {{ line-height: 1.7; }}
.markdown-content h2 {{ font-size: 1.1rem; font-weight: 600; margin: 1.5rem 0 0.75rem 0; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; }}
.markdown-content h3 {{ font-size: 1rem; font-weight: 600; margin: 1.25rem 0 0.5rem 0; }}
.markdown-content h4 {{ font-size: 0.9rem; font-weight: 600; margin: 1rem 0 0.5rem 0; color: var(--text-secondary); }}
.markdown-content p {{ margin-bottom: 0.75rem; }}
.markdown-content ul {{ margin-left: 1.5rem; margin-bottom: 0.75rem; }}
.markdown-content li {{ margin-bottom: 0.35rem; }}
.markdown-content pre {{ margin: 0.75rem 0; }}
.markdown-content strong {{ font-weight: 600; }}
.results-summary {{ display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 1rem; }}
.result-item {{ text-align: center; }}
.result-value {{ font-size: 1.5rem; font-weight: 700; }}
.result-label {{ font-size: 0.7rem; color: var(--text-secondary); text-transform: uppercase; }}
.prose-container {{ max-height: 600px; overflow-y: auto; padding-right: 0.5rem; }}

/* Graded data table styles */
.entity-section {{ background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: var(--radius); margin-bottom: 1rem; padding: 1rem; box-shadow: var(--shadow); }}
.entity-name {{ font-size: 1rem; font-weight: 600; color: var(--accent-color); margin-bottom: 0.75rem; }}
.table-scroll {{ overflow-x: auto; }}
.graded-table {{ border-collapse: collapse; font-size: 0.8rem; width: 100%; }}
.graded-table th, .graded-table td {{ padding: 0.35rem 0.5rem; text-align: left; border: 1px solid var(--border-color); max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.graded-table th {{ background: var(--bg-tertiary); font-weight: 600; font-size: 0.75rem; position: sticky; top: 0; }}
.graded-table .computed-header {{ background: rgba(13, 110, 253, 0.15); color: var(--accent-color); }}
.graded-table .cell-raw {{ font-family: monospace; font-size: 0.75rem; color: var(--text-secondary); }}
.graded-table .cell-passed {{ background: rgba(25, 135, 84, 0.08); }}
.graded-table .cell-passed .check {{ color: var(--success-color); font-weight: bold; margin-right: 0.25rem; }}
.graded-table .cell-passed code {{ font-family: monospace; font-size: 0.75rem; }}
.graded-table .cell-failed {{ background: rgba(220, 53, 69, 0.1); }}
.graded-table .cell-failed .exp-act {{ display: block; font-size: 0.7rem; margin-bottom: 0.1rem; }}
.graded-table .cell-failed .label {{ font-weight: 500; color: var(--text-secondary); margin-right: 0.25rem; }}
.graded-table .cell-failed code.expected {{ background: rgba(25, 135, 84, 0.15); color: var(--success-color); padding: 0.1rem 0.25rem; border-radius: 3px; }}
.graded-table .cell-failed code.actual {{ background: rgba(220, 53, 69, 0.15); color: var(--danger-color); padding: 0.1rem 0.25rem; border-radius: 3px; }}
.graded-table td.computed {{ border-left: 2px solid var(--accent-color); }}
.no-data {{ color: var(--text-secondary); padding: 1rem; text-align: center; }}
    </style>
</head>
<body>
    <header>
        <div class="header-left">
            <span class="substrate-icon">{icon}</span>
            <h1>{title}</h1>
        </div>
        <div class="header-stats">
            <div class="stat"><span>Score:</span><span class="stat-value {score_class}">{score}</span></div>
            <div class="stat"><span>{passed}/{total} passed</span></div>
        </div>
        <button id="theme-toggle" title="Toggle theme"><span class="sun">☀️</span><span class="moon">🌙</span></button>
    </header>
    <nav class="tabs">
        <button class="tab active" data-tab="description">Description</button>
        <button class="tab" data-tab="log">Run Log</button>
        <button class="tab" data-tab="results">Test Results</button>
        <button class="tab" data-tab="graded-data">Graded Data</button>
        <button class="tab" data-tab="specification">Specification</button>
    </nav>
    <main>
        <div id="description" class="tab-content active">
            <div class="card">
                <h2>What This Substrate Does</h2>
                <div class="markdown-content">
                    <p>The English substrate tests whether <strong>plain English can serve as an execution substrate</strong>. It uses a two-step LLM flow:</p>
                    <h3>Two-Step LLM Architecture</h3>
                    <ol>
                        <li><strong>Inject</strong>: <code>inject-into-english.py</code> sends the rulebook JSON to an LLM, which writes a plain English specification explaining how to compute each calculated field</li>
                        <li><strong>Take Test</strong>: <code>take-test.py</code> sends the English specification + test data to an LLM, which computes the calculated field values by following the English instructions</li>
                    </ol>
                    <p><strong>Zero formula parsing.</strong> The LLM reads formulas natively and explains them better than regex could.</p>
                </div>
            </div>
            <div class="card">
                <h2>Key Features</h2>
                <ul class="markdown-content">
                    <li><strong>Generic</strong>: Works with ANY rulebook - no domain-specific hardcoding</li>
                    <li><strong>LLM-Driven</strong>: Specification generated by LLM, not template strings</li>
                    <li><strong>Round-Trip Testing</strong>: Verifies the English spec is clear enough to compute correct values</li>
                    <li><strong>Minimal Code</strong>: ~130 lines total, down from ~425 lines</li>
                </ul>
            </div>
        </div>
        <div id="graded-data" class="tab-content">
            <div class="card">
                <h2>Graded Test Data</h2>
                <p style="color: var(--text-secondary); font-size: 0.85rem; margin-bottom: 1rem;">All columns shown. <span style="color: var(--accent-color); font-weight: 500;">Blue headers</span> indicate computed fields being tested. <span style="color: var(--success-color);">✓</span> = passed, <span style="color: var(--danger-color);">E/A</span> = failed (Expected vs Actual).</p>
                {graded_data}
            </div>
        </div>
        <div id="log" class="tab-content">
            <div class="card">
                <h2>Execution Log</h2>
                <pre>{log_content}</pre>
            </div>
        </div>
        <div id="results" class="tab-content">
            <div class="card">
                <h2>Test Summary</h2>
                <div class="results-summary">
                    <div class="result-item"><div class="result-value {score_class}">{score}</div><div class="result-label">Score</div></div>
                    <div class="result-item"><div class="result-value score-perfect">{passed}</div><div class="result-label">Passed</div></div>
                    <div class="result-item"><div class="result-value">{failed}</div><div class="result-label">Failed</div></div>
                    <div class="result-item"><div class="result-value">{total}</div><div class="result-label">Total</div></div>
                </div>
            </div>
        </div>
        <div id="specification" class="tab-content">
            <div class="card">
                <h2>specification.md (LLM-Generated)</h2>
                <div class="prose-container markdown-content">{specification}</div>
            </div>
        </div>
    </main>
    <script>
const themeToggle = document.getElementById('theme-toggle');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
function getInitialTheme() {{ try {{ if (window.parent && window.parent.document.documentElement.dataset.theme) return window.parent.document.documentElement.dataset.theme; }} catch (e) {{}} return prefersDark ? 'dark' : 'light'; }}
document.documentElement.dataset.theme = getInitialTheme();
themeToggle.addEventListener('click', () => {{ document.documentElement.dataset.theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'; }});
window.addEventListener('message', (event) => {{ if (event.data.type === 'theme-change') document.documentElement.dataset.theme = event.data.theme; }});
document.querySelectorAll('.tab').forEach(tab => {{ tab.addEventListener('click', () => {{ document.querySelectorAll('.tab').forEach(t => t.classList.remove('active')); document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active')); tab.classList.add('active'); document.getElementById(tab.dataset.tab).classList.add('active'); }}); }});
    </script>
</body>
</html>'''

output = html_template.format(
    substrate_name=SUBSTRATE_NAME, title=SUBSTRATE_TITLE, icon=SUBSTRATE_ICON,
    score=score, score_class=score_class, passed=passed, failed=failed, total=total,
    log_content=log_escaped,
    specification=spec_html,
    graded_data=graded_data_html
)

with open('substrate-report.html', 'w') as f:
    f.write(output)
print(f"Generated substrate-report.html for {SUBSTRATE_NAME}")
PYTHON_SCRIPT
