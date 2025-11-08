"""Custom exceptions for the Google Maps API."""


class ParseError(Exception):
    """Raised when the response from Gemini is not in the expected format."""
    pass

class UserLocationError(Exception):
    """
    Custom exception raised when a provided value is not a valid UserLocation.
    """
    pass

class UndefinedLocationError(Exception):
    """
    Custom exception raised when a location variable is not found in the environment variables.
    """
    pass
