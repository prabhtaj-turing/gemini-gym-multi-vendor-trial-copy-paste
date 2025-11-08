class NotFoundError(Exception):
    """Exception raised when a resource is not found."""
    pass

class InvalidInputError(Exception):
    """Exception raised for invalid input."""
    pass

class WorkflowDisabledError(Exception):
    """Exception raised when a workflow is disabled."""
    pass

class ConflictError(Exception):
    """Exception raised due to a conflict."""
    pass

class WorkflowRunCreationError(Exception):
    """Exception raised when a workflow run could not be created."""
    pass