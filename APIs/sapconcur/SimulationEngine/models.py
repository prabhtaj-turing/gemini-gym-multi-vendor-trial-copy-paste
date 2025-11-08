from datetime import datetime, date
from typing import List, Dict, Optional, Union, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

# ---------------------------
# Core Entity Models
# ---------------------------

class PaymentMethod(BaseModel):
    id: str = Field(..., description="Payment method ID")
    source: str = Field(..., description="Payment source (credit_card, gift_card, certificate)")
    brand: str = Field(..., description="Card brand or gift card type")
    last_four: str = Field(..., description="Last four digits")
    amount: Optional[float] = Field(None, description="Amount for gift cards and certificates")

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique user ID as string")
    external_id: Optional[str] = Field(None, description="External system identifier")
    user_name: str = Field(..., description="Unique username for login")
    given_name: str = Field(..., description="First name")
    family_name: str = Field(..., description="Last name")
    display_name: Optional[str] = Field(None, description="Display name")
    active: bool = Field(True, description="Account status")
    email: str = Field(..., description="Primary email address")
    locale: str = Field("en-US", description="User's locale preference")
    timezone: str = Field("UTC", description="User's timezone")
    membership: Optional[str] = Field(None, description="Membership level (e.g., gold, silver, bronze)")
    payment_methods: Dict[str, PaymentMethod] = Field(default_factory=dict, description="User's payment methods")
    created_at: str = Field(default_factory=lambda: str(datetime.now()), description="Creation timestamp as string")
    last_modified: str = Field(default_factory=lambda: str(datetime.now()), description="Last modified timestamp as string")
    dob: Optional[str] = Field(None, description="Date of birth as string")
    
    # Address fields from original user data
    address_line1: Optional[str] = Field(None, description="Address line 1")
    address_line2: Optional[str] = Field(None, description="Address line 2")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State")
    country: Optional[str] = Field(None, description="Country")
    zip_code: Optional[str] = Field(None, description="ZIP/Postal code")
    
    # Saved passengers from user profile
    saved_passengers: List[Dict[str, Any]] = Field(default_factory=list, description="User's saved passenger profiles")

class Passenger(BaseModel):
    passenger_id: Optional[str] = Field(None, description="Unique passenger ID as string")
    name_first: str = Field(..., description="First name")
    name_last: str = Field(..., description="Last name")
    text_name: Optional[str] = Field(None, description="Full name as entered")
    pax_type: str = Field("ADT", description="Passenger type (ADT/CHD/INF)")
    dob: Optional[str] = Field(None, description="Date of birth as string (YYYY-MM-DD)")

class Location(BaseModel):
    id: str = Field(..., description="Unique location ID")
    name: str = Field(..., description="Location name")
    address_line1: Optional[str] = Field(None, description="Address line 1")
    address_line2: Optional[str] = Field(None, description="Address line 2")
    city: str = Field(..., description="City name")
    state_province: Optional[str] = Field(None, description="State/province code")
    country_code: str = Field(..., min_length=2, max_length=2, description="ISO country code")
    postal_code: Optional[str] = Field(None, description="Postal/ZIP code")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    is_active: bool = Field(True, description="Active status")
    location_type: Optional[str] = Field(None, description="Location type")

class BookingStatus(str, Enum):
    ISSUED = "ISSUED"  # Initial status when booking is first created
    CONFIRMED = "CONFIRMED"  # Booking is confirmed
    PENDING = "PENDING"  # Pending confirmation from supplier
    CANCELLED = "CANCELLED"  # Booking has been cancelled
    UPDATED = "UPDATED"  # Booking has been modified

class SegmentStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    WAITLISTED = "WAITLISTED"
    CANCELLED = "CANCELLED"

class SegmentType(str, Enum):
    AIR = "AIR"
    CAR = "CAR"
    HOTEL = "HOTEL"
    RAIL = "RAIL"
    DINING = "DINING"
    PARKING = "PARKING"
    RIDE = "RIDE"

