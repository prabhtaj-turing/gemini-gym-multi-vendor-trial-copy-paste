from common_utils.tool_spec_decorator import tool_spec
from common_utils.print_log import print_log
import json
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from bson import json_util 

from .SimulationEngine import custom_errors
from .SimulationEngine import utils
from .SimulationEngine import models
from .SimulationEngine.db import DB  # Direct import of your MongoDB instance

from pydantic import ValidationError as PydanticValidationError
import pymongo.errors
import re

from .SimulationEngine import utils, custom_errors, models
from .SimulationEngine.models import IndexTypeEnum, CollectionIndexesInput, CollectionIndexDetail, CreateCollectionInput, RenameCollectionInput, CollectionSchemaInput
from .SimulationEngine.db import DB  # Direct import of your MongoDB instance
from .SimulationEngine.utils import MAX_SAMPLE_VALUES
from pymongo_schema.extract import extract_pymongo_client_schema

@tool_spec(
    spec={
        'name': 'create_index',
        'description': """ Create an index for a collection.
        
        This function creates an index for a specified collection within a given database.
        It uses the provided 'database' and 'collection' names, and an index
        definition specified by 'keys'. An optional 'name' can be given to the index. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'database': {
                    'type': 'string',
                    'description': 'Database name.'
                },
                'collection': {
                    'type': 'string',
                    'description': 'Collection name.'
                },
                'keys': {
                    'type': 'object',
                    'description': """ The index definition. Each key is a field name (str) and 
                    each value must be an integer representing the index direction: 1 for ascending, 
                    -1 for descending. """,
                    'properties': {},
                    'required': []
                },
                'name': {
                    'type': 'string',
                    'description': 'The name of the index. Defaults to None.'
                }
            },
            'required': [
                'database',
                'collection',
                'keys'
            ]
        }
    }
)
def create_index(database: str, collection: str, keys: Dict[str, int], name: Optional[str] = None) -> Dict[str, Union[str, None]]:
    """Create an index for a collection.

    This function creates an index for a specified collection within a given database.
    It uses the provided 'database' and 'collection' names, and an index
    definition specified by 'keys'. An optional 'name' can be given to the index.

    Args:
        database (str): Database name.
        collection (str): Collection name.
        keys (Dict[str, int]): The index definition. Each key is a field name (str) and 
            each value must be an integer representing the index direction: 1 for ascending, 
            -1 for descending.
        name (Optional[str]): The name of the index. Defaults to None.

    Returns:
        Dict[str, Union[str, None]]: A dictionary detailing the result of the index creation operation.
        It includes the following keys:
            name (str): The system-generated or user-provided name of the index.
            status_message (Optional[str]): A message indicating the outcome, such as
                'index created successfully', or details if the index already
                existed (e.g., 'index with this name/specification already
                exists, no action taken').

    Raises:
        IndexExistsError: An index with the same name already exists, or an index with the
            same key specification already exists and database options prevent
            creating a duplicate or differently named index with the same
            specification.
        InvalidIndexSpecificationError: The 'keys' argument is invalid (e.g., empty,
            malformed, references non-existent fields, or uses unsupported
            index types) or the provided 'name' for the index is invalid
            (e.g., empty, too long, contains illegal characters).
        ValidationError: If input arguments fail validation.
    """
    try:
        # Validate basic input structure using Pydantic model
        models.CreateIndexInput(
            database=database,
            collection=collection,
            keys=keys,
            name=name
        )
    except PydanticValidationError as e:
        # Check if the error is related to keys values not being integers
        if "keys" in str(e) and any("int" in str(field_error) for field_error in e.errors()):
            # Extract the specific field and value that caused the error
            for error in e.errors():
                if "keys" in error["loc"] and len(error["loc"]) > 1:
                    field_name = error["loc"][1]
                    if field_name in keys:
                        invalid_value = keys[field_name]
                        valid_index_type_values = [member.value for member in IndexTypeEnum]
                        raise custom_errors.InvalidIndexSpecificationError(
                            f"Invalid index type '{invalid_value}' for field '{field_name}'. "
                            f"Supported integer values are: {valid_index_type_values} (e.g., {IndexTypeEnum.ASCENDING.value} for ascending, {IndexTypeEnum.DESCENDING.value} for descending)."
                        )
        raise custom_errors.ValidationError("Input validation failed")

    # Specific validation for 'keys' content
    if not keys:
        raise custom_errors.InvalidIndexSpecificationError("Index 'keys' definition cannot be empty.")

    # Get valid integer values from IndexTypeEnum
    valid_index_type_values = [member.value for member in IndexTypeEnum]

    for key_field, key_type_value in keys.items():
        if not isinstance(key_field, str) or not key_field.strip():
            raise custom_errors.InvalidIndexSpecificationError("Index field names must be non-empty strings.")
        
        # Validate key_type_value against the integer values of IndexTypeEnum
        if not isinstance(key_type_value, int) or key_type_value not in valid_index_type_values:
            raise custom_errors.InvalidIndexSpecificationError(
                f"Invalid index type '{key_type_value}' for field '{key_field}'. "
                f"Supported integer values are: {valid_index_type_values} (e.g., {IndexTypeEnum.ASCENDING.value} for ascending, {IndexTypeEnum.DESCENDING.value} for descending)."
            )

    # Specific validation for 'name' content
    if name: 
        if not isinstance(name, str): 
             raise custom_errors.ValidationError("Index 'name' must be a string if provided.")
        if '$' in name:
            raise custom_errors.InvalidIndexSpecificationError("Index name cannot contain '$' character.")
        if name == "_id_":
            raise custom_errors.InvalidIndexSpecificationError(
                "The index name '_id_' is reserved and cannot be used for a user-defined index."
            )

    client = utils.get_active_connection()
    
    db_obj = client[database]
    
    collection_obj = db_obj[collection]
    index_key_list_to_create: List[Tuple[str, Any]] = list(keys.items())

    existing_indexes = collection_obj.index_information()
    for existing_idx_name, idx_info in existing_indexes.items():
        existing_key_spec: List[Tuple[str, Any]] = idx_info.get('key', [])

        if name and name == existing_idx_name:
            if sorted(index_key_list_to_create) == sorted(existing_key_spec): 
                utils.maintain_index_metadata(database, collection)
                response_model = models.IndexCreationResult(
                    name=name,
                    status_message="index with this name and specification already exists, no action taken"
                )
                return response_model.model_dump(exclude_none=True)
            else:
                raise custom_errors.IndexExistsError(
                    f"An index with name '{name}' already exists but with a different key specification: {existing_key_spec}."
                )

        if sorted(index_key_list_to_create) == sorted(existing_key_spec):
            utils.maintain_index_metadata(database, collection)
            response_model = models.IndexCreationResult(
                name=existing_idx_name,
                status_message=f"index with this specification already exists (name: '{existing_idx_name}'), no action taken"
            )
            return response_model.model_dump(exclude_none=True)

    create_kwargs = {}
    if name: 
        create_kwargs['name'] = name
    
    created_index_name = collection_obj.create_index(index_key_list_to_create, **create_kwargs)
    utils.maintain_index_metadata(database, collection)

    response_model = models.IndexCreationResult(
        name=created_index_name, # This correctly uses the name returned by the driver
        status_message="index created successfully"
    )
    return response_model.model_dump(exclude_none=True)

@tool_spec(
    spec={
        'name': 'collection_indexes',
        'description': """ Describe the indexes for a collection.
        
        This function describes the indexes for a specified collection. It provides
        details for each index associated with the collection, such as its version,
        the fields it indexes along with their sort order, its unique name, and
        its namespace (typically 'database_name.collection_name'). """,
        'parameters': {
            'type': 'object',
            'properties': {
                'database': {
                    'type': 'string',
                    'description': 'Database name.'
                },
                'collection': {
                    'type': 'string',
                    'description': 'Collection name.'
                }
            },
            'required': [
                'database',
                'collection'
            ]
        }
    }
)
def collection_indexes(database: str, collection: str) -> Dict[str, Any]:
    """Describe the indexes for a collection.

    This function describes the indexes for a specified collection. It provides
    details for each index associated with the collection, such as its version,
    the fields it indexes along with their sort order, its unique name, and
    its namespace (typically 'database_name.collection_name').

    Args:
        database (str): Database name.
        collection (str): Collection name.

    Returns:
        Dict[str, Any]: A dictionary with a single key 'content', which maps to a list of dictionaries.
            The first dictionary in the list contains:
                text (str): A message formatted as "Found {index_count} indexes in the collection \"{collection_name}\":",
                            where {index_count} is the number of indexes found and {collection_name} is the name of the collection.
                type (str): The type of content, which is "text".
            The subsequent dictionaries in the list are generated for each index and contain:
                text (str): A message formatted as "Name \"{index_name}\", definition: {index_key_definition}",
                            where {index_name} is the name of the index and {index_key_definition} is the key definition as a string.
                type (str): The type of content, which is "text".
            This structure provides a detailed textual description of the indexes in the collection.

    Raises:
        InvalidInputError: If input arguments fail validation.
    """
    # Input validation using the CollectionIndexesInput Pydantic model
    try:
        CollectionIndexesInput(database=database, collection=collection)
    except PydanticValidationError:
        raise custom_errors.InvalidInputError("Input validation failed")

    client = utils.get_active_connection()

    db_obj = client[database]

    coll_obj = db_obj[collection]

    # Retrieve index information
    indexes = coll_obj.index_information()

    content = [
        {
            "text": f'Found {len(indexes)} indexes in the collection "{collection}":',
            "type": "text",
        }
    ]

    for index_name, index_data in indexes.items():
        key_definition = index_data["key"]
        content.append({
            "text": f'Name "{index_name}", definition: {key_definition}',
            "type": "text",
        })

    return {"content": content}

@tool_spec(
    spec={
        'name': 'create_collection',
        'description': """ Creates a new collection in a database.
        
        This function creates a new collection within the specified database. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'database': {
                    'type': 'string',
                    'description': 'Database name.'
                },
                'collection': {
                    'type': 'string',
                    'description': 'Collection name.'
                }
            },
            'required': [
                'database',
                'collection'
            ]
        }
    }
)
def create_collection(database: str, collection: str) -> Dict[str, str]:
    """Creates a new collection in a database.

    This function creates a new collection within the specified database.

    Args:
        database (str): Database name.
        collection (str): Collection name.

    Returns:
        Dict[str, str]: A dictionary indicating the successful outcome of the collection creation. This dictionary contains the following keys:
            status (str): Always 'success' when the function returns normally.
            message (str): A descriptive message indicating successful creation, e.g., 'Collection created successfully'.

    Raises:
        CollectionExistsError: Raised if the collection already exists.
        InvalidNameError: Raised if the provided database or collection name is invalid. This can be due to issues such as containing illegal characters, exceeding length limits, or violating naming conventions specific to the database system.
        DatabaseNotFoundError: Raised if the database cannot be accessed or created due to connection issues, permissions, or other database-level problems.
        ApiError: Raised for database operation failures or driver errors that are not covered by more specific exceptions.
        PydanticValidationError: If input arguments fail validation.
    """
    # Step 1: Input validation
    try:
        validated_input = CreateCollectionInput(
            database=database, collection=collection
        )
        db_name = validated_input.database
        coll_name = validated_input.collection
    except PydanticValidationError as e:
        raise e

    # Step 2: MongoDB naming convention validation
    utils._validate_database_name_conventions(db_name)
    utils._validate_collection_name_conventions(coll_name)

    # Step 3: Ensure active connection and create collection
    if not DB.current_conn:
        DB.switch_connection()

    client = DB.connections[DB.current_conn]

    try:
        db_instance = client[db_name]
        db_instance.create_collection(coll_name)
        return {"status": "success", "message": "Collection created successfully"}
    except pymongo.errors.CollectionInvalid as e:
        # Handle existing collections and invalid names
        error_msg_lower = str(e).lower()
        if "already exists" in error_msg_lower:
            raise custom_errors.CollectionExistsError(
                f"Collection '{db_name}.{coll_name}' already exists."
            )
        else:
            raise custom_errors.InvalidNameError(
                f"Collection name '{coll_name}' is invalid."
            )
    except pymongo.errors.OperationFailure as e:
        # Handle database operation failures
        error_message_lower = str(e).lower()
        if any(
            keyword in error_message_lower
            for keyword in [
                "invalid ns",
                "invalid collection name",
                "invalid database name",
            ]
        ):
            raise custom_errors.InvalidNameError(f"Invalid name: {e}")
        # Check for database access issues
        if (
            "database not found" in error_message_lower
            or "database does not exist" in error_message_lower
        ):
            raise custom_errors.DatabaseNotFoundError(
                f"Database '{db_name}' not found or cannot be accessed: {e}"
            )
        raise custom_errors.ApiError(f"Database operation failed: {e}")
    except pymongo.errors.PyMongoError as e:
        # Handle other MongoDB driver errors
        error_message_lower = str(e).lower()
        if (
            "database not found" in error_message_lower
            or "database does not exist" in error_message_lower
        ):
            raise custom_errors.DatabaseNotFoundError(
                f"Database '{db_name}' not found or cannot be accessed: {e}"
            )
        raise custom_errors.ApiError(f"Database driver error: {e}")


