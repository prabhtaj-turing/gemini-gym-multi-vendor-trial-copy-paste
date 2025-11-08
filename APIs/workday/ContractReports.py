"""
Contract Reports Management Module for Workday Strategic Sourcing API Simulation.

This module provides functionality for managing and retrieving contract reports
in the Workday Strategic Sourcing system. It supports operations for accessing
contract report entries and their associated schema definitions. The module
enables comprehensive contract tracking and reporting capabilities.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any, Optional, Union
from .SimulationEngine import db
from .SimulationEngine.models import ContractReportEntry
from pydantic import ValidationError

@tool_spec(
    spec={
        'name': 'get_contract_report_entries',
        'description': """ Retrieves a list of contract report entries.
        
        Contract reports are aggregated data entries related to contract performance, values, timelines, or milestones.
        This endpoint returns all available contract report entries in a simple list format. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_entries() -> List[Dict[str, Any]]:
    """
    Retrieves a list of contract report entries.

    Contract reports are aggregated data entries related to contract performance, values, timelines, or milestones.
    This endpoint returns all available contract report entries in a simple list format.

    Returns:
        List[Dict[str, Any]]: A list of contract report entries. Returns an empty list if no entries are available. Each entry contains:
            - id (str): Unique identifier for the contract report entry (e.g., "CR001")
            - contract_id (str): Reference identifier linking to the associated contract (e.g., "CON001")
            - summary (str): Human-readable description of the contract report status or action
              (e.g., "Contract signed and executed", "Pending approval", "Final amendments completed")

    """

    raw_entries = db.DB["reports"].get('contract_reports_entries', [])
    validated_entries = []

    for entry_data in raw_entries:
        try:
            # Pydantic validates the data here.
            # If successful, it creates a model instance with only the defined fields.
            validated_entry = ContractReportEntry(**entry_data)
            validated_entries.append(validated_entry)
        except ValidationError as e:
            # This entry is malformed (e.g., missing a key, wrong type).
            # We can log this error and skip the entry to return only valid ones.
            print(f"Skipping invalid contract report entry: {entry_data}. Error: {e}")
            continue
            
    return validated_entries

@tool_spec(
    spec={
        'name': 'get_contract_report_schema',
        'description': """ Retrieves the schema definition for contract report entries.
        
        The schema outlines the available fields, their types, and how data is structured within contract reports. 
        This information is useful for dynamically interpreting or building UIs and integrations based on contract data fields. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_schema() -> Dict[str, Any]:
    """
    Retrieves the schema definition for contract report entries.

    The schema outlines the available fields, their types, and how data is structured within contract reports. 
    This information is useful for dynamically interpreting or building UIs and integrations based on contract data fields.

    Returns:
        Dict[str, Any]: Schema structure of the contract report.

            - data (Dict[str, Any]):
                - id (str): Always "contract_schemas".
                - type (str): Always "contract_schemas".
                - attributes (Dict[str, Any]):
                    - fields (List[Dict[str, Any]]): List of available fields.
                        - type (str): Field type. Enum: "text", "date", "integer", "select", "string".
                        - name (str): Name of the field.

    Raises:
        AuthenticationError: Unauthorized – API key or user credentials are missing or invalid.
                             Returns with status code 401.
    """
    # Check for authentication
    if "current_user" not in db.DB or db.DB["current_user"] is None or not db.DB["current_user"]:
        # Import here to avoid circular imports
        from .SimulationEngine.custom_errors import AuthenticationError
        raise AuthenticationError("Unauthorized – API key or user credentials are missing or invalid.", 401)

    return db.DB["reports"].get('contract_reports_schema', {}) 