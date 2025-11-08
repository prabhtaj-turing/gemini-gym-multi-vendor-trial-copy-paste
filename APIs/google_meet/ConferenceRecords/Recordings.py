"""
Recordings API for Google Meet API simulation.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, List, Optional, Union
from google_meet.SimulationEngine.db import DB
from google_meet.SimulationEngine.utils import paginate_results, validate_datetime_string


@tool_spec(
    spec={
        'name': 'get_conference_recording',
        'description': 'Gets a recording by recording ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'Resource name of the recording.'
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
    Gets a recording by recording ID.

    Args:
        name (str): Resource name of the recording.

    Returns:
        Dict[str, str]: A dictionary containing the recording object with keys such as:
            - "id" (str): The recording identifier
            - "parent" (str): ID of the parent conference record
            - "start_time" (str): The time when the recording started (ISO 8601 format: "2023-01-01T10:00:00Z")
            - Additional recording-specific properties

    Raises:
        ValueError: If the name parameter is None, empty, or not a string
        KeyError: If the recording is not found in the database
    """
    # Input validation
    if name is None:
        raise ValueError("Recording name cannot be None")
    
    if not isinstance(name, str):
        raise ValueError("Recording name must be a string")
    
    if not name.strip():
        raise ValueError("Recording name cannot be empty or whitespace")
    
    # Check if recording exists and raise if not found
    if name not in DB["recordings"]:
        raise KeyError(f"Recording not found: {name}")
    
    # Validate datetime fields if they exist
    recording = DB["recordings"][name]
    try:
        if "start_time" in recording and recording["start_time"]:
            validate_datetime_string(recording["start_time"], "start_time")
    except ValueError as e:
        recording["start_time"] = ""
    
    return recording


@tool_spec(
    spec={
        'name': 'list_conference_recordings',
        'description': 'Lists the recordings of a conference.',
        'parameters': {
            'type': 'object',
            'properties': {
                'parent': {
                    'type': 'string',
                    'description': 'The parent resource name. Must be a non-empty string.'
                },
                'parent_conference_record': {
                    'type': 'string',
                    'description': 'The parent conference record. Must be a non-empty string.'
                },
                'pageSize': {
                    'type': 'integer',
                    'description': """ The maximum number of recordings to return. Must be a positive integer 
                    between 1 and 1000. Defaults to None (no limit). """
                },
                'pageToken': {
                    'type': 'string',
                    'description': 'The token for continued list pagination. Must be a string if provided. Defaults to None.'
                }
            },
            'required': [
                'parent',
                'parent_conference_record'
            ]
        }
    }
)
def list(
    parent: str,
    parent_conference_record: str,
    pageSize: Optional[int] = None,
    pageToken: Optional[str] = None,
) -> Dict[str, Union[List[Dict[str, str]], Optional[str]]]:
    """
    Lists the recordings of a conference.

    Args:
        parent (str): The parent resource name. Must be a non-empty string.
        parent_conference_record (str): The parent conference record. Must be a non-empty string.
        pageSize (Optional[int]): The maximum number of recordings to return. Must be a positive integer 
                                 between 1 and 1000. Defaults to None (no limit).
        pageToken (Optional[str]): The token for continued list pagination. Must be a string if provided. Defaults to None.

    Returns:
        Dict[str, Union[List[Dict[str, str]], Optional[str]]]: A dictionary containing the results.
        - If the parent is invalid, returns a dictionary with:
            - "error" (str): Error message "Invalid parent"
        - On successful retrieval, returns a dictionary with:
            - "recordings" (List[Dict[str, str]]): List of recording objects, each containing:
                - "id" (str): The recording identifier
                - "parent" (str): ID of the parent conference record
                - "start_time" (str): The time when the recording started (ISO 8601 format: "2023-01-01T10:00:00Z")
                - "duration" (str): Duration of the recording
                - "state" (str): Current state of the recording (e.g., "completed", "processing")
                - Additional recording-specific properties
            - "nextPageToken" (Optional[str]): Token for the next page of results, if more exist.
              Use this token in subsequent calls to retrieve additional pages.

    Raises:
        ValueError: If parent or parent_conference_record is empty or invalid, or if pageSize 
                   is not a positive integer or exceeds 1000.
        TypeError: If pageSize is not an integer or pageToken is not a string.
    """
    # Input validations
    if not parent or not isinstance(parent, str):
        raise ValueError("parent must be a non-empty string")
    
    if not parent_conference_record or not isinstance(parent_conference_record, str):
        raise ValueError("parent_conference_record must be a non-empty string")
    
    if pageSize is not None:
        if not isinstance(pageSize, int):
            raise TypeError("pageSize must be an integer")
        if pageSize <= 0:
            raise ValueError("pageSize must be a positive integer")
        if pageSize > 1000:
            raise ValueError("pageSize cannot exceed 1000")
    
    if pageToken is not None and not isinstance(pageToken, str):
        raise TypeError("pageToken must be a string")

    # This is a simplified implementation - in a real API, we would validate parent
    # For test compatibility
    if parent.split("/")[-1] != parent_conference_record:
        return {"error": "Invalid parent"}

    # Filter recordings by parent conference record
    filtered_recordings = [
        recording
        for recording in DB["recordings"].values()
        if recording.get("parent") == parent_conference_record
    ]

    # Validate datetime fields before sorting
    for recording in filtered_recordings:
        if "start_time" in recording and recording["start_time"]:
            try:
                validate_datetime_string(recording["start_time"], "start_time")
            except ValueError:
                # If validation fails, use empty string for sorting (will appear at the end)
                recording["start_time"] = ""

    # Sort by start_time in ascending order
    filtered_recordings.sort(key=lambda x: x.get("start_time", ""))

    return paginate_results(filtered_recordings, "recordings", pageSize, pageToken)
