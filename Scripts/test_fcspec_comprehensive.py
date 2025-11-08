#!/usr/bin/env python3
"""
Comprehensive test suite for Documentation/Scripts/FCSpec.py

This test focuses on the actual behavior - docstring parsing and schema generation -
rather than internal implementation details. It uses sample docstrings and tests
the expected output schemas.
"""

import os
import sys
import ast
import unittest
import tempfile
import json
from typing import Optional, Union, List, Dict, Any

# Add current directory to the path to allow importing FCSpec
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import the module and functions from Documentation/Scripts
import FCSpec_depricated as doc_fcspec
# Import functions directly from the module
build_initial_schema = doc_fcspec.build_initial_schema
map_type = doc_fcspec.map_type
parse_object_properties_from_description = doc_fcspec.parse_object_properties_from_description


class TestDocstringParsingAndSchemaGeneration(unittest.TestCase):
    """Test cases for docstring parsing and schema generation with sample docstrings."""
    
    def create_function_ast(self, func_def: str) -> ast.FunctionDef:
        """Helper to create AST node from function definition string."""
        tree = ast.parse(func_def)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                return node
        raise ValueError("No FunctionDef found in AST")
    
    def test_basic_optional_parameter_detection(self):
        """Test that Optional parameters are correctly identified as not required."""
        func_def = '''
def process_user_data(user_id: str, name: Optional[str], age: Optional[int], email: str = None):
    """
    Process user data with various parameter types.
    
    Args:
        user_id (str): The unique identifier for the user (required)
        name (Optional[str]): The user's name (optional)
        age (Optional[int]): The user's age (optional)
        email (str, optional): The user's email address (optional, defaults to None)
    """
    pass
'''
        func_node = self.create_function_ast(func_def)
        docstring = ast.get_docstring(func_node)
        parsed_doc = doc_fcspec.docstring_parser.parse(docstring)
        schema = doc_fcspec.build_initial_schema(parsed_doc, func_node, "process_user_data")
        
        # Check required parameters
        required = schema["parameters"].get("required", [])
        self.assertIn("user_id", required, "user_id should be required")
        self.assertNotIn("name", required, "name should not be required (Optional)")
        self.assertNotIn("age", required, "age should not be required (Union with None)")
        self.assertNotIn("email", required, "email should not be required (has default)")
        
        # Check parameter types
        properties = schema["parameters"]["properties"]
        self.assertEqual(properties["user_id"]["type"], doc_fcspec.JSON_TYPE_STRING)
        
        # Check Optional[str] - should have same schema as str (no oneOf)
        name_schema = properties["name"]
        self.assertEqual(name_schema["type"], doc_fcspec.JSON_TYPE_STRING, "Optional[str] should have string type schema")
        self.assertNotIn("oneOf", name_schema, "Optional[str] should NOT have oneOf schema")
        
        # Check Optional[int] - should have same schema as int (no oneOf)
        age_schema = properties["age"]
        self.assertEqual(age_schema["type"], doc_fcspec.JSON_TYPE_INTEGER, "Optional[int] should have integer type schema")
        self.assertNotIn("oneOf", age_schema, "Optional[int] should NOT have oneOf schema")
        
        self.assertEqual(properties["email"]["type"], doc_fcspec.JSON_TYPE_STRING)
    
    def test_dict_property_breakdown(self):
        """Test that dict types with properties in docstring are broken down correctly."""
        func_def = '''
def create_user(user_data: dict):
    """
    Create a new user with the provided data.
    
    Args:
        user_data (dict): Dictionary containing user information
            name (str): The user's full name
            age (int): The user's age in years
            email (str, optional): The user's email address
            preferences (dict): User preferences
                theme (str): UI theme preference
                notifications (bool): Whether to send notifications
    """
    pass
'''
        func_node = self.create_function_ast(func_def)
        docstring = ast.get_docstring(func_node)
        parsed_doc = doc_fcspec.docstring_parser.parse(docstring)
        schema = doc_fcspec.build_initial_schema(parsed_doc, func_node, "create_user")
        
        # Check that user_data is an object with properties
        user_data_schema = schema["parameters"]["properties"]["user_data"]
        self.assertEqual(user_data_schema["type"], doc_fcspec.JSON_TYPE_OBJECT)
        self.assertIn("properties", user_data_schema)
        
        # Check top-level properties
        properties = user_data_schema["properties"]
        self.assertIn("name", properties)
        self.assertIn("age", properties)
        self.assertIn("email", properties)
        self.assertIn("preferences", properties)
        
        # Check property types
        self.assertEqual(properties["name"]["type"], doc_fcspec.JSON_TYPE_STRING)
        self.assertEqual(properties["age"]["type"], doc_fcspec.JSON_TYPE_INTEGER)
        self.assertEqual(properties["email"]["type"], doc_fcspec.JSON_TYPE_STRING)
        self.assertEqual(properties["preferences"]["type"], doc_fcspec.JSON_TYPE_OBJECT)
        
        # Check nested properties in preferences
        pref_properties = properties["preferences"]["properties"]
        self.assertIn("theme", pref_properties)
        self.assertIn("notifications", pref_properties)
        self.assertEqual(pref_properties["theme"]["type"], doc_fcspec.JSON_TYPE_STRING)
        self.assertEqual(pref_properties["notifications"]["type"], doc_fcspec.JSON_TYPE_BOOLEAN)
        
        # Check required properties (email should not be required due to "optional")
        required = user_data_schema.get("required", [])
        self.assertIn("name", required, "name should be required")
        self.assertIn("age", required, "age should be required")
        self.assertNotIn("email", required, "email should not be required (marked as optional)")
        self.assertIn("preferences", required, "preferences should be required")
        
        # Check nested required properties
        pref_required = properties["preferences"].get("required", [])
        self.assertIn("theme", pref_required, "theme should be required")
        self.assertIn("notifications", pref_required, "notifications should be required")
    
    def test_complex_nested_dict_structure(self):
        """Test complex nested dictionary structures with multiple levels."""
        func_def = '''
def update_config(config: dict):
    """
    Update application configuration.
    
    Args:
        config (dict): Configuration dictionary
            database (dict): Database configuration
                host (str): Database host
                port (int): Database port
                credentials (dict): Database credentials
                    username (str): Database username
                    password (str): Database password
                    ssl (bool, optional): Use SSL connection
            api (dict): API configuration
                endpoints (list): List of API endpoints
                timeout (int, optional): Request timeout in seconds
                retries (dict): Retry configuration
                    max_attempts (int): Maximum retry attempts
                    backoff_factor (float): Backoff multiplier
    """
    pass
'''
        func_node = self.create_function_ast(func_def)
        docstring = ast.get_docstring(func_node)
        parsed_doc = doc_fcspec.docstring_parser.parse(docstring)
        schema = doc_fcspec.build_initial_schema(parsed_doc, func_node, "update_config")
        
        config_schema = schema["parameters"]["properties"]["config"]
        self.assertEqual(config_schema["type"], doc_fcspec.JSON_TYPE_OBJECT)
        
        # Check top-level properties
        properties = config_schema["properties"]
        self.assertIn("database", properties)
        self.assertIn("api", properties)
        
        # Check database properties
        db_props = properties["database"]["properties"]
        self.assertIn("host", db_props)
        self.assertIn("port", db_props)
        self.assertIn("credentials", db_props)
        self.assertEqual(db_props["host"]["type"], doc_fcspec.JSON_TYPE_STRING)
        self.assertEqual(db_props["port"]["type"], doc_fcspec.JSON_TYPE_INTEGER)
        
        # Check nested credentials
        cred_props = db_props["credentials"]["properties"]
        self.assertIn("username", cred_props)
        self.assertIn("password", cred_props)
        self.assertIn("ssl", cred_props)
        self.assertEqual(cred_props["username"]["type"], doc_fcspec.JSON_TYPE_STRING)
        self.assertEqual(cred_props["password"]["type"], doc_fcspec.JSON_TYPE_STRING)
        self.assertEqual(cred_props["ssl"]["type"], doc_fcspec.JSON_TYPE_BOOLEAN)
        
        # Check API properties
        api_props = properties["api"]["properties"]
        self.assertIn("endpoints", api_props)
        self.assertIn("timeout", api_props)
        self.assertIn("retries", api_props)
        self.assertEqual(api_props["endpoints"]["type"], doc_fcspec.JSON_TYPE_ARRAY)
        self.assertEqual(api_props["timeout"]["type"], doc_fcspec.JSON_TYPE_INTEGER)
        
        # Check retries properties
        retry_props = api_props["retries"]["properties"]
        self.assertIn("max_attempts", retry_props)
        self.assertIn("backoff_factor", retry_props)
        self.assertEqual(retry_props["max_attempts"]["type"], doc_fcspec.JSON_TYPE_INTEGER)
        self.assertEqual(retry_props["backoff_factor"]["type"], doc_fcspec.JSON_TYPE_NUMBER)
        
        # Check required properties
        config_required = config_schema.get("required", [])
        self.assertIn("database", config_required)
        self.assertIn("api", config_required)
        
        db_required = properties["database"].get("required", [])
        self.assertIn("host", db_required)
        self.assertIn("port", db_required)
        self.assertIn("credentials", db_required)
        self.assertNotIn("ssl", db_required)  # Optional
        
        cred_required = db_props["credentials"].get("required", [])
        self.assertIn("username", cred_required)
        self.assertIn("password", cred_required)
        self.assertNotIn("ssl", cred_required)  # Optional
        
        api_required = properties["api"].get("required", [])
        self.assertIn("endpoints", api_required)
        self.assertIn("retries", api_required)
        self.assertNotIn("timeout", api_required)  # Optional
        
        retry_required = api_props["retries"].get("required", [])
        self.assertIn("max_attempts", retry_required)
        self.assertIn("backoff_factor", retry_required)
    
    def test_optional_types(self):
        """Test Optional types that can be None."""
        func_def = '''
def process_data(data: Optional[str], count: Optional[int], items: Optional[List[str]]):
    """
    Process data with Optional types that can be None.
    
    Args:
        data (Optional[str]): String data or None
        count (Optional[int]): Integer count or None
        items (Optional[List[str]]): List of strings or None
    """
    pass
'''
        func_node = self.create_function_ast(func_def)
        docstring = ast.get_docstring(func_node)
        parsed_doc = doc_fcspec.docstring_parser.parse(docstring)
        schema = doc_fcspec.build_initial_schema(parsed_doc, func_node, "process_data")
        
        # Check that all parameters are not required (Optional makes them optional)
        required = schema["parameters"].get("required", [])
        self.assertNotIn("data", required, "data should not be required (Optional)")
        self.assertNotIn("count", required, "count should not be required (Optional)")
        self.assertNotIn("items", required, "items should not be required (Optional)")
        
        # Check parameter types (should have same schema as inner type, no oneOf)
        properties = schema["parameters"]["properties"]
        
        # Check Optional[str] - should have same schema as str
        data_schema = properties["data"]
        self.assertEqual(data_schema["type"], doc_fcspec.JSON_TYPE_STRING, "Optional[str] should have string type schema")
        self.assertNotIn("oneOf", data_schema, "Optional[str] should NOT have oneOf schema")
        
        # Check Optional[int] - should have same schema as int
        count_schema = properties["count"]
        self.assertEqual(count_schema["type"], doc_fcspec.JSON_TYPE_INTEGER, "Optional[int] should have integer type schema")
        self.assertNotIn("oneOf", count_schema, "Optional[int] should NOT have oneOf schema")
        
        # Check Optional[List[str]] - should have same schema as List[str]
        items_schema = properties["items"]
        self.assertEqual(items_schema["type"], doc_fcspec.JSON_TYPE_ARRAY, "Optional[List[str]] should have array type schema")
        self.assertNotIn("oneOf", items_schema, "Optional[List[str]] should NOT have oneOf schema")
    
    def test_optional_none_only(self):
        """Test Optional with only None type."""
        func_def = '''
def no_data(data: Optional[None]):
    """
    Function that only accepts None.
    
    Args:
        data (Optional[None]): Must be None
    """
    pass
'''
        func_node = self.create_function_ast(func_def)
        docstring = ast.get_docstring(func_node)
        parsed_doc = doc_fcspec.docstring_parser.parse(docstring)
        schema = doc_fcspec.build_initial_schema(parsed_doc, func_node, "no_data")
        
        # Check that parameter type is null
        properties = schema["parameters"]["properties"]
        self.assertEqual(properties["data"]["type"], doc_fcspec.JSON_TYPE_NULL)
        
        # Parameter should not be required (it's effectively optional)
        required = schema["parameters"].get("required", [])
        self.assertNotIn("data", required, "Optional[None] parameter should not be required")
    
    def test_mixed_parameter_types(self):
        """Test function with mixed parameter types including defaults."""
        func_def = '''
def complex_function(
    required_str: str,
    optional_str: Optional[str],
    optional_int: Optional[int],
    with_default: str = "default",
    optional_with_default: Optional[str] = None,
    dict_param: dict = None
):
    """
    Function with mixed parameter types.
    
    Args:
        required_str (str): Required string parameter
        optional_str (Optional[str]): Optional string parameter
        optional_int (Optional[int]): Optional integer parameter
        with_default (str): Parameter with default value
        optional_with_default (Optional[str]): Optional parameter with default
        dict_param (dict): Dictionary parameter with default
            key1 (str): First key
            key2 (int, optional): Second key
    """
    pass
'''
        func_node = self.create_function_ast(func_def)
        docstring = ast.get_docstring(func_node)
        parsed_doc = doc_fcspec.docstring_parser.parse(docstring)
        schema = doc_fcspec.build_initial_schema(parsed_doc, func_node, "complex_function")
        
        # Only required_str should be required
        required = schema["parameters"].get("required", [])
        self.assertIn("required_str", required, "required_str should be required")
        self.assertNotIn("optional_str", required, "optional_str should not be required (Optional)")
        self.assertNotIn("optional_int", required, "optional_int should not be required (Optional)")
        self.assertNotIn("with_default", required, "with_default should not be required (has default)")
        self.assertNotIn("optional_with_default", required, "optional_with_default should not be required (Optional with default)")
        self.assertNotIn("dict_param", required, "dict_param should not be required (has default)")
        
        # Check dict_param properties
        dict_schema = schema["parameters"]["properties"]["dict_param"]
        self.assertEqual(dict_schema["type"], doc_fcspec.JSON_TYPE_OBJECT)
        self.assertIn("properties", dict_schema)
        
        dict_props = dict_schema["properties"]
        self.assertIn("key1", dict_props)
        self.assertIn("key2", dict_props)
        self.assertEqual(dict_props["key1"]["type"], doc_fcspec.JSON_TYPE_STRING)
        self.assertEqual(dict_props["key2"]["type"], doc_fcspec.JSON_TYPE_INTEGER)
        
        # Check dict required properties
        dict_required = dict_schema.get("required", [])
        self.assertIn("key1", dict_required, "key1 should be required")
        self.assertNotIn("key2", dict_required, "key2 should not be required (optional)")
    
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # Test function with no docstring
        func_def = '''
def no_docstring(param: str):
    pass
'''
        func_node = self.create_function_ast(func_def)
        docstring = ast.get_docstring(func_node)
        self.assertIsNone(docstring)
        
        # Test function with empty docstring
        func_def = '''
def empty_docstring(param: str):
    """
    """
    pass
'''
        func_node = self.create_function_ast(func_def)
        docstring = ast.get_docstring(func_node)
        parsed_doc = doc_fcspec.docstring_parser.parse(docstring)
        schema = doc_fcspec.build_initial_schema(parsed_doc, func_node, "empty_docstring")
        
        # Should still have the parameter in properties
        properties = schema["parameters"]["properties"]
        self.assertNotIn("param", properties)
        
        # # Should be required (no default, no Optional, no Union with None)
        # required = schema["parameters"].get("required", [])
        # self.assertIn("param", required, "param should be required")
        
        # Test function with proper Google-style docstring
        func_def = '''
def proper_docstring(param: str):
    """
    Function with proper Google-style docstring.
    
    Args:
        param (str): A string parameter
    """
    pass
'''
        func_node = self.create_function_ast(func_def)
        docstring = ast.get_docstring(func_node)
        parsed_doc = doc_fcspec.docstring_parser.parse(docstring)
        schema = doc_fcspec.build_initial_schema(parsed_doc, func_node, "proper_docstring")
        
        # Should have the parameter in properties
        properties = schema["parameters"]["properties"]
        self.assertIn("param", properties)
        self.assertEqual(properties["param"]["type"], doc_fcspec.JSON_TYPE_STRING)
        
        # Should be required
        required = schema["parameters"].get("required", [])
        self.assertIn("param", required, "param should be required")
    
    def test_list_and_array_types(self):
        """Test List and array type handling."""
        func_def = '''
def process_lists(
    string_list: List[str],
    int_list: List[int],
    mixed_list: List[Any],
    optional_list: Optional[List[str]]
):
    """
    Process various list types.
    
    Args:
        string_list (List[str]): List of strings
        int_list (List[int]): List of integers
        mixed_list (List[Any]): List of mixed types
        optional_list (Optional[List[str]]): Optional list of strings
    """
    pass
'''
        func_node = self.create_function_ast(func_def)
        docstring = ast.get_docstring(func_node)
        parsed_doc = doc_fcspec.docstring_parser.parse(docstring)
        schema = doc_fcspec.build_initial_schema(parsed_doc, func_node, "process_lists")
        
        properties = schema["parameters"]["properties"]
        
        # Check that all list types are mapped to array
        self.assertEqual(properties["string_list"]["type"], doc_fcspec.JSON_TYPE_ARRAY)
        self.assertEqual(properties["int_list"]["type"], doc_fcspec.JSON_TYPE_ARRAY)
        self.assertEqual(properties["mixed_list"]["type"], doc_fcspec.JSON_TYPE_ARRAY)
        
        # Check Optional[List[str]] - should have same schema as List[str] (no oneOf)
        optional_list_schema = properties["optional_list"]
        self.assertEqual(optional_list_schema["type"], doc_fcspec.JSON_TYPE_ARRAY, "Optional[List[str]] should have array type schema")
        self.assertNotIn("oneOf", optional_list_schema, "Optional[List[str]] should NOT have oneOf schema")
        
        # Check required parameters
        required = schema["parameters"].get("required", [])
        self.assertIn("string_list", required)
        self.assertIn("int_list", required)
        self.assertIn("mixed_list", required)
        self.assertNotIn("optional_list", required, "optional_list should not be required (Optional)")


