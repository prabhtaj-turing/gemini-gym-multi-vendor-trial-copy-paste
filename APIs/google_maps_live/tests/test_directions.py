# google_maps_live/tests/test_directions.py
import pytest
import os
from unittest.mock import patch, MagicMock
from google_maps_live.directions import find_directions, navigate
from google_maps_live.SimulationEngine.models import TravelMode, Avoid, UserLocation, FindDirectionsInput, NavigateInput, LatLng, DirectionsSummary
from google_maps_live.SimulationEngine.utils import get_location_from_env
from google_maps_live.SimulationEngine.custom_errors import UserLocationError, UndefinedLocationError
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestEnumHandlingInDirections(BaseTestCaseWithErrorHandler):
    """Test cases for proper enum handling in directions functions."""
    
    @patch('google_maps_live.directions.get_model_from_gemini_response')
    def test_find_directions_avoid_enum_handling(self, mock_gemini_response):
        """Test that avoid enum values are properly converted to strings in route query."""
        # Mock the Gemini response
        mock_gemini_response.return_value = DirectionsSummary(
            map_url="https://maps.google.com",
            travel_mode="driving",
            routes=[]
        )
        
        # Test with avoid parameter containing enum values
        result = find_directions(
            destination="San Francisco, CA",
            origin="Mountain View, CA",
            avoid=["tolls", "highways"]  # These will be converted to Avoid enums
        )
        
        # Verify the function was called with proper enum handling
        mock_gemini_response.assert_called_once()
        call_args = mock_gemini_response.call_args[0]
        route_query = call_args[0]
        
        # The route query should contain the string values, not enum representations
        self.assertIn("avoiding tolls, highways", route_query)
        self.assertNotIn("<Avoid.", route_query)  # Should not contain enum string representation
    
    @patch('google_maps_live.directions.get_model_from_gemini_response')
    def test_find_directions_travel_mode_enum_handling(self, mock_gemini_response):
        """Test that travel_mode enum values are properly converted to strings."""
        # Mock the Gemini response
        mock_gemini_response.return_value = DirectionsSummary(
            map_url="https://maps.google.com",
            travel_mode="walking",
            routes=[]
        )
        
        # Test with travel_mode parameter
        result = find_directions(
            destination="San Francisco, CA",
            origin="Mountain View, CA",
            travel_mode="walking"  # This will be converted to TravelMode enum
        )
        
        # Verify the function was called with proper enum handling
        mock_gemini_response.assert_called_once()
        call_args = mock_gemini_response.call_args[0]
        route_query = call_args[0]
        
        # The route query should contain the string value, not enum representation
        self.assertIn("using walking", route_query)
        self.assertNotIn("<TravelMode.", route_query)  # Should not contain enum string representation
    
    @patch('google_maps_live.directions.get_model_from_gemini_response')
    def test_navigate_avoid_enum_handling(self, mock_gemini_response):
        """Test that avoid enum values are properly converted to strings in navigate function."""
        # Mock the Gemini response
        mock_gemini_response.return_value = DirectionsSummary(
            map_url="https://maps.google.com",
            travel_mode="driving",
            routes=[]
        )
        
        # Test with avoid parameter containing enum values
        result = navigate(
            destination="San Francisco, CA",
            origin_location_bias="Mountain View, CA",
            avoid=["tolls", "ferries"]  # These will be converted to Avoid enums
        )
        
        # Verify the function was called with proper enum handling
        mock_gemini_response.assert_called_once()
        call_args = mock_gemini_response.call_args[0]
        nav_query = call_args[0]
        
        # The nav query should contain the string values, not enum representations
        self.assertIn("avoiding tolls, ferries", nav_query)
        self.assertNotIn("<Avoid.", nav_query)  # Should not contain enum string representation


