"""
Custom error classes for the clock service.
"""

from typing import List, Optional


class ClockError(Exception):
    """Base exception class for clock-related errors."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EmptyFieldError(ClockError):
    """Raised when a required field is empty."""
    
    def __init__(self, field_name: str):
        self.field_name = field_name
        super().__init__(f"Field '{field_name}' cannot be empty")


class MissingRequiredFieldError(ClockError):
    """Raised when required fields are missing."""
    
    def __init__(self, field_names: List[str]):
        self.field_names = field_names
        if isinstance(field_names, str):
            field_names = [field_names]
        
        if len(field_names) == 1:
            message = f"Required field '{field_names[0]}' is missing"
        else:
            message = f"Required fields {', '.join(field_names)} are missing"
        
        super().__init__(message)


class InvalidTimeFormatError(ClockError):
    """Raised when a time format is invalid."""
    
    def __init__(self, time_str: str, expected_format: str = "H[:M[:S]]"):
        self.time_str = time_str
        self.expected_format = expected_format
        super().__init__(f"Invalid time format '{time_str}'. Expected format: {expected_format}")


class InvalidDurationFormatError(ClockError):
    """Raised when a duration format is invalid."""
    
    def __init__(self, duration_str: str):
        self.duration_str = duration_str
        super().__init__(f"Invalid duration format '{duration_str}'. Expected format like '5h30m20s', '10m', or '2m15s'")


class InvalidDateFormatError(ClockError):
    """Raised when a date format is invalid."""
    
    def __init__(self, date_str: str):
        self.date_str = date_str
        super().__init__(f"Invalid date format '{date_str}'. Expected format: YYYY-MM-DD")


class AlarmNotFoundError(ClockError):
    """Raised when an alarm is not found."""
    
    def __init__(self, alarm_id: str):
        self.alarm_id = alarm_id
        super().__init__(f"Alarm with ID '{alarm_id}' not found")


class TimerNotFoundError(ClockError):
    """Raised when a timer is not found."""
    
    def __init__(self, timer_id: str):
        self.timer_id = timer_id
        super().__init__(f"Timer with ID '{timer_id}' not found")


class InvalidRecurrenceError(ClockError):
    """Raised when recurrence days are invalid."""
    
    def __init__(self, invalid_days: List[str]):
        self.invalid_days = invalid_days
        super().__init__(f"Invalid recurrence days: {', '.join(invalid_days)}. Valid days are: SUNDAY, MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY")


class InvalidStateOperationError(ClockError):
    """Raised when an invalid state operation is requested."""
    
    def __init__(self, operation: str, valid_operations: List[str]):
        self.operation = operation
        self.valid_operations = valid_operations
        super().__init__(f"Invalid state operation '{operation}'. Valid operations are: {', '.join(valid_operations)}")


class AlarmAlreadyExistsError(ClockError):
    """Raised when trying to create an alarm that already exists."""
    
    def __init__(self, time: str, date: Optional[str] = None):
        self.time = time
        self.date = date
        if date:
            super().__init__(f"Alarm already exists for {time} on {date}")
        else:
            super().__init__(f"Alarm already exists for {time}")


class TimerAlreadyExistsError(ClockError):
    """Raised when trying to create a timer that already exists."""
    
    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"Timer already exists: {identifier}")


class InvalidAlarmFilterError(ClockError):
    """Raised when alarm filters are invalid."""
    
    def __init__(self, message: str):
        super().__init__(f"Invalid alarm filter: {message}")


class InvalidTimerFilterError(ClockError):
    """Raised when timer filters are invalid."""
    
    def __init__(self, message: str):
        super().__init__(f"Invalid timer filter: {message}")


class StopwatchStateError(ClockError):
    """Raised when stopwatch operation is invalid for current state."""
    
    def __init__(self, current_state: str, attempted_operation: str):
        self.current_state = current_state
        self.attempted_operation = attempted_operation
        super().__init__(f"Cannot perform '{attempted_operation}' when stopwatch is in '{current_state}' state")


class ValidationError(ClockError):
    """Raised when input validation fails."""
    
    def __init__(self, field: str, value: any, expected_type: str):
        self.field = field
        self.value = value
        self.expected_type = expected_type
        super().__init__(f"Validation failed for field '{field}': expected {expected_type}, got {type(value).__name__}") 