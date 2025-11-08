from common_utils.tool_spec_decorator import tool_spec
# google_maps_live/places.py

import json
import re
from typing import Any, Dict, List, Optional, Union

from pydantic import ValidationError

from common_utils.print_log import print_log
from google_maps_live.SimulationEngine.custom_errors import ParseError
from google_maps_live.SimulationEngine.models import (
    AnalyzePlacesInput,
    AnalyzeResult,
    LookupPlaceDetailsInput,
    Place,
    PriceLevel,
    QueryPlacesInput,
    ShowMapResult,
    ShowOnMapInput,
    SummaryPlaces,
    UserLocation,
)
from google_maps_live.SimulationEngine.utils import (
    add_recent_search,
    get_gemini_response,
    get_model_from_gemini_response,
    parse_json_from_gemini_response,
)


@tool_spec(
    spec={
        'name': 'query_places',
        'description': """ Query and locate places or geographical entities.
        
        This function searches for businesses, stores, restaurants, parks, attractions, cities, 
        countries, and other places of interest. It can handle multiple queries and returns 
        structured place data. All inputs are validated using Pydantic models.
        
        Note: This API cannot handle generic Google search queries or image search queries. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'array',
                    'description': """ List of search queries describing desired characteristics of places.
                    Must contain at least one query. Examples: ["coffee shops", "parks near me"] """,
                    'items': {
                        'type': 'string'
                    }
                },
                'location_bias': {
                    'description': """ Location bias for search results. 
                    Can be a place name string, coordinate dict 
                    {"latitude": float, "longitude": float}, or string names of environment variables:
                    - "MY_HOME": User's home location from environment
                    - "MY_LOCATION": User's current location from environment
                    - "MY_WORK": User's work location from environment """,
                    'anyOf': [
                        {
                            'type': 'STRING',
                            'description': 'Place name or environment variable (MY_HOME, MY_LOCATION, MY_WORK)'
                        },
                        {
                            'type': 'OBJECT',
                            'description': 'Coordinate dictionary with latitude and longitude',
                            'properties': {
                                'latitude': {
                                    'type': 'number',
                                    'description': 'Latitude in decimal degrees',
                                    'minimum': -90,
                                    'maximum': 90
                                },
                                'longitude': {
                                    'type': 'number',
                                    'description': 'Longitude in decimal degrees',
                                    'minimum': -180,
                                    'maximum': 180
                                }
                            },
                            'required': ['latitude', 'longitude']
                        }
                    ]
                },
                'only_open_now': {
                    'type': 'boolean',
                    'description': 'If True, filters results to show only places currently open.'
                },
                'min_rating': {
                    'type': 'number',
                    'description': """ Minimum rating filter (1.0 to 5.0). Returns only places with 
                    this rating or higher. """
                },
                'price_levels': {
                    'type': 'array',
                    'description': """ Price level filters. Supported values: "inexpensive", 
                    "moderate", "expensive", "very_expensive". """,
                    'items': {
                        'type': 'string'
                    }
                },
                'rank_preference': {
                    'type': 'string',
                    'description': 'Ranking preference for results. Supported values: "default", "distance".'
                },
                'search_along_route': {
                    'type': 'object',
                    'description': 'Parameters for searching along route support. It includes the id of the route to be searched along and the stop location offset in fraction along the route origin, e.g., 0.5.',
                    'properties': {
                        'routeId': {
                            'type': 'string',
                            'description': 'ID of the route to be searched along'
                        },
                        'routeOriginOffsetFraction': {
                            'type': 'number',
                            'description': 'Stop location offset in fraction along the route origin (0.0 to 1.0)'
                        }
                    },
                    'required': ['routeId', 'routeOriginOffsetFraction']
                },
                'in_history': {
                    'type': 'boolean',
                    'description': 'Whether to search in history (currently unsupported).'
                },
                'is_saved': {
                    'type': 'boolean',
                    'description': 'Whether to search saved places (currently unsupported).'
                },
                'immersive_view': {
                    'type': 'boolean',
                    'description': 'Whether to include immersive views (currently unsupported).'
                }
            },
            'required': [
                'query'
            ]
        }
    }
)
def query_places(
    query: List[str],
    location_bias: Optional[Union[str, Dict[str, float]]] = None,
    only_open_now: Optional[bool] = None,
    min_rating: Optional[float] = None,
    price_levels: Optional[List[str]] = None,
    rank_preference: Optional[str] = None,
    search_along_route: Optional[Dict[str, Dict[str, str]]] = None,
    in_history: Optional[bool] = None,
    is_saved: Optional[bool] = None,
    immersive_view: Optional[bool] = None
) -> Dict[str, Union[str, List[Dict[str, Union[str, float]]], List[Dict[str, str]]]]:
    """
    Query and locate places or geographical entities.
    
    This function searches for businesses, stores, restaurants, parks, attractions, cities, 
    countries, and other places of interest. It can handle multiple queries and returns 
    structured place data. All inputs are validated using Pydantic models.
    
    Note: This API cannot handle generic Google search queries or image search queries.
    
    Args:
        query (List[str]): List of search queries describing desired characteristics of places.
                          Must contain at least one query. Examples: ["coffee shops", "parks near me"]
        location_bias (Optional[Union[str, Dict[str, float]]]): Location bias for search results. 
                                                             Can be a place name string, coordinate dict 
                                                             {"latitude": float, "longitude": float}, or string names of environment variables:
                                                             - "MY_HOME": User's home location from environment
                                                             - "MY_LOCATION": User's current location from environment
                                                             - "MY_WORK": User's work location from environment
        only_open_now (Optional[bool]): If True, filters results to show only places currently open.
        min_rating (Optional[float]): Minimum rating filter (1.0 to 5.0). Returns only places with 
                                     this rating or higher.
        price_levels (Optional[List[str]]): Price level filters. Supported values: "inexpensive", 
                                           "moderate", "expensive", "very_expensive".
        rank_preference (Optional[str]): Ranking preference for results. Supported values: "default", "distance".
        search_along_route (Optional[Dict[str, Dict[str, str]]]): Parameters for searching along route support. It includes the id of the route to be searched along and the stop location offset in fraction along the route origin, e.g., 0.5.
            routeId (str): ID of the route to be searched along
            routeOriginOffsetFraction (float): Stop location offset in fraction along the route origin (0.0 to 1.0)
        in_history (Optional[bool]): Whether to search in history (currently unsupported).
        is_saved (Optional[bool]): Whether to search saved places (currently unsupported).
        immersive_view (Optional[bool]): Whether to include immersive views (currently unsupported).
    
    Returns:
        Dict[str, Union[str, List[Dict[str, Union[str, float]]], List[Dict[str, str]]]]: Summary of places containing:
            - map_url (str): URL to view places on Google Maps
            - places (List[Dict[str, Union[str, float]]]): List of places with details including:
                - name (str): Place name
                - description (str): Place description
                - address (str): Full address
                - phone (str): Phone number
                - website (str): Website URL
                - rating (float): Average rating (1.0-5.0)
                - price_level (str): Price level indicator
                - place_id (str): Unique place identifier
            - detours (List[Dict[str, str]]): List of detour information (if applicable)
                - detour_duration (str): Duration of the detour
                - detour_distance (str): Distance of the detour
            - query (str): The search query used
    
    Raises:
        ValueError: If query list is empty
        ValueError: If min_rating is not between 1.0 and 5.0
        ValueError: If invalid price_levels are provided
        ValueError: If invalid rank_preference is provided
        ValueError: If input validation fails
        ParseError: If JSON parsing from API response fails
        NotImplementedError: If API response cannot be parsed as valid JSON
        ValidationError: If response data doesn't match expected schema
        UndefinedLocationError: If UserLocation environment variable is not set
    """
    
    # Use Pydantic model for input validation
    try:
        input_data = QueryPlacesInput(
            query=query,
            location_bias=location_bias,
            only_open_now=only_open_now,
            min_rating=min_rating,
            price_levels=price_levels,
            rank_preference=rank_preference,
            search_along_route=search_along_route,
            in_history=in_history,
            is_saved=is_saved,
            immersive_view=immersive_view
        )
    except ValidationError as e:
        # Convert Pydantic validation errors to user-friendly messages
        errors = e.errors()
        if errors:
            first_error = errors[0]
            field_name = str(first_error['loc'][0])
            error_type = first_error['type']
            
            if field_name == 'query':
                raise ValueError("Query list cannot be empty")
            elif field_name == 'min_rating':
                raise ValueError("min_rating must be between 1.0 and 5.0")
            elif field_name == 'price_levels':
                raise ValueError("Invalid price level")
            elif field_name == 'rank_preference':
                raise ValueError("Invalid rank_preference")
            else:
                raise ValueError(str(e))
        else:
            raise ValueError(str(e))
    
    # Use API for intelligent place search
    search_query = f"Find places for: {', '.join(input_data.query)}"
    if input_data.location_bias:
        search_query += f" near {input_data.location_bias}"
    if input_data.only_open_now:
        search_query += " that are open now"
    if input_data.min_rating:
        search_query += f" with rating {input_data.min_rating} or higher"
    if input_data.price_levels:
        price_level_names = [priceLevel.value for priceLevel in input_data.price_levels]
        search_query += f" with price levels: {', '.join(price_level_names)}"
    
    search_query += f"""
    Return the response following this JSON schema:
    ```json
    {json.dumps(SummaryPlaces.model_json_schema(), indent=2)}
    ```
    Make sure to include the `map_url`, `places`, and `query` fields in the `SummaryPlaces` model. Use empty strings for any fields that are not available or null.
    For each `Place` in the `places` list, include `id`, `name`, `rating`, `review_count`, `user_rating_count`, `address`, and `phone_number`.
    Use 0 for review_count and user_rating_count if they are not available and use empty strings for any other fields that are not available or null.
    """
    
    print_log(f"Querying Gemini for places")
    summary_places = get_model_from_gemini_response(search_query, SummaryPlaces)

    add_recent_search(
        endpoint="query_places",
        parameters=input_data.get_non_empty_fields(),
        result=summary_places.model_dump())
    
    return summary_places.model_dump()


