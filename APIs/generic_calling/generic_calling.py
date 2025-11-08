from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, List, Dict, Any, Union
from phone import (
    make_call as phone_make_call,
    show_call_recipient_choices as phone_show_call_recipient_choices,
    show_call_recipient_not_found_or_specified as phone_show_call_recipient_not_found,
)
from whatsapp import make_call as whatsapp_make_call
from APIs.whatsapp import send_message as whatsapp_send_message

from generic_calling.SimulationEngine.custom_errors import ValidationError, ContactNotFoundError
from generic_calling.SimulationEngine.models import RecipientModel, RecipientEndpointModel, RecipientInfoModel


@tool_spec(
    spec={
        'name': 'make_call',
        'description': 'Make a call to a single recipient with exactly one phone number endpoint. This function requires both endpoint and recipient_info to be provided. It delegates the actual call to the appropriate service (phone or WhatsApp) based on the endpoint type. The caller is responsible for: - Searching for recipients if needed - Handling multiple recipients/endpoints by calling show_call_recipient_choices - Selecting exactly one endpoint before calling this function',
        'parameters': {
            'type': 'object',
            'properties': {
                'endpoint': {
                    'type': 'object',
                    'description': "The endpoint to call. Contains 'type', 'value', and optionally 'label'.",
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': "The type of endpoint ('PHONE_NUMBER' or 'WHATSAPP_PROFILE')"
                        },
                        'value': {
                            'type': 'string',
                            'description': "The value of the endpoint (e.g. '+1234567890' or '1234567890@s.whatsapp.net')"
                        },
                        'label': {
                            'type': 'string',
                            'description': "The label of the endpoint ('mobile' or 'work')"
                        }
                    },
                    'required': ['type', 'value']
                },
                'recipient_info': {
                    'type': 'object',
                    'description': "Information about the recipient, including 'name' and optionally 'recipient_type', 'address', and 'distance'.",
                    'properties': {
                        'name': {
                            'type': 'string',
                            'description': "The name of the recipient"
                        },
                        'recipient_type': {
                            'type': 'string',
                            'description': "The type of recipient ('CONTACT', 'BUSINESS', 'DIRECT', 'VOICEMAIL')"
                        },
                        'address': {
                            'type': 'string',
                            'description': "The address of the recipient"
                        },
                        'distance': {
                            'type': 'string',
                            'description': "The distance to the recipient"
                        }
                    },
                    'required': ['name']
                },
                'on_speakerphone': {
                    'type': 'boolean',
                    'description': 'If True, the phone call will be placed on the speakerphone. Defaults to False.'
                },
                'video_call': {
                    'type': 'boolean',
                    'description': 'If True, the phone call will be placed on video call. Defaults to False.'
                }
            },
            'required': ['endpoint', 'recipient_info']
        }
    }
)
def make_call(
    endpoint: Dict[str, str],
    recipient_info: Dict[str, str],
    on_speakerphone: bool = False,
    video_call: bool = False,
) -> Dict[str, str]:
    """Make a call to a single recipient with exactly one phone number endpoint.

    This function requires both endpoint and recipient_info to be provided. It delegates 
    the actual call to the appropriate service (phone or WhatsApp) based on the endpoint type.
    
    The caller is responsible for:
    - Searching for recipients if needed
    - Handling multiple recipients/endpoints by calling show_call_recipient_choices
    - Selecting exactly one endpoint before calling this function

    Args:
        endpoint (Dict[str, str]): The endpoint to call. Contains 'type', 'value', and optionally 'label'.
            type (str): The type of endpoint ('PHONE_NUMBER' or 'WHATSAPP_PROFILE')
            value (str): The value of the endpoint (e.g. '+1234567890' or '1234567890@s.whatsapp.net')
            label (Optional[str]): The label of the endpoint ('mobile' or 'work')
        recipient_info (Dict[str, str]): Information about the recipient, including 'name' and optionally 
            'recipient_type', 'address', and 'distance'.
            name (str): The name of the recipient
            recipient_type (Optional[str]): The type of recipient ('CONTACT', 'BUSINESS', 'DIRECT', 'VOICEMAIL')
            address (Optional[str]): The address of the recipient
            distance (Optional[str]): The distance to the recipient
        on_speakerphone (bool): If True, the phone call will be placed on the speakerphone. Defaults to False.
        video_call (bool): If True, the phone call will be a video call. Defaults to False.

    Returns:
        Dict[str, Union[str, int]]: A dictionary representing the observation from the tool
        call, confirming whether the call was successfully made. Contains:
            - status (str): "success" if call was made successfully
            - call_id (str): Unique identifier for the call
            - emitted_action_count (int): Number of actions generated (always 1)
            - templated_tts (str): Text-to-speech message about the call
            - action_card_content_passthrough (str): Content for action card display

    Raises:
        ValidationError: If recipient data is invalid, contact not found, or contact_name/endpoints don't match
    """
    if not (endpoint and recipient_info):
        raise ValidationError("Both endpoint and recipient_info are required to make a call.")

    if not (isinstance(on_speakerphone, bool) and isinstance(video_call, bool)):
        raise ValidationError("Both on_speakerphone and video_call should be bool values.")

    try:
        # Validate recipient_info using RecipientInfoModel
        validated_recipient_info = RecipientInfoModel(**recipient_info)
        
        # Map endpoint to RecipientEndpointModel format
        endpoint_data = {
            "endpoint_type": endpoint.get("type"),
            "endpoint_value": endpoint.get("value"),
            "endpoint_label": endpoint.get("label")
        }
        endpoint = RecipientEndpointModel(**endpoint_data)
    except Exception as e:
        raise ValidationError(f"Invalid recipient: {str(e)}")

    recipient = {
        "contact_name": validated_recipient_info.name,
        "recipient_type": validated_recipient_info.recipient_type,
        "address": validated_recipient_info.address,
        "distance": validated_recipient_info.distance,
        "contact_endpoints": [{
            "endpoint_type": "PHONE_NUMBER",  # WhatsApp service expects PHONE_NUMBER even for WhatsApp profiles
            "endpoint_value": endpoint.endpoint_value,
            "endpoint_label": endpoint.endpoint_label,
        }]
    }

    if endpoint.endpoint_type == "WHATSAPP_PROFILE" or video_call:
        try:
            return whatsapp_make_call(
                recipient=recipient,
                on_speakerphone=on_speakerphone,
                video_call=video_call
            )
        except Exception as e:
            raise  e
    else:  # PHONE_NUMBER
        try:
            return phone_make_call(
                recipient=recipient,
                on_speakerphone=on_speakerphone,
            )
        except Exception as e:
            raise e


