"""Tests for CES Billing Models module."""

import pytest
import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ces_billing.SimulationEngine.models import (
    GetbillinginfoFulfillmentinfo,
    GetbillinginfoResponse,
    GetbillinginfoResponseSessioninfo,
    GetbillinginfoResponseSessioninfoParameters,
    GetbillinginfoSessioninfo,
    GetbillinginfoSessioninfoParameters,
    Session
)


class TestGetbillinginfoFulfillmentinfo:
    """Test cases for GetbillinginfoFulfillmentinfo dataclass."""
    
    def test_fulfillment_info_creation(self):
        """Test creating a GetbillinginfoFulfillmentinfo instance."""
        fulfillment = GetbillinginfoFulfillmentinfo(
            event={"type": "billing_update"},
            tag="billing.action.initviewbill"
        )
        
        assert fulfillment.event == {"type": "billing_update"}
        assert fulfillment.tag == "billing.action.initviewbill"
    
    def test_fulfillment_info_with_none_values(self):
        """Test GetbillinginfoFulfillmentinfo with None values."""
        fulfillment = GetbillinginfoFulfillmentinfo(
            event=None,
            tag=None
        )
        
        assert fulfillment.event is None
        assert fulfillment.tag is None
    
    def test_fulfillment_info_default_values(self):
        """Test GetbillinginfoFulfillmentinfo with default values."""
        fulfillment = GetbillinginfoFulfillmentinfo()
        
        assert fulfillment.event is None
        assert fulfillment.tag is None


class TestGetbillinginfoSessioninfoParameters:
    """Test cases for GetbillinginfoSessioninfoParameters dataclass."""
    
    def test_session_info_parameters_creation(self):
        """Test creating a GetbillinginfoSessioninfoParameters instance."""
        params = GetbillinginfoSessioninfoParameters(
            callId="test_call_123",
            statusCode="0000",
            statusMessage="SUCCESS",
            outstandingBalance="123.45",
            autoPay="false"
        )
        
        assert params.callId == "test_call_123"
        assert params.statusCode == "0000"
        assert params.statusMessage == "SUCCESS"
        assert params.outstandingBalance == "123.45"
        assert params.autoPay == "false"
    
    def test_session_info_parameters_with_none_values(self):
        """Test GetbillinginfoSessioninfoParameters with None values."""
        params = GetbillinginfoSessioninfoParameters()
        
        assert params.callId is None
        assert params.statusCode is None
        assert params.statusMessage is None
        assert params.outstandingBalance is None
        assert params.autoPay is None
    
    def test_session_info_parameters_with_all_fields(self):
        """Test GetbillinginfoSessioninfoParameters with all fields."""
        params = GetbillinginfoSessioninfoParameters(
            accountRole="accountHolder",
            activeMtnCount="4",
            additionalContent="Additional billing info",
            autoPay="true",
            billduedate="12/05/2024",
            callId="test_call_456",
            chargeCounter="3",
            chargeCounterList=["FeatureChange", "TaxCharge"],
            content="Main billing content",
            endPageAction="billing_page",
            lastPaidDate="11/17/2024",
            lastPaymentAmount="324.46",
            mdn="1234567890",
            mileStoneDate="12/01/2024",
            nextBillEstimate="138.45",
            outstandingBalance="325.98",
            pastDueBalance="0.00",
            statusCode="0000",
            statusMessage="SUCCESS"
        )
        
        assert params.accountRole == "accountHolder"
        assert params.activeMtnCount == "4"
        assert params.additionalContent == "Additional billing info"
        assert params.autoPay == "true"
        assert params.billduedate == "12/05/2024"
        assert params.callId == "test_call_456"
        assert params.chargeCounter == "3"
        assert params.chargeCounterList == ["FeatureChange", "TaxCharge"]
        assert params.content == "Main billing content"
        assert params.endPageAction == "billing_page"
        assert params.lastPaidDate == "11/17/2024"
        assert params.lastPaymentAmount == "324.46"
        assert params.mdn == "1234567890"
        assert params.mileStoneDate == "12/01/2024"
        assert params.nextBillEstimate == "138.45"
        assert params.outstandingBalance == "325.98"
        assert params.pastDueBalance == "0.00"
        assert params.statusCode == "0000"
        assert params.statusMessage == "SUCCESS"


