#!/bin/bash

# --- Single Tool Schema Validator ---
# This script regenerates the schema for a specific service and then runs the
# docstring_v_schema check for a single tool within that service.

# --- Argument Validation ---
if [ -z "$1" ]; then
    echo "Error: Missing argument. Please provide the tool in 'service/tool' format."
    echo "Example: ./DevScripts/validate_tool_schema.sh mysql/query"
    exit 1
fi

if ! [[ "$1" =~ \/ ]]; then
    echo "Error: Invalid argument format. Please use 'service/tool'."
    echo "Example: ./DevScripts/validate_tool_schema.sh mysql/query"
    exit 1
fi

# --- Environment Setup ---
TOOL_FULL_PATH=$1
SERVICE_NAME=$(echo "$TOOL_FULL_PATH" | cut -d'/' -f1)
TOOL_NAME=$(echo "$TOOL_FULL_PATH" | cut -d'/' -f2)

echo "--- Validating: $TOOL_FULL_PATH ---"

# Set the Gemini API Key here before running the script
export GEMINI_API_KEY="AIzaSyCkQFuIGGpONvrg1FEF8_mvdWzw9TYClr8"

# Get the absolute path to the project root directory
BASE_DIR=$(git rev-parse --show-toplevel)

# Verify that the key has been set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: GEMINI_API_KEY is not set in the script."
    echo "Please edit this script and add your key."
    exit 1
fi

ANALYZER_DIR="$BASE_DIR/tech_debt_analyzer"
DEV_SCRIPTS_DIR="$BASE_DIR/DevScripts"
RESULTS_DIR="$ANALYZER_DIR/results"
OUTPUT_FILE="$RESULTS_DIR/${SERVICE_NAME}_${TOOL_NAME}_validation.json"

# Create the results directory if it doesn't exist
mkdir -p "$RESULTS_DIR"

# --- Step 1: Regenerate Schema for the Service ---
echo ""
echo "--- Step 1: Regenerating schema for service '$SERVICE_NAME'... ---"
python3 "$DEV_SCRIPTS_DIR/generate_schemas.py" --service "$SERVICE_NAME"
if [ $? -ne 0 ]; then
    echo "Error: Schema generation failed for service '$SERVICE_NAME'. Aborting."
    exit 1
fi
echo "Schema regeneration complete."

# --- Step 2: Run Tech Debt Analyzer for the Specific Tool ---
echo ""
echo "--- Step 2: Running docstring vs. schema analysis for tool '$TOOL_NAME'... ---"
python3 "$ANALYZER_DIR/main.py" \
    --tool "$TOOL_FULL_PATH" \
    --checks docstring_v_schema \
    --output "$OUTPUT_FILE"
if [ $? -ne 0 ]; then
    echo "Error: Tech debt analysis failed for tool '$TOOL_FULL_PATH'. Aborting."
    exit 1
fi
echo "Analysis complete."

# --- Step 3: Display Results ---
echo ""
echo "--- Step 3: Analysis Results ---"
if [ -f "$OUTPUT_FILE" ]; then
    cat "$OUTPUT_FILE"
else
    echo "Error: Output file not found at '$OUTPUT_FILE'."
    exit 1
fi

echo ""
echo "--- Validation Complete ---"
