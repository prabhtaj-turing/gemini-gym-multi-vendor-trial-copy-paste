from typing import Dict
import unittest
import sys
import os
from unittest.mock import patch
from pydantic import ValidationError

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from .account_management_base_exception import AccountManagementBaseTestCase
from ..SimulationEngine.db import DB
from ..SimulationEngine.custom_errors import AccountNotFoundError

from ..SimulationEngine.models import (
    ActiveFeature,
    Address,
    CommunicationPreferences,
    CustomerAccountDetails,
    Device,
    DeviceUpgradeEligibility,
    KnowledgeBaseQueryResponse,
    KnowledgeBaseSnippet,
    ServiceModificationResponse,
    ServicePlan,
)
from .. import (
    update_account_information,
    get_customer_account_details,
    query_available_plans_and_features,
    escalate,
    fail,
    cancel,
)


class TestAccountManagementSmoke(AccountManagementBaseTestCase):
    """
    Smoke tests for Account Management API.
    These are basic tests to ensure the API is functional and can perform core operations.
    """

    def test_end_to_end_account_retrieval(self):
        """End-to-end test for retrieving account details."""
        from APIs.ces_account_management import get_customer_account_details

        # Test with known account from default DB
        result = get_customer_account_details("ACC888777666")

        # Basic checks
        self.assertIsNotNone(result)
        self.assertEqual(result["accountId"], "ACC888777666")
        self.assertEqual(result["customerName"], "Jessica Davis")
        self.assertIsNotNone(result["billingAddress"])
        self.assertIsNotNone(result["devices"])
        self.assertIsNotNone(result["services"])

    def test_end_to_end_device_upgrade_check(self):
        """End-to-end test for checking device upgrade eligibility."""
        from APIs.ces_account_management import check_device_upgrade_eligibility

        # Test with known device from default DB
        result = check_device_upgrade_eligibility(
            "ACC888777666", "555-444-5555", "LINE_NUMBER"
        )

        # Basic checks
        self.assertIsNotNone(result)
        self.assertIsNotNone(result["isEligible"])

    @patch("ces_account_management.SimulationEngine.utils._get_gemini_response")
    def test_end_to_end_plan_query(self, mock_get_gemini_response):
        """End-to-end test for querying available plans."""
        # Mock the Gemini response
        mock_get_gemini_response.return_value = '[{"id": "P003", "name": "Unlimited Data Plan", "description": "Unlimited high-speed data, talk & text. Fair usage policy applies.", "type": "PLAN", "monthlyCost": 50, "dataAllowance": "Unlimited", "termsAndConditionsUrl": "https://api.sundaymobile.com/terms/P003", "compatibilityNotes": ""}]'

        result = query_available_plans_and_features("unlimited")

        # Basic checks
        self.assertIsNotNone(result)
        self.assertIsNotNone(result["answer"])

    def test_end_to_end_account_update(self):
        """End-to-end test for updating account information."""

        # Get original account details
        original = get_customer_account_details("ACC888777666")
        original_email = original["contactEmail"]

        # Update account
        update_data = {"contactEmail": "updated@example.com"}
        result = update_account_information("ACC888777666", update_data)

        # Verify update
        self.assertEqual(result["contactEmail"], "updated@example.com")
        self.assertNotEqual(result["contactEmail"], original_email)

    def test_terminal_functions_basic_functionality(self):
        """Smoke test for terminal functions."""

        # Test escalate
        result = escalate("Test escalation")
        self.assertEqual(result["action"], "escalate")

        # Test fail
        result = fail("Test failure")
        self.assertEqual(result["action"], "fail")

        # Test cancel
        result = cancel("Test cancellation")
        self.assertEqual(result["action"], "cancel")

    def test_all_functions_importable_and_callable(self):
        """Smoke test that all functions can be imported and are callable."""
        import APIs.ces_account_management as am

        functions = [
            "get_customer_account_details",
            "update_account_information",
            "check_device_upgrade_eligibility",
            "modify_service_plan_or_feature",
            "query_available_plans_and_features",
            "query_account_orders",
            "escalate",
            "fail",
            "cancel",
        ]

        for func_name in functions:
            with self.subTest(function=func_name):
                func = getattr(am, func_name)
                self.assertTrue(callable(func))

    def test_database_loaded_with_expected_data(self):
        """Smoke test that database is loaded with expected default data."""
        # Check that we have account data
        self.assertIsInstance(DB["accountDetails"], Dict)
        self.assertGreater(len(DB["accountDetails"]), 0)

        # Check that we have plan data
        self.assertIn("availablePlans", DB)
        if "plans" in DB["availablePlans"]:
            self.assertIsInstance(DB["availablePlans"]["plans"], Dict)
            self.assertGreater(len(DB["availablePlans"]["plans"]), 0)

    def test_basic_error_handling(self):
        """Smoke test for basic error handling."""

        # Test with invalid account ID
        self.assert_error_behavior(
            get_customer_account_details,
            AccountNotFoundError,
            "Account INVALID-ACCOUNT-ID not found in the database.",
            accountId="INVALID-ACCOUNT-ID",
        )

        # Test with empty account ID
        self.assert_error_behavior(
            get_customer_account_details,
            ValidationError,
            "String should have at least 1 character",
            accountId="",
        )

    def test_model_instantiation_smoke(self):
        """Smoke test that all models can be instantiated."""

        # Test basic instantiation
        address = Address(
            recipientName="John Doe",
            streetAddressLine1="123 Main St",
            streetAddressLine2="Apt 1",
            city="San Francisco",
            state="CA",
            zipCode="94105",
            country="USA",
        )
        self.assertIsNotNone(address)

        communicationPreferences = CommunicationPreferences(
            emailOptIn=True, smsOptIn=True
        )
        self.assertIsNotNone(communicationPreferences)

        device = Device(
            deviceId="DEV1101",
            deviceName="iPhone SE",
            lineNumber="555-123-4567",
            upgradeEligibilityDate="2025-01-01",
            paymentPlanActive=True,
            paymentPlanRemainingMonths=12,
        )
        self.assertIsNotNone(device)

        activeFeature = ActiveFeature(
            featureId="F003",
            featureName="Premium Voicemail",
            monthlyCost=5.0,
        )
        self.assertIsNotNone(activeFeature)

        servicePlan = ServicePlan(
            serviceId="SVC011",
            planName="Starter Data Plan",
            planId="P002",
            monthlyCost=25.5,
            dataAllowance="5GB",
            activeFeatures=[
                activeFeature,
            ],
        )
        self.assertIsNotNone(servicePlan)

        account = CustomerAccountDetails(
            accountId="ACC888777666",
            customerName="Jessica Davis",
            contactEmail="jessica.davis@example.com",
            contactPhone="555-123-4567",
            billingAddress=address,
            serviceAddress=address,
            communicationPreferences=communicationPreferences,
            devices=[device],
            services=[servicePlan],
            isVerified=True,
            securityPinSet=True,
        )
        self.assertIsNotNone(account)

        eligibility = DeviceUpgradeEligibility(isEligible=True)
        self.assertIsNotNone(eligibility)

        serviceModificationResponse = ServiceModificationResponse(
            status="success",
            effectiveDate="2025-01-01",
            message="Service modified successfully",
            nextBillImpactEstimate="10.00",
            orderId="1234567890",
        )
        self.assertIsNotNone(serviceModificationResponse)

        knowledgeBaseSnippet = KnowledgeBaseSnippet(
            text="Snippet 1", title="Doc 1", uri="https://example.com/1"
        )
        self.assertIsNotNone(knowledgeBaseSnippet)

        knowledgeBaseQueryResponse = KnowledgeBaseQueryResponse(
            answer="The direct answer to the query, synthesized from the knowledge base.",
            snippets=[knowledgeBaseSnippet],
        )
        self.assertIsNotNone(knowledgeBaseQueryResponse)


if __name__ == "__main__":
    unittest.main()