@tool_spec(
    spec={
        'name': 'rename_collection',
        'description': """ Renames a collection in a MongoDB database.
        
        This function changes the name of an existing collection within a specified database to a new name.
        If a collection with the `newName` already exists, the behavior is controlled by the `dropTarget`
        parameter: if `dropTarget` is true, the existing target collection is dropped before the rename;
        otherwise, if the target collection exists and `dropTarget` is false, an error is raised. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'database': {
                    'type': 'string',
                    'description': 'Database name.'
                },
                'collection': {
                    'type': 'string',
                    'description': 'Collection name.'
                },
                'newName': {
                    'type': 'string',
                    'description': 'The new name for the collection.'
                },
                'dropTarget': {
                    'type': 'boolean',
                    'description': 'If true, drops the target collection if it exists. Defaults to False.'
                }
            },
            'required': [
                'database',
                'collection',
                'newName'
            ]
        }
    }
)
def rename_collection(
    database: str, collection: str, newName: str, dropTarget: bool = False
) -> Dict[str, Any]:
    """Renames a collection in a MongoDB database.

    This function changes the name of an existing collection within a specified database to a new name.
    If a collection with the `newName` already exists, the behavior is controlled by the `dropTarget`
    parameter: if `dropTarget` is true, the existing target collection is dropped before the rename;
    otherwise, if the target collection exists and `dropTarget` is false, an error is raised.

    Args:
        database (str): Database name.
        collection (str): Collection name.
        newName (str): The new name for the collection.
        dropTarget (bool): If true, drops the target collection if it exists. Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary indicating the successful outcome of the rename operation. This dictionary contains the following keys:
            status (str): Always 'success' when the function returns normally.
            message (str): A descriptive message indicating successful rename, e.g., 'Collection renamed successfully'.

    Raises:
        DatabaseNotFoundError: Raised if the specified 'database' does not exist.
        CollectionNotFoundError: Raised if the source 'collection' does not exist in the specified 'database'.
        TargetCollectionExistsError: Raised if a collection with 'new_name' already exists and 'drop_target' is false (or not provided).
        RenameToSameNameError: Raised if 'new_name' is the same as the source 'collection' name.
        InvalidNameError: Raised if 'new_name' is an invalid collection name according to MongoDB naming conventions.
        ApiError: Raised for database operation failures or driver errors that are not covered by more specific exceptions.
        PydanticValidationError: If input arguments fail validation.
    """
    try:
        # Prepare data for Pydantic validation, mapping function arguments to Pydantic model field names.
        # The Pydantic model `RenameCollectionInput` uses `new_name` and `drop_target`.
        input_data_for_validation = {
            "database": database,
            "collection": collection,
            "new_name": newName,  # Maps `newName` (arg) to `new_name` (Pydantic field)
            "drop_target": dropTarget,  # Maps `dropTarget` (arg) to `drop_target` (Pydantic field)
        }
        # Validate input arguments using the Pydantic model.
        validated_args = RenameCollectionInput(**input_data_for_validation)
    except PydanticValidationError as e:
        # Convert Pydantic's detailed errors into a user-friendly message string.
        raise e

    # Use validated arguments from this point onwards.
    db_name_val = validated_args.database
    source_collection_name_val = validated_args.collection
    new_collection_name_val = (
        validated_args.new_name
    )  # This is `newName` after Pydantic validation/coercion
    should_drop_target_val = validated_args.drop_target

    # Perform additional MongoDB-specific validation for the new collection name.
    utils._validate_collection_name_conventions(new_collection_name_val)

    client = utils.get_active_connection()

    # Check if the specified database exists.
    if db_name_val not in client.list_database_names():
        raise custom_errors.DatabaseNotFoundError(
            f"Database '{db_name_val}' not found."
        )

    db_obj = client[db_name_val]

    # Check if the source collection exists in the database.
    if source_collection_name_val not in db_obj.list_collection_names():
        raise custom_errors.CollectionNotFoundError(
            f"Source collection '{source_collection_name_val}' not found in database '{db_name_val}'."
        )

    # If the new name is identical to the old name, MongoDB treats this as an invalid operation.
    if source_collection_name_val == new_collection_name_val:
        raise custom_errors.RenameToSameNameError(
            f"Source collection '{source_collection_name_val}' is identical to the new name '{new_collection_name_val}'. No rename operation was performed."
        )

    # Check if a collection with the new name already exists.
    target_collection_exists = new_collection_name_val in db_obj.list_collection_names()

    if target_collection_exists and not should_drop_target_val:
        raise custom_errors.TargetCollectionExistsError(
            f"Target collection '{new_collection_name_val}' already exists in database '{db_name_val}', and 'dropTarget' is false."
        )

    source_collection_obj = db_obj[source_collection_name_val]

    try:
        # Perform the rename operation.
        # The `dropTarget` kwarg is passed to the underlying MongoDB command.
        source_collection_obj.rename(
            new_collection_name_val, dropTarget=should_drop_target_val
        )

        return {
            "status": "success",
            "message": f"Collection '{source_collection_name_val}' was successfully renamed to '{new_collection_name_val}' in database '{db_name_val}'.",
        }
    except pymongo.errors.OperationFailure as e:
        # Handle database operation failures
        raise custom_errors.ApiError(
            f"Database operation failed while renaming collection '{source_collection_name_val}' to '{new_collection_name_val}': {e}"
        )
    except pymongo.errors.PyMongoError as e:
        # Handle other MongoDB driver errors
        raise custom_errors.ApiError(
            f"Database driver error occurred while renaming collection '{source_collection_name_val}' to '{new_collection_name_val}': {e}"
        )
    except Exception as e:
        # Handle any other unexpected errors
        raise custom_errors.ApiError(
            f"An unexpected error occurred while renaming collection '{source_collection_name_val}' to '{new_collection_name_val}': {e}"
        )
    


@tool_spec(
    spec={
        'name': 'collection_schema',
        'description': """ Describe the schema for a collection.
        
        This function describes the schema for a collection. It provides an analysis
        of the collection's schema, which is typically derived by sampling
        documents within that collection. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'database': {
                    'type': 'string',
                    'description': 'Database name.'
                },
                'collection': {
                    'type': 'string',
                    'description': 'Collection name.'
                }
            },
            'required': [
                'database',
                'collection'
            ]
        }
    }
)
def collection_schema(database: str, collection: str) -> Dict[str, Any]:
    """Describe the schema for a collection.

    This function describes the schema for a collection. It provides an analysis
    of the collection's schema, which is typically derived by sampling
    documents within that collection.

    Args:
        database (str): Database name.
        collection (str): Collection name.

    Returns:
        Dict[str, Any]: An analysis of the collection's schema, derived from
            sampling documents. This dictionary contains the following keys:

            fields (Dict[str, Any]): A dictionary where each key is a field name
                found in the sampled documents, and the value is another dictionary
                describing that field's schema. This inner dictionary (field schema)
                typically contains:
                
                count (int): The number of times this field was encountered in the
                    sampled documents.
                type (str): The most frequently observed BSON type for this field
                    (e.g., 'string', 'integer', 'oid', 'object', 'array', 'null').
                    Note: Type names might be lowercase or specific to the
                    underlying schema analysis library (e.g., 'oid' for ObjectId,
                    'object' for Document, 'array' for Array).
                types_count (Dict[str, int]): A dictionary mapping each observed
                    BSON type name (for this field) to the number of times it occurred.
                    Example: `{'string': 10, 'null': 2}`.
                prop_in_object (float): The probability (0.0 to 1.0) that this field
                    exists in a document, based on the sample.
                
                object (Optional[Dict[str, Any]]): If the field's dominant `type`
                    is 'object' (representing a BSON Document), this key will be
                    present and its value will be another dictionary structured
                    identically to this 'fields' dictionary, recursively describing
                    the schema of the sub-document. Absent if not a document type or
                    if the document type had no discernible sub-fields.
                
                array_types_count (Optional[Dict[str, int]]): If the field's dominant
                    `type` is 'array', this key may be present. Its value is a
                    dictionary mapping BSON type names found within the array elements
                    to their respective counts across all sampled arrays for this field.
                    Example: `{'string': 50, 'integer': 10}`.
                array_type (Optional[str]): If the field's dominant `type` is 'array',
                    this key may indicate the most frequent BSON type of the elements
                    within the arrays.

            num_documents_sampled (int): The total number of documents that were
                actually analyzed from the collection to generate this schema. This
                might be less than the collection's total document count if sampling
                was used (e.g., limited by MAX_SAMPLE_VALUES).

    Raises:
        DatabaseNotFoundError: If the specified database does not exist.
        CollectionNotFoundError: If the specified collection does not exist within the database.
        PydanticValidationError: If input arguments fail validation.
    """
    try:
        CollectionSchemaInput(database=database, collection=collection)
    except PydanticValidationError as e:
        raise e

    if not DB.current_conn or DB.current_conn not in DB.connections:
        raise custom_errors.ApiError("No active MongoDB connection. Please connect first.")
    
    client = DB.connections[DB.current_conn]

    if database in client.list_database_names():
        db_obj = client[database]
    else:
        raise custom_errors.DatabaseNotFoundError(f"Database name '{database}' is invalid or could not be accessed")

    if collection not in db_obj.list_collection_names():
        raise custom_errors.CollectionNotFoundError(
            f"Collection '{collection}' not found in database '{database}'."
        )

    collection_obj = db_obj[collection]
    
    analyzed_fields = extract_pymongo_client_schema(client, database_names=database, collection_names=collection, sample_size=MAX_SAMPLE_VALUES)[database][collection]

    return {
        "fields": analyzed_fields['object'],
        "num_documents_sampled": analyzed_fields['count'],
    }