class TestResolveLocationBiasValues(BaseTestCaseWithErrorHandler):
    """Test cases for the resolve_location_bias_values validator function."""
    
    def test_resolve_location_bias_values_none(self):
        """Test that None values are returned as-is."""
        # Test with FindDirectionsInput
        input_data = FindDirectionsInput(
            destination="San Francisco, CA",
            origin_location_bias=None,
            destination_location_bias=None
        )
        assert input_data.origin_location_bias is None
        assert input_data.destination_location_bias is None
        
        # Test with NavigateInput
        input_data = NavigateInput(
            destination="San Francisco, CA",
            origin_location_bias=None,
            destination_location_bias=None
        )
        assert input_data.origin_location_bias is None
        assert input_data.destination_location_bias is None
    
    def test_resolve_location_bias_values_string_place(self):
        """Test that string place names are returned as-is."""
        # Test with FindDirectionsInput
        input_data = FindDirectionsInput(
            destination="San Francisco, CA",
            origin_location_bias="Mountain View, CA",
            destination_location_bias="Palo Alto, CA"
        )
        assert input_data.origin_location_bias == "Mountain View, CA"
        assert input_data.destination_location_bias == "Palo Alto, CA"
        
        # Test with NavigateInput
        input_data = NavigateInput(
            destination="San Francisco, CA",
            origin_location_bias="Mountain View, CA",
            destination_location_bias="Palo Alto, CA"
        )
        assert input_data.origin_location_bias == "Mountain View, CA"
        assert input_data.destination_location_bias == "Palo Alto, CA"
    
    def test_resolve_location_bias_values_coordinate_dict(self):
        """Test that coordinate dictionaries are converted to LatLng objects."""
        coord_dict = {"latitude": 37.7749, "longitude": -122.4194}
        
        # Test with FindDirectionsInput
        input_data = FindDirectionsInput(
            destination="San Francisco, CA",
            origin_location_bias=coord_dict,
            destination_location_bias=coord_dict
        )
        assert isinstance(input_data.origin_location_bias, LatLng)
        assert input_data.origin_location_bias.latitude == 37.7749
        assert input_data.origin_location_bias.longitude == -122.4194
        assert isinstance(input_data.destination_location_bias, LatLng)
        assert input_data.destination_location_bias.latitude == 37.7749
        assert input_data.destination_location_bias.longitude == -122.4194
        
        # Test with NavigateInput
        input_data = NavigateInput(
            destination="San Francisco, CA",
            origin_location_bias=coord_dict,
            destination_location_bias=coord_dict
        )
        assert isinstance(input_data.origin_location_bias, LatLng)
        assert input_data.origin_location_bias.latitude == 37.7749
        assert input_data.origin_location_bias.longitude == -122.4194
        assert isinstance(input_data.destination_location_bias, LatLng)
        assert input_data.destination_location_bias.latitude == 37.7749
        assert input_data.destination_location_bias.longitude == -122.4194
    
    @patch('google_maps_live.SimulationEngine.utils.get_location_from_env')
    def test_resolve_location_bias_values_user_location_names(self, mock_get_location):
        """Test that UserLocation enum names are resolved to environment values."""
        mock_get_location.return_value = "123 Main St, Mountain View, CA"
        
        # Test with FindDirectionsInput using enum names
        input_data = FindDirectionsInput(
            destination="San Francisco, CA",
            origin_location_bias="MY_HOME",
            destination_location_bias="MY_WORK"
        )
        assert input_data.origin_location_bias == "123 Main St, Mountain View, CA"
        assert input_data.destination_location_bias == "123 Main St, Mountain View, CA"
        
        # Test with NavigateInput using enum names
        input_data = NavigateInput(
            destination="San Francisco, CA",
            origin_location_bias="MY_LOCATION",
            destination_location_bias="MY_HOME"
        )
        assert input_data.origin_location_bias == "123 Main St, Mountain View, CA"
        assert input_data.destination_location_bias == "123 Main St, Mountain View, CA"
        
        # Verify get_location_from_env was called with correct arguments
        assert mock_get_location.call_count == 4
        mock_get_location.assert_any_call("MY_HOME")
        mock_get_location.assert_any_call("MY_WORK")
        mock_get_location.assert_any_call("MY_LOCATION")
    
    @patch('google_maps_live.SimulationEngine.utils.get_location_from_env')
    def test_resolve_location_bias_values_user_location_values(self, mock_get_location):
        """Test that UserLocation enum values are resolved to environment values."""
        mock_get_location.return_value = "456 Work Ave, Palo Alto, CA"
        
        # Test with FindDirectionsInput using enum values
        input_data = FindDirectionsInput(
            destination="San Francisco, CA",
            origin_location_bias=UserLocation.MY_HOME,
            destination_location_bias=UserLocation.MY_WORK
        )
        assert input_data.origin_location_bias == "456 Work Ave, Palo Alto, CA"
        assert input_data.destination_location_bias == "456 Work Ave, Palo Alto, CA"
        
        # Test with NavigateInput using enum values
        input_data = NavigateInput(
            destination="San Francisco, CA",
            origin_location_bias=UserLocation.MY_LOCATION,
            destination_location_bias=UserLocation.MY_HOME
        )
        assert input_data.origin_location_bias == "456 Work Ave, Palo Alto, CA"
        assert input_data.destination_location_bias == "456 Work Ave, Palo Alto, CA"
        
        # Verify get_location_from_env was called with correct arguments
        assert mock_get_location.call_count == 4
        mock_get_location.assert_any_call(UserLocation.MY_HOME)
        mock_get_location.assert_any_call(UserLocation.MY_WORK)
        mock_get_location.assert_any_call(UserLocation.MY_LOCATION)
    
    @patch('google_maps_live.SimulationEngine.utils.get_location_from_env')
    def test_resolve_location_bias_values_mixed_types(self, mock_get_location):
        """Test that mixed types work correctly in the same input."""
        mock_get_location.return_value = "789 Current St, San Jose, CA"
        
        # Test with FindDirectionsInput - mix of types
        input_data = FindDirectionsInput(
            destination="San Francisco, CA",
            origin_location_bias="Mountain View, CA",  # String place
            destination_location_bias=UserLocation.MY_LOCATION  # Enum value
        )
        assert input_data.origin_location_bias == "Mountain View, CA"
        assert input_data.destination_location_bias == "789 Current St, San Jose, CA"
        
        # Test with NavigateInput - mix of types
        coord_dict = {"latitude": 37.7749, "longitude": -122.4194}
        input_data = NavigateInput(
            destination="San Francisco, CA",
            origin_location_bias=coord_dict,  # Coordinate dict
            destination_location_bias="MY_HOME"  # Enum name
        )
        assert isinstance(input_data.origin_location_bias, LatLng)
        assert input_data.origin_location_bias.latitude == 37.7749
        assert input_data.origin_location_bias.longitude == -122.4194
        assert input_data.destination_location_bias == "789 Current St, San Jose, CA"
        
        # Verify get_location_from_env was called only for enum values
        assert mock_get_location.call_count == 2
        mock_get_location.assert_any_call(UserLocation.MY_LOCATION)
        mock_get_location.assert_any_call("MY_HOME")


