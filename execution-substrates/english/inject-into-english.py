#!/usr/bin/env python3
"""
Generate English documentation from ANY Effortless Rulebook.

ARCHITECTURE: Generic Rulebook → English Specification (LLM-Driven)
====================================================================
This substrate reads the effortless-rulebook.json and uses an LLM to generate:
1. specification.md - Plain English explanation of all calculated fields

The core insight: Let the LLM do the work. Instead of writing formula parsers,
just send the rulebook JSON to the LLM and ask it to write the specification.

OFFLINE MODE:
If no OPENAI_API_KEY (or ANTHROPIC_API_KEY) is set, the substrate will:
1. Check for a cached specification in bases/<name>/english-specification.md
2. If found, use it without making any LLM calls
3. If not found, skip with a clear message

This enables Docker/offline operation from a fresh clone.
"""

import sys
import os
import argparse
import json
import shutil
from pathlib import Path

# Add project root to path for shared imports
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from orchestration.shared import load_rulebook, get_candidate_name_from_cwd, handle_clean_arg

# =============================================================================
# OFFLINE CACHE SUPPORT
# =============================================================================

BASES_JSON = PROJECT_ROOT / "orchestration" / "bases.json"
SSOTME_JSON = PROJECT_ROOT / "ssotme.json"

# Colors
YELLOW = '\033[1;33m'
GREEN = '\033[0;32m'
CYAN = '\033[0;36m'
DIM = '\033[2m'
NC = '\033[0m'


def get_current_base_id():
    """Get the current base ID from ssotme.json."""
    if not SSOTME_JSON.exists():
        return None
    try:
        with open(SSOTME_JSON, 'r') as f:
            config = json.load(f)
        for setting in config.get('ProjectSettings', []):
            if setting.get('Name') == 'baseId':
                return setting.get('Value')
    except Exception:
        pass
    return None


def get_base_by_id(base_id: str):
    """Get base config by ID."""
    if not BASES_JSON.exists():
        return None
    try:
        with open(BASES_JSON, 'r') as f:
            bases = json.load(f)
        for base in bases:
            if base.get('id') == base_id:
                return base
    except Exception:
        pass
    return None


def get_cached_specification_path(base_id: str = None) -> Path:
    """Get the path to cached specification in repo cache."""
    if base_id is None:
        base_id = get_current_base_id()
    if not base_id:
        return None

    base = get_base_by_id(base_id)
    if base and base.get('docs'):
        cache_path = PROJECT_ROOT / base['docs'] / "english-specification.md"
        if cache_path.exists():
            return cache_path
    return None


def has_api_key(provider: str = "openai") -> bool:
    """Check if API key is available for the given provider."""
    if provider == "openai":
        return bool(os.environ.get("OPENAI_API_KEY"))
    elif provider == "anthropic":
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
    return False


def restore_from_cache() -> bool:
    """Restore specification from repo cache if available."""
    cache_path = get_cached_specification_path()
    if not cache_path:
        return False

    try:
        target = SCRIPT_DIR / "specification.md"
        shutil.copy2(cache_path, target)
        print(f"  {GREEN}Restored specification from repo cache{NC}")
        print(f"  {DIM}Source: {cache_path.relative_to(PROJECT_ROOT)}{NC}")
        return True
    except Exception as e:
        print(f"  {YELLOW}Warning: Failed to restore from cache: {e}{NC}")
        return False


def save_to_cache() -> bool:
    """Save current specification to repo cache."""
    base_id = get_current_base_id()
    if not base_id:
        return False

    base = get_base_by_id(base_id)
    if not base or not base.get('docs'):
        return False

    source = SCRIPT_DIR / "specification.md"
    if not source.exists():
        return False

    try:
        target = PROJECT_ROOT / base['docs'] / "english-specification.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        print(f"  {GREEN}Saved specification to repo cache{NC}")
        print(f"  {DIM}Target: {target.relative_to(PROJECT_ROOT)}{NC}")
        return True
    except Exception:
        return False

