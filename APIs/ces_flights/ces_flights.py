# pylint: skip-file

import uuid
import secrets
from typing import Any, Dict, List, Optional, Union
from datetime import date, datetime
from math import ceil

from pydantic import ValidationError as PydanticValidationError
from common_utils.tool_spec_decorator import tool_spec, ErrorObject
from common_utils.datetime_utils import validate_airline_date, InvalidDateTimeFormatError
from .SimulationEngine.utils import (
    _get_current_date, 
    convert_city_format, 
    process_date_without_year,
    _simplify_airline_name,
    _format_time,
    _validate_basic_inputs,
    convert_price,
    is_valid_currency,
    get_supported_currencies,
    SUPPORTED_CURRENCIES
)
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import (
    ValidationError,
    BookingError,
    EscalationError,
    ConversationCompletionError,
    ConversationFailureError,
    ConversationCancellationError,
    InvalidDateRangeError
)
from .SimulationEngine.models import (
    BookFlightTravelers,
    BookFlightTravelersInput,
    SeatingClass, 
    BookFlightResponse,
    SearchFlightsResponse,
    SearchFlightsParams,
    PaginationMetadata,
    # New Pydantic models for tool_spec
    BookFlightInput,
    DoneInput,
    DoneOutput,
    EscalateInput,
    EscalateOutput,
    FailInput,
    FailOutput,
    CancelInput,
    CancelOutput,
    FlightSearchResult
)


