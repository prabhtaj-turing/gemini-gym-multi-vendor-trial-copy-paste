"""
Smoke tests for the CES Loyalty Auth API.

This module contains a series of high-level tests to ensure that the main
functions of the CES Loyalty Auth API are available and executable without
raising unexpected errors.
"""

import unittest
import json
from .. import (
    cancel,
    done,
    enroll_in_offer,
    escalate,
    fail,
    get_authenticated_customer_profile,
    get_pre_authentication_call_data,
    manage_customer_authentication,
    record_call_outcome_and_disconnect,
    transfer_to_live_agent,
)
from ces_loyalty_auth.SimulationEngine.db import DB
from ces_loyalty_auth.SimulationEngine import db, utils
from .loyalty_auth_base_exception import LoyaltyAuthBaseTestCase


class TestSmoke(LoyaltyAuthBaseTestCase):
    """
    Test suite for basic smoke testing of the CES Loyalty Auth API functions.
    """

    def test_get_authenticated_customer_profile_smoke(self):
        """
        Smoke test for get_authenticated_customer_profile to ensure it can be called.
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
        utils.set_auth_result(auth_result)
        utils.update_auth_status()

        # Provide a minimal valid profile to prevent validation errors
        DB["PROFILE_AFTER_AUTH"] = {
            "customerProfile": {
                "customerName": "Test User",
                "numberOfLines": "1",
                "accountNumber": "12345",
                "lines": [
                    {
                        "mtn": "555-555-5555",
                        "mtnStatus": {"isActive": True},
                        "equipmentInfos": {},
                    }
                ],
            }
        }
        # Set AUTH_STATUS directly to ensure authentication check passes
        db.DB["AUTH_STATUS"] = "ACCEPT"
        get_authenticated_customer_profile(authstatus="ACCEPT")

    def test_manage_customer_authentication_smoke(self):
        """
        Smoke test for manage_customer_authentication to ensure it can be called.
        """
        auth_result = {
            "sessionInfo": {
                "parameters": {
                    "sessionMap": {
                        "adaptiveAuthentication": json.dumps({"authstatus": "ACCEPT"})
                    },
                    "authstate": "ACCEPT",
                    "sessionId": "S123",
                    "statusMessage": "Success",
                }
            }
        }
        utils.set_auth_result(auth_result)
        # The function should work now that AUTH_RESULT is properly set
        manage_customer_authentication(authstate="AUTHENTICATION_INIT")

    def test_get_pre_authentication_call_data_smoke(self):
        """
        Smoke test for get_pre_authentication_call_data to ensure it can be called.
        """
        get_pre_authentication_call_data()

    def test_record_call_outcome_and_disconnect_smoke(self):
        """
        Smoke test for record_call_outcome_and_disconnect to ensure it can be called.
        """
        record_call_outcome_and_disconnect(
            callEndState="DISCONNECT", dispositionCode="PROMO_ACCEPTED"
        )

    def test_transfer_to_live_agent_smoke(self):
        """
        Smoke test for transfer_to_live_agent to ensure it can be called.
        """
        transfer_to_live_agent(
            callEndState="AGENT_TRANSFER", dispositionCode="AGENT_TRANSFER"
        )

    def test_enroll_in_offer_smoke(self):
        """
        Smoke test for enroll_in_offer to ensure it can be called.
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
        utils.set_auth_result(auth_result)
        utils.update_auth_status()
        # Set AUTH_STATUS directly to ensure authentication check passes
        db.DB["AUTH_STATUS"] = "ACCEPT"
        enroll_in_offer(accountNumber="56985362456-00001", offerId="9635")

    def test_done_smoke(self):
        """
        Smoke test for the done function to ensure it is callable.
        """
        done()

    def test_fail_smoke(self):
        """
        Smoke test for the fail function to ensure it is callable.
        """
        fail(summary="Unable to understand user")

    def test_cancel_smoke(self):
        """
        Smoke test for the cancel function to ensure it is callable.
        """
        cancel(summary="User cancelled request")

    def test_escalate_smoke(self):
        """
        Smoke test for the escalate function to ensure it is callable.
        """
        escalate()


if __name__ == "__main__":
    unittest.main()
