#!/bin/bash

# --- Docstring vs. Schema Analysis Orchestrator ---
# This script runs the 'docstring_v_schema' check for all services and
# saves the output for each service to a separate log file.

echo "--- Launching Docstring vs. Schema Analysis ---"

# Set the Gemini API Key here before running the script
export GEMINI_API_KEY="AIzaSyCkQFuIGGpONvrg1FEF8_mvdWzw9TYClr8"

# Get the absolute path to the project root directory
BASE_DIR=$(git rev-parse --show-toplevel)

# Verify that the key has been set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: GEMINI_API_KEY is not set in the script."
    echo "Please edit DevScripts/run_docstring_schema_analysis.sh and add your key."
    exit 1
fi

ANALYZER_DIR="$BASE_DIR/tech_debt_analyzer"
APIS_DIR="$BASE_DIR/APIs"
RESULTS_DIR="$ANALYZER_DIR/results/docstring_v_schema"
LOGS_DIR="$ANALYZER_DIR/logs"

# Create the results and logs directories if they don't exist
mkdir -p "$RESULTS_DIR"
mkdir -p "$LOGS_DIR"

# Loop through all directories in the APIs folder
for service in "$APIS_DIR"/*; do
    if [ -d "$service" ]; then
        service_name=$(basename "$service")

        # Skip the common_utils and __pycache__ directories
        if [ "$service_name" == "common_utils" ] || [ "$service_name" == "__pycache__" ]; then
            continue
        fi
        
        # Define the output and log file paths
        output_file="$RESULTS_DIR/${service_name}_results.json"
        log_file="$LOGS_DIR/${service_name}_docstring_v_schema.log"

        echo "Launching analysis for service: $service_name -> See log at $log_file"
        
        # Run the analyzer for the current service as a detached background process
        nohup python3 "$ANALYZER_DIR/main.py" --services "$service_name" --checks docstring_v_schema --output "$output_file" > "$log_file" 2>&1 &
    fi
done

echo ""
echo "--- All analysis processes have been launched in the background. ---"
echo "You can monitor their progress in the respective log files in the '$LOGS_DIR' directory."
echo "Once all processes are complete, run the 'consolidate_schema_mismatches.py' script to get the final report."
