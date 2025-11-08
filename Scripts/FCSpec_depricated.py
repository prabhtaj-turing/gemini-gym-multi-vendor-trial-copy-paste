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
from google import genai
import concurrent.futures
import threading
import argparse
from pathlib import Path

# --- Pydantic Validation ---
# Add the common_utils path to sys.path to allow importing the models
current_file_dir = Path(__file__).parent
api_gen_dir = current_file_dir.parent
common_utils_dir = api_gen_dir / "APIs" / "common_utils"
sys.path.append(str(api_gen_dir))
# TODO: Check with @Joseph on this 
#from common_utils.models import CentralConfig, ServiceDocumentationConfig, DocMode

DOC_MODE = "raw_docstring"

# --- Configuration & Constants ---
API_KEY = "API KEY HERE"  # In canvas in api team channel
MAX_WORKERS = 10 # Adjust based on system capabilities
print_lock = threading.Lock()

JSON_TYPE_STRING = "string"
JSON_TYPE_INTEGER = "integer"
JSON_TYPE_NUMBER = "number"
JSON_TYPE_BOOLEAN = "boolean"
JSON_TYPE_ARRAY = "array"
JSON_TYPE_OBJECT = "object"
JSON_TYPE_NULL = "null"
JSON_TYPE_ANY_OF = "anyOf"
JSON_TYPE_BYTES = "string"

# --- Helper Functions ---
# Global variables to track configuration state
_original_doc_mode = DOC_MODE
_applied_config = None
_config_backup = None

def apply_config(config_input: Union[str, dict]) -> bool:
    """
    Applies a configuration to override the default DOC_MODE for specific packages.
    
    Args:
        config_input (Union[str, dict]): Either a path to the configuration JSON file or a config dict
        
    Returns:
        bool: True if configuration was successfully applied, False otherwise
    """
    global _applied_config, _config_backup, DOC_MODE
    
    try:
        # Handle config input - either file path or dict
        if isinstance(config_input, str):
            # Load and validate the configuration file
            with open(config_input, "r") as f:
                config_data = json.load(f)
        elif isinstance(config_input, dict):
            # Use the config dict directly
            config_data = config_input
        else:
            safe_print(f"❌ Invalid config input type: {type(config_input)}. Expected str (file path) or dict")
            return False
        
        # # Validate the structure using Pydantic models
        # validated_config = CentralConfig(**config_data)
        # documentation_config = validated_config.documentation
        
        # if not documentation_config:
        #     safe_print(f"Warning: No 'documentation' section found in config")
        #     return False
        
        # # Backup current configuration
        # _config_backup = {
        #     "doc_mode": DOC_MODE,
        #     "applied_config": _applied_config
        # }
        
        # # Store the applied configuration
        # _applied_config = documentation_config
        
        # if isinstance(config_input, str):
        #     safe_print(f"✅ Configuration applied from {config_input}")
        # else:
        #     safe_print(f"✅ Configuration applied from dict")
        # safe_print(f"   Applied config: {_applied_config}")
        
        return True
        
    except FileNotFoundError:
        safe_print(f"❌ Configuration file not found: {config_input}")
        return False
    except json.JSONDecodeError as e:
        safe_print(f"❌ Invalid JSON in configuration file {config_input}: {e}")
        return False
    except Exception as e:
        safe_print(f"❌ Error applying configuration: {e}")
        return False

def rollback_config() -> bool:
    """
    Reverts the configuration back to the original DOC_MODE for all packages.
    
    Returns:
        bool: True if rollback was successful, False otherwise
    """
    global _applied_config, _config_backup, DOC_MODE
    
    if _config_backup is None:
        safe_print("❌ No configuration to rollback - no config was previously applied")
        return False
    
    # Restore original configuration
    DOC_MODE = _config_backup["doc_mode"]
    _applied_config = _config_backup["applied_config"]
    _config_backup = None
    
    safe_print(f"✅ Configuration rolled back to original DOC_MODE: {DOC_MODE}")
    return True

def get_current_doc_mode(package_name: str) -> str:
    """
    Gets the current doc mode for a specific package, considering applied configuration.
    
    Args:
        package_name (str): Name of the package
        
    Returns:
        str: The doc mode to use for this package
    """
    # If a config was applied, check if this package has a specific doc_mode
    if _applied_config:
        # Check if this package has a specific configuration in services
        if _applied_config.services and package_name in _applied_config.services:
            package_config = _applied_config.services[package_name]
            return package_config.doc_mode.value
        
        # Check if there's a global configuration
        if _applied_config.global_config:
            return _applied_config.global_config.doc_mode.value
    
    # Fall back to the current global DOC_MODE
    return DOC_MODE

def get_config_status() -> Dict[str, Any]:
    """
    Returns the current configuration status.
    
    Returns:
        Dict[str, Any]: Current configuration state
    """
    return {
        "original_doc_mode": _original_doc_mode,
        "current_doc_mode": DOC_MODE,
        "applied_config": _applied_config,
        "has_backup": _config_backup is not None
    }

def safe_print(*args, **kwargs):
    """Thread-safe printing function that uses a lock to prevent output interleaving.
    
    Args:
        *args: Variable length argument list to print
        **kwargs: Arbitrary keyword arguments to pass to print
    """
    with print_lock:
        print(*args, **kwargs)

def clean_description(description: str) -> str:
    """Clean a description by removing newlines and normalizing whitespace.
    
    Args:
        description (str): The description string to clean
        
    Returns:
        str: Cleaned description as a single paragraph
    """
    if not description:
        return ""
    
    # Replace all newlines with spaces
    # cleaned = description.replace('\n', ' ')
    
    cleaned = description
    # Replace multiple consecutive spaces with single space
    # cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Strip leading and trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned

def _reorder_schema_with_description(schema: Dict[str, Any], description: str) -> Dict[str, Any]:
    """Reorder a schema dictionary to place description immediately after type.
    
    Args:
        schema (Dict[str, Any]): The original schema dictionary
        description (str): The description to add
        
    Returns:
        Dict[str, Any]: New schema dictionary with correct field ordering
    """
    if not description:
        return schema
    
    # Create new ordered dictionary
    ordered_schema = {}
    
    # Add type first if it exists
    if "type" in schema:
        ordered_schema["type"] = schema["type"]
    
    # Add description second
    ordered_schema["description"] = description
    
    # Add all other fields in their original order
    for key, value in schema.items():
        if key not in ["type", "description"]:
            ordered_schema[key] = value
    
    return ordered_schema

