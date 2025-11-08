import unittest
import copy
from ..SimulationEngine import custom_errors
from ..SimulationEngine.utils import create_contact
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
import re

class TestCreateContact(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Set up a clean database state for each test."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB['contacts'] = {}
        DB['chats'] = {}

    def tearDown(self):
        """Restore the original database state after each test."""
        DB.clear()
        DB.update(self._original_DB_state)

    def _generate_expected_jid(self, phone_number_str: str) -> str:
        """Generates the expected JID from a phone number string."""
        if not phone_number_str:
            return '@s.whatsapp.net'
        digits = re.sub(r'\D', '', phone_number_str)
        return f'{digits}@s.whatsapp.net' if digits else '@s.whatsapp.net'

    def _generate_expected_resource_name(self, phone_number_str: str) -> str:
        """Generates the expected resourceName for a contact."""
        jid = self._generate_expected_jid(phone_number_str)
        return f"people/{jid}"

    def _assert_person_contact_data(self, contact_dict: dict, expected_phone: str, expected_full_name: str | None):
        """
        Asserts that the contact dictionary matches the new PersonContact structure.
        """
        # --- Top-level Assertions ---
        self.assertIsInstance(contact_dict, dict)
        expected_resource_name = self._generate_expected_resource_name(expected_phone)
        self.assertEqual(contact_dict.get('resourceName'), expected_resource_name)
        self.assertIn('etag', contact_dict)
        self.assertIsInstance(contact_dict.get('etag'), str)

        # --- Names List Assertions ---
        names_list = contact_dict.get('names', [])
        self.assertIsInstance(names_list, list)
        if expected_full_name:
            self.assertEqual(len(names_list), 1)
            name_parts = expected_full_name.strip().split()
            expected_given_name = name_parts[0]
            expected_family_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else None
            self.assertEqual(names_list[0].get('givenName'), expected_given_name)
            self.assertEqual(names_list[0].get('familyName'), expected_family_name)
        else:
            self.assertEqual(len(names_list), 0)

        # --- PhoneNumbers List Assertions ---
        phone_list = contact_dict.get('phoneNumbers', [])
        self.assertIsInstance(phone_list, list)
        self.assertEqual(len(phone_list), 1)
        self.assertEqual(phone_list[0].get('value'), expected_phone)
        self.assertEqual(phone_list[0].get('type'), 'mobile')
        self.assertTrue(phone_list[0].get('primary'))

        # --- Nested WhatsApp Object Assertions ---
        whatsapp_info = contact_dict.get('whatsapp', {})
        expected_jid = self._generate_expected_jid(expected_phone)
        self.assertIsInstance(whatsapp_info, dict)
        self.assertEqual(whatsapp_info.get('jid'), expected_jid)
        self.assertEqual(whatsapp_info.get('name_in_address_book'), expected_full_name)
        self.assertEqual(whatsapp_info.get('phone_number'), expected_phone)
        self.assertTrue(whatsapp_info.get('is_whatsapp_user'))
        self.assertIsNone(whatsapp_info.get('profile_name'))

    def test_create_contact_success_with_name(self):
        phone_number = '12025550104'
        name = 'John Doe'
        expected_resource_name = self._generate_expected_resource_name(phone_number)
        
        result = create_contact(phone_number=phone_number, name_in_address_book=name)
        self._assert_person_contact_data(result, phone_number, name)
        
        self.assertIn(expected_resource_name, DB['contacts'])
        db_contact = DB['contacts'][expected_resource_name]
        self._assert_person_contact_data(db_contact, phone_number, name)

    def test_create_contact_success_without_name(self):
        phone_number = '447912345678'
        expected_resource_name = self._generate_expected_resource_name(phone_number)
        
        result = create_contact(phone_number=phone_number)
        self._assert_person_contact_data(result, phone_number, None)
        
        self.assertIn(expected_resource_name, DB['contacts'])
        db_contact = DB['contacts'][expected_resource_name]
        self._assert_person_contact_data(db_contact, phone_number, None)

    def test_create_contact_success_with_empty_name(self):
        phone_number = '33612345678'
        name = '' # Should be treated like no name was provided
        expected_resource_name = self._generate_expected_resource_name(phone_number)

        result = create_contact(phone_number=phone_number, name_in_address_book=name)
        self._assert_person_contact_data(result, phone_number, name)
        
        db_contact = DB['contacts'][expected_resource_name]
        self.assertEqual(db_contact.get('names', []), []) # Specifically check for empty names list

    def test_create_contact_success_phone_with_formatting(self):
        phone_number_input = '+1 (555) 123-4567'
        name = 'Formatted Phone'
        expected_resource_name = self._generate_expected_resource_name(phone_number_input)
        
        result = create_contact(phone_number=phone_number_input, name_in_address_book=name)
        self._assert_person_contact_data(result, phone_number_input, name)
        
        self.assertIn(expected_resource_name, DB['contacts'])
        db_contact = DB['contacts'][expected_resource_name]
        self._assert_person_contact_data(db_contact, phone_number_input, name)

    def test_create_contact_already_exists(self):
        phone_number = '13035550182'
        resource_name = self._generate_expected_resource_name(phone_number)
        jid = self._generate_expected_jid(phone_number)

        # Pre-populate DB with a contact having the new structure
        DB['contacts'][resource_name] = {
            "resourceName": resource_name,
            "etag": "some-etag-123",
            "names": [{"givenName": "Original", "familyName": "Name"}],
            "phoneNumbers": [{"value": phone_number, "type": "mobile", "primary": True}],
            "whatsapp": {
                "jid": jid,
                "name_in_address_book": "Original Name",
                "phone_number": phone_number,
                "is_whatsapp_user": True
            }
        }
        initial_db_contacts_copy = copy.deepcopy(DB['contacts'])

        self.assert_error_behavior(
            func_to_call=create_contact,
            expected_exception_type=custom_errors.ContactAlreadyExistsError,
            expected_message='A contact with the given phone number already exists.',
            phone_number=phone_number,
            name_in_address_book='Attempt New Name'
        )
        self.assertEqual(DB['contacts'], initial_db_contacts_copy, 'DB should not be modified if contact already exists')

    def test_create_contact_invalid_phone_empty_string(self):
        self.assert_error_behavior(func_to_call=create_contact, expected_exception_type=custom_errors.InvalidPhoneNumberError, expected_message='The provided phone number has an invalid format.', phone_number='', name_in_address_book='Test Name')
        self.assertEqual(DB['contacts'], {}, 'DB should not be modified on error')

    def test_create_contact_invalid_phone_too_short(self):
        self.assert_error_behavior(func_to_call=create_contact, expected_exception_type=custom_errors.InvalidPhoneNumberError, expected_message='The provided phone number has an invalid format.', phone_number='123', name_in_address_book='Short Num')
        self.assertEqual(DB['contacts'], {}, 'DB should not be modified on error')

    def test_create_contact_validation_error_phone_number_wrong_type(self):
        self.assert_error_behavior(func_to_call=create_contact, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed: phone_number must be a string.', phone_number=12345, name_in_address_book='Test Name')
        self.assertEqual(DB['contacts'], {}, 'DB should not be modified on validation error')

    def test_create_contact_validation_error_name_wrong_type(self):
        self.assert_error_behavior(func_to_call=create_contact, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed: name_in_address_book must be a string.', phone_number='17035550123', name_in_address_book=123)
        self.assertEqual(DB['contacts'], {}, 'DB should not be modified on validation error')
    
    def test_create_contact_invalid_phone_number_with_comma(self):
        self.assert_error_behavior(func_to_call=create_contact, expected_exception_type=custom_errors.InvalidPhoneNumberError, expected_message='The provided phone number has an invalid format.', phone_number='+1703,555,0123', name_in_address_book='Test Name')
        self.assertEqual(DB['contacts'], {}, 'DB should not be modified on error')
    
    def test_create_contact_invalid_phone_number_with_colon(self):
        self.assert_error_behavior(func_to_call=create_contact, expected_exception_type=custom_errors.InvalidPhoneNumberError, expected_message='The provided phone number has an invalid format.', phone_number='+1703:555:0123', name_in_address_book='Test Name')
        self.assertEqual(DB['contacts'], {}, 'DB should not be modified on error')
    
    def test_create_contact_invalid_phone_number_with_semicolon(self):
        self.assert_error_behavior(func_to_call=create_contact, expected_exception_type=custom_errors.InvalidPhoneNumberError, expected_message='The provided phone number has an invalid format.', phone_number='+1703;555;0123', name_in_address_book='Test Name')
        self.assertEqual(DB['contacts'], {}, 'DB should not be modified on error')
    
    def test_create_contact_invalid_phone_number_with_slash(self):
        self.assert_error_behavior(func_to_call=create_contact, expected_exception_type=custom_errors.InvalidPhoneNumberError, expected_message='The provided phone number has an invalid format.', phone_number='+1703/555/0123', name_in_address_book='Test Name')
        self.assertEqual(DB['contacts'], {}, 'DB should not be modified on error')
    
    def test_create_contact_invalid_phone_number_with_None(self):
        self.assert_error_behavior(func_to_call=create_contact, expected_exception_type=custom_errors.ValidationError, expected_message='Input validation failed: phone_number must be a string.', phone_number=None, name_in_address_book='Test Name')
        self.assertEqual(DB['contacts'], {}, 'DB should not be modified on error')
    
    def test_create_contact_invalid_phone_too_long(self):
        self.assert_error_behavior(func_to_call=create_contact, expected_exception_type=custom_errors.InvalidPhoneNumberError, expected_message='The provided phone number has an invalid format.', phone_number='+1703555012341111', name_in_address_book='Test Name')
        self.assertEqual(DB['contacts'], {}, 'DB should not be modified on error')

if __name__ == '__main__':
    unittest.main()