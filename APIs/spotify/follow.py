from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from .SimulationEngine.db import DB
from .SimulationEngine import custom_errors, utils


@tool_spec(
    spec={
        'name': 'follow_playlist',
        'description': """ Add the current user as a follower of a playlist.
        
        This endpoint allows the current user to follow a playlist, which will add it to their library and allow them to receive updates about the playlist. The playlist can be followed publicly or privately, and this setting can be changed later. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'playlist_id': {
                    'type': 'string',
                    'description': """ The Spotify ID for the playlist.
                    Examples: 'playlist_1', '37i9dQZF1DXcBWIGoYBM5M'. """
                },
                'public': {
                    'type': 'boolean',
                    'description': """ Defaults to true. If true the playlist will be included in user's public playlists, if false it will remain private. To be able to follow playlists privately, the user must have granted the playlist-modify-private scope.
                    Examples: True (public), False (private). """
                }
            },
            'required': [
                'playlist_id'
            ]
        }
    }
)
def follow_playlist(playlist_id: str, public: bool = True) -> Dict[str, Any]:
    """Add the current user as a follower of a playlist.

    This endpoint allows the current user to follow a playlist, which will add it to their library and allow them to receive updates about the playlist. The playlist can be followed publicly or privately, and this setting can be changed later.

    Args:
        playlist_id (str): The Spotify ID for the playlist.
            Examples: 'playlist_1', '37i9dQZF1DXcBWIGoYBM5M'.
        public (bool): Defaults to true. If true the playlist will be included in user's public playlists, if false it will remain private. To be able to follow playlists privately, the user must have granted the playlist-modify-private scope.
            Examples: True (public), False (private).

    Returns:
        Dict[str, Any]: Success response indicating the playlist was followed.
            message (str): Success message

    Raises:
        InvalidInputError: If playlist_id is not a string or is empty, or if public is not a boolean.
        NoResultsFoundError: If no playlist exists with the specified playlist_id.
        AuthenticationError: If user is not authenticated.
        AuthorizationError: If user does not have required permissions.
    """
    # Validate playlist_id
    utils.validate_playlist_id(playlist_id)

    # Validate public parameter
    if not isinstance(public, bool):
        raise custom_errors.InvalidInputError("public must be a boolean.")

    # Get current user from DB (in a real implementation, this would come from auth token)
    current_user_id = utils.get_current_user_id()

    # Check if playlist exists
    playlists_table = DB.get('playlists', {})
    playlist_data = playlists_table.get(playlist_id)

    if playlist_data is None:
        raise custom_errors.NoResultsFoundError(f"Playlist with ID '{playlist_id}' not found.")

    # Add playlist to user's followed playlists with metadata
    followed_playlists_table = DB.get('followed_playlists', {})
    if current_user_id not in followed_playlists_table:
        followed_playlists_table[current_user_id] = {}

    # Store follow with metadata (public setting and timestamp)
    followed_playlists_table[current_user_id][playlist_id] = {
        "public": public,
        "followed_at": datetime.now(timezone.utc).isoformat()
    }

    return {"message": f"Successfully followed playlist '{playlist_id}'."}


@tool_spec(
    spec={
        'name': 'unfollow_playlist',
        'description': """ Remove the current user as a follower of a playlist.
        
        This endpoint allows the current user to unfollow a playlist, which will remove it from their library and stop receiving updates about the playlist. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'playlist_id': {
                    'type': 'string',
                    'description': """ The Spotify ID for the playlist.
                    Examples: 'playlist_1', '37i9dQZF1DXcBWIGoYBM5M'. """
                }
            },
            'required': [
                'playlist_id'
            ]
        }
    }
)
def unfollow_playlist(playlist_id: str) -> Dict[str, Any]:
    """Remove the current user as a follower of a playlist.

    This endpoint allows the current user to unfollow a playlist, which will remove it from their library and stop receiving updates about the playlist.

    Args:
        playlist_id (str): The Spotify ID for the playlist.
            Examples: 'playlist_1', '37i9dQZF1DXcBWIGoYBM5M'.

    Returns:
        Dict[str, Any]: Success response indicating the playlist was unfollowed.
            message (str): Success message

    Raises:
        InvalidInputError: If playlist_id is not a string or is empty.
        NoResultsFoundError: If no playlist exists with the specified playlist_id.
        AuthenticationError: If user is not authenticated.
        AuthorizationError: If user does not have required permissions.
    """
    # Validate playlist_id
    utils.validate_playlist_id(playlist_id)

    # Get current user from DB (in a real implementation, this would come from auth token)
    current_user_id = utils.get_current_user_id()

    # Check if playlist exists
    playlists_table = DB.get('playlists', {})
    playlist_data = playlists_table.get(playlist_id)

    if playlist_data is None:
        raise custom_errors.NoResultsFoundError(f"Playlist with ID '{playlist_id}' not found.")

    # Remove playlist from user's followed playlists
    followed_playlists_table = DB.get('followed_playlists', {})
    if current_user_id in followed_playlists_table:
        if playlist_id in followed_playlists_table[current_user_id]:
            del followed_playlists_table[current_user_id][playlist_id]

    return {"message": f"Successfully unfollowed playlist '{playlist_id}'."}


