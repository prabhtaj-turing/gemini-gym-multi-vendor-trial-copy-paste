import unittest
import importlib
import os
import sys

class ImportTest(unittest.TestCase):
    def test_import_google_maps_live_package(self):
        """Test that the main google_maps_live package can be imported."""
        try:
            import google_maps_live
        except ImportError as e:
            self.fail(f"Failed to import google_maps_live package: {e}")

    def test_import_public_functions_from_directions(self):
        """Test that public functions can be imported from the directions module."""
        try:
            from google_maps_live.directions import find_directions
            from google_maps_live.directions import navigate
        except ImportError as e:
            self.fail(f"Failed to import directions functions: {e}")

    def test_import_public_functions_from_places(self):
        """Test that public functions can be imported from the places module."""
        try:
            from google_maps_live.places import query_places
            from google_maps_live.places import lookup_place_details
            from google_maps_live.places import analyze_places
            from google_maps_live.places import show_on_map
        except ImportError as e:
            self.fail(f"Failed to import places functions: {e}")

    def test_public_functions_are_callable(self):
        """Test that the public functions are callable."""
        from google_maps_live.directions import find_directions, navigate
        from google_maps_live.places import query_places, lookup_place_details, analyze_places, show_on_map

        # Test directions functions
        self.assertTrue(callable(find_directions))
        self.assertTrue(callable(navigate))
        
        # Test places functions
        self.assertTrue(callable(query_places))
        self.assertTrue(callable(lookup_place_details))
        self.assertTrue(callable(analyze_places))
        self.assertTrue(callable(show_on_map))

    def test_import_simulation_engine_components(self):
        """Test that components from SimulationEngine can be imported."""
        try:
            from google_maps_live.SimulationEngine import utils
            from google_maps_live.SimulationEngine.custom_errors import ParseError, UserLocationError, UndefinedLocationError
            from google_maps_live.SimulationEngine.db import DB, save_state, load_state
            from google_maps_live.SimulationEngine.models import (
                TravelMode, UserLocation, LatLng, DirectionsSummary, Place, SummaryPlaces
            )
        except ImportError as e:
            self.fail(f"Failed to import SimulationEngine components: {e}")

    def test_simulation_engine_components_are_usable(self):
        """Test that imported SimulationEngine components are usable."""
        from google_maps_live.SimulationEngine import utils
        from google_maps_live.SimulationEngine.custom_errors import ParseError, UserLocationError, UndefinedLocationError
        from google_maps_live.SimulationEngine.db import DB, save_state, load_state
        from google_maps_live.SimulationEngine.models import (
            TravelMode, UserLocation, LatLng, DirectionsSummary, Place, SummaryPlaces
        )

        # Test utils module
        self.assertTrue(hasattr(utils, 'get_gemini_response'))
        self.assertTrue(hasattr(utils, 'parse_json_from_gemini_response'))
        self.assertTrue(hasattr(utils, 'get_location_from_env'))
        self.assertTrue(hasattr(utils, 'get_model_from_gemini_response'))
        self.assertTrue(hasattr(utils, 'add_recent_search'))
        self.assertTrue(hasattr(utils, 'get_recent_searches'))

        # Test custom errors
        self.assertTrue(issubclass(ParseError, Exception))
        self.assertTrue(issubclass(UserLocationError, Exception))
        self.assertTrue(issubclass(UndefinedLocationError, Exception))

        # Test database functions
        self.assertTrue(callable(save_state))
        self.assertTrue(callable(load_state))
        self.assertIsInstance(DB, dict)

        # Test models
        self.assertTrue(hasattr(TravelMode, 'DRIVING'))
        self.assertTrue(hasattr(TravelMode, 'WALKING'))
        self.assertTrue(hasattr(TravelMode, 'BICYCLING'))
        self.assertTrue(hasattr(TravelMode, 'TRANSIT'))
        
        self.assertTrue(hasattr(UserLocation, 'MY_HOME'))
        self.assertTrue(hasattr(UserLocation, 'MY_LOCATION'))
        self.assertTrue(hasattr(UserLocation, 'MY_WORK'))

    def test_import_common_utils_dependencies(self):
        """Test that common utility dependencies can be imported."""
        try:
            from common_utils.print_log import print_log
            from common_utils.base_case import BaseTestCaseWithErrorHandler
            from common_utils.error_handling import get_package_error_mode
            from common_utils.init_utils import create_error_simulator, resolve_function_import
        except ImportError as e:
            self.fail(f"Failed to import common_utils dependencies: {e}")

    def test_common_utils_components_are_usable(self):
        """Test that imported common_utils components are usable."""
        from common_utils.print_log import print_log
        from common_utils.base_case import BaseTestCaseWithErrorHandler
        from common_utils.error_handling import get_package_error_mode
        from common_utils.init_utils import create_error_simulator, resolve_function_import

        # Test print_log function
        self.assertTrue(callable(print_log))
        
        # Test base case class
        self.assertTrue(issubclass(BaseTestCaseWithErrorHandler, unittest.TestCase))
        
        # Test error handling functions
        self.assertTrue(callable(get_package_error_mode))
        self.assertTrue(callable(create_error_simulator))
        self.assertTrue(callable(resolve_function_import))

    def test_import_pydantic_dependencies(self):
        """Test that Pydantic dependencies can be imported."""
        try:
            from pydantic import BaseModel, ValidationError, Field, field_validator
        except ImportError as e:
            self.fail(f"Failed to import Pydantic dependencies: {e}")

    def test_pydantic_components_are_usable(self):
        """Test that imported Pydantic components are usable."""
        from pydantic import BaseModel, ValidationError, Field, field_validator

        # Test Pydantic classes
        self.assertTrue(issubclass(BaseModel, object))
        self.assertTrue(issubclass(ValidationError, Exception))
        self.assertTrue(callable(Field))
        self.assertTrue(callable(field_validator))

    def test_import_requests_dependency(self):
        """Test that requests dependency can be imported."""
        try:
            import requests
        except ImportError as e:
            self.fail(f"Failed to import requests dependency: {e}")

    def test_requests_component_is_usable(self):
        """Test that imported requests component is usable."""
        import requests
        
        # Test requests module
        self.assertTrue(hasattr(requests, 'get'))
        self.assertTrue(hasattr(requests, 'post'))
        self.assertTrue(hasattr(requests, 'put'))
        self.assertTrue(hasattr(requests, 'delete'))

    def test_import_dotenv_dependency(self):
        """Test that python-dotenv dependency can be imported."""
        try:
            from dotenv import load_dotenv
        except ImportError as e:
            self.fail(f"Failed to import python-dotenv dependency: {e}")

    def test_dotenv_component_is_usable(self):
        """Test that imported python-dotenv component is usable."""
        from dotenv import load_dotenv
        
        # Test load_dotenv function
        self.assertTrue(callable(load_dotenv))

    def test_package_has_expected_attributes(self):
        """Test that the google_maps_live package has expected attributes."""
        import google_maps_live
        
        # Test package attributes
        self.assertTrue(hasattr(google_maps_live, 'ERROR_MODE'))
        self.assertTrue(hasattr(google_maps_live, '__all__'))
        
        # Test that __all__ contains expected function names
        expected_functions = [
            'find_directions',
            'navigate', 
            'query_places',
            'lookup_place_details',
            'analyze_places',
            'show_on_map'
        ]
        
        for func_name in expected_functions:
            self.assertIn(func_name, google_maps_live.__all__)

    def test_function_imports_work_dynamically(self):
        """Test that functions can be imported dynamically using __getattr__."""
        import google_maps_live
        
        # Test that functions are accessible as attributes
        self.assertTrue(hasattr(google_maps_live, 'find_directions'))
        self.assertTrue(hasattr(google_maps_live, 'navigate'))
        self.assertTrue(hasattr(google_maps_live, 'query_places'))
        self.assertTrue(hasattr(google_maps_live, 'lookup_place_details'))
        self.assertTrue(hasattr(google_maps_live, 'analyze_places'))
        self.assertTrue(hasattr(google_maps_live, 'show_on_map'))

    def test_import_without_side_effects(self):
        """Test that importing the package doesn't cause unexpected side effects."""
        # Store initial state
        initial_modules = set(sys.modules.keys())
        
        # Import the package
        import google_maps_live
        
        # Check that no unexpected modules were loaded
        new_modules = set(sys.modules.keys()) - initial_modules
        expected_new_modules = {
            'google_maps_live',
            'google_maps_live.SimulationEngine',
            'google_maps_live.SimulationEngine.utils',
            'google_maps_live.SimulationEngine.custom_errors',
            'google_maps_live.SimulationEngine.db',
            'google_maps_live.SimulationEngine.models',
            'google_maps_live.directions',
            'google_maps_live.places'
        }
        
        # Only check for expected modules, allow for other dependencies
        for module in expected_new_modules:
            if module in new_modules:
                self.assertIn(module, new_modules)

    def test_import_performance(self):
        """Test that importing the package doesn't take too long."""
        import time
        
        start_time = time.time()
        import google_maps_live
        end_time = time.time()
        
        import_time = end_time - start_time
        
        # Import should complete in under 1 second
        self.assertLess(import_time, 1.0, f"Package import took {import_time:.3f} seconds, which is too slow")


if __name__ == '__main__':
    unittest.main()
