#!/usr/bin/env python3
"""
Comprehensive tests for log_complexity module.

This module tests the log complexity functionality in common_utils.log_complexity module.
"""

import unittest
import os
import sys
import json
import logging
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from io import StringIO

# Add the parent directory to the path so we can import common_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common_utils.log_complexity import log_complexity
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestLogComplexity(BaseTestCaseWithErrorHandler):
    """Test cases for log_complexity module."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        # Create a temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, "metrics.log")
        
        # Configure logging to use our test file
        logging.basicConfig(
            level=logging.INFO,
            filename=self.log_file,
            format="%(name)s: %(message)s",
            force=True
        )
        
        # Capture log output for verification
        self.log_capture = StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setLevel(logging.INFO)

    def tearDown(self):
        """Clean up test fixtures."""
        super().tearDown()
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Clean up logging
        self.handler.close()

    def test_log_complexity_basic_function(self):
        """Test basic log_complexity decorator with simple function."""
        # Create a test function
        @log_complexity
        def test_func():
            return "Hello, World!"
        
        # Call the function
        result = test_func()
        
        # Verify the result
        self.assertEqual(result, "Hello, World!")
        
        # Verify log was written
        self.assertTrue(os.path.exists(self.log_file))
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 1, characters_in_response: 15
        self.assertIn("records_fetched: 1", log_content)
        self.assertIn("characters_in_response: 15", log_content)

    def test_log_complexity_list_response(self):
        """Test log_complexity with list response."""
        @log_complexity
        def test_func():
            return ["item1", "item2", "item3"]
        
        # Call the function
        result = test_func()
        
        # Verify the result
        self.assertEqual(result, ["item1", "item2", "item3"])
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 3, characters_in_response: 27
        self.assertIn("records_fetched: 3", log_content)
        self.assertIn("characters_in_response: 27", log_content)

    def test_log_complexity_dict_response(self):
        """Test log_complexity with dictionary response."""
        @log_complexity
        def test_func():
            return {"key1": "value1", "key2": "value2"}
        
        # Call the function
        result = test_func()
        
        # Verify the result
        self.assertEqual(result, {"key1": "value1", "key2": "value2"})
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 1 (dict counts as 1 record)
        self.assertIn("records_fetched: 1", log_content)

    def test_log_complexity_nested_dict_with_lists(self):
        """Test log_complexity with nested dictionary containing lists."""
        @log_complexity
        def test_func():
            return {
                "users": ["user1", "user2", "user3"],
                "settings": ["setting1", "setting2"],
                "metadata": {"version": "1.0"}
            }
        
        # Call the function
        result = test_func()
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 3 (max length of lists)
        self.assertIn("records_fetched: 3", log_content)

    def test_log_complexity_empty_list(self):
        """Test log_complexity with empty list response."""
        @log_complexity
        def test_func():
            return []
        
        # Call the function
        result = test_func()
        
        # Verify the result
        self.assertEqual(result, [])
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 0
        self.assertIn("records_fetched: 0", log_content)

    def test_log_complexity_none_response(self):
        """Test log_complexity with None response."""
        @log_complexity
        def test_func():
            return None
        
        # Call the function
        result = test_func()
        
        # Verify the result
        self.assertIsNone(result)
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 0
        self.assertIn("records_fetched: 0", log_content)

    def test_log_complexity_function_with_exception(self):
        """Test log_complexity when function raises an exception."""
        @log_complexity
        def test_func():
            raise ValueError("Test error")
        
        # Call the function and expect exception
        with self.assertRaises(ValueError):
            test_func()
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 0, characters_in_response: 0 with exception
        self.assertIn("records_fetched: 0", log_content)
        self.assertIn("characters_in_response: 0", log_content)
        self.assertIn("exception: Test error", log_content)

    def test_log_complexity_function_with_arguments(self):
        """Test log_complexity with function that takes arguments."""
        @log_complexity
        def test_func(arg1, arg2, kwarg1="default"):
            return f"result: {arg1} {arg2} {kwarg1}"
        
        # Call the function
        result = test_func("value1", "value2", kwarg1="custom")
        
        # Verify the result
        self.assertEqual(result, "result: value1 value2 custom")
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 1
        self.assertIn("records_fetched: 1", log_content)

    def test_log_complexity_complex_data_structures(self):
        """Test log_complexity with complex data structures."""
        @log_complexity
        def test_func():
            return {
                "users": [
                    {"id": 1, "name": "Alice"},
                    {"id": 2, "name": "Bob"},
                    {"id": 3, "name": "Charlie"}
                ],
                "groups": [
                    {"id": 1, "members": ["Alice", "Bob"]},
                    {"id": 2, "members": ["Charlie"]}
                ]
            }
        
        # Call the function
        result = test_func()
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 3 (max length of lists)
        self.assertIn("records_fetched: 3", log_content)

    def test_log_complexity_tuple_response(self):
        """Test log_complexity with tuple response."""
        @log_complexity
        def test_func():
            return ("item1", "item2", "item3", "item4")
        
        # Call the function
        result = test_func()
        
        # Verify the result
        self.assertEqual(result, ("item1", "item2", "item3", "item4"))
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 4
        self.assertIn("records_fetched: 4", log_content)

    def test_log_complexity_set_response(self):
        """Test log_complexity with set response."""
        @log_complexity
        def test_func():
            return {"item1", "item2", "item3"}
        
        # Call the function
        result = test_func()
        
        # Verify the result
        self.assertEqual(result, {"item1", "item2", "item3"})
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 3
        self.assertIn("records_fetched: 3", log_content)

    def test_log_complexity_custom_object(self):
        """Test log_complexity with custom object response."""
        class CustomObject:
            def __init__(self, value):
                self.value = value
        
        @log_complexity
        def test_func():
            return CustomObject("test_value")
        
        # Call the function
        result = test_func()
        
        # Verify the result
        self.assertIsInstance(result, CustomObject)
        self.assertEqual(result.value, "test_value")
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 1 (custom object counts as 1)
        self.assertIn("records_fetched: 1", log_content)

    def test_log_complexity_custom_object_with_dict(self):
        """Test log_complexity with custom object that has __dict__."""
        class CustomObject:
            def __init__(self, value):
                self.value = value
                self.items = [1, 2, 3, 4, 5]
        
        @log_complexity
        def test_func():
            return CustomObject("test_value")
        
        # Call the function
        result = test_func()
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 5 (max length of items list)
        self.assertIn("records_fetched: 5", log_content)

    def test_log_complexity_non_json_serializable(self):
        """Test log_complexity with non-JSON serializable object."""
        class NonSerializable:
            def __init__(self, value):
                self.value = value
        
        @log_complexity
        def test_func():
            return NonSerializable("test_value")
        
        # Call the function
        result = test_func()
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log characters_in_response: > 0 (non-serializable objects get string representation)
        # The exact count depends on the object representation, but it should be > 0
        self.assertIn("characters_in_response:", log_content)
        # Extract the character count from the log
        import re
        match = re.search(r'characters_in_response: (\d+)', log_content)
        self.assertIsNotNone(match, "Could not find characters_in_response in log")
        char_count = int(match.group(1))
        self.assertGreater(char_count, 0, f"Expected character count > 0, got {char_count}")

    def test_log_complexity_function_preservation(self):
        """Test that the decorator preserves function metadata."""
        @log_complexity
        def test_func(arg1: str, arg2: int = 42) -> str:
            """Test function with docstring and annotations."""
            return f"result: {arg1} {arg2}"
        
        # Verify function metadata is preserved
        self.assertEqual(test_func.__name__, "test_func")
        self.assertEqual(test_func.__doc__, "Test function with docstring and annotations.")
        self.assertEqual(test_func.__annotations__, {
            'arg1': str,
            'arg2': int,
            'return': str
        })

    def test_log_complexity_multiple_calls(self):
        """Test multiple calls to decorated function."""
        call_count = 0
        
        @log_complexity
        def test_func():
            nonlocal call_count
            call_count += 1
            return f"call {call_count}"
        
        # Make multiple calls
        test_func()
        test_func()
        test_func()
        
        # Verify all calls were made
        self.assertEqual(call_count, 3)
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should have 3 log entries
        log_lines = log_content.strip().split('\n')
        self.assertEqual(len(log_lines), 3)
        
        # Each line should contain the expected format
        for line in log_lines:
            self.assertIn("records_fetched: 1", line)
            self.assertIn("characters_in_response:", line)

    def test_log_complexity_logger_name(self):
        """Test that the logger uses the function name."""
        @log_complexity
        def my_test_function():
            return "test"
        
        # Call the function
        my_test_function()
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should use function name as logger name
        self.assertIn("my_test_function:", log_content)

    def test_log_complexity_numeric_values(self):
        """Test log_complexity with numeric values."""
        @log_complexity
        def test_func():
            return 42
        
        # Call the function
        result = test_func()
        
        # Verify the result
        self.assertEqual(result, 42)
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 1, characters_in_response: 2
        self.assertIn("records_fetched: 1", log_content)
        self.assertIn("characters_in_response: 2", log_content)

    def test_log_complexity_boolean_values(self):
        """Test log_complexity with boolean values."""
        @log_complexity
        def test_func():
            return True
        
        # Call the function
        result = test_func()
        
        # Verify the result
        self.assertTrue(result)
        
        # Read and verify log content
        with open(self.log_file, 'r') as f:
            log_content = f.read()
        
        # Should log records_fetched: 1, characters_in_response: 4
        self.assertIn("records_fetched: 1", log_content)
        self.assertIn("characters_in_response: 4", log_content)


if __name__ == '__main__':
    unittest.main()
