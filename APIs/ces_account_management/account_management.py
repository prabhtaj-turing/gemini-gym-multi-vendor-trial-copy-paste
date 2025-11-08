"""
Account Management Service Implementation
"""
from common_utils.custom_errors import InvalidEmailError
from common_utils.tool_spec_decorator import tool_spec, ErrorObject
from common_utils.utils import validate_email_util
from typing import Literal, Any, Dict, Union, Optional

from .SimulationEngine import db
from .SimulationEngine.custom_errors import AccountNotFoundError, ActionNotSupportedError, ServicePlanNotFoundError
from .SimulationEngine.phone_utils import normalize_phone_number, is_phone_number_valid
from .SimulationEngine import utils
from .SimulationEngine.models import (
    CustomerAccountDetails,
    DeviceIdentifierType,
    DeviceUpgradeEligibility,
    ServiceModificationAction,
    ServiceModificationResponse,
    KnowledgeBaseQueryResponse,
    KnowledgeBaseSnippet,
    TerminalResponse,
    # Input Models
    AccountInformationUpdateInput,
    GetCustomerAccountDetailsInput,
    UpdateAccountInformationInput,
    CheckDeviceUpgradeEligibilityInput,
    ModifyServicePlanOrFeatureInput,
    QueryAvailablePlansAndFeaturesInput,
    QueryAccountOrdersInput,
    EscalateInput,
    FailInput,
    CancelInput,
)



DB = db.DB



