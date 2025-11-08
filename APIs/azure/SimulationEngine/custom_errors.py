'''
Custom error classes for the Azure Simulation Engine.
This module defines custom exceptions used throughout the Azure API simulation.
These exceptions are derived from the "raises" sections of the Azure MCP tools JSON definition,
focusing on the P0 API functions. They help provide clear error messages and
proper error handling for various scenarios encountered during simulated API operations.
Related Simulation Engine Modules:
    - utils.py: May use these exceptions for utility function errors.
    - future API function modules: Will raise these exceptions to simulate API call failures.
'''


class AzureSimulationError(Exception):
    """
    Base class for all Azure simulation errors.
    Provides a common structure for error handling.
    Attributes:
        message (str): The error message.
        status_code (int): An HTTP-like status code for the error.
        error_code (str): The name of the error class (e.g., "ResourceNotFoundError").
    """

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = self.__class__.__name__


# --- Security and Access Errors ---
class AuthenticationError(AzureSimulationError):
    """
    Simulates an authentication failure.
    Raised when credentials are invalid, expired, or insufficient for the operation.
    Common Scenarios:
        - Invalid API key or token.
        - Expired credentials.
        - Service principal misconfiguration.
    """

    def __init__(self, message: str = "Authentication failed or credentials are invalid.", status_code: int = 401):
        super().__init__(message, status_code)


class PermissionError(AzureSimulationError):
    """
    Simulates a permission denial for an authenticated identity.
    Raised when the user or service principal has authenticated successfully
    but lacks the necessary permissions for the requested action on a resource.
    Common Scenarios:
        - Missing required RBAC roles (e.g., Reader, Contributor).
        - Access policies on a resource (like Key Vault) do not grant the operation.
    """

    def __init__(self,
                 message: str = "The authenticated user does not have the required permissions for this operation.",
                 status_code: int = 403):
        super().__init__(message, status_code)


# --- Resource-Related Errors ---
class ResourceNotFoundError(AzureSimulationError):
    """
    Simulates a situation where a specified Azure resource was not found.
    This is a base for more specific 'not found' errors.
    Common Scenarios:
        - Referencing a resource by a name or ID that does not exist.
        - Incorrectly specifying the resource group or subscription for a resource.
    """

    def __init__(self, message: str = "The specified Azure resource was not found.", status_code: int = 404):
        super().__init__(message, status_code)


class SubscriptionNotFoundError(ResourceNotFoundError):
    """
    Simulates a case where the specified Azure subscription ID is not found or accessible.
    This typically occurs when a subscription ID is provided that does not match
    any subscriptions the authenticated identity can access.
    """

    def __init__(self, message: str = "The specified Azure subscription was not found or is not accessible.",
                 status_code: int = 404):
        super().__init__(message, status_code)


class TenantNotFoundError(ResourceNotFoundError):
    """
    Simulates a case where the specified Azure tenant ID is not found or accessible.
    (Primarily for azmcp-subscription-list when a tenant is specified)
    """

    def __init__(self, message: str = "The specified Azure tenant was not found or is inaccessible.",
                 status_code: int = 404):
        super().__init__(message, status_code)


class ConflictError(AzureSimulationError):
    """
    Simulates a conflict with the current state of a resource.
    This error indicates that the requested operation cannot be completed because
    it conflicts with an existing state or configuration of the target resource.
    Common Scenarios:
        - Attempting to create a resource that already exists with the same name.
        - Attempting to modify a locked resource.
        - ETag mismatch during an optimistic concurrency update.
    """

    def __init__(self, message: str = "Operation conflicts with the current state of the resource.",
                 status_code: int = 409):
        super().__init__(message, status_code)


# --- Input and Execution Errors ---
class InvalidInputError(AzureSimulationError):
    """
    Simulates errors due to invalid or missing input parameters provided by the client.
    The request itself is malformed or contains data that does not meet the API's requirements.
    Common Scenarios:
        - Missing required parameters in the request.
        - Parameters with values outside the allowed range or format.
        - Syntactically incorrect query strings.
    """

    def __init__(self, message: str = "One or more input parameters are invalid or missing.", status_code: int = 400):
        super().__init__(message, status_code)


class QueryExecutionError(AzureSimulationError):
    """
    Simulates an error during the execution of a query (e.g., KQL, SQL for Cosmos DB).
    This implies the query was syntactically valid enough to attempt execution,
    but failed due to semantic issues, data access problems, or resource limitations.
    Common Scenarios:
        - Query references non-existent fields or tables (semantically incorrect).
        - Query execution times out.
        - Service-side resource limits reached during query processing.
    """

    def __init__(self, message: str = "The query failed to execute due to semantic errors or other issues.",
                 status_code: int = 400):  # Or 500 if considered more server-side
        super().__init__(message, status_code)


# --- Service and Operational Errors ---
class ServiceError(AzureSimulationError):
    """
    Simulates an unexpected error within an Azure service or its dependencies.
    This typically indicates a server-side issue not directly caused by the client's request.
    This is a base for more specific service-related issues.
    Common Scenarios:
        - Transient issues within an Azure service.
        - Internal service misconfigurations or bugs.
        - Problems with underlying dependencies of the Azure service.
    """

    def __init__(self, message: str = "An unexpected error occurred with the Azure service during the operation.",
                 status_code: int = 500):
        super().__init__(message, status_code)


class NetworkTimeoutError(ServiceError):
    """
    Simulates a network timeout occurring after all retry attempts have been exhausted.
    Indicates that the service did not respond within the expected timeframe,
    potentially due to network issues or service unresponsiveness.
    """

    def __init__(self,
                 message: str = "The request timed out after all retry attempts, potentially due to network issues or service unresponsiveness.",
                 status_code: int = 504):  # Gateway Timeout
        super().__init__(message, status_code)


class InvalidDateTimeFormatError(Exception):
    """Raised when a datetime string is not in the expected format."""
    pass

class ValidationError(AzureSimulationError):
    """
    Simulates an error when input arguments fail validation beyond basic type or format checks.
    This can occur if combinations of parameters are invalid, values do not meet specific
    business rules or constraints, or other programmatic validation checks fail.
    """

    def __init__(self, message: str = "Input arguments failed validation.", status_code: int = 400):
        super().__init__(message, status_code)
