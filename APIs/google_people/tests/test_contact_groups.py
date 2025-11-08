import unittest
from datetime import datetime
import json
import os

from common_utils.base_case import BaseTestCaseWithErrorHandler
from .common import reset_db
from .. import (create_contact_group, delete_contact_group, get_contact_group, list_contact_groups, modify_contact_group_members, update_contact_group)

class TestContactGroupsAPI(BaseTestCaseWithErrorHandler):
    """Test class for Google People Contact Groups API functions."""

    def setUp(self):
        """Set up test database with sample data."""
        reset_db()
        from ..SimulationEngine.db import DB
        
        # Initialize test data
        DB.set("contactGroups", {
            "contactGroups/family": {
                "resourceName": "contactGroups/family",
                "etag": "etag_family_group",
                "name": "Family",
                "groupType": "USER_CONTACT_GROUP",
                "memberResourceNames": ["people/123456789", "people/987654321"],
                "memberCount": 2,
                "created": "2023-01-20T08:00:00Z",
                "updated": "2024-01-10T16:30:00Z"
            },
            "contactGroups/work": {
                "resourceName": "contactGroups/work",
                "etag": "etag_work_group",
                "name": "Work Team",
                "groupType": "USER_CONTACT_GROUP",
                "memberResourceNames": ["people/123456789"],
                "memberCount": 1,
                "created": "2023-02-15T09:00:00Z",
                "updated": "2024-01-12T14:20:00Z"
            }
        })

        DB.set("people", {
            "people/123456789": {
                "resourceName": "people/123456789",
                "names": [{"displayName": "John Doe"}]
            },
            "people/987654321": {
                "resourceName": "people/987654321",
                "names": [{"displayName": "Jane Smith"}]
            },
            "people/555666777": {
                "resourceName": "people/555666777",
                "names": [{"displayName": "Bob Wilson"}]
            }
        })

    def tearDown(self):
        """Clean up after tests."""
        reset_db()

    def test_get_contact_group_success(self):
        """Test successful retrieval of a contact group."""
        result = get_contact_group("contactGroups/family")
        
        self.assertEqual(result["resourceName"], "contactGroups/family")
        self.assertEqual(result["etag"], "etag_family_group")
        self.assertEqual(result["name"], "Family")
        self.assertEqual(result["memberCount"], 2)

    def test_get_contact_group_with_max_members(self):
        """Test contact group retrieval with max members limit."""
        result = get_contact_group("contactGroups/family", max_members=1)
        
        self.assertEqual(len(result["memberResourceNames"]), 1)

    def test_get_contact_group_with_fields_filter(self):
        """Test contact group retrieval with field filtering."""
        result = get_contact_group("contactGroups/family", group_fields="name,memberCount")
        
        self.assertIn("name", result)
        self.assertIn("memberCount", result)
        self.assertNotIn("memberResourceNames", result)
        self.assertNotIn("groupType", result)

    def test_get_contact_group_not_found(self):
        """Test contact group retrieval when group doesn't exist."""
        self.assert_error_behavior(
            func_to_call=get_contact_group,
            expected_exception_type=ValueError,
            expected_message="Contact group with resource name 'contactGroups/nonexistent' not found",
            resource_name="contactGroups/nonexistent"
        )

    def test_create_contact_group_success(self):
        """Test successful contact group creation."""
        group_data = {
            "name": "New Group",
            "groupType": "USER_CONTACT_GROUP",
            "memberResourceNames": ["people/123456789"]
        }
        
        result = create_contact_group(group_data)
        
        self.assertIn("resourceName", result)
        self.assertIn("etag", result)
        self.assertEqual(result["name"], "New Group")
        self.assertEqual(result["memberCount"], 1)

    def test_create_contact_group_with_existing_data(self):
        """Test contact group creation with existing database data."""
        group_data = {
            "name": "Another Group",
            "memberResourceNames": ["people/123456789", "people/987654321"]
        }
        
        result = create_contact_group(group_data)
        
        self.assertIn("resourceName", result)
        self.assertIn("etag", result)
        self.assertEqual(result["name"], "Another Group")
        self.assertEqual(result["memberCount"], 2)

    def test_update_contact_group_success(self):
        """Test successful contact group update."""
        update_data = {
            "name": "Updated Family",
            "memberResourceNames": ["people/123456789", "people/987654321", "people/555666777"]
        }
        
        result = update_contact_group("contactGroups/family", update_data)
        
        self.assertEqual(result["resourceName"], "contactGroups/family")
        self.assertEqual(result["name"], "Updated Family")
        self.assertEqual(result["memberCount"], 3)

    def test_update_contact_group_with_field_filter(self):
        """Test contact group update with specific field filtering."""
        update_data = {
            "name": "Updated Family",
            "memberResourceNames": ["people/123456789", "people/987654321", "people/555666777"]
        }
        
        result = update_contact_group("contactGroups/family", update_data, "name")
        
        self.assertEqual(result["name"], "Updated Family")
        # Should not update memberResourceNames since it's not in the field filter
        self.assertEqual(result["memberCount"], 3)

    def test_update_contact_group_not_found(self):
        """Test contact group update when group doesn't exist."""
        update_data = {"name": "Updated Name"}
        
        self.assert_error_behavior(
            func_to_call=update_contact_group,
            expected_exception_type=ValueError,
            expected_message="Contact group with resource name 'contactGroups/nonexistent' not found",
            resource_name="contactGroups/nonexistent",
            contact_group_data=update_data
        )

    def test_delete_contact_group_success(self):
        """Test successful contact group deletion."""
        result = delete_contact_group("contactGroups/work")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["deletedResourceName"], "contactGroups/work")
        self.assertEqual(result["message"], "Contact group deleted successfully")

    def test_delete_contact_group_with_contacts(self):
        """Test contact group deletion with delete_contacts=True."""
        result = delete_contact_group("contactGroups/family", delete_contacts=True)
        
        self.assertTrue(result["success"])
        self.assertEqual(result["deletedResourceName"], "contactGroups/family")
        self.assertEqual(result["message"], "Contact group deleted successfully")

    def test_delete_contact_group_not_found(self):
        """Test contact group deletion when group doesn't exist."""
        self.assert_error_behavior(
            func_to_call=delete_contact_group,
            expected_exception_type=ValueError,
            expected_message="Contact group with resource name 'contactGroups/nonexistent' not found",
            resource_name="contactGroups/nonexistent"
        )

    def test_list_contact_groups_success(self):
        """Test successful listing of contact groups."""
        result = list_contact_groups()
        
        self.assertIn("contactGroups", result)
        self.assertIn("totalItems", result)
        self.assertEqual(len(result["contactGroups"]), 2)

    def test_list_contact_groups_with_pagination(self):
        """Test listing contact groups with pagination."""
        result = list_contact_groups(page_size=1)
        
        self.assertEqual(len(result["contactGroups"]), 1)
        self.assertIn("nextPageToken", result)

    def test_list_contact_groups_with_fields_filter(self):
        """Test listing contact groups with field filtering."""
        result = list_contact_groups(group_fields="name,memberCount")
        
        for group in result["contactGroups"]:
            self.assertIn("name", group)
            self.assertIn("memberCount", group)
            self.assertNotIn("memberResourceNames", group)

    def test_list_contact_groups_with_page_token(self):
        """Test listing contact groups with page token."""
        result = list_contact_groups(page_token="1", page_size=1)
        
        self.assertEqual(len(result["contactGroups"]), 1)

    def test_list_contact_groups_with_sync_token(self):
        """Test listing contact groups with sync token."""
        result = list_contact_groups(sync_token="sync_123")
        
        self.assertIn("contactGroups", result)
        self.assertIn("totalItems", result)

    def test_modify_members_add_success(self):
        """Test successful addition of members to contact group."""
        request_data = {
            "resourceNamesToAdd": ["people/555666777"]
        }
        result = modify_contact_group_members("contactGroups/family", request_data)
        
        self.assertEqual(result["resourceName"], "contactGroups/family")
        self.assertEqual(result["memberCount"], 3)
        self.assertIn("etag", result)
        self.assertEqual(result["notFoundResourceNames"], [])

    def test_modify_members_remove_success(self):
        """Test successful removal of members from contact group."""
        request_data = {
            "resourceNamesToRemove": ["people/987654321"]
        }
        result = modify_contact_group_members("contactGroups/family", request_data)
        
        self.assertEqual(result["resourceName"], "contactGroups/family")
        self.assertEqual(result["memberCount"], 1)
        self.assertIn("etag", result)
        self.assertEqual(result["notFoundResourceNames"], [])

    def test_modify_members_add_and_remove_success(self):
        """Test successful addition and removal of members."""
        request_data = {
            "resourceNamesToAdd": ["people/555666777"],
            "resourceNamesToRemove": ["people/987654321"]
        }
        result = modify_contact_group_members("contactGroups/family", request_data)
        
        self.assertEqual(result["resourceName"], "contactGroups/family")
        self.assertEqual(result["memberCount"], 2)
        self.assertIn("etag", result)
        self.assertEqual(result["notFoundResourceNames"], [])

    def test_modify_members_add_nonexistent_contact(self):
        """Test adding nonexistent contact to group."""
        request_data = {
            "resourceNamesToAdd": ["people/nonexistent"]
        }
        result = modify_contact_group_members("contactGroups/family", request_data)
        
        self.assertEqual(result["resourceName"], "contactGroups/family")
        self.assertEqual(result["memberCount"], 2)  # Should not change
        self.assertIn("etag", result)
        self.assertIn("people/nonexistent", result["notFoundResourceNames"])

    def test_modify_members_group_not_found(self):
        """Test modifying members of nonexistent group."""
        request_data = {
            "resourceNamesToAdd": ["people/123456789"]
        }
        self.assert_error_behavior(
            func_to_call=modify_contact_group_members,
            expected_exception_type=ValueError,
            expected_message="Contact group with resource name 'contactGroups/nonexistent' not found",
            resource_name="contactGroups/nonexistent",
            request_data=request_data
        )

    def test_modify_members_duplicate_addition(self):
        """Test adding duplicate member to group."""
        request_data = {
            "resourceNamesToAdd": ["people/123456789"]  # Already in group
        }
        result = modify_contact_group_members("contactGroups/family", request_data)
        
        self.assertEqual(result["resourceName"], "contactGroups/family")
        self.assertEqual(result["memberCount"], 2)  # Should not change
        self.assertIn("etag", result)
        self.assertEqual(result["notFoundResourceNames"], [])

    def test_modify_members_remove_nonexistent_member(self):
        """Test removing nonexistent member from group."""
        request_data = {
            "resourceNamesToRemove": ["people/nonexistent"]
        }
        result = modify_contact_group_members("contactGroups/family", request_data)
        
        self.assertEqual(result["resourceName"], "contactGroups/family")
        self.assertEqual(result["memberCount"], 2)  # Should not change
        self.assertIn("etag", result)
        self.assertEqual(result["notFoundResourceNames"], [])

    def test_modify_members_empty_request(self):
        """Test modifying members with empty request."""
        request_data = {}
        result = modify_contact_group_members("contactGroups/family", request_data)
        
        self.assertEqual(result["resourceName"], "contactGroups/family")
        self.assertEqual(result["memberCount"], 2)  # Should not change
        self.assertIn("etag", result)
        self.assertEqual(result["notFoundResourceNames"], [])


if __name__ == '__main__':
    unittest.main() 