from common_utils.tool_spec_decorator import tool_spec
# phone_client/calls.py
import re
import uuid
import time
from typing import Dict, Any, Optional, List, Union
from phone.SimulationEngine.models import (
    RecipientModel, RecipientModelOptionalEndpoints, RecipientEndpointModel, 
    SingleEndpointChoiceModel, MultipleEndpointChoiceModel,
    ChoiceEndpointModel, ShowChoicesResponseModel, PhoneAPIResponseModel
)
from phone.SimulationEngine.db import DB, load_state
from phone.SimulationEngine.utils import (
    add_call_to_history, add_prepared_call, add_recipient_choice, add_not_found_record,
    should_show_recipient_choices, get_recipient_with_single_endpoint, search_contacts_by_name,
    process_recipients_for_call, validate_recipient_contact_consistency
)
from phone.SimulationEngine.custom_errors import (
    PhoneAPIError, InvalidRecipientError, NoPhoneNumberError, 
    MultipleEndpointsError, MultipleRecipientsError, GeofencingPolicyError, ValidationError
)
import os
from common_utils.phone_utils import is_phone_number_valid


@tool_spec(
    spec={
        'name': 'make_call',
        'description': """ Make a call to a single recipient with exactly one phone number endpoint.
        
        To resolve the phone number endpoint, you may have to call one or more tools
        prior to calling this operation. Before calling this operation, always check
        if the Geofencing Policy applies. If there is a recipient with more than one
        phone number endpoints, ask the user for the intended endpoint by invoking
        show_call_recipient_choices. Do not call this operation until the user has
        chosen a single recipient with exactly one phone number endpoint.
        
        The function validates that contact_name and contact_endpoints belong to the same contact
        in the database to prevent mismatched data. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'recipient': {
                    'type': 'object',
                    'description': 'The recipient of the phone call. Contains:',
                    'properties': {
                        'contact_id': {
                            'type': 'string',
                            'description': 'Unique identifier for the contact'
                        },
                        'contact_name': {
                            'type': 'string',
                            'description': 'Name of the contact'
                        },
                        'contact_endpoints': {
                            'type': 'array',
                            'description': 'List of endpoints for the contact (optional - will search if not provided)',
                            'items': {
                                'type': 'object',
                                'properties': {},
                                'required': []
                            }
                        },
                        'contact_photo_url': {
                            'type': 'string',
                            'description': "URL to the contact's profile photo"
                        },
                        'recipient_type': {
                            'type': 'string',
                            'description': 'Type of recipient ("CONTACT", "BUSINESS", "DIRECT", "VOICEMAIL")'
                        },
                        'address': {
                            'type': 'string',
                            'description': 'Address of the recipient'
                        },
                        'distance': {
                            'type': 'string',
                            'description': 'Distance to the recipient'
                        }
                    },
                    'required': []
                },
                'on_speakerphone': {
                    'type': 'boolean',
                    'description': """ If True, the phone call will be placed on the
                    speakerphone. Defaults to False. """
                },
                'recipient_name': {
                    'type': 'string',
                    'description': "The recipient's name."
                },
                'recipient_phone_number': {
                    'type': 'string',
                    'description': """ The phone number of the
                    recipient to make the call to, e.g. "+11234567890". This value is validated for proper format. """
                },
                'recipient_photo_url': {
                    'type': 'string',
                    'description': """ The url to the profile photo
                    of the recipient. """
                }
            },
            'required': []
        }
    }
)
def make_call(
    *,
    recipient: Optional[Dict[str, Union[str, List[Dict[str, str]], None]]] = None,
    on_speakerphone: bool = False,
    recipient_name: Optional[str] = None,
    recipient_phone_number: Optional[str] = None,
    recipient_photo_url: Optional[str] = None
) -> Dict[str, Union[str, int]]:
    """
    Make a call to a single recipient with exactly one phone number endpoint.

    To resolve the phone number endpoint, you may have to call one or more tools
    prior to calling this operation. Before calling this operation, always check
    if the Geofencing Policy applies. If there is a recipient with more than one
    phone number endpoints, ask the user for the intended endpoint by invoking
    show_call_recipient_choices. Do not call this operation until the user has
    chosen a single recipient with exactly one phone number endpoint.

    The function validates that the provided contact_name and contact_endpoints
    actually belong to the same contact in the database to prevent mismatched data.

    Args:
        recipient (Optional[Dict[str, Union[str, List[Dict[str, str]], None]]]): The recipient of the phone call. Contains:
            - contact_id (Optional[str]): Unique identifier for the contact
            - contact_name (Optional[str]): Name of the contact
            - contact_endpoints (Optional[List[Dict]]): List of endpoints for the contact (required - needed to make the call). Each endpoint represents a different phone number (e.g., mobile, work, home).
            - contact_photo_url (Optional[str]): URL to the contact's profile photo
            - recipient_type (Optional[str]): Type of recipient ("CONTACT", "BUSINESS", "DIRECT", "VOICEMAIL")
            - address (Optional[str]): Address of the recipient
            - distance (Optional[str]): Distance to the recipient
        on_speakerphone (bool): If True, the phone call will be placed on the
            speakerphone. Defaults to False.
        recipient_name (Optional[str]): The recipient's name.
        recipient_phone_number (Optional[str]): The phone number of the
            recipient to make the call to, e.g. "+11234567890". This value is validated for proper format.
        recipient_photo_url (Optional[str]): The url to the profile photo
            of the recipient.

    Returns:
        Dict[str, Union[str, int]]: A dictionary representing the observation from the tool
        call, confirming whether the call was successfully made. Contains:
            - status (str): "success" if call was made successfully
            - call_id (str): Unique identifier for the call
            - emitted_action_count (int): Number of actions generated (always 1)
            - templated_tts (str): Text-to-speech message about the call
            - action_card_content_passthrough (str): Content for action card display

    Raises:
        ValidationError: If recipient data is invalid, contact not found, contact_name/endpoints don't match,
            on_speakerphone is not a boolean, or recipient_photo_url is not a valid URL pattern
        NoPhoneNumberError: If no valid phone number can be determined
        MultipleEndpointsError: If recipient has multiple endpoints (use show_call_recipient_choices)
        MultipleRecipientsError: If multiple recipients found (use show_call_recipient_choices)
        GeofencingPolicyError: If geofencing policy applies (use show_call_recipient_choices)
        InvalidRecipientError: If recipient has low confidence match (use show_call_recipient_choices)
        PhoneAPIError: If an unexpected error occurs during call processing
    """
    call_id = str(uuid.uuid4())

    # Validate on_speakerphone parameter type to prevent data integrity issues
    if not isinstance(on_speakerphone, bool):
        raise ValidationError(f"on_speakerphone must be a boolean, got {type(on_speakerphone).__name__}")

    # Validate recipient_photo_url to prevent security vulnerabilities
    if recipient_photo_url is not None and recipient_photo_url.strip():
        if not re.match(r'^(https?://)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$', recipient_photo_url):
            raise ValidationError(f"recipient_photo_url must be a valid URL, got: {recipient_photo_url}")
    
    # Validate recipient input if provided
    validated_recipient = None
    if recipient is not None:
        try:
            validated_recipient = RecipientModelOptionalEndpoints(**recipient)
            # Validate that contact data is consistent with database
            validate_recipient_contact_consistency(validated_recipient)
        except Exception as e:
            raise ValidationError(
                f"Invalid recipient: {str(e)}",
                details={"recipient": recipient, "error": str(e)}
            )
    
    # Validate legacy phone number parameter
    if recipient_phone_number and not is_phone_number_valid(recipient_phone_number):
        raise ValidationError(f"Invalid phone number format: {recipient_phone_number}")

    # Determine the phone number to call
    phone_number = None
    recipient_name_final = None
    recipient_photo_url_final = None
    
    if validated_recipient:
        # Use recipient object data
        phone_number, recipient_name_final, recipient_photo_url_final = process_recipients_for_call(
            [validated_recipient.model_dump()], validated_recipient.contact_name
        )

    # Fallback to individual parameters if not found in recipient object
    if not phone_number:
        phone_number = recipient_phone_number
    if not recipient_name_final:
        recipient_name_final = recipient_name
    if not recipient_photo_url_final:
        recipient_photo_url_final = recipient_photo_url
    
    # If still no phone number, try to resolve from contacts by name
    # Priority: contact_name from recipient object, then top-level recipient_name
    if not phone_number:
        # Try names in priority order: contact_name from recipient object first, then recipient_name
        names_to_try = [
            (validated_recipient.contact_name if validated_recipient else None),
            recipient_name
        ]
        
        for name_to_search in names_to_try:
            if not phone_number and name_to_search:
                matching_contacts = search_contacts_by_name(name_to_search)
                
                recipients = []
                for contact in matching_contacts:
                    phone_data = contact.get("phone", {})
                    if phone_data:
                        recipients.append({
                            "contact_id": phone_data.get("contact_id"),
                            "contact_name": phone_data.get("contact_name"),
                            "contact_endpoints": phone_data.get("contact_endpoints", []),
                            "contact_photo_url": phone_data.get("contact_photo_url"),
                            "recipient_type": phone_data.get("recipient_type"),
                            "address": phone_data.get("address"),
                            "distance": phone_data.get("distance")
                        })
                
                if recipients:
                    resolved_phone, resolved_name, resolved_photo = process_recipients_for_call(recipients, name_to_search)
                    if resolved_phone:
                        phone_number = resolved_phone
                        recipient_name_final = resolved_name or name_to_search
                        recipient_photo_url_final = resolved_photo or recipient_photo_url
    
    if not phone_number:
        raise NoPhoneNumberError(
            "I couldn't determine the phone number to call. Please provide a valid phone number or recipient information.",
            details={
                "recipient": validated_recipient.model_dump() if validated_recipient else None,
                "recipient_name": recipient_name,
                "recipient_phone_number": recipient_phone_number
            }
        )
    
    # Simulate making the call
    try:
        # Update the database to simulate call history
        call_record = {
            "call_id": call_id,
            "timestamp": time.time(),
            "phone_number": phone_number,
            "recipient_name": recipient_name_final,
            "recipient_photo_url": recipient_photo_url_final,
            "on_speakerphone": on_speakerphone,
            "status": "completed"
        }
        
        # Add to call history in DB
        add_call_to_history(call_record)
    
        # Generate response message
        speakerphone_text = " on speakerphone" if on_speakerphone else ""
        recipient_text = f" to {recipient_name_final}" if recipient_name_final else ""
        
        output = {
            "status": "success",
            "call_id": call_id,
            "emitted_action_count": 1,
            "templated_tts": f"Calling{recipient_text} at {phone_number}{speakerphone_text}.",
            "action_card_content_passthrough": f"Call completed successfully to {phone_number}"
        }

        return output
    
    except PhoneAPIError:
        # Re-raise custom errors as-is
        raise
    except Exception as e:
        # Convert unexpected errors to PhoneAPIError
        raise PhoneAPIError(
            f"Sorry, I encountered an error while making the call: {str(e)}",
            details={
                "phone_number": phone_number,
                "recipient_name": recipient_name_final,
                "on_speakerphone": on_speakerphone,
                "original_error": str(e)
            }
        )


@tool_spec(
    spec={
        'name': 'prepare_call',
        'description': 'Prepare a call to one or more recipients, given provided recipient information.',
        'parameters': {
            'type': 'object',
            'properties': {
                'recipients': {
                    'type': 'array',
                    'description': """ A list of recipient objects to
                    prepare call cards for. Each recipient dict contains: """,
                    'items': {
                        'type': 'object',
                        'properties': {
                            'contact_id': {
                                'type': 'string',
                                'description': 'Unique identifier for the contact'
                            },
                            'contact_name': {
                                'type': 'string',
                                'description': 'Name of the contact'
                            },
                            'contact_endpoints': {
                                'type': 'array',
                                'description': 'List of endpoints for the contact (optional - will search if not provided)',
                                'items': {
                                    'type': 'object',
                                    'properties': {},
                                    'required': []
                                }
                            },
                            'contact_photo_url': {
                                'type': 'string',
                                'description': "URL to the contact's profile photo"
                            },
                            'recipient_type': {
                                'type': 'string',
                                'description': 'Type of recipient ("CONTACT", "BUSINESS", "DIRECT", "VOICEMAIL")'
                            },
                            'address': {
                                'type': 'string',
                                'description': 'Address of the recipient'
                            },
                            'distance': {
                                'type': 'string',
                                'description': 'Distance to the recipient'
                            }
                        },
                        'required': []
                    }
                }
            },
            'required': []
        }
    }
)
def prepare_call(
    *,
    recipients: Optional[List[Dict[str, Union[str, List[Dict[str, str]], None]]]] = None
) -> Dict[str, Union[str, int, List[Union[Dict[str, Union[str, List[Dict[str, str]], None]], str]]]]:
    """
    Prepare a call to one or more recipients, given provided recipient information.

    Args:
        recipients (Optional[List[Dict[str, Union[str, List[Dict[str, str]], None]]]]): A list of recipient objects to
            prepare call cards for. Each recipient dict contains:
            - contact_id (Optional[str]): Unique identifier for the contact
            - contact_name (Optional[str]): Name of the contact
            - contact_endpoints (Optional[List[Dict]]): List of endpoints for the contact (required - needed to show choices). Each endpoint represents a different phone number (e.g., mobile, work, home).
            - contact_photo_url (Optional[str]): URL to the contact's profile photo
            - recipient_type (Optional[str]): Type of recipient ("CONTACT", "BUSINESS", "DIRECT", "VOICEMAIL")
            - address (Optional[str]): Address of the recipient
            - distance (Optional[str]): Distance to the recipient

    Returns:
        Dict[str, Union[str, int, List[Union[Dict[str, Union[str, List[Dict[str, str]], None]], str]]]]: A dictionary representing the observation from the tool
        call, containing information about the generated call cards.
    
    Raises:
        ValidationError: If the recipients data is invalid or empty.
        NoPhoneNumberError: If no phone number could be determined for a recipient.
        MultipleEndpointsError: If a recipient has multiple phone number endpoints.
        GeofencingPolicyError: If the geofencing policy applies.
        InvalidRecipientError: If a recipient is invalid or not suitable for calling.
    """
    call_id = str(uuid.uuid4())
    
    # Validate recipients input if provided
    validated_recipients = []
    if recipients is not None:
        for i, recipient in enumerate(recipients):
            try:
                validated_recipient = RecipientModelOptionalEndpoints(**recipient)
                validated_recipients.append(validated_recipient)

            except Exception as e:
                raise ValidationError(
                    f"Invalid recipient at index {i}: {str(e)}",
                    details={"recipient_index": i, "recipient": recipient, "error": str(e)}
                )
    
    if not validated_recipients:
        raise ValidationError(
            "No recipients provided to prepare call cards for.",
            details={
                "recipients": recipients,
                "validated_count": len(validated_recipients)
            }
        )
    
    # Check if any recipients require user choice or have missing endpoints
    # For prepare_call, we only care about multiple endpoints per recipient, not multiple recipients
    for recipient in validated_recipients:
        # Check if recipient has endpoints (required according to phone.json)
        if not recipient.contact_endpoints or len(recipient.contact_endpoints) == 0:
            raise NoPhoneNumberError(
                f"Recipient {recipient.contact_name} does not have any phone number endpoints. All applicable fields should be populated for prepare_call.",
                details={
                    "recipient": recipient.model_dump(),
                    "missing_field": "contact_endpoints"
                }
            )
        
        recipient_dict = recipient.model_dump()
        should_show, reason = should_show_recipient_choices([recipient_dict])
        if should_show:
            # Raise appropriate errors for individual recipients
            if "Multiple phone numbers found" in reason:
                raise MultipleEndpointsError(
                    f"I found multiple phone numbers for {recipient.contact_name}. Please use show_call_recipient_choices to select the desired endpoint.",
                    details={
                        "recipient": recipient_dict,
                        "reason": reason
                    }
                )
            elif "Geofencing policy applies" in reason:
                raise GeofencingPolicyError(
                    f"The business {recipient.contact_name} is {recipient.distance} away. Please use show_call_recipient_choices to confirm you want to call this business.",
                    details={
                        "recipient": recipient_dict,
                        "reason": reason
                    }
                )
            elif "Low confidence match" in reason:
                raise InvalidRecipientError(
                    f"I found a low confidence match for {recipient.contact_name}. Please use show_call_recipient_choices to confirm this is the correct recipient.",
                    details={
                        "recipient": recipient_dict,
                        "reason": reason
                    }
                )
    
    # Generate call cards for each recipient
    call_cards = []
    for recipient in validated_recipients:
        card = {
            "recipient_name": recipient.contact_name,
            "recipient_photo_url": recipient.contact_photo_url,
            "recipient_type": recipient.recipient_type,
            "address": recipient.address,
            "distance": recipient.distance,
            "endpoints": []
        }
        
        if recipient.contact_endpoints:
            for endpoint in recipient.contact_endpoints:
                card["endpoints"].append({
                    "type": endpoint.endpoint_type,
                    "value": endpoint.endpoint_value,
                    "label": endpoint.endpoint_label
                })
        
        call_cards.append(card)
    
    # Store prepared call cards in DB
    prepared_call_record = {
        "call_id": call_id,
        "timestamp": time.time(),
        "recipients": call_cards
    }
    add_prepared_call(prepared_call_record)
    
    # Note: Changes are kept in memory only, not persisted to file
    
    output = {
        "status": "success",
        "call_id": call_id,
        "emitted_action_count": len(call_cards),
        "templated_tts": f"Prepared {len(call_cards)} call card(s) for you.",
        "action_card_content_passthrough": f"Generated {len(call_cards)} call card(s)"
    }

    return output



@tool_spec(
    spec={
        'name': 'show_call_recipient_choices',
        'description': """ Show a list of one or more recipients to the user to choose from.
        
        This operation uses a UI component to show the list of choices. You do not
        need to enumerate the list of choices in your final response. If you call
        this operation, you may not call other operations from this tool before
        drafting the final response.
        
        The function validates that contact_name and contact_endpoints belong to the same contact
        in the database to prevent mismatched data.
        
        Invoke this operation in the following scenarios:
            * There are multiple recipients (contacts or businesses) to choose from.
            * There are multiple phone number endpoints for a business to choose from.
            * There are multiple phone number endpoints for a single contact to choose from.
            * There is a single contact recipient with `confidence_level` LOW.
            * The Geofencing Policy applies. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'recipients': {
                    'type': 'array',
                    'description': """ A list of recipient objects to
                    display as choices. Each recipient dict contains: """,
                    'items': {
                        'type': 'object',
                        'properties': {
                            'contact_id': {
                                'type': 'string',
                                'description': 'Unique identifier for the contact'
                            },
                            'contact_name': {
                                'type': 'string',
                                'description': 'Name of the contact'
                            },
                            'contact_endpoints': {
                                'type': 'array',
                                'description': 'List of phone number endpoints for the contact (required - needed to show choices). Each endpoint represents a different phone number (e.g., mobile, work, home).',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'endpoint_type': {
                                            'type': 'string',
                                            'description': "Endpoint type. Defaults to 'PHONE_NUMBER' if not specified.",
                                            'enum': ['PHONE_NUMBER'],
                                            'default': 'PHONE_NUMBER'
                                        },
                                        'endpoint_value': {
                                            'type': 'string',
                                            'description': "Phone number in E.164 format (e.g., '+11234567890'). If the recipient type is VOICEMAIL, always set this field to '*86'.",
                                            'pattern': '^\\+?[1-9]\\d{1,14}$|^\\*86$'
                                        },
                                        'endpoint_label': {
                                            'type': 'string',
                                            'description': 'Human-readable label for the endpoint (e.g., "Mobile", "Work", "Home").'
                                        }
                                    },
                                    'required': ['endpoint_value']
                                }
                            },
                            'contact_photo_url': {
                                'type': 'string',
                                'description': "URL to the contact's profile photo"
                            },
                            'recipient_type': {
                                'type': 'string',
                                'description': 'Type of recipient ("CONTACT", "BUSINESS", "DIRECT", "VOICEMAIL")'
                            },
                            'address': {
                                'type': 'string',
                                'description': 'Address of the recipient'
                            },
                            'distance': {
                                'type': 'string',
                                'description': 'Distance to the recipient'
                            }
                        },
                        'required': ['contact_endpoints']
                    }
                }
            },
            'required': []
        }
    }
)

