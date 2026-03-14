#!/bin/bash
# =============================================================================
# RUN-IN-DOCKER.SH
# =============================================================================
# Launcher script for running ERB in Docker.
# Builds the image, starts PostgreSQL, and runs the orchestration.
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# =============================================================================
# Colors
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# =============================================================================
# .env file path
# =============================================================================
ENV_FILE="$SCRIPT_DIR/.env"
ENV_EXAMPLE="$SCRIPT_DIR/.env.example"

# =============================================================================
# Functions
# =============================================================================
print_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                              ║"
    echo "║   ███████╗██████╗ ██████╗     ██████╗  ██████╗  ██████╗██╗  ██╗███████╗██████╗║"
    echo "║   ██╔════╝██╔══██╗██╔══██╗    ██╔══██╗██╔═══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██║"
    echo "║   █████╗  ██████╔╝██████╔╝    ██║  ██║██║   ██║██║     █████╔╝ █████╗  ██████╔╝║"
    echo "║   ██╔══╝  ██╔══██╗██╔══██╗    ██║  ██║██║   ██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗║"
    echo "║   ███████╗██║  ██║██████╔╝    ██████╔╝╚██████╔╝╚██████╗██║  ██╗███████╗██║  ██║║"
    echo "║   ╚══════╝╚═╝  ╚═╝╚═════╝     ╚═════╝  ╚═════╝  ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝║"
    echo "║                                                                              ║"
    echo "║              Effortlessly Invariant Rulesbooks - Docker Mode                 ║"
    echo "║                                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

show_help() {
    echo -e "${BOLD}Usage:${NC} ./run-in-docker.sh [COMMAND]"
    echo ""
    echo -e "${BOLD}Commands:${NC}"
    echo "  start       Build and start the ERB stack (default)"
    echo "  run         Run all substrates non-interactively (CI mode)"
    echo "  shell       Open an interactive shell in the ERB container"
    echo "  orchestrate Run the orchestration menu"
    echo "  build       Build/rebuild the Docker images"
    echo "  stop        Stop all containers"
    echo "  down        Stop and remove containers, networks"
    echo "  clean       Remove containers, volumes, and images"
    echo "  logs        Show container logs"
    echo "  status      Show container status"
    echo "  psql        Connect to PostgreSQL"
    echo "  setup       Configure API keys (creates .env file)"
    echo "  env         Show current environment configuration"
    echo "  help        Show this help message"
    echo ""
    echo -e "${BOLD}Examples:${NC}"
    echo "  ./run-in-docker.sh              # Start the stack and run orchestration"
    echo "  ./run-in-docker.sh run          # Run all substrates (CI mode)"
    echo "  ./run-in-docker.sh setup        # Configure API keys"
    echo "  ./run-in-docker.sh shell        # Get a shell in the container"
    echo ""
    echo -e "${BOLD}Environment Variables:${NC}"
    echo "  AIRTABLE_API_KEY    For pulling fresh data from Airtable (optional)"
    echo "  OPENAI_API_KEY      For English substrate LLM generation (optional)"
    echo "  ANTHROPIC_API_KEY   Alternative LLM provider (optional)"
    echo ""
    echo -e "${BOLD}Offline Mode:${NC}"
    echo "  Without API keys, the system uses cached data shipped with the repo."
    echo "  All substrates except English (which needs LLM) work fully offline."
}

