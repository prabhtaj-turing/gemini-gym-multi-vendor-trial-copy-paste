"""
Calendar-specific helper functions for datetime validation.
"""

import re
from zoneinfo import ZoneInfo
from typing import Optional, Tuple
from .custom_errors import DateTimeValidationError


def is_datetime_of_format(datetime_str: str, format_type: str) -> bool:
    """
    Checks if a datetime string is of a given format.

    Args:
        datetime_str (str): The datetime string to check
        format_type (str): The expected format type
    
    Returns:
        bool: True if the datetime string is of the given format, False otherwise
    
    Raises:
        DateTimeValidationError: If the format_type is not supported
    
    Example:
        >>> is_datetime_of_format("2024-03-15T14:30:45Z", "ISO_8601_UTC_Z")
        True
        >>> is_datetime_of_format("2024-03-15 14:30:45", "ISO_8601_UTC_Z")
        False
    """    
    if format_type == "ISO_8601_UTC_Z":
        return re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$', datetime_str) is not None
    elif format_type == "ISO_8601_UTC_OFFSET":
        return re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$', datetime_str) is not None
    elif format_type == "ISO_8601_WITH_TIMEZONE":
        return re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$', datetime_str) is not None
    else:
        raise DateTimeValidationError(f"Unsupported format type: {format_type}")


def validate_google_calendar_datetime(dateTime: str, timeZone: Optional[str] = None) -> Tuple[str, Optional[str]]:
    """
    Validate datetime and timezone IANA for Google Calendar (ISO_8601_UTC_Z, ISO_8601_UTC_OFFSET, or
    ISO_8601_WITH_TIMEZONE).
    
    Args:
        dateTime (str): The datetime string to validate
        timeZone (Optional[str]): The timezone in IANA format (e.g. "America/Sao_Paulo"). Default to None.
    
    Returns:
        dateTime (str): The datetime string validated
        timeZone (Optional[str]): The timezone in IANA format. Defaults to None.
    
    Raises:
        DateTimeValidationError: If the datetime string is invalid; or
                                 timezone is invalid; or
                                 nor the datetime have timezone info nor the timezone is provided.
    
    Example:
        >>> validate_google_calendar_datetime("2024-03-15T14:30:45", "America/Sao_Paulo")
        ("2024-03-15T14:30:45", "America/Sao_Paulo")
        >>> validate_google_calendar_datetime("2024-03-15 14:30:45+04:00")
        ("2024-03-15T14:30:45", None)
    """
    if not dateTime or not isinstance(dateTime, str):
        raise DateTimeValidationError("dateTime must be a string")
    
    if not is_datetime_of_format(dateTime, "ISO_8601_UTC_Z") and not is_datetime_of_format(dateTime, "ISO_8601_UTC_OFFSET") and not is_datetime_of_format(dateTime, "ISO_8601_WITH_TIMEZONE"):
        raise DateTimeValidationError("Invalid dateTime")
    
    if timeZone:
        try:
            ZoneInfo(timeZone)
        except Exception:
            raise DateTimeValidationError("Invalid timeZone")
    
    if is_datetime_of_format(dateTime, "ISO_8601_WITH_TIMEZONE") and not timeZone:
        raise DateTimeValidationError("If timeZone is not provided, dateTime must have timezone information.")
    
    return dateTime, timeZone
