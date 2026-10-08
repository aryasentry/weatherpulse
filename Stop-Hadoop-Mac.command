#!/bin/zsh
set -e
cd "${0:A:h}"
TASK_PYTHON=".venv/bin/python"
if [[ ! -x "$TASK_PYTHON" ]]; then TASK_PYTHON="python3"; fi
"$TASK_PYTHON" scripts/hadoop_native.py stop
