from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any, Optional, Union
from bson import ObjectId, json_util
from pydantic import ValidationError as PydanticValidationError
from pymongo.errors import (
    BulkWriteError as PyMongoBulkWriteError,
    InvalidOperation,
    OperationFailure,  # Will be re-raised for all unmapped OperationFailures
    AutoReconnect,
    WriteError,
)
from pymongo.results import UpdateResult, InsertManyResult

# Correct imports based on the problem description
from .SimulationEngine import utils
from .SimulationEngine.custom_errors import (
    AggregationError,
    DatabaseNotFoundError,
    CollectionNotFoundError,
    InvalidPipelineError,
    InvalidQueryError,
    InvalidUpdateError,
    # InvalidNameError, # Removed, OperationFailure will be used
    BulkWriteError,  # Only for PyMongoBulkWriteError now
    InvalidDocumentError,
)
from .SimulationEngine.models import (
    AggregateInput,
    DeleteManyInput,
    FindInput,
    UpdateManyInput,
    CountInput,
    InsertManyInput,
)


@tool_spec(
    spec={
        'name': 'aggregate',
        'description': """ Run an aggregation against a MongoDB collection.
        
        This function runs an aggregation against a specified MongoDB collection within a given database.
        It executes an array of aggregation pipeline stages provided as input and returns the
        results of this aggregation. """,
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
                'pipeline': {
                    'type': 'array',
                    'description': 'An array of aggregation stages to execute.',
                    'items': {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                }
            },
            'required': [
                'database',
                'collection',
                'pipeline'
            ]
        }
    }
)
def aggregate(database: str, collection: str, pipeline: List[Dict[str, Union[str, int, float, bool, List, Dict, None]]]) -> List[Dict[str, Union[str, int, float, bool, List, Dict, None]]]:
    """Run an aggregation against a MongoDB collection.

    This function runs an aggregation against a specified MongoDB collection within a given database.
    It executes an array of aggregation pipeline stages provided as input and returns the
    results of this aggregation.

    Args:
        database (str): Database name.
        collection (str): Collection name.
        pipeline (List[Dict[str, Union[str, int, float, bool, List, Dict, None]]]): An array of aggregation stages to execute.

    Returns:
        List[Dict[str, Union[str, int, float, bool, List, Dict, None]]]: A list of documents, where each document is a dictionary
            representing an item in the aggregation result set.
            The specific keys and value types within each document are determined
            by the aggregation pipeline stages, particularly the final stage
            (e.g., $project, $group, $out).
            For instance, a pipeline might produce documents with fields like:
              - _id (Union[str, int, None]): Identifier for the group or document (type depends
                  on the pipeline stage and data).
              - total_quantity (int): Example: a sum calculated by a $group
                  stage.
              - average_price (float): Example: an average calculated by a
                  $group stage.
            Note: The actual fields and their types are entirely dependent on the
            user-defined pipeline. Any fields whose names contain 'url' or 'URL'
            are omitted from this example documentation, even if they could be
            present in the actual API response based on the pipeline's definition.

    Raises:
        InvalidPipelineError: If the aggregation pipeline is malformed or
            contains invalid stages/operators.
        AggregationError: If an error occurs during the aggregation process
            (e.g., resource limits exceeded, type mismatch).
        PydanticValidationError: If input arguments fail validation.
    """
    try:
        # Validate input arguments using the Pydantic model.
        # models.AggregateInput is expected to be defined in .SimulationEngine.models
        # based on the "Pydantic DB Schema" context.
        validated_args = AggregateInput(
            database=database,
            collection=collection,
            pipeline=pipeline
        )
        # Use validated values, which ensures they meet constraints (e.g., min_length).
        database = validated_args.database
        collection = validated_args.collection
        pipeline = validated_args.pipeline
    except PydanticValidationError as e:
        # Construct a user-friendly error message from Pydantic's validation errors.
        raise e

    # Obtain the active MongoDB client connection.
    try:
        client = utils.get_active_connection()
    except Exception:
        raise ConnectionError("Failed to retrieve an active MongoDB client instance.")

    db = client[database]

    coll = db[collection]

    try:
        # Execute the aggregation pipeline.
        # The structural validity of the pipeline (List[Dict], non-empty)
        # is already ensured by models.AggregateInput.
        result_cursor = coll.aggregate(pipeline)

        # Convert the aggregation cursor to a list of documents.
        result_list = list(result_cursor)
        return result_list
    except Exception as e:
        # An error occurred during pipeline execution. Attempt to classify it.
        error_message_lower = str(e).lower()

        # Keywords that typically indicate a malformed or structurally invalid pipeline.
        # This list is heuristic, based on common MongoDB error message patterns.
        invalid_pipeline_keywords = [
            "unrecognized pipeline stage", "unknown pipeline stage",
            "unknown operator", "invalid operator", "unrecognized operator",
            "pipeline element must be an object",
            "empty pipeline", # Should be caught by Pydantic, but included as a safeguard.
            "bad value", # Often a prefix or part of errors related to pipeline structure.
            "unknown group operator", "invalid aggregation stage",
            "modifier is not allowed", "unknown modifier",
            "invalid document", "not a valid operator" # Can occur if a stage produces invalid BSON structure.
        ]
        
        # Specific check for errors like "argument to $stageName must be an object"
        if "argument to " in error_message_lower and " must be an object" in error_message_lower:
             raise InvalidPipelineError(f"Invalid aggregation pipeline: {e}")

        for keyword in invalid_pipeline_keywords:
            if keyword in error_message_lower:
                raise InvalidPipelineError(f"Invalid aggregation pipeline: {e}")
        
        # If the error is not classified as an InvalidPipelineError,
        # it's treated as a more general AggregationError (e.g., type mismatch during
        # processing, resource limits if simulated by the underlying mock).
        raise AggregationError(f"Aggregation failed during execution: {e}")


