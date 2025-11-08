"""
Event Management Module for Workday Strategic Sourcing API Simulation.

This module provides functionality for managing events in the Workday Strategic Sourcing system.
Events are core components that represent sourcing activities, auctions, and related processes.
The module supports CRUD operations for events and includes features for event filtering,
pagination, and template-based event creation.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Optional
from .SimulationEngine import db
from .SimulationEngine.models import EventInputModel, PaginationModel, EventFilterModel, EventIdModel, EventResponseModel
from pydantic import ValidationError, BaseModel, Field
from typing import Any
from .SimulationEngine import models

@tool_spec(
    spec={
        'name': 'list_events_with_filters',
        'description': 'Returns a list of events for the specified criteria.',
        'parameters': {
            'type': 'object',
            'properties': {
                'filter': {
                    'type': 'object',
                    'description': """ Dictionary containing filter criteria where keys are
                    event attributes and values are the desired values to match. All filter properties are optional.
                    Supported filters: """,
                    'properties': {
                        'updated_at_from': {
                            'type': 'string',
                            'description': 'Return events updated on or after timestamp'
                        },
                        'updated_at_to': {
                            'type': 'string',
                            'description': 'Return events updated on or before timestamp'
                        },
                        'title_contains': {
                            'type': 'string',
                            'description': 'Return events with title containing string'
                        },
                        'title_not_contains': {
                            'type': 'string',
                            'description': 'Return events with title not containing string'
                        },
                        'spend_category_id_equals': {
                            'type': 'array',
                            'description': 'Find events using specified Spend Category IDs',
                            'items': {
                                'type': 'integer'
                            }
                        },
                        'state_equals': {
                            'type': 'array',
                            'description': 'Find events with specified states ("draft", "scheduled", "published", "live_editing", "closed", "canceled")',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'event_type_equals': {
                            'type': 'array',
                            'description': 'Find events with specified types ("RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT", "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT")',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'request_type_equals': {
                            'type': 'array',
                            'description': 'Find events with specified request types',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'supplier_rsvp_deadline_from': {
                            'type': 'string',
                            'description': 'Return events with RSVP deadline on or after date'
                        },
                        'supplier_rsvp_deadline_to': {
                            'type': 'string',
                            'description': 'Return events with RSVP deadline on or before date'
                        },
                        'supplier_rsvp_deadline_empty': {
                            'type': 'boolean',
                            'description': 'Return events with RSVP deadline not set'
                        },
                        'supplier_rsvp_deadline_not_empty': {
                            'type': 'boolean',
                            'description': 'Return events with RSVP deadline set'
                        },
                        'supplier_question_deadline_from': {
                            'type': 'string',
                            'description': 'Return events with questions deadline on or after date'
                        },
                        'supplier_question_deadline_to': {
                            'type': 'string',
                            'description': 'Return events with questions deadline on or before date'
                        },
                        'supplier_question_deadline_empty': {
                            'type': 'boolean',
                            'description': 'Return events with questions deadline not set'
                        },
                        'supplier_question_deadline_not_empty': {
                            'type': 'boolean',
                            'description': 'Return events with questions deadline set'
                        },
                        'bid_submission_deadline_from': {
                            'type': 'string',
                            'description': 'Return events with bid deadline on or after date'
                        },
                        'bid_submission_deadline_to': {
                            'type': 'string',
                            'description': 'Return events with bid deadline on or before date'
                        },
                        'bid_submission_deadline_empty': {
                            'type': 'boolean',
                            'description': 'Return events with bid deadline not set'
                        },
                        'bid_submission_deadline_not_empty': {
                            'type': 'boolean',
                            'description': 'Return events with bid deadline set'
                        },
                        'created_at_from': {
                            'type': 'string',
                            'description': 'Return events created on or after timestamp'
                        },
                        'created_at_to': {
                            'type': 'string',
                            'description': 'Return events created on or before timestamp'
                        },
                        'published_at_from': {
                            'type': 'string',
                            'description': 'Return events published on or after timestamp'
                        },
                        'published_at_to': {
                            'type': 'string',
                            'description': 'Return events published on or before timestamp'
                        },
                        'published_at_empty': {
                            'type': 'boolean',
                            'description': 'Return events without published timestamp'
                        },
                        'published_at_not_empty': {
                            'type': 'boolean',
                            'description': 'Return events with published timestamp'
                        },
                        'closed_at_from': {
                            'type': 'string',
                            'description': 'Return events closed on or after timestamp'
                        },
                        'closed_at_to': {
                            'type': 'string',
                            'description': 'Return events closed on or before timestamp'
                        },
                        'closed_at_empty': {
                            'type': 'boolean',
                            'description': 'Return events without closed timestamp'
                        },
                        'closed_at_not_empty': {
                            'type': 'boolean',
                            'description': 'Return events with closed timestamp'
                        },
                        'spend_amount_from': {
                            'type': 'number',
                            'description': 'Return events with spend amount >= amount'
                        },
                        'spend_amount_to': {
                            'type': 'number',
                            'description': 'Return events with spend amount <= amount'
                        },
                        'spend_amount_empty': {
                            'type': 'boolean',
                            'description': 'Return events with spend amount not set'
                        },
                        'spend_amount_not_empty': {
                            'type': 'boolean',
                            'description': 'Return events with spend amount set'
                        },
                        'external_id_empty': {
                            'type': 'boolean',
                            'description': 'Return events with blank external_id'
                        },
                        'external_id_not_empty': {
                            'type': 'boolean',
                            'description': 'Return events with non-blank external_id'
                        },
                        'external_id_equals': {
                            'type': 'string',
                            'description': 'Find events by specific external ID'
                        },
                        'external_id_not_equals': {
                            'type': 'string',
                            'description': 'Find events excluding specified external ID'
                        }
                    },
                    'required': []
                },
                'page': {
                    'type': 'object',
                    'description': 'Dictionary containing pagination parameters:',
                    'properties': {
                        'size': {
                            'type': 'integer',
                            'description': 'Number of results per page (default: 10, max: 100)'
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
    Returns a list of events for the specified criteria.

    Args:
        filter (Optional[Dict], optional): Dictionary containing filter criteria where keys are
            event attributes and values are the desired values to match. All filter properties are optional.
            Supported filters:
            - updated_at_from (Optional[str]): Return events updated on or after timestamp
            - updated_at_to (Optional[str]): Return events updated on or before timestamp
            - title_contains (Optional[str]): Return events with title containing string
            - title_not_contains (Optional[str]): Return events with title not containing string
            - spend_category_id_equals (Optional[List[int]]): Find events using specified Spend Category IDs
            - state_equals (Optional[List[str]]): Find events with specified states ("draft", "scheduled", "published", "live_editing", "closed", "canceled")
            - event_type_equals (Optional[List[str]]): Find events with specified types ("RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT", "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT")
            - request_type_equals (Optional[List[str]]): Find events with specified request types
            - supplier_rsvp_deadline_from (Optional[str]): Return events with RSVP deadline on or after date
            - supplier_rsvp_deadline_to (Optional[str]): Return events with RSVP deadline on or before date
            - supplier_rsvp_deadline_empty (Optional[bool]): Return events with RSVP deadline not set
            - supplier_rsvp_deadline_not_empty (Optional[bool]): Return events with RSVP deadline set
            - supplier_question_deadline_from (Optional[str]): Return events with questions deadline on or after date
            - supplier_question_deadline_to (Optional[str]): Return events with questions deadline on or before date
            - supplier_question_deadline_empty (Optional[bool]): Return events with questions deadline not set
            - supplier_question_deadline_not_empty (Optional[bool]): Return events with questions deadline set
            - bid_submission_deadline_from (Optional[str]): Return events with bid deadline on or after date
            - bid_submission_deadline_to (Optional[str]): Return events with bid deadline on or before date
            - bid_submission_deadline_empty (Optional[bool]): Return events with bid deadline not set
            - bid_submission_deadline_not_empty (Optional[bool]): Return events with bid deadline set
            - created_at_from (Optional[str]): Return events created on or after timestamp
            - created_at_to (Optional[str]): Return events created on or before timestamp
            - published_at_from (Optional[str]): Return events published on or after timestamp
            - published_at_to (Optional[str]): Return events published on or before timestamp
            - published_at_empty (Optional[bool]): Return events without published timestamp
            - published_at_not_empty (Optional[bool]): Return events with published timestamp
            - closed_at_from (Optional[str]): Return events closed on or after timestamp
            - closed_at_to (Optional[str]): Return events closed on or before timestamp
            - closed_at_empty (Optional[bool]): Return events without closed timestamp
            - closed_at_not_empty (Optional[bool]): Return events with closed timestamp
            - spend_amount_from (Optional[float]): Return events with spend amount >= amount
            - spend_amount_to (Optional[float]): Return events with spend amount <= amount
            - spend_amount_empty (Optional[bool]): Return events with spend amount not set
            - spend_amount_not_empty (Optional[bool]): Return events with spend amount set
            - external_id_empty (Optional[bool]): Return events with blank external_id
            - external_id_not_empty (Optional[bool]): Return events with non-blank external_id
            - external_id_equals (Optional[str]): Find events by specific external ID
            - external_id_not_equals (Optional[str]): Find events excluding specified external ID
        page (Optional[Dict], optional): Dictionary containing pagination parameters:
            - size (Optional[int]): Number of results per page (default: 10, max: 100)

    Returns:
        List[Dict]: A list of event dictionaries, where each event contains any of the following keys:
            - id (str): Event identifier string
            - name (str): Event name
            - type (str): Event type enum ("RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT", "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT")
            - duplication_state (str): Event duplication state enum ("scheduled", "started", "finished", "failed")
            - suppliers (list): List of suppliers
            - supplier_contacts (list): List of supplier contacts
            - attributes (dict): Event attributes containing:
                - title (str): An event title
                - event_type (str): Event type enum ("RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT", "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT")
                - state (str): Current event state enum ("draft", "scheduled", "published", "live_editing", "closed", "canceled")
                - duplication_state (str): Event duplication state enum ("scheduled", "started", "finished", "failed")
                - spend_amount (float): Actual spend amount
                - request_type (str): Request type
                - late_bids (bool): Whether late bid submissions are allowed
                - revise_bids (bool): Whether suppliers can re-submit bids
                - instant_notifications (bool): Whether notifications are sent immediately
                - supplier_rsvp_deadline (str): RSVP deadline date-time
                - supplier_question_deadline (str): Questions deadline date-time
                - bid_submission_deadline (str): Bid submission deadline date-time
                - created_at (str): Creation date-time
                - closed_at (str): Closing date-time
                - published_at (str): Publication date-time
                - external_id (str): Event ID in internal database
                - is_public (bool): Whether event is accessible for self-registration
                - restricted (bool): Whether event is invitation only
                - custom_fields (list): Custom field values
            - relationships (dict): Event relationships containing:
                - attachments (list): List of attachments
                - project (dict): Associated project
                - spend_category (dict): Associated spend category
                - event_template (dict): Used event template
                - commodity_codes (list): List of commodity codes
            - links (dict): Related links containing:
                - self (str): URL to the resource
    Raises:
        TypeError: If 'filter' or 'page' are provided but are not dictionaries.
        ValidationError: If 'filter' or 'page' dictionary does not conform
                                  to the expected structure (e.g., invalid field types, unknown fields,
                                  values out of constraints like page size limits).
    """
    if filter is not None:
        if not isinstance(filter, dict):
            raise TypeError("Argument 'filter' must be a dictionary or None.")
        try:
            EventFilterModel(**filter)
        except ValidationError as e:
            raise e

    validated_page_model = None
    if page is not None:
        if not isinstance(page, dict):
            raise TypeError("Argument 'page' must be a dictionary or None.")
        try:
            validated_page_model = PaginationModel(**page)
        except ValidationError as e:
            raise e

    # --- Core Logic (preserved) ---
    events_data = db.DB["events"]["events"]
    if not isinstance(events_data, dict):
        events = []
    else:
        events = list(events_data.values())


    if filter:
        filtered_events = []
        for event_item in events:
            match = True
            for key, value in filter.items():
                if key not in event_item or event_item[key] != value:
                    match = False
                    break
            if match:
                filtered_events.append(event_item)
        events = filtered_events
    
    if validated_page_model and validated_page_model.size is not None:
        size = validated_page_model.size
        events = events[:size]
    
    return events

