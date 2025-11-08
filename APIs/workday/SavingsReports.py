"""
Savings Reports Management Module

This module provides functionality for managing savings reports in the Workday Strategic
Sourcing system. It supports operations for retrieving savings report entries and their
associated schema definitions.

The module interfaces with the simulation database to provide access to savings report
data, which includes detailed information about cost savings, financial metrics, and
related reporting information.

Functions:
    get_entries: Retrieves all savings report entries from the system
    get_schema: Retrieves the schema definition for savings reports
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'list_savings_report_entries',
        'description': """ Retrieves a list of savings report entries.
        
        Returns all savings-related entries available in the system. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_entries() -> List[Dict[str, Any]]:
    """
    Retrieves a list of savings report entries.

    Returns all savings-related entries available in the system.

    Returns:
        List[Dict[str, Any]]: A list of savings report entry objects, each containing:
            - id (str): Unique identifier for the savings report entry
            - project_id (str): Associated project identifier  
            - savings_amount (int): Amount of savings in the base currency
            
        Returns an empty list if no savings report entries are found.
    """

    return db.DB["reports"].get('savings_reports_entries', [])

@tool_spec(
    spec={
        'name': 'get_savings_report_schema',
        'description': """ Retrieves the schema definition for the savings report.
        
        The schema provides field names and their data types used in the savings report entries. This is useful for understanding the expected structure and available data fields when creating or interpreting report entries. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_schema() -> Dict[str, Any]:
    """
    Retrieves the schema definition for the savings report.

    The schema provides field names and their data types used in the savings report entries. This is useful for understanding the expected structure and available data fields when creating or interpreting report entries.


    Returns:
        Dict[str, Any]: A dictionary mapping field names to their data types:
            - id (str): Field type for the report entry identifier
            - project_id (str): Field type for the associated project identifier  
            - savings_amount (str): Field type for the savings amount (specified as "integer")
            
        Returns an empty dictionary if no schema definition is found.
    """

    return db.DB["reports"].get('savings_reports_schema', {}) 