from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/ApplicationPropertiesApi.py
from .SimulationEngine.db import DB
from .SimulationEngine.utils import _check_empty_field
from typing import Optional, Dict, Any


@tool_spec(
    spec={
        'name': 'get_application_properties',
        'description': """ Retrieve application properties from Jira.
        
        This method allows fetching either all application properties or a specific property
        by its key. Application properties are system-wide settings that control various
        aspects of Jira's behavior. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'key': {
                    'type': 'string',
                    'description': """ The key of the specific property to retrieve. If not provided,
                    all application properties will be returned. """
                },
                'permissionLevel': {
                    'type': 'string',
                    'description': """ The permission level required to access the property.
                    Valid values: "ADMIN", "USER", "ANONYMOUS". If not provided, all properties
                    will be returned regardless of permission level. """
                },
                'keyFilter': {
                    'type': 'string',
                    'description': """ A filter to apply to the property keys. If provided,
                    only properties whose keys contain this substring will be returned. """
                }
            },
            'required': []
        }
    }
)
def get_application_properties(
    key: Optional[str] = None,
    permissionLevel: Optional[str] = None,
    keyFilter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieve application properties from Jira.

    This method allows fetching either all application properties or a specific property
    by its key. Application properties are system-wide settings that control various
    aspects of Jira's behavior.

    Args:
        key (Optional[str]): The key of the specific property to retrieve. If not provided,
            all application properties will be returned.
        permissionLevel (Optional[str]): The permission level required to access the property.
            Valid values: "ADMIN", "USER", "ANONYMOUS". If not provided, all properties
            will be returned regardless of permission level.
        keyFilter (Optional[str]): A filter to apply to the property keys. If provided,
            only properties whose keys contain this substring will be returned.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - If key is provided and found:
                - key (str): The property key
                - value (str): The property value as a simple string
            
            - If key is not provided:
                - properties (Dict[str, str]): All application properties as key-value pairs
                  where keys are property names and values are simple strings. Available keys:
                  - siteName (str): The name of the Jira site/instance
                  - maintenanceMode (str): Current maintenance mode status ("on" or "off")

    Raises:
        ValueError: If permissionLevel is provided but is not a valid value
        TypeError: If any parameter is not a string when provided
    """
    # Input validation
    if key is not None and not isinstance(key, str):
        raise TypeError("key parameter must be a string or None")
    
    if permissionLevel is not None:
        if not isinstance(permissionLevel, str):
            raise TypeError("permissionLevel parameter must be a string or None")
        valid_permissions = ["ADMIN", "USER", "ANONYMOUS"]
        if permissionLevel not in valid_permissions:
            raise ValueError(f"permissionLevel must be one of: {', '.join(valid_permissions)}")
    
    if keyFilter is not None and not isinstance(keyFilter, str):
        raise TypeError("keyFilter parameter must be a string or None")
    
    # Get all properties from database
    all_properties = DB["application_properties"]
    
    # Apply permission level filtering if specified
    if permissionLevel:
        # In a real implementation, this would check actual permissions
        # For simulation, we'll filter based on a simple rule
        if permissionLevel == "ADMIN":
            # Admin can see all properties
            filtered_properties = all_properties
        elif permissionLevel == "USER":
            # Users can see most properties except sensitive ones
            filtered_properties = {k: v for k, v in all_properties.items() 
                                 if not k.startswith("admin.")}
        elif permissionLevel == "ANONYMOUS":
            # Anonymous users can only see public properties
            filtered_properties = {k: v for k, v in all_properties.items() 
                                 if k in ["siteName", "maintenanceMode"]}
    else:
        filtered_properties = all_properties
    
    # Apply key filter if specified
    if keyFilter:
        filtered_properties = {k: v for k, v in filtered_properties.items() 
                             if keyFilter.lower() in k.lower()}
    
    # Handle specific key request
    if key:
        if key not in filtered_properties:
            raise ValueError(f"Property '{key}' not found.")
        return {"key": key, "value": filtered_properties[key]}
    
    # Return all filtered properties
    return {"properties": filtered_properties}


@tool_spec(
    spec={
        'name': 'update_application_property_by_id',
        'description': """ Update an application property in Jira.
        
        This method allows modifying the value of an existing application property
        or creating a new one if it doesn't exist. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'string',
                    'description': 'The identifier of the property to update'
                },
                'value': {
                    'type': 'string',
                    'description': 'The new value to set for the property'
                }
            },
            'required': [
                'id',
                'value'
            ]
        }
    }
)
def update_application_property(id: str, value: str) -> dict:
    """
    Update an application property in Jira.

    This method allows modifying the value of an existing application property
    or creating a new one if it doesn't exist.

    Args:
        id (str): The identifier of the property to update
        value (str): The new value to set for the property

    Returns:
        dict: A dictionary containing:
            - updated (bool): True if the property was successfully updated
            - property (str): The ID of the updated property
            - newValue (str): The new value that was set

    Raises:
        TypeError: If either id or value is not a string
        ValueError: If either id or value is empty or invalid
    """
    # Input validation
    if not isinstance(id, str):
        raise TypeError("id parameter must be a string")
    if not isinstance(value, str):
        raise TypeError("value parameter must be a string")
    
    # Check for empty fields
    err = _check_empty_field("id", id) + _check_empty_field("value", value)
    if err:
        raise ValueError(f"Validation error: {err}")
    
    # Update the property
    DB["application_properties"][id] = value
    return {"updated": True, "property": id, "newValue": value}