@tool_spec(
    spec={
        "name": "search_flights",
        "description": "Search for flights based on travel criteria. Returns a list of available flights matching the specified parameters.",
        "parameters": {
            "type": "object",
            "properties": {
                "destination": {
                    "type": "string",
                    "description": "The final destination of the trip in the format of 'City Name, State Code' (e.g., San Francisco, CA). If the city is not in the US, append the country name (e.g., Sydney, Australia). Must be a non-empty string."
                },
                "earliest_departure_date": {
                    "type": "string",
                    "description": "Filter for the earliest departure date in MM-DD or YYYY-MM-DD format. Must be a valid date string."
                },
                "num_adult_passengers": {
                    "type": "number",
                    "description": "The number of adult passengers. Must be at least 1."
                },
                "num_child_passengers": {
                    "type": "number",
                    "description": "The number of child passengers. Must be non-negative."
                },
                "origin": {
                    "type": "string",
                    "description": "The location where the trip starts in the format of 'City Name, State Code' (e.g., San Francisco, CA). If the city is not in the US, append the country name (e.g., Sydney, Australia). Must be a non-empty string."
                },
                "latest_departure_date": {
                    "type": "string",
                    "nullable": True,
                    "description": "Filter for the latest departure date in MM-DD or YYYY-MM-DD format. If not provided, defaults to earliest_departure_date for an exact date match. Provide a different date to search a date range. Must be a valid date string if provided. Must be on or after earliest_departure_date."
                },
                "earliest_return_date": {
                    "type": "string",
                    "nullable": True,
                    "description": "Filter for the earliest return date in MM-DD or YYYY-MM-DD format. If provided, return flights will be included in search results. Must be a valid date string if provided. Must be on or after latest_departure_date."
                },
                "latest_return_date": {
                    "type": "string",
                    "nullable": True,
                    "description": "Filter for the latest return date in MM-DD or YYYY-MM-DD format. If not provided, defaults to earliest_return_date for an exact date match. Provide a different date to search a date range. Must be a valid date string if provided. Must be on or after earliest_return_date."
                },
                "carry_on_bag_count": {
                    "type": "integer",
                    "nullable": True,
                    "description": "Filter for flights that allow at least this many carry-on bags per person. Must be non-negative if provided."
                },
                "cheapest": {
                    "type": "boolean",
                    "nullable": True,
                    "description": "If TRUE, the results will be sorted by price (in ascending order)."
                },
                "checked_bag_count": {
                    "type": "integer",
                    "nullable": True,
                    "description": "Filter for flights that allow at least this many checked bags per person. Must be non-negative if provided."
                },
                "currency": {
                    "type": "string",
                    "nullable": True,
                    "description": "Price currency code for displaying flight prices. Supported currencies: USD, EUR, JPY, GBP, CNY, AUD, CAD, CHF, HKD, SGD, SEK, KRW, NOK, NZD, INR, MXN, TWD, ZAR, BRL, DKK. Defaults to USD if not provided."
                },
                "depart_after_hour": {
                    "type": "integer",
                    "nullable": True,
                    "description": "Filter for flights that depart after this hour. Must be between 0 and 23 if provided."
                },
                "depart_before_hour": {
                    "type": "integer",
                    "nullable": True,
                    "description": "Filter for flights that depart before this hour. Must be between 0 and 23 if provided."
                },
                "include_airlines": {
                    "type": "array",
                    "nullable": True,
                    "items": {"type": "string"},
                    "description": "Filter by flights on these airlines only. Each airline must be a string if provided."
                },
                "max_stops": {
                    "type": "integer",
                    "nullable": True,
                    "description": "Filter for maximum number of stops/layovers. Must be non-negative if provided."
                },
                "num_infant_in_lap_passengers": {
                    "type": "integer",
                    "nullable": True,
                    "description": "The number of infant passengers (in lap). Must be non-negative if provided."
                },
                "num_infant_in_seat_passengers": {
                    "type": "integer",
                    "nullable": True,
                    "description": "The number of infant passengers (in seat). Must be non-negative if provided."
                },
                "seating_classes": {
                    "type": "array",
                    "nullable": True,
                    "items": {
                        "type": "string",
                        "enum": ["ECONOMY_CLASS", "ECONOMY_PLUS_CLASS", "BUSINESS_CLASS", "FIRST_CLASS", "SUITES_CLASS"]
                    },
                    "description": "Filter for seating classes of the flight. Each class must be one of: ECONOMY_CLASS, ECONOMY_PLUS_CLASS, BUSINESS_CLASS, FIRST_CLASS, SUITES_CLASS."
                },
                "page": {
                    "type": "integer",
                    "nullable": True,
                    "description": "Page number for pagination (1-indexed). Defaults to 1. Must be at least 1."
                },
                "page_size": {
                    "type": "integer",
                    "nullable": True,
                    "description": "Number of results per page. Defaults to 10. Must be between 1 and 100."
                }
            },
            "required": ["destination", "earliest_departure_date", "num_adult_passengers", "num_child_passengers", "origin"]
        },
        "response": {
            "type": "object",
            "description": "A paginated list of flight search results matching the criteria with pagination metadata",
            "properties": {
                "response": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "flight_id": {"type": "string", "description": "Unique identifier for the flight"},
                            "airline": {"type": "string", "description": "Name of the airline"},
                            "origin": {"type": "string", "description": "Departure city and state"},
                            "destination": {"type": "string", "description": "Arrival city and state"},
                            "depart_date": {"type": "string", "description": "Departure date in YYYY-MM-DD format"},
                            "depart_time": {"type": "string", "description": "Departure time in HH:MM:SS format"},
                            "arrival_date": {"type": "string", "description": "Arrival date in YYYY-MM-DD format"},
                            "arrival_time": {"type": "string", "description": "Arrival time in HH:MM:SS format"},
                            "price": {"type": "number", "description": "Flight price"},
                            "currency": {"type": "string", "description": "Currency code"},
                            "stops": {"type": "integer", "description": "Number of stops/layovers"},
                            "seating_class": {"type": "string", "nullable": True, "description": "Seating class"},
                            "checked_bags": {"type": "integer", "nullable": True, "description": "Number of checked bags included"},
                            "carry_on_bags": {"type": "integer", "nullable": True, "description": "Number of carry-on bags included"}
                        },
                        "required": ["flight_id", "airline", "origin", "destination", "depart_date", "depart_time", "arrival_date", "arrival_time", "price", "currency", "stops"]
                    }
                },
                "pagination": {
                    "type": "object",
                    "description": "Pagination metadata for the search results",
                    "properties": {
                        "total_results": {"type": "integer", "description": "Total number of results matching the criteria"},
                        "total_pages": {"type": "integer", "description": "Total number of pages available"},
                        "current_page": {"type": "integer", "description": "Current page number (1-indexed). If the requested page exceeds total_pages, this reflects the auto-adjusted page (last valid page), not the originally requested page."},
                        "page_size": {"type": "integer", "description": "Number of results per page"},
                        "has_next": {"type": "boolean", "description": "Whether there is a next page available"},
                        "has_previous": {"type": "boolean", "description": "Whether there is a previous page available"}
                    },
                    "required": ["total_results", "total_pages", "current_page", "page_size", "has_next", "has_previous"]
                }
            },
            "required": ["response", "pagination"]
        }
    },
    input_model=SearchFlightsParams,
    output_model=SearchFlightsResponse,
    error_model=[
        ErrorObject(TypeError, ["If any parameter is not of the expected type (e.g., destination not a string, num_adult_passengers not an integer or float, optional parameters not matching their expected types)."]),
        ErrorObject(ValueError, ["If any parameter has an invalid value, including empty or whitespace-only strings for destination, origin, currency, or airline names in include_airlines, num_adult_passengers < 1, num_child_passengers < 0, negative values for bag counts or infant passenger counts, depart_after_hour or depart_before_hour not between 0 and 23, invalid seating class (not one of the valid enum values), max_stops < 0, page < 1, page_size < 1 or page_size > 100."]),
        ErrorObject(InvalidDateTimeFormatError, ["If any date parameter has an invalid format. Dates must be parseable to YYYY-MM-DD format."]),
        ErrorObject(InvalidDateRangeError, ["If date range relationships are invalid, including earliest_departure_date is after latest_departure_date, earliest_return_date is after latest_return_date, earliest_return_date is before earliest_departure_date, earliest_return_date is before latest_departure_date."])
    ]
)
def search_flights(
    destination: str,
    earliest_departure_date: str,
    num_adult_passengers: Union[int, float],
    num_child_passengers: Union[int, float],
    origin: str,
    latest_departure_date: Optional[str] = None,
    earliest_return_date: Optional[str] = None,
    latest_return_date: Optional[str] = None,
    carry_on_bag_count: Optional[int] = None,
    cheapest: Optional[bool] = None,
    checked_bag_count: Optional[int] = None,
    currency: Optional[str] = None,
    depart_after_hour: Optional[int] = None,
    depart_before_hour: Optional[int] = None,
    include_airlines: Optional[list] = None,
    max_stops: Optional[int] = None,
    num_infant_in_lap_passengers: Optional[int] = None,
    num_infant_in_seat_passengers: Optional[int] = None,
    seating_classes: Optional[list] = None,
    page: Optional[int] = 1,
    page_size: Optional[int] = 10,
) -> Dict[str, Any]:
    """
    Search for available flights based on travel criteria.

    Args:
        destination (str): The final destination of the trip in the format of "City Name, State Code" (e.g., San Francisco, CA). If the city is not in the US, append the country name (e.g., Sydney, Australia). Must be a non-empty string.
        earliest_departure_date (str): Filter for the earliest departure date in MM-DD or YYYY-MM-DD format. Must be a valid date string.
        num_adult_passengers (Union[int, float]): The number of adult passengers. Must be at least 1.
        num_child_passengers (Union[int, float]): The number of child passengers. Must be non-negative.
        origin (str): The location where the trip starts in the format of "City Name, State Code" (e.g., San Francisco, CA). If the city is not in the US, append the country name (e.g., Sydney, Australia). Must be a non-empty string.
        latest_departure_date (Optional[str]): Filter for the latest departure date in MM-DD or YYYY-MM-DD format. If not provided, defaults to earliest_departure_date for an exact date match. Provide a different date to search a date range. Must be a valid date string if provided. Must be on or after earliest_departure_date. Defaults to None.
        earliest_return_date (Optional[str]): Filter for the earliest return date in MM-DD or YYYY-MM-DD format. If provided, return flights will be included in search results. Must be a valid date string if provided. Must be on or after latest_departure_date. Defaults to None.
        latest_return_date (Optional[str]): Filter for the latest return date in MM-DD or YYYY-MM-DD format. If not provided but earliest_return_date is provided, defaults to earliest_return_date for an exact date match. Provide a different date to search a date range. Must be a valid date string if provided. Must be on or after earliest_return_date. Defaults to None.
        carry_on_bag_count (Optional[int]): Filter for flights that allow at least this many carry-on bags per person. Must be non-negative if provided. Defaults to None.
        cheapest (Optional[bool]): If TRUE, the results will be sorted by price (in ascending order). Defaults to None.
        checked_bag_count (Optional[int]): Filter for flights that allow at least this many checked bags per person. Must be non-negative if provided. Defaults to None.
        currency (Optional[str]): Price currency code for displaying flight prices. Supported currencies: USD, EUR, JPY, GBP, CNY, AUD, CAD, CHF, HKD, SGD, SEK, KRW, NOK, NZD, INR, MXN, TWD, ZAR, BRL, DKK. Defaults to USD if not provided.
        depart_after_hour (Optional[int]): Filter for flights that depart after this hour. Must be between 0 and 23 if provided. Defaults to None.
        depart_before_hour (Optional[int]): Filter for flights that depart before this hour. Must be between 0 and 23 if provided. Defaults to None.
        include_airlines (Optional[List[str]]): Filter by flights on these airlines only. Each airline must be a string if provided. Defaults to None.
        max_stops (Optional[int]): Filter for maximum number of stops/layovers. Must be non-negative if provided. Defaults to None.
        num_infant_in_lap_passengers (Optional[int]): The number of infant passengers (in lap). Must be non-negative if provided. Defaults to None.
        num_infant_in_seat_passengers (Optional[int]): The number of infant passengers (in seat). Must be non-negative if provided. Defaults to None.
        seating_classes (Optional[list]): Filter for seating classes of the flight. Must be a list of strings. Each class must be one of: ECONOMY_CLASS, ECONOMY_PLUS_CLASS, BUSINESS_CLASS, FIRST_CLASS, SUITES_CLASS. Defaults to None.
        page (Optional[int]): Page number for pagination (1-indexed). Must be at least 1. Defaults to 1.
        page_size (Optional[int]): Number of results per page. Must be between 1 and 100. Defaults to 10.

    Returns:
        Dict[str, Any]: A dictionary containing:
            - "response" (List[FlightSearchResult]): A paginated list of flight search results.
            Results include outbound flights (origin to destination) and optionally return flights (destination to origin) if return dates are provided.
            Each FlightSearchResult contains the following keys:
            flight_id (str): The unique identifier of the flight (e.g., "AA101", "DL202").
            airline (str): The name of the airline operating the flight.
            origin (str): The departure location in the format of {city name, state code}.
            destination (str): The arrival location in the format of {city name, state code}.
            depart_date (str): The departure date in YYYY-MM-DD format.
            depart_time (str): The departure time in HH:MM:SS format.
            arrival_date (str): The arrival date in YYYY-MM-DD format.
            arrival_time (str): The arrival time in HH:MM:SS format.
            price (float): The price of the flight.
            currency (str): The currency of the price (e.g., "USD").
            stops (int): The number of stops/layovers for the flight.
            seating_class (Optional[str]): The seating class of the flight (e.g., "ECONOMY_CLASS", "BUSINESS_CLASS").
            checked_bags (Optional[int]): The max number of checked bags allowed per person.
            carry_on_bags (Optional[int]): The max number of carry-on bags allowed per person.
            - "pagination" (Dict[str, Any]): Pagination metadata containing:
                total_results (int): Total number of results matching the criteria.
                total_pages (int): Total number of pages available.
                current_page (int): Current page number (1-indexed). If the requested page exceeds total_pages, this will reflect the auto-adjusted page (typically the last valid page), not the originally requested page number.
                page_size (int): Number of results per page.
                has_next (bool): Whether there is a next page available.
                has_previous (bool): Whether there is a previous page available.

    Raises:
        TypeError: If any parameter is not of the expected type (e.g., destination not a string, num_adult_passengers not an integer or float, optional parameters not matching their expected types).
        ValueError: If any parameter has an invalid value, including:
            - Empty or whitespace-only strings for destination, origin, or airline names in include_airlines
            - Unsupported currency code (not one of the 20 supported currencies)
            - num_adult_passengers < 1
            - num_child_passengers < 0
            - Negative values for bag counts or infant passenger counts
            - depart_after_hour or depart_before_hour not between 0 and 23
            - Invalid seating class (not one of the valid enum values)
            - max_stops < 0
            - page < 1
            - page_size < 1 or page_size > 100
        InvalidDateTimeFormatError: If any date parameter has an invalid format. Dates must be parseable to YYYY-MM-DD format.
        InvalidDateRangeError: If date range relationships are invalid, including:
            - earliest_departure_date is after latest_departure_date
            - earliest_return_date is after latest_return_date
            - earliest_return_date is before earliest_departure_date
            - earliest_return_date is before latest_departure_date
    """
    # --- Input Validation ---

    # Validate required string parameters
    if not isinstance(destination, str):
        raise TypeError(f"argument 'destination' must be a string, got {type(destination).__name__}")
    if not destination or not destination.strip():
        raise ValueError("argument 'destination' cannot be empty or whitespace")

    if not isinstance(origin, str):
        raise TypeError(f"argument 'origin' must be a string, got {type(origin).__name__}")
    if not origin or not origin.strip():
        raise ValueError("argument 'origin' cannot be empty or whitespace")

    if not isinstance(earliest_departure_date, str):
        raise TypeError(f"argument 'earliest_departure_date' must be a string, got {type(earliest_departure_date).__name__}")

    # Default latest_departure_date to earliest_departure_date if not provided
    if latest_departure_date is None:
        latest_departure_date = earliest_departure_date
    elif not isinstance(latest_departure_date, str):
        raise TypeError(f"argument 'latest_departure_date' must be a string or None, got {type(latest_departure_date).__name__}")

    # Validate optional return date parameters
    if earliest_return_date is not None and not isinstance(earliest_return_date, str):
        raise TypeError(f"argument 'earliest_return_date' must be a string or None, got {type(earliest_return_date).__name__}")

    if latest_return_date is not None and not isinstance(latest_return_date, str):
        raise TypeError(f"argument 'latest_return_date' must be a string or None, got {type(latest_return_date).__name__}")

    # Default latest_return_date to earliest_return_date if earliest_return_date is provided but latest_return_date is not
    if earliest_return_date is not None and latest_return_date is None:
        latest_return_date = earliest_return_date

    # Validate and normalize date formats using common_utils
    # Empty strings and invalid formats will raise InvalidDateTimeFormatError
    validated_earliest_departure = validate_airline_date(earliest_departure_date)
    validated_latest_departure = validate_airline_date(latest_departure_date)
    validated_earliest_return = validate_airline_date(earliest_return_date) if earliest_return_date else None
    validated_latest_return = validate_airline_date(latest_return_date) if latest_return_date else None

    # Validate logical date relationships
    if validated_earliest_departure > validated_latest_departure:
        raise InvalidDateRangeError("argument 'earliest_departure_date' cannot be after 'latest_departure_date'")

    if validated_earliest_return and validated_latest_return:
        if validated_earliest_return > validated_latest_return:
            raise InvalidDateRangeError("argument 'earliest_return_date' cannot be after 'latest_return_date'")

        # Validate that return dates are not before departure dates
        if validated_earliest_return < validated_earliest_departure:
            raise InvalidDateRangeError("argument 'earliest_return_date' cannot be before 'earliest_departure_date'")

        # Validate that earliest return is not before latest departure
        # (if you could depart as late as latest_departure_date, you can't return before that)
        if validated_earliest_return < validated_latest_departure:
            raise InvalidDateRangeError("argument 'earliest_return_date' cannot be before 'latest_departure_date'")

    # Validate required numeric parameters
    if not isinstance(num_adult_passengers, (int, float)):
        raise TypeError(f"argument 'num_adult_passengers' must be an integer or float, got {type(num_adult_passengers).__name__}")
    if num_adult_passengers < 1:
        raise ValueError("argument 'num_adult_passengers' must be at least 1")

    if not isinstance(num_child_passengers, (int, float)):
        raise TypeError(f"argument 'num_child_passengers' must be an integer or float, got {type(num_child_passengers).__name__}")
    if num_child_passengers < 0:
        raise ValueError("argument 'num_child_passengers' must be non-negative")

    # Validate optional parameters
    if currency is not None:
        if not isinstance(currency, str):
            raise TypeError(f"argument 'currency' must be a string or None, got {type(currency).__name__}")
        if not currency.strip():
            raise ValueError("argument 'currency' cannot be empty or whitespace")
        # Validate currency code is supported
        if not is_valid_currency(currency):
            supported = ', '.join(sorted(SUPPORTED_CURRENCIES))
            raise ValueError(
                f"argument 'currency' must be one of the supported currencies: {supported}. "
                f"Got: '{currency}'"
            )
        # Normalize to uppercase for consistency
        currency = currency.upper()
    else:
        # Default to USD if no currency specified
        currency = "USD"

    if cheapest is not None and not isinstance(cheapest, bool):
        raise TypeError(f"argument 'cheapest' must be a boolean or None, got {type(cheapest).__name__}")

    if carry_on_bag_count is not None:
        if not isinstance(carry_on_bag_count, int):
            raise TypeError(f"argument 'carry_on_bag_count' must be an integer or None, got {type(carry_on_bag_count).__name__}")
        if carry_on_bag_count < 0:
            raise ValueError("argument 'carry_on_bag_count' must be non-negative")

    if checked_bag_count is not None:
        if not isinstance(checked_bag_count, int):
            raise TypeError(f"argument 'checked_bag_count' must be an integer or None, got {type(checked_bag_count).__name__}")
        if checked_bag_count < 0:
            raise ValueError("argument 'checked_bag_count' must be non-negative")

    if depart_after_hour is not None:
        if not isinstance(depart_after_hour, int):
            raise TypeError(f"argument 'depart_after_hour' must be an integer or None, got {type(depart_after_hour).__name__}")
        if not 0 <= depart_after_hour <= 23:
            raise ValueError("argument 'depart_after_hour' must be between 0 and 23")

    if depart_before_hour is not None:
        if not isinstance(depart_before_hour, int):
            raise TypeError(f"argument 'depart_before_hour' must be an integer or None, got {type(depart_before_hour).__name__}")
        if not 0 <= depart_before_hour <= 23:
            raise ValueError("argument 'depart_before_hour' must be between 0 and 23")

    if max_stops is not None:
        if not isinstance(max_stops, int):
            raise TypeError(f"argument 'max_stops' must be an integer or None, got {type(max_stops).__name__}")
        if max_stops < 0:
            raise ValueError("argument 'max_stops' must be non-negative")

    if num_infant_in_lap_passengers is not None:
        if not isinstance(num_infant_in_lap_passengers, int):
            raise TypeError(f"argument 'num_infant_in_lap_passengers' must be an integer or None, got {type(num_infant_in_lap_passengers).__name__}")
        if num_infant_in_lap_passengers < 0:
            raise ValueError("argument 'num_infant_in_lap_passengers' must be non-negative")

    if num_infant_in_seat_passengers is not None:
        if not isinstance(num_infant_in_seat_passengers, int):
            raise TypeError(f"argument 'num_infant_in_seat_passengers' must be an integer or None, got {type(num_infant_in_seat_passengers).__name__}")
        if num_infant_in_seat_passengers < 0:
            raise ValueError("argument 'num_infant_in_seat_passengers' must be non-negative")

    if include_airlines is not None:
        if not isinstance(include_airlines, list):
            raise TypeError(f"argument 'include_airlines' must be a list or None, got {type(include_airlines).__name__}")
        for i, airline in enumerate(include_airlines):
            if not isinstance(airline, str):
                raise TypeError(f"include_airlines[{i}] must be a string, got {type(airline).__name__}")
            if not airline.strip():
                raise ValueError(f"include_airlines[{i}] cannot be empty or whitespace")

    if seating_classes is not None:
        if not isinstance(seating_classes, list):
            raise TypeError(f"argument 'seating_classes' must be a list or None, got {type(seating_classes).__name__}")
        valid_classes = [sc.value for sc in SeatingClass]
        for i, seat_class in enumerate(seating_classes):
            # Only accept string primitives, reject complex types including enums
            if not isinstance(seat_class, str):
                raise TypeError(f"seating_classes[{i}] must be a string, got {type(seat_class).__name__}.")
            
            if seat_class not in valid_classes:
                raise ValueError(f"seating_classes[{i}] must be one of {valid_classes}, got '{seat_class}'")

    # Validate pagination parameters
    if page is not None:
        if not isinstance(page, int):
            raise TypeError(f"argument 'page' must be an integer or None, got {type(page).__name__}")
        if page < 1:
            raise ValueError("argument 'page' must be at least 1")
    else:
        page = 1

    if page_size is not None:
        if not isinstance(page_size, int):
            raise TypeError(f"argument 'page_size' must be an integer or None, got {type(page_size).__name__}")
        if page_size < 1:
            raise ValueError("argument 'page_size' must be at least 1")
        if page_size > 100:
            raise ValueError("argument 'page_size' must not exceed 100")
    else:
        page_size = 10

    # --- End of Input Validation ---

    # Get all flights from database
    sample_flights = DB.get("sample_flights", {})

    # Convert city formats for comparison
    converted_origin = convert_city_format(origin)
    converted_destination = convert_city_format(destination)

    # Helper function to check city match
    def city_matches(flight_city: str, search_city: str, converted_search_city: str) -> bool:
        return (
            flight_city.upper() == search_city.upper() or
            search_city.upper() in flight_city.upper() or
            flight_city.upper() in search_city.upper() or
            converted_search_city.upper() == flight_city.upper() or
            convert_city_format(flight_city).upper() == converted_search_city.upper()
        )

    # Helper function to apply common filters
    def passes_filters(flight: Dict[str, Any]) -> bool:
        if max_stops is not None and flight.get("stops", 0) > max_stops:
            return False
        if include_airlines and flight.get("airline", "") not in include_airlines:
            return False
        if seating_classes and flight.get('seating_class') not in seating_classes:
            return False
        depart_hour = int(flight.get('depart_time', '00:00:00').split(':')[0])
        if depart_after_hour is not None and depart_hour < depart_after_hour:
            return False
        if depart_before_hour is not None and depart_hour >= depart_before_hour:
            return False
        # Filter for flights with at least the requested bag count (minimum match, not exact match)
        if checked_bag_count is not None and flight.get("checked_bags", 0) < checked_bag_count:
            return False
        if carry_on_bag_count is not None and flight.get("carry_on_bags", 0) < carry_on_bag_count:
            return False
        # Note: currency is not used as a filter anymore - all prices are converted on display
        return True

    # Search for OUTBOUND flights (origin -> destination)
    outbound_flights = []
    for flight_id, flight in sample_flights.items():
        # Check if this is an outbound flight (origin -> destination)
        if not city_matches(flight.get("origin", ""), origin, converted_origin):
            continue
        if not city_matches(flight.get("destination", ""), destination, converted_destination):
            continue

        # Check if depart_date is within the requested range
        flight_depart_date = flight.get("depart_date", "")
        if not (validated_earliest_departure <= flight_depart_date <= validated_latest_departure):
            continue

        # Apply optional filters
        if not passes_filters(flight):
            continue

        # Add flight with its ID
        flight_copy = dict(flight)
        flight_copy["id"] = flight_id
        outbound_flights.append(flight_copy)

    # Search for RETURN flights (destination -> origin) if return dates are provided
    return_flights = []
    if validated_earliest_return and validated_latest_return:
        for flight_id, flight in sample_flights.items():
            # Check if this is a return flight (destination -> origin)
            if not city_matches(flight.get("origin", ""), destination, converted_destination):
                continue
            if not city_matches(flight.get("destination", ""), origin, converted_origin):
                continue

            # Check if depart_date is within the return date range
            flight_depart_date = flight.get("depart_date", "")
            if not (validated_earliest_return <= flight_depart_date <= validated_latest_return):
                continue

            # Apply optional filters
            if not passes_filters(flight):
                continue

            # Add flight with its ID
            flight_copy = dict(flight)
            flight_copy["id"] = flight_id
            return_flights.append(flight_copy)

    # Combine both lists
    all_matching_flights = outbound_flights + return_flights

    # Sort by price if requested
    if cheapest:
        all_matching_flights.sort(key=lambda x: x["price"])

    # Calculate pagination metadata
    total_results = len(all_matching_flights)
    total_pages = ceil(total_results / page_size) if total_results > 0 else 1
    
    # Validate page number against total pages
    # Note: When requested page exceeds total_pages, auto-adjust to last valid page
    if page > total_pages:
        page = total_pages  # Adjust to last page if requested page exceeds total
    
    # Calculate pagination slice indices
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    # Paginate the results
    paginated_flights = all_matching_flights[start_idx:end_idx]
    
    # Format results with currency conversion
    results = []
    for flight in paginated_flights:
        # All prices in DB are in USD, convert to requested currency
        price_usd = flight.get("price", 0.0)
        converted_price = convert_price(price_usd, currency)
        
        flight_result = FlightSearchResult(
            flight_id=flight.get("id", "Unknown"),
            airline=flight.get("airline", "Unknown"),
            origin=flight.get("origin", ""),
            destination=flight.get("destination", ""),
            depart_date=flight.get("depart_date", ""),
            depart_time=flight.get("depart_time", ""),
            arrival_date=flight.get("arrival_date", ""),
            arrival_time=flight.get("arrival_time", ""),
            price=converted_price,
            currency=currency,  # Use the requested currency
            stops=flight.get("stops", 0),
            seating_class=flight.get("seating_class"),
            checked_bags=flight.get("checked_bags"),
            carry_on_bags=flight.get("carry_on_bags")
        )
        results.append(flight_result)

    # Create pagination metadata
    pagination_metadata = {
        "total_results": total_results,
        "total_pages": total_pages,
        "current_page": page,
        "page_size": page_size,
        "has_next": page < total_pages,
        "has_previous": page > 1
    }

    return {
        "response": results,
        "pagination": pagination_metadata
    }


