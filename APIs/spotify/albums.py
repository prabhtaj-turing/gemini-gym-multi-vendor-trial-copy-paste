from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, List, Dict, Any
from datetime import datetime
import copy

from .SimulationEngine.db import DB
from .SimulationEngine import custom_errors, utils


@tool_spec(
    spec={
        'name': 'get_album',
        'description': """ Get Spotify catalog information for a single album.
        
        This endpoint retrieves detailed information about a specific album including its tracks, artists, release date, and metadata. This is essential for displaying album information, track listings, and album details in music applications. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'album_id': {
                    'type': 'string',
                    'description': 'The Spotify ID for the album.'
                },
                'market': {
                    'type': 'string',
                    'description': 'An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.'
                }
            },
            'required': [
                'album_id'
            ]
        }
    }
)
def get_album(album_id: str, market: Optional[str] = None) -> Dict[str, Any]:
    """Get Spotify catalog information for a single album.

    This endpoint retrieves detailed information about a specific album including its tracks, artists, release date, and metadata. This is essential for displaying album information, track listings, and album details in music applications.

    Args:
        album_id (str): The Spotify ID for the album.
        market (Optional[str]): An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.

    Returns:
        Dict[str, Any]: Album object with comprehensive information.
            id (str): Unique album identifier
            name (str): Album name
            type (str): The type of the album ('album')
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
            restrictions (Optional[Dict[str, Any]]): Album restrictions if any
                - reason (str): The reason for the restriction ('market', 'product', 'explicit')
            tracks (Dict[str, Any]): Album tracks information
                - href (str): A link to the Web API endpoint providing full details of the tracks
                - limit (int): The maximum number of tracks in the response
                - next (Optional[str]): URL to the next page of results
                - offset (int): The offset of the items returned
                - previous (Optional[str]): URL to the previous page of results
                - total (int): The total number of tracks available
                - items (List[Dict[str, Any]]): Array of simplified track objects
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
                    - track_number (int): The number of the track
                    - type (str): The object type ('track')
                    - uri (str): The Spotify URI for the track
                    - is_local (bool): Whether the track is from a local file
            copyrights (List[Dict[str, Any]]): The copyright statements of the album
                - text (str): The copyright text for this content
                - type (str): The type of copyright ('C' = copyright, 'P' = performance copyright)
            external_ids (Dict[str, str]): Known external IDs for the album
                - isrc (str): International Standard Recording Code
                - ean (str): International Article Number
                - upc (str): Universal Product Code
            label (str): The label associated with the album

    Raises:
        InvalidInputError: If album_id is not a string or is empty, or if market is not a valid country code.
        NoResultsFoundError: If no album exists with the specified album_id or if album is not available in the specified market.
        InvalidMarketError: If market is not a valid ISO 3166-1 alpha-2 country code.
    """
    # Validate album_id
    utils.validate_album_id(album_id)

    # Validate market parameter if provided
    if market is not None:
        if not utils.validate_market(market):
            raise custom_errors.InvalidMarketError("market must be a valid ISO 3166-1 alpha-2 country code.")

    # Get album data from DB
    albums_table = DB.get('albums')
    album_data = albums_table.get(album_id)

    if album_data is None:
        raise custom_errors.NoResultsFoundError(f"Album with ID '{album_id}' not found.")

    # Apply market filtering if specified
    if market is not None:
        available_markets = album_data.get('available_markets', [])
        if market not in available_markets:
            raise custom_errors.NoResultsFoundError(f"Album '{album_id}' is not available in market '{market}'.")

    # Create a copy of the album data to avoid modifying the original
    album_response = copy.deepcopy(album_data)

    # Enhance artist objects to match official Spotify API structure
    if 'artists' in album_response:
        for artist in album_response['artists']:
            if 'id' in artist:
                artist_id = artist['id']
                # Add missing fields to match official API structure
                artist['external_urls'] = {
                    'spotify': f"https://open.spotify.com/artist/{artist_id}"
                }
                artist['href'] = f"https://api.spotify.com/v1/artists/{artist_id}"
                artist['type'] = 'artist'
                artist['uri'] = f"spotify:artist:{artist_id}"

    # Add tracks information to match official Spotify API structure
    tracks_table = DB.get('tracks')
    album_tracks = []

    for track_id, track_data in tracks_table.items():
        track_album = track_data.get('album', {})
        if track_album.get('id') == album_id:
            # Apply market filtering if specified
            if market is not None:
                available_markets = track_data.get('available_markets', [])
                if market in available_markets:
                    album_tracks.append(track_data)
            else:
                album_tracks.append(track_data)

    # Sort tracks by disc number and track number
    album_tracks.sort(key=lambda x: (x.get('disc_number', 1), x.get('track_number', 1)))

    # Create tracks object with pagination info
    tracks_info = {
        'href': f"https://api.spotify.com/v1/albums/{album_id}/tracks",
        'limit': 20,
        'next': None,
        'offset': 0,
        'previous': None,
        'total': len(album_tracks),
        'items': album_tracks
    }

    # Add tracks to album response
    album_response['tracks'] = tracks_info

    return album_response


@tool_spec(
    spec={
        'name': 'get_several_albums',
        'description': """ Get Spotify catalog information for multiple albums.
        
        This endpoint retrieves detailed information about multiple albums in a single request. This is useful for efficiently fetching data for multiple albums, such as when displaying album collections or batch processing. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'album_ids': {
                    'type': 'array',
                    'description': 'A list of the Spotify IDs for the albums. Maximum: 20 IDs.',
                    'items': {
                        'type': 'string'
                    }
                },
                'market': {
                    'type': 'string',
                    'description': 'An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.'
                }
            },
            'required': [
                'album_ids'
            ]
        }
    }
)
def get_several_albums(album_ids: List[str], market: Optional[str] = None) -> Dict[str, Any]:
    """Get Spotify catalog information for multiple albums.

    This endpoint retrieves detailed information about multiple albums in a single request. This is useful for efficiently fetching data for multiple albums, such as when displaying album collections or batch processing.

    Args:
        album_ids (List[str]): A list of the Spotify IDs for the albums. Maximum: 20 IDs.
        market (Optional[str]): An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.

    Returns:
        Dict[str, Any]: Response containing an array of album objects.
            albums (List[Dict[str, Any]]): Array of album objects, each containing:
                id (str): Unique album identifier
                name (str): Album name
                type (str): The type of the album ('album')
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
                restrictions (Optional[Dict[str, Any]]): Album restrictions if any
                    - reason (str): The reason for the restriction ('market', 'product', 'explicit')
                tracks (Dict[str, Any]): Album tracks information
                    - href (str): A link to the Web API endpoint providing full details of the tracks
                    - limit (int): The maximum number of tracks in the response
                    - next (Optional[str]): URL to the next page of results
                    - offset (int): The offset of the items returned
                    - previous (Optional[str]): URL to the previous page of results
                    - total (int): The total number of tracks available
                    - items (List[Dict[str, Any]]): Array of simplified track objects
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

                        - track_number (int): The number of the track
                        - type (str): The object type ('track')
                        - uri (str): The Spotify URI for the track
                        - is_local (bool): Whether the track is from a local file
                copyrights (List[Dict[str, Any]]): The copyright statements of the album
                    - text (str): The copyright text for this content
                    - type (str): The type of copyright ('C' = copyright, 'P' = performance copyright)
                external_ids (Dict[str, str]): Known external IDs for the album
                    - isrc (str): International Standard Recording Code
                    - ean (str): International Article Number
                    - upc (str): Universal Product Code

                label (str): The label associated with the album
                Note: Albums that don't exist will be returned as null in the array.

    Raises:
        InvalidInputError: If album_ids is not a list, contains more than 20 IDs, contains invalid album IDs, or if market is not a valid country code.
    """
    # Validate album_ids
    if not isinstance(album_ids, list):
        raise custom_errors.InvalidInputError("album_ids must be a list.")

    if len(album_ids) > 20:
        raise custom_errors.InvalidInputError("album_ids cannot contain more than 20 IDs.")

    if not all(isinstance(album_id, str) and album_id for album_id in album_ids):
        raise custom_errors.InvalidInputError("All album IDs must be non-empty strings.")

    # Validate market parameter if provided
    if market is not None:
        if not utils.validate_market(market):
            raise custom_errors.InvalidMarketError("market must be a valid ISO 3166-1 alpha-2 country code.")

    albums_data = []
    for album_id in album_ids:
        try:
            album_obj = get_album(album_id, market)
            albums_data.append(album_obj)
        except custom_errors.NoResultsFoundError:
            albums_data.append(None)
    return {"albums": albums_data}


