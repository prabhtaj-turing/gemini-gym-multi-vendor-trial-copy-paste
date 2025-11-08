"""Custom exceptions for claude_code SimulationEngine.
"""

class InvalidInputError(Exception):
    """Raised when a parameter fails validation."""
    pass


class WorkspaceNotAvailableError(Exception):
    """Raised when workspace_root or file_system is missing."""
    pass


class FileSystemError(Exception):
    """Base class for file system related errors."""
    pass


class InvalidPathError(FileSystemError):
    """Raised for invalid or disallowed file paths."""
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


class InvalidCodeError(Exception):
    """Raised when the provided string is not valid code that can be parsed or analyzed."""
    pass

class NotImplementedError(Exception):
    """Raised when a method is not implemented."""
    pass
