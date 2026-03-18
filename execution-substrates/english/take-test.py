#!/usr/bin/env python3
"""
Take test for the English execution substrate.

This substrate uses an LLM to "execute" English language specifications.
It reads the GENERATED ENGLISH PROSE (glossary.md, specification.md) and asks
the LLM to compute calculated fields based on those human-readable instructions.

This tests whether natural language specifications can be used to correctly
compute derived fields - essentially testing if an LLM can "execute" English
as a programming language.

IMPORTANT: This reads from glossary.md and specification.md, NOT from the raw
rulebook JSON. The whole point is to test whether English prose is sufficient
to serve as an "execution substrate."

DOMAIN-AGNOSTIC: Works with any Airtable schema, not hardcoded to any specific domain.
"""

import argparse
import glob as glob_module
import json
import os
import sys
from pathlib import Path

# Global flag for skipping confirmations (set by --no-confirm)
SKIP_ALL_CONFIRMATIONS = False

# Get script directory
script_dir = Path(__file__).parent.resolve()

# Add project root to path for shared imports
sys.path.insert(0, str(script_dir.parent.parent))

from orchestration.shared import (
    load_rulebook,
    discover_entities,
    get_entity_schema,
    get_calculated_fields,
    get_raw_fields,
    to_snake_case,
    to_pascal_case,
    compute_lookups,
    compute_aggregations
)


# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

DEFAULT_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")
DEFAULT_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")


def call_llm(prompt: str, skip_confirmation: bool = False) -> str:
    """Call the OpenAI API to get computed values.

    ALWAYS asks for user confirmation before making the API call,
    unless skip_confirmation=True or running non-interactively.
    """
    try:
        import openai
    except ImportError:
        print("Error: openai package not installed")
        print("Run: pip install openai")
        sys.exit(1)

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    client = openai.OpenAI()
    model = DEFAULT_MODEL

    # Log prompt info
    prompt_lines = prompt.split('\n')
    print("=" * 60)
    print("PROMPT (first 2 lines):")
    for line in prompt_lines[:2]:
        print(f"  {line[:100]}")
    print(f"  ... ({len(prompt_lines)} total lines, {len(prompt)} chars)")
    print("=" * 60)

    # Skip confirmation if --no-confirm flag was passed, or skip_confirmation=True, or non-interactive
    if not skip_confirmation and not SKIP_ALL_CONFIRMATIONS and sys.stdin.isatty():
        print(f"\n  This will call OpenAI ({model}).")
        try:
            response = input("  Proceed with LLM call? [y/N]: ").strip().lower()
            if response not in ('y', 'yes'):
                print("  Skipping LLM call.")
                return '[]'  # Return empty JSON array
        except (EOFError, KeyboardInterrupt):
            print("\n  Skipping LLM call.")
            return '[]'

    print(f"Calling OpenAI ({model})... please wait...")
    sys.stdout.flush()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=16384,  # Increased from 8096 to handle larger outputs
    )

    response_text = response.choices[0].message.content

    # Log response info
    response_lines = response_text.split('\n')
    print("=" * 60)
    print("RESPONSE (first 2 lines):")
    for line in response_lines[:2]:
        print(f"  {line[:100]}")
    print(f"  ... ({len(response_lines)} total lines, {len(response_text)} chars)")
    print("=" * 60)
    sys.stdout.flush()

    return response_text


# =============================================================================
# ENGLISH DOCUMENT LOADING
# =============================================================================

def load_english_documents() -> tuple:
    """
    Load the generated English prose documents.
    Returns (glossary_content, specification_content).

    The specification.md is required - it contains the LLM-generated English
    specification for computing calculated fields. Glossary is optional.
    """
    glossary_path = script_dir / "glossary.md"
    spec_path = script_dir / "specification.md"

    glossary_content = ""
    spec_content = ""

    # Glossary is optional - specification.md now contains everything
    if glossary_path.exists():
        with open(glossary_path, 'r', encoding='utf-8') as f:
            glossary_content = f.read()
        print(f"  Loaded glossary.md ({len(glossary_content)} chars)")

    # Specification is required
    if spec_path.exists():
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec_content = f.read()
        print(f"  Loaded specification.md ({len(spec_content)} chars)")
    else:
        print(f"  ERROR: specification.md not found at {spec_path}")
        print(f"  Run inject-into-english.py first to generate specification")

    return glossary_content, spec_content


