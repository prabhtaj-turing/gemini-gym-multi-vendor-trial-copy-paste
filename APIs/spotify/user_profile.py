from common_utils.tool_spec_decorator import tool_spec
from typing import Optional, List, Dict, Any
from datetime import datetime
import copy

from .SimulationEngine.db import DB
from .SimulationEngine import custom_errors, models, utils


@tool_spec(
    spec={
        'name': 'get_current_user_profile',
        'description': """ Get detailed profile information about the current user (including display name, Spotify URI, profile image, and follower count). Requires user authorization.
        
        This endpoint retrieves comprehensive profile information for the currently authenticated user. The response includes personal details, account status, subscription information, and social metrics. This is essential for applications that need to display user information or customize the experience based on user preferences and account type. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        }
    }
)
def get_current_user_profile() -> Dict[str, Any]:
    """Get detailed profile information about the current user (including display name, Spotify URI, profile image, and follower count). Requires user authorization.

    This endpoint retrieves comprehensive profile information for the currently authenticated user. The response includes personal details, account status, subscription information, and social metrics. This is essential for applications that need to display user information or customize the experience based on user preferences and account type.

    Returns:
        Dict[str, Any]: User profile data wrapped in a response dictionary.
            display_name (str): User's display name
            external_urls (Dict[str, str]): External URLs for the user profile
            followers (Dict[str, Any]): Follower information with total count
            href (str): API endpoint URL for this user
            id (str): Unique user identifier
            images (List[Dict[str, Any]]): User profile images
            type (str): Object type ('user')
            uri (str): Spotify URI for the user
            country (Optional[str]): User's country code
            email (Optional[str]): User's email address
            product (Optional[str]): User's subscription type ('premium', 'free', etc.)
            explicit_content (Optional[Dict[str, Any]]): Explicit content filter settings
            birthdate (Optional[str]): User's birthdate
            product_type (Optional[str]): Type of product subscription

    Raises:
        AuthenticationError: If user is not authenticated or token is invalid.
        AuthorizationError: If user does not have required permissions.
    """
    # Get current user from DB using the new function
    try:
        current_user_id = utils.get_current_user_id()
    except custom_errors.NoResultsFoundError:
        raise custom_errors.AuthenticationError("No current user is set. Please authenticate first.")
    
    users_table = DB.get('users', {})
    user_data = users_table.get(current_user_id)
    
    if user_data is None:
        raise custom_errors.AuthenticationError("User not found or not authenticated.")
    
    # Return user profile data
    return user_data


@tool_spec(
    spec={
        'name': 'get_user_top_artists_and_tracks',
        'description': """ Get the current user's top artists or tracks based on their listening history. This can be used for personalized recommendations or statistics.
        
        This endpoint provides access to the user's most listened to artists or tracks over different time periods. The data is based on the user's listening history and can be filtered by time range (short term, medium term, or long term). This is particularly useful for creating personalized experiences, generating recommendations, or displaying user statistics. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'type': {
                    'type': 'string',
                    'description': """ The type of entity to return. Valid values: 'artists' or 'tracks'.
                    Examples: 'artists' (for top artists), 'tracks' (for top tracks). """
                },
                'limit': {
                    'type': 'integer',
                    'description': """ The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
                    Examples: 10 (small selection), 20 (default), 50 (maximum). """
                },
                'offset': {
                    'type': 'integer',
                    'description': """ The index of the first item to return. Default: 0 (the first object).
                    Examples: 0 (start from beginning), 20 (skip first 20 items). """
                },
                'time_range': {
                    'type': 'string',
                    'description': """ Over what time frame the affinities are computed. Valid values: 'long_term', 'medium_term', 'short_term'. Default: 'medium_term'.
                    Examples: 'short_term' (last 4 weeks), 'medium_term' (last 6 months), 'long_term' (calculated from several years). """
                }
            },
            'required': [
                'type'
            ]
        }
    }
)
def get_user_top_artists_and_tracks(
    type: str,
    limit: int = 20,
    offset: int = 0,
    time_range: str = "medium_term"
) -> Dict[str, Any]:
    """Get the current user's top artists or tracks based on their listening history. This can be used for personalized recommendations or statistics.

    This endpoint provides access to the user's most listened to artists or tracks over different time periods. The data is based on the user's listening history and can be filtered by time range (short term, medium term, or long term). This is particularly useful for creating personalized experiences, generating recommendations, or displaying user statistics.

    Args:
        type (str): The type of entity to return. Valid values: 'artists' or 'tracks'.
            Examples: 'artists' (for top artists), 'tracks' (for top tracks).
        limit (int): The maximum number of items to return. Default: 20. Minimum: 1. Maximum: 50.
            Examples: 10 (small selection), 20 (default), 50 (maximum).
        offset (int): The index of the first item to return. Default: 0 (the first object).
            Examples: 0 (start from beginning), 20 (skip first 20 items).
        time_range (str): Over what time frame the affinities are computed. Valid values: 'long_term', 'medium_term', 'short_term'. Default: 'medium_term'.
            Examples: 'short_term' (last 4 weeks), 'medium_term' (last 6 months), 'long_term' (calculated from several years).

    Returns:
        Dict[str, Any]: Top items response with items array and pagination info.
            items (List[Dict[str, Any]]): Array of top artists or tracks, each containing:
                id (str): Unique identifier for the item
                name (str): Name of the artist or track
                type (str): Object type ('artist' or 'track')
                uri (str): Spotify URI for the item
                href (str): API endpoint URL for the item
                external_urls (Dict[str, str]): External URLs for the item
                images (List[Dict[str, Any]]): Images for the item (artists only)
                followers (Dict[str, Any]): Follower information (artists only)
                genres (List[str]): Genres associated with the item (artists only)
                popularity (int): Popularity score (0-100)
                artists (List[Dict[str, Any]]): Artist information (tracks only)
                album (Dict[str, Any]): Album information (tracks only)
                duration_ms (int): Track duration in milliseconds (tracks only)
                explicit (bool): Whether the track contains explicit content (tracks only)
            total (int): Total number of items available
            limit (int): Number of items returned in this response
            offset (int): Offset of the first item returned
            href (str): URL to the full list of items
            next (Optional[str]): URL to the next page of results
            previous (Optional[str]): URL to the previous page of results

    Raises:
        InvalidInputError: If type is not 'artists' or 'tracks', limit is outside 1-50 range, offset is negative, or time_range is invalid.
        AuthenticationError: If user is not authenticated.
        AuthorizationError: If user does not have required permissions.
    """
    # Validate type parameter
    if type not in ['artists', 'tracks']:
        raise custom_errors.InvalidInputError("type must be either 'artists' or 'tracks'.")
    
    # Validate limit parameter
    if limit is not None:
        if not isinstance(limit, int) or limit < 1 or limit > 50:
            raise custom_errors.InvalidInputError("limit must be an integer between 1 and 50.")
    
    # Validate offset parameter
    if offset is not None:
        if not isinstance(offset, int) or offset < 0:
            raise custom_errors.InvalidInputError("offset must be a non-negative integer.")
    
    # Validate time_range parameter
    valid_time_ranges = ['long_term', 'medium_term', 'short_term']
    if time_range not in valid_time_ranges:
        raise custom_errors.InvalidInputError(f"time_range must be one of: {', '.join(valid_time_ranges)}")
    
    # Get current user from DB using the new function
    try:
        current_user_id = utils.get_current_user_id()
    except custom_errors.NoResultsFoundError:
        raise custom_errors.AuthenticationError("No current user is set. Please authenticate first.")
    
    # Get top items based on type
    if type == 'artists':
        top_items_data = DB.get('top_artists', {}).get(current_user_id, {})
        items_key = 'artists'
    else:  # type == 'tracks'
        top_items_data = DB.get('top_tracks', {}).get(current_user_id, {})
        items_key = 'tracks'
    
    if not top_items_data:
        raise custom_errors.NoResultsFoundError(f"No top {type} found for the current user.")
    
    items = top_items_data.get(items_key, [])
    total = len(items)
    
    # Apply pagination
    start = offset or 0
    end = start + (limit or 20)
    paginated_items = items[start:end]
    
    # Construct response
    response = {
        'items': paginated_items,
        'total': total,
        'limit': limit or 20,
        'offset': offset or 0,
        'href': f"https://api.spotify.com/v1/me/top/{type}",
        'next': None,
        'previous': None
    }
    
    # Add pagination links if applicable
    if end < total:
        response['next'] = f"https://api.spotify.com/v1/me/top/{type}?limit={limit or 20}&offset={end}"
    
    if start > 0:
        prev_offset = max(0, start - (limit or 20))
        response['previous'] = f"https://api.spotify.com/v1/me/top/{type}?limit={limit or 20}&offset={prev_offset}"
    
    return response


