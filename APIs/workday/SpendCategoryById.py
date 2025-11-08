"""
Spend Category Management by ID Module

This module provides functionality for managing spend categories using their unique
internal identifiers in the Workday Strategic Sourcing system. It supports operations
for retrieving, updating, and deleting spend category details.

The module interfaces with the simulation database to provide comprehensive spend
category management capabilities, allowing users to perform CRUD operations on spend
categories using their internal IDs.

Functions:
    get: Retrieves spend category details by ID
    patch: Updates spend category details by ID
    delete: Deletes a spend category by ID
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, List, Union
from .SimulationEngine import db, custom_errors

@tool_spec(
    spec={
        'name': 'get_spend_category_details_by_external_id',
        'description': """ Retrieves the details of an existing spend category using its internal identifier.
        
        Internal IDs allow referencing spend categories directly in the database. This is useful for internal operations and direct database access. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'Internal identifier of the spend category.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get(id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieves the details of an existing spend category using its internal identifier.

    Internal IDs allow referencing spend categories directly in the database. This is useful for internal operations and direct database access.

    Args:
        id (int): Internal identifier of the spend category.

    Returns:
        Optional[Dict[str, Any]]: The spend category resource if found, None otherwise.
            - type (str): Always "spend_categories".
            - id (int): Unique internal ID.
            - attributes (Dict[str, Any]):
                - name (str): Name of the spend category.
                - external_id (str): External identifier.
                - usages (List[str]): List of usages.
                    - Enum: "procurement", "expense", "ad_hoc_payment", "supplier_invoice"
    """

    return db.DB["spend_categories"].get(id)

@tool_spec(
    spec={
        'name': 'update_spend_category_details_by_external_id',
        'description': """ Updates the details of an existing spend category using its internal identifier.
        
        The internal ID must match the one provided in the URL path. All parameters are optional and only the provided fields will be updated. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'Internal identifier for the spend category to be updated.'
                },
                'name': {
                    'type': 'string',
                    'description': 'Updated name (max 255 characters).'
                },
                'external_id': {
                    'type': 'string',
                    'description': 'New or same external identifier (max 255 characters).'
                },
                'usages': {
                    'type': 'array',
                    'description': """ Updated list of usages.
                    - Enum: "procurement", "expense", "ad_hoc_payment", "supplier_invoice" """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def patch(id: int, name: Optional[str] = None, external_id: Optional[str] = None, 
          usages: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    Updates the details of an existing spend category using its internal identifier.

    The internal ID must match the one provided in the URL path. All parameters are optional and only the provided fields will be updated.

    Args:
        id (int): Internal identifier for the spend category to be updated.
        name (Optional[str]): Updated name (max 255 characters).
        external_id (Optional[str]): New or same external identifier (max 255 characters).
        usages (Optional[List[str]]): Updated list of usages.
            - Enum: "procurement", "expense", "ad_hoc_payment", "supplier_invoice"

    Returns:
        Optional[Dict[str, Any]]: The updated spend category object if found, None otherwise.

            - data (Dict[str, Any]):
                - type (str): Always "spend_categories".
                - id (int): Unique internal ID.
                - attributes (Dict[str, Any]):
                    - name (str): Updated or existing name.
                    - external_id (str): External identifier.
                    - usages (List[str]): Allowed usages.
    """

    if id not in db.DB["spend_categories"]:
        return None
    category = db.DB["spend_categories"][id]
    if name is not None:
        category["name"] = name
    if external_id is not None:
        category["external_id"] = external_id
    if usages is not None:
        category["usages"] = usages
    return category

@tool_spec(
    spec={
        'name': 'delete_spend_category_by_external_id',
        'description': """ Deletes an existing spend category using its internal identifier.
        
        The internal ID must match the one provided in the URL path. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'Internal identifier of the spend category to be deleted.'
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
    Deletes an existing spend category using its internal identifier.

    The internal ID must match the one provided in the URL path.

    Args:
        id (int): Internal identifier of the spend category to be deleted.

    Returns:
        bool: Always returns True on successful deletion.

    Raises:
        InvalidInputError: If the provided ID is not a positive integer.
        NotFoundError: If no spend category with the given ID is found.
    """
    if not isinstance(id, int) or id <= 0:
        raise custom_errors.InvalidInputError("ID must be a positive integer.")

    try:
        del db.DB["spend_categories"][id]
        return True
    except KeyError:
        raise custom_errors.NotFoundError(f"Spend category with ID {id} not found.")