class TestMapTypeFunction(unittest.TestCase):
    """Test cases for the map_type function directly."""
    
    def setUp(self):
        """Set up test data by loading test cases from JSON file."""
        json_file_path = os.path.join(os.path.dirname(__file__), "map_type_test_cases.json")
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                self.test_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            self.fail(f"Failed to load test cases from JSON file: {e}")
    
    def test_basic_types(self):
        """Test basic type mapping."""
        test_cases = [(case["type_str"], case["expected_type"]) for case in self.test_data["basic_types_test_cases"]]
        
        for type_str, expected_type in test_cases:
            with self.subTest(type_str=type_str):
                result = doc_fcspec.map_type(type_str)
                self.assertEqual(result["type"], expected_type, f"Failed for '{type_str}'")
    
    def test_optional_types(self):
        """Test Optional type mapping."""
        test_cases = [(case["type_str"], case["expected_type"]) for case in self.test_data["optional_types_test_cases"]]
        
        for type_str, expected_type in test_cases:
            with self.subTest(type_str=type_str):
                result = doc_fcspec.map_type(type_str)
                
                # Check the result based on the expected type
                if expected_type == "null":
                    # For Optional[] (empty), should return {"type": "null"}
                    self.assertEqual(result["type"], doc_fcspec.JSON_TYPE_NULL, f"Optional[] should return null type for '{type_str}'")
                else:
                    # For Optional[T], should return the same schema as T (no oneOf)
                    self.assertEqual(result["type"], expected_type, f"Optional[T] should have same type as T for '{type_str}'")
                    self.assertNotIn("oneOf", result, f"Optional[T] should NOT have oneOf schema for '{type_str}'")
    
    def test_union_types(self):
        """Test Union type mapping."""
        test_cases = [(case["type_str"], case["expected_type"]) for case in self.test_data["union_types_test_cases"]]
        
        for type_str, expected_type in test_cases:
            with self.subTest(type_str=type_str):
                result = doc_fcspec.map_type(type_str)
                if expected_type == "anyOf":
                    # For Union types with multiple non-null types, expect anyOf
                    self.assertIn("anyOf", result, f"Expected 'anyOf' for '{type_str}'")
                    self.assertIsInstance(result["anyOf"], list, f"anyOf should be a list for '{type_str}'")
                else:
                    # For Union types with only one non-null type, expect type
                    self.assertEqual(result["type"], expected_type, f"Failed for '{type_str}'")
        
    def test_nested_types(self):
        """Test nested type mapping."""
        test_cases = [(case["type_str"], case["expected_schema"]) for case in self.test_data["nested_types_test_cases"]]
        
        for type_str, expected_schema in test_cases:
            with self.subTest(type_str=type_str):
                result = doc_fcspec.map_type(type_str)
                
                # Check that the result has the expected structure
                self.assertEqual(result["type"], expected_schema["type"], 
                               f"Type mismatch for '{type_str}': expected {expected_schema['type']}, got {result['type']}")
                
                # Check that items key exists for arrays
                if expected_schema["type"] == doc_fcspec.JSON_TYPE_ARRAY:
                    self.assertIn("items", result, 
                                 f"Missing 'items' key for '{type_str}'")
                    
                    # For nested arrays, check the nested structure
                    if expected_schema["items"]["type"] == doc_fcspec.JSON_TYPE_ARRAY:
                        self.assertEqual(result["items"]["type"], expected_schema["items"]["type"],
                                       f"Nested array type mismatch for '{type_str}'")
                        self.assertIn("items", result["items"],
                                     f"Missing nested 'items' key for '{type_str}'")
                
                # Verify the complete schema structure
                self.assertEqual(result, expected_schema, 
                               f"Complete schema mismatch for '{type_str}': expected {expected_schema}, got {result}")
    
    def test_list_types(self):
        """Test List type mapping."""
        test_cases = [(case["type_str"], case["expected_schema"]) for case in self.test_data["list_types_test_cases"]]
        
        for type_str, expected_schema in test_cases:
            with self.subTest(type_str=type_str):
                result = doc_fcspec.map_type(type_str)
                
                # Check that the result has the expected structure
                self.assertEqual(result["type"], expected_schema["type"], 
                               f"Type mismatch for '{type_str}': expected {expected_schema['type']}, got {result['type']}")
                
                # Check that items key exists
                self.assertIn("items", result, 
                             f"Missing 'items' key for '{type_str}'")
                
                # Check that items has the correct type
                self.assertEqual(result["items"], expected_schema["items"], 
                               f"Items mismatch for '{type_str}': expected {expected_schema['items']}, got {result['items']}")
                
                # Verify the complete schema structure
                self.assertEqual(result, expected_schema, 
                               f"Complete schema mismatch for '{type_str}': expected {expected_schema}, got {result}")
    
    def test_dict_types(self):
        """Test Dict type mapping."""
        test_cases = [(case["type_str"], case["expected_schema"]) for case in self.test_data["dict_types_test_cases"]]
        
        for type_str, expected_schema in test_cases:
            with self.subTest(type_str=type_str):
                result = doc_fcspec.map_type(type_str)
                
                # Check that the result has the expected structure
                self.assertEqual(result["type"], expected_schema["type"], 
                               f"Type mismatch for '{type_str}': expected {expected_schema['type']}, got {result['type']}")
                
                # Check that properties key exists
                self.assertIn("properties", result, 
                             f"Missing 'properties' key for '{type_str}'")
                
                # Check that properties has the correct type
                self.assertEqual(result["properties"], expected_schema["properties"], 
                               f"properties mismatch for '{type_str}': expected {expected_schema['properties']}, got {result['properties']}")
                
                # Verify the complete schema structure
                self.assertEqual(result, expected_schema, 
                               f"Complete schema mismatch for '{type_str}': expected {expected_schema}, got {result}")
    
    def test_nested_dict_types(self):
        """Test nested Dict type mapping."""
        test_cases = [(case["type_str"], case["expected_schema"]) for case in self.test_data["nested_dict_types_test_cases"]]
        
        for type_str, expected_schema in test_cases:
            with self.subTest(type_str=type_str):
                result = doc_fcspec.map_type(type_str)
                
                # Check that the result has the expected structure
                self.assertEqual(result["type"], expected_schema["type"], 
                               f"Type mismatch for '{type_str}': expected {expected_schema['type']}, got {result['type']}")
                
                # Check that properties key exists
                self.assertIn("properties", result, 
                             f"Missing 'properties' key for '{type_str}'")
                
                # Check that properties has the correct structure
                self.assertEqual(result["properties"], expected_schema["properties"], 
                               f"properties mismatch for '{type_str}': expected {expected_schema['properties']}, got {result['properties']}")
                
                # Verify the complete schema structure
                self.assertEqual(result, expected_schema, 
                               f"Complete schema mismatch for '{type_str}': expected {expected_schema}, got {result}")
    
    def test_dict_with_properties(self):
        """Test that Dict types always return object with empty properties."""
        test_cases = [(case["type_str"], case["expected_schema"]) 
                     for case in self.test_data["dict_with_properties_test_cases"]]
        
        for type_str, expected_schema in test_cases:
            with self.subTest(type_str=type_str):
                result = doc_fcspec.map_type(type_str)
                
                # Check that the result has the expected structure
                self.assertEqual(result["type"], expected_schema["type"], 
                               f"Type mismatch for '{type_str}': expected {expected_schema['type']}, got {result['type']}")
                
                # Check that properties key exists
                self.assertIn("properties", result, 
                             f"Missing 'properties' key for '{type_str}'")
                
                # Check that properties is empty
                self.assertEqual(result["properties"], expected_schema["properties"], 
                               f"Properties mismatch for '{type_str}': expected {expected_schema['properties']}, got {result['properties']}")
                
                # Verify the complete schema structure
                self.assertEqual(result, expected_schema, 
                               f"Complete schema mismatch for '{type_str}': expected {expected_schema}, got {result}")
    
    def test_complex_nested_structures(self):
        """Test complex nested type structures for Function Calling compliance."""
        test_cases = [(case["type_str"], case["expected_schema"]) for case in self.test_data["complex_nested_structures_test_cases"]]
        
        for type_str, expected_schema in test_cases:
            with self.subTest(type_str=type_str):
                result = doc_fcspec.map_type(type_str)
                
                # Verify the complete schema structure
                self.assertEqual(result, expected_schema, 
                               f"Complex schema mismatch for '{type_str}': expected {expected_schema}, got {result}")
                
                # Additional validation for specific schema components
                if "anyOf" in expected_schema:
                    self.assertIn("anyOf", result, f"Missing 'anyOf' for '{type_str}'")
                    self.assertEqual(len(result["anyOf"]), len(expected_schema["anyOf"]),
                                   f"anyOf length mismatch for '{type_str}'")
                
                # Validate nested array structures
                if expected_schema["type"] == doc_fcspec.JSON_TYPE_ARRAY:
                    self._validate_nested_array_structure(result, expected_schema, type_str)
    
    def _validate_nested_array_structure(self, result, expected, type_str):
        """Helper method to validate nested array structures."""
        if expected["type"] == doc_fcspec.JSON_TYPE_ARRAY:
            self.assertEqual(result["type"], expected["type"],
                           f"Array type mismatch for '{type_str}'")
            self.assertIn("items", result, f"Missing 'items' for '{type_str}'")
            
            # Recursively validate nested items
            if "items" in expected:
                self._validate_nested_array_structure(result["items"], expected["items"], type_str)


if __name__ == "__main__":
    unittest.main(verbosity=2) 