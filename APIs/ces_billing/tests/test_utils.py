"""Tests for CES Billing Utils module."""

import pytest
import sys
import os
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ces_billing.SimulationEngine.utils import (
    _check_empty_field,
    _check_required_fields,
    _generate_id,
    _format_currency,
    _format_date,
    _validate_account_role,
    _get_current_date,
    _calculate_days_until_due,
    _parse_billing_content,
    _format_balance_display,
    _format_charge_description,
    _is_past_due,
    _get_billing_summary,
    _validate_billing_tag,
    _format_phone_number,
    _generate_call_id,
    _parse_escalation_reason,
    _format_autopay_discount,
    _is_autopay_eligible,
    _get_next_billing_cycle,
    _calculate_estimated_savings,
    _validate_conversation_context,
    _format_error_message,
    _get_supported_actions,
    _is_supported_action,
    _format_timestamp,
    _parse_charge_type,
    _get_charge_priority,
    _generate_sequential_id,
    _validate_mdn,
    get_conversation_end_status
)
from ces_billing.SimulationEngine.custom_errors import InvalidMdnError
from ces_billing.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""
    
    def test_check_empty_field_none(self):
        """Test _check_empty_field with None."""
        assert _check_empty_field(None) is True
    
    def test_check_empty_field_empty_string(self):
        """Test _check_empty_field with empty string."""
        assert _check_empty_field("") is True
        assert _check_empty_field("   ") is True
    
    def test_check_empty_field_empty_list(self):
        """Test _check_empty_field with empty list."""
        assert _check_empty_field([]) is True
    
    def test_check_empty_field_empty_dict(self):
        """Test _check_empty_field with empty dict."""
        assert _check_empty_field({}) is True
    
    def test_check_empty_field_valid_values(self):
        """Test _check_empty_field with valid values."""
        assert _check_empty_field("valid") is False
        assert _check_empty_field(123) is False
        assert _check_empty_field([1, 2, 3]) is False
        assert _check_empty_field({"key": "value"}) is False
    
    def test_check_required_fields_valid(self):
        """Test _check_required_fields with valid data."""
        fields = {"name": "John", "email": "john@example.com"}
        # Should not raise exception
        _check_required_fields(fields)
    
    def test_check_required_fields_missing(self):
        """Test _check_required_fields with missing field."""
        fields = {"name": "", "email": "john@example.com"}
        self.assert_error_behavior(_check_required_fields, ValueError,
                                   "Required field 'name' is missing or empty",
                                   fields=fields)
    
    def test_check_required_fields_none(self):
        """Test _check_required_fields with None field."""
        fields = {"name": None, "email": "john@example.com"}
        self.assert_error_behavior(_check_required_fields, ValueError,
                                   "Required field 'name' is missing or empty",
                                   fields=fields)
    
    def test_generate_id(self):
        """Test _generate_id generates unique IDs."""
        id1 = _generate_id()
        id2 = _generate_id()
        
        assert isinstance(id1, str)
        assert isinstance(id2, str)
        assert id1 != id2
        assert len(id1) > 0
    
    def test_format_currency_valid(self):
        """Test _format_currency with valid amounts."""
        assert _format_currency("123.45") == "$123.45"
        assert _format_currency("0.00") == "$0.00"
        assert _format_currency("1000") == "$1000.00"
    
    def test_format_currency_invalid(self):
        """Test _format_currency with invalid amounts."""
        assert _format_currency("invalid") == "invalid"
        assert _format_currency(None) is None
    
    def test_format_date_valid_formats(self):
        """Test _format_date with valid date formats."""
        assert _format_date("2024-03-15") == "March 15"
        assert _format_date("2024-12-25") == "December 25"
    
    def test_format_date_invalid(self):
        """Test _format_date with invalid dates."""
        assert _format_date("invalid-date") == "invalid-date"
        assert _format_date(None) == "None"
        assert _format_date(123) == "123"
    
    def test_validate_mdn_valid(self):
        """Test _validate_mdn with valid MDNs."""
        assert _validate_mdn("1234567890") == "1234567890"
        assert _validate_mdn("(123) 456-7890") == "1234567890"
        assert _validate_mdn("123-456-7890") == "1234567890"
        assert _validate_mdn("123.456.7890") == "1234567890"

    def test_validate_mdn_valid_8_to_11_digits(self):
        """Test _validate_mdn with valid MDNs in the new 8-11 digit range."""
        # Test 8 digits (new minimum)
        assert _validate_mdn("12345678") == "12345678"
        assert _validate_mdn("(123) 456-78") == "12345678"
        assert _validate_mdn("123-456-78") == "12345678"
        
        # Test 9 digits
        assert _validate_mdn("123456789") == "123456789"
        assert _validate_mdn("(123) 456-789") == "123456789"
        assert _validate_mdn("123-456-789") == "123456789"
        
        # Test 10 digits (existing)
        assert _validate_mdn("1234567890") == "1234567890"
        assert _validate_mdn("(123) 456-7890") == "1234567890"
        assert _validate_mdn("123-456-7890") == "1234567890"
        
        # Test 11 digits (new maximum)
        assert _validate_mdn("12345678901") == "12345678901"
        assert _validate_mdn("(123) 456-78901") == "12345678901"
        assert _validate_mdn("123-456-78901") == "12345678901"

    def test_validate_mdn_invalid_too_short(self):
        """Test _validate_mdn with MDNs that are too short (less than 8 digits)."""
        # Test 7 digits
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("1234567")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        # Test 6 digits
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("123456")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        # Test 5 digits
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("12345")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        # Test 4 digits
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("1234")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        # Test 3 digits
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("123")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        # Test 2 digits
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("12")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        # Test 1 digit
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("1")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")

    def test_validate_mdn_invalid_too_long(self):
        """Test _validate_mdn with MDNs that are too long (more than 11 digits)."""
        # Test 12 digits
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("123456789012")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        # Test 13 digits
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("1234567890123")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        # Test 14 digits
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("12345678901234")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        # Test 15 digits
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("123456789012345")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")

    def test_validate_mdn_invalid_non_numeric(self):
        """Test _validate_mdn with non-numeric characters."""
        # Test letters mixed with numbers
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("abc1234567")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        # Test letter at the end
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("123456789a")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        # Test letter at the beginning
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("a123456789")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        # Test letters in the middle
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("123abc4567")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        # Test special characters
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("123456789!")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("123456789@")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("123456789#")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")

    def test_validate_mdn_invalid_empty_or_none(self):
        """Test _validate_mdn with empty or None values."""
        # Test None
        with self.assertRaises(ValueError) as context:
            _validate_mdn(None)
        self.assertEqual(str(context.exception), "mdn cannot be null")
        
        # Test empty string
        with self.assertRaises(ValueError) as context:
            _validate_mdn("")
        self.assertEqual(str(context.exception), "expected string or bytes-like object, got 'NoneType'")
        
        # Test whitespace only
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("   ")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")

    def test_validate_mdn_invalid_type(self):
        """Test _validate_mdn with invalid input types."""
        with pytest.raises(ValueError, match="mdn must be a string"):
            _validate_mdn(1234567890)  # integer
        
        with pytest.raises(ValueError, match="mdn must be a string"):
            _validate_mdn(1234567890.0)  # float
        
        with pytest.raises(ValueError, match="mdn must be a string"):
            _validate_mdn([])  # list
        
        with pytest.raises(ValueError, match="mdn must be a string"):
            _validate_mdn({})  # dict

    def test_validate_mdn_formatting_edge_cases(self):
        """Test _validate_mdn with various formatting edge cases."""
        # Test with mixed formatting characters (these should all be valid)
        assert _validate_mdn("(123) 456-7890") == "1234567890"
        assert _validate_mdn("123-456-7890") == "1234567890"
        assert _validate_mdn("123.456.7890") == "1234567890"
        assert _validate_mdn("123 456 7890") == "1234567890"
        assert _validate_mdn("+1-123-456-7890") == "11234567890"  # 11 digits with country code
        
        # Test with extra formatting characters that should be stripped
        assert _validate_mdn("+1 (123) 456-7890") == "11234567890"  # 11 digits
        
        # Test that formatting resulting in too many digits fails
        with self.assertRaises(InvalidMdnError) as context:
            _validate_mdn("+1-123-456-7890 ext 123")
        self.assertEqual(str(context.exception), "mdn must be 8-11 digits")
        
        # Test edge case formatting with new 8-digit minimum
        assert _validate_mdn("(123) 456-78") == "12345678"  # 8 digits
        assert _validate_mdn("123-456-78") == "12345678"    # 8 digits
        assert _validate_mdn("123.456.78") == "12345678"    # 8 digits


