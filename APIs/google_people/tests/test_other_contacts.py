import unittest
from datetime import datetime
import json
import os

from pydantic import ValidationError

from common_utils.base_case import BaseTestCaseWithErrorHandler
from .common import reset_db
from .. import (get_other_contact, list_other_contacts, search_other_contacts)

class TestOtherContactsAPI(BaseTestCaseWithErrorHandler):
    """Test class for Google People Other Contacts API functions."""

    def setUp(self):
        """Set up test database with sample data."""
        reset_db()
        from ..SimulationEngine.db import DB
        
        # Initialize test data
        DB.set("otherContacts", {
            "otherContacts/111222333": {
                "resourceName": "otherContacts/111222333",
                "etag": "etag_other_111222333",
                "names": [{"displayName": "Alice Johnson", "givenName": "Alice", "familyName": "Johnson"}],
                "emailAddresses": [{"value": "alice.johnson@external.com", "type": "work"}],
                "phoneNumbers": [{"value": "+1-555-111-2222", "type": "mobile"}],
                "addresses": [{"formattedValue": "456 Oak St, City, State"}],
                "organizations": [{"name": "External Corp", "title": "Manager"}],
                "created": "2023-04-15T10:30:00Z",
                "updated": "2024-01-15T14:20:00Z"
            },
            "otherContacts/444555666": {
                "resourceName": "otherContacts/444555666",
                "etag": "etag_other_444555666",
                "names": [{"displayName": "Charlie Brown", "givenName": "Charlie", "familyName": "Brown"}],
                "emailAddresses": [{"value": "charlie.brown@external.com", "type": "personal"}],
                "phoneNumbers": [{"value": "+1-555-444-5555", "type": "home"}],
                "organizations": [{"name": "Another Company", "title": "Developer"}],
                "created": "2023-05-20T11:00:00Z",
                "updated": "2024-01-10T09:15:00Z"
            },
            "otherContacts/777888999": {
                "resourceName": "otherContacts/777888999",
                "etag": "etag_other_777888999",
                "names": [{"displayName": "David Wilson", "givenName": "David", "familyName": "Wilson"}],
                "emailAddresses": [{"value": "david.wilson@external.com", "type": "work"}],
                "organizations": [{"name": "Tech Solutions", "title": "Senior Developer"}],
                "created": "2023-06-10T08:00:00Z",
                "updated": "2024-01-05T16:30:00Z"
            }
        })

    def tearDown(self):
        """Clean up after tests."""
        reset_db()

    def test_get_other_contact_success(self):
        """Test successful retrieval of an other contact."""
        result = get_other_contact("otherContacts/111222333")
        
        self.assertEqual(result["resourceName"], "otherContacts/111222333")
        self.assertEqual(result["etag"], "etag_other_111222333")
        self.assertEqual(len(result["names"]), 1)
        self.assertEqual(result["names"][0]["displayName"], "Alice Johnson")

    def test_get_other_contact_with_read_mask(self):
        """Test other contact retrieval with read mask filtering."""
        result = get_other_contact("otherContacts/111222333", read_mask="names,emailAddresses")
        
        self.assertIn("names", result)
        self.assertIn("emailAddresses", result)
        self.assertNotIn("phoneNumbers", result)
        self.assertNotIn("addresses", result)

    def test_get_other_contact_not_found(self):
        """Test other contact retrieval when contact doesn't exist."""
        self.assert_error_behavior(
            func_to_call=get_other_contact,
            expected_exception_type=ValueError,
            expected_message="Other contact with resource name 'otherContacts/nonexistent' not found",
            resource_name="otherContacts/nonexistent"
        )

    def test_get_other_contact_invalid_resource_name(self):
        """Test other contact retrieval with invalid resource name."""
        self.assert_error_behavior(
            func_to_call=get_other_contact,
            expected_exception_type=ValidationError,
            expected_message='Resource name must start with "otherContacts/"',
            resource_name="invalid_name"
        )

    def test_list_other_contacts_success(self):
        """Test successful listing of other contacts."""
        result = list_other_contacts(read_mask="names,emailAddresses")
        
        self.assertIn("otherContacts", result)
        self.assertIn("totalItems", result)
        self.assertEqual(len(result["otherContacts"]), 3)

    def test_list_other_contacts_without_read_mask(self):
        """Test listing other contacts without required read_mask."""
        self.assert_error_behavior(
            func_to_call=list_other_contacts,
            expected_exception_type=ValueError,
            expected_message="read_mask is required for list_other_contacts"
        )

    def test_list_other_contacts_with_pagination(self):
        """Test listing other contacts with pagination."""
        result = list_other_contacts(read_mask="names", page_size=2)
        
        self.assertEqual(len(result["otherContacts"]), 2)
        self.assertIn("nextPageToken", result)

    def test_list_other_contacts_with_page_token(self):
        """Test listing other contacts with page token."""
        result = list_other_contacts(read_mask="names", page_token="2", page_size=1)
        
        self.assertEqual(len(result["otherContacts"]), 1)

    def test_list_other_contacts_with_sync_token(self):
        """Test listing other contacts with sync token."""
        result = list_other_contacts(read_mask="names", sync_token="sync_123")
        
        self.assertIn("otherContacts", result)
        self.assertIn("totalItems", result)

    def test_list_other_contacts_with_request_sync_token(self):
        """Test listing other contacts with request sync token."""
        result = list_other_contacts(read_mask="names", request_sync_token=True)
        
        self.assertIn("otherContacts", result)
        self.assertIn("nextSyncToken", result)

    def test_list_other_contacts_with_fields_filter(self):
        """Test listing other contacts with field filtering."""
        result = list_other_contacts(read_mask="names,emailAddresses")
        
        for contact in result["otherContacts"]:
            self.assertIn("names", contact)
            self.assertIn("emailAddresses", contact)
            self.assertNotIn("phoneNumbers", contact)

    def test_search_other_contacts_success(self):
        """Test successful search of other contacts."""
        result = search_other_contacts("alice", read_mask="names,emailAddresses")
        
        self.assertIn("results", result)
        self.assertIn("totalItems", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["names"][0]["givenName"], "Alice")

    def test_search_other_contacts_without_read_mask(self):
        """Test searching other contacts without required read_mask."""
        self.assert_error_behavior(
            func_to_call=search_other_contacts,
            expected_exception_type=ValueError,
            expected_message="read_mask is required for search_other_contacts",
            query="alice"
        )

    def test_search_other_contacts_by_email(self):
        """Test searching other contacts by email address."""
        result = search_other_contacts("alice.johnson@external.com", read_mask="names,emailAddresses")
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["emailAddresses"][0]["value"], "alice.johnson@external.com")

    def test_search_other_contacts_by_organization(self):
        """Test searching other contacts by organization."""
        result = search_other_contacts("External Corp", read_mask="names,organizations")
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["organizations"][0]["name"], "External Corp")

    def test_search_other_contacts_by_family_name(self):
        """Test searching other contacts by family name."""
        result = search_other_contacts("Johnson", read_mask="names")
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["names"][0]["familyName"], "Johnson")

    def test_search_other_contacts_by_display_name(self):
        """Test searching other contacts by display name."""
        result = search_other_contacts("Charlie Brown", read_mask="names")
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["names"][0]["displayName"], "Charlie Brown")

    def test_search_other_contacts_with_pagination(self):
        """Test searching other contacts with pagination."""
        result = search_other_contacts("external", read_mask="names", page_size=2)
        
        self.assertEqual(len(result["results"]), 2)
        self.assertIn("nextPageToken", result)

    def test_search_other_contacts_with_page_token(self):
        """Test searching other contacts with page token."""
        result = search_other_contacts("external", read_mask="names", page_token="2", page_size=1)
        
        self.assertEqual(len(result["results"]), 1)

    def test_search_other_contacts_no_results(self):
        """Test searching other contacts with no matching results."""
        result = search_other_contacts("nonexistent", read_mask="names")
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 0)
        self.assertEqual(result["totalItems"], 0)

    def test_search_other_contacts_case_insensitive(self):
        """Test searching other contacts with case-insensitive matching."""
        result = search_other_contacts("ALICE", read_mask="names")
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["names"][0]["givenName"], "Alice")

    def test_search_other_contacts_partial_match(self):
        """Test searching other contacts with partial matching."""
        result = search_other_contacts("al", read_mask="names")
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 3)
        self.assertEqual(result["results"][0]["names"][0]["givenName"], "Alice")

    def test_search_other_contacts_multiple_matches(self):
        """Test searching other contacts with multiple matches."""
        result = search_other_contacts("external", read_mask="names")
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 3)  # alice and david both have external emails

    def test_search_other_contacts_duplicate_removal(self):
        """Test searching other contacts with duplicate removal."""
        # Add a duplicate contact for testing
        from ..SimulationEngine.db import DB
        DB.set("otherContacts", {
            **DB.get("otherContacts", {}),
            "otherContacts/999888777": {
                "resourceName": "otherContacts/999888777",
                "etag": "etag_other_999888777",
                "names": [{"displayName": "Alice Johnson", "givenName": "Alice", "familyName": "Johnson"}],
                "emailAddresses": [{"value": "alice.johnson@external.com", "type": "work"}],
                "created": "2023-07-15T10:30:00Z",
                "updated": "2024-01-15T14:20:00Z"
            }
        })
        
        result = search_other_contacts("alice", read_mask="names")
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 2)  # Should remove duplicates

    def test_search_other_contacts_with_fields_filter(self):
        """Test searching other contacts with field filtering."""
        result = search_other_contacts("alice", read_mask="names,emailAddresses")
        
        for contact in result["results"]:
            self.assertIn("names", contact)
            self.assertIn("emailAddresses", contact)
            self.assertNotIn("phoneNumbers", contact)

    def test_search_other_contacts_empty_query(self):
        """Test searching other contacts with empty query."""
        self.assert_error_behavior(
            func_to_call=search_other_contacts,
            expected_exception_type=ValidationError,
            expected_message="String should have at least 1 character",
            query="",
            read_mask="names"
        )

    def test_search_other_contacts_special_characters(self):
        """Test searching other contacts with special characters."""
        result = search_other_contacts("alice.johnson@external.com", read_mask="names,emailAddresses")
        
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["emailAddresses"][0]["value"], "alice.johnson@external.com")


if __name__ == '__main__':
    unittest.main() 