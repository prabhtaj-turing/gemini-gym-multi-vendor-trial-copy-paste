"""
Test module for UserById.put() function.

This module contains comprehensive tests for the UserById.put() function which replaces
all updatable attributes of a User resource with validation and business rule enforcement.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any

# Import the function under test
from ..UserById import put
from ..SimulationEngine.custom_errors import (
    InvalidAttributeError, UserUpdateValidationError, UserUpdateForbiddenError,
    UserUpdateConflictError, UserUpdateOperationError
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestUserByIdPut(BaseTestCaseWithErrorHandler):
    """Test class for UserById.put() function."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Sample users for testing
        self.sample_users = [
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "id": "1",
                "externalId": "1",
                "userName": "jdoe@gmail.com",
                "name": {
                    "givenName": "Jane",
                    "familyName": "Doe"
                },
                "active": True,
                "roles": [
                    {
                        "value": "admin",
                        "display": "Admin",
                        "primary": True,
                        "type": "primary"
                    }
                ],
                "meta": {
                    "resourceType": "User",
                    "created": "2024-01-01T00:00:00Z",
                    "lastModified": "2024-06-01T00:00:00Z",
                    "location": "https://api.us.workdayspend.com/scim/v2/Users/1"
                }
            },
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "id": "2",
                "externalId": "2",
                "userName": "existing@gmail.com",
                "name": {
                    "givenName": "Existing",
                    "familyName": "User"
                },
                "active": True,
                "roles": [],
                "meta": {
                    "resourceType": "User",
                    "created": "2024-01-02T00:00:00Z",
                    "lastModified": "2024-06-02T00:00:00Z",
                    "location": "https://api.us.workdayspend.com/scim/v2/Users/2"
                }
            }
        ]

        # Valid update data
        self.valid_update_data = {
            "userName": "updated@gmail.com",  # Same domain as test user
            "name": {
                "givenName": "Updated",
                "familyName": "User"
            },
            "externalId": "UPD123",
            "active": True
        }

    def test_empty_user_id(self):
        """Test error when user ID is empty."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            put("", {})
        
        self.assertIn("User ID cannot be empty", str(context.exception))

    def test_none_user_id(self):
        """Test error when user ID is None."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            put(None, {})
        
        self.assertIn("User ID cannot be empty", str(context.exception))

    def test_non_string_user_id(self):
        """Test error when user ID is not a string."""
        # Act & Assert
        with self.assertRaises(TypeError) as context:
            put(123, {})
        
        self.assertIn("User ID must be a string", str(context.exception))

    def test_whitespace_only_user_id(self):
        """Test error when user ID is whitespace only."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            put("   ", {})
        
        self.assertIn("User ID cannot be empty or whitespace only", str(context.exception))

    def test_non_dict_body(self):
        """Test error when body is not a dictionary."""
        # Act & Assert
        with self.assertRaises(TypeError) as context:
            put("1", "not a dict")
        
        self.assertIn("body must be a dictionary", str(context.exception))

    def test_invalid_attributes(self):
        """Test error when invalid attributes are specified."""
        # Act & Assert
        with self.assertRaises(InvalidAttributeError):
            put("1", self.valid_update_data, attributes="invalidAttribute")

    def test_missing_required_username(self):
        """Test validation error when required userName is missing."""
        # Arrange
        invalid_data = {
            "name": {
                "givenName": "Test",
                "familyName": "User"
            }
        }
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_missing_required_name(self):
        """Test validation error when required name is missing."""
        # Arrange
        invalid_data = {
            "userName": "test@example.com"
        }
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_invalid_name_structure(self):
        """Test validation error for invalid name structure."""
        # Arrange
        invalid_data = {
            "userName": "test@example.com",
            "name": {
                "givenName": "Test"  # Missing familyName
            }
        }
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_invalid_email_format(self):
        """Test validation error for invalid email format."""
        # Arrange
        invalid_data = {
            "userName": "",  # Empty email should be invalid
            "name": {
                "givenName": "Test",
                "familyName": "User"
            }
        }
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    @patch('workday.UserById.db')
    def test_user_not_found(self, mock_db):
        """Test return None when user ID is not found."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        
        # Act
        result = put("999", self.valid_update_data)
        
        # Assert
        self.assertIsNone(result)

    @patch('workday.UserById.db')
    def test_forbidden_self_deactivation(self, mock_db):
        """Test forbidden operation when trying to deactivate user."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        deactivate_data = self.valid_update_data.copy()
        deactivate_data["active"] = False
        
        # Act & Assert
        with self.assertRaises(UserUpdateForbiddenError) as context:
            put("1", deactivate_data)
        
        self.assertIn("Self-deactivation is forbidden", str(context.exception))

    @patch('workday.UserById.db')
    def test_forbidden_domain_change(self, mock_db):
        """Test forbidden operation when trying to change email domain."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        domain_change_data = self.valid_update_data.copy()
        domain_change_data["userName"] = "jdoe@different-domain.com"
        
        # Act & Assert
        with self.assertRaises(UserUpdateForbiddenError) as context:
            put("1", domain_change_data)
        
        self.assertIn("Email domain change is forbidden", str(context.exception))

    @patch('workday.UserById.db')
    def test_username_conflict(self, mock_db):
        """Test conflict error when username already exists for different user."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        conflict_data = self.valid_update_data.copy()
        conflict_data["userName"] = "existing@gmail.com"  # User 2's username
        
        # Act & Assert
        with self.assertRaises(UserUpdateConflictError) as context:
            put("1", conflict_data)
        
        self.assertIn("already exists", str(context.exception))

    @patch('workday.UserById.db')
    def test_case_insensitive_username_conflict(self, mock_db):
        """Test that username conflict check is case-insensitive."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        conflict_data = self.valid_update_data.copy()
        conflict_data["userName"] = "EXISTING@GMAIL.COM"  # Different case to test case-insensitive conflict detection
        
        # Act & Assert
        with self.assertRaises(UserUpdateConflictError):
            put("1", conflict_data)

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_successful_user_update(self, mock_db, mock_datetime):
        """Test successful user update with all fields."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = put("1", self.valid_update_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["userName"], "updated@gmail.com")
        self.assertEqual(result["name"]["givenName"], "Updated")
        self.assertEqual(result["name"]["familyName"], "User")
        self.assertEqual(result["externalId"], "UPD123")
        self.assertTrue(result["active"])
        self.assertEqual(result["meta"]["lastModified"], "2024-02-01T12:00:00Z")
        self.assertIn("location", result["meta"])

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_partial_update_minimal_fields(self, mock_db, mock_datetime):
        """Test update with only required fields."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        minimal_data = {
            "userName": "minimal@gmail.com",  # Same domain
            "name": {
                "givenName": "Min",
                "familyName": "User"
            }
        }
        
        # Act
        result = put("1", minimal_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["userName"], "minimal@gmail.com")
        self.assertEqual(result["name"]["givenName"], "Min")
        self.assertEqual(result["name"]["familyName"], "User")
        # externalId should remain from original or be None if not provided
        self.assertTrue(result["active"])  # Should remain unchanged if not provided

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_update_with_same_username(self, mock_db, mock_datetime):
        """Test successful update when using the same username (no conflict)."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        same_username_data = {
            "userName": "jdoe@gmail.com",  # Same as current user
            "name": {
                "givenName": "Updated",
                "familyName": "Name"
            }
        }
        
        # Act
        result = put("1", same_username_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["userName"], "jdoe@gmail.com")
        self.assertEqual(result["name"]["givenName"], "Updated")
        self.assertEqual(result["name"]["familyName"], "Name")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_update_with_attributes_filter(self, mock_db, mock_datetime):
        """Test update with attribute filtering in response."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = put("1", self.valid_update_data, attributes="userName,name")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("userName", result)
        self.assertIn("name", result)
        self.assertIn("schemas", result)  # Always included
        self.assertNotIn("roles", result)
        self.assertNotIn("active", result)

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_location_field_preserved(self, mock_db, mock_datetime):
        """Test that location field is preserved/added in meta object."""
        # Arrange
        user_without_location = self.sample_users[0].copy()
        del user_without_location["meta"]["location"]  # Remove location
        mock_db.DB = {"scim": {"users": [user_without_location]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = put("1", self.valid_update_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("location", result["meta"])
        self.assertEqual(result["meta"]["location"], "https://api.us.workdayspend.com/scim/v2/Users/1")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_external_id_none_handling(self, mock_db, mock_datetime):
        """Test handling when externalId is explicitly set to None."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        data_with_none_external_id = self.valid_update_data.copy()
        data_with_none_external_id["externalId"] = None

        # Act
        result = put("1", data_with_none_external_id)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIsNone(result["externalId"])

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_active_none_handling(self, mock_db, mock_datetime):
        """Test handling when active is explicitly set to None."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        data_with_none_active = {
            "userName": "test@gmail.com",  # Same domain
            "name": {
                "givenName": "Test",
                "familyName": "User"
            },
            "active": None
        }
        
        # Act
        result = put("1", data_with_none_active)
        
        # Assert
        self.assertIsNotNone(result)
        # active should remain unchanged from original value when None is provided

    @patch('workday.UserById.UserReplaceInputModel')
    @patch('workday.UserById.db')
    def test_update_operation_failure(self, mock_db, mock_model):
        """Test error handling when update operation fails."""
        # Arrange - Set up a scenario where user exists but update fails
        mock_users_list = MagicMock()
        mock_users_list.__iter__.return_value = iter([self.sample_users[0]])  # User exists
        mock_users_list.__setitem__.side_effect = Exception("Database error")
        mock_db.DB = {"scim": {"users": mock_users_list}}
        
        # Mock the Pydantic model to avoid validation issues
        mock_replace_input = MagicMock()
        mock_replace_input.userName = "updated@gmail.com"
        mock_replace_input.name.givenName = "Updated"
        mock_replace_input.name.familyName = "User"
        mock_replace_input.externalId = "UPD123"
        mock_replace_input.active = True
        mock_model.return_value = mock_replace_input
        
        # Create a deep copy of valid_update_data to avoid reference issues
        import copy
        test_data = copy.deepcopy(self.valid_update_data)
        
        # Mock enumerate to find the user
        with patch('builtins.enumerate') as mock_enumerate:
            mock_enumerate.return_value = [(0, self.sample_users[0])]
            
            # Act & Assert
            with self.assertRaises(UserUpdateOperationError) as context:
                put("1", test_data)
            
            self.assertIn("Failed to update user", str(context.exception))

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_roles_preserved(self, mock_db, mock_datetime):
        """Test that roles are preserved during update (read-only)."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = put("1", self.valid_update_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(len(result["roles"]), 1)  # Should preserve original roles
        self.assertEqual(result["roles"][0]["value"], "admin")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_meta_fields_preserved(self, mock_db, mock_datetime):
        """Test that meta fields are properly handled during update."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = put("1", self.valid_update_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["meta"]["resourceType"], "User")
        self.assertEqual(result["meta"]["created"], "2024-01-01T00:00:00Z")  # Should preserve original
        self.assertEqual(result["meta"]["lastModified"], "2024-02-01T12:00:00Z")  # Should be updated

    def test_invalid_username_empty_string(self):
        """Test validation error for empty username."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["userName"] = ""
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_invalid_username_none(self):
        """Test validation error for None username."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["userName"] = None
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_invalid_username_non_string(self):
        """Test validation error for non-string username."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["userName"] = 123
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_invalid_name_type(self):
        """Test validation error for invalid name type."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["name"] = "not a dict"
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_invalid_name_none(self):
        """Test validation error for None name."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["name"] = None
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_empty_given_name(self):
        """Test validation error for empty givenName."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["name"]["givenName"] = ""
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_empty_family_name(self):
        """Test validation error for empty familyName."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["name"]["familyName"] = ""
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_none_given_name(self):
        """Test validation error for None givenName."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["name"]["givenName"] = None
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_none_family_name(self):
        """Test validation error for None familyName."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["name"]["familyName"] = None
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_invalid_given_name_type(self):
        """Test validation error for non-string givenName."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["name"]["givenName"] = 123
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_invalid_family_name_type(self):
        """Test validation error for non-string familyName."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["name"]["familyName"] = 123
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_invalid_active_type(self):
        """Test validation error for non-boolean active field."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["active"] = "true"  # String instead of boolean
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_invalid_external_id_type(self):
        """Test validation error for non-string externalId."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["externalId"] = 123
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    @patch('workday.UserById.db')
    def test_username_conflict_different_case(self, mock_db):
        """Test conflict error with different case username."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        conflict_data = self.valid_update_data.copy()
        conflict_data["userName"] = "EXISTING@GMAIL.COM"  # Different case
        
        # Act & Assert
        with self.assertRaises(UserUpdateConflictError):
            put("1", conflict_data)

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_update_with_same_username_different_case(self, mock_db, mock_datetime):
        """Test successful update when using same username with different case."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        same_username_data = {
            "userName": "JDOE@GMAIL.COM",  # Same username, different case
            "name": {
                "givenName": "Updated",
                "familyName": "Name"
            }
        }
        
        # Act
        result = put("1", same_username_data)
        
        # Assert
        self.assertIsNotNone(result)
        # EmailStr normalizes domain to lowercase, which is standard email behavior
        self.assertEqual(result["userName"], "JDOE@gmail.com")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_update_with_whitespace_in_names(self, mock_db, mock_datetime):
        """Test update with whitespace in name fields."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        whitespace_data = {
            "userName": "whitespace@gmail.com",
            "name": {
                "givenName": "  John  ",
                "familyName": "  Smith  "
            }
        }
        
        # Act
        result = put("1", whitespace_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["name"]["givenName"], "  John  ")
        self.assertEqual(result["name"]["familyName"], "  Smith  ")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_update_with_unicode_characters(self, mock_db, mock_datetime):
        """Test update with unicode characters in names."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        unicode_data = {
            "userName": "unicode@gmail.com",
            "name": {
                "givenName": "José",
                "familyName": "Müller"
            }
        }
        
        # Act
        result = put("1", unicode_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["name"]["givenName"], "José")
        self.assertEqual(result["name"]["familyName"], "Müller")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_update_with_long_field_values(self, mock_db, mock_datetime):
        """Test update with very long field values."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        long_data = {
            "userName": "verylongusernamethatexceedsnormallimits@gmail.com",
            "name": {
                "givenName": "A" * 100,  # Very long name
                "familyName": "B" * 100
            },
            "externalId": "C" * 200  # Very long external ID
        }
        
        # Act
        result = put("1", long_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(len(result["name"]["givenName"]), 100)
        self.assertEqual(len(result["name"]["familyName"]), 100)
        self.assertEqual(len(result["externalId"]), 200)

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_update_with_special_characters_in_external_id(self, mock_db, mock_datetime):
        """Test update with special characters in externalId."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        special_data = {
            "userName": "special@gmail.com",
            "name": {
                "givenName": "Special",
                "familyName": "User"
            },
            "externalId": "ext-123_456@domain.com#$%"
        }
        
        # Act
        result = put("1", special_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["externalId"], "ext-123_456@domain.com#$%")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_update_preserves_id_field(self, mock_db, mock_datetime):
        """Test that ID field is preserved during update."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = put("1", self.valid_update_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "1")  # Should preserve original ID

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_update_preserves_schemas_field(self, mock_db, mock_datetime):
        """Test that schemas field is preserved during update."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = put("1", self.valid_update_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("schemas", result)
        self.assertEqual(result["schemas"], ["urn:ietf:params:scim:schemas:core:2.0:User"])

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_meta_object_creation_if_missing(self, mock_db, mock_datetime):
        """Test that meta object is created if it doesn't exist."""
        # Arrange
        user_without_meta = self.sample_users[0].copy()
        del user_without_meta["meta"]
        mock_db.DB = {"scim": {"users": [user_without_meta]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = put("1", self.valid_update_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("meta", result)
        self.assertEqual(result["meta"]["lastModified"], "2024-02-01T12:00:00Z")
        self.assertEqual(result["meta"]["resourceType"], "User")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_meta_object_recreation_if_invalid(self, mock_db, mock_datetime):
        """Test that meta object is recreated if it's not a dictionary."""
        # Arrange
        user_with_invalid_meta = self.sample_users[0].copy()
        user_with_invalid_meta["meta"] = "not a dict"
        mock_db.DB = {"scim": {"users": [user_with_invalid_meta]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = put("1", self.valid_update_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIsInstance(result["meta"], dict)
        self.assertEqual(result["meta"]["lastModified"], "2024-02-01T12:00:00Z")

    def test_extra_field_in_update_data(self):
        """Test validation error for extra fields in update data."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["extraField"] = "should not be allowed"
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_extra_field_in_name_object(self):
        """Test validation error for extra fields in name object."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["name"]["extraField"] = "should not be allowed"
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_empty_body_dict(self):
        """Test validation error for empty body dictionary."""
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", {})

    def test_none_body(self):
        """Test type error for None body."""
        # Act & Assert
        with self.assertRaises(TypeError):
            put("1", None)

    def test_list_body(self):
        """Test type error for list body."""
        # Act & Assert
        with self.assertRaises(TypeError):
            put("1", [])

    def test_string_body(self):
        """Test type error for string body."""
        # Act & Assert
        with self.assertRaises(TypeError):
            put("1", "invalid")

    def test_numeric_body(self):
        """Test type error for numeric body."""
        # Act & Assert
        with self.assertRaises(TypeError):
            put("1", 123)

    def test_boolean_body(self):
        """Test type error for boolean body."""
        # Act & Assert
        with self.assertRaises(TypeError):
            put("1", True)

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_update_database_index_preservation(self, mock_db, mock_datetime):
        """Test that user is updated at correct database index."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        original_user2 = mock_db.DB["scim"]["users"][1].copy()
        
        # Act - Update user 1
        result = put("1", self.valid_update_data)
        
        # Assert
        self.assertIsNotNone(result)
        # User 1 should be updated
        self.assertEqual(mock_db.DB["scim"]["users"][0]["userName"], "updated@gmail.com")
        # User 2 should remain unchanged
        self.assertEqual(mock_db.DB["scim"]["users"][1]["userName"], original_user2["userName"])

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_update_with_boolean_active_false(self, mock_db, mock_datetime):
        """Test update with active explicitly set to false should be forbidden."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        deactivate_data = self.valid_update_data.copy()
        deactivate_data["active"] = False
        
        # Act & Assert
        with self.assertRaises(UserUpdateForbiddenError) as context:
            put("1", deactivate_data)
        
        self.assertIn("Self-deactivation is forbidden", str(context.exception))

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_update_with_boolean_active_true(self, mock_db, mock_datetime):
        """Test update with active explicitly set to true."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        activate_data = self.valid_update_data.copy()
        activate_data["active"] = True
        
        # Act
        result = put("1", activate_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(result["active"])

    def test_invalid_email_format_malformed(self):
        """Test validation error for malformed email format."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["userName"] = "not-an-email"
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_invalid_email_format_missing_at(self):
        """Test validation error for email missing @ symbol."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["userName"] = "missingatgmail.com"
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    def test_invalid_email_format_missing_domain(self):
        """Test validation error for email missing domain."""
        # Arrange
        invalid_data = self.valid_update_data.copy()
        invalid_data["userName"] = "user@"
        
        # Act & Assert
        with self.assertRaises(UserUpdateValidationError):
            put("1", invalid_data)

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_update_preserves_created_timestamp(self, mock_db, mock_datetime):
        """Test that created timestamp is preserved during update."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        original_created = self.sample_users[0]["meta"]["created"]
        
        # Act
        result = put("1", self.valid_update_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["meta"]["created"], original_created)
        self.assertEqual(result["meta"]["lastModified"], "2024-02-01T12:00:00Z")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_update_with_empty_external_id_string(self, mock_db, mock_datetime):
        """Test update with empty string as externalId."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        empty_external_id_data = self.valid_update_data.copy()
        empty_external_id_data["externalId"] = ""
        
        # Act
        result = put("1", empty_external_id_data)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["externalId"], "")


if __name__ == '__main__':
    unittest.main()
