from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, Dict, Any, List
from .SimulationEngine.db import DB
from .SimulationEngine import utils, custom_errors
import uuid
from .SimulationEngine.models import ContactListResponse, Contact, WorkspaceUserListResponse, DirectorySearchResponse
from pydantic import ValidationError as PydanticValidationError
from pydantic import TypeAdapter
from common_utils.phone_utils import normalize_phone_number
from common_utils.utils import validate_email_util

@tool_spec(
    spec={
        'name': 'list_contacts',
        'description': """ List all contacts or filter by name.
        
        Lists all your Google contacts or filters them by name. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'name_filter': {
                    'type': 'string',
                    'description': 'String to filter contacts by name. If None, all contacts are returned.'
                },
                'max_results': {
                    'type': 'integer',
                    'description': 'Maximum number of contacts to return (default: 100).'
                }
            },
            'required': []
        }
    }
)
def list_contacts(name_filter: Optional[str] = None, max_results: Optional[int] = 100) -> Dict[str, Any]:
    """List all contacts or filter by name.

    Lists all your Google contacts or filters them by name.

    Args:
        name_filter (Optional[str]): String to filter contacts by name. If None, all contacts are returned.
        max_results (Optional[int]): Maximum number of contacts to return (default: 100).

    Returns:
        Dict[str, Any]: A dictionary containing the list of contacts.
            - contacts (List[Dict[str, Any]]): A list of contact objects matching
              the query. Each contact object can contain the following keys:
                - resourceName (str): The unique identifier for the contact.
                - etag (str): An entity tag for the resource, used for caching.
                - names (List[Dict[str, str]]): A list of name objects, where
                  each object may contain 'givenName' and 'familyName'.
                - emailAddresses (List[Dict[str, Any]]): A list of email objects,
                  where each object may contain the email 'value', 'type' (e.g.,
                  'home', 'work'), and a boolean 'primary' flag.
                - phoneNumbers (List[Dict[str, Any]]): A list of phone number
                  objects, where each object may contain the phone 'value', 'type',
                  and a boolean 'primary' flag.
                - organizations (List[Dict[str, Union[str, None, bool]]]): A list of organization
                  objects, where each object may contain the company 'name' and
                  job 'title'.
                - notes (str, optional): An alias field about the contact.

    Raises:
        ValidationError: If input arguments fail validation.
        ContactsCollectionNotFoundError: If the contacts collection doesn't exist in the database.
    """
    # Validate input arguments
    if max_results is not None:
        if not isinstance(max_results, int) or max_results <= 0:
            raise custom_errors.ValidationError("max_results must be a positive integer.")
    
    if name_filter is not None and not isinstance(name_filter, str):
        raise custom_errors.ValidationError("name_filter must be a string.")

    try:
        found_contacts = utils.search_collection(
            collection_name="myContacts",
            query=name_filter,
            max_results=max_results
        )
        
        # Validate the structure of the found contacts
        try:
            validated_response = ContactListResponse(contacts=found_contacts)
            return validated_response.model_dump()
        except PydanticValidationError as e:
            # Raise your custom validation error if Pydantic validation fails
            raise custom_errors.ValidationError(f"Contact data validation failed: {e}")

    except KeyError:
        # This handles the case where the "myContacts" collection doesn't exist.
        raise custom_errors.ContactsCollectionNotFoundError("Contacts collection 'myContacts' not found in the database.")

@tool_spec(
    spec={
        'name': 'get_contact',
        'description': """ Retrieves detailed information about a specific contact.
        
        This function gets a contact by their resource name or email address, retrieving detailed information for that specific contact. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'identifier': {
                    'type': 'string',
                    'description': 'Resource name (`people/*`) or email address of the contact.'
                }
            },
            'required': [
                'identifier'
            ]
        }
    }
)
def get_contact(identifier: str) -> Dict[str, Any]:
    """Retrieves detailed information about a specific contact.

    This function gets a contact by their resource name or email address, retrieving detailed information for that specific contact.

    Args:
        identifier (str): Resource name (`people/*`) or email address of the contact.

    Returns:
        Dict[str, Any]: A dictionary containing the contact's information with the
            following structure:
            - `resourceName` (str): The unique identifier for the contact.
            - `etag` (str): An identifier for the current state of the contact.
            - `names` (List[Dict]): A list of name objects, each containing:
                - `givenName` (str): The contact's first name.
                - `familyName` (str): The contact's last name.
            - `emailAddresses` (List[Dict]): A list of email objects, each containing:
                - `value` (str): The email address.
                - `type` (str): The type of email (e.g., 'home', 'work').
                - `primary` (bool): True if this is the primary email.
            - `phoneNumbers` (List[Dict], optional): A list of phone number objects, each containing:
                - `value` (str): The phone number.
                - `type` (str): The type of phone number (e.g., 'mobile', 'work').
                - `primary` (bool): True if this is the primary number.
            - `organizations` (List[Dict], optional): A list of organization objects, each containing:
                - `name` (str): The name of the organization.
                - `title` (str): The job title.
                - `department` (str, optional): The department name.
            - `isWorkspaceUser` (bool, optional): True if the contact is a workspace user
              (typically for directory contacts).

    Raises:
        ValidationError: If the input identifier is invalid.
        ContactNotFoundError: If no contact is found for the given identifier.
        PydanticValidationError: If the fetched contact data fails structure validation.
    """
    if not isinstance(identifier, str) or not identifier.strip():
        raise custom_errors.ValidationError("Identifier must be a non-empty string.")

    contact_data = None
    # Determine if the identifier is an email or a resource name
    if "@" in identifier:
        validate_email_util(identifier, "identifier")
        contact_data = utils.find_contact_by_email(identifier)
    else:
        contact_data = utils.find_contact_by_id(identifier)

    if not contact_data:
        raise custom_errors.ContactNotFoundError(
            f"No contact found for identifier: {identifier}"
        )

    # Validate the structure of the fetched contact data
    try:
        Contact.model_validate(contact_data)
    except PydanticValidationError as e:
        # If validation fails, raise the aliased error
        raise PydanticValidationError(
            f"Fetched contact data for '{identifier}' is invalid."
        ) from e

    return contact_data

