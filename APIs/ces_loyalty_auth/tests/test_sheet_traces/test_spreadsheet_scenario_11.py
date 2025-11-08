"""
Test case for the spreadsheet scenario CES_outbound_loyalty_with_auth_data_train_vcycled_conversation_11.

This test follows the exact conversation flow from the spreadsheet, including:
- Initial call with get_pre_authentication_call_data
- User responds with uncertainty about who's calling
- Assistant asks for identity confirmation
- User asks what the call is about instead of confirming identity
- Assistant terminates the call due to inability to verify identity
"""

import unittest

# Absolute imports for the new folder structure
from ... import (
    get_pre_authentication_call_data,
    record_call_outcome_and_disconnect,
    done,
)
from ces_loyalty_auth.SimulationEngine import db, utils
from ces_loyalty_auth.tests.loyalty_auth_base_exception import LoyaltyAuthBaseTestCase


class TestSpreadsheetScenario11(LoyaltyAuthBaseTestCase):
    """
    Test case that replicates the exact conversation flow from spreadsheet
    CES_outbound_loyalty_with_auth_data_train_vcycled_conversation_11.
    """

    def setUp(self):
        """Set up the test data matching the spreadsheet scenario."""
        super().setUp()
        
        # Reset the DB to a clean state
        db.reset_db()
        
        # Set up the pre-authentication data for John Smith
        self.setup_preauth_data()

    def setup_preauth_data(self):
        """Set up pre-authentication data matching the spreadsheet."""
        preauth_data = {
            "sessionInfo": {
                "parameters": {
                    "autoPayPaperFreeDiscountAmountInfo": {},
                    "loyaltyOffersStatusCode": "00000",
                    "unlimitedPlanPerks": [],
                    "sundayMobileOST": {},
                    "accountNumber": "123456789",
                    "firstName": "John",
                    "myPlanFeatures": {},
                    "loyaltyOffers": [
                        {
                            "offerOrder": "1",
                            "OfferDesc": "10% off your next bill",
                            "offerType": "Discount",
                            "OfferID": "1"
                        }
                    ],
                    "myPlanPerks": {},
                    "myPlanPricingDetails": {},
                    "hasMtnLoyaltyOffers": True,
                    "availablePerks": [],
                    "status": "Success",
                    "preferredFirstName": "John",
                    "customerName": "John Smith",
                    "sundayMobileValueProposition": {},
                    "statusMessage": "Success",
                    "statusCode": "00000"
                }
            }
        }
        
        utils.set_preauth_data(preauth_data)

    def test_spreadsheet_scenario_conversation_flow(self):
        """
        Test the complete conversation flow from the spreadsheet scenario.
        This follows the exact steps from CES_outbound_loyalty_with_auth_data_train_vcycled_conversation_11.
        """
        
        # Step 1: Initial call - get pre-authentication data (Turn 1 in spreadsheet)
        # This corresponds to the SYSTEM_1 role calling get_pre_authentication_call_data
        preauth_response = get_pre_authentication_call_data()
        
        # Verify the response structure and data matches the spreadsheet
        self.assertEqual(preauth_response["sessionInfo"]["parameters"]["customerName"], "John Smith")
        self.assertEqual(preauth_response["sessionInfo"]["parameters"]["status"], "Success")
        self.assertEqual(preauth_response["sessionInfo"]["parameters"]["statusCode"], "00000")
        self.assertTrue(preauth_response["sessionInfo"]["parameters"]["hasMtnLoyaltyOffers"])
        
        # Verify loyalty offers are present
        loyalty_offers = preauth_response["sessionInfo"]["parameters"]["loyaltyOffers"]
        self.assertEqual(len(loyalty_offers), 1)
        self.assertEqual(loyalty_offers[0]["OfferID"], "1")
        self.assertEqual(loyalty_offers[0]["OfferDesc"], "10% off your next bill")
        self.assertEqual(loyalty_offers[0]["offerType"], "Discount")
        self.assertEqual(loyalty_offers[0]["offerOrder"], "1")

        # Step 2: Assistant presents initial greeting and asks for identity verification (Turn 1 in spreadsheet)
        # The assistant should say: "To opt-out of future calls, say 'Do Not Call' or press 9. 
        # Just a heads up, Sunday Mobile and our partners may record or monitor this call for quality, 
        # systems training and personalization. Am I speaking with John Smith?"
        
        # Step 3: User responds with uncertainty (Turn 2 in spreadsheet)
        # User says: "I'm not sure, who's calling?"
        # This is an invalid response that doesn't confirm identity
        
        # Step 4: Assistant asks for identity confirmation again (Turn 3 in spreadsheet)
        # Assistant should say: "I didn't quite catch that. Could you confirm if you are John Smith?"
        
        # Step 5: User asks about the purpose instead of confirming identity (Turn 4 in spreadsheet)
        # User says: "Can you tell me what this is about first?"
        # This is still not a valid identity confirmation
        
        # Step 6: Assistant terminates the call (Turn 5 in spreadsheet)
        # Since the user has not provided clear identity confirmation after multiple attempts,
        # the assistant should terminate the call
        
        # The assistant calls record_call_outcome_and_disconnect with the disposition code
        # from the spreadsheet: 'отказался от аутентификации' (refused authentication)
        disconnect_response = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT",
            dispositionCode="AUTH_DECLINED",
            preferredLang="E"
        )
        
        # Verify disconnect response
        self.assertEqual(disconnect_response["status"], "success")
        
        # Step 7: Assistant calls done() to complete the call termination (Turn 5 in spreadsheet)
        done_response = done()
        
        # Verify done response (should be empty string)
        self.assertEqual(done_response, "")

    def test_preauth_data_structure(self):
        """Test that the pre-authentication data structure matches the spreadsheet exactly."""
        preauth_response = get_pre_authentication_call_data()
        
        # Verify all required fields are present
        session_info = preauth_response["sessionInfo"]
        parameters = session_info["parameters"]
        
        # Verify critical parameters from the spreadsheet
        self.assertEqual(parameters["accountNumber"], "123456789")
        self.assertEqual(parameters["firstName"], "John")
        self.assertEqual(parameters["preferredFirstName"], "John")
        self.assertEqual(parameters["customerName"], "John Smith")
        self.assertEqual(parameters["status"], "Success")
        self.assertEqual(parameters["statusCode"], "00000")
        self.assertEqual(parameters["statusMessage"], "Success")
        self.assertEqual(parameters["loyaltyOffersStatusCode"], "00000")
        self.assertTrue(parameters["hasMtnLoyaltyOffers"])
        
        # Verify loyalty offers structure
        loyalty_offers = parameters["loyaltyOffers"]
        self.assertIsInstance(loyalty_offers, list)
        self.assertEqual(len(loyalty_offers), 1)
        
        offer = loyalty_offers[0]
        self.assertEqual(offer["offerOrder"], "1")
        self.assertEqual(offer["OfferDesc"], "10% off your next bill")
        self.assertEqual(offer["offerType"], "Discount")
        self.assertEqual(offer["OfferID"], "1")
        
        # Verify other parameters are present (even if empty)
        self.assertIn("autoPayPaperFreeDiscountAmountInfo", parameters)
        self.assertIn("unlimitedPlanPerks", parameters)
        self.assertIn("sundayMobileOST", parameters)
        self.assertIn("myPlanFeatures", parameters)
        self.assertIn("myPlanPerks", parameters)
        self.assertIn("myPlanPricingDetails", parameters)
        self.assertIn("availablePerks", parameters)
        self.assertIn("sundayMobileValueProposition", parameters)

    def test_conversation_flow_validation(self):
        """
        Test that the conversation flow follows the exact pattern from the spreadsheet:
        1. get_pre_authentication_call_data() is called
        2. Identity verification fails due to user responses
        3. Call is terminated with record_call_outcome_and_disconnect()
        4. done() is called to complete termination
        """
        
        # Step 1: Get pre-authentication data
        preauth_response = get_pre_authentication_call_data()
        self.assertIsNotNone(preauth_response)
        self.assertEqual(preauth_response["sessionInfo"]["parameters"]["customerName"], "John Smith")
        
        # Step 2: Simulate the conversation flow where identity verification fails
        # The user responses "I'm not sure, who's calling?" and "Can you tell me what this is about first?"
        # are not valid identity confirmations, so the assistant should terminate
        
        # Step 3: Call termination
        disconnect_response = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT",
            dispositionCode="AUTH_DECLINED",
            preferredLang="E"
        )
        self.assertEqual(disconnect_response["status"], "success")
        
        # Step 4: Complete termination
        done_response = done()
        self.assertEqual(done_response, "")


if __name__ == "__main__":
    unittest.main()
