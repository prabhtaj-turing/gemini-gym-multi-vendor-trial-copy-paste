"""
Custom error classes for the youtube_tool API.
"""

class APIError(Exception):
    """Base class for API errors."""
    pass

class ExtractionError(Exception):
    """Base class for extraction errors."""
    pass

class EnvironmentError(Exception):
    """Base class for environment errors."""
    pass