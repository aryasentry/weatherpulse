#!/bin/bash
set -e
PROJECT_DIR="$(cd -- "$(dirname -- "$0")" && pwd)"
cd "$PROJECT_DIR"
for candidate in python3.13 python3.12 python3.11 python3; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info[0] == 3 and 11 <= sys.version_info[1] <= 13 else 1)' >/dev/null 2>&1; then
        exec "$candidate" "$PROJECT_DIR/setup.py"
    fi
done
echo "Python 3.11, 3.12 or 3.13 was not found."
echo "Install a supported version from https://www.python.org/downloads/macos/ and retry."
exit 1