@tool_spec(
    input_model=GetCustomerAccountDetailsInput,
    output_model=CustomerAccountDetails,
    description="""Retrieves a comprehensive set of details for a given customer account.
        
        When to Use:
        - After a customer has been successfully identified and verified.
        - Use this function to answer questions about the customer's billing address,
          contact information, service plans, active features, or devices.
        - This should be the first step before performing any account modifications.""",
    error_model=[
        ErrorObject(ValueError, ['Raised if accountId is empty, not a string, or validation fails.']),
        ErrorObject(AccountNotFoundError, ['Raised if accountId is not found in the database.'])
    ],
    spec={
        'name': 'get_customer_account_details',
        'description': """ Retrieves a comprehensive set of details for a given customer account.
        
        When to Use:
        - After a customer has been successfully identified and verified.
        - Use this function to answer questions about the customer's billing address,
          contact information, service plans, active features, or devices.
        - This should be the first step before performing any account modifications. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'accountId': {
                    'type': 'string',
                    'description': """ The unique identifier for the customer's account or phone number. 
                    Example: "ACC123456789" or "222-334-4556" """
                }
            },
            'required': [
                'accountId'
            ]
        },
        'response': {
            'type': 'object',
            'description': "Dictionary containing the full details of the customer's account:",
            'properties': {
                'accountId': {
                    'type': 'string',
                    'description': "Customer's unique account identifier"
                },
                'customerName': {
                    'type': 'string',
                    'description': "Customer's full name"
                },
                'contactEmail': {
                    'type': 'string',
                    'description': 'Primary contact email address'
                },
                'contactPhone': {
                    'type': 'string',
                    'description': 'Primary contact phone number'
                },
                'billingAddress': {
                    'type': 'object',
                    'description': 'Billing address information',
                    'properties': {
                        'recipientName': {
                            'type': 'string',
                            'description': 'Name for billing address'
                        },
                        'streetAddressLine1': {
                            'type': 'string',
                            'description': 'Primary street address'
                        },
                        'streetAddressLine2': {
                            'type': 'string',
                            'description': 'Secondary address line (apt, suite, etc.)',
                            'nullable': True
                        },
                        'city': {
                            'type': 'string',
                            'description': 'City name'
                        },
                        'state': {
                            'type': 'string',
                            'description': 'State or province code'
                        },
                        'zipCode': {
                            'type': 'string',
                            'description': 'ZIP or postal code'
                        },
                        'country': {
                            'type': 'string',
                            'description': 'Country code (e.g., US, CA)'
                        }
                    },
                    'required': [
                        'recipientName',
                        'streetAddressLine1',
                        'city',
                        'state',
                        'zipCode',
                        'country'
                    ]
                },
                'serviceAddress': {
                    'type': 'object',
                    'description': 'Service installation address',
                    'properties': {
                        'recipientName': {
                            'type': 'string',
                            'description': 'Name for service installation address'
                        },
                        'streetAddressLine1': {
                            'type': 'string',
                            'description': 'Primary street address'
                        },
                        'streetAddressLine2': {
                            'type': 'string',
                            'description': 'Secondary address line (apt, suite, etc.)',
                            'nullable': True
                        },
                        'city': {
                            'type': 'string',
                            'description': 'City name'
                        },
                        'state': {
                            'type': 'string',
                            'description': 'State or province code'
                        },
                        'zipCode': {
                            'type': 'string',
                            'description': 'ZIP or postal code'
                        },
                        'country': {
                            'type': 'string',
                            'description': 'Country code (e.g., US, CA)'
                        }
                    },
                    'required': [
                        'recipientName',
                        'streetAddressLine1',
                        'city',
                        'state',
                        'zipCode',
                        'country'
                    ]
                },
                'communicationPreferences': {
                    'type': 'object',
                    'description': 'Email and SMS preferences',
                    'properties': {
                        'emailOptIn': {
                            'type': 'boolean',
                            'description': 'Whether customer wants email communications'
                        },
                        'smsOptIn': {
                            'type': 'boolean',
                            'description': 'Whether customer wants SMS communications'
                        }
                    },
                    'required': [
                        'emailOptIn',
                        'smsOptIn'
                    ]
                },
                'devices': {
                    'type': 'array',
                    'description': 'List of devices on the account',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'deviceId': {
                                'type': 'string',
                                'description': 'Unique device identifier'
                            },
                            'deviceName': {
                                'type': 'string',
                                'description': 'Name of the device'
                            },
                            'lineNumber': {
                                'type': 'string',
                                'description': 'Phone number associated with the device'
                            },
                            'upgradeEligibilityDate': {
                                'type': 'string',
                                'description': 'Date when device becomes eligible for upgrade'
                            },
                            'paymentPlanActive': {
                                'type': 'boolean',
                                'description': 'Whether device has an active payment plan'
                            },
                            'paymentPlanRemainingMonths': {
                                'type': 'integer',
                                'description': 'Remaining months on payment plan'
                            }
                        },
                        'required': [
                            'deviceId',
                            'deviceName',
                            'lineNumber',
                            'upgradeEligibilityDate',
                            'paymentPlanActive',
                            'paymentPlanRemainingMonths'
                        ]
                    }
                },
                'services': {
                    'type': 'array',
                    'description': 'List of active service plans',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'serviceId': {
                                'type': 'string',
                                'description': 'Unique identifier for the service'
                            },
                            'planName': {
                                'type': 'string',
                                'description': 'Name of the service plan'
                            },
                            'planId': {
                                'type': 'string',
                                'description': 'Unique identifier for the plan'
                            },
                            'monthlyCost': {
                                'type': 'number',
                                'description': 'Monthly cost of the service'
                            },
                            'dataAllowance': {
                                'type': 'string',
                                'description': 'Data allowance for the service (e.g., Unlimited, 10GB)',
                                'nullable': True
                            },
                            'activeFeatures': {
                                'type': 'array',
                                'description': 'List of active features for this service',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'featureId': {
                                            'type': 'string',
                                            'description': 'Unique identifier for the feature'
                                        },
                                        'featureName': {
                                            'type': 'string',
                                            'description': 'Name of the feature'
                                        },
                                        'monthlyCost': {
                                            'type': 'number',
                                            'description': 'Monthly cost of the feature'
                                        }
                                    },
                                    'required': [
                                        'featureId',
                                        'featureName',
                                        'monthlyCost'
                                    ]
                                }
                            }
                        },
                        'required': [
                            'serviceId',
                            'planName',
                            'planId',
                            'monthlyCost',
                            'activeFeatures'
                        ]
                    }
                },
                'isVerified': {
                    'type': 'boolean',
                    'description': 'Whether the account is verified'
                },
                'securityPinSet': {
                    'type': 'boolean',
                    'description': 'Whether security PIN is configured'
                }
            },
            'required': [
                'accountId',
                'customerName',
                'contactEmail',
                'contactPhone',
                'billingAddress',
                'serviceAddress',
                'communicationPreferences',
                'devices',
                'services',
                'isVerified',
                'securityPinSet'
            ]
        }
    }
)
def get_customer_account_details(
    accountId: str,
) -> Dict[str, Any]:
    """
    Retrieves a comprehensive set of details for a given customer account.

    When to Use:
    - After a customer has been successfully identified and verified.
    - Use this function to answer questions about the customer's billing address,
      contact information, service plans, active features, or devices.
    - This should be the first step before performing any account modifications.

    Args:
        accountId (str): The unique identifier for the customer's account or phone number. 
            Example: "ACC123456789" or "222-334-4556"

    Returns:
        Dict[str, Any]: Dictionary containing the full details of the customer's account:
            - accountId (str): Customer's unique account identifier
            - customerName (str): Customer's full name
            - contactEmail (str): Primary contact email address
            - contactPhone (str): Primary contact phone number
            - billingAddress (Dict[str, Union[str, None]]): Billing address information with fields:
                - recipientName (str): Name for billing address
                - streetAddressLine1 (str): Primary street address
                - streetAddressLine2 (Optional[str]): Secondary address line (apt, suite, etc.)
                - city (str): City name
                - state (str): State or province code
                - zipCode (str): ZIP or postal code
                - country (str): Country code (e.g., US, CA)
            - serviceAddress (Dict[str, Union[str, None]]): Service installation address with fields:
                - recipientName (str): Name for service installation address
                - streetAddressLine1 (str): Primary street address
                - streetAddressLine2 (Optional[str]): Secondary address line (apt, suite, etc.)
                - city (str): City name
                - state (str): State or province code
                - zipCode (str): ZIP or postal code
                - country (str): Country code (e.g., US, CA)
            - communicationPreferences (Dict[str, bool]): Email and SMS preferences with fields:
                - emailOptIn (bool): Whether customer wants email communications
                - smsOptIn (bool): Whether customer wants SMS communications
            - devices (List[Dict[str, Union[str, bool, int]]]): List of devices on the account with fields:
                - deviceId (str): Unique device identifier
                - deviceName (str): Name of the device
                - lineNumber (str): Phone number associated with the device
                - upgradeEligibilityDate (str): Date when device becomes eligible for upgrade
                - paymentPlanActive (bool): Whether device has an active payment plan
                - paymentPlanRemainingMonths (int): Remaining months on payment plan
            - services (List[Dict[str, Any]]): List of active service plans with fields:
                - serviceId (str): Unique identifier for the service
                - planName (str): Name of the service plan
                - planId (str): Unique identifier for the plan
                - monthlyCost (float): Monthly cost of the service
                - dataAllowance (Optional[str]): Data allowance for the service (e.g., Unlimited, 10GB)
                - activeFeatures (List[Dict[str, Any]]): List of active features for this service
            - isVerified (bool): Whether the account is verified
            - securityPinSet (bool): Whether security PIN is configured

    Raises:
        ValueError: If accountId is empty or not a string.
        AccountNotFoundError: If accountId is not found in the database.
    """
    if not isinstance(accountId, str) or not accountId.strip():
        raise ValueError('accountId must be a non-empty string.')
    
    account_details = utils.get_account(accountId)    
    
    if account_details is None:
        raise AccountNotFoundError(f"Account {accountId} not found in the database.")
    
    # Convert the raw data to Pydantic model for validation
    try:
        validated_model = CustomerAccountDetails(**account_details)
        return validated_model.model_dump(mode="json")
    except Exception as e:
        raise ValueError(f"Failed to validate account data: {str(e)}")


@tool_spec(
    input_model=UpdateAccountInformationInput,
    output_model=CustomerAccountDetails,
    description="""Updates customer account information including contact details, billing address, and communication preferences.
        
        This function allows modification of various aspects of a customer's account information.
        All fields in the requestBody are optional - only include the fields you want to update.
        Fields with None values will be ignored and not updated.""",
    error_model=[
        ErrorObject(ValueError, ['Raised if accountId is empty, not a string, account not found in database, or validation fails.']),
        ErrorObject(AccountNotFoundError, ['Raised if accountId is not found in the database.']),
        ErrorObject(InvalidEmailError, ['Raised if contactEmail is not a valid email address.'])
    ],
    spec={
        'name': 'update_account_information',
        'description': """ Updates customer account information including contact details, billing address, and communication preferences.
        
        This function allows modification of various aspects of a customer's account information.
        All fields in the requestBody are optional - only include the fields you want to update.
        Fields with None values will be ignored and not updated. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'accountId': {
                    'type': 'string',
                    'description': 'The unique identifier for the customer\'s account or phone number. Example: "ACC888777666" or "222-334-4556"'
                },
                'requestBody': {
                    'type': 'object',
                    'description': """ Dictionary containing the new information to be updated.
                    Only include the fields you want to change. Fields with None values will be ignored.
                    Supported fields: """,
                    'properties': {
                        'contactEmail': {
                            'type': 'string',
                            'description': 'New contact email address. Must be valid email format.',
                            'nullable': True
                        },
                        'contactPhone': {
                            'type': 'string',
                            'description': 'New contact phone number in any valid format (e.g., 555-123-4567, (555) 123-4567, 5551234567). Will be normalized.',
                            'nullable': True
                        },
                        'billingAddress': {
                            'type': 'object',
                            'description': 'New billing address information with fields:',
                            'properties': {
                                'recipientName': {
                                    'type': 'string',
                                    'description': 'Name for billing address',
                                    'nullable': True
                                },
                                'streetAddressLine1': {
                                    'type': 'string',
                                    'description': 'Primary street address',
                                    'nullable': True
                                },
                                'streetAddressLine2': {
                                    'type': 'string',
                                    'description': 'Secondary address line (apt, suite, etc.)',
                                    'nullable': True
                                },
                                'city': {
                                    'type': 'string',
                                    'description': 'City name',
                                    'nullable': True
                                },
                                'state': {
                                    'type': 'string',
                                    'description': 'State or province code',
                                    'nullable': True
                                },
                                'zipCode': {
                                    'type': 'string',
                                    'description': 'ZIP or postal code',
                                    'nullable': True
                                },
                                'country': {
                                    'type': 'string',
                                    'description': 'Country code (e.g., US, CA)',
                                    'nullable': True
                                }
                            },
                            'required': [],
                            'nullable': True
                        },
                        'serviceAddress': {
                            'type': 'object',
                            'description': 'New service installation address with fields:',
                            'properties': {
                                'recipientName': {
                                    'type': 'string',
                                    'description': 'Name for service installation address',
                                    'nullable': True
                                },
                                'streetAddressLine1': {
                                    'type': 'string',
                                    'description': 'Primary street address',
                                    'nullable': True
                                },
                                'streetAddressLine2': {
                                    'type': 'string',
                                    'description': 'Secondary address line (apt, suite, etc.)',
                                    'nullable': True
                                },
                                'city': {
                                    'type': 'string',
                                    'description': 'City name',
                                    'nullable': True
                                },
                                'state': {
                                    'type': 'string',
                                    'description': 'State or province code',
                                    'nullable': True
                                },
                                'zipCode': {
                                    'type': 'string',
                                    'description': 'ZIP or postal code',
                                    'nullable': True
                                },
                                'country': {
                                    'type': 'string',
                                    'description': 'Country code (e.g., US, CA)',
                                    'nullable': True
                                }
                            },
                            'required': [],
                            'nullable': True
                        },
                        'communicationPreferences': {
                            'type': 'object',
                            'description': 'New communication preferences with fields:',
                            'properties': {
                                'emailOptIn': {
                                    'type': 'boolean',
                                    'description': 'Whether customer wants email communications',
                                    'nullable': True
                                },
                                'smsOptIn': {
                                    'type': 'boolean',
                                    'description': 'Whether customer wants SMS communications',
                                    'nullable': True
                                }
                            },
                            'required': [],
                            'nullable': True
                        }
                    },
                    'required': []
                }
            },
            'required': [
                'accountId',
                'requestBody'
            ]
        },
        'response': {
            'type': 'object',
            'description': 'Dictionary showing the complete, updated state of the account including:',
            'properties': {
                'accountId': {
                    'type': 'string',
                    'description': "Customer's unique account identifier"
                },
                'customerName': {
                    'type': 'string',
                    'description': "Customer's full name"
                },
                'contactEmail': {
                    'type': 'string',
                    'description': 'Updated contact email address (unchanged if not provided)'
                },
                'contactPhone': {
                    'type': 'string',
                    'description': 'Updated contact phone number in any valid format (e.g., 555-123-4567, (555) 123-4567, 5551234567) (unchanged if not provided).'
                },
                'billingAddress': {
                    'type': 'object',
                    'description': 'Updated billing address information (unchanged if not provided)',
                    'properties': {
                        'recipientName': {
                            'type': 'string',
                            'description': 'Name for billing address'
                        },
                        'streetAddressLine1': {
                            'type': 'string',
                            'description': 'Primary street address'
                        },
                        'streetAddressLine2': {
                            'type': 'string',
                            'description': 'Secondary address line (apt, suite, etc.)',
                            'nullable': True
                        },
                        'city': {
                            'type': 'string',
                            'description': 'City name'
                        },
                        'state': {
                            'type': 'string',
                            'description': 'State or province code'
                        },
                        'zipCode': {
                            'type': 'string',
                            'description': 'ZIP or postal code'
                        },
                        'country': {
                            'type': 'string',
                            'description': 'Country code (e.g., US, CA)'
                        }
                    },
                    'required': [
                        'recipientName',
                        'streetAddressLine1',
                        'city',
                        'state',
                        'zipCode',
                        'country'
                    ]
                },
                'serviceAddress': {
                    'type': 'object',
                    'description': 'Service installation address (unchanged if not provided)',
                    'properties': {
                        'recipientName': {
                            'type': 'string',
                            'description': 'Name for service installation address'
                        },
                        'streetAddressLine1': {
                            'type': 'string',
                            'description': 'Primary street address'
                        },
                        'streetAddressLine2': {
                            'type': 'string',   
                            'description': 'Secondary address line (apt, suite, etc.)',
                            'nullable': True
                        },
                        'city': {
                            'type': 'string',
                            'description': 'City name'
                        },
                        'state': {
                            'type': 'string',
                            'description': 'State or province code'
                        },
                        'zipCode': {
                            'type': 'string',
                            'description': 'ZIP or postal code'
                        },
                        'country': {
                            'type': 'string',
                            'description': 'Country code (e.g., US, CA)'
                        }
                    },
                    'required': [
                        'recipientName',
                        'streetAddressLine1',
                        'city',
                        'state',
                        'zipCode',
                        'country'
                    ]
                },
                'communicationPreferences': {
                    'type': 'object',
                    'description': 'Updated communication preferences (unchanged if not provided)',
                    'properties': {
                        'emailOptIn': {
                            'type': 'boolean',
                            'description': 'Whether customer wants email communications'
                        },
                        'smsOptIn': {
                            'type': 'boolean',
                            'description': 'Whether customer wants SMS communications'
                        }
                    },
                    'required': [
                        'emailOptIn',
                        'smsOptIn'
                    ]
                },
                'devices': {
                    'type': 'array',
                    'description': 'List of devices on the account (unchanged)',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'deviceId': {
                                'type': 'string',
                                'description': 'Unique device identifier'
                            },
                            'deviceName': {
                                'type': 'string',
                                'description': 'Name of the device'
                            },
                            'lineNumber': {
                                'type': 'string',
                                'description': 'Phone number associated with the device'
                            },
                            'upgradeEligibilityDate': {
                                'type': 'string',
                                'description': 'Date when device becomes eligible for upgrade'
                            },
                            'paymentPlanActive': {
                                'type': 'boolean',
                                'description': 'Whether device has an active payment plan'
                            },
                            'paymentPlanRemainingMonths': {
                                'type': 'integer',
                                'description': 'Remaining months on payment plan'
                            }
                        },
                        'required': [
                            'deviceId',
                            'deviceName',
                            'lineNumber',
                            'upgradeEligibilityDate',
                            'paymentPlanActive',
                            'paymentPlanRemainingMonths'
                        ]
                    }
                },
                'services': {
                    'type': 'array',
                    'description': 'List of active service plans (unchanged)',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'serviceId': {
                                'type': 'string',
                                'description': 'Unique identifier for the service'
                            },
                            'planName': {
                                'type': 'string',
                                'description': 'Name of the service plan'
                            },
                            'planId': {
                                'type': 'string',
                                'description': 'Unique identifier for the plan'
                            },
                            'monthlyCost': {
                                'type': 'number',
                                'description': 'Monthly cost of the service'
                            },
                            'dataAllowance': {
                                'type': 'string',
                                'description': 'Data allowance for the service (e.g., Unlimited, 10GB)',
                                'nullable': True
                            },
                            'activeFeatures': {
                                'type': 'array',
                                'description': 'List of active features for this service',
                                'items': {
                                    'type': 'object',
                                    'properties': {
                                        'featureId': {
                                            'type': 'string',
                                            'description': 'Unique identifier for the feature'
                                        },
                                        'featureName': {
                                            'type': 'string',
                                            'description': 'Name of the feature'
                                        },
                                        'monthlyCost': {
                                            'type': 'number',
                                            'description': 'Monthly cost of the feature'
                                        }
                                    },
                                    'required': [
                                        'featureId', 
                                        'featureName', 
                                        'monthlyCost'
                                    ]
                                }
                            }
                        },
                        'required': [
                            'serviceId',
                            'planName',
                            'planId',
                            'monthlyCost',
                            'activeFeatures'
                        ]
                    }
                },
                'isVerified': {
                    'type': 'boolean',
                    'description': 'Whether the account is verified (unchanged)'
                },
                'securityPinSet': {
                    'type': 'boolean',
                    'description': 'Whether security PIN is configured (unchanged)'
                }
            },
            'required': [
                'accountId',
                'customerName',
                'contactEmail',
                'contactPhone',
                'billingAddress',
                'serviceAddress',
                'communicationPreferences',
                'devices',
                'services',
                'isVerified',
                'securityPinSet'
            ]
        }
    }
)
def update_account_information(
    accountId: str,
    requestBody: Dict[str, Union[str, Dict[str, Union[str, bool, None]]]],
) -> Dict[str, Any]:
    """
    Updates customer account information including contact details, billing address, and communication preferences.

    This function allows modification of various aspects of a customer's account information.
    All fields in the requestBody are optional - only include the fields you want to update.
    Fields with None values will be ignored and not updated.

    Args:
        accountId (str): The unique identifier for the customer's account or phone number. Example: "ACC888777666" or "222-334-4556"
        requestBody (Dict[str, Union[str, Dict[str, Union[str, bool, None]]]]): Dictionary containing the new information to be updated.
            Only include the fields you want to change. Fields with None values will be ignored.
            Supported fields:
            - contactEmail (Optional[str]): New contact email address. Must be valid email format.
            - contactPhone (Optional[str]): New contact phone number in any valid format (e.g., 555-123-4567, (555) 123-4567, 5551234567). Will be normalized.
            - billingAddress (Optional[Dict[str, Optional[str]]]): New billing address information with fields:
                - recipientName (Optional[str]): Name for billing address
                - streetAddressLine1 (Optional[str]): Primary street address
                - streetAddressLine2 (Optional[str]): Secondary address line (apt, suite, etc.)
                - city (Optional[str]): City name
                - state (Optional[str]): State or province code
                - zipCode (Optional[str]): ZIP or postal code
                - country (Optional[str]): Country code (e.g., US, CA)
            - serviceAddress (Optional[Dict[str, Optional[str]]]): New service installation address with fields:
                - recipientName (Optional[str]): Name for service installation address
                - streetAddressLine1 (Optional[str]): Primary street address
                - streetAddressLine2 (Optional[str]): Secondary address line (apt, suite, etc.)
                - city (Optional[str]): City name
                - state (Optional[str]): State or province code
                - zipCode (Optional[str]): ZIP or postal code
                - country (Optional[str]): Country code (e.g., US, CA)
            - communicationPreferences (Optional[Dict[str, Optional[bool]]]): New communication preferences with fields:
                - emailOptIn (Optional[bool]): Whether customer wants email communications
                - smsOptIn (Optional[bool]): Whether customer wants SMS communications

    Returns:
        Dict[str, Any]: Dictionary showing the complete, updated state of the account including:
            - accountId (str): Customer's unique account identifier
            - customerName (str): Customer's full name
            - contactEmail (str): Updated contact email address (unchanged if not provided)
            - contactPhone (str): Updated contact phone number in any valid format (e.g., 555-123-4567, (555) 123-4567, 5551234567) (unchanged if not provided).
            - billingAddress (Dict[str, Union[str, None]]): Updated billing address information (unchanged if not provided) with fields:
                - recipientName (str): Name for billing address
                - streetAddressLine1 (str): Primary street address
                - streetAddressLine2 (Optional[str]): Secondary address line (apt, suite, etc.)
                - city (str): City name
                - state (str): State or province code
                - zipCode (str): ZIP or postal code
                - country (str): Country code (e.g., US, CA)
            - serviceAddress (Dict[str, Union[str, None]]): Service installation address (unchanged if not provided) with fields:
                - recipientName (str): Name for service installation address
                - streetAddressLine1 (str): Primary street address
                - streetAddressLine2 (Optional[str]): Secondary address line (apt, suite, etc.)
                - city (str): City name
                - state (str): State or province code
                - zipCode (str): ZIP or postal code
                - country (str): Country code (e.g., US, CA)
            - communicationPreferences (Dict[str, bool]): Updated communication preferences (unchanged if not provided) with fields:
                - emailOptIn (bool): Whether customer wants email communications
                - smsOptIn (bool): Whether customer wants SMS communications
            - devices (List[Dict[str, Union[str, bool, int]]]): List of devices on the account with fields:
                - deviceId (str): Unique device identifier
                - deviceName (str): Name of the device
                - lineNumber (str): Phone number associated with the device
                - upgradeEligibilityDate (str): Date when device becomes eligible for upgrade
                - paymentPlanActive (bool): Whether device has an active payment plan
                - paymentPlanRemainingMonths (int): Remaining months on payment plan
            - services (List[Dict[str, Any]]): List of active service plans (unchanged) with fields:
                - serviceId (str): Unique identifier for the service
                - planName (str): Name of the service plan
                - planId (str): Unique identifier for the plan
                - monthlyCost (float): Monthly cost of the service
                - dataAllowance (Optional[str]): Data allowance for the service (e.g., Unlimited, 10GB)
                - activeFeatures (List[Dict[str, Any]]): List of active features for this service
            - isVerified (bool): Whether the account is verified (unchanged)
            - securityPinSet (bool): Whether security PIN is configured (unchanged)

    Raises:
        ValueError: If accountId is empty, not a string, account not found in database, or validation fails.
        AccountNotFoundError: If accountId is not found in the database.
        InvalidEmailError: If contactEmail is not a valid email address.
    """
    if not isinstance(accountId, str) or not accountId.strip():
        raise ValueError('accountId must be a non-empty string.')
    
    # Validate the request body using Pydantic model
    try:
        validated_request = AccountInformationUpdateInput(**requestBody)
    except Exception as e:
        raise ValueError(f"Invalid request body: {str(e)}")
    
    # Use utils to verify account exists
    account_details = utils.get_account(accountId)
    if account_details is None:
        raise AccountNotFoundError(f"Account {accountId} not found in the database.")
    
    # Convert to dict for utils functions
    request_dict = validated_request.model_dump(exclude_unset=True)
    actual_account_id = account_details["accountId"]
    
    # Validate email and phone if provided
    if "contactEmail" in request_dict and request_dict["contactEmail"] is not None:
        validate_email_util(request_dict["contactEmail"], "contactEmail")
    
    if "contactPhone" in request_dict and request_dict["contactPhone"] is not None:
        phone = request_dict["contactPhone"]
        if not is_phone_number_valid(phone):
            raise ValueError(f"The phone number '{phone}' is not valid.")
        # Normalize the phone number
        request_dict["contactPhone"] = normalize_phone_number(phone)
    
    # Use utils to update account
    utils.update_account(actual_account_id, request_dict)
    
    return get_customer_account_details(actual_account_id)