def get_variable_from_file(filepath: str, variable_name: str) -> Optional[Dict]:
    """Safely extracts a variable from a Python file using AST parsing.
    
    Args:
        filepath (str): Path to the Python file to parse
        variable_name (str): Name of the variable to extract
        
    Returns:
        Optional[Dict]: The value of the variable if found and successfully parsed, None otherwise
    """
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
            if node.target.id == variable_name:
                try: return ast.literal_eval(node.value)
                except (ValueError, SyntaxError): return None
    return None

def resolve_function_source_path(qualified_name: str, package_root: str) -> Optional[str]:
    """Converts a fully qualified name to a file path.
    
    Args:
        qualified_name (str): The fully qualified name of the function (e.g., 'module.submodule.function')
        package_root (str): The root directory of the package
        
    Returns:
        Optional[str]: The resolved file path if found, None otherwise
    """
    parts = qualified_name.split('.')
    # For a qualified name like 'A.B.C', the module path could be 'A/B/C.py' or 'A/B/C/__init__.py'
    # We start from the full path and go backwards.
    for i in range(len(parts), 0, -1):
        module_parts = parts[:i]
        # The rest of the path is the "inner" path to the function/class
        inner_path_parts = parts[i:]
        
        potential_module_path = os.path.join(package_root, *module_parts)
        
        # Check if it's a .py file
        if os.path.isfile(potential_module_path + ".py"):
            return potential_module_path + ".py"
            
        # Check if it's a package directory
        if os.path.isdir(potential_module_path):
            init_file = os.path.join(potential_module_path, "__init__.py")
            if os.path.isfile(init_file):
                # If the qualified name was just the module, this is the file.
                # If there are more parts, the function is inside this file.
                return init_file

    # Fallback for simple cases where the qualified name directly maps
    simple_path = os.path.join(package_root, *parts)
    if os.path.isfile(simple_path + ".py"):
        return simple_path + ".py"
    init_file = os.path.join(simple_path, "__init__.py")
    if os.path.isfile(init_file):
        return init_file
        
    return None

