import unittest
import os
import json
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import db

class TestDBState(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Set up test directory and reset DB."""
        super().setUp()
        db.reset_db()
        self.test_dir = os.path.join(os.path.dirname(__file__), 'assets')
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_filepath = os.path.join(self.test_dir, 'test_db.json')

    def tearDown(self):
        """Clean up test files and directory."""
        super().tearDown()
        # Clean up test files first
        if os.path.exists(self.test_filepath):
            os.remove(self.test_filepath)
        if os.path.exists(self.test_dir) and os.path.isdir(self.test_dir) and not os.listdir(self.test_dir):
            os.rmdir(self.test_dir)
        # Reset DB for next test
        db.reset_db()

    def test_save_and_load_state(self):
        """Test that the DB state can be saved to and loaded from a file."""
        # 1. Add some data to the DB
        db.DB['suppliers']['supplier_companies']['supplier1'] = {'name': 'Test Supplier', 'status': 'active'}
        db.DB['contracts']['contracts']['contract1'] = {'id': 'contract1', 'status': 'draft'}
        db.DB['events']['events']['event1'] = {'name': 'Test Event', 'type': 'sourcing'}
        db.DB['scim']['users'].append({'id': 'user1', 'name': 'Test User'})
        # Use json loads/dumps for a deep copy to compare later
        original_db = json.loads(json.dumps(db.DB))

        # 2. Save state
        db.save_state(self.test_filepath)

        # 3. Check if the file was created
        self.assertTrue(os.path.exists(self.test_filepath))

        # 4. Reset DB to ensure we are loading fresh data
        db.reset_db()
        self.assertNotEqual(db.DB, original_db)

        # 5. Load state from file
        db.load_state(self.test_filepath)

        # 6. Assert that the data has been restored
        self.assertEqual(db.DB['suppliers']['supplier_companies'], original_db['suppliers']['supplier_companies'])
        self.assertEqual(db.DB['contracts']['contracts'], original_db['contracts']['contracts'])
        self.assertEqual(db.DB['events']['events'], original_db['events']['events'])
        self.assertEqual(db.DB['scim']['users'], original_db['scim']['users'])
        self.assertEqual(db.DB, original_db)

    def test_load_state_nonexistent_file(self):
        """Test that loading from a non-existent file doesn't raise an error and leaves DB unchanged."""
        db.reset_db()
        db.DB['suppliers']['supplier_companies']['supplier1'] = {'name': 'initial_supplier'}
        initial_db = json.loads(json.dumps(db.DB))

        # Attempt to load from a file that does not exist
        db.load_state('nonexistent_filepath.json')

        # The DB state should not have changed
        self.assertEqual(db.DB, initial_db)

    def test_backward_compatibility_loading(self):
        """Test loading a DB state with missing keys (for backward compatibility)."""
        # 1. Create a test DB file that is missing some of the current DB keys
        old_format_db_data = {
            "suppliers": {"supplier_companies": {"supplier1": {"name": "Old Supplier"}}},
            "contracts": {"contracts": {"contract1": {"id": "contract1", "status": "old_draft"}}},
            "events": {"events": {"event1": {"name": "Old Event"}}}
            # This old format is missing 'attachments', 'awards', 'fields', 'payments', 'projects', 'reports', 'scim', 'spend_categories'
        }
        with open(self.test_filepath, 'w') as f:
            json.dump(old_format_db_data, f)

        # 2. Reset the current DB
        db.reset_db()
        self.assertEqual(db.DB['suppliers']['supplier_companies'], {})
        
        # 3. Load the old-format state
        db.load_state(self.test_filepath)

        # 4. Check that the loaded data is present
        self.assertEqual(db.DB['suppliers']['supplier_companies'], old_format_db_data['suppliers']['supplier_companies'])
        self.assertEqual(db.DB['contracts']['contracts'], old_format_db_data['contracts']['contracts'])
        self.assertEqual(db.DB['events']['events'], old_format_db_data['events']['events'])

        # 5. Check that the keys that were missing in the old format are still present with default values
        self.assertIn('attachments', db.DB)
        self.assertEqual(db.DB['attachments'], {})
        self.assertIn('awards', db.DB)
        self.assertEqual(db.DB['awards'], {'award_line_items': [], 'awards': []})
        self.assertIn('fields', db.DB)
        self.assertEqual(db.DB['fields'], {'field_groups': {}, 'field_options': {}, 'fields': {}})
        self.assertIn('payments', db.DB)
        self.assertIn('payment_currencies', db.DB['payments'])
        self.assertIn('projects', db.DB)
        self.assertEqual(db.DB['projects'], {'project_types': {}, 'projects': {}})
        self.assertIn('reports', db.DB)
        self.assertIn('scim', db.DB)
        self.assertEqual(db.DB['scim']['users'], [])
        self.assertIn('spend_categories', db.DB)
        self.assertEqual(db.DB['spend_categories'], {})

    def test_load_state_updates_existing_data(self):
        """Test that loading state properly updates existing data by replacing specified keys."""
        # 1. Set up initial state
        db.reset_db()
        db.DB['suppliers']['supplier_companies']['original'] = {'name': 'Original Supplier'}
        db.DB['contracts']['contracts']['original'] = {'id': 'original', 'status': 'active'}
        
        # 2. Create a saved state with some keys to update
        saved_state = {
            'suppliers': {'supplier_companies': {'saved': {'name': 'Saved Supplier'}}},
            'events': {'events': {'saved_event': {'name': 'Saved Event'}}}
        }
        with open(self.test_filepath, 'w') as f:
            json.dump(saved_state, f)
        
        # 3. Load the saved state
        db.load_state(self.test_filepath)
        
        # 4. Verify that only the specified keys were updated
        self.assertEqual(db.DB['suppliers']['supplier_companies'], saved_state['suppliers']['supplier_companies'])
        self.assertEqual(db.DB['events']['events'], saved_state['events']['events'])
        # Keys not in saved_state should retain their original values
        self.assertEqual(db.DB['contracts']['contracts'], {'original': {'id': 'original', 'status': 'active'}})  # Should preserve original data
        self.assertEqual(db.DB['attachments'], {})  # Should remain at default since it wasn't modified

if __name__ == '__main__':
    unittest.main()
