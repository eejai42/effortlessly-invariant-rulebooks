#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Regenerate Python erb_calc.py (used by take-test to produce test-answers)
echo "=== Regenerating shared erb_calc.py from rulebook ==="
python3 "$SCRIPT_DIR/../python/inject-into-python.py"

# Regenerate COBOL from rulebook
echo "=== Regenerating COBOL from rulebook ==="
python3 inject-into-cobol.py

# Run the test for this substrate (uses Python erb_calc to produce test-answers)
"$SCRIPT_DIR/take-test.sh"
