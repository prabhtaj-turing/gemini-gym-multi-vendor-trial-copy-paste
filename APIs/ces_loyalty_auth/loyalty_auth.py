"""Tools for outbound loyalty."""
from common_utils.tool_spec_decorator import tool_spec, ErrorObject
from typing import Optional, Dict, Any
from pydantic import ValidationError
import uuid
from .SimulationEngine import utils
from .SimulationEngine.db import DB
from .SimulationEngine.custom_errors import AuthenticationFailedError, InvalidRequestError
from .SimulationEngine.models import (
    # Enums
    CallEndState,
    DispositionCode,
    # Input Models
    GetAuthenticatedCustomerProfileInput,
    ManageCustomerAuthenticationInput,
    GetPreAuthenticationCallDataInput,
    RecordCallOutcomeAndDisconnectInput,
    TransferToLiveAgentInput,
    EnrollInOfferInput,
    DoneInput,
    FailInput,
    CancelInput,
    EscalateInput,
    # Output Models
    StatusOutput,
    StringOutput,
    FailOutput,
    CancelOutput,
    GetAuthenticatedCustomerProfileResponse,
    ManageCustomerAuthenticationResponse,
    GetPreAuthenticationCallDataResponse,
)

DETERMINISTIC_SESSION_NAMESPACE_FOR_COLLAB = uuid.uuid5(
    uuid.NAMESPACE_DNS, 
    "ces.loyalty.auth.deterministic.session.collab"
)

