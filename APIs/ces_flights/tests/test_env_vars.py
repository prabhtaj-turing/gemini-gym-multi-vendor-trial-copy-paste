"""
Test cases for environment variable management implementation.
Tests the DI compliance for UpdateEnvVar functionality.
"""

import sys
import os
import unittest
from datetime import datetime
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ces_flights.SimulationEngine.utils import (
    EnvironmentVariableManager,
    FlightBookingEnvironmentManager,
    ConversationStateManager,
    update_env_var
)
from ces_flights.SimulationEngine.custom_errors import ValidationError


class TestEnvironmentVariableManager(BaseTestCaseWithErrorHandler):
    """Test the EnvironmentVariableManager class functionality."""
    
    def setUp(self):
        """Set up mocks to prevent DB writes."""
        self.save_patcher = patch('SimulationEngine.db._save_state_to_file')
        self.mock_save = self.save_patcher.start()
    
    def tearDown(self):
        """Clean up mocks."""
        self.save_patcher.stop()
    
    def test_env_var_manager_initialization(self):
        """Test environment variable manager initializes correctly."""
        manager = EnvironmentVariableManager()
        
        self.assertEqual(manager.variables, {})
        self.assertEqual(manager.variable_types, {})
        self.assertEqual(manager.variable_descriptions, {})
        self.assertEqual(manager.variable_history, {})
    
    def test_update_env_var_basic(self):
        """Test basic environment variable update."""
        manager = EnvironmentVariableManager()
        
        manager.update_env_var("test_var", "test_value", "str", "Test variable")
        
        self.assertEqual(manager.get_env_var("test_var"), "test_value")
        self.assertEqual(manager.get_env_var_type("test_var"), "str")
        self.assertEqual(manager.get_env_var_description("test_var"), "Test variable")
    
    def test_update_env_var_with_history(self):
        """Test environment variable update with history tracking."""
        manager = EnvironmentVariableManager()
        
        # First update
        manager.update_env_var("test_var", "value1", "str", "Test variable")
        
        # Second update
        manager.update_env_var("test_var", "value2", "str", "Test variable")
        
        history = manager.get_env_var_history("test_var")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["old_value"], "value1")
        self.assertEqual(history[0]["new_value"], "value2")
        self.assertEqual(manager.get_env_var("test_var"), "value2")
    
    def test_get_env_var_with_default(self):
        """Test getting environment variable with default value."""
        manager = EnvironmentVariableManager()
        
        # Non-existent variable
        value = manager.get_env_var("nonexistent", "default_value")
        self.assertEqual(value, "default_value")
        
        # Existing variable
        manager.update_env_var("existing", "actual_value")
        value = manager.get_env_var("existing", "default_value")
        self.assertEqual(value, "actual_value")
    
    def test_list_env_vars(self):
        """Test listing all environment variables with metadata."""
        manager = EnvironmentVariableManager()
        
        manager.update_env_var("var1", "value1", "str", "Variable 1")
        manager.update_env_var("var2", 42, "int", "Variable 2")
        
        env_list = manager.list_env_vars()
        
        self.assertIn("var1", env_list)
        self.assertIn("var2", env_list)
        self.assertEqual(env_list["var1"]["value"], "value1")
        self.assertEqual(env_list["var1"]["type"], "str")
        self.assertEqual(env_list["var1"]["description"], "Variable 1")
        self.assertEqual(env_list["var2"]["value"], 42)
        self.assertEqual(env_list["var2"]["type"], "int")
    
    def test_validate_env_var(self):
        """Test environment variable validation."""
        manager = EnvironmentVariableManager()
        
        manager.update_env_var("test_var", "test_value", "str")
        
        # Valid variable
        self.assertTrue(manager.validate_env_var("test_var"))
        self.assertTrue(manager.validate_env_var("test_var", "str"))
        
        # Invalid type
        self.assertFalse(manager.validate_env_var("test_var", "int"))
        
        # Non-existent variable
        self.assertFalse(manager.validate_env_var("nonexistent"))
    
    def test_clear_env_var(self):
        """Test clearing environment variable."""
        manager = EnvironmentVariableManager()
        
        manager.update_env_var("test_var", "test_value", "str", "Test variable")
        self.assertEqual(manager.get_env_var("test_var"), "test_value")
        
        manager.clear_env_var("test_var")
        self.assertIsNone(manager.get_env_var("test_var"))
        self.assertEqual(manager.get_env_var_type("test_var"), "unknown")
        self.assertEqual(manager.get_env_var_description("test_var"), "")
    
    def test_clear_all_env_vars(self):
        """Test clearing all environment variables."""
        manager = EnvironmentVariableManager()
        
        manager.update_env_var("var1", "value1", "str", "Variable 1")
        manager.update_env_var("var2", "value2", "str", "Variable 2")
        
        self.assertEqual(len(manager.variables), 2)
        
        manager.clear_all_env_vars()
        
        self.assertEqual(len(manager.variables), 0)
        self.assertEqual(len(manager.variable_types), 0)
        self.assertEqual(len(manager.variable_descriptions), 0)
        self.assertEqual(len(manager.variable_history), 0)


