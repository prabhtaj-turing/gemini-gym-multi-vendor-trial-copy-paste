import json
import unittest

import pytest
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Relative imports for the service's modules
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
        Set up the test environment and database state before each test.
        """
        # 1. Reset the database to a clean state
        db.reset_db()

        # 2. Define and set pre-authentication data
        # This data will be returned by the first call in the workflow.
        pre_auth_data = {
            "sessionInfo": {
                "parameters": {
                    "hasMtnLoyaltyOffers": True,
                    "availablePerks": [{"perkName": "Disney Bundle"}],
                    "accountNumber": "ACC987654321",
                    "status": "Success",
                    "statusCode": "200",
                    "customerName": "Jane Doe",
                    "preferredFirstName": "Jane",
                    "firstName": "Jane",
                    "statusMessage": "Pre-authentication data retrieved successfully.",
                    "loyaltyOffersStatusCode": "200",
                    "loyaltyOffers": [
                        {
                            "OfferDesc": "$10 Loyalty Discount",
                            "offerOrder": "1",
                            "offerType": "DISCOUNT",
                            "OfferID": "LOYALTYOFFER123",
                        }
                    ],
                    "unlimitedPlanPerks": [],
                    "sundayMobileValueProposition": {
                        "title": "Sunday Mobile",
                        "lastUpdated": "2024-01-01",
                        "introduction": {
                            "headline": "Welcome to Sunday Mobile",
                            "description": "Intro text",
                            "valueStatement": "Best value guarantee",
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
                            "pitch": "How it works text"
                        }
                    },
                    "sundayMobileOST": {"title": "OST", "content": "Content text"},
                    "autoPayPaperFreeDiscountAmountInfo": {
                        "discount": "$10"
                    },
                    "myPlanPricingDetails": {"Plan A": {"price": "$50"}},
                    "myPlanPerks": {"myplan_perks": []},
                    "myPlanFeatures": {"Plan A": ["Unlimited Data"]},
                }
            }
        }
        utils.set_preauth_data(pre_auth_data)

        # 3. Define and set the expected successful authentication result.
        # This simulates the state after manage_customer_authentication succeeds.
        auth_result_data = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_SUCCESS",
                    "sessionId": "test-session-12345",
                    "statusMessage": "Authentication successful.",
                    "sessionMap": {
                        "adaptiveAuthentication": json.dumps({"authstatus": "ACCEPT"})
                    },
                }
            }
        }
        utils.set_auth_result(auth_result_data)
        utils.update_auth_status()  # Update the simplified AUTH_STATUS key

        # 4. Define and set the authenticated customer profile.
        # This data will be returned by get_authenticated_customer_profile.
        authenticated_profile_data = {
            "customerProfile": {
                "customerName": "Jane Doe",
                "numberOfLines": "1",
                "accountNumber": "ACC987654321",
                "lines": [
                    {
                        "mtn": "5551234567",
                        "mtnStatus": {"isActive": True},
                        "equipmentInfos": {
                            "deviceInfo": {
                                "displayName": "iPhone 15",
                                "category": {"smartphone": True},
                            }
                        },
                        "pricePlanInfo": {
                            "planId": "P001",
                            "effectiveDate": "2023-01-01",
                            "planDisplayName": "Unlimited Premium",
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
                "autopayDiscountAmount": "10.00",
                "eligibleForAutopay": "true",
                "customerRole": "Owner",
                "greetByName": "Jane",
                "customerFirstName": "Jane",
                "customerLastName": "Doe",
                "paymentInfo": {
                    "enrolledInAutopay": True,
                    "lastPaymentDate": "2024-05-15",
                    "lastPaymentAmount": "95.50",
                },
            }
        }
        utils.set_customer_profile(authenticated_profile_data)
        
        # 5. Validate the entire DB state against the Pydantic model.
        try:
            models.CesLoyaltyAuthDBModel(**db.get_minified_state())
        except Exception as e:
            pytest.fail(f"DB state validation failed after setup: {e}")

    def test_successful_enrollment_workflow(self):
        """
        Tests the complete end-to-end workflow for a successful offer enrollment.
        """
        # Step 1: Get pre-authentication call data
        pre_auth_response = get_pre_authentication_call_data()
        self.assertIsNotNone(pre_auth_response)
        self.assertIn("sessionInfo", pre_auth_response)
        pre_auth_params = pre_auth_response["sessionInfo"]["parameters"]
        self.assertIn("loyaltyOffers", pre_auth_params)
        self.assertGreater(len(pre_auth_params["loyaltyOffers"]), 0)
        
        # Extract data for later steps
        account_number = pre_auth_params["accountNumber"]
        offer_id = pre_auth_params["loyaltyOffers"][0]["OfferID"]
        self.assertEqual(account_number, "ACC987654321")
        self.assertEqual(offer_id, "LOYALTYOFFER123")

        # Step 2: Manage customer authentication (following DI flow)
        # Initialize authentication
        auth_step1 = manage_customer_authentication(authstate="AUTHENTICATION_INIT")
        self.assertIn("sessionInfo", auth_step1)
        self.assertIn("parameters", auth_step1["sessionInfo"])
        
        success_auth_result = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_SUCCESS",
                    "sessionId": "test-session-12345",
                    "statusMessage": "Authentication successful.",
                    "statusCode": "200",
                    "sessionMap": {
                        "adaptiveAuthentication": '{"authstatus": "ACCEPT"}'
                    },
                }
            }
        }
        utils.set_auth_result(success_auth_result)
        utils.update_auth_status()

        # Check authentication status (simulating user interaction with link)
        auth_step2 = manage_customer_authentication(authstate="AUTHENTICATION_STATUS")
        self.assertIn("sessionInfo", auth_step2)
        self.assertEqual(
            auth_step2["sessionInfo"]["parameters"]["authstate"],
            "AUTHENTICATION_SUCCESS"
        )
        
        # Step 3: Get authenticated customer profile (multiple times for robustness)
        for i in range(3):
            profile_response = get_authenticated_customer_profile(authstatus="ACCEPT")
            self.assertIsNotNone(profile_response)
            self.assertIn("customerProfile", profile_response)
            customer_profile = profile_response["customerProfile"]
            self.assertEqual(customer_profile["accountNumber"], account_number)
            self.assertEqual(customer_profile["customerName"], "Jane Doe")

        # Step 4: Enroll in the loyalty offer
        enrollment_response = enroll_in_offer(
            accountNumber=account_number, offerId=offer_id
        )
        self.assertIsNotNone(enrollment_response)
        self.assertEqual(enrollment_response.get("status"), "success")

        # Step 5: Get authenticated customer profile again to confirm state
        final_profile_response = get_authenticated_customer_profile(authstatus="ACCEPT")
        self.assertIsNotNone(final_profile_response)
        self.assertEqual(
            final_profile_response["customerProfile"]["accountNumber"], account_number
        )

        # Step 6: Record the call outcome and disconnect
        summary = "Customer successfully authenticated and enrolled in loyalty offer"
        disconnect_response = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT",
            dispositionCode="PROMO_ACCEPTED")
        self.assertIsNotNone(disconnect_response)
        self.assertEqual(disconnect_response.get("status"), "success")

        # Step 7: Finalize the conversation
        done_response = done()
        self.assertIsNotNone(done_response)
        self.assertEqual(done_response, "")