# =============================================================================
# Environment/Setup Functions
# =============================================================================
show_env_status() {
    echo ""
    echo -e "${BOLD}Environment Configuration${NC}"
    echo -e "${DIM}══════════════════════════════════════════════════════════════${NC}"
    echo ""

    # Check .env file
    if [ -f "$ENV_FILE" ]; then
        echo -e "  ${GREEN}[OK]${NC} .env file exists"
        # Source it to show status
        set -a
        source "$ENV_FILE" 2>/dev/null || true
        set +a
    else
        echo -e "  ${DIM}[--]${NC} No .env file (using host environment only)"
    fi
    echo ""

    # Show API key status
    echo -e "${BOLD}API Keys:${NC}"

    if [ -n "$AIRTABLE_API_KEY" ]; then
        local masked="${AIRTABLE_API_KEY:0:8}...${AIRTABLE_API_KEY: -4}"
        echo -e "  ${GREEN}[OK]${NC} AIRTABLE_API_KEY: $masked"
    else
        echo -e "  ${DIM}[--]${NC} AIRTABLE_API_KEY: ${DIM}not set (will use cached data)${NC}"
    fi

    if [ -n "$OPENAI_API_KEY" ]; then
        local masked="${OPENAI_API_KEY:0:8}...${OPENAI_API_KEY: -4}"
        echo -e "  ${GREEN}[OK]${NC} OPENAI_API_KEY: $masked"
    else
        echo -e "  ${DIM}[--]${NC} OPENAI_API_KEY: ${DIM}not set (English substrate will use cache)${NC}"
    fi

    if [ -n "$ANTHROPIC_API_KEY" ]; then
        local masked="${ANTHROPIC_API_KEY:0:8}...${ANTHROPIC_API_KEY: -4}"
        echo -e "  ${GREEN}[OK]${NC} ANTHROPIC_API_KEY: $masked"
    else
        echo -e "  ${DIM}[--]${NC} ANTHROPIC_API_KEY: ${DIM}not set${NC}"
    fi

    echo ""
    echo -e "${BOLD}LLM Configuration:${NC}"
    echo -e "  LLM_PROVIDER: ${LLM_PROVIDER:-openai}"
    echo -e "  LLM_TIER: ${LLM_TIER:-medium}"
    echo ""
}

setup_env() {
    echo ""
    echo -e "${BOLD}${CYAN}ERB Environment Setup${NC}"
    echo -e "${DIM}══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "This will create a .env file with your API keys."
    echo "API keys are OPTIONAL - without them, the system uses cached data."
    echo ""

    # Check if .env already exists
    if [ -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}A .env file already exists.${NC}"
        read -p "Overwrite it? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Setup cancelled."
            return
        fi
    fi

    # Start building .env content
    ENV_CONTENT="# ERB Environment Configuration
# Generated by ./run-in-docker.sh setup
# See .env.example for documentation

"

    # Airtable API Key
    echo ""
    echo -e "${BOLD}1. Airtable API Key${NC}"
    echo "   Used for: Pulling fresh data from Airtable bases"
    echo "   Get one at: https://airtable.com/create/tokens"
    echo ""

    # Check if already set in environment
    if [ -n "$AIRTABLE_API_KEY" ]; then
        local masked="${AIRTABLE_API_KEY:0:8}...${AIRTABLE_API_KEY: -4}"
        echo "   Current value from environment: $masked"
        read -p "   Use this value? (Y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            ENV_CONTENT+="AIRTABLE_API_KEY=$AIRTABLE_API_KEY
"
        else
            read -p "   Enter Airtable API Key (or press Enter to skip): " AIRTABLE_KEY
            if [ -n "$AIRTABLE_KEY" ]; then
                ENV_CONTENT+="AIRTABLE_API_KEY=$AIRTABLE_KEY
"
            fi
        fi
    else
        read -p "   Enter Airtable API Key (or press Enter to skip): " AIRTABLE_KEY
        if [ -n "$AIRTABLE_KEY" ]; then
            ENV_CONTENT+="AIRTABLE_API_KEY=$AIRTABLE_KEY
"
        fi
    fi

    # OpenAI API Key
    echo ""
    echo -e "${BOLD}2. OpenAI API Key${NC}"
    echo "   Used for: English substrate LLM generation"
    echo "   Get one at: https://platform.openai.com/api-keys"
    echo ""

    if [ -n "$OPENAI_API_KEY" ]; then
        local masked="${OPENAI_API_KEY:0:8}...${OPENAI_API_KEY: -4}"
        echo "   Current value from environment: $masked"
        read -p "   Use this value? (Y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            ENV_CONTENT+="OPENAI_API_KEY=$OPENAI_API_KEY
"
        else
            read -p "   Enter OpenAI API Key (or press Enter to skip): " OPENAI_KEY
            if [ -n "$OPENAI_KEY" ]; then
                ENV_CONTENT+="OPENAI_API_KEY=$OPENAI_KEY
"
            fi
        fi
    else
        read -p "   Enter OpenAI API Key (or press Enter to skip): " OPENAI_KEY
        if [ -n "$OPENAI_KEY" ]; then
            ENV_CONTENT+="OPENAI_API_KEY=$OPENAI_KEY
"
        fi
    fi

    # Optional: Anthropic API Key
    echo ""
    echo -e "${BOLD}3. Anthropic API Key (optional alternative to OpenAI)${NC}"
    echo "   Used for: English substrate with Claude models"
    echo "   Get one at: https://console.anthropic.com/"
    echo ""

    read -p "   Enter Anthropic API Key (or press Enter to skip): " ANTHROPIC_KEY
    if [ -n "$ANTHROPIC_KEY" ]; then
        ENV_CONTENT+="ANTHROPIC_API_KEY=$ANTHROPIC_KEY
LLM_PROVIDER=anthropic
"
    fi

    # Write the .env file
    echo "$ENV_CONTENT" > "$ENV_FILE"

    echo ""
    echo -e "${GREEN}Setup complete!${NC}"
    echo "Created: $ENV_FILE"
    echo ""
    echo "Run './run-in-docker.sh env' to verify your configuration."
    echo "Run './run-in-docker.sh start' to start ERB with your settings."
    echo ""
}

