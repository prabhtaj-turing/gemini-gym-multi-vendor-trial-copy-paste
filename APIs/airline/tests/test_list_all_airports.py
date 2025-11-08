"""
Test suite for list_all_airports tool.
"""
import unittest
from .airline_base_exception import AirlineBaseTestCase
from .. import list_all_airports
from ..SimulationEngine.db import DB

class TestListAllAirports(AirlineBaseTestCase):

    def test_list_all_airports_returns_dict(self):
        """Test that list_all_airports returns a dictionary."""
        airports = list_all_airports()
        self.assertIsInstance(airports, dict)

    def test_list_all_airports_is_not_empty(self):
        """Test that the returned airport list is not empty with default DB."""
        airports = list_all_airports()
        self.assertGreater(len(airports), 0)

    def test_list_all_airports_contains_known_airports(self):
        """Test that the airport list contains expected airports from the DB."""
        airports = list_all_airports()
        # These airports are known to be in the AirlineDefaultDB.json
        self.assertIn("SFO", airports)
        self.assertEqual(airports["SFO"], "San Francisco")
        self.assertIn("JFK", airports)
        self.assertEqual(airports["JFK"], "New York")
        self.assertIn("LAX", airports)
        self.assertEqual(airports["LAX"], "Los Angeles")

    def test_list_all_airports_with_empty_flights(self):
        """Test that list_all_airports returns an empty dict if there are no flights."""
        DB["flights"] = {}
        airports = list_all_airports()
        self.assertIsInstance(airports, dict)
        self.assertEqual(len(airports), 0)
        
    def test_list_all_airports_with_single_flight(self):
        """Test that list_all_airports correctly processes a single flight."""
        DB["flights"] = {
            "TEST001": {
                "flight_number": "TEST001",
                "origin": "SFO",
                "destination": "JFK",
                "scheduled_departure_time_est": "06:00:00",
                "scheduled_arrival_time_est": "09:00:00",
                "dates": {}
            }
        }
        airports = list_all_airports()
        self.assertEqual(len(airports), 2)
        self.assertIn("SFO", airports)
        self.assertIn("JFK", airports)

if __name__ == '__main__':
    unittest.main()
