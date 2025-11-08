"""
This module provides functionality for managing payment terms using their internal identifiers.
It supports operations for updating term details and deleting terms based on their internal IDs.
This is the primary interface for managing existing payment terms within the Workday Strategic Sourcing system.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'update_payment_term_by_id',
        'description': 'Updates the details of an existing payment term using its internal identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The internal identifier of the payment term to update.'
                },
                'name': {
                    'type': 'string',
                    'description': 'The name for the payment term.'
                },
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier for the payment term.'
                }
            },
            'required': [
                'id',
                'name'
            ]
        }
    }
)
def patch(id: int, name: str, external_id: str = None) -> Optional[Dict]:
    """
    Updates the details of an existing payment term using its internal identifier.

    Args:
        id (int): The internal identifier of the payment term to update.
        name (str): The name for the payment term.
        external_id (str, optional): The external identifier for the payment term.

    Returns:
        Optional[Dict]: The updated payment term object if found, None if no term exists with the given ID.
            The updated payment term object contains any of the following fields:
                - type (str): Object type, should always be "payment_terms"
                - id (str): Payment term identifier string
                - name (str): The name of the payment term
                - external_id (str, optional): Optional external identifier
                - attributes (dict): Payment term attributes containing:
                    - name (str): Payment term name (max 255 characters)
                    - external_id (str): Payment term external identifier (max 255 characters)
    """
    for term in db.DB["payments"]["payment_terms"]:
        if term["id"] == id:
            term["name"] = name
            term["external_id"] = external_id
            return term
    return None

@tool_spec(
    spec={
        'name': 'delete_payment_term_by_id',
        'description': 'Deletes a payment term using its internal identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The internal identifier of the payment term to delete.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete(id: int) -> bool:
    """
    Deletes a payment term using its internal identifier.

    Args:
        id (int): The internal identifier of the payment term to delete.

    Returns:
        bool: True if the payment term was deleted or did not exist, False if the operation failed.
    """
    db.DB["payments"]["payment_terms"] = [term for term in db.DB["payments"]["payment_terms"] if term["id"] != id]
    return True