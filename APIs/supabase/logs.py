"""Defines Supabase logs-related functions.""" 

from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from .SimulationEngine import custom_errors, utils
from .SimulationEngine.db import DB


# Valid service types
VALID_SERVICES = ['api', 'branch-action', 'postgres', 'edge-function', 'auth', 'storage', 'realtime']


@tool_spec(
    spec={
        'name': 'get_logs',
        'description': """ Gets logs for a Supabase project by service type.
        
        This function retrieves logs for a specified Supabase project, filtered by service type,
        to aid in debugging application issues. It only returns logs generated within the
        last minute. If logs older than one minute are required, the actions or tests
        that produce these logs should be re-run to capture them. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'project_id': {
                    'type': 'string',
                    'description': 'The ID of the Supabase project.'
                },
                'service': {
                    'type': 'string',
                    'description': """ The service to fetch logs for. Must be one of 'api',
                    'branch-action', 'postgres', 'edge-function', 'auth', 'storage',
                    'realtime'. """
                }
            },
            'required': [
                'project_id',
                'service'
            ]
        }
    }
)
def get_logs(project_id: str, service: str) -> List[Dict[str, Any]]:
    """Gets logs for a Supabase project by service type.

    This function retrieves logs for a specified Supabase project, filtered by service type,
    to aid in debugging application issues. It only returns logs generated within the
    last minute. If logs older than one minute are required, the actions or tests
    that produce these logs should be re-run to capture them.

    Args:
        project_id (str): The ID of the Supabase project.
        service (str): The service to fetch logs for. Must be one of 'api',
            'branch-action', 'postgres', 'edge-function', 'auth', 'storage',
            'realtime'.

    Returns:
        List[Dict[str, Any]]: A list of log entries for the specified service.
            Note: This endpoint returns logs only from within the last minute.
            If the logs you are looking for are older than 1 minute, you may
            need to re-run your test or actions to reproduce them. Each entry
            is a dictionary with the following keys:
            timestamp (str): ISO 8601 timestamp of the log entry.
            level (str): Log level (e.g., 'INFO', 'ERROR', 'WARN', 'DEBUG').
            message (str): The log message content.
            metadata (Optional[Dict[str, Any]]): Additional structured data
                associated with the log entry (e.g., request_id, region).

    Raises:
        NotFoundError: If the 'project_id' does not exist.
        ValidationError: If the 'service' parameter is not a valid service type
            or is missing.
        LogsNotAvailableError: If logs for the requested service or time frame
            are not available, or if the service does not produce logs.
    """
    # Validate project_id
    if not project_id or (isinstance(project_id, str) and not project_id.strip()):
        raise custom_errors.ValidationError("The 'project_id' parameter cannot be null or empty.")
    
    if not isinstance(project_id, str):
        raise custom_errors.ValidationError("The 'project_id' parameter must be a string.")
    
    # Validate service parameter
    if not service:
        raise custom_errors.ValidationError("The 'service' parameter is required.")
    
    if not isinstance(service, str):
        raise custom_errors.ValidationError("The 'service' parameter must be a string.")
    
    if service not in VALID_SERVICES:
        raise custom_errors.ValidationError(
            f"Invalid service type '{service}'. Must be one of: {', '.join(VALID_SERVICES)}"
        )
    
    # Check if project exists
    project = utils.get_entity_by_id_from_db(DB, "projects", project_id)
    if not project:
        raise custom_errors.NotFoundError(f"Project with id '{project_id}' not found.")
    
    # Get logs from DB with defensive checks
    all_logs_data = DB.get("logs")
    if not isinstance(all_logs_data, dict):
        raise custom_errors.LogsNotAvailableError(
            f"Logs for service '{service}' are not available for project '{project_id}'."
        )
    
    # Get project logs
    project_logs = all_logs_data.get(project_id)
    if not isinstance(project_logs, dict):
        raise custom_errors.LogsNotAvailableError(
            f"Logs for service '{service}' are not available for project '{project_id}'."
        )
    
    # Check if service has logs configured
    if service not in project_logs:
        raise custom_errors.LogsNotAvailableError(
            f"Logs for service '{service}' are not available for project '{project_id}'."
        )
    
    # Get logs for the specific service
    service_logs = project_logs.get(service)
    if not isinstance(service_logs, list):
        raise custom_errors.LogsNotAvailableError(
            f"Logs for service '{service}' are not available for project '{project_id}'."
        )
    
    # Filter logs from the last minute
    current_time = datetime.now(timezone.utc)
    one_minute_ago = current_time - timedelta(minutes=1)
    
    filtered_logs = []
    for log_entry in service_logs:
        # Skip malformed log entries
        if not isinstance(log_entry, dict):
            continue
            
        # Get timestamp
        timestamp_str = log_entry.get('timestamp')
        if not isinstance(timestamp_str, str):
            continue
            
        # Parse the timestamp
        try:
            # Handle both 'Z' suffix and timezone-aware formats
            log_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
            # Ensure timestamp is timezone-aware (assume UTC if naive)
            if log_timestamp.tzinfo is None:
                log_timestamp = log_timestamp.replace(tzinfo=timezone.utc)
                
            if log_timestamp >= one_minute_ago:
                filtered_logs.append(log_entry)
        except ValueError:
            # Skip logs with unparseable timestamps
            continue
    
    # If no logs within the time frame
    if not filtered_logs:
        raise custom_errors.LogsNotAvailableError(
            f"No logs found for service '{service}' within the last minute. "
            "Logs older than 1 minute are not available."
        )
    
    return filtered_logs