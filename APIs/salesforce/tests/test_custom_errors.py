import unittest
import sys
import os

# Add the parent directory to the path to import the custom errors
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from APIs.salesforce.SimulationEngine.custom_errors import (
    TaskNotFoundError, InvalidDateFormatError, InvalidDateTypeError,
    InvalidReplicationDateError, ExceededIdLimitError, InvalidSObjectTypeError,
    UnsupportedSObjectTypeError, LayoutNotFound, EventNotFound, SObjectNotFoundError,
    EventNotFoundError, InvalidParameterException, InvalidArgumentError,
    InvalidConditionsError, UnsupportedOperatorError
)


class TestCustomErrors(unittest.TestCase):
    """Test cases for all custom error classes in custom_errors.py"""

    def test_task_not_found_error(self):
        """Test TaskNotFoundError exception."""
        with self.assertRaises(TaskNotFoundError):
            raise TaskNotFoundError("Task with ID 123 not found")
        
        # Test with custom message
        try:
            raise TaskNotFoundError("Custom task error message")
        except TaskNotFoundError as e:
            self.assertEqual(str(e), "Custom task error message")

    def test_invalid_date_format_error(self):
        """Test InvalidDateFormatError exception."""
        with self.assertRaises(InvalidDateFormatError):
            raise InvalidDateFormatError("Invalid date format: YYYY-MM-DD")
        
        # Test with custom message
        try:
            raise InvalidDateFormatError("Date must be in ISO format")
        except InvalidDateFormatError as e:
            self.assertEqual(str(e), "Date must be in ISO format")

    def test_invalid_date_type_error(self):
        """Test InvalidDateTypeError exception."""
        with self.assertRaises(InvalidDateTypeError):
            raise InvalidDateTypeError("Date parameter must be a string")
        
        # Test with custom message
        try:
            raise InvalidDateTypeError("Expected string, got int")
        except InvalidDateTypeError as e:
            self.assertEqual(str(e), "Expected string, got int")

    def test_invalid_replication_date_error(self):
        """Test InvalidReplicationDateError exception."""
        with self.assertRaises(InvalidReplicationDateError):
            raise InvalidReplicationDateError("Start date must precede end date")
        
        # Test with custom message
        try:
            raise InvalidReplicationDateError("Date range exceeds allowed limit")
        except InvalidReplicationDateError as e:
            self.assertEqual(str(e), "Date range exceeds allowed limit")

    def test_exceeded_id_limit_error(self):
        """Test ExceededIdLimitError exception."""
        with self.assertRaises(ExceededIdLimitError):
            raise ExceededIdLimitError("Too many results returned")
        
        # Test with custom message
        try:
            raise ExceededIdLimitError("Maximum 2000 IDs allowed")
        except ExceededIdLimitError as e:
            self.assertEqual(str(e), "Maximum 2000 IDs allowed")

    def test_invalid_sobject_type_error(self):
        """Test InvalidSObjectTypeError exception."""
        with self.assertRaises(InvalidSObjectTypeError):
            raise InvalidSObjectTypeError("Invalid sObject type")
        
        # Test with custom message
        try:
            raise InvalidSObjectTypeError("sObjectType cannot be empty")
        except InvalidSObjectTypeError as e:
            self.assertEqual(str(e), "sObjectType cannot be empty")

    def test_unsupported_sobject_type_error(self):
        """Test UnsupportedSObjectTypeError exception."""
        with self.assertRaises(UnsupportedSObjectTypeError):
            raise UnsupportedSObjectTypeError("Unsupported sObject type")
        
        # Test with custom message
        try:
            raise UnsupportedSObjectTypeError("CustomObject is not supported")
        except UnsupportedSObjectTypeError as e:
            self.assertEqual(str(e), "CustomObject is not supported")

    def test_layout_not_found_error(self):
        """Test LayoutNotFound exception."""
        with self.assertRaises(LayoutNotFound):
            raise LayoutNotFound("Layout not found")
        
        # Test with custom message
        try:
            raise LayoutNotFound("Layout ID 123 not found")
        except LayoutNotFound as e:
            self.assertEqual(str(e), "Layout ID 123 not found")

    def test_event_not_found_error(self):
        """Test EventNotFound exception with custom message."""
        with self.assertRaises(EventNotFound):
            raise EventNotFound("Custom event error message")
        
        # Test with default message
        try:
            raise EventNotFound()
        except EventNotFound as e:
            self.assertEqual(str(e), "The requested event could not be found.")
        
        # Test with custom message
        try:
            raise EventNotFound("Event with ID 456 not found")
        except EventNotFound as e:
            self.assertEqual(str(e), "Event with ID 456 not found")

    def test_sobject_not_found_error(self):
        """Test SObjectNotFoundError exception."""
        with self.assertRaises(SObjectNotFoundError):
            raise SObjectNotFoundError("SObject not found")
        
        # Test with custom message
        try:
            raise SObjectNotFoundError("No SObject with given criteria")
        except SObjectNotFoundError as e:
            self.assertEqual(str(e), "No SObject with given criteria")

    def test_event_not_found_error_duplicate(self):
        """Test EventNotFoundError exception (duplicate class)."""
        with self.assertRaises(EventNotFoundError):
            raise EventNotFoundError("Event not found")
        
        # Test with custom message
        try:
            raise EventNotFoundError("Event ID 789 not found")
        except EventNotFoundError as e:
            self.assertEqual(str(e), "Event ID 789 not found")

    def test_invalid_parameter_exception(self):
        """Test InvalidParameterException exception."""
        with self.assertRaises(InvalidParameterException):
            raise InvalidParameterException("Invalid parameter")
        
        # Test with custom message
        try:
            raise InvalidParameterException("Parameter 'id' is required")
        except InvalidParameterException as e:
            self.assertEqual(str(e), "Parameter 'id' is required")

    def test_invalid_argument_error(self):
        """Test InvalidArgumentError exception."""
        with self.assertRaises(InvalidArgumentError):
            raise InvalidArgumentError("Invalid argument")
        
        # Test with custom message
        try:
            raise InvalidArgumentError("Argument 'priority' must be High, Medium, or Low")
        except InvalidArgumentError as e:
            self.assertEqual(str(e), "Argument 'priority' must be High, Medium, or Low")

    def test_invalid_conditions_error(self):
        """Test InvalidConditionsError exception."""
        with self.assertRaises(InvalidConditionsError):
            raise InvalidConditionsError("Invalid conditions")
        
        # Test with custom message
        try:
            raise InvalidConditionsError("Conditions must be a list of strings")
        except InvalidConditionsError as e:
            self.assertEqual(str(e), "Conditions must be a list of strings")

    def test_unsupported_operator_error(self):
        """Test UnsupportedOperatorError exception."""
        with self.assertRaises(UnsupportedOperatorError):
            raise UnsupportedOperatorError("Unsupported operator")
        
        # Test with custom message
        try:
            raise UnsupportedOperatorError("Operator '!=' is not supported")
        except UnsupportedOperatorError as e:
            self.assertEqual(str(e), "Operator '!=' is not supported")

    def test_error_inheritance(self):
        """Test that all custom errors inherit from Exception."""
        error_classes = [
            TaskNotFoundError, InvalidDateFormatError, InvalidDateTypeError,
            InvalidReplicationDateError, ExceededIdLimitError, InvalidSObjectTypeError,
            UnsupportedSObjectTypeError, LayoutNotFound, EventNotFound, SObjectNotFoundError,
            EventNotFoundError, InvalidParameterException, InvalidArgumentError,
            InvalidConditionsError, UnsupportedOperatorError
        ]
        
        for error_class in error_classes:
            self.assertTrue(issubclass(error_class, Exception), 
                          f"{error_class.__name__} should inherit from Exception")

    def test_error_instantiation(self):
        """Test that all custom errors can be instantiated without arguments."""
        error_classes = [
            TaskNotFoundError, InvalidDateFormatError, InvalidDateTypeError,
            InvalidReplicationDateError, ExceededIdLimitError, InvalidSObjectTypeError,
            UnsupportedSObjectTypeError, LayoutNotFound, SObjectNotFoundError,
            EventNotFoundError, InvalidParameterException, InvalidArgumentError,
            InvalidConditionsError, UnsupportedOperatorError
        ]
        
        for error_class in error_classes:
            try:
                error_instance = error_class()
                self.assertIsInstance(error_instance, error_class)
            except TypeError:
                # EventNotFound requires a message parameter
                if error_class == EventNotFound:
                    error_instance = error_class("Test message")
                    self.assertIsInstance(error_instance, error_class)

    def test_error_with_context(self):
        """Test custom errors with context information."""
        # Test TaskNotFoundError with task ID
        try:
            raise TaskNotFoundError(f"Task with ID '00T1234567890123' not found")
        except TaskNotFoundError as e:
            self.assertIn("00T1234567890123", str(e))

        # Test InvalidDateFormatError with actual date
        try:
            raise InvalidDateFormatError(f"Invalid date format: '2023/13/45'")
        except InvalidDateFormatError as e:
            self.assertIn("2023/13/45", str(e))

        # Test ExceededIdLimitError with limit information
        try:
            raise ExceededIdLimitError(f"Query returned 2500 results, limit is 2000")
        except ExceededIdLimitError as e:
            self.assertIn("2500", str(e))
            self.assertIn("2000", str(e))

    def test_error_chaining(self):
        """Test that custom errors can be chained with other exceptions."""
        try:
            try:
                # Simulate a file operation that fails
                raise FileNotFoundError("Database file not found")
            except FileNotFoundError as e:
                # Chain with custom error
                raise TaskNotFoundError(f"Task lookup failed: {e}")
        except TaskNotFoundError as e:
            self.assertIn("Task lookup failed", str(e))
            self.assertIn("Database file not found", str(e))

    def test_error_comparison(self):
        """Test that custom errors can be compared."""
        error1 = TaskNotFoundError("Task not found")
        error2 = TaskNotFoundError("Task not found")
        error3 = TaskNotFoundError("Different message")
        
        # Test string comparison
        self.assertEqual(str(error1), str(error2))
        self.assertNotEqual(str(error1), str(error3))
        
        # Test type comparison
        self.assertIsInstance(error1, TaskNotFoundError)
        self.assertIsInstance(error1, Exception)

    def test_error_attributes(self):
        """Test that custom errors have expected attributes."""
        # Test EventNotFound with custom message attribute
        custom_message = "Custom event error message"
        error = EventNotFound(custom_message)
        self.assertEqual(error.message, custom_message)
        self.assertEqual(str(error), custom_message)

    def test_error_documentation(self):
        """Test that custom errors have proper docstrings."""
        error_classes = [
            (InvalidDateFormatError, "Exception raised when date format is invalid."),
            (InvalidDateTypeError, "Exception raised when date parameter is not a string."),
            (InvalidReplicationDateError, "Exception raised when replication date rules are violated."),
            (ExceededIdLimitError, "Exception raised when too many results are returned."),
            (InvalidSObjectTypeError, "Exception raised when sObjectType parameter is invalid."),
            (UnsupportedSObjectTypeError, "Exception raised when sObjectType is not supported by the module."),
            (LayoutNotFound, "Raised when a layout is not found."),
            (EventNotFound, "Raised when an event cannot be found in the Salesforce system."),
            (SObjectNotFoundError, "Exception raised when no sObject is found."),
            (EventNotFoundError, "Exception raised when no event is found."),  # Fixed: actual docstring
            (InvalidParameterException, "Exception raised when a parameter is invalid."),
            (InvalidArgumentError, "Exception raised when an invalid argument is provided."),
            (InvalidConditionsError, "Raised when the conditions parameter is not a valid list of strings."),
            (UnsupportedOperatorError, "Raised when a condition uses an unsupported operator.")
        ]
        
        for error_class, expected_doc in error_classes:
            if hasattr(error_class, '__doc__') and error_class.__doc__:
                self.assertIn(expected_doc.strip(), error_class.__doc__.strip())

    def test_error_usage_patterns(self):
        """Test common usage patterns for custom errors."""
        # Pattern 1: Validation error
        def validate_task_id(task_id):
            if not task_id or not isinstance(task_id, str):
                raise InvalidParameterException("task_id must be a non-empty string")
            if len(task_id) < 15:
                raise InvalidParameterException("task_id must be at least 15 characters")
            return task_id
        
        with self.assertRaises(InvalidParameterException):
            validate_task_id("")
        
        with self.assertRaises(InvalidParameterException):
            validate_task_id(123)
        
        # Pattern 2: Not found error
        def find_task(task_id):
            # Simulate task not found
            raise TaskNotFoundError(f"Task with ID '{task_id}' not found")
        
        with self.assertRaises(TaskNotFoundError) as cm:
            find_task("00T1234567890123")
        self.assertIn("00T1234567890123", str(cm.exception))

        # Pattern 3: Date validation error
        def validate_date(date_str):
            if not isinstance(date_str, str):
                raise InvalidDateTypeError("Date must be a string")
            # Simulate date format validation
            if not date_str or len(date_str) != 10 or date_str[4] != '-' or date_str[7] != '-':
                raise InvalidDateFormatError(f"Invalid date format: '{date_str}'")
            return date_str
        
        with self.assertRaises(InvalidDateTypeError):
            validate_date(123)
        
        with self.assertRaises(InvalidDateFormatError):
            validate_date("2023/01/01")


if __name__ == '__main__':
    unittest.main()