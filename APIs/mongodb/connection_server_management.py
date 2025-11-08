from common_utils.tool_spec_decorator import tool_spec
# === connection_server_management.py ===
from typing import Any, Optional, Dict

# Assuming DB is correctly set up and available.
from .SimulationEngine.db import DB
# Import custom errors
from .SimulationEngine.custom_errors import InvalidInputError, ConnectionError
from .SimulationEngine.models import SwitchConnectionResponse

@tool_spec(
    spec={
        'name': 'switch_connection',
        'description': """ Switch to a different MongoDB connection.
        
        Switches to a different MongoDB connection. If the user has configured a
        connection string or has previously called the connect tool, a connection
        is already established, and there is no need to call this function unless
        the user has explicitly requested to switch to a new instance. Options for
        switching the current MongoDB connection can be provided via the
        `connectionString` parameter. If a `connectionString` argument is not
        supplied, the function will attempt to use a connection string from the
        existing configuration. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'connectionString': {
                    'type': 'string',
                    'description': """ MongoDB connection string to switch to
                    (in the mongodb:// or mongodb+srv:// format). Defaults to None,
                    in which case a default connection string will be used. """
                }
            },
            'required': []
        }
    }
)
def switch_connection(connectionString: Optional[str] = None) -> Dict[str, Any]:
    """Switch to a different MongoDB connection.

    Switches to a different MongoDB connection. If the user has configured a
    connection string or has previously called the connect tool, a connection
    is already established, and there is no need to call this function unless
    the user has explicitly requested to switch to a new instance. Options for
    switching the current MongoDB connection can be provided via the
    `connectionString` parameter. If a `connectionString` argument is not
    supplied, the function will attempt to use a connection string from the
    existing configuration.

    Args:
        connectionString (Optional[str]): MongoDB connection string to switch to
            (in the mongodb:// or mongodb+srv:// format). Defaults to None,
            in which case a default connection string will be used.

    Returns:
        Dict[str, Any]: Indicates the outcome of the connection switch attempt.
            This dictionary contains the following keys:
            status (str): 'success' if the switch was successful, 'failure'
                otherwise.
            message (Optional[str]): A descriptive message about the connection
                attempt (e.g., error details on failure, or success
                confirmation).
            active_connection_info (Optional[str]): Information about the new
                active connection if the switch was successful (e.g., a
                masked connection string, server version, database name, or
                an alias).

    Raises:
        InvalidInputError: If the provided connectionString is empty, contains
            only whitespace, or does not start with 'mongodb://' or 'mongodb+srv://'.
        ConnectionError: If the connection cannot be established by the DB layer
            (e.g., actual connection failure, issues with the "default" target).
    """
    target_connection: str
    status: str
    
    # Validate the provided connectionString sequentially  
    if connectionString is None:
        target_connection = "mongodb://default"
    else:
        target_connection = connectionString
      
    if not isinstance(connectionString, str):
        raise InvalidInputError("Provided connection string must be a string.")

    if not connectionString.strip(): # Check for empty or all-whitespace string
        raise InvalidInputError(
            "Connection string cannot be empty or contain only whitespace."
        )
    
    if not (connectionString.startswith("mongodb://") or connectionString.startswith("mongodb+srv://")):
            result = SwitchConnectionResponse(
                status = "failure",
                message = "Connection failed! Invalid MongoDB connection string format: Must start with 'mongodb://' or 'mongodb+srv://'.",
            )
            return result.model_dump()
    
    if connectionString == DB.current_conn:
        result = SwitchConnectionResponse(
            status = "failure",
            message = f"Connection failed! {connectionString} is already the current connection."
        )
        return result.model_dump()
   
    target_connection = connectionString

    try:
        # DB.switch_connection is now called with either a validated non-empty string,
        # or "mongodb://default".
        result = DB.switch_connection(target_connection)
    except Exception:
        # Catch any exception from DB.switch_connection and wrap it in our custom ConnectionError.
        raise ConnectionError(f"Failed to switch connection to '{target_connection}'")
    
    result = SwitchConnectionResponse(
        status = result["status"],
        message = result["message"],
        active_connection_info = f"Current connection now is {DB.current_conn}.",
    )
    return result.model_dump()