@tool_spec(
    spec={
        'name': 'show_call_recipient_choices',
        'description': "Show a list of one or more recipients to the user to choose from. This function acts as a wrapper around the phone service's `show_call_recipient_choices` function. It transforms the generic recipient choice format into the format expected by the phone service.",
        'parameters': {
            'type': 'object',
            'properties': {
                'recipient_choices': {
                    'type': 'array',
                    'description': "A list of recipient objects to display as choices.",
                    'items': {
                        'type': 'object',
                        'description': "A recipient object to display as a choice.",
                        'properties': {
                            'contact_id': {
                                'type': 'string',
                                'description': "Unique identifier for the contact"
                            },
                            'contact_name': {
                                'type': 'string',
                                'description': "Name of the contact"
                            },
                            'contact_endpoints': {
                                'type': 'array',
                                'description': "List of phone number endpoints for the contact.",
                                'items': {
                                    'type': 'object',
                                    'description': "A phone number endpoint for the contact.",
                                    'properties': {
                                        'endpoint_value': {
                                            'type': 'string',
                                            'description': "Phone number in E.164 format (e.g., '+11234567890'). If the recipient type is VOICEMAIL, always set this field to '*86'.",
                                        },
                                        'endpoint_type': {
                                            'type': 'string',
                                            'description': "Endpoint type. Use 'PHONE_NUMBER'.",
                                        },
                                        'endpoint_label': {
                                            'type': 'string',
                                            'description': "Human-readable label for the endpoint (e.g., 'Mobile', 'Work', 'Home').",
                                        }
                                    },
                                    'required': ['endpoint_value', 'endpoint_type']
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
def show_call_recipient_choices(
    recipient_choices: Optional[List[Dict[str, Union[str, List[Dict[str, str]], None]]]] = None,
) -> Dict[str, Any]:
    """Show a list of one or more recipients to the user to choose from.

    This function acts as a wrapper around the phone service's `show_call_recipient_choices`
    function. It transforms the generic recipient choice format into the format expected
    by the phone service.

    Args:
        recipient_choices (Optional[List[Dict[str, Union[str, List[Dict[str, str]], None]]]]): A list of recipient objects to
            display as choices. Each recipient dict contains:
            - contact_id (Optional[str]): Unique identifier for the contact
            - contact_name (Optional[str]): Name of the contact
            - contact_endpoints (Optional[List[Dict[str, str]]]): List of phone number endpoints for the contact.
                Each endpoint represents a different phone number (e.g., mobile, work, home). Required fields:
                - endpoint_value (str): Phone number in E.164 format (e.g., '+11234567890').
                  If recipient_type is VOICEMAIL, must be '*86'.
                Optional fields:
                - endpoint_type (str): Endpoint type. Use 'PHONE_NUMBER'.
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
            - choices (List[Dict[str, Union[str, List[Dict[str, str]], None]]]): List of recipient choices, each containing:
                - contact_name (Optional[str]): Name of the contact
                - contact_photo_url (Optional[str]): URL to the contact's profile photo
                - recipient_type (Optional[str]): Type of recipient
                - address (Optional[str]): Address of the recipient
                - distance (Optional[str]): Distance to the recipient
                - endpoints (List[Dict[str, str]]): List of phone endpoints (for single-endpoint choices)
                - endpoint (Dict[str, str]): Single phone endpoint (for multi-endpoint choices)

    Raises:
        ValidationError: If recipient data is invalid, contact not found, or contact_name/endpoints don't match
        ContactNotFoundError: If no phone numbers are available to show
    """

    validated_recipients = []
    if recipient_choices is not None:
        for i, recipient in enumerate(recipient_choices):
            try:
                # Map the recipient data to RecipientModel format
                recipient_data = {
                    "contact_name": recipient.get("recipient_info", {}).get("name"),
                    "recipient_type": recipient.get("recipient_info", {}).get("recipient_type"),
                    "address": recipient.get("recipient_info", {}).get("address"),
                    "distance": recipient.get("recipient_info", {}).get("distance")
                }
                validated_recipient = RecipientModel(**recipient_data)
                # Store both the validated model and original data for processing
                validated_recipients.append((validated_recipient, recipient))
            except Exception as e:
                raise ValidationError(
                    f"Invalid recipient at index {i}: {str(e)}"
                )
    else:
        raise ValidationError("recipient_choices is required.")

    recipients_for_phone_service = []
    for validated_recipient, original_choice in validated_recipients:
        phone_endpoints = [
            {
                "endpoint_type": "PHONE_NUMBER",
                "endpoint_value": ep.get("value"),
                "endpoint_label": ep.get("label"),
            }
            for ep in original_choice.get("endpoints", []) if ep.get("type") == "PHONE_NUMBER"
        ]

        if not phone_endpoints:
            continue

        recipient = {
            "contact_name": validated_recipient.contact_name,
            "recipient_type": validated_recipient.recipient_type,
            "address": validated_recipient.address,
            "distance": validated_recipient.distance,
            "contact_endpoints": phone_endpoints,
        }
        recipients_for_phone_service.append(recipient)

    if not recipients_for_phone_service:
        raise ContactNotFoundError('No phone numbers available to show.')

    try:
        return phone_show_call_recipient_choices(recipients=recipients_for_phone_service)
    except Exception as e:
        raise e


@tool_spec(
    spec={
        'name': 'show_call_recipient_not_found_or_specified',
        'description': "Show a message to the user when the call recipient is not found or not specified. This is a simple wrapper around the phone service's `show_call_recipient_not_found_or_specified` function.",
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'The recipient name that was searched for.'
                }
            },
            'required': []
        }
    }
)
def show_call_recipient_not_found_or_specified(
    name: Optional[str] = None
) -> Dict[str, Union[str, int]]:
    """Show a message to the user when the call recipient is not found or not specified.

    This is a simple wrapper around the phone service's `show_call_recipient_not_found_or_specified`
    function.

    Args:
        name (Optional[str]): The name of the recipient that was searched for.

    Returns:
        Dict[str, Union[str, int]]: The result from the underlying phone service. The keys are:
        - status (str): "success" if call was made successfully
        - call_id (str): Unique identifier for the call
        - emitted_action_count (int): Number of actions generated (always 1)
        - templated_tts (str): Text-to-speech message about the call
        - action_card_content_passthrough (str): Content for action card display
    
    Raises:
        ValidationError: If name is not a string or is empty
    """
    if not isinstance(name, str):
        raise ValidationError("name must be a string.")
    if not name.strip():
        raise ValidationError("name must not be empty.")
    try:
        return phone_show_call_recipient_not_found(contact_name=name)
    except Exception as e:
        raise e
