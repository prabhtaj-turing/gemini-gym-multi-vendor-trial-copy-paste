class CommandExecutionError(Exception):
    """
    Raised when an external command fails to execute or returns a non-zero exit code.
    """
    pass

class MetadataError(Exception):
    """Exception raised when metadata operations fail in strict mode."""
    pass


class InvalidDateTimeFormatError(Exception):
    """Raised when a datetime string is not in valid ISO 8601 format."""
    pass