@tool_spec(
    spec={
        'name': 'get_album_tracks',
        'description': """ Get Spotify catalog information about an album's tracks.
        
        This endpoint retrieves all tracks from a specific album with optional pagination and market filtering. This is useful for displaying track listings, creating playlists, or analyzing album content. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'album_id': {
                    'type': 'string',
                    'description': 'The Spotify ID for the album.'
                },
                'market': {
                    'type': 'string',
                    'description': 'An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of tracks to return. Default: 20. Minimum: 1. Maximum: 50.'
                },
                'offset': {
                    'type': 'integer',
                    'description': 'The index of the first track to return. Default: 0 (the first object).'
                }
            },
            'required': [
                'album_id'
            ]
        }
    }
)
def get_album_tracks(
        album_id: str,
        market: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
) -> Dict[str, Any]:
    """Get Spotify catalog information about an album's tracks.

    This endpoint retrieves all tracks from a specific album with optional pagination and market filtering. This is useful for displaying track listings, creating playlists, or analyzing album content.

    Args:
        album_id (str): The Spotify ID for the album.
        market (Optional[str]): An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.
        limit (int): The maximum number of tracks to return. Default: 20. Minimum: 1. Maximum: 50.
        offset (int): The index of the first track to return. Default: 0 (the first object).

    Returns:
        Dict[str, Any]: Album tracks response with pagination info.
            items (List[Dict[str, Any]]): Array of simplified track objects, each containing:
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
                    - uri (str): Spotify URI for the album
                    - href (str): API endpoint URL for the album
                    - external_urls (Dict[str, str]): External URLs for the album
                        - spotify (str): The Spotify URL for the album
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
                external_ids (Dict[str, str]): Known external IDs for the track
                    - isrc (str): International Standard Recording Code
                linked_from (Optional[Dict[str, Any]]): Information about the originally requested track when Track Relinking is applied
                restrictions (Optional[Dict[str, Any]]): Track restrictions if any
                    - reason (str): The reason for the restriction
                preview_url (Optional[str]): A URL to a 30 second preview (MP3 format) of the track
            total (int): Total number of tracks in the album
            limit (int): Number of tracks returned in this response
            offset (int): Offset of the first track returned
            href (str): URL to the full list of tracks
            next (Optional[str]): URL to the next page of results
            previous (Optional[str]): URL to the previous page of results

    Raises:
        InvalidInputError: If album_id is not a string or is empty, market is not a valid country code, limit is outside 1-50 range, or offset is negative.
        NoResultsFoundError: If no album exists with the specified album_id.
    """
    # Validate album_id
    utils.validate_album_id(album_id)

    # Validate market parameter if provided
    if market is not None:
        if not utils.validate_market(market):
            raise custom_errors.InvalidMarketError("market must be a valid ISO 3166-1 alpha-2 country code.")

    # Validate limit and offset
    utils.validate_limit_offset(limit, offset)

    # Get album data from DB
    albums_table = DB.get('albums')
    album_data = albums_table.get(album_id)

    if album_data is None:
        raise custom_errors.NoResultsFoundError(f"Album with ID '{album_id}' not found.")

    # Get tracks for this album
    tracks_table = DB.get('tracks')
    album_tracks = []

    for track_id, track_data in tracks_table.items():
        track_album = track_data.get('album', {})
        if track_album.get('id') == album_id:
            # Apply market filtering if specified
            if market is not None:
                available_markets = track_data.get('available_markets', [])
                if market in available_markets:
                    album_tracks.append(track_data)
            else:
                album_tracks.append(track_data)

    # Sort tracks by disc number and track number
    album_tracks.sort(key=lambda x: (x.get('disc_number', 1), x.get('track_number', 1)))

    # Enhance artist objects in tracks to match official Spotify API structure
    for track in album_tracks:
        # Ensure all required track fields are present
        required_track_fields = [
            'id', 'name', 'type', 'uri', 'href', 'external_urls', 'artists', 'album',
            'duration_ms', 'explicit', 'track_number', 'disc_number', 'available_markets',
            'popularity', 'is_local', 'is_playable', 'external_ids', 'linked_from',
            'restrictions', 'preview_url'
        ]
        for field in required_track_fields:
            if field not in track:
                # Reasonable defaults for some fields
                if field == 'type':
                    track[field] = 'track'
                elif field == 'artists':
                    track[field] = []
                elif field == 'album':
                    track[field] = {}
                elif field == 'external_urls':
                    track[field] = {}
                elif field == 'external_ids':
                    track[field] = {}
                elif field == 'available_markets':
                    track[field] = []
                else:
                    track[field] = None
        # Enhance artist objects
        if 'artists' in track:
            for artist in track['artists']:
                required_artist_fields = ['external_urls', 'href', 'id', 'name', 'type', 'uri']
                for afield in required_artist_fields:
                    if afield not in artist:
                        if afield == 'type':
                            artist[afield] = 'artist'
                        elif afield == 'external_urls':
                            artist[afield] = {}
                        else:
                            artist[afield] = None
                if 'id' in artist:
                    artist_id = artist['id']
                    artist['external_urls'] = artist.get('external_urls', {})
                    artist['external_urls']['spotify'] = f"https://open.spotify.com/artist/{artist_id}"
                    artist['href'] = f"https://api.spotify.com/v1/artists/{artist_id}"
                    artist['type'] = 'artist'
                    artist['uri'] = f"spotify:artist:{artist_id}"
        # Enhance album object in track to include images and required fields
        if 'album' in track:
            track_album = track['album']
            required_album_fields = ['id', 'name', 'uri', 'href', 'external_urls', 'images']
            for afield in required_album_fields:
                if afield not in track_album:
                    if afield == 'external_urls':
                        track_album[afield] = {}
                    elif afield == 'images':
                        track_album[afield] = []
                    else:
                        track_album[afield] = None
            if 'id' in track_album:
                album_id = track_album['id']
                album_data = albums_table.get(album_id, {})
                if 'images' in album_data:
                    track_album['images'] = album_data['images']
                track_album['external_urls']['spotify'] = f"https://open.spotify.com/album/{album_id}"
                track_album['href'] = f"https://api.spotify.com/v1/albums/{album_id}"
                track_album['uri'] = f"spotify:album:{album_id}"

    # Apply pagination
    result = utils.apply_pagination(album_tracks, limit, offset)
    result['href'] = f"https://api.spotify.com/v1/albums/{album_id}/tracks"

    return result


@tool_spec(
    spec={
        'name': 'get_users_saved_albums',
        'description': """ Get a list of the albums saved in the current Spotify user's 'Your Music' library.
        
        This endpoint retrieves all albums that the current user has saved to their library. The response includes detailed album information and can be filtered by market and paginated for efficient data retrieval. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of albums to return. Default: 20. Minimum: 1. Maximum: 50.'
                },
                'offset': {
                    'type': 'integer',
                    'description': 'The index of the first album to return. Default: 0 (the first object).'
                },
                'market': {
                    'type': 'string',
                    'description': 'An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.'
                }
            },
            'required': []
        }
    }
)
def get_users_saved_albums(
        limit: int = 20,
        offset: int = 0,
        market: Optional[str] = None
) -> Dict[str, Any]:
    """Get a list of the albums saved in the current Spotify user's 'Your Music' library.

    This endpoint retrieves all albums that the current user has saved to their library. The response includes detailed album information and can be filtered by market and paginated for efficient data retrieval.

    Args:
        limit (int): The maximum number of albums to return. Default: 20. Minimum: 1. Maximum: 50.
        offset (int): The index of the first album to return. Default: 0 (the first object).
        market (Optional[str]): An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.

    Returns:
        Dict[str, Any]: Saved albums response with pagination info.
            items (List[Dict[str, Any]]): Array of saved album objects, each containing:
                added_at (str): ISO 8601 timestamp when album was added
                album (Dict[str, Any]): Complete album information
                    - id (str): Unique album identifier
                    - name (str): Album name
                    - type (str): The type of the album ('album')
                    - uri (str): Spotify URI for the album
                    - href (str): API endpoint URL for the album
                    - external_urls (Dict[str, str]): External URLs for the album
                        - spotify (str): The Spotify URL for the album
                    - artists (List[Dict[str, Any]]): Array of artist objects
                        - external_urls (Dict[str, str]): Known external URLs for this artist
                            - spotify (str): The Spotify URL for the artist
                        - href (str): A link to the Web API endpoint providing full details of the artist
                        - id (str): The Spotify ID for the artist
                        - name (str): The name of the artist
                        - type (str): The object type ('artist')
                        - uri (str): The Spotify URI for the artist
                    - album_type (str): Type of album ('album', 'single', 'compilation')
                    - total_tracks (int): Total number of tracks
                    - available_markets (List[str]): List of markets where album is available
                    - release_date (str): Release date in YYYY-MM-DD format
                    - release_date_precision (str): Precision of release date ('year', 'month', 'day')
                    - images (List[Dict[str, Any]]): Album cover images
                        - url (str): The source URL of the image
                        - height (int): The image height in pixels
                        - width (int): The image width in pixels
                    - popularity (int): Popularity score (0-100)
                    - restrictions (Optional[Dict[str, Any]]): Album restrictions if any
                        - reason (str): The reason for the restriction ('market', 'product', 'explicit')
                    - genres (List[str]): Array of genres associated with the album
                    - tracks (Dict[str, Any]): Album tracks information
                        - href (str): A link to the Web API endpoint providing full details of the tracks
                        - limit (int): The maximum number of tracks in the response
                        - next (Optional[str]): URL to the next page of results
                        - offset (int): The offset of the items returned
                        - previous (Optional[str]): URL to the previous page of results
                        - total (int): The total number of tracks available
                        - items (List[Dict[str, Any]]): Array of simplified track objects
                            - id (str): Unique track identifier
                            - name (str): Track name
                            - type (str): Object type ('track')
                            - uri (str): Spotify URI for the track
                            - href (str): API endpoint URL for the track
                            - external_urls (Dict[str, str]): External URLs for the track
                                - spotify (str): The Spotify URL for the track
                            - artists (List[Dict[str, Any]]): Array of artist objects
                                - external_urls (Dict[str, str]): Known external URLs for this artist
                                    - spotify (str): The Spotify URL for the artist
                                - href (str): A link to the Web API endpoint providing full details of the artist
                                - id (str): The Spotify ID for the artist
                                - name (str): The name of the artist
                                - type (str): The object type ('artist')
                                - uri (str): The Spotify URI for the artist
                            - album (Dict[str, Any]): Album information
                                - id (str): The Spotify ID for the album
                                - name (str): The name of the album
                                - uri (str): Spotify URI for the album
                                - href (str): API endpoint URL for the album
                                - external_urls (Dict[str, str]): External URLs for the album
                                    - spotify (str): The Spotify URL for the album
                                - images (List[Dict[str, Any]]): Album cover images
                                    - url (str): The source URL of the image
                                    - height (int): The image height in pixels
                                    - width (int): The image width in pixels
                            - duration_ms (int): Track duration in milliseconds
                            - explicit (bool): Whether the track contains explicit content
                            - track_number (int): Track number on the album
                            - disc_number (int): Disc number
                            - available_markets (List[str]): List of markets where track is available
                            - popularity (int): Popularity score (0-100)
                            - is_local (bool): Whether the track is a local file
                            - is_playable (bool): Whether the track is playable
                            - external_ids (Dict[str, str]): Known external IDs for the track
                                - isrc (str): International Standard Recording Code
                            - linked_from (Optional[Dict[str, Any]]): Information about the originally requested track when Track Relinking is applied
                            - restrictions (Optional[Dict[str, Any]]): Track restrictions if any
                                - reason (str): The reason for the restriction
                            - preview_url (Optional[str]): A URL to a 30 second preview (MP3 format) of the track
                    - copyrights (List[Dict[str, Any]]): The copyright statements of the album
                        - text (str): The copyright text for this content
                        - type (str): The type of copyright ('C' = copyright, 'P' = performance copyright)
                    - external_ids (Dict[str, str]): Known external IDs for the album
                        - isrc (str): International Standard Recording Code
                        - ean (str): International Article Number
                        - upc (str): Universal Product Code
                    - label (str): The label associated with the album
            total (int): Total number of saved albums
            limit (int): Number of albums returned in this response
            offset (int): Offset of the first album returned
            href (str): URL to the full list of saved albums
            next (Optional[str]): URL to the next page of results
            previous (Optional[str]): URL to the previous page of results

    Raises:
        InvalidInputError: If limit is outside 1-50 range, offset is negative, or market is not a valid country code.
        AuthenticationError: If user is not authenticated.
        AuthorizationError: If user does not have required permissions.
    """
    # Validate limit and offset
    utils.validate_limit_offset(limit, offset)

    # Validate market parameter if provided
    if market is not None:
        if not utils.validate_market(market):
            raise custom_errors.InvalidMarketError("market must be a valid ISO 3166-1 alpha-2 country code.")

    # Get current user from DB (in a real implementation, this would come from auth token)
    current_user_id = utils.get_current_user_id()

    # Get user's saved albums
    saved_albums_table = DB.get('saved_albums')
    user_saved_albums = saved_albums_table.get(current_user_id, [])

    # Get album details for saved album IDs
    albums_table = DB.get('albums')
    saved_albums_data = []

    for album_id in user_saved_albums:
        album_data = albums_table.get(album_id)
        if album_data:
            # Apply market filtering if specified
            if market is not None:
                available_markets = album_data.get('available_markets', [])
                if market in available_markets:
                    album_response = copy.deepcopy(album_data)
                    if 'artists' in album_response:
                        for artist in album_response['artists']:
                            if 'id' in artist:
                                artist_id = artist['id']
                                artist['external_urls'] = {
                                    'spotify': f"https://open.spotify.com/artist/{artist_id}"
                                }
                                artist['href'] = f"https://api.spotify.com/v1/artists/{artist_id}"
                                artist['type'] = 'artist'
                                artist['uri'] = f"spotify:artist:{artist_id}"
                    tracks_table = DB.get('tracks')
                    album_tracks = []
                    for track_id, track_data in tracks_table.items():
                        track_album = track_data.get('album', {})
                        if track_album.get('id') == album_id:
                            if market is not None:
                                available_markets = track_data.get('available_markets', [])
                                if market in available_markets:
                                    album_tracks.append(copy.deepcopy(track_data))
                            else:
                                album_tracks.append(copy.deepcopy(track_data))
                    album_tracks.sort(key=lambda x: (x.get('disc_number', 1), x.get('track_number', 1)))
                    # --- ENHANCE TRACKS (always apply) ---
                    album_tracks = [track if isinstance(track, dict) else {} for track in album_tracks]
                    for i, track in enumerate(album_tracks):
                        required_track_fields = [
                            'id', 'name', 'type', 'uri', 'href', 'external_urls', 'artists', 'album',
                            'duration_ms', 'explicit', 'track_number', 'disc_number', 'available_markets',
                            'popularity', 'is_local', 'is_playable', 'external_ids', 'linked_from',
                            'restrictions', 'preview_url'
                        ]
                        for field in required_track_fields:
                            if field not in track:
                                if field == 'type':
                                    track[field] = 'track'
                                elif field == 'artists':
                                    track[field] = []
                                elif field == 'album':
                                    track[field] = {}
                                elif field == 'external_urls':
                                    track[field] = {}
                                elif field == 'external_ids':
                                    track[field] = {}
                                elif field == 'available_markets':
                                    track[field] = []
                                else:
                                    track[field] = None
                        # Enhance artist objects
                        if 'artists' in track:
                            for artist in track['artists']:
                                required_artist_fields = ['external_urls', 'href', 'id', 'name', 'type', 'uri']
                                for afield in required_artist_fields:
                                    if afield not in artist:
                                        if afield == 'type':
                                            artist[afield] = 'artist'
                                        elif afield == 'external_urls':
                                            artist[afield] = {}
                                        else:
                                            artist[afield] = None
                                if 'id' in artist:
                                    artist_id = artist['id']
                                    artist['external_urls'] = artist.get('external_urls', {})
                                    artist['external_urls']['spotify'] = f"https://open.spotify.com/artist/{artist_id}"
                                    artist['href'] = f"https://api.spotify.com/v1/artists/{artist_id}"
                                    artist['type'] = 'artist'
                                    artist['uri'] = f"spotify:artist:{artist_id}"
                        # Enhance album object in track to include images and required fields
                        if 'album' in track:
                            track_album = track['album']
                            required_album_fields = ['id', 'name', 'uri', 'href', 'external_urls', 'images']
                            for afield in required_album_fields:
                                if afield not in track_album:
                                    if afield == 'external_urls':
                                        track_album[afield] = {}
                                    elif afield == 'images':
                                        track_album[afield] = []
                                    else:
                                        track_album[afield] = None
                            if 'id' in track_album:
                                tid = track_album['id']
                                album_db = albums_table.get(tid, {})
                                if 'images' in album_db:
                                    track_album['images'] = album_db['images']
                                track_album['external_urls']['spotify'] = f"https://open.spotify.com/album/{tid}"
                                track_album['href'] = f"https://api.spotify.com/v1/albums/{tid}"
                                track_album['uri'] = f"spotify:album:{tid}"
                        album_tracks[i] = track
                    tracks_info = {
                        'href': f"https://api.spotify.com/v1/albums/{album_id}/tracks",
                        'limit': 20,
                        'next': None,
                        'offset': 0,
                        'previous': None,
                        'total': len(album_tracks),
                        'items': album_tracks
                    }
                    album_response['tracks'] = tracks_info
                    saved_albums_data.append({
                        'added_at': utils.format_timestamp(),
                        'album': album_response
                    })
            else:
                album_response = copy.deepcopy(album_data)
                if 'artists' in album_response:
                    for artist in album_response['artists']:
                        if 'id' in artist:
                            artist_id = artist['id']
                            artist['external_urls'] = {
                                'spotify': f"https://open.spotify.com/artist/{artist_id}"
                            }
                            artist['href'] = f"https://api.spotify.com/v1/artists/{artist_id}"
                            artist['type'] = 'artist'
                            artist['uri'] = f"spotify:artist:{artist_id}"
                tracks_table = DB.get('tracks')
                album_tracks = []
                for track_id, track_data in tracks_table.items():
                    track_album = track_data.get('album', {})
                    if track_album.get('id') == album_id:
                        album_tracks.append(copy.deepcopy(track_data))
                album_tracks.sort(key=lambda x: (x.get('disc_number', 1), x.get('track_number', 1)))
                # --- ENHANCE TRACKS (always apply) ---
                album_tracks = [track if isinstance(track, dict) else {} for track in album_tracks]
                for i, track in enumerate(album_tracks):
                    required_track_fields = [
                        'id', 'name', 'type', 'uri', 'href', 'external_urls', 'artists', 'album',
                        'duration_ms', 'explicit', 'track_number', 'disc_number', 'available_markets',
                        'popularity', 'is_local', 'is_playable', 'external_ids', 'linked_from',
                        'restrictions', 'preview_url'
                    ]
                    for field in required_track_fields:
                        if field not in track:
                            if field == 'type':
                                track[field] = 'track'
                            elif field == 'artists':
                                track[field] = []
                            elif field == 'album':
                                track[field] = {}
                            elif field == 'external_urls':
                                track[field] = {}
                            elif field == 'external_ids':
                                track[field] = {}
                            elif field == 'available_markets':
                                track[field] = []
                            else:
                                track[field] = None
                    # Enhance artist objects
                    if 'artists' in track:
                        for artist in track['artists']:
                            required_artist_fields = ['external_urls', 'href', 'id', 'name', 'type', 'uri']
                            for afield in required_artist_fields:
                                if afield not in artist:
                                    if afield == 'type':
                                        artist[afield] = 'artist'
                                    elif afield == 'external_urls':
                                        artist[afield] = {}
                                    else:
                                        artist[afield] = None
                    # Enhance album object in track to include images and required fields
                    if 'album' in track:
                        track_album = track['album']
                        required_album_fields = ['id', 'name', 'uri', 'href', 'external_urls', 'images']
                        for afield in required_album_fields:
                            if afield not in track_album:
                                if afield == 'external_urls':
                                    track_album[afield] = {}
                                elif afield == 'images':
                                    track_album[afield] = []
                                else:
                                    track_album[afield] = None
                        if 'id' in track_album:
                            tid = track_album['id']
                            album_db = albums_table.get(tid, {})
                            if 'images' in album_db:
                                track_album['images'] = album_db['images']
                            track_album['external_urls']['spotify'] = f"https://open.spotify.com/album/{tid}"
                            track_album['href'] = f"https://api.spotify.com/v1/albums/{tid}"
                            track_album['uri'] = f"spotify:album:{tid}"
                    album_tracks[i] = track
                tracks_info = {
                    'href': f"https://api.spotify.com/v1/albums/{album_id}/tracks",
                    'limit': 20,
                    'next': None,
                    'offset': 0,
                    'previous': None,
                    'total': len(album_tracks),
                    'items': album_tracks
                }
                album_response['tracks'] = tracks_info
                saved_albums_data.append({
                    'added_at': utils.format_timestamp(),
                    'album': album_response
                })

    # Apply pagination
    result = utils.apply_pagination(saved_albums_data, limit, offset)
    result['href'] = "https://api.spotify.com/v1/me/albums"

    return result


