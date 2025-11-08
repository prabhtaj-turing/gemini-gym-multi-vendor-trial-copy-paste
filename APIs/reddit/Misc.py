from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any

"""
Simulation of /misc endpoints.
Handles miscellaneous API endpoints.
"""

@tool_spec(
    spec={
        'name': 'get_oauth_scopes',
        'description': 'Retrieves all available OAuth scopes and their descriptions.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_api_v1_scopes() -> Dict[str, Any]:
    """
    Retrieves all available OAuth scopes and their descriptions.

    Returns:
        Dict[str, Any]:
        - If there is an error retrieving scopes, returns a dictionary with the key "error" and the value "Failed to retrieve OAuth scopes.".
        - On successful retrieval, returns a dictionary with the following keys:
            - scopes (Dict[str, str]): A dictionary mapping scope names to their descriptions
                - identity (str): "Access identity"
                - mysubreddits (str): "Access user subreddits"
    """
    return {"scopes": {"identity": "Access identity", "mysubreddits": "Access user subreddits"}}