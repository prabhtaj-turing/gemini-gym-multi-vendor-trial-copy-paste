from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/IssueApi.py

from typing import Any, Dict, List, Optional
from pydantic import ValidationError
from datetime import datetime
from .SimulationEngine.db import DB
from .SimulationEngine.utils import _generate_id

from .SimulationEngine.models import (
    JiraIssueCreationFields,
    JiraIssueFields,
    BulkIssueOperationRequestModel,
)

from .SimulationEngine.custom_errors import EmptyFieldError, MissingRequiredFieldError, ProjectNotFoundError, UserNotFoundError
from .SimulationEngine.models import IssueFieldsUpdateModel, JiraAssignee, JiraIssueResponse
from .AttachmentApi import list_issue_attachments   


@tool_spec(
    spec={
        'name': 'create_issue',
        'description': """ Create a new issue in Jira.
        
        This method creates a new issue with the specified fields. The issue will be
        assigned a unique ID and stored in the system. Only project and summary are 
        required fields. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'fields': {
                    'type': 'object',
                    'description': 'A dictionary containing the issue fields with:',
                    'properties': {
                        'project': {
                            'type': 'string',
                            'description': 'The project key the issue belongs to.'
                        },
                        'summary': {
                            'type': 'string',
                            'description': 'A brief description of the issue.'
                        },
                        'issuetype': {
                            'type': 'string',
                            'description': """ The type of issue (e.g., 'Bug', 'Task', 'Story').
                               Defaults to 'Task' if not provided. """
                        },
                        'description': {
                            'type': 'string',
                            'description': 'A detailed description of the issue.'
                        },
                        'priority': {
                            'type': 'string',
                            'description': """ The priority of the issue (e.g., 'High', 'Medium', 'Low').
                               Defaults to 'Low' if not provided. """
                        },
                        'status': {
                            'type': 'string',
                            'description': """ The status of the issue (e.g., 'Open', 'Closed', etc).
                               Defaults to 'Open' if not provided. """
                        },
                        'assignee': {
                            'type': 'object',
                            'description': """ The user assigned to the issue with:
                               Defaults to {"name": "Unassigned"} if not provided. """,
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': "The assignee's username (e.g., 'jdoe')"
                                }
                            },
                            'required': [
                                'name'
                            ]
                        },
                        'components': {
                            'type': 'array',
                            'description': 'IDs of Components associated with the issue.',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'due_date': {
                            'type': 'string',
                            'description': 'The due date of the issue. Must be in the format: YYYY-MM-DD if provided.'
                        },
                        'comments': {
                            'type': 'array',
                            'description': 'A list of comments to add to the issue.',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'created': {
                            'type': 'string',
                            'description': """ The creation timestamp of the issue in ISO format
                               (e.g., '2025-07-09T10:30:00' or '2025-07-09T10:30:00Z').
                              If not provided, defaults to current timestamp. """
                        }
                    },
                    'required': [
                        'project',
                        'summary'
                    ]
                }
            },
            'required': [
                'fields'
            ]
        }
    }
)
def create_issue(fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new issue in Jira.

    This method creates a new issue with the specified fields. The issue will be
    assigned a unique ID and stored in the system. Only project and summary are 
    required fields.

    Args:
        fields (Dict[str, Any]): A dictionary containing the issue fields with:
            - project (str): The project key the issue belongs to.
            - summary (str): A brief description of the issue.
            - issuetype (Optional[str]): The type of issue (e.g., 'Bug', 'Task', 'Story'). 
              Defaults to 'Task' if not provided.
            - description (Optional[str]): A detailed description of the issue.
            - priority (Optional[str]): The priority of the issue (e.g., 'High', 'Medium', 'Low'). 
              Defaults to 'Low' if not provided.
            - status (Optional[str]): The status of the issue (e.g., 'Open', 'Closed', etc). 
              Defaults to 'Open' if not provided.
            - assignee (Optional[Dict[str, str]]): The user assigned to the issue with:
                - name (str): The assignee's username (e.g., 'jdoe')
              Defaults to {"name": "Unassigned"} if not provided.
            - components (Optional[List[str]]): IDs of Components associated with the issue.
            - due_date (Optional[str]): The due date of the issue. Must be in the format: YYYY-MM-DD if provided.
            - comments (Optional[List[str]]): A list of comments to add to the issue.
            - created (Optional[str]): The creation timestamp of the issue in ISO format 
              (e.g., '2025-07-09T10:30:00' or '2025-07-09T10:30:00Z'). 
              If not provided, defaults to current timestamp.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - id (str): The unique identifier for the new issue
            - fields (Dict[str, Any]): The fields of the created issue including:
                - project (str): The project key
                - summary (str): Issue summary
                - issuetype (str): The type of issue (defaults to 'Task' if not provided)
                - description (str): Issue description (defaults to empty string if not provided)
                - priority (str): The priority of the issue (defaults to 'Low' if not provided)
                - status (str): The status of the issue (defaults to 'Open' if not provided)
                - assignee (Dict[str, str]): Assignee information (defaults to {"name": "Unassigned"} if not provided)
                - components (List[str]): List of component IDs associated with the issue (defaults to empty list if not provided)
                - due_date (Optional[str]): The due date of the issue (None if not provided)
                - comments (List[str]): List of comments on the issue (defaults to empty list if not provided)
                - attachments (List[Dict[str, Any]]): List of attachments (defaults to empty list if not provided)
                - created (str): The creation timestamp of the issue in ISO format
                - updated (str): The last updated timestamp of the issue in ISO format

    Raises:
        EmptyFieldError: If the fields dictionary is empty
        MissingRequiredFieldError: If required fields (project, summary) are missing
        ValidationError: If field values do not meet validation requirements or due date is not in the format: YYYY-MM-DD
        ProjectNotFoundError: If the project does not exist in the database
    """
    # Basic validation - ensure fields is provided and not empty
    if fields is None:
        raise MissingRequiredFieldError("fields")
    if isinstance(fields, dict) and len(fields) == 0:
        raise EmptyFieldError("fields")
    
    # Handle assignee format for backward compatibility
    if "assignee" in fields:
        if isinstance(fields["assignee"], str):
            # Convert string assignee to dict format
            fields["assignee"] = {"name": fields["assignee"]}
        elif isinstance(fields["assignee"], dict) and "name" not in fields["assignee"]:
            # If assignee dict is missing name field, add default
            fields["assignee"]["name"] = "Unassigned"
    
    # Use Pydantic model for validation and default handling
    try:
        validated_fields = JiraIssueCreationFields(**fields)
    except ValidationError as e:
        raise e
    
    # Validate that the project exists in the database
    if validated_fields.project not in DB.get("projects", {}):
        raise ProjectNotFoundError(f"Project '{validated_fields.project}' not found.")
    
    # Initialize DB if needed and generate new ID
    if "issues" not in DB or not DB["issues"]:
        DB["issues"] = {}
    new_id = _generate_id("ISSUE", DB["issues"])
    
    # Convert validated Pydantic model to dict for storage
    fields_dict = validated_fields.model_dump()
    
    # Set created timestamp if not provided
    if fields_dict.get("created") is None:
        fields_dict["created"] = datetime.now().isoformat()

    fields_dict["updated"] = datetime.now().isoformat()
    
    # Store in DB
    DB["issues"][new_id] = {"id": new_id, "fields": fields_dict}
    
    # Create response using Pydantic model
    try:
        response = JiraIssueResponse(id=new_id, fields=fields_dict)
    except ValidationError as e:
        del DB["issues"][new_id]
        raise e
    return response.model_dump()


@tool_spec(
    spec={
        'name': 'get_issue_by_id',
        'description': """ Retrieve a specific issue by its ID.
        
        This method returns detailed information about a specific issue
        identified by its unique ID, including any attachments associated with the issue. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'issue_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the issue to retrieve.'
                }
            },
            'required': [
                'issue_id'
            ]
        }
    }
)
def get_issue(issue_id: str) -> Dict[str, Any]:
    """
    Retrieve a specific issue by its ID.

    This method returns detailed information about a specific issue
    identified by its unique ID, including any attachments associated with the issue.

    Args:
        issue_id (str): The unique identifier of the issue to retrieve.

    Returns:
        Dict[str, Any]: A dictionary containing issue details:
            - id (str): The unique identifier for the issue.
            - fields (Dict[str, Any]): The fields of the issue, including:
                - project (str): The project key.
                - summary (str): Issue summary.
                - description (str): Issue description.
                - priority (str): The priority of the issue.
                - status (str): The status of the issue. Example: (Open, Resolved, Closed, Completed, In Progress)
                - assignee (Dict[str, str]): Assignee information in dictionary format. Example: {"name": "jdoe"}
                    - name (str): The assignee's username (e.g., 'jdoe')
                - issuetype (str): The type of issue
                - attachments (List[Dict[str, Any]]): List of attachment metadata, each containing:
                    - id (int): The unique attachment identifier
                    - filename (str): Original filename of the attachment
                    - fileSize (int): File size in bytes
                    - mimeType (str): MIME type of the file
                    - created (str): ISO 8601 timestamp when attachment was uploaded
                    - checksum (str): SHA256 checksum for file integrity verification
                    - parentId Optional(str): The ID of the issue this attachment belongs to
                - due_date (Optional[str]): The due date of the issue, if present.
                - comments (Optional[List[str]]]): A list of comments to add to the issue.


    Raises:
        TypeError: If issue_id is not a string.
        ValueError: If the issue does not exist (this error originates from the function's core logic).
        ValidationError: If the issue data or attachments(from list_issue_attachments) are invalid.
        NotFoundError: If the attachment with the specified ID does not exist (from list_issue_attachments).
    """
    # --- Input Validation ---
    if not isinstance(issue_id, str):
        raise TypeError(f"issue_id must be a string, but got {type(issue_id).__name__}.")
    if not issue_id:
        raise ValueError("issue_id cannot be empty.")
    # --- End of Input Validation ---

    if issue_id not in DB["issues"]:
        raise ValueError(f"Issue '{issue_id}' not found.")

    issue = DB["issues"][issue_id]
    
    # Get attachment metadata for this issue
    attachment_ids = issue.get("fields", {}).get("attachmentIds", [])
    try:
        attachments = list_issue_attachments(issue_id)
    except Exception as e:
        raise e
    
    # Add attachments to the issue fields
    issue_fields = issue["fields"].copy()
    issue_fields["attachments"] = attachments
    
    try:
        response_fields = JiraIssueFields(**issue_fields)
        response = JiraIssueResponse(id=issue_id, fields=response_fields)
        return response.model_dump()
    except ValidationError as e:
        # This can happen if DB data is inconsistent with the response model
        raise ValueError(f"Issue data for '{issue_id}' is invalid: {e}")


@tool_spec(
    spec={
        'name': 'update_issue_by_id',
        'description': """ Update an existing issue.
        
        This method allows updating the fields of an existing issue.
        Only the provided fields will be updated. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'issue_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the issue to update.'
                },
                'fields': {
                    'type': 'object',
                    'description': """ The fields to update. Can include any valid
                    issue field. Expected structure if provided: """,
                    'properties': {
                        'summary': {
                            'type': 'string',
                            'description': 'The summary of the issue'
                        },
                        'description': {
                            'type': 'string',
                            'description': 'The description of the issue'
                        },
                        'priority': {
                            'type': 'string',
                            'description': 'The priority of the issue'
                        },
                        'status': {
                            'type': 'string',
                            'description': 'The status of the issue. Example: (Open, Resolved, Closed, Completed, In Progress)'
                        },
                        'assignee': {
                            'type': 'object',
                            'description': 'Assignee information in dictionary format. Example: {"name": "jdoe"}',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': "The assignee's username (e.g., 'jdoe')"
                                }
                            },
                            'required': [
                                'name'
                            ]
                        },
                        'issuetype': {
                            'type': 'string',
                            'description': 'The type of issue'
                        },
                        'project': {
                            'type': 'string',
                            'description': 'The project key'
                        },
                        'due_date': {
                            'type': 'string',
                            'description': 'The due date of the issue. Must be in the format: YYYY-MM-DD if provided.'
                        },
                        'comments': {
                            'type': 'array',
                            'description': 'A list of comments to add to the issue.',
                            'items': {
                                'type': 'string'
                            }
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'issue_id'
            ]
        }
    }
)
def update_issue(issue_id: str, fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Update an existing issue.

    This method allows updating the fields of an existing issue.
    Only the provided fields will be updated.

    Args:
        issue_id (str): The unique identifier of the issue to update.
        fields (Optional[Dict[str, Any]]): The fields to update. Can include any valid
            issue field. Expected structure if provided:
            - summary (Optional[str]): The summary of the issue
            - description (Optional[str]): The description of the issue
            - priority (Optional[str]): The priority of the issue
            - status (Optional[str]): The status of the issue. Example: (Open, Resolved, Closed, Completed, In Progress)
            - assignee (Optional[Dict[str, str]]): Assignee information in dictionary format. Example: {"name": "jdoe"}
                - name (str): The assignee's username (e.g., 'jdoe')
            - issuetype (Optional[str]): The type of issue
            - project (Optional[str]): The project key
            - due_date (Optional[str]): The due date of the issue. Must be in the format: YYYY-MM-DD if provided.
            - comments (Optional[List[str]]): A list of comments to add to the issue.
            
    Returns:
        Dict[str, Any]: A dictionary containing:
            - updated (bool): True if the issue was successfully updated
            - issue (Dict[str, Any]): The updated issue object
                - id (str): The unique identifier for the issue
                - fields (Dict[str, Any]): The fields of the issue, including:
                    - project (str): The project key
                    - summary (str): Issue summary
                    - description (str): Issue description
                    - priority (str): The priority of the issue
                    - status (str): The status of the issue. Example: (Open, Resolved, Closed, Completed, In Progress)
                    - assignee (Dict[str, str]): Assignee information
                        - name (str): The assignee's username (e.g., 'jdoe')
                    - issuetype (str): The type of issue
                    - due_date (Optional[str]): The due date of the issue
                    - comments (Optional[List[str]]]): A list of comments to add to the issue.
                    - created (Optional[str]): The creation timestamp of the issue in ISO format
                    - updated (Optional[str]): The last updated timestamp of the issue in ISO format

    Raises:
        TypeError: If 'issue_id' is not a string or 'fields' is not a dictionary.
        ValueError: If the issue with 'issue_id' is not found.
        ValidationError: If 'fields' is provided and does not conform to the
                        IssueFieldsUpdateModel structure (e.g., invalid field types
                        or incorrect assignee structure or invalid due date format).
    """
    if not isinstance(issue_id, str):
        raise TypeError("Argument 'issue_id' must be a string.")
    if not issue_id:
        raise ValueError("issue_id cannot be empty.")

    if issue_id not in DB["issues"]:
        raise ValueError(f"Issue '{issue_id}' not found.")

    if fields is not None:
        if not isinstance(fields, Dict):
            raise TypeError("Argument 'fields' must be a dictionary or None.")
        try:
            # Validate the structure of 'fields' using the Pydantic model
            fields["updated"] = datetime.now().isoformat()
            validated_fields_model = IssueFieldsUpdateModel(**fields)
            # Convert Pydantic model to dict, excluding fields that were not provided (None)
            validated_fields_data = validated_fields_model.model_dump(exclude_none=True)
            
            if "comments" in validated_fields_data:
                new_comments = validated_fields_data.pop("comments")
                existing_comments = DB["issues"][issue_id]["fields"].get("comments", [])
                # Ensure existing_comments is a list (defensive programming)
                if not isinstance(existing_comments, list):
                    existing_comments = []
                DB["issues"][issue_id]["fields"]["comments"] = existing_comments + new_comments
            
            DB["issues"][issue_id]["fields"].update(validated_fields_data)
        except ValidationError as e:
            raise e

    return {"updated": True, "issue": DB["issues"][issue_id]}


@tool_spec(
    spec={
        'name': 'delete_issue_by_id',
        'description': """ Delete an existing issue.
        
        This method permanently removes an issue from the system.
        Optionally, its subtasks can be deleted as well. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'issue_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the issue to delete.'
                },
                'delete_subtasks': {
                    'type': 'boolean',
                    'description': 'Whether to delete subtasks. Defaults to False if not provided.'
                }
            },
            'required': [
                'issue_id'
            ]
        }
    }
)
def delete_issue(issue_id: str, delete_subtasks: Optional[bool] = False) -> Dict[str, Any]:
    """
    Delete an existing issue.

    This method permanently removes an issue from the system.
    Optionally, its subtasks can be deleted as well.

    Args:
        issue_id (str): The unique identifier of the issue to delete.
        delete_subtasks (Optional[bool]): Whether to delete subtasks. Defaults to False if not provided.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - deleted (str): The ID of the deleted issue.
            - deleteSubtasks (str): The value of the delete_subtasks parameter (True or False).

    Raises:
        TypeError: If issue_id is not a string or if delete_subtasks is not a boolean.
        ValueError: If the issue does not exist or if subtasks exist and delete_subtasks is False.
    """
    if not isinstance(issue_id, str):
        raise TypeError(f"issue_id must be a string, got {type(issue_id).__name__}")
    if not issue_id:
        raise ValueError("issue_id cannot be empty.")
    
    # Handle None case and default to False
    if delete_subtasks is None:
        delete_subtasks = False
    if not isinstance(delete_subtasks, bool):
        raise TypeError(f"delete_subtasks must be a boolean, got {type(delete_subtasks).__name__}")

    if issue_id not in DB["issues"]:
        raise ValueError(f"Issue with id '{issue_id}' does not exist.")

    issue_data = DB["issues"][issue_id]
    if "sub-tasks" in issue_data.get("fields", {}):
        if not delete_subtasks:
            raise ValueError(
                "Subtasks exist, cannot delete issue. Set delete_subtasks=True to delete them."
            )
        sub_tasks = issue_data["fields"]["sub-tasks"]
        for subtask in sub_tasks:
            if isinstance(subtask, dict) and "id" in subtask:
                DB["issues"].pop(subtask["id"], None)

    DB["issues"].pop(issue_id)
    return {"deleted": issue_id, "deleteSubtasks": delete_subtasks}


