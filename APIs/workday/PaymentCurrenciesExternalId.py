"""
Module for managing payment currencies by external identifier in the Workday Strategic Sourcing system.

This module provides functionality for managing payment currencies using their external identifiers.
It supports operations for updating currency details and deleting currencies based on their external IDs.
This is particularly useful when integrating with external systems that maintain their own currency identifiers.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional
from .SimulationEngine import db
from .SimulationEngine import custom_errors

@tool_spec(
    spec={
        'name': 'update_payment_currency_by_external_id',
        'description': 'Updates the details of an existing payment currency using its external identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier of the currency to update.'
                },
                'alpha': {
                    'type': 'string',
                    'description': 'The new three-letter currency code (e.g., USD, EUR).'
                },
                'numeric': {
                    'type': 'string',
                    'description': 'The new numeric currency code.'
                }
            },
            'required': [
                'external_id',
                'alpha',
                'numeric'
            ]
        }
    }
)
def patch(external_id: str, alpha: str, numeric: str) -> Optional[Dict]:
    """
    Updates the details of an existing payment currency using its external identifier.

    Args:
        external_id (str): The external identifier of the currency to update.
        alpha (str): The new three-letter currency code (e.g., USD, EUR).
        numeric (str): The new numeric currency code.

    Returns:
        Optional[Dict]: The updated currency object if found, None if no currency exists with the given external ID.
                        The updated currency object contains any of the following fields:
                            - type: Object type, should always be "payment_currencies"
                            - id: Payment currency identifier string
                            - alpha: Three-letter alphabetic currency code (e.g., USD, EUR)
                            - numeric: Three-digit numeric currency code
                            - external_id: Optional external identifier (max 255 characters)
    """
    for currency in db.DB["payments"]["payment_currencies"]:
        if currency.get("external_id") == external_id:
            currency["alpha"] = alpha
            currency["numeric"] = numeric
            return currency
    return None

@tool_spec(
    spec={
        'name': 'delete_payment_currency_by_external_id',
        'description': 'Deletes a payment currency using its external identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier of the currency to delete.'
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
    Deletes a payment currency using its external identifier.

    Args:
        external_id (str): The external identifier of the currency to delete.

    Returns:
        bool: Always returns True if the operation completes successfully, raises an error if the operation fails.

    Raises:
        ValueError: If external_id is not a valid, non-empty string.
        DatabaseSchemaError: If the database structure is invalid or
                                            missing the required keys to perform the operation.
    """
    # Add validation for the input parameter
    if not isinstance(external_id, str) or not external_id.strip():
        raise custom_errors.InvalidInputError("external_id must be a non-empty string.")

    try:
        # Perform the deletion using a list comprehension
        db.DB["payments"]["payment_currencies"] = [
            currency for currency in db.DB["payments"]["payment_currencies"] 
            if currency.get("external_id") != external_id
        ]
        
    except (KeyError, TypeError) as e:
        # Handle potential schema errors by raising a specific custom error
        raise custom_errors.DatabaseSchemaError(
            "Failed to access payment currencies due to an invalid database schema."
        ) from e

    # On success, always return True as per the updated docstring
    return True