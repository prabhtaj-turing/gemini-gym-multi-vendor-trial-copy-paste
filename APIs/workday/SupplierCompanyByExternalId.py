"""
Supplier Company Management by External ID Module

This module provides functionality for managing supplier companies using their external
identifiers in the Workday Strategic Sourcing system. It supports operations for
retrieving, updating, and deleting supplier company records using external IDs.

The module interfaces with the simulation database to provide comprehensive supplier
company management capabilities, particularly useful when integrating with external
systems that maintain their own identifiers. It allows users to:
- Retrieve detailed supplier company information using external IDs
- Update existing supplier company records with external ID validation
- Delete supplier company entries by external ID
- Handle related resource inclusion where applicable

Functions:
    get: Retrieves supplier company details by external ID
    patch: Updates supplier company details by external ID
    delete: Deletes a supplier company by external ID
"""
from common_utils.tool_spec_decorator import tool_spec

from typing import Dict, Any, List, Optional, Tuple, Union, Set

# Standard library imports
import re

# Third-party imports
from pydantic import ValidationError as PydanticValidationError

# Internal imports
from .SimulationEngine import db
from .SimulationEngine import custom_errors
from .SimulationEngine.models import SupplierCompanyUpdateModel

@tool_spec(
    spec={
        'name': 'get_supplier_company_by_external_id',
        'description': """ Retrieves a supplier company using its external identifier.
        
        This endpoint fetches the details of a supplier company by its unique external ID. Related resources can be included using the `include` query parameter. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'Required. The external identifier of the supplier company. Example: "1234-5678-abcd-efgh"'
                },
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated string of related resources to include in the response. 
                    Enum values:
                    - "attachments"
                    - "supplier_category"
                    - "supplier_groups"
                    - "default_payment_term"
                    - "payment_types"
                    - "default_payment_type"
                    - "payment_currencies"
                    - "default_payment_currency"
                    - "supplier_classification_values" """
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def get(external_id: str, _include: Optional[str] = None) -> Tuple[Union[Dict[str, Any], Dict[str, str]], int]:
    """
    Retrieves a supplier company using its external identifier.

    This endpoint fetches the details of a supplier company by its unique external ID. Related resources can be included using the `include` query parameter.

    Args:
        external_id (str): Required. The external identifier of the supplier company. Example: "1234-5678-abcd-efgh"
        _include (Optional[str]): Comma-separated string of related resources to include in the response. 
            Enum values:
            - "attachments"
            - "supplier_category"
            - "supplier_groups"
            - "default_payment_term"
            - "payment_types"
            - "default_payment_type"
            - "payment_currencies"
            - "default_payment_currency"
            - "supplier_classification_values"

    Returns:
        Tuple[Union[Dict[str, Any], Dict[str, str]], int]: A tuple containing the supplier company details or an error message and the HTTP status code.
            If successful:
                - First element (Dict[str, Any]):
                    - type (str): Resource object type, always "supplier_companies".
                    - id (int): Internal identifier of the supplier company.
                    - attributes (Dict[str, Any]): Supplier company metadata.
                        - name (str): Company name.
                        - description (str): Optional company description.
                        - is_suggested (bool): True if suggested by a user but not approved.
                        - public (bool): Indicates if the company is public.
                        - risk (str): Supplier risk (slug from risk object).
                        - segmentation (str): Supplier segmentation (slug from segmentation object).
                        - segmentation_status (str): Segmentation status (slug from segmentation status object).
                        - segmentation_notes (str): Notes related to segmentation.
                        - tags (List[str]): List of user-defined tags.
                        - url (str): Supplier’s website URL.
                        - duns_number (str): D-U-N-S® Number.
                        - external_id (str): External system identifier.
                        - self_registered (bool): True if registered via self-service.
                        - onboarding_form_completion_status (str): Status of onboarding form. Values: null, 'not_started', 'in_progress', 'completed'.
                        - accept_all_currencies (bool): True if all currencies are accepted.
                        - updated_at (str): Last updated timestamp (ISO format).
                        - custom_fields (List[Dict[str, Any]]): List of custom fields.
                            Each field has:
                                - name (str): Field name.
                                - value (Any): Field value depending on type.
                            Supported types:
                                - Checkbox
                                - Short Text
                                - Paragraph
                                - Date
                                - Integer
                                - Currency
                                - Decimal
                                - Single Select
                                - Multiple Select
                                - URL
                                - Lookup
                                - Related
                            Note: File-type custom fields are only accessible via UI and return `null`.

                    - relationships (Dict[str, Any]): Linked resources.
                        - supplier_category (Dict): Assigned category.
                            - data:
                                - type (str): Always "supplier_categories".
                                - id (int): Category ID.
                        - supplier_groups (Dict): Groups assigned to the supplier.
                            - data (List[Dict[str, Any]]): Each with type "supplier_groups" and an integer ID.
                        - default_payment_term, default_payment_type, default_payment_currency (Dict): Payment defaults.
                            - data:
                                - type (str): One of "payment_terms", "payment_types", or "payment_currencies".
                                - id (int): Resource ID.
                        - payment_types, payment_currencies (Dict): Accepted payments.
                            - data (List[Dict]): List of accepted payment method/currency objects.
                        - attachments (List[Dict]): List of attachments.
                            - Each attachment has:
                                - type (str): "attachments"
                                - id (int): Attachment ID.
                        - supplier_classification_values (List[Dict]): Classification values.
                            - Each item:
                                - type (str): "supplier_classification_values"
                                - id (str): Composite ID from supplier and classification.

                    - links (Dict[str, str]): Navigation URLs.
                        - self (str): Canonical URL of the resource.
                - Second element(int):
                    - HTTP status code: 200.

            If error:
                - First element (Dict[str, str]):
                    - error (str): Error message.
                - Second element (int):
                    - HTTP status code: 404.

    """

    for company in db.DB["suppliers"]["supplier_companies"].values():
        if company.get("external_id") == external_id:
            if _include:
                #simulate include
                pass
            return company, 200
    return {"error": "Company not found"}, 404

@tool_spec(
    spec={
        'name': 'update_supplier_company_by_external_id',
        'description': 'Update a supplier company by its external identifier.',
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': """ The external identifier of the supplier company. Example:
                    "1234-5678-abcd-efgh". """
                },
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated list of related resources to include
                    in the response. Allowed values are "attachments", "supplier_category",
                    "supplier_groups", "default_payment_term", "payment_types",
                    "default_payment_type", "payment_currencies", "default_payment_currency"
                    and "supplier_classification_values". """
                },
                'body': {
                    'type': 'object',
                    'description': """ Dictionary describing the update request. Required key
                    ``id`` must equal *external_id*.
                    
                    Top-level keys: """,
                    'properties': {
                        'id': {
                            'type': 'string',
                            'description': 'Must equal the *external_id* path parameter. Required field for validation.'
                        },
                        'type': {
                            'type': 'string',
                            'description': 'Must be "supplier_companies" if provided. Resource type identifier.'
                        },
                        'name': {
                            'type': 'string',
                            'description': 'Convenience field to update the company name. String value.'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Attribute updates with keys:',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Company name string'
                                },
                                'description': {
                                    'type': 'string',
                                    'description': 'Company description text'
                                },
                                'is_suggested': {
                                    'type': 'boolean',
                                    'description': 'Whether the company was suggested by a user'
                                },
                                'public': {
                                    'type': 'boolean',
                                    'description': 'Whether the company is publicly visible'
                                },
                                'risk': {
                                    'type': 'string',
                                    'description': 'Risk assessment string identifier'
                                },
                                'segmentation': {
                                    'type': 'string',
                                    'description': 'Segmentation category string'
                                },
                                'segmentation_status': {
                                    'type': 'string',
                                    'description': 'Current segmentation status'
                                },
                                'segmentation_notes': {
                                    'type': 'string',
                                    'description': 'Notes related to segmentation'
                                },
                                'tags': {
                                    'type': 'array',
                                    'description': 'List of tag strings associated with the company',
                                    'items': {
                                        'type': 'string'
                                    }
                                },
                                'url': {
                                    'type': 'string',
                                    'description': 'Company website URL'
                                },
                                'duns_number': {
                                    'type': 'string',
                                    'description': 'D-U-N-S® Number identifier'
                                },
                                'external_id': {
                                    'type': 'string',
                                    'description': 'External system identifier'
                                },
                                'self_registered': {
                                    'type': 'boolean',
                                    'description': 'Whether company registered via self-service'
                                },
                                'onboarding_form_completion_status': {
                                    'type': 'string',
                                    'description': """ One of
                                               "not_started", "in_progress" or "completed". """
                                },
                                'accept_all_currencies': {
                                    'type': 'boolean',
                                    'description': 'Whether company accepts all currencies'
                                },
                                'custom_fields': {
                                    'type': 'array',
                                    'description': 'List of custom field objects, each containing:',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'name': {
                                                'type': 'string',
                                                'description': 'Custom field name identifier'
                                            },
                                            'value': {
                                                'type': 'object',
                                                'description': 'Custom field value (string, number, boolean, list, dict, or null)',
                                                'properties': {},
                                                'required': []
                                            }
                                        },
                                        'required': [
                                            'name',
                                            'value'
                                        ]
                                    }
                                }
                            },
                            'required': []
                        },
                        'relationships': {
                            'type': 'object',
                            'description': 'Relationship updates with keys:',
                            'properties': {
                                'supplier_category': {
                                    'type': 'object',
                                    'description': 'Category relationship by ID, containing:',
                                    'properties': {
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Category identifier'
                                        }
                                    },
                                    'required': [
                                        'id'
                                    ]
                                },
                                'external_supplier_category': {
                                    'type': 'object',
                                    'description': 'Category by external ID, containing:',
                                    'properties': {
                                        'external_id': {
                                            'type': 'string',
                                            'description': 'External category identifier'
                                        }
                                    },
                                    'required': [
                                        'external_id'
                                    ]
                                },
                                'supplier_groups': {
                                    'type': 'array',
                                    'description': 'List of group relationships by ID, each containing:',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'id': {
                                                'type': 'integer',
                                                'description': 'Group identifier'
                                            }
                                        },
                                        'required': [
                                            'id'
                                        ]
                                    }
                                },
                                'external_supplier_groups': {
                                    'type': 'array',
                                    'description': 'List of groups by external ID, each containing:',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'external_id': {
                                                'type': 'string',
                                                'description': 'External group identifier'
                                            }
                                        },
                                        'required': [
                                            'external_id'
                                        ]
                                    }
                                },
                                'default_payment_term': {
                                    'type': 'object',
                                    'description': 'Default payment term by ID, containing:',
                                    'properties': {
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Payment term identifier'
                                        }
                                    },
                                    'required': [
                                        'id'
                                    ]
                                },
                                'external_default_payment_term': {
                                    'type': 'object',
                                    'description': 'Default payment term by external ID, containing:',
                                    'properties': {
                                        'external_id': {
                                            'type': 'string',
                                            'description': 'External payment term identifier'
                                        }
                                    },
                                    'required': [
                                        'external_id'
                                    ]
                                },
                                'payment_types': {
                                    'type': 'array',
                                    'description': 'List of accepted payment types by ID, each containing:',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'id': {
                                                'type': 'integer',
                                                'description': 'Payment type identifier'
                                            }
                                        },
                                        'required': [
                                            'id'
                                        ]
                                    }
                                },
                                'external_payment_types': {
                                    'type': 'array',
                                    'description': 'List of payment types by external ID, each containing:',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'external_id': {
                                                'type': 'string',
                                                'description': 'External payment type identifier'
                                            }
                                        },
                                        'required': [
                                            'external_id'
                                        ]
                                    }
                                },
                                'default_payment_type': {
                                    'type': 'object',
                                    'description': 'Default payment type by ID, containing:',
                                    'properties': {
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Payment type identifier'
                                        }
                                    },
                                    'required': [
                                        'id'
                                    ]
                                },
                                'external_default_payment_type': {
                                    'type': 'object',
                                    'description': 'Default payment type by external ID, containing:',
                                    'properties': {
                                        'external_id': {
                                            'type': 'string',
                                            'description': 'External payment type identifier'
                                        }
                                    },
                                    'required': [
                                        'external_id'
                                    ]
                                },
                                'payment_currencies': {
                                    'type': 'array',
                                    'description': 'List of accepted currencies by ID, each containing:',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'id': {
                                                'type': 'integer',
                                                'description': 'Currency identifier'
                                            }
                                        },
                                        'required': [
                                            'id'
                                        ]
                                    }
                                },
                                'external_payment_currencies': {
                                    'type': 'array',
                                    'description': 'List of currencies by external ID, each containing:',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'external_id': {
                                                'type': 'string',
                                                'description': 'External currency identifier'
                                            }
                                        },
                                        'required': [
                                            'external_id'
                                        ]
                                    }
                                },
                                'default_payment_currency': {
                                    'type': 'object',
                                    'description': 'Default currency by ID, containing:',
                                    'properties': {
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Currency identifier'
                                        }
                                    },
                                    'required': [
                                        'id'
                                    ]
                                },
                                'external_default_payment_currency': {
                                    'type': 'object',
                                    'description': 'Default currency by external ID, containing:',
                                    'properties': {
                                        'external_id': {
                                            'type': 'string',
                                            'description': 'External currency identifier'
                                        }
                                    },
                                    'required': [
                                        'external_id'
                                    ]
                                },
                                'attachments': {
                                    'type': 'array',
                                    'description': 'List of attachment references, each containing:',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'id': {
                                                'type': 'integer',
                                                'description': 'Attachment identifier'
                                            },
                                            'type': {
                                                'type': 'string',
                                                'description': 'Attachment type (e.g., "attachments")'
                                            }
                                        },
                                        'required': [
                                            'id',
                                            'type'
                                        ]
                                    }
                                },
                                'supplier_classification_values': {
                                    'type': 'array',
                                    'description': 'List of classification values by ID, each containing:',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'id': {
                                                'type': 'string',
                                                'description': 'Classification value identifier (composite ID)'
                                            }
                                        },
                                        'required': [
                                            'id'
                                        ]
                                    }
                                },
                                'external_supplier_classification_values': {
                                    'type': 'array',
                                    'description': 'List of classification values by external ID, each containing:',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'external_id': {
                                                'type': 'string',
                                                'description': 'External classification value identifier'
                                            }
                                        },
                                        'required': [
                                            'external_id'
                                        ]
                                    }
                                }
                            },
                            'required': []
                        }
                    },
                    'required': [
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
def patch(
    external_id: str,
    _include: Optional[str] = None,
    body: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Update a supplier company by its external identifier.

    Args:
        external_id (str): The external identifier of the supplier company. Example:
            "1234-5678-abcd-efgh".
        _include (Optional[str]): Comma-separated list of related resources to include
            in the response. Allowed values are "attachments", "supplier_category",
            "supplier_groups", "default_payment_term", "payment_types",
            "default_payment_type", "payment_currencies", "default_payment_currency"
            and "supplier_classification_values".
        body (Optional[Dict[str, Any]]): Dictionary describing the update request. Required key
            ``id`` must equal *external_id*.

            Top-level keys:
                - id (str): Must equal the *external_id* path parameter. Required field for validation.
                - type (Optional[str]): Must be "supplier_companies" if provided. Resource type identifier.
                - name (Optional[str]): Convenience field to update the company name. String value.
                - attributes (Optional[Dict[str, Any]]): Attribute updates with keys:
                    - name (Optional[str]): Company name string
                    - description (Optional[str]): Company description text
                    - is_suggested (Optional[bool]): Whether the company was suggested by a user
                    - public (Optional[bool]): Whether the company is publicly visible
                    - risk (Optional[str]): Risk assessment string identifier
                    - segmentation (Optional[str]): Segmentation category string
                    - segmentation_status (Optional[str]): Current segmentation status
                    - segmentation_notes (Optional[str]): Notes related to segmentation
                    - tags (Optional[List[str]]): List of tag strings associated with the company
                    - url (Optional[str]): Company website URL
                    - duns_number (Optional[str]): D-U-N-S® Number identifier
                    - external_id (Optional[str]): External system identifier
                    - self_registered (Optional[bool]): Whether company registered via self-service
                    - onboarding_form_completion_status (Optional[str]): One of
                      "not_started", "in_progress" or "completed".
                    - accept_all_currencies (Optional[bool]): Whether company accepts all currencies
                    - custom_fields (Optional[List[Dict[str, Any]]]): List of custom field objects, each containing:
                        - name (str): Custom field name identifier
                        - value (Any): Custom field value (string, number, boolean, list, dict, or null)
                - relationships (Optional[Dict[str, Any]]): Relationship updates with keys:
                    - supplier_category (Optional[Dict[str, Any]]): Category relationship by ID, containing:
                        - id (int): Category identifier
                    - external_supplier_category (Optional[Dict[str, Any]]): Category by external ID, containing:
                        - external_id (str): External category identifier
                    - supplier_groups (Optional[List[Dict[str, Any]]]): List of group relationships by ID, each containing:
                        - id (int): Group identifier
                    - external_supplier_groups (Optional[List[Dict[str, Any]]]): List of groups by external ID, each containing:
                        - external_id (str): External group identifier
                    - default_payment_term (Optional[Dict[str, Any]]): Default payment term by ID, containing:
                        - id (int): Payment term identifier
                    - external_default_payment_term (Optional[Dict[str, Any]]): Default payment term by external ID, containing:
                        - external_id (str): External payment term identifier
                    - payment_types (Optional[List[Dict[str, Any]]]): List of accepted payment types by ID, each containing:
                        - id (int): Payment type identifier
                    - external_payment_types (Optional[List[Dict[str, Any]]]): List of payment types by external ID, each containing:
                        - external_id (str): External payment type identifier
                    - default_payment_type (Optional[Dict[str, Any]]): Default payment type by ID, containing:
                        - id (int): Payment type identifier
                    - external_default_payment_type (Optional[Dict[str, Any]]): Default payment type by external ID, containing:
                        - external_id (str): External payment type identifier
                    - payment_currencies (Optional[List[Dict[str, Any]]]): List of accepted currencies by ID, each containing:
                        - id (int): Currency identifier
                    - external_payment_currencies (Optional[List[Dict[str, Any]]]): List of currencies by external ID, each containing:
                        - external_id (str): External currency identifier
                    - default_payment_currency (Optional[Dict[str, Any]]): Default currency by ID, containing:
                        - id (int): Currency identifier
                    - external_default_payment_currency (Optional[Dict[str, Any]]): Default currency by external ID, containing:
                        - external_id (str): External currency identifier
                    - attachments (Optional[List[Dict[str, Any]]]): List of attachment references, each containing:
                        - id (int): Attachment identifier
                        - type (str): Attachment type (e.g., "attachments")
                    - supplier_classification_values (Optional[List[Dict[str, Any]]]): List of classification values by ID, each containing:
                        - id (str): Classification value identifier (composite ID)
                    - external_supplier_classification_values (Optional[List[Dict[str, Any]]]): List of classification values by external ID, each containing:
                        - external_id (str): External classification value identifier

    Returns:
        Dict[str, Any]: A dictionary mirroring the company structure with at minimum:
            - id (int): Internal identifier of the supplier company
            - external_id (str): External identifier used for the API call
            - name (str): Company name
            - description (Optional[str]): Company description
            - is_suggested (Optional[bool]): Whether the company was suggested by a user
            - public (Optional[bool]): Whether the company is publicly visible
            - risk (Optional[str]): Risk assessment identifier
            - segmentation (Optional[str]): Segmentation category
            - segmentation_status (Optional[str]): Current segmentation status
            - segmentation_notes (Optional[str]): Notes related to segmentation
            - tags (Optional[List[str]]): List of associated tags
            - url (Optional[str]): Company website URL
            - duns_number (Optional[str]): D-U-N-S® Number
            - self_registered (Optional[bool]): Whether registered via self-service
            - onboarding_form_completion_status (Optional[str]): Form completion status
            - accept_all_currencies (Optional[bool]): Whether accepts all currencies
            - updated_at (Optional[str]): Last update timestamp
            - custom_fields (Optional[List[Dict[str, Any]]]): List of custom field objects, each containing:
                - name (str): Custom field name identifier
                - value (Any): Custom field value (string, number, boolean, list, dict, or null)
            - relationships (Dict[str, Any]): Relationship data with same structure as input, containing:
                - supplier_category (Optional[Dict[str, Any]]): Category relationship, containing:
                    - id (int): Category identifier
                - external_supplier_category (Optional[Dict[str, Any]]): Category by external ID, containing:
                    - external_id (str): External category identifier
                - supplier_groups (Optional[List[Dict[str, Any]]]): List of group relationships, each containing:
                    - id (int): Group identifier
                - external_supplier_groups (Optional[List[Dict[str, Any]]]): List of groups by external ID, each containing:
                    - external_id (str): External group identifier
                - default_payment_term (Optional[Dict[str, Any]]): Default payment term, containing:
                    - id (int): Payment term identifier
                - external_default_payment_term (Optional[Dict[str, Any]]): Default payment term by external ID, containing:
                    - external_id (str): External payment term identifier
                - payment_types (Optional[List[Dict[str, Any]]]): List of accepted payment types, each containing:
                    - id (int): Payment type identifier
                - external_payment_types (Optional[List[Dict[str, Any]]]): List of payment types by external ID, each containing:
                    - external_id (str): External payment type identifier
                - default_payment_type (Optional[Dict[str, Any]]): Default payment type, containing:
                    - id (int): Payment type identifier
                - external_default_payment_type (Optional[Dict[str, Any]]): Default payment type by external ID, containing:
                    - external_id (str): External payment type identifier
                - payment_currencies (Optional[List[Dict[str, Any]]]): List of accepted currencies, each containing:
                    - id (int): Currency identifier
                - external_payment_currencies (Optional[List[Dict[str, Any]]]): List of currencies by external ID, each containing:
                    - external_id (str): External currency identifier
                - default_payment_currency (Optional[Dict[str, Any]]): Default currency, containing:
                    - id (int): Currency identifier
                - external_default_payment_currency (Optional[Dict[str, Any]]): Default currency by external ID, containing:
                    - external_id (str): External currency identifier
                - attachments (Optional[List[Dict[str, Any]]]): List of attachment references, each containing:
                    - id (int): Attachment identifier
                    - type (str): Attachment type (e.g., "attachments")
                - supplier_classification_values (Optional[List[Dict[str, Any]]]): List of classification values, each containing:
                    - id (str): Classification value identifier (composite ID)
                - external_supplier_classification_values (Optional[List[Dict[str, Any]]]): List of classification values by external ID, each containing:
                    - external_id (str): External classification value identifier
            - included (Optional[Dict[str, Any]]): Present only when _include is supplied, contains requested related resources:
                - attachments (Optional[List[Dict[str, Any]]]): List of attachment objects, each containing:
                    - id (int): Attachment identifier
                    - type (str): Resource type (e.g., "attachments")
                    - attributes (Optional[Dict[str, Any]]): Attachment attributes
                - supplier_category (Optional[Dict[str, Any]]): Category object, containing:
                    - id (int): Category identifier
                    - type (str): Resource type (e.g., "supplier_categories")
                    - attributes (Optional[Dict[str, Any]]): Category attributes
                - supplier_groups (Optional[List[Dict[str, Any]]]): List of group objects, each containing:
                    - id (int): Group identifier
                    - type (str): Resource type (e.g., "supplier_groups")
                    - attributes (Optional[Dict[str, Any]]): Group attributes
                - default_payment_term (Optional[Dict[str, Any]]): Payment term object, containing:
                    - id (int): Payment term identifier
                    - type (str): Resource type (e.g., "payment_terms")
                    - attributes (Optional[Dict[str, Any]]): Payment term attributes
                - payment_types (Optional[List[Dict[str, Any]]]): List of payment type objects, each containing:
                    - id (int): Payment type identifier
                    - type (str): Resource type (e.g., "payment_types")
                    - attributes (Optional[Dict[str, Any]]): Payment type attributes
                - default_payment_type (Optional[Dict[str, Any]]): Payment type object, containing:
                    - id (int): Payment type identifier
                    - type (str): Resource type (e.g., "payment_types")
                    - attributes (Optional[Dict[str, Any]]): Payment type attributes
                - payment_currencies (Optional[List[Dict[str, Any]]]): List of currency objects, each containing:
                    - id (int): Currency identifier
                    - type (str): Resource type (e.g., "payment_currencies")
                    - attributes (Optional[Dict[str, Any]]): Currency attributes
                - default_payment_currency (Optional[Dict[str, Any]]): Currency object, containing:
                    - id (int): Currency identifier
                    - type (str): Resource type (e.g., "payment_currencies")
                    - attributes (Optional[Dict[str, Any]]): Currency attributes
                - supplier_classification_values (Optional[List[Dict[str, Any]]]): List of classification value objects, each containing:
                    - id (str): Classification value identifier (composite ID)
                    - type (str): Resource type (e.g., "supplier_classification_values")
                    - attributes (Optional[Dict[str, Any]]): Classification value attributes

    Raises:
        ValueError: If external_id is empty/invalid format, _include contains invalid relationships, 
                   body is None/not a dictionary, body validation fails via Pydantic, or body.id 
                   does not match external_id.
        FileNotFoundError: If supplier company with the given external_id is not found.
    """

    ###########################################################################
    # Step 1 – primitive validation                                           #
    ###########################################################################

    # 1.1 – Validate *external_id* (must be a non-empty slug consisting of    #
    #       alphanumerics + dashes).                                          #
    ###########################################################################
    if not isinstance(external_id, str) or not external_id.strip():
        raise ValueError("Invalid external_id")

    if not re.fullmatch(r"[A-Za-z0-9\-]+", external_id):
        raise ValueError("Invalid external_id format")

    ###########################################################################
    # 1.2 – Validate *_include*                                               #
    ###########################################################################
    allowed_includes = {
        "attachments",
        "supplier_category",
        "supplier_groups",
        "default_payment_term",
        "payment_types",
        "default_payment_type",
        "payment_currencies",
        "default_payment_currency",
        "supplier_classification_values",
    }

    if _include is not None:
        if not isinstance(_include, str):
            raise ValueError("_include must be a comma-separated string")

        include_set = {part.strip() for part in _include.split(",") if part.strip()}

        invalid = include_set - allowed_includes
        if invalid:
            raise ValueError(f"Invalid include relationship(s): {', '.join(sorted(invalid))}")
    else:
        include_set: Set[str] = set()

    ###########################################################################
    # Step 2 – Body validation via Pydantic                                   #
    ###########################################################################
    if body is None:
        raise ValueError("Body is required")

    if not isinstance(body, dict):
        raise ValueError("Body must be a JSON object")

    try:
        validated_body = SupplierCompanyUpdateModel(**body)
    except PydanticValidationError as exc:  # noqa: B904 – Pydantic error alias
        # Return the first error message for brevity – client can inspect further
        first_err = exc.errors()[0]
        field = " -> ".join(map(str, first_err["loc"]))
        raise ValueError(f"Invalid body field '{field}': {first_err['msg']}")

    if validated_body.id != external_id:
        raise ValueError("External id in body must match url")

    ###########################################################################
    # Step 3 – Locate the company in the DB                                   #
    ###########################################################################
    supplier_companies = db.DB.setdefault("suppliers", {}).setdefault(
        "supplier_companies", {}
    )

    company_id: Optional[str] = None
    for c_id, c in supplier_companies.items():
        if c.get("external_id") == external_id:
            company_id = c_id
            break

    if company_id is None:
        raise FileNotFoundError("Company not found")

    company_ref = supplier_companies[company_id]

    ###########################################################################
    # Step 4 – Perform the update                                             #
    ###########################################################################
    update_payload: Dict[str, Any] = {}

    # 4.1 – If the caller used root-level convenience fields (e.g. "name"),
    #       apply them directly.
    for key in ("name",):  # Extend as necessary
        value = getattr(validated_body, key)
        if value is not None:
            update_payload[key] = value

    # 4.2 – Merge attributes dictionary if provided
    if validated_body.attributes:
        update_payload.update(validated_body.attributes)

    # NOTE: Relationship handling is non-trivial and depends on other DB
    #       structures – keep it as future work while not breaking contract.

    company_ref.update(update_payload)

    ###########################################################################
    # Step 5 – Build response                                                 #
    ###########################################################################
    response_obj: Dict[str, Any] = company_ref.copy()

    # Very basic _include behaviour – attach empty placeholders for requested
    # relationships so that client code can rely on presence of keys.
    if include_set:
        response_obj.setdefault("included", {})
        for rel in include_set:
            response_obj["included"].setdefault(rel, [])

    return response_obj


@tool_spec(
    spec={
        'name': 'delete_supplier_company_by_external_id',
        'description': """ Deletes a supplier company using its external identifier.
        
        This operation permanently deletes an existing supplier company. You must provide the external identifier used during the supplier company’s creation. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': 'The external ID of the supplier company to delete. Example: "1234-5678-abcd-efgh"'
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def delete(external_id: str) -> Tuple[Dict[str, Any], int]:
    """
    Deletes a supplier company using its external identifier.

    This operation permanently deletes an existing supplier company. You must provide the external identifier used during the supplier company’s creation.

    Args:
        external_id (str): The external ID of the supplier company to delete. Example: "1234-5678-abcd-efgh"

    Returns:
        Tuple[Dict[str, Any], int]: A tuple containing:
            - First element (Dict[str, Any]): Empty dictionary.
            - Second element (int): HTTP status code: 204.

    Raises:
        SupplierCompanyExternalIdInvalidError: If external_id is not a string, is empty, or contains only whitespace.
        NotFoundError: If no supplier company with the given external_id exists.
    """

    # Type and value validation for external_id
    if not isinstance(external_id, str) or not external_id.strip():
        raise custom_errors.SupplierCompanyExternalIdInvalidError(
            "external_id must be a non-empty, non-whitespace string."
        )

    company_id_to_delete = None
    for company_id, company in db.DB["suppliers"]["supplier_companies"].items():
        if company.get("external_id") == external_id:
            company_id_to_delete = company_id
            break
    if company_id_to_delete is None:
        raise custom_errors.NotFoundError(f"Company with external_id '{external_id}' not found.")
    del db.DB["suppliers"]["supplier_companies"][company_id_to_delete]
    return {}, 204 