@tool_spec(
    spec={
        "name": "book_flight",
        "description": "Book a flight for one or more travelers. Creates a booking with confirmation details.",
        "parameters": {
            "type": "object",
            "properties": {
                "flight_id": {
                    "type": "string",
                    "description": "The unique identifier of the departure flight to book (e.g., 'AA101', 'DL201'). Must be a valid flight_id."
                },
                "travelers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "first_name": {
                                "type": "string",
                                "description": "Traveler's first name. Must be a non-empty string."
                            },
                            "last_name": {
                                "type": "string",
                                "description": "Traveler's last name. Must be a non-empty string."
                            },
                            "date_of_birth": {
                                "type": "string",
                                "description": "Traveler's date of birth in YYYY-MM-DD format. Must be a valid date and cannot be in the future."
                            }
                        },
                        "required": ["first_name", "last_name", "date_of_birth"]
                    },
                    "description": "List of traveler details with: first_name, last_name, and date_of_birth."
                },
                "return_flight_id": {
                    "type": "string",
                    "nullable": True,
                    "description": "The return flight identifier if this is a round trip. Must be a valid flight_id if provided."
                },
                "known_traveler_number": {
                    "type": "string",
                    "nullable": True,
                    "description": "The known traveler number (e.g., TSA PreCheck, Global Entry) for the booking. Must be a non-empty string if provided."
                }
            },
            "required": ["flight_id", "travelers"]
        },
        "response": {
            "type": "object",
            "description": "A dictionary containing the booking confirmation details with the following keys:",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "The unique identifier for the booking (UUID format)."
                },
                "flight_id": {
                    "type": "string",
                    "description": "The unique identifier of the departure flight."
                },
                "confirmation_number": {
                    "type": "string",
                    "description": "The booking confirmation number (6-character hexadecimal string like a PNR, e.g., 'A3F7B2')."
                },
                "status": {
                    "type": "string",
                    "description": "The booking status."
                },
                "failed": {
                    "type": "boolean",
                    "description": "Whether the booking failed. True if status is not 'confirmed', False otherwise."
                },
                "return_flight_id": {
                    "type": "string",
                    "nullable": True,
                    "description": "The return flight identifier if this is a round trip."
                },
                "is_round_trip": {
                    "type": "boolean",
                    "description": "Whether this is a round trip."
                }
            },
            "required": ["booking_id", "flight_id", "confirmation_number", "status", "failed", "is_round_trip"]
        }
    },
    input_model=BookFlightInput,
    output_model=BookFlightResponse,
    error_model=[
        ErrorObject(ValidationError, ["If traveler data is invalid, including empty travelers list (at least one traveler must be provided), missing or empty first_name or last_name (whitespace-only strings are invalid), invalid or missing date_of_birth (must be a valid date or parseable date string), future date_of_birth (date of birth cannot be in the future), invalid flight_id type (must be a string), invalid date format (unable to parse date string), any other Pydantic validation errors."]),
        ErrorObject(BookingError, ["If booking operations fail, including flight not found or not available for booking."])
    ]
)
def book_flight(flight_id: str, travelers: list, return_flight_id: Optional[str] = None, known_traveler_number: Optional[str] = None) -> Dict[str, Any]:
    """
    Book a flight with the flight ID and traveler details.

    Args:
        flight_id (str): The unique identifier of the departure flight to book (e.g., "AA101", "DL201"). Must be a valid flight_id.
        travelers (list): List of traveler dictionaries. Each dict must contain only primitive types with keys:
            - first_name (str): The traveler's first name. Must be a non-empty string.
            - last_name (str): The traveler's last name. Must be a non-empty string.
            - date_of_birth (str): The traveler's date of birth in YYYY-MM-DD format. Must be a string. Future dates are not allowed.
        return_flight_id (Optional[str]): The return flight identifier if this is a round trip.
        known_traveler_number (Optional[str]): The known traveler number (e.g., TSA PreCheck, Global Entry) for the booking. Must be a non-empty string if provided.

    Returns:
        Dict[str, Any]: A dictionary containing the booking confirmation details with the following keys:
            booking_id (str): The unique identifier for the booking (UUID format).
            flight_id (str): The unique identifier of the departure flight.
            confirmation_number (str): The booking confirmation number (6-character hexadecimal string like a PNR, e.g., "A3F7B2").
            status (str): The booking status (e.g., "confirmed").
            failed (bool): Whether the booking failed. True if status is not "confirmed", False otherwise.
            return_flight_id (Optional[str]): The return flight identifier if this is a round trip.
            is_round_trip (bool): Whether this is a round trip.

    Raises:
        ValidationError: If traveler data is invalid, including:
            - Empty travelers list (at least one traveler must be provided).
            - Missing or empty first_name or last_name (whitespace-only strings are invalid).
            - Invalid or missing date_of_birth (must be a valid date or parseable date string).
            - Future date_of_birth (date of birth cannot be in the future).
            - Invalid flight_id type (must be a string).
            - Invalid date format (unable to parse date string).
            - Any other Pydantic validation errors.
        BookingError: If booking operations fail, including:
            - Flight not found or not available for booking.
    """
    # Validate flight_id type
    if not isinstance(flight_id, str):
        raise ValidationError(f"flight_id must be a string, got {type(flight_id).__name__}: {flight_id}")
    
    # Validate flight_id is not empty
    if not flight_id or not flight_id.strip():
        raise ValidationError("flight_id cannot be empty or whitespace-only")
    
    # Validate known_traveler_number if provided
    if known_traveler_number is not None:
        if not isinstance(known_traveler_number, str):
            raise ValidationError("known_traveler_number must be a string or None")
        if not known_traveler_number.strip():
            raise ValidationError("known_traveler_number cannot be empty or whitespace-only if provided")
    
    # Validate travelers is a list
    if not isinstance(travelers, list):
        raise ValidationError(f"travelers must be a list, got {type(travelers).__name__}")
    
    if not travelers:
        raise ValidationError("At least one traveler must be provided for booking")

    try:
        # Convert travelers from BookFlightTravelersInput (string dates) to BookFlightTravelers (date objects)
        # The @tool_spec decorator ensures we receive BookFlightTravelersInput instances with primitive types
        validated_travelers = []
        for i, traveler in enumerate(travelers):
            # The decorator should provide BookFlightTravelersInput instances
            # Convert string date to date object for internal BookFlightTravelers model
            if isinstance(traveler, BookFlightTravelersInput):
                # Extract data and convert date string to date object
                traveler_data = traveler.model_dump()
                try:
                    date_str = traveler_data['date_of_birth']
                    # Parse YYYY-MM-DD format
                    if len(date_str) == 10 and date_str.count('-') == 2:
                        traveler_data['date_of_birth'] = datetime.strptime(date_str, '%Y-%m-%d').date()
                    else:
                        raise ValueError(f"Date must be in YYYY-MM-DD format, got: {date_str}")
                except ValueError as e:
                    raise ValidationError(f"Invalid date format for traveler {traveler_data.get('first_name', 'Unknown')}: {e}")
                
                traveler_instance = BookFlightTravelers(**traveler_data)
            elif isinstance(traveler, dict):
                # Handle dict inputs (for backward compatibility with tests that bypass decorator)
                # Validate that date_of_birth is a string primitive, not a date object
                if 'date_of_birth' in traveler:
                    dob = traveler['date_of_birth']
                    if not isinstance(dob, str):
                        raise ValidationError(
                            f"travelers[{i}].date_of_birth must be a string in YYYY-MM-DD format, got {type(dob).__name__}. "
                            "Date objects are not allowed; use string format instead."
                        )
                
                # Convert dict to Pydantic model
                traveler_dict = traveler.copy()
                if isinstance(traveler_dict.get('date_of_birth'), str):
                    try:
                        date_str = traveler_dict['date_of_birth']
                        if len(date_str) == 10 and date_str.count('-') == 2:
                            traveler_dict['date_of_birth'] = datetime.strptime(date_str, '%Y-%m-%d').date()
                        else:
                            raise ValueError(f"Date must be in YYYY-MM-DD format, got: {date_str}")
                    except ValueError as e:
                        raise ValidationError(f"Invalid date format for traveler {traveler_dict.get('first_name', 'Unknown')}: {e}")
                
                traveler_instance = BookFlightTravelers(**traveler_dict)
            else:
                raise ValidationError(
                    f"travelers[{i}] must be a dict with primitive types, got {type(traveler).__name__}. "
                    "Pydantic model objects (other than BookFlightTravelersInput) are not allowed."
                )
            
            # Validate that date_of_birth is not in the future
            if isinstance(traveler_instance.date_of_birth, date):
                today = date.today()
                if traveler_instance.date_of_birth > today:
                    raise ValidationError(f"Date of birth cannot be in the future for traveler {traveler_instance.first_name}: {traveler_instance.date_of_birth}")
            
            validated_travelers.append(traveler_instance)
    except PydanticValidationError as e:
        # Convert Pydantic validation error to custom ValidationError
        error_messages = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error['loc'])
            error_messages.append(f"{field}: {error['msg']}")
        raise ValidationError("; ".join(error_messages))

    # Find the specific flight by flight_id
    sample_flights = DB.get("sample_flights", {})
    if flight_id not in sample_flights:
        raise BookingError(f"Flight {flight_id} not found or not available for booking")

    outbound_flight = sample_flights[flight_id]

    return_flight = None
    if return_flight_id:
        if return_flight_id not in sample_flights:  
            raise BookingError(f"Return flight {return_flight_id} not found or not available for booking")
        return_flight = sample_flights[return_flight_id]

        # Validate that return flight is actually a return flight
        # Return flight should go from destination to origin
        if (return_flight.get("origin", "") != outbound_flight.get("destination", "") or 
            return_flight.get("destination", "") != outbound_flight.get("origin", "")):
            raise BookingError(f"Return flight {return_flight_id} is not a valid return flight for {flight_id}")

        # Validate that return flight date is after outbound flight date
        outbound_date = datetime.strptime(outbound_flight.get("depart_date", "1970-01-01"), "%Y-%m-%d").date()
        return_date = datetime.strptime(return_flight.get("depart_date", "1970-01-01"), "%Y-%m-%d").date()
        if return_date <= outbound_date:
            raise BookingError(f"Return flight date must be after outbound flight date")

    # Create booking
    booking_id = str(uuid.uuid4())
    # Generate 6-character hexadecimal PNR (like real airline confirmation numbers)
    confirmation_number = secrets.token_hex(3).upper()  # 3 bytes = 6 hex characters

    # Convert validated travelers to dicts for storage
    # Use mode='json' to ensure dates are serialized as strings for JSON compatibility
    travelers_dict = [t.model_dump(mode='json') for t in validated_travelers]

    flights_booked = [outbound_flight]

    if return_flight:
        flights_booked.append(return_flight)

    # Store booking
    DB.setdefault("flight_bookings", {})[booking_id] = {
        "booking_id": booking_id,
        "flight_id": flight_id,  # Primary flight ID
        "return_flight_id": return_flight_id,  # Return flight ID if applicable
        "flights": flights_booked,
        "travelers": travelers_dict,
        "status": "confirmed",
        "confirmation_number": confirmation_number,
        "is_round_trip": bool(return_flight),
        "known_traveler_number": known_traveler_number  # Store at booking level
    }

    # Return response matching the Pydantic output model
    booking_status = "confirmed"
    response = {
        "booking_id": booking_id,
        "flight_id": flight_id,  # Primary flight ID for backward compatibility
        "confirmation_number": confirmation_number,
        "status": booking_status,
        "failed": booking_status != "confirmed"  # False for confirmed, True for any other status
    }

    # Add return flight ID if it's a round trip
    if return_flight:
        response["return_flight_id"] = return_flight_id
        response["is_round_trip"] = True
    else:
        response["return_flight_id"] = None
        response["is_round_trip"] = False

    return response


