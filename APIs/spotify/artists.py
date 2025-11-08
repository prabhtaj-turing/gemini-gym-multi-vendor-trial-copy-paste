from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, List, Dict, Any
from datetime import datetime
import copy

from .SimulationEngine.db import DB
from .SimulationEngine import custom_errors, models, utils


@tool_spec(
    spec={
        'name': 'get_artist',
        'description': """ Get Spotify catalog information for a single artist identified by their unique Spotify ID.
        
        This endpoint retrieves comprehensive information about a specific artist including their profile, popularity metrics, genres, and follower count. This is essential for displaying artist pages, creating artist-based recommendations, or providing artist context in music applications. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'artist_id': {
                    'type': 'string',
                    'description': 'The Spotify ID for the artist.'
                }
            },
            'required': [
                'artist_id'
            ]
        }
    }
)
def get_artist(artist_id: str) -> Dict[str, Any]:
    """Get Spotify catalog information for a single artist identified by their unique Spotify ID.

    This endpoint retrieves comprehensive information about a specific artist including their profile, popularity metrics, genres, and follower count. This is essential for displaying artist pages, creating artist-based recommendations, or providing artist context in music applications.

    Args:
        artist_id (str): The Spotify ID for the artist.

    Returns:
        Dict[str, Any]: Artist data with comprehensive information.
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

    Raises:
        InvalidInputError: If artist_id is not a string or is empty.
        NoResultsFoundError: If no artist exists with the specified artist_id.
    """
    # Validate artist_id
    utils.validate_artist_id(artist_id)
    
    # Get artist data from DB
    artists_table = DB.get('artists', {})
    artist_data = artists_table.get(artist_id)
    
    if artist_data is None:
        raise custom_errors.NoResultsFoundError(f"Artist with ID '{artist_id}' not found.")
    
    # Return artist data
    return artist_data


@tool_spec(
    spec={
        'name': 'get_several_artists',
        'description': """ Get Spotify catalog information for several artists based on their Spotify IDs.
        
        This endpoint allows you to retrieve information for multiple artists in a single request, which is more efficient than making individual requests for each artist. The response includes detailed information for each artist, making it ideal for bulk operations or displaying multiple artists in a user interface. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'artist_ids': {
                    'type': 'array',
                    'description': 'A list of the Spotify IDs for the artists. Maximum: 50 IDs.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'artist_ids'
            ]
        }
    }
)
def get_several_artists(artist_ids: List[str]) -> Dict[str, Any]:
    """Get Spotify catalog information for several artists based on their Spotify IDs.

    This endpoint allows you to retrieve information for multiple artists in a single request, which is more efficient than making individual requests for each artist. The response includes detailed information for each artist, making it ideal for bulk operations or displaying multiple artists in a user interface.

    Args:
        artist_ids (List[str]): A list of the Spotify IDs for the artists. Maximum: 50 IDs.

    Returns:
        Dict[str, Any]: Artists response with array of artist objects.
            artists (List[Dict[str, Any]]): Array of artist objects, each containing:
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

    Raises:
        InvalidInputError: If artist_ids is not a list, contains more than 50 items, or any ID is invalid.
        NoResultsFoundError: If none of the specified artists exist.
    """
    # Validate artist_ids
    if not isinstance(artist_ids, list):
        raise custom_errors.InvalidInputError("artist_ids must be a list.")
    
    if not artist_ids:
        raise custom_errors.InvalidInputError("artist_ids cannot be empty.")
    
    if len(artist_ids) > 50:
        raise custom_errors.InvalidInputError("artist_ids cannot contain more than 50 IDs.")
    
    if not all(isinstance(artist_id, str) and artist_id for artist_id in artist_ids):
        raise custom_errors.InvalidInputError("All artist IDs must be non-empty strings.")
    
    # Get artists data from DB
    artists_table = DB.get('artists', {})
    artists_data = []
    
    for artist_id in artist_ids:
        artist_data = artists_table.get(artist_id)
        if artist_data is not None:
            artists_data.append(artist_data)
    
    if not artists_data:
        raise custom_errors.NoResultsFoundError("None of the specified artists were found.")
    
    return {'artists': artists_data}


