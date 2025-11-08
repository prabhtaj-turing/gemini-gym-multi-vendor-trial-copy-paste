import os
import json
import csv
import sys

def build_consolidated_function_map(base_dir):
    """
    Builds a consolidated map of all function maps from all services.
    The structure is: {service_name: {tool_name: actual_function_name}}
    """
    consolidated_map = {}
    apis_dir = os.path.join(base_dir, 'APIs')
    
    # Dynamically import the utils module
    sys.path.insert(0, os.path.join(base_dir, 'tech_debt_analyzer'))
    import utils

    for service_name in os.listdir(apis_dir):
        if service_name == "common_utils" or not os.path.isdir(os.path.join(apis_dir, service_name)):
            continue
        
        service_path = os.path.join(apis_dir, service_name)
        function_map = utils.extract_function_map(service_path)
        
        if function_map:
            consolidated_map[service_name] = {
                tool_name: module_path.split('.')[-1]
                for tool_name, module_path in function_map.items()
            }
    return consolidated_map

def generate_report():
    """
    Generates a CSV report from the tech debt analysis results.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    results_dir = os.path.join(base_dir, 'tech_debt_analyzer', 'results')
    output_path = os.path.join(base_dir, 'tech_debt_report.csv')

    # Build the consolidated map to find the correct function names
    consolidated_map = build_consolidated_function_map(base_dir)

    # Define the headers as per the exact specification
    headers = [
        'API Name',
        'Item Type',
        'Item Name',
        'File Name',
        'Project Structure (Complete|Mostly Complete|Incomplete|Poor Structure|Others)',
        'Project Structure-notes',
        'Docstring Quality (Excellent|Good|Adequate|Poor|Missing|Others)',
        'Docstring Quality-notes',
        'Pydantic Usage (Properly Used|Partially Used|Not Needed|Missing Validation|Not Applicable|Others)',
        'Pydantic Usage-notes',
        'Input Validation (Comprehensive|Good|Partial|Minimal|None|Others)',
        'Input Validation-notes',
        'Function Parameters (Excellent|Good|Fair|Poor|Others)',
        'Function Parameters-notes',
        'Implementation Status (Fully Implemented|Mostly Complete|Partially Complete|Stub|Not Implemented|Others)',
        'Implementation Status-notes',
        'Input Normalization-status', # Assuming a simple name as it wasn't in the list
        'Input Normalization-notes'
    ]
    
    # Mapping from the output_key in config.json to the new header formats
    key_to_header_map = {
        'project_structure': {
            'status': 'Project Structure (Complete|Mostly Complete|Incomplete|Poor Structure|Others)',
            'notes': 'Project Structure-notes'
        },
        'docstring_quality': {
            'status': 'Docstring Quality (Excellent|Good|Adequate|Poor|Missing|Others)',
            'notes': 'Docstring Quality-notes'
        },
        'pydantic_usage': {
            'status': 'Pydantic Usage (Properly Used|Partially Used|Not Needed|Missing Validation|Not Applicable|Others)',
            'notes': 'Pydantic Usage-notes'
        },
        'input_validation': {
            'status': 'Input Validation (Comprehensive|Good|Partial|Minimal|None|Others)',
            'notes': 'Input Validation-notes'
        },
        'function_parameters': {
            'status': 'Function Parameters (Excellent|Good|Fair|Poor|Others)',
            'notes': 'Function Parameters-notes'
        },
        'implementation_status': {
            'status': 'Implementation Status (Fully Implemented|Mostly Complete|Partially Complete|Stub|Not Implemented|Others)',
            'notes': 'Implementation Status-notes'
        },
        'input_normalization': { # Assuming a simple name as it wasn't in the list
            'status': 'Input Normalization-status',
            'notes': 'Input Normalization-notes'
        }
    }

    all_rows = []

    # Process all _results.json files in the results directory
    for filename in os.listdir(results_dir):
        if filename.endswith("_results.json") or filename == "results.json":
            file_path = os.path.join(results_dir, filename)
            
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Process project-level results
            if "project_level" in data:
                for proj_name, proj_data in data["project_level"].items():
                    row = {
                        'API Name': proj_name,
                        'Item Type': 'Service',
                        'Item Name': proj_name,
                        'File Name': '',
                    }
                    for key, header_map in key_to_header_map.items():
                        if key in proj_data:
                            row[header_map['status']] = proj_data[key].get('status', '')
                            row[header_map['notes']] = proj_data[key].get('notes', '')
                    all_rows.append(row)

            # Process function-level results
            if "results" in data:
                for file_name, file_data in data["results"].items():
                    path_parts = file_name.split(os.sep)
                    api_index = path_parts.index('APIs') if 'APIs' in path_parts else -1
                    service_name_from_path = path_parts[api_index + 1] if api_index != -1 and len(path_parts) > api_index + 1 else "general"

                    relative_file_name = os.path.join(service_name_from_path, os.path.basename(file_name)).replace('\\', '/')

                    for tool_name, func_checks in file_data.get("functions", {}).items():
                        # Use the consolidated map to get the correct function name
                        actual_func_name = consolidated_map.get(service_name_from_path, {}).get(tool_name, tool_name)
                        
                        row = {
                            'API Name': service_name_from_path,
                            'Item Type': 'Function',
                            'Item Name': actual_func_name,
                            'File Name': relative_file_name,
                        }
                        for key, header_map in key_to_header_map.items():
                            if key in func_checks:
                                row[header_map['status']] = func_checks[key].get('status', '')
                                row[header_map['notes']] = func_checks[key].get('notes', '')
                        all_rows.append(row)

    # Write the data to the CSV file
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"Successfully generated tech debt report at: {output_path}")
    except IOError:
        print(f"Error: Could not write to file at {output_path}")

if __name__ == "__main__":
    generate_report()
