# google_maps_live/tests/test_smoke.py
"""
Smoke tests for google_maps_live API.

These tests provide a quick check that the package installs and runs without issues.
They ensure the service is ready to be implemented by testing:
- Package can be imported
- Main API functions can be imported and are callable
- Basic functionality works without errors
"""

import unittest
import sys
import os

from common_utils.base_case import BaseTestCaseWithErrorHandler

class SmokeTest(BaseTestCaseWithErrorHandler):
    """Smoke tests to verify basic package functionality."""
    
    def test_package_import(self):
        """Test that the package can be imported without errors."""
        try:
            import google_maps_live
            print("✓ Package import successful")
        except ImportError as e:
            self.fail(f"Package import failed: {e}")
    
    def test_api_functions_import(self):
        """Test that main API functions can be imported."""
        try:
            # Test directions functions
            from google_maps_live.directions import find_directions, navigate
            print("✓ Directions functions imported successfully")
            
            # Test places functions
            from google_maps_live.places import query_places, lookup_place_details, analyze_places, show_on_map
            print("✓ Places functions imported successfully")
            
        except ImportError as e:
            self.fail(f"API function import failed: {e}")
    
    def test_api_functions_callable(self):
        """Test that imported API functions are callable."""
        from google_maps_live.directions import find_directions, navigate
        from google_maps_live.places import query_places, lookup_place_details, analyze_places, show_on_map
        
        # Verify all functions are callable
        functions = [
            find_directions, navigate,
            query_places, lookup_place_details, analyze_places, show_on_map
        ]
        
        for func in functions:
            self.assertTrue(callable(func), f"Function {func.__name__} is not callable")
        
        print("✓ All API functions are callable")
    
    def test_simulation_engine_import(self):
        """Test that SimulationEngine components can be imported."""
        try:
            from google_maps_live.SimulationEngine import utils, custom_errors, db, models
            print("✓ SimulationEngine components imported successfully")
        except ImportError as e:
            self.fail(f"SimulationEngine import failed: {e}")
    
    def test_basic_functionality(self):
        """Test basic functionality without making actual API calls."""
        try:
            # Test that we can access package attributes
            import google_maps_live
            
            # Check package has expected structure
            self.assertTrue(hasattr(google_maps_live, '__all__'))
            self.assertTrue(hasattr(google_maps_live, 'ERROR_MODE'))
            
            # Check that functions are accessible as package attributes
            self.assertTrue(hasattr(google_maps_live, 'find_directions'))
            self.assertTrue(hasattr(google_maps_live, 'query_places'))
            
            print("✓ Basic package functionality verified")
            
        except Exception as e:
            self.fail(f"Basic functionality test failed: {e}")
    
    def test_error_handling_import(self):
        """Test that error handling components can be imported."""
        try:
            from google_maps_live.SimulationEngine.custom_errors import ParseError, UserLocationError
            print("✓ Error handling components imported successfully")
        except ImportError as e:
            self.fail(f"Error handling import failed: {e}")
    
    def test_models_import(self):
        """Test that Pydantic models can be imported."""
        try:
            from google_maps_live.SimulationEngine.models import (
                TravelMode, UserLocation, Place, DirectionsSummary
            )
            print("✓ Pydantic models imported successfully")
        except ImportError as e:
            self.fail(f"Models import failed: {e}")
    
    def test_utils_import(self):
        """Test that utility functions can be imported."""
        try:
            from google_maps_live.SimulationEngine.utils import (
                get_gemini_response, parse_json_from_gemini_response
            )
            print("✓ Utility functions imported successfully")
        except ImportError as e:
            self.fail(f"Utility functions import failed: {e}")
    
    def test_package_ready_for_implementation(self):
        """Final test to confirm package is ready for implementation."""
        try:
            # This test ensures all critical components are available
            import google_maps_live
            
            # Check that we have the core API functions
            core_functions = [
                'find_directions', 'navigate',
                'query_places', 'lookup_place_details', 
                'analyze_places', 'show_on_map'
            ]
            
            for func_name in core_functions:
                self.assertTrue(hasattr(google_maps_live, func_name))
            
            # Check that SimulationEngine is available
            from google_maps_live.SimulationEngine import utils, models, custom_errors, db
            
            # Check that common utilities are available
            from common_utils.print_log import print_log
            
            print("✓ Package is ready for implementation")
            
        except Exception as e:
            self.fail(f"Package readiness check failed: {e}")


if __name__ == '__main__':
    # Run smoke tests with verbose output
    unittest.main(verbosity=2)