class BaseSegment(BaseModel):
    segment_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique segment ID as string")
    type: SegmentType = Field(..., description="Segment type")
    status: SegmentStatus = Field(..., description="Booking status")
    confirmation_number: Optional[str] = Field(None, description="Provider confirmation number")
    start_date: str = Field(..., description="Start date/time as string")
    end_date: str = Field(..., description="End date/time as string")
    vendor: str = Field(..., description="Vendor code")
    vendor_name: Optional[str] = Field(None, description="Vendor full name")
    currency: str = Field("USD", min_length=3, max_length=3, description="Currency code")
    total_rate: float = Field(..., ge=0, description="Total cost")

class CabinClass(str, Enum):
    """Standard cabin classes for flights."""
    ECONOMY = "economy"
    BUSINESS = "business"
    FIRST = "first"
    PREMIUM_ECONOMY = "premium_economy"

class AirSegment(BaseModel):
    segment_id: str = Field(..., description="Unique segment identifier")
    type: SegmentType = Field(..., description="Segment type")
    status: SegmentStatus = Field(..., description="Current segment status")
    confirmation_number: str = Field(..., description="Booking confirmation number")
    start_date: str = Field(..., description="Departure date/time as string")
    end_date: str = Field(..., description="Arrival date/time as string")
    vendor: str = Field(..., description="Airline code")
    vendor_name: str = Field(..., description="Airline name")
    currency: str = Field("USD", description="Currency code")
    total_rate: float = Field(..., description="Total price")
    departure_airport: str = Field(..., description="Departure airport code")
    arrival_airport: str = Field(..., description="Arrival airport code")
    flight_number: str = Field(..., description="Flight number")
    aircraft_type: str = Field(..., description="Aircraft type")
    fare_class: str = Field(..., description="Fare class code")
    is_direct: bool = Field(..., description="Whether flight is direct")
    baggage: Dict[str, Any] = Field(default_factory=dict, description="Baggage information")
    
    # Enhanced fields for detailed flight operational data
    scheduled_departure_time: Optional[str] = Field(None, description="Scheduled departure time")
    scheduled_arrival_time: Optional[str] = Field(None, description="Scheduled arrival time")
    flight_schedule_data: Dict[str, Any] = Field(default_factory=dict, description="Complete flight schedule data by date")
    availability_data: Dict[str, Any] = Field(default_factory=dict, description="Seat availability data by date and class")
    pricing_data: Dict[str, Any] = Field(default_factory=dict, description="Dynamic pricing data by date and class")
    operational_status: Dict[str, Any] = Field(default_factory=dict, description="Flight operational status by date")
    
    # Estimated time fields
    estimated_departure_times: Dict[str, str] = Field(default_factory=dict, description="Estimated departure times by date")
    estimated_arrival_times: Dict[str, str] = Field(default_factory=dict, description="Estimated arrival times by date")

class CarSegment(BaseSegment):
    type: SegmentType = Field(SegmentType.CAR, description="Segment type")
    pickup_location: str = Field(..., description="Pickup location code")
    dropoff_location: str = Field(..., description="Drop-off location code")
    car_type: Optional[str] = Field(None, description="Vehicle type")

class HotelSegment(BaseSegment):
    type: SegmentType = Field(SegmentType.HOTEL, description="Segment type")
    location: str = Field(..., description="Hotel location code")
    room_type: Optional[str] = Field(None, description="Room category")
    meal_plan: Optional[str] = Field(None, description="Meal plan type")

Segment = Union[AirSegment, CarSegment, HotelSegment]

class PaymentHistory(BaseModel):
    payment_id: str = Field(..., description="ID of the payment method used")
    amount: float = Field(..., ge=0, description="Amount charged")
    timestamp: str = Field(default_factory=lambda: str(datetime.now()), description="Time of payment as string")
    type: str = Field(..., description="Type of payment (e.g., 'baggage', 'upgrade')")

