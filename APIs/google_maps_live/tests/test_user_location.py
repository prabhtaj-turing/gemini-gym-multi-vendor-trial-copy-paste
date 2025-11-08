import pytest
import os
import sys
from unittest.mock import patch

# Add the parent directory to the path so we can import common_utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_maps_live.SimulationEngine.models import UserLocation, FindDirectionsInput
from google_maps_live.SimulationEngine.utils import get_location_from_env
from google_maps_live.SimulationEngine.custom_errors import UserLocationError, UndefinedLocationError


class TestUserLocation(BaseTestCaseWithErrorHandler):
    """Test UserLocation enum functionality and environment variable resolution."""
    
    def test_user_location_enum_values(self):
        """Test that UserLocation enum has the correct values."""
        assert UserLocation.MY_HOME == "MY_HOME"
        assert UserLocation.MY_LOCATION == "MY_LOCATION"
        assert UserLocation.MY_WORK == "MY_WORK"
    
    def test_pydantic_model_with_string_location_bias(self):
        """Test that string values are handled correctly by Pydantic models."""
        input_data = FindDirectionsInput(
            destination="Oakland, CA",
            origin_location_bias="San Francisco, CA"
        )
        assert input_data.origin_location_bias == "San Francisco, CA"
    
    def test_pydantic_model_with_dict_location_bias(self):
        """Test that coordinate dict values are handled correctly by Pydantic models."""
        coords = {"latitude": 37.7749, "longitude": -122.4194}
        input_data = FindDirectionsInput(
            destination="Oakland, CA",
            origin_location_bias=coords
        )
        # Pydantic converts the dict to a LatLng object
        assert input_data.origin_location_bias.latitude == coords["latitude"]
        assert input_data.origin_location_bias.longitude == coords["longitude"]
    
    def test_pydantic_model_with_none_location_bias(self):
        """Test that None values are handled correctly by Pydantic models."""
        input_data = FindDirectionsInput(
            destination="Oakland, CA",
            origin_location_bias=None
        )
        assert input_data.origin_location_bias is None
    
    def test_pydantic_model_with_user_location_enum(self):
        """Test that UserLocation enum values are resolved to environment variables."""
        # Set up test environment variables
        os.environ["MY_HOME"] = "123 Main St, San Francisco, CA"
        os.environ["MY_LOCATION"] = "456 Oak Ave, Oakland, CA"
        os.environ["MY_WORK"] = "789 Business Blvd, San Jose, CA"
        
        try:
            # Test MY_HOME
            input_data = FindDirectionsInput(
                destination="Oakland, CA",
                origin_location_bias=UserLocation.MY_HOME
            )
            assert input_data.origin_location_bias == "123 Main St, San Francisco, CA"
            
            # Test MY_LOCATION
            input_data = FindDirectionsInput(
                destination="San Jose, CA",
                origin_location_bias=UserLocation.MY_LOCATION
            )
            assert input_data.origin_location_bias == "456 Oak Ave, Oakland, CA"
            
            # Test MY_WORK
            input_data = FindDirectionsInput(
                destination="San Francisco, CA",
                origin_location_bias=UserLocation.MY_WORK
            )
            assert input_data.origin_location_bias == "789 Business Blvd, San Jose, CA"
            
        finally:
            # Clean up test environment variables
            if "MY_HOME" in os.environ:
                del os.environ["MY_HOME"]
            if "MY_LOCATION" in os.environ:
                del os.environ["MY_LOCATION"]
            if "MY_WORK" in os.environ:
                del os.environ["MY_WORK"]
    
    def test_pydantic_model_with_missing_environment_variable(self):
        """Test that UndefinedLocationError is raised when environment variable is missing."""
        def create_model_with_missing_env():
            return FindDirectionsInput(
                destination="Oakland, CA",
                origin_location_bias="MY_HOME"
            )
        
        self.assert_error_behavior(
            create_model_with_missing_env,
            UndefinedLocationError,
            "Environment variable for 'MY_HOME' is not defined."
        )
    
    def test_get_location_from_env_missing_variable(self):
        """Test that UndefinedLocationError is raised when environment variable is missing."""
        def call_get_location_from_env():
            return get_location_from_env("MY_HOME")
        
        self.assert_error_behavior(
            call_get_location_from_env,
            UndefinedLocationError,
            "Environment variable for 'MY_HOME' is not defined."
        )
    
    def test_get_location_from_env_invalid_enum(self):
        """Test that UserLocationError is raised for invalid enum values."""
        def call_with_invalid_enum():
            return get_location_from_env("INVALID_LOCATION")  # type: ignore
        
        self.assert_error_behavior(
            call_with_invalid_enum,
            UserLocationError,
            "Invalid location variable: 'INVALID_LOCATION'. Must be one of MY_HOME, MY_LOCATION, MY_WORK"
        ) 