@tool_spec(
    spec={
        'name': 'get_artists_albums',
        'description': """ Get Spotify catalog information about an artist's albums.
        
        This endpoint retrieves all albums released by a specific artist, with options to filter by album type (album, single, appears_on, compilation) and market availability. The response supports pagination for artists with extensive discographies, making it suitable for displaying artist discographies or creating artist-based playlists. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'artist_id': {
                    'type': 'string',
                    'description': 'The Spotify ID for the artist.'
                },
                'include_groups': {
                    'type': 'string',
                    'description': "A comma-separated list of keywords that will be used to filter the response. If not supplied, all album types will be returned. Valid values are: 'album', 'single', 'appears_on', 'compilation'."
                },
                'market': {
                    'type': 'string',
                    'description': 'An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of albums to return. Default: 20. Minimum: 1. Maximum: 50.'
                },
                'offset': {
                    'type': 'integer',
                    'description': 'The index of the first album to return. Default: 0 (the first object).'
                }
            },
            'required': [
                'artist_id'
            ]
        }
    }
)
def get_artists_albums(
    artist_id: str,
    include_groups: Optional[str] = None,
    market: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """Get Spotify catalog information about an artist's albums.

    This endpoint retrieves all albums released by a specific artist, with options to filter by album type (album, single, appears_on, compilation) and market availability. The response supports pagination for artists with extensive discographies, making it suitable for displaying artist discographies or creating artist-based playlists.

    Args:
        artist_id (str): The Spotify ID for the artist.
        include_groups (Optional[str]): A comma-separated list of keywords that will be used to filter the response. If not supplied, all album types will be returned. Valid values are: 'album', 'single', 'appears_on', 'compilation'.
        market (Optional[str]): An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.
        limit (int): The maximum number of albums to return. Default: 20. Minimum: 1. Maximum: 50.
        offset (int): The index of the first album to return. Default: 0 (the first object).

    Returns:
        Dict[str, Any]: Artist albums response with pagination info.
            items (List[Dict[str, Any]]): Array of album objects, each containing:
                id (str): Unique album identifier
                name (str): Album name
                type (str): Object type ('album')
                uri (str): Spotify URI for the album
                href (str): API endpoint URL for the album
                external_urls (Dict[str, str]): External URLs for the album
                    - spotify (str): The Spotify URL for the album
                artists (List[Dict[str, Any]]): Array of artist objects
                    - external_urls (Dict[str, str]): Known external URLs for this artist
                        - spotify (str): The Spotify URL for the artist
                    - href (str): A link to the Web API endpoint providing full details of the artist
                    - id (str): The Spotify ID for the artist
                    - name (str): The name of the artist
                    - type (str): The object type ('artist')
                    - uri (str): The Spotify URI for the artist
                album_type (str): Type of album ('album', 'single', 'compilation')
                total_tracks (int): Total number of tracks
                available_markets (List[str]): List of markets where album is available
                release_date (str): Release date in YYYY-MM-DD format
                release_date_precision (str): Precision of release date ('year', 'month', 'day')
                images (List[Dict[str, Any]]): Album cover images
                    - url (str): The source URL of the image
                    - height (int): The image height in pixels
                    - width (int): The image width in pixels
                popularity (int): Popularity score (0-100)
            total (int): Total number of albums by the artist
            limit (int): Number of albums returned in this response
            offset (int): Offset of the first album returned
            href (str): URL to the full list of albums
            next (Optional[str]): URL to the next page of results
            previous (Optional[str]): URL to the previous page of results

    Raises:
        InvalidInputError: If artist_id is not a string or is empty, include_groups contains invalid values, market is not a valid country code, limit is outside 1-50 range, or offset is negative.
        NoResultsFoundError: If no artist exists with the specified artist_id.
        InvalidMarketError: If market is not a valid ISO 3166-1 alpha-2 country code.
    """
    # Validate artist_id
    utils.validate_artist_id(artist_id)
    
    # Validate include_groups parameter if provided
    if include_groups is not None:
        if not isinstance(include_groups, str):
            raise custom_errors.InvalidInputError("include_groups must be a string.")
        
        valid_groups = ['album', 'single', 'appears_on', 'compilation']
        include_groups_list = [group.strip() for group in include_groups.split(',')]
        if not all(group in valid_groups for group in include_groups_list):
            raise custom_errors.InvalidInputError(f"include_groups must contain only valid values: {', '.join(valid_groups)}")
    else:
        include_groups_list = None
    
    # Validate market parameter if provided
    if market is not None:
        if not utils.validate_market(market):
            raise custom_errors.InvalidMarketError("market must be a valid ISO 3166-1 alpha-2 country code.")
    
    # Validate limit and offset
    utils.validate_limit_offset(limit, offset)
    
    # Check if artist exists
    artists_table = DB.get('artists', {})
    artist_data = artists_table.get(artist_id)
    
    if artist_data is None:
        raise custom_errors.NoResultsFoundError(f"Artist with ID '{artist_id}' not found.")
    
    # Get albums for this artist
    albums_table = DB.get('albums', {})
    artist_albums = []
    
    for album_id, album_data in albums_table.items():
        album_artists = album_data.get('artists', [])
        if any(artist.get('id') == artist_id for artist in album_artists):
            # Apply include_groups filtering if specified
            if include_groups_list is not None:
                album_type = album_data.get('album_type', 'album')
                if album_type in include_groups_list:
                    artist_albums.append(album_data)
            else:
                artist_albums.append(album_data)
    
    # Apply market filtering if specified
    if market is not None:
        artist_albums = utils.filter_by_market(artist_albums, market)
    
    # Sort albums by release date (newest first)
    artist_albums.sort(key=lambda x: x.get('release_date', ''), reverse=True)
    
    # Apply pagination
    result = utils.apply_pagination(artist_albums, limit, offset)
    result['href'] = f"https://api.spotify.com/v1/artists/{artist_id}/albums"
    
    return result


@tool_spec(
    spec={
        'name': 'get_artists_top_tracks',
        'description': """ Get Spotify catalog information about an artist's top tracks by country.
        
        This endpoint retrieves the most popular tracks by a specific artist in a given market. The tracks are ranked by popularity and can be used to display an artist's most successful songs or create artist-specific playlists. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'artist_id': {
                    'type': 'string',
                    'description': 'The Spotify ID for the artist.'
                },
                'market': {
                    'type': 'string',
                    'description': 'An ISO 3166-1 alpha-2 country code. The country for which to get the top tracks.'
                }
            },
            'required': [
                'artist_id',
                'market'
            ]
        }
    }
)
def get_artists_top_tracks(
    artist_id: str,
    market: str
) -> Dict[str, Any]:
    """Get Spotify catalog information about an artist's top tracks by country.

    This endpoint retrieves the most popular tracks by a specific artist in a given market. The tracks are ranked by popularity and can be used to display an artist's most successful songs or create artist-specific playlists.

    Args:
        artist_id (str): The Spotify ID for the artist.
        market (str): An ISO 3166-1 alpha-2 country code. The country for which to get the top tracks.

    Returns:
        Dict[str, Any]: Artist top tracks response.
            tracks (List[Dict[str, Any]]): Array of track objects, each containing:
                id (str): Unique track identifier
                name (str): Track name
                type (str): Object type ('track')
                uri (str): Spotify URI for the track
                href (str): API endpoint URL for the track
                external_urls (Dict[str, str]): External URLs for the track
                    - spotify (str): The Spotify URL for the track
                artists (List[Dict[str, Any]]): Array of artist objects
                    - external_urls (Dict[str, str]): Known external URLs for this artist
                        - spotify (str): The Spotify URL for the artist
                    - href (str): A link to the Web API endpoint providing full details of the artist
                    - id (str): The Spotify ID for the artist
                    - name (str): The name of the artist
                    - type (str): The object type ('artist')
                    - uri (str): The Spotify URI for the artist
                album (Dict[str, Any]): Album information
                    - id (str): The Spotify ID for the album
                    - name (str): The name of the album
                    - images (List[Dict[str, Any]]): Album cover images
                        - url (str): The source URL of the image
                        - height (int): The image height in pixels
                        - width (int): The image width in pixels
                duration_ms (int): Track duration in milliseconds
                explicit (bool): Whether the track contains explicit content
                track_number (int): Track number on the album
                disc_number (int): Disc number
                available_markets (List[str]): List of markets where track is available
                popularity (int): Popularity score (0-100)
                is_local (bool): Whether the track is a local file
                is_playable (bool): Whether the track is playable

    Raises:
        InvalidInputError: If artist_id is not a string or is empty, or if market is not a valid country code.
        NoResultsFoundError: If no artist exists with the specified artist_id.
        InvalidMarketError: If market is not a valid ISO 3166-1 alpha-2 country code.
    """
    # Validate artist_id
    utils.validate_artist_id(artist_id)
    
    # Validate market parameter
    if not utils.validate_market(market):
        raise custom_errors.InvalidMarketError("market must be a valid ISO 3166-1 alpha-2 country code.")
    
    # Check if artist exists
    artists_table = DB.get('artists', {})
    artist_data = artists_table.get(artist_id)
    
    if artist_data is None:
        raise custom_errors.NoResultsFoundError(f"Artist with ID '{artist_id}' not found.")
    
    # Get top tracks for this artist
    tracks_table = DB.get('tracks', {})
    artist_tracks = []
    
    for track_id, track_data in tracks_table.items():
        track_artists = track_data.get('artists', [])
        if any(artist.get('id') == artist_id for artist in track_artists):
            # Apply market filtering
            available_markets = track_data.get('available_markets', [])
            if market in available_markets:
                artist_tracks.append(track_data)
    
    # Sort tracks by popularity (highest first)
    artist_tracks.sort(key=lambda x: x.get('popularity', 0), reverse=True)
    
    # Return top tracks (limit to top 10)
    return {'tracks': artist_tracks[:10]}


