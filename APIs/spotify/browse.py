from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, List, Dict, Any
from datetime import datetime
import copy

from .SimulationEngine.db import DB
from .SimulationEngine import custom_errors, models, utils


@tool_spec(
    spec={
        'name': 'get_new_releases',
        'description': """ Get a list of new album releases featured in Spotify.
        
        This endpoint retrieves the latest album releases that are featured on Spotify. The response includes detailed album information and can be filtered by country and paginated for efficient data retrieval. This is essential for music discovery and keeping users updated with the latest releases. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'country': {
                    'type': 'string',
                    'description': 'A country: an ISO 3166-1 alpha-2 country code. Provide this parameter if you want the list of returned items to be relevant to a particular country. If omitted, the returned items will be relevant to all countries.'
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
            'required': []
        }
    }
)
def get_new_releases(
    country: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """Get a list of new album releases featured in Spotify.

    This endpoint retrieves the latest album releases that are featured on Spotify. The response includes detailed album information and can be filtered by country and paginated for efficient data retrieval. This is essential for music discovery and keeping users updated with the latest releases.

    Args:
        country (Optional[str]): A country: an ISO 3166-1 alpha-2 country code. Provide this parameter if you want the list of returned items to be relevant to a particular country. If omitted, the returned items will be relevant to all countries.
        limit (int): The maximum number of albums to return. Default: 20. Minimum: 1. Maximum: 50.
        offset (int): The index of the first album to return. Default: 0 (the first object).

    Returns:
        Dict[str, Any]: New releases response with pagination info.
            albums (Dict[str, Any]): Albums response containing:
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
                total (int): Total number of new releases
                limit (int): Number of albums returned in this response
                offset (int): Offset of the first album returned
                href (str): URL to the full list of new releases
                next (Optional[str]): URL to the next page of results
                previous (Optional[str]): URL to the previous page of results

    Raises:
        InvalidInputError: If country is not a valid country code, limit is outside 1-50 range, or offset is negative.
    """
    # Validate country parameter if provided
    if country is not None:
        if not utils.validate_market(country):
            raise custom_errors.InvalidMarketError("country must be a valid ISO 3166-1 alpha-2 country code.")
    
    # Validate limit and offset
    utils.validate_limit_offset(limit, offset)
    
    # Get albums from DB
    albums_table = DB.get('albums', {})
    new_releases = []
    
    for album_id, album_data in albums_table.items():
        # Filter by country if specified
        if country is not None:
            available_markets = album_data.get('available_markets', [])
            if country in available_markets:
                new_releases.append(album_data)
        else:
            new_releases.append(album_data)
    
    # Sort by release date (newest first)
    new_releases.sort(key=lambda x: x.get('release_date', ''), reverse=True)
    
    # Apply pagination
    result = utils.apply_pagination(new_releases, limit, offset)
    
    return {'albums': result}


@tool_spec(
    spec={
        'name': 'get_featured_playlists',
        'description': """ Get a list of Spotify featured playlists (shown, for example, on a Spotify player's 'Browse' tab).
        
        This endpoint retrieves playlists that are featured on Spotify, such as those shown on the Browse tab. The response can be filtered by country and locale, and supports pagination for efficient data retrieval. This is essential for music discovery and providing curated content to users. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'country': {
                    'type': 'string',
                    'description': """ A country: an ISO 3166-1 alpha-2 country code. Provide this parameter if you want the list of returned items to be relevant to a particular country. If omitted, the returned items will be relevant to all countries.
                    Examples: 'US', 'CA', 'GB', 'DE', 'FR'. """
                },
                'locale': {
                    'type': 'string',
                    'description': """ The desired language, consisting of a lowercase ISO 639-1 language code and an uppercase ISO 3166-1 alpha-2 country code, joined by an underscore. For example: es_MX, meaning "Spanish (Mexico)".
                    Examples: 'en_US', 'es_MX', 'fr_FR'. """
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
                },
                'timestamp': {
                    'type': 'string',
                    'description': """ A timestamp in ISO 8601 format: yyyy-MM-ddTHH:mm:ss. Use this parameter to specify the user's local time to get results tailored for that specific date and time in the day. If not provided, the response defaults to the current UTC time.
                    Examples: '2014-10-23T09:00:00', '2023-12-31T23:59:59'. """
                }
            },
            'required': []
        }
    }
)
def get_featured_playlists(
    country: Optional[str] = None,
    locale: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """Get a list of Spotify featured playlists (shown, for example, on a Spotify player's 'Browse' tab).

    This endpoint retrieves playlists that are featured on Spotify, such as those shown on the Browse tab. The response can be filtered by country and locale, and supports pagination for efficient data retrieval. This is essential for music discovery and providing curated content to users.

    Args:
        country (Optional[str]): A country: an ISO 3166-1 alpha-2 country code. Provide this parameter if you want the list of returned items to be relevant to a particular country. If omitted, the returned items will be relevant to all countries.
            Examples: 'US', 'CA', 'GB', 'DE', 'FR'.
        locale (Optional[str]): The desired language, consisting of a lowercase ISO 639-1 language code and an uppercase ISO 3166-1 alpha-2 country code, joined by an underscore. For example: es_MX, meaning "Spanish (Mexico)".
            Examples: 'en_US', 'es_MX', 'fr_FR'.
        limit (int): The maximum number of playlists to return. Default: 20. Minimum: 1. Maximum: 50.
            Examples: 10 (small selection), 20 (default), 50 (maximum).
        offset (int): The index of the first playlist to return. Default: 0 (the first object).
            Examples: 0 (start from beginning), 20 (skip first 20 playlists).
        timestamp (Optional[str]): A timestamp in ISO 8601 format: yyyy-MM-ddTHH:mm:ss. Use this parameter to specify the user's local time to get results tailored for that specific date and time in the day. If not provided, the response defaults to the current UTC time.
            Examples: '2014-10-23T09:00:00', '2023-12-31T23:59:59'.

    Returns:
        Dict[str, Any]: Featured playlists response with pagination info.
            playlists (Dict[str, Any]): Playlists response containing:
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
                total (int): Total number of featured playlists
                limit (int): Number of playlists returned in this response
                offset (int): Offset of the first playlist returned
                href (str): URL to the full list of featured playlists
                next (Optional[str]): URL to the next page of results
                previous (Optional[str]): URL to the previous page of results

    Raises:
        InvalidInputError: If country is not a valid country code, locale is not in correct format, limit is outside 1-50 range, offset is negative, or timestamp is not in ISO 8601 format.
    """
    # Validate country parameter if provided
    if country is not None:
        if not utils.validate_market(country):
            raise custom_errors.InvalidMarketError("country must be a valid ISO 3166-1 alpha-2 country code.")
    
    # Validate locale parameter if provided
    if locale is not None:
        if not isinstance(locale, str) or '_' not in locale:
            raise custom_errors.InvalidInputError("locale must be in format 'language_COUNTRY' (e.g., 'en_US').")
    
    # Validate limit and offset
    utils.validate_limit_offset(limit, offset)
    
    # Validate timestamp parameter if provided
    if timestamp is not None:
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            raise custom_errors.InvalidInputError("timestamp must be in ISO 8601 format (e.g., '2014-10-23T09:00:00').")
    
    # Get playlists from DB
    playlists_table = DB.get('playlists', {})
    featured_playlists = []
    
    for playlist_id, playlist_data in playlists_table.items():
        # For this simulation, we'll consider all playlists as featured
        # In a real implementation, this would filter based on Spotify's featured criteria
        featured_playlists.append(playlist_data)
    
    # Apply pagination
    result = utils.apply_pagination(featured_playlists, limit, offset)
    
    return {'playlists': result}


@tool_spec(
    spec={
        'name': 'get_categories',
        'description': """ Get a list of categories used to tag items in Spotify (on, for example, the Spotify player's 'Browse' tab).
        
        This endpoint retrieves all available categories that can be used to browse and discover content on Spotify. The response can be filtered by country and locale, and supports pagination for efficient data retrieval. This is essential for building browse interfaces and category-based navigation. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'country': {
                    'type': 'string',
                    'description': """ A country: an ISO 3166-1 alpha-2 country code. Provide this parameter if you want the list of returned items to be relevant to a particular country. If omitted, the returned items will be relevant to all countries.
                    Examples: 'US', 'CA', 'GB', 'DE', 'FR'. """
                },
                'locale': {
                    'type': 'string',
                    'description': """ The desired language, consisting of a lowercase ISO 639-1 language code and an uppercase ISO 3166-1 alpha-2 country code, joined by an underscore. For example: es_MX, meaning "Spanish (Mexico)".
                    Examples: 'en_US', 'es_MX', 'fr_FR'. """
                },
                'limit': {
                    'type': 'integer',
                    'description': """ The maximum number of categories to return. Default: 20. Minimum: 1. Maximum: 50.
                    Examples: 10 (small selection), 20 (default), 50 (maximum). """
                },
                'offset': {
                    'type': 'integer',
                    'description': """ The index of the first category to return. Default: 0 (the first object).
                    Examples: 0 (start from beginning), 20 (skip first 20 categories). """
                }
            },
            'required': []
        }
    }
)
def get_categories(
    country: Optional[str] = None,
    locale: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """Get a list of categories used to tag items in Spotify (on, for example, the Spotify player's 'Browse' tab).

    This endpoint retrieves all available categories that can be used to browse and discover content on Spotify. The response can be filtered by country and locale, and supports pagination for efficient data retrieval. This is essential for building browse interfaces and category-based navigation.

    Args:
        country (Optional[str]): A country: an ISO 3166-1 alpha-2 country code. Provide this parameter if you want the list of returned items to be relevant to a particular country. If omitted, the returned items will be relevant to all countries.
            Examples: 'US', 'CA', 'GB', 'DE', 'FR'.
        locale (Optional[str]): The desired language, consisting of a lowercase ISO 639-1 language code and an uppercase ISO 3166-1 alpha-2 country code, joined by an underscore. For example: es_MX, meaning "Spanish (Mexico)".
            Examples: 'en_US', 'es_MX', 'fr_FR'.
        limit (int): The maximum number of categories to return. Default: 20. Minimum: 1. Maximum: 50.
            Examples: 10 (small selection), 20 (default), 50 (maximum).
        offset (int): The index of the first category to return. Default: 0 (the first object).
            Examples: 0 (start from beginning), 20 (skip first 20 categories).

    Returns:
        Dict[str, Any]: Categories response with pagination info.
            categories (Dict[str, Any]): Categories response containing:
                items (List[Dict[str, Any]]): Array of category objects, each containing:
                    id (str): Unique category identifier
                    name (str): Category name
                    type (str): Object type ('category')
                    uri (str): Spotify URI for the category
                    href (str): API endpoint URL for the category
                    external_urls (Dict[str, str]): External URLs for the category
                    icons (List[Dict[str, Any]]): Category icons
                total (int): Total number of categories
                limit (int): Number of categories returned in this response
                offset (int): Offset of the first category returned
                href (str): URL to the full list of categories
                next (Optional[str]): URL to the next page of results
                previous (Optional[str]): URL to the previous page of results

    Raises:
        InvalidInputError: If country is not a valid country code, locale is not in correct format, limit is outside 1-50 range, or offset is negative.
    """
    # Validate country parameter if provided
    if country is not None:
        if not utils.validate_market(country):
            raise custom_errors.InvalidMarketError("country must be a valid ISO 3166-1 alpha-2 country code.")
    
    # Validate locale parameter if provided
    if locale is not None:
        if not isinstance(locale, str) or '_' not in locale:
            raise custom_errors.InvalidInputError("locale must be in format 'language_COUNTRY' (e.g., 'en_US').")
    
    # Validate limit and offset
    utils.validate_limit_offset(limit, offset)
    
    # Get categories from DB
    categories_table = DB.get('categories', {})
    categories = list(categories_table.values())
    
    # Apply pagination
    result = utils.apply_pagination(categories, limit, offset)
    
    return {'categories': result}


@tool_spec(
    spec={
        'name': 'get_category',
        'description': """ Get a single category used to tag items in Spotify (on, for example, the Spotify player's 'Browse' tab).
        
        This endpoint retrieves detailed information about a specific category, including its name, icons, and other metadata. This is useful for displaying category information or building category-based navigation interfaces. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'category_id': {
                    'type': 'string',
                    'description': """ The Spotify category ID for the category.
                    Examples: 'category_1', '0JQ5DAqbMKFQ00XGBls6ym'. """
                },
                'country': {
                    'type': 'string',
                    'description': """ A country: an ISO 3166-1 alpha-2 country code. Provide this parameter if you want the list of returned items to be relevant to a particular country. If omitted, the returned items will be relevant to all countries.
                    Examples: 'US', 'CA', 'GB', 'DE', 'FR'. """
                },
                'locale': {
                    'type': 'string',
                    'description': """ The desired language, consisting of a lowercase ISO 639-1 language code and an uppercase ISO 3166-1 alpha-2 country code, joined by an underscore. For example: es_MX, meaning "Spanish (Mexico)".
                    Examples: 'en_US', 'es_MX', 'fr_FR'. """
                }
            },
            'required': [
                'category_id'
            ]
        }
    }
)
def get_category(category_id: str, country: Optional[str] = None, locale: Optional[str] = None) -> Dict[str, Any]:
    """Get a single category used to tag items in Spotify (on, for example, the Spotify player's 'Browse' tab).

    This endpoint retrieves detailed information about a specific category, including its name, icons, and other metadata. This is useful for displaying category information or building category-based navigation interfaces.

    Args:
        category_id (str): The Spotify category ID for the category.
            Examples: 'category_1', '0JQ5DAqbMKFQ00XGBls6ym'.
        country (Optional[str]): A country: an ISO 3166-1 alpha-2 country code. Provide this parameter if you want the list of returned items to be relevant to a particular country. If omitted, the returned items will be relevant to all countries.
            Examples: 'US', 'CA', 'GB', 'DE', 'FR'.
        locale (Optional[str]): The desired language, consisting of a lowercase ISO 639-1 language code and an uppercase ISO 3166-1 alpha-2 country code, joined by an underscore. For example: es_MX, meaning "Spanish (Mexico)".
            Examples: 'en_US', 'es_MX', 'fr_FR'.

    Returns:
        Dict[str, Any]: Category data with comprehensive information.
            id (str): Unique category identifier
            name (str): Category name
            type (str): Object type ('category')
            uri (str): Spotify URI for the category
            href (str): API endpoint URL for the category
            external_urls (Dict[str, str]): External URLs for the category
            icons (List[Dict[str, Any]]): Category icons

    Raises:
        InvalidInputError: If category_id is not a string or is empty, country is not a valid country code, or locale is not in correct format.
        NoResultsFoundError: If no category exists with the specified category_id.
    """
    # Validate category_id
    utils.validate_category_id(category_id)
    
    # Validate country parameter if provided
    if country is not None:
        if not utils.validate_market(country):
            raise custom_errors.InvalidMarketError("country must be a valid ISO 3166-1 alpha-2 country code.")
    
    # Validate locale parameter if provided
    if locale is not None:
        if not isinstance(locale, str) or '_' not in locale:
            raise custom_errors.InvalidInputError("locale must be in format 'language_COUNTRY' (e.g., 'en_US').")
    
    # Get category data from DB
    categories_table = DB.get('categories', {})
    category_data = categories_table.get(category_id)
    
    if category_data is None:
        raise custom_errors.NoResultsFoundError(f"Category with ID '{category_id}' not found.")
    
    # Return category data
    return category_data


@tool_spec(
    spec={
        'name': 'get_category_playlists',
        'description': """ Get a list of Spotify playlists tagged with a particular category.
        
        This endpoint retrieves playlists that are tagged with a specific category. The response can be filtered by country and supports pagination for efficient data retrieval. This is useful for displaying category-specific playlists or building category-based browsing interfaces. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'category_id': {
                    'type': 'string',
                    'description': """ The Spotify category ID for the category.
                    Examples: 'category_1', '0JQ5DAqbMKFQ00XGBls6ym'. """
                },
                'country': {
                    'type': 'string',
                    'description': """ A country: an ISO 3166-1 alpha-2 country code. Provide this parameter if you want the list of returned items to be relevant to a particular country. If omitted, the returned items will be relevant to all countries.
                    Examples: 'US', 'CA', 'GB', 'DE', 'FR'. """
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
                'category_id'
            ]
        }
    }
)
def get_category_playlists(
    category_id: str,
    country: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
) -> Dict[str, Any]:
    """Get a list of Spotify playlists tagged with a particular category.

    This endpoint retrieves playlists that are tagged with a specific category. The response can be filtered by country and supports pagination for efficient data retrieval. This is useful for displaying category-specific playlists or building category-based browsing interfaces.

    Args:
        category_id (str): The Spotify category ID for the category.
            Examples: 'category_1', '0JQ5DAqbMKFQ00XGBls6ym'.
        country (Optional[str]): A country: an ISO 3166-1 alpha-2 country code. Provide this parameter if you want the list of returned items to be relevant to a particular country. If omitted, the returned items will be relevant to all countries.
            Examples: 'US', 'CA', 'GB', 'DE', 'FR'.
        limit (int): The maximum number of playlists to return. Default: 20. Minimum: 1. Maximum: 50.
            Examples: 10 (small selection), 20 (default), 50 (maximum).
        offset (int): The index of the first playlist to return. Default: 0 (the first object).
            Examples: 0 (start from beginning), 20 (skip first 20 playlists).

    Returns:
        Dict[str, Any]: Category playlists response with pagination info.
            playlists (Dict[str, Any]): Playlists response containing:
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
                total (int): Total number of playlists in the category
                limit (int): Number of playlists returned in this response
                offset (int): Offset of the first playlist returned
                href (str): URL to the full list of category playlists
                next (Optional[str]): URL to the next page of results
                previous (Optional[str]): URL to the previous page of results

    Raises:
        InvalidInputError: If category_id is not a string or is empty, country is not a valid country code, limit is outside 1-50 range, or offset is negative.
        NoResultsFoundError: If no category exists with the specified category_id.
    """
    # Validate category_id
    utils.validate_category_id(category_id)
    
    # Validate country parameter if provided
    if country is not None:
        if not utils.validate_market(country):
            raise custom_errors.InvalidMarketError("country must be a valid ISO 3166-1 alpha-2 country code.")
    
    # Validate limit and offset
    utils.validate_limit_offset(limit, offset)
    
    # Check if category exists
    categories_table = DB.get('categories', {})
    category_data = categories_table.get(category_id)
    
    if category_data is None:
        raise custom_errors.NoResultsFoundError(f"Category with ID '{category_id}' not found.")
    
    # Get playlists for this category (simulated - in real API this would be based on category tagging)
    playlists_table = DB.get('playlists', {})
    category_playlists = []
    
    for playlist_id, playlist_data in playlists_table.items():
        # For this simulation, we'll include all playlists
        # In a real implementation, this would filter based on category tagging
        category_playlists.append(playlist_data)
    
    # Apply pagination
    result = utils.apply_pagination(category_playlists, limit, offset)
    result['href'] = f"https://api.spotify.com/v1/browse/categories/{category_id}/playlists"
    
    return {'playlists': result}


@tool_spec(
    spec={
        'name': 'get_recommendations',
        'description': """ Get recommendations for one or more seed artists, genres, and/or tracks.
        
        This endpoint creates a playlist of tracks based on the provided seeds and audio features. The response includes detailed track information and can be customized using various audio feature parameters. This is essential for music discovery and creating personalized listening experiences. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'seed_artists': {
                    'type': 'array',
                    'description': """ A list of Spotify IDs for seed artists. Up to 5 seed values may be provided in any combination of seed_artists, seed_tracks and seed_genres.
                    Examples: ['artist_1', 'artist_2'], ['0TnOYISbd1XYRBk9myaseg']. """,
                    'items': {
                        'type': 'string'
                    }
                },
                'seed_genres': {
                    'type': 'array',
                    'description': """ A list of any genres in the set of available genre seeds. Up to 5 seed values may be provided in any combination of seed_artists, seed_tracks and seed_genres.
                    Examples: ['rock', 'pop'], ['classical', 'jazz']. """,
                    'items': {
                        'type': 'string'
                    }
                },
                'seed_tracks': {
                    'type': 'array',
                    'description': """ A list of Spotify IDs for seed tracks. Up to 5 seed values may be provided in any combination of seed_artists, seed_tracks and seed_genres.
                    Examples: ['track_1', 'track_2'], ['4iV5W9uYEdYUVa79Axb7Rh']. """,
                    'items': {
                        'type': 'string'
                    }
                },
                'limit': {
                    'type': 'integer',
                    'description': """ The target size of the list of recommended tracks. For seeds with unusually small pools or when highly restrictive filtering is applied, it may be impossible to generate the requested number of recommended tracks. Debugging information for such cases is available in the response. Default: 20. Minimum: 1. Maximum: 100.
                    Examples: 10 (small selection), 20 (default), 100 (maximum). """
                },
                'market': {
                    'type': 'string',
                    'description': """ An ISO 3166-1 alpha-2 country code. The country for which to get the top tracks.
                    Examples: 'US', 'CA', 'GB', 'DE', 'FR'. """
                }
            },
            'required': []
        }
    }
)
def get_recommendations(
    seed_artists: Optional[List[str]] = None,
    seed_genres: Optional[List[str]] = None,
    seed_tracks: Optional[List[str]] = None,
    limit: Optional[int] = 20,
    market: Optional[str] = None
) -> Dict[str, Any]:
    """Get recommendations for one or more seed artists, genres, and/or tracks.

    This endpoint creates a playlist of tracks based on the provided seeds and audio features. The response includes detailed track information and can be customized using various audio feature parameters. This is essential for music discovery and creating personalized listening experiences.

    Args:
        seed_artists (Optional[List[str]]): A list of Spotify IDs for seed artists. Up to 5 seed values may be provided in any combination of seed_artists, seed_tracks and seed_genres.
            Examples: ['artist_1', 'artist_2'], ['0TnOYISbd1XYRBk9myaseg'].
        seed_genres (Optional[List[str]]): A list of any genres in the set of available genre seeds. Up to 5 seed values may be provided in any combination of seed_artists, seed_tracks and seed_genres.
            Examples: ['rock', 'pop'], ['classical', 'jazz'].
        seed_tracks (Optional[List[str]]): A list of Spotify IDs for seed tracks. Up to 5 seed values may be provided in any combination of seed_artists, seed_tracks and seed_genres.
            Examples: ['track_1', 'track_2'], ['4iV5W9uYEdYUVa79Axb7Rh'].
        limit (Optional[int]): The target size of the list of recommended tracks. For seeds with unusually small pools or when highly restrictive filtering is applied, it may be impossible to generate the requested number of recommended tracks. Debugging information for such cases is available in the response. Default: 20. Minimum: 1. Maximum: 100.
            Examples: 10 (small selection), 20 (default), 100 (maximum).
        market (Optional[str]): An ISO 3166-1 alpha-2 country code. The country for which to get the top tracks.
            Examples: 'US', 'CA', 'GB', 'DE', 'FR'.

    Returns:
        Dict[str, Any]: Recommendations response with seeds and tracks.
            seeds (List[Dict[str, Any]]): Array of seed objects, each containing:
                afterFilteringSize (int): The number of tracks available after filtering
                afterRelinkingSize (int): The number of tracks available after relinking
                href (Optional[str]): A link to the full track or artist data for this seed
                id (str): The ID used to select this seed
                initialPoolSize (int): The number of recommended tracks available for this seed
                type (str): The entity type of this seed ('artist', 'track', or 'genre')
            tracks (List[Dict[str, Any]]): Array of track objects, each containing:
                id (str): Unique track identifier
                name (str): Track name
                type (str): Object type ('track')
                uri (str): Spotify URI for the track
                href (str): API endpoint URL for the track
                external_urls (Dict[str, str]): External URLs for the track
                artists (List[Dict[str, Any]]): Array of artist objects
                album (Dict[str, Any]): Album information
                duration_ms (int): Track duration in milliseconds
                explicit (bool): Whether the track contains explicit content
                track_number (int): Track number on the album
                disc_number (int): Disc number
                available_markets (List[str]): List of markets where track is available
                popularity (int): Popularity score (0-100)
                is_local (bool): Whether the track is a local file
                is_playable (bool): Whether the track is playable

    Raises:
        InvalidInputError: If any seed parameters are invalid, limit is outside 1-100 range, or market is not a valid country code.
    """
    # Validate seed parameters
    total_seeds = 0
    if seed_artists:
        total_seeds += len(seed_artists)
    if seed_genres:
        total_seeds += len(seed_genres)
    if seed_tracks:
        total_seeds += len(seed_tracks)
    
    if total_seeds == 0:
        raise custom_errors.InvalidInputError("At least one seed (artist, genre, or track) must be provided.")
    
    if total_seeds > 5:
        raise custom_errors.InvalidInputError("Maximum 5 seed values allowed in any combination.")
    
    # Validate limit
    if limit is not None:
        if not isinstance(limit, int) or limit < 1 or limit > 100:
            raise custom_errors.InvalidInputError("limit must be an integer between 1 and 100.")
    
    # Validate market parameter if provided
    if market is not None:
        if not utils.validate_market(market):
            raise custom_errors.InvalidMarketError("market must be a valid ISO 3166-1 alpha-2 country code.")
    
    # Get recommendations from DB (simulated)
    recommendations_table = DB.get('recommendations', {})
    
    # Get seeds information
    seeds = []
    if seed_artists:
        for artist_id in seed_artists:
            seeds.append({
                'afterFilteringSize': 1,
                'afterRelinkingSize': 1,
                'href': None,
                'id': artist_id,
                'initialPoolSize': 1,
                'type': 'artist'
            })
    
    if seed_genres:
        for genre in seed_genres:
            seeds.append({
                'afterFilteringSize': 1,
                'afterRelinkingSize': 1,
                'href': None,
                'id': genre,
                'initialPoolSize': 1,
                'type': 'genre'
            })
    
    if seed_tracks:
        for track_id in seed_tracks:
            seeds.append({
                'afterFilteringSize': 1,
                'afterRelinkingSize': 1,
                'href': None,
                'id': track_id,
                'initialPoolSize': 1,
                'type': 'track'
            })
    
    # Get recommended tracks
    tracks_table = DB.get('tracks', {})
    recommended_tracks = []
    
    for track_id, track_data in tracks_table.items():
        # Apply market filtering if specified
        if market is not None:
            available_markets = track_data.get('available_markets', [])
            if market in available_markets:
                recommended_tracks.append(track_data)
        else:
            recommended_tracks.append(track_data)
    
    # Limit to requested number of tracks
    limit = limit or 20
    recommended_tracks = recommended_tracks[:limit]
    
    return {
        'seeds': seeds,
        'tracks': recommended_tracks
    }


@tool_spec(
    spec={
        'name': 'get_available_genre_seeds',
        'description': """ Retrieve a list of available genres seed parameter values for recommendations.
        
        This endpoint retrieves all available genre seeds that can be used as seed_genres in the get_recommendations endpoint. This is useful for building genre selection interfaces or understanding what genres are available for recommendations. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_available_genre_seeds() -> Dict[str, Any]:
    """Retrieve a list of available genres seed parameter values for recommendations.

    This endpoint retrieves all available genre seeds that can be used as seed_genres in the get_recommendations endpoint. This is useful for building genre selection interfaces or understanding what genres are available for recommendations.

    Returns:
        Dict[str, Any]: Available genre seeds response.
            genres (List[str]): Array of available genre seed values
                Examples: ['acoustic', 'afrobeat', 'alt-rock', 'alternative', 'ambient'].

    Raises:
        None: This endpoint does not raise any specific errors.
    """
    # Get genres from DB
    genres_table = DB.get('genres', [])
    
    return {'genres': genres_table} 