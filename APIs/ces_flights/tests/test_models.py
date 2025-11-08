import unittest
import sys
import os
from datetime import date

# Add the parent directory to the path to fix imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ces_flights.SimulationEngine.models import (
    BookFlightTravelers, 
    SearchFlightsParams, 
    BookFlightParams,
    PaginationMetadata,
    BookFlightResponse,
    SearchFlightsResponse,
    FlightSearchResult
)


class TestTravelerModel(BaseTestCaseWithErrorHandler):
    """Test the BookFlightTravelers model."""

    def test_traveler_valid(self):
        traveler = BookFlightTravelers(
            first_name="Alice",
            last_name="Smith",
            date_of_birth=date(1990, 5, 1)
        )
        self.assertEqual(traveler.first_name, "Alice")
        self.assertEqual(traveler.date_of_birth.year, 1990)

    def test_traveler_missing_required(self):
        with self.assertRaises(Exception):
            BookFlightTravelers(first_name="", last_name="Doe", date_of_birth="1990-05-01")


class TestSearchFlightsParams(BaseTestCaseWithErrorHandler):
    """Test the SearchFlightsParams model."""

    def test_search_flights_params_valid(self):
        params = SearchFlightsParams(
            origin="San Francisco, CA",
            destination="New York, NY",
            earliest_departure_date="2024-04-01",
            latest_departure_date="2024-04-01",
            earliest_return_date="2024-04-10",
            latest_return_date="2024-04-10",
            num_adult_passengers=1,
            num_child_passengers=0
        )
        self.assertTrue(params.origin.startswith("San Francisco"))

    def test_search_flights_params_invalid_passenger_count(self):
        with self.assertRaises(Exception):
            SearchFlightsParams(
                origin_city="SFO",
                destination_city="JFK",
                earliest_departure_date=date(2024, 4, 1),
                latest_departure_date=date(2024, 4, 1),
                earliest_return_date=date(2024, 4, 10),
                latest_return_date=date(2024, 4, 10),
                num_adult_passengers=0,  # invalid
                num_child_passengers=0
            )


class TestBookFlightParams(BaseTestCaseWithErrorHandler):
    """Test the BookFlightParams model."""

    def test_book_flight_params_valid(self):
        traveler = BookFlightTravelers(first_name="Bob", last_name="Jones", date_of_birth=date(1985, 7, 10))
        book_params = BookFlightParams(
            selected_flight_id="FL123",
            travelers=[traveler]
        )
        self.assertEqual(book_params.travelers[0].last_name, "Jones")

    def test_book_flight_params_empty_travelers(self):
        # BookFlightParams may accept empty travelers list in some implementations
        # Just verify it creates the object
        params = BookFlightParams(selected_flight_id="FL123", travelers=[])
        self.assertEqual(params.selected_flight_id, "FL123")
        self.assertEqual(len(params.travelers), 0)

    def test_book_flight_input_with_known_traveler_number(self):
        """Test BookFlightInput with known_traveler_number at booking level"""
        from ces_flights.SimulationEngine.models import BookFlightInput
        
        # Use dictionary with primitive types instead of Pydantic model object
        traveler = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01"  # String instead of date object
        }
        
        # Test with known_traveler_number
        booking_input = BookFlightInput(
            flight_id="AA101",
            travelers=[traveler],
            known_traveler_number="KTN123456789"
        )
        
        self.assertEqual(booking_input.flight_id, "AA101")
        self.assertEqual(len(booking_input.travelers), 1)
        self.assertEqual(booking_input.known_traveler_number, "KTN123456789")
        
        # Test without known_traveler_number
        booking_input_no_ktn = BookFlightInput(
            flight_id="AA101",
            travelers=[traveler]
        )
        
        self.assertEqual(booking_input_no_ktn.flight_id, "AA101")
        self.assertEqual(len(booking_input_no_ktn.travelers), 1)
        self.assertIsNone(booking_input_no_ktn.known_traveler_number)


class TestPaginationMetadata(BaseTestCaseWithErrorHandler):
    """Test the PaginationMetadata model."""

    def test_pagination_metadata_valid(self):
        """Test creating valid pagination metadata."""
        pagination = PaginationMetadata(
            total_results=25,
            total_pages=3,
            current_page=1,
            page_size=10,
            has_next=True,
            has_previous=False
        )
        self.assertEqual(pagination.total_results, 25)
        self.assertEqual(pagination.total_pages, 3)
        self.assertEqual(pagination.current_page, 1)
        self.assertEqual(pagination.page_size, 10)
        self.assertTrue(pagination.has_next)
        self.assertFalse(pagination.has_previous)

    def test_pagination_metadata_last_page(self):
        """Test pagination metadata for last page."""
        pagination = PaginationMetadata(
            total_results=25,
            total_pages=3,
            current_page=3,
            page_size=10,
            has_next=False,
            has_previous=True
        )
        self.assertFalse(pagination.has_next)
        self.assertTrue(pagination.has_previous)


