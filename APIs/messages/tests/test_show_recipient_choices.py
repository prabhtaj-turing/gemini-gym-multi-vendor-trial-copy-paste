import unittest
from ..SimulationEngine.custom_errors import InvalidRecipientError
from common_utils.base_case import BaseTestCaseWithErrorHandler as BaseCase
import messages


class TestShowRecipientChoices(BaseCase):
    def setUp(self):
        super().setUp()
        self.valid_recipients = [
            {
                "contact_id": "contact_1",
                "contact_name": "John Doe",
                "contact_endpoints": [
                    {
                        "endpoint_type": "PHONE_NUMBER",
                        "endpoint_value": "+14155552671",
                        "endpoint_label": "mobile"
                    }
                ],
                "contact_photo_url": "https://example.com/photo1.jpg"
            },
            {
                "contact_id": "contact_2",
                "contact_name": "Jane Smith",
                "contact_endpoints": [
                    {
                        "endpoint_type": "PHONE_NUMBER",
                        "endpoint_value": "+14155552671",
                        "endpoint_label": "work"
                    }
                ],
                "contact_photo_url": "https://example.com/photo2.jpg"
            }
        ]
        self.message_body = "Hello everyone!"

    def test_show_recipient_choices_success(self):
        """Test successful display of recipient choices."""
        result = messages.show_message_recipient_choices(
            recipients=self.valid_recipients,
            message_body=self.message_body
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "choices_displayed")
        self.assertIsNone(result["sent_message_id"])
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIsNone(result["action_card_content_passthrough"])

    def test_show_recipient_choices_empty_recipients(self):
        """Test showing choices with empty recipients list."""
        self.assert_error_behavior(
            messages.show_message_recipient_choices,
            ValueError,
            "recipients list cannot be empty",
            recipients=[]
        )

    def test_show_recipient_choices_no_recipients(self):
        """Test showing choices without recipients."""
        self.assert_error_behavior(
            messages.show_message_recipient_choices,
            TypeError,
            "recipients must be a list, got NoneType",
            recipients=None
        )

    def test_show_recipient_choices_invalid_recipients_type(self):
        """Test showing choices with invalid recipients type."""
        self.assert_error_behavior(
            messages.show_message_recipient_choices,
            TypeError,
            "recipients must be a list, got str",
            recipients="invalid"
        )

    def test_show_recipient_choices_invalid_message_body_type(self):
        """Test showing choices with invalid message body type."""
        self.assert_error_behavior(
            messages.show_message_recipient_choices,
            TypeError,
            "message_body must be a string or None, got int",
            recipients=self.valid_recipients,
            message_body=123
        )

    def test_show_recipient_choices_without_message_body(self):
        """Test showing choices without message body."""
        result = messages.show_message_recipient_choices(
            recipients=self.valid_recipients
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "choices_displayed")
        self.assertIsNone(result["sent_message_id"])
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIsNone(result["action_card_content_passthrough"])


if __name__ == '__main__':
    unittest.main() 