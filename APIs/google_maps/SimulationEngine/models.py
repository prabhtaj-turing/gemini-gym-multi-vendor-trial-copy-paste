"""
Pydantic models for Google Maps Places API request validation.
"""
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator, conint, constr, model_validator, validator


class CircleLocation(BaseModel):
    """Model for circle location restriction."""
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in degrees")


class Circle(BaseModel):
    """Model for circle parameters."""
    center: CircleLocation = Field(..., description="Center point of the circle")
    radius: float = Field(..., gt=0, description="Radius in meters")


class LocationRestriction(BaseModel):
    """Model for location restriction parameters."""
    circle: Optional[Circle] = Field(None, description="Circular area restriction")


class RoutingParameters(BaseModel):
    """Model for routing parameters."""
    routingPreference: Optional[Literal[
        "ROUTING_PREFERENCE_UNSPECIFIED",
        "TRAFFIC_UNAWARE",
        "TRAFFIC_AWARE",
        "TRAFFIC_AWARE_OPTIMAL"
    ]] = None
    routeModifiers: Optional[Dict[str, bool]] = None
    origin: Optional[CircleLocation] = None
    travelMode: Optional[Literal[
        "TRAVEL_MODE_UNSPECIFIED",
        "DRIVE",
        "BICYCLE",
        "WALK",
        "TWO_WHEELER"
    ]] = None


class SearchNearbyRequest(BaseModel):
    """Model for searchNearby request validation."""
    includedPrimaryTypes: Optional[List[str]] = Field(default_factory=list)
    excludedPrimaryTypes: Optional[List[str]] = Field(default_factory=list)
    includedTypes: Optional[List[str]] = Field(default_factory=list)
    excludedTypes: Optional[List[str]] = Field(default_factory=list)
    languageCode: Optional[str] = Field(None, max_length=10)
    locationRestriction: Optional[LocationRestriction] = Field(default_factory=dict)
    maxResultCount: int = Field(10, gt=0, le=20)
    regionCode: Optional[str] = Field(None, max_length=2)
    rankPreference: Optional[Literal[
        "RANK_PREFERENCE_UNSPECIFIED",
        "DISTANCE",
        "POPULARITY"
    ]] = None
    routingParameters: Optional[RoutingParameters] = None

    class Config:
        extra = "allow"  # Allow extra fields for backward compatibility


class Viewport(BaseModel):
    """Model for viewport/rectangle bounds."""
    low: CircleLocation
    high: CircleLocation


class Rectangle(BaseModel):
    """Model for rectangle location bias."""
    viewport: Viewport


class LocationBias(BaseModel):
    """Model for location bias parameters."""
    circle: Optional[Circle] = None
    rectangle: Optional[Rectangle] = None


class Polyline(BaseModel):
    """Model for polyline in search along route."""
    encodedPolyline: str = Field(..., min_length=1)


class SearchAlongRouteParameters(BaseModel):
    """Model for search along route parameters."""
    polyline: Polyline


class EVOptions(BaseModel):
    """Model for EV charging options."""
    connectorTypes: Optional[List[str]] = Field(default_factory=list)
    minimumChargingRateKw: Optional[float] = Field(None, gt=0)


class SearchTextRequest(BaseModel):
    """Model for searchText request validation."""
    textQuery: str = Field(..., min_length=1, description="Required text query")
    pageSize: Optional[int] = Field(None, gt=0, le=20)
    maxResultCount: Optional[int] = Field(None, gt=0, le=20)
    strictTypeFiltering: bool = Field(False)
    includedType: Optional[str] = None
    priceLevels: Optional[List[Literal[
        "PRICE_LEVEL_UNSPECIFIED",
        "PRICE_LEVEL_FREE",
        "PRICE_LEVEL_INEXPENSIVE",
        "PRICE_LEVEL_MODERATE",
        "PRICE_LEVEL_EXPENSIVE",
        "PRICE_LEVEL_VERY_EXPENSIVE"
    ]]] = Field(default_factory=list)
    locationBias: Optional[LocationBias] = None
    openNow: bool = Field(False)
    minRating: Optional[float] = Field(None, ge=0.0, le=5.0)
    pageToken: Optional[str] = None
    includePureServiceAreaBusinesses: bool = Field(True)
    locationRestriction: Optional[LocationRestriction] = Field(default_factory=dict)
    languageCode: Optional[str] = Field(None, max_length=10)
    regionCode: Optional[str] = Field(None, max_length=2)
    searchAlongRouteParameters: Optional[SearchAlongRouteParameters] = None
    evOptions: Optional[EVOptions] = None
    routingParameters: Optional[RoutingParameters] = None
    rankPreference: Optional[Literal[
        "RANK_PREFERENCE_UNSPECIFIED",
        "DISTANCE",
        "POPULARITY"
    ]] = None

    class Config:
        extra = "allow"  # Allow extra fields for backward compatibility

from pydantic import BaseModel, Field, field_validator, conint, constr, model_validator
from typing import Optional, List, Dict, Any
import re

