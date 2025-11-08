from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/GroupsPickerApi.py

from .SimulationEngine.db import DB
from typing import Optional, Dict, List


@tool_spec(
    spec={
        'name': 'find_groups_for_picker',
        'description': """ Search for groups matching a query string.
        
        This method searches for groups whose names contain the specified query string.
        Supports filtering, exclusions, and max results. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The search string to match against group names.
                    If None or not provided, all groups will be returned.
                    Must be a string if provided. """
                },
                'exclude': {
                    'type': 'array',
                    'description': """ Group names to exclude from results.
                    Cannot be used with excludeId parameter. """,
                    'items': {
                        'type': 'string'
                    }
                },
                'excludeId': {
                    'type': 'array',
                    'description': """ Group IDs to exclude from results.
                    Cannot be used with exclude parameter. """,
                    'items': {
                        'type': 'string'
                    }
                },
                'maxResults': {
                    'type': 'integer',
                    'description': """ Maximum number of groups to return.
                    Defaults to 20. Must be a positive integer. """
                },
                'caseInsensitive': {
                    'type': 'boolean',
                    'description': """ Whether search should be case-insensitive.
                    Defaults to False (case-sensitive) to match Jira API behavior. """
                },
                'accountId': {
                    'type': 'string',
                    'description': """ The account ID (UUID key) of the user to find groups for.
                    Returns only groups that contain this user. Cannot be empty or whitespace-only if provided. """
                }
            },
            'required': []
        }
    }
)
def find_groups(
    query: Optional[str] = None,
    exclude: Optional[List[str]] = None,
    excludeId: Optional[List[str]] = None,
    maxResults: Optional[int] = 20,
    caseInsensitive: Optional[bool] = False,
    accountId: Optional[str] = None
) -> Dict[str, List[str]]:
    """
    Search for groups matching a query string.

    This method searches for groups whose names contain the specified query string.
    Supports filtering, exclusions, and max results.

    Args:
        query (Optional[str]): The search string to match against group names.
            If None or not provided, all groups will be returned.
            Must be a string if provided.
        exclude (Optional[List[str]]): Group names to exclude from results.
            Cannot be used with excludeId parameter.
        excludeId (Optional[List[str]]): Group IDs to exclude from results.
            Cannot be used with exclude parameter.
        maxResults (Optional[int]): Maximum number of groups to return.
            Defaults to 20. Must be a positive integer.
        caseInsensitive (Optional[bool]): Whether search should be case-insensitive.
            Defaults to False (case-sensitive) to match Jira API behavior.
        accountId (Optional[str]): The account ID (UUID key) of the user to find groups for.
            Returns only groups that contain this user. Cannot be empty or whitespace-only if provided.

    Returns:
        Dict[str, List[str]]: A dictionary containing:
            - groups (List[str]): A list of group names that match the criteria.
                Each item is a group name as a string.

    Raises:
        TypeError: If any parameter has an invalid type.
        ValueError: If exclude and excludeId are both provided, maxResults is not positive,
                   or accountId is empty.
    """
    # Input type validation
    if query is not None and not isinstance(query, str):
        raise TypeError(f"query must be a string or None, got {type(query).__name__}.")
    
    if exclude is not None and not isinstance(exclude, list):
        raise TypeError(f"exclude must be a list or None, got {type(exclude).__name__}.")
    
    if excludeId is not None and not isinstance(excludeId, list):
        raise TypeError(f"excludeId must be a list or None, got {type(excludeId).__name__}.")
    
    if maxResults is not None and not isinstance(maxResults, int):
        raise TypeError(f"maxResults must be an integer or None, got {type(maxResults).__name__}.")
    
    if caseInsensitive is not None and not isinstance(caseInsensitive, bool):
        raise TypeError(f"caseInsensitive must be a boolean or None, got {type(caseInsensitive).__name__}.")
    
    if accountId is not None and not isinstance(accountId, str):
        raise TypeError(f"accountId must be a string or None, got {type(accountId).__name__}.")
    
    # Input value validation
    if exclude is not None and excludeId is not None:
        raise ValueError("Cannot provide both 'exclude' and 'excludeId'. Please provide at most one.")
    
    if maxResults is not None and maxResults <= 0:
        raise ValueError("maxResults must be a positive integer.")
    
    if accountId is not None and not accountId.strip():
        raise ValueError("accountId cannot be empty.")
    
    # Validate exclude list contains only strings
    if exclude is not None:
        for i, item in enumerate(exclude):
            if not isinstance(item, str):
                raise TypeError(f"exclude[{i}] must be a string, got {type(item).__name__}.")
    
    # Validate excludeId list contains only strings  
    if excludeId is not None:
        for i, item in enumerate(excludeId):
            if not isinstance(item, str):
                raise TypeError(f"excludeId[{i}] must be a string, got {type(item).__name__}.")
    
    # Step 1: Get all groups
    all_groups = DB.get("groups", {})
    
    # Step 2: Filter by accountId if provided (find groups containing this user)
    if accountId is not None:
        # Look up the username from the accountId (user key/UUID)
        users_db = DB.get("users", {})
        
        # accountId must be a valid user key (UUID) in the users database
        if accountId not in users_db:
            # User not found - return empty results
            all_groups = {}
        else:
            # Get the username from the user record
            username = users_db[accountId].get("name")
            
            # Filter groups that contain this user
            filtered_groups = {}
            for group_name, group_data in all_groups.items():
                if isinstance(group_data, dict) and username in group_data.get("users", []):
                    filtered_groups[group_name] = group_data
            all_groups = filtered_groups
    
    # Step 3: Apply query filtering
    if query is not None and query != "":
        matched_names = []
        for group_name in all_groups.keys():
            if caseInsensitive:
                # Case-insensitive search
                if query.lower() in group_name.lower():
                    matched_names.append(group_name)
            else:
                # Case-sensitive search (Jira default)
                if query in group_name:
                    matched_names.append(group_name)
    else:
        # No query or empty query - return all groups
        matched_names = list(all_groups.keys())
    
    # Step 4: Apply exclusions
    if exclude is not None:
        exclude_set = set(exclude)
        matched_names = [name for name in matched_names if name not in exclude_set]
    
    if excludeId is not None:
        # Convert group IDs to names for exclusion
        exclude_names_by_id = set()
        for group_name, group_data in all_groups.items():
            if isinstance(group_data, dict) and group_data.get("groupId") in excludeId:
                exclude_names_by_id.add(group_name)
        matched_names = [name for name in matched_names if name not in exclude_names_by_id]
    
    # Step 5: Apply maxResults pagination
    if maxResults is not None:
        matched_names = matched_names[:maxResults]
    
    return {"groups": matched_names}