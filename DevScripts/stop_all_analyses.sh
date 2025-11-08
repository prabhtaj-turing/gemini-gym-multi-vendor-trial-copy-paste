#!/bin/bash

# --- Stop All Tech Debt Analyses ---
# This script finds and terminates all running instances of the
# tech debt analyzer script (main.py).

echo "--- Stopping all running analysis processes ---"

# Find all process IDs (PIDs) for the analyzer script
PIDS=$(pgrep -f "tech_debt_analyzer/main.py")

if [ -z "$PIDS" ]; then
    echo "No running analysis processes found."
    exit 0
fi

# Terminate each process
for PID in $PIDS; do
    echo "Stopping process with PID: $PID"
    kill -9 "$PID"
done

echo "--- All analysis processes have been terminated. ---"
