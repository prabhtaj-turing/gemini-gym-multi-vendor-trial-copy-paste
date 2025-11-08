import unittest
import os
import json
import copy
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, save_state, load_state

# Since there is no reset_db function, we'll manage the default state manually
DEFAULT_DB = copy.deepcopy(DB)

def reset_db_manual():
    """Reset the DB manually for testing purposes."""
    global DB
    DB.clear()
    DB.update(copy.deepcopy(DEFAULT_DB))

class TestDBState(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test directory and reset DB."""
        super().setUp()
        reset_db_manual()
        self.test_dir = os.path.join(os.path.dirname(__file__), 'assets')
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_filepath = os.path.join(self.test_dir, 'test_db.json')
        self.old_format_filepath = os.path.join(self.test_dir, 'old_format_db.json')

    def tearDown(self):
        """Clean up test files and directory."""
        super().tearDown()
        reset_db_manual()
        if os.path.exists(self.test_filepath):
            os.remove(self.test_filepath)
        if os.path.exists(self.old_format_filepath):
            os.remove(self.old_format_filepath)
        if os.path.exists(self.test_dir) and not os.listdir(self.test_dir):
            os.rmdir(self.test_dir)

    def test_save_and_load_state(self):
        """Test that the DB state can be saved to and loaded from a file."""
        # 1. Add some data to the DB
        new_project = {
            "id": "proj_test_save_load",
            "name": "Test Project Save Load",
            "organization_id": "org_abc123",
            "region": "us-west-2",
            "status": "ACTIVE_HEALTHY",
            "created_at": "2024-01-01T00:00:00Z",
            "version": "PostgreSQL 15"
        }
        DB['projects'].append(new_project)
        original_db = copy.deepcopy(DB)

        # 2. Save state
        save_state(self.test_filepath)

        # 3. Check if the file was created
        self.assertTrue(os.path.exists(self.test_filepath))

        # 4. Reset DB to ensure we are loading fresh data
        reset_db_manual()
        self.assertNotEqual(DB, original_db)

        # 5. Load state from file
        load_state(self.test_filepath)

        # 6. Assert that the data has been restored
        self.assertEqual(DB, original_db)

    def test_load_state_nonexistent_file(self):
        """Test that loading from a non-existent file raises an error."""
        with self.assertRaises(FileNotFoundError):
            load_state('nonexistent_filepath.json')

    def test_backward_compatibility_loading(self):
        """Test loading a DB state with missing keys (for backward compatibility)."""
        # 1. Create a test DB file that is missing some of the current DB keys
        old_format_db_data = {
            "organizations": [{"id": "org_retro", "name": "Retro Inc."}],
            "projects": [{"id": "proj_retro", "name": "Retro Project", "organization_id": "org_retro"}],
        }
        with open(self.old_format_filepath, 'w') as f:
            json.dump(old_format_db_data, f)

        # 2. Load the old-format state
        load_state(self.old_format_filepath)

        # 3. Check that the loaded data is present and missing keys are gone
        self.assertEqual(DB['organizations'], old_format_db_data['organizations'])
        self.assertEqual(DB['projects'], old_format_db_data['projects'])
        self.assertNotIn('tables', DB)
        self.assertNotIn('logs', DB)

if __name__ == '__main__':
    unittest.main()
