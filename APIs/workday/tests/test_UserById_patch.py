"""
Test module for UserById.patch() function.

This module contains comprehensive tests for the UserById.patch() function which updates
one or more attributes of a User resource using SCIM PATCH operations with support for
add, remove, and replace operations.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any

# Import the function under test
from ..UserById import patch as patch_user
from ..SimulationEngine.custom_errors import (
    InvalidAttributeError, UserPatchValidationError, UserPatchForbiddenError, 
    UserPatchOperationError
)
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestUserByIdPatch(BaseTestCaseWithErrorHandler):
    """Test class for UserById.patch() function."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Sample user for testing
        self.sample_user = {
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
        }

        # Valid patch operation examples
        self.valid_patch_operations = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "name.givenName",
                    "value": "John"
                }
            ]
        }

    def test_empty_user_id(self):
        """Test error when user ID is empty."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            patch_user("", {})
        
        self.assertIn("User ID cannot be empty", str(context.exception))

    def test_none_user_id(self):
        """Test error when user ID is None."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            patch_user(None, {})
        
        self.assertIn("User ID cannot be empty", str(context.exception))

    def test_non_string_user_id(self):
        """Test error when user ID is not a string."""
        # Act & Assert
        with self.assertRaises(TypeError) as context:
            patch_user(123, {})
        
        self.assertIn("User ID must be a string", str(context.exception))

    def test_whitespace_only_user_id(self):
        """Test error when user ID is whitespace only."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            patch_user("   ", {})
        
        self.assertIn("User ID cannot be empty or whitespace only", str(context.exception))

    def test_non_dict_body(self):
        """Test error when body is not a dictionary."""
        # Act & Assert
        with self.assertRaises(TypeError) as context:
            patch_user("1", "not a dict")
        
        self.assertIn("body must be a dictionary", str(context.exception))

    def test_invalid_attributes(self):
        """Test error when invalid attributes are specified."""
        # Act & Assert
        with self.assertRaises(InvalidAttributeError):
            patch_user("1", self.valid_patch_operations, attributes="invalidAttribute")

    def test_missing_operations(self):
        """Test validation error when Operations field is missing."""
        # Arrange
        invalid_patch = {"schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"]}
        
        # Act & Assert
        with self.assertRaises(UserPatchValidationError):
            patch_user("1", invalid_patch)

    @patch('workday.UserById.db')
    def test_empty_operations_list(self, mock_db):
        """Test handling of empty Operations list."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        empty_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": []
        }
        
        # Act - Empty operations list should succeed but do nothing
        result = patch_user("1", empty_patch)
        
        # Assert - User should be returned unchanged
        self.assertIsNotNone(result)
        self.assertEqual(result["name"]["givenName"], "Jane")

    def test_invalid_operation_structure(self):
        """Test validation error for invalid operation structure."""
        # Arrange
        invalid_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "invalid": "operation"  # Missing required 'op' field
                }
            ]
        }
        
        # Act & Assert
        with self.assertRaises(UserPatchValidationError):
            patch_user("1", invalid_patch)

    @patch('workday.UserById.db')
    def test_user_not_found(self, mock_db):
        """Test return None when user ID is not found."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        
        # Act
        result = patch_user("999", self.valid_patch_operations)
        
        # Assert
        self.assertIsNone(result)

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_successful_replace_operation(self, mock_db, mock_datetime):
        """Test successful replace operation."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        replace_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "name.givenName",
                    "value": "John"
                }
            ]
        }
        
        # Act
        result = patch_user("1", replace_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["name"]["givenName"], "John")
        self.assertEqual(result["name"]["familyName"], "Doe")  # Should remain unchanged
        self.assertEqual(result["meta"]["lastModified"], "2024-02-01T12:00:00Z")
        self.assertIn("location", result["meta"])

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_successful_add_operation(self, mock_db, mock_datetime):
        """Test successful add operation."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        add_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "add",
                    "path": "roles",
                    "value": {
                        "value": "user",
                        "display": "User",
                        "primary": False,
                        "type": "secondary"
                    }
                }
            ]
        }
        
        # Act
        result = patch_user("1", add_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(len(result["roles"]), 2)  # Should have added a role
        self.assertEqual(result["roles"][1]["value"], "user")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_successful_remove_operation(self, mock_db, mock_datetime):
        """Test successful remove operation."""
        # Arrange
        user_with_external_id = self.sample_user.copy()
        mock_db.DB = {"scim": {"users": [user_with_external_id]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        remove_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "remove",
                    "path": "externalId"
                }
            ]
        }
        
        # Act
        result = patch_user("1", remove_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertNotIn("externalId", result)  # Should be removed

    @patch('workday.UserById.db')
    def test_forbidden_self_deactivation(self, mock_db):
        """Test forbidden operation when trying to deactivate user."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        
        deactivate_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "active",
                    "value": False
                }
            ]
        }
        
        # Act & Assert
        with self.assertRaises(UserPatchForbiddenError) as context:
            patch_user("1", deactivate_patch)
        
        self.assertIn("Self-deactivation is forbidden", str(context.exception))

    @patch('workday.UserById.db')
    def test_forbidden_domain_change(self, mock_db):
        """Test forbidden operation when trying to change email domain."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        
        domain_change_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "userName",
                    "value": "jdoe@different-domain.com"
                }
            ]
        }
        
        # Act & Assert
        with self.assertRaises(UserPatchForbiddenError) as context:
            patch_user("1", domain_change_patch)
        
        self.assertIn("Email domain change is forbidden", str(context.exception))

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_multiple_operations(self, mock_db, mock_datetime):
        """Test applying multiple patch operations."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        multiple_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "name.givenName",
                    "value": "John"
                },
                {
                    "op": "replace",
                    "path": "name.familyName",
                    "value": "Smith"
                }
            ]
        }
        
        # Act
        result = patch_user("1", multiple_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["name"]["givenName"], "John")
        self.assertEqual(result["name"]["familyName"], "Smith")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_patch_with_attributes_filter(self, mock_db, mock_datetime):
        """Test patch operation with attribute filtering in response."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = patch_user("1", self.valid_patch_operations, attributes="userName,name")
        
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
        user_without_location = self.sample_user.copy()
        del user_without_location["meta"]["location"]  # Remove location
        mock_db.DB = {"scim": {"users": [user_without_location]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = patch_user("1", self.valid_patch_operations)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("location", result["meta"])
        self.assertEqual(result["meta"]["location"], "https://api.us.workdayspend.com/scim/v2/Users/1")

    @patch('workday.UserById.db')
    def test_patch_operation_failure(self, mock_db):
        """Test error handling when patch operation fails."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        
        # Mock the apply_patch_operation to raise an exception
        with patch('workday.UserById.apply_patch_operation') as mock_apply:
            mock_apply.side_effect = Exception("Operation failed")
            
            # Act & Assert
            with self.assertRaises(UserPatchOperationError) as context:
                patch_user("1", self.valid_patch_operations)
            
            self.assertIn("Failed to apply patch operations", str(context.exception))

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_replace_entire_name_object(self, mock_db, mock_datetime):
        """Test replacing entire name object."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        name_replace_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "name",
                    "value": {
                        "givenName": "Robert",
                        "familyName": "Johnson"
                    }
                }
            ]
        }
        
        # Act
        result = patch_user("1", name_replace_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["name"]["givenName"], "Robert")
        self.assertEqual(result["name"]["familyName"], "Johnson")

    def test_invalid_operation_type(self):
        """Test validation error for invalid operation type."""
        # Arrange
        invalid_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "invalid_operation",
                    "path": "name.givenName",
                    "value": "John"
                }
            ]
        }
        
        # Act & Assert
        with self.assertRaises(UserPatchValidationError):
            patch_user("1", invalid_patch)

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_add_operation_to_array_field(self, mock_db, mock_datetime):
        """Test add operation on array field like roles."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        add_role_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "add",
                    "path": "roles",
                    "value": [
                        {
                            "value": "manager",
                            "display": "Manager",
                            "primary": False,
                            "type": "secondary"
                        }
                    ]
                }
            ]
        }
        
        # Act
        result = patch_user("1", add_role_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(len(result["roles"]), 2)  # Original + added role

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_remove_operation_from_nested_object(self, mock_db, mock_datetime):
        """Test remove operation on nested object field."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        remove_given_name_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "remove",
                    "path": "name.givenName"
                }
            ]
        }
        
        # Act
        result = patch_user("1", remove_given_name_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertNotIn("givenName", result["name"])
        self.assertIn("familyName", result["name"])  # Should remain

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_replace_operation_with_null_value(self, mock_db, mock_datetime):
        """Test replace operation with null value."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        null_replace_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "externalId",
                    "value": None
                }
            ]
        }
        
        # Act
        result = patch_user("1", null_replace_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIsNone(result["externalId"])

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_add_operation_without_path(self, mock_db, mock_datetime):
        """Test add operation without explicit path (root level)."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        add_root_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "add",
                    "value": {
                        "displayName": "Jane Doe Admin"
                    }
                }
            ]
        }
        
        # Act
        result = patch_user("1", add_root_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("displayName", result)
        self.assertEqual(result["displayName"], "Jane Doe Admin")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_remove_operation_without_value(self, mock_db, mock_datetime):
        """Test remove operation without value parameter."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        remove_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "remove",
                    "path": "externalId"
                    # No value parameter
                }
            ]
        }
        
        # Act
        result = patch_user("1", remove_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertNotIn("externalId", result)

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_complex_nested_path_operation(self, mock_db, mock_datetime):
        """Test operation with complex nested path."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        nested_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "meta.lastModified",
                    "value": "2024-03-01T12:00:00Z"
                }
            ]
        }
        
        # Act
        result = patch_user("1", nested_patch)
        
        # Assert
        self.assertIsNotNone(result)
        # The actual lastModified should be updated by the function, not by our patch
        self.assertEqual(result["meta"]["lastModified"], "2024-02-01T12:00:00Z")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_sequential_operations_on_same_field(self, mock_db, mock_datetime):
        """Test multiple operations on the same field in sequence."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        sequential_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "name.givenName",
                    "value": "John"
                },
                {
                    "op": "replace",
                    "path": "name.givenName",
                    "value": "Johnny"
                }
            ]
        }
        
        # Act
        result = patch_user("1", sequential_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["name"]["givenName"], "Johnny")  # Should be the last operation

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_add_then_remove_operation(self, mock_db, mock_datetime):
        """Test adding a field then removing it in the same patch."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        add_remove_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "add",
                    "path": "displayName",
                    "value": "Jane Doe"
                },
                {
                    "op": "remove",
                    "path": "displayName"
                }
            ]
        }
        
        # Act
        result = patch_user("1", add_remove_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertNotIn("displayName", result)  # Should be removed

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_operation_with_complex_value_object(self, mock_db, mock_datetime):
        """Test operation with complex object as value."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        complex_value_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "name",
                    "value": {
                        "givenName": "John",
                        "familyName": "Smith",
                        "middleName": "William",
                        "honorificPrefix": "Mr.",
                        "honorificSuffix": "Jr."
                    }
                }
            ]
        }
        
        # Act
        result = patch_user("1", complex_value_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["name"]["givenName"], "John")
        self.assertEqual(result["name"]["familyName"], "Smith")
        self.assertEqual(result["name"]["middleName"], "William")
        self.assertEqual(result["name"]["honorificPrefix"], "Mr.")
        self.assertEqual(result["name"]["honorificSuffix"], "Jr.")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_operation_with_array_value(self, mock_db, mock_datetime):
        """Test operation with array as value."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        array_value_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "roles",
                    "value": [
                        {
                            "value": "user",
                            "display": "User",
                            "primary": True,
                            "type": "primary"
                        },
                        {
                            "value": "manager",
                            "display": "Manager",
                            "primary": False,
                            "type": "secondary"
                        }
                    ]
                }
            ]
        }
        
        # Act
        result = patch_user("1", array_value_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(len(result["roles"]), 2)
        self.assertEqual(result["roles"][0]["value"], "user")
        self.assertEqual(result["roles"][1]["value"], "manager")

    def test_missing_schemas_field(self):
        """Test that missing schemas field is allowed (schemas is optional)."""
        # Arrange
        valid_patch = {
            "Operations": [
                {
                    "op": "replace",
                    "path": "name.givenName",
                    "value": "John"
                }
            ]
        }
        
        # Act & Assert - Should NOT raise an error since schemas is optional
        with patch('workday.UserById.db') as mock_db:
            mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
            with patch('workday.UserById.datetime') as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
                result = patch_user("1", valid_patch)
                self.assertIsNotNone(result)

    def test_invalid_schemas_value(self):
        """Test validation error for invalid schemas value."""
        # Arrange
        invalid_patch = {
            "schemas": "not_a_list",
            "Operations": [
                {
                    "op": "replace",
                    "path": "name.givenName",
                    "value": "John"
                }
            ]
        }
        
        # Act & Assert
        with self.assertRaises(UserPatchValidationError):
            patch_user("1", invalid_patch)

    def test_empty_schemas_list(self):
        """Test that empty schemas list is allowed (schemas is optional)."""
        # Arrange
        valid_patch = {
            "schemas": [],
            "Operations": [
                {
                    "op": "replace",
                    "path": "name.givenName",
                    "value": "John"
                }
            ]
        }
        
        # Act & Assert - Should NOT raise an error since empty schemas is allowed
        with patch('workday.UserById.db') as mock_db:
            mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
            with patch('workday.UserById.datetime') as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
                result = patch_user("1", valid_patch)
                self.assertIsNotNone(result)

    def test_invalid_schemas_item(self):
        """Test validation error for invalid item in schemas list."""
        # Arrange
        invalid_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp", 123],
            "Operations": [
                {
                    "op": "replace",
                    "path": "name.givenName",
                    "value": "John"
                }
            ]
        }
        
        # Act & Assert
        with self.assertRaises(UserPatchValidationError):
            patch_user("1", invalid_patch)

    def test_missing_op_field_in_operation(self):
        """Test validation error when op field is missing from operation."""
        # Arrange
        invalid_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "path": "name.givenName",
                    "value": "John"
                }
            ]
        }
        
        # Act & Assert
        with self.assertRaises(UserPatchValidationError):
            patch_user("1", invalid_patch)

    def test_invalid_op_value(self):
        """Test validation error for invalid op value."""
        # Arrange
        invalid_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": 123,  # Should be string
                    "path": "name.givenName",
                    "value": "John"
                }
            ]
        }
        
        # Act & Assert
        with self.assertRaises(UserPatchValidationError):
            patch_user("1", invalid_patch)

    def test_invalid_path_type(self):
        """Test validation error for invalid path type."""
        # Arrange
        invalid_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": 123,  # Should be string
                    "value": "John"
                }
            ]
        }
        
        # Act & Assert
        with self.assertRaises(UserPatchValidationError):
            patch_user("1", invalid_patch)

    def test_operations_not_a_list(self):
        """Test validation error when Operations is not a list."""
        # Arrange
        invalid_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": "not_a_list"
        }
        
        # Act & Assert
        with self.assertRaises(UserPatchValidationError):
            patch_user("1", invalid_patch)

    def test_operation_not_an_object(self):
        """Test validation error when operation is not an object."""
        # Arrange
        invalid_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": ["not_an_object"]
        }
        
        # Act & Assert
        with self.assertRaises(UserPatchValidationError):
            patch_user("1", invalid_patch)

    @patch('workday.UserById.db')
    def test_forbidden_username_domain_change(self, mock_db):
        """Test forbidden operation when trying to change username to different domain."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        
        domain_change_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "userName",
                    "value": "jdoe@different-domain.com"
                }
            ]
        }
        
        # Act & Assert
        with self.assertRaises(UserPatchForbiddenError) as context:
            patch_user("1", domain_change_patch)
        
        self.assertIn("Email domain change is forbidden", str(context.exception))

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_allowed_username_same_domain_change(self, mock_db, mock_datetime):
        """Test allowed operation when changing username within same domain."""
        # Arrange
        mock_db.DB = {"scim": {"users": [self.sample_user.copy()]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        same_domain_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "userName",
                    "value": "jane.doe@gmail.com"  # Same domain
                }
            ]
        }
        
        # Act
        result = patch_user("1", same_domain_patch)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["userName"], "jane.doe@gmail.com")

    def test_extra_field_in_patch_body(self):
        """Test validation error for extra fields in patch body."""
        # Arrange
        invalid_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "name.givenName",
                    "value": "John"
                }
            ],
            "extraField": "should not be allowed"
        }
        
        # Act & Assert
        with self.assertRaises(UserPatchValidationError):
            patch_user("1", invalid_patch)

    def test_extra_field_in_operation(self):
        """Test validation error for extra fields in operation."""
        # Arrange
        invalid_patch = {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
            "Operations": [
                {
                    "op": "replace",
                    "path": "name.givenName",
                    "value": "John",
                    "extraField": "should not be allowed"
                }
            ]
        }
        
        # Act & Assert
        with self.assertRaises(UserPatchValidationError):
            patch_user("1", invalid_patch)

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_meta_object_creation_if_missing(self, mock_db, mock_datetime):
        """Test that meta object is created if it doesn't exist."""
        # Arrange
        user_without_meta = self.sample_user.copy()
        del user_without_meta["meta"]
        mock_db.DB = {"scim": {"users": [user_without_meta]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = patch_user("1", self.valid_patch_operations)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("meta", result)
        self.assertEqual(result["meta"]["lastModified"], "2024-02-01T12:00:00Z")

    @patch('workday.UserById.datetime')
    @patch('workday.UserById.db')
    def test_meta_object_recreation_if_invalid(self, mock_db, mock_datetime):
        """Test that meta object is recreated if it's not a dictionary."""
        # Arrange
        user_with_invalid_meta = self.sample_user.copy()
        user_with_invalid_meta["meta"] = "not a dict"
        mock_db.DB = {"scim": {"users": [user_with_invalid_meta]}}
        mock_datetime.now.return_value.isoformat.return_value = "2024-02-01T12:00:00Z"
        mock_datetime.now.return_value = datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        
        # Act
        result = patch_user("1", self.valid_patch_operations)
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIsInstance(result["meta"], dict)
        self.assertEqual(result["meta"]["lastModified"], "2024-02-01T12:00:00Z")

    def test_empty_body_dict(self):
        """Test validation error for empty body dictionary."""
        # Act & Assert
        with self.assertRaises(UserPatchValidationError):
            patch_user("1", {})

    def test_none_body(self):
        """Test type error for None body."""
        # Act & Assert
        with self.assertRaises(TypeError):
            patch_user("1", None)

    def test_list_body(self):
        """Test type error for list body."""
        # Act & Assert
        with self.assertRaises(TypeError):
            patch_user("1", [])

    def test_string_body(self):
        """Test type error for string body."""
        # Act & Assert
        with self.assertRaises(TypeError):
            patch_user("1", "invalid")

    def test_numeric_body(self):
        """Test type error for numeric body."""
        # Act & Assert
        with self.assertRaises(TypeError):
            patch_user("1", 123)

    def test_boolean_body(self):
        """Test type error for boolean body."""
        # Act & Assert
        with self.assertRaises(TypeError):
            patch_user("1", True)


if __name__ == '__main__':
    unittest.main()
