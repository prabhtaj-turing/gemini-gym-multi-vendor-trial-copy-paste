"""
Test cases for the database state management in the CES Loyalty Auth API.

This module ensures that the database functions for loading, saving, and
resetting the application state work as expected.
"""

import unittest
import unittest.mock
import os
import json
from APIs.ces_loyalty_auth.SimulationEngine import db
from .loyalty_auth_base_exception import LoyaltyAuthBaseTestCase


class TestDbState(LoyaltyAuthBaseTestCase):
    """
    Test suite for the database state management functions.
    """

    def setUp(self):
        """
        Set up a temporary file path for testing save and load operations.
        Ensure the file does not exist before each test.
        """
        super().setUp()
        self.test_filepath = "test_db_state.json"
        if os.path.exists(self.test_filepath):
            os.remove(self.test_filepath)

    def tearDown(self):
        """
        Clean up the temporary file after each test.
        """
        if os.path.exists(self.test_filepath):
            os.remove(self.test_filepath)
        super().tearDown()

    def test_save_and_load_state(self):
        """
        Tests that the database state can be saved to a file and then
        loaded back correctly.
        """
        # Modify the state
        db.DB["AUTH_STATUS"] = "PENDING"
        db.save_state(self.test_filepath)

        # Reset the DB and load the state from the file
        db.reset_db()
        self.assertIsNone(db.DB["AUTH_STATUS"])  # Should be reset
        db.load_state(self.test_filepath)

        # Check if the state was restored
        self.assertEqual(db.DB["AUTH_STATUS"], "PENDING")

    def test_reset_db(self):
        """
        Tests that the reset_db function correctly resets the database
        to its initial, empty state.
        """
        # Modify the state
        db.DB["AUTH_STATUS"] = "FAILED"
        db.DB["PROFILE_AFTER_AUTH"] = {"customerName": "Test"}

        # Reset the DB
        db.reset_db()

        # Check if the state is back to the initial values
        self.assertIsNone(db.DB["AUTH_STATUS"])
        # With the fix, reset_db reloads default data.
        self.assertNotEqual(db.DB["PROFILE_AFTER_AUTH"], {})

    def test_get_minified_state(self):
        """
        Tests that get_minified_state returns the current state of the database.
        """
        # Modify the state
        db.DB["SESSION_STATUS"] = "ACTIVE"
        state = db.get_minified_state()
        self.assertEqual(state["SESSION_STATUS"], "ACTIVE")
        self.assertIn("PROFILE_BEFORE_AUTH", state)

    def test_load_default_data(self):
        """
        Tests that load_default_data correctly loads the default database
        from the JSON file.
        """
        # This function is called on module import, so we reset and call it again
        db.reset_db()
        # The profile should be empty after reset (before loading default data within reset)
        # But since we fixed reset_db, it will load data. Let's check a key.
        self.assertIn("sessionInfo", db.DB["PROFILE_BEFORE_AUTH"])

        # To be sure, let's clear it and load again manually.
        db.DB["PROFILE_BEFORE_AUTH"] = {}
        db.load_default_data()
        self.assertIn("sessionInfo", db.DB["PROFILE_BEFORE_AUTH"])

    def test_load_state_file_not_found(self):
        """
        Tests that a warning is printed when load_state cannot find the file.
        This covers line 33.
        """
        with unittest.mock.patch("builtins.print") as mock_print:
            db.load_state("non_existent_file.json")
            mock_print.assert_called_with(
                "Warning: Could not load state from non_existent_file.json: "
                "[Errno 2] No such file or directory: 'non_existent_file.json'"
            )

    def test_load_default_data_name_error(self):
        """
        Tests the fallback path in load_default_data when a NameError occurs.
        This covers line 79.
        """
        with unittest.mock.patch(
            "os.path.dirname", side_effect=NameError("Simulated NameError")
        ):
            db.reset_db()  # Reset to ensure a clean load
            db.load_default_data()
            self.assertIn("sessionInfo", db.DB["PROFILE_BEFORE_AUTH"])

    def test_load_state_validation_error(self):
        """
        Tests that a warning is printed when load_state encounters a validation error.
        """
        # Create a temporary file with invalid data that will cause validation to fail
        invalid_data = {
            "CONVERSATION_STATUS": "INVALID_STATUS",  # This should cause validation to fail
            "SESSION_STATUS": None,
            "AUTH_RESULT": None,
            "AUTH_STATUS": None,
            "OFFER_ENROLLMENT": None,
            "PROFILE_BEFORE_AUTH": {},
            "PROFILE_AFTER_AUTH": {},
            "use_real_datastore": False,
            "end_of_conversation_status": {}
        }
        
        with open(self.test_filepath, "w") as f:
            json.dump(invalid_data, f)
        
        with unittest.mock.patch("builtins.print") as mock_print:
            db.load_state(self.test_filepath)
            # Check that a warning was printed about data validation failure
            mock_print.assert_called()
            # The call should contain the warning message about data validation failure
            warning_calls = [call for call in mock_print.call_args_list 
                           if "Warning: Data validation failed" in str(call)]
            self.assertTrue(len(warning_calls) > 0)

    def test_get_database_function(self):
        """
        Tests that get_database() returns a CesLoyaltyAuthDB instance.
        """
        # Test that get_database returns a Pydantic model instance
        database = db.get_database()
        self.assertIsNotNone(database)
        # Check that it's the correct type
        from APIs.ces_loyalty_auth.SimulationEngine.db_models import CesLoyaltyAuthDB
        self.assertIsInstance(database, CesLoyaltyAuthDB)
        
        # Test that the database has the expected attributes (some may be None)
        self.assertTrue(hasattr(database, 'CONVERSATION_STATUS'))
        self.assertTrue(hasattr(database, 'SESSION_STATUS'))
        self.assertTrue(hasattr(database, 'AUTH_RESULT'))
        self.assertTrue(hasattr(database, 'AUTH_STATUS'))
        self.assertTrue(hasattr(database, 'OFFER_ENROLLMENT'))
        self.assertTrue(hasattr(database, 'PROFILE_BEFORE_AUTH'))
        self.assertTrue(hasattr(database, 'PROFILE_AFTER_AUTH'))
        self.assertTrue(hasattr(database, 'use_real_datastore'))
        self.assertTrue(hasattr(database, 'end_of_conversation_status'))


if __name__ == "__main__":
    unittest.main()