class TestFlightBookingEnvironmentManager(BaseTestCaseWithErrorHandler):
    """Test the FlightBookingEnvironmentManager class functionality."""
    
    def setUp(self):
        """Set up mocks to prevent DB writes."""
        self.save_patcher = patch('SimulationEngine.db._save_state_to_file')
        self.mock_save = self.save_patcher.start()
    
    def tearDown(self):
        """Clean up mocks."""
        self.save_patcher.stop()
    
    def test_flight_env_manager_initialization(self):
        """Test flight booking environment manager initializes with flight variables."""
        manager = FlightBookingEnvironmentManager()
        
        # Check that all flight variables are initialized
        self.assertIn("origin", manager.variables)
        self.assertIn("destination", manager.variables)
        self.assertIn("num_adult_passengers", manager.variables)
        self.assertIn("selected_flight", manager.variables)
        
        # Check default values
        self.assertEqual(manager.get_env_var("origin"), "")
        self.assertEqual(manager.get_env_var("num_adult_passengers"), 0)
        self.assertEqual(manager.get_env_var("selected_flight"), {})
        self.assertEqual(manager.get_env_var("include_airlines"), [])
    
    def test_update_flight_var_valid(self):
        """Test updating flight variables with valid values."""
        manager = FlightBookingEnvironmentManager()
        
        # Test string variable
        manager.update_flight_var("origin", "New York, NY")
        self.assertEqual(manager.get_env_var("origin"), "New York, NY")
        
        # Test integer variable
        manager.update_flight_var("num_adult_passengers", 2)
        self.assertEqual(manager.get_env_var("num_adult_passengers"), 2)
        
        # Test boolean variable
        manager.update_flight_var("cheapest", True)
        self.assertTrue(manager.get_env_var("cheapest"))
        
        # Test list variable
        manager.update_flight_var("include_airlines", ["American", "Delta"])
        self.assertEqual(manager.get_env_var("include_airlines"), ["American", "Delta"])
        
        # Test dict variable
        flight_data = {"airline": "American", "price": 500}
        manager.update_flight_var("selected_flight", flight_data)
        self.assertEqual(manager.get_env_var("selected_flight"), flight_data)
    
    def test_update_flight_var_invalid_type(self):
        """Test updating flight variables with invalid types."""
        manager = FlightBookingEnvironmentManager()
        
        # Test invalid type for string variable
        with self.assertRaises(ValidationError):
            manager.update_flight_var("origin", 123)
        
        # Test invalid type for integer variable
        with self.assertRaises(ValidationError):
            manager.update_flight_var("num_adult_passengers", "two")
        
        # Test invalid type for boolean variable
        with self.assertRaises(ValidationError):
            manager.update_flight_var("cheapest", "yes")
    
    def test_update_flight_var_unknown_variable(self):
        """Test updating unknown flight variable."""
        manager = FlightBookingEnvironmentManager()
        
        with self.assertRaises(ValidationError):
            manager.update_flight_var("unknown_var", "value")
    
    def test_get_flight_search_params(self):
        """Test getting flight search parameters."""
        manager = FlightBookingEnvironmentManager()
        
        # Set some flight search parameters
        manager.update_flight_var("origin", "New York, NY")
        manager.update_flight_var("destination", "Los Angeles, CA")
        manager.update_flight_var("num_adult_passengers", 2)
        manager.update_flight_var("num_child_passengers", 1)
        manager.update_flight_var("max_stops", 1)
        manager.update_flight_var("cheapest", True)
        
        search_params = manager.get_flight_search_params()
        
        self.assertEqual(search_params["origin"], "New York, NY")
        self.assertEqual(search_params["destination"], "Los Angeles, CA")
        self.assertEqual(search_params["num_adult_passengers"], 2)
        self.assertEqual(search_params["num_child_passengers"], 1)
        self.assertEqual(search_params["max_stops"], 1)
        self.assertTrue(search_params["cheapest"])
        
        # Empty/default values should not be included
        self.assertNotIn("earliest_departure_date", search_params)
        self.assertNotIn("carry_on_bag_count", search_params)
    
    def test_is_flight_search_complete(self):
        """Test flight search completion check."""
        manager = FlightBookingEnvironmentManager()
        
        # Initially incomplete
        self.assertFalse(manager.is_flight_search_complete())
        
        # Set required variables
        manager.update_flight_var("origin", "New York, NY")
        manager.update_flight_var("destination", "Los Angeles, CA")
        manager.update_flight_var("earliest_departure_date", "2025-12-25")
        manager.update_flight_var("latest_departure_date", "2025-12-25")
        manager.update_flight_var("earliest_return_date", "2025-12-30")
        manager.update_flight_var("latest_return_date", "2025-12-30")
        manager.update_flight_var("num_adult_passengers", 2)
        manager.update_flight_var("num_child_passengers", 1)
        
        # Now complete
        self.assertTrue(manager.is_flight_search_complete())
    
    def test_is_booking_ready(self):
        """Test booking readiness check."""
        manager = FlightBookingEnvironmentManager()
        
        # Initially not ready
        self.assertFalse(manager.is_booking_ready())
        
        # Set selected flight
        manager.update_flight_var("selected_flight", {"airline": "American", "price": 500})
        self.assertFalse(manager.is_booking_ready())  # Still no travelers
        
        # Set travelers
        manager.update_flight_var("travelers", [{"first_name": "John", "last_name": "Doe"}])
        self.assertTrue(manager.is_booking_ready())
    
    def test_get_missing_flight_info(self):
        """Test getting missing flight information."""
        manager = FlightBookingEnvironmentManager()
        
        # All missing initially
        missing = manager.get_missing_flight_info()
        self.assertEqual(len(missing), 8)  # All required variables
        
        # Set some variables
        manager.update_flight_var("origin", "New York, NY")
        manager.update_flight_var("destination", "Los Angeles, CA")
        manager.update_flight_var("num_adult_passengers", 2)
        
        missing = manager.get_missing_flight_info()
        self.assertNotIn("origin", missing)
        self.assertNotIn("destination", missing)
        self.assertNotIn("num_adult_passengers", missing)
        self.assertIn("earliest_departure_date", missing)
        self.assertIn("latest_departure_date", missing)
        self.assertIn("earliest_return_date", missing)
        self.assertIn("latest_return_date", missing)
        self.assertIn("num_child_passengers", missing)


