from common_utils.tool_spec_decorator import tool_spec
# APIs/google_calendar/ColorsResource/__init__.py
from .SimulationEngine.db import DB
from typing import Dict, Any


@tool_spec(
    spec={
        'name': 'get_calendar_and_event_colors',
        'description': 'Returns the color definitions for calendars and events.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_colors() -> Dict[str, Any]:
    """
    Returns the color definitions for calendars and events.

    Returns:
        Dict[str, Any]: A dictionary containing the color definitions for calendars and events.
            - calendar (Dict[str, Any]): A dictionary containing the color definitions for calendars.
                - id (str): The identifier of the calendar.
                - background (str): The background color of the calendar.
                - foreground (str): The foreground color of the calendar.
            - event (Dict[str, Any]): A dictionary containing the color definitions for events.
                - id (str): The identifier of the event.
                - background (str): The background color of the event.
                - foreground (str): The foreground color of the event.
    """
    return DB["colors"]
