#!/usr/bin/env python3
"""
Tests for base_case module.
"""

import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import common_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from common_utils.error_handling import get_package_error_mode
from pydantic import ValidationError


class TestBaseTestCaseWithErrorHandler(BaseTestCaseWithErrorHandler):
    """Test cases for BaseTestCaseWithErrorHandler class."""

    def test_assert_error_behavior_raise_mode(self):
        """Test assert_error_behavior in raise mode."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='raise'):
            def test_function():
                raise ValueError("Test error message")
            
            self.assert_error_behavior(
                test_function,
                ValueError,
                "Test error message"
            )

    def test_assert_error_behavior_error_dict_mode(self):
        """Test assert_error_behavior in error_dict mode."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='error_dict'):
            def test_function():
                return {
                    "exceptionType": "ValueError",
                    "message": "Test error message",
                    "additional_field": "test_value"
                }
            
            self.assert_error_behavior(
                test_function,
                ValueError,
                "Test error message",
                {"additional_field": "test_value"}
            )

    def test_assert_error_behavior_invalid_error_mode(self):
        """Test assert_error_behavior with invalid error mode."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='INVALID'):
            def test_function():
                pass
            
            with self.assertRaises(AssertionError):
                self.assert_error_behavior(
                    test_function,
                    ValueError,
                    "Test error message"
                )

    def test_assert_error_behavior_name_error(self):
        """Test assert_error_behavior when ERROR_MODE is not defined."""
        with patch('common_utils.base_case.get_package_error_mode', side_effect=NameError):
            def test_function():
                pass
            
            with self.assertRaises(AssertionError):
                self.assert_error_behavior(
                    test_function,
                    ValueError,
                    "Test error message"
                )

    def test_assert_error_behavior_no_exception_raises(self):
        """Test assert_error_behavior when function doesn't raise expected exception."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='raise'):
            def test_function():
                return "success"
            
            with self.assertRaises(AssertionError):
                self.assert_error_behavior(
                    test_function,
                    ValueError,
                    "Test error message"
                )

    def test_assert_error_behavior_wrong_message(self):
        """Test assert_error_behavior when wrong error message is raised."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='raise'):
            def test_function():
                raise ValueError("Wrong message")
            
            with self.assertRaises(AssertionError):
                self.assert_error_behavior(
                    test_function,
                    ValueError,
                    "Expected message"
                )

    def test_assert_error_behavior_error_dict_wrong_type(self):
        """Test assert_error_behavior in error_dict mode with wrong return type."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='error_dict'):
            def test_function():
                return "not a dict"
            
            with self.assertRaises(AssertionError):
                self.assert_error_behavior(
                    test_function,
                    ValueError,
                    "Test error message"
                )

    def test_assert_error_behavior_error_dict_missing_fields(self):
        """Test assert_error_behavior in error_dict mode with missing fields."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='error_dict'):
            def test_function():
                return {"message": "Test error message"}  # Missing exceptionType
            
            with self.assertRaises(AssertionError):
                self.assert_error_behavior(
                    test_function,
                    ValueError,
                    "Test error message"
                )

    def test_assert_error_behavior_validation_error_raise_mode(self):
        """Test assert_error_behavior with ValidationError in raise mode (line 47)."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='raise'):
            def test_function():
                # Create a simple ValidationError with the message
                raise ValidationError("Test error message", [])
            
            self.assert_error_behavior(
                test_function,
                ValidationError,
                "Test error message"
            )

    def test_assert_error_behavior_validation_error_raise_mode_wrong_message(self):
        """Test assert_error_behavior with ValidationError but wrong message in raise mode."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='raise'):
            def test_function():
                # Create a simple ValidationError with the wrong message
                raise ValidationError("Wrong message", [])
            
            with self.assertRaises(AssertionError):
                self.assert_error_behavior(
                    test_function,
                    ValidationError,
                    "Expected message"
                )

    def test_assert_error_behavior_error_dict_without_message(self):
        """Test assert_error_behavior in error_dict mode with None message (line 58)."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='error_dict'):
            def test_function():
                return {
                    "exceptionType": "ValueError",
                    "message": None
                }
            
            self.assert_error_behavior(
                test_function,
                ValueError,
                None
            )

    def test_assert_error_behavior_error_dict_with_empty_message(self):
        """Test assert_error_behavior in error_dict mode with empty message."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='error_dict'):
            def test_function():
                return {
                    "exceptionType": "ValueError",
                    "message": ""
                }
            
            self.assert_error_behavior(
                test_function,
                ValueError,
                ""
            )

    def test_assert_error_behavior_error_dict_with_additional_fields(self):
        """Test assert_error_behavior in error_dict mode with additional fields (lines 60-68)."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='error_dict'):
            def test_function():
                return {
                    "exceptionType": "ValueError",
                    "message": "Test error message",
                    "field1": "value1",
                    "field2": "value2",
                    "nested": {"key": "value"}
                }
            
            self.assert_error_behavior(
                test_function,
                ValueError,
                "Test error message",
                {
                    "field1": "value1",
                    "field2": "value2",
                    "nested": {"key": "value"}
                }
            )

    def test_assert_error_behavior_error_dict_with_wrong_additional_field(self):
        """Test assert_error_behavior in error_dict mode with wrong additional field value."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='error_dict'):
            def test_function():
                return {
                    "exceptionType": "ValueError",
                    "message": "Test error message",
                    "field1": "wrong_value"
                }
            
            with self.assertRaises(AssertionError):
                self.assert_error_behavior(
                    test_function,
                    ValueError,
                    "Test error message",
                    {"field1": "expected_value"}
                )

    def test_assert_error_behavior_error_dict_with_missing_additional_field(self):
        """Test assert_error_behavior in error_dict mode with missing additional field."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='error_dict'):
            def test_function():
                return {
                    "exceptionType": "ValueError",
                    "message": "Test error message"
                    # Missing field1
                }
            
            with self.assertRaises(AssertionError):
                self.assert_error_behavior(
                    test_function,
                    ValueError,
                    "Test error message",
                    {"field1": "expected_value"}
                )

    def test_assert_error_behavior_with_function_args(self):
        """Test assert_error_behavior with function arguments (*func_args, **func_kwargs)."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='raise'):
            def test_function(arg1, arg2, kwarg1=None, kwarg2=None):
                if arg1 == "error" and kwarg1 == "trigger":
                    raise ValueError("Test error message")
                return "success"
            
            self.assert_error_behavior(
                test_function,
                ValueError,
                "Test error message",
                None,
                "error", "arg2",  # *func_args
                kwarg1="trigger", kwarg2="test"  # **func_kwargs
            )

    def test_assert_error_behavior_error_dict_with_function_args(self):
        """Test assert_error_behavior in error_dict mode with function arguments."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='error_dict'):
            def test_function(arg1, arg2, kwarg1=None):
                if arg1 == "error" and kwarg1 == "trigger":
                    return {
                        "exceptionType": "ValueError",
                        "message": "Test error message",
                        "arg_received": arg1,
                        "kwarg_received": kwarg1
                    }
                return {"status": "success"}
            
            self.assert_error_behavior(
                test_function,
                ValueError,
                "Test error message",
                {"arg_received": "error", "kwarg_received": "trigger"},
                "error", "arg2",  # *func_args
                kwarg1="trigger"  # **func_kwargs
            )

    def test_assert_error_behavior_error_dict_wrong_exception_type(self):
        """Test assert_error_behavior in error_dict mode with wrong exception type."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='error_dict'):
            def test_function():
                return {
                    "exceptionType": "TypeError",  # Wrong type
                    "message": "Test error message"
                }
            
            with self.assertRaises(AssertionError):
                self.assert_error_behavior(
                    test_function,
                    ValueError,
                    "Test error message"
                )

    def test_assert_error_behavior_error_dict_wrong_message(self):
        """Test assert_error_behavior in error_dict mode with wrong message."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='error_dict'):
            def test_function():
                return {
                    "exceptionType": "ValueError",
                    "message": "Wrong message"
                }
            
            with self.assertRaises(AssertionError):
                self.assert_error_behavior(
                    test_function,
                    ValueError,
                    "Expected message"
                )

    def test_assert_error_behavior_error_dict_missing_message(self):
        """Test assert_error_behavior in error_dict mode with missing message field."""
        with patch('common_utils.base_case.get_package_error_mode', return_value='error_dict'):
            def test_function():
                return {
                    "exceptionType": "ValueError"
                    # Missing message field
                }
            
            with self.assertRaises(AssertionError):
                self.assert_error_behavior(
                    test_function,
                    ValueError,
                    "Expected message"
                )

    def test_assert_error_behavior_name_error_with_return(self):
        """Test assert_error_behavior when NameError occurs and return statement is executed (line 37)."""
        with patch('common_utils.base_case.get_package_error_mode', side_effect=NameError):
            def test_function():
                return "This should not be called"
            
            # This should fail with AssertionError due to self.fail() call
            with self.assertRaises(AssertionError):
                self.assert_error_behavior(
                    test_function,
                    ValueError,
                    "Test error message"
                )


if __name__ == '__main__':
    unittest.main() 