import unittest
import copy
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..SimulationEngine import custom_errors
from .. import update_contact

class TestUpdateContact(BaseTestCaseWithErrorHandler):
    """
    Test suite for the update_contact function.
    """

    def setUp(self):
        """
        Set up a predictable database state for each test.
        """
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB.update({
            "myContacts": {
                "people/c12345": {
                    "resourceName": "people/c12345",
                    "etag": "initial_etag_12345",
                    "names": [{"givenName": "Alex", "familyName": "Bell"}],
                    "emailAddresses": [{
                        "value": "alex.bell@example.com",
                        "type": "home",
                        "primary": True
                    }],
                    "phoneNumbers": [{
                        "value": "+1234567890",
                        "type": "mobile",
                        "primary": True
                    }],
                    "organizations": [{"name": "Innovation Inc."}]
                },
                "people/c67890": {
                    "resourceName": "people/c67890",
                    "etag": "initial_etag_67890",
                    # No 'names' key
                    "emailAddresses": [],
                    "phoneNumbers": []
                },
                "people/c-no-primary": {
                    "resourceName": "people/c-no-primary",
                    "etag": "etag_no_primary_initial",
                    "names": [{"givenName": "Primary", "familyName": "Less"}],
                    "emailAddresses": [
                        {"value": "first@email.com", "type": "work"},
                        {"value": "second@email.com", "type": "home"}
                    ],
                    "phoneNumbers": [
                        {"value": "111-111-1111", "type": "mobile"},
                        {"value": "222-222-2222", "type": "work"}
                    ]
                }
            },
            "otherContacts": {},
            "directory": {}
        })
        self.contact_to_update = "people/c12345"
        self.minimal_contact = "people/c67890"
        self.no_primary_contact = "people/c-no-primary"

    def tearDown(self):
        """
        Restore the original database state after each test.
        """
        DB.clear()
        DB.update(self._original_DB_state)

    def test_update_single_field_given_name(self):
        """
        Test successfully updating only the given name.
        """
        original_contact = copy.deepcopy(DB["myContacts"][self.contact_to_update])
        updated_contact = update_contact(
            resource_name=self.contact_to_update,
            given_name="Alexander"
        )

        self.assertNotEqual(updated_contact['etag'], original_contact['etag'])
        self.assertEqual(updated_contact['names'][0]['givenName'], "Alexander")
        self.assertEqual(updated_contact['names'][0]['familyName'], original_contact['names'][0]['familyName'])
        self.assertEqual(updated_contact['emailAddresses'], original_contact['emailAddresses'])
        self.assertEqual(updated_contact['phoneNumbers'], original_contact['phoneNumbers'])

    def test_update_single_field_family_name(self):
        """
        Test successfully updating only the family name.
        """
        original_contact = copy.deepcopy(DB["myContacts"][self.contact_to_update])
        updated_contact = update_contact(
            resource_name=self.contact_to_update,
            family_name="Graham Bell"
        )

        self.assertNotEqual(updated_contact['etag'], original_contact['etag'])
        self.assertEqual(updated_contact['names'][0]['familyName'], "Graham Bell")
        self.assertEqual(updated_contact['names'][0]['givenName'], original_contact['names'][0]['givenName'])

    def test_update_single_field_email(self):
        """
        Test successfully updating only the email address.
        """
        original_contact = copy.deepcopy(DB["myContacts"][self.contact_to_update])
        new_email = "alex.g.bell@work.com"
        updated_contact = update_contact(
            resource_name=self.contact_to_update,
            email=new_email
        )

        self.assertNotEqual(updated_contact['etag'], original_contact['etag'])
        self.assertEqual(len(updated_contact['emailAddresses']), 1)
        self.assertEqual(updated_contact['emailAddresses'][0]['value'], new_email)
        self.assertTrue(updated_contact['emailAddresses'][0]['primary'])
        self.assertEqual(updated_contact['names'], original_contact['names'])

    def test_update_single_field_phone(self):
        """
        Test successfully updating only the phone number.
        """
        original_contact = copy.deepcopy(DB["myContacts"][self.contact_to_update])
        new_phone = "+14155552671"
        updated_contact = update_contact(
            resource_name=self.contact_to_update,
            phone=new_phone
        )

        self.assertNotEqual(updated_contact['etag'], original_contact['etag'])
        self.assertEqual(len(updated_contact['phoneNumbers']), 1)
        self.assertEqual(updated_contact['phoneNumbers'][0]['value'], new_phone)
        self.assertTrue(updated_contact['phoneNumbers'][0]['primary'])
        self.assertEqual(updated_contact['names'], original_contact['names'])

    def test_update_multiple_fields(self):
        """
        Test successfully updating multiple fields simultaneously.
        """
        updated_contact = update_contact(
            resource_name=self.contact_to_update,
            given_name="Lex",
            family_name="Luthor",
            email="lex@lexcorp.com"
        )

        self.assertEqual(updated_contact['names'][0]['givenName'], "Lex")
        self.assertEqual(updated_contact['names'][0]['familyName'], "Luthor")
        self.assertEqual(updated_contact['emailAddresses'][0]['value'], "lex@lexcorp.com")
        self.assertIn('phoneNumbers', updated_contact) # Phone number should be preserved

    def test_update_all_fields(self):
        """
        Test successfully updating all available fields.
        """
        updated_contact = update_contact(
            resource_name=self.contact_to_update,
            given_name="John",
            family_name="Smith",
            email="j.smith@example.com",
            phone="+14155552671"
        )

        self.assertEqual(updated_contact['names'][0]['givenName'], "John")
        self.assertEqual(updated_contact['names'][0]['familyName'], "Smith")
        self.assertEqual(updated_contact['emailAddresses'][0]['value'], "j.smith@example.com")
        self.assertEqual(updated_contact['phoneNumbers'][0]['value'], "+14155552671")
        # Ensure other data is preserved
        self.assertIn("organizations", updated_contact)
        self.assertEqual(updated_contact["organizations"][0]["name"], "Innovation Inc.")

    def test_update_add_email_and_phone_to_contact(self):
        """
        Test adding an email and phone to a contact that doesn't have them.
        """
        new_email = "casey.jones@vigilante.net"
        new_phone = "+14155552671"
        updated_contact = update_contact(
            resource_name=self.minimal_contact,
            email=new_email,
            phone=new_phone
        )

        self.assertEqual(len(updated_contact['emailAddresses']), 1)
        self.assertEqual(updated_contact['emailAddresses'][0]['value'], new_email)
        self.assertTrue(updated_contact['emailAddresses'][0]['primary'])

        self.assertEqual(len(updated_contact['phoneNumbers']), 1)
        self.assertEqual(updated_contact['phoneNumbers'][0]['value'], new_phone)
        self.assertTrue(updated_contact['phoneNumbers'][0]['primary'])

    def test_update_non_existent_contact_raises_not_found_error(self):
        """
        Test that updating a non-existent contact raises ContactNotFoundError.
        """
        non_existent_rn = "people/c-does-not-exist"
        self.assert_error_behavior(
            func_to_call=update_contact,
            expected_exception_type=custom_errors.ContactNotFoundError,
            expected_message=f"Contact with resource name '{non_existent_rn}' not found.",
            resource_name=non_existent_rn,
            given_name="Ghost"
        )

    def test_update_no_fields_provided_raises_validation_error(self):
        """
        Test that calling update without any optional fields raises ValidationError.
        """
        self.assert_error_behavior(
            func_to_call=update_contact,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="At least one field (given_name, family_name, email, phone) must be provided for the update.",
            resource_name=self.contact_to_update
        )

    def test_update_with_empty_resource_name_raises_validation_error(self):
        """
        Test that an empty resource_name raises ValidationError.
        """
        self.assert_error_behavior(
            func_to_call=update_contact,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Argument 'resource_name' must be a non-empty string.",
            resource_name="",
            given_name="Test"
        )

    def test_update_with_none_resource_name_raises_validation_error(self):
        """
        Test that a None resource_name raises ValidationError.
        """
        self.assert_error_behavior(
            func_to_call=update_contact,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Argument 'resource_name' must be a non-empty string.",
            resource_name=None,
            family_name="Test"
        )

    def test_update_preserves_unrelated_data(self):
        """
        Test that fields not involved in the update are preserved.
        """
        original_contact = copy.deepcopy(DB["myContacts"][self.contact_to_update])
        update_contact(
            resource_name=self.contact_to_update,
            given_name="Alexy"
        )
        updated_db_contact = DB["myContacts"][self.contact_to_update]

        self.assertEqual(original_contact["organizations"], updated_db_contact["organizations"])
    
    def test_update_adds_name_field_if_missing(self):
        """
        Test updating a name creates the 'names' list if it doesn't exist.
        """
        updated_contact = update_contact(
            resource_name=self.minimal_contact,
            given_name="Casey",
            family_name="Jones"
        )
        self.assertIn('names', updated_contact)
        self.assertEqual(len(updated_contact['names']), 1)
        self.assertEqual(updated_contact['names'][0]['givenName'], "Casey")
        self.assertEqual(updated_contact['names'][0]['familyName'], "Jones")

    def test_update_email_of_first_entry_if_no_primary(self):
        """
        Test that the first email is updated if no primary email exists.
        """
        new_email = "updated.first@email.com"
        original_second_email = DB['myContacts'][self.no_primary_contact]['emailAddresses'][1]['value']

        updated_contact = update_contact(
            resource_name=self.no_primary_contact,
            email=new_email
        )

        self.assertEqual(updated_contact['emailAddresses'][0]['value'], new_email)
        self.assertEqual(updated_contact['emailAddresses'][1]['value'], original_second_email)

    def test_update_phone_of_first_entry_if_no_primary(self):
        """
        Test that the first phone number is updated if no primary phone exists.
        """
        new_phone = "+14155552671"
        original_second_phone = DB['myContacts'][self.no_primary_contact]['phoneNumbers'][1]['value']

        updated_contact = update_contact(
            resource_name=self.no_primary_contact,
            phone=new_phone
        )

        self.assertEqual(updated_contact['phoneNumbers'][0]['value'], new_phone)
        self.assertEqual(updated_contact['phoneNumbers'][1]['value'], original_second_phone)



if __name__ == '__main__':
    unittest.main()