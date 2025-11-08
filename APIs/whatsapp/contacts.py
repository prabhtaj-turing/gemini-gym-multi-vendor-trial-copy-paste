from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict, List, Optional
from pydantic import ValidationError as PydanticValidationError
from .SimulationEngine import utils
from .SimulationEngine.models import GetContactChatsArgs, ContactChatsResponse, WhatsappContact, SearchContactsArguments, FunctionName
from .SimulationEngine import custom_errors
from .SimulationEngine.utils import get_last_message_preview_for_contact_chats

@tool_spec(
    spec={
        'name': 'get_contact_chats',
        'description': """ Get all WhatsApp chats involving the contact.
        
        This function retrieves all WhatsApp chats that involve the contact specified by their JID.
        The number of chats returned can be controlled using `limit`, and `page` allows for
        fetching subsequent sets of chats. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'jid': {
                    'type': 'string',
                    'description': "The contact's JID to search for."
                },
                'limit': {
                    'type': 'integer',
                    'description': 'Maximum number of chats to return. Defaults to 20.'
                },
                'page': {
                    'type': 'integer',
                    'description': 'Page number for pagination. Defaults to 0.'
                }
            },
            'required': [
                'jid'
            ]
        }
    }
)
def get_contact_chats(jid: str, limit: int = 20, page: int = 0) -> Dict[str, Any]:
    """Get all WhatsApp chats involving the contact.

    This function retrieves all WhatsApp chats that involve the contact specified by their JID.
    The number of chats returned can be controlled using `limit`, and `page` allows for
    fetching subsequent sets of chats.

    Args:
        jid (str): The contact's JID to search for.
        limit (int): Maximum number of chats to return. Defaults to 20.
        page (int): Page number for pagination. Defaults to 0.

    Returns:
        Dict[str, Any]: A dictionary containing a list of chats involving the specified contact and pagination details. This dictionary includes the following keys:
            chats (List[Dict[str, Any]]): A list of chat objects. Each chat object contains the following fields:
                chat_jid (str): The JID (Jabber ID) of the chat.
                name (Optional[str]): The name of the chat (e.g., contact name or group subject).
                is_group (bool): True if the chat is a group chat where the contact is a participant, False otherwise.
                last_active_timestamp (Optional[str]): ISO-8601 formatted timestamp of the last activity in the chat.
                unread_count (Optional[int]): Number of unread messages in the chat for the current user.
                last_message_preview (Optional[Dict[str, Any]]): A brief preview of the last message in the chat. The specific structure of this object is detailed in the `list_chats` method response or relevant message object documentation.
            total_chats (int): The total number of chats found involving the contact, across all pages.
            page (int): The current page number (0-indexed) of the returned list of chats.
            limit (int): The maximum number of chats returned per page.

    Raises:
        ContactNotFoundError: If no contact is found with the given `jid`.
        InvalidJIDError: If the provided `jid` is not a valid JID format.
        InvalidParameterError: If input arguments fail validation.
        PaginationError: If the requested page number is out of the valid range (e.g., negative or beyond the total number of pages).
    """
    try:
        validated_args = GetContactChatsArgs(jid=jid, limit=limit, page=page)
    except PydanticValidationError as e:
        # (Error handling logic remains the same as in the original function)
        err = e.errors()[0]
        field_name = err["loc"][0]
        if field_name == "jid":
            raise custom_errors.InvalidJIDError()
        if field_name in ("limit", "page"):
            raise custom_errors.InvalidParameterError(err["msg"])
        raise custom_errors.InvalidParameterError(f"Input validation failed: {e.errors()}")

    target_jid = validated_args.jid
    page_limit = validated_args.limit
    page_number = validated_args.page

    # This utility function now works with the new DB structure
    contact_data = utils.get_contact_data(target_jid)
    if contact_data is None:
        raise custom_errors.ContactNotFoundError()

    all_db_chats = utils.list_all_chats_data()
    contact_related_chats_info = []

    for chat_data in all_db_chats:
        if not isinstance(chat_data, dict):
            continue
        
        is_relevant_chat = False
        chat_is_group = chat_data.get("is_group", False)

        if chat_is_group:
            group_metadata = chat_data.get("group_metadata")
            if isinstance(group_metadata, dict):
                participants = group_metadata.get("participants", [])
                if any(p.get("jid") == target_jid for p in participants if isinstance(p, dict)):
                    is_relevant_chat = True
        else:
            if chat_data.get("chat_jid") == target_jid:
                is_relevant_chat = True
        
        if is_relevant_chat:
            last_msg_preview = get_last_message_preview_for_contact_chats(chat_data)
            
            chat_info_entry = {
                "chat_jid": chat_data.get("chat_jid"),
                "name": chat_data.get("name"),
                "is_group": chat_is_group,
                "last_active_timestamp": chat_data.get("last_active_timestamp"),
                "unread_count": chat_data.get("unread_count", 0),
                "last_message_preview": last_msg_preview,
            }
            contact_related_chats_info.append(chat_info_entry)

    contact_related_chats_info.sort(
        key=lambda c: c.get("last_active_timestamp") or "1970-01-01T00:00:00Z",
        reverse=True
    )

    total_chats_found = len(contact_related_chats_info)
    start_index = page_number * page_limit
    
    if start_index >= total_chats_found and total_chats_found > 0:
        raise custom_errors.PaginationError("Requested page is out of range.")
    if total_chats_found == 0 and page_number > 0:
        raise custom_errors.PaginationError("Requested page is out of range as there are no chats.")

    paginated_chats = contact_related_chats_info[start_index : start_index + page_limit]

    # Validate the final response against the Pydantic model
    response_data =ContactChatsResponse(
        chats=paginated_chats,
        total_chats=total_chats_found,
        page=page_number,
        limit=page_limit,
    )
    
    output = response_data.model_dump(mode="json")
    return output

@tool_spec(
    spec={
        'name': 'search_contacts',
        'description': """ Search WhatsApp contacts by name or phone number.
        
        This function searches WhatsApp contacts by name or phone number.
        It uses the provided query term to match against contact names or phone numbers. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Search term to match against contact names or phone numbers.'
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def search_contacts(query: str) -> List[Dict[str, Any]]:
    """Search WhatsApp contacts by name or phone number.

    This function searches WhatsApp contacts by name or phone number.
    It uses the provided query term to match against contact names or phone numbers.

    Args:
        query (str): Search term to match against contact names or phone numbers.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents a contact
        that matches the search query. Each dictionary includes the following keys:
            jid (str): The Jabber ID of the contact (e.g., "1234567890@s.whatsapp.net").
            name_in_address_book (Optional[str]): The name of the contact as saved in the user's address book, if available.
            profile_name (Optional[str]): The contact's WhatsApp profile name.
            phone_number (Optional[str]): The phone number of the contact.
            is_whatsapp_user (bool): True if the phone number is confirmed to be a WhatsApp user.

    Raises:
        InvalidQueryError: If the search query is invalid, too short, poorly formatted, or fails Pydantic validation.
    """
    
    try:
        validated_args = SearchContactsArguments(query=query)
        current_query = validated_args.query
    except PydanticValidationError as e:
        # It's good practice to provide a more specific error message from the validation
        error_details = e.errors()[0].get('msg', 'Invalid input.')
        raise custom_errors.InvalidQueryError(f"Input validation failed: {error_details}")

    try:
        matching_contacts_data = utils.search_contacts_data(current_query)
    except PydanticValidationError as e:
        error_details = e.errors()[0].get('msg', 'Invalid input.')
        raise custom_errors.InvalidQueryError(f"Input validation failed: {error_details}")
    
    # Validate the results against the WhatsappContact model to ensure the output is correct
    output = [WhatsappContact(**data).model_dump() for data in matching_contacts_data]
    return output
