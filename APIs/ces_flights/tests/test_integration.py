import pytest
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import search_flights, book_flight, done
from ..SimulationEngine import models
from ..SimulationEngine import db

class TestCesFlightsIntegration(BaseTestCaseWithErrorHandler):
    """
    Integration test suite for the CES Flights service.
    This test covers a complete user workflow: searching for flights,
    refining the search, booking a selected flight, and completing the conversation.
    """

    def setUp(self):
        """
        Set up the test environment before each test case.
        This method initializes an in-memory database with sample flight data
        required for the integration test workflow.
        """
        super().setUp()
        # Create an empty DB with keys based on the provided DB schema.
        db.DB = {
            "flight_searches": {},
            "flight_bookings": {},
            "sample_flights": {},
            "_end_of_conversation_status": {},
            "conversation_states": {},
            "retry_counters": {}
        }
        
        # Patch the DB used by ces_flights module
        self.db_patcher = patch('ces_flights.ces_flights.DB', db.DB)
        self.db_patcher.start()

        # Populate the database with sample flight data for the test scenario.
        # This data is designed to test filtering capabilities.
        db.DB["sample_flights"] = {
            "AA101": {
                "airline": "American Airlines",
                "depart_date": "2025-01-15",
                "depart_time": "10:00:00",
                "return_date": "2025-01-20",
                "return_time": "15:00:00",
                "price": 550.0,
                "stops": 0,
                "origin": "Los Angeles, CA",
                "destination": "New York, NY"
            },
            "DL202": {
                "airline": "Delta",
                "depart_date": "2025-01-15",
                "depart_time": "12:00:00",
                "return_date": "2025-01-20",
                "return_time": "17:00:00",
                "price": 600.0,
                "stops": 1,
                "origin": "Los Angeles, CA",
                "destination": "New York, NY"
            },
            "UA303": {
                "airline": "United Airlines",
                "depart_date": "2025-01-15",
                "depart_time": "14:00:00",
                "return_date": "2025-01-20",
                "return_time": "19:00:00",
                "price": 580.0,
                "stops": 0,
                "origin": "Los Angeles, CA",
                "destination": "New York, NY"
            }
        }
    
    def tearDown(self):
        """Clean up mocks after each test"""
        if hasattr(self, 'db_patcher'):
            self.db_patcher.stop()

    def test_search_refine_book_workflow(self):
        """
        Tests the complete workflow: search -> search (refine) -> search (refine) -> book -> done.
        """
        # Step 1: Initial flight search
        search_params_1 = {
            "origin": "Los Angeles, CA",
            "destination": "New York, NY",
            "earliest_departure_date": "2025-01-15",
            "latest_departure_date": "2025-01-15",
            "earliest_return_date": "2025-01-20",
            "latest_return_date": "2025-01-20",
            "num_adult_passengers": 1,
            "num_child_passengers": 0
        }
        search_response_1 = search_flights(**search_params_1)
        
        self.assertIsNotNone(search_response_1, "First search response should not be None.")
        self.assertIsInstance(search_response_1, dict, "First search response should be a dict.")
        self.assertIn("response", search_response_1, "First search response should have 'response' key.")
        self.assertIsInstance(search_response_1["response"], list, "First search results should be a list.")
        self.assertIn("pagination", search_response_1, "First search response should have 'pagination' key.")
        self.assertEqual(len(search_response_1["response"]), 3, "Initial search should find all 3 sample flights.")

        # Step 2: Refine search to non-stop flights only
        search_params_2 = search_params_1.copy()
        search_params_2["max_stops"] = 0
        search_response_2 = search_flights(**search_params_2)

        self.assertIsNotNone(search_response_2, "Second search response should not be None.")
        self.assertIsInstance(search_response_2, dict, "Second search response should be a dict.")
        self.assertIn("response", search_response_2, "Second search response should have 'response' key.")
        self.assertIsInstance(search_response_2["response"], list, "Second search results should be a list.")
        self.assertIn("pagination", search_response_2, "Second search response should have 'pagination' key.")
        self.assertEqual(len(search_response_2["response"]), 2, "Refined search should find 2 non-stop flights.")
        
        # Verify that the flight with stops (DL202) is filtered out
        results_str_2 = "".join(str(r) for r in search_response_2["response"])
        self.assertIn("AA101", results_str_2, "Non-stop flight AA101 should be in the results.")
        self.assertIn("UA303", results_str_2, "Non-stop flight UA303 should be in the results.")
        self.assertNotIn("DL202", results_str_2, "Flight DL202 with 1 stop should be filtered out.")

        # Step 3: Refine search further to a specific airline
        search_params_3 = search_params_2.copy()
        search_params_3["include_airlines"] = ["American Airlines"]
        search_response_3 = search_flights(**search_params_3)

        self.assertIsNotNone(search_response_3, "Third search response should not be None.")
        self.assertIsInstance(search_response_3, dict, "Third search response should be a dict.")
        self.assertIn("response", search_response_3, "Third search response should have 'response' key.")
        self.assertIsInstance(search_response_3["response"], list, "Third search results should be a list.")
        self.assertIn("pagination", search_response_3, "Third search response should have 'pagination' key.")
        self.assertEqual(len(search_response_3["response"]), 1, "Final refined search should find only 1 flight.")
        
        # Verify that only the American Airlines flight (AA101) remains
        self.assertEqual(search_response_3["response"][0]["flight_id"], "AA101", "Flight AA101 should be the only result.")
        self.assertEqual(search_response_3["response"][0]["airline"], "American Airlines", "The airline should be American Airlines.")

        # Step 4: Book the selected flight
        traveler_info = [{
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01"
        }]
        
        booking_response = book_flight(flight_id="AA101", travelers=traveler_info)

        self.assertIsNotNone(booking_response, "Booking response should not be None.")
        self.assertIsInstance(booking_response, dict, "Booking response should be a dictionary.")
        self.assertIn("booking_id", booking_response, "Booking response should contain 'booking_id'.")
        self.assertIn("confirmation_number", booking_response, "Booking response should contain 'confirmation_number'.")
        self.assertIn("flight_id", booking_response, "Booking response should contain 'flight_id'.")
        self.assertEqual(booking_response["flight_id"], "AA101", "Flight ID should match the booked flight.")
        # Check new "failed" field
        self.assertIn("failed", booking_response, "Booking response should contain 'failed' field.")
        self.assertFalse(booking_response["failed"], "Booking should not be failed for a confirmed booking.")
        # Check confirmation number format (6-character hex string)
        self.assertEqual(len(booking_response["confirmation_number"]), 6, "Confirmation number should be 6 characters.")
        self.assertTrue(all(c in '0123456789ABCDEF' for c in booking_response["confirmation_number"]), 
                       "Confirmation number should be hexadecimal.")
        
        # Step 5: End the conversation successfully
        done_response = done(input="Flight booking process completed successfully.")

        self.assertIsNotNone(done_response, "Done response should not be None.")
        self.assertEqual(done_response, {"ok": True}, "Done function should return {'ok': True}.")

    def test_search_with_currency_conversion(self):
        """Test complete workflow with currency conversion"""
        # Step 1: Search for flights with EUR currency
        search_response_eur = search_flights(
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
        
        self.assertIsInstance(search_response_eur, dict)
        self.assertIn("response", search_response_eur)
        
        # Check all flights have EUR currency
        for flight in search_response_eur["response"]:
            self.assertEqual(flight["currency"], "EUR", 
                           f"Flight {flight.get('flight_id')} should have EUR currency")
            self.assertIsInstance(flight["price"], float)
        
        # Step 2: Search for same flights with JPY currency
        search_response_jpy = search_flights(
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
        
        self.assertIsInstance(search_response_jpy, dict)
        self.assertIn("response", search_response_jpy)
        
        # Check all flights have JPY currency
        for flight in search_response_jpy["response"]:
            self.assertEqual(flight["currency"], "JPY",
                           f"Flight {flight.get('flight_id')} should have JPY currency")
            self.assertIsInstance(flight["price"], float)
        
        # Step 3: Verify prices are correctly converted
        # Same flight should cost more in JPY than EUR (since JPY rate is higher)
        if len(search_response_eur["response"]) > 0 and len(search_response_jpy["response"]) > 0:
            # Find a matching flight in both responses
            eur_flight = search_response_eur["response"][0]
            jpy_flight = search_response_jpy["response"][0]
            
            # JPY price should be much higher than EUR price for the same base USD price
            self.assertGreater(jpy_flight["price"], eur_flight["price"],
                             "JPY price should be higher than EUR price for the same flight")
