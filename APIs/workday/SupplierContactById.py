"""
Supplier Contact Management by ID Module

This module provides functionality for managing individual supplier contacts using
their unique internal identifiers in the Workday Strategic Sourcing system. It
supports operations for retrieving, updating, and deleting supplier contact records.

The module interfaces with the simulation database to provide comprehensive supplier
contact management capabilities, allowing users to:
- Retrieve detailed supplier contact information
- Update existing supplier contact records
- Delete supplier contact entries
- Handle related resource inclusion where applicable

Functions:
    get: Retrieves supplier contact details by ID
    patch: Updates supplier contact details by ID
    delete: Deletes a supplier contact by ID
"""
from common_utils.tool_spec_decorator import tool_spec
from typing import Optional


from typing import Dict, Any, Tuple, Union
from .SimulationEngine import db

@tool_spec(
    spec={
        'name': 'get_supplier_contact_by_id',
        'description': """ Retrieves the details of an existing supplier contact by ID.
        
        This function returns full information about a supplier contact, including their
        attributes and optionally included related resources such as contact types, phones,
        and linked supplier company. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'Required. Unique identifier of the supplier contact.'
                },
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated list of related resources to include in the response.
                    Allowed values:
                    - "supplier_company"
                    - "contact_types"
                    - "phones" """
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def get(id: int, _include: str = None) -> Tuple[Union[Dict[str, Any], Dict[str, str]], int]:
    """
    Retrieves the details of an existing supplier contact by ID.

    This function returns full information about a supplier contact, including their
    attributes and optionally included related resources such as contact types, phones,
    and linked supplier company.

    Args:
        id (int): Required. Unique identifier of the supplier contact.
        _include (str): Comma-separated list of related resources to include in the response.
            Allowed values:
                - "supplier_company"
                - "contact_types"
                - "phones"

    Returns:
        Tuple[Union[Dict[str, Any], Dict[str, str]], int]: A tuple containing:
            - First element: Either the supplier contact details or an error message
            - Second element: HTTP status code (200 for success, 404 for not found)

            When successful (status 200), the first element contains:
            - data (Dict[str, Any]): Supplier contact resource.
                - type (str): Always "supplier_contacts".
                - id (int): Unique supplier contact identifier.

                - attributes (Dict[str, Any]):
                    - name (str): Full name of the contact (≤ 255 characters).
                    - first_name (Optional[str]): First name (≤ 255 characters).
                    - last_name (Optional[str]): Last name (≤ 255 characters).
                    - email (str): Email address (≤ 255 characters).
                    - notes (Optional[str]): Additional notes.
                    - phone_number (Optional[str]): Deprecated. Prefer the `phones` relationship.
                    - job_title (Optional[str]): Job title.
                    - external_id (Optional[str]): External reference ID from your system.
                    - is_suggested (Optional[bool]): Whether the contact is suggested and pending approval.
                    - updated_at (str): ISO 8601 timestamp of the last update.

                - relationships (Dict[str, Any]): Related entities.
                    - supplier_company (Dict[str, Any]):
                        - data: { id (int), type (str) }
                    - contact_types (Optional[Dict[str, Any]]):
                        - data: List[{ id (int), type (str) }]
                    - phones (Optional[Dict[str, Any]]):
                        - data: List[{ id (int), type (str) }] (limited to 1)

            When not found (status 404), the first element contains:
            - error (str): Error message "Contact not found"
    """

    contact = db.DB["suppliers"]["supplier_contacts"].get(id)
    if not contact:
        return {"error": "Contact not found"}, 404
    if _include:
        # Simulate include logic (not fully implemented)
        pass
    return contact, 200

@tool_spec(
    spec={
        'name': 'update_supplier_contact_by_id',
        'description': """ Updates the details of an existing supplier contact.
        
        This function modifies a supplier contact's attributes and optionally updates related
        contact types and phone records. The request body must include the `id` of the contact,
        which should match the path parameter. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'Required. Unique identifier of the supplier contact to be updated.'
                },
                '_include': {
                    'type': 'string',
                    'description': 'Comma-separated list of related resources to include in the response. It can be one of the following allowed values ["supplier_company", "contact_types", "phones"]'
                },
                'body': {
                    'type': 'object',
                    'description': 'Payload containing the updated supplier contact information.',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Required. Must be "supplier_contacts".'
                        },
                        'id': {
                            'type': 'integer',
                            'description': 'Required. Must match the `id` in the URL path.'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Supplier contact attributes object containing:',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Required unless both `first_name` and `last_name` are provided. Full name (≤ 255 chars).'
                                },
                                'first_name': {
                                    'type': 'string',
                                    'description': 'First name (≤ 255 chars).'
                                },
                                'last_name': {
                                    'type': 'string',
                                    'description': 'Last name (≤ 255 chars).'
                                },
                                'email': {
                                    'type': 'string',
                                    'description': 'Required. Email address (≤ 255 chars).'
                                },
                                'notes': {
                                    'type': 'string',
                                    'description': 'Notes about the contact.'
                                },
                                'phone_number': {
                                    'type': 'string',
                                    'description': 'Deprecated. Prefer `phones` relationship.'
                                },
                                'job_title': {
                                    'type': 'string',
                                    'description': 'Job title of the contact.'
                                },
                                'external_id': {
                                    'type': 'string',
                                    'description': 'Internal reference ID.'
                                },
                                'is_suggested': {
                                    'type': 'boolean',
                                    'description': 'If the contact is unapproved or suggested.'
                                }
                            },
                            'required': [
                                'name',
                                'email'
                            ]
                        },
                        'relationships': {
                            'type': 'object',
                            'description': 'Contact relationships to update. Optional - only provide when updating relationships. Can be either:',
                            'properties': {
                                'SupplierContactRelationshipUpdate': {
                                    'type': 'object',
                                    'description': 'Internal relationship update object containing:',
                                    'properties': {
                                        'contact_types': {
                                            'type': 'array',
                                            'description': 'List of contact types for a contact.',
                                            'items': {
                                                'type': 'object',
                                                'properties': {
                                                    'type': {
                                                        'type': 'string',
                                                        'description': 'Object type, should always be "contact_types".'
                                                    },
                                                    'id': {
                                                        'type': 'integer',
                                                        'description': 'Contact type identifier.'
                                                    }
                                                },
                                                'required': [
                                                    'type',
                                                    'id'
                                                ]
                                            }
                                        },
                                        'phones': {
                                            'type': 'array',
                                            'description': 'List of phones for a contact.',
                                            'items': {
                                                'type': 'object',
                                                'properties': {
                                                    'type': {
                                                        'type': 'string',
                                                        'description': 'Object type, should always be "phones".'
                                                    },
                                                    'id': {
                                                        'type': 'integer',
                                                        'description': 'Phone identifier.'
                                                    }
                                                },
                                                'required': [
                                                    'type',
                                                    'id'
                                                ]
                                            }
                                        }
                                    },
                                    'required': []
                                },
                                'SupplierContactExternalRelationshipUpdate': {
                                    'type': 'object',
                                    'description': 'External relationship update object containing:',
                                    'properties': {
                                        'external_contact_types': {
                                            'type': 'array',
                                            'description': 'Contact types referenced by external ID.',
                                            'items': {
                                                'type': 'object',
                                                'properties': {
                                                    'type': {
                                                        'type': 'string',
                                                        'description': 'Object type, should always be "contact_types".'
                                                    },
                                                    'id': {
                                                        'type': 'integer',
                                                        'description': 'Contact type identifier.'
                                                    }
                                                },
                                                'required': [
                                                    'type',
                                                    'id'
                                                ]
                                            }
                                        },
                                        'phones': {
                                            'type': 'array',
                                            'description': 'List of phones for a contact (limited to 1 for now).',
                                            'items': {
                                                'type': 'object',
                                                'properties': {
                                                    'type': {
                                                        'type': 'string',
                                                        'description': 'Object type, should always be "phones".'
                                                    },
                                                    'id': {
                                                        'type': 'integer',
                                                        'description': 'Phone identifier.'
                                                    }
                                                },
                                                'required': [
                                                    'type',
                                                    'id'
                                                ]
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
                        'type',
                        'id',
                        'attributes'
                    ]
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def patch(id: int, _include: Optional[str] = None, body: Optional[Dict[str, Any]] = None
          ) -> Tuple[Union[Dict[str, Any], Dict[str, str]], int]:
    """
    Updates the details of an existing supplier contact.

    This function modifies a supplier contact's attributes and optionally updates related
    contact types and phone records. The request body must include the `id` of the contact,
    which should match the path parameter.

    Args:
        id (int): Required. Unique identifier of the supplier contact to be updated.
        _include (Optional[str]): Comma-separated list of related resources to include in the response. It can be one of the following allowed values ["supplier_company", "contact_types", "phones"]
        body (Optional[Dict[str, Any]]): Payload containing the updated supplier contact information.
            - type (str): Required. Must be "supplier_contacts".
            - id (int): Required. Must match the `id` in the URL path.
            - attributes (Dict[str, Any]): Supplier contact attributes object containing:
                - name (str): Required unless both `first_name` and `last_name` are provided. Full name (≤ 255 chars).
                - first_name (Optional[str]): First name (≤ 255 chars).
                - last_name (Optional[str]): Last name (≤ 255 chars).
                - email (str): Required. Email address (≤ 255 chars).
                - notes (Optional[str]): Notes about the contact.
                - phone_number (Optional[str]): Deprecated. Prefer `phones` relationship.
                - job_title (Optional[str]): Job title of the contact.
                - external_id (Optional[str]): Internal reference ID.
                - is_suggested (Optional[bool]): If the contact is unapproved or suggested.
            - relationships (Optional[Dict[str, Any]]): Contact relationships to update. Optional - only provide when updating relationships. Can be either:
                - SupplierContactRelationshipUpdate (Optional[Dict[str, Any]]): Internal relationship update object containing:
                    - contact_types (Optional[List[Dict[str, Any]]]): List of contact types for a contact.
                        - type (str): Object type, should always be "contact_types".
                        - id (int): Contact type identifier.
                    - phones (Optional[List[Dict[str, Any]]]): List of phones for a contact.
                        - type (str): Object type, should always be "phones".
                        - id (int): Phone identifier.
                - SupplierContactExternalRelationshipUpdate (Optional[Dict[str, Any]]): External relationship update object containing:
                    - external_contact_types (Optional[List[Dict[str, Any]]]): Contact types referenced by external ID.
                        - type (str): Object type, should always be "contact_types".
                        - id (int): Contact type identifier.
                    - phones (Optional[List[Dict[str, Any]]]): List of phones for a contact (limited to 1 for now).
                        - type (str): Object type, should always be "phones".
                        - id (int): Phone identifier.

    Returns:
        Tuple[Union[Dict[str, Any], Dict[str, str]], int]: A tuple containing:
            - First element: Either the updated supplier contact details or an error message
            - Second element: HTTP status code (200 for success, 404 for not found, 400 for bad request)

            When successful (status 200), the first element contains:
            - data (Dict[str, Any]):
                - type (str): Always "supplier_contacts".
                - id (int): Supplier contact identifier.
                - attributes (Dict[str, Any]):
                    - name (str): Full name of the contact.
                    - first_name (Optional[str]): First name.
                    - last_name (Optional[str]): Last name.
                    - email (str): Email address.
                    - notes (Optional[str]): Notes.
                    - phone_number (Optional[str]): Deprecated.
                    - job_title (Optional[str]): Job title.
                    - external_id (Optional[str]): External ID from internal systems.
                    - is_suggested (Optional[bool]): Indicates if suggested.
                    - updated_at (str): ISO 8601 timestamp of last update.
                - relationships (Dict[str, Any]):
                    - supplier_company (Dict[str, Any]):
                        - type (str): Object type, should always be "supplier_companies".
                        - id (int): Supplier company identifier.
                    - contact_types (Optional[Dict[str, Any]]): List of contact types for a contact.
                        - type (str): Object type, should always be "contact_types".
                        - id (int): Contact type identifier.
                    - phones (Optional[Dict[str, Any]]): List of phones for a contact.
                        - type (str): Object type, should always be "phones".
                        - id (int): Phone identifier.

            When not found (status 404), the first element contains:
            - error (str): Error message "Contact not found"

            When bad request (status 400), the first element contains:
            - error (str): Error message "Body is required"

    """

    contact = db.DB["suppliers"]["supplier_contacts"].get(id)
    if not contact:
        return {"error": "Contact not found"}, 404
    if not body:
        return {"error": "Body is required"}, 400
    if body.get("id") != id:
        return {"error": "Id in body must match url"}, 400
    contact.update(body)
    if _include:
        # Simulate include logic (not fully implemented)
        pass
    return contact, 200

@tool_spec(
    spec={
        'name': 'delete_supplier_contact_by_id',
        'description': """ Deletes a supplier contact by its unique identifier.
        
        This function permanently removes the specified supplier contact from the system. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'id': {
                    'type': 'integer',
                    'description': 'Required. Unique identifier of the supplier contact to be deleted.'
                }
            },
            'required': [
                'id'
            ]
        }
    }
)
def delete(id: int) -> Tuple[Union[Dict[str, Any], Dict[str, str]], int]:
    """
    Deletes a supplier contact by its unique identifier.

    This function permanently removes the specified supplier contact from the system.

    Args:
        id (int): Required. Unique identifier of the supplier contact to be deleted.

    Returns:
        Tuple[Union[Dict[str, Any], Dict[str, str]], int]: A tuple containing:
            - First element: Either an empty dictionary or an error message
            - Second element: HTTP status code (204 for success, 404 for not found)

            When successful (status 204), the first element contains:
            - Empty dictionary.

            When not found (status 404), the first element contains:
            - error (str): Error message "Contact not found"
    """

    if id not in db.DB["suppliers"]["supplier_contacts"]:
        return {"error": "Contact not found"}, 404
    del db.DB["suppliers"]["supplier_contacts"][id]
    return {}, 204 