@tool_spec(
    spec={
        "name": "done",
        "description": "Mark the conversation as completed successfully. This indicates that the user's request has been fulfilled.",
        "parameters": {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "nullable": True,
                    "description": "Optional completion message or summary. Must be a non-empty string if provided."
                }
            },
            'required': []
        },
        "response": {
            "type": "object",
            "description": "A dictionary containing the completion status with the following keys:",
            "properties": {
                "ok": {
                    "type": "boolean",
                    "description": "Always true, indicating the conversation is completed."
                }
            },
            "required": ["ok"]
        }
    },
    input_model=DoneInput,
    output_model=DoneOutput,
    error_model=[
        ErrorObject(TypeError, ["If input is not a string or None."]),
        ErrorObject(ValueError, ["If input is an empty string or contains only whitespace."]),
        ErrorObject(ConversationCompletionError, ["If storing the completion status fails or if any other error occurs during the operation."])
    ]
)
def done(input: Optional[str] = None) -> Dict[str, bool]:
    """
    Indicate that the agent's task is complete and terminate the conversation successfully.

    Args:
        input (Optional[str]): Additional information to store about the conversation completion. Must be a non-empty string if provided. Defaults to None.

    Returns:
        Dict[str, bool]: A dictionary containing:
            - ok (bool): Whether the operation was successful (always True).

    Raises:
        TypeError: If input is not a string or None.
        ValueError: If input is an empty string or contains only whitespace.
        ConversationCompletionError: If storing the completion status fails or if any other error occurs during the operation.
    """
    # --- Input Validation ---
    if input is not None:
        if not isinstance(input, str):
            raise TypeError(f"argument 'input' must be a string or None, got {type(input).__name__}")
        if not input.strip():
            raise ValueError("argument 'input' cannot be empty or whitespace")
    # --- End of Input Validation ---
    
    try:
        done_data = {
            "status": "completed",
            "timestamp": _get_current_date(),
            "input": input
        }
        
        DB.setdefault("_end_of_conversation_status", {})["done"] = done_data
        return {"ok": True}
        
    except Exception as e:
        raise ConversationCompletionError(f"Failed to complete conversation: {e}")


