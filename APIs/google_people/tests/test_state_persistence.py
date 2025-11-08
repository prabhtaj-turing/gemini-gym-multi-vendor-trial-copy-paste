"""
Test cases for State (Load/Save) functionality in Google People API.

This module tests the database persistence functionality including:
1. Saving database state to files
2. Loading database state from files
3. State consistency and integrity
4. Error handling for invalid files and paths
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, mock_open

from common_utils.base_case import BaseTestCaseWithErrorHandler
from .common import reset_db
from ..SimulationEngine.db import DB, save_state, load_state, DEFAULT_DB_PATH


class TestStatePersistence(BaseTestCaseWithErrorHandler):
    """Test class for state persistence functionality."""

    def setUp(self):
        """Set up test database with sample data."""
        reset_db()
        
        # Create test data
        self.test_data = {
            "people": {
                "people/test123": {
                    "resourceName": "people/test123",
                    "etag": "etag_test123",
                    "names": [{"displayName": "Test User", "givenName": "Test", "familyName": "User"}],
                    "emailAddresses": [{"value": "test@example.com", "type": "work"}],
                    "created": "2023-01-15T10:30:00Z",
                    "updated": "2024-01-15T14:20:00Z"
                }
            },
            "contactGroups": {
                "contactGroups/testgroup": {
                    "resourceName": "contactGroups/testgroup",
                    "etag": "etag_testgroup",
                    "name": "Test Group",
                    "groupType": "USER_CONTACT_GROUP",
                    "memberResourceNames": ["people/test123"],
                    "memberCount": 1,
                    "created": "2023-01-15T10:30:00Z",
                    "updated": "2024-01-15T14:20:00Z"
                }
            },
            "otherContacts": {},
            "directoryPeople": {}
        }

    def tearDown(self):
        """Clean up after each test."""
        reset_db()

    def test_save_state_success(self):
        """Test successful saving of database state."""
        # Set up test data in DB
        for key, value in self.test_data.items():
            DB.set(key, value)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Save state
            save_state(temp_filepath)
            
            # Verify file was created
            self.assertTrue(os.path.exists(temp_filepath))
            
            # Verify file content
            with open(temp_filepath, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data["people"], self.test_data["people"])
            self.assertEqual(saved_data["contactGroups"], self.test_data["contactGroups"])
            
        finally:
            # Clean up
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_save_state_creates_directory(self):
        """Test that save_state works with nested directory paths when directories exist."""
        # Create temporary directory path
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_dir = os.path.join(temp_dir, "nested", "directory")
            temp_filepath = os.path.join(nested_dir, "test_state.json")
            
            # Create the nested directory structure first
            os.makedirs(nested_dir, exist_ok=True)
            
            # Set up test data
            DB.set("people", self.test_data["people"])
            
            # Save state to nested directory
            save_state(temp_filepath)
            
            # Verify file was created
            self.assertTrue(os.path.exists(temp_filepath))
            
            # Verify content
            with open(temp_filepath, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data["people"], self.test_data["people"])

    def test_save_state_empty_database(self):
        """Test saving state when database is empty."""
        # Clear database
        DB.clear()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Save empty state
            save_state(temp_filepath)
            
            # Verify file content
            with open(temp_filepath, 'r') as f:
                saved_data = json.load(f)
            
            self.assertEqual(saved_data, {})
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_save_state_file_permission_error(self):
        """Test save_state handling of file permission errors."""
        # Try to save to a read-only directory (this will vary by OS)
        if os.name == 'posix':  # Unix-like systems
            read_only_path = "/root/readonly_file.json"
        else:  # Windows
            read_only_path = "C:\\Windows\\System32\\readonly_file.json"
        
        # Set up test data
        DB.set("people", self.test_data["people"])
        
        # Should raise PermissionError or similar
        with self.assertRaises((PermissionError, OSError)):
            save_state(read_only_path)

    def test_load_state_success(self):
        """Test successful loading of database state."""
        # Create temporary file with test data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(self.test_data, temp_file)
            temp_filepath = temp_file.name
        
        try:
            # Clear current database
            DB.clear()
            
            # Load state
            load_state(temp_filepath)
            
            # Verify data was loaded correctly
            self.assertEqual(DB.get("people"), self.test_data["people"])
            self.assertEqual(DB.get("contactGroups"), self.test_data["contactGroups"])
            self.assertEqual(DB.get("otherContacts"), self.test_data["otherContacts"])
            self.assertEqual(DB.get("directoryPeople"), self.test_data["directoryPeople"])
            
        finally:
            # Clean up
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_load_state_file_not_found(self):
        """Test load_state handling of non-existent files."""
        non_existent_path = "/path/that/does/not/exist/file.json"
        
        with self.assertRaises(FileNotFoundError):
            load_state(non_existent_path)

    def test_load_state_invalid_json(self):
        """Test load_state handling of invalid JSON files."""
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_file.write("{ invalid json content")
            temp_filepath = temp_file.name
        
        try:
            with self.assertRaises(json.JSONDecodeError):
                load_state(temp_filepath)
                
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_load_state_empty_file(self):
        """Test load_state handling of empty files."""
        # Create empty temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            with self.assertRaises(json.JSONDecodeError):
                load_state(temp_filepath)
                
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_load_state_clears_existing_data(self):
        """Test that load_state clears existing database data."""
        # Set up initial data
        initial_data = {"people": {"people/initial": {"name": "Initial User"}}}
        for key, value in initial_data.items():
            DB.set(key, value)
        
        # Verify initial data exists
        self.assertEqual(DB.get("people"), initial_data["people"])
        
        # Create file with different data
        new_data = {"people": {"people/new": {"name": "New User"}}}
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(new_data, temp_file)
            temp_filepath = temp_file.name
        
        try:
            # Load new state
            load_state(temp_filepath)
            
            # Verify old data was cleared and new data loaded
            self.assertEqual(DB.get("people"), new_data["people"])
            self.assertNotEqual(DB.get("people"), initial_data["people"])
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_save_load_state_roundtrip(self):
        """Test complete save and load roundtrip."""
        # Set up complex test data
        complex_data = {
            "people": {
                "people/user1": {
                    "resourceName": "people/user1",
                    "names": [{"displayName": "User One"}],
                    "emailAddresses": [{"value": "user1@example.com"}]
                },
                "people/user2": {
                    "resourceName": "people/user2",
                    "names": [{"displayName": "User Two"}],
                    "phoneNumbers": [{"value": "+1-555-123-4567"}]
                }
            },
            "contactGroups": {
                "contactGroups/group1": {
                    "resourceName": "contactGroups/group1",
                    "name": "Group One",
                    "memberResourceNames": ["people/user1", "people/user2"]
                }
            },
            "otherContacts": {
                "otherContacts/other1": {
                    "resourceName": "otherContacts/other1",
                    "names": [{"displayName": "Other Contact"}]
                }
            },
            "directoryPeople": {}
        }
        
        # Set up data in DB
        for key, value in complex_data.items():
            DB.set(key, value)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Save state
            save_state(temp_filepath)
            
            # Clear database
            DB.clear()
            self.assertEqual(DB.get("people", {}), {})
            
            # Load state
            load_state(temp_filepath)
            
            # Verify all data was restored correctly
            self.assertEqual(DB.get("people"), complex_data["people"])
            self.assertEqual(DB.get("contactGroups"), complex_data["contactGroups"])
            self.assertEqual(DB.get("otherContacts"), complex_data["otherContacts"])
            self.assertEqual(DB.get("directoryPeople"), complex_data["directoryPeople"])
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_state_persistence_with_unicode(self):
        """Test state persistence with Unicode characters."""
        unicode_data = {
            "people": {
                "people/unicode": {
                    "resourceName": "people/unicode",
                    "names": [{"displayName": "José María García-Rodríguez"}],
                    "emailAddresses": [{"value": "josé@exâmplë.com"}],
                    "notes": "Special characters: ñáéíóú ÇüöäÖÄß 中文 العربية 🎉🌟"
                }
            }
        }
        
        # Set up Unicode data
        DB.set("people", unicode_data["people"])
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Save and load Unicode data
            save_state(temp_filepath)
            DB.clear()
            load_state(temp_filepath)
            
            # Verify Unicode data was preserved
            loaded_data = DB.get("people")
            self.assertEqual(loaded_data, unicode_data["people"])
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_state_persistence_preserves_data_types(self):
        """Test that state persistence preserves different data types."""
        typed_data = {
            "testData": {
                "string_field": "test string",
                "int_field": 42,
                "float_field": 3.14159,
                "bool_true": True,
                "bool_false": False,
                "null_field": None,
                "list_field": [1, "two", 3.0, True, None],
                "dict_field": {"nested": {"deep": "value"}},
                "empty_list": [],
                "empty_dict": {}
            }
        }
        
        # Set up typed data
        for key, value in typed_data.items():
            DB.set(key, value)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filepath = temp_file.name
        
        try:
            # Save and load
            save_state(temp_filepath)
            DB.clear()
            load_state(temp_filepath)
            
            # Verify data types were preserved
            loaded_data = DB.get("testData")
            self.assertEqual(loaded_data, typed_data["testData"])
            self.assertIsInstance(loaded_data["string_field"], str)
            self.assertIsInstance(loaded_data["int_field"], int)
            self.assertIsInstance(loaded_data["float_field"], float)
            self.assertIsInstance(loaded_data["bool_true"], bool)
            self.assertIsInstance(loaded_data["bool_false"], bool)
            self.assertIsNone(loaded_data["null_field"])
            self.assertIsInstance(loaded_data["list_field"], list)
            self.assertIsInstance(loaded_data["dict_field"], dict)
            
        finally:
            if os.path.exists(temp_filepath):
                os.unlink(temp_filepath)

    def test_default_db_path_exists(self):
        """Test that the default database path is correctly defined."""
        # Check that DEFAULT_DB_PATH points to the expected location
        expected_components = ["DBs", "GooglePeopleDefaultDB.json"]
        
        # Verify path components
        for component in expected_components:
            self.assertIn(component, DEFAULT_DB_PATH)
        
        # Verify it's an absolute path
        self.assertTrue(os.path.isabs(DEFAULT_DB_PATH))

    def test_db_singleton_pattern(self):
        """Test that DB follows singleton pattern."""
        from ..SimulationEngine.db import DB as DB1
        from ..SimulationEngine.db import DB as DB2
        
        # Both imports should reference the same instance
        self.assertIs(DB1, DB2)
        
        # Changes to one should affect the other
        DB1.set("test_key", "test_value")
        self.assertEqual(DB2.get("test_key"), "test_value")

    def test_get_database_returns_validated_model(self):
        """Test that get_database returns a validated GooglePeopleDB model."""
        from ..SimulationEngine.db import get_database
        from ..SimulationEngine.db_models import GooglePeopleDB
        
        # Clear database and set up test data
        DB.clear()
        test_data = {
            "people": {
                "people/test123": {
                    "resourceName": "people/test123",
                    "etag": "etag_test123",
                    "names": [{"displayName": "Test User"}],
                    "emailAddresses": [{"value": "test@example.com"}],
                    "phoneNumbers": [],
                    "organizations": [],
                    "addresses": [],
                    "birthdays": [],
                    "photos": [],
                    "urls": [],
                    "userDefined": [],
                    "created": "2023-01-01T00:00:00Z",
                    "updated": "2023-01-01T00:00:00Z"
                }
            },
            "contactGroups": {},
            "otherContacts": {},
            "directoryPeople": {}
        }
        
        # Set up data
        for key, value in test_data.items():
            DB.set(key, value)
        
        # Get database as Pydantic model
        db_model = get_database()
        
        # Verify it's a GooglePeopleDB instance
        self.assertIsInstance(db_model, GooglePeopleDB)
        
        # Verify data is accessible through the model
        self.assertIn("people/test123", db_model.people)
        person = db_model.people["people/test123"]
        self.assertEqual(person.resource_name, "people/test123")
        self.assertEqual(person.etag, "etag_test123")
        self.assertEqual(len(person.names), 1)
        self.assertEqual(person.names[0].display_name, "Test User")

    def test_get_database_validates_data(self):
        """Test that get_database validates data and raises errors for invalid data."""
        from ..SimulationEngine.db import get_database
        from pydantic import ValidationError
        
        # Clear database and set up invalid data
        DB.clear()
        invalid_data = {
            "people": {
                "people/invalid": {
                    "resourceName": "invalid_resource",  # Should start with "people/"
                    "etag": "invalid_etag",  # Should start with "etag_"
                    "names": "not_a_list",  # Should be a list
                    "emailAddresses": [{"value": "invalid-email"}],  # Invalid email format
                    "created": "invalid_timestamp",  # Invalid timestamp format
                    "updated": "invalid_timestamp"
                }
            },
            "contactGroups": {},
            "otherContacts": {},
            "directoryPeople": {}
        }
        
        # Set up invalid data
        for key, value in invalid_data.items():
            DB.set(key, value)
        
        # get_database should raise ValidationError
        with self.assertRaises(ValidationError):
            get_database()

    def test_get_database_with_empty_database(self):
        """Test that get_database works with empty database."""
        from ..SimulationEngine.db import get_database
        from ..SimulationEngine.db_models import GooglePeopleDB
        
        # Clear database
        DB.clear()
        
        # Get database as Pydantic model
        db_model = get_database()
        
        # Verify it's a GooglePeopleDB instance
        self.assertIsInstance(db_model, GooglePeopleDB)
        
        # Verify all collections are empty
        self.assertEqual(len(db_model.people), 0)
        self.assertEqual(len(db_model.contact_groups), 0)
        self.assertEqual(len(db_model.other_contacts), 0)
        self.assertEqual(len(db_model.directory_people), 0)

    def test_get_database_contact_groups_only(self):
        """Test that get_database works with contact groups only."""
        from ..SimulationEngine.db import get_database
        
        # Clear database and set up minimal test data
        DB.clear()
        test_data = {
            "people": {},
            "contactGroups": {
                "contactGroups/group1": {
                    "resourceName": "contactGroups/group1",
                    "etag": "etag_group1",
                    "name": "Test Group",
                    "groupType": "USER_CONTACT_GROUP",
                    "memberCount": 1,
                    "memberResourceNames": ["people/user1"],
                    "created": "2023-01-01T00:00:00Z",
                    "updated": "2023-01-01T00:00:00Z"
                }
            },
            "otherContacts": {},
            "directoryPeople": {}
        }
        
        # Set up data
        for key, value in test_data.items():
            DB.set(key, value)
        
        # Get database as Pydantic model
        db_model = get_database()
        
        # Verify contact groups
        self.assertIn("contactGroups/group1", db_model.contact_groups)
        group = db_model.contact_groups["contactGroups/group1"]
        self.assertEqual(group.resource_name, "contactGroups/group1")
        self.assertEqual(group.name, "Test Group")
        self.assertEqual(group.group_type, "USER_CONTACT_GROUP")
        self.assertEqual(group.member_count, 1)
        self.assertEqual(len(group.member_resource_names), 1)
        self.assertEqual(group.member_resource_names[0], "people/user1")


if __name__ == '__main__':
    unittest.main()
