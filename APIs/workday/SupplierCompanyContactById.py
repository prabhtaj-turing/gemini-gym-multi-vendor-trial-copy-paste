"""
Supplier Company Contact Management by ID Module

This module provides functionality for managing individual contacts associated with
supplier companies in the Workday Strategic Sourcing system using their unique
identifiers. It supports operations for retrieving, updating, and deleting specific
contacts for a supplier company.

The module interfaces with the simulation database to provide comprehensive contact
management capabilities, allowing users to:
- Retrieve specific contact details by company and contact IDs
- Update existing contact information
- Delete contacts from the system
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, Tuple, Union
from .SimulationEngine import db
from .SimulationEngine.custom_errors import ContactNotFoundError, ValidationError, DatabaseSchemaError, NotFoundError

@tool_spec(
    spec={
        'name': 'get_supplier_company_contact_by_id',
        'description': """ Retrieves the details of an existing supplier company contact.
        
        This function locates a specific contact using both the company ID and contact ID,
        then returns the complete contact details with optional related resource inclusion. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'company_id': {
                    'type': 'integer',
                    'description': """ The unique identifier of the supplier company.
                    This is the internal ID used by the system to reference the company. """
                },
                'contact_id': {
                    'type': 'integer',
                    'description': """ The unique identifier of the contact.
                    This is the internal ID used by the system to reference the contact. """
                },
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated list of related resources to include
                    in the response. Not fully implemented. """
                }
            },
            'required': [
                'company_id',
                'contact_id'
            ]
        }
    }
)
def get(company_id: int, contact_id: int, _include: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieves the details of an existing supplier company contact.

    This function locates a specific contact using both the company ID and contact ID,
    then returns the complete contact details with optional related resource inclusion.

    Args:
        company_id (int): The unique identifier of the supplier company.
            This is the internal ID used by the system to reference the company.
        contact_id (int): The unique identifier of the contact.
            This is the internal ID used by the system to reference the contact.
        _include (Optional[str]): Comma-separated list of related resources to include
            in the response. Not fully implemented.

    Returns:
        Dict[str, Any]: Contact details dictionary including:
            - "id" (int): The internal unique identifier
            - "company_id" (int): The ID of the associated supplier company
            - "name" (str): The contact's full name
            - "email" (str): The contact's email address
            - "phone" (Optional[str]): The contact's phone number
            - "role" (str): The contact's role in the company
            - "status" (str): The contact's status
            - Other contact-specific fields

    Raises:
        ValidationError: If company_id or contact_id are invalid (negative or zero)
        NotFoundError: If the specified contact is not found in the database
    """
    # Input validation
    if not isinstance(company_id, int) or company_id <= 0:
        raise ValidationError("company_id must be a positive integer")
    
    if not isinstance(contact_id, int) or contact_id <= 0:
        raise ValidationError("contact_id must be a positive integer")
    
    # Find the contact in the database
    contact = next((c for c in db.DB["suppliers"]["supplier_contacts"].values() 
                   if c.get("company_id") == company_id and c.get("id") == contact_id), None)
    
    if not contact:
        raise NotFoundError(f"Contact with company_id={company_id} and contact_id={contact_id} not found")
    
    # Handle include parameter (simulated implementation)
    if _include:
        # Simulate include logic (not fully implemented)
        pass
    
    return contact

