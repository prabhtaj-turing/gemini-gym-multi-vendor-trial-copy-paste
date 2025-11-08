import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.models import (
    Address,
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


class TestAccountManagementModels(BaseTestCaseWithErrorHandler):
    """
    Test suite for Account Management data models.
    Tests model instantiation, field assignments, and data validation.
    """

    def test_address_model(self):
        """Test Address model instantiation and field assignments."""
        # Test with all fields
        address = Address(
            city="San Francisco",
            country="USA",
            recipientName="John Doe",
            state="CA",
            streetAddressLine1="123 Market St",
            streetAddressLine2="Apt 4B",
            zipCode="94105"
        )
        
        self.assertEqual(address.city, "San Francisco")
        self.assertEqual(address.country, "USA")
        self.assertEqual(address.recipientName, "John Doe")
        self.assertEqual(address.state, "CA")
        self.assertEqual(address.streetAddressLine1, "123 Market St")
        self.assertEqual(address.streetAddressLine2, "Apt 4B")
        self.assertEqual(address.zipCode, "94105")

    def test_communication_preferences_model(self):
        """Test CommunicationPreferences model."""
        prefs = CommunicationPreferences(emailOptIn=True, smsOptIn=False)
        
        self.assertTrue(prefs.emailOptIn)
        self.assertFalse(prefs.smsOptIn)


    def test_device_model(self):
        """Test Device model."""
        device = Device(
            deviceId="DEV123456",
            deviceName="iPhone 15 Pro",
            lineNumber="555-123-4567",
            paymentPlanActive=True,
            paymentPlanRemainingMonths=12,
            upgradeEligibilityDate="2025-03-15"
        )
        
        self.assertEqual(device.deviceId, "DEV123456")
        self.assertEqual(device.deviceName, "iPhone 15 Pro")
        self.assertEqual(device.lineNumber, "555-123-4567")
        self.assertTrue(device.paymentPlanActive)
        self.assertEqual(device.paymentPlanRemainingMonths, 12)
        self.assertEqual(device.upgradeEligibilityDate, "2025-03-15")

    def test_active_feature_model(self):
        """Test ActiveFeature model."""
        feature = ActiveFeature(
            featureId="FEAT_INTL_CALL",
            featureName="International Calling Pass",
            monthlyCost=15.00
        )
        
        self.assertEqual(feature.featureId, "FEAT_INTL_CALL")
        self.assertEqual(feature.featureName, "International Calling Pass")
        self.assertEqual(feature.monthlyCost, 15.00)

    def test_service_plan_model(self):
        """Test ServicePlan model with features."""
        features = [
            ActiveFeature(featureId="F1", featureName="Feature 1", monthlyCost=5.0),
            ActiveFeature(featureId="F2", featureName="Feature 2", monthlyCost=10.0),
        ]
        
        plan = ServicePlan(
            activeFeatures=features,
            dataAllowance="Unlimited",
            monthlyCost=75.50,
            planId="PLAN_UNL_PLUS",
            planName="Unlimited Plus Plan",
            serviceId="SVC_98765"
        )
        
        self.assertEqual(len(plan.activeFeatures), 2)
        self.assertEqual(plan.dataAllowance, "Unlimited")
        self.assertEqual(plan.monthlyCost, 75.50)
        self.assertEqual(plan.planId, "PLAN_UNL_PLUS")
        self.assertEqual(plan.planName, "Unlimited Plus Plan")
        self.assertEqual(plan.serviceId, "SVC_98765")
        ids = {f.featureId for f in plan.activeFeatures}
        self.assertIn("F1", ids)
        self.assertIn("F2", ids)

    def test_customer_account_details_model(self):
        """Test CustomerAccountDetails model with nested objects."""
        billing_address = Address(
            city="San Francisco", 
            state="CA", 
            recipientName="Jane Doe", 
            streetAddressLine1="123 Main St", 
            streetAddressLine2="Apt 1", 
            zipCode="12345", 
            country="USA"
        )
        service_address = Address(
            city="Oakland", 
            state="CA", 
            recipientName="Jane Doe", 
            streetAddressLine1="123 Main St", 
            streetAddressLine2="Apt 1", 
            zipCode="12345", 
            country="USA"
        )
        comm_prefs = CommunicationPreferences(emailOptIn=True, smsOptIn=True)
        
        device = Device(
            deviceId="DEV123", 
            deviceName="iPhone", 
            lineNumber="555-123-4567", 
            upgradeEligibilityDate="2025-01-01", 
            paymentPlanActive=True, 
            paymentPlanRemainingMonths=12,
        )
        
        feature = ActiveFeature(
            featureId="F1", 
            featureName="Feature 1",
            monthlyCost=10.00
        )
        service = ServicePlan(
            serviceId="SVC1", 
            planName="Basic Plan", 
            activeFeatures=[feature],
            dataAllowance="10GB",
            monthlyCost=100.00,
            planId="PLAN1",
        )
        
        account = CustomerAccountDetails(
            accountId="ACC123456789",
            billingAddress=billing_address,
            communicationPreferences=comm_prefs,
            contactEmail="jane.doe@example.com",
            contactPhone="555-867-5309",
            customerName="Jane Doe",
            devices=[device],
            isVerified=True,
            securityPinSet=True,
            serviceAddress=service_address,
            services=[service]
        )
        
        self.assertEqual(account.accountId, "ACC123456789")
        self.assertEqual(account.billingAddress.city, "San Francisco")
        self.assertEqual(account.serviceAddress.city, "Oakland")
        self.assertTrue(account.communicationPreferences.emailOptIn)
        self.assertEqual(account.contactEmail, "jane.doe@example.com")
        self.assertEqual(account.customerName, "Jane Doe")
        self.assertEqual(len(account.devices), 1)
        self.assertEqual(account.devices[0].deviceId, "DEV123")
        self.assertTrue(account.isVerified)
        self.assertTrue(account.securityPinSet)
        self.assertEqual(len(account.services), 1)
        self.assertEqual(account.services[0].serviceId, "SVC1")

    def test_account_information_update_model(self):
        """Test AccountInformationUpdate model."""
        new_address = Address(
            city="New York", 
            state="NY", 
            recipientName="New User", 
            streetAddressLine1="123 Main St", 
            streetAddressLine2="Apt 1", 
            zipCode="12345", 
            country="USA"
        )
        new_prefs = CommunicationPreferences(emailOptIn=False, smsOptIn=True)
        
        update = AccountInformationUpdateInput(
            billingAddress=new_address.model_dump(mode="json"),
            communicationPreferences=new_prefs.model_dump(mode="json"),
            contactEmail="new.email@example.com",
            contactPhone="555-555-1212"
        )
        
        self.assertEqual(update.billingAddress.city, "New York")
        self.assertFalse(update.communicationPreferences.emailOptIn)
        self.assertEqual(update.contactEmail, "new.email@example.com")
        self.assertEqual(update.contactPhone, "555-555-1212")

    def test_device_upgrade_eligibility_model(self):
        """Test DeviceUpgradeEligibility model."""
        eligibility = DeviceUpgradeEligibility(
            earlyUpgradeOptions="Eligible for early upgrade with a $150 fee.",
            eligibilityDate="2024-12-25",
            isEligible=False,
            reason="Device payment plan has 8 remaining payments.",
            remainingDevicePayments=399.99
        )
        
        self.assertEqual(eligibility.earlyUpgradeOptions, "Eligible for early upgrade with a $150 fee.")
        self.assertEqual(eligibility.eligibilityDate, "2024-12-25")
        self.assertFalse(eligibility.isEligible)
        self.assertEqual(eligibility.reason, "Device payment plan has 8 remaining payments.")
        self.assertEqual(eligibility.remainingDevicePayments, 399.99)

    def test_service_modification_response_model(self):
        """Test ServiceModificationResponse model."""
        response = ServiceModificationResponse(
            effectiveDate="2023-11-20",
            message="Your plan has been successfully changed to Unlimited Pro.",
            nextBillImpactEstimate="A prorated charge of $5.50 will be added.",
            orderId="ORD_CHANGE_54321",
            status="Success"
        )
        
        self.assertEqual(response.effectiveDate, "2023-11-20")
        self.assertEqual(response.message, "Your plan has been successfully changed to Unlimited Pro.")
        self.assertEqual(response.nextBillImpactEstimate, "A prorated charge of $5.50 will be added.")
        self.assertEqual(response.orderId, "ORD_CHANGE_54321")
        self.assertEqual(response.status, "Success")

    def test_knowledge_base_snippet_model(self):
        """Test KnowledgeBaseSnippet model."""
        snippet = KnowledgeBaseSnippet(
            text="The raw text of the snippet from the source document.",
            title="The title of the source document.",
            uri="https://example.com/document"
        )
        
        self.assertEqual(snippet.text, "The raw text of the snippet from the source document.")
        self.assertEqual(snippet.title, "The title of the source document.")
        self.assertEqual(snippet.uri, "https://example.com/document")

    def test_knowledge_base_query_response_model(self):
        """Test KnowledgeBaseQueryResponse model."""
        snippets = [
            KnowledgeBaseSnippet(text="Snippet 1", title="Doc 1", uri="https://example.com/1"),
            KnowledgeBaseSnippet(text="Snippet 2", title="Doc 2", uri="https://example.com/2")
        ]
        
        response = KnowledgeBaseQueryResponse(
            answer="The direct answer to the query, synthesized from the knowledge base.",
            snippets=snippets
        )
        
        self.assertEqual(response.answer, "The direct answer to the query, synthesized from the knowledge base.")
        self.assertEqual(len(response.snippets), 2)
        self.assertEqual(response.snippets[0].title, "Doc 1")
        self.assertEqual(response.snippets[1].title, "Doc 2")

    def test_model_defaults(self):
        """Test that all models can be instantiated with default values."""
        models_to_test = [
            AccountInformationUpdateInput,
            KnowledgeBaseSnippet,
        ]
        
        for model_class in models_to_test:
            with self.subTest(model=model_class.__name__):
                instance = model_class()
                self.assertIsNotNone(instance)

    def test_model_field_assignment(self):
        """Test that model fields can be assigned after instantiation."""
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


if __name__ == '__main__':
    unittest.main()
