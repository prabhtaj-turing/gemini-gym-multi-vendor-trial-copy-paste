from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/VersionApi.py
from .SimulationEngine.db import DB
from .SimulationEngine.utils import _generate_id
from typing import Dict, Any, Optional

@tool_spec(
    spec={
        'name': 'get_version_by_id',
        'description': 'Get a version by ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ver_id': {
                    'type': 'string',
                    'description': 'The ID of the version to get.'
                }
            },
            'required': [
                'ver_id'
            ]
        }
    }
)
def get_version(ver_id: str) -> Dict[str, Any]:
    """
    Get a version by ID.

    Args:
        ver_id (str): The ID of the version to get.

    Returns:
        Dict[str, Any]: A dictionary containing the version's information with all enhanced fields:
            - id (str): The ID of the version.
            - name (str): The name of the version.
            - description (str): The description of the version.
            - archived (bool): Whether the version is archived.
            - released (bool): Whether the version is released.
            - releaseDate (str): The release date of the version.
            - userReleaseDate (str): The user release date of the version.
            - project (str): The project of the version.
            - projectId (int): The project ID of the version.
            - expand (str): Additional data to expand in the response.
            - moveUnfixedIssuesTo (str): URL for moving unfixed issues.
            - overdue (bool): Whether the version is overdue.
            - releaseDateSet (bool): Whether the release date is set.
            - self (str): Self-reference URL for this version.
            - startDate (str): The start date of the version.
            - startDateSet (bool): Whether the start date is set.
            - userStartDate (str): The user-friendly start date.

    Raises:
        ValueError: If the ver_id is empty or not found in the database
        TypeError: If the ver_id is not a string
    """
    # input validation
    if not isinstance(ver_id, str):
        raise TypeError("ver_id must be a string")
    
    if ver_id.strip() == "":
        raise ValueError("ver_id cannot be empty")
    
    # get version from the database by ver_id
    if "versions" not in DB:
        DB["versions"] = {}
        
    v = DB["versions"].get(ver_id)
    if not v:
        raise ValueError(f"Version '{ver_id}' not found.")
    
    # Create a copy to avoid modifying the original DB data
    version = v.copy()
    
    # Ensure dynamic URLs are present and correctly formatted
    base_url = DB.get("server_info", {}).get("baseUrl", "http://localhost:8090/jira")
    
    # Generate/update dynamic fields if they're missing or need refreshing
    if "self" not in version or not version["self"]:
        version["self"] = f"{base_url}/rest/api/2/version/{ver_id}"
    
    if "moveUnfixedIssuesTo" not in version or not version["moveUnfixedIssuesTo"]:
        version["moveUnfixedIssuesTo"] = f"{base_url}/rest/api/2/version/{ver_id}/move"
    
    return version


