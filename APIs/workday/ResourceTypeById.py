"""
SCIM Resource Type Management by ID Module

This module provides functionality for managing SCIM (System for Cross-domain Identity
Management) resource types using their unique identifiers in the Workday Strategic
Sourcing system. It supports operations for retrieving detailed information about
specific resource types.

The module interfaces with the simulation database to provide access to SCIM resource
type definitions, which include endpoint configurations, supported schemas, and
extensions for different types of resources in the system.

Functions:
    get: Retrieves SCIM resource type details by resource name
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional, Any
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'get_scim_resource_type_metadata_by_name',
        'description': """ Retrieves metadata for a specific SCIM resource type.
        
        This endpoint provides the schema, endpoint path, and any extensions supported for a given SCIM resource (e.g., "User"). It returns a subset of the information available from the general `/ResourceTypes` endpoint, focusing on a single resource type. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource': {
                    'type': 'string',
                    'description': """ Name of the SCIM resource type.
                    - Example: "User"
                    - Must be a non-empty string """
                }
            },
            'required': [
                'resource'
            ]
        }
    }
)
def get(resource: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves metadata for a specific SCIM resource type.

    This endpoint provides the schema, endpoint path, and any extensions supported for a given SCIM resource (e.g., "User"). It returns a subset of the information available from the general `/ResourceTypes` endpoint, focusing on a single resource type.

    Args:
        resource (str): Name of the SCIM resource type.
            - Example: "User"
            - Must be a non-empty string

    Returns:
        Optional[Dict[str, Any]]: The metadata describing the specified SCIM resource type if found, 
        or None if the resource type does not exist. If found, it can contain the following keys:
            - schemas (List[str]): List of schema URIs this response adheres to.
            - id (str): Unique identifier for the resource type.
            - meta (Dict[str, str]):
                - resourceType (str): The SCIM resource type name.
                - location (str): URI for this specific resource type description.
            - name (str): Human-readable name of the resource.
            - description (str): Description of what the resource represents.
            - endpoint (str): Path to access this resource type (e.g., "/Users").
            - schema (str): URI of the primary schema used by this resource.
            - schemaExtensions (List[Dict[str, Any]]): List of schema extensions.
                - schema (str): URI of the extension schema.
                - required (bool): Indicates if this extension is mandatory.

    Raises:
        ValueError: If resource is None or an empty string.
        TypeError: If resource is not a string.

    """

    # Input validation
    if resource is None:
        raise ValueError("resource parameter cannot be None")
    
    if not isinstance(resource, str):
        raise TypeError("resource parameter must be a string")
    
    if not resource.strip():
        raise ValueError("resource parameter cannot be empty or whitespace only")

    for resource_type in db.DB["scim"]["resource_types"]:
        if resource_type.get("resource") == resource:
            return resource_type
    return None 