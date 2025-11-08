#!/usr/bin/env python3
"""
Test cases for DefaultDB loading and saving functionality in Google People API.

This module tests the comprehensive DefaultDB functionality including:
1. DefaultDB loading on service startup
2. DefaultDB validation against Pydantic schema
3. DefaultDB save and load round-trip testing
4. DefaultDB error handling and edge cases
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, mock_open

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB, save_state, load_state, get_database, DEFAULT_DB_PATH
from ..SimulationEngine.db_models import GooglePeopleDB


class TestDefaultDBLoading(BaseTestCaseWithErrorHandler):
    """Test class for DefaultDB loading and saving functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset DB to ensure clean state
        DB.clear()
        # Load the actual default database using load_state
        load_state(DEFAULT_DB_PATH)

    def test_defaultdb_loads_on_startup(self):
        """Test that DefaultDB loads correctly on service startup."""
        # Verify that DB has data after startup
        self.assertIsNotNone(DB._data)
        self.assertIsInstance(DB._data, dict)
        
        # Verify that the data structure matches expected Google People format
        expected_keys = ["people", "contactGroups", "otherContacts", "directoryPeople"]
        for key in expected_keys:
            self.assertIn(key, DB._data, f"DefaultDB should contain '{key}' key")

    def test_load_state_with_actual_database_file(self):
        """Test load_state function by loading from actual database file."""
        # Clear the current DB to test loading from scratch
        DB.clear()
        
        # Load state from the actual default database file
        load_state(DEFAULT_DB_PATH)
        
        # Verify the database was loaded and validated by Pydantic
        self.assertIn('people', DB._data)
        self.assertIn('contactGroups', DB._data)
        self.assertIn('otherContacts', DB._data)
        self.assertIn('directoryPeople', DB._data)
        
        # Verify we have people loaded
        self.assertGreater(len(DB._data['people']), 0)
        
        # Test that we can get the database as a Pydantic model (this validates the data)
        db_model = get_database()
        self.assertIsInstance(db_model, GooglePeopleDB)

    def test_load_state_with_invalid_json(self):
        """Test load_state function with invalid JSON content."""
        # Create a temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_file.write('{ invalid json content }')
            temp_filepath = temp_file.name
        
        try:
            # Test load_state with invalid JSON
            with self.assertRaises(json.JSONDecodeError):
                load_state(temp_filepath)
        finally:
            # Clean up
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_defaultdb_validation_against_schema(self):
        """Test that DefaultDB data validates against GooglePeopleDB schema."""
        # Get the database as a Pydantic model
        db_model = get_database()
        
        # Verify it's the correct type
        self.assertIsInstance(db_model, GooglePeopleDB)
        
        # Verify the data structure
        self.assertIsInstance(db_model.people, dict)
        self.assertIsInstance(db_model.contact_groups, dict)
        self.assertIsInstance(db_model.other_contacts, dict)
        self.assertIsInstance(db_model.directory_people, dict)

    def test_defaultdb_people_data_structure(self):
        """Test that DefaultDB people data has correct structure."""
        db_model = get_database()
        
        # Verify people data structure
        for person_id, person in db_model.people.items():
            self.assertIsInstance(person_id, str)
            # Person is a Pydantic model, not a dict
            self.assertIsNotNone(person)
            
            # Verify required fields exist as attributes
            self.assertTrue(hasattr(person, 'resource_name'))
            self.assertTrue(hasattr(person, 'etag'))
            self.assertTrue(hasattr(person, 'names'))
            self.assertTrue(hasattr(person, 'phone_numbers'))
            self.assertTrue(hasattr(person, 'email_addresses'))

    def test_defaultdb_contact_groups_structure(self):
        """Test that DefaultDB contact groups have correct structure."""
        db_model = get_database()
        
        # Verify contact groups data structure
        for group_id, group in db_model.contact_groups.items():
            self.assertIsInstance(group_id, str)
            # Group is a Pydantic model, not a dict
            self.assertIsNotNone(group)
            
            # Verify required fields exist as attributes
            self.assertTrue(hasattr(group, 'resource_name'))
            self.assertTrue(hasattr(group, 'etag'))
            self.assertTrue(hasattr(group, 'name'))
            self.assertTrue(hasattr(group, 'member_resource_names'))

    def test_defaultdb_save_and_load_roundtrip(self):
        """Test DefaultDB save and load round-trip maintains data integrity."""
        # Get original data
        original_data = DB._data.copy()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Save current state (which includes DefaultDB)
            save_state(temp_filepath)
            
            # Clear DB and load from file
            DB.clear()
            load_state(temp_filepath)
            
            # Verify data integrity
            self.assertEqual(DB._data, original_data)
            
            # Verify Pydantic validation still works
            db_model = get_database()
            self.assertIsInstance(db_model, GooglePeopleDB)
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_defaultdb_validation_with_invalid_data(self):
        """Test DefaultDB validation fails with invalid data."""
        # Create invalid data with invalid resource name format
        invalid_data = {
            "people": {
                "invalid_person": {
                    "resourceName": "invalid_format",  # Should start with "people/"
                    "etag": "test-etag",
                    "names": [],
                    "emailAddresses": [],
                    "phoneNumbers": []
                }
            },
            "contactGroups": {},
            "otherContacts": {},
            "directoryPeople": {}
        }
        
        # Test that validation fails due to invalid resource name format
        with self.assertRaises(Exception):
            GooglePeopleDB(**invalid_data)

    def test_defaultdb_file_not_found_handling(self):
        """Test DefaultDB loading handles file not found gracefully."""
        # Test load_state with non-existent file
        with self.assertRaises(FileNotFoundError):
            load_state('/nonexistent/file.json')

    def test_defaultdb_json_decode_error_handling(self):
        """Test DefaultDB loading handles JSON decode errors."""
        # Create a temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_file.write('{ invalid json content }')
            temp_filepath = temp_file.name
        
        try:
            # Test load_state with invalid JSON
            with self.assertRaises(json.JSONDecodeError):
                load_state(temp_filepath)
        finally:
            # Clean up
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_defaultdb_data_consistency_after_operations(self):
        """Test that DefaultDB data remains consistent after various operations."""
        # Get original data
        original_people_count = len(DB.get("people", {}))
        original_groups_count = len(DB.get("contactGroups", {}))
        
        # Perform some operations
        DB.set("test_key", "test_value")
        
        # Verify DefaultDB data is still intact
        self.assertEqual(len(DB.get("people", {})), original_people_count)
        self.assertEqual(len(DB.get("contactGroups", {})), original_groups_count)
        
        # Verify Pydantic validation still works
        db_model = get_database()
        self.assertIsInstance(db_model, GooglePeopleDB)

    def test_defaultdb_pydantic_model_operations(self):
        """Test operations on the Pydantic model created from DefaultDB."""
        db_model = get_database()
        
        # Test accessing people data
        people = db_model.people
        self.assertIsInstance(people, dict)
        
        # Test accessing contact groups
        contact_groups = db_model.contact_groups
        self.assertIsInstance(contact_groups, dict)
        
        # Test accessing other contacts
        other_contacts = db_model.other_contacts
        self.assertIsInstance(other_contacts, dict)
        
        # Test accessing directory people
        directory_people = db_model.directory_people
        self.assertIsInstance(directory_people, dict)

    def test_defaultdb_save_state_preserves_structure(self):
        """Test that save_state preserves the DefaultDB structure."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Save current state
            save_state(temp_filepath)
            
            # Load and verify structure
            with open(temp_filepath, 'r') as f:
                saved_data = json.load(f)
            
            # Verify all expected keys are present
            expected_keys = ["people", "contactGroups", "otherContacts", "directoryPeople"]
            for key in expected_keys:
                self.assertIn(key, saved_data, f"Saved data should contain '{key}' key")
                self.assertIsInstance(saved_data[key], dict)
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_defaultdb_load_state_validation(self):
        """Test that load_state validates DefaultDB data against schema."""
        # Create valid test data
        valid_data = {
            "people": {
                "people/test123": {
                    "resourceName": "people/test123",
                    "etag": "test-etag",
                    "names": [{"givenName": "Test", "familyName": "User"}],
                    "phoneNumbers": [{"value": "+1234567890", "type": "mobile"}],
                    "emailAddresses": [{"value": "test@example.com", "type": "work"}]
                }
            },
            "contactGroups": {},
            "otherContacts": {},
            "directoryPeople": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Save valid data
            with open(temp_filepath, 'w') as f:
                json.dump(valid_data, f)
            
            # Clear DB and load
            DB.clear()
            load_state(temp_filepath)
            
            # Verify data was loaded and validates
            db_model = get_database()
            self.assertIsInstance(db_model, GooglePeopleDB)
            self.assertEqual(len(db_model.people), 1)
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    # def test_defaultdb_load_state_invalid_schema(self):
    #     """Test that load_state fails with invalid schema data."""
    #     # Create invalid data with invalid resource name format
    #     invalid_data = {
    #         "people": {
    #             "invalid_person": {
    #                 "resourceName": "invalid_format",  # Should start with "people/"
    #                 "etag": "test-etag",
    #                 "names": [],
    #                 "emailAddresses": [],
    #                 "phoneNumbers": []
    #             }
    #         },
    #         "contactGroups": {},
    #         "otherContacts": {},
    #         "directoryPeople": {}
    #     }
        
    #     with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
    #         temp_filepath = temp_file.name
        
    #     try:
    #         # Save invalid data
    #         with open(temp_filepath, 'w') as f:
    #             json.dump(invalid_data, f)
            
    #         # Test that load_state fails
    #         with self.assertRaises(Exception):
    #             load_state(temp_filepath)
            
    #     finally:
    #         if os.path.exists(temp_filepath):
    #             os.unlink(temp_filepath)

    def test_defaultdb_initial_loading_with_validation(self):
        """Test that DefaultDB initial loading works with Pydantic validation."""
        # This test verifies that the DefaultDB loads correctly on startup
        # and that the data can be validated against the Pydantic schema
        
        # Verify DB has data
        self.assertGreater(len(DB._data), 0)
        
        # Verify we can get a validated model
        db_model = get_database()
        self.assertIsInstance(db_model, GooglePeopleDB)
        
        # Verify the model has the expected structure
        self.assertIsInstance(db_model.people, dict)
        self.assertIsInstance(db_model.contact_groups, dict)
        self.assertIsInstance(db_model.other_contacts, dict)
        self.assertIsInstance(db_model.directory_people, dict)

    def test_defaultdb_comprehensive_roundtrip(self):
        """Test comprehensive DefaultDB save and load round-trip."""
        # Get original state
        original_db_model = get_database()
        original_people_count = len(original_db_model.people)
        original_groups_count = len(original_db_model.contact_groups)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Save current state
            save_state(temp_filepath)
            
            # Clear DB completely
            DB.clear()
            self.assertEqual(len(DB._data), 0)
            
            # Load from file
            load_state(temp_filepath)
            
            # Verify data was restored
            restored_db_model = get_database()
            self.assertIsInstance(restored_db_model, GooglePeopleDB)
            self.assertEqual(len(restored_db_model.people), original_people_count)
            self.assertEqual(len(restored_db_model.contact_groups), original_groups_count)
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)


if __name__ == "__main__":
    unittest.main()
