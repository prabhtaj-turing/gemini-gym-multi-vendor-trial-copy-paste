from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/FilterApi.py

from .SimulationEngine.db import DB
from typing import Any, Dict, Optional


@tool_spec(
    spec={
        'name': 'get_all_filters',
        'description': """ Retrieve all filters from Jira.
        
        This method returns a list of all filters in the system. Filters in Jira
        are used to save and share search queries, allowing users to quickly
        access commonly used issue searches. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_filters() -> Dict[str, Any]:
    """
    Retrieve all filters from Jira.

    This method returns a list of all filters in the system. Filters in Jira
    are used to save and share search queries, allowing users to quickly
    access commonly used issue searches.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - filters (List[Dict[str, Any]]): A list of filter objects,
                each containing:
                - id (str): The unique identifier for the filter
                - name (str): The name of the filter
                - description (str): A description of the filter's purpose
                - owner (Dict[str, str]): Information about the filter owner
                - jql (str): The JQL query that defines the filter
                - favoriteCount (int): Number of users who have favorited the filter
                - sharePermissions (List[Dict[str, Any]]): List of sharing permissions of the format
                    - id (str): The unique identifier for the permission
                    - type (str): The type of permission e.g. "group", "project", "global"
                    - view (bool): Whether the permission allows viewing the filter
                    - edit (bool): Whether the permission allows editing the filter
                    - project (Dict[str, str]): Information about the project that the permission applies to, if type is "project"
                        - id (str): The unique identifier for the project
                        - key (str): The key of the project
                        - name (str): The name of the project
                        - avatarUrls (List[str]): The URL of the project's avatar
                        - self (str): The URL of the project
                        - projectCategory (Dict[str, str]): Information about the category of the project
                            - self (str): The URL of the project category
                            - id (str): The unique identifier for the project category
                            - name (str): The name of the project category
                            - description (str): The description of the project category
                        - role (Dict[str, str]): Information about the role that the permission applies to, if type is "project"
                            - id (str): The unique identifier for the role
                            - name (str): The name of the role
                            - description (str): The description of the role
                            - self (str): The URL of the role
                            - actors (List[Dict[str, str]]): The actors that the role applies to
                                - id (str): The unique identifier for the actor
                                - displayName (str): The display name of the actor
                                - type (str): The type of actor e.g. "group", "user"
                                - name (str): The name of the actor
                        - group (Dict[str, str]): Information about the group that the permission applies to, if type is "group"
                            - self (str): The URL of the group
                            - name (str): The name of the group
    """
    return {"filters": list(DB["filters"].values())}


@tool_spec(
    spec={
        'name': 'get_filter_by_id',
        'description': """ Retrieve a specific filter by its ID.
        
        This method returns detailed information about a specific filter
        identified by its unique ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'filter_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the filter to retrieve'
                }
            },
            'required': [
                'filter_id'
            ]
        }
    }
)
def get_filter(filter_id: str) -> Dict[str, Any]:
    """
    Retrieve a specific filter by its ID.

    This method returns detailed information about a specific filter
    identified by its unique ID.

    Args:
        filter_id (str): The unique identifier of the filter to retrieve

    Returns:
        Dict[str, Any]: A dictionary containing:
            - id (str): The unique identifier for the filter
            - name (str): The name of the filter
            - description (str): A description of the filter's purpose
            - owner (Dict[str, str]): Information about the filter owner
            - jql (str): The JQL query that defines the filter
            - favorite (bool): Whether the filter is a favorite
            - editable (bool): Whether the filter is editable
            - sharePermissions (List[Dict[str, Any]]): List of sharing permissions of the format
                - id (str): The unique identifier for the permission
                - type (str): The type of permission e.g. "group", "project", "global"
                - view (bool): Whether the permission allows viewing the filter
                - edit (bool): Whether the permission allows editing the filter
                - project (Dict[str, str]): Information about the project that the permission applies to, if type is "project"
                    - id (str): The unique identifier for the project
                    - key (str): The key of the project
                    - name (str): The name of the project
                    - avatarUrls (List[str]): The URL of the project's avatar
                    - self (str): The URL of the project
                    - projectCategory (Dict[str, str]): Information about the category of the project
                        - self (str): The URL of the project category
                        - id (str): The unique identifier for the project category
                        - name (str): The name of the project category
                        - description (str): The description of the project category
                - role (Dict[str, str]): Information about the role that the permission applies to, if type is "project"
                    - id (str): The unique identifier for the role
                    - name (str): The name of the role
                    - description (str): The description of the role
                    - self (str): The URL of the role
                    - actors (List[Dict[str, str]]): The actors that the role applies to
                        - id (str): The unique identifier for the actor
                        - displayName (str): The display name of the actor
                        - type (str): The type of actor e.g. "group", "user"
                        - name (str): The name of the actor
                - group (Dict[str, str]): Information about the group that the permission applies to, if type is "group"
                    - self (str): The URL of the group
                    - name (str): The name of the group


    Raises:
        TypeError: If filter_id is not a string
        ValueError: If filter_id is empty or the filter does not exist
    """
    # Input validation
    if not isinstance(filter_id, str):
        raise TypeError("filter_id parameter must be a string")
    
    if not filter_id:
        raise ValueError("filter_id parameter cannot be empty")
    
    flt = DB["filters"].get(filter_id)
    if not flt:
        raise ValueError(f"Filter '{filter_id}' not found.")
    return flt


