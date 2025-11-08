from common_utils.tool_spec_decorator import tool_spec
import json
import re
from typing import Dict, Any, List, Optional
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import (
    DatasetNotFoundError,
    InvalidInputError,
    InvalidQueryError,
    ProjectNotFoundError,
    TableNotFoundError,
)
from .SimulationEngine.utils import (
    parse_full_table_name,
    load_db_dict_to_sqlite,
    validate_and_normalize_phone_numbers_in_data
)
from datetime import datetime


@tool_spec(
    spec={
        'name': 'list_tables',
        'description': """ List all tables in the specified dataset.
        
        This function lists all tables in the specified BigQuery dataset by loading the JSON DB file
        and processing its contents. It returns a response structure that matches the BigQuery API
        format, including pagination support and metadata about the tables. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'Required. Project ID of the tables to list.'
                },
                'dataset_id': {
                    'type': 'string',
                    'description': 'Required. Dataset ID of the tables to list.'
                },
                'max_results': {
                    'type': 'integer',
                    'description': """ The maximum number of results to return in a single 
                    response page. If 0 or None, returns all tables. Leverage the page tokens to iterate 
                    through the entire collection. Defaults to None. """
                },
                'page_token': {
                    'type': 'string',
                    'description': """ Page token, returned by a previous call, to request 
                    the next page of results. Defaults to None. """
                }
            },
            'required': [
                'project_id',
                'dataset_id'
            ]
        }
    }
)
def list_tables(
    project_id: str, 
    dataset_id: str, 
    max_results: Optional[int] = None, 
    page_token: Optional[str] = None
) -> Dict[str, Any]:
    """List all tables in the specified dataset.

    This function lists all tables in the specified BigQuery dataset by loading the JSON DB file
    and processing its contents. It returns a response structure that matches the BigQuery API
    format, including pagination support and metadata about the tables.

    Args:
        project_id (str): Required. Project ID of the tables to list.
        dataset_id (str): Required. Dataset ID of the tables to list.
        max_results (Optional[int]): The maximum number of results to return in a single 
            response page. If 0 or None, returns all tables. Leverage the page tokens to iterate 
            through the entire collection. Defaults to None.
        page_token (Optional[str]): Page token, returned by a previous call, to request 
            the next page of results. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing the BigQuery API response structure with:
            kind (str): The type of list.
            etag (str): A hash of this page of results.
            nextPageToken (Optional[str]): A token to request the next page of results.
            tables (List[Dict[str, Any]]): Tables in the requested dataset.
            totalItems (int): The total number of tables in the dataset.
            
            Each table in the tables list contains:
            kind (str): The resource type.
            id (str): An opaque ID of the table.
            tableReference (Dict[str, str]): A reference uniquely identifying table.
            friendlyName (Optional[str]): The user-friendly name for this table.
            type (str): The type of table.
            creationTime (str): The time when this table was created, in milliseconds since the epoch.
            expirationTime (Optional[str]): The time when this table expires, in milliseconds since the epoch.

    Raises:
        ProjectNotFoundError: If the specified project_id does not exist or is inaccessible.
        DatasetNotFoundError: If the specified dataset_id does not exist in the project.
        InvalidInputError: If the provided project_id or dataset_id is malformed, or if max_results 
            is not a non-negative integer, or if page_token is not a string.
    """
    try:
        # Validate input parameters
        if not project_id or not isinstance(project_id, str):
            raise InvalidInputError("project_id must be a non-empty string")
        if not dataset_id or not isinstance(dataset_id, str):
            raise InvalidInputError("dataset_id must be a non-empty string")
        
        # Validate max_results parameter
        if max_results is not None and (not isinstance(max_results, int) or max_results < 0):
            raise InvalidInputError("max_results must be a non-negative integer or None")
        
        # Validate page_token parameter
        if page_token is not None and not isinstance(page_token, str):
            raise InvalidInputError("page_token must be a string or None")
        
        # Load the JSON DB at function call time
        projects = DB["projects"]

        if not projects:
            raise ProjectNotFoundError(f"Project '{project_id}' not found")

        # Find the specified project
        project = None
        for p in projects:
            if p.get("project_id") == project_id:
                project = p
                break

        if not project:
            raise ProjectNotFoundError(f"Project '{project_id}' not found")

        # Find the specified dataset
        dataset = None
        for d in project.get("datasets", []):
            if d.get("dataset_id") == dataset_id:
                dataset = d
                break

        if not dataset:
            raise DatasetNotFoundError(f"Dataset '{dataset_id}' not found in project '{project_id}'")

        # Get all tables from the dataset
        all_tables = []
        for table_data in dataset.get("tables", []):
            table_id = table_data.get("table_id")
            if not table_id:
                continue

            # Convert creation time to milliseconds if it's a string
            creation_time = table_data.get("creation_time")
            if isinstance(creation_time, str):
                try:
                    # Parse ISO format timestamp and convert to milliseconds
                    dt = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
                    creation_time_ms = str(int(dt.timestamp() * 1000))
                except ValueError:
                    creation_time_ms = creation_time
            else:
                creation_time_ms = str(creation_time) if creation_time else None

            # Convert expiration time to milliseconds if it's a string
            expiration_time = table_data.get("expiration_time")
            if isinstance(expiration_time, str):
                try:
                    # Parse ISO format timestamp and convert to milliseconds
                    dt = datetime.fromisoformat(expiration_time.replace('Z', '+00:00'))
                    expiration_time_ms = str(int(dt.timestamp() * 1000))
                except ValueError:
                    expiration_time_ms = expiration_time
            else:
                expiration_time_ms = str(expiration_time) if expiration_time else None

            table_info = {
                "kind": "bigquery#table",
                "id": f"{project_id}:{dataset_id}.{table_id}",
                "tableReference": {
                    "projectId": project_id,
                    "datasetId": dataset_id,
                    "tableId": table_id
                },
                "type": table_data.get("type", "TABLE"),
                "creationTime": creation_time_ms,
                "expirationTime": expiration_time_ms
            }

            # Add optional fields only if they exist and have values
            if table_data.get("friendly_name"):
                table_info["friendlyName"] = table_data["friendly_name"]
            
            if "labels" in table_data:
                table_info["labels"] = table_data["labels"]
            
            if "view" in table_data:
                table_info["view"] = table_data["view"]
            
            if "timePartitioning" in table_data:
                table_info["timePartitioning"] = table_data["timePartitioning"]
            
            if "rangePartitioning" in table_data:
                table_info["rangePartitioning"] = table_data["rangePartitioning"]
            
            if "clustering" in table_data:
                table_info["clustering"] = table_data["clustering"]
            
            if "hivePartitioningOptions" in table_data:
                table_info["hivePartitioningOptions"] = table_data["hivePartitioningOptions"]
            
            if "requirePartitionFilter" in table_data:
                table_info["requirePartitionFilter"] = table_data["requirePartitionFilter"]

            all_tables.append(table_info)

        # Handle pagination
        total_items = len(all_tables)
        start_index = 0
        
        if page_token:
            try:
                start_index = int(page_token)
                if start_index < 0:
                    start_index = 0
            except ValueError:
                start_index = 0
        
        end_index = total_items
        if max_results is not None and max_results > 0:
            end_index = min(start_index + max_results, total_items)
        
        tables_page = all_tables[start_index:end_index]
        
        # Generate next page token
        next_page_token = None
        if end_index < total_items:
            next_page_token = str(end_index)

        # Generate etag (simple hash of the current page)
        import hashlib
        etag_content = f"{project_id}:{dataset_id}:{start_index}:{end_index}:{total_items}"
        etag = hashlib.md5(etag_content.encode()).hexdigest()

        return {
            "kind": "bigquery#tableList",
            "etag": etag,
            "nextPageToken": next_page_token,
            "tables": tables_page,
            "totalItems": total_items
        }

    except KeyError as e:
        if "projects" in str(e):
            raise ProjectNotFoundError(f"Project '{project_id}' not found")
        raise InvalidInputError(f"Invalid database structure: {e}")


@tool_spec(
    spec={
        'name': 'describe_table',
        'description': """ Get the specified table resource by table ID.
        
        This method does not return the data in the table, it only returns the table resource,
        which describes the structure of this table. The response follows the BigQuery API
        Table resource specification. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'Required. Project ID of the requested table.'
                },
                'dataset_id': {
                    'type': 'string',
                    'description': 'Required. Dataset ID of the requested table.'
                },
                'table_id': {
                    'type': 'string',
                    'description': 'Required. Table ID of the requested table.'
                },
                'selected_fields': {
                    'type': 'string',
                    'description': """ Comma-separated list of table schema fields to return.
                    If unspecified, all fields are returned. Defaults to None. """
                },
                'view': {
                    'type': 'string',
                    'description': """ Specifies the view that determines which table information is returned.
                    Values: 'BASIC', 'STORAGE_STATS', 'FULL'. Defaults to None. If not provided 'STORAGE_STATS' is used. """
                }
            },
            'required': [
                'project_id',
                'dataset_id',
                'table_id'
            ]
        }
    }
)
def describe_table(
    project_id: str, 
    dataset_id: str, 
    table_id: str, 
    selected_fields: Optional[str] = None, 
    view: Optional[str] = None
) -> Dict[str, Any]:
    """Get the specified table resource by table ID.

    This method does not return the data in the table, it only returns the table resource,
    which describes the structure of this table. The response follows the BigQuery API
    Table resource specification.

    Args:
        project_id (str): Required. Project ID of the requested table.
        dataset_id (str): Required. Dataset ID of the requested table.
        table_id (str): Required. Table ID of the requested table.
        selected_fields (Optional[str]): Comma-separated list of table schema fields to return.
            If unspecified, all fields are returned. Defaults to None.
        view (Optional[str]): Specifies the view that determines which table information is returned.
            Values: 'BASIC', 'STORAGE_STATS', 'FULL'. Defaults to None. If not provided 'STORAGE_STATS' is used.

    Returns:
        Dict[str, Any]: A dictionary containing the BigQuery API Table resource with:
            kind (str): The type of resource ID.
            etag (str): A hash of this resource.
            id (str): An opaque ID uniquely identifying the table.
            selfLink (str): A URL that can be used to access this resource again.
            tableReference (Dict[str, str]): Reference describing the ID of this table.
            friendlyName (Optional[str]): A descriptive name for this table.
            description (Optional[str]): A user-friendly description of this table.
            labels (Dict[str, str]): The labels associated with this table.
            schema (Dict[str, Any]): Describes the schema of this table. Contains the key 'fields'
                with a list of field definitions.
            timePartitioning (Optional[Dict[str, Any]]): Time-based partitioning configuration.
            rangePartitioning (Optional[Dict[str, Any]]): Range partitioning configuration.
            clustering (Optional[Dict[str, Any]]): Clustering specification for the table.
            requirePartitionFilter (Optional[bool]): If true, queries require a partition filter.
            numBytes (str): The size of this table in logical bytes.
            numLongTermBytes (str): The number of logical bytes in long-term storage.
            numRows (int): The number of rows of data in this table. Will be 0 if the table has no rows
                or if row metadata is unavailable.
            creationTime (str): The time when this table was created, in milliseconds since epoch.
            expirationTime (Optional[str]): The time when this table expires, in milliseconds since epoch.
            lastModifiedTime (str): The time when this table was last modified, in milliseconds since epoch.
            type (str): The type of table (TABLE, VIEW, EXTERNAL, MATERIALIZED_VIEW, SNAPSHOT).
            view (Optional[Dict[str, Any]]): The view definition.
            materializedView (Optional[Dict[str, Any]]): The materialized view definition.
            materializedViewStatus (Optional[Dict[str, Any]]): The materialized view status.
            externalDataConfiguration (Optional[Dict[str, Any]]): External data configuration.
            biglakeConfiguration (Optional[Dict[str, Any]]): BigLake configuration.
            location (str): The geographic location where the table resides.
            streamingBuffer (Optional[Dict[str, Any]]): Information about the streaming buffer.
            encryptionConfiguration (Optional[Dict[str, Any]]): Custom encryption configuration.
            snapshotDefinition (Optional[Dict[str, Any]]): Information about the snapshot.
            defaultCollation (Optional[str]): Default collation specification.
            defaultRoundingMode (Optional[str]): Default rounding mode specification.
            cloneDefinition (Optional[Dict[str, Any]]): Information about the clone.
            numTimeTravelPhysicalBytes (str): Physical bytes used by time travel storage.
            numTotalLogicalBytes (str): Total number of logical bytes in the table.
            numActiveLogicalBytes (str): Number of logical bytes less than 90 days old.
            numLongTermLogicalBytes (str): Number of logical bytes more than 90 days old.
            numTotalPhysicalBytes (str): The physical size of this table in bytes.
            numActivePhysicalBytes (str): Number of physical bytes less than 90 days old.
            numLongTermPhysicalBytes (str): Number of physical bytes more than 90 days old.
            numPartitions (str): The number of partitions present in the table.
            maxStaleness (Optional[str]): The maximum staleness of data that could be returned.
            tableConstraints (Optional[Dict[str, Any]]): Primary Key and Foreign Key information.
            resourceTags (Optional[Dict[str, str]]): The tags attached to this table.
            replicas (Optional[List[Dict[str, str]]]): Table references of all active replicas.
            externalCatalogTableOptions (Optional[Dict[str, Any]]): Open source compatible table options.
            partitionDefinition (Optional[Dict[str, Any]]): The partition information.

    Raises:
        TableNotFoundError: If the specified table does not exist or is not accessible.
        InvalidInputError: If the provided parameters are malformed.
        ProjectNotFoundError: If the specified project does not exist.
        DatasetNotFoundError: If the specified dataset does not exist in the project.
    """
    # Validate input parameters
    if not project_id or not isinstance(project_id, str):
        raise InvalidInputError("project_id must be a non-empty string")
    if not dataset_id or not isinstance(dataset_id, str):
        raise InvalidInputError("dataset_id must be a non-empty string")
    if not table_id or not isinstance(table_id, str):
        raise InvalidInputError("table_id must be a non-empty string")

    # Find the project
    project = None
    for p in DB.get("projects", []):
        if p.get("project_id") == project_id:
            project = p
            break

    if not project:
        raise ProjectNotFoundError(f"Project '{project_id}' not found")

    # Find the dataset
    dataset = None
    for d in project.get("datasets", []):
        if d.get("dataset_id") == dataset_id:
            dataset = d
            break

    if not dataset:
        raise DatasetNotFoundError(f"Dataset '{dataset_id}' not found in project '{project_id}'")

    # Find the table
    table = None
    for t in dataset.get("tables", []):
        if t.get("table_id") == table_id:
            table = t
            break

    if not table:
        raise TableNotFoundError(f"Table '{table_id}' not found in dataset '{project_id}.{dataset_id}'")

    # Calculate size in bytes if rows exist
    num_bytes = "0"
    num_rows = 0
    if "rows" in table:
        try:
            num_bytes = str(len(json.dumps(table["rows"]).encode("utf-8")))
            num_rows = len(table["rows"])
        except Exception:
            pass

    # Get the schema from the table definition
    schema = table.get("schema", [])

    # Convert timestamps to milliseconds if they're strings
    creation_time = table.get("creation_time_ms") or table.get("creation_time")
    if isinstance(creation_time, str):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(creation_time.replace('Z', '+00:00'))
            creation_time = str(int(dt.timestamp() * 1000))
        except ValueError:
            pass

    last_modified_time = table.get("last_modified_time_ms") or table.get("last_modified_time")
    if isinstance(last_modified_time, str):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(last_modified_time.replace('Z', '+00:00'))
            last_modified_time = str(int(dt.timestamp() * 1000))
        except ValueError:
            pass

    expiration_time = table.get("expiration_time_ms") or table.get("expiration_time")
    if isinstance(expiration_time, str):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(expiration_time.replace('Z', '+00:00'))
            expiration_time = str(int(dt.timestamp() * 1000))
        except ValueError:
            pass

    # Generate etag (simple hash of the table)
    import hashlib
    etag_content = f"{project_id}:{dataset_id}.{table_id}:{creation_time}:{last_modified_time}"
    etag = hashlib.md5(etag_content.encode()).hexdigest()

    # Construct the response according to BigQuery API Table resource
    response = {
        "kind": "bigquery#table",
        "etag": etag,
        "id": f"{project_id}:{dataset_id}.{table_id}",
        "selfLink": f"https://bigquery.googleapis.com/bigquery/v2/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}",
        "tableReference": {
            "projectId": project_id,
            "datasetId": dataset_id,
            "tableId": table_id
        },
        "friendlyName": table.get("friendly_name"),
        "description": table.get("description"),
        "labels": table.get("labels", {}),
        "schema": {"fields": schema},
        "timePartitioning": table.get("timePartitioning"),
        "rangePartitioning": table.get("rangePartitioning"),
        "clustering": table.get("clustering"),
        "requirePartitionFilter": table.get("requirePartitionFilter"),
        "numBytes": num_bytes,
        "numLongTermBytes": "0",  # Default for simulation
        "numRows": num_rows,
        "creationTime": creation_time,
        "expirationTime": expiration_time,
        "lastModifiedTime": last_modified_time,
        "type": table.get("type", "TABLE"),
        "view": table.get("view"),
        "materializedView": table.get("materializedView"),
        "materializedViewStatus": table.get("materializedViewStatus"),
        "externalDataConfiguration": table.get("externalDataConfiguration"),
        "biglakeConfiguration": table.get("biglakeConfiguration"),
        "location": table.get("location", "US"),  # Default location
        "streamingBuffer": table.get("streamingBuffer"),
        "encryptionConfiguration": table.get("encryptionConfiguration"),
        "snapshotDefinition": table.get("snapshotDefinition"),
        "defaultCollation": table.get("defaultCollation"),
        "defaultRoundingMode": table.get("defaultRoundingMode"),
        "cloneDefinition": table.get("cloneDefinition"),
        "numTimeTravelPhysicalBytes": "0",  # Default for simulation
        "numTotalLogicalBytes": num_bytes,
        "numActiveLogicalBytes": num_bytes,
        "numLongTermLogicalBytes": "0",
        "numTotalPhysicalBytes": num_bytes,
        "numActivePhysicalBytes": num_bytes,
        "numLongTermPhysicalBytes": "0",
        "numPartitions": "0",  # Default for simulation
        "maxStaleness": table.get("maxStaleness"),
        "tableConstraints": table.get("tableConstraints"),
        "resourceTags": table.get("resourceTags", {}),
        "replicas": table.get("replicas", []),
        "externalCatalogTableOptions": table.get("externalCatalogTableOptions"),
        "partitionDefinition": table.get("partitionDefinition")
    }

    # Handle selected_fields parameter
    if selected_fields is not None:
        selected_field_list = [field.strip() for field in selected_fields.split(",") if field.strip()]
        if selected_field_list:
            filtered_response = {}
            for field in selected_field_list:
                if field in response:
                    filtered_response[field] = response[field]
            return filtered_response
        else:
            # Return empty response when no valid fields are selected
            return {}

    # Handle view parameter
    if view == "BASIC":
        # Return only basic table information without storage statistics
        basic_fields = [
            "kind", "etag", "id", "selfLink", "tableReference", "friendlyName", 
            "description", "labels", "schema", "timePartitioning", "rangePartitioning", 
            "clustering", "requirePartitionFilter", "creationTime", "expirationTime", 
            "lastModifiedTime", "type", "view", "materializedView", 
            "externalDataConfiguration", "biglakeConfiguration", "location", 
            "encryptionConfiguration", "snapshotDefinition", "defaultCollation", 
            "defaultRoundingMode", "cloneDefinition", "maxStaleness", 
            "tableConstraints", "resourceTags", "replicas", 
            "externalCatalogTableOptions", "partitionDefinition"
        ]
        return {field: response[field] for field in basic_fields if field in response}
    elif view == "FULL":
        # Return all information (same as STORAGE_STATS for now)
        return response
    else:
        # Default to STORAGE_STATS view (includes storage statistics)
        return response