@tool_spec(
    spec={
        'name': 'update_supplier_company_contact_by_id',
        'description': """ Updates the details of an existing supplier company contact.
        
        This function allows modification of contact information by providing updated
        values for specific fields. The contact is identified by both company ID and
        contact ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'company_id': {
                    'type': 'integer',
                    'description': """ The unique identifier of the supplier company.
                    This is the internal ID used by the system to reference the company. """
                },
                'contact_id': {
                    'type': 'integer',
                    'description': """ The unique identifier of the contact.
                    This is the internal ID used by the system to reference the contact. """
                },
                '_include': {
                    'type': 'string',
                    'description': """ Comma-separated list of related resources to include
                    in the response. Not fully implemented. """
                },
                'body': {
                    'type': 'object',
                    'description': 'Supplier contact update data object. Must contain:',
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': 'Object type, should always be "supplier_contacts".'
                        },
                        'id': {
                            'type': 'integer',
                            'description': 'Supplier contact identifier.'
                        },
                        'attributes': {
                            'type': 'object',
                            'description': """ Supplier contact attributes:
                                 - first_name Optional(str): Supplier contact first name. Can be used with last_name (name can be skipped). max length 255 characters
                                - last_name Optional(str): Supplier contact last name. Can be used with first_name (name can be skipped). max length 255 characters
                                - notes Optional(str): Supplier contact notes.
                                - job_title Optional(str): Supplier contact job title.
                                - external_id Optional(str): Supplier contact ID in your internal database.
                                - is_suggested Optional(bool): Whether the contact was suggested by a team member but not yet approved. """,
                            'properties': {
                                'name': {
                                    'type': 'string',
                                    'description': 'Supplier contact name (required). max length 255 characters'
                                },
                                'email': {
                                    'type': 'string',
                                    'description': 'Supplier contact email (required). max length 255 characters'
                                },
                                'phone_number': {
                                    'type': 'string',
                                    'description': 'Supplier contact phone number (deprecated, use phones relation instead).'
                                }
                            },
                            'required': [
                                'name',
                                'email',
                                'phone_number'
                            ]
                        },
                        'relationships': {
                            'type': 'object',
                            'description': 'Related resources. Can be either:',
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
                            'required': [
                                'SupplierContactRelationshipUpdate',
                                'SupplierContactExternalRelationshipUpdate'
                            ]
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
                'company_id',
                'contact_id'
            ]
        }
    }
)
def patch(company_id: int, contact_id: int, _include: Optional[str] = None, 
          body: Optional[Dict[str, Any]] = None) -> Tuple[Union[Dict[str, Any], Dict[str, str]], int]:
    """
    Updates the details of an existing supplier company contact.

    This function allows modification of contact information by providing updated
    values for specific fields. The contact is identified by both company ID and
    contact ID.

    Args:
        company_id (int): The unique identifier of the supplier company.
            This is the internal ID used by the system to reference the company.
        contact_id (int): The unique identifier of the contact.
            This is the internal ID used by the system to reference the contact.
        _include (Optional[str]): Comma-separated list of related resources to include
            in the response. Not fully implemented.
        body (Optional[Dict[str, Any]]): Supplier contact update data object. Must contain:
            - type (str): Object type, should always be "supplier_contacts".
            - id (int): Supplier contact identifier.
            - attributes (Dict[str, Any]): Supplier contact attributes:
                - name (str): Supplier contact name (required). max length 255 characters
                - first_name Optional(str): Supplier contact first name. Can be used with last_name (name can be skipped). max length 255 characters
                - last_name Optional(str): Supplier contact last name. Can be used with first_name (name can be skipped). max length 255 characters
                - email (str): Supplier contact email (required). max length 255 characters
                - notes Optional(str): Supplier contact notes.
                - phone_number (str): Supplier contact phone number (deprecated, use phones relation instead).
                - job_title Optional(str): Supplier contact job title.
                - external_id Optional(str): Supplier contact ID in your internal database.
                - is_suggested Optional(bool): Whether the contact was suggested by a team member but not yet approved.
            - relationships (Optional[Dict[str, Any]]): Related resources. Can be either:
                SupplierContactRelationshipUpdate (Dict[str, Any]): Internal relationship update object containing:
                    - contact_types (List[Dict[str, Any]]): List of contact types for a contact.
                        - type (str): Object type, should always be "contact_types".
                        - id (int): Contact type identifier.
                    - phones (List[Dict[str, Any]]): List of phones for a contact.
                        - type (str): Object type, should always be "phones".
                        - id (int): Phone identifier.
                SupplierContactExternalRelationshipUpdate (Dict[str, Any]): External relationship update object containing:
                    - external_contact_types (List[Dict[str, Any]]): Contact types referenced by external ID.
                        - type (str): Object type, should always be "contact_types".
                        - id (int): Contact type identifier.
                    - phones (List[Dict[str, Any]]): List of phones for a contact (limited to 1 for now).
                        - type (str): Object type, should always be "phones".
                        - id (int): Phone identifier.

    Returns:
        Tuple[Union[Dict[str, Any], Dict[str, str]], int]: A tuple containing:
            - Dict[str, Any]: Updated contact details dictionary
            - int: HTTP status code (200 for success, 400 for bad request, 404 for not found)
            If request body is missing, returns:
            - Dict[str, str]: Error message with key "error"
            - int: 400 status code
            If contact not found, returns:
            - Dict[str, str]: Error message with key "error"
            - int: 404 status code
    """
    if not body:
        return {"error": "Request body is required"}, 400
    
    contact = next((c for c in db.DB["suppliers"]["supplier_contacts"].values() 
                   if c.get("company_id") == company_id and c.get("id") == contact_id), None)
    if not contact:
        return {"error": "Contact not found"}, 404
    
    # Update contact details
    for key, value in body.items():
        contact[key] = value
    
    if _include:
        # Simulate include logic (not fully implemented)
        pass
    return contact, 200

@tool_spec(
    spec={
        'name': 'delete_supplier_company_contact_by_id',
        'description': """ Deletes a supplier company contact.
        
        This function removes a specific contact from the system using both the company ID 
        and contact ID for identification. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'company_id': {
                    'type': 'integer',
                    'description': """ The unique identifier of the supplier company.
                    Must be a positive integer. """
                },
                'contact_id': {
                    'type': 'integer',
                    'description': """ The unique identifier of the contact.
                    Must be a positive integer. """
                }
            },
            'required': [
                'company_id',
                'contact_id'
            ]
        }
    }
)
def delete(company_id: int, contact_id: int) -> None:
    """
    Deletes a supplier company contact.

    This function removes a specific contact from the system using both the company ID 
    and contact ID for identification.

    Args:
        company_id (int): The unique identifier of the supplier company.
            Must be a positive integer.
        contact_id (int): The unique identifier of the contact.
            Must be a positive integer.

    Raises:
        ValidationError: If company_id or contact_id are not positive integers
        ContactNotFoundError: If the specified contact is not found in the database
        DatabaseSchemaError: If the database structure is corrupted or inaccessible

    Note:
        This operation is irreversible. The contact will be permanently deleted
        from the system and cannot be recovered.
    """
    # Validate input parameters
    if not isinstance(company_id, int) or company_id <= 0:
        raise ValidationError("Company ID must be a positive integer")
    
    if not isinstance(contact_id, int) or contact_id <= 0:
        raise ValidationError("Contact ID must be a positive integer")
    
    # Validate database structure
    if not isinstance(db.DB, dict):
        raise DatabaseSchemaError("Database is not properly initialized")
    
    if "suppliers" not in db.DB:
        raise DatabaseSchemaError("Suppliers section not found in database")
    
    suppliers_data = db.DB["suppliers"]
    if not isinstance(suppliers_data, dict):
        raise DatabaseSchemaError("Suppliers data is not properly structured")
    
    if "supplier_contacts" not in suppliers_data:
        raise DatabaseSchemaError("Supplier contacts section not found in database")
    
    # Find the contact
    contact = next((c for c in suppliers_data["supplier_contacts"].values() 
                   if c.get("company_id") == company_id and c.get("id") == contact_id), None)
    
    if not contact:
        raise ContactNotFoundError(f"Contact with company_id {company_id} and contact_id {contact_id} not found")
    
    # Remove contact from database
    del suppliers_data["supplier_contacts"][str(contact_id)] 