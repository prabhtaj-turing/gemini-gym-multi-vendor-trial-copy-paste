import unittest
import sys
import os
import tempfile
import json
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from common_utils.base_case import BaseTestCaseWithErrorHandler
from contacts.SimulationEngine.db import DB, save_state, load_state
from contacts.SimulationEngine import utils

class TestUtilities(BaseTestCaseWithErrorHandler):
    """
    Test suite for utility functions in the contacts API.
    """

    def setUp(self):
        """
        Set up test data for utility function tests.
        """
        # Add test contacts to different collections
        DB["myContacts"]["people/c12345"] = {
            "resourceName": "people/c12345",
            "etag": "etag123",
            "names": [{"givenName": "John", "familyName": "Doe"}],
            "emailAddresses": [{"value": "john.doe@example.com", "type": "work"}]
        }
        
        DB["otherContacts"]["otherContacts/c67890"] = {
            "resourceName": "otherContacts/c67890",
            "etag": "etag456",
            "names": [{"givenName": "Jane", "familyName": "Smith"}],
            "emailAddresses": [{"value": "jane.smith@example.com", "type": "home"}]
        }
        
        DB["directory"]["people/d11111"] = {
            "resourceName": "people/d11111",
            "etag": "etag789",
            "names": [{"givenName": "Alice", "familyName": "Johnson"}],
            "emailAddresses": [{"value": "alice.johnson@company.com", "type": "work"}]
        }

    def test_find_contact_by_id_in_my_contacts(self):
        """
        Test finding a contact by ID in myContacts collection.
        """
        contact = utils.find_contact_by_id("people/c12345")
        self.assertIsNotNone(contact)
        self.assertEqual(contact["resourceName"], "people/c12345")
        self.assertEqual(contact["names"][0]["givenName"], "John")

    def test_find_contact_by_id_in_other_contacts(self):
        """
        Test finding a contact by ID in otherContacts collection.
        """
        contact = utils.find_contact_by_id("otherContacts/c67890")
        self.assertIsNotNone(contact)
        self.assertEqual(contact["resourceName"], "otherContacts/c67890")
        self.assertEqual(contact["names"][0]["givenName"], "Jane")

    def test_find_contact_by_id_in_directory(self):
        """
        Test finding a contact by ID in directory collection.
        """
        contact = utils.find_contact_by_id("people/d11111")
        self.assertIsNotNone(contact)
        self.assertEqual(contact["resourceName"], "people/d11111")
        self.assertEqual(contact["names"][0]["givenName"], "Alice")

    def test_find_contact_by_id_not_found(self):
        """
        Test finding a contact by ID that doesn't exist.
        """
        contact = utils.find_contact_by_id("people/nonexistent")
        self.assertIsNone(contact)

    def test_find_contact_by_email_in_my_contacts(self):
        """
        Test finding a contact by email in myContacts collection.
        """
        contact = utils.find_contact_by_email("john.doe@example.com")
        self.assertIsNotNone(contact)
        self.assertIn("resourceName", contact)
        self.assertEqual(contact["names"][0]["givenName"], "John")

    def test_find_contact_by_email_in_other_contacts(self):
        """
        Test finding a contact by email in otherContacts collection.
        """
        contact = utils.find_contact_by_email("jane.smith@example.com")
        self.assertIsNotNone(contact)
        self.assertIn("resourceName", contact)
        self.assertEqual(contact["names"][0]["givenName"], "Jane")

    def test_find_contact_by_email_in_directory(self):
        """
        Test finding a contact by email in directory collection.
        """
        contact = utils.find_contact_by_email("alice.johnson@company.com")
        self.assertIsNotNone(contact)
        self.assertEqual(contact["resourceName"], "people/d11111")
        self.assertEqual(contact["names"][0]["givenName"], "Alice")

    def test_find_contact_by_email_case_insensitive(self):
        """
        Test finding a contact by email with case insensitive matching.
        """
        contact = utils.find_contact_by_email("JOHN.DOE@EXAMPLE.COM")
        self.assertIsNotNone(contact)
        self.assertIn("resourceName", contact)

    def test_find_contact_by_email_not_found(self):
        """
        Test finding a contact by email that doesn't exist.
        """
        contact = utils.find_contact_by_email("nonexistent@example.com")
        self.assertIsNone(contact)

    def test_find_contact_by_email_no_email_addresses(self):
        """
        Test finding a contact by email when contact has no email addresses.
        """
        # Add a contact without email addresses
        DB["myContacts"]["people/noemail"] = {
            "resourceName": "people/noemail",
            "etag": "etag999",
            "names": [{"givenName": "NoEmail", "familyName": "Contact"}]
        }
        
        contact = utils.find_contact_by_email("john.doe@example.com")
        self.assertIsNotNone(contact)
        self.assertIn("resourceName", contact)

    def test_generate_resource_name_default_prefix(self):
        """
        Test generating resource name with default prefix.
        """
        resource_name = utils.generate_resource_name()
        self.assertTrue(resource_name.startswith("people/c"))
        self.assertGreater(len(resource_name), len("people/c"))

    def test_generate_resource_name_custom_prefix(self):
        """
        Test generating resource name with custom prefix.
        """
        resource_name = utils.generate_resource_name("custom")
        self.assertTrue(resource_name.startswith("custom"))
        self.assertGreater(len(resource_name), len("custom"))

    def test_generate_resource_name_unique(self):
        """
        Test that generated resource names are unique.
        """
        names = set()
        for _ in range(100):
            name = utils.generate_resource_name()
            self.assertNotIn(name, names)
            names.add(name)

    def test_search_collection_with_name_query(self):
        """
        Test searching collection by name.
        """
        results = utils.search_collection("myContacts", "John", 10)
        self.assertGreater(len(results), 0)
        # Find the contact with the exact name "John"
        john_contact = None
        for contact in results:
            if contact["names"][0]["givenName"] == "John":
                john_contact = contact
                break
        self.assertIsNotNone(john_contact)

    def test_search_collection_with_email_query(self):
        """
        Test searching collection by email.
        """
        results = utils.search_collection("myContacts", "john.doe@example.com", 10)
        self.assertGreater(len(results), 0)
        # Find the contact with the exact email
        email_contact = None
        for contact in results:
            if "emailAddresses" in contact and contact["emailAddresses"]:
                if contact["emailAddresses"][0]["value"] == "john.doe@example.com":
                    email_contact = contact
                    break
        self.assertIsNotNone(email_contact)

    def test_search_collection_with_phone_query(self):
        """
        Test searching collection by phone number.
        """
        # Add a contact with phone number
        DB["myContacts"]["people/phone"] = {
            "resourceName": "people/phone",
            "etag": "etag888",
            "names": [{"givenName": "Phone", "familyName": "Contact"}],
            "phoneNumbers": [{"value": "+1234567890", "type": "mobile"}]
        }
        
        results = utils.search_collection("myContacts", "1234567890", 10)
        self.assertGreater(len(results), 0)
        # Find the contact with the exact phone number
        phone_contact = None
        for contact in results:
            if "phoneNumbers" in contact and contact["phoneNumbers"]:
                if contact["phoneNumbers"][0]["value"] == "+1234567890":
                    phone_contact = contact
                    break
        self.assertIsNotNone(phone_contact)

    def test_search_collection_case_insensitive(self):
        """
        Test searching collection with case insensitive matching.
        """
        results = utils.search_collection("myContacts", "JOHN", 10)
        self.assertGreater(len(results), 0)
        # Find the contact with the name "John"
        john_contact = None
        for contact in results:
            if contact["names"][0]["givenName"] == "John":
                john_contact = contact
                break
        self.assertIsNotNone(john_contact)

    def test_search_collection_partial_match(self):
        """
        Test searching collection with partial matches.
        """
        results = utils.search_collection("myContacts", "jo", 10)
        self.assertGreater(len(results), 0)
        # Find the contact with the name "John"
        john_contact = None
        for contact in results:
            if contact["names"][0]["givenName"] == "John":
                john_contact = contact
                break
        self.assertIsNotNone(john_contact)

    def test_search_collection_no_matches(self):
        """
        Test searching collection with no matches.
        """
        results = utils.search_collection("myContacts", "nonexistent", 10)
        self.assertEqual(len(results), 0)

    def test_search_collection_all_contacts(self):
        """
        Test searching collection with None query to get all contacts.
        """
        results = utils.search_collection("myContacts", None, 10)
        self.assertGreater(len(results), 0)

    def test_search_collection_max_results_limit(self):
        """
        Test that search respects max_results limit.
        """
        # Add more contacts
        for i in range(5):
            DB["myContacts"][f"people/test{i}"] = {
                "resourceName": f"people/test{i}",
                "etag": f"etag{i}",
                "names": [{"givenName": f"Test{i}", "familyName": "Contact"}]
            }
        
        results = utils.search_collection("myContacts", None, 3)
        self.assertLessEqual(len(results), 3)

    def test_search_collection_multiple_matches(self):
        """
        Test searching collection with multiple matches.
        """
        # Add another contact with similar name
        DB["myContacts"]["people/john2"] = {
            "resourceName": "people/john2",
            "etag": "etag777",
            "names": [{"givenName": "John", "familyName": "Smith"}]
        }
        
        results = utils.search_collection("myContacts", "John", 10)
        self.assertGreaterEqual(len(results), 2)
        # Verify we have at least 2 contacts with name "John"
        john_contacts = [c for c in results if c["names"][0]["givenName"] == "John"]
        self.assertGreaterEqual(len(john_contacts), 2)

    def test_search_collection_empty_collection(self):
        """
        Test searching an empty collection.
        """
        empty_collection = "emptyCollection"
        DB[empty_collection] = {}
        
        results = utils.search_collection(empty_collection, "test", 10)
        self.assertEqual(len(results), 0)

    def test_search_collection_invalid_collection(self):
        """
        Test searching an invalid collection name.
        """
        with self.assertRaises(KeyError):
            utils.search_collection("nonexistent_collection", "test", 10)

    def test_save_state_functionality(self):
        """
        Test saving database state to a file.
        """
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Save the current state
            save_state(temp_path)
            
            # Verify the file was created and contains data
            self.assertTrue(os.path.exists(temp_path))
            
            # Read and verify the content
            with open(temp_path, 'r') as f:
                saved_data = json.load(f)
            
            # Verify the saved data matches the current DB state
            self.assertEqual(saved_data, dict(DB))
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_state_functionality(self):
        """
        Test loading database state from a file.
        """
        # Create a temporary file with test data
        test_data = {
            "myContacts": {
                "people/test123": {
                    "resourceName": "people/test123",
                    "etag": "test_etag",
                    "names": [{"givenName": "TestLoad", "familyName": "Contact"}],
                    "emailAddresses": [{"value": "testload@example.com", "type": "work"}]
                }
            },
            "otherContacts": {},
            "directory": {}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            json.dump(test_data, temp_file)
            temp_path = temp_file.name
        
        try:
            # Store original state
            original_state = dict(DB)
            
            # Load the test state
            load_state(temp_path)
            
            # Verify the state was loaded correctly
            self.assertEqual(dict(DB), test_data)
            self.assertIn("people/test123", DB["myContacts"])
            self.assertEqual(DB["myContacts"]["people/test123"]["names"][0]["givenName"], "TestLoad")
            
        finally:
            # Restore original state
            DB.clear()
            DB.update(original_state)
            
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_and_load_state_roundtrip(self):
        """
        Test saving and loading state maintains data integrity.
        """
        # Create some test data
        test_contact = {
            "resourceName": "people/roundtrip123",
            "etag": "roundtrip_etag",
            "names": [{"givenName": "Roundtrip", "familyName": "Test"}],
            "emailAddresses": [{"value": "roundtrip@example.com", "type": "work"}]
        }
        
        # Add the test contact to the database
        DB["myContacts"]["people/roundtrip123"] = test_contact
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name
        
        try:
            # Save the state
            save_state(temp_path)
            
            # Clear the database
            DB.clear()
            DB.update({"myContacts": {}, "otherContacts": {}, "directory": {}})
            
            # Verify the database is empty
            self.assertEqual(len(DB["myContacts"]), 0)
            
            # Load the state back
            load_state(temp_path)
            
            # Verify the data was restored correctly
            self.assertIn("people/roundtrip123", DB["myContacts"])
            self.assertEqual(DB["myContacts"]["people/roundtrip123"]["names"][0]["givenName"], "Roundtrip")
            self.assertEqual(DB["myContacts"]["people/roundtrip123"]["emailAddresses"][0]["value"], "roundtrip@example.com")
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_load_state_with_invalid_file(self):
        """
        Test loading state with an invalid file path.
        """
        # Store original state
        original_state = dict(DB)
        
        try:
            # Try to load from a non-existent file
            with self.assertRaises(FileNotFoundError):
                load_state("nonexistent_file.json")
            
            # Verify the database state is unchanged
            self.assertEqual(dict(DB), original_state)
            
        finally:
            # Restore original state
            DB.clear()
            DB.update(original_state)

    def test_save_state_with_invalid_path(self):
        """
        Test saving state with an invalid file path.
        """
        # Try to save to an invalid path (directory that doesn't exist)
        with self.assertRaises(FileNotFoundError):
            save_state("/nonexistent/directory/file.json")

if __name__ == '__main__':
    unittest.main()