@tool_spec(
    spec={
        'name': 'get_user_profile',
        'description': """ Get public profile information about a Spotify user.
        
        This endpoint retrieves public profile information for any Spotify user by their user ID. The response includes basic profile information such as display name, profile images, and follower count. This is useful for displaying user information in playlists, collaborative features, or social aspects of music applications. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'user_id': {
                    'type': 'string',
                    'description': """ The user's Spotify ID.
                    Examples: 'smuqPNFPXrJKcEt943KrY8', 'SLvTb0e3Rp3oLJ8YXl0dC5'. """
                }
            },
            'required': [
                'user_id'
            ]
        }
    }
)
def get_user_profile(user_id: str) -> Dict[str, Any]:
    """Get public profile information about a Spotify user.

    This endpoint retrieves public profile information for any Spotify user by their user ID. The response includes basic profile information such as display name, profile images, and follower count. This is useful for displaying user information in playlists, collaborative features, or social aspects of music applications.

    Args:
        user_id (str): The user's Spotify ID.
            Examples: 'smuqPNFPXrJKcEt943KrY8', 'SLvTb0e3Rp3oLJ8YXl0dC5'.

    Returns:
        Dict[str, Any]: User profile data.
            display_name (str): User's display name
            external_urls (Dict[str, str]): External URLs for the user profile
            followers (Dict[str, Any]): Follower information with total count
            href (str): API endpoint URL for this user
            id (str): Unique user identifier
            images (List[Dict[str, Any]]): User profile images
            type (str): Object type ('user')
            uri (str): Spotify URI for the user

    Raises:
        InvalidInputError: If user_id is not a string or is empty.
        NoResultsFoundError: If no user exists with the specified user_id.
    """
    # Validate user_id
    if not isinstance(user_id, str):
        raise custom_errors.InvalidInputError("user_id must be a string.")
    
    if not user_id:
        raise custom_errors.InvalidInputError("user_id cannot be empty.")
    
    # Get user data from DB
    users_table = DB.get('users', {})
    user_data = users_table.get(user_id)
    
    if user_data is None:
        raise custom_errors.NoResultsFoundError(f"User with ID '{user_id}' not found.")
    
    # Return user profile data
    return user_data 