@tool_spec(
    spec={
        'name': 'get_artists_related_artists',
        'description': """ Get Spotify catalog information about artists similar to a given artist.
        
        This endpoint retrieves artists that are similar to the specified artist based on Spotify's similarity algorithm. This is useful for music discovery, creating artist radio stations, or suggesting similar artists to users. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'artist_id': {
                    'type': 'string',
                    'description': 'The Spotify ID for the artist.'
                }
            },
            'required': [
                'artist_id'
            ]
        }
    }
)
def get_artists_related_artists(artist_id: str) -> Dict[str, Any]:
    """Get Spotify catalog information about artists similar to a given artist.

    This endpoint retrieves artists that are similar to the specified artist based on Spotify's similarity algorithm. This is useful for music discovery, creating artist radio stations, or suggesting similar artists to users.

    Args:
        artist_id (str): The Spotify ID for the artist.

    Returns:
        Dict[str, Any]: Related artists response.
            artists (List[Dict[str, Any]]): Array of artist objects, each containing:
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

    Raises:
        InvalidInputError: If artist_id is not a string or is empty.
        NoResultsFoundError: If no artist exists with the specified artist_id.
    """
    # Validate artist_id
    utils.validate_artist_id(artist_id)
    
    # Check if artist exists
    artists_table = DB.get('artists', {})
    artist_data = artists_table.get(artist_id)
    
    if artist_data is None:
        raise custom_errors.NoResultsFoundError(f"Artist with ID '{artist_id}' not found.")
    
    # Get related artists (simulated - in real API this would be based on similarity algorithm)
    # For this simulation, we'll return other artists with similar genres
    artist_genres = set(artist_data.get('genres', []))
    related_artists = []
    
    for other_artist_id, other_artist_data in artists_table.items():
        if other_artist_id != artist_id:
            other_genres = set(other_artist_data.get('genres', []))
            # Check if there's genre overlap
            if artist_genres & other_genres:  # Intersection of genre sets
                related_artists.append(other_artist_data)
    
    # Sort by popularity and limit to top 20
    related_artists.sort(key=lambda x: x.get('popularity', 0), reverse=True)
    
    return {'artists': related_artists[:20]} 