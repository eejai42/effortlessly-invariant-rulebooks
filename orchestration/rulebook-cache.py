#!/usr/bin/env python3
"""
Rulebook Cache Manager - Handles caching and fallback for rulebook sync.

Provides offline capability by caching the rulebook after successful Airtable sync,
and offering to use the cached version when Airtable is unavailable.
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
RULEBOOK_PATH = PROJECT_ROOT / "effortless-rulebook" / "effortless-rulebook.json"
CACHE_DIR = PROJECT_ROOT / "effortless-rulebook" / ".cache"
CACHE_METADATA_FILE = CACHE_DIR / "cache-metadata.json"

# Colors for terminal output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
BOLD = '\033[1m'
NC = '\033[0m'  # No Color


def get_current_base_id():
    """Get the current base ID from ssotme.json."""
    ssotme_path = PROJECT_ROOT / "ssotme.json"
    if not ssotme_path.exists():
        return None
    try:
        with open(ssotme_path, 'r') as f:
            config = json.load(f)
        for setting in config.get('ProjectSettings', []):
            if setting.get('Name') == 'baseId':
                return setting.get('Value')
    except Exception:
        pass
    return None


def get_project_name():
    """Get the current project name from ssotme.json."""
    ssotme_path = PROJECT_ROOT / "ssotme.json"
    if not ssotme_path.exists():
        return "Unknown"
    try:
        with open(ssotme_path, 'r') as f:
            config = json.load(f)
        return config.get('Name', 'Unknown')
    except Exception:
        return "Unknown"


def get_cache_path(base_id: str) -> Path:
    """Get the cache file path for a specific base."""
    return CACHE_DIR / f"{base_id}.json"


def load_cache_metadata() -> dict:
    """Load the cache metadata file."""
    if not CACHE_METADATA_FILE.exists():
        return {}
    try:
        with open(CACHE_METADATA_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache_metadata(metadata: dict):
    """Save the cache metadata file."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_METADATA_FILE, 'w') as f:
        json.dump(metadata, f, indent=2)


def cache_rulebook(base_id: str = None):
    """Cache the current rulebook after a successful sync."""
    if base_id is None:
        base_id = get_current_base_id()
    if not base_id:
        print(f"{YELLOW}Warning: No base ID found, skipping cache{NC}")
        return False

    if not RULEBOOK_PATH.exists():
        print(f"{YELLOW}Warning: Rulebook not found, skipping cache{NC}")
        return False

    try:
        # Create cache directory if needed
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Copy rulebook to cache
        cache_path = get_cache_path(base_id)
        shutil.copy2(RULEBOOK_PATH, cache_path)

        # Update metadata
        metadata = load_cache_metadata()
        metadata[base_id] = {
            'cached_at': datetime.now().isoformat(),
            'project_name': get_project_name(),
            'file': str(cache_path.name)
        }
        save_cache_metadata(metadata)

        print(f"{GREEN}Rulebook cached for offline use{NC}")
        return True

    except Exception as e:
        print(f"{YELLOW}Warning: Could not cache rulebook: {e}{NC}")
        return False


def restore_from_cache(base_id: str = None) -> bool:
    """Restore rulebook from cache."""
    if base_id is None:
        base_id = get_current_base_id()
    if not base_id:
        return False

    cache_path = get_cache_path(base_id)
    if not cache_path.exists():
        return False

    try:
        shutil.copy2(cache_path, RULEBOOK_PATH)
        return True
    except Exception:
        return False


def get_cache_info(base_id: str = None) -> dict:
    """Get cache info for a base."""
    if base_id is None:
        base_id = get_current_base_id()
    if not base_id:
        return None

    metadata = load_cache_metadata()
    cache_path = get_cache_path(base_id)

    if base_id not in metadata or not cache_path.exists():
        return None

    return metadata[base_id]


def run_ssotme_buildall() -> bool:
    """Run ssotme -buildall and return success status."""
    try:
        result = subprocess.run(
            ["ssotme", "-buildall"],
            cwd=PROJECT_ROOT,
            timeout=300  # 5 minute timeout
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"{RED}Error: ssotme -buildall timed out{NC}")
        return False
    except FileNotFoundError:
        print(f"{RED}Error: ssotme not found in PATH{NC}")
        return False
    except Exception as e:
        print(f"{RED}Error running ssotme: {e}{NC}")
        return False


