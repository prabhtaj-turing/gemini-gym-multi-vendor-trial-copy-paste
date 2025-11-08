from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum

# ---------------------------
# Enum Types
# ---------------------------


class DeviceIdentifierType(str, Enum):
    LINE_NUMBER = "LINE_NUMBER"
    DEVICE_ID = "DEVICE_ID"


class ServiceModificationAction(str, Enum):
    CHANGE_PLAN = "CHANGE_PLAN"
    ADD_FEATURE = "ADD_FEATURE"
    REMOVE_FEATURE = "REMOVE_FEATURE"


# ---------------------------
# Core API Models
# ---------------------------

class StrictBaseModel(BaseModel):
    class Config:
        extra = "forbid"

class Address(StrictBaseModel):
    recipientName: str = Field(
        ...,
        description="Name of the recipient at this address.",
        min_length=1,
        max_length=200
    )
    streetAddressLine1: str = Field(
        ...,
        description="Primary street address line.",
        min_length=1,
        max_length=200
    )
    streetAddressLine2: Optional[str] = Field(
        None,
        description="Secondary street address line (apartment, suite, etc.).",
        max_length=200
    )
    city: str = Field(
        ...,
        description="City name.",
        min_length=1,
        max_length=100
    )
    state: str = Field(
        ...,
        description="State or province code.",
        min_length=2,
        max_length=10
    )
    zipCode: str = Field(
        ...,
        description="ZIP or postal code.",
        min_length=1,
        max_length=20
    )
    country: str = Field(
        ...,
        description="Country code or name.",
        min_length=2,
        max_length=50
    )


class CommunicationPreferences(StrictBaseModel):
    emailOptIn: bool = Field(
        ...,
        description="Whether the customer wants to receive email communications."
    )
    smsOptIn: bool = Field(
        ...,
        description="Whether the customer wants to receive SMS communications."
    )


class Device(StrictBaseModel):
    deviceId: str = Field(
        ...,
        description="Unique device identifier",
        min_length=1,
        max_length=50
    )
    deviceName: str = Field(
        ...,
        description="Name of the device",
        min_length=1,
        max_length=200
    )
    lineNumber: str = Field(
        ...,
        description="Phone number associated with the device",
        min_length=1,
        max_length=50
    )
    upgradeEligibilityDate: str = Field(
        ...,
        description="Date when device becomes eligible for upgrade",
        min_length=1,
        max_length=50
    )
    paymentPlanActive: bool = Field(
        ...,
        description="Whether device has an active payment plan",
    )
    paymentPlanRemainingMonths: int = Field(
        ...,
        description="Remaining months on payment plan",
        ge=0
    )


class Order(BaseModel):
    orderId: str
    status: str
    orderDate: str
    accountId: str
    estimatedCompletionDate: str
    orderType: str
    statusDescription: str


class ActiveFeature(StrictBaseModel):
    featureId: str = Field(
        ...,
        description="Unique identifier for the feature.",
        min_length=1,
        max_length=50
    )
    featureName: str = Field(
        ...,
        description="Name of the feature.",
        min_length=1,
        max_length=200
    )
    monthlyCost: float = Field(
        ...,
        description="Monthly cost of the feature.",
        ge=0.0
    )


class ServicePlan(StrictBaseModel):
    serviceId: str = Field(
        ...,
        description="Unique identifier for the service.",
    )
    planName: str = Field(
        ...,
        description="Name of the service plan.",
    )
    planId: str = Field(
        ...,
        description="Unique identifier for the plan.",
    )
    monthlyCost: float = Field(
        ...,
        description="Monthly cost of the service.",
        ge=0.0
    )
    dataAllowance: Optional[str] = Field(
        None,
        description="Data allowance for the service (e.g., 'Unlimited', '10GB').",
    )
    activeFeatures: List[ActiveFeature] = Field(
        default_factory=list,
        description="List of active features for this service."
    )

# ---------------------------
# Validation Models
# ---------------------------


class DeviceUpgradeEligibility(StrictBaseModel):
    isEligible: bool = Field(
        ...,
        description="Whether the device is eligible for upgrade.",
    )
    eligibilityDate: Optional[str] = Field(
        None,
        description="Date when device becomes eligible for upgrade.",
    )
    reason: Optional[str] = Field(
        None,
        description="Explanation if not eligible.",
    )
    earlyUpgradeOptions: Optional[str] = Field(
        None,
        description="Early upgrade options if available.",
    )
    remainingDevicePayments: Optional[float] = Field(
        None,
        description="Remaining device payments.",
        ge=0.0
    )


class ServiceModificationResponse(StrictBaseModel):
    status: str = Field(
        description="Success status of the operation",
    )
    effectiveDate: str = Field(
        ...,
        description="Date when the modification becomes effective.",
    )
    message: str = Field(
        ...,
        description="Human-readable confirmation message.",
    )
    nextBillImpactEstimate: str = Field(
        ...,
        description="Estimated impact on next bill.",
    )
    orderId: str = Field(
        ...,
        description="Unique order identifier for tracking.",
    )


