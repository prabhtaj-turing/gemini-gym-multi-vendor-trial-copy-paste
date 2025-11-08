class InvalidMediaIDError(ValueError):
    """Custom error raised when media_id is invalid (e.g., an empty string)."""
    pass

class EmptyUsernameError(ValueError):
    """Raised when the username argument is empty or contains only whitespace."""
    pass
  
class UserNotFoundError(ValueError):
    """Custom error raised when a user is not found in the database."""
    pass
  
class UserAlreadyExistsError(ValueError):
    """Custom error raised when trying to create a user that already exists."""
    pass

class MediaNotFoundError(ValueError):
    """Custom exception raised when a media item cannot be found."""
    pass