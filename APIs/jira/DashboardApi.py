from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/DashboardApi.py

from .SimulationEngine.db import DB
from typing import Optional, Dict, Any


@tool_spec(
    spec={
        'name': 'get_all_dashboards',
        'description': """ Retrieve a list of dashboards from Jira.
        
        This method returns a list of all dashboards in the system, with optional
        pagination support. Dashboards are used to display various Jira data and
        metrics in a customizable layout. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'startAt': {
                    'type': 'integer',
                    'description': """ The index of the first dashboard to return.
                    Defaults to 0. """
                },
                'maxResults': {
                    'type': 'integer',
                    'description': """ The maximum number of dashboards to return.
                    If not specified, all dashboards will be returned. """
                }
            },
            'required': []
        }
    }
)
def get_dashboards(
    startAt: Optional[int] = 0, maxResults: Optional[int] = None
) -> Dict[str, Any]:
    """
    Retrieve a list of dashboards from Jira.

    This method returns a list of all dashboards in the system, with optional
    pagination support. Dashboards are used to display various Jira data and
    metrics in a customizable layout.

    Args:
        startAt (Optional[int]): The index of the first dashboard to return.
            Defaults to 0.
        maxResults (Optional[int]): The maximum number of dashboards to return.
            If not specified, all dashboards will be returned.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - dashboards (List[Dict[str, Any]]): A list of dashboard objects,
                each containing:
                - id (str): The unique identifier for the dashboard
                - name (str): The name of the dashboard
                - self (str): The URL of the dashboard
                - view (str): The URL of the dashboard

    Raises:
        ValueError: If the startAt is less than 0, maxResults is less than 0.
        TypeError: If the startAt or maxResults is not a valid integer
    """
    # input validation
    if not isinstance(startAt, int):
        raise TypeError("startAt must be a valid integer")
    if startAt < 0:
        raise ValueError("startAt must not be negative")
    if maxResults and not isinstance(maxResults, int):
        raise TypeError("maxResults must be a valid integer")
    if maxResults and maxResults < 0:
        raise ValueError("maxResults must not be negative")
    
    # get all dashboards from the database
    all_dashboards = list(DB["dashboards"].values())
    
    # filter dashboards by startAt and maxResults
    if startAt:
        all_dashboards = all_dashboards[startAt:]
    if maxResults:
        all_dashboards = all_dashboards[:maxResults]
    
    return {"dashboards": all_dashboards}


@tool_spec(
    spec={
        'name': 'get_dashboard_by_id',
        'description': """ Retrieve a specific dashboard by its ID.
        
        This method returns detailed information about a specific dashboard
        identified by its unique ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'dash_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the dashboard to retrieve'
                }
            },
            'required': [
                'dash_id'
            ]
        }
    }
)
def get_dashboard(dash_id: str) -> Dict[str, Any]:
    """
    Retrieve a specific dashboard by its ID.

    This method returns detailed information about a specific dashboard
    identified by its unique ID.

    Args:
        dash_id (str): The unique identifier of the dashboard to retrieve

    Returns:
        Dict[str, Any]: A dictionary containing:
            - id (str): The unique identifier for the dashboard
            - name (str): The name of the dashboard
            - self (str): The URL of the dashboard
            - view (str): The URL of the dashboard

    Raises:
        ValueError: If the dashboard does not exist
    """
    # input validation
    if not isinstance(dash_id, str):
        raise ValueError("dash_id must be a string")
        
    if dash_id.strip() == "":
        raise ValueError("dash_id cannot be empty")
    
    # get dashboard from the database by dash_id
    dash = DB["dashboards"].get(dash_id)
    if not dash:
        raise ValueError(f"Dashboard '{dash_id}' not found.")
    return dash
