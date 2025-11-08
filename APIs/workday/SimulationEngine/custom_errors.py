class InvalidAttributeError(ValueError):
    """Custom error for invalid attribute names in the 'attributes' parameter."""
    pass
class InvalidPaginationParameterError(ValueError):
    """Custom error for invalid 'startIndex' or 'count' parameter values."""
    pass
class InvalidSortByValueError(ValueError):
    """Custom error for invalid 'sortBy' parameter values."""
    pass
class InvalidSortOrderValueError(ValueError):
    """Custom error for invalid 'sortOrder' parameter values."""
    pass

class ProjectIDMismatchError(ValueError):
    """Custom error raised when the ID in the path does not match the ID in the project_data payload."""
    pass

class InvalidInputError(Exception):
    """Exception raised for invalid input parameters (e.g., non-positive IDs)."""
    pass

class LineItemNotFound(Exception):
    """Exception raised when a line item is not found in the database."""
    pass

class LineItemMismatchError(Exception):
    """Exception raised when a line item does not belong to the specified event or worksheet."""
    pass

class InvalidIdentifierError(ValueError):
    """Exception raised when an identifier is not a positive integer."""
    pass

class NotFoundError(Exception):
    """Exception raised when a requested resource is not found."""
    pass
    
class ValidationError(Exception):
    """Raised when input data fails validation."""
    pass

class ConflictError(Exception):
    """Raised when there is a conflict in the provided data, such as mismatched IDs."""
    pass

class InvalidInputError(ValueError):
    """Exception raised for invalid input parameters, such as type or range violations."""
    pass

class DatabaseStructureError(KeyError):
    """Exception raised when an expected key is not found in the mock database structure."""
    pass

class AuthenticationError(Exception):
    """
    Raised when authentication fails due to invalid or missing credentials.
    
    Attributes:
        message: A description of the authentication error.
        status_code: The HTTP status code (typically 401).
    """
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class PaymentTypesDatabaseError(ValueError):
    """Custom error for payment types database access and structure issues."""
    pass

class DataIntegrityError(Exception):
    """Raised when an object with an invalid structure is retrieved from the database."""
    pass

class ResourceNotFoundError(Exception):
    """
    Raised when a requested resource cannot be found in the database.
    This would typically map to an HTTP 404 Not Found response.
    """
    pass

class DatabaseSchemaError(Exception):
    """
    Raised when the application encounters an unexpected internal database structure.
    This would typically map to an HTTP 500 Internal Server Error status.
    """
    pass

class EventNotFoundError(Exception):
    """Raised when an event with the specified ID is not found."""
    pass

class InvalidEventTypeError(Exception):
    """Raised when an operation is attempted on an event of an unsupported type."""
    pass

class SupplierNotFoundError(Exception):
    """Raised when one or more supplier IDs are not found in the database."""
    pass

class InvalidPayloadError(Exception):
    """Raised when the request payload is malformed or fails validation."""
    pass

class ValidationError(ValueError):
    """Custom error raised when the input data does not match the expected format."""
    pass

class InvalidInputError(ValueError):
    """Raised when user input is invalid (e.g., wrong type, format, or value)."""
    pass

class EventNotFound(Exception):
    """Exception raised when an event cannot be found."""
    pass

class InvalidEventType(Exception):
    """Exception raised when an operation is attempted on an event of an unsupported type."""
    pass

class DuplicateExternalIdError(Exception):
    """Raised when an attempt is made to create an entity with an external_id that already exists."""
    def __init__(self, message="Entity with this external_id already exists."):
        self.message = message
        super().__init__(self.message)

class ContractNotFoundError(ValueError):
    """Custom error for when a contract is not found in the database."""
    pass

class ContractValidationError(ValueError):
    """Custom error for contract validation issues."""
    pass

class ContractIDMismatchError(ValueError):
    """Custom error raised when the ID in the path does not match the ID in the contract body."""
    pass

class DatabaseSchemaError(Exception):
    """Raised when the in-memory database structure is invalid or missing expected keys."""
    pass

class ContactTypeNotFoundError(ValueError):
    """Custom error raised when a contact type with the specified ID is not found."""
    pass

class PaymentTypeNotFoundError(Exception):
    """Exception raised when a requested payment type is not found in the database."""
    pass
  
class ProjectNotFoundError(ValueError):
    """Raised when a project with the specified external_id is not found in the database."""
    pass

class InvalidExternalIdError(ValueError):
    """Raised when the external_id parameter is invalid (empty, None, or wrong type)."""
    pass

class ProjectByExternalIdPatchError(ValueError):
    """Custom error for ProjectByExternalId patch method issues."""
    pass

class ContactNotFoundError(ValueError):
    """Custom error raised when a contact with the specified ID is not found."""
    pass

class SchemaNotFoundError(Exception):
    """Custom error for when a schema is not found in the database."""
    pass

class SupplierCompanyExternalIdInvalidError(Exception):
    """Raised when the external_id for a supplier company is invalid (empty, whitespace, or wrong type)."""

class ResourceConflictError(ValueError):
    """Custom error for resource conflicts (e.g., duplicate userName on SCIM User creation)."""
    pass
class UserValidationError(ValueError):
    """Custom error for user data validation failures."""
    pass
class UserCreationError(ValueError):
    """Custom error for user creation failures."""
    pass
class UserPatchValidationError(ValueError):
    """Custom error for user PATCH data validation failures."""
    pass
class UserPatchForbiddenError(ValueError):
    """Custom error for forbidden PATCH operations (e.g., self-deactivation, userName domain mismatch)."""
    pass
class UserPatchOperationError(ValueError):
    """Custom error for PATCH operation failures."""
    pass
class UserUpdateValidationError(ValueError):
    """Custom error for user PUT data validation failures."""
    pass
class UserUpdateForbiddenError(ValueError):
    """Custom error for forbidden PUT operations (e.g., self-deactivation, userName domain mismatch)."""
    pass
class UserUpdateConflictError(ValueError):
    """Custom error for PUT operation conflicts (e.g., duplicate userName)."""
    pass
class UserUpdateOperationError(ValueError):
    """Custom error for PUT operation failures."""
    pass
class UserDeleteForbiddenError(ValueError):
    """Custom error for forbidden DELETE operations (e.g., self-deactivation)."""
    pass
class UserDeleteOperationError(ValueError):
    """Custom error for DELETE operation failures."""
    pass

class EntriesNotFoundError(ValueError):
    """Custom error raised when report entries are missing."""
    pass

class ProjectByExternalIdValidationError(ValueError):
    """Custom error for ProjectByExternalId validation issues."""
    pass

class ProjectByExternalIdNotFoundError(ValueError):
    """Custom error raised when a project with the specified external_id is not found."""
    pass

class ProjectByExternalIdDatabaseError(ValueError):
    """Custom error for ProjectByExternalId database access and structure issues."""


class MilestoneReportNotFoundError(Exception):
    """Raised when a milestone report with the specified criteria is not found."""
    pass

class InvalidMilestoneStatusError(ValueError):
    """Raised when an invalid milestone status is provided."""
    pass


class ConflictError(Exception):
    """Raised when an action cannot be completed due to a conflict with the current state of the resource."""
    pass