# --- API Tools ---
@tool_spec(
    input_model=GetAuthenticatedCustomerProfileInput,
    output_model=GetAuthenticatedCustomerProfileResponse,
    description="Retrieves the customer's profile after successful authentication.",
    error_model=[
        ErrorObject(AuthenticationFailedError, ["Raised if authentication status is not 'ACCEPT' or customer is not authenticated."]),
        ErrorObject(ValidationError, ['Raised if the customer profile data fails validation.'])
    ],
    spec={
        'name': 'get_authenticated_customer_profile',
        'description': "Retrieves the customer's profile after successful authentication.",
        'parameters': {
            'type': 'object',
            'properties': {
                'authstatus': {
                    'type': 'string',
                    'description': """ The current authentication status (e.g., 'ACCEPT'). 
                    Defaults to 'EMPTY' if not provided. """
                }
            },
            'required': []
        },
        'response': {
            'type': 'object',
            'description': 'An object containing the detailed customer profile.',
            'properties': {
                'customerProfile': {
                    'type': 'object',
                    'description': "A dictionary containing the customer's profile information with the following keys:",
                    'properties': {
                        'customerName': {
                            'type': 'string',
                            'description': "The customer's full name."
                        },
                        'numberOfLines': {
                            'type': 'string',
                            'description': 'The number of lines on the account.'
                        },
                        'accountNumber': {
                            'type': 'string',
                            'description': 'The customer\'s account number in format "XXXXXXXXXXX-XXXXX" (11 digits, dash, 5 digits).'
                        },
                        'lines': {
                            'type': 'array',
                            'description': 'A list of dictionaries, each representing a line with the following structure:',
                            'items': {
                                'type': 'object',
                                'properties': {
                                    'mtn': {
                                        'type': 'string',
                                        'description': 'Mobile telephone number for the line.'
                                    },
                                    'mtnStatus': {
                                        'type': 'object',
                                        'description': 'Status information for the mobile telephone number:',
                                        'properties': {
                                            'isActive': {
                                                'type': 'boolean',
                                                'description': 'Whether the line is currently active.',
                                                'nullable': True
                                            },
                                            'isSuspendedWithBilling': {
                                                'type': 'boolean',
                                                'description': 'Whether the line is suspended with billing.',
                                                'nullable': True
                                            },
                                            'isSuspendedWithoutBilling': {
                                                'type': 'boolean',
                                                'description': 'Whether the line is suspended without billing.',
                                                'nullable': True
                                            },
                                            'voluntarySuspended': {
                                                'type': 'boolean',
                                                'description': 'Whether the line is voluntarily suspended.',
                                                'nullable': True
                                            },
                                            'involuntarySuspended': {
                                                'type': 'boolean',
                                                'description': 'Whether the line is involuntarily suspended.',
                                                'nullable': True
                                            },
                                            'involuntarySuspendedWithNonPayment': {
                                                'type': 'boolean',
                                                'description': 'Whether suspended due to non-payment.',
                                                'nullable': True
                                            },
                                            'mtnStatusReasonCode': {
                                                'type': 'string',
                                                'description': 'Reason code for the current status.',
                                                'nullable': True
                                            }
                                        },
                                        'required': []
                                    },
                                    'pricePlanInfo': {
                                        'type': 'object',
                                        'description': 'Information about the pricing plan:',
                                        'properties': {
                                            'planId': {
                                                'type': 'string',
                                                'description': 'Unique identifier for the plan.'
                                            },
                                            'effectiveDate': {
                                                'type': 'string',
                                                'description': 'Date when the plan became effective.'
                                            },
                                            'planDisplayName': {
                                                'type': 'string',
                                                'description': 'Display name of the plan.'
                                            },
                                            'planCategoryName': {
                                                'type': 'string',
                                                'description': 'Category name of the plan.',
                                                'nullable': True
                                            },
                                            'description': {
                                                'type': 'string',
                                                'description': 'Description of the plan.',
                                                'nullable': True
                                            },
                                            'planSkuName': {
                                                'type': 'string',
                                                'description': 'SKU name of the plan.',
                                                'nullable': True
                                            },
                                            'accessCharge': {
                                                'type': 'object',
                                                'description': 'Access charge information:',
                                                'properties': {
                                                    'monthlyAccessCharge': {
                                                        'type': 'string',
                                                        'description': 'Monthly access charge amount.',
                                                        'nullable': True
                                                    },
                                                    'discountedCharge': {
                                                        'type': 'string',
                                                        'description': 'Discounted charge amount.',
                                                        'nullable': True
                                                    },
                                                    'finalPriceWithLAC': {
                                                        'type': 'string',
                                                        'description': 'Final price with line access charge.',
                                                        'nullable': True
                                                    },
                                                    'finalPriceWithLACAndDiscount': {
                                                        'type': 'string',
                                                        'description': 'Final price with LAC and discount.',
                                                        'nullable': True
                                                    },
                                                    'discountedAccessChargeWithPerk': {
                                                        'type': 'string',
                                                        'description': 'Discounted access charge with perk.',
                                                        'nullable': True
                                                    }
                                                },
                                                'required': [],
                                                'nullable': True
                                            }
                                        },
                                        'required': [
                                            'planId',
                                            'effectiveDate',
                                            'planDisplayName'
                                        ],
                                        'nullable': True
                                    },
                                    'subscriptions': {
                                        'type': 'array',
                                        'description': 'List of subscription services:',
                                        'items': {
                                            'type': 'object',
                                            'properties': {
                                                'spoId': {
                                                    'type': 'string',
                                                    'description': 'Service plan option ID.',
                                                    'nullable': True
                                                },
                                                'description': {
                                                    'type': 'string',
                                                    'description': 'Description of the subscription.',
                                                    'nullable': True
                                                },
                                                'skuName': {
                                                    'type': 'string',
                                                    'description': 'SKU name of the subscription.',
                                                    'nullable': True
                                                },
                                                'price': {
                                                    'type': 'string',
                                                    'description': 'Price of the subscription.',
                                                    'nullable': True
                                                },
                                                'enrolled': {
                                                    'type': 'boolean',
                                                    'description': 'Whether the customer is enrolled.',
                                                    'nullable': True
                                                },
                                                'onPromo': {
                                                    'type': 'boolean',
                                                    'description': 'Whether the subscription is on promotion.',
                                                    'nullable': True
                                                },
                                                'promoRedeemed': {
                                                    'type': 'boolean',
                                                    'description': 'Whether the promotion has been redeemed.',
                                                    'nullable': True
                                                },
                                                'onEligiblePlanAndDevice': {
                                                    'type': 'boolean',
                                                    'description': 'Whether eligible for plan and device.',
                                                    'nullable': True
                                                },
                                                'displayName': {
                                                    'type': 'string',
                                                    'description': 'Display name of the subscription.',
                                                    'nullable': True
                                                },
                                                'registrationStatus': {
                                                    'type': 'string',
                                                    'description': 'Registration status of the subscription.',
                                                    'nullable': True
                                                },
                                                'status': {
                                                    'type': 'string',
                                                    'description': 'Current status of the subscription.',
                                                    'nullable': True
                                                },
                                                'entitlementStatus': {
                                                    'type': 'string',
                                                    'description': 'Entitlement status of the subscription.',
                                                    'nullable': True
                                                },
                                                'subscriptionId': {
                                                    'type': 'string',
                                                    'description': 'Unique identifier for the subscription.',
                                                    'nullable': True
                                                },
                                                'service': {
                                                    'type': 'string',
                                                    'description': 'Service type of the subscription.',
                                                    'nullable': True
                                                },
                                                'isPerk': {
                                                    'type': 'boolean',
                                                    'description': 'Whether this is a perk subscription.',
                                                    'nullable': True
                                                }
                                            },
                                            'required': []
                                        },
                                        'nullable': True
                                    },
                                    'equipmentInfos': {
                                        'type': 'object',
                                        'description': 'Equipment information for the line:',
                                        'properties': {
                                            'deviceInfo': {
                                                'type': 'object',
                                                'description': 'Device information:',
                                                'properties': {
                                                    'displayName': {
                                                        'type': 'string',
                                                        'description': 'Display name of the device.',
                                                        'nullable': True
                                                    },
                                                    'deviceUrl': {
                                                        'type': 'string',
                                                        'description': 'URL to device image.',
                                                        'nullable': True
                                                    },
                                                    'category': {
                                                        'type': 'object',
                                                        'description': 'Device category information:',
                                                        'properties': {
                                                            'smartphone': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a smartphone.",
                                                                'nullable': True
                                                            },
                                                            'basicphone': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a basic phone.",
                                                                'nullable': True
                                                            },
                                                            'tablet': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a tablet.",
                                                                'nullable': True
                                                            },
                                                            'smartwatch': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a smartwatch.",
                                                                'nullable': True
                                                            },
                                                            'homePC': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a home PC.",
                                                                'nullable': True
                                                            },
                                                            'telematics': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a telematics device.",
                                                                'nullable': True
                                                            },
                                                            'WSOnly': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a WS-only device.",
                                                                'nullable': True
                                                            },
                                                            'virtualDevice': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a virtual device.",
                                                                'nullable': True
                                                            },
                                                            'connectedDevice': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a connected device.",
                                                                'nullable': True
                                                            },
                                                            'internetDevice': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's an internet device.",
                                                                'nullable': True
                                                            },
                                                            'homeSolutions': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a home solutions device.",
                                                                'nullable': True
                                                            },
                                                            'laptop': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a laptop.",
                                                                'nullable': True
                                                            }
                                                        },
                                                        'required': [],
                                                        'nullable': True
                                                    },
                                                    'deviceType': {
                                                        'type': 'object',
                                                        'description': 'Device type information:',
                                                        'properties': {
                                                            'device3G': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a 3G device.",
                                                                'nullable': True
                                                            },
                                                            'device4G': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a 4G device.",
                                                                'nullable': True
                                                            },
                                                            'device5GE': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a 5G device.",
                                                                'nullable': True
                                                            },
                                                            'device5GA': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a 5G Advanced device.",
                                                                'nullable': True
                                                            },
                                                            'backupRouter4G': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a backup 4G router.",
                                                                'nullable': True
                                                            },
                                                            'homeFusionDevice': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a home fusion device.",
                                                                'nullable': True
                                                            },
                                                            'autoAttendant': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's an auto attendant.",
                                                                'nullable': True
                                                            },
                                                            'huntGroup': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a hunt group device.",
                                                                'nullable': True
                                                            },
                                                            'overTheTop': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's an over-the-top device.",
                                                                'nullable': True
                                                            },
                                                            'deskphone': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a desk phone.",
                                                                'nullable': True
                                                            },
                                                            'device4GO': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a 4G-only device.",
                                                                'nullable': True
                                                            },
                                                            'antenna5G': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a 5G antenna.",
                                                                'nullable': True
                                                            },
                                                            'home5G': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a home 5G device.",
                                                                'nullable': True
                                                            },
                                                            'jetPack4G': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a 4G jetpack.",
                                                                'nullable': True
                                                            },
                                                            'jetPack5G': {
                                                                'type': 'boolean',
                                                                'description': "Whether it's a 5G jetpack.",
                                                                'nullable': True
                                                            },
                                                            'description': {
                                                                'type': 'string',
                                                                'description': 'Description of the device type.',
                                                                'nullable': True
                                                            }
                                                        },
                                                        'required': [],
                                                        'nullable': True
                                                    }
                                                },
                                                'required': [],
                                                'nullable': True
                                            }
                                        },
                                        'required': []
                                    },
                                    'mobileInfoAttributes': {
                                        'type': 'object',
                                        'description': 'Mobile information attributes:',
                                        'properties': {
                                            'accessRoles': {
                                                'type': 'object',
                                                'description': 'Access roles for the line:',
                                                'properties': {
                                                    'owner': {
                                                        'type': 'boolean',
                                                        'description': 'Whether the user is the owner.'
                                                    },
                                                    'manager': {
                                                        'type': 'boolean',
                                                        'description': 'Whether the user is a manager.'
                                                    },
                                                    'member': {
                                                        'type': 'boolean',
                                                        'description': 'Whether the user is a member.'
                                                    }
                                                },
                                                'required': [
                                                    'owner',
                                                    'manager',
                                                    'member'
                                                ]
                                            }
                                        },
                                        'required': [
                                            'accessRoles'
                                        ],
                                        'nullable': True
                                    },
                                    'equipmentUpgradeEligibility': {
                                        'type': 'object',
                                        'description': 'Equipment upgrade eligibility:',
                                        'properties': {
                                            'upgradeEligible': {
                                                'type': 'string',
                                                'description': 'Whether upgrade is eligible.',
                                                'nullable': True
                                            },
                                            'buyoutRestricted': {
                                                'type': 'string',
                                                'description': 'Whether buyout is restricted.',
                                                'nullable': True
                                            },
                                            'upgradeEligibilityDate': {
                                                'type': 'string',
                                                'description': 'Date when upgrade becomes eligible.',
                                                'nullable': True
                                            },
                                            'earlyUpgradeEligible': {
                                                'type': 'string',
                                                'description': 'Whether early upgrade is eligible.',
                                                'nullable': True
                                            },
                                            'alwaysUpgradeEligible': {
                                                'type': 'string',
                                                'description': 'Whether always upgrade eligible.',
                                                'nullable': True
                                            },
                                            'buyoutEligible': {
                                                'type': 'string',
                                                'description': 'Whether buyout is eligible.',
                                                'nullable': True
                                            }
                                        },
                                        'required': [],
                                        'nullable': True
                                    },
                                    'autoPayEligible': {
                                        'type': 'boolean',
                                        'description': 'Whether the line is eligible for autopay.',
                                        'nullable': True
                                    },
                                    'autoPayReflected': {
                                        'type': 'boolean',
                                        'description': 'Whether autopay is reflected.',
                                        'nullable': True
                                    },
                                    'autoPayDiscount': {
                                        'type': 'string',
                                        'description': 'Autopay discount amount.',
                                        'nullable': True
                                    },
                                    'enrolledForLoyalty': {
                                        'type': 'boolean',
                                        'description': 'Whether enrolled for loyalty program.',
                                        'nullable': True
                                    }
                                },
                                'required': [
                                    'mtn',
                                    'mtnStatus',
                                    'equipmentInfos'
                                ]
                            }
                        },
                        'customerRole': {
                            'type': 'string',
                            'description': "The customer's role on the account.",
                            'nullable': True
                        },
                        'greetByName': {
                            'type': 'string',
                            'description': 'The name to greet the customer with.',
                            'nullable': True
                        },
                        'customerFirstName': {
                            'type': 'string',
                            'description': "The customer's first name.",
                            'nullable': True
                        },
                        'customerLastName': {
                            'type': 'string',
                            'description': "The customer's last name.",
                            'nullable': True
                        },
                        'paymentInfo': {
                            'type': 'object',
                            'description': 'A dictionary with payment information:',
                            'properties': {
                                'enrolledInAutopay': {
                                    'type': 'boolean',
                                    'description': 'Whether enrolled in autopay.'
                                },
                                'invoiceDate': {
                                    'type': 'string',
                                    'description': 'Date of the invoice.',
                                    'nullable': True
                                },
                                'lastPaymentDate': {
                                    'type': 'string',
                                    'description': 'Date of the last payment.',
                                    'nullable': True
                                },
                                'paymentDueDate': {
                                    'type': 'string',
                                    'description': 'Date when payment is due.',
                                    'nullable': True
                                },
                                'pastDueDays': {
                                    'type': 'string',
                                    'description': 'Number of days past due.',
                                    'nullable': True
                                },
                                'enrolledInPaperFree': {
                                    'type': 'boolean',
                                    'description': 'Whether enrolled in paper-free billing.',
                                    'nullable': True
                                },
                                'lastPaymentAmount': {
                                    'type': 'string',
                                    'description': 'Amount of the last payment.',
                                    'nullable': True
                                },
                                'eligibleForPaperFree': {
                                    'type': 'boolean',
                                    'description': 'Whether eligible for paper-free billing.',
                                    'nullable': True
                                },
                                'currentCharges': {
                                    'type': 'string',
                                    'description': 'Current charges amount.',
                                    'nullable': True
                                },
                                'arPastDueBalance': {
                                    'type': 'string',
                                    'description': 'Accounts receivable past due balance.',
                                    'nullable': True
                                },
                                'pastDueBalance': {
                                    'type': 'string',
                                    'description': 'Past due balance amount.',
                                    'nullable': True
                                },
                                'outstandingBalance': {
                                    'type': 'string',
                                    'description': 'Outstanding balance amount.',
                                    'nullable': True
                                },
                                'paymentHistory': {
                                    'type': 'array',
                                    'description': 'List of payment history entries:',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'totalBalance': {
                                                'type': 'string',
                                                'description': 'Total balance for the period.',
                                                'nullable': True
                                            },
                                            'adjustedPreviousAmount': {
                                                'type': 'string',
                                                'description': 'Adjusted previous amount.',
                                                'nullable': True
                                            },
                                            'amountPaid': {
                                                'type': 'string',
                                                'description': 'Amount paid for the period.',
                                                'nullable': True
                                            },
                                            'billCycleStartDate': {
                                                'type': 'string',
                                                'description': 'Start date of the bill cycle.',
                                                'nullable': True
                                            },
                                            'invoiceDate': {
                                                'type': 'string',
                                                'description': 'Date of the invoice.',
                                                'nullable': True
                                            },
                                            'billCycleEndDate': {
                                                'type': 'string',
                                                'description': 'End date of the bill cycle.',
                                                'nullable': True
                                            }
                                        },
                                        'required': []
                                    },
                                    'nullable': True
                                }
                            },
                            'required': [
                                'enrolledInAutopay'
                            ],
                            'nullable': True
                        }
                    },
                    'required': [
                        'customerName',
                        'numberOfLines',
                        'accountNumber',
                        'lines'
                    ]
                }
            },
            'required': [
                'customerProfile'
            ]
        }
    }
)
def get_authenticated_customer_profile(
    authstatus: str = 'EMPTY',
) -> Dict[str, Any]:
    """Retrieves the customer's profile after successful authentication.

    Args:
      authstatus (Optional[str]): The current authentication status (e.g., 'ACCEPT'). 
        Defaults to 'EMPTY' if not provided.

    Returns:
      Dict[str, Any]: An object containing the detailed customer profile.
        - customerProfile (Dict): A dictionary containing the customer's profile information with the following keys:
            - customerName (str): The customer's full name.
            - numberOfLines (str): The number of lines on the account.
            - accountNumber (str): The customer's account number in format "XXXXXXXXXXX-XXXXX" (11 digits, dash, 5 digits).
            - lines (List[Dict]): A list of dictionaries, each representing a line with the following structure:
                - mtn (str): Mobile telephone number for the line.
                - mtnStatus (Dict): Status information for the mobile telephone number:
                    - isActive (Optional[bool]): Whether the line is currently active.
                    - isSuspendedWithBilling (Optional[bool]): Whether the line is suspended with billing.
                    - isSuspendedWithoutBilling (Optional[bool]): Whether the line is suspended without billing.
                    - voluntarySuspended (Optional[bool]): Whether the line is voluntarily suspended.
                    - involuntarySuspended (Optional[bool]): Whether the line is involuntarily suspended.
                    - involuntarySuspendedWithNonPayment (Optional[bool]): Whether suspended due to non-payment.
                    - mtnStatusReasonCode (Optional[str]): Reason code for the current status.
                - pricePlanInfo (Optional[Dict]): Information about the pricing plan:
                    - planId (str): Unique identifier for the plan.
                    - effectiveDate (str): Date when the plan became effective.
                    - planDisplayName (str): Display name of the plan.
                    - planCategoryName (Optional[str]): Category name of the plan.
                    - description (Optional[str]): Description of the plan.
                    - planSkuName (Optional[str]): SKU name of the plan.
                    - accessCharge (Optional[Dict]): Access charge information:
                        - monthlyAccessCharge (Optional[str]): Monthly access charge amount.
                        - discountedCharge (Optional[str]): Discounted charge amount.
                        - finalPriceWithLAC (Optional[str]): Final price with line access charge.
                        - finalPriceWithLACAndDiscount (Optional[str]): Final price with LAC and discount.
                        - discountedAccessChargeWithPerk (Optional[str]): Discounted access charge with perk.
                - subscriptions (Optional[List[Dict]]): List of subscription services:
                    - spoId (Optional[str]): Service plan option ID.
                    - description (Optional[str]): Description of the subscription.
                    - skuName (Optional[str]): SKU name of the subscription.
                    - price (Optional[str]): Price of the subscription.
                    - enrolled (Optional[bool]): Whether the customer is enrolled.
                    - onPromo (Optional[bool]): Whether the subscription is on promotion.
                    - promoRedeemed (Optional[bool]): Whether the promotion has been redeemed.
                    - onEligiblePlanAndDevice (Optional[bool]): Whether eligible for plan and device.
                    - displayName (Optional[str]): Display name of the subscription.
                    - registrationStatus (Optional[str]): Registration status of the subscription.
                    - status (Optional[str]): Current status of the subscription.
                    - entitlementStatus (Optional[str]): Entitlement status of the subscription.
                    - subscriptionId (Optional[str]): Unique identifier for the subscription.
                    - service (Optional[str]): Service type of the subscription.
                    - isPerk (Optional[bool]): Whether this is a perk subscription.
                - equipmentInfos (Dict): Equipment information for the line:
                    - deviceInfo (Optional[Dict]): Device information:
                        - displayName (Optional[str]): Display name of the device.
                        - deviceUrl (Optional[str]): URL to device image.
                        - category (Optional[Dict]): Device category information:
                            - smartphone (Optional[bool]): Whether it's a smartphone.
                            - basicphone (Optional[bool]): Whether it's a basic phone.
                            - tablet (Optional[bool]): Whether it's a tablet.
                            - smartwatch (Optional[bool]): Whether it's a smartwatch.
                            - homePC (Optional[bool]): Whether it's a home PC.
                            - telematics (Optional[bool]): Whether it's a telematics device.
                            - WSOnly (Optional[bool]): Whether it's a WS-only device.
                            - virtualDevice (Optional[bool]): Whether it's a virtual device.
                            - connectedDevice (Optional[bool]): Whether it's a connected device.
                            - internetDevice (Optional[bool]): Whether it's an internet device.
                            - homeSolutions (Optional[bool]): Whether it's a home solutions device.
                            - laptop (Optional[bool]): Whether it's a laptop.
                        - deviceType (Optional[Dict]): Device type information:
                            - device3G (Optional[bool]): Whether it's a 3G device.
                            - device4G (Optional[bool]): Whether it's a 4G device.
                            - device5GE (Optional[bool]): Whether it's a 5G device.
                            - device5GA (Optional[bool]): Whether it's a 5G Advanced device.
                            - backupRouter4G (Optional[bool]): Whether it's a backup 4G router.
                            - homeFusionDevice (Optional[bool]): Whether it's a home fusion device.
                            - autoAttendant (Optional[bool]): Whether it's an auto attendant.
                            - huntGroup (Optional[bool]): Whether it's a hunt group device.
                            - overTheTop (Optional[bool]): Whether it's an over-the-top device.
                            - deskphone (Optional[bool]): Whether it's a desk phone.
                            - device4GO (Optional[bool]): Whether it's a 4G-only device.
                            - antenna5G (Optional[bool]): Whether it's a 5G antenna.
                            - home5G (Optional[bool]): Whether it's a home 5G device.
                            - jetPack4G (Optional[bool]): Whether it's a 4G jetpack.
                            - jetPack5G (Optional[bool]): Whether it's a 5G jetpack.
                            - description (Optional[str]): Description of the device type.
                - mobileInfoAttributes (Optional[Dict]): Mobile information attributes:
                    - accessRoles (Dict): Access roles for the line:
                        - owner (bool): Whether the user is the owner.
                        - manager (bool): Whether the user is a manager.
                        - member (bool): Whether the user is a member.
                - equipmentUpgradeEligibility (Optional[Dict]): Equipment upgrade eligibility:
                    - upgradeEligible (Optional[str]): Whether upgrade is eligible.
                    - buyoutRestricted (Optional[str]): Whether buyout is restricted.
                    - upgradeEligibilityDate (Optional[str]): Date when upgrade becomes eligible.
                    - earlyUpgradeEligible (Optional[str]): Whether early upgrade is eligible.
                    - alwaysUpgradeEligible (Optional[str]): Whether always upgrade eligible.
                    - buyoutEligible (Optional[str]): Whether buyout is eligible.
                - autoPayEligible (Optional[bool]): Whether the line is eligible for autopay.
                - autoPayReflected (Optional[bool]): Whether autopay is reflected.
                - autoPayDiscount (Optional[str]): Autopay discount amount.
                - enrolledForLoyalty (Optional[bool]): Whether enrolled for loyalty program.
            - customerRole (Optional[str]): The customer's role on the account.
            - greetByName (Optional[str]): The name to greet the customer with.
            - customerFirstName (Optional[str]): The customer's first name.
            - customerLastName (Optional[str]): The customer's last name.
            - paymentInfo (Optional[Dict]): A dictionary with payment information:
                - enrolledInAutopay (bool): Whether enrolled in autopay.
                - invoiceDate (Optional[str]): Date of the invoice.
                - lastPaymentDate (Optional[str]): Date of the last payment.
                - paymentDueDate (Optional[str]): Date when payment is due.
                - pastDueDays (Optional[str]): Number of days past due.
                - enrolledInPaperFree (Optional[bool]): Whether enrolled in paper-free billing.
                - lastPaymentAmount (Optional[str]): Amount of the last payment.
                - eligibleForPaperFree (Optional[bool]): Whether eligible for paper-free billing.
                - currentCharges (Optional[str]): Current charges amount.
                - arPastDueBalance (Optional[str]): Accounts receivable past due balance.
                - pastDueBalance (Optional[str]): Past due balance amount.
                - outstandingBalance (Optional[str]): Outstanding balance amount.
                - paymentHistory (Optional[List[Dict]]): List of payment history entries:
                    - totalBalance (Optional[str]): Total balance for the period.
                    - adjustedPreviousAmount (Optional[str]): Adjusted previous amount.
                    - amountPaid (Optional[str]): Amount paid for the period.
                    - billCycleStartDate (Optional[str]): Start date of the bill cycle.
                    - invoiceDate (Optional[str]): Date of the invoice.
                    - billCycleEndDate (Optional[str]): End date of the bill cycle.

    Raises:
        AuthenticationFailedError: If authentication status is not 'ACCEPT' or customer is not authenticated.
        ValidationError: If the customer profile data fails validation.
    """
    if authstatus != "ACCEPT":
        raise AuthenticationFailedError("Authentication not successful")
    # NOTE: This works only because this tool is always called in the same turn as
    # `manage_customer_authentication`. In prod, the DB change would be done in
    # user interaction.
    if DB.get("AUTH_STATUS") == "ACCEPT":
        profile = DB.get("PROFILE_AFTER_AUTH", {})
        return profile
    else:
        raise AuthenticationFailedError("Customer is not authenticated.")


