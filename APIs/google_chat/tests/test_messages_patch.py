"""
Comprehensive test cases for the messages patch function.

This module provides exhaustive test coverage for the patch function including
input validation, Pydantic validation, functional behavior, and edge cases.
"""

import unittest
import sys
import os

# Add the APIs directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from google_chat.Spaces.Messages import patch
from google_chat.SimulationEngine.db import DB


class TestMessagesPatch(unittest.TestCase):
    """Test cases for messages patch function with comprehensive coverage."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Save original DB state
        self.original_messages = DB["Message"].copy() if "Message" in DB else []
        
        # Clear DB for clean testing
        DB["Message"] = []
    
    def tearDown(self):
        """Clean up after tests."""
        # Restore original DB state
        DB["Message"] = self.original_messages
    
    # Input Validation Tests
    def test_input_validation_name_none(self):
        """Test that None name parameter returns empty dict."""
        result = patch(None, "text", True, {"text": "test"})
        self.assertEqual(result, {})
    
    def test_input_validation_name_wrong_type(self):
        """Test that non-string name parameter returns empty dict."""
        result = patch(123, "text", True, {"text": "test"})
        self.assertEqual(result, {})
    
    def test_input_validation_name_empty(self):
        """Test that empty name parameter returns empty dict."""
        result = patch("", "text", True, {"text": "test"})
        self.assertEqual(result, {})
    
    def test_input_validation_name_whitespace_only(self):
        """Test that whitespace-only name parameter returns empty dict."""
        result = patch("   ", "text", True, {"text": "test"})
        self.assertEqual(result, {})
    
    def test_input_validation_update_mask_none(self):
        """Test that None updateMask parameter returns empty dict."""
        result = patch("spaces/test/messages/1", None, True, {"text": "test"})
        self.assertEqual(result, {})
    
    def test_input_validation_update_mask_wrong_type(self):
        """Test that non-string updateMask parameter returns empty dict."""
        result = patch("spaces/test/messages/1", 123, True, {"text": "test"})
        self.assertEqual(result, {})
    
    def test_input_validation_update_mask_empty(self):
        """Test that empty updateMask parameter returns empty dict."""
        result = patch("spaces/test/messages/1", "", True, {"text": "test"})
        self.assertEqual(result, {})
    
    def test_input_validation_update_mask_whitespace_only(self):
        """Test that whitespace-only updateMask parameter returns empty dict."""
        result = patch("spaces/test/messages/1", "   ", True, {"text": "test"})
        self.assertEqual(result, {})
    
    def test_input_validation_allow_missing_wrong_type(self):
        """Test that non-bool allowMissing parameter returns empty dict."""
        result = patch("spaces/test/messages/1", "text", "true", {"text": "test"})
        self.assertEqual(result, {})
    
    def test_input_validation_allow_missing_none_defaults_false(self):
        """Test that None allowMissing parameter defaults to False."""
        # Create existing message so we can test the default value
        existing_msg = {"name": "spaces/test/messages/1", "text": "old"}
        DB["Message"].append(existing_msg)
        
        result = patch("spaces/test/messages/1", "text", None, {"text": "new text"})
        self.assertNotEqual(result, {})  # Should work with None defaulting to False
        self.assertEqual(result["text"], "new text")
    
    def test_input_validation_message_wrong_type(self):
        """Test that non-dict message parameter returns empty dict."""
        result = patch("spaces/test/messages/1", "text", True, "not_a_dict")
        self.assertEqual(result, {})
    
    def test_input_validation_message_none_defaults_empty_dict(self):
        """Test that None message parameter defaults to empty dict."""
        # Create existing message so we can test the default value
        existing_msg = {"name": "spaces/test/messages/1", "text": "old"}
        DB["Message"].append(existing_msg)
        
        result = patch("spaces/test/messages/1", "text", False, None)
        self.assertNotEqual(result, {})  # Should work with None defaulting to {}
    
    # Pydantic Validation Tests
    def test_pydantic_validation_invalid_text_type(self):
        """Test that invalid text type in message returns empty dict."""
        result = patch("spaces/test/messages/1", "text", True, {"text": 123})
        self.assertEqual(result, {})
    
    def test_pydantic_validation_invalid_attachment_type(self):
        """Test that invalid attachment type in message returns empty dict."""
        result = patch("spaces/test/messages/1", "attachment", True, {"attachment": "not_a_list"})
        self.assertEqual(result, {})
    
    def test_pydantic_validation_invalid_cards_type(self):
        """Test that invalid cards type in message returns empty dict."""
        result = patch("spaces/test/messages/1", "cards", True, {"cards": "not_a_list"})
        self.assertEqual(result, {})
    
    def test_pydantic_validation_invalid_cards_v2_type(self):
        """Test that invalid cardsV2 type in message returns empty dict."""
        result = patch("spaces/test/messages/1", "cards_v2", True, {"cardsV2": "not_a_list"})
        self.assertEqual(result, {})
    
    def test_pydantic_validation_invalid_accessory_widgets_type(self):
        """Test that invalid accessoryWidgets type in message returns empty dict."""
        result = patch("spaces/test/messages/1", "accessory_widgets", True, {"accessoryWidgets": "not_a_list"})
        self.assertEqual(result, {})
    
    # Name Format Validation Tests
    def test_name_format_invalid_too_few_parts(self):
        """Test that name with too few path segments returns empty dict."""
        result = patch("spaces/test", "text", True, {"text": "test"})
        self.assertEqual(result, {})
    
    def test_name_format_invalid_wrong_structure(self):
        """Test that name with wrong structure returns empty dict."""
        result = patch("invalid/test/format/1", "text", True, {"text": "test"})
        self.assertEqual(result, {})
    
    def test_name_format_invalid_wrong_middle_segment(self):
        """Test that name with wrong middle segment returns empty dict."""
        result = patch("spaces/test/wrong/1", "text", True, {"text": "test"})
        self.assertEqual(result, {})
    
    # Allow Missing and Client ID Tests
    def test_allow_missing_false_message_not_found(self):
        """Test that non-existent message with allowMissing=False returns empty dict."""
        result = patch("spaces/test/messages/nonexistent", "text", False, {"text": "test"})
        self.assertEqual(result, {})
    
    def test_allow_missing_true_non_client_id(self):
        """Test that missing message with allowMissing=True but non-client ID returns empty dict."""
        result = patch("spaces/test/messages/regular-id", "text", True, {"text": "test"})
        self.assertEqual(result, {})
    
    def test_allow_missing_true_client_id_creates_message(self):
        """Test that missing message with allowMissing=True and client ID creates new message."""
        result = patch("spaces/test/messages/client-123", "text", True, {"text": "Hello World"})
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["name"], "spaces/test/messages/client-123")
        self.assertEqual(result["text"], "Hello World")
        self.assertEqual(result["attachment"], [])
        self.assertIn("createTime", result)
        self.assertIn("sender", result)
        self.assertIn("lastUpdateTime", result)
        
        # Verify message was added to DB
        self.assertEqual(len(DB["Message"]), 1)
        self.assertEqual(DB["Message"][0]["name"], "spaces/test/messages/client-123")
    
    # Update Mask Validation Tests
    def test_update_mask_wildcard(self):
        """Test that updateMask='*' updates all provided fields."""
        # Create existing message
        existing_msg = {
            "name": "spaces/test/messages/1",
            "text": "old text",
            "attachment": [],
            "cards": [],
        }
        DB["Message"].append(existing_msg)
        
        message = {
            "text": "new text",
            "attachment": [{"name": "test"}],
            "cardsV2": [{"cardId": "123"}]
        }
        
        result = patch("spaces/test/messages/1", "*", False, message)
        
        self.assertEqual(result["text"], "new text")
        self.assertEqual(result["attachment"], [{"name": "test"}])
        self.assertEqual(result["cardsV2"], [{"cardId": "123"}])
        self.assertIn("lastUpdateTime", result)
    
    def test_update_mask_specific_fields(self):
        """Test that updateMask with specific fields only updates those fields."""
        # Create existing message
        existing_msg = {
            "name": "spaces/test/messages/1",
            "text": "old text",
            "attachment": [{"old": "attachment"}],
        }
        DB["Message"].append(existing_msg)
        
        message = {
            "text": "new text",
            "attachment": [{"new": "attachment"}]
        }
        
        # Only update text field
        result = patch("spaces/test/messages/1", "text", False, message)
        
        self.assertEqual(result["text"], "new text")
        self.assertEqual(result["attachment"], [{"old": "attachment"}])  # Should remain unchanged
        self.assertIn("lastUpdateTime", result)
    
    def test_update_mask_unknown_fields_skipped(self):
        """Test that unknown fields in updateMask are skipped."""
        # Create existing message
        existing_msg = {
            "name": "spaces/test/messages/1",
            "text": "old text",
        }
        DB["Message"].append(existing_msg)
        
        message = {"text": "new text"}
        
        # Include unknown field in updateMask
        result = patch("spaces/test/messages/1", "text,unknown_field", False, message)
        
        self.assertEqual(result["text"], "new text")
        self.assertIn("lastUpdateTime", result)
    
    # Field Mapping Tests
    def test_field_mapping_text(self):
        """Test that text field mapping works correctly."""
        existing_msg = {"name": "spaces/test/messages/1", "text": "old"}
        DB["Message"].append(existing_msg)
        
        result = patch("spaces/test/messages/1", "text", False, {"text": "new text"})
        self.assertEqual(result["text"], "new text")
        self.assertIn("lastUpdateTime", result)
    
    def test_field_mapping_attachment(self):
        """Test that attachment field mapping works correctly."""
        existing_msg = {"name": "spaces/test/messages/1", "attachment": []}
        DB["Message"].append(existing_msg)
        
        new_attachment = [{"name": "file.txt", "contentType": "text/plain"}]
        result = patch("spaces/test/messages/1", "attachment", False, {"attachment": new_attachment})
        self.assertEqual(result["attachment"], new_attachment)
        self.assertIn("lastUpdateTime", result)
    
    def test_field_mapping_cards(self):
        """Test that cards field mapping works correctly."""
        existing_msg = {"name": "spaces/test/messages/1", "cards": []}
        DB["Message"].append(existing_msg)
        
        new_cards = [{"name": "card1", "header": {"title": "Test"}}]
        result = patch("spaces/test/messages/1", "cards", False, {"cards": new_cards})
        self.assertEqual(result["cards"], new_cards)
        self.assertIn("lastUpdateTime", result)
    
    def test_field_mapping_cards_v2_to_camel_case(self):
        """Test that cards_v2 field maps to cardsV2 in the result."""
        existing_msg = {"name": "spaces/test/messages/1", "cardsV2": []}
        DB["Message"].append(existing_msg)
        
        new_cards_v2 = [{"cardId": "123", "card": {"name": "test"}}]
        result = patch("spaces/test/messages/1", "cards_v2", False, {"cardsV2": new_cards_v2})
        self.assertEqual(result["cardsV2"], new_cards_v2)
        self.assertIn("lastUpdateTime", result)
    
    def test_field_mapping_accessory_widgets_to_camel_case(self):
        """Test that accessory_widgets field maps to accessoryWidgets in the result."""
        existing_msg = {"name": "spaces/test/messages/1", "accessoryWidgets": []}
        DB["Message"].append(existing_msg)
        
        new_widgets = [{"decoratedText": {"text": "Hello"}}]
        result = patch("spaces/test/messages/1", "accessory_widgets", False, {"accessoryWidgets": new_widgets})
        self.assertEqual(result["accessoryWidgets"], new_widgets)
        self.assertIn("lastUpdateTime", result)
    
    # None Value Handling Tests
    def test_none_values_not_updated(self):
        """Test that None values in message are not applied to the message."""
        existing_msg = {
            "name": "spaces/test/messages/1",
            "text": "existing text",
            "attachment": [{"existing": "data"}]
        }
        DB["Message"].append(existing_msg)
        
        # Pass None values in message
        result = patch("spaces/test/messages/1", "text,attachment", False, {
            "text": None,
            "attachment": None
        })
        
        # Values should remain unchanged
        self.assertEqual(result["text"], "existing text")
        self.assertEqual(result["attachment"], [{"existing": "data"}])
        self.assertIn("lastUpdateTime", result)
    
    def test_mixed_none_and_valid_values(self):
        """Test handling of mixed None and valid values in message."""
        existing_msg = {
            "name": "spaces/test/messages/1",
            "text": "old text",
            "attachment": []
        }
        DB["Message"].append(existing_msg)
        
        result = patch("spaces/test/messages/1", "text,attachment", False, {
            "text": "new text",  # Valid value
            "attachment": None   # None value
        })
        
        self.assertEqual(result["text"], "new text")  # Should be updated
        self.assertEqual(result["attachment"], [])    # Should remain unchanged
        self.assertIn("lastUpdateTime", result)
    
    # Complex Integration Tests
    def test_complex_patch_all_fields(self):
        """Test complex patch scenario with all field types."""
        existing_msg = {
            "name": "spaces/test/messages/1",
            "text": "old text",
            "attachment": [],
            "cards": [],
            "cardsV2": [],
            "accessoryWidgets": []
        }
        DB["Message"].append(existing_msg)
        
        complex_message = {
            "text": "Patched message text",
            "attachment": [
                {"name": "file1.pdf", "contentType": "application/pdf"},
                {"name": "image.jpg", "contentType": "image/jpeg"}
            ],
            "cards": [
                {
                    "name": "legacy_card",
                    "header": {"title": "Legacy Card", "subtitle": "Patch Test"}
                }
            ],
            "cardsV2": [
                {
                    "cardId": "modern_card_1",
                    "card": {
                        "name": "Modern Card",
                        "header": {"title": "Advanced Card", "subtitle": "V2 Patch Test"}
                    }
                }
            ],
            "accessoryWidgets": [
                {
                    "decoratedText": {
                        "text": "Widget text",
                        "startIcon": {"iconUrl": "https://example.com/icon.png"}
                    }
                }
            ]
        }
        
        result = patch("spaces/test/messages/1", "*", False, complex_message)
        
        # Verify all fields were updated correctly
        self.assertEqual(result["text"], "Patched message text")
        self.assertEqual(len(result["attachment"]), 2)
        self.assertEqual(result["attachment"][0]["name"], "file1.pdf")
        self.assertEqual(len(result["cards"]), 1)
        self.assertEqual(result["cards"][0]["name"], "legacy_card")
        self.assertEqual(len(result["cardsV2"]), 1)
        self.assertEqual(result["cardsV2"][0]["cardId"], "modern_card_1")
        self.assertEqual(len(result["accessoryWidgets"]), 1)
        self.assertEqual(result["accessoryWidgets"][0]["decoratedText"]["text"], "Widget text")
        self.assertIn("lastUpdateTime", result)
    
    def test_partial_patch_preserves_other_fields(self):
        """Test that partial patches preserve fields not in updateMask."""
        existing_msg = {
            "name": "spaces/test/messages/1",
            "text": "original text",
            "attachment": [{"original": "attachment"}],
            "cards": [{"original": "card"}],
            "cardsV2": [{"original": "cardV2"}],
            "accessoryWidgets": [{"original": "widget"}],
            "customField": "should be preserved"
        }
        DB["Message"].append(existing_msg)
        
        # Only patch text and attachment
        result = patch("spaces/test/messages/1", "text,attachment", False, {
            "text": "patched text",
            "attachment": [{"patched": "attachment"}]
        })
        
        # Updated fields
        self.assertEqual(result["text"], "patched text")
        self.assertEqual(result["attachment"], [{"patched": "attachment"}])
        
        # Preserved fields
        self.assertEqual(result["cards"], [{"original": "card"}])
        self.assertEqual(result["cardsV2"], [{"original": "cardV2"}])
        self.assertEqual(result["accessoryWidgets"], [{"original": "widget"}])
        self.assertEqual(result["customField"], "should be preserved")
        self.assertIn("lastUpdateTime", result)
    
    def test_patch_with_extra_message_fields_allowed(self):
        """Test that extra fields in message are allowed due to Pydantic extra='allow'."""
        existing_msg = {"name": "spaces/test/messages/1", "text": "old"}
        DB["Message"].append(existing_msg)
        
        # Include extra field not in Pydantic model
        message_with_extra = {
            "text": "new text",
            "customExtraField": "this should be allowed"
        }
        
        # Should not return empty dict due to extra field
        result = patch("spaces/test/messages/1", "text", False, message_with_extra)
        self.assertNotEqual(result, {})
        self.assertEqual(result["text"], "new text")
        self.assertIn("lastUpdateTime", result)
    
    def test_patch_sets_last_update_time(self):
        """Test that patch operations set lastUpdateTime."""
        existing_msg = {
            "name": "spaces/test/messages/1",
            "text": "old text"
        }
        DB["Message"].append(existing_msg)
        
        result = patch("spaces/test/messages/1", "text", False, {"text": "new text"})
        
        self.assertIn("lastUpdateTime", result)
        self.assertIsInstance(result["lastUpdateTime"], str)
        # Should be in ISO format with Z suffix
        self.assertTrue(result["lastUpdateTime"].endswith("Z"))
    
    def test_created_message_has_required_fields(self):
        """Test that newly created messages have all required fields."""
        result = patch("spaces/test/messages/client-123", "text", True, {"text": "Hello World"})
        
        # Check all required fields are present
        required_fields = ["name", "text", "attachment", "createTime", "sender", "lastUpdateTime"]
        for field in required_fields:
            self.assertIn(field, result)
        
        # Check field values
        self.assertEqual(result["name"], "spaces/test/messages/client-123")
        self.assertEqual(result["text"], "Hello World")
        self.assertEqual(result["attachment"], [])
        self.assertTrue(result["createTime"].endswith("Z"))
        self.assertTrue(result["lastUpdateTime"].endswith("Z"))
        self.assertIn("name", result["sender"])
        self.assertIn("type", result["sender"])
    
    def test_return_type_consistency(self):
        """Test that patch always returns a dictionary, never None."""
        existing_msg = {"name": "spaces/test/messages/1", "text": "old"}
        DB["Message"].append(existing_msg)
        
        result = patch("spaces/test/messages/1", "text", False, {"text": "new text"})
        
        # Verify return type is dict, not None
        self.assertIsInstance(result, dict)
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main() 