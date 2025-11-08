import unittest
import copy
from ..SimulationEngine.custom_errors import InvalidRecipientError, InvalidEndpointError
from common_utils.base_case import BaseTestCaseWithErrorHandler as BaseCase
import generic_messages
from messages.SimulationEngine.db import DB as MESSAGES_DB


class TestAskForMessageBody(BaseCase):
    def setUp(self):
        """
        Set up the test environment before each test.
        """
        super().setUp()
        
        # Save and initialize messages DB
        self._original_messages_db = copy.deepcopy(MESSAGES_DB)
        MESSAGES_DB.clear()
        MESSAGES_DB['messages'] = {}
        MESSAGES_DB['recipients'] = {}

        # Define valid test data
        self.valid_contact_name = "John Doe"
        self.valid_endpoint = {
            "type": "PHONE_NUMBER",
            "value": "+14155552671",
            "label": "mobile"
        }

    def tearDown(self):
        """Restore original database state."""
        MESSAGES_DB.clear()
        MESSAGES_DB.update(self._original_messages_db)
        super().tearDown()

    def test_ask_for_message_body_success(self):
        """Test successful request for message body through messages service."""
        result = generic_messages.ask_for_message_body(
            contact_name=self.valid_contact_name,
            endpoint=self.valid_endpoint
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "asking_for_message_body")
        self.assertIsNone(result["sent_message_id"])
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIsNone(result["action_card_content_passthrough"])

    def test_ask_for_message_body_whatsapp(self):
        """Test asking for message body for WhatsApp endpoint.
        
        Note: The messages service only accepts PHONE_NUMBER endpoints,
        so WhatsApp endpoints will be rejected by the underlying service.
        """
        from messages.SimulationEngine.custom_errors import InvalidRecipientError as MessagesInvalidRecipientError
        
        whatsapp_endpoint = {
            "type": "WHATSAPP_PROFILE",
            "value": "14155552671@s.whatsapp.net",
            "label": "whatsapp"
        }
        
        # The underlying messages service will reject WHATSAPP_PROFILE endpoints
        with self.assertRaises(MessagesInvalidRecipientError):
            generic_messages.ask_for_message_body(
                contact_name=self.valid_contact_name,
                endpoint=whatsapp_endpoint
            )

    def test_ask_for_message_body_no_contact_name(self):
        """Test asking for message body without contact name."""
        self.assert_error_behavior(
            generic_messages.ask_for_message_body,
            InvalidRecipientError,
            "contact_name cannot be empty",
            contact_name="",
            endpoint=self.valid_endpoint
        )

    def test_ask_for_message_body_invalid_contact_name_type(self):
        """Test asking for message body with invalid contact name type."""
        self.assert_error_behavior(
            generic_messages.ask_for_message_body,
            TypeError,
            "contact_name must be a string, got int",
            contact_name=123,
            endpoint=self.valid_endpoint
        )

    def test_ask_for_message_body_invalid_endpoint_type(self):
        """Test asking for message body with invalid endpoint type."""
        self.assert_error_behavior(
            generic_messages.ask_for_message_body,
            TypeError,
            "endpoint must be a dict, got str",
            contact_name=self.valid_contact_name,
            endpoint="invalid"
        )

    def test_ask_for_message_body_missing_endpoint_type(self):
        """Test asking for message body with missing endpoint type."""
        invalid_endpoint = {
            "value": "+14155552671"
        }
        # Should raise one of these exceptions
        with self.assertRaises((InvalidEndpointError, ValueError, KeyError)):
            generic_messages.ask_for_message_body(
                contact_name=self.valid_contact_name,
                endpoint=invalid_endpoint
            )


if __name__ == "__main__":
    unittest.main()
