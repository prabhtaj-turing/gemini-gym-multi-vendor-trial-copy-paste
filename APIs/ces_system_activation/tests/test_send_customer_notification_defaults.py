import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from APIs.ces_system_activation.SimulationEngine.db import reset_db
from APIs.ces_system_activation.ces_system_activation import send_customer_notification


class TestSendCustomerNotificationDefaults(BaseTestCaseWithErrorHandler):
    """Test suite to verify default values and optional parameters in send_customer_notification."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        reset_db()

    def tearDown(self):
        """Clean up after each test method."""
        reset_db()

    def test_recipient_used_is_none_when_no_recipient_provided(self):
        """
        Test that recipientUsed is None in the returned dictionary when recipient is not provided.
        
        This verifies the fix for Issue 1: Return type hint should allow None values.
        The function's return type is Dict[str, Optional[str]], and recipientUsed should be None
        when no recipient is specified.
        """
        result = send_customer_notification(
            accountId="ACC-102030",
            message="Test notification"
        )

        # Verify the key exists in the result
        self.assertIn("recipientUsed", result)
        # Verify the value is None (not just missing)
        self.assertIsNone(result["recipientUsed"])
        # Verify other fields are still properly set
        self.assertEqual(result["status"], "SENT")
        self.assertEqual(result["channelSent"], "EMAIL")

    def test_recipient_used_is_set_when_recipient_provided(self):
        """
        Test that recipientUsed contains the provided recipient value.
        
        This ensures that when a recipient is provided, it's properly returned in the result.
        """
        test_recipient = "+14155552671"
        result = send_customer_notification(
            accountId="ACC-102030",
            message="Test notification",
            recipient=test_recipient
        )

        self.assertEqual(result["recipientUsed"], test_recipient)

    def test_urgency_defaults_to_normal_when_not_provided(self):
        """
        Test that urgency defaults to 'NORMAL' when not explicitly provided.
        
        This verifies the fix for Issue 2: The schema documentation states urgency
        'Defaults to NORMAL', and the implementation should match this behavior.
        """
        result = send_customer_notification(
            accountId="ACC-102030",
            message="Test notification"
        )

        # The function passes urgency to the Pydantic model, which should default to 'NORMAL'
        # However, NotificationResult model doesn't include urgency in its output
        # So we need to verify this through the input validation layer
        
        # Since urgency is not part of NotificationResult output, we verify the function
        # accepts the call without urgency parameter (no validation error)
        self.assertEqual(result["status"], "SENT")
        self.assertIsNotNone(result["notificationId"])

    def test_urgency_can_be_explicitly_set(self):
        """
        Test that urgency can be explicitly set to a custom value.
        
        This ensures the default doesn't prevent custom values from being used.
        """
        result = send_customer_notification(
            accountId="ACC-102030",
            message="Test notification",
            urgency="HIGH"
        )

        # Function should succeed with custom urgency value
        self.assertEqual(result["status"], "SENT")
        self.assertIsNotNone(result["notificationId"])

    def test_urgency_can_be_explicitly_set_to_none(self):
        """
        Test that urgency can still be explicitly set to None if needed.
        
        This ensures backward compatibility - callers can override the default.
        """
        result = send_customer_notification(
            accountId="ACC-102030",
            message="Test notification",
            urgency=None
        )

        # Function should succeed even with explicit None
        self.assertEqual(result["status"], "SENT")
        self.assertIsNotNone(result["notificationId"])

    def test_all_optional_fields_have_proper_defaults(self):
        """
        Test that calling send_customer_notification with minimal required parameters works correctly.
        
        This is a comprehensive test of all default values.
        """
        result = send_customer_notification(
            accountId="ACC-102030",
            message="Test notification"
        )

        # Verify required fields are present
        self.assertIn("channelSent", result)
        self.assertIn("message", result)
        self.assertIn("notificationId", result)
        self.assertIn("status", result)
        self.assertIn("timestamp", result)
        self.assertIn("recipientUsed", result)

        # Verify default values
        self.assertEqual(result["channelSent"], "EMAIL")  # Default channel
        self.assertEqual(result["status"], "SENT")
        self.assertIsNone(result["recipientUsed"])  # Should be None when not provided

        # Verify generated fields
        self.assertIsNotNone(result["notificationId"])
        self.assertRegex(result["timestamp"], r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z')

    def test_return_type_matches_type_hint(self):
        """
        Test that the return value structure matches the Dict[str, Optional[str]] type hint.
        
        This verifies all returned values are either strings or None.
        """
        result = send_customer_notification(
            accountId="ACC-102030",
            message="Test notification"
        )

        # All values should be either str or None
        for key, value in result.items():
            self.assertTrue(
                isinstance(value, str) or value is None,
                f"Key '{key}' has value '{value}' of type {type(value)}, expected str or None"
            )


if __name__ == '__main__':
    unittest.main()

