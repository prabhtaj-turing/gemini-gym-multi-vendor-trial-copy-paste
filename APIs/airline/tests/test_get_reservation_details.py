"""
Test suite for get_reservation_details tool.
"""
import unittest
from .airline_base_exception import AirlineBaseTestCase
from .. import get_reservation_details
from ..SimulationEngine.custom_errors import ReservationNotFoundError, ValidationError as CustomValidationError

class TestGetReservationDetails(AirlineBaseTestCase):

    def test_get_reservation_details_success(self):
        """Test that get_reservation_details returns the correct data for an existing reservation."""
        reservation = get_reservation_details(reservation_id="4WQ150")
        self.assertIsInstance(reservation, dict)
        self.assertEqual(reservation["user_id"], "chen_jackson_3290")
        self.assertEqual(reservation["reservation_id"], "4WQ150")

    def test_get_reservation_details_not_found(self):
        """Test get_reservation_details for a non-existent reservation."""
        self.assert_error_behavior(
            get_reservation_details,
            ReservationNotFoundError,
            "Reservation with ID 'non_existent_reservation' not found.",
            None,
            reservation_id="non_existent_reservation"
        )

    def test_get_reservation_details_invalid_id(self):
        """Test get_reservation_details with an empty reservation ID."""
        self.assert_error_behavior(
            get_reservation_details,
            CustomValidationError,
            "Reservation ID must be a non-empty string.",
            None,
            reservation_id=""
        )

    def test_get_reservation_details_invalid_id_empty_string(self):
        """Test get_reservation_details with an empty reservation ID."""
        self.assert_error_behavior(
            get_reservation_details,
            CustomValidationError,
            "Reservation ID must be a non-empty string.",
            None,
            reservation_id="  "
        )

if __name__ == '__main__':
    unittest.main()