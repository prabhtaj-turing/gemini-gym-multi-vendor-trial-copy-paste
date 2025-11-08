"""
Test cases for the core functions of the CES Loyalty Auth API.

This module contains detailed tests for each of the main tool functions,
ensuring they handle valid and invalid inputs correctly, manage state as
expected, and interact with the simulation engine properly.
"""

import unittest
from pydantic import ValidationError
from ces_loyalty_auth import (
    get_authenticated_customer_profile,
    manage_customer_authentication,
    get_pre_authentication_call_data,
    record_call_outcome_and_disconnect,
    transfer_to_live_agent,
    enroll_in_offer,
    done,
    fail,
    cancel,
    escalate)
from ces_loyalty_auth.SimulationEngine import db, utils
from ces_loyalty_auth.SimulationEngine.custom_errors import (
    AuthenticationFailedError,
    InvalidRequestError,
)
from ces_loyalty_auth.SimulationEngine.models import CallEndState, DispositionCode
from .loyalty_auth_base_exception import LoyaltyAuthBaseTestCase


class TestCoreFunctions(LoyaltyAuthBaseTestCase):
    """
    Test suite for the core functions of the CES Loyalty Auth API.
    """

    def test_get_pre_authentication_call_data(self):
        """
        Tests that get_pre_authentication_call_data returns the correct data
        from the PROFILE_BEFORE_AUTH section of the DB.
        """
        response = get_pre_authentication_call_data()
        self.assertEqual(
            response["sessionInfo"]["parameters"]["customerName"], "Jane Doe"
        )

    def test_get_pre_authentication_call_data_validation_error(self):
        """
        Tests that get_pre_authentication_call_data raises a ValueError if the
        pre-authentication data fails validation.
        """
        # This profile is invalid because sessionInfo is missing required fields.
        invalid_profile = {"sessionInfo": {"parameters": {}}}
        db.DB["PROFILE_BEFORE_AUTH"] = invalid_profile

        with self.assertRaises(ValueError) as cm:
            get_pre_authentication_call_data()

        # Check for the more specific validation error message
        self.assertIn(
            "parameters is empty or missing in sessionInfo", str(cm.exception)
        )

    def test_get_pre_authentication_call_data_none_profile(self):
        """
        Tests that get_pre_authentication_call_data raises an AuthenticationFailedError when
        PROFILE_BEFORE_AUTH is None.
        """
        db.DB["PROFILE_BEFORE_AUTH"] = None

        with self.assertRaises(AuthenticationFailedError) as cm:
            get_pre_authentication_call_data()

        self.assertIn(
            "Pre-authentication data not found in database", str(cm.exception)
        )

    def test_get_pre_authentication_call_data_empty_profile(self):
        """
        Tests that get_pre_authentication_call_data raises an AuthenticationFailedError when
        PROFILE_BEFORE_AUTH is empty.
        """
        db.DB["PROFILE_BEFORE_AUTH"] = {}

        with self.assertRaises(AuthenticationFailedError) as cm:
            get_pre_authentication_call_data()

        self.assertIn(
            "Pre-authentication data not found in database", str(cm.exception)
        )

    def test_get_pre_authentication_call_data_missing_session_info(self):
        """
        Tests that get_pre_authentication_call_data raises a ValueError when
        sessionInfo key is missing.
        """
        db.DB["PROFILE_BEFORE_AUTH"] = {"invalid": "data"}

        with self.assertRaises(ValueError) as cm:
            get_pre_authentication_call_data()

        self.assertIn(
            "Missing required key 'sessionInfo' in pre-authentication data", str(cm.exception)
        )

    def test_get_pre_authentication_call_data_empty_session_info(self):
        """
        Tests that get_pre_authentication_call_data raises a ValueError when
        sessionInfo is empty.
        """
        db.DB["PROFILE_BEFORE_AUTH"] = {"sessionInfo": {}}

        with self.assertRaises(ValueError) as cm:
            get_pre_authentication_call_data()

        self.assertIn(
            "sessionInfo is empty or missing", str(cm.exception)
        )

    def test_get_pre_authentication_call_data_missing_critical_params(self):
        """
        Tests that get_pre_authentication_call_data raises a ValueError when
        critical parameters are missing.
        """
        db.DB["PROFILE_BEFORE_AUTH"] = {
            "sessionInfo": {
                "parameters": {
                    "accountNumber": "1234567890",
                    "customerName": "John Doe"
                    # Missing other critical parameters
                }
            }
        }

        with self.assertRaises(ValueError) as cm:
            get_pre_authentication_call_data()

        self.assertIn(
            "Missing critical parameter", str(cm.exception)
        )

    def test_manage_customer_authentication_session_id_is_deterministic(self):
        """
        Tests that the session ID is deterministic based on the customer account number.
        """
        response1 = manage_customer_authentication(authstate="AUTHENTICATION_INIT")
        response2 = manage_customer_authentication(authstate="AUTHENTICATION_INIT")
        response3 = manage_customer_authentication(authstate="AUTHENTICATION_INIT")
        session_id1 = response1["sessionInfo"]["parameters"]["sessionId"]
        session_id2 = response2["sessionInfo"]["parameters"]["sessionId"]
        session_id3 = response3["sessionInfo"]["parameters"]["sessionId"]
        self.assertEqual(session_id1, session_id2)
        self.assertEqual(session_id1, session_id3)

    def test_get_pre_authentication_call_data_model_validation_error(self):
        """
        Tests that get_pre_authentication_call_data raises a ValidationError when
        model validation fails.
        """
        # Create a profile that passes our validation but fails Pydantic model validation
        # by providing invalid data types for required fields
        db.DB["PROFILE_BEFORE_AUTH"] = {
            "sessionInfo": {
                "parameters": {
                    "accountNumber": "1234567890",
                    "customerName": "John Doe",
                    "status": "SUCCESS",
                    "statusCode": "00000",
                    "loyaltyOffers": "invalid_type",  # Should be a list
                    "loyaltyOffersStatusCode": "00000",
                    "hasMtnLoyaltyOffers": True,
                    "availablePerks": [],
                    "preferredFirstName": "John",
                    "firstName": "John",
                    "statusMessage": "Success",
                    "unlimitedPlanPerks": [],
                    "sundayMobileValueProposition": {},
                    "sundayMobileOST": {},
                    "autoPayPaperFreeDiscountAmountInfo": {},
                    "myPlanPricingDetails": {},
                    "myPlanPerks": {},
                    "myPlanFeatures": {}
                }
            }
        }

        with self.assertRaises(ValidationError) as cm:
            get_pre_authentication_call_data()

        # Check that the validation error contains information about the type mismatch
        error_str = str(cm.exception)
        self.assertTrue("Input should be a valid list" in error_str or "validation error" in error_str.lower())

    def test_manage_customer_authentication(self):
        """
        Tests that manage_customer_authentication updates and returns the
        correct authentication status.
        """
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
        response = manage_customer_authentication(authstate="AUTHENTICATION_STATUS")
        self.assertIn("sessionMap", response["sessionInfo"]["parameters"])

    def test_manage_customer_authentication_validation_error(self):
        """
        Tests that manage_customer_authentication raises a ValidationError if the
        auth result data fails validation.
        """
        # This auth_result is invalid because parameters is missing required fields.
        invalid_auth_result = {"sessionInfo": {"parameters": {}}}
        utils.set_auth_result(invalid_auth_result)

        with self.assertRaises(ValidationError) as cm:
            manage_customer_authentication(authstate="AUTHENTICATION_STATUS")

        # Check that the validation error contains information about missing fields
        error_str = str(cm.exception)
        self.assertTrue("Field required" in error_str or "validation error" in error_str.lower())

    def test_manage_customer_authentication_none_auth_result(self):
        """
        Tests that manage_customer_authentication raises an AuthenticationFailedError when
        AUTH_RESULT is None.
        """
        # Set AUTH_RESULT to None to trigger the specific error
        db.DB["AUTH_RESULT"] = None

        with self.assertRaises(AuthenticationFailedError) as cm:
            manage_customer_authentication(authstate="AUTHENTICATION_STATUS")

        self.assertIn(
            "Authentication result not found in database. Please initialize authentication first.", 
            str(cm.exception)
        )

    def test_manage_customer_authentication_unknown_authstate(self):
        """
        Tests that manage_customer_authentication raises an AuthenticationFailedError when
        an unknown authstate is provided.
        """
        with self.assertRaises(AuthenticationFailedError) as cm:
            manage_customer_authentication(authstate="UNKNOWN_STATE")

        self.assertIn(
            "Unknown authentication state: UNKNOWN_STATE", 
            str(cm.exception)
        )

    def test_get_authenticated_customer_profile_success(self):
        """
        Tests successful retrieval of the customer profile after authentication.
        """
        auth_result = {
            "sessionInfo": {
                "parameters": {
                    "sessionMap": {
                        "adaptiveAuthentication": '{"authstatus": "ACCEPT"}'
                    }
                }
            }
        }
        utils.set_auth_result(auth_result)
        utils.update_auth_status()  # This will set AUTH_STATUS to "ACCEPT"

        expected_profile = {"customerProfile": {"customerName": "Authenticated User", "numberOfLines": "1", "accountNumber": "123", "lines": []}}
        db.DB["PROFILE_AFTER_AUTH"] = expected_profile
        response = get_authenticated_customer_profile(authstatus="ACCEPT")
        self.assertEqual(
            response["customerProfile"]["customerName"], "Authenticated User"
        )

    def test_get_authenticated_customer_profile_failure(self):
        """
        Tests that get_authenticated_customer_profile raises an error if
        the customer is not authenticated.
        """
        db.DB["AUTH_STATUS"] = "PENDING"
        with self.assertRaises(AuthenticationFailedError):
            get_authenticated_customer_profile(authstatus="ACCEPT")

        with self.assertRaises(AuthenticationFailedError):
            get_authenticated_customer_profile(authstatus="PENDING")

    def test_get_authenticated_customer_profile_validation_error(self):
        """
        Tests that get_authenticated_customer_profile raises a ValidationError if the
        profile data fails validation.
        """
        db.DB["AUTH_STATUS"] = "ACCEPT"
        # This profile is invalid because customerProfile is missing required fields.
        invalid_profile = {"customerProfile": {"customerName": "Test User"}}
        db.DB["PROFILE_AFTER_AUTH"] = invalid_profile

        with self.assertRaises(ValidationError) as cm:
            get_authenticated_customer_profile(authstatus="ACCEPT")

        # Check that the validation error contains information about missing fields
        error_str = str(cm.exception)
        self.assertTrue("Field required" in error_str or "validation error" in error_str.lower())

    def test_enroll_in_offer_success(self):
        """
        Tests that a customer can be successfully enrolled in an offer after
        authentication.
        """
        auth_result = {
            "sessionInfo": {
                "parameters": {
                    "sessionMap": {
                        "adaptiveAuthentication": '{"authstatus": "ACCEPT"}'
                    }
                }
            }
        }
        utils.set_auth_result(auth_result)
        utils.update_auth_status()

        response = enroll_in_offer(accountNumber="56985362456-00001", offerId="9635")
        self.assertEqual(response["status"], "success")
        self.assertEqual(db.DB["OFFER_ENROLLMENT"]["accountNumber"], "56985362456-00001")

    def test_enroll_in_offer_failure(self):
        """
        Tests that enroll_in_offer fails if the customer is not authenticated.
        """
        db.DB["AUTH_STATUS"] = "PENDING"
        with self.assertRaises(AuthenticationFailedError):
            enroll_in_offer(accountNumber="12345", offerId="OFFER01")

    def test_enroll_in_offer_invalid_account_number(self):
        """
        Tests that enroll_in_offer raises ValidationError for invalid accountNumber.
        """
        db.DB["AUTH_STATUS"] = "ACCEPT"
        
        # Test with None accountNumber
        with self.assertRaises(ValidationError) as cm:
            enroll_in_offer(accountNumber=None, offerId="OFFER01")
        self.assertIn("Input should be a valid string", str(cm.exception))
        
        # Test with empty string accountNumber
        with self.assertRaises(ValidationError) as cm:
            enroll_in_offer(accountNumber="", offerId="OFFER01")
        self.assertIn("String should have at least 1 character", str(cm.exception))
        
        # Test with whitespace-only accountNumber
        with self.assertRaises(ValidationError) as cm:
            enroll_in_offer(accountNumber="   ", offerId="OFFER01")
        self.assertIn("String should match pattern", str(cm.exception))
        
        # Test with non-string accountNumber
        with self.assertRaises(ValidationError) as cm:
            enroll_in_offer(accountNumber=12345, offerId="OFFER01")
        self.assertIn("Input should be a valid string", str(cm.exception))

    def test_enroll_in_offer_invalid_offer_id(self):
        """
        Tests that enroll_in_offer raises ValidationError for invalid offerId.
        """
        db.DB["AUTH_STATUS"] = "ACCEPT"
        
        # Test with None offerId
        with self.assertRaises(ValidationError) as cm:
            enroll_in_offer(accountNumber="12345", offerId=None)
        self.assertIn("Input should be a valid string", str(cm.exception))
        
        # Test with empty string offerId
        with self.assertRaises(ValidationError) as cm:
            enroll_in_offer(accountNumber="12345", offerId="")
        self.assertIn("String should have at least 1 character", str(cm.exception))
        
        # Test with whitespace-only offerId
        with self.assertRaises(ValidationError) as cm:
            enroll_in_offer(accountNumber="12345", offerId="   ")
        self.assertIn("String should match pattern", str(cm.exception))
        
        # Test with non-string offerId
        with self.assertRaises(ValidationError) as cm:
            enroll_in_offer(accountNumber="12345", offerId=12345)
        self.assertIn("Input should be a valid string", str(cm.exception))

    def test_enroll_in_offer_mismatched_account_number(self):
        auth_result = {
            "sessionInfo": {
                "parameters": {
                    "sessionMap": {
                        "adaptiveAuthentication": '{"authstatus": "ACCEPT"}'
                    }
                }
            }
        }
        utils.set_auth_result(auth_result)
        utils.update_auth_status()
        self.assert_error_behavior(
            enroll_in_offer,
            InvalidRequestError,
            "Account number does not match the authenticated account number.",
            accountNumber="12345",
            offerId="9635"
        )

    def test_enroll_in_offer_mismatched_offer_id(self):
        auth_result = {
            "sessionInfo": {
                "parameters": {
                    "sessionMap": {
                        "adaptiveAuthentication": '{"authstatus": "ACCEPT"}'
                    }
                }
            }
        }
        utils.set_auth_result(auth_result)
        utils.update_auth_status()

        self.assert_error_behavior(
            enroll_in_offer,
            InvalidRequestError,
            "Offer ID does not match the authenticated offer ID.",
            accountNumber="56985362456-00001",
            offerId="12345"
        )
        

    def test_record_call_outcome_and_disconnect(self):
        """
        Tests that record_call_outcome_and_disconnect correctly records the
        call outcome in the database.
        """
        record_call_outcome_and_disconnect(
            callEndState="disconnect",
            dispositionCode="NOTIFICATION_NOT_RECEIVED",
        )
        status = db.DB["CONVERSATION_STATUS"]
        self.assertEqual(status["status"], "disconnect")
        self.assertEqual(status["session_params"]["dispositionCode"], "NOTIFICATION_NOT_RECEIVED")

    def test_record_call_outcome_and_disconnect_with_spanish_language(self):
        """
        Tests that record_call_outcome_and_disconnect correctly records the
        call outcome with Spanish language preference.
        where preferredLang is added to recorded_inputs when it's not "E".
        """
        record_call_outcome_and_disconnect(
            callEndState="disconnect",
            dispositionCode="NOTIFICATION_NOT_RECEIVED",
            preferredLang="S",
        )
        status = db.DB["CONVERSATION_STATUS"]
        self.assertEqual(status["status"], "disconnect")
        self.assertEqual(status["session_params"]["dispositionCode"], "NOTIFICATION_NOT_RECEIVED")
        self.assertEqual(status["session_params"]["preferredLang"], "S")

    def test_record_call_outcome_and_disconnect_invalid_call_end_state(self):
        """
        Tests that record_call_outcome_and_disconnect raises ValueError for invalid call end state.
        """
        self.assert_error_behavior(
            record_call_outcome_and_disconnect,
            ValueError,
            "Invalid call end state: INVALID_STATE",
            callEndState="INVALID_STATE",
            dispositionCode="NOTIFICATION_NOT_RECEIVED"
        )

    def test_record_call_outcome_and_disconnect_invalid_call_end_state_case_insensitive(self):
        """
        Tests that record_call_outcome_and_disconnect handles case-insensitive validation correctly.
        """
        # Test with valid call end state in lowercase (should work due to .upper())
        record_call_outcome_and_disconnect(
            callEndState="disconnect",  # lowercase, should be converted to uppercase
            dispositionCode="NOTIFICATION_NOT_RECEIVED"
        )
        status = db.DB["CONVERSATION_STATUS"]
        self.assertEqual(status["status"], "disconnect")
        
        # Test with valid call end state in mixed case (should work due to .upper())
        record_call_outcome_and_disconnect(
            callEndState="Do_Not_Call",  # mixed case, should be converted to uppercase
            dispositionCode="NOTIFICATION_NOT_RECEIVED"
        )
        status = db.DB["CONVERSATION_STATUS"]
        self.assertEqual(status["status"], "disconnect")

    def test_record_call_outcome_and_disconnect_all_valid_call_end_states(self):
        """
        Tests that record_call_outcome_and_disconnect accepts all valid call end states.
        """
        valid_states = [e.value for e in CallEndState]
        
        for state in valid_states:
            # Should not raise any exception
            record_call_outcome_and_disconnect(
                callEndState=state,
                dispositionCode="NOTIFICATION_NOT_RECEIVED"
            )
            status = db.DB["CONVERSATION_STATUS"]
            self.assertEqual(status["status"], "disconnect")

    def test_record_call_outcome_and_disconnect_invalid_disposition_code(self):
        """
        Tests that record_call_outcome_and_disconnect raises ValueError for invalid disposition code.
        """
        self.assert_error_behavior(
            record_call_outcome_and_disconnect,
            ValueError,
            "Invalid disposition code: INVALID_DISPOSITION",
            callEndState="disconnect",
            dispositionCode="INVALID_DISPOSITION"
        )

    def test_record_call_outcome_and_disconnect_invalid_disposition_code_case_insensitive(self):
        """
        Tests that record_call_outcome_and_disconnect handles case-insensitive validation for disposition codes.
        """
        # Test with valid disposition code in lowercase (should work due to .upper())
        record_call_outcome_and_disconnect(
            callEndState="disconnect",
            dispositionCode="notification_not_received"  # lowercase, should be converted to uppercase
        )
        status = db.DB["CONVERSATION_STATUS"]
        self.assertEqual(status["status"], "disconnect")
        
        # Test with valid disposition code in mixed case (should work due to .upper())
        record_call_outcome_and_disconnect(
            callEndState="disconnect",
            dispositionCode="Promo_Accepted"  # mixed case, should be converted to uppercase
        )
        status = db.DB["CONVERSATION_STATUS"]
        self.assertEqual(status["status"], "disconnect")

    def test_record_call_outcome_and_disconnect_all_valid_disposition_codes(self):
        """
        Tests that record_call_outcome_and_disconnect accepts all valid disposition codes.
        """
        valid_dispositions = [e.value for e in DispositionCode]
        
        for disposition in valid_dispositions:
            # Should not raise any exception
            record_call_outcome_and_disconnect(
                callEndState="disconnect",
                dispositionCode=disposition
            )
            status = db.DB["CONVERSATION_STATUS"]
            self.assertEqual(status["status"], "disconnect")

    def test_transfer_to_live_agent(self):
        """
        Tests that transfer_to_live_agent correctly sets the state for an
        agent transfer.
        """
        transfer_to_live_agent(
            callEndState="AGENT_TRANSFER",
            dispositionCode="NOTIFICATION_NOT_RECEIVED",
        )
        status = db.DB["CONVERSATION_STATUS"]
        self.assertEqual(status["status"], "live_agent_transfer")
        self.assertEqual(status["session_params"]["dispositionCode"], "NOTIFICATION_NOT_RECEIVED")

    def test_transfer_to_live_agent_with_spanish_language(self):
        """
        Tests that transfer_to_live_agent correctly sets the state for an
        agent transfer with Spanish language preference.
        where preferredLang is added to recorded_inputs when it's not "E".
        """
        transfer_to_live_agent(
            callEndState="AGENT_TRANSFER",
            dispositionCode="NOTIFICATION_NOT_RECEIVED",
            preferredLang="S",
        )
        status = db.DB["CONVERSATION_STATUS"]
        self.assertEqual(status["status"], "live_agent_transfer")
        self.assertEqual(status["session_params"]["dispositionCode"], "NOTIFICATION_NOT_RECEIVED")
        self.assertEqual(status["session_params"]["preferredLang"], "S")

    def test_transfer_to_live_agent_invalid_call_end_state(self):
        """
        Tests that transfer_to_live_agent raises ValueError for invalid call end state.
        """
        self.assert_error_behavior(
            transfer_to_live_agent,
            ValueError,
            "Invalid call end state: INVALID_STATE",
            callEndState="INVALID_STATE",
            dispositionCode="NOTIFICATION_NOT_RECEIVED"
        )

    def test_transfer_to_live_agent_invalid_disposition_code(self):
        """
        Tests that transfer_to_live_agent raises ValueError for invalid disposition code.
        """
        self.assert_error_behavior(
            transfer_to_live_agent,
            ValueError,
            "Invalid disposition code: INVALID_DISPOSITION",
            callEndState="AGENT_TRANSFER",
            dispositionCode="INVALID_DISPOSITION"
        )

    def test_transfer_to_live_agent_invalid_call_end_state_case_insensitive(self):
        """
        Tests that transfer_to_live_agent handles case-insensitive validation for call end states.
        """
        # Test with valid call end state in lowercase (should work due to .upper())
        transfer_to_live_agent(
            callEndState="agent_transfer",  # lowercase, should be converted to uppercase
            dispositionCode="NOTIFICATION_NOT_RECEIVED"
        )
        status = db.DB["CONVERSATION_STATUS"]
        self.assertEqual(status["status"], "live_agent_transfer")
        
        # Test with valid call end state in mixed case (should work due to .upper())
        transfer_to_live_agent(
            callEndState="Do_Not_Call",  # mixed case, should be converted to uppercase
            dispositionCode="NOTIFICATION_NOT_RECEIVED"
        )
        status = db.DB["CONVERSATION_STATUS"]
        self.assertEqual(status["status"], "live_agent_transfer")

    def test_transfer_to_live_agent_invalid_disposition_code_case_insensitive(self):
        """
        Tests that transfer_to_live_agent handles case-insensitive validation for disposition codes.
        """
        # Test with valid disposition code in lowercase (should work due to .upper())
        transfer_to_live_agent(
            callEndState="AGENT_TRANSFER",
            dispositionCode="notification_not_received"  # lowercase, should be converted to uppercase
        )
        status = db.DB["CONVERSATION_STATUS"]
        self.assertEqual(status["status"], "live_agent_transfer")
        
        # Test with valid disposition code in mixed case (should work due to .upper())
        transfer_to_live_agent(
            callEndState="AGENT_TRANSFER",
            dispositionCode="Promo_Accepted"  # mixed case, should be converted to uppercase
        )
        status = db.DB["CONVERSATION_STATUS"]
        self.assertEqual(status["status"], "live_agent_transfer")

    def test_transfer_to_live_agent_all_valid_call_end_states(self):
        """
        Tests that transfer_to_live_agent accepts all valid call end states.
        """
        valid_states = [e.value for e in CallEndState]
        
        for state in valid_states:
            # Should not raise any exception
            transfer_to_live_agent(
                callEndState=state,
                dispositionCode="NOTIFICATION_NOT_RECEIVED"
            )
            status = db.DB["CONVERSATION_STATUS"]
            self.assertEqual(status["status"], "live_agent_transfer")

    def test_transfer_to_live_agent_all_valid_disposition_codes(self):
        """
        Tests that transfer_to_live_agent accepts all valid disposition codes.
        """
        valid_dispositions = [e.value for e in DispositionCode]
        
        for disposition in valid_dispositions:
            # Should not raise any exception
            transfer_to_live_agent(
                callEndState="AGENT_TRANSFER",
                dispositionCode=disposition
            )
            status = db.DB["CONVERSATION_STATUS"]
            self.assertEqual(status["status"], "live_agent_transfer")

    def test_system_tools(self):
        """
        Tests the terminal system tools (done, fail, cancel, escalate).
        """
        done()
        self.assertEqual(db.DB["SESSION_STATUS"]["status"], "done")

        fail()
        self.assertEqual(db.DB["SESSION_STATUS"]["status"], "fail")

        cancel()
        self.assertEqual(db.DB["SESSION_STATUS"]["status"], "cancel")

        escalate()
        self.assertEqual(db.DB["SESSION_STATUS"]["status"], "escalate")


if __name__ == "__main__":
    unittest.main()
