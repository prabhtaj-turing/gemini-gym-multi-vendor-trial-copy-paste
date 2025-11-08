import unittest
import os
import json
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, save_state, load_state, reset_db

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
        DB['message_senders']['sender1'] = {'name': 'test_sender', 'type': 'user'}
        DB['bundled_notifications']['bundle1'] = {'key': 'bundle1', 'is_read': False}
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
        self.assertEqual(DB['message_senders'], original_db['message_senders'])
        self.assertEqual(DB['bundled_notifications'], original_db['bundled_notifications'])
        self.assertEqual(DB, original_db)

    def test_load_state_nonexistent_file(self):
        """Test that loading from a non-existent file doesn't raise an error and leaves DB unchanged."""
        reset_db()
        DB['message_senders']['sender1'] = {'name': 'initial_sender'}
        initial_db = json.loads(json.dumps(DB))

        # Attempt to load from a file that does not exist
        load_state('nonexistent_filepath.json')

        # The DB state should not have changed
        self.assertEqual(DB, initial_db)

    def test_backward_compatibility_loading(self):
        """Test loading a DB state with missing keys (for backward compatibility)."""
        # 1. Create a test DB file that is missing some of the current DB keys
        old_format_db_data = {
            "message_notifications": {"msg1": {"text": "hello old world"}},
            "message_senders": {"sender1": {"name": "Old Sender"}}
            # This old format is missing 'bundled_notifications' and 'reply_actions'
        }
        with open(self.test_filepath, 'w') as f:
            json.dump(old_format_db_data, f)

        # 2. Reset the current DB
        reset_db()
        self.assertEqual(DB['message_notifications'], {})
        
        # 3. Load the old-format state
        load_state(self.test_filepath)

        # 4. Check that the loaded data is present
        self.assertEqual(DB['message_notifications'], old_format_db_data['message_notifications'])
        self.assertEqual(DB['message_senders'], old_format_db_data['message_senders'])

        # 5. Check that the keys that were missing in the old format are still present as empty dicts
        self.assertIn('bundled_notifications', DB)
        self.assertEqual(DB['bundled_notifications'], {})
        self.assertIn('reply_actions', DB)
        self.assertEqual(DB['reply_actions'], {})

if __name__ == '__main__':
    unittest.main()
