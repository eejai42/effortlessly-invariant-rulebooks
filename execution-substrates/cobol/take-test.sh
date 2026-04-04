#!/bin/bash
set -e
set -o pipefail

# take-test.sh for COBOL execution substrate
# Produces test-answers using the shared Python erb_calc (same logic as generated COBOL)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOG_FILE="$SCRIPT_DIR/.last-run.log"
cd "$SCRIPT_DIR"

{
    echo "=== COBOL Substrate Test Run ==="
    echo ""

    if [[ ! -f "../python/erb_calc.py" ]]; then
        echo "FATAL: ../python/erb_calc.py not found. Run inject-substrate.sh first." >&2
        exit 1
    fi

    mkdir -p "$SCRIPT_DIR/test-answers"
    echo "cobol: Producing test-answers via Python erb_calc (same logic as generated COBOL)..."
    python3 "$SCRIPT_DIR/take-test.py"
    echo ""
} 2>&1 | tee "$LOG_FILE"

echo "cobol: test completed successfully"

# Generate substrate report
python3 "$PROJECT_ROOT/orchestration/create-substrate-report.py" cobol --log "$LOG_FILE"
