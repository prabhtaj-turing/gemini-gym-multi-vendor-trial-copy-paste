import unittest
import copy
from ..SimulationEngine.custom_errors import InvalidRecipientError
from common_utils.base_case import BaseTestCaseWithErrorHandler as BaseCase
import generic_messages
from messages.SimulationEngine.db import DB as MESSAGES_DB


class TestShowRecipientChoices(BaseCase):
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
        self.valid_recipients = [
            {
                "name": "John Doe",
                "endpoints": [
                    {
                        "type": "PHONE_NUMBER",
                        "value": "+14155552671",
                        "label": "mobile"
                    }
                ]
            },
            {
                "name": "Jane Smith",
                "endpoints": [
                    {
                        "type": "PHONE_NUMBER",
                        "value": "+14155552672",
                        "label": "work"
                    }
                ]
            }
        ]

        self.recipient_with_multiple_endpoints = [
            {
                "name": "Robert Johnson",
                "endpoints": [
                    {
                        "type": "PHONE_NUMBER",
                        "value": "+1555123456",
                        "label": "mobile"
                    },
                    {
                        "type": "PHONE_NUMBER",
                        "value": "+1555987654",
                        "label": "home"
                    }
                ]
            }
        ]

    def tearDown(self):
        """Restore original database state."""
        MESSAGES_DB.clear()
        MESSAGES_DB.update(self._original_messages_db)
        super().tearDown()

    def test_show_recipient_choices_success(self):
        """Test successful display of recipient choices through messages service."""
        result = generic_messages.show_message_recipient_choices(
            recipients=self.valid_recipients
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "choices_displayed")
        self.assertIsNone(result["sent_message_id"])
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIsNone(result["action_card_content_passthrough"])

    def test_show_recipient_choices_multiple_endpoints(self):
        """Test displaying choices for recipient with multiple endpoints."""
        result = generic_messages.show_message_recipient_choices(
            recipients=self.recipient_with_multiple_endpoints
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "choices_displayed")

    def test_show_recipient_choices_empty_list(self):
        """Test showing recipient choices with empty list."""
        self.assert_error_behavior(
            generic_messages.show_message_recipient_choices,
            ValueError,
            "recipients list cannot be empty",
            recipients=[]
        )

    def test_show_recipient_choices_invalid_type(self):
        """Test showing recipient choices with invalid type."""
        self.assert_error_behavior(
            generic_messages.show_message_recipient_choices,
            TypeError,
            "recipients must be a list, got str",
            recipients="invalid"
        )

    def test_show_recipient_choices_missing_name(self):
        """Test showing recipient choices with missing name."""
        invalid_recipients = [
            {
                "endpoints": [
                    {
                        "type": "PHONE_NUMBER",
                        "value": "+14155552671"
                    }
                ]
            }
        ]
        # Should raise one of these exceptions
        with self.assertRaises((InvalidRecipientError, ValueError, KeyError)):
            generic_messages.show_message_recipient_choices(
                recipients=invalid_recipients
            )


if __name__ == "__main__":
    unittest.main()