def test_validate_mdn_invalid_too_short_standalone():
    """Standalone test for _validate_mdn with MDNs that are too short."""
    from ces_billing.SimulationEngine.utils import _validate_mdn
    from ces_billing.SimulationEngine.custom_errors import InvalidMdnError
    
    # Test 7 digits
    with pytest.raises(InvalidMdnError, match="mdn must be 8-11 digits"):
        _validate_mdn("1234567")
    
    # Test 6 digits
    with pytest.raises(InvalidMdnError, match="mdn must be 8-11 digits"):
        _validate_mdn("123456")
    
    # Test 5 digits
    with pytest.raises(InvalidMdnError, match="mdn must be 8-11 digits"):
        _validate_mdn("12345")


def test_validate_mdn_invalid_too_long_standalone():
    """Standalone test for _validate_mdn with MDNs that are too long."""
    from ces_billing.SimulationEngine.utils import _validate_mdn
    from ces_billing.SimulationEngine.custom_errors import InvalidMdnError
    
    # Test 12 digits
    with pytest.raises(InvalidMdnError, match="mdn must be 8-11 digits"):
        _validate_mdn("123456789012")
    
    # Test 13 digits
    with pytest.raises(InvalidMdnError, match="mdn must be 8-11 digits"):
        _validate_mdn("1234567890123")


