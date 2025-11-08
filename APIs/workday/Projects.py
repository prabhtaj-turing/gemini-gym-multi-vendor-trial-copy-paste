"""
This module provides functionality for managing projects in the Workday Strategic
Sourcing system.
"""

from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine.models import ProjectFilterModel, PageArgumentModel
from pydantic import ValidationError
from typing import Dict, List, Optional, Any
from .SimulationEngine.models import ProjectInput, PydanticValidationError
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'list_projects',
        'description': 'Retrieves a list of projects based on optional filtering criteria and pagination settings.',
        'parameters': {
            'type': 'object',
            'properties': {
                'filter': {
                    'type': 'object',
                    'description': """ A dictionary containing filter criteria for projects. Supported filters include:
                    If None, no filtering is applied. """,
                    'properties': {
                        'updated_at_from': {
                            'type': 'string',
                            'description': 'Return projects updated on or after the specified timestamp'
                        },
                        'updated_at_to': {
                            'type': 'string',
                            'description': 'Return projects updated on or before the specified timestamp'
                        },
                        'number_from': {
                            'type': 'integer',
                            'description': 'Find projects with number equal or greater than the specified one'
                        },
                        'number_to': {
                            'type': 'integer',
                            'description': 'Find projects with number equal or smaller than the specified one'
                        },
                        'title_contains': {
                            'type': 'string',
                            'description': 'Return projects with title containing the specified string'
                        },
                        'title_not_contains': {
                            'type': 'string',
                            'description': 'Return projects with title not containing the specified string'
                        },
                        'description_contains': {
                            'type': 'string',
                            'description': 'Return projects with description containing the specified string'
                        },
                        'description_not_contains': {
                            'type': 'string',
                            'description': 'Return projects with description not containing the specified string'
                        },
                        'external_id_empty': {
                            'type': 'boolean',
                            'description': 'Return projects with external_id blank'
                        },
                        'external_id_not_empty': {
                            'type': 'boolean',
                            'description': 'Return projects with non-blank external_id'
                        },
                        'external_id_equals': {
                            'type': 'string',
                            'description': 'Find projects by a specific external ID'
                        },
                        'external_id_not_equals': {
                            'type': 'string',
                            'description': 'Find projects excluding the one with the specified external ID'
                        },
                        'actual_start_date_from': {
                            'type': 'string',
                            'description': 'Return projects started on or after the specified date'
                        },
                        'actual_start_date_to': {
                            'type': 'string',
                            'description': 'Return projects started on or before the specified date'
                        },
                        'actual_end_date_from': {
                            'type': 'string',
                            'description': 'Return projects ended on or after the specified date'
                        },
                        'actual_end_date_to': {
                            'type': 'string',
                            'description': 'Return projects ended on or before the specified date'
                        },
                        'target_start_date_from': {
                            'type': 'string',
                            'description': 'Return projects targeted to start on or after the specified date'
                        },
                        'target_start_date_to': {
                            'type': 'string',
                            'description': 'Return projects targeted to start on or before the specified date'
                        },
                        'target_end_date_from': {
                            'type': 'string',
                            'description': 'Return projects targeted to end on or after the specified date'
                        },
                        'target_end_date_to': {
                            'type': 'string',
                            'description': 'Return projects targeted to end on or before the specified date'
                        },
                        'actual_spend_amount_from': {
                            'type': 'number',
                            'description': 'Return projects with actual spend amount equal or greater than the specified amount'
                        },
                        'actual_spend_amount_to': {
                            'type': 'number',
                            'description': 'Return projects with actual spend amount equal or smaller than the specified amount'
                        },
                        'approved_spend_amount_from': {
                            'type': 'number',
                            'description': 'Return projects with approved spend amount equal or greater than the specified amount'
                        },
                        'approved_spend_amount_to': {
                            'type': 'number',
                            'description': 'Return projects with approved spend amount equal or smaller than the specified amount'
                        },
                        'estimated_savings_amount_from': {
                            'type': 'number',
                            'description': 'Return projects with estimated savings amount equal or greater than the specified amount'
                        },
                        'estimated_savings_amount_to': {
                            'type': 'number',
                            'description': 'Return projects with estimated savings amount equal or smaller than the specified amount'
                        },
                        'estimated_spend_amount_from': {
                            'type': 'number',
                            'description': 'Return projects with estimated spend amount equal or greater than the specified amount'
                        },
                        'estimated_spend_amount_to': {
                            'type': 'number',
                            'description': 'Return projects with estimated spend amount equal or smaller than the specified amount'
                        },
                        'canceled_note_contains': {
                            'type': 'string',
                            'description': 'Return projects with cancelation note containing the specified string'
                        },
                        'canceled_note_not_contains': {
                            'type': 'string',
                            'description': 'Return projects with cancelation note not containing the specified string'
                        },
                        'canceled_note_empty': {
                            'type': 'string',
                            'description': 'Return projects with an empty cancelation note'
                        },
                        'canceled_note_not_empty': {
                            'type': 'string',
                            'description': 'Return projects with a non-empty cancelation note'
                        },
                        'canceled_reason_contains': {
                            'type': 'string',
                            'description': 'Return projects with cancelation reason containing the specified string'
                        },
                        'canceled_reason_not_contains': {
                            'type': 'string',
                            'description': 'Return projects with cancelation reason not containing the specified string'
                        },
                        'canceled_reason_empty': {
                            'type': 'string',
                            'description': 'Return projects with an empty cancelation reason'
                        },
                        'canceled_reason_not_empty': {
                            'type': 'string',
                            'description': 'Return projects with a non-empty cancelation reason'
                        },
                        'on_hold_note_contains': {
                            'type': 'string',
                            'description': 'Return projects with on-hold note containing the specified string'
                        },
                        'on_hold_note_not_contains': {
                            'type': 'string',
                            'description': 'Return projects with on-hold note not containing the specified string'
                        },
                        'on_hold_note_empty': {
                            'type': 'string',
                            'description': 'Return projects with an empty on-hold note'
                        },
                        'on_hold_note_not_empty': {
                            'type': 'string',
                            'description': 'Return projects with a non-empty on-hold note'
                        },
                        'on_hold_reason_contains': {
                            'type': 'string',
                            'description': 'Return projects with on-hold reason containing the specified string'
                        },
                        'on_hold_reason_not_contains': {
                            'type': 'string',
                            'description': 'Return projects with on-hold reason not containing the specified string'
                        },
                        'on_hold_reason_empty': {
                            'type': 'string',
                            'description': 'Return projects with an empty on-hold reason'
                        },
                        'on_hold_reason_not_empty': {
                            'type': 'string',
                            'description': 'Return projects with a non-empty on-hold reason'
                        },
                        'needs_attention_equals': {
                            'type': 'boolean',
                            'description': 'Return projects with the specified "needs attention" status'
                        },
                        'needs_attention_not_equals': {
                            'type': 'boolean',
                            'description': 'Return projects with the "needs attention" status not equal to the specified one'
                        },
                        'state_equals': {
                            'type': 'array',
                            'description': 'Find projects with specified statuses (draft, requested, planned, active, completed, canceled, on_hold)',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'marked_as_needs_attention_at_from': {
                            'type': 'string',
                            'description': 'Find projects marked as "needs attention" after or on the specified date'
                        },
                        'marked_as_needs_attention_at_to': {
                            'type': 'string',
                            'description': 'Find projects marked as "needs attention" before or on the specified date'
                        },
                        'needs_attention_note_contains': {
                            'type': 'string',
                            'description': 'Return projects with "needs attention" note containing the specified string'
                        },
                        'needs_attention_note_not_contains': {
                            'type': 'string',
                            'description': 'Return projects with "needs attention" note not containing the specified string'
                        },
                        'needs_attention_note_empty': {
                            'type': 'string',
                            'description': 'Return projects with an empty "needs attention" note'
                        },
                        'needs_attention_note_not_empty': {
                            'type': 'string',
                            'description': 'Return projects with a non-empty "needs attention" note'
                        },
                        'needs_attention_reason_contains': {
                            'type': 'string',
                            'description': 'Return projects with "needs attention" reason containing the specified string'
                        },
                        'needs_attention_reason_not_contains': {
                            'type': 'string',
                            'description': 'Return projects with "needs attention" reason not containing the specified string'
                        },
                        'needs_attention_reason_empty': {
                            'type': 'string',
                            'description': 'Return projects with an empty "needs attention" reason'
                        },
                        'needs_attention_reason_not_empty': {
                            'type': 'string',
                            'description': 'Return projects with a non-empty "needs attention" reason'
                        }
                    },
                    'required': []
                },
                'page': {
                    'type': 'object',
                    'description': """ A dictionary containing pagination settings with 'size' parameter
                    to limit the number of results per page (default: 10, max: 100).
                    If None, no pagination is applied. """,
                    'properties': {
                        'size': {
                            'type': 'integer',
                            'description': 'Number of projects to return per page (default: 10, max: 100)'
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def get(filter: Optional[Dict] = None, page: Optional[Dict] = None) -> List[Dict]:
    """
    Retrieves a list of projects based on optional filtering criteria and pagination settings.

    Args:

        filter (Optional[Dict]): A dictionary containing filter criteria for projects. Supported filters include:
                               - updated_at_from (Optional[str]): Return projects updated on or after the specified timestamp
                               - updated_at_to (Optional[str]): Return projects updated on or before the specified timestamp
                               - number_from (Optional[int]): Find projects with number equal or greater than the specified one
                               - number_to (Optional[int]): Find projects with number equal or smaller than the specified one
                               - title_contains (Optional[str]): Return projects with title containing the specified string
                               - title_not_contains (Optional[str]): Return projects with title not containing the specified string
                               - description_contains (Optional[str]): Return projects with description containing the specified string
                               - description_not_contains (Optional[str]): Return projects with description not containing the specified string
                               - external_id_empty (Optional[bool]): Return projects with external_id blank
                               - external_id_not_empty (Optional[bool]): Return projects with non-blank external_id
                               - external_id_equals (Optional[str]): Find projects by a specific external ID
                               - external_id_not_equals (Optional[str]): Find projects excluding the one with the specified external ID
                               - actual_start_date_from (Optional[str]): Return projects started on or after the specified date
                               - actual_start_date_to (Optional[str]): Return projects started on or before the specified date
                               - actual_end_date_from (Optional[str]): Return projects ended on or after the specified date
                               - actual_end_date_to (Optional[str]): Return projects ended on or before the specified date
                               - target_start_date_from (Optional[str]): Return projects targeted to start on or after the specified date
                               - target_start_date_to (Optional[str]): Return projects targeted to start on or before the specified date
                               - target_end_date_from (Optional[str]): Return projects targeted to end on or after the specified date
                               - target_end_date_to (Optional[str]): Return projects targeted to end on or before the specified date
                               - actual_spend_amount_from (Optional[float]): Return projects with actual spend amount equal or greater than the specified amount
                               - actual_spend_amount_to (Optional[float]): Return projects with actual spend amount equal or smaller than the specified amount
                               - approved_spend_amount_from (Optional[float]): Return projects with approved spend amount equal or greater than the specified amount
                               - approved_spend_amount_to (Optional[float]): Return projects with approved spend amount equal or smaller than the specified amount
                               - estimated_savings_amount_from (Optional[float]): Return projects with estimated savings amount equal or greater than the specified amount
                               - estimated_savings_amount_to (Optional[float]): Return projects with estimated savings amount equal or smaller than the specified amount
                               - estimated_spend_amount_from (Optional[float]): Return projects with estimated spend amount equal or greater than the specified amount
                               - estimated_spend_amount_to (Optional[float]): Return projects with estimated spend amount equal or smaller than the specified amount
                               - canceled_note_contains (Optional[str]): Return projects with cancelation note containing the specified string
                               - canceled_note_not_contains (Optional[str]): Return projects with cancelation note not containing the specified string
                               - canceled_note_empty (Optional[str]): Return projects with an empty cancelation note
                               - canceled_note_not_empty (Optional[str]): Return projects with a non-empty cancelation note
                               - canceled_reason_contains (Optional[str]): Return projects with cancelation reason containing the specified string
                               - canceled_reason_not_contains (Optional[str]): Return projects with cancelation reason not containing the specified string
                               - canceled_reason_empty (Optional[str]): Return projects with an empty cancelation reason
                               - canceled_reason_not_empty (Optional[str]): Return projects with a non-empty cancelation reason
                               - on_hold_note_contains (Optional[str]): Return projects with on-hold note containing the specified string
                               - on_hold_note_not_contains (Optional[str]): Return projects with on-hold note not containing the specified string
                               - on_hold_note_empty (Optional[str]): Return projects with an empty on-hold note
                               - on_hold_note_not_empty (Optional[str]): Return projects with a non-empty on-hold note
                               - on_hold_reason_contains (Optional[str]): Return projects with on-hold reason containing the specified string
                               - on_hold_reason_not_contains (Optional[str]): Return projects with on-hold reason not containing the specified string
                               - on_hold_reason_empty (Optional[str]): Return projects with an empty on-hold reason
                               - on_hold_reason_not_empty (Optional[str]): Return projects with a non-empty on-hold reason
                               - needs_attention_equals (Optional[bool]): Return projects with the specified "needs attention" status
                               - needs_attention_not_equals (Optional[bool]): Return projects with the "needs attention" status not equal to the specified one
                               - state_equals (Optional[List[str]]): Find projects with specified statuses (draft, requested, planned, active, completed, canceled, on_hold)
                               - marked_as_needs_attention_at_from (Optional[str]): Find projects marked as "needs attention" after or on the specified date
                               - marked_as_needs_attention_at_to (Optional[str]): Find projects marked as "needs attention" before or on the specified date
                               - needs_attention_note_contains (Optional[str]): Return projects with "needs attention" note containing the specified string
                               - needs_attention_note_not_contains (Optional[str]): Return projects with "needs attention" note not containing the specified string
                               - needs_attention_note_empty (Optional[str]): Return projects with an empty "needs attention" note
                               - needs_attention_note_not_empty (Optional[str]): Return projects with a non-empty "needs attention" note
                               - needs_attention_reason_contains (Optional[str]): Return projects with "needs attention" reason containing the specified string
                               - needs_attention_reason_not_contains (Optional[str]): Return projects with "needs attention" reason not containing the specified string
                               - needs_attention_reason_empty (Optional[str]): Return projects with an empty "needs attention" reason
                               - needs_attention_reason_not_empty (Optional[str]): Return projects with a non-empty "needs attention" reason
                               If None, no filtering is applied.
        page (Optional[Dict]): A dictionary containing pagination settings with 'size' parameter
                             to limit the number of results per page (default: 10, max: 100).
                             If None, no pagination is applied.
                             - size (Optional[int]): Number of projects to return per page (default: 10, max: 100)

    Returns:
        List[Dict]: A list of dictionaries, where each dictionary contains the details
                   of a project that matches the filter criteria, limited by pagination
                   if specified. Each dictionary contains any of the following fields:
                   - type_id (Optional[str]): Object type
                   - id (Optional[str]): Project identifier string
                   - external_id (Optional[str]): Project external identifier string
                   - supplier_companies (Optional[List]): Array of supplier company objects
                   - supplier_contacts (Optional[List]): Array of supplier contact objects
                   - status (Optional[str]): Project status
                   - attributes (Optional[Dict[str, Union[str, float, bool, datetime.date, None]]]): Project attributes object containing:
                       - name (str): Project name
                       - description (Optional[str]): Project description
                       - state (Optional[str]): Project state (draft, requested, planned, active, completed, canceled, on_hold)
                       - target_start_date (Optional[str]): Project target start date
                       - target_end_date (Optional[str]): Project target end date
                       - actual_spend_amount (Optional[float]): Project actual spend amount
                       - approved_spend_amount (Optional[float]): Project approved spend amount
                       - estimated_savings_amount (Optional[float]): Project estimated savings amount
                       - estimated_spend_amount (Optional[float]): Project estimated spend amount
                       - canceled_note (Optional[str]): Project cancelation note
                       - canceled_reason (Optional[str]): Project cancelation reason
                       - on_hold_note (Optional[str]): Project on-hold note
                       - on_hold_reason (Optional[str]): Project on-hold reason
                       - needs_attention (Optional[bool]): Project needs attention status
                       - marked_as_needs_attention_at (Optional[str]): Project marked as needs attention timestamp
                       - needs_attention_note (Optional[str]): Project needs attention note
                       - needs_attention_reason (Optional[str]): Project needs attention reason
                   - relationships (Optional[Dict[str, Union[List[Dict], Dict]]]): Project relationships object containing:
                       - attachments (Optional[List[Dict]]): Array of attachment objects
                       - creator (Optional[Dict]): Project creator stakeholder object
                       - requester (Optional[Dict]): Project requester stakeholder object
                       - owner (Optional[Dict]): Project owner stakeholder object
                       - project_type (Optional[Dict]): Project type object
                   - links (Optional[Dict[str, str]]): Resource links object containing:
                       - self (str): Normalized link to the resource
                       
    Raises:
        TypeError: If 'filter' or 'page' are provided but are not dictionaries.
        ValidationError: If 'filter' or 'page' data does not conform to the
                                  ProjectFilterModel or PageArgumentModel structure respectively (e.g., wrong data types,
                                  out-of-range values, forbidden extra fields).
    """
    validated_filter_model: Optional[ProjectFilterModel] = None
    if filter is not None:
        if not isinstance(filter, dict):
            raise TypeError("Argument 'filter' must be a dictionary or None.")
        try:
            validated_filter_model = ProjectFilterModel(**filter)
        except ValidationError as e:
            raise e

    validated_page_model: Optional[PageArgumentModel] = None
    if page is not None:
        if not isinstance(page, dict):
            raise TypeError("Argument 'page' must be a dictionary or None.")
        try:
            validated_page_model = PageArgumentModel(**page)
        except ValidationError as e:
            raise e

    # --- Original Core Logic ---
    projects = list(db.DB["projects"]["projects"].values())

    if validated_filter_model:
        # Convert Pydantic model to dict, excluding fields that were not set (None)
        active_filters = validated_filter_model.model_dump(exclude_none=True)
        
        if active_filters:
            current_filtered_projects = []
            for project_item in projects:
                match = True
                for key, value in active_filters.items():
                    if project_item.get(key) != value:
                        match = False
                        break
                if match:
                    current_filtered_projects.append(project_item)
            projects = current_filtered_projects

    if validated_page_model and validated_page_model.size is not None:
        size = validated_page_model.size
        projects = projects[:size]
    
    return projects

@tool_spec(
    spec={
        'name': 'create_project',
        'description': 'Creates a new project with the specified attributes.',
        'parameters': {
            'type': 'object',
            'properties': {
                'project_data': {
                    'type': 'object',
                    'description': """ A dictionary containing the project attributes.
                    If 'id' is not provided, a new unique ID will be generated.
                    'attributes' field with at least 'name' is mandatory.
                    project_data can contain any of the following keys: """,
                    'properties': {
                        'type_id': {
                            'type': 'string',
                            'description': 'Object type (defaults to "projects")'
                        },
                        'id': {
                            'type': 'string',
                            'description': 'Project identifier string'
                        },
                        'external_id': {
                            'type': 'string',
                            'description': 'Project external identifier string'
                        },
                        'supplier_companies': {
                            'type': 'array',
                            'description': 'Array of supplier company objects',
                            'items': {
                                'type': 'object',
                                'properties': {},
                                'required': []
                            }
                        },
                        'supplier_contacts': {
                            'type': 'array',
                            'description': 'Array of supplier contact objects',
                            'items': {
                                'type': 'object',
                                'properties': {},
                                'required': []
                            }
                        },
                        'status': {
                            'type': 'string',
                            'description': 'Project status'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Project attributes object containing:',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Project name (mandatory)'
                                },
                                'description': {
                                    'type': 'string',
                                    'description': 'Project description'
                                },
                                'state': {
                                    'type': 'string',
                                    'description': 'Project state (draft, requested, planned, active, completed, canceled, on_hold)'
                                },
                                'target_start_date': {
                                    'type': 'string',
                                    'description': 'Project target start date'
                                },
                                'target_end_date': {
                                    'type': 'string',
                                    'description': 'Project target end date'
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
                                    'description': 'Project marked as needs attention timestamp'
                                },
                                'needs_attention_note': {
                                    'type': 'string',
                                    'description': 'Project needs attention note'
                                },
                                'needs_attention_reason': {
                                    'type': 'string',
                                    'description': 'Project needs attention reason'
                                }
                            },
                            'required': [
                                'name'
                            ]
                        },
                        'relationships': {
                            'type': 'object',
                            'description': 'Project relationships object containing:',
                            'properties': {
                                'attachments': {
                                    'type': 'array',
                                    'description': 'Array of attachment objects',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                },
                                'creator': {
                                    'type': 'object',
                                    'description': 'Project creator stakeholder object',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Should always be "stakeholders"'
                                        },
                                        'id': {
                                            'type': 'string',
                                            'description': 'Stakeholder identifier string'
                                        }
                                    },
                                    'required': []
                                },
                                'requester': {
                                    'type': 'object',
                                    'description': 'Project requester stakeholder object',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Should always be "stakeholders"'
                                        },
                                        'id': {
                                            'type': 'string',
                                            'description': 'Stakeholder identifier string'
                                        }
                                    },
                                    'required': []
                                },
                                'owner': {
                                    'type': 'object',
                                    'description': 'Project owner stakeholder object',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Should always be "stakeholders"'
                                        },
                                        'id': {
                                            'type': 'string',
                                            'description': 'Stakeholder identifier string'
                                        }
                                    },
                                    'required': []
                                },
                                'project_type': {
                                    'type': 'object',
                                    'description': 'Project type object',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Should always be "project_types"'
                                        },
                                        'id': {
                                            'type': 'string',
                                            'description': 'Project type identifier string'
                                        }
                                    },
                                    'required': []
                                }
                            },
                            'required': []
                        }
                    },
                    'required': [
                        'attributes'
                    ]
                }
            },
            'required': [
                'project_data'
            ]
        }
    }
)
def post(project_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new project with the specified attributes.

    Args:
        project_data (Dict[str, Any]): A dictionary containing the project attributes.
            If 'id' is not provided, a new unique ID will be generated.
            'attributes' field with at least 'name' is mandatory.
            project_data can contain any of the following keys:
            - type_id (Optional[str]): Object type (defaults to "projects")
            - id (Optional[str]): Project identifier string
            - external_id (Optional[str]): Project external identifier string
            - supplier_companies (Optional[List[Dict[str, Any]]]): Array of supplier company objects
            - supplier_contacts (Optional[List[Dict[str, Any]]]): Array of supplier contact objects
            - status (Optional[str]): Project status
            - attributes (Dict[str, Union[str, float, bool, datetime.date, None]]): Project attributes object containing:
                - name (str): Project name (mandatory)
                - description (Optional[str]): Project description
                - state (Optional[str]): Project state (draft, requested, planned, active, completed, canceled, on_hold)
                - target_start_date (Optional[str]): Project target start date
                - target_end_date (Optional[str]): Project target end date
                - actual_spend_amount (Optional[float]): Project actual spend amount
                - approved_spend_amount (Optional[float]): Project approved spend amount
                - estimated_savings_amount (Optional[float]): Project estimated savings amount
                - estimated_spend_amount (Optional[float]): Project estimated spend amount
                - canceled_note (Optional[str]): Project cancelation note
                - canceled_reason (Optional[str]): Project cancelation reason
                - on_hold_note (Optional[str]): Project on-hold note
                - on_hold_reason (Optional[str]): Project on-hold reason
                - needs_attention (Optional[bool]): Project needs attention status
                - marked_as_needs_attention_at (Optional[str]): Project marked as needs attention timestamp
                - needs_attention_note (Optional[str]): Project needs attention note
                - needs_attention_reason (Optional[str]): Project needs attention reason
            - relationships (Optional[Dict[str, Union[List[Dict], Dict]]]): Project relationships object containing:
                - attachments (Optional[List[Dict]]): Array of attachment objects
                - creator (Optional[Dict]): Project creator stakeholder object
                    - type (Optional[str]): Should always be "stakeholders"
                    - id (Optional[str]): Stakeholder identifier string
                - requester (Optional[Dict]): Project requester stakeholder object
                    - type (Optional[str]): Should always be "stakeholders"
                    - id (Optional[str]): Stakeholder identifier string
                - owner (Optional[Dict]): Project owner stakeholder object
                    - type (Optional[str]): Should always be "stakeholders"
                    - id (Optional[str]): Stakeholder identifier string
                - project_type (Optional[Dict]): Project type object
                    - type (Optional[str]): Should always be "project_types"
                    - id (Optional[str]): Project type identifier string

    Returns:
        Dict[str, Any]: The created project data, including the assigned ID if one was generated.
            The project data will be returned with the following keys:
            - type_id (Optional[str]): Object type
            - id (Optional[str]): Project identifier string
            - external_id (Optional[str]): Project external identifier string
            - supplier_companies (Optional[List[Dict[str, Any]]]): Array of supplier company objects
            - supplier_contacts (Optional[List[Dict[str, Any]]]): Array of supplier contact objects
            - status (Optional[str]): Project status
            - attributes (Optional[Dict[str, Union[str, float, bool, datetime.date, None]]]): Project attributes object containing:
                - name (str): Project name
                - description (Optional[str]): Project description
                - state (Optional[str]): Project state (draft, requested, planned, active, completed, canceled, on_hold)
                - target_start_date (Optional[str]): Project target start date
                - target_end_date (Optional[str]): Project target end date
                - actual_spend_amount (Optional[float]): Project actual spend amount
                - approved_spend_amount (Optional[float]): Project approved spend amount
                - estimated_savings_amount (Optional[float]): Project estimated savings amount
                - estimated_spend_amount (Optional[float]): Project estimated spend amount
                - canceled_note (Optional[str]): Project cancelation note
                - canceled_reason (Optional[str]): Project cancelation reason
                - on_hold_note (Optional[str]): Project on-hold note
                - on_hold_reason (Optional[str]): Project on-hold reason
                - needs_attention (Optional[bool]): Project needs attention status
                - marked_as_needs_attention_at (Optional[str]): Project marked as needs attention timestamp
                - needs_attention_note (Optional[str]): Project needs attention note
                - needs_attention_reason (Optional[str]): Project needs attention reason
            - relationships (Optional[Dict[str, Union[List[Dict], Dict]]]): Project relationships object containing:
                - attachments (Optional[List[Dict]]): Array of attachment objects
                - creator (Optional[Dict]): Project creator stakeholder object
                    - type (Optional[str]): Should always be "stakeholders"
                    - id (Optional): Stakeholder identifier string
                - requester (Optional[Dict]): Project requester stakeholder object
                    - type (Optional[str]): Should always be "stakeholders"
                    - id (Optional): Stakeholder identifier string
                - owner (Optional[Dict]): Project owner stakeholder object
                    - type (Optional[str]): Should always be "stakeholders"
                    - id (Optional): Stakeholder identifier string
                - project_type (Optional[Dict]): Project type object
                    - type (Optional[str]): Should always be "project_types"
                    - id (Optional[str]): Project type identifier string
            - links (Optional[Dict[str, str]]): Resource links object containing:
                - self (str): Normalized link to the resource

    Raises:
        TypeError: If 'project_data' is not a dictionary.
        ValidationError: If 'project_data' does not conform to the ProjectInput model structure
                                  (e.g., missing 'attributes', 'attributes' missing 'name', incorrect field types,
                                   or extra fields not defined in models).
    """
    if not isinstance(project_data, dict):
        raise TypeError("Input 'project_data' must be a dictionary.")

    try:
        validated_model = ProjectInput(**project_data)
        processed_project_data = validated_model.model_dump(exclude_none=True) # exclude_none=True to keep it cleaner
    except PydanticValidationError as e:
        raise e

    # --- Original core logic starts here ---
    if "projects" not in db.DB: # type: ignore
        db.DB["projects"] = {"projects": {}} # type: ignore
    elif "projects" not in db.DB["projects"]: # type: ignore
        db.DB["projects"]["projects"] = {} # type: ignore
    
    current_projects_dict = db.DB.get("projects", {}).get("projects", {}) # type: ignore

    if processed_project_data.get("id") is None:
        project_id_num = len(current_projects_dict.keys()) + 1
        processed_project_data["id"] = str(project_id_num) # ID should be a string as per model

    # Store the processed_project_data using its 'id' as the key.
    db.DB["projects"]["projects"][processed_project_data["id"]] = processed_project_data # type: ignore
    # --- Original core logic ends ---

    return processed_project_data

