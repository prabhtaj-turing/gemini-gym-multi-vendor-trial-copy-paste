from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict
from pydantic import ValidationError
from retail.SimulationEngine.custom_errors import InvalidInputError
from retail.SimulationEngine.models import TransferToHumanAgentsInput


@tool_spec(
    spec={
        'name': 'transfer_to_human_agents',
        'description': 'Transfer the user to a human agent.',
        'parameters': {
            'type': 'object',
            'properties': {
                'summary': {
                    'type': 'string',
                    'description': "A summary of the user's issue."
                }
            },
            'required': [
                'summary'
            ]
        }
    }
)
def transfer_to_human_agents(summary: str) -> str:
    """Transfer the user to a human agent.

    Args:
        summary (str): A summary of the user's issue.

    Returns:
        str: A confirmation message.

    Raises:
        InvalidInputError: If the input is invalid.
    """
    try:
        TransferToHumanAgentsInput(summary=summary)
    except ValidationError as e:
        raise InvalidInputError(e)

    return "Transfer successful"
