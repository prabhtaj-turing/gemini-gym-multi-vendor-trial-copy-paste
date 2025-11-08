from common_utils.base_case import BaseTestCaseWithErrorHandler
from workday.SimulationEngine import db
from workday import list_contract_awards
import unittest
from workday.SimulationEngine.custom_errors import NotFoundError

class TestListAwards(BaseTestCaseWithErrorHandler):
    """
    Test suite for the ContractAward.list_awards() function.
    """

    def setUp(self):
        """
        Set up a consistent state for the database before each test.
        """
        self.original_db = db.DB
        db.DB = {
            "contracts": {
                "awards": {
                    "AWARD001": {
                        "award_id": 1,
                        "contract_id": 101,
                        "supplier_id": 201,
                        "status": "awarded",
                        "total_value": 50000.0,
                        "currency": "USD"
                    },
                    "AWARD002": {
                        "award_id": 2,
                        "contract_id": 102,
                        "supplier_id": 202,
                        "status": "pending",
                        "total_value": 120000.0,
                        "currency": "EUR"
                    }
                }
            }
        }

    def tearDown(self):
        """
        Restore the original database state after each test.
        """
        db.DB = self.original_db

    def test_list_awards_success(self):
        """
        Tests successful retrieval of all awards.
        """
        result = list_contract_awards()
        
        # Verify that the result is a list
        self.assertIsInstance(result, list, "The function should return a list.")
        
        # Verify the number of awards returned
        self.assertEqual(len(result), 2, "It should return all awards from the database.")
        
        # Verify the content of the awards
        award_ids = {item.get('award_id') for item in result}
        self.assertSetEqual(award_ids, {1, 2}, "The list should contain all expected awards.")

    def test_list_awards_empty(self):
        """
        Tests behavior when no awards are in the database.
        """
        # Set up the specific condition for this test
        db.DB["contracts"]["awards"] = {}
        
        result = list_contract_awards()
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0, "Should return an empty list when no awards exist.")

    def test_list_awards_key_error_missing_awards(self):
        """
        Tests error handling when the 'awards' key is missing.
        """
        # Remove the 'awards' key to trigger the error
        del db.DB["contracts"]["awards"]
        
        expected_message = "Database is missing expected structure: 'awards'. Could not retrieve awards."

        # Use the provided helper to assert the correct exception is raised
        self.assert_error_behavior(
            list_contract_awards,
            NotFoundError,
            expected_message
        )

    def test_list_awards_key_error_missing_contracts(self):
        """
        Tests error handling when the 'contracts' key is missing.
        """
        # Remove the 'contracts' key to trigger the error
        del db.DB["contracts"]
        
        expected_message = "Database is missing expected structure: 'contracts'. Could not retrieve awards."
        
        # Use the provided helper to assert the correct exception is raised
        self.assert_error_behavior(
            list_contract_awards,
            NotFoundError,
            expected_message
        )

if __name__ == '__main__':
    unittest.main()
