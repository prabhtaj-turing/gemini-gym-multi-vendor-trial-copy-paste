from common_utils.tool_spec_decorator import tool_spec
# APIs/hubspot/TransactionalEmails.py
from typing import Dict, Optional, Union, List
import uuid
from hubspot.SimulationEngine.db import DB
import builtins 
from hubspot.SimulationEngine.models import PydanticTransactionalEmailMessage
from common_utils.utils import validate_email_util
from common_utils.custom_errors import InvalidEmailError


@tool_spec(
    spec={
        'name': 'send_transactional_email',
        'description': 'Sends a single transactional email.',
        'parameters': {
            'type': 'object',
            'properties': {
                'message': {
                    'type': 'object',
                    'description': 'An object containing email content and recipient info.',
                    'properties': {
                        'to': {
                            'type': 'string',
                            'description': 'Email address of the recipient.'
                        },
                        'from': {
                            'type': 'string',
                            'description': 'Email address of the sender.'
                        },
                        'subject': {
                            'type': 'string',
                            'description': 'Subject line of the email.'
                        },
                        'htmlBody': {
                            'type': 'string',
                            'description': 'HTML content of the email.'
                        },
                        'cc': {
                            'type': 'array',
                            'description': 'CC recipient email address(es).',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'bcc': {
                            'type': 'array',
                            'description': 'BCC recipient email address(es).',
                            'items': {
                                'type': 'string'
                            }
                        },
                        'replyTo': {
                            'type': 'string',
                            'description': 'Reply-to email address.'
                        }
                    },
                    'required': [
                        'to',
                        'from',
                        'subject',
                        'htmlBody'
                    ]
                },
                'customProperties': {
                    'type': 'object',
                    'description': 'Custom properties for the email. Can include any key-value pairs for email personalization.',
                    'properties': {},
                    'required': []
                }
            },
            'required': [
                'message'
            ]
        }
    }
)
def sendSingleEmail(
    message: Dict[str, Union[str, List[str]]], customProperties: Optional[Dict[str, Union[str, int, bool]]] = None
) -> Dict[str, Union[str, bool]]:
    """Sends a single transactional email.

    Args:
        message (Dict[str, Union[str, List[str]]]): An object containing email content and recipient info.
            - to (str): Email address of the recipient.
            - from (str): Email address of the sender.
            - subject (str): Subject line of the email.
            - htmlBody (str): HTML content of the email.
            - cc (Optional[List[str]]): CC recipient email address(es).
            - bcc (Optional[List[str]]): BCC recipient email address(es).
            - replyTo (Optional[str]): Reply-to email address.
        customProperties (Optional[Dict[str, Union[str, int, bool]]]): Custom properties for the email. Can include any key-value pairs for email personalization. Defaults to None.

    Returns:
        Dict[str, Union[str, bool]]: A dictionary containing:
            - success (bool): Whether the email was sent successfully.
            - message (str): A description of the operation result.
            - email_id (str): A unique identifier for the sent email (only on success).

    Raises:
        TypeError: If message is not a dictionary.
        ValueError: if the input paramteres does not match the expected schema.
    """
    if not isinstance(message, dict):
        raise TypeError(f"message must be a dictionary, but got {builtins.type(message).__name__}.")
    
    if 'from' in message:
        message['from_'] = message['from']
        del message['from'] # Remove the 'from' key to avoid validation error
    
    try:
        validated_message = PydanticTransactionalEmailMessage(**message)
    except Exception as e:
        for error in e.errors():
            loc = error['loc']
            field_name = loc[0]
            if field_name == 'from_':
                field_name = 'from'
            raise ValueError(f"Invalid message property: {field_name}")

    if 'from_' in message:
        message['from'] = message['from_']
        del message['from_'] # Remove the 'from_' key to avoid validation error

    validate_email_util(message["to"], "to")
    validate_email_util(message["from"], "from")
    if "cc" in message:
        for email in message["cc"]:
            validate_email_util(email, "cc")
    if "bcc" in message:
        for email in message["bcc"]:
            validate_email_util(email, "bcc")
    if "replyTo" in message:
        validate_email_util(message["replyTo"], "replyTo")
    email_id = str(uuid.uuid4())

    # Simulate sending the email (store in DB)
    if "transactional_emails" not in DB:
        DB["transactional_emails"] = {}

    if email_id not in DB["transactional_emails"]:
        DB["transactional_emails"][email_id] = []

    DB["transactional_emails"][email_id].append(
        {
            "message": message,
            "customProperties": customProperties,
            "status": "sent",
            "email_id": email_id,
        }
    )

    return {
        "success": True,
        "message": f"Transactional email sent successfully.",
        "email_id": email_id,
    }
