

import os
import sys
import ast
import json
import docstring_parser
import importlib
from googleapiclient.discovery import build # Not used in the provided snippet, kept if used elsewhere
from googleapiclient.http import MediaFileUpload # Not used, kept
from google.oauth2 import service_account # Not used, kept
from typing import Dict, List, Tuple, Optional, Any, Union, Set # Added Set
import sys
import re # Added for regex in strip_comments

# --- Constants ---
JSON_TYPE_STRING = "string"
JSON_TYPE_INTEGER = "integer"
JSON_TYPE_NUMBER = "number"
JSON_TYPE_BOOLEAN = "boolean"
JSON_TYPE_ARRAY = "array"
JSON_TYPE_OBJECT = "object"
JSON_TYPE_NULL = "null"

OPTIONAL_PREFIX = "Optional["
UNION_PREFIX = "Union["
LITERAL_PREFIX = "Literal["
LIST_PREFIXES = ("List[", "list[")
DICT_PREFIXES = ("Dict[", "dict[")
TUPLE_PREFIXES = ("Tuple[", "tuple[")

DEFAULT_TYPE_MAP: Dict[str, Union[str, Dict]] = {
    "str": JSON_TYPE_STRING, "int": JSON_TYPE_INTEGER, "float": JSON_TYPE_NUMBER,
    "bool": JSON_TYPE_BOOLEAN, "None": JSON_TYPE_NULL, "NoneType": JSON_TYPE_NULL,
    "Any": {}, "object": JSON_TYPE_OBJECT, "list": JSON_TYPE_ARRAY,
    "dict": JSON_TYPE_OBJECT, "tuple": JSON_TYPE_ARRAY, "List": JSON_TYPE_ARRAY,
    "Dict": JSON_TYPE_OBJECT, "Tuple": JSON_TYPE_ARRAY, "UUID": JSON_TYPE_STRING,
}

SECTION_HEADERS_FOR_SAFE_PARSE = {
    "args:", "arguments:", "parameters:", "attributes:", "examples:", "example:",
    "methods:", "note:", "notes:", "raises:", "exceptions:", "return:", "returns:",
    "yields:", "yield:", "warns:", "warnings:", "see also:"
}

DEFAULT_ITEM_BASE_TYPE = JSON_TYPE_OBJECT
PLACEHOLDER_TYPE_FOR_NULL_ENUM = JSON_TYPE_STRING

