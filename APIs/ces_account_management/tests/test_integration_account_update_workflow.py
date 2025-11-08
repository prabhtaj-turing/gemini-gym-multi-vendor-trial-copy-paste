import unittest

# Relative imports for the service's modules
from .. import (
    get_customer_account_details,
    update_account_information,
    check_device_upgrade_eligibility,
    modify_service_plan_or_feature,
)
from ..SimulationEngine import utils, db

# Assuming BaseTestCaseWithErrorHandler is in a common_utils package
# As per instructions, the test suite MUST inherit from this base class.
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestAccountUpdateWorkflowIntegration(BaseTestCaseWithErrorHandler):
    """
    Integration test for a complete account update workflow that includes:
    1. Updating account information
    2. Checking device upgrade eligibility 
    3. Modifying service plan or features
    
    This simulates a real customer scenario where they update their contact info,
    check if they can upgrade their device, and then change their service plan.
    """

    def setUp(self):
        """Set up test environment with a clean database state"""
        # Reset the database to ensure a clean state for the test
        db.reset_db()

        # Per instructions, create an empty DB with keys based on the schema
        # This avoids loading a default state and ensures test isolation.
        db.DB["accountDetails"] = {}
        db.DB["availablePlans"] = {"plans": {}}
        db.DB["orders"] = {}

        # Define constant identifiers for test data
        self.account_id = "ACC_WORKFLOW_01"
        self.device_id = "DEV_WORKFLOW_01"
        self.line_number = "555-019-9000"
        self.initial_plan_id = "PLAN_BASIC_WORKFLOW"
        self.target_plan_id = "PLAN_PRO_WORKFLOW"
        self.feature_id = "FEAT_INTL_WORKFLOW"

        # 1. Create a test customer account using the utility function
        account_data = {
            "accountId": self.account_id,
            "customerName": "Sarah Workflow User",
            "contactEmail": "sarah.workflow@testmail.com",
            "contactPhone": "555-019-9000",
            "isVerified": True,
            "securityPinSet": True,
            "billingAddress": {
                "recipientName": "Sarah",
                "streetAddressLine1": "456 Workflow Ave",
                "city": "Testtown",
                "state": "TX",
                "zipCode": "54321",
                "country": "USA",
            },
            "serviceAddress": {
                "recipientName": "Sarah",
                "streetAddressLine1": "456 Workflow Ave",
                "city": "Testtown",
                "state": "TX",
                "zipCode": "54321",
                "country": "USA",
            },
            "communicationPreferences": {
                "emailOptIn": True,
                "smsOptIn": False,
            },
        }
        utils.create_account(account_data)

        # 2. Add a device to the account
        device_data = {
            "deviceId": self.device_id,
            "deviceName": "iPhone 14",
            "lineNumber": self.line_number,
            "paymentPlanActive": False,
            "paymentPlanRemainingMonths": 0,
            "upgradeEligibilityDate": "2023-01-01",  # Already eligible
        }
        utils.add_device_to_account(self.account_id, device_data)

        # 3. Add an initial service plan to the customer's account
        initial_service_data = {
            "serviceId": "SVC_WORKFLOW_01",
            "planName": "Basic Connect",
            "planId": self.initial_plan_id,
            "monthlyCost": 40.00,
            "dataAllowance": "10GB",
            "activeFeatures": [],
        }
        utils.add_service_to_account(self.account_id, initial_service_data)

        # 4. Populate the 'availablePlans' database with plans and features for the test
        db.DB["availablePlans"]["plans"] = {
            self.target_plan_id: {
                "id": self.target_plan_id,
                "name": "Premium Pro",
                "description": "Premium plan with unlimited data and 5G access.",
                "monthlyCost": 85.00,
                "type": "PLAN",
                "dataAllowance": "Unlimited",
            },
            self.feature_id: {
                "id": self.feature_id,
                "name": "International Calling",
                "description": "Unlimited international calling to 50+ countries.",
                "monthlyCost": 20.00,
                "type": "FEATURE_ADDON",
            }
        }

    def test_complete_account_update_workflow(self):
        """
        Tests the full workflow for a customer updating account info, checking upgrade eligibility,
        and modifying their service plan.
        Workflow:
        1. Update account information (email, phone, preferences).
        2. Check device upgrade eligibility.
        3. Change service plan to a premium option.
        4. Add an international calling feature.
        5. Verify all changes persisted correctly.
        """

        # Step 1: Update account information
        update_request = {
            "contactEmail": "sarah.new@updatedmail.com",
            "contactPhone": "555-029-9000",
            "communicationPreferences": {
                "emailOptIn": True,
                "smsOptIn": True
            }
        }
        
        update_result = update_account_information(
            accountId=self.account_id,
            requestBody=update_request
        )
        
        # Verify account information was updated successfully
        self.assertIsNotNone(update_result, "Account update result should not be None")
        self.assertEqual(update_result["contactEmail"], "sarah.new@updatedmail.com")
        self.assertEqual(update_result["contactPhone"], "555-029-9000")
        self.assertTrue(update_result["communicationPreferences"]["emailOptIn"])
        self.assertTrue(update_result["communicationPreferences"]["smsOptIn"])

        # Step 2: Check device upgrade eligibility
        eligibility_result = check_device_upgrade_eligibility(
            accountId=self.account_id,
            identifier=self.line_number,
            identifierType="LINE_NUMBER"
        )
        
        # Verify device is eligible for upgrade (no payment plan active)
        self.assertIsNotNone(eligibility_result, "Eligibility result should not be None")
        self.assertTrue(eligibility_result["isEligible"], "Device should be eligible for upgrade")
        self.assertIsNone(eligibility_result.get("reason"), "No eligibility blocking reason expected")

        # Step 3: Change service plan to premium option
        plan_change_result = modify_service_plan_or_feature(
            accountId=self.account_id,
            action="CHANGE_PLAN",
            itemId=self.target_plan_id,
            currentPlanId=self.initial_plan_id
        )
        
        # Verify plan change was successful
        self.assertIsNotNone(plan_change_result, "Plan change result should not be None")
        self.assertEqual(plan_change_result["status"], "Success")
        self.assertIn("Premium Pro", plan_change_result["message"])
        self.assertIsNotNone(plan_change_result["orderId"], "Order ID should be provided")

        # Step 4: Add international calling feature
        feature_add_result = modify_service_plan_or_feature(
            accountId=self.account_id,
            action="ADD_FEATURE",
            itemId=self.feature_id,
            currentPlanId=self.target_plan_id
        )
        
        # Verify feature was added successfully
        self.assertIsNotNone(feature_add_result, "Feature add result should not be None")
        self.assertEqual(feature_add_result["status"], "Success")
        self.assertIn("International Calling", feature_add_result["message"])
        self.assertIsNotNone(feature_add_result["orderId"], "Order ID should be provided")

        # Step 5: Verify final account state
        final_account_details = get_customer_account_details(accountId=self.account_id)
        
        # Verify all changes persisted correctly
        self.assertIsNotNone(final_account_details, "Final account details should not be None")
        
        # Check updated contact information
        self.assertEqual(final_account_details["contactEmail"], "sarah.new@updatedmail.com")
        self.assertEqual(final_account_details["contactPhone"], "555-029-9000")
        self.assertTrue(final_account_details["communicationPreferences"]["emailOptIn"])
        
        # Verify service plan was updated
        services = final_account_details["services"]
        self.assertIsInstance(services, list, "Services should be a list")
        self.assertIn("SVC_WORKFLOW_01", [svc["serviceId"] for svc in services], "Service should exist")
        
        current_service = next(svc for svc in services if svc["serviceId"] == "SVC_WORKFLOW_01")
        self.assertEqual(current_service["planName"], "Premium Pro")
        self.assertEqual(current_service["planId"], self.target_plan_id)
        self.assertEqual(current_service["monthlyCost"], 85.00)
        
        # Verify feature was added
        active_features = current_service["activeFeatures"]
        self.assertIsInstance(active_features, list, "Active features should be a list")
        self.assertTrue(any(f.get("featureId") == self.feature_id for f in active_features), "International calling feature should be active")
        
        intl_feature = next(f for f in active_features if f.get("featureId") == self.feature_id)
        self.assertEqual(intl_feature["featureName"], "International Calling")
        self.assertEqual(intl_feature["monthlyCost"], 20.00)
        
        # Calculate and verify total monthly cost
        total_cost = current_service["monthlyCost"]
        for feature in active_features:
            total_cost += feature["monthlyCost"]
        
        expected_total = 85.00 + 20.00  # Premium Pro + International Calling
        self.assertEqual(total_cost, expected_total)

    def test_workflow_error_handling(self):
        """
        Test error handling throughout the workflow with invalid data.
        """

        # Test 1: Invalid email update
        self.assert_error_behavior(
            update_account_information,
            ValueError,
            "Invalid email value 'invalid-email-format' for field 'contactEmail'",
            accountId=self.account_id,
            requestBody={"contactEmail": "invalid-email-format"}
        )

        # Test 2: Invalid phone number update
        
        self.assert_error_behavior(
            update_account_information,
            ValueError,
            "The phone number 'invalid-phone-123' is not valid.",
            accountId=self.account_id,
            requestBody={"contactPhone": "invalid-phone-123"}
        )

        # Test 3: Checking eligibility for non-existent device
        self.assert_error_behavior(
            check_device_upgrade_eligibility,
            ValueError,
            "Device with LINE_NUMBER '555-999-9000' not found on account.",
            accountId=self.account_id,
            identifier="555-999-9000",
            identifierType="LINE_NUMBER"
        )

        # Test 4: Changing to non-existent plan
        self.assert_error_behavior(
            modify_service_plan_or_feature,
            ValueError,
            "Item NONEXISTENT_PLAN_XYZ not found in the database.",
            accountId=self.account_id,
            action="CHANGE_PLAN",
            itemId="NONEXISTENT_PLAN_XYZ",
            currentPlanId=self.initial_plan_id
        )

        # Test 5: Adding non-existent feature
        self.assert_error_behavior(
            modify_service_plan_or_feature,
            ValueError,
            "Item NONEXISTENT_FEATURE_ABC not found in the database.",
            accountId=self.account_id,
            action="ADD_FEATURE",
            itemId="NONEXISTENT_FEATURE_ABC",
            currentPlanId=self.initial_plan_id
        )

    def test_workflow_step_by_step_validation(self):
        """
        Test that validates each step affects the subsequent steps correctly.
        This ensures proper state management and data flow between operations.
        """

        # Step 1: Get initial account state
        initial_state = get_customer_account_details(accountId=self.account_id)
        initial_email = initial_state["contactEmail"]
        initial_plan_id = initial_state["services"][0]["planId"]

        # Step 2: Update account and verify change is visible
        new_email = "sarah.steptest@validation.com"
        update_result = update_account_information(
            accountId=self.account_id,
            requestBody={"contactEmail": new_email}
        )
        
        # Verify update result contains new email
        self.assertEqual(update_result["contactEmail"], new_email)
        
        # Verify change is visible in fresh account details fetch
        post_update_state = get_customer_account_details(accountId=self.account_id)
        self.assertEqual(post_update_state["contactEmail"], new_email)
        self.assertNotEqual(post_update_state["contactEmail"], initial_email)
        
        # Step 3: Change plan and verify it affects account details
        plan_change_result = modify_service_plan_or_feature(
            accountId=self.account_id,
            action="CHANGE_PLAN",
            itemId=self.target_plan_id,
            currentPlanId=initial_plan_id
        )
        
        self.assertEqual(plan_change_result["status"], "Success")
        
        # Verify plan change is visible in fresh account details fetch
        post_plan_change_state = get_customer_account_details(accountId=self.account_id)
        current_service = post_plan_change_state["services"][0]
        self.assertEqual(current_service["planId"], self.target_plan_id)
        self.assertNotEqual(current_service["planId"], initial_plan_id)
        
        # Verify email update is still persisted after plan change
        self.assertEqual(post_plan_change_state["contactEmail"], new_email)
        
        # Step 4: Add feature and verify it appears in account details
        feature_add_result = modify_service_plan_or_feature(
            accountId=self.account_id,
            action="ADD_FEATURE",
            itemId=self.feature_id,
            currentPlanId=self.target_plan_id
        )
        
        self.assertEqual(feature_add_result["status"], "Success")
        
        # Verify feature appears in fresh account details fetch
        final_state = get_customer_account_details(accountId=self.account_id)
        final_service = final_state["services"][0]
        self.assertTrue(any(f.get("featureId") == self.feature_id for f in final_service["activeFeatures"]))
        
        # Verify all previous changes are still persisted
        self.assertEqual(final_state["contactEmail"], new_email)
        self.assertEqual(final_service["planId"], self.target_plan_id)


if __name__ == "__main__":
    unittest.main()