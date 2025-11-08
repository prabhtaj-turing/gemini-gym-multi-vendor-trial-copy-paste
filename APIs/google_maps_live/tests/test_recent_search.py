# google_maps_live/tests/test_recent_search.py
import pytest
import os
import time
from unittest.mock import patch, MagicMock
from google_maps_live.directions import find_directions, navigate
from google_maps_live.SimulationEngine.models import TravelMode, Avoid, UserLocation, FindDirectionsInput, NavigateInput, LatLng, DirectionsSummary
from google_maps_live.SimulationEngine.utils import get_location_from_env, add_recent_search, get_recent_searches, get_gemini_response, parse_json_from_gemini_response, get_model_from_gemini_response
from google_maps_live.SimulationEngine.custom_errors import UserLocationError, UndefinedLocationError
from google_maps_live.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestAddRecentSearch(BaseTestCaseWithErrorHandler):
    """Test cases for the add_recent_search utility function."""
    
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
        
        add_recent_search("find_directions", parameters, result)
        
        recent_searches = get_recent_searches("find_directions")
        assert len(recent_searches) == 1
        assert recent_searches[0]["parameters"] == parameters
        assert recent_searches[0]["result"] == result
    
    def test_add_recent_search_existing_endpoint(self):
        """Test adding a recent search to an existing endpoint."""
        # Add first search
        parameters1 = {"destination": "San Francisco, CA", "origin": "Mountain View, CA"}
        result1 = {"map_url": "https://maps.google.com", "travel_mode": "driving"}
        add_recent_search("find_directions", parameters1, result1)
        
        # Add second search
        parameters2 = {"destination": "Palo Alto, CA", "origin": "San Jose, CA"}
        result2 = {"map_url": "https://maps.google.com", "travel_mode": "walking"}
        add_recent_search("find_directions", parameters2, result2)
        
        recent_searches = get_recent_searches("find_directions")
        assert len(recent_searches) == 2
        assert recent_searches[0]["parameters"] == parameters2  # Most recent first
        assert recent_searches[1]["parameters"] == parameters1
    
    def test_add_recent_search_allows_duplicates(self):
        """Test that duplicate searches are allowed and both are present."""
        parameters = {"destination": "San Francisco, CA", "origin": "Mountain View, CA"}
        result = {"map_url": "https://maps.google.com", "travel_mode": "driving"}
        
        # Add same search twice
        add_recent_search("find_directions", parameters, result)
        add_recent_search("find_directions", parameters, result)
        
        recent_searches = get_recent_searches("find_directions")
        assert len(recent_searches) == 2  # Both entries should be present
        assert recent_searches[0]["parameters"] == parameters
        assert recent_searches[1]["parameters"] == parameters
    
    def test_add_recent_search_max_limit(self):
        """Test that recent searches are limited to 50 entries."""
        # Add 55 searches
        for i in range(55):
            parameters = {"destination": f"Location {i}", "origin": f"Origin {i}"}
            result = {"map_url": f"https://maps.google.com/{i}", "travel_mode": "driving"}
            add_recent_search("find_directions", parameters, result)
        
        recent_searches = get_recent_searches("find_directions")
        assert len(recent_searches) <= 50  # Should be limited to 50
        assert recent_searches[0]["parameters"]["destination"] == "Location 54"  # Most recent first