def show_call_recipient_choices(
    *,
    recipients: Optional[List[Dict[str, Union[str, List[Dict[str, str]], None]]]] = None
) -> Dict[str, Union[str, int, List[Union[Dict[str, str]]]]]:
    """
    Show a list of one or more recipients to the user to choose from.

    This operation uses a UI component to show the list of choices. You do not
    need to enumerate the list of choices in your final response. If you call
    this operation, you may not call other operations from this tool before
    drafting the final response.

    The function validates that the provided contact_name and contact_endpoints
    actually belong to the same contact in the database to prevent mismatched data.

    Invoke this operation in the following scenarios:
        * There are multiple recipients (contacts or businesses) to choose from.
        * There are multiple phone number endpoints for a business to choose from.
        * There are multiple phone number endpoints for a single contact to choose from.
        * There is a single contact recipient with `confidence_level` LOW.
        * The Geofencing Policy applies.

    Args:
        recipients (Optional[List[Dict[str, Union[str, List[Dict[str, str]], None]]]]): A list of recipient objects to
            display as choices. Each recipient dict contains:
            - contact_id (Optional[str]): Unique identifier for the contact
            - contact_name (Optional[str]): Name of the contact
            - contact_endpoints ([List[Dict[str, str]]]): List of phone number endpoints for the contact (required - needed to show choices).
                Each endpoint represents a different phone number (e.g., mobile, work, home). Required fields:
                - endpoint_value (str): Phone number in E.164 format (e.g., '+11234567890'). 
                  If recipient_type is VOICEMAIL, must be '*86'.
                Optional fields:
                - endpoint_type (str): Endpoint type. Defaults to 'PHONE_NUMBER' if not specified.
                - endpoint_label (Optional[str]): Human-readable label (e.g., "Mobile", "Work", "Home").
            - contact_photo_url (Optional[str]): URL to the contact's profile photo
            - recipient_type (Optional[str]): Type of recipient ("CONTACT", "BUSINESS", "DIRECT", "VOICEMAIL")
            - address (Optional[str]): Address of the recipient
            - distance (Optional[str]): Distance to the recipient

    Returns:
        Dict[str, Union[str, int, List[Union[Dict[str, str]]]]]: A dictionary containing:
            - status (str): Operation status, always "success"
            - call_id (str): Unique identifier for the call session
            - emitted_action_count (int): Number of recipient choices generated
            - templated_tts (str): Text-to-speech message for the user
            - action_card_content_passthrough (str): Content for the action card UI
            - choices (List[Dict]): List of recipient choices, each containing:
                - contact_name (Optional[str]): Name of the contact
                - contact_photo_url (Optional[str]): URL to the contact's profile photo
                - recipient_type (Optional[str]): Type of recipient
                - address (Optional[str]): Address of the recipient
                - distance (Optional[str]): Distance to the recipient
                - endpoints (Optional[List[Dict[str, str]]]): List of phone endpoints, used when recipient has 0-1 phone numbers (single choice with all endpoints).
                    Each endpoint must contain the following fields:
                    - type (str): Endpoint type. Defaults to 'PHONE_NUMBER' if not specified.
                    - value (str): Phone number in E.164 format (e.g., '+11234567890'). If recipient_type is VOICEMAIL, must be '*86'.
                    - label (Optional[str]): Human-readable label (e.g., "Mobile", "Work", "Home").
                - endpoint (Optional[Dict[str, str]]): Single phone endpoint, used when recipient has 2+ phone numbers (separate choice for each endpoint).
                    Each endpoint must contain the following fields:
                    - type (str): Endpoint type. Defaults to 'PHONE_NUMBER' if not specified.
                    - value (str): Phone number in E.164 format (e.g., '+11234567890'). If recipient_type is VOICEMAIL, must be '*86'.
                    - label (Optional[str]): Human-readable label (e.g., "Mobile", "Work", "Home").
                Note: Each choice contains EITHER 'endpoints' OR 'endpoint', never both
    
    Raises:
        ValidationError: If recipient data is invalid, contact not found, or contact_name/endpoints don't match
        PhoneAPIError: If an unexpected error occurs during choice processing
    """
    call_id = str(uuid.uuid4())
    
    # Validate recipients input if provided
    validated_recipients = []
    if recipients is not None:
        for i, recipient in enumerate(recipients):
            try:
                validated_recipient = RecipientModel(**recipient)
                # Validate that contact data is consistent with database
                validate_recipient_contact_consistency(validated_recipient)
                validated_recipients.append(validated_recipient)
            except Exception as e:
                raise ValidationError(
                    f"Invalid recipient at index {i}: {str(e)}",
                    details={"recipient_index": i, "recipient": recipient, "error": str(e)}
                )
    
    if not validated_recipients:
        raise ValidationError(
            "No recipients provided to show choices for.",
            details={
                "recipients": recipients,
                "validated_count": len(validated_recipients)
            }
        )
    
    # Prepare choices for display
    choices = []
    for recipient in validated_recipients:
        try:
            if len(recipient.contact_endpoints) > 1:
                # Multiple endpoints for single recipient - create separate choices for each endpoint
                for endpoint in recipient.contact_endpoints:
                    choice_data = {
                        "contact_name": recipient.contact_name,
                        "contact_photo_url": recipient.contact_photo_url,
                        "recipient_type": recipient.recipient_type,
                        "address": recipient.address,
                        "distance": recipient.distance,
                        "endpoint": {
                            "type": endpoint.endpoint_type,
                            "value": endpoint.endpoint_value,
                            "label": endpoint.endpoint_label
                        }
                    }
                    # Validate the choice with Pydantic
                    choice = MultipleEndpointChoiceModel(**choice_data)
                    choices.append(choice)
            else:
                # Single endpoint - create one choice for the recipient
                choice_data = {
                    "contact_name": recipient.contact_name,
                    "contact_photo_url": recipient.contact_photo_url,
                    "recipient_type": recipient.recipient_type,
                    "address": recipient.address,
                    "distance": recipient.distance,
                    "endpoints": []
                }
                
                # Add all endpoints to the choice (will be exactly 1 since contact_endpoints is required)
                for endpoint in recipient.contact_endpoints:
                    choice_data["endpoints"].append({
                        "type": endpoint.endpoint_type,
                        "value": endpoint.endpoint_value,
                        "label": endpoint.endpoint_label
                    })
                
                # Validate the choice with Pydantic
                choice = SingleEndpointChoiceModel(**choice_data)
                choices.append(choice)
        except Exception as e:
            raise ValidationError(
                f"Failed to create choice for recipient {recipient.contact_name}: {str(e)}",
                details={"recipient": recipient.model_dump(), "error": str(e)}
            )
    # Validate that we have at least one valid choice
    if not choices:
        raise ValidationError(
            "No valid recipients found to show choices for. All recipients failed validation.",
            details={
                "recipients": [r.model_dump() for r in validated_recipients],
                "recipients_count": len(validated_recipients)
            }
        )
    
    # Generate choice text based on actual number of choices
    choice_count = len(choices)
    if choice_count == 1:
        choice = choices[0]
        contact_name = choice.contact_name or "Unknown Contact"
        if hasattr(choice, 'endpoint'):
            # Multiple endpoints case - single choice with specific endpoint
            choice_text = f"Would you like to call {contact_name} at {choice.endpoint.label} ({choice.endpoint.value})?"
        else:
            # Single endpoint case - choice with endpoints array
            choice_text = f"Would you like to call {contact_name}?"
    else:
        choice_text = f"Please choose from {choice_count} options to call."
    
    # Store the choices in DB
    choice_record = {
        "call_id": call_id,
        "timestamp": time.time(),
        "recipient_options": [choice.model_dump() for choice in choices]
    }
    add_recipient_choice(choice_record)

    # Create response data - match the ShowChoicesResponseModel schema
    response_data = {
        "status": "success",
        "call_id": call_id,
        "emitted_action_count": choice_count,
        "templated_tts": choice_text,
        "action_card_content_passthrough": f"Showing {choice_count} recipient choice(s)",
        "choices": choices
    }
    
    # Validate the final response with Pydantic
    try:
        validated_response = ShowChoicesResponseModel(**response_data)
        output = validated_response.model_dump()

        return output
    
    except Exception as e:
        raise ValidationError(
            f"Failed to validate response: {str(e)}",
            details={"response_data": response_data, "error": str(e)}
        )