# =============================================================================
# PROMPT BUILDING (Uses English Documents)
# =============================================================================

def build_schema_description(schema: list) -> str:
    """Build a human-readable description of the schema for the LLM.

    NOTE: This is a FALLBACK only used if English documents don't exist.
    The preferred path uses glossary.md and specification.md directly.
    """
    raw_fields = get_raw_fields(schema)
    calc_fields = get_calculated_fields(schema)

    lines = []

    # Raw fields section
    lines.append("## Input Fields (Raw Data)")
    lines.append("")
    for field in raw_fields:
        name = field.get('name', 'Unknown')
        datatype = field.get('datatype', 'string')
        desc = field.get('Description', '')
        snake_name = to_snake_case(name)
        lines.append(f"- **{snake_name}** ({datatype}): {desc if desc else 'Input field'}")
    lines.append("")

    # Calculated fields section
    lines.append("## Calculated Fields (To Be Computed)")
    lines.append("")
    for field in calc_fields:
        name = field.get('name', 'Unknown')
        datatype = field.get('datatype', 'string')
        formula = field.get('formula', '')
        desc = field.get('Description', '')
        snake_name = to_snake_case(name)
        lines.append(f"### {snake_name}")
        lines.append(f"- **Type:** {datatype}")
        lines.append(f"- **Formula:** `{formula}`")
        if desc:
            lines.append(f"- **Description:** {desc}")
        lines.append("")

    return "\n".join(lines)


def build_computed_columns_list(schema: list) -> list:
    """Get list of calculated column names in snake_case."""
    calc_fields = get_calculated_fields(schema)
    return [to_snake_case(f.get('name', '')) for f in calc_fields]


def build_prompt_with_english_docs(glossary: str, specification: str, entity_name: str,
                                    test_data: list, computed_columns: list) -> str:
    """
    Build the prompt using the ENGLISH PROSE documents (specification.md, optionally glossary.md).

    This is the PRIMARY prompt builder - it tests whether the LLM can execute
    English as a programming language by reading human-readable specifications.
    """
    # Build glossary section only if we have one
    glossary_section = ""
    if glossary:
        glossary_section = f"""
# GLOSSARY (Predicate Definitions)

{glossary}

---
"""

    prompt = f"""You are taking a test. Your task is to fill in the computed columns for each record based on the English language specification provided below.

IMPORTANT: You must follow the instructions in the specification document EXACTLY. The specification contains human-readable instructions for how to compute each calculated field.

---
{glossary_section}
# SPECIFICATION (Calculation Instructions)

{specification}

---

# YOUR TASK

Below is a JSON array of "{entity_name}" records. Each record has raw input fields already filled in, but the following computed columns are null and need to be calculated:

{', '.join(computed_columns)}

## Input Data (with null values for computed fields)

```json
{json.dumps(test_data, indent=2)}
```

## Instructions

1. Read the SPECIFICATION above carefully - it tells you exactly how to compute each field
2. For EACH record in the array, compute the null fields following the specification instructions
3. Return ONLY the complete JSON array with all computed fields filled in
4. Use exact field names as shown (snake_case)
5. Boolean values should be true/false (lowercase, no quotes)
6. String values should be in quotes
7. null should remain null (not "null") if the formula cannot be computed
8. Preserve ALL other fields exactly as they appear in the input

Return ONLY valid JSON - no markdown code blocks, no explanations, just the JSON array."""

    return prompt


def build_prompt(schema: list, entity_name: str, test_data: list) -> str:
    """FALLBACK: Build the prompt from raw schema if English docs don't exist."""
    schema_description = build_schema_description(schema)
    calc_fields = get_calculated_fields(schema)
    computed_columns = build_computed_columns_list(schema)

    # Build bullet list of computed columns with their types and formulas
    computed_cols_desc = []
    for field in calc_fields:
        name = to_snake_case(field.get('name', ''))
        datatype = field.get('datatype', 'string')
        formula = field.get('formula', '')
        computed_cols_desc.append(f"- {name} ({datatype}): {formula}")

    prompt = f"""You are taking a test. Your task is to fill in the computed columns for each record in the "{entity_name}" entity based on the schema and formulas provided.

## Schema Definition

{schema_description}

## Your Task

Below is a JSON array of {entity_name} records. Each record has raw input fields already filled in, but the following computed columns are null and need to be calculated:

{chr(10).join(computed_cols_desc)}

## Input Data (with null values for computed fields)

```json
{json.dumps(test_data, indent=2)}
```

## Instructions

1. For EACH record in the array, compute the null fields using the formulas provided above
2. Return ONLY the complete JSON array with all computed fields filled in
3. Use exact field names as shown (snake_case)
4. Boolean values should be true/false (lowercase, no quotes)
5. String values should be in quotes
6. null should remain null (not "null") if the formula cannot be computed
7. Preserve ALL other fields exactly as they appear in the input

Return ONLY valid JSON - no markdown code blocks, no explanations, just the JSON array."""

    return prompt


