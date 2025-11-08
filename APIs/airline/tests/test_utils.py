import unittest
from .airline_base_exception import AirlineBaseTestCase
from ..SimulationEngine.utils import (
    create_user,
    add_flight,
    add_payment_method_to_user,
    get_user,
    get_flight,
    get_reservation,
    search_flights,
    search_onestop_flights
)
from ..SimulationEngine.custom_errors import InvalidDateTimeFormatError

class TestUtils(AirlineBaseTestCase):
    def test_create_user_success(self):
        """Test that a user can be created successfully."""
        address = {"address1": "123 Main St", "city": "Anytown", "state": "CA", "zip": "12345"}
        user = create_user(
            "new_user", "Test", "User", "test@example.com", "1990-01-01", address=address
        )
        self.assertIsNotNone(user)
        self.assertEqual(user["user_id"], "new_user")
        self.assertEqual(user["name"]["first_name"], "Test")
        retrieved_user = get_user("new_user")
        self.assertEqual(retrieved_user["address"]["city"], "Anytown")

    def test_create_user_duplicate_id(self):
        """Test that creating a user with a duplicate ID raises a ValueError."""
        create_user(
            "test_user", "Test", "User", "test@example.com", "1990-01-01"
        )
        self.assert_error_behavior(
            create_user,
            ValueError,
            "User with ID 'test_user' already exists.",
            None,
            "test_user", "Another", "User", "another@example.com", "1991-02-03"
        )
    
    def test_create_user_invalid_dob(self):
        """Test that creating a user with an invalid date of birth raises a ValueError."""
        self.assert_error_behavior(
            create_user,
            InvalidDateTimeFormatError,
            "Invalid user date of birth format: Invalid Airline date format: invalid. Expected YYYY-MM-DD format.",
            None,
            "test_user", "Test", "User", "test@example.com", "invalid", "gold"
        )


    def test_add_flight_success(self):
        """Test that a flight can be added successfully."""
        flight_details = {
            "2024-09-15": {
                "status": "available",
                "prices": {"economy": 350, "business": 950},
                "available_seats": {"economy": 100, "business": 40}
            }
        }
        flight = add_flight("UA999", "MIA", "BOS", "10:00", "13:00", flight_details)
        self.assertIsNotNone(flight)
        retrieved_flight = get_flight("UA999")
        self.assertEqual(retrieved_flight["origin"], "MIA")

    def test_add_flight_duplicate_number(self):
        """Test that adding a flight with a duplicate number raises a ValueError."""
        add_flight("UA101", "JFK", "LAX", "08:00", "11:00", {})
        self.assert_error_behavior(
            add_flight,
            ValueError,
            "Flight with number 'UA101' already exists.",
            None,
            "UA101", "SFO", "ORD", "10:00", "14:00", {}
        )

    def test_add_payment_method_credit_card(self):
        """Test adding a credit card to a user."""
        create_user("test_user", "Test", "User", "test@example.com", "1990-01-01")
        details = {"brand": "Mastercard", "last_four": "5678"}
        user = add_payment_method_to_user("test_user", "cc_new", "credit_card", details)
        
        payment_method = user["payment_methods"]["cc_new"]
        self.assertEqual(payment_method["source"], "credit_card")
        self.assertEqual(payment_method["brand"], "Mastercard")

    def test_add_payment_method_gift_card(self):
        """Test adding a gift card to a user."""
        create_user("test_user", "Test", "User", "test@example.com", "1990-01-01")
        details = {"amount": 250}
        user = add_payment_method_to_user("test_user", "gc_new", "gift_card", details)

        payment_method = user["payment_methods"]["gc_new"]
        self.assertEqual(payment_method["source"], "gift_card")
        self.assertEqual(payment_method["amount"], 250)

    def test_add_payment_method_to_nonexistent_user(self):
        """Test that adding a payment method to a non-existent user raises a ValueError."""
        self.assert_error_behavior(
            add_payment_method_to_user,
            ValueError,
            "User with ID 'non_existent_user' not found.",
            None,
            "non_existent_user", "pm_1", "credit_card", {}
        )

    def test_add_duplicate_payment_method(self):
        """Test that adding a payment method with a duplicate ID raises a ValueError."""
        create_user("test_user", "Test", "User", "test@example.com", "1990-01-01")
        add_payment_method_to_user("test_user", "pm_1", "credit_card", {})
        self.assert_error_behavior(
            add_payment_method_to_user,
            ValueError,
            "Payment method 'pm_1' already exists for user 'test_user'.",
            None,
            "test_user", "pm_1", "gift_card", {"amount": 50}
        )

    def test_get_flight_success(self):
        """Test that a flight can be retrieved successfully."""
        flight = get_flight("HAT001")
        self.assertIsNotNone(flight)
        self.assertEqual(flight["flight_number"], "HAT001")
        self.assertEqual(flight["origin"], "PHL")
        self.assertEqual(flight["destination"], "LGA")
    
    def test_get_flight_nonexistent(self):
        """Test that retrieving a non-existent flight returns None."""
        flight = get_flight("123")
        self.assertIsNone(flight)

    def test_get_reservation_success(self):
        """Test that a reservation can be retrieved successfully."""
        reservation = get_reservation("4WQ150")
        self.assertIsNotNone(reservation)
        self.assertEqual(reservation["reservation_id"], "4WQ150")

    def test_get_reservation_nonexistent(self):
        """Test that retrieving a non-existent reservation returns None."""
        reservation = get_reservation("123")
        self.assertIsNone(reservation)


    def test_get_user_success(self):
        """Test that a user can be retrieved successfully."""
        user = get_user("mia_li_3668")
        self.assertIsNotNone(user)
        self.assertEqual(user["name"]["first_name"], "Mia")
        self.assertEqual(user["name"]["last_name"], "Li")
    
    def test_get_user_nonexistent(self):
        """Test that retrieving a non-existent user returns None."""
        user = get_user("123")
        self.assertIsNone(user)


    def test_search_flights_success(self):
        """Test that flights can be searched successfully."""
        flights = search_flights("PHL", "LGA", "2024-05-16")
        self.assertIsNotNone(flights)
        self.assertEqual(len(flights), 4)
    
    def test_search_flights_nonexistent(self):
        """Test that searching for non-existent flights returns an empty list."""
        flights = search_flights("PHL", "LGA", "2024-05-15")
        self.assertIsNotNone(flights)
        self.assertEqual(len(flights), 0)

    def test_search_onestop_flights_success(self):
        """Test that one-stop flights can be searched successfully."""
        flights = search_onestop_flights("PHL", "LGA", "2024-05-16")
        self.assertIsNotNone(flights)
        self.assertEqual(len(flights), 5)

    def test_search_onestop_flights_nonexistent(self):
        """Test that searching for non-existent one-stop flights returns an empty list."""
        flights = search_onestop_flights("PHL", "LGA", "2024-05-15")
        self.assertIsNotNone(flights)
        self.assertEqual(len(flights), 0)

    

if __name__ == '__main__':
    unittest.main() 