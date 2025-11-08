from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, Dict, Any, List
from .SimulationEngine import custom_errors
from .SimulationEngine.db import DB
import copy

@tool_spec(
    spec={
        'name': 'list_ticket_comments',
        'description': 'List all comments for a ticket.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticket_id': {
                    'type': 'integer',
                    'description': 'The ID of the ticket to list comments for.'
                },
                'include': {
                    'type': 'string',
                    'description': """ Accepts "users". Use this parameter to list email CCs by side-loading users.
                    Note: If the comment source is email, a deleted user will be represented as the CCd email address.
                    If the comment source is anything else, a deleted user will be represented as the user name.
                    Example: ?include=users. Its in the documentation but not implemented. """
                },
                'include_inline_images': {
                    'type': 'boolean',
                    'description': 'Default is false. When true, inline images are also listed as attachments in the response.'
                }
            },
            'required': [
                'ticket_id'
            ]
        }
    }
)
def list_ticket_comments(
        ticket_id: int,
        include: Optional[str] = None,
        include_inline_images: bool = False,
        ) -> Dict[str, List[Dict[str, Any]]]:
    """
    List all comments for a ticket.

    Args:
        ticket_id(int): The ID of the ticket to list comments for.
        include(Optional[str]): Accepts "users". Use this parameter to list email CCs by side-loading users.
                                Note: If the comment source is email, a deleted user will be represented as the CCd email address.
                                If the comment source is anything else, a deleted user will be represented as the user name.
                                Example: ?include=users. Its in the documentation but not implemented.
        include_inline_images(bool): Default is false. When true, inline images are also listed as attachments in the response.

    Returns:
        Dict[str, List[Dict[str, Any]]]: It returns the comments for the ticket.
            - comments(List[Dict[str, Any]]): A list of comments for the ticket. Each comment is a dictionary with the following keys:
                - id(int): The ID of the comment.
                - ticket_id(int): The ID of the ticket.
                - author_id(int): The ID of the user who created the comment.
                - body(str): The body of the comment.
                - public(bool): Whether the comment is public.
                - type(str): The type of the comment.
                - audit_id(int): The ID of the audit.
                - attachments(List[Dict[str, Any]]): The IDs of the attachments. Each attachment is a dictionary with the following keys:
                    - id(int): The ID of the attachment.
                    - file_name(str): The name of the attachment.
                    - content_url(str): The URL of the attachment.
                    - content_type(str): The MIME type of the attachment.
                    - size(int): The size of the attachment in bytes.
                    - thumbnail(List[Dict[str, Any]]): The thumbnail of the attachment.
                - created_at(str): The date and time the comment was created.
                - updated_at(str): The date and time the comment was updated.
                - metadata(Dict[str, Any]): The metadata of the comment.
                    - system(Dict[str, Any]): The system metadata of the comment.
                        - client(str): The Browser used to create the comment.
                        - ip_address(str): The IP address from which the comment was created.
                        - location(str): The location from which the comment was created.
                        - latitude(float): The latitude of the location from which the comment was created.
                        - longitude(float): The longitude of the location from which the comment was created.
                - via(Dict[str, Any]): The via metadata of the comment.
                    - channel(str): The channel through which the comment was created.
                    - source(Dict[str, Any]): The source metadata of the comment.
                        - from(Dict[str, Any]): The from metadata of the comment.
                        - rel(str): The relationship between the comment and the user who created the comment.
                        - to(Dict[str, Any]): The to metadata of the comment.
                            
    Raises:
        TicketNotFoundError: If the ticket is not found.
        TypeError: If the input parameters are not of the correct type.
    """
    if not isinstance(ticket_id, int):
        raise TypeError("ticket_id must be an integer")

    if include and not isinstance(include, str):
        raise TypeError("include must be a string")

    if not isinstance(include_inline_images, bool):
        raise TypeError("include_inline_images must be a boolean")

    if str(ticket_id) not in DB.get("tickets", {}).keys():
        raise custom_errors.TicketNotFoundError(f"Ticket with ID {ticket_id} not found")

    ticket_comments = []
    all_comments = DB.get("comments", {})

    for comment in all_comments.values():
        deep_copy_comment = comment.copy()
        if deep_copy_comment["ticket_id"] == ticket_id:
            if not include_inline_images and "attachments" in deep_copy_comment:
                deep_copy_comment.pop("attachments")
            else:
                attachments = []
                for attachment in deep_copy_comment["attachments"]:
                    attachment = DB.get("attachments", {}).get(str(attachment), {})
                    attachments.append(attachment)
                deep_copy_comment["attachments"] = attachments

            ticket_comments.append(deep_copy_comment)

    return {
        "comments": ticket_comments
    }