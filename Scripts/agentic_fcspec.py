#%%
import os
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

# --- Configuration & Constants ---
API_KEY = "API KEY HERE"  # In canvas in api team channel
MAX_WORKERS = 10 # Adjust based on system capabilities
MODEL_NAME = "gemini-2.5-flash"
print_lock = threading.Lock()

JSON_TYPE_STRING = "string"
JSON_TYPE_INTEGER = "integer"
JSON_TYPE_NUMBER = "number"
JSON_TYPE_BOOLEAN = "boolean"
JSON_TYPE_ARRAY = "array"
JSON_TYPE_OBJECT = "object"
JSON_TYPE_NULL = "null"

# --- Helper Functions ---

def safe_print(*args, **kwargs):
    """Thread-safe printing function that uses a lock to prevent output interleaving.
    
    Args:
        *args: Variable length argument list to print
        **kwargs: Arbitrary keyword arguments to pass to print
    """
    with print_lock:
        print(*args, **kwargs)

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
    for i in range(len(parts) - 1, 0, -1):
        module_parts = parts[:i]
        potential_path = os.path.join(package_root, *module_parts)
        if os.path.isfile(potential_path + ".py"): return potential_path + ".py"
        init_file = os.path.join(potential_path, "__init__.py")
        if os.path.isfile(init_file): return init_file
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
    
    # Check for Optional[T]
    if type_str.startswith("Optional[") and type_str.endswith("]"):
        return True
    
    # Check for Union[T, None] or Union[None, T]
    if type_str.startswith("Union[") and type_str.endswith("]"):
        inner_str = type_str[6:-1]  # Remove "Union[" and "]"
        types = _split_comma_separated_types(inner_str)
        # Check if any type is None or NoneType
        return any(t.strip().lower() in ['none', 'nonetype'] for t in types)
    
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
    """Recursively parses sub-properties from a description string.
    
    Args:
        description (str): The description string to parse
        
    Returns:
        Tuple[str, Optional[Dict[str, Any]]]: Tuple containing:
            - The main description (text before property definitions)
            - A dictionary with 'properties' and 'required' keys, or None if no properties found
    """
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
        name = data["name"].strip().strip("'\"`")
        type_str, desc_on_line = data["type"].strip(), data["desc"].strip()

        child_lines = []
        j = i + 1
        while j < len(prop_lines) and (not prop_lines[j].strip() or get_indent(prop_lines[j]) > current_indent):
            child_lines.append(prop_lines[j])
            j += 1
        
        full_prop_description = desc_on_line + "\n" + "\n".join(child_lines)
        
        # Use the same optional detection logic as top-level parameters
        is_optional_by_type = is_optional_type_string(type_str)
        if not is_optional_by_type: 
            required.append(name)
        
        # Clean the type string by removing Optional[] wrapper or Union[..., None] patterns
        if type_str.startswith("Optional[") and type_str.endswith("]"):
            type_str_cleaned = type_str[9:-1].strip()  # Remove "Optional[" and "]"
        elif type_str.startswith("Union[") and type_str.endswith("]"):
            inner_str = type_str[6:-1]  # Remove "Union[" and "]"
            types = _split_comma_separated_types(inner_str)
            # Remove None/NoneType types and take the first remaining type
            non_null_types = [t.strip() for t in types if t.strip().lower() not in ['none', 'nonetype']]
            type_str_cleaned = non_null_types[0] if non_null_types else "Any"
        else:
            # Fallback to the old simple cleaning for backward compatibility
            type_str_cleaned = re.sub(r',?\s*optional\s*', '', type_str, flags=re.IGNORECASE).strip()
        
        prop_schema = map_type(type_str_cleaned)
        sub_main_desc, sub_props_schema = parse_object_properties_from_description(full_prop_description)
        prop_schema["description"] = sub_main_desc.strip()
        
        # Handle nested properties for both objects and arrays
        if sub_props_schema:
            if prop_schema.get("type") == JSON_TYPE_OBJECT:
                prop_schema["properties"] = sub_props_schema.get("properties", {})
            if sub_props_schema.get("required"): prop_schema["required"] = sub_props_schema.get("required")
            elif prop_schema.get("type") == JSON_TYPE_ARRAY and prop_schema.get("items", {}).get("type") == JSON_TYPE_OBJECT:
                # For List[Dict], populate the items properties
                prop_schema["items"]["properties"] = sub_props_schema.get("properties", {})
                if sub_props_schema.get("required"): prop_schema["items"]["required"] = sub_props_schema.get("required")
        
        properties[name] = prop_schema
        i = j

    result_schema = {"properties": properties}
    if required: result_schema["required"] = sorted(required)
    return main_description, result_schema

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
        for arg in func_node.args.args[num_pos_args - num_pos_defaults:]: params_with_defaults.add(arg.arg)
    for i, kw_arg in enumerate(func_node.args.kwonlyargs):
        if i < len(func_node.args.kw_defaults) and func_node.args.kw_defaults[i] is not None: params_with_defaults.add(kw_arg.arg)

    # --- Start of fix ---
    description_parts = []
    if doc.short_description:
        description_parts.append(doc.short_description)
    if doc.long_description:
        description_parts.append(doc.long_description)
    full_description = "\n\n".join(description_parts)
    # --- End of fix ---

    schema = {
        "name": func_name,
        "description": (full_description or ""),
        "parameters": {"type": JSON_TYPE_OBJECT, "properties": {}}
    }
    required_params = []

    for param in doc.params:
        param_schema = map_type(param.type_name)
        
        # Handle different parameter types
        if param_schema.get("type") == JSON_TYPE_ARRAY and param_schema.get("items", {}).get("type") == JSON_TYPE_OBJECT:
            # Handle List[Dict] or List[Object] - parse properties for the items
            main_desc, props_schema = parse_object_properties_from_description(param.description or "")
            param_schema["description"] = main_desc.strip()
            if props_schema:
                param_schema["items"]["properties"] = props_schema.get("properties", {})
                if props_schema.get("required"): param_schema["items"]["required"] = props_schema["required"]
        elif param_schema.get("type") == JSON_TYPE_OBJECT:
            # Handle Dict/Object - parse properties directly
            main_desc, props_schema = parse_object_properties_from_description(param.description or "")
            param_schema["description"] = main_desc.strip()
            if props_schema:
                param_schema["properties"] = props_schema.get("properties", {})
                if props_schema.get("required"): param_schema["required"] = props_schema["required"]
        else:
            # Handle primitive types - just add description
            param_schema["description"] = param.description or ""
        
        schema["parameters"]["properties"][param.arg_name] = param_schema
        
        has_default = param.arg_name in params_with_defaults
        is_optional_by_docstring = param.is_optional or param.default is not None
        is_optional_by_type = is_optional_type_string(param.type_name)
        is_optional = is_optional_by_docstring or is_optional_by_type
        if not has_default and not is_optional: required_params.append(param.arg_name)

    if required_params: schema["parameters"]["required"] = sorted(required_params)
    return schema

