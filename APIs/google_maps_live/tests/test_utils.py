"""
Test suite for utility functions in the Google Maps Live API.
"""

import unittest
import os
import json
import time
from unittest.mock import patch, MagicMock, Mock
from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_maps_live.SimulationEngine.db import DB, save_state, load_state
from google_maps_live.SimulationEngine.models import TravelMode, UserLocation, DirectionsSummary
from google_maps_live.SimulationEngine.custom_errors import ParseError, UserLocationError, UndefinedLocationError
from google_maps_live.SimulationEngine import utils


class TestUtilsHelpers(BaseTestCaseWithErrorHandler):
    
    def setUp(self):
        """Set up a clean test database before each test."""
        # Store original DB state
        self.original_db = DB.copy()
        # Clear DB for clean testing
        DB.clear()
        DB.update({
            "recent_searches": {},
            "user_locations": {},
            "search_history": {}
        })

    def tearDown(self):
        """Reset the database after each test."""
        # Restore original DB state
        DB.clear()
        DB.update(self.original_db)

    def test_get_location_from_env_valid_names(self):
        """Test that valid UserLocation names work correctly."""
        # Test with environment variables set
        with patch.dict(os.environ, {
            'MY_HOME': '123 Home St, Mountain View, CA',
            'MY_LOCATION': '456 Current Ave, Palo Alto, CA',
            'MY_WORK': '789 Work Blvd, San Francisco, CA'
        }):
            assert utils.get_location_from_env('MY_HOME') == '123 Home St, Mountain View, CA'
            assert utils.get_location_from_env('MY_LOCATION') == '456 Current Ave, Palo Alto, CA'
            assert utils.get_location_from_env('MY_WORK') == '789 Work Blvd, San Francisco, CA'

    def test_get_location_from_env_valid_values(self):
        """Test that valid UserLocation enum values work correctly."""
        # Test with environment variables set
        with patch.dict(os.environ, {
            'MY_HOME': '123 Home St, Mountain View, CA',
            'MY_LOCATION': '456 Current Ave, Palo Alto, CA',
            'MY_WORK': '789 Work Blvd, San Francisco, CA'
        }):
            assert utils.get_location_from_env(UserLocation.MY_HOME) == '123 Home St, Mountain View, CA'
            assert utils.get_location_from_env(UserLocation.MY_LOCATION) == '456 Current Ave, Palo Alto, CA'
            assert utils.get_location_from_env(UserLocation.MY_WORK) == '789 Work Blvd, San Francisco, CA'

    def test_get_location_from_env_missing_environment_variable(self):
        """Test that missing environment variables raise UndefinedLocationError."""
        # Test with no environment variables set
        with patch.dict(os.environ, {}, clear=True):
            self.assert_error_behavior(
                lambda: utils.get_location_from_env('MY_HOME'),
                UndefinedLocationError,
                "Environment variable for 'MY_HOME' is not defined."
            )
            
            self.assert_error_behavior(
                lambda: utils.get_location_from_env('MY_LOCATION'),
                UndefinedLocationError,
                "Environment variable for 'MY_LOCATION' is not defined."
            )
            
            self.assert_error_behavior(
                lambda: utils.get_location_from_env('MY_WORK'),
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
                lambda: utils.get_location_from_env('MY_HOME'),
                UndefinedLocationError,
                "Environment variable for 'MY_HOME' is not defined."
            )
            
            self.assert_error_behavior(
                lambda: utils.get_location_from_env('MY_LOCATION'),
                UndefinedLocationError,
                "Environment variable for 'MY_LOCATION' is not defined."
            )
            
            self.assert_error_behavior(
                lambda: utils.get_location_from_env('MY_WORK'),
                UndefinedLocationError,
                "Environment variable for 'MY_WORK' is not defined."
            )

    def test_get_location_from_env_invalid_location_name(self):
        """Test that invalid location names raise UserLocationError."""
        self.assert_error_behavior(
            lambda: utils.get_location_from_env('INVALID_LOCATION'),
            UserLocationError,
            "Invalid location variable: 'INVALID_LOCATION'. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )
        
        self.assert_error_behavior(
            lambda: utils.get_location_from_env(''),
            UserLocationError,
            "Invalid location variable: ''. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )
        
        self.assert_error_behavior(
            lambda: utils.get_location_from_env('random_string'),
            UserLocationError,
            "Invalid location variable: 'random_string'. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )

    def test_get_location_from_env_case_sensitivity(self):
        """Test that location names are case-sensitive."""
        self.assert_error_behavior(
            lambda: utils.get_location_from_env('my_home'),
            UserLocationError,
            "Invalid location variable: 'my_home'. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )
        
        self.assert_error_behavior(
            lambda: utils.get_location_from_env('My_Home'),
            UserLocationError,
            "Invalid location variable: 'My_Home'. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )
        
        self.assert_error_behavior(
            lambda: utils.get_location_from_env('MY_home'),
            UserLocationError,
            "Invalid location variable: 'MY_home'. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )

    def test_get_location_from_env_with_whitespace(self):
        """Test that whitespace in location names is handled correctly."""
        self.assert_error_behavior(
            lambda: utils.get_location_from_env(' MY_HOME '),
            UserLocationError,
            "Invalid location variable: ' MY_HOME '. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        )
        
        self.assert_error_behavior(
            lambda: utils.get_location_from_env('MY_HOME\n'),
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
            assert utils.get_location_from_env('MY_HOME') == '  123 Home St, Mountain View, CA  '
            assert utils.get_location_from_env('MY_LOCATION') == '\n456 Current Ave, Palo Alto, CA\n'
            assert utils.get_location_from_env('MY_WORK') == '789 Work Blvd, San Francisco, CA'


class TestGeminiAPIUtils(BaseTestCaseWithErrorHandler):
    """Test cases for Gemini API utility functions."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Store original environment variables
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment variables."""
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch('google_maps_live.SimulationEngine.utils.requests.post')
    def test_get_gemini_response_success(self, mock_post):
        """Test successful Gemini API response."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            'candidates': [{
                'content': {
                    'parts': [{'text': 'Mock Gemini response'}]
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Set required environment variables
        os.environ['GOOGLE_API_KEY'] = 'test_api_key'
        os.environ['LIVE_API_URL'] = 'https://api.example.com/v1/models/generateContent?'
        
        response = utils.get_gemini_response("test query")
        
        self.assertEqual(response, 'Mock Gemini response')
        mock_post.assert_called_once()

    @patch('google_maps_live.SimulationEngine.utils.requests.post')
    def test_get_gemini_response_missing_api_key(self, mock_post):
        """Test that missing API key raises EnvironmentError."""
        # Don't set GOOGLE_API_KEY
        os.environ['LIVE_API_URL'] = 'https://api.example.com/v1/models/generateContent?'
        
        self.assert_error_behavior(
            lambda: utils.get_gemini_response("test query"),
            EnvironmentError,
            "Google API Key not found. Please create a .env file in the project root with GOOGLE_API_KEY or GEMINI_API_KEY, or set it as an environment variable."
        )

    @patch('google_maps_live.SimulationEngine.utils.requests.post')
    def test_get_gemini_response_missing_live_api_url(self, mock_post):
        """Test that missing LIVE_API_URL raises EnvironmentError."""
        # Don't set LIVE_API_URL
        os.environ['GOOGLE_API_KEY'] = 'test_api_key'
        
        self.assert_error_behavior(
            lambda: utils.get_gemini_response("test query"),
            EnvironmentError,
            "Live API URL not found. Please create a .env file in the project root with LIVE_API_URL, or set it as an environment variable."
        )

    @patch('google_maps_live.SimulationEngine.utils.requests.post')
    def test_get_gemini_response_http_error(self, mock_post):
        """Test that HTTP errors are properly handled."""
        # Mock HTTP error
        mock_post.side_effect = Exception("HTTP Error")
        
        os.environ['GOOGLE_API_KEY'] = 'test_api_key'
        os.environ['LIVE_API_URL'] = 'https://api.example.com/v1/models/generateContent?'
        
        self.assert_error_behavior(
            lambda: utils.get_gemini_response("test query"),
            Exception,
            "HTTP Error"
        )

    def test_parse_json_from_gemini_response_valid_object(self):
        """Test parsing valid JSON object from Gemini response."""
        gemini_response = 'Here is the response: {"key": "value", "number": 42} and more text'
        
        result = utils.parse_json_from_gemini_response(gemini_response)
        
        self.assertEqual(result, {"key": "value", "number": 42})

    def test_parse_json_from_gemini_response_valid_array(self):
        """Test parsing valid JSON array from Gemini response."""
        gemini_response = 'Response: [{"item": "1"}, {"item": "2"}] with extra text'
        
        result = utils.parse_json_from_gemini_response(gemini_response)
        
        self.assertEqual(result, [{"item": "1"}, {"item": "2"}])

    def test_parse_json_from_gemini_response_object_first(self):
        """Test that object is parsed when it comes before array."""
        gemini_response = '{"key": "value"} [1, 2, 3]'
        
        result = utils.parse_json_from_gemini_response(gemini_response)
        
        self.assertEqual(result, {"key": "value"})

    def test_parse_json_from_gemini_response_array_first(self):
        """Test that array is parsed when it comes before object."""
        gemini_response = '[1, 2, 3] {"key": "value"}'
        
        result = utils.parse_json_from_gemini_response(gemini_response)
        
        self.assertEqual(result, [1, 2, 3])

    def test_parse_json_from_gemini_response_no_json(self):
        """Test that ParseError is raised when no JSON is found."""
        gemini_response = 'No JSON content here, just plain text'
        
        self.assert_error_behavior(
            lambda: utils.parse_json_from_gemini_response(gemini_response),
            ParseError,
            "No JSON object or array found in Gemini response."
        )

    def test_parse_json_from_gemini_response_malformed_json(self):
        """Test that ParseError is raised for malformed JSON."""
        gemini_response = '{"key": "value" - missing closing brace'
        
        self.assert_error_behavior(
            lambda: utils.parse_json_from_gemini_response(gemini_response),
            ParseError,
            "Malformed JSON in Gemini response."
        )

    def test_parse_json_from_gemini_response_invalid_json_content(self):
        """Test that ParseError is raised for invalid JSON content."""
        gemini_response = '{"key": "value", "invalid": "quotes missing}'
        
        self.assert_error_behavior(
            lambda: utils.parse_json_from_gemini_response(gemini_response),
            ParseError,
            "Error decoding JSON from Gemini response: Unterminated string starting at: line 1 column 29 (char 28)"
        )

    def test_parse_json_from_gemini_response_nested_structures(self):
        """Test parsing nested JSON structures."""
        gemini_response = '''
        Here is the complex response:
        {
            "nested": {
                "array": [1, 2, 3],
                "object": {"key": "value"}
            },
            "simple": "string"
        }
        '''
        
        result = utils.parse_json_from_gemini_response(gemini_response)
        
        expected = {
            "nested": {
                "array": [1, 2, 3],
                "object": {"key": "value"}
            },
            "simple": "string"
        }
        self.assertEqual(result, expected)


class TestModelValidationUtils(BaseTestCaseWithErrorHandler):
    """Test cases for Pydantic model validation utilities."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Store original environment variables
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Restore original environment variables."""
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_get_model_from_gemini_response_success(self, mock_parse, mock_gemini):
        """Test successful model validation from Gemini response."""
        # Mock successful responses
        mock_gemini.return_value = "Mock response"
        mock_parse.return_value = {
            "map_url": "https://maps.google.com",
            "travel_mode": "driving",
            "routes": []
        }
        
        result = utils.get_model_from_gemini_response("test query", DirectionsSummary)
        
        self.assertIsInstance(result, DirectionsSummary)
        self.assertEqual(result.map_url, "https://maps.google.com")
        self.assertEqual(result.travel_mode, "driving")

    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_get_model_from_gemini_response_with_retries(self, mock_parse, mock_gemini):
        """Test that model validation retries on failure."""
        # Mock first attempt fails, second succeeds
        mock_gemini.return_value = "Mock response"
        mock_parse.side_effect = [
            ParseError("First attempt fails"),
            {"map_url": "https://maps.google.com", "travel_mode": "driving", "routes": []}
        ]
        
        result = utils.get_model_from_gemini_response("test query", DirectionsSummary, max_retries=1)
        
        self.assertIsInstance(result, DirectionsSummary)
        self.assertEqual(mock_parse.call_count, 2)

    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_get_model_from_gemini_response_max_retries_exceeded(self, mock_parse, mock_gemini):
        """Test that NotImplementedError is raised when max retries are exceeded."""
        # Mock all attempts fail
        mock_gemini.return_value = "Mock response"
        mock_parse.side_effect = ParseError("All attempts fail")
        
        self.assert_error_behavior(
            lambda: utils.get_model_from_gemini_response("test query", DirectionsSummary, max_retries=2),
            NotImplementedError,
            "Mock response"
        )

    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_get_model_from_gemini_response_custom_retry_delay(self, mock_parse, mock_gemini):
        """Test that custom retry delay is respected."""
        # Mock first attempt fails, second succeeds
        mock_gemini.return_value = "Mock response"
        mock_parse.side_effect = [
            ParseError("First attempt fails"),
            {"map_url": "https://maps.google.com", "travel_mode": "driving", "routes": []}
        ]
        
        start_time = time.time()
        result = utils.get_model_from_gemini_response("test query", DirectionsSummary, max_retries=1, retry_delay=0.1)
        end_time = time.time()
        
        self.assertIsInstance(result, DirectionsSummary)
        # Should have at least 0.1 second delay
        self.assertGreaterEqual(end_time - start_time, 0.1)


class TestRecentSearchUtils(BaseTestCaseWithErrorHandler):
    """Test cases for recent search utility functions."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Clear any existing recent searches
        DB["recent_searches"] = {}

    def tearDown(self):
        """Clean up after each test."""
        # Clear any existing recent searches
        DB["recent_searches"] = {}

    def test_add_recent_search_new_endpoint(self):
        """Test adding a recent search for a new endpoint."""
        parameters = {"destination": "San Francisco, CA", "origin": "Mountain View, CA"}
        result = {"map_url": "https://maps.google.com", "travel_mode": "driving"}
        
        utils.add_recent_search("find_directions", parameters, result)
        
        recent_searches = utils.get_recent_searches("find_directions")
        assert len(recent_searches) == 1
        assert recent_searches[0]["parameters"] == parameters
        assert recent_searches[0]["result"] == result

    def test_add_recent_search_existing_endpoint(self):
        """Test adding a recent search to an existing endpoint."""
        # Add first search
        parameters1 = {"destination": "San Francisco, CA", "origin": "Mountain View, CA"}
        result1 = {"map_url": "https://maps.google.com", "travel_mode": "driving"}
        utils.add_recent_search("find_directions", parameters1, result1)
        
        # Add second search
        parameters2 = {"destination": "Palo Alto, CA", "origin": "San Jose, CA"}
        result2 = {"map_url": "https://maps.google.com", "travel_mode": "walking"}
        utils.add_recent_search("find_directions", parameters2, result2)
        
        recent_searches = utils.get_recent_searches("find_directions")
        assert len(recent_searches) == 2
        assert recent_searches[0]["parameters"] == parameters2  # Most recent first
        assert recent_searches[1]["parameters"] == parameters1

    def test_add_recent_search_allows_duplicates(self):
        """Test that duplicate searches are allowed and both are present."""
        parameters = {"destination": "San Francisco, CA", "origin": "Mountain View, CA"}
        result = {"map_url": "https://maps.google.com", "travel_mode": "driving"}
        
        # Add same search twice
        utils.add_recent_search("find_directions", parameters, result)
        utils.add_recent_search("find_directions", parameters, result)
        
        recent_searches = utils.get_recent_searches("find_directions")
        assert len(recent_searches) == 2  # Both entries should be present
        assert recent_searches[0]["parameters"] == parameters
        assert recent_searches[1]["parameters"] == parameters

    def test_add_recent_search_max_limit(self):
        """Test that recent searches are limited to 50 entries."""
        # Add 55 searches
        for i in range(55):
            parameters = {"destination": f"Location {i}", "origin": f"Origin {i}"}
            result = {"map_url": f"https://maps.google.com/{i}", "travel_mode": "driving"}
            utils.add_recent_search("find_directions", parameters, result)
        
        recent_searches = utils.get_recent_searches("find_directions")
        assert len(recent_searches) <= 50  # Should be limited to 50
        assert recent_searches[0]["parameters"]["destination"] == "Location 54"  # Most recent first

    def test_get_recent_searches_empty_endpoint(self):
        """Test getting recent searches for an endpoint with no history."""
        recent_searches = utils.get_recent_searches("nonexistent_endpoint")
        assert recent_searches == []

    def test_get_recent_searches_with_max_results(self):
        """Test getting recent searches with max_results limit."""
        # Add 10 searches
        for i in range(10):
            parameters = {"destination": f"Location {i}", "origin": f"Origin {i}"}
            result = {"map_url": f"https://maps.google.com/{i}", "travel_mode": "driving"}
            utils.add_recent_search("find_directions", parameters, result)
        
        # Get only 3 most recent
        recent_searches = utils.get_recent_searches("find_directions", max_results=3)
        assert len(recent_searches) == 3
        assert recent_searches[0]["parameters"]["destination"] == "Location 9"  # Most recent
        assert recent_searches[2]["parameters"]["destination"] == "Location 7"  # Third most recent

    def test_get_recent_searches_default_max_results(self):
        """Test that default max_results is 5."""
        # Add 10 searches
        for i in range(10):
            parameters = {"destination": f"Location {i}", "origin": f"Origin {i}"}
            result = {"map_url": f"https://maps.google.com/{i}", "travel_mode": "driving"}
            utils.add_recent_search("find_directions", parameters, result)
        
        recent_searches = utils.get_recent_searches("find_directions")
        assert len(recent_searches) == 5  # Default should be 5

    def test_multiple_endpoints_separate_storage(self):
        """Test that different endpoints store recent searches separately."""
        # Add searches to both endpoints
        utils.add_recent_search("find_directions", {"dest": "SF"}, {"result": "directions"})
        utils.add_recent_search("navigate", {"dest": "PA"}, {"result": "navigation"})
        
        # Check that searches are stored separately
        find_directions_searches = utils.get_recent_searches("find_directions")
        navigate_searches = utils.get_recent_searches("navigate")
        
        assert len(find_directions_searches) == 1
        assert len(navigate_searches) == 1
        assert find_directions_searches[0]["parameters"]["dest"] == "SF"
        assert navigate_searches[0]["parameters"]["dest"] == "PA"


if __name__ == '__main__':
    unittest.main()