def extract_json_from_response(response_text: str) -> list:
    """Extract JSON array from LLM response.

    Handles various LLM response formats:
    - Raw JSON array
    - Markdown code blocks (```json ... ```)
    - Truncated responses (attempts partial recovery)
    """
    # Try to parse directly first
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON array in the response
    text = response_text.strip()

    # Remove markdown code blocks if present (strip first to handle trailing newlines)
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    # Strip again before checking end (handles newlines between JSON and closing ```)
    text = text.strip()

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    # Find the array bounds
    start = text.find('[')
    end = text.rfind(']')

    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end+1])
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Attempted to parse: {text[start:start+200]}...")

            # Try to recover partial data from truncated response
            # Find the last complete object by looking for },
            truncated_json = text[start:end+1]
            last_complete = truncated_json.rfind('},')
            if last_complete > 0:
                # Try parsing up to the last complete object
                partial = truncated_json[:last_complete+1] + ']'
                try:
                    records = json.loads(partial)
                    print(f"RECOVERED {len(records)} complete records from truncated response")
                    return records
                except json.JSONDecodeError:
                    pass

    return None


# =============================================================================
# MULTI-ENTITY PROCESSING
# =============================================================================

def process_entity(input_path: str, output_path: str, entity_name: str,
                   schema: list, glossary: str = "", specification: str = "",
                   rulebook: dict = None, project_root = None) -> tuple:
    """
    Process a single entity file using the LLM.

    If glossary and specification are provided (the English documents),
    uses those for the prompt. Otherwise falls back to raw schema.

    Uses batching for large datasets to avoid token limits.

    Returns: (record_count, filled_field_count)
    """
    # Load input data
    with open(input_path, 'r', encoding='utf-8') as f:
        test_data = json.load(f)

    if not test_data:
        # Empty file - just copy it
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        return (0, 0)

    # Always compute lookups/aggregations first
    if rulebook is not None and project_root is not None:
        test_data = compute_lookups(test_data, entity_name, rulebook, project_root)
        test_data = compute_aggregations(test_data, entity_name, rulebook, project_root)

    computed_columns = build_computed_columns_list(schema)

    if not computed_columns:
        # No calculated fields - save with lookups/aggregations computed
        print(f"    No calculated fields for {entity_name}, saved with lookups/aggregations")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        return (len(test_data), 0)

    # Use batching for large datasets to avoid token limits
    BATCH_SIZE = 10  # Process 10 records at a time
    all_filled_answers = []

    if len(test_data) > BATCH_SIZE:
        print(f"    Processing {len(test_data)} records in batches of {BATCH_SIZE}...")

    for batch_start in range(0, len(test_data), BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, len(test_data))
        batch_data = test_data[batch_start:batch_end]

        if len(test_data) > BATCH_SIZE:
            print(f"    Batch {batch_start//BATCH_SIZE + 1}/{(len(test_data) + BATCH_SIZE - 1)//BATCH_SIZE}: records {batch_start+1}-{batch_end}")

        # Build prompt - prefer English documents if available
        if specification:
            doc_desc = "specification" + (" + glossary" if glossary else "")
            if batch_start == 0:  # Only print on first batch
                print(f"    Using English prose documents ({doc_desc})")
            prompt = build_prompt_with_english_docs(glossary, specification, entity_name,
                                                     batch_data, computed_columns)
        else:
            if batch_start == 0:  # Only print on first batch
                print(f"    WARNING: English documents not available, using raw schema fallback")
            prompt = build_prompt(schema, entity_name, batch_data)

        response = call_llm(prompt, skip_confirmation=batch_start > 0)

        # Parse response
        batch_answers = extract_json_from_response(response)

        if batch_answers is None:
            print(f"Error: Could not parse LLM response as JSON for {entity_name} (batch {batch_start//BATCH_SIZE + 1})")
            print("Response was:")
            print(response[:1000])
            # Use original data for this batch (null values remain)
            all_filled_answers.extend(batch_data)
            continue

        if len(batch_answers) != len(batch_data):
            print(f"Warning: LLM returned {len(batch_answers)} records, expected {len(batch_data)}")
            # Pad or truncate as needed
            if len(batch_answers) < len(batch_data):
                batch_answers.extend(batch_data[len(batch_answers):])
            else:
                batch_answers = batch_answers[:len(batch_data)]

        all_filled_answers.extend(batch_answers)

    filled_answers = all_filled_answers

    if len(filled_answers) != len(test_data):
        print(f"Warning: Total results {len(filled_answers)} records, expected {len(test_data)}")

    # Count filled fields
    filled_count = 0
    for record in filled_answers:
        for col in computed_columns:
            if record.get(col) is not None:
                filled_count += 1

    # Write results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filled_answers, f, indent=2)

    return (len(filled_answers), filled_count)