@tool_spec(
    spec={
        'name': 'create_contact',
        'description': """ Creates a new contact in your Google Contacts.
        
        This function creates a new contact entry in Google Contacts using the provided personal details. The 'given_name' field is required. In addition, at least one of 'email' or 'phone' must be provided.""",
        'parameters': {
            'type': 'object',
            'properties': {
                'given_name': {
                    'type': 'string',
                    'description': 'First name of the contact.'
                },
                'family_name': {
                    'type': 'string',
                    'description': 'Last name of the contact.'
                },
                'email': {
                    'type': 'string',
                    'description': 'Email address of the contact.'
                },
                'phone': {
                    'type': 'string',
                    'description': 'Phone number of the contact. Must be 7-15 digits and may include a country code with \'+\' prefix. Examples: \'+14155552671\', \'4155552671\', \'(415) 555-2671\'.'
                }
            },
            'required': [
                'given_name'
            ]
        }
    }
)
def create_contact(given_name: str, family_name: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None) -> Dict[str, Any]:
    """Creates a new contact in your Google Contacts.

    This function creates a new contact entry in Google Contacts using the provided personal details.
    The 'given_name' field is required. In addition, at least one of 'email' or 'phone' must be provided.

    Args:
        given_name (str): First name of the contact.
        family_name (Optional[str]): Last name of the contact.
        email (Optional[str]): Email address of the contact.
        phone (Optional[str]): Phone number of the contact. Must be 7-15 digits and may include a country code with '+' prefix. Examples: '+14155552671', '4155552671', '(415) 555-2671'.

    Returns:
        Dict[str, Any]: A dictionary detailing the outcome of the creation operation.
            - "status" (str): Indicates the result of the operation, typically "success".
            - "message" (str): A human-readable summary of the action taken.
            - "contact" (Dict[str, Any]): The complete dictionary object for the newly
              created contact, including its server-assigned `resourceName` and `etag`. Contains the following fields:
                - "resourceName" (str): The unique identifier for the contact.
                - "etag" (str): An identifier for the current state of the contact.
                - "names" (List[Dict[str, str]]): A list of name objects, each containing:
                    - "givenName" (str): The contact's first name.
                    - "familyName" (str): The contact's last name.
                - "emailAddresses" (List[Dict[str, Any]]): A list of email objects, each containing:
                    - "value" (str): The email address.
                    - "type" (str): The type of email (e.g., 'home', 'work').
                    - "primary" (bool): True if this is the primary email.
                - "organizations" (List[Dict[str, str]]): A list of organization objects, each containing:
                    - "name" (str): The name of the organization.
                    - "title" (str): The job title.
                    - "department" (str, optional): The department name.
                - "phoneNumbers" (List[Dict[str, Any]]): A list of phone number objects, each containing:
                    - "value" (str): The phone number.
                    - "type" (str): The type of phone number (e.g., 'mobile', 'work').
                    - "primary" (bool): True if this is the primary number.
                - "whatsapp" (Dict[str, Any]): A dictionary containing WhatsApp-specific information:
                    - "jid" (str): The WhatsApp ID for the contact.
                    - "name_in_address_book" (str): The name of the contact in the address book.
                    - "profile_name" (str): The profile name of the contact.
                    - "phone_number" (str): The phone number of the contact.
                    - "is_whatsapp_user" (bool): A flag indicating if the contact is a WhatsApp user (True only if phone number is provided).
                - "phone" (Dict[str, Any]): A dictionary containing phone-specific information:
                    - "contact_id" (str): The ID of the contact.
                    - "contact_name" (str): The name of the contact.
                    - "recipient_type" (str): The type of recipient (always "CONTACT").
                    - "contact_endpoints" (List[Dict[str, Any]]): A list of contact endpoints.
                        - "endpoint_type" (str): The type of endpoint (always "PHONE_NUMBER").
                        - "endpoint_value" (str): The value of the endpoint (the phone number).
                        - "endpoint_label" (str): The label of the endpoint (always "mobile").

    Raises:
        ValidationError: If input arguments fail validation (e.g., empty given_name, invalid email, duplicate email, or when no contact method is provided).
    """
    # --- Input Validation (for business logic) ---
    # Sanitize and validate given_name
    given_name = utils.sanitize_name(given_name)

    if not any([email, phone]):
        raise custom_errors.ValidationError(
            "At least one contact method (email or phone) must be provided."
        )

    if email:
        validate_email_util(email, "email")
        if utils.find_contact_by_email(email):
            raise custom_errors.ValidationError(
                f"A contact with the email '{email}' already exists."
            )

    normalized_phone = None
    if phone:
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone:
            raise custom_errors.ValidationError(
                f"The phone number '{phone}' is not valid."
            )

    # --- Contact Construction ---
    resource_name = utils.generate_resource_name()
    new_contact = {
        "resourceName": resource_name,
        "etag": uuid.uuid4().hex,
        "names": [{"givenName": given_name}],
    }

    if family_name:
        # Sanitize and validate family_name
        sanitized_family_name = utils.sanitize_name(family_name)
        new_contact["names"][0]["familyName"] = sanitized_family_name

    if email:
        new_contact["emailAddresses"] = [
            {"value": email, "type": "home", "primary": True}
        ]

    if normalized_phone:
        new_contact["phoneNumbers"] = [
            {"value": normalized_phone, "type": "mobile", "primary": True}
        ]

    # --- WhatsApp Field Construction ---
    # Create WhatsApp field - is_whatsapp_user should only be True if phone number is provided
    whatsapp_data = {
        "is_whatsapp_user": normalized_phone is not None
    }
    
    # Set jid using phone number if available, otherwise use a placeholder
    if normalized_phone:
        # Clean phone number and create jid
        clean_phone = normalized_phone.replace("+", "").replace("-", "").replace(" ", "")
        whatsapp_data["jid"] = f"{clean_phone}@s.whatsapp.net"
        whatsapp_data["phone_number"] = normalized_phone
    else:
        # For contacts without phone, create a placeholder jid using email or name
        if email:
            # Use email domain as jid
            domain = email.split("@")[1]
            whatsapp_data["jid"] = f"contact_{uuid.uuid4().hex[:8]}@{domain}"
        else:
            # Use name-based jid
            name_part = given_name.lower().replace(" ", "")
            whatsapp_data["jid"] = f"{name_part}_{uuid.uuid4().hex[:8]}@s.whatsapp.net"
        whatsapp_data["phone_number"] = None
    
    # Set name_in_address_book and profile_name using names
    full_name = given_name
    if family_name:
        full_name = f"{given_name} {family_name}"
    
    whatsapp_data["name_in_address_book"] = full_name
    whatsapp_data["profile_name"] = full_name
    
    new_contact["whatsapp"] = whatsapp_data

    # --- Phone Field Construction ---
    # Create phone field with contact information
    phone_data = {
        "contact_id": resource_name,
        "contact_name": full_name,
        "recipient_type": "CONTACT",
        "contact_endpoints": []  # Always include empty list to satisfy Pydantic model
    }
    # Add contact_endpoints if phone number is provided
    if normalized_phone:
        phone_data["contact_endpoints"] = [
            {
                "endpoint_type": "PHONE_NUMBER",
                "endpoint_value": normalized_phone,
                "endpoint_label": "mobile"  # Default to mobile type
            }
        ]

    new_contact["phone"] = phone_data

    # Add missing organizations field
    new_contact["organizations"] = []

    # --- Pydantic Structure Validation ---
    try:
        # Use the Contact model to validate the structure of the dictionary
        Contact.model_validate(new_contact)
    except PydanticValidationError as e:
        # Re-raise as the API's custom error for consistent error handling
        raise custom_errors.ValidationError(
            f"Failed to create contact due to invalid data structure: {e}"
        )

    # --- Database Update ---
    DB["myContacts"][resource_name] = new_contact
    
    return {
        "status": "success",
        "message": f"Contact '{given_name}' created successfully.",
        "contact": new_contact,
    }

