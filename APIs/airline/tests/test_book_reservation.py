"""
Test suite for book_reservation tool.
"""
import unittest
from pydantic import ValidationError
from .airline_base_exception import AirlineBaseTestCase
from .. import book_reservation
from ..SimulationEngine.custom_errors import UserNotFoundError, FlightNotFoundError, SeatsUnavailableError, PaymentMethodNotFoundError, InsufficientFundsError, ValidationError as CustomValidationError

from ..SimulationEngine.db import DB
class TestBookReservation(AirlineBaseTestCase):

    def test_book_reservation_success(self):
        """Test successful booking of a reservation."""
        flights = [{"flight_number": "HAT001", "date": "2024-05-16"}]
        passengers = [{"first_name": "Test", "last_name": "User", "dob": "1990-01-01"}]
        payment_methods = [{"payment_id": "credit_card_1955700", "amount": 87.0}]
        
        reservation = book_reservation(
            user_id="mia_li_3668",
            origin="PHL",
            destination="LGA",
            flight_type="one_way",
            cabin="basic_economy",
            flights=flights,
            passengers=passengers,
            payment_methods=payment_methods,
            total_baggages=0,
            nonfree_baggages=0,
            insurance="no"
        )
        self.assertIsInstance(reservation, dict)
        self.assertEqual(reservation["user_id"], "mia_li_3668")
        self.assertEqual(len(reservation["flights"]), 1)

    def test_book_reservation_user_not_found(self):
        """Test booking with a non-existent user ID."""
        self.assert_error_behavior(
            book_reservation,
            UserNotFoundError,
            "User with ID 'non_existent_user' not found.",
            None,
            user_id="non_existent_user",
            origin="PHL", destination="LGA", flight_type="one_way", cabin="economy",
            flights=[{"flight_number": "HAT001", "date": "2024-05-16"}],
            passengers=[{"first_name": "Test", "last_name": "User", "dob": "1990-01-01"}],
            payment_methods=[{"payment_id": "credit_card_12345", "amount": 122.0}],
            total_baggages=0, nonfree_baggages=0, insurance="no"
        )

    def test_book_reservation_flight_not_found(self):
        """Test booking with a non-existent flight number."""
        self.assert_error_behavior(
            book_reservation,
            FlightNotFoundError,
            "Flight 'INVALIDFLIGHT' not found.",
            None,
            user_id="mia_li_3668",
            origin="PHL", destination="LGA", flight_type="one_way", cabin="economy",
            flights=[{"flight_number": "INVALIDFLIGHT", "date": "2024-05-16"}],
            passengers=[{"first_name": "Test", "last_name": "User", "dob": "1990-01-01"}],
            payment_methods=[{"payment_id": "credit_card_1955700", "amount": 0.0}],
            total_baggages=0, nonfree_baggages=0, insurance="no"
        )

    def test_book_reservation_no_seats(self):
        """Test booking a flight with insufficient seats."""
        self.assert_error_behavior(
            book_reservation,
            SeatsUnavailableError,
            "Not enough seats on flight 'HAT020'.",
            None,
            user_id="mia_li_3668",
            origin="MCO", destination="LGA", flight_type="one_way", cabin="business",
            flights=[{"flight_number": "HAT020", "date": "2024-05-29"}],
            passengers=[
                {"first_name": "Chen", "last_name": "Jackson", "dob": "1956-07-07"},
                {"first_name": "Raj", "last_name": "Smith", "dob": "1967-04-01"},
                {"first_name": "Test", "last_name": "User", "dob": "1990-01-01"}
            ],
            payment_methods=[{"payment_id": "credit_card_1955700", "amount": 1281.0}],
            total_baggages=0, nonfree_baggages=0, insurance="no"
        )

    def test_book_reservation_payment_method_not_found(self):
        """Test booking with a non-existent payment method."""
        self.assert_error_behavior(
            book_reservation,
            PaymentMethodNotFoundError,
            "Payment method 'invalid_payment_id' not found.",
            None,
            user_id="mia_li_3668",
            origin="PHL", destination="LGA", flight_type="one_way", cabin="economy",
            flights=[{"flight_number": "HAT001", "date": "2024-05-16"}],
            passengers=[{"first_name": "Test", "last_name": "User", "dob": "1990-01-01"}],
            payment_methods=[{"payment_id": "invalid_payment_id", "amount": 122.0}],
            total_baggages=0, nonfree_baggages=0, insurance="no"
        )

    def test_book_reservation_insufficient_funds(self):
        """Test booking with a gift card that has insufficient funds."""
        user_id = "chen_jackson_3290"
        payment_id = "gift_card_3576581"
        
        users = DB.get("users")
        payment_method = users[user_id]["payment_methods"][payment_id]
        original_amount = payment_method["amount"]

        try:
            payment_method["amount"] = 100.0
            self.assert_error_behavior(
                book_reservation,
                InsufficientFundsError,
                f"Not enough balance in payment method '{payment_id}'.",
                None,
                user_id=user_id,
                origin="MCO", destination="LGA", flight_type="one_way", cabin="economy",
                flights=[{"flight_number": "HAT019", "date": "2024-05-16"}],
                passengers=[{"first_name": "Chen", "last_name": "Jackson", "dob": "1956-07-07"}],
                payment_methods=[{"payment_id": payment_id, "amount": 147.0}],
                total_baggages=0, nonfree_baggages=0, insurance="no"
            )
        finally:
            payment_method["amount"] = original_amount

    def test_book_reservation_invalid_passenger_data(self):
        """Test booking with invalid passenger data."""
        self.assert_error_behavior(
            book_reservation,
            ValidationError,
            "last_name",
            None,
            user_id="mia_li_3668",
            origin="PHL", destination="LGA", flight_type="one_way", cabin="economy",
            flights=[{"flight_number": "HAT001", "date": "2024-05-16"}],
            passengers=[{"first_name": "Test", "dob": "1990-01-01"}],
            payment_methods=[{"payment_id": "credit_card_1955700", "amount": 122.0}],
            total_baggages=0, nonfree_baggages=0, insurance="no"
        )

    def test_book_reservation_incorrect_payment_total(self):
        """Test booking when the payment amount does not match the total price."""
        self.assert_error_behavior(
            book_reservation,
            ValueError,
            "Payment amount does not add up, total price is 87, but paid 50.0.",
            None,
            user_id="mia_li_3668",
            origin="PHL", destination="LGA", flight_type="one_way", cabin="basic_economy",
            flights=[{"flight_number": "HAT001", "date": "2024-05-16"}],
            passengers=[{"first_name": "Test", "last_name": "User", "dob": "1990-01-01"}],
            payment_methods=[{"payment_id": "credit_card_1955700", "amount": 50.0}],
            total_baggages=0, nonfree_baggages=0, insurance="no"
        )

    def test_book_reservation_with_empty_flights_list(self):
        with self.assertRaisesRegex(
            CustomValidationError, "The 'flights' list cannot be empty."
        ):
            book_reservation(
                user_id="sara_doe_496",
                origin="JFK",
                destination="LAX",
                flight_type="one_way",
                cabin="economy",
                flights=[],
                passengers=[
                    {
                        "first_name": "John",
                        "last_name": "Doe",
                        "dob": "1990-01-01",
                    }
                ],
                payment_methods=[
                    {
                        "payment_id": "credit_card_4421486",
                        "amount": 250.0,
                    }
                ],
                total_baggages=2,
                nonfree_baggages=1,
                insurance="no",
            )

    def test_book_reservation_with_empty_passengers_list(self):
        with self.assertRaisesRegex(
            CustomValidationError, "The 'passengers' list cannot be empty."
        ):
            book_reservation(
                user_id="sara_doe_496",
                origin="JFK",
                destination="LAX",
                flight_type="one_way",
                cabin="economy",
                flights=[
                    {
                        "flight_number": "HAT001",
                        "date": "2024-05-15",
                    }
                ],
                passengers=[],
                payment_methods=[
                    {
                        "payment_id": "credit_card_4421486",
                        "amount": 250.0,
                    }
                ],
                total_baggages=2,
                nonfree_baggages=1,
                insurance="no",
            )

    def test_book_reservation_with_empty_payment_methods_list(self):
        with self.assertRaisesRegex(
            CustomValidationError, "The 'payment_methods' list cannot be empty."
        ):
            book_reservation(
                user_id="sara_doe_496",
                origin="JFK",
                destination="LAX",
                flight_type="one_way",
                cabin="economy",
                flights=[
                    {
                        "flight_number": "HAT001",
                        "date": "2024-05-15",
                    }
                ],
                passengers=[
                    {
                        "first_name": "John",
                        "last_name": "Doe",
                        "dob": "1990-01-01",
                    }
                ],
                payment_methods=[],
                total_baggages=2,
                nonfree_baggages=1,
                insurance="no",
            )


if __name__ == '__main__':
    unittest.main()