@tool_spec(
    input_model=CheckDeviceUpgradeEligibilityInput,
    output_model=DeviceUpgradeEligibility,
    description="""Checks if a specific device or line on an account is eligible for an upgrade.
        
        When to Use:
        - Use this function when a user asks "Can I upgrade my phone?", "Am I eligible
        for an upgrade?", or similar questions about a specific device or phone line.
        
        Eligibility Rules:
        - A device is eligible for upgrade if: the device has no active payment plan (paymentPlanActive=False) AND the device has a valid line number (lineNumber != "n/a")
        - A device is NOT eligible if: It has an active payment plan (paymentPlanActive=True) OR it has no line number (lineNumber="n/a")""",
    error_model=[
        ErrorObject(ValueError, ['Raised if accountId or identifier is empty/invalid, account not found, or device not found on account.']),
        ErrorObject(AccountNotFoundError, ['Raised if accountId is not found in the database.'])
    ],
    spec={
        'name': 'check_device_upgrade_eligibility',
        'description': """ Checks if a specific device or line on an account is eligible for an upgrade.
        
        When to Use:
        - Use this function when a user asks "Can I upgrade my phone?", "Am I eligible
        for an upgrade?", or similar questions about a specific device or phone line.
        
        Eligibility Rules:
        - A device is eligible for upgrade if: the device has no active payment plan (paymentPlanActive=False) AND the device has a valid line number (lineNumber != "n/a")
        - A device is NOT eligible if: It has an active payment plan (paymentPlanActive=True) OR it has no line number (lineNumber="n/a") """,
        'parameters': {
            'type': 'object',
            'properties': {
                'accountId': {
                    'type': 'string',
                    'description': """ The unique identifier for the customer's account or phone number. 
                    Example: "ACC123456789" or "222-334-4556" """
                },
                'identifier': {
                    'type': 'string',
                    'description': """ The phone number or device ID to check. Examples:
                    - For LINE_NUMBER: "555-123-4567"
                    - For DEVICE_ID: "DEV987654321" """
                },
                'identifierType': {
                    'type': 'string',
                    'description': """ Specifies the type of 
                    the identifier provided. Must be one of:
                    - "LINE_NUMBER": Use when searching by phone number
                    - "DEVICE_ID": Use when searching by device identifier """
                }
            },
            'required': [
                'accountId',
                'identifier',
                'identifierType'
            ]
        },
        'response': {
            'type': 'object',
            'description': 'Dictionary containing eligibility information:',
            'properties': {
                'isEligible': {
                    'type': 'boolean',
                    'description': 'Whether the device is eligible for upgrade'
                },
                'reason': {
                    'type': 'string',
                    'description': 'Explanation if not eligible',
                    'nullable': True
                },
                'remainingDevicePayments': {
                    'type': 'number',
                    'description': 'Remaining balance on payment plan',
                    'nullable': True
                },
                'eligibilityDate': {
                    'type': 'string',
                    'description': 'Date when device becomes eligible',
                    'nullable': True
                },
                'earlyUpgradeOptions': {
                    'type': 'string',
                    'description': 'Early upgrade options if available',
                    'nullable': True
                }
            },
            'required': [
                'isEligible'
            ]
        }
    }
)
def check_device_upgrade_eligibility(
    accountId: str,
    identifier: str,
    identifierType: Literal["LINE_NUMBER", "DEVICE_ID"],
) -> Dict[str, Any]:
    """
    Checks if a specific device or line on an account is eligible for an upgrade.

    When to Use:
    - Use this function when a user asks "Can I upgrade my phone?", "Am I eligible
    for an upgrade?", or similar questions about a specific device or phone line.

    Eligibility Rules:
    - A device is eligible for upgrade if: the device has no active payment plan (paymentPlanActive=False) AND the device has a valid line number (lineNumber != "n/a")
    - A device is NOT eligible if: It has an active payment plan (paymentPlanActive=True) OR it has no line number (lineNumber="n/a")

    Args:
        accountId (str): The unique identifier for the customer's account or phone number. 
            Example: "ACC123456789" or "222-334-4556"
        identifier (str): The phone number or device ID to check. Examples:
            - For LINE_NUMBER: "555-123-4567"
            - For DEVICE_ID: "DEV987654321"
        identifierType (Literal["LINE_NUMBER", "DEVICE_ID"]): Specifies the type of 
            the identifier provided. Must be one of:
            - "LINE_NUMBER": Use when searching by phone number
            - "DEVICE_ID": Use when searching by device identifier

    Returns:
        Dict[str, Any]: Dictionary containing eligibility information:
            - isEligible (bool): Whether the device is eligible for upgrade
            - reason (Optional[str]): Explanation if not eligible
            - remainingDevicePayments (Optional[float]): Remaining balance on payment plan
            - eligibilityDate (Optional[str]): Date when device becomes eligible
            - earlyUpgradeOptions (Optional[str]): Early upgrade options if available

    Raises:
        ValueError: If accountId or identifier is empty/invalid, account not found, 
            or device not found on account.
        AccountNotFoundError: If accountId is not found in the database.
    """
    if not isinstance(accountId, str) or not accountId.strip():
        raise ValueError('accountId must be a non-empty string.')
    if not isinstance(identifier, str) or not identifier.strip():
        raise ValueError('identifier must be a non-empty string.')

    if identifierType is None or identifierType.strip() == "":
        raise ValueError('identifierType must be a non-empty string.')

    allowed_identifier_types = [identifier_type.value for identifier_type in DeviceIdentifierType]
    if identifierType not in allowed_identifier_types:
        allowed_str = ", ".join([f"'{v}'" for v in allowed_identifier_types])
        raise ValueError(
            f"Parameter 'identifierType' has an invalid value '{identifierType}'. Allowed values are {allowed_str}."
        )
    
    
    # Validate phone number if identifierType is LINE_NUMBER
    if identifierType == "LINE_NUMBER":
        if not is_phone_number_valid(identifier):
            raise ValueError(f"The phone number '{identifier}' is not valid.")
        # Normalize the phone number for comparison
        identifier = normalize_phone_number(identifier)
    
    # Use utils to get account information
    account_information = utils.get_account(accountId)
    if account_information is None:
        raise AccountNotFoundError(f"Account {accountId} not found in the database.")
    
    devices = account_information.get("devices", [])
    for device in devices:
        device_matches = False
        
        if identifierType == "LINE_NUMBER":
            # Normalize the stored phone number for comparison
            stored_phone = device.get("lineNumber")
            if stored_phone:
                stored_phone_normalized = normalize_phone_number(stored_phone)
                device_matches = stored_phone_normalized == identifier
            else:
                device_matches = False
        elif identifierType == "DEVICE_ID":
            device_matches = device.get("deviceId") == identifier
        else:
            raise ValueError(f"Identifier type {identifierType} not supported.")
        
        if device_matches:
            if not device.get("paymentPlanActive") and device.get("lineNumber") != "n/a":
                # Create and validate the response using Pydantic model
                try:
                    validated_model = DeviceUpgradeEligibility(isEligible=True)
                    return validated_model.model_dump(mode="json")
                except Exception as e:
                    raise ValueError(f"Failed to create valid response: {str(e)}")
            else:
                # Create and validate the response using Pydantic model
                try:
                    ineligible_reason = "Device is not eligible for an upgrade because payment plan is active."
                    if not device.get("paymentPlanActive"):
                        ineligible_reason = "Device is not eligible for an upgrade because lineNumber is n/a."

                    validated_model = DeviceUpgradeEligibility(
                        isEligible=False,
                        reason=ineligible_reason,
                        remainingDevicePayments=device.get("paymentPlanRemainingMonths"),
                        eligibilityDate=device.get("upgradeEligibilityDate"),
                    )
                    return validated_model.model_dump(mode="json")
                except Exception as e:
                    raise ValueError(f"Failed to create valid response: {str(e)}")
    
    raise ValueError(f"Device with {identifierType} '{identifier}' not found on account.")


