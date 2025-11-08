from typing import Any, Dict, List, Optional
from datetime import datetime
from dateutil import parser as dateutil_parser
from .db import DB
from .models import APIName, Action
from .phone_utils import normalize_phone_number
import re
import copy

VALID_STATUSES = {"sent", "failed", "pending"}

def _ensure_recipient_exists(resource_name: str) -> None:
    """Ensures that a recipient exists in the database by their resource name.
    
    Args:
        resource_name (str): The resource name to check (e.g., 'people/c1a2b3c4...').
        
    Raises:
        ValueError: If the recipient does not exist in the database.
    """
    if resource_name not in DB["recipients"]:
        raise ValueError(f"Recipient with resource name '{resource_name}' does not exist.")


def _next_counter(counter_name: str) -> int:
    """Get the next counter value and increment it.
    
    Args:
        counter_name (str): The name of the counter to increment.
        
    Returns:
        int: The next counter value.

    Raises:
        TypeError: If `counter_name` is not a string.
        ValueError: If `counter_name` is an empty string.
    """
    # Validate counter name
    if not isinstance(counter_name, str):
        raise TypeError("counter_name must be a string.")
    if not counter_name:
        raise ValueError("counter_name cannot be empty.")

    current_val = DB["counters"].get(counter_name, 0)
    new_val = current_val + 1
    DB["counters"][counter_name] = new_val
    return new_val


def _validate_phone_number(phone_number: str) -> bool:
    """Strict E.164 validation for phone numbers.
    
    Args:
        phone_number (str): The phone number to validate.
        
    Returns:
        bool: True if valid strict E.164 format, False otherwise.
    """
    if not isinstance(phone_number, str):
        return False
    phone_number = phone_number.strip()
    if not phone_number:
        return False
    
    return normalize_phone_number(phone_number) is not None


def _get_recipient_by_phone(phone_number: str) -> Optional[dict]:
    """Find a recipient's phone-specific data object by phone number.
    
    Args:
        phone_number (str): The phone number to search for.
        
    Returns:
        Optional[dict]: The recipient's 'phone' data if found, None otherwise.
    """
    for contact_data in DB["recipients"].values():
        for number_info in contact_data.get("phoneNumbers", []):
            if number_info.get("value") == phone_number:
                # Return the nested 'phone' object which matches the Recipient model
                return contact_data.get("phone")
    return None


def _add_message_to_history(message_data: dict) -> None:
    """Add a message to the message history.
    
    Args:
        message_data (dict): The message data to add to history.
    """
    DB["message_history"].append(message_data)


