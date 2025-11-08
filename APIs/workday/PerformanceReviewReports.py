"""
Performance Review Reports Module

This module provides functionality for managing and retrieving performance review reports
in the Workday Strategic Sourcing system. It supports operations for retrieving both the
report entries and the associated schema definitions.

The module interfaces with the simulation database to provide access to performance review
report data, which includes comprehensive information about performance reviews, their
status, and associated metadata.

Functions:
    get_entries: Retrieves a list of all performance review report entries
    get_schema: Retrieves the schema definition for performance review reports
"""

from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine import db
from typing import List, Dict, Any
from .SimulationEngine.custom_errors import EntriesNotFoundError, SchemaNotFoundError

@tool_spec(
    spec={
        'name': 'list_performance_review_report_entries',
        'description': """ Retrieves a list of performance review report entries.
        
        Returns detailed performance review report data in a paginated format. 
        Each entry contains attributes related to a performance review. 
        Use pagination links to iterate through results. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_entries() -> List[Dict[str, Any]]:
    """
    Retrieves a list of performance review report entries.

    Returns detailed performance review report data in a paginated format. 
    Each entry contains attributes related to a performance review. 
    Use pagination links to iterate through results.

    Returns:
        List[Dict[str, Any]]: A list of performance review report entries.
            Each entry contains:
                - type (str): Always "performance_review_report_entries".
                - id (Any): Unique identifier for the report entry.
                - attributes (Dict[str, Any]): Key-value pairs for the report entry data.

    Raises:
        EntriesNotFoundError: If no entries are found in the in-memory DB or if entries format is invalid.
    """
    try:
        entries = db.DB["reports"]["performance_review_reports_entries"]
        # Validate that entries is a list
        if not isinstance(entries, list):
            raise EntriesNotFoundError("Performance review report entries format is invalid.")
        return entries
    except KeyError:
        raise EntriesNotFoundError("Performance review report entries not found.")

@tool_spec(
    spec={
        'name': 'get_performance_review_report_schema',
        'description': """ Retrieves the schema for the performance review report.
        
        The schema defines the structure of performance review report entries, including field types and names.
        This is useful for dynamically building forms, validating input, or rendering reports. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_schema() -> Dict[str, Any]:
    """
    Retrieves the schema for the performance review report.

    The schema defines the structure of performance review report entries, including field types and names.
    This is useful for dynamically building forms, validating input, or rendering reports.

    Returns:
        Dict[str, Any]: Schema definition containing field names as keys and their data types as string values.
                        Expected structure:
                            - id (str): Field type for the performance review ID
                            - employee_id (str): Field type for the employee identifier
                            - summary (str): Field type for the performance review summary

    Raises:
        SchemaNotFoundError: If the schema is missing in the database.
    """
    try:
        return db.DB["reports"]["performance_review_reports_schema"]
    except KeyError:
        raise SchemaNotFoundError("Performance review schema not found in the database.")
