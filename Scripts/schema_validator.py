from google import genai
from google.genai import types
from typing import Union, Any, List, Dict, Tuple, Set
import json
import os
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.utils.function_calling import (convert_to_openai_function, 
                                                   convert_to_openai_tool)
from langchain_anthropic import convert_to_anthropic_tool

def validate_schema_with_genai(schema_data: List[Dict], service_name: str) -> List[str]:
    """
    Validates a schema by attempting to create a Google GenAI Tool from it.
    
    Args:
        schema_data: List of function declarations
        service_name: Name of the service (from filename)
    
    Returns:
        List of error messages for invalid functions
    """
    errors = []
    
    for func_declaration in schema_data:
        func_name = func_declaration.get("name", "unnamed_function")
        
        try:
            # Try to create a Tool with this function declaration
            tools = types.Tool(function_declarations=[func_declaration])
            # If no exception is raised, the schema is valid
        except Exception as e:
            error_msg = f"{service_name}-{func_name}: {str(e)}"
            errors.append(error_msg)
    
    return errors

def validate_schema_with_openai(schema_data: List[Dict], service_name: str) -> List[str]:
    """
    Validates a schema by attempting to create a Google GenAI Tool from it.
    
    Args:
        schema_data: List of function declarations
        service_name: Name of the service (from filename)
    
    Returns:
        List of error messages for invalid functions
    """
    errors = []
    try:
        # Try to create a Tool with this function declaration
        model = ChatOpenAI(model="gpt-4o", temperature=0, api_key='abc')
        model.bind_tools(schema_data)
    except Exception as e:
        error_msg = f"{service_name}: {str(e)}"
        errors.append(error_msg)
    for func_declaration in schema_data:
        func_name = func_declaration.get("name", "unnamed_function")
        
        try:
            # Try to create a Tool with this function declaration
            convert_to_openai_tool(func_declaration)
            convert_to_openai_function(func_declaration)
            # If no exception is raised, the schema is valid
        except Exception as e:
            error_msg = f"{service_name}-{func_name}: {str(e)}"
            errors.append(error_msg)
    
    return errors

def validate_schema_with_anthropic(schema_data: List[Dict], service_name: str) -> List[str]:
    """
    Validates a schema by attempting to create a Google GenAI Tool from it.
    
    Args:
        schema_data: List of function declarations
        service_name: Name of the service (from filename)
    
    Returns:
        List of error messages for invalid functions
    """
    errors = []
    try:
        # Try to create a Tool with this function declaration
        model = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0, api_key='abc')
        model.bind_tools(schema_data)
    except Exception as e:
        error_msg = f"{service_name}: {str(e)}"
        errors.append(error_msg)

    for func_declaration in schema_data:
        func_name = func_declaration.get("name", "unnamed_function")
        try:
            convert_to_anthropic_tool(func_declaration)
            # If no exception is raised, the schema is valid
        except Exception as e:
            error_msg = f"{service_name}-{func_name}: {str(e)}"
            errors.append(error_msg)
    
    return errors

def validate_array_items_in_declarations(declarations: List[Dict]) -> List[str]:
    """
    Checks all function declarations to ensure array types have an 'items' dictionary.
    
    Args:
        declarations: A list of function calling declaration dictionaries.
    
    Returns:
        A list of formatted error strings. Returns an empty list if all are valid.
    """
    error_messages = []
    
    for func_def in declarations:
        func_name = func_def.get("name", "Unnamed Function")
        
        # Check the main parameters object first
        params = func_def.get("parameters", {})
        if params.get("type") == "array":
            items_value = params.get("items")
            if not isinstance(items_value, dict):
                error = f"{func_name}: Main parameters is type 'array' but missing valid 'items' dictionary"
                error_messages.append(error)
        
        # Safely get properties, defaulting to an empty dict if keys are missing
        properties = params.get("properties", {})
        
        if not properties:
            continue
        
        for param_name, param_details in properties.items():
            # Check if the parameter is of type 'array'
            if param_details.get("type") == "array":
                items_value = param_details.get("items")
                
                # The 'items' key must exist and its value must be a dictionary
                if not isinstance(items_value, dict):
                    error = f"{func_name}: Parameter '{param_name}' is type 'array' but missing valid 'items' dictionary"
                    error_messages.append(error)
    
    return error_messages

