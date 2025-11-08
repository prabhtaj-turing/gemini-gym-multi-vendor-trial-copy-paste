import datetime as dt
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum

# ---------------------------
# Enum Types
# ---------------------------

class SeatingClass(str, Enum):
    """Available seating classes for flights"""
    ECONOMY_CLASS = "ECONOMY_CLASS"
    ECONOMY_PLUS_CLASS = "ECONOMY_PLUS_CLASS"
    BUSINESS_CLASS = "BUSINESS_CLASS"
    FIRST_CLASS = "FIRST_CLASS"
    SUITES_CLASS = "SUITES_CLASS"


class ConversationState(str, Enum):
    """Conversation state types"""
    MAIN = "main"
    ESCALATE_TO_AGENT = "escalate_to_agent"
    DONE = "done"
    FAIL = "fail"
    CANCEL = "cancel"


# ---------------------------
# Sub-models for nested structures
# ---------------------------

class FlightInfo(BaseModel):
    """
    Flight information model.
    
    Represents a single flight with all its details including departure,
    arrival, pricing, and baggage information.
    """
    airline: str = Field(
        ...,
        description="Name of the airline operating the flight (e.g., 'American Airlines', 'Delta')."
    )
    depart_date: str = Field(
        ...,
        description="Departure date in YYYY-MM-DD format."
    )
    depart_time: str = Field(
        ...,
        description="Departure time in HH:MM:SS format (24-hour)."
    )
    arrival_date: str = Field(
        ...,
        description="Arrival date in YYYY-MM-DD format."
    )
    arrival_time: str = Field(
        ...,
        description="Arrival time in HH:MM:SS format (24-hour)."
    )
    price: float = Field(
        ...,
        ge=0.0,
        description="Price of the flight in the specified currency."
    )
    stops: int = Field(
        ...,
        ge=0,
        description="Number of stops/layovers for this flight (0 for direct flights)."
    )
    origin: str = Field(
        ...,
        description="Departure location in 'City, State' format (e.g., 'New York, NY')."
    )
    destination: str = Field(
        ...,
        description="Arrival location in 'City, State' format (e.g., 'Los Angeles, CA')."
    )
    seating_class: str = Field(
        ...,
        description="Seating class for the flight (e.g., 'ECONOMY_CLASS', 'BUSINESS_CLASS')."
    )
    carry_on_bags: int = Field(
        ...,
        ge=0,
        description="Maximum number of carry-on bags allowed per passenger."
    )
    checked_bags: int = Field(
        ...,
        ge=0,
        description="Maximum number of checked bags allowed per passenger."
    )
    currency: Optional[str] = Field(
        "USD",
        description="Currency code for the price. Must be 'USD'. Defaults to USD if not provided or None is sent."
    )
    
    @field_validator('currency')
    @classmethod
    def validate_currency_is_usd(cls, v):
        """Validate that currency is always USD in the database."""
        if v is not None and v.upper() != "USD":
            raise ValueError(
                f"Database currency must be 'USD'. Got '{v}'. "
                "All flight prices in the database must be stored in USD. "
                "Currency conversion is handled at the API level during search_flights."
            )
        return "USD" if v is None else v.upper()


class TravelerInfo(BaseModel):
    """
    Traveler information model.
    
    Contains personal details for a passenger booking a flight.
    """
    first_name: str = Field(
        ...,
        description="Traveler's first name."
    )
    last_name: str = Field(
        ...,
        description="Traveler's last name."
    )
    date_of_birth: str = Field(
        ...,
        description="Traveler's date of birth in YYYY-MM-DD format."
    )
    known_traveler_number: Optional[str] = Field(
        None,
        description="Known Traveler Number (TSA PreCheck) or similar security program ID. Can be null."
    )


class ConversationHistoryItem(BaseModel):
    """
    Conversation history entry.
    
    Records a state transition in the conversation flow.
    """
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp when the state transition occurred."
    )
    from_state: str = Field(
        ...,
        description="The state the conversation was transitioning from."
    )
    to_state: str = Field(
        ...,
        description="The state the conversation transitioned to."
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for the state transition. Can be null."
    )