def extract_specific_function_node(filepath: str, fqn: str) -> Optional[Tuple[ast.FunctionDef, str]]:
    """Extracts the AST node and source code of a specific function.
    
    Args:
        filepath (str): Path to the Python file containing the function
        fqn (str): Fully qualified name of the function to extract
        
    Returns:
        Optional[Tuple[ast.FunctionDef, str]]: Tuple containing the function's AST node and source code if found,
                                             None otherwise
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source_code = f.read()
        tree = ast.parse(source_code, filename=filepath)
        target_path = fqn.split('.')
        function_name, class_name = target_path[-1], target_path[-2] if len(target_path) > 1 else None
        module_name = os.path.splitext(os.path.basename(filepath))[0]
        if class_name == module_name: class_name = None
        
        nodes_to_check = tree.body
        if class_name:
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    nodes_to_check = node.body
                    break
        
        for node in nodes_to_check:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                return node, ast.unparse(node)
    except (IOError, SyntaxError): pass
    return None

# --- Deterministic Schema Building Logic ---

def _split_comma_separated_types(params_str: str) -> List[str]:
    """Splits a comma-separated string of types while respecting nested brackets.
    
    Args:
        params_str (str): String containing comma-separated types
        
    Returns:
        List[str]: List of individual type strings
    """
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
    """Check if a type string represents an optional type.
    
    Args:
        type_str (Optional[str]): Python type string to check
        
    Returns:
        bool: True if the type is optional (Optional[T] or Union[T, None])
    """
    if not type_str:
        return False
    
    type_str = type_str.strip()
    type_str = type_str.strip("()").strip()
    
    # Check for Optional[T] - may have additional metadata after the closing bracket
    if type_str.startswith("Optional["):
        # Find the matching closing bracket
        bracket_count = 0
        for i, char in enumerate(type_str[9:], start=9):  # Start after "Optional["
            if char == '[':
                bracket_count += 1
            elif char == ']':
                if bracket_count == 0:
                    # Found the matching closing bracket for Optional
                    return True
                bracket_count -= 1
    
    # Check for Union[T, None] or Union[None, T] - may have additional metadata
    if type_str.startswith("Union["):
        # Find the matching closing bracket
        bracket_count = 0
        end_pos = -1
        for i, char in enumerate(type_str[6:], start=6):  # Start after "Union["
            if char == '[':
                bracket_count += 1
            elif char == ']':
                if bracket_count == 0:
                    # Found the matching closing bracket for Union
                    end_pos = i
                    break
                bracket_count -= 1
        
        if end_pos > 6:
            inner_str = type_str[6:end_pos]  # Extract content between Union[ and ]
            types = _split_comma_separated_types(inner_str)
            # Check if any type is None or NoneType
            if any(t.strip().lower() in ['none', 'nonetype'] for t in types):
                return True
    
    # 3. As a final check, look for the format "(..., optional)"
    # This logic runs only if the string is NOT a standard Optional/Union.
    
    # Check if stripping parens changed the string, ensuring it was parenthesized.
    inner_parts = type_str.split(',')
    if any(part.strip().lower() == 'optional' for part in inner_parts):
        return True
        
    return False

# --- Type Mapping Constants ---
TYPE_MAP = {
    "str": JSON_TYPE_STRING, 
    "bytes": JSON_TYPE_BYTES,  # Add bytes mapping to string type
    "int": JSON_TYPE_INTEGER, 
    "float": JSON_TYPE_NUMBER, 
    "bool": JSON_TYPE_BOOLEAN, 
    "list": JSON_TYPE_ARRAY, 
    "List": JSON_TYPE_ARRAY,  # Handle both lowercase and uppercase
    "tuple": JSON_TYPE_ARRAY, 
    "Tuple": JSON_TYPE_ARRAY,  # Handle both lowercase and uppercase
    "dict": JSON_TYPE_OBJECT, 
    "Dict": JSON_TYPE_OBJECT,  # Handle both lowercase and uppercase
    "Any": JSON_TYPE_OBJECT,
    "UUID": JSON_TYPE_STRING  # UUID should be represented as string in JSON schema
}

# --- Type Pattern Constants ---
UNION_PREFIX = "Union["
OPTIONAL_PREFIX = "Optional["
LIST_PREFIX = "List["
LIST_BUILTIN_PREFIX = "list["
TUPLE_PREFIX = "Tuple["
TUPLE_BUILTIN_PREFIX = "tuple["
DICT_PREFIX = "Dict["
DICT_BUILTIN_PREFIX = "dict["
LITERAL_PREFIX = "Literal["

def _extract_generic_inner_type(type_str: str, prefix: str) -> str:
    """Extract the inner type from a generic type string.
    
    Args:
        type_str (str): The generic type string (e.g., "List[str]")
        prefix (str): The prefix to remove (e.g., "List[")
        
    Returns:
        str: The inner type without the generic wrapper, or empty string if none
    """
    inner = type_str[len(prefix):-1].strip()
    return inner  # Don't fallback to "Any" - let caller handle empty case

def _handle_union_type(type_str: str) -> Dict[str, Any]:
    """Handle Union type mapping with JSON_TYPE_ANY_OF schema."""
    inner_str = _extract_generic_inner_type(type_str, UNION_PREFIX)
    
    if not inner_str or inner_str.strip() == "":
        return {"type": JSON_TYPE_NULL}
    
    types = _split_comma_separated_types(inner_str)
    non_null_types = [t for t in types if t.strip().lower() not in ['none', 'nonetype']]
    
    if not non_null_types:
        return {"type": JSON_TYPE_NULL}
    
    # Revert Any to previous logic
    if non_null_types: 
        return map_type(non_null_types[0])
    
    return {"type": JSON_TYPE_NULL}

def _handle_optional_type(type_str: str) -> Dict[str, Any]:
    """Handle Optional type mapping.
    
    Args:
        type_str (str): Optional type string (e.g., "Optional[str]")
        
    Returns:
        Dict[str, Any]: JSON schema for the Optional type
    """
    inner_str = _extract_generic_inner_type(type_str, OPTIONAL_PREFIX)
    
    # Handle empty Optional[] case
    if not inner_str or inner_str.strip() == "":
        return {"type": JSON_TYPE_NULL}
    
    types = _split_comma_separated_types(inner_str)
    non_null_types = [t for t in types if t.strip().lower() not in ['none', 'nonetype']]
    
    if non_null_types:
        # For Optional[T], return the same schema as T
        # The "optional" nature is handled in the required parameter logic, not in the schema
        inner_schema = map_type(non_null_types[0])
        return inner_schema
    
    else:
        return {"type": JSON_TYPE_NULL}

def _handle_list_type(type_str: str) -> Dict[str, Any]:
    """Handle List type mapping.
    
    Args:
        type_str (str): List type string (e.g., "List[str]" or "list[str]")
        
    Returns:
        Dict[str, Any]: JSON schema for the List type
    """
    if type_str.startswith(LIST_PREFIX):
        item_type = _extract_generic_inner_type(type_str, LIST_PREFIX)
    else:  # list[
        item_type = _extract_generic_inner_type(type_str, LIST_BUILTIN_PREFIX)
    
    # If item_type is empty (e.g., just "List" without brackets), provide empty object
    if not item_type or item_type.strip() == "":
        return {"type": JSON_TYPE_ARRAY, "items": {}}
    
    return {"type": JSON_TYPE_ARRAY, "items": map_type(item_type)}

def _handle_tuple_type(type_str: str) -> Dict[str, Any]:
    """Handle Tuple type mapping.
    
    Args:
        type_str (str): Tuple type string (e.g., "Tuple[str, int]" or "tuple[str, int]")
        
    Returns:
        Dict[str, Any]: JSON schema for the Tuple type
    """
    if type_str.startswith(TUPLE_PREFIX):
        item_type = _extract_generic_inner_type(type_str, TUPLE_PREFIX)
    else:  # tuple[
        item_type = _extract_generic_inner_type(type_str, TUPLE_BUILTIN_PREFIX)
    
    # If item_type is empty (e.g., just "Tuple" without brackets), provide empty object
    if not item_type or not item_type.strip() == "":
        return {"type": JSON_TYPE_ARRAY, "items": {}}
    
    return {"type": JSON_TYPE_ARRAY, "items": map_type(item_type)}

def _handle_dict_type(type_str: str) -> Dict[str, Any]:
    """
    Handle Dict type mapping to produce a schema that allows properties to be added later.
    
    Args:
        type_str (str): Dict type string (e.g., "Dict[str, Any]" or "dict[str, Any]")
        
    Returns:
        Dict[str, Any]: JSON schema for the Dict type
    """
    return {"type": JSON_TYPE_OBJECT, "properties": {}, "required": []}

def _handle_literal_type(type_str: str) -> Dict[str, Any]:
    """Handle Literal type mapping.
    
    Args:
        type_str (str): Literal type string (e.g., "Literal['success', 'error']")
        
    Returns:
        Dict[str, Any]: JSON schema for the Literal type
    """
    inner_str = _extract_generic_inner_type(type_str, LITERAL_PREFIX)
    
    # Determine base type from literal values
    if any(char.isdigit() for char in inner_str):
        return {"type": JSON_TYPE_INTEGER}
    elif any(char in ["'", '"'] for char in inner_str):
        return {"type": JSON_TYPE_STRING}
    else:
        return {"type": JSON_TYPE_STRING}

def _handle_forward_reference(type_str: str) -> Dict[str, Any]:
    """Handle forward reference type mapping.
    
    Args:
        type_str (str): Forward reference string (e.g., "'List[str]'")
        
    Returns:
        Dict[str, Any]: JSON schema for the forward reference type
    """
    inner_type = type_str[1:-1]  # Remove quotes
    return map_type(inner_type)

def map_type(type_str: Optional[str]) -> Dict[str, Any]:
    """Maps a Python type string to a JSON schema object.
    
    This function handles various Python type annotations including:
    - Basic types (str, bytes, int, float, bool, list, dict, Any)
    - Typing module types (Union, Optional, List, Tuple, Dict, Literal)
    - Built-in generic types (list, tuple, dict)
    - Forward references (quoted type names)
    - Parenthesized types ((bytes), (str), etc.)
    
    Args:
        type_str (Optional[str]): Python type string to map
        
    Returns:
        Dict[str, Any]: JSON schema object representing the type
        
    Examples:
        >>> map_type("str")
        {'type': 'string'}
        >>> map_type("bytes")
        {'type': 'string'}
        >>> map_type("(bytes)")
        {'type': 'string'}
        >>> map_type("Union[str, int, None]")
        {'type': 'string'}
        >>> map_type("List[str]")
        {'type': 'array', 'items': {'type': 'string'}}
        >>> map_type("'MyClass'")
        {'type': 'object'}
    """
    # Handle None/empty input
    if not type_str:
        return {"type": JSON_TYPE_OBJECT, "properties": {}, "required": []}
    
    type_str = type_str.strip()
    
    # Check basic type mapping first
    if type_str in TYPE_MAP:
        # Special handling for List, list, Tuple, tuple without brackets
        if type_str in ["List", "list", "Tuple", "tuple"]:
            return {"type": TYPE_MAP[type_str], "items": {}}
        # Special handling for Dict, dict, Any without brackets
        elif type_str in ["Dict", "dict", "Any"]:
            return {"type": TYPE_MAP[type_str], "properties": {}, "required": []}
        return {"type": TYPE_MAP[type_str]}
    
    # Handle forward references (quoted type names) - check early
    if type_str.startswith("'") and type_str.endswith("'"):
        return _handle_forward_reference(type_str)
    
    # Handle Optional types (check before Union and other generic types)
    # Note: Optional[T] returns the same schema as T, but affects required parameter logic
    if type_str.startswith(OPTIONAL_PREFIX):
        return _handle_optional_type(type_str)
    
    # Handle Union types (check before bracket validation)
    if type_str.startswith(UNION_PREFIX):
        return _handle_union_type(type_str)
    
    # Handle generic types with brackets
    if not type_str.endswith("]"):
        return {"type": JSON_TYPE_OBJECT, "properties": {}, "required": []}
    
    # Handle List types
    if type_str.startswith(LIST_PREFIX) or type_str.startswith(LIST_BUILTIN_PREFIX):
        return _handle_list_type(type_str)
    
    # Handle Tuple types
    if type_str.startswith(TUPLE_PREFIX) or type_str.startswith(TUPLE_BUILTIN_PREFIX):
        return _handle_tuple_type(type_str)
    
    # Handle Dict types
    if type_str.startswith(DICT_PREFIX) or type_str.startswith(DICT_BUILTIN_PREFIX):
        return _handle_dict_type(type_str)
    
    # Handle Literal types
    if type_str.startswith(LITERAL_PREFIX):
        return _handle_literal_type(type_str)
    
    # Fallback for unrecognized types (custom classes, etc.)
    return {"type": JSON_TYPE_OBJECT, "properties": {}, "required": []}

def parse_object_properties_from_description(description: str, description_stack: Optional[Dict[int, List[Dict[str, Any]]]] = None) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Parses sub-properties from a description string, preserving any lines
    that are not valid property definitions as part of the main description.
    Uses a dictionary of stacks approach with indentation levels as keys and stacks as values,
    ensuring continuation lines are assigned to the correct parent property.
    Supports recursion through the description_stack parameter.
    """
    if not description:
        return "", None

    def get_indent(line: str) -> int:
        """Get the indentation level of a line."""
        return len(line) - len(line.lstrip(' '))
    
    def is_property_definition(line: str) -> bool:
        """Check if a line is a property definition like '- name (type): description' or 'name (type): description'."""
        stripped = line.strip()
        
        # Handle both formats: with or without leading dash
        content = stripped
        if stripped.startswith('-'):
            # Remove the leading dash if present
            content = stripped[1:].strip()
        
        # Must have parentheses with type and colon with description
        # The key is the pattern: name (type): description
        if '(' in content and '):' in content:
            # Find the first '):' sequence, then find the matching '(' before it
            close_paren = content.find('):')
            if close_paren != -1:
                # Look for the matching opening parenthesis before the closing one
                open_paren = content.rfind('(', 0, close_paren)
                if open_paren != -1 and open_paren < close_paren:
                    # Check that there's content between parentheses (the type)
                    type_content = content[open_paren + 1:close_paren].strip()
                    # Also check that there's a name before the parentheses
                    name_part = content[:open_paren].strip()
                    
                    # Validate that the name part is a valid Python variable name
                    # Property names must be valid Python identifiers (single word, no spaces)
                    if type_content and name_part:
                        # Remove quotes if present to get the actual property name
                        actual_name = name_part
                        if ((name_part.startswith('"') and name_part.endswith('"')) or 
                            (name_part.startswith("'") and name_part.endswith("'")) or
                            (name_part.startswith("`") and name_part.endswith("`"))):
                            actual_name = name_part[1:-1]
                        
                        # Check if the actual property name is a valid Python identifier
                        # This automatically rejects names with spaces, special characters, etc.
                        if actual_name.isidentifier():
                            return True
                        else:
                            return False
        return False
    
    def parse_property_definition(line: str) -> Tuple[str, str, str]:
        """Parse a property definition line to extract name, type, and description."""
        stripped = line.strip()
        
        # Handle both formats: with or without leading dash
        content = stripped
        if stripped.startswith('-'):
            # Remove leading dash if present
            content = stripped[1:].strip()
        
        # Find the colon that separates type from description
        colon_pos = content.find('):')
        if colon_pos == -1:
            return None, None, None
        
        # Extract the part before the colon
        before_colon = content[:colon_pos + 1].strip()
        
        # Find the opening parenthesis
        paren_pos = before_colon.rfind('(')
        if paren_pos == -1:
            return None, None, None
        
        # Extract name, type, and description
        name = _clean_property_name(before_colon[:paren_pos].strip())
        type_str = before_colon[paren_pos + 1:-1].strip()  # Remove parentheses
        description = content[colon_pos + 2:].strip()  # After '):'
        
        return name, type_str, description

    def process_property(property_data: Dict[str, Any], properties: Dict[str, Any], required: List[str]) -> None:
        """Helper function to process a property and add it to the properties dict."""
        name = property_data['name']
        type_str = property_data['type_str']
        desc_on_line = property_data['desc_on_line']
        continuation_lines = property_data['continuation_lines']
        
        # Combine the description from the property line with all continuation lines
        full_description = desc_on_line
        if continuation_lines:
            # Add a space if the description doesn't end with a space
            if desc_on_line and not desc_on_line.endswith(' '):
                full_description += '\n '
            # Join all continuation lines, preserving indentation but filtering out empty ones
            continuation_text = '\n'.join(line.rstrip() for line in continuation_lines if line.strip())
            if continuation_text:
                full_description += continuation_text
        
        # Determine if the property is required
        is_optional_by_type = is_optional_type_string(type_str)
        if not is_optional_by_type:
            required.append(name)
        
        # Clean the type string
        if type_str.startswith("Optional[") and type_str.endswith("]"):
            type_str_cleaned = type_str[9:-1].strip()
        elif type_str.startswith("Union[") and type_str.endswith("]"):
            inner_str = type_str[6:-1]
            types = _split_comma_separated_types(inner_str)
            non_null_types = [t.strip() for t in types if t.strip().lower() not in ['none', 'nonetype']]
            type_str_cleaned = non_null_types[0] if non_null_types else "Any"
        else:
            # Use proper comma splitting that respects nested brackets
            types = _split_comma_separated_types(type_str)
            if len(types) > 1:
                type_str_cleaned = types[0].strip()
            else:
                type_str_cleaned = re.sub(r',?\s*(optional|required)\s*', '', type_str, flags=re.IGNORECASE).strip()
        
        # Create the property schema
        prop_schema = map_type(type_str_cleaned)
        
        # Handle nested properties if this property has them
        if 'nested_properties' in property_data and property_data['nested_properties']:
            prop_schema["properties"] = property_data['nested_properties']
            if 'nested_required' in property_data and property_data['nested_required']:
                # Remove duplicates while preserving order
                seen = set()
                prop_schema["required"] = [param for param in property_data['nested_required'] if not (param in seen or seen.add(param))]
        # Recursively parse nested properties if this is an object type
        elif prop_schema.get("type") == JSON_TYPE_OBJECT:
            sub_main_desc, sub_props_schema = parse_object_properties_from_description(full_description, description_stack)
            prop_schema = _reorder_schema_with_description(prop_schema, clean_description(sub_main_desc))
            if sub_props_schema:
                prop_schema["properties"] = sub_props_schema.get("properties", {})
                if sub_props_schema.get("required"):
                    prop_schema["required"] = sub_props_schema.get("required")
        elif prop_schema.get("type") == JSON_TYPE_ARRAY and prop_schema.get("items", {}).get("type") == JSON_TYPE_OBJECT:
            sub_main_desc, sub_props_schema = parse_object_properties_from_description(full_description, description_stack)
            prop_schema = _reorder_schema_with_description(prop_schema, clean_description(sub_main_desc))
            if sub_props_schema:
                prop_schema["items"]["properties"] = sub_props_schema.get("properties", {})
                if sub_props_schema.get("required"):
                    prop_schema["items"]["required"] = sub_props_schema.get("required")
        else:
            # For primitive types, just set the description
            prop_schema = _reorder_schema_with_description(prop_schema, clean_description(full_description))
        
        properties[name] = prop_schema

    # Initialize the description stack if not provided
    if description_stack is None:
        description_stack = {}
    
    lines = description.splitlines()
    properties = {}
    required = []
    unconsumed_lines = []
    
    # Dictionary to track properties by indentation level
    # Key: indentation level (number of spaces), Value: dict with 'stack' (list of properties) and 'spaces' (number of spaces)
    indentation_levels = {}
    
    # Track previous indentation level for continuation lines
    # None when a valid property is encountered, set to indentation level when continuation line is encountered
    previous_continuation_indent = None
    last_continuation_property = None
    
    i = 0
    while i < len(lines):
        line = lines[i]
        line_stripped = line.strip()
        line_indent = get_indent(line)
        
        # Skip empty lines
        if not line_stripped:
            # Add empty lines to the current property if we have one
            # Use previous continuation logic if we're in a continuation sequence
            if previous_continuation_indent is not None and last_continuation_property is not None:
                if 'continuation_lines' not in last_continuation_property:
                    last_continuation_property['continuation_lines'] = []
                last_continuation_property['continuation_lines'].append(line)
            else:
                # Find the property with the highest indentation level that's less than or equal to current line
                current_property = None
                max_indent = -1
                for indent_level in indentation_levels:
                    if indent_level <= line_indent and indent_level > max_indent:
                        if indentation_levels[indent_level]['stack']:  # Check if stack is not empty
                            max_indent = indent_level
                            current_property = indentation_levels[indent_level]['stack'][-1]  # Get the latest property
                
                if current_property:
                    if 'continuation_lines' not in current_property:
                        current_property['continuation_lines'] = []
                    current_property['continuation_lines'].append(line)
                else:
                    unconsumed_lines.append(line)
            i += 1
            continue
        
        # Check if this is a property definition
        if is_property_definition(line):
            # Reset previous continuation tracking when we encounter a valid property
            previous_continuation_indent = None
            last_continuation_property = None
            
            # Parse the property definition
            name, type_str, desc_on_line = parse_property_definition(line)
            
            if name and type_str:
                # Create property data structure
                property_data = {
                    'name': name,
                    'type_str': type_str,
                    'desc_on_line': desc_on_line,
                    'indent': line_indent,
                    'line_number': i,  # Track line number for ordering
                    'continuation_lines': []
                }
                
                # Initialize the indentation level if it doesn't exist
                if line_indent not in indentation_levels:
                    indentation_levels[line_indent] = {
                        'stack': [],
                        'spaces': line_indent
                    }
                
                # Add this property to its indentation level
                indentation_levels[line_indent]['stack'].append(property_data)
                
                i += 1
            else:
                # Invalid property line, treat as unconsumed
                unconsumed_lines.append(line)
                i += 1
        else:
            # This is not a property line - it's continuation content
            target_property = None
            use_dict_of_stacks = True  # Flag to determine if we should use dict of stacks logic
            
            # If we have a previous continuation line, check if this should continue with the same property
            if previous_continuation_indent is not None:
                # If current line has more indentation than previous continuation, continue with same target
                if line_indent > previous_continuation_indent:
                    target_property = last_continuation_property  # Could be None for main description
                    use_dict_of_stacks = False  # Don't use dict of stacks, we have a target from continuation logic
                    # Don't reset the continuation tracking - we're continuing the chain
                else:
                    # Current line has less or equal indentation, need to find new target based on dict of stacks
                    previous_continuation_indent = None
                    last_continuation_property = None
                    target_property = None  # Will be determined by dict of stacks logic below
                    use_dict_of_stacks = True
            
            # If no target from continuation logic, use dict of stacks
            if use_dict_of_stacks:
                # Find the appropriate property to add this continuation to
                # Look for the property with the highest indentation level that's LESS THAN the current line
                # This ensures that lines at the same indentation level as properties go to the parent property
                max_indent = -1
                
                for indent_level in indentation_levels:
                    if indent_level < line_indent and indent_level > max_indent:
                        if indentation_levels[indent_level]['stack']:  # Check if stack is not empty
                            max_indent = indent_level
                            target_property = indentation_levels[indent_level]['stack'][-1]  # Get the latest property
            
            if target_property is not None:
                # Add this line as continuation to the target property
                if 'continuation_lines' not in target_property:
                    target_property['continuation_lines'] = []
                target_property['continuation_lines'].append(line)
                
                # Set previous continuation tracking only if we're not already in a continuation chain
                # or if we're starting a new chain
                if previous_continuation_indent is None or last_continuation_property != target_property:
                    previous_continuation_indent = line_indent
                    last_continuation_property = target_property
            else:
                # This line goes to main description (target_property is None)
                unconsumed_lines.append(line)
                # Set previous continuation tracking for main description only if we're not already in a continuation chain
                # or if we're starting a new chain
                if previous_continuation_indent is None or last_continuation_property is not None:
                    previous_continuation_indent = line_indent
                    last_continuation_property = None  # None indicates main description
            i += 1
    
        # Process all properties from all indentation levels
    # Process from lowest to highest indentation to build hierarchy correctly
    sorted_levels = sorted(indentation_levels.keys())
    
    # First pass: process all properties into a flat structure
    all_processed_props = {}
    prop_name_to_keys = {}  # Map property names to their unique keys for lookup
    
    for level in sorted_levels:
        for property_data in indentation_levels[level]['stack']:
            temp_props = {}
            temp_required = []
            process_property(property_data, temp_props, temp_required)
            
            prop_name = property_data['name']
            # Use a unique key that includes line number to handle duplicate names
            unique_key = f"{prop_name}_{property_data.get('line_number', 0)}"
            
            all_processed_props[unique_key] = {
                'schema': temp_props[prop_name],
                'level': level,
                'required': prop_name in temp_required,
                'name': prop_name,
                'property_data': property_data
            }
            
            # Track all keys for each property name
            if prop_name not in prop_name_to_keys:
                prop_name_to_keys[prop_name] = []
            prop_name_to_keys[prop_name].append(unique_key)
    
    # Second pass: build hierarchy by finding parents for each property
    # We need to process properties in the order they appear in the docstring to correctly identify parents
    # Create a list of properties in order of appearance
    ordered_props = []
    for level in sorted_levels:
        for property_data in indentation_levels[level]['stack']:
            ordered_props.append(property_data)
    
    # Sort by line number to maintain order
    ordered_props.sort(key=lambda x: x.get('line_number', 0))
    
    for unique_key, prop_info in all_processed_props.items():
        current_level = prop_info['level']
        current_property_data = prop_info['property_data']
        
        # Find the immediate parent property
        parent_name = None
        best_parent_indent = -1
        best_parent_line = -1
        parent_unique_key = None
        
        # Look for the closest property at a shallower indentation level that comes BEFORE the current property
        # This is the property that should contain the current property
        current_line = current_property_data.get('line_number', 0)
        current_indent = current_property_data['indent']
        
        # Look for a parent candidate that comes before this property
        for parent_candidate in ordered_props:
            parent_line = parent_candidate.get('line_number', 0)
            parent_indent = parent_candidate['indent']
            
            # Parent must come before current property and have shallower indentation
            if (parent_line < current_line and parent_indent < current_indent):
                parent_candidate_name = parent_candidate['name']
                parent_candidate_key = f"{parent_candidate_name}_{parent_line}"
                
                # Check if this parent candidate can contain the current property
                if parent_candidate_key in all_processed_props:
                    parent_schema = all_processed_props[parent_candidate_key]['schema']
                    
                    # Object types can contain other properties directly
                    # Array types with object items can contain properties in their items
                    can_be_parent = False
                    if parent_schema.get('type') == 'object':
                        can_be_parent = True
                    elif parent_schema.get('type') == 'array' and parent_schema.get('items', {}).get('type') == 'object':
                        can_be_parent = True
                    
                    if can_be_parent:
                        # Check if this parent is closer than any previously found parent
                        # First prioritize by indentation (higher = closer), then by line number (higher = more recent)
                        is_better_parent = False
                        if parent_indent > best_parent_indent:
                            is_better_parent = True
                        elif parent_indent == best_parent_indent and parent_line > best_parent_line:
                            # Same indentation level, prefer the more recent (closer) parent
                            is_better_parent = True
                        
                        if is_better_parent:
                            best_parent_indent = parent_indent
                            best_parent_line = parent_line
                            parent_unique_key = parent_candidate_key
        
        if parent_unique_key:
            # Nest this property under its parent
            parent_schema = all_processed_props[parent_unique_key]['schema']
            
            # For object types, nest directly under properties
            if parent_schema.get('type') == 'object':
                if 'properties' not in parent_schema:
                    parent_schema['properties'] = {}
                if 'required' not in parent_schema:
                    parent_schema['required'] = []
                
                parent_schema['properties'][prop_info['name']] = prop_info['schema'] # Use the name from the processed_props dict
                if prop_info['required']:
                    parent_schema['required'].append(prop_info['name']) # Use the name from the processed_props dict
            
            # For array types with object items, nest under items.properties
            elif parent_schema.get('type') == 'array' and parent_schema.get('items', {}).get('type') == 'object':
                if 'properties' not in parent_schema['items']:
                    parent_schema['items']['properties'] = {}
                if 'required' not in parent_schema['items']:
                    parent_schema['items']['required'] = []
                
                parent_schema['items']['properties'][prop_info['name']] = prop_info['schema'] # Use the name from the processed_props dict
                if prop_info['required']:
                    parent_schema['items']['required'].append(prop_info['name']) # Use the name from the processed_props dict
        else:
            # This is a top-level property
            properties[prop_info['name']] = prop_info['schema'] # Use the name from the processed_props dict
            if prop_info['required']:
                required.append(prop_info['name']) # Use the name from the processed_props dict

    # If no properties were parsed, return the original description
    if not properties:
        return clean_description(description), None

    # Create the result schema
    main_description = clean_description("\n".join(unconsumed_lines))
    result_schema = {"properties": properties}
    # Always include the required array, even if empty, to be explicit about requirements
    # Remove duplicates from required list while preserving order
    seen = set()
    result_schema["required"] = [param for param in required if not (param in seen or seen.add(param))]
    
    # Note: Preserving empty required arrays as they may be meaningful in JSON schemas
    # Empty required: [] indicates that no fields are required, which is different from
    # not having a required field at all (which could be ambiguous)
    
    # Previously we cleaned up empty required arrays, but this has been removed
    # to preserve explicit empty required arrays in the schema output

    return main_description, result_schema

