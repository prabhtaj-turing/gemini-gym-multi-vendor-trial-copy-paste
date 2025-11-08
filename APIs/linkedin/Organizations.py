from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, Union, List

from .SimulationEngine.file_utils import _apply_projection
from .SimulationEngine.db import DB
from .SimulationEngine.models import GetByVanityInputModel, OrganizationData, OrganizationUpdateModel
from pydantic import ValidationError
from typing import Type, Dict, Any, Optional, List
from .SimulationEngine.custom_errors import InvalidOrganizationIdError, OrganizationNotFoundError, InvalidQueryFieldError, InvalidVanityNameError, OrganizationNotFound

"""
API simulation for the '/organizations' resource.
"""

@tool_spec(
    spec={
        'name': 'get_organizations_by_vanity_name',
        'description': 'Retrieves organization(s) by vanity name with optional field projection and pagination.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query_field': {
                    'type': 'string',
                    'description': "Query parameter expected to be 'vanityName'."
                },
                'vanity_name': {
                    'type': 'string',
                    'description': "The organization's vanity name to search for."
                },
                'projection': {
                    'type': 'string',
                    'description': """ Field projection syntax for controlling which fields to return.
                    The projection string should consist of comma-separated field names and may optionally
                    be enclosed in parentheses. Defaults to None. """
                },
                'start': {
                    'type': 'integer',
                    'description': 'Starting index for pagination. Defaults to 0.'
                },
                'count': {
                    'type': 'integer',
                    'description': 'Number of items to return. Defaults to 10.'
                }
            },
            'required': [
                'query_field',
                'vanity_name'
            ]
        }
    }
)
def get_organizations_by_vanity_name(query_field: str,
                                        vanity_name: str,
                                        projection: Optional[str] = None,
                                        start: Optional[int] = 0,
                                        count: Optional[int] = 10) -> Dict[str, Any]:
    """
    Retrieves organization(s) by vanity name with optional field projection and pagination.

    Args:
        query_field (str): Query parameter expected to be 'vanityName'.
        vanity_name (str): The organization's vanity name to search for.
        projection (Optional[str]): Field projection syntax for controlling which fields to return.
            The projection string should consist of comma-separated field names and may optionally
            be enclosed in parentheses. Valid fields: 'id', 'vanityName', 'name', 'primaryOrganizationType'.
            Defaults to None (returns all fields).
        start (Optional[int]): Starting index for pagination. Must be non-negative. Defaults to 0.
        count (Optional[int]): Number of items to return. Must be positive. Defaults to 10.

    Returns:
        Dict[str, Any]: Dictionary with the following keys and value types:
            - 'data' (List[Dict[str, Any]]): List of organization data dictionaries with keys:
                - 'id' (int): Organization's unique identifier.
                - 'vanityName' (str): Organization's vanity name (e.g., 'global-tech').
                - 'name' (Dict[str, Any]): Localized organization name with keys:
                    - 'localized' (Dict[str, str]): Dictionary with locale keys mapping to the localized name, keys are locale codes in the format <language>_<COUNTRY>, for example:
                        - 'en_US' (str): English (US) localized name.
                    - 'preferredLocale' (Dict[str, str]): tells you which language/country version LinkedIn considers the "main" or "default" for that particular localized content. Dictionary with keys:
                        - 'country' (str): Country code (e.g., 'US').
                        - 'language' (str): Language code (e.g., 'en').
                - 'primaryOrganizationType' (str): Type of organization ('COMPANY' or 'SCHOOL').

    Raises:
        ValueError: If vanity_name, start, or count parameters are invalid.
    """
    # Validate inputs using Pydantic to enforce types and constraints
    try:

        try:
            _validated = GetByVanityInputModel(
                query_field=query_field,
                vanity_name=vanity_name,
                projection=projection,
                start=start,
                count=count,
            )
        except ValidationError as e:
            # Map Pydantic errors to legacy ValueError messages expected by tests
            if e.errors():
                first_error = e.errors()[0]
                field_name = first_error.get('loc')[-1] if first_error.get('loc') else None
                error_type = first_error.get('type', '')
                msg = first_error.get('msg', '')

                if field_name == 'query_field':
                    raise ValueError("Invalid query parameter. Expected 'vanityName'.")

                if field_name == 'vanity_name':
                    if 'string_type' in error_type or 'string' in error_type:
                        raise ValueError("vanity_name must be a string")
                    # Use our validator message when present
                    cleaned = msg.split('Value error, ', 1)[1] if msg.startswith('Value error, ') else msg
                    raise ValueError(cleaned or "vanity_name cannot be empty")

                if field_name == 'start':
                    if 'int_type' in error_type or 'int' in error_type:
                        raise ValueError("start must be an integer")
                    cleaned = msg.split('Value error, ', 1)[1] if msg.startswith('Value error, ') else msg
                    raise ValueError(cleaned or "start must be non-negative")

                if field_name == 'count':
                    if 'int_type' in error_type or 'int' in error_type:
                        raise ValueError("count must be an integer")
                    cleaned = msg.split('Value error, ', 1)[1] if msg.startswith('Value error, ') else msg
                    # Expect either "count must be positive" or "count cannot exceed 100"
                    if cleaned in ("count must be positive", "count cannot exceed 100"):
                        raise ValueError(cleaned)
                    # Default fallback
                    raise ValueError("count must be positive")

                if field_name == 'projection':
                    # Wrap projection-related validation into the expected error format
                    if 'string_type' in error_type or 'string' in error_type or 'Projection must be a string' in msg:
                        raise ValueError("Invalid projection format: Projection must be a string")
                    if 'Projection must contain at least one field' in msg:
                        raise ValueError("Invalid projection format: Projection must contain at least one field")
                    if 'Invalid field(s) in projection:' in msg:
                        raise ValueError(f"Invalid projection format: {msg}")
                    # Fallback
                    raise ValueError(f"Invalid projection format: {msg}")

            # Generic fallback if structure is unexpected
            raise ValueError("Invalid input parameters")

        # Overwrite with validated values (ensures defaults and strict types applied)
        query_field = _validated.query_field
        vanity_name = _validated.vanity_name
        projection = _validated.projection
        start = _validated.start
        count = _validated.count
        projected_fields = _validated.projected_fields
    except Exception:
        # Re-raise after mapping; no additional wrapping here
        raise
    
    # Search for organizations
    results = [org for org in DB["organizations"].values() if org.get("vanityName") == vanity_name]
    
    # Apply projection to each result
    if projected_fields is not None:
        results = [_apply_projection(org, projected_fields) for org in results]
    
    # Apply pagination
    paginated = results[start:start+count]
    
    return {"data": paginated}

