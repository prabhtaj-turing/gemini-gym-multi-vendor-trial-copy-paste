"""
Supplier Company Management by ID Module

This module provides functionality for managing individual supplier companies using
their unique internal identifiers in the Workday Strategic Sourcing system. It
supports operations for retrieving, updating, and deleting supplier company records.

The module interfaces with the simulation database to provide comprehensive supplier
company management capabilities, allowing users to:
- Retrieve detailed supplier company information
- Update existing supplier company records
- Delete supplier company entries
- Handle related resource inclusion where applicable

Functions:
    get: Retrieves supplier company details by ID
    patch: Updates supplier company details by ID
    delete: Deletes a supplier company by ID
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, Tuple, Union
from .SimulationEngine import db
from .SimulationEngine.custom_errors import (
    InvalidInputError,
    NotFoundError,
    DatabaseSchemaError,
    ValidationError,
)
from .SimulationEngine.utils import (
    ALLOWED_INCLUDE_VALUES,
    collect_included_resources,
    set_company_relationships,
)

@tool_spec(
    spec={
        'name': 'get_supplier_company_by_id',
        'description': """ Retrieve details of a supplier company by ID.
        
        Fetches the metadata, attributes, and relationships of a supplier company
        using its unique ID. Optionally includes related resources by specifying
        the `_include` parameter. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': """ Unique identifier of the supplier company.
                    Example: 1 """
                },
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated string of related resources to include.
                    Allowed values:
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
                'id'
            ]
        }
    }
)
def get(id: int, _include: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve details of a supplier company by ID.

    Fetches the metadata, attributes, and relationships of a supplier company
    using its unique ID. Optionally includes related resources by specifying
    the `_include` parameter.

    Args:
        id (int): Unique identifier of the supplier company.
            Example: 1

        _include (Optional[str]): Comma-separated string of related resources to include.
            Allowed values:
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
        Dict[str, Any]: A dictionary containing the supplier company details.

            - data (Dict[str, Any]):
                - type (str): Always "supplier_companies".
                - id (int): Unique supplier company ID.
                - attributes (Dict[str, Any]):
                    - name (str): Supplier company name (≤ 255 characters).
                    - description (Optional[str]): Supplier company description.
                    - is_suggested (bool): True if the supplier was suggested by a team member.
                    - public (bool): Indicates if the supplier company is public.
                    - risk (Optional[str]): Supplier risk slug value.
                    - segmentation (Optional[str]): Segmentation slug.
                    - segmentation_status (Optional[str]): Segmentation status slug.
                    - segmentation_notes (Optional[str]): Notes regarding segmentation.
                    - tags (List[str]): List of tags assigned to the supplier.
                    - url (Optional[str]): Supplier website URL.
                    - duns_number (Optional[str]): D-U-N-S® number.
                    - external_id (Optional[str]): Supplier's internal database ID.
                    - self_registered (bool): Whether the supplier self-registered.
                    - onboarding_form_completion_status (Optional[str]): Onboarding status. One of:
                        - null
                        - "not_started"
                        - "in_progress"
                        - "completed"
                    - accept_all_currencies (bool): Indicates if all currencies are accepted.
                    - updated_at (str): ISO 8601 datetime string for the last modification.
                    - custom_fields (List[Dict[str, Any]]):  List of custom field entries. Each entry can be of multiple supported types.
                        Note: File-type custom fields are only accessible via UI and return `null` in the API.
                        Supported types include:
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
                        - name (str): Field name.
                        - value (Union[str, int, float, bool, List[Any], None]): Field value depending on type.

                - relationships (Dict[str, Any]):
                    - attachments:
                        - data (List[Dict[str, Union[str, int]]]):
                            - id (int): Attachment ID.
                            - type (str): Always "attachments".
                    - supplier_category:
                        - data:
                            - id (int): Category ID.
                            - type (str): Always "supplier_categories".
                    - supplier_groups:
                        - data (List[Dict[str, Union[str, int]]]):
                            - id (int): Group ID.
                            - type (str): Always "supplier_groups".
                    - default_payment_term:
                        - data:
                            - id (int): Term ID.
                            - type (str): Always "payment_terms".
                    - payment_types:
                        - data (List[Dict[str, Union[str, int]]]):
                            - id (int): Payment type ID.
                            - type (str): Always "payment_types".
                    - default_payment_type:
                        - data:
                            - id (int): Payment type ID.
                            - type (str): Always "payment_types".
                    - payment_currencies:
                        - data (List[Dict[str, Union[str, int]]]):
                            - id (int): Currency ID.
                            - type (str): Always "payment_currencies".
                    - default_payment_currency:
                        - data:
                            - id (int): Currency ID.
                            - type (str): Always "payment_currencies".
                    - supplier_classification_values:
                        - data (List[Dict[str, Union[str, int]]]):
                            - id (str): Composite ID (e.g., "1-22").
                            - type (str): Always "supplier_classification_values".

                - links (Dict[str, str]):
                    - self (str): Resource URL.

    Raises:
        ValidationError: If `id` is not a positive integer or `_include` is not a string.
        NotFoundError: If no supplier company exists with the provided `id`.
    """

    # Input validation
    if not isinstance(id, int) or id <= 0:
        raise InvalidInputError("id must be a positive integer")

    if _include and not isinstance(_include, str):
        raise InvalidInputError("_include must be a string")

    # Get the company from the database
    company = db.DB.get("suppliers", {}).get("supplier_companies", {}).get(id)
    if not company:
        raise NotFoundError("Company not found")

    if _include:
        # Simulate include logic (not fully implemented)
        pass
    return company

