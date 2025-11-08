
"""
Generates FCSpec schemas by dynamically importing tool functions and
accessing the .spec attribute provided by the @tool_spec decorator.
This script is a drop-in replacement for the original docstring-based FCSpec.py.
"""

import os
import sys
import json
import importlib
import ast
import concurrent.futures
from pathlib import Path

# --- Configuration & Constants ---
# Adjust MAX_WORKERS based on the number of CPU cores for optimal performance
try:
    MAX_WORKERS = os.cpu_count() or 4
except NotImplementedError:
    MAX_WORKERS = 4

# --- Helper Functions ---

def _strip_descriptions(data):
    """
    Recursively strips whitespace from all 'description' values in a dictionary
    and reorders keys to put 'description' before 'type'.
    """
    if isinstance(data, dict):
        # Check if this looks like a property definition (has 'type' and possibly 'description')
        if 'type' in data and 'description' in data:
            # Reorder to put description first
            reordered = {}
            # First add description if it exists
            if 'description' in data:
                reordered['description'] = data['description']
            # Then add type
            if 'type' in data:
                reordered['type'] = data['type']
            # Then add all other keys in their original order
            for k, v in data.items():
                if k not in ['description', 'type']:
                    reordered[k] = v
            data = reordered
        
        # Process all values recursively
        for key, value in list(data.items()):
            if key == "description" and isinstance(value, str):
                # Custom dedent logic for descriptions that start without indentation
                lines = value.split('\n')
                if len(lines) > 1:
                    # Find minimum indentation of non-empty lines (excluding first line)
                    min_indent = float('inf')
                    for line in lines[1:]:  # Skip first line
                        if line.strip():  # Only consider non-empty lines
                            indent = len(line) - len(line.lstrip())
                            min_indent = min(min_indent, indent)
                    

                    if min_indent != float('inf') and min_indent > 0:
                        dedented_lines = [lines[0]]  # Keep first line as-is
                        for line in lines[1:]:
                            if line.strip():  # Non-empty line
                                dedented_lines.append(line[min_indent:])
                            else:  # Empty line
                                dedented_lines.append(line)
                        value = '\n'.join(dedented_lines)
                
                # Final strip to remove leading/trailing whitespace
                data[key] = value.strip()
            else:
                data[key] = _strip_descriptions(value)
    elif isinstance(data, list):
        return [_strip_descriptions(item) for item in data]
    return data

def get_variable_from_file(filepath: str, variable_name: str):
    """Safely extracts a variable from a Python file using AST parsing."""
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as source_file:
        source_code = source_file.read()
    try:
        tree = ast.parse(source_code, filename=filepath)
    except SyntaxError as e:
        print(f"  - ERROR: Syntax error in {filepath}: {e}")
        return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable_name:
                    try:
                        return ast.literal_eval(node.value)
                    except (ValueError, SyntaxError):
                        return None
    return None

# --- Core Schema Generation Logic (Decorator-based) ---

def process_single_function(args):
    """
    Processes a single function to generate its schema by reading its .spec attribute.
    """
    public_name, fqn, package_root = args
    try:
        module_path, func_name = fqn.rsplit('.', 1)
        
        # Add APIs directory to sys.path so packages can import each other
        apis_path = os.path.join(package_root, 'APIs')
        if apis_path not in sys.path:
            sys.path.insert(0, apis_path)

        full_module_path = module_path  # Use original path since APIs is in sys.path
        
        # Ensure the module is fresh for each function to avoid import cache issues
        if full_module_path in sys.modules:
            importlib.reload(sys.modules[full_module_path])
            
        module = importlib.import_module(full_module_path)
        func = getattr(module, func_name)

        if hasattr(func, 'spec'):
            spec_data = dict(func.spec)
            spec_data['name'] = public_name
            return _strip_descriptions(spec_data)
        else:
            print(f"  - WARNING: Function '{fqn}' does not have a .spec attribute.")
            return None

    except Exception as e:
        # Catching a broad exception class because import errors can be varied and tricky
        print(f"  - ERROR: An unexpected error occurred for '{public_name}' ({fqn}): {e}")
    return None