@tool_spec(
    input_model=ModifyServicePlanOrFeatureInput,
    output_model=ServiceModificationResponse,
    description="""Modifies a customer's service plan or adds/removes features from their plan.
        
        When to Use:
        - Use this tool after a user has explored their options and explicitly
        confirmed that they want to make a specific change to their services.
        - For 'CHANGE_PLAN': User says "Yes, switch me to the Unlimited Pro plan."
        - For 'ADD_FEATURE': User says "Okay, please add the international calling
        pass."
        - For 'REMOVE_FEATURE': User says "I don't need the hotspot feature anymore,
        please remove it." """,
    error_model=[
        ErrorObject(ValueError, ['Raised if accountId or itemId is empty/invalid, account not found, plan not found, or invalid action type.']),
        ErrorObject(AccountNotFoundError, ['Raised if accountId is not found in the database.']),
        ErrorObject(ActionNotSupportedError, ['Raised if action is not supported.']),
        ErrorObject(ServicePlanNotFoundError, ['Raised if currentPlanId is not found in the account.'])
    ],
    spec={
        'name': 'modify_service_plan_or_feature',
        'description': """ Modifies a customer's service plan or adds/removes features from their plan.
        
        When to Use:
        - Use this tool after a user has explored their options and explicitly
        confirmed that they want to make a specific change to their services.
        - For 'CHANGE_PLAN': User says "Yes, switch me to the Unlimited Pro plan."
        - For 'ADD_FEATURE': User says "Okay, please add the international calling
        pass."
        - For 'REMOVE_FEATURE': User says "I don't need the hotspot feature anymore,
        please remove it." """,
        'parameters': {
            'type': 'object',
            'properties': {
                'accountId': {
                    'type': 'string',
                    'description': """ The unique identifier for the customer's account or phone number. 
                    Example: "ACC123456789" or "222-334-4556" """
                },
                'action': {
                    'type': 'string',
                    'description': """ The type of modification to perform:
                    - "CHANGE_PLAN": Replaces current plan with a new one specified in itemId.
                    - "ADD_FEATURE": Adds a feature specified in itemId to the current plan.
                    - "REMOVE_FEATURE": Removes a feature specified in itemId. """
                },
                'itemId': {
                    'type': 'string',
                    'description': """ The unique identifier for the plan or feature being actioned. 
                    Examples:
                    - For a plan: "PLAN_UNL_PRO"
                    - For a feature: "FEAT_INTL_CALL" """
                },
                'currentPlanId': {
                    'type': 'string',
                    'description': """ The ID of the customer's current plan to ensure the correct plan is being replaced or modified. 
                    Example: "PLAN_UNL_PLUS" """
                },
                'customerConfirmationText': {
                    'type': 'string',
                    'description': 'A summary of the change that the user has explicitly agreed to. Used for logging and auditing purposes.',
                    'nullable': True
                }
            },
            'required': [
                'accountId',
                'action',
                'itemId',
                'currentPlanId'
            ]
        },
        'response': {
            'type': 'object',
            'description': 'Dictionary confirming the modification:',
            'properties': {
                'status': {
                    'type': 'string',
                    'description': 'Success status of the operation'
                },
                'message': {
                    'type': 'string',
                    'description': 'Human-readable confirmation message'
                },
                'orderId': {
                    'type': 'string',
                    'description': 'Unique order identifier for tracking'
                },
                'effectiveDate': {
                    'type': 'string',
                    'description': 'Date when changes take effect'
                },
                'nextBillImpactEstimate': {
                    'type': 'string',
                    'description': 'Estimated impact on next bill'
                }
            },
            'required': [
                'status',
                'message',
                'orderId',
                'effectiveDate',
                'nextBillImpactEstimate'
            ]
        }
    }
)
def modify_service_plan_or_feature(
    accountId: str,
    action: Literal["CHANGE_PLAN", "ADD_FEATURE", "REMOVE_FEATURE"],
    itemId: str,
    currentPlanId: str,
    customerConfirmationText: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Modifies a customer's service plan or adds/removes features from their plan.

    When to Use:
    - Use this tool after a user has explored their options and explicitly
    confirmed that they want to make a specific change to their services.
    - For 'CHANGE_PLAN': User says "Yes, switch me to the Unlimited Pro plan."
    - For 'ADD_FEATURE': User says "Okay, please add the international calling
    pass."
    - For 'REMOVE_FEATURE': User says "I don't need the hotspot feature anymore,
    please remove it."

    Args:
        accountId (str): The unique identifier for the customer's account or phone number. 
            Example: "ACC123456789" or "222-334-4556"
        action (Literal["CHANGE_PLAN", "ADD_FEATURE", "REMOVE_FEATURE"]): The type of modification to perform:
            - "CHANGE_PLAN": Replaces current plan with a new one specified in itemId.
            - "ADD_FEATURE": Adds a feature specified in itemId to the current plan.
            - "REMOVE_FEATURE": Removes a feature specified in itemId.
        itemId (str): The unique identifier for the plan or feature being actioned. 
            Examples:
            - For a plan: "PLAN_UNL_PRO"
            - For a feature: "FEAT_INTL_CALL"
        currentPlanId (str): The ID of the customer's current plan to ensure the correct plan is being replaced or modified. 
            Example: "PLAN_UNL_PLUS"
        customerConfirmationText (Optional[str]): A summary of the change that the user has explicitly agreed to. Used for logging and auditing purposes.

    Returns:
        Dict[str, Any]: Dictionary confirming the modification:
            - status (str): Success status of the operation
            - message (str): Human-readable confirmation message
            - orderId (str): Unique order identifier for tracking
            - effectiveDate (str): Date when changes take effect
            - nextBillImpactEstimate (str): Estimated impact on next bill

    Raises:
        ValueError: If accountId or itemId is empty/invalid, account not found, 
            plan not found, or invalid action type.
        AccountNotFoundError: If accountId is not found in the database.
        ActionNotSupportedError: If action is not supported.
        ServicePlanNotFoundError: If currentPlanId is not found in the account.
    """
    
    if not isinstance(accountId, str) or not accountId.strip():
        raise ValueError('accountId must be a non-empty string.')
    if not isinstance(itemId, str) or not itemId.strip():
        raise ValueError('itemId must be a non-empty string.')
    if not isinstance(currentPlanId, str) or not currentPlanId.strip():
        raise ValueError('currentPlanId must be a non-empty string.')
    if action is None or action.strip() == "":
        raise ValueError('action must be a non-empty string.')

    allowed_actions = [action.value for action in ServiceModificationAction]
    if action not in allowed_actions:
        allowed_str = ", ".join([f"'{v}'" for v in allowed_actions])
        raise ValueError(
            f"Parameter 'action' has an invalid value '{action}'. Allowed values are {allowed_str}."
        )

    # Use utils to verify account exists
    account_details = utils.get_account(accountId)
    if account_details is None:
        raise AccountNotFoundError(f"Account {accountId} not found in the database.")
    
    account_services = account_details["services"]
    actual_account_id = account_details["accountId"]

    # For action, find the specific plan to replace using currentPlanId
    service_to_modify = next(
        (s for s in account_services if s["planId"] == currentPlanId), None
    )
    if service_to_modify is None:
        raise ServicePlanNotFoundError(f"Plan {currentPlanId} not found in the account.")
    
    service_index = account_services.index(service_to_modify)
    
    if action == "CHANGE_PLAN":
        
        # Get new plan information
        item_info = utils.get_service_plan(itemId)
        if item_info is None:
            raise ValueError(f"Item {itemId} not found in the database.")
        if item_info["type"] != "PLAN":
            raise ValueError(f"Item {itemId} is not a plan.")
        
        service_to_modify.update({
            "planName": item_info["name"],
            "planId": item_info["id"],
            "monthlyCost": item_info["monthlyCost"],
            "dataAllowance": item_info["dataAllowance"],
            "activeFeatures": [],  # Reset features when changing plan
        })
        message = f"Your plan has been successfully changed to {item_info['name']}"
        bill_impact = f"${item_info['monthlyCost']} will be your next bill."
        
        utils.update_service_plan(actual_account_id, service_index, service_to_modify)
        
    elif action == "ADD_FEATURE":
        # For ADD_FEATURE, add to the first/primary service plan on the account
        if not account_services:
            raise ValueError("No service plans found on the account to add feature to.")

        # Get feature information
        item_info = utils.get_service_plan(itemId)
        if item_info is None:
            raise ValueError(f"Item {itemId} not found in the database.")
        if item_info["type"] != "FEATURE_ADDON":
            raise ValueError(f"Item {itemId} is not an add-on feature.")
        
        feature_to_add = {
            "featureId": item_info["id"],
            "featureName": item_info["name"],
            "monthlyCost": item_info["monthlyCost"],
        }
        if "activeFeatures" not in service_to_modify or not isinstance(service_to_modify["activeFeatures"], list):
            service_to_modify["activeFeatures"] = []
        # Replace if already present
        replaced = False
        for idx, existing in enumerate(service_to_modify["activeFeatures"]):
            if existing.get("featureId") == item_info["id"]:
                service_to_modify["activeFeatures"][idx] = feature_to_add
                replaced = True
                break
        if not replaced:
            service_to_modify["activeFeatures"].append(feature_to_add)
        message = f"Feature {item_info['name']} has been successfully added to your plan."
        bill_impact = f"${item_info['monthlyCost']} will be added to your next bill."
        
        utils.update_service_plan(actual_account_id, service_index, service_to_modify)
        
    elif action == "REMOVE_FEATURE":
        # For REMOVE_FEATURE, search through all services to find and remove the feature
        feature_found = False
        removed_feature_cost = 0
        
        active_features = service_to_modify.get("activeFeatures", [])
        # remove by id
        for idx, feat in enumerate(active_features):
            if feat.get("featureId") == itemId:
                removed_feature_cost = feat.get("monthlyCost", 0)
                del service_to_modify["activeFeatures"][idx]
                utils.update_service_plan(actual_account_id, service_index, service_to_modify)
                feature_found = True
                break
        
        if not feature_found:
            raise ValueError(f"Feature {itemId} was not found for the plan {currentPlanId} and could not be removed.")
        
        message = f"Feature {itemId} has been successfully removed from your plan."
        bill_impact = f"${removed_feature_cost} will be deducted from your next bill."
        
    else:
        raise ActionNotSupportedError(f"Action {action} not supported.")

    # Create and validate the response using Pydantic model
    try:
        order = utils.create_order(account_details['accountId'], action, message)
        validated_model = ServiceModificationResponse(
            status="Success",
            message=message,
            orderId=order['orderId'],
            effectiveDate=order['estimatedCompletionDate'], 
            nextBillImpactEstimate=bill_impact,
        )
        return validated_model.model_dump(mode="json")
    except Exception as e:
        raise ValueError(f"Failed to create valid response: {str(e)}")


@tool_spec(
    input_model=QueryAvailablePlansAndFeaturesInput,
    output_model=KnowledgeBaseQueryResponse,
    description="""Searches a knowledge base for information about available service plans and features.
        
        When to Use:
        - Use this function when the user asks general, informational questions about
          products or services that you don't have structured data for.
        - Examples: "What international plans do you have?", "How much does the
          hotspot feature cost?", "What are the benefits of the Unlimited Pro plan?".
        - Do NOT use this to get information about a specific customer's current plan;
          use get_customer_account_details() for that.""",
    error_model=[
        ErrorObject(ValueError, ['Raised if query is empty or not a string.'])
    ],
    spec={
        'name': 'query_available_plans_and_features',
        'description': """ Searches a knowledge base for information about available service plans and features.
        
        When to Use:
        - Use this function when the user asks general, informational questions about
          products or services that you don't have structured data for.
        - Examples: "What international plans do you have?", "How much does the
          hotspot feature cost?", "What are the benefits of the Unlimited Pro plan?".
        - Do NOT use this to get information about a specific customer's current plan;
          use get_customer_account_details() for that. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The user's question, phrased as a clear, specific search query.
                    Examples:
                    - "details of Unlimited Pro plan data allowance"
                    - "cost of international calling pass feature"
                    - "what plans include mobile hotspot" """
                }
            },
            'required': [
                'query'
            ]
        },
        'response': {
            'type': 'object',
            'description': 'Dictionary containing search results:',
            'properties': {
                'answer': {
                    'type': 'string',
                    'description': 'Human-readable answer to the query',
                    'nullable': True
                },
                'snippets': {
                    'type': 'array',
                    'description': 'Supporting information snippets, each containing:',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'text': {
                                'type': 'string',
                                'description': 'Snippet content',
                                'nullable': True
                            },
                            'title': {
                                'type': 'string',
                                'description': 'Source title',
                                'nullable': True
                            },
                            'uri': {
                                'type': 'string',
                                'description': 'Reference URL',
                                'nullable': True
                            }
                        },
                        'required': []
                    }
                }
            },
            'required': [
                'snippets'
            ]
        }
    }
)
def query_available_plans_and_features(
    query: str,
) -> Dict[str, Any]:
    """
    Searches a knowledge base for information about available service plans and features.

    When to Use:
    - Use this function when the user asks general, informational questions about
      products or services that you don't have structured data for.
    - Examples: "What international plans do you have?", "How much does the
      hotspot feature cost?", "What are the benefits of the Unlimited Pro plan?".
    - Do NOT use this to get information about a specific customer's current plan;
      use get_customer_account_details() for that.

    Args:
        query (str): The user's question, phrased as a clear, specific search query.
            Examples:
            - "details of Unlimited Pro plan data allowance"
            - "cost of international calling pass feature"
            - "what plans include mobile hotspot"

    Returns:
        Dict[str, Any]: Dictionary containing search results:
            - answer (Optional[str]): Human-readable answer to the query
            - snippets (List[Dict[str, Optional[str]]]): Supporting information snippets, each containing:
                - text (Optional[str]): Snippet content
                - title (Optional[str]): Source title
                - uri (Optional[str]): Reference URL

    Raises:
        ValueError: If query is empty or not a string.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError('Query must be a non-empty string.')
    
    if DB["use_real_datastore"]:
        response = utils.query_plans_and_features_infobot(query)
        validated_model = KnowledgeBaseQueryResponse(
            answer=response.get("answer"),
            snippets=[
                KnowledgeBaseSnippet(
                    text=snippet.get("text"),
                    title=snippet.get("title"),
                    uri=snippet.get("uri"),
                )
                for snippet in response.get("snippets", [])
            ],
        )
        return validated_model.model_dump(mode="json")

    matching_plans = utils.search_plans_by_query(query)

    if matching_plans:
        answer_parts = []
        snippets = []
        
        for plan in matching_plans:
            plan_info = f"{plan['name']}: {plan['description']} - ${plan['monthlyCost']}/month"
            answer_parts.append(plan_info)
            
            snippets.append(KnowledgeBaseSnippet(
                text=plan['description'],
                title=plan['name'],
                uri=plan.get('termsAndConditionsUrl', 'https://example.com/terms')
            ))
        
        answer = "Here are the available plans and features that match your query:\n" + "\n".join(answer_parts)
    else:
        answer = "I don't have specific information about that plan or feature in our current offerings."
        snippets = []
    
    # Create and validate the response using Pydantic model
    try:
        validated_model = KnowledgeBaseQueryResponse(
            answer=answer,
            snippets=snippets,
        )
        return validated_model.model_dump(mode="json")
    except Exception as e:
        raise ValueError(f"Failed to create valid response: {str(e)}")


@tool_spec(
    input_model=QueryAccountOrdersInput,
    output_model=KnowledgeBaseQueryResponse,
    description="""Searches a customer's order history in a knowledge base.
        
        When to Use:
        - Use this function when a user asks about the status of a recent order, their
          order history, or details about a past purchase.
        - You MUST use the `filter` parameter to scope the search to the correct
        account.""",
    error_model=[
        ErrorObject(ValueError, ['Raised if query or filter is empty or not a string.'])
    ],
    spec={
        'name': 'query_account_orders',
        'description': """ Searches a customer's order history in a knowledge base.
        
        When to Use:
        - Use this function when a user asks about the status of a recent order, their
          order history, or details about a past purchase.
        - You MUST use the `filter` parameter to scope the search to the correct
        account. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': """ The user's question about their orders. Examples:
                    - "What was the shipping status of my most recent order?"
                    - "How much did I pay for the phone I bought in May?"
                    - "Show me my order history for the past 3 months" """
                },
                'filter': {
                    'type': 'string',
                    'description': """ An expression to filter the search to the specific customer's
                    account. The format MUST be "accountId='<customer_account_id>'". 
                    Example: "accountId='ACC123456789'" """
                }
            },
            'required': [
                'query',
                'filter'
            ]
        },
        'response': {
            'type': 'object',
            'description': 'Dictionary containing order search results:',
            'properties': {
                'answer': {
                    'type': 'string',
                    'description': 'Response about the order history',
                    'nullable': True
                },
                'snippets': {
                    'type': 'array',
                    'description': 'Supporting order information',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'text': {
                                'type': 'string',
                                'description': 'Snippet content',
                                'nullable': True
                            },
                            'title': {
                                'type': 'string',
                                'description': 'Source title',
                                'nullable': True
                            },
                            'uri': {
                                'type': 'string',
                                'description': 'Reference URL',
                                'nullable': True
                            }
                        },
                        'required': []
                    }
                }
            },
            'required': [
                'snippets'
            ]
        }
    }
)
def query_account_orders(
    query: str,
    filter: str,
) -> Dict[str, Any]:
    """
    Searches a customer's order history in a knowledge base.

    When to Use:
    - Use this function when a user asks about the status of a recent order, their
      order history, or details about a past purchase.
    - You MUST use the `filter` parameter to scope the search to the correct
    account.

    Args:
        query (str): The user's question about their orders. Examples:
            - "What was the shipping status of my most recent order?"
            - "How much did I pay for the phone I bought in May?"
            - "Show me my order history for the past 3 months"
        filter (str): An expression to filter the search to the specific customer's
            account. The format MUST be "accountId='<customer_account_id>'". 
            Example: "accountId='ACC123456789'"

    Returns:
        Dict[str, Any]: Dictionary containing order search results:
            - answer (Optional[str]): Response about the order history
            - snippets (List[Dict[str, Optional[str]]]): Supporting order information with fields:
                - text (Optional[str]): Snippet content
                - title (Optional[str]): Source title
                - uri (Optional[str]): Reference URL

    Raises:
        ValueError: If query or filter is empty or not a string.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError('query must be a non-empty string.')
    if not isinstance(filter, str) or not filter.strip():
        raise ValueError('filter must be a non-empty string.')
    
    # Validate filter format
    if not filter.startswith("accountId='") or not filter.endswith("'"):
        raise ValueError("filter must be in format 'accountId='<customer_account_id>''")
    
    if DB["use_real_datastore"]:
        updated_query = f"{filter}: {query}"
        response = utils.query_account_orders_infobot(updated_query)
        validated_model = KnowledgeBaseQueryResponse(
            answer=response.get("answer"),
            snippets=[
                KnowledgeBaseSnippet(
                    text=snippet.get("text"),
                    title=snippet.get("title"),
                    uri=snippet.get("uri"),
                )
                for snippet in response.get("snippets", [])
            ],
        )
        return validated_model.model_dump(mode="json")
    # Extract account ID from filter
    account_id = filter[11:-1]  # Remove "accountId='" from start and "'" from end

    matching_orders = utils.search_account_orders_by_query(query, account_id)
    if matching_orders:
        answer_parts = []
        snippets = []
        for order in matching_orders[:3]:
            order_info = f"{order.get('orderId', '')}: {order.get('status', '')} - {order.get('statusDescription', '')}"
            answer_parts.append(order_info)
            snippets.append(KnowledgeBaseSnippet(
                text=order.get('statusDescription'),
                title=order.get('orderId'),
                uri=order.get('termsAndConditionsUrl', 'https://example.com/terms')
            ))
        answer = "Here are the available orders that match your query:\n" + "\n".join(answer_parts)
    else:
        answer = "I don't have access to this order history information."
        snippets = []
    
    # Create and validate the response using Pydantic model
    try:
        validated_model = KnowledgeBaseQueryResponse(
            answer=answer,
            snippets=snippets,
        )
        return validated_model.model_dump(mode="json")
    except Exception as e:
        raise ValueError(f"Failed to create valid response: {str(e)}")


@tool_spec(
    input_model=EscalateInput,
    output_model=TerminalResponse,
    description="""Use this function to transfer the user to a human agent.
        
        This is a terminal action and will end your conversation.
        
        When to Use:
        - The user explicitly asks to speak to a human, manager, or representative.
        - The user's request is outside of your capabilities (e.g., closing an
          account, handling sensitive personal information, or resolving a complex
          technical issue you are not trained for).
        - The user is expressing extreme frustration or anger that you cannot resolve.""",
    error_model=[
        ErrorObject(ValueError, ['Raised if the reason is empty or not a string.'])
    ],
    spec={
        'name': 'escalate',
        'description': """ Use this function to transfer the user to a human agent.
        
        This is a terminal action and will end your conversation.
        
        When to Use:
        - The user explicitly asks to speak to a human, manager, or representative.
        - The user's request is outside of your capabilities (e.g., closing an
          account, handling sensitive personal information, or resolving a complex
          technical issue you are not trained for).
        - The user is expressing extreme frustration or anger that you cannot resolve. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'reason': {
                    'type': 'string',
                    'description': """ A clear and concise explanation for the escalation. This reason
                    will be logged and shown to the human agent. Examples:
                    - "The user wants to file a formal complaint about their billing"
                    - "The user is requesting account closure which requires human approval"
                    - "The user is experiencing technical issues beyond my capabilities" """
                }
            },
            'required': [
                'reason'
            ]
        },
        'response': {
            'type': 'object',
            'description': 'Dictionary containing termination details:',
            'properties': {
                'action': {
                    'type': 'string',
                    'description': 'The action type ("escalate")'
                },
                'reason': {
                    'type': 'string',
                    'description': 'The provided escalation reason'
                },
                'status': {
                    'type': 'string',
                    'description': 'Status message for the user'
                }
            },
            'required': [
                'action',
                'reason',
                'status'
            ]
        }
    }
)
def escalate(reason: str) -> Dict[str, str]:
    """
    Use this function to transfer the user to a human agent.

    This is a terminal action and will end your conversation.

    When to Use:
    - The user explicitly asks to speak to a human, manager, or representative.
    - The user's request is outside of your capabilities (e.g., closing an
      account, handling sensitive personal information, or resolving a complex
      technical issue you are not trained for).
    - The user is expressing extreme frustration or anger that you cannot resolve.

    Args:
        reason (str): A clear and concise explanation for the escalation. This reason
            will be logged and shown to the human agent. Examples:
            - "The user wants to file a formal complaint about their billing"
            - "The user is requesting account closure which requires human approval"
            - "The user is experiencing technical issues beyond my capabilities"

    Returns:
        Dict[str, str]: Dictionary containing termination details:
            - action (str): The action type ("escalate")
            - reason (str): The provided escalation reason
            - status (str): Status message for the user

    Raises:
        ValueError: If the reason is empty or not a string.
    """
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError('Reason must be a non-empty string.')
    
    if '_end_of_conversation_status' not in DB:
        DB['_end_of_conversation_status'] = {}
    
    DB['_end_of_conversation_status']['escalate'] = {
        "reason": reason,
        "action": "escalate",
        "status": "You will be connected to a human agent shortly.",
    }
    
    # Create and validate the response using Pydantic model
    try:
        validated_model = TerminalResponse(
            action='escalate',
            reason=reason,
            status='You will be connected to a human agent shortly.',
        )
        return validated_model.model_dump(mode="json")
    except Exception as e:
        raise ValueError(f"Failed to create valid response: {str(e)}")


@tool_spec(
    input_model=FailInput,
    output_model=TerminalResponse,
    description="""End conversation when request is unfulfillable after multiple attempts.
        
        Use this function to gracefully end the conversation when you are unable to
        understand or fulfill the user's request after multiple attempts. This is a
        terminal action.
        
        When to Use:
        - Only after you have tried to understand the user at least twice and are
          still failing.
        - Use this if you are stuck in a loop of not understanding the user's intent.
        - Do NOT use this if the user is frustrated; use escalate() instead.""",
    error_model=[
        ErrorObject(ValueError, ['Raised if the reason is empty or not a string.'])
    ],
    spec={
        'name': 'fail',
        'description': """ End conversation when request is unfulfillable after multiple attempts.
        
        Use this function to gracefully end the conversation when you are unable to
        understand or fulfill the user's request after multiple attempts. This is a
        terminal action.
        
        When to Use:
        - Only after you have tried to understand the user at least twice and are
          still failing.
        - Use this if you are stuck in a loop of not understanding the user's intent.
        - Do NOT use this if the user is frustrated; use escalate() instead. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'reason': {
                    'type': 'string',
                    'description': """ A clear and concise internal-facing explanation for why the task
                    failed. This is used for logging and improving the agent. Examples:
                    - "After three attempts, I could not understand the user's request"
                    - "User provided unclear instructions and did not respond to clarification"
                    - "Unable to parse the user's intent from their messages" """
                }
            },
            'required': [
                'reason'
            ]
        },
        'response': {
            'type': 'object',
            'description': 'Dictionary containing termination details:',
            'properties': {
                'action': {
                    'type': 'string',
                    'description': 'The action type ("fail")'
                },
                'reason': {
                    'type': 'string',
                    'description': 'The provided failure reason'
                },
                'status': {
                    'type': 'string',
                    'description': 'Apologetic status message for the user'
                }
            },
            'required': [
                'action',
                'reason',
                'status'
            ]
        }
    }
)
def fail(reason: str) -> Dict[str, str]:
    """
    End conversation when request is unfulfillable after multiple attempts.

    Use this function to gracefully end the conversation when you are unable to
    understand or fulfill the user's request after multiple attempts. This is a
    terminal action.

    When to Use:
    - Only after you have tried to understand the user at least twice and are
      still failing.
    - Use this if you are stuck in a loop of not understanding the user's intent.
    - Do NOT use this if the user is frustrated; use escalate() instead.

    Args:
        reason (str): A clear and concise internal-facing explanation for why the task
            failed. This is used for logging and improving the agent. Examples:
            - "After three attempts, I could not understand the user's request"
            - "User provided unclear instructions and did not respond to clarification"
            - "Unable to parse the user's intent from their messages"

    Returns:
        Dict[str, str]: Dictionary containing termination details:
            - action (str): The action type ("fail")
            - reason (str): The provided failure reason
            - status (str): Apologetic status message for the user

    Raises:
        ValueError: If the reason is empty or not a string.
    """
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError('Reason must be a non-empty string.')
    
    if '_end_of_conversation_status' not in DB:
        DB['_end_of_conversation_status'] = {}
    
    DB['_end_of_conversation_status']['fail'] = {
        "reason": reason,
        "action": "fail",
        "status": "I'm sorry, I'm unable to help with that at the moment. Please try again later.",
    }
    
    # Create and validate the response using Pydantic model
    try:
        validated_model = TerminalResponse(
            action='fail',
            reason=reason,
            status="I'm sorry, I'm unable to help with that at the moment. Please try again later.",
        )
        return validated_model.model_dump(mode="json")
    except Exception as e:
        raise ValueError(f"Failed to create valid response: {str(e)}")


