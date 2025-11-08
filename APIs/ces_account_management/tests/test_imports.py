import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
import importlib


class TestImports(BaseTestCaseWithErrorHandler):
    """
    Test suite for validating the account_management package imports and basic functionality.
    """

    def test_import_account_management_package(self):
        """
        Test that the account_management package can be imported successfully.
        """
        try:
            import APIs.ces_account_management
        except ImportError:
            self.fail("Failed to import APIs.account_management package")

    def test_import_public_functions(self):
        """
        Test that the public functions can be imported successfully.
        """
        try:
            from APIs.ces_account_management import (
                get_customer_account_details,
                update_account_information,
                check_device_upgrade_eligibility,
                modify_service_plan_or_feature,
                query_available_plans_and_features,
                query_account_orders,
                escalate,
                fail,
                cancel
            )
        except ImportError as e:
            self.fail(f"Failed to import public functions: {e}")

    def test_import_simulation_engine(self):
        """
        Test that SimulationEngine components can be imported.
        """
        try:
            from APIs.ces_account_management.SimulationEngine import db, models, utils
        except ImportError as e:
            self.fail(f"Failed to import SimulationEngine components: {e}")

    def test_import_models(self):
        """
        Test that data models can be imported successfully.
        """
        try:
            from APIs.ces_account_management.SimulationEngine.models import (
                AddressInput,
                CommunicationPreferences,
                Device,
                ActiveFeature,
                ServicePlan,
                CustomerAccountDetails,
                AccountInformationUpdateInput,
                DeviceUpgradeEligibility,
                ServiceModificationResponse,
                KnowledgeBaseSnippet,
                KnowledgeBaseQueryResponse
            )
        except ImportError as e:
            self.fail(f"Failed to import data models: {e}")

    def test_db_structure(self):
        """
        Test that the database has the expected structure.
        """
        from APIs.ces_account_management.SimulationEngine.db import DB
        
        self.assertIsInstance(DB, dict)
        self.assertIn("accountDetails", DB)
        self.assertIn("availablePlans", DB)

    def test_function_availability(self):
        """
        Test that all expected functions are available in the package.
        """
        import APIs.ces_account_management as am
        
        expected_functions = [
            'get_customer_account_details',
            'update_account_information',
            'check_device_upgrade_eligibility',
            'modify_service_plan_or_feature',
            'query_available_plans_and_features',
            'query_account_orders',
            'escalate',
            'fail',
            'cancel'
        ]
        
        for func_name in expected_functions:
            self.assertTrue(hasattr(am, func_name), f"Function {func_name} not available")

    def test_function_callability(self):
        """
        Test that imported functions are callable.
        """
        import APIs.ces_account_management as am
        
        functions_to_test = [
            'get_customer_account_details',
            'update_account_information',
            'check_device_upgrade_eligibility',
            'modify_service_plan_or_feature',
            'query_available_plans_and_features',
            'query_account_orders',
            'escalate',
            'fail',
            'cancel'
        ]
        
        for func_name in functions_to_test:
            func = getattr(am, func_name)
            self.assertTrue(callable(func), f"Function {func_name} is not callable")

    def test_models_instantiation(self):
        """
        Test that model classes can be instantiated.
        """
        from APIs.ces_account_management.SimulationEngine.models import (
            Address, 
            CustomerAccountDetails,
            DeviceUpgradeEligibility,
            CommunicationPreferences,
        )
        
        # Test Address model
        address = Address(
            city="Test City", 
            state="TS", 
            recipientName="Test User", 
            streetAddressLine1="123 Main St", 
            streetAddressLine2="Apt 1", 
            zipCode="12345", 
            country="USA"
        )
        self.assertEqual(address.city, "Test City")
        self.assertEqual(address.state, "TS")
        self.assertEqual(address.recipientName, "Test User")
        self.assertEqual(address.streetAddressLine1, "123 Main St")
        self.assertEqual(address.streetAddressLine2, "Apt 1")
        self.assertEqual(address.zipCode, "12345")
        self.assertEqual(address.country, "USA")
        
        # Test CustomerAccountDetails model
        account = CustomerAccountDetails(
            accountId="TEST123",
            customerName="Test User",
            contactEmail="test.user@example.com",
            contactPhone="555-000-0000",
            billingAddress=address,
            serviceAddress=address,
            communicationPreferences=CommunicationPreferences(emailOptIn=True, smsOptIn=False),
            devices=[],
            services=[],
            isVerified=True,
            securityPinSet=True,
        )
        self.assertEqual(account.accountId, "TEST123")
        self.assertEqual(account.customerName, "Test User")
        
        # Test DeviceUpgradeEligibility model
        eligibility = DeviceUpgradeEligibility(isEligible=True)
        self.assertTrue(eligibility.isEligible)


if __name__ == '__main__':
    unittest.main()