@tool_spec(
    input_model=ManageCustomerAuthenticationInput,
    output_model=ManageCustomerAuthenticationResponse,
    description="""Manages the customer authentication state.
        
Used to initiate or update the authentication process.""",
    error_model=[
        ErrorObject(AuthenticationFailedError, ['Raised if authentication result not found in database.']),
        ErrorObject(ValidationError, ['Raised if the authentication response data fails validation.'])
    ],
    spec={
        'name': 'manage_customer_authentication',
        'description': """ Manages the customer authentication state.
        
        Used to initiate or update the authentication process. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'authstate': {
                    'type': 'string',
                    'description': "The desired authentication state (e.g., 'AUTHENTICATION_INIT', 'AUTHENTICATION_STATUS')."
                }
            },
            'required': [
                'authstate'
            ]
        },
        'response': {
            'type': 'object',
            'description': 'An object containing the result of the authentication action.',
            'properties': {
                'sessionInfo': {
                    'type': 'object',
                    'description': 'A dictionary containing session information with the following key:',
                    'properties': {
                        'parameters': {
                            'type': 'object',
                            'description': 'A dictionary containing authentication parameters with keys:',
                            'properties': {
                                'authstate': {
                                    'type': 'string',
                                    'description': 'The current authentication state.'
                                },
                                'sessionId': {
                                    'type': 'string',
                                    'description': 'The session ID.'
                                },
                                'statusMessage': {
                                    'type': 'string',
                                    'description': 'A message describing the status.'
                                },
                                'gotoPage': {
                                    'type': 'string',
                                    'description': 'The page to redirect to.',
                                    'nullable': True
                                },
                                'error': {
                                    'type': 'string',
                                    'description': 'Error message, if any.',
                                    'nullable': True
                                },
                                'statusCode': {
                                    'type': 'string',
                                    'description': 'The status code.',
                                    'nullable': True
                                },
                                'sessionMap': {
                                    'type': 'object',
                                    'description': 'Session data containing adaptive authentication information.',
                                    'properties': {
                                        'adaptiveAuthentication': {
                                            'type': 'string',
                                            'description': 'A JSON string containing adaptive authentication data with the following structure: {"authstatus": "ACCEPT|PENDING|REJECT", "reason": "optional reason string"}',
                                            'nullable': True
                                        }
                                    },
                                    'required': [],
                                    'nullable': True
                                },
                                'noService': {
                                    'type': 'string',
                                    'description': 'Indicates if there is no service.',
                                    'nullable': True
                                },
                                'authmode': {
                                    'type': 'string',
                                    'description': 'The authentication mode used.',
                                    'nullable': True
                                }
                            },
                            'required': [
                                'authstate',
                                'sessionId',
                                'statusMessage'
                            ]
                        }
                    },
                    'required': [
                        'parameters'
                    ]
                }
            },
            'required': [
                'sessionInfo'
            ]
        }
    }
)
def manage_customer_authentication(
    authstate: str,
) -> Dict[str, Any]:
    """Manages the customer authentication state.

    Used to initiate or update the authentication process.

    Args:
      authstate (str): The desired authentication state (e.g., 'AUTHENTICATION_INIT', 'AUTHENTICATION_STATUS'). 


    Returns:
      Dict[str, Any]: An object containing the result of the authentication action.
        - sessionInfo (Dict): A dictionary containing session information with the following key:
            - parameters (Dict): A dictionary containing authentication parameters with keys:
                - authstate (str): The current authentication state.
                - sessionId (str): The session ID.
                - statusMessage (str): A message describing the status.
                - gotoPage (Optional[str]): The page to redirect to.
                - error (Optional[str]): Error message, if any.
                - statusCode (Optional[str]): The status code.
                - sessionMap (Optional[Dict[str, str]]): Session data containing adaptive authentication information.
                    - adaptiveAuthentication (Optional[str]): A JSON string containing adaptive authentication data with the following structure: {"authstatus": "ACCEPT|PENDING|REJECT", "reason": "optional reason string"}.
                - noService (Optional[str]): Indicates if there is no service.
                - authmode (Optional[str]): The authentication mode used.

    Raises:
        AuthenticationFailedError: If authentication result not found in database.
        ValidationError: If the authentication response data fails validation.
    """
    # Handle different authentication states
    if authstate == "AUTHENTICATION_INIT":
        # Initialize authentication process - send SMS link
        # According to DI: "Invoke manage_customer_authentication with authstate: 'AUTHENTICATION_INIT' to send the text link"
        # In simulation, we simulate sending the SMS and return a response indicating the SMS was sent
        customer_account_number = utils.get_customer_account_number_from_preauth()
        auth_init_response = {
            "sessionInfo": {
                "parameters": {
                    "authstate": "AUTHENTICATION_INIT",
                    "sessionId": str(uuid.uuid5(DETERMINISTIC_SESSION_NAMESPACE_FOR_COLLAB, customer_account_number)),
                    "statusMessage": "Authentication SMS sent successfully",
                    "statusCode": "200",
                    "sessionMap": {
                        "adaptiveAuthentication": '{"authstatus": "PENDING"}'
                    },
                    "error": None,
                    "noService": None,
                    "authmode": "TEXT",
                    "gotoPage": None
                }
            }
        }
        utils.set_auth_result(auth_init_response)
        utils.update_auth_status()
        return auth_init_response
    
    elif authstate == "AUTHENTICATION_STATUS":
        # Check current authentication status
        # According to DI: "invoke manage_customer_authentication with authstate: 'AUTHENTICATION_STATUS' to re-check status"
        # We require the client to seed the DB with `set_auth_result` during setup to
        # simulate user interaction.
        utils.update_auth_status()
        auth_result = DB.get("AUTH_RESULT")

        # Check if auth_result exists and is not None
        if auth_result is None:
            raise AuthenticationFailedError("Authentication result not found in database. Please initialize authentication first.")
        
        return auth_result
    
    else:
        # Handle unknown authstate
        raise AuthenticationFailedError(f"Unknown authentication state: {authstate}")


@tool_spec(
    input_model=GetPreAuthenticationCallDataInput,
    output_model=GetPreAuthenticationCallDataResponse,
    description="""Retrieves pre-authentication data for the call session.
        
This includes information like customer name, account number, loyalty offers,
and plan perks.""",
    error_model=[
        ErrorObject(AuthenticationFailedError, ['Raised if pre-authentication data not found in database.']),
        ErrorObject(ValidationError, ['Raised if the pre-authentication data fails validation.']),
        ErrorObject(ValueError, ['Raised if the pre-authentication data is missing required keys.'])
    ],
    spec={
        'name': 'get_pre_authentication_call_data',
        'description': """ Retrieves pre-authentication data for the call session.
        
        This includes information like customer name, account number, loyalty offers,
        and plan perks. """,
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        },
        'response': {
            'type': 'object',
            'description': 'An object containing the pre-authentication call data.',
            'properties': {
                'sessionInfo': {
                    'type': 'object',
                    'description': 'A dictionary containing session information with the following key:',
                    'properties': {
                        'parameters': {
                            'type': 'object',
                            'description': 'A dictionary containing pre-authentication parameters with keys:',
                            'properties': {
                                'hasMtnLoyaltyOffers': {
                                    'type': 'boolean',
                                    'description': 'Whether the customer has loyalty offers.'
                                },
                                'availablePerks': {
                                    'type': 'array',
                                    'description': 'A list of dictionaries, each with a single key for the perk name.',
                                    'items': {
                                        'type': 'object',
                                        'properties': {},
                                        'required': []
                                    }
                                },
                                'accountNumber': {
                                    'type': 'string',
                                    'description': 'The customer\'s account number in format "XXXXXXXXXXX-XXXXX" (11 digits, dash, 5 digits).'
                                },
                                'autopayDiscountAmount': {
                                    'type': 'string',
                                    'description': 'The autopay discount amount.',
                                    'nullable': True
                                },
                                'status': {
                                    'type': 'string',
                                    'description': 'The status of the pre-authentication check.'
                                },
                                'statusCode': {
                                    'type': 'string',
                                    'description': 'The status code.'
                                },
                                'customerName': {
                                    'type': 'string',
                                    'description': "The customer's full name."
                                },
                                'customerFirstName': {
                                    'type': 'string',
                                    'description': "The customer's first name.",
                                    'nullable': True
                                },
                                'customerLastName': {
                                    'type': 'string',
                                    'description': "The customer's last name.",
                                    'nullable': True
                                },
                                'customerRole': {
                                    'type': 'string',
                                    'description': "The customer's role.",
                                    'nullable': True
                                },
                                'eligibleForAutopay': {
                                    'type': 'string',
                                    'description': "Whether the customer is eligible for autopay.",
                                    'nullable': True
                                },
                                'greetByName': {
                                    'type': 'string',
                                    'description': "The name to greet the customer by.",
                                    'nullable': True
                                },
                                'preferredFirstName': {
                                    'type': 'string',
                                    'description': "The customer's preferred first name."
                                },
                                'firstName': {
                                    'type': 'string',
                                    'description': "The customer's first name."
                                },
                                'statusMessage': {
                                    'type': 'string',
                                    'description': 'A message describing the status.'
                                },
                                'loyaltyOffersStatusCode': {
                                    'type': 'string',
                                    'description': 'Status code for loyalty offers.'
                                },
                                'loyaltyOffers': {
                                    'type': 'array',
                                    'description': 'A list of loyalty offer dictionaries with the following structure:',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'OfferDesc': {
                                                'type': 'string',
                                                'description': 'Description of the loyalty offer.'
                                            },
                                            'offerOrder': {
                                                'type': 'string',
                                                'description': 'Order/priority of the offer.'
                                            },
                                            'offerType': {
                                                'type': 'string',
                                                'description': 'Type of the offer (e.g., DISCOUNT, PERK).'
                                            },
                                            'OfferID': {
                                                'type': 'string',
                                                'description': 'Unique identifier for the offer.'
                                            }
                                        },
                                        'required': [
                                            'OfferDesc',
                                            'offerOrder',
                                            'offerType',
                                            'OfferID'
                                        ]
                                    }
                                },
                                'numberOfLines': {
                                    'type': 'string',
                                    'description': 'The number of lines on the account.',
                                    'nullable': True
                                },
                                'lines': {
                                    'type': 'array',
                                    'description': 'A list of line information.',
                                    'items': {
                                        'type': 'object',
                                        'properties': {
                                            'mtn': {
                                                'type': 'string',
                                                'description': 'Mobile Telephone Number'
                                            },
                                            'mtnStatus': {
                                                'type': 'object',
                                                'description': 'Status information for the mobile telephone number:',
                                                'properties': {
                                                    'isActive': {
                                                        'type': 'boolean',
                                                        'description': 'Whether the line is currently active.',
                                                        'nullable': True
                                                    },
                                                    'isSuspendedWithBilling': {
                                                        'type': 'boolean',
                                                        'description': 'Whether the line is suspended with billing.',
                                                        'nullable': True
                                                    },
                                                    'isSuspendedWithoutBilling': {
                                                        'type': 'boolean',
                                                        'description': 'Whether the line is suspended without billing.',
                                                        'nullable': True
                                                    },
                                                    'voluntarySuspended': {
                                                        'type': 'boolean',
                                                        'description': 'Whether the line is voluntarily suspended.',
                                                        'nullable': True
                                                    },
                                                    'involuntarySuspended': {
                                                        'type': 'boolean',
                                                        'description': 'Whether the line is involuntarily suspended.',
                                                        'nullable': True
                                                    },
                                                    'involuntarySuspendedWithNonPayment': {
                                                        'type': 'boolean',
                                                        'description': 'Whether suspended due to non-payment.',
                                                        'nullable': True
                                                    },
                                                    'mtnStatusReasonCode': {
                                                        'type': 'string',
                                                        'description': 'Reason code for the current status.',
                                                        'nullable': True
                                                    }
                                                },
                                                'required': []
                                            },
                                            'equipmentInfos': {
                                                'type': 'object',
                                                'description': 'Equipment information',
                                                'properties': {
                                                    'deviceInfo': {
                                                        'type': 'object',
                                                        'nullable': True,
                                                        'properties': {
                                                            'displayName': {
                                                                'type': 'string',
                                                                'nullable': True
                                                            },
                                                            'category': {
                                                                'type': 'object',
                                                                'description': 'Device category information:',
                                                                'properties': {
                                                                    'smartphone': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a smartphone.",
                                                                        'nullable': True
                                                                    },
                                                                    'basicphone': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a basic phone.",
                                                                        'nullable': True
                                                                    },
                                                                    'tablet': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a tablet.",
                                                                        'nullable': True
                                                                    },
                                                                    'smartwatch': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a smartwatch.",
                                                                        'nullable': True
                                                                    },
                                                                    'homePC': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a home PC.",
                                                                        'nullable': True
                                                                    },
                                                                    'telematics': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a telematics device.",
                                                                        'nullable': True
                                                                    },
                                                                    'WSOnly': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a WS-only device.",
                                                                        'nullable': True
                                                                    },
                                                                    'virtualDevice': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a virtual device.",
                                                                        'nullable': True
                                                                    },
                                                                    'connectedDevice': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a connected device.",
                                                                        'nullable': True
                                                                    },
                                                                    'internetDevice': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's an internet device.",
                                                                        'nullable': True
                                                                    },
                                                                    'homeSolutions': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a home solutions device.",
                                                                        'nullable': True
                                                                    },
                                                                    'laptop': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a laptop.",
                                                                        'nullable': True
                                                                    }
                                                                },
                                                                'required': [],
                                                                'nullable': True
                                                            },
                                                            'deviceUrl': {
                                                                'type': 'string',
                                                                'nullable': True
                                                            },
                                                            'deviceType': {
                                                                'type': 'object',
                                                                'description': 'Device type information:',
                                                                'properties': {
                                                                    'device3G': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a 3G device.",
                                                                        'nullable': True
                                                                    },
                                                                    'device4G': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a 4G device.",
                                                                        'nullable': True
                                                                    },
                                                                    'device5GE': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a 5G device.",
                                                                        'nullable': True
                                                                    },
                                                                    'device5GA': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a 5G Advanced device.",
                                                                        'nullable': True
                                                                    },
                                                                    'backupRouter4G': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a backup 4G router.",
                                                                        'nullable': True
                                                                    },
                                                                    'homeFusionDevice': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a home fusion device.",
                                                                        'nullable': True
                                                                    },
                                                                    'autoAttendant': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's an auto attendant.",
                                                                        'nullable': True
                                                                    },
                                                                    'huntGroup': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a hunt group device.",
                                                                        'nullable': True
                                                                    },
                                                                    'overTheTop': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's an over-the-top device.",
                                                                        'nullable': True
                                                                    },
                                                                    'deskphone': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a desk phone.",
                                                                        'nullable': True
                                                                    },
                                                                    'device4GO': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a 4G-only device.",
                                                                        'nullable': True
                                                                    },
                                                                    'antenna5G': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a 5G antenna.",
                                                                        'nullable': True
                                                                    },
                                                                    'home5G': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a home 5G device.",
                                                                        'nullable': True
                                                                    },
                                                                    'jetPack4G': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a 4G jetpack.",
                                                                        'nullable': True
                                                                    },
                                                                    'jetPack5G': {
                                                                        'type': 'boolean',
                                                                        'description': "Whether it's a 5G jetpack.",
                                                                        'nullable': True
                                                                    },
                                                                    'description': {
                                                                        'type': 'string',
                                                                        'description': 'Description of the device type.',
                                                                        'nullable': True
                                                                    }
                                                                },
                                                                'required': [],
                                                                'nullable': True
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            'autoPayReflected': {
                                                'type': 'boolean',
                                                'nullable': True
                                            },
                                            'pricePlanInfo': {
                                                'type': 'object',
                                                'nullable': True,
                                                'properties': {
                                                    'planId': {
                                                        'type': 'string'
                                                    },
                                                    'effectiveDate': {
                                                        'type': 'string'
                                                    },
                                                    'planDisplayName': {
                                                        'type': 'string'
                                                    },
                                                    'planCategoryName': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    },
                                                    'description': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    },
                                                    'planSkuName': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    },
                                                    'accessCharge': {
                                                        'type': 'object',
                                                        'nullable': True,
                                                        'properties': {
                                                            'monthlyAccessCharge': {
                                                                'type': 'string',
                                                                'nullable': True
                                                            },
                                                            'finalPriceWithLACAndDiscount': {
                                                                'type': 'string',
                                                                'nullable': True
                                                            },
                                                            'discountedCharge': {
                                                                'type': 'string',
                                                                'nullable': True
                                                            },
                                                            'finalPriceWithLAC': {
                                                                'type': 'string',
                                                                'nullable': True
                                                            },
                                                            'discountedAccessChargeWithPerk': {
                                                                'type': 'string',
                                                                'nullable': True
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            'mobileInfoAttributes': {
                                                'type': 'object',
                                                'nullable': True,
                                                'properties': {
                                                    'accessRoles': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'owner': {
                                                                'type': 'boolean'
                                                            },
                                                            'manager': {
                                                                'type': 'boolean'
                                                            },
                                                            'member': {
                                                                'type': 'boolean'
                                                            }
                                                        }
                                                    }
                                                }
                                            },
                                            'equipmentUpgradeEligibility': {
                                                'type': 'object',
                                                'nullable': True,
                                                'properties': {
                                                    'upgradeEligible': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    },
                                                    'buyoutRestricted': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    },
                                                    'upgradeEligibilityDate': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    },
                                                    'earlyUpgradeEligible': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    },
                                                    'alwaysUpgradeEligible': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    },
                                                    'buyoutEligible': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    }
                                                }
                                            },
                                            'autoPayDiscount': {
                                                'type': 'string',
                                                'nullable': True
                                            },
                                            'autoPayEligible': {
                                                'type': 'boolean',
                                                'nullable': True
                                            },
                                            'subscriptions': {
                                                'type': 'array',
                                                'nullable': True,
                                                'items': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'skuName': {
                                                            'type': 'string',
                                                            'nullable': True
                                                        },
                                                        'spoId': {
                                                            'type': 'string',
                                                            'nullable': True
                                                        },
                                                        'onPromo': {
                                                            'type': 'boolean',
                                                            'nullable': True
                                                        },
                                                        'enrolled': {
                                                            'type': 'boolean',
                                                            'nullable': True
                                                        },
                                                        'promoRedeemed': {
                                                            'type': 'boolean',
                                                            'nullable': True
                                                        },
                                                        'price': {
                                                            'type': 'string',
                                                            'nullable': True
                                                        },
                                                        'description': {
                                                            'type': 'string',
                                                            'nullable': True
                                                        },
                                                        'onEligiblePlanAndDevice': {
                                                            'type': 'boolean',
                                                            'nullable': True
                                                        },
                                                        'displayName': {
                                                            'type': 'string',
                                                            'nullable': True
                                                        },
                                                        'registrationStatus': {
                                                            'type': 'string',
                                                            'nullable': True
                                                        },
                                                        'status': {
                                                            'type': 'string',
                                                            'nullable': True
                                                        },
                                                        'entitlementStatus': {
                                                            'type': 'string',
                                                            'nullable': True
                                                        },
                                                        'subscriptionId': {
                                                            'type': 'string',
                                                            'nullable': True
                                                        },
                                                        'service': {
                                                            'type': 'string',
                                                            'nullable': True
                                                        },
                                                        'isPerk': {
                                                            'type': 'boolean',
                                                            'nullable': True
                                                        }
                                                    }
                                                }
                                            },
                                            'enrolledForLoyalty': {
                                                'type': 'boolean',
                                                'nullable': True
                                            }
                                        },
                                        'required': [
                                            'mtn', 
                                            'mtnStatus', 
                                            'equipmentInfos'
                                        ]
                                    },
                                    'nullable': True
                                },
                                'paymentInfo': {
                                    'type': 'object',
                                    'description': 'Payment information for the customer.',
                                    'properties': {
                                        'enrolledInAutopay': {
                                            'type': 'boolean',
                                            'description': 'Whether the customer is enrolled in autopay'
                                        },
                                        'invoiceDate': {
                                            'type': 'string',
                                            'description': 'Date of the invoice',
                                            'nullable': True
                                        },
                                        'lastPaymentDate': {
                                            'type': 'string',
                                            'description': 'Date of the last payment',
                                            'nullable': True
                                        },
                                        'paymentDueDate': {
                                            'type': 'string',
                                            'description': 'Due date for payment',
                                            'nullable': True
                                        },
                                        'pastDueDays': {
                                            'type': 'string',
                                            'description': 'Number of days past due',
                                            'nullable': True
                                        },
                                        'enrolledInPaperFree': {
                                            'type': 'boolean',
                                            'description': 'Whether enrolled in paper-free billing',
                                            'nullable': True
                                        },
                                        'lastPaymentAmount': {
                                            'type': 'string',
                                            'description': 'Amount of the last payment',
                                            'nullable': True
                                        },
                                        'eligibleForPaperFree': {
                                            'type': 'boolean',
                                            'description': 'Whether eligible for paper-free billing',
                                            'nullable': True
                                        },
                                        'currentCharges': {
                                            'type': 'string',
                                            'description': 'Current charges amount',
                                            'nullable': True
                                        },
                                        'arPastDueBalance': {
                                            'type': 'string',
                                            'description': 'Accounts receivable past due balance',
                                            'nullable': True
                                        },
                                        'paymentHistory': {
                                            'type': 'array',
                                            'description': 'List of payment history records',
                                            'nullable': True,
                                            'items': {
                                                'type': 'object',
                                                'properties': {
                                                    'totalBalance': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    },
                                                    'adjustedPreviousAmount': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    },
                                                    'amountPaid': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    },
                                                    'billCycleStartDate': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    },
                                                    'invoiceDate': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    },
                                                    'billCycleEndDate': {
                                                        'type': 'string',
                                                        'nullable': True
                                                    }
                                                }
                                            }
                                        },
                                        'pastDueBalance': {
                                            'type': 'string',
                                            'description': 'Past due balance amount',
                                            'nullable': True
                                        },
                                        'outstandingBalance': {
                                            'type': 'string',
                                            'description': 'Outstanding balance amount',
                                            'nullable': True
                                        }
                                    },
                                    'required': [
                                        'enrolledInAutopay'
                                    ],
                                    'nullable': True
                                },
                                'unlimitedPlanPerks': {
                                    'type': 'array',
                                    'description': 'A list of lists of perk dictionaries with the following structure:',
                                    'items': {
                                        'type': 'array',
                                        'items': {
                                            'type': 'object',
                                            'properties': {
                                                'monthly_value': {
                                                    'type': 'string',
                                                    'description': 'Monthly value of the perk.',
                                                    'nullable': True
                                                },
                                                'perk_id': {
                                                    'type': 'string',
                                                    'description': 'Unique identifier for the perk.'
                                                },
                                                'prorate': {
                                                    'type': 'string',
                                                    'description': 'Proration information for the perk.'
                                                },
                                                'description': {
                                                    'type': 'string',
                                                    'description': 'Description of the perk.'
                                                },
                                                'notes': {
                                                    'type': 'string',
                                                    'description': 'Additional notes about the perk.',
                                                    'nullable': True
                                                },
                                                'backdate': {
                                                    'type': 'string',
                                                    'description': 'Backdate information for the perk.'
                                                }
                                            },
                                            'required': [
                                                'perk_id',
                                                'prorate',
                                                'description',
                                                'backdate'
                                            ]
                                        }
                                    }
                                },
                                'sundayMobileValueProposition': {
                                    'type': 'object',
                                    'description': 'Sunday Mobile value proposition information with the following structure:',
                                    'properties': {
                                        'title': {
                                            'type': 'string',
                                            'description': 'Title of the value proposition',
                                            'nullable': True
                                        },
                                        'lastUpdated': {
                                            'type': 'string',
                                            'description': 'Last updated timestamp',
                                            'nullable': True
                                        },
                                        'introduction': {
                                            'type': 'object',
                                            'description': 'Introduction information',
                                            'nullable': True,
                                            'properties': {
                                                'headline': {
                                                    'type': 'string',
                                                    'description': 'Introduction headline',
                                                    'nullable': True
                                                },
                                                'description': {
                                                    'type': 'string',
                                                    'description': 'Introduction description',
                                                    'nullable': True
                                                },
                                                'valueStatement': {
                                                    'type': 'string',
                                                    'description': 'Value statement',
                                                    'nullable': True
                                                },
                                                'launchUpdatesLink': {
                                                    'type': 'object',
                                                    'properties': {
                                                        'text': {
                                                            'type': 'string',
                                                            'description': 'Link text',
                                                            'nullable': True
                                                        },
                                                    },
                                                    'required': [
                                                        'text'
                                                    ],
                                                    'nullable': True
                                                }
                                            },
                                            'required': ['headline', 'description', 'valueStatement', 'launchUpdatesLink']
                                        },
                                        'howItWorks': {
                                            'type': 'object',
                                            'description': 'How it works information',
                                            'nullable': True,
                                            'properties': {
                                                'title': {
                                                    'type': 'string',
                                                    'description': 'How it works title',
                                                    'nullable': True
                                                },
                                                'guarantees': {
                                                    'type': 'array',
                                                    'description': 'List of guarantees',
                                                    'items': {
                                                        'type': 'object',
                                                        'properties': {
                                                            'type': {
                                                                'type': 'string',
                                                                'description': 'Type of guarantee'
                                                            },
                                                            'title': {
                                                                'type': 'string',
                                                                'description': 'Title of the guarantee'
                                                            },
                                                            'startDate': {
                                                                'type': 'string',
                                                                'nullable': True,
                                                                'description': 'Start date of the guarantee'
                                                            },
                                                            'newOffers': {
                                                                'type': 'array',
                                                                'nullable': True,
                                                                'items': {
                                                                    'type': 'object',
                                                                    'properties': {
                                                                        'category': {
                                                                            'type': 'string',
                                                                            'description': 'Offer category'
                                                                        },
                                                                        'details': {
                                                                            'type': 'string',
                                                                            'description': 'Offer details'
                                                                        }
                                                                    },
                                                                    'required': ['category', 'details']
                                                                }
                                                            },
                                                            'explanation': {
                                                                'type': 'array',
                                                                'nullable': True,
                                                                'items': {
                                                                    'type': 'string'
                                                                }
                                                            },
                                                            'exclusions': {
                                                                'type': 'string',
                                                                'nullable': True,
                                                                'description': 'Exclusions text'
                                                            },
                                                            'notes': {
                                                                'type': 'array',
                                                                'nullable': True,
                                                                'items': {
                                                                    'type': 'object',
                                                                    'properties': {
                                                                        'audience': {
                                                                            'type': 'string',
                                                                            'description': 'Target audience'
                                                                        },
                                                                        'detail': {
                                                                            'type': 'string',
                                                                            'description': 'Note detail'
                                                                        }
                                                                    },
                                                                    'required': ['audience', 'detail']
                                                                }
                                                            },
                                                            'systemUpdateNote': {
                                                                'type': 'object',
                                                                'nullable': True,
                                                                'properties': {
                                                                    'title': {
                                                                        'type': 'string',
                                                                        'description': 'System update note title'
                                                                    },
                                                                    'period': {
                                                                        'type': 'string',
                                                                        'description': 'Update period'
                                                                    },
                                                                    'details': {
                                                                        'type': 'array',
                                                                        'items': {
                                                                            'type': 'string'
                                                                        }
                                                                    }
                                                                },
                                                                'required': ['title', 'period', 'details']
                                                            },
                                                            'offer': {
                                                                'type': 'string',
                                                                'nullable': True,
                                                                'description': 'Offer description'
                                                            },
                                                            'summary': {
                                                                'type': 'string',
                                                                'nullable': True,
                                                                'description': 'Summary text'
                                                            },
                                                            'newFeature': {
                                                                'type': 'string',
                                                                'nullable': True,
                                                                'description': 'New feature description'
                                                            },
                                                            'explanationTitle': {
                                                                'type': 'string',
                                                                'nullable': True,
                                                                'description': 'Explanation title'
                                                            },
                                                            'savingsBreakdown': {
                                                                'type': 'array',
                                                                'nullable': True,
                                                                'items': {
                                                                    'type': 'object',
                                                                    'properties': {
                                                                        'area': {
                                                                            'type': 'string',
                                                                            'description': 'Savings area'
                                                                        },
                                                                        'description': {
                                                                            'type': 'string',
                                                                            'description': 'Area description'
                                                                        }
                                                                    },
                                                                    'required': ['area', 'description']
                                                                }
                                                            }
                                                        },
                                                        'required': ['type', 'title']
                                                    },
                                                    'nullable': True
                                                }
                                            },
                                            'required': ['title', 'guarantees']
                                        },
                                        'quickPitch': {
                                            'type': 'object',
                                            'description': 'Quick pitch information',
                                            'nullable': True,
                                            'properties': {
                                                'title': {
                                                    'type': 'string',
                                                    'description': 'Quick pitch title',
                                                    'nullable': True
                                                },
                                                'description': {
                                                    'type': 'string',
                                                    'description': 'Quick pitch description',
                                                    'nullable': True
                                                },
                                                'pitch': {
                                                    'type': 'string',
                                                    'description': 'Quick pitch text',
                                                    'nullable': True
                                                }
                                            },
                                            'required': ['title', 'description', 'pitch']
                                        }
                                    },
                                    'required': []
                                },
                                'sundayMobileOST': {
                                    'type': 'object',
                                    'description': 'A dictionary with the following structure:',
                                    'properties': {},
                                    'required': []
                                },
                                'autoPayPaperFreeDiscountAmountInfo': {
                                    'type': 'object',
                                    'description': 'A dictionary containing details about autopay discounts with the following structure:',
                                    'properties': {},
                                    'required': []
                                },
                                'myPlanPricingDetails': {
                                    'type': 'object',
                                    'description': 'A dictionary with plan names as keys, containing pricing details with the following structure:',
                                    'properties': {},
                                    'required': []
                                },
                                'myPlanPerks': {
                                    'type': 'object',
                                    'description': 'A dictionary with the following structure:',
                                    'properties': {},
                                    'required': []
                                },
                                'myPlanFeatures': {
                                    'type': 'object',
                                    'description': 'A dictionary with plan names as keys and lists of feature descriptions with the following structure:',
                                    'properties': {},
                                    'required': []
                                }
                            },
                            'required': [
                                'hasMtnLoyaltyOffers',
                                'availablePerks',
                                'accountNumber',
                                'status',
                                'statusCode',
                                'customerName',
                                'preferredFirstName',
                                'firstName',
                                'statusMessage',
                                'loyaltyOffersStatusCode',
                                'loyaltyOffers',
                                'unlimitedPlanPerks',
                                'sundayMobileValueProposition',
                                'sundayMobileOST',
                                'autoPayPaperFreeDiscountAmountInfo',
                                'myPlanPricingDetails',
                                'myPlanPerks',
                                'myPlanFeatures'
                            ]
                        }
                    },
                    'required': [
                        'parameters'
                    ]
                }
            },
            'required': [
                'sessionInfo'
            ]
        }
    }
)
def get_pre_authentication_call_data() -> Dict[str, Any]:
    """Retrieves pre-authentication data for the call session.

    This includes information like customer name, account number, loyalty offers,
    and plan perks.

    Returns:
      Dict[str, Any]: An object containing the pre-authentication call data.
        - sessionInfo (Dict[str, Any]): A dictionary containing session information with the following key:
            - parameters (Dict[str, Any]): A dictionary containing pre-authentication parameters with keys:
                - hasMtnLoyaltyOffers (bool): Whether the customer has loyalty offers.
                - availablePerks (List[Dict]): A list of dictionaries, each with a single key for the perk name.
                - accountNumber (str): The customer's account number in format "XXXXXXXXXXX-XXXXX" (11 digits, dash, 5 digits).
                - autopayDiscountAmount (Optional[str]): The autopay discount amount.
                - status (str): The status of the pre-authentication check.
                - statusCode (str): The status code.
                - customerName (str): The customer's full name.
                - customerFirstName (Optional[str]): The customer's first name.
                - customerLastName (Optional[str]): The customer's last name.
                - customerRole (Optional[str]): The customer's role.
                - eligibleForAutopay (Optional[str]): Whether the customer is eligible for autopay.
                - greetByName (Optional[str]): The name to greet the customer by.
                - preferredFirstName (str): The customer's preferred first name.
                - firstName (str): The customer's first name.
                - statusMessage (str): A message describing the status.
                - loyaltyOffersStatusCode (str): Status code for loyalty offers.
                - numberOfLines (Optional[str]): The number of lines on the account.
                - lines (Optional[List[Dict[str, Any]]]): A list of line information dictionaries with the following structure:
                    - mtn (str): Mobile Telephone Number
                    - mtnStatus (Dict): Status information for the mobile telephone number:
                        - isActive (Optional[bool]): Whether the line is currently active.
                        - isSuspendedWithBilling (Optional[bool]): Whether the line is suspended with billing.
                        - isSuspendedWithoutBilling (Optional[bool]): Whether the line is suspended without billing.
                        - voluntarySuspended (Optional[bool]): Whether the line is voluntarily suspended.
                        - involuntarySuspended (Optional[bool]): Whether the line is involuntarily suspended.
                        - involuntarySuspendedWithNonPayment (Optional[bool]): Whether suspended due to non-payment.
                        - mtnStatusReasonCode (Optional[str]): Reason code for the current status.
                    - equipmentInfos (Dict[str, Any]): Equipment information with properties:
                        - deviceInfo (Optional[Dict[str, Any]]): Device information with properties:
                            - displayName (Optional[str]): Display name of the device
                            - category (Optional[Dict]): Device category information:
                                - smartphone (Optional[bool]): Whether it's a smartphone.
                                - basicphone (Optional[bool]): Whether it's a basic phone.
                                - tablet (Optional[bool]): Whether it's a tablet.
                                - smartwatch (Optional[bool]): Whether it's a smartwatch.
                                - homePC (Optional[bool]): Whether it's a home PC.
                                - telematics (Optional[bool]): Whether it's a telematics device.
                                - WSOnly (Optional[bool]): Whether it's a WS-only device.
                                - virtualDevice (Optional[bool]): Whether it's a virtual device.
                                - connectedDevice (Optional[bool]): Whether it's a connected device.
                                - internetDevice (Optional[bool]): Whether it's an internet device.
                                - homeSolutions (Optional[bool]): Whether it's a home solutions device.
                                - laptop (Optional[bool]): Whether it's a laptop.
                            - deviceUrl (Optional[str]): URL for device information
                            - deviceType (Optional[Dict]): Device type information:
                                - device3G (Optional[bool]): Whether it's a 3G device.
                                - device4G (Optional[bool]): Whether it's a 4G device.
                                - device5GE (Optional[bool]): Whether it's a 5G device.
                                - device5GA (Optional[bool]): Whether it's a 5G Advanced device.
                                - backupRouter4G (Optional[bool]): Whether it's a backup 4G router.
                                - homeFusionDevice (Optional[bool]): Whether it's a home fusion device.
                                - autoAttendant (Optional[bool]): Whether it's an auto attendant.
                                - huntGroup (Optional[bool]): Whether it's a hunt group device.
                                - overTheTop (Optional[bool]): Whether it's an over-the-top device.
                                - deskphone (Optional[bool]): Whether it's a desk phone.
                                - device4GO (Optional[bool]): Whether it's a 4G-only device.
                                - antenna5G (Optional[bool]): Whether it's a 5G antenna.
                                - home5G (Optional[bool]): Whether it's a home 5G device.
                                - jetPack4G (Optional[bool]): Whether it's a 4G jetpack.
                                - jetPack5G (Optional[bool]): Whether it's a 5G jetpack.
                                - description (Optional[str]): Description of the device type.
                    - autoPayReflected (Optional[bool]): Whether autopay is reflected
                    - pricePlanInfo (Optional[Dict[str, Any]]): Price plan information with properties:
                        - planId (str): Plan identifier
                        - effectiveDate (str): Effective date of the plan
                        - planDisplayName (str): Display name of the plan
                        - planCategoryName (Optional[str]): Category name of the plan
                        - description (Optional[str]): Description of the plan
                        - planSkuName (Optional[str]): SKU name of the plan
                        - accessCharge (Optional[Dict[str, Any]]): Access charge information with properties:
                            - monthlyAccessCharge (Optional[str]): Monthly access charge amount
                            - finalPriceWithLACAndDiscount (Optional[str]): Final price with LAC and discount
                            - discountedCharge (Optional[str]): Discounted charge amount
                            - finalPriceWithLAC (Optional[str]): Final price with line access charge
                            - discountedAccessChargeWithPerk (Optional[str]): Discounted access charge with perk
                    - mobileInfoAttributes (Optional[Dict[str, Any]]): Mobile info attributes with properties:
                        - accessRoles (Dict[str, bool]): Access roles with properties:
                            - owner (bool): Whether user is owner
                            - manager (bool): Whether user is manager
                            - member (bool): Whether user is member
                    - equipmentUpgradeEligibility (Optional[Dict[str, Any]]): Equipment upgrade eligibility with properties:
                        - upgradeEligible (Optional[str]): Whether upgrade is eligible
                        - buyoutRestricted (Optional[str]): Whether buyout is restricted
                        - upgradeEligibilityDate (Optional[str]): Date when upgrade becomes eligible
                        - earlyUpgradeEligible (Optional[str]): Whether early upgrade is eligible
                        - alwaysUpgradeEligible (Optional[str]): Whether always upgrade eligible
                        - buyoutEligible (Optional[str]): Whether buyout is eligible
                    - autoPayDiscount (Optional[str]): Autopay discount information
                    - autoPayEligible (Optional[bool]): Whether eligible for autopay
                    - subscriptions (Optional[List[Dict[str, Any]]]): List of subscriptions with properties:
                        - skuName (Optional[str]): SKU name of the subscription
                        - spoId (Optional[str]): Service plan option ID
                        - onPromo (Optional[bool]): Whether the subscription is on promotion
                        - enrolled (Optional[bool]): Whether the customer is enrolled
                        - promoRedeemed (Optional[bool]): Whether the promotion has been redeemed
                        - price (Optional[str]): Price of the subscription
                        - description (Optional[str]): Description of the subscription
                        - onEligiblePlanAndDevice (Optional[bool]): Whether eligible for plan and device
                        - displayName (Optional[str]): Display name of the subscription
                        - registrationStatus (Optional[str]): Registration status of the subscription
                        - status (Optional[str]): Current status of the subscription
                        - entitlementStatus (Optional[str]): Entitlement status of the subscription
                        - subscriptionId (Optional[str]): Unique identifier for the subscription
                        - service (Optional[str]): Service type of the subscription
                        - isPerk (Optional[bool]): Whether this is a perk subscription
                    - enrolledForLoyalty (Optional[bool]): Whether enrolled for loyalty
                - loyaltyOffers (List[Dict[str, Any]]): A list of loyalty offer dictionaries with the following structure:
                    - OfferDesc (str): Description of the loyalty offer.
                    - offerOrder (str): Order/priority of the offer.
                    - offerType (str): Type of the offer (e.g., 'DISCOUNT', 'PERK').
                    - OfferID (str): Unique identifier for the offer.
                - unlimitedPlanPerks (List[List[Dict[str, Any]]]): A list of lists of perk dictionaries with the following structure:
                    - monthly_value (Optional[str]): Monthly value of the perk.
                    - perk_id (str): Unique identifier for the perk.
                    - prorate (str): Proration information for the perk.
                    - description (str): Description of the perk.
                    - notes (Optional[str]): Additional notes about the perk.
                    - backdate (str): Backdate information for the perk.
                - sundayMobileValueProposition (Dict[str, Any]): Sunday Mobile value proposition information with the following structure:
                    - title (Optional[str]): Title of the value proposition
                    - lastUpdated (Optional[str]): Last updated timestamp
                    - introduction (Optional[Dict[str, Any]]): Introduction information with properties:
                        - headline (Optional[str]): Introduction headline
                        - description (Optional[str]): Introduction description
                        - valueStatement (Optional[str]): Value statement
                        - launchUpdatesLink (Optional[Dict[str, str]]): Launch updates link with properties:
                            - text (Optional[str]): Link text
                    - howItWorks (Optional[Dict[str, Any]]): How it works information with properties:
                        - title (Optional[str]): How it works title
                        - guarantees (Optional[List[Dict[str, Any]]]): List of guarantees with properties:
                            - type (str): Type of guarantee
                            - title (str): Title of the guarantee
                            - startDate (Optional[str]): Start date of the guarantee
                            - newOffers (Optional[List[Dict[str, str]]]): New offers with properties:
                                - category (str): Offer category
                                - details (str): Offer details
                            - explanation (Optional[List[str]]): Explanation text
                            - exclusions (Optional[str]): Exclusions text
                            - notes (Optional[List[Dict[str, str]]]): Notes with properties:
                                - audience (str): Target audience
                                - detail (str): Note detail
                            - systemUpdateNote (Optional[Dict[str, Any]]): System update note with properties:
                                - title (str): System update note title
                                - period (str): Update period
                                - details (List[str]): Update details
                            - offer (Optional[str]): Offer description
                            - summary (Optional[str]): Summary text
                            - newFeature (Optional[str]): New feature description
                            - explanationTitle (Optional[str]): Explanation title
                            - savingsBreakdown (Optional[List[Dict[str, str]]]): Savings breakdown with properties:
                                - area (str): Savings area
                                - description (str): Area description
                    - quickPitch (Optional[Dict[str, str]]): Quick pitch information with properties:
                        - title (Optional[str]): Quick pitch title
                        - description (Optional[str]): Quick pitch description
                        - pitch (Optional[str]): Quick pitch text
                - sundayMobileOST (Dict[str, str]): A dictionary with the title of the OST content and the content of the OST message.
                - autoPayPaperFreeDiscountAmountInfo (Dict[str, Any]): A dictionary containing details about autopay discounts.
                - myPlanPricingDetails (Dict[str, str]): A dictionary with plan names as keys, containing pricing details.
                - myPlanPerks (Dict[str, Any]): A dictionary with the following structure:
                    - myplan_perks (List[Dict[str, Any]]): List of perk details with the following structure:
                        - monthly_value (str): Monthly value of the perk.
                        - monthly_cost (str): Monthly cost of the perk.
                        - savings (str): Savings amount from the perk.
                        - description (str): Description of the perk.
                        - perk (str): Name of the perk.
                        - notes (Optional[str]): Additional notes about the perk.
                - paymentInfo (Optional[Dict[str, Any]]): Payment information for the customer with the following structure:
                    - enrolledInAutopay (bool): Whether the customer is enrolled in autopay
                    - invoiceDate (Optional[str]): Date of the invoice
                    - lastPaymentDate (Optional[str]): Date of the last payment
                    - paymentDueDate (Optional[str]): Due date for payment
                    - pastDueDays (Optional[str]): Number of days past due
                    - enrolledInPaperFree (Optional[bool]): Whether enrolled in paper-free billing
                    - lastPaymentAmount (Optional[str]): Amount of the last payment
                    - eligibleForPaperFree (Optional[bool]): Whether eligible for paper-free billing
                    - currentCharges (Optional[str]): Current charges amount
                    - arPastDueBalance (Optional[str]): Accounts receivable past due balance
                    - paymentHistory (Optional[List[Dict[str, Any]]]): List of payment history records with the following structure:
                        - totalBalance (Optional[str]): Total balance amount
                        - adjustedPreviousAmount (Optional[str]): Adjusted previous amount
                        - amountPaid (Optional[str]): Amount paid
                        - billCycleStartDate (Optional[str]): Bill cycle start date
                        - invoiceDate (Optional[str]): Invoice date
                        - billCycleEndDate (Optional[str]): Bill cycle end date
                    - pastDueBalance (Optional[str]): Past due balance amount
                    - outstandingBalance (Optional[str]): Outstanding balance amount
                - myPlanFeatures (Dict[str, List[str]]): A dictionary with plan names as keys and lists of feature descriptions.

    Raises:
        AuthenticationFailedError: If pre-authentication data not found in database.
        ValidationError: If the pre-authentication data fails validation or is missing required keys.
    """
    profile = DB.get("PROFILE_BEFORE_AUTH")

    # Check if profile data exists
    if profile is None or not profile:
        raise AuthenticationFailedError("Pre-authentication data not found in database")

    # Validate that required keys are present
    required_keys = ["sessionInfo"]

    for key in required_keys:
        if key not in profile:
            raise ValueError(f"Missing required key '{key}' in pre-authentication data")

    # Validate sessionInfo structure
    session_info = profile.get("sessionInfo", {})
    if not session_info:
        raise ValueError("sessionInfo is empty or missing")

    # Validate parameters structure
    parameters = session_info.get("parameters", {})
    if not parameters:
        raise ValueError("parameters is empty or missing in sessionInfo")

    # Validate critical parameters
    critical_params = [
        'autoPayPaperFreeDiscountAmountInfo',
        'availablePerks',
        'firstName',
        'hasMtnLoyaltyOffers',
        'myPlanFeatures',
        'myPlanPerks',
        'myPlanPricingDetails',
        'preferredFirstName',
        'statusMessage',
        'sundayMobileOST',
        'sundayMobileValueProposition',
        'unlimitedPlanPerks',
        "accountNumber",
        "customerName",
        "loyaltyOffers",
        "loyaltyOffersStatusCode",
        "status",
        "statusCode",
    ]

    for param in critical_params:
        if param not in parameters:
            raise ValueError(f"Missing critical parameter '{param}' in pre-authentication data")
    
    return profile

# --- Python Tools ---
@tool_spec(
    input_model=RecordCallOutcomeAndDisconnectInput,
    output_model=StatusOutput,
    description="""Logs the final outcome of the call and terminates the connection.
        
This is a terminal action used to end the call for any reason OTHER THAN a
transfer to a live agent. It records the key events and the final reason for
the disconnection (e.g., customer declined offer, voicemail detected, DNC
request processed) for reporting purposes. After invoking this action, you
must immediately invoke the done() action to hang up.
        
When to call:
  Use this as the final step for all non-transfer call endings.
  Examples: The customer accepts and enrolls in the offer, the customer
  declines the offer, a Do Not Call/SMS request is completed, or a voicemail
  is detected and the message has been left.
        
When NOT to call:
  Do NOT use this if the customer needs to be transferred to a live agent. Use
  transfer_to_live_agent instead.""",
    error_model=[
        ErrorObject(ValidationError, ["Raised if the call end state or disposition code is invalid."])
    ],
    spec={
        'name': 'record_call_outcome_and_disconnect',
        'description': """ Logs the final outcome of the call and terminates the connection.
        
        This is a terminal action used to end the call for any reason OTHER THAN a
        transfer to a live agent. It records the key events and the final reason for
        the disconnection (e.g., customer declined offer, voicemail detected, DNC
        request processed) for reporting purposes. After invoking this action, you
        must immediately invoke the done() action to hang up.
        
        When to call:
          Use this as the final step for all non-transfer call endings.
          Examples: The customer accepts and enrolls in the offer, the customer
          declines the offer, a Do Not Call/SMS request is completed, or a voicemail
          is detected and the message has been left.
        
        When NOT to call:
          Do NOT use this if the customer needs to be transferred to a live agent. Use
          transfer_to_live_agent instead. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'dispositionSequence': {
                    'type': 'string',
                    'description': 'Disposition sequence for the call.'
                },
                'callEndState': {
                    'type': 'string',
                    'description': """ The primary reason for ending the call (e.g.,
                    'DISCONNECT', 'DO_NOT_CALL', 'ANSWERING_MACHINE'). """
                },
                'dispositionCode': {
                    'type': 'string',
                    'description': """ The final, specific status code for the call (e.g.,
                    'PROMO_DECLINED', 'ANSWERING_MACHINE'). """
                },
                'preferredLang': {
                    'type': 'string',
                    'description': """ The customer's preferred language. Defaults to 'E' for
                    English. Set to 'S' for Spanish. """
                }
            },
            'required': []
        },
        'response': {
            'type': 'object',
            'description': 'A dictionary confirming the action was received:',
            'properties': {
                'status': {
                    'type': 'string',
                    'description': '"success" if the action was recorded.'
                }
            },
            'required': [
                'status'
            ]
        }
    }
)
def record_call_outcome_and_disconnect(
    dispositionSequence: str = '',
    callEndState: str = '',
    dispositionCode: str = '',
    preferredLang: str = 'E',
) -> Dict[str, str]:
    """Logs the final outcome of the call and terminates the connection.

    This is a terminal action used to end the call for any reason OTHER THAN a
    transfer to a live agent. It records the key events and the final reason for
    the disconnection (e.g., customer declined offer, voicemail detected, DNC
    request processed) for reporting purposes. After invoking this action, you
    must immediately invoke the done() action to hang up.

    When to call:
      Use this as the final step for all non-transfer call endings.
      Examples: The customer accepts and enrolls in the offer, the customer
      declines the offer, a Do Not Call/SMS request is completed, or a voicemail
      is detected and the message has been left.

    When NOT to call:
      Do NOT use this if the customer needs to be transferred to a live agent. Use
      transfer_to_live_agent instead.

    Args:
      dispositionSequence (Optional[str]): Disposition sequence for the call.
      callEndState (Optional[str]): The primary reason for ending the call (e.g.,
        'DISCONNECT', 'DO_NOT_CALL', 'ANSWERING_MACHINE').
      dispositionCode (Optional[str]): The final, specific status code for the call (e.g.,
        'PROMO_DECLINED', 'ANSWERING_MACHINE').
      preferredLang (str): The customer's preferred language. Defaults to 'E' for
        English. Set to 'S' for Spanish.

    Returns:
      Dict[str, str]: A dictionary confirming the action was received:
        - status (str): "success" if the action was recorded.

    Raises:
        ValueError: If the call end state or disposition code is invalid.
    """
    if callEndState:
        allowed_end_states = {e.value for e in CallEndState}
        if callEndState.upper() not in allowed_end_states:
            raise ValueError(f"Invalid call end state: {callEndState}")
    if dispositionCode:
        allowed_dispositions = {e.value for e in DispositionCode}
        if dispositionCode.upper() not in allowed_dispositions:
            raise ValueError(f"Invalid disposition code: {dispositionCode}")

    recorded_inputs = {
        'dispositionSequence': dispositionSequence,
        'callEndState': callEndState,
        'dispositionCode': dispositionCode,
    }
    if preferredLang != 'E':
        recorded_inputs['preferredLang'] = preferredLang
    utils._set_conversation_status('disconnect', **recorded_inputs)
    return {'status': 'success'}


