from common_utils.print_log import print_log
from common_utils.phone_utils import normalize_phone_number
"""
Utility functions for BigQuery API simulation.

This module provides helper functions for the BigQuery API simulation, including:
- Type conversions between BigQuery and SQLite
- Table name parsing and validation
- Database operations and management
- File operations for JSON storage

Dependencies:
    - json: For JSON file operations
    - os: For file operations
    - sqlite3: For database operations
    - datetime: For timestamp handling
    - typing: For type hints

Related Modules:
    - query_executor.py: Uses these utilities for query execution
    - db.py: Uses these utilities for database operations
    - models.py: Provides data models used by these utilities
    - errors.py: Provides exceptions used by these utilities
"""

import tempfile
from datetime import datetime, timezone
import time
import json
import os
import sqlite3
from typing import Any, Dict, Optional, List

from .models import BigQueryDatabase, Table, FieldMode
from .custom_errors import InvalidInputError
from .db import DB

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Get the directory where this file (utils.py) is located
_UTILS_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the root directory (2 levels up from utils.py)
_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(_UTILS_DIR)))
# Default database path relative to the root directory
_DEFAULT_DB_PATH: str = os.path.join(_ROOT_DIR, "DBs", "BigQueryDefaultDB.json")
_DEFAULT_SQLITE_DB_DIR: str = os.path.join(_UTILS_DIR, "bq_emulator_data")

