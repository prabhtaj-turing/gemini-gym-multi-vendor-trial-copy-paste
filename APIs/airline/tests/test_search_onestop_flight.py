"""
Test suite for search_onestop_flight tool.
"""
import unittest
from .airline_base_exception import AirlineBaseTestCase
from .. import search_onestop_flight
from ..SimulationEngine.custom_errors import ValidationError as CustomValidationError

class TestSearchOnestopFlight(AirlineBaseTestCase):

    def test_search_onestop_flight_success(self):
        """Test a successful search for one-stop flights."""
        flights = search_onestop_flight(origin="LGA", destination="SFO", date="2024-05-26")
        self.assertIsInstance(flights, list)
        self.assertGreater(len(flights), 0)
        self.assertIsInstance(flights[0], list)
        self.assertEqual(len(flights[0]), 2)
        self.assertIn("flight_number", flights[0][0])
        self.assertIn("flight_number", flights[0][1]) 

    def test_search_onestop_flight_no_results(self):
        """Test a search that should return no one-stop flights."""
        flights = search_onestop_flight(origin="SFO", destination="JFK", date="2024-06-01")
        self.assertIsInstance(flights, list)
        self.assertEqual(len(flights), 0)

    def test_search_onestop_flight_invalid_origin(self):
        """Test search with an empty origin."""
        self.assert_error_behavior(
            search_onestop_flight,
            CustomValidationError,
            "Origin must be a non-empty string.",
            None,
            origin="",
            destination="SFO",
            date="2024-05-26"
        )

    def test_search_onestop_flight_invalid_destination(self):
        """Test search with an empty destination."""
        self.assert_error_behavior(
            search_onestop_flight,
            CustomValidationError,
            "Destination must be a non-empty string.",
            None,
            origin="LGA",
            destination="",
            date="2024-05-26"
        )

    def test_search_onestop_flight_invalid_date(self):
        """Test search with an empty date."""
        self.assert_error_behavior(
            search_onestop_flight,
            CustomValidationError,
            "Date must be a non-empty string.",
            None,
            origin="LGA",
            destination="SFO",
            date=""
        )

    def test_search_onestop_flight_invalid_date_format(self):
        """Test search with an invalid date format."""
        self.assert_error_behavior(
            search_onestop_flight,
            CustomValidationError,
            "Date must be in YYYY-MM-DD format.",
            None,   
            origin="LGA",
            destination="SFO",
            date="2024-05-26-16"
        )

    def test_search_onestop_flight_invalid_date_range(self):
        """Test search with an invalid date range."""
        self.assert_error_behavior(
            search_onestop_flight,
            CustomValidationError,
            "Date must be a valid calendar date in YYYY-MM-DD format.",
            None,
            origin="LGA",
            destination="SFO",
            date="2024-09-32"
        )
    
    def test_search_onestop_flight_invalid_origin_length(self):
        """Test search with an invalid origin length."""
        self.assert_error_behavior(
            search_onestop_flight,
            CustomValidationError,
            "Origin and destination must be three letters.",
            None,
            origin="LGA",
            destination="LA",
            date="2024-05-26"
        )


if __name__ == '__main__':
    unittest.main()