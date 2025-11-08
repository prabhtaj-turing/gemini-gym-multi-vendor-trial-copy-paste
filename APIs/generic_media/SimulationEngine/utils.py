from typing import List, Dict, Optional, Union, Any
from generic_media.SimulationEngine.db import DB
from generic_media.SimulationEngine.models import IntentType, MediaItem, MediaItemMetadata
from generic_media.SimulationEngine.search_engine import search_engine_manager
import re
from datetime import datetime, timezone
from generic_media.SimulationEngine import models

def validate_datetime_string(datetime_str: str, field_name: str = "datetime") -> datetime:
    """
    Validates and parses a datetime string to a datetime object.
    
    Expected formats:
    - ISO 8601 datetime: "2023-01-01T10:00:00Z" or "2023-01-01T10:00:00"
    - Simple time: "10:00", "10:05", "23:59" (assumes current date)
    
    Args:
        datetime_str (str): The datetime string to validate and parse (ISO 8601 format: "2023-01-01T10:00:00Z").
        field_name (str): The name of the field being validated (for error messages).
        
    Returns:
        datetime: The parsed datetime object.
        
    Raises:
        ValueError: If the datetime string is invalid or cannot be parsed.
    """
    if not isinstance(datetime_str, str):
        raise ValueError(f"{field_name} must be a string, got {type(datetime_str).__name__}")

    if not datetime_str.strip():
        raise ValueError(f"{field_name} cannot be empty or whitespace only")

    # Try parsing as simple time format first (HH:MM or HH:MM:SS)
    if ':' in datetime_str and 'T' not in datetime_str and '-' not in datetime_str:
        try:
            # Handle simple time formats like "10:00" or "10:00:00"
            time_parts = datetime_str.split(':')
            if len(time_parts) == 2:  # HH:MM
                hour, minute = int(time_parts[0]), int(time_parts[1])
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    # Create datetime with current date and specified time
                    from datetime import date, time
                    today = date.today()
                    return datetime.combine(today, time(hour=hour, minute=minute))
            elif len(time_parts) == 3:  # HH:MM:SS
                hour, minute, second = int(time_parts[0]), int(time_parts[1]), int(time_parts[2])
                if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
                    # Create datetime with current date and specified time
                    from datetime import date, time
                    today = date.today()
                    return datetime.combine(today, time(hour=hour, minute=minute, second=second))
        except (ValueError, IndexError):
            pass  # Fall through to ISO 8601 parsing

    # Try parsing ISO 8601 format
    try:
        # Handle both with and without timezone info
        if datetime_str.endswith('Z'):
            # UTC timezone
            dt = datetime.fromisoformat(datetime_str[:-1].replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(datetime_str)
        return dt
    except ValueError as e:
        raise ValueError(f"Invalid {field_name} format. Expected ISO 8601 format (e.g., '2023-01-01T10:00:00Z' or '2023-01-01T10:00:00') or simple time format (e.g., '10:00'). Error: {str(e)}")

    # If we get here, the format is not recognized
    raise ValueError(f"Invalid {field_name} format. Expected ISO 8601 format (e.g., '2023-01-01T10:00:00Z' or '2023-01-01T10:00:00') or simple time format (e.g., '10:00'). Got: {datetime_str}")

def resolve_media_uri(uri: str) -> Optional[Dict[str, Union[Optional[str], bool, int]]]:
    """Resolves a media URI and returns the corresponding item from the database if it exists.

    A valid URI is a string in the format "provider:content_type:id".

    Args:
        uri (str): The URI to resolve and look up.

    Returns:
        Optional[Dict[str, Union[Optional[str], bool, int]]]: The media item from the database if the URI is valid and the item exists, otherwise None.
            The returned dictionary for a track will have the following structure:
                - id (str): The ID of the track.
                - title (str): The title of the track.
                - artist_name (str): The name of the artist.
                - album_id (Optional[str]): The ID of the album the track belongs to, or None.
                - rank (int): The popularity rank of the track.
                - release_timestamp (str): The ISO 8601 timestamp of the track's release.
                - is_liked (bool): True if the user has liked the track, otherwise False.
                - provider (str): The name of the content provider (e.g., 'spotify', 'youtube_music').
                - content_type (str): The type of media, which is 'TRACK' for tracks.
    """
    if not re.match(r"\w+:\w+:\w+", uri):
        return None

    provider, content_type, item_id = uri.split(":")
    
    db_key = f"{content_type.lower()}s"
    if db_key == "podcast_episodes":
        for podcast in DB["podcasts"]:
            for episode in podcast["episodes"]:
                if episode["id"] == item_id and episode["provider"] == provider:
                    return episode
    elif db_key not in DB:
        return None
    else:
        for item in DB[db_key]:
            if item["id"] == item_id and item["provider"] == provider:
                return item
    
    return None

def search_media(query: str, intent_type: str, filtering_type: Optional[str] = None) -> List[Dict[str, Union[Optional[str], Dict[str, Optional[str]]]]]:
    """Searches for media in the database using the search engine.

    Args:
        query (str): The search query.
        intent_type (str): The type of content to search for. Possible values are:
            "ALBUM", "ARTIST", "GENERIC_MUSIC", "GENERIC_PODCAST", "GENERIC_MUSIC_NEW",
            "GENERIC_SOMETHING_ELSE", "LIKED_SONGS", "PERSONAL_PLAYLIST", "PODCAST_EPISODE",
            "PODCAST_SHOW", "PUBLIC_PLAYLIST", "TRACK".
        filtering_type (Optional[str]): The type of content to filter by. Possible values are:
            "ALBUM", "PLAYLIST", "TRACK".

    Returns:
        List[Dict[str, Union[Optional[str], Dict[str, Optional[str]]]]]: A list of media items that match the search query. Each media item is a dictionary with the following structure:
            - uri (str): The unique resource identifier for the media item.
            - media_item_metadata (Dict[str, Optional[str]]): Metadata about the media item.
                - entity_title (Optional[str]): The title of the media item (e.g., song title, playlist name).
                - container_title (Optional[str]): The title of the container of the media item (e.g., album name for a track, show name for a podcast episode).
                - description (Optional[str]): A short description of the media item.
                - artist_name (Optional[str]): The name of the artist associated with the media item.
                - content_type (Optional[str]): The type of the media item (e.g., "TRACK", "ALBUM").
            - provider (Optional[str]): The name of the content provider (e.g., "spotify").
            - action_card_content_passthrough (Optional[str]): A passthrough string that can be used for actions.
    """
    engine = search_engine_manager.get_engine()
    
    search_kwargs = {"filter": {}}
    if intent_type == IntentType.LIKED_SONGS:
        search_kwargs["filter"].update({"is_liked": "True", "content_type": "TRACK"})
    elif intent_type == IntentType.PERSONAL_PLAYLIST:
        search_kwargs["filter"].update({"is_personal": "True", "content_type": "PLAYLIST"})
    
    if filtering_type:
        search_kwargs["filter"]["content_type"] = filtering_type
    elif "content_type" not in search_kwargs["filter"]:
        if intent_type not in [IntentType.LIKED_SONGS, IntentType.PERSONAL_PLAYLIST, IntentType.GENERIC_MUSIC, IntentType.GENERIC_PODCAST, IntentType.GENERIC_MUSIC_NEW]:
            search_kwargs["filter"]["content_type"] = intent_type

    if intent_type == IntentType.GENERIC_MUSIC:
        results = engine.search(query, **search_kwargs)
    elif intent_type == IntentType.GENERIC_PODCAST:
        results = engine.search(query, **search_kwargs)
    elif intent_type == IntentType.GENERIC_MUSIC_NEW:
        results = engine.search(query, **search_kwargs)
    else:
        results = engine.search(query, **search_kwargs)

    media_items = []
    for result in results:
        item = result
        uri = f"{item.get('provider', 'generic')}:{item.get('content_type', 'track').lower()}:{item.get('id')}"
        
        container_title = None
        if item.get("content_type") == "TRACK":
            container_title = item.get("album_id")
        elif item.get("content_type") == "PODCAST_EPISODE":
            container_title = item.get("show_id")

        entity_title = item.get("title")
        if item.get("content_type") in ["ARTIST", "PLAYLIST"]:
            entity_title = item.get("name")

        media_item = MediaItem(
            uri=uri,
            media_item_metadata=MediaItemMetadata(
                entity_title=entity_title,
                artist_name=item.get("artist_name"),
                content_type=item.get("content_type"),
                container_title=container_title,
            ),
            provider=item.get("provider", "generic"),
            action_card_content_passthrough=uri,
        )
        media_items.append(media_item.model_dump(mode="json"))

    return media_items

def get_db_state() -> Dict[str, Any]:
    """
    Retrieves the current state of the database.

    Returns:
        Dict[str, Any]: A dictionary representing the database's state.
            - providers (List[Dict[str, Optional[str]]]): A list of providers.
                - name (str): The name of the provider.
                - base_url (str): The base URL of the provider.
            - actions (List[Dict[str, Optional[str]]]): A list of actions.
                - action_type (str): The type of action. Can be 'play' or 'search'.
                - inputs (Dict[str, Optional[str]]): The inputs to the action.
                - outputs (List[Dict[str, Optional[str]]]): The outputs of the action.
                - timestamp (str): The timestamp of the action (ISO 8601 format: "2023-01-01T10:00:00Z").
            - tracks (List[Dict[str, Optional[str]]]): A list of tracks.
                - id (str): The ID of the track.
                - title (str): The title of the track.
                - artist_name (str): The name of the artist.
                - album_id (Optional[str]): The ID of the album, or None.
                - rank (int): The rank of the track.
                - release_timestamp (str): The release timestamp of the track (ISO 8601 format: "2023-01-01T10:00:00Z").
                - is_liked (bool): Whether the track is liked.
                - provider (str): The provider of the track.
                - content_type (str): The type of content.
            - albums (List[Dict[str, Optional[str]]]): A list of albums.
                - id (str): The ID of the album.
                - title (str): The title of the album.
                - artist_name (str): The name of the artist.
                - track_ids (List[str]): A list of track IDs in the album.
                - provider (str): The provider of the album.
                - content_type (str): The type of content.
            - artists (List[Dict[str, Optional[str]]]): A list of artists.
                - id (str): The ID of the artist.
                - name (str): The name of the artist.
                - provider (str): The provider of the artist.
                - content_type (str): The type of content.
            - playlists (List[Dict[str, Optional[str]]]): A list of playlists.
                - id (str): The ID of the playlist.
                - name (str): The name of the playlist.
                - track_ids (List[str]): A list of track IDs in the playlist.
                - is_personal (bool): Whether the playlist is personal.
                - provider (str): The provider of the playlist.
                - content_type (str): The type of content.
            - podcasts (List[Dict[str, Optional[str]]]): A list of podcast shows.
                - id (str): The ID of the podcast show.
                - title (str): The title of the podcast show.
                - episodes (List[Dict[str, Optional[str]]]): A list of podcast episodes.
                    - id (str): The ID of the podcast episode.
                    - title (str): The title of the podcast episode.
                    - show_id (str): The ID of the show.
                    - provider (str): The provider of the podcast episode.
                    - content_type (str): The type of content.
                - provider (str): The provider of the podcast show.
                - content_type (str): The type of content.
            - recently_played (List[Dict[str, str]]): A list of recently played items with timestamp in ISO 8601 format ("2023-01-01T10:00:00Z").
    """
    return DB

def update_db_state(partial_state: Dict[str, Any]):
    """
    Updates the state of the database with a partial state.

    Args:
        partial_state (Dict[str, Any]): A dictionary containing the fields to update.
            Each key should correspond to a top-level field of the database state.
    """
    # Validate timestamps in recently_played if present
    if 'recently_played' in partial_state:
        recently_played = partial_state['recently_played']
        if isinstance(recently_played, list):
            for item in recently_played:
                if isinstance(item, dict) and 'timestamp' in item:
                    validate_datetime_string(item['timestamp'], 'timestamp')

    DB.update(partial_state)

def _generic_get(resource_type: str, resource_id: str) -> Optional[Dict[str, Any]]:
    """
    Generic internal function to get a resource by its ID.

    Args:
        resource_type (str): The plural name of the resource type (e.g., 'tracks', 'albums').
        resource_id (str): The ID of the resource to retrieve.

    Returns:
        Optional[Dict[str, Any]]: The resource dictionary if found, otherwise None.
    """
    resources = DB.get(resource_type, [])
    for resource in resources:
        if resource.get("id") == resource_id:
            return resource
    return None

def _generic_create(resource_type: str, resource_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic internal function to create a new resource.

    Args:
        resource_type (str): The plural name of the resource type (e.g., 'tracks', 'albums').
        resource_data (Dict[str, Union[str, int, bool, List[str], List[Dict[str, str]], None]]): The dictionary containing the data for the new resource. Must include an 'id'.

    Returns:
        Dict[str, Any]: The created resource dictionary.

    Raises:
        ValueError: If `resource_data` does not contain an 'id' field, or if a resource with the given id already exists.
    """
    if 'id' not in resource_data:
        raise ValueError("Resource data must contain an 'id' field.")
    
    resources = DB.get(resource_type, [])
    if any(r.get("id") == resource_data['id'] for r in resources):
        raise ValueError(f"Resource with id {resource_data['id']} already exists in {resource_type}.")

    resources.append(resource_data)
    DB[resource_type] = resources
    return resource_data

def _generic_update(resource_type: str, resource_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Generic internal function to update a resource by its ID.

    Args:
        resource_type (str): The plural name of the resource type (e.g., 'tracks', 'albums').
        resource_id (str): The ID of the resource to update.
        update_data (Dict[str, Any]): A dictionary with the fields to update.

    Returns:
        Optional[Dict[str, Any]]: The updated resource dictionary if found, otherwise None.
    """
    resources = DB.get(resource_type, [])
    for resource in resources:
        if resource.get("id") == resource_id:
            resource.update(update_data)
            return resource
    return None

def _generic_delete(resource_type: str, resource_id: str) -> bool:
    """
    Generic internal function to delete a resource by its ID.

    Args:
        resource_type (str): The plural name of the resource type (e.g., 'tracks', 'albums').
        resource_id (str): The ID of the resource to delete.

    Returns:
        bool: True if the resource was successfully deleted, False otherwise.
    """
    resources = DB.get(resource_type, [])
    resource_to_delete = None
    for resource in resources:
        if resource.get("id") == resource_id:
            resource_to_delete = resource
            break
    
    if resource_to_delete:
        resources.remove(resource_to_delete)
        DB[resource_type] = resources
        return True
    
    return False

# CRUD for Tracks
def get_track(track_id: str) -> Optional[Dict[str, Union[Optional[str], int, bool]]]:
    """
    Retrieves a single track by its ID.

    Args:
        track_id (str): The ID of the track to retrieve.

    Returns:
        Optional[Dict[str, Union[Optional[str], int, bool]]]: A dictionary representing the track, or None if not found.
            The track dictionary has the following structure:
                - id (str): The ID of the track.
                - title (str): The title of the track.
                - artist_name (str): The name of the artist.
                - album_id (Optional[str]): The ID of the album the track belongs to, or None.
                - rank (int): The popularity rank of the track.
                - release_timestamp (str): The ISO 8601 timestamp of the track's release.
                - is_liked (bool): True if the user has liked the track, otherwise False.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('TRACK').
    """
    return _generic_get("tracks", track_id)

def create_track(track_data: Dict[str, Union[Optional[str], bool, int]]) -> Dict[str, Union[Optional[str], bool, int]]:
    """
    Creates a new track.

    Args:
        track_data (Dict[str, Union[Optional[str], bool, int]]): A dictionary containing the track's data.
            The dictionary should have the following structure:
                - title (str): The title of the track.
                - artist_name (str): The name of the artist.
                - album_id (Optional[str]): The ID of the album the track belongs to, or None.
                - rank (int): The popularity rank of the track.
                - release_timestamp (str): The ISO 8601 timestamp of the track's release.
                - is_liked (bool): True if the user has liked the track, otherwise False.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('TRACK').

    Returns:
        Dict[str, Union[Optional[str], bool, int]]: The dictionary of the created track.
            The track dictionary has the following structure:
                - id (str): The ID of the track.
                - title (str): The title of the track.
                - artist_name (str): The name of the artist.
                - album_id (Optional[str]): The ID of the album the track belongs to, or None.
                - rank (int): The popularity rank of the track.
                - release_timestamp (str): The ISO 8601 timestamp of the track's release.
                - is_liked (bool): True if the user has liked the track, otherwise False.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('TRACK').
    """
    # Validate release_timestamp if present
    if 'release_timestamp' in track_data and track_data['release_timestamp'] is not None:
        validate_datetime_string(track_data['release_timestamp'], 'release_timestamp')
    
    track_data.pop('id', None)
    new_track_model = models.Track(**track_data)
    track_dict = new_track_model.model_dump(mode="json")
    return _generic_create("tracks", track_dict)

def update_track(track_id: str, update_data: Dict[str, Union[Optional[str], bool]]) -> Optional[Dict[str, Union[Optional[str], int, bool]]]:
    """
    Updates an existing track.

    Args:
        track_id (str): The ID of the track to update.
        update_data (Dict[str, Union[Optional[str], bool]]): A dictionary with the fields to update.
            - title (Optional[str]): The new title for the track.
            - artist_name (Optional[str]): The new artist name for the track.
            - album_id (Optional[str]): The new album ID for the track.
            - rank (Optional[str]): The new rank for the track.
            - release_timestamp (Optional[str]): The new release timestamp (ISO 8601 format).
            - is_liked (Optional[bool]): The new liked status.
            - provider (Optional[str]): The new provider name.

    Returns:
        Optional[Dict[str, Union[Optional[str], int, bool]]]: The updated track dictionary, or None if the track was not found.
            The track dictionary has the following structure:
                - id (str): The ID of the track.
                - title (str): The title of the track.
                - artist_name (str): The name of the artist.
                - album_id (Optional[str]): The ID of the album the track belongs to, or None.
                - rank (int): The popularity rank of the track.
                - release_timestamp (str): The ISO 8601 timestamp of the track's release.
                - is_liked (bool): True if the user has liked the track, otherwise False.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('TRACK').
    """
    # Validate release_timestamp if present in update data
    if 'release_timestamp' in update_data and update_data['release_timestamp'] is not None:
        validate_datetime_string(update_data['release_timestamp'], 'release_timestamp')
    
    return _generic_update("tracks", track_id, update_data)

def delete_track(track_id: str) -> bool:
    """
    Deletes a track by its ID.

    Args:
        track_id (str): The ID of the track to delete.

    Returns:
        bool: True if the track was deleted, False otherwise.
    """
    return _generic_delete("tracks", track_id)

# CRUD for Albums
def get_album(album_id: str) -> Optional[Dict[str, Union[str, List[str]]]]:
    """
    Retrieves a single album by its ID.

    Args:
        album_id (str): The ID of the album to retrieve.

    Returns:
        Optional[Dict[str, Union[str, List[str]]]]: A dictionary representing the album, or None if not found.
            The album dictionary has the following structure:
                - id (str): The ID of the album.
                - title (str): The title of the album.
                - artist_name (str): The name of the artist.
                - track_ids (List[str]): A list of track IDs in the album.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('ALBUM').
    """
    return _generic_get("albums", album_id)

def create_album(album_data: Dict[str, Union[str, List[str]]]) -> Dict[str, Union[str, List[str]]]:
    """
    Creates a new album.

    Args:
        album_data (Dict[str, Union[str, List[str]]]): A dictionary containing the album's data.
            The dictionary should have the following structure:
                - title (str): The title of the album.
                - artist_name (str): The name of the artist.
                - track_ids (List[str]): A list of track IDs in the album.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('ALBUM').

    Returns:
        Dict[str, Union[str, List[str]]]: The dictionary of the created album.
            The album dictionary has the following structure:
                - id (str): The ID of the album.
                - title (str): The title of the album.
                - artist_name (str): The name of the artist.
                - track_ids (List[str]): A list of track IDs in the album.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('ALBUM').
    """
    album_data.pop('id', None)
    new_album_model = models.Album(**album_data)
    album_dict = new_album_model.model_dump(mode="json")
    return _generic_create("albums", album_dict)

def update_album(album_id: str, update_data: Dict[str, Union[Optional[str], Optional[List[str]]]]) -> Optional[Dict[str, Union[str, List[str]]]]:
    """
    Updates an existing album.

    Args:
        album_id (str): The ID of the album to update.
        update_data (Dict[str, Union[Optional[str], Optional[List[str]]]]): A dictionary with the fields to update.
            - title (Optional[str]): The new title for the album.
            - artist_name (Optional[str]): The new artist name for the album.
            - track_ids (Optional[List[str]]): The new list of track IDs for the album.
            - provider (Optional[str]): The new provider name.

    Returns:
        Optional[Dict[str, Union[str, List[str]]]]: The updated album dictionary, or None if the album was not found.
            The album dictionary has the following structure:
                - id (str): The ID of the album.
                - title (str): The title of the album.
                - artist_name (str): The name of the artist.
                - track_ids (List[str]): A list of track IDs in the album.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('ALBUM').
    """
    return _generic_update("albums", album_id, update_data)

def delete_album(album_id: str) -> bool:
    """
    Deletes an album by its ID.

    Args:
        album_id (str): The ID of the album to delete.

    Returns:
        bool: True if the album was deleted, False otherwise.
    """
    return _generic_delete("albums", album_id)

# CRUD for Artists
def get_artist(artist_id: str) -> Optional[Dict[str, str]]:
    """
    Retrieves a single artist by their ID.

    Args:
        artist_id (str): The ID of the artist to retrieve.

    Returns:
        Optional[Dict[str, str]]: A dictionary representing the artist, or None if not found.
            The artist dictionary has the following structure:
                - id (str): The ID of the artist.
                - name (str): The name of the artist.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('ARTIST').
    """
    return _generic_get("artists", artist_id)

def create_artist(artist_data: Dict[str, str]) -> Dict[str, str]:
    """
    Creates a new artist.

    Args:
        artist_data (Dict[str, str]): A dictionary containing the artist's data.
            The dictionary should have the following structure:
                - name (str): The name of the artist.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('ARTIST').

    Returns:
        Dict[str, str]: The dictionary of the created artist.
            The artist dictionary has the following structure:
                - id (str): The ID of the artist.
                - name (str): The name of the artist.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('ARTIST').
    """
    artist_data.pop('id', None)
    new_artist_model = models.Artist(**artist_data)
    artist_dict = new_artist_model.model_dump(mode="json")
    return _generic_create("artists", artist_dict)

def update_artist(artist_id: str, update_data: Dict[str, Union[Optional[str]]]) -> Optional[Dict[str, str]]:
    """
    Updates an existing artist.

    Args:
        artist_id (str): The ID of the artist to update.
        update_data (Dict[str, Union[Optional[str]]]): A dictionary with the fields to update.
            - name (Optional[str]): The new name for the artist.
            - provider (Optional[str]): The new provider name.

    Returns:
        Optional[Dict[str, str]]: The updated artist dictionary, or None if the artist was not found.
            The artist dictionary has the following structure:
                - id (str): The ID of the artist.
                - name (str): The name of the artist.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('ARTIST').
    """
    return _generic_update("artists", artist_id, update_data)

def delete_artist(artist_id: str) -> bool:
    """
    Deletes an artist by their ID.

    Args:
        artist_id (str): The ID of the artist to delete.

    Returns:
        bool: True if the artist was deleted, False otherwise.
    """
    return _generic_delete("artists", artist_id)

# CRUD for Playlists
def get_playlist(playlist_id: str) -> Optional[Dict[str, Union[str, List[str], bool]]]:
    """
    Retrieves a single playlist by its ID.

    Args:
        playlist_id (str): The ID of the playlist to retrieve.

    Returns:
        Optional[Dict[str, Union[str, List[str], bool]]]: A dictionary representing the playlist, or None if not found.
            The playlist dictionary has the following structure:
                - id (str): The ID of the playlist.
                - name (str): The name of the playlist.
                - track_ids (List[str]): A list of track IDs in the playlist.
                - is_personal (bool): True if the playlist is a personal playlist.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('PLAYLIST').
    """
    return _generic_get("playlists", playlist_id)

def create_playlist(playlist_data: Dict[str, Union[str, List[str], bool]]) -> Dict[str, Union[str, List[str], bool]]:
    """
    Creates a new playlist.

    Args:
        playlist_data (Dict[str, Union[str, List[str], bool]]): A dictionary containing the playlist's data.
            The dictionary should have the following structure:
                - name (str): The name of the playlist.
                - track_ids (List[str]): A list of track IDs in the playlist.
                - is_personal (bool): True if the playlist is a personal playlist.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('PLAYLIST').

    Returns:
        Dict[str, Union[str, List[str], bool]]: The dictionary of the created playlist.
            The playlist dictionary has the following structure:
                - id (str): The ID of the playlist.
                - name (str): The name of the playlist.
                - track_ids (List[str]): A list of track IDs in the playlist.
                - is_personal (bool): True if the playlist is a personal playlist.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('PLAYLIST').
    """
    playlist_data.pop('id', None)
    new_playlist_model = models.Playlist(**playlist_data)
    playlist_dict = new_playlist_model.model_dump(mode="json")
    return _generic_create("playlists", playlist_dict)

def update_playlist(playlist_id: str, update_data: Dict[str, Optional[Union[Optional[str], Optional[List[str]], Optional[bool]]]]) -> Optional[Dict[str, Union[str, List[str], bool]]]:
    """
    Updates an existing playlist.

    Args:
        playlist_id (str): The ID of the playlist to update.
        update_data (Dict[str, Optional[Union[Optional[str], Optional[List[str]], Optional[bool]]]]): A dictionary with the fields to update.
            - name (Optional[str]): The new name for the playlist.
            - track_ids (Optional[List[str]]): The new list of track IDs.
            - is_personal (Optional[bool]): The new personal status.
            - provider (Optional[str]): The new provider name.

    Returns:
        Optional[Dict[str, Union[str, List[str], bool]]]: The updated playlist dictionary, or None if the playlist was not found.
            The playlist dictionary has the following structure:
                - id (str): The ID of the playlist.
                - name (str): The name of the playlist.
                - track_ids (List[str]): A list of track IDs in the playlist.
                - is_personal (bool): True if the playlist is a personal playlist.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('PLAYLIST').
    """
    return _generic_update("playlists", playlist_id, update_data)

def delete_playlist(playlist_id: str) -> bool:
    """
    Deletes a playlist by its ID.

    Args:
        playlist_id (str): The ID of the playlist to delete.

    Returns:
        bool: True if the playlist was deleted, False otherwise.
    """
    return _generic_delete("playlists", playlist_id)

# CRUD for Podcasts (PodcastShows)
def get_podcast(podcast_id: str) -> Optional[Dict[str, Union[str, List[Dict[str, str]]]]]:
    """
    Retrieves a single podcast show by its ID.

    Args:
        podcast_id (str): The ID of the podcast show to retrieve.

    Returns:
        Optional[Dict[str, Union[str, List[Dict[str, str]]]]]: A dictionary representing the podcast show, or None if not found.
            The podcast show dictionary has the following structure:
                - id (str): The ID of the podcast show.
                - title (str): The title of the podcast show.
                - episodes (List[Dict[str, str]]): A list of podcast episodes.
                    - id (str): The ID of the podcast episode.
                    - title (str): The title of the podcast episode.
                    - show_id (str): The ID of the show this episode belongs to.
                    - provider (str): The name of the content provider.
                    - content_type (str): The type of media ('PODCAST_EPISODE').
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('PODCAST_SHOW').
    """
    return _generic_get("podcasts", podcast_id)

def create_podcast(podcast_data: Dict[str, Union[str, List[Dict[str, str]]]]) -> Dict[str, Union[str, List[Dict[str, str]]]]:
    """
    Creates a new podcast show.

    Args:
        podcast_data (Dict[str, Union[str, List[Dict[str, str]]]]): A dictionary containing the podcast show's data.
            The dictionary should have the following structure:
                - title (str): The title of the podcast show.
                - episodes (List[Dict[str, str]]): A list of podcast episodes.
                    Each episode dictionary should have the following structure:
                    - title (str): The title of the podcast episode.
                    - show_id (str): The ID of the show this episode belongs to.
                    - provider (str): The name of the content provider.
                    - content_type (str): The type of media ('PODCAST_EPISODE').
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('PODCAST_SHOW').

    Returns:
        Dict[str, Union[str, List[Dict[str, str]]]]: The dictionary of the created podcast show.
            The podcast show dictionary has the following structure:
                - id (str): The ID of the podcast show.
                - title (str): The title of the podcast show.
                - episodes (List[Dict[str, str]]): A list of podcast episodes.
                    - id (str): The ID of the podcast episode.
                    - title (str): The title of the podcast episode.
                    - show_id (str): The ID of the show this episode belongs to.
                    - provider (str): The name of the content provider.
                    - content_type (str): The type of media ('PODCAST_EPISODE').
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('PODCAST_SHOW').
    """
    podcast_data.pop('id', None)
    new_podcast_model = models.PodcastShow(**podcast_data)
    podcast_dict = new_podcast_model.model_dump(mode="json")
    return _generic_create("podcasts", podcast_dict)

def update_podcast(podcast_id: str, update_data: Dict[str, Optional[Union[Optional[str], Optional[List[Dict[str, str]]]]]]) ->Optional[Dict[str, Union[str, List[Dict[str, str]]]]]:
    """
    Updates an existing podcast show.

    Args:
        podcast_id (str): The ID of the podcast show to update.
        update_data (Dict[str, Optional[Union[Optional[str], Optional[List[Dict[str, str]]]]]]): A dictionary with the fields to update.
            - title (Optional[str]): The new title of the podcast show.
            - episodes (Optional[List[Dict[str, str]]]): The new list of episodes.
                Each episode dictionary should have the following structure:
                - id (str): The ID of the podcast episode.
                - title (str): The title of the podcast episode.
                - show_id (str): The ID of the show this episode belongs to.
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('PODCAST_EPISODE').
            - provider (Optional[str]): The new provider name.

    Returns:
        Optional[Dict[str, Union[str, List[Dict[str, str]]]]]: The updated podcast show dictionary, or None if not found.
            The podcast show dictionary has the following structure:
                - id (str): The ID of the podcast show.
                - title (str): The title of the podcast show.
                - episodes (List[Dict[str, str]]): A list of podcast episodes.
                    - id (str): The ID of the podcast episode.
                    - title (str): The title of the podcast episode.
                    - show_id (str): The ID of the show this episode belongs to.
                    - provider (str): The name of the content provider.
                    - content_type (str): The type of media ('PODCAST_EPISODE').
                - provider (str): The name of the content provider.
                - content_type (str): The type of media ('PODCAST_SHOW').
    """
    return _generic_update("podcasts", podcast_id, update_data)

def delete_podcast(podcast_id: str) -> bool:
    """
    Deletes a podcast show by its ID.

    Args:
        podcast_id (str): The ID of the podcast show to delete.

    Returns:
        bool: True if the podcast show was deleted, False otherwise.
    """
    return _generic_delete("podcasts", podcast_id)

# CRUD for Providers
def get_provider(provider_name: str) -> Optional[Dict[str, str]]:
    """
    Retrieves a single provider by its name.

    Args:
        provider_name (str): The name of the provider to retrieve.

    Returns:
        Optional[Dict[str, str]]: A dictionary representing the provider, or None if not found.
            The provider dictionary has the following structure:
                - name (str): The name of the provider.
                - base_url (str): The base URL for the provider's 
    """
    providers = DB.get("providers", [])
    for provider in providers:
        if provider.get("name") == provider_name:
            return provider
    return None

def create_provider(provider_data: Dict[str, str]) -> Dict[str, str]:
    """
    Creates a new provider.

    Args:
        provider_data (Dict[str, str]): A dictionary containing the provider's data.
            The dictionary should have the following structure:
                - name (str): The name of the provider.
                - base_url (str): The base URL for the provider's 

    Returns:
        Dict[str, str]: The dictionary of the created provider.
            The provider dictionary has the following structure:
                - name (str): The name of the provider.
                - base_url (str): The base URL for the provider's 

    Raises:
        ValueError: If `provider_data` does not contain a 'name' field, or if a provider with the given name already exists.
    """
    if 'name' not in provider_data:
        raise ValueError("Provider data must contain a 'name' field.")
    
    providers = DB.get("providers", [])
    if any(p.get("name") == provider_data['name'] for p in providers):
        raise ValueError(f"Provider with name {provider_data['name']} already exists.")

    providers.append(provider_data)
    DB["providers"] = providers
    return provider_data

def update_provider(provider_name: str, update_data: Dict[str, Optional[str]]) -> Optional[Dict[str, str]]:
    """
    Updates an existing provider.

    Args:
        provider_name (str): The name of the provider to update.
        update_data (Dict[str, Optional[str]]): A dictionary with the fields to update.
            - base_url (Optional[str]): The new base URL for the provider.

    Returns:
        Optional[Dict[str, str]]: The updated provider dictionary, or None if the provider was not found.
            The provider dictionary has the following structure:
                - name (str): The name of the provider.
                - base_url (str): The base URL for the provider's 
    """
    providers = DB.get("providers", [])
    for provider in providers:
        if provider.get("name") == provider_name:
            provider.update(update_data)
            return provider
    return None

def delete_provider(provider_name: str) -> bool:
    """
    Deletes a provider by its name.

    Args:
        provider_name (str): The name of the provider to delete.

    Returns:
        bool: True if the provider was deleted, False otherwise.
    """
    providers = DB.get("providers", [])
    provider_to_delete = None
    for provider in providers:
        if provider.get("name") == provider_name:
            provider_to_delete = provider
            break
    
    if provider_to_delete:
        providers.remove(provider_to_delete)
        DB["providers"] = providers
        return True
    
    return False
