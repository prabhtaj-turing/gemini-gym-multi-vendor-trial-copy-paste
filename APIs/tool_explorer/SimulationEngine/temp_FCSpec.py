# %%
import os
import shutil
import sys
import ast
import json
import docstring_parser
import importlib
from typing import Dict, List, Tuple, Optional, Any, Union, Set
import re
import concurrent.futures
import threading

# --- Configuration & Constants ---
MAX_WORKERS = 10 # Adjust based on system capabilities
print_lock = threading.Lock()

JSON_TYPE_STRING = "string"
JSON_TYPE_INTEGER = "integer"
JSON_TYPE_NUMBER = "number"
JSON_TYPE_BOOLEAN = "boolean"
JSON_TYPE_ARRAY = "array"
JSON_TYPE_OBJECT = "object"
JSON_TYPE_NULL = "null"

# --- Trivial Function Detection Logic (from Utils/FCSpec.py) ---

def resolve_function_source_path(qualified: str, source_root: str) -> str:
    """
    Convert a qualified path (e.g., 'my_package.my_module.my_function') to a file path
    and return the .py file containing the function.
    """
    parts = qualified.split(".")
    # The last part is the function/class name, the preceding parts form the module path.
    *module_parts, _ = parts
    base_path = os.path.join(source_root, *module_parts)

    module_file = base_path + ".py"
    if os.path.isfile(module_file):
        return module_file
    elif os.path.isdir(base_path):
        # Check for package __init__.py
        init_file = os.path.join(base_path, "__init__.py")
        if os.path.isfile(init_file):
            return init_file
    # Providing more details in the error message for better debugging
    raise FileNotFoundError(f"Could not resolve source file for {qualified}. Tried: '{module_file}' and '{init_file if 'init_file' in locals() else 'N/A'}'")

def strip_comments(source: str) -> str:
    """
    Strip comments from a Python source code string.
    Removes lines that are entirely comments or inline comments from the end of lines.
    """
    lines = source.splitlines()
    no_comment_lines = []
    for line in lines:
        # Remove everything from '#' to the end of the line
        no_comment = re.sub(r'#.*', '', line)
        # Keep only non-empty lines after stripping comments and whitespace
        if no_comment.strip():
            no_comment_lines.append(no_comment)
    return '\n'.join(no_comment_lines)

def strip_comments_and_docstrings(source: str) -> str:
    """
    Strip comments and docstrings from a Python source code string.
    This version improves docstring removal by precisely identifying docstring
    line ranges via AST (using `lineno` and `end_lineno`) and then reconstructing
    the source without those lines. It ensures that only actual docstring content
    is removed without affecting identical strings elsewhere in the code.
    It then applies `strip_comments` to handle remaining comments.
    """
    try:
        parsed = ast.parse(source)
    except Exception: # Catching broad exception for resilience against syntax errors
        # If parsing fails, fall back to just stripping comments
        return strip_comments(source)

    lines = source.splitlines()
    lines_to_exclude = set()

    for node in ast.walk(parsed):
        # Check for nodes that can contain docstrings
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            # Docstring is typically the first statement in the body
            if hasattr(node, 'body') and len(node.body) > 0:
                doc_node = node.body[0]
                # Verify it's an AST expression node containing a string constant (the docstring itself)
                if isinstance(doc_node, ast.Expr) and isinstance(doc_node.value, ast.Constant) and isinstance(doc_node.value.value, str):
                    # Mark all lines occupied by the docstring for exclusion
                    # `ast.lineno` and `ast.end_lineno` are 1-based, so adjust to 0-based for list indexing
                    start_line = doc_node.lineno - 1
                    end_line = getattr(doc_node, 'end_lineno', start_line) - 1 # `end_lineno` available since Python 3.8+
                    
                    for i in range(start_line, end_line + 1):
                        lines_to_exclude.add(i)

    # Reconstruct the source without docstring lines
    filtered_lines = []
    for i, line in enumerate(lines):
        if i not in lines_to_exclude:
            filtered_lines.append(line)
            
    # Join the lines and then strip any remaining comments
    return strip_comments('\n'.join(filtered_lines))

def extract_function_source(source: str, func_path: str) -> str:
    """
    Extracts the source code for a function or method from the full module source.
    `func_path` can be: 'function_name' or 'ClassName.method_name'.
    """
    tree = ast.parse(source)

    if "." in func_path:
        class_name, method_name = func_path.split(".", 1)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                # Recursively call to find the method within the class source
                class_source = ast.get_source_segment(source, node)
                if class_source:
                    return extract_function_source(class_source, method_name)
    else:
        # Top-level function
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_path:
                # ast.get_source_segment requires the original source string
                return ast.get_source_segment(source, node) or ''

    raise ValueError(f"Function or method '{func_path}' not found in source.")

