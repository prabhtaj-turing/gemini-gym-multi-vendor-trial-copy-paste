from datetime import datetime
from typing import List, Dict, Optional, Union, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

# ---------------------------
# Enum Types
# ---------------------------

class FlightStatus(str, Enum):
    LANDED = "landed"
    CANCELLED = "cancelled"
    AVAILABLE = "available"
    DELAYED = "delayed"
    FLYING = "flying"
    ON_TIME = "on time"

class CabinType(str, Enum):
    BASIC_ECONOMY = "basic_economy"
    ECONOMY = "economy"
    BUSINESS = "business"

class FlightType(str, Enum):
    ONE_WAY = "one_way"
    ROUND_TRIP = "round_trip"

class PaymentSource(str, Enum):
    CREDIT_CARD = "credit_card"
    GIFT_CARD = "gift_card"
    CERTIFICATE = "certificate"

class Membership(str, Enum):
    GOLD = "gold"
    SILVER = "silver"
    REGULAR = "regular"

# ---------------------------
# Core API Models
# ---------------------------

class SeatInfo(BaseModel):
    basic_economy: int
    economy: int
    business: int

class FlightDateDetails(BaseModel):
    status: FlightStatus
    actual_departure_time_est: Optional[str] = None
    actual_arrival_time_est: Optional[str] = None
    estimated_departure_time_est: Optional[str] = None
    estimated_arrival_time_est: Optional[str] = None
    available_seats: Optional[SeatInfo] = None
    prices: Optional[SeatInfo] = None

    @validator("actual_departure_time_est", "actual_arrival_time_est", "estimated_departure_time_est", "estimated_arrival_time_est")
    @classmethod
    def validate_datetime_fields(cls, v):
        """Validate datetime fields using centralized validation."""
        if v is not None:
            from common_utils.datetime_utils import validate_airline_datetime, InvalidDateTimeFormatError
            try:
                return validate_airline_datetime(v)
            except InvalidDateTimeFormatError as e:
                from airline.SimulationEngine.custom_errors import InvalidDateTimeFormatError as AirlineInvalidDateTimeFormatError
                raise AirlineInvalidDateTimeFormatError(f"Invalid datetime format: {e}")
        return v

class Flight(BaseModel):
    flight_number: str
    origin: str
    destination: str
    scheduled_departure_time_est: str
    scheduled_arrival_time_est: str
    dates: Dict[str, FlightDateDetails]

    @validator("scheduled_departure_time_est", "scheduled_arrival_time_est")
    @classmethod
    def validate_scheduled_times(cls, v):
        """Validate scheduled time fields using centralized validation."""
        from common_utils.datetime_utils import validate_airline_datetime, InvalidDateTimeFormatError
        try:
            return validate_airline_datetime(v)
        except InvalidDateTimeFormatError as e:
            from airline.SimulationEngine.custom_errors import InvalidDateTimeFormatError as AirlineInvalidDateTimeFormatError
            raise AirlineInvalidDateTimeFormatError(f"Invalid scheduled time format: {e}")

class Passenger(BaseModel):
    first_name: str
    last_name: str
    dob: str

    @validator("dob")
    @classmethod
    def validate_dob(cls, v):
        """Validate date of birth using centralized validation."""
        from common_utils.datetime_utils import validate_airline_date, InvalidDateTimeFormatError
        try:
            return validate_airline_date(v)
        except InvalidDateTimeFormatError as e:
            from airline.SimulationEngine.custom_errors import InvalidDateTimeFormatError as AirlineInvalidDateTimeFormatError
            raise AirlineInvalidDateTimeFormatError(f"Invalid date of birth format: {e}")

class FlightInReservation(BaseModel):
    origin: str
    destination: str
    flight_number: str
    date: str
    price: int

    @validator("date")
    @classmethod
    def validate_date(cls, v):
        """Validate flight date using centralized validation."""
        from common_utils.datetime_utils import validate_airline_date, InvalidDateTimeFormatError
        try:
            return validate_airline_date(v)
        except InvalidDateTimeFormatError as e:
            from airline.SimulationEngine.custom_errors import InvalidDateTimeFormatError as AirlineInvalidDateTimeFormatError
            raise AirlineInvalidDateTimeFormatError(f"Invalid flight date format: {e}")

class PaymentMethodInReservation(BaseModel):
    payment_id: str
    amount: float

class Reservation(BaseModel):
    reservation_id: str
    user_id: str
    origin: str
    destination: str
    flight_type: FlightType
    cabin: CabinType
    flights: List[FlightInReservation]
    passengers: List[Passenger]
    payment_history: List[PaymentMethodInReservation]
    created_at: str
    total_baggages: int
    nonfree_baggages: int
    insurance: str
    status: Optional[str] = None

    @validator("created_at")
    @classmethod
    def validate_created_at(cls, v):
        """Validate creation timestamp using centralized validation."""
        from common_utils.datetime_utils import validate_airline_datetime, InvalidDateTimeFormatError
        try:
            return validate_airline_datetime(v)
        except InvalidDateTimeFormatError as e:
            from airline.SimulationEngine.custom_errors import InvalidDateTimeFormatError as AirlineInvalidDateTimeFormatError
            raise AirlineInvalidDateTimeFormatError(f"Invalid creation time format: {e}")

class PaymentMethod(BaseModel):
    source: PaymentSource
    brand: Optional[str] = None
    last_four: Optional[str] = None
    id: str
    amount: Optional[int] = None

class User(BaseModel):
    name: Dict[str, str]
    address: Dict[str, str]
    email: str
    dob: str
    payment_methods: Dict[str, PaymentMethod]
    saved_passengers: List[Passenger]
    membership: Membership
    reservations: List[str]

    @validator("dob")
    @classmethod
    def validate_dob(cls, v):
        """Validate user date of birth using centralized validation."""
        from common_utils.datetime_utils import validate_airline_date, InvalidDateTimeFormatError
        try:
            return validate_airline_date(v)
        except InvalidDateTimeFormatError as e:
            from airline.SimulationEngine.custom_errors import InvalidDateTimeFormatError as AirlineInvalidDateTimeFormatError
            raise AirlineInvalidDateTimeFormatError(f"Invalid user date of birth format: {e}")

# ---------------------------
# Root Database Model
# ---------------------------

class AirlineDB(BaseModel):
    """Validates entire database structure"""
    flights: Dict[str, Flight]
    reservations: Dict[str, Reservation]
    users: Dict[str, User]

    class Config:
        str_strip_whitespace = True