@tool_spec(
    spec={
        "name": "escalate",
        "description": "Escalate the conversation to a human agent or external system. Use this when the agent cannot complete the user's request.",
        "parameters": {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "nullable": True,
                    "description": "Optional escalation message or reason. Must be a non-empty string if provided."
                }
            },
            'required': []
        },
        "response": {
            "type": "object",
            "description": "A dictionary containing the escalation status with the following keys:",
            "properties": {
                "ok": {
                    "type": "boolean",
                    "description": "Always true, indicating the conversation has been escalated."
                }
            },
            "required": ["ok"]
        }
    },
    input_model=EscalateInput,
    output_model=EscalateOutput,
    error_model=[
        ErrorObject(TypeError, ["If input is not a string or None."]),
        ErrorObject(ValueError, ["If input is an empty string or contains only whitespace."]),
        ErrorObject(EscalationError, ["If storing the escalation status fails or if any other error occurs during the operation."])
    ]
)
def escalate(input: Optional[str] = None) -> Dict[str, bool]:
    """
    Escalate the conversation to a human agent.

    Args:
        input (Optional[str]): Additional information about the escalation reason or context. Must be a non-empty string if provided. Defaults to None.

    Returns:
        Dict[str, bool]: A dictionary containing:
            - ok (bool): Whether the operation was successful (always True).

    Raises:
        TypeError: If input is not a string or None.
        ValueError: If input is an empty string or contains only whitespace.
        EscalationError: If storing the escalation status fails or if any other error occurs during the operation.
    """
    # --- Input Validation ---
    if input is not None:
        if not isinstance(input, str):
            raise TypeError(f"argument 'input' must be a string or None, got {type(input).__name__}")
        if not input.strip():
            raise ValueError("argument 'input' cannot be empty or whitespace")
    # --- End of Input Validation ---
    
    try:
        escalation_data = {
            "input": input,
            "status": "escalated",
            "escalation_type": "human_agent_transfer",
            "timestamp": _get_current_date()
        }
        
        DB.setdefault("_end_of_conversation_status", {})["escalate"] = escalation_data
        
        return {"ok": True}
        
    except Exception as e:
        raise EscalationError(f"Failed to escalate to human agent: {e}")


