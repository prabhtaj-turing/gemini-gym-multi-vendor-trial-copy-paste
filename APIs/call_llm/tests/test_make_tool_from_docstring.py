import unittest
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from call_llm import llm_execution
from call_llm.SimulationEngine.custom_errors import ValidationError

class TestMakeToolFromDocstring(BaseTestCaseWithErrorHandler):
    """Test cases for the make_tool_from_docstring function."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_docstring = """
        Creates a new user account.
        
        Args:
            username (str): The username for the new account.
            email (str): The email address for the new account.
            password (str): The password for the new account.
            
        Returns:
            dict: User account information.
        """
        self.function_name = "create_user"

    def test_make_tool_from_valid_docstring(self):
        """Test creating a tool from a valid docstring."""
        tool_dict = llm_execution.make_tool_from_docstring(self.valid_docstring, self.function_name)
        
        # Assert the type is dict and access data using keys
        self.assertIsInstance(tool_dict, dict)
        self.assertIn("tool", tool_dict)
        self.assertEqual(len(tool_dict["tool"]), 1)
        
        func_decl = tool_dict["tool"][0]
        self.assertEqual(func_decl["name"], "create_user")
        self.assertIn("Creates a new user account", func_decl["description"])
        self.assertIsNotNone(func_decl["parameters"])

    def test_make_tool_from_docstring_with_complex_params(self):
        """Test creating a tool with complex parameter descriptions."""
        complex_docstring = """
        Analyzes data with advanced filtering.
        
        Args:
            data (list): The input data to analyze.
            filters (dict): Filter criteria with keys 'min_value', 'max_value'.
            options (dict, optional): Additional options like 'sort_by', 'limit'.
            
        Returns:
            dict: Analysis results with 'summary' and 'details' keys.
        """
        
        tool_dict = llm_execution.make_tool_from_docstring(complex_docstring, "analyze_data")
        
        self.assertIsInstance(tool_dict, dict)
        func_decl = tool_dict["tool"][0]
        self.assertEqual(func_decl["name"], "analyze_data")
        self.assertIn("Analyzes data", func_decl["description"])

    def test_make_tool_from_docstring_with_no_args(self):
        """Test creating a tool from docstring with no parameters."""
        no_args_docstring = """
        Gets the current system time.
        
        Returns:
            str: Current timestamp.
        """
        
        tool_dict = llm_execution.make_tool_from_docstring(no_args_docstring, "get_time")
        
        self.assertIsInstance(tool_dict, dict)
        func_decl = tool_dict["tool"][0]
        self.assertEqual(func_decl["name"], "get_time")
        # Ensure parameters property exists but is empty
        self.assertEqual(len(func_decl["parameters"]["properties"]), 0)

    def test_make_tool_from_docstring_with_multiline_description(self):
        """Test creating a tool with multiline description."""
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
        
        tool_dict = llm_execution.make_tool_from_docstring(multiline_docstring, "calculate")
        
        self.assertIsInstance(tool_dict, dict)
        func_decl = tool_dict["tool"][0]
        self.assertEqual(func_decl["name"], "calculate")
        self.assertIn("Performs complex calculations", func_decl["description"])
        self.assertIn("mathematical operations", func_decl["description"])

    def test_make_tool_from_docstring_with_optional_parameters(self):
        """Test creating a tool with optional parameters."""
        optional_params_docstring = """
        Sends an email message.
        
        Args:
            to (str): Recipient email address.
            subject (str): Email subject line.
            body (str): Email body content.
            cc (list, optional): List of CC recipients.
            bcc (list, optional): List of BCC recipients.
            
        Returns:
            bool: True if email sent successfully.
        """
        
        tool_dict = llm_execution.make_tool_from_docstring(optional_params_docstring, "send_email")
        
        func_decl = tool_dict["tool"][0]
        self.assertEqual(func_decl["name"], "send_email")
        
        # Check that required parameters are correctly identified
        required_params = func_decl["parameters"].get("required", [])
        self.assertIn("to", required_params)
        self.assertIn("subject", required_params)
        self.assertIn("body", required_params)
        self.assertNotIn("cc", required_params)
        self.assertNotIn("bcc", required_params)

    def test_make_tool_from_docstring_with_union_types(self):
        """Test creating a tool with Union type parameters."""
        union_types_docstring = """
        Processes data with flexible input types.
        
        Args:
            data (Union[str, list]): Input data as string or list.
            format (Union[str, dict]): Format specification.
            options (Union[dict, None], optional): Processing options.
            
        Returns:
            Union[str, dict]: Processed data.
        """
        
        tool_dict = llm_execution.make_tool_from_docstring(union_types_docstring, "process_data")
        
        func_decl = tool_dict["tool"][0]
        self.assertEqual(func_decl["name"], "process_data")
        
        # Check that Union types are handled correctly
        properties = func_decl["parameters"]["properties"]
        self.assertIn("data", properties)
        self.assertIn("format", properties)

    def test_make_tool_from_docstring_with_nested_types(self):
        """Test creating a tool with nested type parameters."""
        nested_types_docstring = """
        Configures system settings.
        
        Args:
            settings (dict): Configuration settings with nested structure.
            metadata (dict, optional): Additional metadata.
            
        Returns:
            dict: Configuration status.
        """
        
        tool_dict = llm_execution.make_tool_from_docstring(nested_types_docstring, "configure_system")
        
        func_decl = tool_dict["tool"][0]
        self.assertEqual(func_decl["name"], "configure_system")
        
        properties = func_decl["parameters"]["properties"]
        self.assertIn("settings", properties)
        self.assertIn("metadata", properties)

    def test_make_tool_from_docstring_input_validation(self):
        """Test input validation for make_tool_from_docstring."""
        # Test with non-string docstring
        with self.assertRaises(ValidationError):
            llm_execution.make_tool_from_docstring(123, "test_function")
        
        # Test with empty docstring
        with self.assertRaises(ValidationError):
            llm_execution.make_tool_from_docstring("", "test_function")
        
        # Test with whitespace-only docstring
        with self.assertRaises(ValidationError):
            llm_execution.make_tool_from_docstring("   \n   ", "test_function")
        
        # Test with non-string function name
        with self.assertRaises(ValidationError):
            llm_execution.make_tool_from_docstring(self.valid_docstring, 123)
        
        # Test with empty function name
        with self.assertRaises(ValidationError):
            llm_execution.make_tool_from_docstring(self.valid_docstring, "")
        
        # Test with whitespace-only function name
        with self.assertRaises(ValidationError):
            llm_execution.make_tool_from_docstring(self.valid_docstring, "   ")

    def test_make_tool_from_docstring_with_special_characters(self):
        """Test creating a tool with special characters in function name."""
        special_name = "create_user_v2.1"
        
        tool_dict = llm_execution.make_tool_from_docstring(self.valid_docstring, special_name)
        
        func_decl = tool_dict["tool"][0]
        self.assertEqual(func_decl["name"], special_name)

    def test_make_tool_from_docstring_with_long_description(self):
        """Test creating a tool with a very long description."""
        long_description = """
        This is a very long description that contains many words and should be handled properly.
        It includes multiple sentences and various punctuation marks like commas, periods, and exclamation points!
        The description should be preserved exactly as provided in the docstring, including all formatting
        and special characters. This tests the robustness of the docstring parsing functionality.
        
        Args:
            param1 (str): A simple parameter.
            
        Returns:
            str: A simple return value.
        """
        
        tool_dict = llm_execution.make_tool_from_docstring(long_description, "long_description_test")
        
        func_decl = tool_dict["tool"][0]
        self.assertEqual(func_decl["name"], "long_description_test")
        self.assertIn("very long description", func_decl["description"])
        self.assertIn("robustness", func_decl["description"])

    def test_make_tool_from_docstring_with_complex_return_types(self):
        """Test creating a tool with complex return type descriptions."""
        complex_return_docstring = """
        Performs advanced data analysis.
        
        Args:
            data (list): Input data for analysis.
            
        Returns:
            dict: Analysis results containing:
                - summary (str): Summary of findings
                - details (list): Detailed analysis results
                - metadata (dict): Additional metadata
        """
        
        tool_dict = llm_execution.make_tool_from_docstring(complex_return_docstring, "analyze_data")
        
        func_decl = tool_dict["tool"][0]
        self.assertEqual(func_decl["name"], "analyze_data")
        self.assertIn("advanced data analysis", func_decl["description"])

    def test_make_tool_from_docstring_with_raises_section(self):
        """Test creating a tool with a raises section in docstring."""
        raises_docstring = """
        Performs a risky operation.
        
        Args:
            input_data (str): Input data to process.
            
        Returns:
            str: Processed result.
            
        Raises:
            ValueError: If input_data is invalid.
            RuntimeError: If processing fails.
        """
        
        tool_dict = llm_execution.make_tool_from_docstring(raises_docstring, "risky_operation")
        
        func_decl = tool_dict["tool"][0]
        self.assertEqual(func_decl["name"], "risky_operation")
        self.assertIn("risky operation", func_decl["description"])

    def test_make_tool_from_docstring_with_examples(self):
        """Test creating a tool with examples in docstring."""
        examples_docstring = """
        Calculates the sum of numbers.
        
        Args:
            numbers (list): List of numbers to sum.
            
        Returns:
            float: Sum of all numbers.
            
        Examples:
            >>> sum_numbers([1, 2, 3])
            6.0
            >>> sum_numbers([1.5, 2.5])
            4.0
        """
        
        tool_dict = llm_execution.make_tool_from_docstring(examples_docstring, "sum_numbers")
        
        func_decl = tool_dict["tool"][0]
        self.assertEqual(func_decl["name"], "sum_numbers")
        self.assertIn("Calculates the sum", func_decl["description"])

    def test_make_tool_from_docstring_with_note_section(self):
        """Test creating a tool with a note section in docstring."""
        note_docstring = """
        Processes user data.
        
        Args:
            user_id (str): User identifier.
            
        Returns:
            dict: User data.
            
        Note:
            This function requires authentication.
        """
        
        tool_dict = llm_execution.make_tool_from_docstring(note_docstring, "get_user_data")
        
        func_decl = tool_dict["tool"][0]
        self.assertEqual(func_decl["name"], "get_user_data")
        self.assertIn("Processes user data", func_decl["description"])

    def test_make_tool_from_docstring_pydantic_validation(self):
        """Test that the generated tool passes Pydantic validation."""
        tool_dict = llm_execution.make_tool_from_docstring(self.valid_docstring, self.function_name)
        
        # The function should return a valid dictionary that can be validated
        # by the ToolContainer model
        from call_llm.SimulationEngine.models import ToolContainer
        
        # This should not raise an exception
        validated_tool = ToolContainer.model_validate(tool_dict)
        self.assertIsNotNone(validated_tool)

if __name__ == '__main__':
    unittest.main()
