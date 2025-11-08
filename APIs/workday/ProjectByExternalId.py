"""
This module provides functionality for managing projects using their external identifiers
in the Workday Strategic Sourcing system.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional, Union, List
import datetime

from .SimulationEngine import db
from .SimulationEngine.custom_errors import (
    ProjectByExternalIdValidationError,
    ProjectByExternalIdNotFoundError,
    ProjectByExternalIdDatabaseError,
    ProjectByExternalIdPatchError, DatabaseSchemaError, ProjectNotFoundError, InvalidExternalIdError
)

@tool_spec(
    spec={
        'name': 'get_project_by_external_id',
        'description': 'Retrieves the details of a specific project using its external identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': """ The unique external identifier of the project to retrieve.
                    Must be a non-empty string. """
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def get(external_id: str) -> Dict[str, Union[str, List[str]]]:
    """
    Retrieves the details of a specific project using its external identifier.

    Args:
        external_id (str): The unique external identifier of the project to retrieve.
                          Must be a non-empty string.

    Returns:
        Dict[str, Union[str, List[str]]]: A dictionary containing the project details. The project details will be returned 
              with the following keys:
                - id (str): Project identifier string
                - external_id (str): Project external identifier string
                - supplier_companies (List[str]): Array of supplier company identifiers
                - supplier_contacts (List[str]): Array of supplier contact identifiers
                - name (str): Project name
                - type_id (str): Project type identifier
                - status (str): Project status (e.g., "In Progress", "Planning", "Completed", "Ongoing", "Kickoff")

    Raises:
        ProjectByExternalIdValidationError: If external_id is None, empty, or not a string
        ProjectByExternalIdDatabaseError: If database structure is invalid or inaccessible
        ProjectByExternalIdNotFoundError: If project with the specified external_id is not found
    """
    # Input validation
    if external_id is None:
        raise ProjectByExternalIdValidationError("external_id cannot be None")
    
    if not isinstance(external_id, str):
        raise ProjectByExternalIdValidationError("external_id must be a string")
    
    if not external_id.strip():
        raise ProjectByExternalIdValidationError("external_id cannot be empty or whitespace only")
    
    # Database structure validation
    try:
        if not hasattr(db, 'DB') or not isinstance(db.DB, dict):
            raise ProjectByExternalIdDatabaseError("Database is not properly initialized")
        
        if 'projects' not in db.DB:
            raise ProjectByExternalIdDatabaseError("Projects collection not found in database")
        
        if 'projects' not in db.DB['projects']:
            raise ProjectByExternalIdDatabaseError("Projects subcollection not found in database")
        
        projects_collection = db.DB['projects']['projects']
        if not isinstance(projects_collection, dict):
            raise ProjectByExternalIdDatabaseError("Projects collection is not properly structured")
        
    except Exception as e:
        if isinstance(e, ProjectByExternalIdDatabaseError):
            raise
        raise ProjectByExternalIdDatabaseError(f"Database access error: {str(e)}")
    
    # Search for project with matching external_id
    for project in projects_collection.values():
        if not isinstance(project, dict):
            continue  # Skip invalid project entries
        
        project_external_id = project.get("external_id")
        if project_external_id == external_id:
            return project
    
    # Project not found
    raise ProjectByExternalIdNotFoundError(f"Project with external_id '{external_id}' not found")

@tool_spec(
    spec={
        'name': 'update_project_by_external_id',
        'description': 'Updates the details of an existing project using its external identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The unique external identifier of the project to update.'
                },
                'project_data': {
                    'type': 'object',
                    'description': """ A dictionary containing the updated project details.
                    Must include an 'external_id' field matching the provided ID. """,
                    'properties': {
                        'type_id': {
                            'type': 'string',
                            'description': 'Object type'
                        },
                        'id': {
                            'type': 'string',
                            'description': 'Project identifier string'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Project attributes object containing:',
                            'properties': {
                                'title': {
                                    'type': 'string',
                                    'description': 'Project title'
                                },
                                'description': {
                                    'type': 'string',
                                    'description': 'Project description'
                                },
                                'state': {
                                    'type': 'string',
                                    'description': 'Current project state. Allowed values: "draft", "requested", "planned", "active", "completed", "canceled", "on_hold".'
                                },
                                'state_label': {
                                    'type': 'string',
                                    'description': 'Customer-specific project state label.'
                                },
                                'external_id': {
                                    'type': 'string',
                                    'description': 'Customer provided unique project identifier'
                                },
                                'target_start_date': {
                                    'type': 'string',
                                    'description': 'The planned start date for the project, in ISO 8601 `YYYY-MM-DD` format.'
                                },
                                'target_end_date': {
                                    'type': 'string',
                                    'description': 'Target end date of the project, in ISO 8601 `YYYY-MM-DD` format.'
                                },
                                'actual_start_date': {
                                    'type': 'string',
                                    'description': 'The actual start date for the project, in ISO 8601 `YYYY-MM-DD` format.'
                                },
                                'actual_end_date': {
                                    'type': 'string',
                                    'description': 'The actual end date of the project, in ISO 8601 `YYYY-MM-DD` format.'
                                },
                                'actual_spend_amount': {
                                    'type': 'number',
                                    'description': 'Project actual spend amount'
                                },
                                'approved_spend_amount': {
                                    'type': 'number',
                                    'description': 'Project approved spend amount'
                                },
                                'estimated_savings_amount': {
                                    'type': 'number',
                                    'description': 'Project estimated savings amount'
                                },
                                'estimated_spend_amount': {
                                    'type': 'number',
                                    'description': 'Project estimated spend amount'
                                },
                                'canceled_note': {
                                    'type': 'string',
                                    'description': 'Project cancelation note'
                                },
                                'canceled_reason': {
                                    'type': 'string',
                                    'description': 'Project cancelation reason'
                                },
                                'on_hold_note': {
                                    'type': 'string',
                                    'description': 'Project on-hold note'
                                },
                                'on_hold_reason': {
                                    'type': 'string',
                                    'description': 'Project on-hold reason'
                                },
                                'needs_attention': {
                                    'type': 'boolean',
                                    'description': 'Project needs attention status'
                                },
                                'marked_as_needs_attention_at': {
                                    'type': 'string',
                                    'description': 'ISO 8601 date-time string (`YYYY-MM-DDTHH:MM:SSZ`) indicating when the project was flagged as needing attention.'
                                },
                                'needs_attention_note': {
                                    'type': 'string',
                                    'description': 'Project needs attention note'
                                },
                                'needs_attention_reason': {
                                    'type': 'string',
                                    'description': 'Project needs attention reason'
                                },
                                'approval_rounds': {
                                    'type': 'integer',
                                    'description': 'Times project has been sent for approval.'
                                },
                                'sent_for_approval_at': {
                                    'type': 'string',
                                    'description': 'Date and time when the project was sent for approval in ISO 8601 date-time string (`YYYY-MM-DDTHH:MM:SSZ`).'
                                }
                            },
                            'required': [
                                'title',
                                'description'
                            ]
                        },
                        'relationships': {
                            'type': 'object',
                            'description': 'Project relationships object containing:',
                            'properties': {
                                'owner': {
                                    'type': 'object',
                                    'description': 'Stakeholder who owns the project.',
                                    'properties': {
                                        'data': {
                                            'type': 'object',
                                            'description': 'Stakeholder data object containing:',
                                            'properties': {
                                                'id': {
                                                    'type': 'string',
                                                    'description': 'Stakeholder identifier.'
                                                },
                                                'type': {
                                                    'type': 'string',
                                                    'description': 'Always "stakeholders".'
                                                }
                                            },
                                            'required': [
                                                'id',
                                                'type'
                                            ]
                                        }
                                    },
                                    'required': [
                                        'data'
                                    ]
                                },
                                'requester': {
                                    'type': 'object',
                                    'description': 'Stakeholder who requested the project.',
                                    'properties': {
                                        'data': {
                                            'type': 'object',
                                            'description': 'Stakeholder data object containing:',
                                            'properties': {
                                                'id': {
                                                    'type': 'string',
                                                    'description': 'Stakeholder identifier.'
                                                },
                                                'type': {
                                                    'type': 'string',
                                                    'description': 'Always "stakeholders".'
                                                }
                                            },
                                            'required': [
                                                'id',
                                                'type'
                                            ]
                                        }
                                    },
                                    'required': [
                                        'data'
                                    ]
                                }
                            },
                            'required': []
                        }
                    },
                    'required': [
                        'type_id',
                        'id',
                        'attributes',
                        'relationships'
                    ]
                }
            },
            'required': [
                'external_id',
                'project_data'
            ]
        }
    }
)
def patch(external_id: str, project_data: Dict[str, Union[str, int, float, bool, datetime.date, datetime.datetime, None, List, Dict]]) -> Optional[Dict[str, Union[str, int, float, bool, datetime.date, datetime.datetime, None, List, Dict]]]:
    """
    Updates the details of an existing project using its external identifier.

    Args:
        external_id (str): The unique external identifier of the project to update.
        project_data (Dict[str, Union[str, int, float, bool, datetime.date, datetime.datetime, None, List, Dict]]): 
            A dictionary containing the updated project details.
            Must include an 'external_id' field matching the provided ID.
            - type_id (str): Object type
            - id (str): Project identifier string
            - attributes (Dict[str, Union[str, float, bool, datetime.date, datetime.datetime, None]]): 
                Project attributes object containing:
                - title (str): Project title
                - description (str): Project description
                - state (str, optional): Current project state. Allowed values: "draft", "requested", "planned", "active", "completed", "canceled", "on_hold".
                - state_label(str, optional): Customer-specific project state label.
                - external_id(str, optional): Customer provided unique project identifier
                - target_start_date (str, optional): The planned start date for the project, in ISO 8601 `YYYY-MM-DD` format.
                - target_end_date (str, optional): Target end date of the project, in ISO 8601 `YYYY-MM-DD` format.
                - actual_start_date (str, optional): The actual start date for the project, in ISO 8601 `YYYY-MM-DD` format.
                - actual_end_date (str, optional): The actual end date of the project, in ISO 8601 `YYYY-MM-DD` format.
                - actual_spend_amount (float, optional): Project actual spend amount
                - approved_spend_amount (float, optional): Project approved spend amount
                - estimated_savings_amount (float, optional): Project estimated savings amount
                - estimated_spend_amount (float, optional): Project estimated spend amount
                - canceled_note (Optional[str]): Project cancelation note
                - canceled_reason (Optional[str]): Project cancelation reason
                - on_hold_note (Optional[str]): Project on-hold note
                - on_hold_reason (Optional[str]): Project on-hold reason
                - needs_attention (Optional[bool]): Project needs attention status
                - marked_as_needs_attention_at (Optional[str]): ISO 8601 date-time string (`YYYY-MM-DDTHH:MM:SSZ`) indicating when the project was flagged as needing attention.
                - needs_attention_note (Optional[str]): Project needs attention note
                - needs_attention_reason (Optional[str]): Project needs attention reason
                - approval_rounds(int, optional): Times project has been sent for approval.
                - sent_for_approval_at(Optional[str]): Date and time when the project was sent for approval in ISO 8601 date-time string (`YYYY-MM-DDTHH:MM:SSZ`).
            - relationships (Dict[str, Union[List[Dict], Dict[str, Dict]]]): Project relationships object containing:
                - owner (Dict[str, Dict[str, str]], optional): Stakeholder who owns the project.
                    - data (Dict[str, str], required): Stakeholder data object containing:
                        - id (str): Stakeholder identifier.
                        - type (str): Always "stakeholders".
                - requester (Dict[str, Dict[str, str]], optional): Stakeholder who requested the project.
                    - data (Dict[str, str], required): Stakeholder data object containing:
                        - id (str): Stakeholder identifier.
                        - type (str): Always "stakeholders".


    Returns:
        Optional[Dict[str, Union[str, int, float, bool, datetime.date, datetime.datetime, None, List, Dict]]]: The updated project details if successful,
                       None if the project doesn't exist or the external IDs don't match.
                       The updated project details will be returned with any of the following keys:
                        - type_id (str): Object type
                        - id (str): Project identifier string.
                        - external_id (str): Project external identifier string
                        - supplier_companies (List[Dict]): Array of supplier company objects
                        - supplier_contacts (List[Dict]): Array of supplier contact objects
                        - status (str): Project status
                        - attributes (Dict[str, Union[str, float, bool, datetime.date, datetime.datetime, None]]): Project attributes object containing:
                            - name (str): Project name
                            - description (str): Project description
                            - state (str): Project state (draft, requested, planned, active, completed, canceled, on_hold)
                            - target_start_date (datetime.date): Project target start date
                            - target_end_date (datetime.date): Project target end date
                            - actual_spend_amount (float): Project actual spend amount
                            - approved_spend_amount (float): Project approved spend amount
                            - estimated_savings_amount (float): Project estimated savings amount
                            - estimated_spend_amount (float): Project estimated spend amount
                            - canceled_note (Optional[str]): Project cancelation note
                            - canceled_reason (Optional[str]): Project cancelation reason
                            - on_hold_note (Optional[str]): Project on-hold note
                            - on_hold_reason (Optional[str]): Project on-hold reason
                            - needs_attention (bool): Project needs attention status
                            - marked_as_needs_attention_at (Optional[datetime.datetime]): Project marked as needs attention timestamp
                            - needs_attention_note (Optional[str]): Project needs attention note
                            - needs_attention_reason (Optional[str]): Project needs attention reason
                        - relationships (Dict[str, Union[List[Dict], Dict[str, Dict]]]): Project relationships object containing:
                            - attachments (List[Dict]): Array of attachment objects
                            - creator (Dict[str, str]): Project creator stakeholder object
                            - requester (Dict[str, str]): Project requester stakeholder object
                            - owner (Dict[str, str]): Project owner stakeholder object
                            - project_type (Dict[str, str]): Project type object
                        - links (Dict[str, str]): Resource links object containing:
                            - self (str): Normalized link to the resource

    Raises:
        ProjectByExternalIdPatchError: If validation fails, external_id mismatch, project not found, or database error
    """
    # Input validation for external_id
    if external_id is None or not isinstance(external_id, str) or not external_id.strip():
        raise ProjectByExternalIdPatchError("external_id must be a non-empty string")
    
    # Input validation for project_data
    if project_data is None or not isinstance(project_data, dict) or not project_data:
        raise ProjectByExternalIdPatchError("project_data must be a non-empty dictionary")
    
    # Validate external_id mismatch
    project_external_id = project_data.get("external_id")
    if project_external_id != external_id:
        raise ProjectByExternalIdPatchError(
            f"external_id in path ('{external_id}') does not match external_id in project_data ('{project_external_id}')"
        )
    
    # Database structure validation
    try:
        if not hasattr(db, 'DB') or not isinstance(db.DB, dict):
            raise ProjectByExternalIdPatchError("Database is not properly initialized")
        
        if 'projects' not in db.DB or 'projects' not in db.DB['projects']:
            raise ProjectByExternalIdPatchError("Projects collection not found in database")
        
        projects_collection = db.DB['projects']['projects']
        if not isinstance(projects_collection, dict):
            raise ProjectByExternalIdPatchError("Projects collection is not properly structured")
        
    except Exception as e:
        if isinstance(e, ProjectByExternalIdPatchError):
            raise
        raise ProjectByExternalIdPatchError(f"Database access error: {str(e)}")
    
    # Search for project with matching external_id
    for project_id, project in projects_collection.items():
        if not isinstance(project, dict):
            continue  # Skip invalid project entries
        
        project_external_id = project.get("external_id")
        if project_external_id == external_id:
            # Update the project with new data
            projects_collection[project_id].update(project_data)
            return projects_collection[project_id]
    
    # Project not found
    raise ProjectByExternalIdPatchError(f"Project with external_id '{external_id}' not found")

@tool_spec(
    spec={
        'name': 'delete_project_by_external_id',
        'description': """ This function validates the external_id parameter, searches for the project
        
        in the database, and removes it if found. The function provides comprehensive
        error handling for various edge cases. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The unique external identifier of the project to delete. Must be a non-empty string.'
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def delete(external_id: str) -> bool:
    """
    This function validates the external_id parameter, searches for the project
    in the database, and removes it if found. The function provides comprehensive
    error handling for various edge cases.

    Args:
        external_id (str): The unique external identifier of the project to delete. Must be a non-empty string.

    Returns:
        bool: True if the project was successfully deleted.

    Raises:
        InvalidExternalIdError: If external_id is None, empty, or not a string.
        DatabaseSchemaError: If the database structure is unexpected or corrupted.
        ProjectNotFoundError: If no project exists with the specified external_id.
    """
    # Input validation
    if external_id is None:
        raise InvalidExternalIdError("External ID cannot be empty or None.")

    if not isinstance(external_id, str):
        raise InvalidExternalIdError("External ID must be a string.")

    if not external_id.strip():
        raise InvalidExternalIdError("External ID cannot be empty or None.")

    # Database structure validation
    try:
        projects_db = db.DB.get("projects", {})
        if not isinstance(projects_db, dict):
            raise DatabaseSchemaError("Invalid database structure: 'projects' is not a dictionary.")

        projects = projects_db.get("projects", {})
        if not isinstance(projects, dict):
            raise DatabaseSchemaError("Invalid database structure: 'projects.projects' is not a dictionary.")
    except AttributeError:
        raise DatabaseSchemaError("Database is not properly initialized.")

    # Search and delete the project
    project_found = False
    for project_id, project in projects.items():
        if not isinstance(project, dict):
            continue  # Skip invalid project entries

        project_external_id = project.get("external_id")
        if project_external_id == external_id:
            try:
                del projects[project_id]
                project_found = True
                break
            except (KeyError, TypeError) as e:
                raise DatabaseSchemaError(f"Failed to delete project: {str(e)}")

    if not project_found:
        raise ProjectNotFoundError(f"No project found with external_id: {external_id}")

    return True