def validate_object_properties_in_declarations(declarations: List[Dict]) -> List[str]:
    """
    Checks all function declarations to ensure object types have a 'properties' dictionary.
    
    Args:
        declarations: A list of function calling declaration dictionaries.
    
    Returns:
        A list of formatted error strings. Returns an empty list if all are valid.
    """
    error_messages = []
    
    for func_def in declarations:
        func_name = func_def.get("name", "Unnamed Function")
        
        # Check the main parameters object first
        params = func_def.get("parameters", {})
        if params.get("type") == "object":
            properties_value = params.get("properties")
            if not isinstance(properties_value, dict):
                error = f"{func_name}: Main parameters is type 'object' but missing valid 'properties' dictionary"
                error_messages.append(error)
        
        # Safely get properties, defaulting to an empty dict if keys are missing
        properties = params.get("properties", {})
        
        if not properties:
            continue
        
        for param_name, param_details in properties.items():
            # Check if the parameter is of type 'object'
            if param_details.get("type") == "object":
                properties_value = param_details.get("properties")
                
                # The 'properties' key must exist and its value must be a dictionary
                if not isinstance(properties_value, dict):
                    error = f"{func_name}: Parameter '{param_name}' is type 'object' but missing valid 'properties' dictionary"
                    error_messages.append(error)
    
    return error_messages

def validate_nested_schema_recursive(obj: Dict, path: str = "") -> List[str]:
    """
    Recursively validates nested objects for array types without items and object types without properties.
    
    Args:
        obj: Dictionary to validate
        path: Current path in the object for error reporting
    
    Returns:
        List of error messages
    """
    errors = []
    
    if not isinstance(obj, dict):
        return errors
    
    for key, value in obj.items():
        current_path = f"{path}.{key}" if path else key
        
        if isinstance(value, dict):
            # Check if this is an array type
            if value.get("type") == "array":
                items_value = value.get("items")
                if not isinstance(items_value, dict):
                    errors.append(f"Array at '{current_path}' missing valid 'items' dictionary")
                else:
                    # Recursively check the items object
                    errors.extend(validate_nested_schema_recursive(items_value, current_path))
            # Check if this is an object type
            elif value.get("type") == "object":
                properties_value = value.get("properties")
                if not isinstance(properties_value, dict):
                    errors.append(f"Object at '{current_path}' missing valid 'properties' dictionary")
                else:
                    # Recursively check the properties object
                    errors.extend(validate_nested_schema_recursive(properties_value, current_path))
            else:
                # Recursively check other objects
                errors.extend(validate_nested_schema_recursive(value, current_path))
    
    return errors

def validate_type_values(obj: Dict, path: str = "") -> List[str]:
    """
    Recursively validates that all 'type' values are valid JSON Schema types.
    
    Args:
        obj: Dictionary to validate
        path: Current path in the object for error reporting
    
    Returns:
        List of error messages
    """
    errors = []
    valid_types = {"string", "integer", "number", "boolean", "object", "array", "null"}
    # Schema structure keywords that should not be checked for type values
    schema_keywords = {"properties", "items", "required", "description", "enum", "default", "examples"}
    
    if not isinstance(obj, dict):
        return errors
    
    for key, value in obj.items():
        current_path = f"{path}.{key}" if path else key
        
        if isinstance(value, dict):
            # Skip schema structure keywords - they don't have type values
            if key in schema_keywords:
                # Still recursively check their contents
                errors.extend(validate_type_values(value, current_path))
                continue
                
            # Check if this object has a 'type' field
            if "type" in value:
                type_value = value.get("type")
                # Handle both string types and array of types (union types)
                if isinstance(type_value, str):
                    if type_value not in valid_types:
                        errors.append(f"Invalid type '{type_value}' at '{current_path}' - must be one of {valid_types}")
                elif isinstance(type_value, list):
                    # Check each type in the union
                    for t in type_value:
                        if t not in valid_types:
                            errors.append(f"Invalid type '{t}' in union at '{current_path}' - must be one of {valid_types}")
                else:
                    errors.append(f"Type value at '{current_path}' must be string or array, got {type(type_value).__name__}")
            
            # Recursively check nested objects
            errors.extend(validate_type_values(value, current_path))
        elif isinstance(value, list):
            # Handle lists (including anyOf, oneOf, allOf arrays)
            for i, list_item in enumerate(value):
                if isinstance(list_item, dict):
                    # Check if this list item has a 'type' field
                    if "type" in list_item:
                        type_value = list_item.get("type")
                        if isinstance(type_value, str):
                            if type_value not in valid_types:
                                errors.append(f"Invalid type '{type_value}' at '{current_path}[{i}]' - must be one of {valid_types}")
                        elif isinstance(type_value, list):
                            # Check each type in the union
                            for t in type_value:
                                if t not in valid_types:
                                    errors.append(f"Invalid type '{t}' in union at '{current_path}[{i}]' - must be one of {valid_types}")
                        else:
                            errors.append(f"Type value at '{current_path}[{i}]' must be string or array, got {type(type_value).__name__}")
                    
                    # Recursively check the list item
                    errors.extend(validate_type_values(list_item, f"{current_path}[{i}]"))
    
    return errors

