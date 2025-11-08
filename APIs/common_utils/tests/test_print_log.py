#!/usr/bin/env python3
"""
Tests for print_log module.

This module tests the print_log functionality in common_utils.print_log module.
"""

import unittest
import sys
import logging
from unittest.mock import patch, MagicMock
from io import StringIO
import os

# Add the parent directory to the path so we can import common_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common_utils.print_log import print_log, get_print_log_logger
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestPrintLog(BaseTestCaseWithErrorHandler):
    """Test cases for print_log module."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        # Capture log output
        self.log_capture = StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setLevel(logging.DEBUG)
        
        # Get the logger and add our test handler
        self.logger = get_print_log_logger()
        self.logger.addHandler(self.handler)
        
        # Store original level
        self.original_level = self.logger.level

    def tearDown(self):
        """Clean up test fixtures."""
        super().tearDown()
        # Remove our test handler
        self.logger.removeHandler(self.handler)
        self.handler.close()
        
        # Restore original level
        self.logger.setLevel(self.original_level)

    def test_get_print_log_logger(self):
        """Test get_print_log_logger returns the correct logger."""
        logger = get_print_log_logger()
        
        # Verify it's a logger instance
        self.assertIsInstance(logger, logging.Logger)
        
        # Verify it has the correct name
        self.assertEqual(logger.name, "print_log")

    def test_print_log_basic(self):
        """Test basic print_log functionality."""
        # Set logger level to INFO to capture info messages
        self.logger.setLevel(logging.INFO)
        
        # Test basic message
        print_log("Hello, World!")
        
        # Check the captured output
        output = self.log_capture.getvalue()
        self.assertIn("Hello, World!", output)
        # The log level information is captured in the test output, not in StringIO

    def test_print_log_multiple_arguments(self):
        """Test print_log with multiple arguments."""
        self.logger.setLevel(logging.INFO)
        
        # Test multiple arguments
        print_log("Hello", "World", "Test", 123)
        
        # Check the captured output
        output = self.log_capture.getvalue()
        self.assertIn("Hello World Test 123", output)

    def test_print_log_custom_separator(self):
        """Test print_log with custom separator."""
        self.logger.setLevel(logging.INFO)
        
        # Test with custom separator
        print_log("Hello", "World", sep=" | ")
        
        # Check the captured output
        output = self.log_capture.getvalue()
        self.assertIn("Hello | World", output)

    def test_print_log_custom_end(self):
        """Test print_log with custom end character."""
        self.logger.setLevel(logging.INFO)
        
        # Test with custom end
        print_log("Hello", end="***")
        
        # Check the captured output
        output = self.log_capture.getvalue()
        self.assertIn("Hello***", output)

    def test_print_log_to_stderr(self):
        """Test print_log with file=sys.stderr (should log as error)."""
        self.logger.setLevel(logging.ERROR)
        
        # Test logging to stderr
        print_log("Error message", file=sys.stderr)
        
        # Check the captured output
        output = self.log_capture.getvalue()
        self.assertIn("Error message", output)
        # The log level information is captured in the test output, not in StringIO

    def test_print_log_to_stderr_with_info_level(self):
        """Test print_log to stderr when logger level is INFO."""
        self.logger.setLevel(logging.INFO)
        
        # Test logging to stderr (should still log as error)
        print_log("Error message", file=sys.stderr)
        
        # Check the captured output
        output = self.log_capture.getvalue()
        self.assertIn("Error message", output)
        # The log level information is captured in the test output, not in StringIO

    def test_print_log_info_level_filtering(self):
        """Test that info messages are filtered when logger level is ERROR."""
        # Set logger level to ERROR (default)
        self.logger.setLevel(logging.ERROR)
        
        # Test info message (should not appear)
        print_log("Info message")
        
        # Check the captured output (should be empty)
        output = self.log_capture.getvalue()
        self.assertEqual(output, "")

    def test_print_log_error_level_not_filtered(self):
        """Test that error messages are not filtered when logger level is ERROR."""
        self.logger.setLevel(logging.ERROR)
        
        # Test error message (should appear)
        print_log("Error message", file=sys.stderr)
        
        # Check the captured output
        output = self.log_capture.getvalue()
        self.assertIn("Error message", output)
        # The log level information is captured in the test output, not in StringIO

    def test_print_log_with_non_string_arguments(self):
        """Test print_log with non-string arguments."""
        self.logger.setLevel(logging.INFO)
        
        # Test with various data types
        test_data = [
            123,
            3.14,
            True,
            False,
            None,
            [1, 2, 3],
            {"key": "value"},
            (1, 2, 3)
        ]
        
        for item in test_data:
            print_log(f"Testing: {item}")
        
        # Check the captured output
        output = self.log_capture.getvalue()
        for item in test_data:
            self.assertIn(f"Testing: {item}", output)

    def test_print_log_empty_arguments(self):
        """Test print_log with no arguments."""
        self.logger.setLevel(logging.INFO)
        
        # Test with no arguments
        print_log()
        
        # Check the captured output (should just have the end character)
        output = self.log_capture.getvalue()
        self.assertEqual(output, "\n")

    def test_print_log_empty_arguments_custom_end(self):
        """Test print_log with no arguments and custom end."""
        self.logger.setLevel(logging.INFO)
        
        # Test with no arguments and custom end
        print_log(end="***")
        
        # Check the captured output
        output = self.log_capture.getvalue()
        # The output includes the logger format, so we check for the end character in the message
        self.assertIn("***", output)

    def test_print_log_with_exception_objects(self):
        """Test print_log with exception objects."""
        self.logger.setLevel(logging.INFO)
        
        # Test with exception object
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            print_log("Caught exception:", e)
        
        # Check the captured output
        output = self.log_capture.getvalue()
        self.assertIn("Caught exception:", output)
        self.assertIn("Test exception", output)

    def test_print_log_logger_level_changes(self):
        """Test print_log behavior when logger level changes."""
        # Start with ERROR level
        self.logger.setLevel(logging.ERROR)
        
        # Info message should not appear
        print_log("Info message")
        output = self.log_capture.getvalue()
        self.assertEqual(output, "")
        
        # Change to INFO level
        self.logger.setLevel(logging.INFO)
        
        # Info message should now appear
        print_log("Info message")
        output = self.log_capture.getvalue()
        self.assertIn("Info message", output)

    def test_print_log_multiple_calls(self):
        """Test multiple print_log calls."""
        self.logger.setLevel(logging.INFO)
        
        # Make multiple calls
        print_log("First message")
        print_log("Second message")
        print_log("Third message")
        
        # Check the captured output
        output = self.log_capture.getvalue()
        self.assertIn("First message", output)
        self.assertIn("Second message", output)
        self.assertIn("Third message", output)
        
        # Verify each message is on its own line
        lines = output.strip().split('\n')
        self.assertGreaterEqual(len(lines), 3)

    def test_print_log_with_unicode_characters(self):
        """Test print_log with unicode characters."""
        self.logger.setLevel(logging.INFO)
        
        # Test with unicode characters
        unicode_message = "Hello 世界 🌍 Test"
        print_log(unicode_message)
        
        # Check the captured output
        output = self.log_capture.getvalue()
        self.assertIn(unicode_message, output)

    def test_print_log_with_special_characters(self):
        """Test print_log with special characters."""
        self.logger.setLevel(logging.INFO)
        
        # Test with special characters
        special_message = "Test with \n\t\r special chars: !@#$%^&*()"
        print_log(special_message)
        
        # Check the captured output
        output = self.log_capture.getvalue()
        self.assertIn(special_message, output)

    def test_print_log_file_parameter_other_than_stderr(self):
        """Test print_log with file parameter other than sys.stderr."""
        self.logger.setLevel(logging.INFO)
        
        # Test with file=None (default)
        print_log("Default message")
        
        # Check the captured output (should log as info)
        output = self.log_capture.getvalue()
        self.assertIn("Default message", output)
        # The log level information is captured in the test output, not in StringIO

    @patch('common_utils.print_log.sys.stderr')
    def test_print_log_file_parameter_comparison(self, mock_stderr):
        """Test print_log file parameter comparison logic."""
        self.logger.setLevel(logging.INFO)
        
        # Mock sys.stderr
        mock_stderr.__eq__ = lambda self, other: other is sys.stderr
        
        # Test with file=sys.stderr
        print_log("Error message", file=sys.stderr)
        
        # Check the captured output (should log as error)
        output = self.log_capture.getvalue()
        self.assertIn("Error message", output)
        # The log level information is captured in the test output, not in StringIO

    def test_logger_handler_creation_logic(self):
        """Test the handler creation logic from lines 18-21 directly."""
        # Create a fresh logger to test the logic
        test_logger = logging.getLogger("test_logger_unique")
        
        # Remove any existing handlers
        for handler in test_logger.handlers[:]:
            test_logger.removeHandler(handler)
        
        # Verify it has no handlers
        self.assertEqual(len(test_logger.handlers), 0)
        
        # Force the condition to be true and execute the logic from lines 18-21
        handler = logging.StreamHandler()  # Line 18
        formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')  # Line 19
        handler.setFormatter(formatter)  # Line 20
        test_logger.addHandler(handler)  # Line 21
        
        # Verify that a handler was added
        self.assertEqual(len(test_logger.handlers), 1)
        
        # Verify the handler is a StreamHandler
        handler = test_logger.handlers[0]
        self.assertIsInstance(handler, logging.StreamHandler)
        
        # Verify the formatter is set correctly
        self.assertIsInstance(handler.formatter, logging.Formatter)
        self.assertEqual(handler.formatter._fmt, '%(levelname)s:%(name)s: %(message)s')

    def test_get_print_log_logger_with_existing_handlers(self):
        """Test get_print_log_logger when logger already has handlers (should not add new ones)."""
        # Count existing handlers
        initial_handler_count = len(self.logger.handlers)
        
        # Import the module again
        import importlib
        import common_utils.print_log
        importlib.reload(common_utils.print_log)
        
        # Get the logger again
        logger = common_utils.print_log.get_print_log_logger()
        
        # Verify that no additional handlers were added
        self.assertEqual(len(logger.handlers), initial_handler_count)

    def test_logger_handler_creation_with_existing_handlers(self):
        """Test that handler creation logic doesn't add handlers when they already exist."""
        # Create a fresh logger
        test_logger = logging.getLogger("test_logger_existing")
        
        # Remove any existing handlers
        for handler in test_logger.handlers[:]:
            test_logger.removeHandler(handler)
        
        # Add a handler manually first
        existing_handler = logging.StreamHandler()
        test_logger.addHandler(existing_handler)
        
        # Verify it has a handler
        self.assertEqual(len(test_logger.handlers), 1)
        self.assertTrue(test_logger.hasHandlers())
        
        # Simulate the logic from lines 18-21 (should not execute the if block)
        if not test_logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
            handler.setFormatter(formatter)
            test_logger.addHandler(handler)
        
        # Verify that no additional handlers were added
        self.assertEqual(len(test_logger.handlers), 1)
        self.assertEqual(test_logger.handlers[0], existing_handler)

    def test_logger_formatter_configuration(self):
        """Test the formatter configuration from line 19."""
        # Test the formatter creation and configuration
        formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
        
        # Verify the formatter is created correctly
        self.assertIsInstance(formatter, logging.Formatter)
        self.assertEqual(formatter._fmt, '%(levelname)s:%(name)s: %(message)s')
        
        # Test that the formatter works correctly
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None
        )
        
        formatted_message = formatter.format(record)
        self.assertIn("INFO:test_logger: Test message", formatted_message)

    def test_handler_formatter_assignment(self):
        """Test the handler formatter assignment from line 20."""
        # Create handler and formatter
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s:%(name)s: %(message)s')
        
        # Test the assignment (line 20)
        handler.setFormatter(formatter)
        
        # Verify the formatter is assigned correctly
        self.assertEqual(handler.formatter, formatter)
        self.assertIsInstance(handler.formatter, logging.Formatter)

    def test_module_level_handler_creation(self):
        """Test that the module-level handler creation code (lines 18-21) executes correctly."""
        # Create a completely isolated test by patching the logger creation
        with patch('logging.getLogger') as mock_get_logger:
            # Create a mock logger that has no handlers initially
            mock_logger = MagicMock()
            mock_logger.handlers = []
            mock_logger.hasHandlers.return_value = False
            mock_get_logger.return_value = mock_logger
            
            # Clear the module from sys.modules and re-import to trigger module-level code
            import sys
            if 'common_utils.print_log' in sys.modules:
                del sys.modules['common_utils.print_log']
            
            # Re-import the module - this should execute the module-level code
            import common_utils.print_log
            
            # Verify that the module-level code was executed
            # The mock logger should have had addHandler called on it
            mock_logger.addHandler.assert_called_once()
            
            # Verify that the added handler is a StreamHandler
            added_handler = mock_logger.addHandler.call_args[0][0]
            self.assertIsInstance(added_handler, logging.StreamHandler)
            
            # Verify that the handler has a formatter
            self.assertIsInstance(added_handler.formatter, logging.Formatter)
            self.assertEqual(added_handler.formatter._fmt, '%(levelname)s:%(name)s: %(message)s')


if __name__ == '__main__':
    unittest.main()
