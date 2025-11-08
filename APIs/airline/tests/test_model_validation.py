import unittest
from pydantic import ValidationError
from .airline_base_exception import AirlineBaseTestCase
from ..SimulationEngine.models import AirlineDB, Reservation, Flight, User 
from ..SimulationEngine.models import FlightDateDetails, PaymentMethodInReservation, FlightInReservation, PaymentMethod, SeatInfo, Membership
from ..SimulationEngine.db import DB
from ..SimulationEngine.models import FlightType, CabinType, Passenger, FlightDateDetails, FlightStatus


class TestModelValidation(AirlineBaseTestCase):
    """
    Test suite for validating the Pydantic models.
    """

    def setUp(self):
        super().setUp()

        self.valid_seat_info_dict = {
            "basic_economy": 100,
            "economy": 100,
            "business": 100,
        }

        self.valid_flight_date_details_dict = {
            "status": 'landed',
            "actual_departure_time_est": "2021-01-01",
            "actual_arrival_time_est": "2021-01-01",
            "estimated_departure_time_est": "2021-01-01",
            "estimated_arrival_time_est": "2021-01-01",
            "available_seats": self.valid_seat_info_dict,
            "prices": self.valid_seat_info_dict,
        }

        self.valid_flight_dict = {
            "flight_number": "123",
            "origin": "PHL",
            "destination": "LGA",
            "scheduled_departure_time_est": "2021-01-01",
            "scheduled_arrival_time_est": "2021-01-01",
            "dates": {
                "2021-01-01": self.valid_flight_date_details_dict,
            },
        }

        self.valid_passenger_dict = {
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1990-01-01",
        }

        self.valid_payment_method_dict = {
            "source": "credit_card",
            "brand": "Visa",
            "last_four": "1234",
            "id": "123",
            "amount": 100,
        }

        self.valid_flight_in_reservation_dict = {
            "origin": "PHL",
            "destination": "LGA",
            "flight_number": "123",
            "date": "2021-01-01",
            "price": 100,
        }

        self.valid_payment_method_in_reservation_dict = {
            "payment_id": "123",
            "amount": 100,
        }

        self.valid_reservation_dict = {
            "reservation_id": "123",
            "user_id": "456",
            "origin": "PHL",
            "destination": "LGA",
            "flight_type": 'one_way',
            "cabin": 'basic_economy',
            "flights": [self.valid_flight_in_reservation_dict],
            "passengers": [self.valid_passenger_dict],
            "payment_history": [self.valid_payment_method_in_reservation_dict],
            "created_at": "2021-01-01",
            "total_baggages": 0,
            "nonfree_baggages": 0,
            "insurance": "no",
            "status": "pending",
        }

        self.valid_user_dict = {
            "name": {
                "first_name": "John",
                "last_name": "Doe",
            },
            "address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "USA",
                "zip": "12345",
            },
            "email": "john.doe@example.com",
            "dob": "1990-01-01",
            "payment_methods": {
                "credit_card": self.valid_payment_method_dict,
            },
            "saved_passengers": [self.valid_passenger_dict],
            "membership": 'gold',
            "reservations": [],
        }

        self.valid_airline_db_dict = {
            "flights": {
                "123": self.valid_flight_dict,
            },
            "reservations": {
                "123": self.valid_reservation_dict,
            },
            "users": {
                "456": self.valid_user_dict,
            },
        }

    def test_valid_user_creation(self):
        """
        Test that the Pydantic models are valid.
        """
        user = User(**self.valid_user_dict)
        self.assertEqual(user.name["first_name"], "John")
        self.assertEqual(user.name["last_name"], "Doe")
        self.assertEqual(user.address["street"], "123 Main St")
        self.assertEqual(user.address["city"], "Anytown")
        self.assertEqual(user.address["state"], "USA")
        self.assertEqual(user.address["zip"], "12345")
        self.assertEqual(user.email, "john.doe@example.com")
        self.assertEqual(user.dob, "1990-01-01")
        self.assertEqual(user.payment_methods["credit_card"].source, "credit_card")
        self.assertEqual(user.payment_methods["credit_card"].brand, "Visa")
        self.assertEqual(user.payment_methods["credit_card"].last_four, "1234")
        self.assertEqual(user.payment_methods["credit_card"].id, "123")
        self.assertEqual(user.payment_methods["credit_card"].amount, 100)
        self.assertEqual(user.saved_passengers[0].first_name, "John")
        self.assertEqual(user.saved_passengers[0].last_name, "Doe")
        self.assertEqual(user.saved_passengers[0].dob, "1990-01-01")
        self.assertEqual(user.membership, 'gold')
        self.assertEqual(user.reservations, [])

    def test_invalid_user_creation(self):
        """
        Test that the Pydantic models are invalid.
        """
        self.valid_user_dict['name'] = "hirenpatel"
        with self.assertRaises(ValidationError):
            User(**self.valid_user_dict)

    def test_valid_reservation_creation(self):
        """
        Test that the Pydantic models are valid.
        """
        reservation = Reservation(**self.valid_reservation_dict)
        self.assertEqual(reservation.reservation_id, "123")
        self.assertEqual(reservation.user_id, "456")
        self.assertEqual(reservation.origin, "PHL")
        self.assertEqual(reservation.destination, "LGA")
        self.assertEqual(reservation.flight_type, 'one_way')
        self.assertEqual(reservation.cabin, 'basic_economy')
        self.assertEqual(reservation.flights, [FlightInReservation(**self.valid_flight_in_reservation_dict)])
        self.assertEqual(reservation.passengers, [Passenger(**self.valid_passenger_dict)])
        self.assertEqual(reservation.payment_history, [PaymentMethodInReservation(**self.valid_payment_method_in_reservation_dict)])
        self.assertEqual(reservation.created_at, "2021-01-01")
        self.assertEqual(reservation.total_baggages, 0)
        self.assertEqual(reservation.nonfree_baggages, 0)
        self.assertEqual(reservation.insurance, "no")
        self.assertEqual(reservation.status, "pending")


    def test_invalid_reservation_creation(self):
        """
        Test that the Pydantic models are invalid.
        """
        valid_reservation_dict_copy = self.valid_reservation_dict.copy()
        valid_reservation_dict_copy['reservation_id'] = 123
        with self.assertRaises(ValidationError):
            Reservation(**valid_reservation_dict_copy)

    def test_valid_flight_creation(self):
        """
        Test that the Pydantic models are valid.
        """
        flight = Flight(**self.valid_flight_dict)

        self.assertEqual(flight.flight_number, "123")
        self.assertEqual(flight.origin, "PHL")
        self.assertEqual(flight.destination, "LGA")
        self.assertEqual(flight.scheduled_departure_time_est, "2021-01-01")
        self.assertEqual(flight.scheduled_arrival_time_est, "2021-01-01")
        self.assertEqual(flight.dates, {
            "2021-01-01": FlightDateDetails(
                status='landed',
                actual_departure_time_est="2021-01-01",
                actual_arrival_time_est="2021-01-01",
                estimated_departure_time_est="2021-01-01",
                estimated_arrival_time_est="2021-01-01",
                available_seats=SeatInfo(
                    basic_economy=100,
                    economy=100,
                    business=100
                ),
                prices=SeatInfo(
                    basic_economy=100,
                    economy=100,
                    business=100
                ),
            )
        })

        self.assertEqual(flight.flight_number, "123")
        self.assertEqual(flight.origin, "PHL")
        self.assertEqual(flight.destination, "LGA")
        self.assertEqual(flight.scheduled_departure_time_est, "2021-01-01")
        self.assertEqual(flight.scheduled_arrival_time_est, "2021-01-01")


        self.assertEqual(flight.dates["2021-01-01"].status, 'landed')
        self.assertEqual(flight.dates["2021-01-01"].actual_departure_time_est, "2021-01-01")
        self.assertEqual(flight.dates["2021-01-01"].actual_arrival_time_est, "2021-01-01")
        self.assertEqual(flight.dates["2021-01-01"].estimated_departure_time_est, "2021-01-01")
        self.assertEqual(flight.dates["2021-01-01"].estimated_arrival_time_est, "2021-01-01")
        self.assertEqual(flight.dates["2021-01-01"].available_seats, SeatInfo(
            basic_economy=100,
            economy=100,
            business=100
        ))

        self.assertEqual(flight.dates["2021-01-01"].prices, SeatInfo(
            basic_economy=100,
            economy=100,
            business=100
        ))      

    def test_user_model_json_serialization(self):
        """
        Test that the Pydantic models are valid.
        """
        user = User(**self.valid_user_dict)
        user_json = user.model_dump(mode="json")
        self.assertEqual(user_json, self.valid_user_dict)

    def test_reservation_model_json_serialization(self):
        """
        Test that the Pydantic models are valid.
        """
        reservation = Reservation(**self.valid_reservation_dict)
        reservation_json = reservation.model_dump(mode="json")
        self.assertEqual(reservation_json, self.valid_reservation_dict)


    def test_flight_model_json_serialization(self):
        """
        Test that the Pydantic models are valid.
        """
        flight = Flight(**self.valid_flight_dict)
        flight_json = flight.model_dump(mode="json")
        self.assertEqual(flight_json, self.valid_flight_dict)


if __name__ == '__main__':
    unittest.main()