@tool_spec(
    spec={
        'name': 'update_supplier_company_by_id',
        'description': 'Updates the details of an existing supplier company by ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': """ Unique identifier of the supplier company.
                    Example: 1 """
                },
                '_include': {
                    'type': 'string',
                    'description': 'Related resources to include in the response. It can be one of the following values ["attachments", "supplier_category", "supplier_groups", "default_payment_term", "payment_types", "default_payment_type", "payment_currencies", "default_payment_currency", "supplier_classification_values"]'
                },
                'body': {
                    'type': 'object',
                    'description': 'SupplierCompanyUpdate object containing:',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Must be "supplier_companies".'
                        },
                        'id': {
                            'type': 'integer',
                            'description': 'Supplier company ID (must match the path parameter).'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'A dictionary containing the attributes of the supplier company:',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Name of the supplier (≤ 255 characters).'
                                },
                                'description': {
                                    'type': 'string',
                                    'description': 'Company description.'
                                },
                                'public': {
                                    'type': 'boolean',
                                    'description': 'Whether the company is publicly listed.'
                                },
                                'risk': {
                                    'type': 'string',
                                    'description': 'Risk slug defined by your organization.'
                                },
                                'segmentation': {
                                    'type': 'string',
                                    'description': 'Segmentation slug.'
                                },
                                'segmentation_status': {
                                    'type': 'string',
                                    'description': 'Segmentation status slug.'
                                },
                                'segmentation_notes': {
                                    'type': 'string',
                                    'description': 'Notes about the segmentation.'
                                },
                                'tags': {
                                    'type': 'array',
                                    'description': 'Tags assigned to the supplier.',
                                    'items': {
                                        'type': 'string'
                                    }
                                },
                                'url': {
                                    'type': 'string',
                                    'description': 'Website of the supplier.'
                                },
                                'duns_number': {
                                    'type': 'string',
                                    'description': 'D-U-N-S® Number.'
                                },
                                'external_id': {
                                    'type': 'string',
                                    'description': 'Your internal system ID for the supplier.'
                                },
                                'self_registered': {
                                    'type': 'boolean',
                                    'description': 'Whether the supplier self-registered.'
                                },
                                'onboarding_form_completion_status': {
                                    'type': 'string',
                                    'description': "One of: null, 'not_started', 'in_progress', 'completed'."
                                },
                                'accept_all_currencies': {
                                    'type': 'boolean',
                                    'description': 'Whether all currencies are accepted.'
                                },
                                'custom_fields': {
                                    'type': 'array',
                                    'description': """ List of custom field entries. Each entry can be of multiple supported types.
                                             Note: File-type custom fields are only accessible via UI and return `null` in the API.
                                            Supported types include:
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
                                                - Related """,
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                }
                            },
                            'required': [
                                'name',
                                'public',
                                'tags',
                                'self_registered',
                                'onboarding_form_completion_status',
                                'accept_all_currencies',
                                'custom_fields'
                            ]
                        },
                        'relationships': {
                            'type': 'object',
                            'description': 'Supplier relationships (replaces existing data).',
                            'properties': {
                                'supplier_category': {
                                    'type': 'object',
                                    'description': "A dictionary representing the supplier category relationship. Must contain 'data' with 'type' ('supplier_categories') and 'id'.",
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "supplier_categories".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Supplier category identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'supplier_groups': {
                                    'type': 'object',
                                    'description': "A dictionary representing supplier group relationships. Must contain 'data' as a list of dictionaries, each with 'type' ('supplier_groups') and 'id'.",
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "supplier_groups".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Supplier group identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'default_payment_term': {
                                    'type': 'object',
                                    'description': "A dictionary for the default payment term relationship. Must contain 'data' with 'type' ('payment_terms') and 'id'.",
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "payment_terms".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Payment term identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'payment_types': {
                                    'type': 'object',
                                    'description': "A dictionary for payment type relationships. Must contain 'data' as a list of dictionaries, each with 'type' ('payment_types') and 'id'.",
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "payment_types".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Payment type identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'default_payment_type': {
                                    'type': 'object',
                                    'description': "A dictionary for the default payment type relationship. Must contain 'data' with 'type' ('payment_types') and 'id'.",
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "payment_types".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Payment type identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'payment_currencies': {
                                    'type': 'object',
                                    'description': "A dictionary for payment currency relationships. Must contain 'data' as a list of dictionaries, each with 'type' ('currencies') and 'id'.",
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "payment_currencies".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Payment currency identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'default_payment_currency': {
                                    'type': 'object',
                                    'description': "A dictionary for the default payment currency relationship. Must contain 'data' with 'type' ('currencies') and 'id'.",
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "payment_currencies".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Payment currency identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'attachments': {
                                    'type': 'object',
                                    'description': "A dictionary for attachment relationships. Must contain 'data' as a list of dictionaries, each with 'type' ('attachments') and 'id'.",
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "attachments".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Attachment identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                },
                                'supplier_classification_values': {
                                    'type': 'object',
                                    'description': "A dictionary for supplier classification value relationships. Must contain 'data' as a list of dictionaries, each with 'type' ('supplier_classification_values') and 'id'.",
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': 'Object type, should always be "supplier_classification_values".'
                                        },
                                        'id': {
                                            'type': 'integer',
                                            'description': 'Supplier classification value identifier string.'
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'id'
                                    ]
                                }
                            },
                            'required': [
                                'supplier_category',
                                'supplier_groups',
                                'default_payment_term',
                                'payment_types',
                                'default_payment_type',
                                'payment_currencies',
                                'default_payment_currency',
                                'attachments',
                                'supplier_classification_values'
                            ]
                        }
                    },
                    'required': [
                        'type',
                        'id',
                        'attributes',
                        'relationships'
                    ]
                }
            },
            'required': [
                'id',
                'body'
            ]
        }
    }
)
def patch(
    id: int, body: Dict[str, Any], _include: Optional[str] = None
) -> Dict[str, Any]:
    """
    Updates the details of an existing supplier company by ID.

    Args:
        id (int): Unique identifier of the supplier company.
            Example: 1

        _include (Optional[str]): Comma-separated list of related resource types to include.
            Allowed values:
                - "attachments"
                - "supplier_category"
                - "supplier_groups"
                - "default_payment_term"
                - "payment_types"
                - "default_payment_type"
                - "payment_currencies"
                - "default_payment_currency"
                - "supplier_classification_values"

        body (Dict[str, Any]): SupplierCompanyUpdate object containing:
            - type (str): Must be "supplier_companies".
            - id (int): Supplier company ID (must match the path parameter).
            - attributes (Dict[str, Any]): A dictionary containing the attributes of the supplier company:
                - name (str): Name of the supplier (≤ 255 characters).
                - description (Optional[str]): Company description.
                - public (bool): Whether the company is publicly listed.
                - risk (Optional[str]): Risk slug defined by your organization.
                - segmentation (Optional[str]): Segmentation slug.
                - segmentation_status (Optional[str]): Segmentation status slug.
                - segmentation_notes (Optional[str]): Notes about the segmentation.
                - tags (List[str]): Tags assigned to the supplier.
                - url (Optional[str]): Website of the supplier.
                - duns_number (Optional[str]): D-U-N-S® Number.
                - external_id (Optional[str]): Your internal system ID for the supplier.
                - self_registered (bool): Whether the supplier self-registered.
                - onboarding_form_completion_status (str): One of: null, 'not_started', 'in_progress', 'completed'.
                - accept_all_currencies (bool): Whether all currencies are accepted.
                - custom_fields (List[Dict[str, Any]]): List of custom field entries. Each entry can be of multiple supported types.
                    Note: File-type custom fields are only accessible via UI and return `null` in the API.

                    Supported types include:
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

            - relationships (Dict[str, Any]): Supplier relationships (replaces existing data).
                - 'supplier_category' (Dict[str, Any]): A dictionary representing the supplier category relationship. Must contain 'data' with 'type' ('supplier_categories') and 'id'.
                    - type (str): Object type, should always be "supplier_categories".
                    - id (int): Supplier category identifier string.
                - 'supplier_groups' (Dict[str, Any]): A dictionary representing supplier group relationships. Must contain 'data' as a list of dictionaries, each with 'type' ('supplier_groups') and 'id'.
                    - type (str): Object type, should always be "supplier_groups".
                    - id (int): Supplier group identifier string.
                - 'default_payment_term' (Dict[str, Any]): A dictionary for the default payment term relationship. Must contain 'data' with 'type' ('payment_terms') and 'id'.
                    - type (str): Object type, should always be "payment_terms".
                    - id (int): Payment term identifier string.
                - 'payment_types' (Dict[str, Any]): A dictionary for payment type relationships. Must contain 'data' as a list of dictionaries, each with 'type' ('payment_types') and 'id'.
                    - type (str): Object type, should always be "payment_types".
                    - id (int): Payment type identifier string.
                - 'default_payment_type' (Dict[str, Any]): A dictionary for the default payment type relationship. Must contain 'data' with 'type' ('payment_types') and 'id'.
                    - type (str): Object type, should always be "payment_types".
                    - id (int): Payment type identifier string.
                - 'payment_currencies' (Dict[str, Any]): A dictionary for payment currency relationships. Must contain 'data' as a list of dictionaries, each with 'type' ('currencies') and 'id'.
                    - type (str): Object type, should always be "payment_currencies".
                    - id (int): Payment currency identifier string.
                - 'default_payment_currency' (Dict[str, Any]): A dictionary for the default payment currency relationship. Must contain 'data' with 'type' ('currencies') and 'id'.
                    - type (str): Object type, should always be "payment_currencies".
                    - id (int): Payment currency identifier string.
                - 'attachments' (Dict[str, Any]): A dictionary for attachment relationships. Must contain 'data' as a list of dictionaries, each with 'type' ('attachments') and 'id'.
                    - type (str): Object type, should always be "attachments".
                    - id (int): Attachment identifier string.
                - 'supplier_classification_values' (Dict[str, Any]): A dictionary for supplier classification value relationships. Must contain 'data' as a list of dictionaries, each with 'type' ('supplier_classification_values') and 'id'.
                    - type (str): Object type, should always be "supplier_classification_values".
                    - id (int): Supplier classification value identifier string.

        _include (Optional[str]): Related resources to include in the response. It can be one of the following values ["attachments", "supplier_category", "supplier_groups", "default_payment_term", "payment_types", "default_payment_type", "payment_currencies", "default_payment_currency", "supplier_classification_values"]

    Returns:
        Dict[str, Any]: A dictionary containing the updated supplier company details.

            - data (Dict[str, Any]):
                - type (str): Always "supplier_companies".
                - id (int): Unique supplier company ID.
                - attributes (Dict[str, Any]):
                    - name (str): Supplier company name (≤ 255 characters).
                    - description (Optional[str]): Supplier company description.
                    - is_suggested (bool): True if the supplier was suggested by a team member.
                    - public (bool): Indicates if the supplier company is public.
                    - risk (Optional[str]): Supplier risk slug value.
                    - segmentation (Optional[str]): Segmentation slug.
                    - segmentation_status (Optional[str]): Segmentation status slug.
                    - segmentation_notes (Optional[str]): Notes regarding segmentation.
                    - tags (List[str]): List of tags assigned to the supplier.
                    - url (Optional[str]): Supplier website URL.
                    - duns_number (Optional[str]): D-U-N-S® number.
                    - external_id (Optional[str]): Supplier's internal database ID.
                    - self_registered (bool): Whether the supplier self-registered.
                    - onboarding_form_completion_status (Optional[str]): Onboarding status. One of:
                        - null
                        - "not_started"
                        - "in_progress"
                        - "completed"
                    - accept_all_currencies (bool): Indicates if all currencies are accepted.
                    - updated_at (str): ISO 8601 datetime string for the last modification.
                    - custom_fields (List[Dict[str, Any]]):  List of custom field entries. Each entry can be of multiple supported types.
                        Note: File-type custom fields are only accessible via UI and return `null` in the API.
                        Supported types include:
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
                        - name (str): Field name.
                        - value (Union[str, int, float, bool, List[Any], None]): Field value depending on type.

                - relationships (Dict[str, Any]):
                    - attachments:
                        - data (List[Dict[str, Union[str, int]]]):
                            - id (int): Attachment ID.
                            - type (str): Always "attachments".
                    - supplier_category:
                        - data:
                            - id (int): Category ID.
                            - type (str): Always "supplier_categories".
                    - supplier_groups:
                        - data (List[Dict[str, Union[str, int]]]):
                            - id (int): Group ID.
                            - type (str): Always "supplier_groups".
                    - default_payment_term:
                        - data:
                            - id (int): Term ID.
                            - type (str): Always "payment_terms".
                    - payment_types:
                        - data (List[Dict[str, Union[str, int]]]):
                            - id (int): Payment type ID.
                            - type (str): Always "payment_types".
                    - default_payment_type:
                        - data:
                            - id (int): Payment type ID.
                            - type (str): Always "payment_types".
                    - payment_currencies:
                        - data (List[Dict[str, Union[str, int]]]):
                            - id (int): Currency ID.
                            - type (str): Always "payment_currencies".
                    - default_payment_currency:
                        - data:
                            - id (int): Currency ID.
                            - type (str): Always "payment_currencies".
                    - supplier_classification_values:
                        - data (List[Dict[str, Union[str, int]]]):
                            - id (str): Composite ID (e.g., "1-22").
                            - type (str): Always "supplier_classification_values".

                - links (Dict[str, str]):
                    - self (str): Resource URL.

    Raises:
        InvalidInputError: If `id` is not a positive integer or `_include` is not a string.
        NotFoundError: If no supplier company exists with the provided `id`.
        ValidationError: If the `_include` parameter contains invalid values.
        ValidationError: If the `relationships` payload contains invalid values.
    """

    # Input validation
    if not isinstance(id, int) or id <= 0:
        raise InvalidInputError("id must be a positive integer")

    if _include and not isinstance(_include, str):
        raise InvalidInputError("_include must be a string")

    # Get the company from the database
    company = db.DB.get("suppliers", {}).get("supplier_companies", {}).get(id)
    if not company:
        raise NotFoundError("Company not found")

    # Validate that the body is not empty
    if not body:
        raise InvalidInputError("Body is required")

    relationships = body.get("relationships", {})
    # Update the company with the new data
    company.update(body)

    # Update the company in the database
    db.DB["suppliers"]["supplier_companies"][id] = company

    if relationships:
        for key in relationships.keys():
            if key not in ALLOWED_INCLUDE_VALUES:
                raise ValidationError(f"Invalid relationship: {key}")
        set_company_relationships(company, relationships)

    if _include:
        includes = [item.strip() for item in _include.split(",")]
        for include in includes:
            if include not in ALLOWED_INCLUDE_VALUES:
                raise ValidationError(f"Invalid include parameter: {include}")
        included_resources = collect_included_resources(company, includes)
        company["included"] = included_resources

    return company