def _clean_type_name(type_name: str) -> str:
    """Clean type name by removing parentheses and extra whitespace.
    
    Args:
        type_name (str): Raw type name from docstring
        
    Returns:
        str: Cleaned type name
        
    Examples:
        >>> _clean_type_name("(bytes)")
        "bytes"
        >>> _clean_type_name("(str)")
        "str"
        >>> _clean_type_name("bytes")
        "bytes"
    """
    if not type_name:
        return type_name
    
    # Remove parentheses and clean whitespace
    cleaned = type_name.strip()
    if cleaned.startswith("(") and cleaned.endswith(")"):
        cleaned = cleaned[1:-1].strip()
    
    return cleaned

def _clean_property_name(property_name: str) -> str:
    """Clean property name by removing quotes and extra whitespace.
    
    Args:
        property_name (str): Raw property name from docstring
        
    Returns:
        str: Cleaned property name without quotes
        
    Examples:
        >>> _clean_property_name('"property_name"')
        "property_name"
        >>> _clean_property_name("'property_name'")
        "property_name"
        >>> _clean_property_name("property_name")
        "property_name"
    """
    if not property_name:
        return property_name
    
    # Remove quotes and clean whitespace
    cleaned = property_name.strip()
    # Only remove quotes if we have matching pairs and the string is longer than 2 characters
    if len(cleaned) >= 2:
        if (cleaned.startswith('"') and cleaned.endswith('"')) or (cleaned.startswith("'") and cleaned.endswith("'")) or (cleaned.startswith("`") and cleaned.endswith("`")):
            cleaned = cleaned[1:-1].strip()
    
    return cleaned

