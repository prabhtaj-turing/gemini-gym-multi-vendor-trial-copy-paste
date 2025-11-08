import json
import unittest
from typing import Dict, Any

from common_utils.base_case import BaseTestCaseWithErrorHandler

# Relative imports for the service's API and Simulation Engine
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
    Integration test suite for the CES Loyalty Auth service, covering the
    full customer authentication and offer enrollment workflow.
    """

    def setUp(self):
        """
        Sets up the necessary mock database state for the integration test.
        This method is run before each test case.
        """
        # Per instruction 4: Create an empty DB with keys from the schema.
        # This approach avoids loading default data from files, ensuring a clean slate.
        db.DB.clear()
        db.DB.update(
            {
                "CONVERSATION_STATUS": None,
                "SESSION_STATUS": None,
                "AUTH_RESULT": None,
                "AUTH_STATUS": None,
                "OFFER_ENROLLMENT": None,
                "PROFILE_BEFORE_AUTH": {},
                "PROFILE_AFTER_AUTH": {},
                "use_real_datastore": False,
                "_end_of_conversation_status": {},
            }
        )

        # Define common test data to be used across setup and test execution
        self.account_number = "ACC987654321"
        self.offer_id = "LOYALTY15OFF"
        self.session_id = "session-test-integration-12345"
        self.customer_name = "John Doe"

        # Setup data for get_pre_authentication_call_data
        pre_auth_data: Dict[str, Any] = {
            "sessionInfo": {
                "parameters": {
                    "hasMtnLoyaltyOffers": True,
                    "availablePerks": [{"perkName": "Free Movie Ticket"}],
                    "accountNumber": self.account_number,
                    "status": "Success",
                    "statusCode": "200",
                    "customerName": self.customer_name,
                    "preferredFirstName": "John",
                    "firstName": "John",
                    "statusMessage": "Pre-authentication data retrieved.",
                    "loyaltyOffersStatusCode": "success",
                    "loyaltyOffers": [
                        {
                            "OfferDesc": "15% Loyalty Discount",
                            "offerOrder": "1",
                            "offerType": "DISCOUNT",
                            "OfferID": self.offer_id,
                        }
                    ],
                    "unlimitedPlanPerks": [],
                    "sundayMobileValueProposition": {"title": "Sunday Value"},
                    "sundayMobileOST": {"title": "Sunday OST"},
                    "autoPayPaperFreeDiscountAmountInfo": {"amount": "5.00"},
                    "myPlanPricingDetails": {"Unlimited Plan": {"price": "75.00"}},
                    "myPlanPerks": {"myplan_perks": []},
                    "myPlanFeatures": {"Unlimited Plan": ["Unlimited Talk & Text"]},
                }
            }
        }
        utils.set_preauth_data(pre_auth_data)

        # Setup data for manage_customer_authentication (simulating a successful auth)
        auth_result_data: Dict[str, Any] = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATED",
                    "sessionId": self.session_id,
                    "statusMessage": "Authentication Successful.",
                    "statusCode": "200",
                    "sessionMap": {
                        "adaptiveAuthentication": json.dumps({"authstatus": "ACCEPT"})
                    },
                }
            }
        }
        utils.set_auth_result(auth_result_data)

        # Setup data for get_authenticated_customer_profile
        customer_profile_data: Dict[str, Any] = {
            "customerProfile": {
                "customerName": self.customer_name,
                "numberOfLines": "1",
                "accountNumber": self.account_number,
                "lines": [
                    {
                        "mtn": "5555551001",
                        "mtnStatus": {"isActive": True},
                        "equipmentInfos": {"deviceInfo": {"displayName": "Galaxy S24"}},
                        "pricePlanInfo": {
                            "planId": "P001",
                            "effectiveDate": "2024-01-01",
                            "planDisplayName": "Unlimited Welcome",
                        },
                    }
                ],
                "customerFirstName": "John",
                "customerLastName": "Doe",
                "greetByName": "John",
                "customerRole": "Account Owner",
                "eligibleForAutopay": "true",
                "autopayDiscountAmount": "10.00",
            }
        }
        utils.set_customer_profile(customer_profile_data)

        # Per instruction 5: Validate the complete DB state against the Pydantic model
        try:
            models.CesLoyaltyAuthDBModel(**db.get_minified_state())
        except Exception as e:
            self.fail(f"DB setup failed Pydantic validation: {e}")

    def test_integration_workflow(self):
        """
        Tests the end-to-end workflow from pre-authentication to offer enrollment
        and call completion.
        """
        # Step 1: get_pre_authentication_call_data
        pre_auth_response = get_pre_authentication_call_data()
        self.assertIsNotNone(
            pre_auth_response, "get_pre_authentication_call_data should return a response"
        )
        pre_auth_params = pre_auth_response.get("sessionInfo", {}).get("parameters", {})
        self.assertEqual(pre_auth_params.get("accountNumber"), self.account_number)
        self.assertEqual(pre_auth_params.get("customerName"), self.customer_name)
        self.assertTrue(pre_auth_params.get("hasMtnLoyaltyOffers"))

        retrieved_account_number = pre_auth_params.get("accountNumber")
        retrieved_offer_id = pre_auth_params.get("loyaltyOffers", [{}])[0].get("OfferID")

        # Step 2: manage_customer_authentication (following DI flow)
        # Step 2a: Initialize authentication (send SMS)
        auth_init_response = manage_customer_authentication(authstate="AUTHENTICATION_INIT")
        self.assertIsNotNone(
            auth_init_response, "manage_customer_authentication INIT should return a response"
        )
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
                    "authstate": "ACCEPT",
                    "sessionId": "S123",
                    "statusMessage": "Success",
                }
            }
       }
        utils.set_auth_result(auth_result)

        # Step 2b: Check authentication status (simulating user interaction with link)
        auth_status_response = manage_customer_authentication(authstate="AUTHENTICATION_STATUS")
        self.assertIsNotNone(
            auth_status_response, "manage_customer_authentication STATUS should return a response"
        )
        auth_status_params = auth_status_response.get("sessionInfo", {}).get("parameters", {})
        self.assertEqual(auth_status_params.get("authstate"), "ACCEPT")
        adaptive_auth_str = auth_status_params.get("sessionMap", {}).get("adaptiveAuthentication")
        self.assertIsNotNone(adaptive_auth_str, "adaptiveAuthentication string should be present")
        adaptive_auth_data = json.loads(adaptive_auth_str)
        auth_status = adaptive_auth_data.get("authstatus")
        self.assertEqual(auth_status, "ACCEPT")

        # Step 3: get_authenticated_customer_profile
        profile_response = get_authenticated_customer_profile(authstatus=auth_status)
        self.assertIsNotNone(
            profile_response, "get_authenticated_customer_profile should return a response"
        )
        customer_profile = profile_response.get("customerProfile", {})
        self.assertEqual(customer_profile.get("accountNumber"), self.account_number)
        self.assertEqual(customer_profile.get("customerName"), self.customer_name)
        self.assertEqual(len(customer_profile.get("lines", [])), 1)

        # Step 4: enroll_in_offer
        enrollment_response = enroll_in_offer(
            accountNumber=retrieved_account_number, offerId=retrieved_offer_id
        )
        self.assertIsNotNone(enrollment_response, "enroll_in_offer should return a response")
        self.assertEqual(
            enrollment_response.get("status"), "success", "Enrollment status should be 'success' for success"
        )

        # Step 5: record_call_outcome_and_disconnect
        summary = "Customer accepted and enrolled in loyalty offer"
        outcome_response = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT",
            dispositionCode="PROMO_ACCEPTED",
        )
        self.assertIsNotNone(
            outcome_response, "record_call_outcome_and_disconnect should return a response"
        )
        self.assertEqual(outcome_response.get("status"), "success")

        # Step 6: done
        done_response = done()
        self.assertIsNotNone(done_response, "done should return a response")
        self.assertEqual(done_response, "", "done function should return an empty string")