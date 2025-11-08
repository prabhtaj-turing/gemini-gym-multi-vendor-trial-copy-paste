import copy
import json
import os
from pydantic import ValidationError
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler


class LoyaltyAuthBaseTestCase(BaseTestCaseWithErrorHandler):
    """
    Base class for loyalty auth tests with automated DB setup and teardown.
    """
    _initial_db_state: dict = None

    @classmethod
    def setUpClass(cls):
        """
        Loads and validates the initial database state once for all tests in the class.
        """
        if cls._initial_db_state is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'DBs', 'CesLoyaltyAuthDefaultDB.json')
            with open(db_path, 'r') as f:
                db_data = json.load(f)
            
            # Validate the database structure at setup
            try:
                # The database structure validation can be added here if needed
                # For now, we'll just load the data as-is
                pass
            except ValidationError as e:
                raise RuntimeError(f"Failed to validate initial DB state: {e}") from e
            
            cls._initial_db_state = db_data

    def setUp(self):
        """
        Resets the database to the initial state before each test.
        """
        # Reset to the proper database structure
        DB.clear()
        
        # Load the initial state
        for key, value in self._initial_db_state.items():
            DB[key] = copy.deepcopy(value)

    def tearDown(self):
        """
        Clears the database after each test to ensure isolation.
        """
        DB.clear()