def validate_nested_arrays(properties: Dict) -> List[str]:
    """
    Recursively validates nested array properties.
    
    Args:
        properties: Dictionary of properties to validate
    
    Returns:
        List of error messages
    """
    errors = []
    
    for param_name, param_details in properties.items():
        if param_details.get("type") == "array":
            items_value = param_details.get("items")
            if not isinstance(items_value, dict) or not items_value:
                errors.append(f"Parameter '{param_name}' is type 'array' but missing valid 'items' dictionary")
            else:
                # Check nested properties if items is an object
                if items_value.get("type") == "object":
                    nested_props = items_value.get("properties", {})
                    if nested_props:
                        errors.extend(validate_nested_arrays(nested_props))
    
    return errors

def validate_schema_structure(schema_data: List[Dict], service_name: str) -> List[str]:
    """
    Validates the basic structure and common issues in schemas.
    
    Args:
        schema_data: List of function declarations
        service_name: Name of the service
    
    Returns:
        List of error messages
    """
    errors = []
    
    for func_def in schema_data:
        func_name = func_def.get("name", "Unnamed Function")
        
        # Check for required fields
        if not func_def.get("name"):
            errors.append(f"{service_name}-{func_name}: Missing 'name' field")
        
        if not func_def.get("description"):
            errors.append(f"{service_name}-{func_name}: Missing 'description' field")
        
        if not func_def.get("parameters"):
            errors.append(f"{service_name}-{func_name}: Missing 'parameters' field")
        else:
            params = func_def["parameters"]
            
            # Check parameters structure
            if not isinstance(params, dict):
                errors.append(f"{service_name}-{func_name}: 'parameters' must be an object")
            else:
                param_type = params.get("type")
                if param_type not in ["object", "array"]:
                    errors.append(f"{service_name}-{func_name}: 'parameters.type' must be 'object' or 'array', got '{param_type}'")
                
                # Check for empty items in array parameters
                if param_type == "array":
                    items = params.get("items")
                    if not isinstance(items, dict) or not items:
                        errors.append(f"{service_name}-{func_name}: Array parameters must have non-empty 'items' object")
                    elif items == {}:
                        errors.append(f"{service_name}-{func_name}: Array parameters has empty 'items' object {{}}")
                
                # Check for properties in object parameters
                elif param_type == "object":
                    properties = params.get("properties")
                    if not isinstance(properties, dict):
                        errors.append(f"{service_name}-{func_name}: Object parameters must have 'properties' object")
    
    return errors

