#!/usr/bin/env bash
# Build and install the Tracker Quick Capture Alfred workflow.
# Usage: ./install.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKFLOW_FILE="$SCRIPT_DIR/tracker-capture.alfredworkflow"

# Package as .alfredworkflow (a zip archive)
cd "$SCRIPT_DIR"
zip -j "$WORKFLOW_FILE" info.plist

echo "Built: $WORKFLOW_FILE"
echo "Double-click to import into Alfred, or run:"
echo "  open \"$WORKFLOW_FILE\""

# Auto-open if Alfred is running
if pgrep -q "Alfred"; then
    open "$WORKFLOW_FILE"
fi
