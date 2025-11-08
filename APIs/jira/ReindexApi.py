from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/ReindexApi.py
from .SimulationEngine.db import DB
from datetime import datetime, timezone
from typing import Dict, Any


@tool_spec(
    spec={
        'name': 'start_reindex',
        'description': """ Start a reindex operation in Jira.
        
        This method initiates a reindex operation which rebuilds the search indexes in Jira.
        The reindex can be performed in either FOREGROUND or BACKGROUND mode with additional
        options for indexing specific content types. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'reindex_type': {
                    'type': 'string',
                    'description': """ The type of reindex to perform. 
                    - "FOREGROUND": Reindex runs in the foreground, blocking other operations
                    - "BACKGROUND": Reindex runs in the background, allowing other operations
                    Defaults to "FOREGROUND". Cannot be empty or whitespace-only. """
                },
                'index_change_history': {
                    'type': 'boolean',
                    'description': """ Whether changeHistory should be reindexed.
                    Not relevant for foreground reindex where changeHistory is always reindexed.
                    Defaults to False. """
                },
                'index_worklogs': {
                    'type': 'boolean',
                    'description': """ Whether worklogs should be reindexed.
                    Not relevant for foreground reindex where worklogs are always reindexed. 
                    Defaults to False. """
                },
                'index_comments': {
                    'type': 'boolean',
                    'description': """ Whether comments should be reindexed.
                    Not relevant for foreground reindex where comments are always reindexed.
                    Defaults to False. """
                }
            },
            'required': []
        }
    }
)
def start_reindex(
    reindex_type: str = "FOREGROUND", 
    index_change_history: bool = False,
    index_worklogs: bool = False, 
    index_comments: bool = False
) -> Dict[str, Any]:
    """
    Start a reindex operation in Jira.

    This method initiates a reindex operation which rebuilds the search indexes in Jira.
    The reindex can be performed in either FOREGROUND or BACKGROUND mode with additional
    options for indexing specific content types.

    Args:
        reindex_type (str, optional): The type of reindex to perform. 
            - "FOREGROUND": Reindex runs in the foreground, blocking other operations
            - "BACKGROUND": Reindex runs in the background, allowing other operations
            Defaults to "FOREGROUND". Cannot be empty or whitespace-only.
        index_change_history (bool, optional): Whether changeHistory should be reindexed.
            Not relevant for foreground reindex where changeHistory is always reindexed.
            Defaults to False.
        index_worklogs (bool, optional): Whether worklogs should be reindexed.
            Not relevant for foreground reindex where worklogs are always reindexed. 
            Defaults to False.
        index_comments (bool, optional): Whether comments should be reindexed.
            Not relevant for foreground reindex where comments are always reindexed.
            Defaults to False.

    Returns:
        Dict[str, Any]: A dictionary containing reindex operation details:
            - currentProgress (int): Current progress percentage (0-100)
            - currentSubTask (str): Description of current reindex task
            - finishTime (str): Estimated finish time (ISO 8601 format)
            - progressUrl (str): URL to check progress status
            - startTime (str): When the reindex started (ISO 8601 format)
            - submittedTime (str): When the reindex was submitted (ISO 8601 format)
            - success (bool): Whether the reindex was successfully started
            - type (str): The type of reindex being performed

    Raises:
        TypeError: If parameters are not of the expected types
        ValueError: If reindex_type is not "FOREGROUND" or "BACKGROUND"
    """
    # Input validation - Type checking
    if not isinstance(reindex_type, str):
        raise TypeError("reindex_type parameter must be a string")
    
    if not isinstance(index_change_history, bool):
        raise TypeError("index_change_history parameter must be a boolean")
        
    if not isinstance(index_worklogs, bool):
        raise TypeError("index_worklogs parameter must be a boolean")
        
    if not isinstance(index_comments, bool):
        raise TypeError("index_comments parameter must be a boolean")
    
    # Input validation - Value checking
    valid_types = ["FOREGROUND", "BACKGROUND"]
    if reindex_type not in valid_types:
        raise ValueError(f"reindex_type must be one of {valid_types}, got '{reindex_type}'")
    
    # Generate timestamps
    current_time = datetime.now(timezone.utc)
    submitted_time = current_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "+0000"
    start_time = submitted_time  # For simulation, start immediately
    finish_time = "<string>"  # Placeholder as per specification
    
    # Get base URL for progress URL
    base_url = DB.get("server_info", {}).get("baseUrl", "http://localhost:8080")
    progress_url = f"{base_url}/rest/api/2/reindex/progress"
    
    # Update database with enhanced reindex info
    DB["reindex_info"] = {
        "running": True,
        "type": reindex_type,
        "currentProgress": 0,
        "currentSubTask": "Currently reindexing",
        "finishTime": finish_time,
        "progressUrl": progress_url,
        "startTime": start_time,
        "submittedTime": submitted_time,
        "indexChangeHistory": index_change_history,
        "indexWorklogs": index_worklogs,
        "indexComments": index_comments
    }
    
    return {
        "currentProgress": 0,
        "currentSubTask": "Currently reindexing", 
        "finishTime": finish_time,
        "progressUrl": progress_url,
        "startTime": start_time,
        "submittedTime": submitted_time,
        "success": True,
        "type": reindex_type
    }


@tool_spec(
    spec={
        'name': 'get_reindex_status',
        'description': """ Get the current status of the reindex operation.
        
        This method returns comprehensive information about any ongoing reindex operation,
        including progress details, timestamps, and configuration. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_reindex_status() -> Dict[str, Any]:
    """
    Get the current status of the reindex operation.

    This method returns comprehensive information about any ongoing reindex operation,
    including progress details, timestamps, and configuration.

    Returns:
        Dict[str, Any]: A dictionary containing detailed reindex status:
            - running (bool): True if a reindex operation is currently in progress
            - type (str): The type of the current reindex operation ("FOREGROUND" or "BACKGROUND")
            - currentProgress (int): Current progress percentage (0-100)
            - currentSubTask (str): Description of current reindex task
            - finishTime (str): Estimated finish time (ISO 8601 format)
            - progressUrl (str): URL to check progress status
            - startTime (str): When the reindex started (ISO 8601 format)
            - submittedTime (str): When the reindex was submitted (ISO 8601 format)
            - indexChangeHistory (bool): Whether change history is being reindexed
            - indexWorklogs (bool): Whether worklogs are being reindexed
            - indexComments (bool): Whether comments are being reindexed

    """
    reindex_info = DB.get("reindex_info", {})
    
    # Basic compatibility fields
    basic_status = {
        "running": reindex_info.get("running", False),
        "type": reindex_info.get("type", None),
    }
    
    # If reindex is running, include enhanced progress information
    if reindex_info.get("running", False):
        basic_status.update({
            "currentProgress": reindex_info.get("currentProgress", 0),
            "currentSubTask": reindex_info.get("currentSubTask", "Currently reindexing"),
            "finishTime": reindex_info.get("finishTime", "<string>"),
            "progressUrl": reindex_info.get("progressUrl", ""),
            "startTime": reindex_info.get("startTime", ""),
            "submittedTime": reindex_info.get("submittedTime", ""),
            "indexChangeHistory": reindex_info.get("indexChangeHistory", False),
            "indexWorklogs": reindex_info.get("indexWorklogs", False),
            "indexComments": reindex_info.get("indexComments", False)
        })
    
    return basic_status
