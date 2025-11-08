import copy
import unittest
from unittest.mock import patch, MagicMock

from generic_calling import generic_calling
from generic_calling.SimulationEngine.custom_errors import ValidationError, ContactNotFoundError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from phone.SimulationEngine.db import DB as PHONE_DB, load_state as load_phone_state, DEFAULT_DB_PATH
from whatsapp.SimulationEngine.db import DB as WHATSAPP_DB


class TestGenericCalling(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Set up test fixtures."""
        # Backup and clear DBs
        self._original_phone_db_state = copy.deepcopy(PHONE_DB)
        self._original_whatsapp_db_state = copy.deepcopy(WHATSAPP_DB)
        PHONE_DB.clear()
        WHATSAPP_DB.clear()

        # Load phone data
        load_phone_state(DEFAULT_DB_PATH)

        # Setup WhatsApp data
        self.current_user_jid = "0000000000@s.whatsapp.net"
        self.contact_alice_jid = "1112223333@s.whatsapp.net"
        self.contact_alice_phone = "1112223333"
        WHATSAPP_DB['current_user_jid'] = self.current_user_jid
        WHATSAPP_DB['contacts'] = {
            f"people/{self.contact_alice_jid}": {
                "resourceName": f"people/{self.contact_alice_jid}",
                "names": [{"givenName": "Alice"}],
                "phoneNumbers": [{"value": self.contact_alice_phone, "type": "mobile", "primary": True}],
                "whatsapp": {"jid": self.contact_alice_jid, "is_whatsapp_user": True}
            }
        }
        WHATSAPP_DB['chats'] = {}
        WHATSAPP_DB['actions'] = []

    def tearDown(self):
        """Clean up after each test."""
        PHONE_DB.clear()
        PHONE_DB.update(self._original_phone_db_state)
        WHATSAPP_DB.clear()
        WHATSAPP_DB.update(self._original_whatsapp_db_state)

    def test_make_call_with_phone_number(self):
        """Test make_call with a PHONE_NUMBER endpoint."""
        endpoint = {"type": "PHONE_NUMBER", "value": "+14155552671"}
        recipient_info = {"name": "John Doe"}
        result = generic_calling.make_call(endpoint, recipient_info)
        self.assertEqual(result["status"], "success")

    def test_make_call_with_whatsapp_profile(self):
        """Test make_call with a WHATSAPP_PROFILE endpoint."""
        endpoint = {"type": "WHATSAPP_PROFILE", "value": self.contact_alice_jid}
        recipient_info = {"name": "Alice"}
        result = generic_calling.make_call(endpoint, recipient_info)
        self.assertEqual(result['status'], 'success')
        self.assertIn('call_id', result)

    def test_make_call_with_video_call(self):
        """Test make_call with video_call=True forces WhatsApp."""
        endpoint = {"type": "PHONE_NUMBER", "value": self.contact_alice_phone}
        recipient_info = {"name": "Alice"}
        result = generic_calling.make_call(endpoint, recipient_info, video_call=True)
        self.assertEqual(result['status'], 'success')
        self.assertIn('call_id', result)

    def test_make_call_missing_endpoint(self):
        """Test make_call with a missing endpoint."""
        self.assert_error_behavior(
            generic_calling.make_call,
            ValidationError,
            "Both endpoint and recipient_info are required to make a call.",
            endpoint=None, recipient_info={"name": "Test"}
        )

    def test_make_call_missing_recipient_info(self):
        """Test make_call with missing recipient_info."""
        self.assert_error_behavior(
            generic_calling.make_call,
            ValidationError,
            "Both endpoint and recipient_info are required to make a call.",
            endpoint={"type": "PHONE_NUMBER", "value": "+123"}, recipient_info=None
        )

    def test_make_call_invalid_speakerphone_type(self):
        """Test make_call with invalid on_speakerphone type."""
        self.assert_error_behavior(
            generic_calling.make_call,
            ValidationError,
            "Both on_speakerphone and video_call should be bool values.",
            endpoint={"type": "PHONE_NUMBER", "value": "+123"}, recipient_info={"name": "test"}, on_speakerphone="true"
        )

    def test_make_call_invalid_recipient_data(self):
        """Test make_call with invalid recipient data."""
        self.assert_error_behavior(
            generic_calling.make_call,
            ValidationError,
            "Invalid recipient: 1 validation error for RecipientInfoModel\nname\n  Input should be a valid string [type=string_type, input_value=123, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type",
            endpoint={"type": "PHONE_NUMBER", "value": "+123"}, recipient_info={"name": 123}
        )

    def test_show_call_recipient_choices_success(self):
        """Test show_call_recipient_choices for success."""
        recipient_choices = [{
            "recipient_info": {"name": "Test User"},
            "endpoints": [{"type": "PHONE_NUMBER", "value": "+14155552671"}]
        }]
        result = generic_calling.show_call_recipient_choices(recipient_choices)
        self.assertEqual(result["status"], "success")
        self.assertIn("choices", result)

    def test_show_call_recipient_choices_no_choices(self):
        """Test show_call_recipient_choices with no choices."""
        self.assert_error_behavior(
            generic_calling.show_call_recipient_choices,
            ValidationError,
            "recipient_choices is required.",
            recipient_choices=None
        )

    def test_show_call_recipient_choices_invalid_recipient(self):
        """Test show_call_recipient_choices with invalid recipient data."""
        recipient_choices = [{"recipient_info": {"name": 123}}]
        self.assert_error_behavior(
            generic_calling.show_call_recipient_choices,
            ValidationError,
            "Invalid recipient at index 0: 1 validation error for RecipientModel\ncontact_name\n  Input should be a valid string [type=string_type, input_value=123, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type",
            recipient_choices=recipient_choices
        )

    def test_show_call_recipient_choices_no_phone_numbers(self):
        """Test show_call_recipient_choices with no phone numbers."""
        recipient_choices = [{
            "recipient_info": {"name": "Test User"},
            "endpoints": [{"type": "WHATSAPP_PROFILE", "value": "123"}]
        }]
        self.assert_error_behavior(
            generic_calling.show_call_recipient_choices,
            ContactNotFoundError,
            "No phone numbers available to show.",
            recipient_choices=recipient_choices
        )

    def test_show_call_recipient_not_found_success(self):
        """Test show_call_recipient_not_found_or_specified for success."""
        result = generic_calling.show_call_recipient_not_found_or_specified("Test")
        self.assertEqual(result["status"], "success")

    def test_show_call_recipient_not_found_no_name(self):
        """Test show_call_recipient_not_found_or_specified with no name."""
        self.assert_error_behavior(
            generic_calling.show_call_recipient_not_found_or_specified,
            ValidationError,
            "name must be a string.",
            name=None
        )

    def test_show_call_recipient_not_found_empty_name(self):
        """Test show_call_recipient_not_found_or_specified with empty name."""
        self.assert_error_behavior(
            generic_calling.show_call_recipient_not_found_or_specified,
            ValidationError,
            "name must not be empty.",
            name=" "
        )

    def test_make_call_with_speakerphone_true(self):
        """Test make_call with speakerphone=True."""
        endpoint = {"type": "PHONE_NUMBER", "value": "+14155552671"}
        recipient_info = {"name": "John Doe"}
        result = generic_calling.make_call(endpoint, recipient_info, on_speakerphone=True)
        self.assertEqual(result["status"], "success")
        self.assertIn("call_id", result)

    def test_make_call_with_speakerphone_false(self):
        """Test make_call with speakerphone=False."""
        endpoint = {"type": "PHONE_NUMBER", "value": "+14155552671"}
        recipient_info = {"name": "John Doe"}
        result = generic_calling.make_call(endpoint, recipient_info, on_speakerphone=False)
        self.assertEqual(result["status"], "success")
        self.assertIn("call_id", result)

    def test_make_call_with_video_call_false(self):
        """Test make_call with video_call=False."""
        endpoint = {"type": "PHONE_NUMBER", "value": "+14155552671"}
        recipient_info = {"name": "John Doe"}
        result = generic_calling.make_call(endpoint, recipient_info, video_call=False)
        self.assertEqual(result["status"], "success")
        self.assertIn("call_id", result)

    def test_make_call_with_recipient_type(self):
        """Test make_call with recipient_type specified."""
        endpoint = {"type": "PHONE_NUMBER", "value": "+14155552671"}
        recipient_info = {"name": "John Doe", "recipient_type": "CONTACT"}
        result = generic_calling.make_call(endpoint, recipient_info)
        self.assertEqual(result["status"], "success")
        self.assertIn("call_id", result)

    def test_make_call_with_address_and_distance(self):
        """Test make_call with address and distance specified."""
        endpoint = {"type": "PHONE_NUMBER", "value": "+14155552671"}
        recipient_info = {
            "name": "John Doe", 
            "address": "123 Main St", 
            "distance": "5 miles"
        }
        result = generic_calling.make_call(endpoint, recipient_info)
        self.assertEqual(result["status"], "success")
        self.assertIn("call_id", result)

    def test_make_call_with_endpoint_label(self):
        """Test make_call with endpoint label specified."""
        endpoint = {"type": "PHONE_NUMBER", "value": "+14155552671", "label": "mobile"}
        recipient_info = {"name": "John Doe"}
        result = generic_calling.make_call(endpoint, recipient_info)
        self.assertEqual(result["status"], "success")
        self.assertIn("call_id", result)

    def test_make_call_invalid_video_call_type(self):
        """Test make_call with invalid video_call type."""
        self.assert_error_behavior(
            generic_calling.make_call,
            ValidationError,
            "Both on_speakerphone and video_call should be bool values.",
            endpoint={"type": "PHONE_NUMBER", "value": "+123"}, 
            recipient_info={"name": "test"}, 
            video_call="true"
        )

    def test_make_call_invalid_endpoint_type(self):
        """Test make_call with invalid endpoint type."""
        self.assert_error_behavior(
            generic_calling.make_call,
            ValidationError,
            "Invalid recipient: 1 validation error for RecipientEndpointModel\nendpoint_type\n  Input should be 'PHONE_NUMBER' or 'WHATSAPP_PROFILE' [type=literal_error, input_value='INVALID_TYPE', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/literal_error",
            endpoint={"type": "INVALID_TYPE", "value": "+123"}, 
            recipient_info={"name": "test"}
        )

    def test_make_call_missing_endpoint_value(self):
        """Test make_call with missing endpoint value."""
        self.assert_error_behavior(
            generic_calling.make_call,
            ValidationError,
            "Invalid recipient: 1 validation error for RecipientEndpointModel\nendpoint_value\n  Input should be a valid string [type=string_type, input_value=None, input_type=NoneType]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type",
            endpoint={"type": "PHONE_NUMBER"}, 
            recipient_info={"name": "test"}
        )

    def test_make_call_missing_recipient_name(self):
        """Test make_call with missing recipient name."""
        self.assert_error_behavior(
            generic_calling.make_call,
            ValidationError,
            "Both endpoint and recipient_info are required to make a call.",
            endpoint={"type": "PHONE_NUMBER", "value": "+123"}, 
            recipient_info={}
        )

    def test_show_call_recipient_choices_with_multiple_recipients(self):
        """Test show_call_recipient_choices with multiple recipients."""
        recipient_choices = [
            {
                "recipient_info": {"name": "User One"},
                "endpoints": [{"type": "PHONE_NUMBER", "value": "+14155552671"}]
            },
            {
                "recipient_info": {"name": "User Two"},
                "endpoints": [{"type": "PHONE_NUMBER", "value": "+14155552672"}]
            }
        ]
        result = generic_calling.show_call_recipient_choices(recipient_choices)
        self.assertEqual(result["status"], "success")
        self.assertIn("choices", result)

    def test_show_call_recipient_choices_with_mixed_endpoints(self):
        """Test show_call_recipient_choices with mixed endpoint types."""
        recipient_choices = [{
            "recipient_info": {"name": "Test User"},
            "endpoints": [
                {"type": "PHONE_NUMBER", "value": "+14155552671"},
                {"type": "WHATSAPP_PROFILE", "value": "123@s.whatsapp.net"}
            ]
        }]
        result = generic_calling.show_call_recipient_choices(recipient_choices)
        self.assertEqual(result["status"], "success")
        self.assertIn("choices", result)

    def test_show_call_recipient_choices_with_recipient_type(self):
        """Test show_call_recipient_choices with recipient_type specified."""
        recipient_choices = [{
            "recipient_info": {"name": "Test User", "recipient_type": "BUSINESS"},
            "endpoints": [{"type": "PHONE_NUMBER", "value": "+14155552671"}]
        }]
        result = generic_calling.show_call_recipient_choices(recipient_choices)
        self.assertEqual(result["status"], "success")
        self.assertIn("choices", result)

    def test_show_call_recipient_choices_with_address_and_distance(self):
        """Test show_call_recipient_choices with address and distance."""
        recipient_choices = [{
            "recipient_info": {
                "name": "Test User", 
                "address": "123 Main St", 
                "distance": "2 miles"
            },
            "endpoints": [{"type": "PHONE_NUMBER", "value": "+14155552671"}]
        }]
        result = generic_calling.show_call_recipient_choices(recipient_choices)
        self.assertEqual(result["status"], "success")
        self.assertIn("choices", result)

    def test_show_call_recipient_choices_with_endpoint_labels(self):
        """Test show_call_recipient_choices with endpoint labels."""
        recipient_choices = [{
            "recipient_info": {"name": "Test User"},
            "endpoints": [
                {"type": "PHONE_NUMBER", "value": "+14155552671", "label": "mobile"},
                {"type": "PHONE_NUMBER", "value": "+14155552672", "label": "work"}
            ]
        }]
        result = generic_calling.show_call_recipient_choices(recipient_choices)
        self.assertEqual(result["status"], "success")
        self.assertIn("choices", result)

    def test_show_call_recipient_choices_empty_recipient_choices(self):
        """Test show_call_recipient_choices with empty list."""
        self.assert_error_behavior(
            generic_calling.show_call_recipient_choices,
            ContactNotFoundError,
            "No phone numbers available to show.",
            recipient_choices=[]
        )

    def test_show_call_recipient_choices_invalid_endpoint_type(self):
        """Test show_call_recipient_choices with invalid endpoint type."""
        recipient_choices = [{
            "recipient_info": {"name": "Test User"},
            "endpoints": [{"type": "INVALID_TYPE", "value": "+14155552671"}]
        }]
        self.assert_error_behavior(
            generic_calling.show_call_recipient_choices,
            ContactNotFoundError,
            "No phone numbers available to show.",
            recipient_choices=recipient_choices
        )

    def test_show_call_recipient_choices_missing_recipient_info(self):
        """Test show_call_recipient_choices with missing recipient_info."""
        recipient_choices = [{"endpoints": [{"type": "PHONE_NUMBER", "value": "+14155552671"}]}]
        # This should work because recipient_info is optional and will be empty dict
        result = generic_calling.show_call_recipient_choices(recipient_choices)
        self.assertEqual(result["status"], "success")
        self.assertIn("choices", result)

    def test_show_call_recipient_choices_missing_endpoints(self):
        """Test show_call_recipient_choices with missing endpoints."""
        recipient_choices = [{"recipient_info": {"name": "Test User"}}]
        self.assert_error_behavior(
            generic_calling.show_call_recipient_choices,
            ContactNotFoundError,
            "No phone numbers available to show.",
            recipient_choices=recipient_choices
        )

    def test_show_call_recipient_not_found_with_valid_name(self):
        """Test show_call_recipient_not_found_or_specified with valid name."""
        result = generic_calling.show_call_recipient_not_found_or_specified("John Doe")
        self.assertEqual(result["status"], "success")

    def test_show_call_recipient_not_found_with_empty_string(self):
        """Test show_call_recipient_not_found_or_specified with empty string."""
        self.assert_error_behavior(
            generic_calling.show_call_recipient_not_found_or_specified,
            ValidationError,
            "name must not be empty.",
            name=""
        )

    def test_make_call_whatsapp_with_speakerphone(self):
        """Test make_call with WhatsApp profile and speakerphone."""
        endpoint = {"type": "WHATSAPP_PROFILE", "value": self.contact_alice_jid}
        recipient_info = {"name": "Alice"}
        result = generic_calling.make_call(endpoint, recipient_info, on_speakerphone=True)
        self.assertEqual(result['status'], 'success')
        self.assertIn('call_id', result)

    def test_make_call_phone_with_video_call_forced_whatsapp(self):
        """Test make_call with phone number but video_call=True forces WhatsApp."""
        endpoint = {"type": "PHONE_NUMBER", "value": "+14155552671"}
        recipient_info = {"name": "John Doe"}
        result = generic_calling.make_call(endpoint, recipient_info, video_call=True)
        self.assertEqual(result['status'], 'success')
        self.assertIn('call_id', result)

    @patch('generic_calling.generic_calling.whatsapp_make_call')
    def test_make_call_whatsapp_exception_handling(self, mock_whatsapp_call):
        """Test make_call WhatsApp exception handling."""
        # Mock WhatsApp call to raise an exception
        mock_whatsapp_call.side_effect = Exception("WhatsApp service error")
        
        endpoint = {"type": "WHATSAPP_PROFILE", "value": self.contact_alice_jid}
        recipient_info = {"name": "Alice"}
        
        with self.assertRaises(Exception) as context:
            generic_calling.make_call(endpoint, recipient_info)
        
        self.assertEqual(str(context.exception), "WhatsApp service error")
        mock_whatsapp_call.assert_called_once()

    @patch('generic_calling.generic_calling.phone_make_call')
    def test_make_call_phone_exception_handling(self, mock_phone_call):
        """Test make_call phone exception handling."""
        # Mock phone call to raise an exception
        mock_phone_call.side_effect = Exception("Phone service error")
        
        endpoint = {"type": "PHONE_NUMBER", "value": "+14155552671"}
        recipient_info = {"name": "John Doe"}
        
        with self.assertRaises(Exception) as context:
            generic_calling.make_call(endpoint, recipient_info)
        
        self.assertEqual(str(context.exception), "Phone service error")
        mock_phone_call.assert_called_once()

    @patch('generic_calling.generic_calling.phone_show_call_recipient_choices')
    def test_show_call_recipient_choices_exception_handling(self, mock_phone_choices):
        """Test show_call_recipient_choices exception handling."""
        # Mock phone service to raise an exception
        mock_phone_choices.side_effect = Exception("Phone service error")
        
        recipient_choices = [{
            "recipient_info": {"name": "Test User"},
            "endpoints": [{"type": "PHONE_NUMBER", "value": "+14155552671"}]
        }]
        
        with self.assertRaises(Exception) as context:
            generic_calling.show_call_recipient_choices(recipient_choices)
        
        self.assertEqual(str(context.exception), "Phone service error")
        mock_phone_choices.assert_called_once()

    @patch('generic_calling.generic_calling.phone_show_call_recipient_not_found')
    def test_show_call_recipient_not_found_exception_handling(self, mock_phone_not_found):
        """Test show_call_recipient_not_found_or_specified exception handling"""
        # Mock phone service to raise an exception
        mock_phone_not_found.side_effect = Exception("Phone service error")
        
        with self.assertRaises(Exception) as context:
            generic_calling.show_call_recipient_not_found_or_specified("John Doe")
        
        self.assertEqual(str(context.exception), "Phone service error")
        mock_phone_not_found.assert_called_once_with(contact_name="John Doe")
    
    def test_make_call_with_video_call(self):
        """Test make_call with video_call set to True."""
        endpoint = {"type": "PHONE_NUMBER", "value": "+14155552671"}
        recipient_info = {"name": "John Doe"}
        result = generic_calling.make_call(endpoint, recipient_info, video_call=True)
        self.assertEqual(result["status"], "success")
        self.assertIn("call_id", result)
    
    def test_make_call_with_video_call_not_bool_failure(self):
        """Test make_call with video_call set to a non-boolean value."""
        self.assert_error_behavior(
            generic_calling.make_call,
            ValidationError,
            "Both on_speakerphone and video_call should be bool values.",
            endpoint={"type": "PHONE_NUMBER", "value": "+14155552671"}, recipient_info={"name": "John Doe"}, video_call="True"
        )

if __name__ == '__main__':
    unittest.main()
