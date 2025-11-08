from common_utils.print_log import print_log
"""
Utility functions for the Generic Service.

This module contains the core business logic for the service. It's responsible
for interacting with the database (DB), performing calculations, and preparing
data for the API layer.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from .db import DB
from .models import EntityStorage, EntityStatus, ComplexInput
from .custom_errors import ValidationError, ResourceNotFoundError

# ---------------------------
# Business Logic Functions
# ---------------------------

def perform_action(name: str) -> Dict[str, Any]:
    """
    A sample business logic function that creates a new entity.

    Args:
        name: The name of the entity to create.

    Returns:
        A dictionary containing the result of the action.
    """
    print_log(f"Performing action for entity '{name}'")
    
    new_entity = create_entity(name=name, status=EntityStatus.ACTIVE)
    
    return {
        "entity_id": new_entity["id"],
        "status_message": f"Entity '{name}' created successfully with ID {new_entity['id']}."
    }

# ---------------------------
# Response Formatting Functions
# ---------------------------

def build_tool_response(entity_id: str, message: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds the standard, specifically structured response for a tool.

    Args:
        entity_id: The ID of the affected entity.
        message: A descriptive message for the response.
        inputs: The original, validated inputs received by the tool.

    Returns:
        A dictionary formatted for the API response, matching the specific
        structure defined in the tool's docstring.
    """
    return {
        "success": True,
        "message": message,
        "data": {
            "entity_id": entity_id,
            "params_received": inputs
        }
    }

# ---------------------------
# CRUD Operations for Entities
# ---------------------------

def create_entity(name: str, status: EntityStatus) -> Dict[str, Any]:
    """Creates a new entity and saves it to the database."""
    entity_data = EntityStorage(name=name, status=status)
    entity_dict = entity_data.model_dump()
    DB["entities"][entity_dict["id"]] = entity_dict
    return entity_dict

def get_entity(entity_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single entity from the database by its ID."""
    return DB.get("entities", {}).get(entity_id)

def update_entity(entity_id: str, name: Optional[str] = None, status: Optional[EntityStatus] = None) -> Optional[Dict[str, Any]]:
    """Updates an existing entity in the database."""
    entities = DB.get("entities", {})
    if entity_id not in entities:
        raise ResourceNotFoundError(f"Entity with ID '{entity_id}' not found.")

    entity = entities[entity_id]
    if name is not None:
        entity["name"] = name
    if status is not None:
        entity["status"] = status.value
    entity["updated_at"] = datetime.now().isoformat()
    
    EntityStorage(**entity)  # Validate before returning
    return entity

def delete_entity(entity_id: str) -> bool:
    """Deletes an entity from the database."""
    if entity_id in DB.get("entities", {}):
        del DB["entities"][entity_id]
        return True
    return False

def list_entities() -> List[Dict[str, Any]]:
    """Returns a list of all entities in the database."""
    return list(DB.get("entities", {}).values())
