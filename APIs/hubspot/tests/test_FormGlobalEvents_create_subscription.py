import unittest
from unittest.mock import patch
import uuid
from pydantic import ValidationError
from hubspot.SimulationEngine.db import DB
from hubspot.FormGlobalEvents import create_subscription
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestCreateSubscription(BaseTestCaseWithErrorHandler):
    """Test cases for the create_subscription function with Pydantic validation."""

    def setUp(self):
        """Setup method to prepare for each test."""
        # Clear the subscriptions DB before each test
        DB.update({
            "subscriptions": {},
            "subscription_definitions": []
        })

    def test_create_subscription_success_with_all_fields(self):
        """Test successful subscription creation with all fields provided."""
        endpoint = "https://example.com/webhook"
        subscription_details = {
            "contact_id": "contact-123",
            "subscribed": True,
            "opt_in_date": "2024-01-15T10:30:00Z"
        }

        result = create_subscription(endpoint, subscription_details)

        # Verify return structure
        self.assertIn("id", result)
        self.assertIsInstance(result["id"], str)
        self.assertEqual(result["endpoint"], endpoint)
        self.assertEqual(result["active"], True)
        
        # Verify subscriptionDetails structure
        returned_details = result["subscriptionDetails"]
        self.assertEqual(returned_details["contact_id"], "contact-123")
        self.assertEqual(returned_details["subscribed"], True)
        self.assertEqual(returned_details["opt_in_date"], "2024-01-15T10:30:00Z")
        self.assertEqual(returned_details["subscription_id"], result["id"])
        
        # Verify data is stored in DB
        self.assertIn(result["id"], DB["subscriptions"])
        self.assertEqual(DB["subscriptions"][result["id"]], result)

    def test_create_subscription_success_with_optional_fields_none(self):
        """Test successful subscription creation with optional fields as None."""
        endpoint = None
        subscription_details = {
            "contact_id": "contact-456",
            "subscribed": False,
            "opt_in_date": None
        }

        result = create_subscription(endpoint, subscription_details)

        # Verify return structure
        self.assertIn("id", result)
        self.assertIsNone(result["endpoint"])
        self.assertEqual(result["active"], True)
        
        # Verify subscriptionDetails structure
        returned_details = result["subscriptionDetails"]
        self.assertEqual(returned_details["contact_id"], "contact-456")
        self.assertEqual(returned_details["subscribed"], False)
        self.assertIsNone(returned_details["opt_in_date"])
        self.assertEqual(returned_details["subscription_id"], result["id"])

    def test_create_subscription_success_minimal_required_fields(self):
        """Test successful subscription creation with only required fields."""
        subscription_details = {
            "contact_id": "contact-789",
            "subscribed": True
        }

        result = create_subscription(None, subscription_details)

        # Verify return structure
        self.assertIn("id", result)
        self.assertIsNone(result["endpoint"])
        self.assertEqual(result["active"], True)
        
        # Verify subscriptionDetails structure
        returned_details = result["subscriptionDetails"]
        self.assertEqual(returned_details["contact_id"], "contact-789")
        self.assertEqual(returned_details["subscribed"], True)
        self.assertIsNone(returned_details["opt_in_date"])

    def test_create_subscription_completely_empty(self):
        """Test successful subscription creation with completely empty/None values."""
        result = create_subscription(None, None)

        # Verify return structure
        self.assertIn("id", result)
        self.assertIsNone(result["endpoint"])
        self.assertEqual(result["active"], True)
        
        # Verify subscriptionDetails structure - should contain subscription_id and None values for optional fields
        returned_details = result["subscriptionDetails"]
        self.assertEqual(returned_details["subscription_id"], result["id"])
        # Pydantic includes optional fields with None values in model_dump()
        self.assertIsNone(returned_details["contact_id"])
        self.assertIsNone(returned_details["subscribed"])
        self.assertIsNone(returned_details["opt_in_date"])

    def test_create_subscription_empty_subscription_details(self):
        """Test successful subscription creation with empty subscription details dict."""
        result = create_subscription("https://example.com/webhook", {})

        # Verify return structure
        self.assertIn("id", result)
        self.assertEqual(result["endpoint"], "https://example.com/webhook")
        self.assertEqual(result["active"], True)
        
        # Verify subscriptionDetails structure - should contain subscription_id and None values for optional fields
        returned_details = result["subscriptionDetails"]
        self.assertEqual(returned_details["subscription_id"], result["id"])
        # Pydantic includes optional fields with None values in model_dump()
        self.assertIsNone(returned_details["contact_id"])
        self.assertIsNone(returned_details["subscribed"])
        self.assertIsNone(returned_details["opt_in_date"])

    def test_create_subscription_partial_fields(self):
        """Test successful subscription creation with only some optional fields provided."""
        subscription_details = {
            "contact_id": "contact-456",
            # subscribed and opt_in_date are omitted
        }

        result = create_subscription("https://example.com/webhook", subscription_details)

        # Verify return structure
        self.assertIn("id", result)
        self.assertEqual(result["endpoint"], "https://example.com/webhook")
        self.assertEqual(result["active"], True)
        
        # Verify subscriptionDetails structure
        returned_details = result["subscriptionDetails"]
        self.assertEqual(returned_details["contact_id"], "contact-456")
        self.assertEqual(returned_details["subscription_id"], result["id"])
        # Pydantic includes optional fields with None values even when not provided
        self.assertIsNone(returned_details["subscribed"])
        self.assertIsNone(returned_details["opt_in_date"])

    def test_create_subscription_missing_contact_id(self):
        """Test behavior when contact_id is missing - should succeed since all fields are optional."""
        subscription_details = {
            "subscribed": True,
            "opt_in_date": "2024-01-15T10:30:00Z"
        }

        # This should now succeed since all fields are optional
        result = create_subscription("https://example.com/webhook", subscription_details)
        
        # Verify it succeeded and contact_id is None
        self.assertIn("id", result)
        returned_details = result["subscriptionDetails"]
        self.assertIsNone(returned_details["contact_id"])  # Should be None, not missing
        self.assertEqual(returned_details["subscribed"], True)

    def test_create_subscription_missing_subscribed(self):
        """Test behavior when subscribed field is missing - should succeed since all fields are optional."""
        subscription_details = {
            "contact_id": "contact-123",
            "opt_in_date": "2024-01-15T10:30:00Z"
        }

        # This should now succeed since all fields are optional
        result = create_subscription("https://example.com/webhook", subscription_details)
        
        # Verify it succeeded and subscribed is None
        self.assertIn("id", result)
        returned_details = result["subscriptionDetails"]
        self.assertEqual(returned_details["contact_id"], "contact-123")
        self.assertIsNone(returned_details["subscribed"])  # Should be None, not missing

    def test_create_subscription_invalid_contact_id_type(self):
        """Test validation error when contact_id is not a string."""
        subscription_details = {
            "contact_id": 123,  # Should be string
            "subscribed": True,
            "opt_in_date": "2024-01-15T10:30:00Z"
        }

        self.assert_error_behavior(
            create_subscription,
            ValidationError,
            "contact_id\n  Input should be a valid string",
            None,
            "https://example.com/webhook",
            subscription_details
        )

    def test_create_subscription_invalid_subscribed_type(self):
        """Test validation error when subscribed is not a boolean."""
        subscription_details = {
            "contact_id": "contact-123",
            "subscribed": "invalid_boolean",  # Should be boolean, not convertible string
            "opt_in_date": "2024-01-15T10:30:00Z"
        }

        self.assert_error_behavior(
            create_subscription,
            ValidationError,
            "subscribed\n  Input should be a valid boolean",
            None,
            "https://example.com/webhook",
            subscription_details
        )

    def test_create_subscription_pydantic_boolean_conversion(self):
        """Test that Pydantic converts string 'true' to boolean True (expected behavior)."""
        subscription_details = {
            "contact_id": "contact-123",
            "subscribed": "true",  # Pydantic converts this to boolean True
            "opt_in_date": "2024-01-15T10:30:00Z"
        }

        result = create_subscription("https://example.com/webhook", subscription_details)

        # Verify that Pydantic converted the string to boolean
        self.assertEqual(result["subscriptionDetails"]["subscribed"], True)
        self.assertIsInstance(result["subscriptionDetails"]["subscribed"], bool)

    def test_create_subscription_invalid_endpoint_type(self):
        """Test validation error when endpoint is not a string or None."""
        subscription_details = {
            "contact_id": "contact-123",
            "subscribed": True,
            "opt_in_date": "2024-01-15T10:30:00Z"
        }

        self.assert_error_behavior(
            create_subscription,
            ValidationError,
            "endpoint\n  Input should be a valid string",
            None,
            123,  # Should be string or None
            subscription_details
        )

    def test_create_subscription_invalid_opt_in_date_type(self):
        """Test validation error when opt_in_date is not a string or None."""
        subscription_details = {
            "contact_id": "contact-123",
            "subscribed": True,
            "opt_in_date": 123456789  # Should be string or None
        }

        self.assert_error_behavior(
            create_subscription,
            ValidationError,
            "opt_in_date\n  Input should be a valid string",
            None,
            "https://example.com/webhook",
            subscription_details
        )

    def test_create_subscription_empty_contact_id(self):
        """Test behavior when contact_id is empty string.
        
        Note: Currently this passes validation since Pydantic allows empty strings.
        Consider adding custom validation in the future if empty contact_id should be rejected.
        """
        subscription_details = {
            "contact_id": "",  # Empty string
            "subscribed": True,
            "opt_in_date": "2024-01-15T10:30:00Z"
        }

        # This currently succeeds with Pydantic's default string validation
        result = create_subscription("https://example.com/webhook", subscription_details)
        
        # Verify the function completed successfully but contact_id is empty
        self.assertEqual(result["subscriptionDetails"]["contact_id"], "")
        self.assertIn("id", result)
        self.assertEqual(result["active"], True)

    def test_create_subscription_invalid_subscription_details_type(self):
        """Test validation error when subscriptionDetails is not a dict."""
        self.assert_error_behavior(
            create_subscription,
            ValidationError,
            "subscriptionDetails\n  Input should be a valid dictionary",
            None,
            "https://example.com/webhook",
            "invalid_subscription_details"  # Should be dict
        )

    def test_create_subscription_generates_unique_ids(self):
        """Test that multiple subscriptions get unique IDs."""
        subscription_details_1 = {
            "contact_id": "contact-1",
            "subscribed": True
        }
        subscription_details_2 = {
            "contact_id": "contact-2",
            "subscribed": False
        }

        result1 = create_subscription("https://example.com/webhook1", subscription_details_1)
        result2 = create_subscription("https://example.com/webhook2", subscription_details_2)

        # Verify IDs are different
        self.assertNotEqual(result1["id"], result2["id"])
        
        # Verify both are in DB
        self.assertIn(result1["id"], DB["subscriptions"])
        self.assertIn(result2["id"], DB["subscriptions"])
        self.assertEqual(len(DB["subscriptions"]), 2)

    def test_create_subscription_subscription_id_matches_main_id(self):
        """Test that subscription_id in subscriptionDetails matches the main id."""
        subscription_details = {
            "contact_id": "contact-123",
            "subscribed": True,
            "opt_in_date": "2024-01-15T10:30:00Z"
        }

        result = create_subscription("https://example.com/webhook", subscription_details)

        # Verify that subscription_id matches the main id
        self.assertEqual(result["id"], result["subscriptionDetails"]["subscription_id"])

    @patch('hubspot.FormGlobalEvents.uuid.uuid4')
    def test_create_subscription_uses_uuid_for_id(self, mock_uuid):
        """Test that the function uses uuid.uuid4() to generate IDs."""
        mock_uuid.return_value.hex = "test-uuid-123"
        mock_uuid.return_value.__str__ = lambda x: "test-uuid-123"
        
        subscription_details = {
            "contact_id": "contact-123",
            "subscribed": True
        }

        result = create_subscription("https://example.com/webhook", subscription_details)

        # Verify uuid.uuid4 was called
        mock_uuid.assert_called_once()
        self.assertEqual(result["id"], "test-uuid-123")

    def test_create_subscription_preserves_input_data(self):
        """Test that the function doesn't modify the original input data."""
        original_endpoint = "https://example.com/webhook"
        original_subscription_details = {
            "contact_id": "contact-123",
            "subscribed": True,
            "opt_in_date": "2024-01-15T10:30:00Z"
        }
        
        # Create copies to compare later
        endpoint_copy = original_endpoint
        subscription_details_copy = original_subscription_details.copy()

        result = create_subscription(original_endpoint, original_subscription_details)

        # Verify original data wasn't modified
        self.assertEqual(original_endpoint, endpoint_copy)
        self.assertEqual(original_subscription_details, subscription_details_copy)
        
        # Verify the function didn't add subscription_id to the original input
        self.assertNotIn("subscription_id", original_subscription_details)

    def test_create_subscription_preserves_extra_fields(self):
        """Test that extra fields in subscriptionDetails are preserved."""
        subscription_details = {
            "contact_id": "contact-123",
            "subscribed": True,
            "opt_in_date": "2024-01-15T10:30:00Z",
            "subscriptionType": "form.submission",  # Extra field
            "customField": "custom_value",          # Another extra field
            "priority": "high"                      # Yet another extra field
        }

        result = create_subscription("https://example.com/webhook", subscription_details)

        # Verify all fields are preserved in the result
        returned_details = result["subscriptionDetails"]
        self.assertEqual(returned_details["contact_id"], "contact-123")
        self.assertEqual(returned_details["subscribed"], True)
        self.assertEqual(returned_details["opt_in_date"], "2024-01-15T10:30:00Z")
        self.assertEqual(returned_details["subscription_id"], result["id"])
        
        # Verify extra fields are preserved
        self.assertEqual(returned_details["subscriptionType"], "form.submission")
        self.assertEqual(returned_details["customField"], "custom_value")
        self.assertEqual(returned_details["priority"], "high")


if __name__ == '__main__':
    unittest.main() 