class Booking(BaseModel):
    booking_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique booking ID as string")
    booking_source: str = Field(..., description="Supplier's name")
    record_locator: str = Field(..., min_length=6, description="Record locator (6+ alphanum)")
    trip_id: str = Field(..., description="Associated trip ID as string")
    date_booked_local: str = Field(default_factory=lambda: str(datetime.now()), description="Booking creation date as string")
    form_of_payment_name: Optional[str] = Field(None, description="Payment method name")
    form_of_payment_type: Optional[str] = Field(None, description="Payment method type")
    delivery: Optional[str] = Field(None, description="Delivery method")
    status: BookingStatus = Field(BookingStatus.ISSUED, description="Booking status")
    passengers: List[Passenger] = Field(..., description="Passenger details")
    segments: List[Segment] = Field(..., description="Travel segments")
    warnings: List[str] = Field(default_factory=list, description="Booking warnings")
    payment_history: List[PaymentHistory] = Field(default_factory=list, description="Payment history")
    created_at: str = Field(default_factory=lambda: str(datetime.now()), description="Creation timestamp as string")
    last_modified: str = Field(default_factory=lambda: str(datetime.now()), description="Last modified timestamp as string")
    
    # Original reservation fields
    flight_type: Optional[str] = Field(None, description="Original flight type (round_trip/one_way)")
    cabin: Optional[str] = Field(None, description="Original cabin class")
    insurance: Optional[str] = Field(None, description="Original insurance status")
    total_baggages: Optional[int] = Field(None, description="Original total baggage count")
    nonfree_baggages: Optional[int] = Field(None, description="Original non-free baggage count")
    origin: Optional[str] = Field(None, description="Original origin airport")
    destination: Optional[str] = Field(None, description="Original destination airport")

class TripStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CANCELED = "CANCELED"
    COMPLETED = "COMPLETED"
    PENDING_APPROVAL = "PENDING_APPROVAL"

class Trip(BaseModel):
    trip_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique trip ID as string")
    trip_name: str = Field(..., description="Trip name/description")
    user_id: str = Field(..., description="Trip owner ID as string")
    start_date: str = Field(..., description="Start date as string (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date as string (YYYY-MM-DD)")
    destination_summary: Optional[str] = Field(None, description="Destination summary")
    status: TripStatus = Field(TripStatus.CONFIRMED, description="Trip status")
    created_date: str = Field(default_factory=lambda: str(datetime.now()), description="Creation timestamp as string")
    last_modified_date: str = Field(default_factory=lambda: str(datetime.now()), description="Last modified timestamp as string")
    booking_type: Optional[SegmentType] = Field(None, description="Primary booking type")
    is_virtual_trip: bool = Field(False, description="Virtual trip flag")
    is_canceled: bool = Field(False, description="Cancellation status")
    is_guest_booking: bool = Field(False, description="Guest booking flag")
    booking_ids: List[str] = Field(default_factory=list, description="Associated booking IDs as strings")
    
    # Original reservation fields
    flight_type: Optional[str] = Field(None, description="Original flight type (round_trip/one_way)")
    cabin: Optional[str] = Field(None, description="Original cabin class")
    insurance: Optional[str] = Field(None, description="Original insurance status")
    total_baggages: Optional[int] = Field(None, description="Original total baggage count")
    nonfree_baggages: Optional[int] = Field(None, description="Original non-free baggage count")
    origin: Optional[str] = Field(None, description="Original origin airport")
    destination: Optional[str] = Field(None, description="Original destination airport")

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Notification ID as string")
    user_id: str = Field(..., description="Recipient user ID as string")
    session_id: str = Field(..., description="Unique session ID as string")
    template_id: str = Field(..., description="Template identifier")
    context: Dict[str, Any] = Field(..., description="Template context data")
    created_at: str = Field(default_factory=lambda: str(datetime.now()), description="Creation timestamp as string")
    url: Optional[str] = Field(None, description="Context URL")

