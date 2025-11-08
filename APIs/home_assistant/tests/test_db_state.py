"""
Test suite for home_assistant database state management functionality.

This test suite verifies:
1. Data save and load operations work correctly with various data structures
2. Backward compatibility is maintained with legacy data formats
3. Database state consistency across save/load cycles
4. Error handling for invalid file operations
"""

import unittest
import tempfile
import os
import json
from common_utils.base_case import BaseTestCaseWithErrorHandler
from home_assistant.SimulationEngine.db import DB, save_state, load_state, get_minified_state


class TestDBState(BaseTestCaseWithErrorHandler):
    """Test suite for database state management functionality."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Store original DB state to restore after each test
        self.original_db_state = DB.copy()
        
        # Clear DB to ensure clean state for each test
        DB.clear()
        
        # Path to test assets directory
        self.assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        
        # Define paths to test data files
        self.modern_data_path = os.path.join(self.assets_dir, "modern_test_data.json")
        self.legacy_data_path = os.path.join(self.assets_dir, "legacy_test_data.json")
        self.empty_data_path = os.path.join(self.assets_dir, "empty_test_data.json")
        self.complex_data_path = os.path.join(self.assets_dir, "complex_test_data.json")
        
        # Create temporary file for testing save operations
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.temp_file_path = self.temp_file.name

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original DB state
        DB.clear()
        DB.update(self.original_db_state)
        
        # Clean up temporary file
        if os.path.exists(self.temp_file_path):
            os.unlink(self.temp_file_path)

    def test_save_and_load_modern_data_exact_match(self):
        """
        DATA SAVE AND LOAD TEST: Verify modern data can be saved and loaded with exact match.
        
        This test ensures that data saved to a file can be loaded back exactly as it was,
        maintaining all data structure integrity and values.
        """
        # Load modern test data into DB
        load_state(self.modern_data_path)
        original_data = get_minified_state().copy()
        
        # Save the data to temporary file
        save_state(self.temp_file_path)
        
        # Clear DB and load from saved file
        DB.clear()
        load_state(self.temp_file_path)
        loaded_data = get_minified_state()
        
        # Verify exact match between original and loaded data
        self.assertEqual(original_data, loaded_data, "Loaded data must match original data exactly")
        
        # Verify specific data structure elements are preserved
        self.assertIn("environment", loaded_data)
        self.assertIn("automations", loaded_data)
        self.assertIn("metadata", loaded_data)
        
        # Verify nested data integrity
        devices = loaded_data["environment"]["home_assistant"]["devices"]
        self.assertEqual(devices["LIGHT_001"]["attributes"]["brightness"], 75)
        self.assertEqual(devices["DOOR_001"]["attributes"]["locked"], True)
        self.assertEqual(loaded_data["metadata"]["total_devices"], 3)

    def test_save_and_load_empty_data_structure(self):
        """
        DATA SAVE AND LOAD TEST: Verify empty data structures are handled correctly.
        
        This test ensures that empty dictionaries can be saved and loaded properly,
        which is important for initialization and reset scenarios.
        """
        # Load empty test data
        load_state(self.empty_data_path)
        original_data = get_minified_state().copy()
        
        # Verify original data is empty
        self.assertEqual(original_data, {}, "Empty data should be an empty dictionary")
        
        # Save empty data to temporary file
        save_state(self.temp_file_path)
        
        # Add some data to DB, then load empty data back
        DB.update({"test_key": "test_value"})
        load_state(self.temp_file_path)
        loaded_data = get_minified_state()
        
        # Verify loaded data is empty and previous data was cleared
        self.assertEqual(loaded_data, {}, "Loaded empty data should clear existing data")
        self.assertNotIn("test_key", loaded_data, "Previous data should be completely cleared")

    def test_save_and_load_complex_nested_data_integrity(self):
        """
        DATA SAVE AND LOAD TEST: Verify complex nested data structures maintain integrity.
        
        This test ensures that deeply nested dictionaries, arrays, and mixed data types
        are preserved correctly through save/load cycles.
        """
        # Load complex test data
        load_state(self.complex_data_path)
        original_data = get_minified_state().copy()
        
        # Save and reload data
        save_state(self.temp_file_path)
        DB.clear()
        load_state(self.temp_file_path)
        loaded_data = get_minified_state()
        
        # Verify exact match for complex structure
        self.assertEqual(original_data, loaded_data, "Complex nested data must be preserved exactly")
        
        # Verify specific nested structures are intact
        light_color = loaded_data["environment"]["home_assistant"]["devices"]["LIGHT_001"]["attributes"]["color"]
        self.assertEqual(light_color["r"], 255)
        self.assertEqual(light_color["g"], 128)
        self.assertEqual(light_color["b"], 0)
        
        # Verify arrays are preserved
        effects = loaded_data["environment"]["home_assistant"]["devices"]["LIGHT_001"]["attributes"]["effects"]
        self.assertEqual(effects, ["breathing", "rainbow", "strobe"])
        
        # Verify deeply nested objects
        sensors = loaded_data["environment"]["home_assistant"]["devices"]["THERMOSTAT_001"]["attributes"]["sensors"]
        self.assertEqual(sensors["indoor"]["temperature"], 72.5)
        self.assertEqual(sensors["outdoor"]["humidity"], 65.3)
        
        # Verify automation actions array structure
        actions = loaded_data["automations"]["morning_routine"]["actions"]
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0]["device"], "LIGHT_001")
        self.assertEqual(actions[1]["temperature"], 72)

    def test_backward_compatibility_legacy_data_format(self):
        """
        BACKWARD COMPATIBILITY TEST: Verify legacy data format loads correctly.
        
        This test ensures that older data formats can still be loaded and accessed
        properly, maintaining backward compatibility with previous versions.
        """
        # Load legacy test data
        load_state(self.legacy_data_path)
        loaded_data = get_minified_state()
        
        # Verify legacy structure is loaded correctly
        self.assertIn("environment", loaded_data)
        self.assertIn("automations", loaded_data)
        
        # Verify legacy device naming convention is preserved
        devices = loaded_data["environment"]["home_assistant"]["devices"]
        self.assertIn("light.living_room", devices)
        self.assertIn("switch.kitchen", devices)
        self.assertIn("sensor.temperature", devices)
        
        # Verify legacy device structure
        light_device = devices["light.living_room"]
        self.assertEqual(light_device["type"], "light")
        self.assertEqual(light_device["attributes"]["state"], "off")
        
        # Verify legacy automation format
        automations = loaded_data["automations"]
        self.assertIn("automation.morning_routine", automations)
        self.assertIn("automation.night_mode", automations)
        
        morning_routine = automations["automation.morning_routine"]
        self.assertEqual(morning_routine["triggered"], False)
        self.assertEqual(morning_routine["description"], "Turns on lights and coffee")

    def test_backward_compatibility_legacy_vs_modern_structure_comparison(self):
        """
        BACKWARD COMPATIBILITY TEST: Compare legacy and modern data structures.
        
        This test verifies that both legacy and modern formats can coexist and
        that essential data elements remain accessible regardless of format.
        """
        # Load legacy data first
        load_state(self.legacy_data_path)
        legacy_data = get_minified_state().copy()
        
        # Load modern data
        load_state(self.modern_data_path)
        modern_data = get_minified_state().copy()
        
        # Verify both have required top-level structure
        for data, data_type in [(legacy_data, "legacy"), (modern_data, "modern")]:
            self.assertIn("environment", data, f"{data_type} data must have environment section")
            self.assertIn("automations", data, f"{data_type} data must have automations section")
            
            # Verify home_assistant structure exists
            self.assertIn("home_assistant", data["environment"], 
                         f"{data_type} data must have home_assistant in environment")
            self.assertIn("devices", data["environment"]["home_assistant"],
                         f"{data_type} data must have devices in home_assistant")
        
        # Verify device count differences are expected
        legacy_devices = legacy_data["environment"]["home_assistant"]["devices"]
        modern_devices = modern_data["environment"]["home_assistant"]["devices"]
        
        self.assertEqual(len(legacy_devices), 3, "Legacy data should have 3 devices")
        self.assertEqual(len(modern_devices), 3, "Modern data should have 3 devices")
        
        # Verify all devices have required attributes structure
        for device_id, device in legacy_devices.items():
            self.assertIn("type", device, f"Legacy device {device_id} must have type")
            self.assertIn("attributes", device, f"Legacy device {device_id} must have attributes")
        
        for device_id, device in modern_devices.items():
            self.assertIn("type", device, f"Modern device {device_id} must have type")
            self.assertIn("attributes", device, f"Modern device {device_id} must have attributes")

    def test_data_persistence_across_multiple_save_load_cycles(self):
        """
        DATA SAVE AND LOAD TEST: Verify data integrity across multiple save/load cycles.
        
        This test ensures that repeated save and load operations don't introduce
        data corruption or gradual data loss.
        """
        # Start with modern test data
        load_state(self.modern_data_path)
        original_data = get_minified_state().copy()
        
        # Perform multiple save/load cycles
        for cycle in range(5):
            # Save current state
            save_state(self.temp_file_path)
            
            # Clear and reload
            DB.clear()
            load_state(self.temp_file_path)
            
            # Verify data integrity after each cycle
            current_data = get_minified_state()
            self.assertEqual(
                original_data, 
                current_data, 
                f"Data integrity must be maintained after cycle {cycle + 1}"
            )
        
        # Verify specific critical data points are still intact
        final_data = get_minified_state()
        self.assertEqual(final_data["metadata"]["version"], "2.1.0")
        self.assertEqual(final_data["automations"]["morning_routine"]["triggered"], False)
        self.assertEqual(
            final_data["environment"]["home_assistant"]["devices"]["LIGHT_001"]["attributes"]["brightness"], 
            75
        )

    def test_get_minified_state_returns_current_db_state(self):
        """
        DATA SAVE AND LOAD TEST: Verify get_minified_state returns current DB state.
        
        This test ensures that get_minified_state always returns the current
        state of the database and reflects any changes made to DB.
        """
        # Start with empty DB
        self.assertEqual(get_minified_state(), {}, "get_minified_state should return empty dict for empty DB")
        
        # Add data directly to DB
        test_data = {
            "test_section": {
                "test_key": "test_value",
                "test_number": 42,
                "test_boolean": True
            }
        }
        DB.update(test_data)
        
        # Verify get_minified_state reflects the change
        current_state = get_minified_state()
        self.assertEqual(current_state, test_data, "get_minified_state should reflect DB changes")
        
        # Modify DB and verify changes are reflected
        DB["test_section"]["test_key"] = "modified_value"
        updated_state = get_minified_state()
        self.assertEqual(updated_state["test_section"]["test_key"], "modified_value")
        
        # Clear DB and verify get_minified_state reflects clearing
        DB.clear()
        cleared_state = get_minified_state()
        self.assertEqual(cleared_state, {}, "get_minified_state should reflect DB clearing")

    def test_load_state_clears_existing_data_before_loading(self):
        """
        DATA SAVE AND LOAD TEST: Verify load_state clears existing data before loading new data.
        
        This test ensures that loading new data completely replaces existing data
        rather than merging with it, preventing data contamination.
        """
        # Add initial data to DB
        initial_data = {
            "initial_section": {
                "initial_key": "initial_value",
                "should_be_removed": True
            }
        }
        DB.update(initial_data)
        
        # Verify initial data is in DB
        self.assertIn("initial_section", get_minified_state())
        self.assertEqual(get_minified_state()["initial_section"]["initial_key"], "initial_value")
        
        # Load different data from file
        load_state(self.modern_data_path)
        loaded_state = get_minified_state()
        
        # Verify initial data was completely cleared
        self.assertNotIn("initial_section", loaded_state, "Initial data should be completely cleared")
        self.assertNotIn("initial_key", str(loaded_state), "No trace of initial data should remain")
        
        # Verify new data was loaded correctly
        self.assertIn("environment", loaded_state)
        self.assertIn("metadata", loaded_state)
        self.assertEqual(loaded_state["metadata"]["version"], "2.1.0")

    def test_save_state_file_error_handling_invalid_path(self):
        """
        ERROR HANDLING TEST: Verify save_state handles invalid file paths gracefully.
        
        This test ensures that attempting to save to invalid paths raises
        appropriate exceptions.
        """
        # Load some data to save
        load_state(self.modern_data_path)
        
        # Test saving to invalid directory path
        invalid_path = "/invalid/directory/that/does/not/exist/test.json"
        self.assert_error_behavior(
            save_state,
            FileNotFoundError,
            "[Errno 2] No such file or directory: '/invalid/directory/that/does/not/exist/test.json'",
            None,
            invalid_path
        )

    def test_load_state_file_error_handling_nonexistent_file(self):
        """
        ERROR HANDLING TEST: Verify load_state handles nonexistent files gracefully.
        
        This test ensures that attempting to load from nonexistent files raises
        appropriate exceptions.
        """
        nonexistent_path = "/nonexistent/file/path/test.json"
        self.assert_error_behavior(
            load_state,
            FileNotFoundError,
            "[Errno 2] No such file or directory: '/nonexistent/file/path/test.json'",
            None,
            nonexistent_path
        )

    def test_load_state_file_error_handling_invalid_json(self):
        """
        ERROR HANDLING TEST: Verify load_state handles invalid JSON gracefully.
        
        This test ensures that attempting to load malformed JSON files raises
        appropriate exceptions.
        """
        # Create temporary file with invalid JSON
        invalid_json_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        invalid_json_file.write('{"invalid": json content}')
        invalid_json_file.close()
        
        # Attempt to load invalid JSON
        self.assert_error_behavior(
            load_state,
            json.JSONDecodeError,
            "Expecting value: line 1 column 13 (char 12)",
            None,
            invalid_json_file.name
        )
        
        # Clean up
        os.unlink(invalid_json_file.name)

    def test_save_and_load_preserves_data_types(self):
        """
        DATA SAVE AND LOAD TEST: Verify all Python data types are preserved correctly.
        
        This test ensures that various Python data types (strings, numbers, booleans,
        lists, dictionaries) maintain their types through save/load operations.
        """
        # Create test data with various data types
        test_data = {
            "string_value": "test_string",
            "integer_value": 42,
            "float_value": 3.14159,
            "boolean_true": True,
            "boolean_false": False,
            "list_value": [1, "two", 3.0, True, None],
            "dict_value": {
                "nested_string": "nested_value",
                "nested_number": 100,
                "nested_list": ["a", "b", "c"]
            },
            "null_value": None
        }
        
        # Load test data into DB
        DB.update(test_data)
        
        # Save and reload
        save_state(self.temp_file_path)
        DB.clear()
        load_state(self.temp_file_path)
        loaded_data = get_minified_state()
        
        # Verify data types are preserved
        self.assertIsInstance(loaded_data["string_value"], str)
        self.assertIsInstance(loaded_data["integer_value"], int)
        self.assertIsInstance(loaded_data["float_value"], float)
        self.assertIsInstance(loaded_data["boolean_true"], bool)
        self.assertIsInstance(loaded_data["boolean_false"], bool)
        self.assertIsInstance(loaded_data["list_value"], list)
        self.assertIsInstance(loaded_data["dict_value"], dict)
        self.assertIsNone(loaded_data["null_value"])
        
        # Verify exact values are preserved
        self.assertEqual(loaded_data["string_value"], "test_string")
        self.assertEqual(loaded_data["integer_value"], 42)
        self.assertAlmostEqual(loaded_data["float_value"], 3.14159, places=5)
        self.assertEqual(loaded_data["boolean_true"], True)
        self.assertEqual(loaded_data["boolean_false"], False)
        self.assertEqual(loaded_data["list_value"], [1, "two", 3.0, True, None])
        self.assertEqual(loaded_data["dict_value"]["nested_string"], "nested_value")


if __name__ == "__main__":
    unittest.main()