run_all_substrates() {
    echo -e "${BLUE}Running all substrates (non-interactive mode)...${NC}"
    docker compose run --rm erb bash orchestration/orchestrate.sh --docker
}

# =============================================================================
# First-Run Auto-Setup
# =============================================================================
check_first_run() {
    # If .env exists, we're good - just continue
    if [ -f "$ENV_FILE" ]; then
        return 0
    fi

    # First run - check if API keys are already in the environment
    local has_airtable_env=false
    local has_openai_env=false

    if [ -n "$AIRTABLE_API_KEY" ]; then
        has_airtable_env=true
    fi
    if [ -n "$OPENAI_API_KEY" ]; then
        has_openai_env=true
    fi

    # Start with .env.example as base (or empty if not found)
    if [ -f "$ENV_EXAMPLE" ]; then
        cp "$ENV_EXAMPLE" "$ENV_FILE"
    else
        touch "$ENV_FILE"
    fi

    # If both keys are already in environment, auto-configure without prompting
    if $has_airtable_env && $has_openai_env; then
        echo ""
        echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
        echo -e "${CYAN}${BOLD}  First Run - Auto-configuring from environment${NC}"
        echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
        echo ""

        # Add both keys to .env
        grep -v "^AIRTABLE_API_KEY=" "$ENV_FILE" > "$ENV_FILE.tmp" 2>/dev/null || true
        echo "AIRTABLE_API_KEY=$AIRTABLE_API_KEY" >> "$ENV_FILE.tmp"
        mv "$ENV_FILE.tmp" "$ENV_FILE"

        grep -v "^OPENAI_API_KEY=" "$ENV_FILE" > "$ENV_FILE.tmp" 2>/dev/null || true
        echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> "$ENV_FILE.tmp"
        mv "$ENV_FILE.tmp" "$ENV_FILE"

        local masked_airtable="${AIRTABLE_API_KEY:0:8}...${AIRTABLE_API_KEY: -4}"
        local masked_openai="${OPENAI_API_KEY:0:8}...${OPENAI_API_KEY: -4}"
        echo -e "  ${GREEN}[OK]${NC} AIRTABLE_API_KEY: $masked_airtable (from environment)"
        echo -e "  ${GREEN}[OK]${NC} OPENAI_API_KEY: $masked_openai (from environment)"
        echo ""
        echo -e "  ${GREEN}Setup complete!${NC} Configuration saved to .env"
        echo -e "  ${DIM}Run './run-in-docker.sh setup' anytime to reconfigure.${NC}"
        echo ""

        # Reload the .env we just created
        set -a
        source "$ENV_FILE" 2>/dev/null || true
        set +a
        return 0
    fi

    # Not all keys in environment - show setup prompt
    echo ""
    echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}${BOLD}  First Run Detected - Environment Setup${NC}"
    echo -e "${CYAN}${BOLD}════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  Created ${GREEN}.env${NC} from .env.example"
    echo ""
    echo -e "  ${BOLD}API keys are optional${NC} - the system uses cached data when not set."
    echo -e "  However, some features require API keys:"
    echo ""
    echo -e "    ${CYAN}AIRTABLE_API_KEY${NC}  - Pull fresh data from Airtable bases"
    echo -e "    ${CYAN}OPENAI_API_KEY${NC}    - Generate English specifications via LLM"
    echo ""

    # Auto-save any keys already in environment
    if $has_airtable_env; then
        grep -v "^AIRTABLE_API_KEY=" "$ENV_FILE" > "$ENV_FILE.tmp" 2>/dev/null || true
        echo "AIRTABLE_API_KEY=$AIRTABLE_API_KEY" >> "$ENV_FILE.tmp"
        mv "$ENV_FILE.tmp" "$ENV_FILE"
        local masked="${AIRTABLE_API_KEY:0:8}...${AIRTABLE_API_KEY: -4}"
        echo -e "  ${GREEN}[OK]${NC} AIRTABLE_API_KEY: $masked (from environment)"
    fi
    if $has_openai_env; then
        grep -v "^OPENAI_API_KEY=" "$ENV_FILE" > "$ENV_FILE.tmp" 2>/dev/null || true
        echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> "$ENV_FILE.tmp"
        mv "$ENV_FILE.tmp" "$ENV_FILE"
        local masked="${OPENAI_API_KEY:0:8}...${OPENAI_API_KEY: -4}"
        echo -e "  ${GREEN}[OK]${NC} OPENAI_API_KEY: $masked (from environment)"
    fi

    # Only prompt for missing keys
    local missing_keys=false
    if ! $has_airtable_env || ! $has_openai_env; then
        missing_keys=true
    fi

    if $missing_keys; then
        read -p "  Would you like to configure missing API keys now? (y/N) " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo ""

            # Airtable API Key (only if not in environment)
            if ! $has_airtable_env; then
                echo -e "  ${BOLD}Airtable API Key${NC} (https://airtable.com/create/tokens)"
                read -p "  Enter key (or press Enter to skip): " AIRTABLE_INPUT
                if [ -n "$AIRTABLE_INPUT" ]; then
                    grep -v "^AIRTABLE_API_KEY=" "$ENV_FILE" > "$ENV_FILE.tmp" 2>/dev/null || true
                    echo "AIRTABLE_API_KEY=$AIRTABLE_INPUT" >> "$ENV_FILE.tmp"
                    mv "$ENV_FILE.tmp" "$ENV_FILE"
                    echo -e "  ${GREEN}Saved!${NC}"
                else
                    echo -e "  ${DIM}Skipped - will use cached data${NC}"
                fi
                echo ""
            fi

            # OpenAI API Key (only if not in environment)
            if ! $has_openai_env; then
                echo -e "  ${BOLD}OpenAI API Key${NC} (https://platform.openai.com/api-keys)"
                read -p "  Enter key (or press Enter to skip): " OPENAI_INPUT
                if [ -n "$OPENAI_INPUT" ]; then
                    grep -v "^OPENAI_API_KEY=" "$ENV_FILE" > "$ENV_FILE.tmp" 2>/dev/null || true
                    echo "OPENAI_API_KEY=$OPENAI_INPUT" >> "$ENV_FILE.tmp"
                    mv "$ENV_FILE.tmp" "$ENV_FILE"
                    echo -e "  ${GREEN}Saved!${NC}"
                else
                    echo -e "  ${DIM}Skipped - will use cached English specs${NC}"
                fi
            fi
        fi
    fi

    echo ""
    echo -e "  ${GREEN}Setup complete!${NC} Configuration saved to .env"
    echo -e "  ${DIM}Run './run-in-docker.sh setup' anytime to reconfigure.${NC}"
    echo ""

    # Reload the .env we just created
    set -a
    source "$ENV_FILE" 2>/dev/null || true
    set +a
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
        exit 1
    fi
    if ! docker info &> /dev/null; then
        echo -e "${RED}Error: Docker daemon is not running${NC}"
        exit 1
    fi
}