# =============================================================================
# MODEL TIER CONFIGURATION
# =============================================================================

MODEL_TIERS = {
    "smart": {
        "openai": "gpt-4o",
        "anthropic": "claude-sonnet-4-20250514",
        "description": "Most capable models - highest accuracy, slowest, most expensive"
    },
    "medium": {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-haiku-20241022",
        "description": "Balanced models - good accuracy, moderate speed/cost"
    },
    "cheap": {
        "openai": "gpt-3.5-turbo",
        "anthropic": "claude-3-haiku-20240307",
        "description": "Budget models - faster/cheaper but less reliable"
    },
}

DEFAULT_TIER = os.environ.get("LLM_TIER", "medium")
DEFAULT_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")


def get_model_for_tier(tier: str, provider: str) -> str:
    """Get the model name for a given tier and provider."""
    if tier not in MODEL_TIERS:
        print(f"Warning: Unknown tier '{tier}', using 'medium'")
        tier = "medium"
    return MODEL_TIERS[tier].get(provider, MODEL_TIERS[tier]["openai"])


def get_llm_response(prompt: str, provider: str = None, tier: str = None) -> str:
    """Get a response from the LLM."""
    provider = provider or DEFAULT_PROVIDER
    tier = tier or DEFAULT_TIER
    model = get_model_for_tier(tier, provider)

    print(f"  Calling {provider.upper()} ({model})...")
    sys.stdout.flush()

    try:
        if provider == "openai":
            import openai
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temp for more consistent outputs
                max_tokens=4096,
            )
            return response.choices[0].message.content
        elif provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic()
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        else:
            raise ValueError(f"Unknown provider: {provider}")
    except Exception as e:
        print(f"Warning: LLM call failed: {e}")
        return f"[LLM generation failed: {e}]"


# =============================================================================
# LLM-DRIVEN SPECIFICATION GENERATION
# =============================================================================

def generate_specification(rulebook: dict, provider: str = None, tier: str = None) -> str:
    """Use LLM to generate plain English specification from rulebook."""

    provider = provider or DEFAULT_PROVIDER
    tier = tier or DEFAULT_TIER

    rulebook_name = rulebook.get('Name', 'Untitled Rulebook')

    prompt = f"""You are a technical writer creating a specification document.

Given this rulebook JSON, write a clear English specification document that explains
how to compute each calculated field.

RULEBOOK:
```json
{json.dumps(rulebook, indent=2)}
```

Write a specification document in Markdown format that includes:

1. A title and brief overview of what this rulebook does
2. For each entity that has calculated fields:
   - List the input fields (type="raw") with their names, types, and descriptions
   - For each calculated field (type="calculated"):
     - Explain in plain English exactly how to compute it from the inputs
     - Include the formula for reference
     - Provide a concrete example using data from the rulebook if available

The specification should be clear enough that someone could follow it to compute
the correct values without seeing the original formulas.

IMPORTANT: Focus on the actual content of this specific rulebook ("{rulebook_name}").
Do not include generic boilerplate about "language classification" or unrelated domains."""

    print(f"  Generating specification via LLM...")
    return get_llm_response(prompt, provider, tier)


# =============================================================================
# MAIN
# =============================================================================