def build_initial_schema(doc: docstring_parser.Docstring, func_node: ast.FunctionDef, func_name: str) -> Dict[str, Any]:
    """Builds the entire initial JSON schema from docstring and AST node with raw descriptions.
    
    Args:
        doc (docstring_parser.Docstring): Parsed docstring object
        func_node (ast.FunctionDef): AST node of the function
        func_name (str): Name of the function
        
    Returns:
        Dict[str, Any]: Complete JSON schema for the function
    """
    params_with_defaults = set()
    num_pos_args = len(func_node.args.args)
    num_pos_defaults = len(func_node.args.defaults)
    if num_pos_defaults > 0:
        for arg in func_node.args.args[num_pos_args - num_pos_defaults:]: params_with_defaults.add(_clean_property_name(arg.arg))
    for i, kw_arg in enumerate(func_node.args.kwonlyargs):
        if i < len(func_node.args.kw_defaults) and func_node.args.kw_defaults[i] is not None: params_with_defaults.add(_clean_property_name(kw_arg.arg))

    # --- Start of fix ---
    description_parts = []
    if doc.short_description:
        description_parts.append(doc.short_description)
    if doc.long_description:
        description_parts.append(doc.long_description)
    # Filter out any empty parts and join them cleanly.
    full_description = "\n\n".join(filter(None, description_parts))
    # --- End of fix ---

    schema = {
        "name": func_name,
        "description": clean_description(full_description),
        "parameters": {"type": JSON_TYPE_OBJECT, "properties": {}, "required": []}
    }
    required_params = []

    for param in doc.params:
        # Clean the type name to handle parenthesized types like (bytes)
        cleaned_type_name = _clean_type_name(param.type_name)
        param_schema = map_type(cleaned_type_name)
        
        # Handle different parameter types
        if param_schema.get("type") == JSON_TYPE_ARRAY and param_schema.get("items", {}).get("type") == JSON_TYPE_OBJECT:
            # Handle List[Dict] or List[Object] - parse properties for the items
            main_desc, props_schema = parse_object_properties_from_description(param.description or "")
            param_schema = _reorder_schema_with_description(param_schema, clean_description(main_desc))
            if props_schema:
                param_schema["items"]["properties"] = props_schema.get("properties", {})
                if props_schema.get("required"): param_schema["items"]["required"] = props_schema["required"]
        elif param_schema.get("type") == JSON_TYPE_OBJECT:
            # Handle Dict/Object - parse properties directly
            main_desc, props_schema = parse_object_properties_from_description(param.description or "")
            param_schema = _reorder_schema_with_description(param_schema, clean_description(main_desc))
            if props_schema:
                param_schema["properties"] = props_schema.get("properties", {})
                if props_schema.get("required"): param_schema["required"] = props_schema["required"]
        else:
            # Handle primitive types - just add description
            param_schema = _reorder_schema_with_description(param_schema, clean_description(param.description or ""))
        
        # Clean the parameter name to remove any quotes
        clean_param_name = _clean_property_name(param.arg_name)
        schema["parameters"]["properties"][clean_param_name] = param_schema
        
        has_default = clean_param_name in params_with_defaults
        is_optional_by_docstring = param.is_optional or param.default is not None
        is_optional_by_type = is_optional_type_string(cleaned_type_name)
        is_optional = is_optional_by_docstring or is_optional_by_type
        if not has_default and not is_optional: required_params.append(clean_param_name)

    # Always include the required array, even if empty, to be explicit about requirements
    # Remove duplicates from required list while preserving order
    seen = set()
    schema["parameters"]["required"] = [param for param in required_params if not (param in seen or seen.add(param))]
    return schema


