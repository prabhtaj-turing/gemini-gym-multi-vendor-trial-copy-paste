import unittest
import copy
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..SimulationEngine import custom_errors
from .. import get_contact

class TestGetContact(BaseTestCaseWithErrorHandler):
    """
    Test suite for the get_contact function.
    """

    def setUp(self):
        """
        Set up the test environment before each test.
        """
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        # Populate the global DB with test data
        DB.update({
            "myContacts": {
                "people/c1234567890": {
                    "resourceName": "people/c1234567890",
                    "etag": "etagForJohnDoe",
                    "names": [{"givenName": "John", "familyName": "Doe"}],
                    "emailAddresses": [{
                        "value": "john.doe@example.com",
                        "type": "home",
                        "primary": True
                    }],
                    "phoneNumbers": [{
                        "value": "+1-222-333-4444",
                        "type": "mobile",
                        "primary": True
                    }],
                    "organizations": [{
                        "name": "Example Corp",
                        "title": "Software Developer"
                    }]
                }
            },
            "otherContacts": {
                "otherContacts/c0987654321": {
                    "resourceName": "otherContacts/c0987654321",
                    "etag": "etagForJaneSmith",
                    "names": [{"givenName": "Jane", "familyName": "Smith"}],
                    "emailAddresses": [{
                        "value": "jane.smith@work.com",
                        "type": "work",
                        "primary": True
                    }]
                }
            },
            "directory": {
                "people/d1122334455": {
                    "resourceName": "people/d1122334455",
                    "etag": "etagForAlexChen",
                    "names": [{"givenName": "Alex", "familyName": "Chen"}],
                    "emailAddresses": [{
                        "value": "alex.chen@yourcompany.com",
                        "primary": True
                    }],
                    "organizations": [{
                        "name": "YourCompany",
                        "title": "Product Manager",
                        "department": "Product"
                    }],
                    "isWorkspaceUser": True
                }
            }
        })
        self.john_doe_contact = DB["myContacts"]["people/c1234567890"]
        self.jane_smith_contact = DB["otherContacts"]["otherContacts/c0987654321"]
        self.alex_chen_contact = DB["directory"]["people/d1122334455"]

    def tearDown(self):
        """
        Clean up the test environment after each test.
        """
        DB.clear()
        DB.update(self._original_DB_state)

    def test_get_contact_by_resource_name_from_mycontacts_success(self):
        """
        Test successfully retrieving a contact from 'myContacts' by its resourceName.
        """
        contact = get_contact(identifier="people/c1234567890")
        self.assertEqual(contact, self.john_doe_contact)

    def test_get_contact_by_resource_name_from_othercontacts_success(self):
        """
        Test successfully retrieving a contact from 'otherContacts' by its resourceName.
        """
        contact = get_contact(identifier="otherContacts/c0987654321")
        self.assertEqual(contact, self.jane_smith_contact)

    def test_get_contact_by_resource_name_from_directory_success(self):
        """
        Test successfully retrieving a contact from 'directory' by its resourceName.
        """
        contact = get_contact(identifier="people/d1122334455")
        self.assertEqual(contact, self.alex_chen_contact)

    def test_get_contact_by_email_from_mycontacts_success(self):
        """
        Test successfully retrieving a contact from 'myContacts' by its email address.
        """
        contact = get_contact(identifier="john.doe@example.com")
        self.assertEqual(contact, self.john_doe_contact)

    def test_get_contact_by_email_from_othercontacts_success(self):
        """
        Test successfully retrieving a contact from 'otherContacts' by its email address.
        """
        contact = get_contact(identifier="jane.smith@work.com")
        self.assertEqual(contact, self.jane_smith_contact)

    def test_get_contact_by_email_from_directory_success(self):
        """
        Test successfully retrieving a contact from 'directory' by its email address.
        """
        contact = get_contact(identifier="alex.chen@yourcompany.com")
        self.assertEqual(contact, self.alex_chen_contact)

    def test_get_contact_by_email_case_insensitive(self):
        """
        Test that email lookup is case-insensitive.
        """
        contact = get_contact(identifier="JOHN.DOE@EXAMPLE.COM")
        self.assertEqual(contact, self.john_doe_contact)

    def test_get_contact_not_found_by_resource_name_raises_error(self):
        """
        Test that ContactNotFoundError is raised for a non-existent resourceName.
        """
        identifier = "people/nonexistent"
        self.assert_error_behavior(
            func_to_call=get_contact,
            expected_exception_type=custom_errors.ContactNotFoundError,
            expected_message=f"No contact found for identifier: {identifier}",
            identifier=identifier
        )

    def test_get_contact_not_found_by_email_raises_error(self):
        """
        Test that ContactNotFoundError is raised for a non-existent email.
        """
        identifier = "nonexistent@example.com"
        self.assert_error_behavior(
            func_to_call=get_contact,
            expected_exception_type=custom_errors.ContactNotFoundError,
            expected_message=f"No contact found for identifier: {identifier}",
            identifier=identifier
        )

    def test_get_contact_with_empty_identifier_raises_validation_error(self):
        """
        Test that ValidationError is raised for an empty string identifier.
        """
        self.assert_error_behavior(
            func_to_call=get_contact,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Identifier must be a non-empty string.",
            identifier=""
        )

    def test_get_contact_with_none_identifier_raises_validation_error(self):
        """
        Test that ValidationError is raised for a None identifier.
        """
        self.assert_error_behavior(
            func_to_call=get_contact,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Identifier must be a non-empty string.",
            identifier=None
        )

    def test_get_contact_with_non_string_identifier_raises_validation_error(self):
        """
        Test that ValidationError is raised for a non-string identifier like an integer.
        """
        self.assert_error_behavior(
            func_to_call=get_contact,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Identifier must be a non-empty string.",
            identifier=12345
        )

if __name__ == '__main__':
    unittest.main()