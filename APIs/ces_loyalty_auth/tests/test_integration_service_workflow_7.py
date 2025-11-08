import json
import unittest

from common_utils.base_case import BaseTestCaseWithErrorHandler

# Relative imports for the service's modules
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
        Set up the test environment and mock database state for the workflow.
        """
        # 1. Reset the database to a clean state
        db.reset_db()

        # 2. Define and set pre-authentication data
        # This data will be returned by get_pre_authentication_call_data()
        account_number = "ACC-INTEGRATION-TEST"
        offer_id = "OFFER-LOYAL-INT-TEST"

        preauth_data = {
            "sessionInfo": {
                "parameters": {
                    "hasMtnLoyaltyOffers": True,
                    "availablePerks": [{"perk_name": "Free International Calling"}],
                    "accountNumber": account_number,
                    "status": "Success",
                    "statusCode": "200",
                    "customerName": "Jane Doe",
                    "preferredFirstName": "Jane",
                    "firstName": "Jane",
                    "statusMessage": "Pre-authentication data retrieved successfully.",
                    "loyaltyOffersStatusCode": "200",
                    "loyaltyOffers": [
                        {
                            "OfferDesc": "Integration Test Loyalty Discount",
                            "offerOrder": "1",
                            "offerType": "DISCOUNT",
                            "OfferID": offer_id,
                        }
                    ],
                    "unlimitedPlanPerks": [],
                    "sundayMobileValueProposition": {
                        "title": "Test Prop",
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
                            "pitch": "It works"
                        }
                    },
                    "sundayMobileOST": {"title": "Test OST", "content": "Content"},
                    "autoPayPaperFreeDiscountAmountInfo": {
                        "discountAmount": "5.00"
                    },
                    "myPlanPricingDetails": {"Plan A": {"price": "50.00"}},
                    "myPlanPerks": {"myplan_perks": []},
                    "myPlanFeatures": {"Plan A": ["Feature 1"]},
                }
            }
        }
        utils.set_preauth_data(preauth_data)

        # 3. Define and set the expected authentication result
        # This data will be returned by manage_customer_authentication()
        auth_result_data = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_SUCCESS",
                    "sessionId": "int-test-session-12345",
                    "statusMessage": "Customer successfully authenticated.",
                    "statusCode": "200",
                    "sessionMap": {
                        "adaptiveAuthentication": json.dumps({"authstatus": "ACCEPT"})
                    },
                }
            }
        }
        utils.set_auth_result(auth_result_data)

        # 4. Define and set the authenticated customer profile
        # This data will be returned by get_authenticated_customer_profile()
        customer_profile_data = {
            "customerProfile": {
                "customerName": "Jane Doe",
                "numberOfLines": "1",
                "accountNumber": account_number,
                "lines": [
                    {
                        "mtn": "5558675309",
                        "mtnStatus": {
                            "isActive": True,
                            "isSuspendedWithBilling": False,
                        },
                        "equipmentInfos": {
                            "deviceInfo": {"displayName": "Test Phone"}
                        },
                        "pricePlanInfo": {
                            "planId": "PLAN1",
                            "effectiveDate": "2023-01-01",
                            "planDisplayName": "Test Plan",
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
                "autopayDiscountAmount": "5.00",
                "eligibleForAutopay": "true",
                "customerRole": "Owner",
                "greetByName": "Jane",
                "customerFirstName": "Jane",
                "customerLastName": "Doe",
                "paymentInfo": {
                    "enrolledInAutopay": True,
                    "lastPaymentDate": "2023-10-15",
                    "lastPaymentAmount": "95.00",
                },
            }
        }
        utils.set_customer_profile(customer_profile_data)
        
        # 5. Validate the overall DB state against the Pydantic model
        models.CesLoyaltyAuthDBModel(**db.get_minified_state())

    def test_successful_enrollment_workflow(self):
        """
        Tests the complete successful workflow from pre-auth to offer enrollment
        and call disconnection.
        """
        # Step 1: Get Pre-Authentication Call Data
        pre_auth_result = get_pre_authentication_call_data()
        self.assertIsNotNone(pre_auth_result, "Pre-auth data should not be None")
        
        pre_auth_params = pre_auth_result.get("sessionInfo", {}).get("parameters", {})
        self.assertEqual(pre_auth_params.get("status"), "Success")
        
        account_number = pre_auth_params.get("accountNumber")
        self.assertEqual(account_number, "ACC-INTEGRATION-TEST")
        
        loyalty_offers = pre_auth_params.get("loyaltyOffers", [])
        self.assertTrue(len(loyalty_offers) > 0, "Should have loyalty offers")
        offer_id = loyalty_offers[0].get("OfferID")
        self.assertEqual(offer_id, "OFFER-LOYAL-INT-TEST")

        # Step 2: Manage Customer Authentication (following DI flow)
        # Step 2a: Initialize authentication (send SMS)
        auth_init_result = manage_customer_authentication(authstate="AUTHENTICATION_INIT")
        self.assertIsNotNone(auth_init_result, "Auth INIT result should not be None")
        auth_init_params = auth_init_result.get("sessionInfo", {}).get("parameters", {})
        self.assertEqual(auth_init_params.get("authstate"), "AUTHENTICATION_INIT")
        self.assertEqual(auth_init_params.get("statusCode"), "200")
        self.assertEqual(auth_init_params.get("statusMessage"), "Authentication SMS sent successfully")
        
        # Step 2b: Check authentication status (simulating user interaction with link)
        utils.set_auth_result({
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_SUCCESS",
                    "sessionId": "int-test-session-12345",
                    "statusMessage": "Authentication successful.",
                    "statusCode": "200",
                    "sessionMap": {
                        "adaptiveAuthentication": '{"authstatus": "ACCEPT"}'
                    },
                }
            }
        })
        utils.update_auth_status()
        auth_status_result = manage_customer_authentication(authstate="AUTHENTICATION_STATUS")
        self.assertIsNotNone(auth_status_result, "Auth STATUS result should not be None")
        auth_status_params = auth_status_result.get("sessionInfo", {}).get("parameters", {})
        self.assertEqual(auth_status_params.get("authstate"), "AUTHENTICATION_SUCCESS")
        
        # Verify that the DB's auth status was updated to 'ACCEPT'
        self.assertEqual(db.DB.get("AUTH_STATUS"), "ACCEPT")

        # Step 3: Get Authenticated Customer Profile
        profile_result = get_authenticated_customer_profile(authstatus="ACCEPT")
        self.assertIsNotNone(profile_result, "Profile result should not be None")
        
        customer_profile = profile_result.get("customerProfile", {})
        self.assertEqual(customer_profile.get("accountNumber"), account_number)
        self.assertEqual(customer_profile.get("customerName"), "Jane Doe")

        # Step 4: Enroll in Offer
        enroll_result = enroll_in_offer(accountNumber=account_number, offerId=offer_id)
        self.assertIsNotNone(enroll_result, "Enrollment result should not be None")
        self.assertEqual(enroll_result.get("status"), "success", "Enrollment should be successful")
        
        # Verify that the offer enrollment details were recorded in the DB
        offer_enrollment_db = db.DB.get("OFFER_ENROLLMENT")
        self.assertIsNotNone(offer_enrollment_db, "Offer enrollment should be in DB")
        self.assertEqual(offer_enrollment_db.get("accountNumber"), account_number)
        self.assertEqual(offer_enrollment_db.get("offerId"), offer_id)

        # Step 5: Record Call Outcome and Disconnect
        disconnect_result = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT",
            dispositionCode="PROMO_ACCEPTED",
            preferredLang="E",
        )
        self.assertIsNotNone(disconnect_result, "Disconnect result should not be None")
        self.assertEqual(disconnect_result.get("status"), "success")

        # Verify the conversation status was logged in the DB
        conversation_status_db = db.DB.get("CONVERSATION_STATUS", {})
        self.assertEqual(conversation_status_db.get("status"), "disconnect")
        session_params = conversation_status_db.get("session_params", {})
        self.assertEqual(session_params.get("dispositionCode"), "PROMO_ACCEPTED")

        # Step 6: Done (Final hang-up)
        done_result = done()
        self.assertIsNotNone(done_result, "Done result should not be None")
        self.assertEqual(done_result, "", "Done function should return an empty string")

        # Verify the session status was updated in the DB
        session_status_db = db.DB.get("SESSION_STATUS", {})
        self.assertEqual(session_status_db.get("status"), "done")