# --------------------------
# Input Validation Models
# --------------------------
class CancelBookingInput(BaseModel):
    bookingSource: str = Field(..., min_length=1, description="Unique supplier identifier configured during SAP Concur application review")
    confirmationNumber: str = Field(..., min_length=1, description="Confirmation number of the booking to be canceled")
    userid_value: Optional[str] = Field(None, description="SAP Concur login ID of the booking owner")
    
    class Config:
        str_strip_whitespace = True  # Automatically strip whitespace from string fields

# --------------------------
# Response Models
# --------------------------
class CancelBookingResponse(BaseModel):
    success: bool = Field(..., description="Indicates if the cancellation was successful")
    message: str = Field(..., description="Human-readable message about the cancellation")
    booking_id: str = Field(..., description="Unique identifier of the cancelled booking")
    booking_source: str = Field(..., description="Supplier name of the cancelled booking")
    confirmation_number: str = Field(..., description="Confirmation number of the cancelled booking")
    status: str = Field(..., description="Current status of the booking (should be CANCELLED)")
    cancelled_at: str = Field(..., description="ISO timestamp of when the booking was cancelled")

# --------------------------
# Root Database Model
# --------------------------
class ConcurAirlineDB(BaseModel):
    users: Dict[str, User] = {}
    locations: Dict[str, Location] = {}
    trips: Dict[str, Trip] = {}
    bookings: Dict[str, Booking] = {}
    notifications: Dict[str, Notification] = {}
    
    # Indexes for faster lookups
    user_by_external_id: Dict[str, str] = {}
    booking_by_locator: Dict[str, str] = {}
    trips_by_user: Dict[str, List[str]] = {}
    bookings_by_trip: Dict[str, List[str]] = {}


class TripSummary(BaseModel):
    """Represents a summary of a trip."""
    trip_id: str = Field(..., description="Unique identifier for the trip.")
    trip_name: str = Field(..., description="Name or title of the trip (e.g., 'Sales Conference Q3').")
    start_date: str = Field(..., description="Start date of the trip (format: 'YYYY-MM-DD').")
    end_date: str = Field(..., description="End date of the trip (format: 'YYYY-MM-DD').")
    destination_summary: str = Field(..., description="A brief textual summary of the trip's main destination(s) (e.g., 'New York, NY').")
    status: str = Field(..., description="Current status of the trip (e.g., 'CONFIRMED', 'CANCELED', 'COMPLETED', 'PENDING_APPROVAL').")
    last_modified_date: str = Field(..., description="Date and time the trip was last modified (ISO 8601 format: 'YYYY-MM-DDTHH:MM:SSZ').")
    created_date: str = Field(..., description="Date and time the trip was created (ISO 8601 format: 'YYYY-MM-DDTHH:MM:SSZ').")
    booking_type: Optional[str] = Field(None, description="Primary type of booking associated with the trip (e.g., 'FLIGHT', 'HOTEL', 'PACKAGE', 'TRAIN'). This field may be null if not applicable or determinable for a summary.")
    is_virtual_trip: bool = Field(..., description="True if the trip is a virtual or placeholder entry, false otherwise.")
    is_canceled: bool = Field(..., description="True if the trip has been canceled, false otherwise.")
    is_guest_booking: bool = Field(..., description="True if the trip is a guest booking, false otherwise.")

class PaginationMetadata(BaseModel):
    """Represents pagination and other metadata for a list of results."""
    total_count: int = Field(..., description="Total number of trip summaries matching the filter criteria across all pages.")
    limit: int = Field(..., description="The maximum number of items requested per page (corresponds to 'ItemsPerPage' input or default).")
    offset_marker: Optional[str] = Field(None, description="A marker or token that can be used in a subsequent request to fetch the next page of results (cursor-based pagination). If null or absent, it indicates there are no more subsequent pages or pagination is not active for this request.")

