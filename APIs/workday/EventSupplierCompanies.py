"""
This module provides functionality for managing supplier companies associated with
specific events in the Workday Strategic Sourcing system. It supports operations
for adding and removing suppliers from events, with a focus on RFP-type events.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Optional, Any
from .SimulationEngine import db
from .SimulationEngine.custom_errors import EventNotFoundError, InvalidEventTypeError, SupplierNotFoundError, InvalidPayloadError
from .SimulationEngine.models import EventSupplierInput
from pydantic import ValidationError as PydanticValidationError

@tool_spec(
    spec={
        'name': 'add_supplier_companies_to_event_by_internal_id',
        'description': 'Add suppliers to an event. Only events of type RFP are supported.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'integer',
                    'description': """ The unique identifier of the event to which suppliers
                    will be added. """
                },
                'data': {
                    'type': 'object',
                    'description': 'A dictionary containing the supplier information, including:',
                    'properties': {
                        'supplier_ids': {
                            'type': 'array',
                            'description': 'A list of supplier IDs to be added to the event',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "supplier_companies"'
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
def post(event_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Add suppliers to an event. Only events of type RFP are supported.

    Args:
        event_id (int): The unique identifier of the event to which suppliers
            will be added.
        data (Dict[str, Any]): A dictionary containing the supplier information, including:
            - supplier_ids (List[str], optional): A list of supplier IDs to be added to the event
            - type (str): Object type, should always be "supplier_companies"

    Returns:
        Dict[str, Any]: The updated event data if successful, including the newly
            added suppliers.
    
    Raises:
        InvalidPayloadError: If the input data is malformed or fails validation.
        EventNotFoundError: If no event with the given `event_id` exists.
        InvalidEventTypeError: If the event is not of type "RFP".
        SupplierNotFoundError: If one or more `supplier_ids` do not correspond
            to existing suppliers in the database.
    """
    # Validate the input payload by instantiating the Pydantic model
    try:
        validated_data = EventSupplierInput.model_validate(data)
    except PydanticValidationError as e:
        # Re-raise Pydantic's detailed error as a single, clear custom exception
        raise InvalidPayloadError(f"Invalid input payload: {e}")

    # Check if the event exists
    # Convert integer event_id to string for database lookup since event IDs are stored as strings
    str_event_id = str(event_id)
    if str_event_id not in db.DB["events"]["events"]:
        raise EventNotFoundError(f"Event with ID {event_id} not found.")

    event = db.DB["events"]["events"][str_event_id]

    # Validate that the event is an RFP
    if event.get("type") != "RFP":
        raise InvalidEventTypeError("Suppliers can only be added to events of type 'RFP'.")

    # Validate that all supplier IDs exist for data integrity
    all_known_supplier_ids = set(db.DB["suppliers"]["supplier_companies"].keys())
    submitted_supplier_ids = set(validated_data.supplier_ids)

    # Find any submitted IDs that are not in the database
    invalid_ids = submitted_supplier_ids - all_known_supplier_ids
    if invalid_ids:
        raise SupplierNotFoundError(f"The following supplier IDs were not found: {sorted(list(invalid_ids))}")

    # Add suppliers idempotently (preventing duplicates)
    event_suppliers = event.setdefault("suppliers", [])
    for supplier_id in validated_data.supplier_ids:
        if supplier_id not in event_suppliers:
            event_suppliers.append(supplier_id)

    return event

@tool_spec(
    spec={
        'name': 'remove_supplier_companies_from_event_by_internal_id',
        'description': 'Remove suppliers from an event. Only events of type RFP are supported.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the event from which suppliers will be removed.'
                },
                'data': {
                    'type': 'object',
                    'description': 'A dictionary containing the supplier information, including:',
                    'properties': {
                        'supplier_ids': {
                            'type': 'array',
                            'description': 'A list of supplier IDs to be removed from the event',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "supplier_companies"'
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
def delete(event_id: int, data: dict) -> bool:
    """Remove suppliers from an event. Only events of type RFP are supported.

    Args:
        event_id (int): The unique identifier of the event from which suppliers will be removed.
        data (dict): A dictionary containing the supplier information, including:
            - supplier_ids (List[str], optional): A list of supplier IDs to be removed from the event
            - type (str): Object type, should always be "supplier_companies"

    Returns:
        bool: True if suppliers were successfully removed from the event.

    Raises:
        InvalidPayloadError: If the input data is malformed or fails validation.
        EventNotFoundError: If no event with the given `event_id` exists.
        InvalidEventTypeError: If the event is not of type "RFP".
        SupplierNotFoundError: If one or more `supplier_ids` do not correspond to existing suppliers in the database.
    """
    # Validate the input payload by instantiating the Pydantic model
    try:
        validated_data = EventSupplierInput.model_validate(data)
    except PydanticValidationError as e:
        raise InvalidPayloadError(f"Invalid input payload: {e}")

    # Check if the event exists
    # Convert integer event_id to string for database lookup since event IDs are stored as strings
    str_event_id = str(event_id)
    if str_event_id not in db.DB["events"]["events"]:
        raise EventNotFoundError(f"Event with ID {event_id} not found.")

    event = db.DB["events"]["events"][str_event_id]

    # Validate that the event is an RFP
    if event.get("type") != "RFP":
        raise InvalidEventTypeError("Suppliers can only be removed from events of type 'RFP'.")

    # Validate that all supplier IDs exist for data integrity
    all_known_supplier_ids = set(db.DB["suppliers"]["supplier_companies"].keys())
    submitted_supplier_ids = set(validated_data.supplier_ids)

    # Find any submitted IDs that are not in the database
    invalid_ids = submitted_supplier_ids - all_known_supplier_ids
    if invalid_ids:
        raise SupplierNotFoundError(f"The following supplier IDs were not found: {sorted(list(invalid_ids))}")

    # Remove suppliers if present
    event_suppliers = event.setdefault("suppliers", [])
    for supplier_id in validated_data.supplier_ids:
        if supplier_id in event_suppliers:
            event_suppliers.remove(supplier_id)

    return True 