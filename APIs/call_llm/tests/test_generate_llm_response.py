import unittest
from unittest.mock import patch, MagicMock
from common_utils.base_case import BaseTestCaseWithErrorHandler
from call_llm import llm_execution
from call_llm.SimulationEngine.custom_errors import ValidationError, LLMExecutionError

class TestGenerateLLMResponse(BaseTestCaseWithErrorHandler):
    """Test cases for the generate_llm_response function."""

    def setUp(self):
        """Set up test fixtures."""
        self.valid_prompt = "What is the capital of France?"
        self.valid_api_key = "test_api_key_12345"
        self.valid_model_name = "gemini-2.5-pro"
        self.valid_system_prompt = "You are a helpful assistant."

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_basic(self, mock_genai):
        """Test basic LLM response generation."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.text = "Paris is the capital of France."
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        result = llm_execution.generate_llm_response(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key
        )
        
        self.assertEqual(result, "Paris is the capital of France.")
        
        # Verify the client was called correctly
        mock_genai.Client.assert_called_once_with(api_key=self.valid_api_key)
        mock_genai.Client.return_value.models.generate_content.assert_called_once()

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_system_prompt(self, mock_genai):
        """Test LLM response generation with system prompt."""
        mock_response = MagicMock()
        mock_response.text = "Based on my knowledge, Paris is the capital of France."
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        result = llm_execution.generate_llm_response(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            system_prompt=self.valid_system_prompt
        )
        
        self.assertEqual(result, "Based on my knowledge, Paris is the capital of France.")
        
        # Verify system prompt was passed correctly
        call_args = mock_genai.Client.return_value.models.generate_content.call_args
        self.assertIn('config', call_args[1])
        self.assertEqual(call_args[1]['config'].system_instruction, self.valid_system_prompt)

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_files(self, mock_genai):
        """Test LLM response generation with file uploads."""
        mock_file = MagicMock()
        mock_genai.Client.return_value.files.upload.return_value = mock_file
        
        mock_response = MagicMock()
        mock_response.text = "I analyzed the uploaded file and found..."
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        files = ["test_file1.txt", "test_file2.pdf"]
        
        result = llm_execution.generate_llm_response(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            files=files
        )
        
        self.assertEqual(result, "I analyzed the uploaded file and found...")
        
        # Verify files were uploaded
        self.assertEqual(mock_genai.Client.return_value.files.upload.call_count, 2)
        mock_genai.Client.return_value.files.upload.assert_any_call("test_file1.txt")
        mock_genai.Client.return_value.files.upload.assert_any_call("test_file2.pdf")

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_custom_model(self, mock_genai):
        """Test LLM response generation with custom model name."""
        mock_response = MagicMock()
        mock_response.text = "Custom model response."
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        custom_model = "gemini-1.5-pro"
        
        result = llm_execution.generate_llm_response(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            model_name=custom_model
        )
        
        self.assertEqual(result, "Custom model response.")
        
        # Verify custom model was used
        call_args = mock_genai.Client.return_value.models.generate_content.call_args
        self.assertEqual(call_args[1]['model'], custom_model)

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_with_all_parameters(self, mock_genai):
        """Test LLM response generation with all parameters."""
        mock_file = MagicMock()
        mock_genai.Client.return_value.files.upload.return_value = mock_file
        
        mock_response = MagicMock()
        mock_response.text = "Complete response with all parameters."
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        files = ["document.pdf"]
        system_prompt = "You are an expert analyst."
        model_name = "gemini-2.0-pro"
        
        result = llm_execution.generate_llm_response(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            files=files,
            system_prompt=system_prompt,
            model_name=model_name
        )
        
        self.assertEqual(result, "Complete response with all parameters.")
        
        # Verify all parameters were passed correctly
        call_args = mock_genai.Client.return_value.models.generate_content.call_args
        self.assertEqual(call_args[1]['model'], model_name)
        self.assertEqual(call_args[1]['config'].system_instruction, system_prompt)

    def test_generate_llm_response_input_validation(self):
        """Test input validation for generate_llm_response."""
        # Test with non-string prompt
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response(
                prompt=123,
                api_key=self.valid_api_key
            )
        
        # Test with empty prompt
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response(
                prompt="",
                api_key=self.valid_api_key
            )
        
        # Test with whitespace-only prompt
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response(
                prompt="   \n   ",
                api_key=self.valid_api_key
            )
        
        # Test with non-string api_key
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response(
                prompt=self.valid_prompt,
                api_key=123
            )
        
        # Test with empty api_key
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response(
                prompt=self.valid_prompt,
                api_key=""
            )
        
        # Test with non-string model_name
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                model_name=123
            )
        
        # Test with empty model_name
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                model_name=""
            )
        
        # Test with non-list files
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                files="not_a_list"
            )
        
        # Test with files containing non-string elements
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                files=["file1.txt", 123, "file2.pdf"]
            )
        
        # Test with non-string system_prompt
        with self.assertRaises(ValidationError):
            llm_execution.generate_llm_response(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                system_prompt=123
            )

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_execution_error(self, mock_genai):
        """Test handling of LLM execution errors."""
        # Mock an exception during execution
        mock_genai.Client.return_value.models.generate_content.side_effect = Exception("API Error")
        
        with self.assertRaises(LLMExecutionError):
            llm_execution.generate_llm_response(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key
            )

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_file_upload_error(self, mock_genai):
        """Test handling of file upload errors."""
        # Mock file upload exception
        mock_genai.Client.return_value.files.upload.side_effect = Exception("File upload failed")
        
        with self.assertRaises(LLMExecutionError):
            llm_execution.generate_llm_response(
                prompt=self.valid_prompt,
                api_key=self.valid_api_key,
                files=["nonexistent_file.txt"]
            )

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_empty_files_list(self, mock_genai):
        """Test LLM response generation with empty files list."""
        mock_response = MagicMock()
        mock_response.text = "Response without files."
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        result = llm_execution.generate_llm_response(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            files=[]
        )
        
        self.assertEqual(result, "Response without files.")
        
        # Verify no files were uploaded
        mock_genai.Client.return_value.files.upload.assert_not_called()

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_none_files(self, mock_genai):
        """Test LLM response generation with None files parameter."""
        mock_response = MagicMock()
        mock_response.text = "Response with None files."
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        result = llm_execution.generate_llm_response(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            files=None
        )
        
        self.assertEqual(result, "Response with None files.")
        
        # Verify no files were uploaded
        mock_genai.Client.return_value.files.upload.assert_not_called()

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_none_system_prompt(self, mock_genai):
        """Test LLM response generation with None system prompt."""
        mock_response = MagicMock()
        mock_response.text = "Response with None system prompt."
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        result = llm_execution.generate_llm_response(
            prompt=self.valid_prompt,
            api_key=self.valid_api_key,
            system_prompt=None
        )
        
        self.assertEqual(result, "Response with None system prompt.")
        
        # Verify system prompt was not set
        call_args = mock_genai.Client.return_value.models.generate_content.call_args
        self.assertIsNone(call_args[1]['config'].system_instruction)

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_long_prompt(self, mock_genai):
        """Test LLM response generation with a very long prompt."""
        long_prompt = "This is a very long prompt that contains many words and should be handled properly. " * 100
        
        mock_response = MagicMock()
        mock_response.text = "Response to long prompt."
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        result = llm_execution.generate_llm_response(
            prompt=long_prompt,
            api_key=self.valid_api_key
        )
        
        self.assertEqual(result, "Response to long prompt.")
        
        # Verify the long prompt was passed correctly
        call_args = mock_genai.Client.return_value.models.generate_content.call_args
        self.assertIn(long_prompt, call_args[1]['contents'])

    @patch('call_llm.llm_execution.genai')
    def test_generate_llm_response_special_characters(self, mock_genai):
        """Test LLM response generation with special characters in prompt."""
        special_prompt = "What is 2 + 2? Answer with symbols: @#$%^&*()"
        
        mock_response = MagicMock()
        mock_response.text = "The answer is 4."
        mock_genai.Client.return_value.models.generate_content.return_value = mock_response
        
        result = llm_execution.generate_llm_response(
            prompt=special_prompt,
            api_key=self.valid_api_key
        )
        
        self.assertEqual(result, "The answer is 4.")
        
        # Verify special characters were preserved
        call_args = mock_genai.Client.return_value.models.generate_content.call_args
        self.assertIn(special_prompt, call_args[1]['contents'])

if __name__ == '__main__':
    unittest.main()
