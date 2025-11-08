class InvalidFormatError(ValueError):
    """Custom error raised when an invalid 'format' parameter is provided."""
    pass
class InvalidMaxResultsValueError(ValueError):
    """Custom error for invalid max_results argument."""
    pass

class InvalidFormatValueError(ValueError):
    """Custom error for invalid 'format' argument values."""
    pass

class ValidationError(ValueError):
    """Custom error for validation errors."""
    pass

class NotFoundError(Exception):
    """Custom error for when a requested resource is not found."""
    pass

class InvalidDateTimeFormatError(ValueError):
    """Raised when a datetime string is not in the expected format."""
    pass