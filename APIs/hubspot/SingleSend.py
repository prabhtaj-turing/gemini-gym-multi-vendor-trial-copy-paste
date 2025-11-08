# APIs/hubspot/SingleSend.py
from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Union, Optional, List
import uuid
from hubspot.SimulationEngine.db import DB
from hubspot.SimulationEngine.models import SendSingleEmailRequest
from hubspot.SimulationEngine.custom_errors import TemplateNotFoundError, TemplateNotValidError

@tool_spec(
    spec={
        'name': 'send_single_email_with_template',
        'description': 'Sends a single transactional email based on a pre-existing email template.',
        'parameters': {
            'type': 'object',
            'properties': {
                'template_id': {
                    'type': 'string',
                    'description': 'The ID of the pre-existing transactional email template to send.'
                },
                'message': {
                    'type': 'object',
                    'description': 'An object containing email content and recipient info.',
                    'properties': {
                        'to': {
                            'type': 'array',
                            'description': 'Required. List of recipient objects.',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'email': {
                                        'type': 'string',
                                        'description': 'Required. Email address of the recipient.'
                                    },
                                    'name': {
                                        'type': 'string',
                                        'description': 'Name of the recipient.'
                                    }
                                },
                                'required': [
                                    'email'
                                ]
                            }
                        },
                        'cc': {
                            'type': 'array',
                            'description': 'List of CC recipient objects.',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'email': {
                                        'type': 'string',
                                        'description': 'Required. Email address of the CC recipient.'
                                    },
                                    'name': {
                                        'type': 'string',
                                        'description': 'Name of the CC recipient.'
                                    }
                                },
                                'required': [
                                    'email'
                                ]
                            }
                        },
                        'bcc': {
                            'type': 'array',
                            'description': 'List of BCC recipient objects.',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'email': {
                                        'type': 'string',
                                        'description': 'Required. Email address of the BCC recipient.'
                                    },
                                    'name': {
                                        'type': 'string',
                                        'description': 'Name of the BCC recipient.'
                                    }
                                },
                                'required': [
                                    'email'
                                ]
                            }
                        },
                        'from': {
                            'type': 'object',
                            'description': 'Sender information.',
                            'properties': {
                                'email': {
                                    'type': 'string',
                                    'description': 'Required. Email address of the sender.'
                                },
                                'name': {
                                    'type': 'string',
                                    'description': 'Name of the sender.'
                                }
                            },
                            'required': [
                                'email'
                            ]
                        },
                        'replyTo': {
                            'type': 'array',
                            'description': 'List of reply-to addresses.',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'email': {
                                        'type': 'string',
                                        'description': 'Required. Reply-to email address.'
                                    },
                                    'name': {
                                        'type': 'string',
                                        'description': 'Reply-to name.'
                                    }
                                },
                                'required': [
                                    'email'
                                ]
                            }
                        }
                    },
                    'required': [
                        'to'
                    ]
                },
                'customProperties': {
                    'type': 'object',
                    'description': """ Custom property values for template personalization.
                    - key : The key of the custom property of string type.
                    - value : The value of the custom property, union of string, integer, boolean. """,
                    'properties': {},
                    'required': []
                },
                'contactProperties': {
                    'type': 'object',
                    'description': """ Contact property values.
                    - key : The key of the contact property of string type.
                    - value : The value of the contact property, union of string, integer, boolean. """,
                    'properties': {},
                    'required': []
                }
            },
            'required': [
                'template_id',
                'message'
            ]
        }
    }
)
def sendSingleEmail(
    template_id: str,
    message: Dict[str, Union[List[Dict[str, str]], Dict[str, str]]],
    customProperties: Optional[Dict[str, Union[str, int, bool]]] = None,
    contactProperties: Optional[Dict[str, Union[str, int, bool]]] = None,
) -> Dict[str, Union[str, Dict[str, Union[str, str]]]]:
    """
    Sends a single transactional email based on a pre-existing email template.

    Args:
        template_id (str): The ID of the pre-existing transactional email template to send.
        message (Dict[str, Union[List[Dict[str, str]], Dict[str, str]]]): An object containing email content and recipient info.
            - to (List[Dict[str, str]]): Required. List of recipient objects.
                - email (str): Required. Email address of the recipient.
                - name (Optional[str]): Name of the recipient.
            - cc (Optional[List[Dict[str, str]]]): List of CC recipient objects.
                - email (str): Required. Email address of the CC recipient.
                - name (Optional[str]): Name of the CC recipient.
            - bcc (Optional[List[Dict[str, str]]]): List of BCC recipient objects.
                - email (str): Required. Email address of the BCC recipient.
                - name (Optional[str]): Name of the BCC recipient.
            - from (Optional[Dict[str, str]]): Sender information.
                - email (str): Required. Email address of the sender.
                - name (Optional[str]): Name of the sender.
            - replyTo (Optional[List[Dict[str, str]]]): List of reply-to addresses.
                - email (str): Required. Reply-to email address.
                - name (Optional[str]): Reply-to name.
        customProperties (Optional[Dict[str, Union[str, int, bool]]]): Custom property values for template personalization.
            - key : The key of the custom property of string type.
            - value : The value of the custom property, union of string, integer, boolean.
            Defaults to None.
        contactProperties (Optional[Dict[str, Union[str, int, bool]]]): Contact property values.
            - key : The key of the contact property of string type.
            - value : The value of the contact property, union of string, integer, boolean.
            Defaults to None.

    Returns:
        Dict[str, Union[str, Dict[str, Union[str, str]]]]: A dictionary representing the API response with the following structure:
            - status (str): Status of the operation ('success' or 'error').
            - message (str): Description of the operation result.
            - template_id (str): The ID of the template used (only on success).
            - transactional_email_id (str): Unique ID for the sent email (only on success).
            - log (Dict[str, Union[str, Dict[str, Union[str, str]]]]): Log entry containing send details (only on success).
                - template_id (str): The ID of the template used.
                - transactional_email_id (str): Unique ID for the sent email.
                - message (Dict[str, Union[List[Dict[str, str]], Dict[str, str]]]): Original message object.
                    - to (List[Dict[str, str]]): Required. List of recipient objects.
                        - email (str): Required. Email address of the recipient.
                        - name (Optional[str]): Name of the recipient.
                    - cc (Optional[List[Dict[str, str]]]): List of CC recipient objects.
                        - email (str): Required. Email address of the CC recipient.
                        - name (Optional[str]): Name of the CC recipient.
                    - bcc (Optional[List[Dict[str, str]]]): List of BCC recipient objects.
                        - email (str): Required. Email address of the BCC recipient.
                        - name (Optional[str]): Name of the BCC recipient.
                    - from (Optional[Dict[str, str]]): Sender information.
                        - email (str): Required. Email address of the sender.
                        - name (Optional[str]): Name of the sender.
                    - replyTo (Optional[List[Dict[str, str]]]): List of reply-to addresses.
                        - email (str): Required. Reply-to email address.
                        - name (Optional[str]): Reply-to name.
                - properties (Dict[str, Union[str, str]]): Merged properties used.
                    - firstName (str): First name of the contact.
                    - lastName (str): Last name of the contact.
                    - customProperty1 (str): Value of custom property 1.
                    - customProperty2 (str): Value of custom property 2.
                    - ... (additional custom properties)
                - status (str): Status of the send operation.

    Raises:
        ValidationError: If any of the input parameters fail validation (template_id, message structure, properties format).
        TemplateNotFoundError: If template_id is not found or not an email template.
        TemplateNotValidError: If template_id is not found or not an email template.
    """

    # Handle 'from' key conversion for Pydantic validation
    message_copy = message.copy() if message is not None and isinstance(message, dict) else message
    if message_copy and isinstance(message_copy, dict) and 'from' in message_copy:
        message_copy['from_'] = message_copy['from']
        del message_copy['from']
    
    # Validate all parameters using Pydantic model
    request_data = SendSingleEmailRequest(
        template_id=template_id,
        message=message_copy,
        customProperties=customProperties,
        contactProperties=contactProperties
    )


    # Extract validated data from Pydantic model
    template_id = request_data.template_id
    validated_message = request_data.message
    customProperties = request_data.customProperties or {}
    contactProperties = request_data.contactProperties
    
    # Check if the email template exists
    if not DB.get("templates", {}):
        DB["templates"] = {}
    if template_id not in DB["templates"]:
        raise TemplateNotFoundError(f"Email template with ID {template_id} not found.")
    
    if DB["templates"][template_id]["template_type"] != 2:
        raise TemplateNotValidError(f"Template with ID {template_id} is not an email template.")
    
    # Convert validated Pydantic models back to dict format for processing
    to = validated_message.to
    cc = validated_message.cc
    bcc = validated_message.bcc
    from_ = validated_message.from_
    replyTo = validated_message.replyTo

    # Iterate through recipients to apply contactProperties
    for recipient in to:
        recipient_email = recipient.email
        contact = DB["contacts"].get(recipient_email, None)
        if contact:
            # Merge contact properties with precedence over custom properties
            customProperties.update(contact)
        if contactProperties:
            customProperties.update(contactProperties)

    # Reconstruct the message for logging
    reconstructed_message = {
        "to": to,
        "cc": cc,
        "bcc": bcc,
        "replyTo": replyTo
    }
    if from_:
        reconstructed_message["from"] = from_
    
    # Simulate sending the email (no actual sending)
    # Use a unique ID for each transactional email
    transactional_email_id = str(uuid.uuid4())
    log_entry = {
        "template_id": template_id,
        "transactional_email_id": transactional_email_id,  # Unique ID for the send
        "message": reconstructed_message,
        "properties": customProperties,  # Store merged properties
        "status": "sent",  # Assume successful send for simulation
    }
    DB["transactional_emails"][transactional_email_id] = log_entry  # Store by ID

    return {
        "status": "success",
        "message": f"Email sent successfully using template.",
        "template_id": template_id,
        "transactional_email_id": str(transactional_email_id),  # Return the unique ID
        "log": log_entry,
    }
