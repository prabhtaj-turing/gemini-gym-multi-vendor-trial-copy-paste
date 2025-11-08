"""
Spend Category Management by External ID Module

This module provides functionality for managing spend categories using their external
identifiers in the Workday Strategic Sourcing system. It supports operations for
retrieving, updating, and deleting spend category details using external IDs.

The module interfaces with the simulation database to provide comprehensive spend
category management capabilities, allowing users to perform CRUD operations on spend
categories using their external IDs. This is particularly useful when integrating
with external systems that maintain their own spend category identifiers.

Functions:
    get: Retrieves spend category details by external ID
    patch: Updates spend category details by external ID
    delete: Deletes a spend category by external ID
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, List
from .SimulationEngine import db, custom_errors, models
from pydantic import ValidationError as PydanticValidationError

@tool_spec(
    spec={
        'name': 'get_spend_category_by_id',
        'description': """ Retrieves the details of a specific spend category by its unique identifier.
        
        Spend categories define classification for various types of organizational spend such as procurement, expenses, supplier invoices, etc. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'Unique identifier of the spend category.'
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def get(external_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the details of a specific spend category by its unique identifier.

    Spend categories define classification for various types of organizational spend such as procurement, expenses, supplier invoices, etc.

    Args:
        external_id (str): Unique identifier of the spend category.

    Returns:
        Optional[Dict[str, Any]]: A spend category object including its attributes.

            - data (Dict[str, Any]):
                - type (str): Always "spend_categories".
                - id (str): Unique identifier of the spend category.
                - attributes (Dict[str, Any]):
                    - name (str): Spend category name.
                    - external_id (str): Optional. External system identifier (max 255 characters).
                    - usages (List[str]): Applicable usage contexts for this category.
                        - Enum: "procurement", "expense", "ad_hoc_payment", "supplier_invoice"

    Raises:
        HTTPError 401: Unauthorized – API credentials are missing or invalid.
        HTTPError 404: Not Found – No spend category found with the provided ID.
    """

    for category in db.DB["spend_categories"].values():
        if category.get("external_id") == external_id:
            return category
    return None

@tool_spec(
    spec={
        'name': 'update_spend_category_by_id',
        'description': """ Updates an existing spend category with new attributes.
        
        The spend category must be identified by its unique ID (same as provided in the path). Only fields passed in the payload will be updated; others remain unchanged. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The unique external identifier of the spend category to update.'
                },
                'name': {
                    'type': 'string',
                    'description': 'The new name for the spend category (1-255 characters).'
                },
                'new_external_id': {
                    'type': 'string',
                    'description': 'The new external system ID (1-255 characters).'
                },
                'usages': {
                    'type': 'array',
                    'description': """ List of applicable contexts. Must be one or more of:
                    - "procurement", "expense", "ad_hoc_payment", "supplier_invoice" """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def patch(external_id: str, name: Optional[str] = None, new_external_id: Optional[str] = None, 
          usages: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Updates an existing spend category with new attributes.

    The spend category must be identified by its unique ID (same as provided in the path). Only fields passed in the payload will be updated; others remain unchanged.

    Args:
        external_id (str): The unique external identifier of the spend category to update.
        name (Optional[str]): The new name for the spend category (1-255 characters).
        new_external_id (Optional[str]): The new external system ID (1-255 characters).
        usages (Optional[List[str]]): List of applicable contexts. Must be one or more of:
            - "procurement", "expense", "ad_hoc_payment", "supplier_invoice"

    Returns:
        Dict[str, Any]: Updated spend category object.
            - data (Dict[str, Any]):
                - type (str): "spend_categories"
                - id (str): Spend category ID.
                - attributes (Dict[str, Any]):
                    - name (str): Spend category name.
                    - external_id (str): External system ID.
                    - usages (List[str]): Usage contexts.

    Raises:
        ValidationError: If input data is invalid (e.g., wrong type, out of range, empty).
        NotFoundError: If no spend category is found with the given external_id.
        ConflictError: If the `new_external_id` is already in use by another category.
    """
    # 0. Validate external_id parameter
    if not isinstance(external_id, str):
        raise custom_errors.ValidationError("external_id must be a string")
    
    if len(external_id.strip()) == 0:
        raise custom_errors.ValidationError("external_id cannot be empty or whitespace-only")
    
    # 1. Validate inputs using the Pydantic model
    update_payload = {
        "name": name,
        "new_external_id": new_external_id,
        "usages": usages
    }
    # Filter out None values to only validate the fields that were provided
    provided_data = {k: v for k, v in update_payload.items() if v is not None}

    if not provided_data:
        raise custom_errors.ValidationError("At least one field to update must be provided.")

    try:
        validated_data = models.SpendCategoryUpdateModel(**provided_data)
    except PydanticValidationError as e:
        # Re-raise as our custom, more user-friendly error
        raise custom_errors.ValidationError(f"Input validation failed: {e}") from e

    # 2. Find the spend category to update
    target_id = None
    target_category = None
    for cat_id, category in db.DB.get("spend_categories", {}).items():
        if category.get("external_id") == external_id:
            target_id = cat_id
            target_category = category
            break

    if not target_category:
        raise custom_errors.NotFoundError(f"Spend category with external_id '{external_id}' not found.")

    # 3. Critical Bug Fix: Check for conflicts before updating
    if validated_data.new_external_id:
        for cat_id, category in db.DB.get("spend_categories", {}).items():
            # Check if another category (not the one we're updating) already uses the new ID
            if category.get("external_id") == validated_data.new_external_id and cat_id != target_id:
                raise custom_errors.ConflictError(f"Conflict: External ID '{validated_data.new_external_id}' is already in use.")

    # 4. Apply the updates to the found category
    if validated_data.name is not None:
        target_category["name"] = validated_data.name
    if validated_data.new_external_id is not None:
        target_category["external_id"] = validated_data.new_external_id
    if validated_data.usages is not None:
        # Pydantic model returns a list of strings, store directly
        target_category["usages"] = validated_data.usages

    # 5. Format the response to match the docstring
    response = {
        "data": {
            "type": "spend_categories",
            "id": target_id,
            "attributes": {
                "name": target_category["name"],
                "external_id": target_category["external_id"],
                "usages": target_category["usages"]
            }
        }
    }
    return response

@tool_spec(
    spec={
        'name': 'delete_spend_category_by_id',
        'description': """ Deletes an existing spend category by its unique identifier.
        
        The identifier must match the one returned during spend category creation. This operation is irreversible and will permanently remove the category. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'Unique ID of the spend category to delete.'
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
    Deletes an existing spend category by its unique identifier.

    The identifier must match the one returned during spend category creation. This operation is irreversible and will permanently remove the category.

    Args:
        external_id (str): Unique ID of the spend category to delete.

    Returns:
        bool: Returns HTTP 204 No Content on successful deletion.

    Raises:
        HTTPError 401: Unauthorized – API credentials are missing or invalid.
        HTTPError 404: Not Found – No spend category found with the provided ID.
    """

    for id, category in db.DB["spend_categories"].items():
        if category.get("external_id") == external_id:
            del db.DB["spend_categories"][id]
            return True
    return False 