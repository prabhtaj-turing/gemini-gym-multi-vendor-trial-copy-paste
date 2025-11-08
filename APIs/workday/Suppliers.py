"""
Suppliers Management Module

This module provides functionality for managing suppliers in the Workday Strategic
Sourcing system. It supports operations for retrieving supplier information,
including both bulk retrieval of all suppliers and individual supplier lookup.

The module interfaces with the simulation database to provide comprehensive
supplier management capabilities, allowing users to:
- Retrieve a list of all suppliers in the system
- Look up individual suppliers by their unique identifier
"""
from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, List, Tuple, Any
from .SimulationEngine import db
from .SimulationEngine.utils import (
    ALLOWED_FILTER_KEYS,
    ALLOWED_INCLUDE_VALUES,
    apply_company_filters,
    collect_included_resources,
)
from .SimulationEngine.custom_errors import (
    SupplierNotFoundError, 
    InvalidInputError
)

@tool_spec(
    spec={
        'name': 'list_all_suppliers',
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
                        },
                        'name': {
                            'type': 'string',
                            'description': 'Exact match on name.'
                        },
                        'risk': {
                            'type': 'string',
                            'description': 'Exact match on risk.'
                        }
                    },
                    'required': [
                        'updated_at_from',
                        'updated_at_to',
                        'external_id_empty',
                        'external_id_not_empty',
                        'external_id_equals',
                        'external_id_not_equals',
                        'segmentation_status_equals',
                        'name',
                        'risk'
                    ]
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
def get_suppliers(
    filter: Optional[Dict[str, Any]] = None,
    _include: Optional[str] = None,
    page: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Any], int]:
    """Retrieve supplier companies with optional filtering, inclusion and pagination.

    Args:
        filter (Optional[Dict[str, Any]]): Filter criteria with allowed keys and expected value types.
            - updated_at_from (str): ISO-8601 timestamp. Include companies updated on or after this time.
            - updated_at_to (str): ISO-8601 timestamp. Include companies updated on or before this time.
            - external_id_empty (bool): Only companies whose external_id is empty.
            - external_id_not_empty (bool): Only companies whose external_id is not empty.
            - external_id_equals (str): Exact match on external_id.
            - external_id_not_equals (str): Exclude this external_id value.
            - segmentation_status_equals (List[str] | str): Any of the given segmentation statuses.
            - name (str): Exact match on name.
            - risk (str): Exact match on risk.
        _include (Optional[str]): Comma-separated list of related resources to embed. Allowed values:
            "attachments", "supplier_category", "supplier_groups", "default_payment_term",
            "payment_types", "default_payment_type", "payment_currencies", "default_payment_currency",
            "supplier_classification_values".
        page (Optional[Dict[str, Any]]): Pagination settings.
            - size (int): Page size between 1 and 100. Default 10.
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
        
        Error response (400):
            - errors (List[Dict[str, str]]): Array of error objects.
                - detail (str): A human-readable explanation specific to this occurrence of the problem.

    Raises:
        TypeError: If any of the following validation fails:
            - filter is not None and not a dictionary
            - _include is not None and not a string
            - page is not None and not a dictionary
            - filter values have incorrect types (e.g., boolean fields not bool, string fields not str)
        ValueError: If any of the following validation fails:
            - Unknown filter keys are provided
            - Invalid ISO-8601 timestamp format for date filters
            - Invalid include parameter values
            - Invalid pagination parameters (size not between 1-100, number not positive)
        
        Note: These exceptions are caught internally and returned as 400 Bad Request responses.
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

                elif key in {"external_id_equals", "external_id_not_equals", "name", "risk"}:
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

        # Validate pagination
        size = 10
        number = 1
        if page:
            size = page.get("size", size)
            number = page.get("number", number)
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

        # Pagination
        start_idx = (number - 1) * size
        paginated_companies = companies[start_idx : start_idx + size]
        total_pages = max(1, (len(companies) + size - 1) // size) if companies else 1

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
        'name': 'get_supplier_by_id',
        'description': """ Retrieves the details of an existing supplier company by its unique ID.
        
        This function searches for a supplier in the database by their ID and returns
        the supplier object if found, or raises a SupplierNotFoundError if not found. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'supplier_id': {
                    'type': 'integer',
                    'description': 'Unique identifier of the supplier company to retrieve.'
                }
            },
            'required': [
                'supplier_id'
            ]
        }
    }
)
def get_supplier(supplier_id: int) -> Dict[str, Any]:
    """
    Retrieves the details of an existing supplier company by its unique ID.

    This function searches for a supplier in the database by their ID and returns
    the supplier object if found, or raises a SupplierNotFoundError if not found.

    Args:
        supplier_id (int): Unique identifier of the supplier company to retrieve.

    Returns:
        Dict[str, Any]: The supplier company object if found.
            The supplier object contains:
                - id (str): Unique supplier company identifier.
                - name (str): Supplier company name.
                - industry (str): Industry category of the supplier.
                - contact_email (str): Contact email address for the supplier.

    Raises:
        SupplierNotFoundError: If the supplier with the specified ID is not found.
        InvalidInputError: If the supplier_id is not a positive integer.
    """
    
    # Input validation
    if not isinstance(supplier_id, int):
        raise InvalidInputError("supplier_id must be an integer")
    if supplier_id <= 0:
        raise InvalidInputError("supplier_id must be a positive integer")

    suppliers = db.DB["reports"].get('suppliers', [])
    for supplier in suppliers:
        if supplier.get('id') == supplier_id:
            return supplier
    
    raise SupplierNotFoundError(f"Supplier with ID {supplier_id} not found") 

