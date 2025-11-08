from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, Dict, Any
from github_actions.SimulationEngine import utils
from github_actions.SimulationEngine.custom_errors import NotFoundError, InvalidInputError
from github_actions.SimulationEngine.db import DB
from github_actions.SimulationEngine.models import WorkflowDetail

@tool_spec(
    spec={
        'name': 'get_workflow',
        'description': """ Get details of a specific workflow.
        
        Gets details of a specific workflow. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'owner': {
                    'type': 'string',
                    'description': 'The owner of the repository.'
                },
                'repo': {
                    'type': 'string',
                    'description': 'The name of the repository.'
                },
                'workflow_id': {
                    'type': 'string',
                    'description': """ The identifier of the workflow.
                    This can be the workflow's integer ID (as a string)
                    or its filename (e.g., "main.yml" or ".github/workflows/main.yml"). """
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
def get_workflow(owner: str, repo: str, workflow_id: str) -> Dict[str, Any]:
    """Get details of a specific workflow.

    Gets details of a specific workflow.

    Args:
        owner (str): The owner of the repository.
        repo (str): The name of the repository.
        workflow_id (str): The identifier of the workflow.
                             This can be the workflow's integer ID (as a string)
                             or its filename (e.g., "main.yml" or ".github/workflows/main.yml").

    Returns:
        Dict[str, Any]: A dictionary containing details of the workflow with the following keys:
            id (int): Unique identifier of the workflow.
            node_id (str): A globally unique identifier for the workflow.
            name (str): The name of the workflow.
            path (str): The path of the workflow file relative to the repository root.
            state (str): The state of the workflow (e.g., 'active', 'deleted', 'disabled_fork', 'disabled_inactivity', 'disabled_manually').
            created_at (str): Timestamp of when the workflow was created (ISO 8601 format).
            updated_at (str): Timestamp of when the workflow was last updated (ISO 8601 format).

    Raises:
        InvalidInputError: If owner, repo, or workflow_id is empty or consists only of whitespace.
        NotFoundError: If the specified owner, repository, or workflow ID does not exist.
    """
    if not owner or owner.isspace():
        raise InvalidInputError("Owner name cannot be empty or whitespace.")
    if not repo or repo.isspace():
        raise InvalidInputError("Repository name cannot be empty or whitespace.")
    if not workflow_id or workflow_id.isspace():
        raise InvalidInputError("Workflow ID or filename cannot be empty or whitespace.")

    repo_data = utils.get_repository(owner, repo)
    if not repo_data:
        raise NotFoundError(f"Repository '{owner}/{repo}' not found.")

    # workflows_dict is Dict[int, Dict[str, Any]], where the inner Dict represents a Workflow model
    workflows_dict: Optional[Dict[int, Dict[str, Any]]] = repo_data.get('workflows')
    found_workflow_data: Optional[Dict[str, Any]] = None

    if workflows_dict:
        # Try to interpret workflow_id as an integer ID first
        try:
            wf_id_as_int = int(workflow_id)
            if wf_id_as_int in workflows_dict:
                found_workflow_data = workflows_dict[wf_id_as_int]
        except ValueError:
            # workflow_id is not a simple integer string, so it must be a filename/path.
            # The search by filename will proceed if found_workflow_data is still None.
            pass

        if not found_workflow_data:
            # If not found by integer ID (or if workflow_id was not an int string),
            # search by path/filename.
            for wf_data_item in workflows_dict.values():
                workflow_path = wf_data_item.get('path')
                if workflow_path:
                    # workflow_id could be the full path (e.g., ".github/workflows/main.yml")
                    # or just the filename (e.g., "main.yml").
                    if workflow_path == workflow_id or workflow_path.endswith('/' + workflow_id):
                        found_workflow_data = wf_data_item
                        break

    if not found_workflow_data:
        raise NotFoundError(f"Workflow '{workflow_id}' not found in repository '{owner}/{repo}'.")

    workflow_detail_instance = WorkflowDetail(**found_workflow_data)
    return workflow_detail_instance.model_dump()