class TestGetRecentSearches(BaseTestCaseWithErrorHandler):
    """Test cases for the get_recent_searches utility function."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Clear any existing recent searches
        DB["recent_searches"] = {}
    
    def tearDown(self):
        """Clean up after each test."""
        # Clear any existing recent searches
        DB["recent_searches"] = {}
    
    def test_get_recent_searches_empty_endpoint(self):
        """Test getting recent searches for an endpoint with no history."""
        recent_searches = get_recent_searches("nonexistent_endpoint")
        assert recent_searches == []
    
    def test_get_recent_searches_with_max_results(self):
        """Test getting recent searches with max_results limit."""
        # Add 10 searches
        for i in range(10):
            parameters = {"destination": f"Location {i}", "origin": f"Origin {i}"}
            result = {"map_url": f"https://maps.google.com/{i}", "travel_mode": "driving"}
            add_recent_search("find_directions", parameters, result)
        
        # Get only 3 most recent
        recent_searches = get_recent_searches("find_directions", max_results=3)
        assert len(recent_searches) == 3
        assert recent_searches[0]["parameters"]["destination"] == "Location 9"  # Most recent
        assert recent_searches[2]["parameters"]["destination"] == "Location 7"  # Third most recent
    
    def test_get_recent_searches_default_max_results(self):
        """Test that default max_results is 5."""
        # Add 10 searches
        for i in range(10):
            parameters = {"destination": f"Location {i}", "origin": f"Origin {i}"}
            result = {"map_url": f"https://maps.google.com/{i}", "travel_mode": "driving"}
            add_recent_search("find_directions", parameters, result)
        
        recent_searches = get_recent_searches("find_directions")
        assert len(recent_searches) == 5  # Default should be 5


class TestFindDirectionsRecentSearch(BaseTestCaseWithErrorHandler):
    """Test cases for recent search functionality in find_directions function."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Clear any existing recent searches
        DB["recent_searches"] = {}
    
    def tearDown(self):
        """Clean up after each test."""
        # Clear any existing recent searches
        DB["recent_searches"] = {}
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_find_directions_adds_recent_search(self, mock_parse_json, mock_get_gemini):
        """Test that find_directions adds a recent search entry."""
        # Mock the Gemini response
        mock_get_gemini.return_value = "Mock Gemini response"
        mock_parse_json.return_value = {
            "map_url": "https://maps.google.com",
            "travel_mode": "driving",
            "routes": []
        }
        
        # Call find_directions
        result = find_directions(
            destination="San Francisco, CA",
            origin="Mountain View, CA",
            travel_mode="driving"
        )
        
        # Check that recent search was added
        recent_searches = get_recent_searches("find_directions")
        assert len(recent_searches) == 1
        assert recent_searches[0]["parameters"]["destination"] == "San Francisco, CA"
        assert recent_searches[0]["parameters"]["origin"] == "Mountain View, CA"
        assert recent_searches[0]["parameters"]["travel_mode"] == TravelMode.DRIVING
        assert recent_searches[0]["result"] == result
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_find_directions_recent_search_with_waypoints(self, mock_parse_json, mock_get_gemini):
        """Test that find_directions adds recent search with waypoints."""
        # Mock the Gemini response
        mock_get_gemini.return_value = "Mock Gemini response"
        mock_parse_json.return_value = {
            "map_url": "https://maps.google.com",
            "travel_mode": "driving",
            "routes": []
        }
        
        # Call find_directions with waypoints
        waypoints = ["Palo Alto, CA", "Redwood City, CA"]
        result = find_directions(
            destination="San Francisco, CA",
            origin="Mountain View, CA",
            waypoints=waypoints
        )
        
        # Check that recent search was added with waypoints
        recent_searches = get_recent_searches("find_directions")
        assert len(recent_searches) == 1
        assert recent_searches[0]["parameters"]["waypoints"] == waypoints
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_find_directions_recent_search_with_avoid(self, mock_parse_json, mock_get_gemini):
        """Test that find_directions adds recent search with avoid features."""
        # Mock the Gemini response
        mock_get_gemini.return_value = "Mock Gemini response"
        mock_parse_json.return_value = {
            "map_url": "https://maps.google.com",
            "travel_mode": "driving",
            "routes": []
        }
        
        # Call find_directions with avoid features
        avoid = ["tolls", "highways"]
        result = find_directions(
            destination="San Francisco, CA",
            origin="Mountain View, CA",
            avoid=avoid
        )
        
        # Check that recent search was added with avoid features
        recent_searches = get_recent_searches("find_directions")
        assert len(recent_searches) == 1
        assert recent_searches[0]["parameters"]["avoid"] == [Avoid.TOLLS, Avoid.HIGHWAYS]
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_find_directions_recent_search_with_time_constraints(self, mock_parse_json, mock_get_gemini):
        """Test that find_directions adds recent search with time constraints."""
        # Mock the Gemini response
        mock_get_gemini.return_value = "Mock Gemini response"
        mock_parse_json.return_value = {
            "map_url": "https://maps.google.com",
            "travel_mode": "driving",
            "routes": []
        }
        
        # Call find_directions with departure time
        departure_time = 1640995200  # Unix timestamp
        result = find_directions(
            destination="San Francisco, CA",
            origin="Mountain View, CA",
            departure_time=departure_time
        )
        
        # Check that recent search was added with departure time
        recent_searches = get_recent_searches("find_directions")
        assert len(recent_searches) == 1
        assert recent_searches[0]["parameters"]["departure_time"] == departure_time
    
    def test_find_directions_recent_search_on_validation_error(self):
        """Test that recent search is not added when validation fails."""
        # This should raise a ValueError due to invalid travel mode
        self.assert_error_behavior(
            lambda: find_directions(
                destination="San Francisco, CA",
                origin="Mountain View, CA",
                travel_mode="invalid_mode"
            ),
            ValueError,
            "Invalid travel_mode"
        )
        
        # Check that no recent search was added
        recent_searches = get_recent_searches("find_directions")
        assert len(recent_searches) == 0


