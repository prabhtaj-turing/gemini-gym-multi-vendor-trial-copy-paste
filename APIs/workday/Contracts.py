"""
Contract Management Module for Workday Strategic Sourcing API Simulation.

This module provides comprehensive functionality for managing contracts and contract types
in the Workday Strategic Sourcing system. It supports CRUD operations for both contracts
and contract types, with support for filtering, pagination, and relationship inclusion.
The module handles both internal IDs and external IDs for contract identification.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import List, Dict, Optional, Any
from .SimulationEngine import db
from .SimulationEngine.models import ContractPatchByExternalIdInputModel, ValidationError

from .SimulationEngine.models import ContractTypeUpdate, ContractFilterModel, ContractPageModel, \
  ContractTypeCreateModel, ContractTypeResponseModel, ContractInputModel, ExternalIdModel

from .SimulationEngine.custom_errors import ContractIDMismatchError, ContractNotFoundError, ContractValidationError
from .SimulationEngine.utils import add_included_relationships
from pydantic import ValidationError


@tool_spec(
    spec={
        'name': 'list_contracts',
        'description': """ Retrieve a list of contracts based on specified criteria.
        
        This function supports filtering, relationship inclusion, and pagination of contracts.
        Contracts can be filtered based on any attribute present in the contract object. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'filter': {
                    'type': 'object',
                    'description': 'Dictionary containing filter criteria for contracts. Contains any of the following keys:',
                    'properties': {
                        'updated_at_from': {
                            'type': 'string',
                            'description': 'Return contracts updated on or after timestamp'
                        },
                        'updated_at_to': {
                            'type': 'string',
                            'description': 'Return contracts updated on or before timestamp'
                        },
                        'number_from': {
                            'type': 'string',
                            'description': 'Find contracts with number >= specified'
                        },
                        'number_to': {
                            'type': 'string',
                            'description': 'Find contracts with number <= specified'
                        },
                        'title_contains': {
                            'type': 'string',
                            'description': 'Return contracts with title containing string'
                        },
                        'title_not_contains': {
                            'type': 'string',
                            'description': 'Return contracts with title not containing string'
                        },
                        'description_contains': {
                            'type': 'string',
                            'description': 'Return contracts with description containing string'
                        },
                        'description_not_contains': {
                            'type': 'string',
                            'description': 'Return contracts with description not containing string'
                        },
                        'external_id_empty': {
                            'type': 'boolean',
                            'description': 'Return contracts with blank external_id'
                        },
                        'external_id_not_empty': {
                            'type': 'boolean',
                            'description': 'Return contracts with non-blank external_id'
                        },
                        'external_id_equals': {
                            'type': 'string',
                            'description': 'Find contracts by specific external ID'
                        },
                        'external_id_not_equals': {
                            'type': 'string',
                            'description': 'Find contracts excluding specified external ID'
                        },
                        'actual_start_date_from': {
                            'type': 'string',
                            'description': 'Return contracts started on or after date'
                        },
                        'actual_start_date_to': {
                            'type': 'string',
                            'description': 'Return contracts started on or before date'
                        },
                        'actual_end_date_from': {
                            'type': 'string',
                            'description': 'Return contracts ended on or after date'
                        },
                        'actual_end_date_to': {
                            'type': 'string',
                            'description': 'Return contracts ended on or before date'
                        },
                        'actual_spend_amount_from': {
                            'type': 'number',
                            'description': 'Return contracts with spend >= amount'
                        },
                        'actual_spend_amount_to': {
                            'type': 'number',
                            'description': 'Return contracts with spend <= amount'
                        },
                        'auto_renewal': {
                            'type': 'array',
                            'description': 'Auto-renewal mode ("yes", "no", "evergreen")',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'needs_attention_equals': {
                            'type': 'boolean',
                            'description': 'Return contracts with specified needs attention status'
                        },
                        'needs_attention_not_equals': {
                            'type': 'boolean',
                            'description': 'Return contracts with needs attention status not equal'
                        },
                        'renew_number_of_times_from': {
                            'type': 'integer',
                            'description': 'Find contracts renewing >= specified times'
                        },
                        'renew_number_of_times_to': {
                            'type': 'integer',
                            'description': 'Find contracts renewing <= specified times'
                        },
                        'state_equals': {
                            'type': 'array',
                            'description': 'Find contracts with specified states',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'terminated_note_contains': {
                            'type': 'string',
                            'description': 'Return contracts with termination note containing string'
                        },
                        'terminated_note_not_contains': {
                            'type': 'string',
                            'description': 'Return contracts with termination note not containing string'
                        },
                        'terminated_note_empty': {
                            'type': 'string',
                            'description': 'Return contracts with empty termination note'
                        },
                        'terminated_note_not_empty': {
                            'type': 'string',
                            'description': 'Return contracts with non-empty termination note'
                        },
                        'terminated_reason_contains': {
                            'type': 'string',
                            'description': 'Return contracts with termination reason containing string'
                        },
                        'terminated_reason_not_contains': {
                            'type': 'string',
                            'description': 'Return contracts with termination reason not containing string'
                        },
                        'terminated_reason_empty': {
                            'type': 'string',
                            'description': 'Return contracts with empty termination reason'
                        },
                        'terminated_reason_not_empty': {
                            'type': 'string',
                            'description': 'Return contracts with non-empty termination reason'
                        },
                        'contract_type_id_equals': {
                            'type': 'integer',
                            'description': 'Find contracts with specified contract type'
                        },
                        'contract_type_id_not_equals': {
                            'type': 'integer',
                            'description': 'Find contracts with different contract type'
                        },
                        'marked_as_needs_attention_at_from': {
                            'type': 'string',
                            'description': 'Find contracts marked needs attention after date'
                        },
                        'marked_as_needs_attention_at_to': {
                            'type': 'string',
                            'description': 'Find contracts marked needs attention before date'
                        },
                        'needs_attention_note_contains': {
                            'type': 'string',
                            'description': 'Return contracts with needs attention note containing string'
                        },
                        'needs_attention_note_not_contains': {
                            'type': 'string',
                            'description': 'Return contracts with needs attention note not containing string'
                        },
                        'needs_attention_note_empty': {
                            'type': 'string',
                            'description': 'Return contracts with empty needs attention note'
                        },
                        'needs_attention_note_not_empty': {
                            'type': 'string',
                            'description': 'Return contracts with non-empty needs attention note'
                        },
                        'needs_attention_reason_contains': {
                            'type': 'string',
                            'description': 'Return contracts with needs attention reason containing string'
                        },
                        'needs_attention_reason_not_contains': {
                            'type': 'string',
                            'description': 'Return contracts with needs attention reason not containing string'
                        },
                        'needs_attention_reason_empty': {
                            'type': 'string',
                            'description': 'Return contracts with empty needs attention reason'
                        },
                        'needs_attention_reason_not_empty': {
                            'type': 'string',
                            'description': 'Return contracts with non-empty needs attention reason'
                        },
                        'renewal_termination_notice_date_from': {
                            'type': 'string',
                            'description': 'Find contracts with termination notice date >= specified'
                        },
                        'renewal_termination_notice_date_to': {
                            'type': 'string',
                            'description': 'Find contracts with termination notice date <= specified'
                        },
                        'renewal_termination_reminder_date_from': {
                            'type': 'string',
                            'description': 'Find contracts with termination reminder date >= specified'
                        },
                        'renewal_termination_reminder_date_to': {
                            'type': 'string',
                            'description': 'Find contracts with termination reminder date <= specified'
                        },
                        'spend_category_id_equals': {
                            'type': 'array',
                            'description': 'Find contracts using specified Spend Category IDs',
                            'items': {
                                'type': 'integer'
                            }
                        }
                    },
                    'required': []
                },
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated list of relationships to include in response.
                    Supported values: "contract_type", "spend_category", "supplier_company", 
                    "docusign_envelopes", "adobe_sign_agreements" """
                },
                'page': {
                    'type': 'object',
                    'description': 'Dictionary containing pagination parameters. Contains any of the following keys:',
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
def get(filter: Optional[Dict] = None, _include: Optional[str] = None, page: Optional[Dict] = None) -> List[Dict]:
    """
    Retrieve a list of contracts based on specified criteria.

    This function supports filtering, relationship inclusion, and pagination of contracts.
    Contracts can be filtered based on any attribute present in the contract object.

    Args:
        filter (Optional[Dict]): Dictionary containing filter criteria for contracts. Contains any of the following keys:
            - updated_at_from (Optional[str]): Return contracts updated on or after timestamp
            - updated_at_to (Optional[str]): Return contracts updated on or before timestamp
            - number_from (Optional[str]): Find contracts with number >= specified
            - number_to (Optional[str]): Find contracts with number <= specified
            - title_contains (Optional[str]): Return contracts with title containing string
            - title_not_contains (Optional[str]): Return contracts with title not containing string
            - description_contains (Optional[str]): Return contracts with description containing string
            - description_not_contains (Optional[str]): Return contracts with description not containing string
            - external_id_empty (Optional[bool]): Return contracts with blank external_id
            - external_id_not_empty (Optional[bool]): Return contracts with non-blank external_id
            - external_id_equals (Optional[str]): Find contracts by specific external ID
            - external_id_not_equals (Optional[str]): Find contracts excluding specified external ID
            - actual_start_date_from (Optional[str]): Return contracts started on or after date
            - actual_start_date_to (Optional[str]): Return contracts started on or before date
            - actual_end_date_from (Optional[str]): Return contracts ended on or after date
            - actual_end_date_to (Optional[str]): Return contracts ended on or before date
            - actual_spend_amount_from (Optional[float]): Return contracts with spend >= amount
            - actual_spend_amount_to (Optional[float]): Return contracts with spend <= amount
            - auto_renewal (Optional[List[str]]): Auto-renewal mode ("yes", "no", "evergreen")
            - needs_attention_equals (Optional[bool]): Return contracts with specified needs attention status
            - needs_attention_not_equals (Optional[bool]): Return contracts with needs attention status not equal
            - renew_number_of_times_from (Optional[int]): Find contracts renewing >= specified times
            - renew_number_of_times_to (Optional[int]): Find contracts renewing <= specified times
            - state_equals (Optional[List[str]]): Find contracts with specified states
            - terminated_note_contains (Optional[str]): Return contracts with termination note containing string
            - terminated_note_not_contains (Optional[str]): Return contracts with termination note not containing string
            - terminated_note_empty (Optional[str]): Return contracts with empty termination note
            - terminated_note_not_empty (Optional[str]): Return contracts with non-empty termination note
            - terminated_reason_contains (Optional[str]): Return contracts with termination reason containing string
            - terminated_reason_not_contains (Optional[str]): Return contracts with termination reason not containing string
            - terminated_reason_empty (Optional[str]): Return contracts with empty termination reason
            - terminated_reason_not_empty (Optional[str]): Return contracts with non-empty termination reason
            - contract_type_id_equals (Optional[int]): Find contracts with specified contract type
            - contract_type_id_not_equals (Optional[int]): Find contracts with different contract type
            - marked_as_needs_attention_at_from (Optional[str]): Find contracts marked needs attention after date
            - marked_as_needs_attention_at_to (Optional[str]): Find contracts marked needs attention before date
            - needs_attention_note_contains (Optional[str]): Return contracts with needs attention note containing string
            - needs_attention_note_not_contains (Optional[str]): Return contracts with needs attention note not containing string
            - needs_attention_note_empty (Optional[str]): Return contracts with empty needs attention note
            - needs_attention_note_not_empty (Optional[str]): Return contracts with non-empty needs attention note
            - needs_attention_reason_contains (Optional[str]): Return contracts with needs attention reason containing string
            - needs_attention_reason_not_contains (Optional[str]): Return contracts with needs attention reason not containing string
            - needs_attention_reason_empty (Optional[str]): Return contracts with empty needs attention reason
            - needs_attention_reason_not_empty (Optional[str]): Return contracts with non-empty needs attention reason
            - renewal_termination_notice_date_from (Optional[str]): Find contracts with termination notice date >= specified
            - renewal_termination_notice_date_to (Optional[str]): Find contracts with termination notice date <= specified
            - renewal_termination_reminder_date_from (Optional[str]): Find contracts with termination reminder date >= specified
            - renewal_termination_reminder_date_to (Optional[str]): Find contracts with termination reminder date <= specified
            - spend_category_id_equals (Optional[List[int]]): Find contracts using specified Spend Category IDs
        _include (Optional[str]): Comma-separated list of relationships to include in response.
            Supported values: "contract_type", "spend_category", "supplier_company", 
            "docusign_envelopes", "adobe_sign_agreements"
        page (Optional[Dict]): Dictionary containing pagination parameters. Contains any of the following keys:
            - size (Optional[int]): Number of results per page (default: 10, max: 100)

    Returns:
        List[Dict]: A list of contract dictionaries, where each contract contains any of the following keys:
            - type (str): Object type 
            - id (int): Contract identifier string
            - supplier_id (str): Supplier identifier
            - start_date (str): Contract start date
            - end_date (str): Contract end date
            - external_id (str): External contract identifier
            - attributes (dict): Contract attributes containing:
                - title (str): Contract title (max 255 characters)
                - description (str): Contract description
                - state (str): Current contract state ("draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated")
                - state_label (str): Customer-specific contract state label
                - number (int): Contract number, generated sequentially
                - external_id (str): Customer provided unique contract identifier
                - actual_start_date (str): Contract start date
                - actual_end_date (str): Contract end date
                - actual_spend_amount (float): Actual spend amount
                - auto_renewal (str): Auto-renewal mode ("yes", "no", "evergreen")
                - marked_as_needs_attention_at (str): Date and time when contract was flagged as needs attention
                - needs_attention (bool): Whether contract needs attention
                - needs_attention_note (str): Notes on why contract needs attention
                - needs_attention_reason (str): Reason why contract needs attention
                - renew_number_of_times (int): Number of times contract should be renewed
                - renewal_term_unit (str): Term unit for renewals ("days", "weeks", "months", "years")
                - renewal_term_value (int): Number of term units between renewals
                - renewal_termination_notice_date (str): Date for termination notice
                - renewal_termination_notice_unit (str): Term unit for termination notice
                - renewal_termination_notice_value (int): Term units before end date for notice
                - renewal_termination_reminder_date (str): Date for termination reminder
                - renewal_termination_reminder_unit (str): Term unit for termination reminder
                - renewal_termination_reminder_value (int): Term units before notice for reminder
                - terminated_note (str): Termination notes
                - terminated_reason (str): Termination reason
                - updated_at (str): Last modification date
                - custom_fields (list): Custom field values
                - approved_at (str): Date and time of contract approval
                - approval_rounds (int): Times contract has been sent for approval
                - first_sent_for_approval_at (str): First approval request date
                - sent_for_approval_at (str): Last approval request date
                - public (bool): Public visibility of contract
            - relationships (dict): Contract relationships containing:
                - attachments (list): Contract attachments
                - supplier_company (dict): Associated supplier company
                - creator (dict): Contract creator
                - owner (dict): Contract owner
                - docusign_envelopes (list): Docusign envelopes
                - adobe_sign_agreements (list): Adobe Sign agreements
                - contract_type (dict): Contract type
                - spend_category (dict): Spend category
            - links (dict): Related links containing:
                - self (str): URL to the resource

    Raises:
        ValueError: If any of the input parameters are invalid
        TypeError: If any of the input parameters have incorrect types
    """
    # Validate filter parameter with Pydantic
    if filter is not None:
        if not isinstance(filter, dict):
            raise TypeError("filter parameter must be a dictionary")
        try:
            validated_filter = ContractFilterModel(**filter)
            filter = validated_filter.model_dump(exclude_none=True)
        except Exception as e:
            raise ValueError(f"Invalid filter parameters: {str(e)}")

    if _include is not None:
        if not isinstance(_include, str) or not _include.strip():
            raise TypeError("_include parameter must be a string")

        valid_include_values = {'contract_type', 'spend_category', 'supplier_company', 'docusign_envelopes', 'adobe_sign_agreements'}
        include_relationships = [rel.strip() for rel in _include.split(',') if rel.strip()]
        
        for relationship in include_relationships:
            if relationship not in valid_include_values:
                raise ValueError(f"Invalid include relationship: {relationship}. Must be one of {valid_include_values}")

    # Validate page parameter with Pydantic
    if page is not None:
        if not isinstance(page, dict):
            raise TypeError("page parameter must be a dictionary")
        try:
            validated_page = ContractPageModel(**page)
            page = validated_page.model_dump(exclude_none=True)
        except Exception as e:
            raise ValueError(f"Invalid page parameters: {str(e)}")

    contracts = list(db.DB["contracts"]["contracts"].values())
    if filter:
        contracts = [c for c in contracts if all(c.get(k) == v for k, v in filter.items())]
    if _include:
        include_relationships = [rel.strip() for rel in _include.split(',') if rel.strip()]
        for contract in contracts:
            add_included_relationships(contract, include_relationships)
    
    # Apply pagination with default size of 10
    page_size = page.get("size", 10) if page else 10
    contracts = contracts[:page_size]
    return contracts

@tool_spec(
    spec={
        'name': 'create_contract',
        'description': 'Create a new contract with the specified attributes.',
        'parameters': {
            'type': 'object',
            'properties': {
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated list of relationships to include
                    in the response. 
                    Supported values: "contract_type", "spend_category", "supplier_company", "docusign_envelopes", "adobe_sign_agreements" """
                },
                'body': {
                    'type': 'object',
                    'description': "Dictionary containing contract creation data. Required keys are 'type', 'attributes', and 'relationships'. Optional keys include:",
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Object type'
                        },
                        'supplier_id': {
                            'type': 'string',
                            'description': 'Supplier identifier'
                        },
                        'start_date': {
                            'type': 'string',
                            'description': 'Contract start date'
                        },
                        'end_date': {
                            'type': 'string',
                            'description': 'Contract end date'
                        },
                        'external_id': {
                            'type': 'string',
                            'description': 'External contract identifier'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Contract attributes containing:',
                            'properties': {
                                'title': {
                                    'type': 'string',
                                    'description': 'Contract title (max 255 characters)'
                                },
                                'description': {
                                    'type': 'string',
                                    'description': 'Contract description'
                                },
                                'state': {
                                    'type': 'string',
                                    'description': 'Current contract state, one of ["draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated"].'
                                },
                                'state_label': {
                                    'type': 'string',
                                    'description': 'Customer-specific contract state label'
                                },
                                'external_id': {
                                    'type': 'string',
                                    'description': 'Customer provided unique contract identifier'
                                },
                                'actual_start_date': {
                                    'type': 'string',
                                    'description': 'Contract start date'
                                },
                                'actual_end_date': {
                                    'type': 'string',
                                    'description': 'Contract end date'
                                },
                                'actual_spend_amount': {
                                    'type': 'number',
                                    'description': 'Actual spend amount'
                                },
                                'auto_renewal': {
                                    'type': 'string',
                                    'description': 'Auto-renewal mode, one of ["yes", "no", "evergreen"].'
                                },
                                'marked_as_needs_attention_at': {
                                    'type': 'string',
                                    'description': 'Date when contract was flagged as needs attention'
                                },
                                'needs_attention': {
                                    'type': 'boolean',
                                    'description': 'Whether contract needs attention'
                                },
                                'needs_attention_note': {
                                    'type': 'string',
                                    'description': 'Notes on why contract needs attention'
                                },
                                'needs_attention_reason': {
                                    'type': 'string',
                                    'description': 'Reason why contract needs attention'
                                },
                                'renew_number_of_times': {
                                    'type': 'integer',
                                    'description': 'Number of times contract should be renewed'
                                },
                                'renewal_term_unit': {
                                    'type': 'string',
                                    'description': 'Term unit for renewals, one of ["days", "weeks", "months", "years"].'
                                },
                                'renewal_term_value': {
                                    'type': 'integer',
                                    'description': 'Number of term units between renewals'
                                },
                                'renewal_termination_notice_unit': {
                                    'type': 'string',
                                    'description': 'Term unit for termination notice'
                                },
                                'renewal_termination_notice_value': {
                                    'type': 'integer',
                                    'description': 'Term units before end date for notice'
                                },
                                'renewal_termination_reminder_unit': {
                                    'type': 'string',
                                    'description': 'Term unit for termination reminder'
                                },
                                'renewal_termination_reminder_value': {
                                    'type': 'integer',
                                    'description': 'Term units before notice for reminder'
                                },
                                'terminated_note': {
                                    'type': 'string',
                                    'description': 'Termination notes'
                                },
                                'terminated_reason': {
                                    'type': 'string',
                                    'description': 'Termination reason'
                                },
                                'custom_fields': {
                                    'type': 'array',
                                    'description': "A list of user-defined fields for this contract, where each dictionary contains the field's identifier and value",
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                },
                                'approval_rounds': {
                                    'type': 'integer',
                                    'description': 'Times contract has been sent for approval'
                                },
                                'public': {
                                    'type': 'boolean',
                                    'description': 'Public visibility of contract'
                                }
                            },
                            'required': [
                                'title',
                                'state'
                            ]
                        },
                        'relationships': {
                            'type': 'object',
                            'description': 'Contract relationships containing:',
                            'properties': {
                                'owner': {
                                    'type': 'object',
                                    'description': 'Contract owner with:',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Owner identifier'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'supplier_company': {
                                    'type': 'object',
                                    'description': 'Associated supplier company with:',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Always "supplier_companies"'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Supplier company identifier'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'contract_type': {
                                    'type': 'object',
                                    'description': 'Contract type with:',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Always "contract_types"'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Contract type identifier'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'spend_category': {
                                    'type': 'object',
                                    'description': 'Spend category with:',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Always "spend_categories"'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Spend category identifier'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'payment_currency': {
                                    'type': 'object',
                                    'description': 'Payment currency with:',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Always "payment_currencies"'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Payment currency identifier'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                }
                            },
                            'required': [
                                'owner',
                                'supplier_company',
                                'contract_type'
                            ]
                        }
                    },
                    'required': [
                        'type',
                        'attributes',
                        'relationships'
                    ]
                }
            },
            'required': []
        }
    }
)
def post(_include: Optional[str] = None, body: Optional[Dict] = None) -> Dict:
    """
    Create a new contract with the specified attributes.

    Args:
        _include (Optional[str]): Comma-separated list of relationships to include
            in the response. 
            Supported values: "contract_type", "spend_category", "supplier_company", "docusign_envelopes", "adobe_sign_agreements"
        body (Optional[Dict]): Dictionary containing contract creation data. Required keys are 'type', 'attributes', and 'relationships'. Optional keys include:
            - type (str): Object type 
            - supplier_id (Optional[str]): Supplier identifier
            - start_date (Optional[str]): Contract start date
            - end_date (Optional[str]): Contract end date
            - external_id (Optional[str]): External contract identifier
            - attributes (dict): Contract attributes containing:
                - title (str): Contract title (max 255 characters)
                - description (Optional[str]): Contract description
                - state (str): Current contract state, one of ["draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated"].
                - state_label (Optional[str]): Customer-specific contract state label
                - external_id (Optional[str]): Customer provided unique contract identifier
                - actual_start_date (Optional[str]): Contract start date
                - actual_end_date (Optional[str]): Contract end date
                - actual_spend_amount (Optional[float]): Actual spend amount
                - auto_renewal (Optional[str]): Auto-renewal mode, one of ["yes", "no", "evergreen"].
                - marked_as_needs_attention_at (Optional[str]): Date when contract was flagged as needs attention
                - needs_attention (Optional[bool]): Whether contract needs attention
                - needs_attention_note (Optional[str]): Notes on why contract needs attention
                - needs_attention_reason (Optional[str]): Reason why contract needs attention
                - renew_number_of_times (Optional[int]): Number of times contract should be renewed
                - renewal_term_unit (Optional[str]): Term unit for renewals, one of ["days", "weeks", "months", "years"].
                - renewal_term_value (Optional[int]): Number of term units between renewals
                - renewal_termination_notice_unit (Optional[str]): Term unit for termination notice
                - renewal_termination_notice_value (Optional[int]): Term units before end date for notice
                - renewal_termination_reminder_unit (Optional[str]): Term unit for termination reminder
                - renewal_termination_reminder_value (Optional[int]): Term units before notice for reminder
                - terminated_note (Optional[str]): Termination notes
                - terminated_reason (Optional[str]): Termination reason
                - custom_fields (Optional[List[Dict[str, Any]]]): A list of user-defined fields for this contract, where each dictionary contains the field's identifier and value
                - approval_rounds (Optional[int]): Times contract has been sent for approval
                - public (Optional[bool]): Public visibility of contract
            - relationships (dict): Contract relationships containing:
                - owner (dict): Contract owner with:
                    - type (str): Object type
                    - id (int): Owner identifier
                - supplier_company (dict): Associated supplier company with:
                    - type (str): Always "supplier_companies"
                    - id (int): Supplier company identifier
                - contract_type (dict): Contract type with:
                    - type (str): Always "contract_types"
                    - id (int): Contract type identifier
                - spend_category (Optional[dict]): Spend category with:
                    - type (str): Always "spend_categories"
                    - id (int): Spend category identifier
                - payment_currency (Optional[dict]): Payment currency with:
                    - type (str): Always "payment_currencies"
                    - id (int): Payment currency identifier

    Returns:
        Dict: The newly created contract object with any of the following keys:
            - type (str): Object type 
            - id (int): Contract identifier string
            - supplier_id (str): Supplier identifier
            - start_date (str): Contract start date
            - end_date (str): Contract end date
            - external_id (str): External contract identifier
            - attributes (dict): Contract attributes containing:
                - title (str): Contract title (max 255 characters)
                - description (str): Contract description
                - state (str): Current contract state ("draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated")
                - state_label (str): Customer-specific contract state label
                - number (int): Contract number, generated sequentially
                - external_id (str): Customer provided unique contract identifier
                - actual_start_date (str): Contract start date
                - actual_end_date (str): Contract end date
                - actual_spend_amount (float): Actual spend amount
                - auto_renewal (str): Auto-renewal mode ("yes", "no", "evergreen")
                - marked_as_needs_attention_at (str): Date and time when contract was flagged as needs attention
                - needs_attention (bool): Whether contract needs attention
                - needs_attention_note (str): Notes on why contract needs attention
                - needs_attention_reason (str): Reason why contract needs attention
                - renew_number_of_times (int): Number of times contract should be renewed
                - renewal_term_unit (str): Term unit for renewals ("days", "weeks", "months", "years")
                - renewal_term_value (int): Number of term units between renewals
                - renewal_termination_notice_date (str): Date for termination notice
                - renewal_termination_notice_unit (str): Term unit for termination notice
                - renewal_termination_notice_value (int): Term units before end date for notice
                - renewal_termination_reminder_date (str): Date for termination reminder
                - renewal_termination_reminder_unit (str): Term unit for termination reminder
                - renewal_termination_reminder_value (int): Term units before notice for reminder
                - terminated_note (str): Termination notes
                - terminated_reason (str): Termination reason
                - updated_at (str): Last modification date
                - custom_fields (list): Custom field values
                - approved_at (str): Date and time of contract approval
                - approval_rounds (int): Times contract has been sent for approval
                - first_sent_for_approval_at (str): First approval request date
                - sent_for_approval_at (str): Last approval request date
                - public (bool): Public visibility of contract
            - relationships (dict): Contract relationships containing:
                - attachments (list): Contract attachments
                - supplier_company (dict): Associated supplier company
                - creator (dict): Contract creator
                - owner (dict): Contract owner
                - docusign_envelopes (list): Docusign envelopes
                - adobe_sign_agreements (list): Adobe Sign agreements
                - contract_type (dict): Contract type
                - spend_category (dict): Spend category
            - links (dict): Related links containing:
                - self (str): URL to the resource

    Raises:
        ValueError: If the body is not provided or validation fails.
        ContractInputModel: If the body does not conform to the expected schema.
    """
    if not body:
        raise ValueError("Body must be provided.")
    
    if _include is not None:
        if not isinstance(_include, str):
            raise ValueError("_include must be a string.")
    
    # Validate the input using Pydantic model
    try:
        validated_body = ContractInputModel(**body)
        body_dict = validated_body.model_dump()
    except Exception as e:
        raise ValueError(f"Validation failed: {str(e)}")
    
    contract_id = len(db.DB.get("contracts", {}).get("contracts", {})) + 1
    while contract_id in db.DB.get("contracts", {}).get("contracts", {}).keys():
        contract_id += 1
    body_dict["id"] = contract_id
    if _include:
        include_relationships = [rel.strip() for rel in _include.split(',') if rel.strip()]
        add_included_relationships(body_dict, include_relationships)
    db.DB["contracts"]["contracts"][contract_id] = body_dict
    return body_dict