def is_node_trivial_return(node: ast.stmt) -> bool:
    """
    Checks if an AST node represents a trivial return statement (e.g., `return`, `return None`,
    `return []`, `return {}`, `return 0`, `return ""`).
    """
    if not isinstance(node, ast.Return):
        return False

    value = node.value
    if value is None:
        return True  # `return` (without a value)

    if isinstance(value, ast.Constant):
        # Check for `None`, empty string, empty bytes, zero (int/float), `False`
        if value.value is None: return True
        if isinstance(value.value, (str, bytes)) and not value.value: return True
        if isinstance(value.value, (int, float)) and value.value == 0: return True
        if isinstance(value.value, bool) and not value.value: return True # `False`
    elif isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        # Check for empty lists, tuples, sets
        if not value.elts: return True
    elif isinstance(value, ast.Dict):
        # Check for empty dictionaries
        if not value.keys: return True
    elif isinstance(value, ast.Name) and value.id == 'None':
        # For older Python versions or specific contexts where `None` might be a `Name` node
        return True
    return False

def is_function_body_trivial(func_source_code: str) -> bool:
    """
    Analyzes the extracted source code of a single function to determine if its body is trivial.
    """
    stripped_func_source = strip_comments_and_docstrings(func_source_code)

    if not stripped_func_source.strip():
        return True

    try:
        tree = ast.parse(stripped_func_source)
        # The AST should contain one top-level FunctionDef or AsyncFunctionDef node.
        if not tree.body or not isinstance(tree.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False # Not a simple function definition
        
        function_node = tree.body[0]
        
        # Filter out any `Expr` nodes that are just string literals (e.g., remaining docstrings)
        effective_statements = [
            stmt for stmt in function_node.body 
            if not (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str))
        ]

        if not effective_statements:
            return True

        if len(effective_statements) == 1:
            stmt = effective_statements[0]
            if isinstance(stmt, ast.Pass) or is_node_trivial_return(stmt):
                return True
    except (SyntaxError, IndexError):
        # If parsing fails or there's no body, it's not what we consider a simple trivial function.
        return False
    return False

def find_trivial_functions(fq_function_names: List[str], source_root: str) -> List[str]:
    """
    Find trivial functions by analyzing their stripped source code based on AST.
    """
    trivial_functions_list = []

    for fq in fq_function_names:
        try:
            file_path = resolve_function_source_path(fq, source_root)
            
            fq_parts = fq.split('.')
            module_name_from_path = os.path.splitext(os.path.basename(file_path))[0]
            if module_name_from_path == "__init__":
                module_name_from_path = os.path.basename(os.path.dirname(file_path))

            # Heuristic to find the start of the function/class path within the FQN
            func_path_in_module = fq
            try:
                # Find where the module path ends and the class/func path begins
                # e.g., if fq is a.b.c.D.e and file is c.py, module path is a.b.c
                # We need to find 'c' in the fq parts
                module_parts = file_path.replace(source_root, '').strip(os.sep).replace('.py','').split(os.sep)
                
                # Find the sequence of module parts in the fq parts
                start_idx = -1
                for i in range(len(fq_parts) - len(module_parts) + 1):
                    if fq_parts[i:i+len(module_parts)] == module_parts:
                        start_idx = i + len(module_parts)
                        break
                if start_idx != -1:
                    func_path_in_module = ".".join(fq_parts[start_idx:])
                else: # Fallback
                    func_path_in_module = fq_parts[-1]

            except Exception:
                 func_path_in_module = fq.split(f"{module_name_from_path}.")[-1]


            with open(file_path, "r", encoding="utf-8") as f:
                full_source = f.read()
            
            func_source = extract_function_source(full_source, func_path_in_module)
            if is_function_body_trivial(func_source):
                trivial_functions_list.append(fq)
        except (FileNotFoundError, ValueError, IndexError) as e:
            # These errors are expected for some paths, so we can continue.
            # print(f"Skipping trivial check for {fq}: {e}")
            continue
        except Exception as e:
            # print(f"An unexpected error in trivial check for {fq}: {e}")
            continue
    return trivial_functions_list

# --- Helper Functions ---

def get_variable_from_file(filepath: str, variable_name: str) -> Optional[Dict]:
    """Safely extracts a variable from a Python file using AST parsing."""
    if not os.path.exists(filepath): return None
    with open(filepath, "r", encoding="utf-8") as source_file:
        source_code = source_file.read()
    try:
        tree = ast.parse(source_code, filename=filepath)
    except SyntaxError: return None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == variable_name:
                    try: return ast.literal_eval(node.value)
                    except (ValueError, SyntaxError): return None
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == variable_name:
                try: return ast.literal_eval(node.value)
                except (ValueError, SyntaxError): return None
    return None