@tool_spec(
    input_model=CancelInput,
    output_model=TerminalResponse,
    description="""Cancel task and end conversation when the user asks to stop.
        
        Use this function to cancel the current task and end the conversation when
        the user explicitly states they do not want to proceed. This is a terminal
        action.
        
        When to Use:
        - The user says "never mind", "I don't want to do this anymore", "stop", or
          "cancel".""",
    error_model=[
        ErrorObject(ValueError, ['Raised if the reason is empty or not a string.'])
    ],
    spec={
        'name': 'cancel',
        'description': """ Cancel task and end conversation when the user asks to stop.
        
        Use this function to cancel the current task and end the conversation when
        the user explicitly states they do not want to proceed. This is a terminal
        action.
        
        When to Use:
        - The user says "never mind", "I don't want to do this anymore", "stop", or
          "cancel". """,
        'parameters': {
            'type': 'object',
            'properties': {
                'reason': {
                    'type': 'string',
                    'description': """ A clear and concise summary of why the task was canceled, 
                    based on the user's request. Examples:
                    - "The user stated they did not have their account information ready"
                    - "The user changed their mind and no longer wants to proceed"
                    - "The user asked to cancel the current operation" """
                }
            },
            'required': [
                'reason'
            ]
        },
        'response': {
            'type': 'object',
            'description': 'Dictionary containing termination details:',
            'properties': {
                'action': {
                    'type': 'string',
                    'description': 'The action type ("cancel")'
                },
                'reason': {
                    'type': 'string',
                    'description': 'The provided cancellation reason'
                },
                'status': {
                    'type': 'string',
                    'description': 'Confirmation message for the user'
                }
            },
            'required': [
                'action',
                'reason',
                'status'
            ]
        }
    }
)
def cancel(reason: str) -> Dict[str, str]:
    """
    Cancel task and end conversation when the user asks to stop.

    Use this function to cancel the current task and end the conversation when
    the user explicitly states they do not want to proceed. This is a terminal
    action.

    When to Use:
    - The user says "never mind", "I don't want to do this anymore", "stop", or
      "cancel".

    Args:
        reason (str): A clear and concise summary of why the task was canceled, 
            based on the user's request. Examples:
            - "The user stated they did not have their account information ready"
            - "The user changed their mind and no longer wants to proceed"
            - "The user asked to cancel the current operation"

    Returns:
        Dict[str, str]: Dictionary containing termination details:
            - action (str): The action type ("cancel")
            - reason (str): The provided cancellation reason
            - status (str): Confirmation message for the user

    Raises:
        ValueError: If the reason is empty or not a string.
    """
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError('Reason must be a non-empty string.')
    
    if '_end_of_conversation_status' not in DB:
        DB['_end_of_conversation_status'] = {}
    
    DB['_end_of_conversation_status']['cancel'] = {
        "reason": reason,
        "action": "cancel",
        "status": "Okay, I have canceled this request.",
    }
    
    # Create and validate the response using Pydantic model
    try:
        validated_model = TerminalResponse(
            action='cancel',
            reason=reason,
            status='Okay, I have canceled this request.',
        )
        return validated_model.model_dump(mode="json")
    except Exception as e:
        raise ValueError(f"Failed to create valid response: {str(e)}")