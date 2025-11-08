from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any

from .SimulationEngine import utils
from .SimulationEngine.db import DB
from .SimulationEngine import custom_errors 

@tool_spec(
    spec={
        'name': 'list_databases',
        'description': 'List all databases for a MongoDB connection.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def list_databases() -> List[Dict[str, Any]]:
    """
    List all databases for a MongoDB connection.
 
    Returns:
        List[Dict[str, Any]]: A list of database information dictionaries. Each dictionary contains:
            name (str): The name of the database.
            size_on_disk (float): The total size of the database on disk in bytes.

    Raises:
        ConnectionError: If no active connection or invalid connection.
        ValueError: If no active connection or invalid connection.
    """
    try:
        # Check if there's an active connection
        if not DB.current_conn:
            raise custom_errors.ConnectionError("No active MongoDB connection.")

        if DB.current_conn not in DB.connections:
            raise custom_errors.ConnectionError("Invalid MongoDB connection.")

        connection = DB.connections[DB.current_conn]
        database_names = connection.list_database_names()
        # Get database sizes
        database_sizes = utils._get_database_sizes(connection, database_names)

        response = []
        for db_name, size in database_sizes.items():
            response.append({
                "name": db_name,
                "size_on_disk": size
            })      
        return response
    except ValueError as e:
        # Re-raise ValueError (e.g., no active connection)
        raise e

@tool_spec(
    spec={
        'name': 'drop_database',
        'description': """ Removes the specified database, deleting the associated data files.
        
        This function removes the specified database. In doing so, it deletes
        the associated data files. """,
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
def drop_database(database: str) -> Dict[str, List[Dict[str, str]]]:
    """Removes the specified database, deleting the associated data files.

    This function removes the specified database. In doing so, it deletes
    the associated data files.

    Args:
        database (str): Database name.

    Returns:
        Dict[str, List[Dict[str, str]]]: A dictionary with the following keys:
            "content" (List[Dict[str, str]]): A list containing a single dictionary with the following keys:
                "text" (str): A human-readable message describing the result, such as 'Successfully dropped database "mydb"' or 'Failed to drop database "mydb"'.
                "type" (str): The type of content, always set to 'text'.

    Raises:
        ConnectionError: If no active connection or invalid connection.
        TypeError: If database name is not a string.
        ValueError: If database name is empty or whitespace.
    """
    if not database:
        raise ValueError("Database name cannot be empty.")
    if not isinstance(database, str):
        raise TypeError("Database name must be a string.")
    if database.isspace():
        raise ValueError("Database name cannot be empty.")
    if not DB.current_conn:
        raise ConnectionError("No active MongoDB connection.")
    if DB.current_conn not in DB.connections:
        raise ConnectionError("Invalid MongoDB connection.")

    client = utils.get_active_connection()
    if client is None:
        raise ConnectionError("Failed to retrieve an active MongoDB client instance.")
    
    try:
        # Perform the drop database operation using the MongoDB client.
        client.drop_database(database)
        
        if DB.current_db is not None and DB.current_db == database:
            DB.current_db = None

        message = f'Successfully dropped database "{database}"'
    except Exception as e:
        message = f'Failed to drop database "{database}"'

    return {"content": [{"text": message, "type": "text"}]}