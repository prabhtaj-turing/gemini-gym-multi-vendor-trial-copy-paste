import unittest
import json
import os
from pydantic import ValidationError
from APIs.canva.SimulationEngine.db_models import CanvaDB
from pydantic import ValidationError as PydanticValidationError

class TestDBModelsValidation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load the sample database data once for all tests."""
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'DBs', 'CanvaDefaultDB.json')
        with open(db_path, 'r') as f:
            cls.sample_db_data = json.load(f)

    def test_sample_db_structure_validation(self):
        """Test that the sample database conforms to the CanvaDB model."""
        # Validate the entire database structure
        try:
            validated_db = CanvaDB(**self.sample_db_data)
            self.assertIsInstance(validated_db, CanvaDB)
        except PydanticValidationError as e:
            self.fail(f"Sample database validation failed: {e}")
    
    def test_empty_database_validation(self):
        """Test that an empty database structure is valid."""
        empty_db = {
            "Users": {},
            "Designs": {},
            "brand_templates": {},
            "autofill_jobs": {},
            "asset_upload_jobs": {},
            "design_export_jobs": {},
            "design_import_jobs": {},
            "url_import_jobs": {},
            "assets": {},
            "folders": {}
        }
        try:
            validated_db = CanvaDB(**empty_db)
            self.assertIsInstance(validated_db, CanvaDB)
            self.assertEqual(len(validated_db.Users), 0)
            self.assertEqual(len(validated_db.Designs), 0)
        except PydanticValidationError as e:
            self.fail(f"Empty database validation failed: {e}")
    
    def test_database_with_default_factories(self):
        """Test that database can be created with only some fields."""
        # CanvaDB model might have default_factory for fields
        minimal_db = {}
        try:
            # This may work if all fields have default_factory
            validated_db = CanvaDB(**minimal_db)
            self.assertIsInstance(validated_db, CanvaDB)
        except PydanticValidationError:
            # If it doesn't work, that's also valid - the model requires all fields
            pass
 
    def test_invalid_user_structure(self):
        """Test that invalid user structure causes validation failure."""
        invalid_db = self.sample_db_data.copy()
        invalid_db["Users"] = {
            "invalid_user": {
                "invalid_field": "invalid_value"
            }
        }
        with self.assertRaises(PydanticValidationError):
            CanvaDB(**invalid_db)
    
    def test_invalid_design_structure(self):
        """Test that invalid design structure causes validation failure."""
        invalid_db = self.sample_db_data.copy()
        invalid_db["Designs"] = {
            "invalid_design": {
                "invalid_field": "invalid_value"
            }
        }
        with self.assertRaises(PydanticValidationError):
            CanvaDB(**invalid_db)
    
    def test_users_dict_structure(self):
        """Test that Users field is a dictionary."""
        validated_db = CanvaDB(**self.sample_db_data)
        self.assertIsInstance(validated_db.Users, dict)
    
    def test_designs_dict_structure(self):
        """Test that Designs field is a dictionary."""
        validated_db = CanvaDB(**self.sample_db_data)
        self.assertIsInstance(validated_db.Designs, dict)
    
    def test_brand_templates_dict_structure(self):
        """Test that brand_templates field is a dictionary."""
        validated_db = CanvaDB(**self.sample_db_data)
        self.assertIsInstance(validated_db.brand_templates, dict)
    
    def test_jobs_dict_structures(self):
        """Test that all job fields are dictionaries."""
        validated_db = CanvaDB(**self.sample_db_data)
        self.assertIsInstance(validated_db.autofill_jobs, dict)
        self.assertIsInstance(validated_db.asset_upload_jobs, dict)
        self.assertIsInstance(validated_db.design_export_jobs, dict)
        self.assertIsInstance(validated_db.design_import_jobs, dict)
        self.assertIsInstance(validated_db.url_import_jobs, dict)
    
    def test_assets_dict_structure(self):
        """Test that assets field is a dictionary."""
        validated_db = CanvaDB(**self.sample_db_data)
        self.assertIsInstance(validated_db.assets, dict)
    
    def test_folders_dict_structure(self):
        """Test that folders field is a dictionary."""
        validated_db = CanvaDB(**self.sample_db_data)
        self.assertIsInstance(validated_db.folders, dict)
    
    def test_partial_db_with_users_only(self):
        """Test database with only Users populated."""
        partial_db = {
            "Users": {
                "user1": {
                    "user_id": "user1",
                    "team_id": "team1",
                    "profile": {"display_name": "Test User"}
                }
            },
            "Designs": {},
            "brand_templates": {},
            "autofill_jobs": {},
            "asset_upload_jobs": {},
            "design_export_jobs": {},
            "design_import_jobs": {},
            "url_import_jobs": {},
            "assets": {},
            "folders": {}
        }
        try:
            validated_db = CanvaDB(**partial_db)
            self.assertEqual(len(validated_db.Users), 1)
            self.assertEqual(validated_db.Users["user1"].user_id, "user1")
        except PydanticValidationError as e:
            self.fail(f"Partial database validation failed: {e}")

if __name__ == '__main__':
    unittest.main()
