import unittest

# Absolute imports for the new folder structure
from ... import (
    get_pre_authentication_call_data,
    manage_customer_authentication,
    transfer_to_live_agent,
    escalate,
)
from ces_loyalty_auth.SimulationEngine import db, utils
from ces_loyalty_auth.tests.loyalty_auth_base_exception import LoyaltyAuthBaseTestCase


class TestSpreadsheetScenario89(LoyaltyAuthBaseTestCase):
    """
    Test case that replicates the conversation flow from spreadsheet
    CES_outbound_loyalty_0.3_conversation_89.
    """

    def setUp(self):
        """Set up the test data matching the spreadsheet scenario."""
        super().setUp()
        
        # Reset the DB to a clean state
        db.reset_db()
        
        # Set up the pre-authentication data for John Smith
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
                    "preferredFirstName": "John",
                    "firstName": "John",
                    "customerName": "John Smith",
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
                                    "laptop": False
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
        This follows the exact steps from CES_outbound_loyalty_0.3_conversation_89.
        """
        
        # Step 1: Initial call - get pre-authentication data. Corresponds to turn 1 in the spreadsheet.
        preauth_response = get_pre_authentication_call_data()
        
        # Verify the response structure and data
        self.assertEqual(preauth_response["sessionInfo"]["parameters"]["customerName"], "John Smith")
        self.assertEqual(preauth_response["sessionInfo"]["parameters"]["status"], "SUCCESS")
        self.assertTrue(preauth_response["sessionInfo"]["parameters"]["hasMtnLoyaltyOffers"])
        
        # Verify loyalty offers are present
        loyalty_offers = preauth_response["sessionInfo"]["parameters"]["loyaltyOffers"]
        self.assertEqual(len(loyalty_offers), 1)
        self.assertEqual(loyalty_offers[0]["OfferID"], "LOYALTY123")
        self.assertEqual(loyalty_offers[0]["OfferDesc"], "Save $10 per month for the next 12 months")

        # Turns 2-6: The user confirms their identity, agrees to the offer, and confirms they are ready to authenticate.
        # This leads the agent to initiate the authentication process.
        
        # Step 7: Authentication initiation (turn 7 in spreadsheet)
        # Set up the mock response for when the agent initiates authentication.
        auth_init_data = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_INIT",
                    "statusCode": "0",
                    "statusMessage": "Authentication initiated",
                    "sessionMap": None,
                    "error": None,
                    "noService": None,
                    "sessionId": "1234567890",
                    "authmode": None,
                    "gotoPage": None
                }
            }
        }
        utils.set_auth_result(auth_init_data)
        
        # Agent calls manage_customer_authentication with AUTHENTICATION_INIT
        auth_init_response = manage_customer_authentication(authstate="AUTHENTICATION_INIT")
        
        # Verify authentication initiation response
        self.assertEqual(auth_init_response["sessionInfo"]["parameters"]["authstate"], "AUTHENTICATION_INIT")
        self.assertEqual(auth_init_response["sessionInfo"]["parameters"]["statusMessage"], "Authentication SMS sent successfully")

        # Step 8: User says they did not receive the text message.
        # This triggers the agent to transfer the call.

        # Step 9: Agent transfer (turn 9 in spreadsheet)
        # Assistant calls transfer_to_live_agent
        transfer_response = transfer_to_live_agent(
            dispositionCode="NOTIFICATION_NOT_RECEIVED",
            callEndState="AGENT_TRANSFER",
            preferredLang="E"
        )
        
        # Verify transfer response
        self.assertEqual(transfer_response["status"], "success")
        
        # Step 10: Escalate call (turn 9 in spreadsheet)
        # Assistant calls escalate as per the "Call Termination Protocol" directive
        escalate_response = escalate()
        
        # Verify escalate response
        self.assertEqual(escalate_response, "Escalated to live agent.")

if __name__ == "__main__":
    unittest.main()