def validate_all_schemas(schemas_dir: str = "Schemas") -> Dict[str, List[str]]:
    """
    Validates all schema files in the Schemas directory.
    
    Args:
        schemas_dir: Path to the schemas directory
    
    Returns:
        Dictionary mapping service names to lists of invalid function names
    """
    invalid_functions = {}
    
    # Get all JSON files in the schemas directory
    schemas_path = Path(schemas_dir)
    if not schemas_path.exists():
        raise FileNotFoundError(f"Schemas directory not found: {schemas_dir}")
    
    json_files = list(schemas_path.glob("*.json"))
    
    print(f"Found {len(json_files)} schema files to validate...")
    
    for json_file in json_files:
        service_name = json_file.stem  # Get filename without extension
        print(f"Validating {service_name}...")
        
        try:
            with open(json_file, 'r') as f:
                schema_data = json.load(f)
            
            if not isinstance(schema_data, list):
                print(f"Warning: {service_name}.json is not a list of function declarations")
                continue
            
            # Validate using multiple methods
            structure_errors = validate_schema_structure(schema_data, service_name)
            array_errors = validate_array_items_in_declarations(schema_data)
            object_errors = validate_object_properties_in_declarations(schema_data)
            
            # Check for nested schema issues
            nested_errors = []
            type_errors = []
            for func_def in schema_data:
                # Validate the entire function definition recursively
                nested_errors.extend(validate_nested_schema_recursive(func_def, func_def.get("name", "unnamed_function")))
                type_errors.extend(validate_type_values(func_def, func_def.get("name", "unnamed_function")))
            
            # Try GenAI validation (optional - requires API key)
            genai_errors = []
            try:
                genai_errors = validate_schema_with_genai(schema_data, service_name)
            except Exception as e:
                print(f"GenAI validation skipped for {service_name}: {e}")
            
            openai_errors = []
            try:
                openai_errors = validate_schema_with_openai(schema_data, service_name)
            except Exception as e:
                print(f"OpenAI validation skipped for {service_name}: {e}")
            
            anthropic_errors = []
            try:
                anthropic_errors = validate_schema_with_anthropic(schema_data, service_name)
            except Exception as e:
                print(f"Anthropic validation skipped for {service_name}: {e}")
            
            # Combine all errors
            all_errors = structure_errors + array_errors + object_errors + nested_errors + type_errors + genai_errors + openai_errors + anthropic_errors
            
            if all_errors:
                invalid_functions[service_name] = all_errors
                print(f"❌ {service_name}: {len(all_errors)} errors found")
            else:
                print(f"✅ {service_name}: Valid")
                
        except json.JSONDecodeError as e:
            print(f"❌ {service_name}: JSON decode error - {e}")
            invalid_functions[service_name] = [f"JSON decode error: {e}"]
        except Exception as e:
            print(f"❌ {service_name}: Unexpected error - {e}")
            invalid_functions[service_name] = [f"Unexpected error: {e}"]
    
    return invalid_functions

def validate_single_schema_file(schema_file_path: str, package_name: str = None) -> List[str]:
    """
    Validates a single schema file and returns any errors.
    
    Args:
        schema_file_path: Path to the schema file to validate
        package_name: Optional package name to use instead of extracting from filename
    
    Returns:
        List of error messages
    """
    errors = []
    
    try:
        with open(schema_file_path, 'r') as f:
            schema_data = json.load(f)
        
        if not isinstance(schema_data, list):
            return [f"Schema is not a list of function declarations"]
        
        service_name = package_name if package_name else Path(schema_file_path).stem
        
        # Run all validations
        structure_errors = validate_schema_structure(schema_data, service_name)
        array_errors = validate_array_items_in_declarations(schema_data)
        object_errors = validate_object_properties_in_declarations(schema_data)
        
        # Check for nested schema issues
        nested_errors = []
        type_errors = []
        for func_def in schema_data:
            # Validate the entire function definition recursively
            nested_errors.extend(validate_nested_schema_recursive(func_def, func_def.get("name", "unnamed_function")))
            type_errors.extend(validate_type_values(func_def, func_def.get("name", "unnamed_function")))
        
        # Try GenAI validation
        genai_errors = []
        try:
            genai_errors = validate_schema_with_genai(schema_data, service_name)
        except Exception as e:
            print(f"GenAI validation skipped: {e}")
        
        openai_errors = []
        try:
            openai_errors = validate_schema_with_openai(schema_data, service_name)
        except Exception as e:
            print(f"OpenAI validation skipped: {e}")
        
        anthropic_errors = []
        try:
            anthropic_errors = validate_schema_with_anthropic(schema_data, service_name)
        except Exception as e:
            print(f"Anthropic validation skipped: {e}")
        
        errors = structure_errors + array_errors + object_errors + nested_errors + type_errors + genai_errors + openai_errors + anthropic_errors
                
    except json.JSONDecodeError as e:
        errors.append(f"JSON decode error: {e}")
    except Exception as e:
        errors.append(f"Unexpected error: {e}")
    
    return errors

