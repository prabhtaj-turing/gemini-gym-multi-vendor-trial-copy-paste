#!/usr/bin/env python3
"""
Comprehensive tests for call_logger module.

This module tests the call logging functionality in common_utils.call_logger module.
"""

import unittest
import os
import sys
import json
import tempfile
import shutil
import threading
import time
from unittest.mock import patch, MagicMock, mock_open

# Add the parent directory to the path so we can import common_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common_utils.call_logger import (
    log_function_call,
    set_runtime_id,
    clear_log_file,
    RUNTIME_ID,
    LOG_FILE_PATH,
    OUTPUT_DIR
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestCallLogger(BaseTestCaseWithErrorHandler):
    """Test cases for call_logger module."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        # Create a temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp()
        self.original_output_dir = OUTPUT_DIR
        
        # Store original runtime ID
        self.original_runtime_id = RUNTIME_ID
        
        # Clear the log file before each test
        clear_log_file()

    def tearDown(self):
        """Clean up test fixtures."""
        super().tearDown()
        # Restore original output directory
        with patch('common_utils.call_logger.OUTPUT_DIR', self.original_output_dir):
            pass
        
        # Restore original runtime ID
        with patch('common_utils.call_logger.RUNTIME_ID', self.original_runtime_id):
            pass
        
        # Remove temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_log_function_call_success(self):
        """Test successful function call logging."""
        # Create a test function
        @log_function_call("test_package", "test_function")
        def test_func(arg1, arg2, kwarg1="default"):
            return f"result: {arg1} {arg2} {kwarg1}"
        
        # Call the function
        result = test_func("value1", "value2", kwarg1="custom")
        
        # Verify the result
        self.assertEqual(result, "result: value1 value2 custom")
        
        # Verify log file was created (check the actual log file)
        self.assertTrue(os.path.exists(LOG_FILE_PATH))
        
        # Read and verify log content
        with open(LOG_FILE_PATH, 'r') as f:
            log_data = json.load(f)
        
        # Verify log structure (should be a list with one entry)
        self.assertIsInstance(log_data, list)
        self.assertEqual(len(log_data), 1)
        
        log_entry = log_data[0]
        self.assertIn("function_name", log_entry)
        self.assertEqual(log_entry["function_name"], "test_package.test_function")
        
        self.assertIn("param_dict", log_entry)
        self.assertEqual(log_entry["param_dict"]["arg_0"], "'value1'")
        self.assertEqual(log_entry["param_dict"]["arg_1"], "'value2'")
        self.assertEqual(log_entry["param_dict"]["kwarg1"], "'custom'")
        
        self.assertIn("response", log_entry)
        self.assertEqual(log_entry["response"]["status"], "success")
        self.assertEqual(log_entry["response"]["return_value"], "result: value1 value2 custom")

    def test_log_function_call_exception(self):
        """Test function call logging with exception."""
        # Create a test function that raises an exception
        @log_function_call("test_package", "test_function")
        def test_func(arg1):
            raise ValueError(f"Test error: {arg1}")
        
        # Call the function and expect exception
        with self.assertRaises(ValueError):
            test_func("error_value")
        
        # Verify log file was created
        self.assertTrue(os.path.exists(LOG_FILE_PATH))
        
        # Read and verify log content
        with open(LOG_FILE_PATH, 'r') as f:
            log_data = json.load(f)
        
        # Verify log structure (should be a list with one entry)
        self.assertIsInstance(log_data, list)
        self.assertEqual(len(log_data), 1)
        
        log_entry = log_data[0]
        self.assertEqual(log_entry["function_name"], "test_package.test_function")
        self.assertEqual(log_entry["param_dict"]["arg_0"], "'error_value'")
        
        self.assertEqual(log_entry["response"]["status"], "error")
        self.assertEqual(log_entry["response"]["exception_type"], "ValueError")
        self.assertEqual(log_entry["response"]["exception_message"], "Test error: error_value")

    def test_log_function_call_non_json_serializable_result(self):
        """Test logging with non-JSON serializable return value."""
        # Create a test function that returns a non-JSON serializable object
        class NonSerializable:
            def __init__(self, value):
                self.value = value
        
        @log_function_call("test_package", "test_function")
        def test_func():
            return NonSerializable("test_value")
        
        # Call the function
        result = test_func()
        
        # Verify the result
        self.assertIsInstance(result, NonSerializable)
        self.assertEqual(result.value, "test_value")
        
        # Verify log file was created
        self.assertTrue(os.path.exists(LOG_FILE_PATH))
        
        # Read and verify log content
        with open(LOG_FILE_PATH, 'r') as f:
            log_data = json.load(f)
        
        # Verify log structure (should be a list with one entry)
        self.assertIsInstance(log_data, list)
        self.assertEqual(len(log_data), 1)
        
        log_entry = log_data[0]
        # Verify response uses repr() for non-serializable objects
        self.assertEqual(log_entry["response"]["status"], "success")
        self.assertIn("NonSerializable", log_entry["response"]["return_value"])

    def test_log_function_call_multiple_calls(self):
        """Test multiple function calls to the same log file."""
        # Create a test function
        @log_function_call("test_package", "test_function")
        def test_func(value):
            return f"result: {value}"
        
        # Make multiple calls
        test_func("first")
        test_func("second")
        test_func("third")
        
        # Verify log file was created
        self.assertTrue(os.path.exists(LOG_FILE_PATH))
        
        # Read and verify log content (should contain all calls)
        with open(LOG_FILE_PATH, 'r') as f:
            log_data = json.load(f)
        
        # Verify all calls were logged (should be a list with 3 entries)
        self.assertIsInstance(log_data, list)
        self.assertEqual(len(log_data), 3)
        
        # Verify last call was logged correctly
        last_entry = log_data[2]
        self.assertEqual(last_entry["function_name"], "test_package.test_function")
        self.assertEqual(last_entry["param_dict"]["arg_0"], "'third'")
        self.assertEqual(last_entry["response"]["return_value"], "result: third")

    def test_log_function_call_thread_safety(self):
        """Test thread safety of function call logging."""
        # Create a test function
        @log_function_call("test_package", "test_function")
        def test_func(thread_id, delay=0.01):
            time.sleep(delay)  # Simulate some work
            return f"result from thread {thread_id}"
        
        # Create multiple threads
        threads = []
        results = []
        
        def thread_worker(thread_id):
            try:
                result = test_func(thread_id)
                results.append(result)
            except Exception as e:
                results.append(f"error: {e}")
        
        # Start multiple threads
        for i in range(5):
            thread = threading.Thread(target=thread_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all threads completed successfully
        self.assertEqual(len(results), 5)
        for i in range(5):
            self.assertIn(f"result from thread {i}", results)
        
        # Verify log file was created (should contain all calls)
        self.assertTrue(os.path.exists(LOG_FILE_PATH))
        
        # Read and verify log content
        with open(LOG_FILE_PATH, 'r') as f:
            log_data = json.load(f)
        
        # Verify log structure is valid (should be a list with 5 entries)
        self.assertIsInstance(log_data, list)
        self.assertEqual(len(log_data), 5)
        
        # Verify all entries have the expected structure
        for entry in log_data:
            self.assertIn("function_name", entry)
            self.assertIn("param_dict", entry)
            self.assertIn("response", entry)

    def test_set_runtime_id(self):
        """Test setting custom runtime ID."""
        # Store original values
        original_runtime_id = RUNTIME_ID
        original_log_file_path = LOG_FILE_PATH
        
        # Test setting new runtime ID
        new_runtime_id = "test_runtime_123"
        set_runtime_id(new_runtime_id)
        
        # Import the module again to get the updated values
        import common_utils.call_logger as call_logger_module
        
        # Verify runtime ID was updated
        self.assertEqual(call_logger_module.RUNTIME_ID, new_runtime_id)
        
        # Verify log file path was updated
        expected_log_file = os.path.join(OUTPUT_DIR, f"call_log_{new_runtime_id}.json")
        self.assertEqual(call_logger_module.LOG_FILE_PATH, expected_log_file)
        
        # Restore original values
        set_runtime_id(original_runtime_id)

    def test_clear_log_file_existing_file(self):
        """Test clearing an existing log file."""
        # Create a test log file at the actual LOG_FILE_PATH
        with open(LOG_FILE_PATH, 'w') as f:
            json.dump({"test": "data"}, f)
        
        # Verify file exists
        self.assertTrue(os.path.exists(LOG_FILE_PATH))
        
        # Clear the log file
        clear_log_file()
        
        # Verify file was removed
        self.assertFalse(os.path.exists(LOG_FILE_PATH))

    def test_clear_log_file_nonexistent_file(self):
        """Test clearing a nonexistent log file."""
        # Remove the log file if it exists
        if os.path.exists(LOG_FILE_PATH):
            os.remove(LOG_FILE_PATH)
        
        # Verify file doesn't exist
        self.assertFalse(os.path.exists(LOG_FILE_PATH))
        
        # Clear the log file (should not raise exception)
        try:
            clear_log_file()
        except Exception as e:
            self.fail(f"clear_log_file raised an exception: {e}")

    def test_log_function_call_no_arguments(self):
        """Test function call logging with no arguments."""
        # Create a test function with no arguments
        @log_function_call("test_package", "test_function")
        def test_func():
            return "no args result"
        
        # Call the function
        result = test_func()
        
        # Verify the result
        self.assertEqual(result, "no args result")
        
        # Verify log file was created
        self.assertTrue(os.path.exists(LOG_FILE_PATH))
        
        # Read and verify log content
        with open(LOG_FILE_PATH, 'r') as f:
            log_data = json.load(f)
        
        # Verify log structure (should be a list with one entry)
        self.assertIsInstance(log_data, list)
        self.assertEqual(len(log_data), 1)
        
        log_entry = log_data[0]
        self.assertEqual(log_entry["function_name"], "test_package.test_function")
        self.assertEqual(log_entry["param_dict"], {})
        self.assertEqual(log_entry["response"]["return_value"], "no args result")

    def test_log_function_call_complex_arguments(self):
        """Test function call logging with complex arguments."""
        # Create a test function with complex arguments
        @log_function_call("test_package", "test_function")
        def test_func(list_arg, dict_arg, tuple_arg, set_arg):
            return f"processed: {len(list_arg)} {len(dict_arg)} {len(tuple_arg)} {len(set_arg)}"
        
        # Call the function with complex arguments
        result = test_func(
            [1, 2, 3],
            {"a": 1, "b": 2},
            (1, 2, 3, 4),
            {1, 2, 3, 4, 5}
        )
        
        # Verify the result
        self.assertEqual(result, "processed: 3 2 4 5")
        
        # Verify log file was created
        self.assertTrue(os.path.exists(LOG_FILE_PATH))
        
        # Read and verify log content
        with open(LOG_FILE_PATH, 'r') as f:
            log_data = json.load(f)
        
        # Verify log structure (should be a list with one entry)
        self.assertIsInstance(log_data, list)
        self.assertEqual(len(log_data), 1)
        
        log_entry = log_data[0]
        self.assertEqual(log_entry["function_name"], "test_package.test_function")
        self.assertIn("arg_0", log_entry["param_dict"])  # list_arg
        self.assertIn("arg_1", log_entry["param_dict"])  # dict_arg
        self.assertIn("arg_2", log_entry["param_dict"])  # tuple_arg
        self.assertIn("arg_3", log_entry["param_dict"])  # set_arg

    def test_log_function_call_function_preservation(self):
        """Test that the decorator preserves function metadata."""
        # Create a test function with docstring and annotations
        @log_function_call("test_package", "test_function")
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
        
        # Call the function
        result = test_func("test", 123)
        
        # Verify the result
        self.assertEqual(result, "result: test 123")
        
        # Verify log file was created
        self.assertTrue(os.path.exists(LOG_FILE_PATH))


if __name__ == '__main__':
    unittest.main()
