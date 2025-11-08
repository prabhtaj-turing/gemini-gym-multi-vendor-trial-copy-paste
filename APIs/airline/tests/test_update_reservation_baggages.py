"""
Test suite for update_reservation_baggages tool.
"""
import unittest
from .airline_base_exception import AirlineBaseTestCase
from .. import update_reservation_baggages
from ..SimulationEngine.custom_errors import PaymentMethodNotFoundError, ReservationNotFoundError, CertificateUpdateError, InsufficientFundsError, ValidationError as CustomValidationError

class TestUpdateReservationBaggages(AirlineBaseTestCase):

    def test_update_reservation_baggages_success(self):
        """Test a successful baggage update."""
        reservation_id = "NO6JO3"
        payment_id = "credit_card_4421486"
        
        reservation = update_reservation_baggages(
            reservation_id=reservation_id,
            total_baggages=6,
            nonfree_baggages=1,
            payment_id=payment_id
        )
        self.assertIsInstance(reservation, dict)
        self.assertEqual(reservation["total_baggages"], 6)
        self.assertEqual(reservation["nonfree_baggages"], 1)

    def test_update_reservation_baggages_payment_not_found(self):
        """Test updating with a non-existent payment method."""
        self.assert_error_behavior(
            update_reservation_baggages,
            PaymentMethodNotFoundError,
            "Payment method 'non_existent_payment' not found.",
            None,
            reservation_id="4WQ150",
            total_baggages=6,
            nonfree_baggages=1,
            payment_id="non_existent_payment"
        )

    def test_update_reservation_baggages_reservation_not_found(self):
        """Test updating a non-existent reservation."""
        self.assert_error_behavior(
            update_reservation_baggages,
            ReservationNotFoundError,
            "Reservation with ID 'invalid_id' not found.",
            None,
            reservation_id="invalid_id",
            total_baggages=6,
            nonfree_baggages=1,
            payment_id="credit_card_4421486"
        )

    def test_update_reservation_baggages_negative_total(self):
        """Test updating with a negative total baggage count."""
        self.assert_error_behavior(
            update_reservation_baggages,
            CustomValidationError,
            "Total baggages must be a non-negative integer.",
            None,
            reservation_id="NO6JO3",
            total_baggages=-1,
            nonfree_baggages=1,
            payment_id="credit_card_4421486"
        )

    def test_update_reservation_baggages_negative_nonfree(self):
        """Test updating with a negative non-free baggage count."""
        self.assert_error_behavior(
            update_reservation_baggages,
            CustomValidationError,
            "Non-free baggages must be a non-negative integer.",
            None,
            reservation_id="NO6JO3",
            total_baggages=6,
            nonfree_baggages=-1,
            payment_id="credit_card_4421486"
        )

    def test_update_reservation_baggages_with_certificate(self):
        """Test that using a certificate for payment raises an error."""
        self.assert_error_behavior(
            update_reservation_baggages,
            CertificateUpdateError,
            "Certificate cannot be used to update reservation.",
            None,
            reservation_id="VAAOXJ",
            total_baggages=2,
            nonfree_baggages=1,
            payment_id="certificate_991631"
        )

    def test_update_reservation_baggages_insufficient_funds(self):
        """Test updating with a gift card that has insufficient funds."""
        self.assert_error_behavior(
            update_reservation_baggages,
            InsufficientFundsError,
            "Gift card balance is not enough.",
            None,
            reservation_id="4WQ150",
            total_baggages=10,
            nonfree_baggages=10, # This will incur a high cost
            payment_id="gift_card_3576581" # This card has a low balance
        )

    def test_invalid_reservation_id(self):
        """Test updating with an invalid reservation ID."""
        self.assert_error_behavior(
            update_reservation_baggages,
            CustomValidationError,
            "Reservation ID must be a non-empty string.",
            None,
            reservation_id="",
            total_baggages=6,
            nonfree_baggages=1,
            payment_id="credit_card_4421486"
        )

    def test_invalid_payment_id(self):
        """Test updating with an invalid payment ID."""
        self.assert_error_behavior(
            update_reservation_baggages,
            CustomValidationError,
            "Payment ID must be a non-empty string.",
            None,
            reservation_id="NO6JO3",
            total_baggages=6,
            nonfree_baggages=1,
            payment_id=""
        )
    
    def test_update_reservation_baggages_nonfree_greater_than_total(self):
        """Test updating with a non-free baggage count greater than the total baggage count."""
        self.assert_error_behavior(
            update_reservation_baggages,
            CustomValidationError,
            "Non-free baggages must be less than or equal to total baggages.",
            None,
            reservation_id="NO6JO3",
            total_baggages=6,
            nonfree_baggages=10,
            payment_id="credit_card_4421486"
        )
    

if __name__ == '__main__':
    unittest.main()
