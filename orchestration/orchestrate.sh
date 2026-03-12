#!/bin/bash
# =============================================================================
# ORCHESTRATE.SH
# =============================================================================
# Central orchestration for ERB execution substrates.
# Handles: Airtable sync, running tests, viewing results, cleaning.
# =============================================================================

set -e
set -o pipefail  # CRITICAL: Catch failures in piped commands (e.g., bash script | tee)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SUBSTRATES_DIR="$PROJECT_ROOT/execution-substrates"
SSOTME_JSON="$PROJECT_ROOT/ssotme.json"

# =============================================================================
# COLORS
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Substrate colors (cycle through for visual distinction)
SUBSTRATE_COLORS=(
    '\033[38;5;214m'  # Orange
    '\033[38;5;118m'  # Bright green
    '\033[38;5;147m'  # Light purple
    '\033[38;5;81m'   # Sky blue
    '\033[38;5;219m'  # Pink
    '\033[38;5;228m'  # Light yellow
    '\033[38;5;123m'  # Aqua
    '\033[38;5;183m'  # Lavender
    '\033[38;5;203m'  # Coral
    '\033[38;5;157m'  # Mint
    '\033[38;5;208m'  # Dark orange
    '\033[38;5;120m'  # Light green
)

# =============================================================================
# PARSE ARGUMENTS
# =============================================================================
CI_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --ci)
            CI_MODE=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

# =============================================================================
# TOOL DETECTION
# =============================================================================
if [ -z "$SSOTME_AVAILABLE" ]; then
    if command -v ssotme &> /dev/null; then
        SSOTME_AVAILABLE=true
    else
        SSOTME_AVAILABLE=false
    fi
fi

if command -v psql &> /dev/null; then
    POSTGRES_AVAILABLE=true
else
    POSTGRES_AVAILABLE=false
fi

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
get_current_base_id() {
    if [ -f "$SSOTME_JSON" ]; then
        python3 -c "
import json
with open('$SSOTME_JSON', 'r') as f:
    config = json.load(f)
for setting in config.get('ProjectSettings', []):
    if setting.get('Name') == 'baseId':
        print(setting.get('Value', ''))
        break
"
    else
        echo ""
    fi
}

get_project_name() {
    if [ -f "$SSOTME_JSON" ]; then
        python3 -c "
import json
with open('$SSOTME_JSON', 'r') as f:
    config = json.load(f)
print(config.get('Name', 'Unknown'))
"
    else
        echo "Unknown"
    fi
}

get_bases_list() {
    # Read from separate bases.json file (primary) or fallback to ssotme.json
    BASES_FILE="$SCRIPT_DIR/bases.json"
    python3 -c "
import json
import os
import sys

bases_file = '$BASES_FILE'
ssotme_file = '$SSOTME_JSON'

# Try bases.json first
if os.path.exists(bases_file):
    try:
        with open(bases_file, 'r') as f:
            bases = json.load(f)
            for base in bases:
                print(base['id'] + '|' + base['name'])
        sys.exit(0)
    except SystemExit:
        raise
    except Exception:
        pass

# Fallback to ssotme.json
if os.path.exists(ssotme_file):
    try:
        with open(ssotme_file, 'r') as f:
            config = json.load(f)
        for setting in config.get('ProjectSettings', []):
            if setting.get('Name') == 'bases':
                bases = json.loads(setting.get('Value', '[]'))
                for base in bases:
                    print(base['id'] + '|' + base['name'])
                break
    except Exception:
        pass
"
}

get_bases_count() {
    get_bases_list | wc -l | tr -d ' '
}

