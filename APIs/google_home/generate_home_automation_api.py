from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, Dict, Any
from pydantic import ValidationError
from google_home.SimulationEngine.custom_errors import InvalidInputError
from google_home.SimulationEngine.models import GenerateHomeAutomationResult, GenerateHomeAutomationParams


@tool_spec(
    spec={
        'name': 'generate_home_automation',
        'description': 'Generates a home automation script via the Home Agent, and returns the response.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The query to pass to the Home Agent Bard Service'
                },
                'home_name': {
                    'type': 'string',
                    'description': 'The home name which the query applies to'
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def generate_home_automation(
    query: str, home_name: Optional[str] = None
) -> Dict[str, Any]:
    """Generates a home automation script via the Home Agent, and returns the response.

    Args:
        query (str): The query to pass to the Home Agent Bard Service
        home_name (Optional[str]): The home name which the query applies to

    Returns:
        Dict[str, Any]: A dictionary containing the result of the home automation generation.
            - automation_script_code (str): The automation script code.
            - user_instructions (str): Instructions for the user on how to use the script.

    Raises:
        InvalidInputError: If the input parameters are invalid.
    """
    try:
        GenerateHomeAutomationParams(query=query, home_name=home_name)
    except ValidationError as e:
        raise InvalidInputError(f"Invalid input: {e}") from e

    # This is a simplified implementation. A real implementation would
    # need to call the Home Agent Bard Service to generate the script.
    return GenerateHomeAutomationResult(
        automation_script_code="print('Hello, world!')",
        user_instructions="This is a test script.",
    ).model_dump(mode="json")
