#!/usr/bin/env python3
"""
Cache Manager - Comprehensive caching for ERB offline/Docker operation.

Manages two types of caches:
1. REPO CACHE (checked into git): bases/<name>/
   - effortless-rulebook.json - The rulebook schema + data
   - english-specification.md - Cached LLM output for English substrate

2. USER CACHE (gitignored): effortless-rulebook/.cache/
   - Working cache for live development
   - Gets populated when pulling fresh from Airtable

The repo cache enables "cold start" - clone the repo, run Docker, everything works.
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent

# Paths
BASES_DIR = PROJECT_ROOT / "bases"
BASES_JSON = SCRIPT_DIR / "bases.json"
SSOTME_JSON = PROJECT_ROOT / "ssotme.json"
RULEBOOK_PATH = PROJECT_ROOT / "effortless-rulebook" / "effortless-rulebook.json"
USER_CACHE_DIR = PROJECT_ROOT / "effortless-rulebook" / ".cache"
ENGLISH_SUBSTRATE_DIR = PROJECT_ROOT / "execution-substrates" / "english"

# Colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
BOLD = '\033[1m'
DIM = '\033[2m'
NC = '\033[0m'


def load_bases_config() -> list:
    """Load the bases configuration."""
    if BASES_JSON.exists():
        with open(BASES_JSON, 'r') as f:
            return json.load(f)
    return []


def get_base_by_id(base_id: str) -> Optional[dict]:
    """Get base config by ID."""
    for base in load_bases_config():
        if base.get('id') == base_id:
            return base
    return None


def get_base_dir(base_id: str) -> Optional[Path]:
    """Get the repo cache directory for a base."""
    base = get_base_by_id(base_id)
    if base and base.get('docs'):
        return PROJECT_ROOT / base['docs']
    return None


def get_current_base_id() -> Optional[str]:
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


def get_project_name() -> str:
    """Get the current project name."""
    if not SSOTME_JSON.exists():
        return "Unknown"
    try:
        with open(SSOTME_JSON, 'r') as f:
            config = json.load(f)
        return config.get('Name', 'Unknown')
    except Exception:
        return "Unknown"


# =============================================================================
# REPO CACHE OPERATIONS
# =============================================================================

def get_repo_cache_rulebook(base_id: str) -> Optional[Path]:
    """Get the repo-cached rulebook path for a base."""
    base_dir = get_base_dir(base_id)
    if base_dir:
        rulebook = base_dir / "effortless-rulebook.json"
        if rulebook.exists():
            return rulebook
    return None


def get_repo_cache_english_spec(base_id: str) -> Optional[Path]:
    """Get the repo-cached English specification path for a base."""
    base_dir = get_base_dir(base_id)
    if base_dir:
        spec = base_dir / "english-specification.md"
        if spec.exists():
            return spec
    return None


def restore_rulebook_from_repo_cache(base_id: str = None) -> bool:
    """Restore the active rulebook from repo cache."""
    if base_id is None:
        base_id = get_current_base_id()
    if not base_id:
        return False

    cached = get_repo_cache_rulebook(base_id)
    if not cached:
        print(f"{YELLOW}No repo cache found for base {base_id}{NC}")
        return False

    try:
        # Ensure target directory exists
        RULEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cached, RULEBOOK_PATH)
        print(f"{GREEN}Restored rulebook from repo cache: {cached.relative_to(PROJECT_ROOT)}{NC}")
        return True
    except Exception as e:
        print(f"{RED}Error restoring from repo cache: {e}{NC}")
        return False


def save_rulebook_to_repo_cache(base_id: str = None) -> bool:
    """Save the current rulebook to repo cache (for updating shipped cache)."""
    if base_id is None:
        base_id = get_current_base_id()
    if not base_id:
        print(f"{YELLOW}No base ID found{NC}")
        return False

    base_dir = get_base_dir(base_id)
    if not base_dir:
        print(f"{YELLOW}No repo cache directory configured for base {base_id}{NC}")
        return False

    if not RULEBOOK_PATH.exists():
        print(f"{RED}No active rulebook to cache{NC}")
        return False

    try:
        base_dir.mkdir(parents=True, exist_ok=True)
        target = base_dir / "effortless-rulebook.json"
        shutil.copy2(RULEBOOK_PATH, target)
        print(f"{GREEN}Saved rulebook to repo cache: {target.relative_to(PROJECT_ROOT)}{NC}")
        return True
    except Exception as e:
        print(f"{RED}Error saving to repo cache: {e}{NC}")
        return False


def save_english_spec_to_repo_cache(base_id: str = None) -> bool:
    """Save the current English specification to repo cache."""
    if base_id is None:
        base_id = get_current_base_id()
    if not base_id:
        return False

    base_dir = get_base_dir(base_id)
    if not base_dir:
        return False

    source = ENGLISH_SUBSTRATE_DIR / "specification.md"
    if not source.exists():
        print(f"{YELLOW}No specification.md to cache{NC}")
        return False

    try:
        target = base_dir / "english-specification.md"
        shutil.copy2(source, target)
        print(f"{GREEN}Saved English specification to repo cache: {target.relative_to(PROJECT_ROOT)}{NC}")
        return True
    except Exception as e:
        print(f"{RED}Error saving English spec to repo cache: {e}{NC}")
        return False


def restore_english_spec_from_repo_cache(base_id: str = None) -> bool:
    """Restore English specification from repo cache."""
    if base_id is None:
        base_id = get_current_base_id()
    if not base_id:
        return False

    cached = get_repo_cache_english_spec(base_id)
    if not cached:
        return False

    try:
        target = ENGLISH_SUBSTRATE_DIR / "specification.md"
        ENGLISH_SUBSTRATE_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(cached, target)
        print(f"{GREEN}Restored English specification from repo cache{NC}")
        return True
    except Exception as e:
        print(f"{RED}Error restoring English spec: {e}{NC}")
        return False


# =============================================================================
# CACHE STATUS
# =============================================================================

def get_cache_status(base_id: str = None) -> dict:
    """Get comprehensive cache status for a base."""
    if base_id is None:
        base_id = get_current_base_id()

    base = get_base_by_id(base_id) if base_id else None
    base_dir = get_base_dir(base_id) if base_id else None

    status = {
        'base_id': base_id,
        'base_name': base.get('name') if base else None,
        'base_dir': str(base_dir.relative_to(PROJECT_ROOT)) if base_dir else None,
        'repo_cache': {
            'rulebook': None,
            'english_spec': None,
        },
        'user_cache': {
            'rulebook': None,
        },
        'active': {
            'rulebook': RULEBOOK_PATH.exists(),
            'english_spec': (ENGLISH_SUBSTRATE_DIR / "specification.md").exists(),
        }
    }

    # Check repo cache
    if base_dir:
        rb = base_dir / "effortless-rulebook.json"
        if rb.exists():
            status['repo_cache']['rulebook'] = {
                'path': str(rb.relative_to(PROJECT_ROOT)),
                'size': rb.stat().st_size,
                'modified': datetime.fromtimestamp(rb.stat().st_mtime).isoformat()
            }

        es = base_dir / "english-specification.md"
        if es.exists():
            status['repo_cache']['english_spec'] = {
                'path': str(es.relative_to(PROJECT_ROOT)),
                'size': es.stat().st_size,
                'modified': datetime.fromtimestamp(es.stat().st_mtime).isoformat()
            }

    # Check user cache
    if base_id and USER_CACHE_DIR.exists():
        uc = USER_CACHE_DIR / f"{base_id}.json"
        if uc.exists():
            status['user_cache']['rulebook'] = {
                'path': str(uc.relative_to(PROJECT_ROOT)),
                'size': uc.stat().st_size,
                'modified': datetime.fromtimestamp(uc.stat().st_mtime).isoformat()
            }

    return status


def print_cache_status(base_id: str = None):
    """Print cache status in a readable format."""
    status = get_cache_status(base_id)

    print(f"\n{BOLD}Cache Status{NC}")
    print(f"{'='*60}\n")

    if status['base_id']:
        print(f"  Base ID:   {CYAN}{status['base_id']}{NC}")
        print(f"  Name:      {status['base_name'] or 'Unknown'}")
        print(f"  Directory: {status['base_dir'] or 'Not configured'}")
    else:
        print(f"  {YELLOW}No base selected{NC}")

    print(f"\n{BOLD}Repo Cache{NC} (checked into git)")
    rc = status['repo_cache']
    if rc['rulebook']:
        print(f"  {GREEN}[OK]{NC} Rulebook: {rc['rulebook']['path']}")
    else:
        print(f"  {RED}[--]{NC} Rulebook: not cached")

    if rc['english_spec']:
        print(f"  {GREEN}[OK]{NC} English spec: {rc['english_spec']['path']}")
    else:
        print(f"  {DIM}[--]{NC} English spec: not cached")

    print(f"\n{BOLD}User Cache{NC} (local, gitignored)")
    uc = status['user_cache']
    if uc['rulebook']:
        print(f"  {GREEN}[OK]{NC} Rulebook: {uc['rulebook']['path']}")
    else:
        print(f"  {DIM}[--]{NC} Rulebook: not cached")

    print(f"\n{BOLD}Active Files{NC}")
    active = status['active']
    if active['rulebook']:
        print(f"  {GREEN}[OK]{NC} effortless-rulebook/effortless-rulebook.json")
    else:
        print(f"  {RED}[--]{NC} No active rulebook")

    if active['english_spec']:
        print(f"  {GREEN}[OK]{NC} execution-substrates/english/specification.md")
    else:
        print(f"  {DIM}[--]{NC} No English specification")

    print()


def list_all_bases():
    """List all bases with their cache status."""
    bases = load_bases_config()

    print(f"\n{BOLD}Available Bases{NC}")
    print(f"{'='*70}\n")

    current = get_current_base_id()

    for base in bases:
        base_id = base.get('id')
        name = base.get('name', 'Unknown')
        docs = base.get('docs')

        # Check cache status
        rb_cached = get_repo_cache_rulebook(base_id) is not None
        es_cached = get_repo_cache_english_spec(base_id) is not None

        # Active indicator
        if base_id == current:
            indicator = f"{GREEN}>>>{NC}"
        else:
            indicator = "   "

        # Cache status
        cache_status = []
        if rb_cached:
            cache_status.append(f"{GREEN}rulebook{NC}")
        if es_cached:
            cache_status.append(f"{GREEN}english{NC}")

        cache_str = ", ".join(cache_status) if cache_status else f"{DIM}no cache{NC}"

        print(f"{indicator} {BOLD}{name}{NC}")
        print(f"    ID:    {CYAN}{base_id}{NC}")
        print(f"    Dir:   {docs or 'not configured'}")
        print(f"    Cache: [{cache_str}]")
        print()


# =============================================================================
# DOCKER/OFFLINE MODE
# =============================================================================

def setup_for_offline(base_id: str = None) -> bool:
    """
    Set up the working environment from repo cache for offline/Docker operation.

    This is the key function for cold starts - restores everything needed
    to run substrates without any API keys.
    """
    if base_id is None:
        base_id = get_current_base_id()

    if not base_id:
        print(f"{RED}No base selected. Use --base-id or select a base first.{NC}")
        return False

    print(f"\n{BOLD}{CYAN}Setting up offline environment...{NC}")
    print(f"  Base: {base_id}\n")

    success = True

    # 1. Restore rulebook
    print(f"{BLUE}[1/2]{NC} Restoring rulebook...")
    if not restore_rulebook_from_repo_cache(base_id):
        print(f"  {RED}Failed to restore rulebook{NC}")
        success = False

    # 2. Restore English specification (optional)
    print(f"{BLUE}[2/2]{NC} Restoring English specification...")
    if not restore_english_spec_from_repo_cache(base_id):
        print(f"  {DIM}No cached English specification (will require OPENAI_API_KEY){NC}")

    if success:
        print(f"\n{GREEN}Offline setup complete!{NC}")
    else:
        print(f"\n{YELLOW}Offline setup incomplete - some features may require API keys{NC}")

    return success


def update_repo_cache(base_id: str = None) -> bool:
    """
    Update the repo cache with current working files.

    Call this after a fresh Airtable pull to update the shipped cache.
    """
    if base_id is None:
        base_id = get_current_base_id()

    if not base_id:
        print(f"{RED}No base selected{NC}")
        return False

    print(f"\n{BOLD}{CYAN}Updating repo cache...{NC}")
    print(f"  Base: {base_id}\n")

    # Save rulebook
    print(f"{BLUE}[1/2]{NC} Saving rulebook to repo cache...")
    save_rulebook_to_repo_cache(base_id)

    # Save English spec if it exists
    print(f"{BLUE}[2/2]{NC} Saving English specification to repo cache...")
    save_english_spec_to_repo_cache(base_id)

    print(f"\n{GREEN}Repo cache updated!{NC}")
    print(f"{DIM}Remember to commit these changes to ship the updated cache.{NC}\n")

    return True


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="ERB Cache Manager - Manage repo and user caches for offline operation"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # status command
    status_parser = subparsers.add_parser("status", help="Show cache status")
    status_parser.add_argument("--base-id", help="Base ID to check (default: current)")

    # list command
    subparsers.add_parser("list", help="List all bases and their cache status")

    # setup-offline command
    offline_parser = subparsers.add_parser("setup-offline",
        help="Set up environment from repo cache (for Docker/offline)")
    offline_parser.add_argument("--base-id", help="Base ID to set up (default: current)")

    # update-repo-cache command
    update_parser = subparsers.add_parser("update-repo-cache",
        help="Update repo cache with current working files")
    update_parser.add_argument("--base-id", help="Base ID to update (default: current)")

    # restore-rulebook command
    restore_rb_parser = subparsers.add_parser("restore-rulebook",
        help="Restore rulebook from repo cache")
    restore_rb_parser.add_argument("--base-id", help="Base ID (default: current)")

    # restore-english command
    restore_en_parser = subparsers.add_parser("restore-english",
        help="Restore English specification from repo cache")
    restore_en_parser.add_argument("--base-id", help="Base ID (default: current)")

    args = parser.parse_args()

    try:
        if args.command == "status":
            print_cache_status(args.base_id)

        elif args.command == "list":
            list_all_bases()

        elif args.command == "setup-offline":
            success = setup_for_offline(args.base_id)
            sys.exit(0 if success else 1)

        elif args.command == "update-repo-cache":
            success = update_repo_cache(args.base_id)
            sys.exit(0 if success else 1)

        elif args.command == "restore-rulebook":
            success = restore_rulebook_from_repo_cache(args.base_id)
            sys.exit(0 if success else 1)

        elif args.command == "restore-english":
            success = restore_english_spec_from_repo_cache(args.base_id)
            sys.exit(0 if success else 1)

        else:
            # Default: show status
            print_cache_status()

    except KeyboardInterrupt:
        print("\nCancelled")
        sys.exit(1)
    except Exception as e:
        print(f"{RED}Error: {e}{NC}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
