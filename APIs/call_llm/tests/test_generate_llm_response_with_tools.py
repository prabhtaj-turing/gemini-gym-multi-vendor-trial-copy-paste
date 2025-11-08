import unittest
from unittest.mock import patch, MagicMock
from common_utils.base_case import BaseTestCaseWithErrorHandler
from call_llm import llm_execution
from call_llm.SimulationEngine.custom_errors import ValidationError, LLMExecutionError
from google.genai.types import Tool, Part

class TestGenerateLLMResponseWithTools(BaseTestCaseWithErrorHandler):
    """Test cases for the generate_llm_response_with_tools function."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_prompt = "What is the weather like today?"
        self.valid_api_key = "test_api_key_12345"
        self.valid_model_name = "gemini-2.5-pro"
        self.valid_system_prompt = "You are a helpful assistant with access to tools."
        
        # Create a mock Tool object
        self.mock_tool = MagicMock(spec=Tool)
        self.mock_tool.name = "get_weather"
        self.mock_tool.description = "Get current weather information"
        
        # Create a mock FunctionCall object
        self.mock_function_call = MagicMock()
        self.mock_function_call.name = "get_weather"
        self.mock_function_call.args = {"location": "New York"}

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_tools_basic(self, mock_genai):
        """Test basic LLM response generation with tools."""
        # Mock the response with function call
        mock_response = MagicMock()
        mock_response.text = ""
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = self.mock_function_call
        
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        tools = [self.mock_tool]
        
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            tools=tools
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("function_call", result)
        self.assertIn("response_text", result)
        self.assertEqual(result["function_call"], self.mock_function_call)
        self.assertEqual(result["response_text"], "")
        
        # Verify the client was called correctly
        mock_genai.Client.assert_called_once_with(api_key=self.valid_api_key)
        mock_genai.Client.return_value.models.generate_content.assert_called_once()

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_tools_text_only(self, mock_genai):
        """Test LLM response generation with tools but no function call."""
        # Mock the response with only text (no function call)
        mock_response = MagicMock()
        mock_response.text = "I can help you with that. Let me check the weather."
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = None
        
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        tools = [self.mock_tool]
        
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            tools=tools
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("function_call", result)
        self.assertIn("response_text", result)
        self.assertIsNone(result["function_call"])
        self.assertEqual(result["response_text"], "I can help you with that. Let me check the weather.")

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_tools_and_files(self, mock_genai):
        """Test LLM response generation with tools and file uploads."""
        mock_file = MagicMock()
        mock_genai.Client.return_value.files.upload.return_value = mock_file
        
        mock_response = MagicMock()
        mock_response.text = "I analyzed the file and will use tools to help."
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = self.mock_function_call
        
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        files = ["data.csv"]
        tools = [self.mock_tool]
        
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            files=files,
            tools=tools
        )
        
        self.assertEqual(result["function_call"], self.mock_function_call)
        self.assertEqual(result["response_text"], "I analyzed the file and will use tools to help.")
        
        # Verify files were uploaded
        mock_genai.Client.return_value.files.upload.assert_called_once_with("data.csv")

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_tools_and_system_prompt(self, mock_genai):
        """Test LLM response generation with tools and system prompt."""
        mock_response = MagicMock()
        mock_response.text = "Based on my instructions, I'll use the weather tool."
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = self.mock_function_call
        
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        tools = [self.mock_tool]
        
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            system_prompt=self.valid_system_prompt,
            tools=tools
        )
        
        self.assertEqual(result["function_call"], self.mock_function_call)
        self.assertEqual(result["response_text"], "Based on my instructions, I'll use the weather tool.")
        
        # Verify system prompt was passed correctly
        call_args = mock_genai.Client.return_value.models.generate_content.call_args
        self.assertEqual(call_args[1]['config'].system_instruction, self.valid_system_prompt)

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_tools_custom_model(self, mock_genai):
        """Test LLM response generation with tools and custom model."""
        mock_response = MagicMock()
        mock_response.text = "Custom model response with tools."
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = self.mock_function_call
        
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        custom_model = "gemini-1.5-pro"
        tools = [self.mock_tool]
        
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            model_name=custom_model,
            tools=tools
        )
        
        self.assertEqual(result["function_call"], self.mock_function_call)
        self.assertEqual(result["response_text"], "Custom model response with tools.")
        
        # Verify custom model was used
        call_args = mock_genai.Client.return_value.models.generate_content.call_args
        self.assertEqual(call_args[1]['model'], custom_model)

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_tools_all_parameters(self, mock_genai):
        """Test LLM response generation with tools and all parameters."""
        mock_file = MagicMock()
        mock_genai.Client.return_value.files.upload.return_value = mock_file
        
        mock_response = MagicMock()
        mock_response.text = "Complete response with all parameters and tools."
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = self.mock_function_call
        
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        files = ["document.pdf"]
        system_prompt = "You are an expert analyst with tool access."
        model_name = "gemini-2.0-pro"
        tools = [self.mock_tool]
        
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            files=files,
            model_name=model_name,
            system_prompt=system_prompt,
            tools=tools
        )
        
        self.assertEqual(result["function_call"], self.mock_function_call)
        self.assertEqual(result["response_text"], "Complete response with all parameters and tools.")
        
        # Verify all parameters were passed correctly
        call_args = mock_genai.Client.return_value.models.generate_content.call_args
        self.assertEqual(call_args[1]['model'], model_name)
        self.assertEqual(call_args[1]['config'].system_instruction, system_prompt)
        self.assertEqual(call_args[1]['config'].tools, tools)

    def test_generate_llm_response_with_tools_input_validation(self):
        """Test input validation for generate_llm_response_with_tools."""
        # Test with non-string prompt
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response_with_tools(
                prompt=123,
                api_key=self.valid_api_key,
                tools=[self.mock_tool]
            )
        
        # Test with empty prompt
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response_with_tools(
                prompt="",
                api_key=self.valid_api_key,
                tools=[self.mock_tool]
            )
        
        # Test with non-string api_key
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response_with_tools(
                prompt=self.valid_prompt,
                api_key=123,
                tools=[self.mock_tool]
            )
        
        # Test with non-string model_name
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response_with_tools(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                model_name=123,
                tools=[self.mock_tool]
            )
        
        # Test with non-list tools
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response_with_tools(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                tools="not_a_list"
            )
        
        # Test with tools containing non-Tool elements
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response_with_tools(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                tools=[self.mock_tool, "not_a_tool"]
            )
        
        # Test with non-list files
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response_with_tools(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                files="not_a_list",
                tools=[self.mock_tool]
            )
        
        # Test with files containing non-string elements
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response_with_tools(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                files=["file1.txt", 123],
                tools=[self.mock_tool]
            )
        
        # Test with non-string system_prompt
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response_with_tools(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                system_prompt=123,
                tools=[self.mock_tool]
            )

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_tools_execution_error(self, mock_genai):
        """Test handling of LLM execution errors with tools."""
        # Mock an exception during execution
        mock_genai.Client.return_value.models.generate_content.side_effect = Exception("API Error")
        
        with self.assertRaises(LLMExecutionError):
            llm_execution.generate_llm_response_with_tools(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                tools=[self.mock_tool]
            )

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_tools_file_upload_error(self, mock_genai):
        """Test handling of file upload errors with tools."""
        # Mock file upload exception
        mock_genai.Client.return_value.files.upload.side_effect = Exception("File upload failed")
        
        with self.assertRaises(LLMExecutionError):
            llm_execution.generate_llm_response_with_tools(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                files=["nonexistent_file.txt"],
                tools=[self.mock_tool]
            )

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_tools_none_files(self, mock_genai):
        """Test LLM response generation with tools and None files parameter."""
        mock_response = MagicMock()
        mock_response.text = "Response with None files and tools."
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = None
        
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            files=None,
            tools=[self.mock_tool]
        )
        
        self.assertIsNone(result["function_call"])
        self.assertEqual(result["response_text"], "Response with None files and tools.")
        
        # Verify no files were uploaded
        mock_genai.Client.return_value.files.upload.assert_not_called()

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_tools_none_system_prompt(self, mock_genai):
        """Test LLM response generation with tools and None system prompt."""
        mock_response = MagicMock()
        mock_response.text = "Response with None system prompt and tools."
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = None
        
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            system_prompt=None,
            tools=[self.mock_tool]
        )
        
        self.assertIsNone(result["function_call"])
        self.assertEqual(result["response_text"], "Response with None system prompt and tools.")
        
        # Verify system prompt was not set
        call_args = mock_genai.Client.return_value.models.generate_content.call_args
        self.assertIsNone(call_args[1]['config'].system_instruction)

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_tools_none_tools(self, mock_genai):
        """Test LLM response generation with None tools parameter."""
        mock_response = MagicMock()
        mock_response.text = "Response with None tools."
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = None
        
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            tools=None
        )
        
        self.assertIsNone(result["function_call"])
        self.assertEqual(result["response_text"], "Response with None tools.")
        
        # Verify tools were not passed
        call_args = mock_genai.Client.return_value.models.generate_content.call_args
        self.assertIsNone(call_args[1]['config'].tools)

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_tools_empty_tools_list(self, mock_genai):
        """Test LLM response generation with empty tools list."""
        mock_response = MagicMock()
        mock_response.text = "Response with empty tools list."
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = None
        
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            tools=[]
        )
        
        self.assertIsNone(result["function_call"])
        self.assertEqual(result["response_text"], "Response with empty tools list.")
        
        # Verify empty tools list was passed
        call_args = mock_genai.Client.return_value.models.generate_content.call_args
        self.assertEqual(call_args[1]['config'].tools, [])

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_tools_multiple_tools(self, mock_genai):
        """Test LLM response generation with multiple tools."""
        mock_tool2 = MagicMock(spec=Tool)
        mock_tool2.name = "get_time"
        mock_tool2.description = "Get current time"
        
        mock_response = MagicMock()
        mock_response.text = "I'll use multiple tools to help you."
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = self.mock_function_call
        
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        tools = [self.mock_tool, mock_tool2]
        
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            tools=tools
        )
        
        self.assertEqual(result["function_call"], self.mock_function_call)
        self.assertEqual(result["response_text"], "I'll use multiple tools to help you.")
        
        # Verify multiple tools were passed
        call_args = mock_genai.Client.return_value.models.generate_content.call_args
        self.assertEqual(len(call_args[1]['config'].tools), 2)

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_tools_complex_function_call(self, mock_genai):
        """Test LLM response generation with complex function call arguments."""
        complex_function_call = MagicMock()
        complex_function_call.name = "analyze_data"
        complex_function_call.args = {
            "data_source": "database",
            "filters": {"category": "sales", "date_range": "last_month"},
            "options": {"include_metadata": True, "format": "json"}
        }
        
        mock_response = MagicMock()
        mock_response.text = "I'll analyze the data with complex parameters."
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].content = MagicMock()
        mock_response.candidates[0].content.parts = [MagicMock()]
        mock_response.candidates[0].content.parts[0].function_call = complex_function_call
        
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        tools = [self.mock_tool]
        
        result = llm_execution.generate_llm_response_with_tools(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            tools=tools
        )
        
        self.assertEqual(result["function_call"], complex_function_call)
        self.assertEqual(result["function_call"].name, "analyze_data")
        self.assertEqual(result["function_call"].args["data_source"], "database")

if __name__ == '__main__':
    unittest.main()
