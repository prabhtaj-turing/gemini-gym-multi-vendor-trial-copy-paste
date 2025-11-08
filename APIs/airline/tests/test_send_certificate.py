"""
Test suite for send_certificate tool.
"""
import unittest
from .airline_base_exception import AirlineBaseTestCase
from .. import send_certificate
from ..SimulationEngine.db import DB
from ..SimulationEngine.custom_errors import UserNotFoundError, ValidationError as CustomValidationError

class TestSendCertificate(AirlineBaseTestCase):

    def test_send_certificate_success(self):
        """Test sending a certificate successfully."""
        user_id = "mia_li_3668"
        initial_payment_methods_count = len(DB["users"][user_id]["payment_methods"])
        
        result = send_certificate(user_id=user_id, amount=100)
        
        self.assertIn("Certificate", result)
        self.assertIn(f"added to user {user_id} with amount 100", result)
        
        final_payment_methods_count = len(DB["users"][user_id]["payment_methods"])
        self.assertEqual(final_payment_methods_count, initial_payment_methods_count + 1)

    def test_send_certificate_user_not_found(self):
        """Test sending a certificate to a non-existent user."""
        self.assert_error_behavior(
            send_certificate,
            UserNotFoundError,
            "User with ID 'non_existent_user' not found.",
            None,
            user_id="non_existent_user",
            amount=100
        )

    def test_send_certificate_invalid_user_id(self):
        """Test sending a certificate with an empty user ID."""
        self.assert_error_behavior(
            send_certificate,
            CustomValidationError,
            "User ID must be a non-empty string.",
            None,
            user_id="",
            amount=100
        )

    def test_send_certificate_zero_amount(self):
        """Test sending a certificate with zero amount."""
        self.assert_error_behavior(
            send_certificate,
            CustomValidationError,
            "Amount must be a positive integer.",
            None,
            user_id="mia_li_3668",
            amount=0
        )

    def test_send_certificate_negative_amount(self):
        """Test sending a certificate with a negative amount."""
        self.assert_error_behavior(
            send_certificate,
            CustomValidationError,
            "Amount must be a positive integer.",
            None,
            user_id="mia_li_3668",
            amount=-50
        )

if __name__ == '__main__':
    unittest.main()