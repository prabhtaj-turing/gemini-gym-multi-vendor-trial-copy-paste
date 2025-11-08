"""
Transcripts API for Google Meet API simulation.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional, List, Union
from google_meet.SimulationEngine.db import DB
from google_meet.SimulationEngine.utils import paginate_results, validate_datetime_string
from google_meet.SimulationEngine.models import TranscriptsListParams
from google_meet.SimulationEngine.custom_errors import InvalidTranscriptNameError, NotFoundError


@tool_spec(
    spec={
        'name': 'get_conference_transcript',
        'description': 'Gets a transcript by transcript ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'Resource name of the transcript.'
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
    Gets a transcript by transcript ID.

    Args:
        name (str): Resource name of the transcript.

    Returns:
        Dict[str, str]: A dictionary.
        - If the transcript is found, returns a transcript object with keys such as:
            - "id" (str): The transcript identifier
            - "parent" (str): ID of the parent conference record
            - "start_time" (str): The time when the transcript started (ISO 8601 format: "2023-01-01T10:00:00Z")
            - Additional transcript-specific properties
    Raises:
        InvalidTranscriptNameError: If the transcript name is invalid (empty or whitespace-only).
        NotFoundError: If the transcript is not found.
    """
    if not name or not name.strip():
        raise InvalidTranscriptNameError("Transcript name is required and cannot be empty or whitespace-only")
    elif name not in DB["transcripts"]:
        raise NotFoundError(f"Transcript not found: {name}")
    else:
        # Validate datetime fields if they exist
        transcript = DB["transcripts"][name]
        try:
            if "start_time" in transcript and transcript["start_time"]:
                validate_datetime_string(transcript["start_time"], "start_time")
        except ValueError as e:
            transcript["start_time"] = ""
        
        return transcript

@tool_spec(
    spec={
        'name': 'list_conference_transcript',
        'description': 'Lists the transcripts of a conference.',
        'parameters': {
            'type': 'object',
            'properties': {
                'parent': {
                    'type': 'string',
                    'description': 'The parent resource name.'
                },
                'pageSize': {
                    'type': 'integer',
                    'description': 'The maximum number of transcripts to return, defaults to 100.'
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
    parent: str,
    pageSize: int = 100,
    pageToken: Optional[str] = None,
) -> Dict[str, Union[List[Dict[str, str]], Optional[str]]]:
    """
    Lists the transcripts of a conference.

    Args:
        parent (str): The parent resource name.
        pageSize (int): The maximum number of transcripts to return, defaults to 100.
        pageToken (Optional[str]): The token for continued list pagination, defaults to None.

    Returns:
        Dict[str, Union[List[Dict[str, str]], Optional[str]]]: A dictionary.
        - On successful retrieval, returns a dictionary with:
            - "transcripts" (List[Dict[str, str]]): List of transcript objects, each containing:
                - "id" (str): The transcript identifier
                - "parent" (str): ID of the parent conference record
                - "start_time" (str): The time when the transcript started (ISO 8601 format: "2023-01-01T10:00:00Z")
                - Additional transcript-specific properties
            - "nextPageToken" (Optional[str]): Token for the next page of results, if more exist

    Raises:
        ValidationError: If input arguments fail validation.
        NotFoundError: If no transcripts are found for the given parent.
    """
    # Validate parameters using pydantic
    validated_params = TranscriptsListParams(
        parent=parent,
        pageToken=pageToken,
        pageSize=pageSize
    )

    # Filter transcripts by parent conference record
    filtered_transcripts = [
        transcript
        for transcript in DB["transcripts"].values()
        if transcript.get("parent") == validated_params.parent
    ]

    if not filtered_transcripts:
        raise NotFoundError(f"No transcripts found for parent: {validated_params.parent}")

    # Validate datetime fields before sorting
    for transcript in filtered_transcripts:
        if "start_time" in transcript and transcript["start_time"]:
            try:
                validate_datetime_string(transcript["start_time"], "start_time")
            except ValueError:
                # If validation fails, use empty string for sorting (will appear at the end)
                transcript["start_time"] = ""

    # Sort by start_time in ascending order
    filtered_transcripts.sort(key=lambda x: x.get("start_time", ""))

    return paginate_results(filtered_transcripts, "transcripts", validated_params.pageSize, validated_params.pageToken)
