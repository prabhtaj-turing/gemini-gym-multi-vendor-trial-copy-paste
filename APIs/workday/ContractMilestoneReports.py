"""
Contract Milestone Reports Management Module for Workday Strategic Sourcing API Simulation.

This module provides functionality for managing and retrieving contract milestone
reports in the Workday Strategic Sourcing system. It supports operations for
accessing milestone report entries and their associated schema definitions. The
module enables comprehensive tracking and reporting of contract milestones and
their associated metrics.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any
from .SimulationEngine import db
from requests.exceptions import HTTPError
import os

@tool_spec(
    spec={
        'name': 'list_contract_milestone_report_entries',
        'description': """ Retrieves a list of contract milestone report entries.
        
        Returns paginated milestone entries submitted under contract reports. Used for tracking progress or performance milestones across contracts. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_entries() -> List[Dict[str, Any]]:
    """
    Retrieves a list of contract milestone report entries.

    Returns paginated milestone entries submitted under contract reports. Used for tracking progress or performance milestones across contracts.

    Returns:
        List[Dict[str, Any]]: A paginated list of contract milestone report entries.

            - data (List[Dict[str, Any]]): List of milestone entries.
                - type (str): Always "contract_milestone_report_entries".
                - id (str): Milestone report entry identifier.
                - attributes (Dict[str, Any]): Milestone-specific field values.

            - links (Dict[str, Optional[str]]): Pagination controls.
                - next (Optional[str]): URL to fetch next result set.
                - prev (Optional[str]): URL to fetch previous result set.

    """
    # Get entries from database
    entries = db.DB["reports"].get('contract_milestone_reports_entries', [])
    
    # Format entries to match documented structure
    formatted_entries = []
    for entry in entries:
        if isinstance(entry, dict) and 'id' in entry:
            # Extract fields that should be in attributes
            attributes = {}
            for key, value in entry.items():
                if key != 'id':  # Keep id separate as it's a top-level field
                    attributes[key] = value
                    
            formatted_entry = {
                "type": "contract_milestone_report_entries",
                "id": entry['id'],
                "attributes": attributes
            }
            formatted_entries.append(formatted_entry)
    
    # Return with the structure promised by the docstring
    return {
        "data": formatted_entries,
        "links": {
            "next": None,  # Would be a URL in real implementation
            "prev": None   # Would be a URL in real implementation
        }
    }


@tool_spec(
    spec={
        'name': 'get_contract_milestone_report_schema',
        'description': """ Retrieves the contract milestone report schema.
        
        The schema defines the structure and expected data types for each field in a contract milestone report entry. 
        This information is useful for dynamically generating forms, validating input, or formatting report data. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_schema() -> Dict[str, Any]:
    """
    Retrieves the contract milestone report schema.

    The schema defines the structure and expected data types for each field in a contract milestone report entry. 
    This information is useful for dynamically generating forms, validating input, or formatting report data.

    Returns:
        Dict[str, Any]: Schema describing contract milestone report fields.

            - data (Dict[str, Any]):
                - id (str): Unique schema identifier. Always "contract_milestone_schemas".
                - type (str): Resource type. Always "contract_milestone_schemas".
                - attributes (Dict[str, Any]):
                    - fields (List[Dict[str, Any]]): List of schema field definitions.
                        - type (str): Field data type. One of: "text", "date", "integer", "select", "string".
                        - name (str): Human-readable name of the field.

    """
    # If authentication is valid, return the schema
    result = db.DB["reports"].get('contract_milestone_reports_schema', {})
    
    # Validate the structure of the returned data
    if not result or not isinstance(result, dict):
        result = {
            "data": {
                "id": "contract_milestone_schemas",
                "type": "contract_milestone_schemas",
                "attributes": {
                    "fields": []
                }
            }
        }
    
    return result 