class KnowledgeBaseSnippet(StrictBaseModel):
    text: Optional[str] = Field(
        None,
        description="Snippet content",
    )
    title: Optional[str] = Field(
        None,
        description="Source title",
    )
    uri: Optional[str] = Field(
        None,
        description="Reference URL",
    )


class KnowledgeBaseQueryResponse(StrictBaseModel):
    answer: Optional[str] = Field(
        None,
        description="Human-readable answer to the query",
    )
    snippets: List[KnowledgeBaseSnippet] = Field(
        default_factory=list,
        description="List of snippets from the knowledge base.",
    )


class CustomerAccountDetails(StrictBaseModel):
    """Account details information"""
    accountId: str = Field(
        ...,
        description="Unique identifier for the account.",
        min_length=1,
        max_length=50
    )
    isVerified: bool = Field(
        ...,
        description="Whether the account is verified."
    )
    customerName: str = Field(
        ...,
        description="Full name of the customer.",
        min_length=1,
        max_length=200
    )
    contactEmail: str = Field(
        ...,
        description="Contact email address for the customer.",
        min_length=1,
        max_length=200,
        pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    contactPhone: str = Field(
        ...,
        description="Contact phone number for the customer.",
        min_length=1,
        max_length=20
    )
    billingAddress: Address = Field(
        ...,
        description="Billing address for the account."
    )
    serviceAddress: Address = Field(
        ...,
        description="Service address for the account."
    )
    communicationPreferences: CommunicationPreferences = Field(
        ...,
        description="Communication preferences for the customer."
    )
    services: List[ServicePlan] = Field(
        default_factory=list,
        description="List of services associated with the account."
    )
    devices: List[Device] = Field(
        default_factory=list,
        description="List of devices associated with the account."
    )
    securityPinSet: bool = Field(
        ...,
        description="Whether a security PIN has been set for the account."
    )


class TerminalResponse(StrictBaseModel):
    action: str = Field(
        ...,
        description="The action type (e.g. 'escalate', 'fail', 'cancel').",
    )
    reason: str = Field(
        ...,
        description="The provided reason for the action.",
        min_length=1,
    )
    status: str = Field(
        ...,
        description="Status message for the user.",
        min_length=1,
        max_length=100
    )


class PlanSearchResult(BaseModel):
    """Model for individual plan or feature search results from Gemini API."""

    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None  # "PLAN" or "FEATURE_ADDON"
    monthlyCost: Optional[float] = None
    dataAllowance: Optional[str] = None
    termsAndConditionsUrl: Optional[str] = None
    compatibilityNotes: Optional[str] = None


# ---------------------------
# Tool Input Models
# ---------------------------


class CommunicationPreferencesInput(StrictBaseModel):
    """Input parameters for updating communication preferences."""

    emailOptIn: Optional[bool] = Field(
        None, description="Whether the customer wants to receive email communications."
    )
    smsOptIn: Optional[bool] = Field(
        None, description="Whether the customer wants to receive SMS communications."
    )


class GetCustomerAccountDetailsInput(StrictBaseModel):
    """Input parameters for retrieving customer account details."""

    accountId: str = Field(
        ...,
        min_length=1,
        description="""The unique identifier for the customer's account or phone number. 
Example: "ACC123456789" or "122-334-4556" """
    )

class AddressInput(StrictBaseModel):
    recipientName: Optional[str] = Field(
        None,
        description="Name of the recipient at this address.",
        min_length=1,
        max_length=200
    )
    streetAddressLine1: Optional[str] = Field(
        None,
        description="Primary street address line.",
        min_length=1,
        max_length=200
    )
    streetAddressLine2: Optional[str] = Field(
        None,
        description="Secondary street address line (apartment, suite, etc.).",
        max_length=200
    )
    city: Optional[str] = Field(
        None,
        description="City name.",
        min_length=1,
        max_length=100
    )
    state: Optional[str] = Field(
        None,
        description="State or province code.",
        min_length=2,
        max_length=10
    )
    zipCode: Optional[str] = Field(
        None,
        description="ZIP or postal code.",
        min_length=1,
        max_length=20
    )
    country: Optional[str] = Field(
        None,
        description="Country code or name.",
        min_length=2,
        max_length=50
    )

class AccountInformationUpdateInput(StrictBaseModel):
    billingAddress: Optional[AddressInput] = Field(
        None,
        description="The billing address of the customer."
    )
    serviceAddress: Optional[AddressInput] = Field(
        None,
        description="The service address of the customer."
    )
    communicationPreferences: Optional[CommunicationPreferencesInput] = Field(
        None,
        description="The communication preferences of the customer."
    )
    contactEmail: Optional[str] = Field(
        None,
        description="The email address of the customer. Must be a valid email address."
    )
    contactPhone: Optional[str] = Field(
        None,
        description="New contact phone number in any valid format (e.g., 555-123-4567, (555) 123-4567, 5551234567). Will be normalized."
    )


class UpdateAccountInformationInput(StrictBaseModel):
    """Input parameters for updating account information."""

    accountId: str = Field(
        ...,
        min_length=1,
        description="""The unique identifier for the customer's account or phone number. 
Example: "ACC888777666" or "222-334-4556" """
    )
    requestBody: AccountInformationUpdateInput = Field(
        ...,
        description="""Dictionary containing the new information to be updated.
Only include the fields you want to change. Fields with None values will be ignored."""
    )


class CheckDeviceUpgradeEligibilityInput(StrictBaseModel):
    """Input parameters for checking device upgrade eligibility."""

    accountId: str = Field(
        ...,
        min_length=1,
        description="""The unique identifier for the customer's account or phone number. 
Example: "ACC123456789" or "222-334-4556" """
    )
    identifier: str = Field(
        ...,
        min_length=1,
        description="""The phone number or device ID to check. Examples:
- For LINE_NUMBER: "555-123-4567"
- For DEVICE_ID: "DEV987654321" """
    )
    identifierType: Literal["LINE_NUMBER", "DEVICE_ID"] = Field(
        ...,
        description="""Specifies the type of the identifier provided. Must be one of:
- "LINE_NUMBER": Use when searching by phone number
- "DEVICE_ID": Use when searching by device identifier """
    )


class ModifyServicePlanOrFeatureInput(StrictBaseModel):
    """Input parameters for modifying service plan or feature."""

    accountId: str = Field(
        ...,
        min_length=1,
        description="""The unique identifier for the customer's account or phone number. 
Example: "ACC123456789" or "222-334-4556" """
    )
    action: Literal["CHANGE_PLAN", "ADD_FEATURE", "REMOVE_FEATURE"] = Field(
        ...,
        description="""The type of modification to perform:
- "CHANGE_PLAN": Replaces current plan with a new one specified in itemId.
- "ADD_FEATURE": Adds a feature specified in itemId to the current plan.
- "REMOVE_FEATURE": Removes a feature specified in itemId. """
    )
    itemId: str = Field(
        ...,
        min_length=1,
        description="""The unique identifier for the plan or feature being actioned. 
Examples:
- For a plan: "PLAN_UNL_PRO"
- For a feature: "FEAT_INTL_CALL" """
    )
    currentPlanId: str = Field(
        ...,
        min_length=1,
        description="""The ID of the customer's current plan to ensure the correct plan is being replaced or modified. 
Example: "PLAN_UNL_PLUS" """
    )
    customerConfirmationText: Optional[str] = Field(
        default=None,
        description="""A summary of the change that the user has explicitly agreed to. 
Used for logging and auditing purposes. """
    )


class QueryAvailablePlansAndFeaturesInput(StrictBaseModel):
    """Input parameters for querying available plans and features."""

    query: str = Field(
        ...,
        min_length=1,
        description="""The user's question, phrased as a clear, specific search query.
Examples:
- "details of Unlimited Pro plan data allowance"
- "cost of international calling pass feature"
- "what plans include mobile hotspot" """
    )


class QueryAccountOrdersInput(StrictBaseModel):
    """Input parameters for querying account orders."""

    query: str = Field(
        ...,
        min_length=1,
        description="""The user's question about their orders. Examples:
- "What was the shipping status of my most recent order?"
- "How much did I pay for the phone I bought in May?"
- "Show me my order history for the past 3 months" """
    )
    filter: str = Field(
        ...,
        min_length=1,
        description="""An expression to filter the search to the specific customer's
account. The format MUST be "accountId='<customer_account_id>'". 
Example: "accountId='ACC123456789'" """
    )


class EscalateInput(StrictBaseModel):
    """Input parameters for escalate action."""

    reason: str = Field(
        ...,
        min_length=1,
        description="""A clear and concise explanation for the escalation. This reason will be logged and shown to the human agent. Examples:
- "The user wants to file a formal complaint about their billing"
- "The user is requesting account closure which requires human approval"
- "The user is experiencing technical issues beyond my capabilities" """
    )


class FailInput(StrictBaseModel):
    """Input parameters for fail action."""

    reason: str = Field(
        ...,
        min_length=1,
        description="""A clear and concise internal-facing explanation for why the task failed. This is used for logging and improving the agent. Examples:
- "After three attempts, I could not understand the user's request"
- "User provided unclear instructions and did not respond to clarification"
- "Unable to parse the user's intent from their messages" """
    )


class CancelInput(StrictBaseModel):
    """Input parameters for cancel action."""

    reason: str = Field(
        ...,
        min_length=1,
        description="""A clear and concise summary of why the task was canceled, 
based on the user's request. Examples:
- "The user stated they did not have their account information ready"
- "The user changed their mind and no longer wants to proceed"
- "The user asked to cancel the current operation" """
    )
