import unittest
from ..SimulationEngine.custom_errors import InvalidRecipientError
from common_utils.base_case import BaseTestCaseWithErrorHandler as BaseCase
import messages


class TestAskForMessageBody(BaseCase):
    def setUp(self):
        super().setUp()
        self.valid_recipient = {
            "contact_id": "contact_1",
            "contact_name": "John Doe",
            "contact_endpoints": [
                {
                    "endpoint_type": "PHONE_NUMBER",
                    "endpoint_value": "+14155552671",
                    "endpoint_label": "mobile"
                }
            ],
            "contact_photo_url": "https://example.com/photo.jpg"
        }

    def test_ask_for_message_body_success(self):
        """Test successful ask for message body."""
        result = messages.ask_for_message_body(recipient=self.valid_recipient)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "asking_for_message_body")
        self.assertIsNone(result["sent_message_id"])
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIsNone(result["action_card_content_passthrough"])

    def test_ask_for_message_body_no_recipient(self):
        """Test asking for message body without recipient."""
        self.assert_error_behavior(
            messages.ask_for_message_body,
            InvalidRecipientError,
            "recipient is required and cannot be None",
            recipient=None
        )

    def test_ask_for_message_body_invalid_recipient_type(self):
        """Test asking for message body with invalid recipient type."""
        self.assert_error_behavior(
            messages.ask_for_message_body,
            TypeError,
            "recipient must be a dict or Recipient object, got int",
            recipient=123
        )

    def test_ask_for_message_body_invalid_recipient_data(self):
        """Test asking for message body with invalid recipient data."""
        invalid_recipient = {
            "contact_name": "",  # Empty name should fail validation
            "contact_endpoints": []
        }
        
        self.assert_error_behavior(
            messages.ask_for_message_body,
            InvalidRecipientError,
            "Invalid recipient data: 2 validation errors for Recipient\ncontact_name\n  Value error, contact_name is required and cannot be empty [type=value_error, input_value='', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/value_error\ncontact_endpoints\n  Value error, contact_endpoints must be a non-empty list [type=value_error, input_value=[], input_type=list]\n    For further information visit https://errors.pydantic.dev/2.11/v/value_error",
            recipient=invalid_recipient
        )


if __name__ == '__main__':
    unittest.main() 