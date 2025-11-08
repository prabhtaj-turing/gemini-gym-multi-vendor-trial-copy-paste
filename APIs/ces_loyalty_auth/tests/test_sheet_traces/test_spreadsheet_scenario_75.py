"""
Test case for the spreadsheet scenario CES_outbound_loyalty_0.3_conversation_75.

This test follows the exact conversation flow from the spreadsheet, including:
- Initial identity verification with Michael Jones
- Loyalty offer presentation
- Authentication flow where user initially can't receive texts but then accepts
- Successful enrollment
- Account information request
- Plan upgrade inquiry and agent transfer
- Final call termination
"""

import unittest

# Absolute imports for the new folder structure
from ... import (
    get_pre_authentication_call_data,
    manage_customer_authentication,
    get_authenticated_customer_profile,
    enroll_in_offer,
    transfer_to_live_agent,
    done,
    escalate,
    record_call_outcome_and_disconnect,
)
from ces_loyalty_auth.SimulationEngine import db, utils
from ces_loyalty_auth.tests.loyalty_auth_base_exception import LoyaltyAuthBaseTestCase


class TestSpreadsheetScenario75(LoyaltyAuthBaseTestCase):
    """
    Test case that replicates the exact conversation flow from spreadsheet
    CES_outbound_loyalty_0.3_conversation_75.
    """

    def setUp(self):
        """Set up the test data matching the spreadsheet scenario."""
        super().setUp()
        
        # Reset the DB to a clean state
        db.reset_db()
        
        # Set up the pre-authentication data for Michael Jones
        self.setup_preauth_data()
        
        # Set up authentication flow data
        self.setup_auth_data()
        
        # Set up authenticated customer profile data
        self.setup_authenticated_profile_data()

    def setup_preauth_data(self):
        """Set up pre-authentication data matching the spreadsheet."""
        preauth_data = {
            "sessionInfo": {
                "parameters": {
                    "status": "SUCCESS",
                    "statusMessage": "verified",
                    "hasMtnLoyaltyOffers": True,
                    "myPlanFeatures": {
                        "inclusions": [
                            "network", "ultimate phone upgrade", "mobile hotspot",
                            "enhanced video calling", "streaming quality", "talk & text",
                            "plan discounts", "high speed international data, talk & text (while traveling abroad)",
                            "international calling from the u.s.", "mexico and canada usage",
                            "speed boost", "international text", "mobile + home discount",
                            "other services & perks", "optional services & perks available to add"
                        ],
                        "sunday mobile ultimate": [
                            "Sunday Mobile's reliable fastest 5g up to 10x faster than 4g lte. No matter how much is used.",
                            "Truly unlimited premium network access on the smartphone includes: 5g uw, 5g, 4g lte.",
                            "Unlimited (domestic) mobile hotspot includes 60 GB per line. International hotspot included with 10 GB roaming high-speed data per month.",
                            "Enhanced video calling delivers optimized video and sound quality on select apps such as Facetime, WhatsApp and Zoom; available in 150+ metro areas.",
                            "1080p HD & 4K-quality streaming available.",
                            "Unlimited talk & text.",
                            "50% off select connected devices with Unlimited Ultimate plan."
                        ]
                    },
                    "preferredFirstName": "Michael",
                    "firstName": "Michael",
                    "customerName": "Michael Jones",
                    "accountNumber": "741852963",
                    "statusCode": "200",
                    "loyaltyOffersStatusCode": "available",
                    "loyaltyOffers": [
                        {
                            "OfferID": "LOYALTY123",
                            "OfferDesc": "Save $10 per month for the next 12 months",
                            "offerType": "loyaltyDiscount",
                            "offerOrder": "1",
                            "mtn": "9082207890"
                        }
                    ],
                    "availablePerks": [
                        {"perkType": "Cloud Storage", "perkAmount": "50 GB data"},
                        {"perkType": "Entertainment", "perkAmount": "Disney+ subscription"}
                    ],
                    "unlimitedPlanPerks": [],
                    "sundayMobileOST": {
                        "ostCustomerStatusCode": "ACTIVE",
                        "OSTOptInStatus": "ENROLLED",
                        "OSTOptInDate": "2024-03-15",
                        "OSTStatusMes": "Opted into Sunday OST perks"
                    },
                    "sundayMobileValueProposition": {
                        "hasUnlimitedPlanPerks": "True",
                        "u": "Unlimited Ultimate Value",
                        "unlimitedPlanValue": "Best value with premium data + perks"
                    },
                    "autoPayPaperFreeDiscountAmountInfo": {
                        "hasApPfls": "True",
                        "apPflsDiscountAmount": "30.00"
                    },
                    "myPlanPricingDetails": {
                        "myPlanDiscount": "10.00",
                        "myplanDescription": "Unlimited Ultimate Plan",
                        "perkAmount": "5.00",
                        "myplanCode": "ULT123",
                        "is": "active"
                    },
                    "myPlanPerks": {
                        "planCode": [
                            {
                                "monthly_value": "40",
                                "perk": "Disney+ Bundle",
                                "savings": "2200",
                                "monthly_cost": "included",
                                "description": "Entertainment perk"
                            }
                        ],
                        "perkAmount": [
                            {
                                "monthly_value": "30",
                                "perk": "Cloud Storage",
                                "savings": "3000",
                                "monthly_cost": "included",
                                "description": "Extra cloud storage perk"
                            }
                        ],
                        "perkDescription": [
                            {
                                "monthly_value": "50",
                                "perk": "Premium Network",
                                "savings": "3300",
                                "monthly_cost": "included",
                                "description": "Unlimited premium network"
                            }
                        ]
                    },
                    "lines": [
                        {
                            "autoPayReflected": False,
                            "mtn": "9082207890",
                            "mtnStatus": {
                                "involuntarySuspendedWithNonPayment": False,
                                "isActive": True,
                                "isSuspendedWithBilling": False,
                                "mtnStatusReasonCode": "",
                                "voluntarySuspended": False,
                                "involuntarySuspended": False,
                                "isSuspendedWithoutBilling": False
                            },
                            "equipmentInfos": {
                                "deviceInfo": {
                                    "displayName": "Apple iPhone 14 Pro 256GB in Space Black",
                                    "category": {
                                        "connectedDevice": False,
                                        "smartwatch": False,
                                        "homeSolutions": False,
                                        "internetDevice": False,
                                        "basicphone": False,
                                        "WSOnly": False,
                                        "tablet": False,
                                        "homePC": False,
                                        "virtualDevice": False,
                                        "telematics": False,
                                        "laptop": False,
                                        "smartphone": True
                                    },
                                    "deviceUrl": "https://ss7.sundaymobile.com/is/image/SundayMobile/iphone-14-pro-space-black",
                                    "deviceType": {
                                        "jetPack4G": False,
                                        "deskphone": False,
                                        "homeFusionDevice": False,
                                        "device3G": False,
                                        "device5GE": True,
                                        "backupRouter4G": False,
                                        "autoAttendant": False,
                                        "description": "Connected Device",
                                        "device5GA": False,
                                        "device4G": False,
                                        "overTheTop": False,
                                        "antenna5G": False,
                                        "home5G": False,
                                        "huntGroup": False,
                                        "jetPack5G": False,
                                        "device4GO": False
                                    }
                                }
                            },
                            "pricePlanInfo": {
                                "description": "UNLIMITED ULTIMATE",
                                "planSkuName": "Unlimited Ultimate",
                                "accessCharge": {
                                    "monthlyAccessCharge": "65.00",
                                    "finalPriceWithLACAndDiscount": "0.00",
                                    "discountedCharge": "65.00",
                                    "finalPriceWithLAC": "0.00",
                                    "discountedAccessChargeWithPerk": "75.00"
                                },
                                "planId": "69185",
                                "effectiveDate": "2023-11-20",
                                "planDisplayName": "Unlimited Ultimate",
                                "planCategoryName": "MY PLAN"
                            },
                            "mobileInfoAttributes": {'accessRoles': {'member': 'False', 'owner': 'True', 'manager': 'False'}},
                            "equipmentUpgradeEligibility": {'buyoutEligible': 'False', 'buyoutRestricted': 'False', 'upgradeEligibilityDate': '08/12/2023', 'earlyUpgradeEligible': 'False', 'alwaysUpgradeEligible': 'True', 'upgradeEligible': 'True'}
                        }
                    ]
                }
            }
        }
        
        utils.set_preauth_data(preauth_data)

    def setup_auth_data(self):
        """Set up authentication data for the flow."""
        # Don't set up authentication data initially - let the test control the flow
        # The authentication will be set up during the test execution
        pass

    def setup_authenticated_profile_data(self):
        """Set up the authenticated customer profile data."""
        profile_data = {
            "customerProfile": {
                "paymentInfo": {
                    "enrolledInAutopay": False,
                    "invoiceDate": "05/25/2025",
                    "lastPaymentDate": "05/28/2025",
                    "paymentDueDate": "06/17/2025",
                    "pastDueDays": "0",
                    "enrolledInPaperFree": True,
                    "lastPaymentAmount": "336.65",
                    "eligibleForPaperFree": False,
                    "currentCharges": "336.65",
                    "arPastDueBalance": "0.00",
                    "paymentHistory": [
                        {
                            "totalBalance": "336.65",
                            "adjustedPreviousAmount": "0.00",
                            "amountPaid": "219.93",
                            "billCycleStartDate": "04/26/2025",
                            "invoiceDate": "05/25/2025",
                            "billCycleEndDate": "05/25/2025"
                        },
                        {
                            "invoiceDate": "04/25/2025",
                            "billCycleEndDate": "04/25/2025",
                            "billCycleStartDate": "04/07/2025",
                            "adjustedPreviousAmount": "0.00",
                            "amountPaid": "372.35",
                            "totalBalance": "219.93"
                        },
                        {
                            "adjustedPreviousAmount": "0.00",
                            "billCycleEndDate": "04/06/2025",
                            "billCycleStartDate": "03/07/2025",
                            "invoiceDate": "04/06/2025",
                            "totalBalance": "372.35",
                            "amountPaid": "347.09"
                        }
                    ],
                    "pastDueBalance": "0.00",
                    "outstandingBalance": "0.00"
                },
                "accountNumber": "741852963",
                "customerFirstName": "John",
                "customerLastName": "Smith",
                "greetByName": "John",
                "eligibleForAutopay": "true",
                "customerRole": "accountHolder",
                "customerName": "John Smith",
                "autopayDiscountAmount": "30.00",
                "numberOfLines": "",
                "lines": [
                    {
                        "autoPayReflected": False,
                        "mtn": "9082207890",
                        "mtnStatus": {
                            "involuntarySuspendedWithNonPayment": False,
                            "isActive": True,
                            "isSuspendedWithBilling": False,
                            "mtnStatusReasonCode": "",
                            "voluntarySuspended": False,
                            "involuntarySuspended": False,
                            "isSuspendedWithoutBilling": False
                        },
                        "equipmentInfos": {
                            "deviceInfo": {
                                "displayName": "Apple iPhone 14 Pro 256GB in Space Black",
                                "category": {
                                    "connectedDevice": False,
                                    "smartwatch": False,
                                    "homeSolutions": False,
                                    "internetDevice": False,
                                    "basicphone": False,
                                    "WSOnly": False,
                                    "tablet": False,
                                    "homePC": False,
                                    "virtualDevice": False,
                                    "telematics": False,
                                    "laptop": False,
                                    "smartphone": True
                                }
                            }
                        }
                    }
                ]
            }
        }
        
        utils.set_customer_profile(profile_data)

    def test_spreadsheet_scenario_conversation_flow(self):
        """
        Test the complete conversation flow from the spreadsheet scenario.
        This follows the exact steps from CES_outbound_loyalty_0.3_conversation_75.
        """
        
        # Step 1: Initial call - get pre-authentication data
        # This corresponds to turn 1 in the spreadsheet
        preauth_response = get_pre_authentication_call_data()
        
        # Verify the response structure and data
        self.assertEqual(preauth_response["sessionInfo"]["parameters"]["customerName"], "Michael Jones")
        self.assertEqual(preauth_response["sessionInfo"]["parameters"]["accountNumber"], "741852963")
        self.assertEqual(preauth_response["sessionInfo"]["parameters"]["status"], "SUCCESS")
        self.assertTrue(preauth_response["sessionInfo"]["parameters"]["hasMtnLoyaltyOffers"])
        
        # Verify loyalty offers are present
        loyalty_offers = preauth_response["sessionInfo"]["parameters"]["loyaltyOffers"]
        self.assertEqual(len(loyalty_offers), 1)
        self.assertEqual(loyalty_offers[0]["OfferID"], "LOYALTY123")
        self.assertEqual(loyalty_offers[0]["OfferDesc"], "Save $10 per month for the next 12 months")
        
        # Step 2: Identity verification (turn 2 in spreadsheet)
        # User responds "Who is this?" (turn 2)
        # Assistant should ask for clarification (turn 3)
        
        # Step 3: User confirms identity (turn 4)
        # User says "Yes, this is Michael." (turn 4)
        
        # Step 4: Legal disclosure and offer introduction (turn 5)
        # Assistant presents the loyalty offer for phone line ending in 7 8 9 0
        
        # Step 5: User accepts offer (turn 6)
        # User says "Ok, I'm interested. What do I need to do?" (turn 6)
        
        # Step 6: Authentication gate check (turn 7)
        # Assistant asks about authentication
        
        # Step 7: User initially can't receive texts (turn 8)
        # User says "I can't receive texts on this phone." but then changes to "Yes send the link now"
        
        # Step 8: Authentication initiation (turn 9)
        # Set up authentication initiation data
        auth_init_data = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_INIT",
                    "statusCode": "0",
                    "statusMessage": "Authentication initiated",
                    "sessionMap": None,
                    "error": None,
                    "noService": None,
                    "sessionId": "12345-67890-ABCDE",
                    "authmode": "TEXT",
                    "gotoPage": None
                }
            }
        }
        utils.set_auth_result(auth_init_data)
        
        # Assistant calls manage_customer_authentication with AUTHENTICATION_INIT
        auth_init_response = manage_customer_authentication(authstate="AUTHENTICATION_INIT")
        
        # Verify authentication initiation response
        self.assertEqual(auth_init_response["sessionInfo"]["parameters"]["authstate"], "AUTHENTICATION_INIT")
        self.assertEqual(auth_init_response["sessionInfo"]["parameters"]["statusCode"], "200")
        self.assertEqual(auth_init_response["sessionInfo"]["parameters"]["statusMessage"], "Authentication SMS sent successfully")
        
        # Step 9: User confirms ready for authentication (turn 10)
        # User says "Yes" but then "Where was the link sent to?"
        
        # Step 10: Authentication status check (turn 11)
        # Set up authentication pending data
        auth_pending_data = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "PENDING",
                    "statusCode": "0",
                    "statusMessage": "Authentication Pending",
                    "sessionMap": None,
                    "error": None,
                    "noService": None,
                    "sessionId": "12345-67890-ABCDE",
                    "authmode": "TEXT",
                    "gotoPage": None
                }
            }
        }
        utils.set_auth_result(auth_pending_data)
        
        # Assistant calls manage_customer_authentication with AUTHENTICATION_STATUS
        auth_status_response = manage_customer_authentication(authstate="AUTHENTICATION_STATUS")
        
        # Verify authentication status response
        self.assertEqual(auth_status_response["sessionInfo"]["parameters"]["authstate"], "PENDING")
        self.assertEqual(auth_status_response["sessionInfo"]["parameters"]["statusCode"], "0")
        self.assertEqual(auth_status_response["sessionInfo"]["parameters"]["statusMessage"], "Authentication Pending")
        
        # Step 11: User completes authentication (turn 12)
        # User says "All done."
        
        # Step 12: Final authentication status check (turn 13)
        # Set up authentication success data
        auth_success_data = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "ACCEPT",
                    "statusCode": "success",
                    "statusMessage": "Authentication successful",
                    "sessionMap": None,
                    "error": None,
                    "noService": None,
                    "sessionId": "12345-67890-ABCDE",
                    "authmode": "TEXT",
                    "gotoPage": None
                }
            }
        }
        utils.set_auth_result(auth_success_data)
        utils.update_auth_status()  # This processes the result and sets AUTH_STATUS
        
        # Assistant calls manage_customer_authentication again to check status
        final_auth_response = manage_customer_authentication(authstate="AUTHENTICATION_STATUS")
        
        # Verify authentication success
        self.assertEqual(final_auth_response["sessionInfo"]["parameters"]["authstate"], "ACCEPT")
        self.assertEqual(final_auth_response["sessionInfo"]["parameters"]["statusCode"], "success")
        self.assertEqual(final_auth_response["sessionInfo"]["parameters"]["statusMessage"], "Authentication successful")
        
        # Step 13: Get authenticated customer profile (turn 13)
        # Set up the authenticated customer profile data
        profile_data = {
            "customerProfile": {
                "paymentInfo": {
                    "enrolledInAutopay": False,
                    "invoiceDate": "05/25/2025",
                    "lastPaymentDate": "05/28/2025",
                    "paymentDueDate": "06/17/2025",
                    "pastDueDays": "0",
                    "enrolledInPaperFree": True,
                    "lastPaymentAmount": "336.65",
                    "eligibleForPaperFree": False,
                    "currentCharges": "336.65",
                    "arPastDueBalance": "0.00",
                    "paymentHistory": [
                        {
                            "totalBalance": "336.65",
                            "adjustedPreviousAmount": "0.00",
                            "amountPaid": "219.93",
                            "billCycleStartDate": "04/26/2025",
                            "invoiceDate": "05/25/2025",
                            "billCycleEndDate": "05/25/2025"
                        },
                        {
                            "invoiceDate": "04/25/2025",
                            "billCycleEndDate": "04/25/2025",
                            "billCycleStartDate": "04/07/2025",
                            "adjustedPreviousAmount": "0.00",
                            "amountPaid": "372.35",
                            "totalBalance": "219.93"
                        },
                        {
                            "adjustedPreviousAmount": "0.00",
                            "billCycleEndDate": "04/06/2025",
                            "billCycleStartDate": "03/07/2025",
                            "invoiceDate": "04/06/2025",
                            "totalBalance": "372.35",
                            "amountPaid": "347.09"
                        }
                    ],
                    "pastDueBalance": "0.00",
                    "outstandingBalance": "0.00"
                },
                "accountNumber": "741852963",
                "customerFirstName": "John",
                "customerLastName": "Smith",
                "greetByName": "John",
                "eligibleForAutopay": "true",
                "customerRole": "accountHolder",
                "customerName": "John Smith",
                "autopayDiscountAmount": "30.00",
                "numberOfLines": "",
                "lines": [
                    {
                        "autoPayReflected": False,
                        "mtn": "9082207890",
                        "mtnStatus": {
                            "involuntarySuspendedWithNonPayment": False,
                            "isActive": True,
                            "isSuspendedWithBilling": False,
                            "mtnStatusReasonCode": "",
                            "voluntarySuspended": False,
                            "involuntarySuspended": False,
                            "isSuspendedWithoutBilling": False
                        },
                        "equipmentInfos": {
                            "deviceInfo": {
                                "displayName": "Apple iPhone 14 Pro 256GB in Space Black",
                                "category": {
                                    "connectedDevice": False,
                                    "smartwatch": False,
                                    "homeSolutions": False,
                                    "internetDevice": False,
                                    "basicphone": False,
                                    "WSOnly": False,
                                    "tablet": False,
                                    "homePC": False,
                                    "virtualDevice": False,
                                    "telematics": False,
                                    "laptop": False,
                                    "smartphone": True
                                }
                            }
                        }
                    }
                ]
            }
        }
        utils.set_customer_profile(profile_data)
        
        # Set the AUTH_STATUS in the database to "ACCEPT" to match what the function expects
        db.DB["AUTH_STATUS"] = "ACCEPT"
        
        # Assistant calls get_authenticated_customer_profile
        profile_response = get_authenticated_customer_profile(authstatus="ACCEPT")
        
        # Verify profile response
        self.assertEqual(profile_response["customerProfile"]["customerName"], "John Smith")
        self.assertEqual(profile_response["customerProfile"]["accountNumber"], "741852963")
        self.assertEqual(profile_response["customerProfile"]["customerFirstName"], "John")
        self.assertEqual(profile_response["customerProfile"]["customerLastName"], "Smith")
        
        # Step 14: Enroll in offer (turn 13)
        # Assistant calls enroll_in_offer
        enrollment_response = enroll_in_offer(
            accountNumber="741852963",
            offerId="LOYALTY123"
        )
        
        # Verify enrollment response
        self.assertEqual(enrollment_response["status"], "success")
        
        # Step 15: User requests account information (turn 14)
        # User says "Alright, what's my current plan details?"
        
        # Step 16: User requests plan upgrade (turn 16)
        # User says "Got it, thank you. Is there a higher grade plan I can be upgrade to if yes at what cost?"
        
        # Step 17: Agent transfer for plan upgrade (turn 17)
        # Assistant offers to transfer to agent for plan changes
        
        # Step 18: User declines transfer (turn 18)
        # User says "No"
        
        # Step 19: Final wrap-up (turn 19)
        # Assistant asks if there's anything else regarding the loyalty offer
        
        # Step 20: User declines further assistance (turn 20)
        # User says "No I'm good for now."
        
        # Step 21: Call termination (turn 21)
        # Assistant calls record_call_outcome_and_disconnect
        disconnect_response = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT"
        )
        
        # Verify disconnect response
        self.assertEqual(disconnect_response["status"], "success")
        
        # Step 22: Done (turn 21)
        # Assistant calls done
        done_response = done()
        
        # Verify done response (should be empty string)
        self.assertEqual(done_response, "")

    def test_authentication_flow_variations(self):
        """
        Test different authentication flow scenarios that could occur.
        """
        
        # Set up authentication initiation data
        auth_init_data = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_INIT",
                    "statusCode": "0",
                    "statusMessage": "Authentication initiated",
                    "sessionMap": None,
                    "error": None,
                    "noService": None,
                    "sessionId": "12345-67890-ABCDE",
                    "authmode": "TEXT",
                    "gotoPage": None
                }
            }
        }
        utils.set_auth_result(auth_init_data)
        
        # Test authentication initiation
        auth_init_response = manage_customer_authentication(authstate="AUTHENTICATION_INIT")
        self.assertEqual(auth_init_response["sessionInfo"]["parameters"]["authstate"], "AUTHENTICATION_INIT")
        
        # Set up authentication success data
        auth_success_data = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "ACCEPT",
                    "statusCode": "success",
                    "statusMessage": "Authentication successful",
                    "sessionMap": None,
                    "error": None,
                    "noService": None,
                    "sessionId": "12345-67890-ABCDE",
                    "authmode": "TEXT",
                    "gotoPage": None
                }
            }
        }
        utils.set_auth_result(auth_success_data)
        utils.update_auth_status()
        
        # Test authentication status check
        auth_status_response = manage_customer_authentication(authstate="AUTHENTICATION_STATUS")
        self.assertEqual(auth_status_response["sessionInfo"]["parameters"]["authstate"], "ACCEPT")
        
        # Set up customer profile data
        profile_data = {
            "customerProfile": {
                "customerName": "John Smith",
                "accountNumber": "741852963",
                "customerFirstName": "John",
                "customerLastName": "Smith",
                "numberOfLines": "1",
                "lines": [],
                "autopayDiscountAmount": "30.00",
                "eligibleForAutopay": "true",
                "customerRole": "accountHolder",
                "greetByName": "John",
                "paymentInfo": {"enrolledInAutopay": False}
            }
        }
        utils.set_customer_profile(profile_data)
        
        # Set the AUTH_STATUS in the database to "ACCEPT" to match what the function expects
        db.DB["AUTH_STATUS"] = "ACCEPT"
        
        # Test getting authenticated profile
        profile_response = get_authenticated_customer_profile(authstatus="ACCEPT")
        self.assertIn("customerProfile", profile_response)
        self.assertEqual(profile_response["customerProfile"]["customerName"], "John Smith")

    def test_offer_enrollment_flow(self):
        """
        Test the offer enrollment flow with proper authentication.
        """
        
        # Set up authentication success data
        auth_success_data = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "ACCEPT",
                    "statusCode": "success",
                    "statusMessage": "Authentication successful",
                    "sessionMap": None,
                    "error": None,
                    "noService": None,
                    "sessionId": "12345-67890-ABCDE",
                    "authmode": "TEXT",
                    "gotoPage": None
                }
            }
        }
        utils.set_auth_result(auth_success_data)
        utils.update_auth_status()
        
        # Ensure authentication is successful
        auth_response = manage_customer_authentication(authstate="AUTHENTICATION_STATUS")
        self.assertEqual(auth_response["sessionInfo"]["parameters"]["authstate"], "ACCEPT")
        
        # Set up customer profile data
        profile_data = {
            "customerProfile": {
                "customerName": "John Smith",
                "accountNumber": "741852963",
                "customerFirstName": "John",
                "customerLastName": "Smith",
                "numberOfLines": "1",
                "lines": [],
                "autopayDiscountAmount": "30.00",
                "eligibleForAutopay": "true",
                "customerRole": "accountHolder",
                "greetByName": "John",
                "paymentInfo": {"enrolledInAutopay": False}
            }
        }
        utils.set_customer_profile(profile_data)
        
        # Set the AUTH_STATUS in the database to "ACCEPT" to match what the function expects
        db.DB["AUTH_STATUS"] = "ACCEPT"
        
        # Get authenticated profile
        profile_response = get_authenticated_customer_profile(authstatus="ACCEPT")
        
        # Enroll in offer
        enrollment_response = enroll_in_offer(
            accountNumber=profile_response["customerProfile"]["accountNumber"],
            offerId="LOYALTY123"
        )
        
        # Verify enrollment
        self.assertEqual(enrollment_response["status"], "success")
        
        # Verify enrollment was recorded in DB
        self.assertIsNotNone(db.DB.get("OFFER_ENROLLMENT"))
        self.assertEqual(db.DB["OFFER_ENROLLMENT"]["accountNumber"], "741852963")
        self.assertEqual(db.DB["OFFER_ENROLLMENT"]["offerId"], "LOYALTY123")

    def test_agent_transfer_flow(self):
        """
        Test the agent transfer flow for various scenarios.
        """
        
        # Test transfer for authentication issues
        transfer_response = transfer_to_live_agent(
            dispositionCode="AUTH_FAILED",
            callEndState="AGENT_TRANSFER",
            preferredLang="E"
        )
        self.assertEqual(transfer_response["status"], "success")
        
        # Test transfer for general agent request
        transfer_response = transfer_to_live_agent(
            dispositionCode="AGENT_TRANSFER",
            callEndState="AGENT_TRANSFER",
            preferredLang="E"
        )
        self.assertEqual(transfer_response["status"], "success")
        
        # Test escalate call
        escalate_response = escalate()
        self.assertEqual(escalate_response, "Escalated to live agent.")

    def test_call_termination_flow(self):
        """
        Test the call termination flow for various scenarios.
        """
        
        # Test disconnect for successful completion
        disconnect_response = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT"
        )
        self.assertEqual(disconnect_response["status"], "success")
        
        # Test disconnect for declined offer
        disconnect_response = record_call_outcome_and_disconnect(
            callEndState="DISCONNECT",
            dispositionCode="PROMO_DECLINED"
        )
        self.assertEqual(disconnect_response["status"], "success")
        
        # Test done call
        done_response = done()
        self.assertEqual(done_response, "")


if __name__ == "__main__":
    unittest.main()