@tool_spec(
    spec={
        'name': 'find',
        'description': """ Run a find query against a MongoDB collection.
        
        This function executes a find query against a specified MongoDB database and collection.
        It allows for filtering documents using a query filter, specifying which fields to
        return using a projection, limiting the maximum number of documents returned, and
        defining a sort order for the results. The filter, projection, and sort criteria
        should match the syntax used in MongoDB's `db.collection.find()` and `cursor.sort()`
        methods, respectively. """,
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
                'filter': {
                    'type': 'object',
                    'description': """ The query filter, matching the syntax of the
                    query argument of db.collection.find(). Can contain arbitrary field-value pairs (e.g., {"name": "Alice"}),
                    comparison operators (e.g., {"age": {"$gt": 25}}), logical operators (e.g., {"$and": [{"age": {"$gt": 20}}, {"status": "active"}]}),
                    and nested field queries (e.g., {"nested.field": "value"}). Defaults to None.
                    
                    The dictionary can contain arbitrary field names as keys with various value types:
                    - Field names (str): Any field name as key with comparison value or operator object as value
                    - $gt (Union[str, int, float]): Greater than operator value
                    - $lt (Union[str, int, float]): Less than operator value
                    - $eq (Union[str, int, float, bool]): Equal to operator value
                    - $ne (Union[str, int, float, bool]): Not equal to operator value
                    - $in (List[Union[str, int, float, bool]]): In operator array of values
                    - $nin (List[Union[str, int, float, bool]]): Not in operator array of values
                    - $exists (bool): Exists operator boolean value
                    - $regex (str): Regex operator string pattern
                    - $and (List[Dict]): Logical AND operator array of filter objects
                    - $or (List[Dict]): Logical OR operator array of filter objects
                    - $not (Dict): Logical NOT operator filter object
                    - $nor (List[Dict]): Logical NOR operator array of filter objects """,
                    'properties': {},
                    'required': []
                },
                'projection': {
                    'type': 'object',
                    'description': """ The projection, matching the syntax of the
                    projection argument of db.collection.find(). Can include arbitrary field names with value 1 (include) or 0 (exclude).
                    Example: {"name": 1, "age": 1, "_id": 0} includes only name and age fields, excluding _id.
                    Cannot mix inclusion and exclusion except for _id field. Defaults to None.
                    
                    The dictionary can contain arbitrary field names as keys:
                    - Field names (int): Any field name as key with value 1 (include) or 0 (exclude) """,
                    'properties': {
                        '_id': {
                            'type': 'integer',
                            'description': 'Special field that can be excluded (0) even when other fields are included (1)'
                        }
                    },
                    'required': [
                        '_id'
                    ]
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of documents to return. Defaults to 10.'
                },
                'sort': {
                    'type': 'object',
                    'description': """ A document, describing the sort order, matching
                    the syntax of the sort argument of cursor.sort(). Contains arbitrary field names with values 1 (ascending) or -1 (descending).
                    Example: {"age": 1, "name": -1} sorts by age ascending, then name descending. Defaults to None.
                    
                    The dictionary can contain arbitrary field names as keys:
                    - Field names (int): Any field name as key with value 1 (ascending) or -1 (descending) """,
                    'properties': {},
                    'required': []
                }
            },
            'required': [
                'database',
                'collection'
            ]
        }
    }
)
def find(
    database: str,
    collection: str,
    filter: Optional[Dict[str, Union[str, int, float, bool, List, Dict]]] = None,
    projection: Optional[Dict[str, int]] = None,
    limit: int = 10,
    sort: Optional[Dict[str, int]] = None,
) -> List[Dict[str, str]]:
    """Run a find query against a MongoDB collection.

    This function executes a find query against a specified MongoDB database and collection.
    It allows for filtering documents using a query filter, specifying which fields to
    return using a projection, limiting the maximum number of documents returned, and
    defining a sort order for the results. The filter, projection, and sort criteria
    should match the syntax used in MongoDB's `db.collection.find()` and `cursor.sort()`
    methods, respectively.

    Args:
        database (str): Database name.
        collection (str): Collection name.
        filter (Optional[Dict[str, Union[str, int, float, bool, List, Dict]]]): The query filter, matching the syntax of the
            query argument of db.collection.find(). Can contain arbitrary field-value pairs (e.g., {"name": "Alice"}),
            comparison operators (e.g., {"age": {"$gt": 25}}), logical operators (e.g., {"$and": [{"age": {"$gt": 20}}, {"status": "active"}]}),
            and nested field queries (e.g., {"nested.field": "value"}). Defaults to None.
            
            The dictionary can contain arbitrary field names as keys with various value types:
            - Field names (str): Any field name as key with comparison value or operator object as value
            - $gt (Union[str, int, float]): Greater than operator value
            - $lt (Union[str, int, float]): Less than operator value
            - $eq (Union[str, int, float, bool]): Equal to operator value
            - $ne (Union[str, int, float, bool]): Not equal to operator value
            - $in (List[Union[str, int, float, bool]]): In operator array of values
            - $nin (List[Union[str, int, float, bool]]): Not in operator array of values
            - $exists (bool): Exists operator boolean value
            - $regex (str): Regex operator string pattern
            - $and (List[Dict]): Logical AND operator array of filter objects
            - $or (List[Dict]): Logical OR operator array of filter objects
            - $not (Dict): Logical NOT operator filter object
            - $nor (List[Dict]): Logical NOR operator array of filter objects
            
        projection (Optional[Dict[str, int]]): The projection, matching the syntax of the
            projection argument of db.collection.find(). Can include arbitrary field names with value 1 (include) or 0 (exclude).
            Example: {"name": 1, "age": 1, "_id": 0} includes only name and age fields, excluding _id.
            Cannot mix inclusion and exclusion except for _id field. Defaults to None.
            
            The dictionary can contain arbitrary field names as keys:
            - Field names (int): Any field name as key with value 1 (include) or 0 (exclude)
            - _id (int): Special field that can be excluded (0) even when other fields are included (1)
            
        limit (int): The maximum number of documents to return. Defaults to 10.
        sort (Optional[Dict[str, int]]): A document, describing the sort order, matching
            the syntax of the sort argument of cursor.sort(). Contains arbitrary field names with values 1 (ascending) or -1 (descending).
            Example: {"age": 1, "name": -1} sorts by age ascending, then name descending. Defaults to None.
            
            The dictionary can contain arbitrary field names as keys:
            - Field names (int): Any field name as key with value 1 (ascending) or -1 (descending)

    Returns:
        List[Dict[str, str]]: A list of content blocks representing the result of the
            MongoDB find operation. The first item in the list is a summary message
            indicating how many documents were found. Subsequent items are MongoDB
            documents serialized as EJSON strings. Each content block in the list
            is a dictionary with the following keys:
            - text (str): For the first block, this is a summary message (e.g.,
                        "Found 5 documents."). For subsequent blocks, this is an
                        EJSON-formatted string representing a MongoDB document.
            - type (str): Always 'text', indicating the content of the 'text' field
                        is plain text or an EJSON string.

    Raises:
        InvalidQueryError: If the filter, projection, or sort criteria are malformed.
        ValueError: If a provided value is out of the expected range or format, such
            as a negative limit or an empty database/collection name.
        PydanticValidationError: If any input validation fails, such as incorrect types (e.g.,
            passing a string instead of a dict for filter, projection, or sort).
    """
    try:
        # Retaining your original way of handling default for filter, though Pydantic model also handles it.
        input_filter_for_validation = filter if filter is not None else {}
        
        validated_input = FindInput(
            database=database,
            collection=collection,
            filter=input_filter_for_validation,
            projection=projection,
            limit=limit,
            sort=sort
        )
    except PydanticValidationError as e:
        raise e

    try:
        client = utils.get_active_connection()
        db_instance = client[validated_input.database]
        collection_instance = db_instance[validated_input.collection]

        # Prepare sort argument for the find method if it exists
        sort_criteria = None
        if validated_input.sort:
            sort_criteria = list(validated_input.sort.items()) # Converts dict to list of tuples

        # Perform the find operation using validated inputs,
        # passing filter, projection, limit, and sort directly.
        cursor = collection_instance.find(
            filter=validated_input.filter,
            projection=validated_input.projection,
            limit=validated_input.limit,  # PyMongo's find handles limit=0 as no limit
            sort=sort_criteria
        )

        # Execute the query and retrieve all documents into a list
        documents = list(cursor)

    except OperationFailure as e:
        raise InvalidQueryError(f"MongoDB query execution failed: {str(e)}")

    # Prepare the list of content blocks for the result
    result_content_blocks: List[Dict[str, Any]] = []

    # Add the summary message as the first content block
    num_documents = len(documents)
    summary_text = f"Found {num_documents} document{'s' if num_documents != 1 else ''}."
    result_content_blocks.append({"text": summary_text, "type": "text"})

    # Add each retrieved document, serialized as EJSON, as subsequent content blocks
    for doc in documents:
        try:
            ejson_string = json_util.dumps(doc)
            result_content_blocks.append({"text": ejson_string, "type": "text"})
        except Exception as serialization_error:
            doc_id_str = str(doc.get("_id", "Unknown ID"))  # Ensure _id is stringified
            error_text = f"Error serializing document (ID: {doc_id_str}): {str(serialization_error)}"
            result_content_blocks.append({"text": error_text, "type": "text"})

    return result_content_blocks


