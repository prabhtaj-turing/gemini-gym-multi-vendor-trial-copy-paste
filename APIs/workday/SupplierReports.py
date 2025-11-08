"""
Supplier Reports Management Module

This module provides functionality for managing supplier reports in the Workday
Strategic Sourcing system. It supports operations for retrieving supplier report
entries and their associated schema.

The module interfaces with the simulation database to provide comprehensive
report management capabilities, allowing users to:
- Retrieve all supplier report entries
- Access the supplier report schema definition
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'list_supplier_report_entries',
        'description': 'This function retrieves all supplier report entries.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_entries() -> List[Dict[str, Any]]:
    """
    This function retrieves all supplier report entries.

    Returns:
        List[Dict[str, Any]]: A list of supplier report entries. Each entry is a dictionary containing the following fields:
            - type (str): Always "supplier_report_entries".
            - id (str): Unique identifier of the supplier report entry.
            - attributes (Dict[str, Any]): Attributes of the supplier report entry.

    """
    
    return db.DB["reports"].get('supplier_reports_entries', [])

@tool_spec(
    spec={
        'name': 'get_supplier_report_schema',
        'description': """ Returns the supplier report schema.
        
        This function retrieves the schema definition for supplier reports, including
        field names, types, and metadata that describe how supplier report entries are structured. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_schema() -> Dict[str, Any]:
    """
    Returns the supplier report schema.

    This function retrieves the schema definition for supplier reports, including
    field names, types, and metadata that describe how supplier report entries are structured.

    Returns:
        Dict[str, Any]: A dictionary containing the supplier report schema definition.
            - id (str): Schema object ID, always "supplier_schemas".
            - type (str): Object type, always "supplier_schemas".
            - attributes (Dict[str, List[Dict[str, str]]]): Attributes of the schema object containing:
                - fields (List[Dict[str, str]]): List of field definitions containing:
                    - type (str): Field type. Allowed values: "text", "date", "integer", "select", "string".
                    - name (str): Name of the field.
    """

    return db.DB["reports"].get('supplier_reports_schema', {}) 