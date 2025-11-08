"""
SCIM Service Provider Configuration Module

This module provides functionality for managing and retrieving the SCIM (System for Cross-domain
Identity Management) service provider configuration in the Workday Strategic Sourcing system.

The module interfaces with the simulation database to provide access to the service provider
configuration, which details the SCIM specification features and capabilities supported by the
system, including authentication schemes, supported operations, and bulk configuration.

Functions:
    get: Retrieves the complete service provider configuration
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, List
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'get_scim_service_provider_config',
        'description': """ Retrieves the SCIM service provider configuration, describing supported features and capabilities.
        
        This endpoint returns metadata about the SCIM implementation, including patch, filter, bulk, authentication schemes, and more, as specified in Section 5 of RFC 7643. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> Dict[str, Any]:
    """
    Retrieves the SCIM service provider configuration, describing supported features and capabilities.

    This endpoint returns metadata about the SCIM implementation, including patch, filter, bulk, authentication schemes, and more, as specified in Section 5 of RFC 7643.

    Returns:
        Dict[str, Any]: SCIM service provider configuration including supported operations.

            - schemas (List[str]): List of SCIM schema URIs defining this resource.
            - meta (Dict[str, str]):
                - resourceType (str): The type of SCIM resource (always "ServiceProviderConfig").
                - created (str): ISO 8601 creation timestamp.
                - lastModified (str): ISO 8601 last modification timestamp.
                - version (str): Version identifier.
                - location (str): URI for retrieving the resource.
            - documentationUri (str): URI to documentation of the SCIM service.
            - patch (Dict[str, bool]):
                - supported (bool): Whether PATCH operations are supported.
            - bulk (Dict[str, Union[bool, int]]):
                - supported (bool): Whether bulk operations are supported.
                - maxOperations (int): Maximum number of operations per request (if present).
            - filter (Dict[str, Union[bool, int]]):
                - supported (bool): Whether filtering is supported.
                - maxResults (int): Max number of results returned in filtered requests.
            - changePassword (Dict[str, bool]):
                - supported (bool): Whether the changePassword operation is supported.
            - sort (Dict[str, bool]):
                - supported (bool): Whether sorting is supported.
            - etag (Dict[str, bool]):
                - supported (bool): Whether ETag headers are supported.
            - authenticationSchemes (List[Dict[str, Union[str, bool]]]):
                - type (str): Scheme type (e.g., "oauth", "httpBasic").
                - name (str): Human-readable scheme name.
                - description (str): Human-readable scheme description.
                - primary (bool): Indicates the default scheme.
    """
    return db.DB["scim"]["service_provider_config"] 