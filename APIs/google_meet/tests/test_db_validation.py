import unittest
from .google_meet_base_exception import GoogleMeetBaseTestCase
from ..SimulationEngine.models import GoogleMeetDB
from ..SimulationEngine.db import DB

class TestDatabaseValidation(GoogleMeetBaseTestCase):
    """
    Test suite for validating the sample database against Pydantic models.
    """

    def test_initial_db_state_validation(self):
        """
        Test that the initial database state loaded in the base case
        conforms to the GoogleMeetDB model. This test implicitly runs
        due to the setUpClass logic in the base case.
        """
        try:
            GoogleMeetDB.model_validate(self._initial_db_state)
        except Exception as e:
            self.fail(f"Initial DB state validation failed in base class: {e}")

    def test_db_module_harmony(self):
        """
        Test that the database used by the db module is in harmony with the sample DB
        after setup.
        """
        try:
            GoogleMeetDB.model_validate(DB)
        except Exception as e:
            self.fail(f"DB module data structure validation failed after setUp: {e}")

if __name__ == '__main__':
    unittest.main()