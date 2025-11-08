import os
import json
import sys
import re

# Add the project root to the sys.path to allow imports from other directories
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tech_debt_analyzer.main import tech_debt_analyzer
from tech_debt_analyzer import utils

# Define the order of quality scores from best to worst for each check.
QUALITY_RANKING = {
    "docstring_quality": ["Excellent", "Good", "Adequate", "Poor", "Missing"],
    "pydantic_usage": ["Properly Used", "Partially Used", "Not Needed", "Missing Validation", "Not Applicable"],
    "input_validation": ["Comprehensive", "Good", "Partial", "Minimal", "None"],
    "function_parameters": ["Excellent", "Good", "Fair", "Poor"],
    "implementation_status": ["Fully Implemented", "Mostly Complete", "Partially Complete", "Stub", "Not Implemented"],
    "input_normalization": ["Excellent", "Good", "Poor", "Not Applicable"]
}

def parse_changed_functions_from_diff(diff_content):
    """Parses a diff to extract file paths and the names of changed functions."""
    # Regex to find file paths (e.g., '--- a/path/to/file.py')
    file_pattern = re.compile(r'^\-\-\- a/(.+?)\s*$', re.MULTILINE)
    # Regex to find function names from hunk headers (e.g., '@@ ... @@ def function_name(...):')
    # This is a best-effort pattern and might need refinement.
    func_pattern = re.compile(r'^\@\@ .+ \@\@ .*def\s+([a-zA-Z_][a-zA-Z0-9_]*)', re.MULTILINE)
    
    file_paths = file_pattern.findall(diff_content)
    changed_funcs = {}

    if not file_paths:
        return {}

    # For simplicity, we'll assume one file per diff. A more complex diff would require more complex parsing.
    current_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', file_paths[0].strip()))
    
    func_names = func_pattern.findall(diff_content)
    if func_names:
        changed_funcs[current_file] = list(set(func_names)) # Store unique function names

    return changed_funcs

def build_tool_map():
    """Build a map from (file_path, function_name) to tool_identifier."""
    tool_map = {}
    apis_dir = os.path.join(os.path.dirname(__file__), '..', 'APIs')
    for service_name in os.listdir(apis_dir):
        if service_name == "common_utils" or not os.path.isdir(os.path.join(apis_dir, service_name)):
            continue
        
        function_map = utils.extract_function_map(os.path.join(apis_dir, service_name))
        if not function_map:
            continue

        for tool_name, module_path in function_map.items():
            path_parts = module_path.split('.')
            actual_func_name = path_parts[-1]
            file_path = os.path.abspath(os.path.join(apis_dir, service_name, *path_parts[1:-1]) + '.py')
            tool_map[(file_path, actual_func_name)] = f"{service_name}/{tool_name}"
            
    return tool_map

def main(diff_content):
    """
    Main function to validate changes based on diff content.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    thresholds_path = os.path.join(base_dir, 'tech_debt_analyzer', 'quality_thresholds.json')
    violations_path = os.path.join(base_dir, 'quality_violations.json')

    with open(thresholds_path, 'r') as f:
        thresholds = json.load(f)

    changed_funcs = parse_changed_functions_from_diff(diff_content)
    tool_map = build_tool_map()
    violations = {}
    has_violations = False

    tools_to_analyze = []
    for file_path, func_names in changed_funcs.items():
        for func_name in func_names:
            tool_identifier = tool_map.get((file_path, func_name))
            if tool_identifier:
                tools_to_analyze.append(tool_identifier)

    # Analyze all identified tools in a single batch
    for tool_identifier in set(tools_to_analyze):
        print(f"Analyzing changed tool: {tool_identifier}")
        
        # Run the analyzer directly
        results = tech_debt_analyzer(tool=tool_identifier)
        
        if "error" in results:
            print(f"  -> Analysis failed: {results['error']}")
            continue

        service_name, tool_name = tool_identifier.split('/')
        
        # The results dictionary is now structured with the tool_name as the key
        tool_results = results.get("results", {}).get(os.path.abspath(os.path.join(base_dir, 'APIs', service_name, 'mysql_handler.py')), {}).get("functions", {}).get(tool_name, {})
        # This path logic is getting complicated. Let's simplify the lookup.
        # The new analyzer returns results keyed by absolute path.
        
        # Let's find the result for our specific tool
        found_result = None
        for path_data in results.get("results", {}).values():
            if tool_name in path_data.get("functions", {}):
                found_result = path_data["functions"][tool_name]
                break
        
        if not found_result:
            print(f"  -> Could not find analysis results for tool: {tool_identifier}")
            continue

        tool_thresholds = thresholds.get(service_name, {}).get(tool_name, {})

        for check, result in found_result.items():
            if check not in tool_thresholds:
                continue

            threshold_score = tool_thresholds[check]
            actual_score = result['status']
            
            ranking = QUALITY_RANKING.get(check)
            if not ranking: continue

            if actual_score in ranking and threshold_score in ranking:
                if ranking.index(actual_score) > ranking.index(threshold_score):
                    if tool_identifier not in violations:
                        violations[tool_identifier] = []
                    violations[tool_identifier].append({
                        "check": check,
                        "threshold": threshold_score,
                        "actual": actual_score,
                        "notes": result['notes']
                    })
                    has_violations = True

    if has_violations:
        with open(violations_path, 'w') as f:
            json.dump(violations, f, indent=2)
        print("\n--- QUALITY VIOLATIONS DETECTED ---")
        print(f"Push rejected. Please review the issues in {violations_path}")
        sys.exit(1)

    print("\n--- All changed tools meet quality standards. ---")
    sys.exit(0)

if __name__ == "__main__":
    # This script now expects the diff content to be piped to it
    # e.g., git diff | python DevScripts/validate_changes.py
    # Or for the debugger, it will read from diff.txt
    
    diff_file_path = os.path.join(os.path.dirname(__file__), '..', 'diff.txt')
    try:
        with open(diff_file_path, 'r') as f:
            diff_content = f.read()
        main(diff_content)
    except FileNotFoundError:
        print(f"Error: For debugging, a 'diff.txt' file is expected at the project root.")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)