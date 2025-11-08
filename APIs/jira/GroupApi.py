from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/GroupApi.py
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import GroupAlreadyExistsError
from typing import Any, Dict, List, Optional
import uuid


@tool_spec(
    spec={
        'name': 'get_group_by_name',
        'description': """ Retrieve a specific group by its name or ID.
        
        This method returns detailed information about a specific group
        identified by either its name or groupId. Groups in Jira are used to manage user permissions
        and access control. As a group's name can change, use of groupId is recommended to identify a group.
        Exactly one of groupname or groupId must be provided. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'groupname': {
                    'type': 'string',
                    'description': 'The name of the group to retrieve. Cannot be empty or whitespace-only.'
                },
                'groupId': {
                    'type': 'string',
                    'description': 'The ID of the group to retrieve. Cannot be empty or whitespace-only.'
                }
            },
            'required': []
        }
    }
)
def get_group(groupname: Optional[str] = None, groupId: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Retrieve a specific group by its name or ID.

    This method returns detailed information about a specific group
    identified by either its name or groupId. Groups in Jira are used to manage user permissions
    and access control. As a group's name can change, use of groupId is recommended to identify a group.
    Exactly one of groupname or groupId must be provided.

    Args:
        groupname (Optional[str]): The name of the group to retrieve. Cannot be empty or whitespace-only.
        groupId (Optional[str]): The ID of the group to retrieve. Cannot be empty or whitespace-only.
 
    Returns:
        Dict[str, Dict[str, Any]]: A dictionary containing:
            - group (Dict[str, Any]): The group object containing:
                - groupId (str): The unique identifier of the group
                - name (str): The name of the group
                - users (List[str]): List of names of users in the group

    Raises:
        TypeError: If provided parameters are not strings.
        ValueError: If neither or both parameters are provided, if parameters are empty/whitespace-only, 
                   or if the group does not exist in the database.
    """
    # Validate that exactly one parameter is provided
    if (groupname is None and groupId is None) or (groupname is not None and groupId is not None):
        raise ValueError("Exactly one of 'groupname' or 'groupId' must be provided.")
    
    # Handle backward compatibility - if only groupname is provided (including None)
    if groupId is None:
        # Original behavior for groupname-only calls
        if not isinstance(groupname, str):
            raise TypeError(f"Expected groupname to be a string, but got {type(groupname).__name__}.")
        if not groupname or groupname.isspace():
            raise ValueError("groupname cannot be empty or consist only of whitespace.")
        
        # Search by group name
        group_data = DB["groups"].get(groupname)
        if not group_data:
            raise ValueError(f"Group '{groupname}' not found.")
        return {"group": group_data}
    
    # Handle groupId-only calls
    if groupname is None:
        if not isinstance(groupId, str):
            raise TypeError(f"Expected groupId to be a string, but got {type(groupId).__name__}.")
        if not groupId or groupId.isspace():
            raise ValueError("groupId cannot be empty or consist only of whitespace.")
        
        # Search by group ID
        for group_data in DB["groups"].values():
            if group_data.get("groupId") == groupId:
                return {"group": group_data}
        raise ValueError(f"Group with ID '{groupId}' not found.")


@tool_spec(
    spec={
        'name': 'update_group_members_by_name',
        'description': """ Update the members of an existing group.
        
        This method allows updating the list of users in a specific group.
        The group must exist before it can be updated. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'groupname': {
                    'type': 'string',
                    'description': 'The name of the group to update'
                },
                'users': {
                    'type': 'array',
                    'description': 'List of usernames to add to the group',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'groupname',
                'users'
            ]
        }
    }
)
def update_group(groupname: str, users: List[str]) -> Dict[str, Any]:
    """
    Update the members of an existing group.

    This method allows updating the list of users in a specific group.
    The group must exist before it can be updated.

    Args:
        groupname (str): The name of the group to update
        users (List[str]): List of usernames to add to the group

    Returns:
        Dict[str, Any]: A dictionary containing:
            - {groupname} (Dict[str, Any]): The updated group object containing:
                - groupId (str): The unique identifier of the group
                - name (str): The name of the group
                - users (List[str]): List of usernames in the group

    Raises:
        TypeError: If groupname is not a string or users is not a list
        ValueError: If groupname is empty, whitespace-only, or if the group does not exist
        ValueError: If any user in the users list is not a string or is empty/whitespace-only
    """
    # Input validation for groupname
    if not isinstance(groupname, str):
        raise TypeError(f"Expected groupname to be a string, but got {type(groupname).__name__}.")
    if not groupname or groupname.isspace():
        raise ValueError("groupname cannot be empty or consist only of whitespace.")
    
    # Input validation for users
    if not isinstance(users, List):
        raise TypeError(f"Expected users to be a List, but got {type(users).__name__}.")
    
    # Validate each user in the List
    for i, user in enumerate(users):
        if not isinstance(user, str):
            raise TypeError(f"Expected all users to be strings, but user at index {i} is {type(user).__name__}.")
        if not user or user.isspace():
            raise ValueError(f"User at index {i} cannot be empty or consist only of whitespace.")

    # Check if group exists
    if groupname not in DB["groups"]:
        raise ValueError(f"Group '{groupname}' does not exist.")
    
    # Update the group while preserving groupId
    existing_group = DB["groups"][groupname]
    updated_group = {"groupId": existing_group.get("groupId"), "name": groupname, "users": users}
    DB["groups"][groupname] = updated_group
    return {groupname: updated_group}


@tool_spec(
    spec={
        'name': 'create_group',
        'description': """ Create a new group.
        
        This method creates a new group with the specified name. The group
        will initially have no members. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The name of the group to create.'
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def create_group(name: str) -> Dict[str, Any]:
    """
    Create a new group.

    This method creates a new group with the specified name. The group
    will initially have no members.

    Args:
        name (str): The name of the group to create.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - created (bool): True if the group was successfully created.
            - group (Dict[str, Any]): The created group object containing:
                - groupId (str): The unique identifier of the group.
                - name (str): The name of the group.
                - users (List[str]): Empty list of users.

    Raises:
        TypeError: If 'name' is not a string.
        ValueError: If 'name' is empty or consists only of whitespace.
        GroupAlreadyExistsError: If the group with the given 'name' already exists.
    """
    # Input validation
    if not isinstance(name, str):
        raise TypeError("Argument 'name' must be a string.")
    if not name or name.isspace(): # Check for empty or whitespace-only string
        raise ValueError("Argument 'name' cannot be empty or consist only of whitespace.")

    # Core logic (adapted from original to raise exceptions)
    # DB is assumed to be a globally available dictionary representing the database.
    if name in DB["groups"]:
        raise GroupAlreadyExistsError(f"Group '{name}' already exists.")
    
    # Generate unique group ID using UUID format
    group_id = str(uuid.uuid4())
    
    # Create the new group with groupId included
    new_group = {"groupId": group_id, "name": name, "users": []}
    DB["groups"][name] = new_group
    return {"created": True, "group": new_group}


@tool_spec(
    spec={
        'name': 'delete_group_by_name',
        'description': """ Delete an existing group.
        
        This method permanently removes a group from the system. All users
        in the group will lose their group-based permissions. As a group's name can change, 
        use of groupId is recommended to identify a group. Exactly one of groupname or groupId must be provided. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'groupname': {
                    'type': 'string',
                    'description': 'The name of the group to delete. Cannot be used with groupId parameter. Cannot be empty or whitespace-only.'
                },
                'groupId': {
                    'type': 'string',
                    'description': 'The ID of the group to delete. Cannot be used with groupname parameter. Cannot be empty or whitespace-only.'
                }
            },
            'required': []
        }
    }
)
def delete_group(
    groupname: Optional[str] = None, 
    groupId: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete an existing group.

    This method permanently removes a group from the system. All users
    in the group will lose their group-based permissions. As a group's name can change, 
    use of groupId is recommended to identify a group. Exactly one of groupname or groupId must be provided.

    Args:
        groupname (Optional[str]): The name of the group to delete. Cannot be used with groupId parameter. Cannot be empty or whitespace-only.
        groupId (Optional[str]): The ID of the group to delete. Cannot be used with groupname parameter. Cannot be empty or whitespace-only.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - deleted (str): The name of the deleted group

    Raises:
        TypeError: If provided parameters are not strings.
        ValueError: If neither or both group identifiers are provided, if parameters are empty/whitespace-only,
                   or if the group does not exist.
    """
    # Validate that exactly one group identifier is provided
    if (groupname is None and groupId is None) or (groupname is not None and groupId is not None):
        raise ValueError("Exactly one of 'groupname' or 'groupId' must be provided.")
    
    # Find the group to delete
    group_to_delete = None
    group_name = None
    
    if groupname is not None:
        if not isinstance(groupname, str):
            raise TypeError("groupname must be a string.")
        if not groupname or not groupname.strip():
            raise ValueError("groupname cannot be empty or whitespace-only.")
        
        if groupname not in DB["groups"]:
            raise ValueError(f"Group '{groupname}' does not exist.")
        
        group_to_delete = DB["groups"][groupname]
        group_name = groupname
    
    else:  # groupId is not None
        if not isinstance(groupId, str):
            raise TypeError("groupId must be a string.")
        if not groupId or not groupId.strip():
            raise ValueError("groupId cannot be empty or whitespace-only.")
        
        # Find group by ID
        for name, group_data in DB["groups"].items():
            if group_data.get("groupId") == groupId:
                group_to_delete = group_data
                group_name = name
                break
        
        if not group_to_delete:
            raise ValueError(f"Group with ID '{groupId}' does not exist.")
    
    # Delete the group
    DB["groups"].pop(group_name)
    
    return {"deleted": group_name}