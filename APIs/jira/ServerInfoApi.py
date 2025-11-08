from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/ServerInfoApi.py
from typing import Dict, Any
from datetime import datetime, timezone
from .SimulationEngine.db import DB


@tool_spec(
    spec={
        'name': 'get_server_info',
        'description': """ Get server information.
        
        Retrieves comprehensive server information including version, URLs, build details,
        and current server time. This endpoint provides essential metadata about the 
        Jira server instance. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_server_info() -> Dict[str, Any]:
    """
    Get server information.

    Retrieves comprehensive server information including version, URLs, build details,
    and current server time. This endpoint provides essential metadata about the 
    Jira server instance.

    Returns:
        Dict[str, Any]: A dictionary containing server information:
            - version (str): The version of the Jira server software
            - deploymentTitle (str): The deployment title/name of the server
            - buildNumber (int): The build number of the server
            - buildDate (str): Date when the server was built (YYYY-MM-DD format)
            - baseUrl (str): The base URL of the Jira server
            - versions (List[str]): Version numbers as an array of strings [major, minor, patch]
            - deploymentType (str): The type of deployment (e.g., "Server")
            - serverTime (str): Current server time in ISO 8601 format with timezone offset

    Raises:
        RuntimeError: If server_info configuration is missing from the database
    """
    # Ensure server_info exists in DB
    if "server_info" not in DB:
        raise RuntimeError("Server information is not configured in the database")
    
    server_info = DB["server_info"].copy()
    
    # Generate current server time dynamically with timezone offset
    current_time = datetime.now(timezone.utc)
    server_info["serverTime"] = current_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+0000"
    
    return server_info