def sync_with_fallback(force_cache: bool = False, non_interactive: bool = False) -> bool:
    """
    Sync from Airtable with fallback to cached version.

    Args:
        force_cache: Skip Airtable sync and use cache directly
        non_interactive: Don't prompt for user input (use cache automatically if available)

    Returns:
        True if rulebook is available (from sync or cache), False otherwise
    """
    base_id = get_current_base_id()
    project_name = get_project_name()
    cache_info = get_cache_info(base_id)

    if force_cache:
        if cache_info:
            print(f"{CYAN}Using cached rulebook for '{project_name}'...{NC}")
            if restore_from_cache(base_id):
                print(f"{GREEN}Restored from cache (cached: {cache_info['cached_at']}){NC}")
                return True
            else:
                print(f"{RED}Failed to restore from cache{NC}")
                return False
        else:
            print(f"{RED}No cached rulebook available for this base{NC}")
            return False

    # Try to sync from Airtable
    print(f"{BLUE}Syncing from Airtable...{NC}")
    if run_ssotme_buildall():
        # Success - cache the new rulebook
        cache_rulebook(base_id)
        return True

    # Sync failed - offer fallback
    print("")
    print(f"{YELLOW}{'='*60}{NC}")
    print(f"{YELLOW}  Airtable sync failed!{NC}")
    print(f"{YELLOW}{'='*60}{NC}")
    print("")

    if cache_info:
        cached_at = cache_info.get('cached_at', 'unknown')
        cached_name = cache_info.get('project_name', project_name)

        print(f"  A cached version is available:")
        print(f"    Project:    {CYAN}{cached_name}{NC}")
        print(f"    Base ID:    {CYAN}{base_id}{NC}")
        print(f"    Cached at:  {CYAN}{cached_at}{NC}")
        print("")

        if non_interactive:
            # In non-interactive mode, use cache automatically
            print(f"{YELLOW}Non-interactive mode: using cached rulebook{NC}")
            use_cache = True
        else:
            # Prompt user
            try:
                response = input(f"  Use cached rulebook? [{GREEN}Y{NC}/n]: ").strip().lower()
                use_cache = response in ('', 'y', 'yes')
            except (EOFError, KeyboardInterrupt):
                print("")
                use_cache = False

        if use_cache:
            if restore_from_cache(base_id):
                print(f"{GREEN}Restored from cache{NC}")
                return True
            else:
                print(f"{RED}Failed to restore from cache{NC}")
                return False
        else:
            print(f"{YELLOW}Skipping - no rulebook available{NC}")
            return False
    else:
        print(f"  {RED}No cached version available for base '{base_id}'{NC}")
        print(f"  {YELLOW}You'll need internet access to sync from Airtable.{NC}")
        return False


def list_cached():
    """List all cached rulebooks."""
    metadata = load_cache_metadata()

    if not metadata:
        print("No cached rulebooks found.")
        return

    print(f"\n{BOLD}Cached Rulebooks:{NC}\n")
    for base_id, info in metadata.items():
        cache_path = get_cache_path(base_id)
        exists = cache_path.exists()
        status = f"{GREEN}OK{NC}" if exists else f"{RED}MISSING{NC}"

        print(f"  Base ID:    {CYAN}{base_id}{NC}")
        print(f"  Project:    {info.get('project_name', 'Unknown')}")
        print(f"  Cached at:  {info.get('cached_at', 'Unknown')}")
        print(f"  Status:     {status}")
        print("")


def clear_cache():
    """Clear all cached rulebooks."""
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        print(f"{GREEN}Cache cleared{NC}")
    else:
        print("No cache to clear")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Rulebook cache manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Sync command (default behavior)
    sync_parser = subparsers.add_parser("sync", help="Sync from Airtable with fallback to cache")
    sync_parser.add_argument("--offline", action="store_true", help="Use cache directly (skip Airtable)")
    sync_parser.add_argument("--non-interactive", "-y", action="store_true",
                            help="Non-interactive mode (use cache automatically on failure)")

    # Cache command
    subparsers.add_parser("cache", help="Cache the current rulebook")

    # List command
    subparsers.add_parser("list", help="List cached rulebooks")

    # Clear command
    subparsers.add_parser("clear", help="Clear all cached rulebooks")

    # Info command
    subparsers.add_parser("info", help="Show cache info for current base")

    args = parser.parse_args()

    try:
        if args.command == "sync" or args.command is None:
            offline = getattr(args, 'offline', False)
            non_interactive = getattr(args, 'non_interactive', False) or os.environ.get('SSOTME_NONINTERACTIVE')
            success = sync_with_fallback(force_cache=offline, non_interactive=non_interactive)
            sys.exit(0 if success else 1)

        elif args.command == "cache":
            success = cache_rulebook()
            sys.exit(0 if success else 1)

        elif args.command == "list":
            list_cached()

        elif args.command == "clear":
            clear_cache()

        elif args.command == "info":
            info = get_cache_info()
            if info:
                print(f"Project:    {info.get('project_name', 'Unknown')}")
                print(f"Cached at:  {info.get('cached_at', 'Unknown')}")
            else:
                print("No cache available for current base")
                sys.exit(1)

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\nCancelled")
        sys.exit(1)
    except Exception as e:
        print(f"{RED}Error: {e}{NC}", file=sys.stderr)
        sys.exit(1)