def extract_specific_function_node(filepath: str, fqn: str) -> Optional[Tuple[ast.FunctionDef, str]]:
    """Extracts the AST node and source code of a specific function."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source_code = f.read()
        tree = ast.parse(source_code, filename=filepath)
        
        # This logic needs to correctly find the function/method in the file
        # It's simplified here; a robust solution might need to trace imports
        # For now, we assume the FQN maps directly to file structure
        path_parts = fqn.split('.')
        
        # The path we need to walk down *within* the AST
        # e.g., for 'pkg.module.Class.method', if file is module.py, we need ['Class', 'method']
        # This requires knowing the module part of the FQN.
        # This is a simplification and might fail for complex project structures.
        
        # Let's assume the last part is the function, and the one before (if any) is the class.
        # This is a heuristic.
        func_name = path_parts[-1]
        
        current_nodes = tree.body
        
        # Walk through class definitions if they are in the FQN
        if len(path_parts) > 1:
            class_name_in_fqn = path_parts[-2]
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name_in_fqn:
                    current_nodes = node.body
                    break
        
        for node in current_nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                return node, ast.unparse(node)

    except (IOError, SyntaxError, IndexError): pass
    return None

# --- Deterministic Schema Building Logic ---

def _split_comma_separated_types(params_str: str) -> List[str]:
    """Splits a comma-separated string of types while respecting nested brackets."""
    params, balance, start = [], 0, 0
    for i, char in enumerate(params_str):
        if char in '([': balance += 1
        elif char in ')]': balance -= 1
        elif char == ',' and balance == 0:
            params.append(params_str[start:i].strip())
            start = i + 1
    params.append(params_str[start:].strip())
    return [p for p in params if p]

def is_optional_type_string(type_str: Optional[str]) -> bool:
    """Check if a type string represents an optional type."""
    if not type_str: return False
    type_str = type_str.strip().strip("()").strip()
    if type_str.startswith("Optional[") and type_str.endswith("]"): return True
    if type_str.startswith("Union[") and type_str.endswith("]"):
        return any(t.strip().lower() in ['none', 'nonetype'] for t in _split_comma_separated_types(type_str[6:-1]))
    return any(part.strip().lower() == 'optional' for part in type_str.split(','))

def map_type(type_str: Optional[str]) -> Dict[str, Any]:
    """Maps a Python type string to a JSON schema object."""
    type_str = (type_str or "Any").strip()
    type_map = {"str": JSON_TYPE_STRING, "int": JSON_TYPE_INTEGER, "float": JSON_TYPE_NUMBER, "bool": JSON_TYPE_BOOLEAN, "list": JSON_TYPE_ARRAY, "dict": JSON_TYPE_OBJECT, "Any": JSON_TYPE_OBJECT, "UUID": JSON_TYPE_STRING}
    if type_str in type_map: return {"type": type_map[type_str]}
    if type_str.startswith(("Optional[", "Union[")) and type_str.endswith("]"):
        is_optional = type_str.startswith("Optional[")
        inner_str = type_str[len("Optional["):-1] if is_optional else type_str[len("Union["):-1]
        types = _split_comma_separated_types(inner_str)
        non_null_types = [t for t in types if t.lower() not in ['none', 'nonetype']]
        return map_type(non_null_types[0]) if non_null_types else {"type": JSON_TYPE_NULL}
    if type_str.startswith(("List[", "list[")) and type_str.endswith("]"):
        return {"type": JSON_TYPE_ARRAY, "items": map_type(type_str[5:-1].strip() or "Any")}
    if type_str.startswith(("Dict[", "dict[")) and type_str.endswith("]"):
         return {"type": JSON_TYPE_OBJECT, "properties": {}}
    return {"type": JSON_TYPE_OBJECT}

def parse_object_properties_from_description(description: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Recursively parses sub-properties from a description string."""
    if not description: return "", None
    prop_regex = re.compile(r"^\s*(?:[-*]\s*)?(?P<name>[\w'\"`]+)\s*\((?P<type>.*?)\):\s*(?P<desc>.*)", re.IGNORECASE)
    def get_indent(line: str) -> int: return len(line) - len(line.lstrip(' '))
    lines = description.splitlines()
    first_prop_index = next((i for i, line in enumerate(lines) if prop_regex.match(line.strip())), -1)
    if first_prop_index == -1: return description, None
    main_description = "\n".join(lines[:first_prop_index]).strip()
    prop_lines = lines[first_prop_index:]
    properties, required = {}, []
    i = 0
    while i < len(prop_lines):
        line = prop_lines[i]
        match = prop_regex.match(line.strip())
        if not match: i += 1; continue
        current_indent = get_indent(line)
        data = match.groupdict()
        name, type_str, desc_on_line = data["name"].strip().strip("'\"`"), data["type"].strip(), data["desc"].strip()
        child_lines = []
        j = i + 1
        while j < len(prop_lines) and (not prop_lines[j].strip() or get_indent(prop_lines[j]) > current_indent):
            child_lines.append(prop_lines[j]); j += 1
        full_prop_description = desc_on_line + "\n" + "\n".join(child_lines)
        if not is_optional_type_string(type_str): required.append(name)
        type_str_cleaned = re.sub(r',?\s*optional\s*', '', type_str, flags=re.IGNORECASE).strip()
        if type_str_cleaned.startswith("Optional["): type_str_cleaned = type_str_cleaned[9:-1]
        elif type_str_cleaned.startswith("Union["):
            non_nulls = [t.strip() for t in _split_comma_separated_types(type_str_cleaned[6:-1]) if t.strip().lower() not in ['none', 'nonetype']]
            type_str_cleaned = non_nulls[0] if non_nulls else "Any"
        prop_schema = map_type(type_str_cleaned)
        sub_main_desc, sub_props_schema = parse_object_properties_from_description(full_prop_description)
        prop_schema["description"] = sub_main_desc.strip()
        if sub_props_schema:
            if prop_schema.get("type") == JSON_TYPE_OBJECT:
                prop_schema.update(sub_props_schema)
            elif prop_schema.get("type") == JSON_TYPE_ARRAY and prop_schema.get("items", {}).get("type") == JSON_TYPE_OBJECT:
                prop_schema["items"].update(sub_props_schema)
        properties[name] = prop_schema
        i = j
    result_schema = {"properties": properties}
    if required: result_schema["required"] = sorted(required)
    return main_description, result_schema