# =============================================================================
# MENU DISPLAY
# =============================================================================
show_menu() {
    PROJECT_NAME=$(get_project_name)
    CURRENT_BASE=$(get_current_base_id)

    echo ""
    echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║${NC}          ${BOLD}${WHITE}EXECUTION SUBSTRATE ORCHESTRATOR${NC}                  ${BOLD}${CYAN}║${NC}"
    echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Project:  ${WHITE}$PROJECT_NAME${NC}"
    echo -e "  Airtable: ${CYAN}https://airtable.com/$CURRENT_BASE${NC}"
    echo ""

    # Get list of substrates for the menu
    SUBSTRATES=$(ls -d "$SUBSTRATES_DIR"/*/ 2>/dev/null | xargs -n1 basename)
    SUBSTRATES_ARRAY=($SUBSTRATES)
    TOTAL_SUBSTRATES=${#SUBSTRATES_ARRAY[@]}

    echo -e "${BOLD}${WHITE}Select an option:${NC}"
    echo ""
    echo -e "  ${GREEN}[A]${NC} Run ${BOLD}ALL${NC} substrates ($TOTAL_SUBSTRATES total) ${DIM}(default)${NC}"
    echo -e "  ${MAGENTA}[V]${NC} ${BOLD}VIEW RESULTS${NC} - Generate and open HTML report"
    echo ""

    echo -e "  ${DIM}────────────────────────────────────────${NC}"
    echo -e "  ${YELLOW}Or select a specific substrate:${NC}"
    echo ""

    # Display substrates with numbers
    INDEX=1
    for substrate in $SUBSTRATES; do
        substrate_dir="$SUBSTRATES_DIR/$substrate"
        inject_script="$substrate_dir/inject-substrate.sh"
        if [ -f "$inject_script" ]; then
            if [ $INDEX -lt 10 ]; then
                echo -e "  ${CYAN}[0$INDEX]${NC} $substrate"
            else
                echo -e "  ${CYAN}[$INDEX]${NC} $substrate"
            fi
        fi
        INDEX=$((INDEX + 1))
    done

    # Airtable/Sync options
    echo -e "  ${DIM}────────────────────────────────────────${NC}"
    # Dev-Ops
    echo -e "  ${RED}[C]${NC} ${BOLD}CLEAN${NC} all generated files"
    echo -e "  ${YELLOW}[D]${NC} ${BOLD}DEV-OPS${NC} menu (PostgreSQL init, SSoTME setup)"
    if [ "$SSOTME_AVAILABLE" = true ]; then
        echo -e "  ${CYAN}[P]${NC} ${BOLD}PULL${NC} & Inject (Airtable → Postgres → Substrates)"
        echo -e "  ${CYAN}[B]${NC} ${BOLD}CHANGE BASE ID${NC} and pull"
    else
        echo -e "  ${DIM}[P] Pull & Inject (requires SSoTME)${NC}"
        echo -e "  ${DIM}[B] Change Base ID (requires SSoTME)${NC}"
    fi

    echo ""

    echo -e "  [${RED}Q${NC}] Quit"
    echo ""

}

# =============================================================================
# ACTION FUNCTIONS
# =============================================================================
action_pull_airtable() {
    CURRENT_BASE=$(get_current_base_id)

    if [ "$SSOTME_AVAILABLE" != true ]; then
        echo ""
        echo -e "${RED}SSoTME is not installed.${NC}"
        echo -e "Visit ${CYAN}https://www.ssotme.com${NC} for installation instructions."
        echo ""
        read -p "Press Enter to continue..."
        return
    fi

    echo ""
    echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║${NC}              ${BOLD}${WHITE}PULL & INJECT RULEBOOK${NC}                        ${BOLD}${CYAN}║${NC}"
    echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Base ID: ${WHITE}$CURRENT_BASE${NC}"
    echo ""

    # Step 1: Pull from Airtable
    echo -e "${BOLD}${BLUE}┌──────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${BOLD}${BLUE}│${NC} ${BOLD}${WHITE}STEP 1:${NC} ${YELLOW}Pulling from Airtable (ssotme -buildall)...${NC}        ${BOLD}${BLUE}│${NC}"
    echo -e "${BOLD}${BLUE}└──────────────────────────────────────────────────────────────┘${NC}"
    echo ""

    cd "$PROJECT_ROOT"
    ssotme -buildall

    echo ""

    # Step 2: Generate answer keys from PostgreSQL
    echo -e "${BOLD}${BLUE}┌──────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${BOLD}${BLUE}│${NC} ${BOLD}${WHITE}STEP 2:${NC} ${YELLOW}Generating answer keys from PostgreSQL...${NC}          ${BOLD}${BLUE}│${NC}"
    echo -e "${BOLD}${BLUE}└──────────────────────────────────────────────────────────────┘${NC}"
    echo ""

    python3 -c "
import sys
import psycopg2
sys.path.insert(0, '$SCRIPT_DIR')
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

# Load test-orchestrator module
spec = spec_from_loader('test_orchestrator', SourceFileLoader('test_orchestrator', '$SCRIPT_DIR/test-orchestrator.py'))
test_orch = module_from_spec(spec)
spec.loader.exec_module(test_orch)

# Load rulebook and connect to database
rulebook = test_orch.load_rulebook()
conn = psycopg2.connect(test_orch.DB_CONNECTION)

# Generate answer keys and blank tests
all_answer_keys = test_orch.generate_all_answer_keys(conn, rulebook)
test_orch.generate_all_blank_tests(all_answer_keys, rulebook)

conn.close()
print('Answer keys and blank tests generated.')
"

    echo ""

    # Step 3: Inject rulebook into all substrates
    echo -e "${BOLD}${BLUE}┌──────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${BOLD}${BLUE}│${NC} ${BOLD}${WHITE}STEP 3:${NC} ${YELLOW}Injecting rulebook into all substrates...${NC}          ${BOLD}${BLUE}│${NC}"
    echo -e "${BOLD}${BLUE}└──────────────────────────────────────────────────────────────┘${NC}"
    echo ""

    SUBSTRATES=$(ls -d "$SUBSTRATES_DIR"/*/ 2>/dev/null | xargs -n1 basename)
    for substrate in $SUBSTRATES; do
        substrate_dir="$SUBSTRATES_DIR/$substrate"
        inject_script="$substrate_dir/inject-into-${substrate}.py"

        if [ -f "$inject_script" ]; then
            echo -e "  ${CYAN}▶${NC} Injecting into ${BOLD}$substrate${NC}..."
            (cd "$substrate_dir" && python3 "inject-into-${substrate}.py" 2>&1) || {
                echo -e "    ${YELLOW}⚠${NC} Warning: inject-into-${substrate}.py had issues"
            }
        else
            echo -e "  ${DIM}○ $substrate: no inject script${NC}"
        fi
    done

    echo ""
    echo -e "${BOLD}${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║${NC}              ${BOLD}${WHITE}PULL & INJECT COMPLETE${NC}                        ${BOLD}${GREEN}║${NC}"
    echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${DIM}Rulebook has been pulled from Airtable and injected into all substrates.${NC}"
    echo -e "${DIM}Run tests with [A] to verify all substrates.${NC}"
    echo ""
    read -p "Press Enter to continue..."
}

