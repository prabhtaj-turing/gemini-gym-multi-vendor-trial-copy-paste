
import json
import os
from deepdiff import DeepDiff

def compare_schemas(old_dir, new_dir):
    """
    Compares schema files between two directories, ignoring top-level 'required' fields.
    """
    print("--- Starting Schema Comparison ---")
    
    old_files = set(os.listdir(old_dir))
    new_files = set(os.listdir(new_dir))

    common_files = sorted(list(old_files.intersection(new_files)))
    missing_in_new = sorted(list(old_files - new_files))
    
    differences_found = False

    print(f"Found {len(common_files)} common schema files to compare.")

    for filename in common_files:
        if not filename.endswith('.json'):
            continue

        old_path = os.path.join(old_dir, filename)
        new_path = os.path.join(new_dir, filename)

        try:
            with open(old_path, 'r') as f:
                old_data = json.load(f)
            with open(new_path, 'r') as f:
                new_data = json.load(f)

            # Create a dictionary for quick lookup by tool name
            old_tools = {tool['name']: tool for tool in old_data}
            new_tools = {tool['name']: tool for tool in new_data}

            all_tool_names = sorted(list(set(old_tools.keys()) | set(new_tools.keys())))

            for tool_name in all_tool_names:
                old_tool = old_tools.get(tool_name)
                new_tool = new_tools.get(tool_name)

                if not old_tool:
                    print(f"\n- [{filename}] New tool found: {tool_name}")
                    differences_found = True
                    continue
                if not new_tool:
                    print(f"\n- [{filename}] Tool missing in new schema: {tool_name}")
                    differences_found = True
                    continue

                # Extract the 'parameters' object from both schemas for a direct comparison.
                old_params = old_tool.get('parameters', {})
                new_params = new_tool.get('parameters', {})

                # The main comparison logic
                diff = DeepDiff(
                    old_params, 
                    new_params, 
                    ignore_order=True
                )

                if diff:
                    print(f"\n--- Differences found in {filename} for tool '{tool_name}' ---")
                    print(diff.pretty())
                    differences_found = True

        except json.JSONDecodeError as e:
            print(f"\nERROR: Could not decode JSON in {filename}: {e}")
            differences_found = True
        except Exception as e:
            print(f"\nERROR: An unexpected error occurred with {filename}: {e}")
            differences_found = True

    if missing_in_new:
        print("\n--- Schemas Missing in 'Schemas_new' Directory ---")
        for filename in missing_in_new:
            print(f"  - {filename}")
        differences_found = True

    print("\n--- Comparison Summary ---")
    if not differences_found:
        print("✅ SUCCESS: No significant differences found between the old and new schemas.")
    else:
        print("❌ FAILURE: Differences were found. Please review the logs above.")
    print("--------------------------")


if __name__ == "__main__":
    old_schemas_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Schemas'))
    new_schemas_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'SchemasNew'))
    compare_schemas(old_schemas_dir, new_schemas_dir)