# --- Agentic Converter Class ---

class AgenticConverter:
    """Uses an LLM to rewrite descriptions for schema components."""
    def __init__(self, model_name=MODEL_NAME, config: Optional[Dict[str, Any]] = None):
        self.client = genai.Client(api_key=API_KEY)
        self.model = model_name
        self.config = config

    def rewrite_description(self, original_description: str, context: str) -> Optional[str]:
        """Rewrites a description based on the provided style and context."""
        desc_config = self.config.get("description_config", {})
        type_ = desc_config.get("type", "concise")
        
        if type_ == "medium_detail":
            word_limit = desc_config.get("word_limit", 30)
            prompt = f"""
You are an expert technical writer. Rewrite the "Original Description" to be a clear, medium-length explanation (1-3 sentences).

**Rules:**
1. The description should clearly state the primary purpose of the element and crucially how it is structured or constrained if such information is present in the original description.
2. **Can have 1 to 3 sentences (and {word_limit} words) but not limited to this as Most Crucially, DO NOT LOSE CRITICAL INFORMATION in the original description about what the function/parameter is, crucial parameter details on how the parameter is structured or constrained. If a parameter should have a specific structure provide that information/example if provided. A longer, clear description is better than a brief, ambiguous one.**
3. It MUST be in an imperative tone if it's for a function (e.g., "Calculates the total...") or descriptive for a parameter.
4. It MUST NOT contain any internal implementation details (like "saves to the database")
5. <IMPORTANT> DO NOT LOSE CRITICAL INFORMATION in the original description about what the function/parameter is, crutial parameter details on how the parameter is structured or constrained. If a parameter should have a specific structure provide that information/example if provided. A longer, clear, and complete description is better than a brief, ambiguous one with unexplained references.</IMPORTANT>
6. <IMPORTANT> DO NOT CREATE NEW UNVERIFIED INFORMATION THAT IS NOT PRESENT IN THE ORIGINAL DESCRIPTION OR CONTEXT DOCSTRING.</IMPORTANT>
7. <IMPORTANT> DO NOT INCLUDE ANY INFORMATION ABOUT THE FUNCTION/PARAMETER THAT IS NOT PRESENT IN THE ORIGINAL DESCRIPTION OR CONTEXT DOCSTRING.</IMPORTANT>
8. <IMPORTANT> DO NOT CREATE FACTUAL CONTRADICTIONS, MISLEADING INFORMATION/DESCRIPTION, OR INACCURACIES IN THE DESCRIPTION.</IMPORTANT>

**Example 1:**
- **Original:** "This function takes a list of items, iterates through them to find the ones marked as 'taxable,' calculates the sales tax for each based on a predefined rate, and then returns the sum total of all taxes."
- **Rewritten (medium-detail):** Calculates the total sales tax for a list of items. It processes only taxable items and returns the final sum. Non-taxable items are ignored.

**Example 2 (for parameters):**
- **Original:**
Specifies the search query.
This parameter is a string that can contain one or more conditions. Each condition should be in the format 'field:value'.
Multiple conditions can be combined using 'AND' or 'OR' operators. For example: 'status:active AND user_id:123'.

- **Rewritten (medium-detail):** A query string used to filter search results. The query must be formatted with conditions like `field:value`. Multiple conditions can be joined using `AND` or `OR` operators to create more complex searches (e.g. 'status:active AND user_id:123').
---
**Original Description to Rewrite:**
"{original_description}"

**Additional Context for Understanding (do not extract new info):**
{context}
---
**Rewritten Description:**
"""
        else: # concise
            word_limit = desc_config.get("word_limit", 10)
            prompt = f"""
You are an expert technical writer creating concise API documentation.
Your task is to rewrite the provided "Original Description" to be brief but clear.

**Guidelines:**
1. Aim for a single, clear sentence. While there's a soft guideline of about {word_limit} words, this is flexible and not limited to this as...
2. **...Most Crucially, DO NOT LOSE CRITICAL INFORMATION in the original description about what the function/parameter is, crutial parameter details on how the parameter is structured or constrained. If a parameter should have a specific structure provide that information/example if provided. A longer, clear, and complete description is better than a brief, ambiguous one with unexplained references.**
3. It MUST be in an imperative tone if it's for a function (e.g., "Send an email.") or descriptive for a parameter.
4. Do not include internal implementation details (e.g., "saves to the database").
5. <IMPORTANT> DO NOT LOSE CRITICAL INFORMATION in the original description about what the function/parameter is, crutial parameter details on how the parameter is structured or constrained. If a parameter should have a specific structure provide that information/example if provided. A longer, clear, and complete description is better than a brief, ambiguous one with unexplained references.</IMPORTANT>
6. <IMPORTANT> DO NOT CREATE NEW UNVERIFIED INFORMATION THAT IS NOT PRESENT IN THE ORIGINAL DESCRIPTION OR CONTEXT DOCSTRING.</IMPORTANT>
7. <IMPORTANT> DO NOT INCLUDE ANY INFORMATION ABOUT THE FUNCTION/PARAMETER THAT IS NOT PRESENT IN THE ORIGINAL DESCRIPTION OR CONTEXT DOCSTRING.</IMPORTANT>
8. <IMPORTANT> DO NOT CREATE FACTUAL CONTRADICTIONS, MISLEADING INFORMATION/DESCRIPTION, OR INACCURACIES IN THE DESCRIPTION.</IMPORTANT>

**Example 1:**
- **Original:** "This function takes a user object and a message string, processes it, and then saves the resulting message to the database, returning the new message's ID."
- **Rewritten (concise):** Sends a message to a user and returns the new message ID.

**Example 2 (for parameters):**
- **Original:**
Specifies the search query.
This parameter is a string that can contain one or more conditions. Each condition should be in the format 'field:value'.
Multiple conditions can be combined using 'AND' or 'OR' operators. For example: 'status:active AND user_id:123'.

- **Rewritten (concise):** A query string for searching, formatted as `field:value` and supporting `AND` or `OR` operators for combining multiple conditions.
---
**Original Description to Rewrite:**
"{original_description}"

**Additional Context for Understanding (do not extract new info):**
{context}
---
**Rewritten Description (brief and clear):**
"""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            return response.text.strip()
        except Exception: return None