def test_validate_mdn_invalid_non_numeric_standalone():
    """Standalone test for _validate_mdn with non-numeric characters."""
    from ces_billing.SimulationEngine.utils import _validate_mdn
    from ces_billing.SimulationEngine.custom_errors import InvalidMdnError
    
    # Test letters mixed with numbers
    with pytest.raises(InvalidMdnError, match="mdn must be 8-11 digits"):
        _validate_mdn("abc1234567")
    
    # Test special characters (this will have 9 digits after removing !, so it's valid)
    # Let's test with a case that has fewer digits after removing non-numeric chars
    with pytest.raises(InvalidMdnError, match="mdn must be 8-11 digits"):
        _validate_mdn("1234567!")  # 7 digits after removing !


def test_validate_mdn_invalid_empty_or_none_standalone():
    """Standalone test for _validate_mdn with empty or None values."""
    from ces_billing.SimulationEngine.utils import _validate_mdn
    from ces_billing.SimulationEngine.custom_errors import InvalidMdnError
    
    # Test None - should raise ValidationError (not ValueError)
    from ces_billing.SimulationEngine.custom_errors import ValidationError
    with pytest.raises(ValidationError, match="mdn cannot be null"):
        _validate_mdn(None)
    
    # Test empty string - should raise InvalidMdnError
    with pytest.raises(InvalidMdnError, match="mdn must be 8-11 digits"):
        _validate_mdn("")
    
    # Test whitespace only
    with pytest.raises(InvalidMdnError, match="mdn must be 8-11 digits"):
        _validate_mdn("   ")


