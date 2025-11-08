"""
Project Reports Module

This module provides functionality for managing and retrieving project reports
in the Workday Strategic Sourcing system. It supports operations for retrieving
both individual project report entries and all project report entries, as well
as the associated schema definitions.

The module interfaces with the simulation database to provide access to project
report data, which includes comprehensive information about projects, their
status, milestones, and associated metadata.

Functions:
    get_project_report_entries: Retrieves entries for a specific project report
    get_entries: Retrieves all project report entries
    get_schema: Retrieves the schema definition for project reports
"""

from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine import db
from typing import Dict, Any, List
from .SimulationEngine.custom_errors import NotFoundError 

@tool_spec(
    spec={
        'name': 'get_project_report_entries_by_id',
        'description': """ Retrieves a list of report entries for a specified project report.
        
        Accepts an optional project_report_id parameter in newer API versions (2019-01-01 and later). Use this to scope results to a particular report. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_report_id': {
                    'type': 'integer',
                    'description': 'Unique identifier of the project report.'
                }
            },
            'required': [
                'project_report_id'
            ]
        }
    }
)
def get_project_report_entries(project_report_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves a list of report entries for a specified project report.

    Accepts an optional project_report_id parameter in newer API versions (2019-01-01 and later). Use this to scope results to a particular report.

    Args:
        project_report_id (int): Unique identifier of the project report.

    Returns:
        List[Dict[str, Any]]: A list of project report entries containing:
            - type (str): Always "project_report_entries".
            - id (int): Unique identifier for the project report entry.
            - attributes (Dict[str, Any]): All relevant report entry data.

    """

    return db.DB["reports"].get(f'project_reports_{project_report_id}_entries', [])

@tool_spec(
    spec={
        'name': 'list_user_owned_project_report_entries',
        'description': """ Retrieves a list of project report entries owned by the user.
        
        Deprecated: This endpoint is only available for API version `2018-04-01`. It has been removed in versions released after `2019-01-01`. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_entries() -> Dict[str, Any]:
    """
    Retrieves a list of project report entries owned by the user.

    Deprecated: This endpoint is only available for API version `2018-04-01`. It has been removed in versions released after `2019-01-01`.

    Returns:
        Dict[str, Any]: A paginated list of project report entries.

            - data (List[Dict[str, Any]]): Report entries list.
                - type (str): Always "project_report_entries".
                - id (Union[str, int]): Unique identifier for the project report entry.
                - attributes (Dict[str, Any]): All relevant report entry data.

            - links (Dict[str, Optional[str]]):
                - next (str|None): URL to the next page of results.
                - prev (str|None): URL to the previous page of results.
    """

    return db.DB["reports"]["project_reports_entries"]

@tool_spec(
    spec={
        'name': 'get_project_report_schema',
        'description': """ Retrieves the schema definition for project report entries.
        
        The schema provides metadata about the fields used in project reports, including
        field names and data types. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_schema() -> Dict[str, Any]:
    """
    Retrieves the schema definition for project report entries.

    The schema provides metadata about the fields used in project reports, including
    field names and data types.

    Returns:
        Dict[str, Any]: Schema definition for project report entries. It can contain the following keys:
            - id (str): Field type definition for the ID property.
            - project_id (str): Field type definition for the project ID property.
            - summary (str): Field type definition for the summary property.

    Raises:
        NotFoundError: If the project reports schema is not found in the
                             database.
    """
    try:
        return db.DB["reports"]["project_reports_schema"]
    except KeyError:
        raise NotFoundError(
            "Project reports schema could not be found in the database."
        )

    