@tool_spec(
    input_model=TransferToLiveAgentInput,
    output_model=StatusOutput,
    description="""Transfers the customer to a live human agent.
        
This is a terminal action that logs the reason for the transfer and then
hands the call off to a human agent from the Sunday Mobile loyalty department.
After invoking this action, you must immediately invoke the done() action
to complete the transfer process.
        
When to call:
  The customer explicitly asks to speak to a person ("agent", "human", etc.).
  The customer requests something outside your scope (e.g., changing plans,
  making payments, porting a number).
  The customer fails or declines the authentication process.
  The customer is speaking Spanish.
  The customer insists on leaving Sunday Mobile or cancelling their service.
        
When NOT to call:
  Do not use this for standard call endings where a transfer is not required.
  Use record_call_outcome_and_disconnect for those cases.""",
    error_model=[
        ErrorObject(ValidationError, ["Raised if the call end state or disposition code is invalid."])
    ],
    spec={
        'name': 'transfer_to_live_agent',
        'description': """ Transfers the customer to a live human agent.
        
        This is a terminal action that logs the reason for the transfer and then
        hands the call off to a human agent from the Sunday Mobile loyalty department.
        After invoking this action, you must immediately invoke the done() action
        to complete the transfer process.
        
        When to call:
          The customer explicitly asks to speak to a person ("agent", "human", etc.).
          The customer requests something outside your scope (e.g., changing plans,
          making payments, porting a number).
          The customer fails or declines the authentication process.
          The customer is speaking Spanish.
          The customer insists on leaving Sunday Mobile or cancelling their service.
        
        When NOT to call:
          Do not use this for standard call endings where a transfer is not required.
          Use record_call_outcome_and_disconnect for those cases. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'dispositionSequence': {
                    'type': 'string',
                    'description': 'Disposition sequence for the call.'
                },
                'callEndState': {
                    'type': 'string',
                    'description': """ The reason for ending the call. MUST be set to
                    'AGENT_TRANSFER'. """
                },
                'dispositionCode': {
                    'type': 'string',
                    'description': """ The specific reason for the transfer (e.g.,
                    'AGENT_TRANSFER', 'AUTH_FAILED'). """
                },
                'preferredLang': {
                    'type': 'string',
                    'description': """ The customer's preferred language. Defaults to 'E' for
                    English. Set to 'S' for Spanish transfers. """
                }
            },
            'required': []
        },
        'response': {
            'type': 'object',
            'description': 'A dictionary confirming the action was received:',
            'properties': {
                'status': {
                    'type': 'string',
                    'description': '"success" if the action was recorded.'
                }
            },
            'required': [
                'status'
            ]
        }
    }
)
def transfer_to_live_agent(
    dispositionSequence: str = '',
    callEndState: str = '',
    dispositionCode: str = '',
    preferredLang: str = 'E',
) -> Dict[str, str]:
    """Transfers the customer to a live human agent.

    This is a terminal action that logs the reason for the transfer and then
    hands the call off to a human agent from the Sunday Mobile loyalty department.
    After invoking this action, you must immediately invoke the done() action
    to complete the transfer process.

    When to call:
      The customer explicitly asks to speak to a person ("agent", "human", etc.).
      The customer requests something outside your scope (e.g., changing plans,
      making payments, porting a number).
      The customer fails or declines the authentication process.
      The customer is speaking Spanish.
      The customer insists on leaving Sunday Mobile or cancelling their service.

    When NOT to call:
      Do not use this for standard call endings where a transfer is not required.
      Use record_call_outcome_and_disconnect for those cases.

    Args:
      dispositionSequence (Optional[str]): Disposition sequence for the call.
      callEndState (Optional[str]): The reason for ending the call. MUST be set to
        'AGENT_TRANSFER'.
      dispositionCode (Optional[str]): The specific reason for the transfer (e.g.,
        'AGENT_TRANSFER', 'AUTH_FAILED').
      preferredLang (str): The customer's preferred language. Defaults to 'E' for
        English. Set to 'S' for Spanish transfers.

    Returns:
      Dict[str, str]: A dictionary confirming the action was received:
        - status (str): "success" if the action was recorded.

    Raises:
        ValueError: If the call end state or disposition code is invalid.
    """
    if callEndState:
        allowed_end_states = {e.value for e in CallEndState}
        if callEndState.upper() not in allowed_end_states:
            raise ValueError(f"Invalid call end state: {callEndState}")
    if dispositionCode:
        allowed_dispositions = {e.value for e in DispositionCode}
        if dispositionCode.upper() not in allowed_dispositions:
            raise ValueError(f"Invalid disposition code: {dispositionCode}")

    recorded_inputs = {
        'dispositionSequence': dispositionSequence,
        'callEndState': callEndState,
        'dispositionCode': dispositionCode,
    }
    if preferredLang != 'E':
        recorded_inputs['preferredLang'] = preferredLang
    utils._set_conversation_status('live_agent_transfer', **recorded_inputs)
    return {'status': 'success'}


@tool_spec(
    input_model=EnrollInOfferInput,
    output_model=StatusOutput,
    description="""Enrolls the customer in the specific loyalty offer.
        
This action submits the request to add the pre-defined loyalty discount to
the customer's account. This is a "Gated Action" and is strictly prohibited
from being called unless the customer has been successfully authenticated.
        
When to call:
  Call this action ONLY after the customer has explicitly agreed to the offer
  AND has been successfully authenticated.
        
When NOT to call:
  You MUST NOT call this if the customer has not been authenticated.
  Do not call if the customer has declined the offer or has not yet explicitly
  agreed to it.
  Do not call this action more than once per session.""",
    error_model=[
        ErrorObject(AuthenticationFailedError, ['Raised if the customer is not authenticated.']),
        ErrorObject(ValidationError, ['Raised if the accountNumber or offerId parameters are invalid.']),
        ErrorObject(InvalidRequestError, ['Raised if the accountNumber or offerId does not match the authenticated account number or offer ID.']),
    ],
    spec={
        'name': 'enroll_in_offer',
        'description': """ Enrolls the customer in the specific loyalty offer.
        
        This action submits the request to add the pre-defined loyalty discount to
        the customer's account. This is a "Gated Action" and is strictly prohibited
        from being called unless the customer has been successfully authenticated.
        
        When to call:
          Call this action ONLY after the customer has explicitly agreed to the offer
          AND has been successfully authenticated.
        
        When NOT to call:
          You MUST NOT call this if the customer has not been authenticated.
          Do not call if the customer has declined the offer or has not yet explicitly
          agreed to it.
          Do not call this action more than once per session. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'accountNumber': {
                    'type': 'string',
                    'description': """ The customer's account number in format "XXXXXXXXXXX-XXXXX" (11 digits, dash, 5 digits), 
                    which must be retrieved from the authenticated customer profile. """
                },
                'offerId': {
                    'type': 'string',
                    'description': """ The unique ID for the loyalty offer, retrieved from the
                    initial get_pre_authentication_call_data action. """
                }
            },
            'required': [
                'accountNumber',
                'offerId'
            ]
        },
        'response': {
            'type': 'object',
            'description': 'A dictionary containing the submission status of the offer enrollment.',
            'properties': {
                'status': {
                    'type': 'string',
                    'description': 'A status code of success.'
                }
            },
            'required': [
                'status'
            ]
        }
    }
)
def enroll_in_offer(accountNumber: str, offerId: str) -> Dict[str, str]:
    """Enrolls the customer in the specific loyalty offer.

    This action submits the request to add the pre-defined loyalty discount to
    the customer's account. This is a "Gated Action" and is strictly prohibited
    from being called unless the customer has been successfully authenticated.

    When to call:
      Call this action ONLY after the customer has explicitly agreed to the offer
      AND has been successfully authenticated.

    When NOT to call:
      You MUST NOT call this if the customer has not been authenticated.
      Do not call if the customer has declined the offer or has not yet explicitly
      agreed to it.
      Do not call this action more than once per session.

    Args:
      accountNumber (str): The customer's account number in format "XXXXXXXXXXX-XXXXX" (11 digits, dash, 5 digits), 
        which must be retrieved from the authenticated customer profile.
      offerId (str): The unique ID for the loyalty offer, retrieved from the
        initial get_pre_authentication_call_data action.

    Returns:
      Dict[str, str]: A dictionary containing the submission status of the offer enrollment.
        - status (str): A status code of success.

    Raises:
        AuthenticationFailedError: If the customer is not authenticated.
        ValidationError: If the accountNumber or offerId parameters are invalid.
        InvalidRequestError: If the accountNumber or offerId does not match the authenticated account number or offer ID.

    """
    # Check authentication status
    if DB.get("AUTH_STATUS") != "ACCEPT":
        raise AuthenticationFailedError(
            "Customer must be authenticated to enroll in an offer."
        )

    customer_profile_after_auth = DB.get("PROFILE_AFTER_AUTH", {}).get("customerProfile",{})
    if accountNumber.strip() != customer_profile_after_auth.get("accountNumber"):
        raise InvalidRequestError("Account number does not match the authenticated account number.")
    
    customer_loyalty_offers = (
        DB.get("PROFILE_BEFORE_AUTH", {})
        .get("sessionInfo", {})
        .get("parameters", {})
        .get("loyaltyOffers", [])
    )
    if offerId.strip() not in [offer.get("OfferID") for offer in customer_loyalty_offers]:
        raise InvalidRequestError("Offer ID does not match the authenticated offer ID.")
    
    DB["OFFER_ENROLLMENT"] = {
        "accountNumber": accountNumber.strip(),
        "offerId": offerId.strip(),
    }
    return {'status': 'success'}


