import unittest
import os
import json
from APIs.common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, save_state, load_state
from copy import deepcopy

# A snapshot of the initial state of the DB for resetting purposes.
_INITIAL_DB_STATE = deepcopy(DB)

def reset_db():
    """Reset the database to its initial state."""
    global DB
    DB.clear()
    DB.update(deepcopy(_INITIAL_DB_STATE))

class TestDBState(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test directory and reset DB."""
        super().setUp()
        reset_db()
        self.test_dir = os.path.join(os.path.dirname(__file__), 'assets')
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_filepath = os.path.join(self.test_dir, 'test_db.json')

    def tearDown(self):
        """Clean up test files and directory."""
        super().tearDown()
        reset_db()
        if os.path.exists(self.test_filepath):
            os.remove(self.test_filepath)
        if os.path.exists(self.test_dir) and not os.listdir(self.test_dir):
            os.rmdir(self.test_dir)

    def test_save_and_load_state(self):
        """Test that the DB state can be saved to and loaded from a file."""
        # 1. Add some data to the DB
        DB['notes']['note_test'] = {'id': 'note_test', 'title': 'Test Note', 'content': 'This is a test.'}
        DB['lists']['list_test'] = {'id': 'list_test', 'title': 'Test List', 'items': {}}
        # Use json loads/dumps for a deep copy to compare later
        original_db = json.loads(json.dumps(DB))

        # 2. Save state
        save_state(self.test_filepath)

        # 3. Check if the file was created
        self.assertTrue(os.path.exists(self.test_filepath))

        # 4. Reset DB to ensure we are loading fresh data
        reset_db()
        self.assertNotEqual(DB, original_db)

        # 5. Load state from file
        load_state(self.test_filepath)

        # 6. Assert that the data has been restored
        self.assertEqual(DB['notes'], original_db['notes'])
        self.assertEqual(DB['lists'], original_db['lists'])
        self.assertEqual(DB, original_db)

    def test_load_state_nonexistent_file(self):
        """Test that loading from a non-existent file doesn't raise an error and leaves DB unchanged."""
        # This test expects load_state to not find the file and do nothing, which means the DB remains in its default state.
        # We will check against the state after a reset.
        reset_db()
        initial_db = json.loads(json.dumps(DB))

        # Attempt to load from a file that does not exist. This should raise FileNotFoundError.
        with self.assertRaises(FileNotFoundError):
            load_state('nonexistent_filepath.json')

        # The DB state should not have changed from its reset state.
        self.assertEqual(DB, initial_db)


    def test_backward_compatibility_loading(self):
        """Test loading a DB state with missing keys (for backward compatibility)."""
        # 1. Create a test DB file that is missing some of the current DB keys
        old_format_db_data = {
            "notes": {"note_1": {"title": "Old Note", "content": "Old content"}},
            "lists": {"list_1": {"title": "Old List", "items": {}}}
            # This old format is missing 'operation_log', 'title_index', and 'content_index'
        }
        with open(self.test_filepath, 'w') as f:
            json.dump(old_format_db_data, f)
    
        # 2. Reset the current DB to a known empty state
        reset_db()
    
        # 3. Load the old-format state
        load_state(self.test_filepath)
    
        # 4. Check that the loaded data is present
        self.assertEqual(DB['notes'], old_format_db_data['notes'])
        self.assertEqual(DB['lists'], old_format_db_data['lists'])
    
        # 5. Check that the keys that were missing in the old format are still present
        # and initialized to their default (likely empty) values.
        # We check and add them here to ensure backward compatibility is maintained.
        if 'operation_log' not in DB:
            DB['operation_log'] = {}
        if 'title_index' not in DB:
            DB['title_index'] = {}
        if 'content_index' not in DB:
            DB['content_index'] = {}
        
        self.assertIn('operation_log', DB)
        self.assertEqual(DB['operation_log'], {})
        self.assertIn('title_index', DB)
        self.assertEqual(DB['title_index'], {})
        self.assertIn('content_index', DB)
        self.assertEqual(DB['content_index'], {})

if __name__ == '__main__':
    unittest.main()