@tool_spec(
    spec={
        'name': 'update_contact',
        'description': """ Updates an existing contact with new information.
        
        This function updates an existing contact by applying the provided new details. At least one optional parameter must be provided to perform an update. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource_name': {
                    'type': 'string',
                    'description': 'Contact resource name (`people/*`).'
                },
                'given_name': {
                    'type': 'string',
                    'description': 'Updated first name.'
                },
                'family_name': {
                    'type': 'string',
                    'description': 'Updated last name.'
                },
                'email': {
                    'type': 'string',
                    'description': 'Updated email address.'
                },
                'phone': {
                    'type': 'string',
                    'description': 'Updated phone number. Must be 7-15 digits and may include a country code with \'+\' prefix. Examples: \'+14155552671\', \'4155552671\', \'(415) 555-2671\'.'
                }
            },
            'required': [
                'resource_name'
            ]
        }
    }
)
def update_contact(resource_name: str, given_name: Optional[str] = None, family_name: Optional[str] = None, email: Optional[str] = None, phone: Optional[str] = None) -> Dict[str, Any]:
    """Updates an existing contact with new information.

    This function updates an existing contact by applying the provided new details. At least one optional parameter must be provided to perform an update.

    Args:
        resource_name (str): Contact resource name (`people/*`).
        given_name (Optional[str]): Updated first name.
        family_name (Optional[str]): Updated last name.
        email (Optional[str]): Updated email address.
        phone (Optional[str]): Updated phone number. Must be 7-15 digits and may include a country code with '+' prefix. Examples: '+14155552671', '4155552671', '(415) 555-2671'.

    Returns:
        Dict[str, Any]: A dictionary representing the fully updated contact object. The structure includes:
            - 'resourceName' (str): The unique identifier for the contact (e.g., "people/c123...").
            - 'etag' (str): A unique string identifying the current state of the contact. This changes after every update.
            - 'names' (List[Dict[str, str]]): A list of name objects. Each object contains:
                - 'givenName' (str): The contact's first name.
                - 'familyName' (str): The contact's last name.
            - 'emailAddresses' (List[Dict[str, Any]]): A list of email objects. Each object can contain:
                - 'value' (str): The email address.
                - 'type' (str): The category of the email (e.g., 'home', 'work').
                - 'primary' (bool): A flag indicating if it's the primary email.
            - 'phoneNumbers' (List[Dict[str, Any]]): A list of phone number objects. Each object can contain:
                - 'value' (str): The phone number string.
                - 'type' (str): The category of the phone number (e.g., 'mobile', 'work').
                - 'primary' (bool): A flag indicating if it's the primary phone number.
            - Other fields like 'organizations' may be present depending on the contact's original data.

    Raises:
        custom_errors.ValidationError: If input arguments fail validation.
        custom_errors.ContactNotFoundError: If the contact does not exist.
        PydanticValidationError: If the structure of the returned contact is invalid.
    """
    if not resource_name or not isinstance(resource_name, str):
        raise custom_errors.ValidationError(
            "Argument 'resource_name' must be a non-empty string."
        )
    if email:
        validate_email_util(email, "email")

    if all(arg is None for arg in [given_name, family_name, email, phone]):
        raise custom_errors.ValidationError(
            "At least one field (given_name, family_name, email, phone) must be provided for the update."
        )

    contact = utils.find_contact_by_id(resource_name)
    if not contact:
        raise custom_errors.ContactNotFoundError(
            f"Contact with resource name '{resource_name}' not found."
        )

    is_updated = False

    # Update names
    if given_name is not None or family_name is not None:
        if not contact.get("names"):
            contact["names"] = [{"givenName": "", "familyName": ""}]

        if given_name is not None and contact["names"][0].get("givenName") != given_name:
            contact["names"][0]["givenName"] = given_name
            is_updated = True

        if family_name is not None and contact["names"][0].get("familyName") != family_name:
            contact["names"][0]["familyName"] = family_name
            is_updated = True

    # Update email
    if email is not None:
        if not contact.get("emailAddresses"):
            contact["emailAddresses"] = [
                {"value": email, "type": "other", "primary": True}
            ]
            is_updated = True
        else:
            primary_email = next(
                (e for e in contact["emailAddresses"] if e.get("primary")), None
            )
            if primary_email:
                if primary_email.get("value") != email:
                    primary_email["value"] = email
                    is_updated = True
            elif contact["emailAddresses"][0].get("value") != email:
                contact["emailAddresses"][0]["value"] = email
                is_updated = True

    # Update phone number
    if phone is not None:
        normalized_phone = normalize_phone_number(phone)
        if not normalized_phone:
            raise custom_errors.ValidationError(
                f"The phone number '{phone}' is not valid."
            )
        if not contact.get("phoneNumbers"):
            contact["phoneNumbers"] = [
                {"value": normalized_phone, "type": "mobile", "primary": True}
            ]
            is_updated = True
        else:
            primary_phone = next(
                (p for p in contact["phoneNumbers"] if p.get("primary")), None
            )
            if primary_phone:
                if primary_phone.get("value") != normalized_phone:
                    primary_phone["value"] = normalized_phone
                    is_updated = True
            elif contact["phoneNumbers"][0].get("value") != normalized_phone:
                contact["phoneNumbers"][0]["value"] = normalized_phone
                is_updated = True

    # Update etag if any data was changed
    if is_updated:
        contact["etag"] = uuid.uuid4().hex

    try:
        # Validate the structure of the contact dictionary before returning
        validated_contact = Contact.model_validate(contact)
        # Return the validated data as a dictionary, excluding fields that are None
        return validated_contact.model_dump(exclude_none=True)
    except PydanticValidationError as e:
        # This error indicates a mismatch between the function's output and the
        # Pydantic model, signifying a potential server-side bug.
        raise e
    
@tool_spec(
    spec={
        'name': 'delete_contact',
        'description': """ Deletes a contact by resource name from your Google Contacts.
        
        This function deletes a contact from Google Contacts using its specified resource name. Directory contacts or 'otherContacts' cannot be deleted via this method. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'resource_name': {
                    'type': 'string',
                    'description': 'Contact resource name (`people/*`) to delete.'
                }
            },
            'required': [
                'resource_name'
            ]
        }
    }
)
def delete_contact(resource_name: str) -> Dict[str, Any]:
    """Deletes a contact by resource name from your Google Contacts.

    This function deletes a contact from Google Contacts using its specified resource name. Directory contacts or 'otherContacts' cannot be deleted via this method.

    Args:
        resource_name (str): Contact resource name (`people/*`) to delete.

    Returns:
        Dict[str, Any]: A dictionary containing the function's results. The structure includes:
            - "status" (str): Indicates the result of the operation, typically "success".
            - "message" (str): A human-readable summary of the action taken.

    Raises:
        ValidationError: If input arguments fail validation.
        ContactNotFoundError: If the contact is not found in the database.
    """
    # 1. Input Validation
    if not isinstance(resource_name, str) or not resource_name.strip():
        raise custom_errors.ValidationError(
            "The 'resource_name' must be a non-empty string."
        )

    # Note: Deletion is restricted to 'myContacts'.
    # Directory contacts or 'otherContacts' cannot be deleted via this method.
    if resource_name not in DB["myContacts"]:
        raise custom_errors.ContactNotFoundError(
            f"Contact with resource name '{resource_name}' not found."
        )

    # 2. Deletion Logic
    try:
        del DB["myContacts"][resource_name]
    except KeyError:
        # This is a fallback, but the initial check should prevent this.
        raise custom_errors.ContactNotFoundError(
            f"Contact with resource name '{resource_name}' not found."
        )

    # 3. Return successful result
    return {
        "status": "success",
        "message": f"Contact '{resource_name}' was deleted successfully."
    }

