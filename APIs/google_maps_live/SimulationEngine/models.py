# google_maps_live/models.py
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import os


class TravelMode(str, Enum):
    """Supported travel modes for directions and navigation."""
    BICYCLING = "bicycling"
    BUS = "bus"
    DRIVING = "driving"
    RAIL = "rail"
    SUBWAY = "subway"
    TRAIN = "train"
    TRAM = "tram"
    TRANSIT = "transit"
    TWOWHEELER = "twowheeler"
    WALKING = "walking"

    @classmethod
    def values(cls):
        return [member.value for member in cls]

    @classmethod
    def names(cls):
        return [member.name for member in cls]


class Avoid(str, Enum):
    """Features to avoid in routes."""
    FERRIES = "ferries"
    HIGHWAYS = "highways"
    INDOOR = "indoor"
    TOLLS = "tolls"

    @classmethod
    def values(cls):
        return [member.value for member in cls]

    @classmethod
    def names(cls):
        return [member.name for member in cls]


class PriceLevel(str, Enum):
    """Price levels for filtering places."""
    INEXPENSIVE = "inexpensive"
    MODERATE = "moderate"
    EXPENSIVE = "expensive"
    VERY_EXPENSIVE = "very_expensive"

    @classmethod
    def values(cls):
        return [member.value for member in cls]

    @classmethod
    def names(cls):
        return [member.name for member in cls]


class RankPreference(str, Enum):
    """Ranking preferences for search results."""
    DEFAULT = "default"
    DISTANCE = "distance"

    @classmethod
    def values(cls):
        return [member.value for member in cls]

    @classmethod
    def names(cls):
        return [member.name for member in cls]


class UserLocation(str, Enum):
    """Special user location values."""
    MY_HOME = "MY_HOME"
    MY_LOCATION = "MY_LOCATION"
    MY_WORK = "MY_WORK"

    @classmethod
    def values(cls):
        return [member.value for member in cls]

    @classmethod
    def names(cls):
        return [member.name for member in cls]