@tool_spec(
    spec={
        'name': 'create_organization',
        'description': 'Creates a new organization in the database.',
        'parameters': {
            'type': 'object',
            'properties': {
                'organization_data': {
                    'type': 'object',
                    'description': 'Dictionary required to create a new organization, including its public name, type, and localization settings:',
                    'properties': {
                        'vanityName': {
                            'type': 'string',
                            'description': "Organization's vanity name (e.g., 'global-tech')."
                        },
                        'name': {
                            'type': 'object',
                            'description': 'Localized organization name with keys:',
                            'properties': {
                                'localized': {
                                    'type': 'object',
                                    'description': "Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized organization names.",
                                    'properties': {},
                                    'required': []
                                },
                                'preferredLocale': {
                                    'type': 'object',
                                    'description': 'Dictionary specifying the default locale for this organization with keys:',
                                    'properties': {
                                        'country': {
                                            'type': 'string',
                                            'description': "Country code (e.g., 'US')."
                                        },
                                        'language': {
                                            'type': 'string',
                                            'description': "Language code (e.g., 'en')."
                                        }
                                    },
                                    'required': [
                                        'country',
                                        'language'
                                    ]
                                }
                            },
                            'required': [
                                'localized',
                                'preferredLocale'
                            ]
                        },
                        'primaryOrganizationType': {
                            'type': 'string',
                            'description': "Type of organization ('COMPANY' or 'SCHOOL')."
                        }
                    },
                    'required': [
                        'vanityName',
                        'name',
                        'primaryOrganizationType'
                    ]
                }
            },
            'required': [
                'organization_data'
            ]
        }
    }
)
def create_organization(organization_data: Dict[str, Union[str, Dict[str, str], Dict[str, Dict[str, str]]]]) -> Dict[str, Any]:
    """
    Creates a new organization in the database with comprehensive input validation.

    Args:
        organization_data (Dict[str, Union[str, Dict[str, str], Dict[str, Dict[str, str]]]]): Dictionary required to create a new organization, including its public name, type, and localization settings:
            - 'vanityName' (str): Organization's vanity name (e.g., 'global-tech').
            - 'name' (Dict[str, Dict[str, str]]): Localized organization name with keys:
                - 'localized' (Dict[str, str]): Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized organization names.
                - 'preferredLocale' (Dict[str, str]): Dictionary specifying the default locale for this organization with keys:
                    - 'country' (str): Country code (e.g., 'US').
                    - 'language' (str): Language code (e.g., 'en').
            - 'primaryOrganizationType' (str): Type of organization ('COMPANY' or 'SCHOOL').

    Returns:
        Dict[str, Any]: Dictionary containing the created organization data with keys:
            - 'data' (Dict[str, Any]): Dictionary of created organization with keys:
                - 'id' (int): Newly assigned unique identifier.
                - 'vanityName' (str): Organization's vanity name (e.g., 'global-tech').
                - 'name' (Dict[str, Any]): Localized organization name with keys:
                    - 'localized' (Dict[str, str]): Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized organization names.
                    - 'preferredLocale' (Dict[str, str]): Dictionary specifying the default locale with keys:
                        - 'country' (str): Country code (e.g., 'US').
                        - 'language' (str): Language code (e.g., 'en').
                - 'primaryOrganizationType' (str): Type of organization ('COMPANY' or 'SCHOOL').

    Raises:
        ValueError: If input validation fails, including invalid data types, missing required fields,
                   invalid vanity name format, duplicate vanity name, or invalid organization type.
        TypeError: If organization_data is not a dictionary.
    """
    # Type validation
    if not isinstance(organization_data, dict):
        raise TypeError("organization_data must be a dictionary")
    
    # Validate and parse the input data using Pydantic
    try:
        validated_data = OrganizationData(**organization_data)
    except Exception as e:
        raise ValueError(f"Invalid organization data: {str(e)}")
    
    # Create the organization
    org_id = DB["next_org_id"]
    DB["next_org_id"] += 1
    
    # Convert validated data back to dictionary and add ID
    org_dict = validated_data.model_dump(mode='json')
    org_dict["id"] = org_id
    
    # Store in database
    DB["organizations"][str(org_id)] = org_dict
    
    return {"data": org_dict}

