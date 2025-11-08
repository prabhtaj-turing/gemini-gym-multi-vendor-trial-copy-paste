from pydantic import ValidationError
"""
Test cases for the custom error classes in the CES Loyalty Auth API.

This module ensures that all custom exceptions defined in the API are
instantiated correctly and behave as expected.
"""

import unittest
from APIs.ces_loyalty_auth.SimulationEngine.custom_errors import (
    InvalidRequestError,
    AuthenticationFailedError,
    InvalidSessionError,
    OfferEnrollmentError,
    CustomerNotEligibleError,
    NotFoundError)
from .loyalty_auth_base_exception import LoyaltyAuthBaseTestCase


class TestCustomErrors(LoyaltyAuthBaseTestCase):
    """
    Test suite for the custom error classes in the CES Loyalty Auth API.
    """

    def test_invalid_request_error(self):
        """
        Tests that InvalidRequestError can be raised and caught correctly.
        """
        with self.assertRaises(InvalidRequestError):
            raise InvalidRequestError("Invalid request")

    def test_authentication_failed_error(self):
        """
        Tests that AuthenticationFailedError can be raised and caught correctly.
        """
        with self.assertRaises(AuthenticationFailedError):
            raise AuthenticationFailedError("Authentication failed")

    def test_invalid_session_error(self):
        """
        Tests that InvalidSessionError can be raised and caught correctly.
        """
        with self.assertRaises(InvalidSessionError):
            raise InvalidSessionError("Invalid session")

    def test_offer_enrollment_error(self):
        """
        Tests that OfferEnrollmentError can be raised and caught correctly.
        """
        with self.assertRaises(OfferEnrollmentError):
            raise OfferEnrollmentError("Offer enrollment failed")

    def test_customer_not_eligible_error(self):
        """
        Tests that CustomerNotEligibleError can be raised and caught correctly.
        """
        with self.assertRaises(CustomerNotEligibleError):
            raise CustomerNotEligibleError("Customer not eligible")

    def test_not_found_error(self):
        """
        Tests that NotFoundError can be raised and caught correctly.
        """
        with self.assertRaises(NotFoundError):
            raise NotFoundError("Resource not found")

    def test_validation_error(self):
        """
        Tests that ValidationError can be raised and caught correctly.
        """
        from pydantic import BaseModel
        with self.assertRaises(ValidationError):
            # Create a simple ValidationError using the constructor
            class TestModel(BaseModel):
                field: int
            # This will raise a ValidationError
            TestModel(field="not_an_int")


if __name__ == "__main__":
    unittest.main()