@tool_spec(
    spec={
        'name': 'create_version',
        'description': 'Create a new version.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The name of the version. Required and cannot be empty or whitespace-only.'
                },
                'description': {
                    'type': 'string',
                    'description': 'The description of the version. Defaults to None.'
                },
                'archived': {
                    'type': 'boolean',
                    'description': 'Whether the version is archived. Defaults to None.'
                },
                'released': {
                    'type': 'boolean',
                    'description': 'Whether the version is released. Defaults to None.'
                },
                'release_date': {
                    'type': 'string',
                    'description': 'The release date of the version. Defaults to None.'
                },
                'user_release_date': {
                    'type': 'string',
                    'description': 'The user release date of the version. Defaults to None.'
                },
                'project': {
                    'type': 'string',
                    'description': 'The project of the version. Defaults to None.'
                },
                'project_id': {
                    'type': 'integer',
                    'description': 'The project ID of the version. Defaults to None.'
                },
                'expand': {
                    'type': 'string',
                    'description': 'Additional data to expand in the response. Defaults to None.'
                },
                'id': {
                    'type': 'string',
                    'description': 'Custom ID for the version. If empty, auto-generated. Defaults to None.'
                },
                'move_unfixed_issues_to': {
                    'type': 'string',
                    'description': 'URL for moving unfixed issues. Defaults to None.'
                },
                'overdue': {
                    'type': 'boolean',
                    'description': 'Whether the version is overdue. Defaults to None.'
                },
                'release_date_set': {
                    'type': 'boolean',
                    'description': 'Whether the release date is set. Defaults to None.'
                },
                'start_date': {
                    'type': 'string',
                    'description': 'The start date of the version. Defaults to None.'
                },
                'start_date_set': {
                    'type': 'boolean',
                    'description': 'Whether the start date is set. Defaults to None.'
                },
                'user_start_date': {
                    'type': 'string',
                    'description': 'The user-friendly start date. Defaults to None.'
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def create_version(
    name: str,
    description: Optional[str] = None,
    archived: Optional[bool] = None,
    released: Optional[bool] = None,
    release_date: Optional[str] = None,
    user_release_date: Optional[str] = None,
    project: Optional[str] = None,
    project_id: Optional[int] = None,
    expand: Optional[str] = None,
    id: Optional[str] = None,
    move_unfixed_issues_to: Optional[str] = None,
    overdue: Optional[bool] = None,
    release_date_set: Optional[bool] = None,
    start_date: Optional[str] = None,
    start_date_set: Optional[bool] = None,
    user_start_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new version.

    Args:
        name (str): The name of the version. Required and cannot be empty or whitespace-only.
        description (Optional[str]): The description of the version. Defaults to None.
        archived (Optional[bool]): Whether the version is archived. Defaults to None.
        released (Optional[bool]): Whether the version is released. Defaults to None.
        release_date (Optional[str]): The release date of the version. Defaults to None.
        user_release_date (Optional[str]): The user release date of the version. Defaults to None.
        project (Optional[str]): The project of the version. Defaults to None.
        project_id (Optional[int]): The project ID of the version. Defaults to None.
        expand (Optional[str]): Additional data to expand in the response. Defaults to None.
        id (Optional[str]): Custom ID for the version. If empty, auto-generated. Defaults to None.
        move_unfixed_issues_to (Optional[str]): URL for moving unfixed issues. Defaults to None.
        overdue (Optional[bool]): Whether the version is overdue. Defaults to None.
        release_date_set (Optional[bool]): Whether the release date is set. Defaults to None.
        start_date (Optional[str]): The start date of the version. Defaults to None.
        start_date_set (Optional[bool]): Whether the start date is set. Defaults to None.
        user_start_date (Optional[str]): The user-friendly start date. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing the version's information.
            - created (bool): Whether the version was created.
            - version (dict): The version's information including all provided fields.

    Raises:
        TypeError: If parameters are not of the expected types
        ValueError: If the required field 'name' is missing or empty, or if custom ID already exists
    """
    # Input validation - type checking
    if not isinstance(name, str):
        raise TypeError("name parameter must be a string")
    
    if description is not None and not isinstance(description, str):
        raise TypeError("description parameter must be a string")
    
    if archived is not None and not isinstance(archived, bool):
        raise TypeError("archived parameter must be a boolean")
        
    if released is not None and not isinstance(released, bool):
        raise TypeError("released parameter must be a boolean")
        
    if release_date is not None and not isinstance(release_date, str):
        raise TypeError("release_date parameter must be a string")
        
    if user_release_date is not None and not isinstance(user_release_date, str):
        raise TypeError("user_release_date parameter must be a string")
        
    if project is not None and not isinstance(project, str):
        raise TypeError("project parameter must be a string")
        
    if project_id is not None and not isinstance(project_id, int):
        raise TypeError("project_id parameter must be an integer")
    
    if expand is not None and not isinstance(expand, str):
        raise TypeError("expand parameter must be a string")
        
    if id is not None and not isinstance(id, str):
        raise TypeError("id parameter must be a string")
        
    if move_unfixed_issues_to is not None and not isinstance(move_unfixed_issues_to, str):
        raise TypeError("move_unfixed_issues_to parameter must be a string")
        
    if overdue is not None and not isinstance(overdue, bool):
        raise TypeError("overdue parameter must be a boolean")
        
    if release_date_set is not None and not isinstance(release_date_set, bool):
        raise TypeError("release_date_set parameter must be a boolean")
        
    if start_date is not None and not isinstance(start_date, str):
        raise TypeError("start_date parameter must be a string")
        
    if start_date_set is not None and not isinstance(start_date_set, bool):
        raise TypeError("start_date_set parameter must be a boolean")
        
    if user_start_date is not None and not isinstance(user_start_date, str):
        raise TypeError("user_start_date parameter must be a string")
    
    # Input validation - value checking
    if not name or not name.strip():
        raise ValueError("name parameter cannot be empty or whitespace-only")

    # Handle version ID
    if "versions" not in DB:
        DB["versions"] = {}
    
    if id and id.strip():
        # Use custom ID if provided
        ver_id = id.strip()
        if ver_id in DB["versions"]:
            raise ValueError(f"Version with ID '{ver_id}' already exists")
    else:
        # Generate a new version ID
        ver_id = _generate_id("VER", DB["versions"])

    # Get base URL for self link
    base_url = DB.get("server_info", {}).get("baseUrl", "http://localhost:8090/jira")
    self_url = f"{base_url}/rest/api/2/version/{ver_id}"

    # Create the version object with defaults for None values
    version = {
        "id": ver_id,
        "name": name,
        "description": description if description is not None else "",
        "archived": archived if archived is not None else False,
        "released": released if released is not None else False,
        "releaseDate": release_date if release_date is not None else "",
        "userReleaseDate": user_release_date if user_release_date is not None else "",
        "project": project if project is not None else "",
        "projectId": project_id if project_id is not None else 0,
        "expand": expand if expand is not None else "",
        "moveUnfixedIssuesTo": move_unfixed_issues_to if move_unfixed_issues_to else f"{base_url}/rest/api/2/version/{ver_id}/move",
        "overdue": overdue if overdue is not None else False,
        "releaseDateSet": release_date_set if release_date_set is not None else False,
        "self": self_url,
        "startDate": start_date if start_date is not None else "",
        "startDateSet": start_date_set if start_date_set is not None else False,
        "userStartDate": user_start_date if user_start_date is not None else "",
    }

    # Store in DB
    DB["versions"][ver_id] = version

    return {"created": True, "version": version}


@tool_spec(
    spec={
        'name': 'delete_version_by_id',
        'description': 'Delete a version.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ver_id': {
                    'type': 'string',
                    'description': 'The ID of the version to delete. Cannot be empty or whitespace-only.'
                },
                'move_fix_issues_to': {
                    'type': 'string',
                    'description': """ The ID of the version to move the fixed issues to. 
                    Currently not used. Defaults to None. """
                },
                'move_affected_issues_to': {
                    'type': 'string',
                    'description': """ The ID of the version to move the affected issues to. 
                    Currently not used. Defaults to None. """
                }
            },
            'required': [
                'ver_id'
            ]
        }
    }
)
def delete_version_and_replace_values(
    ver_id: str, move_fix_issues_to: Optional[str] = None, move_affected_issues_to: Optional[str] = None
) -> Dict[str, Any]:
    """
    Delete a version.

    Args:
        ver_id (str): The ID of the version to delete. Cannot be empty or whitespace-only.
        move_fix_issues_to (Optional[str]): The ID of the version to move the fixed issues to. 
                                           Currently not used. Defaults to None.
        move_affected_issues_to (Optional[str]): The ID of the version to move the affected issues to. 
                                                Currently not used. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary containing the version's information.
            - deleted (str): The ID of the version that was deleted.
            - moveFixIssuesTo (str): The ID of the version to move the fixed issues to.
            - moveAffectedIssuesTo (str): The ID of the version to move the affected issues to.
    Raises:
        TypeError: If ver_id is not a string, or if move_fix_issues_to/move_affected_issues_to 
                  are not strings when provided
        ValueError: If ver_id is empty or whitespace-only, or if the version does not exist
    """
    # Input validation - type checking
    if not isinstance(ver_id, str):
        raise TypeError("ver_id parameter must be a string")
    
    if move_fix_issues_to is not None and not isinstance(move_fix_issues_to, str):
        raise TypeError("move_fix_issues_to parameter must be a string when provided")
    
    if move_affected_issues_to is not None and not isinstance(move_affected_issues_to, str):
        raise TypeError("move_affected_issues_to parameter must be a string when provided")
    
    # Input validation - value checking
    if not ver_id or not ver_id.strip():
        raise ValueError("ver_id parameter cannot be empty or whitespace-only")
    
    if "versions" not in DB:
        DB["versions"] = {}
    if ver_id not in DB["versions"]:
        raise ValueError(f"Version '{ver_id}' does not exist")
    DB["versions"].pop(ver_id)
    return {
        "deleted": ver_id,
        "moveFixIssuesTo": move_fix_issues_to,
        "moveAffectedIssuesTo": move_affected_issues_to,
    }


@tool_spec(
    spec={
        'name': 'get_version_related_issue_counts_by_id',
        'description': 'Get the related issue counts for a version.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ver_id': {
                    'type': 'string',
                    'description': """ The ID of the version to get the related issue counts for.
                    Cannot be empty or whitespace-only. """
                }
            },
            'required': [
                'ver_id'
            ]
        }
    }
)
def get_version_related_issue_counts(ver_id: str) -> Dict[str, int]:
    """
    Get the related issue counts for a version.

    Args:
        ver_id (str): The ID of the version to get the related issue counts for.
                     Cannot be empty or whitespace-only.

    Returns:
        Dict[str, int]: A dictionary containing the related issue counts.
            - fixCount (int): The number of issues that reference this version as a fix version.
            - affectedCount (int): The number of issues that reference this version as an affected version.

    Raises:
        TypeError: If ver_id is not a string
        ValueError: If ver_id is empty, whitespace-only, or the version does not exist
    """
    # Input validation
    if not isinstance(ver_id, str):
        raise TypeError(f"ver_id must be a string, got {type(ver_id).__name__}")
    
    if not ver_id.strip():
        raise ValueError("ver_id cannot be empty or whitespace")
    
    # Check if versions exist in DB
    if "versions" not in DB:
        DB["versions"] = {}
    
    # Validate that the version exists
    if ver_id not in DB["versions"]:
        raise ValueError(f"Version '{ver_id}' not found")
    
    # Initialize counters
    fix_count = 0
    affected_count = 0
    
    # Check if issues exist in DB
    if "issues" in DB:
        # Iterate through all issues to count references to this version
        for issue_id, issue_data in DB["issues"].items():
            fields = issue_data.get("fields", {})
            
            # Check for fixVersion field
            fix_versions = fields.get("fixVersion", [])
            if isinstance(fix_versions, list):
                for version in fix_versions:
                    if isinstance(version, dict) and version.get("id") == ver_id:
                        fix_count += 1
                        break
            elif isinstance(fix_versions, dict) and fix_versions.get("id") == ver_id:
                fix_count += 1
            
            # Check for affectedVersion field
            affected_versions = fields.get("affectedVersion", [])
            if isinstance(affected_versions, list):
                for version in affected_versions:
                    if isinstance(version, dict) and version.get("id") == ver_id:
                        affected_count += 1
                        break
            elif isinstance(affected_versions, dict) and affected_versions.get("id") == ver_id:
                affected_count += 1
    
    return {"fixCount": fix_count, "affectedCount": affected_count}
