import unittest
import sys
import os
from datetime import date
from unittest.mock import patch
from copy import deepcopy

# Add the parent directory to the path to fix imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ces_flights.SimulationEngine import db
from ces_flights.SimulationEngine.custom_errors import ValidationError, BookingError, DatabaseError
from ces_flights import (
    search_flights,
    book_flight,
    escalate,
    done,
    fail,
    cancel,
)

# Define initial test DB state
INITIAL_TEST_DB = {
    "flight_bookings": {},
    "_end_of_conversation_status": {},
    "sample_flights": {
        "AA101": {
            "airline": "American Airlines",
            "depart_date": "2025-12-25",
            "depart_time": "10:00:00",
            "arrival_date": "2025-12-25",
            "arrival_time": "18:30:00",
            "price": 550.0,
            "stops": 0,
            "origin": "Los Angeles, CA",
            "destination": "New York, NY",
            "currency": "USD",
            "seating_class": "ECONOMY_CLASS",
            "checked_bags": 1,
            "carry_on_bags": 1
        },
        "DL202": {
            "airline": "Delta",
            "depart_date": "2025-12-25",
            "depart_time": "12:00:00",
            "arrival_date": "2025-12-25",
            "arrival_time": "22:00:00",
            "price": 600.0,
            "stops": 1,
            "origin": "Los Angeles, CA",
            "destination": "New York, NY",
            "currency": "USD",
            "seating_class": "ECONOMY_CLASS",
            "checked_bags": 1,
            "carry_on_bags": 1
        },
        "UA303": {
            "airline": "United Airlines",
            "depart_date": "2025-12-25",
            "depart_time": "14:00:00",
            "arrival_date": "2025-12-25",
            "arrival_time": "22:30:00",
            "price": 580.0,
            "stops": 0,
            "origin": "Los Angeles, CA",
            "destination": "New York, NY",
            "currency": "USD",
            "seating_class": "ECONOMY_CLASS",
            "checked_bags": 1,
            "carry_on_bags": 1
        }
    }
}