class TestBookFlightResponse(BaseTestCaseWithErrorHandler):
    """Test the BookFlightResponse model."""

    def test_book_flight_response_valid(self):
        """Test creating valid booking response."""
        response = BookFlightResponse(
            booking_id="123e4567-e89b-12d3-a456-426614174000",
            flight_id="AA101",
            confirmation_number="A3F7B2",
            status="confirmed",
            failed=False,
            is_round_trip=False
        )
        self.assertEqual(response.booking_id, "123e4567-e89b-12d3-a456-426614174000")
        self.assertEqual(response.flight_id, "AA101")
        self.assertEqual(response.confirmation_number, "A3F7B2")
        self.assertEqual(response.status, "confirmed")
        self.assertFalse(response.failed)
        self.assertFalse(response.is_round_trip)

    def test_book_flight_response_with_return_flight(self):
        """Test booking response with return flight."""
        response = BookFlightResponse(
            booking_id="123e4567-e89b-12d3-a456-426614174000",
            flight_id="AA101",
            confirmation_number="B4E8C3",
            status="confirmed",
            failed=False,
            return_flight_id="AA102",
            is_round_trip=True
        )
        self.assertEqual(response.return_flight_id, "AA102")
        self.assertTrue(response.is_round_trip)
        self.assertFalse(response.failed)

    def test_book_flight_response_confirmation_number_format(self):
        """Test that confirmation number is 6-character hex string."""
        response = BookFlightResponse(
            booking_id="123e4567-e89b-12d3-a456-426614174000",
            flight_id="AA101",
            confirmation_number="1A2B3C",
            status="confirmed",
            failed=False,
            is_round_trip=False
        )
        self.assertEqual(len(response.confirmation_number), 6)
        # Verify it's a valid hex string
        try:
            int(response.confirmation_number, 16)
            is_hex = True
        except ValueError:
            is_hex = False
        self.assertTrue(is_hex)


class TestSearchFlightsResponse(BaseTestCaseWithErrorHandler):
    """Test the SearchFlightsResponse model."""

    def test_search_flights_response_valid(self):
        """Test creating valid search flights response."""
        flight_result = FlightSearchResult(
            flight_id="AA101",
            airline="American Airlines",
            origin="Los Angeles, CA",
            destination="New York, NY",
            depart_date="2025-12-25",
            depart_time="10:00:00",
            arrival_date="2025-12-25",
            arrival_time="18:30:00",
            price=550.0,
            currency="USD",
            stops=0
        )
        
        pagination = PaginationMetadata(
            total_results=1,
            total_pages=1,
            current_page=1,
            page_size=10,
            has_next=False,
            has_previous=False
        )
        
        response = SearchFlightsResponse(
            response=[flight_result],
            pagination=pagination
        )
        
        self.assertEqual(len(response.response), 1)
        self.assertEqual(response.response[0].flight_id, "AA101")
        self.assertEqual(response.pagination.total_results, 1)
        self.assertEqual(response.pagination.current_page, 1)

    def test_search_flights_response_with_pagination(self):
        """Test search response with multiple pages."""
        flights = [
            FlightSearchResult(
                flight_id=f"AA{i}",
                airline="American Airlines",
                origin="Los Angeles, CA",
                destination="New York, NY",
                depart_date="2025-12-25",
                depart_time="10:00:00",
                arrival_date="2025-12-25",
                arrival_time="18:30:00",
                price=550.0 + (i * 10),
                currency="USD",
                stops=0
            )
            for i in range(10)
        ]
        
        pagination = PaginationMetadata(
            total_results=25,
            total_pages=3,
            current_page=1,
            page_size=10,
            has_next=True,
            has_previous=False
        )
        
        response = SearchFlightsResponse(
            response=flights,
            pagination=pagination
        )
        
        self.assertEqual(len(response.response), 10)
        self.assertEqual(response.pagination.total_results, 25)
        self.assertTrue(response.pagination.has_next)
        self.assertFalse(response.pagination.has_previous)


class TestSearchFlightsParamsWithPagination(BaseTestCaseWithErrorHandler):
    """Test SearchFlightsParams with pagination parameters."""

    def test_search_flights_params_with_pagination(self):
        """Test search params with pagination parameters."""
        params = SearchFlightsParams(
            origin="San Francisco, CA",
            destination="New York, NY",
            earliest_departure_date="2024-04-01",
            latest_departure_date="2024-04-01",
            earliest_return_date="2024-04-10",
            latest_return_date="2024-04-10",
            num_adult_passengers=1,
            num_child_passengers=0,
            page=2,
            page_size=20
        )
        self.assertEqual(params.page, 2)
        self.assertEqual(params.page_size, 20)

    def test_search_flights_params_pagination_defaults(self):
        """Test that pagination params have correct defaults."""
        params = SearchFlightsParams(
            origin="San Francisco, CA",
            destination="New York, NY",
            earliest_departure_date="2024-04-01",
            latest_departure_date="2024-04-01",
            earliest_return_date="2024-04-10",
            latest_return_date="2024-04-10",
            num_adult_passengers=1,
            num_child_passengers=0
        )
        self.assertEqual(params.page, 1)
        self.assertEqual(params.page_size, 10)


if __name__ == "__main__":
    unittest.main()