@tool_spec(
    spec={
        'name': 'save_albums_for_user',
        'description': """ Save one or more albums to the current user's 'Your Music' library.
        
        This endpoint allows users to save albums to their personal library for easy access and offline listening. The albums will appear in the user's 'Your Music' section and can be accessed across all their devices. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'album_ids': {
                    'type': 'array',
                    'description': 'A list of the Spotify IDs for the albums. Maximum: 50 IDs.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'album_ids'
            ]
        }
    }
)
def save_albums_for_user(album_ids: List[str]) -> Dict[str, Any]:
    """Save one or more albums to the current user's 'Your Music' library.

    This endpoint allows users to save albums to their personal library for easy access and offline listening. The albums will appear in the user's 'Your Music' section and can be accessed across all their devices.

    Args:
        album_ids (List[str]): A list of the Spotify IDs for the albums. Maximum: 50 IDs.

    Returns:
        Dict[str, Any]: Success response indicating albums were saved.
            message (str): Success message

    Raises:
        InvalidInputError: If album_ids is not a list, contains more than 50 IDs, or contains invalid album IDs.
        AuthenticationError: If user is not authenticated.
        AuthorizationError: If user does not have required permissions.
    """
    # Validate album_ids
    if not isinstance(album_ids, list):
        raise custom_errors.InvalidInputError("album_ids must be a list.")

    if len(album_ids) > 50:
        raise custom_errors.InvalidInputError("album_ids cannot contain more than 50 IDs.")

    if not all(isinstance(album_id, str) and album_id for album_id in album_ids):
        raise custom_errors.InvalidInputError("All album IDs must be non-empty strings.")

    # Get current user from DB (in a real implementation, this would come from auth token)
    current_user_id = utils.get_current_user_id()

    # Validate that all albums exist
    albums_table = DB.get('albums')
    for album_id in album_ids:
        if album_id not in albums_table:
            raise custom_errors.NoResultsFoundError(f"Album with ID '{album_id}' not found.")

    saved_albums_table = DB.get('saved_albums')
    if current_user_id not in saved_albums_table:
        saved_albums_table[current_user_id] = []

    # Add only albums that aren't already saved
    user_saved_albums = saved_albums_table[current_user_id]
    for album_id in album_ids:
        if album_id not in user_saved_albums:
            user_saved_albums.append(album_id)

    return {"message": "The album is saved"}


@tool_spec(
    spec={
        'name': 'remove_albums_for_user',
        'description': """ Remove one or more albums from the current user's 'Your Music' library.
        
        This endpoint allows users to remove albums from their personal library. The albums will no longer appear in the user's 'Your Music' section. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'album_ids': {
                    'type': 'array',
                    'description': 'A list of the Spotify IDs for the albums. Maximum: 50 IDs.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'album_ids'
            ]
        }
    }
)
def remove_albums_for_user(album_ids: List[str]) -> Dict[str, Any]:
    """Remove one or more albums from the current user's 'Your Music' library.

    This endpoint allows users to remove albums from their personal library. The albums will no longer appear in the user's 'Your Music' section.

    Args:
        album_ids (List[str]): A list of the Spotify IDs for the albums. Maximum: 50 IDs.

    Returns:
        Dict[str, Any]: Success response indicating albums were removed.
            message (str): Success message

    Raises:
        InvalidInputError: If album_ids is not a list, contains more than 50 IDs, or contains invalid album IDs.
        AuthenticationError: If user is not authenticated.
        AuthorizationError: If user does not have required permissions.
    """
    # Validate album_ids
    if not isinstance(album_ids, list):
        raise custom_errors.InvalidInputError("album_ids must be a list.")

    if len(album_ids) > 50:
        raise custom_errors.InvalidInputError("album_ids cannot contain more than 50 IDs.")

    if not all(isinstance(album_id, str) and album_id for album_id in album_ids):
        raise custom_errors.InvalidInputError("All album IDs must be non-empty strings.")

    # Get current user from DB (in a real implementation, this would come from auth token)
    current_user_id = utils.get_current_user_id()

    # Remove albums from user's saved albums
    saved_albums_table = DB.get('saved_albums')
    if current_user_id in saved_albums_table:
        user_saved_albums = saved_albums_table[current_user_id]
        for album_id in album_ids:
            if album_id in user_saved_albums:
                user_saved_albums.remove(album_id)

    return {"message": "Album(s) have been removed from the library"}


