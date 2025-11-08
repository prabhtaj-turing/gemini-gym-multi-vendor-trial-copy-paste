from common_utils.tool_spec_decorator import tool_spec
import re
import uuid
import base64

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from .SimulationEngine.db import DB
from .SimulationEngine import custom_errors, utils
from .SimulationEngine.models import SpotifyPlaylistTrack, SpotifyUserSimple


@tool_spec(
    spec={
        'name': 'add_items_to_playlist',
        'description': """ Add one or more items (tracks or episodes) to a user's playlist.
        
        This endpoint allows you to add tracks or episodes to an existing playlist. 
        You can specify the position at which to insert the new items, or append them 
        to the end. The function validates input, updates the playlist's track list, 
        and generates a new snapshot ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'playlist_id': {
                    'type': 'string',
                    'description': "The Spotify ID for the playlist. Example: 'QDyH69WryQ7dPRXVOFmy2V'."
                },
                'uris': {
                    'type': 'array',
                    'description': """ List of Spotify track or episode URIs to add. 
                    Each must be a valid URI of the form 'spotify:track:<id>' or 'spotify:episode:<id>'. 
                    Maximum 100 items per request.
                    Example: ['spotify:track:4iV5W9uYEdYUVa79Axb7Rh', 'spotify:episode:518j5o704s0mygKUv9aJL4'] """,
                    'items': {
                        'type': 'string'
                    }
                },
                'position': {
                    'type': 'integer',
                    'description': 'The position to insert the items (0-based). If omitted, items are appended to the end.'
                }
            },
            'required': [
                'playlist_id',
                'uris'
            ]
        }
    }
)
def add_items_to_playlist(
    playlist_id: str,
    uris: List[str],
    position: Optional[int] = None
) -> Dict[str, Any]:
    """
    Add one or more items (tracks or episodes) to a user's playlist.

    This endpoint allows you to add tracks or episodes to an existing playlist. 
    You can specify the position at which to insert the new items, or append them 
    to the end. The function validates input, updates the playlist's track list, 
    and generates a new snapshot ID.

    Args:
        playlist_id (str): The Spotify ID for the playlist. Example: 'QDyH69WryQ7dPRXVOFmy2V'.
        uris (List[str]): List of Spotify track or episode URIs to add. 
                          Each must be a valid URI of the form 'spotify:track:<id>' or 'spotify:episode:<id>'. 
                          Maximum 100 items per request.
                          Example: ['spotify:track:4iV5W9uYEdYUVa79Axb7Rh', 'spotify:episode:518j5o704s0mygKUv9aJL4']
        position (Optional[int]): The position to insert the items (0-based). If omitted, items are appended to the end.

    Returns:
        Dict[str, Any]: Dictionary with the new snapshot ID, e.g. {"snapshot_id": str}.

    Raises:
        InvalidInputError: If input is invalid (bad playlist_id, uris, or position).
        NoResultsFoundError: If the playlist, track, or episode does not exist.
        AuthenticationError: If the current user is not authenticated.
    """
    # Validate playlist_id
    utils.validate_playlist_id(playlist_id)

    # Validate uris
    if not isinstance(uris, list) or not uris:
        raise custom_errors.InvalidInputError("uris must be a non-empty list of Spotify URIs.")
    if len(uris) > 100:
        raise custom_errors.InvalidInputError("A maximum of 100 items can be added in one request.")
    for uri in uris:
        if not isinstance(uri, str) or not uri:
            raise custom_errors.InvalidInputError("Each URI must be a non-empty string.")
        if not re.match(r"^spotify:(track|episode):[A-Za-z0-9]+$", uri):
            raise custom_errors.InvalidInputError(f"Invalid Spotify URI: {uri}")

    # Validate position
    if position is not None:
        if not isinstance(position, int) or position < 0:
            raise custom_errors.InvalidInputError("position must be a non-negative integer.")

    # Get current user
    current_user_id = utils.get_current_user_id()
    users_table = DB.get('users')
    current_user = users_table.get(current_user_id)
    if not current_user:
        raise custom_errors.AuthenticationError("Current user not found.")
    user_simple = SpotifyUserSimple(
        id=current_user['id'],
        display_name=current_user['display_name'],
        external_urls=current_user.get('external_urls'),
        href=current_user.get('href'),
        type=current_user.get('type'),
        uri=current_user.get('uri'),
    )

    # Get playlist
    playlists_table = DB.get('playlists')
    playlist = playlists_table.get(playlist_id)
    if not playlist:
        raise custom_errors.NoResultsFoundError(f"Playlist with ID '{playlist_id}' not found.")

    # Get playlist_tracks
    playlist_tracks = DB.get('playlist_tracks').get(playlist_id, [])

    # Validate position is not out of bounds
    if position is not None and position > len(playlist_tracks):
        raise custom_errors.InvalidInputError("position is out of bounds for the playlist.")

    # Prepare new tracks
    new_tracks = []
    now_iso = datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    for uri in uris:
        kind, item_id = uri.split(":")[1:]
        if kind == 'track':
            tracks_table = DB.get('tracks')
            track_data = tracks_table.get(item_id)
            if not track_data:
                raise custom_errors.NoResultsFoundError(f"Track with ID '{item_id}' not found.")
            playlist_track = SpotifyPlaylistTrack(
                added_at=now_iso,
                added_by=user_simple,
                is_local=track_data.get('is_local', False),
                track=track_data
            )
        elif kind == 'episode':
            episodes_table = DB.get('episodes')
            episode_data = episodes_table.get(item_id)
            if not episode_data:
                raise custom_errors.NoResultsFoundError(f"Episode with ID '{item_id}' not found.")
            # Convert episode to track-like dict
            track_like = utils._episode_to_track_dict(episode_data)
            playlist_track = SpotifyPlaylistTrack(
                added_at=now_iso,
                added_by=user_simple,
                is_local=track_like.get('is_local', False),
                track=track_like
            )
        else:
            raise custom_errors.InvalidInputError(f"Unsupported URI type: {kind}")
        new_tracks.append(playlist_track.dict())

    # Insert or append
    if position is None:
        playlist_tracks.extend(new_tracks)
    else:
        playlist_tracks[position:position] = new_tracks

    # Update DB
    DB['playlist_tracks'][playlist_id] = playlist_tracks
    # Update playlist's track count
    playlist['tracks']['total'] = len(playlist_tracks)
    # Update snapshot_id (simulate by using a new timestamp-based string, always unique)
    new_snapshot_id = f"snapshot_{datetime.now(timezone.utc).timestamp():.6f}_{id(playlist)}"
    playlist['snapshot_id'] = new_snapshot_id

    return {"snapshot_id": new_snapshot_id}


@tool_spec(
    spec={
        'name': 'remove_playlist_items',
        'description': """ Remove one or more items (tracks or episodes) from a user's playlist.
        
        This endpoint removes all occurrences of the specified tracks or episodes from the playlist.
        You can optionally provide a snapshot_id to ensure you are modifying the correct playlist version.
        The function validates input, updates the playlist's track list, and generates a new snapshot ID. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'playlist_id': {
                    'type': 'string',
                    'description': "The Spotify ID for the playlist. Example: 'QDyH69WryQ7dPRXVOFmy2V'."
                },
                'tracks': {
                    'type': 'array',
                    'description': 'List of track objects, each containing:',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'uri': {
                                'type': 'string',
                                'description': "The Spotify URI of the track or episode to remove. Must be a valid URI of the form 'spotify:track:<id>' or 'spotify:episode:<id>'. Maximum 100 items per request. Example: [{'uri': 'spotify:track:4iV5W9uYEdYUVa79Axb7Rh'}]"
                            }
                        },
                        'required': [
                            'uri'
                        ]
                    }
                },
                'snapshot_id': {
                    'type': 'string',
                    'description': "The playlist's snapshot ID to validate against (optional)."
                }
            },
            'required': [
                'playlist_id',
                'tracks'
            ]
        }
    }
)
def remove_tracks_from_playlist(
    playlist_id: str,
    tracks: List[Dict[str, str]],
    snapshot_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Remove one or more items (tracks or episodes) from a user's playlist.

    This endpoint removes all occurrences of the specified tracks or episodes from the playlist.
    You can optionally provide a snapshot_id to ensure you are modifying the correct playlist version.
    The function validates input, updates the playlist's track list, and generates a new snapshot ID.

    Args:
        playlist_id (str): The Spotify ID for the playlist. Example: 'QDyH69WryQ7dPRXVOFmy2V'.
        tracks (List[Dict[str, str]]): List of track objects, each containing:
            - 'uri' (str): The Spotify URI of the track or episode to remove. Must be a valid URI of the form 'spotify:track:<id>' or 'spotify:episode:<id>'. Maximum 100 items per request. Example: [{'uri': 'spotify:track:4iV5W9uYEdYUVa79Axb7Rh'}]
        snapshot_id (Optional[str]): The playlist's snapshot ID to validate against (optional).

    Returns:
        Dict[str, Any]: Dictionary with the new snapshot ID, e.g. {"snapshot_id": str}.

    Raises:
        InvalidInputError: If input is invalid (bad playlist_id, tracks, or snapshot_id).
        NoResultsFoundError: If the playlist or playlist_tracks do not exist.
    """
    # Validate playlist_id
    utils.validate_playlist_id(playlist_id)

    # Validate tracks
    if not isinstance(tracks, list) or not tracks:
        raise custom_errors.InvalidInputError("tracks must be a non-empty list of dicts with 'uri' key.")
    if len(tracks) > 100:
        raise custom_errors.InvalidInputError("A maximum of 100 tracks can be removed in one request.")
    uris = []
    for t in tracks:
        if not isinstance(t, dict) or 'uri' not in t or not isinstance(t['uri'], str) or not t['uri']:
            raise custom_errors.InvalidInputError("Each track must be a dict with a non-empty 'uri' string.")
        if not re.match(r"^spotify:(track|episode):[A-Za-z0-9]+$", t['uri']):
            raise custom_errors.InvalidInputError(f"Invalid Spotify URI: {t['uri']}")
        uris.append(t['uri'])

    # Validate snapshot_id (if provided)
    if snapshot_id is not None and not isinstance(snapshot_id, str):
        raise custom_errors.InvalidInputError("snapshot_id must be a string if provided.")

    # Get playlist
    playlists_table = DB.get('playlists')
    playlist = playlists_table.get(playlist_id)
    if not playlist:
        raise custom_errors.NoResultsFoundError(f"Playlist with ID '{playlist_id}' not found.")

    # Validate snapshot_id (if provided)
    if snapshot_id is not None and playlist.get('snapshot_id') != snapshot_id:
        raise custom_errors.InvalidInputError("snapshot_id does not match the current playlist snapshot.")

    # Get playlist_tracks
    playlist_tracks = DB.get('playlist_tracks').get(playlist_id, [])

    # Remove all occurrences of each URI
    def uri_matches(track_obj, uri):
        kind, item_id = uri.split(":")[1:]
        if kind == 'track' and track_obj['track']['type'] == 'track':
            return track_obj['track']['uri'] == uri
        elif kind == 'episode' and track_obj['track']['type'] == 'track':
            # For episodes, convert the episode to track-like dict and compare uri
            # (since episodes are stored as track-like dicts)
            return track_obj['track']['uri'] == uri
        return False

    new_playlist_tracks = [pt for pt in playlist_tracks if not any(uri_matches(pt, uri) for uri in uris)]

    # Update DB
    DB['playlist_tracks'][playlist_id] = new_playlist_tracks
    # Update playlist's track count
    playlist['tracks']['total'] = len(new_playlist_tracks)
    # Update snapshot_id (simulate by using a new timestamp-based string, always unique)
    new_snapshot_id = f"snapshot_{datetime.now(timezone.utc).timestamp():.6f}_{id(playlist)}"
    playlist['snapshot_id'] = new_snapshot_id

    return {"snapshot_id": new_snapshot_id}


@tool_spec(
    spec={
        'name': 'get_current_users_playlists',
        'description': """ Get a list of the current user's playlists (owned or followed).
        
        This endpoint retrieves all playlists that the current user owns or follows. The response 
        includes detailed playlist information and supports pagination for efficient data retrieval. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'limit': {
                    'type': 'integer',
                    'description': """ The maximum number of playlists to return. Default: 20. Minimum: 1. Maximum: 50.
                    Examples: 10 (small selection), 20 (default), 50 (maximum). """
                },
                'offset': {
                    'type': 'integer',
                    'description': """ The index of the first playlist to return. Default: 0 (the first object).
                    Examples: 0 (start from beginning), 20 (skip first 20 playlists). """
                }
            },
            'required': []
        }
    }
)
def get_current_users_playlists(
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get a list of the current user's playlists (owned or followed).

    This endpoint retrieves all playlists that the current user owns or follows. The response 
    includes detailed playlist information and supports pagination for efficient data retrieval.

    Args:
        limit (int): The maximum number of playlists to return. Default: 20. Minimum: 1. Maximum: 50.
            Examples: 10 (small selection), 20 (default), 50 (maximum).
        offset (int): The index of the first playlist to return. Default: 0 (the first object).
            Examples: 0 (start from beginning), 20 (skip first 20 playlists).

    Returns:
        Dict[str, Any]: Playlists response with pagination info.
            items (List[Dict[str, Any]]): Array of playlist objects, each containing:
                id (str): Unique playlist identifier
                name (str): Playlist name
                type (str): Object type ('playlist')
                uri (str): Spotify URI for the playlist
                href (str): API endpoint URL for the playlist
                external_urls (Dict[str, str]): External URLs for the playlist
                owner (Dict[str, Any]): Playlist owner information
                public (bool): Whether the playlist is public
                collaborative (bool): Whether the playlist is collaborative
                description (str): Playlist description
                images (List[Dict[str, Any]]): Playlist cover images
                tracks (Dict[str, Any]): Playlist tracks information
                followers (Dict[str, Any]): Follower information
                snapshot_id (str): Playlist snapshot ID
            total (int): Total number of playlists available
            limit (int): Number of playlists returned in this response
            offset (int): Offset of the first playlist returned
            href (str): URL to the full list of playlists
            next (Optional[str]): URL to the next page of results
            previous (Optional[str]): URL to the previous page of results

    Raises:
        InvalidInputError: If limit is outside 1-50 range or offset is negative.
        AuthenticationError: If user is not authenticated.
    """
    # Validate limit and offset
    if not isinstance(limit, int) or limit < 1 or limit > 50:
        raise custom_errors.InvalidInputError("limit must be an integer between 1 and 50.")
    if not isinstance(offset, int) or offset < 0:
        raise custom_errors.InvalidInputError("offset must be a non-negative integer.")

    # Get current user from DB
    try:
        current_user_id = utils.get_current_user_id()
    except custom_errors.NoResultsFoundError:
        raise custom_errors.AuthenticationError("No current user is set. Please authenticate first.")

    users_table = DB.get('users')
    if current_user_id not in users_table:
        raise custom_errors.AuthenticationError("User not found or not authenticated.")

    # Get user's playlists (owned or followed)
    user_playlist_ids = DB.get('user_playlists').get(current_user_id, [])
    playlists_table = DB.get('playlists')
    playlist_objs = [playlists_table[pid] for pid in user_playlist_ids if pid in playlists_table]
    total = len(playlist_objs)

    # Apply pagination
    start = offset
    end = start + limit
    paginated_playlists = playlist_objs[start:end]

    # Build response
    href = "https://api.spotify.com/v1/me/playlists"
    response = {
        'items': paginated_playlists,
        'total': total,
        'limit': limit,
        'offset': offset,
        'href': href,
        'next': href + f"?limit={limit}&offset={end}" if end < total else None,
        'previous': href + f"?limit={limit}&offset={max(0, start - limit)}" if start > 0 else None
    }
    return response


@tool_spec(
    spec={
        'name': 'get_user_playlists',
        'description': """ Get a list of a user's playlists (owned or followed).
        
        This endpoint retrieves all playlists that the specified user owns or follows. The response includes detailed playlist information and supports pagination for efficient data retrieval. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': "The user's Spotify ID. Example: 'smuqPNFPXrJKcEt943KrY8'."
                },
                'limit': {
                    'type': 'integer',
                    'description': """ The maximum number of playlists to return. Default: 20. Minimum: 1. Maximum: 50.
                    Examples: 10 (small selection), 20 (default), 50 (maximum). """
                },
                'offset': {
                    'type': 'integer',
                    'description': """ The index of the first playlist to return. Default: 0 (the first object).
                    Examples: 0 (start from beginning), 20 (skip first 20 playlists). """
                }
            },
            'required': [
                'user_id'
            ]
        }
    }
)
def get_user_playlists(
    user_id: str,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """
    Get a list of a user's playlists (owned or followed).

    This endpoint retrieves all playlists that the specified user owns or follows. The response includes detailed playlist information and supports pagination for efficient data retrieval.

    Args:
        user_id (str): The user's Spotify ID. Example: 'smuqPNFPXrJKcEt943KrY8'.
        limit (int): The maximum number of playlists to return. Default: 20. Minimum: 1. Maximum: 50.
            Examples: 10 (small selection), 20 (default), 50 (maximum).
        offset (int): The index of the first playlist to return. Default: 0 (the first object).
            Examples: 0 (start from beginning), 20 (skip first 20 playlists).

    Returns:
        Dict[str, Any]: Playlists response with pagination info.
            items (List[Dict[str, Any]]): Array of playlist objects, each containing:
                id (str): Unique playlist identifier
                name (str): Playlist name
                type (str): Object type ('playlist')
                uri (str): Spotify URI for the playlist
                href (str): API endpoint URL for the playlist
                external_urls (Dict[str, str]): External URLs for the playlist
                owner (Dict[str, Any]): Playlist owner information
                public (bool): Whether the playlist is public
                collaborative (bool): Whether the playlist is collaborative
                description (str): Playlist description
                images (List[Dict[str, Any]]): Playlist cover images
                tracks (Dict[str, Any]): Playlist tracks information
                followers (Dict[str, Any]): Follower information
                snapshot_id (str): Playlist snapshot ID
            total (int): Total number of playlists available
            limit (int): Number of playlists returned in this response
            offset (int): Offset of the first playlist returned
            href (str): URL to the full list of playlists
            next (Optional[str]): URL to the next page of results
            previous (Optional[str]): URL to the previous page of results

    Raises:
        InvalidInputError: If user_id is not a string or is empty, limit is outside 1-50 range, or offset is negative.
        NoResultsFoundError: If no user exists with the specified user_id.
    """
    # Validate user_id
    if not isinstance(user_id, str):
        raise custom_errors.InvalidInputError("user_id must be a string.")
    if not user_id:
        raise custom_errors.InvalidInputError("user_id cannot be empty.")
    if not isinstance(limit, int) or limit < 1 or limit > 50:
        raise custom_errors.InvalidInputError("limit must be an integer between 1 and 50.")
    if not isinstance(offset, int) or offset < 0:
        raise custom_errors.InvalidInputError("offset must be a non-negative integer.")

    # Get user data from DB
    users_table = DB.get('users')
    if user_id not in users_table:
        raise custom_errors.NoResultsFoundError(f"User with ID '{user_id}' not found.")

    # Get user's playlists (owned or followed)
    user_playlist_ids = DB.get('user_playlists').get(user_id, [])
    playlists_table = DB.get('playlists')
    playlist_objs = [playlists_table[pid] for pid in user_playlist_ids if pid in playlists_table]
    total = len(playlist_objs)

    # Apply pagination
    start = offset
    end = start + limit
    paginated_playlists = playlist_objs[start:end]

    # Build response
    href = f"https://api.spotify.com/v1/users/{user_id}/playlists"
    response = {
        'items': paginated_playlists,
        'total': total,
        'limit': limit,
        'offset': offset,
        'href': href,
        'next': href + f"?limit={limit}&offset={end}" if end < total else None,
        'previous': href + f"?limit={limit}&offset={max(0, start - limit)}" if start > 0 else None
    }
    return response


@tool_spec(
    spec={
        'name': 'create_playlist',
        'description': """ Create a new playlist for a user.
        
        This endpoint creates a new playlist owned by the specified user. The playlist 
        is added to the user's list of playlists and initialized with no tracks. 
        The response includes the full playlist object as stored in the database. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': "The user's Spotify ID. Example: 'smuqPNFPXrJKcEt943KrY8'."
                },
                'name': {
                    'type': 'string',
                    'description': "The name of the playlist. Example: 'My Playlist'."
                },
                'public': {
                    'type': 'boolean',
                    'description': 'Whether the playlist is public. Default: True.'
                },
                'collaborative': {
                    'type': 'boolean',
                    'description': 'Whether the playlist is collaborative. Default: False.'
                },
                'description': {
                    'type': 'string',
                    'description': 'Playlist description. Default: None.'
                }
            },
            'required': [
                'user_id',
                'name'
            ]
        }
    }
)
def create_playlist(
    user_id: str,
    name: str,
    public: bool = True,
    collaborative: bool = False,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new playlist for a user.

    This endpoint creates a new playlist owned by the specified user. The playlist 
    is added to the user's list of playlists and initialized with no tracks. 
    The response includes the full playlist object as stored in the database.

    Args:
        user_id (str): The user's Spotify ID. Example: 'smuqPNFPXrJKcEt943KrY8'.
        name (str): The name of the playlist. Example: 'My Playlist'.
        public (bool): Whether the playlist is public. Default: True.
        collaborative (bool): Whether the playlist is collaborative. Default: False.
        description (Optional[str]): Playlist description. Default: None.

    Returns:
        Dict[str, Any]: The created playlist object, including:
            id (str): Unique playlist identifier
            name (str): Playlist name
            type (str): Object type ('playlist')
            uri (str): Spotify URI for the playlist
            href (str): API endpoint URL for the playlist
            external_urls (Dict[str, str]): External URLs for the playlist
            owner (Dict[str, Any]): Playlist owner information
            public (bool): Whether the playlist is public
            collaborative (bool): Whether the playlist is collaborative
            description (str): Playlist description
            images (List[Dict[str, Any]]): Playlist cover images
            tracks (Dict[str, Any]): Playlist tracks information (total=0)
            followers (Dict[str, Any]): Follower information (total=0)
            snapshot_id (str): Playlist snapshot ID

    Raises:
        InvalidInputError: If user_id or name is invalid.
        NoResultsFoundError: If the user does not exist.
    """
    # Validate user_id and name
    if not isinstance(user_id, str) or not user_id:
        raise custom_errors.InvalidInputError("user_id must be a non-empty string.")
    if not isinstance(name, str) or not name:
        raise custom_errors.InvalidInputError("name must be a non-empty string.")
    if not isinstance(public, bool):
        raise custom_errors.InvalidInputError("public must be a boolean.")
    if not isinstance(collaborative, bool):
        raise custom_errors.InvalidInputError("collaborative must be a boolean.")
    if description is not None and not isinstance(description, str):
        raise custom_errors.InvalidInputError("description must be a string if provided.")

    # Get user data from DB
    users_table = DB.get('users')
    user = users_table.get(user_id)
    if not user:
        raise custom_errors.NoResultsFoundError(f"User with ID '{user_id}' not found.")

    # Generate unique playlist ID
    playlist_id = utils.generate_spotify_id('playlist')
    uri = f"spotify:playlist:{playlist_id}"
    href = f"https://api.spotify.com/v1/playlists/{playlist_id}"
    external_urls = {"spotify": f"https://open.spotify.com/playlist/{playlist_id}"}
    owner = {
        "id": user['id'],
        "display_name": user.get('display_name', user['id'])
    }
    playlist = {
        "id": playlist_id,
        "name": name,
        "type": "playlist",
        "uri": uri,
        "href": href,
        "external_urls": external_urls,
        "owner": owner,
        "public": public,
        "collaborative": collaborative,
        "description": description,
        "images": [],
        "tracks": {"total": 0},
        "followers": {"total": 0},
        "snapshot_id": f"snapshot_{datetime.now(timezone.utc).timestamp():.6f}_{playlist_id}"
    }
    # Add to DB
    DB.get('playlists')[playlist_id] = playlist
    if user_id not in DB.get('user_playlists'):
        DB.get('user_playlists')[user_id] = []
    DB.get('user_playlists')[user_id].append(playlist_id)
    DB.get('playlist_tracks')[playlist_id] = []
    return playlist


@tool_spec(
    spec={
        'name': 'get_playlist_cover_image',
        'description': """ Get the current cover image(s) for a playlist.
        
        This endpoint retrieves the cover image(s) for the specified playlist. The response is a list of image objects, each containing the image URL and its dimensions. If no cover image is set, an empty list is returned. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'playlist_id': {
                    'type': 'string',
                    'description': "The Spotify ID for the playlist. Example: 'QDyH69WryQ7dPRXVOFmy2V'."
                }
            },
            'required': [
                'playlist_id'
            ]
        }
    }
)
def get_playlist_cover_image(
    playlist_id: str
) -> List[Dict[str, Any]]:
    """
    Get the current cover image(s) for a playlist.

    This endpoint retrieves the cover image(s) for the specified playlist. The response is a list of image objects, each containing the image URL and its dimensions. If no cover image is set, an empty list is returned.

    Args:
        playlist_id (str): The Spotify ID for the playlist. Example: 'QDyH69WryQ7dPRXVOFmy2V'.

    Returns:
        List[Dict[str, Any]]: List of image objects, each with:
            url (str): The source URL of the image
            height (int): The image height in pixels
            width (int): The image width in pixels
        If no cover image is set, returns an empty list.

    Raises:
        InvalidInputError: If playlist_id is not a string or is empty.
        NoResultsFoundError: If no playlist exists with the specified playlist_id.
    """
    if not isinstance(playlist_id, str) or not playlist_id:
        raise custom_errors.InvalidInputError("playlist_id must be a non-empty string.")
    playlists_table = DB.get('playlists')
    playlist = playlists_table.get(playlist_id)
    if not playlist:
        raise custom_errors.NoResultsFoundError(f"Playlist with ID '{playlist_id}' not found.")
    # Try DB['playlist_cover_images'], then DB['playlist_images'], then playlist['images']
    playlist_cover_images = DB.get('playlist_cover_images')
    if playlist_cover_images and playlist_id in playlist_cover_images:
        imgs = playlist_cover_images[playlist_id]
        return imgs if isinstance(imgs, list) else []
    playlist_images = DB.get('playlist_images')
    if playlist_images and playlist_id in playlist_images:
        imgs = playlist_images[playlist_id]
        return imgs if isinstance(imgs, list) else []
    images = playlist.get('images', [])
    return images if isinstance(images, list) and images else []


@tool_spec(
    spec={
        'name': 'add_custom_playlist_cover_image',
        'description': """ Add or replace the custom cover image for a playlist.
        
        This endpoint allows you to upload a new JPEG image to be used as the cover for a specific playlist. The image must be base64-encoded JPEG data, with a maximum size of 256 KB. Any previous cover image will be replaced. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'playlist_id': {
                    'type': 'string',
                    'description': "The Spotify ID for the playlist. Example: 'QDyH69WryQ7dPRXVOFmy2V'."
                },
                'image_data': {
                    'type': 'string',
                    'description': 'Base64-encoded JPEG image data. Maximum 256 KB after decoding.'
                }
            },
            'required': [
                'playlist_id',
                'image_data'
            ]
        }
    }
)
def add_custom_playlist_cover_image(
    playlist_id: str,
    image_data: str
) -> None:
    """
    Add or replace the custom cover image for a playlist.

    This endpoint allows you to upload a new JPEG image to be used as the cover for a specific playlist. The image must be base64-encoded JPEG data, with a maximum size of 256 KB. Any previous cover image will be replaced.

    Args:
        playlist_id (str): The Spotify ID for the playlist. Example: 'QDyH69WryQ7dPRXVOFmy2V'.
        image_data (str): Base64-encoded JPEG image data. Maximum 256 KB after decoding.

    Returns:
        None.

    Raises:
        InvalidInputError: If playlist_id or image_data is invalid, not base64, not JPEG, or too large.
        NoResultsFoundError: If the playlist does not exist.
    """
    # Validate playlist_id
    utils.validate_playlist_id(playlist_id)
    # Validate image_data
    if not isinstance(image_data, str) or not image_data:
        raise custom_errors.InvalidInputError("image_data must be a non-empty base64-encoded string.")
    try:
        decoded = base64.b64decode(image_data, validate=True)
    except Exception:
        raise custom_errors.InvalidInputError("image_data must be valid base64-encoded JPEG data.")
    if len(decoded) > 256 * 1024:
        raise custom_errors.InvalidInputError("Image size exceeds 256 KB limit.")
    # Check JPEG header (first 2 bytes: 0xFFD8, last 2 bytes: 0xFFD9)
    if not (decoded.startswith(b'\xff\xd8') and decoded.endswith(b'\xff\xd9')):
        raise custom_errors.InvalidInputError("Image must be a JPEG file.")
    # Validate playlist exists
    playlists_table = DB.get('playlists')
    playlist = playlists_table.get(playlist_id)
    if not playlist:
        raise custom_errors.NoResultsFoundError(f"Playlist with ID '{playlist_id}' not found.")
    # Simulate image URL and dimensions (fixed for test, e.g. 300x300)
    url = f"https://images.spotify.com/playlist/{playlist_id}/cover.jpg"
    image_obj = {"url": url, "height": 300, "width": 300}
    DB.get('playlist_cover_images')[playlist_id] = [image_obj]
    # Optionally update playlist['images'] for consistency
    playlist['images'] = [image_obj]
    # No return (202 accepted)
from typing import Optional, List, Dict, Any
from datetime import datetime
import copy

from .SimulationEngine.db import DB
from .SimulationEngine import custom_errors, utils


@tool_spec(
    spec={
        'name': 'get_playlist',
        'description': """ Get a playlist owned by a Spotify user.
        
        This endpoint retrieves detailed information about a specific playlist including its tracks, metadata, and owner information. This is essential for displaying playlist information, track listings, and playlist details in music applications. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'playlist_id': {
                    'type': 'string',
                    'description': 'The Spotify ID for the playlist.'
                },
                'market': {
                    'type': 'string',
                    'description': 'An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.'
                },
                'fields': {
                    'type': 'string',
                    'description': 'Filters for the query: a comma-separated list of the fields to return. If omitted, all fields are returned.'
                },
                'additional_types': {
                    'type': 'string',
                    'description': 'A comma-separated list of item types that your client supports besides the default track type. Valid types are: track and episode.'
                }
            },
            'required': [
                'playlist_id'
            ]
        }
    }
)
def get_playlist(
    playlist_id: str,
    market: Optional[str] = None,
    fields: Optional[str] = None,
    additional_types: Optional[str] = None
) -> Dict[str, Any]:
    """Get a playlist owned by a Spotify user.

    This endpoint retrieves detailed information about a specific playlist including its tracks, metadata, and owner information. This is essential for displaying playlist information, track listings, and playlist details in music applications.

    Args:
        playlist_id (str): The Spotify ID for the playlist.
        market (Optional[str]): An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.
        fields (Optional[str]): Filters for the query: a comma-separated list of the fields to return. If omitted, all fields are returned.
        additional_types (Optional[str]): A comma-separated list of item types that your client supports besides the default track type. Valid types are: track and episode.

    Returns:
        Dict[str, Any]: Playlist object with comprehensive information.
            collaborative (bool): Whether the playlist is collaborative
            description (Optional[str]): The playlist description
            external_urls (Dict[str, str]): Known external URLs for this playlist
                - spotify (str): The Spotify URL for the playlist
            followers (Dict[str, Any]): Information about the followers of the playlist
                - href (Optional[str]): A link to the Web API endpoint providing full details of the followers
                - total (int): The total number of followers
            href (str): A link to the Web API endpoint providing full details of the playlist
            id (str): The Spotify ID for the playlist
            images (List[Dict[str, Any]]): Images for the playlist
                - url (str): The source URL of the image
                - height (int): The image height in pixels
                - width (int): The image width in pixels
            name (str): The name of the playlist
            owner (Dict[str, Any]): The user who owns the playlist
                - display_name (str): The name displayed on the user's profile
                - external_urls (Dict[str, str]): Known external URLs for this user
                    - spotify (str): The Spotify URL for the user
                - followers (Dict[str, Any]): Information about the followers of the user
                    - href (Optional[str]): A link to the Web API endpoint providing full details of the followers
                    - total (int): The total number of followers
                - href (str): A link to the Web API endpoint providing full details of the user
                - id (str): The Spotify ID for the user
                - images (List[Dict[str, Any]]): The user's profile image
                - type (str): The object type ('user')
                - uri (str): The Spotify URI for the user
            public (bool): Whether the playlist is public
            snapshot_id (str): The version identifier for the current playlist
            tracks (Dict[str, Any]): Information about the tracks of the playlist
                - href (str): A link to the Web API endpoint providing full details of the playlist tracks
                - limit (int): The maximum number of tracks in the response
                - next (Optional[str]): URL to the next page of results
                - offset (int): The offset of the items returned
                - previous (Optional[str]): URL to the previous page of results
                - total (int): The total number of tracks available
                - items (List[Dict[str, Any]]): Array of playlist track objects
                    - added_at (str): The date and time the track was added
                    - added_by (Dict[str, Any]): The Spotify user who added the track
                        - display_name (str): The name displayed on the user's profile
                        - external_urls (Dict[str, str]): Known external URLs for this user
                            - spotify (str): The Spotify URL for the user
                        - href (str): A link to the Web API endpoint providing full details of the user
                        - id (str): The Spotify ID for the user
                        - type (str): The object type ('user')
                        - uri (str): The Spotify URI for the user
                    - is_local (bool): Whether this track is a local file or not
                    - track (Dict[str, Any]): Information about the track
                        - artists (List[Dict[str, Any]]): Array of artist objects
                        - available_markets (List[str]): List of markets where track is available
                        - disc_number (int): The disc number
                        - duration_ms (int): The track length in milliseconds
                        - explicit (bool): Whether the track has explicit lyrics
                        - external_urls (Dict[str, str]): External URLs for this track
                            - spotify (str): The Spotify URL for the track
                        - href (str): A link to the Web API endpoint providing full details of the track
                        - id (str): The Spotify ID for the track
                        - is_playable (bool): Whether the track is playable in the given market
                        - linked_from (Optional[Dict[str, Any]]): Information about the originally requested track when Track Relinking is applied
                        - restrictions (Optional[Dict[str, Any]]): Track restrictions if any
                            - reason (str): The reason for the restriction
                        - name (str): The name of the track
                        - preview_url (Optional[str]): A URL to a 30 second preview (MP3 format) of the track
                        - track_number (int): The number of the track
                        - type (str): The object type ('track')
                        - uri (str): The Spotify URI for the track
                        - is_local (bool): Whether the track is from a local file
            type (str): The object type ('playlist')
            uri (str): The Spotify URI for the playlist

    Raises:
        InvalidInputError: If playlist_id is not a string or is empty, or if additional_types has invalid values.
        InvalidMarketError: If market is not a valid ISO 3166-1 alpha-2 country code.
        NoResultsFoundError: If no playlist exists with the specified playlist_id or if playlist is not available in the specified market.
    """
    # Validate playlist_id
    utils.validate_playlist_id(playlist_id)
    
    # Validate market parameter if provided
    if market is not None:
        if not utils.validate_market(market):
            raise custom_errors.InvalidMarketError("market must be a valid ISO 3166-1 alpha-2 country code.")
    
    # Validate additional_types if provided
    if additional_types is not None:
        if not isinstance(additional_types, str):
            raise custom_errors.InvalidInputError("additional_types must be a string.")
        valid_types = ['track', 'episode']
        if not utils.validate_type(additional_types, valid_types):
            raise custom_errors.InvalidInputError("additional_types must contain valid types: track, episode.")
    else:
        additional_types = 'track'
    allowed_types = [t.strip() for t in additional_types.split(',')]
    
    # Get playlist data from DB
    playlists_table = DB.get('playlists', {})
    playlist_data = playlists_table.get(playlist_id)
    
    if playlist_data is None:
        raise custom_errors.NoResultsFoundError(f"Playlist with ID '{playlist_id}' not found.")
    
    # Get playlist tracks
    playlist_tracks_table = DB.get('playlist_tracks', {})
    tracks_data = playlist_tracks_table.get(playlist_id, [])
    
    # Get tracks details
    tracks_table = DB.get('tracks', {})
    tracks_items = []
    
    for track_item in tracks_data:
        # Only include allowed types
        item_type = track_item['track'].get('type', 'track')
        if item_type not in allowed_types:
            continue
        track_id = track_item['track']['id']
        track_data = tracks_table.get(track_id)
        if track_data:
            # Apply market filtering if specified
            if market is not None:
                available_markets = track_data.get('available_markets', [])
                if market not in available_markets:
                    continue
            # Create playlist track item
            playlist_track_item = {
                'added_at': track_item['added_at'],
                'added_by': track_item['added_by'],
                'is_local': track_item['is_local'],
                'track': track_data
            }
            tracks_items.append(playlist_track_item)
    
    # Create tracks object
    tracks_object = {
        'href': f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
        'limit': 100,
        'next': None,
        'offset': 0,
        'previous': None,
        'total': len(tracks_items),
        'items': tracks_items
    }
    
    # Create complete playlist object
    playlist_object = copy.deepcopy(playlist_data)
    playlist_object['tracks'] = tracks_object
    
    # Apply field filtering if specified
    if fields is not None:
        if not isinstance(fields, str):
            raise custom_errors.InvalidInputError("fields must be a string.")
        # For simplicity, we'll return the full object as field filtering is complex
    
    return playlist_object


@tool_spec(
    spec={
        'name': 'change_playlist_details',
        'description': """ Change a playlist's name and public/private state, collaborative state, and description.
        
        This endpoint allows users to modify the metadata of their playlists, including the name, visibility settings, collaborative status, and description. This is essential for playlist management functionality. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'playlist_id': {
                    'type': 'string',
                    'description': 'The Spotify ID for the playlist.'
                },
                'name': {
                    'type': 'string',
                    'description': 'The new name for the playlist, for example "My New Playlist Title".'
                },
                'public': {
                    'type': 'boolean',
                    'description': 'If true the playlist will be public, if false it will be private.'
                },
                'collaborative': {
                    'type': 'boolean',
                    'description': 'If true, the playlist will become collaborative and other users will be able to modify the playlist in their Spotify client.'
                },
                'description': {
                    'type': 'string',
                    'description': 'Value for playlist description as displayed in Spotify Clients and in the Web API.'
                }
            },
            'required': [
                'playlist_id'
            ]
        }
    }
)
def change_playlist_details(playlist_id: str, name: Optional[str] = None, public: Optional[bool] = None, 
                          collaborative: Optional[bool] = None, description: Optional[str] = None) -> Dict[str, Any]:
    """Change a playlist's name and public/private state, collaborative state, and description.

    This endpoint allows users to modify the metadata of their playlists, including the name, visibility settings, collaborative status, and description. This is essential for playlist management functionality.

    Args:
        playlist_id (str): The Spotify ID for the playlist.
        name (Optional[str]): The new name for the playlist, for example "My New Playlist Title".
        public (Optional[bool]): If true the playlist will be public, if false it will be private.
        collaborative (Optional[bool]): If true, the playlist will become collaborative and other users will be able to modify the playlist in their Spotify client.
        description (Optional[str]): Value for playlist description as displayed in Spotify Clients and in the Web API.

    Returns:
        Dict[str, Any]: Empty object indicating success.

    Raises:
        InvalidInputError: If playlist_id is not a string or is empty, or if any parameter has invalid values.
        NoResultsFoundError: If no playlist exists with the specified playlist_id.
        AuthenticationError: If the user is not authorized to modify the playlist.
    """
    # Validate playlist_id
    utils.validate_playlist_id(playlist_id)
    
    # Validate parameters
    if name is not None:
        if not isinstance(name, str):
            raise custom_errors.InvalidInputError("name must be a string.")
        if not name.strip():
            raise custom_errors.InvalidInputError("name cannot be empty or contain only whitespace.")
        if len(name) > 100:
            raise custom_errors.InvalidInputError("name cannot exceed 100 characters.")
        if len(name.strip()) < 1:
            raise custom_errors.InvalidInputError("name must be at least 1 character long.")
    
    if public is not None:
        if not isinstance(public, bool):
            raise custom_errors.InvalidInputError("public must be a boolean.")
    
    if collaborative is not None:
        if not isinstance(collaborative, bool):
            raise custom_errors.InvalidInputError("collaborative must be a boolean.")
    
    if description is not None:
        if not isinstance(description, str):
            raise custom_errors.InvalidInputError("description must be a string.")
        if len(description) > 300:
            raise custom_errors.InvalidInputError("description cannot exceed 300 characters.")
    
    # Validate collaborative and public logic (Spotify rule: collaborative playlists can't be public)
    if collaborative is not None and public is not None:
        if collaborative and public:
            raise custom_errors.InvalidInputError("Collaborative playlists cannot be public.")
    elif collaborative is not None:
        # If only collaborative is being set, check current public state
        playlists_table = DB.get('playlists', {})
        playlist_data = playlists_table.get(playlist_id)
        if playlist_data and collaborative and playlist_data.get('public', False):
            raise custom_errors.InvalidInputError("Cannot make playlist collaborative while it is public.")
    elif public is not None:
        # If only public is being set, check current collaborative state
        playlists_table = DB.get('playlists', {})
        playlist_data = playlists_table.get(playlist_id)
        if playlist_data and public and playlist_data.get('collaborative', False):
            raise custom_errors.InvalidInputError("Cannot make playlist public while it is collaborative.")
    
    # Get playlist data from DB
    playlists_table = DB.get('playlists', {})
    playlist_data = playlists_table.get(playlist_id)
    
    if playlist_data is None:
        raise custom_errors.NoResultsFoundError(f"Playlist with ID '{playlist_id}' not found.")
    
    # Check if user is authorized to modify the playlist
    try:
        current_user_id = utils.get_current_user_id()
    except custom_errors.NoResultsFoundError:
        raise custom_errors.AuthenticationError("No authenticated user found.")
    
    playlist_owner_id = playlist_data.get('owner', {}).get('id')
    
    if playlist_owner_id != current_user_id:
        raise custom_errors.AuthenticationError("You can only modify playlists that you own.")
    
    # Update playlist details
    if name is not None:
        playlist_data['name'] = name.strip()
    
    if public is not None:
        playlist_data['public'] = public
    
    if collaborative is not None:
        playlist_data['collaborative'] = collaborative
    
    if description is not None:
        playlist_data['description'] = description
    
    # Update snapshot_id to indicate change
    playlist_data['snapshot_id'] = f"snapshot_{utils.generate_base62_id(8)}"
    
    # Save updated playlist
    playlists_table[playlist_id] = playlist_data
    DB['playlists'] = playlists_table
    
    return {}


