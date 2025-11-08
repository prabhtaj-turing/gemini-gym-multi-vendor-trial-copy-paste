import unittest
from pydantic import ValidationError
from ..SimulationEngine.custom_errors import (
    InvalidRecipientError,
    InvalidEndpointError,
    InvalidMediaAttachmentError
)
from ..SimulationEngine.models import (
    Endpoint,
    Recipient,
    MediaAttachment,
    Observation,
    Action,
    APIName,
    validate_send,
    validate_show_recipient_choices,
    validate_ask_for_message_body
)
from common_utils.base_case import BaseTestCaseWithErrorHandler as BaseCase


class TestEndpointModel(BaseCase):
    """Test Endpoint model validation."""

    def test_endpoint_invalid_type_value(self):
        """Test Endpoint with invalid type value (not PHONE_NUMBER or WHATSAPP_PROFILE)."""
        with self.assertRaises(ValidationError):
            Endpoint(type="EMAIL", value="+1234567890", label="personal")

    def test_endpoint_empty_value(self):
        """Test Endpoint with empty value."""
        with self.assertRaises((ValidationError, InvalidEndpointError)):
            Endpoint(type="PHONE_NUMBER", value="", label="mobile")

    def test_endpoint_whitespace_only_value(self):
        """Test Endpoint with whitespace-only value."""
        with self.assertRaises((ValidationError, InvalidEndpointError)):
            Endpoint(type="PHONE_NUMBER", value="   ", label="mobile")
    
    def test_endpoint_phone_number_valid_e164(self):
        """Test Endpoint with valid E.164 phone number."""
        endpoint = Endpoint(type="PHONE_NUMBER", value="+14155552671", label="mobile")
        self.assertEqual(endpoint.value, "+14155552671")
        self.assertEqual(endpoint.type, "PHONE_NUMBER")
    
    def test_endpoint_phone_number_invalid_no_plus(self):
        """Test Endpoint with phone number missing + prefix."""
        with self.assertRaises((ValidationError, InvalidEndpointError)) as context:
            Endpoint(type="PHONE_NUMBER", value="14155552671", label="mobile")
        self.assertIn("E.164 format", str(context.exception))
    
    def test_endpoint_phone_number_invalid_too_short(self):
        """Test Endpoint with phone number too short for E.164."""
        with self.assertRaises((ValidationError, InvalidEndpointError)) as context:
            Endpoint(type="PHONE_NUMBER", value="+1", label="mobile")
        self.assertIn("E.164 format", str(context.exception))
    
    def test_endpoint_phone_number_invalid_too_long(self):
        """Test Endpoint with phone number too long for E.164 (>15 digits)."""
        with self.assertRaises((ValidationError, InvalidEndpointError)) as context:
            Endpoint(type="PHONE_NUMBER", value="+12345678901234567", label="mobile")
        self.assertIn("E.164 format", str(context.exception))
    
    def test_endpoint_phone_number_invalid_starts_with_zero(self):
        """Test Endpoint with phone number starting with 0 after +."""
        with self.assertRaises((ValidationError, InvalidEndpointError)) as context:
            Endpoint(type="PHONE_NUMBER", value="+01234567890", label="mobile")
        self.assertIn("E.164 format", str(context.exception))
    
    def test_endpoint_phone_number_invalid_contains_letters(self):
        """Test Endpoint with phone number containing letters."""
        with self.assertRaises((ValidationError, InvalidEndpointError)) as context:
            Endpoint(type="PHONE_NUMBER", value="+1415ABC2671", label="mobile")
        self.assertIn("E.164 format", str(context.exception))
    
    def test_endpoint_whatsapp_valid_jid(self):
        """Test Endpoint with valid WhatsApp JID."""
        endpoint = Endpoint(type="WHATSAPP_PROFILE", value="14155552671@s.whatsapp.net")
        self.assertEqual(endpoint.value, "14155552671@s.whatsapp.net")
        self.assertEqual(endpoint.type, "WHATSAPP_PROFILE")
    
    def test_endpoint_whatsapp_invalid_missing_domain(self):
        """Test Endpoint with WhatsApp JID missing domain."""
        with self.assertRaises((ValidationError, InvalidEndpointError)) as context:
            Endpoint(type="WHATSAPP_PROFILE", value="14155552671")
        self.assertIn("JID format", str(context.exception))
    
    def test_endpoint_whatsapp_invalid_wrong_domain(self):
        """Test Endpoint with WhatsApp JID with wrong domain."""
        with self.assertRaises((ValidationError, InvalidEndpointError)) as context:
            Endpoint(type="WHATSAPP_PROFILE", value="14155552671@c.us")
        self.assertIn("JID format", str(context.exception))
    
    def test_endpoint_whatsapp_invalid_has_plus_prefix(self):
        """Test Endpoint with WhatsApp JID incorrectly having + prefix."""
        with self.assertRaises((ValidationError, InvalidEndpointError)) as context:
            Endpoint(type="WHATSAPP_PROFILE", value="+14155552671@s.whatsapp.net")
        self.assertIn("JID format", str(context.exception))


