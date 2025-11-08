import unittest
import sys
import os
import json
import tempfile
import shutil
import copy
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from APIs.ces_system_activation.SimulationEngine import db
from APIs.ces_system_activation.SimulationEngine.models import *


class TestCESDBState(BaseTestCaseWithErrorHandler):
    """
    Test suite for CES database state management: load/save operations and backward compatibility.
    Ensures data can be loaded and saved correctly across different versions.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        
        # Store original DB state
        self.original_db = db.DB.copy()
        
        # Reset DB to known state
        db.reset_db()

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original DB state
        db.DB.clear()
        db.DB.update(self.original_db)
        
        # Clean up temporary directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # Tests for save_state
    def test_save_state_success(self):
        """
        Test successful saving of database state to file.
        """
        # Ensure we have customers to modify
        if not db.DB.get('customers'):
            db.DB['customers'] = [{'firstName': 'Test', 'lastName': 'User'}]
        
        # Modify DB state
        db.DB['customers'][0]['firstName'] = 'Modified'
        db.DB['use_real_datastore'] = True
        
        # Save state
        test_file = os.path.join(self.temp_dir, 'test_save.json')
        db.save_state(test_file)
        
        # Verify file was created and contains correct data
        self.assertTrue(os.path.exists(test_file))
        
        with open(test_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data['customers'][0]['firstName'], 'Modified')
        self.assertEqual(saved_data['use_real_datastore'], True)
        self.assertEqual(len(saved_data['customers']), len(db.DB['customers']))

    def test_save_state_file_permissions(self):
        """
        Test save_state handles file permission errors gracefully.
        """
        # Try to save to a read-only directory (if possible)
        readonly_dir = os.path.join(self.temp_dir, 'readonly')
        os.makedirs(readonly_dir)
        os.chmod(readonly_dir, 0o444)  # Read-only
        
        readonly_file = os.path.join(readonly_dir, 'test.json')
        
        try:
            self.assert_error_behavior(
                db.save_state,
                PermissionError,
                f"[Errno 13] Permission denied: '{readonly_file}'",
                None,
                readonly_file
            )
        finally:
            # Restore permissions for cleanup
            os.chmod(readonly_dir, 0o755)

    def test_save_state_invalid_path(self):
        """
        Test save_state handles invalid file paths gracefully.
        """
        invalid_path = '/nonexistent/directory/file.json'
        
        self.assert_error_behavior(
            db.save_state,
            FileNotFoundError,
            "[Errno 2] No such file or directory: '/nonexistent/directory/file.json'",
            None,
            invalid_path
        )

    # Tests for load_state
    def test_load_state_success(self):
        """
        Test successful loading of database state from file.
        """
        # Create test data
        test_data = {
            '_error_simulator': {'test_func': ['error1']},
            '_end_of_conversation_status': {'escalate': 'test reason'},
            'use_real_datastore': True,
            'customers': [{
                'customerId': 'test-id',
                'firstName': 'Test',
                'lastName': 'User',
                'email': 'test@example.com',
                'phoneNumber': '+1234567890',
                'status': 'Test Status',
                'planSubscribed': 'Test Plan',
                'applicationStatus': 'Test',
                'applicationId': 'TEST-001'
            }]
        }
        
        # Save test data to file
        test_file = os.path.join(self.temp_dir, 'test_load.json')
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # Load state
        db.load_state(test_file)
        
        # Verify data was loaded correctly
        self.assertEqual(db.DB['use_real_datastore'], True)
        self.assertEqual(db.DB['customers'][0]['firstName'], 'Test')
        self.assertEqual(db.DB['_end_of_conversation_status']['escalate'], 'test reason')
        self.assertEqual(len(db.DB['customers']), 1)

    def test_load_state_file_not_found(self):
        """
        Test load_state handles missing files gracefully.
        """
        nonexistent_file = os.path.join(self.temp_dir, 'nonexistent.json')
        
        self.assert_error_behavior(
            db.load_state,
            FileNotFoundError,
            f"[Errno 2] No such file or directory: '{nonexistent_file}'",
            None,
            nonexistent_file
        )

    def test_load_state_invalid_json(self):
        """
        Test load_state handles invalid JSON gracefully.
        """
        # Create file with invalid JSON
        test_file = os.path.join(self.temp_dir, 'invalid.json')
        with open(test_file, 'w') as f:
            f.write('{invalid}')
        
        self.assert_error_behavior(
            db.load_state,
            json.JSONDecodeError,
            "Expecting property name enclosed in double quotes: line 1 column 2 (char 1)",
            None,
            test_file
        )

    def test_load_state_clears_existing_data(self):
        """
        Test that load_state clears existing data before loading new data.
        """
        # Add some data to current DB
        db.DB['test_key'] = 'test_value'
        original_customers_count = len(db.DB['customers'])
        
        # Load test data that doesn't have 'test_key'
        test_file = os.path.join(self.test_assets_dir, 'test_db_state_v1.json')
        db.load_state(test_file)
        
        # Verify old data was cleared
        self.assertNotIn('test_key', db.DB)
        # Verify new data was loaded
        self.assertIn('customers', db.DB)

    # Tests for get_minified_state
    def test_get_minified_state_returns_current_db(self):
        """
        Test get_minified_state returns the current database state.
        """
        # Modify DB
        db.DB['test_modification'] = 'test_value'
        
        result = db.get_minified_state()
        
        # Verify it returns the current DB
        self.assertEqual(result, db.DB)
        self.assertEqual(result['test_modification'], 'test_value')
        
        # Verify it's a reference, not a copy
        self.assertIs(result, db.DB)

    # Backward compatibility tests
    def test_load_v1_state_compatibility(self):
        """
        Test loading version 1 state file maintains backward compatibility.
        """
        test_file = os.path.join(self.test_assets_dir, 'test_db_state_v1.json')
        
        # Load v1 state
        db.load_state(test_file)
        
        # Verify basic structure is maintained
        self.assertIn('customers', db.DB)
        self.assertIn('_error_simulator', db.DB)
        self.assertIn('_end_of_conversation_status', db.DB)
        self.assertIn('use_real_datastore', db.DB)
        
        # Verify customer data structure
        customers = db.DB['customers']
        self.assertEqual(len(customers), 2)
        
        # Check first customer
        customer1 = customers[0]
        self.assertEqual(customer1['firstName'], 'Grace')
        self.assertEqual(customer1['lastName'], 'Goings')
        self.assertEqual(customer1['email'], 'gracegoings@cymbal.com')
        
        # Check required fields exist
        required_fields = ['customerId', 'firstName', 'lastName', 'email', 
                          'phoneNumber', 'status', 'applicationStatus', 'applicationId']
        for field in required_fields:
            self.assertIn(field, customer1)

    def test_load_v2_state_compatibility(self):
        """
        Test loading version 2 state file with additional fields.
        """
        test_file = os.path.join(self.test_assets_dir, 'test_db_state_v2.json')
        
        # Load v2 state
        db.load_state(test_file)
        
        # Verify enhanced structure is supported
        self.assertIn('metadata', db.DB)
        self.assertEqual(db.DB['metadata']['version'], '2.0')
        
        # Verify additional customer fields
        customers = db.DB['customers']
        self.assertEqual(len(customers), 3)
        
        # Check enhanced customer data
        customer1 = customers[0]
        self.assertIn('lastUpdated', customer1)
        self.assertEqual(customer1['leadId'], 'LEAD-001')
        self.assertEqual(customer1['planSubscribed'], 'Go Swiss Premium')
        
        # Check new customer
        customer3 = customers[2]
        self.assertEqual(customer3['firstName'], 'John')
        self.assertEqual(customer3['status'], 'New Lead')

    def test_save_load_roundtrip(self):
        """
        Test that save and load operations are consistent (roundtrip test).
        """
        self.skipTest("Skipping test_save_load_roundtrip")
        # Ensure we have customers to modify
        if not db.DB.get('customers'):
            db.DB['customers'] = [{'firstName': 'Original', 'lastName': 'User'}]
        
        # Store original state before modifications using deep copy
        original_state = copy.deepcopy(db.get_minified_state())
        original_first_name = db.DB['customers'][0]['firstName']
            
        # Modify DB state
        db.DB['customers'][0]['firstName'] = 'Roundtrip Test'
        db.DB['use_real_datastore'] = True
        db.DB['_end_of_conversation_status']['escalate'] = 'test escalation'
        
        # Save state
        test_file = os.path.join(self.temp_dir, 'roundtrip.json')
        db.save_state(test_file)
        
        # Reset DB to original state
        db.DB.clear()
        db.DB.update(original_state)
        
        # Verify DB was reset (check if customers exist first)
        if db.DB.get('customers'):
            # If customers exist after reset, check the original name
            self.assertEqual(db.DB['customers'][0]['firstName'], original_first_name)
        self.assertEqual(db.DB['use_real_datastore'], False)
        
        # Load saved state
        db.load_state(test_file)
        
        # Verify modifications were restored
        self.assertEqual(db.DB['customers'][0]['firstName'], 'Roundtrip Test')
        self.assertEqual(db.DB['use_real_datastore'], True)
        self.assertEqual(db.DB['_end_of_conversation_status']['escalate'], 'test escalation')

    def test_state_persistence_across_resets(self):
        """
        Test that saved states persist correctly across database resets.
        """
        # Ensure we have a clean slate for customers
        db.DB['customers'] = []
        
        # Add a customer with a known original state
        db.DB['customers'].append({'firstName': 'Test', 'lastName': 'User', 'status': 'Original Status'})
            
        # Save current state
        original_file = os.path.join(self.temp_dir, 'original.json')
        db.save_state(original_file)
        
        # Modify and save modified state
        db.DB['customers'][0]['status'] = 'Modified Status'
        modified_file = os.path.join(self.temp_dir, 'modified.json')
        db.save_state(modified_file)
        
        # Reset DB
        db.reset_db()
        
        # Load original state
        db.load_state(original_file)
        self.assertEqual(db.DB['customers'][0]['status'], 'Original Status')
        
        # Load modified state
        db.load_state(modified_file)
        self.assertEqual(db.DB['customers'][0]['status'], 'Modified Status')

    # Data validation tests using Pydantic models
    def test_loaded_customer_data_validation(self):
        """
        Test that loaded customer data can be validated using Pydantic models.
        """
        test_file = os.path.join(self.test_assets_dir, 'test_db_state_v1.json')
        db.load_state(test_file)
        
        # Validate customer data structure (basic validation)
        customers = db.DB['customers']
        for customer in customers:
            # Check required fields
            self.assertIsInstance(customer['customerId'], str)
            self.assertIsInstance(customer['firstName'], str)
            self.assertIsInstance(customer['lastName'], str)
            self.assertIsInstance(customer['email'], str)
            self.assertIsInstance(customer['phoneNumber'], str)
            self.assertIsInstance(customer['status'], str)
            self.assertIsInstance(customer['applicationStatus'], str)
            self.assertIsInstance(customer['applicationId'], str)
            
            # Check data integrity
            self.assertTrue(customer['customerId'].strip())
            self.assertTrue(customer['firstName'].strip())
            self.assertTrue(customer['lastName'].strip())
            self.assertIn('@', customer['email'])
            self.assertTrue(customer['phoneNumber'].startswith('+'))

    def test_conversation_status_state_persistence(self):
        """
        Test that conversation status persists correctly.
        """
        # Set conversation status
        db.DB['_end_of_conversation_status']['escalate'] = 'User requested manager'
        db.DB['_end_of_conversation_status']['fail'] = 'System error occurred'
        
        # Save and reload
        test_file = os.path.join(self.temp_dir, 'conv_status.json')
        db.save_state(test_file)
        db.reset_db()
        db.load_state(test_file)
        
        # Verify conversation status was restored
        self.assertEqual(db.DB['_end_of_conversation_status']['escalate'], 'User requested manager')
        self.assertEqual(db.DB['_end_of_conversation_status']['fail'], 'System error occurred')


if __name__ == '__main__':
    unittest.main()
