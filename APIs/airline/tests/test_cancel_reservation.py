"""
Test suite for cancel_reservation tool.
"""
import unittest
from .airline_base_exception import AirlineBaseTestCase
from .. import cancel_reservation, get_reservation_details
from ..SimulationEngine.custom_errors import ReservationNotFoundError, ValidationError as CustomValidationError, ReservationAlreadyCancelledError

class TestCancelReservation(AirlineBaseTestCase):

    def test_cancel_reservation_success(self):
        """Test that a reservation can be successfully cancelled."""
        reservation_id = "4WQ150"
        
        initial_reservation = get_reservation_details(reservation_id)
        self.assertNotEqual(initial_reservation.get("status"), "cancelled")
        
        cancelled_reservation = cancel_reservation(reservation_id=reservation_id)
        
        self.assertIsInstance(cancelled_reservation, dict)
        self.assertEqual(cancelled_reservation["status"], "cancelled")
        
        final_reservation = get_reservation_details(reservation_id)
        self.assertEqual(final_reservation["status"], "cancelled")

    def test_cancel_reservation_not_found(self):
        """Test cancelling a non-existent reservation."""
        self.assert_error_behavior(
            cancel_reservation,
            ReservationNotFoundError,
            "Reservation with ID 'non_existent_reservation' not found.",
            None,
            reservation_id="non_existent_reservation"
        )

    def test_cancel_reservation_invalid_id(self):
        """Test cancelling with an invalid reservation ID format."""
        self.assert_error_behavior(
            cancel_reservation,
            CustomValidationError,
            "Reservation ID must be a non-empty string.",
            None,
            reservation_id=""
        )

    def test_cancel_reservation_refund_logic(self):
        """Test that cancelling a reservation correctly processes refunds."""
        reservation_id = "4WQ150"
        initial_reservation = get_reservation_details(reservation_id)
        initial_payment_count = len(initial_reservation.get("payment_history", []))
        
        expected_refunds = [
            {"payment_id": p["payment_id"], "amount": -p["amount"]} 
            for p in initial_reservation.get("payment_history", [])
        ]
        
        cancelled_reservation = cancel_reservation(reservation_id=reservation_id)
        
        final_payment_history = cancelled_reservation.get("payment_history", [])
        self.assertEqual(len(final_payment_history), initial_payment_count + len(expected_refunds))
        
        for refund in expected_refunds:
            self.assertIn(refund, final_payment_history)

    def test_cancel_reservation_already_cancelled(self):
        """Test that cancelling an already cancelled reservation raises an error."""
        reservation_id = "4WQ150"
        cancel_reservation(reservation_id=reservation_id)
        self.assert_error_behavior(
            cancel_reservation,
            ReservationAlreadyCancelledError,
            "Reservation with ID '4WQ150' is already cancelled.",
            None,
            reservation_id="4WQ150"
        )
if __name__ == '__main__':
    unittest.main()