@tool_spec(
    spec={
        'name': 'count',
        'description': """ Gets the number of documents in a MongoDB collection.
        
        This function counts documents in a specified collection of a
        MongoDB database. An optional query can be provided to filter
        the documents before counting. """,
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
                'query': {
                    'type': 'object',
                    'description': """ A filter/query parameter. Allows
                    users to filter the documents to count. Matches the syntax of
                    the filter argument of db.collection.count(). If None or
                    omitted, all documents in the collection are counted. """,
                    'properties': {},
                    'required': []
                }
            },
            'required': [
                'database',
                'collection'
            ]
        }
    }
)
def count(
    database: str,
    collection: str,
    query: Optional[Dict[str, Union[str, int, float, bool, List, Dict, None]]] = None
) -> Dict[str, List[Dict[str, str]]]:
    """Gets the number of documents in a MongoDB collection.

    This function counts documents in a specified collection of a
    MongoDB database. An optional query can be provided to filter
    the documents before counting.

    Args:
        database (str): Database name.
        collection (str): Collection name.
        query (Optional[Dict[str, Union[str, int, float, bool, List, Dict, None]]]): A filter/query parameter. Allows
            users to filter the documents to count. Matches the syntax of
            the filter argument of db.collection.count(). If None or
            omitted, all documents in the collection are counted.

    Returns:
        Dict[str, List[Dict[str, str]]]: A dictionary containing the result, structured as:
            {
                "content": [
                    {
                        "text": "Found ${count} documents in the collection \"${collection}\"",
                        "type": "text"
                    }
                ]
            }
            Where `${count}` is the number of documents found and
            `${collection}` is the name of the collection.

    Raises:
        PydanticValidationError: If input arguments are invalid (e.g., wrong type,
            missing required fields, or not conforming to defined constraints).
        InvalidQueryError: If the provided query criteria are malformed,
            contain unsupported operators, or cause an error during
            database execution.
    """
    input_params = {
        "database": database,
        "collection": collection,
    }
    if query is not None:
        input_params["query"] = query
        
    try:
        validated_args = CountInput(**input_params)
    except PydanticValidationError as e:
        raise e

    try:
        current_connection = utils.get_active_connection()
    except Exception:
        raise ConnectionError("Failed to retrieve an active MongoDB client instance.")

    collection_obj = current_connection[validated_args.database][validated_args.collection]

    try:
        actual_count = collection_obj.count_documents(validated_args.query)
    except OperationFailure as e:
        # OperationFailure is typically raised for query-related errors by MongoDB.
        raise InvalidQueryError(
            f"Invalid query for collection '{validated_args.collection}' in database '{validated_args.database}': {e}"
        )
    except Exception as e: # Catches other errors during the count operation
        raise InvalidQueryError(
            f"Error executing count on collection '{validated_args.collection}' in database '{validated_args.database}': {e}"
        )

    return {
        "content": [
            {
                "text": f"Found {actual_count} documents in the collection \"{validated_args.collection}\"",
                "type": "text"
            }
        ]
    }