@tool_spec(
    spec={
        'name': 'follow_artists_or_users',
        'description': """ Add the current user as a follower of one or more artists or users.
        
        This endpoint allows the current user to follow multiple artists or users at once. Following an artist will add their music to the user's recommendations and allow them to receive updates about the artist. Following a user will allow them to see the user's public playlists and activity. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'ids': {
                    'type': 'array',
                    'description': """ A list of the Spotify IDs for the artists or users. Maximum: 50 IDs.
                    Examples: ['0TnOYISbd1XYRBk9myaseg', '3HqSLMAZ3g3d5poNaI7GOU'] for artists,
                    ['smuqPNFPXrJKcEt943KrY8', 'SLvTb0e3Rp3oLJ8YXl0dC5'] for users. """,
                    'items': {
                        'type': 'string'
                    }
                },
                'type': {
                    'type': 'string',
                    'description': 'The type of items to follow. Must be either "artist" or "user".'
                }
            },
            'required': [
                'ids',
                'type'
            ]
        }
    }
)
def follow_artists_or_users(ids: List[str], type: str) -> Dict[str, Any]:
    """Add the current user as a follower of one or more artists or users.

    This endpoint allows the current user to follow multiple artists or users at once. Following an artist will add their music to the user's recommendations and allow them to receive updates about the artist. Following a user will allow them to see the user's public playlists and activity.

    Args:
        ids (List[str]): A list of the Spotify IDs for the artists or users. Maximum: 50 IDs.
            Examples: ['0TnOYISbd1XYRBk9myaseg', '3HqSLMAZ3g3d5poNaI7GOU'] for artists,
                     ['smuqPNFPXrJKcEt943KrY8', 'SLvTb0e3Rp3oLJ8YXl0dC5'] for users.
        type (str): The type of items to follow. Must be either "artist" or "user".

    Returns:
        Dict[str, Any]: Success response indicating the items were followed.
            message (str): Success message

    Raises:
        InvalidInputError: If ids is not a list, contains more than 50 IDs, contains invalid IDs, or type is invalid.
        NoResultsFoundError: If none of the specified artists or users exist.
        AuthenticationError: If user is not authenticated.
        AuthorizationError: If user does not have required permissions.
    """
    # Validate type parameter
    if type not in ["artist", "user"]:
        raise custom_errors.InvalidInputError("type must be either 'artist' or 'user'.")

    # Validate ids
    if not isinstance(ids, list):
        raise custom_errors.InvalidInputError("ids must be a list.")

    if not ids:
        raise custom_errors.InvalidInputError("ids cannot be empty.")

    if len(ids) > 50:
        raise custom_errors.InvalidInputError("ids cannot contain more than 50 IDs.")

    if not all(isinstance(item_id, str) and item_id for item_id in ids):
        raise custom_errors.InvalidInputError("All IDs must be non-empty strings.")

    # Get current user from DB (in a real implementation, this would come from auth token)
    current_user_id = utils.get_current_user_id()

    if type == "artist":
        # Check if artists exist
        artists_table = DB.get('artists', {})
        for artist_id in ids:
            if artist_id not in artists_table:
                raise custom_errors.NoResultsFoundError(f"Artist with ID '{artist_id}' not found.")

        # Add artists to user's followed artists
        followed_artists_table = DB.get('followed_artists', {})
        if current_user_id not in followed_artists_table:
            followed_artists_table[current_user_id] = []

        for artist_id in ids:
            if artist_id not in followed_artists_table[current_user_id]:
                followed_artists_table[current_user_id].append(artist_id)

        return {"message": f"Successfully followed {len(ids)} artist(s)."}

    else:  # type == "user"
        # Check if users exist
        users_table = DB.get('users', {})
        for user_id in ids:
            if user_id not in users_table:
                raise custom_errors.NoResultsFoundError(f"User with ID '{user_id}' not found.")

        # Add users to current user's followed users
        followed_users_table = DB.get('followed_users', {})
        if current_user_id not in followed_users_table:
            followed_users_table[current_user_id] = []

        for user_id in ids:
            if user_id not in followed_users_table[current_user_id]:
                followed_users_table[current_user_id].append(user_id)

        return {"message": f"Successfully followed {len(ids)} user(s)."}


@tool_spec(
    spec={
        'name': 'unfollow_artists_or_users',
        'description': """ Remove the current user as a follower of one or more artists or users.
        
        This endpoint allows the current user to unfollow multiple artists or users at once. Unfollowing an artist will remove their music from the user's recommendations and stop receiving updates about the artist. Unfollowing a user will stop seeing their public playlists and activity. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'ids': {
                    'type': 'array',
                    'description': """ A list of the Spotify IDs for the artists or users. Maximum: 50 IDs.
                    Examples: ['0TnOYISbd1XYRBk9myaseg', '3HqSLMAZ3g3d5poNaI7GOU'] for artists,
                    ['smuqPNFPXrJKcEt943KrY8', 'SLvTb0e3Rp3oLJ8YXl0dC5'] for users. """,
                    'items': {
                        'type': 'string'
                    }
                },
                'type': {
                    'type': 'string',
                    'description': 'The type of items to unfollow. Must be either "artist" or "user".'
                }
            },
            'required': [
                'ids',
                'type'
            ]
        }
    }
)
def unfollow_artists_or_users(ids: List[str], type: str) -> Dict[str, Any]:
    """Remove the current user as a follower of one or more artists or users.

    This endpoint allows the current user to unfollow multiple artists or users at once. Unfollowing an artist will remove their music from the user's recommendations and stop receiving updates about the artist. Unfollowing a user will stop seeing their public playlists and activity.

    Args:
        ids (List[str]): A list of the Spotify IDs for the artists or users. Maximum: 50 IDs.
            Examples: ['0TnOYISbd1XYRBk9myaseg', '3HqSLMAZ3g3d5poNaI7GOU'] for artists,
                     ['smuqPNFPXrJKcEt943KrY8', 'SLvTb0e3Rp3oLJ8YXl0dC5'] for users.
        type (str): The type of items to unfollow. Must be either "artist" or "user".

    Returns:
        Dict[str, Any]: Success response indicating the items were unfollowed.
            message (str): Success message

    Raises:
        InvalidInputError: If ids is not a list, contains more than 50 IDs, contains invalid IDs, or type is invalid.
        NoResultsFoundError: If none of the specified artists or users exist.
        AuthenticationError: If user is not authenticated.
        AuthorizationError: If user does not have required permissions.
    """
    # Validate type parameter
    if type not in ["artist", "user"]:
        raise custom_errors.InvalidInputError("type must be either 'artist' or 'user'.")

    # Validate ids
    if not isinstance(ids, list):
        raise custom_errors.InvalidInputError("ids must be a list.")

    if not ids:
        raise custom_errors.InvalidInputError("ids cannot be empty.")

    if len(ids) > 50:
        raise custom_errors.InvalidInputError("ids cannot contain more than 50 IDs.")

    if not all(isinstance(item_id, str) and item_id for item_id in ids):
        raise custom_errors.InvalidInputError("All IDs must be non-empty strings.")

    # Get current user from DB (in a real implementation, this would come from auth token)
    current_user_id = utils.get_current_user_id()

    if type == "artist":
        # Check if artists exist
        artists_table = DB.get('artists', {})
        for artist_id in ids:
            if artist_id not in artists_table:
                raise custom_errors.NoResultsFoundError(f"Artist with ID '{artist_id}' not found.")

        # Remove artists from user's followed artists
        followed_artists_table = DB.get('followed_artists', {})
        if current_user_id in followed_artists_table:
            for artist_id in ids:
                if artist_id in followed_artists_table[current_user_id]:
                    followed_artists_table[current_user_id].remove(artist_id)

        return {"message": f"Successfully unfollowed {len(ids)} artist(s)."}

    else:  # type == "user"
        # Check if users exist
        users_table = DB.get('users', {})
        for user_id in ids:
            if user_id not in users_table:
                raise custom_errors.NoResultsFoundError(f"User with ID '{user_id}' not found.")

        # Remove users from current user's followed users
        followed_users_table = DB.get('followed_users', {})
        if current_user_id in followed_users_table:
            for user_id in ids:
                if user_id in followed_users_table[current_user_id]:
                    followed_users_table[current_user_id].remove(user_id)

        return {"message": f"Successfully unfollowed {len(ids)} user(s)."}


