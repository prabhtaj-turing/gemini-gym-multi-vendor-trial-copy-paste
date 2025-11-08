"""
Test suite for CRUD utility functions in the Generic Service.

This file provides a template for testing the internal state-management
functions of the service. It demonstrates how to test both success and
error cases for each CRUD operation.

NOTE: These tests are skipped by default as they are part of a template.
Remove the @unittest.skip decorator to enable them in your new service.
"""

import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, reset_db
from ..SimulationEngine.models import GenericServiceDB, EntityStatus, EntityStorage
from ..SimulationEngine import utils
from ..SimulationEngine.custom_errors import ValidationError, ResourceNotFoundError
from pydantic import ValidationError as PydanticValidationError

#@unittest.skip("This is a template for service tests and is not meant to be run directly.")
class TestUtilsCrud(BaseTestCaseWithErrorHandler):
    
    def setUp(self):
        """Set up a clean, empty database before each test."""
        reset_db()
        DB.update(GenericServiceDB().model_dump())

    def tearDown(self):
        """Reset the database after each test to ensure test isolation."""
        reset_db()
        
    def validate_db(self):
        """
        Helper method to validate the current state of the database against the
        Pydantic model. This should be called after any operation that
        modifies the database to ensure its state remains valid.
        """
        try:
            GenericServiceDB(**DB)
        except PydanticValidationError as e:
            self.fail(f"Database validation failed: {e}")

    # --- Success Cases for Entity CRUD Operations ---

    def test_create_entity(self):
        """Test unique use case: Successfully creating a new entity."""
        entity = utils.create_entity(name="Test Entity", status=EntityStatus.ACTIVE)
        
        self.assertIn("id", entity)
        self.assertEqual(entity["name"], "Test Entity")
        
        db_entity = DB["entities"][entity["id"]]
        self.assertEqual(db_entity["name"], "Test Entity")
        self.validate_db()

    def test_get_entity(self):
        """Test unique use case: Retrieving an existing and non-existent entity."""
        entity = utils.create_entity(name="Get Me", status=EntityStatus.INACTIVE)
        self.validate_db()
        
        # Test getting an existing entity
        retrieved_entity = utils.get_entity(entity["id"])
        self.assertEqual(entity, retrieved_entity)
        
        # Test getting a non-existent entity
        retrieved_entity_none = utils.get_entity("nonexistent-id")
        self.assertIsNone(retrieved_entity_none)
        self.validate_db()

    def test_list_entities(self):
        """Test unique use case: Listing all created entities."""
        utils.create_entity(name="Entity 1", status=EntityStatus.ACTIVE)
        utils.create_entity(name="Entity 2", status=EntityStatus.ARCHIVED)
        
        entities = utils.list_entities()
        self.assertEqual(len(entities), 2)
        self.validate_db()

    def test_update_entity(self):
        """Test unique use case: Successfully updating an entity's fields."""
        entity = utils.create_entity(name="Initial Name", status=EntityStatus.ACTIVE)
        original_timestamp = entity["updated_at"]
        self.validate_db()
        
        updated_entity = utils.update_entity(entity["id"], name="Updated Name", status=EntityStatus.INACTIVE)
        
        self.assertEqual(updated_entity["name"], "Updated Name")
        self.assertEqual(updated_entity["status"], EntityStatus.INACTIVE.value)
        self.assertNotEqual(original_timestamp, updated_entity["updated_at"])
        self.validate_db()

    def test_delete_entity(self):
        """Test unique use case: Successfully deleting an entity."""
        entity = utils.create_entity(name="To Be Deleted", status=EntityStatus.ACTIVE)
        self.validate_db()
        
        was_deleted = utils.delete_entity(entity["id"])
        
        self.assertTrue(was_deleted)
        self.assertIsNone(utils.get_entity(entity["id"]))
        self.validate_db()

    # --- Error and Validation Cases ---

    def test_update_nonexistent_entity_raises_error(self):
        """Test error case: Updating a non-existent entity raises ResourceNotFoundError."""
        self.assert_error_behavior(
            lambda: utils.update_entity("nonexistent-id", name="New Name"),
            ResourceNotFoundError,
            "Entity with ID 'nonexistent-id' not found."
        )
        self.validate_db()

    def test_delete_nonexistent_entity_returns_false(self):
        """Test error case: Deleting a non-existent entity returns False."""
        was_deleted = utils.delete_entity("nonexistent-id")
        self.assertFalse(was_deleted)
        self.validate_db()

    def test_pydantic_validation_for_invalid_status(self):
        """Test validation case: EntityStorage model rejects an invalid status enum."""
        self.assert_error_behavior(
            lambda: EntityStorage(name="Invalid Entity", status="invalid_status"),
            PydanticValidationError,
            "Input should be 'active', 'inactive' or 'archived'"
        )

    def test_pydantic_validation_for_empty_id(self):
        """Test validation case: EntityStorage model rejects an empty string for an ID."""
        self.assert_error_behavior(
            lambda: EntityStorage(id="", name="Test", status=EntityStatus.ACTIVE),
            PydanticValidationError,
            "ID cannot be an empty string"
        )

    def test_pydantic_validation_for_invalid_uuid(self):
        """Test validation case: EntityStorage model rejects a non-UUID string for an ID."""
        self.assert_error_behavior(
            lambda: EntityStorage(id="not-a-uuid", name="Test", status=EntityStatus.ACTIVE),
            PydanticValidationError,
            "ID must be a valid UUID4 string"
        )

if __name__ == "__main__":
    unittest.main()