def _list_messages(
    recipient_id: Optional[str] = None,
    recipient_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Lists messages from the database with optional filters.

    Args:
        recipient_id (Optional[str]): Filter messages by the recipient's contact ID.
        recipient_name (Optional[str]): Filter messages by the recipient's name (case-insensitive).
        start_date (Optional[str]): Filter messages sent on or after this date (ISO 8601 format).
        end_date (Optional[str]): Filter messages sent on or before this date (ISO 8601 format).
        status (Optional[str]): Filter messages by status (e.g., "sent", "failed").

    Returns:
        List[Dict[str, Any]]: A list of message objects matching the criteria. Each dict contains:
            - id (str): The unique message ID.
            - recipient (Dict): Information about the recipient.
                - contact_id (str): The contact's unique ID.
                - contact_name (str): The contact's name.
            - timestamp (str): The message timestamp in ISO 8601 format.
            - status (str): The message status (e.g., "sent").
        
    Raises:
        TypeError: If `recipient_id`, `recipient_name`, `start_date`, `end_date`, or `status`
                   are provided but are not strings.
        ValueError: If `start_date` or `end_date` are provided with an invalid ISO 8601 format.
    """
    # --- Input Validation ---
    if recipient_id is not None and not isinstance(recipient_id, str):
        raise TypeError("recipient_id must be a string.")
    if recipient_name is not None and not isinstance(recipient_name, str):
        raise TypeError("recipient_name must be a string.")
    if start_date is not None and not isinstance(start_date, str):
        raise TypeError("start_date must be a string.")
    if end_date is not None and not isinstance(end_date, str):
        raise TypeError("end_date must be a string.")
    if status is not None and not isinstance(status, str):
        raise TypeError("status must be a string.")

    if status and status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Must be one of {sorted(list(VALID_STATUSES))}.")

    if recipient_id and recipient_id not in DB.get("recipients", {}):
        raise ValueError(f"Recipient with id '{recipient_id}' not found.")

    all_recipients = DB.get("recipients", {}).values()

    # Build a list of known recipient names from the recipients DB
    searchable_names: List[str] = []
    if recipient_name:
        for recipient_record in all_recipients:
            if not isinstance(recipient_record, dict):
                continue
            # Top-level contact_name
            top_level_name = recipient_record.get("contact_name")
            if isinstance(top_level_name, str):
                searchable_names.append(top_level_name)
            # Nested phone.contact_name (Contacts-linked shape)
            phone_obj = recipient_record.get("phone")
            if isinstance(phone_obj, dict):
                phone_name = phone_obj.get("contact_name")
                if isinstance(phone_name, str):
                    searchable_names.append(phone_name)
            # Derive from names[0].givenName/familyName or displayName if present
            names_list = recipient_record.get("names")
            if isinstance(names_list, list) and names_list:
                primary_name = names_list[0] if isinstance(names_list[0], dict) else None
                if isinstance(primary_name, dict):
                    display_name = primary_name.get("displayName") or ""
                    given = primary_name.get("givenName") or ""
                    family = primary_name.get("familyName") or ""
                    combined = f"{given} {family}".strip()
                    if display_name:
                        searchable_names.append(display_name)   
                    elif combined:
                        searchable_names.append(combined)

        # Raise only if we have any known names and none match
        if searchable_names and not any(
            recipient_name.lower() in name.lower() for name in searchable_names
        ):
            raise ValueError(f"Recipient with name containing '{recipient_name}' not found.")

    messages = list(DB.get("messages", {}).values())
    
    # Also check notifications DB for reply actions
    from notifications.SimulationEngine.db import DB as NOTIFICATIONS_DB
    reply_actions = list(NOTIFICATIONS_DB.get("reply_actions", {}).values())
    
    # Convert reply actions to message format
    for reply in reply_actions:
        # Filter by app_name
        reply_app_name = reply.get("app_name")
        if reply_app_name != "Messages":
            continue
        
        # Ensure timestamp has timezone info for consistent comparison
        timestamp = reply.get("created_at", "")
        if timestamp and not timestamp.endswith("Z") and not timestamp.endswith("+00:00"):
            timestamp = timestamp + "Z"
        
        reply_message = {
            "id": f"reply_{reply.get('id', '')}",
            "recipient": {
                "contact_id": f"contact_{reply.get('id', '')}",
                "contact_name": reply.get("recipient_name", ""),
            },
            "message_body": reply.get("message_body", ""),
            "timestamp": timestamp,
            "status": reply.get("status", "sent")
        }
        messages.append(reply_message)
    
    if recipient_id:
        messages = [m for m in messages if m.get("recipient", {}).get("contact_id") == recipient_id]

    if recipient_name:
        messages = [
            m for m in messages
            if recipient_name.lower() in m.get("recipient", {}).get("contact_name", "").lower()
        ]

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            filtered_messages = []
            for m in messages:
                try:
                    msg_timestamp = datetime.fromisoformat(m["timestamp"].replace("Z", "+00:00"))
                    if msg_timestamp >= start_dt:
                        filtered_messages.append(m)
                except (ValueError, KeyError):
                    # Skip messages with invalid timestamps (like reply actions)
                    continue
            messages = filtered_messages
        except (ValueError, KeyError):
            raise ValueError("Invalid start_date format. Use ISO 8601 format.")

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            filtered_messages = []
            for m in messages:
                try:
                    msg_timestamp = datetime.fromisoformat(m["timestamp"].replace("Z", "+00:00"))
                    if msg_timestamp <= end_dt:
                        filtered_messages.append(m)
                except (ValueError, KeyError):
                    # Skip messages with invalid timestamps (like reply actions)
                    continue
            messages = filtered_messages
        except (ValueError, KeyError):
            raise ValueError("Invalid end_date format. Use ISO 8601 format.")

    if status:
        messages = [m for m in messages if m.get("status") == status]

    return messages


def _delete_message(message_id: str) -> bool:
    """Deletes a message from the database and its history.

    Args:
        message_id (str): The ID of the message to delete.

    Returns:
        bool: True if the message was successfully deleted.
        
    Raises:
        TypeError: If `message_id` is not a string.
        ValueError: If `message_id` is an empty string or the message is not found.
    """
    # --- Input Validation ---
    if not isinstance(message_id, str):
        raise TypeError("message_id must be a string.")
    if not message_id:
        raise ValueError("message_id cannot be an empty string.")

    if message_id not in DB.get("messages", {}):
        raise ValueError(f"Message with id '{message_id}' not found.")

    del DB["messages"][message_id]
    
    # Also remove from message history
    DB["message_history"] = [
        item for item in DB.get("message_history", []) if item.get("id") != message_id
    ]
    
    return True 

    return True


def get_contact_data(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Gets a specific contact by phone number or resource name.

    This function searches for a contact in the recipients database by checking:
    1. If the identifier matches a resourceName key (e.g., "people/c1234")
    2. If the identifier matches a phone number in the contact's phoneNumbers list
    3. If the identifier matches any endpoint_value in the nested phone.contact_endpoints array

    Args:
        identifier (str): The phone number (E.164 format) or resource name of the contact.

    Returns:
        Optional[Dict[str, Any]]: A copy of the contact data, or None if not found.
    """
  
    
    recipients_dict = DB.get("recipients", {})
    if not isinstance(recipients_dict, dict):
        return None

    # First, check if a contact exists with this resourceName
    if identifier in recipients_dict:
        contact = recipients_dict.get(identifier)
        if isinstance(contact, dict):
            return copy.deepcopy(contact)

    # Normalize the identifier if it looks like a phone number
    normalized_identifier = normalize_phone_number(identifier)
    
    # If not found by resource name, search by phone number
    for contact_data in recipients_dict.values():
        if isinstance(contact_data, dict):
            # Check phoneNumbers list
            for phone_entry in contact_data.get("phoneNumbers", []):
                if isinstance(phone_entry, dict):
                    phone_value = phone_entry.get("value")
                    if phone_value:
                        # Direct match
                        if phone_value == identifier:
                            return copy.deepcopy(contact_data)
                        # Normalized match
                        if normalized_identifier and normalize_phone_number(phone_value) == normalized_identifier:
                            return copy.deepcopy(contact_data)
            
            # Check nested phone object's contact_endpoints
            phone_info = contact_data.get("phone")
            if isinstance(phone_info, dict):
                contact_endpoints = phone_info.get("contact_endpoints", [])
                for endpoint in contact_endpoints:
                    if isinstance(endpoint, dict):
                        endpoint_value = endpoint.get("endpoint_value")
                        if endpoint_value:
                            # Direct match
                            if endpoint_value == identifier:
                                return copy.deepcopy(contact_data)
                            # Normalized match
                            if normalized_identifier and normalize_phone_number(endpoint_value) == normalized_identifier:
                                return copy.deepcopy(contact_data)

    return None


def search_contacts_data(query: str) -> List[Dict[str, Any]]:
    """
    Searches for contacts by name or phone number.

    This function searches the recipients database for contacts matching the query.
    It searches through contact names (from various fields) and phone numbers.

    Args:
        query (str): The search term (name or phone number).

    Returns:
        List[Dict[str, Any]]: A list of matching contact data dictionaries.
            Each dictionary contains the phone-specific contact information.
    """
    
    if not query or not isinstance(query, str):
        return []

    q_lower = query.lower()
    q_digits = re.sub(r"\D", "", query)

    results = []
    recipients_dict = DB.get("recipients", {})
    if not isinstance(recipients_dict, dict):
        return []

    for resource_name, contact in recipients_dict.items():
        if not isinstance(contact, dict):
            continue

        # Get the nested phone object
        phone_data = contact.get("phone", {})
        
        # Skip if no phone data
        if not phone_data or not isinstance(phone_data, dict):
            continue

        # 1) Match by name from the phone object
        contact_name = phone_data.get("contact_name", "")
        name_match = q_lower in contact_name.lower() if contact_name else False

        # 2) Also check names list from the main contact object
        if not name_match:
            names_list = contact.get("names", [])
            for name_obj in names_list:
                if isinstance(name_obj, dict):
                    given_name = name_obj.get("givenName", "")
                    family_name = name_obj.get("familyName", "")
                    display_name = name_obj.get("displayName", "")
                    
                    if (q_lower in given_name.lower() or 
                        q_lower in family_name.lower() or
                        q_lower in display_name.lower()):
                        name_match = True
                        break

        # 3) Match by phone number if query contains digits
        phone_match = False
        if q_digits:
            # Check phoneNumbers list
            for phone_obj in contact.get("phoneNumbers", []):
                if isinstance(phone_obj, dict):
                    phone_value = phone_obj.get("value", "")
                    phone_digits = re.sub(r"\D", "", phone_value)
                    if q_digits in phone_digits:
                        phone_match = True
                        break
            
            # Also check nested phone.contact_endpoints
            if not phone_match:
                contact_endpoints = phone_data.get("contact_endpoints", [])
                for endpoint in contact_endpoints:
                    if isinstance(endpoint, dict):
                        endpoint_value = endpoint.get("endpoint_value", "")
                        if endpoint_value:
                            phone_digits = re.sub(r"\D", "", endpoint_value)
                            if q_digits in phone_digits:
                                phone_match = True
                                break

        # If matched, add the phone data to results
        if name_match or phone_match:
            results.append(copy.deepcopy(phone_data))

    return results 



 