class TestConversationStateManagerWithEnvVars(BaseTestCaseWithErrorHandler):
    """Test ConversationStateManager with environment variable integration."""
    
    def setUp(self):
        """Set up mocks to prevent DB writes."""
        self.save_patcher = patch('SimulationEngine.db._save_state_to_file')
        self.mock_save = self.save_patcher.start()
    
    def tearDown(self):
        """Clean up mocks."""
        self.save_patcher.stop()
    
    def test_conversation_state_manager_with_env_vars(self):
        """Test conversation state manager with environment variables."""
        manager = ConversationStateManager()
        
        # Test flight environment variable updates
        manager.update_flight_env_var("origin", "New York, NY")
        manager.update_flight_env_var("destination", "Los Angeles, CA")
        manager.update_flight_env_var("num_adult_passengers", 2)
        
        self.assertEqual(manager.get_flight_env_var("origin"), "New York, NY")
        self.assertEqual(manager.get_flight_env_var("destination"), "Los Angeles, CA")
        self.assertEqual(manager.get_flight_env_var("num_adult_passengers"), 2)
    
    def test_flight_search_completion_check(self):
        """Test flight search completion check in conversation manager."""
        manager = ConversationStateManager()
        
        # Initially incomplete
        self.assertFalse(manager.is_flight_search_complete())
        
        # Set required variables
        manager.update_flight_env_var("origin", "New York, NY")
        manager.update_flight_env_var("destination", "Los Angeles, CA")
        manager.update_flight_env_var("earliest_departure_date", "2025-12-25")
        manager.update_flight_env_var("latest_departure_date", "2025-12-25")
        manager.update_flight_env_var("earliest_return_date", "2025-12-30")
        manager.update_flight_env_var("latest_return_date", "2025-12-30")
        manager.update_flight_env_var("num_adult_passengers", 2)
        manager.update_flight_env_var("num_child_passengers", 1)
        
        # Now complete
        self.assertTrue(manager.is_flight_search_complete())
    
    def test_booking_readiness_check(self):
        """Test booking readiness check in conversation manager."""
        manager = ConversationStateManager()
        
        # Initially not ready
        self.assertFalse(manager.is_booking_ready())
        
        # Set selected flight and travelers
        manager.update_flight_env_var("selected_flight", {"airline": "American", "price": 500})
        manager.update_flight_env_var("travelers", [{"first_name": "John", "last_name": "Doe"}])
        
        self.assertTrue(manager.is_booking_ready())
    
    def test_get_missing_flight_info(self):
        """Test getting missing flight information from conversation manager."""
        manager = ConversationStateManager()
        
        # Set some variables
        manager.update_flight_env_var("origin", "New York, NY")
        manager.update_flight_env_var("num_adult_passengers", 2)
        
        missing = manager.get_missing_flight_info()
        self.assertNotIn("origin", missing)
        self.assertNotIn("num_adult_passengers", missing)
        self.assertIn("destination", missing)
        self.assertIn("earliest_departure_date", missing)
    
    def test_get_flight_search_params(self):
        """Test getting flight search parameters from conversation manager."""
        manager = ConversationStateManager()
        
        # Set flight search parameters
        manager.update_flight_env_var("origin", "New York, NY")
        manager.update_flight_env_var("destination", "Los Angeles, CA")
        manager.update_flight_env_var("num_adult_passengers", 2)
        manager.update_flight_env_var("max_stops", 1)
        
        search_params = manager.get_flight_search_params()
        
        self.assertEqual(search_params["origin"], "New York, NY")
        self.assertEqual(search_params["destination"], "Los Angeles, CA")
        self.assertEqual(search_params["num_adult_passengers"], 2)
        self.assertEqual(search_params["max_stops"], 1)
    
    def test_list_flight_env_vars(self):
        """Test listing flight environment variables from conversation manager."""
        manager = ConversationStateManager()
        
        # Set some variables
        manager.update_flight_env_var("origin", "New York, NY")
        manager.update_flight_env_var("num_adult_passengers", 2)
        
        env_vars = manager.list_flight_env_vars()
        
        self.assertIn("origin", env_vars)
        self.assertIn("num_adult_passengers", env_vars)
        self.assertEqual(env_vars["origin"]["value"], "New York, NY")
        self.assertEqual(env_vars["num_adult_passengers"]["value"], 2)