class TripSummariesResponse(BaseModel):
    """Represents the response structure for the get_trip_summaries function."""
    summaries: List[TripSummary] = Field(..., description="The list of trip summary objects.")
    metadata: Optional[PaginationMetadata] = Field(None, description="Pagination and other metadata. This field is present if 'include_metadata' was requested as true and there are items to report on.")
class InputPassengerModel(BaseModel):
    NameFirst: str
    NameLast: str
    TextName: Optional[str] = None
    FrequentTravelerProgram: Optional[str] = None

class InputCarSegmentModel(BaseModel):
    Vendor: str
    VendorName: Optional[str] = None
    Status: Optional[str] = None
    StartDateLocal: str
    EndDateLocal: str
    ConfirmationNumber: Optional[str] = None
    StartLocation: str
    EndLocation: str
    TotalRate: float
    Currency: str
    CarType: Optional[str] = None

class InputAirSegmentModel(BaseModel):
    Vendor: str
    VendorName: Optional[str] = None
    Status: Optional[str] = None
    DepartureDateTimeLocal: str
    ArrivalDateTimeLocal: str
    ConfirmationNumber: Optional[str] = None
    DepartureAirport: str
    ArrivalAirport: str
    FlightNumber: str
    AircraftType: Optional[str] = None
    FareClass: Optional[str] = None
    TotalRate: float
    Currency: str
    IsDirect: Optional[bool] = True
    Baggage: Optional[Dict[str, int]] = Field(
        default={"count": 0, "weight_kg": 0, "nonfree_count": 0}, 
        description="Baggage allowance (e.g., {'count': 2, 'weight_kg': 23, 'nonfree_count': 1})"
    )

class InputHotelSegmentModel(BaseModel):
    Vendor: str
    VendorName: Optional[str] = None
    Status: Optional[str] = None
    CheckInDateLocal: str
    CheckOutDateLocal: str
    ConfirmationNumber: Optional[str] = None
    HotelName: Optional[str] = None
    Location: str
    RoomType: Optional[str] = None
    MealPlan: Optional[str] = None
    TotalRate: float
    Currency: str

class InputAllSegmentsModel(BaseModel):
    Car: Optional[List[InputCarSegmentModel]] = None
    Air: Optional[List[InputAirSegmentModel]] = None
    Hotel: Optional[List[InputHotelSegmentModel]] = None

class BookingInputModel(BaseModel):
    BookingSource: str
    RecordLocator: str = Field(min_length=6)
    Passengers: List[InputPassengerModel] = Field(min_length=1)
    DateBookedLocal: Optional[str] = None
    FormOfPaymentName: Optional[str] = None
    FormOfPaymentType: Optional[str] = None
    TicketMailingAddress: Optional[str] = None
    TicketPickupLocation: Optional[str] = None
    TicketPickupNumber: Optional[str] = None
    Segments: Optional[InputAllSegmentsModel] = None
    Delivery: Optional[str] = None
    Warnings: Optional[List[str]] = None
    insurance: Optional[str] = None

class CustomFieldDetail(BaseModel):
    """
    Represents a single custom field associated with a location.
    """
    field_id: str
    field_name: str
    value: Any

class LocationDetails(BaseModel):
    """
    Represents the detailed information about a specific location.
    Corresponds to the return type of the get_location_by_id function.
    """
    id: str
    name: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state_province: str
    postal_code: str
    country_code: str
    latitude: float
    longitude: float
    is_active: bool
    location_type: str
    timezone: str
    created_at: str  # ISO 8601 format
    updated_at: str  # ISO 8601 format
    custom_fields: List[CustomFieldDetail]

