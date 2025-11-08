import unittest
import copy
from common_utils.base_case import BaseTestCaseWithErrorHandler as BaseCase
import generic_messages
from messages.SimulationEngine.db import DB as MESSAGES_DB


class TestRecipientNotFound(BaseCase):
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

    def tearDown(self):
        """Restore original database state."""
        MESSAGES_DB.clear()
        MESSAGES_DB.update(self._original_messages_db)
        super().tearDown()

    def test_recipient_not_found_with_name(self):
        """Test showing recipient not found with a contact name through messages service."""
        result = generic_messages.show_message_recipient_not_found_or_specified(
            contact_name="John Doe"
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "recipient_not_found")
        self.assertIsNone(result["sent_message_id"])
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIsNone(result["action_card_content_passthrough"])

    def test_recipient_not_found_without_name(self):
        """Test showing recipient not found without a contact name."""
        result = generic_messages.show_message_recipient_not_found_or_specified(
            contact_name=None
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "recipient_not_found")

    def test_recipient_not_found_no_args(self):
        """Test showing recipient not found with no arguments."""
        result = generic_messages.show_message_recipient_not_found_or_specified()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "recipient_not_found")

    def test_recipient_not_found_invalid_type(self):
        """Test showing recipient not found with invalid contact name type."""
        self.assert_error_behavior(
            generic_messages.show_message_recipient_not_found_or_specified,
            TypeError,
            "contact_name must be a string or None, got int",
            contact_name=123
        )

    def test_recipient_not_found_empty_string_normalized(self):
        """Test that empty string is normalized to None."""
        result = generic_messages.show_message_recipient_not_found_or_specified(
            contact_name=""
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "recipient_not_found")
        # Should behave the same as passing None
        
    def test_recipient_not_found_whitespace_string_normalized(self):
        """Test that whitespace-only string is normalized to None."""
        result = generic_messages.show_message_recipient_not_found_or_specified(
            contact_name="   "
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "recipient_not_found")
        # Should behave the same as passing None


if __name__ == "__main__":
    unittest.main()