class TestUtils(unittest.TestCase):
    """Test cases for utility functions."""
    
    def test_validate_account_role_valid(self):
        """Test _validate_account_role with valid roles."""
        assert _validate_account_role("accountHolder") is True
        assert _validate_account_role("accountManager") is True
        assert _validate_account_role("mobileSecure") is True
        assert _validate_account_role("") is True
    
    def test_validate_account_role_invalid(self):
        """Test _validate_account_role with invalid roles."""
        assert _validate_account_role("invalid_role") is False
        assert _validate_account_role("admin") is False
    
    def test_get_current_date(self):
        """Test _get_current_date returns current date."""
        current_date = _get_current_date()
        assert isinstance(current_date, str)
        assert len(current_date) == 19  # YYYY-MM-DD HH:MM:SS format
        assert current_date.count("-") == 2
        assert current_date.count(":") == 2
    
    def test_calculate_days_until_due_future(self):
        """Test _calculate_days_until_due with future date."""
        future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        days = _calculate_days_until_due(future_date)
        assert days == 5
    
    def test_calculate_days_until_due_past(self):
        """Test _calculate_days_until_due with past date."""
        past_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        days = _calculate_days_until_due(past_date)
        assert days == -3
    
    def test_calculate_days_until_due_invalid(self):
        """Test _calculate_days_until_due with invalid date."""
        days = _calculate_days_until_due("invalid-date")
        assert days == 0
    
    def test_parse_billing_content_empty(self):
        """Test _parse_billing_content with empty content."""
        result = _parse_billing_content([])
        assert result == []
    
    def test_parse_billing_content_valid(self):
        """Test _parse_billing_content with valid content."""
        content = [
            {
                "chargeType": "Monthly Service",
                "amount": "85.00",
                "description": "Unlimited Plan"
            },
            {
                "chargeType": "Device Payment",
                "amount": "25.00",
                "description": "iPhone 15 Pro"
            }
        ]
        
        result = _parse_billing_content(content)
        assert len(result) == 2
        assert result[0]["chargeType"] == "Monthly Service"
        assert result[0]["amount"] == "$85.00"
        assert result[1]["chargeType"] == "Device Payment"
        assert result[1]["amount"] == "$25.00"
    
    def test_format_balance_display_zero(self):
        """Test _format_balance_display with zero balance."""
        result = _format_balance_display("0.00")
        assert "don't have an outstanding balance" in result
    
    def test_format_balance_display_positive(self):
        """Test _format_balance_display with positive balance."""
        result = _format_balance_display("123.45")
        assert result == "$123.45"
    
    def test_format_balance_display_negative(self):
        """Test _format_balance_display with negative balance (credit)."""
        result = _format_balance_display("-50.00")
        assert "credit" in result
        assert "$50.00" in result
    
    def test_format_balance_display_invalid(self):
        """Test _format_balance_display with invalid amount."""
        result = _format_balance_display("invalid")
        assert result == "invalid"
    
    def test_format_charge_description_normal(self):
        """Test _format_charge_description with normal description."""
        result = _format_charge_description("Monthly Service")
        assert result == "Monthly Service"
    
    def test_format_charge_description_md(self):
        """Test _format_charge_description with MD formatting."""
        result = _format_charge_description("MD Service")
        assert result == "M D Service"
    
    def test_format_charge_description_md_only(self):
        """Test _format_charge_description with just MD."""
        result = _format_charge_description("MD")
        assert result == "MD"
    
    def test_format_charge_description_empty(self):
        """Test _format_charge_description with empty description."""
        result = _format_charge_description("")
        assert result == ""
    
    def test_is_past_due_future(self):
        """Test _is_past_due with future due date."""
        future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        result = _is_past_due("100.00", future_date)
        assert result is False
    
    def test_is_past_due_past(self):
        """Test _is_past_due with past due date."""
        past_date = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        result = _is_past_due("100.00", past_date)
        assert result is True
    
    def test_is_past_due_invalid(self):
        """Test _is_past_due with invalid date."""
        result = _is_past_due("100.00", "invalid-date")
        assert result is False
    
    def test_get_billing_summary(self):
        """Test _get_billing_summary."""
        billing_info = {
            "outstandingBalance": "123.45",
            "billduedate": "2024-03-15",
            "pastDueBalance": "0.00",
            "lastPaymentAmount": "100.00",
            "lastPaidDate": "2024-02-15",
            "autoPay": "true"
        }
        
        summary = _get_billing_summary(billing_info)
        assert summary["outstandingBalance"] == "123.45"
        assert summary["dueDate"] == "2024-03-15"
        assert summary["pastDueBalance"] == "0.00"
        assert summary["lastPayment"]["amount"] == "100.00"
        assert summary["lastPayment"]["date"] == "2024-02-15"
        assert summary["autoPay"] is True
        assert "isPastDue" in summary
    
    def test_validate_billing_tag_valid(self):
        """Test _validate_billing_tag with valid tags."""
        assert _validate_billing_tag("billing.action.initviewbill") is True
        assert _validate_billing_tag("billing.action.nextBillEstimate") is True
        assert _validate_billing_tag("billing.action.error") is True
    
    def test_validate_billing_tag_invalid(self):
        """Test _validate_billing_tag with invalid tags."""
        assert _validate_billing_tag("invalid.tag") is False
        assert _validate_billing_tag("") is False
    
    def test_format_phone_number_valid(self):
        """Test _format_phone_number with valid phone numbers."""
        assert _format_phone_number("1234567890") == "(123) 456-7890"
        assert _format_phone_number("(123) 456-7890") == "(123) 456-7890"
        assert _format_phone_number("123-456-7890") == "(123) 456-7890"
    
    def test_format_phone_number_invalid(self):
        """Test _format_phone_number with invalid phone numbers."""
        assert _format_phone_number("123") == "123"
        assert _format_phone_number("") == ""
        assert _format_phone_number(None) is None
    
    def test_generate_call_id(self):
        """Test _generate_call_id generates call IDs."""
        call_id = _generate_call_id()
        assert isinstance(call_id, str)
        assert call_id.startswith("CALL_")
        assert len(call_id) == 13  # "CALL_" + 8 hex chars
    
    def test_parse_escalation_reason_valid(self):
        """Test _parse_escalation_reason with valid reasons."""
        valid_reasons = [
            "billing_dispute",
            "complex_issue",
            "customer_request",
            "technical_error",
            "unsupported_request"
        ]
        
        for reason in valid_reasons:
            assert _parse_escalation_reason(reason) == reason
    
    def test_parse_escalation_reason_invalid(self):
        """Test _parse_escalation_reason with invalid reason."""
        result = _parse_escalation_reason("invalid_reason")
        assert result == "customer_request"
    
    def test_format_autopay_discount_default(self):
        """Test _format_autopay_discount with default amount."""
        result = _format_autopay_discount()
        assert result == "$10.00"
    
    def test_format_autopay_discount_custom(self):
        """Test _format_autopay_discount with custom amount."""
        result = _format_autopay_discount("15.00")
        assert result == "$15.00"
    
    def test_is_autopay_eligible_not_enrolled(self):
        """Test _is_autopay_eligible for non-enrolled customer."""
        billing_info = {"autoPay": "false"}
        assert _is_autopay_eligible(billing_info) is True
    
    def test_is_autopay_eligible_enrolled(self):
        """Test _is_autopay_eligible for enrolled customer."""
        billing_info = {"autoPay": "true"}
        assert _is_autopay_eligible(billing_info) is False
    
    def test_get_next_billing_cycle(self):
        """Test _get_next_billing_cycle."""
        next_cycle = _get_next_billing_cycle()
        assert isinstance(next_cycle, str)
        assert len(next_cycle) == 10  # YYYY-MM-DD format
        
        # Verify it's approximately 30 days from now
        next_cycle_date = datetime.strptime(next_cycle, "%Y-%m-%d")
        today = datetime.now()
        diff = (next_cycle_date - today).days
        assert 25 <= diff <= 35  # Allow some variance
    
    def test_calculate_estimated_savings_default(self):
        """Test _calculate_estimated_savings with default months."""
        savings = _calculate_estimated_savings()
        assert savings == "$120.00"  # 12 months * $10
    
    def test_calculate_estimated_savings_custom(self):
        """Test _calculate_estimated_savings with custom months."""
        savings = _calculate_estimated_savings(6)
        assert savings == "$60.00"  # 6 months * $10
    
    def test_validate_conversation_context_valid(self):
        """Test _validate_conversation_context with valid context."""
        context = {"callId": "test_call_123", "mdn": "1234567890"}
        assert _validate_conversation_context(context) is True
    
    def test_validate_conversation_context_missing_call_id(self):
        """Test _validate_conversation_context with missing callId."""
        context = {"mdn": "1234567890"}
        assert _validate_conversation_context(context) is False
    
    def test_validate_conversation_context_empty_call_id(self):
        """Test _validate_conversation_context with empty callId."""
        context = {"callId": "", "mdn": "1234567890"}
        assert _validate_conversation_context(context) is False
    
    def test_format_error_message(self):
        """Test _format_error_message."""
        result = _format_error_message("5001", "Service unavailable")
        assert result == "Error 5001: Service unavailable"
    
    def test_get_supported_actions(self):
        """Test _get_supported_actions."""
        actions = _get_supported_actions()
        assert isinstance(actions, list)
        assert "get_billing_info" in actions
        assert "escalate" in actions
        assert "autopay" in actions
        assert "bill" in actions
        assert "default_start_flow" in actions
        assert "ghost" in actions
        assert "cancel" in actions
        assert "done" in actions
    
    def test_is_supported_action_valid(self):
        """Test _is_supported_action with valid actions."""
        assert _is_supported_action("get_billing_info") is True
        assert _is_supported_action("escalate") is True
        assert _is_supported_action("autopay") is True
    
    def test_is_supported_action_invalid(self):
        """Test _is_supported_action with invalid actions."""
        assert _is_supported_action("invalid_action") is False
        assert _is_supported_action("") is False
    
    def test_format_timestamp(self):
        """Test _format_timestamp."""
        timestamp = _format_timestamp()
        assert isinstance(timestamp, str)
        # Should be in ISO format
        assert "T" in timestamp
        assert timestamp.count("-") >= 2  # Date part
        assert timestamp.count(":") >= 2  # Time part
    
    def test_parse_charge_type_valid(self):
        """Test _parse_charge_type with valid charge types."""
        assert _parse_charge_type("Monthly Service") == "Monthly Service"
        assert _parse_charge_type("Device Payment") == "Device Payment"
        assert _parse_charge_type("Taxes & Fees") == "Taxes & Fees"
        assert _parse_charge_type("Insurance") == "Device Protection"
        assert _parse_charge_type("Family Plan") == "Family Plan"
    
    def test_parse_charge_type_unknown(self):
        """Test _parse_charge_type with unknown charge type."""
        assert _parse_charge_type("Unknown Type") == "Unknown Type"
    
    def test_get_charge_priority_valid(self):
        """Test _get_charge_priority with valid charge types."""
        assert _get_charge_priority("Monthly Service") == 1
        assert _get_charge_priority("Family Plan") == 1
        assert _get_charge_priority("Device Payment") == 2
        assert _get_charge_priority("Insurance") == 3
        assert _get_charge_priority("Taxes & Fees") == 4
    
    def test_get_charge_priority_unknown(self):
        """Test _get_charge_priority with unknown charge type."""
        assert _get_charge_priority("Unknown Type") == 5
    
    def test_generate_sequential_id_new_section(self):
        """Test _generate_sequential_id creates first ID in empty section."""
        from ces_billing.SimulationEngine.db import DB
        
        # Create a fresh test section
        test_section = "test_sequential_ids"
        if test_section in DB:
            DB[test_section] = {}
        
        # Generate first ID
        first_id = _generate_sequential_id("TEST", [test_section])
        assert first_id == "TEST_001"
        
        # Clean up
        if test_section in DB:
            del DB[test_section]
    
    def test_generate_sequential_id_increments(self):
        """Test _generate_sequential_id increments from existing IDs."""
        from ces_billing.SimulationEngine.db import DB
        
        # Create test section with existing IDs
        test_section = "test_sequential_increment"
        DB[test_section] = {
            "BILL_001": {"data": "test1"},
            "BILL_002": {"data": "test2"},
            "BILL_003": {"data": "test3"}
        }
        
        # Generate next ID - should be BILL_004
        next_id = _generate_sequential_id("BILL", [test_section])
        assert next_id == "BILL_004"
        
        # Clean up
        del DB[test_section]
    
    def test_generate_sequential_id_with_gaps(self):
        """Test _generate_sequential_id with gaps in sequence.
        
        If we have BILL_001 and BILL_003 (missing BILL_002), 
        the next ID should be BILL_004, not BILL_002.
        This tests that the function finds the maximum and increments,
        rather than filling gaps.
        """
        from ces_billing.SimulationEngine.db import DB
        
        # Create test section with gaps in sequence
        test_section = "test_sequential_gaps"
        DB[test_section] = {
            "BILL_001": {"data": "test1"},
            "BILL_003": {"data": "test3"}  # Gap: BILL_002 is missing
        }
        
        # Generate next ID - should be BILL_004 (max + 1), not BILL_002
        next_id = _generate_sequential_id("BILL", [test_section])
        assert next_id == "BILL_004", "Should increment from max (003) to get 004, not fill gap at 002"
        
        # Clean up
        del DB[test_section]
    
    def test_generate_sequential_id_uniqueness(self):
        """Test _generate_sequential_id always generates unique IDs."""
        from ces_billing.SimulationEngine.db import DB
        
        # Create test section
        test_section = "test_sequential_unique"
        DB[test_section] = {}
        
        # Generate multiple IDs and ensure uniqueness
        generated_ids = set()
        for i in range(10):
            new_id = _generate_sequential_id("UNIQUE", [test_section])
            assert new_id not in generated_ids, f"Duplicate ID generated: {new_id}"
            generated_ids.add(new_id)
            # Add to DB to simulate real usage
            DB[test_section][new_id] = {"index": i}
        
        # Verify we got 10 unique sequential IDs
        assert len(generated_ids) == 10
        assert "UNIQUE_001" in generated_ids
        assert "UNIQUE_010" in generated_ids
        
        # Clean up
        del DB[test_section]
    
    def test_generate_sequential_id_nested_path(self):
        """Test _generate_sequential_id with nested DB path."""
        from ces_billing.SimulationEngine.db import DB
        
        # Create nested structure
        if "test_nested" not in DB:
            DB["test_nested"] = {}
        if "level2" not in DB["test_nested"]:
            DB["test_nested"]["level2"] = {}
        
        DB["test_nested"]["level2"]["ESC_001"] = {"data": "test"}
        
        # Generate ID in nested path
        next_id = _generate_sequential_id("ESC", ["test_nested", "level2"])
        assert next_id == "ESC_002"
        
        # Clean up
        del DB["test_nested"]
    
    def test_generate_sequential_id_mixed_prefixes(self):
        """Test _generate_sequential_id with mixed prefixes in same section."""
        from ces_billing.SimulationEngine.db import DB
        
        # Create test section with different prefixes
        test_section = "test_mixed_prefixes"
        DB[test_section] = {
            "BILL_001": {"data": "bill1"},
            "BILL_002": {"data": "bill2"},
            "FLOW_001": {"data": "flow1"},
            "FLOW_005": {"data": "flow5"}
        }
        
        # Generate BILL ID - should only consider BILL_ prefix
        bill_id = _generate_sequential_id("BILL", [test_section])
        assert bill_id == "BILL_003", "Should only count BILL_ prefixed IDs"
        
        # Generate FLOW ID - should only consider FLOW_ prefix
        flow_id = _generate_sequential_id("FLOW", [test_section])
        assert flow_id == "FLOW_006", "Should only count FLOW_ prefixed IDs"
        
        # Clean up
        del DB[test_section]
    
    def test_get_conversation_end_status_all(self):
        """Test get_conversation_end_status returns all statuses when no function_name provided."""
        # Set up test data
        test_statuses = {
            "escalate": "test escalation reason",
            "fail": "test failure reason",
            "cancel": "test cancel reason"
        }
        DB["end_of_conversation_status"] = test_statuses
        
        result = get_conversation_end_status()
        assert result == test_statuses
        assert result["escalate"] == "test escalation reason"
        assert result["fail"] == "test failure reason"
        assert result["cancel"] == "test cancel reason"
        
        # Clean up
        DB["end_of_conversation_status"] = {"escalate": {}, "fail": {}, "cancel": {}, "ghost": {}, "done": {}}
    
    def test_get_conversation_end_status_specific_function(self):
        """Test get_conversation_end_status returns specific function status."""
        # Set up test data
        DB["end_of_conversation_status"] = {
            "escalate": "escalation reason",
            "fail": "failure reason",
            "cancel": None
        }
        
        # Test getting specific function statuses
        assert get_conversation_end_status("escalate") == "escalation reason"
        assert get_conversation_end_status("fail") == "failure reason"
        assert get_conversation_end_status("cancel") is None
        
        # Clean up
        DB["end_of_conversation_status"] = {"escalate": {}, "fail": {}, "cancel": {}, "ghost": {}, "done": {}}
    
    def test_get_conversation_end_status_missing_key(self):
        """Test get_conversation_end_status when DB key doesn't exist."""
        # Remove the key temporarily
        original = DB.pop("end_of_conversation_status", None)
        
        result = get_conversation_end_status()
        assert result is None
        
        # Restore
        if original:
            DB["end_of_conversation_status"] = original
        else:
            DB["end_of_conversation_status"] = {"escalate": {}, "fail": {}, "cancel": {}, "ghost": {}, "done": {}}


if __name__ == "__main__":
    pytest.main([__file__])
