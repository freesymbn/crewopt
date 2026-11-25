#!/bin/bash
# Stop hook: before Claude finishes a turn, run the test suite.
# If tests fail, exit 2 sends the failure output back to Claude so it keeps working on a fix.
INPUT=$(cat)
ACTIVE=$(printf '%s' "$INPUT" | uv run --quiet python -c 'import json,sys; print(str(json.load(sys.stdin).get("stop_hook_active", False)).lower())' 2>/dev/null)
if [ "$ACTIVE" = "true" ]; then
  exit 0  # already continued once because of this hook; let Claude stop to avoid loops
fi
cd "$CLAUDE_PROJECT_DIR" || exit 0
OUTPUT=$(uv run --quiet pytest -q 2>&1)
if [ $? -ne 0 ]; then
  echo "Tests are failing. Fix them before finishing (constitution principle II):" >&2
  echo "$OUTPUT" | tail -40 >&2
  exit 2
fi
exit 0
