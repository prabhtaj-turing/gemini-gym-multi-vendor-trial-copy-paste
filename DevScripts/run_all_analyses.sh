#!/bin/bash

# --- Docstring Quality Analysis Orchestrator ---
# This script runs the tech debt analyzer for all services as detached
# background processes, saving the output for each service to a log file.

echo "--- Launching Detached Docstring Quality Analyses ---"

# Set the Gemini API Key here before running the script
export GEMINI_API_KEY="AIzaSyCkQFuIGGpONvrg1FEF8_mvdWzw9TYClr8"

# Get the absolute path to the project root directory
BASE_DIR=$(git rev-parse --show-toplevel)

# Verify that the key has been set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: GEMINI_API_KEY is not set in the script."
    echo "Please edit DevScripts/run_all_analyses.sh and add your key."
    exit 1
fi

ANALYZER_DIR="$BASE_DIR/tech_debt_analyzer"
APIS_DIR="$BASE_DIR/APIs"
RESULTS_DIR="$ANALYZER_DIR/results"
LOGS_DIR="$ANALYZER_DIR/logs"

# Create the results and logs directories if they don't exist
mkdir -p "$RESULTS_DIR"
mkdir -p "$LOGS_DIR"

# Loop through all directories in the APIs folder
for service in "$APIS_DIR"/*; do
    if [ -d "$service" ]; then
        service_name=$(basename "$service")

        # Skip the common_utils directory
        if [ "$service_name" == "common_utils" ]; then
            continue
        fi
        
        # Define the output and log file paths
        output_file="$RESULTS_DIR/${service_name}_docstring_results.json"
        log_file="$LOGS_DIR/${service_name}_docstring.log"

        echo "Launching docstring analysis for service: $service_name -> See log at $log_file"
        
        # Run the analyzer for the current service as a detached background process
        nohup python3 "$ANALYZER_DIR/main.py" --services "$service_name" --checks docstring_quality --output "$output_file" > "$log_file" 2>&1 &
    fi
done

echo ""
echo "--- All docstring analysis processes have been launched in the background. ---"
echo "You can monitor their progress in the respective log files in the '$LOGS_DIR' directory."
