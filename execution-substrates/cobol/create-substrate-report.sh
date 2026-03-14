#!/bin/bash
# create-substrate-report.sh - Generate substrate-report.html for COBOL substrate

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$SCRIPT_DIR"

python3 "$PROJECT_ROOT/orchestration/create-substrate-report.py" cobol --log "$SCRIPT_DIR/.last-run.log"