@tool_spec(
    spec={
        'name': 'check_user_follows_playlist',
        'description': """ Check to see if the one or more users are following a specified playlist.
        
        This endpoint allows you to check the follow status of multiple users for a specific playlist. This is useful for displaying follow/unfollow buttons or understanding the social reach of a playlist. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'playlist_id': {
                    'type': 'string',
                    'description': """ The Spotify ID for the playlist.
                    Examples: 'playlist_1', '37i9dQZF1DXcBWIGoYBM5M'. """
                },
                'user_ids': {
                    'type': 'array',
                    'description': """ A list of the Spotify IDs for the users. Maximum: 5 IDs.
                    Examples: ['smuqPNFPXrJKcEt943KrY8', 'SLvTb0e3Rp3oLJ8YXl0dC5']. """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'playlist_id',
                'user_ids'
            ]
        }
    }
)
def check_user_follows_playlist(playlist_id: str, user_ids: List[str]) -> List[bool]:
    """Check to see if the one or more users are following a specified playlist.

    This endpoint allows you to check the follow status of multiple users for a specific playlist. This is useful for displaying follow/unfollow buttons or understanding the social reach of a playlist.

    Args:
        playlist_id (str): The Spotify ID for the playlist.
            Examples: 'playlist_1', '37i9dQZF1DXcBWIGoYBM5M'.
        user_ids (List[str]): A list of the Spotify IDs for the users. Maximum: 5 IDs.
            Examples: ['smuqPNFPXrJKcEt943KrY8', 'SLvTb0e3Rp3oLJ8YXl0dC5'].

    Returns:
        List[bool]: Array of boolean values indicating whether each user is following the playlist.
            True if the user is following the playlist, False otherwise.

    Raises:
        InvalidInputError: If playlist_id is not a string or is empty, user_ids is not a list, contains more than 5 IDs, or contains invalid user IDs.
        NoResultsFoundError: If no playlist exists with the specified playlist_id.
        AuthenticationError: If user is not authenticated.
        AuthorizationError: If user does not have required permissions.
    """
    # Validate playlist_id
    utils.validate_playlist_id(playlist_id)

    # Validate user_ids
    if not isinstance(user_ids, list):
        raise custom_errors.InvalidInputError("user_ids must be a list.")

    if not user_ids:
        raise custom_errors.InvalidInputError("user_ids cannot be empty.")

    if len(user_ids) > 5:
        raise custom_errors.InvalidInputError("user_ids cannot contain more than 5 IDs.")

    if not all(isinstance(user_id, str) and user_id for user_id in user_ids):
        raise custom_errors.InvalidInputError("All user IDs must be non-empty strings.")

    # Check if playlist exists
    playlists_table = DB.get('playlists', {})
    playlist_data = playlists_table.get(playlist_id)

    if playlist_data is None:
        raise custom_errors.NoResultsFoundError(f"Playlist with ID '{playlist_id}' not found.")

    # Check follow status for each user
    followed_playlists_table = DB.get('followed_playlists', {})
    follow_status = []

    for user_id in user_ids:
        user_followed_playlists = followed_playlists_table.get(user_id, [])
        follow_status.append(playlist_id in user_followed_playlists)

    return follow_status


@tool_spec(
    spec={
        'name': 'check_user_follows_artists_or_users',
        'description': """ Check if the current user follows one or more artists or users.
        
        This endpoint allows you to check the follow status of the current user for multiple artists or users. This is useful for displaying follow/unfollow buttons or understanding the user's music preferences and social connections. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'ids': {
                    'type': 'array',
                    'description': """ A list of the Spotify IDs for the artists or users. Maximum: 50 IDs.
                    Examples: ['0TnOYISbd1XYRBk9myaseg', '3HqSLMAZ3g3d5poNaI7GOU'] for artists,
                    ['smuqPNFPXrJKcEt943KrY8', 'SLvTb0e3Rp3oLJ8YXl0dC5'] for users. """,
                    'items': {
                        'type': 'string'
                    }
                },
                'type': {
                    'type': 'string',
                    'description': 'The type of items to check. Must be either "artist" or "user".'
                }
            },
            'required': [
                'ids',
                'type'
            ]
        }
    }
)
def check_user_follows_artists_or_users(ids: List[str], type: str) -> List[bool]:
    """Check if the current user follows one or more artists or users.

    This endpoint allows you to check the follow status of the current user for multiple artists or users. This is useful for displaying follow/unfollow buttons or understanding the user's music preferences and social connections.

    Args:
        ids (List[str]): A list of the Spotify IDs for the artists or users. Maximum: 50 IDs.
            Examples: ['0TnOYISbd1XYRBk9myaseg', '3HqSLMAZ3g3d5poNaI7GOU'] for artists,
                     ['smuqPNFPXrJKcEt943KrY8', 'SLvTb0e3Rp3oLJ8YXl0dC5'] for users.
        type (str): The type of items to check. Must be either "artist" or "user".

    Returns:
        List[bool]: Array of boolean values indicating whether the current user follows each item.
            True if the user follows the item, False otherwise.

    Raises:
        InvalidInputError: If ids is not a list, contains more than 50 IDs, contains invalid IDs, or type is invalid.
        NoResultsFoundError: If none of the specified artists or users exist.
        AuthenticationError: If user is not authenticated.
        AuthorizationError: If user does not have required permissions.
    """
    # Validate type parameter
    if type not in ["artist", "user"]:
        raise custom_errors.InvalidInputError("type must be either 'artist' or 'user'.")

    # Validate ids
    if not isinstance(ids, list):
        raise custom_errors.InvalidInputError("ids must be a list.")

    if not ids:
        raise custom_errors.InvalidInputError("ids cannot be empty.")

    if len(ids) > 50:
        raise custom_errors.InvalidInputError("ids cannot contain more than 50 IDs.")

    if not all(isinstance(item_id, str) and item_id for item_id in ids):
        raise custom_errors.InvalidInputError("All IDs must be non-empty strings.")

    # Get current user from DB (in a real implementation, this would come from auth token)
    current_user_id = utils.get_current_user_id()

    if type == "artist":
        # Check if artists exist
        artists_table = DB.get('artists', {})
        for artist_id in ids:
            if artist_id not in artists_table:
                raise custom_errors.NoResultsFoundError(f"Artist with ID '{artist_id}' not found.")

        # Check follow status for each artist
        followed_artists_table = DB.get('followed_artists', {})
        user_followed_artists = followed_artists_table.get(current_user_id, [])
        follow_status = []

        for artist_id in ids:
            follow_status.append(artist_id in user_followed_artists)

        return follow_status

    else:  # type == "user"
        # Check if users exist
        users_table = DB.get('users', {})
        for user_id in ids:
            if user_id not in users_table:
                raise custom_errors.NoResultsFoundError(f"User with ID '{user_id}' not found.")

        # Check follow status for each user
        followed_users_table = DB.get('followed_users', {})
        user_followed_users = followed_users_table.get(current_user_id, [])
        follow_status = []

        for user_id in ids:
            follow_status.append(user_id in user_followed_users)

        return follow_status


