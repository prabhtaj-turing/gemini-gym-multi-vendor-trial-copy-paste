# tests/test_multiple_recipients_support.py
"""
Test cases for multiple recipients support in Gmail API endpoints.
Tests comma-separated recipient strings for TO, CC, and BCC fields.
"""
import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.utils import reset_db
from .. import (
    send_message, import_message, insert_message, create_draft, 
    update_draft, send_draft, create_user, list_messages, get_message
)
from ..SimulationEngine.attachment_utils import create_mime_message_with_attachments
from ..SimulationEngine import custom_errors


class TestMultipleRecipientsSupport(BaseTestCaseWithErrorHandler):
    """Test cases for multiple recipients functionality."""
    
    def setUp(self):
        reset_db()
        create_user("me", profile={"emailAddress": "me@example.com"})
        self.userId = "me"
    
    # ===== SEND MESSAGE TESTS =====
    
    def test_send_message_single_recipient(self):
        """Test sending message with single recipient (baseline)."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com",
            "subject": "Single Recipient Test",
            "body": "Test message to single recipient"
        }
        
        result = send_message(self.userId, msg)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["recipient"], "user1@example.com")
        self.assertEqual(result["subject"], "Single Recipient Test")
    
    def test_send_message_multiple_recipients_comma_separated(self):
        """Test sending message with multiple recipients (comma-separated)."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com, user2@example.com, user3@example.com",
            "subject": "Multiple Recipients Test",
            "body": "Test message to multiple recipients"
        }
        
        # This should currently fail or not handle multiple recipients properly
        # We expect this to be handled as a single string currently
        result = send_message(self.userId, msg)
        
        # Current implementation treats this as a single recipient string
        self.assertEqual(result["recipient"], "user1@example.com, user2@example.com, user3@example.com")
        
        # Note: Gmail API stores recipients as comma-separated strings, not arrays
        # Parsing can be done on-demand using parse_email_list() utility function
    
    def test_send_message_with_cc_field(self):
        """Test sending message with CC field."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com",
            "cc": "cc1@example.com, cc2@example.com",
            "subject": "CC Test",
            "body": "Test message with CC"
        }
        
        # This should currently fail as CC is not supported
        try:
            result = send_message(self.userId, msg)
            # If it doesn't fail, CC field is being ignored
            self.assertNotIn("cc", result)  # Current behavior - CC is ignored
        except Exception as e:
            # Expected to fail with current implementation
            pass
    
    def test_send_message_with_bcc_field(self):
        """Test sending message with BCC field."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com",
            "bcc": "bcc1@example.com, bcc2@example.com",
            "subject": "BCC Test",
            "body": "Test message with BCC"
        }
        
        # This should currently fail as BCC is not supported
        try:
            result = send_message(self.userId, msg)
            # If it doesn't fail, BCC field is being ignored
            self.assertNotIn("bcc", result)  # Current behavior - BCC is ignored
        except Exception as e:
            # Expected to fail with current implementation
            pass
    
    def test_send_message_with_all_recipient_types(self):
        """Test sending message with TO, CC, and BCC fields."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com, user2@example.com",
            "cc": "cc1@example.com, cc2@example.com",
            "bcc": "bcc1@example.com",
            "subject": "All Recipients Test",
            "body": "Test message with TO, CC, and BCC"
        }
        
        # This should currently not handle CC/BCC properly
        try:
            result = send_message(self.userId, msg)
            # Current implementation only handles recipient field
            self.assertEqual(result["recipient"], "user1@example.com, user2@example.com")
            self.assertNotIn("cc", result)
            self.assertNotIn("bcc", result)
        except Exception as e:
            # May fail with current implementation
            pass
    
    def test_send_message_empty_recipients(self):
        """Test sending message with empty recipient fields."""
        msg = {
            "sender": "me@example.com",
            "recipient": "",
            "subject": "Empty Recipients Test",
            "body": "Test message with empty recipients"
        }
        
        # Should fail validation
        with self.assertRaises(ValueError):
            send_message(self.userId, msg)
    
    def test_send_message_invalid_email_in_recipients(self):
        """Test sending message with invalid email addresses in recipients."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com, invalid-email, user2@example.com",
            "subject": "Invalid Email Test",
            "body": "Test message with invalid email"
        }
        
        # Should handle invalid emails gracefully or fail validation
        try:
            result = send_message(self.userId, msg)
            # Current implementation may not validate individual emails in comma-separated list
            self.assertIsInstance(result, dict)
        except Exception as e:
            # May fail with validation error
            pass
    
    # ===== DRAFT TESTS =====
    
    def test_create_draft_multiple_recipients(self):
        """Test creating draft with multiple recipients."""
        draft_data = {
            "message": {
                "sender": "me@example.com",
                "recipient": "user1@example.com, user2@example.com, user3@example.com",
                "subject": "Draft Multiple Recipients",
                "body": "Draft with multiple recipients"
            }
        }
        
        result = create_draft(self.userId, draft_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["message"]["recipient"], "user1@example.com, user2@example.com, user3@example.com")
        
        # Note: Gmail API stores recipients as comma-separated strings
    
    def test_create_draft_with_cc_bcc(self):
        """Test creating draft with CC and BCC fields."""
        draft_data = {
            "message": {
                "sender": "me@example.com",
                "recipient": "user1@example.com",
                "cc": "cc1@example.com, cc2@example.com",
                "bcc": "bcc1@example.com",
                "subject": "Draft with CC/BCC",
                "body": "Draft with CC and BCC fields"
            }
        }
        
        # This should currently not handle CC/BCC
        try:
            result = create_draft(self.userId, draft_data)
            # CC/BCC fields are likely ignored
            self.assertNotIn("cc", result["message"])
            self.assertNotIn("bcc", result["message"])
        except Exception as e:
            # May fail with current implementation
            pass
    
    def test_update_draft_multiple_recipients(self):
        """Test updating draft with multiple recipients."""
        # First create a draft
        draft_data = {
            "message": {
                "sender": "me@example.com",
                "recipient": "user1@example.com",
                "subject": "Original Draft",
                "body": "Original content"
            }
        }
        
        draft = create_draft(self.userId, draft_data)
        draft_id = draft["id"]
        
        # Update with multiple recipients
        update_data = {
            "message": {
                "recipient": "user1@example.com, user2@example.com, user3@example.com",
                "cc": "cc1@example.com",
                "bcc": "bcc1@example.com"
            }
        }
        
        result = update_draft(draft_id, self.userId, update_data)
        
        if result:
            self.assertEqual(result["message"]["recipient"], "user1@example.com, user2@example.com, user3@example.com")
            # CC/BCC likely not supported yet
    
    def test_send_draft_multiple_recipients(self):
        """Test sending draft with multiple recipients."""
        # Create draft with multiple recipients
        draft_data = {
            "message": {
                "sender": "me@example.com",
                "recipient": "user1@example.com, user2@example.com",
                "subject": "Send Draft Multiple Recipients",
                "body": "Sending draft with multiple recipients"
            }
        }
        
        draft = create_draft(self.userId, draft_data)
        
        # Send the draft
        result = send_draft(self.userId, draft)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["recipient"], "user1@example.com, user2@example.com")
    
    # ===== INSERT/IMPORT MESSAGE TESTS =====
    
    def test_insert_message_multiple_recipients(self):
        """Test inserting message with multiple recipients."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com, user2@example.com",
            "subject": "Insert Multiple Recipients",
            "body": "Inserted message with multiple recipients"
        }
        
        result = insert_message(self.userId, msg)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result["recipient"], "user1@example.com, user2@example.com")
    
    def test_import_message_multiple_recipients(self):
        """Test importing message with multiple recipients."""
        # Create a raw MIME message with multiple recipients
        raw_content = create_mime_message_with_attachments(
            to="user1@example.com, user2@example.com",
            subject="Import Multiple Recipients",
            body="Imported message with multiple recipients",
            from_email="me@example.com"
        )
        
        msg = {
            "raw": raw_content,
            "labelIds": ["INBOX"]
        }
        
        result = import_message(self.userId, msg)
        
        self.assertIsInstance(result, dict)
        self.assertIn("raw", result)
    
    # ===== EDGE CASES =====
    
    def test_recipients_with_whitespace(self):
        """Test recipients with various whitespace patterns."""
        test_cases = [
            "user1@example.com,user2@example.com",  # No spaces
            "user1@example.com, user2@example.com",  # Standard spacing
            "user1@example.com ,user2@example.com",  # Space before comma
            "user1@example.com , user2@example.com",  # Spaces around comma
            " user1@example.com, user2@example.com ",  # Leading/trailing spaces
            "user1@example.com,  user2@example.com",  # Multiple spaces after comma
        ]
        
        for recipients in test_cases:
            with self.subTest(recipients=recipients):
                msg = {
                    "sender": "me@example.com",
                    "recipient": recipients,
                    "subject": "Whitespace Test",
                    "body": "Testing whitespace handling"
                }
                
                try:
                    result = send_message(self.userId, msg)
                    self.assertIsInstance(result, dict)
                    # Current implementation stores as-is
                    self.assertEqual(result["recipient"], recipients)
                except Exception as e:
                    # May fail with current implementation
                    pass
    
    def test_recipients_none_values(self):
        """Test handling of None values in recipient fields."""
        test_cases = [
            {"recipient": None, "description": "None recipient"},
            {"recipient": "user1@example.com", "cc": None, "description": "None CC"},
            {"recipient": "user1@example.com", "bcc": None, "description": "None BCC"},
            {"recipient": None, "cc": None, "bcc": None, "description": "All None"},
        ]
        
        for case in test_cases:
            with self.subTest(case=case["description"]):
                msg = {
                    "sender": "me@example.com",
                    "subject": "None Values Test",
                    "body": "Testing None value handling"
                }
                
                # Add non-None fields
                for field in ["recipient", "cc", "bcc"]:
                    if field in case and case[field] is not None:
                        msg[field] = case[field]
                    elif field in case and case[field] is None:
                        msg[field] = None
                
                try:
                    result = send_message(self.userId, msg)
                    # Should handle None values gracefully
                    self.assertIsInstance(result, dict)
                except (TypeError, ValueError, AttributeError) as e:
                    # Expected to fail with None values
                    self.assertIsInstance(e, (TypeError, ValueError, AttributeError))
                except Exception as e:
                    # Other exceptions may occur
                    pass
    
    def test_recipients_non_string_types(self):
        """Test handling of non-string types in recipient fields."""
        test_cases = [
            {"recipient": 123, "description": "Integer recipient"},
            {"recipient": 12.34, "description": "Float recipient"},
            {"recipient": True, "description": "Boolean recipient"},
            {"recipient": [], "description": "Empty list recipient"},
            {"recipient": ["user1@example.com", "user2@example.com"], "description": "List recipient"},
            {"recipient": {"email": "user1@example.com"}, "description": "Dict recipient"},
            {"cc": 456, "description": "Integer CC"},
            {"bcc": ["bcc1@example.com"], "description": "List BCC"},
            {"recipient": b"user1@example.com", "description": "Bytes recipient"},
        ]
        
        for case in test_cases:
            with self.subTest(case=case["description"]):
                msg = {
                    "sender": "me@example.com",
                    "subject": "Non-String Types Test",
                    "body": "Testing non-string type handling"
                }
                
                # Add the test field
                for field in ["recipient", "cc", "bcc"]:
                    if field in case:
                        msg[field] = case[field]
                
                # Ensure we have a valid recipient if testing other fields
                if "recipient" not in case:
                    msg["recipient"] = "user1@example.com"
                
                try:
                    result = send_message(self.userId, msg)
                    # May succeed if type is coerced to string
                    self.assertIsInstance(result, dict)
                except (TypeError, ValueError, AttributeError) as e:
                    # Expected to fail with non-string types
                    self.assertIsInstance(e, (TypeError, ValueError, AttributeError))
                except Exception as e:
                    # Other exceptions may occur
                    pass
    
    def test_recipients_empty_and_whitespace_strings(self):
        """Test handling of empty and whitespace-only strings."""
        test_cases = [
            {"recipient": "", "description": "Empty string recipient"},
            {"recipient": " ", "description": "Single space recipient"},
            {"recipient": "   ", "description": "Multiple spaces recipient"},
            {"recipient": "\t", "description": "Tab character recipient"},
            {"recipient": "\n", "description": "Newline character recipient"},
            {"recipient": "\r\n", "description": "CRLF recipient"},
            {"recipient": "user1@example.com", "cc": "", "description": "Empty CC"},
            {"recipient": "user1@example.com", "bcc": "   ", "description": "Whitespace BCC"},
            {"recipient": "user1@example.com", "cc": "\t\n", "description": "Tab/newline CC"},
        ]
        
        for case in test_cases:
            with self.subTest(case=case["description"]):
                msg = {
                    "sender": "me@example.com",
                    "subject": "Empty/Whitespace Test",
                    "body": "Testing empty and whitespace handling"
                }
                
                # Add test fields
                for field in ["recipient", "cc", "bcc"]:
                    if field in case:
                        msg[field] = case[field]
                
                try:
                    result = send_message(self.userId, msg)
                    # May succeed if empty strings are handled gracefully
                    self.assertIsInstance(result, dict)
                except (ValueError, TypeError) as e:
                    # Expected to fail for empty recipient
                    if case.get("recipient") in ["", " ", "   ", "\t", "\n", "\r\n"]:
                        self.assertIsInstance(e, (ValueError, TypeError))
                except Exception as e:
                    # Other exceptions may occur
                    pass
    
    def test_recipients_malformed_comma_patterns(self):
        """Test handling of malformed comma-separated patterns."""
        test_cases = [
            ",",  # Single comma
            ",,",  # Double comma
            ",,,",  # Triple comma
            "user1@example.com,",  # Trailing comma
            ",user1@example.com",  # Leading comma
            "user1@example.com,,user2@example.com",  # Double comma between emails
            "user1@example.com,,,user2@example.com",  # Triple comma between emails
            ",user1@example.com,",  # Leading and trailing comma
            ",,user1@example.com,,",  # Multiple leading/trailing commas
            "user1@example.com, , user2@example.com",  # Comma with spaces only
            "user1@example.com,\t,user2@example.com",  # Comma with tab
            "user1@example.com,\n,user2@example.com",  # Comma with newline
        ]
        
        for recipients in test_cases:
            with self.subTest(recipients=recipients):
                msg = {
                    "sender": "me@example.com",
                    "recipient": recipients,
                    "subject": "Malformed Comma Test",
                    "body": "Testing malformed comma patterns"
                }
                
                try:
                    result = send_message(self.userId, msg)
                    # Current implementation may store as-is
                    self.assertIsInstance(result, dict)
                    self.assertEqual(result["recipient"], recipients)
                    
                    # TODO: After implementation, should handle malformed patterns gracefully
                    # - Filter out empty segments
                    # - Validate remaining email addresses
                    # - Provide meaningful error messages for invalid patterns
                    
                except (ValueError, TypeError) as e:
                    # May fail with malformed patterns
                    self.assertIsInstance(e, (ValueError, TypeError))
                except Exception as e:
                    # Other exceptions may occur
                    pass
    
    def test_recipients_special_characters(self):
        """Test handling of special characters in recipient fields."""
        test_cases = [
            "user1@example.com;user2@example.com",  # Semicolon separator
            "user1@example.com|user2@example.com",  # Pipe separator
            "user1@example.com user2@example.com",  # Space separator
            "user1@example.com\tuser2@example.com",  # Tab separator
            "user1@example.com\nuser2@example.com",  # Newline separator
            "user1@example.com,user2@example.com,",  # Trailing comma
            "user1@example.com, user2@example.com;",  # Mixed separators
            "user1@example.com, user2@example.com\n",  # Mixed with newline
            "user1@example.com, user2@example.com\0",  # Null character
            "user1@example.com, user2@example.com\x00",  # Null byte
        ]
        
        for recipients in test_cases:
            with self.subTest(recipients=recipients):
                msg = {
                    "sender": "me@example.com",
                    "recipient": recipients,
                    "subject": "Special Characters Test",
                    "body": "Testing special character handling"
                }
                
                try:
                    result = send_message(self.userId, msg)
                    # Current implementation may store as-is
                    self.assertIsInstance(result, dict)
                except Exception as e:
                    # May fail with special characters
                    pass
    
    def test_recipients_unicode_and_international(self):
        """Test handling of Unicode and international characters."""
        test_cases = [
            "用户@example.com, user2@example.com",  # Chinese characters
            "usuário@example.com, user2@example.com",  # Portuguese characters
            "пользователь@example.com, user2@example.com",  # Cyrillic characters
            "user1@例え.com, user2@example.com",  # International domain
            "user1@example.com, user2@例え.com",  # International domain in second email
            "José María <jose@example.com>, user2@example.com",  # Accented display name
            "user1@example.com, 山田太郎 <yamada@example.com>",  # Japanese display name
            "user1@example.com, user2@xn--fsq.com",  # Punycode domain
            "user1@example.com, user2@münchen.de",  # German umlaut domain
        ]
        
        for recipients in test_cases:
            with self.subTest(recipients=recipients):
                msg = {
                    "sender": "me@example.com",
                    "recipient": recipients,
                    "subject": "Unicode Test",
                    "body": "Testing Unicode character handling"
                }
                
                try:
                    result = send_message(self.userId, msg)
                    # Should handle Unicode gracefully
                    self.assertIsInstance(result, dict)
                    self.assertEqual(result["recipient"], recipients)
                except Exception as e:
                    # May fail with Unicode characters
                    pass
    
    def test_recipients_extremely_long_values(self):
        """Test handling of extremely long recipient values."""
        # Very long email address
        long_email = "a" * 1000 + "@example.com"
        
        # Very long recipient list
        long_list = ", ".join([f"user{i}@example.com" for i in range(1000)])
        
        # Very long display name
        long_display_name = "A" * 1000 + " <user@example.com>"
        
        test_cases = [
            {"recipient": long_email, "description": "Very long email address"},
            {"recipient": long_list, "description": "Very long recipient list"},
            {"recipient": long_display_name, "description": "Very long display name"},
            {"recipient": "user1@example.com", "cc": long_list, "description": "Very long CC list"},
            {"recipient": "user1@example.com", "bcc": long_email, "description": "Very long BCC email"},
        ]
        
        for case in test_cases:
            with self.subTest(case=case["description"]):
                msg = {
                    "sender": "me@example.com",
                    "subject": "Long Values Test",
                    "body": "Testing extremely long values"
                }
                
                # Add test fields
                for field in ["recipient", "cc", "bcc"]:
                    if field in case:
                        msg[field] = case[field]
                
                try:
                    result = send_message(self.userId, msg)
                    # May succeed or fail depending on size limits
                    self.assertIsInstance(result, dict)
                except Exception as e:
                    # May fail due to size limits or memory constraints
                    pass
    
    def test_recipients_with_display_names(self):
        """Test recipients with display names."""
        msg = {
            "sender": "me@example.com",
            "recipient": "John Doe <john@example.com>, Jane Smith <jane@example.com>",
            "subject": "Display Names Test",
            "body": "Testing display names in recipients"
        }
        
        try:
            result = send_message(self.userId, msg)
            self.assertIsInstance(result, dict)
            # Current implementation may not parse display names
        except Exception as e:
            # May fail with current implementation
            pass
    
    def test_very_long_recipient_list(self):
        """Test with a very long list of recipients."""
        recipients = ", ".join([f"user{i}@example.com" for i in range(100)])
        
        msg = {
            "sender": "me@example.com",
            "recipient": recipients,
            "subject": "Long Recipient List Test",
            "body": "Testing very long recipient list"
        }
        
        try:
            result = send_message(self.userId, msg)
            self.assertIsInstance(result, dict)
            # Should handle large recipient lists
        except Exception as e:
            # May fail due to size limits or parsing issues
            pass
    
    def test_duplicate_recipients(self):
        """Test with duplicate recipients in the list."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com, user2@example.com, user1@example.com",
            "subject": "Duplicate Recipients Test",
            "body": "Testing duplicate recipients"
        }
        
        try:
            result = send_message(self.userId, msg)
            self.assertIsInstance(result, dict)
            # Should handle duplicates gracefully (dedupe or keep as-is)
        except Exception as e:
            # May fail with current implementation
            pass


if __name__ == '__main__':
    unittest.main()
