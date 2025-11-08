#!/usr/bin/env python3
"""
Tests for call_logger module.
"""

import unittest
import os
import sys
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open

# Add the parent directory to the path so we can import common_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from APIs.common_utils.base_case import BaseTestCaseWithErrorHandler
from common_utils.call_logger import (
    log_function_call, 
    set_runtime_id, 
    clear_log_file,
    RUNTIME_ID,
    LOG_FILE_PATH
)


class TestCallLogger(BaseTestCaseWithErrorHandler):
    """Test cases for call_logger module."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test logs
        self.test_dir = tempfile.mkdtemp()
        self.original_output_dir = None
        
        # Store original values
        self.original_runtime_id = RUNTIME_ID
        self.original_log_file_path = LOG_FILE_PATH

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original values
        import common_utils.call_logger
        common_utils.call_logger.RUNTIME_ID = self.original_runtime_id
        common_utils.call_logger.LOG_FILE_PATH = self.original_log_file_path
        
        # Clean up test directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch('common_utils.call_logger.OUTPUT_DIR')
    def test_set_runtime_id(self, mock_output_dir):
        """Test set_runtime_id function."""
        mock_output_dir.__str__ = lambda: self.test_dir
        
        # Test setting a custom runtime ID
        custom_id = "test-runtime-123"
        set_runtime_id(custom_id)
        
        import common_utils.call_logger
        self.assertEqual(common_utils.call_logger.RUNTIME_ID, custom_id)
        self.assertIn(custom_id, common_utils.call_logger.LOG_FILE_PATH)

    @patch('common_utils.call_logger.OUTPUT_DIR')
    def test_clear_log_file(self, mock_output_dir):
        """Test clear_log_file function."""
        mock_output_dir.__str__ = lambda: self.test_dir
        
        # Create a test log file
        test_log_path = os.path.join(self.test_dir, "test_log.json")
        with open(test_log_path, 'w') as f:
            json.dump([{"test": "data"}], f)
        
        # Set the log file path to our test file
        import common_utils.call_logger
        common_utils.call_logger.LOG_FILE_PATH = test_log_path
        
        # Test clearing the log file
        clear_log_file()
        
        # Verify the file was removed
        self.assertFalse(os.path.exists(test_log_path))

    @patch('common_utils.call_logger.OUTPUT_DIR')
    def test_clear_log_file_nonexistent(self, mock_output_dir):
        """Test clear_log_file with nonexistent file."""
        mock_output_dir.__str__ = lambda: self.test_dir
        
        # Set the log file path to a nonexistent file
        import common_utils.call_logger
        common_utils.call_logger.LOG_FILE_PATH = os.path.join(self.test_dir, "nonexistent.json")
        
        # Should not raise an exception
        clear_log_file()

    def test_log_function_call_success(self):
        """Test log_function_call decorator with successful function."""
        @log_function_call("test_package", "test_function")
        def test_func(arg1, arg2, kwarg1="default"):
            return {"result": "success", "args": [arg1, arg2], "kwarg": kwarg1}
        
        # Call the decorated function
        result = test_func("value1", "value2", kwarg1="custom")
        
        # Verify the result
        self.assertEqual(result["result"], "success")
        self.assertEqual(result["args"], ["value1", "value2"])
        self.assertEqual(result["kwarg"], "custom")

    def test_log_function_call_exception(self):
        """Test log_function_call decorator with exception."""
        @log_function_call("test_package", "test_function")
        def test_func():
            raise ValueError("Test exception")
        
        # Verify the exception is re-raised
        with self.assertRaises(ValueError) as context:
            test_func()
        
        self.assertEqual(str(context.exception), "Test exception")

    @patch('common_utils.call_logger._log_lock')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('os.path.exists', return_value=False)
    @patch('os.path.getsize', return_value=0)
    def test_log_function_call_file_writing(self, mock_getsize, mock_exists, mock_json_dump, mock_open, mock_lock):
        """Test that log_function_call writes to file correctly."""
        @log_function_call("test_package", "test_function")
        def test_func():
            return "success"
        
        # Call the decorated function
        result = test_func()
        
        # Verify the result
        self.assertEqual(result, "success")
        
        # Verify file operations were called
        mock_open.assert_called()
        mock_json_dump.assert_called()

    @patch('common_utils.call_logger._log_lock')
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    @patch('os.path.exists', return_value=True)
    @patch('os.path.getsize', return_value=100)
    @patch('json.load', return_value=[{"existing": "data"}])
    def test_log_function_call_append_to_existing(self, mock_json_load, mock_getsize, mock_exists, mock_json_dump, mock_open, mock_lock):
        """Test that log_function_call appends to existing file."""
        @log_function_call("test_package", "test_function")
        def test_func():
            return "success"
        
        # Call the decorated function
        result = test_func()
        
        # Verify the result
        self.assertEqual(result, "success")
        
        # Verify file operations were called
        mock_open.assert_called()
        mock_json_load.assert_called()
        mock_json_dump.assert_called()

    @patch('common_utils.call_logger._log_lock')
    @patch('builtins.open', side_effect=IOError("File error"))
    @patch('os.path.exists', return_value=True)
    @patch('os.path.getsize', return_value=100)
    def test_log_function_call_file_error(self, mock_getsize, mock_exists, mock_open, mock_lock):
        """Test log_function_call handles file errors gracefully."""
        @log_function_call("test_package", "test_function")
        def test_func():
            return "success"
        
        # Should not raise an exception, just log a warning
        result = test_func()
        self.assertEqual(result, "success")

    def test_log_function_call_json_serialization_error(self):
        """Test log_function_call with non-serializable return value."""
        class NonSerializable:
            def __repr__(self):
                return "NonSerializable()"
        
        @log_function_call("test_package", "test_function")
        def test_func():
            return NonSerializable()
        
        # Should handle non-serializable objects gracefully
        result = test_func()
        self.assertIsInstance(result, NonSerializable)

    def test_log_function_call_with_complex_arguments(self):
        """Test log_function_call with complex arguments."""
        @log_function_call("test_package", "test_function")
        def test_func(arg1, arg2, kwarg1=None, kwarg2=None):
            return {"arg1": arg1, "arg2": arg2, "kwarg1": kwarg1, "kwarg2": kwarg2}
        
        # Call with complex arguments
        complex_obj = {"nested": {"data": [1, 2, 3]}}
        result = test_func(
            "string_arg", 
            complex_obj, 
            kwarg1={"key": "value"}, 
            kwarg2=[1, 2, 3]
        )
        
        # Verify the result
        self.assertEqual(result["arg1"], "string_arg")
        self.assertEqual(result["arg2"], complex_obj)
        self.assertEqual(result["kwarg1"], {"key": "value"})
        self.assertEqual(result["kwarg2"], [1, 2, 3])

    def test_log_function_call_thread_safety(self):
        """Test that log_function_call is thread-safe."""
        import threading
        import time
        
        results = []
        errors = []
        
        @log_function_call("test_package", "test_function")
        def test_func(thread_id):
            time.sleep(0.01)  # Simulate some work
            return f"result_from_thread_{thread_id}"
        
        def worker(thread_id):
            try:
                result = test_func(thread_id)
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all threads completed successfully
        self.assertEqual(len(results), 5)
        self.assertEqual(len(errors), 0)
        
        # Verify all expected results are present
        expected_results = [f"result_from_thread_{i}" for i in range(5)]
        self.assertEqual(sorted(results), sorted(expected_results))

    @patch('common_utils.call_logger.print_log')
    def test_clear_log_file_with_exception(self, mock_print_log):
        """Test clear_log_file with exception handling (lines 42-43)."""
        with patch('common_utils.call_logger.OUTPUT_DIR') as mock_output_dir:
            mock_output_dir.__str__ = lambda: self.test_dir
            
            # Create a test log file
            test_log_path = os.path.join(self.test_dir, "test_log.json")
            with open(test_log_path, 'w') as f:
                json.dump([{"test": "data"}], f)
            
            # Set the log file path to our test file
            import common_utils.call_logger
            common_utils.call_logger.LOG_FILE_PATH = test_log_path
            
            # Mock os.remove to raise an exception
            with patch('os.remove', side_effect=OSError("Permission denied")):
                clear_log_file()
                
                # Verify warning was logged
                mock_print_log.assert_called()
                warning_calls = [call[0][0] for call in mock_print_log.call_args_list]
                warning_messages = [msg for msg in warning_calls if "Failed to clear log file" in str(msg)]
                self.assertEqual(len(warning_messages), 1)

    @patch('common_utils.call_logger.print_log')
    def test_log_function_call_clear_file_exception(self, mock_print_log):
        """Test log_function_call with exception when clearing file (lines 103-108)."""
        with patch('common_utils.call_logger.OUTPUT_DIR') as mock_output_dir:
            mock_output_dir.__str__ = lambda: self.test_dir
            
            # Create a test log file
            test_log_path = os.path.join(self.test_dir, "test_log.json")
            with open(test_log_path, 'w') as f:
                json.dump([{"test": "data"}], f)
            
            # Set the log file path to our test file
            import common_utils.call_logger
            common_utils.call_logger.LOG_FILE_PATH = test_log_path
            common_utils.call_logger._log_file_initialized = False
            
            # Mock os.remove to raise an exception
            with patch('os.remove', side_effect=IOError("File in use")):
                @log_function_call("test_package", "test_function")
                def test_func():
                    return "success"
                
                # Should not raise an exception, just log a warning
                result = test_func()
                self.assertEqual(result, "success")
                
                # Verify warning was logged
                mock_print_log.assert_called()
                warning_calls = [call[0][0] for call in mock_print_log.call_args_list]
                warning_messages = [msg for msg in warning_calls if "Failed to clear log file" in str(msg)]
                self.assertEqual(len(warning_messages), 1)

    @patch('common_utils.call_logger.print_log')
    def test_log_function_call_malformed_json(self, mock_print_log):
        """Test log_function_call with malformed JSON file (lines 120-123)."""
        with patch('common_utils.call_logger.OUTPUT_DIR') as mock_output_dir:
            mock_output_dir.__str__ = lambda: self.test_dir
            
            # Create a test log file with malformed JSON
            test_log_path = os.path.join(self.test_dir, "test_log.json")
            with open(test_log_path, 'w') as f:
                f.write('{"invalid": json content')  # Malformed JSON
            
            # Set the log file path to our test file
            import common_utils.call_logger
            common_utils.call_logger.LOG_FILE_PATH = test_log_path
            common_utils.call_logger._log_file_initialized = True
            
            @log_function_call("test_package", "test_function")
            def test_func():
                return "success"
            
            # Should handle malformed JSON gracefully
            result = test_func()
            self.assertEqual(result, "success")

    @patch('common_utils.call_logger.print_log')
    def test_log_function_call_json_not_list(self, mock_print_log):
        """Test log_function_call with JSON that is not a list (line 120)."""
        with patch('common_utils.call_logger.OUTPUT_DIR') as mock_output_dir:
            mock_output_dir.__str__ = lambda: self.test_dir
            
            # Create a test log file with JSON that is not a list
            test_log_path = os.path.join(self.test_dir, "test_log.json")
            with open(test_log_path, 'w') as f:
                json.dump({"not_a_list": "data"}, f)
            
            # Set the log file path to our test file
            import common_utils.call_logger
            common_utils.call_logger.LOG_FILE_PATH = test_log_path
            common_utils.call_logger._log_file_initialized = True
            
            @log_function_call("test_package", "test_function")
            def test_func():
                return "success"
            
            # Should handle non-list JSON gracefully
            result = test_func()
            self.assertEqual(result, "success")

    @patch('common_utils.call_logger.print_log')
    def test_log_function_call_file_system_errors(self, mock_print_log):
        """Test log_function_call with file system errors (lines 120-123)."""
        with patch('common_utils.call_logger.OUTPUT_DIR') as mock_output_dir:
            mock_output_dir.__str__ = lambda: self.test_dir
            
            # Set the log file path to our test file
            import common_utils.call_logger
            common_utils.call_logger.LOG_FILE_PATH = os.path.join(self.test_dir, "test_log.json")
            common_utils.call_logger._log_file_initialized = True
            
            # Mock os.path.exists to raise an exception
            with patch('os.path.exists', side_effect=OSError("File system error")):
                @log_function_call("test_package", "test_function")
                def test_func():
                    return "success"
                
                # Should handle file system errors gracefully
                result = test_func()
                self.assertEqual(result, "success")

    @patch('common_utils.call_logger.print_log')
    def test_log_function_call_write_error(self, mock_print_log):
        """Test log_function_call with write error (lines 120-123)."""
        with patch('common_utils.call_logger.OUTPUT_DIR') as mock_output_dir:
            mock_output_dir.__str__ = lambda: self.test_dir
            
            # Set the log file path to our test file
            import common_utils.call_logger
            common_utils.call_logger.LOG_FILE_PATH = os.path.join(self.test_dir, "test_log.json")
            common_utils.call_logger._log_file_initialized = True
            
            # Mock open to raise an exception when writing
            with patch('builtins.open', side_effect=IOError("Disk full")):
                @log_function_call("test_package", "test_function")
                def test_func():
                    return "success"
                
                # Should handle write errors gracefully
                result = test_func()
                self.assertEqual(result, "success")
                
                # Verify warning was logged
                mock_print_log.assert_called()
                warning_calls = [call[0][0] for call in mock_print_log.call_args_list]
                warning_messages = [msg for msg in warning_calls if "Failed to write to call log file" in str(msg)]
                self.assertEqual(len(warning_messages), 1)

    def test_log_function_call_empty_file(self):
        """Test log_function_call with empty file (line 120)."""
        with patch('common_utils.call_logger.OUTPUT_DIR') as mock_output_dir:
            mock_output_dir.__str__ = lambda: self.test_dir
            
            # Create an empty test log file
            test_log_path = os.path.join(self.test_dir, "test_log.json")
            with open(test_log_path, 'w') as f:
                pass  # Create empty file
            
            # Set the log file path to our test file
            import common_utils.call_logger
            common_utils.call_logger.LOG_FILE_PATH = test_log_path
            common_utils.call_logger._log_file_initialized = True
            
            @log_function_call("test_package", "test_function")
            def test_func():
                return "success"
            
            # Should handle empty file gracefully
            result = test_func()
            self.assertEqual(result, "success")

    def test_log_function_call_file_size_zero(self):
        """Test log_function_call with file size zero (line 120)."""
        with patch('common_utils.call_logger.OUTPUT_DIR') as mock_output_dir:
            mock_output_dir.__str__ = lambda: self.test_dir
            
            # Create a test log file
            test_log_path = os.path.join(self.test_dir, "test_log.json")
            with open(test_log_path, 'w') as f:
                pass  # Create empty file
            
            # Set the log file path to our test file
            import common_utils.call_logger
            common_utils.call_logger.LOG_FILE_PATH = test_log_path
            common_utils.call_logger._log_file_initialized = True
            
            @log_function_call("test_package", "test_function")
            def test_func():
                return "success"
            
            # Should handle zero-size file gracefully
            result = test_func()
            self.assertEqual(result, "success")

    def test_log_function_call_json_decode_error(self):
        """Test log_function_call with JSON decode error (lines 120-123)."""
        with patch('common_utils.call_logger.OUTPUT_DIR') as mock_output_dir:
            mock_output_dir.__str__ = lambda: self.test_dir
            
            # Create a test log file with invalid JSON
            test_log_path = os.path.join(self.test_dir, "test_log.json")
            with open(test_log_path, 'w') as f:
                f.write('invalid json content')
            
            # Set the log file path to our test file
            import common_utils.call_logger
            common_utils.call_logger.LOG_FILE_PATH = test_log_path
            common_utils.call_logger._log_file_initialized = True
            
            @log_function_call("test_package", "test_function")
            def test_func():
                return "success"
            
            # Should handle JSON decode errors gracefully
            result = test_func()
            self.assertEqual(result, "success")

    def test_log_function_call_value_error(self):
        """Test log_function_call with ValueError during JSON loading (lines 120-123)."""
        with patch('common_utils.call_logger.OUTPUT_DIR') as mock_output_dir:
            mock_output_dir.__str__ = lambda: self.test_dir
            
            # Create a test log file
            test_log_path = os.path.join(self.test_dir, "test_log.json")
            with open(test_log_path, 'w') as f:
                json.dump([{"test": "data"}], f)
            
            # Set the log file path to our test file
            import common_utils.call_logger
            common_utils.call_logger.LOG_FILE_PATH = test_log_path
            common_utils.call_logger._log_file_initialized = True
            
            # Mock json.load to raise ValueError
            with patch('json.load', side_effect=ValueError("Invalid value")):
                @log_function_call("test_package", "test_function")
                def test_func():
                    return "success"
                
                # Should handle ValueError gracefully
                result = test_func()
                self.assertEqual(result, "success")


if __name__ == '__main__':
    unittest.main() 