def set_default_db_path(path: str) -> None:
    """Set the default database path.
    
    Args:
        path (str): Path to the default database file
    
    Raises:
        FileNotFoundError: If the specified path does not exist
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Database file not found: {path}")
    global _DEFAULT_DB_PATH
    _DEFAULT_DB_PATH = path

def get_default_db_path() -> str:
    """Get the current default database path.
    
    Returns:
        str: Path to the default database file
    """
    return _DEFAULT_DB_PATH

def get_default_sqlite_db_dir() -> str:
    """Get the current default SQLite database directory.

    Returns:
        str: Path to the SQLite database directory
    """
    return _DEFAULT_SQLITE_DB_DIR

def bq_type_to_sqlite_type(bq_type_obj: Dict[str, str]) -> str:
    """Convert BigQuery type to SQLite type.
    
    Args:
        bq_type_obj (Dict[str, str]): BigQuery type object with 'type' key
    
    Returns:
        str: Corresponding SQLite type
    
    Example:
        >>> bq_type_to_sqlite_type({"type": "STRING"})
        'TEXT'
        >>> bq_type_to_sqlite_type({"type": "INT64"})
        'INTEGER'
    """
    type_map = {
        "STRING": "TEXT",
        "INT64": "INTEGER",
        "FLOAT64": "REAL",
        "BOOLEAN": "INTEGER",
        "TIMESTAMP": "TEXT",
        "DATE": "TEXT",
        "DATETIME": "TEXT",
        "TIME": "TEXT",
        "BYTES": "BLOB",
        "NUMERIC": "REAL",
        "BIGNUMERIC": "REAL",
        "JSON": "TEXT",
        "GEOGRAPHY": "TEXT",
        "ARRAY": "TEXT",
        "STRUCT": "TEXT"
    }
    return type_map.get(bq_type_obj.get("type", ""), "TEXT")

def get_current_timestamp_ms() -> int:
    """Get current timestamp in milliseconds.
    
    Returns:
        int: Current timestamp in milliseconds since epoch
    
    Example:
        >>> timestamp = get_current_timestamp_ms()
        >>> isinstance(timestamp, int)
        True
    """
    return int(datetime.now(timezone.utc).timestamp() * 1000)

def get_table_from_path(db: BigQueryDatabase, table_path: str) -> Optional[Table]:
    """Get a table from the database using its full path.
    
    Args:
        db (BigQueryDatabase): The database to search in
        table_path (str): Full path to the table (project.dataset.table)
    
    Returns:
        Optional[Table]: The found table or None if not found
    
    Example:
        >>> table = get_table_from_path(db, "my-project.my_dataset.my_table")
        >>> if table:
        ...     print(table.metadata.table_id)
        'my_table'
    """
    project_id, dataset_id, table_id = parse_full_table_name(table_path)
    for project in db.projects:
        if project.project_id == project_id:
            for dataset in project.datasets:
                if dataset.dataset_id == dataset_id:
                    for table in dataset.tables:
                        if table.metadata.table_id == table_id:
                            return table
    return None

def convert_timestamp_to_milliseconds(timestamp: Optional[datetime]) -> Optional[int]:
    """Convert datetime to milliseconds since epoch.
    
    Args:
        timestamp (Optional[datetime]): Datetime to convert
    
    Returns:
        Optional[int]: Milliseconds since epoch or None if input is None
    
    Example:
        >>> dt = datetime.now(timezone.utc)
        >>> ms = convert_timestamp_to_milliseconds(dt)
        >>> isinstance(ms, int)
        True
    """
    if timestamp is None:
        return None
    return int(timestamp.timestamp() * 1000)

def format_table_metadata(table: Table) -> Dict[str, Any]:
    """Format table metadata into the standard output format.
    
    Args:
        table (Table): The table to format
    
    Returns:
        Dict[str, Any]: Formatted table metadata
            - table_id (str): The table ID
            - dataset_id (str): The dataset ID
            - project_id (str): The project ID
            - type (str): The table type
            - creation_time (int): The creation time in milliseconds
            - last_modified_time (int): The last modified time in milliseconds
            - expiration_time (int): The expiration time in milliseconds
            - num_rows (int): The number of rows in the table
            - size_bytes (int): The size of the table in bytes
            - schema (Dict[str, Any]): The schema of the table
                - fields (List[Dict[str, Any]]): The fields in the schema
                    - name (str): The name of the field
                    - type (str): The type of the field
                    - mode (str): The mode of the field
                    - description (str): The description of the field
                    - fields (List[Dict[str, Any]]): The fields in the schema
    
    Example:
        >>> metadata = format_table_metadata(table)
        >>> print(metadata['table_id'])
        'my_table'
    """
    return {
        'table_id': table.metadata.table_id,
        'dataset_id': table.metadata.dataset_id,
        'project_id': table.metadata.project_id,
        'type': table.metadata.type,
        'creation_time': convert_timestamp_to_milliseconds(table.metadata.creation_time),
        'last_modified_time': convert_timestamp_to_milliseconds(table.metadata.last_modified_time),
        'expiration_time': convert_timestamp_to_milliseconds(table.metadata.expiration_time),
        'num_rows': table.metadata.num_rows,
        'size_bytes': table.metadata.size_bytes,
        'schema': {
            'fields': [
                {
                    'name': field.name,
                    'type': field.type,
                    'mode': field.mode,
                    'description': field.description,
                    'fields': field.fields
                }
                for field in table.metadata.fields
            ]
        }
    }

def find_table_by_name(db: BigQueryDatabase, table_name: str) -> Optional[Table]:
    """Find a table by its name across all projects and datasets.
    
    Args:
        db (BigQueryDatabase): The database to search in
        table_name (str): Name of the table to find
    
    Returns:
        Optional[Table]: The found table or None if not found
    
    Example:
        >>> table = find_table_by_name(db, "my_table")
        >>> if table:
        ...     print(table.metadata.table_id)
        'my_table'
    """
    for project in db.projects:
        for dataset in project.datasets:
            for table in dataset.tables:
                if table.metadata.table_id == table_name:
                    return table
    return None

def get_table_size_info(table: Table) -> Dict[str, Any]:
    """Get size information for a table.
    
    Args:
        table (Table): The table to analyze
    
    Returns:
        Dict[str, Any]: Dictionary containing size information:
            - num_rows (int): Number of rows in the table
            - size_bytes (int): Size of the table in bytes
            - avg_row_size (float): Average size of a row in bytes
    
    Example:
        >>> info = get_table_size_info(table)
        >>> print(f"Table has {info['num_rows']} rows")
        'Table has 100 rows'
    """
    num_rows = len(table.rows)
    size_bytes = sum(len(str(row).encode('utf-8')) for row in table.rows)
    avg_row_size = size_bytes / num_rows if num_rows > 0 else 0
    
    return {
        'num_rows': num_rows,
        'size_bytes': size_bytes,
        'avg_row_size': avg_row_size
    }

def is_table_expired(table: Table) -> bool:
    """Check if a table has expired.
    
    Args:
        table (Table): The table to check
    
    Returns:
        bool: True if the table has expired, False otherwise
    
    Example:
        >>> if is_table_expired(table):
        ...     print("Table has expired")
    """
    if not table.metadata.expiration_time:
        return False
    return datetime.now(timezone.utc) > table.metadata.expiration_time

def get_table_age(table: Table) -> Optional[float]:
    """Get the age of a table in days since creation.
    
    Args:
        table (Table): The table to check
    
    Returns:
        Optional[float]: Age in days or None if creation_time is not available
    
    Example:
        >>> age = get_table_age(table)
        >>> if age is not None:
        ...     print(f"Table is {age:.1f} days old")
    """
    if not table.metadata.creation_time:
        return None
    age = datetime.now(timezone.utc) - table.metadata.creation_time
    return age.total_seconds() / (24 * 3600)  # Convert to days 

def parse_full_table_name(full_table_name: str) -> tuple[str, str, str]:
    """Parse a full table name in format 'project.dataset.table'.
    
    Args:
        full_table_name: The full table name to parse
        
    Returns:
        Tuple of (project_id, dataset_id, table_id)
        
    Raises:
        InvalidInputError: If the table name format is invalid or contains invalid characters
    """
    if not full_table_name:
        raise InvalidInputError("Table name cannot be empty")

    parts = full_table_name.split('.')
    if len(parts) != 3:
        raise InvalidInputError(f"Invalid table name format: '{full_table_name}'. Expected 'project.dataset.table'.")

    project_id, dataset_id, table_id = parts

    # Check for empty parts
    if not project_id:
        raise InvalidInputError("Project ID cannot be empty")
    if not dataset_id:
        raise InvalidInputError("Dataset ID cannot be empty")
    if not table_id:
        raise InvalidInputError("Table ID cannot be empty")

    # Check for invalid characters (excluding hyphens)
    invalid_chars = set(' !@#$%^&*()+=[]{}|\\:;"\'<>,?/')
    
    # Check each part for invalid characters
    for part, part_name in [(project_id, "Project ID"), (dataset_id, "Dataset ID"), (table_id, "Table ID")]:
        if any(c in invalid_chars for c in part):
            raise InvalidInputError(f"{part_name} contains invalid characters: '{part}'")

    return project_id, dataset_id, table_id

def initialize_sqlite_db(project_id: str, dataset_id: str) -> None:
    """Initialize SQLite database for a project and dataset.
    
    Args:
        project_id (str): The project ID
        dataset_id (str): The dataset ID
        
    Raises:
        ValueError: If the specified project or dataset is not found in the default database.
    
    Example:
        >>> initialize_sqlite_db("my-project", "my_dataset")
    """
    # Create directory if it doesn't exist
    os.makedirs(get_default_sqlite_db_dir(), exist_ok=True)
    
    # Load default database
    with open(_DEFAULT_DB_PATH, 'r') as f:
        db_data = json.load(f)
    
    # Find project and dataset
    project = None
    dataset = None
    for p in db_data["projects"]:
        if p["project_id"] == project_id:
            project = p
            for d in p["datasets"]:
                if d["dataset_id"] == dataset_id:
                    dataset = d
                    break
            break
    
    if not project or not dataset:
        raise ValueError(f"Project {project_id} or dataset {dataset_id} not found in default database")
    
    # Create SQLite database
    db_path = os.path.join(get_default_sqlite_db_dir(), f"{project_id}_{dataset_id}.db")
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            # If we can't remove it, try to close any open connections
            try:
                conn_temp = sqlite3.connect(db_path)
                conn_temp.close()
                time.sleep(1)  # Give time for connections to close
                os.remove(db_path)
            except:
                pass  # If we still can't remove it, we'll try to overwrite it
    
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables and insert data
        for table in dataset["tables"]:
            # Create table with schema
            columns = []
            for field in table["schema"]:
                sql_type = bq_type_to_sqlite_type({"type": field["type"]})
                nullable = "" if field["mode"] == "REQUIRED" else "NULL"
                columns.append(f'"{field["name"]}" {sql_type} {nullable}')
            
            # Quote table name to handle hyphens
            table_id = f'"{table["table_id"]}"'
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_id} (
                {', '.join(columns)}
            )
            """
            cursor.execute(create_table_sql)
            
            # Insert rows
            if table["rows"]:
                placeholders = ", ".join(["?"] * len(table["schema"]))
                insert_sql = f"""
                INSERT INTO {table_id}
                ({', '.join(f'"{field["name"]}"' for field in table["schema"])})
                VALUES ({placeholders})
                """
                
                for row in table["rows"]:
                    values = []
                    for field in table["schema"]:
                        value = row.get(field["name"])
                        if field["type"] == "JSON" and value is not None:
                            value = json.dumps(value)
                        values.append(value)
                    cursor.execute(insert_sql, values)
        
        conn.commit()
    finally:
        if conn:
            conn.close()

