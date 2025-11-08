import unittest
import json

from common_utils.base_case import BaseTestCaseWithErrorHandler

# Use relative imports to access the service's modules
from .. import (
    done,
    enroll_in_offer,
    get_authenticated_customer_profile,
    get_pre_authentication_call_data,
    manage_customer_authentication,
    record_call_outcome_and_disconnect,
    fail)
from ..SimulationEngine import db, models, utils


class TestCesLoyaltyAuthIntegration(BaseTestCaseWithErrorHandler):
    """
    Integration test suite for the CES Loyalty Auth service workflow.
    """

    def setUp(self):
        """
        Set up the test environment and seed the database.
        This method is called before each test function execution.
        """
        # 1. Reset the database to a clean state
        db.reset_db()

        # 2. Define test data constants
        self.account_number = "ACC987654321"
        self.offer_id = "LOYALTY-SPECIAL-15"
        self.customer_name = "Jane Doe"
        self.session_id = "test-session-12345"

        # 3. Prepare data for seeding the database
        
        # Data for get_pre_authentication_call_data response
        pre_auth_data = {
            "sessionInfo": {
                "parameters": {
                    "hasMtnLoyaltyOffers": True,
                    "availablePerks": [{"perk": "Streaming Bundle"}],
                    "accountNumber": self.account_number,
                    "status": "Success",
                    "statusCode": "200",
                    "customerName": self.customer_name,
                    "preferredFirstName": "Jane",
                    "firstName": "Jane",
                    "statusMessage": "Pre-authentication data retrieved.",
                    "loyaltyOffersStatusCode": "0",
                    "loyaltyOffers": [
                        {
                            "OfferDesc": "$15 Off For 12 Months",
                            "offerOrder": "1",
                            "offerType": "Discount",
                            "OfferID": self.offer_id,
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

        # Data for manage_customer_authentication to simulate successful auth
        auth_result_data = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_SUCCESS",
                    "sessionId": self.session_id,
                    "statusMessage": "Authentication successful.",
                    "sessionMap": {
                        "adaptiveAuthentication": json.dumps(
                            {"authstatus": "ACCEPT"}
                        )
                    },
                }
            }
        }
        
        # Data for get_authenticated_customer_profile response
        post_auth_data = {
            "customerProfile": {
                "customerName": self.customer_name,
                "numberOfLines": "1",
                "accountNumber": self.account_number,
                "lines": [
                    {
                        "mtn": "5551234567",
                        "mtnStatus": {"isActive": True},
                        "equipmentInfos": {
                            "deviceInfo": {"displayName": "SuperPhone 15"}
                        },
                        "pricePlanInfo": {
                            "planId": "PLAN-UNLIMITED-MAX",
                            "effectiveDate": "2023-01-01",
                            "planDisplayName": "Unlimited Max Plan",
                        },
                    }
                ],
                "customerFirstName": "Jane",
                "customerLastName": "Doe",
            }
        }
        
        # 4. Use utility functions to seed the database
        utils.set_preauth_data(pre_auth_data)
        utils.set_auth_result(auth_result_data)
        utils.set_customer_profile(post_auth_data)

        # 5. Validate the entire DB state against the Pydantic model
        try:
            models.CesLoyaltyAuthDBModel(**db.DB)
        except Exception as e:
            self.fail(f"DB state validation failed after setup: {e}")

    def test_successful_enrollment_workflow(self):
        """
        Tests the complete workflow from pre-authentication to offer enrollment
        and call disconnection.
        """
        # Step 1: Get Pre-Authentication Call Data
        pre_auth_response = get_pre_authentication_call_data()
        self.assertIsNotNone(pre_auth_response, "Pre-auth response should not be None")
        
        params = pre_auth_response.get("sessionInfo", {}).get("parameters", {})
        retrieved_account_number = params.get("accountNumber")
        retrieved_offer_id = params.get("loyaltyOffers", [{}])[0].get("OfferID")

        self.assertEqual(retrieved_account_number, self.account_number)
        self.assertEqual(retrieved_offer_id, self.offer_id)

        # Step 2: Manage Customer Authentication (following DI flow)
        # Step 2a: Initialize authentication (send SMS)
        auth_init_response = manage_customer_authentication(authstate="AUTHENTICATION_INIT")
        self.assertIsNotNone(auth_init_response, "Auth INIT response should not be None")
        auth_init_params = auth_init_response.get("sessionInfo", {}).get("parameters", {})
        self.assertEqual(auth_init_params.get("authstate"), "AUTHENTICATION_INIT")
        self.assertEqual(auth_init_params.get("statusCode"), "200")
        self.assertEqual(auth_init_params.get("statusMessage"), "Authentication SMS sent successfully")
        
        # Step 2b: Check authentication status (simulating user interaction with link)
        utils.set_auth_result({
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_SUCCESS",
                    "sessionId": self.session_id,
                    "statusMessage": "Authentication successful.",
                    "statusCode": "200",
                    "sessionMap": {
                        "adaptiveAuthentication": '{"authstatus": "ACCEPT"}'
                    },
                }
            }
        })
        utils.update_auth_status()
        auth_status_response = manage_customer_authentication(authstate="AUTHENTICATION_STATUS")
        self.assertIsNotNone(auth_status_response, "Auth STATUS response should not be None")
        auth_status_params = auth_status_response.get("sessionInfo", {}).get("parameters", {})
        session_map = auth_status_params.get("sessionMap", {})
        adaptive_auth_str = session_map.get("adaptiveAuthentication", "{}")
        auth_status = json.loads(adaptive_auth_str).get("authstatus")
        
        self.assertEqual(auth_status, "ACCEPT", "Authentication status should be ACCEPT")

        # Step 3: Get Authenticated Customer Profile
        profile_response = get_authenticated_customer_profile(authstatus="ACCEPT")
        self.assertIsNotNone(profile_response, "Profile response should not be None")
        
        customer_profile = profile_response.get("customerProfile", {})
        self.assertEqual(customer_profile.get("accountNumber"), self.account_number)
        self.assertEqual(customer_profile.get("customerName"), self.customer_name)

        # Step 4: Enroll in Offer
        enrollment_response = enroll_in_offer(
            accountNumber=retrieved_account_number, offerId=retrieved_offer_id
        )
        self.assertIsNotNone(enrollment_response, "Enrollment response should not be None")
        self.assertEqual(enrollment_response.get("status"), "success", "Enrollment status should be 'success'")

        # Step 5: Record Call Outcome and Disconnect
        summary = "Customer successfully authenticated and enrolled in loyalty offer"
        outcome_response = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT",
            dispositionCode="PROMO_ACCEPTED")
        self.assertIsNotNone(outcome_response, "Outcome response should not be None")
        self.assertEqual(outcome_response.get("status"), "success", "Call outcome status should be 'success'")

        # Step 6: Done (Final hang-up)
        done_response = done()
        self.assertIsNotNone(done_response, "Done response should not be None")
        self.assertEqual(done_response, "", "Done response should be an empty string")