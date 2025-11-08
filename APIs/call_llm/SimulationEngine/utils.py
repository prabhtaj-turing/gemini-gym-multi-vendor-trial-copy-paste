"""
Utility functions for the Call LLM Service.
These functions provide LLM-specific functionality for docstring parsing and schema generation.
"""
import re
from typing import Dict, List, Tuple, Optional, Any
import docstring_parser

from .custom_errors import ValidationError

# --- Constants for JSON Schema Types ---
JSON_TYPE_STRING = "string"
JSON_TYPE_INTEGER = "integer"
JSON_TYPE_NUMBER = "number"
JSON_TYPE_BOOLEAN = "boolean"
JSON_TYPE_ARRAY = "array"
JSON_TYPE_OBJECT = "object"
JSON_TYPE_NULL = "null"

# --- Core Parsing and Schema Generation Logic ---

def _split_comma_separated_types(params_str: str) -> List[str]:
    """
    Splits a comma-separated string of types, respecting nested structures.
    
    Args:
        params_str: A string containing comma-separated types.
        
    Returns:
        A list of individual type strings.
    """
    params, balance, start = [], 0, 0
    for i, char in enumerate(params_str):
        if char in '([':
            balance += 1
        elif char in ')]':
            balance -= 1
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
    
    # Check for Optional[T]
    if type_str.startswith("Optional[") and type_str.endswith("]"):
        return True
    
    # Check for Union[T, None] or Union[None, T]
    if type_str.startswith("Union[") and type_str.endswith("]"):
        inner_str = type_str[6:-1]  # Remove "Union[" and "]"
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

def map_type(type_str: Optional[str]) -> Dict[str, Any]:
    """Maps a Python type string to a JSON schema object.
    
    Args:
        type_str (Optional[str]): Python type string to map
        
    Returns:
        Dict[str, Any]: JSON schema object representing the type
    """
    type_str = (type_str or "Any").strip()
    
    type_map = {"str": JSON_TYPE_STRING, "int": JSON_TYPE_INTEGER, "float": JSON_TYPE_NUMBER, "bool": JSON_TYPE_BOOLEAN, "list": JSON_TYPE_ARRAY, "dict": JSON_TYPE_OBJECT, "Any": JSON_TYPE_OBJECT, "UUID": JSON_TYPE_STRING}

    if type_str in type_map: return {"type": type_map[type_str]}
    
    if type_str.startswith(("Optional[", "Union[")) and type_str.endswith("]"):
        is_optional = type_str.startswith("Optional[")
        inner_str = type_str[len("Optional["):-1] if is_optional else type_str[len("Union["):-1]
        types = _split_comma_separated_types(inner_str)
        non_null_types = [t for t in types if t.lower() not in ['none', 'nonetype']]
        if non_null_types: return map_type(non_null_types[0])
        return {"type": JSON_TYPE_NULL}

    if type_str.startswith(("List[", "list[")) and type_str.endswith("]"):
        item_type = type_str[5:-1].strip() or "Any"
        return {"type": JSON_TYPE_ARRAY, "items": map_type(item_type)}
        
    if type_str.startswith(("Dict[", "dict[")) and type_str.endswith("]"):
         return {"type": JSON_TYPE_OBJECT, "properties": {}}

    return {"type": JSON_TYPE_OBJECT} # Fallback for custom classes

def parse_object_properties_from_description(description: str) -> Tuple[str, Optional[Dict[str, Any]]]:
    """Recursively parses sub-properties from a description string."""
    if not description: return "", None
    # This regex is from your FCSpec.py file
    prop_regex = re.compile(r"^\s*(?:[-*]\s*)?(?P<name>[\w'\"`]+)\s*\((?P<type>.*?)\):\s*(?P<desc>.*)", re.IGNORECASE)
    get_indent = lambda line: len(line) - len(line.lstrip(' '))

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
        if not match: 
            i += 1
            continue
            
        current_indent = get_indent(line)
        data = match.groupdict()
        name = data["name"].strip().strip("'\"`")
        type_str, desc_on_line = data["type"].strip(), data["desc"].strip()

        child_lines = []
        j = i + 1
        while j < len(prop_lines) and (not prop_lines[j].strip() or get_indent(prop_lines[j]) > current_indent):
            child_lines.append(prop_lines[j])
            j += 1
        
        full_prop_description = (desc_on_line + "\n" + "\n".join(child_lines)).strip()
        
        # This logic for 'required' is from your file
        if "optional" not in type_str.lower():
            required.append(name)
        
        type_str_cleaned = re.sub(r',?\s*optional\s*', '', type_str, flags=re.IGNORECASE).strip()
        
        prop_schema = map_type(type_str_cleaned)
        sub_main_desc, sub_props_schema = parse_object_properties_from_description(full_prop_description)
        prop_schema["description"] = sub_main_desc.strip()
        
        if sub_props_schema and prop_schema.get("type") == JSON_TYPE_OBJECT:
            prop_schema["properties"] = sub_props_schema.get("properties", {})
            if sub_props_schema.get("required"):
                prop_schema["required"] = sub_props_schema.get("required")
        
        properties[name] = prop_schema
        i = j

    result_schema = {"properties": properties}
    if required:
        result_schema["required"] = sorted(required)
    return main_description, result_schema

def docstring_to_fcspec(docstring: str, function_name: str) -> Dict[str, Any]:
    """
    Builds a JSON schema from a single docstring string, based on the logic
    from the provided FCSpec.py file.

    Args:
        docstring: The docstring to convert.
        function_name: The name of the function.

    Returns:
        A dictionary representing the JSON schema (FCSpec).
    """
    doc = docstring_parser.parse(docstring)
    
    description_parts = [doc.short_description, doc.long_description]
    full_description = "\n\n".join(part for part in description_parts if part).strip()

    schema = {
        "name": function_name,
        "description": full_description,
        "parameters": {"type": JSON_TYPE_OBJECT, "properties": {}}
    }
    required_params = []

    for param in doc.params:
        param_schema = map_type(param.type_name)
        
        # This logic is from your build_initial_schema function
        if param_schema.get("type") != JSON_TYPE_OBJECT:
            param_schema["description"] = param.description or ""
        else:
            main_desc, props_schema = parse_object_properties_from_description(param.description or "")
            param_schema["description"] = main_desc.strip()
            if props_schema:
                param_schema["properties"] = props_schema.get("properties", {})
                if props_schema.get("required"):
                    param_schema["required"] = props_schema["required"]
        
        schema["parameters"]["properties"][param.arg_name] = param_schema
        
        # Simplified check for required parameters (cannot use AST on a string)
        is_optional = param.is_optional or is_optional_type_string(param.type_name)
        if not is_optional:
            required_params.append(param.arg_name)

    if required_params:
        schema["parameters"]["required"] = sorted(required_params)
        
    return schema

