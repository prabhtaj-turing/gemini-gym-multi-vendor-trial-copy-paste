#!/usr/bin/env bash

# Ensure pytest-timeout is installed
if ! python -c "import pytest_timeout" 2>/dev/null; then
    echo "⏳ Installing pytest-timeout..."
    pip install pytest-timeout
fi


export GEMINI_API_KEY=""
export GOOGLE_API_KEY=""

echo "📁 Listing API folders using: ls -d APIs/*/"
folders=$(ls -d APIs/*/ 2>/dev/null | grep -v '__pycache__/')

if [ -z "$folders" ]; then
    echo "❗ No subdirectories found in APIs/"
    exit 1
fi

echo "📂 Found folders:"
echo "$folders"
echo

PASSED=()
FAILED=()

for dir in $folders; do
    # Skip __pycache__ just in case
    if [[ "$dir" == *"__pycache__"* ]]; then
        echo "⚠️  Skipping '$dir' (__pycache__ directory)"
        continue
    fi

    echo "--------------------------------------------------"
    echo "🔍 Running tests in '$dir' (per-test timeout: 20s)"

    if [ ! -d "$dir" ]; then
        echo "⚠️  Skipping '$dir' (not a directory)"
        continue
    fi

    # Run pytest with per-test timeout using pytest-timeout
    pytest "$dir" -p no:warnings --timeout=20
    exit_code=$?
    echo "📦 Exit code for $dir: $exit_code"

    if [ $exit_code -eq 0 ]; then
        PASSED+=("$dir")
    else
        FAILED+=("$dir ❌ FAILED (exit code $exit_code)")
    fi
done

echo
echo "📋 Test Summary:"
for dir in "${PASSED[@]}"; do
    echo "$dir: ✅ PASSED"
done
for dir in "${FAILED[@]}"; do
    echo "$dir"
done