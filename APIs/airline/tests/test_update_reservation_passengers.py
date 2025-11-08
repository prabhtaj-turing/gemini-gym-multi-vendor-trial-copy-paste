"""
Test suite for update_reservation_passengers tool.
"""
import unittest
from pydantic import ValidationError
from .airline_base_exception import AirlineBaseTestCase
from .. import update_reservation_passengers
from ..SimulationEngine.custom_errors import ReservationNotFoundError, MismatchedPassengerCountError, ValidationError as CustomValidationError

class TestUpdateReservationPassengers(AirlineBaseTestCase):

    def test_update_reservation_passengers_success(self):
        """Test a successful passenger update."""
        passengers = [
            { "first_name": "Chen", "last_name": "Jackson", "dob": "1956-07-07" },
            { "first_name": "Raj", "last_name": "Smith", "dob": "1967-04-01" },
            { "first_name": "Fatima", "last_name": "Martin", "dob": "1970-01-20" }
        ]
        reservation = update_reservation_passengers(reservation_id="4WQ150", passengers=passengers)
        self.assertIsInstance(reservation, dict)
        self.assertEqual(len(reservation["passengers"]), 3)
        self.assertEqual(reservation["passengers"][1]["first_name"], "Raj")

    def test_update_reservation_passengers_reservation_not_found(self):
        """Test updating a non-existent reservation."""
        self.assert_error_behavior(
            update_reservation_passengers,
            ReservationNotFoundError,
            "Reservation with ID 'non_existent_reservation' not found.",
            None,
            reservation_id="non_existent_reservation",
            passengers=[]
        )

    def test_update_reservation_passengers_mismatched_count(self):
        """Test updating with a mismatched number of passengers."""
        self.assert_error_behavior(
            update_reservation_passengers,
            MismatchedPassengerCountError,
            "Number of passengers does not match.",
            None,
            reservation_id="4WQ150", # This reservation has 3 passengers
            passengers=[{ "first_name": "Test", "last_name": "User", "dob": "1990-01-01" }] # Only one
        )

    def test_update_reservation_passengers_invalid_passenger_data(self):
        """Test updating with invalid passenger data."""
        passengers = [{"first_name": "Test", "last_name": "User"}] # Missing 'dob'
        self.assert_error_behavior(
            update_reservation_passengers,
            ValidationError,
            "dob", 
            None,
            reservation_id="4WQ150",
            passengers=passengers
        )
        
    def test_update_reservation_passengers_empty_list(self):
        """Test updating with an empty list of passengers against a non-empty reservation."""
        self.assert_error_behavior(
            update_reservation_passengers,
            MismatchedPassengerCountError,
            "Number of passengers does not match.",
            None,
            reservation_id="4WQ150", # This reservation has 3 passengers
            passengers=[]
        )

    def test_update_reservation_passengers_invalid_id(self):
        """Test updating with an empty reservation ID."""
        self.assert_error_behavior(
            update_reservation_passengers,
            CustomValidationError,
            "Reservation ID must be a non-empty string.",
            None,
            reservation_id="",
            passengers=[]
        )

if __name__ == '__main__':
    unittest.main()