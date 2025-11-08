"""
Entries API for Google Meet API simulation.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional, List, Union
from pydantic import ValidationError
from google_meet.SimulationEngine.db import DB
from google_meet.SimulationEngine.utils import paginate_results, validate_datetime_string
from google_meet.SimulationEngine.models import TranscriptEntriesListParams


@tool_spec(
    spec={
        'name': 'get_transcript_entry',
        'description': 'Gets a transcript entry by entry ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'Resource name of the entry.'
                }
            },
            'required': [
                'name'
            ]
        }
    }
)
def get(name: str) -> Dict[str, str]:
    """
    Gets a transcript entry by entry ID.

    Args:
        name (str): Resource name of the entry.

    Returns:
        Dict[str, str]: A dictionary.
        - If the entry is found, returns an entry object with keys such as:
            - "id" (str): The entry identifier
            - "parent" (str): ID of the parent transcript
            - "start_time" (str): The time when the entry was created (ISO 8601 format: "2023-01-01T10:00:00Z")
            - "text" (str): The transcript text content
            - Additional entry-specific properties
    Raises:
        TypeError: If the entry name is not a string
        ValueError: If the entry name is empty or whitespace-only
        ValueError: If the entry is not found
    """
    if not isinstance(name, str):
        raise TypeError(f"Entry name must be a string, got {type(name).__name__}")
    if not name or not name.strip():
        raise ValueError("Entry name is required and cannot be empty or whitespace-only")
    if name not in DB["entries"]:
        raise ValueError(f"Entry {name} not found")
    
    # Validate datetime fields if they exist
    entry = DB["entries"][name]
    try:
        if "start_time" in entry and entry["start_time"]:
            validate_datetime_string(entry["start_time"], "start_time")
    except ValueError as e:
        entry["start_time"] = ""
    
    return entry


@tool_spec(
    spec={
        'name': 'list_transcript_entries',
        'description': 'Lists the entries of a transcript.',
        'parameters': {
            'type': 'object',
            'properties': {
                'parent': {
                    'type': 'string',
                    'description': 'The parent transcript resource name.'
                },
                'pageSize': {
                    'type': 'integer',
                    'description': 'The maximum number of entries to return, defaults to 100.'
                },
                'pageToken': {
                    'type': 'string',
                    'description': 'The token for continued list pagination, defaults to None.'
                }
            },
            'required': [
                'parent'
            ]
        }
    }
)
def list(
    parent: str, pageSize: Optional[int] = 100, pageToken: Optional[str] = None
) -> Dict[str, Union[List[Dict[str, str]], Optional[str]]]:
    """
    Lists the entries of a transcript.

    Args:
        parent (str): The parent transcript resource name.
        pageSize (Optional[int]): The maximum number of entries to return, defaults to 100.
        pageToken (Optional[str]): The token for continued list pagination, defaults to None.

    Returns:
        Dict[str, Union[List[Dict[str, str]], Optional[str]]]: A dictionary.
        - On successful retrieval, returns a dictionary with:
            - "entries" (List[Dict[str, str]]): List of entry objects, each containing:
                - "id" (str): The entry identifier
                - "parent" (str): ID of the parent transcript
                - "start_time" (str): The time when the entry was created (ISO 8601 format: "2023-01-01T10:00:00Z")
                - "text" (str): The transcript text content
                - Additional entry-specific properties
            - "nextPageToken" (Optional[str]): Token for the next page of results, if more exist
    Raises:
        ValidationError: If the parameters are invalid.
    """
    # Validate parameters
    try:
        params = TranscriptEntriesListParams(
            parent=parent, 
            pageSize=pageSize, 
            pageToken=pageToken
        )
    except ValidationError as e:
        raise ValidationError(f"Invalid parameters: {e}")
    
    # Filter entries by parent transcript
    filtered_entries = [
        entry for entry in DB["entries"].values() 
        if entry.get("parent") == params.parent
    ]

    # Validate datetime fields before sorting
    for entry in filtered_entries:
        if "start_time" in entry and entry["start_time"]:
            try:
                validate_datetime_string(entry["start_time"], "start_time")
            except ValueError:
                # If validation fails, use empty string for sorting (will appear at the end)
                entry["start_time"] = ""

    # Sort by start_time in ascending order
    filtered_entries.sort(key=lambda x: x.get("start_time", ""))

    return paginate_results(filtered_entries, "entries", params.pageSize, params.pageToken) 