# --- Main Orchestration Logic ---

def rewrite_descriptions_agentically(schema_part: Any, context_stack: List[str], agent: AgenticConverter, source_code: str):
    """Recursively traverses the schema and uses an agent to rewrite descriptions.
    
    Args:
        schema_part (Any): The schema part to process (can be a dict or other type)
        context_stack (List[str]): List of context strings showing the path to this schema part
        agent (AgenticConverter): The agent to use for rewriting descriptions
        source_code (str): The source code of the function being processed
    """
    if isinstance(schema_part, dict):
        original_desc = schema_part.get("description")
        if original_desc: # Only rewrite if a description exists
            full_context = f"Function Source Code:\n```python\n{source_code}\n```\n\nSchema Context: {' -> '.join(context_stack)}"
            new_desc = agent.rewrite_description(original_desc, full_context)
            if new_desc:
                schema_part["description"] = new_desc
            else:
                 safe_print(f"      ❌ Failed to rewrite description for: {' -> '.join(context_stack)}")
        
        if "parameters" in schema_part:
            if "properties" in schema_part["parameters"]:
                for prop_name, prop_schema in schema_part["parameters"]["properties"].items():
                    rewrite_descriptions_agentically(prop_schema, context_stack + [f"Property: {prop_name}"], agent, source_code)
        
        if "properties" in schema_part:
            for prop_name, prop_schema in schema_part["properties"].items():
                rewrite_descriptions_agentically(prop_schema, context_stack + [f"Property: {prop_name}"], agent, source_code)

