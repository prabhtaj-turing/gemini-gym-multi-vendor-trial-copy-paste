class InvalidRequestError(ValueError):
    """Custom error for requests that are malformed (e.g., wrong number of keys)."""
    pass

class UnsupportedRequestTypeError(InvalidRequestError):
    """Custom error for unsupported request types in the batch update."""
    pass

# Note: Business logic errors like "SheetAlreadyExistsError" or "SheetNotFoundError"
# are kept as ValueError as in the original function, arising from core logic after validation.
# If more specific exceptions were desired for these, they would be defined here.

class InvalidFunctionParameterError(ValueError):
    """Custom error for invalid function parameter values not covered by TypeError or Pydantic's ValidationError."""
    pass
