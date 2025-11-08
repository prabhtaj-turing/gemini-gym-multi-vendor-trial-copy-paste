import unittest
import copy
import sys
import os
from pydantic import ValidationError

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ..SimulationEngine.db import DB
from ..SimulationEngine.models import SupabaseDB, Organization, Project, EdgeFunction, LogEntry, LogLevel, EdgeFunctionStatus, ProjectStatus
from common_utils.base_case import BaseTestCaseWithErrorHandler

# A known-good, minimal DB structure for validation.
SAMPLE_DB = {
    "organizations": [],
    "projects": [],
    "tables": {},
    "extensions": {},
    "migrations": {},
    "edge_functions": {},
    "branches": {},
    "costs": {},
    "unconfirmed_costs": {},
    "project_urls": {},
    "project_anon_keys": {},
    "project_ts_types": {},
    "logs": {}
}

class TestDBValidation(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Set up a clean, validated database before each test."""
        self.db_backup = copy.deepcopy(DB)
        DB.clear()
        DB.update(copy.deepcopy(SAMPLE_DB))

        # Create test data using Pydantic models for validation
        self.test_organization = Organization(
            id="org_1",
            name="Test Org",
            created_at="2023-01-01T00:00:00Z"
        )

        self.test_project = Project(
            id="project_1",
            name="Test Project",
            organization_id="org_1",
            region="us-west-1",
            status=ProjectStatus.ACTIVE_HEALTHY,
            created_at="2023-01-01T00:00:00Z",
            version="1.0"
        )
        
        self.test_edge_function = EdgeFunction(
            id="func_1",
            slug="test-func",
            name="Test Function",
            version="1",
            status=EdgeFunctionStatus.ACTIVE,
            created_at=1672531200,
            updated_at=1672531200
        )

        self.test_log_entry = LogEntry(
            timestamp="2023-01-01T00:00:00Z",
            level=LogLevel.INFO,
            message="Test log message"
        )

        # Add the validated data to the database
        DB["organizations"].append(self.test_organization.model_dump())
        DB["projects"].append(self.test_project.model_dump())
        DB["edge_functions"][self.test_project.id] = [self.test_edge_function.model_dump()]
        DB["logs"][self.test_project.id] = {"services": {"api": [self.test_log_entry.model_dump()]}}


    def tearDown(self):
        """Restore the original database state after each test."""
        DB.clear()
        DB.update(self.db_backup)

    def test_db_module_harmony(self):
        """
        Test that the database schema is in harmony with the Pydantic model.
        """
        try:
            validated_db = SupabaseDB(**DB)
            self.assertIsInstance(validated_db, SupabaseDB)
        except ValidationError as e:
            self.fail(f"Database schema validation failed: {e}")

    def test_pydantic_validation_error_on_invalid_data(self):
        """
        Test that a Pydantic ValidationError is raised for invalid data.
        """
        invalid_project_data = {
            "id": "project_2",
            "name": "Invalid Project",
            "organization_id": "org_1",
            "region": "us-west-1",
            "status": "INVALID_STATUS",  # Invalid status
            "created_at": "2023-01-01T00:00:00Z",
            "version": "1.0"
        }

        with self.assertRaises(ValidationError):
            Project(**invalid_project_data)

    def test_setup_data_is_valid(self):
        """
        Test that the data added in setUp is valid and present in the DB.
        """
        self.assertEqual(len(DB["organizations"]), 1)
        self.assertEqual(DB["organizations"][0]["name"], "Test Org")

        self.assertEqual(len(DB["projects"]), 1)
        self.assertEqual(DB["projects"][0]["name"], "Test Project")

        self.assertIn(self.test_project.id, DB["edge_functions"])
        self.assertEqual(len(DB["edge_functions"][self.test_project.id]), 1)
        self.assertEqual(DB["edge_functions"][self.test_project.id][0]["name"], "Test Function")
        
        self.assertIn(self.test_project.id, DB["logs"])
        self.assertEqual(len(DB["logs"][self.test_project.id]["services"]["api"]), 1)
        self.assertEqual(DB["logs"][self.test_project.id]["services"]["api"][0]["message"], "Test log message")


if __name__ == "__main__":
    unittest.main()