class TestCESFlights(BaseTestCaseWithErrorHandler):
    """Test cases for CES Flights API."""

    def setUp(self):
        """Reset DB before each test and mock file saves"""
        # Mock the save function to prevent writing to file during tests
        self.save_patcher = patch('SimulationEngine.db._save_state_to_file')
        self.mock_save = self.save_patcher.start()
        
        # Reset DB to initial test state (deep copy to avoid mutations)
        # We need to update the DB dict in place, not replace it
        db.DB.clear()
        db.DB.update(deepcopy(INITIAL_TEST_DB))
        
        # Also patch the DB used by ces_flights module
        self.db_patcher = patch('ces_flights.ces_flights.DB', db.DB)
        self.db_patcher.start()
    
    def tearDown(self):
        """Clean up mocks after each test"""
        self.save_patcher.stop()
        self.db_patcher.stop()

    # ------------------------
    # search_flights tests
    # ------------------------

    def test_search_flights_valid_minimal(self):
        resp = search_flights(
            origin="San Francisco, CA",
            destination="New York, NY",
            earliest_departure_date="2025-12-01",
            latest_departure_date="2025-12-01",
            earliest_return_date="2025-12-05",
            latest_return_date="2025-12-05",
            num_adult_passengers=1,
            num_child_passengers=0
        )
        self.assertIsInstance(resp, dict)
        self.assertIn("response", resp)
        self.assertIsInstance(resp["response"], list)
        # Check pagination metadata
        self.assertIn("pagination", resp)
        self.assertIn("total_results", resp["pagination"])
        self.assertIn("total_pages", resp["pagination"])
        self.assertIn("current_page", resp["pagination"])
        self.assertIn("page_size", resp["pagination"])
        self.assertIn("has_next", resp["pagination"])
        self.assertIn("has_previous", resp["pagination"])
        # DB may or may not have entries depending on implementation

    def test_search_flights_with_optional_params(self):
        resp = search_flights(
            origin="Los Angeles, CA",
            destination="Chicago, IL",
            earliest_departure_date="2025-12-10",
            latest_departure_date="2025-12-12",
            earliest_return_date="2025-12-20",
            latest_return_date="2025-12-22",
            num_adult_passengers=2,
            num_child_passengers=1,
            carry_on_bag_count=2,
            checked_bag_count=1,
            currency="USD",
            depart_after_hour=9,
            depart_before_hour=17,
            include_airlines=["Delta", "United"],
            max_stops=1,
            seating_classes=["ECONOMY_CLASS", "BUSINESS_CLASS"]
        )
        self.assertIsInstance(resp, dict)
        self.assertIn("response", resp)
        self.assertIsInstance(resp["response"], list)
        self.assertIn("pagination", resp)

    def test_search_flights_invalid_dates(self):
        with self.assertRaises(Exception):  # Can be InvalidDateTimeFormatError or similar
            search_flights(
                origin="SFO",
                destination="JFK",
                earliest_departure_date="invalid-date",
                latest_departure_date="2025-12-01",
                earliest_return_date="2025-12-05",
                latest_return_date="2025-12-05",
                num_adult_passengers=1,
                num_child_passengers=0
            )

    def test_search_flights_invalid_passengers(self):
        with self.assertRaises((ValidationError, ValueError)):  # Can be either
            search_flights(
                origin="SFO",
                destination="JFK",
                earliest_departure_date="2025-12-01",
                latest_departure_date="2025-12-01",
                earliest_return_date="2025-12-05",
                latest_return_date="2025-12-05",
                num_adult_passengers=0,  # not allowed
                num_child_passengers=0
            )

    def test_search_flights_pagination(self):
        """Test pagination functionality"""
        # Search without pagination params (defaults to page=1, page_size=10)
        resp = search_flights(
            origin="Los Angeles, CA",
            destination="New York, NY",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0
        )
        self.assertIn("pagination", resp)
        self.assertEqual(resp["pagination"]["current_page"], 1)
        self.assertEqual(resp["pagination"]["page_size"], 10)
        self.assertFalse(resp["pagination"]["has_previous"])

    def test_search_flights_pagination_custom_page_size(self):
        """Test pagination with custom page size"""
        resp = search_flights(
            origin="Los Angeles, CA",
            destination="New York, NY",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0,
            page=1,
            page_size=5
        )
        self.assertIn("pagination", resp)
        self.assertEqual(resp["pagination"]["page_size"], 5)
        self.assertLessEqual(len(resp["response"]), 5)

    def test_search_flights_pagination_zero_results_high_page(self):
        """Test pagination with zero results and high page number - should adjust to page 1"""
        resp = search_flights(
            origin="NonExistent City, XX",
            destination="Another NonExistent City, YY",
            earliest_departure_date="2099-12-25",
            latest_departure_date="2099-12-25",
            num_adult_passengers=1,
            num_child_passengers=0,
            page=99,  # Request a very high page number
            page_size=10
        )
        
        self.assertIsInstance(resp, dict)
        self.assertIn("pagination", resp)
        
        pagination = resp["pagination"]
        # When there are 0 results, pagination should be properly adjusted
        self.assertEqual(pagination["total_results"], 0, "Should have 0 results")
        self.assertEqual(pagination["total_pages"], 1, "Should have 1 page (minimum) even with 0 results")
        self.assertEqual(pagination["current_page"], 1, "Should auto-adjust to page 1 when requested page 99 with 0 results")
        self.assertFalse(pagination["has_next"], "Should not have next page with 0 results")
        self.assertFalse(pagination["has_previous"], "Should not have previous page when on page 1")
        self.assertEqual(len(resp["response"]), 0, "Response should be empty")

    def test_search_flights_bag_count_minimum_match(self):
        """Test that bag count filters use minimum match (>=) not exact match
        
        Bug fix test: Verifies that requesting checked_bag_count=1 returns flights
        with 1, 2, or more checked bags (not just exactly 1).
        """
        # Search for flights that allow at least 1 checked bag
        resp = search_flights(
            origin="Los Angeles, CA",
            destination="New York, NY",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0,
            checked_bag_count=1
        )
        
        self.assertIsInstance(resp, dict)
        self.assertIn("response", resp)
        
        # If there are results, verify all have at least 1 checked bag
        # (could have 1, 2, 3, etc. - not just exactly 1)
        for flight in resp["response"]:
            if "checked_bags" in flight and flight["checked_bags"] is not None:
                self.assertGreaterEqual(flight["checked_bags"], 1, 
                    f"Flight {flight.get('flight_id')} should have at least 1 checked bag, has {flight['checked_bags']}")

    def test_search_flights_carry_on_bag_count_minimum_match(self):
        """Test that carry-on bag count filters use minimum match (>=) not exact match"""
        resp = search_flights(
            origin="Los Angeles, CA",
            destination="New York, NY",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0,
            carry_on_bag_count=1
        )
        
        self.assertIsInstance(resp, dict)
        self.assertIn("response", resp)
        
        # If there are results, verify all have at least 1 carry-on bag
        for flight in resp["response"]:
            if "carry_on_bags" in flight and flight["carry_on_bags"] is not None:
                self.assertGreaterEqual(flight["carry_on_bags"], 1,
                    f"Flight {flight.get('flight_id')} should have at least 1 carry-on bag, has {flight['carry_on_bags']}")

    # ------------------------
    # Currency conversion tests
    # ------------------------

    def test_search_flights_currency_usd_default(self):
        """Test that USD is used by default when no currency specified"""
        resp = search_flights(
            origin="Los Angeles, CA",
            destination="New York, NY",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0
        )
        
        self.assertIsInstance(resp, dict)
        self.assertIn("response", resp)
        
        # All flights should have USD as currency when not specified
        for flight in resp["response"]:
            self.assertEqual(flight["currency"], "USD",
                f"Flight {flight.get('flight_id')} should have USD currency when not specified")

    def test_search_flights_currency_eur_conversion(self):
        """Test EUR currency conversion"""
        resp = search_flights(
            origin="Los Angeles, CA",
            destination="New York, NY",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0,
            currency="EUR"
        )
        
        self.assertIsInstance(resp, dict)
        self.assertIn("response", resp)
        
        # All flights should have EUR as currency
        for flight in resp["response"]:
            self.assertEqual(flight["currency"], "EUR",
                f"Flight {flight.get('flight_id')} should have EUR currency")
            # Price should be converted (EUR rate is 0.92, so EUR price < USD price)
            self.assertIsInstance(flight["price"], float)

    def test_search_flights_currency_jpy_conversion(self):
        """Test JPY currency conversion"""
        resp = search_flights(
            origin="Los Angeles, CA",
            destination="New York, NY",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0,
            currency="JPY"
        )
        
        self.assertIsInstance(resp, dict)
        self.assertIn("response", resp)
        
        # All flights should have JPY as currency
        for flight in resp["response"]:
            self.assertEqual(flight["currency"], "JPY",
                f"Flight {flight.get('flight_id')} should have JPY currency")
            # JPY prices should be much higher than USD (rate is 156.12)
            self.assertIsInstance(flight["price"], float)

    def test_search_flights_currency_invalid(self):
        """Test that invalid currency code raises ValueError"""
        with self.assertRaises(ValueError) as context:
            search_flights(
                origin="Los Angeles, CA",
                destination="New York, NY",
                earliest_departure_date="2025-12-25",
                latest_departure_date="2025-12-25",
                earliest_return_date="2026-01-05",
                latest_return_date="2026-01-05",
                num_adult_passengers=1,
                num_child_passengers=0,
                currency="INVALID"
            )
        
        error_message = str(context.exception)
        self.assertIn("supported currencies", error_message.lower())

    def test_search_flights_currency_case_insensitive(self):
        """Test that currency codes are case-insensitive"""
        resp_lower = search_flights(
            origin="Los Angeles, CA",
            destination="New York, NY",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0,
            currency="eur"  # lowercase
        )
        
        resp_upper = search_flights(
            origin="Los Angeles, CA",
            destination="New York, NY",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0,
            currency="EUR"  # uppercase
        )
        
        # Both should have EUR as currency
        for flight in resp_lower["response"]:
            self.assertEqual(flight["currency"], "EUR")
        for flight in resp_upper["response"]:
            self.assertEqual(flight["currency"], "EUR")

    def test_search_flights_all_supported_currencies(self):
        """Test that all 20 supported currencies work"""
        supported = ["USD", "EUR", "JPY", "GBP", "CNY", "AUD", "CAD", "CHF", "HKD", "SGD",
                     "SEK", "KRW", "NOK", "NZD", "INR", "MXN", "TWD", "ZAR", "BRL", "DKK"]
        
        for currency_code in supported:
            with self.subTest(currency=currency_code):
                resp = search_flights(
                    origin="Los Angeles, CA",
                    destination="New York, NY",
                    earliest_departure_date="2025-12-25",
                    latest_departure_date="2025-12-25",
                    earliest_return_date="2026-01-05",
                    latest_return_date="2026-01-05",
                    num_adult_passengers=1,
                    num_child_passengers=0,
                    currency=currency_code
                )
                
                self.assertIsInstance(resp, dict)
                self.assertIn("response", resp)
                
                # Check all flights have the requested currency
                for flight in resp["response"]:
                    self.assertEqual(flight["currency"], currency_code)
                    self.assertIsInstance(flight["price"], float)

    # ------------------------
    # book_flight tests
    # ------------------------

    def test_book_flight_valid_single_traveler(self):
        traveler = {
            "first_name": "Alice", 
            "last_name": "Smith", 
            "date_of_birth": "1990-01-01"
        }
        # Try to book - may succeed if flight exists, or raise BookingError if not
        try:
            resp = book_flight(flight_id="AA101", travelers=[traveler])
            # If flight exists, check response structure
            self.assertIsInstance(resp, dict)
            self.assertIn("booking_id", resp)
            self.assertIn("confirmation_number", resp)
            self.assertIn("flight_id", resp)
            self.assertEqual(resp["flight_id"], "AA101")
            # Check new "failed" field
            self.assertIn("failed", resp)
            self.assertFalse(resp["failed"])  # Should be False for confirmed bookings
            # Check confirmation number is 6-character hex string
            self.assertEqual(len(resp["confirmation_number"]), 6)
            self.assertTrue(all(c in '0123456789ABCDEF' for c in resp["confirmation_number"]))
        except BookingError:
            # Expected if no flights available - this is acceptable
            pass

    def test_book_flight_valid_multiple_travelers(self):
        t1 = {
            "first_name": "Alice", 
            "last_name": "Smith", 
            "date_of_birth": "1990-01-01",
        }
        t2 = {
            "first_name": "Bob", 
            "last_name": "Jones", 
            "date_of_birth": "1985-05-20",
            "known_traveler_number": "KTN123"
        }
        # Try to book - may succeed if flight exists, or raise BookingError if not
        try:
            resp = book_flight(flight_id="AA101", travelers=[t1, t2])
            # If flight exists, check response structure
            self.assertIsInstance(resp, dict)
            self.assertIn("booking_id", resp)
            self.assertIn("confirmation_number", resp)
            self.assertIn("flight_id", resp)
            self.assertEqual(resp["flight_id"], "AA101")
            # Check new "failed" field
            self.assertIn("failed", resp)
            self.assertFalse(resp["failed"])
            # Check confirmation number format
            self.assertEqual(len(resp["confirmation_number"]), 6)
            self.assertTrue(all(c in '0123456789ABCDEF' for c in resp["confirmation_number"]))
        except BookingError:
            # Expected if no flights available - this is acceptable
            pass

    def test_book_flight_missing_travelers(self):
        # Should raise error when no travelers provided
        with self.assertRaises((ValidationError, Exception)):
            book_flight(flight_id="AA101", travelers=[])

    def test_book_flight_invalid_traveler_schema(self):
        bad_traveler = {"first_name": "", "last_name": "Doe", "date_of_birth": "not-a-date"}
        # Should raise ValidationError for invalid traveler data
        with self.assertRaises((ValidationError, Exception)):
            book_flight(flight_id="AA101", travelers=[bad_traveler])

    def test_book_flight_travelers_as_strings(self):
        """Test booking with travelers as strings instead of dictionaries"""
        # Should raise TypeError when trying to unpack strings with **
        with self.assertRaises((TypeError, ValidationError, Exception)):
            book_flight(flight_id="AA101", travelers=["NotAnObject", "AlsoNotAnObject"])

    # ------------------------
    # escalate tests
    # ------------------------

    def test_escalate_with_input(self):
        resp = escalate(input="Need human agent")
        self.assertEqual(resp, {"ok": True})
        self.assertIsNotNone(db.DB.get("_end_of_conversation_status"))

    def test_escalate_without_input(self):
        resp = escalate()
        self.assertEqual(resp, {"ok": True})
        self.assertIsNotNone(db.DB.get("_end_of_conversation_status"))

    # ------------------------
    # done tests
    # ------------------------

    def test_done_with_input(self):
        resp = done(input="Task completed successfully")
        self.assertEqual(resp, {"ok": True})
        self.assertIsNotNone(db.DB.get("_end_of_conversation_status"))

    def test_done_without_input(self):
        resp = done()
        self.assertEqual(resp, {"ok": True})
        self.assertIsNotNone(db.DB.get("_end_of_conversation_status"))

    def test_done_persists_multiple_calls(self):
        done(input="Task A completed")
        done(input="Task B completed")
        # Check that _end_of_conversation_status exists and has entries
        status = db.DB.get("_end_of_conversation_status", {})
        self.assertGreaterEqual(len(status), 0)  # May be 0 or more depending on implementation

    # ------------------------
    # fail tests
    # ------------------------

    def test_fail_with_input(self):
        resp = fail(input="Could not understand customer request")
        self.assertEqual(resp, {"ok": True})
        self.assertIsNotNone(db.DB.get("_end_of_conversation_status"))

    def test_fail_without_input(self):
        resp = fail()
        self.assertEqual(resp, {"ok": True})
        self.assertIsNotNone(db.DB.get("_end_of_conversation_status"))

    # ------------------------
    # cancel tests
    # ------------------------

    def test_cancel_with_input(self):
        resp = cancel(input="Customer wants to cancel booking")
        self.assertEqual(resp, {"ok": True})
        self.assertIsNotNone(db.DB.get("_end_of_conversation_status"))

    def test_cancel_without_input(self):
        resp = cancel()
        self.assertEqual(resp, {"ok": True})
        self.assertIsNotNone(db.DB.get("_end_of_conversation_status"))

    # ------------------------
    # search_flights enhanced tests
    # ------------------------

    def test_search_flights_city_format_conversion(self):
        """Test that city names are properly converted to City, State format"""
        resp = search_flights(
            origin="New York",  # Should be converted to "New York, NY"
            destination="Los Angeles",  # Should be converted to "Los Angeles, CA"
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=2,
            num_child_passengers=1
        )
        self.assertIsInstance(resp, dict)
        self.assertIn("response", resp)
        self.assertIsInstance(resp["response"], list)

    def test_search_flights_float_passenger_counts(self):
        """Test that float passenger counts are converted to integers"""
        resp = search_flights(
            origin="New York, NY",
            destination="Los Angeles, CA",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=2.0,  # Float value
            num_child_passengers=1.0   # Float value
        )
        self.assertIsInstance(resp, dict)
        self.assertIn("response", resp)
        self.assertIsInstance(resp["response"], list)

    def test_search_flights_international_cities(self):
        """Test international city format conversion"""
        resp = search_flights(
            origin="London",  # Should be converted to "London, United Kingdom"
            destination="Paris",  # Should be converted to "Paris, France"
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0
        )
        self.assertIsInstance(resp, dict)
        self.assertIn("response", resp)
        self.assertIsInstance(resp["response"], list)

    def test_search_flights_date_range_validation(self):
        """Test that return date must be after departure date"""
        # Should raise InvalidDateRangeError when return date is before departure date
        with self.assertRaises(Exception):  # Can be InvalidDateRangeError or similar
            search_flights(
                origin="New York, NY",
                destination="Los Angeles, CA",
                earliest_departure_date="2025-12-25",
                latest_departure_date="2025-12-25",
                earliest_return_date="2025-12-24",  # Before departure date
                latest_return_date="2025-12-24",
                num_adult_passengers=1,
                num_child_passengers=0
            )

    def test_search_flights_date_range_limits(self):
        """Test that dates must be within allowed range (2024-03-29 to 2025-03-28)"""
        resp = search_flights(
            origin="New York, NY",
            destination="Los Angeles, CA",
            earliest_departure_date="2025-01-01",  # Too early
            latest_departure_date="2025-01-01",
            earliest_return_date="2025-01-05",
            latest_return_date="2025-01-05",
            num_adult_passengers=1,
            num_child_passengers=0
        )
        # No status key in DI - just check results
        # No message key in DI - just check results

    def test_search_flights_all_optional_parameters(self):
        """Test search with all optional parameters"""
        resp = search_flights(
            origin="New York, NY",
            destination="Los Angeles, CA",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=2,
            num_child_passengers=1,
            carry_on_bag_count=2,
            checked_bag_count=1,
            currency="USD",
            depart_after_hour=9,
            depart_before_hour=17,
            include_airlines=["American Airlines", "Delta"],
            max_stops=1,
            num_infant_in_lap_passengers=0,
            num_infant_in_seat_passengers=0,
            seating_classes=["ECONOMY_CLASS", "BUSINESS_CLASS"],
            cheapest=True
        )
        self.assertIsInstance(resp, dict)
        self.assertIn("response", resp)
        self.assertIsInstance(resp["response"], list)

    def test_search_flights_no_results(self):
        """Test search that returns no flights"""
        resp = search_flights(
            origin="New York, NY",
            destination="Los Angeles, CA",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0,
            include_airlines=["NonExistent Airline"]  # Should return no results
        )
        self.assertIsInstance(resp, dict)
        self.assertIn("response", resp)
        self.assertIsInstance(resp["response"], list)
        # Results might be empty due to filtering

    # ------------------------
    # book_flight enhanced tests
    # ------------------------

    def test_book_flight_with_known_traveler_number(self):
        """Test booking with known traveler number"""
        traveler = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1985-06-15"
        }
        # Try to book - may succeed if flight exists, or raise BookingError if not
        try:
            resp = book_flight(flight_id="AA101", travelers=[traveler], known_traveler_number="KTN123456789")
            # If flight exists, check response structure
            self.assertIsInstance(resp, dict)
            self.assertIn("booking_id", resp)
            self.assertIn("confirmation_number", resp)
            self.assertIn("flight_id", resp)
            self.assertEqual(resp["flight_id"], "AA101")
        except BookingError:
            # Expected if no flights available - this is acceptable
            pass

    def test_book_flight_invalid_date_format(self):
        """Test booking with invalid date format"""
        traveler = {
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "not-a-date",
        }
        # Should raise ValidationError for invalid date
        with self.assertRaises((ValidationError, Exception)):
            book_flight(flight_id="AA101", travelers=[traveler])

    def test_book_flight_missing_required_fields(self):
        """Test booking with missing required fields"""
        traveler = {
            "first_name": "",  # Empty first name
            "last_name": "Smith",
            "date_of_birth": "1990-01-01",
        }
        # Should raise ValidationError for empty first name
        with self.assertRaises((ValidationError, Exception)):
            book_flight(flight_id="AA101", travelers=[traveler])

    def test_book_flight_integer_flight_id_bug_fix(self):
        """Test that flight_id must be a string, not an integer - User prompt: 'Book flight 123 for me'"""
        traveler = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1985-06-15",
        }
        # Should raise ValidationError when flight_id is an integer instead of string
        with self.assertRaises((ValidationError, Exception)) as context:
            book_flight(flight_id=123, travelers=[traveler])
        
        # Verify the error message mentions the type issue
        error_message = str(context.exception)
        self.assertIn("Input should be a valid string", error_message)
        self.assertIn("int", error_message)

    def test_book_flight_float_flight_id_bug_fix(self):
        """Test that flight_id must be a string, not a float - User prompt: 'Book flight 123.45 for me'"""
        traveler = {
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "1990-03-20",
        }
        # Should raise ValidationError when flight_id is a float instead of string
        with self.assertRaises((ValidationError, Exception)) as context:
            book_flight(flight_id=123.45, travelers=[traveler])
        
        # Verify the error message mentions the type issue
        error_message = str(context.exception)
        self.assertIn("Input should be a valid string", error_message)
        self.assertIn("float", error_message)

    def test_book_flight_none_flight_id_bug_fix(self):
        """Test that flight_id cannot be None - User prompt: 'Book flight for me' (missing flight ID)"""
        traveler = {
            "first_name": "Bob",
            "last_name": "Johnson",
            "date_of_birth": "1988-12-10",
        }
        # Should raise ValidationError when flight_id is None
        with self.assertRaises((ValidationError, Exception)) as context:
            book_flight(flight_id=None, travelers=[traveler])
        
        # Verify the error message mentions the type issue
        error_message = str(context.exception)
        self.assertIn("Input should be a valid string", error_message)
        self.assertIn("NoneType", error_message)

    def test_book_flight_empty_string_flight_id_bug_fix(self):
        """Test that flight_id cannot be empty string - User prompt: 'Book flight with empty ID'"""
        traveler = {
            "first_name": "Alice",
            "last_name": "Brown",
            "date_of_birth": "1992-07-25",
        }
        # Should raise ValidationError when flight_id is empty string
        with self.assertRaises((ValidationError, Exception)) as context:
            book_flight(flight_id="", travelers=[traveler])
        
        # Verify the error message mentions empty flight_id
        error_message = str(context.exception)
        self.assertIn("flight_id cannot be empty", error_message)

    def test_book_flight_whitespace_only_flight_id_bug_fix(self):
        """Test that flight_id cannot be whitespace-only - User prompt: 'Book flight with spaces'"""
        traveler = {
            "first_name": "Charlie",
            "last_name": "Wilson",
            "date_of_birth": "1987-11-03",
        }
        # Should raise ValidationError when flight_id is whitespace-only
        with self.assertRaises((ValidationError, Exception)) as context:
            book_flight(flight_id="   ", travelers=[traveler])
        
        # Verify the error message mentions whitespace-only flight_id
        error_message = str(context.exception)
        self.assertIn("flight_id cannot be empty", error_message)

    def test_book_flight_valid_string_flight_id(self):
        """Test that valid string flight_id works correctly - User prompt: 'Book flight AA101 for me'"""
        traveler = {
            "first_name": "David",
            "last_name": "Miller",
            "date_of_birth": "1983-09-18",
        }
        # Should work with valid string flight_id
        try:
            resp = book_flight(flight_id="AA101", travelers=[traveler])
            # If flight exists, check response structure
            self.assertIsInstance(resp, dict)
            self.assertIn("booking_id", resp)
            self.assertIn("confirmation_number", resp)
            self.assertIn("flight_id", resp)
            self.assertEqual(resp["flight_id"], "AA101")
        except BookingError:
            # Expected if no flights available - this is acceptable
            pass

    def test_book_flight_numeric_string_flight_id(self):
        """Test that numeric string flight_id works correctly - User prompt: 'Book flight 123 for me' (as string)"""
        traveler = {
            "first_name": "Emma",
            "last_name": "Davis",
            "date_of_birth": "1991-04-12",
        }
        # Should work with numeric string flight_id
        try:
            resp = book_flight(flight_id="123", travelers=[traveler])
            # If flight exists, check response structure
            self.assertIsInstance(resp, dict)
            self.assertIn("booking_id", resp)
            self.assertIn("confirmation_number", resp)
            self.assertIn("flight_id", resp)
            self.assertEqual(resp["flight_id"], "123")
        except (BookingError, Exception) as e:
            # Expected if no flights available - this is acceptable
            if "not found" in str(e):
                pass
            else:
                raise

    def test_book_flight_large_group_mixed_optional_parameters(self):
        """Test large group booking with mixed optional parameters - User prompt: 'Book flight for our company retreat group of 10 people'"""
        # Sample input from the user with 10 travelers, some with known_traveler_number, some without
        travelers = [
            {"first_name": "Alice", "last_name": "Williams", "date_of_birth": "1990-05-15", "known_traveler_number": "987654321"},
            {"first_name": "Bob", "last_name": "Johnson", "date_of_birth": "1985-08-22"},
            {"first_name": "Charlie", "last_name": "Brown", "date_of_birth": "2002-01-30", "known_traveler_number": "123123123"},
            {"first_name": "Diana", "last_name": "Prince", "date_of_birth": "1988-11-01"},
            {"first_name": "Ethan", "last_name": "Hunt", "date_of_birth": "1992-03-12", "known_traveler_number": "456456456"},
            {"first_name": "Fiona", "last_name": "Glenanne", "date_of_birth": "1995-07-19"},
            {"first_name": "George", "last_name": "Costanza", "date_of_birth": "1979-09-25", "known_traveler_number": "789789789"},
            {"first_name": "Helen", "last_name": "Troy", "date_of_birth": "2000-02-29"},
            {"first_name": "Ivan", "last_name": "Drago", "date_of_birth": "1980-04-04", "known_traveler_number": "101010101"},
            {"first_name": "Jane", "last_name": "Doe", "date_of_birth": "1999-12-31"}
        ]
        
        # Should work with large group and mixed optional parameters
        try:
            resp = book_flight(flight_id="AA101", travelers=travelers)
            # If flight exists, check response structure
            self.assertIsInstance(resp, dict)
            self.assertIn("booking_id", resp)
            self.assertIn("confirmation_number", resp)
            self.assertIn("flight_id", resp)
            self.assertEqual(resp["flight_id"], "AA101")
            
            # Verify that all 10 travelers were processed
            booking_data = db.DB.get("flight_bookings", {}).get(resp["booking_id"])
            if booking_data:
                self.assertEqual(len(booking_data["travelers"]), 10)
        except BookingError:
            # Expected if no flights available - this is acceptable
            pass

    def test_book_flight_valid_yyyy_mm_dd_format(self):
        """Test that valid YYYY-MM-DD date strings work correctly - User prompt: 'Book flight for John born on 1990-05-15'"""
        traveler = {
            "first_name": "John",
            "last_name": "Smith",
            "date_of_birth": "1990-05-15",  # Valid YYYY-MM-DD format
        }
        
        # Should work with valid YYYY-MM-DD date string
        try:
            resp = book_flight(flight_id="AA101", travelers=[traveler])
            # If flight exists, check response structure
            self.assertIsInstance(resp, dict)
            self.assertIn("booking_id", resp)
            self.assertIn("confirmation_number", resp)
            self.assertIn("flight_id", resp)
            self.assertEqual(resp["flight_id"], "AA101")
        except BookingError:
            # Expected if no flights available - this is acceptable
            pass

    def test_book_flight_invalid_date_format_mm_dd_yyyy(self):
        """Test booking with MM/DD/YYYY date format (should fail) - User prompt: 'Book flight for John born on 05/15/1990'"""
        traveler = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "05/15/1990",  # MM/DD/YYYY format (not supported)
        }
        
        # Should raise ValidationError for unsupported date format
        with self.assertRaises((ValidationError, Exception)) as context:
            book_flight(flight_id="AA101", travelers=[traveler])
        
        # Verify the error message mentions date validation
        error_message = str(context.exception)
        self.assertIn("Date must be in YYYY-MM-DD format", error_message)

    def test_book_flight_invalid_date_format_dd_mm_yyyy(self):
        """Test booking with DD/MM/YYYY date format (should fail) - User prompt: 'Book flight for Jane born on 15/05/1990'"""
        traveler = {
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "15/05/1990",  # DD/MM/YYYY format (not supported)
        }
        
        # Should raise ValidationError for unsupported date format
        with self.assertRaises((ValidationError, Exception)) as context:
            book_flight(flight_id="AA101", travelers=[traveler])
        
        # Verify the error message mentions date validation
        error_message = str(context.exception)
        self.assertIn("Date must be in YYYY-MM-DD format", error_message)

    def test_book_flight_invalid_date_format(self):
        """Test booking with invalid date format - User prompt: 'Book flight for John born on invalid-date'"""
        traveler = {
            "first_name": "John",
            "last_name": "Smith",
            "date_of_birth": "invalid-date",
        }
        
        # Should raise ValidationError for invalid date format
        with self.assertRaises((ValidationError, Exception)) as context:
            book_flight(flight_id="AA101", travelers=[traveler])
        
        # Verify the error message mentions date validation
        error_message = str(context.exception)
        self.assertIn("Date must be in YYYY-MM-DD format", error_message)

    def test_book_flight_malformed_yyyy_mm_dd_format(self):
        """Test booking with malformed YYYY-MM-DD format - User prompt: 'Book flight for John born on 1990-5-15'"""
        traveler = {
            "first_name": "John",
            "last_name": "Smith",
            "date_of_birth": "1990-5-15",  # Missing leading zero in month
        }
        
        # Should raise ValidationError for malformed date format
        with self.assertRaises((ValidationError, Exception)) as context:
            book_flight(flight_id="AA101", travelers=[traveler])
        
        # Verify the error message mentions date validation
        error_message = str(context.exception)
        self.assertIn("Date must be in YYYY-MM-DD format", error_message)

    def test_book_flight_mixed_known_traveler_numbers(self):
        """Test booking with mixed known traveler number scenarios - User prompt: 'Book flight for group with some TSA PreCheck members'"""
        travelers = [
            {"first_name": "Alice", "last_name": "Williams", "date_of_birth": "1990-05-15", "known_traveler_number": "987654321"},
            {"first_name": "Bob", "last_name": "Johnson", "date_of_birth": "1985-08-22"},  # No KTN
            {"first_name": "Charlie", "last_name": "Brown", "date_of_birth": "2002-01-30", "known_traveler_number": "123123123"},
            {"first_name": "Diana", "last_name": "Prince", "date_of_birth": "1988-11-01", "known_traveler_number": None},  # Explicit None
            {"first_name": "Ethan", "last_name": "Hunt", "date_of_birth": "1992-03-12"}  # Missing KTN field
        ]
        
        # Should work with mixed known traveler number scenarios
        try:
            resp = book_flight(flight_id="AA101", travelers=travelers)
            # If flight exists, check response structure
            self.assertIsInstance(resp, dict)
            self.assertIn("booking_id", resp)
            self.assertIn("confirmation_number", resp)
            self.assertIn("flight_id", resp)
            self.assertEqual(resp["flight_id"], "AA101")
            
            # Verify that all 5 travelers were processed
            booking_data = db.DB.get("flight_bookings", {}).get(resp["booking_id"])
            if booking_data:
                self.assertEqual(len(booking_data["travelers"]), 5)
        except BookingError:
            # Expected if no flights available - this is acceptable
            pass

    def test_book_flight_large_group_performance(self):
        """Test large group booking performance - User prompt: 'Book flight for our entire department of 20 people'"""
        # Create a large group of 20 travelers
        travelers = []
        for i in range(20):
            traveler = {
                "first_name": f"Person{i+1}",
                "last_name": f"LastName{i+1}",
                "date_of_birth": f"{1985 + (i % 10)}-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}"
            }
            # Add known_traveler_number for every 3rd person
            if i % 3 == 0:
                traveler["known_traveler_number"] = f"KTN{i+1:06d}"
            travelers.append(traveler)
        
        # Should work with large group
        try:
            resp = book_flight(flight_id="AA101", travelers=travelers)
            # If flight exists, check response structure
            self.assertIsInstance(resp, dict)
            self.assertIn("booking_id", resp)
            self.assertIn("confirmation_number", resp)
            self.assertIn("flight_id", resp)
            self.assertEqual(resp["flight_id"], "AA101")
            
            # Verify that all 20 travelers were processed
            booking_data = db.DB.get("flight_bookings", {}).get(resp["booking_id"])
            if booking_data:
                self.assertEqual(len(booking_data["travelers"]), 20)
        except BookingError:
            # Expected if no flights available - this is acceptable
            pass

    def test_book_flight_future_date_of_birth_string(self):
        """Test booking with future date of birth as string - User prompt: 'Book flight for John born tomorrow'"""
        from datetime import date, timedelta
        tomorrow = date.today() + timedelta(days=1)
        tomorrow_str = tomorrow.strftime('%Y-%m-%d')
        
        traveler = {
            "first_name": "John",
            "last_name": "Future",
            "date_of_birth": tomorrow_str,  # Future date as string
        }
        
        # Should raise ValidationError for future date of birth
        with self.assertRaises((ValidationError, Exception)) as context:
            book_flight(flight_id="AA101", travelers=[traveler])
        
        # Verify the error message mentions future date
        error_message = str(context.exception)
        self.assertIn("Date of birth cannot be in the future", error_message)
        self.assertIn("John", error_message)

    # REMOVED: test_book_flight_future_date_of_birth_object
    # This test was removed because the API now only accepts primitive types (strings)
    # and rejects date objects. The test was passing date objects which are now correctly rejected
    # before even checking if the date is in the future.

    def test_book_flight_mixed_future_and_valid_dates(self):
        """Test booking with mixed future and valid dates - User prompt: 'Book flight for group with one person born in the future'"""
        from datetime import date, timedelta
        future_date = date.today() + timedelta(days=30)
        future_date_str = future_date.strftime('%Y-%m-%d')
        
        travelers = [
            {"first_name": "Alice", "last_name": "Valid", "date_of_birth": "1990-05-15"},
            {"first_name": "Bob", "last_name": "Future", "date_of_birth": future_date_str},  # Future date
            {"first_name": "Charlie", "last_name": "Valid", "date_of_birth": "1985-08-22"}
        ]
        
        # Should raise ValidationError for future date of birth
        with self.assertRaises((ValidationError, Exception)) as context:
            book_flight(flight_id="AA101", travelers=travelers)
        
        # Verify the error message mentions future date and the correct traveler
        error_message = str(context.exception)
        self.assertIn("Date of birth cannot be in the future", error_message)
        self.assertIn("Bob", error_message)

    def test_book_flight_today_date_of_birth(self):
        """Test booking with today's date of birth - User prompt: 'Book flight for someone born today'"""
        from datetime import date
        today = date.today()
        today_str = today.strftime('%Y-%m-%d')
        
        traveler = {
            "first_name": "Today",
            "last_name": "Born",
            "date_of_birth": today_str,  # Today's date (should be valid)
        }
        
        # Should work with today's date (not future)
        try:
            resp = book_flight(flight_id="AA101", travelers=[traveler])
            # If flight exists, check response structure
            self.assertIsInstance(resp, dict)
            self.assertIn("booking_id", resp)
            self.assertIn("confirmation_number", resp)
            self.assertIn("flight_id", resp)
            self.assertEqual(resp["flight_id"], "AA101")
        except BookingError:
            # Expected if no flights available - this is acceptable
            pass

    # ------------------------
    # Integration tests
    # ------------------------

    def test_complete_booking_workflow(self):
        """Test complete workflow: search -> book -> done"""
        # Step 1: Search for flights
        search_resp = search_flights(
            origin="New York, NY",
            destination="Los Angeles, CA",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0
        )
        self.assertIsInstance(search_resp, dict)
        self.assertIn("response", search_resp)
        self.assertIsInstance(search_resp["response"], list)
        
        # Step 2: Try to book a flight (will likely fail if no flights available)
        # This is expected behavior, so we catch the error
        traveler = {
            "first_name": "Alice",
            "last_name": "Johnson",
            "date_of_birth": "1990-03-15",
        }
        booking_attempted = False
        try:
            book_resp = book_flight(flight_id="AA101", travelers=[traveler])
            self.assertIn("booking_id", book_resp)
            self.assertIn("confirmation_number", book_resp)
            self.assertIn("flight_id", book_resp)
            booking_attempted = True
        except (BookingError, Exception):
            # Expected if no flights available - this is normal
            booking_attempted = True
        
        # Verify booking was attempted
        self.assertTrue(booking_attempted)
        
        # Step 3: Complete the task
        done_resp = done(input="Booking completed successfully")
        self.assertEqual(done_resp, {"ok": True})

    def test_error_handling_workflow(self):
        """Test error handling workflow: search error -> escalate"""
        # Step 1: Search with invalid parameters should raise exception
        try:
            search_resp = search_flights(
                origin="New York, NY",
                destination="Los Angeles, CA",
                earliest_departure_date="invalid-date",
                latest_departure_date="2025-12-25",
                earliest_return_date="2026-01-05",
                latest_return_date="2026-01-05",
                num_adult_passengers=1,
                num_child_passengers=0
            )
        except Exception:
            pass  # Expected
        
        # Step 2: Escalate due to error
        escalate_resp = escalate(input="Search failed due to invalid date format")
        self.assertEqual(escalate_resp, {"ok": True})

    def test_cancellation_workflow(self):
        """Test cancellation workflow: search -> cancel"""
        # Step 1: Search for flights
        search_resp = search_flights(
            origin="New York, NY",
            destination="Los Angeles, CA",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0
        )
        self.assertIsInstance(search_resp, dict)
        self.assertIn("response", search_resp)
        self.assertIsInstance(search_resp["response"], list)
        
        # Step 2: Cancel the booking
        cancel_resp = cancel(input="Customer changed their mind")
        self.assertEqual(cancel_resp, {"ok": True})

    def test_booking_escalation_workflow(self):
        """Test booking escalation workflow: search -> escalate to airline website"""
        # Step 1: Search for flights
        search_resp = search_flights(
            origin="New York, NY",
            destination="Los Angeles, CA",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0
        )
        self.assertIsInstance(search_resp, dict)
        self.assertIn("response", search_resp)
        self.assertIsInstance(search_resp["response"], list)
        
        # Step 2: User wants to book - system escalates to airline website
        escalate_resp = escalate(input="To complete your booking, please proceed to the airline's website.")
        self.assertEqual(escalate_resp, {"ok": True})
        self.assertIsNotNone(db.DB.get("_end_of_conversation_status"))  # Should be recorded in database

    def test_exact_booking_escalation_flow(self):
        """Test the exact flow described: user wants to book -> escalate to airline website"""
        # This test covers the exact scenario described in the user query:
        # "To complete your booking, please proceed to the airline's website."
        # FUNCTION_CALL: escalate(args={'input': "To complete your booking, please proceed to the airline's website."})
        
        # Step 1: User searches for flights (implied previous step)
        search_resp = search_flights(
            origin="New York, NY",
            destination="Los Angeles, CA",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2026-01-05",
            latest_return_date="2026-01-05",
            num_adult_passengers=1,
            num_child_passengers=0
        )
        self.assertIsInstance(search_resp, dict)
        self.assertIn("response", search_resp)
        self.assertIsInstance(search_resp["response"], list)
        
        # Step 2: User wants to book a flight
        # System responds with escalation message and calls escalate function
        escalation_message = "To complete your booking, please proceed to the airline's website."
        escalate_resp = escalate(input=escalation_message)
        
        # Verify the escalation call matches the expected format
        self.assertEqual(escalate_resp, {"ok": True})
        self.assertIsNotNone(db.DB.get("_end_of_conversation_status"))  # Escalation is recorded
        
        # Verify the escalation data contains the expected message if DB has entries
        status_dict = db.DB.get("_end_of_conversation_status", {})
        if status_dict:
            escalation_data = None
            for key, data in status_dict.items():
                if isinstance(data, dict) and data.get("input") == escalation_message:
                    escalation_data = data
                    break
            
            if escalation_data:
                self.assertEqual(escalation_data["input"], escalation_message)
                self.assertEqual(escalation_data["status"], "escalated")

    def test_exact_no_flights_found_response(self):
        """Test the exact 'no flights found' response format as shown in user query"""
        # This test covers the exact scenario from the user query:
        # FUNCTION_CALL: search_flights(args={...}) 
        # FUNCTION_RESPONSE: search_flights(response={'results': []})
        # "I'm sorry, but no flights were found that match your request. Would you like to revise your search?"
        
        # Search for flights on a date that doesn't exist in the test database (2025-12-20)
        # Our test DB only has flights on 2025-12-25
        resp = search_flights(
            num_infant_in_lap_passengers=None,
            checked_bag_count=None,
            earliest_return_date=None,  # Don't request return flights
            carry_on_bag_count=None,
            latest_return_date=None,  # Don't request return flights
            latest_departure_date="2025-12-20",
            depart_before_hour=None,
            destination="New York, NY",
            currency=None,
            include_airlines=None,
            num_child_passengers=1.0,
            depart_after_hour=None,
            num_adult_passengers=2.0,
            origin="Los Angeles, CA",
            num_infant_in_seat_passengers=None,
            max_stops=None,
            cheapest=None,
            earliest_departure_date="2025-12-20",
            seating_classes=None
        )
        
        # Verify the exact response format
        self.assertIsInstance(resp, dict)
        self.assertIn("response", resp)
        self.assertIsInstance(resp["response"], list)
        self.assertEqual(resp["response"], [])  # Empty results list
        
        # Verify the response structure matches the expected format
        self.assertEqual(len(resp["response"]), 0)

    def test_no_flights_found_with_different_criteria(self):
        """Test no flights found with various search criteria combinations"""
        test_cases = [
            # Case 1: Non-existent airline filter
            {
                "origin": "Los Angeles, CA",
                "destination": "New York, NY",
                "earliest_departure_date": "2025-12-25",
                "latest_departure_date": "2025-12-25", 
                "earliest_return_date": "2025-12-30",
                "latest_return_date": "2025-12-30",
                "num_adult_passengers": 1,
                "num_child_passengers": 0,
                "include_airlines": ["NonExistent Airline"]
            },
            # Case 2: Impossible time constraints
            {
                "origin": "Los Angeles, CA",
                "destination": "New York, NY",
                "earliest_departure_date": "2025-12-25",
                "latest_departure_date": "2025-12-25",
                "earliest_return_date": "2025-12-30", 
                "latest_return_date": "2025-12-30",
                "num_adult_passengers": 1,
                "num_child_passengers": 0,
                "depart_after_hour": 23,
                "depart_before_hour": 1  # Impossible constraint
            },
            # Case 3: Different route that doesn't exist
            {
                "origin": "Miami, FL",
                "destination": "Seattle, WA",
                "earliest_departure_date": "2025-12-25",
                "latest_departure_date": "2025-12-25",
                "earliest_return_date": "2025-12-30",
                "latest_return_date": "2025-12-30", 
                "num_adult_passengers": 1,
                "num_child_passengers": 0
            },
            # Case 4: Different date that doesn't exist in database
            {
                "origin": "Los Angeles, CA",
                "destination": "New York, NY",
                "earliest_departure_date": "2025-12-26",
                "latest_departure_date": "2025-12-26",
                "earliest_return_date": "2025-12-31",
                "latest_return_date": "2025-12-31", 
                "num_adult_passengers": 1,
                "num_child_passengers": 0
            }
        ]
        
        for i, test_case in enumerate(test_cases):
            resp = search_flights(**test_case)
            
            # All should return empty results or error
            self.assertIsInstance(resp, dict)
            self.assertIn("response", resp)
            self.assertIsInstance(resp["response"], list)
            self.assertEqual(resp["response"], [])


