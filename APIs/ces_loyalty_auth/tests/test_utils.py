"""
Test cases for the utility functions in the CES Loyalty Auth API simulation engine.

This module verifies that the utility functions for managing conversation status,
authentication state, and customer data in the simulation engine work as expected.
"""

import unittest
import json
from APIs.ces_loyalty_auth.SimulationEngine import utils, db
from .loyalty_auth_base_exception import LoyaltyAuthBaseTestCase


class TestUtils(LoyaltyAuthBaseTestCase):
    """
    Test suite for the utility functions in the simulation engine.
    """

    def test_set_conversation_status(self):
        """
        Tests that _set_conversation_status correctly updates the conversation status in the DB.
        """
        utils._set_conversation_status("test_status", param1="value1")
        self.assertEqual(db.DB["CONVERSATION_STATUS"]["status"], "test_status")
        self.assertEqual(
            db.DB["CONVERSATION_STATUS"]["session_params"]["param1"], "value1"
        )

    def test_set_session_status(self):
        """
        Tests that _set_session_status correctly updates the session status in the DB.
        """
        utils._set_session_status("active")
        self.assertEqual(db.DB["SESSION_STATUS"]["status"], "active")

    def test_set_auth_result(self):
        """
        Tests that set_auth_result correctly updates the auth result in the DB.
        """
        auth_data = {"result": "success"}
        utils.set_auth_result(auth_data)
        self.assertEqual(db.DB["AUTH_RESULT"], auth_data)

    def test_update_auth_status(self):
        """
        Tests that update_auth_status correctly extracts and updates the auth status
        from the sessionMap in the AUTH_RESULT.
        """
        auth_result = {
            "sessionInfo": {
                "parameters": {
                    "sessionMap": {
                        "adaptiveAuthentication": json.dumps({"authstatus": "ACCEPT"})
                    }
                }
            }
        }
        db.DB["AUTH_RESULT"] = auth_result
        utils.update_auth_status()
        self.assertEqual(db.DB["AUTH_STATUS"], "ACCEPT")

    def test_update_auth_status_no_auth(self):
        """
        Tests that update_auth_status handles cases where no authentication
        information is present.
        """
        db.DB["AUTH_RESULT"] = {}
        utils.update_auth_status()
        self.assertIsNone(db.DB["AUTH_STATUS"])

    def test_update_auth_status_invalid_json(self):
        """
        Tests that update_auth_status handles invalid JSON in adaptiveAuthentication.
        """
        auth_result = {
            "sessionInfo": {
                "parameters": {
                    "sessionMap": {
                        "adaptiveAuthentication": "this is not valid json"
                    }
                }
            }
        }
        db.DB["AUTH_RESULT"] = auth_result
        utils.update_auth_status()
        self.assertEqual(
            db.DB["AUTH_STATUS"], "error: authentication not successful"
        )

    def test_update_auth_status_none_auth_result(self):
        """
        Tests that update_auth_status handles None auth_result.
        """
        db.DB["AUTH_RESULT"] = None
        utils.update_auth_status()
        self.assertIsNone(db.DB["AUTH_STATUS"])

    def test_update_auth_status_empty_session_map(self):
        """
        Tests that update_auth_status handles empty sessionMap.
        """
        auth_result = {
            "sessionInfo": {
                "parameters": {
                    "sessionMap": {}
                }
            }
        }
        db.DB["AUTH_RESULT"] = auth_result
        utils.update_auth_status()
        self.assertIsNone(db.DB["AUTH_STATUS"])

    def test_update_auth_status_empty_parameters(self):
        """
        Tests that update_auth_status handles empty parameters.
        """
        auth_result = {
            "sessionInfo": {
                "parameters": {}
            }
        }
        db.DB["AUTH_RESULT"] = auth_result
        utils.update_auth_status()
        self.assertIsNone(db.DB["AUTH_STATUS"])

    def test_set_preauth_data(self):
        """
        Tests that set_preauth_data correctly updates the pre-authentication
        profile data in the DB.
        """
        preauth_data = {"customerName": "PreAuth Customer"}
        utils.set_preauth_data(preauth_data)
        self.assertEqual(db.DB["PROFILE_BEFORE_AUTH"], preauth_data)

    def test_set_customer_profile(self):
        """
        Tests that set_customer_profile correctly updates the post-authentication
        customer profile data in the DB.
        """
        profile_data = {"customerName": "PostAuth Customer"}
        utils.set_customer_profile(profile_data)
        self.assertEqual(db.DB["PROFILE_AFTER_AUTH"], profile_data)

    def test_get_conversation_status(self):
        """
        Tests that get_conversation_status correctly retrieves the conversation status from the DB.
        """
        # Set up test data
        test_status = {"status": "active", "session_params": {"param1": "value1"}}
        db.DB["CONVERSATION_STATUS"] = test_status
        
        # Test getting the status
        result = utils.get_conversation_status()
        self.assertEqual(result, test_status)
        
        # Test getting status when not set
        db.DB.pop("CONVERSATION_STATUS", None)
        result = utils.get_conversation_status()
        self.assertIsNone(result)

    def test_get_session_status(self):
        """
        Tests that get_session_status correctly retrieves the session status from the DB.
        """
        # Set up test data
        test_status = {"status": "active"}
        db.DB["SESSION_STATUS"] = test_status
        
        # Test getting the status
        result = utils.get_session_status()
        self.assertEqual(result, test_status)
        
        # Test getting status when not set
        db.DB.pop("SESSION_STATUS", None)
        result = utils.get_session_status()
        self.assertIsNone(result)

    def test_get_offer_enrollment(self):
        """
        Tests that get_offer_enrollment correctly retrieves the offer enrollment data from the DB.
        """
        # Set up test data
        test_enrollment = {
            "accountNumber": "56985362456-00001",
            "offerId": "9635"
        }
        db.DB["OFFER_ENROLLMENT"] = test_enrollment
        
        # Test getting the enrollment data
        result = utils.get_offer_enrollment()
        self.assertEqual(result, test_enrollment)
        self.assertEqual(result["accountNumber"], "56985362456-00001")
        self.assertEqual(result["offerId"], "9635")
        
        # Test getting enrollment when not set
        db.DB.pop("OFFER_ENROLLMENT", None)
        result = utils.get_offer_enrollment()
        self.assertIsNone(result)

    def test_get_loyalty_offers(self):
        """
        Tests that get_loyalty_offers correctly retrieves the loyalty offers from the DB.
        """
        # Set up test data
        test_offers = [
            {"OfferDesc": "10% off", "offerOrder": "1", "offerType": "DISCOUNT", "OfferID": "12345"}
        ]
        db.DB["PROFILE_BEFORE_AUTH"] = {"sessionInfo": {"parameters": {"loyaltyOffers": test_offers}}}
        result = utils.get_loyalty_offers()
        self.assertEqual(result, test_offers)
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], dict)
        self.assertEqual(result[0]["OfferDesc"], "10% off")
        self.assertEqual(result[0]["offerOrder"], "1")
        self.assertEqual(result[0]["offerType"], "DISCOUNT")
        self.assertEqual(result[0]["OfferID"], "12345")

    def test_get_auth_status(self):
        """
        Tests that get_auth_status correctly retrieves the authentication status from the DB.
        """
        # Set up test data with realistic auth status
        test_auth_status = "ACCEPT"
        db.DB["AUTH_STATUS"] = test_auth_status
        
        # Test getting the auth status
        result = utils.get_auth_status()
        self.assertEqual(result, test_auth_status)
        self.assertIsInstance(result, str)
        
        # Test getting auth status when not set
        db.DB.pop("AUTH_STATUS", None)
        result = utils.get_auth_status()
        self.assertIsNone(result)

    def test_get_customer_name_from_preauth(self):
        """
        Tests that get_customer_name_from_preauth correctly retrieves the customer name 
        from the pre-authentication profile data.
        """
        # Set up test data with proper structure
        test_profile_before_auth = {
            "sessionInfo": {
                "parameters": {
                    "customerName": "Jane Doe",
                    "firstName": "Jane",
                    "accountNumber": "56985362456-00001"
                }
            }
        }
        db.DB["PROFILE_BEFORE_AUTH"] = test_profile_before_auth
        
        # Test getting the customer name
        result = utils.get_customer_name_from_preauth()
        self.assertEqual(result, "Jane Doe")
        self.assertIsInstance(result, str)
        
        # Test getting customer name when profile is not set
        db.DB.pop("PROFILE_BEFORE_AUTH", None)
        result = utils.get_customer_name_from_preauth()
        self.assertIsNone(result)
        
        # Test getting customer name when sessionInfo is missing
        db.DB["PROFILE_BEFORE_AUTH"] = {}
        result = utils.get_customer_name_from_preauth()
        self.assertIsNone(result)
        
        # Test getting customer name when parameters is missing
        db.DB["PROFILE_BEFORE_AUTH"] = {"sessionInfo": {}}
        result = utils.get_customer_name_from_preauth()
        self.assertIsNone(result)
        
        # Test getting customer name when parameters is empty
        db.DB["PROFILE_BEFORE_AUTH"] = {"sessionInfo": {"parameters": {}}}
        result = utils.get_customer_name_from_preauth()
        self.assertIsNone(result)
        
        # Test getting customer name when customerName is missing
        db.DB["PROFILE_BEFORE_AUTH"] = {
            "sessionInfo": {
                "parameters": {
                    "firstName": "Jane",
                    "accountNumber": "56985362456-00001"
                }
            }
        }
        result = utils.get_customer_name_from_preauth()
        self.assertIsNone(result)

    def test_get_customer_account_number_from_preauth_success(self):
        """
        Tests that get_customer_account_number_from_preauth correctly retrieves the account number 
        from the pre-authentication profile data when all data is present.
        """
        # Set up test data with proper structure that matches ProfileBeforeAuth model
        test_profile_before_auth = {
            "sessionInfo": {
                "parameters": {
                    "customerName": "Jane Doe",
                    "firstName": "Jane",
                    "accountNumber": "56985362456-00001"
                }
            }
        }
        db.DB["PROFILE_BEFORE_AUTH"] = test_profile_before_auth
        
        # Test getting the account number
        result = utils.get_customer_account_number_from_preauth()
        self.assertEqual(result, "56985362456-00001")
        self.assertIsInstance(result, str)

    def test_get_customer_account_number_from_preauth_no_profile(self):
        """
        Tests that get_customer_account_number_from_preauth returns None when PROFILE_BEFORE_AUTH is not set.
        Return None when profile_before_auth is falsy.
        """
        # Ensure PROFILE_BEFORE_AUTH is not set
        db.DB.pop("PROFILE_BEFORE_AUTH", None)
        
        result = utils.get_customer_account_number_from_preauth()
        self.assertIsNone(result)

    def test_get_customer_account_number_from_preauth_empty_profile(self):
        """
        Tests that get_customer_account_number_from_preauth returns None when PROFILE_BEFORE_AUTH is empty.
        Return None when profile_before_auth is falsy.
        """
        # Set empty profile
        db.DB["PROFILE_BEFORE_AUTH"] = {}
        
        result = utils.get_customer_account_number_from_preauth()
        self.assertIsNone(result)

    def test_get_customer_account_number_from_preauth_none_profile(self):
        """
        Tests that get_customer_account_number_from_preauth returns None when PROFILE_BEFORE_AUTH is None.
        Return None when profile_before_auth is falsy.
        """
        # Set None profile
        db.DB["PROFILE_BEFORE_AUTH"] = None
        
        result = utils.get_customer_account_number_from_preauth()
        self.assertIsNone(result)

    def test_get_customer_account_number_from_preauth_empty_session_info(self):
        """
        Tests that get_customer_account_number_from_preauth returns None when sessionInfo is empty.
        Return None when session_info is falsy.
        """
        # Set profile with empty sessionInfo
        db.DB["PROFILE_BEFORE_AUTH"] = {
            "sessionInfo": {}
        }
        
        result = utils.get_customer_account_number_from_preauth()
        self.assertIsNone(result)

    def test_get_customer_account_number_from_preauth_none_session_info(self):
        """
        Tests that get_customer_account_number_from_preauth returns None when sessionInfo is None.
        Return None when session_info is falsy.
        """
        # Set profile with None sessionInfo
        db.DB["PROFILE_BEFORE_AUTH"] = {
            "sessionInfo": None
        }
        
        result = utils.get_customer_account_number_from_preauth()
        self.assertIsNone(result)

    def test_get_customer_account_number_from_preauth_no_parameters(self):
        """
        Tests that get_customer_account_number_from_preauth returns None when parameters is missing.
        Return None when parameters is falsy.
        """
        # Set profile with sessionInfo but no parameters
        db.DB["PROFILE_BEFORE_AUTH"] = {
            "sessionInfo": {
                "someOtherKey": "someValue"
            }
        }
        
        result = utils.get_customer_account_number_from_preauth()
        self.assertIsNone(result)

    def test_get_customer_account_number_from_preauth_empty_parameters(self):
        """
        Tests that get_customer_account_number_from_preauth returns None when parameters is empty.
        Return None when parameters is falsy.
        """
        # Set profile with sessionInfo but empty parameters
        db.DB["PROFILE_BEFORE_AUTH"] = {
            "sessionInfo": {
                "parameters": {}
            }
        }
        
        result = utils.get_customer_account_number_from_preauth()
        self.assertIsNone(result)

    def test_get_customer_account_number_from_preauth_none_parameters(self):
        """
        Tests that get_customer_account_number_from_preauth returns None when parameters is None.
        Return None when parameters is falsy.
        """
        # Set profile with sessionInfo but None parameters
        db.DB["PROFILE_BEFORE_AUTH"] = {
            "sessionInfo": {
                "parameters": None
            }
        }
        
        result = utils.get_customer_account_number_from_preauth()
        self.assertIsNone(result)

    def test_update_auth_status_authstate_transition(self):
        """
        Tests that update_auth_status correctly transitions authstate from AUTHENTICATION_INIT 
        to AUTHENTICATION_PENDING when auth status is ACCEPT.
        """
        # Set up test data with AUTHENTICATION_INIT state
        auth_result = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_INIT",
                    "sessionMap": {
                        "adaptiveAuthentication": json.dumps({"authstatus": "ACCEPT"})
                    }
                }
            }
        }
        db.DB["AUTH_RESULT"] = auth_result
        
        # Call update_auth_status
        utils.update_auth_status()
        
        # Verify auth status is set correctly
        self.assertEqual(db.DB["AUTH_STATUS"], "ACCEPT")
        
        # Verify authstate is transitioned from AUTHENTICATION_INIT to AUTHENTICATION_PENDING
        self.assertEqual(
            db.DB["AUTH_RESULT"]["sessionInfo"]["parameters"]["authstate"], 
            "AUTHENTICATION_PENDING"
        )

    def test_update_auth_status_authstate_no_transition_when_not_accept(self):
        """
        Tests that update_auth_status does not transition authstate when auth status is not ACCEPT.
        """
        # Set up test data with AUTHENTICATION_INIT state but auth status is not ACCEPT
        auth_result = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_INIT",
                    "sessionMap": {
                        "adaptiveAuthentication": json.dumps({"authstatus": "REJECT"})
                    }
                }
            }
        }
        db.DB["AUTH_RESULT"] = auth_result
        
        # Call update_auth_status
        utils.update_auth_status()
        
        # Verify auth status is set correctly
        self.assertEqual(db.DB["AUTH_STATUS"], "REJECT")
        
        # Verify authstate remains unchanged (should still be AUTHENTICATION_INIT)
        self.assertEqual(
            db.DB["AUTH_RESULT"]["sessionInfo"]["parameters"]["authstate"], 
            "AUTHENTICATION_INIT"
        )

    def test_update_auth_status_authstate_no_transition_when_not_init(self):
        """
        Tests that update_auth_status does not transition authstate when authstate is not AUTHENTICATION_INIT.
        """
        # Set up test data with auth status ACCEPT but authstate is not AUTHENTICATION_INIT
        auth_result = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_PENDING",
                    "sessionMap": {
                        "adaptiveAuthentication": json.dumps({"authstatus": "ACCEPT"})
                    }
                }
            }
        }
        db.DB["AUTH_RESULT"] = auth_result
        
        # Call update_auth_status
        utils.update_auth_status()
        
        # Verify auth status is set correctly
        self.assertEqual(db.DB["AUTH_STATUS"], "ACCEPT")
        
        # Verify authstate remains unchanged (should still be AUTHENTICATION_PENDING)
        self.assertEqual(
            db.DB["AUTH_RESULT"]["sessionInfo"]["parameters"]["authstate"], 
            "AUTHENTICATION_PENDING"
        )


if __name__ == "__main__":
    unittest.main()