# --- System Tools ---
@tool_spec(
    input_model=DoneInput,
    output_model=StringOutput,
    description="Indicates that the agent's task is complete.",
    spec={
        'name': 'done',
        'description': "Indicates that the agent's task is complete.",
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        },
        'response': {
            'type': 'string',
            'description': 'An empty string indicating that the task has been completed.'
        }
    }
)
def done() -> str:
    """Indicates that the agent's task is complete.
    Returns:
      An empty string indicating that the task has been completed.
    """
    utils._set_session_status('done')
    return ""


@tool_spec(
    input_model=FailInput,
    output_model=FailOutput,
    description="Indicates failure because the agent could not understand the customer.",
    spec={
        'name': 'fail',
        'description': 'Indicates failure because the agent could not understand the customer.',
        'parameters': {
            'type': 'object',
            'properties': {
                'summary': {
                    'type': 'string',
                    'description': 'Summary of the failure reason.',
                    'nullable': True
                }
            },
            'required': []
        },
        'response': {
            'type': 'string',
            'description': 'A string indicating that the task has been failed.'
        }
    }
)
def fail(summary: Optional[str] = None) -> str:
    """Indicates failure because the agent could not understand the customer.

    Args:
      summary (Optional[str]): Summary of the failure reason.

    Returns:
      A string indicating that the task has been failed.
    """
    utils._set_session_status('fail')
    return f'Failing task. summary: {summary}'


