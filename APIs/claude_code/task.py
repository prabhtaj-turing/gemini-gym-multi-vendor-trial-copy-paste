from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict

from common_utils.log_complexity import log_complexity


@log_complexity
@tool_spec(
    spec={
        'name': 'task',
        'description': 'Launch a new agent to handle complex, multi-step tasks autonomously.',
        'parameters': {
            'type': 'object',
            'properties': {
                'description': {
                    'type': 'string',
                    'description': 'A short description of the task.'
                },
                'prompt': {
                    'type': 'string',
                    'description': 'The task for the agent to perform.'
                },
                'subagent_type': {
                    'type': 'string',
                    'description': 'The type of specialized agent to use for this task.'
                }
            },
            'required': [
                'description',
                'prompt',
                'subagent_type'
            ]
        }
    }
)
def task(
    description: str,
    prompt: str,
    subagent_type: str,
) -> Dict[str, Any]:
    """Launch a new agent to handle complex, multi-step tasks autonomously.

    Args:
        description (str): A short description of the task.
        prompt (str): The task for the agent to perform.
        subagent_type (str): The type of specialized agent to use for this task.

    Returns:
        Dict[str, Any]: A dictionary containing the result of the task with the following key:
            - "result" (str): A string indicating the task has been completed.

    Raises:
        TypeError: If any of the arguments are not strings.
    """
    if not all(isinstance(arg, str) for arg in [description, prompt, subagent_type]):
        raise TypeError("All arguments must be strings")

    # In a real implementation, this would involve a more complex sub-agent framework.
    # For simulation purposes, we'll return a mock response.
    return {
        "result": f"Task '{description}' with sub-agent '{subagent_type}' has been completed. "
        f"Prompt: {prompt}"
    }
