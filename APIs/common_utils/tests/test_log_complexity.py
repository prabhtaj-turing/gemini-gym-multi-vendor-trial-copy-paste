#!/usr/bin/env python3
"""
Tests for log_complexity module.
"""

import unittest
import os
import sys
import logging
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import common_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common_utils.log_complexity import log_complexity


class TestLogComplexity(unittest.TestCase):
    """Test cases for log_complexity module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test logs
        self.test_dir = tempfile.mkdtemp()
        self.original_logging_config = None
        
        # Store original logging configuration
        self.original_handlers = logging.getLogger().handlers[:]
        self.original_level = logging.getLogger().level

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original logging configuration
        logging.getLogger().handlers = self.original_handlers
        logging.getLogger().setLevel(self.original_level)
        
        # Clean up test directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_log_complexity_success(self):
        """Test log_complexity decorator with successful function."""
        @log_complexity
        def test_func():
            return {"data": [1, 2, 3], "count": 3}
        
        # Capture log output
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = test_func()
            
            # Verify the result
            self.assertEqual(result, {"data": [1, 2, 3], "count": 3})
            
            # Verify logging was called
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            self.assertIn("records_fetched: 3", log_message)
            self.assertIn("characters_in_response:", log_message)

    def test_log_complexity_with_exception(self):
        """Test log_complexity decorator with exception."""
        @log_complexity
        def test_func():
            raise ValueError("Test exception")
        
        # Capture log output
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            # Verify the exception is re-raised
            with self.assertRaises(ValueError) as context:
                test_func()
            
            self.assertEqual(str(context.exception), "Test exception")
            
            # Verify logging was called with exception info
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            self.assertIn("records_fetched: 0", log_message)
            self.assertIn("characters_in_response: 0", log_message)
            self.assertIn("exception:", log_message)

    def test_log_complexity_with_simple_types(self):
        """Test log_complexity decorator with simple data types."""
        @log_complexity
        def test_func():
            return "simple string"
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = test_func()
            
            # Verify the result
            self.assertEqual(result, "simple string")
            
            # Verify logging
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            self.assertIn("records_fetched: 1", log_message)

    def test_log_complexity_with_list(self):
        """Test log_complexity decorator with list data."""
        @log_complexity
        def test_func():
            return [1, 2, 3, 4, 5]
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = test_func()
            
            # Verify the result
            self.assertEqual(result, [1, 2, 3, 4, 5])
            
            # Verify logging
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            self.assertIn("records_fetched: 5", log_message)

    def test_log_complexity_with_dict(self):
        """Test log_complexity decorator with dictionary data."""
        @log_complexity
        def test_func():
            return {"key1": [1, 2], "key2": [3, 4, 5], "key3": "string"}
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = test_func()
            
            # Verify the result
            self.assertEqual(result, {"key1": [1, 2], "key2": [3, 4, 5], "key3": "string"})
            
            # Verify logging (should count the longest list)
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            self.assertIn("records_fetched: 3", log_message)

    def test_log_complexity_with_nested_structure(self):
        """Test log_complexity decorator with nested data structure."""
        @log_complexity
        def test_func():
            return {
                "users": [
                    {"id": 1, "name": "Alice"},
                    {"id": 2, "name": "Bob"},
                    {"id": 3, "name": "Charlie"}
                ],
                "metadata": {
                    "total": 3,
                    "page": 1
                }
            }
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = test_func()
            
            # Verify the result
            self.assertEqual(len(result["users"]), 3)
            
            # Verify logging (should count the longest list)
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            self.assertIn("records_fetched: 3", log_message)

    def test_log_complexity_with_none(self):
        """Test log_complexity decorator with None return value."""
        @log_complexity
        def test_func():
            return None
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = test_func()
            
            # Verify the result
            self.assertIsNone(result)
            
            # Verify logging
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            self.assertIn("records_fetched: 0", log_message)

    def test_log_complexity_with_empty_containers(self):
        """Test log_complexity decorator with empty containers."""
        @log_complexity
        def test_func():
            return {"empty_list": [], "empty_dict": {}, "string": "test"}
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = test_func()
            
            # Verify the result
            self.assertEqual(result, {"empty_list": [], "empty_dict": {}, "string": "test"})
            
            # Verify logging (should count as 1 for non-empty dict)
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            self.assertIn("records_fetched: 1", log_message)

    def test_log_complexity_with_custom_object(self):
        """Test log_complexity decorator with custom object."""
        class CustomObject:
            def __init__(self, data):
                self.data = data
            
            def __repr__(self):
                return f"CustomObject({self.data})"
        
        @log_complexity
        def test_func():
            return CustomObject("test data")
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = test_func()
            
            # Verify the result
            self.assertIsInstance(result, CustomObject)
            self.assertEqual(result.data, "test data")
            
            # Verify logging (should count as 1 for custom object)
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            self.assertIn("records_fetched: 1", log_message)

    def test_log_complexity_with_function_arguments(self):
        """Test log_complexity decorator with function arguments."""
        @log_complexity
        def test_func(arg1, arg2, kwarg1="default"):
            return f"result: {arg1}, {arg2}, {kwarg1}"
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = test_func("arg1", "arg2", kwarg1="custom")
            
            # Verify the result
            self.assertEqual(result, "result: arg1, arg2, custom")
            
            # Verify logging
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            self.assertIn("records_fetched: 1", log_message)

    def test_log_complexity_function_metadata(self):
        """Test log_complexity decorator preserves function metadata."""
        @log_complexity
        def test_func(arg1, arg2, kwarg1="default"):
            """Test function docstring."""
            return "success"
        
        # Verify function metadata is preserved
        self.assertEqual(test_func.__name__, 'test_func')
        self.assertEqual(test_func.__doc__, 'Test function docstring.')

    def test_log_complexity_with_complex_nested_structure(self):
        """Test log_complexity decorator with complex nested structure."""
        @log_complexity
        def test_func():
            return {
                "level1": {
                    "level2": {
                        "level3": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                    },
                    "other": [1, 2]
                },
                "another": [1, 2, 3]
            }
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = test_func()
            
            # Verify the result
            self.assertEqual(len(result["level1"]["level2"]["level3"]), 10)
            
            # Verify logging (should count the longest list)
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            self.assertIn("records_fetched: 10", log_message)

    def test_log_complexity_with_mixed_data_types(self):
        """Test log_complexity decorator with mixed data types."""
        @log_complexity
        def test_func():
            return {
                "strings": ["a", "b", "c"],
                "numbers": [1, 2, 3, 4, 5],
                "booleans": [True, False],
                "mixed": [1, "string", True, None]
            }
        
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger
            
            result = test_func()
            
            # Verify the result
            self.assertEqual(len(result["numbers"]), 5)
            
            # Verify logging (should count the longest list)
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            self.assertIn("records_fetched: 5", log_message)


if __name__ == '__main__':
    unittest.main() 