@tool_spec(
    spec={
        'name': 'drop_collection',
        'description': """ Removes a collection or view from the database.
        
        This function removes a collection or view from the database. The method also removes any indexes associated with the dropped collection. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'database': {
                    'type': 'string',
                    'description': 'Database name.'
                },
                'collection': {
                    'type': 'string',
                    'description': 'Collection name.'
                }
            },
            'required': [
                'database',
                'collection'
            ]
        }
    }
)
def drop_collection(database: str, collection: str) -> Dict[str, str]:
    """Removes a collection or view from the database.

    This function removes a collection or view from the database. The method also removes any indexes associated with the dropped collection.

    Args:
        database (str): Database name.
        collection (str): Collection name.

    Returns:
        Dict[str, str]: A dictionary detailing the outcome of the drop collection operation, containing the following keys:
            status (str): The operational status, e.g., 'success' or 'failure'.
            message (Optional[str]): A descriptive message about the operation's result, e.g., 'Collection dropped successfully' or 'Collection not found'.

    Raises:
        PydanticValidationError: If input arguments fail validation.
        InvalidNameError: Raised if the provided database or collection name is invalid according to MongoDB naming conventions.
        DatabaseNotFoundError: Raised if the specified database does not exist.
        ApiError: Raised for unexpected errors during the drop operation, such as database connection issues or other operational failures.
    """
    try:
        # Step 1: Pydantic Validation
        # This validates type, non-null, and length constraints (min_length=1, max_length)
        validated_input = models.DropCollectionInput(
            database=database, collection=collection
        )
        db_name = validated_input.database
        coll_name = validated_input.collection
    except PydanticValidationError as e:
        raise e

    # Step 2: MongoDB-specific naming convention validation
    # This provides additional validation beyond Pydantic's basic constraints
    utils._validate_database_name_conventions(db_name)
    utils._validate_collection_name_conventions(coll_name)

    client = utils.get_active_connection()

    # Step 3: Check if the database exists
    if db_name not in client.list_database_names():
        raise custom_errors.DatabaseNotFoundError(f"Database '{db_name}' not found.")

    db_obj = client[db_name]

    # Verify that the specified collection exists within the database, even if it is absent the operation executes successfully
    if coll_name not in db_obj.list_collection_names():
        return {"status": "success", "message": "Collection not found."}

    try:
        # Perform the drop collection operation
        db_obj.drop_collection(coll_name)

        return {
            "status": "success",
            "message": "Collection dropped successfully.",  # Docstring example message
        }
    except Exception as e:
        # Handle unexpected errors during the drop operation, logging, or state saving
        # It's advisable to log the specific exception `e` for internal diagnostics.
        raise custom_errors.ApiError(
            f"An error occurred during the drop operation: {str(e)}"
        )

@tool_spec(
    spec={
        'name': 'collection_storage_size',
        'description': """ Gets the size of the collection.
        
        This function retrieves detailed storage statistics for a specified collection within a database.
        It provides comprehensive information about the collection's storage utilization including
        document counts, sizes, and index information. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'database': {
                    'type': 'string',
                    'description': 'Database name.'
                },
                'collection': {
                    'type': 'string',
                    'description': 'Collection name.'
                }
            },
            'required': [
                'database',
                'collection'
            ]
        }
    }
)
def collection_storage_size(database: str, collection: str) -> Dict[str, Any]:
    """Gets the size of the collection.

    This function retrieves detailed storage statistics for a specified collection within a database.
    It provides comprehensive information about the collection's storage utilization including
    document counts, sizes, and index information.

    Args:
        database (str): Database name.
        collection (str): Collection name.

    Returns:
        Dict[str, Any]: A dictionary containing information about the collection's storage utilization, with the following keys:
            ns (str): The namespace of the collection.
            size (float): The total uncompressed size of the data in the collection in bytes.
            count (int): The number of documents in the collection.
            storage_size (float): The total amount of storage space allocated to this collection for document storage, including free space, in bytes.
            avg_obj_size (float): The average size of an object in the collection in bytes.
            num_indexes (int): The number of indexes on the collection.
            total_index_size (float): The total size of all indexes on the collection in bytes.
            scale_factor (Optional[float]): The scale factor used to calculate storage sizes, if applicable.

    Raises:
        DatabaseNotFoundError: If the specified database does not exist.
        CollectionNotFoundError: If the specified collection does not exist.
        InvalidNameError: If the database or collection name violates MongoDB naming conventions.
        ApiError: If there's an error during database operations or size calculations.
        PydanticValidationError: If input arguments fail validation.
    """
    # Step 1: Validate input arguments using Pydantic model
    try:
        input_data = {"database": database, "collection": collection}
        models.CollectionStorageSizeInput(**input_data)
    except PydanticValidationError as e:
        raise e

    # Step 2: Validate MongoDB naming conventions
    utils._validate_database_name_conventions(database)
    utils._validate_collection_name_conventions(collection)

    # Step 3: Ensure active connection
    if not DB.current_conn:
        DB.switch_connection()

    client = DB.connections.get(DB.current_conn)
    if not client:
        raise custom_errors.ApiError(
            f"No active MongoDB client found for connection '{DB.current_conn}'."
        )

    # Step 4: Check if database exists
    if database not in client.list_database_names():
        raise custom_errors.DatabaseNotFoundError(
            f"Database '{database}' not found on connection '{DB.current_conn}'."
        )

    db_obj = client[database]

    # Step 5: Check if collection exists
    if collection not in db_obj.list_collection_names():
        raise custom_errors.CollectionNotFoundError(
            f"Collection '{collection}' not found in database '{database}' on connection '{DB.current_conn}'."
        )

    coll_obj = db_obj[collection]

    try:
        # Step 6: Calculate collection statistics
        result_ns: str = f"{database}.{collection}"

        # Use count_documents for better performance instead of loading all documents
        result_count: int = coll_obj.count_documents({})

        # Calculate size more efficiently by sampling documents if collection is large
        result_size: float = 0.0
        result_avg_obj_size: float = 0.0

        if result_count > 0:
            # For small collections, calculate exact size
            if result_count <= 1000:
                documents = list(coll_obj.find({}))
                try:
                    serializable_documents = json.loads(json_util.dumps(documents))
                    result_size = float(len(json.dumps(serializable_documents)))
                except Exception as e:
                    raise custom_errors.ApiError(
                        f"Error serializing documents for size calculation: {str(e)}"
                    )
            else:
                # For large collections, estimate size by sampling
                sample_size = min(100, result_count)
                sample_documents = list(coll_obj.find({}).limit(sample_size))
                try:
                    serializable_sample = json.loads(json_util.dumps(sample_documents))
                    sample_size_bytes = len(json.dumps(serializable_sample))
                    result_size = (sample_size_bytes / sample_size) * result_count
                except Exception as e:
                    raise custom_errors.ApiError(
                        f"Error calculating estimated size from sample: {str(e)}"
                    )

            result_avg_obj_size = result_size / result_count

        # Storage size is typically the same as data size in simulation
        result_storage_size: float = result_size

        # Get index information
        index_info = coll_obj.index_information()
        result_num_indexes: int = len(index_info) if index_info else 0

        # Calculate total index size more accurately
        result_total_index_size: float = 0.0
        if index_info:
            try:
                for idx_name, idx_details in index_info.items():
                    # Estimate index size based on index definition
                    idx_definition = json.dumps(idx_details, default=json_util.default)
                    # Rough estimation: index size is typically proportional to document count
                    estimated_idx_size = len(idx_definition) * (
                        result_count / 100
                    )  # Rough approximation
                    result_total_index_size += estimated_idx_size
            except Exception as e:
                # If index size calculation fails, continue with 0.0
                result_total_index_size = 0.0

        # Scale factor is typically 1.0 when sizes are in bytes
        result_scale_factor: Optional[float] = 1.0

        # Step 7: Create and return response
        response_model = models.CollectionStorageStatsOutput(
            ns=result_ns,
            size=result_size,
            count=result_count,
            storage_size=result_storage_size,
            avg_obj_size=result_avg_obj_size,
            num_indexes=result_num_indexes,
            total_index_size=result_total_index_size,
            scale_factor=result_scale_factor,
        )
        return response_model.model_dump(exclude_none=True)

    except pymongo.errors.OperationFailure as e:
        raise custom_errors.ApiError(
            f"Database operation failed while calculating storage statistics for collection '{collection}' in database '{database}': {str(e)}"
        )
    except pymongo.errors.PyMongoError as e:
        raise custom_errors.ApiError(
            f"Database driver error occurred while calculating storage statistics for collection '{collection}' in database '{database}': {str(e)}"
        )
    except Exception as e:
        raise custom_errors.ApiError(
            f"An unexpected error occurred while calculating storage statistics for collection '{collection}' in database '{database}': {str(e)}"
        )

