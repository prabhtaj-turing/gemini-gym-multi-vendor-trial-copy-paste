import unittest
import copy
import tempfile
import os
from ..SimulationEngine.custom_errors import (
    MessageBodyRequiredError, 
    InvalidRecipientError,
    InvalidEndpointError,
    InvalidMediaAttachmentError
)
from common_utils.base_case import BaseTestCaseWithErrorHandler as BaseCase
import generic_messages
from messages.SimulationEngine.db import DB as MESSAGES_DB
from whatsapp.SimulationEngine.db import DB as WHATSAPP_DB


class TestSend(BaseCase):
    def setUp(self):
        """
        Set up the test environment before each test.
        Initializes real databases for messages and whatsapp services.
        """
        super().setUp()
        
        # Save original database states
        self._original_messages_db = copy.deepcopy(MESSAGES_DB)
        self._original_whatsapp_db = copy.deepcopy(WHATSAPP_DB)
        
        # Initialize messages DB
        MESSAGES_DB.clear()
        MESSAGES_DB['messages'] = {}
        MESSAGES_DB['message_history'] = []
        MESSAGES_DB['counters'] = {'message': 0, 'recipient': 0, 'media_attachment': 0}
        MESSAGES_DB['recipients'] = {}
        
        # Initialize whatsapp DB
        WHATSAPP_DB.clear()
        WHATSAPP_DB['actions'] = []
        WHATSAPP_DB['contacts'] = {}
        WHATSAPP_DB['chats'] = {}
        WHATSAPP_DB['current_user_jid'] = "0000000000@s.whatsapp.net"

        # Define valid test data
        self.valid_contact_name = "John Doe"
        self.valid_endpoint_sms = {
            "type": "PHONE_NUMBER",
            "value": "+14155552671",
            "label": "mobile"
        }
        self.valid_endpoint_whatsapp = {
            "type": "WHATSAPP_PROFILE",
            "value": "14155552671@s.whatsapp.net",  # JID format without + prefix
            "label": "whatsapp"
        }
        self.valid_body = "Hello, this is a test message!"
        self.valid_media_attachments = [
            {
                "media_id": "https://example.com/image.jpg",
                "media_type": "IMAGE",
                "source": "IMAGE_UPLOAD"
            }
        ]

    def tearDown(self):
        """Restore original database states."""
        MESSAGES_DB.clear()
        MESSAGES_DB.update(self._original_messages_db)
        WHATSAPP_DB.clear()
        WHATSAPP_DB.update(self._original_whatsapp_db)
        super().tearDown()

    def test_send_sms_success(self):
        """Test successful SMS message sending through messages service."""
        result = generic_messages.send(
            contact_name=self.valid_contact_name,
            endpoint=self.valid_endpoint_sms,
            body=self.valid_body
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertIn("sent_message_id", result)
        self.assertEqual(result["emitted_action_count"], 1)
        
        # Verify message was stored in messages database
        message_id = result["sent_message_id"]
        self.assertIn(message_id, MESSAGES_DB['messages'])
        stored_message = MESSAGES_DB['messages'][message_id]
        self.assertEqual(stored_message['message_body'], self.valid_body)

    def test_send_whatsapp_success(self):
        """Test successful WhatsApp message sending through whatsapp service."""
        # Setup WhatsApp contact - must match the JID format exactly
        contact_jid = "14155552671@s.whatsapp.net"
        
        # Store contact with the exact JID as key (WhatsApp expects this format)
        WHATSAPP_DB['contacts'][contact_jid] = {
            "resourceName": f"people/{contact_jid}",
            "names": [{"givenName": self.valid_contact_name}],
            "phoneNumbers": [{"value": "14155552671", "type": "mobile"}],
            "whatsapp": {
                "jid": contact_jid,
                "phone_number": "14155552671",
                "name_in_address_book": self.valid_contact_name,
                "is_whatsapp_user": True
            }
        }
        
        # Create or ensure chat exists
        WHATSAPP_DB['chats'][contact_jid] = {
            "jid": contact_jid,
            "chat_jid": contact_jid,
            "name": self.valid_contact_name,
            "is_group": False,
            "messages": []
        }
        
        result = generic_messages.send(
            contact_name=self.valid_contact_name,
            endpoint=self.valid_endpoint_whatsapp,
            body=self.valid_body
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertIsNotNone(result.get("sent_message_id"))
        
        # Verify message was stored in WhatsApp chat
        chat = WHATSAPP_DB['chats'][contact_jid]
        self.assertGreater(len(chat['messages']), 0)
        sent_message = chat['messages'][-1]
        # WhatsApp uses 'text_content' field for message text
        self.assertEqual(sent_message['text_content'], self.valid_body)

    def test_send_whatsapp_with_media_success(self):
        """Test successful WhatsApp message with media attachments.
        
        WhatsApp media is now supported through generic_messages using
        whatsapp.send_file() and whatsapp.send_audio_message().
        """
        # Create a temporary image file for testing
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'fake image data')
            temp_image_path = temp_file.name
        
        try:
            # Setup WhatsApp contact - must match the JID format exactly
            contact_jid = "14155552671@s.whatsapp.net"
            
            # Store contact with the resourceName key format (WhatsApp expects this format)
            resource_name_key = f"people/{contact_jid}"
            WHATSAPP_DB['contacts'][resource_name_key] = {
                "resourceName": resource_name_key,
                "names": [{"givenName": self.valid_contact_name}],
                "phoneNumbers": [{"value": "14155552671", "type": "mobile"}],
                "whatsapp": {
                    "jid": contact_jid,
                    "phone_number": "14155552671",
                    "name_in_address_book": self.valid_contact_name,
                    "is_whatsapp_user": True
                }
            }
            
            # Create or ensure chat exists
            WHATSAPP_DB['chats'][contact_jid] = {
                "jid": contact_jid,
                "chat_jid": contact_jid,
                "name": self.valid_contact_name,
                "is_group": False,
                "messages": []
            }
            
            # Create media attachment with actual file path
            media_attachments = [{
                "media_id": temp_image_path,
                "media_type": "IMAGE",
                "source": "IMAGE_UPLOAD"
            }]
            
            result = generic_messages.send(
                contact_name=self.valid_contact_name,
                endpoint=self.valid_endpoint_whatsapp,
                body=self.valid_body,
                media_attachments=media_attachments
            )
            
            # Verify the result
            self.assertIsInstance(result, dict)
            self.assertEqual(result["status"], "success")
            self.assertIn("sent_message_id", result)
            self.assertEqual(result["emitted_action_count"], 1)
            
            # Verify media was sent via WhatsApp
            chat = WHATSAPP_DB['chats'][contact_jid]
            self.assertGreater(len(chat['messages']), 0)
            
            # With the new implementation, we send both media and text
            # So we should have at least 2 messages: media + text
            self.assertGreaterEqual(len(chat['messages']), 2)
            
            # Find the media message (should have media_info)
            media_message = None
            text_message = None
            for message in chat['messages']:
                if message.get('media_info') is not None:
                    media_message = message
                elif message.get('text_content') is not None:
                    text_message = message
            
            # Verify media message was sent
            self.assertIsNotNone(media_message, "Media message should be present")
            self.assertIsNotNone(media_message['media_info'])
            self.assertIsNone(media_message['media_info']['caption'])
            
            # Verify text message was also sent
            self.assertIsNotNone(text_message, "Text message should be present")
            self.assertEqual(text_message['text_content'], self.valid_body)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_image_path):
                os.unlink(temp_image_path)

    def test_send_whatsapp_with_audio_media(self):
        """Test successful WhatsApp message with audio media attachment."""
        # Create a temporary audio file for testing
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(b'fake audio data')
            temp_audio_path = temp_file.name
        
        try:
            # Setup WhatsApp contact
            contact_jid = "14155552671@s.whatsapp.net"
            
            # Store contact with the resourceName key format (WhatsApp expects this format)
            resource_name_key = f"people/{contact_jid}"
            WHATSAPP_DB['contacts'][resource_name_key] = {
                "resourceName": resource_name_key,
                "names": [{"givenName": self.valid_contact_name}],
                "phoneNumbers": [{"value": "14155552671", "type": "mobile"}],
                "whatsapp": {
                    "jid": contact_jid,
                    "phone_number": "14155552671",
                    "name_in_address_book": self.valid_contact_name,
                    "is_whatsapp_user": True
                }
            }
            
            # Create or ensure chat exists
            WHATSAPP_DB['chats'][contact_jid] = {
                "jid": contact_jid,
                "chat_jid": contact_jid,
                "name": self.valid_contact_name,
                "is_group": False,
                "messages": []
            }
            
            # Create audio media attachment with actual file path
            audio_media_attachments = [{
                "media_id": temp_audio_path,
                "media_type": "AUDIO",
                "source": "IMAGE_UPLOAD"
            }]
            
            result = generic_messages.send(
                contact_name=self.valid_contact_name,
                endpoint=self.valid_endpoint_whatsapp,
                body="Check out this audio!",
                media_attachments=audio_media_attachments
            )
            
            # Verify the result
            self.assertIsInstance(result, dict)
            self.assertEqual(result["status"], "success")
            self.assertIn("sent_message_id", result)
            self.assertEqual(result["emitted_action_count"], 1)
            
            # Verify audio was sent via WhatsApp
            chat = WHATSAPP_DB['chats'][contact_jid]
            self.assertGreater(len(chat['messages']), 0)
            
            # With the new implementation, we send both audio and text
            # So we should have at least 2 messages: audio + text
            self.assertGreaterEqual(len(chat['messages']), 2)
            
            # Find the audio message (should have media_info)
            audio_message = None
            text_message = None
            for message in chat['messages']:
                if message.get('media_info') is not None:
                    audio_message = message
                elif message.get('text_content') is not None:
                    text_message = message
            
            # Verify audio message was sent
            self.assertIsNotNone(audio_message, "Audio message should be present")
            self.assertIsNotNone(audio_message['media_info'])
            # Audio messages don't have captions in WhatsApp
            
            # Verify text message was also sent
            self.assertIsNotNone(text_message, "Text message should be present")
            self.assertEqual(text_message['text_content'], "Check out this audio!")
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_audio_path):
                os.unlink(temp_audio_path)

    def test_send_with_media_attachments(self):
        """Test sending message with media attachments."""
        result = generic_messages.send(
            contact_name=self.valid_contact_name,
            endpoint=self.valid_endpoint_sms,
            body=self.valid_body,
            media_attachments=self.valid_media_attachments
        )
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        
        # Verify media was stored
        message_id = result["sent_message_id"]
        stored_message = MESSAGES_DB['messages'][message_id]
        self.assertEqual(len(stored_message['media_attachments']), 1)
        self.assertEqual(stored_message['media_attachments'][0]['media_id'], "https://example.com/image.jpg")

    def test_send_empty_body_with_media(self):
        """Test sending message with empty body but with media attachments.
        
        Note: Both SMS and WhatsApp now allow empty body when media is provided.
        The message is sent successfully with just the media attachments.
        """
        result = generic_messages.send(
            contact_name=self.valid_contact_name,
            endpoint=self.valid_endpoint_sms,
            body="",
            media_attachments=self.valid_media_attachments
        )
        
        # Verify the result is successful
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertIn("sent_message_id", result)
        self.assertEqual(result["emitted_action_count"], 1)
        
        # Verify media was stored in messages database
        message_id = result["sent_message_id"]
        stored_message = MESSAGES_DB['messages'][message_id]
        self.assertEqual(len(stored_message['media_attachments']), 1)
        # Body should be None or empty (messages service normalizes empty string to None)
        self.assertTrue(stored_message['message_body'] is None or stored_message['message_body'] == "")

    def test_send_empty_body_no_media(self):
        """Test sending message with empty body and no media."""
        self.assert_error_behavior(
            generic_messages.send,
            MessageBodyRequiredError,
            "both body and media_attachments cannot be empty",
            contact_name=self.valid_contact_name,
            endpoint=self.valid_endpoint_sms,
            body=""
        )

    def test_send_no_contact_name(self):
        """Test sending message without contact name."""
        self.assert_error_behavior(
            generic_messages.send,
            InvalidRecipientError,
            "contact_name cannot be empty",
            contact_name="",
            endpoint=self.valid_endpoint_sms,
            body=self.valid_body
        )

    def test_send_invalid_contact_name_type(self):
        """Test sending message with invalid contact name type."""
        self.assert_error_behavior(
            generic_messages.send,
            TypeError,
            "contact_name must be a string, got int",
            contact_name=123,
            endpoint=self.valid_endpoint_sms,
            body=self.valid_body
        )

    def test_send_invalid_endpoint_type(self):
        """Test sending message with invalid endpoint type."""
        self.assert_error_behavior(
            generic_messages.send,
            TypeError,
            "endpoint must be a dict, got str",
            contact_name=self.valid_contact_name,
            endpoint="invalid",
            body=self.valid_body
        )

    def test_send_invalid_body_type(self):
        """Test sending message with invalid body type."""
        self.assert_error_behavior(
            generic_messages.send,
            TypeError,
            "body must be a string or None, got int",
            contact_name=self.valid_contact_name,
            endpoint=self.valid_endpoint_sms,
            body=123
        )

    def test_send_invalid_media_attachments_type(self):
        """Test sending message with invalid media attachments type."""
        self.assert_error_behavior(
            generic_messages.send,
            TypeError,
            "media_attachments must be a list or None, got str",
            contact_name=self.valid_contact_name,
            endpoint=self.valid_endpoint_sms,
            body=self.valid_body,
            media_attachments="invalid"
        )

    def test_send_unsupported_endpoint_type(self):
        """Test send with unsupported endpoint type (defensive check).
        
        This tests the defensive code at line 145 that handles endpoint types
        that are neither PHONE_NUMBER nor WHATSAPP_PROFILE. Under normal
        circumstances, this is unreachable due to Pydantic validation.
        """
        from unittest.mock import MagicMock, patch
        
        # Create a mock endpoint with unsupported type
        mock_endpoint = MagicMock()
        mock_endpoint.type = "EMAIL"
        mock_endpoint.value = "test@example.com"
        mock_endpoint.label = "personal"
        
        mock_validated_data = {
            "contact_name": "John Doe",
            "endpoint": mock_endpoint,
            "body": "Test message",
            "media_attachments": None
        }
        
        with patch('generic_messages.message_controller.validate_send', return_value=mock_validated_data):
            # Just check that InvalidEndpointError is raised
            with self.assertRaises(InvalidEndpointError) as context:
                generic_messages.send(
                    contact_name="John Doe",
                    endpoint={"type": "EMAIL", "value": "test@example.com"},
                    body="Test message"
                )
            # Verify error message contains expected text
            self.assertIn("Unsupported endpoint type", str(context.exception))

    def test_send_exception_reraise_whitespace_name(self):
        """Test that validation exceptions are properly re-raised."""
        # Test InvalidRecipientError with whitespace-only name
        with self.assertRaises(InvalidRecipientError):
            generic_messages.send(
                contact_name="   ",
                endpoint={"type": "PHONE_NUMBER", "value": "+1234567890"},
                body="Test"
            )

    def test_send_exception_reraise_whitespace_body(self):
        """Test MessageBodyRequiredError with whitespace-only body."""
        from ..SimulationEngine.custom_errors import MessageBodyRequiredError
        with self.assertRaises(MessageBodyRequiredError):
            generic_messages.send(
                contact_name="John Doe",
                endpoint={"type": "PHONE_NUMBER", "value": "+1234567890"},
                body="  "
            )


if __name__ == "__main__":
    unittest.main()
