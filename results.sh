#!/bin/bash
# Opens the orchestration report in the default browser

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
open "$SCRIPT_DIR/orchestration/orchestration-report.html"
