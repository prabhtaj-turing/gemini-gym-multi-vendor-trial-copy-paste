import copy
import json
import os
from pydantic import ValidationError
from ..SimulationEngine.db import DB
from ..SimulationEngine.db_models import AccountDetails
from common_utils.base_case import BaseTestCaseWithErrorHandler

class AccountManagementBaseTestCase(BaseTestCaseWithErrorHandler):
    """
    Base class for account management tests with automated DB setup and teardown.
    """
    _initial_db_state: dict = None

    @classmethod
    def setUpClass(cls):
        """
        Loads and validates the initial database state once for all tests in the class.
        """
        if cls._initial_db_state is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'DBs', 'CesAccountManagementDefaultDB.json')
            with open(db_path, 'r') as f:
                db_data = json.load(f)
            
            # Note: Added orders for ACC-12345 to test query orders functionality. 
            # This can be removed once the orders are added to the database.
            db_data["accountDetails"]["ACC-12345"]["orders"] = {
                "ORD-789107": {
                    "orderId": "ORD-789107",
                    "status": "Delayed",
                    "orderDate": "2025-05-22 15:00:00 UTC",
                    "accountId": "",
                    "estimatedCompletionDate": "2025-06-10 23:59:59 UTC",
                    "orderType": "NEW_DEVICE",
                    "statusDescription": "Shipment of your device has been delayed due to a stock shortage. We apologize for the inconvenience."
                },
                "ORD-789108": {
                    "orderId": "ORD-789108",
                    "status": "Processing",
                    "orderDate": "2025-05-22 15:00:00 UTC",
                    "accountId": "ACC-12345",
                    "estimatedCompletionDate": "2025-06-10 23:59:59 UTC",
                    "orderType": "CHANGE_PLAN",
                    "statusDescription": "Your plan has been successfully changed to the Basic Talk & Text plan."
                },
                "ORD-789109": {
                    "orderId": "ORD-789109",
                    "status": "Completed",
                    "orderDate": "2025-05-22 15:00:00 UTC",
                    "accountId": "ACC-12345",
                    "estimatedCompletionDate": "2025-06-10 23:59:59 UTC",
                    "orderType": "REMOVE_FEATURE",
                    "statusDescription": "The hotspot feature has been successfully removed from your plan."
                }
            }

            # Validate the database structure at setup
            try:
                # Validate account details if present
                if 'accountDetails' in db_data:
                    for account_id, account in db_data['accountDetails'].items():
                        # The database structure now uses dictionaries directly
                        AccountDetails.model_validate(account)
            except ValidationError as e:
                raise RuntimeError(f"Failed to validate initial DB state: {e}") from e
            
            cls._initial_db_state = db_data

    def setUp(self):
        """
        Resets the database to the initial state before each test.
        """
        # Reset to the proper database structure
        DB.clear()
        DB.update({
            "accountDetails": {},
            "availablePlans": {},
            "use_real_datastore": False,
            "_end_of_conversation_status": {},
        })
        
        for key, value in self._initial_db_state.items():
            DB[key] = copy.deepcopy(value)

    def tearDown(self):
        """
        Clears the database after each test to ensure isolation.
        """
        DB.clear()