class TestNavigateRecentSearch(BaseTestCaseWithErrorHandler):
    """Test cases for recent search functionality in navigate function."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Clear any existing recent searches
        DB["recent_searches"] = {}
    
    def tearDown(self):
        """Clean up after each test."""
        # Clear any existing recent searches
        DB["recent_searches"] = {}
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_navigate_adds_recent_search(self, mock_parse_json, mock_get_gemini):
        """Test that navigate adds a recent search entry."""
        # Mock the Gemini response
        mock_get_gemini.return_value = "Mock Gemini response"
        mock_parse_json.return_value = {
            "map_url": "https://maps.google.com",
            "travel_mode": "driving",
            "routes": []
        }
        
        # Call navigate
        result = navigate(
            destination="San Francisco, CA",
            travel_mode="driving"
        )
        
        # Check that recent search was added
        recent_searches = get_recent_searches("navigate")
        assert len(recent_searches) == 1
        assert recent_searches[0]["parameters"]["destination"] == "San Francisco, CA"
        assert recent_searches[0]["parameters"]["travel_mode"] == TravelMode.DRIVING
        assert recent_searches[0]["result"] == result
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_navigate_recent_search_with_waypoints(self, mock_parse_json, mock_get_gemini):
        """Test that navigate adds recent search with waypoints."""
        # Mock the Gemini response
        mock_get_gemini.return_value = "Mock Gemini response"
        mock_parse_json.return_value = {
            "map_url": "https://maps.google.com",
            "travel_mode": "driving",
            "routes": []
        }
        
        # Call navigate with waypoints
        waypoints = ["Palo Alto, CA", "Redwood City, CA"]
        result = navigate(
            destination="San Francisco, CA",
            waypoints=waypoints
        )
        
        # Check that recent search was added with waypoints
        recent_searches = get_recent_searches("navigate")
        assert len(recent_searches) == 1
        assert recent_searches[0]["parameters"]["waypoints"] == waypoints
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_navigate_recent_search_with_avoid(self, mock_parse_json, mock_get_gemini):
        """Test that navigate adds recent search with avoid features."""
        # Mock the Gemini response
        mock_get_gemini.return_value = "Mock Gemini response"
        mock_parse_json.return_value = {
            "map_url": "https://maps.google.com",
            "travel_mode": "driving",
            "routes": []
        }
        
        # Call navigate with avoid features
        avoid = ["tolls", "highways"]
        result = navigate(
            destination="San Francisco, CA",
            avoid=avoid
        )
        
        # Check that recent search was added with avoid features
        recent_searches = get_recent_searches("navigate")
        assert len(recent_searches) == 1
        assert recent_searches[0]["parameters"]["avoid"] == [Avoid.TOLLS, Avoid.HIGHWAYS]
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_navigate_recent_search_with_location_bias(self, mock_parse_json, mock_get_gemini):
        """Test that navigate adds recent search with location bias."""
        # Mock the Gemini response
        mock_get_gemini.return_value = "Mock Gemini response"
        mock_parse_json.return_value = {
            "map_url": "https://maps.google.com",
            "travel_mode": "driving",
            "routes": []
        }
        
        # Call navigate with location bias
        origin_bias = {"latitude": 37.7749, "longitude": -122.4194}
        result = navigate(
            destination="San Francisco, CA",
            origin_location_bias=origin_bias
        )
        
        # Check that recent search was added with location bias
        recent_searches = get_recent_searches("navigate")
        assert len(recent_searches) == 1
        assert recent_searches[0]["parameters"]["origin_location_bias"] == origin_bias
    
    def test_navigate_recent_search_on_validation_error(self):
        """Test that recent search is not added when validation fails."""
        # This should raise a ValueError due to invalid travel mode
        self.assert_error_behavior(
            lambda: navigate(
                destination="San Francisco, CA",
                travel_mode="invalid_mode"
            ),
            ValueError,
            "Invalid travel_mode"
        )
        
        # Check that no recent search was added
        recent_searches = get_recent_searches("navigate")
        assert len(recent_searches) == 0


class TestRecentSearchIntegration(BaseTestCaseWithErrorHandler):
    """Integration tests for recent search functionality across multiple endpoints."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Clear any existing recent searches
        DB["recent_searches"] = {}
    
    def tearDown(self):
        """Clean up after each test."""
        # Clear any existing recent searches
        DB["recent_searches"] = {}
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_multiple_endpoints_separate_storage(self, mock_parse_json, mock_get_gemini):
        """Test that different endpoints store recent searches separately."""
        # Mock the Gemini response
        mock_get_gemini.return_value = "Mock Gemini response"
        mock_parse_json.return_value = {
            "map_url": "https://maps.google.com",
            "travel_mode": "driving",
            "routes": []
        }
        
        # Add searches to both endpoints
        find_directions(destination="San Francisco, CA", origin="Mountain View, CA")
        navigate(destination="Palo Alto, CA")
        
        # Check that searches are stored separately
        find_directions_searches = get_recent_searches("find_directions")
        navigate_searches = get_recent_searches("navigate")
        
        assert len(find_directions_searches) == 1
        assert len(navigate_searches) == 1
        assert find_directions_searches[0]["parameters"]["destination"] == "San Francisco, CA"
        assert navigate_searches[0]["parameters"]["destination"] == "Palo Alto, CA"
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_recent_search_persistence(self, mock_parse_json, mock_get_gemini):
        """Test that recent searches persist across multiple calls."""
        # Mock the Gemini response
        mock_get_gemini.return_value = "Mock Gemini response"
        mock_parse_json.return_value = {
            "map_url": "https://maps.google.com",
            "travel_mode": "driving",
            "routes": []
        }
        
        # Make multiple calls to find_directions
        destinations = ["San Francisco, CA", "Palo Alto, CA", "Mountain View, CA"]
        for dest in destinations:
            find_directions(destination=dest, origin="Current Location")
        
        # Check that all searches are stored
        recent_searches = get_recent_searches("find_directions")
        assert len(recent_searches) == 3
        
        # Check order (most recent first)
        assert recent_searches[0]["parameters"]["destination"] == "Mountain View, CA"
        assert recent_searches[1]["parameters"]["destination"] == "Palo Alto, CA"
        assert recent_searches[2]["parameters"]["destination"] == "San Francisco, CA"
    
    @patch('google_maps_live.SimulationEngine.utils.get_gemini_response')
    @patch('google_maps_live.SimulationEngine.utils.parse_json_from_gemini_response')
    def test_recent_search_parameter_filtering(self, mock_parse_json, mock_get_gemini):
        """Test that only non-empty parameters are stored in recent searches."""
        # Mock the Gemini response
        mock_get_gemini.return_value = "Mock Gemini response"
        mock_parse_json.return_value = {
            "map_url": "https://maps.google.com",
            "travel_mode": "driving",
            "routes": []
        }
        
        # Call find_directions with some None parameters
        result = find_directions(
            destination="San Francisco, CA",
            origin=None,  # This should be filtered out
            travel_mode="driving",
            waypoints=None,  # This should be filtered out
            avoid=["tolls"]
        )
        
        # Check that only non-empty parameters are stored
        recent_searches = get_recent_searches("find_directions")
        assert len(recent_searches) == 1
        
        parameters = recent_searches[0]["parameters"]
        assert "destination" in parameters
        assert "travel_mode" in parameters
        assert "avoid" in parameters
        assert "origin" not in parameters  # Should be filtered out
        assert "waypoints" not in parameters  # Should be filtered out 