def format_invalid_functions_report(invalid_functions: Dict[str, List[str]]) -> str:
    """
    Formats the invalid functions into a readable report.
    
    Args:
        invalid_functions: Dictionary of invalid functions by service
    
    Returns:
        Formatted report string
    """
    if not invalid_functions:
        return "✅ All schemas are valid!"
    
    report = "❌ Invalid schemas found:\n\n"
    
    for service_name, errors in invalid_functions.items():
        report += f"📁 {service_name}:\n"
        for error in errors:
            report += f"  • {error}\n"
        report += "\n"
    
    return report

def get_invalid_function_names(invalid_functions: Dict[str, List[str]]) -> List[str]:
    """
    Extracts just the invalid function names in the format 'service-function_name'.
    
    Args:
        invalid_functions: Dictionary of invalid functions by service
    
    Returns:
        List of invalid function names in 'service-function_name' format
    """
    invalid_names = []
    
    for service_name, errors in invalid_functions.items():
        for error in errors:
            # Extract function name from error message
            if "-" in error and ":" in error:
                # Format: "service-function_name: error message"
                function_part = error.split(":")[0]
                invalid_names.append(function_part)
            else:
                # If we can't parse it, just add the service name
                invalid_names.append(service_name)
    
    return list(set(invalid_names))  # Remove duplicates

def main():
    """
    Main function to run the schema validation.
    """
    print("🔍 Starting schema validation...\n")
    
    # Validate all schemas
    invalid_functions = validate_all_schemas()
    
    # Print summary
    print("\n" + "="*50)
    print("VALIDATION SUMMARY")
    print("="*50)
    
    if invalid_functions:
        print(f"❌ Found {len(invalid_functions)} services with invalid schemas:")
        for service_name in invalid_functions.keys():
            print(f"  • {service_name}")
        
        # Get invalid function names
        invalid_names = get_invalid_function_names(invalid_functions)
        print(f"\nInvalid function names ({len(invalid_names)} total):")
        for name in invalid_names:
            print(f"  • {name}")
        
        print("\n" + "="*50)
        print("DETAILED REPORT")
        print("="*50)
        print(format_invalid_functions_report(invalid_functions))
        
        # Return the invalid functions for programmatic use
        return invalid_functions, invalid_names
    else:
        print("✅ All schemas are valid!")
        return {}, []

def test_specific_schemas():
    """
    Test function to validate specific schemas that are known to have issues.
    """
    print("🧪 Testing specific schemas for known issues...\n")
    
    # Test the schemas you mentioned
    test_files = [
        ("workday", "Schemas/workday.json"),
        ("gdrive", "Schemas/gdrive.json"), 
        ("code_execution", "Schemas/code_execution.json")
    ]
    
    for service_name, file_path in test_files:
        print(f"Testing {service_name}...")
        try:
            errors = validate_single_schema_file(file_path)
            if errors:
                print(f"❌ {service_name}: {len(errors)} errors found")
                for error in errors[:5]:  # Show first 5 errors
                    print(f"  • {error}")
                if len(errors) > 5:
                    print(f"  ... and {len(errors) - 5} more errors")
            else:
                print(f"✅ {service_name}: Valid")
        except Exception as e:
            print(f"❌ {service_name}: Error reading file - {e}")
        print()