class Coordinates(BaseModel):
    """
    Represents geographic coordinates.

    Attributes:
        lat (float): The latitude in degrees. Must be between -90 and 90.
        lng (float): The longitude in degrees. Must be between -180 and 180.
    """
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class Place(BaseModel):
    id: str
    name: str
    address: str
    location: Coordinates
    phone_number: Optional[str] = None
    website: Optional[str] = None

class GeocodingResult(BaseModel):
    place_id: str
    formatted_address: str
    geometry: Dict[str, Any]

class DirectionsLeg(BaseModel):
    distance: Dict[str, Any]
    duration: Dict[str, Any]
    start_address: str
    end_address: str
    steps: List[Dict[str, Any]]

class DirectionsRoute(BaseModel):
    summary: str
    legs: List[DirectionsLeg]
    copyrights: str
    warnings: List[str]
    bounds: Dict[str, Any]
    fare: Optional[Dict[str, Any]] = None

class PhotoMedia(BaseModel):
    name: str
    photoUri: str 

class GetMediaInputModel(BaseModel):
    """
    Model for the GetMedia endpoint input.
    """
    name: constr(
        strip_whitespace=True,
        pattern=r"^places/[^/]+/photos/[^/]+/media$",
    ) = Field(
        ...,
        description='The resource name of a photo, formatted as "places/{place_id}/photos/{photo_reference}/media".',
    )
    maxWidthPx: Optional[conint(ge=1, le=4800)] = Field(
        None,
        description="The maximum desired photo width (range 1–4800)."
    )
    maxHeightPx: Optional[conint(ge=1, le=4800)] = Field(
        None,
        description="The maximum desired photo height (range 1–4800)."
    )
    skipHttpRedirect: bool = Field(
        False,
        description="If True, skips HTTP redirects and returns JSON data."
    )

    @model_validator(mode='after')
    def check_one_dimension_is_present(self):
        if self.maxWidthPx is None and self.maxHeightPx is None:
            raise ValueError("At least one of maxWidthPx or maxHeightPx must be specified.")
        return self
class AutocompleteOrigin(BaseModel):
    latitude: float
    longitude: float

class AutocompleteCircle(BaseModel):
    radius: float
    center: AutocompleteOrigin

class AutocompleteLocationRestriction(BaseModel):
    circle: AutocompleteCircle

class AutocompleteRequest(BaseModel):
    input: constr(min_length=1)
    inputOffset: Optional[int] = None
    languageCode: Optional[str] = None
    regionCode: Optional[str] = None
    sessionToken: Optional[str] = None
    includeQueryPredictions: Optional[bool] = False
    includePureServiceAreaBusinesses: Optional[bool] = True
    includedPrimaryTypes: Optional[List[str]] = None
    includedRegionCodes: Optional[List[str]] = None
    origin: Optional[AutocompleteOrigin] = None
    locationRestriction: Optional[AutocompleteLocationRestriction] = None

class PlacePrediction(BaseModel):
    place: str
    id: str
    distanceMeters: Optional[int] = None
    types: List[str]

class QueryPredictionText(BaseModel):
    text: str
    matches: List[Dict[str, int]]

class QueryPrediction(BaseModel):
    text: QueryPredictionText

class Suggestion(BaseModel):
    placePrediction: Optional[PlacePrediction] = None
    queryPrediction: Optional[QueryPrediction] = None

class AutocompleteResponse(BaseModel):
    suggestions: List[Suggestion]


class GetRequest(BaseModel):
    name: constr(strip_whitespace=True)
    languageCode: Optional[constr(strip_whitespace=True)] = None
    sessionToken: Optional[constr(strip_whitespace=True)] = None
    regionCode: Optional[constr(strip_whitespace=True)] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v:
            raise ValueError("name cannot be empty")
        if not v.startswith("places/"):
            raise ValueError("name must start with 'places/'")
        parts = v.split("/")
        if len(parts) != 2 or not parts[1]:
            raise ValueError("name must be in format 'places/{place_id}' where place_id is not empty")
        return v

    @field_validator('languageCode')
    @classmethod
    def validate_language_code(cls, v):
        if v is not None:
            if not v:
                raise ValueError("languageCode cannot be empty if provided")
            if not re.match(r'^[a-z]{2,3}(-[A-Z]{2})?$', v):
                raise ValueError("languageCode must be a valid ISO 639-1 language code (e.g., 'en', 'es', 'en-US')")
        return v

    @field_validator('sessionToken')
    @classmethod
    def validate_session_token(cls, v):
        if v is not None:
            if not v:
                raise ValueError("sessionToken cannot be empty if provided")
            if len(v) > 36:
                raise ValueError("sessionToken must be <= 36 ASCII characters")
            try:
                v.encode('ascii')
            except UnicodeEncodeError:
                raise ValueError("sessionToken must contain only ASCII characters")
            if not re.match(r'^[A-Za-z0-9+/=]+$', v):
                raise ValueError("sessionToken must be base64-safe (alphanumeric, +, /, = characters only)")
        return v

    @field_validator('regionCode')
    @classmethod
    def validate_region_code(cls, v):
        if v is not None:
            if not v:
                raise ValueError("regionCode cannot be empty if provided")
            if not re.match(r'^[A-Z]{2,3}$', v):
                raise ValueError("regionCode must be a valid CLDR region code (2-3 uppercase letters, e.g., 'US', 'GBR')")
        return v