@tool_spec(
    spec={
        "name": "update_organization_by_id",
        "description": "Updates an existing organization's data in the database.",
        "parameters": {
            "type": "object",
            "properties": {
                "organization_id": {
                    "type": "string",
                    "description": "Unique identifier of the organization to update."
                },
                "organization_data": {
                    "type": "object",
                    "description": "Dictionary required to update an existing organization, including its public name, type, and localization settings:",
                    "properties": {
                        "vanityName": {
                            "type": "string",
                            "description": "Updated vanity name (e.g., 'global-tech')."
                        },
                        "name": {
                            "type": "object",
                            "description": "Updated localized organization name with keys:",
                            "properties": {
                                "localized": {
                                    "type": "object",
                                    "description": "Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.",
                                    "properties": {},
                                    "required": []
                                },
                                "preferredLocale": {
                                    "type": "object",
                                    "description": "tells you which language/country version LinkedIn considers the \"main\" or \"default\" for that particular localized content. Dictionary with keys:",
                                    "properties": {
                                        "country": {
                                            "type": "string",
                                            "description": "Country code (e.g., 'US')."
                                        },
                                        "language": {
                                            "type": "string",
                                            "description": "Language code (e.g., 'en')."
                                        }
                                    },
                                    "required": [
                                        "country",
                                        "language"
                                    ]
                                }
                            },
                            "required": [
                                "localized",
                                "preferredLocale"
                            ]
                        },
                        "primaryOrganizationType": {
                            "type": "string",
                            "description": "Updated type of organization ('COMPANY' or 'SCHOOL')."
                        }
                    },
                    "required": [
                        "vanityName",
                        "name",
                        "primaryOrganizationType"
                    ]
                }
            },
            "required": [
                "organization_id",
                "organization_data"
            ]
        }
    }
)
def update_organization(organization_id: str,
                        organization_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates an existing organization's data in the database.

    Args:
        organization_id (str): Unique identifier of the organization to update.
        organization_data (Dict[str, Any]): Dictionary required to update an existing organization, including its public name, type, and localization settings:
            - 'vanityName' (str): Updated vanity name (e.g., 'global-tech').
            - 'name' (Dict[str, Any]): Updated localized organization name with keys:
                - 'localized' (Dict[str, str]): Dictionary with locale codes as keys mapping to localized names. Keys are locale codes in format <language>_<COUNTRY> (e.g., 'en_US', 'fr_FR', 'de_DE'). Values are the corresponding localized names.
                - 'preferredLocale' (Dict[str, str]): tells you which language/country version LinkedIn considers the "main" or "default" for that particular localized content. Dictionary with keys:
                    - 'country' (str): Country code (e.g., 'US').
                    - 'language' (str): Language code (e.g., 'en').
            - 'primaryOrganizationType' (str): Updated type of organization ('COMPANY' or 'SCHOOL').

    Returns:
        Dict[str, Any]:
        - On successful update, returns a dictionary with the following keys and value types:
            - 'id' (str): The unique identifier of the organization.
            - 'vanityName' (str): URL-friendly version of the organization's name.
            - 'name' (Dict[str, Any]): Localized name with keys:
                - 'localized' (Dict[str, str]): Dictionary with locale keys mapping to the localized name.
                - 'preferredLocale' (Dict[str, str]): Dictionary with keys for country and language.
            - 'primaryOrganizationType' (str): The primary type of the organization.

    Raises:
        TypeError: If organization_id is not a string or if organization_data is not a dictionary.
        ValueError: If organization_id is an empty string, if organization_data is empty
        ValidationError: If validation fails for any field within organization_data (e.g., invalid format, empty strings, or incorrect enum values).
    """
    if not isinstance(organization_id, str):
        raise TypeError("organization_id must be a string.")
    if not organization_id:
        raise ValueError("organization_id cannot be an empty string.")

    if not isinstance(organization_data, dict):
        raise TypeError("organization_data must be a dictionary.")
    if not organization_data:
        raise ValueError("organization_data cannot be empty.")

    if organization_id not in DB["organizations"]:
        raise OrganizationNotFound("Organization not found.")

    validated_data = OrganizationUpdateModel(**organization_data)
    update_data = validated_data.model_dump(exclude_unset=True)

    if not update_data:
        raise ValueError("No valid fields to update were provided.")

    existing_org = DB["organizations"][organization_id]
    
    # Recursively update the existing organization data
    def recursive_update(original, updates):
        for key, value in updates.items():
            if isinstance(value, dict) and key in original and isinstance(original[key], dict):
                original[key] = recursive_update(original[key], value)
            else:
                original[key] = value
        return original

    updated_org = recursive_update(existing_org, update_data)
    DB["organizations"][organization_id] = updated_org
    
    return {"data": updated_org}

@tool_spec(
    spec={
        'name': 'delete_organization_by_id',
        'description': 'Deletes an organization from the database by its ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'organization_id': {
                    'type': 'string',
                    'description': 'Unique identifier of the organization to delete.'
                }
            },
            'required': [
                'organization_id'
            ]
        }
    }
)
def delete_organization(organization_id: str) -> Dict[str, Any]:
    """
    Deletes an organization from the database by its ID.

    Args:
        organization_id (str): Unique identifier of the organization to delete.

    Returns:
        Dict[str, Any]:
        - On successful deletion, returns a dictionary with the following keys and value types:
            - 'status' (str): Success message confirming deletion of the organization.

    Raises:
        InvalidOrganizationIdError: If 'organization_id' is not non-empty string.
        OrganizationNotFoundError: If the organization is not found in the database.
    """
    if not isinstance(organization_id, str) or not organization_id.strip():
        raise InvalidOrganizationIdError(f"Argument 'organization_id' must be a non-empty string, but got {type(organization_id).__name__}.")

    if organization_id not in DB["organizations"]:
        raise OrganizationNotFoundError(f"Organization with ID {organization_id} not found.")
    del DB["organizations"][organization_id]
    return {"status": f"Organization {organization_id} deleted."}

@tool_spec(
    spec={
        'name': 'delete_organization_by_vanity_name',
        'description': 'Deletes organization(s) from the database by vanity name.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query_field': {
                    'type': 'string',
                    'description': "Query parameter expected to be 'vanityName'."
                },
                'vanity_name': {
                    'type': 'string',
                    'description': "The organization's vanity name to delete."
                }
            },
            'required': [
                'query_field',
                'vanity_name'
            ]
        }
    }
)
def delete_organization_by_vanity_name(query_field: str,
                                        vanity_name: str) -> Dict[str, Any]:
    """
    Deletes organization(s) from the database by vanity name.

    Args:
        query_field (str): Query parameter expected to be 'vanityName'.
        vanity_name (str): The organization's vanity name to delete.

    Returns:
        Dict[str, Any]:
        - On successful deletion, returns a dictionary with the following keys and value types:
            - 'status' (str): Success message confirming deletion of organizations with the specified vanity name.

    Raises:
        InvalidQueryFieldError: If query_field is not a string or not 'vanityName'.
        InvalidVanityNameError: If vanity_name is not a string, empty, or contains only whitespace.
        OrganizationNotFoundError: If no organization with the given vanity name is found.
    """
    # Add explicit type validation for query_field
    if not isinstance(query_field, str):
        raise InvalidQueryFieldError(f"Argument 'query_field' must be a string, but got {type(query_field).__name__}.")
    
    # Add explicit type validation for vanity_name
    if not isinstance(vanity_name, str):
        raise InvalidVanityNameError(f"Argument 'vanity_name' must be a string, but got {type(vanity_name).__name__}.")
    
    # Add empty string validation for vanity_name
    if not vanity_name.strip():
        raise InvalidVanityNameError("Argument 'vanity_name' must be a non-empty string.")
    
    if query_field != "vanityName":
        raise InvalidQueryFieldError("Query parameter must be 'vanityName'.")
    
    to_delete = [org_id for org_id, org in DB["organizations"].items() if org.get("vanityName") == vanity_name]
    if not to_delete:
        raise OrganizationNotFoundError(f"No organization found with vanity name '{vanity_name}'.")
    
    for org_id in to_delete:
        del DB["organizations"][org_id]
    return {"status": f"Organizations with vanity name '{vanity_name}' deleted."}

