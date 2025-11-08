import unittest
from .airline_base_exception import AirlineBaseTestCase
from ..SimulationEngine.models import AirlineDB
from ..SimulationEngine.db import DB
import os
from ..SimulationEngine.db import save_state, load_state, reset_db
import json

class TestStateValidation(AirlineBaseTestCase):
    """
    Test suite for validating the state of the database.
    """

    def setUp(self):
        super().setUp()
        self.db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'DBs', 'AirlineDefaultDB.json')
        reset_db()
        load_state(self.db_path)
        self.DB = DB.copy()
        self.temp_db_file = self.db_path + ".temp"

        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)
        else:
            temp_db = {
                "flights": [],
                "reservations": [],
                "users": []
            }
            with open(self.temp_db_file, 'w') as f:
                json.dump(temp_db, f)

    def tearDown(self):
        super().tearDown()
        reset_db()
        if os.path.exists(self.temp_db_file):
            os.remove(self.temp_db_file)

    def test_load_db_from_file(self):
        """
        Test that the database can be loaded from a file.
        """
        load_state(self.temp_db_file)
        self.assertEqual(len(DB['flights']), 0)
        self.assertEqual(len(DB['reservations']), 0)

    def test_save_db_to_file(self):
        """
        Test that the database can be saved to a file.
        """
        load_state(self.temp_db_file)
        DB["flights"] = [
            {
                "flight_number": "HAT001",
                "origin": "PHL",
                "destination": "LGA",
                "date": "2024-05-16",
                "time": "10:00",
                "price": 100
            }
        ]
        save_state(self.temp_db_file)
        load_state(self.temp_db_file)
        self.assertEqual(len(DB['flights']), 1)
        self.assertEqual(len(DB['reservations']), 0)


class TestDatabaseValidation(AirlineBaseTestCase):
    """
    Test suite for validating the sample database against Pydantic models.
    """

    def test_initial_db_state_validation(self):
        """
        Test that the initial database state loaded in the base case
        conforms to the AirlineDB model. This test implicitly runs
        due to the setUpClass logic in the base case.
        """
        try:
            AirlineDB.model_validate(self._initial_db_state)
        except Exception as e:
            self.fail(f"Initial DB state validation failed in base class: {e}")

    def test_db_module_harmony(self):
        """
        Test that the database used by the db module is in harmony with the sample DB
        after setup.
        """
        try:
            AirlineDB.model_validate(DB)
        except Exception as e:
            self.fail(f"DB module data structure validation failed after setUp: {e}")

    

if __name__ == '__main__':
    unittest.main()