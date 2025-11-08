from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, Dict, Any
from pydantic import ValidationError
from google_home.SimulationEngine.custom_errors import InvalidInputError
from google_home.SimulationEngine.models import SearchHomeEventsResult, SearchHomeEventsParams


@tool_spec(
    spec={
        'name': 'search_home_events',
        'description': 'Queries the home agent for events in the given home, such as those gathered by camera perception.',
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
def search_home_events(
    query: str, home_name: Optional[str] = None
) -> Dict[str, Any]:
    """Queries the home agent for events in the given home, such as those gathered by camera perception.

    Args:
        query (str): The query to pass to the Home Agent Bard Service
        home_name (Optional[str]): The home name which the query applies to

    Returns:
        Dict[str, Any]: A dictionary containing the result of the home events search.
            - search_home_events_response (str): The response from the Home Agent.
            - camera_clip_urls (List[str]): A list of camera clip URLs, if available.

    Raises:
        InvalidInputError: If the input parameters are invalid.
    """
    try:
        SearchHomeEventsParams(query=query, home_name=home_name)
    except ValidationError as e:
        raise InvalidInputError(f"Invalid input: {e}") from e

    # This is a simplified implementation. A real implementation would
    # need to call the Home Agent Bard Service to search for events.
    return SearchHomeEventsResult(
        search_home_events_response="Found 1 event.",
        camera_clip_urls=["https://example.com/clip1.mp4"],
    ).model_dump(mode="json")
