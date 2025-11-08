#!/usr/bin/env python3
"""
Tests for error_handling module.
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import common_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common_utils.error_handling import (
    get_package_error_mode,
    get_print_error_reports,
    process_caught_exception,
    handle_api_errors,
    error_format_handler,
    set_package_error_mode,
    reset_package_error_mode,
    temporary_error_mode
)


class TestErrorHandling(unittest.TestCase):
    """Test cases for error_handling module."""

    def setUp(self):
        """Set up test fixtures."""
        # Store original environment variables
        self.original_error_mode = os.environ.get('OVERWRITE_ERROR_MODE')
        self.original_print_reports = os.environ.get('PRINT_ERROR_REPORTS')

    def tearDown(self):
        """Clean up test fixtures."""
        # Restore original environment variables
        if self.original_error_mode is not None:
            os.environ['OVERWRITE_ERROR_MODE'] = self.original_error_mode
        elif 'OVERWRITE_ERROR_MODE' in os.environ:
            del os.environ['OVERWRITE_ERROR_MODE']
            
        if self.original_print_reports is not None:
            os.environ['PRINT_ERROR_REPORTS'] = self.original_print_reports
        elif 'PRINT_ERROR_REPORTS' in os.environ:
            del os.environ['PRINT_ERROR_REPORTS']
        
        # Reset any overrides
        reset_package_error_mode()

    def test_get_package_error_mode_default(self):
        """Test get_package_error_mode with default value."""
        # Clear environment variable
        if 'OVERWRITE_ERROR_MODE' in os.environ:
            del os.environ['OVERWRITE_ERROR_MODE']
        
        mode = get_package_error_mode()
        self.assertEqual(mode, "raise")

    def test_get_package_error_mode_raise(self):
        """Test get_package_error_mode with raise mode."""
        os.environ['OVERWRITE_ERROR_MODE'] = 'raise'
        mode = get_package_error_mode()
        self.assertEqual(mode, "raise")

    def test_get_package_error_mode_error_dict(self):
        """Test get_package_error_mode with error_dict mode."""
        os.environ['OVERWRITE_ERROR_MODE'] = 'error_dict'
        mode = get_package_error_mode()
        self.assertEqual(mode, "error_dict")

    def test_get_package_error_mode_invalid(self):
        """Test get_package_error_mode with invalid mode."""
        os.environ['OVERWRITE_ERROR_MODE'] = 'INVALID_MODE'
        mode = get_package_error_mode()
        self.assertEqual(mode, "raise")  # Should return default

    def test_get_package_error_mode_case_insensitive(self):
        """Test get_package_error_mode with case insensitive input."""
        os.environ['OVERWRITE_ERROR_MODE'] = 'raise'
        mode = get_package_error_mode()
        self.assertEqual(mode, "raise")

    def test_set_package_error_mode_valid(self):
        """Test set_package_error_mode with valid modes."""
        # Test raise mode
        set_package_error_mode("raise")
        self.assertEqual(get_package_error_mode(), "raise")
        
        # Test error_dict mode
        set_package_error_mode("error_dict")
        self.assertEqual(get_package_error_mode(), "error_dict")

    def test_set_package_error_mode_invalid(self):
        """Test set_package_error_mode with invalid mode."""
        with self.assertRaises(ValueError) as context:
            set_package_error_mode("INVALID_MODE")
        self.assertIn("Invalid error mode", str(context.exception))

    def test_reset_package_error_mode(self):
        """Test reset_package_error_mode functionality."""
        # Set a global override
        set_package_error_mode("error_dict")
        self.assertEqual(get_package_error_mode(), "error_dict")
        
        # Reset to environment variable
        reset_package_error_mode()
        self.assertEqual(get_package_error_mode(), "raise")  # Default

    def test_temporary_error_mode_context_manager(self):
        """Test temporary_error_mode context manager."""
        # Set global mode
        set_package_error_mode("raise")
        
        # Use context manager to temporarily change mode
        with temporary_error_mode("error_dict"):
            self.assertEqual(get_package_error_mode(), "error_dict")
        
        # Should be back to global mode
        self.assertEqual(get_package_error_mode(), "raise")

    def test_temporary_error_mode_nested(self):
        """Test nested temporary_error_mode context managers."""
        set_package_error_mode("raise")
        
        with temporary_error_mode("error_dict"):
            self.assertEqual(get_package_error_mode(), "error_dict")
            
            with temporary_error_mode("raise"):
                self.assertEqual(get_package_error_mode(), "raise")
            
            # Back to first context
            self.assertEqual(get_package_error_mode(), "error_dict")
        
        # Back to global
        self.assertEqual(get_package_error_mode(), "raise")

    def test_temporary_error_mode_invalid(self):
        """Test temporary_error_mode with invalid mode."""
        with self.assertRaises(ValueError) as context:
            with temporary_error_mode("INVALID_MODE"):
                pass
        self.assertIn("Invalid error mode", str(context.exception))

    def test_priority_system_context_overrides_global(self):
        """Test that context override takes priority over global override."""
        set_package_error_mode("error_dict")
        
        with temporary_error_mode("raise"):
            self.assertEqual(get_package_error_mode(), "raise")
        
        self.assertEqual(get_package_error_mode(), "error_dict")

    def test_priority_system_global_overrides_environment(self):
        """Test that global override takes priority over environment variable."""
        os.environ['OVERWRITE_ERROR_MODE'] = 'error_dict'
        
        set_package_error_mode("raise")
        self.assertEqual(get_package_error_mode(), "raise")
        
        reset_package_error_mode()
        self.assertEqual(get_package_error_mode(), "error_dict")

    def test_priority_system_environment_overrides_default(self):
        """Test that environment variable takes priority over default."""
        # Clear environment
        if 'OVERWRITE_ERROR_MODE' in os.environ:
            del os.environ['OVERWRITE_ERROR_MODE']
        
        # Should return default
        self.assertEqual(get_package_error_mode(), "raise")
        
        # Set environment
        os.environ['OVERWRITE_ERROR_MODE'] = 'error_dict'
        self.assertEqual(get_package_error_mode(), "error_dict")

    def test_get_print_error_reports_default(self):
        """Test get_print_error_reports with default value."""
        # Clear environment variable
        if 'PRINT_ERROR_REPORTS' in os.environ:
            del os.environ['PRINT_ERROR_REPORTS']
        
        should_print = get_print_error_reports()
        self.assertFalse(should_print)

    def test_get_print_error_reports_true_variants(self):
        """Test get_print_error_reports with true variants."""
        true_variants = ['true', '1', 'yes', 'on']
        for variant in true_variants:
            with self.subTest(variant=variant):
                os.environ['PRINT_ERROR_REPORTS'] = variant
                should_print = get_print_error_reports()
                self.assertTrue(should_print)

    def test_get_print_error_reports_false_variants(self):
        """Test get_print_error_reports with false variants."""
        false_variants = ['false', '0', 'no', 'off']
        for variant in false_variants:
            with self.subTest(variant=variant):
                os.environ['PRINT_ERROR_REPORTS'] = variant
                should_print = get_print_error_reports()
                self.assertFalse(should_print)

    def test_get_print_error_reports_invalid(self):
        """Test get_print_error_reports with invalid value."""
        os.environ['PRINT_ERROR_REPORTS'] = 'invalid_value'
        should_print = get_print_error_reports()
        self.assertFalse(should_print)  # Should return default

    def test_handle_api_errors_decorator_success(self):
        """Test handle_api_errors decorator with successful function."""
        @handle_api_errors()
        def test_func():
            return "success"
        
        result = test_func()
        self.assertEqual(result, "success")

    def test_handle_api_errors_decorator_exception_raise_mode(self):
        """Test handle_api_errors decorator with exception in raise mode."""
        set_package_error_mode("raise")
        
        @handle_api_errors()
        def test_func():
            raise ValueError("Test error")
        
        with self.assertRaises(ValueError) as context:
            test_func()
        
        self.assertEqual(str(context.exception), "Test error")

    def test_handle_api_errors_decorator_exception_error_dict_mode(self):
        """Test handle_api_errors decorator with exception in error_dict mode."""
        set_package_error_mode("error_dict")
        
        @handle_api_errors()
        def test_func():
            raise ValueError("Test error")
        
        result = test_func()
        
        # Verify the error dictionary structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result['message'], 'Test error')
        self.assertIn('timestamp', result)

    def test_handle_api_errors_decorator_with_arguments(self):
        """Test handle_api_errors decorator with function arguments."""
        @handle_api_errors()
        def test_func(arg1, arg2, kwarg1="default"):
            return f"result: {arg1}, {arg2}, {kwarg1}"
        
        result = test_func("arg1", "arg2", kwarg1="custom")
        self.assertEqual(result, "result: arg1, arg2, custom")

    def test_handle_api_errors_decorator_exception_with_arguments(self):
        """Test handle_api_errors decorator with exception and arguments."""
        set_package_error_mode("error_dict")
        
        @handle_api_errors()
        def test_func(arg1, arg2, kwarg1="default"):
            raise ValueError(f"Error with {arg1}, {arg2}, {kwarg1}")
        
        result = test_func("arg1", "arg2", kwarg1="custom")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['message'], 'Error with arg1, arg2, custom')

    def test_handle_api_errors_decorator_nested_exception(self):
        """Test handle_api_errors decorator with nested exceptions."""
        set_package_error_mode("error_dict")
        
        @handle_api_errors()
        def test_func():
            try:
                raise ValueError("Inner error")
            except ValueError as e:
                raise RuntimeError("Outer error") from e
        
        result = test_func()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['message'], 'Outer error')

    def test_handle_api_errors_decorator_with_original_func_path(self):
        """Test handle_api_errors decorator with original_func_path parameter."""
        set_package_error_mode("error_dict")
        
        @handle_api_errors()
        def test_func():
            raise ValueError("Test error")
        
        # Mock process_caught_exception to verify it's called correctly
        with patch('common_utils.error_handling.process_caught_exception') as mock_process:
            mock_process.return_value = {"test": "error_dict"}
            
            result = test_func()
            
            # Verify process_caught_exception was called
            mock_process.assert_called_once()
            call_args = mock_process.call_args
            self.assertIsInstance(call_args[0][0], ValueError)  # caught_exception
            self.assertIsInstance(call_args[0][1], str)  # func_module_name

    def test_handle_api_errors_decorator_print_reports_enabled(self):
        """Test handle_api_errors decorator with print reports enabled."""
        set_package_error_mode("raise")
        os.environ['PRINT_ERROR_REPORTS'] = 'true'
        
        @handle_api_errors()
        def test_func():
            raise ValueError("Test error")
        
        # Should not raise an exception, but should print the error report
        with self.assertRaises(ValueError):
            test_func()

    def test_handle_api_errors_decorator_print_reports_disabled(self):
        """Test handle_api_errors decorator with print reports disabled."""
        set_package_error_mode("raise")
        os.environ['PRINT_ERROR_REPORTS'] = 'false'
        
        @handle_api_errors()
        def test_func():
            raise ValueError("Test error")
        
        # Should not raise an exception, but should not print the error report
        with self.assertRaises(ValueError):
            test_func()

    def test_handle_api_errors_decorator_with_mini_traceback_disabled(self):
        """Test handle_api_errors decorator with mini traceback disabled."""
        set_package_error_mode("error_dict")
        
        @handle_api_errors(include_mini_traceback_for_causes=False)
        def test_func():
            raise ValueError("Test error")
        
        result = test_func()
        
        self.assertIsInstance(result, dict)
        # The causes should not have miniTraceback field
        for cause in result.get('causes', []):
            self.assertNotIn('miniTraceback', cause)

    def test_handle_api_errors_decorator_function_metadata(self):
        """Test handle_api_errors decorator preserves function metadata."""
        @handle_api_errors()
        def test_func(arg1, arg2, kwarg1="default"):
            """Test function docstring."""
            return "success"
        
        # Verify function metadata is preserved
        self.assertEqual(test_func.__name__, 'test_func')
        self.assertEqual(test_func.__doc__, 'Test function docstring.')

    def test_process_caught_exception_raise_mode(self):
        """Test process_caught_exception in raise mode."""
        set_package_error_mode("raise")
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            with self.assertRaises(ValueError):
                error_format_handler(e, "test_module")

    def test_process_caught_exception_error_dict_mode(self):
        """Test process_caught_exception in error_dict mode."""
        set_package_error_mode("error_dict")
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            result = process_caught_exception(e, "test_module")
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['message'], 'Test error')

    def test_process_caught_exception_with_original_func_path(self):
        """Test process_caught_exception with original_func_path parameter."""
        set_package_error_mode("error_dict")
        
        try:
            raise ValueError("Test error")
        except ValueError as e:
            result = process_caught_exception(
                e, 
                "test_module", 
                original_func_path="custom.module.function"
            )
            
            self.assertIsInstance(result, dict)



if __name__ == '__main__':
    unittest.main() 