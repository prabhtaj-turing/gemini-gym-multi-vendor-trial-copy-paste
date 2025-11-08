from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Union, List, Optional
from generic_media.SimulationEngine.models import IntentType, FilteringType, MediaItem, MediaItemMetadata
from generic_media.SimulationEngine.db import DB
from generic_media.SimulationEngine.utils import search_media, resolve_media_uri
from datetime import datetime, timezone

@tool_spec(
    spec={
        'name': 'play',
        'description': 'Play songs, artists, albums, playlists or podcasts on a media provider.',
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Content that the user is looking for. Must be a non-empty string, even for generic types.'
                },
                'intent_type': {
                    'type': 'string',
                    'description': 'The type of content to play. One of: "ALBUM", "ARTIST", "GENERIC_MUSIC", "GENERIC_PODCAST", "GENERIC_MUSIC_NEW", "GENERIC_SOMETHING_ELSE", "LIKED_SONGS", "PERSONAL_PLAYLIST", "PODCAST_EPISODE", "PODCAST_SHOW", "PUBLIC_PLAYLIST", "TRACK".'
                },
                'filtering_type': {
                    'type': 'string',
                    'description': 'The type of content to filter by. One of: "ALBUM", "PLAYLIST", "TRACK". Defaults to None (no filtering applied).'
                }
            },
            'required': [
                'query',
                'intent_type'
            ]
        }
    }
)
def play(query: str, intent_type: str, filtering_type: Optional[str] = None) -> List[Dict[str, Union[Optional[str], Dict[str, Optional[str]]]]]:
    """
    Play songs, artists, albums, playlists or podcasts on a media provider.
    
    Also updates the recently_played list with the first played item and timestamp in ISO 8601 format ("2023-01-01T10:00:00Z").

    Args:
        query (str): Content that the user is looking for. Must be a non-empty string, even for generic types.
        intent_type (str): The type of content to play. One of: "ALBUM", "ARTIST", "GENERIC_MUSIC", "GENERIC_PODCAST", "GENERIC_MUSIC_NEW", "GENERIC_SOMETHING_ELSE", "LIKED_SONGS", "PERSONAL_PLAYLIST", "PODCAST_EPISODE", "PODCAST_SHOW", "PUBLIC_PLAYLIST", "TRACK".
        filtering_type (Optional[str]): The type of content to filter by. One of: "ALBUM", "PLAYLIST", "TRACK". Defaults to None (no filtering applied).

    Returns:
        List[Dict[str, Union[Optional[str], Dict[str, Optional[str]]]]]: A list of media items to be played. Each media item is a dictionary with the following keys:
            uri (str): The URI of the media item.
            media_item_metadata (Dict[str, Optional[str]]): Metadata about the media item.
                entity_title (Optional[str]): The title of the media item.
                container_title (Optional[str]): The title of the container of the media item (e.g., album or show).
                description (Optional[str]): A description of the media item.
                artist_name (Optional[str]): The name of the artist.
                content_type (Optional[str]): The type of content.
            provider (Optional[str]): The provider of the media item.
            action_card_content_passthrough (Optional[str]): The URI of the media item.

    Raises:
        ValueError: If the query is empty or if the intent_type or filtering_type are invalid.
    """
    # Input validation
    if not query:
        raise ValueError("Query cannot be empty.")

    try:
        intent = IntentType(intent_type)
    except ValueError:
        raise ValueError(f"Invalid intent_type: {intent_type}")

    if filtering_type:
        try:
            FilteringType(filtering_type)
        except ValueError:
            raise ValueError(f"Invalid filtering_type: {filtering_type}")

    media_item_dict = resolve_media_uri(query)
    if media_item_dict:
        uri = f"{media_item_dict.get('provider', 'generic')}:{media_item_dict.get('content_type', 'track').lower()}:{media_item_dict.get('id')}"
        container_title = None
        if media_item_dict.get("content_type") == "TRACK":
            container_title = media_item_dict.get("album_id")
        elif media_item_dict.get("content_type") == "PODCAST_EPISODE": # pragma: no cover
            container_title = media_item_dict.get("show_id")
            
        media_item = MediaItem(
            uri=uri,
            media_item_metadata=MediaItemMetadata(
                entity_title=media_item_dict.get("title"),
                artist_name=media_item_dict.get("artist_name"),
                content_type=media_item_dict.get("content_type"),
                container_title=container_title,
            ),
            provider=media_item_dict.get("provider", "generic"),
            action_card_content_passthrough=uri,
        )
        results = [media_item.model_dump(mode="json")]
    else:
        results = search_media(query, intent_type, filtering_type)

    if results:
        DB["recently_played"].append(
            {
                "uri": results[0]["uri"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    return results