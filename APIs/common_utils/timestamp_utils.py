"""
Timestamp Utilities for Consistent ISO 8601 Format

This module provides standardized timestamp generation functions to ensure
all APIs use the same ISO 8601 format: YYYY-MM-DDTHH:MM:SS.ffffffZ

Key Points:
- Always use datetime.timezone.utc (NOT datetime.UTC)
- Always use .replace("+00:00", "Z") (NOT + "Z")
- This ensures timestamps like: 2025-10-06T21:05:52.510677Z
- Prevents malformed timestamps like: 2025-10-06T21:05:52.510677+00:00Z
"""

import datetime
from typing import Optional


def get_iso_timestamp() -> str:
    """
    Returns the current time in ISO 8601 format with 'Z' suffix (UTC).
    
    This is the standard timestamp format used across all APIs.
    
    Returns:
        str: ISO 8601 timestamp string, e.g., "2025-10-06T21:05:52.510677Z"
    
    Example:
        >>> timestamp = get_iso_timestamp()
        >>> print(timestamp)
        2025-10-06T21:05:52.510677Z
    """
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def timestamp_from_unix(unix_timestamp: float) -> str:
    """
    Converts a Unix timestamp (seconds since epoch) to ISO 8601 format with 'Z' suffix.
    
    Args:
        unix_timestamp (float): Unix timestamp in seconds (e.g., from os.path.getmtime())
    
    Returns:
        str: ISO 8601 timestamp string, e.g., "2025-10-06T21:05:52.510677Z"
    
    Example:
        >>> import os
        >>> mtime = os.path.getmtime("file.txt")
        >>> timestamp = timestamp_from_unix(mtime)
        >>> print(timestamp)
        2025-10-06T21:05:52.510677Z
    """
    return datetime.datetime.fromtimestamp(
        unix_timestamp, tz=datetime.timezone.utc
    ).isoformat().replace("+00:00", "Z")


def validate_iso_timestamp(timestamp_str: str) -> bool:
    """
    Validates whether a string is a valid ISO 8601 timestamp.
    
    Requires both date AND time components (date-only strings are invalid).
    
    Args:
        timestamp_str (str): The timestamp string to validate
    
    Returns:
        bool: True if valid ISO 8601 format, False otherwise
    
    Example:
        >>> validate_iso_timestamp("2025-10-06T21:05:52.510677Z")
        True
        >>> validate_iso_timestamp("2025-10-06T21:05:52.510677+00:00Z")
        False  # Malformed
        >>> validate_iso_timestamp("2025-10-06")
        False  # Date only, missing time
        >>> validate_iso_timestamp("invalid")
        False
    """
    if not isinstance(timestamp_str, str):
        return False
    
    if not timestamp_str:
        return False
    
    # Must contain 'T' separator (date AND time required)
    if 'T' not in timestamp_str:
        return False
    
    try:
        # Handle both Z and +00:00 formats
        test_str = timestamp_str.replace('Z', '+00:00')
        datetime.datetime.fromisoformat(test_str)
        
        # Additional check: ensure no malformed +00:00Z
        if '+00:00Z' in timestamp_str:
            return False
        
        return True
    except (ValueError, AttributeError):
        return False


def fix_malformed_timestamp(timestamp_str: str) -> str:
    """
    Attempts to fix common timestamp formatting issues.
    
    Args:
        timestamp_str (str): Potentially malformed timestamp string
    
    Returns:
        str: Fixed timestamp string in standard format
    
    Example:
        >>> fix_malformed_timestamp("2025-10-06T21:05:52.510677+00:00Z")
        "2025-10-06T21:05:52.510677Z"
    """
    if not isinstance(timestamp_str, str):
        return get_iso_timestamp()  # Return current time as fallback
    
    # Fix double timezone suffix: +00:00Z -> Z
    if '+00:00Z' in timestamp_str:
        return timestamp_str.replace('+00:00Z', 'Z')
    
    # Fix missing Z: +00:00 -> Z (standardize to Z format)
    if timestamp_str.endswith('+00:00') and not timestamp_str.endswith('Z'):
        return timestamp_str.replace('+00:00', 'Z')
    
    return timestamp_str


# Alias for backward compatibility
get_current_timestamp_iso = get_iso_timestamp
