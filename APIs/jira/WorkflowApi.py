from common_utils.tool_spec_decorator import tool_spec
# APIs/jira/WorkflowApi.py
from .SimulationEngine.db import DB
from typing import Dict, List, Any


@tool_spec(
    spec={
        'name': 'get_all_workflows',
        'description': 'Get all workflows.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_workflows() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all workflows.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary containing the workflows' information.
            - workflows (List[Dict[str, Any]]): The workflows' information.
                - id (str): The ID of the workflow.
                - name (str): The name of the workflow.
                - steps (List[str]): The steps of the workflow.
    """
    return {"workflows": list(DB["workflows"].values())}
