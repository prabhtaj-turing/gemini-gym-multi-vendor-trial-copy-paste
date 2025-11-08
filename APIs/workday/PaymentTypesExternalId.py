"""
This module provides functionality for managing payment types using their external identifiers.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional
from .SimulationEngine import db
from .SimulationEngine import custom_errors

@tool_spec(
    spec={
        'name': 'update_payment_type_by_external_id',
        'description': 'Updates the details of an existing payment type using its external identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier of the payment type to update.'
                },
                'name': {
                    'type': 'string',
                    'description': 'The new name for the payment type.'
                },
                'payment_method': {
                    'type': 'string',
                    'description': 'The new payment method. One of: "Direct Deposit", "Check", "EFT", "Cash", "Credit Card", "Wire", "Manual", "Direct Debit", "PayPal", "EFT with Reference"'
                }
            },
            'required': [
                'external_id',
                'name'
            ]
        }
    }
)
def patch(external_id: str, name: str, payment_method: str = None) -> Optional[Dict]:
    """
    Updates the details of an existing payment type using its external identifier.

    Args:
        external_id (str): The external identifier of the payment type to update.
        name (str): The new name for the payment type.
        payment_method (str, optional): The new payment method. One of: "Direct Deposit", "Check", "EFT", "Cash", "Credit Card", "Wire", "Manual", "Direct Debit", "PayPal", "EFT with Reference"

    Returns:
        Optional[Dict]: The updated payment type object if found, None if no type exists with the given external ID.
        The updated payment type object contains any of the following fields:
            - type (str): The object type, always "payment_types"
            - id (str): The payment type identifier
            - name (str): The name of the payment type
            - payment_method (str): Payment method (one of: "Direct Deposit", "Check", "EFT", "Cash", "Credit Card", "Wire", "Manual", "Direct Debit", "PayPal", "EFT with Reference")
            - external_id (str, optional): Optional external identifier (max 255 characters)
    """
    for type_ in db.DB["payments"]["payment_types"]:
        if type_.get("external_id") == external_id:
            type_["name"] = name
            if payment_method is not None:
                type_["payment_method"] = payment_method
            return type_
    return None

@tool_spec(
    spec={
        'name': 'delete_payment_type_by_external_id',
        'description': 'Deletes a payment type using its external identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier of the payment type to delete.'
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
    Deletes a payment type using its external identifier.

    Args:
        external_id (str): The external identifier of the payment type to delete.

    Returns:
        bool: True if the payment type was found and successfully deleted.

    Raises:
        ValueError: If external_id is not a string or is an empty/whitespace string.
        NotFoundError: If no payment type with the given external_id is found.
        DatabaseIntegrityError: If the internal database structure for 
                                              payment types is corrupt or missing.
    """
    # Validate input: ensure external_id is a non-empty, non-whitespace string.
    if not isinstance(external_id, str) or not external_id.strip():
        raise ValueError("external_id must be a non-empty string.")

    try:
        payment_types = db.DB["payments"]["payment_types"]
        initial_count = len(payment_types)

        # Rebuild the list, excluding the item with the matching external_id
        filtered_list = [
            type_ for type_ in payment_types if type_.get("external_id") != external_id
        ]
        
        # If the list length is unchanged, the item was not found.
        if len(filtered_list) == initial_count:
            raise custom_errors.NotFoundError(
                f"Payment type with external_id '{external_id}' not found."
            )

        # Otherwise, the deletion was successful. Update the DB and return True.
        db.DB["payments"]["payment_types"] = filtered_list
        return True

    except KeyError:
        # If the expected keys don't exist in the DB, raise a specific error.
        raise custom_errors.DatabaseSchemaError(
            "Database structure for payment types is corrupt or missing."
        )