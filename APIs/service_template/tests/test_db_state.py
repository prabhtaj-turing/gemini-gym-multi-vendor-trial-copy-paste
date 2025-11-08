"""
Test suite for validating the database schema and default data.

NOTE: This test suite is ENABLED by default. It validates that the default
database file (e.g., ServiceTemplateDefaultDB.json) conforms to the Pydantic
models defined in the service. This is a crucial check to ensure the service
starts in a valid state.
"""

import unittest
import json
import os
from ..SimulationEngine.models import GenericServiceDB, EntityStatus
from ..SimulationEngine.db import DB

class TestDatabaseValidation(unittest.TestCase):
    """
    Test suite for validating the sample database against the Pydantic models
    for the generic service template.
    """

    @classmethod
    def setUpClass(cls):
        """
        Load the sample database data once for all tests.
        
        This method attempts to load a default DB file. If it doesn't exist,
        it uses an empty structure, allowing tests to run even without a
        pre-existing default DB file.
        """
        # TODO: Change 'ServiceTemplateDefaultDB.json' to the actual default DB file name
        db_filename = "ServiceTemplateDefaultDB.json"
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'DBs', db_filename)
        
        if os.path.exists(db_path):
            with open(db_path, 'r') as f:
                cls.sample_db_data = json.load(f)
        else:
            # If no default DB file exists, use an empty structure that matches the model
            print(f"Warning: Default DB file not found at {db_path}. Running tests against an empty schema.")
            cls.sample_db_data = {
                "entities": {}
            }

    def test_sample_db_structure_validation(self):
        """Test that the sample database conforms to the GenericServiceDB model."""
        try:
            validated_db = GenericServiceDB(**self.sample_db_data)
            self.assertIsInstance(validated_db, GenericServiceDB)
        except Exception as e:
            self.fail(f"Sample database validation failed: {e}")

    def test_db_module_harmony(self):
        """
        Test that the live database used by the db module is in harmony with the schema.
        This ensures that tests are running against the expected data structure.
        """
        try:
            validated_db = GenericServiceDB(**DB)
            self.assertIsInstance(validated_db, GenericServiceDB)
        except Exception as e:
            self.fail(f"DB module data structure validation failed: {e}")

    def test_entities_validation(self):
        """Test the validation of the 'entities' table."""
        self.assertIn("entities", self.sample_db_data)
        self.assertIsInstance(self.sample_db_data["entities"], dict)
        
        # Validate each entity in the table
        for entity_id, entity_data in self.sample_db_data["entities"].items():
            self.assertEqual(entity_id, entity_data.get("id"))
            self.assertIn("name", entity_data)
            self.assertIn("status", entity_data)
            self.assertIn("created_at", entity_data)
            self.assertIn("updated_at", entity_data)

    def test_entity_status_validation(self):
        """Test that entity statuses are valid enum values."""
        validated_db = GenericServiceDB(**self.sample_db_data)
        valid_statuses = {item.value for item in EntityStatus}
        
        for entity in validated_db.entities.values():
            self.assertIn(entity.status, valid_statuses)

    def test_timestamp_format_validation(self):
        """
        Test that timestamp formats are valid.
        The Pydantic models will automatically validate this on load.
        If this test is reached without a `ValidationError`, the validation has passed.
        """
        try:
            GenericServiceDB(**self.sample_db_data)
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Timestamp validation failed during model instantiation: {e}")

if __name__ == '__main__':
    unittest.main()
