import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from call_llm.SimulationEngine import utils
from call_llm.SimulationEngine.custom_errors import ValidationError

class TestUtilsHelpers(BaseTestCaseWithErrorHandler):
    """Test cases for utility functions in the SimulationEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_docstring = """
        Creates a new user account.
        
        Args:
            username (str): The username for the new account.
            email (str): The email address for the new account.
            password (str): The password for the new account.
            age (int, optional): The user's age.
            
        Returns:
            dict: User account information.
        """
        self.function_name = "create_user"

    def test_docstring_to_fcspec_basic(self):
        """Test basic docstring to FCSpec conversion."""
        fcspec = utils.docstring_to_fcspec(self.sample_docstring, self.function_name)
        
        self.assertIsInstance(fcspec, dict)
        self.assertEqual(fcspec["name"], "create_user")
        self.assertIn("Creates a new user account", fcspec["description"])
        self.assertIn("parameters", fcspec)
        self.assertIn("properties", fcspec["parameters"])
        self.assertIn("username", fcspec["parameters"]["properties"])
        self.assertIn("email", fcspec["parameters"]["properties"])
        self.assertIn("password", fcspec["parameters"]["properties"])

    def test_docstring_to_fcspec_no_parameters(self):
        """Test docstring conversion with no parameters."""
        no_params_docstring = """
        Gets the current system time.
        
        Returns:
            str: Current timestamp.
        """
        
        fcspec = utils.docstring_to_fcspec(no_params_docstring, "get_time")
        
        self.assertEqual(fcspec["name"], "get_time")
        self.assertIn("Gets the current system time", fcspec["description"])
        self.assertEqual(len(fcspec["parameters"]["properties"]), 0)

    def test_docstring_to_fcspec_complex_types(self):
        """Test docstring conversion with complex parameter types."""
        complex_docstring = """
        Analyzes data with advanced filtering.
        
        Args:
            data (list): The input data to analyze.
            filters (dict): Filter criteria with keys 'min_value', 'max_value'.
            options (dict, optional): Additional options like 'sort_by', 'limit'.
            threshold (float): Analysis threshold value.
            enabled (bool): Whether analysis is enabled.
            
        Returns:
            dict: Analysis results with 'summary' and 'details' keys.
        """
        
        fcspec = utils.docstring_to_fcspec(complex_docstring, "analyze_data")
        
        self.assertEqual(fcspec["name"], "analyze_data")
        properties = fcspec["parameters"]["properties"]
        
        # Check that all parameters are present
        self.assertIn("data", properties)
        self.assertIn("filters", properties)
        self.assertIn("options", properties)
        self.assertIn("threshold", properties)
        self.assertIn("enabled", properties)
        
        # Check types
        self.assertEqual(properties["data"]["type"], "array")
        self.assertEqual(properties["filters"]["type"], "object")
        self.assertEqual(properties["threshold"]["type"], "number")
        self.assertEqual(properties["enabled"]["type"], "boolean")

    def test_map_type_basic_types(self):
        """Test mapping of basic Python types to JSON schema types."""
        type_mappings = {
            "str": "string",
            "int": "integer", 
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object",
            "Any": "object"
        }
        
        for python_type, expected_json_type in type_mappings.items():
            result = utils.map_type(python_type)
            self.assertEqual(result["type"], expected_json_type)

    def test_map_type_optional_types(self):
        """Test mapping of Optional types."""
        optional_str = utils.map_type("Optional[str]")
        self.assertEqual(optional_str["type"], "string")
        
        optional_int = utils.map_type("Optional[int]")
        self.assertEqual(optional_int["type"], "integer")
        
        optional_list = utils.map_type("Optional[list]")
        self.assertEqual(optional_list["type"], "array")

    def test_map_type_union_types(self):
        """Test mapping of Union types."""
        # The actual implementation doesn't handle Union types with multiple non-None types
        # It just returns the first non-None type
        union_str_int = utils.map_type("Union[str, int]")
        self.assertEqual(union_str_int["type"], "string")  # Takes first type
        
        union_with_none = utils.map_type("Union[str, None]")
        self.assertEqual(union_with_none["type"], "string")

    def test_map_type_none_value(self):
        """Test mapping when type is None."""
        result = utils.map_type(None)
        self.assertEqual(result["type"], "object")

    def test_is_optional_type_string(self):
        """Test detection of optional type strings."""
        # Test Optional types
        self.assertTrue(utils.is_optional_type_string("Optional[str]"))
        self.assertTrue(utils.is_optional_type_string("Optional[int]"))
        
        # Test Union with None
        self.assertTrue(utils.is_optional_type_string("Union[str, None]"))
        self.assertTrue(utils.is_optional_type_string("Union[None, int]"))
        
        # Test non-optional types
        self.assertFalse(utils.is_optional_type_string("str"))
        self.assertFalse(utils.is_optional_type_string("int"))
        self.assertFalse(utils.is_optional_type_string("Union[str, int]"))
        
        # Test None input
        self.assertFalse(utils.is_optional_type_string(None))

    def test_split_comma_separated_types(self):
        """Test splitting comma-separated types respecting nested structures."""
        # Test simple comma separation
        result = utils._split_comma_separated_types("str, int, bool")
        self.assertEqual(result, ["str", "int", "bool"])
        
        # Test with nested structures
        result = utils._split_comma_separated_types("list[str], dict[str, int], bool")
        self.assertEqual(result, ["list[str]", "dict[str, int]", "bool"])
        
        # Test with spaces
        result = utils._split_comma_separated_types("str , int , bool")
        self.assertEqual(result, ["str", "int", "bool"])

    def test_docstring_to_fcspec_with_required_parameters(self):
        """Test that required parameters are correctly identified."""
        required_docstring = """
        Creates a user with required fields.
        
        Args:
            username (str): The username (required).
            email (str): The email (required).
            age (int, optional): The age (optional).
            
        Returns:
            dict: User information.
        """
        
        fcspec = utils.docstring_to_fcspec(required_docstring, "create_user")
        
        # username and email should be required, age should not
        required_params = fcspec["parameters"].get("required", [])
        self.assertIn("username", required_params)
        self.assertIn("email", required_params)
        self.assertNotIn("age", required_params)

    def test_docstring_to_fcspec_multiline_description(self):
        """Test handling of multiline descriptions."""
        multiline_docstring = """
        Performs complex calculations.
        
        This function handles various mathematical operations
        including addition, subtraction, multiplication,
        and division with proper error handling.
        
        Args:
            operation (str): The operation to perform.
            values (list): List of numeric values.
            
        Returns:
            float: The calculated result.
        """
        
        fcspec = utils.docstring_to_fcspec(multiline_docstring, "calculate")
        
        description = fcspec["description"]
        self.assertIn("Performs complex calculations", description)
        self.assertIn("mathematical operations", description)
        self.assertIn("error handling", description)

    def test_docstring_to_fcspec_empty_docstring(self):
        """Test handling of empty docstring."""
        # The function doesn't validate empty docstrings, it just processes them
        result = utils.docstring_to_fcspec("", "test_function")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "test_function")

    def test_docstring_to_fcspec_none_docstring(self):
        """Test handling of None docstring."""
        # The function doesn't validate None docstrings, it just processes them
        result = utils.docstring_to_fcspec(None, "test_function")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "test_function")

    def test_docstring_to_fcspec_empty_function_name(self):
        """Test handling of empty function name."""
        # The function doesn't validate empty function names, it just processes them
        result = utils.docstring_to_fcspec(self.sample_docstring, "")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "")

    def test_docstring_to_fcspec_none_function_name(self):
        """Test handling of None function name."""
        # The function doesn't validate None function names, it just processes them
        result = utils.docstring_to_fcspec(self.sample_docstring, None)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], None)

if __name__ == '__main__':
    unittest.main()
