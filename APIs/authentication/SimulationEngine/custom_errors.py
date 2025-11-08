"""
Authentication Service Custom Errors

Defines custom exceptions for authentication operations.
"""
class AuthenticationError(Exception):
    """Raised when authentication operations fail."""
    pass
class ValidationError(Exception):
    """Raised when input validation fails."""
    pass
class ServiceNotFoundError(AuthenticationError):
    """Raised when a service is not found."""
    pass
class AuthenticationSessionError(AuthenticationError):
    """Raised when authentication session operations fail."""
    pass