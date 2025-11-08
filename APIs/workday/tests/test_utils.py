"""
Test suite for utility functions in the Workday Strategic Sourcing API Simulation.
"""

import unittest
from datetime import datetime
from typing import Dict, Any, List
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import utils
from ..SimulationEngine.custom_errors import InvalidAttributeError, UserPatchForbiddenError
from pydantic import ValidationError as PydanticValidationError


class TestWorkdayUtils(BaseTestCaseWithErrorHandler):
    
    def setUp(self):
        """Set up test data before each test."""
        self.sample_users = [
            {
                "id": "user1",
                "userName": "john.doe@example.com",
                "name": {"givenName": "John", "familyName": "Doe"},
                "active": True,
                "externalId": "ext123",
                "roles": [
                    {"value": "admin", "display": "Administrator", "primary": True, "type": "role"},
                    {"value": "user", "display": "User", "primary": False, "type": "role"}
                ],
                "meta": {
                    "resourceType": "User",
                    "created": "2023-01-01T00:00:00Z",
                    "lastModified": "2024-01-01T00:00:00Z",
                    "location": "/scim/v2/Users/user1"
                },
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"]
            },
            {
                "id": "user2", 
                "userName": "jane.smith@example.com",
                "name": {"givenName": "Jane", "familyName": "Smith"},
                "active": False,
                "externalId": "ext456",
                "roles": [
                    {"value": "user", "display": "User", "primary": True, "type": "role"}
                ],
                "meta": {
                    "resourceType": "User",
                    "created": "2023-02-01T00:00:00Z",
                    "lastModified": "2024-02-01T00:00:00Z",
                    "location": "/scim/v2/Users/user2"
                },
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"]
            }
        ]

    def tearDown(self):
        """Clean up after each test."""
        pass

    # region Attribute Validation Tests
    def test_validate_attributes_valid_single_attribute(self):
        """Test validation of a single valid attribute."""
        try:
            utils.validate_attributes("userName")
        except InvalidAttributeError:
            self.fail("validate_attributes raised InvalidAttributeError unexpectedly!")

    def test_validate_attributes_valid_multiple_attributes(self):
        """Test validation of multiple valid attributes."""
        try:
            utils.validate_attributes("userName,name.givenName,active")
        except InvalidAttributeError:
            self.fail("validate_attributes raised InvalidAttributeError unexpectedly!")

    def test_validate_attributes_none(self):
        """Test validation with None attributes (should pass)."""
        try:
            utils.validate_attributes(None)
        except InvalidAttributeError:
            self.fail("validate_attributes raised InvalidAttributeError unexpectedly!")

    def test_validate_attributes_empty_string(self):
        """Test validation with empty string (should pass)."""
        try:
            utils.validate_attributes("")
        except InvalidAttributeError:
            self.fail("validate_attributes raised InvalidAttributeError unexpectedly!")

    def test_validate_attributes_whitespace_only(self):
        """Test validation with whitespace-only string (should fail)."""
        with self.assertRaises(InvalidAttributeError) as context:
            utils.validate_attributes("   ")
        self.assertIn("Invalid attributes: .", str(context.exception))

    def test_validate_attributes_invalid_attribute(self):
        """Test validation with an invalid attribute."""
        with self.assertRaises(InvalidAttributeError) as context:
            utils.validate_attributes("invalidAttribute")
        self.assertIn("Invalid attributes: invalidAttribute.", str(context.exception))

    def test_validate_attributes_mixed_valid_invalid(self):
        """Test validation with mix of valid and invalid attributes."""
        with self.assertRaises(InvalidAttributeError) as context:
            utils.validate_attributes("userName,invalidAttr,active")
        self.assertIn("Invalid attributes: invalidAttr.", str(context.exception))
    # endregion

    # region Filter Tests
    def test_apply_filter_simple_eq(self):
        """Test applying a simple equals filter."""
        result = utils.apply_filter(self.sample_users, 'userName eq "john.doe@example.com"')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "user1")

    def test_apply_filter_boolean_active_true(self):
        """Test filtering by active=true."""
        result = utils.apply_filter(self.sample_users, 'active eq true')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "user1")

    def test_apply_filter_boolean_active_false(self):
        """Test filtering by active=false."""
        result = utils.apply_filter(self.sample_users, 'active eq false')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "user2")

    def test_apply_filter_contains(self):
        """Test applying a contains filter."""
        result = utils.apply_filter(self.sample_users, 'userName co "jane"')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "user2")

    def test_apply_filter_starts_with(self):
        """Test applying a starts-with filter."""
        result = utils.apply_filter(self.sample_users, 'userName sw "john"')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "user1")

    def test_apply_filter_ends_with(self):
        """Test applying an ends-with filter."""
        result = utils.apply_filter(self.sample_users, 'userName ew "@example.com"')
        self.assertEqual(len(result), 2)

    def test_apply_filter_present(self):
        """Test applying a present filter."""
        result = utils.apply_filter(self.sample_users, 'externalId pr')
        self.assertEqual(len(result), 2)

    def test_apply_filter_not_equals(self):
        """Test applying a not-equals filter."""
        result = utils.apply_filter(self.sample_users, 'active ne true')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "user2")

    def test_apply_filter_and_operation(self):
        """Test applying an AND filter operation."""
        result = utils.apply_filter(self.sample_users, 'active eq true and userName co "john"')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "user1")

    def test_apply_filter_or_operation(self):
        """Test applying an OR filter operation."""
        result = utils.apply_filter(self.sample_users, 'userName co "john" or userName co "jane"')
        self.assertEqual(len(result), 2)

    def test_apply_filter_not_operation(self):
        """Test applying a NOT filter operation."""
        result = utils.apply_filter(self.sample_users, 'not (active eq false)')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "user1")

    def test_apply_filter_parentheses_grouping(self):
        """Test applying filters with parentheses grouping."""
        result = utils.apply_filter(self.sample_users, '(userName co "john" or userName co "jane") and active eq true')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "user1")

    def test_apply_filter_nested_attributes(self):
        """Test filtering on nested attributes."""
        result = utils.apply_filter(self.sample_users, 'name.givenName eq "John"')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "user1")

    def test_apply_filter_roles_value(self):
        """Test filtering on roles.value."""
        result = utils.apply_filter(self.sample_users, 'roles.value eq "admin"')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "user1")

    def test_apply_filter_meta_created_gt(self):
        """Test filtering on meta.created with greater than."""
        result = utils.apply_filter(self.sample_users, 'meta.created gt "2023-01-15T00:00:00Z"')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "user2")

    def test_apply_filter_invalid_expression(self):
        """Test applying an invalid filter expression."""
        with self.assertRaises(ValueError) as context:
            utils.apply_filter(self.sample_users, 'invalid filter')
        self.assertIn("Invalid filter expression", str(context.exception))

    def test_apply_filter_invalid_attribute(self):
        """Test filtering with an invalid attribute."""
        with self.assertRaises(ValueError) as context:
            utils.apply_filter(self.sample_users, 'invalidAttr eq "value"')
        self.assertIn("Unsupported filter attribute", str(context.exception))

    def test_apply_filter_invalid_operator(self):
        """Test filtering with an invalid operator."""
        with self.assertRaises(ValueError) as context:
            utils.apply_filter(self.sample_users, 'userName invalidOp "value"')
        self.assertIn("Unsupported filter operator", str(context.exception))
    # endregion

    # region Sorting Tests
    def test_apply_sorting_by_id_ascending(self):
        """Test sorting by id in ascending order."""
        result = utils.apply_sorting(self.sample_users, "id", "ascending")
        self.assertEqual(result[0]["id"], "user1")
        self.assertEqual(result[1]["id"], "user2")

    def test_apply_sorting_by_id_descending(self):
        """Test sorting by id in descending order."""
        result = utils.apply_sorting(self.sample_users, "id", "descending")
        self.assertEqual(result[0]["id"], "user2")
        self.assertEqual(result[1]["id"], "user1")

    def test_apply_sorting_by_external_id(self):
        """Test sorting by externalId."""
        result = utils.apply_sorting(self.sample_users, "externalId", "ascending")
        self.assertEqual(result[0]["externalId"], "ext123")
        self.assertEqual(result[1]["externalId"], "ext456")

    def test_apply_sorting_unsupported_field(self):
        """Test sorting by unsupported field (should return original list)."""
        original_order = [user["id"] for user in self.sample_users]
        result = utils.apply_sorting(self.sample_users, "unsupportedField", "ascending")
        result_order = [user["id"] for user in result]
        self.assertEqual(original_order, result_order)
    # endregion

    # region Attribute Filtering Tests
    def test_filter_attributes_single_attribute(self):
        """Test filtering to return single attribute."""
        result = utils.filter_attributes(self.sample_users, "userName")
        self.assertEqual(len(result), 2)
        for user in result:
            self.assertIn("userName", user)
            self.assertIn("schemas", user)  # Always included
            self.assertIn("id", user)       # Always included
            self.assertNotIn("active", user)

    def test_filter_attributes_multiple_attributes(self):
        """Test filtering to return multiple attributes."""
        result = utils.filter_attributes(self.sample_users, "userName,active")
        self.assertEqual(len(result), 2)
        for user in result:
            self.assertIn("userName", user)
            self.assertIn("active", user)
            self.assertIn("schemas", user)
            self.assertIn("id", user)
            self.assertNotIn("externalId", user)

    def test_filter_attributes_nested_name(self):
        """Test filtering nested name attributes."""
        result = utils.filter_attributes(self.sample_users, "name.givenName")
        self.assertEqual(len(result), 2)
        for user in result:
            self.assertIn("name", user)
            self.assertIn("givenName", user["name"])
            self.assertNotIn("familyName", user["name"])

    def test_filter_attributes_roles_sub_attribute(self):
        """Test filtering roles sub-attributes."""
        result = utils.filter_attributes(self.sample_users, "roles.value")
        self.assertEqual(len(result), 2)
        for user in result:
            self.assertIn("roles", user)
            for role in user["roles"]:
                self.assertIn("value", role)
                self.assertNotIn("display", role)

    def test_filter_attributes_meta_sub_attribute(self):
        """Test filtering meta sub-attributes."""
        result = utils.filter_attributes(self.sample_users, "meta.created")
        self.assertEqual(len(result), 2)
        for user in result:
            self.assertIn("meta", user)
            self.assertIn("created", user["meta"])
            self.assertNotIn("lastModified", user["meta"])
    # endregion

    # region Helper Function Tests
    def test_is_iso_datetime_valid_formats(self):
        """Test is_iso_datetime with valid formats."""
        valid_dates = [
            "2023-01-01T00:00:00Z",
            "2023-12-31T23:59:59",
            "2023-01-01T12:30:45+05:00"
        ]
        for date_str in valid_dates:
            self.assertTrue(utils.is_iso_datetime(date_str))

    def test_is_iso_datetime_invalid_formats(self):
        """Test is_iso_datetime with invalid formats."""
        invalid_dates = [
            "2023-01-01",
            "not a date",
            "2023/01/01 12:00:00",
            None,
            123,
            ""
        ]
        for date_str in invalid_dates:
            self.assertFalse(utils.is_iso_datetime(date_str))

    def test_get_user_attribute_value_simple_attributes(self):
        """Test getting simple user attributes."""
        user = self.sample_users[0]
        
        self.assertEqual(utils.get_user_attribute_value(user, "userName"), "john.doe@example.com")
        self.assertEqual(utils.get_user_attribute_value(user, "active"), True)
        self.assertEqual(utils.get_user_attribute_value(user, "id"), "user1")
        self.assertEqual(utils.get_user_attribute_value(user, "externalId"), "ext123")

    def test_get_user_attribute_value_nested_attributes(self):
        """Test getting nested user attributes."""
        user = self.sample_users[0]
        
        self.assertEqual(utils.get_user_attribute_value(user, "name.givenName"), "John")
        self.assertEqual(utils.get_user_attribute_value(user, "name.familyName"), "Doe")
        self.assertEqual(utils.get_user_attribute_value(user, "meta.created"), "2023-01-01T00:00:00Z")
        self.assertEqual(utils.get_user_attribute_value(user, "meta.resourceType"), "User")

    def test_get_user_attribute_value_roles(self):
        """Test getting roles attributes."""
        user = self.sample_users[0]
        
        roles_values = utils.get_user_attribute_value(user, "roles.value")
        self.assertEqual(roles_values, ["admin", "user"])
        
        roles_display = utils.get_user_attribute_value(user, "roles.display")
        self.assertEqual(roles_display, ["Administrator", "User"])

    def test_get_user_attribute_value_nonexistent(self):
        """Test getting non-existent attributes."""
        user = self.sample_users[0]
        
        self.assertIsNone(utils.get_user_attribute_value(user, "nonexistent"))
        self.assertIsNone(utils.get_user_attribute_value(user, "name.nonexistent"))

    def test_compare_values_numeric(self):
        """Test numeric value comparison."""
        self.assertTrue(utils.compare_values(10, "5", "gt"))
        self.assertTrue(utils.compare_values(10, "10", "ge"))
        self.assertTrue(utils.compare_values(5, "10", "lt"))
        self.assertTrue(utils.compare_values(10, "10", "le"))
        self.assertFalse(utils.compare_values(5, "10", "gt"))

    def test_compare_values_datetime(self):
        """Test datetime value comparison."""
        self.assertTrue(utils.compare_values("2023-02-01T00:00:00Z", "2023-01-01T00:00:00Z", "gt"))
        self.assertTrue(utils.compare_values("2023-01-01T00:00:00Z", "2023-01-01T00:00:00Z", "ge"))
        self.assertTrue(utils.compare_values("2023-01-01T00:00:00Z", "2023-02-01T00:00:00Z", "lt"))
        self.assertTrue(utils.compare_values("2023-01-01T00:00:00Z", "2023-01-01T00:00:00Z", "le"))

    def test_compare_values_string_lexicographical(self):
        """Test string lexicographical comparison."""
        self.assertTrue(utils.compare_values("zebra", "apple", "gt"))
        self.assertTrue(utils.compare_values("apple", "apple", "ge"))
        self.assertTrue(utils.compare_values("apple", "zebra", "lt"))
        self.assertTrue(utils.compare_values("apple", "apple", "le"))
    # endregion

    # region PATCH Operation Tests  
    def test_apply_patch_operation_replace_simple(self):
        """Test applying a simple replace patch operation."""
        user = self.sample_users[0].copy()
        
        class MockOperation:
            def __init__(self, op, path, value):
                self.op = op
                self.path = path
                self.value = value
        
        operation = MockOperation("replace", "externalId", "new_ext_123")
        result = utils.apply_patch_operation(user, operation, "user1")
        
        self.assertEqual(result["externalId"], "new_ext_123")

    def test_apply_patch_operation_replace_nested(self):
        """Test applying a nested replace patch operation."""
        user = self.sample_users[0].copy()
        
        class MockOperation:
            def __init__(self, op, path, value):
                self.op = op
                self.path = path
                self.value = value
        
        operation = MockOperation("replace", "name.givenName", "Johnny")
        result = utils.apply_patch_operation(user, operation, "user1")
        
        self.assertEqual(result["name"]["givenName"], "Johnny")

    def test_apply_patch_operation_add_roles(self):
        """Test applying an add patch operation for roles."""
        user = self.sample_users[0].copy()
        
        class MockOperation:
            def __init__(self, op, path, value):
                self.op = op
                self.path = path
                self.value = value
        
        new_role = {"value": "manager", "display": "Manager", "primary": False, "type": "role"}
        operation = MockOperation("add", "roles", new_role)
        result = utils.apply_patch_operation(user, operation, "user1")
        
        self.assertEqual(len(result["roles"]), 3)
        self.assertEqual(result["roles"][-1]["value"], "manager")

    def test_apply_patch_operation_remove(self):
        """Test applying a remove patch operation."""
        user = self.sample_users[0].copy()
        
        class MockOperation:
            def __init__(self, op, path, value):
                self.op = op
                self.path = path
                self.value = value
        
        operation = MockOperation("remove", "externalId", None)
        result = utils.apply_patch_operation(user, operation, "user1")
        
        self.assertNotIn("externalId", result)

    def test_apply_patch_operation_forbidden_self_deactivation(self):
        """Test that self-deactivation is forbidden."""
        user = self.sample_users[0].copy()
        
        class MockOperation:
            def __init__(self, op, path, value):
                self.op = op
                self.path = path
                self.value = value
        
        operation = MockOperation("replace", "active", False)
        
        self.assert_error_behavior(
            lambda: utils.apply_patch_operation(user, operation, "user1"),
            UserPatchForbiddenError,
            "Self-deactivation is forbidden"
        )

    def test_apply_patch_operation_forbidden_domain_change(self):
        """Test that email domain change is forbidden."""
        user = self.sample_users[0].copy()
        
        class MockOperation:
            def __init__(self, op, path, value):
                self.op = op
                self.path = path
                self.value = value
        
        operation = MockOperation("replace", "userName", "john.doe@different.com")
        
        self.assert_error_behavior(
            lambda: utils.apply_patch_operation(user, operation, "user1"),
            UserPatchForbiddenError,
            "Email domain change is forbidden by SSO policy"
        )

    def test_apply_patch_operation_protected_immutable_fields(self):
        """Test that immutable fields are protected from modification."""
        user = self.sample_users[0].copy()
        original_id = user["id"]
        
        class MockOperation:
            def __init__(self, op, path, value):
                self.op = op
                self.path = path
                self.value = value
        
        operation = MockOperation("replace", "id", "new_id")
        result = utils.apply_patch_operation(user, operation, "user1")
        
        # ID should remain unchanged
        self.assertEqual(result["id"], original_id)
    # endregion


if __name__ == "__main__":
    unittest.main()