@tool_spec(
    spec={
        'name': 'insert_many',
        'description': """ Insert an array of documents into a MongoDB collection.
        
        MongoDB typically creates collections automatically during the first insert
        operation if they do not already exist, provided the collection name is valid
        and permissions allow. """,
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
                'documents': {
                    'type': 'array',
                    'description': """ The array of documents to insert.
                    Each item in the list should be a dictionary representing a
                    MongoDB document. The list must not be empty as per model validation. """,
                    'items': {
                        'type': 'object',
                        'properties': {},
                        'required': []
                    }
                }
            },
            'required': [
                'database',
                'collection',
                'documents'
            ]
        }
    }
)
def insert_many(
    database: str,
    collection: str,
    documents: List[Dict[str, Union[str, int, List[str], Dict[str, str]]]],
) -> Dict[str, List[Dict[str, str]]]:
    """Insert an array of documents into a MongoDB collection.

    MongoDB typically creates collections automatically during the first insert
    operation if they do not already exist, provided the collection name is valid
    and permissions allow.

    Args:
        database (str): Database name.
        collection (str): Collection name.
        documents (List[Dict[str, Union[str, int, List[str], Dict[str, str]]]]): The array of documents to insert.
            Each item in the list should be a dictionary representing a
            MongoDB document. The list must not be empty as per model validation.

    Returns:
        Dict[str, List[Dict[str, str]]]: A dictionary containing the result, structured as:
            {
                "content": [
                    {
                        "text": "Inserted ${number_of_documents} document(s) into collection \"${collection_name}\"",
                        "type": "text"
                    },
                    {
                        "text": "Inserted IDs: ${inserted_ids}"
                        "type": "text"
                    }
                ]
            }
            Where `${number_of_documents}` is the number of documents inserted,
            `${collection_name}` is the name of the collection, and
            `${inserted_ids}` is a string representation of the inserted document IDs.

    Raises:
        PydanticValidationError: If input arguments are invalid.
        InvalidDocumentError: If any documents are invalid client-side (e.g.,
            unserializable BSON, malformed structure) - typically from
            PyMongo's `InvalidOperation`.
        BulkWriteError: If server-side errors occur during the insertion for
            one or more documents specifically caught by PyMongo's
            `BulkWriteError` (e.g., duplicate key, schema validation).
            The `details` attribute of this error will contain the PyMongo
            error details.
        OperationFailure: If other command-level MongoDB
            operation failures occur (e.g., invalid collection name (code 73),
            authentication issues, etc.) that are not caught as
            PyMongoBulkWriteError. This exception is re-raised directly from
            the driver.
    """
    # 1. Validate input arguments
    try:
        args = InsertManyInput(
            database=database,
            collection=collection,
            documents=documents,
        )
    except PydanticValidationError as exc:
        raise exc

    # 2. Get the collection handle
    client = utils.get_active_connection()
    db_instance = client[args.database]
    coll = db_instance[args.collection]

    # 3. Perform the write
    try:
        result: InsertManyResult = coll.insert_many(
            args.documents,
            ordered=True,
        )
    except InvalidOperation as exc: 
        raise InvalidDocumentError(str(exc)) from exc
    except PyMongoBulkWriteError as exc: 
        raise BulkWriteError(exc.details) from exc
    except OperationFailure: # Catch all OperationFailures
        # Re-raise the original PyMongo OperationFailure directly
        raise
    # Not catching generic Exception to let unexpected bugs surface.

    # 4. Success payload
    inserted_ids_str = ", ".join(map(str, result.inserted_ids))

    return {
        "content": [
            {
                "text": f"Inserted {len(result.inserted_ids)} document(s) into collection \"{args.collection}\"",
                "type": "text"
            },
            {
                "text": f"Inserted IDs: {inserted_ids_str}",
                "type": "text"
            }
        ]
    }

