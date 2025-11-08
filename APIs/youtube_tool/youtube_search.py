from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, List

from youtube_tool.SimulationEngine import utils, custom_errors

@tool_spec(
    spec={
        'name': 'search',
        'description': 'Search for videos, channels, or playlists on YouTube.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'The query with which search should be performed. Must be a non-empty string.'
                },
                'result_type': {
                    'type': 'string',
                    'description': 'Enum to specify search result type. Can be "VIDEO", "CHANNEL" or "PLAYLIST". Defaults to "VIDEO".'
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def search(
    query: str,
    result_type: Optional[str] = "VIDEO"
) -> List[Dict[str, Any]]:
    """
    Search for videos, channels, or playlists on YouTube.

    Args:
        query (str): The query with which search should be performed. Must be a non-empty string.
        result_type (Optional[str]): Enum to specify search result type. Can be "VIDEO", "CHANNEL" or "PLAYLIST". Defaults to "VIDEO".

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing search results.
        For result_type = "VIDEO" - List[Dict[str, Any]] with keys: 'channel_avatar_url', 'channel_external_id', 'channel_name', 'external_video_id', 'like_count', 'publish_date', 'search_query', 'search_url', Optional['snippets'], 'title', 'url', 'video_length', 'view_count'
        For result_type = "CHANNEL" - List[Dict[str, Any]] with keys: 'channel_avatar_url', 'channel_name', 'channel_external_id', 'search_query', 'search_url', Optional['snippets'], 'url'
        For result_type = "PLAYLIST" - List[Dict[str, Any]] with keys: 'channel_avatar_url', 'channel_external_id', 'channel_name', Optional['external_playlist_id'], Optional['playlist_name'], Optional['playlist_video_ids'], 'search_query', 'search_url', Optional['snippets'], 'url'
        TypeError: If query is not a string or other parameters are of incorrect types.
        ValueError: If query is an empty string or not provided
                    or if the result_type(if provided) is not one of the following: VIDEO, CHANNEL, PLAYLIST.
        APIError: If the search result is not found.
        ExtractionError: If the results are not found in the response.
        EnvironmentError: If the environment variables GOOGLE_API_KEY or GEMINI_API_KEY or LIVE_API_URL are not set.
    """
    # Input type validation
    if query is None:
        raise ValueError("query is required.")
    if not isinstance(query, str):
        raise TypeError("query must be a string.")
    
    # Input value validation
    if not query.strip():
        raise ValueError("query cannot be empty.")
    
    if not isinstance(result_type, str):
        raise TypeError("result_type must be a string.")
    if result_type not in ["VIDEO", "CHANNEL", "PLAYLIST"]:
        raise ValueError("result_type must be one of: VIDEO, CHANNEL, PLAYLIST.")
    result_type = result_type.lower()

    user_input = f"""Use @YouTube to search exactly this query for {result_type}s only, do not alter it: '{query}'"""

    try:    
        search_result = utils.get_gemini_response(user_input)
    except custom_errors.EnvironmentError as e:
        raise custom_errors.EnvironmentError(f"Environment error: {e}")
    if search_result is None:
        raise custom_errors.APIError("Failed to get search result.")
    results = utils.get_json_response(search_result)
    if results is None or results==[]:
        raise custom_errors.ExtractionError("Failed to extract results.")
    utils.add_recent_search(endpoint="search", parameters={"query": query, "result_type": result_type}, result=results)
    return results
