import unittest
from unittest.mock import patch, MagicMock
from google.genai.types import Tool, Part
from call_llm import llm_execution
from call_llm.SimulationEngine.custom_errors import ValidationError, LLMExecutionError
from common_utils.base_case import BaseTestCaseWithErrorHandler


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
        # The function now returns a dictionary
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
        self.assertIn("This function handles various mathematical operations", func_decl["description"])


    # --- No changes are needed for the error handling tests ---

    def test_docstring_not_string(self):
        """Test that non-string docstring raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.make_tool_from_docstring,
            ValidationError,
            "docstring must be a string got type <class 'int'>.",
            None,
            123,
            "function_name"
        )

    def test_docstring_empty(self):
        """Test that empty docstring raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.make_tool_from_docstring,
            ValidationError,
            "docstring cannot be empty .",
            None,
            "",
            "function_name"
        )

    def test_docstring_whitespace_only(self):
        """Test that whitespace-only docstring raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.make_tool_from_docstring,
            ValidationError,
            "docstring cannot be empty .",
            None,
            "   \t\n   ",
            "function_name"
        )

    def test_function_name_not_string(self):
        """Test that non-string function_name raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.make_tool_from_docstring,
            ValidationError,
            "function_name must be a string got type <class 'int'>.",
            None,
            self.valid_docstring,
            123
        )

    def test_function_name_empty(self):
        """Test that empty function_name raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.make_tool_from_docstring,
            ValidationError,
            "function_name cannot be empty.",
            None,
            self.valid_docstring,
            ""
        )

    def test_function_name_whitespace_only(self):
        """Test that whitespace-only function_name raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.make_tool_from_docstring,
            ValidationError,
            "function_name cannot be empty.",
            None,
            self.valid_docstring,
            "   \t\n   "
        )
        
    def test_public_api_access(self):
        """Test accessing the function through the public API."""
        from call_llm import make_tool_from_docstring
        
        tool_dict = make_tool_from_docstring(self.valid_docstring, self.function_name)
        
        self.assertIsInstance(tool_dict, dict)
        self.assertEqual(len(tool_dict["tool"]), 1)
        self.assertEqual(tool_dict["tool"][0]["name"], "create_user")

    @patch('call_llm.llm_execution.docstring_to_fcspec')
    def test_invalid_internal_spec_raises_validation_error(self, mock_docstring_to_fcspec):
        """Test that a ValidationError is raised if the internally generated spec is invalid."""
        # Arrange: Configure the mock to return a spec that is missing the required 'description' field.
        invalid_fcspec = {
            "name": self.function_name,
            # "description" key is intentionally missing to cause a PydanticValidationError
            "parameters": {
                "type": "OBJECT",
                "properties": {}
            }
        }
        mock_docstring_to_fcspec.return_value = invalid_fcspec

        # Act & Assert: Verify that the specific ValidationError is raised.
        with self.assertRaises(ValidationError) as context:
            llm_execution.make_tool_from_docstring(self.valid_docstring, self.function_name)

        self.assertIn(
            f"The internally generated tool spec for '{self.function_name}' is invalid.",
            str(context.exception)
        )
        mock_docstring_to_fcspec.assert_called_once()



