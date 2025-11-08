# google_maps_live/tests/test_models.py
import pytest
from pydantic import ValidationError
from google_maps_live.SimulationEngine.models import (
    TravelMode, Avoid, PriceLevel, RankPreference, UserLocation,
    LatLng, SearchAlongRoute, Fare, TravelAdvisory, Detour,
    Route, DirectionsSummary, Place, SummaryPlaces, WebAnswer,
    AnalyzeResult, ShowMapResult,
    FindDirectionsInput, NavigateInput, QueryPlacesInput,
    LookupPlaceDetailsInput, AnalyzePlacesInput, ShowOnMapInput
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestEnums(BaseTestCaseWithErrorHandler):
    """Test cases for enum classes."""
    
    def test_travel_mode_enum(self):
        """Test TravelMode enum values."""
        assert TravelMode.DRIVING == "driving"
        assert TravelMode.WALKING == "walking"
        assert TravelMode.BICYCLING == "bicycling"
        assert TravelMode.TRANSIT == "transit"
        assert TravelMode.BUS == "bus"
        assert TravelMode.RAIL == "rail"
        assert TravelMode.SUBWAY == "subway"
        assert TravelMode.TRAIN == "train"
        assert TravelMode.TRAM == "tram"
        assert TravelMode.TWOWHEELER == "twowheeler"
    
    def test_avoid_enum(self):
        """Test Avoid enum values."""
        assert Avoid.FERRIES == "ferries"
        assert Avoid.HIGHWAYS == "highways"
        assert Avoid.INDOOR == "indoor"
        assert Avoid.TOLLS == "tolls"
    
    def test_price_level_enum(self):
        """Test PriceLevel enum values."""
        assert PriceLevel.INEXPENSIVE == "inexpensive"
        assert PriceLevel.MODERATE == "moderate"
        assert PriceLevel.EXPENSIVE == "expensive"
        assert PriceLevel.VERY_EXPENSIVE == "very_expensive"
    
    def test_rank_preference_enum(self):
        """Test RankPreference enum values."""
        assert RankPreference.DEFAULT == "default"
        assert RankPreference.DISTANCE == "distance"
    
    def test_user_location_enum(self):
        """Test UserLocation enum values."""
        assert UserLocation.MY_HOME == "MY_HOME"
        assert UserLocation.MY_LOCATION == "MY_LOCATION"
        assert UserLocation.MY_WORK == "MY_WORK"


class TestBasicModels(BaseTestCaseWithErrorHandler):
    """Test cases for basic data models."""
    
    def test_latlng_model(self):
        """Test LatLng model validation."""
        # Valid coordinates
        latlng = LatLng(latitude=37.7749, longitude=-122.4194)
        assert latlng.latitude == 37.7749
        assert latlng.longitude == -122.4194
        
        # Invalid latitude
        self.assert_error_behavior(
            lambda: LatLng(latitude=91.0, longitude=-122.4194),
            ValidationError,
            "Input should be less than or equal to 90"
        )
        
        # Invalid longitude
        self.assert_error_behavior(
            lambda: LatLng(latitude=37.7749, longitude=181.0),
            ValidationError,
            "Input should be less than or equal to 180"
        )
    
    def test_search_along_route_model(self):
        """Test SearchAlongRoute model validation."""
        # Valid parameters
        search = SearchAlongRoute(
            route_id="route_123",
            route_origin_offset_fraction=0.5
        )
        assert search.route_id == "route_123"
        assert search.route_origin_offset_fraction == 0.5
        
        # Invalid offset fraction
        self.assert_error_behavior(
            lambda: SearchAlongRoute(
                route_id="route_123",
                route_origin_offset_fraction=1.5
            ),
            ValidationError,
            "Input should be less than or equal to 1"
        )
    
    def test_fare_model(self):
        """Test Fare model validation."""
        # Valid fare
        fare = Fare(currency="USD", value=2.50)
        assert fare.currency == "USD"
        assert fare.value == 2.50
        
        # Invalid negative value
        self.assert_error_behavior(
            lambda: Fare(currency="USD", value=-1.0),
            ValidationError,
            "Input should be greater than or equal to 0"
        )
    
    def test_travel_advisory_model(self):
        """Test TravelAdvisory model validation."""
        advisory = TravelAdvisory(
            text="Road construction ahead",
            url="https://example.com/advisory",
            category="TEMPORARY_ROAD_CLOSURE"
        )
        assert advisory.text == "Road construction ahead"
        assert advisory.url == "https://example.com/advisory"
        assert advisory.category == "TEMPORARY_ROAD_CLOSURE"
    
    def test_detour_model(self):
        """Test Detour model validation."""
        detour = Detour(
            detour_duration="15 mins",
            detour_distance="2.3 km"
        )
        assert detour.detour_duration == "15 mins"
        assert detour.detour_distance == "2.3 km"


class TestComplexModels(BaseTestCaseWithErrorHandler):
    """Test cases for complex data models."""
    
    def test_route_model(self):
        """Test Route model validation."""
        route = Route(
            route_id="route_123",
            start_address="Mountain View, CA",
            end_address="San Francisco, CA",
            distance="15.2 km",
            duration="25 mins",
            summary="Route from Mountain View to San Francisco",
            url="https://maps.google.com/directions",
            mode="driving",
            steps=["Start at Mountain View", "Follow route", "Arrive at San Francisco"]
        )
        assert route.route_id == "route_123"
        assert route.start_address == "Mountain View, CA"
        assert route.end_address == "San Francisco, CA"
        assert route.mode == "driving"
        assert len(route.steps) == 3
    
    def test_place_model(self):
        """Test Place model validation."""
        place = Place(
            id="place_123",
            name="Sample Restaurant",
            description="A great place to eat",
            rating="4.2",
            url="https://example.com/restaurant",
            map_url="https://maps.google.com/place",
            review_count=150,
            user_rating_count=150,
            address="123 Main St, City, CA",
            phone_number="+1-555-0123",
            photos=["https://example.com/photo1.jpg"],
            opening_hours=["Monday: 9:00 AM – 6:00 PM"],
            distance="0.5 km",
            distance_in_meters=500
        )
        assert place.id == "place_123"
        assert place.name == "Sample Restaurant"
        assert place.rating == "4.2"
        assert place.review_count == 150
        assert place.distance_in_meters == 500
    
    def test_directions_summary_model(self):
        """Test DirectionsSummary model validation."""
        route = Route(
            route_id="route_123",
            start_address="Mountain View, CA",
            end_address="San Francisco, CA",
            distance="15.2 km",
            duration="25 mins",
            summary="Route summary",
            url="https://maps.google.com/directions",
            mode="driving"
        )
        
        summary = DirectionsSummary(
            map_url="https://maps.google.com/directions",
            travel_mode="driving",
            routes=[route]
        )
        assert summary.map_url == "https://maps.google.com/directions"
        assert summary.travel_mode == "driving"
        assert len(summary.routes) == 1
    
    def test_summary_places_model(self):
        """Test SummaryPlaces model validation."""
        place = Place(
            id="place_123",
            name="Sample Place",
            rating="4.2",
            review_count=150,
            user_rating_count=150,
            address="123 Main St",
            phone_number="+1-555-0123"
        )
        
        summary = SummaryPlaces(
            map_url="https://maps.google.com/maps",
            places=[place],
            detours=[],
            query="restaurants"
        )
        assert summary.map_url == "https://maps.google.com/maps"
        assert len(summary.places) == 1
        assert summary.query == "restaurants"
    
    def test_web_answer_model(self):
        """Test WebAnswer model validation."""
        web_answer = WebAnswer(
            url="https://example.com/review",
            answer="This place has excellent reviews."
        )
        assert web_answer.url == "https://example.com/review"
        assert web_answer.answer == "This place has excellent reviews."
    
    def test_analyze_result_model(self):
        """Test AnalyzeResult model validation."""
        web_answer = WebAnswer(
            url="https://example.com/review",
            answer="Great place!"
        )
        
        result = AnalyzeResult(
            map_answer="Analysis result",
            web_answers=[web_answer]
        )
        assert result.map_answer == "Analysis result"
        assert len(result.web_answers) == 1
    
    def test_show_map_result_model(self):
        """Test ShowMapResult model validation."""
        result = ShowMapResult(
            content_id="map_content_123"
        )
        assert result.content_id == "map_content_123"


class TestInputValidationModels(BaseTestCaseWithErrorHandler):
    """Test cases for input validation models."""
    
    def test_find_directions_input_valid(self):
        """Test valid FindDirectionsInput."""
        input_data = FindDirectionsInput(
            destination="San Francisco, CA",
            origin="Mountain View, CA",
            travel_mode=TravelMode.DRIVING,
            waypoints=["Palo Alto, CA"],
            avoid=[Avoid.TOLLS],
            departure_time=1640995200
        )
        assert input_data.destination == "San Francisco, CA"
        assert input_data.origin == "Mountain View, CA"
        assert input_data.travel_mode == TravelMode.DRIVING
    
    def test_find_directions_input_invalid_time(self):
        """Test FindDirectionsInput with invalid time values."""
        self.assert_error_behavior(
            lambda: FindDirectionsInput(
                destination="San Francisco, CA",
                departure_time=-1
            ),
            ValidationError,
            "Time values must be non-negative"
        )
    
    def test_find_directions_input_empty_waypoints(self):
        """Test FindDirectionsInput with empty waypoints."""
        self.assert_error_behavior(
            lambda: FindDirectionsInput(
                destination="San Francisco, CA",
                waypoints=[]
            ),
            ValidationError,
            "Waypoints list cannot be empty when provided"
        )
    
    def test_navigate_input_valid(self):
        """Test valid NavigateInput."""
        input_data = NavigateInput(
            destination="San Francisco, CA",
            travel_mode=TravelMode.WALKING,
            waypoints=["Palo Alto, CA"],
            avoid=[Avoid.HIGHWAYS]
        )
        assert input_data.destination == "San Francisco, CA"
        assert input_data.travel_mode == TravelMode.WALKING
    
    def test_query_places_input_valid(self):
        """Test valid QueryPlacesInput."""
        input_data = QueryPlacesInput(
            query=["restaurants", "coffee shops"],
            location_bias="San Francisco, CA",
            only_open_now=True,
            min_rating=4.0,
            price_levels=[PriceLevel.MODERATE, PriceLevel.EXPENSIVE],
            rank_preference=RankPreference.DISTANCE
        )
        assert len(input_data.query) == 2
        assert input_data.min_rating == 4.0
        assert len(input_data.price_levels) == 2
    
    def test_query_places_input_invalid_rating(self):
        """Test QueryPlacesInput with invalid rating."""
        self.assert_error_behavior(
            lambda: QueryPlacesInput(
                query=["restaurants"],
                min_rating=6.0
            ),
            ValidationError,
            "Input should be less than or equal to 5"
        )
    
    def test_lookup_place_details_input_valid(self):
        """Test valid LookupPlaceDetailsInput."""
        input_data = LookupPlaceDetailsInput(
            place_ids=["place_123", "place_456"],
            query="reviews about food"
        )
        assert len(input_data.place_ids) == 2
        assert input_data.query == "reviews about food"
    
    def test_lookup_place_details_input_empty_ids(self):
        """Test LookupPlaceDetailsInput with empty place IDs."""
        self.assert_error_behavior(
            lambda: LookupPlaceDetailsInput(place_ids=[]),
            ValidationError,
            "List should have at least 1 item after validation, not 0"
        )
    
    def test_analyze_places_input_valid(self):
        """Test valid AnalyzePlacesInput."""
        input_data = AnalyzePlacesInput(
            place_ids=["place_123"],
            question="What are the best features?"
        )
        assert len(input_data.place_ids) == 1
        assert input_data.question == "What are the best features?"
    
    def test_analyze_places_input_empty_question(self):
        """Test AnalyzePlacesInput with empty question."""
        self.assert_error_behavior(
            lambda: AnalyzePlacesInput(
                place_ids=["place_123"],
                question=""
            ),
            ValidationError,
            "String should have at least 1 character"
        )
    
    def test_show_on_map_input_valid(self):
        """Test valid ShowOnMapInput."""
        input_data = ShowOnMapInput(
            places=["place_123", "place_456"]
        )
        assert len(input_data.places) == 2
    
    def test_show_on_map_input_empty_places(self):
        """Test ShowOnMapInput with empty places list."""
        self.assert_error_behavior(
            lambda: ShowOnMapInput(places=[]),
            ValidationError,
            "Value error, Places list cannot be empty when provided"
        ) 