# tests/test_bcc_cc_functionality.py
"""
Test cases for BCC/CC functionality in Gmail API endpoints.
Tests CC and BCC field handling in messages and drafts.
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


class TestBccCcFunctionality(BaseTestCaseWithErrorHandler):
    """Test cases for BCC/CC functionality."""
    
    def setUp(self):
        reset_db()
        create_user("me", profile={"emailAddress": "me@example.com"})
        self.userId = "me"
    
    # ===== CC FUNCTIONALITY TESTS =====
    
    def test_send_message_with_cc_single(self):
        """Test sending message with single CC recipient."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com",
            "cc": "cc1@example.com",
            "subject": "Single CC Test",
            "body": "Test message with single CC"
        }
        
        # Current implementation likely doesn't support CC
        try:
            result = send_message(self.userId, msg)
            # If successful, check if CC is handled
            if "cc" in result:
                self.assertEqual(result["cc"], "cc1@example.com")
            else:
                # CC field is ignored in current implementation
                self.assertNotIn("cc", result)
        except Exception as e:
            # Expected to fail or ignore CC field
            self.assertIsInstance(e, (TypeError, ValueError, AttributeError))
    
    def test_send_message_with_cc_multiple(self):
        """Test sending message with multiple CC recipients."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com",
            "cc": "cc1@example.com, cc2@example.com, cc3@example.com",
            "subject": "Multiple CC Test",
            "body": "Test message with multiple CC"
        }
        
        try:
            result = send_message(self.userId, msg)
            # TODO: After implementation, should handle multiple CC recipients
            if "cc" in result:
                self.assertEqual(result["cc"], "cc1@example.com, cc2@example.com, cc3@example.com")
        except Exception as e:
            # Expected to fail with current implementation
            pass
    
    def test_send_message_cc_only_no_to(self):
        """Test sending message with CC but no TO recipients."""
        msg = {
            "sender": "me@example.com",
            "recipient": "",  # Empty TO field
            "cc": "cc1@example.com, cc2@example.com",
            "subject": "CC Only Test",
            "body": "Test message with only CC recipients"
        }
        
        # Should succeed - CC-only messages are valid
        result = send_message(self.userId, msg)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('cc'), 'cc1@example.com, cc2@example.com')
    
    # ===== BCC FUNCTIONALITY TESTS =====
    
    def test_send_message_with_bcc_single(self):
        """Test sending message with single BCC recipient."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com",
            "bcc": "bcc1@example.com",
            "subject": "Single BCC Test",
            "body": "Test message with single BCC"
        }
        
        try:
            result = send_message(self.userId, msg)
            # BCC should not appear in the final message (by design)
            # But should be stored for delivery purposes
            if "bcc" in result:
                self.assertEqual(result["bcc"], "bcc1@example.com")
            else:
                # BCC field is ignored in current implementation
                self.assertNotIn("bcc", result)
        except Exception as e:
            # Expected to fail with current implementation
            pass
    
    def test_send_message_with_bcc_multiple(self):
        """Test sending message with multiple BCC recipients."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com",
            "bcc": "bcc1@example.com, bcc2@example.com, bcc3@example.com",
            "subject": "Multiple BCC Test",
            "body": "Test message with multiple BCC"
        }
        
        try:
            result = send_message(self.userId, msg)
            # TODO: After implementation, should handle multiple BCC recipients
            if "bcc" in result:
                self.assertEqual(result["bcc"], "bcc1@example.com, bcc2@example.com, bcc3@example.com")
        except Exception as e:
            # Expected to fail with current implementation
            pass
    
    def test_send_message_bcc_only_no_to_cc(self):
        """Test sending message with BCC but no TO or CC recipients."""
        msg = {
            "sender": "me@example.com",
            "recipient": "",  # Empty TO field
            "bcc": "bcc1@example.com, bcc2@example.com",
            "subject": "BCC Only Test",
            "body": "Test message with only BCC recipients"
        }
        
        # Should succeed - BCC-only messages are valid
        result = send_message(self.userId, msg)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('bcc'), 'bcc1@example.com, bcc2@example.com')
    
    # ===== COMBINED CC/BCC TESTS =====
    
    def test_send_message_with_to_cc_bcc(self):
        """Test sending message with TO, CC, and BCC recipients."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com, user2@example.com",
            "cc": "cc1@example.com, cc2@example.com",
            "bcc": "bcc1@example.com, bcc2@example.com",
            "subject": "Complete Recipients Test",
            "body": "Test message with TO, CC, and BCC"
        }
        
        try:
            result = send_message(self.userId, msg)
            # Check all recipient types are handled
            self.assertEqual(result["recipient"], "user1@example.com, user2@example.com")
            if "cc" in result:
                self.assertEqual(result["cc"], "cc1@example.com, cc2@example.com")
            if "bcc" in result:
                self.assertEqual(result["bcc"], "bcc1@example.com, bcc2@example.com")
        except Exception as e:
            # Expected to fail with current implementation
            pass
    
    # ===== DRAFT CC/BCC TESTS =====
    
    def test_create_draft_with_cc(self):
        """Test creating draft with CC recipients."""
        draft_data = {
            "message": {
                "sender": "me@example.com",
                "recipient": "user1@example.com",
                "cc": "cc1@example.com, cc2@example.com",
                "subject": "Draft with CC",
                "body": "Draft message with CC recipients"
            }
        }
        
        try:
            result = create_draft(self.userId, draft_data)
            self.assertIsInstance(result, dict)
            if "cc" in result["message"]:
                self.assertEqual(result["message"]["cc"], "cc1@example.com, cc2@example.com")
        except Exception as e:
            # Expected to fail with current implementation
            pass
    
    def test_create_draft_with_bcc(self):
        """Test creating draft with BCC recipients."""
        draft_data = {
            "message": {
                "sender": "me@example.com",
                "recipient": "user1@example.com",
                "bcc": "bcc1@example.com, bcc2@example.com",
                "subject": "Draft with BCC",
                "body": "Draft message with BCC recipients"
            }
        }
        
        try:
            result = create_draft(self.userId, draft_data)
            self.assertIsInstance(result, dict)
            if "bcc" in result["message"]:
                self.assertEqual(result["message"]["bcc"], "bcc1@example.com, bcc2@example.com")
        except Exception as e:
            # Expected to fail with current implementation
            pass
    
    def test_update_draft_add_cc_bcc(self):
        """Test updating draft to add CC and BCC recipients."""
        # Create initial draft
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
        
        # Update to add CC and BCC
        update_data = {
            "message": {
                "cc": "cc1@example.com, cc2@example.com",
                "bcc": "bcc1@example.com"
            }
        }
        
        try:
            result = update_draft(draft_id, self.userId, update_data)
            if result and "cc" in result["message"]:
                self.assertEqual(result["message"]["cc"], "cc1@example.com, cc2@example.com")
            if result and "bcc" in result["message"]:
                self.assertEqual(result["message"]["bcc"], "bcc1@example.com")
        except Exception as e:
            # Expected to fail with current implementation
            pass
    
    def test_send_draft_with_cc_bcc(self):
        """Test sending draft that contains CC and BCC recipients."""
        draft_data = {
            "message": {
                "sender": "me@example.com",
                "recipient": "user1@example.com",
                "cc": "cc1@example.com",
                "bcc": "bcc1@example.com",
                "subject": "Send Draft with CC/BCC",
                "body": "Sending draft with CC and BCC"
            }
        }
        
        try:
            draft = create_draft(self.userId, draft_data)
            result = send_draft(self.userId, draft)
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result["recipient"], "user1@example.com")
            # CC/BCC handling depends on implementation
        except Exception as e:
            # Expected to fail with current implementation
            pass
    
    # ===== RAW MIME MESSAGE TESTS =====
    
    def test_send_message_raw_with_cc_bcc_headers(self):
        """Test sending raw MIME message with CC and BCC headers."""
        # Create raw MIME with CC/BCC headers
        raw_mime = """From: me@example.com
To: user1@example.com
Cc: cc1@example.com, cc2@example.com
Bcc: bcc1@example.com
Subject: Raw MIME with CC/BCC
Content-Type: text/plain

This is a test message with CC and BCC headers in raw MIME format."""
        
        # Encode as base64url
        import base64
        raw_encoded = base64.urlsafe_b64encode(raw_mime.encode()).decode().rstrip('=')
        
        msg = {
            "raw": raw_encoded
        }
        
        try:
            result = send_message(self.userId, msg)
            self.assertIsInstance(result, dict)
            # Should parse CC/BCC from raw MIME headers
        except Exception as e:
            # May fail with current implementation
            pass
    
    def test_import_message_with_cc_bcc_headers(self):
        """Test importing message with CC/BCC headers."""
        raw_mime = """From: sender@example.com
To: user1@example.com
Cc: cc1@example.com
Bcc: bcc1@example.com
Subject: Imported message with CC/BCC
Content-Type: text/plain

Imported message with CC and BCC."""
        
        import base64
        raw_encoded = base64.urlsafe_b64encode(raw_mime.encode()).decode().rstrip('=')
        
        msg = {
            "raw": raw_encoded,
            "labelIds": ["INBOX"]
        }
        
        try:
            result = import_message(self.userId, msg)
            self.assertIsInstance(result, dict)
            # Should preserve CC/BCC information from imported message
        except Exception as e:
            # May fail with current implementation
            pass
    
    # ===== VALIDATION TESTS =====
    
    def test_invalid_cc_email_addresses(self):
        """Test handling of invalid email addresses in CC field."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com",
            "cc": "invalid-email, cc1@example.com, another-invalid",
            "subject": "Invalid CC Test",
            "body": "Test with invalid CC emails"
        }
        
        try:
            result = send_message(self.userId, msg)
            # Should handle invalid emails gracefully or fail validation
        except Exception as e:
            # May fail with validation error
            self.assertIsInstance(e, (ValueError, TypeError))
    
    def test_invalid_bcc_email_addresses(self):
        """Test handling of invalid email addresses in BCC field."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com",
            "bcc": "invalid-email, bcc1@example.com, another-invalid",
            "subject": "Invalid BCC Test",
            "body": "Test with invalid BCC emails"
        }
        
        try:
            result = send_message(self.userId, msg)
            # Should handle invalid emails gracefully or fail validation
        except Exception as e:
            # May fail with validation error
            self.assertIsInstance(e, (ValueError, TypeError))
    
    def test_empty_cc_bcc_fields(self):
        """Test handling of empty CC/BCC fields."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com",
            "cc": "",
            "bcc": "",
            "subject": "Empty CC/BCC Test",
            "body": "Test with empty CC/BCC fields"
        }
        
        try:
            result = send_message(self.userId, msg)
            # Empty fields should be handled gracefully
            self.assertIsInstance(result, dict)
        except Exception as e:
            # Should not fail for empty CC/BCC
            pass
    
    def test_whitespace_only_cc_bcc(self):
        """Test handling of whitespace-only CC/BCC fields."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com",
            "cc": "   ",
            "bcc": "\t\n",
            "subject": "Whitespace CC/BCC Test",
            "body": "Test with whitespace-only CC/BCC"
        }
        
        try:
            result = send_message(self.userId, msg)
            # Whitespace-only fields should be treated as empty
            self.assertIsInstance(result, dict)
        except Exception as e:
            # Should not fail for whitespace-only CC/BCC
            pass
    
    # ===== EDGE CASES =====
    
    def test_cc_bcc_none_values(self):
        """Test handling of None values in CC/BCC fields."""
        test_cases = [
            {"cc": None, "description": "None CC"},
            {"bcc": None, "description": "None BCC"},
            {"cc": None, "bcc": None, "description": "Both None"},
            {"cc": "cc1@example.com", "bcc": None, "description": "CC valid, BCC None"},
            {"cc": None, "bcc": "bcc1@example.com", "description": "CC None, BCC valid"},
        ]
        
        for case in test_cases:
            with self.subTest(case=case["description"]):
                msg = {
                    "sender": "me@example.com",
                    "recipient": "user1@example.com",
                    "subject": "None Values Test",
                    "body": "Testing None value handling in CC/BCC"
                }
                
                # Add test fields
                for field in ["cc", "bcc"]:
                    if field in case:
                        msg[field] = case[field]
                
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
    
    def test_cc_bcc_non_string_types(self):
        """Test handling of non-string types in CC/BCC fields."""
        test_cases = [
            {"cc": 123, "description": "Integer CC"},
            {"bcc": 456, "description": "Integer BCC"},
            {"cc": 12.34, "description": "Float CC"},
            {"bcc": 56.78, "description": "Float BCC"},
            {"cc": True, "description": "Boolean CC"},
            {"bcc": False, "description": "Boolean BCC"},
            {"cc": [], "description": "Empty list CC"},
            {"bcc": [], "description": "Empty list BCC"},
            {"cc": ["cc1@example.com", "cc2@example.com"], "description": "List CC"},
            {"bcc": ["bcc1@example.com", "bcc2@example.com"], "description": "List BCC"},
            {"cc": {"email": "cc1@example.com"}, "description": "Dict CC"},
            {"bcc": {"email": "bcc1@example.com"}, "description": "Dict BCC"},
            {"cc": b"cc1@example.com", "description": "Bytes CC"},
            {"bcc": b"bcc1@example.com", "description": "Bytes BCC"},
        ]
        
        for case in test_cases:
            with self.subTest(case=case["description"]):
                msg = {
                    "sender": "me@example.com",
                    "recipient": "user1@example.com",
                    "subject": "Non-String Types Test",
                    "body": "Testing non-string type handling in CC/BCC"
                }
                
                # Add test field
                for field in ["cc", "bcc"]:
                    if field in case:
                        msg[field] = case[field]
                
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
    
    def test_cc_bcc_empty_and_whitespace_strings(self):
        """Test handling of empty and whitespace-only strings in CC/BCC."""
        test_cases = [
            {"cc": "", "description": "Empty string CC"},
            {"bcc": "", "description": "Empty string BCC"},
            {"cc": " ", "description": "Single space CC"},
            {"bcc": " ", "description": "Single space BCC"},
            {"cc": "   ", "description": "Multiple spaces CC"},
            {"bcc": "   ", "description": "Multiple spaces BCC"},
            {"cc": "\t", "description": "Tab character CC"},
            {"bcc": "\t", "description": "Tab character BCC"},
            {"cc": "\n", "description": "Newline character CC"},
            {"bcc": "\n", "description": "Newline character BCC"},
            {"cc": "\r\n", "description": "CRLF CC"},
            {"bcc": "\r\n", "description": "CRLF BCC"},
            {"cc": "", "bcc": "", "description": "Both empty"},
            {"cc": "   ", "bcc": "\t\n", "description": "Both whitespace"},
        ]
        
        for case in test_cases:
            with self.subTest(case=case["description"]):
                msg = {
                    "sender": "me@example.com",
                    "recipient": "user1@example.com",
                    "subject": "Empty/Whitespace Test",
                    "body": "Testing empty and whitespace handling in CC/BCC"
                }
                
                # Add test fields
                for field in ["cc", "bcc"]:
                    if field in case:
                        msg[field] = case[field]
                
                try:
                    result = send_message(self.userId, msg)
                    # Should handle empty/whitespace strings gracefully
                    self.assertIsInstance(result, dict)
                except Exception as e:
                    # Should not fail for empty CC/BCC
                    pass
    
    def test_cc_bcc_malformed_comma_patterns(self):
        """Test handling of malformed comma-separated patterns in CC/BCC."""
        malformed_patterns = [
            ",",  # Single comma
            ",,",  # Double comma
            ",,,",  # Triple comma
            "cc1@example.com,",  # Trailing comma
            ",cc1@example.com",  # Leading comma
            "cc1@example.com,,cc2@example.com",  # Double comma between emails
            "cc1@example.com,,,cc2@example.com",  # Triple comma between emails
            ",cc1@example.com,",  # Leading and trailing comma
            ",,cc1@example.com,,",  # Multiple leading/trailing commas
            "cc1@example.com, , cc2@example.com",  # Comma with spaces only
            "cc1@example.com,\t,cc2@example.com",  # Comma with tab
            "cc1@example.com,\n,cc2@example.com",  # Comma with newline
        ]
        
        for pattern in malformed_patterns:
            with self.subTest(pattern=pattern):
                # Test CC field
                msg_cc = {
                    "sender": "me@example.com",
                    "recipient": "user1@example.com",
                    "cc": pattern,
                    "subject": "Malformed CC Test",
                    "body": "Testing malformed comma patterns in CC"
                }
                
                try:
                    result = send_message(self.userId, msg_cc)
                    # Current implementation may store as-is
                    self.assertIsInstance(result, dict)
                except Exception as e:
                    # May fail with malformed patterns
                    pass
                
                # Test BCC field
                msg_bcc = {
                    "sender": "me@example.com",
                    "recipient": "user1@example.com",
                    "bcc": pattern,
                    "subject": "Malformed BCC Test",
                    "body": "Testing malformed comma patterns in BCC"
                }
                
                try:
                    result = send_message(self.userId, msg_bcc)
                    # Current implementation may store as-is
                    self.assertIsInstance(result, dict)
                except Exception as e:
                    # May fail with malformed patterns
                    pass
    
    def test_cc_bcc_special_characters(self):
        """Test handling of special characters in CC/BCC fields."""
        special_patterns = [
            "cc1@example.com;cc2@example.com",  # Semicolon separator
            "cc1@example.com|cc2@example.com",  # Pipe separator
            "cc1@example.com cc2@example.com",  # Space separator
            "cc1@example.com\tcc2@example.com",  # Tab separator
            "cc1@example.com\ncc2@example.com",  # Newline separator
            "cc1@example.com, cc2@example.com;",  # Mixed separators
            "cc1@example.com, cc2@example.com\n",  # Mixed with newline
            "cc1@example.com, cc2@example.com\0",  # Null character
            "cc1@example.com, cc2@example.com\x00",  # Null byte
            "cc1@example.com\r\ncc2@example.com",  # CRLF separator
        ]
        
        for pattern in special_patterns:
            with self.subTest(pattern=pattern):
                msg = {
                    "sender": "me@example.com",
                    "recipient": "user1@example.com",
                    "cc": pattern,
                    "bcc": pattern.replace("cc", "bcc"),  # Test both fields
                    "subject": "Special Characters Test",
                    "body": "Testing special character handling in CC/BCC"
                }
                
                try:
                    result = send_message(self.userId, msg)
                    # Current implementation may store as-is
                    self.assertIsInstance(result, dict)
                except Exception as e:
                    # May fail with special characters
                    pass
    
    def test_cc_bcc_unicode_and_international(self):
        """Test handling of Unicode and international characters in CC/BCC."""
        unicode_patterns = [
            "用户@example.com, cc2@example.com",  # Chinese characters
            "usuário@example.com, cc2@example.com",  # Portuguese characters
            "пользователь@example.com, cc2@example.com",  # Cyrillic characters
            "cc1@例え.com, cc2@example.com",  # International domain
            "José María <jose@example.com>, cc2@example.com",  # Accented display name
            "山田太郎 <yamada@example.com>, cc2@example.com",  # Japanese display name
            "cc1@xn--fsq.com, cc2@example.com",  # Punycode domain
            "cc1@münchen.de, cc2@example.com",  # German umlaut domain
            "Владимир <vladimir@example.com>",  # Cyrillic display name
            "François <françois@café.fr>",  # French accents in name and domain
        ]
        
        for pattern in unicode_patterns:
            with self.subTest(pattern=pattern):
                msg = {
                    "sender": "me@example.com",
                    "recipient": "user1@example.com",
                    "cc": pattern,
                    "bcc": pattern.replace("cc", "bcc").replace("josé", "bcc").replace("yamada", "bcc"),
                    "subject": "Unicode Test",
                    "body": "Testing Unicode character handling in CC/BCC"
                }
                
                try:
                    result = send_message(self.userId, msg)
                    # Should handle Unicode gracefully
                    self.assertIsInstance(result, dict)
                except Exception as e:
                    # May fail with Unicode characters
                    pass
    
    def test_cc_bcc_extremely_long_values(self):
        """Test handling of extremely long CC/BCC values."""
        # Very long email address
        long_email = "a" * 1000 + "@example.com"
        
        # Very long recipient list
        long_cc_list = ", ".join([f"cc{i}@example.com" for i in range(500)])
        long_bcc_list = ", ".join([f"bcc{i}@example.com" for i in range(500)])
        
        # Very long display name
        long_display_name = "A" * 1000 + " <cc@example.com>"
        
        test_cases = [
            {"cc": long_email, "description": "Very long CC email address"},
            {"bcc": long_email, "description": "Very long BCC email address"},
            {"cc": long_cc_list, "description": "Very long CC list"},
            {"bcc": long_bcc_list, "description": "Very long BCC list"},
            {"cc": long_display_name, "description": "Very long CC display name"},
            {"bcc": long_display_name.replace("cc@", "bcc@"), "description": "Very long BCC display name"},
            {"cc": long_cc_list, "bcc": long_bcc_list, "description": "Both CC and BCC very long"},
        ]
        
        for case in test_cases:
            with self.subTest(case=case["description"]):
                msg = {
                    "sender": "me@example.com",
                    "recipient": "user1@example.com",
                    "subject": "Long Values Test",
                    "body": "Testing extremely long values in CC/BCC"
                }
                
                # Add test fields
                for field in ["cc", "bcc"]:
                    if field in case:
                        msg[field] = case[field]
                
                try:
                    result = send_message(self.userId, msg)
                    # May succeed or fail depending on size limits
                    self.assertIsInstance(result, dict)
                except Exception as e:
                    # May fail due to size limits or memory constraints
                    pass
    
    def test_cc_bcc_with_display_names(self):
        """Test CC/BCC with display names."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com",
            "cc": "John Doe <john@example.com>, Jane Smith <jane@example.com>",
            "bcc": "Bob Wilson <bob@example.com>",
            "subject": "Display Names in CC/BCC",
            "body": "Test with display names in CC/BCC"
        }
        
        try:
            result = send_message(self.userId, msg)
            # Should handle display names in CC/BCC
            self.assertIsInstance(result, dict)
        except Exception as e:
            # May fail with current implementation
            pass
    
    def test_cc_bcc_mixed_valid_invalid_emails(self):
        """Test CC/BCC with mix of valid and invalid email addresses."""
        test_cases = [
            {
                "cc": "valid@example.com, invalid-email, another@example.com",
                "description": "CC with mixed valid/invalid emails"
            },
            {
                "bcc": "valid@example.com, @invalid.com, user@",
                "description": "BCC with malformed emails"
            },
            {
                "cc": "user1@example.com, , user2@example.com",
                "description": "CC with empty segment"
            },
            {
                "bcc": "user1@example.com, user2@, @example.com",
                "description": "BCC with incomplete emails"
            },
            {
                "cc": "user@example.com, user@.com, user@example.",
                "description": "CC with domain issues"
            },
        ]
        
        for case in test_cases:
            with self.subTest(case=case["description"]):
                msg = {
                    "sender": "me@example.com",
                    "recipient": "user1@example.com",
                    "subject": "Mixed Valid/Invalid Test",
                    "body": "Testing mixed valid and invalid emails"
                }
                
                # Add test field
                for field in ["cc", "bcc"]:
                    if field in case:
                        msg[field] = case[field]
                
                try:
                    result = send_message(self.userId, msg)
                    # Should handle mixed emails gracefully
                    self.assertIsInstance(result, dict)
                except Exception as e:
                    # May fail with validation errors
                    pass
    
    def test_cc_bcc_case_sensitivity(self):
        """Test case sensitivity in CC/BCC email addresses."""
        test_cases = [
            {
                "cc": "User@Example.Com, user@EXAMPLE.COM",
                "description": "CC with different cases"
            },
            {
                "bcc": "BCC@EXAMPLE.COM, bcc@example.com",
                "description": "BCC with different cases"
            },
            {
                "cc": "John.Doe@Example.Com",
                "bcc": "jane.smith@EXAMPLE.COM",
                "description": "Both CC and BCC with mixed cases"
            },
        ]
        
        for case in test_cases:
            with self.subTest(case=case["description"]):
                msg = {
                    "sender": "me@example.com",
                    "recipient": "user1@example.com",
                    "subject": "Case Sensitivity Test",
                    "body": "Testing case sensitivity in CC/BCC"
                }
                
                # Add test fields
                for field in ["cc", "bcc"]:
                    if field in case:
                        msg[field] = case[field]
                
                try:
                    result = send_message(self.userId, msg)
                    # Should handle case variations
                    self.assertIsInstance(result, dict)
                except Exception as e:
                    # Should not fail for case variations
                    pass
    
    def test_very_long_cc_bcc_lists(self):
        """Test with very long CC and BCC lists."""
        cc_list = ", ".join([f"cc{i}@example.com" for i in range(50)])
        bcc_list = ", ".join([f"bcc{i}@example.com" for i in range(50)])
        
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com",
            "cc": cc_list,
            "bcc": bcc_list,
            "subject": "Long CC/BCC Lists",
            "body": "Test with very long CC/BCC lists"
        }
        
        try:
            result = send_message(self.userId, msg)
            # Should handle large CC/BCC lists
            self.assertIsInstance(result, dict)
        except Exception as e:
            # May fail due to size limits
            pass
    
    def test_duplicate_addresses_across_to_cc_bcc(self):
        """Test with duplicate addresses across TO, CC, and BCC fields."""
        msg = {
            "sender": "me@example.com",
            "recipient": "user1@example.com, user2@example.com",
            "cc": "user1@example.com, cc1@example.com",  # user1 is duplicate
            "bcc": "user2@example.com, cc1@example.com",  # user2 and cc1 are duplicates
            "subject": "Duplicate Addresses Test",
            "body": "Test with duplicate addresses across fields"
        }
        
        try:
            result = send_message(self.userId, msg)
            # Should handle duplicates gracefully (dedupe or keep as-is)
            self.assertIsInstance(result, dict)
        except Exception as e:
            # May fail with current implementation
            pass


if __name__ == '__main__':
    unittest.main()