class LatLng(BaseModel):
    """Latitude/longitude pair."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")


class SearchAlongRoute(BaseModel):
    """Parameters for searching along route support."""
    route_id: str = Field(..., description="ID of the route to be searched along")
    route_origin_offset_fraction: float = Field(..., ge=0.0, le=1.0, description="Stop location offset in fraction along the route origin")


class Fare(BaseModel):
    """Fare information for transit routes."""
    currency: str = Field(..., description="Currency code for the fare")
    value: float = Field(..., ge=0, description="Fare value")


class TravelAdvisory(BaseModel):
    """Important information for a route."""
    text: str = Field(..., description="Advisory text")
    url: Optional[str] = Field(None, description="URL for more information")
    category: str = Field(..., description="Category of the advisory")


class Detour(BaseModel):
    """Distance and duration of a detour."""
    detour_duration: str = Field(..., description="Duration of the detour")
    detour_distance: str = Field(..., description="Distance of the detour")


class Route(BaseModel):
    """A summary of directions."""
    route_id: str = Field(..., description="Unique identifier for the route")
    start_address: str = Field(..., description="Starting address")
    end_address: str = Field(..., description="Ending address")
    distance: str = Field(..., description="Total distance of the route")
    duration: str = Field(..., description="Total duration of the route")
    summary: str = Field(..., description="Summary of the route")
    url: str = Field(..., description="URL to view the route on Google Maps")
    mode: str = Field(..., description="Travel mode used")
    steps: Optional[List[str]] = Field(None, description="Step-by-step directions")
    fare: Optional[Fare] = Field(None, description="Fare information for transit routes")
    travel_advisory: Optional[List[TravelAdvisory]] = Field(None, description="Travel advisories")


class DirectionsSummary(BaseModel):
    """Response from directions API."""
    map_url: str = Field(..., description="URL to view the route on a map")
    travel_mode: str = Field(..., description="Travel mode used")
    routes: List[Route] = Field(..., description="List of route options")


class Place(BaseModel):
    """Represents a place."""
    id: str = Field(..., description="Unique place identifier")
    name: str = Field(..., description="Name of the place")
    description: Optional[str] = Field(None, description="Description of the place")
    rating: str = Field(..., description="Average rating")
    url: Optional[str] = Field(None, description="Place's website URL")
    map_url: Optional[str] = Field(None, description="URL to view place on Google Maps")
    review_count: int = Field(..., description="Number of reviews")
    user_rating_count: int = Field(..., description="Number of user ratings")
    address: str = Field(..., description="Full address")
    phone_number: str = Field(..., description="Phone number")
    photos: Optional[List[str]] = Field(None, description="List of photo URLs")
    opening_hours: Optional[List[str]] = Field(None, description="Opening hours")
    distance: Optional[str] = Field(None, description="Distance from location bias")
    distance_in_meters: Optional[int] = Field(None, description="Distance in meters")


class SummaryPlaces(BaseModel):
    """Summary of places search results."""
    map_url: str = Field(..., description="URL to view places on a map")
    places: List[Place] = Field(..., description="List of places found")
    detours: Optional[List[Detour]] = Field(None, description="Detour information")
    query: str = Field(..., description="Search query used")


class WebAnswer(BaseModel):
    """Answer from web content."""
    url: str = Field(..., description="Source URL")
    answer: str = Field(..., description="Answer text")


class AnalyzeResult(BaseModel):
    """Result of analyzing places."""
    map_answer: str = Field(..., description="Analysis result in natural language")
    web_answers: Optional[List[WebAnswer]] = Field(None, description="List of web answers")


class ShowMapResult(BaseModel):
    """Result of showing places on a map."""
    content_id: str = Field(..., description="Unique identifier for the map content")


# Input validation models
class FindDirectionsInput(BaseModel):
    """Input validation for find_directions function."""
    destination: str = Field(..., description="The destination place")
    origin: Optional[str] = Field(None, description="The origin place")
    travel_mode: Optional[TravelMode] = Field(None, description="Travel mode to use")
    waypoints: Optional[List[str]] = Field(None, description="Locations to pass through")
    avoid: Optional[List[Avoid]] = Field(None, description="Features to avoid")
    origin_location_bias: Optional[Union[str, LatLng, UserLocation]] = Field(None, description="Origin location bias. Can be a place name string, coordinate dict, or UserLocation enum value (MY_HOME, MY_LOCATION, MY_WORK)")
    destination_location_bias: Optional[Union[str, LatLng, UserLocation]] = Field(None, description="Destination location bias. Can be a place name string, coordinate dict, or UserLocation enum value (MY_HOME, MY_LOCATION, MY_WORK)")
    search_along_route: Optional[bool] = Field(None, description="Search along route (unsupported)")
    departure_time: Optional[int] = Field(None, description="Departure time in seconds since epoch")
    arrival_time: Optional[int] = Field(None, description="Arrival time in seconds since epoch")

    @field_validator('departure_time', 'arrival_time')
    @classmethod
    def validate_time_values(cls, v):
        if v is not None and v <= 0:
            raise ValueError("Time values must be non-negative")
        return v

    @field_validator('waypoints')
    @classmethod
    def validate_waypoints(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError("Waypoints list cannot be empty when provided")
        return v

    @field_validator('origin_location_bias', 'destination_location_bias')
    @classmethod
    def resolve_location_bias_values(cls, v):
        """Resolve UserLocation enum values to environment variable values."""
        if v is None:
            return None
        
        if v in UserLocation.values() or v in UserLocation.names():
            from google_maps_live.SimulationEngine.utils import get_location_from_env
            return get_location_from_env(v)
        
        return v

    def get_non_empty_fields(self) -> Dict[str, Any]:
        """
        Get all non-empty fields, excluding falsy values (None, empty lists, etc.).
        
        Returns:
            Dict[str, Any]: Dictionary containing only non-falsy fields
        """
        data = self.model_dump()
        return {k: v for k, v in data.items() if v is not None and v != [] and v != ""}


class NavigateInput(BaseModel):
    """Input validation for navigate function."""
    destination: str = Field(..., description="The destination place")
    travel_mode: Optional[TravelMode] = Field(None, description="Travel mode to use")
    waypoints: Optional[List[str]] = Field(None, description="Locations to pass through")
    avoid: Optional[List[Avoid]] = Field(None, description="Features to avoid")
    origin_location_bias: Optional[Union[str, LatLng, UserLocation]] = Field(None, description="Origin location bias. Can be a place name string, coordinate dict, or UserLocation enum value (MY_HOME, MY_LOCATION, MY_WORK)")
    destination_location_bias: Optional[Union[str, LatLng, UserLocation]] = Field(None, description="Destination location bias. Can be a place name string, coordinate dict, or UserLocation enum value (MY_HOME, MY_LOCATION, MY_WORK)")

    @field_validator('waypoints')
    @classmethod
    def validate_waypoints(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError("Waypoints list cannot be empty when provided")
        return v

    @field_validator('origin_location_bias', 'destination_location_bias')
    @classmethod
    def resolve_location_bias_values(cls, v):
        """Resolve UserLocation enum values to environment variable values."""
        if v is None:
            return None
        
        if v in UserLocation.values() or v in UserLocation.names():
            from google_maps_live.SimulationEngine.utils import get_location_from_env
            return get_location_from_env(v)
        
        return v
    
    def get_non_empty_fields(self) -> Dict[str, Any]:
        """
        Get all non-empty fields, excluding falsy values (None, empty lists, etc.).
        
        Returns:
            Dict[str, Any]: Dictionary containing only non-falsy fields
        """
        data = self.model_dump()
        return {k: v for k, v in data.items() if v is not None and v != [] and v != ""}

class QueryPlacesInput(BaseModel):
    """Input validation for query_places function."""
    query: List[str] = Field(..., min_items=1, description="Search queries")
    location_bias: Optional[Union[str, LatLng, UserLocation]] = Field(None, description="Location bias for results. Can be a place name string, coordinate dict, or UserLocation enum value (MY_HOME, MY_LOCATION, MY_WORK)")
    only_open_now: Optional[bool] = Field(None, description="Filter for places open now")
    min_rating: Optional[float] = Field(None, ge=1.0, le=5.0, description="Minimum rating filter")
    price_levels: Optional[List[PriceLevel]] = Field(None, description="Price level filters")
    rank_preference: Optional[RankPreference] = Field(None, description="Ranking preference")
    search_along_route: Optional[SearchAlongRoute] = Field(None, description="Search along route parameters")
    in_history: Optional[bool] = Field(None, description="Search in history (unsupported)")
    is_saved: Optional[bool] = Field(None, description="Search saved places (unsupported)")
    immersive_view: Optional[bool] = Field(None, description="Include immersive views (unsupported)")
    
    @field_validator("search_along_route", mode="before")
    def search_along_route_must_be_none_or_have_keys(cls, v):
        if isinstance(v, dict) and not v:
            return None
        return v

    @field_validator('location_bias')
    @classmethod
    def resolve_location_bias_values(cls, v):
        """Resolve UserLocation enum values to environment variable values."""
        if v is None:
            return None
        
        if v in UserLocation.values() or v in UserLocation.names():
            from google_maps_live.SimulationEngine.utils import get_location_from_env
            return get_location_from_env(v)
        
        return v

    def get_non_empty_fields(self) -> Dict[str, Any]:
        """
        Get all non-empty fields, excluding falsy values (None, empty lists, etc.).
        
        Returns:
            Dict[str, Any]: Dictionary containing only non-falsy fields
        """
        data = self.model_dump()
        return {k: v for k, v in data.items() if v is not None and v != [] and v != ""}


class LookupPlaceDetailsInput(BaseModel):
    """Input validation for lookup_place_details function."""
    place_ids: List[str] = Field(..., min_items=1, description="List of place IDs")
    query: Optional[str] = Field(None, description="Semantic filtering query")

    def get_non_empty_fields(self) -> Dict[str, Any]:
        """
        Get all non-empty fields, excluding falsy values (None, empty lists, etc.).
        
        Returns:
            Dict[str, Any]: Dictionary containing only non-falsy fields
        """
        data = self.model_dump()
        return {k: v for k, v in data.items() if v is not None and v != [] and v != ""}


class AnalyzePlacesInput(BaseModel):
    """Input validation for analyze_places function."""
    place_ids: List[str] = Field(..., min_items=1, description="List of place IDs")
    question: str = Field(..., min_length=1, description="Analysis question")

    @field_validator('question')
    @classmethod
    def validate_question(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError("question cannot be empty")
        return v
    
    def get_non_empty_fields(self) -> Dict[str, Any]:
        """
        Get all non-empty fields, excluding falsy values (None, empty lists, etc.).
        
        Returns:
            Dict[str, Any]: Dictionary containing only non-falsy fields
        """
        data = self.model_dump()
        return {k: v for k, v in data.items() if v is not None and v != [] and v != ""}


class ShowOnMapInput(BaseModel):
    """Input validation for show_on_map function."""
    places: Optional[List[str]] = Field(None, description="List of places to show on map")

    @field_validator('places')
    @classmethod
    def validate_places(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError("Places list cannot be empty when provided")
        return v

    def get_non_empty_fields(self) -> Dict[str, Any]:
        """
        Get all non-empty fields, excluding falsy values (None, empty lists, etc.).
        
        Returns:
            Dict[str, Any]: Dictionary containing only non-falsy fields
        """
        data = self.model_dump()
        return {k: v for k, v in data.items() if v is not None and v != [] and v != ""}