@tool_spec(
    spec={
        'name': 'get_followed_artists',
        'description': """ Get the artists that the current user follows.
        
        This endpoint retrieves all artists that the current user is following. The response includes detailed artist information and supports pagination for efficient data retrieval. This is essential for displaying the user's followed artists, creating artist-based recommendations, or managing user preferences. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'limit': {
                    'type': 'integer',
                    'description': """ The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
                    Examples: 10 (small selection), 20 (default), 50 (maximum). """
                },
                'after': {
                    'type': 'string',
                    'description': """ The last artist ID retrieved from the previous request. Used for pagination.
                    Examples: '0TnOYISbd1XYRBk9myaseg', '3HqSLMAZ3g3d5poNaI7GOU'. """
                }
            },
            'required': []
        }
    }
)
def get_followed_artists(limit: int = 20, after: Optional[str] = None) -> Dict[str, Any]:
    """Get the artists that the current user follows.

    This endpoint retrieves all artists that the current user is following. The response includes detailed artist information and supports pagination for efficient data retrieval. This is essential for displaying the user's followed artists, creating artist-based recommendations, or managing user preferences.

    Args:
        limit (int): The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
            Examples: 10 (small selection), 20 (default), 50 (maximum).
        after (Optional[str]): The last artist ID retrieved from the previous request. Used for pagination.
            Examples: '0TnOYISbd1XYRBk9myaseg', '3HqSLMAZ3g3d5poNaI7GOU'.

    Returns:
        Dict[str, Any]: Followed artists response with pagination info.
            artists (Dict[str, Any]): Artists response containing:
                items (List[Dict[str, Any]]): Array of artist objects, each containing:
                    id (str): Unique artist identifier
                    name (str): Artist name
                    type (str): Object type ('artist')
                    uri (str): Spotify URI for the artist
                    href (str): API endpoint URL for the artist
                    external_urls (Dict[str, str]): External URLs for the artist
                        - spotify (str): The Spotify URL for the artist
                    followers (Dict[str, Any]): Follower information with total count
                        - href (str): A link to the Web API endpoint providing full details of the followers
                        - total (int): The total number of followers
                    genres (List[str]): Array of genres associated with the artist
                    images (List[Dict[str, Any]]): Artist profile images
                        - url (str): The source URL of the image
                        - height (int): The image height in pixels
                        - width (int): The image width in pixels
                    popularity (int): Popularity score (0-100)
                total (int): Total number of followed artists
                limit (int): Number of artists returned in this response
                offset (int): Offset of the first artist returned
                href (str): URL to the full list of followed artists
                next (Optional[str]): URL to the next page of results
                previous (Optional[str]): URL to the previous page of results

    Raises:
        InvalidInputError: If limit is outside 1-50 range or after is not a valid artist ID.
        AuthenticationError: If user is not authenticated.
        AuthorizationError: If user does not have required permissions.
    """
    # Validate limit parameter
    if limit is not None:
        if not isinstance(limit, int) or limit < 1 or limit > 50:
            raise custom_errors.InvalidInputError("limit must be an integer between 1 and 50.")

    # Validate after parameter if provided
    if after is not None:
        if not isinstance(after, str) or not after:
            raise custom_errors.InvalidInputError("after must be a non-empty string.")
        # Check if the artist exists
        artists_table = DB.get('artists', {})
        if after not in artists_table:
            raise custom_errors.InvalidInputError(f"Artist with ID '{after}' not found.")

    # Get current user from DB (in a real implementation, this would come from auth token)
    current_user_id = utils.get_current_user_id()

    # Get user's followed artists
    followed_artists_table = DB.get('followed_artists', {})
    user_followed_artists = followed_artists_table.get(current_user_id, [])

    if not user_followed_artists:
        # Return empty response if user follows no artists
        return {
            'artists': {
                'items': [],
                'total': 0,
                'limit': limit or 20,
                'offset': 0,
                'href': 'https://api.spotify.com/v1/me/following?type=artist',
                'next': None,
                'previous': None
            }
        }

    # Get full artist data for followed artists
    artists_table = DB.get('artists', {})
    followed_artists_data = []

    for artist_id in user_followed_artists:
        if artist_id in artists_table:
            followed_artists_data.append(artists_table[artist_id])

    # Apply pagination based on after parameter
    if after:
        # Find the index of the artist after which we should start
        try:
            after_index = user_followed_artists.index(after)
            # Start from the next artist after the 'after' artist
            followed_artists_data = followed_artists_data[after_index + 1:]
        except ValueError:
            # If after artist not found in followed list, start from beginning
            pass

    # Apply limit
    if limit:
        followed_artists_data = followed_artists_data[:limit]

    # Calculate offset for pagination
    offset = 0
    if after:
        try:
            after_index = user_followed_artists.index(after)
            offset = after_index + 1
        except ValueError:
            offset = 0

    # Construct response
    response = {
        'artists': {
            'items': followed_artists_data,
            'total': len(user_followed_artists),
            'limit': limit or 20,
            'offset': offset,
            'href': 'https://api.spotify.com/v1/me/following?type=artist',
            'next': None,
            'previous': None
        }
    }

    # Add pagination links if applicable
    if len(followed_artists_data) == (limit or 20) and offset + (limit or 20) < len(user_followed_artists):
        # There are more artists to fetch
        next_artist_id = user_followed_artists[offset + (limit or 20) - 1]
        response['artists'][
            'next'] = f"https://api.spotify.com/v1/me/following?type=artist&limit={limit or 20}&after={next_artist_id}"

    if offset > 0:
        # There are previous artists
        prev_artist_id = user_followed_artists[max(0, offset - 1)]
        response['artists'][
            'previous'] = f"https://api.spotify.com/v1/me/following?type=artist&limit={limit or 20}&after={prev_artist_id}"

    return response
