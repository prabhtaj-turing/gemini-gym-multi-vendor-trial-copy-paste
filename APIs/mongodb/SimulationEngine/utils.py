"""
MongoDB Simulation Helpers

Essential utility functions for maintaining data consistency in MongoDB simulation.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from bson import ObjectId, json_util
from mongomock import MongoClient
from .db import DB, save_state
import re
from . import custom_errors
import sys


_DB_NAME_ILLEGAL_CHARS_PATTERN = re.compile(r"[/\\\s*<>:|?]")
_COLL_NAME_ILLEGAL_CHAR_PATTERN = re.compile(r"[$]")
_COLL_NAME_RESERVED_PREFIX = "system."
MAX_SAMPLE_VALUES = 50

# --------------------------------------------------
# CORE CONSISTENCY HELPERS
# --------------------------------------------------

def log_operation(
    operation_type: str,
    database: str,
    collection: str,
    document_ids: List[ObjectId],
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Maintain audit trail in backup connection.
    
    Args:
        operation_type (str): Type of operation performed (e.g., 'insert', 'update', 'delete').
        database (str): Name of the database where operation occurred.
        collection (str): Name of the collection where operation occurred.
        document_ids (List[ObjectId]): List of ObjectIds of documents affected by the operation.
        metadata (Optional[Dict[str, Any]]): Optional additional metadata about the operation.
        
    Raises:
        KeyError: If backup connection key is invalid or doesn't exist.
    """
    original_conn = DB.current_conn
    original_db = DB.current_db

    try:
        # Switch to backup connection
        DB.switch_connection("backup_connection")
        DB.use_database("archive_db")
        
        # Insert log entry
        client = DB.connections[DB.current_conn]
        logs_collection = client[DB.current_db]["logs"]
        logs_collection.insert_one({
            "timestamp": datetime.utcnow(),
            "operation": operation_type,
            "database": database,
            "collection": collection,
            "document_ids": document_ids,
            "metadata": metadata or {}
        })
    finally:
        # Restore original connection state
        DB.switch_connection(original_conn)
        if original_db:
            DB.use_database(original_db)

def maintain_index_metadata(database: str, collection: str) -> None:
    """Sync index metadata with actual collection state
    
    Args:
        database (str): Name of the database containing the collection.
        collection (str): Name of the collection to sync index metadata for.
        
    Raises:
        KeyError: If current connection key is invalid or doesn't exist.
    """
    client = DB.connections[DB.current_conn]
    coll = client[database][collection]
    
    # Get current indexes
    indexes = [{
        "name": name,
        "key": spec['key'],
        "options": {k: v for k, v in spec.items() if k != 'key'}
    } for name, spec in coll.index_information().items()]

    # Update in-memory state
    save_state()

def validate_document_references(
    database: str,
    collection: str,
    reference_map: Dict[str, str],  # {'field_name': 'target_collection'}
    document: Dict[str, Any]
) -> None:
    """Ensure foreign key validity across collections.
    
    Args:
        database (str): Name of the database containing collections.
        collection (str): Name of the source collection (for context).
        reference_map (Dict[str, str]): Mapping of field names to target collection names (e.g., {'user_id': 'users'}).
        document (Dict[str, Any]): Document to validate references for.
        
    Raises:
        ValueError: If any referenced document does not exist in target collection.
        KeyError: If current connection key is invalid or doesn't exist.
    """
    client = DB.connections[DB.current_conn]
    db = client[database]
    
    for field, target_collection in reference_map.items():
        if field_value := document.get(field):
            if not db[target_collection].find_one({"_id": field_value}):
                raise ValueError(f"Invalid reference: {field_value} in {target_collection}")

# --------------------------------------------------
# STATISTICS HELPERS
# --------------------------------------------------

def update_collection_metrics(database: str, collection: str) -> Dict[str, Any]:
    """Calculate and store real-time collection statistics.
    
    Args:
        database (str): Name of the database containing the collection.
        collection (str): Name of the collection to calculate metrics for.
        
    Returns:
        Dict[str, Any]: Dictionary containing collection metrics with the following keys:
            - document_count (int): Total number of documents in the collection.
            - storage_size (int): Estimated storage size in bytes.
            - average_doc_size (float): Average document size in bytes.
            - index_count (int): Number of indexes on the collection.
            
    Raises:
        KeyError: If current connection key is invalid or doesn't exist.
    """
    client = DB.connections[DB.current_conn]
    coll = client[database][collection]
    
    metrics = {
        "document_count": coll.count_documents({}),
        "storage_size": len(json_util.dumps(list(coll.find({})))),
        "average_doc_size": 0,
        "index_count": len(coll.index_information())
    }
    
    if metrics['document_count'] > 0:
        metrics['average_doc_size'] = metrics['storage_size'] / metrics['document_count']

    # Store metrics in collection metadata
    coll.update_one(
        {"_id": "__metrics__"},
        {"$set": metrics},
        upsert=True
    )
    
    return metrics