@tool_spec(
    spec={
        'name': 'get_contract_by_id',
        'description': 'Retrieve details of a specific contract by its internal ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The internal identifier of the contract to retrieve.'
                },
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated list of relationships to include
                    in the response. 
                    Supported values: "contract_type", "spend_category", "supplier_company", "docusign_envelopes", "adobe_sign_agreements" """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_contract_by_id(id: int, _include: Optional[str] = None) -> Dict:
    """
    Retrieve details of a specific contract by its internal ID.

    Args:
        id (int): The internal identifier of the contract to retrieve.
        _include (Optional[str]): Comma-separated list of relationships to include
            in the response. 
            Supported values: "contract_type", "spend_category", "supplier_company", "docusign_envelopes", "adobe_sign_agreements"

    Returns:
        Dict: The contract object. Contains any of the following keys:
            - type (str): Object type 
            - id (int): Contract identifier string
            - supplier_id (str): Supplier identifier
            - start_date (str): Contract start date
            - end_date (str): Contract end date
            - external_id (str): External contract identifier
            - attributes (dict): Contract attributes containing:
                - title (str): Contract title (max 255 characters)
                - description (str): Contract description
                - state (str): Current contract state ("draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated")
                - state_label (str): Customer-specific contract state label
                - number (int): Contract number, generated sequentially
                - external_id (str): Customer provided unique contract identifier
                - actual_start_date (str): Contract start date
                - actual_end_date (str): Contract end date
                - actual_spend_amount (float): Actual spend amount
                - auto_renewal (str): Auto-renewal mode ("yes", "no", "evergreen")
                - marked_as_needs_attention_at (str): Date and time when contract was flagged as needs attention
                - needs_attention (bool): Whether contract needs attention
                - needs_attention_note (str): Notes on why contract needs attention
                - needs_attention_reason (str): Reason why contract needs attention
                - renew_number_of_times (int): Number of times contract should be renewed
                - renewal_term_unit (str): Term unit for renewals ("days", "weeks", "months", "years")
                - renewal_term_value (int): Number of term units between renewals
                - renewal_termination_notice_date (str): Date for termination notice
                - renewal_termination_notice_unit (str): Term unit for termination notice
                - renewal_termination_notice_value (int): Term units before end date for notice
                - renewal_termination_reminder_date (str): Date for termination reminder
                - renewal_termination_reminder_unit (str): Term unit for termination reminder
                - renewal_termination_reminder_value (int): Term units before notice for reminder
                - terminated_note (str): Termination notes
                - terminated_reason (str): Termination reason
                - updated_at (str): Last modification date
                - custom_fields (list): Custom field values
                - approved_at (str): Date and time of contract approval
                - approval_rounds (int): Times contract has been sent for approval
                - first_sent_for_approval_at (str): First approval request date
                - sent_for_approval_at (str): Last approval request date
                - public (bool): Public visibility of contract
            - relationships (dict): Contract relationships containing:
                - attachments (list): Contract attachments
                - supplier_company (dict): Associated supplier company
                - creator (dict): Contract creator
                - owner (dict): Contract owner
                - docusign_envelopes (list): Docusign envelopes
                - adobe_sign_agreements (list): Adobe Sign agreements
                - contract_type (dict): Contract type
                - spend_category (dict): Spend category
            - links (dict): Related links containing:
                - self (str): URL to the resource

    Raises:
        KeyError: If no contract exists with the specified ID.
    """
    if not isinstance(id, int) or id <= 0:
        raise TypeError("id parameter must be a positive integer")
    if _include is not None:
        if not isinstance(_include, str) or not _include.strip():
            raise TypeError("_include parameter must be a string")

        valid_include_values = ['contract_type', 'spend_category', 'supplier_company', 'docusign_envelopes',
                                'adobe_sign_agreements']
        include_relationships = [rel.strip() for rel in _include.split(',') if rel.strip()]

        for relationship in include_relationships:
            if relationship not in valid_include_values:
                raise ValueError(f"Invalid include relationship: {relationship}. Must be one of {valid_include_values}")

    if id not in db.DB["contracts"]["contracts"]:
        raise KeyError(f"Contract with id {id} not found.")

    contract = db.DB["contracts"]["contracts"][id]
    if _include:
        include_relationships = [rel.strip() for rel in _include.split(',') if rel.strip()]
        add_included_relationships(contract, include_relationships)

    return contract

@tool_spec(
    spec={
        'name': 'update_contract_by_id',
        'description': 'Update an existing contract by its internal ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The internal identifier of the contract to update.'
                },
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated list of relationships to include
                    in the response.
                    Supported values: "contract_type", "spend_category", "supplier_company", "docusign_envelopes", "adobe_sign_agreements" """
                },
                'body': {
                    'type': 'object',
                    'description': 'Dictionary containing the fields to update. Includes any of the following keys:',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Object type'
                        },
                        'id': {
                            'type': 'integer',
                            'description': 'Contract identifier string'
                        },
                        'supplier_id': {
                            'type': 'string',
                            'description': 'Supplier identifier'
                        },
                        'start_date': {
                            'type': 'string',
                            'description': 'Contract start date'
                        },
                        'end_date': {
                            'type': 'string',
                            'description': 'Contract end date'
                        },
                        'external_id': {
                            'type': 'string',
                            'description': 'External contract identifier'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Contract attributes containing:',
                            'properties': {
                                'title': {
                                    'type': 'string',
                                    'description': 'Contract title (max 255 characters)'
                                },
                                'description': {
                                    'type': 'string',
                                    'description': 'Contract description'
                                },
                                'state': {
                                    'type': 'string',
                                    'description': 'Current contract state ("draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated")'
                                },
                                'state_label': {
                                    'type': 'string',
                                    'description': 'Customer-specific contract state label'
                                },
                                'number': {
                                    'type': 'integer',
                                    'description': 'Contract number, generated sequentially'
                                },
                                'external_id': {
                                    'type': 'string',
                                    'description': 'Customer provided unique contract identifier'
                                },
                                'actual_start_date': {
                                    'type': 'string',
                                    'description': 'Contract start date'
                                },
                                'actual_end_date': {
                                    'type': 'string',
                                    'description': 'Contract end date'
                                },
                                'actual_spend_amount': {
                                    'type': 'number',
                                    'description': 'Actual spend amount'
                                },
                                'auto_renewal': {
                                    'type': 'string',
                                    'description': 'Auto-renewal mode ("yes", "no", "evergreen")'
                                },
                                'marked_as_needs_attention_at': {
                                    'type': 'string',
                                    'description': 'Date and time when contract was flagged as needs attention'
                                },
                                'needs_attention': {
                                    'type': 'boolean',
                                    'description': 'Whether contract needs attention'
                                },
                                'needs_attention_note': {
                                    'type': 'string',
                                    'description': 'Notes on why contract needs attention'
                                },
                                'needs_attention_reason': {
                                    'type': 'string',
                                    'description': 'Reason why contract needs attention'
                                },
                                'renew_number_of_times': {
                                    'type': 'integer',
                                    'description': 'Number of times contract should be renewed'
                                },
                                'renewal_term_unit': {
                                    'type': 'string',
                                    'description': 'Term unit for renewals ("days", "weeks", "months", "years")'
                                },
                                'renewal_term_value': {
                                    'type': 'integer',
                                    'description': 'Number of term units between renewals'
                                },
                                'renewal_termination_notice_date': {
                                    'type': 'string',
                                    'description': 'Date for termination notice'
                                },
                                'renewal_termination_notice_unit': {
                                    'type': 'string',
                                    'description': 'Term unit for termination notice'
                                },
                                'renewal_termination_notice_value': {
                                    'type': 'integer',
                                    'description': 'Term units before end date for notice'
                                },
                                'renewal_termination_reminder_date': {
                                    'type': 'string',
                                    'description': 'Date for termination reminder'
                                },
                                'renewal_termination_reminder_unit': {
                                    'type': 'string',
                                    'description': 'Term unit for termination reminder'
                                },
                                'renewal_termination_reminder_value': {
                                    'type': 'integer',
                                    'description': 'Term units before notice for reminder'
                                },
                                'terminated_note': {
                                    'type': 'string',
                                    'description': 'Termination notes'
                                },
                                'terminated_reason': {
                                    'type': 'string',
                                    'description': 'Termination reason'
                                },
                                'updated_at': {
                                    'type': 'string',
                                    'description': 'Last modification date'
                                },
                                'custom_fields': {
                                    'type': 'array',
                                    'description': 'Custom field values',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                },
                                'approved_at': {
                                    'type': 'string',
                                    'description': 'Date and time of contract approval'
                                },
                                'approval_rounds': {
                                    'type': 'integer',
                                    'description': 'Times contract has been sent for approval'
                                },
                                'first_sent_for_approval_at': {
                                    'type': 'string',
                                    'description': 'First approval request date'
                                },
                                'sent_for_approval_at': {
                                    'type': 'string',
                                    'description': 'Last approval request date'
                                },
                                'public': {
                                    'type': 'boolean',
                                    'description': 'Public visibility of contract'
                                }
                            },
                            'required': []
                        },
                        'relationships': {
                            'type': 'object',
                            'description': 'Contract relationships containing:',
                            'properties': {
                                'attachments': {
                                    'type': 'array',
                                    'description': 'Contract attachments',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                },
                                'supplier_company': {
                                    'type': 'object',
                                    'description': 'Associated supplier company',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "supplier_companies".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Supplier company identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'owner': {
                                    'type': 'object',
                                    'description': 'Contract owner',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "stakeholders".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Stakeholder identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'docusign_envelopes': {
                                    'type': 'array',
                                    'description': 'Docusign envelopes',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                },
                                'adobe_sign_agreements': {
                                    'type': 'array',
                                    'description': 'Adobe Sign agreements',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                },
                                'contract_type': {
                                    'type': 'object',
                                    'description': 'Contract type',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "contract_types".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Contract type identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'spend_category': {
                                    'type': 'object',
                                    'description': 'Spend category',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "spend_categories".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Spend category identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                }
                            },
                            'required': []
                        }
                    },
                    'required': [
                        'type',
                        'id'
                    ]
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def patch_contract_by_id(id: int, _include: Optional[str] = None, body: Optional[Dict] = None) -> Dict:
    """
    Update an existing contract by its internal ID.

    Args:
        id (int): The internal identifier of the contract to update.
        _include (Optional[str]): Comma-separated list of relationships to include
            in the response.
            Supported values: "contract_type", "spend_category", "supplier_company", "docusign_envelopes", "adobe_sign_agreements"
        body (Optional[Dict]): Dictionary containing the fields to update. Includes any of the following keys:
            - type (str): Object type 
            - id (int): Contract identifier string
            - supplier_id (Optional[str]): Supplier identifier
            - start_date (Optional[str]): Contract start date
            - end_date (Optional[str]): Contract end date
            - external_id (Optional[str]): External contract identifier
            - attributes (Optional[dict]): Contract attributes containing:
                - title (Optional[str]): Contract title (max 255 characters)
                - description (Optional[str]): Contract description
                - state (Optional[str]): Current contract state ("draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated")
                - state_label (Optional[str]): Customer-specific contract state label
                - number (Optional[int]): Contract number, generated sequentially
                - external_id (Optional[str]): Customer provided unique contract identifier
                - actual_start_date (Optional[str]): Contract start date
                - actual_end_date (Optional[str]): Contract end date
                - actual_spend_amount (Optional[float]): Actual spend amount
                - auto_renewal (Optional[str]): Auto-renewal mode ("yes", "no", "evergreen")
                - marked_as_needs_attention_at (Optional[str]): Date and time when contract was flagged as needs attention
                - needs_attention (Optional[bool]): Whether contract needs attention
                - needs_attention_note (Optional[str]): Notes on why contract needs attention
                - needs_attention_reason (Optional[str]): Reason why contract needs attention
                - renew_number_of_times (Optional[int]): Number of times contract should be renewed
                - renewal_term_unit (Optional[str]): Term unit for renewals ("days", "weeks", "months", "years")
                - renewal_term_value (Optional[int]): Number of term units between renewals
                - renewal_termination_notice_date (Optional[str]): Date for termination notice
                - renewal_termination_notice_unit (Optional[str]): Term unit for termination notice
                - renewal_termination_notice_value (Optional[int]): Term units before end date for notice
                - renewal_termination_reminder_date (Optional[str]): Date for termination reminder
                - renewal_termination_reminder_unit (Optional[str]): Term unit for termination reminder
                - renewal_termination_reminder_value (Optional[int]): Term units before notice for reminder
                - terminated_note (Optional[str]): Termination notes
                - terminated_reason (Optional[str]): Termination reason
                - updated_at (Optional[str]): Last modification date
                - custom_fields (Optional[List[Dict[str, Any]]]): Custom field values
                - approved_at (Optional[str]): Date and time of contract approval
                - approval_rounds (Optional[int]): Times contract has been sent for approval
                - first_sent_for_approval_at (Optional[str]): First approval request date
                - sent_for_approval_at (Optional[str]): Last approval request date
                - public (Optional[bool]): Public visibility of contract
            - relationships (Optional[dict]): Contract relationships containing:
                - attachments (Optional[List[Dict[str, Any]]]): Contract attachments
                - supplier_company (Optional[dict]): Associated supplier company
                    - type (str): Object type, should always be "supplier_companies".
                    - id (int): Supplier company identifier string.
                - owner (Optional[dict]): Contract owner
                    - type (str): Object type, should always be "stakeholders".
                    - id (int): Stakeholder identifier string.
                - docusign_envelopes (Optional[List[Dict[str, Any]]]): Docusign envelopes
                - adobe_sign_agreements (Optional[List[Dict[str, Any]]]): Adobe Sign agreements
                - contract_type (Optional[dict]): Contract type
                    - type (str): Object type, should always be "contract_types".
                    - id (int): Contract type identifier string.
                - spend_category (Optional[dict]): Spend category
                    - type (str): Object type, should always be "spend_categories".
                    - id (int): Spend category identifier string.

    Returns:
        Dict: The updated contract object. Contains any of the following keys:
            - type (str): Object type 
            - id (int): Contract identifier string
            - supplier_id (str): Supplier identifier
            - start_date (str): Contract start date
            - end_date (str): Contract end date
            - external_id (str): External contract identifier
            - attributes (dict): Contract attributes containing:
                - title (str): Contract title (max 255 characters)
                - description (str): Contract description
                - state (str): Current contract state ("draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated")
                - state_label (str): Customer-specific contract state label
                - number (int): Contract number, generated sequentially
                - external_id (str): Customer provided unique contract identifier
                - actual_start_date (str): Contract start date
                - actual_end_date (str): Contract end date
                - actual_spend_amount (float): Actual spend amount
                - auto_renewal (str): Auto-renewal mode ("yes", "no", "evergreen")
                - marked_as_needs_attention_at (str): Date and time when contract was flagged as needs attention
                - needs_attention (bool): Whether contract needs attention
                - needs_attention_note (str): Notes on why contract needs attention
                - needs_attention_reason (str): Reason why contract needs attention
                - renew_number_of_times (int): Number of times contract should be renewed
                - renewal_term_unit (str): Term unit for renewals ("days", "weeks", "months", "years")
                - renewal_term_value (int): Number of term units between renewals
                - renewal_termination_notice_date (str): Date for termination notice
                - renewal_termination_notice_unit (str): Term unit for termination notice
                - renewal_termination_notice_value (int): Term units before end date for notice
                - renewal_termination_reminder_date (str): Date for termination reminder
                - renewal_termination_reminder_unit (str): Term unit for termination reminder
                - renewal_termination_reminder_value (int): Term units before notice for reminder
                - terminated_note (str): Termination notes
                - terminated_reason (str): Termination reason
                - updated_at (str): Last modification date
                - custom_fields (list): Custom field values
                - approved_at (str): Date and time of contract approval
                - approval_rounds (int): Times contract has been sent for approval
                - first_sent_for_approval_at (str): First approval request date
                - sent_for_approval_at (str): Last approval request date
                - public (bool): Public visibility of contract
            - relationships (dict): Contract relationships containing:
                - attachments (list): Contract attachments
                - supplier_company (dict): Associated supplier company
                    - type (str): Object type, should always be "supplier_companies".
                    - id (int): Supplier company identifier string.
                - creator (dict): Contract creator
                    - type (str): Object type, should always be "stakeholders".
                    - id (int): Stakeholder identifier string.
                - owner (dict): Contract owner
                    - type (str): Object type, should always be "stakeholders".
                    - id (int): Stakeholder identifier string.
                - docusign_envelopes (list): Docusign envelopes
                - adobe_sign_agreements (list): Adobe Sign agreements
                - contract_type (dict): Contract type
                    - type (str): Object type, should always be "contract_types".
                    - id (int): Contract type identifier string.
                - spend_category (dict): Spend category
                    - type (str): Object type, should always be "spend_categories".
                    - id (int): Spend category identifier string.
            - links (dict): Related links containing:
                - self (str): URL to the resource

    Raises:
        ContractNotFoundError: If no contract exists with the specified ID.
        ContractValidationError: If the body is None or empty.
        ContractIDMismatchError: If the body does not contain the correct 'id'.
    """

    # Check if contract exists
    if id not in db.DB["contracts"]["contracts"]:
        raise ContractNotFoundError(f"Contract with id {id} not found.")
    
    # Validate body parameter
    if body is None:
        raise ContractValidationError("Request body cannot be None.")
    
    if not isinstance(body, dict):
        raise ContractValidationError("Request body must be a dictionary.")
    
    if not body:
        raise ContractValidationError("Request body cannot be empty.")
    
    # Validate ID mismatch
    if body.get("id") != id:
        raise ContractIDMismatchError("Body must contain the correct 'id'.")
    
    # Update the contract
    db.DB["contracts"]["contracts"][id].update(body)
    return db.DB["contracts"]["contracts"][id]

@tool_spec(
    spec={
        'name': 'delete_contract_by_id',
        'description': 'Delete a contract by its internal ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The internal identifier of the contract to delete.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete_contract_by_id(id: int) -> None:
    """
    Delete a contract by its internal ID.

    Args:
        id (int): The internal identifier of the contract to delete.

    Raises:
        KeyError: If no contract exists with the specified ID.
    """

    # adding input validation
    if not isinstance(id, int):
        raise ValueError("id must be an integer")
    if id <= 0:
        raise ValueError("id must be a positive integer")
    
    
    if id not in db.DB["contracts"]["contracts"]:
        raise KeyError(f"Contract with id {id} not found.")
    del db.DB["contracts"]["contracts"][id]

@tool_spec(
    spec={
        'name': 'get_contract_by_external_id',
        'description': 'Retrieve details of a specific contract by its external ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier of the contract to retrieve.'
                },
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated list of relationships to include
                    in the response.
                    Supported values: "contract_type", "spend_category", "supplier_company", "docusign_envelopes", "adobe_sign_agreements" """
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def get_contract_by_external_id(external_id: str, _include: Optional[str] = None) -> Dict:
    """
    Retrieve details of a specific contract by its external ID.

    Args:
        external_id (str): The external identifier of the contract to retrieve.
        _include (Optional[str]): Comma-separated list of relationships to include
            in the response.
            Supported values: "contract_type", "spend_category", "supplier_company", "docusign_envelopes", "adobe_sign_agreements"
    Returns:
        Dict: The contract object.
        Contains any of the following keys:
            - type (str): Object type 
            - id (int): Contract identifier string
            - supplier_id (str): Supplier identifier
            - start_date (str): Contract start date
            - end_date (str): Contract end date
            - external_id (str): External contract identifier
            - attributes (dict): Contract attributes containing:
                - title (str): Contract title (max 255 characters)
                - description (str): Contract description
                - state (str): Current contract state ("draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated")
                - state_label (str): Customer-specific contract state label
                - number (int): Contract number, generated sequentially
                - external_id (str): Customer provided unique contract identifier
                - actual_start_date (str): Contract start date
                - actual_end_date (str): Contract end date
                - actual_spend_amount (float): Actual spend amount
                - auto_renewal (str): Auto-renewal mode ("yes", "no", "evergreen")
                - marked_as_needs_attention_at (str): Date and time when contract was flagged as needs attention
                - needs_attention (bool): Whether contract needs attention
                - needs_attention_note (str): Notes on why contract needs attention
                - needs_attention_reason (str): Reason why contract needs attention
                - renew_number_of_times (int): Number of times contract should be renewed
                - renewal_term_unit (str): Term unit for renewals ("days", "weeks", "months", "years")
                - renewal_term_value (int): Number of term units between renewals
                - renewal_termination_notice_date (str): Date for termination notice
                - renewal_termination_notice_unit (str): Term unit for termination notice
                - renewal_termination_notice_value (int): Term units before end date for notice
                - renewal_termination_reminder_date (str): Date for termination reminder
                - renewal_termination_reminder_unit (str): Term unit for termination reminder
                - renewal_termination_reminder_value (int): Term units before notice for reminder
                - terminated_note (str): Termination notes
                - terminated_reason (str): Termination reason
                - updated_at (str): Last modification date
                - custom_fields (list): Custom field values
                - approved_at (str): Date and time of contract approval
                - approval_rounds (int): Times contract has been sent for approval
                - first_sent_for_approval_at (str): First approval request date
                - sent_for_approval_at (str): Last approval request date
                - public (bool): Public visibility of contract
            - relationships (dict): Contract relationships containing:
                - attachments (list): Contract attachments
                - supplier_company (dict): Associated supplier company
                - creator (dict): Contract creator
                - owner (dict): Contract owner
                - docusign_envelopes (list): Docusign envelopes
                - adobe_sign_agreements (list): Adobe Sign agreements
                - contract_type (dict): Contract type
                - spend_category (dict): Spend category
            - links (dict): Related links containing:
                - self (str): URL to the resource

    Raises:
        ValueError: If external_id is None, empty, or not a string.
        ValueError: If _include contains invalid relationship values.
        KeyError: If no contract exists with the specified external ID.
    """
    if not isinstance(external_id, str):
        raise ValueError("external_id must be a string")
    
    if not external_id.strip():
        raise ValueError("external_id cannot be empty or contain only whitespace")

    if _include is not None:
        if not isinstance(_include, str):
            raise ValueError("_include must be a string")
        
        valid_include_values = ["contract_type", "spend_category", "supplier_company", "docusign_envelopes", "adobe_sign_agreements"]
        include_values = [value.strip() for value in _include.split(",") if value.strip()]
        
        for value in include_values:
            if value not in valid_include_values:
                raise ValueError(f"Invalid _include value: '{value}'. Valid values are: {', '.join(sorted(valid_include_values))}")

    for contract in db.DB["contracts"]["contracts"].values():
        if contract.get("external_id") == external_id:
            if _include:
                add_included_relationships(contract, include_values)
            return contract
    
    raise KeyError(f"Contract with external_id {external_id} not found.")

@tool_spec(
    spec={
        'name': 'update_contract_by_external_id',
        'description': 'Update an existing contract by its external ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier of the contract to update.'
                },
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated list of relationships to include
                    in the response.
                    Supported values: "contract_type", "spend_category", "supplier_company", "docusign_envelopes", "adobe_sign_agreements" """
                },
                'body': {
                    'type': 'object',
                    'description': """ A dictionary representing the contract patch payload, containing the specific fields of the contract to be modified. Must include:
                    Can contain any of the following keys: """,
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Object type'
                        },
                        'id': {
                            'type': 'integer',
                            'description': 'Contract identifier string'
                        },
                        'supplier_id': {
                            'type': 'string',
                            'description': 'Supplier identifier'
                        },
                        'start_date': {
                            'type': 'string',
                            'description': 'Contract start date'
                        },
                        'end_date': {
                            'type': 'string',
                            'description': 'Contract end date'
                        },
                        'external_id': {
                            'type': 'string',
                            'description': 'External contract identifier'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Contract attributes containing:',
                            'properties': {
                                'title': {
                                    'type': 'string',
                                    'description': 'Contract title (max 255 characters)'
                                },
                                'description': {
                                    'type': 'string',
                                    'description': 'Contract description'
                                },
                                'state': {
                                    'type': 'string',
                                    'description': 'Current contract state ("draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated")'
                                },
                                'state_label': {
                                    'type': 'string',
                                    'description': 'Customer-specific contract state label'
                                },
                                'number': {
                                    'type': 'integer',
                                    'description': 'Contract number, generated sequentially'
                                },
                                'external_id': {
                                    'type': 'string',
                                    'description': 'Customer provided unique contract identifier'
                                },
                                'actual_start_date': {
                                    'type': 'string',
                                    'description': 'Contract start date'
                                },
                                'actual_end_date': {
                                    'type': 'string',
                                    'description': 'Contract end date'
                                },
                                'actual_spend_amount': {
                                    'type': 'number',
                                    'description': 'Actual spend amount'
                                },
                                'auto_renewal': {
                                    'type': 'string',
                                    'description': 'Auto-renewal mode ("yes", "no", "evergreen")'
                                },
                                'marked_as_needs_attention_at': {
                                    'type': 'string',
                                    'description': 'Date and time when contract was flagged as needs attention'
                                },
                                'needs_attention': {
                                    'type': 'boolean',
                                    'description': 'Whether contract needs attention'
                                },
                                'needs_attention_note': {
                                    'type': 'string',
                                    'description': 'Notes on why contract needs attention'
                                },
                                'needs_attention_reason': {
                                    'type': 'string',
                                    'description': 'Reason why contract needs attention'
                                },
                                'renew_number_of_times': {
                                    'type': 'integer',
                                    'description': 'Number of times contract should be renewed'
                                },
                                'renewal_term_unit': {
                                    'type': 'string',
                                    'description': 'Term unit for renewals ("days", "weeks", "months", "years")'
                                },
                                'renewal_term_value': {
                                    'type': 'integer',
                                    'description': 'Number of term units between renewals'
                                },
                                'renewal_termination_notice_date': {
                                    'type': 'string',
                                    'description': 'Date for termination notice'
                                },
                                'renewal_termination_notice_unit': {
                                    'type': 'string',
                                    'description': 'Term unit for termination notice'
                                },
                                'renewal_termination_notice_value': {
                                    'type': 'integer',
                                    'description': 'Term units before end date for notice'
                                },
                                'renewal_termination_reminder_date': {
                                    'type': 'string',
                                    'description': 'Date for termination reminder'
                                },
                                'renewal_termination_reminder_unit': {
                                    'type': 'string',
                                    'description': 'Term unit for termination reminder'
                                },
                                'renewal_termination_reminder_value': {
                                    'type': 'integer',
                                    'description': 'Term units before notice for reminder'
                                },
                                'terminated_note': {
                                    'type': 'string',
                                    'description': 'Termination notes'
                                },
                                'terminated_reason': {
                                    'type': 'string',
                                    'description': 'Termination reason'
                                },
                                'updated_at': {
                                    'type': 'string',
                                    'description': 'Last modification date'
                                },
                                'custom_fields': {
                                    'type': 'array',
                                    'description': 'Custom field values',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                },
                                'approved_at': {
                                    'type': 'string',
                                    'description': 'Date and time of contract approval'
                                },
                                'approval_rounds': {
                                    'type': 'integer',
                                    'description': 'Times contract has been sent for approval'
                                },
                                'first_sent_for_approval_at': {
                                    'type': 'string',
                                    'description': 'First approval request date'
                                },
                                'sent_for_approval_at': {
                                    'type': 'string',
                                    'description': 'Last approval request date'
                                },
                                'public': {
                                    'type': 'boolean',
                                    'description': 'Public visibility of contract'
                                }
                            },
                            'required': []
                        },
                        'relationships': {
                            'type': 'object',
                            'description': 'Contract relationships containing:',
                            'properties': {
                                'attachments': {
                                    'type': 'array',
                                    'description': 'Contract attachments',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                },
                                'supplier_company': {
                                    'type': 'object',
                                    'description': 'Associated supplier company',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "supplier_companies".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Supplier company identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'creator': {
                                    'type': 'object',
                                    'description': 'Contract creator',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "stakeholders".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Stakeholder identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'owner': {
                                    'type': 'object',
                                    'description': 'Contract owner',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "stakeholders".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Stakeholder identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'docusign_envelopes': {
                                    'type': 'array',
                                    'description': 'Docusign envelopes',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                },
                                'adobe_sign_agreements': {
                                    'type': 'array',
                                    'description': 'Adobe Sign agreements',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                },
                                'contract_type': {
                                    'type': 'object',
                                    'description': 'Contract type',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "contract_types".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Contract type identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'spend_category': {
                                    'type': 'object',
                                    'description': 'Spend category',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "spend_categories".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Spend category identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                }
                            },
                            'required': []
                        }
                    },
                    'required': [
                        'type',
                        'id'
                    ]
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def patch_contract_by_external_id(external_id: str, _include: Optional[str] = None, body: Optional[Dict] = None) -> Dict:
    """
    Update an existing contract by its external ID.

    Args:
        external_id (str): The external identifier of the contract to update.
        _include (Optional[str]): Comma-separated list of relationships to include
            in the response.
            Supported values: "contract_type", "spend_category", "supplier_company", "docusign_envelopes", "adobe_sign_agreements"
        body (Optional[Dict]): A dictionary representing the contract patch payload, containing the specific fields of the contract to be modified. Must include:
            - type (str): Object type 
            - id (int): Contract identifier string
            Can contain any of the following keys:
            - supplier_id (Optional[str]): Supplier identifier
            - start_date (Optional[str]): Contract start date
            - end_date (Optional[str]): Contract end date
            - external_id (Optional[str]): External contract identifier
            - attributes (Optional[dict]): Contract attributes containing:
                - title (Optional[str]): Contract title (max 255 characters)
                - description (Optional[str]): Contract description
                - state (Optional[str]): Current contract state ("draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated")
                - state_label (Optional[str]): Customer-specific contract state label
                - number (Optional[int]): Contract number, generated sequentially
                - external_id (Optional[str]): Customer provided unique contract identifier
                - actual_start_date (Optional[str]): Contract start date
                - actual_end_date (Optional[str]): Contract end date
                - actual_spend_amount (Optional[float]): Actual spend amount
                - auto_renewal (Optional[str]): Auto-renewal mode ("yes", "no", "evergreen")
                - marked_as_needs_attention_at (Optional[str]): Date and time when contract was flagged as needs attention
                - needs_attention (Optional[bool]): Whether contract needs attention
                - needs_attention_note (Optional[str]): Notes on why contract needs attention
                - needs_attention_reason (Optional[str]): Reason why contract needs attention
                - renew_number_of_times (Optional[int]): Number of times contract should be renewed
                - renewal_term_unit (Optional[str]): Term unit for renewals ("days", "weeks", "months", "years")
                - renewal_term_value (Optional[int]): Number of term units between renewals
                - renewal_termination_notice_date (Optional[str]): Date for termination notice
                - renewal_termination_notice_unit (Optional[str]): Term unit for termination notice
                - renewal_termination_notice_value (Optional[int]): Term units before end date for notice
                - renewal_termination_reminder_date (Optional[str]): Date for termination reminder
                - renewal_termination_reminder_unit (Optional[str]): Term unit for termination reminder
                - renewal_termination_reminder_value (Optional[int]): Term units before notice for reminder
                - terminated_note (Optional[str]): Termination notes
                - terminated_reason (Optional[str]): Termination reason
                - updated_at (Optional[str]): Last modification date
                - custom_fields (Optional[List[Dict[str, Any]]]): Custom field values
                - approved_at (Optional[str]): Date and time of contract approval
                - approval_rounds (Optional[int]): Times contract has been sent for approval
                - first_sent_for_approval_at (Optional[str]): First approval request date
                - sent_for_approval_at (Optional[str]): Last approval request date
                - public (Optional[bool]): Public visibility of contract
            - relationships (Optional[dict]): Contract relationships containing:
                - attachments (Optional[List[Dict[str, Any]]]): Contract attachments
                - supplier_company (Optional[dict]): Associated supplier company
                    - type (str): Object type, should always be "supplier_companies".
                    - id (int): Supplier company identifier string.
                - creator (Optional[dict]): Contract creator
                    - type (str): Object type, should always be "stakeholders".
                    - id (int): Stakeholder identifier string.
                - owner (Optional[dict]): Contract owner
                    - type (str): Object type, should always be "stakeholders".
                    - id (int): Stakeholder identifier string.
                - docusign_envelopes (Optional[List[Dict[str, Any]]]): Docusign envelopes
                - adobe_sign_agreements (Optional[List[Dict[str, Any]]]): Adobe Sign agreements
                - contract_type (Optional[dict]): Contract type
                    - type (str): Object type, should always be "contract_types".
                    - id (int): Contract type identifier string.
                - spend_category (Optional[dict]): Spend category
                    - type (str): Object type, should always be "spend_categories".
                    - id (int): Spend category identifier string.
    Returns:
        Dict: The updated contract object. Contains any of the following keys:
            - type (str): Object type 
            - id (int): Contract identifier string
            - supplier_id (str): Supplier identifier
            - start_date (str): Contract start date
            - end_date (str): Contract end date
            - external_id (str): External contract identifier
            - attributes (dict): Contract attributes containing:
                - title (str): Contract title (max 255 characters)
                - description (str): Contract description
                - state (str): Current contract state ("draft", "requested", "in_progress", "out_for_approval", "approved", "active", "expired", "terminated")
                - state_label (str): Customer-specific contract state label
                - number (int): Contract number, generated sequentially
                - external_id (str): Customer provided unique contract identifier
                - actual_start_date (str): Contract start date
                - actual_end_date (str): Contract end date
                - actual_spend_amount (float): Actual spend amount
                - auto_renewal (str): Auto-renewal mode ("yes", "no", "evergreen")
                - marked_as_needs_attention_at (str): Date and time when contract was flagged as needs attention
                - needs_attention (bool): Whether contract needs attention
                - needs_attention_note (str): Notes on why contract needs attention
                - needs_attention_reason (str): Reason why contract needs attention
                - renew_number_of_times (int): Number of times contract should be renewed
                - renewal_term_unit (str): Term unit for renewals ("days", "weeks", "months", "years")
                - renewal_term_value (int): Number of term units between renewals
                - renewal_termination_notice_date (str): Date for termination notice
                - renewal_termination_notice_unit (str): Term unit for termination notice
                - renewal_termination_notice_value (int): Term units before end date for notice
                - renewal_termination_reminder_date (str): Date for termination reminder
                - renewal_termination_reminder_unit (str): Term unit for termination reminder
                - renewal_termination_reminder_value (int): Term units before notice for reminder
                - terminated_note (str): Termination notes
                - terminated_reason (str): Termination reason
                - updated_at (str): Last modification date
                - custom_fields (list): Custom field values
                - approved_at (str): Date and time of contract approval
                - approval_rounds (int): Times contract has been sent for approval
                - first_sent_for_approval_at (str): First approval request date
                - sent_for_approval_at (str): Last approval request date
                - public (bool): Public visibility of contract
            - relationships (dict): Contract relationships containing:
                - attachments (list): Contract attachments
                - supplier_company (dict): Associated supplier company
                    - type (str): Object type, should always be "supplier_companies".
                    - id (int): Supplier company identifier string.
                - creator (dict): Contract creator
                    - type (str): Object type, should always be "stakeholders".
                    - id (int): Stakeholder identifier string.
                - owner (dict): Contract owner
                    - type (str): Object type, should always be "stakeholders".
                    - id (int): Stakeholder identifier string.
                - docusign_envelopes (list): Docusign envelopes
                - adobe_sign_agreements (list): Adobe Sign agreements
                - contract_type (dict): Contract type
                    - type (str): Object type, should always be "contract_types".
                    - id (int): Contract type identifier string.
                - spend_category (dict): Spend category
                    - type (str): Object type, should always be "spend_categories".
                    - id (int): Spend category identifier string.
            - links (dict): Related links containing:
                - self (str): URL to the resource

    Raises:
        KeyError: If no contract exists with the specified external ID.
        ValueError: If the body does not contain the correct 'external_id'.
        ValidationError: If the input data fails Pydantic validation.
    """
    # Input validation
    if not isinstance(external_id, str) or not external_id.strip():
        raise TypeError("external_id must be a string.")

    if _include is not None:
        if not isinstance(_include, str) or not _include.strip():
            raise TypeError("_include must be a string.")
        _include = _include.split(",")

    if body is not None:
        try:
            validated_body = ContractPatchByExternalIdInputModel(**body)
        except ValidationError as e:
            raise ValueError(f"Validation error: {e}")

    contract = None
    for c in db.DB["contracts"]["contracts"].values():
        if c.get("external_id") == external_id:
            contract = c
            break
    
    if not contract:
        raise KeyError(f"Contract with external_id {external_id} not found.")
    
    if body:
        contract.update(validated_body.model_dump(exclude_none=True))
    
    return contract

@tool_spec(
    spec={
        'name': 'delete_contract_by_external_id',
        'description': """ Delete a contract by its external ID.
        
        This function removes a contract from the database using its external identifier.
        The function performs comprehensive validation of the external_id parameter and
        ensures the contract exists before attempting deletion. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': """ The external identifier of the contract to delete.
                    Must be a non-empty string containing only alphanumeric characters,
                    hyphens, and underscores. Maximum length of 255 characters. """
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def delete_contract_by_external_id(external_id: str) -> bool:
    """
    Delete a contract by its external ID.

    This function removes a contract from the database using its external identifier.
    The function performs comprehensive validation of the external_id parameter and
    ensures the contract exists before attempting deletion.

    Args:
        external_id (str): The external identifier of the contract to delete.
            Must be a non-empty string containing only alphanumeric characters,
            hyphens, and underscores. Maximum length of 255 characters.

    Returns:
        bool: True if the contract was successfully deleted.

    Raises:
        ValueError: If external_id is None, empty, or contains invalid characters.
        TypeError: If external_id is not a string.
        KeyError: If no contract exists with the specified external ID.
    """
    # Validate external_id parameter
    try:
        validated_external_id = ExternalIdModel(external_id=external_id)
        external_id = validated_external_id.external_id
    except ValidationError as e:
        raise ValueError(f"Invalid external_id format: {str(e)}")
    
    # Find and delete the contract
    contract_id = None
    for id, contract in db.DB["contracts"]["contracts"].items():
        if contract.get("external_id") == external_id:
            contract_id = id
            break
    
    if contract_id is None:
        raise KeyError(f"Contract with external_id {external_id} not found.")
    
    del db.DB["contracts"]["contracts"][contract_id]
    return True

@tool_spec(
    spec={
        'name': 'get_contract_fields_description',
        'description': 'Retrieve a list of all available fields for the contract object.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_contracts_description() -> List[str]:
    """
    Retrieve a list of all available fields for the contract object.

    Returns:
        List[str]: A list of field names that can be present in a contract object.
    """
    all_fields = set()
    if db.DB["contracts"]["contracts"]:
        for contract in db.DB["contracts"]["contracts"].values():
            all_fields.update(contract.keys())
        return list(all_fields)
    return []

@tool_spec(
    spec={
        'name': 'list_contract_types',
        'description': 'Retrieve a list of all available contract types.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_contract_types() -> List[Dict]:
    """
    Retrieve a list of all available contract types.

    Returns:
        List[Dict]: A list of contract type dictionaries, where each contains:
            - type (str): Object type, should always be "contract_types"
            - id (int): Contract type identifier
            - name (str): Name of the contract type
            - external_id (str): External contract type identifier
            - links (dict): Dictionary of related links containing:
                - self (str): Normalized link to the resource
    """
    return list(db.DB["contracts"]["contract_types"].values())

@tool_spec(
    spec={
        'name': 'create_contract_type',
        'description': 'Create a new contract type.',
        'parameters': {
            'type': 'object',
            'properties': {
                'body': {
                    'type': 'object',
                    'description': 'Dictionary containing contract type creation data. Can contain any of the following keys:',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "contract_types"'
                        },
                        'name': {
                            'type': 'string',
                            'description': 'Name of the contract type'
                        },
                        'external_id': {
                            'type': 'string',
                            'description': 'External contract type identifier'
                        }
                    },
                    'required': []
                }
            },
            'required': []
        }
    }
)
def post_contract_types(body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a new contract type.

    Args:
        body (Optional[Dict[str, Any]]): Dictionary containing contract type creation data. Can contain any of the following keys:
            - type (Optional[str]): Object type, should always be "contract_types"
            - name (Optional[str]): Name of the contract type
            - external_id (Optional[str]): External contract type identifier

    Returns:
        Dict[str, Any]: A dictionary representing the complete, newly created
            contract type. It will contain:
            - id (int): The newly generated contract type identifier.
            - type (str): Object type, always "contract_types".
            - name (str): Name of the contract type.
            - external_id (str): External contract type identifier, if provided.

    Raises:
        ValidationError: Raised by Pydantic if the input `body` dictionary
            does not conform to the structure or validation rules defined in
            the `ContractTypeCreateModel`.
    """
    try:
        # 1. VALIDATE: Pydantic parses the raw dictionary.
        # If 'body' doesn't match the model, it raises a ValidationError.
        validated_input = ContractTypeCreateModel(**body)

        # 2. GENERATE ID: This logic remains the same.
        contract_types = db.DB.get("contracts", {}).get("contract_types", {})
        new_id = max(contract_types.keys()) + 1 if contract_types else 1

        # 3. CREATE RESPONSE OBJECT: Combine the new ID with the validated data.
        response_data = ContractTypeResponseModel(id=new_id, **validated_input.model_dump())

        # 4. STORE: Save the validated data (as a dictionary) to the database.
        db.DB.setdefault("contracts", {}).setdefault("contract_types", {})[new_id] = response_data.model_dump()

        # 5. RETURN: Return the final, complete object as a dictionary.
        return response_data.model_dump()

    except ValidationError as e:
        # If validation fails, re-raise the detailed error from Pydantic.
        # This provides clear feedback on what went wrong.
        raise e

@tool_spec(
    spec={
        'name': 'get_contract_type_by_id',
        'description': 'Retrieve details of a specific contract type by its internal ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The internal identifier of the contract type to retrieve.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get_contract_type_by_id(id: int) -> Dict:
    """
    Retrieve details of a specific contract type by its internal ID.

    Args:
        id (int): The internal identifier of the contract type to retrieve.

    Returns:
        Dict: The contract type object. Contains any of the following keys:
            - type (str): Object type, should always be "contract_types"
            - id (int): Contract type identifier
            - name (str): Name of the contract type
            - external_id (str): External contract type identifier

    Raises:
        KeyError: If no contract type exists with the specified ID.
        TypeError: If id is not an integer.
        ValueError: If id is None.
    """
    if id is None:
        raise ValueError("Contract type id cannot be None.")
    if not isinstance(id, int):
        raise TypeError(f"Contract type id must be an integer, got {type(id).__name__} instead.")
    if id not in db.DB["contracts"]["contract_types"]:
        raise KeyError(f"Contract type with id {id} not found.")
    return db.DB["contracts"]["contract_types"][id]

@tool_spec(
    spec={
        'name': 'update_contract_type_by_id',
        'description': 'Update an existing contract type by its internal ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The internal identifier of the contract type to update.'
                },
                'body': {
                    'type': 'object',
                    'description': """ A dictionary representing the contract type attributes to be updated. Must include:
                    Can contain any of the following keys: """,
                    'properties': {
                        'id': {
                            'type': 'integer',
                            'description': 'Must match the id parameter in the URL'
                        },
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "contract_types"'
                        },
                        'name': {
                            'type': 'string',
                            'description': 'Name of the contract type'
                        },
                        'external_id': {
                            'type': 'string',
                            'description': 'External contract type identifier'
                        }
                    },
                    'required': [
                        'id',
                        'type'
                    ]
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def patch_contract_type_by_id(id: int, body: Optional[Dict] = None) -> Dict:
    """
    Update an existing contract type by its internal ID. 

    Args:
        id (int): The internal identifier of the contract type to update.
        body (Optional[Dict]): A dictionary representing the contract type attributes to be updated. Must include:
            - id (int): Must match the id parameter in the URL
            - type (str): Object type, should always be "contract_types"
            Can contain any of the following keys:
            - name (Optional[str]): Name of the contract type
            - external_id (Optional[str]): External contract type identifier

    Returns:
        Dict: The updated contract type object. Contains any of the following keys:
            - type (str): Object type, should always be "contract_types"
            - id (int): Contract type identifier string
            - name (str): Name of the contract type
            - external_id (str): External contract type identifier

    Raises:
        KeyError: If no contract type exists with the specified ID.
        ValueError: If the body does not contain the correct 'id' or has invalid data.
    """
    if id not in db.DB["contracts"]["contract_types"]:
        raise KeyError(f"Contract type with id {id} not found.")
    
    if not body:
        raise ValueError("Body must be provided")
        
    # Check for required fields before Pydantic validation
    if "type" not in body:
        raise ValueError("Body must include 'type' field with value 'contract_types'")
    
    if body.get("type") != "contract_types":
        raise ValueError("The 'type' field must be 'contract_types'")
        
    # Validate the body using Pydantic
    try:
        validated_body = ContractTypeUpdate(**body)
        if validated_body.id != id:
            raise ValueError("Body must contain the correct 'id'")
    except Exception as e:
        raise ValueError(f"Invalid contract type data: {str(e)}")
    
    # Update only with validated data
    update_data = validated_body.model_dump(exclude_unset=True)
    db.DB["contracts"]["contract_types"][id].update(update_data)
    
    return db.DB["contracts"]["contract_types"][id]

@tool_spec(
    spec={
        'name': 'delete_contract_type_by_id',
        'description': 'Delete a contract type by its internal ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'The internal identifier of the contract type to delete.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete_contract_type_by_id(id: int) -> None:
    """
    Delete a contract type by its internal ID.

    Args:
        id (int): The internal identifier of the contract type to delete.

    Raises:
        TypeError: If the provided id is not an integer.
        ValueError: If the provided id is not a positive integer.
        KeyError: If no contract type exists with the specified ID.
    """
    if not isinstance(id, int):
        raise TypeError(f"Contract type id must be an integer, got {type(id).__name__}")
    
    if id <= 0:
        raise ValueError(f"Contract type id must be a positive integer, got {id}")
    
    if id not in db.DB["contracts"]["contract_types"]:
        raise KeyError(f"Contract type with id {id} not found.")
    del db.DB["contracts"]["contract_types"][id]

@tool_spec(
    spec={
        'name': 'get_contract_type_by_external_id',
        'description': 'Retrieve details of a specific contract type by its external ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier of the contract type to retrieve.'
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def get_contract_type_by_external_id(external_id: str) -> Dict:
    """
    Retrieve details of a specific contract type by its external ID.

    Args:
        external_id (str): The external identifier of the contract type to retrieve.

    Returns:
        Dict: The contract type object. Contains any of the following keys:
            - type (str): Object type, should always be "contract_types"
            - id (int): Contract type identifier
            - name (str): Name of the contract type
            - external_id (str): External contract type identifier

    Raises:
        KeyError: If no contract type exists with the specified external ID.
        TypeError: If external_id is not a string.
        ValueError: If external_id is empty or has an invalid format.
    """
    # Type validation
    if not isinstance(external_id, str):
        raise TypeError(f"external_id must be a string, got {type(external_id).__name__}")
    
    # Empty/None validation
    if not external_id:
        raise ValueError("external_id cannot be empty")
    
    # Format validation - assuming external_id should be alphanumeric with underscores
    if not all(c.isalnum() or c == '_' for c in external_id):
        raise ValueError("external_id must contain only alphanumeric characters and underscores")
    
    for contract_type in db.DB["contracts"]["contract_types"].values():
        if contract_type.get("external_id") == external_id:
            return contract_type
    raise KeyError(f"Contract type with external_id {external_id} not found.")

@tool_spec(
    spec={
        'name': 'update_contract_type_by_external_id',
        'description': 'Update an existing contract type by its external ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier of the contract type to update.'
                },
                'body': {
                    'type': 'object',
                    'description': """ Dictionary containing the fields to update. Must include:
                    Can contain any of the following keys: """,
                    'properties': {
                        'external_id': {
                            'type': 'string',
                            'description': 'Must match the external_id parameter in the URL'
                        },
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "contract_types"'
                        },
                        'name': {
                            'type': 'string',
                            'description': 'Name of the contract type'
                        }
                    },
                    'required': [
                        'external_id',
                        'type'
                    ]
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def patch_contract_type_by_external_id(external_id: str, body: Optional[Dict] = None) -> Dict:
    """
    Update an existing contract type by its external ID.

    Args:
        external_id (str): The external identifier of the contract type to update.
        body (Optional[Dict]): Dictionary containing the fields to update. Must include:
            - external_id (str): Must match the external_id parameter in the URL
            - type (str): Object type, should always be "contract_types"
            Can contain any of the following keys:
            - name (Optional[str]): Name of the contract type

    Returns:
        Dict: The updated contract type object. Contains any of the following keys:
            - type (str): Object type, should always be "contract_types"
            - id (int): Contract type identifier
            - name (str): Name of the contract type
            - external_id (str): External contract type identifier

    Raises:
        KeyError: If no contract type exists with the specified external ID.
        ValueError: If the body does not contain the correct 'external_id'.
    """
    # Validate external_id parameter
    if not external_id or not isinstance(external_id, str):
        raise ValueError("external_id must be a non-empty string")
    
    # Find the contract type
    contract_type = None
    for c in db.DB["contracts"]["contract_types"].values():
        if c.get("external_id") == external_id:
            contract_type = c
            break
    if not contract_type:
        raise KeyError(f"Contract type with external_id {external_id} not found.")
    
    # Validate body
    if not body:
        raise ValueError("Body must be provided")
    
    # Validate required fields in body
    if body.get("external_id") != external_id:
        raise ValueError("Body must contain the correct 'external_id'")
    
    if "type" not in body:
        raise ValueError("Body must contain 'type' field")
    
    if body.get("type") != "contract_types":
        raise ValueError("Body 'type' field must be 'contract_types'")
    
    # Validate types of optional fields if present
    if "name" in body and not isinstance(body["name"], str):
        raise ValueError("Field 'name' must be a string")
    
    # Update the contract type
    contract_type.update(body)
    return contract_type

@tool_spec(
    spec={
        'name': 'delete_contract_type_by_external_id',
        'description': 'Delete a contract type by its external ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external identifier of the contract type to delete.'
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def delete_contract_type_by_external_id(external_id: str) -> None:
    """
    Delete a contract type by its external ID.

    Args:
        external_id (str): The external identifier of the contract type to delete.

    Raises:
        KeyError: If no contract type exists with the specified external ID.
        ValueError: If external_id is None, empty, or not a string.
        
    Returns:
        None
    """
    # Validate input
    if external_id is None or not isinstance(external_id, str):
        raise ValueError("external_id must be a string")
    if not external_id.strip():
        raise ValueError("external_id cannot be empty")
        
    contract_type_id = None
    for id, contract_type in db.DB["contracts"]["contract_types"].items():
        if contract_type.get("external_id") == external_id:
            contract_type_id = id
            break
    if contract_type_id is None:
        raise KeyError(f"Contract type with external_id {external_id} not found.")
    del db.DB["contracts"]["contract_types"][contract_type_id] 
