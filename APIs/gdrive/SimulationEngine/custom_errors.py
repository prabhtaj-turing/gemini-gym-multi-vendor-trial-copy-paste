class MissingEmailForOwnershipTransferError(ValueError):
    """
    Raised when 'transferOwnership' is True but 'emailAddress' is not provided
    in the 'body' for the update operation.
    """
    pass
class InvalidPageSizeError(ValueError):
    """Custom error for invalid pageSize values."""
    pass

class PageSizeOutOfBoundsError(ValueError):
    """Custom error for pageSize being outside the allowed range."""
    pass

class InvalidTimestampFormatError(ValueError):
    """Custom error for startModifiedTime not being a valid RFC 3339 timestamp."""
    pass

class MalformedPageTokenError(ValueError):
    """Custom error for pageToken having an invalid format."""
    pass

class ValidationError(ValueError):
    """Custom error for validation errors."""
    pass

class QuotaExceededError(Exception):
    """Custom error for when storage quota is exceeded."""
    pass

class InvalidQueryError(ValueError):
    """Custom error for invalid query strings."""
    pass

class PermissionDeniedError(Exception):
    """Raised when the user does not have permission to perform an action."""
    pass

class LastOwnerDeletionError(Exception):
    """Raised when attempting to delete the last owner of a file without transferring ownership."""
    pass

class ResourceNotFoundError(Exception):
    """Custom error for when a requested resource (e.g., a file) is not found."""
    pass
  
class NotFoundError(ValueError):
    """Raised when a resource is not found."""
    pass

class InvalidRequestError(Exception):
    """Raised when a request is invalid or malformed."""
    pass

class FileNotFoundError(Exception):
    """Raised when a requested file does not exist."""
    pass

class ChannelNotFoundError(Exception):
    """Raised when a requested channel does not exist."""
    pass

class InvalidDateTimeFormatError(ValueError):
    """Raised when a datetime string is not in the expected format."""
    pass

class UserNotFoundError(ValueError):
    """Raised when a user is not found in the database."""
    pass