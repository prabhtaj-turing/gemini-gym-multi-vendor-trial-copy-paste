from common_utils.tool_spec_decorator import tool_spec
import json
import re
from typing import Any, Dict, List, Optional, Union

from common_utils.print_log import print_log
from pydantic import ValidationError

from google_maps_live.SimulationEngine.custom_errors import ParseError, UndefinedLocationError
from google_maps_live.SimulationEngine.models import (
    FindDirectionsInput,
    NavigateInput,
    TravelMode,
    DirectionsSummary,
    UserLocation,
)
from google_maps_live.SimulationEngine.utils import (
    get_model_from_gemini_response,
    add_recent_search,
    get_location_from_env,
)

@tool_spec(
    spec={
        'name': 'find_directions',
        'description': """ Find directions between two places.
        
        This function generates intelligent route analysis and returns structured direction data.
        All inputs are validated using Pydantic models. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'destination': {
                    'type': 'string',
                    'description': 'The destination place (required).'
                },
                'origin': {
                    'type': 'string',
                    'description': """ The origin place. If not provided, will use "current location" 
                    Can be empty if origin is not found in user query. """
                },
                'travel_mode': {
                    'type': 'string',
                    'description': """ The travel mode to use. Supported values: driving, walking, 
                    bicycling, transit, bus, rail, subway, train, tram. 
                    Defaults to "driving" if not specified. """
                },
                'waypoints': {
                    'type': 'array',
                    'description': """ A list of locations to pass through or stop over at, 
                    e.g. ["Googleplex, Mountain View, CA", "Computer History Museum, Mountain View, CA"] """,
                    'items': {
                        'type': 'string'
                    }
                },
                'avoid': {
                    'type': 'array',
                    'description': """ A list of features to avoid for the routes. Supports: tolls, 
                    highways, ferries, indoor. e.g. ["tolls", "highways", "ferries"] """,
                    'items': {
                        'type': 'string'
                    }
                },
                'origin_location_bias': {
                    'description': """ Location bias for origin. 
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
                'destination_location_bias': {
                    'description': """ Location bias for destination. 
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
                'search_along_route': {
                    'type': 'boolean',
                    'description': 'Whether to search along the route (currently unsupported).'
                },
                'departure_time': {
                    'type': 'integer',
                    'description': """ Desired time of departure in seconds since Unix epoch. 
                    Cannot be used with arrival_time. """
                },
                'arrival_time': {
                    'type': 'integer',
                    'description': """ Desired time of arrival in seconds since Unix epoch. 
                    Cannot be used with departure_time. """
                }
            },
            'required': [
                'destination'
            ]
        }
    }
)
def find_directions(
    destination: str,
    origin: Optional[str] = None,
    travel_mode: Optional[str] = None,
    waypoints: Optional[List[str]] = None,
    avoid: Optional[List[str]] = None,
    origin_location_bias: Optional[Union[str, Dict[str, Any]]] = None,
    destination_location_bias: Optional[Union[str, Dict[str, Any]]] = None,
    search_along_route: Optional[bool] = None,
    departure_time: Optional[int] = None,
    arrival_time: Optional[int] = None
) -> Dict[str, Any]:
    """
    Find directions between two places.
    
    This function generates intelligent route analysis and returns structured direction data.
    All inputs are validated using Pydantic models.
    
    Args:
        destination (str): The destination place (required).
        origin (Optional[str]): The origin place. If not provided, will use "current location" 
                                Can be empty if origin is not found in user query.
        travel_mode (Optional[str]): The travel mode to use. Supported values: driving, walking, 
                                   bicycling, transit, bus, rail, subway, train, tram. 
                                   Defaults to "driving" if not specified.
        waypoints (Optional[List[str]]): A list of locations to pass through or stop over at, 
                                       e.g. ["Googleplex, Mountain View, CA", "Computer History Museum, Mountain View, CA"]
        avoid (Optional[List[str]]): A list of features to avoid for the routes. Supports: tolls, 
                                   highways, ferries, indoor. e.g. ["tolls", "highways", "ferries"]
        origin_location_bias (Optional[Union[str, Dict[str, Any]]]): Location bias for origin. 
                                                                     Can be a place name string, coordinate dict 
                                                                     {"latitude": float, "longitude": float}, or string names of environment variables:
                                                                     - "MY_HOME": User's home location from environment
                                                                     - "MY_LOCATION": User's current location from environment  
                                                                     - "MY_WORK": User's work location from environment
        destination_location_bias (Optional[Union[str, Dict[str, Any]]]): Location bias for destination. 
                                                                         Can be a place name string, coordinate dict 
                                                                         {"latitude": float, "longitude": float}, or string names of environment variables:
                                                                         - "MY_HOME": User's home location from environment
                                                                         - "MY_LOCATION": User's current location from environment
                                                                         - "MY_WORK": User's work location from environment
        search_along_route (Optional[bool]): Whether to search along the route (currently unsupported).
        departure_time (Optional[int]): Desired time of departure in seconds since Unix epoch. 
                                       Cannot be used with arrival_time.
        arrival_time (Optional[int]): Desired time of arrival in seconds since Unix epoch. 
                                     Cannot be used with departure_time.
    
    Returns:
        Dict[str, Any]: Direction summary containing:
            - map_url (str): URL to view the route on Google Maps
            - travel_mode (str): The travel mode used for the route
            - routes (List[Dict]): List of route options with details including:
                - distance (str): Route distance (e.g., "37.8 miles")
                - duration (str): Estimated travel time (e.g., "45m")
                - start_address (str): Starting address
                - end_address (str): Destination address
                - mode (str): Travel mode for this route
                - route_id (str): Unique route identifier
                - steps (List[str]): Turn-by-turn directions
                - summary (str): Route summary
                - url (str): Direct link to this route
    
    Raises:
        ValueError: If both departure_time and arrival_time are specified
        ValueError: If invalid travel_mode is provided
        ValueError: If invalid avoid features are provided
        ValueError: If input validation fails (empty waypoints, invalid times, etc.)
        ParseError: If JSON parsing from API response fails
        NotImplementedError: If API response cannot be parsed as valid JSON
        ValidationError: If response data doesn't match expected schema
        UndefinedLocationError: If UserLocation environment variable is not set
    """
    
    # Use Pydantic model for input validation
    try:
        input_data = FindDirectionsInput(
            destination=destination,
            origin=origin,
            travel_mode=travel_mode,
            waypoints=waypoints,
            avoid=avoid,
            origin_location_bias=origin_location_bias,
            destination_location_bias=destination_location_bias,
            search_along_route=search_along_route,
            departure_time=departure_time,
            arrival_time=arrival_time
        )
    except ValidationError as e:
        # Convert Pydantic validation errors to user-friendly messages
        errors = e.errors()
        if errors:
            first_error = errors[0]
            field_name = str(first_error['loc'][0])
            error_type = first_error['type']
            
            if field_name == 'travel_mode':
                raise ValueError("Invalid travel_mode")
            elif field_name == 'avoid':
                raise ValueError("Invalid avoid feature")
            else:
                raise ValueError(str(e))
        else:
            raise ValueError(str(e))
    
    # Additional validation for departure_time and arrival_time conflict
    if departure_time is not None and arrival_time is not None:
        raise ValueError("Cannot specify both departure_time and arrival_time")
    
    # Default travel mode if not specified
    if not input_data.travel_mode:
        travel_mode = TravelMode.DRIVING.value
    else:
        travel_mode = input_data.travel_mode.value
    
    resolved_origin = input_data.origin
    if not resolved_origin:
        try:
            resolved_origin = get_location_from_env(UserLocation.MY_LOCATION.value)
        except UndefinedLocationError:
            print_log(f"MY_LOCATION environment variable is not set.")
            resolved_origin = None
    
    # Use Gemini to get intelligent route analysis
    route_query = f"Find directions to {input_data.destination}" if resolved_origin is None else f"Find directions from {resolved_origin} to {input_data.destination}"
    if travel_mode and travel_mode != TravelMode.DRIVING.value:
        route_query += f" using {travel_mode}"
    if input_data.waypoints:
        route_query += f" via {', '.join(input_data.waypoints)}"
    if input_data.avoid:
        route_query += f" avoiding {', '.join([a.value for a in input_data.avoid])}"
    if input_data.origin_location_bias:
        route_query += f" with origin bias: {input_data.origin_location_bias}"
    if input_data.destination_location_bias:
        route_query += f" with destination bias: {input_data.destination_location_bias}"
    if input_data.departure_time:
        route_query += f" departing at {input_data.departure_time}"
    if input_data.arrival_time:
        route_query += f" arriving at {input_data.arrival_time}"
    
    route_query += f"""
    Return the response following this JSON schema:
    ```json
    {json.dumps(DirectionsSummary.model_json_schema(), indent=2)}
    ```
    Make sure to include the `map_url`, `travel_mode`, and `routes` fields in the `DirectionsSummary` model. 
    Use empty strings for any fields that are not available or null.
    For each `Route` in the `routes` list, include `route_id`, `start_address`, `end_address`, `distance`, `duration`, `summary`, `url`, and `mode`. 
    Use empty strings for any fields that are not available or null.
    """
    
    print_log(f"Querying Gemini for directions")
    directions_summary = get_model_from_gemini_response(route_query, DirectionsSummary)
    
    add_recent_search(
        endpoint="find_directions",
        parameters=input_data.get_non_empty_fields(),
        result=directions_summary.model_dump())
    
    return directions_summary.model_dump()


@tool_spec(
    spec={
        'name': 'navigate',
        'description': """ Navigate from current location to a destination.
        
        This function is similar to find_directions but specifically designed for navigation
        from the user's current location. It generates intelligent route analysis
        and returns structured direction data. All inputs are validated using Pydantic models.
        
        Note: This function assumes "current location" as the starting point.
        For real-world applications, you would need to provide actual GPS coordinates. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'destination': {
                    'type': 'string',
                    'description': 'The destination place (required).'
                },
                'travel_mode': {
                    'type': 'string',
                    'description': """ The travel mode to use. Supported values: driving, walking, 
                    bicycling, transit, bus, rail, subway, train, tram. 
                    Defaults to "driving" if not specified. """
                },
                'waypoints': {
                    'type': 'array',
                    'description': """ A list of locations to pass through or stop over at, 
                    e.g. ["Googleplex, Mountain View, CA", "Computer History Museum, Mountain View, CA"] """,
                    'items': {
                        'type': 'string'
                    }
                },
                'avoid': {
                    'type': 'array',
                    'description': """ A list of features to avoid for the routes. Supports: tolls, 
                    highways, ferries, indoor. e.g. ["tolls", "highways", "ferries"] """,
                    'items': {
                        'type': 'string'
                    }
                },
                'origin_location_bias': {
                    'description': """ Location bias for origin. 
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
                'destination_location_bias': {
                    'description': """ Location bias for destination. 
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
                }
            },
            'required': [
                'destination',
                'origin_location_bias'
            ]
        }
    }
)
def navigate(
    destination: str,
    travel_mode: Optional[str] = None,
    waypoints: Optional[List[str]] = None,
    avoid: Optional[List[str]] = None,
    origin_location_bias: Optional[Union[str, Dict[str, Any]]] = None,
    destination_location_bias: Optional[Union[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Navigate from current location to a destination.
    
    This function is similar to find_directions but specifically designed for navigation
    from the user's current location. It generates intelligent route analysis
    and returns structured direction data. All inputs are validated using Pydantic models.
    
    Note: This function assumes "current location" as the starting point.
    For real-world applications, you would need to provide actual GPS coordinates.
    
    Args:
        destination (str): The destination place (required).
        travel_mode (Optional[str]): The travel mode to use. Supported values: driving, walking, 
                                   bicycling, transit, bus, rail, subway, train, tram. 
                                   Defaults to "driving" if not specified.
        waypoints (Optional[List[str]]): A list of locations to pass through or stop over at, 
                                       e.g. ["Googleplex, Mountain View, CA", "Computer History Museum, Mountain View, CA"]
        avoid (Optional[List[str]]): A list of features to avoid for the routes. Supports: tolls, 
                                   highways, ferries, indoor. e.g. ["tolls", "highways", "ferries"]
        origin_location_bias (Optional[Union[str, Dict[str, Any]]]): Location bias for origin. 
                                                                     Can be a place name string, coordinate dict 
                                                                     {"latitude": float, "longitude": float}, or string names of environment variables:
                                                                     - "MY_HOME": User's home location from environment
                                                                     - "MY_LOCATION": User's current location from environment  
                                                                     - "MY_WORK": User's work location from environment
        destination_location_bias (Optional[Union[str, Dict[str, Any]]]): Location bias for destination. 
                                                                         Can be a place name string, coordinate dict 
                                                                         {"latitude": float, "longitude": float}, or string names of environment variables:
                                                                         - "MY_HOME": User's home location from environment
                                                                         - "MY_LOCATION": User's current location from environment
                                                                         - "MY_WORK": User's work location from environment
    
    Returns:
        Dict[str, Any]: Direction summary containing:
            - map_url (str): URL to view the route on Google Maps
            - travel_mode (str): The travel mode used for the route
            - routes (List[Dict]): List of route options with details including:
                - distance (str): Route distance (e.g., "37.8 miles")
                - duration (str): Estimated travel time (e.g., "45m")
                - start_address (str): Starting address (current location)
                - end_address (str): Destination address
                - mode (str): Travel mode for this route
                - route_id (str): Unique route identifier
                - steps (List[str]): Turn-by-turn directions
                - summary (str): Route summary
                - url (str): Direct link to this route
    
    Raises:
        ValueError: If invalid travel_mode is provided
        ValueError: If invalid avoid features are provided
        ValueError: If input validation fails (empty waypoints, etc.)
        ParseError: If JSON parsing from API response fails
        NotImplementedError: If API response cannot be parsed as valid JSON
        ValidationError: If response data doesn't match expected schema
        UndefinedLocationError: If UserLocation environment variable is not set
    """
    
    # Use Pydantic model for input validation
    try:
        input_data = NavigateInput(
            destination=destination,
            travel_mode=travel_mode,
            waypoints=waypoints,
            avoid=avoid,
            origin_location_bias=origin_location_bias,
            destination_location_bias=destination_location_bias
        )
    except ValidationError as e:
        # Convert Pydantic validation errors to user-friendly messages
        errors = e.errors()
        if errors:
            first_error = errors[0]
            field_name = str(first_error['loc'][0])
            error_type = first_error['type']
            
            if field_name == 'travel_mode':
                raise ValueError("Invalid travel_mode")
            elif field_name == 'avoid':
                raise ValueError("Invalid avoid feature")
            else:
                raise ValueError(str(e))
        else:
            raise ValueError(str(e))
    
    # Default travel mode if not specified
    if not input_data.travel_mode:
        travel_mode = TravelMode.DRIVING.value
    else:
        travel_mode = input_data.travel_mode
    
    # Use Gemini to get intelligent navigation analysis
    nav_query = f"Navigate from {input_data.origin_location_bias or 'current location'} to {input_data.destination}"
    if travel_mode and travel_mode != TravelMode.DRIVING.value:
        nav_query += f" using {travel_mode}"
    if input_data.waypoints:
        nav_query += f" via {', '.join(input_data.waypoints)}"
    if input_data.avoid:
        nav_query += f" avoiding {', '.join(input_data.avoid)}"
    
    nav_query += f"""
    Return the response following this JSON schema:
    ```json
    {json.dumps(DirectionsSummary.model_json_schema(), indent=2)}
    ```
    Make sure to include the `map_url`, `travel_mode`, and `routes` fields in the `DirectionsSummary` model. 
    Use empty strings for any fields that are not available or null.
    For each `Route` in the `routes` list, include `route_id`, `start_address`, `end_address`, `distance`, `duration`, `summary`, `url`, and `mode`. 
    Use empty strings for any fields that are not available or null.
    """
    
    print_log(f"Querying Gemini for navigation")
    directions_summary = get_model_from_gemini_response(nav_query, DirectionsSummary)
    
    add_recent_search(
        endpoint="navigate",
        parameters=input_data.get_non_empty_fields(),
        result=directions_summary.model_dump())
    
    return directions_summary.model_dump() 