@tool_spec(
    spec={
        'name': 'show_call_recipient_not_found_or_specified',
        'description': """ Show a message to the user when the call recipient is not found or not specified.
        
        You must attempt to search for a recipient before calling this operation.
        Call this operation when no match is found for a recipient, or when the user
        expresses an intent to call without specifying a recipient. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'contact_name': {
                    'type': 'string',
                    'description': 'The recipient name that was searched for.'
                }
            },
            'required': []
        }
    }
)
def show_call_recipient_not_found_or_specified(
    contact_name: Optional[str] = None
) -> Dict[str, Union[str, int]]:
    """
    Show a message to the user when the call recipient is not found or not specified.

    You must attempt to search for a recipient before calling this operation.
    Call this operation when no match is found for a recipient, or when the user
    expresses an intent to call without specifying a recipient.

    Args:
        contact_name (Optional[str]): The recipient name that was searched for.

    Returns:
        Dict[str, Union[str, int]]: A dictionary representing the observation from the tool call.
    """
    call_id = str(uuid.uuid4())
    
    # Store the not found record in DB
    not_found_record = {
        "call_id": call_id,
        "timestamp": time.time(),
        "contact_name": contact_name
    }
    add_not_found_record(not_found_record)
    
    # Note: Changes are kept in memory only, not persisted to file
    
    # Generate appropriate message
    if contact_name:
        message = f"I couldn't find a contact or business named '{contact_name}' to call. Could you please provide more details or check the spelling?"
    else:
        message = "I need to know who you'd like to call. Could you please specify a name, phone number, or business?"
    
    output = {
        "status": "success",
        "call_id": call_id,
        "emitted_action_count": 0,
        "templated_tts": message,
        "action_card_content_passthrough": "Recipient not found or not specified"
    }

    return output
