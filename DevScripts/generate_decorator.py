import os
import sys
import json

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from DevScripts.extract_fcspecs import load_fcspecs

def _format_value(value, indent_level=1):
    """
    Recursively formats a Python value into a string suitable for code generation.
    It handles multiline strings with triple quotes and ensures consistent indentation.
    """
    indent_str = '    ' * indent_level

    if isinstance(value, str):
        if '\n' in value:
            # For multiline strings, perform robust escaping.
            # 1. Escape backslashes to prevent them from being interpreted as escape sequences.
            # 2. Escape triple-quotes to prevent premature termination of the string literal.
            escaped_value = value.replace('\\', '\\\\').replace('"""', '\\\"\\\"\\\"')

            # The string is split by lines and then rejoined with proper indentation.
            lines = escaped_value.split('\n')
            # The first line is already aligned. Indent subsequent lines.
            formatted_str = '\n'.join([lines[0]] + [indent_str + line for line in lines[1:]])
            return f'""" {formatted_str} """'
        else:
            # For single-line strings, the default representation is safe and readable.
            return repr(value)

    if isinstance(value, dict):
        if not value:
            return '{}'
        
        # Format each key-value pair recursively.
        items = []
        for key, val in value.items():
            # Keys are strings and can be represented directly.
            # Values are formatted recursively with an increased indent level.
            formatted_val = _format_value(val, indent_level + 1)
            items.append(f"\n{indent_str}    {repr(key)}: {formatted_val}")
        
        return f"{{{','.join(items)}\n{indent_str}}}"

    if isinstance(value, list):
        if not value:
            return '[]'
        
        # Format each item in the list recursively.
        items = []
        for item in value:
            formatted_item = _format_value(item, indent_level + 1)
            items.append(f"\n{indent_str}    {formatted_item}")
            
        return f"[{','.join(items)}\n{indent_str}]"

    # For other JSON-compatible types (int, float, bool, None), repr() is sufficient.
    return repr(value)

def format_fcspec_to_decorator(spec):
    """
    Formats a single FCSpec dictionary into a @tool_spec decorator string
    with a single 'spec' argument, passing the spec through without modification.
    """
    # Format the entire, unmodified spec dictionary into a string.
    spec_str = _format_value(spec, indent_level=1)

    # Assemble the final, multi-line decorator string.
    decorator_str = (
        f'@tool_spec(\n'
        f'    spec={spec_str}\n'
        f')'
    )
    return decorator_str

if __name__ == '__main__':
    """
    Example usage: Load all specs and print the generated decorator for a
    specific tool to demonstrate the robust formatting.
    """
    schemas_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Schemas'))
    all_specs = load_fcspecs(schemas_dir)
    
    # --- Example: Zendesk 'create_attachment' tool ---
    # This tool has a multiline description at both the root and parameter level.
    example_service = 'zendesk'
    example_tool = 'create_attachment'

    if example_service in all_specs and example_tool in all_specs[example_service]:
        print(f"--- Generating decorator for '{example_service}.{example_tool}' ---")
        spec_to_format = all_specs[example_service][example_tool]
        generated_decorator = format_fcspec_to_decorator(spec_to_format)
        print(generated_decorator)
    else:
        print(f"Could not find the example tool '{example_service}.{example_tool}'.")
