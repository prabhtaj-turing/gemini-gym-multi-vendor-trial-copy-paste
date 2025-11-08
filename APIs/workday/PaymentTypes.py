"""
This module provides comprehensive functionality for managing payment types
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Optional, Any
from .SimulationEngine import db
from .SimulationEngine.custom_errors import PaymentTypesDatabaseError

@tool_spec(
    spec={
        'name': 'list_payment_types',
        'description': """ Retrieves a list of all available payment types in the system.
        
        This function accesses the in-memory database to retrieve all payment type records.
        The function handles potential database access issues gracefully. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> List[Dict[str, Any]]:
    """
    Retrieves a list of all available payment types in the system.

    This function accesses the in-memory database to retrieve all payment type records.
    The function handles potential database access issues gracefully.

    Returns:
        List[Dict[str, Any]]: A list of payment type objects, each containing:
            - id (int): The payment type identifier (auto-generated)
            - name (str): The name of the payment type (e.g., "Credit Card", "Bank Transfer")
            - payment_method (str): Payment method (e.g., "Visa", "Mastercard", "Direct Deposit")
            - external_id (str, optional): Optional external identifier (max 255 characters)
            - type (str): The object type, always "payment_types"

    Raises:
        PaymentTypesDatabaseError: If the database structure is corrupted or payment_types collection is missing
    """
    try:
        payment_types = db.DB["payments"]["payment_types"]
        
        # Validate that payment_types is a list
        if not isinstance(payment_types, list):
            raise PaymentTypesDatabaseError("Payment types data is not in the expected list format")

        return payment_types

    except (KeyError, AttributeError) as e:
        raise PaymentTypesDatabaseError(f"Database access error: {str(e)}")
    except Exception as e:
        # Re-raise unexpected errors with context
        raise PaymentTypesDatabaseError(f"Unexpected error while retrieving payment types: {str(e)}")

@tool_spec(
    spec={
        'name': 'create_payment_type',
        'description': 'Create a payment type with given parameters.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The name of the payment type (e.g., "Credit Card", "Bank Transfer").'
                },
                'payment_method': {
                    'type': 'string',
                    'description': 'The method of payment (e.g., "card", "transfer").'
                },
                'external_id': {
                    'type': 'string',
                    'description': 'An external identifier for the payment type.'
                }
            },
            'required': [
                'name',
                'payment_method'
            ]
        }
    }
)
def post(name: str, payment_method: str, external_id: str = None) -> Dict:
    """
    Create a payment type with given parameters.

    Args:
        name (str): The name of the payment type (e.g., "Credit Card", "Bank Transfer").
        payment_method (str): The method of payment (e.g., "card", "transfer").
        external_id (str, optional): An external identifier for the payment type.

    Returns:
        Dict: The newly created payment type object containing any of the following fields:
            - type (str): The object type, always "payment_types"
            - id (str): The payment type identifier
            - name (str): The name of the payment type
            - payment_method (str): Payment method (one of: "Direct Deposit", "Check", "EFT", "Cash", "Credit Card", "Wire", "Manual", "Direct Debit", "PayPal", "EFT with Reference")
            - external_id (str, optional): Optional external identifier (max 255 characters)
    """
    new_type = {
        "id": db.DB["payments"]["payment_type_id_counter"],
        "name": name,
        "external_id": external_id,
        "payment_method": payment_method,
        "type": "payment_types"
    }
    db.DB["payments"]["payment_types"].append(new_type)
    db.DB["payments"]["payment_type_id_counter"] += 1
    return new_type