class TestUpdateEnvVarFunction(BaseTestCaseWithErrorHandler):
    """Test the update_env_var function."""
    
    def setUp(self):
        """Set up mocks to prevent DB writes."""
        self.save_patcher = patch('SimulationEngine.db._save_state_to_file')
        self.mock_save = self.save_patcher.start()
    
    def tearDown(self):
        """Clean up mocks."""
        self.save_patcher.stop()
    
    def test_update_env_var_function(self):
        """Test the update_env_var function (placeholder implementation)."""
        # This is a placeholder function, so we just test it doesn't raise an error
        update_env_var("test_var", "test_value", "str", "Test variable")
        # Function should complete without error


class TestEnvironmentVariableIntegration(BaseTestCaseWithErrorHandler):
    """Integration tests for environment variable management with DI scenarios."""
    
    def setUp(self):
        """Set up mocks to prevent DB writes."""
        self.save_patcher = patch('SimulationEngine.db._save_state_to_file')
        self.mock_save = self.save_patcher.start()
    
    def tearDown(self):
        """Clean up mocks."""
        self.save_patcher.stop()
    
    def test_di_update_env_var_pattern(self):
        """Test DI UpdateEnvVar pattern implementation."""
        manager = ConversationStateManager()
        
        # DI Pattern: UpdateEnvVar [variable: 'origin', value: 'New York, NY']
        manager.update_flight_env_var("origin", "New York, NY")
        self.assertEqual(manager.get_flight_env_var("origin"), "New York, NY")
        
        # DI Pattern: UpdateEnvVar [variable: 'destination', value: 'Los Angeles, CA']
        manager.update_flight_env_var("destination", "Los Angeles, CA")
        self.assertEqual(manager.get_flight_env_var("destination"), "Los Angeles, CA")
        
        # DI Pattern: UpdateEnvVar [variable: 'num_adult_passengers', value: 2]
        manager.update_flight_env_var("num_adult_passengers", 2)
        self.assertEqual(manager.get_flight_env_var("num_adult_passengers"), 2)
    
    def test_flight_booking_conversation_flow(self):
        """Test complete flight booking conversation flow with environment variables."""
        manager = ConversationStateManager()
        
        # Step 1: Collect origin city
        manager.update_flight_env_var("origin", "New York, NY")
        self.assertEqual(manager.get_flight_env_var("origin"), "New York, NY")
        
        # Step 2: Collect destination city
        manager.update_flight_env_var("destination", "Los Angeles, CA")
        self.assertEqual(manager.get_flight_env_var("destination"), "Los Angeles, CA")
        
        # Step 3: Collect dates
        manager.update_flight_env_var("earliest_departure_date", "2025-12-25")
        manager.update_flight_env_var("latest_departure_date", "2025-12-25")
        manager.update_flight_env_var("earliest_return_date", "2025-12-30")
        manager.update_flight_env_var("latest_return_date", "2025-12-30")
        
        # Step 4: Collect passenger count
        manager.update_flight_env_var("num_adult_passengers", 2)
        manager.update_flight_env_var("num_child_passengers", 1)
        
        # Check if search is complete
        self.assertTrue(manager.is_flight_search_complete())
        
        # Step 5: Select flight
        selected_flight = {
            "airline": "American Airlines",
            "flight_number": "AA101",
            "price": 550.0,
            "departure_time": "10:00",
            "arrival_time": "13:00"
        }
        manager.update_flight_env_var("selected_flight", selected_flight)
        
        # Step 6: Provide traveler information
        travelers = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-01"
            },
            {
                "first_name": "Jane",
                "last_name": "Doe",
                "date_of_birth": "1992-05-15"
            }
        ]
        manager.update_flight_env_var("travelers", travelers)
        
        # Check if booking is ready
        self.assertTrue(manager.is_booking_ready())
        
        # Step 7: Complete booking
        manager.update_flight_env_var("booking_confirmation", "ABC123")
        self.assertEqual(manager.get_flight_env_var("booking_confirmation"), "ABC123")
    
    def test_environment_variable_persistence(self):
        """Test environment variable persistence across sessions."""
        # Create first session
        manager1 = ConversationStateManager(session_id="test_session_001")
        manager1.update_flight_env_var("origin", "New York, NY")
        manager1.update_flight_env_var("destination", "Los Angeles, CA")
        
        # Create second session with same ID (simulating session restoration)
        manager2 = ConversationStateManager(session_id="test_session_001")
        
        # Environment variables should be loaded from database
        # Note: This test may not work without actual database persistence
        # but it demonstrates the intended behavior
        self.assertEqual(manager2.get_flight_env_var("origin"), "New York, NY")
        self.assertEqual(manager2.get_flight_env_var("destination"), "Los Angeles, CA")


if __name__ == "__main__":
    unittest.main()