@tool_spec(
    input_model=CancelInput,
    output_model=CancelOutput,
    description="Indicates cancellation because the customer does not want to proceed.",
    spec={
        'name': 'cancel',
        'description': 'Indicates cancellation because the customer does not want to proceed.',
        'parameters': {
            'type': 'object',
            'properties': {
                'summary': {
                    'type': 'string',
                    'description': 'Summary of the cancellation reason.',
                    'nullable': True
                }
            },
            'required': []
        },
        'response': {
            'type': 'string',
            'description': 'A string indicating that the task has been cancelled.'
        }
    }
)
def cancel(summary: Optional[str] = None) -> str:
    """Indicates cancellation because the customer does not want to proceed.

    Args:
      summary (Optional[str]): Summary of the cancellation reason.

    Returns:
      A string indicating that the task has been cancelled.
    """
    utils._set_session_status('cancel')
    return f'Cancelling task. summary: {summary}'


@tool_spec(
    input_model=EscalateInput,
    output_model=StringOutput,
    description="Indicates escalation to a live agent.",
    spec={
        'name': 'escalate',
        'description': 'Indicates escalation to a live agent.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        },
        'response': {
            'type': 'string',
            'description': 'A string indicating that the task has been escalated to a live agent.'
        }
    }
)
def escalate() -> str:
    """Indicates escalation to a live agent.
    Returns:
      A string indicating that the task has been escalated to a live agent.
    """
    utils._set_session_status('escalate')
    return 'Escalated to live agent.'