def process_single_function(args: Tuple[str, str, str, AgenticConverter]) -> Optional[Dict[str, Any]]:
    """Processes a single function to generate its schema.
    
    Args:
        args (Tuple[str, str, str, AgenticConverter]): Tuple containing:
            - public_name: The public name of the function
            - fqn: Fully qualified name of the function
            - package_root: Root directory of the package
            - agent: The agent to use for rewriting descriptions
            
    Returns:
        Optional[Dict[str, Any]]: The generated schema if successful, None otherwise
    """
    public_name, fqn, package_root, agent = args

    source_file_path = resolve_function_source_path(fqn, package_root)
    if not source_file_path: return None
    
    node_info = extract_specific_function_node(source_file_path, fqn)
    if not node_info: return None
    func_node, func_src = node_info
    
    docstring_text = ast.get_docstring(func_node)
    if not docstring_text: return None
    parsed_docstring = docstring_parser.parse(docstring_text)

    schema = build_initial_schema(parsed_docstring, func_node, public_name)
    
    type_ = agent.config.get("description_config", {}).get("type", "raw_docstring")
    if type_ not in ["concise", "medium_detail", "raw_docstring"]:
        safe_print(f"  - Using raw docstring descriptions for '{public_name}'.")
        return schema

    if type_ != "raw_docstring":
        rewrite_descriptions_agentically(schema, [f"Function: {public_name}"], agent, func_src)
    else:
        safe_print(f"  - Using raw docstring descriptions for '{public_name}'.")

    safe_print(f"  ✅ Success! Schema generated for '{public_name}'.")
    return schema