action_change_base_id() {
    CURRENT_BASE=$(get_current_base_id)
    PROJECT_NAME=$(get_project_name)

    if [ "$SSOTME_AVAILABLE" != true ]; then
        echo ""
        echo -e "${RED}SSoTME is not installed.${NC}"
        echo -e "Base swapping requires SSoTME to regenerate code after changing the base."
        echo ""
        read -p "Press Enter to continue..."
        return
    fi

    echo ""
    echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║${NC}              ${BOLD}${WHITE}SELECT AIRTABLE BASE${NC}                          ${BOLD}${CYAN}║${NC}"
    echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  Current: ${GREEN}${PROJECT_NAME}${NC} ${DIM}(${CURRENT_BASE})${NC}"
    echo ""
    echo -e "  ${DIM}────────────────────────────────────────${NC}"
    echo -e "  ${BOLD}${WHITE}Known bases:${NC}"
    echo ""

    # Sync bases list to ensure current base is included (ignore errors)
    python3 "$SCRIPT_DIR/base-manager.py" sync >/dev/null 2>&1 || true

    # Get bases list and display with numbers
    BASES_LIST=$(get_bases_list)
    BASES_ARRAY=()
    INDEX=1
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            BASE_ID=$(echo "$line" | cut -d'|' -f1)
            BASE_NAME=$(echo "$line" | cut -d'|' -f2)
            BASES_ARRAY+=("$line")
            if [ "$BASE_ID" = "$CURRENT_BASE" ]; then
                echo -e "  ${GREEN}[$INDEX]${NC} ${GREEN}${BASE_NAME}${NC} ${DIM}(active)${NC}"
            else
                echo -e "  ${CYAN}[$INDEX]${NC} ${BASE_NAME}"
            fi
            echo -e "      ${DIM}${BASE_ID}${NC}"
            INDEX=$((INDEX + 1))
        fi
    done <<< "$BASES_LIST"

    BASES_COUNT=${#BASES_ARRAY[@]}

    echo ""
    echo -e "  ${DIM}────────────────────────────────────────${NC}"
    echo -e "  ${YELLOW}[N]${NC} Add ${BOLD}NEW${NC} base by ID"
    echo -e "  ${RED}[Q]${NC} Cancel"
    echo ""

    read -p "  Select base [1-$BASES_COUNT, N, Q]: " BASE_CHOICE

    case $BASE_CHOICE in
        [Qq]|"")
            echo ""
            echo -e "  ${DIM}Cancelled - no changes made${NC}"
            echo ""
            return
            ;;
        [Nn])
            # Add new base
            echo ""
            read -p "  Enter new Airtable base ID (e.g., appXXXXX): " NEW_BASE_ID

            if [ -z "$NEW_BASE_ID" ]; then
                echo ""
                echo -e "  ${DIM}Cancelled - no changes made${NC}"
                echo ""
                return
            fi

            # Validate format
            if [[ ! "$NEW_BASE_ID" =~ ^app[A-Za-z0-9]+ ]]; then
                echo ""
                echo -e "${RED}Invalid Base ID format.${NC}"
                echo -e "Airtable Base IDs start with 'app' followed by alphanumeric characters."
                echo ""
                read -p "Press Enter to continue..."
                return
            fi

            echo ""
            echo -e "${YELLOW}Fetching base name from Airtable...${NC}"

            # Add the base - name is fetched from Airtable (NO FALLBACKS)
            if ! python3 "$SCRIPT_DIR/base-manager.py" add "$NEW_BASE_ID"; then
                echo ""
                echo -e "${RED}Failed to add base - could not fetch name from Airtable${NC}"
                echo ""
                read -p "Press Enter to continue..."
                return
            fi

            if ! python3 "$SCRIPT_DIR/base-manager.py" select "$NEW_BASE_ID"; then
                echo ""
                echo -e "${RED}Failed to select base${NC}"
                echo ""
                read -p "Press Enter to continue..."
                return
            fi
            ;;
        [0-9]|[0-9][0-9])
            # Select existing base by number
            if [ "$BASE_CHOICE" -ge 1 ] && [ "$BASE_CHOICE" -le "$BASES_COUNT" ]; then
                SELECTED_LINE="${BASES_ARRAY[$((BASE_CHOICE - 1))]}"
                NEW_BASE_ID=$(echo "$SELECTED_LINE" | cut -d'|' -f1)
                NEW_BASE_NAME=$(echo "$SELECTED_LINE" | cut -d'|' -f2)

                if [ "$NEW_BASE_ID" = "$CURRENT_BASE" ]; then
                    echo ""
                    echo -e "  ${DIM}Already using this base${NC}"
                    echo ""
                    read -p "Press Enter to continue..."
                    return
                fi

                echo ""
                echo -e "Switching to: ${WHITE}${NEW_BASE_NAME}${NC}"
                if ! python3 "$SCRIPT_DIR/base-manager.py" select "$NEW_BASE_ID"; then
                    echo ""
                    echo -e "${RED}Failed to select base${NC}"
                    echo ""
                    read -p "Press Enter to continue..."
                    return
                fi
            else
                echo ""
                echo -e "${RED}Invalid selection: $BASE_CHOICE${NC}"
                echo ""
                read -p "Press Enter to continue..."
                return
            fi
            ;;
        *)
            echo ""
            echo -e "${RED}Invalid option: $BASE_CHOICE${NC}"
            echo ""
            read -p "Press Enter to continue..."
            return
            ;;
    esac

    # Regenerate from new base
    echo ""
    echo -e "${YELLOW}Regenerating from new base...${NC}"
    echo ""

    cd "$PROJECT_ROOT"
    # Use || to prevent set -e from killing the script on failure
    BUILDALL_FAILED=""
    ssotme -buildall || BUILDALL_FAILED="true"

    if [ -z "$BUILDALL_FAILED" ]; then
        NEW_PROJECT_NAME=$(get_project_name)
        NEW_BASE=$(get_current_base_id)
        echo ""
        echo -e "${BOLD}${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}${GREEN}║${NC}              ${BOLD}${WHITE}BASE SWITCH COMPLETE${NC}                         ${BOLD}${GREEN}║${NC}"
        echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "  Project: ${WHITE}$NEW_PROJECT_NAME${NC}"
        echo -e "  Base ID: ${WHITE}$NEW_BASE${NC}"
    else
        echo ""
        echo -e "${RED}Regeneration failed.${NC}"
        echo -e "You may need to restore the previous base: ${WHITE}$PROJECT_NAME${NC} (${CURRENT_BASE})"
    fi
    echo ""
    read -p "Press Enter to continue..."
}

action_view_results() {
    echo ""
    echo -e "${BOLD}${MAGENTA}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${MAGENTA}║${NC}              ${BOLD}${WHITE}GENERATING HTML REPORT${NC}                       ${BOLD}${MAGENTA}║${NC}"
    echo -e "${BOLD}${MAGENTA}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    # Note: We don't regenerate individual substrate reports here because:
    # 1. They were already generated during the test run
    # 2. Regenerating would overwrite meaningful logs with stale data (e.g., for skipped tests)
    # The orchestration report reads from the existing substrate-report.html files

    # Generate main orchestration report
    python3 "$SCRIPT_DIR/generate-report.py"
    echo ""
    echo -e "${BOLD}${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║${NC}              ${BOLD}${WHITE}REPORT GENERATED${NC}                              ${BOLD}${GREEN}║${NC}"
    echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    read -p "Press Enter to continue..."
}

