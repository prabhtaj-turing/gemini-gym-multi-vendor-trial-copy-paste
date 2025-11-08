class InvalidRequestError(Exception):
    pass

class ResourceNotFoundError(Exception):
    pass

class ApiError(Exception):
    pass

class ValidationError(Exception):
    """Custom exception for input argument validation failures."""
    pass

class ProductNotFoundError(Exception):
    pass

class InvalidDateTimeFormatError(Exception):
    """Raised when a datetime string is not in the expected format."""
    pass
