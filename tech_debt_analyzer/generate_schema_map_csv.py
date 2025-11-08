#!/usr/bin/env python3

"""
This script generates a CSV that maps function names to their public tool names
and their corresponding FCSpec schemas, using a three-part key for accuracy.
It precisely replicates the file path logic from the main analyzer.
"""

import os
import sys
import json
import csv

# --- Add Project Root to Python Path ---
try:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
except NameError:
    BASE_DIR = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from tech_debt_analyzer import utils

def load_all_function_maps_with_files(apis_dir):
    """
    Loads all _function_maps and creates a reverse map that includes the file path,
    replicating the logic from the main analyzer.
    """
    print("Loading all function maps...")
    reverse_map = {}
    
    service_dirs = [d for d in os.listdir(apis_dir) if os.path.isdir(os.path.join(apis_dir, d))]
    
    for service_name in service_dirs:
        service_path = os.path.join(apis_dir, service_name)
        function_map = utils.extract_function_map(service_path)
        if not function_map:
            continue
        
        for tool_name, module_path in function_map.items():
            path_parts = module_path.split('.')
            actual_func_name = path_parts[-1]
            
            # --- REPLICATE MAIN ANALYZER LOGIC ---
            # 1. Construct the full path to the file, just as the analyzer does.
            # Note: We don't need the 'APIs' prefix here as the base is already apis_dir
            full_file_path = os.path.join(service_path, *path_parts[1:-1]) + '.py'
            
            # 2. Extract just the basename for the mapping key. This is the crucial step.
            file_name_for_key = os.path.basename(full_file_path)

            map_key = (service_name, file_name_for_key, actual_func_name)
            reverse_map[map_key] = tool_name
            
    print(f"Loaded maps for {len(reverse_map)} functions across services.")
    return reverse_map

def load_all_schemas(schemas_dir):
    """
    Loads all FCSpec schemas from the Schemas directory into a dictionary.
    """
    print("Loading all schemas...")
    schemas = {}
    for filename in os.listdir(schemas_dir):
        if filename.endswith(".json"):
            service_name = filename.replace(".json", "")
            file_path = os.path.join(schemas_dir, filename)
            try:
                with open(file_path, 'r') as f:
                    schemas[service_name] = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load schema for '{service_name}': {e}")
    print(f"Loaded {len(schemas)} schemas.")
    return schemas

def find_schema_for_tool(schema_data, tool_name):
    """
    Finds the specific function's schema within the loaded schema data.
    """
    if not schema_data or not tool_name:
        return None

    if isinstance(schema_data, list):
        for func_schema in schema_data:
            if func_schema.get('name') == tool_name:
                return func_schema
    elif isinstance(schema_data, dict):
        for tool in schema_data.get('tools', []):
            for func_schema in tool.get('function_declarations', []):
                if func_schema.get('name') == tool_name:
                    return func_schema
    return None

def main():
    """
    Main function to generate the mapping CSV.
    """
    apis_dir = os.path.join(BASE_DIR, "APIs")
    schemas_dir = os.path.join(BASE_DIR, "Schemas")
    output_csv = os.path.join(BASE_DIR, "function_schema_map.csv")

    # 1. Load all necessary data into memory
    reverse_function_map = load_all_function_maps_with_files(apis_dir)
    all_schemas = load_all_schemas(schemas_dir)

    # 2. Prepare rows for the new CSV
    header = ["APIs", "File", "Function Name", "Tool Name", "Schema"]
    rows = []
    for (service_name, file_name, func_name), tool_name in reverse_function_map.items():
        schema_for_service = all_schemas.get(service_name)
        schema_dict = find_schema_for_tool(schema_for_service, tool_name)
        schema_json = json.dumps(schema_dict) if schema_dict else "N/A"
        rows.append([service_name, file_name, func_name, tool_name, schema_json])

    # 3. Write the data to the output CSV
    try:
        with open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header)
            writer.writerows(rows)
        print(f"\nSuccessfully created mapping file: {output_csv}")
        print(f"Mapped {len(rows)} functions.")
    except (IOError, csv.Error) as e:
        print(f"Error writing to CSV file: {e}")

if __name__ == "__main__":
    main()
