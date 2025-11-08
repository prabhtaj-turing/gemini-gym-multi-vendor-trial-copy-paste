"""
Supplier Company Contacts Management Module

This module provides functionality for managing contacts associated with supplier
companies in the Workday Strategic Sourcing system. It supports operations for
retrieving and filtering contacts for a specific supplier company.

The module interfaces with the simulation database to provide comprehensive contact
management capabilities, allowing users to:
- Retrieve all contacts for a specific supplier company
- Filter contacts based on specific criteria
- Include related resources in the response
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, List, Tuple
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'list_supplier_company_contacts_by_company_external_id',
        'description': """ Retrieves a list of contacts for a specific supplier company.
        
        This function returns supplier contacts associated with a given supplier company ID.
        Supports detailed filtering, relationship includes, and pagination options. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'company_id': {
                    'type': 'integer',
                    'description': """ Required. Unique identifier of the supplier company.
                    Example: 1 """
                },
                '_include': {
                    'type': 'string',
                    'description': 'Comma-separated list of related resources to include in the response. Allowed values: "supplier_company", "contact_types", "phones".'
                },
                'filter': {
                    'type': 'object',
                    'description': """ Dictionary of filter parameters to narrow down contact results.
                    All filter properties are optional and can be used in any combination.
                    Supported filters include: """,
                    'properties': {
                        'updated_at_from': {
                            'type': 'string',
                            'description': 'Return contacts updated on or after this timestamp.'
                        },
                        'updated_at_to': {
                            'type': 'string',
                            'description': 'Return contacts updated on or before this timestamp.'
                        },
                        'name_contains': {
                            'type': 'string',
                            'description': 'Filter contacts whose name contains the specified string.'
                        },
                        'name_not_contains': {
                            'type': 'string',
                            'description': 'Filter contacts whose name does not contain the specified string.'
                        },
                        'first_name_contains': {
                            'type': 'string',
                            'description': 'Filter contacts whose first name contains the specified string.'
                        },
                        'first_name_not_contains': {
                            'type': 'string',
                            'description': 'Filter contacts whose first name does not contain the specified string.'
                        },
                        'last_name_contains': {
                            'type': 'string',
                            'description': 'Filter contacts whose last name contains the specified string.'
                        },
                        'last_name_not_contains': {
                            'type': 'string',
                            'description': 'Filter contacts whose last name does not contain the specified string.'
                        },
                        'email_equals': {
                            'type': 'string',
                            'description': 'Filter contacts with exact email match.'
                        },
                        'email_not_equals': {
                            'type': 'string',
                            'description': 'Filter contacts without exact email match.'
                        },
                        'email_contains': {
                            'type': 'string',
                            'description': 'Filter contacts whose email contains the specified string.'
                        },
                        'email_not_contains': {
                            'type': 'string',
                            'description': 'Filter contacts whose email does not contain the specified string.'
                        },
                        'phone_number_contains': {
                            'type': 'string',
                            'description': 'Filter contacts whose phone number contains the specified string.'
                        },
                        'phone_number_not_contains': {
                            'type': 'string',
                            'description': 'Filter contacts whose phone number does not contain the specified string.'
                        },
                        'phone_number_empty': {
                            'type': 'boolean',
                            'description': 'Filter contacts with empty phone numbers.'
                        },
                        'phone_number_not_empty': {
                            'type': 'boolean',
                            'description': 'Filter contacts with non-empty phone numbers.'
                        },
                        'job_title_contains': {
                            'type': 'string',
                            'description': 'Filter contacts whose job title contains the specified string.'
                        },
                        'job_title_not_contains': {
                            'type': 'string',
                            'description': 'Filter contacts whose job title does not contain the specified string.'
                        },
                        'job_title_empty': {
                            'type': 'boolean',
                            'description': 'Filter contacts with empty job titles.'
                        },
                        'job_title_not_empty': {
                            'type': 'boolean',
                            'description': 'Filter contacts with non-empty job titles.'
                        },
                        'notes_contains': {
                            'type': 'string',
                            'description': 'Filter contacts whose notes contain the specified string.'
                        },
                        'notes_not_contains': {
                            'type': 'string',
                            'description': 'Filter contacts whose notes do not contain the specified string.'
                        },
                        'notes_empty': {
                            'type': 'boolean',
                            'description': 'Filter contacts with empty notes.'
                        },
                        'notes_not_empty': {
                            'type': 'boolean',
                            'description': 'Filter contacts with non-empty notes.'
                        },
                        'is_suggested_equals': {
                            'type': 'boolean',
                            'description': 'Filter contacts by suggestion status.'
                        },
                        'is_suggested_not_equals': {
                            'type': 'boolean',
                            'description': 'Filter contacts by non-suggestion status.'
                        },
                        'external_id_equals': {
                            'type': 'string',
                            'description': 'Filter contacts with exact external ID match.'
                        },
                        'external_id_not_equals': {
                            'type': 'string',
                            'description': 'Filter contacts without exact external ID match.'
                        },
                        'external_id_empty': {
                            'type': 'boolean',
                            'description': 'Filter contacts with empty external IDs.'
                        },
                        'external_id_not_empty': {
                            'type': 'boolean',
                            'description': 'Filter contacts with non-empty external IDs.'
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'company_id'
            ]
        }
    }
)
def get(company_id: int, _include: Optional[str] = None, 
        filter: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], int]:
    """
    Retrieves a list of contacts for a specific supplier company.

    This function returns supplier contacts associated with a given supplier company ID.
    Supports detailed filtering, relationship includes, and pagination options.

    Args:
        company_id (int): Required. Unique identifier of the supplier company.
            Example: 1

        _include (Optional[str]): Comma-separated list of related resources to include in the response. Allowed values: "supplier_company", "contact_types", "phones".

        filter (Optional[Dict[str, Any]]): Dictionary of filter parameters to narrow down contact results.
            All filter properties are optional and can be used in any combination.
            Supported filters include:
                updated_at_from (Optional[str]): Return contacts updated on or after this timestamp.
                updated_at_to (Optional[str]): Return contacts updated on or before this timestamp.
                name_contains (Optional[str]): Filter contacts whose name contains the specified string.
                name_not_contains (Optional[str]): Filter contacts whose name does not contain the specified string.
                first_name_contains (Optional[str]): Filter contacts whose first name contains the specified string.
                first_name_not_contains (Optional[str]): Filter contacts whose first name does not contain the specified string.
                last_name_contains (Optional[str]): Filter contacts whose last name contains the specified string.
                last_name_not_contains (Optional[str]): Filter contacts whose last name does not contain the specified string.
                email_equals (Optional[str]): Filter contacts with exact email match.
                email_not_equals (Optional[str]): Filter contacts without exact email match.
                email_contains (Optional[str]): Filter contacts whose email contains the specified string.
                email_not_contains (Optional[str]): Filter contacts whose email does not contain the specified string.
                phone_number_contains (Optional[str]): Filter contacts whose phone number contains the specified string.
                phone_number_not_contains (Optional[str]): Filter contacts whose phone number does not contain the specified string.
                phone_number_empty (Optional[bool]): Filter contacts with empty phone numbers.
                phone_number_not_empty (Optional[bool]): Filter contacts with non-empty phone numbers.
                job_title_contains (Optional[str]): Filter contacts whose job title contains the specified string.
                job_title_not_contains (Optional[str]): Filter contacts whose job title does not contain the specified string.
                job_title_empty (Optional[bool]): Filter contacts with empty job titles.
                job_title_not_empty (Optional[bool]): Filter contacts with non-empty job titles.
                notes_contains (Optional[str]): Filter contacts whose notes contain the specified string.
                notes_not_contains (Optional[str]): Filter contacts whose notes do not contain the specified string.
                notes_empty (Optional[bool]): Filter contacts with empty notes.
                notes_not_empty (Optional[bool]): Filter contacts with non-empty notes.
                is_suggested_equals (Optional[bool]): Filter contacts by suggestion status.
                is_suggested_not_equals (Optional[bool]): Filter contacts by non-suggestion status.
                external_id_equals (Optional[str]): Filter contacts with exact external ID match.
                external_id_not_equals (Optional[str]): Filter contacts without exact external ID match.
                external_id_empty (Optional[bool]): Filter contacts with empty external IDs.
                external_id_not_empty (Optional[bool]): Filter contacts with non-empty external IDs.

    Returns:
        Tuple[List[Dict[str, Any]], int]: A tuple containing:
            - First element (List[Dict[str, Any]]): A list of supplier contacts. It can contain the following keys:
                - type (str): Always "supplier_contacts".
                - id (int): Unique identifier of the contact.
                - attributes (Dict[str, Any]):
                    - name (str): Full name (≤ 255 characters).
                    - first_name (Optional[str]): First name.
                    - last_name (Optional[str]): Last name.
                    - email (str): Contact email (≤ 255 characters).
                    - notes (Optional[str]): Additional notes.
                    - phone_number (Optional[str]): Deprecated field for phone.
                    - job_title (Optional[str]): Contact job title.
                    - external_id (Optional[str]): Internal system ID.
                    - is_suggested (bool): True if contact is a suggestion.
                    - updated_at (str): Last updated timestamp (ISO 8601).

                - relationships (Dict[str, Any]):
                    - supplier_company (Dict): Linked supplier company.
                        - data: { id (int), type (str) }
                    - contact_types (List[Dict]): Associated contact types.
                    - phones (List[Dict]): Linked phone numbers (max 1).

            - Second element (int): HTTP status code. It is 200 for success.

    """

    contacts = [c for c in db.DB["suppliers"]["supplier_contacts"].values() if c.get("company_id") == company_id]
    if filter:
        filtered_contacts = []
        for contact in contacts:
            match = True
            for key, value in filter.items():
                if contact.get(key) != value:
                    match = False
                    break
            if match:
                filtered_contacts.append(contact)
        contacts = filtered_contacts
    if _include:
        # Simulate include logic (not fully implemented)
        pass
    return contacts, 200 
