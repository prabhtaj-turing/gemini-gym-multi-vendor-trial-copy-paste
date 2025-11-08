

import argparse
import os
import sys
import json
import ast

# Add parent directories to sys.path to allow importing modules from other directories.
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
# Add project root to path for Scripts.FCSpec
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
# Add tech_debt_analyzer to path for utils
tech_debt_analyzer_path = os.path.join(parent_dir, 'tech_debt_analyzer')
if tech_debt_analyzer_path not in sys.path:
    sys.path.insert(0, tech_debt_analyzer_path)

try:
    import utils
    from Scripts.FCSpec_depricated import generate_package_schema
except ImportError as e:
    print(f"Error: Could not import a required module: {e}")
    print("Please ensure all dependencies and paths are correct.")
    sys.exit(1)

def get_function_docstring(file_path, func_name):
    """
    Parses a Python file to extract the docstring of a specific function using AST.

    Args:
        file_path (str): The absolute path to the Python file.
        func_name (str): The name of the function whose docstring to extract.

    Returns:
        str: The extracted docstring, or a message if not found.
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"

    with open(file_path, 'r', encoding='utf-8') as source_file:
        try:
            tree = ast.parse(source_file.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    docstring = ast.get_docstring(node)
                    return docstring if docstring else "No docstring found for this function."
            return f"Error: Function '{func_name}' not found in the file."
        except Exception as e:
            return f"Error parsing file {file_path}: {e}"

def get_tool_schema(service_name, tool_name):
    """
    Finds and returns the FC Spec schema for a specific tool.

    Args:
        service_name (str): The name of the service.
        tool_name (str): The name of the tool.

    Returns:
        dict: The tool's schema, or an error dictionary if not found.
    """
    schema_path = os.path.join(parent_dir, 'Schemas', f"{service_name}.json")
    if not os.path.exists(schema_path):
        return {"error": f"Schema file not found at {schema_path}"}

    with open(schema_path, 'r', encoding='utf-8') as f:
        try:
            schema_data = json.load(f)
            for schema in schema_data:
                if schema.get('name') == tool_name:
                    return schema
            return {"error": f"Tool '{tool_name}' not found in schema file."}
        except json.JSONDecodeError as e:
            return {"error": f"Error decoding JSON from {schema_path}: {e}"}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {e}"}

def main():
    """
    Main function to drive the script.
    """
    parser = argparse.ArgumentParser(
        description="Extract, display, and save the docstring and FC Spec schema for a given tool.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'tool',
        help="The tool to inspect, in the format <service_name>/<tool_name>."
    )
    args = parser.parse_args()

    tool_identifier = args.tool
    if '/' not in tool_identifier:
        print("Error: Invalid format for the tool. Please use <service_name>/<tool_name>.")
        sys.exit(1)

    service_name, tool_name = tool_identifier.split('/', 1)
    service_path = os.path.join(parent_dir, 'APIs', service_name)

    if not os.path.isdir(service_path):
        print(f"Error: Service '{service_name}' not found at '{service_path}'.")
        sys.exit(1)

    # --- 0. Generate Latest Schema ---
    print("---" * 15)
    print(f"🔄 Generating latest schema for service: {service_name}")
    print("---" * 15)
    schema_output_dir = os.path.join(parent_dir, 'Schemas')
    try:
        generate_package_schema(service_path, output_folder_path=schema_output_dir)
        print(f"✅ Schema generated successfully at {os.path.join(schema_output_dir, service_name + '.json')}")
    except Exception as e:
        print(f"❌ Error generating schema: {e}")
        print("Aborting due to schema generation failure.")
        sys.exit(1)
    print("\n")

    function_map = utils.extract_function_map(service_path)
    if not function_map:
        print(f"Error: No `_function_map` found for service '{service_name}'.")
        sys.exit(1)

    if tool_name not in function_map:
        print(f"Error: Tool '{tool_name}' not found in the function map for service '{service_name}'.")
        sys.exit(1)

    import_path = function_map[tool_name]
    try:
        module_path, actual_func_name = import_path.rsplit('.', 1)
    except ValueError:
        print(f"Error: Invalid import path format for '{import_path}' (no '.' found).")
        sys.exit(1)


    if module_path.startswith(service_name + '.'):
        module_path = module_path.split('.', 1)[1]

    # Construct the file path from the module path, assuming it's relative to the service directory.
    relative_to_service_path = module_path.replace('.', os.sep)

    # First, check for a .py file
    absolute_file_path = os.path.join(service_path, relative_to_service_path + '.py')

    if not os.path.isfile(absolute_file_path):
        # If not found, check for a package with __init__.py
        init_path = os.path.join(service_path, relative_to_service_path, '__init__.py')
        if os.path.isfile(init_path):
            absolute_file_path = init_path
        else:
            print(f"Error: File not found for import path '{import_path}' in service '{service_name}'")
            print(f"Looked for: {absolute_file_path}")
            print(f"And for: {init_path}")
            sys.exit(1)
    
    relative_file_path = os.path.relpath(absolute_file_path, parent_dir)

    # --- Setup Output Directory ---
    output_dir = os.path.join(parent_dir, 'analysis_output')
    os.makedirs(output_dir, exist_ok=True)
    docstring_output_path = os.path.join(output_dir, 'docstring.txt')
    schema_output_path = os.path.join(output_dir, 'fcspec.json')

    # --- 1. Get, Print, and Save Docstring ---
    print("---" * 15)
    print(f"🐍 Docstring for: {service_name}/{tool_name} ({actual_func_name})")
    print(f"   Source File: {relative_file_path}")
    print("---" * 15)
    docstring = get_function_docstring(absolute_file_path, actual_func_name)
    print(docstring)
    with open(docstring_output_path, 'w', encoding='utf-8') as f:
        f.write(docstring)
    print(f"\n💾 Docstring saved to: {docstring_output_path}")
    print("\n")

    # --- 2. Get, Print, and Save FC Spec Schema ---
    print("---" * 15)
    print(f"📄 FC Spec Schema for: {service_name}/{tool_name}")
    print("---" * 15)
    schema = get_tool_schema(service_name, tool_name)
    schema_json = json.dumps(schema, indent=2)
    print(schema_json)
    with open(schema_output_path, 'w', encoding='utf-8') as f:
        f.write(schema_json)
    print(f"\n💾 Schema saved to: {schema_output_path}")


if __name__ == '__main__':
    main()