class TestRecipientModel(BaseCase):
    """Test Recipient model validation."""

    def test_recipient_empty_name(self):
        """Test Recipient with empty name."""
        with self.assertRaises((ValidationError, InvalidRecipientError)):
            Recipient(
                name="",
                endpoints=[{"type": "PHONE_NUMBER", "value": "+1234567890"}]
            )

    def test_recipient_whitespace_only_name(self):
        """Test Recipient with whitespace-only name."""
        with self.assertRaises((ValidationError, InvalidRecipientError)):
            Recipient(
                name="   ",
                endpoints=[{"type": "PHONE_NUMBER", "value": "+1234567890"}]
            )

    def test_recipient_empty_endpoints_list(self):
        """Test Recipient with empty endpoints list."""
        with self.assertRaises((ValidationError, InvalidRecipientError)):
            Recipient(name="John Doe", endpoints=[])

    def test_recipient_non_list_endpoints(self):
        """Test Recipient with non-list endpoints."""
        with self.assertRaises((ValidationError, InvalidRecipientError)):
            Recipient(name="John Doe", endpoints="not a list")


class TestMediaAttachmentModel(BaseCase):
    """Test MediaAttachment model validation."""

    def test_media_attachment_empty_media_id(self):
        """Test MediaAttachment with empty media_id."""
        with self.assertRaises((ValidationError, InvalidMediaAttachmentError)):
            MediaAttachment(
                media_id="",
                media_type="IMAGE",
                source="IMAGE_UPLOAD"
            )

    def test_media_attachment_whitespace_media_id(self):
        """Test MediaAttachment with whitespace-only media_id."""
        with self.assertRaises((ValidationError, InvalidMediaAttachmentError)):
            MediaAttachment(
                media_id="   ",
                media_type="IMAGE",
                source="IMAGE_UPLOAD"
            )


class TestObservationModel(BaseCase):
    """Test Observation model."""

    def test_observation_basic_fields(self):
        """Test Observation model with basic fields."""
        obs = Observation(
            status="success",
            sent_message_id="msg_123",
            action_card_content_passthrough=None
        )
        self.assertEqual(obs.status, "success")
        self.assertEqual(obs.sent_message_id, "msg_123")
        self.assertIsNone(obs.action_card_content_passthrough)


class TestActionModel(BaseCase):
    """Test Action model with timestamp validation."""

    def test_action_with_timestamp(self):
        """Test Action model with valid timestamp."""
        action = Action(
            action_type=APIName.SEND,
            inputs={"contact_name": "John Doe"},
            outputs={"status": "success"},
            metadata={},
            timestamp="2025-10-12T10:00:00"
        )
        self.assertEqual(action.action_type, APIName.SEND)
        self.assertEqual(action.timestamp, "2025-10-12T10:00:00")

    def test_action_invalid_timestamp(self):
        """Test Action with invalid timestamp format."""
        with self.assertRaises(ValidationError):
            Action(
                action_type=APIName.SEND,
                inputs={},
                outputs={},
                timestamp="invalid-timestamp"
            )


class TestValidationFunctions(BaseCase):
    """Test validation helper functions."""

    def test_validate_send_non_dict_endpoint(self):
        """Test validate_send with non-dict endpoint."""
        with self.assertRaises(InvalidEndpointError):
            validate_send(
                contact_name="John Doe",
                endpoint="not a dict",
                body="Hello"
            )

    def test_validate_send_non_string_body(self):
        """Test validate_send with non-string body."""
        from ..SimulationEngine.custom_errors import MessageBodyRequiredError
        with self.assertRaises(MessageBodyRequiredError):
            validate_send(
                contact_name="John Doe",
                endpoint={"type": "PHONE_NUMBER", "value": "+1234567890"},
                body=123
            )

    def test_validate_send_non_list_media_attachments(self):
        """Test validate_send with non-list media_attachments."""
        with self.assertRaises(InvalidMediaAttachmentError):
            validate_send(
                contact_name="John Doe",
                endpoint={"type": "PHONE_NUMBER", "value": "+1234567890"},
                body="Hello",
                media_attachments="not a list"
            )

    def test_validate_show_recipient_choices_non_list(self):
        """Test validate_show_recipient_choices with non-list input."""
        with self.assertRaises(InvalidRecipientError):
            validate_show_recipient_choices("not a list")

    def test_validate_show_recipient_choices_empty_list(self):
        """Test validate_show_recipient_choices with empty list."""
        with self.assertRaises(InvalidRecipientError):
            validate_show_recipient_choices([])

    def test_validate_ask_for_message_body_empty_name(self):
        """Test validate_ask_for_message_body with empty contact name."""
        with self.assertRaises(InvalidRecipientError):
            validate_ask_for_message_body(
                contact_name="",
                endpoint={"type": "PHONE_NUMBER", "value": "+1234567890"}
            )

    def test_validate_ask_for_message_body_non_dict_endpoint(self):
        """Test validate_ask_for_message_body with non-dict endpoint."""
        with self.assertRaises(InvalidEndpointError):
            validate_ask_for_message_body(
                contact_name="John Doe",
                endpoint="not a dict"
            )


class TestAPINameEnum(BaseCase):
    """Test APIName enum."""

    def test_api_name_enum_values(self):
        """Test that APIName enum has expected values."""
        self.assertEqual(APIName.SEND, "send")
        self.assertEqual(APIName.SHOW_MESSAGE_RECIPIENT_CHOICES, "show_message_recipient_choices")
        self.assertEqual(APIName.ASK_FOR_MESSAGE_BODY, "ask_for_message_body")
        self.assertEqual(APIName.SHOW_MESSAGE_RECIPIENT_NOT_FOUND_OR_SPECIFIED, "show_message_recipient_not_found_or_specified")


if __name__ == "__main__":
    unittest.main()

