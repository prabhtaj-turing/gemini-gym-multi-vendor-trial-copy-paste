import unittest
from unittest.mock import patch
from ..locations import list_all_airports
from .. import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestListAllAirports(BaseTestCaseWithErrorHandler):

    def test_list_all_airports_success(self):
        """Test successful retrieval of all airports."""
        self.original_db = DB.copy()
        DB.clear()
        DB.update({
            'locations': {
                'airport_1': {'location_type': 'airport', 'name': 'JFK', 'city': 'New York'},
                'airport_2': {'location_type': 'airport', 'name': 'LAX', 'city': 'Los Angeles'},
                'other_location': {'location_type': 'office', 'name': 'Corporate HQ', 'city': 'Seattle'}
            }
        })
        airports = list_all_airports()
        self.assertEqual(len(airports), 2)
        self.assertIn('JFK', airports)
        self.assertEqual(airports['JFK'], 'New York')
        DB.clear()
        DB.update(self.original_db)

    def test_list_all_airports_no_airports(self):
        """Test with no locations of type 'airport'."""
        self.original_db = DB.copy()
        DB.clear()
        DB.update({
            'locations': {
                'office_1': {'location_type': 'office', 'name': 'Downtown Office', 'city': 'Boston'}
            }
        })
        airports = list_all_airports()
        self.assertEqual(len(airports), 0)
        DB.clear()
        DB.update(self.original_db)

    def test_list_all_airports_mixed_data(self):
        """Test with airports missing name or city."""
        self.original_db = DB.copy()
        DB.clear()
        DB.update({
            'locations': {
                'airport_1': {'location_type': 'airport', 'name': 'SFO', 'city': 'San Francisco'},
                'airport_2': {'location_type': 'airport', 'name': None, 'city': 'Chicago'},
                'airport_3': {'location_type': 'airport', 'name': 'MIA', 'city': None}
            }
        })
        airports = list_all_airports()
        self.assertEqual(len(airports), 1)
        self.assertIn('SFO', airports)
        DB.clear()
        DB.update(self.original_db)

    def test_list_all_airports_empty_db(self):
        """Test with an empty locations database."""
        self.original_db = DB.copy()
        DB.clear()
        DB.update({'locations': {}})
        airports = list_all_airports()
        self.assertEqual(len(airports), 0)
        DB.clear()
        DB.update(self.original_db)

if __name__ == '__main__':
    unittest.main() 