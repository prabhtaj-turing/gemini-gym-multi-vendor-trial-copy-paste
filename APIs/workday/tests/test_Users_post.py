"""
Test module for Users.post() function.

This module contains comprehensive tests for the Users.post() function which creates
a new SCIM user in the Workday Strategic Sourcing system with validation and
business rule enforcement.
"""

import unittest
import uuid
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any

# Import the function under test
from ..Users import post
from ..SimulationEngine.custom_errors import (
    ResourceConflictError, UserValidationError, UserCreationError
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestUsersPost(BaseTestCaseWithErrorHandler):
    """Test class for Users.post() function."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Valid user data for testing
        self.valid_user_data = {
            "userName": "newuser@example.com",
            "name": {
                "givenName": "John",
                "familyName": "Smith"
            },
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "externalId": "EXT123",
            "active": True,
            "roles": [
                {
                    "value": "user",
                    "display": "User",
                    "primary": True,
                    "type": "primary"
                }
            ]
        }

        # Existing users in database
        self.existing_users = [
            {
                "id": "1",
                "userName": "existing@example.com",
                "name": {"givenName": "Jane", "familyName": "Doe"},
                "active": True
            }
        ]

    def test_invalid_body_type(self):
        """Test error when body is not a dictionary."""
        # Act & Assert
        with self.assertRaises(TypeError) as context:
            post("not a dict")
        
        self.assertIn("body must be a dictionary", str(context.exception))

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing."""
        # Arrange
        invalid_data = {"userName": "test@example.com"}  # Missing name
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_email_format(self):
        """Test validation error for invalid email format."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["userName"] = ""  # Empty email should be invalid
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_name_structure(self):
        """Test validation error for invalid name structure."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["name"] = {"givenName": "John"}  # Missing familyName
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    @patch('workday.Users.db')
    def test_duplicate_username(self, mock_db):
        """Test conflict error when username already exists."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.existing_users.copy()}}
        duplicate_data = self.valid_user_data.copy()
        duplicate_data["userName"] = "existing@example.com"
        
        # Act & Assert
        with self.assertRaises(ResourceConflictError) as context:
            post(duplicate_data)
        
        self.assertIn("already exists", str(context.exception))

    @patch('workday.Users.db')
    def test_case_insensitive_username_check(self, mock_db):
        """Test that username conflict check is case-insensitive."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.existing_users.copy()}}
        duplicate_data = self.valid_user_data.copy()
        duplicate_data["userName"] = "EXISTING@EXAMPLE.COM"  # Different case
        
        # Act & Assert
        with self.assertRaises(ResourceConflictError):
            post(duplicate_data)

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_successful_user_creation(self, mock_db, mock_datetime, mock_uuid):
        """Test successful user creation with all fields."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = post(self.valid_user_data)
        
        # Assert
        self.assertIsInstance(result, dict)
        self.assertEqual(result["userName"], "newuser@example.com")
        self.assertEqual(result["name"]["givenName"], "John")
        self.assertEqual(result["name"]["familyName"], "Smith")
        self.assertEqual(result["externalId"], "EXT123")
        self.assertTrue(result["active"])
        self.assertIn("id", result)
        self.assertIn("meta", result)
        self.assertEqual(result["meta"]["resourceType"], "User")
        self.assertIn("created", result["meta"])
        self.assertIn("lastModified", result["meta"])
        self.assertIn("location", result["meta"])
        self.assertTrue(result["meta"]["location"].endswith(result["id"]))

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_user_creation_with_minimal_data(self, mock_db, mock_datetime, mock_uuid):
        """Test user creation with only required fields."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        minimal_data = {
            "userName": "minimal@example.com",
            "name": {
                "givenName": "Min",
                "familyName": "User"
            }
        }
        
        # Act
        result = post(minimal_data)
        
        # Assert
        self.assertEqual(result["userName"], "minimal@example.com")
        self.assertTrue(result["active"])  # Should default to True
        self.assertEqual(result["schemas"], ["urn:ietf:params:scim:schemas:core:2.0:User"])
        self.assertEqual(result["roles"], [])  # Should default to empty list
        self.assertIsNone(result["externalId"])

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_user_creation_with_custom_schemas(self, mock_db, mock_datetime, mock_uuid):
        """Test user creation with custom schemas."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        custom_data = self.valid_user_data.copy()
        custom_data["schemas"] = ["urn:ietf:params:scim:schemas:core:2.0:User", "custom:schema:user"]  # Must include core schema
        
        # Act
        result = post(custom_data)
        
        # Assert
        self.assertEqual(result["schemas"], ["urn:ietf:params:scim:schemas:core:2.0:User", "custom:schema:user"])

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_user_creation_with_roles(self, mock_db, mock_datetime, mock_uuid):
        """Test user creation with multiple roles."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        data_with_roles = self.valid_user_data.copy()
        data_with_roles["roles"] = [
            {
                "value": "admin",
                "display": "Administrator",
                "primary": True,
                "type": "primary"
            },
            {
                "value": "user",
                "display": "User",
                "primary": False,
                "type": "secondary"
            }
        ]
        
        # Act
        result = post(data_with_roles)
        
        # Assert
        self.assertEqual(len(result["roles"]), 2)
        self.assertEqual(result["roles"][0]["value"], "admin")
        self.assertEqual(result["roles"][1]["value"], "user")

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_user_creation_inactive_user(self, mock_db, mock_datetime, mock_uuid):
        """Test user creation with active=False."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        inactive_data = self.valid_user_data.copy()
        inactive_data["active"] = False
        
        # Act
        result = post(inactive_data)
        
        # Assert
        self.assertFalse(result["active"])

    @patch('workday.Users.db')
    def test_database_save_failure(self, mock_db):
        """Test error handling when database save fails."""
        # Arrange
        mock_users_list = MagicMock()
        mock_users_list.append.side_effect = Exception("Database error")
        mock_db.DB = {"scim": {"users": mock_users_list}}
        
        # Act & Assert
        with self.assertRaises(UserCreationError) as context:
            post(self.valid_user_data)
        
        self.assertIn("Failed to create user in database", str(context.exception))

    def test_invalid_role_structure(self):
        """Test validation error for invalid role structure."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["roles"] = [{"invalid": "role"}]  # Missing required fields
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_generated_id_is_uuid_string(self, mock_db, mock_datetime, mock_uuid):
        """Test that generated ID is a string representation of UUID."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        test_uuid = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        mock_uuid.return_value = test_uuid
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = post(self.valid_user_data)
        
        # Assert
        self.assertEqual(result["id"], str(test_uuid))
        self.assertIsInstance(result["id"], str)

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_location_url_format(self, mock_db, mock_datetime, mock_uuid):
        """Test that location URL follows correct format."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        test_uuid = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        mock_uuid.return_value = test_uuid
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = post(self.valid_user_data)
        
        # Assert
        expected_location = f"https://api.us.workdayspend.com/scim/v2/Users/{str(test_uuid)}"
        self.assertEqual(result["meta"]["location"], expected_location)

    def test_invalid_username_empty_string(self):
        """Test validation error for empty username."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["userName"] = ""
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_username_none(self):
        """Test validation error for None username."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["userName"] = None
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_username_non_string(self):
        """Test validation error for non-string username."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["userName"] = 123
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_missing_name_object(self):
        """Test validation error when name object is missing."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        del invalid_data["name"]
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_name_type(self):
        """Test validation error for invalid name type."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["name"] = "not a dict"
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_missing_given_name(self):
        """Test validation error when givenName is missing from name."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["name"] = {"familyName": "Smith"}
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_missing_family_name(self):
        """Test validation error when familyName is missing from name."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["name"] = {"givenName": "John"}
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_empty_given_name(self):
        """Test validation error for empty givenName."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["name"]["givenName"] = ""
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_empty_family_name(self):
        """Test validation error for empty familyName."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["name"]["familyName"] = ""
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_given_name_type(self):
        """Test validation error for non-string givenName."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["name"]["givenName"] = 123
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_family_name_type(self):
        """Test validation error for non-string familyName."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["name"]["familyName"] = 123
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_active_type(self):
        """Test validation error for non-boolean active field."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["userName"] = "unique_invalid_active@example.com"  # Unique username
        invalid_data["active"] = "true"  # String instead of boolean
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_external_id_type(self):
        """Test validation error for non-string externalId."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["externalId"] = 123
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_schemas_type(self):
        """Test validation error for non-list schemas."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["schemas"] = "not a list"
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_schemas_item_type(self):
        """Test validation error for non-string items in schemas list."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["schemas"] = [123, "valid_schema"]
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_roles_type(self):
        """Test validation error for non-list roles."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["roles"] = "not a list"
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_role_structure_missing_value(self):
        """Test validation error for role missing required value field."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["roles"] = [{"display": "User", "primary": True, "type": "primary"}]
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_role_structure_missing_display(self):
        """Test that role missing display field is allowed (display is optional)."""
        # Arrange
        valid_data = self.valid_user_data.copy()
        valid_data["userName"] = "unique_missing_display@example.com"  # Unique username
        valid_data["roles"] = [{"value": "user", "primary": True, "type": "primary"}]
        
        # Act & Assert - Should NOT raise an error since display is optional
        with patch('workday.Users.db') as mock_db:
            mock_db.DB = {"scim": {"users": []}}
            with patch('workday.Users.uuid.uuid4') as mock_uuid:
                mock_uuid.return_value = "test-uuid"
                with patch('workday.Users.datetime') as mock_datetime:
                    mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
                    result = post(valid_data)
                    self.assertIsNotNone(result)

    def test_invalid_role_structure_missing_primary(self):
        """Test that role missing primary field is allowed (primary is optional)."""
        # Arrange
        valid_data = self.valid_user_data.copy()
        valid_data["userName"] = "unique_missing_primary@example.com"  # Unique username
        valid_data["roles"] = [{"value": "user", "display": "User", "type": "primary"}]
        
        # Act & Assert - Should NOT raise an error since primary is optional
        with patch('workday.Users.db') as mock_db:
            mock_db.DB = {"scim": {"users": []}}
            with patch('workday.Users.uuid.uuid4') as mock_uuid:
                mock_uuid.return_value = "test-uuid"
                with patch('workday.Users.datetime') as mock_datetime:
                    mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
                    result = post(valid_data)
                    self.assertIsNotNone(result)

    def test_invalid_role_structure_missing_type(self):
        """Test that role missing type field is allowed (type is optional)."""
        # Arrange
        valid_data = self.valid_user_data.copy()
        valid_data["userName"] = "unique_missing_type@example.com"  # Unique username
        valid_data["roles"] = [{"value": "user", "display": "User", "primary": True}]
        
        # Act & Assert - Should NOT raise an error since type is optional
        with patch('workday.Users.db') as mock_db:
            mock_db.DB = {"scim": {"users": []}}
            with patch('workday.Users.uuid.uuid4') as mock_uuid:
                mock_uuid.return_value = "test-uuid"
                with patch('workday.Users.datetime') as mock_datetime:
                    mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
                    result = post(valid_data)
                    self.assertIsNotNone(result)

    def test_invalid_role_value_type(self):
        """Test validation error for non-string role value."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["roles"] = [{"value": 123, "display": "User", "primary": True, "type": "primary"}]
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_role_display_type(self):
        """Test validation error for non-string role display."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["roles"] = [{"value": "user", "display": 123, "primary": True, "type": "primary"}]
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_role_primary_type(self):
        """Test validation error for non-boolean role primary."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["userName"] = "unique_invalid_role_primary@example.com"  # Unique username
        invalid_data["roles"] = [{"value": "user", "display": "User", "primary": "true", "type": "primary"}]
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_invalid_role_type_value(self):
        """Test validation error for non-string role type."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["roles"] = [{"value": "user", "display": "User", "primary": True, "type": 123}]
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    @patch('workday.Users.db')
    def test_duplicate_username_mixed_case(self, mock_db):
        """Test conflict error with mixed case username."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.existing_users.copy()}}
        duplicate_data = self.valid_user_data.copy()
        duplicate_data["userName"] = "Existing@Example.Com"  # Mixed case
        
        # Act & Assert
        with self.assertRaises(ResourceConflictError):
            post(duplicate_data)

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_user_creation_without_external_id(self, mock_db, mock_datetime, mock_uuid):
        """Test user creation without externalId field."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        data_without_external_id = {
            "userName": "noexternal@example.com",
            "name": {
                "givenName": "No",
                "familyName": "External"
            }
        }
        
        # Act
        result = post(data_without_external_id)
        
        # Assert
        self.assertIsNone(result["externalId"])
        self.assertEqual(result["userName"], "noexternal@example.com")

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_user_creation_without_schemas(self, mock_db, mock_datetime, mock_uuid):
        """Test user creation without schemas field uses default."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        data_without_schemas = {
            "userName": "noschemas@example.com",
            "name": {
                "givenName": "No",
                "familyName": "Schemas"
            }
        }
        
        # Act
        result = post(data_without_schemas)
        
        # Assert
        self.assertEqual(result["schemas"], ["urn:ietf:params:scim:schemas:core:2.0:User"])

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_user_creation_without_active_defaults_true(self, mock_db, mock_datetime, mock_uuid):
        """Test user creation without active field defaults to True."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        data_without_active = {
            "userName": "noactive@example.com",
            "name": {
                "givenName": "No",
                "familyName": "Active"
            }
        }
        
        # Act
        result = post(data_without_active)
        
        # Assert
        self.assertTrue(result["active"])

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_user_creation_without_roles_defaults_empty(self, mock_db, mock_datetime, mock_uuid):
        """Test user creation without roles field defaults to empty list."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        data_without_roles = {
            "userName": "noroles@example.com",
            "name": {
                "givenName": "No",
                "familyName": "Roles"
            }
        }
        
        # Act
        result = post(data_without_roles)
        
        # Assert
        self.assertEqual(result["roles"], [])

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_user_creation_with_empty_roles_list(self, mock_db, mock_datetime, mock_uuid):
        """Test user creation with explicitly empty roles list."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        data_with_empty_roles = self.valid_user_data.copy()
        data_with_empty_roles["roles"] = []
        
        # Act
        result = post(data_with_empty_roles)
        
        # Assert
        self.assertEqual(result["roles"], [])

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_user_creation_with_null_external_id(self, mock_db, mock_datetime, mock_uuid):
        """Test user creation with null externalId."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        data_with_null_external_id = self.valid_user_data.copy()
        data_with_null_external_id["externalId"] = None
        
        # Act
        result = post(data_with_null_external_id)
        
        # Assert
        self.assertIsNone(result["externalId"])

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_user_creation_timestamps_match(self, mock_db, mock_datetime, mock_uuid):
        """Test that created and lastModified timestamps are identical for new users."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        timestamp = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value.isoformat.return_value = timestamp
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = post(self.valid_user_data)
        
        # Assert
        self.assertEqual(result["meta"]["created"], timestamp)
        self.assertEqual(result["meta"]["lastModified"], timestamp)

    @patch('workday.Users.uuid.uuid4')
    @patch('workday.Users.datetime')
    @patch('workday.Users.db')
    def test_user_creation_meta_resource_type(self, mock_db, mock_datetime, mock_uuid):
        """Test that meta resourceType is always set to 'User'."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-9abc-123456789012')
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = post(self.valid_user_data)
        
        # Assert
        self.assertEqual(result["meta"]["resourceType"], "User")

    def test_extra_field_in_user_data(self):
        """Test validation error for extra fields in user data."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["extraField"] = "should not be allowed"
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_extra_field_in_name_object(self):
        """Test validation error for extra fields in name object."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["name"]["extraField"] = "should not be allowed"
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    def test_extra_field_in_role_object(self):
        """Test validation error for extra fields in role object."""
        # Arrange
        invalid_data = self.valid_user_data.copy()
        invalid_data["roles"][0]["extraField"] = "should not be allowed"
        
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post(invalid_data)

    @patch('workday.Users.db')
    def test_database_append_called(self, mock_db):
        """Test that database append is called during user creation."""
        # Arrange
        mock_users_list = MagicMock()
        mock_db.DB = {"scim": {"users": mock_users_list}}
        
        # Act
        post(self.valid_user_data)
        
        # Assert
        mock_users_list.append.assert_called_once()

    def test_empty_body_dict(self):
        """Test validation error for empty body dictionary."""
        # Act & Assert
        with self.assertRaises(UserValidationError):
            post({})

    def test_none_body(self):
        """Test type error for None body."""
        # Act & Assert
        with self.assertRaises(TypeError):
            post(None)

    def test_list_body(self):
        """Test type error for list body."""
        # Act & Assert
        with self.assertRaises(TypeError):
            post([])

    def test_string_body(self):
        """Test type error for string body."""
        # Act & Assert
        with self.assertRaises(TypeError):
            post("invalid")


if __name__ == '__main__':
    unittest.main()