class EnvVarsData(BaseModel):
    """
    Environment variables data for conversation state.
    
    Stores all the variables collected during the conversation along with
    their types, descriptions, and history.
    """
    variables: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of conversation variables with their current values."
    )
    variable_types: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping variable names to their Python type names (e.g., 'str', 'int', 'list')."
    )
    variable_descriptions: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping variable names to human-readable descriptions."
    )
    variable_history: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary tracking the history of variable changes. Can be empty."
    )


class SearchParams(BaseModel):
    """
    Flight search parameters.
    
    Contains all the criteria used for searching flights.
    """
    origin_city: Optional[str] = Field(
        None,
        description="Departure city in 'City, State' format."
    )
    destination_city: Optional[str] = Field(
        None,
        description="Destination city in 'City, State' format."
    )
    earliest_departure_date: Optional[str] = Field(
        None,
        description="Earliest departure date in YYYY-MM-DD format."
    )
    latest_departure_date: Optional[str] = Field(
        None,
        description="Latest departure date in YYYY-MM-DD format."
    )
    earliest_return_date: Optional[str] = Field(
        None,
        description="Earliest return date in YYYY-MM-DD format."
    )
    latest_return_date: Optional[str] = Field(
        None,
        description="Latest return date in YYYY-MM-DD format."
    )
    num_adult_passengers: int = Field(
        1,
        ge=1,
        description="Number of adult passengers."
    )
    num_child_passengers: int = Field(
        0,
        ge=0,
        description="Number of child passengers."
    )
    num_infant_in_lap_passengers: int = Field(
        0,
        ge=0,
        description="Number of infant passengers in lap."
    )
    num_infant_in_seat_passengers: int = Field(
        0,
        ge=0,
        description="Number of infant passengers in seat."
    )
    carry_on_bag_count: int = Field(
        0,
        ge=0,
        description="Number of carry-on bags per passenger."
    )
    checked_bag_count: int = Field(
        0,
        ge=0,
        description="Number of checked bags per passenger."
    )
    currency: Optional[str] = Field(
        None,
        description="Price currency code (e.g., 'USD')."
    )
    depart_after_hour: int = Field(
        0,
        ge=0,
        le=23,
        description="Departure after this hour (0-23)."
    )
    depart_before_hour: int = Field(
        0,
        ge=0,
        le=23,
        description="Departure before this hour (0-23)."
    )
    include_airlines: List[str] = Field(
        default_factory=list,
        description="List of preferred airline names."
    )
    max_stops: int = Field(
        0,
        ge=0,
        description="Maximum number of stops allowed."
    )
    seating_classes: List[str] = Field(
        default_factory=list,
        description="List of preferred seating classes."
    )
    cheapest: bool = Field(
        False,
        description="Whether to sort results by price (ascending)."
    )


class SelectedFlight(BaseModel):
    """
    Selected flight information.
    
    Contains details about a flight selected for booking.
    """
    flight_id: Optional[str] = Field(
        None,
        description="Unique identifier of the selected flight."
    )
    airline: Optional[str] = Field(
        None,
        description="Airline operating the flight."
    )
    origin: Optional[str] = Field(
        None,
        description="Departure location."
    )
    destination: Optional[str] = Field(
        None,
        description="Arrival location."
    )
    depart_date: Optional[str] = Field(
        None,
        description="Departure date."
    )
    depart_time: Optional[str] = Field(
        None,
        description="Departure time."
    )
    arrival_date: Optional[str] = Field(
        None,
        description="Arrival date."
    )
    arrival_time: Optional[str] = Field(
        None,
        description="Arrival time."
    )
    price: Optional[float] = Field(
        None,
        description="Flight price."
    )


# ---------------------------
# Internal Storage Models
# ---------------------------

