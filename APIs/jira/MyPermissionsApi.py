from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/MyPermissionsApi.py
from .SimulationEngine.db import DB
from .SimulationEngine.utils import _check_empty_field
from typing import Optional, Dict, Any


@tool_spec(
    spec={
        'name': 'get_current_user_permissions',
        'description': """ Get the current user's permissions.
        
        This method returns the permissions of the current user from the database.
        The permissions are returned as a list of permission keys that the user has access to. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'projectKey': {
                    'type': 'string',
                    'description': 'The key of the project to check permissions for. Defaults to None.'
                },
                'issueKey': {
                    'type': 'string',
                    'description': 'The key of the issue to check permissions for. Defaults to None.'
                }
            },
            'required': []
        }
    }
)
def get_current_user_permissions(
    projectKey: Optional[str] = None, issueKey: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the current user's permissions.

    This method returns the permissions of the current user from the database.
    The permissions are returned as a list of permission keys that the user has access to.

    Args:
        projectKey (Optional[str]): The key of the project to check permissions for. Defaults to None.
        issueKey (Optional[str]): The key of the issue to check permissions for. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - permissions (List[str]): List of permission keys the user has access to, retrieved from the database.

    Raises:
        ValueError: If projectKey or issueKey is an empty string, or if the specified project/issue is not found.
        TypeError: If projectKey or issueKey is not a string.
    """
    # Type validation
    if projectKey is not None and not isinstance(projectKey, str):
        raise TypeError("projectKey must be a string.")
    if issueKey is not None and not isinstance(issueKey, str):
        raise TypeError("issueKey must be a string.")

    # Input validation
    if projectKey is not None:
        err = _check_empty_field("projectKey", projectKey)
        if err:
            raise ValueError(err)
        if projectKey not in DB["projects"]:
            raise ValueError(f"Project '{projectKey}' not found.")

    if issueKey is not None:
        err = _check_empty_field("issueKey", issueKey)
        if err:
            raise ValueError(err)
        if issueKey not in DB["issues"]:
            raise ValueError(f"Issue '{issueKey}' not found.")

    # Get permissions from DB
    permissions = list(DB.get("permissions", {}).keys())

    return {"permissions": permissions}