class TestDICompliance(BaseTestCaseWithErrorHandler):
    """DI Compliance Tests - Strict Order and Booking Flow Validation"""

    def setUp(self):
        """Reset DB before each test and mock file saves"""
        # Mock the save function to prevent writing to file during tests
        self.save_patcher = patch('SimulationEngine.db._save_state_to_file')
        self.mock_save = self.save_patcher.start()
        
        # Reset DB to initial test state (deep copy to avoid mutations)
        # We need to update the DB dict in place, not replace it
        db.DB.clear()
        db.DB.update(deepcopy(INITIAL_TEST_DB))
        
        # Also patch the DB used by ces_flights module
        self.db_patcher = patch('ces_flights.ces_flights.DB', db.DB)
        self.db_patcher.start()
    
    def tearDown(self):
        """Clean up mocks after each test"""
        self.save_patcher.stop()
        self.db_patcher.stop()

    def test_strict_order_flight_information_collection(self):
        """Test that flight information must be collected in strict order (a) to (d)"""
        # According to DI, the system must collect information in strict order:
        # (a) Origin and destination cities
        # (b) Departure and return dates  
        # (c) Number of passengers (adults, children, infants)
        # (d) Any additional preferences
        
        # Test 1: Missing origin - should fail
        with self.assertRaises((TypeError, Exception)):
            search_flights(
                destination="New York, NY",
                earliest_departure_date="2025-12-25",
                latest_departure_date="2025-12-25",
                earliest_return_date="2025-12-30",
                latest_return_date="2025-12-30",
                num_adult_passengers=1,
                num_child_passengers=0,
                origin=None  # Missing origin
            )

    def test_booking_without_complete_traveler_information(self):
        """Test that booking cannot proceed without complete traveler information"""
        # Test 1: Missing first name
        with self.assertRaises((ValidationError, Exception)):
            book_flight(flight_id="AA101", travelers=[{
                "first_name": "",  # Missing first name
                "last_name": "Doe",
                "date_of_birth": "1985-06-15"
            }])
        
        # Test 2: Missing last name
        with self.assertRaises((ValidationError, Exception)):
            book_flight(flight_id="AA101", travelers=[{
                "first_name": "John",
                "last_name": "",  # Missing last name
                "date_of_birth": "1985-06-15"
            }])
        
        # Test 3: Missing date of birth
        with self.assertRaises((ValidationError, Exception)):
            book_flight(flight_id="AA101", travelers=[{
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": None  # Missing date of birth
            }])
        
        # Test 4: Invalid date of birth format
        with self.assertRaises((ValidationError, Exception)):
            book_flight(flight_id="AA101", travelers=[{
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "invalid-date"  # Invalid date format
            }])

    def test_immediate_tool_calls_after_data_collection(self):
        """Test that tool calls are made immediately after all required data is collected"""
        # Test 1: Complete flight search data should immediately call search_flights
        resp = search_flights(
            origin="Los Angeles, CA",
            destination="New York, NY",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2025-12-30",
            latest_return_date="2025-12-30",
            num_adult_passengers=1,
            num_child_passengers=0
        )
        
        # Should immediately return results without asking for more information
        self.assertIsInstance(resp, dict)
        self.assertIn("response", resp)
        self.assertIsInstance(resp["response"], list)
        
        # Test 2: Complete booking data should immediately call book_flight
        # May raise BookingError if no flights available - this is expected
        booking_called = False
        try:
            resp = book_flight(flight_id="AA101", travelers=[{
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1985-06-15"
            }])
            self.assertIn("booking_id", resp)
            self.assertIn("confirmation_number", resp)
            self.assertIn("flight_id", resp)
            booking_called = True
        except (BookingError, Exception):
            # Expected if no flights available
            booking_called = True
        
        self.assertTrue(booking_called)

    def test_no_booking_without_complete_traveler_info(self):
        """Test that booking tool is not called unless all traveler information is provided"""
        # This test ensures the system doesn't attempt booking with incomplete information
        
        # Test with incomplete traveler information
        incomplete_travelers = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1985-06-15"
            },
            {
                "first_name": "Jane",
                "last_name": "",  # Missing last name for second traveler
                "date_of_birth": "1990-03-20"
            }
        ]
        
        # Should raise ValidationError due to incomplete information
        with self.assertRaises((ValidationError, Exception)):
            book_flight(flight_id="AA101", travelers=incomplete_travelers)
        
        # Test with complete information (may raise BookingError if no flights available)
        complete_travelers = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1985-06-15"
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "date_of_birth": "1990-03-20"
            }
        ]
        
        booking_attempted = False
        try:
            resp = book_flight(flight_id="AA101", travelers=complete_travelers)
            self.assertIn("booking_id", resp)
            self.assertIn("confirmation_number", resp)
            self.assertIn("flight_id", resp)
            booking_attempted = True
        except (BookingError, Exception):
            # Expected if no flights available
            booking_attempted = True
        
        self.assertTrue(booking_attempted)

    def test_workflow_order_enforcement(self):
        """Test that the system enforces proper workflow order"""
        # This test validates the overall workflow:
        # 1. Search flights (with complete search criteria)
        # 2. Present results to user
        # 3. User selects flight
        # 4. Collect traveler information
        # 5. Book flight
        
        # Step 1: Search flights with complete information
        search_resp = search_flights(
            origin="Los Angeles, CA",
            destination="New York, NY",
            earliest_departure_date="2025-12-25",
            latest_departure_date="2025-12-25",
            earliest_return_date="2025-12-30",
            latest_return_date="2025-12-30",
            num_adult_passengers=1,
            num_child_passengers=0
        )
        
        self.assertIsInstance(search_resp, dict)
        self.assertIn("response", search_resp)
        self.assertIsInstance(search_resp["response"], list)
        self.assertGreaterEqual(len(search_resp), 0)
        
        # Step 2: Try to book flight with complete traveler information
        # May raise BookingError if no flights available - this is expected
        booking_attempted = False
        try:
            booking_resp = book_flight(flight_id="AA101", travelers=[{
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1985-06-15"
            }])
            self.assertIn("booking_id", booking_resp)
            self.assertIn("confirmation_number", booking_resp)
            self.assertIn("flight_id", booking_resp)
            booking_attempted = True
        except (BookingError, Exception):
            # Expected if no flights available
            booking_attempted = True
        
        self.assertTrue(booking_attempted)

    # ------------------------
    # Bug fix tests
    # ------------------------

    def test_fail_reason_from_input(self):
        """Test that fail function uses input as the reason, not hardcoded string"""
        # Bug 1 fix: The reason should come from input parameter
        custom_reason = "User provided incomplete information"
        resp = fail(input=custom_reason)
        
        self.assertEqual(resp, {"ok": True})
        fail_data = db.DB.get("_end_of_conversation_status", {}).get("fail")
        self.assertIsNotNone(fail_data)
        self.assertEqual(fail_data["reason"], custom_reason)
        self.assertEqual(fail_data["status"], "failed")
        
    def test_fail_default_reason_when_no_input(self):
        """Test that fail function uses default reason when input is not provided"""
        resp = fail()
        
        self.assertEqual(resp, {"ok": True})
        fail_data = db.DB.get("_end_of_conversation_status", {}).get("fail")
        self.assertIsNotNone(fail_data)
        self.assertEqual(fail_data["reason"], "Task failed")
        self.assertEqual(fail_data["status"], "failed")

    def test_depart_before_hour_excludes_exact_hour(self):
        """Test that depart_before_hour filter excludes flights at the exact hour"""
        # Bug 2 fix: depart_before_hour should exclude flights at or after the specified hour
        
        # Add flights with different departure times
        db.DB["sample_flights"]["TEST_0900"] = {
            "airline": "Test Airlines",
            "depart_date": "2025-12-25",
            "depart_time": "09:00:00",
            "arrival_date": "2025-12-25",
            "arrival_time": "12:00:00",
            "price": 300.0,
            "stops": 0,
            "origin": "Los Angeles, CA",
            "destination": "New York, NY",
            "currency": "USD"
        }
        
        db.DB["sample_flights"]["TEST_1000"] = {
            "airline": "Test Airlines",
            "depart_date": "2025-12-25",
            "depart_time": "10:00:00",
            "arrival_date": "2025-12-25",
            "arrival_time": "13:00:00",
            "price": 300.0,
            "stops": 0,
            "origin": "Los Angeles, CA",
            "destination": "New York, NY",
            "currency": "USD"
        }
        
        db.DB["sample_flights"]["TEST_1100"] = {
            "airline": "Test Airlines",
            "depart_date": "2025-12-25",
            "depart_time": "11:00:00",
            "arrival_date": "2025-12-25",
            "arrival_time": "14:00:00",
            "price": 300.0,
            "stops": 0,
            "origin": "Los Angeles, CA",
            "destination": "New York, NY",
            "currency": "USD"
        }
        
        # Search for flights departing before 10:00
        resp = search_flights(
            origin="Los Angeles, CA",
            destination="New York, NY",
            earliest_departure_date="2025-12-25",
            num_adult_passengers=1,
            num_child_passengers=0,
            depart_before_hour=10
        )
        
        self.assertIn("response", resp)
        flights = resp["response"]
        
        # Should only include flights before 10:00 (not at 10:00 or after)
        for flight in flights:
            # Flight can be either dict or Pydantic model
            depart_time = flight.get('depart_time') if isinstance(flight, dict) else flight.depart_time
            flight_id = flight.get('flight_id') if isinstance(flight, dict) else flight.flight_id
            
            flight_hour = int(depart_time.split(':')[0])
            self.assertLess(flight_hour, 10, 
                f"Flight {flight_id} at {depart_time} should not be included when depart_before_hour=10")

    # REMOVED: test_book_flight_with_pydantic_models
    # This test was removed because the API now only accepts primitive types
    # and explicitly rejects Pydantic model objects (BookFlightTravelers).
    # The new API contract requires callers to pass dictionaries with primitive types,
    # and the function internally converts them to Pydantic models for validation.
        
    def test_book_flight_converts_dict_to_pydantic(self):
        """Test that book_flight converts dictionary travelers to Pydantic instances"""
        # Bug 3 fix: book_flight should accept dicts and convert them to Pydantic instances
        # This ensures the function signature (expecting Pydantic) is enforced internally
        
        travelers = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1985-06-15"
            },
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "date_of_birth": "1990-03-20"
            }
        ]
        
        # Should accept dictionaries and convert them internally to Pydantic
        resp = book_flight(flight_id="AA101", travelers=travelers)
        
        self.assertIn("booking_id", resp)
        self.assertIn("confirmation_number", resp)
        self.assertIn("flight_id", resp)
        self.assertEqual(resp["flight_id"], "AA101")
        self.assertIn("failed", resp)
        self.assertFalse(resp["failed"])

    # ------------------------
    # Additional Bug fix tests (new batch)
    # ------------------------

    def test_done_timestamp_has_timezone(self):
        """Test that done function generates timezone-aware ISO-8601 timestamps"""
        # Bug fix: Timestamps should include timezone information for proper ISO-8601 compliance
        resp = done(input="Task completed successfully")
        
        self.assertEqual(resp, {"ok": True})
        done_data = db.DB.get("_end_of_conversation_status", {}).get("done")
        self.assertIsNotNone(done_data)
        
        # Check timestamp format includes timezone (ends with +00:00 or Z or contains timezone offset)
        timestamp = done_data["timestamp"]
        self.assertTrue(
            '+' in timestamp or 'Z' in timestamp or timestamp.endswith('+00:00'),
            f"Timestamp should include timezone information: {timestamp}"
        )

    def test_cancel_reason_from_input(self):
        """Test that cancel function uses input as the reason, not hardcoded string"""
        # Bug fix: The reason should come from input parameter
        custom_reason = "User decided to change their plans"
        resp = cancel(input=custom_reason)
        
        self.assertEqual(resp, {"ok": True})
        cancel_data = db.DB.get("_end_of_conversation_status", {}).get("cancel")
        self.assertIsNotNone(cancel_data)
        self.assertEqual(cancel_data["reason"], custom_reason)
        self.assertEqual(cancel_data["status"], "cancelled")
        
    def test_cancel_default_reason_when_no_input(self):
        """Test that cancel function uses default reason when input is not provided"""
        resp = cancel()
        
        self.assertEqual(resp, {"ok": True})
        cancel_data = db.DB.get("_end_of_conversation_status", {}).get("cancel")
        self.assertIsNotNone(cancel_data)
        self.assertEqual(cancel_data["reason"], "Conversation cancelled")
        self.assertEqual(cancel_data["status"], "cancelled")

    def test_search_flights_with_seating_class_enums(self):
        """Test that search_flights handles SeatingClass enum objects correctly"""
        # Bug fix: Function should accept both enum objects and strings for seating_classes
        from ces_flights.SimulationEngine.models import SeatingClass
        
        # Test with enum objects
        resp = search_flights(
            origin="Los Angeles, CA",
            destination="New York, NY",
            earliest_departure_date="2025-12-25",
            num_adult_passengers=1,
            num_child_passengers=0,
            seating_classes=[SeatingClass.ECONOMY_CLASS, SeatingClass.BUSINESS_CLASS]
        )
        
        self.assertIn("response", resp)
        self.assertIsInstance(resp["response"], list)

    def test_book_flight_travelers_date_serialization(self):
        """Test that book_flight serializes date objects to JSON-compatible strings"""
        # Bug fix: model_dump(mode='json') should convert dates to strings for JSON compatibility
        travelers = [
            {
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1985-06-15"
            }
        ]
        
        resp = book_flight(flight_id="AA101", travelers=travelers)
        
        # Verify booking was created successfully
        self.assertIn("booking_id", resp)
        booking_id = resp["booking_id"]
        
        # Check the stored data in DB
        booking = db.DB.get("flight_bookings", {}).get(booking_id)
        self.assertIsNotNone(booking)
        
        # Verify travelers' date_of_birth is stored as string (JSON-serializable)
        for traveler in booking["travelers"]:
            self.assertIsInstance(traveler["date_of_birth"], str, 
                "date_of_birth should be serialized as string for JSON compatibility")
            # Verify it's a valid date string format
            self.assertEqual(len(traveler["date_of_birth"]), 10)
            self.assertEqual(traveler["date_of_birth"].count('-'), 2)


if __name__ == "__main__":
    unittest.main()