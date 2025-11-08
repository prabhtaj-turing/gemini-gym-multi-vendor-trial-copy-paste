"""
Event Reports Management Module for Workday Strategic Sourcing API Simulation.

This module provides functionality for managing and retrieving event reports
in the Workday Strategic Sourcing system. It supports operations for accessing
report entries, retrieving specific report data, and managing report schemas.
The module enables users to track and analyze event-related data through
comprehensive reporting capabilities.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any
from .SimulationEngine import db
from .SimulationEngine.custom_errors import SchemaNotFoundError, EntriesNotFoundError

@tool_spec(
    spec={
        'name': 'list_event_report_entries',
        'description': """ Retrieves a list of event report entries.
        
        Event report entries contain detailed records of events captured within the system. These can include audit events, workflow triggers, system updates, etc. The response is paginated and supports traversal through `next` and `prev` links. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_entries() -> List[Dict[str, Any]]:
    """
    Retrieves a list of event report entries.

    Event report entries contain detailed records of events captured within the system. These can include audit events, workflow triggers, system updates, etc. The response is paginated and supports traversal through `next` and `prev` links.

    Returns:
        List[Dict[str, Any]]: A list of event report entries. It can contain the following keys:
            - type (str): Always "event_report_entries".
            - id (str): Unique identifier for the event report.
            - attributes (Dict[str, Any]): Properties of the event report. It can contain the following keys:
                - fields (List[Dict[str, str]]): List of fields present in the schema.
                    - type (str): Field data type.
                        - Enum: "text", "date", "integer", "select", "string"
                    - name (str): Field name used in event reports.

    """

    return db.DB["reports"].get('event_reports_entries', [])

@tool_spec(
    spec={
        'name': 'get_event_report_entries_by_report_id',
        'description': """ Retrieves a list of event report entries for a specific event report.
        
        This endpoint provides detailed entries linked to a single event report, identified by `event_report_id`. 
        It is useful for retrieving scoped data related to a specific event. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'event_report_id': {
                    'type': 'integer',
                    'description': """ Unique identifier for the event report to retrieve entries from.
                    Must be a positive integer. """
                }
            },
            'required': [
                'event_report_id'
            ]
        }
    }
)
def get_event_report_entries(event_report_id: int) -> List[Dict[str, Any]]:
    """
    Retrieves a list of event report entries for a specific event report.

    This endpoint provides detailed entries linked to a single event report, identified by `event_report_id`. 
    It is useful for retrieving scoped data related to a specific event.

    Args:
        event_report_id (int): Unique identifier for the event report to retrieve entries from.
            Must be a positive integer.

    Returns:
        List[Dict[str, Any]]: A list of event report entries tied to the provided report ID. 
        Each entry contains the following keys:
            - id (str): Unique identifier for the event report entry (e.g., "ER1001")
            - event_id (str): Identifier for the associated event (e.g., "EVT001")
            - summary (str): Summary description of the event report entry

    Raises:
        ValueError: If event_report_id is not a positive integer
        EntriesNotFoundError: If no entries are found for the specified event report ID
        SchemaNotFoundError: If the 'reports' collection is not found in the database
    """
    # Input validation
    if not isinstance(event_report_id, int) or event_report_id <= 0:
        raise ValueError("event_report_id must be a positive integer")
    
    try:
        entries = db.DB["reports"].get(f'event_reports_{event_report_id}_entries', [])
        if not entries:
            raise EntriesNotFoundError(f"No entries found for event report ID: {event_report_id}")
        return entries
    except KeyError:
        raise SchemaNotFoundError("The 'reports' collection was not found in the database.")


@tool_spec(
    spec={
        'name': 'list_user_owned_event_report_entries',
        'description': 'Retrieves a list of event report entries owned by the user.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_reports() -> List[Dict[str, Any]]:
    """
    Retrieves a list of event report entries owned by the user.

    Returns:
        List[Dict[str, Any]]: A list of event report entries owned by the user. Each entry is a dictionary
        that can contain the following keys:
            - id (str): Unique identifier for the event report entry.
            - event_id (str): Identifier for the associated event.
            - summary (str): Summary description of the event report.

    Raises:
        SchemaNotFoundError: If the 'reports' collection is not found in the database.
    """
    try:
        # The .get() safely handles a missing 'event_reports' key.
        # The try/except block now handles a missing 'reports' key.
        return db.DB["reports"]["event_reports"]
    except KeyError:
        raise SchemaNotFoundError("The 'reports' collection or 'event_reports' key was not found in the database.")


@tool_spec(
    spec={
        'name': 'get_event_report_schema',
        'description': """ Retrieves the schema definition for event report entries.
        
        This schema provides metadata about the fields available in event report
        entries, including their names and data types. It can be used to
        dynamically interpret and render event report data. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_schema() -> Dict[str, Any]:
    """
    Retrieves the schema definition for event report entries.

    This schema provides metadata about the fields available in event report
    entries, including their names and data types. It can be used to
    dynamically interpret and render event report data.

    Returns:
        Dict[str, Any]: Schema definition for event report entries. It can contain the following keys:
            - id (str): Field type definition for the ID property.
            - event_id (str): Field type definition for the event ID property.
            - summary (str): Field type definition for the summary property.

    Raises:
        SchemaNotFoundError: If the 'reports' key or the 'event_reports_schema' key
                               is not found in the database.
    """
    try:
        return db.DB["reports"]['event_reports_schema']
    except KeyError:
        raise SchemaNotFoundError(
            "The event reports schema could not be found. "
            "Ensure that both 'reports' and 'event_reports_schema' keys exist in the database."
        )