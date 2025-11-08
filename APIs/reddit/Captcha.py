from common_utils.tool_spec_decorator import tool_spec
from .SimulationEngine.db import DB

"""
Simulation of /captcha endpoints.
Handles CAPTCHA-related functionality for enhanced security.
"""

@tool_spec(
    spec={
        'name': 'check_captcha_requirement',
        'description': 'Checks if CAPTCHA is required for user requests.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_api_needs_captcha() -> bool:
    """
    Checks if CAPTCHA is required for user requests.

    Returns:
        bool: Returns True if CAPTCHA is required for the current user's requests,
              False otherwise.
    """
    return DB["captcha_needed"]