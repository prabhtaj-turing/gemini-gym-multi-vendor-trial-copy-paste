import unittest
import unittest.mock
import sys
import os
import tempfile
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from ..SimulationEngine.db_models import CesAccountManagementDB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import (
    DB,
    reset_db,
    save_state,
    load_state,
    get_database,
    get_minified_state,
    load_default_data
)


class TestAccountManagementDBState(BaseTestCaseWithErrorHandler):
    """
    Test suite for Account Management database state management.
    Tests database initialization, state persistence, and data integrity.
    """

    def setUp(self):
        """Set up test fixtures before each test method."""
        reset_db()

    def tearDown(self):
        """Clean up after each test method."""
        reset_db()

    def test_initial_db_structure(self):
        """Test that DB has the correct initial structure."""
        expected_keys = [
            "accountDetails",
            "availablePlans",
            "_end_of_conversation_status",
        ]

        for key in expected_keys:
            self.assertIn(key, DB)

    def test_reset_db_functionality(self):
        """Test that reset_db properly clears the database."""
        # Add some data
        DB["test_key"] = "test_value"
        DB["accountDetails"] = {"test_id": {"test": "data"}}

        # Reset and verify
        reset_db()

        # Check that core structure exists but is empty/default
        self.assertIn("accountDetails", DB)
        self.assertEqual(DB["accountDetails"], {})
        self.assertNotIn("test_key", DB)

    def test_load_default_data(self):
        """Test loading default data from CesAccountManagementDefaultDB.json."""
        db_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "DBs",
            "CesAccountManagementDefaultDB.json",
        )
        load_state(db_path)

        # Verify that data was loaded
        self.assertIsInstance(DB["accountDetails"], dict)
        self.assertGreater(len(DB["accountDetails"]), 0)

        # Verify structure of first account
        if DB["accountDetails"]:
            account = next(iter(DB["accountDetails"].values()))
            self.assertIn("accountId", account)
            self.assertIn("customerName", account)
            self.assertIn("devices", account)
            self.assertIn("services", account)

    def test_available_plans_structure(self):
        """Test that available plans have the correct structure."""
        db_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "DBs",
            "CesAccountManagementDefaultDB.json",
        )
        load_state(db_path)

        self.assertIn("availablePlans", DB)
        available_plans = DB["availablePlans"]

        if "plans" in available_plans:
            plans = available_plans["plans"]
            self.assertIsInstance(plans, dict)

            for plan in plans.values():
                self.assertIn("id", plan)
                self.assertIn("name", plan)
                self.assertIn("type", plan)
                self.assertIn("monthlyCost", plan)

    def test_account_details_structure(self):
        """Test that account details have the expected structure."""
        db_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "DBs",
            "CesAccountManagementDefaultDB.json",
        )
        load_state(db_path)

        accounts = DB["accountDetails"]
        self.assertIsInstance(accounts, dict)

        if accounts:
            account = next(iter(accounts.values()))

            # Required fields
            required_fields = ["accountId", "customerName", "devices", "services"]
            for field in required_fields:
                self.assertIn(field, account)

            # Test devices structure
            if account["devices"]:
                device = account["devices"][0]
                device_fields = ["deviceId", "deviceName", "lineNumber"]
                for field in device_fields:
                    self.assertIn(field, device)

            # Test services structure
            if account["services"]:
                service = account["services"][0]
                service_fields = ["serviceId", "planId", "planName", "monthlyCost"]
                for field in service_fields:
                    self.assertIn(field, service)

    def test_db_persistence_operations(self):
        """Test save_state and load_state operations."""
        # Load default data
        db_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "DBs",
            "CesAccountManagementDefaultDB.json",
        )
        load_state(db_path)
        original_accounts = DB["accountDetails"].copy()

        # Save to temporary file
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".json"
        ) as temp_file:
            temp_path = temp_file.name

        try:
            save_state(temp_path)

            # Reset and reload
            reset_db()
            self.assertEqual(DB["accountDetails"], {})

            load_state(temp_path)

            # Verify data was restored
            self.assertEqual(DB["accountDetails"], original_accounts)

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_data_integrity_after_operations(self):
        """Test that data integrity is maintained after various operations."""
        db_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "DBs",
            "CesAccountManagementDefaultDB.json",
        )
        load_state(db_path)

        # Store original state
        original_state = {
            "accountDetails": DB["accountDetails"].copy(),
            "availablePlans": DB["availablePlans"].copy(),
        }

        # Perform some operations
        if DB["accountDetails"]:
            # Modify an account
            first_account_id = next(iter(DB["accountDetails"].keys()))
            DB["accountDetails"][first_account_id]["contactEmail"] = "modified@example.com"

            # Verify modification
            self.assertEqual(
                DB["accountDetails"][first_account_id]["contactEmail"], "modified@example.com"
            )

            # Verify other data unchanged
            self.assertEqual(
                len(DB["accountDetails"]), len(original_state["accountDetails"])
            )

    def test_database_concurrent_access_safety(self):
        """Test that database can handle concurrent-like access patterns."""
        db_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "DBs",
            "CesAccountManagementDefaultDB.json",
        )
        load_state(db_path)

        # Simulate multiple reads
        for _ in range(10):
            accounts = DB["accountDetails"]
            self.assertIsInstance(accounts, dict)

        # Simulate multiple modifications
        if DB["accountDetails"]:
            first_account_id = next(iter(DB["accountDetails"].keys()))
            original_email = DB["accountDetails"][first_account_id].get("contactEmail")

            for i in range(5):
                DB["accountDetails"][first_account_id]["contactEmail"] = f"test{i}@example.com"

            # Verify final state
            self.assertEqual(
                DB["accountDetails"][first_account_id]["contactEmail"], "test4@example.com"
            )

    def test_use_real_datastore_flag(self):
        """Test the use_real_datastore flag functionality."""
        self.assertIn("use_real_datastore", DB)
        self.assertIsInstance(DB["use_real_datastore"], bool)
        self.assertFalse(DB["use_real_datastore"])  # Should default to False

        # Test toggling
        DB["use_real_datastore"] = True
        self.assertTrue(DB["use_real_datastore"])

    def test_end_of_conversation_status(self):
        """Test the end of conversation status tracking."""
        self.assertIn("_end_of_conversation_status", DB)
        self.assertIsInstance(DB["_end_of_conversation_status"], dict)

        # Test setting status
        DB["_end_of_conversation_status"]["escalate"] = "test reason"
        self.assertEqual(DB["_end_of_conversation_status"]["escalate"], "test reason")

    def test_load_state_file_not_found(self):
        """
        Tests that a warning is printed when load_state cannot find the file.
        """
        with unittest.mock.patch("builtins.print") as mock_print:
            load_state("non_existent_file.json")
            mock_print.assert_called_with(
                "Warning: Could not load state from non_existent_file.json: "
                "[Errno 2] No such file or directory: 'non_existent_file.json'"
            )

    def test_get_database_function(self):
        """
        Tests that get_database() returns a CesAccountManagementDB instance.
        """
        # Test that get_database returns a Pydantic model instance
        database = get_database()
        self.assertIsNotNone(database)
        self.assertIsInstance(database, CesAccountManagementDB)
        
        # Test that the database has the expected attributes
        self.assertTrue(hasattr(database, 'error_simulator'))
        self.assertTrue(hasattr(database, 'end_of_conversation_status'))
        self.assertTrue(hasattr(database, 'use_real_datastore'))
        self.assertTrue(hasattr(database, 'accountDetails'))
        
    def test_load_state_json_decode_error(self):
        """
        Tests that a warning is printed when load_state encounters a JSON decode error.
        """
        # Create a temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file.write("invalid json content {")
            temp_file_path = temp_file.name
        
        try:
            with unittest.mock.patch("builtins.print") as mock_print:
                load_state(temp_file_path)
                mock_print.assert_called()
                # Check that a warning was printed about JSON decode error
                warning_calls = [call for call in mock_print.call_args_list 
                               if "Warning: Could not load state from" in str(call)]
                self.assertTrue(len(warning_calls) > 0)
        finally:
            os.unlink(temp_file_path)

    def test_load_default_data_name_error(self):
        """
        Tests the fallback path in load_default_data when a NameError occurs.
        """
        with unittest.mock.patch(
            "os.path.dirname", side_effect=NameError("Simulated NameError")
        ):
            with unittest.mock.patch("builtins.print") as mock_print:
                load_default_data()
                # The function should handle the NameError gracefully
                # and try the fallback path

    def test_load_state_validation_error(self):
        """
        Tests that a warning is printed when load_state encounters a validation error.
        """
        # Create a temporary file with invalid data that will cause validation to fail
        invalid_data = {
            "error_simulator": {"example_function_name": []},
            "end_of_conversation_status": {"escalate": None, "fail": None, "cancel": None},
            "use_real_datastore": False,
            "accountDetails": {
                "invalid_account": {
                    "accountId": "invalid_account",
                    "isVerified": "invalid_boolean",  # This should cause validation to fail
                    "customerName": "Test Customer",
                    "contactEmail": "test@example.com",
                    "contactPhone": "555-123-4567",
                    "billingAddress": {
                        "recipientName": "Test Customer",
                        "streetAddressLine1": "123 Main St",
                        "city": "Test City",
                        "state": "TS",
                        "zipCode": "12345",
                        "country": "USA"
                    },
                    "serviceAddress": {
                        "recipientName": "Test Customer",
                        "streetAddressLine1": "123 Main St",
                        "city": "Test City",
                        "state": "TS",
                        "zipCode": "12345",
                        "country": "USA"
                    },
                    "communicationPreferences": {
                        "emailOptIn": True,
                        "smsOptIn": False
                    },
                    "services": [],
                    "devices": [],
                    "securityPinSet": False
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(invalid_data, temp_file)
            temp_file_path = temp_file.name
        
        try:
            with unittest.mock.patch("builtins.print") as mock_print:
                load_state(temp_file_path)
                # Check that a warning was printed about data validation failure
                mock_print.assert_called()
                # The call should contain the warning message about data validation failure
                warning_calls = [call for call in mock_print.call_args_list 
                               if "Warning: Data validation failed" in str(call)]
                self.assertTrue(len(warning_calls) > 0)
        finally:
            os.unlink(temp_file_path)

    def test_get_minified_state_function(self):
        """
        Tests that get_minified_state() returns the current database state.
        """        
        # Test that get_minified_state returns the current DB state
        state = get_minified_state()
        self.assertIsNotNone(state)
        self.assertIsInstance(state, dict)
        
        # Test that it contains the expected keys
        self.assertIn("accountDetails", state)
        self.assertIn("availablePlans", state)
        self.assertIn("_end_of_conversation_status", state)
        self.assertIn("use_real_datastore", state)
        
        # Test that it's the same as the global DB
        self.assertEqual(state, DB)


if __name__ == "__main__":
    unittest.main()