@tool_spec(
    spec={
        'name': 'execute_query',
        'description': 'Execute a SELECT query on the BigQuery database.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The SQL query to execute.'
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def execute_query(query: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Execute a SELECT query on the BigQuery database.

    Args:
        query (str): The SQL query to execute.

    Returns:
        Dict[str, List[Dict[str, Any]]]: Query results containing a list of row dictionaries.
        The dictionary contains the key 'query_results' which is a list of row dictionaries.
        Each row dictionary contains the key 'column_name' which is the name of the column and the value is the value of the column.
            - query_results (List[Dict[str, Any]]): A list of row dictionaries.
            - bytes_processed (int): The number of bytes processed.
            - rows_processed (int): The number of rows processed.
    Raises:
        InvalidQueryError: If the SQL query is malformed, contains syntax errors, references non-existent tables/columns, or is otherwise invalid.
        InvalidInputError: If the provided query parameter is invalid (None, empty, or not a string).
    """
    
    # Input validation for query parameter
    if query is None:
        raise InvalidInputError("Query parameter cannot be None")
    
    if not isinstance(query, str):
        raise InvalidInputError(f"Query parameter must be a string, got {type(query).__name__}")
    
    if not query.strip():
        raise InvalidInputError("Query parameter cannot be empty or contain only whitespace")
    
    # Check for minimum query length
    if len(query.strip()) < 6:  # Minimum for "SELECT"
        raise InvalidInputError("Query is too short to be a valid SQL query")

    # Validate that this is a SELECT query
    query_upper = query.strip().upper()
    if not query_upper.startswith("SELECT"):
        raise InvalidQueryError("Only SELECT queries are supported")

    # Extract table name from query
    fqdn_pattern = r"((?:`?[\w-]+`?\.){2}`?[\w-]+`?)"
    regex_for_table_extraction = re.compile(r"FROM\s+" + fqdn_pattern, re.IGNORECASE)
    match = regex_for_table_extraction.search(query)

    if not match:
        # Attempt to extract table name if it's not fully qualified (e.g. for subqueries or direct table names)
        # This is a simplified extraction and might need refinement for complex queries.
        simple_table_match = re.search(r"FROM\s+`?([\w-]+)`?", query, re.IGNORECASE)
        if simple_table_match:
            # This case implies the table is in the default project/dataset context,
            # which needs to be handled or assume a default.
            # For now, we'll raise an error if FQDN is not found, as per original logic.
            raise InvalidQueryError(
                f"Could not parse fully qualified table name (project.dataset.table) from query: {query[:100]}..."
            )
        else:
            raise InvalidQueryError(
                f"Could not parse table name from query: {query[:100]}..."
            )

    full_table_name = match.group(1).replace("`", "")
    try:
        project_id, dataset_id, table_id = parse_full_table_name(full_table_name)
    except InvalidQueryError as e:  # Catching specific error from parse_full_table_name
        raise InvalidQueryError(f"Invalid table name format '{full_table_name}': {e}")

    # Initialize tracking variables
    bytes_processed = 0
    rows_processed = 0
    conn = None
    try:
        # Get database connection
        conn = load_db_dict_to_sqlite(DB)
        cursor = conn.cursor()

        # Modify query to properly quote table names with hyphens for SQLite
        # This simple replace might be problematic if full_table_name is a substring of another identifier
        # A more robust way would be to parse the query or use regex with word boundaries.
        # For now, assuming simple table references.
        # Example: project-id.dataset-id.table-name -> "table-name"
        # This replacement needs to be careful if `full_table_name` can appear elsewhere
        # or if the query involves aliases that match `full_table_name`.
        # A safer replacement would target `full_table_name` specifically after FROM or JOIN.
        # Consider the query: SELECT col FROM project.dataset.table WHERE table.col = 1
        # If full_table_name is "project.dataset.table", replacing it with "table"
        # would break "table.col". The current code uses table_id.

        # Current replacement logic:
        # sqlite_query = query.replace(full_table_name, f'"{table_id}"')
        # This is risky. If query is "SELECT a.name FROM project-foo.dataset-bar.table-baz AS a"
        # and full_table_name is "project-foo.dataset-bar.table-baz",
        # table_id is "table-baz". The replacement becomes "SELECT a.name FROM "table-baz" AS a"
        # This should be okay for the FROM clause.

        # A regex based replacement for the FROM clause part:
        # Pattern to find 'FROM project.dataset.table' or 'JOIN project.dataset.table'
        # and replace 'project.dataset.table' with '"table"'

        # Replace FQDN with just the table name, quoted.
        # This assumes `full_table_name` is unique enough not to clash with column names or aliases.
        # And that it's the direct reference in FROM/JOIN.

        # To make replacement safer, target only the FQDN after FROM or JOIN keywords.
        # This is complex due to potential aliases and subqueries.
        # The original simple replacement:
        sqlite_query = query.replace(full_table_name, f'"{table_id}"')

        # Execute query
        cursor.execute(sqlite_query)
        rows = cursor.fetchall()
        column_names = (
            [desc[0] for desc in cursor.description] if cursor.description else []
        )

        # Process results
        query_results = []
        for row_idx, row_data in enumerate(rows):

            rows_processed += 1

            # Convert row to dictionary
            row_dict: Dict[str, Any] = {}
            for i, col_name in enumerate(column_names):
                # Use the index to access the tuple value
                value = row_data[i]

                # Handle different data types
                if value is None:
                    row_dict[col_name] = None
                elif isinstance(value, str):
                    # Try to parse JSON strings if column is supposed to be JSON
                    # This requires schema inspection, which is not done here.
                    # For now, assume strings that look like JSON are JSON.
                    try:
                        # A more robust check would be to see if the original BQ schema type was JSON
                        # For now, this is a general attempt.
                        if (value.startswith("{") and value.endswith("}")) or (
                            value.startswith("[") and value.endswith("]")
                        ):
                            row_dict[col_name] = json.loads(value)
                        else:
                            row_dict[col_name] = value
                    except json.JSONDecodeError:
                        row_dict[col_name] = value  # Keep as string if not valid JSON
                else:
                    row_dict[col_name] = value

                # Track bytes processed (rough estimation)
                if isinstance(value, (str, bytes)):
                    bytes_processed += len(
                        str(value)
                    )  # len(bytes(value, 'utf-8')) for more accuracy
                elif isinstance(value, (int, float)):
                    bytes_processed += 8  # Approx size for numeric types
                elif isinstance(value, bool):
                    bytes_processed += 1  # Approx size for boolean
                elif (
                    value is not None
                ):  # For other types, estimate based on string representation
                    bytes_processed += len(str(value))

            # Validate and normalize phone numbers in the row data
            row_dict = validate_and_normalize_phone_numbers_in_data(row_dict)
            query_results.append(row_dict)

        conn.close()

        # bytes processed and rows processed are not used in the BigQuery emulator - can be enable in future implementaitons
        # return {"query_results": query_results, "bytes_processed": bytes_processed, "rows_processed": rows_processed}

        return {"query_results": query_results}

    except Exception as e:
        if conn:  # Ensure connection is closed if error occurs after opening
            conn.close()
        # Refine error message for "no such table"
        if "no such table" in str(e):
            raise InvalidQueryError(
                f"Table '{table_id}' not found in dataset '{project_id}.{dataset_id}'. SQLite error: {e}"
            )
        raise InvalidQueryError(
            f"SQLite execution error: {e}. Query: {sqlite_query[:200]}..."
        )