class TestGetbillinginfoSessioninfo:
    """Test cases for GetbillinginfoSessioninfo dataclass."""
    
    def test_session_info_creation(self):
        """Test creating a GetbillinginfoSessioninfo instance."""
        params = GetbillinginfoSessioninfoParameters(
            callId="test_call_123",
            statusCode="0000"
        )
        session_info = GetbillinginfoSessioninfo(
            parameters=params,
            session="test_session"
        )
        
        assert session_info.parameters == params
        assert session_info.session == "test_session"
    
    def test_session_info_with_none_values(self):
        """Test GetbillinginfoSessioninfo with None values."""
        session_info = GetbillinginfoSessioninfo()
        
        assert session_info.parameters is None
        assert session_info.session is None


class TestGetbillinginfoResponseSessioninfoParameters:
    """Test cases for GetbillinginfoResponseSessioninfoParameters dataclass."""
    
    def test_response_session_info_parameters_creation(self):
        """Test creating a GetbillinginfoResponseSessioninfoParameters instance."""
        params = GetbillinginfoResponseSessioninfoParameters(
            # Required fields (per tool spec)
            outstandingBalance="123.45",
            additionalContent="Additional details",
            billduedate="12/05/2024",
            chargeCounter="3",
            activeMtnCount="4",
            autoPay="false",
            pastDueBalance="0.00",
            chargeCounterList=["Tax", "Fee"],
            lastPaidDate="11/05/2024",
            lastPaymentAmount="100.00",
            statusCode="0000",
            content="Main content",
            statusMessage="SUCCESS"
            # Note: callId is not a field in the response model
        )
        
        assert params.statusCode == "0000"
        assert params.statusMessage == "SUCCESS"
        assert params.outstandingBalance == "123.45"
        assert params.autoPay == "false"
    
    def test_response_session_info_parameters_with_optional_none(self):
        """Test GetbillinginfoResponseSessioninfoParameters with optional fields as None."""
        params = GetbillinginfoResponseSessioninfoParameters(
            # All required fields provided
            outstandingBalance="123.45",
            additionalContent="Additional details",
            billduedate="12/05/2024",
            chargeCounter="3",
            activeMtnCount="4",
            autoPay="false",
            pastDueBalance="0.00",
            chargeCounterList=["Tax"],
            lastPaidDate="11/05/2024",
            lastPaymentAmount="100.00",
            statusCode="0000",
            content="Main content",
            statusMessage="SUCCESS"
            # Optional fields not provided (will be None)
        )
        
        # Note: callId, accountRole, and mdn are not fields in the response model
        # They only exist in the input/general session parameters model
        assert params.statusCode == "0000"
        assert params.outstandingBalance == "123.45"
        assert params.activeMtnCount == "4"


class TestGetbillinginfoResponseSessioninfo:
    """Test cases for GetbillinginfoResponseSessioninfo dataclass."""
    
    def test_response_session_info_creation(self):
        """Test creating a GetbillinginfoResponseSessioninfo instance."""
        params = GetbillinginfoResponseSessioninfoParameters(
            # Required fields
            outstandingBalance="123.45",
            additionalContent="Additional details",
            billduedate="12/05/2024",
            chargeCounter="3",
            activeMtnCount="4",
            autoPay="false",
            pastDueBalance="0.00",
            chargeCounterList=["Tax"],
            lastPaidDate="11/05/2024",
            lastPaymentAmount="100.00",
            statusCode="0000",
            content="Main content",
            statusMessage="SUCCESS"
            # Note: callId is not a field in the response model
        )
        session_info = GetbillinginfoResponseSessioninfo(
            parameters=params
        )
        
        assert session_info.parameters == params
    
    def test_response_session_info_requires_parameters(self):
        """Test GetbillinginfoResponseSessioninfo requires parameters field."""
        # Since parameters is now required, creating without it should fail
        with pytest.raises(Exception):  # ValidationError
            GetbillinginfoResponseSessioninfo()


