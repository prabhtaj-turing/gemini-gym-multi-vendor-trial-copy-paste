"""
Test cases for the Pydantic models in the CES Loyalty Auth API.

This module verifies that all Pydantic models used in the CES Loyalty Auth API
can be instantiated correctly, handle optional fields properly, and raise
validation errors for invalid data.
"""

import unittest
from pydantic import ValidationError
from APIs.ces_loyalty_auth.SimulationEngine.models import (
    Subscription,
    PaymentHistory,
    PaymentInfo,
    MtnStatus,
    DeviceCategory,
    DeviceType,
    DeviceInfo,
    EquipmentInfo,
    AccessCharge,
    ManageCustomerAuthenticationResponse,
    PricePlanInfo,
    Line,
    CustomerProfile,
    LoyaltyOffer,
    MyPlanPerk,
    GetPreAuthenticationCallDataParams,
    GetPreAuthenticationCallDataSessionInfo,
    GetPreAuthenticationCallDataResponse,
    GetAuthenticatedCustomerProfileResponse,
    ManageCustomerAuthenticationParams,
    ManageCustomerAuthenticationSessionInfo)
from .loyalty_auth_base_exception import LoyaltyAuthBaseTestCase


class TestModels(LoyaltyAuthBaseTestCase):
    """
    Test suite for the Pydantic models in the CES Loyalty Auth API.
    """

    def test_subscription_model(self):
        """
        Tests the Subscription model for correct instantiation.
        """
        data = {"skuName": "Test SKU", "price": "10.00"}
        sub = Subscription(**data)
        self.assertEqual(sub.skuName, "Test SKU")

    def test_payment_history_model(self):
        """
        Tests the PaymentHistory model for correct instantiation.
        """
        data = {"totalBalance": "100.00", "amountPaid": "50.00"}
        ph = PaymentHistory(**data)
        self.assertEqual(ph.totalBalance, "100.00")

    def test_payment_info_model(self):
        """
        Tests the PaymentInfo model with required and optional fields.
        """
        data = {"enrolledInAutopay": True, "lastPaymentAmount": "50.00"}
        pi = PaymentInfo(**data)
        self.assertTrue(pi.enrolledInAutopay)

    def test_mtn_status_model(self):
        """
        Tests the MtnStatus model for correct instantiation.
        """
        data = {"isActive": True}
        ms = MtnStatus(**data)
        self.assertTrue(ms.isActive)

    def test_device_models(self):
        """
        Tests the device-related models (DeviceCategory, DeviceType, DeviceInfo, EquipmentInfo).
        """
        cat = DeviceCategory(smartphone=True)
        dtype = DeviceType(device5GE=True)
        dinfo = DeviceInfo(displayName="Test Device", category=cat, deviceType=dtype)
        einfo = EquipmentInfo(deviceInfo=dinfo)
        self.assertEqual(einfo.deviceInfo.displayName, "Test Device")
        self.assertTrue(einfo.deviceInfo.category.smartphone)

    def test_plan_and_line_models(self):
        """
        Tests the AccessCharge, PricePlanInfo, and Line models.
        """
        ac = AccessCharge(monthlyAccessCharge="50.00")
        ppi = PricePlanInfo(
            planId="123",
            effectiveDate="2023-01-01",
            planDisplayName="Test Plan",
            accessCharge=ac,
        )
        line = Line(
            mtn="1234567890",
            mtnStatus=MtnStatus(isActive=True),
            equipmentInfos=EquipmentInfo(),
            pricePlanInfo=ppi,
        )
        self.assertEqual(line.pricePlanInfo.planDisplayName, "Test Plan")

    def test_customer_profile_model(self):
        """
        Tests the CustomerProfile model with required fields.
        """
        line_data = {
            "mtn": "1234567890",
            "mtnStatus": {"isActive": True},
            "equipmentInfos": {},
        }
        data = {
            "customerName": "John Doe",
            "numberOfLines": "1",
            "accountNumber": "ACC123",
            "lines": [line_data],
        }
        profile = CustomerProfile(**data)
        self.assertEqual(profile.customerName, "John Doe")
        self.assertEqual(len(profile.lines), 1)

    def test_offer_and_perk_models(self):
        """
        Tests the LoyaltyOffer and MyPlanPerk models.
        """
        offer = LoyaltyOffer(
            OfferDesc="Test Offer",
            offerOrder="1",
            offerType="Loyalty",
            OfferID="O123",
        )
        perk = MyPlanPerk(
            monthly_value="20",
            monthly_cost="10",
            savings="10",
            description="Test Perk",
            perk="PERK01",
        )
        self.assertEqual(offer.OfferDesc, "Test Offer")
        self.assertEqual(perk.perk, "PERK01")

    def test_response_models(self):
        """
        Tests the main response models for the API tools.
        """
        # Test GetPreAuthenticationCallDataResponse
        pre_auth_params = {
            "hasMtnLoyaltyOffers": True,
            "availablePerks": [{"perk": "data"}],
            "accountNumber": "ACC123",
            "status": "SUCCESS",
            "statusCode": "00000",
            "customerName": "John Doe",
            "preferredFirstName": "John",
            "firstName": "John",
            "statusMessage": "",
            "loyaltyOffersStatusCode": "00000",
            "loyaltyOffers": [],
            "unlimitedPlanPerks": [],
            "sundayMobileValueProposition": {},
            "sundayMobileOST": {},
            "autoPayPaperFreeDiscountAmountInfo": {},
            "myPlanPricingDetails": {},
            "myPlanPerks": {"myplan_perks": []},
            "myPlanFeatures": {},
        }
        pre_auth_info = {"parameters": pre_auth_params}
        pre_auth_response = GetPreAuthenticationCallDataResponse(
            sessionInfo=pre_auth_info
        )
        self.assertEqual(
            pre_auth_response.sessionInfo.parameters.customerName, "John Doe"
        )

        # Test GetAuthenticatedCustomerProfileResponse
        profile_data = {
            "customerName": "John Doe",
            "numberOfLines": "1",
            "accountNumber": "ACC123",
            "lines": [
                {
                    "mtn": "1234567890",
                    "mtnStatus": {"isActive": True},
                    "equipmentInfos": {},
                }
            ],
        }
        auth_profile_response = GetAuthenticatedCustomerProfileResponse(
            customerProfile=profile_data
        )
        self.assertEqual(
            auth_profile_response.customerProfile.customerName, "John Doe"
        )

        # Test ManageCustomerAuthenticationResponse
        auth_params = {
            "authstate": "ACCEPT",
            "sessionId": "S123",
            "statusMessage": "Success",
        }
        auth_info = {"parameters": auth_params}
        auth_response = ManageCustomerAuthenticationResponse(sessionInfo=auth_info)
        self.assertEqual(auth_response.sessionInfo.parameters.authstate, "ACCEPT")

    def test_model_validation_errors(self):
        """
        Tests that Pydantic models raise validation errors for missing required fields.
        """
        with self.assertRaises(ValidationError):
            # Missing required fields for CustomerProfile
            CustomerProfile(customerName="John Doe")

        with self.assertRaises(ValidationError):
            # Missing required fields for Line
            Line(mtn="1234567890")


if __name__ == "__main__":
    unittest.main()