build_images() {
    echo -e "${BLUE}Building Docker images...${NC}"
    docker compose build
    echo -e "${GREEN}Build complete!${NC}"
}

start_services() {
    echo -e "${BLUE}Starting services...${NC}"
    docker compose up -d postgres
    echo -e "${YELLOW}Waiting for PostgreSQL to be ready...${NC}"

    # Wait for postgres with a timeout
    local timeout=60
    local count=0
    while ! docker compose exec -T postgres pg_isready -U postgres &>/dev/null; do
        count=$((count + 1))
        if [ $count -ge $timeout ]; then
            echo -e "${RED}Timeout waiting for PostgreSQL${NC}"
            exit 1
        fi
        sleep 1
    done

    echo -e "${GREEN}PostgreSQL is ready!${NC}"
}

run_orchestration() {
    echo -e "${BLUE}Starting ERB orchestration...${NC}"
    docker compose run --rm -e ERB_DOCKER_MODE=false erb bash orchestration/orchestrate.sh
}

open_shell() {
    echo -e "${BLUE}Opening shell in ERB container...${NC}"
    docker compose run --rm erb bash
}

connect_psql() {
    echo -e "${BLUE}Connecting to PostgreSQL...${NC}"
    docker compose exec postgres psql -U postgres -d erb
}

