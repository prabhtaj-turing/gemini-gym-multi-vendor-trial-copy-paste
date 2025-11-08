

import os
import ast
import re
from pathlib import Path
from typing import List, Dict

def get_function_code_from_file(file_path: str, function_name: str) -> str:
    """
    Extract the specific function code from a file by reading it directly.
    This is the most robust method to avoid in-memory corruption.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        return f"File not found: {file_path}"
    except Exception as e:
        return f"Error reading file {file_path}: {e}"

    start_line = -1
    # Find the starting line of the function definition
    for i, line in enumerate(lines):
        # A more robust check for the function definition
        if re.match(rf'\s*def\s+{function_name}\s*\(', line) or re.match(rf'\s*async\s+def\s+{function_name}\s*\(', line):
            start_line = i
            break
            
    if start_line == -1:
        return "Function not found in file"
        
    # Find the end of the function by looking for the next function definition at the same indentation level
    try:
        base_indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())
        end_line = start_line + 1
        
        while end_line < len(lines):
            line = lines[end_line]
            current_indent_level = len(line) - len(line.lstrip())
            
            # Check if the line is a new function definition at the same indentation level
            if (line.strip().startswith("def ") or line.strip().startswith("async def ")) and current_indent_level == base_indent_level:
                break
            
            end_line += 1
            
        return ''.join(lines[start_line:end_line])
    except IndexError:
        # This can happen if the function is the last one in the file
        return ''.join(lines[start_line:])
    except Exception as e:
        return f"Error extracting function: {str(e)}"

def extract_function_map(api_service_path: str) -> Dict[str, str]:
    """
    Extract function map from API service's __init__.py file.
    """
    init_file = os.path.join(api_service_path, "__init__.py")
    if not os.path.exists(init_file):
        return {}
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()

        start_index = content.find('_function_map = {')
        if start_index == -1: return {}
        
        start_brace_index = content.find('{', start_index)
        if start_brace_index == -1: return {}

        content_from_start_brace = content[start_brace_index:]
        bracket_count = 0
        end_brace_index = -1
        
        for i, char in enumerate(content_from_start_brace):
            if char == '{': bracket_count += 1
            elif char == '}': bracket_count -= 1
            if bracket_count == 0:
                end_brace_index = i
                break
        
        if end_brace_index == -1: return {}

        dict_string = content_from_start_brace[:end_brace_index + 1]
        return ast.literal_eval(dict_string)

    except (ValueError, SyntaxError, FileNotFoundError) as e:
        print(f"Error processing {init_file}: {e}")
        return {}

def get_api_structure(service_path: str) -> Dict:
    """
    Gathers the file structure of a service, ignoring specified folders.
    """
    api_data = {
        'api_name': os.path.basename(service_path),
        'simulation_engine_files': [],
        'tests_files': [],
        'main_api_files': [],
        'init_file': None
    }
    
    ignore_dirs = ['mutations', '__pycache__']

    for root, dirs, files in os.walk(service_path):
        # Modify dirs in-place to prevent walking into ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        for file in files:
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, service_path)
            
            file_info = {'name': file, 'path': file_path, 'content': ''} # content can be added if needed

            if 'SimulationEngine' in root:
                api_data['simulation_engine_files'].append(file_info)
            elif 'tests' in root:
                api_data['tests_files'].append(file_info)
            elif root == service_path:
                if file == '__init__.py':
                    api_data['init_file'] = file_info
                else:
                    api_data['main_api_files'].append(file_info)

    return api_data

