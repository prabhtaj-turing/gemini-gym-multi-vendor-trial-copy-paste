"""
Supplier Company Contacts Management by External ID Module

This module provides functionality for managing contacts associated with supplier
companies in the Workday Strategic Sourcing system using the company's external
identifier. It supports operations for retrieving and filtering contacts for a
specific supplier company.

The module interfaces with the simulation database to provide comprehensive contact
management capabilities, allowing users to:
- Retrieve all contacts for a specific supplier company using its external ID
- Filter contacts based on specific criteria
- Include related resources in the response
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, List, Tuple, Union
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'get_supplier_company_contacts_by_external_id',
        'description': """ Retrieves contacts associated with a supplier company by external identifier.
        
        This function returns all contacts for a specific supplier company and optionally
        filters them based on provided criteria. The external ID must match the one used
        when the company was created. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': """ Required. External identifier of the supplier company.
                    Example: "COMP-001" """
                },
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated list of related resources to include.
                    Currently not fully implemented. """
                },
                'filter': {
                    'type': 'object',
                    'description': """ Optional filter criteria to apply to contacts.
                    Each key-value pair in the dictionary will be used to filter contacts. Possible filter keys: """,
                    'properties': {
                        'updated_at_from': {
                            'type': 'string',
                            'description': 'Return supplier contacts updated on or after the specified timestamp.'
                        },
                        'updated_at_to': {
                            'type': 'string',
                            'description': 'Return supplier contacts updated on or before the specified timestamp.'
                        },
                        'name_contains': {
                            'type': 'string',
                            'description': 'Return supplier contacts with a specific name.'
                        },
                        'name_not_contains': {
                            'type': 'string',
                            'description': 'Return supplier contacts with a name that does not contain a given value.'
                        },
                        'first_name_contains': {
                            'type': 'string',
                            'description': 'Return supplier contacts with a specific first_name.'
                        },
                        'first_name_not_contains': {
                            'type': 'string',
                            'description': 'Return supplier contacts with a first name that does not contain a given value.'
                        },
                        'last_name_contains': {
                            'type': 'string',
                            'description': 'Return supplier contacts with a specific last_name.'
                        },
                        'last_name_not_contains': {
                            'type': 'string',
                            'description': 'Return supplier contacts with a last name that does not contain a given value.'
                        },
                        'email_equals': {
                            'type': 'string',
                            'description': 'Find supplier contacts by a specific email.'
                        },
                        'email_not_equals': {
                            'type': 'string',
                            'description': 'Find supplier contacts excluding the one with the specified email.'
                        },
                        'email_contains': {
                            'type': 'string',
                            'description': 'Find supplier contacts by a specific email.'
                        },
                        'email_not_contains': {
                            'type': 'string',
                            'description': 'Find supplier contacts excluding the one with the specified email.'
                        },
                        'phone_number_contains': {
                            'type': 'string',
                            'description': 'Find supplier contacts by a specific phone.'
                        },
                        'phone_number_not_contains': {
                            'type': 'string',
                            'description': 'Find supplier contacts excluding the one with the specified phone.'
                        },
                        'phone_number_empty': {
                            'type': 'boolean',
                            'description': 'Return supplier companies with phone blank.'
                        },
                        'phone_number_not_empty': {
                            'type': 'boolean',
                            'description': 'Return supplier companies with non-blank phone.'
                        },
                        'job_title_contains': {
                            'type': 'string',
                            'description': 'Find supplier contacts by a specific job title.'
                        },
                        'job_title_not_contains': {
                            'type': 'string',
                            'description': 'Find supplier contacts excluding the one with the specified job title.'
                        },
                        'job_title_empty': {
                            'type': 'boolean',
                            'description': 'Return supplier companies with job_title blank.'
                        },
                        'job_title_not_empty': {
                            'type': 'boolean',
                            'description': 'Return supplier companies with non-blank job_title.'
                        },
                        'notes_contains': {
                            'type': 'string',
                            'description': 'Find supplier contacts by a specific notes.'
                        },
                        'notes_not_contains': {
                            'type': 'string',
                            'description': 'Find supplier contacts excluding the one with the specified notes.'
                        },
                        'notes_empty': {
                            'type': 'boolean',
                            'description': 'Return supplier companies with notes blank.'
                        },
                        'notes_not_empty': {
                            'type': 'boolean',
                            'description': 'Return supplier companies with non-blank notes.'
                        },
                        'is_suggested_equals': {
                            'type': 'boolean',
                            'description': 'Find only suggested supplier contacts.'
                        },
                        'is_suggested_not_equals': {
                            'type': 'boolean',
                            'description': 'Find supplier contacts that were approved.'
                        },
                        'external_id_empty': {
                            'type': 'boolean',
                            'description': 'Return supplier contacts with external_id blank.'
                        },
                        'external_id_not_empty': {
                            'type': 'boolean',
                            'description': 'Return supplier contacts with non-blank external_id.'
                        },
                        'external_id_equals': {
                            'type': 'string',
                            'description': 'Find supplier contacts by a specific external ID.'
                        },
                        'external_id_not_equals': {
                            'type': 'string',
                            'description': 'Find supplier contacts excluding the one with the specified external ID.'
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def get(external_id: str, _include: Optional[str] = None, 
        filter: Optional[Dict[str, Any]] = None) -> Tuple[Union[List[Dict[str, Any]], Dict[str, str]], int]:
    """
    Retrieves contacts associated with a supplier company by external identifier.

    This function returns all contacts for a specific supplier company and optionally
    filters them based on provided criteria. The external ID must match the one used
    when the company was created.

    Args:
        external_id (str): Required. External identifier of the supplier company.
            Example: "COMP-001"

        _include (Optional[str]): Comma-separated list of related resources to include.
            Currently not fully implemented.

        filter (Optional[Dict[str, Any]]): Optional filter criteria to apply to contacts.
            Each key-value pair in the dictionary will be used to filter contacts. Possible filter keys:
            - updated_at_from (Optional[str]): Return supplier contacts updated on or after the specified timestamp.
            - updated_at_to (Optional[str]): Return supplier contacts updated on or before the specified timestamp.
            - name_contains (Optional[str]): Return supplier contacts with a specific name.
            - name_not_contains (Optional[str]): Return supplier contacts with a name that does not contain a given value.
            - first_name_contains (Optional[str]): Return supplier contacts with a specific first_name.
            - first_name_not_contains (Optional[str]): Return supplier contacts with a first name that does not contain a given value.
            - last_name_contains (Optional[str]): Return supplier contacts with a specific last_name.
            - last_name_not_contains (Optional[str]): Return supplier contacts with a last name that does not contain a given value.
            - email_equals (Optional[str]): Find supplier contacts by a specific email.
            - email_not_equals (Optional[str]): Find supplier contacts excluding the one with the specified email.
            - email_contains (Optional[str]): Find supplier contacts by a specific email.
            - email_not_contains (Optional[str]): Find supplier contacts excluding the one with the specified email.
            - phone_number_contains (Optional[str]): Find supplier contacts by a specific phone.
            - phone_number_not_contains (Optional[str]): Find supplier contacts excluding the one with the specified phone.
            - phone_number_empty (Optional[bool]): Return supplier companies with phone blank.
            - phone_number_not_empty (Optional[bool]): Return supplier companies with non-blank phone.
            - job_title_contains (Optional[str]): Find supplier contacts by a specific job title.
            - job_title_not_contains (Optional[str]): Find supplier contacts excluding the one with the specified job title.
            - job_title_empty (Optional[bool]): Return supplier companies with job_title blank.
            - job_title_not_empty (Optional[bool]): Return supplier companies with non-blank job_title.
            - notes_contains (Optional[str]): Find supplier contacts by a specific notes.
            - notes_not_contains (Optional[str]): Find supplier contacts excluding the one with the specified notes.
            - notes_empty (Optional[bool]): Return supplier companies with notes blank.
            - notes_not_empty (Optional[bool]): Return supplier companies with non-blank notes.
            - is_suggested_equals (Optional[bool]): Find only suggested supplier contacts.
            - is_suggested_not_equals (Optional[bool]): Find supplier contacts that were approved.
            - external_id_empty (Optional[bool]): Return supplier contacts with external_id blank.
            - external_id_not_empty (Optional[bool]): Return supplier contacts with non-blank external_id.
            - external_id_equals (Optional[str]): Find supplier contacts by a specific external ID.
            - external_id_not_equals (Optional[str]): Find supplier contacts excluding the one with the specified external ID.

    Returns:
        Tuple[Union[List[Dict[str, Any]], Dict[str, str]], int]: A tuple containing:
            - First element (Union[List[Dict[str, Any]], Dict[str, str]]): Either a list of contact dictionaries or an error dictionary
            - Second element (int): HTTP status code (200 for success, 404 for not found)

            Contact dictionary structure:
                - id (int): Internal unique identifier of the contact
                - company_id (int): ID of the associated supplier company
                - name (str): Contact's full name
                - email (str): Contact's email address
                - phone (Optional[str]): Contact's phone number
                - title (Optional[str]): Contact's job title
                - active (bool): Whether the contact is active
    """

    company_id = None
    for company in db.DB["suppliers"]["supplier_companies"].values():
        if company.get("external_id") == external_id:
            company_id = company.get("id")
            break
    if company_id is None:
        return {"error": "Company not found"}, 404
    
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