class TestGetLocationFromEnv(BaseTestCaseWithErrorHandler):
    """Test cases for the get_location_from_env function."""
    
    def test_get_location_from_env_valid_names(self):
        """Test that valid UserLocation names work correctly."""
        # Test with environment variables set
        with patch.dict(os.environ, {
            'MY_HOME': '123 Home St, Mountain View, CA',
            'MY_LOCATION': '456 Current Ave, Palo Alto, CA',
            'MY_WORK': '789 Work Blvd, San Francisco, CA'
        }):
            assert get_location_from_env('MY_HOME') == '123 Home St, Mountain View, CA'
            assert get_location_from_env('MY_LOCATION') == '456 Current Ave, Palo Alto, CA'
            assert get_location_from_env('MY_WORK') == '789 Work Blvd, San Francisco, CA'
    
    def test_get_location_from_env_valid_values(self):
        """Test that valid UserLocation enum values work correctly."""
        # Test with environment variables set
        with patch.dict(os.environ, {
            'MY_HOME': '123 Home St, Mountain View, CA',
            'MY_LOCATION': '456 Current Ave, Palo Alto, CA',
            'MY_WORK': '789 Work Blvd, San Francisco, CA'
        }):
            assert get_location_from_env(UserLocation.MY_HOME) == '123 Home St, Mountain View, CA'
            assert get_location_from_env(UserLocation.MY_LOCATION) == '456 Current Ave, Palo Alto, CA'
            assert get_location_from_env(UserLocation.MY_WORK) == '789 Work Blvd, San Francisco, CA'
    
    def test_get_location_from_env_missing_environment_variable(self):
        """Test that missing environment variables raise UndefinedLocationError."""
        # Test with no environment variables set
        with patch.dict(os.environ, {}, clear=True):
            self.assert_error_behavior(
                lambda: get_location_from_env('MY_HOME'),
                UndefinedLocationError,
                "Environment variable for 'MY_HOME' is not defined."
            )
            
            self.assert_error_behavior(
                lambda: get_location_from_env('MY_LOCATION'),
                UndefinedLocationError,
                "Environment variable for 'MY_LOCATION' is not defined."
            )
            
            self.assert_error_behavior(
                lambda: get_location_from_env('MY_WORK'),
                UndefinedLocationError,
                "Environment variable for 'MY_WORK' is not defined."
            )
    
    def test_get_location_from_env_empty_environment_variable(self):
        """Test that empty environment variables raise UndefinedLocationError."""
        # Test with empty environment variables
        with patch.dict(os.environ, {
            'MY_HOME': '',
            'MY_LOCATION': '',
            'MY_WORK': ''
        }):
            self.assert_error_behavior(
                lambda: get_location_from_env('MY_HOME'),
                UndefinedLocationError,
                "Environment variable for 'MY_HOME' is not defined."
            )
            
            self.assert_error_behavior(
                lambda: get_location_from_env('MY_LOCATION'),
                UndefinedLocationError,
                "Environment variable for 'MY_LOCATION' is not defined."
            )
            
            self.assert_error_behavior(
                lambda: get_location_from_env('MY_WORK'),
                UndefinedLocationError,
                "Environment variable for 'MY_WORK' is not defined."
            )
    
    def test_get_location_from_env_invalid_location_name(self):
        """Test that invalid location names raise UserLocationError."""
        self.assert_error_behavior(
            lambda: get_location_from_env('INVALID_LOCATION'),
            UserLocationError,
            "Invalid location variable: 'INVALID_LOCATION'. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )
        
        self.assert_error_behavior(
            lambda: get_location_from_env(''),
            UserLocationError,
            "Invalid location variable: ''. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )
        
        self.assert_error_behavior(
            lambda: get_location_from_env('random_string'),
            UserLocationError,
            "Invalid location variable: 'random_string'. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )
    
    def test_get_location_from_env_case_sensitivity(self):
        """Test that location names are case-sensitive."""
        self.assert_error_behavior(
            lambda: get_location_from_env('my_home'),
            UserLocationError,
            "Invalid location variable: 'my_home'. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )
        
        self.assert_error_behavior(
            lambda: get_location_from_env('My_Home'),
            UserLocationError,
            "Invalid location variable: 'My_Home'. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )
        
        self.assert_error_behavior(
            lambda: get_location_from_env('MY_home'),
            UserLocationError,
            "Invalid location variable: 'MY_home'. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )
    
    def test_get_location_from_env_with_whitespace(self):
        """Test that whitespace in location names is handled correctly."""
        self.assert_error_behavior(
            lambda: get_location_from_env(' MY_HOME '),
            UserLocationError,
            "Invalid location variable: ' MY_HOME '. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )
        
        self.assert_error_behavior(
            lambda: get_location_from_env('MY_HOME\n'),
            UserLocationError,
            "Invalid location variable: 'MY_HOME\n'. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )
    
    def test_get_location_from_env_environment_variable_with_whitespace(self):
        """Test that environment variables with whitespace are handled correctly."""
        with patch.dict(os.environ, {
            'MY_HOME': '  123 Home St, Mountain View, CA  ',
            'MY_LOCATION': '\n456 Current Ave, Palo Alto, CA\n',
            'MY_WORK': '789 Work Blvd, San Francisco, CA'
        }):
            # Should return the value as-is, including whitespace
            assert get_location_from_env('MY_HOME') == '  123 Home St, Mountain View, CA  '
            assert get_location_from_env('MY_LOCATION') == '\n456 Current Ave, Palo Alto, CA\n'
            assert get_location_from_env('MY_WORK') == '789 Work Blvd, San Francisco, CA'


class TestFindDirections(BaseTestCaseWithErrorHandler):
    """Test cases for the find_directions function."""
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_basic_directions(self, mock_parse_json, mock_get_gemini):
        """Test basic directions functionality."""
        # Mock the JSON response that would be returned by parse_json_from_gemini_response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?origin=Mountain+View,+CA&destination=San+Francisco,+CA",
            "travel_mode": "driving",
            "routes": [{
                "route_id": "route_1",
                "start_address": "Mountain View, CA",
                "end_address": "San Francisco, CA",
                "distance": "45 miles",
                "duration": "1 hour 15 minutes",
                "summary": "Route from Mountain View to San Francisco: 45 miles, 1 hour 15 minutes. Take US-101 North.",
                "url": "https://maps.google.com/directions?origin=Mountain+View,+CA&destination=San+Francisco,+CA",
                "mode": "driving",
                "steps": ["Head north on US-101", "Continue for 45 miles", "Arrive in San Francisco"]
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        result = find_directions(
            destination="San Francisco, CA",
            origin="Mountain View, CA"
        )
        
        assert isinstance(result, dict)
        assert "map_url" in result
        assert "travel_mode" in result
        assert "routes" in result
        assert len(result["routes"]) > 0
        
        route = result["routes"][0]
        assert route["start_address"] == "Mountain View, CA"
        assert route["end_address"] == "San Francisco, CA"
        assert route["mode"] == "driving"
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_directions_with_travel_mode(self, mock_parse_json, mock_get_gemini):
        """Test directions with specific travel mode."""
        # Mock the JSON response that would be returned by parse_json_from_gemini_response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?origin=Mountain+View,+CA&destination=San+Francisco,+CA&mode=walking",
            "travel_mode": "walking",
            "routes": [{
                "route_id": "route_1",
                "start_address": "Mountain View, CA",
                "end_address": "San Francisco, CA",
                "distance": "25 miles",
                "duration": "8 hours",
                "summary": "Walking route from Mountain View to San Francisco: 25 miles, 8 hours. Follow pedestrian paths.",
                "url": "https://maps.google.com/directions?origin=Mountain+View,+CA&destination=San+Francisco,+CA&mode=walking",
                "mode": "walking",
                "steps": ["Follow pedestrian paths", "Continue for 25 miles", "Arrive in San Francisco"]
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        result = find_directions(
            destination="San Francisco, CA",
            origin="Mountain View, CA",
            travel_mode="walking"
        )
        
        assert result["travel_mode"] == "walking"
        assert result["routes"][0]["mode"] == "walking"
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_directions_with_waypoints(self, mock_parse_json, mock_get_gemini):
        """Test directions with waypoints."""
        # Mock the JSON response that would be returned by parse_json_from_gemini_response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?origin=Mountain+View,+CA&destination=San+Francisco,+CA&waypoints=Palo+Alto,+CA|Redwood+City,+CA",
            "travel_mode": "driving",
            "routes": [{
                "route_id": "route_1",
                "start_address": "Mountain View, CA",
                "end_address": "San Francisco, CA",
                "distance": "50 miles",
                "duration": "1 hour 30 minutes",
                "summary": "Route from Mountain View to San Francisco via Palo Alto and Redwood City: 50 miles, 1 hour 30 minutes.",
                "url": "https://maps.google.com/directions?origin=Mountain+View,+CA&destination=San+Francisco,+CA&waypoints=Palo+Alto,+CA|Redwood+City,+CA",
                "mode": "driving",
                "steps": ["Head to Palo Alto", "Continue to Redwood City", "Arrive in San Francisco"]
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        result = find_directions(
            destination="San Francisco, CA",
            origin="Mountain View, CA",
            waypoints=["Palo Alto, CA", "Redwood City, CA"]
        )
        
        assert isinstance(result, dict)
        assert "routes" in result
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_directions_with_avoid(self, mock_parse_json, mock_get_gemini):
        """Test directions with avoid features."""
        # Mock the JSON response that would be returned by parse_json_from_gemini_response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?origin=Mountain+View,+CA&destination=San+Francisco,+CA&avoid=tolls|highways",
            "travel_mode": "driving",
            "routes": [{
                "route_id": "route_1",
                "start_address": "Mountain View, CA",
                "end_address": "San Francisco, CA",
                "distance": "55 miles",
                "duration": "1 hour 45 minutes",
                "summary": "Route avoiding tolls and highways: 55 miles, 1 hour 45 minutes via surface streets.",
                "url": "https://maps.google.com/directions?origin=Mountain+View,+CA&destination=San+Francisco,+CA&avoid=tolls|highways",
                "mode": "driving",
                "steps": ["Take surface streets", "Avoid toll roads", "Arrive in San Francisco"]
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        result = find_directions(
            destination="San Francisco, CA",
            origin="Mountain View, CA",
            avoid=["tolls", "highways"]
        )
        
        assert isinstance(result, dict)
        assert "routes" in result
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_directions_with_time_constraints(self, mock_parse_json, mock_get_gemini):
        """Test directions with departure time."""
        # Mock the JSON response that would be returned by parse_json_from_gemini_response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?origin=Mountain+View,+CA&destination=San+Francisco,+CA&departure_time=1640995200",
            "travel_mode": "driving",
            "routes": [{
                "route_id": "route_1",
                "start_address": "Mountain View, CA",
                "end_address": "San Francisco, CA",
                "distance": "45 miles",
                "duration": "1 hour 20 minutes",
                "summary": "Route departing at specified time: 45 miles, 1 hour 20 minutes with traffic conditions.",
                "url": "https://maps.google.com/directions?origin=Mountain+View,+CA&destination=San+Francisco,+CA&departure_time=1640995200",
                "mode": "driving",
                "steps": ["Depart at specified time", "Consider traffic conditions", "Arrive in San Francisco"]
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        result = find_directions(
            destination="San Francisco, CA",
            origin="Mountain View, CA",
            departure_time=1640995200  # Jan 1, 2022 00:00:00 UTC
        )
        
        assert isinstance(result, dict)
        assert "routes" in result
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_transit_directions_with_fare(self, mock_parse_json, mock_get_gemini):
        """Test transit directions that should include fare information."""
        # Mock the JSON response that would be returned by parse_json_from_gemini_response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?origin=Mountain+View,+CA&destination=San+Francisco,+CA&mode=transit",
            "travel_mode": "transit",
            "routes": [{
                "route_id": "route_1",
                "start_address": "Mountain View, CA",
                "end_address": "San Francisco, CA",
                "distance": "45 miles",
                "duration": "1 hour 30 minutes",
                "summary": "Transit route: Take Caltrain from Mountain View to San Francisco. Fare: $12.50 USD.",
                "url": "https://maps.google.com/directions?origin=Mountain+View,+CA&destination=San+Francisco,+CA&mode=transit",
                "mode": "transit",
                "steps": ["Take Caltrain from Mountain View", "Transfer if needed", "Arrive in San Francisco"],
                "fare": {
                    "currency": "USD",
                    "value": 12.50
                }
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        result = find_directions(
            destination="San Francisco, CA",
            origin="Mountain View, CA",
            travel_mode="transit"
        )
        
        assert result["travel_mode"] == "transit"
        route = result["routes"][0]
        assert "fare" in route
        assert route["fare"]["currency"] == "USD"
        assert route["fare"]["value"] > 0
    
    def test_invalid_travel_mode(self):
        """Test that invalid travel mode raises ValueError."""
        self.assert_error_behavior(
            lambda: find_directions(
                destination="San Francisco, CA",
                travel_mode="invalid_mode"
            ),
            ValueError,
            "Invalid travel_mode"
        )
    
    def test_invalid_avoid_features(self):
        """Test that invalid avoid features raise ValueError."""
        self.assert_error_behavior(
            lambda: find_directions(
                destination="San Francisco, CA",
                avoid=["invalid_feature"]
            ),
            ValueError,
            "Invalid avoid feature"
        )
    
    def test_both_departure_and_arrival_time(self):
        """Test that specifying both departure and arrival time raises ValueError."""
        self.assert_error_behavior(
            lambda: find_directions(
                destination="San Francisco, CA",
                departure_time=1640995200,
                arrival_time=1640998800
            ),
            ValueError,
            "Cannot specify both departure_time and arrival_time"
        )

    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_find_directions_with_location_bias(self, mock_parse_json, mock_get_gemini):
        """Test find_directions with location bias parameters."""
        # Mock the JSON response that would be returned by parse_json_from_gemini_response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?origin=123+Home+St,+Mountain+View,+CA&destination=San+Francisco,+CA",
            "travel_mode": "driving",
            "routes": [{
                "route_id": "route_1",
                "start_address": "123 Home St, Mountain View, CA",
                "end_address": "San Francisco, CA",
                "distance": "45 miles",
                "duration": "1 hour 15 minutes",
                "summary": "Route from home to San Francisco: 45 miles, 1 hour 15 minutes.",
                "url": "https://maps.google.com/directions?origin=123+Home+St,+Mountain+View,+CA&destination=San+Francisco,+CA",
                "mode": "driving",
                "steps": ["Start from home", "Take US-101 North", "Arrive in San Francisco"]
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        # Test with origin_location_bias as UserLocation enum
        with patch.dict(os.environ, {'MY_HOME': '123 Home St, Mountain View, CA'}):
            result = find_directions(
                destination="San Francisco, CA",
                origin_location_bias="MY_HOME"
            )
            
            assert isinstance(result, dict)
            assert "routes" in result
            route = result["routes"][0]
            assert route["start_address"] == "123 Home St, Mountain View, CA"
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_find_directions_with_coordinate_location_bias(self, mock_parse_json, mock_get_gemini):
        """Test find_directions with coordinate-based location bias."""
        # Mock the JSON response that would be returned by parse_json_from_gemini_response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?origin=37.7749,-122.4194&destination=San+Francisco,+CA",
            "travel_mode": "driving",
            "routes": [{
                "route_id": "route_1",
                "start_address": "37.7749, -122.4194",
                "end_address": "San Francisco, CA",
                "distance": "2 miles",
                "duration": "10 minutes",
                "summary": "Route from coordinates to San Francisco: 2 miles, 10 minutes.",
                "url": "https://maps.google.com/directions?origin=37.7749,-122.4194&destination=San+Francisco,+CA",
                "mode": "driving",
                "steps": ["Start from coordinates", "Follow local streets", "Arrive in San Francisco"]
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        # Test with coordinate-based location bias
        result = find_directions(
            destination="San Francisco, CA",
            origin_location_bias={"latitude": 37.7749, "longitude": -122.4194}
        )
        
        assert isinstance(result, dict)
        assert "routes" in result
        route = result["routes"][0]
        assert "37.7749" in route["start_address"]
        assert "-122.4194" in route["start_address"]
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    @patch.dict(os.environ, {}, clear=True)
    def test_find_directions_without_origin_no_my_location(self, mock_parse_json, mock_get_gemini):
        """Test find_directions with no origin and no MY_LOCATION environment variable."""
        # Mock the JSON response that would be returned by parse_json_from_gemini_response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?destination=San+Francisco,+CA",
            "travel_mode": "driving",
            "routes": [{
                "route_id": "route_1",
                "start_address": "Current Location",
                "end_address": "San Francisco, CA",
                "distance": "45 miles",
                "duration": "1 hour 15 minutes",
                "summary": "Route to San Francisco: 45 miles, 1 hour 15 minutes.",
                "url": "https://maps.google.com/directions?destination=San+Francisco,+CA",
                "mode": "driving",
                "steps": ["Head toward San Francisco", "Take US-101 North", "Arrive in San Francisco"]
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        # Call find_directions with only destination (no origin, no MY_LOCATION env var)
        result = find_directions(destination="San Francisco, CA")
        
        assert isinstance(result, dict)
        assert "map_url" in result
        assert "travel_mode" in result
        assert "routes" in result
        assert len(result["routes"]) > 0
        
        # Verify the Gemini query was constructed correctly without origin
        call_args = mock_get_gemini.call_args[0][0]
        assert "Find directions to San Francisco, CA" in call_args
        # Should NOT have "from X to Y" format when origin is None
        assert call_args.startswith("Find directions to")
        
        route = result["routes"][0]
        assert route["end_address"] == "San Francisco, CA"
        assert route["mode"] == "driving"
    
    @patch('google_maps_live.directions.get_location_from_env')
    @patch('google_maps_live.directions.print_log')
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_find_directions_handles_undefined_location_error(self, mock_parse_json, mock_get_gemini, mock_print_log, mock_get_location):
        """Test that find_directions catches and handles UndefinedLocationError gracefully."""
        # Setup mock to raise UndefinedLocationError when trying to get MY_LOCATION
        mock_get_location.side_effect = UndefinedLocationError("Environment variable for 'MY_LOCATION' is not defined.")
        
        # Mock the JSON response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?destination=San+Francisco,+CA",
            "travel_mode": "driving",
            "routes": [{
                "route_id": "route_1",
                "start_address": "Current Location",
                "end_address": "San Francisco, CA",
                "distance": "45 miles",
                "duration": "1 hour 15 minutes",
                "summary": "Route to San Francisco: 45 miles, 1 hour 15 minutes.",
                "url": "https://maps.google.com/directions?destination=San+Francisco,+CA",
                "mode": "driving",
                "steps": ["Head toward San Francisco", "Take US-101 North", "Arrive in San Francisco"]
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        # Call find_directions without origin - this should trigger the exception handling
        result = find_directions(destination="San Francisco, CA")
        
        # Verify that get_location_from_env was called (which raised the exception)
        mock_get_location.assert_called_once_with(UserLocation.MY_LOCATION.value)
        
        # Verify that print_log was called with the expected message
        mock_print_log.assert_any_call("MY_LOCATION environment variable is not set.")
        
        # Verify that the function continued execution successfully (didn't re-raise)
        assert isinstance(result, dict)
        assert "routes" in result
        
        # Verify the query was formatted without origin (because resolved_origin = None)
        call_args = mock_get_gemini.call_args[0][0]
        assert "Find directions to San Francisco, CA" in call_args
        assert call_args.startswith("Find directions to")

class TestNavigate(BaseTestCaseWithErrorHandler):
    """Test cases for the navigate function."""
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_basic_navigation(self, mock_parse_json, mock_get_gemini):
        """Test basic navigation functionality."""
        # Mock the JSON response that would be returned by parse_json_from_gemini_response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?destination=San+Francisco,+CA",
            "travel_mode": "driving",
            "routes": [{
                "route_id": "route_1",
                "start_address": "Current Location",
                "end_address": "San Francisco, CA",
                "distance": "45 miles",
                "duration": "1 hour 15 minutes",
                "summary": "Navigation to San Francisco from current location: 45 miles, 1 hour 15 minutes.",
                "url": "https://maps.google.com/directions?destination=San+Francisco,+CA",
                "mode": "driving",
                "steps": ["Start from current location", "Follow GPS directions", "Arrive in San Francisco"]
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        result = navigate(destination="San Francisco, CA")
        
        assert isinstance(result, dict)
        assert "map_url" in result
        assert "travel_mode" in result
        assert "routes" in result
        assert len(result["routes"]) > 0
        
        route = result["routes"][0]
        assert route["start_address"] == "Current Location"
        assert route["end_address"] == "San Francisco, CA"
        assert route["mode"] == "driving"
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_navigation_with_travel_mode(self, mock_parse_json, mock_get_gemini):
        """Test navigation with specific travel mode."""
        # Mock the JSON response that would be returned by parse_json_from_gemini_response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?destination=San+Francisco,+CA&mode=bicycling",
            "travel_mode": "bicycling",
            "routes": [{
                "route_id": "route_1",
                "start_address": "Current Location",
                "end_address": "San Francisco, CA",
                "distance": "25 miles",
                "duration": "2 hours 30 minutes",
                "summary": "Bicycling route to San Francisco: 25 miles, 2 hours 30 minutes via bike paths.",
                "url": "https://maps.google.com/directions?destination=San+Francisco,+CA&mode=bicycling",
                "mode": "bicycling",
                "steps": ["Follow bike paths", "Use dedicated lanes", "Arrive in San Francisco"]
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        result = navigate(
            destination="San Francisco, CA",
            travel_mode="bicycling"
        )
        
        assert result["travel_mode"] == "bicycling"
        assert result["routes"][0]["mode"] == "bicycling"
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_navigation_with_waypoints(self, mock_parse_json, mock_get_gemini):
        """Test navigation with waypoints."""
        # Mock the JSON response that would be returned by parse_json_from_gemini_response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?destination=San+Francisco,+CA&waypoints=Palo+Alto,+CA",
            "travel_mode": "driving",
            "routes": [{
                "route_id": "route_1",
                "start_address": "Current Location",
                "end_address": "San Francisco, CA",
                "distance": "50 miles",
                "duration": "1 hour 30 minutes",
                "summary": "Route to San Francisco via Palo Alto: 50 miles, 1 hour 30 minutes.",
                "url": "https://maps.google.com/directions?destination=San+Francisco,+CA&waypoints=Palo+Alto,+CA",
                "mode": "driving",
                "steps": ["Head to Palo Alto", "Continue to San Francisco", "Arrive at destination"]
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        result = navigate(
            destination="San Francisco, CA",
            waypoints=["Palo Alto, CA"]
        )
        
        assert isinstance(result, dict)
        assert "routes" in result
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_navigation_with_avoid(self, mock_parse_json, mock_get_gemini):
        """Test navigation with avoid features."""
        # Mock the JSON response that would be returned by parse_json_from_gemini_response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?destination=San+Francisco,+CA&avoid=ferries",
            "travel_mode": "driving",
            "routes": [{
                "route_id": "route_1",
                "start_address": "Current Location",
                "end_address": "San Francisco, CA",
                "distance": "45 miles",
                "duration": "1 hour 20 minutes",
                "summary": "Route avoiding ferries: 45 miles, 1 hour 20 minutes via bridges.",
                "url": "https://maps.google.com/directions?destination=San+Francisco,+CA&avoid=ferries",
                "mode": "driving",
                "steps": ["Use bridges instead of ferries", "Follow route", "Arrive in San Francisco"]
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        result = navigate(
            destination="San Francisco, CA",
            avoid=["ferries"]
        )
        
        assert isinstance(result, dict)
        assert "routes" in result
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_transit_navigation_with_fare(self, mock_parse_json, mock_get_gemini):
        """Test transit navigation that should include fare information."""
        # Mock the JSON response that would be returned by parse_json_from_gemini_response
        mock_json_response = {
            "map_url": "https://maps.google.com/directions?destination=San+Francisco,+CA&mode=bus",
            "travel_mode": "bus",
            "routes": [{
                "route_id": "route_1",
                "start_address": "Current Location",
                "end_address": "San Francisco, CA",
                "distance": "45 miles",
                "duration": "2 hours",
                "summary": "Bus route to San Francisco: Take bus 22. Fare: $8.50 USD.",
                "url": "https://maps.google.com/directions?destination=San+Francisco,+CA&mode=bus",
                "mode": "bus",
                "steps": ["Take bus 22", "Transfer if needed", "Arrive in San Francisco"],
                "fare": {
                    "currency": "USD",
                    "value": 8.50
                }
            }]
        }
        mock_parse_json.return_value = mock_json_response
        mock_get_gemini.return_value = "mock response"
        
        result = navigate(
            destination="San Francisco, CA",
            travel_mode="bus"
        )
        
        assert result["travel_mode"] == "bus"
        route = result["routes"][0]
        assert "fare" in route
        assert route["fare"]["currency"] == "USD"
        assert route["fare"]["value"] > 0
    
    def test_invalid_travel_mode(self):
        """Test that invalid travel mode raises ValueError."""
        self.assert_error_behavior(
            lambda: navigate(
                destination="San Francisco, CA",
                travel_mode="invalid_mode"
            ),
            ValueError,
            "Invalid travel_mode"
        )
    
    def test_invalid_avoid_features(self):
        """Test that invalid avoid features raise ValueError."""
        self.assert_error_behavior(
            lambda: navigate(
                destination="San Francisco, CA",
                avoid=["invalid_feature"]
            ),
            ValueError,
            "Invalid avoid feature"
        ) 

    @patch('google_maps_live.directions.get_model_from_gemini_response')
    def test_navigate_with_location_bias(self, mock_get_model):
        """Test navigate with location bias parameters."""
        # Mock the DirectionsSummary model response
        mock_directions = DirectionsSummary(
            map_url="https://maps.google.com/directions?destination=San+Francisco,+CA&origin=456+Work+Ave,+Palo+Alto,+CA",
            travel_mode="driving",
            routes=[{
                "route_id": "route_1",
                "start_address": "456 Work Ave, Palo Alto, CA",
                "end_address": "San Francisco, CA",
                "distance": "35 miles",
                "duration": "45 minutes",
                "summary": "Navigation from work to San Francisco: 35 miles, 45 minutes.",
                "url": "https://maps.google.com/directions?destination=San+Francisco,+CA&origin=456+Work+Ave,+Palo+Alto,+CA",
                "mode": "driving",
                "steps": ["Start from work", "Take US-101 North", "Arrive in San Francisco"]
            }]
        )
        mock_get_model.return_value = mock_directions
        
        # Test with origin_location_bias as UserLocation enum
        with patch.dict(os.environ, {'MY_WORK': '456 Work Ave, Palo Alto, CA'}):
            result = navigate(
                destination="San Francisco, CA",
                origin_location_bias="MY_WORK"
            )
            
            assert isinstance(result, dict)
            assert "routes" in result
            route = result["routes"][0]
            assert route["start_address"] == "456 Work Ave, Palo Alto, CA"
    
    @patch('google_maps_live.directions.get_model_from_gemini_response')
    def test_navigate_with_coordinate_location_bias(self, mock_get_model):
        """Test navigate with coordinate-based location bias."""
        # Mock the DirectionsSummary model response
        mock_directions = DirectionsSummary(
            map_url="https://maps.google.com/directions?destination=San+Francisco,+CA&origin=37.4419,-122.1430",
            travel_mode="driving",
            routes=[{
                "route_id": "route_1",
                "start_address": "37.4419, -122.1430",
                "end_address": "San Francisco, CA",
                "distance": "25 miles",
                "duration": "35 minutes",
                "summary": "Navigation from coordinates to San Francisco: 25 miles, 35 minutes.",
                "url": "https://maps.google.com/directions?destination=San+Francisco,+CA&origin=37.4419,-122.1430",
                "mode": "driving",
                "steps": ["Start from coordinates", "Take local roads", "Arrive in San Francisco"]
            }]
        )
        mock_get_model.return_value = mock_directions
        
        # Test with coordinate-based location bias
        result = navigate(
            destination="San Francisco, CA",
            origin_location_bias={"latitude": 37.4419, "longitude": -122.1430}
        )
        
        assert isinstance(result, dict)
        assert "routes" in result
        route = result["routes"][0]
        assert "37.4419" in route["start_address"]
        assert "-122.1430" in route["start_address"]
    
    @patch('google_maps_live.directions.get_model_from_gemini_response')
    def test_navigate_with_destination_location_bias(self, mock_get_model):
        """Test navigate with destination location bias."""
        # Mock the DirectionsSummary model response
        mock_directions = DirectionsSummary(
            map_url="https://maps.google.com/directions?destination=789+Work+Blvd,+San+Francisco,+CA",
            travel_mode="driving",
            routes=[{
                "route_id": "route_1",
                "start_address": "Current Location",
                "end_address": "789 Work Blvd, San Francisco, CA",
                "distance": "15 miles",
                "duration": "25 minutes",
                "summary": "Navigation to work address: 15 miles, 25 minutes.",
                "url": "https://maps.google.com/directions?destination=789+Work+Blvd,+San+Francisco,+CA",
                "mode": "driving",
                "steps": ["Start from current location", "Follow GPS directions", "Arrive at work"]
            }]
        )
        mock_get_model.return_value = mock_directions
        
        # Test with destination_location_bias as UserLocation enum
        with patch.dict(os.environ, {'MY_WORK': '789 Work Blvd, San Francisco, CA'}):
            result = navigate(
                destination="San Francisco, CA",
                destination_location_bias="MY_WORK"
            )
            
            assert isinstance(result, dict)
            assert "routes" in result
            route = result["routes"][0]
            assert route["end_address"] == "789 Work Blvd, San Francisco, CA" 