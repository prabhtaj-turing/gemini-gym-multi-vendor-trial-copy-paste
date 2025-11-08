"""Tests for CES Billing Custom Errors module."""

import pytest
import sys
import os

# Add the parent directory to the path so we can import the modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ces_billing.SimulationEngine.custom_errors import (
    BillingServiceError,
    EmptyFieldError,
    MissingRequiredFieldError,
    InvalidMdnError,
    InvalidAccountRoleError,
    BillingDataError,
    PaymentProcessingError,
    AutoPayError,
    EscalationError,
    ValidationError,
    DatabaseError,
    AuthenticationError,
    AuthorizationError,
    ServiceUnavailableError,
    RateLimitError,
    BillingTimeoutError
)


class TestCustomErrors:
    """Test cases for custom exception classes."""
    
    def test_billing_service_error_inheritance(self):
        """Test BillingServiceError inherits from Exception."""
        error = BillingServiceError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
    
    def test_empty_field_error_inheritance(self):
        """Test EmptyFieldError inherits from BillingServiceError."""
        error = EmptyFieldError("Field is empty")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Field is empty"
    
    def test_missing_required_field_error_inheritance(self):
        """Test MissingRequiredFieldError inherits from BillingServiceError."""
        error = MissingRequiredFieldError("Required field missing")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Required field missing"
    
    def test_invalid_mdn_error_inheritance(self):
        """Test InvalidMdnError inherits from BillingServiceError."""
        error = InvalidMdnError("Invalid MDN format")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Invalid MDN format"
    
    def test_invalid_account_role_error_inheritance(self):
        """Test InvalidAccountRoleError inherits from BillingServiceError."""
        error = InvalidAccountRoleError("Invalid account role")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Invalid account role"
    
    def test_billing_data_error_inheritance(self):
        """Test BillingDataError inherits from BillingServiceError."""
        error = BillingDataError("Billing data corrupted")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Billing data corrupted"
    
    def test_payment_processing_error_inheritance(self):
        """Test PaymentProcessingError inherits from BillingServiceError."""
        error = PaymentProcessingError("Payment failed")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Payment failed"
    
    def test_autopay_error_inheritance(self):
        """Test AutoPayError inherits from BillingServiceError."""
        error = AutoPayError("AutoPay enrollment failed")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "AutoPay enrollment failed"
    
    def test_escalation_error_inheritance(self):
        """Test EscalationError inherits from BillingServiceError."""
        error = EscalationError("Escalation failed")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Escalation failed"
    
    def test_validation_error_inheritance(self):
        """Test ValidationError inherits from BillingServiceError."""
        error = ValidationError("Validation failed")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Validation failed"
    
    def test_database_error_inheritance(self):
        """Test DatabaseError inherits from BillingServiceError."""
        error = DatabaseError("Database connection failed")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Database connection failed"
    
    def test_authentication_error_inheritance(self):
        """Test AuthenticationError inherits from BillingServiceError."""
        error = AuthenticationError("Authentication failed")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Authentication failed"
    
    def test_authorization_error_inheritance(self):
        """Test AuthorizationError inherits from BillingServiceError."""
        error = AuthorizationError("Authorization failed")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Authorization failed"
    
    def test_service_unavailable_error_inheritance(self):
        """Test ServiceUnavailableError inherits from BillingServiceError."""
        error = ServiceUnavailableError("Service unavailable")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Service unavailable"
    
    def test_rate_limit_error_inheritance(self):
        """Test RateLimitError inherits from BillingServiceError."""
        error = RateLimitError("Rate limit exceeded")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Rate limit exceeded"
    
    def test_timeout_error_inheritance(self):
        """Test BillingTimeoutError inherits from BillingServiceError."""
        error = BillingTimeoutError("Operation timed out")
        assert isinstance(error, BillingServiceError)
        assert isinstance(error, Exception)
        assert str(error) == "Operation timed out"
    
    def test_exception_raising_and_catching(self):
        """Test that exceptions can be raised and caught properly."""
        with pytest.raises(EmptyFieldError):
            raise EmptyFieldError("Test empty field error")
        
        with pytest.raises(MissingRequiredFieldError):
            raise MissingRequiredFieldError("Test missing field error")
        
        with pytest.raises(InvalidMdnError):
            raise InvalidMdnError("Test invalid MDN error")
        
        with pytest.raises(InvalidAccountRoleError):
            raise InvalidAccountRoleError("Test invalid account role error")
        
        with pytest.raises(BillingDataError):
            raise BillingDataError("Test billing data error")
        
        with pytest.raises(PaymentProcessingError):
            raise PaymentProcessingError("Test payment processing error")
        
        with pytest.raises(AutoPayError):
            raise AutoPayError("Test AutoPay error")
        
        with pytest.raises(EscalationError):
            raise EscalationError("Test escalation error")
        
        with pytest.raises(ValidationError):
            raise ValidationError("Test validation error")
        
        with pytest.raises(DatabaseError):
            raise DatabaseError("Test database error")
        
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("Test authentication error")
        
        with pytest.raises(AuthorizationError):
            raise AuthorizationError("Test authorization error")
        
        with pytest.raises(ServiceUnavailableError):
            raise ServiceUnavailableError("Test service unavailable error")
        
        with pytest.raises(RateLimitError):
            raise RateLimitError("Test rate limit error")
        
        with pytest.raises(BillingTimeoutError):
            raise BillingTimeoutError("Test timeout error")
    
    def test_exception_catching_by_base_class(self):
        """Test that specific exceptions can be caught by their base class."""
        try:
            raise EmptyFieldError("Test error")
        except BillingServiceError as e:
            assert str(e) == "Test error"
        except Exception:
            pytest.fail("Should have been caught by BillingServiceError")
        
        try:
            raise InvalidMdnError("Test MDN error")
        except BillingServiceError as e:
            assert str(e) == "Test MDN error"
        except Exception:
            pytest.fail("Should have been caught by BillingServiceError")
    
    def test_exception_catching_by_exception_class(self):
        """Test that BillingServiceError can be caught by Exception."""
        try:
            raise BillingServiceError("Test base error")
        except Exception as e:
            assert str(e) == "Test base error"
        except:
            pytest.fail("Should have been caught by Exception")
    
    def test_exception_with_no_message(self):
        """Test exceptions can be created without a message."""
        error = BillingServiceError()
        assert str(error) == ""
        
        error = EmptyFieldError()
        assert str(error) == ""
    
    def test_exception_with_custom_message(self):
        """Test exceptions with custom messages."""
        custom_message = "This is a custom error message with details"
        error = BillingServiceError(custom_message)
        assert str(error) == custom_message
        
        error = ValidationError(custom_message)
        assert str(error) == custom_message


if __name__ == "__main__":
    pytest.main([__file__])