class TestGenerateLLMResponse(BaseTestCaseWithErrorHandler):
    """Test cases for the generate_llm_response function."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_api_key = "test-api-key-12345"
        self.valid_prompt = "Hello, how are you?"
        self.valid_model = "gemini-2.5-pro"

    @patch('google.genai.Client')
    def test_generate_llm_response_success(self, mock_client):
        """Test successful LLM response generation."""
        # Mock the client and response
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.text = "I'm doing well, thank you for asking!"
        mock_client_instance.models.generate_content.return_value = mock_response
        
        response = llm_execution.generate_llm_response(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key
        )
        
        self.assertEqual(response, "I'm doing well, thank you for asking!")
        mock_client_instance.models.generate_content.assert_called_once()

    @patch('google.genai.Client')
    def test_generate_llm_response_with_system_prompt(self, mock_client):
        """Test LLM response generation with system prompt."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.text = "Response with system prompt"
        mock_client_instance.models.generate_content.return_value = mock_response
        
        system_prompt = "You are a helpful assistant."
        response = llm_execution.generate_llm_response(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            system_prompt=system_prompt
        )
        
        self.assertEqual(response, "Response with system prompt")
        # Verify system prompt was passed correctly
        call_args = mock_client_instance.models.generate_content.call_args
        self.assertIn('system_instruction', call_args[1]['config'].__dict__)

    @patch('google.genai.Client')
    def test_generate_llm_response_with_custom_model(self, mock_client):
        """Test LLM response generation with custom model."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.text = "Response from custom model"
        mock_client_instance.models.generate_content.return_value = mock_response
        
        custom_model = "gemini-1.5-pro"
        response = llm_execution.generate_llm_response(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            model_name=custom_model
        )
        
        self.assertEqual(response, "Response from custom model")
        # Verify custom model was used
        call_args = mock_client_instance.models.generate_content.call_args
        self.assertEqual(call_args[1]['model'], custom_model)

    @patch('google.genai.Client')
    def test_generate_llm_response_with_file_part(self, mock_client):
        """Test LLM response generation with file Part."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.text = "Response with file"
        mock_client_instance.models.generate_content.return_value = mock_response
        
        # Create a mock Part
        mock_part = MagicMock(spec=Part)
        contents_with_file = [mock_part, "Analyze this file"]
        
        response = llm_execution.generate_llm_response(
            prompt="Analyze this file",
            api_key=self.valid_api_key,
            files=["test_file.txt"]
        )
        
        self.assertEqual(response, "Response with file")

    def test_prompt_not_string(self):
        """Test that non-string prompt raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response,
            ValidationError,
            "prompt must be a string got type <class 'list'>.",
            None,
            ["not a string"],
            self.valid_api_key
        )

    def test_prompt_empty(self):
        """Test that empty prompt raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response,
            ValidationError,
            "prompt cannot be empty.",
            None,
            "",
            self.valid_api_key
        )

    def test_files_invalid_type(self):
        """Test that files with invalid types raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response,
            ValidationError,
            "All files must be a string.",
            None,
            self.valid_prompt,
            self.valid_api_key,
            ["file1.txt", 123, "file2.txt"]
        )

    def test_api_key_not_string(self):
        """Test that non-string api_key raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response,
            ValidationError,
            "api_key must be a string got type <class 'int'>.",
            None,
            self.valid_prompt,
            123
        )

    def test_api_key_empty(self):
        """Test that empty api_key raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response,
            ValidationError,
            "api_key cannot be empty.",
            None,
            self.valid_prompt,
            ""
        )

    def test_api_key_whitespace_only(self):
        """Test that whitespace-only api_key raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response,
            ValidationError,
            "api_key cannot be empty.",
            None,
            self.valid_prompt,
            "   \t\n   "
        )

    def test_model_name_not_string(self):
        """Test that non-string model_name raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response,
            ValidationError,
            "model_name must be a string got type <class 'int'>.",
            None,
            self.valid_prompt,
            self.valid_api_key,
            None,
            None,
            123
        )

    def test_model_name_empty(self):
        """Test that empty model_name raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response,
            ValidationError,
            "model_name cannot be empty.",
            None,
            self.valid_prompt,
            self.valid_api_key,
            None,
            None,
            ""
        )

    def test_system_prompt_not_string(self):
        """Test that non-string system_prompt raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response,
            ValidationError,
            "system_prompt must be a string got type <class 'int'>.",
            None,
            self.valid_prompt,
            self.valid_api_key,
            None,
            123
        )

    @patch('google.genai.Client')
    def test_llm_execution_error(self, mock_client):
        """Test that LLM execution errors are properly handled."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.models.generate_content.side_effect = Exception("API Error")
        
        self.assert_error_behavior(
            llm_execution.generate_llm_response,
            LLMExecutionError,
            "Model execution failed: API Error",
            None,
            self.valid_prompt,
            self.valid_api_key
        )

    def test_public_api_access(self):
        """Test accessing the function through the public API."""
        from call_llm import generate_llm_response
        
        with patch('google.genai.Client') as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            
            mock_response = MagicMock()
            mock_response.text = "Public API test response"
            mock_client_instance.models.generate_content.return_value = mock_response
            
            response = generate_llm_response(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key
            )
            
            self.assertEqual(response, "Public API test response")