@tool_spec(
    spec={
        'name': 'get_playlist_items',
        'description': """ Get full details of the items of a playlist owned by a Spotify user.
        
        This endpoint retrieves the tracks and episodes in a playlist, along with metadata about when they were added and by whom. This is essential for displaying playlist contents and managing playlist items. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'playlist_id': {
                    'type': 'string',
                    'description': 'The Spotify ID for the playlist.'
                },
                'market': {
                    'type': 'string',
                    'description': 'An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.'
                },
                'fields': {
                    'type': 'string',
                    'description': 'Filters for the query: a comma-separated list of the fields to return. If omitted, all fields are returned.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.'
                },
                'offset': {
                    'type': 'integer',
                    'description': 'The index of the first item to return. Default: 0 (the first item).'
                },
                'additional_types': {
                    'type': 'string',
                    'description': 'A comma-separated list of item types that your client supports besides the default track type. Valid types are: track and episode.'
                }
            },
            'required': [
                'playlist_id'
            ]
        }
    }
)
def get_playlist_items(playlist_id: str, market: Optional[str] = None, fields: Optional[str] = None,
                      limit: Optional[int] = None, offset: Optional[int] = None, additional_types: Optional[str] = None) -> Dict[str, Any]:
    """Get full details of the items of a playlist owned by a Spotify user.

    This endpoint retrieves the tracks and episodes in a playlist, along with metadata about when they were added and by whom. This is essential for displaying playlist contents and managing playlist items.

    Args:
        playlist_id (str): The Spotify ID for the playlist.
        market (Optional[str]): An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.
        fields (Optional[str]): Filters for the query: a comma-separated list of the fields to return. If omitted, all fields are returned.
        limit (Optional[int]): The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset (Optional[int]): The index of the first item to return. Default: 0 (the first item).
        additional_types (Optional[str]): A comma-separated list of item types that your client supports besides the default track type. Valid types are: track and episode.

    Returns:
        Dict[str, Any]: Playlist tracks object with comprehensive information.
            href (str): A link to the Web API endpoint providing full details of the playlist tracks
            limit (int): The maximum number of tracks in the response
            next (Optional[str]): URL to the next page of results
            offset (int): The offset of the items returned
            previous (Optional[str]): URL to the previous page of results
            total (int): The total number of tracks available
            items (List[Dict[str, Any]]): Array of playlist track objects
                - added_at (str): The date and time the track was added
                - added_by (Dict[str, Any]): The Spotify user who added the track
                    - display_name (str): The name displayed on the user's profile
                    - external_urls (Dict[str, str]): Known external URLs for this user
                        - spotify (str): The Spotify URL for the user
                    - href (str): A link to the Web API endpoint providing full details of the user
                    - id (str): The Spotify ID for the user
                    - type (str): The object type ('user')
                    - uri (str): The Spotify URI for the user
                - is_local (bool): Whether this track is a local file or not
                - track (Dict[str, Any]): Information about the track
                    - artists (List[Dict[str, Any]]): Array of artist objects
                    - available_markets (List[str]): List of markets where track is available
                    - disc_number (int): The disc number
                    - duration_ms (int): The track length in milliseconds
                    - explicit (bool): Whether the track has explicit lyrics
                    - external_urls (Dict[str, str]): External URLs for this track
                        - spotify (str): The Spotify URL for the track
                    - href (str): A link to the Web API endpoint providing full details of the track
                    - id (str): The Spotify ID for the track
                    - is_playable (bool): Whether the track is playable in the given market
                    - linked_from (Optional[Dict[str, Any]]): Information about the originally requested track when Track Relinking is applied
                    - restrictions (Optional[Dict[str, Any]]): Track restrictions if any
                        - reason (str): The reason for the restriction
                    - name (str): The name of the track
                    - preview_url (Optional[str]): A URL to a 30 second preview (MP3 format) of the track
                    - track_number (int): The number of the track
                    - type (str): The object type ('track')
                    - uri (str): The Spotify URI for the track
                    - is_local (bool): Whether the track is from a local file

    Raises:
        InvalidInputError: If playlist_id is not a string or is empty, or if any parameter has invalid values.
        InvalidMarketError: If market is not a valid ISO 3166-1 alpha-2 country code.
        NoResultsFoundError: If no playlist exists with the specified playlist_id or if playlist is not available in the specified market.
    """
    # Validate playlist_id
    utils.validate_playlist_id(playlist_id)
    
    # Validate market parameter if provided
    if market is not None:
        if not utils.validate_market(market):
            raise custom_errors.InvalidMarketError("market must be a valid ISO 3166-1 alpha-2 country code.")
    
    # Validate limit and offset
    utils.validate_limit_offset(limit, offset)
    
    # Validate additional_types if provided
    if additional_types is not None:
        if not isinstance(additional_types, str):
            raise custom_errors.InvalidInputError("additional_types must be a string.")
        valid_types = ['track', 'episode']
        if not utils.validate_type(additional_types, valid_types):
            raise custom_errors.InvalidInputError("additional_types must contain valid types: track, episode.")
    
    # Get playlist data from DB
    playlists_table = DB.get('playlists', {})
    playlist_data = playlists_table.get(playlist_id)
    
    if playlist_data is None:
        raise custom_errors.NoResultsFoundError(f"Playlist with ID '{playlist_id}' not found.")
    
    # Get playlist tracks
    playlist_tracks_table = DB.get('playlist_tracks', {})
    tracks_data = playlist_tracks_table.get(playlist_id, [])
    
    # Get tracks details
    tracks_table = DB.get('tracks', {})
    tracks_items = []
    
    for track_item in tracks_data:
        track_id = track_item['track']['id']
        track_data = tracks_table.get(track_id)
        if track_data:
            # Apply market filtering if specified
            if market is not None:
                available_markets = track_data.get('available_markets', [])
                if market not in available_markets:
                    continue
            
            # Create playlist track item
            playlist_track_item = {
                'added_at': track_item['added_at'],
                'added_by': track_item['added_by'],
                'is_local': track_item['is_local'],
                'track': track_data
            }
            tracks_items.append(playlist_track_item)
    
    # Apply pagination
    pagination_result = utils.apply_pagination(tracks_items, limit, offset)
    
    # Create tracks object
    tracks_object = {
        'href': f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks",
        'limit': pagination_result['limit'],
        'next': pagination_result['next'],
        'offset': pagination_result['offset'],
        'previous': pagination_result['previous'],
        'total': pagination_result['total'],
        'items': pagination_result['items']
    }
    
    return tracks_object


@tool_spec(
    spec={
        'name': 'update_playlist_items',
        'description': """ Either reorder or replace a playlist's items depending on the request's parameters.
        
        This endpoint allows users to modify the contents of their playlists by either reordering existing tracks or replacing them entirely. This is essential for playlist management functionality. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'playlist_id': {
                    'type': 'string',
                    'description': 'The Spotify ID for the playlist.'
                },
                'uris': {
                    'type': 'array',
                    'description': 'A list of Spotify URIs to set, can be track or episode URIs. A maximum of 100 items can be set in one request.',
                    'items': {
                        'type': 'string'
                    }
                },
                'range_start': {
                    'type': 'integer',
                    'description': 'The position of the first item to be reordered.'
                },
                'insert_before': {
                    'type': 'integer',
                    'description': 'The position where the items should be inserted.'
                },
                'range_length': {
                    'type': 'integer',
                    'description': 'The amount of items to be reordered. Defaults to 1 if not set.'
                },
                'snapshot_id': {
                    'type': 'string',
                    'description': "The playlist's snapshot ID against which you want to make the changes."
                }
            },
            'required': [
                'playlist_id'
            ]
        }
    }
)
def update_playlist_items(playlist_id: str, uris: Optional[List[str]] = None, range_start: Optional[int] = None,
                         insert_before: Optional[int] = None, range_length: Optional[int] = None,
                         snapshot_id: Optional[str] = None) -> Dict[str, Any]:
    """Either reorder or replace a playlist's items depending on the request's parameters.

    This endpoint allows users to modify the contents of their playlists by either reordering existing tracks or replacing them entirely. This is essential for playlist management functionality.

    Args:
        playlist_id (str): The Spotify ID for the playlist.
        uris (Optional[List[str]]): A list of Spotify URIs to set, can be track or episode URIs. A maximum of 100 items can be set in one request.
        range_start (Optional[int]): The position of the first item to be reordered.
        insert_before (Optional[int]): The position where the items should be inserted.
        range_length (Optional[int]): The amount of items to be reordered. Defaults to 1 if not set.
        snapshot_id (Optional[str]): The playlist's snapshot ID against which you want to make the changes.

    Returns:
        Dict[str, Any]: Playlist snapshot object.
            snapshot_id (str): The version identifier for the current playlist.

    Raises:
        InvalidInputError: If playlist_id is not a string or is empty, or if any parameter has invalid values.
        NoResultsFoundError: If no playlist exists with the specified playlist_id.
        AuthenticationError: If the user is not authorized to modify the playlist.
    """
    # Validate playlist_id
    utils.validate_playlist_id(playlist_id)
    
    # Validate uris if provided
    if uris is not None:
        if not isinstance(uris, list):
            raise custom_errors.InvalidInputError("uris must be a list.")
        if len(uris) > 100:
            raise custom_errors.InvalidInputError("uris cannot contain more than 100 items.")
        if not all(isinstance(uri, str) and uri for uri in uris):
            raise custom_errors.InvalidInputError("All URIs must be non-empty strings.")
    
    # Validate range_start if provided
    if range_start is not None:
        if not isinstance(range_start, int) or range_start < 0:
            raise custom_errors.InvalidInputError("range_start must be a non-negative integer.")
    
    # Validate insert_before if provided
    if insert_before is not None:
        if not isinstance(insert_before, int) or insert_before < 0:
            raise custom_errors.InvalidInputError("insert_before must be a non-negative integer.")
    
    # Validate range_length if provided
    if range_length is not None:
        if not isinstance(range_length, int) or range_length < 1:
            raise custom_errors.InvalidInputError("range_length must be a positive integer.")
    
    # Validate snapshot_id if provided
    if snapshot_id is not None:
        if not isinstance(snapshot_id, str):
            raise custom_errors.InvalidInputError("snapshot_id must be a string.")
        if not snapshot_id.strip():
            raise custom_errors.InvalidInputError("snapshot_id cannot be empty.")
    
    # Get playlist data from DB
    playlists_table = DB.get('playlists', {})
    playlist_data = playlists_table.get(playlist_id)
    
    if playlist_data is None:
        raise custom_errors.NoResultsFoundError(f"Playlist with ID '{playlist_id}' not found.")
    
    # Check if user is authorized to modify the playlist
    try:
        current_user_id = utils.get_current_user_id()
    except custom_errors.NoResultsFoundError:
        raise custom_errors.AuthenticationError("No authenticated user found.")
    
    playlist_owner_id = playlist_data.get('owner', {}).get('id')
    
    if playlist_owner_id != current_user_id:
        raise custom_errors.AuthenticationError("You can only modify playlists that you own.")
    
    # Check snapshot_id if provided
    if snapshot_id is not None:
        current_snapshot_id = playlist_data.get('snapshot_id')
        if snapshot_id != current_snapshot_id:
            raise custom_errors.InvalidInputError("The provided snapshot_id does not match the current playlist state.")
    
    # Get current playlist tracks
    playlist_tracks_table = DB.get('playlist_tracks', {})
    current_tracks = playlist_tracks_table.get(playlist_id, [])
    
    if uris is not None:
        # Replace all tracks
        new_tracks = []
        current_time = utils.format_timestamp()
        
        for uri in uris:
            # Extract track ID from URI
            if uri.startswith('spotify:track:'):
                track_id = uri.replace('spotify:track:', '')
                tracks_table = DB.get('tracks', {})
                track_data = tracks_table.get(track_id)
                
                if track_data:
                    new_track_item = {
                        'added_at': current_time,
                        'added_by': {
                            'id': current_user_id,
                            'display_name': 'Current User',
                            'external_urls': {'spotify': f'https://open.spotify.com/user/{current_user_id}'},
                            'href': f'https://api.spotify.com/v1/users/{current_user_id}',
                            'type': 'user',
                            'uri': f'spotify:user:{current_user_id}'
                        },
                        'is_local': False,
                        'track': track_data
                    }
                    new_tracks.append(new_track_item)
        
        playlist_tracks_table[playlist_id] = new_tracks
    
    elif range_start is not None and insert_before is not None:
        # Reorder tracks
        range_length = range_length or 1
        
        if range_start >= len(current_tracks):
            raise custom_errors.InvalidInputError("range_start is out of bounds.")
        
        if insert_before > len(current_tracks):
            raise custom_errors.InvalidInputError("insert_before is out of bounds.")
        
        # Extract the range of tracks to move
        end_index = min(range_start + range_length, len(current_tracks))
        tracks_to_move = current_tracks[range_start:end_index]
        
        # Remove tracks from their current position
        new_tracks = current_tracks[:range_start] + current_tracks[end_index:]
        
        # Insert tracks at the new position
        new_tracks = new_tracks[:insert_before] + tracks_to_move + new_tracks[insert_before:]
        
        playlist_tracks_table[playlist_id] = new_tracks
    
    else:
        raise custom_errors.InvalidInputError("Either uris must be provided for replacement, or range_start and insert_before must be provided for reordering.")
    
    # Update snapshot_id
    new_snapshot_id = f"snapshot_{utils.generate_base62_id(8)}"
    playlist_data['snapshot_id'] = new_snapshot_id
    
    # Update playlist tracks count
    playlist_data['tracks']['total'] = len(playlist_tracks_table[playlist_id])
    
    # Save changes
    DB['playlists'] = playlists_table
    DB['playlist_tracks'] = playlist_tracks_table
    
    return {
        'snapshot_id': new_snapshot_id
    }
