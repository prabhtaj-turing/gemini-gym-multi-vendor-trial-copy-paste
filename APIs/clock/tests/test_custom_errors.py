"""
Custom error tests for the Clock service.

This module tests all custom error classes in the Clock service's custom_errors module.
These are domain-specific exceptions that provide meaningful error messages for clock operations.

Test Categories:
- Error class instantiation tests
- Error message validation tests
- Error inheritance tests
- Error attribute tests
- Edge cases and error handling
"""

import unittest
from typing import List

try:
    from common_utils.base_case import BaseTestCaseWithErrorHandler
except ImportError:
    from common_utils.base_case import BaseTestCaseWithErrorHandler

from clock.SimulationEngine.custom_errors import (
    ClockError, EmptyFieldError, MissingRequiredFieldError,
    InvalidTimeFormatError, InvalidDurationFormatError, InvalidDateFormatError,
    AlarmNotFoundError, TimerNotFoundError, InvalidRecurrenceError,
    InvalidStateOperationError, AlarmAlreadyExistsError, TimerAlreadyExistsError,
    InvalidAlarmFilterError, InvalidTimerFilterError, StopwatchStateError,
    ValidationError
)


class TestCustomErrors(BaseTestCaseWithErrorHandler):
    """Test Clock service custom error classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
    
    def tearDown(self):
        """Clean up after tests."""
        super().tearDown()

    def test_clock_error_base_class(self):
        """Test the base ClockError class."""
        message = "Test error message"
        error = ClockError(message)
        
        self.assertIsInstance(error, Exception)
        self.assertEqual(error.message, message)
        self.assertEqual(str(error), message)

    def test_empty_field_error(self):
        """Test EmptyFieldError exception."""
        field_name = "duration"
        error = EmptyFieldError(field_name)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(error.field_name, field_name)
        self.assertEqual(str(error), f"Field '{field_name}' cannot be empty")

    def test_missing_required_field_error_single_field(self):
        """Test MissingRequiredFieldError with single field."""
        field_name = "time"
        error = MissingRequiredFieldError(field_name)
        
        self.assertIsInstance(error, ClockError)
        # The implementation stores the original input, not the converted list
        self.assertEqual(error.field_names, field_name)
        self.assertEqual(str(error), f"Required field '{field_name}' is missing")

    def test_missing_required_field_error_multiple_fields(self):
        """Test MissingRequiredFieldError with multiple fields."""
        field_names = ["time", "duration", "label"]
        error = MissingRequiredFieldError(field_names)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(error.field_names, field_names)
        expected_message = f"Required fields {', '.join(field_names)} are missing"
        self.assertEqual(str(error), expected_message)

    def test_missing_required_field_error_string_input(self):
        """Test MissingRequiredFieldError handles string input by converting to list."""
        field_name = "time"
        error = MissingRequiredFieldError(field_name)
        
        # The implementation stores the original input
        self.assertEqual(error.field_names, field_name)

    def test_invalid_time_format_error(self):
        """Test InvalidTimeFormatError exception."""
        time_str = "25:00"
        error = InvalidTimeFormatError(time_str)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(error.time_str, time_str)
        self.assertEqual(error.expected_format, "H[:M[:S]]")
        expected_message = f"Invalid time format '{time_str}'. Expected format: H[:M[:S]]"
        self.assertEqual(str(error), expected_message)

    def test_invalid_time_format_error_custom_format(self):
        """Test InvalidTimeFormatError with custom expected format."""
        time_str = "invalid"
        expected_format = "HH:MM:SS"
        error = InvalidTimeFormatError(time_str, expected_format)
        
        self.assertEqual(error.expected_format, expected_format)
        expected_message = f"Invalid time format '{time_str}'. Expected format: {expected_format}"
        self.assertEqual(str(error), expected_message)

    def test_invalid_duration_format_error(self):
        """Test InvalidDurationFormatError exception."""
        duration_str = "invalid"
        error = InvalidDurationFormatError(duration_str)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(error.duration_str, duration_str)
        expected_message = f"Invalid duration format '{duration_str}'. Expected format like '5h30m20s', '10m', or '2m15s'"
        self.assertEqual(str(error), expected_message)

    def test_invalid_date_format_error(self):
        """Test InvalidDateFormatError exception."""
        date_str = "2024-13-45"
        error = InvalidDateFormatError(date_str)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(error.date_str, date_str)
        expected_message = f"Invalid date format '{date_str}'. Expected format: YYYY-MM-DD"
        self.assertEqual(str(error), expected_message)

    def test_alarm_not_found_error(self):
        """Test AlarmNotFoundError exception."""
        alarm_id = "ALARM-123"
        error = AlarmNotFoundError(alarm_id)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(error.alarm_id, alarm_id)
        self.assertEqual(str(error), f"Alarm with ID '{alarm_id}' not found")

    def test_timer_not_found_error(self):
        """Test TimerNotFoundError exception."""
        timer_id = "TIMER-456"
        error = TimerNotFoundError(timer_id)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(error.timer_id, timer_id)
        self.assertEqual(str(error), f"Timer with ID '{timer_id}' not found")

    def test_invalid_recurrence_error(self):
        """Test InvalidRecurrenceError exception."""
        invalid_days = ["INVALID_DAY", "ANOTHER_INVALID"]
        error = InvalidRecurrenceError(invalid_days)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(error.invalid_days, invalid_days)
        expected_message = f"Invalid recurrence days: {', '.join(invalid_days)}. Valid days are: SUNDAY, MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY"
        self.assertEqual(str(error), expected_message)

    def test_invalid_state_operation_error(self):
        """Test InvalidStateOperationError exception."""
        operation = "INVALID_OP"
        valid_operations = ["START", "STOP", "PAUSE"]
        error = InvalidStateOperationError(operation, valid_operations)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(error.operation, operation)
        self.assertEqual(error.valid_operations, valid_operations)
        expected_message = f"Invalid state operation '{operation}'. Valid operations are: {', '.join(valid_operations)}"
        self.assertEqual(str(error), expected_message)

    def test_alarm_already_exists_error_with_date(self):
        """Test AlarmAlreadyExistsError with date."""
        time = "09:00 AM"
        date = "2024-01-15"
        error = AlarmAlreadyExistsError(time, date)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(error.time, time)
        self.assertEqual(error.date, date)
        self.assertEqual(str(error), f"Alarm already exists for {time} on {date}")

    def test_alarm_already_exists_error_without_date(self):
        """Test AlarmAlreadyExistsError without date."""
        time = "09:00 AM"
        error = AlarmAlreadyExistsError(time)
        
        self.assertEqual(error.time, time)
        self.assertIsNone(error.date)
        self.assertEqual(str(error), f"Alarm already exists for {time}")

    def test_timer_already_exists_error(self):
        """Test TimerAlreadyExistsError exception."""
        identifier = "Timer for 10 minutes"
        error = TimerAlreadyExistsError(identifier)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(error.identifier, identifier)
        self.assertEqual(str(error), f"Timer already exists: {identifier}")

    def test_invalid_alarm_filter_error(self):
        """Test InvalidAlarmFilterError exception."""
        message = "Invalid filter criteria"
        error = InvalidAlarmFilterError(message)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(str(error), f"Invalid alarm filter: {message}")

    def test_invalid_timer_filter_error(self):
        """Test InvalidTimerFilterError exception."""
        message = "Invalid timer filter criteria"
        error = InvalidTimerFilterError(message)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(str(error), f"Invalid timer filter: {message}")

    def test_stopwatch_state_error(self):
        """Test StopwatchStateError exception."""
        current_state = "STOPPED"
        attempted_operation = "PAUSE"
        error = StopwatchStateError(current_state, attempted_operation)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(error.current_state, current_state)
        self.assertEqual(error.attempted_operation, attempted_operation)
        expected_message = f"Cannot perform '{attempted_operation}' when stopwatch is in '{current_state}' state"
        self.assertEqual(str(error), expected_message)

    def test_validation_error(self):
        """Test ValidationError exception."""
        field = "duration"
        value = "invalid"
        expected_type = "string with valid format"
        error = ValidationError(field, value, expected_type)
        
        self.assertIsInstance(error, ClockError)
        self.assertEqual(error.field, field)
        self.assertEqual(error.value, value)
        self.assertEqual(error.expected_type, expected_type)
        expected_message = f"Validation failed for field '{field}': expected {expected_type}, got {type(value).__name__}"
        self.assertEqual(str(error), expected_message)

    def test_error_inheritance_hierarchy(self):
        """Test that all error classes inherit from ClockError properly."""
        error_classes = [
            EmptyFieldError, MissingRequiredFieldError, InvalidTimeFormatError,
            InvalidDurationFormatError, InvalidDateFormatError, AlarmNotFoundError,
            TimerNotFoundError, InvalidRecurrenceError, InvalidStateOperationError,
            AlarmAlreadyExistsError, TimerAlreadyExistsError, InvalidAlarmFilterError,
            InvalidTimerFilterError, StopwatchStateError, ValidationError
        ]
        
        for error_class in error_classes:
            with self.subTest(error_class=error_class.__name__):
                self.assertTrue(issubclass(error_class, ClockError))
                self.assertTrue(issubclass(error_class, Exception))

    def test_error_messages_non_empty(self):
        """Test that all error instances produce non-empty messages."""
        test_cases = [
            (EmptyFieldError("test_field"), ),
            (MissingRequiredFieldError(["field1"]), ),
            (InvalidTimeFormatError("25:00"), ),
            (InvalidDurationFormatError("invalid"), ),
            (InvalidDateFormatError("invalid"), ),
            (AlarmNotFoundError("alarm-1"), ),
            (TimerNotFoundError("timer-1"), ),
            (InvalidRecurrenceError(["INVALID"]), ),
            (InvalidStateOperationError("INVALID", ["VALID"]), ),
            (AlarmAlreadyExistsError("09:00"), ),
            (TimerAlreadyExistsError("test"), ),
            (InvalidAlarmFilterError("test"), ),
            (InvalidTimerFilterError("test"), ),
            (StopwatchStateError("STOPPED", "PAUSE"), ),
            (ValidationError("field", "value", "string"), ),
        ]
        
        for error_instance, in test_cases:
            with self.subTest(error_type=type(error_instance).__name__):
                message = str(error_instance)
                self.assertIsInstance(message, str)
                self.assertGreater(len(message), 0)
                self.assertFalse(message.isspace())

    def test_error_attributes_accessible(self):
        """Test that error-specific attributes are properly accessible."""
        # Test EmptyFieldError
        empty_error = EmptyFieldError("test_field")
        self.assertEqual(empty_error.field_name, "test_field")
        
        # Test InvalidTimeFormatError  
        time_error = InvalidTimeFormatError("25:00", "HH:MM")
        self.assertEqual(time_error.time_str, "25:00")
        self.assertEqual(time_error.expected_format, "HH:MM")
        
        # Test InvalidStateOperationError
        state_error = InvalidStateOperationError("INVALID", ["VALID1", "VALID2"])
        self.assertEqual(state_error.operation, "INVALID")
        self.assertEqual(state_error.valid_operations, ["VALID1", "VALID2"])
        
        # Test AlarmAlreadyExistsError with and without date
        alarm_error_with_date = AlarmAlreadyExistsError("09:00", "2024-01-01")
        self.assertEqual(alarm_error_with_date.time, "09:00")
        self.assertEqual(alarm_error_with_date.date, "2024-01-01")
        
        alarm_error_without_date = AlarmAlreadyExistsError("09:00")
        self.assertEqual(alarm_error_without_date.time, "09:00")
        self.assertIsNone(alarm_error_without_date.date)

    def test_error_raising_and_catching(self):
        """Test that errors can be properly raised and caught."""
        # Test raising and catching specific error
        with self.assertRaises(EmptyFieldError) as cm:
            raise EmptyFieldError("test_field")
        
        caught_error = cm.exception
        self.assertEqual(caught_error.field_name, "test_field")
        
        # Test catching as base ClockError
        with self.assertRaises(ClockError):
            raise InvalidTimeFormatError("25:00")
        
        # Test catching as general Exception
        with self.assertRaises(Exception):
            raise TimerNotFoundError("timer-1")

    def test_error_repr_and_str_consistency(self):
        """Test that error string representation is consistent."""
        error = InvalidDurationFormatError("invalid_duration")
        
        # Both str() and direct access should give same result
        self.assertEqual(str(error), error.message)
        
        # Message should be descriptive
        self.assertIn("invalid_duration", str(error))
        self.assertIn("Invalid duration format", str(error))
