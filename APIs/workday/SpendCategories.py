"""
Spend Categories Management Module

This module provides functionality for managing spend categories in the Workday Strategic
Sourcing system. It supports operations for retrieving all spend categories and creating
new spend category entries.

The module interfaces with the simulation database to maintain spend category data, which
is used to categorize and track spending across different areas of procurement and
supplier management.

Functions:
    get: Retrieves all spend categories
    post: Creates a new spend category
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any, Optional
from .SimulationEngine import db
from .SimulationEngine.custom_errors import ValidationError, InvalidInputError, DuplicateExternalIdError

@tool_spec(
    spec={
        'name': 'list_spend_categories',
        'description': """ Retrieves a list of spend categories.
        
        Allows listing of all available spend categories along with optional usage types. Categories can be used to group procurement, expenses, ad-hoc payments, and supplier invoices. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> Dict[str, Any]:
    """
    Retrieves a list of spend categories.

    Allows listing of all available spend categories along with optional usage types. Categories can be used to group procurement, expenses, ad-hoc payments, and supplier invoices.

    Returns:
        Dict[str, Any]: A paginated response containing spend categories.

            - data (List[Dict[str, Any]]): List of spend categories.
                - type (str): Always "spend_categories".
                - id (str): Spend category identifier.
                - attributes (Dict[str, Any]):
                    - name (str): Name of the spend category.
                    - external_id (str): External system identifier for the spend category.
                    - usages (List[str]): Category usage contexts.
                        - Enum: "procurement", "expense", "ad_hoc_payment", "supplier_invoice"

            - meta (Dict[str, Any]):
                - count (int): Total number of spend categories.

            - links (Dict[str, Any]):
                - self (str): Link to current result set.
                - next (str|None): URL to next page of results.
                - prev (str|None): Deprecated. URL to previous page of results.
    """

    spend_categories = list(db.DB["spend_categories"].values())
    
    return {
        "data": spend_categories,
        "meta": {
            "count": len(spend_categories)
        },
        "links": {
            "self": "https://api.us.workdayspend.com/services/spend_categories/v1/spend_categories",
            "next": None,
            "prev": None
        }
    }

@tool_spec(
    spec={
        'name': 'create_spend_category',
        'description': """ Creates a new spend category with specified attributes.
        
        Spend categories are used to classify spend for procurement, expense, ad-hoc payment, or supplier invoice use cases. Only categories with the "procurement" usage can be used in requisitions. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'Required. Name of the spend category (max 255 characters).'
                },
                'external_id': {
                    'type': 'string',
                    'description': 'External identifier of the category (max 255 characters).'
                },
                'usages': {
                    'type': 'array',
                    'description': """ List of applicable usage contexts.
                    - Allowed values: "procurement", "expense", "ad_hoc_payment", "supplier_invoice" """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def post(name: str, external_id: Optional[str] = None, usages: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Creates a new spend category with specified attributes.

    Spend categories are used to classify spend for procurement, expense, ad-hoc payment, or supplier invoice use cases. Only categories with the "procurement" usage can be used in requisitions.

    Args:
        name (str): Required. Name of the spend category (max 255 characters).
        external_id (Optional[str]): External identifier of the category (max 255 characters).
        usages (Optional[List[str]]): List of applicable usage contexts.
            - Allowed values: "procurement", "expense", "ad_hoc_payment", "supplier_invoice"

    Returns:
        Dict[str, Any]: A created spend category object containing:
            - type (str): Always "spend_categories".
            - id (str): Unique identifier of the spend category.
            - attributes (Dict[str, Any]):
                - name (str): Spend category name.
                - external_id (str): External system identifier.
                - usages (List[str]): Category usage types.
                    - Allowed values: "procurement", "expense", "ad_hoc_payment", "supplier_invoice"

    Raises:
        ValidationError: When input validation fails (invalid name, external_id, or usages).
        DuplicateExternalIdError: When external_id already exists in the database.
    """
    
    # Validate name
    if not name or not isinstance(name, str):
        raise ValidationError("Input validation failed: Name is required and must be a string")
    
    name = name.strip()
    if not name:
        raise ValidationError("Input validation failed: Name cannot be empty or just whitespace")
    
    if len(name) > 255:
        raise ValidationError("Input validation failed: Name cannot exceed 255 characters")
    
    # Validate external_id
    if external_id is not None:
        if not isinstance(external_id, str):
            raise ValidationError("Input validation failed: External ID must be a string if provided")
        
        external_id = external_id.strip()
        if len(external_id) == 0:
            raise ValidationError("Input validation failed: External ID cannot be empty if provided")
        
        if len(external_id) > 255:
            raise ValidationError("Input validation failed: External ID cannot exceed 255 characters")
    
    # Validate usages
    if usages is not None:
        if not isinstance(usages, list):
            raise ValidationError("Input validation failed: Usages must be a list if provided")
        
        allowed_values = {"procurement", "expense", "ad_hoc_payment", "supplier_invoice"}
        for usage in usages:
            if not isinstance(usage, str):
                raise ValidationError("Input validation failed: All usage values must be strings")
            if usage not in allowed_values:
                raise ValidationError(f"Input validation failed: Invalid usage '{usage}'. Allowed values: {', '.join(sorted(allowed_values))}")
    
    # Check for duplicate external_id if provided
    if external_id:
        existing_categories = db.DB["spend_categories"]
        for existing_id, category in existing_categories.items():
            if category.get("external_id") == external_id:
                raise DuplicateExternalIdError(
                    f"A spend category with external_id '{external_id}' already exists "
                    f"(category ID: {existing_id}). External IDs must be unique across all spend categories."
                )
    
    # Generate new ID following the pattern SC001, SC002, etc.
    existing_categories = db.DB["spend_categories"]
    if not existing_categories:
        new_id = "SC001"
    else:
        # Extract numeric parts from existing IDs and find the next one
        numeric_ids = []
        for cat_id in existing_categories.keys():
            if cat_id.startswith("SC") and len(cat_id) == 5:
                try:
                    numeric_ids.append(int(cat_id[2:]))
                except ValueError:
                    continue
        
        if numeric_ids:
            next_num = max(numeric_ids) + 1
        else:
            next_num = 1
        
        new_id = f"SC{next_num:03d}"
    
    # Create the new category in database format
    new_category_data = {
        "id": new_id,
        "name": name,
        "external_id": external_id,
        "usages": usages
    }
    
    # Store in database
    db.DB["spend_categories"][new_id] = new_category_data
    
    # Return in JSON:API format as specified in docstring
    return {
        "type": "spend_categories",
        "id": new_id,
        "attributes": {
            "name": name,
            "external_id": external_id,
            "usages": usages
        }
    } 