import unittest
import copy
from common_utils.base_case import BaseTestCaseWithErrorHandler as BaseCase
import generic_messages
from messages.SimulationEngine.db import DB as MESSAGES_DB
from whatsapp.SimulationEngine.db import DB as WHATSAPP_DB


class TestServiceRouting(BaseCase):
    """Test that generic_messages correctly routes to appropriate underlying services."""

    def setUp(self):
        """Set up test environment with real databases."""
        super().setUp()
        
        # Save original states
        self._original_messages_db = copy.deepcopy(MESSAGES_DB)
        self._original_whatsapp_db = copy.deepcopy(WHATSAPP_DB)
        
        # Initialize messages DB
        MESSAGES_DB.clear()
        MESSAGES_DB['messages'] = {}
        MESSAGES_DB['counters'] = {'message': 0}
        MESSAGES_DB['recipients'] = {}
        
        # Initialize whatsapp DB
        WHATSAPP_DB.clear()
        WHATSAPP_DB['actions'] = []
        WHATSAPP_DB['contacts'] = {}
        WHATSAPP_DB['chats'] = {}
        WHATSAPP_DB['current_user_jid'] = "0000000000@s.whatsapp.net"

    def tearDown(self):
        """Restore original states."""
        MESSAGES_DB.clear()
        MESSAGES_DB.update(self._original_messages_db)
        WHATSAPP_DB.clear()
        WHATSAPP_DB.update(self._original_whatsapp_db)
        super().tearDown()

    def test_sms_routes_to_messages_service(self):
        """Test that SMS endpoint routes to messages service."""
        result = generic_messages.send(
            contact_name="Test User",
            endpoint={
                "type": "PHONE_NUMBER",
                "value": "+14155552671",
                "label": "mobile"
            },
            body="Test message"
        )
        
        # Verify result came from messages service
        self.assertEqual(result["status"], "success")
        self.assertIn("sent_message_id", result)
        
        # Verify message was stored in messages DB (not whatsapp)
        message_id = result["sent_message_id"]
        self.assertIn(message_id, MESSAGES_DB['messages'])
        
        # Verify whatsapp DB is empty
        self.assertEqual(len(WHATSAPP_DB['chats']), 0)

    def test_whatsapp_routes_to_whatsapp_service(self):
        """Test that WhatsApp endpoint routes to whatsapp service."""
        # Setup WhatsApp contact with correct database structure
        contact_jid = "14155552671@s.whatsapp.net"
        
        # Store contact with JID as key (not people/JID)
        WHATSAPP_DB['contacts'][contact_jid] = {
            "resourceName": f"people/{contact_jid}",
            "names": [{"givenName": "Test User"}],
            "whatsapp": {
                "jid": contact_jid,
                "phone_number": "14155552671",
                "is_whatsapp_user": True
            }
        }
        WHATSAPP_DB['chats'][contact_jid] = {
            "jid": contact_jid,
            "chat_jid": contact_jid,
            "name": "Test User",
            "is_group": False,
            "messages": []
        }
        
        result = generic_messages.send(
            contact_name="Test User",
            endpoint={
                "type": "WHATSAPP_PROFILE",
                "value": contact_jid,
                "label": "whatsapp"
            },
            body="Test message"
        )
        
        # Verify result came from whatsapp service
        self.assertEqual(result["status"], "success")
        
        # Verify message was stored in whatsapp chat (not messages)
        chat = WHATSAPP_DB['chats'][contact_jid]
        self.assertGreater(len(chat['messages']), 0)
        
        # Verify messages DB has no messages
        self.assertEqual(len(MESSAGES_DB['messages']), 0)

    def test_both_services_can_be_used_in_sequence(self):
        """Test that both services can be used in the same test session."""
        # Send SMS
        sms_result = generic_messages.send(
            contact_name="SMS User",
            endpoint={
                "type": "PHONE_NUMBER",
                "value": "+14155552671",
                "label": "mobile"
            },
            body="SMS message"
        )
        
        # Setup for WhatsApp - store contact with JID as key
        contact_jid = "14155552672@s.whatsapp.net"
        WHATSAPP_DB['contacts'][contact_jid] = {
            "resourceName": f"people/{contact_jid}",
            "names": [{"givenName": "WhatsApp User"}],
            "whatsapp": {"jid": contact_jid, "is_whatsapp_user": True}
        }
        WHATSAPP_DB['chats'][contact_jid] = {
            "jid": contact_jid,
            "chat_jid": contact_jid,
            "name": "WhatsApp User",
            "is_group": False,
            "messages": []
        }
        
        # Send WhatsApp
        wa_result = generic_messages.send(
            contact_name="WhatsApp User",
            endpoint={
                "type": "WHATSAPP_PROFILE",
                "value": contact_jid,
                "label": "whatsapp"
            },
            body="WhatsApp message"
        )
        
        # Verify both succeeded
        self.assertEqual(sms_result["status"], "success")
        self.assertEqual(wa_result["status"], "success")
        
        # Verify they went to different services
        self.assertEqual(len(MESSAGES_DB['messages']), 1)
        self.assertGreater(len(WHATSAPP_DB['chats'][contact_jid]['messages']), 0)

    def test_ui_operations_route_to_messages_service(self):
        """Test that UI operations (show choices, ask body) route to messages service."""
        # Test show_message_recipient_choices
        recipients = [
            {
                "name": "John Doe",
                "endpoints": [
                    {"type": "PHONE_NUMBER", "value": "+14155552671", "label": "mobile"}
                ]
            }
        ]
        result = generic_messages.show_message_recipient_choices(recipients=recipients)
        self.assertEqual(result["status"], "choices_displayed")
        
        # Test ask_for_message_body
        result = generic_messages.ask_for_message_body(
            contact_name="John Doe",
            endpoint={"type": "PHONE_NUMBER", "value": "+14155552671", "label": "mobile"}
        )
        self.assertEqual(result["status"], "asking_for_message_body")
        
        # Test show_message_recipient_not_found_or_specified
        result = generic_messages.show_message_recipient_not_found_or_specified(
            contact_name="Unknown"
        )
        self.assertEqual(result["status"], "recipient_not_found")


if __name__ == "__main__":
    unittest.main()