def process_single_function(args: Tuple[str, str, str]) -> Optional[Dict[str, Any]]:
    """Processes a single function to generate its schema.
    
    Args: 
        args (Tuple[str, str, str]): Tuple containing:
            - public_name: The public name of the function
            - fqn: Fully qualified name of the function
            - package_root: Root directory of the package
            
    Returns:
        Optional[Dict[str, Any]]: The generated schema if successful, None otherwise
    """
    public_name, fqn, package_root = args

    source_file_path = resolve_function_source_path(fqn, package_root)
    if not source_file_path: return None
    
    node_info = extract_specific_function_node(source_file_path, fqn)
    if not node_info: return None
    func_node, func_src = node_info
    
    docstring_text = ast.get_docstring(func_node)
    if not docstring_text: return None
    parsed_docstring = docstring_parser.parse(docstring_text)

    schema = build_initial_schema(parsed_docstring, func_node, public_name)
    
    type_ = DOC_MODE
    if type_ not in ["concise", "medium_detail", "raw_docstring"]:
        safe_print(f"  - Using raw docstring descriptions for '{public_name}'.")
        return schema

    if type_ != "raw_docstring":
        print("Use agentic_fcspec.py to generate the schema for", public_name)

    # safe_print(f"  ✅ Success! Schema generated for '{public_name}'.")
    return schema

