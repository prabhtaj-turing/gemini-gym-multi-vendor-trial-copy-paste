class NotFoundError(Exception):
    """Raised if the presentation with the given 'presentation_id' does not exist."""
    pass

class InvalidInputError(Exception):
    """Raised if the 'requests' list is malformed, contains invalid update
    operations, or 'write_control' is invalid."""
    pass

class ConcurrencyError(Exception):
    """Raised if a write control conflict occurs (e.g., the provided
    revision ID in 'write_control' does not match the current
    revision of the presentation)."""
    pass

class ValidationError(Exception):
    """Raised when input arguments fail validation."""
    pass

class UserNotFoundError(Exception):
    """Raised when a user is not found in the database."""
    pass
