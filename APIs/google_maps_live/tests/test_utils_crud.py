"""
Test suite for CRUD utility functions in the Google Maps Live API.
"""

import unittest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_maps_live.SimulationEngine.db import DB, save_state, load_state
from google_maps_live.SimulationEngine import utils


class TestUtilsCrud(BaseTestCaseWithErrorHandler):
    
    def setUp(self):
        """Set up a clean test database before each test."""
        # Store original DB state
        self.original_db = DB.copy()
        # Clear DB for clean testing
        DB.clear()
        # Don't set default keys - let tests set what they need
        
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp()
        self.test_filepath = os.path.join(self.test_dir, 'test_db.json')

    def tearDown(self):
        """Reset the database after each test."""
        # Restore original DB state
        DB.clear()
        DB.update(self.original_db)
        
        # Clean up test files
        if os.path.exists(self.test_filepath):
            os.remove(self.test_filepath)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def validate_db(self):
        """Validate the current state of the database."""
        # Basic validation that DB is a dictionary
        self.assertIsInstance(DB, dict)
        # Check that required keys exist (only if they were set in setUp)
        if "recent_searches" in DB:
            self.assertIsInstance(DB["recent_searches"], dict)
        if "user_locations" in DB:
            self.assertIsInstance(DB["user_locations"], dict)
        if "search_history" in DB:
            self.assertIsInstance(DB["search_history"], dict)

    # region Recent Searches CRUD Tests
    def test_add_recent_search_create(self):
        """Test creating a new recent search entry."""
        parameters = {"destination": "San Francisco, CA", "origin": "Mountain View, CA"}
        result = {"map_url": "https://maps.google.com", "travel_mode": "driving"}
        
        utils.add_recent_search("find_directions", parameters, result)
        
        # Validate database state
        self.validate_db()
        self.assertIn("recent_searches", DB)
        self.assertIn("find_directions", DB["recent_searches"])
        
        # Check that the search was added
        searches = DB["recent_searches"]["find_directions"]
        self.assertEqual(len(searches), 1)
        self.assertEqual(searches[0]["parameters"], parameters)
        self.assertEqual(searches[0]["result"], result)

    def test_add_recent_search_update_existing(self):
        """Test updating an existing recent search endpoint."""
        # Add first search
        parameters1 = {"destination": "San Francisco, CA", "origin": "Mountain View, CA"}
        result1 = {"map_url": "https://maps.google.com", "travel_mode": "driving"}
        utils.add_recent_search("find_directions", parameters1, result1)
        
        # Add second search to same endpoint
        parameters2 = {"destination": "Palo Alto, CA", "origin": "San Jose, CA"}
        result2 = {"map_url": "https://maps.google.com", "travel_mode": "walking"}
        utils.add_recent_search("find_directions", parameters2, result2)
        
        # Validate database state
        self.validate_db()
        
        # Check that both searches are present
        searches = DB["recent_searches"]["find_directions"]
        self.assertEqual(len(searches), 2)
        # Most recent should be first
        self.assertEqual(searches[0]["parameters"], parameters2)
        self.assertEqual(searches[1]["parameters"], parameters1)

    def test_add_recent_search_multiple_endpoints(self):
        """Test adding searches to multiple endpoints."""
        # Add to find_directions
        utils.add_recent_search("find_directions", {"dest": "SF"}, {"result": "directions"})
        
        # Add to navigate
        utils.add_recent_search("navigate", {"dest": "PA"}, {"result": "navigation"})
        
        # Add to query_places
        utils.add_recent_search("query_places", {"query": "restaurants"}, {"result": "places"})
        
        # Validate database state
        self.validate_db()
        
        # Check that all endpoints have searches
        self.assertIn("find_directions", DB["recent_searches"])
        self.assertIn("navigate", DB["recent_searches"])
        self.assertIn("query_places", DB["recent_searches"])
        
        # Check counts
        self.assertEqual(len(DB["recent_searches"]["find_directions"]), 1)
        self.assertEqual(len(DB["recent_searches"]["navigate"]), 1)
        self.assertEqual(len(DB["recent_searches"]["query_places"]), 1)

    def test_add_recent_search_max_limit(self):
        """Test that recent searches are limited to 50 entries per endpoint."""
        # Add 55 searches to the same endpoint
        for i in range(55):
            parameters = {"destination": f"Location {i}", "origin": f"Origin {i}"}
            result = {"map_url": f"https://maps.google.com/{i}", "travel_mode": "driving"}
            utils.add_recent_search("find_directions", parameters, result)
        
        # Validate database state
        self.validate_db()
        
        # Check that only 50 searches are kept
        searches = DB["recent_searches"]["find_directions"]
        self.assertLessEqual(len(searches), 50)
        
        # Most recent should be first
        self.assertEqual(searches[0]["parameters"]["destination"], "Location 54")

    def test_add_recent_search_duplicate_entries(self):
        """Test that duplicate searches are allowed."""
        parameters = {"destination": "San Francisco, CA", "origin": "Mountain View, CA"}
        result = {"map_url": "https://maps.google.com", "travel_mode": "driving"}
        
        # Add the same search twice
        utils.add_recent_search("find_directions", parameters, result)
        utils.add_recent_search("find_directions", parameters, result)
        
        # Validate database state
        self.validate_db()
        
        # Both entries should be present
        searches = DB["recent_searches"]["find_directions"]
        self.assertEqual(len(searches), 2)
        self.assertEqual(searches[0]["parameters"], parameters)
        self.assertEqual(searches[1]["parameters"], parameters)

    def test_add_recent_search_error_handling(self):
        """Test error handling in add_recent_search."""
        # Test with invalid parameters (should not crash)
        utils.add_recent_search("find_directions", None, None)
        
        # Validate database state
        self.validate_db()
        
        # Should still have the endpoint
        self.assertIn("find_directions", DB["recent_searches"])

    def test_get_recent_searches_empty(self):
        """Test getting recent searches for empty endpoint."""
        searches = utils.get_recent_searches("nonexistent_endpoint")
        self.assertEqual(searches, [])
        
        # Validate database state
        self.validate_db()

    def test_get_recent_searches_with_limit(self):
        """Test getting recent searches with max_results limit."""
        # Add 10 searches
        for i in range(10):
            parameters = {"destination": f"Location {i}", "origin": f"Origin {i}"}
            result = {"map_url": f"https://maps.google.com/{i}", "travel_mode": "driving"}
            utils.add_recent_search("find_directions", parameters, result)
        
        # Get only 3 most recent
        searches = utils.get_recent_searches("find_directions", max_results=3)
        self.assertEqual(len(searches), 3)
        
        # Most recent should be first
        self.assertEqual(searches[0]["parameters"]["destination"], "Location 9")
        self.assertEqual(searches[2]["parameters"]["destination"], "Location 7")
        
        # Validate database state
        self.validate_db()

    def test_get_recent_searches_default_limit(self):
        """Test that default max_results is 5."""
        # Add 10 searches
        for i in range(10):
            parameters = {"destination": f"Location {i}", "origin": f"Origin {i}"}
            result = {"map_url": f"https://maps.google.com/{i}", "travel_mode": "driving"}
            utils.add_recent_search("find_directions", parameters, result)
        
        # Get with default limit
        searches = utils.get_recent_searches("find_directions")
        self.assertEqual(len(searches), 5)
        
        # Validate database state
        self.validate_db()

    def test_get_recent_searches_all_endpoints(self):
        """Test getting searches from all endpoints."""
        # Add searches to multiple endpoints
        utils.add_recent_search("find_directions", {"dest": "SF"}, {"result": "directions"})
        utils.add_recent_search("navigate", {"dest": "PA"}, {"result": "navigation"})
        utils.add_recent_search("query_places", {"query": "restaurants"}, {"result": "places"})
        
        # Get searches from each endpoint
        directions_searches = utils.get_recent_searches("find_directions")
        navigate_searches = utils.get_recent_searches("navigate")
        places_searches = utils.get_recent_searches("query_places")
        
        # Validate results
        self.assertEqual(len(directions_searches), 1)
        self.assertEqual(len(navigate_searches), 1)
        self.assertEqual(len(places_searches), 1)
        
        # Validate database state
        self.validate_db()
    # endregion

    # region Database State Management Tests
    def test_save_state_create_file(self):
        """Test that save_state creates a file."""
        # Add some data to DB
        DB["recent_searches"] = {
            "find_directions": [{"parameters": {"dest": "SF"}, "result": {"result": "directions"}}]
        }
        DB["user_locations"] = {"home": {"lat": 37.7749, "lng": -122.4194}}
        
        # Save state
        save_state(self.test_filepath)
        
        # Check if file was created
        self.assertTrue(os.path.exists(self.test_filepath))
        
        # Validate database state
        self.validate_db()

    def test_save_state_overwrite_existing(self):
        """Test that save_state overwrites existing files."""
        # Create initial file with old data
        old_data = {"old": "data", "version": "1.0"}
        with open(self.test_filepath, 'w') as f:
            json.dump(old_data, f)
        
        # Add new data to DB
        new_data = {"new": "data", "version": "2.0", "recent_searches": {"test": []}}
        DB.update(new_data)
        
        # Save the new state
        save_state(self.test_filepath)
        
        # Verify the file was overwritten with new data
        with open(self.test_filepath, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, new_data)
        self.assertNotIn("old", saved_data)
        
        # Validate database state
        self.validate_db()

    def test_load_state_from_file(self):
        """Test that load_state loads data from file."""
        # Create test file with data
        test_data = {
            "recent_searches": {"test_endpoint": [{"parameters": {"dest": "SF"}, "result": {"result": "test"}}]},
            "user_locations": {"home": {"lat": 37.7749, "lng": -122.4194}}
        }
        with open(self.test_filepath, 'w') as f:
            json.dump(test_data, f)
        
        # Clear DB
        DB.clear()
        self.assertEqual(DB, {})
        
        # Load state from file
        load_state(self.test_filepath)
        
        # Verify data was loaded
        self.assertEqual(DB["recent_searches"], test_data["recent_searches"])
        self.assertEqual(DB["user_locations"], test_data["user_locations"])
        
        # Validate database state
        self.validate_db()

    def test_load_state_clears_existing_data(self):
        """Test that load_state clears existing data before loading new data."""
        # Add existing data to DB
        DB.update({"existing": "data", "should": "be_cleared"})
        
        # Create test file with new data
        new_data = {"new": "data", "recent_searches": {"test": []}}
        with open(self.test_filepath, 'w') as f:
            json.dump(new_data, f)
        
        # Load the new state
        load_state(self.test_filepath)
        
        # Verify only the new data exists
        self.assertEqual(DB, new_data)
        self.assertNotIn("existing", DB)
        self.assertNotIn("should", DB)
        
        # Validate database state
        self.validate_db()

    def test_load_state_nonexistent_file(self):
        """Test that loading from a non-existent file raises an error."""
        # Attempt to load from a file that does not exist
        self.assert_error_behavior(
            lambda: load_state('nonexistent_filepath.json'),
            FileNotFoundError,
            "[Errno 2] No such file or directory: 'nonexistent_filepath.json'"
        )
        
        # The DB state should not have changed (DB.clear() was called in setUp)
        self.assertEqual(DB, {})

    def test_load_state_invalid_json(self):
        """Test that load_state handles invalid JSON gracefully."""
        # Create file with invalid JSON
        with open(self.test_filepath, 'w') as f:
            f.write('{"invalid": json, missing: quotes}')
        
        # Loading invalid JSON should raise an error
        self.assert_error_behavior(
            lambda: load_state(self.test_filepath),
            json.JSONDecodeError,
            "Expecting value: line 1 column 13 (char 12)"
        )

    def test_save_and_load_state_roundtrip(self):
        """Test that save_state and load_state work together."""
        # Add test data to DB
        test_data = {
            "recent_searches": {
                "find_directions": [{"parameters": {"dest": "SF"}, "result": {"result": "directions"}}],
                "navigate": [{"parameters": {"dest": "PA"}, "result": {"result": "navigation"}}]
            },
            "user_locations": {"home": {"lat": 37.7749, "lng": -122.4194}}
        }
        DB.update(test_data)
        
        # Save state
        save_state(self.test_filepath)
        
        # Clear DB
        DB.clear()
        self.assertEqual(DB, {})
        
        # Load state
        load_state(self.test_filepath)
        
        # Verify data was restored
        self.assertEqual(DB["recent_searches"], test_data["recent_searches"])
        self.assertEqual(DB["user_locations"], test_data["user_locations"])
        
        # Validate database state
        self.validate_db()

    def test_save_state_json_formatting(self):
        """Test that save_state creates properly formatted JSON."""
        # Add test data to DB
        test_data = {
            "nested": {
                "data": [1, 2, 3],
                "metadata": {"count": 3, "type": "array"}
            }
        }
        DB.update(test_data)
        
        # Save the state
        save_state(self.test_filepath)
        
        # Verify the JSON is properly formatted (indented)
        with open(self.test_filepath, 'r') as f:
            content = f.read()
        
        # Check that the content is valid JSON
        parsed_content = json.loads(content)
        self.assertEqual(parsed_content, test_data)
        
        # Check that it's formatted (indented) - should contain newlines
        self.assertIn('\n', content)
        
        # Validate database state
        self.validate_db()

    def test_load_state_empty_file(self):
        """Test that load_state handles empty JSON files correctly."""
        # Create empty JSON file
        with open(self.test_filepath, 'w') as f:
            json.dump({}, f)
        
        # Load the empty state
        load_state(self.test_filepath)
        
        # Verify the DB is now empty
        self.assertEqual(DB, {})
        
        # Validate database state
        self.validate_db()

    def test_multiple_save_operations(self):
        """Test that multiple save operations work correctly."""
        # First save
        test_data_1 = {"version": "1.0", "recent_searches": {"test": []}}
        DB.update(test_data_1)
        save_state(self.test_filepath)
        
        # Second save
        test_data_2 = {"version": "2.0", "recent_searches": {"test": []}, "additional": "info"}
        DB.clear()
        DB.update(test_data_2)
        save_state(self.test_filepath)
        
        # Verify the file contains the latest data
        with open(self.test_filepath, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, test_data_2)
        
        # Validate database state
        self.validate_db()

    def test_db_persistence_across_operations(self):
        """Test that DB state persists correctly across multiple operations."""
        # Initial state
        initial_data = {"initial": "data", "recent_searches": {}}
        DB.update(initial_data)
        
        # Save initial state
        save_state(self.test_filepath)
        
        # Modify DB
        DB.update({"modified": "data"})
        
        # Save modified state
        save_state(self.test_filepath)
        
        # Clear and reload
        DB.clear()
        load_state(self.test_filepath)
        
        # Should have the modified data
        expected_data = {"initial": "data", "modified": "data", "recent_searches": {}}
        self.assertEqual(DB, expected_data)
        
        # Validate database state
        self.validate_db()
    # endregion

    # region Error Handling Tests
    def test_add_recent_search_with_exception(self):
        """Test that add_recent_search handles exceptions gracefully."""
        # Mock print_log to avoid output during testing
        with patch('google_maps_live.SimulationEngine.utils.print_log') as mock_print:
            # This should not crash even with invalid data
            utils.add_recent_search("test", "invalid_parameters", "invalid_result")
            
            # Should have logged an error (if an exception occurred)
            # Note: add_recent_search is designed to handle exceptions gracefully
            # so it may not always call print_log
            
            # Validate database state
            self.validate_db()

    def test_get_recent_searches_with_corrupted_db(self):
        """Test that get_recent_searches handles corrupted database gracefully."""
        # Corrupt the database structure
        DB["recent_searches"] = "not_a_dict"
        
        # This should raise an AttributeError since the function tries to call .get() on a string
        self.assert_error_behavior(
            lambda: utils.get_recent_searches("any_endpoint"),
            AttributeError,
            "'str' object has no attribute 'get'"
        )
        
        # Validate database state (should handle corruption gracefully)
        self.assertIsInstance(DB, dict)

    def test_save_state_with_permission_error(self):
        """Test that save_state handles permission errors gracefully."""
        # Try to save to a directory that doesn't exist
        invalid_path = "/invalid/directory/test.json"
        
        self.assert_error_behavior(
            lambda: save_state(invalid_path),
            FileNotFoundError,
            "[Errno 2] No such file or directory: '/invalid/directory/test.json'"
        )
        
        # Validate database state
        self.validate_db()

    def test_load_state_with_corrupted_file(self):
        """Test that load_state handles corrupted files gracefully."""
        # Create a corrupted file
        with open(self.test_filepath, 'w') as f:
            f.write('{"incomplete": json')
        
        # Should raise JSONDecodeError
        self.assert_error_behavior(
            lambda: load_state(self.test_filepath),
            json.JSONDecodeError,
            "Expecting value: line 1 column 16 (char 15)"
        )
        
        # Validate database state
        self.validate_db()
    # endregion

    # region Integration Tests
    def test_full_workflow_integration(self):
        """Test the complete workflow of adding searches, saving, and loading."""
        # Add searches to multiple endpoints
        utils.add_recent_search("find_directions", {"dest": "SF"}, {"result": "directions"})
        utils.add_recent_search("navigate", {"dest": "PA"}, {"result": "navigation"})
        utils.add_recent_search("query_places", {"query": "restaurants"}, {"result": "places"})
        
        # Save state
        save_state(self.test_filepath)
        
        # Verify file was created and contains data
        self.assertTrue(os.path.exists(self.test_filepath))
        with open(self.test_filepath, 'r') as f:
            saved_data = json.load(f)
        
        self.assertIn("recent_searches", saved_data)
        self.assertIn("find_directions", saved_data["recent_searches"])
        self.assertIn("navigate", saved_data["recent_searches"])
        self.assertIn("query_places", saved_data["recent_searches"])
        
        # Clear DB and reload
        DB.clear()
        load_state(self.test_filepath)
        
        # Verify data was restored
        self.assertIn("recent_searches", DB)
        self.assertIn("find_directions", DB["recent_searches"])
        self.assertIn("navigate", DB["recent_searches"])
        self.assertIn("query_places", DB["recent_searches"])
        
        # Validate database state
        self.validate_db()

    def test_concurrent_operations(self):
        """Test that operations work correctly when performed in sequence."""
        # Add searches
        utils.add_recent_search("test1", {"param": "1"}, {"result": "1"})
        utils.add_recent_search("test2", {"param": "2"}, {"result": "2"})
        
        # Get searches
        searches1 = utils.get_recent_searches("test1")
        searches2 = utils.get_recent_searches("test2")
        
        # Save state
        save_state(self.test_filepath)
        
        # Load state
        load_state(self.test_filepath)
        
        # Verify all operations worked
        self.assertEqual(len(searches1), 1)
        self.assertEqual(len(searches2), 1)
        self.assertTrue(os.path.exists(self.test_filepath))
        
        # Validate database state
        self.validate_db()

    def test_data_integrity_across_operations(self):
        """Test that data integrity is maintained across all operations."""
        # Create complex data structure
        complex_data = {
            "recent_searches": {
                "endpoint1": [
                    {"parameters": {"complex": {"nested": [1, 2, 3]}}, "result": {"data": "value"}},
                    {"parameters": {"simple": "string"}, "result": {"number": 42}}
                ]
            },
            "user_locations": {
                "home": {"lat": 37.7749, "lng": -122.4194, "name": "Home"},
                "work": {"lat": 37.7849, "lng": -122.4094, "name": "Work"}
            }
        }
        
        # Add to DB
        DB.update(complex_data)
        
        # Save and reload
        save_state(self.test_filepath)
        DB.clear()
        load_state(self.test_filepath)
        
        # Verify data integrity
        self.assertEqual(DB["recent_searches"], complex_data["recent_searches"])
        self.assertEqual(DB["user_locations"], complex_data["user_locations"])
        
        # Validate database state
        self.validate_db()
    # endregion


if __name__ == '__main__':
    unittest.main()
