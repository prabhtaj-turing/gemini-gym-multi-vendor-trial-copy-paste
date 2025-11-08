from typing import Any, Dict, List

from .SimulationEngine import custom_errors
from .SimulationEngine.db import DB
from common_utils.tool_spec_decorator import tool_spec

@tool_spec(
    spec={
        'name': 'list_audits_for_ticket',
        'description': 'List all audits for a given ticket.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticket_id': {
                    'type': 'integer', 
                    'description': 'The ID of the ticket to list audits for.'
                    }
            },
            'required': [
                'ticket_id'
                ]
        }
    }
)
def list_audits_for_ticket(ticket_id: int) -> Dict[str, Any]:
    """
    List all audits for a given ticket.

    Args:
        ticket_id (int): The ID of the ticket to list audits for.

    Returns:
        Dict[str, Any]: Audit Ticket response.
            - audits (List[Dict[str, Any]]): A list of audits for the given ticket with the following fields:
                - id (int): The ID of the audit.
                - ticket_id (int): The ID of the ticket.
                - author_id (int): The ID of the user who created the audit.
                - created_at (str): The date and time the audit was created.
                - metadata (Dict[str, Any]): Metadata associated with the audit.
                    system (Optional[Dict[str, Any]]): System-related metadata
                        providing context of the change, may include:
                        applied_macro_ids (Optional[List[int]]): List of macro IDs
                            that were applied during ticket creation (derived from
                            macro_id and macro_ids input parameters).
                    custom (Optional[Dict[str, Any]]): Custom metadata.
                - events (List[Dict[str, Any]]): A list of events that occurred in
                    this audit. Each event object describes a change and contains:
                    - id (int): Unique ID for the event.
                    - type (str): Type of event (e.g., 'Create', 'Change', 'Comment').
                    - author_id (int): The ID of the user who performed the action.
                    - field_name (Optional[str]): The name of the field that was
                        changed (for 'Change' events).
                    - value (Any): The new value of the field or the content of the
                        comment.
                    - previous_value (Any): The previous value of the field (for
                        'Change' events).
                    - body (Optional[str]): For comment events, the text of the comment.
                    - public (Optional[bool]): For comment events, whether the comment
                        is public.
                    - html_body (Optional[str]): For comment events, the HTML body of 
                        the comment if provided.
                    - metadata (Optional[Dict[str, Any]]): For comment events, additional
                        metadata such as:
                        - uploads (Optional[List[str]]): The list of attachment tokens
                            if uploads were provided.
                    via (Dict[str, Any]): Information about how the change was made.
                        channel (str): The channel through which the audit event
                            occurred.
                        source (Dict[str, Any]): Source details, structure depends
                            on the channel (e.g., 'from', 'to', 'rel').
    Raises:
        TicketNotFoundError: If the ticket is not found.
        TypeError: If the ticket_id is not an integer.
    """
    if not isinstance(ticket_id, int):
        raise TypeError("ticket_id must be an integer")

    if str(ticket_id) not in DB.get("tickets", {}).keys():
        raise custom_errors.TicketNotFoundError(f"Ticket with ID {ticket_id} not found")

    audits = []
    # Find all audits for the given ticket_id in DB['ticket_audits']
    for audit in DB.get("ticket_audits", {}).values():
        if audit.get("ticket_id") == ticket_id:
            audits.append(audit)

    return {
        "audits": audits
    }

@tool_spec(
    spec={
        'name': 'show_audit',
        'description': 'Show an audit by its ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'ticket_audit_id': {
                    'type': 'integer', 
                    'description': 'The ID of the ticket audit.'
                    },
                'audit_id': {
                    'type': 'integer', 
                    'description': 'The ID of the audit to show.'
                    }
            },
            'required': [
                'ticket_audit_id',
                'audit_id'
            ]
        }
    }
)
def show_audit(ticket_audit_id: int, audit_id: int) -> Dict[str, Any]:
    """
    Show an audit by its ID.

    Args:
        ticket_audit_id (int): The ID of the ticket audit.
        audit_id (int): The ID of the audit to show.

    Returns:
        Dict[str, Any]: Audit Ticket response. 
        - audit (Dict[str, Any]): The audit with the following fields:  
            - id (int): The ID of the audit.
            - ticket_id (int): The ID of the ticket.
            - author_id (int): The ID of the user who created the audit.
            - created_at (str): The date and time the audit was created.
            - metadata (Dict[str, Any]): Metadata associated with the audit.
                system (Optional[Dict[str, Any]]): System-related metadata
                    providing context of the change, may include:
                    applied_macro_ids (Optional[List[int]]): List of macro IDs
                        that were applied during ticket creation (derived from
                        macro_id and macro_ids input parameters).
                    custom (Optional[Dict[str, Any]]): Custom metadata.
            - events (List[Dict[str, Any]]): A list of events that occurred in this audit.
                - id (int): Unique ID for the event.
                - type (str): Type of event (e.g., 'Create', 'Change', 'Comment').
                - author_id (int): The ID of the user who performed the action.
                - field_name (Optional[str]): The name of the field that was
                    changed (for 'Change' events).
                - value (Any): The new value of the field or the content of the
                    comment.
                - previous_value (Any): The previous value of the field (for
                    'Change' events).
                - body (Optional[str]): For comment events, the text of the comment.
                - public (Optional[bool]): For comment events, whether the comment
                    is public.
                - html_body (Optional[str]): For comment events, the HTML body of 
                    the comment if provided.
                - metadata (Optional[Dict[str, Any]]): For comment events, additional
                    metadata such as:
                    - uploads (Optional[List[str]]): The list of attachment tokens
                        if uploads were provided.
                - via (Dict[str, Any]): Information about how the change was made.
                    channel (str): The channel through which the audit event
                        occurred.
                    source (Dict[str, Any]): Source details, structure depends
                        on the channel (e.g., 'from', 'to', 'rel').
    Raises:
        TicketNotFoundError: If the ticket is not found.
        TypeError: If the ticket_id is not an integer.
    """
    if not isinstance(ticket_audit_id, int):
        raise TypeError("ticket_audit_id must be an integer")

    if not isinstance(audit_id, int):
        raise TypeError("audit_id must be an integer")

    if str(ticket_audit_id) not in DB.get("ticket_audits", {}).keys():
        raise custom_errors.TicketNotFoundError(f"Ticket with ID {ticket_audit_id} not found")
    
    if str(audit_id) not in DB.get("ticket_audits", {}).keys():
        raise custom_errors.TicketAuditNotFoundError(f"Ticket Audit with ID {audit_id} not found")


    audit = DB.get("ticket_audits", {}).get(str(audit_id))

    return {
        "audit": audit
    }