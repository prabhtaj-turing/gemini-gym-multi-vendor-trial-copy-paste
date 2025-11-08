"""
SCIM Resource Types Management Module

This module provides functionality for managing SCIM (System for Cross-domain Identity
Management) resource types in the Workday Strategic Sourcing system. It supports
operations for discovering available resource types and retrieving detailed information
about specific resource types.

The module interfaces with the simulation database to provide access to SCIM resource
type definitions, which include endpoint configurations, supported schemas, and
extensions for different types of resources in the system.

Functions:
    get: Retrieves a list of all available SCIM resource types
    get_by_resource: Retrieves details for a specific SCIM resource type
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Optional, Any
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'list_scim_resource_types',
        'description': """ Lists SCIM resource types available on the service provider.
        
        This endpoint allows clients to discover all supported SCIM resource types and their associated metadata, including endpoint paths and schemas. This is based on Section 4 of RFC 7644. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> List[Dict[str, Any]]:
    """
    Lists SCIM resource types available on the service provider.

    This endpoint allows clients to discover all supported SCIM resource types and their associated metadata, including endpoint paths and schemas. This is based on Section 4 of RFC 7644.

    Returns:
        List[Dict[str, Any]]: A list of SCIM resource types containing:
            - schemas (List[str]): Schema URIs the resource type adheres to.
            - id (str): Unique identifier of the resource type.
            - meta (Dict[str, str]):
                - resourceType (str): Resource type (e.g., ResourceType).
                - location (str): URI of the resource type.
            - name (str): Human-readable name of the resource type.
            - description (str): Description of the resource type.
            - endpoint (str): URI path where resources of this type can be accessed.
            - schema (str): Main schema URI for this resource type.
            - schemaExtensions (List[Dict[str, Union[str, bool]]]): Additional schema extensions containing:
                - schema (str): Extension schema URI.
                - required (bool): Whether the extension schema is mandatory.
    """

    return db.DB["scim"]["resource_types"]

@tool_spec(
    spec={
        'name': 'get_scim_resource_type_by_name',
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
def get_by_resource(resource: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves metadata for a specific SCIM resource type.

    This endpoint provides the schema, endpoint path, and any extensions supported for a given SCIM resource (e.g., "User"). It returns a subset of the information available from the general `/ResourceTypes` endpoint, focusing on a single resource type.

    Args:
        resource (str): Name of the SCIM resource type.
            - Example: "User"
            - Must be a non-empty string

    Returns:
        Optional[Dict[str, Any]]: The metadata describing the specified SCIM resource type if found, otherwise None. If found, it can contain the following keys:
            - schemas (List[str]): List of schema URIs this response adheres to.
            - id (str): Unique identifier for the resource type.
            - meta (Dict[str, str]):
                - resourceType (str): The SCIM resource type name.
                - location (str): URI for this specific resource type description.
            - name (str): Human-readable name of the resource.
            - description (str): Description of what the resource represents.
            - endpoint (str): Path to access this resource type (e.g., "/Users").
            - schema (str): URI of the primary schema used by this resource.
            - schemaExtensions (List[Dict[str, Union[str, bool]]]): List of schema extensions containing:
                - schema (str): URI of the extension schema.
                - required (bool): Indicates if this extension is mandatory.

    Raises:
        ValueError: If resource is None, empty string, or not a string type.
    """
    # Input validation
    if not isinstance(resource, str):
        raise ValueError("resource parameter must be a string")
    
    if not resource or resource.strip() == "":
        raise ValueError("resource parameter cannot be None or empty")
    
    # Search for the resource type
    for resource_type in db.DB["scim"]["resource_types"]:
        if resource_type.get("name") == resource:
            return resource_type
    
    return None 