action_clean() {
    SUBSTRATES=$(ls -d "$SUBSTRATES_DIR"/*/ 2>/dev/null | xargs -n1 basename)

    echo ""
    echo -e "${BOLD}${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${RED}║${NC}              ${BOLD}${WHITE}CLEANING ALL SUBSTRATES${NC}                       ${BOLD}${RED}║${NC}"
    echo -e "${BOLD}${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    for substrate in $SUBSTRATES; do
        substrate_dir="$SUBSTRATES_DIR/$substrate"
        echo -e "${YELLOW}Cleaning ${substrate}...${NC}"

        # Try different clean methods in order of preference
        if [ -f "$substrate_dir/inject-into-${substrate}.py" ]; then
            # Most substrates have inject-into-*.py with --clean
            (cd "$substrate_dir" && python3 "inject-into-${substrate}.py" --clean 2>/dev/null) || true
        elif [ -f "$substrate_dir/clean.py" ]; then
            # YAML has a separate clean.py
            (cd "$substrate_dir" && python3 clean.py --clean 2>/dev/null) || true
        else
            echo -e "  ${DIM}No clean script found${NC}"
        fi
    done

    echo ""
    echo -e "${BOLD}${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║${NC}              ${BOLD}${WHITE}CLEAN COMPLETE${NC}                                ${BOLD}${GREEN}║${NC}"
    echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    read -p "Press Enter to continue..."
}

# =============================================================================
# DEV-OPS ACTIONS
# =============================================================================
action_devops_menu() {
    while true; do
        echo ""
        echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BOLD}${CYAN}║${NC}                    ${BOLD}${WHITE}DEV-OPS MENU${NC}                           ${BOLD}${CYAN}║${NC}"
        echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
        echo ""

        # PostgreSQL
        if $POSTGRES_AVAILABLE; then
            echo -e "  [${CYAN}I${NC}] Initialize PostgreSQL Database"
        else
            echo -e "  ${DIM}[I] Initialize PostgreSQL (not installed)${NC}"
        fi

        # SSoTME setup
        if [ "$SSOTME_AVAILABLE" = true ]; then
            echo -e "  ${DIM}[S] SSoTME Setup (already installed)${NC}"
        else
            echo -e "  [${CYAN}S${NC}] SSoTME Setup Instructions"
        fi

        echo ""
        echo -e "  ${DIM}────────────────────────────────────────${NC}"
        echo -e "  ${BOLD}Tool Status:${NC}"
        if [ "$SSOTME_AVAILABLE" = true ]; then
            echo -e "    SSoTME:     ${GREEN}Available${NC}"
        else
            echo -e "    SSoTME:     ${YELLOW}Not installed${NC} ${DIM}(Airtable sync disabled)${NC}"
        fi

        if $POSTGRES_AVAILABLE; then
            echo -e "    PostgreSQL: ${GREEN}Available${NC}"
        else
            echo -e "    PostgreSQL: ${YELLOW}Not installed${NC} ${DIM}(DB init disabled)${NC}"
        fi
        echo ""

        echo -e "  [${RED}Q${NC}] Back to main menu"
        echo ""

        read -p "Enter choice [I/S/Q]: " devops_choice

        case $devops_choice in
            [Ii])
                if $POSTGRES_AVAILABLE; then
                    action_init_postgres
                else
                    echo ""
                    echo -e "${RED}PostgreSQL is not installed.${NC}"
                    read -p "Press Enter to continue..."
                fi
                ;;
            [Ss])
                action_setup_ssotme
                ;;
            [Qq]|"")
                return
                ;;
            *)
                echo ""
                echo -e "${RED}Invalid option: $devops_choice${NC}"
                sleep 1
                ;;
        esac
    done
}

action_setup_ssotme() {
    echo ""
    echo -e "${BOLD}${CYAN}SSoTME Installation Instructions${NC}"
    echo ""
    echo -e "SSoTME (Single Source of Truth Made Easy) is required for:"
    echo -e "  ${DIM}-${NC} Pulling data from Airtable"
    echo -e "  ${DIM}-${NC} Regenerating code from rulebook changes"
    echo ""
    echo -e "${YELLOW}To install SSoTME:${NC}"
    echo ""
    echo -e "  1. Visit: ${CYAN}https://www.ssotme.com${NC}"
    echo -e "  2. Follow the installation instructions for your platform"
    echo -e "  3. Run ${WHITE}ssotme --version${NC} to verify installation"
    echo ""
    echo -e "${DIM}Note: You can still run substrate tests without SSoTME using existing files.${NC}"
    echo ""
    read -p "Press Enter to continue..."
}

action_init_postgres() {
    if ! $POSTGRES_AVAILABLE; then
        echo ""
        echo -e "${RED}PostgreSQL (psql) is not installed or not in PATH.${NC}"
        echo ""
        echo -e "${YELLOW}To install PostgreSQL:${NC}"
        echo -e "  macOS:  ${WHITE}brew install postgresql${NC}"
        echo -e "  Ubuntu: ${WHITE}sudo apt install postgresql${NC}"
        echo ""
        read -p "Press Enter to continue..."
        return
    fi

    echo ""
    echo -e "${BOLD}${CYAN}Initialize PostgreSQL Database${NC}"
    echo ""

    local init_script="$PROJECT_ROOT/postgres/init-db.sh"

    if [ ! -f "$init_script" ]; then
        echo -e "${RED}Error: init-db.sh not found at $init_script${NC}"
        read -p "Press Enter to continue..."
        return
    fi

    echo -e "${YELLOW}This will:${NC}"
    echo -e "  1. Drop existing tables (if any)"
    echo -e "  2. Create tables, functions, and views"
    echo -e "  3. Insert seed data"
    echo ""

    read -p "Proceed? [Y/n]: " confirm
    if [[ "$confirm" =~ ^[Nn]$ ]]; then
        echo "Cancelled."
        return
    fi

    echo ""
    bash "$init_script"

    echo ""
    read -p "Press Enter to continue..."
}

# =============================================================================
# RUN SUBSTRATES (extracted as function for reuse)
# =============================================================================
run_substrates() {
    local RUN_SINGLE="$1"

    # Get substrates list
    SUBSTRATES=$(ls -d "$SUBSTRATES_DIR"/*/ 2>/dev/null | xargs -n1 basename)
    SUBSTRATES_ARRAY=($SUBSTRATES)
    TOTAL_SUBSTRATES=${#SUBSTRATES_ARRAY[@]}

    # -----------------------------------------------------------------------------
    # Step 1: Generate answer key and blank test from database
    # -----------------------------------------------------------------------------
echo -e "${BOLD}${BLUE}┌──────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BOLD}${BLUE}│${NC} ${BOLD}${WHITE}STEP 1:${NC} ${YELLOW}Generating answer key and blank test...${NC}              ${BOLD}${BLUE}│${NC}"
echo -e "${BOLD}${BLUE}└──────────────────────────────────────────────────────────────┘${NC}"
python3 -c "
import sys
import psycopg2
sys.path.insert(0, '$SCRIPT_DIR')
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

# Load test-orchestrator module
spec = spec_from_loader('test_orchestrator', SourceFileLoader('test_orchestrator', '$SCRIPT_DIR/test-orchestrator.py'))
test_orch = module_from_spec(spec)
spec.loader.exec_module(test_orch)

# Load rulebook and connect to database
rulebook = test_orch.load_rulebook()
conn = psycopg2.connect(test_orch.DB_CONNECTION)

# Run steps 1 and 2 (new generic functions)
all_answer_keys = test_orch.generate_all_answer_keys(conn, rulebook)
test_orch.generate_all_blank_tests(all_answer_keys, rulebook)

conn.close()
"
echo ""

# -----------------------------------------------------------------------------
# Step 2: Run inject-substrate.sh for each substrate
# -----------------------------------------------------------------------------
echo -e "${BOLD}${BLUE}┌──────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BOLD}${BLUE}│${NC} ${BOLD}${WHITE}STEP 2:${NC} ${YELLOW}Running inject + test for each substrate...${NC}         ${BOLD}${BLUE}│${NC}"
echo -e "${BOLD}${BLUE}└──────────────────────────────────────────────────────────────┘${NC}"
echo ""

# Determine which substrates to process
if [ -n "$RUN_SINGLE" ]; then
    SUBSTRATES_TO_RUN="$RUN_SINGLE"
    TOTAL_TO_RUN=1
else
    SUBSTRATES_TO_RUN=$(ls -d "$SUBSTRATES_DIR"/*/ 2>/dev/null | xargs -n1 basename)
    TOTAL_TO_RUN=$(echo "$SUBSTRATES_TO_RUN" | wc -w | tr -d ' ')
fi

INJECT_RESULTS=""
COLOR_INDEX=0
CURRENT=0

# Array to store failed substrates (outputs stored in temp files)
FAILED_SUBSTRATES=""
FAILED_OUTPUTS_DIR=$(mktemp -d)
trap "rm -rf $FAILED_OUTPUTS_DIR" EXIT

for substrate in $SUBSTRATES_TO_RUN; do
    substrate_dir="$SUBSTRATES_DIR/$substrate"
    inject_script="$substrate_dir/inject-substrate.sh"
    CURRENT=$((CURRENT + 1))

    # Get color for this substrate
    COLOR="${SUBSTRATE_COLORS[$COLOR_INDEX]}"
    COLOR_INDEX=$(( (COLOR_INDEX + 1) % ${#SUBSTRATE_COLORS[@]} ))

    if [ -f "$inject_script" ]; then
        substrate_upper=$(echo "$substrate" | tr '[:lower:]' '[:upper:]')
        echo -e "${COLOR}╔══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${COLOR}║${NC} ${BOLD}[$CURRENT/$TOTAL_TO_RUN]${NC} ${COLOR}▶ ${BOLD}${substrate_upper}${NC}"
        echo -e "${COLOR}╚══════════════════════════════════════════════════════════════╝${NC}"

        # Backup/restore mechanism to preserve successful results on failure
        test_answers_dir="$substrate_dir/test-answers"
        test_answers_backup="$substrate_dir/test-answers.bak"

        # Backup existing test-answers before clearing (if they exist and have files)
        if [ -d "$test_answers_dir" ] && [ "$(ls -A "$test_answers_dir" 2>/dev/null)" ]; then
            echo -e "  ${DIM}Backing up previous test-answers...${NC}"
            rm -rf "$test_answers_backup"
            cp -r "$test_answers_dir" "$test_answers_backup"
        fi

        # Clear test-answers for fresh run
        if [ -d "$test_answers_dir" ]; then
            rm -rf "$test_answers_dir"
        fi
        mkdir -p "$test_answers_dir"

        # Run script with real-time output AND capture for error reporting
        # Use tee to show output live while also saving to temp file
        # CRITICAL: Use || true to prevent set -e from exiting, then capture PIPESTATUS
        INJECT_TEMP_FILE=$(mktemp)
        START_TIME=$(python3 -c "import time; print(time.time())")
        # Run the script; with pipefail set, pipeline returns first non-zero exit code
        # The '|| true' prevents set -e from exiting, while PIPESTATUS still captures the real exit code
        bash "$inject_script" 2>&1 | tee "$INJECT_TEMP_FILE" || true
        INJECT_EXIT_CODE=${PIPESTATUS[0]}  # Capture IMMEDIATELY - must be first command after pipeline
        END_TIME=$(python3 -c "import time; print(time.time())")
        ELAPSED_TIME=$(python3 -c "print($END_TIME - $START_TIME)")
        INJECT_OUTPUT=$(cat "$INJECT_TEMP_FILE")
        rm -f "$INJECT_TEMP_FILE"

        # Check for SUBSTRATE_SKIPPED_BUT_GRADE signal (preserve timing from last run)
        PRESERVE_TIMING=false
        if echo "$INJECT_OUTPUT" | grep -q "SUBSTRATE_SKIPPED_BUT_GRADE"; then
            PRESERVE_TIMING=true
            echo -e "  ${YELLOW}○${NC} ${substrate}: ${YELLOW}Using previous answers (timing preserved)${NC}"
        fi

        if [ $INJECT_EXIT_CODE -eq 0 ]; then
            if ! $PRESERVE_TIMING; then
                INJECT_RESULTS="$INJECT_RESULTS$substrate:OK\n"
                echo -e "  ${GREEN}✓${NC} ${substrate}: ${GREEN}${BOLD}OK${NC}"
            fi
            # Success: delete backup (new results are good)
            rm -rf "$test_answers_backup"
        else
            INJECT_RESULTS="$INJECT_RESULTS$substrate:FAILED\n"
            echo -e "  ${RED}✗${NC} ${substrate}: ${RED}${BOLD}FAILED TO EXECUTE${NC}"
            # Store failure information
            FAILED_SUBSTRATES="$FAILED_SUBSTRATES $substrate"
            echo "$INJECT_OUTPUT" > "$FAILED_OUTPUTS_DIR/$substrate.txt"
            # Failure: restore backup to preserve previous successful results
            if [ -d "$test_answers_backup" ]; then
                echo -e "  ${YELLOW}↩${NC} Restoring previous test-answers from backup..."
                rm -rf "$test_answers_dir"
                mv "$test_answers_backup" "$test_answers_dir"
            fi

            # ═══════════════════════════════════════════════════════════════
            # FAIL LOUDLY: Pause and ask user if they want to continue
            # ═══════════════════════════════════════════════════════════════
            if ! $CI_MODE; then
                echo ""
                echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
                echo -e "${RED}║${NC}     ${BOLD}${RED}⚠️  SUBSTRATE FAILED: ${substrate_upper}${NC}                          ${RED}║${NC}"
                echo -e "${RED}╠════════════════════════════════════════════════════════════════╣${NC}"
                echo -e "${RED}║${NC} ${DIM}Last 10 lines of output:${NC}                                       ${RED}║${NC}"
                echo -e "${RED}╟────────────────────────────────────────────────────────────────╢${NC}"
                tail -10 "$FAILED_OUTPUTS_DIR/$substrate.txt" | while IFS= read -r line; do
                    # Truncate long lines and format
                    truncated="${line:0:60}"
                    printf "${RED}║${NC} %-60s ${RED}║${NC}\n" "$truncated"
                done
                echo -e "${RED}╠════════════════════════════════════════════════════════════════╣${NC}"
                echo -e "${RED}║${NC}  ${YELLOW}[C]${NC} Continue with remaining substrates                        ${RED}║${NC}"
                echo -e "${RED}║${NC}  ${RED}[S]${NC} Stop orchestration now                                    ${RED}║${NC}"
                echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
                echo ""
                read -p "  Choice [C/S]: " FAILURE_CHOICE
                case $FAILURE_CHOICE in
                    [Ss])
                        echo ""
                        echo -e "${RED}${BOLD}Orchestration stopped by user after failure.${NC}"
                        echo -e "Run ${WHITE}./orchestrate.sh${NC} to retry."
                        echo ""
                        # Still grade and save what we have before exiting
                        return 1
                        ;;
                    *)
                        echo ""
                        echo -e "${YELLOW}Continuing with remaining substrates...${NC}"
                        echo ""
                        ;;
                esac
            fi
        fi

        # Grade this substrate immediately
        python3 -c "
import sys
import json
import os
import glob
sys.path.insert(0, '$SCRIPT_DIR')
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

spec = spec_from_loader('test_orchestrator', SourceFileLoader('test_orchestrator', '$SCRIPT_DIR/test-orchestrator.py'))
test_orch = module_from_spec(spec)
spec.loader.exec_module(test_orch)

# Load all answer keys
all_answer_keys = {}
for entity_file in glob.glob(os.path.join(test_orch.ANSWER_KEYS_DIR, '*.json')):
    entity = os.path.basename(entity_file).replace('.json', '')
    with open(entity_file, 'r') as f:
        all_answer_keys[entity] = json.load(f)

# Load rulebook for grading
rulebook = test_orch.load_rulebook()

substrate = '$substrate'
inject_exit_code = $INJECT_EXIT_CODE
elapsed_seconds = $ELAPSED_TIME
preserve_timing = True if '$PRESERVE_TIMING' == 'true' else False

# Grade substrate (new generic function)
if inject_exit_code != 0:
    grades = test_orch.grade_substrate(substrate, all_answer_keys, rulebook)
    grades['error'] = 'FAILED TO EXECUTE (inject-substrate.sh returned non-zero)'
    grades['execution_failed'] = True
    error_msg = 'inject-substrate.sh returned non-zero exit code'
else:
    grades = test_orch.grade_substrate(substrate, all_answer_keys, rulebook)
    error_msg = None

# Add timing information (use previous timing if preserve_timing is True)
if preserve_timing:
    # Load previous timing from metadata
    metadata = test_orch.load_run_metadata(substrate)
    prev_run = metadata.get('last_successful_run') or metadata.get('last_run')
    if prev_run and 'duration_seconds' in prev_run:
        grades['elapsed_seconds'] = prev_run['duration_seconds']
        grades['timing_preserved'] = True
    else:
        grades['elapsed_seconds'] = elapsed_seconds
else:
    grades['elapsed_seconds'] = elapsed_seconds

# Update run metadata (tracks success/failure history)
success = inject_exit_code == 0
test_orch.update_run_metadata(substrate, grades, success, error_msg, preserve_timing=preserve_timing)

test_orch.generate_substrate_report(substrate, grades, rulebook)
test_orch.print_substrate_test_summary(substrate, grades, rulebook)

# Generate per-substrate HTML report using the substrate's custom script
# SKIP if preserve_timing=True (test was skipped) - keeps previous meaningful log intact
import subprocess
substrate_dir = os.path.join(test_orch.SUBSTRATES_DIR, substrate)
custom_script = os.path.join(substrate_dir, 'create-substrate-report.sh')
if os.path.exists(custom_script) and not preserve_timing:
    subprocess.run(['bash', 'create-substrate-report.sh'], cwd=substrate_dir, capture_output=True)

# Save grades to temp file for final summary
import pickle
grades_file = os.path.join(test_orch.SUBSTRATES_DIR, substrate, '.grades.pkl')
with open(grades_file, 'wb') as f:
    pickle.dump(grades, f)

# Also write score to a simple file for bash to check
score_file = os.path.join(test_orch.SUBSTRATES_DIR, substrate, '.score')
score = grades.get('score', -1)
with open(score_file, 'w') as f:
    f.write(str(score))
"
        # Check for 0% score and pause if so (similar to execution failure)
        score_file="$SUBSTRATES_DIR/$substrate/.score"
        if [ -f "$score_file" ]; then
            SCORE=$(cat "$score_file")
            rm -f "$score_file"  # Clean up

            # Check if score is 0 (using bc for float comparison)
            if echo "$SCORE == 0" | bc -l | grep -q 1; then
                # Only pause if execution itself succeeded (0% test score is the issue)
                if [ $INJECT_EXIT_CODE -eq 0 ] && ! $CI_MODE; then
                    echo ""
                    echo -e "${YELLOW}╔════════════════════════════════════════════════════════════════╗${NC}"
                    echo -e "${YELLOW}║${NC}     ${BOLD}${YELLOW}⚠️  TEST SCORE 0%: ${substrate_upper}${NC}                             ${YELLOW}║${NC}"
                    echo -e "${YELLOW}╠════════════════════════════════════════════════════════════════╣${NC}"
                    echo -e "${YELLOW}║${NC} ${DIM}Execution succeeded but all tests failed.${NC}                      ${YELLOW}║${NC}"
                    echo -e "${YELLOW}║${NC} ${DIM}This usually means test-answers are missing or stale.${NC}          ${YELLOW}║${NC}"
                    echo -e "${YELLOW}╠════════════════════════════════════════════════════════════════╣${NC}"
                    echo -e "${YELLOW}║${NC}  ${GREEN}[C]${NC} Continue with remaining substrates                        ${YELLOW}║${NC}"
                    echo -e "${YELLOW}║${NC}  ${RED}[S]${NC} Stop orchestration now                                    ${YELLOW}║${NC}"
                    echo -e "${YELLOW}╚════════════════════════════════════════════════════════════════╝${NC}"
                    echo ""
                    read -p "  Choice [C/S]: " SCORE_CHOICE
                    case $SCORE_CHOICE in
                        [Ss])
                            echo ""
                            echo -e "${YELLOW}${BOLD}Orchestration stopped by user after 0% score.${NC}"
                            echo -e "Run ${WHITE}./orchestrate.sh${NC} to retry."
                            echo ""
                            return 1
                            ;;
                        *)
                            echo ""
                            echo -e "${YELLOW}Continuing with remaining substrates...${NC}"
                            echo ""
                            ;;
                    esac
                fi
            fi
        fi

        # Add vertical spacing after each substrate for visual isolation
        printf '\n%.0s' {1..10}
    else
        echo -e "  ${YELLOW}○${NC} ${substrate}: ${DIM}SKIPPED (no inject-substrate.sh)${NC}"
        INJECT_RESULTS="$INJECT_RESULTS$substrate:SKIPPED\n"
    fi
done

# -----------------------------------------------------------------------------
# Step 3: Generate summary report
# -----------------------------------------------------------------------------
# Breathing room before summary
printf '\n%.0s' {1..5}
echo -e "${BOLD}${BLUE}┌──────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BOLD}${BLUE}│${NC} ${BOLD}${WHITE}STEP 3:${NC} ${YELLOW}Generating summary report...${NC}                         ${BOLD}${BLUE}│${NC}"
echo -e "${BOLD}${BLUE}└──────────────────────────────────────────────────────────────┘${NC}"
python3 -c "
import sys
import json
import os
import pickle
sys.path.insert(0, '$SCRIPT_DIR')
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

spec = spec_from_loader('test_orchestrator', SourceFileLoader('test_orchestrator', '$SCRIPT_DIR/test-orchestrator.py'))
test_orch = module_from_spec(spec)
spec.loader.exec_module(test_orch)

# Load rulebook for reporting
rulebook = test_orch.load_rulebook()

# Collect grades from temp files
run_single = '$RUN_SINGLE'
if run_single:
    substrates = [run_single]
else:
    substrates = test_orch.get_substrates()

all_grades = {}
for substrate in substrates:
    grades_file = os.path.join(test_orch.SUBSTRATES_DIR, substrate, '.grades.pkl')
    if os.path.exists(grades_file):
        with open(grades_file, 'rb') as f:
            all_grades[substrate] = pickle.load(f)
        os.remove(grades_file)  # Clean up

# Generate summary report and print final table
if run_single:
    # For single substrate, just print the summary table (no full report)
    test_orch.print_final_summary_table(all_grades, rulebook)
else:
    test_orch.generate_summary_report(all_grades, rulebook)
    test_orch.print_final_summary_table(all_grades, rulebook)
"
echo ""

# -----------------------------------------------------------------------------
# Step 4: Cleanup timing-only changes before generating report
# -----------------------------------------------------------------------------
# Revert files where ONLY duration_seconds changed (no real test result changes)
# This prevents noise in git history from timing variations
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from importlib.util import spec_from_loader, module_from_spec
from importlib.machinery import SourceFileLoader

spec = spec_from_loader('test_orchestrator', SourceFileLoader('test_orchestrator', '$SCRIPT_DIR/test-orchestrator.py'))
test_orch = module_from_spec(spec)
spec.loader.exec_module(test_orch)

test_orch.cleanup_unchanged_files()
"

# -----------------------------------------------------------------------------
# Step 5: Generate HTML Report
# -----------------------------------------------------------------------------
echo -e "${BOLD}${BLUE}┌──────────────────────────────────────────────────────────────┐${NC}"
echo -e "${BOLD}${BLUE}│${NC} ${BOLD}${WHITE}STEP 5:${NC} ${YELLOW}Generating HTML report...${NC}                            ${BOLD}${BLUE}│${NC}"
echo -e "${BOLD}${BLUE}└──────────────────────────────────────────────────────────────┘${NC}"
python3 "$SCRIPT_DIR/generate-report.py"
echo ""

# -----------------------------------------------------------------------------
# Step 6: Show Failed Substrates Summary (if any)
# -----------------------------------------------------------------------------
# Trim leading space from FAILED_SUBSTRATES
FAILED_SUBSTRATES=$(echo "$FAILED_SUBSTRATES" | xargs)
FAILED_COUNT=$(echo "$FAILED_SUBSTRATES" | wc -w | tr -d ' ')

if [ -n "$FAILED_SUBSTRATES" ]; then
    printf '\n%.0s' {1..3}
    echo -e "${BOLD}${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${RED}║${NC}           ${BOLD}${WHITE}⚠️  FAILED TO EXECUTE ($FAILED_COUNT substrates)${NC}              ${BOLD}${RED}║${NC}"
    echo -e "${BOLD}${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    for failed_substrate in $FAILED_SUBSTRATES; do
        failed_upper=$(echo "$failed_substrate" | tr '[:lower:]' '[:upper:]')
        echo -e "${RED}┌──────────────────────────────────────────────────────────────┐${NC}"
        echo -e "${RED}│${NC} ${BOLD}${RED}✗ ${failed_upper}${NC} ${DIM}(FAILED TO EXECUTE)${NC}"
        echo -e "${RED}├──────────────────────────────────────────────────────────────┤${NC}"
        
        # Show the captured output (last 20 lines to keep it manageable)
        echo -e "${DIM}Output (last 20 lines):${NC}"
        if [ -f "$FAILED_OUTPUTS_DIR/$failed_substrate.txt" ]; then
            tail -20 "$FAILED_OUTPUTS_DIR/$failed_substrate.txt" | while IFS= read -r line; do
                echo -e "  ${DIM}│${NC} $line"
            done
        fi
        
        echo -e "${RED}└──────────────────────────────────────────────────────────────┘${NC}"
        echo ""
    done
    
    # List all failed substrates on one line for easy copy/paste
    echo -e "${RED}${BOLD}Failed substrates:${NC} $FAILED_SUBSTRATES"
    echo ""
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
if [ -n "$FAILED_SUBSTRATES" ]; then
    echo -e "${BOLD}${YELLOW}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${YELLOW}║${NC}         ${BOLD}${WHITE}ORCHESTRATION COMPLETE (WITH FAILURES)${NC}            ${BOLD}${YELLOW}║${NC}"
    echo -e "${BOLD}${YELLOW}╚════════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${BOLD}${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${GREEN}║${NC}              ${BOLD}${WHITE}ORCHESTRATION COMPLETE${NC}                       ${BOLD}${GREEN}║${NC}"
    echo -e "${BOLD}${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
fi
echo ""
echo -e "${CYAN}Results written to:${NC}"
if [ -n "$RUN_SINGLE" ]; then
    echo -e "  ${DIM}•${NC} Per-substrate: ${WHITE}execution-substrates/$RUN_SINGLE/test-results.md${NC}"
else
    echo -e "  ${DIM}•${NC} Per-substrate: ${WHITE}execution-substrates/*/test-results.md${NC}"
    echo -e "  ${DIM}•${NC} Summary:       ${WHITE}orchestration/all-tests-results.md${NC}"
fi
echo -e "  ${DIM}•${NC} HTML Report:   ${WHITE}orchestration/orchestration-report.html${NC}"
echo ""

# Open browser (skip in CI mode)
if ! $CI_MODE; then
    echo -e "${CYAN}Opening HTML report in browser...${NC}"
    open "$SCRIPT_DIR/orchestration-report.html"
    echo ""
fi

# Return failure status (don't exit, let caller handle)
if [ -n "$FAILED_SUBSTRATES" ]; then
    echo -e "${RED}${BOLD}⚠️  $FAILED_COUNT substrate(s) failed to execute: $FAILED_SUBSTRATES${NC}"
    return 1
fi
return 0
}

# =============================================================================
# MAIN LOOP
# =============================================================================

# CI MODE: Run all tests immediately and exit
if $CI_MODE; then
    echo ""
    echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BOLD}${CYAN}║${NC}          ${BOLD}${WHITE}EXECUTION SUBSTRATE ORCHESTRATOR${NC}                  ${BOLD}${CYAN}║${NC}"
    echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BOLD}Running in CI mode - executing all substrates...${NC}"
    run_substrates ""
    exit $?
