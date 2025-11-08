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
        Set up the test environment and database state before each test.
        """
        # Create an empty DB structure
        db.reset_db()

        # --- Test Data Setup ---

        # 1. Data for `get_pre_authentication_call_data`
        self.pre_auth_data = {
            'sessionInfo': {
                'parameters': {
                    'hasMtnLoyaltyOffers': True,
                    'availablePerks': [{'perk_name': 'Disney Bundle'}],
                    'accountNumber': 'ACC123456789',
                    'status': 'success',
                    'statusCode': '200',
                    'customerName': 'Jane Doe',
                    'preferredFirstName': 'Jane',
                    'firstName': 'Jane',
                    'statusMessage': 'Pre-authentication data retrieved successfully.',
                    'loyaltyOffersStatusCode': '200',
                    'loyaltyOffers': [{
                        'OfferDesc': '$10 off for 12 months',
                        'offerOrder': '1',
                        'offerType': 'Discount',
                        'OfferID': 'LOYALTY_10_OFF'
                    }],
                    'unlimitedPlanPerks': [],
                    'sundayMobileValueProposition': {'title': 'Sunday Mobile'},
                    'sundayMobileOST': {'title': 'OST'},
                    'autoPayPaperFreeDiscountAmountInfo': {'discount': '5.00'},
                    'myPlanPricingDetails': {'Unlimited Plan': {'price': '75.00'}},
                    'myPlanPerks': {'myplan_perks': []},
                    'myPlanFeatures': {'Unlimited Plan': ['Feature A', 'Feature B']}
                }
            }
        }

        # 2. Data for simulating a successful authentication response
        self.auth_result_data = {
            'sessionInfo': {
                'parameters': {
                    'authstate': 'AUTHENTICATION_SUCCESS',
                    'sessionId': 'test-session-id-xyz',
                    'statusMessage': 'Authentication successful.',
                    'sessionMap': {
                        'adaptiveAuthentication': json.dumps({'authstatus': 'ACCEPT'})
                    }
                }
            }
        }

        # 3. Data for the authenticated customer profile
        self.customer_profile_data = {
            'customerProfile': {
                'customerName': 'Jane Doe',
                'numberOfLines': '1',
                'accountNumber': 'ACC123456789',
                'lines': [{
                    'mtn': '5551234567',
                    'mtnStatus': {'isActive': True},
                    'equipmentInfos': {'deviceInfo': {'displayName': 'iPhone 15'}},
                    'pricePlanInfo': {
                        'planId': 'PLAN01',
                        'effectiveDate': '2023-01-01',
                        'planDisplayName': 'Unlimited Plus'
                    },
                    'mobileInfoAttributes': {
                        'accessRoles': {
                            'owner': True,
                            'manager': False,
                            'member': False
                        }
                    }
                }],
                'customerFirstName': 'Jane',
                'customerLastName': 'Doe',
                'customerRole': 'Owner'
            }
        }

        # --- Populate DB using utils ---
        utils.set_preauth_data(self.pre_auth_data)
        utils.set_auth_result(self.auth_result_data)
        utils.set_customer_profile(self.customer_profile_data)

        # This utility function must be called after setting the auth result
        # to correctly populate the DB['AUTH_STATUS'] key.
        utils.update_auth_status()
        
        # Validate the overall DB state against the Pydantic model
        models.CesLoyaltyAuthDBModel(**db.get_minified_state())

    def test_integration_workflow(self):
        """
        Tests the complete end-to-end workflow for a successful offer enrollment.
        """
        # --- Step 1: Get Pre-Authentication Call Data ---
        pre_auth_response = get_pre_authentication_call_data()
        self.assertIsNotNone(pre_auth_response, "Pre-authentication response should not be None.")
        
        pre_auth_params = pre_auth_response['sessionInfo']['parameters']
        self.assertEqual(pre_auth_params['accountNumber'], 'ACC123456789')
        self.assertTrue(pre_auth_params['hasMtnLoyaltyOffers'])
        self.assertGreater(len(pre_auth_params['loyaltyOffers']), 0, "Should have at least one loyalty offer.")
        
        account_number = pre_auth_params['accountNumber']
        offer_id = pre_auth_params['loyaltyOffers'][0]['OfferID']
        self.assertEqual(offer_id, 'LOYALTY_10_OFF')

        # --- Step 2: Manage Customer Authentication (following DI flow) ---
        # Step 2a: Initialize authentication (send SMS)
        auth_init_response = manage_customer_authentication(authstate='AUTHENTICATION_INIT')
        self.assertIsNotNone(auth_init_response, "Auth INIT response should not be None.")
        auth_init_params = auth_init_response['sessionInfo']['parameters']
        self.assertEqual(auth_init_params['authstate'], 'AUTHENTICATION_INIT')
        self.assertEqual(auth_init_params['statusCode'], '200')
        self.assertEqual(auth_init_params['statusMessage'], 'Authentication SMS sent successfully')
        
        # Step 2b: Check authentication status (simulating user interaction with link)
        utils.set_auth_result({
            'sessionInfo': {
                'parameters': {
                    'authstate': 'AUTHENTICATION_SUCCESS',
                    'sessionId': 'test-session-id-xyz',
                    'statusMessage': 'Authentication successful.',
                    'statusCode': '200',
                    'sessionMap': {
                        'adaptiveAuthentication': '{"authstatus": "ACCEPT"}'
                    }
                }
            }
        })
        utils.update_auth_status()
        auth_status_response = manage_customer_authentication(authstate='AUTHENTICATION_STATUS')
        self.assertIsNotNone(auth_status_response, "Auth STATUS response should not be None.")
        auth_status_params = auth_status_response['sessionInfo']['parameters']
        self.assertEqual(auth_status_params['authstate'], 'AUTHENTICATION_SUCCESS')
        auth_status_from_map = json.loads(auth_status_params['sessionMap']['adaptiveAuthentication'])['authstatus']
        self.assertEqual(auth_status_from_map, 'ACCEPT')

        # --- Step 3: Get Authenticated Customer Profile ---
        profile_response = get_authenticated_customer_profile(authstatus='ACCEPT')
        self.assertIsNotNone(profile_response, "Authenticated profile response should not be None.")
        
        customer_profile = profile_response['customerProfile']
        self.assertEqual(customer_profile['accountNumber'], account_number)
        self.assertEqual(customer_profile['customerName'], 'Jane Doe')
        self.assertEqual(customer_profile['numberOfLines'], '1')

        # --- Step 4: Enroll in Offer ---
        enroll_response = enroll_in_offer(accountNumber=account_number, offerId=offer_id)
        self.assertIsNotNone(enroll_response, "Enrollment response should not be None.")
        self.assertEqual(enroll_response.get('status'), 'success', "Enrollment status should be 'success' for success.")

        # --- Step 5: Record Call Outcome and Disconnect ---
        disconnect_response = record_call_outcome_and_disconnect(
            callEndState='DISCONNECT',
            dispositionCode='PROMO_ACCEPTED',
        )
        self.assertIsNotNone(disconnect_response, "Disconnect response should not be None.")
        self.assertEqual(disconnect_response.get('status'), 'success', "Disconnect status should be 'success'.")

        # --- Step 6: Done ---
        done_response = done()
        self.assertIsNotNone(done_response, "Done response should not be None.")
        self.assertEqual(done_response, "", "Done response should be an empty string.")