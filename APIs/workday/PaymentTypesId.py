"""
This module provides functionality for managing payment types using their internal identifiers.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional
from .SimulationEngine import db
from .SimulationEngine.custom_errors import InvalidInputError, PaymentTypeNotFoundError

@tool_spec(
    spec={
        'name': 'update_payment_type_by_id',
        'description': 'Updates the details of an existing payment type using its internal identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The internal identifier of the payment type to update.'
                },
                'name': {
                    'type': 'string',
                    'description': 'The new name for the payment type.'
                },
                'payment_method': {
                    'type': 'string',
                    'description': 'The new payment method. One of: "Direct Deposit", "Check", "EFT", "Cash", "Credit Card", "Wire", "Manual", "Direct Debit", "PayPal", "EFT with Reference"'
                },
                'external_id': {
                    'type': 'string',
                    'description': 'The new external identifier for the payment type.'
                }
            },
            'required': [
                'id',
                'name'
            ]
        }
    }
)
def patch(id: int, name: str, payment_method: str = None, external_id: str = None) -> Optional[Dict]:
    """
    Updates the details of an existing payment type using its internal identifier.

    Args:
        id (int): The internal identifier of the payment type to update.
        name (str): The new name for the payment type. 
        payment_method (str, optional): The new payment method. One of: "Direct Deposit", "Check", "EFT", "Cash", "Credit Card", "Wire", "Manual", "Direct Debit", "PayPal", "EFT with Reference"
        external_id (str, optional): The new external identifier for the payment type.

    Returns:
        Optional[Dict]: The updated payment type object if found, None if no type exists with the given ID.
        The updated payment type object contains any of the following fields:
            - type (str): The object type, always "payment_types"
            - id (str): The payment type identifier
            - name (str): The name of the payment type
            - payment_method (str): Payment method (one of: "Direct Deposit", "Check", "EFT", "Cash", "Credit Card", "Wire", "Manual", "Direct Debit", "PayPal", "EFT with Reference")
            - external_id (str, optional): Optional external identifier (max 255 characters)
    """
    for type_ in db.DB["payments"]["payment_types"]:
        if type_["id"] == id:
            type_["name"] = name
            if external_id is not None:
                type_["external_id"] = external_id
            if payment_method is not None:
                type_["payment_method"] = payment_method
            return type_
    return None

@tool_spec(
    spec={
        'name': 'delete_payment_type_by_id',
        'description': 'Deletes a payment type using its internal identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The internal identifier of the payment type to delete.'
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
    Deletes a payment type using its internal identifier.

    Args:
        id (int): The internal identifier of the payment type to delete.

    Returns:
        bool: True if the payment type was successfully deleted.

    Raises:
        InvalidInputError: If the provided id is not a positive integer.
        PaymentTypeNotFoundError: If no payment type with the specified id is found.
    """
    # 1. Validate input for type and range
    if not isinstance(id, int) or id <= 0:
        raise InvalidInputError("Payment type 'id' must be a positive integer.")

    # 2. Check for existence and perform deletion
    payment_types = db.DB["payments"]["payment_types"]
    len_before = len(payment_types)

    # Filter the list to exclude the item with the matching id
    db.DB["payments"]["payment_types"] = [
        pt for pt in payment_types if pt.get("id") != id
    ]

    # 3. Verify that an item was actually deleted
    if len(db.DB["payments"]["payment_types"]) == len_before:
        raise PaymentTypeNotFoundError(f"Payment type with id '{id}' not found.")

    # On success, return True
    return True