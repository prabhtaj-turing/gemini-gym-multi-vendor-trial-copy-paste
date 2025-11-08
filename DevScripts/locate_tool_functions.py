import ast
import os
import json
from DevScripts.extract_function_maps import extract_function_maps

def get_function_details(filepath, func_name):
    """
    Finds a function's line number and checks for an existing @tool_spec decorator.
    Returns detailed information about the decorator if found.
    Returns None if the function is not found.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
            tree = ast.parse(source, filename=filepath)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                # The line number for the 'def' keyword is after the last decorator.
                def_line = node.lineno
                if node.decorator_list:
                    def_line = node.decorator_list[-1].end_lineno + 1

                # Check if '@tool_spec' is in any of the decorator lines.
                has_tool_spec = False
                tool_spec_info = None
                source_lines = source.splitlines()
                
                for i, decorator_node in enumerate(node.decorator_list):
                    # Read the line content for the decorator to check its name
                    decorator_line_content = source_lines[decorator_node.lineno - 1]
                    if '@tool_spec' in decorator_line_content:
                        has_tool_spec = True
                        # Get the complete decorator span (can be multi-line)
                        tool_spec_info = {
                            "start_line": decorator_node.lineno,
                            "end_line": decorator_node.end_lineno,
                            "decorator_index": i,
                            "total_decorators": len(node.decorator_list)
                        }
                        break
                
                return {
                    "line": def_line, 
                    "has_decorator": has_tool_spec,
                    "tool_spec_info": tool_spec_info,
                    "function_start_line": node.lineno,
                    "decorator_count": len(node.decorator_list)
                }
        return None  # Function not found in file
    except Exception as e:
        return None # Error parsing file

def locate_tool_function(apis_dir, service, tool_name):
    """
    Resolves the file path and function location details for a given tool.
    """
    all_function_maps = extract_function_maps(apis_dir)
    
    function_map = all_function_maps.get(service)
    if not function_map:
        return {"error": f"Service '{service}' not found."}

    import_path = function_map.get(tool_name)
    if not import_path:
        return {"error": f"Tool '{tool_name}' not found in service '{service}'."}

    try:
        module_path, func_name = import_path.rsplit('.', 1)
        relative_file_path = module_path.replace('.', os.sep)
        file_py_path = os.path.join(apis_dir, relative_file_path + '.py')

        if not os.path.isfile(file_py_path):
            # Handle cases where the module is a package (__init__.py)
            file_init_path = os.path.join(apis_dir, relative_file_path, '__init__.py')
            if os.path.isfile(file_init_path):
                file_py_path = file_init_path
            else:
                return {"error": f"File not found for import path '{import_path}'"}

        location_details = get_function_details(file_py_path, func_name)
        
        if location_details:
            result = {
                "service": service,
                "tool": tool_name,
                "file_path": file_py_path,
                "function_name": func_name,
                "import_path": import_path,
                "line": location_details["line"],
                "has_decorator": location_details["has_decorator"]
            }
            # Include detailed decorator info if present
            if location_details.get("tool_spec_info"):
                result["tool_spec_info"] = location_details["tool_spec_info"]
            return result
        else:
            return {"error": f"Function '{func_name}' not found in file: {file_py_path}"}

    except ValueError:
        return {"error": f"Invalid import path format for '{import_path}' (no '.' found)."}

if __name__ == '__main__':
    current_dir = os.path.dirname(__file__)
    apis_dir = os.path.abspath(os.path.join(current_dir, '..', 'APIs'))
    
    # --- Example 1: A standard tool ---
    service_to_find = 'google_search'
    tool_to_find = 'search'
    print(f"Locating: '{service_to_find}.{tool_to_find}'...")
    location_info = locate_tool_function(apis_dir, service_to_find, tool_to_find)
    print(json.dumps(location_info, indent=2))

    print("-" * 20)

    # --- Example 2: A tool in a different service ---
    service_to_find = 'gmail'
    tool_to_find = 'create_draft'
    print(f"Locating: '{service_to_find}.{tool_to_find}'...")
    location_info = locate_tool_function(apis_dir, service_to_find, tool_to_find)
    print(json.dumps(location_info, indent=2))