def create_table_schema(table: Table) -> str:
    """Generate SQLite CREATE TABLE statement from BigQuery table schema.
    
    Args:
        table (Table): The BigQuery table to create schema for
    
    Returns:
        str: SQLite CREATE TABLE statement
    
    Example:
        >>> schema = create_table_schema(table)
        >>> print(schema)
        'CREATE TABLE IF NOT EXISTS "my_table" (id INTEGER, name TEXT NULL)'
    """
    columns = []
    for field in table.metadata.fields:
        sql_type = bq_type_to_sqlite_type({"type": field.type})
        nullable = "" if field.mode == FieldMode.REQUIRED else "NULL"
        columns.append(f'"{field.name}" {sql_type} {nullable}')
    
    return f"""
    CREATE TABLE IF NOT EXISTS "{table.metadata.table_id}" (
        {', '.join(columns)}
    )
    """

def load_database_from_json(json_path: str) -> BigQueryDatabase:
    """Load a BigQuery database from a JSON file.
    
    Args:
        json_path (str): Path to the JSON file
    
    Returns:
        BigQueryDatabase: The loaded database
    
    Raises:
        FileNotFoundError: If the JSON file is not found
        ValueError: If the JSON file is invalid
        ValidationError: If the JSON file does not match the BigQueryDatabase schema
    
    Example:
        >>> db = load_database_from_json("my_database.json")
        >>> print(f"Loaded {len(db.projects)} projects")
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Database file not found: {json_path}")
    
    with open(json_path, 'r') as f:
        db_data = json.load(f)
    
    return BigQueryDatabase(**db_data)

def load_db_dict_to_sqlite(DB: Dict[str, Any]) -> sqlite3.Connection:
    """
    Convert a BigQuery-style in-memory dictionary into an SQLite database.

    Args:
        DB (Dict[str, Any]): The in-memory dictionary structured like BigQuery emulator data.

    Returns:
        sqlite3.Connection: SQLite connection to the temporary database with all tables created and populated.
    """
    projects_list = DB.get('projects', [])
    if not isinstance(projects_list, list):
        pass


    temp_db_path = os.path.join(tempfile.gettempdir(), "bq_emulator.db")
    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
        except OSError as e:
            print_log(f"Warning: Could not remove old temp DB {temp_db_path}: {e}")

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    for project_entry in projects_list:
        for dataset in project_entry.get("datasets", []):
            for table in dataset.get("tables", []):
                table_id = table["table_id"]
                schema = table["schema"]
                rows = table.get("rows", [])

                columns_sql_definitions = []
                column_processing_info = [] 

                for field in schema:
                    name = field["name"]
                    bq_type = field["type"].upper() 
                    quoted_name = f'"{name}"' 

                    sqlite_type = "TEXT" 
                    if bq_type == "STRING": sqlite_type = "TEXT"
                    elif bq_type == "INT64": sqlite_type = "INTEGER"
                    elif bq_type in ["NUMERIC", "BIGNUMERIC", "FLOAT64"]: sqlite_type = "REAL"
                    elif bq_type == "BOOLEAN": sqlite_type = "INTEGER" 
                    elif bq_type in ["TIMESTAMP", "DATE", "DATETIME", "TIME"]: sqlite_type = "TEXT"
                    elif bq_type == "BYTES": sqlite_type = "BLOB"
                    elif bq_type in ["JSON", "ARRAY", "STRUCT"]: sqlite_type = "TEXT"
                    
                    columns_sql_definitions.append(f'{quoted_name} {sqlite_type}')
                    column_processing_info.append({"name": name, "bq_type": bq_type, "quoted_name": quoted_name})

                create_sql = f'CREATE TABLE IF NOT EXISTS "{table_id}" ({", ".join(columns_sql_definitions)});'
                try:
                    cursor.execute(create_sql)
                except sqlite3.OperationalError as e:
                    print_log(f"Error creating table {table_id}: {e}. SQL: {create_sql}")
                    continue 

                if rows:
                    col_names_for_insert_sql = [info['quoted_name'] for info in column_processing_info]
                    placeholders = ", ".join(["?"] * len(col_names_for_insert_sql))
                    insert_sql = f'INSERT INTO "{table_id}" ({", ".join(col_names_for_insert_sql)}) VALUES ({placeholders})'

                    for row_idx, row_data in enumerate(rows):
                        values_for_sql: List[Any] = [] # Explicitly type as List[Any]
                        for col_info in column_processing_info:
                            raw_value = row_data.get(col_info["name"])

                            if raw_value is None:
                                values_for_sql.append(None)
                            elif col_info["bq_type"] in ["JSON", "ARRAY", "STRUCT"]:
                                if isinstance(raw_value, (dict, list)):
                                    try:
                                        values_for_sql.append(json.dumps(raw_value))
                                    except TypeError:
                                        values_for_sql.append(None) # Store as None if serialization fails
                                else:
                                    # If it's not a dict/list but a text type, store as is, otherwise None
                                    values_for_sql.append(str(raw_value) if isinstance(raw_value, (str, int, float, bool)) else None)
                            elif col_info["bq_type"] == "BOOLEAN":
                                # Handle None for BOOLEAN correctly for nullable booleans
                                values_for_sql.append(1 if raw_value else 0 if raw_value is not None else None)
                            else:
                                values_for_sql.append(raw_value)
                        
                        try:
                            cursor.execute(insert_sql, values_for_sql)
                        except sqlite3.Error as e:
                            print_log(f"Error inserting row into {table_id}: {e}. SQL: {insert_sql}. Values: {values_for_sql}")

    conn.commit()
    return conn

# ---------------------------------------------------------------------------------------
# In-Memory DB Management Functions
# ---------------------------------------------------------------------------------------

def _get_current_utc_timestamp_iso() -> str:
    """Generates the current UTC timestamp in ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def create_project(project_id: str) -> Dict[str, Any]:
    """
    Creates a new project in the global DB if it doesn't exist, or returns the existing one.

    Args:
        project_id (str): The unique identifier for the project.

    Returns:
        Dict[str, Any]: The project dictionary.
    """
    if 'projects' not in DB or not isinstance(DB['projects'], list):
        DB['projects'] = []

    for project in DB['projects']:
        if project.get('project_id') == project_id:
            return project
    
    new_project = {
        'project_id': project_id,
        'datasets': []
    }
    DB['projects'].append(new_project)
    return new_project