@tool_spec(
    spec={
        'name': 'create_event',
        'description': """ Create a new event.
        
        This function creates a new event in the Workday Strategic Sourcing system. It
        validates the input data and creates a new event with the provided details.
        The new event is added to the events database and returned as a dictionary. The
        event is assigned a unique identifier and duplication state is set to "scheduled". """,
        'parameters': {
            'type': 'object',
            'properties': {
                'data': {
                    'type': 'object',
                    'description': 'Dictionary containing event creation data. Can contain any of the following keys:',
                    'properties': {
                        'external_id': {
                            'type': 'string',
                            'description': 'Event identifier string'
                        },
                        'name': {
                            'type': 'string',
                            'description': 'Event name'
                        },
                        'type': {
                            'type': 'string',
                            'description': """ Event type. Can be one of the following: "RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT", "PERFORMANCE_REVIEW_EVENT",
                                                     "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT" """
                        },
                        'suppliers': {
                            'type': 'array',
                            'description': 'List of suppliers',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'supplier_contacts': {
                            'type': 'array',
                            'description': 'List of supplier contacts',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Event attributes containing:',
                            'properties': {
                                'title': {
                                    'type': 'string',
                                    'description': 'An event title'
                                },
                                'event_type': {
                                    'type': 'string',
                                    'description': """ Event type. Can be one of the following: "RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT",
                                                                       "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT",
                                                                      "SUPPLIER_REVIEW_MASTER_EVENT" """
                                },
                                'state': {
                                    'type': 'string',
                                    'description': 'Current event state. Can be one of the following: "draft", "scheduled", "published", "live_editing", "closed", "canceled"'
                                },
                                'duplication_state': {
                                    'type': 'string',
                                    'description': 'Event duplication state. Can be one of the following: "scheduled", "started", "finished", "failed"'
                                },
                                'spend_amount': {
                                    'type': 'number',
                                    'description': 'Actual spend amount'
                                },
                                'request_type': {
                                    'type': 'string',
                                    'description': 'Request type'
                                },
                                'late_bids': {
                                    'type': 'boolean',
                                    'description': 'Whether late bid submissions are allowed'
                                },
                                'revise_bids': {
                                    'type': 'boolean',
                                    'description': 'Whether suppliers can re-submit bids'
                                },
                                'instant_notifications': {
                                    'type': 'boolean',
                                    'description': 'Whether notifications are sent immediately'
                                },
                                'supplier_rsvp_deadline': {
                                    'type': 'string',
                                    'description': 'RSVP deadline date-time'
                                },
                                'supplier_question_deadline': {
                                    'type': 'string',
                                    'description': 'Questions deadline date-time'
                                },
                                'bid_submission_deadline': {
                                    'type': 'string',
                                    'description': 'Bid submission deadline date-time'
                                },
                                'created_at': {
                                    'type': 'string',
                                    'description': 'Creation date-time'
                                },
                                'closed_at': {
                                    'type': 'string',
                                    'description': 'Closing date-time'
                                },
                                'published_at': {
                                    'type': 'string',
                                    'description': 'Publication date-time'
                                },
                                'external_id': {
                                    'type': 'string',
                                    'description': 'Event ID in internal database'
                                },
                                'is_public': {
                                    'type': 'boolean',
                                    'description': 'Whether event is accessible for self-registration'
                                },
                                'restricted': {
                                    'type': 'boolean',
                                    'description': 'Whether event is invitation only'
                                },
                                'custom_fields': {
                                    'type': 'array',
                                    'description': 'Custom field values',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                }
                            },
                            'required': []
                        },
                        'relationships': {
                            'type': 'object',
                            'description': 'Event relationships containing:',
                            'properties': {
                                'attachments': {
                                    'type': 'array',
                                    'description': 'List of attachments',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                },
                                'project': {
                                    'type': 'object',
                                    'description': 'Associated project',
                                    'properties': {},
                                    'required': []
                                },
                                'spend_category': {
                                    'type': 'object',
                                    'description': 'Associated spend category',
                                    'properties': {},
                                    'required': []
                                },
                                'event_template': {
                                    'type': 'object',
                                    'description': 'Used event template',
                                    'properties': {},
                                    'required': []
                                },
                                'commodity_codes': {
                                    'type': 'array',
                                    'description': 'List of commodity codes',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                }
                            },
                            'required': []
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'data'
            ]
        }
    }
)
def post(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new event.

    This function creates a new event in the Workday Strategic Sourcing system. It
    validates the input data and creates a new event with the provided details.
    The new event is added to the events database and returned as a dictionary. The
    event is assigned a unique identifier and duplication state is set to "scheduled".
    
    Args:
        data (Dict[str, Any]): Dictionary containing event creation data. Can contain any of the following keys:
            - external_id (Optional[str]): Event identifier string
            - name (Optional[str]): Event name
            - type (Optional[str]): Event type. Can be one of the following: "RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT", "PERFORMANCE_REVIEW_EVENT",
                                    "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT"
            - suppliers (Optional[List[str]]): List of suppliers
            - supplier_contacts (Optional[List[str]]): List of supplier contacts
            - attributes (Optional[Dict[str, Any]]): Event attributes containing:
                - title (Optional[str]): An event title
                - event_type (Optional[str]): Event type. Can be one of the following: "RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT",
                                              "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT",
                                              "SUPPLIER_REVIEW_MASTER_EVENT"
                - state (Optional[str]): Current event state. Can be one of the following: "draft", "scheduled", "published", "live_editing", "closed", "canceled"
                - duplication_state (Optional[str]): Event duplication state. Can be one of the following: "scheduled", "started", "finished", "failed"
                - spend_amount (Optional[float]): Actual spend amount
                - request_type (Optional[str]): Request type
                - late_bids (Optional[bool]): Whether late bid submissions are allowed
                - revise_bids (Optional[bool]): Whether suppliers can re-submit bids
                - instant_notifications (Optional[bool]): Whether notifications are sent immediately
                - supplier_rsvp_deadline (Optional[str]): RSVP deadline date-time
                - supplier_question_deadline (Optional[str]): Questions deadline date-time
                - bid_submission_deadline (Optional[str]): Bid submission deadline date-time
                - created_at (Optional[str]): Creation date-time
                - closed_at (Optional[str]): Closing date-time
                - published_at (Optional[str]): Publication date-time
                - external_id (Optional[str]): Event ID in internal database
                - is_public (Optional[bool]): Whether event is accessible for self-registration
                - restricted (Optional[bool]): Whether event is invitation only
                - custom_fields (Optional[List[Dict[str, Any]]]): Custom field values
            - relationships (Optional[Dict[str, Any]]): Event relationships containing:
                - attachments (Optional[List[Dict[str, Any]]]): List of attachments
                - project (Optional[Dict[str, Any]]): Associated project
                - spend_category (Optional[Dict[str, Any]]): Associated spend category
                - event_template (Optional[Dict[str, Any]]): Used event template
                - commodity_codes (Optional[List[Dict[str, Any]]]): List of commodity codes

    Returns:
        Dict[str, Any]: The newly created event object containing:
            - id (str): Event identifier id
            - duplication_state (str): Event duplication state (default: "scheduled")
            - external_id (Optional[str]): Event identifier string
            - name (Optional[str]): Event name
            - type (Optional[str]): Event type. Can be one of the following: "RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT", "PERFORMANCE_REVIEW_EVENT",
                                    "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT"
            - suppliers (Optional[List[Any]]): List of suppliers
            - supplier_contacts (Optional[List[Any]]): List of supplier contacts
            - attributes (Optional[Dict[str, Any]]): Event attributes containing:
                - title (Optional[str]): An event title
                - event_type (Optional[str]): Event type. Can be one of the following: "RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT",
                                              "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT",
                                              "SUPPLIER_REVIEW_MASTER_EVENT"
                - state (Optional[str]): Current event state. Can be one of the following: "draft", "scheduled", "published", "live_editing", "closed", "canceled"
                - duplication_state (Optional[str]): Event duplication state. Can be one of the following: "scheduled", "started", "finished", "failed"
                - spend_amount (Optional[float]): Actual spend amount
                - request_type (Optional[str]): Request type
                - late_bids (Optional[bool]): Whether late bid submissions are allowed
                - revise_bids (Optional[bool]): Whether suppliers can re-submit bids
                - instant_notifications (Optional[bool]): Whether notifications are sent immediately
                - supplier_rsvp_deadline (Optional[str]): RSVP deadline date-time
                - supplier_question_deadline (Optional[str]): Questions deadline date-time
                - bid_submission_deadline (Optional[str]): Bid submission deadline date-time
                - created_at (Optional[str]): Creation date-time
                - closed_at (Optional[str]): Closing date-time
                - published_at (Optional[str]): Publication date-time
                - external_id (Optional[str]): Event ID in internal database
                - is_public (Optional[bool]): Whether event is accessible for self-registration
                - restricted (Optional[bool]): Whether event is invitation only
                - custom_fields (Optional[List[Any]]): Custom field values
            - relationships (Optional[Dict[str, Any]]): Event relationships containing:
                - attachments (Optional[List[Any]]): List of attachments
                - project (Optional[Dict[str, Any]]): Associated project
                - spend_category (Optional[Dict[str, Any]]): Associated spend category
                - event_template (Optional[Dict[str, Any]]): Used event template
                - commodity_codes (Optional[List[Any]]): List of commodity codes
    Raises:
        TypeError: If the 'data' argument is not a dictionary.
        ValidationError: If the 'data' argument does not conform to the EventInputModel structure,
                                  including type errors or invalid enum values within the dictionary.
    """
    # Validate input type for 'data'
    if not isinstance(data, dict):
        raise TypeError("Input 'data' must be a dictionary.")

    try:
        validated_event_input = EventInputModel(**data)
    except ValidationError as e:
        raise e

    validated_data_dict = validated_event_input.model_dump(exclude_none=True)

    new_id = max([int(k) for k in db.DB["events"]["events"].keys()], default=0) + 1
    new_event = {
        "id": str(new_id),
        "duplication_state": "scheduled",
        **validated_data_dict
    }
    db.DB["events"]["events"][str(new_id)] = new_event
    return new_event

@tool_spec(
    spec={
        'name': 'get_event_by_id',
        'description': 'Retrieve details of a specific event.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the event to retrieve.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_by_id(id: int) -> Dict:
    """
    Retrieve details of a specific event.

    Args:
        id (int): The unique identifier of the event to retrieve.

    Returns:
        Dict: A dictionary representing the event object, containing the following keys:
            - id (str): Event identifier.
            - type (str): The object type, typically "events".
            - attributes (dict): A dictionary of event attributes, containing:
                - name (str): Event name.
                - title (str): An event title.
                - event_type (str): Event type ("RFP", "AUCTION", etc.).
                - state (str): Current event state ("draft", "published", "closed", etc.).
                - duplication_state (str): Event duplication state ("scheduled", "finished", etc.).
                - spend_amount (float): Actual spend amount.
                - request_type (str): Request type.
                - late_bids (bool): Whether late bid submissions are allowed.
                - revise_bids (bool): Whether suppliers can re-submit bids.
                - instant_notifications (bool): Whether notifications are sent immediately.
                - supplier_rsvp_deadline (str): RSVP deadline date-time (ISO 8601 format).
                - supplier_question_deadline (str): Questions deadline date-time (ISO 8601 format).
                - bid_submission_deadline (str): Bid submission deadline date-time (ISO 8601 format).
                - created_at (str): Creation date-time (ISO 8601 format).
                - closed_at (str): Closing date-time (ISO 8601 format).
                - published_at (str): Publication date-time (ISO 8601 format).
                - external_id (str): Event ID in an internal database.
                - is_public (bool): Whether the event is accessible for self-registration.
                - restricted (bool): Whether the event is invitation-only.
                - custom_fields (list): A list of custom field values for the event.
            - relationships (dict): A dictionary of related resources, containing:
                - attachments (list): A list of attachment objects.
                - project (dict): The associated project object.
                - spend_category (dict): The associated spend category object.
                - event_template (dict): The event template used.
                - commodity_codes (list): A list of associated commodity codes.
                - suppliers (list): A list of supplier objects.
                - supplier_contacts (list): A list of supplier contact objects.
            - links (dict): A dictionary of related HATEOAS links, e.g., {"self": "URL"}.
                
    Raises:
        TypeError: If the 'id' argument is not an integer.
        ValueError: If no event with the specified 'id' is found in the database.
    """
    # Validation for type and positive value
    if not isinstance(id, int):
        raise TypeError("Event ID must be an integer.")
    if id <= 0:
        raise ValueError("Event ID must be a positive integer.")

    # Use .get() for a cleaner lookup and check the result.
    # Convert integer ID to string for database lookup since IDs are stored as strings
    event = db.DB.get("events", {}).get("events", {}).get(str(id))
    if event is None:
        raise ValueError(f"Event with ID '{id}' not found.")

    try:
        EventResponseModel.model_validate(event)
    except ValidationError as e:
        print(f"CRITICAL: Data integrity error for event ID '{id}'. {e}")
        raise ValueError(f"Malformed data found for event ID '{id}'.")
    
    return event

@tool_spec(
    spec={
        'name': 'update_event_by_id',
        'description': 'Update an existing event.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the event to update.'
                },
                'data': {
                    'type': 'object',
                    'description': 'A dictionary containing event data object containing the specific fields to be modified. Must include:',
                    'properties': {
                        'id': {
                            'type': 'integer',
                            'description': 'Must match the id parameter in the URL'
                        },
                        'type': {
                            'type': 'string',
                            'description': 'Event type enum ("RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT", "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT")'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Event attributes containing the following required fields:',
                            'properties': {
                                'title': {
                                    'type': 'string',
                                    'description': 'An event title'
                                },
                                'event_type': {
                                    'type': 'string',
                                    'description': 'Event type enum ("RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT", "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT")'
                                },
                                'spend_amount': {
                                    'type': 'number',
                                    'description': 'Actual spend amount used to calculate savings and keep reporting up to date'
                                },
                                'late_bids': {
                                    'type': 'boolean',
                                    'description': 'Whether late bid submissions are allowed'
                                },
                                'revise_bids': {
                                    'type': 'boolean',
                                    'description': 'Whether suppliers are allowed to re-submit bids'
                                },
                                'instant_notifications': {
                                    'type': 'boolean',
                                    'description': 'When true, notification emails are sent immediately; when false, notifications are delivered every 3 hours in a digest form'
                                },
                                'external_id': {
                                    'type': 'string',
                                    'description': 'Event ID in your internal database'
                                },
                                'restricted': {
                                    'type': 'boolean',
                                    'description': 'Whether event is invitation only even when posted on the public site'
                                },
                                'custom_fields': {
                                    'type': 'array',
                                    'description': 'Custom field values (note: custom fields of type File can only be accessed through the user interface, they will be exposed as null in the public API)',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                }
                            },
                            'required': [
                                'title',
                                'event_type',
                                'spend_amount',
                                'late_bids',
                                'revise_bids',
                                'instant_notifications',
                                'external_id',
                                'restricted'
                            ]
                        }
                    },
                    'required': [
                        'id',
                        'type',
                        'attributes'
                    ]
                }
            },
            'required': [
                'id',
                'data'
            ]
        }
    }
)
def patch(id: int, data: dict) -> Optional[Dict]:
    """
    Update an existing event.

    Args:
        id (int): The unique identifier of the event to update.
        data (dict): A dictionary containing event data object containing the specific fields to be modified. Must include:
            - id (int): Must match the id parameter in the URL
            - type (str): Event type enum ("RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT", "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT")
            - attributes (dict): Event attributes containing the following required fields:
                - title (str): An event title
                - event_type (str): Event type enum ("RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT", "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT")
                - spend_amount (float): Actual spend amount used to calculate savings and keep reporting up to date
                - late_bids (bool): Whether late bid submissions are allowed
                - revise_bids (bool): Whether suppliers are allowed to re-submit bids
                - instant_notifications (bool): When true, notification emails are sent immediately; when false, notifications are delivered every 3 hours in a digest form
                - external_id (str): Event ID in your internal database
                - restricted (bool): Whether event is invitation only even when posted on the public site
                - custom_fields (List[Dict[str, Any]], optional): Custom field values (note: custom fields of type File can only be accessed through the user interface, they will be exposed as null in the public API)

    Returns:
        Optional[Dict]: The updated event object if successful, None otherwise.
        The updated event object contains any of the following keys:
            - id (str): Event identifier string
            - name (str): Event name
            - type (str): Event type enum ("RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT", "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT")
            - duplication_state (str): Event duplication state enum ("scheduled", "started", "finished", "failed")
            - suppliers (list): List of suppliers
            - supplier_contacts (list): List of supplier contacts
            - attributes (dict): Event attributes containing:
                - title (str): An event title
                - event_type (str): Event type enum ("RFP", "AUCTION", "AUCTION_WITH_LOTS", "AUCTION_LOT", "PERFORMANCE_REVIEW_EVENT", "PERFORMANCE_REVIEW_SCORE_CARD_ONLY_EVENT", "SUPPLIER_REVIEW_EVENT", "SUPPLIER_REVIEW_MASTER_EVENT")
                - state (str): Current event state enum ("draft", "scheduled", "published", "live_editing", "closed", "canceled")
                - duplication_state (str): Event duplication state enum ("scheduled", "started", "finished", "failed")
                - spend_amount (float): Actual spend amount
                - request_type (str): Request type
                - late_bids (bool): Whether late bid submissions are allowed
                - revise_bids (bool): Whether suppliers can re-submit bids
                - instant_notifications (bool): Whether notifications are sent immediately
                - supplier_rsvp_deadline (str): RSVP deadline date-time
                - supplier_question_deadline (str): Questions deadline date-time
                - bid_submission_deadline (str): Bid submission deadline date-time
                - created_at (str): Creation date-time
                - closed_at (str): Closing date-time
                - published_at (str): Publication date-time
                - external_id (str): Event ID in internal database
                - is_public (bool): Whether event is accessible for self-registration
                - restricted (bool): Whether event is invitation only
                - custom_fields (list): Custom field values
            - relationships (dict): Event relationships containing:
                - attachments (list): List of attachments
                - project (dict): Associated project
                - spend_category (dict): Associated spend category
                - event_template (dict): Used event template
                - commodity_codes (list): List of commodity codes
            - links (dict): Related links containing:
                - self (str): URL to the resource
    Raises:
        TypeError: If 'id' is not an integer or 'data' is not a dictionary.
        ValueError: If 'data' contains an 'id' field that doesn't match the 'id' parameter.
        ValidationError: If the 'data' argument does not conform to the EventInputModel structure,
                                  including type errors or invalid enum values within the dictionary.
    """
    # Validate id is an integer
    if not isinstance(id, int):
        raise TypeError("Argument 'id' must be an integer.")
    
    # Validate data is a dictionary
    if not isinstance(data, dict):
        raise TypeError("Argument 'data' must be a dictionary.")
    
    # Validate that if data contains an id, it matches the function parameter id
    if "id" in data and data["id"] != id:
        raise ValueError("The 'id' in data must match the 'id' parameter.")
    
    # Create a clean copy of data without the id field for validation
    validation_data = {k: v for k, v in data.items() if k != 'id'}
    
    # Validate the structure of the data using Pydantic model
    try:
        # Using EventInputModel for validation since the patch fields are a subset of input fields
        validated_event_input = EventInputModel(**validation_data)
        validated_data_dict = validated_event_input.model_dump(exclude_none=True)
    except ValidationError as e:
        raise e
    
    # Check if event exists in the database
    # Convert integer ID to string for database lookup since IDs are stored as strings
    event_id = str(id)
    if event_id not in db.DB["events"]["events"]:
        return None
    
    # Update the event with validated data
    db.DB["events"]["events"][event_id].update(validated_data_dict)
    return db.DB["events"]["events"][event_id]

@tool_spec(
    spec={
        'name': 'delete_event_by_id',
        'description': 'Delete an event.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the event to delete.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete(id: int) -> bool:
    """
    Delete an event.

    Args:
        id (int): The unique identifier of the event to delete.

    Returns:
        bool: True if the event was successfully deleted.
        
    Raises:
        TypeError: If id is None or not an integer.
        ValueError: If id is not a positive integer.
        KeyError: If no event with the specified id exists.
    """
    # Type validation
    if id is None:
        raise TypeError("Event id cannot be None")
    if not isinstance(id, int):
        raise TypeError(f"Event id must be an integer, got {type(id).__name__}")
    
    # Value validation
    if id <= 0:
        raise ValueError(f"Event id must be a positive integer, got {id}")
    
    # Check existence
    # Convert integer ID to string for database lookup since IDs are stored as strings
    event_id = str(id)
    if event_id not in db.DB["events"]["events"]:
        raise KeyError(f"No event found with id {id}")
    
    # Delete the event
    del db.DB["events"]["events"][event_id]
    return True
