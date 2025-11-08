class InternalError(Exception):
    """Exception raised for internal errors."""
    pass

class DatabaseOrTableDoesNotExistError(Exception):
    """Exception raised when the database or table does not exist."""
    pass

