class InvalidRequestError(Exception):
    """Error for invalid requests made by the client."""
    pass

class ResourceNotFoundError(Exception):
    """Error indicating a requested resource was not found. Preserved from existing definitions."""
    pass

class ApiError(Exception):
    """Generic error for API interactions."""
    pass

class ValidationError(Exception):
    """Custom exception for input argument validation failures."""
    pass

class NotFoundError(Exception):
    """Raised when a specific item (e.g., a project as per get_project) is not found.
    This corresponds to the 'NotFoundError' in the get_project docstring."""
    pass
class InvalidRequestError(Exception):
    """Custom exception for invalid requests."""
    pass

class ResourceNotFoundError(Exception):
    """Custom exception for when a resource is not found."""
    pass

class ApiError(Exception):
    """Base custom exception for API-related errors."""
    pass

class ValidationError(Exception):
    """Custom exception for input argument validation failures."""
    pass

class NotFoundError(Exception):
    """Custom exception for when an entity is not found (e.g., organization)."""
    pass

class PermissionDeniedError(Exception):
    """Custom exception for permission denied errors."""
    pass

class OperationNotPermittedError(Exception):
    """Valid request but operation not allowed due to state transition rules"""
    pass

class MergeConflictError(Exception):
    """Custom exception for conflicts that prevent a merge (e.g., migration conflicts, edge function conflicts)."""
    pass
class BranchingNotEnabledError(Exception):
    "Accessing branching feature of a project with branching_enabled feature not present in the list of feature for an organization"
    pass

class RebaseConflictError(Exception):
    """Custom exception for rebase conflicts that cannot be automatically resolved."""
    pass

class MigrationError(Exception):
    """Custom exception for when a migration query fails to apply."""
    pass
class InvalidInputError(Exception):
    """
    Custom exception for inconsistent or invalid input details,
    especially when they do not match a previously obtained quote.
    """
    pass

class DatabaseConnectionError(Exception):
    """Custom exception for database connection failures."""
    pass

class SQLError(Exception):
    """Custom exception for SQL execution errors."""
    pass

class LogsNotAvailableError(Exception):
    """Custom exception for when logs are not available for a service or time frame."""
    pass
class FeatureNotEnabledError(Exception):
    """Custom exception for when a feature (e.g., Edge Functions) is not enabled or available for the project's subscription plan."""
    pass

class TypeGenerationError(Exception):
    """Custom exception for errors during the type generation process."""
    pass

class CostConfirmationError(Exception):
    """
    Custom exception for issues related to cost confirmation.
    Raised if the confirm_cost_id is invalid, expired, already used,
    or does not match the intended operation.
    """
    pass
