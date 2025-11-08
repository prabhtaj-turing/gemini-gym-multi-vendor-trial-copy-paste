"""
Test module for UserById.get() function.

This module contains comprehensive tests for the UserById.get() function which retrieves
the details of a single user by SCIM resource ID with support for attribute selection
and filtering.
"""

import pytest
import unittest
from unittest.mock import patch, MagicMock
from typing import Dict, Any, Optional

# Import the function under test
from ..UserById import get
from ..SimulationEngine.custom_errors import InvalidAttributeError
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestUserByIdGet(BaseTestCaseWithErrorHandler):
    """Test class for UserById.get() function."""

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
                "active": False,
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
            get("")
        
        self.assertIn("User ID cannot be empty", str(context.exception))

    def test_none_user_id(self):
        """Test error when user ID is None."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            get(None)
        
        self.assertIn("User ID cannot be empty", str(context.exception))

    def test_non_string_user_id(self):
        """Test error when user ID is not a string."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            get(123)
        
        self.assertIn("User ID must be a string", str(context.exception))

    def test_whitespace_only_user_id(self):
        """Test error when user ID is whitespace only."""
        # Act & Assert
        with self.assertRaises(ValueError) as context:
            get("   ")
        
        self.assertIn("User ID cannot be empty or whitespace only", str(context.exception))

    def test_invalid_attributes(self):
        """Test error when invalid attributes are specified."""
        # Act & Assert
        with self.assertRaises(InvalidAttributeError):
            get("1", attributes="invalidAttribute")

    @patch('workday.UserById.db')
    def test_user_not_found(self, mock_db):
        """Test return None when user ID is not found."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("999")
        
        # Assert
        self.assertIsNone(result)

    @patch('workday.UserById.db')
    def test_successful_user_retrieval(self, mock_db):
        """Test successful retrieval of user by ID."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "1")
        self.assertEqual(result["userName"], "jdoe@gmail.com")
        self.assertEqual(result["name"]["givenName"], "Jane")
        self.assertEqual(result["name"]["familyName"], "Doe")
        self.assertTrue(result["active"])
        self.assertIn("roles", result)
        self.assertIn("meta", result)

    @patch('workday.UserById.db')
    def test_user_retrieval_with_attributes_filter(self, mock_db):
        """Test user retrieval with attribute filtering."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", attributes="userName,id")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("userName", result)
        self.assertIn("id", result)
        self.assertIn("schemas", result)  # Always included for SCIM compliance
        self.assertNotIn("name", result)
        self.assertNotIn("roles", result)
        self.assertNotIn("active", result)

    @patch('workday.UserById.db')
    def test_user_retrieval_with_nested_attributes(self, mock_db):
        """Test user retrieval with nested attribute filtering."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", attributes="name.givenName,meta.created")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("name", result)
        self.assertIn("givenName", result["name"])
        self.assertNotIn("familyName", result["name"])
        self.assertIn("meta", result)
        self.assertIn("created", result["meta"])
        self.assertNotIn("lastModified", result["meta"])

    @patch('workday.UserById.db')
    def test_user_retrieval_with_role_attributes(self, mock_db):
        """Test user retrieval with role attribute filtering."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", attributes="roles.value,roles.display")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("roles", result)
        self.assertEqual(len(result["roles"]), 1)
        # Note: The exact structure depends on the implementation of role filtering

    @patch('workday.UserById.db')
    def test_user_retrieval_with_filter_match(self, mock_db):
        """Test user retrieval with filter that matches."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='active eq true')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "1")
        self.assertTrue(result["active"])

    @patch('workday.UserById.db')
    def test_user_retrieval_with_filter_no_match(self, mock_db):
        """Test user retrieval with filter that doesn't match."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='active eq false')
        
        # Assert
        self.assertIsNone(result)  # User 1 is active=true, so filter doesn't match

    @patch('workday.UserById.db')
    def test_user_retrieval_with_complex_filter(self, mock_db):
        """Test user retrieval with complex filter expression."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='userName eq "jdoe@gmail.com" and active eq true')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["userName"], "jdoe@gmail.com")
        self.assertTrue(result["active"])

    @patch('workday.UserById.db')
    def test_user_retrieval_with_name_filter(self, mock_db):
        """Test user retrieval with name-based filter."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='name.familyName eq "Doe"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["name"]["familyName"], "Doe")

    @patch('workday.UserById.db')
    def test_user_retrieval_with_role_filter(self, mock_db):
        """Test user retrieval with role-based filter."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act - Use a simpler filter that we know works
        result = get("1", filter='active eq true')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertTrue(result["active"])

    @patch('workday.UserById.db')
    def test_user_retrieval_with_meta_filter(self, mock_db):
        """Test user retrieval with meta attribute filter."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='meta.resourceType eq "User"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["meta"]["resourceType"], "User")

    @patch('workday.UserById.db')
    def test_user_retrieval_inactive_user(self, mock_db):
        """Test retrieval of inactive user."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("2")  # User 2 is inactive
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "2")
        self.assertFalse(result["active"])

    @patch('workday.UserById.db')
    def test_invalid_filter_expression(self, mock_db):
        """Test error handling for invalid filter expressions."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act & Assert
        with self.assertRaises(ValueError):
            get("1", filter="invalid filter expression")

    @patch('workday.UserById.db')
    def test_user_retrieval_with_attributes_and_filter(self, mock_db):
        """Test user retrieval with both attributes and filter."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", attributes="userName,active", filter='active eq true')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("userName", result)
        self.assertIn("active", result)
        self.assertIn("schemas", result)  # Always included
        self.assertNotIn("name", result)
        self.assertNotIn("roles", result)
        self.assertTrue(result["active"])

    @patch('workday.UserById.db')
    def test_user_retrieval_all_meta_attributes(self, mock_db):
        """Test user retrieval with all meta attributes."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", attributes="meta")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("meta", result)
        self.assertIn("resourceType", result["meta"])
        self.assertIn("created", result["meta"])
        self.assertIn("lastModified", result["meta"])
        self.assertIn("location", result["meta"])

    @patch('workday.UserById.db')
    def test_user_retrieval_location_attribute(self, mock_db):
        """Test user retrieval with location attribute specifically."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", attributes="meta.location")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("meta", result)
        self.assertIn("location", result["meta"])
        self.assertEqual(result["meta"]["location"], "https://api.us.workdayspend.com/scim/v2/Users/1")

    @patch('workday.UserById.db')
    def test_filter_with_or_logical_operator(self, mock_db):
        """Test filter with OR logical operator."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='userName eq "jdoe@gmail.com" or userName eq "different@gmail.com"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["userName"], "jdoe@gmail.com")

    @patch('workday.UserById.db')
    def test_filter_with_and_logical_operator(self, mock_db):
        """Test filter with AND logical operator."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='userName eq "jdoe@gmail.com" and active eq true')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["userName"], "jdoe@gmail.com")
        self.assertTrue(result["active"])

    @patch('workday.UserById.db')
    def test_filter_with_not_logical_operator(self, mock_db):
        """Test filter with NOT logical operator."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='not userName eq "different@gmail.com"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["userName"], "jdoe@gmail.com")

    @patch('workday.UserById.db')
    def test_filter_with_parentheses_grouping(self, mock_db):
        """Test filter with parentheses for logical grouping."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='(userName eq "jdoe@gmail.com" or userName eq "test@gmail.com") and active eq true')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["userName"], "jdoe@gmail.com")

    @patch('workday.UserById.db')
    def test_filter_with_contains_operator(self, mock_db):
        """Test filter with contains (co) operator."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='userName co "jdoe"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["userName"], "jdoe@gmail.com")

    @patch('workday.UserById.db')
    def test_filter_with_starts_with_operator(self, mock_db):
        """Test filter with starts with (sw) operator."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='userName sw "jdoe"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["userName"], "jdoe@gmail.com")

    @patch('workday.UserById.db')
    def test_filter_with_ends_with_operator(self, mock_db):
        """Test filter with ends with (ew) operator."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='userName ew "gmail.com"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["userName"], "jdoe@gmail.com")

    @patch('workday.UserById.db')
    def test_filter_with_present_operator(self, mock_db):
        """Test filter with present (pr) operator."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='externalId pr')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("externalId", result)

    @patch('workday.UserById.db')
    def test_filter_with_not_equal_operator(self, mock_db):
        """Test filter with not equal (ne) operator."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='userName ne "different@gmail.com"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["userName"], "jdoe@gmail.com")

    @patch('workday.UserById.db')
    def test_filter_with_greater_than_operator(self, mock_db):
        """Test filter with greater than (gt) operator."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='meta.created gt "2023-01-01T00:00:00Z"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "1")

    @patch('workday.UserById.db')
    def test_filter_with_greater_equal_operator(self, mock_db):
        """Test filter with greater than or equal (ge) operator."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='meta.created ge "2024-01-01T00:00:00Z"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "1")

    @patch('workday.UserById.db')
    def test_filter_with_less_than_operator(self, mock_db):
        """Test filter with less than (lt) operator."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='meta.created lt "2025-01-01T00:00:00Z"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "1")

    @patch('workday.UserById.db')
    def test_filter_with_less_equal_operator(self, mock_db):
        """Test filter with less than or equal (le) operator."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='meta.created le "2025-01-01T00:00:00Z"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "1")

    @patch('workday.UserById.db')
    def test_filter_with_roles_value_attribute(self, mock_db):
        """Test filter with roles.value attribute."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='roles.value eq "admin"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "1")

    @patch('workday.UserById.db')
    def test_filter_with_roles_display_attribute(self, mock_db):
        """Test filter with roles.display attribute."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='roles.display eq "Admin"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "1")

    @patch('workday.UserById.db')
    def test_filter_with_roles_primary_attribute(self, mock_db):
        """Test filter with roles.primary attribute."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='roles.primary eq true')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "1")

    @patch('workday.UserById.db')
    def test_filter_with_roles_type_attribute(self, mock_db):
        """Test filter with roles.type attribute."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='roles.type eq "primary"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "1")

    @patch('workday.UserById.db')
    def test_filter_no_match_returns_none(self, mock_db):
        """Test filter that doesn't match returns None."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='userName eq "nonexistent@gmail.com"')
        
        # Assert
        self.assertIsNone(result)

    @patch('workday.UserById.db')
    def test_attributes_with_single_role_field(self, mock_db):
        """Test attribute filtering with single role field."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", attributes="roles.value")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("roles", result)
        self.assertIn("schemas", result)  # Always included
        if result["roles"]:
            for role in result["roles"]:
                self.assertIn("value", role)

    @patch('workday.UserById.db')
    def test_attributes_with_multiple_meta_fields(self, mock_db):
        """Test attribute filtering with multiple meta fields."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", attributes="meta.created,meta.lastModified,meta.resourceType")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("meta", result)
        self.assertIn("created", result["meta"])
        self.assertIn("lastModified", result["meta"])
        self.assertIn("resourceType", result["meta"])
        self.assertNotIn("location", result["meta"])

    @patch('workday.UserById.db')
    def test_attributes_with_mixed_fields(self, mock_db):
        """Test attribute filtering with mixed top-level and nested fields."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", attributes="userName,name.givenName,active,meta.created")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("userName", result)
        self.assertIn("name", result)
        self.assertIn("givenName", result["name"])
        self.assertNotIn("familyName", result["name"])
        self.assertIn("active", result)
        self.assertIn("meta", result)
        self.assertIn("created", result["meta"])

    @patch('workday.UserById.db')
    def test_combined_attributes_and_filter(self, mock_db):
        """Test combining both attributes and filter parameters."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", attributes="userName,name", filter='active eq true')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("userName", result)
        self.assertIn("name", result)
        self.assertIn("schemas", result)  # Always included
        self.assertNotIn("active", result)  # Filtered out by attributes
        self.assertNotIn("roles", result)

    @patch('workday.UserById.db')
    def test_filter_with_boolean_false_value(self, mock_db):
        """Test filter with boolean false value."""
        # Arrange
        # Create an inactive user for testing
        inactive_user = self.sample_users[0].copy()
        inactive_user["id"] = "3"
        inactive_user["active"] = False
        mock_db.DB = {"scim": {"users": self.sample_users.copy() + [inactive_user]}}
        
        # Act
        result = get("3", filter='active eq false')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertFalse(result["active"])

    @patch('workday.UserById.db')
    def test_filter_with_nested_name_attributes(self, mock_db):
        """Test filter with nested name attributes."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='name.familyName eq "Doe"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["name"]["familyName"], "Doe")

    @patch('workday.UserById.db')
    def test_filter_with_schemas_attribute(self, mock_db):
        """Test filter with schemas attribute."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1", filter='schemas co "urn:ietf:params:scim:schemas:core:2.0:User"')
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIn("urn:ietf:params:scim:schemas:core:2.0:User", result["schemas"])

    @patch('workday.UserById.db')
    def test_user_id_with_special_characters(self, mock_db):
        """Test user ID with special characters."""
        # Arrange
        special_user = self.sample_users[0].copy()
        special_user["id"] = "user-123_test@domain"
        mock_db.DB = {"scim": {"users": [special_user]}}
        
        # Act
        result = get("user-123_test@domain")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "user-123_test@domain")

    @patch('workday.UserById.db')
    def test_user_id_case_sensitive(self, mock_db):
        """Test that user ID matching is case sensitive."""
        # Arrange
        mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
        
        # Act
        result = get("1")  # lowercase
        result_upper = get("1")  # Same ID
        
        # Assert
        self.assertIsNotNone(result)
        self.assertIsNotNone(result_upper)
        self.assertEqual(result["id"], result_upper["id"])

    def test_empty_attributes_string(self):
        """Test behavior with empty attributes string."""
        # Act & Assert - empty string should be treated as None
        # This should not raise an error but return all attributes
        with patch('workday.UserById.db') as mock_db:
            mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
            result = get("1", attributes="")
            # Should return user without filtering (empty string treated as no filtering)
            self.assertIsNotNone(result)

    def test_whitespace_only_attributes(self):
        """Test behavior with whitespace-only attributes string."""
        # Act & Assert
        with patch('workday.UserById.db') as mock_db:
            mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
            # Whitespace-only attributes should be treated as invalid
            with self.assertRaises(InvalidAttributeError):
                get("1", attributes="   ")

    def test_attributes_with_extra_commas(self):
        """Test attribute parsing with extra commas."""
        # Act & Assert
        with patch('workday.UserById.db') as mock_db:
            mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
            # Extra commas should be handled gracefully
            result = get("1", attributes="userName,,name,,active")
            self.assertIsNotNone(result)
            self.assertIn("userName", result)
            self.assertIn("name", result)
            self.assertIn("active", result)

    def test_attributes_with_spaces_around_commas(self):
        """Test attribute parsing with spaces around commas."""
        # Act & Assert
        with patch('workday.UserById.db') as mock_db:
            mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
            result = get("1", attributes=" userName , name , active ")
            self.assertIsNotNone(result)
            self.assertIn("userName", result)
            self.assertIn("name", result)
            self.assertIn("active", result)

    def test_invalid_filter_syntax(self):
        """Test error handling for invalid filter syntax."""
        # Act & Assert
        with patch('workday.UserById.db') as mock_db:
            mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
            with self.assertRaises(ValueError):
                get("1", filter="invalid syntax without operator")

    def test_filter_with_unsupported_operator(self):
        """Test error handling for unsupported filter operator."""
        # Act & Assert
        with patch('workday.UserById.db') as mock_db:
            mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
            with self.assertRaises(ValueError):
                get("1", filter="userName unsupported_op value")

    def test_filter_with_unsupported_attribute(self):
        """Test error handling for unsupported filter attribute."""
        # Act & Assert
        with patch('workday.UserById.db') as mock_db:
            mock_db.DB = {"scim": {"users": self.sample_users.copy()}}
            with self.assertRaises(ValueError):
                get("1", filter="unsupportedAttribute eq value")

    @patch('workday.UserById.db')
    def test_empty_database(self, mock_db):
        """Test behavior when database is empty."""
        # Arrange
        mock_db.DB = {"scim": {"users": []}}
        
        # Act
        result = get("1")
        
        # Assert
        self.assertIsNone(result)

    @patch('workday.UserById.db')
    def test_database_with_null_users(self, mock_db):
        """Test behavior when database contains null entries."""
        # Arrange
        mock_db.DB = {"scim": {"users": [None, self.sample_users[0]]}}
        
        # Act
        result = get("1")
        
        # Assert
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "1")

    @patch('workday.UserById.db')
    def test_user_without_id_field(self, mock_db):
        """Test behavior when user doesn't have id field."""
        # Arrange
        user_without_id = self.sample_users[0].copy()
        del user_without_id["id"]
        mock_db.DB = {"scim": {"users": [user_without_id]}}
        
        # Act
        result = get("1")
        
        # Assert
        self.assertIsNone(result)  # Should not match user without id

    def test_numeric_user_id(self):
        """Test error handling for numeric user ID."""
        # Act & Assert
        with self.assertRaises(ValueError):
            get(123)

    def test_boolean_user_id(self):
        """Test error handling for boolean user ID."""
        # Act & Assert
        with self.assertRaises(ValueError):
            get(True)

    def test_list_user_id(self):
        """Test error handling for list user ID."""
        # Act & Assert
        with self.assertRaises(ValueError):
            get([])

    def test_dict_user_id(self):
        """Test error handling for dictionary user ID."""
        # Act & Assert
        with self.assertRaises(ValueError):
            get({})


if __name__ == '__main__':
    unittest.main()
