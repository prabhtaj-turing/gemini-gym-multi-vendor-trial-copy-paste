import unittest
import copy
import uuid
from datetime import datetime, timezone
from ..SimulationEngine import models
from ..SimulationEngine.utils import create_or_update_trip
from .. import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestCreateOrUpdateTripUtil(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Set up a clean DB state before each test."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        
        # Initialize all required collections for the DB model
        DB.update({
            'users': {},
            'locations': {},
            'trips': {},
            'bookings': {},
            'notifications': {},
            'user_by_external_id': {},
            'booking_by_locator': {},
            'trips_by_user': {},
            'bookings_by_trip': {},
        })
        
        # Create a test user
        self.user_id = str(uuid.uuid4())
        DB['users'][self.user_id] = {
            'id': self.user_id, 
            'user_name': 'testuser', 
            'given_name': 'Test', 
            'family_name': 'User', 
            'email': 'test@example.com', 
            'active': True, 
            'locale': 'en-US', 
            'timezone': 'UTC', 
            'created_at': str(datetime.now(timezone.utc)), 
            'last_modified': str(datetime.now(timezone.utc))
        }
        
        self._validate_db_structure()

    def tearDown(self):
        """Restore the original DB state after each test."""
        DB.clear()
        DB.update(self._original_DB_state)

    def _validate_db_structure(self):
        """Ensure the DB structure is valid before running a test."""
        try:
            models.ConcurAirlineDB(**DB)
        except Exception as e:
            raise AssertionError(f"DB structure validation failed: {str(e)}")

    def _get_basic_trip_input(self, trip_name="Test Trip", locator=None):
        """Returns a basic but valid raw input dictionary for the function."""
        input_data = {
            "TripName": trip_name,
            "StartDateLocal": "2024-08-01",
            "EndDateLocal": "2024-08-05",
            "Bookings": []
        }
        if locator:
            input_data["ItinLocator"] = locator
        return input_data

    def _assert_successful_trip_response(self, response, trip_input, user_id):
        """Asserts that the response and DB state are correct after a successful call."""
        # 1. Validate response structure
        self.assertIsInstance(response, dict)
        self.assertTrue(uuid.UUID(response['TripId']))
        self.assertIn('/api/v3.0/itinerary/trips/', response['TripUri'])
        self.assertEqual(response['TripName'], trip_input['TripName'])
        self.assertEqual(response['StartDateLocal'], trip_input['StartDateLocal'])
        self.assertEqual(response['EndDateLocal'], trip_input['EndDateLocal'])
        self.assertIsInstance(response['DateModifiedUtc'], str)
        self.assertIsInstance(response['Bookings'], list)

        # 2. Validate DB state for the trip
        trip_id = response['TripId']
        db_trip = DB['trips'].get(trip_id)
        self.assertIsNotNone(db_trip)
        self.assertEqual(db_trip['user_id'], user_id)
        self.assertEqual(db_trip['trip_name'], trip_input['TripName'])
        self.assertIn(trip_id, DB['trips_by_user'][user_id])
        
        # 3. Validate bookings if they exist in the database
        self.assertEqual(len(response['Bookings']), len(db_trip['booking_ids']))
        for booking_id in db_trip['booking_ids']:
            self.assertTrue(uuid.UUID(booking_id))
            db_booking = DB['bookings'].get(booking_id)
            self.assertIsNotNone(db_booking)
            self.assertEqual(db_booking['trip_id'], trip_id)
            self.assertIn(booking_id, DB.get('bookings_by_trip', {}).get(trip_id, []))

    def test_create_new_trip_with_one_booking_success(self):
        """Test creating a new trip with a single booking and car segment."""
        trip_input = self._get_basic_trip_input("Trip with Car")
        trip_input['Bookings'] = [
            {
                "RecordLocator": "CARBOOK1",
                "BookingSource": "TestCarCo",
                "Passengers": [{"NameFirst": "John", "NameLast": "Doe"}],
                "Segments": {
                    "Car": [{
                        'Vendor': 'CR',
                        'Status': 'CONFIRMED',
                        'StartDateLocal': '2024-08-01T10:00:00',
                        'EndDateLocal': '2024-08-05T18:00:00',
                        'StartLocation': 'LAX',
                        'EndLocation': 'LAX',
                        'TotalRate': 250.00,
                        'Currency': 'USD'
                    }]
                }
            }
        ]

        response = create_or_update_trip(user_id=uuid.UUID(self.user_id), raw_trip_input=trip_input)
        
        # Perform detailed validation
        self._assert_successful_trip_response(response, trip_input, self.user_id)

        # Specific checks for this test
        self.assertEqual(len(response['Bookings']), 1)
        # We can get the booking ID from the DB for more detailed checks
        booking_id = DB['trips'][response['TripId']]['booking_ids'][0]
        db_booking = DB['bookings'].get(booking_id)
        self.assertIsNotNone(db_booking)
        self.assertEqual(len(db_booking['segments']), 1)
        self.assertEqual(db_booking['segments'][0]['type'], 'CAR')

if __name__ == '__main__':
    unittest.main() 