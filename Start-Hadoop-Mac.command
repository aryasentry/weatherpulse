#!/bin/zsh
set -e
cd "${0:A:h}"
TASK_PYTHON=".venv/bin/python"
if [[ ! -x "$TASK_PYTHON" ]]; then
  print "Run Setup-Mac.command first to create the project Python environment."
  exit 1
fi
"$TASK_PYTHON" scripts/setup_hadoop.py
"$TASK_PYTHON" scripts/hadoop_native.py run
print "Hadoop verification complete. NameNode: http://127.0.0.1:19870"
print "Use Stop-Hadoop-Mac.command when finished; HDFS storage will be retained."
