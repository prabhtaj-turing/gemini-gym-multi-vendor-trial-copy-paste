"""
Supplier Contact Management by External ID Module

This module provides functionality for managing supplier contacts using their external
identifiers in the Workday Strategic Sourcing system. It supports operations for
retrieving, updating, and deleting supplier contact records using external IDs.

The module interfaces with the simulation database to provide comprehensive supplier
contact management capabilities, particularly useful when integrating with external
systems that maintain their own identifiers. It allows users to:
- Retrieve detailed supplier contact information using external IDs
- Update existing supplier contact records with external ID validation
- Delete supplier contact entries by external ID
- Handle related resource inclusion where applicable

Functions:
    get: Retrieves supplier contact details by external ID
    patch: Updates supplier contact details by external ID
    delete: Deletes a supplier contact by external ID
"""
from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, Dict, Any, Tuple
from pydantic import ValidationError
from .SimulationEngine.models import ExternalIdValidator
from .SimulationEngine import db
from .SimulationEngine.custom_errors import ContactNotFoundError, DatabaseSchemaError


@tool_spec(
    spec={
        'name': 'get_supplier_contact_by_external_id',
        'description': """ Retrieves the details of an existing supplier contact by external ID.
        
        This function returns the full resource representation of a supplier contact
        identified by its external ID, with optional inclusion of related entities. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': """ Required. Unique external identifier of the supplier contact.
                    Example: "CNT-17" """
                },
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated string of related resources to include in the response.
                    Allowed values:
                    - "supplier_company"
                    - "contact_types"
                    - "phones" """
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def get(external_id: str, _include: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
    """
    Retrieves the details of an existing supplier contact by external ID.

    This function returns the full resource representation of a supplier contact
    identified by its external ID, with optional inclusion of related entities.

    Args:
        external_id (str): Required. Unique external identifier of the supplier contact.
            Example: "CNT-17"
        _include (Optional[str]): Comma-separated string of related resources to include in the response.
            Allowed values:
                - "supplier_company"
                - "contact_types"
                - "phones"

    Returns:
        Tuple[Dict[str, Any], int]: A tuple containing the supplier contact and HTTP status code.
            - First element (Dict[str, Any]): A dictionary containing the supplier contact details if successful, else the error message.
            - Second element (int): HTTP status code. It is 200 if successful, 404 if not found.

            If Success, First element is a dictionary containing the supplier contact details.
                - type (str): Always "supplier_contacts".
                - id (int): Unique internal identifier for the supplier contact.
                - attributes (Dict[str, Any]):
                    - name (str): Full name (≤ 255 characters).
                    - first_name (Optional[str]): First name (≤ 255 characters).
                    - last_name (Optional[str]): Last name (≤ 255 characters).
                    - email (str): Contact's email address (≤ 255 characters).
                    - notes (Optional[str]): Notes related to the contact.
                    - phone_number (Optional[str]): Deprecated. Prefer using `phones` relationship.
                    - job_title (Optional[str]): Job title.
                    - external_id (str): The external identifier of the contact.
                    - is_suggested (Optional[bool]): Whether the contact was suggested and unapproved.
                    - updated_at (str): Timestamp of the last update (ISO 8601).

                - relationships (Dict[str, Any]):
                    - supplier_company (Dict[str, Any]):
                        - data: { id (int), type (str) }
                    - contact_types (Optional[Dict[str, Any]]):
                        - data: List[{ id (int), type (str) }]
                    - phones (Optional[Dict[str, Any]]):
                        - data: List[{ id (int), type (str) }]

            If Error, First element is a dictionary containing the error message.  
                - error (str): Error message.
    """

    for contact in db.DB["suppliers"]["supplier_contacts"].values():
        if contact.get("external_id") == external_id:
            if _include:
                # Simulate include logic (not fully implemented)
                pass
            return contact, 200
    return {"error": "Contact not found"}, 404

@tool_spec(
    spec={
        'name': 'update_supplier_contact_by_external_id',
        'description': """ Updates the details of an existing supplier contact using the external ID.
        
        The function modifies a supplier contact’s attributes and relationships such as contact types
        and phone numbers, identified via the external ID. The request body must include the contact's
        internal `id`, which must match the contact's actual identifier in the system. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': """ Required. Unique external identifier of the supplier contact.
                    Example: "CNT-17" """
                },
                '_include': {
                    'type': 'string',
                    'description': 'Related resources to include in the response. It can be one of the following values ["supplier_company", "contact_types", "phones"]'
                },
                'body': {
                    'type': 'object',
                    'description': 'Payload with updated supplier contact details.',
                    'properties': {
                        'data': {
                            'type': 'object',
                            'description': 'Required. Empty object container.',
                            'properties': {},
                            'required': []
                        },
                        'type': {
                            'type': 'string',
                            'description': 'Required. Must be "supplier_contacts".'
                        },
                        'id': {
                            'type': 'integer',
                            'description': 'Required. Must match the internal ID of the contact being updated.'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': 'Required. Contact attributes to update.',
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Required unless both `first_name` and `last_name` are given. Full name (≤ 255 chars).'
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
                                    'description': 'Optional notes related to the contact.'
                                },
                                'phone_number': {
                                    'type': 'string',
                                    'description': 'Deprecated. Prefer using `phones` relationship.'
                                },
                                'job_title': {
                                    'type': 'string',
                                    'description': 'Job title of the contact.'
                                },
                                'external_id': {
                                    'type': 'string',
                                    'description': 'External ID of the contact.'
                                },
                                'is_suggested': {
                                    'type': 'boolean',
                                    'description': 'Indicates if the contact was suggested and not yet approved.'
                                }
                            },
                            'required': [
                                'name',
                                'email'
                            ]
                        },
                        'relationships': {
                            'type': 'object',
                            'description': 'Required. Contact relationships to update. Can be either:',
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
                                    'required': [
                                        'contact_types',
                                        'phones'
                                    ]
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
                                    'required': [
                                        'external_contact_types',
                                        'phones'
                                    ]
                                }
                            },
                            'required': []
                        }
                    },
                    'required': [
                        'data',
                        'type',
                        'id',
                        'attributes',
                        'relationships'
                    ]
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def patch(external_id: str, _include: Optional[str] = None, body: Optional[Dict[str, Any]] = None
          ) -> Tuple[Dict[str, Any], int]:
    """
    Updates the details of an existing supplier contact using the external ID.

    The function modifies a supplier contact’s attributes and relationships such as contact types
    and phone numbers, identified via the external ID. The request body must include the contact's
    internal `id`, which must match the contact's actual identifier in the system.

    Args:
        external_id (str): Required. Unique external identifier of the supplier contact.
            Example: "CNT-17"
        _include (Optional[str]): Related resources to include in the response. It can be one of the following values ["supplier_company", "contact_types", "phones"]
        body (Optional[Dict[str, Any]]): Payload with updated supplier contact details.
            - data (Dict[str, Any]): Required. Empty object container.
            - type (str): Required. Must be "supplier_contacts".
            - id (int): Required. Must match the internal ID of the contact being updated.
            - attributes (Dict[str, Any]): Required. Contact attributes to update.
                - name (str): Required unless both `first_name` and `last_name` are given. Full name (≤ 255 chars).
                - first_name (Optional[str]): First name (≤ 255 chars).
                - last_name (Optional[str]): Last name (≤ 255 chars).
                - email (str): Required. Email address (≤ 255 chars).
                - notes (Optional[str]): Optional notes related to the contact.
                - phone_number (Optional[str]): Deprecated. Prefer using `phones` relationship.
                - job_title (Optional[str]): Job title of the contact.
                - external_id (Optional[str]): External ID of the contact.
                - is_suggested (Optional[bool]): Indicates if the contact was suggested and not yet approved.
            - relationships (Dict[str, Any]): Required. Contact relationships to update. Can be either:
                - SupplierContactRelationshipUpdate (Optional[Dict[str, Any]]): Internal relationship update object containing:
                    - contact_types (List[Dict[str, Any]]): List of contact types for a contact.
                        - type (str): Object type, should always be "contact_types".
                        - id (int): Contact type identifier.
                    - phones (List[Dict[str, Any]]): List of phones for a contact.
                        - type (str): Object type, should always be "phones".
                        - id (int): Phone identifier.
                - SupplierContactExternalRelationshipUpdate (Optional[Dict[str, Any]]): External relationship update object containing:
                    - external_contact_types (List[Dict[str, Any]]): Contact types referenced by external ID.
                        - type (str): Object type, should always be "contact_types".
                        - id (int): Contact type identifier.
                    - phones (List[Dict[str, Any]]): List of phones for a contact (limited to 1 for now).
                        - type (str): Object type, should always be "phones".
                        - id (int): Phone identifier.

    Returns:
        Tuple[Dict[str, Any], int]: A tuple containing the updated supplier contact resource and HTTP status code.
            - First element (Dict[str, Any]): A dictionary containing the updated supplier contact resource if successful, else the error message.
            - Second element (int): HTTP status code. It is 200 if successful, 400 if body is required, 404 if not found.

            If Success, First element is a dictionary containing the updated supplier contact details.
                - type (str): Always "supplier_contacts".
                - id (int): Internal ID of the supplier contact.
                - attributes (Dict[str, Any]):
                    - name (str): Full contact name.
                    - first_name (Optional[str]): First name.
                    - last_name (Optional[str]): Last name.
                    - email (str): Contact's email.
                    - notes (Optional[str]): Notes.
                    - phone_number (Optional[str]): Deprecated phone number.
                    - job_title (Optional[str]): Job title.
                    - external_id (Optional[str]): External system ID.
                    - is_suggested (Optional[bool]): Indicates if contact is suggested.
                    - updated_at (str): Last updated timestamp (ISO 8601).
                - relationships (Dict[str, Any]):
                    - supplier_company (Dict[str, Any]):
                        - data: { id (int), type (str) }
                    - contact_types (Optional[Dict[str, Any]]):
                        - data: List[{ id (int), type (str) }]
                    - phones (Optional[Dict[str, Any]]): List of phones for a contact. limited to 1 for now.
                        - type (str): Object type, should always be "phones".
                        - id (int): Phone identifier.

            If Error, First element is a dictionary containing the error message.  
                - error (str): Error message.
    """

    for contact_id, contact in db.DB["suppliers"]["supplier_contacts"].items():
        if contact.get("external_id") == external_id:
            if not body:
                return {"error": "Body is required"}, 400
            contact.update(body)
            if _include:
                # Simulate include logic (not fully implemented)
                pass
            return contact, 200
    return {"error": "Contact not found"}, 404

@tool_spec(
    spec={
        'name': 'delete_supplier_contact_by_external_id',
        'description': """ Deletes a supplier contact using the external identifier.
        
        This function permanently removes the specified supplier contact identified by
        its external ID from the system. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'external_id': {
                    'type': 'string',
                    'description': """ Required. The unique external identifier of the supplier contact.
                    Example: "CNT-17" """
                }
            },
            'required': [
                'external_id'
            ]
        }
    }
)
def delete(external_id: str) -> str:
    """
    Deletes a supplier contact using the external identifier.

    This function permanently removes the specified supplier contact identified by
    its external ID from the system.

    Args:
        external_id (str): Required. The unique external identifier of the supplier contact.
            Example: "CNT-17"

    Returns:
        str: Success message indicating the contact was deleted successfully.

    Raises:
        ValidationError: If the external_id is invalid (None, empty string, whitespace, or wrong type).
        ContactNotFoundError: If the supplier contact with the specified external_id is not found.
        DatabaseSchemaError: If the database schema is malformed and supplier contacts cannot be accessed.
    """
    try:
        validated_id = external_id.strip() if isinstance(external_id, str) else external_id
        ExternalIdValidator(external_id=validated_id)
    except ValidationError as e:
        # Re-raise the original ValidationError instead of creating a new one
        raise e
    except AttributeError:
        # Create a proper ValidationError for non-string input
        from pydantic import ValidationError as PydanticValidationError
        raise PydanticValidationError.from_exception_data(
            "ValidationError",
            [{"loc": ("external_id",), "msg": "External ID must be a string.", "type": "value_error"}]
        )

    try:
        contact_id_to_delete = None
        for contact_id, contact in db.DB["suppliers"]["supplier_contacts"].items():
            if contact.get("external_id") == external_id:
                contact_id_to_delete = contact_id
                break

        if contact_id_to_delete is None:
            raise ContactNotFoundError(f"Contact with external_id '{external_id}' not found")

        del db.DB["suppliers"]["supplier_contacts"][contact_id_to_delete]
        return f"Contact with external_id '{external_id}' deleted successfully"

    except KeyError:
        raise DatabaseSchemaError("Database schema is malformed. Could not access supplier contacts.")