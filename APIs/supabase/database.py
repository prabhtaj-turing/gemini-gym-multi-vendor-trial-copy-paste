from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any, Optional
from pydantic import ValidationError as PydanticValidationError
from datetime import datetime , timezone
from .SimulationEngine.db import DB
from .SimulationEngine import utils, models, custom_errors
from .SimulationEngine.duckdb_manager import get_duckdb_manager






@tool_spec(
    spec={
        'name': 'list_extensions',
        'description': """ Lists all extensions in the database.
        
        This function lists all extensions in the database associated with the specified project. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'The identifier of the project.'
                }
            },
            'required': [
                'project_id'
            ]
        }
    }
)
def list_extensions(project_id: str) -> List[Dict[str, Any]]:
    """Lists all extensions in the database.

    This function lists all extensions in the database associated with the specified project.

    Args:
        project_id (str): The identifier of the project.

    Returns:
        List[Dict[str, Any]]: A list of database extensions. Each dictionary in the list
            represents an extension and contains the following fields:
            name (str): The name of the extension.
            schema (str): The schema where the extension is installed.
            version (str): The version of the extension.
            description (str): A description of the extension.

    Raises:
        NotFoundError: If the project_id does not exist.
        ValidationError: If input arguments fail validation.
    """
    try:
        _ = models.ListExtensionsInput(project_id=project_id)
    except PydanticValidationError:
        raise custom_errors.ValidationError("Input should be a valid string")
    
    cleaned_project_id = project_id.strip()

    project = utils.get_entity_by_id(DB['projects'], cleaned_project_id)
    if not project:
        raise custom_errors.NotFoundError(f"Project with id '{cleaned_project_id}' not found.")

    # Retrieve the list of extensions associated with the cleaned_project_id.
    project_extensions_data = DB['extensions'].get(cleaned_project_id, [])

    # Format the raw extension data into the specified response structure.
    response_extensions = []
    for ext_data in project_extensions_data:
        formatted_extension = {
            "name": ext_data["name"],
            "schema": ext_data["schema"],
            "version": ext_data["version"],
            "description": ext_data["description"],
        }
        response_extensions.append(formatted_extension)

    return response_extensions



@tool_spec(
    spec={
        'name': 'execute_sql',
        'description': """ Executes raw SQL in the Postgres database. Use `apply_migration` instead for DDL operations.
        
        This function implements PostgreSQL query execution for the Supabase API.
        All operations are performed in-memory with no persistence between sessions.
        
        Supported SQL Operations:
        - SELECT queries with WHERE, JOIN, GROUP BY, HAVING, ORDER BY, LIMIT
        - INSERT statements (single and multiple rows)
        - UPDATE statements with WHERE conditions
        - DELETE statements with WHERE conditions
        - Basic DDL: CREATE TABLE, ALTER TABLE, DROP TABLE
        - Transaction commands: BEGIN, COMMIT, ROLLBACK
        - Multi-schema support (e.g., public.users, analytics.products)
        
        Supported Data Types:
        - Text types: TEXT, VARCHAR, CHAR
        - Numeric types: INTEGER, BIGINT, SMALLINT, DECIMAL, NUMERIC, REAL, DOUBLE
        - Boolean: BOOLEAN
        - Date/Time: DATE, TIME, TIMESTAMP, TIMESTAMP WITH TIME ZONE
        - UUID (stored as VARCHAR internally)
        - JSON/JSONB (stored as JSON)
        - SERIAL/BIGSERIAL types (converted to INTEGER/BIGINT, auto-increment not supported)
        
        PostgreSQL Compatibility Notes:
        - SERIAL/BIGSERIAL columns are converted to INTEGER/BIGINT (manual ID management required)
        - PostgreSQL functions like now() and uuid_generate_v4() are automatically converted
        - Foreign key constraints across different schemas are not supported
        - Type OIDs in responses are approximated based on common PostgreSQL types
        
        Limitations:
        - PostgreSQL-specific functions are limited (e.g., array functions, full-text search)
        - Advanced features like CTEs and window functions have limited support
        - Stored procedures, functions, and triggers are not supported
        - PostgreSQL extensions (postgis, pg_trgm, etc.) are not available
        - Transaction isolation levels are not enforced
        - Constraints are partially supported (PRIMARY KEY works, CHECK constraints work, but foreign keys have limitations)
        - No support for COPY, VACUUM, ANALYZE, or other maintenance commands
        - Limited support for advanced index types (only basic indexes work)
        - Sequences and auto-increment functionality not available
        - User-defined types and domains are not supported """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'The project ID.'
                },
                'query': {
                    'type': 'string',
                    'description': 'The SQL query to execute.'
                }
            },
            'required': [
                'project_id',
                'query'
            ]
        }
    }
)
def execute_sql(project_id: str, query: str) -> Dict[str, Any]:
    """Executes raw SQL in the Postgres database. Use `apply_migration` instead for DDL operations.
    
    This function implements PostgreSQL query execution for the Supabase API.
    All operations are performed in-memory with no persistence between sessions.
    
    Supported SQL Operations:
    - SELECT queries with WHERE, JOIN, GROUP BY, HAVING, ORDER BY, LIMIT
    - INSERT statements (single and multiple rows)
    - UPDATE statements with WHERE conditions
    - DELETE statements with WHERE conditions
    - Basic DDL: CREATE TABLE, ALTER TABLE, DROP TABLE
    - Transaction commands: BEGIN, COMMIT, ROLLBACK
    - Multi-schema support (e.g., public.users, analytics.products)
    
    Supported Data Types:
    - Text types: TEXT, VARCHAR, CHAR
    - Numeric types: INTEGER, BIGINT, SMALLINT, DECIMAL, NUMERIC, REAL, DOUBLE
    - Boolean: BOOLEAN
    - Date/Time: DATE, TIME, TIMESTAMP, TIMESTAMP WITH TIME ZONE
    - UUID (stored as VARCHAR internally)
    - JSON/JSONB (stored as JSON)
    - SERIAL/BIGSERIAL types (converted to INTEGER/BIGINT, auto-increment not supported)
    
    PostgreSQL Compatibility Notes:
    - SERIAL/BIGSERIAL columns are converted to INTEGER/BIGINT (manual ID management required)
    - PostgreSQL functions like now() and uuid_generate_v4() are automatically converted
    - Foreign key constraints across different schemas are not supported
    - Type OIDs in responses are approximated based on common PostgreSQL types
    
    Limitations:
    - PostgreSQL-specific functions are limited (e.g., array functions, full-text search)
    - Advanced features like CTEs and window functions have limited support
    - Stored procedures, functions, and triggers are not supported
    - PostgreSQL extensions (postgis, pg_trgm, etc.) are not available
    - Transaction isolation levels are not enforced
    - Constraints are partially supported (PRIMARY KEY works, CHECK constraints work, but foreign keys have limitations)
    - No support for COPY, VACUUM, ANALYZE, or other maintenance commands
    - Limited support for advanced index types (only basic indexes work)
    - Sequences and auto-increment functionality not available
    - User-defined types and domains are not supported
    
    Args:
        project_id (str): The project ID.
        query (str): The SQL query to execute.
    
    Returns:
        Dict[str, Any]: The result of the SQL query execution. The structure of this dictionary varies based on the type of SQL query executed.
            
            For SELECT queries, this dictionary typically contains:
            `rows`: List[Dict[str, Any]] - A list of dictionaries, where each dictionary represents a data row. In each row dictionary, keys are column names (str) and values are the corresponding cell data (Any).
            `columns`: List[Dict[str, Any]] - A list of dictionaries, each describing a column in the result set. Each column dictionary has the following keys:
                `name`: str - The name of the column.
                `type_oid`: int - The PostgreSQL Object Identifier (OID) for the column's data type.
            `row_count`: int - The number of rows returned by the SELECT query.
            
            For Data Manipulation Language (DML) statements (e.g., INSERT, UPDATE, DELETE), this dictionary typically contains:
            `row_count`: int - The number of rows affected by the DML statement.
            `status_message`: str - A status message from the database indicating the outcome of the DML operation (e.g., 'INSERT 0 1', 'UPDATE 5').
    
    Raises:
        NotFoundError: If the project_id does not exist.
        InvalidInputError: If the query is missing or malformed.
        DatabaseConnectionError: If there's an issue connecting to the project's database.
        SQLError: If the SQL query is invalid, encounters a runtime error during execution, or violates database constraints.
    """
    # Validate inputs
    if not project_id:
        raise custom_errors.InvalidInputError("The project_id parameter cannot be null or empty")
    
    if not isinstance(project_id, str):
        raise custom_errors.InvalidInputError("project_id must be a string")
    
    if not query:
        raise custom_errors.InvalidInputError("The query parameter cannot be null or empty")
    
    if not isinstance(query, str):
        raise custom_errors.InvalidInputError("query must be a string")
    
    # Check if query is just whitespace
    if not query.strip():
        raise custom_errors.InvalidInputError("The query parameter cannot be empty or contain only whitespace")
    
    # Check if project exists
    project = utils.get_entity_by_id_from_db(DB, "projects", project_id)
    if not project:
        raise custom_errors.NotFoundError(f"Project with id '{project_id}' not found")
    
    # Validate project state for SQL execution
    if not utils.validate_project_for_sql_execution(DB, project_id):
        project_status = project.get("status", "UNKNOWN")
        raise custom_errors.DatabaseConnectionError(
            f"Cannot execute SQL on project '{project_id}' in status '{project_status}'. "
            f"Project must be in ACTIVE status."
        )
    
    # Get DuckDB manager and execute query
    db_manager = get_duckdb_manager()
    
    try:
        result = db_manager.execute_query(project_id, query)
        
        # The DuckDB manager already returns the result in the correct format
        # For SELECT: {"rows": [...], "columns": [...], "row_count": n}
        # For DML: {"row_count": n, "status_message": "..."}
        
        # Validate the result structure using our models
        if "rows" in result:
            # SELECT query result
            validated_result = models.SQLSelectResult(**result)
            return validated_result.model_dump()
        elif "status_message" in result:
            # DML or DDL result
            if result.get("status_message") == "OK":
                validated_result = models.SQLDDLResult(**result)
            else:
                validated_result = models.SQLDMLResult(**result)
            return validated_result.model_dump()
        else:
            # Shouldn't happen, but handle gracefully
            return result
            
    except custom_errors.DatabaseConnectionError:
        # Re-raise as is
        raise
    except custom_errors.SQLError:
        # Re-raise as is
        raise
    except Exception as e:
        # Catch any unexpected errors and wrap them
        raise custom_errors.SQLError(f"Unexpected error during query execution: {str(e)}") 
    

@tool_spec(
    spec={
        'name': 'apply_migration',
        'description': """ Applies a migration to the database.
        
        Applies a migration to the database. Use this when executing DDL operations.
        Do not hardcode references to generated IDs in data migrations. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'The ID of the project.'
                },
                'name': {
                    'type': 'string',
                    'description': 'The name of the migration in snake_case.'
                },
                'query': {
                    'type': 'string',
                    'description': 'The SQL query to apply.'
                }
            },
            'required': [
                'project_id',
                'name',
                'query'
            ]
        }
    }
)
def apply_migration(project_id: str, name: str, query: str) -> Dict[str, Any]:
    """Applies a migration to the database.

    Applies a migration to the database. Use this when executing DDL operations.
    Do not hardcode references to generated IDs in data migrations.

    Args:
        project_id (str): The ID of the project.
        name (str): The name of the migration in snake_case.
        query (str): The SQL query to apply.

    Returns:
        Dict[str, Any]: Result of the migration application, detailing its outcome.
                        Contains the following fields:
            version (str): The version identifier of the applied migration,
                           used for tracking (often derived from name or timestamp).
            name (str): The name of the applied migration.
            status (str): Status of the migration (e.g., 'APPLIED_SUCCESSFULLY',
                          'FAILED').
            message (Optional[str]): Any relevant messages from the migration
                                     process, such as error details if it failed.

    Raises:
        NotFoundError: If the project_id does not exist.
        ValidationError: If the migration name or query is invalid or missing.
        MigrationError: If the migration query fails to apply (e.g., SQL syntax
                        error, conflicts with existing schema, transaction rollback).
    """

    # Validate project_id type and emptiness
    if not isinstance(project_id, str):
        raise custom_errors.ValidationError("Project ID must be a string.")
    if not project_id:
        raise custom_errors.ValidationError("Project ID cannot be empty.")

    # Validate migration name type and emptiness
    if not isinstance(name, str):
        raise custom_errors.ValidationError("Migration name must be a string.")
    if not name:
        raise custom_errors.ValidationError("Migration name cannot be empty.")
    

    # Validate migration query type and emptiness
    if not isinstance(query, str):
        raise custom_errors.ValidationError("Migration query must be a string.")
    if not query:
        raise custom_errors.ValidationError("Migration query cannot be empty.")

    # Check if project exists
    project_list = DB.get("projects", [])
    project = utils.get_entity_by_id(project_list, project_id)
    if not project:
        raise custom_errors.NotFoundError(f"Project with ID '{project_id}' not found.")

    # Prepare migration metadata
    applied_time = datetime.now(timezone.utc)
    # Generate a version identifier using timestamp and unique ID for robustness
    unique_id = utils.generate_unique_id()[:8]  # Use first 8 characters for brevity
    migration_version = f"{applied_time.strftime('%Y%m%d%H%M%S%f')}_{name}_{unique_id}"


    # Check that migrations structure exists for the project
    if project_id not in DB["migrations"]:
        raise custom_errors.NotFoundError(f"No migrations found for project '{project_id}'. Project may not be properly initialized.")
    
    project_migrations_list = DB["migrations"][project_id]
    
    # Execute the migration using our real SQL engine
    migration_status: str
    error_message: str = None
    
    try:
        # Use execute_sql to run the migration query
        # This gives us real SQL validation and execution
        execute_sql(project_id, query)
        
        # If we get here, the migration executed successfully
        migration_status = "APPLIED_SUCCESSFULLY"
        
        migration_record = {
            "version": migration_version,
            "name": name,
            "status": migration_status,
            "applied_at": applied_time,
            "query": query
        }
        project_migrations_list.append(migration_record)

        # Prepare the successful return payload
        return_payload = {
            "version": migration_version,
            "name": name,
            "status": "APPLIED_SUCCESSFULLY",
            "message": None 
        }
        return return_payload
        
    except (custom_errors.SQLError, custom_errors.DatabaseConnectionError) as e:
        # Migration failed due to SQL execution error
        migration_status = "FAILED"
        error_message = str(e)
        
        migration_record = {
            "version": migration_version,
            "name": name,
            "status": migration_status,
            "applied_at": applied_time,
            "query": query
        }
        project_migrations_list.append(migration_record)
        
        # Raise MigrationError with details from the SQL execution
        raise custom_errors.MigrationError(f"Migration '{name}' failed: {error_message}")
    
    except Exception as e:
        # Unexpected error during migration execution
        migration_status = "FAILED"
        error_message = str(e)
        
        migration_record = {
            "version": migration_version,
            "name": name,
            "status": migration_status,
            "applied_at": applied_time,
            "query": query
        }
        project_migrations_list.append(migration_record)
        
        # Raise MigrationError for any unexpected errors
        raise custom_errors.MigrationError(f"Migration '{name}' failed with unexpected error: {error_message}")



