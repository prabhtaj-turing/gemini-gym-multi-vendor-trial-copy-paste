"""Custom exceptions for gemini_cli SimulationEngine.

We start with a minimal set; extend as tools surface more specific error
cases.
"""

class InvalidInputError(Exception):
    """Raised when a parameter fails validation."""
    pass


class WorkspaceNotAvailableError(Exception):
    """Raised when workspace_root or file_system is missing."""
    pass


class InvalidGlobPatternError(Exception):
    """Raised when a glob pattern cannot be parsed."""
    pass


class CommandExecutionError(Exception):
    """Raised when run_in_terminal encounters an error."""
    pass

class ShellSecurityError(Exception):
    """Raised when a command is blocked for security reasons."""
    pass

class ProcessNotFoundError(Exception):
    """Raised when a background process ID is not found."""
    pass

class MetadataError(Exception):
    """Exception raised when metadata operations fail in strict mode."""
    pass


class InvalidDateTimeFormatError(Exception):
    """Raised when a datetime string is not in valid ISO 8601 format."""
    pass