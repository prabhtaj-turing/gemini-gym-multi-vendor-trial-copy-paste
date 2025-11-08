"""
SCIM Schema Management Module.

This module provides functionality for retrieving information about supported SCIM schemas
as defined in RFC 7644, section 3.4. It serves as a central point for schema information
used across the Workday Strategic Sourcing API simulation.

The module provides a single function to retrieve all available SCIM schemas, which are
essential for understanding the structure and attributes of identity resources in the system.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Any
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'list_scim_schemas',
        'description': """ Retrieves the list of supported SCIM schemas and their attribute definitions.
        
        This endpoint provides metadata about each schema in use, including its attributes and constraints. Refer to Section 3.4 of RFC 7644 for schema discovery guidance. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get() -> Dict[str, Any]:
    """
    Retrieves the list of supported SCIM schemas and their attribute definitions.

    This endpoint provides metadata about each schema in use, including its attributes and constraints. Refer to Section 3.4 of RFC 7644 for schema discovery guidance.

    Returns:
        Dict[str, Any]: A dictionary representing a SCIM ListResponse, with the following keys:
            - schemas (List[str]): List of schema URIs this object adheres to.
            - totalResults (int): The total number of schemas.
            - startIndex (int): The starting index for pagination (1-based).
            - itemsPerPage (int): The number of items per page.
            - Resources (List[Dict[str, Any]]): A list of schema resources. Each item can contain:
                - id (str): Unique identifier for the schema.
                - meta (Dict[str, str]):
                    - resourceType (str): Type of resource (e.g., "Schema").
                    - location (str): URI to retrieve the schema definition.
                - name (str): Human-readable schema name.
                - description (str): Human-readable schema description.
                - attributes (List[Dict[str, Any]]): Attribute definitions for the schema.
                    - name (str): Name of the attribute.
                    - type (str): Data type (e.g., "string", "boolean").
                    - subAttributes (List[Dict[str, Any]]): Nested attributes, if any.
                    - multiValued (bool): Whether the attribute is an array.
                    - description (str): Human-readable attribute description.
                    - required (bool): Whether the field is required.
                    - caseExact (bool): If true, string matching is case sensitive.
                    - mutability (str): "readOnly", "readWrite", "immutable", or "writeOnly".
                    - returned (str): "always", "never", "default", or "request".
                    - uniqueness (str): "none", "server", or "global".
                    - referenceTypes (List[str]): Applicable if type is "reference".
        If no schemas are available, this function returns a valid SCIM ListResponse
        where `totalResults` and `itemsPerPage` are 0, and `Resources` is an empty list.

    """
    schemas_list = db.DB["scim"]["schemas"]
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(schemas_list),
        "startIndex": 1,
        "itemsPerPage": len(schemas_list),
        "Resources": schemas_list,
    }
