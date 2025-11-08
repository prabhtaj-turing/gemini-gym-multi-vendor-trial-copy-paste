"""
Test module for testing database state management in Confluence API.
Tests save_state, load_state, and get_minified_state functions.
"""

import unittest
import os
import json
import tempfile
import sys
from unittest.mock import patch, mock_open

# Add the project root to the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))


class TestConfluenceDbState(unittest.TestCase):
    """Test class for Confluence database state management."""

    def setUp(self):
        """Set up test environment."""
        # Import after path setup
        from confluence.SimulationEngine.db import DB
        self.original_db_state = DB.copy()

    def tearDown(self):
        """Clean up after each test."""
        from confluence.SimulationEngine.db import DB
        # Restore original state
        DB.clear()
        DB.update(self.original_db_state)

    def test_db_initial_state(self):
        """Test that DB is properly initialized with correct default data."""
        from confluence.SimulationEngine.db import DB
        
        # DB should be a dictionary
        self.assertIsInstance(DB, dict)
        
        # Should have some initial data (loaded from ConfluenceDefaultDB.json)
        self.assertGreater(len(DB), 0)
        
        # Should contain all expected top-level keys from default DB
        expected_keys = [
            'contents',
            'content_counter', 
            'content_properties',
            'content_labels',
            'long_tasks',
            'long_task_counter',
            'spaces',
            'deleted_spaces_tasks'
        ]
        
        for key in expected_keys:
            self.assertIn(key, DB, f"Missing expected key '{key}' in default DB")


    def test_save_state_creates_file(self):
        """Test that save_state creates a proper JSON file."""
        from confluence.SimulationEngine.db import DB, save_state
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Add test data
            DB['test_save'] = {'nested': 'data', 'number': 42}
            
            # Save state
            save_state(temp_path)
            
            # Verify file exists
            self.assertTrue(os.path.exists(temp_path))
            
            # Read and verify file content
            with open(temp_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            self.assertIn('test_save', loaded_data)
            self.assertEqual(loaded_data['test_save']['nested'], 'data')
            self.assertEqual(loaded_data['test_save']['number'], 42)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if 'test_save' in DB:
                del DB['test_save']

    def test_save_state_with_unicode(self):
        """Test that save_state properly handles Unicode characters."""
        from confluence.SimulationEngine.db import DB, save_state
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Add Unicode test data
            DB['unicode_test'] = {
                'english': 'hello',
                'chinese': '你好',
                'emoji': '😀',
                'special': 'café'
            }
            
            # Save state
            save_state(temp_path)
            
            # Read and verify Unicode is preserved
            with open(temp_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            self.assertEqual(loaded_data['unicode_test']['chinese'], '你好')
            self.assertEqual(loaded_data['unicode_test']['emoji'], '😀')
            self.assertEqual(loaded_data['unicode_test']['special'], 'café')
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if 'unicode_test' in DB:
                del DB['unicode_test']

    def test_load_state_restores_data(self):
        """Test that load_state properly restores data."""
        from confluence.SimulationEngine.db import DB, save_state, load_state
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Create test data and save
            test_data = {
                'restored_key': 'restored_value',
                'nested': {'inner': 'value'},
                'list': [1, 2, 3]
            }
            
            DB.update(test_data)
            save_state(temp_path)
            
            # Clear DB and reload
            DB.clear()
            self.assertEqual(len(DB), 0)
            
            load_state(temp_path)
            
            # Verify data was restored
            self.assertIn('restored_key', DB)
            self.assertEqual(DB['restored_key'], 'restored_value')
            self.assertEqual(DB['nested']['inner'], 'value')
            self.assertEqual(DB['list'], [1, 2, 3])
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_state_merges_with_existing(self):
        """Test that load_state merges with existing data rather than replacing."""
        from confluence.SimulationEngine.db import DB, save_state, load_state
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Create and save some data
            save_data = {'saved_key': 'saved_value'}
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f)
            
            # Add some existing data to DB
            DB['existing_key'] = 'existing_value'
            existing_count = len(DB)
            
            # Load state (should merge, not replace)
            load_state(temp_path)
            
            # Should have both existing and loaded data
            self.assertIn('existing_key', DB)
            self.assertIn('saved_key', DB)
            self.assertEqual(DB['existing_key'], 'existing_value')
            self.assertEqual(DB['saved_key'], 'saved_value')
            self.assertGreaterEqual(len(DB), existing_count + 1)
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_state_file_not_found(self):
        """Test that load_state raises FileNotFoundError for missing files."""
        from confluence.SimulationEngine.db import load_state
        
        non_existent_path = 'definitely_does_not_exist.json'
        
        with self.assertRaises(FileNotFoundError):
            load_state(non_existent_path)

    def test_load_state_invalid_json(self):
        """Test that load_state handles invalid JSON gracefully."""
        from confluence.SimulationEngine.db import load_state
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
            # Write invalid JSON
            temp_file.write('{"invalid": json, missing quotes}')
        
        try:
            with self.assertRaises(json.JSONDecodeError):
                load_state(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_get_minified_state_returns_reference(self):
        """Test that get_minified_state returns the same reference as DB."""
        from confluence.SimulationEngine.db import DB, get_minified_state
        
        minified = get_minified_state()
        
        # Should return the same reference
        self.assertIs(minified, DB)
        
        # Should be the same data
        self.assertEqual(minified, DB)

    def test_get_minified_state_modifications(self):
        """Test that modifications to minified state affect DB."""
        from confluence.SimulationEngine.db import DB, get_minified_state
        
        minified = get_minified_state()
        original_length = len(DB)
        
        # Modify minified state
        minified['minified_test'] = 'test_value'
        
        # Should affect DB since it's the same reference
        self.assertEqual(len(DB), original_length + 1)
        self.assertIn('minified_test', DB)
        self.assertEqual(DB['minified_test'], 'test_value')
        
        # Clean up
        del DB['minified_test']

    def test_save_state_preserves_structure(self):
        """Test that save_state preserves complex data structures."""
        from confluence.SimulationEngine.db import DB, save_state
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Create complex nested structure
            complex_data = {
                'string': 'value',
                'number': 42,
                'float': 3.14,
                'boolean': True,
                'null': None,
                'list': [1, 'two', {'three': 3}],
                'nested_dict': {
                    'level1': {
                        'level2': {
                            'level3': 'deep_value'
                        }
                    }
                }
            }
            
            DB['complex_test'] = complex_data
            save_state(temp_path)
            
            # Read back and verify structure
            with open(temp_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            saved_complex = loaded_data['complex_test']
            self.assertEqual(saved_complex['string'], 'value')
            self.assertEqual(saved_complex['number'], 42)
            self.assertEqual(saved_complex['float'], 3.14)
            self.assertEqual(saved_complex['boolean'], True)
            self.assertIsNone(saved_complex['null'])
            self.assertEqual(saved_complex['list'], [1, 'two', {'three': 3}])
            self.assertEqual(saved_complex['nested_dict']['level1']['level2']['level3'], 'deep_value')
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if 'complex_test' in DB:
                del DB['complex_test']

    def test_save_state_with_empty_db(self):
        """Test that save_state works with empty database."""
        from confluence.SimulationEngine.db import DB, save_state
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Clear DB
            DB.clear()
            
            # Save empty state
            save_state(temp_path)
            
            # Verify file exists and contains empty object
            self.assertTrue(os.path.exists(temp_path))
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            self.assertEqual(loaded_data, {})
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_state_persistence_integration(self):
        """Test full save/load cycle integration."""
        from confluence.SimulationEngine.db import DB, save_state, load_state
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Create test scenario
            original_data = DB.copy()
            
            # Add test content
            test_content = {
                'content': {
                    'test_page': {
                        'id': 'test_page',
                        'type': 'page',
                        'title': 'Test Page',
                        'spaceKey': 'TEST'
                    }
                },
                'spaces': {
                    'TEST': {
                        'key': 'TEST',
                        'name': 'Test Space'
                    }
                }
            }
            
            DB.update(test_content)
            
            # Save state
            save_state(temp_path)
            
            # Clear and verify empty
            DB.clear()
            self.assertEqual(len(DB), 0)
            
            # Load state
            load_state(temp_path)
            
            # Verify restoration
            self.assertIn('content', DB)
            self.assertIn('spaces', DB)
            self.assertEqual(DB['content']['test_page']['title'], 'Test Page')
            self.assertEqual(DB['spaces']['TEST']['name'], 'Test Space')
            
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_save_state_permission_error(self, mock_file):
        """Test that save_state handles permission errors gracefully."""
        from confluence.SimulationEngine.db import save_state
        
        with self.assertRaises(PermissionError):
            save_state('/root/test.json')

    def test_db_default_path_exists(self):
        """Test that the default DB path is accessible."""
        from confluence.SimulationEngine.db import DEFAULT_DB_PATH
        
        # The default path should be set
        self.assertIsNotNone(DEFAULT_DB_PATH)
        self.assertIsInstance(DEFAULT_DB_PATH, str)
        
        # Should point to a JSON file
        self.assertTrue(DEFAULT_DB_PATH.endswith('.json'))
        
        # File should exist (since it's loaded at import)
        self.assertTrue(os.path.exists(DEFAULT_DB_PATH))


if __name__ == '__main__':
    unittest.main()
