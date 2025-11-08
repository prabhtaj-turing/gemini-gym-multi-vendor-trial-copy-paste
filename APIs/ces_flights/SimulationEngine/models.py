from pydantic import conint, constr, BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import date
from enum import Enum

class SeatingClass(str, Enum):
    """Enumeration of available seating classes for flights."""
    ECONOMY_CLASS = "ECONOMY_CLASS"
    ECONOMY_PLUS_CLASS = "ECONOMY_PLUS_CLASS"
    BUSINESS_CLASS = "BUSINESS_CLASS"
    FIRST_CLASS = "FIRST_CLASS"
    SUITES_CLASS = "SUITES_CLASS"

class BookFlightTravelers(BaseModel):
    """Internal model for traveler data after validation (with date object)."""
    first_name: constr(strip_whitespace=True, min_length=1)
    last_name: constr(strip_whitespace=True, min_length=1)
    date_of_birth: date

class BookFlightTravelersInput(BaseModel):
    """Input model for traveler data from API calls (primitive types only - string date)."""
    first_name: constr(strip_whitespace=True, min_length=1)
    last_name: constr(strip_whitespace=True, min_length=1)
    date_of_birth: str = Field(..., description="Traveler's date of birth in YYYY-MM-DD format (string, not date object)")

# ---------------------------
# Input Models for Tool Spec
# ---------------------------


class BookFlightInput(BaseModel):
    """Input model for book_flight function - accepts only primitive types."""
    flight_id: str = Field(..., description="The unique identifier of the departure flight to book (e.g., 'AA101', 'DL201'). Must be a valid flight_id.")
    travelers: List[BookFlightTravelersInput] = Field(..., description="List of traveler details with: first_name, last_name, and date_of_birth (as string).")
    return_flight_id: Optional[str] = Field(None, description="The return flight identifier if this is a round trip. Must be a valid flight_id if provided.")
    known_traveler_number: Optional[str] = Field(None, description="The known traveler number (e.g., TSA PreCheck, Global Entry) for the booking. Must be a non-empty string if provided.")

class DoneInput(BaseModel):
    """Input model for done function."""
    input: Optional[str] = Field(None, description="Additional information to store about the conversation completion. Must be a non-empty string if provided.")

class EscalateInput(BaseModel):
    """Input model for escalate function."""
    input: Optional[str] = Field(None, description="Additional information about the escalation reason or context. Must be a non-empty string if provided.")

class FailInput(BaseModel):
    """Input model for fail function."""
    input: Optional[str] = Field(None, description="Additional information about why the task failed. Must be a non-empty string if provided.")

class CancelInput(BaseModel):
    """Input model for cancel function."""
    input: Optional[str] = Field(None, description="Additional information about the cancellation reason. Must be a non-empty string if provided.")

# ---------------------------
# Output Models for Tool Spec
# ---------------------------

class FlightSearchResult(BaseModel):
    """Individual flight search result."""
    flight_id: str = Field(..., description="The unique identifier of the flight (e.g., 'AA101', 'DL202').")
    airline: str = Field(..., description="The name of the airline operating the flight.")
    origin: str = Field(..., description="The departure location in the format of {city name, state code}.")
    destination: str = Field(..., description="The arrival location in the format of {city name, state code}.")
    depart_date: str = Field(..., description="The departure date in YYYY-MM-DD format.")
    depart_time: str = Field(..., description="The departure time in HH:MM:SS format.")
    arrival_date: str = Field(..., description="The arrival date in YYYY-MM-DD format.")
    arrival_time: str = Field(..., description="The arrival time in HH:MM:SS format.")
    price: float = Field(..., description="The price of the flight.")
    currency: str = Field(..., description="The currency of the price (e.g., 'USD').")
    stops: int = Field(..., description="The number of stops/layovers for the flight.")
    seating_class: Optional[str] = Field(None, description="The seating class of the flight (e.g., 'ECONOMY_CLASS', 'BUSINESS_CLASS').")
    checked_bags: Optional[int] = Field(None, description="The max number of checked bags allowed per person.")
    carry_on_bags: Optional[int] = Field(None, description="The max number of carry-on bags allowed per person.")

class DoneOutput(BaseModel):
    """Output model for done function."""
    ok: bool = Field(..., description="Whether the operation was successful (always True).")

class EscalateOutput(BaseModel):
    """Output model for escalate function."""
    ok: bool = Field(..., description="Whether the operation was successful (always True).")

class FailOutput(BaseModel):
    """Output model for fail function."""
    ok: bool = Field(..., description="Whether the operation was successful (always True).")

class CancelOutput(BaseModel):
    """Output model for cancel function."""
    ok: bool = Field(..., description="Whether the operation was successful (always True).")

# ---------------------------
# Legacy Models (for backward compatibility)
# ---------------------------