def generate_package_schema(package_path: str, output_folder_path: str, **kwargs):
    """
    Generates a schema file for a single package by reading decorators.
    This function is designed to be run in its own process.
    """
    package_name = os.path.basename(package_path)
    print(f"-> Processing package: {package_name}")
    
    init_path = os.path.join(package_path, "__init__.py")

    if not os.path.exists(init_path):
        print(f"   - Error: __init__.py not found in {package_path}")
        return

    function_map = get_variable_from_file(init_path, "_function_map")
    if not function_map:
        print(f"   - Error: Could not find a valid _function_map in {init_path}.")
        return

    package_root = str(Path(package_path).parent.parent)
    function_args = [(name, fqn, package_root) for name, fqn in function_map.items()]
    
    # Process functions sequentially within this single process
    all_schemas = [s for s in map(process_single_function, function_args) if s]

    if all_schemas:
        all_schemas.sort(key=lambda x: x.get('name', ''))
        
        output_file = os.path.join(output_folder_path, f"{package_name}.json")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_schemas, f, indent=2, ensure_ascii=False)
        print(f"✅ Schema generation complete for {package_name}: {output_file}")
    else:
        print(f"❌ No schemas were generated for {package_name}.")


def generate_schemas_for_packages(source_folder: str, schemas_folder: str):
    """
    Generates schemas for all packages found in the source directory using a process pool.
    The 'mysql' package is processed sequentially AFTER all other packages are completed.
    """
    source_path = Path(source_folder)
    schemas_path = Path(schemas_folder)

    if not source_path.is_dir():
        raise FileNotFoundError(f"Source folder not found: {source_path}")

    os.makedirs(schemas_path, exist_ok=True)

    packages_to_process = [
        (str(p), str(schemas_path))
        for p in source_path.iterdir()
        if p.is_dir() and p.name not in ['common_utils', '__pycache__']
    ]

    mysql_package = next((p for p in packages_to_process if os.path.basename(p[0]) == 'mysql'), None)
    other_packages = [p for p in packages_to_process if os.path.basename(p[0]) != 'mysql']

    print(f"Found {len(packages_to_process)} packages to process.")
    if mysql_package:
        print(f"Note: mysql package will be processed last, sequentially.")

    # Use ProcessPoolExecutor to run each package schema generation in a separate process
    if other_packages:
        print(f"Processing {len(other_packages)} packages in parallel...")
        with concurrent.futures.ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(generate_package_schema, *args) for args in other_packages]
            
            # Wait for ALL futures to complete before proceeding
            completed = 0
            for future in concurrent.futures.as_completed(futures):
                completed += 1
                try:
                    future.result()  # We call result() to raise any exceptions from the child process
                except Exception as e:
                    print(f"--- A child process failed with an error ---")
                    print(e)
                    print("-------------------------------------------")
                
                # Progress indicator
                if completed % 10 == 0 or completed == len(other_packages):
                    print(f"Progress: {completed}/{len(other_packages)} packages completed")
        
        print("All parallel processing completed.")
    
    # Process mysql package sequentially AFTER all other packages are done
    if mysql_package:
        print("\nNow processing mysql package sequentially...")
        try:
            generate_package_schema(*mysql_package)
        except Exception as e:
            print(f"--- The mysql package processing failed with an error ---")
            print(e)
            print("-------------------------------------------------------")


def main():
    """Sets up paths and initiates schema generation."""
    current_file_dir = Path(__file__).parent
    project_root = current_file_dir.parent
    
    # Add project root to Python path to allow dynamic imports from child processes
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    source_folder = project_root / "APIs"
    schemas_folder = project_root / "Schemas"

    generate_schemas_for_packages(str(source_folder), str(schemas_folder))

if __name__ == "__main__":
    main()