class TestGenerateLLMResponseWithTools(BaseTestCaseWithErrorHandler):
    """Test cases for the generate_llm_response_with_tools function."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_api_key = "test-api-key-12345"
        self.valid_prompt = "What's the weather like?"
        self.valid_model = "gemini-2.5-pro"
        
        # Create a mock tool
        self.mock_tool = MagicMock(spec=Tool)
        self.mock_function_call = MagicMock()
        self.mock_function_call.name = "get_weather"
        self.mock_function_call.args = {"location": "New York"}

    @patch('google.genai.Client')
    def test_generate_llm_response_with_tools_success(self, mock_client):
        """Test successful LLM response generation with tools."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.text = "I'll check the weather for you."
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = self.mock_function_call
        mock_client_instance.models.generate_content.return_value = mock_response
        
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            tools=[self.mock_tool]
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["function_call"], self.mock_function_call)
        self.assertEqual(result["response_text"], "I'll check the weather for you.")

    @patch('google.genai.Client')
    def test_generate_llm_response_with_tools_no_function_call(self, mock_client):
        """Test LLM response with tools but no function call."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.text = "I can help you with that."
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = None
        mock_client_instance.models.generate_content.return_value = mock_response
        
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            tools=[self.mock_tool]
        )
        
        self.assertIsInstance(result, dict)
        self.assertIsNone(result["function_call"])
        self.assertEqual(result["response_text"], "I can help you with that.")

    @patch('google.genai.Client')
    def test_generate_llm_response_with_tools_system_prompt(self, mock_client):
        """Test LLM response with tools and system prompt."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.text = "Response with system prompt"
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = None
        mock_client_instance.models.generate_content.return_value = mock_response
        
        system_prompt = "You are a helpful assistant that can use tools."
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            system_prompt=system_prompt,
            tools=[self.mock_tool]
        )
        
        self.assertEqual(result["response_text"], "Response with system prompt")

    @patch('google.genai.Client')
    def test_generate_llm_response_with_tools_custom_model(self, mock_client):
        """Test LLM response with tools and custom model."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        
        mock_response = MagicMock()
        mock_response.text = "Response from custom model"
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = None
        mock_client_instance.models.generate_content.return_value = mock_response
        
        custom_model = "gemini-1.5-pro"
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            model_name=custom_model,
            tools=[self.mock_tool]
        )
        
        self.assertEqual(result["response_text"], "Response from custom model")

    def test_prompt_not_string(self):
        """Test that non-string prompt raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response_with_tools,
            ValidationError,
            "prompt must be a string got type <class 'list'>.",
            None,
            ["not a string"],
            self.valid_api_key
        )

    def test_prompt_empty(self):
        """Test that empty prompt raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response_with_tools,
            ValidationError,
            "prompt cannot be empty.",
            None,
            "",
            self.valid_api_key
        )

    def test_files_invalid_type(self):
        """Test that files with invalid types raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response_with_tools,
            ValidationError,
            "All files must be a string.",
            None,
            self.valid_prompt,
            self.valid_api_key,
            ["file1.txt", 123, "file2.txt"]
        )

    def test_api_key_not_string(self):
        """Test that non-string api_key raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response_with_tools,
            ValidationError,
            "api_key must be a string got type <class 'int'>.",
            None,
            self.valid_prompt,
            123
        )

    def test_api_key_empty(self):
        """Test that empty api_key raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response_with_tools,
            ValidationError,
            "api_key cannot be empty.",
            None,
            self.valid_prompt,
            ""
        )

    def test_model_name_not_string(self):
        """Test that non-string model_name raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response_with_tools,
            ValidationError,
            "model_name must be a string got type <class 'int'>.",
            None,
            self.valid_prompt,
            self.valid_api_key,
            [],
            123
        )

    def test_model_name_empty(self):
        """Test that empty model_name raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response_with_tools,
            ValidationError,
            "model_name cannot be empty.",
            None,
            self.valid_prompt,
            self.valid_api_key,
            [],
            ""
        )

    def test_system_prompt_not_string(self):
        """Test that non-string system_prompt raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response_with_tools,
            ValidationError,
            "system_prompt must be a string got type <class 'int'>.",
            None,
            self.valid_prompt,
            self.valid_api_key,
            None,
            self.valid_model,
            123
        )

    def test_tools_not_list(self):
        """Test that non-list tools raises ValidationError."""
        self.assert_error_behavior(
            llm_execution.generate_llm_response_with_tools,
            ValidationError,
            "tools must be a list got type <class 'str'>.",
            None,
            self.valid_prompt,
            self.valid_api_key,
            None,
            self.valid_model,
            None,
            "not a list"
        )

    def test_tools_invalid_type(self):
        """Test that tools with invalid types raises ValidationError."""
        invalid_tools = [self.mock_tool, "not a tool", self.mock_tool]
        
        self.assert_error_behavior(
            llm_execution.generate_llm_response_with_tools,
            ValidationError,
            "All tools must be of type Tool got type <class 'list'>.",
            None,
            self.valid_prompt,
            self.valid_api_key,
            None,
            self.valid_model,
            None,
            invalid_tools
        )

    @patch('google.genai.Client')
    def test_llm_execution_error(self, mock_client):
        """Test that LLM execution errors are properly handled."""
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.models.generate_content.side_effect = Exception("API Error")
        
        self.assert_error_behavior(
            llm_execution.generate_llm_response_with_tools,
            LLMExecutionError,
            "Model execution failed: API Error",
            None,
            self.valid_prompt,
            self.valid_api_key,
            tools=[self.mock_tool]
        )

    def test_public_api_access(self):
        """Test accessing the function through the public API."""
        from call_llm import generate_llm_response_with_tools
        
        with patch('google.genai.Client') as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            
            mock_response = MagicMock()
            mock_response.text = "Public API test response"
            mock_response.candidates = [MagicMock()]
            mock_response.candidates[0].content = MagicMock()
            mock_response.candidates[0].content.parts = [MagicMock()]
            mock_response.candidates[0].content.parts[0].function_call = None
            mock_client_instance.models.generate_content.return_value = mock_response
            
            result = generate_llm_response_with_tools(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                tools=[self.mock_tool]
            )
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result["response_text"], "Public API test response")


if __name__ == '__main__':
    unittest.main() 