@tool_spec(
    spec={
        'name': 'lookup_place_details',
        'description': """ Fetch detailed information about places using their IDs.
        
        This function retrieves enriched place details for the specified place IDs.
        All inputs are validated using Pydantic models. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'place_ids': {
                    'type': 'array',
                    'description': 'List of place ids.',
                    'items': {
                        'type': 'string'
                    }
                },
                'query': {
                    'type': 'string',
                    'description': """ Optional query which query can be used for semantic filtering 
                    of place data, e.g. finding relevant reviews. """
                }
            },
            'required': [
                'place_ids'
            ]
        }
    }
)
def lookup_place_details(
    place_ids: List[str],
    query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch detailed information about places using their IDs.
    
    This function retrieves enriched place details for the specified place IDs.
    All inputs are validated using Pydantic models.
    
    Args:
        place_ids (List[str]): List of place ids.
        query (Optional[str]): Optional query which query can be used for semantic filtering 
                              of place data, e.g. finding relevant reviews.
    
    Returns:
        List[Dict[str, Any]]: List of places with detailed information.
    
    Raises:
        ValueError: If place_ids list is empty
        ParseError: If JSON parsing from API response fails
        NotImplementedError: If API response cannot be parsed as valid JSON
        ValidationError: If response data doesn't match expected schema
    """
    
    # Use Pydantic model for input validation
    try:
        input_data = LookupPlaceDetailsInput(
            place_ids=place_ids,
            query=query
        )
    except ValidationError as e:
        # Convert Pydantic validation errors to user-friendly messages
        errors = e.errors()
        if errors:
            first_error = errors[0]
            field_name = str(first_error['loc'][0])
            error_type = first_error['type']
            
            if field_name == 'place_ids':
                raise ValueError("place_ids list cannot be empty")
            else:
                raise ValueError(str(e))
        else:
            raise ValueError(str(e))
    
    # Use Gemini for detailed place information
    details_query = f"Get detailed information about places: {', '.join(input_data.place_ids)}"
    if input_data.query:
        details_query += f" focusing on: {input_data.query}"
    
    details_query += f"""
    Return the response as a list of places following this JSON schema:
    ```json
    {json.dumps(Place.model_json_schema(), indent=2)}
    ```
    For each `Place`, ensure all fields have non-null values, especially `id`, `name`, `rating`, `review_count`, `user_rating_count`, `address`, and `phone_number`.
    Use 0 for review_count and user_rating_count if they are not available and use empty strings for any other fields that are not available or null.
    """
    
    print_log(f"Querying Gemini for place details")
    gemini_response = get_gemini_response(details_query)

    try:
        json_response = parse_json_from_gemini_response(gemini_response)
    except ParseError as e:
        raise NotImplementedError(gemini_response)
    
    # Validate each place in the list
    places = []
    for place_data in json_response:
        try:
            place = Place(**place_data)
            places.append(place)
        except ValidationError as e:
            print_log(f"Validation error for place data: {e}")
            # Continue with other places if one fails validation
            continue
    
    if not places:
        raise ValueError("No valid places found in response")
    
    result = [place.model_dump() for place in places]
    
    add_recent_search(
        endpoint="lookup_place_details",
        parameters=input_data.get_non_empty_fields(),
        result=result)
    
    return result


@tool_spec(
    spec={
        'name': 'analyze_places',
        'description': """ Analyze places using natural language queries.
        
        This function provides intelligent analysis of places based on natural language questions.
        All inputs are validated using Pydantic models. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'place_ids': {
                    'type': 'array',
                    'description': 'List of place ids.',
                    'items': {
                        'type': 'string'
                    }
                },
                'question': {
                    'type': 'string',
                    'description': 'Question in natural language form.'
                }
            },
            'required': [
                'place_ids',
                'question'
            ]
        }
    }
)
def analyze_places(
    place_ids: List[str],
    question: str
) -> Dict[str, Any]:
    """
    Analyze places using natural language queries.
    
    This function provides intelligent analysis of places based on natural language questions.
    All inputs are validated using Pydantic models.
    
    Args:
        place_ids (List[str]): List of place ids.
        question (str): Question in natural language form.
    
    Returns:
        Dict[str, Any]: Analyze result containing:
            - map_answer (str): Analysis result in natural language form
            - web_answers (List[Dict]): List of web answers
            - place_images_passthrough (str): Image data (hidden from model)
            - image_grid_passthrough (str): Image grid data (hidden from model)
    
    Raises:
        ValueError: If place_ids list is empty
        ValueError: If question is empty
        ParseError: If JSON parsing from API response fails
        NotImplementedError: If API response cannot be parsed as valid JSON
        ValidationError: If response data doesn't match expected schema
    """
    
    # Use Pydantic model for input validation
    try:
        input_data = AnalyzePlacesInput(
            place_ids=place_ids,
            question=question
        )
    except ValidationError as e:
        # Convert Pydantic validation errors to user-friendly messages
        errors = e.errors()
        if errors:
            first_error = errors[0]
            field_name = str(first_error['loc'][0])
            error_type = first_error['type']
            
            if field_name == 'place_ids':
                raise ValueError("place_ids list cannot be empty")
            elif field_name == 'question':
                # Handle both Pydantic min_length and custom validator errors
                if error_type == 'string_too_short' or error_type == 'value_error':
                    raise ValueError("question cannot be empty")
                else:
                    raise ValueError(str(e))
            else:
                raise ValueError(str(e))
        else:
            raise ValueError(str(e))
    
    # Use Gemini for intelligent place analysis
    analysis_query = f"Analyze places {', '.join(input_data.place_ids)} and answer this question: {input_data.question}"
    
    analysis_query += f"""
    Return the response following this JSON schema:
    ```json
    {json.dumps(AnalyzeResult.model_json_schema(), indent=2)}
    ```
    Ensure the `map_answer` field is always populated with a non-null value. Use empty strings if not available or null.
    """
    
    print_log(f"Querying Gemini for analysis")
    analyze_result = get_model_from_gemini_response(analysis_query, AnalyzeResult)

    add_recent_search(
        endpoint="analyze_places",
        parameters=input_data.get_non_empty_fields(),
        result=analyze_result.model_dump())

    return analyze_result.model_dump()


@tool_spec(
    spec={
        'name': 'show_on_map',
        'description': """ Display places on a map.
        
        This function generates a map containing pins for the specified places.
        All inputs are validated using Pydantic models. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'places': {
                    'type': 'array',
                    'description': """ List of place ids or place names to be shown on the map. 
                    If place ids are provided, they should always have a prefix 'place_id://'. """,
                    'items': {
                        'type': 'string'
                    }
                }
            },
            'required': []
        }
    }
)
def show_on_map(
    places: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Display places on a map.
    
    This function generates a map containing pins for the specified places.
    All inputs are validated using Pydantic models.
    
    Args:
        places (Optional[List[str]]): List of place ids or place names to be shown on the map. 
                                     If place ids are provided, they should always have a prefix 'place_id://'.
    
    Returns:
        Dict[str, Any]: Show map result containing:
            - content_id (str): Unique identifier for the map content
            - place_marker_passthrough (str): Place marker data (hidden from model)
            - map_title (str): Title for the map (hidden from model)
    
    Raises:
        ValueError: If places list is empty when provided
        ParseError: If JSON parsing from API response fails
        NotImplementedError: If API response cannot be parsed as valid JSON
        ValidationError: If response data doesn't match expected schema
    """
    
    # Use Pydantic model for input validation
    try:
        input_data = ShowOnMapInput(places=places)
    except ValidationError as e:
        # Convert Pydantic validation errors to user-friendly messages
        errors = e.errors()
        if errors:
            first_error = errors[0]
            field_name = str(first_error['loc'][0])
            error_type = first_error['type']
            
            if field_name == 'places':
                raise ValueError("places list cannot be empty when provided")
            else:
                raise ValueError(str(e))
        else:
            raise ValueError(str(e))
    
    # Use Gemini to generate map title and content
    map_query = "Generate a map title and description for displaying places on a map"
    if input_data.places:
        map_query += f" including: {', '.join(input_data.places)}"
    else:
        map_query += " for a general map view"
    
    map_query += f"""
    Return the response following this JSON schema:
    ```json
    {json.dumps(ShowMapResult.model_json_schema(), indent=2)}
    ```
    Ensure the `content_id` field is always populated with a non-null value.
    Use empty string if `content_id` is not available or null.
    """
    
    print_log(f"Querying Gemini for map display")
    show_map_result = get_model_from_gemini_response(map_query, ShowMapResult)

    add_recent_search(
        endpoint="show_on_map",
        parameters=input_data.get_non_empty_fields(),
        result=show_map_result.model_dump())

    return show_map_result.model_dump() 