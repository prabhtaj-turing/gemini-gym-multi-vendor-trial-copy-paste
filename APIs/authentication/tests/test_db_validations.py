import unittest
import copy

from ..SimulationEngine.db import DB, get_minified_state
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestAuthenticationDBValidations(BaseTestCaseWithErrorHandler):
    """Test suite for authentication database validation."""

    def setUp(self):
        """Set up a clean, validated database before each test."""
        self.db_backup = copy.deepcopy(DB)

    def tearDown(self):
        """Restore the original database state after each test."""
        DB.clear()
        DB.update(self.db_backup)

    def test_db_structure_harmony(self):
        """
        Test that the database schema is in harmony with expected structure.
        """
        try:
            self._validate_db_structure(DB)
            self.assertTrue(True, "Database structure validation passed")
        except (AssertionError, KeyError, TypeError) as e:
            self.fail(f"Database structure validation failed: {e}")

    def test_setup_data_is_valid(self):
        """
        Test that the expected services are present and valid in the DB.
        """
        # Check some known services are present
        for service_name in ["airline", "gmail", "slack", "stripe"]:
            with self.subTest(service=service_name):
                self.assertIn(service_name, DB["services"])
                service_data = DB["services"][service_name]
                self.assertEqual(service_data["name"], service_name)
                self.assertIsInstance(service_data["description"], str)
                self.assertGreater(len(service_data["description"]), 0)

        # Test that the structure is valid
        self._validate_db_structure(DB)

    def test_db_structure_exists(self):
        """Test that the DB has the expected top-level structure."""
        self.assertIsInstance(DB, dict, "DB should be a dictionary")

        # Check for expected top-level keys
        expected_keys = {"services", "authentication_sessions", "authentication_logs"}

        actual_keys = set(DB.keys())
        self.assertTrue(
            expected_keys.issubset(actual_keys),
            f"DB missing required keys: {expected_keys - actual_keys}",
        )

    def test_services_section_structure(self):
        """Test that the services section has correct structure."""
        self.assertIn("services", DB)
        services = DB["services"]
        self.assertIsInstance(services, dict, "Services should be a dictionary")
        self.assertGreater(len(services), 0, "Services dictionary should not be empty")

        # Check that we have expected core services
        expected_services = ["airline", "gmail", "slack", "stripe", "github", "gdrive"]
        for service_name in expected_services:
            self.assertIn(
                service_name,
                services,
                f"Core service '{service_name}' should be present",
            )

    def test_all_services_have_required_fields(self):
        """Test that all services have required name and description fields."""
        services = DB["services"]
        required_fields = {"name", "description"}

        for service_name, service_data in services.items():
            with self.subTest(service=service_name):
                self.assertIsInstance(
                    service_data,
                    dict,
                    f"Service {service_name} data should be a dictionary",
                )

                actual_fields = set(service_data.keys())
                missing_fields = required_fields - actual_fields
                self.assertEqual(
                    len(missing_fields),
                    0,
                    f"Service {service_name} missing fields: {missing_fields}",
                )

    def test_service_data_types(self):
        """Test that service entries have correct data types."""
        services = DB["services"]

        for service_name, service_data in services.items():
            with self.subTest(service=service_name):
                self.assertIsInstance(service_data, dict)
                if "name" in service_data:
                    self.assertIsInstance(service_data["name"], str)
                if "description" in service_data:
                    self.assertIsInstance(service_data["description"], str)

    def test_service_keys_are_strings(self):
        """Test that service keys are strings."""
        services = DB["services"]

        for service_key in services.keys():
            with self.subTest(service=service_key):
                self.assertIsInstance(
                    service_key, str, f"Service key should be string: {service_key}"
                )

    def test_service_descriptions_are_strings(self):
        """Test that service descriptions are strings."""
        services = DB["services"]

        for service_name, service_data in services.items():
            with self.subTest(service=service_name):
                description = service_data.get("description", "")

                # Should be a string
                self.assertIsInstance(
                    description,
                    str,
                    f"Service {service_name} description should be string",
                )

    def test_authentication_sessions_structure(self):
        """Test that authentication_sessions has correct structure."""
        self.assertIn("authentication_sessions", DB)
        sessions = DB["authentication_sessions"]
        self.assertIsInstance(
            sessions, dict, "Authentication sessions should be a dictionary"
        )

    def test_authentication_logs_structure(self):
        """Test that authentication_logs has correct structure."""
        self.assertIn("authentication_logs", DB)
        logs = DB["authentication_logs"]
        self.assertIsInstance(logs, list, "Authentication logs should be a list")

    def test_get_minified_state_function(self):
        """Test that get_minified_state function works correctly."""
        try:
            minified_state = get_minified_state()
            self.assertIsInstance(minified_state, dict)
            self.assertEqual(minified_state, DB, "get_minified_state should return DB")
        except Exception as e:
            self.fail(f"get_minified_state function failed: {e}")

    def test_db_serializable(self):
        """Test that the entire DB structure is JSON serializable."""
        import json

        try:
            json_str = json.dumps(DB)
            self.assertIsInstance(json_str, str)

            # Should be able to deserialize back
            deserialized = json.loads(json_str)
            self.assertIsInstance(deserialized, dict)

        except (TypeError, ValueError) as e:
            self.fail(f"DB is not JSON serializable: {e}")

    def test_service_directory_structure_exists(self):
        """Test that API directory structure exists."""
        import os

        # Just check if APIs directory exists - don't require specific alignment
        apis_path = os.path.join(os.path.dirname(__file__), "..", "..", "..")
        self.assertTrue(os.path.exists(apis_path), "APIs directory should exist")

    def test_real_services_data_integrity(self):
        """Test that the actual services in DB have correct data."""
        services = DB["services"]

        # Test specific services that we know exist
        expected_services = {
            "airline": "Airline booking and management",
            "azure": "Microsoft Azure cloud services",
            "gmail": "Google email service",
            "github": "Git repository hosting service",
            "slack": "Team communication platform",
            "stripe": "Payment processing platform",
            "zendesk": "Customer service platform",
        }

        for service_name, expected_description in expected_services.items():
            with self.subTest(service=service_name):
                self.assertIn(service_name, services)
                service_data = services[service_name]
                self.assertEqual(service_data["name"], service_name)
                self.assertEqual(service_data["description"], expected_description)

    # Helper methods for validation

    def _validate_db_structure(self, db):
        """Validate the overall DB structure."""
        if not isinstance(db, dict):
            raise AssertionError("DB must be a dictionary")

        required_keys = {"services", "authentication_sessions", "authentication_logs"}
        missing_keys = required_keys - set(db.keys())
        if missing_keys:
            raise AssertionError(f"DB missing required keys: {missing_keys}")

        if not isinstance(db["services"], dict):
            raise AssertionError("services must be a dictionary")

        if not isinstance(db["authentication_sessions"], dict):
            raise AssertionError("authentication_sessions must be a dictionary")

        if not isinstance(db["authentication_logs"], list):
            raise AssertionError("authentication_logs must be a list")

        # Validate a sample of services (not all to keep tests fast)
        for service_name in db["services"]:
            self._validate_service_data(service_name, db["services"][service_name])

    def _validate_service_data(self, service_name, service_data):
        """Validate individual service data."""
        if not isinstance(service_data, dict):
            raise AssertionError(f"Service {service_name} data must be a dictionary")

        required_fields = {"name", "description"}
        missing_fields = required_fields - set(service_data.keys())
        if missing_fields:
            raise AssertionError(
                f"Service {service_name} missing fields: {missing_fields}"
            )

        if not isinstance(service_data["name"], str):
            raise TypeError(f"Service {service_name} name must be a string")

        if not isinstance(service_data["description"], str):
            raise TypeError(f"Service {service_name} description must be a string")

        if not service_data["name"].strip():
            raise AssertionError(f"Service {service_name} name cannot be empty")

        if not service_data["description"].strip():
            raise AssertionError(f"Service {service_name} description cannot be empty")


if __name__ == "__main__":
    unittest.main()