@tool_spec(
    spec={
        'name': 'check_users_saved_albums',
        'description': """ Check if one or more albums is already saved in the current Spotify user's 'Your Music' library.
        
        This endpoint allows applications to check the saved status of albums without retrieving the full album data. This is useful for displaying save/unsave buttons or tracking user preferences. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'album_ids': {
                    'type': 'array',
                    'description': 'A list of the Spotify IDs for the albums. Maximum: 50 IDs.',
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': [
                'album_ids'
            ]
        }
    }
)
def check_users_saved_albums(album_ids: List[str]) -> List[bool]:
    """Check if one or more albums is already saved in the current Spotify user's 'Your Music' library.

    This endpoint allows applications to check the saved status of albums without retrieving the full album data. This is useful for displaying save/unsave buttons or tracking user preferences.

    Args:
        album_ids (List[str]): A list of the Spotify IDs for the albums. Maximum: 50 IDs.

    Returns:
        List[bool]: Array of boolean values indicating whether each album is saved.
            True if the album is saved, False otherwise.

    Raises:
        InvalidInputError: If album_ids is not a list, contains more than 50 IDs, or contains invalid album IDs.
        AuthenticationError: If user is not authenticated.
        AuthorizationError: If user does not have required permissions.
    """
    # Validate album_ids
    if not isinstance(album_ids, list):
        raise custom_errors.InvalidInputError("album_ids must be a list.")

    if len(album_ids) > 50:
        raise custom_errors.InvalidInputError("album_ids cannot contain more than 50 IDs.")

    if not all(isinstance(album_id, str) and album_id for album_id in album_ids):
        raise custom_errors.InvalidInputError("All album IDs must be non-empty strings.")

    # Get current user from DB (in a real implementation, this would come from auth token)
    current_user_id = utils.get_current_user_id()

    # Get user's saved albums
    saved_albums_table = DB.get('saved_albums')
    user_saved_albums = saved_albums_table.get(current_user_id, [])

    # Check which albums are saved
    saved_status = []
    for album_id in album_ids:
        saved_status.append(album_id in user_saved_albums)

    return saved_status
