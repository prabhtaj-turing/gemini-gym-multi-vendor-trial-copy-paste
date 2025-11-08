import json
import unittest

# This import assumes a project structure where 'common_utils' is a sibling
# to the service's package directory.
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Use relative imports to access the service's API and Simulation Engine modules
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
    full workflow from pre-authentication to offer enrollment and disconnection.
    """

    def setUp(self):
        """
        Set up the mock database with the necessary data for the test workflow.
        This method prepares the initial state that the API functions will read from.
        """
        # Create an empty DB with the default schema.
        db.reset_db()

        # Define common variables to be used across the setup and test.
        self.account_number = "ACC888777666"
        self.offer_id = "LOYALTY2024"
        self.session_id = "test-session-id-12345"
        self.customer_name = "Jane Doe"

        # Prepare data for the get_pre_authentication_call_data function.
        # This data is stored in the DB's PROFILE_BEFORE_AUTH key.
        preauth_data = {
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
                    "statusMessage": "Data retrieved successfully.",
                    "loyaltyOffersStatusCode": "0",
                    "loyaltyOffers": [
                        {
                            "OfferDesc": "$10 monthly discount for 1 year",
                            "offerOrder": "1",
                            "offerType": "Discount",
                            "OfferID": self.offer_id,
                        }
                    ],
                    "unlimitedPlanPerks": [[]],
                    "sundayMobileValueProposition": {"title": "Value Prop"},
                    "sundayMobileOST": {"title": "OST Content"},
                    "autoPayPaperFreeDiscountAmountInfo": {"amount": "10.00"},
                    "myPlanPricingDetails": {"Go5G Plus": {"price": "90.00"}},
                    "myPlanPerks": {"myplan_perks": []},
                    "myPlanFeatures": {"Go5G Plus": ["Netflix On Us"]},
                }
            }
        }
        utils.set_preauth_data(preauth_data)

        # Prepare data for the successful manage_customer_authentication call.
        # This is stored in AUTH_RESULT. The API reads this to formulate its response.
        auth_result_data = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_SUCCESS",
                    "sessionId": self.session_id,
                    "statusMessage": "Authentication successful.",
                    "statusCode": "200",
                    "sessionMap": {
                        "adaptiveAuthentication": json.dumps(
                            {"authstatus": "ACCEPT", "reason": "Authenticated"}
                        )
                    },
                }
            }
        }
        utils.set_auth_result(auth_result_data)

        # Prepare data for the get_authenticated_customer_profile function.
        # This is stored in PROFILE_AFTER_AUTH.
        customer_profile_data = {
            "customerProfile": {
                "customerName": self.customer_name,
                "numberOfLines": "1",
                "accountNumber": self.account_number,
                "lines": [
                    {
                        "mtn": "5558675309",
                        "mtnStatus": {"isActive": True},
                        "equipmentInfos": {
                            "deviceInfo": {"displayName": "Samsung Galaxy S24"}
                        },
                        "pricePlanInfo": {
                            "planId": "P001",
                            "effectiveDate": "2023-01-01",
                            "planDisplayName": "Go5G Plus",
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
                "customerRole": "Owner",
                "greetByName": "Jane",
                "customerFirstName": "Jane",
                "customerLastName": "Doe",
                "autopayDiscountAmount": "10.00",
                "eligibleForAutopay": "Yes",
                "paymentInfo": {"enrolledInAutopay": True},
            }
        }
        utils.set_customer_profile(customer_profile_data)

        # Final step: Validate the entire DB state against the master Pydantic model.
        # This ensures the setup is complete and structurally correct before any tests run.
        try:
            models.CesLoyaltyAuthDBModel(**db.get_minified_state())
        except Exception as e:
            self.fail(f"Database state failed Pydantic validation after setUp: {e}")

    def test_integration_workflow(self):
        """
        Executes and validates the complete toolchain for a successful
        customer authentication and offer enrollment scenario.
        """
        # Step 1: get_pre_authentication_call_data
        pre_auth_res = get_pre_authentication_call_data()
        self.assertIsNotNone(pre_auth_res)
        session_info = pre_auth_res.get("sessionInfo", {})
        params = session_info.get("parameters", {})
        self.assertEqual(params.get("accountNumber"), self.account_number)
        self.assertTrue(params.get("hasMtnLoyaltyOffers"))
        offers = params.get("loyaltyOffers", [])
        self.assertEqual(len(offers), 1)
        self.assertEqual(offers[0].get("OfferID"), self.offer_id)
        # Store key details for later steps
        retrieved_account_number = params.get("accountNumber")
        retrieved_offer_id = offers[0].get("OfferID")

        # Steps 2, 3, 4: manage_customer_authentication (following DI flow)
        # Step 2: Initialize authentication
        manage_customer_authentication(authstate="AUTHENTICATION_INIT")
        auth_result = {
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
        }
        utils.set_auth_result(auth_result)
        # Step 3: Check authentication status (simulating user interaction with link)
        auth_res = manage_customer_authentication(authstate="AUTHENTICATION_STATUS")
        self.assertIsNotNone(auth_res)
        session_map = auth_res["sessionInfo"]["parameters"].get("sessionMap", {})
        auth_details_str = session_map.get("adaptiveAuthentication", "{}")
        auth_details = json.loads(auth_details_str)
        self.assertEqual(auth_details.get("authstatus"), "ACCEPT")

        # Step 5: get_authenticated_customer_profile
        profile_res = get_authenticated_customer_profile(authstatus="ACCEPT")
        self.assertIsNotNone(profile_res)
        profile = profile_res.get("customerProfile", {})
        self.assertEqual(profile.get("accountNumber"), self.account_number)
        self.assertEqual(profile.get("customerName"), self.customer_name)
        self.assertEqual(profile.get("numberOfLines"), "1")

        # Step 6: get_pre_authentication_call_data (called again per workflow)
        pre_auth_res_2 = get_pre_authentication_call_data()
        self.assertIsNotNone(pre_auth_res_2)
        session_info_2 = pre_auth_res_2.get("sessionInfo", {})
        params_2 = session_info_2.get("parameters", {})
        self.assertEqual(
            params_2.get("accountNumber"),
            self.account_number,
        )

        # Step 7: get_authenticated_customer_profile (called again per workflow)
        profile_res_2 = get_authenticated_customer_profile(authstatus="ACCEPT")
        self.assertIsNotNone(profile_res_2)
        self.assertEqual(
            profile_res_2.get("customerProfile", {}).get("accountNumber"),
            self.account_number,
        )

        # Step 8: enroll_in_offer
        enroll_res = enroll_in_offer(
            accountNumber=retrieved_account_number, offerId=retrieved_offer_id
        )
        self.assertIsNotNone(enroll_res)
        self.assertEqual(enroll_res.get("status"), "success")

        # Step 9: record_call_outcome_and_disconnect
        disconnect_res = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT",
            dispositionCode="PROMO_ACCEPTED")
        self.assertIsNotNone(disconnect_res)
        self.assertEqual(disconnect_res.get("status"), "success")

        # Step 10: done
        done_res = done()
        self.assertIsInstance(done_res, str)
        self.assertEqual(done_res, "")