@tool_spec(
    spec={
        'name': 'list_migrations',
        'description': """ Lists all migrations in the database.
        
        This function lists all migrations in the database associated with the provided project_id. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'The identifier of the project.'
                }
            },
            'required': [
                'project_id'
            ]
        }
    }
)
def list_migrations(project_id: str) -> List[Dict[str, Any]]:
    """Lists all migrations in the database.

    This function lists all migrations in the database associated with the provided project_id.

    Args:
        project_id (str): The identifier of the project.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a database migration and includes the following keys:
            version (str): The version identifier of the migration (often a timestamp).
            name (str): The descriptive name of the migration.
            status (str): The status of the migration (e.g., 'applied', 'pending').
            applied_at (Optional[str]): ISO 8601 timestamp of when the migration was applied, if applicable.

    Raises:
        NotFoundError: If the project_id does not exist.
        PydanticValidationError: If input arguments fail validation.
    """
    try:
        # Validate the input project_id.
        # This ensures project_id is strictly a string. An empty string is permissible here;
        # its existence as a project ID will be checked later.
        models.ListMigrationsArgsValidator(project_id=project_id)
    except PydanticValidationError:
        # Re-raise Pydantic's validation error as a custom ValidationError
        # with a generic message as expected by tests.
        raise

    # Verify that the project exists.
    # DB['projects'] is expected to be a list of project dictionaries.
    # Note: Assumes DB['projects'] exists. If it might not, further checks are needed.
    if not utils.get_entity_by_id(DB.get('projects', []), project_id): # Added DB.get for safety
        raise custom_errors.NotFoundError("Object not found.") # Changed message

    # Retrieve migrations associated with the project_id.
    # DB.get('migrations', {}) handles cases where 'migrations' key might be missing from DB.
    # .get(project_id, []) gracefully handles cases where the project has no migrations
    # or if the project_id key itself is missing from the migrations mapping.
    project_migrations_data = DB.get('migrations', {}).get(project_id, [])

    formatted_migrations: List[Dict[str, Any]] = []
    for migration_data in project_migrations_data:
        # The Migration schema in the DB defines 'applied_at' as Optional[datetime].
        applied_at_value = migration_data.get('applied_at')
        applied_at_iso_str: Optional[str] = None

        if isinstance(applied_at_value, datetime):
            applied_at_iso_str = applied_at_value.isoformat()
        elif applied_at_value is not None:
            # This case implies applied_at_value is present but not a datetime object,
            # which is inconsistent with the DB schema's type hint (Optional[datetime]).
            # Such an entry might indicate a data integrity issue.
            # The current handling ensures applied_at_iso_str remains None,
            # adhering to the Optional[str] return type for 'applied_at'.
            # In a production system, logging this anomaly would be advisable.
            pass # applied_at_iso_str remains None as initialized

        # Construct the migration item dictionary for the return list.
        # Fields 'version', 'name', 'status' are defined as non-optional strings
        # in the Migration DB schema. Direct dictionary access (e.g., migration_data['version'])
        # assumes these fields are always present.
        try:
            migration_item = {
                'version': migration_data['version'],
                'name': migration_data['name'],
                'status': migration_data['status'],
                'applied_at': applied_at_iso_str
            }
            formatted_migrations.append(migration_item)
        except KeyError:
            # This block is executed if a mandatory field ('version', 'name', or 'status')
            # is missing from migration_data. This indicates a malformed migration record
            # relative to the expected schema.
            # Skipping such malformed records makes the function more robust.
            # For diagnostic purposes, logging could be added here.
            continue
            
    return formatted_migrations

@tool_spec(
    spec={
        'name': 'list_tables',
        'description': """ Lists all tables in one or more schemas.
        
        This function lists all tables found within one or more specified schemas for a given project.
        If the `schemas` parameter is not provided, it defaults to listing tables from all available schemas
        associated with the `project_id`. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'The identifier of the project.'
                },
                'schemas': {
                    'type': 'array',
                    'description': 'List of schemas to include. Defaults to all schemas if None.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'project_id'
            ]
        }
    }
)
def list_tables(project_id: str, schemas: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Lists all tables in one or more schemas.

    This function lists all tables found within one or more specified schemas for a given project.
    If the `schemas` parameter is not provided, it defaults to listing tables from all available schemas
    associated with the `project_id`.

    Args:
        project_id (str): The identifier of the project.
        schemas (Optional[List[str]]): List of schemas to include. Defaults to all schemas if None.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary (representing a table object)
        details a single table and includes the following keys:
            name (str): The name of the table.
            schema (str): The schema the table belongs to.
            comment (Optional[str]): The comment associated with the table, if any.
            columns (List[Dict[str, Any]]): A list of column dictionaries detailing the table's columns.
                Each column dictionary contains:
                    name (str): The name of the column.
                    data_type (str): The data type of the column.
                    is_nullable (bool): Indicates if the column can contain NULL values.
                    default_value (Optional[str]): The default value of the column, if any.
            primary_keys (List[Dict[str, Any]]): A list of dictionaries representing primary key columns.
                Each primary key dictionary contains:
                    name (str): The name of the primary key column.
            relationships (List[Dict[str, Any]]): A list of dictionaries detailing foreign key relationships.
                Each relationship dictionary contains:
                    constraint_name (str): The name of the foreign key constraint.
                    source_schema (str): The schema of the table containing the foreign key.
                    source_table_name (str): The name of the table containing the foreign key.
                    source_column_name (str): The name of the column in the source table that is part of the foreign key.
                    target_table_schema (str): The schema of the table referenced by the foreign key.
                    target_table_name (str): The name of the table referenced by the foreign key.
                    target_column_name (str): The name of the column in the target table referenced by the foreign key.

    Raises:
        NotFoundError: If the project_id does not exist.
        ValidationError: If input arguments fail validation.
    """
    # Input validation for basic types.
    if not isinstance(project_id, str):
        raise custom_errors.ValidationError("Input validation failed: project_id must be a string.")
    
    if schemas is not None:
        if not isinstance(schemas, list):
            raise custom_errors.ValidationError("Input validation failed: schemas must be a list of strings or None.")
        if not all(isinstance(s, str) for s in schemas):
            raise custom_errors.ValidationError("Input validation failed: all elements in schemas list must be strings.")

    # Check if the project exists using the utility function.
    project = utils.get_entity_by_id_from_db(DB, "projects", project_id)
    if not project:
        raise custom_errors.NotFoundError(f"Project with ID '{project_id}' not found.")

    db_tables = utils.get_tables_by_project_and_schemas(DB, project_id, schemas)

    result_tables: List[Dict[str, Any]] = []
    for db_table_dict in db_tables:
        processed_columns = []
        # Robustly get column data: use `or []` to ensure iteration over an empty list
        # if "columns" is missing or its value is None.
        db_column_data_list = db_table_dict.get("columns") or []
        for col_data in db_column_data_list:
            # Ensure each column dictionary in the output has the 'default_value' key.
            processed_columns.append({
                "name": col_data["name"],
                "data_type": col_data["data_type"],
                "is_nullable": col_data["is_nullable"],
                "default_value": col_data.get("default_value") 
            })
        
        table_output = {
            "name": db_table_dict["name"],
            "schema": db_table_dict["schema"],
            "comment": db_table_dict.get("comment"),
            "columns": processed_columns,
            # Robustly get primary_keys and relationships: use `or []` to default to an empty list
            # if the key is missing or its value is None.
            "primary_keys": db_table_dict.get("primary_keys") or [],
            "relationships": db_table_dict.get("relationships") or [],
        }
        result_tables.append(models.Table(**table_output).model_dump())

    return result_tables
