"""
Search resource for Slack API simulation.

This module provides functionality for searching messages and files in Slack.
It simulates the search-related endpoints of the Slack API.
"""

import datetime
import re
from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, List
from .SimulationEngine.db import DB
from .SimulationEngine.utils import _matches_filters, _convert_timestamp_to_utc_date, _parse_query
from .SimulationEngine.search_engine import search_engine_manager, service_adapter


def _matches_date_filters(msg: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    """
    Check if a message matches date filters only (no text filtering).
    
    Args:
        msg: The message to check
        filters: The parsed filters containing date information
        
    Returns:
        bool: True if the message matches the date filters
    """
    # Convert timestamp to UTC date
    try:
        msg_date = _convert_timestamp_to_utc_date(msg["ts"])
    except ValueError:
        return False

    if filters["date_after"]:
        # Normalize to YYYY-MM-DD format
        if re.fullmatch(r"\d{4}", filters["date_after"]):
            date_after = datetime.date(int(filters["date_after"]), 1, 1)
        elif re.fullmatch(r"\d{4}-\d{2}", filters["date_after"]):
            year, month = map(int, filters["date_after"].split("-"))
            date_after = datetime.date(year, month, 1)
        else:
            date_after = datetime.datetime.strptime(filters["date_after"], "%Y-%m-%d").date()
        
        if msg_date <= date_after:
            return False
            
    if filters["date_before"]:
        date_before = datetime.datetime.strptime(filters["date_before"], "%Y-%m-%d").date()
        if msg_date >= date_before:
            return False
            
    if filters["date_during"]:
        during_value = filters["date_during"]
        # Year-only filter (e.g., during:2024)
        if re.fullmatch(r"\d{4}", during_value):
            msg_year = msg_date.year
            if msg_year != int(during_value):
                return False

        # Year and Month filter (e.g., during:2024-03)
        elif re.fullmatch(r"\d{4}-\d{2}", during_value):
            year, month = map(int, during_value.split("-"))
            msg_year, msg_month = msg_date.year, msg_date.month
            if msg_year != year or msg_month != month:
                return False

        # Full Date filter (e.g., during:2024-03-23)
        elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", during_value):
            date_during = datetime.datetime.strptime(during_value, "%Y-%m-%d").date()
            if msg_date != date_during:
                return False

    return True


@tool_spec(
    spec={
        'name': 'search_messages',
        'description': """ Searches for messages matching a query.
        
        The query is a space-separated string of terms and filters. Text terms are
        matched against the message's content. By default, all text terms must be
        present in the message (AND logic). """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The search query. The structure is a space-separated string
                    of terms and filters. Supported filters are:
                    - `from:@<username>`: Restricts the search to messages from a specific user (e.g., `from:@alice`).
                    - `in:#<channel_name>`: Restricts the search to a specific channel by name (e.g., `in:#general`).
                    - `has:link`: Narrows search to messages that contain a URL.
                    - `has:reaction`: Narrows search to messages that have a reaction.
                    - `has:star`: Narrows search to messages that have been starred.
                    - `before:YYYY-MM-DD`: Filters for messages sent before a specific date.
                    - `after:YYYY-MM-DD`: Filters for messages sent after a specific date.
                    - `during:YYYY-MM-DD`: Filters for messages on a specific date. Also
                      supports `YYYY` for a year or `YYYY-MM` for a month.
                    - `-<word>`: Excludes messages containing the specified word.
                    - `some*`: Wildcard support for partial word matching.
                    - `OR`: When used between text terms (e.g., "hello OR world"), the
                      logic changes to match messages containing any of the terms. """
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def search_messages(query: str) -> List[Dict[str, Any]]:
    """
    Searches for messages matching a query.

    The query is a space-separated string of terms and filters. Text terms are
    matched against the message's content. By default, all text terms must be
    present in the message (AND logic).

    Args:
        query (str): The search query. The structure is a space-separated string
            of terms and filters. Supported filters are:
            - `from:@<username>`: Restricts the search to messages from a specific user (e.g., `from:@alice`).
            - `in:#<channel_name>`: Restricts the search to a specific channel by name (e.g., `in:#general`).
            - `has:link`: Narrows search to messages that contain a URL.
            - `has:reaction`: Narrows search to messages that have a reaction.
            - `has:star`: Narrows search to messages that have been starred.
            - `before:YYYY-MM-DD`: Filters for messages sent before a specific date.
            - `after:YYYY-MM-DD`: Filters for messages sent after a specific date.
            - `during:YYYY-MM-DD`: Filters for messages on a specific date. Also
              supports `YYYY` for a year or `YYYY-MM` for a month.
            - `-<word>`: Excludes messages containing the specified word.
            - `some*`: Wildcard support for partial word matching.
            - `OR`: When used between text terms (e.g., "hello OR world"), the
              logic changes to match messages containing any of the terms.

    Returns:
        List[Dict[str, Any]]: List of matching messages, where each message contains:
            - ts (str): Message timestamp
            - text (str): Message content
            - user (str): User ID who sent the message
            - channel (str): Channel ID where message was sent
            - reactions (Optional[List[Dict[str, Any]]]): List of reactions if any

    Raises:
        TypeError: If 'query' is not a string.
        ValueError: If query is empty, contains only whitespace, or has invalid date formats.
    """
    # --- Input Validation Start ---
    if not isinstance(query, str):
        raise TypeError(
            f"Argument 'query' must be a string, but got {type(query).__name__}."
        )

    if not query.strip():
        raise ValueError(
            "Argument 'query' must be a non-empty string and cannot contain only whitespace."
        )
    # --- Input Validation End ---

    # Start with all messages from all channels
    messages_list = []
    for channel_id, channel_data in DB.get("channels", {}).items():
        if "messages" in channel_data:
            for msg in channel_data["messages"]:
                # Add channel info to each message
                msg_with_channel = dict(msg)
                msg_with_channel["channel"] = channel_id
                msg_with_channel["channel_name"] = channel_data.get("name", "")
                messages_list.append(msg_with_channel)

    filters = _parse_query(query, target_type="messages", strict=True)

    # Apply filters progressively
    if filters["user"]:
        messages_list = [
            msg for msg in messages_list
            if msg.get("user", "") == filters["user"]
        ]

    if filters["channel"]:
        messages_list = [
            msg for msg in messages_list
            if msg.get("channel_name", "") == filters["channel"]
        ]

    # Handle has: filters with traditional filtering
    if "link" in filters["has"]:
        # Check for URLs in message text using comprehensive regex pattern
        # Matches http://, https://, ftp://, www., and common URL patterns including subdomains
        url_pattern = r'(?:https?://|ftp://|www\.)\S+|(?:^|\s)[\w.-]+\.(?:com|org|net|edu|gov|io|co|info|biz|dev|uk|ca|au|de|fr|jp|cn|in|br|mx|es|it|nl|se|no|fi|dk|be|ch|at|pl|cz|gr|pt|ie|nz|sg|hk|kr|tw|th|my|ph|id|vn|za|ae|sa|eg|ng|ke|tn|ma|dz|ly|sd|gh|ug|zm|zw|bw|mz|ao|cm|ci|sn|ml|bf|ne|td|so|rw|bi|dj|er|et|gm|gn|gw|lr|mr|sl|tg)(?:/\S*)?'
        messages_list = [
            msg for msg in messages_list
            if (msg.get("links") and len(msg.get("links", [])) > 0) or 
               re.search(url_pattern, msg.get("text", ""), re.IGNORECASE)
        ]

    if "reaction" in filters["has"]:
        messages_list = [
            msg for msg in messages_list
            if msg.get("reactions") and len(msg.get("reactions", [])) > 0
        ]

    if "star" in filters["has"]:
        messages_list = [
            msg for msg in messages_list
            if msg.get("is_starred", False) is True
        ]

    # Handle text queries with search engine (always use search engine for text)
    if filters["text"]:
        engine = search_engine_manager.get_engine()

        if filters["boolean"] == "OR":
            # OR logic: find messages matching any text term
            text_matched_ids = set()
            for text_term in filters["text"]:
                search_results = engine.search(text_term, {
                    "resource_type": "message", 
                    "content_type": "text"
                })
                for result in search_results:
                    # The search engine returns the original JSON object directly
                    if result:
                        # Create unique identifier for message
                        msg_id = f"{result.get('ts', '')}_{result.get('channel', '')}"
                        text_matched_ids.add(msg_id)

            # Filter messages list to only include those that matched text search
            messages_list = [
                msg for msg in messages_list
                if f"{msg.get('ts', '')}_{msg.get('channel', '')}" in text_matched_ids
            ]
        else:
            # AND logic: find messages matching all text terms
            for text_term in filters["text"]:
                search_results = engine.search(text_term, {
                    "resource_type": "message", 
                    "content_type": "text"
                })
                matched_ids = set()
                for result in search_results:
                    # The search engine returns the original JSON object directly
                    if result:
                        msg_id = f"{result.get('ts', '')}_{result.get('channel', '')}"
                        matched_ids.add(msg_id)

                # Filter messages list to only include those that matched this term
                messages_list = [
                    msg for msg in messages_list
                    if f"{msg.get('ts', '')}_{msg.get('channel', '')}" in matched_ids
                ]

    # Handle date filters with traditional filtering (only for date logic, not text)
    if filters["date_before"] or filters["date_after"] or filters["date_during"]:
        messages_list = [
            msg for msg in messages_list
            if _matches_date_filters(msg, filters)
        ]

    # Handle exclusions with traditional filtering
    if filters["excluded"]:
        for excluded_word in filters["excluded"]:
            messages_list = [
                msg for msg in messages_list
                if excluded_word.lower() not in msg.get("text", "").lower()
            ]

    # Handle wildcard matching with proper regex pattern matching
    if filters["wildcard"]:
        # Convert wildcard to regex with word boundaries for proper matching
        wildcard_pattern = filters["wildcard"]
        
        if wildcard_pattern.startswith("*") and wildcard_pattern.endswith("*"):
            # Pattern like "*test*" - match anywhere in word
            pattern = wildcard_pattern.replace("*", ".*")
        elif wildcard_pattern.startswith("*"):
            # Pattern like "*test" - match at end of word
            suffix = wildcard_pattern[1:]  # Remove leading *
            pattern = r"\w*" + re.escape(suffix) + r"\b"
        elif wildcard_pattern.endswith("*"):
            # Pattern like "test*" - match at beginning of word
            prefix = wildcard_pattern[:-1]  # Remove trailing *
            pattern = r"\b" + re.escape(prefix) + r"\w*"
        else:
            # Pattern like "te*st" - match in middle of word
            pattern = r"\b" + re.escape(wildcard_pattern).replace(r"\*", r"\w*") + r"\b"
        
        messages_list = [
            msg for msg in messages_list
            if re.search(pattern, msg.get("text", ""), re.IGNORECASE)
        ]

    return messages_list


@tool_spec(
    spec={
        'name': 'search_files',
        'description': """ Searches for files matching a query.
        
        The query is a space-separated string of terms and filters. Text terms are
        matched against the file's name and title. If multiple text terms are
        provided, a match occurs if any term is found (OR logic). """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The search query. Must be a non-empty string. The structure is a space-separated string
                    of terms and filters. Supported filters for files are:
                    - `in:#<channel_name>`: Restricts the search to a specific channel by name (e.g., `in:#general`).
                    - `from:@<username>`: Restricts the search to files uploaded by a specific user (e.g., `from:@alice`).
                    - `type:<file_type>`: Narrows search to a specific file type (e.g., 'pdf', 'docs', 'images').
                    - `filename:<name>`: Search for files containing the specified text in filename or title.
                    - `after:<date>`: Restricts to files uploaded after a specific date (YYYY-MM-DD format).
                    - `before:<date>`: Restricts to files uploaded before a specific date (YYYY-MM-DD format).
                    - `during:<date>`: Restricts to files uploaded during a specific time period.
                      Supports YYYY for year, YYYY-MM for month, or YYYY-MM-DD for specific date.
                    - `has:star`: Narrows search to files that have been starred.
                    - `is:pinned`: Narrows search to files that have been pinned.
                    - `is:saved`: Narrows search to files that have been saved.
                    
                    Note: Exclusion (`-<word>`) and wildcards (`*`) are not applicable to file searches. """
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def search_files(query: str) -> List[Dict[str, Any]]:
    """
    Searches for files matching a query.

    The query is a space-separated string of terms and filters. Text terms are
    matched against the file's name and title. If multiple text terms are
    provided, a match occurs if any term is found (OR logic).

    Args:
        query (str): The search query. Must be a non-empty string. The structure is a space-separated string
            of terms and filters. Supported filters for files are:
            - `in:#<channel_name>`: Restricts the search to a specific channel by name (e.g., `in:#general`).
            - `from:@<username>`: Restricts the search to files uploaded by a specific user (e.g., `from:@alice`).
            - `type:<file_type>`: Narrows search to a specific file type (e.g., 'pdf', 'docs', 'images').
            - `filename:<name>`: Search for files containing the specified text in filename or title.
            - `after:<date>`: Restricts to files uploaded after a specific date (YYYY-MM-DD format).
            - `before:<date>`: Restricts to files uploaded before a specific date (YYYY-MM-DD format).
            - `during:<date>`: Restricts to files uploaded during a specific time period.
              Supports YYYY for year, YYYY-MM for month, or YYYY-MM-DD for specific date.
            - `has:star`: Narrows search to files that have been starred.
            - `is:pinned`: Narrows search to files that have been pinned.
            - `is:saved`: Narrows search to files that have been saved.
            
            Note: Exclusion (`-<word>`) and wildcards (`*`) are not applicable to file searches.

    Returns:
        List[Dict[str, Any]]: List of matching files, where each file contains:
            - id (str): File ID
            - name (str): File name
            - title (str): File title
            - filetype (str): File type
            - channels (List[str]): List of channel IDs where file is shared
            - user (str): User ID who uploaded the file
            - created (str): Unix timestamp when file was created (as string)
            - timestamp (str): Alternative timestamp field
            - mimetype (str): MIME type of the file
            - size (int): File size in bytes
            - url_private (str): Private URL to access the file
            - permalink (str): Public permalink to the file
            - comments (List[Dict]): List of comments on the file
            - is_starred (bool): Whether the file is starred
            - is_pinned (bool): Whether the file is pinned
            - is_saved (bool): Whether the file is saved
            
    Raises:
        TypeError: If query is not a string.
        ValueError: If query is empty, contains only whitespace, or has invalid date formats.
    """
    # --- Input Validation Start ---
    if not isinstance(query, str):
        raise TypeError(
            f"Argument 'query' must be a string, but got {type(query).__name__}."
        )
    
    if not query.strip():
        raise ValueError(
            "Argument 'query' must be a non-empty string and cannot contain only whitespace."
        )
    # --- Input Validation End ---

    # Start with all files
    files_list = []
    processed_file_ids = set()  # Track processed files to avoid duplicates
    global_files = DB.get("files", {})
    
    # First pass: Build mapping of file_id to all channels it appears in
    file_to_channels = {}  # {file_id: [(channel_id, channel_name), ...]}
    for channel_id, channel_data in DB.get("channels", {}).items():
        channel_name = channel_data.get("name", "")
        if "files" in channel_data:
            for file_id in channel_data["files"].keys():
                if file_id not in file_to_channels:
                    file_to_channels[file_id] = []
                file_to_channels[file_id].append((channel_id, channel_name))
    
    # Second pass: Process files using the pre-built mapping
    for file_id, channel_list in file_to_channels.items():
        if file_id in global_files and file_id not in processed_file_ids:
            file_info = global_files[file_id]
            # Create a copy and add channel info
            file_with_info = dict(file_info)
            if "id" not in file_with_info:
                file_with_info["id"] = file_id
            
            # Use pre-built mapping to get all channels
            file_channels = [ch_id for ch_id, ch_name in channel_list]
            file_channel_names = [ch_name for ch_id, ch_name in channel_list]
            
            file_with_info["channels"] = file_channels
            file_with_info["channel_names"] = file_channel_names
            files_list.append(file_with_info)
            processed_file_ids.add(file_id)

    # Also include global files that aren't referenced in any channel
    for file_id, file_info in global_files.items():
        if file_id not in processed_file_ids:
            file_with_info = dict(file_info)
            if "id" not in file_with_info:
                file_with_info["id"] = file_id
            if "channels" not in file_with_info:
                file_with_info["channels"] = []
            file_with_info["channel_names"] = []
            files_list.append(file_with_info)

    filters = _parse_query(query, target_type="files", strict=True)

    # Note: Exclusions (-word) are not applicable to file searches per docstring
    # They are parsed but ignored here for consistency with the API specification
    
    # Handle user filter with traditional filtering (from:@<user>)
    if filters["user"]:
        files_list = [
            file_info for file_info in files_list
            if file_info.get("user", "") == filters["user"]
        ]
    
    # Handle channel filter with traditional filtering (case-insensitive)
    if filters["channel"]:
        channel_filter_lower = filters["channel"].lower()
        files_list = [
            file_info for file_info in files_list
            if any(ch_name.lower() == channel_filter_lower for ch_name in file_info.get("channel_names", []))
        ]

    # Handle filetype filter with traditional filtering (case-insensitive, supports both filetype: and type:)
    if filters["filetype"]:
        filetype_filter_lower = filters["filetype"].lower()
        files_list = [
            file_info for file_info in files_list
            if file_info.get("filetype", "").lower() == filetype_filter_lower
        ]
    
    if filters["date_after"] or filters["date_before"] or filters["date_during"]:
        filtered_files = []
        for file_info in files_list:
            file_timestamp = file_info.get("created")
            if file_timestamp is None:
                continue
                
            try:
                file_date = _convert_timestamp_to_utc_date(str(file_timestamp))
                
                # Check date_after filter
                if filters["date_after"]:
                    date_after = datetime.datetime.strptime(filters["date_after"], "%Y-%m-%d").date()
                    if file_date <= date_after:
                        continue
                
                # Check date_before filter
                if filters["date_before"]:
                    date_before = datetime.datetime.strptime(filters["date_before"], "%Y-%m-%d").date()
                    if file_date >= date_before:
                        continue
                
                # Check date_during filter
                if filters["date_during"]:
                    during_value = filters["date_during"]
                    # Year-only filter (e.g., during:2024)
                    if re.fullmatch(r"\d{4}", during_value):
                        file_year = file_date.year
                        if file_year != int(during_value):
                            continue

                    # Year and Month filter (e.g., during:2024-03)
                    elif re.fullmatch(r"\d{4}-\d{2}", during_value):
                        year, month = map(int, during_value.split("-"))
                        file_year, file_month = file_date.year, file_date.month
                        if file_year != year or file_month != month:
                            continue

                    # Full Date filter (e.g., during:2024-03-23)
                    elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", during_value):
                        date_during = datetime.datetime.strptime(during_value, "%Y-%m-%d").date()
                        if file_date != date_during:
                            continue
                        
                filtered_files.append(file_info)
            except ValueError:
                # Skip files with invalid timestamps
                continue
        files_list = filtered_files

    # Handle has:star filter with traditional filtering
    if "star" in filters["has"]:
        files_list = [
            file_info for file_info in files_list
            if file_info.get("is_starred", False)
        ]
    
    # Handle is: filters (is:pinned, is:saved)
    if "pinned" in filters["is"]:
        files_list = [
            file_info for file_info in files_list
            if file_info.get("is_pinned", False)
        ]
    
    if "saved" in filters["is"]:
        files_list = [
            file_info for file_info in files_list
            if file_info.get("is_saved", False)
        ]

    # Handle filename filter with traditional filtering
    if filters["filename"]:
        filename_term = filters["filename"].lower()
        files_list = [
            file_info for file_info in files_list
            if (filename_term in file_info.get("name", "").lower() or 
                filename_term in file_info.get("title", "").lower())
        ]

    # Handle text queries with search engine (OR logic for files)
    if filters["text"]:
        engine = search_engine_manager.get_engine()
        
        text_matched_ids = set()
        for text_term in filters["text"]:
            # Search in file names
            name_results = engine.search(text_term, {
                "resource_type": "file", 
                "content_type": "name"
            })
            # Search in file titles
            title_results = engine.search(text_term, {
                "resource_type": "file", 
                "content_type": "title"
            })

            # Collect matched file IDs
            for result in name_results + title_results:
                # The search engine returns the original JSON object directly
                if result and result.get("id"):
                    text_matched_ids.add(result.get("id"))

        # Filter files list to only include those that matched text search
        files_list = [
            file_info for file_info in files_list
            if file_info.get("id") in text_matched_ids
        ]

    return files_list


@tool_spec(
    spec={
        'name': 'search_all_content',
        'description': """ Searches for messages and files matching a query.
        
        This function executes a search across both messages and files using a single
        query. The query is a space-separated string of terms and filters. Filters
        are applied to the resource type they are relevant to (e.g., `type:`
        only applies to files). """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The search query. The structure is a space-separated string
                    of terms and filters.
                    
                    For Text Terms:
                    - In Messages: Matched against message content. Default logic is AND,
                      but `OR` can be used to match any term.
                    - In Files: Matched against the file's name and title. The logic is
                      always OR (any term match).
                    
                    Supported Filters:
                    - `in:#<channel_name>`: (Messages & Files) Restricts search to a channel by name (e.g., `in:#general`).
                    - `has:star`: (Messages & Files) Narrows to starred items.
                    - `from:@<username>`: (Messages & Files) Restricts to content from a user (e.g., `from:@alice`).
                    - `has:link`: (Messages-only) Narrows to messages containing a URL.
                    - `has:reaction`: (Messages-only) Narrows to messages with reactions.
                    - `before:`, `after:`, `during:`: (Messages-only) Date-based filters.
                    - `-<word>`: (Messages-only) Excludes messages with the word.
                    - `some*`: (Messages-only) Wildcard support.
                    - `type:<file_type>`: (Files-only) Narrows search to a specific file type.
                    - `filename:<name>`: (Files-only) Search for files containing text in filename or title.
                    - `is:pinned`: (Files-only) Narrows search to files that have been pinned.
                    - `is:saved`: (Files-only) Narrows search to files that have been saved. """
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def search_all(query: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Searches for messages and files matching a query.

    This function executes a search across both messages and files using a single
    query. The query is a space-separated string of terms and filters. Filters
    are applied to the resource type they are relevant to (e.g., `type:`
    only applies to files).

    Args:
        query (str): The search query. The structure is a space-separated string
            of terms and filters.

            For Text Terms:
            - In Messages: Matched against message content. Default logic is AND,
              but `OR` can be used to match any term.
            - In Files: Matched against the file's name and title. The logic is
              always OR (any term match).

            Supported Filters:
            - `in:#<channel_name>`: (Messages & Files) Restricts search to a channel by name (e.g., `in:#general`).
            - `has:star`: (Messages & Files) Narrows to starred items.
            - `from:@<username>`: (Messages & Files) Restricts to content from a user (e.g., `from:@alice`).
            - `has:link`: (Messages-only) Narrows to messages containing a URL.
            - `has:reaction`: (Messages-only) Narrows to messages with reactions.
            - `before:`, `after:`, `during:`: (Messages-only) Date-based filters.
            - `-<word>`: (Messages-only) Excludes messages with the word.
            - `some*`: (Messages-only) Wildcard support.
            - `type:<file_type>`: (Files-only) Narrows search to a specific file type.
            - `filename:<name>`: (Files-only) Search for files containing text in filename or title.
            - `is:pinned`: (Files-only) Narrows search to files that have been pinned.
            - `is:saved`: (Files-only) Narrows search to files that have been saved.

    Returns:
        Dict[str, List[Dict[str, Any]]]: Dictionary containing:
            - messages (List[Dict[str, Any]]): List of matching messages
            - files (List[Dict[str, Any]]): List of matching files
            
    Raises:
        TypeError: If 'query' is not a string.
        ValueError: If query is empty, contains only whitespace, or has invalid date formats.
    """
    # --- Input Validation Start ---
    if not isinstance(query, str):
        raise TypeError(
            f"Argument 'query' must be a string, but got {type(query).__name__}."
        )

    if not query.strip():
        raise ValueError(
            "Argument 'query' must be a non-empty string and cannot contain only whitespace."
        )
    # --- Input Validation End ---

    # Parse query once with all filters for better efficiency
    all_filters = _parse_query(query, target_type="all", strict=False)
    
    # Extract message and file specific filters to avoid redundant parsing
    message_filters = {
        "text": all_filters.get("text", []),
        "excluded": all_filters.get("excluded", []),
        "user": all_filters.get("user"),
        "channel": all_filters.get("channel"),
        "date_after": all_filters.get("date_after"),
        "date_before": all_filters.get("date_before"),
        "date_during": all_filters.get("date_during"),
        "has": all_filters.get("has", set()),
        "wildcard": all_filters.get("wildcard"),
        "boolean": all_filters.get("boolean", "AND"),
    }
    
    file_filters = {
        "text": all_filters.get("text", []),
        "filetype": all_filters.get("filetype"),
        "filename": all_filters.get("filename"),
        "user": all_filters.get("user"),
        "channel": all_filters.get("channel"),
        "date_after": all_filters.get("date_after"),
        "date_before": all_filters.get("date_before"),
        "date_during": all_filters.get("date_during"),
        "has": all_filters.get("has", set()),
        "is": all_filters.get("is", set()),
        "boolean": "OR",  # Files always use OR logic
    }
    
    # Get search engine once if needed for text queries
    engine = None
    if all_filters.get("text"):
        engine = search_engine_manager.get_engine()
    
    # Collect and filter messages in a single pass
    messages_list = _collect_and_filter_messages(message_filters, engine)
    
    # Collect and filter files in a single pass  
    files_list = _collect_and_filter_files(file_filters, engine)

    return {"messages": messages_list, "files": files_list}


def _collect_and_filter_messages(filters: Dict[str, Any], engine=None) -> List[Dict[str, Any]]:
    """
    Efficiently collect and filter messages in a single pass.
    
    Args:
        filters: Parsed message filters
        engine: Search engine instance (if text search is needed)
        
    Returns:
        List of filtered messages
    """
    # Pre-compute text search results if needed
    text_matched_ids = None
    if filters["text"] and engine:
        text_matched_ids = set()
        
        if filters["boolean"] == "OR":
            # OR logic: collect all matching message IDs
            for text_term in filters["text"]:
                search_results = engine.search(text_term, {"resource_type": "message", "content_type": "text"})
                for result in search_results:
                    if result:
                        msg_id = f"{result.get('ts', '')}_{result.get('channel', '')}"
                        text_matched_ids.add(msg_id)
        else:
            # AND logic: find intersection of all terms
            for i, text_term in enumerate(filters["text"]):
                search_results = engine.search(text_term, {"resource_type": "message", "content_type": "text"})
                current_ids = set()
                for result in search_results:
                    if result:
                        msg_id = f"{result.get('ts', '')}_{result.get('channel', '')}"
                        current_ids.add(msg_id)
                
                if i == 0:
                    text_matched_ids = current_ids
                else:
                    text_matched_ids.intersection_update(current_ids)
                    
                # Early exit if no matches remain
                if not text_matched_ids:
                    break
    
    # Pre-compute wildcard pattern if needed
    wildcard_pattern = None
    if filters["wildcard"]:
        wildcard_pattern = filters["wildcard"].replace("*", "").lower()
    
    # Single pass collection and filtering
    messages_list = []
    channels = DB.get("channels", {})
    
    for channel_id, channel_data in channels.items():
        if "messages" not in channel_data:
            continue
            
        channel_name = channel_data.get("name", "")
        
        # Apply channel filter early to skip entire channels
        if filters["channel"] and channel_name != filters["channel"]:
            continue
            
        for msg in channel_data["messages"]:
            # Apply all filters in single pass
            if not _message_passes_filters(msg, filters, channel_id, channel_name, text_matched_ids, wildcard_pattern):
                continue
                
            # Create message with channel info
            msg_with_channel = dict(msg)
            msg_with_channel["channel"] = channel_id
            msg_with_channel["channel_name"] = channel_name
            messages_list.append(msg_with_channel)
    
    return messages_list


def _message_passes_filters(msg: Dict[str, Any], filters: Dict[str, Any], 
                          channel_id: str, channel_name: str, 
                          text_matched_ids: set = None, wildcard_pattern: str = None) -> bool:
    """
    Check if a message passes all filters in a single pass.
    
    Args:
        msg: Message to check
        filters: All message filters
        channel_id: Channel ID
        channel_name: Channel name
        text_matched_ids: Pre-computed text search results
        wildcard_pattern: Pre-computed wildcard pattern
        
    Returns:
        True if message passes all filters
    """
    # User filter
    if filters["user"] and msg.get("user", "") != filters["user"]:
        return False
    
    # Has filters
    has_filters = filters["has"]
    if "link" in has_filters:
        # Check for URLs both in the links field and in message text using regex pattern
        # Matches http://, https://, ftp://, www., and common URL patterns including subdomains
        has_link_field = msg.get("links") and len(msg.get("links", [])) > 0
        url_pattern = r'(?:https?://|ftp://|www\.)\S+|(?:^|\s)[\w.-]+\.(?:com|org|net|edu|gov|io|co|info|biz|dev|uk|ca|au|de|fr|jp|cn|in|br|mx|es|it|nl|se|no|fi|dk|be|ch|at|pl|cz|gr|pt|ie|nz|sg|hk|kr|tw|th|my|ph|id|vn|za|ae|sa|eg|ng|ke|tn|ma|dz|ly|sd|gh|ug|zm|zw|bw|mz|ao|cm|ci|sn|ml|bf|ne|td|so|rw|bi|dj|er|et|gm|gn|gw|lr|mr|sl|tg)(?:/\S*)?'
        has_link_in_text = re.search(url_pattern, msg.get("text", ""), re.IGNORECASE)
        if not (has_link_field or has_link_in_text):
            return False
    if "reaction" in has_filters and not (msg.get("reactions") and len(msg.get("reactions", [])) > 0):
        return False
    if "star" in has_filters and msg.get("is_starred", False) is not True:
        return False
    
    # Date filters
    if (filters["date_before"] or filters["date_after"] or filters["date_during"]) and \
       not _matches_filters(msg, filters, channel_name):
        return False
    
    # Exclusion filters
    if filters["excluded"]:
        msg_text = msg.get("text", "").lower()
        for excluded_word in filters["excluded"]:
            if excluded_word.lower() in msg_text:
                return False
    
    # Text search
    if text_matched_ids is not None:
        msg_id = f"{msg.get('ts', '')}_{channel_id}"
        if msg_id not in text_matched_ids:
            return False
    
    # Wildcard filter
    if wildcard_pattern and wildcard_pattern not in msg.get("text", "").lower():
        return False
    
    return True


def _collect_and_filter_files(filters: Dict[str, Any], engine=None) -> List[Dict[str, Any]]:
    """
    Efficiently collect and filter files in a single pass.
    
    Args:
        filters: Parsed file filters
        engine: Search engine instance (if text search is needed)
        
    Returns:
        List of filtered files
    """
    # Pre-compute text search results if needed
    text_matched_ids = None
    if filters["text"] and engine:
        text_matched_ids = set()
        for text_term in filters["text"]:
            # Search in both name and title
            name_results = engine.search(text_term, {"resource_type": "file", "content_type": "name"})
            title_results = engine.search(text_term, {"resource_type": "file", "content_type": "title"})
            
            for result in name_results + title_results:
                if result and result.get("id"):
                    text_matched_ids.add(result.get("id"))
    
    # Pre-compute filename filter
    filename_term = filters["filename"].lower() if filters["filename"] else None
    
    # Build file-to-channels mapping efficiently
    global_files = DB.get("files", {})
    file_to_channels = {}
    channels = DB.get("channels", {})
    
    for channel_id, channel_data in channels.items():
        channel_name = channel_data.get("name", "")
        if "files" in channel_data:
            for file_id in channel_data["files"].keys():
                if file_id not in file_to_channels:
                    file_to_channels[file_id] = []
                file_to_channels[file_id].append((channel_id, channel_name))
    
    # Single pass collection and filtering
    files_list = []
    processed_file_ids = set()
    
    # Process files referenced in channels
    for file_id, channel_list in file_to_channels.items():
        if file_id not in global_files or file_id in processed_file_ids:
            continue
            
        file_info = global_files[file_id]
        
        # Create file with channel info
        file_channels = [ch_id for ch_id, ch_name in channel_list]
        file_channel_names = [ch_name for ch_id, ch_name in channel_list]
        
        # Apply all filters in single pass
        if _file_passes_filters(file_info, file_id, filters, file_channel_names, 
                              text_matched_ids, filename_term):
            file_with_info = dict(file_info)
            if "id" not in file_with_info:
                file_with_info["id"] = file_id
            file_with_info["channels"] = file_channels
            file_with_info["channel_names"] = file_channel_names
            files_list.append(file_with_info)
        
        processed_file_ids.add(file_id)
    
    # Process global files not in any channel
    for file_id, file_info in global_files.items():
        if file_id in processed_file_ids:
            continue
            
        if _file_passes_filters(file_info, file_id, filters, [], text_matched_ids, filename_term):
            file_with_info = dict(file_info)
            if "id" not in file_with_info:
                file_with_info["id"] = file_id
            if "channels" not in file_with_info:
                file_with_info["channels"] = []
            file_with_info["channel_names"] = []
            files_list.append(file_with_info)
    
    return files_list


def _file_passes_filters(file_info: Dict[str, Any], file_id: str, filters: Dict[str, Any],
                        channel_names: List[str], text_matched_ids: set = None, 
                        filename_term: str = None) -> bool:
    """
    Check if a file passes all filters in a single pass.
    
    Args:
        file_info: File information
        file_id: File ID
        filters: All file filters
        channel_names: List of channel names file is in
        text_matched_ids: Pre-computed text search results
        filename_term: Pre-computed filename search term
        
    Returns:
        True if file passes all filters
    """
    # User filter
    if filters["user"] and file_info.get("user", "") != filters["user"]:
        return False
    
    # Channel filter (case-insensitive)
    if filters["channel"]:
        channel_filter_lower = filters["channel"].lower()
        if not any(ch_name.lower() == channel_filter_lower for ch_name in channel_names):
            return False
    
    # Filetype filter (case-insensitive)
    if filters["filetype"]:
        if file_info.get("filetype", "").lower() != filters["filetype"].lower():
            return False
    
    # Date filters
    if filters["date_after"] or filters["date_before"] or filters["date_during"]:
        file_timestamp = file_info.get("created")
        if file_timestamp is None:
            return False
        
        try:
            file_date = _convert_timestamp_to_utc_date(str(file_timestamp))
            
            if filters["date_after"]:
                date_after = datetime.datetime.strptime(filters["date_after"], "%Y-%m-%d").date()
                if file_date <= date_after:
                    return False
            
            if filters["date_before"]:
                date_before = datetime.datetime.strptime(filters["date_before"], "%Y-%m-%d").date()
                if file_date >= date_before:
                    return False
            
            if filters["date_during"]:
                during_value = filters["date_during"]
                if re.fullmatch(r"\d{4}", during_value):
                    if file_date.year != int(during_value):
                        return False
                elif re.fullmatch(r"\d{4}-\d{2}", during_value):
                    year, month = map(int, during_value.split("-"))
                    if file_date.year != year or file_date.month != month:
                        return False
                elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", during_value):
                    date_during = datetime.datetime.strptime(during_value, "%Y-%m-%d").date()
                    if file_date != date_during:
                        return False
        except ValueError:
            return False
    
    # Has filters
    if "star" in filters["has"] and not file_info.get("is_starred", False):
        return False
    
    # Is filters
    if "pinned" in filters["is"] and not file_info.get("is_pinned", False):
        return False
    if "saved" in filters["is"] and not file_info.get("is_saved", False):
        return False
    
    # Filename filter
    if filename_term:
        name = file_info.get("name", "").lower()
        title = file_info.get("title", "").lower()
        if filename_term not in name and filename_term not in title:
            return False
    
    # Text search
    if text_matched_ids is not None and file_id not in text_matched_ids:
        return False
    
    return True
