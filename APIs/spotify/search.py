from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, List, Dict, Any
from datetime import datetime
import copy

from .SimulationEngine.db import DB
from .SimulationEngine import custom_errors, models, utils


@tool_spec(
    spec={
        'name': 'search_for_item',
        'description': """ Get Spotify catalog information about artists, albums, tracks, playlists, shows, episodes, or audiobooks that match a keyword string.
        
        This endpoint allows you to search Spotify's catalog for various types of content using keywords. The search is powered by Spotify's search engine and supports various filters and parameters. This is essential for music discovery, content browsing, and user search functionality. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'q': {
                    'type': 'string',
                    'description': 'Your search query. You can use wildcards and field filters.'
                },
                'type': {
                    'type': 'string',
                    'description': "A comma-separated list of item types to search across. Valid types are: 'album', 'artist', 'playlist', 'track', 'show', 'episode', 'audiobook'."
                },
                'market': {
                    'type': 'string',
                    'description': 'An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.'
                },
                'offset': {
                    'type': 'integer',
                    'description': 'The index of the first item to return. Default: 0 (the first object).'
                },
                'include_external': {
                    'type': 'string',
                    'description': "If 'audio', the response will include any relevant audio content that is hosted externally."
                }
            },
            'required': [
                'q',
                'type'
            ]
        }
    }
)
def search_for_item(
    q: str,
    type: str,
    market: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    include_external: Optional[str] = None
) -> Dict[str, Any]:
    """Get Spotify catalog information about artists, albums, tracks, playlists, shows, episodes, or audiobooks that match a keyword string.

    This endpoint allows you to search Spotify's catalog for various types of content using keywords. The search is powered by Spotify's search engine and supports various filters and parameters. This is essential for music discovery, content browsing, and user search functionality.

    Args:
        q (str): Your search query. You can use wildcards and field filters.
        type (str): A comma-separated list of item types to search across. Valid types are: 'album', 'artist', 'playlist', 'track', 'show', 'episode', 'audiobook'.
        market (Optional[str]): An ISO 3166-1 alpha-2 country code. If a market is not supplied, no market is applied.
        limit (int): The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
        offset (int): The index of the first item to return. Default: 0 (the first object).
        include_external (Optional[str]): If 'audio', the response will include any relevant audio content that is hosted externally.

    Returns:
        Dict[str, Any]: Search results with items arrays for each type.
            tracks (Optional[Dict[str, Any]]): Track search results containing:
                items (List[Dict[str, Any]]): Array of track objects
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
                total (int): Total number of tracks found
                limit (int): Number of tracks returned
                offset (int): Offset of the first track returned
                href (str): URL to the full search results
                next (Optional[str]): URL to the next page of results
                previous (Optional[str]): URL to the previous page of results
            artists (Optional[Dict[str, Any]]): Artist search results containing:
                items (List[Dict[str, Any]]): Array of artist objects
                    - id (str): Unique artist identifier
                    - name (str): Artist name
                    - type (str): Object type ('artist')
                    - uri (str): Spotify URI for the artist
                    - href (str): API endpoint URL for the artist
                    - external_urls (Dict[str, str]): External URLs for the artist
                        - spotify (str): The Spotify URL for the artist
                    - followers (Dict[str, Any]): Follower information with total count
                        - href (str): A link to the Web API endpoint providing full details of the followers
                        - total (int): The total number of followers
                    - genres (List[str]): Array of genres associated with the artist
                    - images (List[Dict[str, Any]]): Artist profile images
                        - url (str): The source URL of the image
                        - height (int): The image height in pixels
                        - width (int): The image width in pixels
                    - popularity (int): Popularity score (0-100)
                total (int): Total number of artists found
                limit (int): Number of artists returned
                offset (int): Offset of the first artist returned
                href (str): URL to the full search results
                next (Optional[str]): URL to the next page of results
                previous (Optional[str]): URL to the previous page of results
            albums (Optional[Dict[str, Any]]): Album search results containing:
                items (List[Dict[str, Any]]): Array of album objects
                    - id (str): Unique album identifier
                    - name (str): Album name
                    - type (str): Object type ('album')
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
                total (int): Total number of albums found
                limit (int): Number of albums returned
                offset (int): Offset of the first album returned
                href (str): URL to the full search results
                next (Optional[str]): URL to the next page of results
                previous (Optional[str]): URL to the previous page of results
            playlists (Optional[Dict[str, Any]]): Playlist search results containing:
                items (List[Dict[str, Any]]): Array of playlist objects
                total (int): Total number of playlists found
                limit (int): Number of playlists returned
                offset (int): Offset of the first playlist returned
                href (str): URL to the full search results
                next (Optional[str]): URL to the next page of results
                previous (Optional[str]): URL to the previous page of results
            shows (Optional[Dict[str, Any]]): Show search results containing:
                items (List[Dict[str, Any]]): Array of show objects
                total (int): Total number of shows found
                limit (int): Number of shows returned
                offset (int): Offset of the first show returned
                href (str): URL to the full search results
                next (Optional[str]): URL to the next page of results
                previous (Optional[str]): URL to the previous page of results
            episodes (Optional[Dict[str, Any]]): Episode search results containing:
                items (List[Dict[str, Any]]): Array of episode objects
                total (int): Total number of episodes found
                limit (int): Number of episodes returned
                offset (int): Offset of the first episode returned
                href (str): URL to the full search results
                next (Optional[str]): URL to the next page of results
                previous (Optional[str]): URL to the previous page of results
            audiobooks (Optional[Dict[str, Any]]): Audiobook search results containing:
                items (List[Dict[str, Any]]): Array of audiobook objects
                total (int): Total number of audiobooks found
                limit (int): Number of audiobooks returned
                offset (int): Offset of the first audiobook returned
                href (str): URL to the full search results
                next (Optional[str]): URL to the next page of results
                previous (Optional[str]): URL to the previous page of results

    Raises:
        InvalidInputError: If q is not a string or is empty, type contains invalid values, market is not a valid country code, limit is outside 1-50 range, offset is negative, or include_external is invalid.
    """
    # Validate q parameter
    if not isinstance(q, str):
        raise custom_errors.InvalidInputError("q must be a string.")
    
    if not q:
        raise custom_errors.InvalidInputError("q cannot be empty.")
    
    # Validate type parameter
    valid_types = ['album', 'artist', 'playlist', 'track', 'show', 'episode', 'audiobook']
    if not isinstance(type, str):
        raise custom_errors.InvalidInputError("type must be a string.")
    
    type_list = [t.strip() for t in type.split(',')]
    if not all(t in valid_types for t in type_list):
        raise custom_errors.InvalidInputError(f"type must contain only valid values: {', '.join(valid_types)}")
    
    # Validate market parameter if provided
    if market is not None:
        if not isinstance(market, str) or len(market) != 2:
            raise custom_errors.InvalidInputError("market must be a valid ISO 3166-1 alpha-2 country code.")
    
    # Validate limit parameter
    if limit < 1 or limit > 50:
        raise custom_errors.InvalidInputError("limit must be an integer between 1 and 50.")
    
    # Validate offset parameter
    if offset < 0:
        raise custom_errors.InvalidInputError("offset must be a non-negative integer.")
    
    # Validate include_external parameter if provided
    if include_external is not None:
        if include_external != 'audio':
            raise custom_errors.InvalidInputError("include_external must be 'audio' or None.")
    
    # Perform search across different types
    results = {}
    
    # Search tracks
    if 'track' in type_list:
        tracks_table = DB.get('tracks', {})
        track_results = []
        
        for track_id, track_data in tracks_table.items():
            # Simple search implementation - in real API this would use more sophisticated search
            track_name = track_data.get('name', '').lower()
            if q.lower() in track_name:
                # Apply market filtering if specified
                if market is not None:
                    available_markets = track_data.get('available_markets', [])
                    if market in available_markets:
                        track_results.append(track_data)
                else:
                    track_results.append(track_data)
        
        # Apply pagination
        start = offset or 0
        end = start + (limit or 20)
        paginated_tracks = track_results[start:end]
        
        results['tracks'] = {
            'items': paginated_tracks,
            'total': len(track_results),
            'limit': limit or 20,
            'offset': offset or 0,
            'href': f"https://api.spotify.com/v1/search?q={q}&type=track",
            'next': None,
            'previous': None
        }
        
        # Add pagination links if applicable
        if end < len(track_results):
            results['tracks']['next'] = f"https://api.spotify.com/v1/search?q={q}&type=track&limit={limit or 20}&offset={end}"
        
        if start > 0:
            prev_offset = max(0, start - (limit or 20))
            results['tracks']['previous'] = f"https://api.spotify.com/v1/search?q={q}&type=track&limit={limit or 20}&offset={prev_offset}"
    
    # Search artists
    if 'artist' in type_list:
        artists_table = DB.get('artists', {})
        artist_results = []
        
        for artist_id, artist_data in artists_table.items():
            artist_name = artist_data.get('name', '').lower()
            if q.lower() in artist_name:
                artist_results.append(artist_data)
        
        # Apply pagination
        start = offset or 0
        end = start + (limit or 20)
        paginated_artists = artist_results[start:end]
        
        results['artists'] = {
            'items': paginated_artists,
            'total': len(artist_results),
            'limit': limit or 20,
            'offset': offset or 0,
            'href': f"https://api.spotify.com/v1/search?q={q}&type=artist",
            'next': None,
            'previous': None
        }
        
        # Add pagination links if applicable
        if end < len(artist_results):
            results['artists']['next'] = f"https://api.spotify.com/v1/search?q={q}&type=artist&limit={limit or 20}&offset={end}"
        
        if start > 0:
            prev_offset = max(0, start - (limit or 20))
            results['artists']['previous'] = f"https://api.spotify.com/v1/search?q={q}&type=artist&limit={limit or 20}&offset={prev_offset}"
    
    # Search albums
    if 'album' in type_list:
        albums_table = DB.get('albums', {})
        album_results = []
        
        for album_id, album_data in albums_table.items():
            album_name = album_data.get('name', '').lower()
            if q.lower() in album_name:
                # Apply market filtering if specified
                if market is not None:
                    available_markets = album_data.get('available_markets', [])
                    if market in available_markets:
                        album_results.append(album_data)
                else:
                    album_results.append(album_data)
        
        # Apply pagination
        start = offset or 0
        end = start + (limit or 20)
        paginated_albums = album_results[start:end]
        
        results['albums'] = {
            'items': paginated_albums,
            'total': len(album_results),
            'limit': limit or 20,
            'offset': offset or 0,
            'href': f"https://api.spotify.com/v1/search?q={q}&type=album",
            'next': None,
            'previous': None
        }
        
        # Add pagination links if applicable
        if end < len(album_results):
            results['albums']['next'] = f"https://api.spotify.com/v1/search?q={q}&type=album&limit={limit or 20}&offset={end}"
        
        if start > 0:
            prev_offset = max(0, start - (limit or 20))
            results['albums']['previous'] = f"https://api.spotify.com/v1/search?q={q}&type=album&limit={limit or 20}&offset={prev_offset}"
    
    # Search playlists
    if 'playlist' in type_list:
        playlists_table = DB.get('playlists', {})
        playlist_results = []
        
        for playlist_id, playlist_data in playlists_table.items():
            playlist_name = playlist_data.get('name', '').lower()
            if q.lower() in playlist_name:
                playlist_results.append(playlist_data)
        
        # Apply pagination
        start = offset or 0
        end = start + (limit or 20)
        paginated_playlists = playlist_results[start:end]
        
        results['playlists'] = {
            'items': paginated_playlists,
            'total': len(playlist_results),
            'limit': limit or 20,
            'offset': offset or 0,
            'href': f"https://api.spotify.com/v1/search?q={q}&type=playlist",
            'next': None,
            'previous': None
        }
        
        # Add pagination links if applicable
        if end < len(playlist_results):
            results['playlists']['next'] = f"https://api.spotify.com/v1/search?q={q}&type=playlist&limit={limit or 20}&offset={end}"
        
        if start > 0:
            prev_offset = max(0, start - (limit or 20))
            results['playlists']['previous'] = f"https://api.spotify.com/v1/search?q={q}&type=playlist&limit={limit or 20}&offset={prev_offset}"
    
    # Search shows
    if 'show' in type_list:
        shows_table = DB.get('shows', {})
        show_results = []
        
        for show_id, show_data in shows_table.items():
            show_name = show_data.get('name', '').lower()
            if q.lower() in show_name:
                # Apply market filtering if specified
                if market is not None:
                    available_markets = show_data.get('available_markets', [])
                    if market in available_markets:
                        show_results.append(show_data)
                else:
                    show_results.append(show_data)
        
        # Apply pagination
        start = offset or 0
        end = start + (limit or 20)
        paginated_shows = show_results[start:end]
        
        results['shows'] = {
            'items': paginated_shows,
            'total': len(show_results),
            'limit': limit or 20,
            'offset': offset or 0,
            'href': f"https://api.spotify.com/v1/search?q={q}&type=show",
            'next': None,
            'previous': None
        }
        
        # Add pagination links if applicable
        if end < len(show_results):
            results['shows']['next'] = f"https://api.spotify.com/v1/search?q={q}&type=show&limit={limit or 20}&offset={end}"
        
        if start > 0:
            prev_offset = max(0, start - (limit or 20))
            results['shows']['previous'] = f"https://api.spotify.com/v1/search?q={q}&type=show&limit={limit or 20}&offset={prev_offset}"
    
    # Search episodes
    if 'episode' in type_list:
        episodes_table = DB.get('episodes', {})
        episode_results = []
        
        for episode_id, episode_data in episodes_table.items():
            episode_name = episode_data.get('name', '').lower()
            if q.lower() in episode_name:
                # Apply market filtering if specified
                if market is not None:
                    available_markets = episode_data.get('available_markets', [])
                    if market in available_markets:
                        episode_results.append(episode_data)
                else:
                    episode_results.append(episode_data)
        
        # Apply pagination
        start = offset or 0
        end = start + (limit or 20)
        paginated_episodes = episode_results[start:end]
        
        results['episodes'] = {
            'items': paginated_episodes,
            'total': len(episode_results),
            'limit': limit or 20,
            'offset': offset or 0,
            'href': f"https://api.spotify.com/v1/search?q={q}&type=episode",
            'next': None,
            'previous': None
        }
        
        # Add pagination links if applicable
        if end < len(episode_results):
            results['episodes']['next'] = f"https://api.spotify.com/v1/search?q={q}&type=episode&limit={limit or 20}&offset={end}"
        
        if start > 0:
            prev_offset = max(0, start - (limit or 20))
            results['episodes']['previous'] = f"https://api.spotify.com/v1/search?q={q}&type=episode&limit={limit or 20}&offset={prev_offset}"
    
    # Search audiobooks
    if 'audiobook' in type_list:
        audiobooks_table = DB.get('audiobooks', {})
        audiobook_results = []
        
        for audiobook_id, audiobook_data in audiobooks_table.items():
            audiobook_name = audiobook_data.get('name', '').lower()
            if q.lower() in audiobook_name:
                # Apply market filtering if specified
                if market is not None:
                    available_markets = audiobook_data.get('available_markets', [])
                    if market in available_markets:
                        audiobook_results.append(audiobook_data)
                else:
                    audiobook_results.append(audiobook_data)
        
        # Apply pagination
        start = offset or 0
        end = start + (limit or 20)
        paginated_audiobooks = audiobook_results[start:end]
        
        results['audiobooks'] = {
            'items': paginated_audiobooks,
            'total': len(audiobook_results),
            'limit': limit or 20,
            'offset': offset or 0,
            'href': f"https://api.spotify.com/v1/search?q={q}&type=audiobook",
            'next': None,
            'previous': None
        }
        
        # Add pagination links if applicable
        if end < len(audiobook_results):
            results['audiobooks']['next'] = f"https://api.spotify.com/v1/search?q={q}&type=audiobook&limit={limit or 20}&offset={end}"
        
        if start > 0:
            prev_offset = max(0, start - (limit or 20))
            results['audiobooks']['previous'] = f"https://api.spotify.com/v1/search?q={q}&type=audiobook&limit={limit or 20}&offset={prev_offset}"
    
    return results 