class BookingStorage(BaseModel):
    """
    Internal storage model for flight bookings.
    
    Represents a completed flight booking with passenger information
    and confirmation details.
    """
    booking_id: str = Field(
        ...,
        description="Unique identifier for this booking."
    )
    flight_id: str = Field(
        ...,
        description="Flight identifier for the booked flight."
    )
    travelers: List[TravelerInfo] = Field(
        default_factory=list,
        description="List of travelers on this booking."
    )
    confirmation_number: Optional[str] = Field(
        None,
        description="Booking confirmation number. Can be null."
    )
    booking_date: Optional[str] = Field(
        None,
        description="Date and time when the booking was made (ISO 8601 format)."
    )
    status: Optional[str] = Field(
        "confirmed",
        description="Status of the booking (e.g., 'confirmed', 'cancelled', 'pending')."
    )


class FlightDataStorage(BaseModel):
    """
    Internal storage model for flight search data.
    
    Stores the results and parameters of a flight search operation.
    """
    search_id: str = Field(
        ...,
        description="Unique identifier for this search."
    )
    search_params: SearchParams = Field(
        ...,
        description="Parameters used for this flight search."
    )
    results: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of flight search results."
    )
    timestamp: Optional[str] = Field(
        None,
        description="When this search was performed (ISO 8601 format)."
    )


class ConversationStateStorage(BaseModel):
    """
    Internal storage model for conversation states.
    
    Tracks the current state of a conversation session including all
    collected variables, history, and metadata.
    """
    current_state: str = Field(
        ...,
        description="Current state of the conversation (e.g., 'main', 'escalate_to_agent')."
    )
    env_vars: Dict[str, Any] = Field(
        default_factory=dict,
        description="Environment variables for this conversation. Can be empty."
    )
    conversation_history: List[ConversationHistoryItem] = Field(
        default_factory=list,
        description="History of state transitions in this conversation."
    )
    env_vars_data: EnvVarsData = Field(
        ...,
        description="Detailed environment variable data including types and descriptions."
    )
    last_updated: str = Field(
        ...,
        description="ISO 8601 timestamp of when this conversation state was last updated."
    )


class SessionStorage(BaseModel):
    """
    Internal storage model for user sessions.
    
    Stores session-specific data for tracking user interactions.
    """
    session_id: str = Field(
        ...,
        description="Unique identifier for this session."
    )
    created_at: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp when the session was created."
    )
    last_activity: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp of the last activity in this session."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional session metadata."
    )


# ---------------------------
# Root Database Model
# ---------------------------

class CesFlightsDB(BaseModel):
    """
    Root model that validates the entire CES Flights database structure.
    
    This model ensures all data in the database conforms to the defined schemas
    for flights, bookings, conversation states, and other entities.
    """
    sample_flights: Dict[str, FlightInfo] = Field(
        default_factory=dict,
        description="Dictionary of sample flights indexed by flight ID (e.g., 'AA101')."
    )
    flight_bookings: Dict[str, BookingStorage] = Field(
        default_factory=dict,
        description="Dictionary of flight bookings indexed by booking ID."
    )
    flight_data: Dict[str, FlightDataStorage] = Field(
        default_factory=dict,
        description="Dictionary of flight search data indexed by search ID."
    )
    end_of_conversation_status: Dict[str, Any] = Field(
        default_factory=dict,
        alias='_end_of_conversation_status',
        serialization_alias='_end_of_conversation_status',
        description="Dictionary tracking end-of-conversation statuses (escalate, done, fail, cancel)."
    )
    conversation_states: Dict[str, ConversationStateStorage] = Field(
        default_factory=dict,
        description="Dictionary of conversation states indexed by session ID."
    )
    retry_counters: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="Dictionary of retry counters for each session, tracking retry attempts per operation."
    )
    sessions: Dict[str, SessionStorage] = Field(
        default_factory=dict,
        description="Dictionary of user sessions indexed by session ID."
    )
    sample_travelers: Dict[str, TravelerInfo] = Field(
        default_factory=dict,
        description="Dictionary of sample traveler profiles indexed by traveler ID."
    )
    sample_bookings: Dict[str, BookingStorage] = Field(
        default_factory=dict,
        description="Dictionary of sample bookings for testing indexed by booking ID."
    )
    use_real_datastore: bool = Field(
        False,
        description="Flag indicating whether to use real datastore instead of simulated data."
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True
    )

