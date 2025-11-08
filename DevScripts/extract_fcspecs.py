import os
import json

def load_fcspecs(schemas_dir):
    """
    Loads all FCSpecs from the schemas directory.

    Args:
        schemas_dir (str): The directory containing the schema JSON files.

    Returns:
        dict: A dictionary where keys are service names and values are dictionaries
              of tool names to their FCSpecs.
    """
    all_fcspecs = {}
    for filename in os.listdir(schemas_dir):
        if filename.endswith('.json'):
            service_name = filename[:-5]  # Remove .json extension
            filepath = os.path.join(schemas_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    specs = json.load(f)
                    tool_specs = {spec['name']: spec for spec in specs}
                    all_fcspecs[service_name] = tool_specs
            except Exception as e:
                print(f"Could not process {filepath}: {e}")
    return all_fcspecs

if __name__ == '__main__':
    schemas_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Schemas'))
    all_specs = load_fcspecs(schemas_dir)
    
    # --- Example Usage ---
    # Print the loaded specs for one service to demonstrate the function works.
    example_service = 'spotify'
    if example_service in all_specs:
        print(f"--- FCSpecs for '{example_service}' ---")
        print(json.dumps(all_specs[example_service], indent=2))
    else:
        print(f"Service '{example_service}' not found. Printing all loaded services.")
        print(list(all_specs.keys()))
