import json
import unittest

# Assuming common_utils is in the python path
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Relative imports for the service and its simulation engine
from .. import (
    done,
    enroll_in_offer,
    get_authenticated_customer_profile,
    get_pre_authentication_call_data,
    manage_customer_authentication,
    record_call_outcome_and_disconnect,
    fail)
from ..SimulationEngine import db, utils, models


class CesLoyaltyAuthIntegrationTest(BaseTestCaseWithErrorHandler):
    """
    Integration test suite for the 'ces_loyalty_auth' service.
    This test covers the successful workflow of authenticating a customer,
    enrolling them in a loyalty offer, and disconnecting the call.
    """

    def setUp(self):
        """
        Set up the mock database with required data for the test workflow.
        This method configures the database state that the tool functions
        will read from during the test execution.
        """
        super().setUp()
        db.reset_db()  # Ensure a clean state for each test

        # --- Test Data Constants ---
        self.ACCOUNT_NUMBER = "987654321"
        self.CUSTOMER_NAME = "Jane Doe"
        self.OFFER_ID = "LOYALTY123"

        # --- Setup for get_pre_authentication_call_data ---
        pre_auth_data = {
            "sessionInfo": {
                "parameters": {
                    "accountNumber": self.ACCOUNT_NUMBER,
                    "customerName": self.CUSTOMER_NAME,
                    "firstName": "Jane",
                    "preferredFirstName": "Janey",
                    "hasMtnLoyaltyOffers": True,
                    "loyaltyOffers": [
                        {
                            "OfferID": self.OFFER_ID,
                            "OfferDesc": "Special Discount Offer",
                            "offerOrder": "1",
                            "offerType": "DISCOUNT",
                        }
                    ],
                    "status": "Success",
                    "statusCode": "200",
                    "statusMessage": "Data retrieved successfully.",
                    "loyaltyOffersStatusCode": "200",
                    "availablePerks": [{"perkName": "Free Streaming"}],
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

        # --- Setup for manage_customer_authentication ---
        # This data simulates a successful authentication response.
        auth_result_data = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_SUCCESS",
                    "sessionId": "mock-session-12345",
                    "statusMessage": "Authentication successful.",
                    "sessionMap": {
                        "adaptiveAuthentication": json.dumps({"authstatus": "ACCEPT"})
                    },
                }
            }
        }
        utils.set_auth_result(auth_result_data)

        # --- Setup for get_authenticated_customer_profile ---
        # This data represents the detailed profile returned after successful auth.
        customer_profile_data = {
            "customerProfile": {
                "accountNumber": self.ACCOUNT_NUMBER,
                "customerName": self.CUSTOMER_NAME,
                "customerFirstName": "Jane",
                "customerLastName": "Doe",
                "greetByName": "Jane",
                "customerRole": "Account Holder",
                "numberOfLines": "1",
                "lines": [
                    {
                        "mtn": "5555551234",
                        "mtnStatus": {"isActive": True},
                        "equipmentInfos": {
                            "deviceInfo": {"displayName": "SuperPhone 2000"}
                        },
                        "pricePlanInfo": {
                            "planId": "P001",
                            "effectiveDate": "2023-01-01T00:00:00Z",
                            "planDisplayName": "Unlimited Everything",
                        },
                    }
                ],
            }
        }
        utils.set_customer_profile(customer_profile_data)

        try:
            # Directly validate the parts of the DB that are set
            if db.DB["PROFILE_BEFORE_AUTH"]:
                models.GetPreAuthenticationCallDataResponse(
                    **db.DB["PROFILE_BEFORE_AUTH"]
                )
            if db.DB["AUTH_RESULT"]:
                models.ManageCustomerAuthenticationResponse(**db.DB["AUTH_RESULT"])
            if db.DB["PROFILE_AFTER_AUTH"]:
                models.GetAuthenticatedCustomerProfileResponse(
                    **db.DB["PROFILE_AFTER_AUTH"]
                )
        except Exception as e:
            self.fail(f"DB state validation failed: {e}")

    def test_enrollment_workflow(self):
        """
        Tests the full workflow:
        1. Get pre-auth data and identify a loyalty offer.
        2. Authenticate the customer successfully.
        3. Retrieve the authenticated customer's profile.
        4. Enroll the customer in the identified offer.
        5. Record the call outcome and disconnect.
        6. End the session.
        """
        # Step 1: Get Pre-Authentication Data
        pre_auth_response = get_pre_authentication_call_data()
        self.assertIsNotNone(pre_auth_response, "Pre-auth response should not be None")

        pre_auth_params = pre_auth_response.get("sessionInfo", {}).get("parameters", {})
        self.assertEqual(pre_auth_params.get("accountNumber"), self.ACCOUNT_NUMBER)
        self.assertTrue(pre_auth_params.get("hasMtnLoyaltyOffers"))

        loyalty_offers = pre_auth_params.get("loyaltyOffers", [])
        self.assertGreater(len(loyalty_offers), 0, "Should have loyalty offers")

        account_number_from_pre_auth = pre_auth_params.get("accountNumber")
        offer_id_from_pre_auth = loyalty_offers[0].get("OfferID")
        self.assertEqual(offer_id_from_pre_auth, self.OFFER_ID)

        # Step 2: Manage Customer Authentication (following DI flow)
        # Step 2a: Initialize authentication (send SMS)
        auth_init_response = manage_customer_authentication(authstate="AUTHENTICATION_INIT")
        self.assertIsNotNone(auth_init_response, "Auth INIT response should not be None")
        auth_init_params = auth_init_response.get("sessionInfo", {}).get("parameters", {})
        self.assertEqual(auth_init_params.get("authstate"), "AUTHENTICATION_INIT")
        self.assertEqual(auth_init_params.get("statusCode"), "200")
        self.assertEqual(auth_init_params.get("statusMessage"), "Authentication SMS sent successfully")
        
        auth_result = {
            "sessionInfo": {
                "parameters": {
                    "sessionMap": {
                        "adaptiveAuthentication": '{"authstatus": "ACCEPT"}'
                    },
                    "authstate": "AUTHENTICATION_SUCCESS",
                    "sessionId": "S123",
                    "statusMessage": "Success",
                }
            }
        }
        utils.set_auth_result(auth_result)
        utils.update_auth_status()
        # Step 2b: Check authentication status (simulating user interaction with link)
        auth_status_response = manage_customer_authentication(authstate="AUTHENTICATION_STATUS")
        self.assertIsNotNone(auth_status_response, "Auth STATUS response should not be None")
        auth_status_params = auth_status_response.get("sessionInfo", {}).get("parameters", {})
        self.assertEqual(auth_status_params.get("authstate"), "AUTHENTICATION_SUCCESS")

        # Manually update internal auth status to simulate successful authentication
        # for subsequent tool calls.
        utils.update_auth_status()
        self.assertEqual(db.DB.get("AUTH_STATUS"), "ACCEPT")

        # Step 3: Get Authenticated Customer Profile
        profile_response = get_authenticated_customer_profile(authstatus="ACCEPT")
        self.assertIsNotNone(profile_response, "Profile response should not be None")

        customer_profile = profile_response.get("customerProfile", {})
        self.assertEqual(customer_profile.get("accountNumber"), self.ACCOUNT_NUMBER)
        self.assertEqual(customer_profile.get("customerName"), self.CUSTOMER_NAME)

        # Step 4: Enroll in Offer
        enrollment_response = enroll_in_offer(
            accountNumber=account_number_from_pre_auth,
            offerId=offer_id_from_pre_auth,
        )
        self.assertIsNotNone(
            enrollment_response, "Enrollment response should not be None"
        )
        self.assertEqual(
            enrollment_response.get("status"),
            "success")

        # Step 5: Record Call Outcome and Disconnect
        disconnect_response = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT",
            dispositionCode="PROMO_ACCEPTED",
        )
        self.assertIsNotNone(disconnect_response, "Disconnect response should not be None")
        self.assertEqual(disconnect_response.get("status"), "success")

        # Step 6: Done (Final hang-up call)
        done_response = done()
        self.assertIsNotNone(done_response, "Done response should not be None")
        self.assertEqual(done_response, "", "Done response should be an empty string")