def run_multi_entity():
    """Process all entity files from shared testing/blank-tests/ directory."""
    # Use shared blank-tests directory at project root
    project_root = script_dir.parent.parent
    blank_tests_dir = project_root / "testing" / "blank-tests"
    test_answers_dir = script_dir / "test-answers"

    if not blank_tests_dir.is_dir():
        print(f"Error: {blank_tests_dir} not found")
        sys.exit(1)

    # Ensure output directory exists
    test_answers_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("English Execution Substrate - LLM Test Execution")
    print("Using ENGLISH PROSE documents (glossary.md, specification.md)")
    print("=" * 70)
    print()

    # Load English documents FIRST - this is what makes this the "English" substrate
    print("Loading English specification documents...")
    glossary, specification = load_english_documents()

    if not specification:
        print()
        print("ERROR: specification.md not found!")
        print("The English substrate requires specification.md")
        print("Run: python inject-into-english.py")
        print()
        sys.exit(1)

    print()

    # Load rulebook to get schemas (for field names and types)
    print("Loading rulebook for schema metadata...")
    try:
        rulebook = load_rulebook()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Discover all entities
    entities = discover_entities(rulebook)
    print(f"Discovered {len(entities)} entities: {', '.join(entities)}")

    # Process each entity file (skip metadata files starting with _)
    total_records = 0
    total_filled = 0
    entity_count = 0

    for input_path in sorted(glob_module.glob(str(blank_tests_dir / "*.json"))):
        filename = os.path.basename(input_path)

        # Skip metadata files
        if filename.startswith('_'):
            continue

        entity_snake = filename.replace('.json', '')
        output_path = test_answers_dir / filename

        # Find matching rulebook entity (case-insensitive)
        rulebook_entity = None
        for e in entities:
            if to_snake_case(e) == entity_snake:
                rulebook_entity = e
                break

        if not rulebook_entity:
            print(f"  -> {entity_snake}: No matching entity in rulebook, copying as-is")
            with open(input_path, 'r') as f:
                data = json.load(f)
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
            continue

        # Get schema for this entity
        schema = get_entity_schema(rulebook, rulebook_entity)
        calc_fields = get_calculated_fields(schema)

        print(f"\nProcessing {entity_snake}...")
        print(f"  Schema: {len(schema)} fields, {len(calc_fields)} calculated")

        # Process the entity using English documents
        record_count, filled_count = process_entity(
            input_path, output_path, entity_snake, schema,
            glossary=glossary, specification=specification,
            rulebook=rulebook, project_root=project_root
        )

        total_records += record_count
        total_filled += filled_count
        entity_count += 1

        print(f"  -> {entity_snake}: {record_count} records, {filled_count} computed fields filled")

    print()
    print("=" * 70)
    print(f"English substrate: Processed {entity_count} entities, {total_records} total records")
    print(f"Filled {total_filled} computed fields total")
    print("=" * 70)


def main():
    """Main entry point."""
    global SKIP_ALL_CONFIRMATIONS

    parser = argparse.ArgumentParser(description="Take English substrate test using LLM")
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip all LLM call confirmations (user already confirmed in take-test.sh)"
    )
    args = parser.parse_args()

    if args.no_confirm:
        SKIP_ALL_CONFIRMATIONS = True

    run_multi_entity()


if __name__ == "__main__":
    main()
