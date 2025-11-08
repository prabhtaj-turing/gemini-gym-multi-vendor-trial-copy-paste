import json
import unittest
from typing import Dict, Any

# Assuming common_utils is available in the python path
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Relative imports as per instructions
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
    Integration test for the CES Loyalty Auth happy path workflow.
    It simulates a complete customer interaction from start to finish.
    """

    def setUp(self) -> None:
        """
        Set up the mock database with required data for the test workflow.
        This method prepares the DB state for each step of the interaction,
        then validates the entire DB against the Pydantic model.
        """
        super().setUp()
        # Per instructions, reset the DB to a clean state
        db.reset_db()

        # 1. Prepare data for the `get_pre_authentication_call_data` function
        self.account_number = "ACC987654321"
        self.offer_id = "OFFER12345"
        self.customer_name = "Jane Doe"

        preauth_data: Dict[str, Any] = {
            "sessionInfo": {
                "parameters": {
                    "hasMtnLoyaltyOffers": True,
                    "availablePerks": [{"perk_name": "Disney Bundle"}],
                    "accountNumber": self.account_number,
                    "status": "Success",
                    "statusCode": "200",
                    "customerName": self.customer_name,
                    "preferredFirstName": "Jane",
                    "firstName": "Jane",
                    "statusMessage": "Pre-authentication data retrieved successfully.",
                    "loyaltyOffersStatusCode": "200",
                    "loyaltyOffers": [
                        {
                            "OfferDesc": "$10 Loyalty Discount",
                            "offerOrder": "1",
                            "offerType": "DISCOUNT",
                            "OfferID": self.offer_id,
                        }
                    ],
                    "unlimitedPlanPerks": [],
                    "sundayMobileValueProposition": {
                        "title": "Value Prop",
                        "lastUpdated": "2024-01-01",
                        "introduction": {
                            "headline": "Welcome",
                            "description": "Intro",
                            "valueStatement": "Best value",
                            "launchUpdatesLink": {
                                "text": "Learn more"
                            }
                        },
                        "howItWorks": {
                            "title": "How it works",
                            "guarantees": []
                        },
                        "quickPitch": {
                            "title": "Quick Pitch",
                            "description": "Pitch description",
                            "pitch": "It works."
                        }
                    },
                    "sundayMobileOST": {"title": "OST Title", "content": "Content"},
                    "autoPayPaperFreeDiscountAmountInfo": {
                        "discountAmount": "10.00"
                    },
                    "myPlanPricingDetails": {"Plan A": {"price": "50.00"}},
                    "myPlanPerks": {"myplan_perks": []},
                    "myPlanFeatures": {"Plan A": ["Feature 1"]},
                }
            }
        }
        utils.set_preauth_data(preauth_data)

        # 2. Prepare data for the `manage_customer_authentication` function
        # The key is the 'adaptiveAuthentication' JSON string which indicates success
        auth_success_payload = json.dumps({"authstatus": "ACCEPT"})
        auth_result_data: Dict[str, Any] = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_SUCCESS",
                    "sessionId": "test-session-id-12345",
                    "statusMessage": "Authentication successful.",
                    "statusCode": "200",
                    "sessionMap": {"adaptiveAuthentication": auth_success_payload},
                }
            }
        }
        utils.set_auth_result(auth_result_data)
        utils.update_auth_status()  # This processes the result and sets AUTH_STATUS

        # 3. Prepare data for the `get_authenticated_customer_profile` function
        customer_profile_data: Dict[str, Any] = {
            "customerProfile": {
                "customerName": self.customer_name,
                "numberOfLines": "1",
                "accountNumber": self.account_number,
                "lines": [
                    {
                        "mtn": "5551234567",
                        "mtnStatus": {"isActive": True},
                        "equipmentInfos": {},
                        "pricePlanInfo": {
                            "planId": "PLAN01",
                            "effectiveDate": "2023-01-01",
                            "planDisplayName": "Unlimited Plus",
                        },
                    }
                ],
                "autopayDiscountAmount": "10.00",
                "eligibleForAutopay": "true",
                "customerRole": "Account Holder",
                "greetByName": "Jane",
                "customerFirstName": "Jane",
                "customerLastName": "Doe",
                "paymentInfo": {"enrolledInAutopay": True},
            }
        }
        utils.set_customer_profile(customer_profile_data)

        # 4. Final DB state validation against the Pydantic model
        db_state = db.get_minified_state()
        models.CesLoyaltyAuthDBModel(**db_state)

    def test_integration_workflow(self) -> None:
        """
        Executes and verifies the full toolchain workflow for a successful
        loyalty offer enrollment.
        """
        # Step 1: Get Pre-Authentication Call Data
        pre_auth_response = get_pre_authentication_call_data()
        self.assertIsNotNone(pre_auth_response, "Pre-auth response should not be None")
        pre_auth_params = pre_auth_response["sessionInfo"]["parameters"]
        self.assertEqual(pre_auth_params["accountNumber"], self.account_number)
        self.assertEqual(pre_auth_params["customerName"], self.customer_name)
        self.assertTrue(pre_auth_params["hasMtnLoyaltyOffers"])
        loyalty_offers = pre_auth_params["loyaltyOffers"]
        self.assertEqual(len(loyalty_offers), 1)
        offer_id_from_api = loyalty_offers[0]["OfferID"]
        self.assertEqual(offer_id_from_api, self.offer_id)

        # Step 2: Manage Customer Authentication (following DI flow)
        # Step 2a: Initialize authentication (send SMS)
        auth_init_response = manage_customer_authentication(authstate="AUTHENTICATION_INIT")
        self.assertIsNotNone(auth_init_response, "Auth INIT response should not be None")
        auth_init_params = auth_init_response["sessionInfo"]["parameters"]
        self.assertEqual(auth_init_params["authstate"], "AUTHENTICATION_INIT")
        self.assertEqual(auth_init_params["statusCode"], "200")
        self.assertEqual(auth_init_params["statusMessage"], "Authentication SMS sent successfully")
        
        # Step 2b: Check authentication status (simulating user interaction with link)
        utils.set_auth_result({
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_SUCCESS",
                    "sessionId": "test-session-id-12345",
                    "statusMessage": "Authentication successful.",
                    "statusCode": "200",
                    "sessionMap": {"adaptiveAuthentication": '{"authstatus": "ACCEPT"}'},
                }
            }
        })
        utils.update_auth_status()
        auth_status_response = manage_customer_authentication(authstate="AUTHENTICATION_STATUS")
        self.assertIsNotNone(auth_status_response, "Auth STATUS response should not be None")
        auth_status_params = auth_status_response["sessionInfo"]["parameters"]
        self.assertEqual(auth_status_params["authstate"], "AUTHENTICATION_SUCCESS")
        adaptive_auth_data = json.loads(auth_status_params["sessionMap"]["adaptiveAuthentication"])
        self.assertEqual(adaptive_auth_data["authstatus"], "ACCEPT")

        # Step 3: Get Authenticated Customer Profile
        profile_response = get_authenticated_customer_profile(authstatus="ACCEPT")
        self.assertIsNotNone(profile_response, "Profile response should not be None")
        customer_profile = profile_response["customerProfile"]
        account_number_from_api = customer_profile["accountNumber"]
        self.assertEqual(account_number_from_api, self.account_number)
        self.assertEqual(customer_profile["customerName"], self.customer_name)

        # Step 4: Enroll in Offer
        enrollment_response = enroll_in_offer(
            accountNumber=account_number_from_api, offerId=offer_id_from_api
        )
        self.assertIsNotNone(enrollment_response, "Enrollment response should not be None")
        self.assertEqual(enrollment_response["status"], "success", "Enrollment status should be 'success'")
        enrollment_record = db.DB["OFFER_ENROLLMENT"]
        self.assertIsNotNone(enrollment_record, "Enrollment record should exist in DB")
        self.assertEqual(enrollment_record["accountNumber"], self.account_number)
        self.assertEqual(enrollment_record["offerId"], self.offer_id)

        # Step 5: Record Call Outcome and Disconnect
        summary = "Customer Jane Doe accepted the loyalty offer and was enrolled"
        disconnect_response = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT",
            dispositionCode="PROMO_ACCEPTED",
        )
        self.assertIsNotNone(disconnect_response, "Disconnect response should not be None")
        self.assertEqual(disconnect_response["status"], "success")
        conversation_status = db.DB["CONVERSATION_STATUS"]
        self.assertIsNotNone(conversation_status, "Conversation status should exist in DB")
        self.assertEqual(conversation_status["session_params"]["dispositionCode"], "PROMO_ACCEPTED")

        # Step 6: End the session
        done_response = done()
        self.assertIsNotNone(done_response, "Done response should not be None")
        self.assertEqual(done_response, "")
        session_status = db.DB["SESSION_STATUS"]
        self.assertIsNotNone(session_status, "Session status should exist in DB")
        self.assertEqual(session_status["status"], "done")