@tool_spec(
    spec={
        'name': 'list_collections',
        'description': """ List all collections for a given database.
        
        This function lists all collections for a given database. Collection names
        are expected to be strings. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'database': {
                    'type': 'string',
                    'description': 'Database name.'
                }
            },
            'required': [
                'database'
            ]
        }
    }
)
def list_collections(database: str) -> List[str]:
    """List all collections for a given database.

    This function lists all collections for a given database. Collection names
    are expected to be strings.

    Args:
        database (str): Database name.

    Returns:
        List[str]: A list of collection names in the specified database.
                   Returns an empty list if the database exists but has no collections.

    Raises:
        DatabaseNotFoundError: If the specified database does not exist on the connection.
        InvalidNameError: If the database name violates MongoDB naming conventions.
        ValidationError: If input arguments fail validation.
        MongoOperationError: If there's an issue accessing DB connection or client.
        ApiError: If there's an error during database operations.
        PydanticValidationError: If input arguments fail validation.
    """
    # Step 1: Validate input arguments using Pydantic model
    try:
        models.ListCollectionsInput(database=database)
    except PydanticValidationError as e:
        # Convert PydanticValidationError to ValidationError for backward compatibility
        if "String should have at least 1 character" in str(e):
            raise custom_errors.ValidationError(
                "Input 'database' cannot be an empty string."
            )
        elif "Input should be a valid string" in str(e):
            raise custom_errors.ValidationError("Input 'database' must be a string.")
        else:
            raise e

    # Step 2: Validate MongoDB naming conventions
    utils._validate_database_name_conventions(database)

    # Step 3: Ensure active connection
    if not DB.current_conn:
        DB.switch_connection()

    client = DB.connections.get(DB.current_conn)
    if not client:
        raise custom_errors.MongoOperationError(
            f"No active MongoDB client found for connection '{DB.current_conn}'."
        )

    try:
        # Step 4: Check if database exists
        database_names_on_client = client.list_database_names()
        if database not in database_names_on_client:
            raise custom_errors.DatabaseNotFoundError(
                f"Database '{database}' not found on connection '{DB.current_conn}'."
            )

        # Step 5: Retrieve collection names
        db_obj = client[database]
        collection_names = db_obj.list_collection_names()

        return collection_names

    except custom_errors.DatabaseNotFoundError:
        # Re-raise DatabaseNotFoundError without wrapping
        raise
    except pymongo.errors.OperationFailure as e:
        raise custom_errors.ApiError(
            f"Database operation failed while listing collections for database '{database}': {str(e)}"
        )
    except pymongo.errors.PyMongoError as e:
        raise custom_errors.ApiError(
            f"Database driver error occurred while listing collections for database '{database}': {str(e)}"
        )
    except Exception as e:
        raise custom_errors.ApiError(
            f"An unexpected error occurred while listing collections for database '{database}': {str(e)}"
        )
