import os
import json
import sys

# Add the parent directory to the sys.path to allow imports from there
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tech_debt_analyzer import utils

def generate_thresholds():
    """
    Generates a JSON file with quality thresholds for all tools.
    """
    # This map defines the highest possible score for each check.
    # The order of categories in analyzer.py is from best to worst.
    threshold_map = {
        "docstring_quality": "Excellent",
        "pydantic_usage": "Properly Used",
        "input_validation": "Comprehensive",
        "function_parameters": "Excellent",
        "implementation_status": "Fully Implemented",
        "input_normalization": "Excellent",
        "project_structure": "Complete"
    }

    all_thresholds = {}
    apis_dir = os.path.join(os.path.dirname(__file__), '..', 'APIs')
    
    for service_name in os.listdir(apis_dir):
        if service_name == "common_utils" or not os.path.isdir(os.path.join(apis_dir, service_name)):
            continue

        service_path = os.path.join(apis_dir, service_name)
        function_map = utils.extract_function_map(service_path)
        
        if not function_map:
            continue

        all_thresholds[service_name] = {}
        for tool_name in function_map.keys():
            all_thresholds[service_name][tool_name] = threshold_map

    output_path = os.path.join(os.path.dirname(__file__), '..', 'tech_debt_analyzer', 'quality_thresholds.json')
    with open(output_path, 'w') as f:
        json.dump(all_thresholds, f, indent=2)

    print(f"Successfully generated quality thresholds at: {output_path}")

if __name__ == "__main__":
    generate_thresholds()
