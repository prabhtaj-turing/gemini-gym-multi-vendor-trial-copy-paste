"""
This module provides functionality for managing supplier contacts associated with
specific events using external identifiers in the Workday Strategic Sourcing system.
It supports operations for adding and removing suppliers from events using external
IDs, with a focus on RFP-type events.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, Dict, Any
from .SimulationEngine import db
from .SimulationEngine.models import SupplierContactInput
from .SimulationEngine.custom_errors import InvalidInputError, EventNotFound, InvalidEventType
from pydantic import ValidationError

@tool_spec(
    spec={
        'name': 'add_supplier_contacts_to_event_by_external_ids',
        'description': "Add suppliers to an event using supplier contacts. Only events of type RFP are supported. You must supply the unique event external identifier (the one you used when created the event). You must supply the external identifiers of the supplier contacts too. The operation will be rolled back upon any failure, and invitations won't be sent. For best performance, we recommend inviting 10 or less supplier contacts in a single request.",
        'parameters': {
            'type': 'object',
            'properties': {
                'event_external_id': {
                    'type': 'string',
                    'description': 'The unique external identifier of the event to which suppliers will be added.'
                },
                'data': {
                    'type': 'object',
                    'description': 'A dictionary containing the supplier contact information, including:',
                    'properties': {
                        'supplier_contact_external_ids': {
                            'type': 'array',
                            'description': 'A list of supplier contact external IDs to be added to the event',
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
                'event_external_id',
                'data'
            ]
        }
    }
)
def post(event_external_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Add suppliers to an event using supplier contacts. Only events of type RFP are supported. You must supply the unique event external identifier (the one you used when created the event). You must supply the external identifiers of the supplier contacts too. The operation will be rolled back upon any failure, and invitations won't be sent. For best performance, we recommend inviting 10 or less supplier contacts in a single request.
    
    Args:
        event_external_id (str): The unique external identifier of the event to which suppliers will be added.
        data (Dict[str, Any]): A dictionary containing the supplier contact information, including:
            - supplier_contact_external_ids (List[str], optional): A list of supplier contact external IDs to be added to the event
            - type (str): Object type, should always be "supplier_contacts"

    Returns:
        Dict[str, Any]: The updated event object, including the following keys:
            - id (int): The internal unique identifier of the event.
            - name (str): The name of the event.
            - type (str): The type of the event (will be "RFP").
            - external_id (str): The unique external identifier you provided.
            - supplier_contacts (List[str]): The complete list of supplier contact external IDs now associated with the event.

    Raises:
        InvalidInputError: If 'event_external_id' is empty or the 'data'
            payload does not conform to the required format.
        EventNotFound: If no event with the given 'event_external_id' exists.
        InvalidEventType: If the found event is not of type 'RFP'.
    """
    if not event_external_id or not event_external_id.strip():
        raise InvalidInputError("event_external_id cannot be empty.")

    if event_external_id not in {
        ev.get("external_id") for ev in db.DB["events"]["events"].values()
    }:
        raise EventNotFound(
            f"Event with external_id '{event_external_id}' not found in the database."
        )

    try:
        validated_data = SupplierContactInput.model_validate(data)
    except ValidationError as e:
        raise InvalidInputError(f"Invalid data format: {e}") from e

    event = next((
        event for event in db.DB["events"]["events"].values() 
        if event.get("external_id") == event_external_id
    ), None)

    if not event:
        raise EventNotFound(f"Event with external_id '{event_external_id}' not found.")

    if event.get("type") != "RFP":
        raise InvalidEventType(f"Event '{event_external_id}' is of type '{event.get('type')}', but must be 'RFP'.")
    
    # Ensure 'supplier_contacts' list exists
    if "supplier_contacts" not in event:
        event["supplier_contacts"] = []
    
    # Add only new contacts to prevent duplicates
    for contact_id in validated_data.supplier_contact_external_ids:
        if contact_id not in event["supplier_contacts"]:
            event["supplier_contacts"].append(contact_id)

    return event

 
@tool_spec(
    spec={
        'name': 'remove_supplier_contacts_from_event_by_external_ids',
        'description': "Remove suppliers from an event using supplier contacts. Only events of type RFP are supported. You must supply the unique event external identifier (the one you used when created the event). You must supply the external identifiers of the supplier contacts too. The operation will be rolled back upon any failure, and invitations won't be removed. For best performance, we recommend removing 10 or less supplier contacts in a single request.",
        'parameters': {
            'type': 'object',
            'properties': {
                'event_external_id': {
                    'type': 'string',
                    'description': 'The unique external identifier of the event from which supplier contacts will be removed.'
                },
                'data': {
                    'type': 'object',
                    'description': 'A dictionary containing the supplier contact information, including:',
                    'properties': {
                        'supplier_contact_external_ids': {
                            'type': 'array',
                            'description': 'A list of supplier contact external IDs to be removed from the event',
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
                'event_external_id',
                'data'
            ]
        }
    }
)
def delete(event_external_id: str, data: dict) -> bool:
    """Remove suppliers from an event using supplier contacts. Only events of type RFP are supported. You must supply the unique event external identifier (the one you used when created the event). You must supply the external identifiers of the supplier contacts too. The operation will be rolled back upon any failure, and invitations won't be removed. For best performance, we recommend removing 10 or less supplier contacts in a single request.
    
    Args:
        event_external_id (str): The unique external identifier of the event from which supplier contacts will be removed.
        data (dict): A dictionary containing the supplier contact information, including:
            - supplier_contact_external_ids (List[str], optional): A list of supplier contact external IDs to be removed from the event
            - type (str): Object type, should always be "supplier_contacts"

    Returns:
        bool: True if every contact id was found and removed.
        ValueError: Raised if the event is missing, not RFP, or any
                     supplier-contact id is missing.
    """
    event = next(
        (e for e in db.DB["events"]["events"].values()
         if e.get("external_id") == event_external_id),
        None
    )
    if not event or event.get("type") != "RFP":
        raise ValueError("Event not found or not of type RFP")

    contacts = event.setdefault("supplier_contacts", [])
    to_remove = data.get("supplier_contact_external_ids", [])

    missing = [cid for cid in to_remove if cid not in contacts]
    if missing:
        raise ValueError(f"Supplier contact external id(s) not found: {missing}")

    for cid in to_remove:
        contacts.remove(cid)

    return True