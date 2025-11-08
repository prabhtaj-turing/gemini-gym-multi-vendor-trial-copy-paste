"""
Test cases for LLM interface functions with 0% coverage in the Copilot API.
Targeting call_llm and _log_with_caller_info for massive coverage wins.
"""

import unittest
import copy
import os
import logging
from unittest.mock import patch, MagicMock

from copilot.SimulationEngine import custom_errors
from copilot.SimulationEngine.db import DB
from copilot.SimulationEngine import llm_interface
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestLLMInterface(BaseTestCaseWithErrorHandler):
    """Test cases for LLM interface functions with 0% coverage."""

    def setUp(self):
        """Set up test fixtures."""
        self._original_DB_state = copy.deepcopy(DB)

    def tearDown(self):
        """Clean up after each test."""
        DB.clear()
        DB.update(self._original_DB_state)

    # ========================
    # call_llm Tests (63 statements, 0% coverage - HUGE WIN!)
    # ========================

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    @patch('copilot.SimulationEngine.llm_interface.genai.Client')
    def test_call_llm_basic_success(self, mock_client_class):
        """Test call_llm with successful API response."""
        # Mock the client and response
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock the response structure to match Google GenAI
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Hello from LLM!"
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        result = llm_interface.call_llm("Test prompt")
        
        self.assertEqual(result, "Hello from LLM!")
        mock_client.models.generate_content.assert_called_once()

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    @patch('copilot.SimulationEngine.llm_interface.genai.Client')
    def test_call_llm_with_temperature(self, mock_client_class):
        """Test call_llm with custom temperature parameter."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Response with temperature"
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        result = llm_interface.call_llm("Test", temperature=0.8)
        
        self.assertEqual(result, "Response with temperature")
        # Verify that temperature was passed in config
        call_args = mock_client.models.generate_content.call_args
        self.assertIn('config', call_args.kwargs)

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    @patch('copilot.SimulationEngine.llm_interface.genai.Client')
    def test_call_llm_with_timeout(self, mock_client_class):
        """Test call_llm with custom timeout parameter."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Response with timeout"
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        result = llm_interface.call_llm("Test", timeout_seconds=60)
        
        self.assertEqual(result, "Response with timeout")

    def test_call_llm_no_api_key(self):
        """Test call_llm handles missing API key."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                llm_interface.call_llm("Test prompt")
            
            self.assertIn("API Key not available", str(context.exception))

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    @patch('copilot.SimulationEngine.llm_interface.genai.Client')
    def test_call_llm_api_error(self, mock_client_class):
        """Test call_llm handles API errors."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Simulate API error
        mock_client.models.generate_content.side_effect = Exception("API Error")
        
        with self.assertRaises(RuntimeError) as context:
            llm_interface.call_llm("Test prompt")
        
        self.assertIn("LLM call failed", str(context.exception))

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    @patch('copilot.SimulationEngine.llm_interface.genai.Client')
    def test_call_llm_timeout_error(self, mock_client_class):
        """Test call_llm handles timeout errors."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Simulate timeout error
        timeout_error = Exception("timeout")
        mock_client.models.generate_content.side_effect = timeout_error
        
        with self.assertRaises(RuntimeError) as context:
            llm_interface.call_llm("Test prompt", timeout_seconds=5)
        
        self.assertIn("timed out", str(context.exception))

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    @patch('copilot.SimulationEngine.llm_interface.genai.Client')
    def test_call_llm_no_candidates(self, mock_client_class):
        """Test call_llm handles response with no candidates."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock response with no candidates
        mock_response = MagicMock()
        mock_response.candidates = []
        
        mock_client.models.generate_content.return_value = mock_response
        
        with self.assertRaises(RuntimeError) as context:
            llm_interface.call_llm("Test prompt")
        
        self.assertIn("no usable text content", str(context.exception))

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    @patch('copilot.SimulationEngine.llm_interface.genai.Client')
    def test_call_llm_empty_content(self, mock_client_class):
        """Test call_llm handles response with empty content."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock response with candidate but no content
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.content = None
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        with self.assertRaises(RuntimeError) as context:
            llm_interface.call_llm("Test prompt")
        
        self.assertIn("no usable text content", str(context.exception))

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    @patch('copilot.SimulationEngine.llm_interface.genai.Client')
    def test_call_llm_custom_model(self, mock_client_class):
        """Test call_llm with custom model name."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Custom model response"
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        result = llm_interface.call_llm("Test", model_name="custom-model")
        
        self.assertEqual(result, "Custom model response")
        # Verify model was passed correctly
        call_args = mock_client.models.generate_content.call_args
        self.assertEqual(call_args.kwargs['model'], "custom-model")

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    @patch('copilot.SimulationEngine.llm_interface.genai.Client')
    def test_call_llm_timeout_conversion_errors(self, mock_client_class):
        """Test call_llm handles timeout conversion errors."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Response despite timeout error"
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        # Test with invalid timeout values
        result = llm_interface.call_llm("Test", timeout_seconds="invalid")
        self.assertEqual(result, "Response despite timeout error")
        
        result = llm_interface.call_llm("Test", timeout_seconds=-5)
        self.assertEqual(result, "Response despite timeout error")

    # ========================
    # _log_with_caller_info Tests (17 statements, 0% coverage)
    # ========================

    def test_log_with_caller_info_info_level(self):
        """Test _log_with_caller_info with INFO level."""
        with patch('copilot.SimulationEngine.llm_interface.logger.info') as mock_info:
            llm_interface._log_with_caller_info(logging.INFO, "Test message")
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            self.assertIn("Test message", call_args)

    def test_log_with_caller_info_error_level(self):
        """Test _log_with_caller_info with ERROR level."""
        with patch('copilot.SimulationEngine.llm_interface.logger.error') as mock_error:
            llm_interface._log_with_caller_info(logging.ERROR, "Error message")
            
            mock_error.assert_called_once()
            call_args = mock_error.call_args[0][0]
            self.assertIn("Error message", call_args)

    def test_log_with_caller_info_warning_level(self):
        """Test _log_with_caller_info with WARNING level."""
        with patch('copilot.SimulationEngine.llm_interface.logger.warning') as mock_warning:
            llm_interface._log_with_caller_info(logging.WARNING, "Warning message")
            
            mock_warning.assert_called_once()
            call_args = mock_warning.call_args[0][0]
            self.assertIn("Warning message", call_args)

    def test_log_with_caller_info_debug_level(self):
        """Test _log_with_caller_info with DEBUG level."""
        with patch('copilot.SimulationEngine.llm_interface.logger.debug') as mock_debug:
            llm_interface._log_with_caller_info(logging.DEBUG, "Debug message")
            
            mock_debug.assert_called_once()
            call_args = mock_debug.call_args[0][0]
            self.assertIn("Debug message", call_args)

    def test_log_with_caller_info_with_exc_info(self):
        """Test _log_with_caller_info with exception info."""
        with patch('copilot.SimulationEngine.llm_interface.logger.error') as mock_error:
            llm_interface._log_with_caller_info(logging.ERROR, "Error with exc", exc_info=True)
            
            mock_error.assert_called_once()
            # Check that exc_info was passed
            call_kwargs = mock_error.call_args[1]
            self.assertTrue(call_kwargs.get('exc_info', False))

    def test_log_with_caller_info_caller_details(self):
        """Test _log_with_caller_info includes caller information in message."""
        with patch('copilot.SimulationEngine.llm_interface.logger.info') as mock_info:
            llm_interface._log_with_caller_info(logging.INFO, "Test with caller")
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            # Should include function name and line number in format "function:line - message"
            self.assertIn(":", call_args)  # Function:line format
            self.assertIn(" - ", call_args)  # Separator
            self.assertIn("Test with caller", call_args)  # Original message

    def test_log_with_caller_info_frame_error(self):
        """Test _log_with_caller_info handles frame inspection errors."""
        with patch('copilot.SimulationEngine.llm_interface.inspect.currentframe') as mock_frame:
            mock_frame.side_effect = Exception("Frame error")
            
            with patch('copilot.SimulationEngine.llm_interface.logger.info') as mock_info:
                llm_interface._log_with_caller_info(logging.INFO, "Test with frame error")
                
                # Should still log the message even if frame inspection fails
                mock_info.assert_called_once()
                call_args = mock_info.call_args[0][0]
                self.assertIn("Test with frame error", call_args)

    def test_log_with_caller_info_empty_message(self):
        """Test _log_with_caller_info with empty message."""
        with patch('copilot.SimulationEngine.llm_interface.logger.info') as mock_info:
            llm_interface._log_with_caller_info(logging.INFO, "")
            
            mock_info.assert_called_once()

    # ========================
    # Additional call_llm coverage improvements (76% -> higher)
    # ========================

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    @patch('copilot.SimulationEngine.llm_interface.genai.Client')
    @patch('copilot.SimulationEngine.llm_interface.genai.types.HttpOptions')
    def test_call_llm_timeout_http_options_error(self, mock_http_options, mock_client_class):
        """Test call_llm handles HttpOptions creation errors."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock HttpOptions to raise an error
        mock_http_options.side_effect = TypeError("Invalid timeout format")
        
        # Mock successful response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Response despite timeout error"
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        result = llm_interface.call_llm("Test", timeout_seconds=30)
        
        self.assertEqual(result, "Response despite timeout error")

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    @patch('copilot.SimulationEngine.llm_interface.genai.Client')
    def test_call_llm_response_with_finish_reason(self, mock_client_class):
        """Test call_llm handles response with finish_reason feedback."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock response with finish_reason but no usable content
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_candidate.content = None
        mock_candidate.finish_reason = MagicMock()
        mock_candidate.finish_reason.name = "SAFETY"
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        with self.assertRaises(RuntimeError) as context:
            llm_interface.call_llm("Test prompt")
        
        self.assertIn("no usable text content", str(context.exception))

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    @patch('copilot.SimulationEngine.llm_interface.genai.Client')
    def test_call_llm_response_with_prompt_feedback(self, mock_client_class):
        """Test call_llm handles response with prompt_feedback."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock response with prompt_feedback but no usable content
        mock_response = MagicMock()
        mock_response.candidates = []
        mock_response.prompt_feedback = "Content blocked for safety"
        
        mock_client.models.generate_content.return_value = mock_response
        
        with self.assertRaises(RuntimeError) as context:
            llm_interface.call_llm("Test prompt")
        
        self.assertIn("no usable text content", str(context.exception))
        self.assertIn("Content blocked for safety", str(context.exception))

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    @patch('copilot.SimulationEngine.llm_interface.genai.Client')
    def test_call_llm_zero_timeout_handling(self, mock_client_class):
        """Test call_llm handles zero and negative timeout values."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Response with zero timeout"
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        # Test with zero timeout
        result1 = llm_interface.call_llm("Test", timeout_seconds=0)
        self.assertEqual(result1, "Response with zero timeout")
        
        # Test with negative timeout
        result2 = llm_interface.call_llm("Test", timeout_seconds=-5)
        self.assertEqual(result2, "Response with zero timeout")

    @patch.dict(os.environ, {'GOOGLE_API_KEY': 'test_key'})
    @patch('copilot.SimulationEngine.llm_interface.genai.Client')
    def test_call_llm_string_timeout_conversion(self, mock_client_class):
        """Test call_llm handles string timeout conversion edge cases."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        mock_part.text = "Response with string timeout"
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_client.models.generate_content.return_value = mock_response
        
        # Test with string timeout that converts to float but then to zero int
        result = llm_interface.call_llm("Test", timeout_seconds="0.5")
        self.assertEqual(result, "Response with string timeout")


if __name__ == '__main__':
    unittest.main()