def generate_package_schema(package_path: str, output_folder_path: str, config_path: Optional[str] = None):
    """Generates schemas for all functions in a package.
    
    Args:
        package_path (str): Path to the Python package directory
        output_folder_path (str): Path to the output folder for schema files
        config (Optional[Dict]): A dictionary containing the configuration
    """
    if config_path:
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {}
    
    if config:
        print("Using config for type: ", config.get("description_config", {}).get("type", "concise"))

    package_root = os.path.dirname(os.path.abspath(package_path))
    init_path = os.path.join(package_path, "__init__.py")
    if not os.path.exists(init_path):
        safe_print(f"Error: __init__.py not found in {package_path}")
        return

    function_map = get_variable_from_file(init_path, "_function_map")
    if not function_map:
        safe_print("Error: Could not find a valid _function_map.")
        return

    agent = AgenticConverter(config=config)
    function_args = [(name, fqn, package_root, agent) for name, fqn in function_map.items()]
    
    all_schemas = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(process_single_function, function_args)
        all_schemas = [s for s in results if s]

    if all_schemas:
        all_schemas.sort(key=lambda x: x.get('name', ''))
        
        package_name = os.path.basename(package_path)
        desc_type = config.get("description_config", {}).get("type", "raw_docstring")
        
        if desc_type == "concise":
            filename = f"concise_{package_name}.json"
        elif desc_type == "medium_detail":
            filename = f"medium_detail_{package_name}.json"
        else: # raw_docstring
            filename = f"{package_name}.json"
        
        # Save schema to simulation engine folder if it exists
        if "SimulationEngine" in os.listdir(package_path) and desc_type != "raw_docstring":
            simulation_engine_path = os.path.join(package_path, "SimulationEngine")
            output_folder_path = os.path.join(simulation_engine_path, "alternate_fcds")
            output_file = os.path.join(output_folder_path, filename)
            os.makedirs(output_folder_path, exist_ok=True)
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_schemas, f, indent=2, ensure_ascii=False)
            safe_print(f"\n{'*' * 50}\n✅ {package_name} Schema generation complete: {output_file}\n{'*' * 50}")
        else:
            # Save schema to output folder
            output_file = os.path.join(output_folder_path, filename)
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_schemas, f, indent=2, ensure_ascii=False)
            safe_print(f"\n{'*' * 50}\n✅ {package_name} Schema generation complete: {output_file}\n{'*' * 50}")
    else:
        safe_print("\n❌ No schemas were generated.")


#%%
if __name__ == "__main__":
    import os
    import sys

    from pathlib import Path

    current_file_dir = Path(__file__).parent
    APIS_DIR = current_file_dir.parent / "APIs"
    CONTENT_DIR = current_file_dir.parent
    config_path = current_file_dir / "config.json"

    sys.path.append(CONTENT_DIR)
    # Output directory for generated schemas
    FC_DIR = CONTENT_DIR / "Schemas"

    print('\nGenerating Original FC Schemas with agentic_fcspec.py')
    os.makedirs(FC_DIR, exist_ok=True)

    # Change working directory to the source folder
    os.chdir(APIS_DIR)

    # Process all packages in the APIs directory
    for package_name in os.listdir(APIS_DIR):
        package_path = os.path.join(APIS_DIR, package_name)
        
        if os.path.isdir(package_path):
            print(f'Processing {package_name}...')
            try:
                # Pass None as config_path to use default "raw_docstring" mode
                generate_package_schema(package_path, output_folder_path=FC_DIR, config_path=config_path)
                print(f'✅ Generated schema for {package_name}')
            except Exception as e:
                print(f'❌ Failed to generate schema for {package_name}: {e}')

    print(f'✅ Successfully generated schemas in {FC_DIR}')
    os.chdir(CONTENT_DIR) 
#%%