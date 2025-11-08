"""
Custom error classes for the porting scripts.
"""

class DateTimeValidationError(Exception):
    """Custom exception for datetime validation errors."""
    pass


class InvalidDateTimeFormatError(DateTimeValidationError):
    """Raised when a datetime string cannot be parsed or is in an invalid format."""
    pass


class UnsupportedDateTimeFormatError(DateTimeValidationError):
    """Raised when a datetime string is valid but not supported by the specific service."""
    pass
