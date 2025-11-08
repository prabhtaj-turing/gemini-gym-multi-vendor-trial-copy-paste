"""
This module provides functionality for managing supplier companies associated with
specific events using external identifiers in the Workday Strategic Sourcing system.
It supports operations for adding and removing suppliers from events using external
IDs, with a focus on RFP-type events.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Optional
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'add_supplier_companies_to_event_by_external_id',
        'description': 'Add suppliers to an event using external identifiers. Only events of type RFP are supported.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_external_id': {
                    'type': 'string',
                    'description': """ The unique external identifier of the event to
                    which suppliers will be added. """
                },
                'data': {
                    'type': 'object',
                    'description': 'A dictionary containing the supplier information, including:',
                    'properties': {
                        'supplier_external_ids': {
                            'type': 'array',
                            'description': """ A list of supplier external IDs to be
                                 added to the event """,
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
                'event_external_id',
                'data'
            ]
        }
    }
)
def post(event_external_id: str, data: dict) -> Optional[Dict]:
    """Add suppliers to an event using external identifiers. Only events of type RFP are supported.

    Args:
        event_external_id (str): The unique external identifier of the event to
            which suppliers will be added.
        data (dict): A dictionary containing the supplier information, including:
            - supplier_external_ids (List[str], optional): A list of supplier external IDs to be
                added to the event
            - type (str): Object type, should always be "supplier_companies"

    Returns:
        Optional[Dict]: The updated event data if successful, including the newly
            added suppliers. Returns None if:
            - The event does not exist
            - The event is not of type RFP
            - The operation fails
    """
    event = next((event for event in db.DB["events"]["events"].values() if event.get("external_id") == event_external_id), None)

    if not event or event.get("type") != "RFP":
        return None

    if "suppliers" not in event:
        event["suppliers"] = []
    event["suppliers"].extend(data.get("supplier_external_ids", []))
    return event

@tool_spec(
    spec={
        'name': 'remove_supplier_companies_from_event_by_external_id',
        'description': 'Removes supplier companies from a specific event using external identifiers. Only events of type RFP are supported.',
        'parameters': {
            'type': 'object',
            'properties': {
                'event_external_id': {
                    'type': 'string',
                    'description': """ The unique external identifier of the event from
                    which suppliers will be removed. """
                },
                'data': {
                    'type': 'object',
                    'description': 'A dictionary containing the supplier information, including:',
                    'properties': {
                        'supplier_external_ids': {
                            'type': 'array',
                            'description': """ A list of supplier external IDs to be
                                 removed from the event """,
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
                        'supplier_external_ids',
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
def delete(event_external_id: str, data: dict) -> Optional[Dict]:
    """Removes supplier companies from a specific event using external identifiers. Only events of type RFP are supported.

    Args:
        event_external_id (str): The unique external identifier of the event from
            which suppliers will be removed.
        data (dict): A dictionary containing the supplier information, including:
            - supplier_external_ids (List[str]): A list of supplier external IDs to be
                removed from the event
            - type (str): Object type, should always be "supplier_companies"
    Returns:
        Optional[Dict]: The event data after attempting to remove the specified
            suppliers, regardless of whether any suppliers were actually found and removed.
            Returns None if:
            - The event does not exist
            - The event is not of type RFP
            - The operation fails
            - The data type is not "supplier_companies"
            - The supplier_external_ids is not a list of strings
            - event_external_id is None or empty
            - data is not a dictionary or is None
    """
    # Validate event_external_id
    if not event_external_id or not isinstance(event_external_id, str):
        return None
        
    # Validate data structure is a dictionary
    if not data or not isinstance(data, dict):
        return None
    
    # Validate required data type field
    if data.get("type") != "supplier_companies":
        return None
        
    # Validate supplier_external_ids
    supplier_ids = data.get("supplier_external_ids", [])
    if not isinstance(supplier_ids, list) or not all(isinstance(id, str) and id for id in supplier_ids):
        return None
        
    # Find and validate the event
    event = next((event for event in db.DB["events"]["events"].values() if event.get("external_id") == event_external_id), None)
    if not event or event.get("type") != "RFP":
        return None

    # Process removal of suppliers
    if "suppliers" in event:
        for supplier_external_id in supplier_ids:
            if supplier_external_id in event["suppliers"]:
                event["suppliers"].remove(supplier_external_id)
        return event
    return None