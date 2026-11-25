#!/bin/bash
# PostToolUse hook: after Claude edits or writes a Python file, format and auto-fix it with ruff.
# Never blocks: formatting problems are fixed silently, remaining lint issues are reported by tests/CI.
INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | uv run --quiet python -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null)
case "$FILE" in
  *.py)
    cd "$CLAUDE_PROJECT_DIR" || exit 0
    uv run --quiet ruff check --fix --quiet "$FILE" >/dev/null 2>&1
    uv run --quiet ruff format --quiet "$FILE" >/dev/null 2>&1
    ;;
esac
exit 0