class GetLocationByIdArgs(BaseModel):
    """
    Pydantic model for validating the input arguments to the get_location_by_id function.
    """
    id: str  # Pydantic automatically validates that 'id' is a string.

    @validator('id')
    def id_must_not_be_empty(cls, v: str) -> str:
        """Validator to ensure the 'id' string is not empty."""
        if not v:  # An empty string evaluates to False in boolean context
            raise ValueError("ID must not be empty.")
        return v

    class Config:
        # Corresponds to "additionalProperties": "false" in the inputSchema.
        # Forbids any extra fields if the model were instantiated from a dictionary
        # with more keys than defined in the model.
        extra = "forbid"

class FlightUpdate(BaseModel):
    """Model for flight update requests."""
    flight_number: str = Field(..., description="The flight number")
    date: str = Field(..., description="The date of the flight in ISO format")
    origin: Optional[str] = Field(None, min_length=3, max_length=3, description="Origin airport code")
    destination: Optional[str] = Field(None, min_length=3, max_length=3, description="Destination airport code")
    price: Optional[float] = Field(None, description="The price of the flight.")

class FlightUpdateRequest(BaseModel):
    """Model for update_reservation_flights request."""
    booking_source: str = Field(..., description="The supplier's name that must match the booking")
    confirmation_number: str = Field(..., description="Record locator for the booking")
    fare_class: str = Field(..., description="Fare class for all flights")
    flights: List[FlightUpdate] = Field(..., min_length=1, description="List of flights to update or add")
    payment_id: str = Field(..., description="ID of the payment method to use")

class FlightUpdateResponse(BaseModel):
    """Model for update_reservation_flights response."""
    booking_id: str = Field(..., description="The unique identifier for this booking")
    booking_source: str = Field(..., description="The source from which the booking was made")
    confirmation_number: str = Field(..., description="The external record locator for the booking")
    status: str = Field("SUCCESS", description="The status of the update operation")
    fare_class: str = Field(..., description="The fare class for all flights")
    last_modified: str = Field(..., description="ISO timestamp of last modification")
    flights: List[Dict[str, Any]] = Field(..., description="Updated flight details")
    payment: Optional[Dict[str, Any]] = Field(None, description="Payment details if price changed")

class PassengerUpdate(BaseModel):
    """Model for passenger update data."""
    name_first: str = Field(..., description="First name of passenger")
    name_last: str = Field(..., description="Last name of passenger")
    text_name: Optional[str] = Field(None, description="Full name as entered")
    pax_type: str = Field("ADT", description="Passenger type (ADT/CHD/INF)")
    dob: Optional[str] = Field(None, description="Date of birth as string (YYYY-MM-DD)")

class PassengerUpdateRequest(BaseModel):
    """Model for update_reservation_passengers request."""
    booking_source: str = Field(..., description="The supplier's name that must match the booking")
    confirmation_number: str = Field(..., description="Record locator for the booking")
    passengers: List[PassengerUpdate] = Field(..., description="List of passengers to update")

class PassengerUpdateResponse(BaseModel):
    """Model for update_reservation_passengers response."""
    booking_id: str = Field(..., description="The unique identifier for this booking")
    booking_source: str = Field(..., description="The source from which the booking was made")
    confirmation_number: str = Field(..., description="The external record locator for the booking")
    status: str = Field("SUCCESS", description="The status of the update operation")
    last_modified: str = Field(..., description="ISO timestamp of last modification")
    passengers: List[Dict[str, Any]] = Field(..., description="Updated passenger details")

class CreateOrUpdateTripInput(BaseModel):
    ItinLocator: Optional[str] = None
    TripName: str
    StartDateLocal: Optional[str] = None
    EndDateLocal: Optional[str] = None
    Comments: Optional[str] = None
    is_virtual_trip: bool = Field(False, alias='IsVirtualTrip')
    is_guest_booking: bool = Field(False, alias='IsGuestBooking')
    Bookings: List['BookingInputModel']

    class Config:
        populate_by_name = True