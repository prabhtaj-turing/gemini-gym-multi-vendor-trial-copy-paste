"""
This module provides functionality for managing event templates in the Workday
Strategic Sourcing system. It supports retrieving a list of all event templates
and getting specific template details by ID.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Optional, Any
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'list_event_templates',
        'description': """ Returns a list of all event templates.
        
        This function safely retrieves event templates from the database.
        If the required data structure is not present, it returns an empty list. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> List[Dict[str, Any]]:
    """Returns a list of all event templates.

    This function safely retrieves event templates from the database.
    If the required data structure is not present, it returns an empty list.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary
        represents an event template with the following keys:
            - name (str): The name of the event template.
            - description (str): The detailed description of the event template.
    """
    
    event_templates = db.DB.get("events", {}).get("event_templates", {})
    result = []

    for template in event_templates.values():
        if isinstance(template, dict) and "name" in template and "description" in template:
            result.append({
                "name": template["name"],
                "description": template["description"]
            })
    
    return result

@tool_spec(
    spec={
        'name': 'get_event_template_by_id',
        'description': 'Retrieves the details of an existing event template by its ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': """ The unique internal identifier of the event template to retrieve.
                    Must be a positive integer. """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_by_id(id: int) -> Optional[Dict]:
    """Retrieves the details of an existing event template by its ID.

    Args:
        id (int): The unique internal identifier of the event template to retrieve.
                  Must be a positive integer.

    Returns:
        Optional[Dict]: A dictionary containing the event template details if found,
                        including any of the following keys:
                            - type (str): Object type, should always be "event_templates"
                            - id (str): Event template identifier string
                            - attributes (dict): Event template attributes containing:
                                - title (str): Event template title (max 255 characters)
                                - event_type (str): Event type enum ("RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT", "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT")
                            - links (dict): Related links containing:
                                - self (str): Normalized link to the resource
            
    Raises:
        TypeError: If the provided id is not an integer.
        ValueError: If the provided id is not positive.
        ValueError: If the provided id is not found in the db
    """
    if not isinstance(id, int):
        raise TypeError(f"Expected id to be an integer, got {type(id).__name__}")
    
    if id <= 0:
        raise ValueError(f"Expected id to be a positive integer, got {id}")
        
    template = db.DB["events"]["event_templates"].get(id, None)
    
    if not template:
        raise ValueError(f"No Event template found for the provided")

    # Define the keys that are allowed in the public response.
    # This creates a strict contract.
    allowed_keys = ["type", "id", "attributes", "links"]
    
    # Build the final output by filtering the template object.
    # This prevents leaking any extra internal fields from the database.
    filtered_template = {key: template.get(key) for key in allowed_keys}

    return filtered_template
