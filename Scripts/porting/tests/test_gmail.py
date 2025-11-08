import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
import sys
import re

# Add project root to path for imports
ROOT = Path(__file__).resolve().parents[3]
APIS_PATH = ROOT / "APIs"
if str(APIS_PATH) not in sys.path:
    sys.path.insert(0, str(APIS_PATH))

# Import the functions and modules under test
from Scripts.porting.port_gmail import (
    port_gmail, 
    convert_datetime_with_tz, 
    transform_email_entry,
    normalize_labels
)


class TestGmailPortingTDD:
    """Gmail porting tests written with pure TDD principles - testing contracts and ideal behavior"""

    # Test Case 1: DateTime conversion must handle timezones properly (TDD)
    def test_datetime_conversion_respects_timezones(self):
        """DateTime conversion must properly handle timezone conversion to UTC"""
        # Contract: When given a datetime with timezone, output should be converted to UTC
        test_cases = [
            ("2024-01-15T10:00:00", "UTC", "2024-01-15T10:00:00Z"),
            ("2024-01-15T10:00:00", "America/New_York", "2024-01-15T15:00:00Z"),  # EST +5
            ("2024-01-15T10:00:00", "Europe/London", "2024-01-15T10:00:00Z"),     # GMT 
            ("2024-01-15T10:00:00", "Asia/Tokyo", "2024-01-15T01:00:00Z"),        # JST -9
        ]
        
        for input_dt, input_tz, expected_utc in test_cases:
            utc_date, epoch = convert_datetime_with_tz(input_dt, input_tz)
            
            # MUST convert timezone to UTC (not ignore timezone like current code)
            assert utc_date == expected_utc, \
                f"Timezone conversion failed: {input_dt} {input_tz} should become {expected_utc}, got {utc_date}"
            
            # Epoch MUST match the UTC datetime
            expected_timestamp = int(datetime.fromisoformat(expected_utc.replace("Z", "+00:00")).timestamp())
            assert epoch == str(expected_timestamp), \
                f"Epoch mismatch: expected {expected_timestamp}, got {epoch}"
    
    def test_datetime_conversion_validates_input_format(self):
        """DateTime conversion must validate input and fail gracefully on invalid input"""
        invalid_formats = [
            "",
            "not-a-date", 
            "2024-13-45T25:70:99",  # Invalid values
            "2024/01/15 10:30:00",  # Wrong format
            None,
            2024,  # Wrong type
        ]
        
        for invalid_input in invalid_formats:
            with pytest.raises((ValueError, TypeError), 
                             match="Invalid datetime format|Invalid input type"):
                convert_datetime_with_tz(invalid_input, "UTC")

    # Test Case 2: Recipients must be validated and formatted properly (TDD)
    def test_recipients_validation_and_formatting(self):
        """Recipients must be validated as valid emails and formatted consistently"""
        test_data = {
            "profile": {"emailAddress": "sender@gmail.com"},
            "messages": {
                "msg-1": {
                    "id": "msg-1",
                    "threadId": "thread-1",
                    "sender": "sender@gmail.com",
                    "recipients": ["alice@example.com", "bob@test.org", "charlie@company.co.uk"],
                    "subject": "Multi-recipient Test",
                    "body": "Testing multiple recipients.",
                    "date": "2024-01-15T10:30:00",
                    "timeZone": "UTC"
                }
            }
        }
        
        result, message = port_gmail(json.dumps(test_data))
        assert result is not None, f"Valid recipients should not fail: {message}"
        
        msg = result["users"]["me"]["messages"]["msg-1"]
        
        # MUST format recipients consistently with RFC 5322 standard
        assert msg["recipient"] == "alice@example.com, bob@test.org, charlie@company.co.uk"
        
        # To header MUST match recipient field exactly
        to_header = next(h for h in msg["payload"]["headers"] if h["name"] == "To")
        assert to_header["value"] == msg["recipient"]
        
    def test_recipients_rejects_invalid_emails(self):
        """System must reject invalid email addresses in recipients"""
        invalid_recipients_tests = [
            ["invalid-email"],
            ["@domain.com"],
            ["user@"],
            ["user@@domain.com"],
            ["user space@domain.com"],
        ]
        
        for invalid_recipients in invalid_recipients_tests:
            test_data = {
                "profile": {"emailAddress": "sender@gmail.com"},
                "messages": {
                    "msg-1": {
                        "id": "msg-1",
                        "sender": "sender@gmail.com", 
                        "recipients": invalid_recipients,
                        "subject": "Test",
                        "body": "Test",
                        "date": "2024-01-15T10:30:00",
                        "timeZone": "UTC"
                    }
                }
            }
            
            result, message = port_gmail(json.dumps(test_data))
            # MUST fail gracefully with clear error message
            assert result is None, f"Invalid recipients should be rejected: {invalid_recipients}"
            assert "Invalid email" in message or "recipient" in message.lower(), \
                f"Error message should mention email validation: {message}"

    # Test Case 3: Email headers must be RFC compliant (TDD)
    def test_email_headers_rfc_compliance(self):
        """Email headers must follow RFC 5322 standards"""
        test_data = {
            "profile": {"emailAddress": "test@gmail.com"},
            "messages": {
                "msg-1": {
                    "id": "msg-1",
                    "sender": "alice@example.com",
                    "recipients": ["test@gmail.com"],
                    "subject": "Test Message with Special Chars: äöü & < >",
                    "body": "Body content",
                    "date": "2024-01-15T10:30:00",
                    "timeZone": "UTC"
                }
            }
        }
        
        result, message = port_gmail(json.dumps(test_data))
        assert result is not None, f"Valid message should not fail: {message}"
        
        headers = result["users"]["me"]["messages"]["msg-1"]["payload"]["headers"]
        
        # MUST have exactly these required headers
        required_headers = {"From", "To", "Subject", "Date"}
        header_names = {h["name"] for h in headers}
        assert required_headers.issubset(header_names), \
            f"Missing required headers: {required_headers - header_names}"
        
        # Headers MUST be properly encoded/escaped
        subject_header = next(h for h in headers if h["name"] == "Subject")
        assert len(subject_header["value"]) > 0, "Subject header cannot be empty"
        
        # Date header MUST be in UTC format
        date_header = next(h for h in headers if h["name"] == "Date")
        assert date_header["value"].endswith("Z"), "Date header must be in UTC format"
        
        # From/To headers MUST contain valid emails
        from_header = next(h for h in headers if h["name"] == "From")
        to_header = next(h for h in headers if h["name"] == "To")
        assert "@" in from_header["value"], "From header must contain valid email"
        assert "@" in to_header["value"], "To header must contain valid email"

    # Test Case 4: System labels must follow Gmail specifications (TDD)
    def test_system_labels_gmail_specification(self):
        """System labels must exactly match Gmail API specifications"""
        test_data = {
            "profile": {"emailAddress": "test@gmail.com"},
            "messages": {},
            "labels": ["Custom Label", "Work Project", "Important Stuff"]
        }
        
        result, message = port_gmail(json.dumps(test_data))
        assert result is not None, f"Label processing should not fail: {message}"
        
        labels = result["users"]["me"]["labels"]
        
        # MUST include all Gmail system labels with exact specifications
        required_system_labels = {
            "INBOX": {"labelListVisibility": "labelShow", "messageListVisibility": "show", "type": "system"},
            "SENT": {"labelListVisibility": "labelHide", "messageListVisibility": "hide", "type": "system"},
            "DRAFT": {"labelListVisibility": "labelHide", "messageListVisibility": "hide", "type": "system"},
            "TRASH": {"labelListVisibility": "labelHide", "messageListVisibility": "hide", "type": "system"},
            "SPAM": {"labelListVisibility": "labelHide", "messageListVisibility": "hide", "type": "system"},
            "UNREAD": {"labelListVisibility": "labelShow", "messageListVisibility": "show", "type": "system"},
            "IMPORTANT": {"labelListVisibility": "labelShow", "messageListVisibility": "show", "type": "system"},
        }
        
        for label_id, expected_attrs in required_system_labels.items():
            assert label_id in labels, f"Missing required system label: {label_id}"
            label = labels[label_id]
            for attr, expected_value in expected_attrs.items():
                assert label[attr] == expected_value, \
                    f"Label {label_id} {attr} should be {expected_value}, got {label[attr]}"
        
        # Custom labels MUST be transformed consistently
        assert "CUSTOM_LABEL" in labels, "Custom labels should be transformed to uppercase with underscores"
        assert "WORK_PROJECT" in labels, "Multi-word labels should use underscores"
        assert "IMPORTANT_STUFF" in labels, "All custom labels should follow same pattern"
        
        # Custom labels MUST have user type and hidden visibility
        custom_labels = [l for l in labels.values() if l["type"] == "user"]
        for custom_label in custom_labels:
            assert custom_label["labelListVisibility"] == "labelHide", \
                f"Custom label should have labelHide: {custom_label}"
            assert custom_label["messageListVisibility"] == "hide", \
                f"Custom label should have hide: {custom_label}"

    # Test Case 5: SendAs profile generation must be secure and valid (TDD)
    def test_sendas_profile_security_and_validation(self):
        """SendAs profiles must be securely generated with proper validation"""
        test_cases = [
            "user@gmail.com",
            "complex.email+tag@subdomain.example.org",
            "test123@company-name.co.uk"
        ]
        
        for email in test_cases:
            test_data = {
                "profile": {"emailAddress": email},
                "messages": {}
            }
            
            result, message = port_gmail(json.dumps(test_data))
            assert result is not None, f"Valid email should not fail: {email}"
            
            send_as = result["users"]["me"]["settings"]["sendAs"]
            assert email in send_as, f"SendAs profile should be created for {email}"
            
            profile = send_as[email]
            
            # MUST have all required fields with valid values
            assert profile["sendAsEmail"] == email, "SendAs email must match profile email"
            assert len(profile["displayName"]) > 0, "Display name cannot be empty"
            assert profile["replyToAddress"] == email, "Reply-to must match send-as email"
            assert len(profile["signature"]) > 0, "Signature cannot be empty"
            assert profile["verificationStatus"] == "accepted", "Verification status must be accepted"
            
            # MUST include S/MIME configuration
            assert "smimeInfo" in profile, "S/MIME info is required"
            assert len(profile["smimeInfo"]) > 0, "S/MIME info cannot be empty"
            
    def test_sendas_rejects_invalid_emails(self):
        """SendAs profile generation must reject invalid emails"""
        invalid_emails = ["invalid", "@domain.com", "user@", "user@@domain.com"]
        
        for invalid_email in invalid_emails:
            test_data = {"profile": {"emailAddress": invalid_email}}
            
            result, message = port_gmail(json.dumps(test_data))
            assert result is None, f"Invalid email should be rejected: {invalid_email}"
            assert "Invalid email" in message or "email" in message.lower(), \
                f"Error should mention email validation: {message}"

    # Test Case 6: Counter accuracy must be mathematically correct (TDD)
    def test_counter_mathematical_accuracy(self):
        """Counters must accurately reflect actual data counts"""
        # Create test data with known counts
        test_data = {
            "profile": {"emailAddress": "test@gmail.com"},
            "messages": {f"msg-{i}": {
                "id": f"msg-{i}",
                "sender": "sender@example.com",
                "recipients": ["test@gmail.com"],
                "subject": f"Message {i}",
                "body": f"Body {i}",
                "date": "2024-01-15T10:30:00",
                "timeZone": "UTC"
            } for i in range(1, 6)},  # 5 messages
            "threads": {f"thread-{i}": {
                "id": f"thread-{i}",
                "messageIds": [f"msg-{i}"]
            } for i in range(1, 4)},  # 3 threads
            "drafts": {f"draft-{i}": {
                "id": f"draft-{i}",
                "sender": "test@gmail.com",
                "recipients": ["recipient@example.com"],
                "subject": f"Draft {i}",
                "body": f"Draft body {i}",
                "date": "2024-01-15T10:30:00",
                "timeZone": "UTC"
            } for i in range(1, 3)},  # 2 drafts
            "attachments": {f"att-{i}": {
                "attachmentId": f"att-{i}",
                "filename": f"file{i}.pdf",
                "size": 1024
            } for i in range(1, 4)}  # 3 attachments
        }
        
        result, message = port_gmail(json.dumps(test_data))
        assert result is not None, f"Counter test data should not fail: {message}"
        
        counters = result["counters"]
        
        # Counters MUST exactly match actual counts
        assert counters["message"] == 5, f"Message counter incorrect: expected 5, got {counters['message']}"
        assert counters["thread"] == 3, f"Thread counter incorrect: expected 3, got {counters['thread']}"
        assert counters["draft"] == 2, f"Draft counter incorrect: expected 2, got {counters['draft']}"
        assert counters["attachment"] == 3, f"Attachment counter incorrect: expected 3, got {counters['attachment']}"
        
        # MUST also count system-generated items
        assert counters["label"] >= 7, "Must count at least 7 system labels"
        
        # All counters MUST be non-negative integers
        for counter_name, counter_value in counters.items():
            assert isinstance(counter_value, int), f"Counter {counter_name} must be integer"
            assert counter_value >= 0, f"Counter {counter_name} cannot be negative"

    # Test Case 7: Gmail API structure compliance must be exact (TDD)
    def test_gmail_api_structure_compliance(self):
        """Output structure must exactly match Gmail API specifications"""
        test_data = {
            "profile": {"emailAddress": "test@gmail.com"},
            "messages": {
                "msg-1": {
                    "id": "msg-1",
                    "sender": "sender@example.com",
                    "recipients": ["test@gmail.com"],
                    "subject": "Test",
                    "body": "Test body",
                    "date": "2024-01-15T10:30:00",
                    "timeZone": "UTC"
                }
            }
        }
        
        result, message = port_gmail(json.dumps(test_data))
        assert result is not None, f"API compliance test should not fail: {message}"
        
        # Top-level structure MUST match Gmail API
        required_top_level = {"users", "attachments", "counters"}
        assert required_top_level.issubset(result.keys()), \
            f"Missing top-level keys: {required_top_level - set(result.keys())}"
        
        # users.me structure MUST be complete
        me = result["users"]["me"]
        required_me_fields = {"profile", "messages", "drafts", "threads", "labels", "settings"}
        assert required_me_fields.issubset(me.keys()), \
            f"Missing users.me fields: {required_me_fields - set(me.keys())}"
        
        # Message structure MUST follow Gmail API message resource
        msg = me["messages"]["msg-1"]
        required_msg_fields = {"id", "threadId", "raw", "payload", "internalDate"}
        assert required_msg_fields.issubset(msg.keys()), \
            f"Missing message fields: {required_msg_fields - set(msg.keys())}"
        
        # Payload MUST have correct structure
        payload = msg["payload"]
        assert "mimeType" in payload, "Payload missing mimeType"
        assert "headers" in payload, "Payload missing headers"
        assert "parts" in payload, "Payload missing parts"
        
        # internalDate MUST be numeric string (Gmail API requirement)
        assert msg["internalDate"].isdigit(), "internalDate must be numeric string"
        assert len(msg["internalDate"]) >= 10, "internalDate should be in milliseconds or seconds"

    # Test Case 8: IMAP settings must have secure defaults (TDD)
    def test_imap_settings_secure_defaults(self):
        """IMAP settings must have secure, production-ready defaults"""
        test_data = {
            "profile": {"emailAddress": "test@gmail.com"},
            "messages": {}
        }
        
        result, message = port_gmail(json.dumps(test_data))
        assert result is not None, f"IMAP settings test should not fail: {message}"
        
        settings = result["users"]["me"]["settings"]
        
        # IMAP MUST have secure defaults
        imap = settings["imap"]
        assert imap["enabled"] is True, "IMAP should be enabled by default"
        assert imap["server"] == "imap.gmail.com", "IMAP server must be Gmail's secure server"
        assert imap["port"] == 993, "IMAP must use secure port 993 (SSL/TLS)"
        
        # POP MUST have different, secure defaults
        pop = settings["pop"]
        assert pop["enabled"] is False, "POP should be disabled by default (less secure)"
        assert pop["server"] == "pop.gmail.com", "POP server must be Gmail's server"
        assert pop["port"] == 995, "POP must use secure port 995 (SSL/TLS)"
        
        # Custom settings MUST override defaults securely
        custom_data = test_data.copy()
        custom_data["settings"] = {
            "imap": {"enabled": False, "server": "custom.example.com", "port": 143}
        }
        
        custom_result, custom_message = port_gmail(json.dumps(custom_data))
        assert custom_result is not None, f"Custom IMAP settings should work: {custom_message}"
        
        custom_imap = custom_result["users"]["me"]["settings"]["imap"]
        assert custom_imap["enabled"] is False, "Custom IMAP settings should override defaults"
        assert custom_imap["server"] == "custom.example.com", "Custom server should be preserved"

    # Test Case 9: Draft handling must support both formats consistently (TDD)
    def test_draft_format_consistency(self):
        """Draft handling must work consistently for both nested and direct formats"""
        test_data = {
            "profile": {"emailAddress": "user@gmail.com"},
            "drafts": {
                "draft-nested": {
                    "id": "draft-nested",
                    "message": {  # Nested format
                        "sender": "user@gmail.com",
                        "recipients": ["recipient@example.com"],
                        "subject": "Nested Draft",
                        "body": "Nested draft body",
                        "date": "2024-01-15T10:30:00",
                        "timeZone": "UTC"
                    }
                },
                "draft-direct": {  # Direct format
                    "id": "draft-direct",
                    "sender": "user@gmail.com",
                    "recipients": ["another@example.com"],
                    "subject": "Direct Draft",
                    "body": "Direct draft body",
                    "date": "2024-01-15T11:00:00",
                    "timeZone": "UTC"
                }
            }
        }
        
        result, message = port_gmail(json.dumps(test_data))
        assert result is not None, f"Draft handling should not fail: {message}"
        
        drafts = result["users"]["me"]["drafts"]
        
        # Both formats MUST produce identical structure
        for draft_id in ["draft-nested", "draft-direct"]:
            assert draft_id in drafts, f"Draft {draft_id} should be processed"
            draft = drafts[draft_id]
            
            # MUST have consistent structure regardless of input format
            assert "id" in draft, f"Draft {draft_id} missing id"
            assert "message" in draft, f"Draft {draft_id} missing message"
            
            msg = draft["message"]
            required_fields = {"sender", "recipient", "subject", "body", "date", "payload", "raw"}
            assert required_fields.issubset(msg.keys()), \
                f"Draft {draft_id} message missing fields: {required_fields - set(msg.keys())}"
            
            # Message content MUST be properly transformed
            assert "@" in msg["sender"], f"Draft {draft_id} sender should be valid email"
            assert "@" in msg["recipient"], f"Draft {draft_id} recipient should be valid email"
            assert msg["date"].endswith("Z"), f"Draft {draft_id} date should be UTC format"

    # Test Case 10: Malformed input must fail gracefully with helpful errors (TDD)
    def test_malformed_input_graceful_failure(self):
        """System must handle malformed input gracefully with helpful error messages"""
        
        malformed_inputs = [
            # Invalid JSON
            ('{"invalid": json}', "Invalid JSON syntax"),
            
            # Missing required fields
            ('{}', "Missing required profile"),
            ('{"profile": {}}', "Missing required emailAddress"),
            
            # Invalid data types
            ('{"profile": {"emailAddress": 123}}', "emailAddress must be string"),
            ('{"profile": {"emailAddress": "test@gmail.com"}, "messages": "not-a-dict"}', "messages must be object"),
            
            # Malformed messages
            ('{"profile": {"emailAddress": "test@gmail.com"}, "messages": {"msg-1": {"invalid": "message"}}}', "Invalid message structure"),
        ]
        
        for malformed_input, expected_error_type in malformed_inputs:
            result, message = port_gmail(malformed_input)
            
            # MUST fail gracefully (not crash)
            assert result is None, f"Malformed input should be rejected: {malformed_input[:50]}..."
            
            # MUST provide helpful error message
            assert message is not None and len(message) > 0, \
                f"Error message should not be empty for: {malformed_input[:50]}..."
            
            # Error message SHOULD be helpful (not just generic)
            assert len(message) > 10, f"Error message should be descriptive: {message}"

    # Test Case 11: Attachment preservation must be complete and accurate (TDD)
    def test_attachment_complete_preservation(self):
        """All attachment data must be preserved exactly without modification"""
        test_data = {
            "profile": {"emailAddress": "test@gmail.com"},
            "attachments": {
                "att-1": {
                    "attachmentId": "att-1",
                    "filename": "document.pdf",
                    "mimeType": "application/pdf",
                    "size": 2048,
                    "customField": "should be preserved"  # Custom fields should pass through
                },
                "att-2": {
                    "attachmentId": "att-2",
                    "filename": "image.jpg",
                    "mimeType": "image/jpeg", 
                    "size": 1024000,
                    "metadata": {"creator": "user", "date": "2024-01-15"}  # Nested data
                }
            }
        }
        
        result, message = port_gmail(json.dumps(test_data))
        assert result is not None, f"Attachment preservation should not fail: {message}"
        
        result_attachments = result["attachments"]
        original_attachments = test_data["attachments"]
        
        # MUST preserve all attachments
        assert len(result_attachments) == len(original_attachments), \
            f"Attachment count mismatch: expected {len(original_attachments)}, got {len(result_attachments)}"
        
        # MUST preserve every field exactly
        for att_id, original_att in original_attachments.items():
            assert att_id in result_attachments, f"Attachment {att_id} missing from result"
            result_att = result_attachments[att_id]
            
            # Every field must be preserved exactly
            for field, value in original_att.items():
                assert field in result_att, f"Attachment {att_id} missing field {field}"
                assert result_att[field] == value, \
                    f"Attachment {att_id} field {field} modified: expected {value}, got {result_att[field]}"
        
        # MUST update counter accurately
        assert result["counters"]["attachment"] == len(original_attachments), \
            f"Attachment counter incorrect: expected {len(original_attachments)}, got {result['counters']['attachment']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
