from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Union, Optional

from .SimulationEngine import utils
from .SimulationEngine.custom_errors import NotFoundError, InvalidInputError

@tool_spec(
    spec={
        'name': 'get_workflow_usage',
        'description': """ Get usage statistics of a workflow.
        
        This function retrieves the billable usage statistics for a specific workflow,
        broken down by operating system. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'owner': {
                    'type': 'string',
                    'description': 'The account owner of the repository. The name is not case sensitive.'
                },
                'repo': {
                    'type': 'string',
                    'description': 'The name of the repository without the .git extension. The name is not case sensitive.'
                },
                'workflow_id': {
                    'type': 'integer',
                    'description': """ The ID of the workflow (as an positive integer) or the workflow's filename
                    (as a string, e.g., 'ci.yml'). """
                }
            },
            'required': [
                'owner',
                'repo',
                'workflow_id'
            ]
        }
    }
)
def get_workflow_usage(
    owner: str,
    repo: str,
    workflow_id: Union[int, str] 
) -> Dict[str, Any]:
    """Get usage statistics of a workflow.

    This function retrieves the billable usage statistics for a specific workflow,
    broken down by operating system.

    Args:
        owner (str): The account owner of the repository. The name is not case sensitive.
        repo (str): The name of the repository without the .git extension. The name is not case sensitive.
        workflow_id (Union[int, str]): The ID of the workflow (as an positive integer) or the workflow's filename
                                       (as a string, e.g., 'ci.yml').

    Returns:
        Dict[str, Any]: A dictionary representing the usage statistics for the workflow.
            This dictionary contains the following key:
            billable (Dict[str, Dict[str, int]]): Contains billable time information
                for different runner OS types. This dictionary maps OS strings
                (e.g., 'UBUNTU', 'MACOS', 'WINDOWS') to OS-specific usage
                dictionaries. Each OS-specific usage dictionary (the value
                associated with an OS string key) contains the following keys:
                    total_ms (int): Total milliseconds used by runners for that OS.
                    jobs (int): Number of jobs run on runners for that OS.
                Note: An OS key (e.g., 'UBUNTU') might be absent from the `billable`
                dictionary if there is no usage for that OS.

    Raises:
        InvalidInputError: If owner, repo, or workflow_id are invalid.
        NotFoundError: If the specified owner, repository, or workflow ID does not exist.
    """
    if not isinstance(owner, str) or not owner.strip():
        raise InvalidInputError("Owner must be a non-empty string.")
    if not isinstance(repo, str) or not repo.strip():
        raise InvalidInputError("Repo must be a non-empty string.")
    
    # Validate workflow_id
    if workflow_id is None: # Explicitly check for None first
        raise InvalidInputError("Workflow ID/filename must be provided and non-empty.") # Covers line 47
    
    if isinstance(workflow_id, str):
        if not workflow_id.strip():
            raise InvalidInputError("Workflow ID (if string filename) must not be empty.")
    elif isinstance(workflow_id, int):
        if isinstance(workflow_id, bool): # bool is a subclass of int, handle it specifically
            raise InvalidInputError("Workflow ID must be a non-empty string (filename) or an integer (ID).")
        if workflow_id <= 0:
            raise InvalidInputError("Workflow ID (if integer) must be positive.")
    else: # Not str, not int (and not bool because it's caught above)
        raise InvalidInputError("Workflow ID must be a non-empty string (filename) or an integer (ID).") # Covers line 49

    workflow_data = utils.get_workflow_by_id_or_filename(owner, repo, workflow_id)

    if not workflow_data:
        if not utils.get_repository(owner, repo):
            raise NotFoundError(f"Repository '{owner}/{repo}' not found.")
        else:
            raise NotFoundError(f"Workflow with ID/filename '{workflow_id}' not found in repository '{owner}/{repo}'.")

    usage_stats = workflow_data.get('usage')
    billable_data = {} 

    if isinstance(usage_stats, dict) and isinstance(usage_stats.get('billable'), dict):
        billable_data = usage_stats['billable']
    
    return {"billable": billable_data}