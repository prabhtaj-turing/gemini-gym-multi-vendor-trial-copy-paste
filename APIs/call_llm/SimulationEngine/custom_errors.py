class ValidationError(Exception):
    """Custom exception for input argument validation failures."""
    pass

class LLMExecutionError(Exception):
    """Custom exception for when model execution fails."""
    pass