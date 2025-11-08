class BucketError(Exception):
    """Base class for bucket-related errors."""
    pass

class MissingGenerationError(BucketError):
    """Custom error for when generation is required but not provided."""
    pass

class InvalidProjectionValueError(BucketError):
    """Custom error for invalid projection values."""
    pass

class BucketNotFoundError(BucketError):
    """Raised when a specified bucket is not found."""
    pass

class MetagenerationMismatchError(BucketError):
    """Raised when a metageneration condition is not met."""
    pass

class NotSoftDeletedError(BucketError):
    """Raised when an operation requires a bucket to be soft-deleted, but it is not."""
    pass

class SoftDeleteRetentionActiveError(BucketError):
    """Raised when a soft delete operation is done on a bucket that has a soft delete retention period active."""
    pass

class GenerationMismatchError(BucketError):
    """Raised when a generation condition for a soft-deleted bucket is not met."""

class BucketNotEmptyError(BucketError):
    """Raised when attempting to delete a non-empty bucket."""
    pass

class InvalidPredefinedAclValueError(BucketError):
    """Raised when the 'predefinedAcl' parameter contains a value outside the allowed set (e.g., 'private', 'publicRead')."""
    pass

class InvalidPredefinedDefaultObjectAclValueError(BucketError):
    """Raised when the 'predefined_default_object_acl' parameter contains a value outside the allowed set (e.g., 'bucketOwnerRead', 'authenticatedRead')."""
    pass