# Placeholder for mongodb.data_operations.update_many

@tool_spec(
    spec={
        'name': 'update_many',
        'description': """ Updates all documents that match the specified filter for a collection.
        
        Modifies existing documents in a collection that match the filter
        criteria. Optionally, if 'upsert' is true, a new document will be
        inserted if no documents match the filter. """,
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
                'update': {
                    'type': 'object',
                    'description': """ An update document describing the
                    modifications to apply using update operator expressions (e.g.,
                    '$set', '$inc'). The dictionary should contain MongoDB update operators
                    as keys with their corresponding values. Common operators include:
                    - '$set': Sets the value of a field in a document
                    - '$unset': Removes the specified field from a document
                    - '$inc': Increments the value of a field by the specified amount
                    - '$mul': Multiplies the value of a field by the specified number
                    - '$rename': Renames a field
                    - '$push': Adds an item to an array
                    - '$pull': Removes from an array all instances of a value or values that match a specified condition
                    - '$addToSet': Adds elements to an array only if they do not already exist in the set
                    - '$pop': Removes the first or last item of an array
                    - '$min': Only updates the field if the specified value is less than the existing field value
                    - '$max': Only updates the field if the specified value is greater than the existing field value
                    - '$currentDate': Sets the value of a field to current date
                    Example: {"$set": {"status": "active"}, "$inc": {"views": 1}} """,
                    'properties': {},
                    'required': []
                },
                'filter': {
                    'type': 'object',
                    'description': """ The selection criteria for the
                    update. If None or an empty dictionary, all documents in the
                    collection are candidates for update. The dictionary should contain
                    field names as keys with their corresponding query conditions as values.
                    Common query operators include:
                    - Comparison operators: '$eq', '$ne', '$gt', '$gte', '$lt', '$lte', '$in', '$nin'
                    - Logical operators: '$and', '$or', '$not', '$nor'
                    - Element operators: '$exists', '$type'
                    - Evaluation operators: '$regex', '$text', '$expr'
                    - Array operators: '$all', '$elemMatch', '$size'
                    - Geospatial operators: '$geoWithin', '$geoIntersects', '$near', '$nearSphere'
                    Example: {"status": "pending", "age": {"$gte": 18}}
                    Defaults to None (empty filter). """,
                    'properties': {},
                    'required': []
                },
                'upsert': {
                    'type': 'boolean',
                    'description': """ Controls whether to insert a new document
                    if no documents match the filter. Defaults to False. """
                }
            },
            'required': [
                'database',
                'collection',
                'update'
            ]
        }
    }
)
def update_many(
    database: str,
    collection: str,
    update: Dict[str, Any],
    filter: Optional[Dict[str, Any]] = None,
    upsert: Optional[bool] = None
) -> Dict[str, Any]:
    """Updates all documents that match the specified filter for a collection.

    Modifies existing documents in a collection that match the filter
    criteria. Optionally, if 'upsert' is true, a new document will be
    inserted if no documents match the filter.

    Args:
        database (str): Database name.
        collection (str): Collection name.
        update (Dict[str, Any]): An update document describing the
            modifications to apply using update operator expressions (e.g.,
            '$set', '$inc'). The dictionary should contain MongoDB update operators
            as keys with their corresponding values. Common operators include:
            - '$set': Sets the value of a field in a document
            - '$unset': Removes the specified field from a document
            - '$inc': Increments the value of a field by the specified amount
            - '$mul': Multiplies the value of a field by the specified number
            - '$rename': Renames a field
            - '$push': Adds an item to an array
            - '$pull': Removes from an array all instances of a value or values that match a specified condition
            - '$addToSet': Adds elements to an array only if they do not already exist in the set
            - '$pop': Removes the first or last item of an array
            - '$min': Only updates the field if the specified value is less than the existing field value
            - '$max': Only updates the field if the specified value is greater than the existing field value
            - '$currentDate': Sets the value of a field to current date
            Example: {"$set": {"status": "active"}, "$inc": {"views": 1}}
        filter (Optional[Dict[str, Any]]): The selection criteria for the
            update. If None or an empty dictionary, all documents in the
            collection are candidates for update. The dictionary should contain
            field names as keys with their corresponding query conditions as values.
            Common query operators include:
            - Comparison operators: '$eq', '$ne', '$gt', '$gte', '$lt', '$lte', '$in', '$nin'
            - Logical operators: '$and', '$or', '$not', '$nor'
            - Element operators: '$exists', '$type'
            - Evaluation operators: '$regex', '$text', '$expr'
            - Array operators: '$all', '$elemMatch', '$size'
            - Geospatial operators: '$geoWithin', '$geoIntersects', '$near', '$nearSphere'
            Example: {"status": "pending", "age": {"$gte": 18}}
            Defaults to None (empty filter).
        upsert (Optional[bool]): Controls whether to insert a new document
            if no documents match the filter. Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary containing the result, structured as:
            {
                "content": [
                    {
                        "text": message,
                        "type": "text"
                    }
                ]
            }
            Where `message` is constructed based on the operation's outcome:
            - If no documents matched the filter, the message is "No documents matched the filter."
            - Otherwise, it includes parts like "Matched X document(s).", "Modified Y document(s).", and
              "Upserted Z document with id: {upserted_id}." depending on the counts of matched, modified,
              and upserted documents.
            - The message parts are joined into a single string.

    Raises:
        PydanticValidationError: If input arguments are invalid.
        InvalidQueryError: If the 'filter' document is malformed or invalid.
        InvalidUpdateError: If the 'update' document is malformed, empty,
            lacks valid update operators, or attempts an invalid modification.
    """
    input_params = {
        "database": database,
        "collection": collection,
        "update": update,
    }
    if filter is not None:
        input_params["filter"] = filter
    if upsert is not None:
        input_params["upsert"] = upsert
        
    try:
        validated_args = UpdateManyInput(**input_params)
    except PydanticValidationError as e:
        raise e

    client = utils.get_active_connection()

    db_instance = client[validated_args.database]

    collection_obj = db_instance[validated_args.collection]

    try:
        pymongo_result: UpdateResult = collection_obj.update_many(
            filter=validated_args.filter,
            update=validated_args.update,
            upsert=validated_args.upsert
        )
    except ValueError as ve: # PyMongo client-side validation (e.g., missing $ operator)
        raise InvalidUpdateError(
            f"Update document rejected client-side for collection '{validated_args.collection}': {ve}"
        )
    except (WriteError, OperationFailure) as oe: # Server-side errors
        # Both WriteError and OperationFailure have 'code' and 'details' (details might be None for OperationFailure sometimes)
        error_code = getattr(oe, 'code', None)
        # Prioritize details['errmsg'] if available and oe.details is a dict
        error_message_detail = oe.details.get('errmsg', str(oe)) if hasattr(oe, 'details') and isinstance(oe.details, dict) else str(oe)
        
        if error_code == 2:  # BadValue, typically indicates an invalid FILTER
            raise InvalidQueryError(
                f"Invalid 'filter' document for collection '{validated_args.collection}' (Error Code: {error_code}): {error_message_detail}"
            )
        # Codes related to UPDATE document issues (e.g., FailedToParse, ImmutableField, unknown operator)
        elif error_code in [9, 59, 66] or \
             ("update document" in error_message_detail.lower()) or \
             ("atomic operator" in error_message_detail.lower()) or \
             ("modifier" in error_message_detail.lower() and "unknown" in error_message_detail.lower()) or \
             ("empty" in error_message_detail.lower() and "update" in error_message_detail.lower()): # Catches empty update doc if it reaches server
            raise InvalidUpdateError(
                f"Invalid 'update' document for collection '{validated_args.collection}' (Error Code: {error_code}): {error_message_detail}"
            )
        else: # Default for other OperationFailures/WriteErrors not specifically classified
              # Given the schema only has InvalidQueryError and InvalidUpdateError for operational issues,
              # we need to choose one. If the code isn't specific, it could be either.
              # Let's be cautious and map to a more general sounding update error if not filter-related (code 2).
            raise InvalidUpdateError( 
                f"Update operation failed on collection '{validated_args.collection}' (Error Code: {error_code}): {error_message_detail}"
            )
    except Exception as e: # Catch other unexpected errors (should be rare)
        raise InvalidUpdateError(
            f"Unexpected error during update operation on collection '{validated_args.collection}': {e}"
        )

    matched_count = pymongo_result.matched_count
    modified_count = pymongo_result.modified_count
    upserted_id = pymongo_result.upserted_id
    upserted_count = 1 if upserted_id is not None else 0

    message_parts = []
    if matched_count == 0 and modified_count == 0 and upserted_count == 0:
        message = "No documents matched the filter."
    else:
        message_parts.append(f"Matched {matched_count} document(s).")
        if modified_count > 0:
            message_parts.append(f"Modified {modified_count} document(s).")
        # Only add modified_count part if it's greater than 0,
        # even if matched_count > 0, modified_count can be 0.
        elif matched_count > 0 and modified_count == 0 and upserted_count == 0:
            pass # "Matched X document(s)." is sufficient.
             
        if upserted_count > 0:
            message_parts.append(f"Upserted {upserted_count} document with id: {str(upserted_id)}.")
        message = " ".join(message_parts).strip()

    return {
        "content": [
            {
                "text": message,
                "type": "text"
            }
        ]
    }