class SearchFlightsParams(BaseModel):
    """Input model for search_flights function."""
    destination: str = Field(..., description="The final destination of the trip in the format of 'City Name, State Code' (e.g., San Francisco, CA). If the city is not in the US, append the country name (e.g., Sydney, Australia). Must be a non-empty string.")
    earliest_departure_date: str = Field(..., description="Filter for the earliest departure date in MM-DD or YYYY-MM-DD format. Must be a valid date string.")
    num_adult_passengers: Union[int, float] = Field(..., description="The number of adult passengers. Must be at least 1.")
    num_child_passengers: Union[int, float] = Field(..., description="The number of child passengers. Must be non-negative.")
    origin: str = Field(..., description="The location where the trip starts in the format of 'City Name, State Code' (e.g., San Francisco, CA). If the city is not in the US, append the country name (e.g., Sydney, Australia). Must be a non-empty string.")
    latest_departure_date: Optional[str] = Field(None, description="Filter for the latest departure date in MM-DD or YYYY-MM-DD format. If not provided, defaults to earliest_departure_date for an exact date match. Provide a different date to search a date range. Must be a valid date string if provided. Must be on or after earliest_departure_date.")
    earliest_return_date: Optional[str] = Field(None, description="Filter for the earliest return date in MM-DD or YYYY-MM-DD format. If provided, return flights will be included in search results. Must be a valid date string if provided. Must be on or after latest_departure_date.")
    latest_return_date: Optional[str] = Field(None, description="Filter for the latest return date in MM-DD or YYYY-MM-DD format. If not provided, defaults to earliest_return_date for an exact date match. Provide a different date to search a date range. Must be a valid date string if provided. Must be on or after earliest_return_date.")
    carry_on_bag_count: Optional[int] = Field(None, description="Filter for max number of carry on bags allowed per person. Must be non-negative if provided.")
    cheapest: Optional[bool] = Field(None, description="If TRUE, the results will be sorted by price (in ascending order).")
    checked_bag_count: Optional[int] = Field(None, description="Filter for max number of checked bags allowed per person. Must be non-negative if provided.")
    currency: Optional[str] = Field(None, description="Price currency. Must be a non-empty string if provided.")
    depart_after_hour: Optional[int] = Field(None, description="Filter for flights that depart after this hour. Must be between 0 and 23 if provided.")
    depart_before_hour: Optional[int] = Field(None, description="Filter for flights that depart before this hour. Must be between 0 and 23 if provided.")
    include_airlines: Optional[List[str]] = Field(None, description="Filter by flights on these airlines only. Each airline must be a string if provided.")
    max_stops: Optional[int] = Field(None, description="Filter for maximum number of stops/layovers. Must be non-negative if provided.")
    num_infant_in_lap_passengers: Optional[int] = Field(None, description="The number of infant passengers (in lap). Must be non-negative if provided.")
    num_infant_in_seat_passengers: Optional[int] = Field(None, description="The number of infant passengers (in seat). Must be non-negative if provided.")
    seating_classes: Optional[List[SeatingClass]] = Field(None, description="Filter for seating classes of the flight. Each class must be one of: ECONOMY_CLASS, ECONOMY_PLUS_CLASS, BUSINESS_CLASS, FIRST_CLASS, SUITES_CLASS.")
    page: Optional[int] = Field(1, description="Page number for pagination (1-indexed). Must be at least 1.")
    page_size: Optional[int] = Field(10, description="Number of results per page. Must be between 1 and 100.")

class BookFlightParams(BaseModel):
    selected_flight_id: str
    travelers: List[BookFlightTravelers]

class EscalateParams(BaseModel):
    reason: Optional[str] = None

class PaginationMetadata(BaseModel):
    """
    Pagination metadata for search results.
    """
    total_results: int = Field(..., description="Total number of results matching the criteria.")
    total_pages: int = Field(..., description="Total number of pages available.")
    current_page: int = Field(..., description="Current page number (1-indexed).")
    page_size: int = Field(..., description="Number of results per page.")
    has_next: bool = Field(..., description="Whether there is a next page available.")
    has_previous: bool = Field(..., description="Whether there is a previous page available.")

class BookFlightResponse(BaseModel):
    """
    Response model for flight booking operations.
    """
    booking_id: str = Field(..., description="The unique identifier for the booking (UUID format).")
    flight_id: str = Field(..., description="The unique identifier of the departure flight.")
    confirmation_number: str = Field(..., description="The booking confirmation number (6-character hexadecimal string like a PNR, e.g., 'A3F7B2').")
    status: str = Field(..., description="The booking status.")
    failed: bool = Field(..., description="Whether the booking failed. True if status is not 'confirmed', False otherwise.")
    return_flight_id: Optional[str] = Field(None, description="The return flight identifier if this is a round trip.")
    is_round_trip: bool = Field(..., description="Whether this is a round trip.")

class SearchFlightsResponse(BaseModel):
    """
    Response model for flight search operations.
    """
    response: List[FlightSearchResult] = Field(..., description="A list of flight search results.")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata for the search results.")