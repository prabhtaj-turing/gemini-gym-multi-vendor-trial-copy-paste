import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from call_llm.SimulationEngine import utils
from call_llm.SimulationEngine.custom_errors import ValidationError

class TestUtilsExtended(BaseTestCaseWithErrorHandler):
    """Additional test cases to cover missing lines in utils.py."""

    def test_is_optional_type_string_with_parenthesized_optional(self):
        """Test is_optional_type_string with parenthesized optional format (line 77)."""
        # Test the case where type_str has parentheses with "optional"
        type_str = "(str, optional)"
        self.assertTrue(utils.is_optional_type_string(type_str))
        
        # Test with different variations
        type_str2 = "(int, optional)"
        self.assertTrue(utils.is_optional_type_string(type_str2))
        
        type_str3 = "(list, optional)"
        self.assertTrue(utils.is_optional_type_string(type_str3))

    def test_is_optional_type_string_without_parentheses(self):
        """Test is_optional_type_string with non-parenthesized strings (line 77)."""
        # Test strings that don't have parentheses but contain "optional"
        type_str = "str, optional"
        self.assertTrue(utils.is_optional_type_string(type_str))
        
        # Test with different variations
        type_str2 = "int, optional"
        self.assertTrue(utils.is_optional_type_string(type_str2))

    def test_map_type_with_union_none_only(self):
        """Test map_type with Union containing only None (lines 102-111)."""
        # Test Union[None] - should return null type
        result = utils.map_type("Union[None]")
        self.assertEqual(result["type"], "null")
        
        # Test Union[NoneType] - should return null type
        result2 = utils.map_type("Union[NoneType]")
        self.assertEqual(result2["type"], "null")

    def test_map_type_with_list_types(self):
        """Test map_type with List types (lines 102-111)."""
        # Test List[str]
        result = utils.map_type("List[str]")
        self.assertEqual(result["type"], "array")
        self.assertIn("items", result)
        self.assertEqual(result["items"]["type"], "string")
        
        # Test list[str] (lowercase)
        result2 = utils.map_type("list[str]")
        self.assertEqual(result2["type"], "array")
        self.assertIn("items", result2)
        self.assertEqual(result2["items"]["type"], "string")
        
        # Test List with empty item type
        result3 = utils.map_type("List[]")
        self.assertEqual(result3["type"], "array")
        self.assertIn("items", result3)
        self.assertEqual(result3["items"]["type"], "object")  # Defaults to "Any"

    def test_map_type_with_dict_types(self):
        """Test map_type with Dict types (lines 102-111)."""
        # Test Dict[str, int]
        result = utils.map_type("Dict[str, int]")
        self.assertEqual(result["type"], "object")
        self.assertIn("properties", result)
        self.assertEqual(result["properties"], {})
        
        # Test dict[str, int] (lowercase)
        result2 = utils.map_type("dict[str, int]")
        self.assertEqual(result2["type"], "object")
        self.assertIn("properties", result2)
        self.assertEqual(result2["properties"], {})

    def test_parse_object_properties_from_description_with_nested_properties(self):
        """Test parse_object_properties_from_description with nested properties (lines 125-171)."""
        description = """
        Configuration settings.
        
        - settings (dict): Main settings
            - api_key (str): API key for authentication
            - timeout (int): Request timeout in seconds
        - metadata (dict, optional): Additional metadata
            - version (str): Version information
        """
        
        main_desc, props_schema = utils.parse_object_properties_from_description(description)
        
        self.assertIsNotNone(props_schema)
        self.assertIn("settings", props_schema["properties"])
        self.assertIn("metadata", props_schema["properties"])
        
        # Check that settings has nested properties
        settings_props = props_schema["properties"]["settings"]
        self.assertEqual(settings_props["type"], "object")
        self.assertIn("properties", settings_props)
        self.assertIn("api_key", settings_props["properties"])
        self.assertIn("timeout", settings_props["properties"])
        
        # Check that metadata has nested properties
        metadata_props = props_schema["properties"]["metadata"]
        self.assertEqual(metadata_props["type"], "object")
        self.assertIn("properties", metadata_props)
        self.assertIn("version", metadata_props["properties"])

    def test_parse_object_properties_from_description_with_required_properties(self):
        """Test parse_object_properties_from_description with required properties (lines 125-171)."""
        description = """
        User configuration.
        
        - username (str): User's username
        - email (str): User's email address
        - age (int, optional): User's age
        - preferences (dict, optional): User preferences
        """
        
        main_desc, props_schema = utils.parse_object_properties_from_description(description)
        
        self.assertIsNotNone(props_schema)
        self.assertIn("required", props_schema)
        required = props_schema["required"]
        
        # username and email should be required, age and preferences should not
        self.assertIn("username", required)
        self.assertIn("email", required)
        self.assertNotIn("age", required)
        self.assertNotIn("preferences", required)

    def test_parse_object_properties_from_description_with_complex_nesting(self):
        """Test parse_object_properties_from_description with complex nested structures (lines 125-171)."""
        description = """
        Complex data structure.
        
        - data (dict): Main data container
            - items (list): List of items
                - id (str): Item identifier
                - value (int): Item value
            - metadata (dict): Metadata information
                - created_at (str): Creation timestamp
                - updated_at (str, optional): Update timestamp
        """
        
        main_desc, props_schema = utils.parse_object_properties_from_description(description)
        
        self.assertIsNotNone(props_schema)
        data_props = props_schema["properties"]["data"]
        
        # Check nested structure
        self.assertEqual(data_props["type"], "object")
        self.assertIn("items", data_props["properties"])
        self.assertIn("metadata", data_props["properties"])
        
        # Check items has array type but no nested properties (parse_object_properties_from_description doesn't handle list nesting)
        items_props = data_props["properties"]["items"]
        self.assertEqual(items_props["type"], "array")  # list types map to array
        self.assertIn("description", items_props)  # should have description
        
        # Check metadata has nested properties
        metadata_props = data_props["properties"]["metadata"]
        self.assertEqual(metadata_props["type"], "object")
        self.assertIn("created_at", metadata_props["properties"])
        self.assertIn("updated_at", metadata_props["properties"])

    def test_docstring_to_fcspec_with_object_type_parameters(self):
        """Test docstring_to_fcspec with object type parameters (lines 207-209)."""
        docstring = """
        Process user data with complex configuration.
        
        Args:
            user_data (dict): User data to process
                - name (str): User's name
                - age (int): User's age
            config (dict): Processing configuration
                - mode (str): Processing mode
                - options (dict, optional): Additional options
        """
        
        result = utils.docstring_to_fcspec(docstring, "process_user_data")
        
        self.assertIn("parameters", result)
        self.assertIn("properties", result["parameters"])
        
        # Check that user_data has nested properties
        user_data_props = result["parameters"]["properties"]["user_data"]
        self.assertEqual(user_data_props["type"], "object")
        self.assertIn("properties", user_data_props)
        self.assertIn("name", user_data_props["properties"])
        self.assertIn("age", user_data_props["properties"])
        
        # Check that config has nested properties
        config_props = result["parameters"]["properties"]["config"]
        self.assertEqual(config_props["type"], "object")
        self.assertIn("properties", config_props)
        self.assertIn("mode", config_props["properties"])
        self.assertIn("options", config_props["properties"])

    def test_docstring_to_fcspec_with_required_parameters_from_object_types(self):
        """Test docstring_to_fcspec with required parameters from object types (lines 207-209)."""
        docstring = """
        Create user profile.
        
        Args:
            profile (dict): User profile data
                - name (str): User's full name
                - email (str): User's email address
                - preferences (dict, optional): User preferences
        """
        
        result = utils.docstring_to_fcspec(docstring, "create_profile")
        
        self.assertIn("parameters", result)
        self.assertIn("required", result["parameters"])
        
        # profile should be required
        self.assertIn("profile", result["parameters"]["required"])
        
        # Check nested properties
        profile_props = result["parameters"]["properties"]["profile"]
        self.assertEqual(profile_props["type"], "object")
        self.assertIn("properties", profile_props)
        self.assertIn("name", profile_props["properties"])
        self.assertIn("email", profile_props["properties"])
        self.assertIn("preferences", profile_props["properties"])

    def test_parse_object_properties_from_description_with_no_match(self):
        """Test parse_object_properties_from_description when no properties match regex (lines 125-171)."""
        description = "This is a simple description without any property definitions."
        
        main_desc, props_schema = utils.parse_object_properties_from_description(description)
        
        self.assertEqual(main_desc, description)
        self.assertIsNone(props_schema)

    def test_parse_object_properties_from_description_with_empty_lines(self):
        """Test parse_object_properties_from_description with empty lines in description (lines 125-171)."""
        description = """
        Configuration object.
        
        - setting1 (str): First setting
        
        - setting2 (int): Second setting
        
        - setting3 (bool, optional): Third setting
        """
        
        main_desc, props_schema = utils.parse_object_properties_from_description(description)
        
        self.assertIsNotNone(props_schema)
        self.assertIn("properties", props_schema)
        self.assertIn("setting1", props_schema["properties"])
        self.assertIn("setting2", props_schema["properties"])
        self.assertIn("setting3", props_schema["properties"])

    def test_parse_object_properties_from_description_with_indented_content(self):
        """Test parse_object_properties_from_description with indented content (lines 125-171)."""
        description = """
        API configuration.
        
        - endpoints (dict): API endpoints
            - users (str): Users endpoint URL
                This endpoint handles user operations
            - products (str): Products endpoint URL
                This endpoint handles product operations
        """
        
        main_desc, props_schema = utils.parse_object_properties_from_description(description)
        
        self.assertIsNotNone(props_schema)
        endpoints_props = props_schema["properties"]["endpoints"]
        
        # Check that the indented descriptions are captured
        self.assertEqual(endpoints_props["type"], "object")
        self.assertIn("properties", endpoints_props)
        self.assertIn("users", endpoints_props["properties"])
        self.assertIn("products", endpoints_props["properties"])

    def test_map_type_with_custom_class_fallback(self):
        """Test map_type fallback for custom classes (lines 102-111)."""
        # Test with a custom class name
        result = utils.map_type("CustomClass")
        self.assertEqual(result["type"], "object")
        
        # Test with another custom class
        result2 = utils.map_type("MyCustomType")
        self.assertEqual(result2["type"], "object")

    def test_is_optional_type_string_edge_cases(self):
        """Test is_optional_type_string with edge cases (line 77)."""
        # Test with empty string
        self.assertFalse(utils.is_optional_type_string(""))
        
        # Test with None
        self.assertFalse(utils.is_optional_type_string(None))
        
        # Test with whitespace only
        self.assertFalse(utils.is_optional_type_string("   "))
        
        # Test with non-optional type
        self.assertFalse(utils.is_optional_type_string("str"))
        self.assertFalse(utils.is_optional_type_string("int"))

    def test_parse_object_properties_from_description_with_non_matching_lines(self):
        """Test parse_object_properties_from_description with lines that don't match regex (lines 134-135)."""
        description = """
        Configuration object.
        
        - setting1 (str): First setting
        This is a comment line that doesn't match the regex pattern
        - setting2 (int): Second setting
        Another non-matching line
        - setting3 (bool, optional): Third setting
        """
        
        main_desc, props_schema = utils.parse_object_properties_from_description(description)
        
        self.assertIsNotNone(props_schema)
        self.assertIn("properties", props_schema)
        # Should still parse the valid properties despite non-matching lines
        self.assertIn("setting1", props_schema["properties"])
        self.assertIn("setting2", props_schema["properties"])
        self.assertIn("setting3", props_schema["properties"])

if __name__ == '__main__':
    unittest.main()