@tool_spec(
    spec={
        "name": "fail",
        "description": "Mark the conversation as failed. Use this when the agent encounters an error that prevents completion of the user's request.",
        "parameters": {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "nullable": True,
                    "description": "Optional failure message or error description. Must be a non-empty string if provided."
                }
            },
            'required': []
        },
        "response": {
            "type": "object",
            "description": "A dictionary containing the failure status with the following keys:",
            "properties": {
                "ok": {
                    "type": "boolean",
                    "description": "Always true, indicating the conversation has failed."
                }
            },
            "required": ["ok"]
        }
    },
    input_model=FailInput,
    output_model=FailOutput,
    error_model=[
        ErrorObject(TypeError, ["If input is not a string or None."]),
        ErrorObject(ValueError, ["If input is an empty string or contains only whitespace."]),
        ErrorObject(ConversationFailureError, ["If storing the failure status fails or if any other error occurs during the operation."])
    ]
)
def fail(input: Optional[str] = None) -> Dict[str, bool]:
    """
    Indicate failure on the current task.

    Args:
        input (Optional[str]): Additional information about why the task failed. Must be a non-empty string if provided. Defaults to None.

    Returns:
        Dict[str, bool]: A dictionary containing:
            - ok (bool): Whether the operation was successful (always True).

    Raises:
        TypeError: If input is not a string or None.
        ValueError: If input is an empty string or contains only whitespace.
        ConversationFailureError: If storing the failure status fails or if any other error occurs during the operation.
    """
    # --- Input Validation ---
    if input is not None:
        if not isinstance(input, str):
            raise TypeError(f"argument 'input' must be a string or None, got {type(input).__name__}")
        if not input.strip():
            raise ValueError("argument 'input' cannot be empty or whitespace")
    # --- End of Input Validation ---
    
    try:
        fail_data = {
            "input": input,
            "status": "failed",
            "reason": input if input else "Task failed",
            "timestamp": _get_current_date()
        }
        
        DB.setdefault("_end_of_conversation_status", {})["fail"] = fail_data
        
        return {"ok": True}
        
    except Exception as e:
        raise ConversationFailureError(f"Failed to record failure: {e}")