class TestGetbillinginfoResponse:
    """Test cases for GetbillinginfoResponse dataclass."""
    
    def test_response_creation(self):
        """Test creating a GetbillinginfoResponse instance."""
        params = GetbillinginfoResponseSessioninfoParameters(
            # Required fields
            outstandingBalance="123.45",
            additionalContent="Additional details",
            billduedate="12/05/2024",
            chargeCounter="3",
            activeMtnCount="4",
            autoPay="false",
            pastDueBalance="0.00",
            chargeCounterList=["Tax"],
            lastPaidDate="11/05/2024",
            lastPaymentAmount="100.00",
            statusCode="0000",
            content="Main content",
            statusMessage="SUCCESS"
            # Note: callId is not a field in the response model
        )
        session_info = GetbillinginfoResponseSessioninfo(
            parameters=params
        )
        response = GetbillinginfoResponse(
            sessionInfo=session_info
        )
        
        assert response.sessionInfo == session_info
    
    def test_response_requires_session_info(self):
        """Test GetbillinginfoResponse requires sessionInfo field."""
        # Since sessionInfo is now required, creating without it should fail
        with pytest.raises(Exception):  # ValidationError
            GetbillinginfoResponse()


class TestSession:
    """Test cases for Session dataclass."""
    
    def test_session_creation(self):
        """Test creating a Session instance."""
        session_data = {
            "session1": {
                "params1": GetbillinginfoSessioninfoParameters(
                    callId="test_call_123",
                    statusCode="0000"
                )
            }
        }
        session = Session(id=session_data)
        
        assert session.id == session_data
        assert "session1" in session.id
        assert "params1" in session.id["session1"]
    
    def test_session_with_empty_dict(self):
        """Test Session with empty dictionary."""
        session = Session(id={})
        
        assert session.id == {}
        assert len(session.id) == 0


class TestModelIntegration:
    """Test integration between different model classes."""
    
    def test_full_response_creation(self):
        """Test creating a complete response using all model classes."""
        # Create parameters with all required fields
        params = GetbillinginfoResponseSessioninfoParameters(
            # Required fields
            outstandingBalance="123.45",
            additionalContent="Additional details",
            billduedate="12/05/2024",
            chargeCounter="3",
            activeMtnCount="4",
            autoPay="false",
            pastDueBalance="0.00",
            chargeCounterList=["Tax"],
            lastPaidDate="11/05/2024",
            lastPaymentAmount="100.00",
            statusCode="0000",
            content="Main content",
            statusMessage="SUCCESS"
            # Note: callId is not a field in the response model
        )
        
        # Create session info
        session_info = GetbillinginfoResponseSessioninfo(
            parameters=params
        )
        
        # Create response
        response = GetbillinginfoResponse(
            sessionInfo=session_info
        )
        
        # Verify the complete structure
        assert response.sessionInfo.parameters.statusCode == "0000"
        assert response.sessionInfo.parameters.statusMessage == "SUCCESS"
        assert response.sessionInfo.parameters.outstandingBalance == "123.45"
        assert response.sessionInfo.parameters.autoPay == "false"
    
    def test_fulfillment_info_integration(self):
        """Test GetbillinginfoFulfillmentinfo integration."""
        fulfillment = GetbillinginfoFulfillmentinfo(
            event={"type": "billing_update", "timestamp": "2024-01-01"},
            tag="billing.action.initviewbill"
        )
        
        assert fulfillment.event["type"] == "billing_update"
        assert fulfillment.event["timestamp"] == "2024-01-01"
        assert fulfillment.tag == "billing.action.initviewbill"


if __name__ == "__main__":
    pytest.main([__file__])