def generate_package_schema(package_path: str,
                            output_folder_path: str, 
                            doc_mode = DOC_MODE,
                            package_import_prefix: Optional[str] = None,
                            output_file_name: Optional[str] = None,
                            source_root_path: Optional[str] = None):
    """Generates schemas for all functions in a package.
    
    Args:
        package_path (str): Path to the Python package directory
        output_folder_path (str): Path to the output folder for schema files
        package_import_prefix (str, optional): The prefix to use for package imports. Defaults to None.
        output_file_name (str, optional): The name of the output file. Defaults to None.
        source_root_path (str, optional): The root path for resolving source files. Defaults to None.
    """
    if doc_mode not in ["concise", "medium_detail", "raw_docstring"]:
        safe_print(f"Error: Invalid DOC_MODE: {doc_mode}")
        return
    package_root = source_root_path or os.path.dirname(os.path.abspath(package_path))
    package_name = os.path.basename(package_path)
    
    # Use the provided import prefix or default to the package name
    import_name = package_import_prefix or package_name
    
    init_path = os.path.join(package_path, "__init__.py")
    if not os.path.exists(init_path):
        safe_print(f"Error: __init__.py not found in {package_path}")
        return
    
    if doc_mode == "concise":
        filename = f"concise_{package_name}.json"
    elif doc_mode == "medium_detail":
        filename = f"medium_detail_{package_name}.json"
    else: # raw_docstring
        filename = f"{package_name}.json"

    # output_file_name = f"{package_name}.json"
    # output_file = os.path.join(output_folder_path, output_file_name)
    if output_file_name:
        output_file = os.path.join(output_folder_path, output_file_name)
    else:
        output_file = os.path.join(output_folder_path, filename)

    # Save schema to simulation engine folder if it exists
    if "SimulationEngine" in os.listdir(package_path) and doc_mode != "raw_docstring":
        simulation_engine_path = os.path.join(package_path, "SimulationEngine")
        agentic_scripts_path = os.path.join(simulation_engine_path, "alternate_fcds")
        file_path = os.path.join(agentic_scripts_path, filename)

        # If file path does not exist, print error
        if not os.path.exists(file_path):
            safe_print(f"Error: {doc_mode} schema does not exist for {package_name}, use agentic_fcspec.py to generate the schema")
            return
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        # Copy file in file_path to output_file
        shutil.copy(file_path, output_file)
        safe_print(f"✅ {package_name} Schema generation complete: {output_file}\n")

    elif doc_mode == "raw_docstring":
        function_map = get_variable_from_file(init_path, "_function_map")
        if not function_map:
            safe_print(f"Error: Could not find a valid _function_map in {init_path}.")
            return

        # Adjust the FQNs with the import prefix if provided
        adjusted_function_map = {name: fqn for name, fqn in function_map.items()}
        
        function_args = [(name, fqn, package_root) for name, fqn in adjusted_function_map.items()]
        
        all_schemas = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = executor.map(process_single_function, function_args)
            all_schemas = [s for s in results if s]

        if all_schemas:
            all_schemas.sort(key=lambda x: x.get('name', ''))
            

            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_schemas, f, indent=2, ensure_ascii=False)
            safe_print(f"✅ {import_name} Schema generation complete: {output_file}\n")
        else:
            safe_print(f"\n❌ No schemas were generated for {import_name}.")
            return
    else:
        safe_print(f"Error: {doc_mode} schema does not exist for {package_name}, use agentic_fcspec.py to generate the schema")
    
    # Handle mutations if present
    mutations_dir = os.path.join(package_path, "mutations")
    if os.path.isdir(mutations_dir):
        for mutation_name in os.listdir(mutations_dir):
            if mutation_name == "__pycache__":
                continue
            mutation_path = os.path.join(mutations_dir, mutation_name)
            if os.path.isdir(mutation_path):
                output_folder = os.path.join(os.path.dirname(output_folder_path), "MutationSchemas", mutation_name)
                os.makedirs(output_folder, exist_ok=True)
                safe_print(f"\nProcessing mutation {package_name}.mutations.{mutation_name}...")
                generate_package_schema(
                    mutation_path, 
                    output_folder,
                    package_import_prefix=f"{package_name}.mutations.{mutation_name}",
                    output_file_name=filename,
                    source_root_path=package_root
                )

