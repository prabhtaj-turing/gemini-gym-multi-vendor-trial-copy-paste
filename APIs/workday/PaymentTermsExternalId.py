"""
This module provides functionality for managing payment terms using their external identifiers.
It supports operations for updating term details and deleting terms based on their external IDs.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'update_payment_term_by_external_id',
        'description': 'Updates the details of an existing payment term using its external identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier of the payment term to update.'
                },
                'name': {
                    'type': 'string',
                    'description': 'The new name for the payment term (e.g., "Net 30", "Net 60").'
                }
            },
            'required': [
                'external_id',
                'name'
            ]
        }
    }
)
def patch(external_id: str, name: str) -> Optional[Dict]:
    """
    Updates the details of an existing payment term using its external identifier.

    Args:
        external_id (str): The external identifier of the payment term to update.
        name (str): The new name for the payment term (e.g., "Net 30", "Net 60").

    Returns:
        Optional[Dict]: The updated payment term object if found, None if no term exists with the given external ID.
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
        if term.get("external_id") == external_id:
            term["name"] = name
            return term
    return None

@tool_spec(
    spec={
        'name': 'delete_payment_term_by_external_id',
        'description': 'Deletes a payment term using its external identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier of the payment term to delete.'
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def delete(external_id: str) -> bool:
    """
    Deletes a payment term using its external identifier.

    Args:
        external_id (str): The external identifier of the payment term to delete.

    Returns:
        bool: True if the payment term was deleted or did not exist, False if the operation failed.
    """
    db.DB["payments"]["payment_terms"] = [
        term for term in db.DB["payments"]["payment_terms"] if term.get("external_id") != external_id
    ]
    return True