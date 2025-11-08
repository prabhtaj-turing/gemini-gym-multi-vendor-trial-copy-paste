"""
This module provides functionality for retrieving the schema and field definitions
of bid line items in the Workday Strategic Sourcing system. It enables users to
understand the structure and available fields of bid line item objects.
"""

from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine import db
from .SimulationEngine.custom_errors import DatabaseSchemaError, ResourceNotFoundError

@tool_spec(
    spec={
        'name': 'describe_bid_line_items_fields',
        'description': """ Retrieves the list of available fields for bid line item objects.
        
        This function returns a comprehensive list of all fields that can be present
        in a bid line item object, based on the schema definition in the system. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> list[str]:
    """Retrieves the list of available fields for bid line item objects.

    This function returns a comprehensive list of all fields that can be present
    in a bid line item object, based on the schema definition in the system.

    Returns:
        list[str]: A list of strings, where each string represents a field name
            available in bid line item objects. The list includes:
            - "event_id" (str): The ID of the associated event.
            - "description" (str): Description of the line item.
            - "amount" (float): Monetary amount for the line item.

    Raises:
        DatabaseSchemaError: If the 'events' or 'bid_line_items' sections are missing from the database.
        ResourceNotFoundError: If no bid line items exist in the database.

    Note:
        The function uses the first bid line item in the database as a template
        to determine the available fields. This assumes that all bid line items
        share the same schema structure.
    """
    # Check if 'events' section exists in the database
    if 'events' not in db.DB:
        raise DatabaseSchemaError("Missing 'events' section in the database")
    
    # Check if 'bid_line_items' section exists within events
    if 'bid_line_items' not in db.DB['events']:
        raise DatabaseSchemaError("Missing 'bid_line_items' section in the events database")
    
    bid_line_items = db.DB['events']['bid_line_items']
    
    # Check if any bid line items exist
    if not bid_line_items:
        raise ResourceNotFoundError("No bid line items exist in the database")
    
    # Get the first bid line item as a template for the schema
    first_bid_line_item_id = list(bid_line_items.keys())[0]
    return list(bid_line_items[first_bid_line_item_id].keys())