def generate_schemas_for_package_mutations(service_name: str, mutation_names: List[str]):
    """Generates schemas for all mutations in a package."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    api_root = os.path.join(project_root, 'APIs')
    service_root = os.path.join(api_root, service_name)
    
    for mutation_name in mutation_names:
        generate_package_schema(
            os.path.join(service_root, "mutations", mutation_name),
            os.path.join(project_root, "MutationSchemas", mutation_name),
            package_import_prefix=f"{service_name}.mutations.{mutation_name}",
            output_file_name=f"{service_name}.json",
            source_root_path=api_root
        )

def generate_schemas_for_packages(source_folder: str, schemas_folder: str, package_names: Optional[List[str]] = None):
    """
    Generates schemas for all packages found in the source directory.

    Args:
        source_folder (Path): The directory containing the API packages.
        schemas_folder (Path): The directory where generated schemas will be saved.
    """
    # Convert String to Path objects
    source_folder = Path(source_folder)
    schemas_folder = Path(schemas_folder)

    if not source_folder.is_dir():
        raise FileNotFoundError(f"Source folder not found or is not a directory: {source_folder}")

    source_folder_abs = source_folder.resolve()
    schemas_folder_abs = schemas_folder.resolve()

    sys.path.append(str(source_folder_abs))
    os.makedirs(schemas_folder_abs, exist_ok=True)
    os.chdir(source_folder_abs)

    for package_name in os.listdir(source_folder_abs):
        if package_names and package_name not in package_names:
            continue
        package_path = source_folder_abs / package_name
        if package_path.is_dir():
            package_doc_mode = get_current_doc_mode(package_name)
            generate_package_schema(str(package_path), output_folder_path=str(schemas_folder_abs), doc_mode=package_doc_mode)

def main(source_folder=None, schemas_folder=None, package_names: Optional[List[str]] = None):
    """Sets up paths and initiates schema generation."""
    # Define source folder for the APIs
    current_file_dir = Path(__file__).parent
    content_dir = current_file_dir.parent
    source_folder = source_folder or content_dir / "APIs"
    schemas_folder = schemas_folder or content_dir / "Schemas"

    # Example usage of configuration management:
    # 
    # 1. Apply a custom configuration
    # apply_config("path/to/custom_config.json")
    #
    # 2. Generate schemas with applied configuration
    # generate_schemas_for_packages(source_folder, schemas_folder)
    #
    # 3. Rollback to original configuration
    # rollback_config()
    #
    # 4. Check configuration status
    # status = get_config_status()
    # print(f"Current config status: {status}")

    generate_schemas_for_packages(source_folder, schemas_folder, package_names)

if __name__ == "__main__":
    main()