@tool_spec(
    spec={
        "name": "cancel",
        "description": "Cancel the conversation. Use this when the user wants to stop the current interaction or cancel their request.",
        "parameters": {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "nullable": True,
                    "description": "Optional cancellation message or reason. Must be a non-empty string if provided."
                }
            },
            'required': []
        },
        "response": {
            "type": "object",
            "description": "A dictionary containing the cancellation status with the following keys:",
            "properties": {
                "ok": {
                    "type": "boolean",
                    "description": "Always true, indicating the conversation has been cancelled."
                }
            },
            "required": ["ok"]
        }
    },
    input_model=CancelInput,
    output_model=CancelOutput,
    error_model=[
        ErrorObject(TypeError, ["If input is not a string or None."]),
        ErrorObject(ValueError, ["If input is an empty string or contains only whitespace."]),
        ErrorObject(ConversationCancellationError, ["If storing the cancellation status fails or if any other error occurs during the operation."])
    ]
)
def cancel(input: Optional[str] = None) -> Dict[str, bool]:
    """
    Indicate cancellation of the current task.

    Args:
        input (Optional[str]): Additional information about the cancellation reason. Must be a non-empty string if provided. Defaults to None.

    Returns:
        Dict[str, bool]: A dictionary containing:
            - ok (bool): Whether the operation was successful (always True).

    Raises:
        TypeError: If input is not a string or None.
        ValueError: If input is an empty string or contains only whitespace.
        ConversationCancellationError: If storing the cancellation status fails or if any other error occurs during the operation.
    """
    # --- Input Validation ---
    if input is not None:
        if not isinstance(input, str):
            raise TypeError(f"argument 'input' must be a string or None, got {type(input).__name__}")
        if not input.strip():
            raise ValueError("argument 'input' cannot be empty or whitespace")
    # --- End of Input Validation ---
    
    try:
        cancel_data = {
            "input": input,
            "status": "cancelled",
            "reason": input if input else "Conversation cancelled",
            "timestamp": _get_current_date()
        }
        
        DB.setdefault("_end_of_conversation_status", {})["cancel"] = cancel_data
        
        return {"ok": True}
        
    except Exception as e:
        raise ConversationCancellationError(f"Failed to record cancellation: {e}")