def main():
    GENERATED_FILES = [
        'test-results.md',
        'specification.md',
    ]

    if '--clean' in sys.argv:
        if handle_clean_arg(GENERATED_FILES, "English substrate: Removes test-results.md and specification.md."):
            return 0

    parser = argparse.ArgumentParser(
        description="Generate English specification from any Effortless Rulebook (LLM-driven)"
    )
    parser.add_argument(
        "--tier", "-t",
        choices=["smart", "medium", "cheap"],
        default=DEFAULT_TIER,
        help=f"Model intelligence tier (default: {DEFAULT_TIER})"
    )
    parser.add_argument(
        "--provider", "-p",
        choices=["openai", "anthropic"],
        default=DEFAULT_PROVIDER,
        help=f"LLM provider (default: {DEFAULT_PROVIDER})"
    )
    parser.add_argument(
        "--regenerate", "-r",
        action="store_true",
        help="Force regeneration of all content without prompting"
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Skip interactive prompts"
    )
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Use cached specification from repo (skip LLM)"
    )
    parser.add_argument(
        "--save-cache",
        action="store_true",
        help="Save generated specification to repo cache after generation"
    )

    args = parser.parse_args()

    candidate_name = get_candidate_name_from_cwd()
    provider = args.provider

    # ==========================================================================
    # OFFLINE MODE: Check for API key, use cache if unavailable
    # ==========================================================================
    api_available = has_api_key(provider)
    cache_path = get_cached_specification_path()

    if args.use_cache:
        # Explicit cache usage requested
        print(f"\n{CYAN}Using cached specification (--use-cache){NC}")
        if restore_from_cache():
            return 0
        else:
            print(f"  {YELLOW}No cached specification available{NC}")
            return 2

    if not api_available and not args.regenerate:
        # No API key - try to use cache
        print(f"\n{YELLOW}No API key found for {provider.upper()}{NC}")

        if cache_path:
            print(f"  Using cached specification from repo...")
            if restore_from_cache():
                return 0

        # No cache available
        print(f"\n  {YELLOW}No cached specification available for this base.{NC}")
        print(f"  {DIM}To generate a specification, set {provider.upper()}_API_KEY environment variable.{NC}")
        print(f"  {DIM}Or run with --use-cache after caching a specification.{NC}")
        return 2

    # ==========================================================================
    # NORMAL MODE: Generate via LLM
    # ==========================================================================

    # Check if specification already exists
    spec_file = Path("specification.md")
    if spec_file.exists() and not args.regenerate:
        print(f"\nExisting specification.md found.")
        if args.no_prompt:
            print("Skipping regeneration (use --regenerate to force).")
            return 2

        if not sys.stdin.isatty():
            print("Non-interactive mode detected. Skipping regeneration (use --regenerate to force).")
            return 2

        print(f"\nRegenerate English specification?")
        try:
            response = input("Regenerate? [y/N]: ").strip().lower()
            if response not in ('y', 'yes'):
                print("Skipping regeneration.")
                return 2
        except (EOFError, KeyboardInterrupt):
            print("\nSkipping regeneration.")
            return 2

    print(f"Generating {candidate_name} substrate...")

    # Load the rulebook
    try:
        rulebook = load_rulebook()
        rulebook_name = rulebook.get('Name', 'Unknown')
        print(f"  Loaded rulebook: {rulebook_name}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    # Generate specification via LLM
    print("\n=== Generating Specification (LLM-driven) ===")
    print(f"  Generating specification via LLM...")

    # ALWAYS ask before making LLM call (unless --no-prompt or non-interactive)
    if not args.no_prompt and sys.stdin.isatty():
        model = get_model_for_tier(args.tier, args.provider)
        print(f"\n  This will call {args.provider.upper()} ({model}) to generate the specification.")
        try:
            response = input("  Proceed with LLM call? [y/N]: ").strip().lower()
            if response not in ('y', 'yes'):
                print("  Skipping LLM call.")
                return 2
        except (EOFError, KeyboardInterrupt):
            print("\n  Skipping LLM call.")
            return 2

    spec_content = generate_specification(rulebook, args.provider, args.tier)
    with open("specification.md", 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("  Created specification.md")

    # AUTO-SAVE to repo cache (self-maintaining system)
    # This ensures the cache stays up-to-date as specs are generated
    print("\n=== Auto-saving to Repo Cache ===")
    if save_to_cache():
        print(f"  {DIM}(Cache will be used for offline/Docker runs){NC}")
    else:
        print(f"  {DIM}(No cache location configured for this base){NC}")

    print(f"\nDone generating {candidate_name} substrate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