show_logs() {
    docker compose logs -f
}

show_status() {
    echo -e "${BOLD}Container Status:${NC}"
    docker compose ps
    echo ""
    echo -e "${BOLD}Volumes:${NC}"
    docker volume ls | grep erb || echo "  (no ERB volumes found)"
}

stop_services() {
    echo -e "${YELLOW}Stopping services...${NC}"
    docker compose stop
    echo -e "${GREEN}Services stopped${NC}"
}

down_services() {
    echo -e "${YELLOW}Stopping and removing containers...${NC}"
    docker compose down
    echo -e "${GREEN}Done${NC}"
}

clean_all() {
    echo -e "${RED}${BOLD}WARNING: This will remove all containers, volumes, and images!${NC}"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker compose down -v --rmi local
        echo -e "${GREEN}Cleaned up${NC}"
    else
        echo "Cancelled"
    fi
}

# =============================================================================
# Main
# =============================================================================
print_banner
check_docker

COMMAND="${1:-start}"

# Load .env file if it exists
if [ -f "$ENV_FILE" ]; then
    set -a
    source "$ENV_FILE" 2>/dev/null || true
    set +a
fi

# Auto-setup on first run (for start/run commands that need Docker)
case "$COMMAND" in
    start|run|orchestrate)
        check_first_run
        ;;
esac

case "$COMMAND" in
    start)
        build_images
        start_services
        run_orchestration
        ;;
    run)
        build_images
        start_services
        run_all_substrates
        ;;
    shell)
        start_services
        open_shell
        ;;
    orchestrate)
        start_services
        run_orchestration
        ;;
    build)
        build_images
        ;;
    stop)
        stop_services
        ;;
    down)
        down_services
        ;;
    clean)
        clean_all
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    psql)
        start_services
        connect_psql
        ;;
    setup)
        setup_env
        ;;
    env)
        show_env_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
