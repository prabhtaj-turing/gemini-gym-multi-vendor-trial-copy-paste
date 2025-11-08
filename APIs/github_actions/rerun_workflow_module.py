from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any
from datetime import datetime, timezone

from .SimulationEngine import utils
from .SimulationEngine.custom_errors import NotFoundError, InvalidInputError, ConflictError
from .SimulationEngine.models import WorkflowRunStatus 

@tool_spec(
    spec={
        'name': 'rerun_workflow',
        'description': """ Re-run a workflow run.
        
        This API endpoint allows re-running a previously executed workflow run.
        It creates a new workflow run attempt based on the original run's configuration.
        The new run will start in a 'queued' state. """,
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
                'run_id': {
                    'type': 'integer',
                    'description': 'The unique identifier of the workflow run to re-run.'
                }
            },
            'required': [
                'owner',
                'repo',
                'run_id'
            ]
        }
    }
)
def rerun_workflow(owner: str, repo: str, run_id: int) -> Dict[str, Any]:
    """Re-run a workflow run.

    This API endpoint allows re-running a previously executed workflow run.
    It creates a new workflow run attempt based on the original run's configuration.
    The new run will start in a 'queued' state.

    Args:
        owner (str): The account owner of the repository. The name is not case sensitive.
        repo (str): The name of the repository without the .git extension. The name is not case sensitive.
        run_id (int): The unique identifier of the workflow run to re-run.

    Returns:
        Dict[str, Any]: An empty dictionary to acknowledge successful processing of the re-run request.

    Raises:
        InvalidInputError: If the provided owner, repo, or run_id are invalid (e.g., empty strings, non-positive run_id).
        NotFoundError: If the specified owner, repository, or the original run_id does not exist.
        ConflictError: If the original workflow run is currently in a state that prohibits re-running (e.g., already in_progress or queued).
    """
    if not isinstance(owner, str) or not owner.strip():
        raise InvalidInputError("Owner must be a non-empty string.")
    if not isinstance(repo, str) or not repo.strip():
        raise InvalidInputError("Repo must be a non-empty string.")
    if not isinstance(run_id, int) or run_id <= 0:
        raise InvalidInputError("Run ID must be a positive integer.")

    original_run_data = utils.get_workflow_run_by_id(owner, repo, run_id)

    if not original_run_data:
        if not utils.get_repository(owner, repo): # Check if repo itself is missing
            raise NotFoundError(f"Repository '{owner}/{repo}' not found.")
        else:
            raise NotFoundError(f"Workflow run with ID '{run_id}' to re-run not found in repository '{owner}/{repo}'.")

    original_status = original_run_data.get('status')
    # Define statuses that prevent a re-run if the original run is in one of them
    non_rerunnable_active_statuses = [
        WorkflowRunStatus.QUEUED.value,
        WorkflowRunStatus.IN_PROGRESS.value,
        WorkflowRunStatus.WAITING.value,
        WorkflowRunStatus.ACTION_REQUIRED.value,
        WorkflowRunStatus.PENDING.value,
        WorkflowRunStatus.REQUESTED.value,
    ]
    if original_status in non_rerunnable_active_statuses:
        raise ConflictError(f"Workflow run '{run_id}' is currently in status '{original_status}' and cannot be re-run yet.")

    # Prepare data for the new (re-run) workflow instance
    new_run_input_data = {
        'workflow_id': original_run_data['workflow_id'],
        'name': original_run_data.get('name'),
        'head_branch': original_run_data.get('head_branch'),
        'head_sha': original_run_data['head_sha'],
        'event': original_run_data['event'],
        'actor': original_run_data.get('actor'),
        'triggering_actor': original_run_data.get('triggering_actor'),
        'head_commit': original_run_data.get('head_commit'),
        'status': WorkflowRunStatus.QUEUED.value, # New runs start as queued
        'conclusion': None,
        'run_attempt': original_run_data.get('run_attempt', 0) + 1,
        'created_at': datetime.now(timezone.utc), # Fresh timestamps
        'updated_at': datetime.now(timezone.utc),
        'run_started_at': None,
        'run_number': original_run_data['run_number'], # Re-runs typically share the same run_number
        # Jobs are not copied; a new set of jobs will be created for the new run instance.
        # check_suite_id and node_id will be new for the new run.
    }
    
    # It can't retun None because we already have check for repository existence
    utils.add_workflow_run(owner, repo, new_run_input_data)

    return {}