"""
Participants API for Google Meet API simulation.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional, List, Union
from pydantic import ValidationError
from google_meet.SimulationEngine.db import DB
from google_meet.SimulationEngine.utils import paginate_results, validate_datetime_string
from google_meet.SimulationEngine.models import ParticipantsListParams


@tool_spec(
    spec={
        'name': 'get_conference_participant',
        'description': 'Gets a participant by ID.',
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'Resource name of the participant.'
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
    Gets a participant by ID.

    Args:
        name (str): Resource name of the participant.

    Returns:
        Dict[str, str]: A dictionary.
        - If the participant is found, returns a participant object with keys such as:
            - "id" (str): The participant identifier
            - "conferenceRecordId" (str): ID of the parent conference record
            - "join_time" (str): The time when the participant joined (ISO 8601 format: "2023-01-01T10:00:00Z")
            - Additional participant-specific properties like:
                - "email" (Optional[str]): Participant's email address
                - "displayName" (Optional[str]): Participant's display name
    Raises:
        ValueError: If the name parameter is None, empty, or not a string
        ValueError: If the participant is not found
    """
    # Validate required parameter
    if not name or not isinstance(name, str):
        raise TypeError("Name parameter is required and must be a non-empty string")

    if name not in DB["participants"]:
        raise ValueError(f"Participant {name} not found")

    # Validate datetime fields if they exist
    participant = DB["participants"][name]
    try:
        if "join_time" in participant and participant["join_time"]:
            validate_datetime_string(participant["join_time"], "join_time")
    except ValueError as e:
        participant["join_time"] = ""

    return participant


@tool_spec(
    spec={
        'name': 'list_conference_participants',
        'description': 'Lists participants of a conference record.',
        'parameters': {
            'type': 'object',
            'properties': {
                'parent': {
                    'type': 'string',
                    'description': 'The parent conference record resource name.'
                },
                'pageSize': {
                    'type': 'integer',
                    'description': 'The maximum number of participants to return, defaults to 100.'
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
    parent: str, pageSize: int = 100, pageToken: Optional[str] = None
) -> Dict[str, Union[List[Dict[str, str]], Optional[str]]]:
    """
    Lists participants of a conference record.

    Args:
        parent (str): The parent conference record resource name.
        pageSize (int): The maximum number of participants to return, defaults to 100.
        pageToken (Optional[str]): The token for continued list pagination, defaults to None.

    Returns:
        Dict[str, Union[List[Dict[str, str]], Optional[str]]]: A dictionary.
        - If validation fails, returns a dictionary with the key "error" and an appropriate error message.
        - On successful retrieval, returns a dictionary with:
            - "participants" (List[Dict[str, str]]): List of participant objects, each containing:
                - "id" (str): The participant identifier
                - "conferenceRecordId" (str): ID of the parent conference record
                - "join_time" (str): The time when the participant joined (ISO 8601 format: "2023-01-01T10:00:00Z")
                - Additional participant-specific properties
            - "nextPageToken" (Optional[str]): Token for the next page of results, if more exist

    Raises:
        ValidationError: If input arguments fail validation.
    """
    # Validate parameters using pydantic
    try:
        validated_params = ParticipantsListParams(
            parent=parent,
            pageSize=pageSize,
            pageToken=pageToken
        )
    except ValidationError as e:
        return {"error": f"Parameter validation failed: {str(e)}"}

    # Filter participants by parent conference record
    filtered_participants = [
        participant
        for participant in DB["participants"].values()
        if participant.get("parent") == validated_params.parent
    ]

    # Validate datetime fields before returning
    for participant in filtered_participants:
        if "join_time" in participant and participant["join_time"]:
            try:
                validate_datetime_string(participant["join_time"], "join_time")
            except ValueError:
                # If validation fails, use empty string for sorting (will appear at the end)
                participant["join_time"] = ""

    return paginate_results(filtered_participants, "participants", validated_params.pageSize, validated_params.pageToken)