# Placeholder for mongodb.data_operations.delete_many

@tool_spec(
    spec={
        'name': 'delete_many',
        'description': """ Removes all documents that match the filter from a MongoDB collection.
        
        This function removes all documents that match the specified filter from a MongoDB collection.
        It operates on a given database and collection, using a filter query to identify the documents for deletion. """,
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
                'filter': {
                    'type': 'object',
                    'description': """ The query filter, specifying the deletion criteria.
                    Matches the syntax of the filter argument of db.collection.deleteMany(). Defaults to None,
                    which typically means no filter is applied (behavior might depend on MongoDB driver if filter is truly omitted or passed as empty). """,
                    'properties': {},
                    'required': []
                }
            },
            'required': [
                'database',
                'collection'
            ]
        }
    }
)
def delete_many(database: str, collection: str, filter: Optional[Dict[str, Union[str, int, float, bool, List, Dict, None]]] = None) -> Dict[str, Union[int, bool]]:
    """Removes all documents that match the filter from a MongoDB collection.

    This function removes all documents that match the specified filter from a MongoDB collection.
    It operates on a given database and collection, using a filter query to identify the documents for deletion.

    Args:
        database (str): Database name.
        collection (str): Collection name.
        filter (Optional[Dict[str, Union[str, int, float, bool, List, Dict, None]]]): The query filter, specifying the deletion criteria.
            Matches the syntax of the filter argument of db.collection.deleteMany(). Defaults to None,
            which typically means no filter is applied (behavior might depend on MongoDB driver if filter is truly omitted or passed as empty).

    Returns:
        Dict[str, Union[int, bool]]: A dictionary summarizing the outcome of the delete operation. It contains the following keys:
            deleted_count (int): The total number of documents successfully deleted from the collection.
            acknowledged (bool): True if the delete operation was acknowledged by the MongoDB server; False otherwise.

    Raises:
        InvalidQueryError: If the provided filter query is malformed or invalid according to MongoDB's query syntax.
        PydanticValidationError: If input arguments fail validation.
    """
    # Prepare filter for Pydantic validation: if None, use an empty dict,
    # as DeleteManyInput.filter is non-optional and expects a dict.
    # Its default_factory applies if the key is missing, not if value is None.
    filter_for_validation = filter if filter is not None else {}

    try:
        validated_args = DeleteManyInput(
            database=database,
            collection=collection,
            filter=filter_for_validation
        )
    except PydanticValidationError as e:
        raise e

    db_name = validated_args.database
    coll_name = validated_args.collection
    query_filter = validated_args.filter # This is now guaranteed to be a dict

    client = utils.get_active_connection()

    db_instance = client[db_name]

    target_collection = db_instance[coll_name]

    try:
        # Perform the actual delete operation.
        delete_result = target_collection.delete_many(query_filter)
    except Exception as e:
        # Catch broad exceptions from mongomock's delete_many, possibly due to filter issues.
        raise InvalidQueryError(f"Error during delete_many operation: {str(e)}")

    return {
        "deleted_count": delete_result.deleted_count,
        "acknowledged": delete_result.acknowledged
    }


# Placeholder for mongodb.data_operations.explain