@tool_spec(
    spec={
        'name': 'search_contacts',
        'description': """ Search contacts by name, email, phone number, contact notes, or contact organization.
        
        This function searches for contacts using a provided search term. The number of results returned can be limited. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Search term to find in contacts; matches against names, emails, phone numbers, contact notes, and contact organizations.'
                },
                'max_results': {
                    'type': 'integer',
                    'description': 'Maximum number of results to return (default: 10). Must be a positive integer.'
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def search_contacts(query: str, max_results: Optional[int] = 10) -> Dict[str, List[Dict[str, Any]]]:
    """
    Search contacts by name, email, phone number, contact notes, or contact organization.

    This function searches for contacts using a provided search term. The number of results returned can be limited.

    Args:
        query (str): Search term to find in contacts; matches against names, emails, phone numbers, contact notes, and contact organizations.
        max_results (Optional[int]): Maximum number of results to return (default: 10). Must be a positive integer.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary containing the search results.
            The dictionary has the following key:
            - "results" (List[Dict[str, Any]]): A list of contact objects matching the query.
              Each object is a dictionary with a structure like the following:
              - `resourceName` (str): The unique server-assigned identifier for the contact.
              - `etag` (str): An opaque identifier for a specific version of the contact.
              - `names` (List[Dict[str, str]]): A list of name objects, each with
                keys like `givenName` and `familyName`.
              - `emailAddresses` (List[Dict[str, Any]]): A list of email objects, each with
                a `value` (the email address), a `type` (e.g., 'home', 'work'), and an
                optional `primary` boolean flag.
              - `phoneNumbers` (List[Dict[str, Any]]): A list of phone number objects,
                each with a `value` (the number), a `type` (e.g., 'mobile'), and an
                optional `primary` boolean flag.
              - `organizations` (List[Dict[str, str]]): A list of organization objects,
                each with keys like `name` and `title`.
              - `isWorkspaceUser` (Optional[bool]): Indicates whether the contact is a Google Workspace user.
              - `notes` (Optional[str]): Contact notes or additional information about the contact.
              - `whatsapp` (Optional[Dict[str, Any]]): WhatsApp-specific contact information.
              - `phone` (Optional[Dict[str, Any]]): Native phone contact information.
              Note: Not all fields are guaranteed to be present in every contact object.

    Raises:
        ValidationError: If input arguments fail validation.
        DataIntegrityError: If the fetched contact data has an invalid structure.
    """
    # --- Input Validation ---
    if not isinstance(query, str):
        raise custom_errors.ValidationError("Search query must be a string.")

    if max_results is not None:
        if not isinstance(max_results, int):
            raise custom_errors.ValidationError("max_results must be an integer.")
        if max_results < 0:
            raise custom_errors.ValidationError("max_results cannot be negative.")

    limit = max_results if max_results is not None else 10

    # --- Search Execution ---
    all_found_contacts = []
    collections_to_search = ["myContacts", "otherContacts", "directory"]

    for collection in collections_to_search:
        results = utils.search_collection(
            collection_name=collection, query=query, max_results=limit
        )

        # --- In-loop Validation and Dumping (As per your request) ---
        validated_batch = []
        for contact_dict in results:
            try:
                # 1. Validate the dictionary using the Contact model
                contact_model = Contact.model_validate(contact_dict)
                # 2. Dump the validated model back to a dictionary
                validated_batch.append(contact_model.model_dump(exclude_unset=True))
            except PydanticValidationError as e:
                raise custom_errors.DataIntegrityError(
                    f"Invalid data structure in collection '{collection}': {e}"
                )
        
        # 3. Extend the main list with the batch of validated dictionaries
        all_found_contacts.extend(validated_batch)


    # --- Result Processing & De-duplication ---
    unique_contacts = {}
    for contact in all_found_contacts:
        if len(unique_contacts) >= limit:
            break
        # The list now contains dictionaries, so we use .get()
        resource_name = contact.get("resourceName")
        if resource_name and resource_name not in unique_contacts:
            unique_contacts[resource_name] = contact
    
    final_results = list(unique_contacts.values())
    
    return {"results": final_results}

@tool_spec(
    spec={
        'name': 'list_workspace_users',
        'description': """ Lists Google Workspace users in your organization's directory.
        
        This function lists users from the Google Workspace directory. It allows for
        filtering the results based on a search term and controlling the number of
        users returned in a single request. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ Search term to find specific users. The search
                    looks through names, email addresses, and phone numbers. """
                },
                'max_results': {
                    'type': 'integer',
                    'description': """ Maximum number of results to return.
                    Must be a positive integer. Defaults to 50. """
                }
            },
            'required': []
        }
    }
)
def list_workspace_users(query: Optional[str] = None, max_results: Optional[int] = 50
                         ) -> Dict[str, List[Dict[str, Any]]]:
    """Lists Google Workspace users in your organization's directory.

    This function lists users from the Google Workspace directory. It allows for
    filtering the results based on a search term and controlling the number of
    users returned in a single request.

    Args:
        query (Optional[str]): Search term to find specific users. The search
            looks through names, email addresses, and phone numbers.
        max_results (Optional[int]): Maximum number of results to return.
            Must be a positive integer. Defaults to 50.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary where the key 'users'
            contains a list of user profile dictionaries. Each dictionary
            represents a Google Workspace user and has the following structure:
            - 'resourceName' (str): The unique identifier for the user.
            - 'etag' (str): An ETag for the resource, used for optimistic
              concurrency.
            - 'isWorkspaceUser' (bool): Flag indicating if this is a
              Workspace user. Always true in this function's results.
            - 'names' (List[Dict[str, str]]): A list of name objects,
              typically containing one object with 'givenName' and 'familyName'.
            - 'emailAddresses' (List[Dict[str, Any]]): A list of email objects,
              each containing the 'value' (the email address) and a 'primary'
              boolean flag.
            - 'organizations' (List[Dict[str, Any]]): A list of organization
              objects, detailing the user's role, with keys like 'name',
              'title', 'department', and a 'primary' boolean flag.

    Raises:
        ValidationError: If input arguments fail validation.
        DataIntegrityError: If the fetched workspace user data has an invalid structure.
    """
    # Validate the 'max_results' parameter
    if not isinstance(max_results, int):
        raise custom_errors.ValidationError("max_results must be an integer.")
    if not max_results > 0:
        raise custom_errors.ValidationError(
            "max_results must be a positive integer."
        )

    # Validate the 'query' parameter
    if query is not None and not isinstance(query, str):
        raise custom_errors.ValidationError("query must be a string.")

    # Use the helper function to search the 'directory' collection
    # The helper handles the core logic of searching by name, email, etc.
    all_directory_results = utils.search_collection(
        collection_name="directory", query=query, max_results=max_results
    )

    # Ensure that only actual workspace users are returned by checking the flag
    workspace_users = [
        user
        for user in all_directory_results
        if user.get("isWorkspaceUser") is True
    ]

    # Validate the structure of the returned data using Pydantic models
    try:
        validated_response = WorkspaceUserListResponse(users=workspace_users)
    except PydanticValidationError as e:
        # If data from DB doesn't match the model, it's a data integrity issue
        raise custom_errors.DataIntegrityError(
            f"Fetched workspace user data failed validation: {e}"
        )

    # Return the validated data as a dictionary
    return validated_response.model_dump()

@tool_spec(
    spec={
        'name': 'search_directory',
        'description': """ Performs a targeted search of your organization's Google Workspace directory.
        
        Searches for people in the Google Workspace directory. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Search term to find directory members by name, email, or phone number.'
                },
                'max_results': {
                    'type': 'integer',
                    'description': 'Maximum number of results to return.'
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def search_directory(query: str, max_results: Optional[int] = 20) -> List[Dict[str, Any]]:
    """Performs a targeted search of your organization's Google Workspace directory.

    Searches for people in the Google Workspace directory.

    Args:
        query (str): Search term to find directory members by name, email, or phone number.
        max_results (Optional[int]): Maximum number of results to return.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a
        person found in the directory. Each dictionary has the following structure:
            - `resourceName` (str): The unique, server-assigned resource name for the person.
            - `etag` (str): An opaque identifier for the resource's current state, used for caching.
            - `names` (List[Dict]): A list of name objects. Typically contains one primary entry with:
                - `givenName` (str): The person's first name.
                - `familyName` (str): The person's last name.
            - `emailAddresses` (List[Dict]): A list of email address objects, each with:
                - `value` (str): The email address.
                - `primary` (bool): A flag indicating if this is the primary email.
            - `organizations` (List[Dict]): A list of organization objects, each with:
                - `name` (str): The name of the organization (e.g., "YourCompany").
                - `title` (str): The person's job title.
                - `department` (str): The department the person belongs to.
                - `primary` (bool): A flag indicating if this is the primary organization.
            - `isWorkspaceUser` (bool): A boolean flag that is true if the contact is a Google Workspace user.

    Raises:
        ValidationError: If input arguments fail validation.
        DataIntegrityError: If the data retrieved from the directory fails structure validation.
    """
    # --- Input Validation ---
    if not isinstance(query, str) or not query.strip():
        raise custom_errors.ValidationError("The 'query' argument must be a non-empty string.")

    if not isinstance(max_results, int) or max_results <= 0:
        raise custom_errors.ValidationError("The 'max_results' argument must be a positive integer.")

    # --- Search Logic ---
    # Utilize the search_collection helper to perform the search on the 'directory' collection.
    # The helper function is designed to handle matching the query against names, emails, etc.
    results = utils.search_collection(
        collection_name="directory",
        query=query,
        max_results=max_results
    )

    # --- Output Validation ---
    try:
        # Validate the structure of the results from the database.
        validated_response = DirectorySearchResponse(directory_users=results)
        
        # Return the validated data as a list of dictionaries.
        return [user.model_dump(exclude_none=True) for user in validated_response.directory_users]
    
    except PydanticValidationError as e:
        # If validation fails, it indicates a problem with the data in our 'database'.
        raise custom_errors.DataIntegrityError(f"Directory data validation failed: {e}")

@tool_spec(
    spec={
        'name': 'get_other_contacts',
        'description': """ Retrieves contacts from the 'Other contacts' section.
        
        Retrieves contacts from the 'Other contacts' section, which contains people you have interacted with but not explicitly added to your contacts. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'max_results': {
                    'type': 'integer',
                    'description': 'Maximum number of results to return. Must be a positive integer. Defaults to 50.'
                }
            },
            'required': []
        }
    }
)
def get_other_contacts(max_results: Optional[int] = 50) -> List[Dict[str, Any]]:
    """Retrieves contacts from the 'Other contacts' section.

    Retrieves contacts from the 'Other contacts' section, which contains people you have interacted with but not explicitly added to your contacts.

    Args:
        max_results (Optional[int]): Maximum number of results to return. Must be a positive integer. Defaults to 50.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents an 'other' contact. The dictionary has the following structure:
            - `resourceName` (str): The unique identifier for the contact, e.g., "otherContacts/c098...".
            - `etag` (str): An identifier for the current state of the contact.
            - `names` (List[Dict[str, str]]): A list of dictionaries containing name details.
                - `givenName` (str): The contact's first name.
                - `familyName` (str): The contact's last name.
            - `emailAddresses` (List[Dict[str, Any]]): A list of dictionaries for email addresses.
                - `value` (str): The email address string.
                - `type` (str): The type of email (e.g., 'work', 'home').
                - `primary` (bool): True if this is the primary email.
            - `phoneNumbers` (List[Dict[str, Any]]): A list of phone numbers, if available.
                - `value` (str): The phone number string.
                - `type` (str): The type of phone number (e.g., 'mobile', 'work').
                - `primary` (bool): True if this is the primary number.

    Raises:
        ValidationError: If input arguments fail validation.
        ContactsCollectionNotFoundError: If the 'otherContacts' collection doesn't exist in the database.
        DataIntegrityError: If the fetched contact data has an invalid structure.
    """
    if not isinstance(max_results, int) or max_results < 0:
        raise custom_errors.ValidationError("max_results must be a non-negative integer.")

    if "otherContacts" not in DB:
        raise custom_errors.ContactsCollectionNotFoundError("Contacts collection 'otherContacts' not found in the database.")
    # The search_collection helper with a null query lists all items in a collection.
    other_contacts = utils.search_collection(
        collection_name="otherContacts",
        query=None,
        max_results=max_results
    )

    try:
        # Validate the structure of the fetched data against a list of Contacts
        contact_adapter = TypeAdapter(List[Contact])
        validated_contacts = contact_adapter.validate_python(other_contacts)
    except PydanticValidationError as e:
        # If validation fails, raise a custom data integrity error
        raise custom_errors.DataIntegrityError(
            f"Fetched 'other contact' data failed validation: {e}"
        )

    # Return the validated data as a list of dictionaries, excluding unset fields
    return [contact.model_dump(exclude_none=True) for contact in validated_contacts]