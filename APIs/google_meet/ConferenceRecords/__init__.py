"""
ConferenceRecords API for Google Meet API simulation.
"""

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Optional, List, Union
from google_meet.SimulationEngine.db import DB
from google_meet.SimulationEngine.utils import paginate_results, validate_datetime_string


@tool_spec(
    spec={
        'name': 'get_conference_record',
        'description': """ Gets a conference record by conference ID.
        
        Retrieves detailed information about a specific conference record. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'name': {
                    'type': 'string',
                    'description': 'Resource name of the conference to retrieve.'
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
    Gets a conference record by conference ID.

    Retrieves detailed information about a specific conference record.

    Args:
        name (str): Resource name of the conference to retrieve.

    Returns:
        Dict[str, str]: A dictionary.
        - On successful retrieval, returns a dictionary with the following keys and value types:
            - "id" (str): The conference record identifier
            - "start_time" (str): The time when the conference started (ISO 8601 format: "2023-01-01T10:00:00Z")
            - Additional conference-specific properties, which may include:
                - meeting_code (Optional[str])
                - name (Optional[str])
                - end_time (Optional[str]): The time when the conference ended (ISO 8601 format: "2023-01-01T11:00:00Z")

    Raises:
        TypeError: If the conference record name is not a string.
        ValueError: If the conference record name is empty or whitespace-only.
        KeyError: If the conference record is not found.
    """
    if not isinstance(name, str):
        raise TypeError(f"Conference record name must be a string, got {type(name).__name__}")
    name = name.strip()
    if not name:
        raise ValueError("Conference record name is required and cannot be empty or whitespace-only")
    if name not in DB["conferenceRecords"]:
        raise KeyError(f"Conference record not found: {name}")
    
    # Validate datetime fields if they exist
    record = DB["conferenceRecords"][name]
    try:
        if "start_time" in record and record["start_time"]:
            validate_datetime_string(record["start_time"], "start_time")
        if "end_time" in record and record["end_time"]:
            validate_datetime_string(record["end_time"], "end_time")
    except ValueError as e:
        record["start_time"] = ""
        record["end_time"] = ""
    
    return record


@tool_spec(
    spec={
        'name': 'list_conference_records',
        'description': """ Lists the conference records.
        
        Retrieves a list of conference records with optional filtering and pagination.
        By default, results are ordered by start time in descending order (most recent first). """,
        'parameters': {
            'type': 'object',
            'properties': {
                'filter': {
                    'type': 'string',
                    'description': """ An optional filter string to apply to the records. The filter is applied
                    to the string representation of each record object. Defaults to None. """
                },
                'pageSize': {
                    'type': 'integer',
                    'description': 'An optional maximum number of records to return per page, defaults to 100.'
                },
                'pageToken': {
                    'type': 'string',
                    'description': 'An optional token for pagination, representing the start index.'
                }
            },
            'required': []
        }
    }
)
def list(
    filter: Optional[str] = None,
    pageSize: int = 100,
    pageToken: Optional[str] = None,
) -> Dict[str, Union[List[Dict[str, str]], Optional[str]]]:
    """
    Lists the conference records.

    Retrieves a list of conference records with optional filtering and pagination.
    By default, results are ordered by start time in descending order (most recent first).

    Args:
        filter (Optional[str]): An optional filter string to apply to the records. The filter is applied
                to the string representation of each record object. Defaults to None.
        pageSize (int): An optional maximum number of records to return per page, defaults to 100.
        pageToken (Optional[str]): An optional token for pagination, representing the start index.

    Returns:
        Dict[str, Union[List[Dict[str, str]], Optional[str]]]: A dictionary.
        - On successful retrieval, returns a dictionary with the following keys and value types:
            - "conferenceRecords" (List[Dict[str, str]]): A list of conference record objects,
                each containing:
                - "id" (str): The conference record identifier
                - "start_time" (str): The time when the conference started (ISO 8601 format: "2023-01-01T10:00:00Z")
                - Additional conference-specific properties
            - "nextPageToken" (Optional[str]): A token for the next page of results,
                if more results exist

    Raises:
        TypeError: If input arguments fail validation.
        ValueError: If input arguments fail validation.
    """
    if filter:
        if not isinstance(filter, str):
            raise TypeError("filter must be a string")

        filter = filter.strip()
        if not filter:
            raise ValueError("Filter cannot be empty")

    if not isinstance(pageSize, int):
        raise TypeError("pageSize must be an integer")

    if pageSize <= 0:
        raise ValueError("pageSize must be positive")

    if pageToken:
        if not isinstance(pageToken, str):
            raise TypeError("pageToken must be a string")

        pageToken = pageToken.strip()
        if not pageToken:
            raise ValueError("pageToken cannot be empty")

    records = [value for value in DB["conferenceRecords"].values()]

    if filter:
        records = [r for r in records if filter in str(r)]

    # Sort by start_time in descending order
    # Validate datetime fields before sorting to ensure proper comparison
    for record in records:
        if "start_time" in record and record["start_time"]:
            try:
                validate_datetime_string(record["start_time"], "start_time")
            except ValueError:
                # If validation fails, use empty string for sorting (will appear at the end)
                record["start_time"] = ""
    
    records.sort(key=lambda x: x.get("start_time", ""), reverse=True)

    return paginate_results(records, "conferenceRecords", pageSize, pageToken)
