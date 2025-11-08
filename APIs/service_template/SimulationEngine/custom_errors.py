"""
Custom Exceptions for the Generic Service

This module defines custom exception classes to handle specific error scenarios
within the service. Using custom exceptions makes the code more readable and
allows for more precise error handling.
"""

class ValidationError(Exception):
    """
    Raised when input argument validation fails.
    This is typically used in the main tool function (`entity.py`) to check
    the parameters provided by the user.
    """
    pass

class ResourceNotFoundError(Exception):
    """
    Raised when a requested resource (e.g., an entity) cannot be found.
    This is useful for CRUD operations where an ID is provided for a
    non-existent resource.
    """
    pass
