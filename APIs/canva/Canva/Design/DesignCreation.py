from common_utils.tool_spec_decorator import tool_spec
# canva/Canva/Design/DesignCreation.py
"""
This module provides design creation functionality for Canva.

It includes functions for creating new designs with validation and error handling.
"""

import time
from typing import Dict, Any, Optional, Union
from pydantic import ValidationError

from canva.SimulationEngine.db import DB
from canva.SimulationEngine.models import DesignTypeInputModel, DesignModel
from canva.SimulationEngine.custom_errors import (
    InvalidAssetIDError, 
    InvalidTitleError
)
from canva.SimulationEngine.utils import (
    generate_canva_design_id,
    generate_default_thumbnail
)

@tool_spec(
    spec={
        'name': 'create_design',
        'description': 'Creates a new design with specified design type, asset, and title.',
        'parameters': {
            'type': 'object',
            'properties': {
                'design_type': {
                    'type': 'object',
                    'description': "Optional dictionary specifying the design's foundational template or category. Format: {\"type\": \"preset\", \"name\": \"doc\"}",
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'The category of design creation method. Currently only "preset" is supported.',
                            'enum': ['preset']
                        },
                        'name': {
                            'type': 'string',
                            'description': 'The specific preset template. Accepted values: doc, whiteboard, presentation',
                            'enum': ['doc', 'whiteboard', 'presentation']
                        }
                    },
                    'required': ['type', 'name']
                },
                'asset_id': {
                    'type': 'string',
                    'description': """ Optional ID of the asset (e.g., image) to include in the design.
                    Must be a non-empty string if provided. """
                },
                'title': {
                    'type': 'string',
                    'description': 'Optional title of the design. Must be 1–255 characters if provided.'
                }
            },
            'required': []
        }
    }
)
def create_design(design_type: Optional[Dict[str, str]] = None, asset_id: Optional[str] = None, title: Optional[str] = None) -> Dict[str, Union[str, int, Dict]]:
    """
    Creates a new design with specified design type, asset, and title.

    Args:
        design_type (Optional[Dict[str, str]]): Optional dictionary specifying the design's foundational template or category.
            Format: {"type": "preset", "name": "doc"}
            - type (str): The category of design creation method. Currently only "preset" is supported.
            - name (str): The specific preset template. Accepted values: doc, whiteboard, presentation
        asset_id (Optional[str]): Optional ID of the asset (e.g., image) to include in the design.
                                  Must be a non-empty string if provided.
        title (Optional[str]): Optional title of the design. Must be 1–255 characters if provided.

    Returns:
        Dict[str, Union[str, int, Dict]]: A dictionary containing:
            - id (str): Design ID.
            - title (str): Design title.
            - owner (Dict[str, str]): Owner information with user_id and team_id.
            - thumbnail (Dict[str, Union[str, int]]): Thumbnail metadata with width, height, and url.
            - urls (Dict[str, str]): Navigation URLs with edit_url and view_url.
            - created_at (int): Unix timestamp.
            - updated_at (int): Unix timestamp.
            - page_count (int): Number of pages in the design.
        Otherwise, returns None.

    Raises:
        ValidationError: If 'design_type' is provided but does not conform to the DesignTypeInputModel structure,
                                  or if the created design fails validation against DesignModel.
        TypeError: If 'asset_id' or 'title' are provided but are not strings.
        InvalidAssetIDError: If 'asset_id' is provided but is an empty string.
        InvalidTitleError: If 'title' is provided but length is not between 1 and 255 characters.
    """
    # --- Input Validation ---
    validated_design_type_model = None
    
    # 1. Validate 'design_type' using Pydantic (if provided)
    if design_type is not None:
        if not isinstance(design_type, dict):
            raise TypeError("design_type should be a valid dictionary")
        # Strict validation - raise error if input doesn't match Canva API format
        validated_design_type_model = DesignTypeInputModel.model_validate(design_type)
    
    # 2. Validate 'asset_id' (if provided)
    if asset_id is not None:
        if not isinstance(asset_id, str):
            raise TypeError("asset_id must be a string.")
        if not asset_id:  # Check for empty string
            raise InvalidAssetIDError("asset_id cannot be empty.")

    # 3. Validate 'title' (if provided)
    if title is not None:
        if not isinstance(title, str):
            raise TypeError("title must be a string.")
        if not (1 <= len(title) <= 255):
            raise InvalidTitleError(
                f"title must be between 1 and 255 characters long. Received length: {len(title)}."
            )

    # --- Core Function Logic ---
    design_id = generate_canva_design_id()
    timestamp = int(time.time())
    
    # Default user/team IDs for simulation (in real API, these would come from auth context)
    default_user_id = "auDAbliZ2rQNNOsUl5OLu"
    default_team_id = "Oi2RJILTrKk0KRhRUZozX"

    # Create design schema matching real Canva API response format
    # Ensure all required fields are present with proper types
    new_design = {
        "id": design_id,
        "title": title if title is not None else "Untitled Design",
        "design_type": {
            "type": validated_design_type_model.type if validated_design_type_model is not None else None,
            "name": validated_design_type_model.name if validated_design_type_model is not None else None
        },
        "owner": {
            "user_id": default_user_id,
            "team_id": default_team_id
        },
        "thumbnail": generate_default_thumbnail(),
        "urls": {
            "edit_url": f"https://www.canva.com/api/design/{design_id}/edit",
            "view_url": f"https://www.canva.com/api/design/{design_id}/view"
        },
        "created_at": timestamp,
        "updated_at": timestamp,
        "page_count": 1,
        "pages": {},  # Empty dict for pages
        "comments": {  # Empty comments structure
            "threads": {}
        },
        "asset_id": asset_id if asset_id is not None else None
    }

    # --- Output Validation ---
    # Validate the created design against the DesignModel schema
    # This ensures ID rules and schema compliance are enforced
    # Add design_type if provided (flexible handling)
    if validated_design_type_model is not None:
        # Use the validated Pydantic model's dictionary representation.
        # model_dump() creates a dict from the model.
        # exclude_none=True means fields with None value won't be in the dict.
        new_design["design_type"] = validated_design_type_model.model_dump(exclude_none=True)
    
    # --- Output Validation ---
    # Validate the created design against the DesignModel schema
    # This ensures ID rules and schema compliance are enforced
    validated_design = DesignModel.model_validate(new_design)
    validated_design_dict = validated_design.model_dump()
    
    # Store the complete validated design in the database
    DB["Designs"][design_id] = validated_design_dict
    
    return validated_design.model_dump(
            include={'id', 'title', 'owner', 'thumbnail', 'urls', 'created_at', 'updated_at', 'page_count', 'design_type', 'asset_id'}
        ) if validated_design else None
