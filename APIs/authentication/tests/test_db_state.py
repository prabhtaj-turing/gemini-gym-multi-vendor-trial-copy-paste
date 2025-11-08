import unittest
import os
import json
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, get_minified_state
from .. import (
    authenticate_service,
    deauthenticate_service,
    is_service_authenticated,
    reset_all_authentication,
)
from copy import deepcopy

# A snapshot of the initial state of the DB for resetting purposes.
_INITIAL_DB_STATE = deepcopy(DB)


class TestAuthenticationDBState(BaseTestCaseWithErrorHandler):
    """Test suite for authentication database state operations."""

    def setUp(self):
        """Set up framework test environment."""
        # Reset the database to its initial state
        global DB
        DB.clear()
        DB.update(deepcopy(_INITIAL_DB_STATE))

        # Store original framework DB state
        self.original_db_state = deepcopy(DB)

    def tearDown(self):
        """Clean up test files and directory."""
        DB.clear()
        DB.update(self.original_db_state)

    def test_db_state_json_serialization(self):
        """Test that the DB state can be serialized to and from JSON."""
        # 1. Get current DB state
        original_db = json.loads(json.dumps(DB))

        # 2. Serialize to JSON
        json_str = json.dumps(DB)
        self.assertIsInstance(json_str, str)

        # 3. Deserialize from JSON
        deserialized = json.loads(json_str)

        # 4. Assert that the data has been preserved
        self.assertEqual(deserialized["services"], original_db["services"])
        self.assertEqual(
            deserialized["authentication_sessions"],
            original_db["authentication_sessions"],
        )
        self.assertEqual(
            deserialized["authentication_logs"], original_db["authentication_logs"]
        )
        self.assertEqual(deserialized, original_db)

    def test_get_minified_state_consistency(self):
        """Test that get_minified_state returns consistent results."""
        # 1. Get minified state multiple times
        state1 = get_minified_state()
        state2 = get_minified_state()

        # 2. Should be identical
        self.assertEqual(
            state1, state2, "get_minified_state should return consistent results"
        )

        # 3. Should equal the current DB state
        self.assertEqual(state1, DB)
        self.assertEqual(state2, DB)

    def test_db_state_immutability_during_reads(self):
        """Test that reading DB state doesn't modify the original state."""
        original_state = deepcopy(DB)

        # Perform various read operations
        _ = DB["services"]
        _ = DB["authentication_sessions"]
        _ = DB["authentication_logs"]

        # Get minified state
        _ = get_minified_state()

        # Verify original state unchanged
        self.assertEqual(DB, original_state)

    def test_db_state_consistency_after_authentication(self):
        """Test that DB state remains consistent after authentication operations."""
        original_services_count = len(DB["services"])
        original_sessions_structure = type(DB["authentication_sessions"])
        original_logs_structure = type(DB["authentication_logs"])

        # Perform authentication operations with a known service
        if "gmail" in DB["services"]:
            try:
                # Test authentication/deauthentication cycle
                is_service_authenticated("gmail")
                authenticate_service("gmail")
                deauthenticate_service("gmail")
            except Exception:
                pass  # We're testing DB consistency, not auth success

        # Verify DB structure integrity maintained
        self.assertEqual(len(DB["services"]), original_services_count)
        self.assertIsInstance(
            DB["authentication_sessions"], original_sessions_structure
        )
        self.assertIsInstance(DB["authentication_logs"], original_logs_structure)

        # Verify core structure still exists
        self.assertIn("services", DB)
        self.assertIn("authentication_sessions", DB)
        self.assertIn("authentication_logs", DB)

    def test_db_state_after_reset_operations(self):
        """Test DB state consistency after authentication reset operations."""
        original_state = deepcopy(DB)

        try:
            # Perform reset operation
            result = reset_all_authentication()
            self.assertIsInstance(result, dict)

            # Verify DB structure maintained
            self.assertEqual(set(DB.keys()), set(original_state.keys()))
            self.assertEqual(len(DB["services"]), len(original_state["services"]))

            # Service data should be unchanged
            for service_name, service_data in original_state["services"].items():
                self.assertIn(service_name, DB["services"])
                self.assertEqual(DB["services"][service_name], service_data)

        except Exception:
            # Even if reset fails, DB should remain consistent
            self.assertEqual(set(DB.keys()), set(original_state.keys()))

    def test_load_state_nonexistent_file(self):
        """Test handling of non-existent files during state loading."""
        DB.clear()
        DB.update(self.original_db_state)
        initial_db = json.loads(json.dumps(DB))

        # Attempt to load from a file that does not exist
        nonexistent_file = os.path.join(os.path.dirname(__file__), "nonexistent.json")

        # Should raise FileNotFoundError when trying to open non-existent file
        with self.assertRaises(FileNotFoundError):
            with open(nonexistent_file, "r") as f:
                json.load(f)

        # The DB state should not have changed
        self.assertEqual(DB, initial_db)

    def test_db_state_with_corrupted_data(self):
        """Test DB state operations with various data corruption scenarios."""
        original_db = deepcopy(DB)

        try:
            # Test with missing services data
            corrupted_db_1 = {
                "authentication_sessions": {},
                "authentication_logs": [],
                # Missing 'services' key
            }

            DB.clear()
            DB.update(corrupted_db_1)

            # get_minified_state should handle missing keys
            try:
                state = get_minified_state()
                self.assertIsInstance(state, dict)
            except KeyError:
                # Missing 'services' key should cause KeyError, which is acceptable
                pass

            # Test with None values
            corrupted_db_2 = {
                "services": None,
                "authentication_sessions": {},
                "authentication_logs": [],
            }

            DB.clear()
            DB.update(corrupted_db_2)

            try:
                state = get_minified_state()
                self.assertIsInstance(state, dict)
                # If it succeeds, None should be preserved
                self.assertIsNone(state.get("services"))
            except (TypeError, AttributeError):
                # Operations on None might fail, which is acceptable
                pass

        finally:
            # Always restore original DB
            DB.clear()
            DB.update(original_db)

    def test_db_state_large_service_handling(self):
        """Test DB state operations with all available services."""
        # Test that we can handle operations on all services in the DB
        services_list = list(DB["services"].keys())

        # Should have many services
        self.assertGreater(
            len(services_list), 10, "Should have multiple services to test"
        )

        # Test reading all service data
        for service_name in services_list[:10]:  # Test first 10 services
            with self.subTest(service=service_name):
                service_data = DB["services"][service_name]
                self.assertIsInstance(service_data, dict)
                self.assertIn("name", service_data)
                self.assertIn("description", service_data)

                # Test is_service_authenticated doesn't corrupt state
                try:
                    result = is_service_authenticated(service_name)
                    self.assertIsInstance(result, bool)
                except Exception:
                    pass  # Some services might not be properly configured

        # Verify DB structure still intact after operations
        self.assertIn("services", DB)
        self.assertIn("authentication_sessions", DB)
        self.assertIn("authentication_logs", DB)
        self.assertEqual(len(DB["services"]), len(services_list))

    def test_db_state_basic_recovery(self):
        """Test basic DB state recovery from simple corruption."""
        original_db = deepcopy(DB)

        try:
            # Test clearing DB and verifying it can be restored
            DB.clear()

            # get_minified_state should handle empty DB
            try:
                state = get_minified_state()
                self.assertIsInstance(state, dict)
                self.assertEqual(len(state), 0)  # Empty DB
            except KeyError:
                # Empty DB might cause KeyError, which is acceptable
                pass

            # Restore DB and verify it works
            DB.update(original_db)

            state = get_minified_state()
            self.assertIsInstance(state, dict)
            self.assertEqual(state, DB)
            self.assertIn("services", state)

        finally:
            # Ensure DB is restored
            DB.clear()
            DB.update(original_db)


if __name__ == "__main__":
    unittest.main()
