"""
Notifications Service Implementation

This module provides the core functionality for managing Android notifications,
including retrieval, filtering, and reply capabilities.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional, List, Union
from .SimulationEngine import utils
from .SimulationEngine.custom_errors import ValidationError
from .SimulationEngine.db import DB

@tool_spec(
    spec={
        'name': 'get_notifications',
        'description': 'Get Android notifications with optional filtering.',
        'parameters': {
            'type': 'object',
            'properties': {
                'sender_name': {
                    'type': 'string',
                    'description': """ Filter notifications by sender/group name. 
                    Must be a non-empty string with maximum length of 256 characters if provided. """
                },
                'app_name': {
                    'type': 'string',
                    'description': """ Filter notifications by application name.
                    Must be a non-empty string with maximum length of 256 characters if provided. """
                },
                'unread': {
                    'type': 'boolean',
                    'description': """ If True (default), fetches only unread notifications and marks them as read.
                    If False, fetches only read notifications without changing their read status. """
                }
            },
            'required': []
        }
    }
)
def get_notifications(
    sender_name: Optional[str] = None,
    app_name: Optional[str] = None,
    unread: bool = True
) -> Dict[str, Union[str, int, bool, List[Dict[str, Union[str, int, List]]], None]]:
    """
    Get Android notifications with optional filtering.
    
    Args:
        sender_name (Optional[str]): Filter notifications by sender/group name. 
            Must be a non-empty string with maximum length of 256 characters if provided.
        app_name (Optional[str]): Filter notifications by application name.
            Must be a non-empty string with maximum length of 256 characters if provided.
        unread (bool): If True (default), fetches only unread notifications and marks them as read.
            If False, fetches only read notifications without changing their read status.
        
    Returns:
        Dict[str, Union[str, int, bool, List[Dict[str, Union[str, int, List]]], None]]: Dictionary containing bundled message notifications with the following structure:
        - action_card_content_passthrough (Optional[str]): Optional string for UI content
        - card_id (Optional[str]): Optional card identifier
        - bundled_message_notifications (List[Dict[str, Union[str, int, List]]]): List of notification bundles, each containing:
            - key (str): Unique identifier for this notification bundle
            - localized_app_name (str): The localized app name
            - app_package_name (str): The app package name
            - sender (Dict[str, str]): The sender of the bundle with keys:
                - type (str): The type of the sender ('user' or 'group')
                - name (str): The name of the sender
            - message_count (int): The number of messages in this bundle
            - message_notifications (List[Dict[str, str]]): All message notifications in this bundle, each containing:
                - sender_name (str): The name of the user who sent the message
                - content (str): The main content of the notification
                - content_type (str): The type of content ('text', 'image', 'audio', or 'video')
                - date (str): Date when the message was sent in format YYYY-MM-DD
                - time_of_day (str): Time when the message was sent in format HH:MM:SS
            - supported_actions (List[str]): The supported actions on this notifications bundle (['reply'])
        - is_permission_denied (bool): Boolean indicating permission status
        - status_code (str): Status code ('OK' or 'PERMISSION_DENIED')
        - skip_reply_disclaimer (Optional[bool]): Optional boolean for UI behavior
        - total_message_count (int): Total count of messages across all bundles
        
    Raises:
        ValidationError: If sender_name or app_name is not a string, is an empty string, 
            or exceeds 256 characters. If unread is not a boolean.
    """
    # Validate input parameters
    if sender_name is not None:
        if not isinstance(sender_name, str):
            raise ValidationError(f"sender_name must be a string, got {type(sender_name).__name__}")
        if sender_name.strip() == "":
            raise ValidationError("sender_name cannot be an empty string")
        if len(sender_name) > 256:
            raise ValidationError("sender_name cannot exceed 256 characters")
    
    if app_name is not None:
        if not isinstance(app_name, str):
            raise ValidationError(f"app_name must be a string, got {type(app_name).__name__}")
        if app_name.strip() == "":
            raise ValidationError("app_name cannot be an empty string")
        if len(app_name) > 256:
            raise ValidationError("app_name cannot exceed 256 characters")
    
    if not isinstance(unread, bool):
        raise ValidationError(f"unread must be a boolean, got {type(unread).__name__}")
    
    # Check permissions first
    if not utils.simulate_permission_check():
        return utils.build_notification_response([], permission_denied=True)
    
    # Get filtered bundles based on criteria
    filtered_bundles = utils.get_filtered_bundles(
        sender_name=sender_name.strip() if sender_name else None,
        app_name=app_name.strip() if app_name else None,
        unread=unread
    )
    
    # Build and return the response
    output = utils.build_notification_response(filtered_bundles)
    return output


@tool_spec(
    spec={
        'name': 'reply_notification',
        'description': 'Reply to a notification with confirmation.',
        'parameters': {
            'type': 'object',
            'properties': {
                'key': {
                    'type': 'string',
                    'description': """ Unique bundle identifier to reply to. Must be a non-empty string
                    with maximum length of 256 characters. """
                },
                'message_body': {
                    'type': 'string',
                    'description': 'The reply message text. Must be a non-empty string.'
                },
                'recipient_name': {
                    'type': 'string',
                    'description': """ Display name of the recipient. Must be a non-empty string
                    with maximum length of 256 characters. """
                },
                'app_name': {
                    'type': 'string',
                    'description': """ Optional application name for the reply.
                    Must be a non-empty string with maximum length of 256 characters if provided. Defaults to None. """
                },
                'app_package_name': {
                    'type': 'string',
                    'description': """ Optional package name. This parameter is not used 
                    in the current implementation but is validated for API compatibility.
                    Must be a non-empty string with maximum length of 256 characters if provided. Defaults to None. """
                }
            },
            'required': [
                'key',
                'message_body',
                'recipient_name'
            ]
        }
    }
)
def reply_notification(
    key: str,
    message_body: str,
    recipient_name: str,
    app_name: Optional[str] = None,
    app_package_name: Optional[str] = None
) -> Dict[str, Union[str, int, None]]:
    """
    Reply to a notification with confirmation.
    
    Args:
        key (str): Unique bundle identifier to reply to. Must be a non-empty string
            with maximum length of 256 characters.
        message_body (str): The reply message text. Must be a non-empty string.
        recipient_name (str): Display name of the recipient. Must be a non-empty string
            with maximum length of 256 characters.
        app_name (Optional[str]): Optional application name for the reply.
            Must be a non-empty string with maximum length of 256 characters if provided. Defaults to None.
        app_package_name (Optional[str]): Optional package name. This parameter is not used 
            in the current implementation but is validated for API compatibility.
            Must be a non-empty string with maximum length of 256 characters if provided. Defaults to None.
        
    Returns:
        Dict[str, Union[str, int, None]]: Dictionary containing reply confirmation:
        - action_card_content_passthrough (Optional[str]): Optional string for UI content
        - card_id (Optional[str]): Optional card identifier
        - emitted_action_count (int): Number of replies sent (1)
        
    Raises:
        ValidationError: If input parameters don't meet type or length requirements
        ValueError: If any of the following occur:
            - The bundle key does not exist
            - Reply action is not supported for the bundle
            - Sender information is missing for the bundle
            - Creating the reply action fails
    """
    # Validate required parameters
    if not isinstance(key, str):
        raise ValidationError(f"key must be a string, got {type(key).__name__}")
    if not key.strip():
        raise ValidationError("key cannot be an empty string or whitespace-only")
    if len(key) > 256:
        raise ValidationError("key cannot exceed 256 characters")

    if not isinstance(message_body, str):
        raise ValidationError(f"message_body must be a string, got {type(message_body).__name__}")
    if not message_body.strip():
        raise ValidationError("message_body cannot be an empty string or whitespace-only")

    if not isinstance(recipient_name, str):
        raise ValidationError(f"recipient_name must be a string, got {type(recipient_name).__name__}")
    if not recipient_name.strip():
        raise ValidationError("recipient_name cannot be an empty string or whitespace-only")
    if len(recipient_name) > 256:
        raise ValidationError("recipient_name cannot exceed 256 characters")

    # Validate optional parameters
    if app_name is not None:
        if not isinstance(app_name, str):
            raise ValidationError(f"app_name must be a string, got {type(app_name).__name__}")
        if not app_name.strip():
            raise ValidationError("app_name cannot be an empty string or whitespace-only")
        if len(app_name) > 256:
            raise ValidationError("app_name cannot exceed 256 characters")

    if app_package_name is not None:
        if not isinstance(app_package_name, str):
            raise ValidationError(f"app_package_name must be a string, got {type(app_package_name).__name__}")
        if not app_package_name.strip():
            raise ValidationError("app_package_name cannot be an empty string or whitespace-only")
        if len(app_package_name) > 256:
            raise ValidationError("app_package_name cannot exceed 256 characters")
    
    # Validate bundle exists
    if not utils.validate_bundle_exists(key):
        raise ValueError(f"Notification bundle with key '{key}' not found")
    
    # Check if reply is supported for this bundle
    if not utils.validate_reply_supported(key):
        raise ValueError(f"Reply action is not supported for bundle '{key}'")
    
    # Validate sender exists for the bundle
    sender_info = utils.get_sender_from_bundle(key)
    if not sender_info:
        raise ValueError(f"No sender information found for bundle '{key}'")
    
    # In a real implementation, we might validate the recipient_name matches
    # For simulation, we'll accept any recipient_name provided
    
    # Create the reply action
    try:
        reply_id = utils.create_reply_action(
            bundle_key=key,
            recipient_name=recipient_name,
            message_body=message_body,
            app_name=app_name
        )
    except Exception as e:
        raise ValueError(f"Failed to create reply action: {str(e)}")
    output = utils.build_reply_response(emitted_action_count=1, card_id=reply_id)
    # Return successful reply response
    return output


@tool_spec(
    spec={
        'name': 'reply_notification_message_or_contact_missing',
        'description': """ Handle cases where message body or recipient is missing.
        
        This function is called when a reply attempt is made without
        providing the necessary information (message body or recipient name). """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def reply_notification_message_or_contact_missing() -> Dict[str, Union[str, int, None]]:
    """
    Handle cases where message body or recipient is missing.
    
    This function is called when a reply attempt is made without
    providing the necessary information (message body or recipient name).
    
    Returns:
        Dict[str, Union[str, int, None]]: Dictionary containing a prompt for missing information:
        - action_card_content_passthrough (str): Message asking for missing info
        - card_id (Optional[str]): Optional card identifier (None)
        - emitted_action_count (int): 0 (no reply was sent)
    """
    output = utils.format_missing_info_response()
    return output