fi

# Interactive menu loop
while true; do
    show_menu

    # Get substrates for numbered selection
    SUBSTRATES=$(ls -d "$SUBSTRATES_DIR"/*/ 2>/dev/null | xargs -n1 basename)
    SUBSTRATES_ARRAY=($SUBSTRATES)
    TOTAL_SUBSTRATES=${#SUBSTRATES_ARRAY[@]}

    read -p "Enter choice [A, V, C, P, B, D, 1-$TOTAL_SUBSTRATES, Q] (default: A): " USER_CHOICE

    # Default to 'A' if user just presses Enter
    if [ -z "$USER_CHOICE" ]; then
        USER_CHOICE="A"
    fi

    case $USER_CHOICE in
        [Aa])
            echo ""
            echo -e "${GREEN}Running ALL substrates...${NC}"
            run_substrates ""
            ;;
        [Vv])
            action_view_results
            ;;
        [Cc])
            action_clean
            ;;
        [Pp])
            action_pull_airtable
            ;;
        [Bb])
            action_change_base_id
            ;;
        [Dd])
            action_devops_menu
            ;;
        [Qq])
            echo ""
            exit 0
            ;;
        [0-9]|[0-9][0-9])
            if [ "$USER_CHOICE" -ge 1 ] && [ "$USER_CHOICE" -le "$TOTAL_SUBSTRATES" ]; then
                RUN_SINGLE="${SUBSTRATES_ARRAY[$((USER_CHOICE - 1))]}"
                echo ""
                echo -e "${GREEN}Running single substrate: ${BOLD}$RUN_SINGLE${NC}"
                run_substrates "$RUN_SINGLE"
            else
                echo ""
                echo -e "${RED}Invalid substrate number: $USER_CHOICE${NC}"
                sleep 1
            fi
            ;;
        *)
            echo ""
            echo -e "${RED}Invalid option: $USER_CHOICE${NC}"
            sleep 1
            ;;
    esac
done
