#!/usr/bin/env python3
"""
Comprehensive test cases for the show_call_recipient_not_found_or_specified function.
Tests all scenarios including valid calls, error conditions, edge cases, and validation.
"""

import unittest
import sys
import os
import time
from unittest.mock import patch, MagicMock

from .. import show_call_recipient_not_found_or_specified
from common_utils.base_case import BaseTestCaseWithErrorHandler
from phone.SimulationEngine.db import DB, DEFAULT_DB_PATH

class TestShowCallRecipientNotFound(BaseTestCaseWithErrorHandler):
    """Comprehensive test cases for show_call_recipient_not_found_or_specified function."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear the database to ensure clean state for each test
        import json
        
        # Clear all data from DB
        DB.clear()
        
        # Reinitialize with default data
        with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
            default_data = json.load(f)
        
        # Only load the static data (contacts, businesses, special_contacts)
        static_data = {
            "contacts": default_data.get("contacts", {}),
            "businesses": default_data.get("businesses", {}),
            "special_contacts": default_data.get("special_contacts", {})
        }
        DB.update(static_data)
        
        # Initialize empty dynamic collections
        DB["call_history"] = {}
        DB["prepared_calls"] = {}
        DB["recipient_choices"] = {}
        DB["not_found_records"] = {}
        DB["actions"] = []

    def test_show_not_found_with_contact_name(self):
        """Test show_call_recipient_not_found_or_specified with a contact name."""
        contact_name = "John Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertIn("call_id", result)
        self.assertTrue(len(result["call_id"]) > 0)
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_without_contact_name(self):
        """Test show_call_recipient_not_found_or_specified without a contact name."""
        result = show_call_recipient_not_found_or_specified()
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "success")
        self.assertIn("call_id", result)
        self.assertTrue(len(result["call_id"]) > 0)
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn("need to know who you'd like to call", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_empty_string_contact_name(self):
        """Test show_call_recipient_not_found_or_specified with empty string contact name."""
        result = show_call_recipient_not_found_or_specified(contact_name="")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        # Empty string is treated as None, so it should show the generic message
        self.assertIn("need to know who you'd like to call", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_whitespace_contact_name(self):
        """Test show_call_recipient_not_found_or_specified with whitespace-only contact name."""
        result = show_call_recipient_not_found_or_specified(contact_name="   ")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn("couldn't find a contact or business named '   '", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_special_characters_contact_name(self):
        """Test show_call_recipient_not_found_or_specified with special characters in contact name."""
        special_name = "John@Doe#123"
        result = show_call_recipient_not_found_or_specified(contact_name=special_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{special_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_unicode_contact_name(self):
        """Test show_call_recipient_not_found_or_specified with unicode characters in contact name."""
        unicode_name = "José María"
        result = show_call_recipient_not_found_or_specified(contact_name=unicode_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{unicode_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_long_contact_name(self):
        """Test show_call_recipient_not_found_or_specified with very long contact name."""
        long_name = "A" * 1000  # Very long name
        result = show_call_recipient_not_found_or_specified(contact_name=long_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{long_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_numeric_contact_name(self):
        """Test show_call_recipient_not_found_or_specified with numeric contact name."""
        numeric_name = "12345"
        result = show_call_recipient_not_found_or_specified(contact_name=numeric_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{numeric_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_business_name(self):
        """Test show_call_recipient_not_found_or_specified with business name."""
        business_name = "Acme Corporation"
        result = show_call_recipient_not_found_or_specified(contact_name=business_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{business_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_phone_number_as_name(self):
        """Test show_call_recipient_not_found_or_specified with phone number as contact name."""
        phone_as_name = "+1234567890"
        result = show_call_recipient_not_found_or_specified(contact_name=phone_as_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{phone_as_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_call_id_uniqueness(self):
        """Test that show_call_recipient_not_found_or_specified generates unique call IDs."""
        result1 = show_call_recipient_not_found_or_specified(contact_name="Contact 1")
        result2 = show_call_recipient_not_found_or_specified(contact_name="Contact 2")
        
        self.assertNotEqual(result1["call_id"], result2["call_id"])

    def test_show_not_found_database_integration(self):
        """Test that show_call_recipient_not_found_or_specified properly updates the database."""
                
        initial_not_found_count = len(DB.get("not_found_records", {}))
        
        contact_name = "Database Test Contact"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        final_not_found_count = len(DB.get("not_found_records", {}))
        self.assertEqual(final_not_found_count, initial_not_found_count + 1)
        
        # Verify the not found record was added
        not_found_record = DB["not_found_records"].get(result["call_id"])
        self.assertIsNotNone(not_found_record)
        self.assertEqual(not_found_record["contact_name"], contact_name)

    def test_show_not_found_database_integration_no_name(self):
        """Test database integration when no contact name is provided."""
                
        initial_not_found_count = len(DB.get("not_found_records", {}))
        
        result = show_call_recipient_not_found_or_specified()
        
        final_not_found_count = len(DB.get("not_found_records", {}))
        self.assertEqual(final_not_found_count, initial_not_found_count + 1)
        
        # Verify the not found record was added with None contact_name
        not_found_record = DB["not_found_records"].get(result["call_id"])
        self.assertIsNotNone(not_found_record)
        self.assertIsNone(not_found_record["contact_name"])

    def test_show_not_found_message_variations(self):
        """Test different message variations based on contact name presence."""
        # With contact name
        result_with_name = show_call_recipient_not_found_or_specified(contact_name="Test Contact")
        self.assertIn("couldn't find a contact or business named 'Test Contact'", result_with_name["templated_tts"])
        self.assertIn("Could you please provide more details or check the spelling?", result_with_name["templated_tts"])
        
        # Without contact name
        result_without_name = show_call_recipient_not_found_or_specified()
        self.assertIn("need to know who you'd like to call", result_without_name["templated_tts"])
        self.assertIn("Could you please specify a name, phone number, or business?", result_without_name["templated_tts"])

    def test_show_not_found_with_none_contact_name(self):
        """Test show_call_recipient_not_found_or_specified with None contact name."""
        result = show_call_recipient_not_found_or_specified(contact_name=None)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn("need to know who you'd like to call", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_consistent_response_structure(self):
        """Test that show_call_recipient_not_found_or_specified returns consistent response structure."""
        result = show_call_recipient_not_found_or_specified(contact_name="Test Contact")
        
        # Check all required fields are present
        required_fields = ["status", "call_id", "emitted_action_count", "templated_tts", "action_card_content_passthrough"]
        for field in required_fields:
            self.assertIn(field, result)
        
        # Check field types
        self.assertIsInstance(result["status"], str)
        self.assertIsInstance(result["call_id"], str)
        self.assertIsInstance(result["emitted_action_count"], int)
        self.assertIsInstance(result["templated_tts"], str)
        self.assertIsInstance(result["action_card_content_passthrough"], str)
        
        # Check specific values
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_case_sensitive_contact_name(self):
        """Test show_call_recipient_not_found_or_specified with case-sensitive contact name."""
        contact_name = "John DOE"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_quotes(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing quotes."""
        contact_name = "John \"Johnny\" Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_apostrophe(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing apostrophe."""
        contact_name = "O'Connor"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_newlines(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing newlines."""
        contact_name = "John\nDoe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_tabs(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing tabs."""
        contact_name = "John\tDoe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_backslashes(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing backslashes."""
        contact_name = "John\\Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_forward_slashes(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing forward slashes."""
        contact_name = "John/Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_periods(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing periods."""
        contact_name = "Dr. John Doe Jr."
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_commas(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing commas."""
        contact_name = "Doe, John"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_parentheses(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing parentheses."""
        contact_name = "John (Johnny) Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_brackets(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing brackets."""
        contact_name = "John [Johnny] Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_braces(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing braces."""
        contact_name = "John {Johnny} Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_angle_brackets(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing angle brackets."""
        contact_name = "John <Johnny> Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_ampersand(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing ampersand."""
        contact_name = "John & Jane Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_plus_sign(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing plus sign."""
        contact_name = "John + Jane Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_equal_sign(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing equal sign."""
        contact_name = "John = Jane Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_at_symbol(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing @ symbol."""
        contact_name = "john@example.com"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_hash_symbol(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing # symbol."""
        contact_name = "John #1 Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_dollar_sign(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing $ symbol."""
        contact_name = "John $ Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_percent_sign(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing % symbol."""
        contact_name = "John % Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_caret(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing ^ symbol."""
        contact_name = "John ^ Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_asterisk(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing * symbol."""
        contact_name = "John * Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_exclamation_mark(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing ! symbol."""
        contact_name = "John! Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_question_mark(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing ? symbol."""
        contact_name = "John? Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_colon(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing : symbol."""
        contact_name = "John: Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_semicolon(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing ; symbol."""
        contact_name = "John; Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_pipe(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing | symbol."""
        contact_name = "John | Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")

    def test_show_not_found_with_contact_name_containing_tilde(self):
        """Test show_call_recipient_not_found_or_specified with contact name containing ~ symbol."""
        contact_name = "John ~ Doe"
        result = show_call_recipient_not_found_or_specified(contact_name=contact_name)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["emitted_action_count"], 0)
        self.assertIn(f"couldn't find a contact or business named '{contact_name}'", result["templated_tts"])
        self.assertEqual(result["action_card_content_passthrough"], "Recipient not found or not specified")


if __name__ == "__main__":
    unittest.main() 