import json
import unittest

from common_utils.base_case import BaseTestCaseWithErrorHandler

from .. import (
    done,
    enroll_in_offer,
    get_authenticated_customer_profile,
    get_pre_authentication_call_data,
    manage_customer_authentication,
    record_call_outcome_and_disconnect)
from ..SimulationEngine import db, models, utils


class TestCesLoyaltyAuthIntegration(BaseTestCaseWithErrorHandler):
    """
    Integration test suite for the CES Loyalty Auth service workflow.
    """

    def setUp(self):
        """
        Set up the mock database with required data for the integration test.
        This method prepares the data for the entire successful workflow.
        """
        # 1. Create an empty DB using the reset utility
        db.reset_db()

        # 2. Prepare and set pre-authentication data
        pre_auth_data = {
            "sessionInfo": {
                "parameters": {
                    "hasMtnLoyaltyOffers": True,
                    "availablePerks": [{"perk": "Streaming Bundle"}],
                    "accountNumber": "ACC-INTEGRATION-TEST",
                    "status": "Success",
                    "statusCode": "200",
                    "customerName": "John Test",
                    "preferredFirstName": "John",
                    "firstName": "John",
                    "statusMessage": "Pre-authentication data retrieved successfully.",
                    "loyaltyOffersStatusCode": "200",
                    "loyaltyOffers": [
                        {
                            "OfferDesc": "$10 Loyalty Discount for 12 months",
                            "offerOrder": "1",
                            "offerType": "DISCOUNT",
                            "OfferID": "LOYALTYOFFER001",
                        }
                    ],
                    "unlimitedPlanPerks": [],
                    "sundayMobileValueProposition": {},
                    "sundayMobileOST": {},
                    "autoPayPaperFreeDiscountAmountInfo": {},
                    "myPlanPricingDetails": {},
                    "myPlanPerks": {"myplan_perks": []},
                    "myPlanFeatures": {},
                }
            }
        }
        utils.set_preauth_data(pre_auth_data)

        # 3. Prepare and set authentication result data for a successful auth
        auth_result_data = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_COMPLETE",
                    "sessionId": "test-session-12345",
                    "statusMessage": "Authentication successful.",
                    "statusCode": "200",
                    "sessionMap": {
                        "adaptiveAuthentication": json.dumps({"authstatus": "ACCEPT"})
                    },
                }
            }
        }
        utils.set_auth_result(auth_result_data)

        # 4. Prepare and set the authenticated customer profile data
        customer_profile_data = {
            "customerProfile": {
                "customerName": "John Test",
                "numberOfLines": "1",
                "accountNumber": "ACC-INTEGRATION-TEST",
                "lines": [
                    {
                        "mtn": "555-0101",
                        "mtnStatus": {"isActive": True},
                        "equipmentInfos": {
                            "deviceInfo": {"displayName": "Test Phone Model"}
                        },
                        "mobileInfoAttributes": {
                            "accessRoles": {
                                "owner": True,
                                "manager": False,
                                "member": False,
                            }
                        },
                    }
                ],
                "customerFirstName": "John",
                "customerLastName": "Test",
                "customerRole": "Owner",
            }
        }
        utils.set_customer_profile(customer_profile_data)

        # 5. Validate the overall DB state against the Pydantic model
        models.CesLoyaltyAuthDBModel(**db.DB)

    def test_integration_workflow(self):
        """
        Tests the full integration workflow from pre-authentication to call disconnection.
        """
        # Step 1: Get Pre-Authentication Call Data
        pre_auth_result = get_pre_authentication_call_data()
        self.assertIsNotNone(pre_auth_result)
        pre_auth_params = pre_auth_result.get("sessionInfo", {}).get("parameters", {})
        self.assertEqual(pre_auth_params.get("accountNumber"), "ACC-INTEGRATION-TEST")
        self.assertTrue(pre_auth_params.get("hasMtnLoyaltyOffers"))
        loyalty_offers = pre_auth_params.get("loyaltyOffers")
        self.assertIsNotNone(loyalty_offers)
        self.assertEqual(len(loyalty_offers), 1)
        offer_id = loyalty_offers[0].get("OfferID")
        self.assertEqual(offer_id, "LOYALTYOFFER001")

        # Step 2: Manage Customer Authentication (following DI flow)
        # Step 2a: Initialize authentication (send SMS)
        auth_init_result = manage_customer_authentication(authstate="AUTHENTICATION_INIT")
        self.assertIsNotNone(auth_init_result, "Auth INIT response should not be None")
        auth_init_params = auth_init_result.get("sessionInfo", {}).get("parameters", {})
        self.assertEqual(auth_init_params.get("authstate"), "AUTHENTICATION_INIT")
        self.assertEqual(auth_init_params.get("statusCode"), "200")
        self.assertEqual(auth_init_params.get("statusMessage"), "Authentication SMS sent successfully")
        
        # Step 2b: Check authentication status (simulating user interaction with link)
        utils.set_auth_result({
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_SUCCESS",
                    "sessionId": "12345-67890-ABCDE",
                    "statusMessage": "Authentication successful",
                    "statusCode": "200",
                    "sessionMap": {"adaptiveAuthentication": '{"authstatus": "ACCEPT"}'},
                }
            }
        })

        auth_status_result = manage_customer_authentication(authstate="AUTHENTICATION_STATUS")
        self.assertIsNotNone(auth_status_result, "Auth STATUS response should not be None")
        auth_status_params = auth_status_result.get("sessionInfo", {}).get("parameters", {})
        session_map = auth_status_params.get("sessionMap", {})
        adaptive_auth_str = session_map.get("adaptiveAuthentication")
        self.assertIsNotNone(adaptive_auth_str)
        auth_status_data = json.loads(adaptive_auth_str)
        auth_status = auth_status_data.get("authstatus")
        self.assertEqual(auth_status, "ACCEPT")

        # Step 3: Get Authenticated Customer Profile
        # The 'authstatus' from the previous step is used as input here.
        profile_result = get_authenticated_customer_profile(authstatus=auth_status)
        self.assertIsNotNone(profile_result)
        customer_profile = profile_result.get("customerProfile")
        self.assertIsNotNone(customer_profile)
        account_number = customer_profile.get("accountNumber")
        self.assertEqual(account_number, "ACC-INTEGRATION-TEST")
        self.assertEqual(customer_profile.get("customerName"), "John Test")

        # Step 4: Enroll in Offer
        # Use the accountNumber and offerId retrieved in previous steps.
        enrollment_result = enroll_in_offer(
            accountNumber=account_number, offerId=offer_id
        )
        self.assertIsNotNone(enrollment_result)
        self.assertEqual(enrollment_result.get("status"), "success")

        # Step 5: Record Call Outcome and Disconnect
        disconnect_result = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT",
            dispositionCode="PROMO_ACCEPTED")
        self.assertIsNotNone(disconnect_result)
        self.assertEqual(disconnect_result.get("status"), "success")

        # Step 6: Done (Final hang-up)
        done_result = done()
        # The 'done' function should return an empty dictionary.
        self.assertIsInstance(done_result, str)
        self.assertEqual(done_result, "")