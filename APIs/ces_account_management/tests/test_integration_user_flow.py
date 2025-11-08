from unittest.mock import patch
# Relative imports for the service's modules
from .. import (
    get_customer_account_details,
    query_available_plans_and_features,
    modify_service_plan_or_feature,
)
from ..SimulationEngine import utils, db

# Assuming BaseTestCaseWithErrorHandler is in a common_utils package
# As per instructions, the test suite MUST inherit from this base class.
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestAccountManagementIntegration(BaseTestCaseWithErrorHandler):
    """
    Integration test suite for the 'ces_account_management' service.
    This test covers a complete user workflow for changing a service plan.
    """

    def setUp(self):
        """
        Set up the in-memory database with necessary test data.
        This method is called before each test function execution.
        """
        # Reset the database to ensure a clean state for the test
        db.reset_db()

        # Per instructions, create an empty DB with keys based on the schema
        # This avoids loading a default state and ensures test isolation.
        db.DB["accountDetails"] = {}
        db.DB["availablePlans"] = {"plans": {}}
        db.DB["orders"] = {}

        # Define constant identifiers for test data
        self.account_id = "ACC_INTEGRATION_01"
        self.service_id = "SVC_INTEGRATION_01"
        self.initial_plan_id = "PLAN_BASIC_INT"
        self.target_plan_id = "PLAN_PRO_INT"

        # 1. Create a test customer account using the utility function
        account_data = {
            "accountId": self.account_id,
            "customerName": "Jane Integration Doe",
            "contactEmail": "jane.doe@integrationtest.com",
            "contactPhone": "555-0123",
            "isVerified": True,
            "securityPinSet": True,
            "billingAddress": {
                "recipientName": "Jane",
                "streetAddressLine1": "123 Test Ave",
                "city": "Testville",
                "state": "TS",
                "zipCode": "12345",
                "country": "USA",
            },
            "serviceAddress": {
                "recipientName": "Jane",
                "streetAddressLine1": "123 Test Ave",
                "city": "Testville",
                "state": "TS",
                "zipCode": "12345",
                "country": "USA",
            },
            "devices": [],
            "communicationPreferences": {
                "emailOptIn": True,
                "smsOptIn": False,
            },
            "services": [],
        }
        utils.create_account(account_data)

        # 2. Add an initial service plan to the customer's account
        initial_service_data = {
            "serviceId": self.service_id,
            "planName": "Basic Unlimited",
            "planId": self.initial_plan_id,
            "monthlyCost": 45.00,
            "dataAllowance": "15GB",
            "activeFeatures": [],
        }
        utils.add_service_to_account(self.account_id, initial_service_data)

        # 3. Populate the 'availablePlans' database with plans for the test
        # (There is no utility for this, so we populate the DB directly)
        db.DB["availablePlans"]["plans"] = {
            self.target_plan_id: {
                "id": self.target_plan_id,
                "name": "Unlimited Pro",
                "description": "Premium plan with 50GB high-speed data.",
                "monthlyCost": 75.00,
                "type": "PLAN",
                "dataAllowance": "50GB",
            },
        }


    @patch('ces_account_management.SimulationEngine.utils._get_gemini_response')
    def test_integration_workflow_change_plan(self, mock_get_gemini_response):
        """
        Tests the full toolchain for a customer changing their service plan.
        Workflow:
        1. Get current account details (verify initial plan).
        2. Query available plans (simulate user searching for an upgrade).
        3. Modify the service plan (execute the upgrade).
        4. Get account details again (verify the plan has changed).
        """
        # Mock the Gemini response
        mock_get_gemini_response.return_value = '[{"id": "P003", "name": "Unlimited Data Plan", "description": "Unlimited high-speed data, talk & text. Fair usage policy applies.", "type": "PLAN", "monthlyCost": 50, "dataAllowance": "Unlimited", "termsAndConditionsUrl": "https://api.sundaymobile.com/terms/P003", "compatibilityNotes": ""}]'
        # Step 1: get_customer_account_details (Initial State Verification)
        initial_details = get_customer_account_details(accountId=self.account_id)

        # Assert that the initial account details are correct
        self.assertIsNotNone(initial_details, "Initial account details should not be None")
        self.assertEqual(initial_details["accountId"], self.account_id)
        # Per the function schema, 'services' is a list.
        self.assertIsInstance(initial_details["services"], list, "Services should be a list")
        
        initial_service = initial_details["services"][0]
        self.assertEqual(initial_service["planId"], self.initial_plan_id)
        self.assertEqual(initial_service["planName"], "Basic Unlimited")
        current_plan_id = initial_service["planId"]

        # Step 2: query_available_plans_and_features
        plan_query_result = query_available_plans_and_features(
            query="Unlimited Plan"
        )
        # Assert that the search function can find the target plan
        self.assertIsNotNone(plan_query_result, "I don't have specific information about that plan or feature in our current offerings.")
        self.assertIn("Unlimited", plan_query_result["answer"])

        # Step 3: modify_service_plan_or_feature
        modification_result = modify_service_plan_or_feature(
            accountId=self.account_id,
            action="CHANGE_PLAN",
            itemId=self.target_plan_id,
            currentPlanId=current_plan_id
        )

        # Assert that the modification API call was successful
        self.assertIsNotNone(modification_result, "Modification result should not be None")
        self.assertEqual(modification_result["status"], "Success")
        self.assertIn("Your plan has been successfully changed", modification_result["message"])
        self.assertIsNotNone(modification_result["orderId"], "An orderId must be returned")
        order_id = modification_result["orderId"]

        # Step 4: get_customer_account_details (Final State Verification)
        updated_details = get_customer_account_details(accountId=self.account_id)

        # Assert that the account details now reflect the new plan
        self.assertIsNotNone(updated_details, "Updated account details should not be None")
        updated_service = updated_details["services"][0]
        self.assertEqual(updated_service["planId"], self.target_plan_id)
        self.assertEqual(updated_service["planName"], "Unlimited Pro")
        self.assertEqual(updated_service["monthlyCost"], 75.00)