def create_dataset(project_id: str, dataset_id: str) -> Dict[str, Any]:
    """
    Creates a new dataset within a project in the global DB if it doesn't exist, 
    or returns the existing one. Creates the project if it doesn't exist.

    Args:
        project_id (str): The ID of the project.
        dataset_id (str): The unique identifier for the dataset within the project.

    Returns:
        Dict[str, Any]: The dataset dictionary.
    """
    project = create_project(project_id) # Ensures project exists

    for dataset in project.get('datasets', []):
        if dataset.get('dataset_id') == dataset_id:
            return dataset
            
    new_dataset = {
        'dataset_id': dataset_id,
        'tables': []
    }
    if 'datasets' not in project: # Should have been initialized by create_project if new
        project['datasets'] = []
    project['datasets'].append(new_dataset)
    return new_dataset

def create_table(
    project_id: str, 
    dataset_id: str, 
    table_id: str, 
    schema: List[Dict[str, Any]], 
    table_type: str = 'TABLE', 
    creation_time: Optional[str] = None, 
    expiration_time: Optional[str] = None
) -> Dict[str, Any]:
    """
    Creates a new table within a dataset in the global DB if it doesn't exist, 
    or returns the existing one. Creates project/dataset if they don't exist.

    Args:
        project_id (str): The ID of the project.
        dataset_id (str): The ID of the dataset.
        table_id (str): The unique identifier for the table within the dataset.
        schema (List[Dict[str, Any]]): A list of dictionaries defining the table schema.
            Each dictionary should represent a field (e.g., 
            {'name': 'col1', 'type': 'STRING', 'mode': 'NULLABLE'}).
        table_type (str, optional): The type of the table. Defaults to 'TABLE'.
        creation_time (Optional[str], optional): ISO 8601 timestamp for creation. 
                                                 Defaults to current UTC time.
        expiration_time (Optional[str], optional): ISO 8601 timestamp for expiration. 
                                                   Defaults to None.

    Returns:
        Dict[str, Any]: The table dictionary.

    """
    dataset = create_dataset(project_id, dataset_id) # Ensures dataset and project exist

    for table in dataset.get('tables', []):
        if table.get('table_id') == table_id:
            return table

    ct_to_use = creation_time or _get_current_utc_timestamp_iso()
    
    new_table = {
        'table_id': table_id,
        'schema': schema,
        'rows': [],
        'type': table_type,
        'creation_time': ct_to_use,
        'last_modified_time': ct_to_use, # Initially, last_modified is same as creation
        'expiration_time': expiration_time,
        # Other metadata like num_rows, size_bytes could be initialized or updated by other functions
    }
    if 'tables' not in dataset: # Should have been initialized by create_dataset if new
        dataset['tables'] = []
    dataset['tables'].append(new_table)
    return new_table