def test_bad_schema_example():
    """
    Test function to demonstrate validation of a bad schema like the one in the original code.
    """
    print("🧪 Testing bad schema example...\n")
    
    # This is the bad schema from the original code
    bad_schema = [
        {
            "name": "azmcp_appconfig_kv_unlock",
            "description": "Unlock a key-value setting in an App Configuration store.",
            "parameters": {
                "type": "array"
            }
        }
    ]
    
    # Test the validation functions
    structure_errors = validate_schema_structure(bad_schema, "test")
    array_errors = validate_array_items_in_declarations(bad_schema)
    object_errors = validate_object_properties_in_declarations(bad_schema)
    nested_errors = []
    type_errors = []
    for func_def in bad_schema:
        nested_errors.extend(validate_nested_schema_recursive(func_def, func_def.get("name", "unnamed_function")))
        type_errors.extend(validate_type_values(func_def, func_def.get("name", "unnamed_function")))
    
    all_errors = structure_errors + array_errors + object_errors + nested_errors + type_errors
    
    if all_errors:
        print("✅ Correctly caught bad schema errors:")
        for error in all_errors:
            print(f"  • {error}")
    else:
        print("❌ Failed to catch bad schema errors")
    
    print()

def test_bad_object_schema_example():
    """
    Test function to demonstrate validation of object types without properties.
    """
    print("🧪 Testing bad object schema example...\n")
    
    # This is a bad schema with object type missing properties
    bad_object_schema = [
        {
            "name": "test_object_function",
            "description": "Test function with object type missing properties",
            "parameters": {
                "type": "object"
                # Missing properties field
            }
        }
    ]
    
    # Test the validation functions
    structure_errors = validate_schema_structure(bad_object_schema, "test")
    array_errors = validate_array_items_in_declarations(bad_object_schema)
    object_errors = validate_object_properties_in_declarations(bad_object_schema)
    nested_errors = []
    type_errors = []
    for func_def in bad_object_schema:
        nested_errors.extend(validate_nested_schema_recursive(func_def, func_def.get("name", "unnamed_function")))
        type_errors.extend(validate_type_values(func_def, func_def.get("name", "unnamed_function")))
    
    all_errors = structure_errors + array_errors + object_errors + nested_errors + type_errors
    
    if all_errors:
        print("✅ Correctly caught bad object schema errors:")
        for error in all_errors:
            print(f"  • {error}")
    else:
        print("❌ Failed to catch bad object schema errors")
    
    print()

def test_invalid_types():
    """
    Test function to demonstrate validation of schemas with invalid type values.
    """
    print("🧪 Testing invalid type values...\n")
    
    # Schema with invalid types including anyOf union
    invalid_type_schema = [
        {
            "name": "test_function",
            "description": "Test function with invalid types",
            "parameters": {
                "type": "object",
                "properties": {
                    "valid_string": {
                        "type": "string",
                        "description": "This is valid"
                    },
                    "invalid_type": {
                        "type": "invalid_type",
                        "description": "This should be caught"
                    },
                    "another_invalid": {
                        "type": "float",
                        "description": "This should also be caught"
                    },
                    "union_with_invalid": {
                        "anyOf": [
                            {
                                "type": "string"
                            },
                            {
                                "type": "bytes"
                            }
                        ],
                        "description": "Union with invalid bytes type"
                    },
                    "nested_object": {
                        "type": "object",
                        "properties": {
                            "nested_invalid": {
                                "type": "double",
                                "description": "Nested invalid type"
                            }
                        }
                    }
                }
            }
        }
    ]
    
    # Test the validation functions
    structure_errors = validate_schema_structure(invalid_type_schema, "test")
    array_errors = validate_array_items_in_declarations(invalid_type_schema)
    nested_errors = []
    type_errors = []
    for func_def in invalid_type_schema:
        nested_errors.extend(validate_nested_schema_recursive(func_def, func_def.get("name", "unnamed_function")))
        type_errors.extend(validate_type_values(func_def, func_def.get("name", "unnamed_function")))
    
    all_errors = structure_errors + array_errors + nested_errors + type_errors
    
    if type_errors:
        print("✅ Correctly caught invalid type errors:")
        for error in type_errors:
            print(f"  • {error}")
    else:
        print("❌ Failed to catch invalid type errors")
    
    print()

if __name__ == "__main__":
    # Run the specific tests first
    test_bad_schema_example()
    test_bad_object_schema_example()
    test_invalid_types()
    test_specific_schemas()
    
    # Then run the full validation
    print("="*60)
    invalid_functions, invalid_names = main() 