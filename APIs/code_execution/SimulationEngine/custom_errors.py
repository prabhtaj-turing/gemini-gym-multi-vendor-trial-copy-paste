class ValidationError(Exception):
    """Custom exception for input argument validation failures."""
    pass

class ServiceNotFoundError(Exception):
    """Custom exception for when a service is not found."""
    pass

class ToolNotFoundError(Exception):
    """Custom exception for when a tool is not found."""
    pass

class CodeExecutionError(Exception):
    """Custom exception for when code execution fails."""
    pass

class LLMExecutionError(Exception):
    """Custom exception for when model execution fails."""
    pass

class FileWriteError(Exception):
    """Custom exception for when file writing fails."""
    pass

class FileNotFoundError(Exception):
    """Custom exception for when a file is not found."""
    pass

class AuthenticationError(Exception):
    """Custom exception for authentication-related errors."""
    pass