@tool_spec(
    spec={
        'name': 'update_filter_by_id',
        'description': """ Update an existing filter.
        
        This method allows updating various properties of an existing filter including
        name, JQL query, description, favorite status, and editability. At least one 
        parameter (other than filter_id) must be provided for the update to proceed. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'filter_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the filter to update. Must be non-empty.'
                },
                'name': {
                    'type': 'string',
                    'description': """ The new name for the filter. Must be non-empty if provided. 
                    Empty or whitespace-only strings are invalid. Defaults to None. """
                },
                'jql': {
                    'type': 'string',
                    'description': """ The new JQL query for the filter. Must be non-empty if provided. 
                    Empty or whitespace-only strings are invalid. Defaults to None. """
                },
                'description': {
                    'type': 'string',
                    'description': 'The new description of the filter. Defaults to None.'
                },
                'favorite': {
                    'type': 'boolean',
                    'description': 'Whether the filter should be marked as favorite. Defaults to None.'
                },
                'editable': {
                    'type': 'boolean',
                    'description': 'Whether the filter should be editable. Defaults to None.'
                }
            },
            'required': [
                'filter_id'
            ]
        }
    }
)
def update_filter(
    filter_id: str,
    name: Optional[str] = None,
    jql: Optional[str] = None,
    description: Optional[str] = None,
    favorite: Optional[bool] = None,
    editable: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Update an existing filter.

    This method allows updating various properties of an existing filter including
    name, JQL query, description, favorite status, and editability. At least one 
    parameter (other than filter_id) must be provided for the update to proceed.

    Args:
        filter_id (str): The unique identifier of the filter to update. Must be non-empty.
        name (Optional[str]): The new name for the filter. Must be non-empty if provided. 
                             Empty or whitespace-only strings are invalid. Defaults to None.
        jql (Optional[str]): The new JQL query for the filter. Must be non-empty if provided. 
                            Empty or whitespace-only strings are invalid. Defaults to None.
        description (Optional[str]): The new description of the filter. Defaults to None.
        favorite (Optional[bool]): Whether the filter should be marked as favorite. Defaults to None.
        editable (Optional[bool]): Whether the filter should be editable. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing:
                - updated (bool): True if the filter was successfully updated
                - filter (Dict[str, Any]): The updated filter object containing:
                    - id (str): The unique identifier for the filter
                    - name (str): The name of the filter
                    - jql (str): The JQL query that defines the filter
                    - description (str): The description of the filter
                    - favorite (bool): Whether the filter is a favorite
                    - editable (bool): Whether the filter is editable
                    - sharePermissions (List[Dict[str, Any]]): List of sharing permissions
                        - id (str): The unique identifier for the permission
                        - type (str): The type of permission e.g. "group", "project", "global"
                        - view (bool): Whether the permission allows viewing the filter
                        - edit (bool): Whether the permission allows editing the filter
                        - project (Dict[str, str]): Information about the project that the permission applies to, if type is "project"
                            - id (str): The unique identifier for the project
                            - key (str): The key of the project
                            - name (str): The name of the project
                            - avatarUrls (List[str]): The URL of the project's avatar
                            - self (str): The URL of the project
                            - projectCategory (Dict[str, str]): Information about the category of the project
                                - self (str): The URL of the project category
                                - id (str): The unique identifier for the project category
                                - name (str): The name of the project category
                                - description (str): The description of the project category
                        - role (Dict[str, str]): Information about the role that the permission applies to, if type is "project"
                            - id (str): The unique identifier for the role
                            - name (str): The name of the role
                            - description (str): The description of the role
                            - self (str): The URL of the role
                            - actors (List[Dict[str, str]]): The actors that the role applies to
                                - id (str): The unique identifier for the actor
                                - displayName (str): The display name of the actor
                                - type (str): The type of actor e.g. "group", "user"
                                - name (str): The name of the actor
                        - group (Dict[str, str]): Information about the group that the permission applies to, if type is "group"
                            - self (str): The URL of the group
                            - name (str): The name of the group

    Raises:
        TypeError: If filter_id is not a string, or if name/jql/description are not strings when provided,
                  or if favorite/editable are not booleans when provided
        ValueError: If filter_id is empty, if the filter does not exist, if all update parameters are None,
                   or if name/jql/description are empty strings when provided
    """
    # Input validation - Type checking
    if not isinstance(filter_id, str):
        raise TypeError("filter_id parameter must be a string")
    
    if name is not None and not isinstance(name, str):
        raise TypeError("name parameter must be a string when provided")
        
    if jql is not None and not isinstance(jql, str):
        raise TypeError("jql parameter must be a string when provided")
        
    if description is not None and not isinstance(description, str):
        raise TypeError("description parameter must be a string when provided")
        
    if favorite is not None and not isinstance(favorite, bool):
        raise TypeError("favorite parameter must be a boolean when provided")
        
    if editable is not None and not isinstance(editable, bool):
        raise TypeError("editable parameter must be a boolean when provided")
    
    # Input validation - Value checking
    if not filter_id:
        raise ValueError("filter_id parameter cannot be empty")
        
    if name is not None and not name.strip():
        raise ValueError("name parameter cannot be empty when provided")
        
    if jql is not None and not jql.strip():
        raise ValueError("jql parameter cannot be empty when provided")
    
    # Business rule validation - at least one parameter must be provided for update
    if all(param is None for param in [name, jql, description, favorite, editable]):
        raise ValueError("At least one parameter (name, jql, description, favorite, or editable) must be provided for update")
    
    # Check if filter exists
    flt = DB["filters"].get(filter_id)
    if not flt:
        raise ValueError(f"Filter '{filter_id}' not found")
    
    # Ensure filter has all required fields with default values if missing
    if "description" not in flt:
        flt["description"] = ""
    if "favorite" not in flt:
        flt["favorite"] = False
    if "editable" not in flt:
        flt["editable"] = True
    if "sharePermissions" not in flt:
        flt["sharePermissions"] = []
    
    # Update filter fields
    if name is not None:
        flt["name"] = name.strip()
    if jql is not None:
        flt["jql"] = jql.strip()
    if description is not None:
        flt["description"] = description
    if favorite is not None:
        flt["favorite"] = favorite
    if editable is not None:
        flt["editable"] = editable
    
    return {"updated": True, "filter": flt}
