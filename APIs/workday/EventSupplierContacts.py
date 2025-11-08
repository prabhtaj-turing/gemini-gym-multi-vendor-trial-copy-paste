"""
This module provides functionality for managing supplier contacts associated with
specific events in the Workday Strategic Sourcing system. It supports operations
for adding and removing supplier contacts from events, with a focus on RFP-type
events.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional
from .SimulationEngine import db
from .SimulationEngine.models import SupplierContactData

@tool_spec(
    spec={
        'name': 'add_supplier_contacts_to_event_by_internal_id',
        'description': 'Adds supplier contacts to a specific event. Only events of type RFP are supported.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'integer',
                    'description': """ The unique identifier of the event to which supplier
                    contacts will be added. """
                },
                'data': {
                    'type': 'object',
                    'description': """ A dictionary containing the supplier contact information,
                    including: """,
                    'properties': {
                        'supplier_contact_ids': {
                            'type': 'array',
                            'description': """ A list of supplier contact IDs to be
                                 added to the event """,
                            'items': {
                                'type': 'string'
                            }
                        },
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "supplier_contacts"'
                        }
                    },
                    'required': [
                        'type'
                    ]
                }
            },
            'required': [
                'event_id',
                'data'
            ]
        }
    }
)
def post(event_id: int, data: dict) -> Optional[Dict]:
    """Adds supplier contacts to a specific event. Only events of type RFP are supported.

    Args:
        event_id (int): The unique identifier of the event to which supplier
            contacts will be added.
        data (dict): A dictionary containing the supplier contact information,
            including:
            - supplier_contact_ids (List[str], optional): A list of supplier contact IDs to be
                added to the event
            - type (str): Object type, should always be "supplier_contacts"

    Returns:
        Optional[Dict]: The updated event data if successful, including the newly
            added supplier contacts. Returns None if:
            - The event does not exist
            - The event is not of type RFP
            - The operation fails
            - The input validation fails
    """
    # Validate event_id is an integer
    if not isinstance(event_id, int):
        return None
        
    # Validate data structure using Pydantic model
    try:
        validated_data = SupplierContactData(**data)
    except Exception:
        return None
    
    # Convert integer event_id to string for database lookup since event IDs are stored as strings
    str_event_id = str(event_id)
    if str_event_id not in db.DB["events"]["events"]:
        return None
    event = db.DB["events"]["events"][str_event_id]
    if event.get("type") != "RFP":
        return None
    if "supplier_contacts" not in event:
        event["supplier_contacts"] = []
    event["supplier_contacts"].extend(validated_data.supplier_contact_ids)
    return event

@tool_spec(
    spec={
        'name': 'remove_supplier_contacts_from_event_by_internal_id',
        'description': 'Remove suppliers from an event using supplier contacts. Only events of type RFP are supported.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'integer',
                    'description': """ The unique identifier of the event from which supplier
                    contacts will be removed. """
                },
                'data': {
                    'type': 'object',
                    'description': """ A dictionary containing the supplier contact information,
                    including: """,
                    'properties': {
                        'supplier_contact_ids': {
                            'type': 'array',
                            'description': """ A list of supplier contact IDs to be
                                 removed from the event """,
                            'items': {
                                'type': 'string'
                            }
                        },
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "supplier_contacts"'
                        }
                    },
                    'required': [
                        'type'
                    ]
                }
            },
            'required': [
                'event_id',
                'data'
            ]
        }
    }
)
def delete(event_id: int, data: dict) -> Optional[Dict]:
    """Remove suppliers from an event using supplier contacts. Only events of type RFP are supported.

    Args:
        event_id (int): The unique identifier of the event from which supplier
            contacts will be removed.
        data (dict): A dictionary containing the supplier contact information,
            including:
            - supplier_contact_ids (List[str], optional): A list of supplier contact IDs to be
                removed from the event
            - type (str): Object type, should always be "supplier_contacts"
    Returns:
        Optional[Dict]: The updated event data if successful, with the specified
            supplier contacts removed. Returns None if:
            - The event does not exist
            - The event is not of type RFP
            - The operation fails
    """
    # Validate inputs using Pydantic
    try:
        # Validate that event_id is an int (handled by Python type annotations)
        if not isinstance(event_id, int):
            return None
            
        # Validate data structure
        validated_data = SupplierContactData(**data)
        
        # Convert integer event_id to string for database lookup since event IDs are stored as strings
        str_event_id = str(event_id)
        if str_event_id not in db.DB["events"]["events"]:
            return None
        event = db.DB["events"]["events"][str_event_id]
        if event.get("type") != "RFP":
            return None
        if "supplier_contacts" in event:
            for supplier_contact_id in validated_data.supplier_contact_ids:
                if supplier_contact_id in event["supplier_contacts"]:
                    event["supplier_contacts"].remove(supplier_contact_id)
        return event
    except (TypeError, ValueError):
        # Return None if validation fails (as per docstring)
        return None