@tool_spec(
    spec={
        'name': 'delete_supplier_company_by_id',
        'description': """ Deletes a supplier company by its unique identifier.
        
        This operation permanently removes the supplier company record from the system.
        You must provide the supplier company ID that was returned upon its creation. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': """ Required. Unique identifier of the supplier company.
                    Example: 1 """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete(id: int) -> str:
    """
    Deletes a supplier company by its unique identifier.

    This operation permanently removes the supplier company record from the system.
    You must provide the supplier company ID that was returned upon its creation.

    Args:
        id (int): Required. Unique identifier of the supplier company.
            Example: 1

    Returns:
        str: A success message indicating the deletion was successful.

    Raises:
        InvalidInputError: If the ID is not a positive integer.
        NotFoundError: If the company with the specified ID is not found.
        DatabaseSchemaError: If there's an issue with the database schema structure.
    """

    # Validate that the ID is a positive integer internally
    if not isinstance(id, int) or id <= 0:
        raise InvalidInputError("ID must be a positive integer")

    # Check for the company's existence in the database.
    try:
        if id not in db.DB["suppliers"]["supplier_companies"]:
            raise NotFoundError("Company not found")
    except KeyError:
        # Check which key is missing to provide specific error message
        if "suppliers" not in db.DB:
            raise DatabaseSchemaError(
                "Database schema error: 'suppliers' key is missing"
            )
        elif "supplier_companies" not in db.DB["suppliers"]:
            raise DatabaseSchemaError(
                "Database schema error: 'supplier_companies' key is missing"
            )
        else:
            raise DatabaseSchemaError(
                "Suppliers or supplier_companies not found in schema"
            )

    # Delete the company record.
    del db.DB["suppliers"]["supplier_companies"][id]
    return "Deletion successful"
