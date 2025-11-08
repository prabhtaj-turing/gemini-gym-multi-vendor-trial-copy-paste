"""
Test suite for update_reservation_flights tool.
"""
import unittest
from pydantic import ValidationError
from .airline_base_exception import AirlineBaseTestCase
from .. import update_reservation_flights
from ..SimulationEngine.custom_errors import SeatsUnavailableError, FlightNotFoundError, ReservationNotFoundError, ValidationError as CustomValidationError

class TestUpdateReservationFlights(AirlineBaseTestCase):

    def test_update_reservation_flights_success(self):
        """Test a successful flight update for a reservation."""
        flights = [{"flight_number": "HAT001", "date": "2024-05-16"}]
        reservation = update_reservation_flights(
            reservation_id="VAAOXJ",
            cabin="economy",
            flights=flights,
            payment_id="credit_card_1052991"
        )
        self.assertIsInstance(reservation, dict)
        self.assertEqual(len(reservation["flights"]), 1)
        self.assertEqual(reservation["flights"][0]["flight_number"], "HAT001")

    def test_update_reservation_flights_no_seats(self):
        """Test updating to a flight with no available seats."""
        flights = [{"flight_number": "HAT002", "date": "2024-05-25"}] # This flight has 0 business seats
        self.assert_error_behavior(
            update_reservation_flights,
            SeatsUnavailableError,
            "Not enough seats on flight 'HAT002'.",
            None,
            reservation_id="4WQ150",  # This reservation has 3 passengers
            cabin="business",
            flights=flights,
            payment_id="gift_card_3576581"
        )

    def test_update_reservation_flights_flight_not_found(self):
        """Test updating to a non-existent flight."""
        flights = [{"flight_number": "INVALIDFLIGHT", "date": "2024-05-16"}]
        self.assert_error_behavior(
            update_reservation_flights,
            FlightNotFoundError,
            "Flight 'INVALIDFLIGHT' not found.",
            None,
            reservation_id="VAAOXJ",
            cabin="economy",
            flights=flights,
            payment_id="credit_card_1052991"
        )
        
    def test_update_reservation_flights_reservation_not_found(self):
        """Test updating a non-existent reservation."""
        flights = [{"flight_number": "HAT001", "date": "2024-05-16"}]
        self.assert_error_behavior(
            update_reservation_flights,
            ReservationNotFoundError,
            "Reservation with ID 'invalid_id' not found.",
            None,
            reservation_id="invalid_id",
            cabin="economy",
            flights=flights,
            payment_id="credit_card_1052991"
        )

    def test_update_reservation_flights_invalid_flight_data(self):
        """Test updating with invalid flight data format."""
        flights = [{"flight_number": "HAT001"}] # Missing 'date'
        self.assert_error_behavior(
            update_reservation_flights,
            ValidationError,
            "date", 
            None,
            reservation_id="VAAOXJ",
            cabin="economy",
            flights=flights,
            payment_id="credit_card_1052991"
        )

    def test_update_reservation_flights_invalid_cabin(self):
        """Test updating with an empty cabin string."""
        flights = [{"flight_number": "HAT001", "date": "2024-05-16"}]
        self.assert_error_behavior(
            update_reservation_flights,
            CustomValidationError,
            "Cabin must be a non-empty string.",
            None,
            reservation_id="VAAOXJ",
            cabin="",
            flights=flights,
            payment_id="credit_card_1052991"
        )

    def test_invalid_reservation_id(self):
        """Test updating with an invalid reservation ID."""
        flights = [{"flight_number": "HAT001", "date": "2024-05-16"}]
        self.assert_error_behavior(
            update_reservation_flights,
            CustomValidationError,
            "Reservation ID must be a non-empty string.",
            None,
            reservation_id="",
            cabin="economy",
            flights=flights,
            payment_id="credit_card_1052991"
        )

    def test_update_reservation_flights_invalid_date(self):
        """Test updating with an invalid date."""
        flights = [{"flight_number": "HAT001", "date": "2024-05-32"}]
        self.assert_error_behavior(
            update_reservation_flights,
            CustomValidationError,
            "Invalid date format or non-existent date: '2024-05-32'. Expected format: YYYY-MM-DD.",
            None,
            reservation_id="VAAOXJ",
            cabin="economy",
            flights=flights,
            payment_id="credit_card_1052991"
        )

    def test_update_reservation_flights_invalid_payment_id(self):
        """Test updating with an invalid payment ID."""
        flights = [{"flight_number": "HAT001", "date": "2024-05-16"}]
        self.assert_error_behavior(
            update_reservation_flights,
            CustomValidationError,
            "Payment ID must be a non-empty string.",
            None,
            reservation_id="VAAOXJ",
            cabin="economy",
            flights=flights,
            payment_id=" ",
        )
    
    def test_update_reservation_flights_invalid_reservation_id(self):
        """Test updating with an invalid reservation ID."""
        flights = [{"flight_number": "HAT001", "date": "2024-05-16"}]
        self.assert_error_behavior(
            update_reservation_flights,
            CustomValidationError,
            "Reservation ID must be a non-empty string.",
            None,
            reservation_id=" ",
            cabin="economy",
            flights=flights,
            payment_id="credit_card_1052991"
        )

    def test_update_reservation_flights_invalid_cabin(self):
        """Test updating with an invalid cabin."""
        flights = [{"flight_number": "HAT001", "date": "2024-05-16"}]
        self.assert_error_behavior(
            update_reservation_flights,
            CustomValidationError,
            "Cabin must be one of basic_economy, economy, business.",
            None,
            reservation_id="VAAOXJ",
            cabin="invalid_cabin",
            flights=flights,
            payment_id="credit_card_1052991"
        )
    

if __name__ == '__main__':
    unittest.main()