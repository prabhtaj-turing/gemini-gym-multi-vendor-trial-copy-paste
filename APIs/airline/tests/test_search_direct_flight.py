"""
Test suite for search_direct_flight tool.
"""
import unittest
from .airline_base_exception import AirlineBaseTestCase
from .. import search_direct_flight
from ..SimulationEngine.custom_errors import ValidationError as CustomValidationError

class TestSearchDirectFlight(AirlineBaseTestCase):

    def test_search_direct_flight_success(self):
        """Test a successful search for direct flights."""
        flights = search_direct_flight(origin="PHL", destination="LGA", date="2024-05-16")
        self.assertIsInstance(flights, list)
        self.assertGreater(len(flights), 0)
        flight_numbers = [f["flight_number"] for f in flights]
        self.assertIn("HAT001", flight_numbers)
        self.assertIn("prices", flights[0])
        self.assertIn("available_seats", flights[0])

    def test_search_direct_flight_no_results(self):
        """Test a search that should return no flights."""
        flights = search_direct_flight(origin="PHL", destination="LGA", date="2024-06-01")
        self.assertIsInstance(flights, list)
        self.assertEqual(len(flights), 0)

    def test_search_direct_flight_invalid_origin(self):
        """Test search with an empty origin."""
        self.assert_error_behavior(
            search_direct_flight,
            CustomValidationError,
            "Origin must be a non-empty string.",
            None,
            origin="",
            destination="LGA",
            date="2024-05-16"
        )

    def test_search_direct_flight_invalid_destination(self):
        """Test search with an empty destination."""
        self.assert_error_behavior(
            search_direct_flight,
            CustomValidationError,
            "Destination must be a non-empty string.",
            None,
            origin="PHL",
            destination="",
            date="2024-05-16"
        )

    def test_search_direct_flight_invalid_date(self):
        """Test search with an empty date."""
        self.assert_error_behavior(
            search_direct_flight,
            CustomValidationError,
            "Date must be a non-empty string.",
            None,
            origin="PHL",
            destination="LGA",
            date=""
        )

    def test_search_direct_flight_invalid_date_format(self):
        """Test search with an invalid date format."""
        self.assert_error_behavior(
            search_direct_flight,
            CustomValidationError,
            "Date must be in YYYY-MM-DD format.",
            None,
            origin="PHL",
            destination="LGA",
            date="2024-05-16-16"
        )

    def test_search_direct_flight_invalid_date_range(self):
        """Test search with an invalid date range."""
        self.assert_error_behavior(
            search_direct_flight,
            CustomValidationError,
            "Date must be a valid calendar date in YYYY-MM-DD format.",
            None,
            origin="PHL",
            destination="LGA",
            date="2024-09-32"
        )

    def test_search_direct_flight_invalid_origin_length(self):
        """Test search with an invalid origin length."""
        self.assert_error_behavior(
            search_direct_flight,
            CustomValidationError,
            "Origin and destination must be three letters.",
            None,
            origin="PHL",
            destination="L",
            date="2024-05-26"
        )

        
if __name__ == '__main__':
    unittest.main()