# --------------------------------------------------
# SCHEMA HELPERS
# --------------------------------------------------

class SchemaValidator:
    """Maintain document structure consistency"""
    
    @staticmethod
    def enforce_required_fields(
        database: str,
        collection: str,
        document: Dict[str, Any],
        required_fields: List[str]
    ) -> None:
        """Validate mandatory document fields"""
        missing = [field for field in required_fields if field not in document]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

    @staticmethod
    def validate_field_types(
        database: str,
        collection: str,
        document: Dict[str, Any],
        field_rules: Dict[str, type]
    ) -> None:
        """Check field type compliance"""
        for field, expected_type in field_rules.items():
            if value := document.get(field):
                if not isinstance(value, expected_type):
                    raise TypeError(
                        f"Field '{field}' must be {expected_type.__name__}, "
                        f"got {type(value).__name__}"
                    )

# --------------------------------------------------
# CONNECTION HELPERS
# --------------------------------------------------

def get_active_connection() -> MongoClient:
    """Get currently active MongoDB connection.
        
    Returns:
        MongoClient: MongoClient instance representing the active connection.
        
    Raises:
        KeyError: If current connection key is invalid or doesn't exist.
    """
    return DB.connections[DB.current_conn]

def get_active_database() -> str:
    """Get name of currently selected database.
         
    Returns:
        str: String name of the currently active database, or None if no database selected.
    """
    return DB.current_db if DB.current_db else None

# --------------------------------------------------
# UTILITY HELPERS
# --------------------------------------------------

def generate_object_id() -> ObjectId:
    """Generate new BSON ObjectID.
        
    Returns:
        ObjectId: New ObjectId instance with unique identifier.
    """
    return ObjectId()

def sanitize_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare document for MongoDB insertion.
    
    Args:
        document (Dict[str, Any]): Raw document dictionary to sanitize.
        
    Returns:
        Dict[str, Any]: Sanitized document ready for MongoDB insertion with proper data types.
        
    Raises:
        TypeError: If document contains non-serializable types.
        ValueError: If document structure is invalid.
    """
    return json_util.loads(json_util.dumps(document))

def _validate_collection_name_conventions(coll_name: str) -> None:
    if '\0' in coll_name:
        raise custom_errors.InvalidNameError(
            # Align with test message:
            f"Collection name '{coll_name}' contains illegal characters."
            # Original: f"Collection name '{coll_name}' contains an illegal null character."
        )
    if _COLL_NAME_ILLEGAL_CHAR_PATTERN.search(coll_name):
        raise custom_errors.InvalidNameError(
            # Align with test message:
            f"Collection name '{coll_name}' contains illegal characters."
            # Original: f"Collection name '{coll_name}' contains an illegal character '$'."
        )
    if coll_name.startswith(_COLL_NAME_RESERVED_PREFIX) or ".system." in coll_name:
        raise custom_errors.InvalidNameError(
            # Align with test message:
            f"Collection name '{coll_name}' cannot start with 'system.' or contain '.system.'."
            # Original: f"Collection name '{coll_name}' starts with the reserved prefix '{_COLL_NAME_RESERVED_PREFIX}'."
        )
    # Note: MongoDB allows dots in collection names (not starting/ending with ., no ..)
    # If you want to enforce stricter dot rules, add checks here. For example:
    if ".." in coll_name or coll_name.startswith(".") or coll_name.endswith("."):
        if "." in coll_name: # Only raise if dots are actually used in a problematic way
            raise custom_errors.InvalidNameError(
                f"Collection name '{coll_name}' has invalid dot usage (e.g., '..' or starts/ends with '.')."
            )

def _validate_database_name_conventions(db_name: str) -> None:
    if '\0' in db_name:
        raise custom_errors.InvalidNameError(
            f"Database name '{db_name}' contains an illegal null character."
        )
    if _DB_NAME_ILLEGAL_CHARS_PATTERN.search(db_name):
        # If a specific character is found, you could mention it.
        raise custom_errors.InvalidNameError(
            # Align with test message:
            f"Database name '{db_name}' contains illegal characters."
            # Original, more detailed message:
            # f"Database name '{db_name}' contains one or more illegal characters (e.g., '/', '\\', ' ', '*', '<', '>', ':', '|', '?')."
        )
    
def _get_database_sizes(connection, database_names: List[str]) -> Dict[str, float]:
    # Estimate size using sys.getsizeof (shallow)
    database_sizes = {}
    for db_name in database_names:
        db = connection[db_name]
        all_docs = []
        for coll_name in db.list_collection_names():
            all_docs.extend(list(db[coll_name].find()))
        size = sys.getsizeof(all_docs)
        database_sizes[db_name] = size
    return database_sizes