def build_initial_schema(doc: docstring_parser.Docstring, func_node: ast.FunctionDef, func_name: str) -> Dict[str, Any]:
    """Builds the entire initial JSON schema from docstring and AST node."""
    params_with_defaults = set()
    num_pos_args = len(func_node.args.args)
    num_pos_defaults = len(func_node.args.defaults)
    if num_pos_defaults > 0:
        for arg in func_node.args.args[num_pos_args - num_pos_defaults:]: params_with_defaults.add(arg.arg)
    for i, kw_arg in enumerate(func_node.args.kwonlyargs):
        if i < len(func_node.args.kw_defaults) and func_node.args.kw_defaults[i] is not None: params_with_defaults.add(kw_arg.arg)
    
    full_description = "\n\n".join(filter(None, [doc.short_description, doc.long_description]))
    schema = {"name": func_name, "description": full_description, "parameters": {"type": JSON_TYPE_OBJECT, "properties": {}}}
    required_params = []
    for param in doc.params:
        param_schema = map_type(param.type_name)
        main_desc, props_schema = parse_object_properties_from_description(param.description or "")
        param_schema["description"] = main_desc.strip()
        if props_schema:
            if param_schema.get("type") == JSON_TYPE_OBJECT: param_schema.update(props_schema)
            elif param_schema.get("type") == JSON_TYPE_ARRAY and param_schema.get("items", {}).get("type") == JSON_TYPE_OBJECT:
                param_schema["items"].update(props_schema)
        schema["parameters"]["properties"][param.arg_name] = param_schema
        if not (param.arg_name in params_with_defaults or param.is_optional or param.default is not None or is_optional_type_string(param.type_name)):
            required_params.append(param.arg_name)
    if required_params: schema["parameters"]["required"] = sorted(required_params)
    return schema

def process_single_function(args: Tuple[str, str, str]) -> Optional[Dict[str, Any]]:
    """Processes a single function to generate its schema."""
    public_name, fqn, package_root = args
    source_file_path = resolve_function_source_path(fqn, package_root)
    if not source_file_path: return None
    node_info = extract_specific_function_node(source_file_path, fqn)
    if not node_info: return None
    func_node, _ = node_info
    docstring_text = ast.get_docstring(func_node)
    if not docstring_text: return None
    return build_initial_schema(docstring_parser.parse(docstring_text), func_node, public_name)

def generate_package_schema(package_path: str) -> Dict[str, Any]:
    """
    Generates schemas for all functions in a package and returns them as a dictionary.
    """
    package_root = os.path.dirname(os.path.abspath(package_path))
    init_path = os.path.join(package_path, "__init__.py")
    if not os.path.exists(init_path): return {}
    
    function_map = get_variable_from_file(init_path, "_function_map")
    if not function_map: return {}

    all_fqns = list(function_map.values())
    trivial_fqns = set(find_trivial_functions(all_fqns, package_root))
    
    non_trivial_map = {k: v for k, v in function_map.items() if v not in trivial_fqns}
    
    function_args = [(name, fqn, package_root) for name, fqn in non_trivial_map.items()]
    
    all_schemas = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(process_single_function, function_args)
        all_schemas = [s for s in results if s]

    return {schema['name']: schema for schema in all_schemas}