@tool_spec(
    spec={
        'name': 'bulk_delete_issues',
        'description': """ Delete multiple issues in bulk.
        
        This method validates all issue IDs first and deletes them in a single operation.
        If any issue IDs are invalid or do not exist, all invalid IDs will be reported in the error message. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'issue_ids': {
                    'type': 'array',
                    'description': 'A list of issue IDs to delete',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'issue_ids'
            ]
        }
    }
)
def bulk_delete_issues(issue_ids: List[str]) -> Dict[str, List[str]]:
    """
    Delete multiple issues in bulk.

    This method validates all issue IDs first and deletes them in a single operation.
    If any issue IDs are invalid or do not exist, all invalid IDs will be reported in the error message.

    Args:
        issue_ids (List[str]): A list of issue IDs to delete

    Returns:
        Dict[str, List[str]]: A dictionary containing:
            - deleted (List[str]): List of successfully deleted issue messages

    Raises:
        MissingRequiredFieldError: If issue_ids is not provided.
        TypeError: If issue_ids is not a list or if any issue_id is not a string (all invalid IDs will be reported).
        ValueError: If any issue_id does not exist (all non-existent IDs will be reported).

    """
    results = {"deleted": []}

    if not issue_ids:
        raise MissingRequiredFieldError(field_name="issue_ids")

    if not isinstance(issue_ids, list):
        raise TypeError(f"issue_ids must be a list")

    # Collect all invalid IDs first
    non_string_ids = []
    non_existent_ids = []
    
    for issue_id in issue_ids:
        if not isinstance(issue_id, str):
            non_string_ids.append(repr(issue_id))
        elif issue_id not in DB["issues"]:
            non_existent_ids.append(issue_id)
    
    # Raise errors with all invalid IDs if any found
    if non_string_ids:
        raise TypeError(f"issue_ids must be a list of strings. Invalid IDs: {', '.join(non_string_ids)}")
    
    if non_existent_ids:
        raise ValueError(f"The following issue(s) do not exist: {', '.join(non_existent_ids)}")

    # Delete all valid issues
    for issue_id in issue_ids:
        DB["issues"].pop(issue_id)
        results["deleted"].append(f"Issue '{issue_id}' has been deleted.")

    # Return the results containing deleted issues and any errors encountered
    return results


@tool_spec(
    spec={
        'name': 'assign_issue_to_user',
        'description': """ Assign an issue to a user.
        
        This method assigns an issue to a specific user. The assignee can be
        a user or can be set to null to unassign the issue (handled by how 'assignee' dict is populated). """,
        'parameters': {
            'type': 'object',
            'properties': {
                'issue_id': {
                    'type': 'string',
                    'description': 'The unique identifier of the issue to assign.'
                },
                'assignee': {
                    'type': 'object',
                    'description': 'The assignee information. Must contain:',
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': "The assignee's username (e.g., 'jdoe')."
                        }
                    },
                    'required': [
                        'name'
                    ]
                }
            },
            'required': [
                'issue_id',
                'assignee'
            ]
        }
    }
)
def assign_issue(issue_id: str, assignee: Dict) -> Dict[str, Any]:
    """
    Assign an issue to a user.

    This method assigns an issue to a specific user. The assignee can be
    a user or can be set to null to unassign the issue (handled by how 'assignee' dict is populated).

    Args:
        issue_id (str): The unique identifier of the issue to assign.
        assignee (Dict): The assignee information. Must contain:
            - name (str): The assignee's username (e.g., 'jdoe').

    Returns:
        Dict[str, Any]: A dictionary containing:
            - assigned (bool): True if the issue was successfully assigned (if issue exists).
            - issue (Dict[str, Any]): The updated issue object if successful.
                - id (str): The unique identifier for the issue.
                - fields (Dict[str, Any]): The fields of the issue, including:
                    - project (str): The project key
                    - summary (str): Issue summary
                    - description (str): Issue description
                    - priority (str): The priority of the issue
                    - status (str): The status of the issue. Example: (Open, Resolved, Closed, Completed, In Progress)
                    - assignee (Dict[str, str]): Assignee information
                        - name (str): The assignee's username (e.g., 'jdoe')
                    - issuetype (str): The type of issue
    Raises:
        TypeError: If 'issue_id' is not a string or 'assignee' is not a dictionary.
        ValueError: If the issue with 'issue_id' is not found or issue_id is empty.
        pydantic.ValidationError: If 'assignee' dictionary does not conform to the required structure (e.g., missing 'name', or 'name' is not a string).
        UserNotFoundError: If the assignee username does not exist in the system's user database.
    """
    if not isinstance(issue_id, str):
        raise TypeError(f"issue_id must be a string, got {type(issue_id).__name__}.")
    if not issue_id:
        raise ValueError("issue_id cannot be empty.")
    if not isinstance(assignee, dict):
        raise TypeError(f"assignee must be a dictionary, got {type(assignee).__name__}.")

    if issue_id not in DB["issues"]:
        raise ValueError(f"Issue '{issue_id}' not found.")

    try:
        validated_assignee = JiraAssignee(**assignee)
    except ValidationError as e:
        raise e

    # Validate that the assignee user exists in the database
    # "Unassigned" is allowed as it represents an unassigned issue
    if validated_assignee.name != "Unassigned":
        user_exists = any(
            user_data.get("name") == validated_assignee.name 
            for user_data in DB.get("users", {}).values()
        )
        
        if not user_exists:
            raise UserNotFoundError(f"User '{validated_assignee.name}' not found in the system.")

    DB["issues"][issue_id]["fields"]["assignee"] = validated_assignee.model_dump()
    DB["issues"][issue_id]["fields"]["updated"] = datetime.now().isoformat()
    return {"assigned": True, "issue": DB["issues"][issue_id]}


@tool_spec(
    spec={
        'name': 'perform_bulk_issue_operations',
        'description': """ Performs bulk operations on multiple Jira issues.
        
        This function allows updating multiple issues in a single operation.
        Each update can modify fields, assignee, status, priority, summary, or description.
        Additionally, issues can be deleted with optional subtask deletion. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'issueUpdates': {
                    'type': 'array',
                    'description': """ A list of issue updates to perform.
                    Each update should contain: """,
                    'items': {
                        'type': 'object',
                        'properties': {
                            'issueId': {
                                'type': 'string',
                                'description': 'The ID of the issue to update'
                            },
                            'fields': {
                                'type': 'object',
                                'description': 'Fields to update. Can contain:',
                                'properties': {
                                    'summary': {
                                        'type': 'string',
                                        'description': 'The summary of the issue'
                                    },
                                    'description': {
                                        'type': 'string',
                                        'description': 'The description of the issue'
                                    },
                                    'priority': {
                                        'type': 'string',
                                        'description': 'The priority of the issue'
                                    },
                                    'status': {
                                        'type': 'string',
                                        'description': 'The status of the issue'
                                    },
                                    'assignee': {
                                        'type': 'object',
                                        'description': 'Assignee information with:',
                                        'properties': {
                                            'name': {
                                                'type': 'string',
                                                'description': "The assignee's username (e.g., 'jdoe')"
                                            }
                                        },
                                        'required': [
                                            'name'
                                        ]
                                    },
                                    'issuetype': {
                                        'type': 'string',
                                        'description': 'The type of issue'
                                    },
                                    'project': {
                                        'type': 'string',
                                        'description': 'The project key'
                                    },
                                    'due_date': {
                                        'type': 'string',
                                        'description': 'The due date of the issue'
                                    },
                                    'comments': {
                                        'type': 'array',
                                        'description': 'A list of comments to add to the issue',
                                        'items': {
                                            'type': 'string'
                                        }
                                    }
                                },
                                'required': []
                            },
                            'assignee': {
                                'type': 'object',
                                'description': 'Assignee information (takes precedence over fields.assignee):',
                                'properties': {
                                    'name': {
                                        'type': 'string',
                                        'description': "The assignee's username (e.g., 'jdoe')"
                                    }
                                },
                                'required': [
                                    'name'
                                ]
                            },
                            'status': {
                                'type': 'string',
                                'description': 'New status (takes precedence over fields.status)'
                            },
                            'priority': {
                                'type': 'string',
                                'description': 'New priority (takes precedence over fields.priority)'
                            },
                            'summary': {
                                'type': 'string',
                                'description': 'New summary (takes precedence over fields.summary)'
                            },
                            'description': {
                                'type': 'string',
                                'description': 'New description (takes precedence over fields.description)'
                            },
                            'delete': {
                                'type': 'boolean',
                                'description': 'Whether to delete this issue (default: False)'
                            },
                            'deleteSubtasks': {
                                'type': 'boolean',
                                'description': 'Whether to delete subtasks when deleting (default: False)'
                            }
                        },
                        'required': [
                            'issueId'
                        ]
                    }
                }
            },
            'required': [
                'issueUpdates'
            ]
        }
    }
)
def bulk_issue_operation(issueUpdates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Performs bulk operations on multiple Jira issues.
    
    This function allows updating multiple issues in a single operation.
    Each update can modify fields, assignee, status, priority, summary, or description.
    Additionally, issues can be deleted with optional subtask deletion.
    
    Args:
        issueUpdates (List[Dict[str, Any]]): A list of issue updates to perform.
            Each update should contain:
            - issueId (str): The ID of the issue to update
            - fields (Optional[Dict[str, Any]]): Fields to update. Can contain:
                - summary (Optional[str]): The summary of the issue
                - description (Optional[str]): The description of the issue
                - priority (Optional[str]): The priority of the issue
                - status (Optional[str]): The status of the issue
                - assignee (Optional[Dict[str, str]]): Assignee information with:
                    - name (str): The assignee's username (e.g., 'jdoe')
                - issuetype (Optional[str]): The type of issue
                - project (Optional[str]): The project key
                - due_date (Optional[str]): The due date of the issue
                - comments (Optional[List[str]]): A list of comments to add to the issue
            - assignee (Optional[Dict[str, str]]): Assignee information (takes precedence over fields.assignee):
                - name (str): The assignee's username (e.g., 'jdoe')
            - status (Optional[str]): New status (takes precedence over fields.status)
            - priority (Optional[str]): New priority (takes precedence over fields.priority)
            - summary (Optional[str]): New summary (takes precedence over fields.summary)
            - description (Optional[str]): New description (takes precedence over fields.description)
            - delete (Optional[bool]): Whether to delete this issue (default: False)
            - deleteSubtasks (Optional[bool]): Whether to delete subtasks when deleting (default: False)
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - bulkProcessed (bool): Whether all operations were processed successfully
            - updatesCount (int): The number of operations processed
            - successfulUpdates (List[str]): List of successfully updated issue IDs
            - deletedIssues (List[str]): List of successfully deleted issue IDs
    
    Raises:
        TypeError: If 'issueUpdates' is not a list.
        ValueError: If 'issueUpdates' is empty or if any issue IDs do not exist (all non-existent IDs will be reported).
        pydantic.ValidationError: If validation fails when the issue update is not in the required format.
    """
    # --- Input Validation ---
    if not isinstance(issueUpdates, list):
        raise TypeError("issueUpdates must be a list")
    
    if not issueUpdates:
        raise ValueError("issueUpdates cannot be empty")
    
 
    validated_request = BulkIssueOperationRequestModel(issueUpdates=issueUpdates)
    
    # First, validate that all issue IDs exist in DB
    non_existent_ids = []
    for update in validated_request.issueUpdates:
        if update.issueId not in DB.get("issues", {}):
            non_existent_ids.append(update.issueId)
    
    # Raise error with all non-existent IDs if any found
    if non_existent_ids:
        raise ValueError(f"The following issue(s) do not exist: {', '.join(non_existent_ids)}")
    
    successful_updates = []
    deleted_issues = []
    
    for update in validated_request.issueUpdates:
        
        # Handle delete operation
        if update.delete:
            issue_data = DB["issues"][update.issueId]
            
            # Check for subtasks if deleteSubtasks is False
            if not update.deleteSubtasks and "sub-tasks" in issue_data.get("fields", {}):
                sub_tasks = issue_data["fields"]["sub-tasks"]
                if sub_tasks:
                    raise ValueError(
                        f"Subtasks exist for issue '{update.issueId}', cannot delete. Set deleteSubtasks=True to delete them."
                    )
            
            # Delete subtasks if requested
            if update.deleteSubtasks and "sub-tasks" in issue_data.get("fields", {}):
                sub_tasks = issue_data["fields"]["sub-tasks"]
                for subtask in sub_tasks:
                    if isinstance(subtask, dict) and "id" in subtask:
                        DB["issues"].pop(subtask["id"], None)
            
            # Delete the issue
            DB["issues"].pop(update.issueId, None)
            deleted_issues.append(update.issueId)
            
        else:
            # Handle update operation
            issue_data = DB["issues"][update.issueId]
            
            # Update fields if provided
            if update.fields:
                if update.fields.summary is not None:
                    issue_data["fields"]["summary"] = update.fields.summary
                if update.fields.description is not None:
                    issue_data["fields"]["description"] = update.fields.description
                if update.fields.priority is not None:
                    issue_data["fields"]["priority"] = update.fields.priority
                if update.fields.status is not None:
                    issue_data["fields"]["status"] = update.fields.status
                if update.fields.assignee is not None:
                    issue_data["fields"]["assignee"] = update.fields.assignee.model_dump()
                if update.fields.issuetype is not None:
                    issue_data["fields"]["issuetype"] = update.fields.issuetype
                if update.fields.project is not None:
                    issue_data["fields"]["project"] = update.fields.project
            
            # Update individual fields if provided (these take precedence over fields object)
            if update.assignee is not None:
                issue_data["fields"]["assignee"] = update.assignee.model_dump()
            if update.status is not None:
                issue_data["fields"]["status"] = update.status
            if update.priority is not None:
                issue_data["fields"]["priority"] = update.priority
            if update.summary is not None:
                issue_data["fields"]["summary"] = update.summary
            if update.description is not None:
                issue_data["fields"]["description"] = update.description
            issue_data["fields"]["updated"] = datetime.now().isoformat()
            DB["issues"][update.issueId] = issue_data
            
            successful_updates.append(update.issueId)
    
    # Create response
    response_data = {
        "bulkProcessed": len(successful_updates) + len(deleted_issues) == len(issueUpdates),  # True only if all operations succeeded
        "updatesCount": len(issueUpdates),
        "successfulUpdates": successful_updates,
        "deletedIssues": deleted_issues
    }
    return response_data

@tool_spec(
    spec={
        'name': 'search_issues_for_picker',
        'description': """ Search for issues based on a query string and/or JQL.
        
        This method searches for issues based on a text query string and/or JQL (Jira Query Language).
        The search is case-insensitive for text queries. JQL filtering is applied first, then text filtering. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The text query string to search for in issue summaries and IDs.
                    If None, no text filtering will be applied.
                    An empty string "" will generally match all issues. """
                },
                'currentJQL': {
                    'type': 'string',
                    'description': """ JQL expression to filter issues before applying text search.
                    If provided, only issues matching the JQL will be considered.
                    Supports all standard JQL operators and functions. """
                },
                'currentIssueKey': {
                    'type': 'string',
                    'description': """ The key of an issue to exclude from search results.
                    For example, the issue the user is viewing when they perform this query.
                    Cannot be empty or whitespace-only. """
                },
                'showSubTasks': {
                    'type': 'boolean',
                    'description': """ Whether to include subtasks in results. Defaults to True.
                    If False, issues with issuetype "Subtask" will be excluded. """
                }
            },
            'required': []
        }
    }
)
def issue_picker(
    query: Optional[str] = None, 
    currentJQL: Optional[str] = None,
    currentIssueKey: Optional[str] = None,
    showSubTasks: Optional[bool] = True
) -> Dict[str, Any]:
    """
    Search for issues based on a query string and/or JQL.

    This method searches for issues based on a text query string and/or JQL (Jira Query Language).
    The search is case-insensitive for text queries. JQL filtering is applied first, then text filtering.

    Args:
        query (Optional[str]): The text query string to search for in issue summaries and IDs.
                               If None, no text filtering will be applied.
                               An empty string "" will generally match all issues.
        currentJQL (Optional[str]): JQL expression to filter issues before applying text search.
                                   If provided, only issues matching the JQL will be considered.
                                   Supports all standard JQL operators and functions.
        currentIssueKey (Optional[str]): The key of an issue to exclude from search results.
                                        For example, the issue the user is viewing when they perform this query.
                                        Cannot be empty or whitespace-only.
        showSubTasks (Optional[bool]): Whether to include subtasks in results. Defaults to True.
                                      If False, issues with issuetype "Subtask" will be excluded.
                                      

    Returns:
        Dict[str, Any]: A dictionary containing:
            - issues (List[str]): List of issue IDs that match the query and/or JQL.

    Raises:
        TypeError: If 'query', 'currentJQL', or 'currentIssueKey' are provided and are not strings,
                   or if 'showSubTasks' is provided and is not a boolean.
        ValueError: If 'currentJQL' contains invalid JQL syntax, or if 'currentIssueKey' is empty.

    """
    # --- Input Validation ---
    if query is not None and not isinstance(query, str):
        raise TypeError(f"Query must be a string or None, but got {type(query).__name__}.")
    
    if currentJQL is not None and not isinstance(currentJQL, str):
        raise TypeError(f"currentJQL must be a string or None, but got {type(currentJQL).__name__}.")
    
    if currentIssueKey is not None:
        if not isinstance(currentIssueKey, str):
            raise TypeError(f"currentIssueKey must be a string or None, but got {type(currentIssueKey).__name__}.")
        if not currentIssueKey.strip():
            raise ValueError("currentIssueKey cannot be empty.")
    
    if showSubTasks is not None and not isinstance(showSubTasks, bool):
        raise TypeError(f"showSubTasks must be a boolean or None, but got {type(showSubTasks).__name__}.")

    # --- Core Logic ---
    # Step 1: Apply JQL filtering if provided
    if currentJQL:
        from .SearchApi import search_issues
        try:
            jql_results = search_issues(jql=currentJQL, max_results=1000)
            filtered_issues = {issue["id"]: issue for issue in jql_results["issues"]}
        except Exception as e:
            raise ValueError(f"Invalid JQL syntax: {str(e)}")
    else:
        # No JQL filtering, use all issues - but handle edge cases
        db_issues = DB.get("issues", {})
        if not isinstance(db_issues, dict):
            # Handle case where DB["issues"] is not a dictionary
            filtered_issues = {}
        else:
            filtered_issues = db_issues

    # Step 2: Apply text query filtering if provided
    matched: List[str] = []
    
    if query is not None:
        processed_query = query.lower()
        
        for iss_id, data in filtered_issues.items():
            if isinstance(data, dict) and "fields" in data and isinstance(data["fields"], dict):
                summary_value = data["fields"].get("summary", "")
                # Handle None summary values
                summary = (summary_value or "").lower()
            else:
                summary = ""

            # For empty string query, match all (after JQL filtering)
            if processed_query == "" or processed_query in iss_id.lower() or processed_query in summary:
                matched.append(iss_id)
    else:
        # No text query provided
        if currentJQL:
            # If JQL was provided, return all JQL-filtered results
            matched = list(filtered_issues.keys())
        else:
            # No JQL and no text query, return empty list (per test expectations)
            matched = []
    
    # Step 3: Apply currentIssueKey exclusion if provided
    if currentIssueKey is not None:
        matched = [issue_id for issue_id in matched if issue_id != currentIssueKey]
    
    # Step 4: Apply showSubTasks filtering if needed
    if showSubTasks is False:
        # Filter out subtasks (issues with issuetype "Subtask")
        filtered_matched = []
        for issue_id in matched:
            issue_data = filtered_issues.get(issue_id)
            if isinstance(issue_data, dict) and "fields" in issue_data:
                fields = issue_data["fields"]
                if isinstance(fields, dict):
                    issuetype = fields.get("issuetype", "")
                    if issuetype != "Subtask":
                        filtered_matched.append(issue_id)
                else:
                    # If fields is not a dict, include it (assume not a subtask)
                    filtered_matched.append(issue_id)
            else:
                # If issue_data is malformed, include it (assume not a subtask)
                filtered_matched.append(issue_id)
        matched = filtered_matched
    
    return {"issues": matched}


@tool_spec(
    spec={
        'name': 'get_issue_create_metadata',
        'description': """ Get the create metadata for projects and issue types.
        
        This method returns metadata about projects and their available issue types
        that can be used for creating new issues. The response can be filtered by
        project keys and issue type names. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'projectKeys': {
                    'type': 'string',
                    'description': """ Project keys to filter the results. 
                    If None, all projects are returned. This parameter accepts a 
                    comma-separated list of project keys. Specifying a project 
                    that does not exist is not an error, but it will not be in the results. """
                },
                'issueTypeNames': {
                    'type': 'string',
                    'description': """ Issue type names to filter the results.
                    If None, all issue types are returned. This parameter accepts a 
                    comma-separated list of issue type names. Specifying an issue type 
                    that does not exist is not an error. """
                }
            },
            'required': []
        }
    }
)
def get_create_meta(
    projectKeys: Optional[str] = None, issueTypeNames: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get the create metadata for projects and issue types.

    This method returns metadata about projects and their available issue types
    that can be used for creating new issues. The response can be filtered by
    project keys and issue type names.

    Args:
        projectKeys (Optional[str]): Project keys to filter the results. 
            If None, all projects are returned. This parameter accepts a 
            comma-separated list of project keys. Specifying a project 
            that does not exist is not an error, but it will not be in the results.
        issueTypeNames (Optional[str]): Issue type names to filter the results.
            If None, all issue types are returned. This parameter accepts a 
            comma-separated list of issue type names. Specifying an issue type 
            that does not exist is not an error.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - projects (List[Dict[str, Any]]): List of projects with their metadata
                - key (str): The project key
                - name (str): The project name
                - lead (str): The project lead username
                - issueTypes (List[Dict[str, Any]]): List of available issue types for this project
                    - id (str): The issue type ID
                    - name (str): The issue type name (e.g., "Bug", "Task")
                    - fields (Dict[str, Dict[str, Any]]): Field metadata for creating this issue type.
                      Each field contains:
                        - required (bool): Whether the field is required
                        - name (str): Display name of the field
                        - schema (Dict[str, str]): Type information (e.g., {"type": "string"})
                        - hasDefaultValue (bool): Whether a default value exists

    Raises:
        TypeError: If projectKeys or issueTypeNames are provided and are not strings.
    """
    # Input validation
    if projectKeys is not None and not isinstance(projectKeys, str):
        raise TypeError(f"projectKeys must be a string or None, got {type(projectKeys).__name__}")
    
    if issueTypeNames is not None and not isinstance(issueTypeNames, str):
        raise TypeError(f"issueTypeNames must be a string or None, got {type(issueTypeNames).__name__}")

    # Define field metadata based on JiraIssueCreationFields model
    field_metadata = {
        "project": {
            "required": True,
            "name": "Project",
            "schema": {"type": "string"},
            "hasDefaultValue": False
        },
        "summary": {
            "required": True,
            "name": "Summary",
            "schema": {"type": "string"},
            "hasDefaultValue": False
        },
        "issuetype": {
            "required": False,
            "name": "Issue Type",
            "schema": {"type": "string"},
            "hasDefaultValue": True
        },
        "description": {
            "required": False,
            "name": "Description",
            "schema": {"type": "string"},
            "hasDefaultValue": True
        },
        "priority": {
            "required": False,
            "name": "Priority",
            "schema": {"type": "string"},
            "hasDefaultValue": True
        },
        "assignee": {
            "required": False,
            "name": "Assignee",
            "schema": {"type": "object"},
            "hasDefaultValue": True
        },
        "status": {
            "required": False,
            "name": "Status",
            "schema": {"type": "string"},
            "hasDefaultValue": True
        },
        "created": {
            "required": False,
            "name": "Created",
            "schema": {"type": "string"},
            "hasDefaultValue": False
        },
        "updated": {
            "required": False,
            "name": "Updated",
            "schema": {"type": "string"},
            "hasDefaultValue": False
        },
        "due_date": {
            "required": False,
            "name": "Due Date",
            "schema": {"type": "string"},
            "hasDefaultValue": False
        },
        "comments": {
            "required": False,
            "name": "Comments",
            "schema": {"type": "array", "items": "string"},
            "hasDefaultValue": True
        },
        "components": {
            "required": False,
            "name": "Components",
            "schema": {"type": "array", "items": "string"},
            "hasDefaultValue": True
        }
    }

    # Parse project keys - handle comma-separated list
    requested_project_keys = set()
    if projectKeys:
        # Split by comma and strip whitespace
        keys = [key.strip() for key in projectKeys.split(',')]
        # Filter out empty strings
        requested_project_keys = {key for key in keys if key}
    
    # Parse issue type names - handle comma-separated list
    requested_issue_types = set()
    if issueTypeNames:
        # Split by comma and strip whitespace
        types = [type_name.strip() for type_name in issueTypeNames.split(',')]
        # Filter out empty strings
        requested_issue_types = {type_name for type_name in types if type_name}

    # Get available projects and issue types
    available_projects = DB["projects"]
    available_issue_types = DB.get("issue_types", {})

    # First, build a map of project -> issue types from existing issues
    project_issue_types = {}
    for issue_data in DB["issues"].values():
        if isinstance(issue_data, dict) and "fields" in issue_data:
            issue_fields = issue_data["fields"]
            if isinstance(issue_fields, dict):
                project = issue_fields.get("project")
                issue_type = issue_fields.get("issuetype")
                if project and issue_type:
                    if project not in project_issue_types:
                        project_issue_types[project] = set()
                    project_issue_types[project].add(issue_type)

    # Filter projects based on requested keys
    filtered_projects = []
    for project_key, project_data in available_projects.items():
        # If no project keys specified, include all projects
        # If project keys specified, only include requested ones
        if not requested_project_keys or project_key in requested_project_keys:
            # Get issue types for this project
            project_types = project_issue_types.get(project_key, set())
            
            # If no issue types found for project, use all available issue types
            if not project_types and available_issue_types:
                project_types = set(available_issue_types.keys())
            
            # Filter issue types if requested
            if requested_issue_types:
                project_types = project_types.intersection(requested_issue_types)
            
            # Convert to list of dictionaries with full metadata
            issue_types_list = []
            for type_name in sorted(project_types):
                issue_type_data = available_issue_types.get(type_name, {})
                issue_types_list.append({
                    "id": issue_type_data.get("id", type_name),
                    "name": type_name,
                    "fields": field_metadata
                })
            
            # Add project with its issue types
            filtered_projects.append({
                "key": project_data["key"],
                "name": project_data["name"],
                "lead": project_data["lead"],
                "issueTypes": issue_types_list
            })

    return {"projects": filtered_projects}