def insert_rows(
    project_id: str, 
    dataset_id: str, 
    table_id: str, 
    rows_to_insert: List[Dict[str, Any]]
) -> bool:
    """
    Inserts one or more rows into an existing table in the global DB.
    Updates the table's last_modified_time.

    Args:
        project_id (str): The ID of the project.
        dataset_id (str): The ID of the dataset.
        table_id (str): The ID of the table.
        rows_to_insert (List[Dict[str, Any]]): A list of dictionaries, where each 
                                               dictionary represents a row.

    Returns:
        bool: True if rows were successfully inserted.

    Raises:
        ValueError: If the specified project, dataset, or table does not exist.
    """
    found_project = None
    if 'projects' in DB and isinstance(DB['projects'], list):
        for project in DB['projects']:
            if project.get('project_id') == project_id:
                found_project = project
                break
    if not found_project:
        raise ValueError(f"Project '{project_id}' not found.")

    found_dataset = None
    for dataset in found_project.get('datasets', []):
        if dataset.get('dataset_id') == dataset_id:
            found_dataset = dataset
            break
    if not found_dataset:
        raise ValueError(f"Dataset '{dataset_id}' not found in project '{project_id}'.")

    found_table = None
    for table in found_dataset.get('tables', []):
        if table.get('table_id') == table_id:
            found_table = table
            break
    if not found_table:
        raise ValueError(f"Table '{table_id}' not found in dataset '{dataset_id}'.")

    if not isinstance(rows_to_insert, list):
        raise ValueError("rows_to_insert must be a list of dictionaries.")
    
    # Validate and normalize phone numbers in the data before insertion
    normalized_rows = []
    for row in rows_to_insert:
        if not isinstance(row, dict):
            raise ValueError("Each item in rows_to_insert must be a dictionary.")
        
        # Normalize phone numbers in the row data
        normalized_row = validate_and_normalize_phone_numbers_in_data(row)
        normalized_rows.append(normalized_row)
    
    if 'rows' not in found_table or not isinstance(found_table['rows'], list):
        found_table['rows'] = [] # Ensure 'rows' key exists and is a list

    found_table['rows'].extend(normalized_rows)
    found_table['last_modified_time'] = _get_current_utc_timestamp_iso()
    
    # Optionally, update num_rows if that metadata is actively maintained
    # found_table['num_rows'] = len(found_table['rows'])
    
    return True

