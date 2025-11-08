import unittest
import copy
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..SimulationEngine import custom_errors
from .. import list_contacts

class TestListContacts(BaseTestCaseWithErrorHandler):
    """
    Test suite for the list_contacts function.
    """

    def setUp(self):
        """
        Set up the test environment by initializing the database
        with a predefined set of contacts.
        """
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        # Populate the DB with test data for this test class
        DB.update({
            "myContacts": {
                "people/c1": {
                    "resourceName": "people/c1",
                    "etag": "etag1",
                    "names": [{"givenName": "John", "familyName": "Doe"}],
                    "emailAddresses": [{"value": "john.doe@example.com"}],
                    "notes": "My best friend"
                },
                "people/c2": {
                    "resourceName": "people/c2",
                    "etag": "etag2",
                    "names": [{"givenName": "Jane", "familyName": "Smith"}],
                    "phoneNumbers": [{"value": "+1234567890"}],
                },
                "people/c3": {
                    "resourceName": "people/c3",
                    "etag": "etag3",
                    "names": [{"givenName": "Peter", "familyName": "Jones"}],
                    "emailAddresses": [{"value": "peter.jones@work.com"}],
                },
                "people/c4": {
                    "resourceName": "people/c4",
                    "etag": "etag4",
                    "names": [{"givenName": "John", "familyName": "Appleseed"}],
                }
            },
            "otherContacts": {
                "otherContacts/oc1": {
                    "resourceName": "otherContacts/oc1",
                    "etag": "etag_oc1",
                    "names": [{"givenName": "Hidden", "familyName": "Contact"}],
                }
            },
            "directory": {}
        })
        # Keep a clean copy of the setup data for easy access in tests
        self.initial_db_data = copy.deepcopy(DB)


    def tearDown(self):
        """
        Restore the original database state after each test.
        """
        DB.clear()
        DB.update(self._original_DB_state)

    def test_list_contacts_no_args_success(self):
        """
        Test listing contacts with default parameters, expecting all contacts from 'myContacts'.
        """
        result = list_contacts()
        self.assertIsInstance(result, dict)
        self.assertIn('contacts', result)
        self.assertEqual(len(result['contacts']), 4)
        # Verify it doesn't include contacts from other collections
        resource_names = {c['resourceName'] for c in result['contacts']}
        self.assertNotIn("otherContacts/oc1", resource_names)

    def test_list_contacts_with_max_results_less_than_total(self):
        """
        Test listing contacts with max_results set to a value less than the total number of contacts.
        """
        result = list_contacts(max_results=2)
        self.assertEqual(len(result['contacts']), 2)

    def test_list_contacts_with_max_results_equal_to_total(self):
        """
        Test listing contacts with max_results equal to the total number of contacts.
        """
        result = list_contacts(max_results=4)
        self.assertEqual(len(result['contacts']), 4)

    def test_list_contacts_with_max_results_greater_than_total(self):
        """
        Test listing contacts with max_results greater than the total, should return all contacts.
        """
        result = list_contacts(max_results=10)
        self.assertEqual(len(result['contacts']), 4)

    def test_list_contacts_zero_max_results_raises_validation_error(self):
        """
        Test that max_results=0 raises a ValidationError as it's not a positive integer.
        """
        self.assert_error_behavior(
            func_to_call=list_contacts,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="max_results must be a positive integer.",
            max_results=0
        )

    def test_list_contacts_filter_by_given_name(self):
        """
        Test filtering contacts by a given name that matches multiple entries.
        """
        result = list_contacts(name_filter="John")
        self.assertEqual(len(result['contacts']), 2)
        resource_names = {c['resourceName'] for c in result['contacts']}
        self.assertIn("people/c1", resource_names)
        self.assertIn("people/c4", resource_names)

    def test_list_contacts_filter_by_family_name(self):
        """
        Test filtering contacts by a unique family name.
        """
        result = list_contacts(name_filter="Smith")
        self.assertEqual(len(result['contacts']), 1)
        self.assertEqual(result['contacts'][0]['resourceName'], "people/c2")

    def test_list_contacts_filter_case_insensitive(self):
        """
        Test that name filtering is case-insensitive.
        """
        result = list_contacts(name_filter="peter")
        self.assertEqual(len(result['contacts']), 1)
        self.assertEqual(result['contacts'][0]['resourceName'], "people/c3")

    def test_list_contacts_filter_no_match(self):
        """
        Test filtering with a name that does not match any contact.
        """
        result = list_contacts(name_filter="NonExistentName")
        self.assertEqual(len(result['contacts']), 0)

    def test_list_contacts_filter_does_not_search_other_collections(self):
        """
        Test that filtering does not return results from 'otherContacts'.
        """
        result = list_contacts(name_filter="Hidden")
        self.assertEqual(len(result['contacts']), 0)

    def test_list_contacts_filter_with_max_results(self):
        """
        Test filtering that yields multiple results but is limited by max_results.
        """
        result = list_contacts(name_filter="John", max_results=1)
        self.assertEqual(len(result['contacts']), 1)
        # The result should be one of the 'John' contacts
        self.assertIn(result['contacts'][0]['resourceName'], ["people/c1", "people/c4"])

    def test_list_contacts_empty_mycontacts_collection(self):
        """
        Test listing contacts when the 'myContacts' collection is empty.
        """
        DB['myContacts'].clear()
        result = list_contacts()
        self.assertEqual(len(result['contacts']), 0)

    def test_list_contacts_no_mycontacts_collection_raises_error(self):
        """
        Test that ContactsCollectionNotFoundError is raised if 'myContacts' key is missing.
        """
        del DB['myContacts']
        self.assert_error_behavior(
            func_to_call=list_contacts,
            expected_exception_type=custom_errors.ContactsCollectionNotFoundError,
            expected_message="Contacts collection 'myContacts' not found in the database."
        )

    def test_list_contacts_invalid_name_filter_type_raises_validation_error(self):
        """
        Test that a non-string name_filter raises a ValidationError.
        """
        self.assert_error_behavior(
            func_to_call=list_contacts,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="name_filter must be a string.",
            name_filter=12345
        )

    def test_list_contacts_invalid_max_results_type_raises_validation_error(self):
        """
        Test that a non-integer max_results raises a ValidationError.
        """
        self.assert_error_behavior(
            func_to_call=list_contacts,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="max_results must be a positive integer.",
            max_results="not-a-number"
        )

    def test_list_contacts_negative_max_results_raises_validation_error(self):
        """
        Test that a negative max_results value raises a ValidationError.
        """
        self.assert_error_behavior(
            func_to_call=list_contacts,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="max_results must be a positive integer.",
            max_results=-5
        )

    def test_list_contacts_empty_filter_string_returns_all(self):
        """
        Test that an empty string for name_filter behaves like no filter was provided.
        """
        result_with_empty_filter = list_contacts(name_filter="")
        result_with_no_filter = list_contacts()
        self.assertEqual(len(result_with_empty_filter['contacts']), 4)
        self.assertEqual(result_with_empty_filter, result_with_no_filter)

    def test_list_contacts_includes_notes_field(self):
        """
        Test that the 'notes' field is included in the output when it exists.
        """
        result = list_contacts(name_filter="John")
        self.assertEqual(len(result['contacts']), 2)
        
        # Find the contact that should have notes
        john_doe_contact = next((c for c in result['contacts'] if c['resourceName'] == "people/c1"), None)
        
        # Assert that the contact was found and has the correct note
        self.assertIsNotNone(john_doe_contact)
        self.assertIn("notes", john_doe_contact)
        self.assertEqual(john_doe_contact["notes"], "My best friend")
        
        # Find a contact that should not have notes
        john_appleseed_contact = next((c for c in result['contacts'] if c['resourceName'] == "people/c4"), None)

        # Assert that the contact was found and does not have the notes field
        self.assertIsNotNone(john_appleseed_contact)
        self.assertIsNone(john_appleseed_contact['notes'])

if __name__ == '__main__':
    unittest.main()