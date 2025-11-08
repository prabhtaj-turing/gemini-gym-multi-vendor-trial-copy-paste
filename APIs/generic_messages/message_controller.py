from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict, List, Optional, Union
from .SimulationEngine.models import (
    validate_send,
    validate_show_recipient_choices,
    validate_ask_for_message_body,
)
from .SimulationEngine.custom_errors import (
    InvalidRecipientError,
    InvalidEndpointError,
    MessageBodyRequiredError,
    InvalidMediaAttachmentError
)
from APIs import messages, whatsapp


@tool_spec(
    spec={
        'name': 'send',
        'description': """ Send a message to a recipient containing a single endpoint.
        
        This method sends a message to a recipient via SMS or WhatsApp. 
        The message can include text and optional media (images, videos, documents, audio). """,
        'parameters': {
            'type': 'object',
            'properties': {
                'contact_name': {
                    'type': 'string',
                    'description': 'The name of the contact'
                },
                'endpoint': {
                    'type': 'object',
                    'description': """ The endpoint object containing type and value.
                    Expected structure: """,
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': """ Endpoint type. Must be either "PHONE_NUMBER"
                               for SMS or "WHATSAPP_PROFILE" for WhatsApp """
                        },
                        'value': {
                            'type': 'string',
                            'description': """ The endpoint value. For PHONE_NUMBER, use
                               E.164 format (e.g., '+14155552671'). For WHATSAPP_PROFILE,
                              use format {number}@s.whatsapp.net """
                        },
                        'label': {
                            'type': 'string',
                            'description': "Label for the endpoint (e.g., 'mobile', 'work')"
                        }
                    },
                    'required': [
                        'type',
                        'value'
                    ]
                },
                'body': {
                    'type': 'string',
                    'description': """ The text message content to send to the recipient. 
                    Should use correct grammar, capitalization, and punctuation. If the 
                    message body contains a list of items, format it as a bulleted list 
                    with asterisks. Optional - can be None or empty if media_attachments are provided. 
                    At least one of body or media_attachments must be provided. """
                },
                'media_attachments': {
                    'type': 'array',
                    'description': """ Metadata associated with media payload. Supports images, videos, 
                    documents, and audio files. Each attachment should contain:
                    Note: For SMS endpoints, all fields (media_id, media_type, source) are required.
                    For WhatsApp endpoints, media_id and media_type are required; source is optional.
                    For WhatsApp, media is sent using whatsapp.send_file() or whatsapp.send_audio_message() 
                    based on media_type, and text is sent as a separate message to ensure complete delivery. 
                    For SMS endpoints, media and text are sent together via the messages service. 
                    When multiple attachments are sent to WhatsApp, they are sent as separate messages. """,
                    'items': {
                        'type': 'object',
                        'properties': {
                            'media_id': {
                                'type': 'string',
                                'description': 'File path or URL to the media (required for all endpoints)'
                            },
                            'media_type': {
                                'type': 'string',
                                'description': """ Type of media ("IMAGE", "VIDEO", "DOCUMENT", or "AUDIO").
                                   Required for all endpoints. """
                            },
                            'source': {
                                'type': 'string',
                                'description': """ Source of media ("IMAGE_RETRIEVAL", "IMAGE_GENERATION",
                                   "IMAGE_UPLOAD", or "GOOGLE_PHOTO"). Required for SMS endpoints, optional for WhatsApp endpoints. """
                            }
                        },
                        'required': [
                            'media_id',
                            'media_type'
                        ]
                    }
                }
            },
            'required': [
                'contact_name',
                'endpoint'
            ]
        }
    }
)
def send(
    contact_name: str,
    endpoint: Dict[str, Any],
    body: Optional[str] = None,
    media_attachments: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Send a message to a recipient containing a single endpoint.
    
    This method sends a message to a recipient via SMS or WhatsApp. 
    The message can include text and optional media (images, videos, documents, audio).
    
    Args:
        contact_name (str): The name of the contact
        endpoint (Dict[str, Any]): The endpoint object containing type and value.
            Expected structure:
            - type (str): Endpoint type. Must be either "PHONE_NUMBER" 
              for SMS or "WHATSAPP_PROFILE" for WhatsApp
            - value (str): The endpoint value. For PHONE_NUMBER, use 
              E.164 format (e.g., '+14155552671'). For WHATSAPP_PROFILE, 
              use format {number}@s.whatsapp.net
            - label (Optional[str]): Label for the endpoint (e.g., 'mobile', 'work')
        body (Optional[str]): The text message content to send to the recipient. 
            Should use correct grammar, capitalization, and punctuation. If the 
            message body contains a list of items, format it as a bulleted list 
            with asterisks. Optional - can be None or empty if media_attachments are provided. 
            At least one of body or media_attachments must be provided.
        media_attachments (Optional[List[Dict[str, Any]]]): 
            Metadata associated with media payload. Supports images, videos, 
            documents, and audio files. Each attachment should contain:
            - media_id (str): File path or URL to the media (required for all endpoints)
            - media_type (str): Type of media ("IMAGE", "VIDEO", "DOCUMENT", or "AUDIO"). 
              Required for all endpoints.
            - source (Optional[str]): Source of media ("IMAGE_RETRIEVAL", "IMAGE_GENERATION", 
              "IMAGE_UPLOAD", or "GOOGLE_PHOTO"). Required for SMS endpoints, optional for WhatsApp endpoints.
            Note: For SMS endpoints, all fields (media_id, media_type, source) are required.
            For WhatsApp endpoints, media_id and media_type are required; source is optional.
            For WhatsApp, media is sent using whatsapp.send_file() or whatsapp.send_audio_message() 
            based on media_type, and text is sent as a separate message to ensure complete delivery. 
            For SMS endpoints, media and text are sent together via the messages service. 
            When multiple attachments are sent to WhatsApp, they are sent as separate messages.
    
    Returns:
        Dict[str, Any]: A dictionary containing the operation result with:
            - status (str): "success" if the message was sent successfully, "failed" otherwise
            - sent_message_id (str): Unique identifier for the sent message
            - emitted_action_count (int): Number of actions generated (1 if successful, 0 if failed)
            - action_card_content_passthrough (Optional[str]): Additional content metadata
    
    Raises:
        TypeError: If contact_name is not a string, if endpoint is not a dict,
            if body is not a string or None, or if media_attachments is not a list when provided.
        InvalidRecipientError: If contact_name is empty or contains only whitespace.
        InvalidEndpointError: If endpoint is missing 'type' field, if endpoint is missing 
            'value' field, if endpoint.type is not 'PHONE_NUMBER' or 'WHATSAPP_PROFILE',
            if endpoint.value is empty, if endpoint.value doesn't match E.164 format for 
            PHONE_NUMBER, or if endpoint.value doesn't match JID format for WHATSAPP_PROFILE.
        MessageBodyRequiredError: If both body and media_attachments are None or empty.
        InvalidMediaAttachmentError: If media_attachments contains invalid data, if any 
            attachment is missing 'media_id' field, if any attachment is missing 'media_type' 
            field, or if 'source' field is missing for SMS endpoints (source is optional for WhatsApp).
    """
    # --- Input Validation ---
    if not isinstance(contact_name, str):
        raise TypeError(f"contact_name must be a string, got {type(contact_name).__name__}")
    
    if not contact_name.strip():
        raise InvalidRecipientError("contact_name cannot be empty")
    
    if not isinstance(endpoint, dict):
        raise TypeError(f"endpoint must be a dict, got {type(endpoint).__name__}")
    
    if body is not None and not isinstance(body, str):
        raise TypeError(f"body must be a string or None, got {type(body).__name__}")
    
    # At least one of body or media_attachments must be provided
    if (body is None or not body.strip()) and not media_attachments:
        raise MessageBodyRequiredError("both body and media_attachments cannot be empty")
    
    if media_attachments is not None and not isinstance(media_attachments, list):
        raise TypeError(f"media_attachments must be a list or None, got {type(media_attachments).__name__}")
    
    # --- Input Validation (using Pydantic models via helper) ---
    try:
        validated_data = validate_send(
            contact_name, endpoint, body, media_attachments
        )
    except (TypeError, ValueError, InvalidRecipientError, InvalidEndpointError, 
            MessageBodyRequiredError, InvalidMediaAttachmentError) as e:
        # Re-raise validation errors to be handled by the caller
        raise e

    # --- Core Logic ---
    endpoint_obj = validated_data["endpoint"]
    endpoint_type = endpoint_obj.type
    
    # Determine which service to call based on endpoint type
    if endpoint_type == "PHONE_NUMBER":
        # Call messages service for SMS
        # Build recipient object for messages service
        recipient = {
            "contact_name": validated_data["contact_name"],
            "contact_endpoints": [
                {
                    "endpoint_type": "PHONE_NUMBER",
                    "endpoint_value": endpoint_obj.value,
                    "endpoint_label": endpoint_obj.label
                }
            ]
        }
        
        result = messages.send_chat_message(
            recipient=recipient,
            message_body=validated_data["body"],
            media_attachments=[att.model_dump() for att in validated_data.get("media_attachments", [])] if validated_data.get("media_attachments") else None
        )
        
    elif endpoint_type == "WHATSAPP_PROFILE":
        # Call whatsapp service for WhatsApp
        media_attachments = validated_data.get("media_attachments", [])
        body_text = validated_data["body"]
        
        if media_attachments:
            # WhatsApp with media - send media files without captions, then send body as separate message
            
            # Send all media attachments
            for idx, attachment in enumerate(media_attachments):
                media_id = attachment.media_id
                media_type = attachment.media_type
                
                if media_type == "AUDIO":
                    # Audio messages don't support captions in WhatsApp
                    result_item = whatsapp.send_audio_message(
                        recipient=endpoint_obj.value,
                        media_path=media_id
                    )
                else:
                    # For IMAGE, VIDEO, DOCUMENT, or any other type
                    result_item = whatsapp.send_file(
                        recipient=endpoint_obj.value,
                        media_path=media_id,
                        caption=None
                    )
                
                # Store the first result for the return value
                if idx == 0:
                    result = result_item
            
            # Send body text as a separate message if provided
            if body_text and body_text.strip():
                whatsapp.send_message(
                    recipient=endpoint_obj.value,
                    message=body_text
                )
            
            # Transform whatsapp response to match generic_messages format
            if isinstance(result, dict):
                transformed_result = {
                    "status": "success" if result.get("success") else "failed",
                    "sent_message_id": result.get("message_id"),
                    "emitted_action_count": 1 if result.get("success") else 0,
                    "action_card_content_passthrough": None
                }
                result = transformed_result
        else:
            # WhatsApp text-only message
            # whatsapp.send_message only accepts recipient (JID) and message text
            result = whatsapp.send_message(
                recipient=endpoint_obj.value,
                message=body_text
            )
            
            # Transform whatsapp response to match generic_messages format
            if isinstance(result, dict):
                # Whatsapp returns different format, normalize it
                transformed_result = {
                    "status": "success" if result.get("success") else "failed",
                    "sent_message_id": result.get("message_id"),
                    "emitted_action_count": 1 if result.get("success") else 0,
                    "action_card_content_passthrough": None
                }
                result = transformed_result
    else:
        raise InvalidEndpointError(f"Unsupported endpoint type: {endpoint_type}")
    
    # Return the observation response from the underlying service
    return result


@tool_spec(
    spec={
        'name': 'show_message_recipient_choices',
        'description': """ Display potential recipients in a card for user selection.
        
        This method displays a list of one or more recipients that the user can choose 
        to send a message to. It is used when there are multiple recipients or when 
        a single recipient has multiple endpoints, requiring user clarification. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'recipients': {
                    'type': 'array',
                    'description': """ List of possible recipients to send the message to. 
                    Each recipient should contain: """,
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {
                                'type': 'string',
                                'description': 'The name of the contact'
                            },
                            'endpoints': {
                                'type': 'array',
                                'description': 'List of endpoints for the contact. Each endpoint should contain:',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'type': {
                                            'type': 'string',
                                            'description': """ Endpoint type. Must be either "PHONE_NUMBER" for SMS
                                                   or "WHATSAPP_PROFILE" for WhatsApp """
                                        },
                                        'value': {
                                            'type': 'string',
                                            'description': """ The endpoint value. For PHONE_NUMBER, use E.164 format
                                                   (e.g., '+14155552671'). For WHATSAPP_PROFILE, use format {number}@s.whatsapp.net """
                                        },
                                        'label': {
                                            'type': 'string',
                                            'description': "Label for the endpoint (e.g., 'mobile', 'work')"
                                        }
                                    },
                                    'required': [
                                        'type',
                                        'value'
                                    ]
                                }
                            }
                        },
                        'required': [
                            'name',
                            'endpoints'
                        ]
                    }
                }
            },
            'required': [
                'recipients'
            ]
        }
    }
)
def show_message_recipient_choices(
    recipients: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Display potential recipients in a card for user selection.
    
    This method displays a list of one or more recipients that the user can choose 
    to send a message to. It is used when there are multiple recipients or when 
    a single recipient has multiple endpoints, requiring user clarification.
    
    Args:
        recipients (List[Dict[str, Any]]): List of possible recipients to send the message to. 
            Each recipient should contain:
            - name (str): The name of the contact 
            - endpoints (List[Dict]): List of endpoints for the contact. Each endpoint should contain:
                - type (str): Endpoint type. Must be either "PHONE_NUMBER" for SMS 
                  or "WHATSAPP_PROFILE" for WhatsApp
                - value (str): The endpoint value. For PHONE_NUMBER, use E.164 format 
                  (e.g., '+14155552671'). For WHATSAPP_PROFILE, use format {number}@s.whatsapp.net
                - label (Optional[str]): Label for the endpoint (e.g., 'mobile', 'work')
    
    Returns:
        Dict[str, Any]: A dictionary containing the display result with:
            - status (str): "choices_displayed" indicating choices were shown
            - sent_message_id (Optional[str]): Always None for choice operations
            - emitted_action_count (int): Number of actions generated (always 0)
            - action_card_content_passthrough (Optional[str]): Additional content metadata
    
    Raises:
        TypeError: If recipients is not a list.
        ValueError: If recipients list is empty.
        InvalidRecipientError: If any recipient is missing 'name' field, if any recipient 
            has empty name, if any recipient is missing 'endpoints' field, if any recipient 
            has empty endpoints list, if endpoints is not a list.
        InvalidEndpointError: If any endpoint is missing 'type' field, if any endpoint is 
            missing 'value' field, if any endpoint.type is not 'PHONE_NUMBER' or 
            'WHATSAPP_PROFILE', if any endpoint.value is empty, if any endpoint.value 
            doesn't match E.164 format for PHONE_NUMBER, or if any endpoint.value doesn't 
            match JID format for WHATSAPP_PROFILE.
    """
    # --- Input Validation ---
    if not isinstance(recipients, list):
        raise TypeError(f"recipients must be a list, got {type(recipients).__name__}")
    
    if not recipients:
        raise ValueError("recipients list cannot be empty")
    
    # --- Core Logic ---
    # Validate input using the validation function
    validated_data = validate_show_recipient_choices(recipients)
    
    # Determine the channel based on the first recipient's first endpoint
    # For display purposes, we use the messages service as it handles recipient choices
    # Note: This is a UI operation, not channel-specific
    formatted_recipients = []
    for recipient_obj in validated_data["recipients"]:
        formatted_recipient = {
            "contact_name": recipient_obj.name,
            "contact_endpoints": [
                {
                    "endpoint_type": ep.type,
                    "endpoint_value": ep.value,
                    "endpoint_label": ep.label
                }
                for ep in recipient_obj.endpoints
            ]
        }
        formatted_recipients.append(formatted_recipient)
    
    # Use messages service to show recipient choices (this is a UI operation)
    result = messages.show_message_recipient_choices(
        recipients=formatted_recipients
    )
    
    return result


@tool_spec(
    spec={
        'name': 'ask_for_message_body',
        'description': """ Display recipient and ask user for message body.
        
        This method displays the recipient in a card shown to the user, with the intent 
        to ask the user to provide the message body. It is used when there is a single 
        recipient with a single endpoint, but the user has not specified a message body. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'contact_name': {
                    'type': 'string',
                    'description': 'The name of the contact (required)'
                },
                'endpoint': {
                    'type': 'object',
                    'description': """ The endpoint object containing type and value.
                    Expected structure: """,
                    'properties': {
                        'type': {
                            'type': 'string',
                            'description': """ Endpoint type. Must be either "PHONE_NUMBER" for SMS
                               or "WHATSAPP_PROFILE" for WhatsApp """
                        },
                        'value': {
                            'type': 'string',
                            'description': """ The endpoint value. For PHONE_NUMBER, use E.164 format
                               (e.g., '+14155552671'). For WHATSAPP_PROFILE, use format {number}@s.whatsapp.net """
                        },
                        'label': {
                            'type': 'string',
                            'description': "Label for the endpoint (e.g., 'mobile', 'work')"
                        }
                    },
                    'required': [
                        'type',
                        'value'
                    ]
                }
            },
            'required': [
                'contact_name',
                'endpoint'
            ]
        }
    }
)
def ask_for_message_body(
    contact_name: str,
    endpoint: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Display recipient and ask user for message body.
    
    This method displays the recipient in a card shown to the user, with the intent 
    to ask the user to provide the message body. It is used when there is a single 
    recipient with a single endpoint, but the user has not specified a message body.
    
    Args:
        contact_name (str): The name of the contact (required)
        endpoint (Dict[str, Any]): The endpoint object containing type and value.
            Expected structure:
            - type (str): Endpoint type. Must be either "PHONE_NUMBER" for SMS 
              or "WHATSAPP_PROFILE" for WhatsApp
            - value (str): The endpoint value. For PHONE_NUMBER, use E.164 format 
              (e.g., '+14155552671'). For WHATSAPP_PROFILE, use format {number}@s.whatsapp.net
            - label (Optional[str]): Label for the endpoint (e.g., 'mobile', 'work')
    
    Returns:
        Dict[str, Any]: A dictionary containing the request result with:
            - status (str): "asking_for_message_body" indicating body was requested
            - sent_message_id (Optional[str]): Always None for request operations
            - emitted_action_count (int): Number of actions generated (always 0)
            - action_card_content_passthrough (Optional[str]): Additional content metadata
    
    Raises:
        TypeError: If contact_name is not a string or if endpoint is not a dict.
        InvalidRecipientError: If contact_name is empty or contains only whitespace.
        InvalidEndpointError: If endpoint is missing 'type' field, if endpoint is missing 
            'value' field, if endpoint.type is not 'PHONE_NUMBER' or 'WHATSAPP_PROFILE',
            if endpoint.value is empty, if endpoint.value doesn't match E.164 format for 
            PHONE_NUMBER, or if endpoint.value doesn't match JID format for WHATSAPP_PROFILE.
    """
    # --- Input Validation ---
    if not isinstance(contact_name, str):
        raise TypeError(f"contact_name must be a string, got {type(contact_name).__name__}")
    
    if not contact_name.strip():
        raise InvalidRecipientError("contact_name cannot be empty")
    
    if not isinstance(endpoint, dict):
        raise TypeError(f"endpoint must be a dict, got {type(endpoint).__name__}")
    
    # --- Core Logic ---
    # Validate input using the validation function
    validated_data = validate_ask_for_message_body(contact_name, endpoint)
    
    endpoint_obj = validated_data["endpoint"]
    
    # Use messages service to ask for message body (this is a UI operation)
    recipient = {
        "contact_name": validated_data["contact_name"],
        "contact_endpoints": [
            {
                "endpoint_type": endpoint_obj.type,
                "endpoint_value": endpoint_obj.value,
                "endpoint_label": endpoint_obj.label
            }
        ]
    }
    
    result = messages.ask_for_message_body(recipient=recipient)
    
    return result


@tool_spec(
    spec={
        'name': 'show_message_recipient_not_found_or_specified',
        'description': """ Inform the user that the message recipient is not found or not specified.
        
        This method is used to inform the user that the message recipient is not found 
        or not specified. It is invoked when there are no contacts returned from contact 
        search or when the user has not specified a contact name in the query. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'contact_name': {
                    'type': 'string',
                    'description': """ The recipient name that was searched for.
                    May be None if no name was provided in the search. Empty or whitespace-only 
                    strings are normalized to None. """
                }
            },
            'required': []
        }
    }
)
def show_message_recipient_not_found_or_specified(
    contact_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Inform the user that the message recipient is not found or not specified.
    
    This method is used to inform the user that the message recipient is not found 
    or not specified. It is invoked when there are no contacts returned from contact 
    search or when the user has not specified a contact name in the query.
    
    Args:
        contact_name (Optional[str]): The recipient name that was searched for.
            May be None if no name was provided in the search. Empty or whitespace-only 
            strings are normalized to None.
    
    Returns:
        Dict[str, Any]: A dictionary containing the notification result with:
            - status (str): "recipient_not_found" indicating no recipient was found
            - sent_message_id (Optional[str]): Always None for notification operations
            - emitted_action_count (int): Number of actions generated (always 0)
            - action_card_content_passthrough (Optional[str]): Additional content metadata
    
    Raises:
        TypeError: If contact_name is not a string when provided.
    """
    # --- Input Validation ---
    if contact_name is not None and not isinstance(contact_name, str):
        raise TypeError(f"contact_name must be a string or None, got {type(contact_name).__name__}")
    
    # Normalize empty/whitespace-only strings to None
    if contact_name is not None and isinstance(contact_name, str) and not contact_name.strip():
        contact_name = None
    
    # --- Core Logic ---
    # Use messages service to show recipient not found (this is a UI operation)
    result = messages.show_message_recipient_not_found_or_specified(
        contact_name=contact_name
    )
    
    return result