def validate_and_normalize_phone_numbers_in_data(data: Any) -> Any:
    """
    Recursively validates and normalizes phone numbers in data structures.
    
    This function traverses through dictionaries, lists, and other data structures
    to find phone number fields and normalize them to E.164 format.
    
    Args:
        data: The data structure to process (dict, list, or primitive type)
    
    Returns:
        The processed data with normalized phone numbers
    
    Example:
        >>> data = {'phone': '+1-555-0101', 'name': 'John'}
        >>> validate_and_normalize_phone_numbers_in_data(data)
        {'phone': '+15550101', 'name': 'John'}
    """
    if isinstance(data, dict):
        processed_dict = {}
        for key, value in data.items():
            # Check if the key suggests this might be a phone number field
            if isinstance(key, str) and any(phone_indicator in key.lower() for phone_indicator in ['phone', 'tel', 'mobile', 'cell']):
                if isinstance(value, str) and value:
                    normalized = normalize_phone_number(value)
                    if normalized:
                        processed_dict[key] = normalized
                    else:
                        # Keep original value if normalization fails
                        processed_dict[key] = value
                else:
                    processed_dict[key] = value
            else:
                # Recursively process nested structures
                processed_dict[key] = validate_and_normalize_phone_numbers_in_data(value)
        return processed_dict
    elif isinstance(data, list):
        return [validate_and_normalize_phone_numbers_in_data(item) for item in data]
    else:
        return data

def validate_phone_number_field(value: str) -> str:
    """
    Validates a phone number field and returns the normalized E.164 format.
    
    Args:
        value (str): The phone number to validate
    
    Returns:
        str: The normalized phone number in E.164 format
    
    Raises:
        ValueError: If the phone number is invalid
    """
    if not value:
        return value
    
    normalized = normalize_phone_number(value)
    if not normalized:
        raise ValueError(f"Invalid phone number format: {value}")
    
    return normalized
