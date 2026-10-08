#!/bin/bash
set -e
PROJECT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$PROJECT_DIR"
if [ ! -x "$PROJECT_DIR/.venv/bin/python" ]; then
    /bin/bash "$PROJECT_DIR/Setup-Mac.command"
fi
exec "$PROJECT_DIR/.venv/bin/python" "$PROJECT_DIR/run.py" "$@"
