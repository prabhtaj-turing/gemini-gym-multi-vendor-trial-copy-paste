import ast
import os
import json

def extract_function_maps(base_dir):
    """
    Extracts _function_map dictionaries from __init__.py files in subdirectories.

    Args:
        base_dir (str): The base directory to search for service folders.

    Returns:
        dict: A dictionary where keys are service names and values are their _function_map.
    """
    all_function_maps = {}
    for service_name in os.listdir(base_dir):
        service_path = os.path.join(base_dir, service_name)
        if os.path.isdir(service_path) and service_name not in ['common_utils', '__pycache__']:
            init_file = os.path.join(service_path, '__init__.py')
            if os.path.exists(init_file):
                try:
                    with open(init_file, 'r', encoding='utf-8') as f:
                        file_contents = f.read()
                    
                    tree = ast.parse(file_contents)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name) and target.id == '_function_map':
                                    if isinstance(node.value, ast.Dict):
                                        # Safely evaluate the dictionary literal
                                        function_map = ast.literal_eval(node.value)
                                        all_function_maps[service_name] = function_map
                                    break  # Found the assignment, no need to check other targets
                except Exception as e:
                    print(f"Could not process {init_file}: {e}")
    return all_function_maps

if __name__ == '__main__':
    apis_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'APIs'))
    function_maps = extract_function_maps(apis_dir)
    print(json.dumps(function_maps, indent=2))
