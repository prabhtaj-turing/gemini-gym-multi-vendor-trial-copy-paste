import unittest
from ..SimulationEngine.utils import _validate_endpoint_value
from common_utils.base_case import BaseTestCaseWithErrorHandler as BaseCase


class TestUtilsFunctions(BaseCase):
    """Test utility functions in SimulationEngine/utils.py."""

    def test_validate_endpoint_value_phone_valid(self):
        """Test _validate_endpoint_value with valid phone number."""
        result = _validate_endpoint_value("PHONE_NUMBER", "+14155552671")
        self.assertTrue(result)

    def test_validate_endpoint_value_phone_invalid_no_plus(self):
        """Test _validate_endpoint_value with phone number missing + prefix."""
        result = _validate_endpoint_value("PHONE_NUMBER", "14155552671")
        self.assertFalse(result)

    def test_validate_endpoint_value_phone_too_short(self):
        """Test _validate_endpoint_value with phone number too short."""
        result = _validate_endpoint_value("PHONE_NUMBER", "+123")
        self.assertFalse(result)

    def test_validate_endpoint_value_whatsapp_valid(self):
        """Test _validate_endpoint_value with valid WhatsApp JID."""
        result = _validate_endpoint_value("WHATSAPP_PROFILE", "14155552671@s.whatsapp.net")
        self.assertTrue(result)

    def test_validate_endpoint_value_whatsapp_invalid(self):
        """Test _validate_endpoint_value with invalid WhatsApp format."""
        result = _validate_endpoint_value("WHATSAPP_PROFILE", "14155552671")
        self.assertFalse(result)

    def test_validate_endpoint_value_empty_string(self):
        """Test _validate_endpoint_value with empty string."""
        result = _validate_endpoint_value("PHONE_NUMBER", "")
        self.assertFalse(result)

    def test_validate_endpoint_value_whitespace(self):
        """Test _validate_endpoint_value with whitespace."""
        result = _validate_endpoint_value("PHONE_NUMBER", "   ")
        self.assertFalse(result)

    def test_validate_endpoint_value_non_string(self):
        """Test _validate_endpoint_value with non-string value."""
        result = _validate_endpoint_value("PHONE_NUMBER", 123)
        self.assertFalse(result)

    def test_validate_endpoint_value_unknown_type(self):
        """Test _validate_endpoint_value with unknown endpoint type."""
        result = _validate_endpoint_value("UNKNOWN_TYPE", "+14155552671")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()

