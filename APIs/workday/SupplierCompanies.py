"""
Supplier Companies Management Module

This module provides functionality for managing supplier companies in the Workday
Strategic Sourcing system. It supports operations for retrieving and creating
supplier company records with various filtering, inclusion, and pagination options.

The module interfaces with the simulation database to provide comprehensive supplier
company management capabilities. It allows users to:
- Retrieve supplier companies with flexible filtering options
- Create new supplier company records with custom attributes
- Support for related resource inclusion and pagination
- Handle complex relationships and attributes

Functions:
    get: Retrieves supplier companies based on specified criteria
    post: Creates a new supplier company record
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, List, Tuple, Union
import datetime

from .SimulationEngine import db
from .SimulationEngine.utils import (
    ALLOWED_FILTER_KEYS,
    ALLOWED_INCLUDE_VALUES,
    apply_company_filters,
    collect_included_resources,
)
from .SimulationEngine.models import (
    IncludeOptions,
    SegmentationStatus,
    OnboardingStatus,
    SupplierCompanyCreate,
    SupplierCompanyResponse,
)


@tool_spec(
    spec={
        'name': 'list_supplier_companies',
        'description': 'Retrieve supplier companies with optional filtering, inclusion and pagination.',
        'parameters': {
            'type': 'object',
            'properties': {
                'filter': {
                    'type': 'object',
                    'description': 'Filter criteria with allowed keys and expected value types.',
                    'properties': {
                        'updated_at_from': {
                            'type': 'string',
                            'description': 'ISO-8601 timestamp. Include companies updated on or after this time.'
                        },
                        'updated_at_to': {
                            'type': 'string',
                            'description': 'ISO-8601 timestamp. Include companies updated on or before this time.'
                        },
                        'external_id_empty': {
                            'type': 'boolean',
                            'description': 'Only companies whose external_id is empty.'
                        },
                        'external_id_not_empty': {
                            'type': 'boolean',
                            'description': 'Only companies whose external_id is not empty.'
                        },
                        'external_id_equals': {
                            'type': 'string',
                            'description': 'Exact match on external_id.'
                        },
                        'external_id_not_equals': {
                            'type': 'string',
                            'description': 'Exclude this external_id value.'
                        },
                        'segmentation_status_equals': {
                            'type': 'object',
                            'description': 'Any of the given segmentation statuses.',
                            'properties': {},
                            'required': []
                        }
                    },
                    'required': []
                },
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated list of related resources to embed. Allowed values:
                    "attachments", "supplier_category", "supplier_groups", "default_payment_term",
                    "payment_types", "default_payment_type", "payment_currencies", "default_payment_currency",
                    "supplier_classification_values". """
                },
                'page': {
                    'type': 'object',
                    'description': 'Pagination settings.',
                    'properties': {
                        'size': {
                            'type': 'integer',
                            'description': 'Page size between 1 and 100. Default 10.'
                        },
                        'number': {
                            'type': 'integer',
                            'description': 'Page number starting at 1. Default 1.'
                        }
                    },
                    'required': [
                        'size',
                        'number'
                    ]
                }
            },
            'required': []
        }
    }
)
def get(
    filter: Optional[Dict[str, Any]] = None,
    _include: Optional[str] = None,
    page: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], int]:
    """Retrieve supplier companies with optional filtering, inclusion and pagination.

    Args:
        filter (Optional[Dict[str, Any]]): Filter criteria with allowed keys and expected value types.
            - updated_at_from (Optional[str]): ISO-8601 timestamp. Include companies updated on or after this time.
            - updated_at_to (Optional[str]): ISO-8601 timestamp. Include companies updated on or before this time.
            - external_id_empty (Optional[bool]): Only companies whose external_id is empty.
            - external_id_not_empty (Optional[bool]): Only companies whose external_id is not empty.
            - external_id_equals (Optional[str]): Exact match on external_id.
            - external_id_not_equals (Optional[str]): Exclude this external_id value.
            - segmentation_status_equals (Optional[List[str] | str]): Any of the given segmentation statuses.
        _include (Optional[str]): Comma-separated list of related resources to embed. Allowed values:
            "attachments", "supplier_category", "supplier_groups", "default_payment_term",
            "payment_types", "default_payment_type", "payment_currencies", "default_payment_currency",
            "supplier_classification_values".
        page (Optional[Dict[str, Any]]): Pagination settings. If not provided, returns all results.
            - size (int): Page size between 1 and 100. Default 10 when page is provided.
            - number (int): Page number starting at 1. Default 1.

    Returns:
        Tuple[Dict[str, Any], int]: Response body and HTTP status code.
        
        Success response (200):
            - data (List[Dict[str, Any]]): Array of supplier company objects.
                - type (str): Always "supplier_companies".
                - id (str): Supplier company identifier.
                - attributes (Dict[str, Any]): Core company attributes.
                    - name (str): Company name.
                    - description (str): Company description.
                    - is_suggested (bool): Whether company is user-suggested.
                    - public (bool): Whether company is publicly listed.
                    - risk (str): Risk classification.
                    - segmentation (str): Segmentation type.
                    - segmentation_status (str): Segmentation status.
                    - segmentation_notes (str): Segmentation notes.
                    - tags (List[str]): Associated tags.
                    - url (str): Company website URL.
                    - duns_number (str): D-U-N-S number.
                    - external_id (str): External system identifier.
                    - self_registered (bool): Whether supplier self-registered.
                    - onboarding_form_completion_status (str): Onboarding status.
                    - accept_all_currencies (bool): Whether accepts all currencies.
                    - updated_at (str): Last modification timestamp.
                    - custom_fields (List[Dict[str, Any]]): Custom field definitions.
                        - name (str): Field name.
                        - value (Any): Field value.
                - relationships (Dict[str, Any]): Relationship linkage objects.
                    - supplier_category: Supplier category relationship.
                    - supplier_groups: Supplier groups relationship.
                    - default_payment_term: Default payment term relationship.
                    - payment_types: Payment types relationship.
                    - default_payment_type: Default payment type relationship.
                    - payment_currencies: Payment currencies relationship.
                    - default_payment_currency: Default payment currency relationship.
                    - attachments: Attachments relationship.
                    - supplier_classification_values: Classification values relationship.
                - links (Dict[str, str]): Resource links.
                    - self (str): Link to the resource.
            - included (List[Dict[str, Any]]): Related resources requested via _include.
                - type (str): Type of the related resource.
                - id (str|int): Identifier of the related resource.
                - attributes (Dict[str, Any]): Resource-specific attributes.
            - meta (Dict[str, Any]): Result set metadata.
                - count (int): Total number of pages available for the current size parameter.
            - links (Dict[str, str]): List of related links.
                - self (str): Link to the current page.
                - next (str|None): Link to the next page.
                - prev (str|None): Link to the previous page.

    Raises:
        Returns 400 Bad Request when validation fails with response containing:
            - errors (List[Dict[str, str]]): Array of error objects.
                - detail (str): A human-readable explanation specific to this occurrence of the problem.
    """
    
    try:
        # Input validation
        if filter is not None and not isinstance(filter, dict):
            raise TypeError("Argument 'filter' must be a dictionary or None.")

        if _include is not None and not isinstance(_include, str):
            raise TypeError("Argument '_include' must be a string or None.")

        if page is not None and not isinstance(page, dict):
            raise TypeError("Argument 'page' must be a dictionary or None.")

        # Validate filter keys & value types
        if filter:
            unknown_keys = set(filter) - set(ALLOWED_FILTER_KEYS)
            if unknown_keys:
                raise ValueError(f"Unknown filter keys: {sorted(unknown_keys)}")

            for key, value in filter.items():
                if key in {"external_id_empty", "external_id_not_empty"}:
                    if not isinstance(value, bool):
                        raise TypeError(f"Filter '{key}' must be a boolean.")

                elif key in {"external_id_equals", "external_id_not_equals"}:
                    if not isinstance(value, str):
                        raise TypeError(f"Filter '{key}' must be a string.")

                elif key == "segmentation_status_equals":
                    if not isinstance(value, (list, str)):
                        raise TypeError("Filter 'segmentation_status_equals' must be a string or a list of strings.")
                    if isinstance(value, str):
                        filter[key] = [value]

                elif key in {"updated_at_from", "updated_at_to"}:
                    if not isinstance(value, str):
                        raise TypeError(f"Filter '{key}' must be an ISO-8601 timestamp string.")
                    import re
                    iso_regex = r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2}(\.\d{1,6})?)?(Z|[\+\-]\d{2}:?\d{2})?)?$"
                    if not re.match(iso_regex, value):
                        raise ValueError(f"Filter '{key}' must be a valid ISO-8601 timestamp.")

        # Validate includes
        include_values: List[str] = []
        if _include:
            include_values = [v.strip() for v in _include.split(",") if v.strip()]
            invalid_includes = [v for v in include_values if v not in ALLOWED_INCLUDE_VALUES]
            if invalid_includes:
                raise ValueError(f"'include' parameter does not support following values: {invalid_includes}")

        # Validate pagination - only apply pagination if page parameter is provided
        size = None  # No pagination by default
        number = 1
        if page:
            size = page.get("size", 10)  # Default to 10 only if page is provided
            number = page.get("number", 1)
            if not isinstance(size, int) or size <= 0 or size > 100:
                raise ValueError("'size' must be an integer between 1 and 100 (inclusive).")
            if not isinstance(number, int) or number <= 0:
                raise ValueError("'number' must be an integer greater than zero.")

        # Data fetch - ensure we have the right structure
        suppliers_section = db.DB.get("suppliers", {})
        companies_dict = suppliers_section.get("supplier_companies", {})
        
        # Convert to list of properly formatted supplier company objects
        companies: List[Dict[str, Any]] = []
        for company_id, company_data in companies_dict.items():
            if not isinstance(company_data, dict):
                continue
                
            # Create proper API-compliant company object
            company_obj = {
                "type": "supplier_companies",
                "id": str(company_data.get("id", company_id)),
                "attributes": {},
                "relationships": company_data.get("relationships", {}),
                "links": {
                    "self": f"https://api.us.workdayspend.com/services/suppliers/v1/supplier_companies/{company_data.get('id', company_id)}"
                }
            }
            
            # Handle attributes - either from nested structure or flat structure
            if "attributes" in company_data:
                company_obj["attributes"] = company_data["attributes"].copy()
            else:
                # Convert flat structure to attributes
                for key, value in company_data.items():
                    if key not in ["id", "type", "relationships", "links"]:
                        company_obj["attributes"][key] = value
            
            # Ensure required attributes have default values if missing
            default_attributes = {
                "name": "",
                "description": "",
                "is_suggested": False,
                "public": False,
                "risk": "",
                "segmentation": "",
                "segmentation_status": "",
                "segmentation_notes": "",
                "tags": [],
                "url": "",
                "duns_number": "",
                "external_id": "",
                "self_registered": False,
                "onboarding_form_completion_status": None,
                "accept_all_currencies": False,
                "updated_at": "",
                "custom_fields": []
            }
            
            for attr_key, default_value in default_attributes.items():
                if attr_key not in company_obj["attributes"]:
                    company_obj["attributes"][attr_key] = default_value
            
            companies.append(company_obj)

        # Apply filters
        if filter:
            companies = apply_company_filters(companies, filter)

        # Apply pagination only if size is specified
        if size is not None:
            start_idx = (number - 1) * size
            paginated_companies = companies[start_idx : start_idx + size]
            total_pages = max(1, (len(companies) + size - 1) // size) if companies else 1
        else:
            # No pagination - return all results
            paginated_companies = companies
            total_pages = 1

        # Inclusion
        included_resources: List[Dict[str, Any]] = []
        for comp in paginated_companies:
            included_resources.extend(collect_included_resources(comp, include_values))

        # Deduplicate based on (type, id)
        unique = {}
        for res in included_resources:
            unique[(res.get("type"), res.get("id"))] = res
        included_deduped = list(unique.values()) if unique else []

        # Build response according to API documentation
        response: Dict[str, Any] = {
            "data": paginated_companies,
            "meta": {"count": total_pages},
            "links": {
                "self": "https://api.us.workdayspend.com/services/suppliers/v1/supplier_companies",
                "next": None,
                "prev": None,
            },
        }

        if include_values and included_deduped:
            response["included"] = included_deduped

        return response, 200
        
    except (TypeError, ValueError) as exc:
        return {"errors": [{"detail": str(exc)}]}, 400

@tool_spec(
    spec={
        'name': 'create_supplier_company',
        'description': """ Creates a new supplier company with specified attributes, linked resources, and optional custom fields.
        
        Supports internal and external ID references via `external_` prefixes for relationships. Allows compound creation via `include` parameter to return related resources in one request. """,
        'parameters': {
            'type': 'object',
            'properties': {
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated list of related resources to include in the response.
                    - Enum: "attachments", "supplier_category", "supplier_groups", "default_payment_term",
                    "payment_types", "default_payment_type", "payment_currencies",
                    "default_payment_currency", "supplier_classification_values" """
                },
                'body': {
                    'type': 'object',
                    'description': """ JSON API compliant supplier company payload. Must contain:
                    - external_... (Optional[dict] or Optional[list]): Use `external_` prefix for external ID references.
                        - external_supplier_category
                        - external_supplier_groups
                        - external_default_payment_term
                        - external_payment_types
                        - external_default_payment_type
                        - external_payment_currencies
                        - external_default_payment_currency
                        - external_supplier_classification_values """,
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Required. Must be "supplier_companies".'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': "Required. Contains the supplier's attributes:",
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Required. Supplier company name.'
                                },
                                'description': {
                                    'type': 'string',
                                    'description': 'Company description.'
                                },
                                'public': {
                                    'type': 'boolean',
                                    'description': 'Whether the company is public.'
                                },
                                'risk': {
                                    'type': 'string',
                                    'description': 'Risk classification (slug).'
                                },
                                'segmentation': {
                                    'type': 'string',
                                    'description': 'Segmentation type (slug).'
                                },
                                'segmentation_status': {
                                    'type': 'string',
                                    'description': 'Segmentation status (slug).'
                                },
                                'segmentation_notes': {
                                    'type': 'string',
                                    'description': 'Notes for segmentation.'
                                },
                                'tags': {
                                    'type': 'array',
                                    'description': 'Associated tags.',
                                    'items': {
                                        'type': 'string'
                                    }
                                },
                                'url': {
                                    'type': 'string',
                                    'description': 'Supplier website.'
                                },
                                'duns_number': {
                                    'type': 'string',
                                    'description': 'D-U-N-S® number.'
                                },
                                'external_id': {
                                    'type': 'string',
                                    'description': 'External system identifier.'
                                },
                                'self_registered': {
                                    'type': 'boolean',
                                    'description': 'Whether supplier self-registered.'
                                },
                                'onboarding_form_completion_status': {
                                    'type': 'string',
                                    'description': """ Onboarding status.
                                             - Enum: null, "not_started", "in_progress", "completed" """
                                },
                                'accept_all_currencies': {
                                    'type': 'boolean',
                                    'description': 'Accepts all currencies.'
                                },
                                'custom_fields': {
                                    'type': 'array',
                                    'description': """ List of custom fields.
                                             - Supported types: "Checkbox", "Short Text", "Paragraph", "Date", "Integer",
                                                               "Currency", "Decimal", "Single Select", "Multiple Select",
                                                               "URL", "Lookup", "Related" """,
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'name': {
                                                'type': 'string',
                                                'description': 'Field name.'
                                            },
                                            'value': {
                                                'type': 'object',
                                                'description': 'Field value.',
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
                            'required': [
                                'name'
                            ]
                        },
                        'relationships': {
                            'type': 'object',
                            'description': """ Resource links.
                                 - supplier_category
                                - supplier_groups
                                - default_payment_term
                                - payment_types
                                - default_payment_type
                                - payment_currencies
                                - default_payment_currency
                                - attachments
                                - supplier_classification_values """,
                            'properties': {},
                            'required': []
                        }
                    },
                    'required': [
                        'type',
                        'attributes'
                    ]
                }
            },
            'required': []
        }
    }
)
def post(_include: Optional[str] = None,
         body: Optional[Dict[str, Union[str, Dict[str, Union[str, bool, List[str], List[Dict[str, Union[str, int, bool, float, List[str], Dict[str, str]]]]]], Dict[str, Union[Dict[str, str], List[Dict[str, str]]]]]]] = None) -> Tuple[Dict[str, Union[str, int, Dict[str, Union[str, bool, List[str], List[Dict[str, Union[str, int, bool, float, List[str], Dict[str, str]]]]]], Dict[str, Union[Dict[str, str], List[Dict[str, str]]]]]], int]:
    """
    Creates a new supplier company with specified attributes, linked resources, and optional custom fields.

    Supports internal and external ID references via `external_` prefixes for relationships. Allows compound creation via `include` parameter to return related resources in one request.

    Args:
        _include (Optional[str]): Comma-separated list of related resources to include in the response.
            - Enum: "attachments", "supplier_category", "supplier_groups", "default_payment_term",
                    "payment_types", "default_payment_type", "payment_currencies",
                    "default_payment_currency", "supplier_classification_values"

        body (Optional[Dict[str, Union[str, Dict[str, Union[str, bool, List[str], List[Dict[str, Union[str, int, bool, float, List[str], Dict[str, str]]]]]], Dict[str, Union[Dict[str, str], List[Dict[str, str]]]]]]]): JSON API compliant supplier company payload. Must contain:
            - type (str): Required. Must be "supplier_companies".
            - attributes (Dict[str, Union[str, bool, List[str], List[Dict[str, Union[str, int, bool, float, List[str], Dict[str, str]]]]]]): Required. Contains the supplier's attributes:
                - name (str): Required. Supplier company name.
                - description (Optional[str]): Company description.
                - public (Optional[bool]): Whether the company is public.
                - risk (Optional[str]): Risk classification (slug).
                - segmentation (Optional[str]): Segmentation type (slug).
                - segmentation_status (Optional[str]): Segmentation status (slug).
                - segmentation_notes (Optional[str]): Notes for segmentation.
                - tags (Optional[List[str]]): Associated tags.
                - url (Optional[str]): Supplier website.
                - duns_number (Optional[str]): D-U-N-S® number.
                - external_id (Optional[str]): External system identifier.
                - self_registered (Optional[bool]): Whether supplier self-registered.
                - onboarding_form_completion_status (Optional[str]): Onboarding status.
                    - Enum: null, "not_started", "in_progress", "completed"
                - accept_all_currencies (Optional[bool]): Accepts all currencies.
                - custom_fields (Optional[List[Dict[str, Any]]]): List of custom fields.
                    - name (str): Field name.
                    - value (Any): Field value.
                    - Supported types: "Checkbox", "Short Text", "Paragraph", "Date", "Integer",
                                       "Currency", "Decimal", "Single Select", "Multiple Select",
                                       "URL", "Lookup", "Related"
            - relationships (Optional[Dict[str, Any]]): Resource links.
                - supplier_category
                - supplier_groups
                - default_payment_term
                - payment_types
                - default_payment_type
                - payment_currencies
                - default_payment_currency
                - attachments
                - supplier_classification_values

            - external_... (Optional[dict] or Optional[list]): Use `external_` prefix for external ID references.
                - external_supplier_category
                - external_supplier_groups
                - external_default_payment_term
                - external_payment_types
                - external_default_payment_type
                - external_payment_currencies
                - external_default_payment_currency
                - external_supplier_classification_values

    Returns:
        Tuple[Dict[str, Union[str, int, Dict[str, Union[str, bool, List[str], List[Dict[str, Union[str, int, bool, float, List[str], Dict[str, str]]]]]], Dict[str, Union[Dict[str, str], List[Dict[str, str]]]]]], int]: Response body and HTTP status code.
        
        Success response (201):
            - data (Dict[str, Any]):
                - type (str): Always "supplier_companies".
                - id (int): Unique supplier company identifier.
                - attributes (Dict[str, Any]):
                    - name (str)
                    - description (str)
                    - is_suggested (bool)
                    - public (bool)
                    - risk (str)
                    - segmentation (str)
                    - segmentation_status (str)
                    - segmentation_notes (str)
                    - tags (List[str])
                    - url (str)
                    - duns_number (str)
                    - external_id (str)
                    - self_registered (bool)
                    - onboarding_form_completion_status (str)
                    - accept_all_currencies (bool)
                    - updated_at (str)
                    - custom_fields (List[Dict[str, Any]]):
                        - name (str)
                        - value (Any)
                - relationships (Optional[Dict[str, Any]]): Resource links. Supports standard resource linkage or `external_` prefixed keys for external ID references.
                    - supplier_category (Optional[dict]): Linkage object.
                        - type (Optional[str]): Should always be "supplier_categories"
                        - id (Optional[str]): Supplier category identifier string
                    - supplier_groups (Optional[list]): List of linkage objects.
                        - type (Optional[str]): Should always be "supplier_groups"
                        - id (Optional[str]): Supplier group identifier string
                    - default_payment_term (Optional[dict]): Linkage object.
                        - type (Optional[str]): Should always be "payment_terms"
                        - id (Optional[str]): Payment term identifier string
                    - payment_types (Optional[list]): List of linkage objects.
                    - default_payment_type (Optional[dict]): Linkage object.
                        - type (Optional[str]): Should always be "payment_types"
                        - id (Optional[str]): Payment type identifier string
                    - payment_currencies (Optional[list]): List of linkage objects.
                    - default_payment_currency (Optional[dict]): Linkage object.
                        - type (Optional[str]): Should always be "payment_currencies"
                        - id (Optional[str]): Payment currency identifier string
                    - attachments (Optional[list[dict]]): List of linkage objects.
                        - type (Optional[str]): Should always be "attachments"
                        - id (Optional[str]): Attachment identifier string
                    - supplier_classification_values (Optional[list]): List of linkage objects.
                    - external_supplier_category (Optional[dict]): External ID reference.
                        - type (Optional[str]): Should always be "supplier_categories"
                        - id (Optional[str]): Supplier category identifier string
                    - external_supplier_groups (Optional[list]): List of external ID references.
                    - external_default_payment_term (Optional[dict]): External ID reference.
                    - external_payment_types (Optional[list]): List of external ID references.
                    - external_default_payment_type (Optional[dict]): External ID reference.
                        - type (Optional[str]): Should always be "payment_types"
                        - id (Optional[str]): Payment type identifier string
                    - external_payment_currencies (Optional[list]): List of external ID references.
                    - external_default_payment_currency (Optional[dict]): External ID reference.
                        - type (Optional[str]): Should always be "payment_currencies"
                        - id (Optional[str]): Payment currency identifier string
                    - external_supplier_classification_values (Optional[list]): List of external ID references.

    Raises:
        ValueError: When validation fails or invalid data is provided.
            - Body is required
            - Invalid include options
            - Invalid supplier company data
            - Unexpected errors during processing
    """
    try:
        if not body:
            raise ValueError("Body is required")

        # Validate include parameter
        if _include:
            include_options = [opt.value for opt in IncludeOptions]
            provided_includes = [inc.strip() for inc in _include.split(',')]
            invalid_includes = [inc for inc in provided_includes if inc not in include_options]
            if invalid_includes:
                raise ValueError(f"Invalid include options: {', '.join(invalid_includes)}. "
                               f"Valid options: {', '.join(include_options)}")

        # Validate and parse the request body
        # Extract attributes from JSON API structure
        attributes = body.get("attributes", {})
        if not attributes:
            raise ValueError("Body must contain 'attributes' object")
        
        supplier_data = SupplierCompanyCreate(**attributes)

        # Create the company record
        company_id = len(db.DB["suppliers"]["supplier_companies"]) + 1
        company_dict = supplier_data.model_dump(exclude_none=True)
        company = {"id": company_id, **company_dict}

        # Store in database
        db.DB["suppliers"]["supplier_companies"][company_id] = company

        # Handle include logic (simplified)
        if _include:
            # Simulate include logic (not fully implemented)
            pass

        # Return the created company
        response_data = SupplierCompanyResponse(
            id=company_id,
            attributes=company_dict,
            relationships={}  # Simplified for now
        )
        return response_data.model_dump(), 201

    except ValueError as e:
        raise ValueError(str(e))
    except Exception as e:
        raise ValueError(f"Unexpected error: {str(e)}")
