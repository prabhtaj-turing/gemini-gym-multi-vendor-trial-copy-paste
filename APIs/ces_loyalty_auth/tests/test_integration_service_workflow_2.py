import json
import unittest
from pydantic import ValidationError

# Relative imports for the service's API functions
from .. import (
    done,
    enroll_in_offer,
    get_authenticated_customer_profile,
    get_pre_authentication_call_data,
    manage_customer_authentication,
    record_call_outcome_and_disconnect,
    fail)

# Relative imports for the simulation engine components
from ..SimulationEngine import db, models, utils

# Import base test case for error handling
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestCesLoyaltyAuthIntegration(BaseTestCaseWithErrorHandler):
    """
    Integration test suite for the CES Loyalty Auth service workflow.

    This test covers the successful path where a customer is authenticated,
    retrieves their profile, enrolls in a loyalty offer, and the call is
    concluded.
    """

    def setUp(self):
        """
        Set up the mock database with necessary data for the integration test.

        This method initializes an empty database, prepares structured data for
        pre-authentication, authentication, and customer profiles, and uses
        the provided utility functions to populate the database state.
        Finally, it validates the entire database state against the Pydantic model.
        """
        # 1. Create an empty DB with the required schema
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

        # 2. Define test data variables
        self.account_number = "9876543210"
        self.offer_id = "LOYALTY_DISCOUNT_15"
        self.session_id = "int-test-session-abc-123"
        self.customer_name = "Jane Smith"
        self.customer_first_name = "Jane"

        # 3. Prepare mock data structures for each API response
        pre_auth_data = {
            "sessionInfo": {
                "parameters": {
                    "hasMtnLoyaltyOffers": True,
                    "availablePerks": [{"perkName": "InternationalCalling"}],
                    "accountNumber": self.account_number,
                    "status": "Success",
                    "statusCode": "200",
                    "customerName": self.customer_name,
                    "preferredFirstName": self.customer_first_name,
                    "firstName": self.customer_first_name,
                    "statusMessage": "Pre-authentication data retrieved successfully.",
                    "loyaltyOffersStatusCode": "0",
                    "loyaltyOffers": [
                        {
                            "OfferDesc": "$15 off for being a loyal customer",
                            "offerOrder": "1",
                            "offerType": "DISCOUNT",
                            "OfferID": self.offer_id,
                        }
                    ],
                    "unlimitedPlanPerks": [[]],
                    "sundayMobileValueProposition": {"title": "Sunday Ticket"},
                    "sundayMobileOST": {"title": "Special Offer"},
                    "autoPayPaperFreeDiscountAmountInfo": {"discount": "5.00"},
                    "myPlanPricingDetails": {"Go5G Plus": {"price": "90.00"}},
                    "myPlanPerks": {
                        "myplan_perks": [
                            {
                                "perk": "Netflix",
                                "description": "Netflix ON US",
                                "monthly_cost": "0.00",
                                "monthly_value": "15.49",
                                "savings": "15.49",
                            }
                        ]
                    },
                    "myPlanFeatures": {"Go5G Plus": ["Unlimited Talk & Text"]},
                }
            }
        }

        successful_auth_data = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_SUCCESS",
                    "sessionId": self.session_id,
                    "statusMessage": "Customer authenticated successfully.",
                    "statusCode": "200",
                    "sessionMap": {
                        "adaptiveAuthentication": json.dumps({"authstatus": "ACCEPT"})
                    },
                }
            }
        }

        authenticated_profile_data = {
            "customerProfile": {
                "customerName": self.customer_name,
                "numberOfLines": "1",
                "accountNumber": self.account_number,
                "lines": [
                    {
                        "mtn": "555-867-5309",
                        "mtnStatus": {"isActive": True},
                        "equipmentInfos": {"deviceInfo": {"displayName": "iPhone 15"}},
                        "pricePlanInfo": {
                            "planId": "G5GP",
                            "effectiveDate": "2023-10-01T00:00:00Z",
                            "planDisplayName": "Go5G Plus",
                        },
                        "mobileInfoAttributes": {
                            "accessRoles": {"owner": True, "manager": False, "member": False}
                        },
                    }
                ],
                "greetByName": self.customer_first_name,
                "customerFirstName": self.customer_first_name,
                "customerLastName": "Smith",
                "customerRole": "Account Owner",
            }
        }

        # 4. Use utils to populate the DB
        utils.set_preauth_data(pre_auth_data)
        utils.set_auth_result(successful_auth_data)
        utils.update_auth_status()  # Crucial step to process auth result
        utils.set_customer_profile(authenticated_profile_data)

        # 5. Validate the entire DB state
        try:
            models.CesLoyaltyAuthDBModel.model_validate(db.get_minified_state())
        except ValidationError as e:
            self.fail(f"Database setup failed Pydantic validation: {e}")

    def test_successful_enrollment_workflow(self):
        """
        Tests the full, successful toolchain workflow from start to finish.
        """
        # Step 1: get_pre_authentication_call_data
        pre_auth_response = get_pre_authentication_call_data()
        self.assertIsNotNone(pre_auth_response, "Pre-auth response should not be None")
        pre_auth_params = pre_auth_response.get("sessionInfo", {}).get("parameters", {})
        self.assertEqual(
            pre_auth_params.get("accountNumber"),
            self.account_number)
        self.assertTrue(
            pre_auth_params.get("hasMtnLoyaltyOffers"))
        loyalty_offers = pre_auth_params.get("loyaltyOffers", [])
        self.assertEqual(
            len(loyalty_offers), 1, "There should be one loyalty offer"
        )
        retrieved_offer_id = loyalty_offers[0].get("OfferID")
        self.assertEqual(
            retrieved_offer_id,
            self.offer_id)

        # Step 2: manage_customer_authentication (following DI flow)
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
                    "statusMessage": "Customer authenticated successfully.",
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
        self.assertEqual(auth_status_params.get("authstate"), "AUTHENTICATION_SUCCESS")
        adaptive_auth_str = auth_status_params.get("sessionMap", {}).get(
            "adaptiveAuthentication", "{}"
        )
        adaptive_auth_data = json.loads(adaptive_auth_str)
        self.assertEqual(
            adaptive_auth_data.get("authstatus"),
            "ACCEPT")

        # Step 3: get_authenticated_customer_profile
        profile_response = get_authenticated_customer_profile(authstatus="ACCEPT")
        self.assertIsNotNone(profile_response, "Profile response should not be None")
        customer_profile = profile_response.get("customerProfile", {})
        retrieved_account_number = customer_profile.get("accountNumber")
        self.assertEqual(
            retrieved_account_number,
            self.account_number)
        self.assertEqual(
            customer_profile.get("customerName"),
            self.customer_name)

        # Step 4: enroll_in_offer
        enroll_response = enroll_in_offer(
            accountNumber=retrieved_account_number, offerId=retrieved_offer_id
        )
        self.assertIsNotNone(enroll_response, "Enrollment response should not be None")
        self.assertEqual(
            enroll_response.get("status"),
            "success")

        # Step 5: record_call_outcome_and_disconnect
        summary = "Customer successfully authenticated and enrolled in loyalty offer"
        outcome_response = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT",
            dispositionCode="PROMO_ACCEPTED",
        )
        self.assertIsNotNone(
            outcome_response, "Call outcome response should not be None"
        )
        self.assertEqual(
            outcome_response.get("status"),
            "success")

        # Step 6: done
        done_response = done()
        self.assertIsNotNone(done_response, "Done response should not be None")
        self.assertEqual(
            done_response, "", "Done response should be an empty string"
        )