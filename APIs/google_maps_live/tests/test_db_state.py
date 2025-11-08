import unittest
import os
import json
import time
import tempfile
from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_maps_live.SimulationEngine.db import DB, save_state, load_state


class TestDBState(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test directory and reset DB."""
        super().setUp()
        # Store original DB state
        self.original_db = DB.copy()
        # Clear DB for clean testing
        DB.clear()
        
        # Create temporary test directory
        self.test_dir = tempfile.mkdtemp()
        self.test_filepath = os.path.join(self.test_dir, 'test_db.json')

    def tearDown(self):
        """Clean up test files and directory."""
        super().tearDown()
        # Restore original DB state
        DB.clear()
        DB.update(self.original_db)
        
        if os.path.exists(self.test_filepath):
            os.remove(self.test_filepath)
        if os.path.exists(self.test_dir) and not os.listdir(self.test_dir):
            os.rmdir(self.test_dir)

    def test_save_and_load_state(self):
        """Test that the DB state can be saved to and loaded from a file."""
        # 1. Add some data to the DB
        DB['user_locations'] = {
            'home': {'lat': 37.7749, 'lng': -122.4194, 'name': 'Home'},
            'work': {'lat': 37.7849, 'lng': -122.4094, 'name': 'Work'}
        }
        DB['recent_searches'] = ['San Francisco', 'New York', 'London']
        DB['favorites'] = {
            'places': ['Golden Gate Bridge', 'Alcatraz'],
            'routes': ['home_to_work', 'work_to_gym']
        }
        
        # Use json loads/dumps for a deep copy to compare later
        original_db = json.loads(json.dumps(DB))

        # 2. Save state
        save_state(self.test_filepath)

        # 3. Check if the file was created
        self.assertTrue(os.path.exists(self.test_filepath))

        # 4. Clear DB to ensure we are loading fresh data
        DB.clear()
        self.assertNotEqual(DB, original_db)

        # 5. Load state from file
        load_state(self.test_filepath)

        # 6. Assert that the data has been restored
        self.assertEqual(DB['user_locations'], original_db['user_locations'])
        self.assertEqual(DB['recent_searches'], original_db['recent_searches'])
        self.assertEqual(DB['favorites'], original_db['favorites'])
        self.assertEqual(DB, original_db)

    def test_load_state_nonexistent_file(self):
        """Test that loading from a non-existent file raises an error."""
        # Add some initial data to DB
        DB['user_locations'] = {'home': {'lat': 37.7749, 'lng': -122.4194}}
        initial_db = json.loads(json.dumps(DB))

        # Attempt to load from a file that does not exist
        self.assert_error_behavior(
            lambda: load_state('nonexistent_filepath.json'),
            FileNotFoundError,
            "[Errno 2] No such file or directory: 'nonexistent_filepath.json'"
        )

        # The DB state should not have changed
        self.assertEqual(DB, initial_db)

    def test_backward_compatibility_loading(self):
        """Test loading a DB state with missing keys (for backward compatibility)."""
        # 1. Create a test DB file that is missing some of the current DB keys
        old_format_db_data = {
            "user_locations": {"home": {"lat": 37.7749, "lng": -122.4194}},
            "recent_searches": ["San Francisco", "New York"]
            # This old format is missing 'favorites' and 'search_history'
        }
        with open(self.test_filepath, 'w') as f:
            json.dump(old_format_db_data, f)

        # 2. Clear the current DB
        DB.clear()
        self.assertEqual(DB, {})
        
        # 3. Load the old-format state
        load_state(self.test_filepath)

        # 4. Check that the loaded data is present
        self.assertEqual(DB['user_locations'], old_format_db_data['user_locations'])
        self.assertEqual(DB['recent_searches'], old_format_db_data['recent_searches'])

        # 5. Check that the keys that were missing in the old format are not present
        # (since this DB doesn't have default empty dicts like the notification API)
        self.assertNotIn('favorites', DB)
        self.assertNotIn('search_history', DB)

    def test_load_state_from_old_format(self):
        """Test loading from an old format database structure."""
        # Create old format data inline
        old_format_data = {
            "user_locations": {"home": {"lat": 37.7749, "lng": -122.4194}},
            "recent_searches": ["San Francisco", "New York"]
            # This old format is missing 'favorites' and 'search_history'
        }
        
        # Write old format data to test file
        with open(self.test_filepath, 'w') as f:
            json.dump(old_format_data, f)
        
        # Clear current DB
        DB.clear()
        self.assertEqual(DB, {})
        
        # Load old format data
        load_state(self.test_filepath)
        
        # Check that old format data is loaded correctly
        self.assertIn('user_locations', DB)
        self.assertIn('recent_searches', DB)
        
        # Check specific data
        self.assertEqual(DB['user_locations']['home']['lat'], 37.7749)
        self.assertEqual(DB['user_locations']['home']['lng'], -122.4194)
        self.assertEqual(len(DB['recent_searches']), 2)
        self.assertIn('San Francisco', DB['recent_searches'])
        
        # Check that newer fields are not present
        self.assertNotIn('favorites', DB)
        self.assertNotIn('places_cache', DB)
        self.assertNotIn('directions_cache', DB)

    def test_load_state_from_new_format(self):
        """Test loading from a new format database structure with additional fields."""
        # Create new format data inline
        new_format_data = {
            "user_locations": {
                "home": {
                    "lat": 37.7749, 
                    "lng": -122.4194, 
                    "name": "Home",
                    "timezone": "America/Los_Angeles"
                }
            },
            "recent_searches": ["San Francisco, CA", "New York, NY", "Tokyo, Japan"],
            "favorites": {
                "places": ["Golden Gate Bridge", "Alcatraz Island"],
                "routes": ["home_to_work"]
            },
            "places_cache": {
                "place_123": {"id": "place_123", "name": "Joe's Pizza"}
            }
        }
        
        # Write new format data to test file
        with open(self.test_filepath, 'w') as f:
            json.dump(new_format_data, f)
        
        # Clear current DB
        DB.clear()
        self.assertEqual(DB, {})
        
        # Load new format data
        load_state(self.test_filepath)
        
        # Check that new format data is loaded correctly
        self.assertIn('user_locations', DB)
        self.assertIn('recent_searches', DB)
        self.assertIn('favorites', DB)
        self.assertIn('places_cache', DB)
        
        # Check specific data
        self.assertEqual(DB['user_locations']['home']['timezone'], 'America/Los_Angeles')
        self.assertEqual(len(DB['recent_searches']), 3)
        self.assertIn('Tokyo, Japan', DB['recent_searches'])
        
        # Check newer fields
        self.assertEqual(len(DB['favorites']['places']), 2)
        self.assertEqual(len(DB['favorites']['routes']), 1)
        self.assertIn('Golden Gate Bridge', DB['favorites']['places'])

    def test_forward_compatibility_loading(self):
        """Test that loading newer data with additional fields works correctly."""
        # Create new format data inline
        new_format_data = {
            "user_locations": {
                "home": {
                    "lat": 37.7749, 
                    "lng": -122.4194, 
                    "timezone": "America/Los_Angeles"
                }
            },
            "favorites": {
                "places": ["Golden Gate Bridge", "Alcatraz Island"]
            },
            "places_cache": {
                "place_123": {"id": "place_123", "name": "Joe's Pizza"}
            }
        }
        
        # Write new format data to test file
        with open(self.test_filepath, 'w') as f:
            json.dump(new_format_data, f)
        
        # Start with minimal DB
        DB.clear()
        DB.update({
            "user_locations": {},
            "recent_searches": []
        })
        
        # Load new format data (should overwrite completely)
        load_state(self.test_filepath)
        
        # Check that all new fields are present
        self.assertIn('favorites', DB)
        self.assertIn('places_cache', DB)
        
        # Check that data is correctly loaded
        self.assertEqual(DB['user_locations']['home']['timezone'], 'America/Los_Angeles')
        self.assertEqual(len(DB['favorites']['places']), 2)

    def test_load_state_corrupted_file(self):
        """Test loading from a corrupted JSON file."""
        # Create corrupted JSON data inline
        corrupted_data = '{"user_locations": {"home": {"lat": 37.7749, "lng": -122.4194}}, "recent_searches": ["San Francisco", "New York"], "incomplete_object": {"missing_closing_brace": "value", "nested": {"also_incomplete": "missing_brace"}}, "favorites": {"places": ["Golden Gate Bridge", "Alcatraz Island"]}, "malformed_array": ["item1", "item2", "item3", "missing_comma" "item4"]}'
        
        # Write corrupted data to test file
        with open(self.test_filepath, 'w') as f:
            f.write(corrupted_data)
        
        # Clear current DB
        DB.clear()
        DB.update({"existing": "data"})
        
        # Loading corrupted JSON should raise an error
        self.assert_error_behavior(
            lambda: load_state(self.test_filepath),
            json.JSONDecodeError,
            "Expecting ',' delimiter: line 1 column 352 (char 351)"
        )
        
        # DB should remain unchanged
        self.assertEqual(DB, {"existing": "data"})

    def test_save_state_with_complex_data(self):
        """Test saving complex nested data structures."""
        complex_data = {
            "nested_objects": {
                "level1": {
                    "level2": {
                        "level3": {
                            "array": [1, 2, 3, {"nested": "value"}],
                            "boolean": True,
                            "null_value": None,
                            "number": 42.5
                        }
                    }
                }
            },
            "arrays": [
                {"item": 1, "metadata": {"type": "number"}},
                {"item": "string", "metadata": {"type": "text"}},
                {"item": [1, 2, 3], "metadata": {"type": "array"}}
            ]
        }
        
        DB.update(complex_data)
        save_state(self.test_filepath)
        
        # Verify the file was created and contains the data
        self.assertTrue(os.path.exists(self.test_filepath))
        
        with open(self.test_filepath, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, complex_data)
        
        # Test that we can load it back
        DB.clear()
        load_state(self.test_filepath)
        self.assertEqual(DB, complex_data)

    def test_save_state_unicode_handling(self):
        """Test that save_state handles Unicode characters correctly."""
        unicode_data = {
            "user_locations": {
                "café": {
                    "name": "Café de Paris",
                    "address": "Rue de la Paix, Paris, France",
                    "description": "Un excellent café avec du café délicieux"
                },
                "restaurant": {
                    "name": "寿司店",
                    "address": "東京, 日本",
                    "description": "最高の寿司を提供する店"
                }
            },
            "recent_searches": [
                "São Paulo, Brazil",
                "München, Germany",
                "Barcelona, España"
            ]
        }
        
        DB.update(unicode_data)
        save_state(self.test_filepath)
        
        # Verify the file was created
        self.assertTrue(os.path.exists(self.test_filepath))
        
        # Test that we can load it back with Unicode intact
        DB.clear()
        load_state(self.test_filepath)
        self.assertEqual(DB, unicode_data)
        
        # Check specific Unicode values
        self.assertEqual(DB['user_locations']['café']['name'], 'Café de Paris')
        self.assertEqual(DB['user_locations']['restaurant']['name'], '寿司店')
        self.assertIn('São Paulo, Brazil', DB['recent_searches'])

    def test_save_state_large_dataset(self):
        """Test saving a large dataset to ensure performance and correctness."""
        large_data = {}
        
        # Create large user_locations dataset
        large_data['user_locations'] = {}
        for i in range(1000):
            large_data['user_locations'][f'location_{i}'] = {
                'lat': 37.7749 + (i * 0.001),
                'lng': -122.4194 + (i * 0.001),
                'name': f'Location {i}',
                'address': f'{i} Test St, City, State',
                'metadata': {
                    'created_at': f'2024-01-{i%28+1:02d}T00:00:00Z',
                    'tags': [f'tag_{j}' for j in range(i % 5 + 1)]
                }
            }
        
        # Create large recent_searches dataset
        large_data['recent_searches'] = [f'Search Query {i}' for i in range(500)]
        
        # Create large search_history dataset
        large_data['search_history'] = {
            'find_directions': [
                {
                    'query': f'Route {i}',
                    'timestamp': f'2024-01-{i%28+1:02d}T{i%24:02d}:00:00Z',
                    'result_count': i % 10 + 1
                }
                for i in range(200)
            ]
        }
        
        DB.update(large_data)
        
        # Save the large dataset
        start_time = time.time()
        save_state(self.test_filepath)
        save_time = time.time() - start_time
        
        # Verify the file was created and check file size
        self.assertTrue(os.path.exists(self.test_filepath))
        file_size = os.path.getsize(self.test_filepath)
        self.assertGreater(file_size, 100000)  # Should be at least 100KB
        
        # Test loading the large dataset back
        DB.clear()
        start_time = time.time()
        load_state(self.test_filepath)
        load_time = time.time() - start_time
        
        # Verify data integrity
        self.assertEqual(len(DB['user_locations']), 1000)
        self.assertEqual(len(DB['recent_searches']), 500)
        self.assertEqual(len(DB['search_history']['find_directions']), 200)
        
        # Check specific data points
        self.assertEqual(DB['user_locations']['location_0']['name'], 'Location 0')
        self.assertEqual(DB['user_locations']['location_999']['name'], 'Location 999')
        self.assertEqual(DB['recent_searches'][0], 'Search Query 0')
        self.assertEqual(DB['recent_searches'][499], 'Search Query 499')
        
        # Performance assertions (should complete within reasonable time)
        self.assertLess(save_time, 5.0)  # Save should complete in under 5 seconds
        self.assertLess(load_time, 5.0)  # Load should complete in under 5 seconds

    def test_save_state_overwrites_existing_file(self):
        """Test that save_state overwrites existing files."""
        # Create initial file with old data
        old_data = {"old": "data", "version": "1.0"}
        with open(self.test_filepath, 'w') as f:
            json.dump(old_data, f)
        
        # Add new data to DB
        new_data = {"new": "data", "version": "2.0", "features": ["maps", "directions"]}
        DB.update(new_data)
        
        # Save the new state
        save_state(self.test_filepath)
        
        # Verify the file was overwritten with new data
        with open(self.test_filepath, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, new_data)
        self.assertNotIn("old", saved_data)

    def test_load_state_clears_existing_data(self):
        """Test that load_state clears existing data before loading new data."""
        # Add existing data to DB
        DB.update({"existing": "data", "should": "be_cleared"})
        
        # Create test file with new data
        new_data = {"new": "data", "locations": ["San Francisco"]}
        with open(self.test_filepath, 'w') as f:
            json.dump(new_data, f)
        
        # Load the new state
        load_state(self.test_filepath)
        
        # Verify only the new data exists
        self.assertEqual(DB, new_data)
        self.assertNotIn("existing", DB)
        self.assertNotIn("should", DB)

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

    def test_load_state_empty_file(self):
        """Test that load_state handles empty JSON files correctly."""
        # Create empty JSON file
        with open(self.test_filepath, 'w') as f:
            json.dump({}, f)
        
        # Load the empty state
        load_state(self.test_filepath)
        
        # Verify the DB is now empty
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

    def test_multiple_save_operations(self):
        """Test that multiple save operations work correctly."""
        # First save
        test_data_1 = {"version": "1.0", "data": "first"}
        DB.update(test_data_1)
        save_state(self.test_filepath)
        
        # Second save
        test_data_2 = {"version": "2.0", "data": "second", "additional": "info"}
        DB.clear()
        DB.update(test_data_2)
        save_state(self.test_filepath)
        
        # Verify the file contains the latest data
        with open(self.test_filepath, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, test_data_2)

    def test_db_persistence_across_operations(self):
        """Test that DB state persists correctly across multiple operations."""
        # Initial state
        initial_data = {"initial": "data"}
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
        expected_data = {"initial": "data", "modified": "data"}
        self.assertEqual(DB, expected_data)


if __name__ == '__main__':
    unittest.main()
