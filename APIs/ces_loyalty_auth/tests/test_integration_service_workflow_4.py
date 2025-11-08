import json
import unittest

# Assuming common_utils.base_case exists in the project structure
# In a real scenario, this would be part of a shared test library.
# For this exercise, we define a placeholder to make the code runnable.
class BaseTestCaseWithErrorHandler(unittest.TestCase):
    """Placeholder for the actual base class."""
    pass

# Import API functions using relative imports as specified
from .. import (
    done,
    enroll_in_offer,
    get_authenticated_customer_profile,
    get_pre_authentication_call_data,
    manage_customer_authentication,
    record_call_outcome_and_disconnect,
    fail)

# Import Simulation Engine modules using relative imports as specified
from ..SimulationEngine import db, models, utils


class CesLoyaltyAuthIntegrationTest(BaseTestCaseWithErrorHandler):
    """
    Integration test suite for the CES Loyalty Auth service workflow.
    """

    def setUp(self):
        """
        Set up the test environment by initializing the database and populating it
        with the necessary data for the happy path workflow.
        """
        # 1. Create an empty DB with keys based on the schema
        # Adhering to the instruction to not use `load_state` or `reset_db`
        # which might load default files.
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
        
        # 2. Define mock data for the entire workflow
        self.account_number = "9876543210"
        self.offer_id = "LOYALTYOFFER2024"
        self.customer_name = "John Smith"
        self.session_id = "test-session-xyz-123"

        # Data for get_pre_authentication_call_data
        pre_auth_data = {
            "sessionInfo": {
                "parameters": {
                    "hasMtnLoyaltyOffers": True,
                    "availablePerks": [{"perkName": "Streaming Service Bundle"}],
                    "accountNumber": self.account_number,
                    "status": "Success",
                    "statusCode": "200",
                    "customerName": self.customer_name,
                    "preferredFirstName": "John",
                    "firstName": "John",
                    "statusMessage": "Pre-authentication data retrieved successfully.",
                    "loyaltyOffersStatusCode": "0",
                    "loyaltyOffers": [
                        {
                            "OfferDesc": "Get $10 off your monthly bill.",
                            "offerOrder": "1",
                            "offerType": "DISCOUNT",
                            "OfferID": self.offer_id,
                        }
                    ],
                    "unlimitedPlanPerks": [],
                    "sundayMobileValueProposition": {"title": "Sunday Mobile"},
                    "sundayMobileOST": {"title": "Sunday OST"},
                    "autoPayPaperFreeDiscountAmountInfo": {"amount": "5.00"},
                    "myPlanPricingDetails": {"Unlimited Plan": {"price": "75.00"}},
                    "myPlanPerks": {"myplan_perks": []},
                    "myPlanFeatures": {"Unlimited Plan": ["Unlimited Talk & Text"]},
                }
            }
        }

        # Data for manage_customer_authentication (simulates a successful auth)
        auth_result_data = {
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
        
        # Data for get_authenticated_customer_profile
        customer_profile_data = {
            "customerProfile": {
                "customerName": self.customer_name,
                "numberOfLines": "2",
                "accountNumber": self.account_number,
                "lines": [
                    {
                        "mtn": "5551112222",
                        "mtnStatus": {"isActive": True},
                        "equipmentInfos": {"deviceInfo": {"displayName": "Galaxy S24"}},
                        "pricePlanInfo": {
                            "planId": "P001",
                            "effectiveDate": "2023-01-15",
                            "planDisplayName": "Premium Unlimited",
                        },
                        "mobileInfoAttributes": {
                            "accessRoles": {"owner": True, "manager": False, "member": False}
                        },
                    },
                    {
                        "mtn": "5553334444",
                        "mtnStatus": {"isActive": True},
                        "equipmentInfos": {"deviceInfo": {"displayName": "iPhone 15 Pro"}},
                         "pricePlanInfo": {
                            "planId": "P001",
                            "effectiveDate": "2023-01-15",
                            "planDisplayName": "Premium Unlimited",
                        },
                         "mobileInfoAttributes": {
                            "accessRoles": {"owner": False, "manager": False, "member": True}
                        },
                    }
                ],
                "autopayDiscountAmount": "10.00",
                "eligibleForAutopay": "true",
                "customerRole": "Owner",
                "greetByName": "John",
                "customerFirstName": "John",
                "customerLastName": "Smith",
                "paymentInfo": {
                    "enrolledInAutopay": True,
                    "lastPaymentDate": "2024-05-20",
                    "lastPaymentAmount": "150.00"
                }
            }
        }

        # 3. Use utils to populate the DB
        utils.set_preauth_data(pre_auth_data)
        utils.set_auth_result(auth_result_data)
        utils.set_customer_profile(customer_profile_data)

        # 4. Validate the overall DB state against the Pydantic model
        try:
            models.CesLoyaltyAuthDBModel(**db.get_minified_state())
        except Exception as e:
            self.fail(f"DB setup failed validation: {e}")

    def test_successful_enrollment_workflow(self):
        """
        Tests the complete end-to-end happy path workflow:
        Pre-auth -> Auth -> Get Profile -> Enroll -> Disconnect.
        """
        # 1. Get Pre-Authentication Call Data
        pre_auth_response = get_pre_authentication_call_data()
        self.assertIsNotNone(pre_auth_response)
        
        pre_auth_params = pre_auth_response.get("sessionInfo", {}).get("parameters", {})
        self.assertEqual(pre_auth_params.get("status"), "Success")
        self.assertEqual(pre_auth_params.get("accountNumber"), self.account_number)
        
        # Extract account number and offer ID for later steps
        retrieved_account_number = pre_auth_params.get("accountNumber")
        retrieved_offer_id = pre_auth_params.get("loyaltyOffers", [{}])[0].get("OfferID")
        self.assertEqual(retrieved_offer_id, self.offer_id)

        # 2. Manage Customer Authentication (following DI flow)
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

        # After managing authentication, update the status to reflect the outcome
        utils.update_auth_status()
        self.assertEqual(db.DB.get("AUTH_STATUS"), "ACCEPT")

        # 3. Get Authenticated Customer Profile
        profile_response = get_authenticated_customer_profile(authstatus="ACCEPT")
        self.assertIsNotNone(profile_response)
        
        customer_profile = profile_response.get("customerProfile", {})
        self.assertEqual(customer_profile.get("accountNumber"), self.account_number)
        self.assertEqual(customer_profile.get("customerName"), self.customer_name)
        self.assertEqual(len(customer_profile.get("lines")), 2)

        # 4. Enroll in Offer
        enrollment_response = enroll_in_offer(
            accountNumber=retrieved_account_number, offerId=retrieved_offer_id
        )
        self.assertIsNotNone(enrollment_response)
        self.assertEqual(enrollment_response.get("status"), "success")

        # 5. Record Call Outcome and Disconnect
        disconnect_response = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT",
            dispositionCode="PROMO_ACCEPTED",
            preferredLang="E",
        )
        self.assertIsNotNone(disconnect_response)
        self.assertEqual(disconnect_response.get("status"), "success")

        # 6. Done (Final call termination)
        done_response = done()
        self.assertIsNotNone(done_response)
        self.assertEqual(done_response, "", "done function should return an empty string")