"""
Test module for UserById.delete() function.

This module contains comprehensive tests for the UserById.delete() function which deactivates
a user by setting their active field to False with business rule enforcement.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any

# Import the function under test
from ..UserById import delete
from ..SimulationEngine.custom_errors import (
    UserDeleteForbiddenError, UserDeleteOperationError
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestUserByIdDelete(BaseTestCaseWithErrorHandler):
    """Test class for UserById.delete() function."""

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
                "userName": "asmith@gmail.com",
                "name": {
                    "givenName": "Alice",
                    "familyName": "Smith"
                },
                "active": False,  # Already inactive
                "roles": [
                    {
                        "value": "manager",
                        "display": "Manager",
                        "primary": True,
                        "type": "primary"
                    }
                ],
                "meta": {
                    "resourceType": "User",
                    "created": "2024-01-02T00:00:00Z",
                    "lastModified": "2024-06-02T00:00:00Z",
                    "location": "https://api.us.workdayspend.com/scim/v2/Users/2"
                }
            }
        ]

    def test_empty_user_id(self):
        """Test error when user ID is empty."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            delete("")
        
        self.assertIn("User ID cannot be empty", str(context.exception))

    def test_none_user_id(self):
        """Test error when user ID is None."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            delete(None)
        
        self.assertIn("User ID cannot be empty", str(context.exception))

    def test_non_string_user_id(self):
        """Test error when user ID is not a string."""
        # Act & Assert
        with self.assertRaises(TypeError) as context:
            delete(123)
        
        self.assertIn("User ID must be a string", str(context.exception))

    def test_whitespace_only_user_id(self):
        """Test error when user ID is whitespace only."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            delete("   ")
        
        self.assertIn("User ID cannot be empty or whitespace only", str(context.exception))

    @patch('workday.UserById.db')
    def test_user_not_found(self, mock_db):
        """Test return False when user ID is not found."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        
        # Act
        result = delete("999")
        
        # Assert
        self.assertFalse(result)

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_successful_user_deactivation(self, mock_db, mock_datetime):
        """Test successful user deactivation."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        # Verify user is deactivated in database
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertFalse(updated_user["active"])
        self.assertEqual(updated_user["meta"]["lastModified"], "2024-02-01T12:00:00Z")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_deactivate_already_inactive_user(self, mock_db, mock_datetime):
        """Test deactivating an already inactive user."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("2")  # User 2 is already inactive
        
        # Assert
        self.assertTrue(result)
        # Verify user remains inactive
        updated_user = mock_db.DB["scim"]["users"][1]
        self.assertFalse(updated_user["active"])
        self.assertEqual(updated_user["meta"]["lastModified"], "2024-02-01T12:00:00Z")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_location_field_preserved_during_deactivation(self, mock_db, mock_datetime):
        """Test that location field is preserved/added during deactivation."""
        # Arrange
        user_without_location = self.sample_users[0].copy()
        del user_without_location["meta"]["location"]  # Remove location
        mock_db.DB = {"scim": {"users": [user_without_location]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertIn("location", updated_user["meta"])
        self.assertEqual(updated_user["meta"]["location"], "https://api.us.workdayspend.com/scim/v2/Users/1")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_meta_object_created_if_missing(self, mock_db, mock_datetime):
        """Test that meta object is created if it doesn't exist."""
        # Arrange
        user_without_meta = self.sample_users[0].copy()
        del user_without_meta["meta"]  # Remove meta object
        mock_db.DB = {"scim": {"users": [user_without_meta]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertIn("meta", updated_user)
        self.assertEqual(updated_user["meta"]["lastModified"], "2024-02-01T12:00:00Z")
        self.assertEqual(updated_user["meta"]["location"], "https://api.us.workdayspend.com/scim/v2/Users/1")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_meta_object_recreated_if_not_dict(self, mock_db, mock_datetime):
        """Test that meta object is recreated if it's not a dictionary."""
        # Arrange
        user_with_invalid_meta = self.sample_users[0].copy()
        user_with_invalid_meta["meta"] = "not a dict"  # Invalid meta
        mock_db.DB = {"scim": {"users": [user_with_invalid_meta]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertIsInstance(updated_user["meta"], dict)
        self.assertEqual(updated_user["meta"]["lastModified"], "2024-02-01T12:00:00Z")

    @patch('workday.UserById.db')
    def test_delete_operation_failure(self, mock_db):
        """Test error handling when delete operation fails."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Mock the database update to raise an exception
        with patch('workday.UserById.datetime') as mock_datetime:
            mock_datetime.now.side_effect = Exception("DateTime error")
            
            # Act & Assert
            with self.assertRaises(UserDeleteOperationError) as context:
                delete("1")
            
            self.assertIn("Failed to deactivate user", str(context.exception))

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_user_fields_preserved_except_active(self, mock_db, mock_datetime):
        """Test that all user fields are preserved except active during deactivation."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        original_user = self.sample_users[0].copy()
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        
        # Check that all fields are preserved except active
        self.assertEqual(updated_user["id"], original_user["id"])
        self.assertEqual(updated_user["userName"], original_user["userName"])
        self.assertEqual(updated_user["name"], original_user["name"])
        self.assertEqual(updated_user["externalId"], original_user["externalId"])
        self.assertEqual(updated_user["roles"], original_user["roles"])
        self.assertEqual(updated_user["schemas"], original_user["schemas"])
        
        # active should be changed to False
        self.assertFalse(updated_user["active"])
        self.assertTrue(original_user["active"])  # Original was True

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_multiple_users_correct_user_deactivated(self, mock_db, mock_datetime):
        """Test that only the specified user is deactivated when multiple users exist."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("1")  # Deactivate user 1
        
        # Assert
        self.assertTrue(result)
        
        # User 1 should be deactivated
        user1 = mock_db.DB["scim"]["users"][0]
        self.assertFalse(user1["active"])
        self.assertEqual(user1["meta"]["lastModified"], "2024-02-01T12:00:00Z")
        
        # User 2 should remain unchanged
        user2 = mock_db.DB["scim"]["users"][1]
        self.assertFalse(user2["active"])  # Was already inactive
        self.assertEqual(user2["meta"]["lastModified"], "2024-06-02T00:00:00Z")  # Original timestamp unchanged

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_deactivation_updates_correct_user_index(self, mock_db, mock_datetime):
        """Test that deactivation updates the correct user in the database list."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Get original references
        original_user1 = mock_db.DB["scim"]["users"][0]
        original_user2 = mock_db.DB["scim"]["users"][1]
        
        # Act
        result = delete("2")  # Deactivate user 2
        
        # Assert
        self.assertTrue(result)
        
        # Verify the correct user object was modified
        self.assertTrue(mock_db.DB["scim"]["users"][0]["active"])  # User 1 unchanged
        self.assertFalse(mock_db.DB["scim"]["users"][1]["active"])  # User 2 deactivated
        self.assertEqual(mock_db.DB["scim"]["users"][1]["meta"]["lastModified"], "2024-02-01T12:00:00Z")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_existing_location_preserved(self, mock_db, mock_datetime):
        """Test that existing location field is preserved during deactivation."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        original_location = self.sample_users[0]["meta"]["location"]
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertEqual(updated_user["meta"]["location"], original_location)

    @patch('workday.UserById.db')
    def test_empty_database(self, mock_db):
        """Test behavior when database is empty."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertFalse(result)

    @patch('workday.UserById.db')
    def test_database_with_null_users(self, mock_db):
        """Test behavior when database contains null entries."""
        # Arrange
        mock_db.DB = {"scim": {"users": [None, self.sample_users[0]]}}
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)

    @patch('workday.UserById.db')
    def test_user_without_id_field(self, mock_db):
        """Test behavior when user doesn't have id field."""
        # Arrange
        user_without_id = self.sample_users[0].copy()
        del user_without_id["id"]
        mock_db.DB = {"scim": {"users": [user_without_id]}}
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertFalse(result)  # Should not match user without id

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_user_id_with_special_characters(self, mock_db, mock_datetime):
        """Test deletion with user ID containing special characters."""
        # Arrange
        special_user = self.sample_users[0].copy()
        special_user["id"] = "user-123_test@domain"
        mock_db.DB = {"scim": {"users": [special_user]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("user-123_test@domain")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertFalse(updated_user["active"])

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_user_id_case_sensitive(self, mock_db, mock_datetime):
        """Test that user ID matching is case sensitive."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act - Try with different case
        result_lower = delete("1")  # Should match
        result_upper = delete("1")  # Same ID
        
        # Assert
        self.assertTrue(result_lower)
        self.assertTrue(result_upper)  # Should work for same ID

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_multiple_calls_on_same_user(self, mock_db, mock_datetime):
        """Test multiple delete calls on the same user."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act - First delete
        result1 = delete("1")
        # Act - Second delete on same user
        result2 = delete("1")
        
        # Assert
        self.assertTrue(result1)  # First delete should succeed
        self.assertTrue(result2)  # Second delete should also succeed (user still exists)
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertFalse(updated_user["active"])  # Should remain inactive

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_deactivation_preserves_all_other_fields(self, mock_db, mock_datetime):
        """Test that deactivation preserves all fields except active."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        original_user = self.sample_users[0].copy()
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        
        # Check all fields are preserved except active
        self.assertEqual(updated_user["id"], original_user["id"])
        self.assertEqual(updated_user["userName"], original_user["userName"])
        self.assertEqual(updated_user["name"], original_user["name"])
        self.assertEqual(updated_user["externalId"], original_user["externalId"])
        self.assertEqual(updated_user["roles"], original_user["roles"])
        self.assertEqual(updated_user["schemas"], original_user["schemas"])
        self.assertFalse(updated_user["active"])  # Only this should change
        self.assertTrue(original_user["active"])  # Original was active

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_database_index_preservation(self, mock_db, mock_datetime):
        """Test that user is deactivated at correct database index."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        original_user2 = mock_db.DB["scim"]["users"][1].copy()
        
        # Act - Delete user 1
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        # User 1 should be deactivated
        self.assertFalse(mock_db.DB["scim"]["users"][0]["active"])
        # User 2 should remain unchanged
        self.assertEqual(mock_db.DB["scim"]["users"][1]["active"], original_user2["active"])
        self.assertEqual(mock_db.DB["scim"]["users"][1]["meta"]["lastModified"], original_user2["meta"]["lastModified"])

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_timestamp_format_consistency(self, mock_db, mock_datetime):
        """Test that timestamp format is consistent."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        test_timestamp = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value.isoformat.return_value = test_timestamp
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertEqual(updated_user["meta"]["lastModified"], test_timestamp)

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_meta_resource_type_preserved(self, mock_db, mock_datetime):
        """Test that meta resourceType is preserved during deactivation."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertEqual(updated_user["meta"]["resourceType"], "User")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_meta_created_preserved(self, mock_db, mock_datetime):
        """Test that meta created timestamp is preserved during deactivation."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        original_created = self.sample_users[0]["meta"]["created"]
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertEqual(updated_user["meta"]["created"], original_created)

    def test_numeric_user_id(self):
        """Test error handling for numeric user ID."""
        # Act & Assert
        with self.assertRaises(TypeError):
            delete(123)

    def test_boolean_user_id(self):
        """Test error handling for boolean user ID."""
        # Act & Assert
        with self.assertRaises(TypeError):
            delete(True)

    def test_list_user_id(self):
        """Test error handling for list user ID."""
        # Act & Assert
        with self.assertRaises(TypeError):
            delete([])

    def test_dict_user_id(self):
        """Test error handling for dictionary user ID."""
        # Act & Assert
        with self.assertRaises(TypeError):
            delete({})

    def test_float_user_id(self):
        """Test error handling for float user ID."""
        # Act & Assert
        with self.assertRaises(TypeError):
            delete(1.23)

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_user_with_missing_active_field(self, mock_db, mock_datetime):
        """Test deactivation of user missing active field."""
        # Arrange
        user_without_active = self.sample_users[0].copy()
        del user_without_active["active"]
        mock_db.DB = {"scim": {"users": [user_without_active]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertFalse(updated_user["active"])  # Should be added and set to False

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_user_with_invalid_active_field(self, mock_db, mock_datetime):
        """Test deactivation of user with invalid active field type."""
        # Arrange
        user_with_invalid_active = self.sample_users[0].copy()
        user_with_invalid_active["active"] = "true"  # String instead of boolean
        mock_db.DB = {"scim": {"users": [user_with_invalid_active]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertFalse(updated_user["active"])  # Should be set to False

    @patch('workday.UserById.db')
    def test_datetime_exception_handling(self, mock_db):
        """Test error handling when datetime operation fails."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Mock datetime to raise an exception
        with patch('workday.UserById.datetime') as mock_datetime:
            mock_datetime.now.side_effect = Exception("DateTime error")
            
            # Act & Assert
            with self.assertRaises(UserDeleteOperationError) as context:
                delete("1")
            
            self.assertIn("Failed to deactivate user", str(context.exception))

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_database_modification_in_place(self, mock_db, mock_datetime):
        """Test that database list is modified in place."""
        # Arrange
        original_list = self.sample_users.copy()
        mock_db.DB = {"scim": {"users": original_list}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        # Verify the same list object was modified
        self.assertIs(mock_db.DB["scim"]["users"], original_list)
        self.assertFalse(original_list[0]["active"])

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_unicode_user_id(self, mock_db, mock_datetime):
        """Test deletion with unicode user ID."""
        # Arrange
        unicode_user = self.sample_users[0].copy()
        unicode_user["id"] = "user-José-123"
        mock_db.DB = {"scim": {"users": [unicode_user]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("user-José-123")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertFalse(updated_user["active"])

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_very_long_user_id(self, mock_db, mock_datetime):
        """Test deletion with very long user ID."""
        # Arrange
        long_user = self.sample_users[0].copy()
        long_user["id"] = "a" * 1000  # Very long ID
        mock_db.DB = {"scim": {"users": [long_user]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("a" * 1000)
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertFalse(updated_user["active"])

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_user_id_with_newlines(self, mock_db, mock_datetime):
        """Test deletion with user ID containing newlines."""
        # Arrange
        newline_user = self.sample_users[0].copy()
        newline_user["id"] = "user\nwith\nnewlines"
        mock_db.DB = {"scim": {"users": [newline_user]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("user\nwith\nnewlines")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        self.assertFalse(updated_user["active"])

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_location_url_format_consistency(self, mock_db, mock_datetime):
        """Test that location URL format is consistent."""
        # Arrange
        user_without_location = self.sample_users[0].copy()
        del user_without_location["meta"]["location"]
        mock_db.DB = {"scim": {"users": [user_without_location]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = delete("1")
        
        # Assert
        self.assertTrue(result)
        updated_user = mock_db.DB["scim"]["users"][0]
        expected_location = "https://api.us.workdayspend.com/scim/v2/Users/1"
        self.assertEqual(updated_user["meta"]["location"], expected_location)


if __name__ == '__main__':
    unittest.main()
