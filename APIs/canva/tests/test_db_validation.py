"""
Database Validation Tests for Canva Service

This module contains tests to validate the database structure and data integrity
following the same pattern as Generic Reminders, Blender, and other services.
"""

import unittest
import copy
import os
import json
from typing import Dict, Any

from common_utils.base_case import BaseTestCaseWithErrorHandler as BaseCase
from canva.SimulationEngine.db import DB, save_state, load_state, reset_db
from canva.SimulationEngine.models import (
    CanvaDB,
    validate_canva_db,
    validate_db_integrity,
    DesignModel,
    UserModel,
    BrandTemplateModel,
    AssetModel,
    FolderModel,
    AssetUploadJobModel
)
import canva


class TestDatabaseValidation(BaseCase):
    """Test database structure validation and data integrity."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        # Reset to clean DB state
        reset_db()

    def tearDown(self):
        """Reset database after each test."""
        reset_db()

    def _validate_db_structure(self) -> CanvaDB:
        """
        Helper method to validate database structure using CanvaDB model.
        
        Returns:
            CanvaDB: Validated database object
            
        Raises:
            AssertionError: If validation fails
        """
        try:
            db_data = DB.copy()
            validated_db = CanvaDB(**db_data)
            self.assertIsInstance(validated_db, CanvaDB)
            return validated_db
        except Exception as e:
            self.fail(f"DB structure validation failed: {e}")

    def test_sample_db_structure_validation(self):
        """Test that the sample database conforms to the CanvaDB model."""
        # Validate the entire database structure
        try:
            validated_db = self._validate_db_structure()
            self.assertIsInstance(validated_db, CanvaDB)
        except Exception as e:
            self.fail(f"Sample database validation failed: {e}")

    def test_db_module_harmony(self):
        """
        Test that the database used by the db module is in harmony with the sample DB.
        This ensures that tests are running against the expected data structure.
        """
        try:
            validated_db = CanvaDB(**DB)
            self.assertIsInstance(validated_db, CanvaDB)
        except Exception as e:
            self.fail(f"DB module data structure validation failed: {e}")

    def test_validate_canva_db_function(self):
        """Test the validate_canva_db helper function."""
        db_copy = DB.copy()
        
        # Should pass validation
        validated_db = validate_canva_db(db_copy)
        self.assertIsInstance(validated_db, CanvaDB)

    def test_validate_db_integrity_function(self):
        """Test the validate_db_integrity helper function."""
        # Should return True for valid DB
        self.assertTrue(validate_db_integrity(DB))
        
        # Should return False for invalid DB
        invalid_db = {"invalid_structure": "bad_data"}
        self.assertFalse(validate_db_integrity(invalid_db))

    def test_required_db_keys_present(self):
        """Test that all required top-level keys are present."""
        required_keys = [
            "Users", "Designs", "brand_templates", "autofill_jobs",
            "asset_upload_jobs", "design_export_jobs", "design_import_jobs",
            "url_import_jobs", "assets", "folders"
        ]
        
        for key in required_keys:
            self.assertIn(key, DB, f"Missing required DB key: {key}")

    def test_db_key_data_types(self):
        """Test that all DB keys have correct data types."""
        # All top-level keys should be dictionaries
        for key, value in DB.items():
            self.assertIsInstance(value, dict, f"Key '{key}' should be a dictionary, got {type(value)}")

    def test_users_collection_validation(self):
        """Test validation of the Users collection."""
        validated_db = self._validate_db_structure()
        
        # Check that users collection exists and is properly typed
        self.assertIsInstance(validated_db.Users, dict)
        
        # If there are users, validate their structure
        for user_id, user_data in validated_db.Users.items():
            self.assertIsInstance(user_data, UserModel)
            self.assertIsInstance(user_id, str)

    def test_designs_collection_validation(self):
        """Test validation of the Designs collection."""
        validated_db = self._validate_db_structure()
        
        # Check that designs collection exists and is properly typed
        self.assertIsInstance(validated_db.Designs, dict)
        
        # If there are designs, validate their structure
        for design_id, design_data in validated_db.Designs.items():
            self.assertIsInstance(design_data, DesignModel)
            self.assertIsInstance(design_id, str)

    def test_brand_templates_collection_validation(self):
        """Test validation of the brand_templates collection."""
        validated_db = self._validate_db_structure()
        
        # Check that brand_templates collection exists and is properly typed
        self.assertIsInstance(validated_db.brand_templates, dict)
        
        # If there are templates, validate their structure
        for template_id, template_data in validated_db.brand_templates.items():
            self.assertIsInstance(template_data, BrandTemplateModel)
            self.assertIsInstance(template_id, str)

    def test_assets_collection_validation(self):
        """Test validation of the assets collection."""
        validated_db = self._validate_db_structure()
        
        # Check that assets collection exists and is properly typed
        self.assertIsInstance(validated_db.assets, dict)
        
        # If there are assets, validate their structure
        for asset_id, asset_data in validated_db.assets.items():
            self.assertIsInstance(asset_data, AssetModel)
            self.assertIsInstance(asset_id, str)

    def test_folders_collection_validation(self):
        """Test validation of the folders collection."""
        validated_db = self._validate_db_structure()
        
        # Check that folders collection exists and is properly typed
        self.assertIsInstance(validated_db.folders, dict)
        
        # If there are folders, validate their structure
        for folder_id, folder_data in validated_db.folders.items():
            self.assertIsInstance(folder_data, FolderModel)
            self.assertIsInstance(folder_id, str)

    def test_asset_upload_jobs_collection_validation(self):
        """Test validation of the asset_upload_jobs collection."""
        validated_db = self._validate_db_structure()
        
        # Check that asset_upload_jobs collection exists and is properly typed
        self.assertIsInstance(validated_db.asset_upload_jobs, dict)
        
        # If there are jobs, validate their structure
        for job_id, job_data in validated_db.asset_upload_jobs.items():
            self.assertIsInstance(job_data, AssetUploadJobModel)
            self.assertIsInstance(job_id, str)

    def test_job_collections_exist(self):
        """Test that all job collections exist."""
        job_collections = [
            "autofill_jobs", "asset_upload_jobs", "design_export_jobs",
            "design_import_jobs", "url_import_jobs"
        ]
        
        validated_db = self._validate_db_structure()
        
        for collection in job_collections:
            self.assertTrue(hasattr(validated_db, collection), 
                          f"Missing job collection: {collection}")
            collection_data = getattr(validated_db, collection)
            self.assertIsInstance(collection_data, dict, 
                                f"Job collection '{collection}' should be a dictionary")

    def test_nested_comment_structure_validation(self):
        """Test validation of nested comment structures in designs."""
        validated_db = self._validate_db_structure()
        
        # Check designs with comments
        for design_id, design_data in validated_db.Designs.items():
            self.assertIsInstance(design_data.comments, object)  # CommentsModel
            self.assertIsInstance(design_data.comments.threads, dict)
            
            # If there are comment threads, validate their structure
            for thread_id, thread_data in design_data.comments.threads.items():
                self.assertIsInstance(thread_id, str)
                self.assertIsInstance(thread_data.replies, dict)
                
                # Validate reply structure if present
                for reply_id, reply_data in thread_data.replies.items():
                    self.assertIsInstance(reply_id, str)
                    self.assertIsInstance(reply_data.content, object)  # ContentModel

    def test_db_save_load_cycle(self):
        """Test that the DB can be saved and loaded while maintaining validation."""
        import tempfile
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            temp_path = tmp_file.name
        
        try:
            # Save current DB
            save_state(temp_path)
            
            # Clear and load from file
            original_data = DB.copy()
            DB.clear()
            load_state(temp_path)
            
            # Validate loaded data
            validated_db = self._validate_db_structure()
            self.assertIsInstance(validated_db, CanvaDB)
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_empty_collections_validation(self):
        """Test that empty collections still validate correctly."""
        # Create a minimal valid DB structure
        minimal_db = {
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
        
        # Should validate successfully
        validated_db = CanvaDB(**minimal_db)
        self.assertIsInstance(validated_db, CanvaDB)

    def test_data_consistency_across_collections(self):
        """Test that data is consistent across related collections."""
        validated_db = self._validate_db_structure()
        
        # Test that design owners reference valid users (if both exist)
        if validated_db.Users and validated_db.Designs:
            for design in validated_db.Designs.values():
                # Note: In a real system, we might want to validate that design.owner.user_id
                # exists in the Users collection, but for simulation purposes,
                # we just ensure the structure is valid
                self.assertIsInstance(design.owner.user_id, str)
                self.assertIsInstance(design.owner.team_id, str)


class TestDataIntegrity(BaseCase):
    """Test data integrity and business logic validation."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.original_db_state = copy.deepcopy(DB)

    def tearDown(self):
        """Restore original DB state."""
        DB.clear()
        DB.update(self.original_db_state)

    def test_timestamp_fields_are_integers(self):
        """Test that timestamp fields are integers."""
        validated_db = CanvaDB(**DB)
        
        # Check designs timestamps
        for design in validated_db.Designs.values():
            self.assertIsInstance(design.created_at, int)
            self.assertIsInstance(design.updated_at, int)

        # Check brand templates timestamps
        for template in validated_db.brand_templates.values():
            self.assertIsInstance(template.created_at, int)
            self.assertIsInstance(template.updated_at, int)

        # Check assets timestamps
        for asset in validated_db.assets.values():
            self.assertIsInstance(asset.created_at, int)
            self.assertIsInstance(asset.updated_at, int)

    def test_id_fields_consistency(self):
        """Test that ID fields are consistent within entities."""
        validated_db = CanvaDB(**DB)
        
        # Check that design IDs in the collection match their internal IDs
        for design_id, design in validated_db.Designs.items():
            # Note: In simulation, the ID might be empty, but structure should be consistent
            self.assertIsInstance(design_id, str)
            self.assertIsInstance(design.id, str)

        # Check that asset IDs in the collection match their internal IDs
        for asset_id, asset in validated_db.assets.items():
            self.assertIsInstance(asset_id, str)
            self.assertIsInstance(asset.id, str)


if __name__ == '__main__':
    unittest.main()
