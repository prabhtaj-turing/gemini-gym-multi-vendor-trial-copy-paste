class InvalidQueryError(Exception):
    """Custom exception for invalid query errors."""
    pass
    
class ValidationError(Exception):
    """Custom exception for input validation errors."""
    pass

class MongoOperationError(Exception):
    """Custom exception for errors during MongoDB operations."""
    pass

class InvalidInputError(Exception):
    """If the provided connection string is malformed or invalid."""
    pass

class InvalidLogTypeError(Exception):
    """If the specified 'log_type' (e.g., global, rs, startupWarnings) is not recognized or supported."""
    pass

class LogAccessError(Exception):
    """If there's an issue retrieving logs from the server or the specified log type is unavailable."""
    pass

class ConnectionError(Exception):
    """If there is an issue communicating with the MongoDB server."""
    pass

class DatabaseNotFoundError(Exception):
    """If the specified database does not exist."""
    pass

class OperationInProgressError(Exception):
    """If the database is currently involved in an operation that prevents it from being dropped."""
    pass

class CollectionExistsError(Exception):
    """Raised if the collection already exists and the API is configured not to overwrite or re-create it."""
    pass

class InvalidNameError(Exception):
    """Raised if the provided database or collection name is invalid."""
    pass

class CollectionNotFoundError(Exception):
    """Raised if the source 'collection' does not exist in the specified 'database'."""
    pass

class TargetCollectionExistsError(Exception):
    """Raised if a collection with 'new_name' already exists and 'drop_target' is false (or not provided)."""
    pass

class IndexExistsError(Exception):
    """An index with the same name already exists, or an index with the same key specification already exists."""
    pass

class InvalidIndexSpecificationError(Exception):
    """The 'keys' argument is invalid or the provided 'name' for the index is invalid."""
    pass

class InvalidQueryError(Exception):
    """If the filter, projection, or sort criteria are malformed."""
    pass

class InvalidPipelineError(Exception):
    """If the aggregation pipeline is malformed or contains invalid stages/operators."""
    pass

class AggregationError(Exception):
    """If an error occurs during the aggregation process."""
    pass

class BulkWriteError(Exception):
    """If one or more documents failed to insert due to issues like duplicate key errors."""
    pass

class InvalidDocumentError(Exception):
    """If any of the documents in the input list are structurally invalid or contain data that cannot be serialized to BSON."""
    pass

class InvalidUpdateError(Exception):
    """If the 'update' document is malformed, empty, or does not contain valid update operators."""
    pass

class InvalidOperationError(Exception):
    """If the 'method' to be explained is invalid, malformed, or not explainable."""
    pass

class RenameToSameNameError(Exception):
    """Raised if 'new_name' is the same as the source 'collection' name."""
    pass

class ApiError(Exception):
    """Generic base class for API-related errors or a specific error if the API interaction fails unexpectedly."""
    pass

class RenameToSameNameError(Exception):
    """Raised if 'new_name' is the same as the source 'collection' name."""
    pass
