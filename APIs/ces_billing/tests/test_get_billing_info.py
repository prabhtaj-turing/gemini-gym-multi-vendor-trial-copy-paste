import pytest
import sys
import os
from pydantic import ValidationError as PydanticValidationError

# Add the parent directory to the path so we can import the service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ces_billing_service import get_billing_info
from ces_billing.SimulationEngine.models import (
    GetbillinginfoResponse,
    GetbillinginfoFulfillmentinfo,
    GetbillinginfoSessioninfo,
    GetbillinginfoSessioninfoParameters
)
from ces_billing.SimulationEngine.custom_errors import BillingDataError, ValidationError as BillingValidationError, InvalidMdnError
from ces_billing.SimulationEngine.db import DB, reset_db_for_tests
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestGetBillingInfo(BaseTestCaseWithErrorHandler):
    """Test cases for the get_billing_info function."""

    def setup_method(self, method):
        """Set up test environment before each test."""
        # Store original DB state
        self._original_db = DB.copy()
        
        # Reset DB to clean state for tests
        reset_db_for_tests()
        
        # Add test bills with call_id for testing
        test_bill_id = "test_bill_123"
        test_call_id = "test_call_123"
        DB["bills"] = {
            test_bill_id: {
                "call_id": test_call_id,
                "mdn": "5551234567",
                "outstandingBalance": "325.98",
                "billduedate": "12/05/2024",
                "autoPay": "false",
                "statusCode": "0000",
                "statusMessage": "SUCCESS",
                "activeMtnCount": "4",
                "pastDueBalance": "0.00",
                "lastPaidDate": "11/17/2024",
                "lastPaymentAmount": "324.46",
                "chargeCounter": "3",
                "chargeCounterList": ["FeatureChange", "TaxCharge", "LateFee"],
                "nextBillEstimate": "150.00",
                "mileStoneDate": "March 15th"
            }
        }
    
    def teardown_method(self, method):
        """Clean up after each test."""
        # Restore original DB state to ensure no test affects the DB
        DB.clear()
        DB.update(self._original_db)

    def test_get_billing_info_with_default_parameters(self):
        """Test get_billing_info with call_id parameter."""
        fulfillment_info = {
                "tag": "billing.action.initviewbill"
        }
        session_info = {
            "parameters": {
                "callId": "test_call_123",
                "mdn": "5551234567"
            }
        }
        result = get_billing_info(fulfillmentInfo=fulfillment_info, sessionInfo=session_info)
        
        assert result["sessionInfo"]["parameters"]["outstandingBalance"] == "325.98"
        assert result["sessionInfo"]["parameters"]["statusCode"] == "0000"

    def test_get_billing_info_bill_not_found(self):
        """Test get_billing_info when a bill is not found."""
        fulfillment_info = {
            "tag": "billing.action.initviewbill"
        }
        session_info = {
            "parameters": {
                "callId": "non_existent_call_id",
                "mdn": "5551234567"
            }
        }
        with pytest.raises(BillingDataError):
            get_billing_info(fulfillmentInfo=fulfillment_info, sessionInfo=session_info)

    def test_get_billing_info_with_fulfillment_info(self):
        """Test get_billing_info with fulfillment info."""
        fulfillment_info = {
            "event": {"type": "billing_inquiry"},
            "tag": "billing.action.initviewbill"
        }
        session_info = {
            "parameters": {
                "callId": "test_call_123",
                "mdn": "5551234567"
            }
        }
        
        result = get_billing_info(fulfillmentInfo=fulfillment_info, sessionInfo=session_info)
        
        assert result["sessionInfo"]["parameters"]["outstandingBalance"] == "325.98"

    def test_get_billing_info_with_session_info(self):
        """Test get_billing_info with session info."""
        session_params = {
            "callId": "test_call_123",
            "mdn": "5551234567"
            # All other fields are OUTPUT fields, not INPUT
            # They should not be in the input session_params
        }
        
        session_info = {
            "parameters": session_params
            # "session" field removed - it's not in the INPUT model
        }
        fulfillment_info = {
            "tag": "billing.action.initviewbill"
        }
        
        result = get_billing_info(fulfillmentInfo=fulfillment_info, sessionInfo=session_info)
        
        assert result["sessionInfo"]["parameters"]["outstandingBalance"] == "325.98"

    def test_get_billing_info_with_both_parameters(self):
        """Test get_billing_info with both fulfillment and session info."""
        fulfillment_info = {
            "event": {"type": "billing_inquiry"},
            "tag": "billing.action.initviewbill"
        }
        
        session_params = {
            "callId": "test_call_123",
            "mdn": "5551234567"
            # All other fields are OUTPUT fields, removed from INPUT
        }
        
        session_info = {
            "parameters": session_params
            # "session" field removed - it's not in the INPUT model
        }
        
        result = get_billing_info(
            fulfillmentInfo=fulfillment_info,
            sessionInfo=session_info
        )
        
        assert result["sessionInfo"]["parameters"]["outstandingBalance"] == "325.98"

    def test_get_billing_info_with_new_mdn_validation_8_digits(self):
        """Test get_billing_info with 8-digit MDN (new minimum)."""
        # First add a bill with 8-digit MDN to the database
        test_bill_id = "test_8_digit_mdn"
        DB["bills"][test_bill_id] = {
            "call_id": "test_call_8_digit",
            "mdn": "12345678",
            "outstandingBalance": "$50.00",
            "additionalContent": "Test 8-digit MDN",
            "billduedate": "12/15/2024",
            "chargeCounter": "1",
            "activeMtnCount": "1",
            "autoPay": "false",
            "pastDueBalance": "$0.00",
            "chargeCounterList": ["MonthlyService"],
            "lastPaidDate": "11/15/2024",
            "lastPaymentAmount": "$50.00",
            "content": "Test content for 8-digit MDN"
        }
        
        fulfillment_info = {"tag": "billing.action.initviewbill"}
        session_info = {
            "parameters": {
                "callId": "test_call_8_digit",
                "mdn": "12345678"
            }
        }
        
        result = get_billing_info(fulfillmentInfo=fulfillment_info, sessionInfo=session_info)
        
        assert result["sessionInfo"]["parameters"]["outstandingBalance"] == "$50.00"
        assert result["sessionInfo"]["parameters"]["statusCode"] == "0000"

    def test_get_billing_info_with_new_mdn_validation_11_digits(self):
        """Test get_billing_info with 11-digit MDN (new maximum)."""
        # First add a bill with 11-digit MDN to the database
        test_bill_id = "test_11_digit_mdn"
        DB["bills"][test_bill_id] = {
            "call_id": "test_call_11_digit",
            "mdn": "12345678901",
            "outstandingBalance": "$75.00",
            "additionalContent": "Test 11-digit MDN",
            "billduedate": "12/20/2024",
            "chargeCounter": "2",
            "activeMtnCount": "1",
            "autoPay": "true",
            "pastDueBalance": "$0.00",
            "chargeCounterList": ["MonthlyService", "DataPlan"],
            "lastPaidDate": "11/20/2024",
            "lastPaymentAmount": "$75.00",
            "content": "Test content for 11-digit MDN"
        }
        
        fulfillment_info = {"tag": "billing.action.initviewbill"}
        session_info = {
            "parameters": {
                "callId": "test_call_11_digit",
                "mdn": "12345678901"
            }
        }
        
        result = get_billing_info(fulfillmentInfo=fulfillment_info, sessionInfo=session_info)
        
        assert result["sessionInfo"]["parameters"]["outstandingBalance"] == "$75.00"
        assert result["sessionInfo"]["parameters"]["statusCode"] == "0000"

    def test_get_billing_info_invalid_mdn_too_short(self):
        """Test get_billing_info with MDN that is too short (7 digits)."""
        fulfillment_info = {"tag": "billing.action.initviewbill"}
        session_info = {
            "parameters": {
                "callId": "test_call_short_mdn",
                "mdn": "1234567"  # 7 digits - should fail
            }
        }
        
        with pytest.raises(InvalidMdnError, match="mdn must be 8-11 digits"):
            get_billing_info(fulfillmentInfo=fulfillment_info, sessionInfo=session_info)

    def test_get_billing_info_invalid_mdn_too_long(self):
        """Test get_billing_info with MDN that is too long (12 digits)."""
        fulfillment_info = {"tag": "billing.action.initviewbill"}
        session_info = {
            "parameters": {
                "callId": "test_call_long_mdn",
                "mdn": "123456789012"  # 12 digits - should fail
            }
        }
        
        with pytest.raises(InvalidMdnError, match="mdn must be 8-11 digits"):
            get_billing_info(fulfillmentInfo=fulfillment_info, sessionInfo=session_info)

    def test_get_billing_info_invalid_mdn_non_numeric(self):
        """Test get_billing_info with non-numeric MDN."""
        fulfillment_info = {"tag": "billing.action.initviewbill"}
        session_info = {
            "parameters": {
                "callId": "test_call_non_numeric_mdn",
                "mdn": "abc1234567"  # non-numeric - should fail
            }
        }
        
        with pytest.raises(InvalidMdnError, match="mdn must be 8-11 digits"):
            get_billing_info(fulfillmentInfo=fulfillment_info, sessionInfo=session_info)

    def test_get_billing_info_with_none_parameters(self):
        """Test get_billing_info with None parameters."""
        # Pydantic validation happens at decorator level before custom error handling
        self.assert_error_behavior(
            get_billing_info,
            PydanticValidationError,
            "fulfillmentInfo",
            fulfillmentInfo=None,
            sessionInfo=None
        )

    def test_get_billing_info_response_structure(self):
        """Test that get_billing_info returns properly structured response."""
        # Create minimal session info
        session_params = {
            "callId": "test_call_123",
            "mdn": "5551234567"
        }
        session_info = {"parameters": session_params}
        fulfillment_info = {"tag": "billing.action.initviewbill"}
        
        result = get_billing_info(fulfillmentInfo=fulfillment_info, sessionInfo=session_info)
        
        # Check that all expected fields are present in OUTPUT
        expected_fields = [
            'outstandingBalance', 'additionalContent', 'billduedate', 'chargeCounter',
            'activeMtnCount', 'autoPay', 'pastDueBalance', 'chargeCounterList',
            'lastPaidDate', 'lastPaymentAmount', 'statusCode', 'content', 'statusMessage'
        ]
        
        for field in expected_fields:
            assert field in result["sessionInfo"]["parameters"]

    def test_get_billing_info_json_serializable(self):
        """Test that get_billing_info response is JSON serializable."""
        import json
        
        # Create minimal session info
        session_params = {
            "callId": "test_call_123",
            "mdn": "5551234567"
        }
        session_info = {"parameters": session_params}
        fulfillment_info = {"tag": "billing.action.initviewbill"}
        
        result = get_billing_info(fulfillmentInfo=fulfillment_info, sessionInfo=session_info)
        
        # Should not raise an exception
        json.dumps(result)
        
        assert isinstance(result, dict)

    def test_get_billing_info_with_minimal_session_info(self):
        """Test get_billing_info with minimal session info."""
        session_params = {
            "callId": "test_call_123",
            "mdn": "5551234567"
            # statusCode and statusMessage are OUTPUT fields, not INPUT
        }
        
        session_info = {"parameters": session_params}
        fulfillment_info = {"tag": "billing.action.initviewbill"}

        result = get_billing_info(fulfillmentInfo=fulfillment_info, sessionInfo=session_info)
        
        # Check the OUTPUT contains statusCode and statusMessage
        assert result["sessionInfo"]["parameters"]["statusCode"] == "0000"
        assert result["sessionInfo"]["parameters"]["statusMessage"] == "Success"
    
    def test_get_billing_info_nonexistent_bill(self):
        """Test get_billing_info with non-existent bill (regression test for bill lookup bug).
        
        This test ensures that when a bill doesn't exist, the function properly raises
        BillingDataError instead of returning the wrong bill. This was a critical bug
        where the loop variable 'bill_id' would retain the last bill ID even when no
        match was found.
        """
        DB["bills"] = {}
        session_params = {
            "callId": "test_call_123",
            "mdn": "5551234567"
        }
        
        session_info = {"parameters": session_params}
        fulfillment_info = {"tag": "billing.action.initviewbill"}
        
        # Should raise BillingDataError for non-existent bill
        self.assert_error_behavior(
            get_billing_info,
            BillingDataError,
            "No bills found in database",
            fulfillmentInfo=fulfillment_info,
            sessionInfo=session_info
        )
    
    def test_get_billing_info_empty_bills_table(self):
        """Test get_billing_info when bills table is empty or missing."""
        # Clear the bills table
        DB["bills"] = {}
        
        session_params = {
            "callId": "test_call_123",
            "mdn": "5551234567"
        }
        
        session_info = {"parameters": session_params}
        fulfillment_info = {"tag": "billing.action.initviewbill"}
        
        # Should raise BillingDataError for empty bills table
        self.assert_error_behavior(
            get_billing_info,
            BillingDataError,
            "No bills found in database",
            fulfillmentInfo=fulfillment_info,
            sessionInfo=session_info
        )
    
    def test_get_billing_info_invalid_nested_sessionInfo(self):
        """Test get_billing_info with invalid nested sessionInfo structure."""
        # sessionInfo.parameters should be a dict, not a string
        session_info = {"parameters": "invalid_string_not_dict"}
        fulfillment_info = {"tag": "billing.action.initviewbill"}
        
        # Pydantic validation happens at decorator level before custom error handling
        self.assert_error_behavior(
            get_billing_info,
            PydanticValidationError,
            "parameters",
            fulfillmentInfo=fulfillment_info,
            sessionInfo=session_info
        )
    
    def test_get_billing_info_invalid_fulfillmentInfo_tag_type(self):
        """Test get_billing_info with invalid tag type in fulfillmentInfo."""
        # tag should be a string, not an int
        fulfillment_info = {"tag": 12345}
        session_params = {
            "callId": "test_call_123",
            "mdn": "5551234567"
        }
        session_info = {"parameters": session_params}
        
        # Pydantic validation happens at decorator level before custom error handling
        self.assert_error_behavior(
            get_billing_info,
            PydanticValidationError,
            "tag",
            fulfillmentInfo=fulfillment_info,
            sessionInfo=session_info
        )
    
    def test_get_billing_info_missing_parameters(self):
        """Test get_billing_info when sessionInfo.parameters is missing."""
        session_info = {}  # No parameters
        fulfillment_info = {"tag": "billing.action.initviewbill"}
        
        # Pydantic validation happens at decorator level
        # The model validator catches this and raises a clean error message
        self.assert_error_behavior(
            get_billing_info,
            PydanticValidationError,
            "sessionInfo.parameters is required",
            fulfillmentInfo=fulfillment_info,
            sessionInfo=session_info
        )