# --- Helper Functions for filtering trivial (pass) functions ---
def extract_function_map_from_init(init_path: str) -> dict:
    """
    Extracts _function_map from a module's __init__.py using AST.

    Args:
        init_path (str): Path to the __init__.py file.

    Returns:
        dict: Flattened name -> fully qualified name
    """
    with open(init_path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_function_map":
                    return ast.literal_eval(ast.unparse(node.value)) # Python 3.9+

    return {}

def resolve_function_source_path(qualified: str, source_root: str) -> str:
    """
    Convert a qualified path (e.g., 'my_package.my_module.my_function') to a file path
    and return the .py file containing the function.
    """
    parts = qualified.split(".")
    *module_parts, _ = parts
    base_path = os.path.join(source_root, *module_parts)

    module_file = base_path + ".py"
    if os.path.isfile(module_file):
        return module_file
    elif os.path.isdir(base_path):
        init_file = os.path.join(base_path, "__init__.py")
        if os.path.isfile(init_file):
            return init_file
    raise FileNotFoundError(f"Could not resolve source file for {qualified}. Tried: '{module_file}' and '{init_file if 'init_file' in locals() else 'N/A'}'")

def strip_comments(source: str) -> str:
    """
    Strip comments from a Python source code string.
    Removes lines that are entirely comments or inline comments from the end of lines.
    """
    lines = source.splitlines()
    no_comment_lines = []
    for line in lines:
        no_comment = re.sub(r'#.*', '', line)
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
        return strip_comments(source)

    lines = source.splitlines()
    lines_to_exclude = set()

    for node in ast.walk(parsed):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if hasattr(node, 'body') and len(node.body) > 0:
                doc_node = node.body[0]
                if isinstance(doc_node, ast.Expr) and isinstance(doc_node.value, ast.Constant) and isinstance(doc_node.value.value, str):
                    start_line = doc_node.lineno - 1
                    end_line = doc_node.end_lineno - 1

                    for i in range(start_line, end_line + 1):
                        lines_to_exclude.add(i)

    filtered_lines = []
    for i, line in enumerate(lines):
        if i not in lines_to_exclude:
            filtered_lines.append(line)

    return strip_comments('\n'.join(filtered_lines))

def extract_function_source(source: str, func_path: str) -> str:
    """
    Extracts the source code for a function or method from the full module source.
    `func_path` can be: 'function_name' or 'ClassName.method_name'.
    """
    tree = ast.parse(source)

    if "." in func_path:
        class_name, method_name = func_path.split(".")
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for sub_node in node.body:
                    if isinstance(sub_node, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub_node.name == method_name:
                        source_segment = ast.get_source_segment(source, sub_node)
                        if source_segment is None:
                             raise ValueError(f"Could not get source segment for {func_path}")
                        return source_segment
    else:
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_path:
                source_segment = ast.get_source_segment(source, node)
                if source_segment is None:
                    raise ValueError(f"Could not get source segment for {func_path}")
                return source_segment
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
        return True # `return` (without a value)

    if isinstance(value, ast.Constant):
        if value.value is None: return True
        if isinstance(value.value, (str, bytes)) and not value.value: return True
        if isinstance(value.value, (int, float)) and value.value == 0: return True
        if isinstance(value.value, bool) and not value.value: return True # Catches `return False`
    elif isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        if not value.elts: return True
    elif isinstance(value, ast.Dict):
        if not value.keys: return True
    elif isinstance(value, ast.Name) and value.id == 'None': # For older Python versions if Constant isn't used for None
        return True
    return False

def is_function_body_trivial(func_source_code: str) -> bool:
    """
    Analyzes the extracted source code of a single function to determine if its body is trivial.
    Trivial bodies include:
    - Only a `pass` statement.
    - Only a `return` statement (with or without a value, including empty literals).
    - An empty body after stripping comments and docstrings.
    """
    stripped_func_source = strip_comments_and_docstrings(func_source_code)

    if not stripped_func_source.strip():
        return True

    try:
        tree = ast.parse(stripped_func_source)
    except SyntaxError: # If stripping made it invalid, it's likely not "simply pass"
        return False
    except Exception as e: # Catch any other parsing errors
        print(f"⚠️ An unexpected error occurred during AST parsing for triviality check: {e}")
        return False


    function_node = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_node = node
            break

    if not function_node: # Should not happen if func_source_code was valid func code
        return False

    # Consider function body statements, excluding docstrings (already stripped by strip_comments_and_docstrings)
    function_body_statements = function_node.body

    # Filter out any potential lingering string expressions that were not formal docstrings
    effective_statements = []
    for stmt in function_body_statements:
        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
            continue # Skip bare string expressions in the body
        effective_statements.append(stmt)

    if not effective_statements: # Empty body after stripping and filtering
        return True

    if len(effective_statements) == 1:
        stmt = effective_statements[0]
        if isinstance(stmt, ast.Pass):
            return True
        if is_node_trivial_return(stmt):
            return True

    return False

def find_trivial_functions(fq_function_names: List[str], source_root: str) -> List[str]:
    """
    Find trivial functions by analyzing their stripped source code based on AST.
    Trivial functions include those with only 'pass', 'return', 'return None',
    'return []', 'return {}', 'return 0', 'return ""', etc. in their body.
    """
    trivial_functions_list = []

    for fq in fq_function_names:
        try:
            file_path = resolve_function_source_path(fq, source_root)

            fq_parts = fq.split('.')
            module_file_name_from_path = os.path.splitext(os.path.basename(file_path))[0]
            # Determine the part of FQN that is module (e.g. package.module) vs class.method
            # This logic attempts to reconstruct the internal path used by extract_function_source

            # Heuristic: find the module part in FQN
            # e.g. fq = "my_package.my_module.ClassName.method_name", file_path points to my_module.py
            # module_file_name_from_path = "my_module"
            # func_path_relative_to_module should be "ClassName.method_name" or "method_name"

            func_path_parts = []
            # Find where the module name (or package name if it's an __init__.py) ends in the FQN
            # This is a bit tricky if class names match module names, but generally, AST extraction needs this relative path.
            module_name_in_fq_index = -1
            current_module_name_to_match = module_file_name_from_path
            if current_module_name_to_match == "__init__":
                # If it's an __init__.py, the "module" name is the directory name
                current_module_name_to_match = os.path.basename(os.path.dirname(file_path))


            # Try to match module path from right to left in FQ parts
            # Example: fq = `pkg.sub.mod.Class.func`, module is `mod.py` (current_module_name_to_match=`mod`)
            # fq_parts = ["pkg", "sub", "mod", "Class", "func"]
            # We want to find "mod" and take "Class.func"
            idx_module_part = -1
            for i in range(len(fq_parts) -1, -1, -1):
                if fq_parts[i] == current_module_name_to_match:
                    idx_module_part = i
                    break
            
            if idx_module_part != -1 and idx_module_part < len(fq_parts) -1:
                func_path_relative_to_module = ".".join(fq_parts[idx_module_part+1:])
            elif idx_module_part != -1 and idx_module_part == len(fq_parts) -1 : # fq ends with module name (top-level func in module)
                func_path_relative_to_module = fq_parts[-1]
            else: # Fallback or complex case (e.g. function imported into __init__ and re-exported)
                # This might happen if FQN is from _function_map and doesn't directly map to file structure
                # Default to last part, extract_function_source will try to find it.
                print(f"⚠️ Could not precisely determine function path within module for {fq} (module name: {current_module_name_to_match}). Defaulting to last FQDN component: '{fq_parts[-1]}'")
                func_path_relative_to_module = fq_parts[-1]


            with open(file_path, "r", encoding="utf-8") as f:
                full_source = f.read()

            func_source = None
            try:
                func_source = extract_function_source(full_source, func_path_relative_to_module)
                if not func_source: # Should be caught by ValueError in extract_function_source if not found
                    print(f"⚠️ No source extracted for {fq} using path '{func_path_relative_to_module}', possibly malformed or not found; skipping triviality check.")
                    continue
            except ValueError as e: # Raised by extract_function_source if function not found
                print(f"❌ Error extracting function source for {fq} using path '{func_path_relative_to_module}': {e}")
                # This could happen if FQN is an alias or re-export not directly in the resolved file.
                # Or if the relative path logic above isn't perfect for all cases.
                continue
            except Exception as e: # Catch other unexpected errors during extraction
                print(f"❌ Unexpected error during source extraction for {fq}: {e}")
                continue


            if is_function_body_trivial(func_source):
                trivial_functions_list.append(fq)

        except FileNotFoundError as e:
            print(f"❌ File not found for {fq}: {e}") # Expected if FQN is e.g. a built-in or C extension
            continue
        except Exception as e: # Broad catch for other issues like AST parsing errors in called functions
            print(f"❌ An unexpected error occurred while processing {fq} for triviality: {e}")
            continue

    return trivial_functions_list

def get_cleaned_function_bodies(fq_function_names: List[str], source_root: str) -> Dict[str, str]:
    """
    Given a list of fully qualified function names, returns a dictionary where keys are the
    fully qualified names and values are the cleaned source code of the function body.
    The cleaned source code includes only the executable statements, with docstrings,
    comments, and the function definition (e.g., `def ...:`) removed.
    """
    cleaned_bodies = {}

    for fq in fq_function_names:
        try:
            file_path = resolve_function_source_path(fq, source_root)

            # --- Logic to determine func_path_relative_to_module (similar to find_trivial_functions) ---
            fq_parts = fq.split('.')
            module_file_name_from_path = os.path.splitext(os.path.basename(file_path))[0]
            current_module_name_to_match = module_file_name_from_path
            if current_module_name_to_match == "__init__":
                current_module_name_to_match = os.path.basename(os.path.dirname(file_path))
            
            idx_module_part = -1
            for i in range(len(fq_parts) -1, -1, -1):
                if fq_parts[i] == current_module_name_to_match:
                    idx_module_part = i
                    break
            
            if idx_module_part != -1 and idx_module_part < len(fq_parts) -1:
                func_path_relative_to_module = ".".join(fq_parts[idx_module_part+1:])
            elif idx_module_part != -1 and idx_module_part == len(fq_parts) -1 :
                func_path_relative_to_module = fq_parts[-1]
            else:
                print(f"⚠️ Could not precisely determine function path within module for {fq} (module: {current_module_name_to_match}) for body cleaning. Defaulting to last FQDN component: '{fq_parts[-1]}'")
                func_path_relative_to_module = fq_parts[-1]
            # --- End of func_path_relative_to_module logic ---

            with open(file_path, "r", encoding="utf-8") as f:
                full_source = f.read()

            func_source_block = None
            try:
                func_source_block = extract_function_source(full_source, func_path_relative_to_module)
                if not func_source_block:
                    print(f"⚠️ No source extracted for {fq} (path '{func_path_relative_to_module}'), possibly malformed or not found; skipping body cleaning.")
                    continue
            except ValueError as e:
                print(f"❌ Error extracting function source for {fq} (path '{func_path_relative_to_module}') for body cleaning: {e}")
                continue
            except Exception as e:
                print(f"❌ Unexpected error during source extraction for {fq} for body cleaning: {e}")
                continue

            stripped_func_source_block = strip_comments_and_docstrings(func_source_block)

            try:
                tree = ast.parse(stripped_func_source_block) # Parse the stripped block

                function_node = None
                for node_in_block in tree.body: # The block should contain one function def
                    if isinstance(node_in_block, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        function_node = node_in_block
                        break
                
                if not function_node or not function_node.body:
                    cleaned_bodies[fq] = "" # No body or not a function node
                    continue

                # Get lines of the stripped source block (not the original full source)
                source_lines = stripped_func_source_block.splitlines()
                
                # AST nodes have lineno and end_lineno relative to the source they were parsed from.
                # Here, it's relative to stripped_func_source_block.
                # The body starts after the `def ...:` line and its docstring (if any, though stripped).
                
                # We need to extract lines corresponding to the function body statements.
                # function_node.body[0].lineno is the start of the first statement.
                # function_node.body[-1].end_lineno is the end of the last statement.
                
                body_start_lineno_in_block = function_node.body[0].lineno
                body_end_lineno_in_block = function_node.body[-1].end_lineno
                
                # Extract these lines
                body_lines_from_block = source_lines[body_start_lineno_in_block - 1 : body_end_lineno_in_block]

                # De-indent based on the first statement's column offset
                min_indent = function_node.body[0].col_offset
                
                deindented_body_lines = []
                for line in body_lines_from_block:
                    if line.strip(): # Only de-indent non-empty lines
                        if len(line) > min_indent and not line[:min_indent].strip(): # Check if prefix is whitespace
                             deindented_body_lines.append(line[min_indent:])
                        else: # Line is shorter than min_indent or has non-whitespace before it
                             deindented_body_lines.append(line) # Keep as is, or strip if preferred
                    else: # Keep empty lines as they are (or "" if preferred)
                        deindented_body_lines.append(line)


                cleaned_bodies[fq] = '\n'.join(deindented_body_lines)

            except SyntaxError as e:
                print(f"❌ Syntax error parsing stripped function source for {fq} (likely malformed after stripping): {e}. Body set to original stripped block.")
                cleaned_bodies[fq] = stripped_func_source_block # Fallback
                continue
            except Exception as e:
                print(f"❌ Unexpected error processing function body for {fq} for cleaning: {e}. Body set to original stripped block.")
                cleaned_bodies[fq] = stripped_func_source_block # Fallback
                continue

        except FileNotFoundError as e:
            print(f"❌ File not found for {fq} (for body cleaning): {e}")
            continue
        except Exception as e:
            print(f"❌ An unexpected error occurred while processing {fq} for body cleaning: {e}")
            continue

    return cleaned_bodies

# --- Helper Functions for JSON Schema Mapping ---
def _ensure_item_schema_has_type(item_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures that the item schema has a type.
    """
    if not isinstance(item_schema, dict) or not item_schema: # Handles empty or non-dict schema
        return {"type": DEFAULT_ITEM_BASE_TYPE, "description": "Defaulted item type as original was invalid or empty."}
    if "$ref" in item_schema: return item_schema # If it's a reference, assume it's valid
    if isinstance(item_schema.get("type"), str) and item_schema.get("type"): return item_schema # Has a type string
    # If type is missing or not a string (e.g. another dict), add default type, preserving other keys
    return {"type": DEFAULT_ITEM_BASE_TYPE, **item_schema}

def _split_comma_separated_types(params_str: str) -> List[str]:
    """
    Splits a comma-separated string of types into a list of individual types.
    Handles nested generics like Union[List[int], str].
    """
    params = []
    balance = 0 # For brackets like [], (), {}
    current_param_start = 0
    if not params_str: return params
    for i, char in enumerate(params_str):
        if char == '[' or char == '(': balance += 1
        elif char == ']' or char == ')': balance -= 1
        elif char == ',' and balance == 0:
            params.append(params_str[current_param_start:i].strip())
            current_param_start = i + 1
    params.append(params_str[current_param_start:].strip()) # Add the last parameter
    return [p for p in params if p] # Filter out empty strings if any (e.g., "type, ")

def map_type(type_str: Optional[str], type_map: Dict[str, Union[str, Dict]] = DEFAULT_TYPE_MAP) -> Dict[str, Any]:
    """
    Maps a Python type string to a JSON schema type as per the OpenAPI 3.0 specification.
    """
    effective_type_str = (type_str or "").strip()

    if not effective_type_str: # Empty type string
        # Default to 'object' or a more generic representation for "any type"
        return {"type": JSON_TYPE_OBJECT, "description": "Represents any type; schema defaulted to 'object'."}

    # Specific handling for None or NoneType
    if effective_type_str.lower() == "none" or effective_type_str == "NoneType":
        # Representing "only None" which can be done with enum and nullable,
        # but type must be non-null. Using a placeholder type.
        return {"type": PLACEHOLDER_TYPE_FOR_NULL_ENUM, "nullable": True, "enum": [None]}
    if effective_type_str == "{}": # Often used as a hint for "any object" or untyped dict
        return {"type": JSON_TYPE_OBJECT, "description": "Represents any type (from '{}' hint); schema defaulted to 'object'."}


    if effective_type_str.startswith(OPTIONAL_PREFIX) and effective_type_str.endswith("]"):
        inner_type_str = effective_type_str[len(OPTIONAL_PREFIX):-1].strip()
        base_schema: Dict[str, Any]
        if not inner_type_str: base_schema = map_type("Any", type_map) # Optional[] -> Optional[Any]
        else: base_schema = map_type(inner_type_str, type_map)
        # If inner type already implies nullability (e.g. Optional[NoneType]), avoid double marking
        if base_schema.get("nullable") is True: return base_schema
        return {**base_schema, "nullable": True}

    if effective_type_str.startswith(UNION_PREFIX) and effective_type_str.endswith("]"):
        inner_types_str = effective_type_str[len(UNION_PREFIX):-1]
        union_params_list = _split_comma_separated_types(inner_types_str)
        if not union_params_list: return map_type("Any", type_map) # Union[] -> Any

        non_null_types_str: List[str] = []
        is_union_nullable = False
        original_union_hint_parts = [p.strip() for p in union_params_list] # For description

        for t_str_item in union_params_list:
            current_item_str_lower = t_str_item.strip().lower() # Check for 'none' or 'nonetype'
            if current_item_str_lower == "none" or current_item_str_lower == "nonetype":
                 is_union_nullable = True
            else:
                non_null_types_str.append(t_str_item)

        full_original_hint_for_desc = f"Union[{', '.join(original_union_hint_parts)}]"

        # If all types were None, or only None remains
        if not non_null_types_str: return map_type("None", type_map) # e.g., Union[None, NoneType]

        base_schema_for_union: Dict[str,Any]
        additional_description = ""

        if len(non_null_types_str) == 1: # e.g. Union[str, None] -> map_type("str") then add nullable
            base_schema_for_union = map_type(non_null_types_str[0], type_map)
        else: # Multiple non-null types, e.g. Union[str, int, None]
            # OpenAPI's `oneOf` or `anyOf` would be ideal, but for simplicity,
            # we might pick the first type or a common base. Here, pick first.
            # Or, more generally, just use "object" or a generic base type.
            first_type_mapped = map_type(non_null_types_str[0], type_map)
            base_type = first_type_mapped.get("type", JSON_TYPE_OBJECT) # Get type of the first element
            if not isinstance(base_type, str) or not base_type : base_type = JSON_TYPE_OBJECT # Fallback
            base_schema_for_union = {"type": base_type} # Basic schema using the type of the first non-null type

            original_non_null_types_desc = ", ".join(non_null_types_str)
            additional_description = (
                f"Value can be one of several Python types: {original_non_null_types_desc}. "
                f"Schema represents the first type ('{non_null_types_str[0]}') or a generic base due to schema constraints. "
                f"Original hint: {full_original_hint_for_desc}."
            )

        # Merge descriptions
        current_desc = base_schema_for_union.get("description", "")
        if additional_description:
            final_desc = f"{current_desc} {additional_description}".strip() if current_desc and current_desc not in additional_description else additional_description
            base_schema_for_union["description"] = final_desc

        if is_union_nullable:
            if base_schema_for_union.get("nullable") is True: return base_schema_for_union # Already nullable
            # Add nullable and potentially update description if not implied
            current_desc = base_schema_for_union.get("description", "")
            if "can be null" not in current_desc.lower() and "Optional" not in full_original_hint_for_desc: # Avoid redundant phrasing
                 final_desc_with_null = (current_desc + f" The value can also be null (originally part of {full_original_hint_for_desc}).").strip()
                 base_schema_for_union["description"] = final_desc_with_null
            return {**base_schema_for_union, "nullable": True}
        else: # Not nullable
            return base_schema_for_union


    if effective_type_str.startswith(LITERAL_PREFIX) and effective_type_str.endswith("]"):
        enum_values_str = effective_type_str[len(LITERAL_PREFIX):-1]
        enum_params = [v.strip() for v in _split_comma_separated_types(enum_values_str)]
        parsed_enums: List[Any] = []
        for p_item in enum_params:
            if (p_item.startswith("'" ) and p_item.endswith("'")) or \
               (p_item.startswith('"') and p_item.endswith('"')):
                parsed_enums.append(p_item[1:-1]) # Strip quotes for string literals
            else: # Attempt to parse as bool, int, float, None
                try: parsed_enums.append(ast.literal_eval(p_item))
                except (ValueError, SyntaxError): parsed_enums.append(p_item) # Keep as string if unparseable
        enum_type = JSON_TYPE_STRING # Default enum type
        if parsed_enums:
            first_val_type = type(parsed_enums[0])
            if first_val_type is int: enum_type = JSON_TYPE_INTEGER
            elif first_val_type is float: enum_type = JSON_TYPE_NUMBER # Or integer if it's like 1.0
            elif first_val_type is bool: enum_type = JSON_TYPE_BOOLEAN
            # Consider mixed types: OpenAPI requires enum values to be of the same type as schema 'type'
            # If types are mixed, this schema might be problematic for some validators.
            # For simplicity, base type on first element. Add note if mixed.
            if not all(type(val) is first_val_type for val in parsed_enums):
                # This is a simplification; a more robust solution might use oneOf for mixed-type enums
                pass # Keeping it simple, type based on first element.
        return {"type": enum_type, "enum": parsed_enums}

    for prefix in LIST_PREFIXES: # Handles "List[...]" and "list[...]"
        if effective_type_str.startswith(prefix) and effective_type_str.endswith("]"):
            item_type_str = effective_type_str[len(prefix):-1].strip()
            # For List without inner type (e.g. "List[]" - though unusual, treat as List[Any])
            raw_items_schema = map_type(item_type_str if item_type_str else "Any", type_map)
            return {"type": JSON_TYPE_ARRAY, "items": _ensure_item_schema_has_type(raw_items_schema)}

    for prefix in TUPLE_PREFIXES: # Handles "Tuple[...]" and "tuple[...]"
        if effective_type_str.startswith(prefix) and effective_type_str.endswith("]"):
            inner_tuple_str = effective_type_str[len(prefix):-1].strip()
            items_any_schema = _ensure_item_schema_has_type(map_type("Any", type_map)) # Default item for empty/variadic
            if not inner_tuple_str or inner_tuple_str == "...": # Tuple or Tuple[...] -> array of any
                return {"type": JSON_TYPE_ARRAY, "items": items_any_schema}
            # Variadic tuple: Tuple[X, ...]
            if inner_tuple_str.endswith(", ...") or inner_tuple_str.endswith(",..."):
                item_type_str = inner_tuple_str.rsplit(",", 1)[0].strip() # Type before ",..."
                raw_item_schema = map_type(item_type_str, type_map)
                return {"type": JSON_TYPE_ARRAY, "items": _ensure_item_schema_has_type(raw_item_schema)}
            else: # Fixed-length tuple: Tuple[X, Y, Z] -> use prefixItems
                tuple_params = _split_comma_separated_types(inner_tuple_str)
                if not tuple_params: return {"type": JSON_TYPE_ARRAY, "items": items_any_schema} # e.g. Tuple[]
                mapped_params = [_ensure_item_schema_has_type(map_type(t, type_map)) for t in tuple_params]
                return {"type": JSON_TYPE_ARRAY, "prefixItems": mapped_params}


    for prefix in DICT_PREFIXES: # Handles "Dict[...]" and "dict[...]"
        if effective_type_str.startswith(prefix) and effective_type_str.endswith("]"):
            kv_type_str = effective_type_str[len(prefix):-1].strip()
            kv_params = _split_comma_separated_types(kv_type_str)
            key_type_desc, value_type_desc = "string", "any" # Defaults
            if len(kv_params) == 1 and kv_params[0]: # Dict[V] implies Dict[Any, V] or Dict[str, V]
                value_type_desc = kv_params[0]
            elif len(kv_params) == 2: # Dict[K, V]
                key_type_desc = kv_params[0] if kv_params[0] else "string" # Default key type if empty
                value_type_desc = kv_params[1] if kv_params[1] else "any"   # Default value type if empty
            
            # JSON object keys must be strings.
            # additionalProperties can be used for value types if K is str.
            # If K is not str, this is a simplification.
            desc_parts = [f"An object/dictionary. Python type hint indicates keys of type '{key_type_desc}' and values of type '{value_type_desc}'."]
            if key_type_desc.lower() not in ["str", "string", "any"]: # If Python key type isn't string
                 desc_parts.append("Note: JSON object keys are strings;  non-string Python dict keys may require special handling (e.g., stringification).")
            # Using "properties: {}" implies an open object, "additionalProperties: true" is default.
            # To be more specific about value types if key is string-compatible:
            # "additionalProperties": map_type(value_type_desc, type_map)
            return {"type": JSON_TYPE_OBJECT, "properties": {}, "description": " ".join(desc_parts)}


    # Handle built-in generic types like 'dict', 'list', 'tuple' (lowercase)
    type_str_lower = effective_type_str.lower()
    if type_str_lower == "dict": # Untyped dict -> object with any properties
        return {"type": JSON_TYPE_OBJECT, "properties": {}, "description": "A dictionary object with arbitrary key-value pairs (specific key/value types not detailed in this part of the hint)."}
    if type_str_lower == "object": # Explicit 'object' type
        return {"type": JSON_TYPE_OBJECT, "properties": {}, "description": "A generic Python object."}
    if type_str_lower in ["list", "tuple"]: # Untyped list/tuple -> array of any
        return {"type": JSON_TYPE_ARRAY, "items": _ensure_item_schema_has_type(map_type("Any", type_map))}


    # Check direct map after complex types
    mapped_value = type_map.get(effective_type_str) or type_map.get(type_str_lower) # Check case-sensitive then lower
    if mapped_value is not None:
        if isinstance(mapped_value, str): return {"type": mapped_value}
        elif isinstance(mapped_value, dict): # e.g. "Any": {}
             if not mapped_value: return map_type("Any", type_map) # If mapped to empty dict, treat as Any
             return mapped_value # Return the predefined schema dict


    # Fallback for unknown types: assume custom class or unhandled built-in
    # If it starts with an uppercase letter, likely a custom class name.
    if effective_type_str and effective_type_str[0].isupper():
        return {"type": JSON_TYPE_OBJECT, "properties": {}, "description": f"Represents an object of type '{effective_type_str}'."}

    # Final fallback: treat as string with a description of the unresolved type.
    return {"type": JSON_TYPE_STRING, "description": f"Unresolved type: {effective_type_str}"}


def schema_is_nullable(schema: Dict[str, Any]) -> bool:
    """
    Determines if a JSON schema indicates that a value can be null.
    """
    if not isinstance(schema, dict): return False
    if schema.get("nullable") is True: return True
    # Check for the specific 'None' type representation:
    if schema.get("enum") == [None] and schema.get("type") == PLACEHOLDER_TYPE_FOR_NULL_ENUM :
        return True
    # Consider if 'oneOf' or 'anyOf' includes a null type schema (more advanced)
    # For this implementation, 'nullable: True' is the primary indicator.
    return False

# --- Docstring Parsing Logic ---
def safe_parse_docstring(docstring_text: str) -> docstring_parser.Docstring:
    """
    Parses a docstring and returns a Docstring object.
    Attempts to handle common "Args: None" cases gracefully by potentially removing empty sections.
    """
    if not docstring_text: return docstring_parser.parse("", style=docstring_parser.DocstringStyle.GOOGLE)
    lines = docstring_text.splitlines()
    cleaned_lines: List[str] = []
    i = 0
    while i < len(lines):
        line_content = lines[i]
        stripped_line = line_content.strip()
        # Heuristic to remove empty "Args:" sections followed by "None" or another section header immediately.
        if stripped_line.lower() == "args:": # Could extend to other sections if needed
            arg_content_present = False
            next_meaningful_line_idx = -1
            # Look ahead for content under "Args:"
            for j_lookahead in range(i + 1, len(lines)):
                if lines[j_lookahead].strip(): # Found a non-empty line
                    next_meaningful_line_idx = j_lookahead
                    break
            
            if next_meaningful_line_idx != -1:
                next_line_content_stripped = lines[next_meaningful_line_idx].strip()
                # If the next line is indented (param) or not a known header or "None", assume content exists.
                is_indented_param = len(lines[next_meaningful_line_idx]) > len(line_content) # Basic indent check
                if (is_indented_param or next_line_content_stripped.lower() not in SECTION_HEADERS_FOR_SAFE_PARSE) and \
                   next_line_content_stripped.lower() != "none":
                    arg_content_present = True
            
            if arg_content_present:
                cleaned_lines.append(line_content)
            else: # No content, or "None", or followed by another header
                if next_meaningful_line_idx != -1 and \
                   lines[next_meaningful_line_idx].strip().lower() == "none":
                    # Skip "Args:" and the "None" line
                    i = next_meaningful_line_idx
                # If no content and followed by another section, just skip "Args:"
                # The loop structure will handle 'i' increment.
                i += 1
                continue # Skip adding "Args:" to cleaned_lines
        else:
            cleaned_lines.append(line_content)
        i += 1
    
    final_docstring_to_parse = "\n".join(cleaned_lines)
    try:
        return docstring_parser.parse(final_docstring_to_parse, style=docstring_parser.DocstringStyle.GOOGLE)
    except docstring_parser.ParseError: # If cleaning caused error, try original
        try:
            return docstring_parser.parse(docstring_text, style=docstring_parser.DocstringStyle.GOOGLE)
        except docstring_parser.ParseError: # If original also fails, return empty
            return docstring_parser.parse("", style=docstring_parser.DocstringStyle.GOOGLE)


def docstring_to_json_schema(
    docstring_text: str,
    function_name_for_error: str,
    params_with_signature_defaults_set: Optional[Set[str]] = None
) -> Dict[str, Any]:
    """
    Converts a function's docstring into a JSON schema object adhering to specified constraints.
    The 'required' array in parameters is omitted if empty.
    Checks for default values in function signature to determine 'required' status.
    """
    parsed_docstring = safe_parse_docstring(docstring_text)
    effective_params_with_signature_defaults = params_with_signature_defaults_set or set()

    parameters_object: Dict[str, Any] = {"type": JSON_TYPE_OBJECT, "properties": {}}
    required_list: List[str] = []

    # Handle cases where parsing might have issues (e.g., completely malformed docstring)
    if not parsed_docstring and docstring_text: # Docstring existed but parsing failed to extract anything
        # This indicates a severe parsing issue or an unconventional docstring format.
        # Fallback schema:
        return {
            "name": function_name_for_error,
            "description": "Error during docstring parsing or docstring format not fully recognized.",
            "parameters": parameters_object # Empty parameters
        }

    # Combine short and long descriptions
    description_parts = [parsed_docstring.short_description, parsed_docstring.long_description]
    full_description = "\n\n".join(filter(None, description_parts)).strip() # Filter None, join, strip

    schema_output: Dict[str, Any] = {
        "name": function_name_for_error,
        "description": full_description,
        "parameters": parameters_object
    }

    for param in parsed_docstring.params:
        param_schema = map_type(param.type_name) # Get base schema from type hint
        docstring_param_description = (param.description or "").strip()

        # map_type might generate its own description (e.g., for Union, Literal, unresolved types)
        map_type_generated_description = param_schema.pop("description", "") # Remove if exists, to merge manually

        # Merge descriptions: param description from docstring takes precedence or is augmented
        final_merged_description = docstring_param_description
        if map_type_generated_description:
            if final_merged_description: # Both exist
                # Append type-based info in a distinguishable way, e.g., in brackets
                final_merged_description = f"{docstring_param_description} [{map_type_generated_description}]"
            else: # Only map_type generated description exists
                final_merged_description = map_type_generated_description
        
        current_param_schema_for_properties = {**param_schema} # Copy base schema
        current_param_schema_for_properties["description"] = final_merged_description.strip()

        parameters_object["properties"][param.arg_name] = current_param_schema_for_properties

        # Determine if parameter is required
        is_optional_by_docstring_tag = param.is_optional  # e.g. "(optional)" in description parsed by library
        is_optional_by_type_hint = schema_is_nullable(current_param_schema_for_properties) # e.g. Optional[str], Union[str, None]
        has_default_value_in_docstring = param.default is not None # e.g. "Defaults to True" in docstring
        
        # NEW: Check if parameter has a default in the function signature (passed from AST)
        has_default_value_in_signature = param.arg_name in effective_params_with_signature_defaults

        if not (is_optional_by_docstring_tag or \
                is_optional_by_type_hint or \
                has_default_value_in_docstring or \
                has_default_value_in_signature):
            required_list.append(param.arg_name)

    if required_list:
        required_list.sort() # Keep sorted for consistency
        parameters_object["required"] = required_list

    return schema_output

# --- AST Parsing and File/Package Iteration ---
class SchemaExtractor(ast.NodeVisitor):
    """
    A class that extracts docstring schemas from a Python file,
    considering function signature defaults.
    """

    def __init__(self, file_path_for_error_context: str):
        """
        Initializes the SchemaExtractor.
        """
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.current_class_name: Optional[str] = None
        self.file_path_context = file_path_for_error_context

    def _process_function_node(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]):
        """
        Helper to process both FunctionDef and AsyncFunctionDef nodes.
        """
        docstring_text = ast.get_docstring(node)
        if docstring_text: # Only process if there's a docstring
            base_func_name = node.name
            # Construct an internal "qualified name" relative to the file/class context
            internal_qualified_name = f"{self.current_class_name}.{base_func_name}" if self.current_class_name else base_func_name

            params_with_signature_defaults = set()
            args_node = node.args

            # Positional-only and regular arguments with defaults
            all_positional_args = args_node.posonlyargs + args_node.args
            num_defaults_for_positional = len(args_node.defaults)
            if num_defaults_for_positional > 0:
                start_index = len(all_positional_args) - num_defaults_for_positional
                for i in range(start_index, len(all_positional_args)):
                    params_with_signature_defaults.add(all_positional_args[i].arg)
            
            # Keyword-only arguments with defaults
            # kw_defaults is a list of default values; None means no default for that kwonlyarg
            for i, kw_arg_obj in enumerate(args_node.kwonlyargs):
                if i < len(args_node.kw_defaults) and args_node.kw_defaults[i] is not None:
                    params_with_signature_defaults.add(kw_arg_obj.arg)
            
            try:
                self.schemas[internal_qualified_name] = docstring_to_json_schema(
                    docstring_text,
                    internal_qualified_name, # Use internal name for context if schema name is later changed
                    params_with_signature_defaults_set=params_with_signature_defaults
                )
            except Exception as e:
                # Catch errors during schema generation for a specific function
                print(f"Error generating schema for {internal_qualified_name} in {self.file_path_context}: {e}")
                pass


    def visit_ClassDef(self, node: ast.ClassDef):
        """
        Visits a ClassDef node and updates the current class name context.
        """
        outer_class_name = self.current_class_name
        # Nest class names: Outer.Inner
        self.current_class_name = f"{outer_class_name}.{node.name}" if outer_class_name else node.name
        self.generic_visit(node) # Visit methods and nested classes within this class
        self.current_class_name = outer_class_name # Restore context after visiting class body

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """
        Visits a FunctionDef node and extracts the docstring schema.
        """
        self._process_function_node(node)
        # self.generic_visit(node) # Typically not needed unless functions can nest in Python < 3.x ways not common now

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """
        Visits an AsyncFunctionDef node and extracts the docstring schema.
        """
        self._process_function_node(node)
        # self.generic_visit(node)

def extract_docstring_schemas_from_file(file_path: str) -> Dict[str, Any]:
    """
    Extracts docstring schemas from a Python file using SchemaExtractor.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f_in: source_code = f_in.read()
        tree = ast.parse(source_code, filename=file_path) # Provide filename for better error messages
    except (FileNotFoundError, SyntaxError, UnicodeDecodeError) as e:
        # print(f"Skipping file {file_path}: {e}")
        return {}
    except Exception as e: # Catch other potential errors during file read or initial parse
        # print(f"Error processing file {file_path}: {e}")
        return {}
    
    extractor = SchemaExtractor(file_path) # Pass file_path for error context
    extractor.visit(tree)
    return extractor.schemas

def iterate_package(package_dir_path: str,
                    exclude_folders: Optional[List[str]] = None,
                    package_import_prefix: Optional[str] = None,
                    source_root_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Iterates through a package directory and extracts docstring schemas from Python files,
    filtering to include only functions listed in the package's _function_map
    and also filtering out trivial functions.
    """
    all_schemas: Dict[str, Any] = {}
    default_exclusions = ['venv', '.venv', '__pycache__', '.git', '.hg', 'docs', 'tests', 'test', 'Test']
    user_exclusions = exclude_folders or ['SimulationEngine', "Unit Tests"]
    effective_excluded_folders = sorted(list(set(default_exclusions + user_exclusions)))
    
    package_name = os.path.basename(os.path.normpath(package_dir_path))
    import_name = package_import_prefix or package_name
    source_root = source_root_path or os.path.dirname(os.path.abspath(package_dir_path))

    _function_map_from_package: Dict[str, str] = {}
    function_map_lookup: Dict[str, str] = {}
    allowed_fq_names_set: Set[str] = set()

    sys_path_modified = False
    if source_root not in sys.path:
        sys.path.insert(0, source_root)
        sys_path_modified = True

    try:
        package_module = importlib.import_module(import_name)
        if hasattr(package_module, '_function_map') and isinstance(getattr(package_module, '_function_map'), dict):
            _function_map_from_package = getattr(package_module, '_function_map')
            # Invert map for easy lookup: FQN_in_code (value) -> desired_schema_name (key)
            function_map_lookup = {v: k for k, v in _function_map_from_package.items()}
            # Create a set of allowed fully qualified names (the *values* from _function_map)
            allowed_fq_names_set = set(_function_map_from_package.values())
            # print(f"Successfully loaded _function_map for package '{package_root_name}'. {len(allowed_fq_names_set)} functions targeted for schema generation.")
        else:
            print(f"Note: _function_map not found or not a dict in package '{import_name}'.")
            # allowed_fq_names_set remains empty, so no functions will be included
            pass
    except ImportError as e:
        print(f"Note: Could not import package '{import_name}': {e}.")
    finally:
        if sys_path_modified and source_root in sys.path:
            sys.path.remove(source_root)

    if not allowed_fq_names_set:
        print(f"Warning: No functions will be included for '{import_name}'.")
        return {} # Return empty if no functions are allowed

    all_found_fq_names_for_trivial_check: List[str] = []  # Collect FQNs of *allowed* functions for trivial check
    schemas_to_process: Dict[str, Dict[str, Any]] = {} # Store schemas for allowed functions: FQN -> schema_data

    for root_dir, dirs, files in os.walk(package_dir_path, topdown=True):
        dirs[:] = [d for d in dirs if d not in effective_excluded_folders and not d.startswith('.')]
        for file_name in files:
            if file_name.endswith(".py"):
                file_full_path = os.path.join(root_dir, file_name)
                
                # Construct the qualified module name from the file path
                relative_file_path = os.path.relpath(file_full_path, package_dir_path)
                module_path_parts = list(os.path.splitext(relative_file_path)[0].split(os.sep))
                if module_path_parts and module_path_parts[-1] == "__init__":
                    module_path_parts.pop()
                
                qualified_module_name_prefix = import_name
                if module_path_parts and not (len(module_path_parts) == 1 and module_path_parts[0] == ''):
                    qualified_module_name_prefix = f"{import_name}.{'.'.join(module_path_parts)}"

                schemas_in_file = extract_docstring_schemas_from_file(file_full_path)
                for func_name_in_file, schema_data in schemas_in_file.items():
                    fully_qualified_py_name = f"{qualified_module_name_prefix}.{func_name_in_file}"
                    if fully_qualified_py_name in allowed_fq_names_set:
                        all_found_fq_names_for_trivial_check.append(fully_qualified_py_name)
                        schemas_to_process[fully_qualified_py_name] = schema_data

    trivial_functions = set(find_trivial_functions(all_found_fq_names_for_trivial_check, source_root))

    for fq_name, schema_data in schemas_to_process.items():
        if fq_name in trivial_functions:
            continue
        schema_final_name = function_map_lookup.get(fq_name)
        if schema_final_name:
            schema_data["name"] = schema_final_name
            all_schemas[schema_final_name] = schema_data

    if not all_schemas:
        print(f"No non-trivial functions from the _function_map were found for '{import_name}'.")

    return all_schemas


def generate_package_schema(
    package_path: str,
    output_file: Optional[str] = None,
    output_folder_path: Optional[str] = None,
    exclude_folders: Optional[List[str]] = None,
    package_import_prefix: Optional[str] = None,
    source_root_path: Optional[str] = None
) -> str:
    """
    Generates a JSON schema file (as a JSON array) from all docstrings
    in a Python package, filtering out trivial functions.
    Also recursively processes any mutations subfolders.
    """
    if not os.path.isdir(package_path):
        raise NotADirectoryError(f"Package directory not found: {package_path}")

    package_name = os.path.basename(os.path.normpath(package_path))
    effective_output_filename = output_file or f"{package_name}.json" # Default filename if not given

    # Determine final output path
    final_output_path: str
    if output_folder_path: # If a specific output folder is given
        os.makedirs(output_folder_path, exist_ok=True) # Ensure directory exists
        final_output_path = os.path.join(output_folder_path, effective_output_filename)
    else: # Default to current working directory if no folder path given
        final_output_path = os.path.join(os.getcwd(), effective_output_filename)

    # result_dict is: { "schema_name_or_fqn": {schema_object}, ... }
    result_dict = iterate_package(
        package_path,
        exclude_folders=exclude_folders,
        package_import_prefix=package_import_prefix,
        source_root_path=source_root_path
    )

    # Convert dict of schemas to a list of schemas, as per typical package schema output
    result_list = list(result_dict.values())

    # Sort the list of schemas by the 'name' field for consistent output
    result_list.sort(key=lambda schema: schema.get("name", ""))

    with open(final_output_path, "w", encoding="utf-8") as f_out:
        json.dump(result_list, f_out, indent=2, ensure_ascii=False)

    print(f"Schema generated for package '{package_import_prefix or package_name}' and saved to {final_output_path}")

    # --- Handle mutations if present ---
    mutations_dir = os.path.join(package_path, "mutations")
    if os.path.isdir(mutations_dir):
        for mutation_name in os.listdir(mutations_dir):
            if mutation_name.startswith('.') or mutation_name == "__pycache__":
                continue
            mutation_path = os.path.join(mutations_dir, mutation_name)
            if os.path.isdir(mutation_path):
                # Compose import prefix and output folder for mutation
                mutation_import_prefix = f"{package_name}.mutations.{mutation_name}"
                mutation_output_folder = os.path.join(
                    output_folder_path or os.getcwd(), "mutations", mutation_name
                )
                mutation_output_filename = f"{package_name}.json"
                print(f"\nProcessing mutation {mutation_import_prefix}...")
                generate_package_schema(
                    mutation_path,
                    output_folder_path=mutation_output_folder,
                    output_file=mutation_output_filename,
                    package_import_prefix=mutation_import_prefix,
                    source_root_path=source_root_path or os.path.dirname(package_path)
                )

    return final_output_path # Return the path

def update_files_to_schema_folder(service, folder_path, drive_folder_id = ''):
    """
    Update each file in md_files to corresponding file in Drive folder.
    """
    # List all files in local md_files folder
    for filename in os.listdir(folder_path):
        local_file_path = os.path.join(folder_path, filename)
        
        if not os.path.isfile(local_file_path):
            continue  # Skip if it's a folder
        
        # Find the matching file in Drive
        query = f"'{drive_folder_id}' in parents and name = '{filename}' and trashed = false"
        response = service.files().list(q=query, fields="files(id, name)").execute()
        files = response.get('files', [])

        if not files:
            media = MediaFileUpload(local_file_path, resumable=True)
            service.files().create(body={'name': filename, 'parents': [drive_folder_id]}, media_body=media).execute()
            print(f"✅ New File '{filename}' created in Drive folder.")
            continue
        
        file_id = files[0]['id']  # Take the first match

        # Update the file content
        media = MediaFileUpload(local_file_path, resumable=True)
        service.files().update(fileId=file_id, media_body=media).execute()
        
        print(f"⬆️ Updated '{filename}' in Drive.")


def authenticate():
    """Authenticate using service account."""
    try:
        creds_dict = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

if __name__ == "__main__":
    # Define source folder for the APIs
    source_folder = "./APIs"
    if os.path.exists(source_folder):
        source_folder = os.path.abspath(source_folder)

        # Define the output folder for the schemas
        schemas_folder = "./Schemas"
        os.makedirs(schemas_folder, exist_ok=True)

        if os.path.exists(schemas_folder):
            schemas_folder = os.path.abspath(schemas_folder)

        # Create the output folder if it doesn't exist
        os.makedirs(schemas_folder, exist_ok=True)

        # Add the source folder to the Python path to allow for correct imports
        if source_folder not in sys.path:
            sys.path.insert(0, source_folder)

        # Iterate through the packages in the /content/APIs directory
        for package_name in os.listdir(source_folder):
            if package_name.startswith('.') or package_name == "__pycache__":
                continue
            package_path = os.path.join(source_folder, package_name)

            # Check if it's a directory (to avoid processing files)
            if os.path.isdir(package_path):
                # Call the function to generate schema for the current package (mutations handled inside)
                generate_package_schema(package_path, output_folder_path=schemas_folder, source_root_path=source_folder)
        
    else:
        raise FileNotFoundError(f"Source folder not found: {source_folder}")
