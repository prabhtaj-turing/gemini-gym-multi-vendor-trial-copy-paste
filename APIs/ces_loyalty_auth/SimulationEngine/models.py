from typing import List, Dict, Optional, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, RootModel


class DispositionCode(str, Enum):
    AGENT_TRANSFER = 'AGENT_TRANSFER'
    ANSWERING_MACHINE = 'ANSWERING_MACHINE'
    AUTH_DECLINED = 'AUTH_DECLINED'
    AUTH_FAILED = 'AUTH_FAILED'
    CANCELLATION_REQUEST = 'CANCELLATION_REQUEST'
    DO_NOT_CALL = 'DO_NOT_CALL'
    DO_NOT_SMS = 'DO_NOT_SMS'
    NOTIFICATION_NOT_RECEIVED = 'NOTIFICATION_NOT_RECEIVED'
    PROMO_ACCEPTED = 'PROMO_ACCEPTED'
    PROMO_DECLINED = 'PROMO_DECLINED'
    PROMO_SUBMITTED = 'PROMO_SUBMITTED'
    UNENROLL_REQUEST = 'UNENROLL_REQUEST'



class CallEndState(str, Enum):
    AGENT_TRANSFER = 'AGENT_TRANSFER'
    DISCONNECT = 'DISCONNECT'
    DO_NOT_CALL = 'DO_NOT_CALL'
    DO_NOT_SMS = 'DO_NOT_SMS'


class Subscription(BaseModel):
    skuName: Optional[str] = Field(None, description="SKU name of the subscription.")
    spoId: Optional[str] = Field(None, description="Service plan option ID.")
    onPromo: Optional[bool] = Field(None, description="Whether the subscription is on promotion.")
    enrolled: Optional[bool] = Field(None, description="Whether the customer is enrolled.")
    promoRedeemed: Optional[bool] = Field(None, description="Whether the promotion has been redeemed.")
    price: Optional[str] = Field(None, description="Price of the subscription.")
    description: Optional[str] = Field(None, description="Description of the subscription.")
    onEligiblePlanAndDevice: Optional[bool] = Field(None, description="Whether eligible for plan and device.")
    displayName: Optional[str] = Field(None, description="Display name of the subscription.")
    registrationStatus: Optional[str] = Field(None, description="Registration status of the subscription.")
    status: Optional[str] = Field(None, description="Current status of the subscription.")
    entitlementStatus: Optional[str] = Field(None, description="Entitlement status of the subscription.")
    subscriptionId: Optional[str] = Field(None, description="Unique identifier for the subscription.")
    service: Optional[str] = Field(None, description="Service type of the subscription.")
    isPerk: Optional[bool] = Field(None, description="Whether this is a perk subscription.")


class PaymentHistory(BaseModel):
    totalBalance: Optional[str] = Field(None, description="Total balance for the period.")
    adjustedPreviousAmount: Optional[str] = Field(None, description="Adjusted previous amount.")
    amountPaid: Optional[str] = Field(None, description="Amount paid for the period.")
    billCycleStartDate: Optional[str] = Field(None, description="Start date of the bill cycle.")
    invoiceDate: Optional[str] = Field(None, description="Date of the invoice.")
    billCycleEndDate: Optional[str] = Field(None, description="End date of the bill cycle.")


class PaymentInfo(BaseModel):
    enrolledInAutopay: bool = Field(..., description="Whether enrolled in autopay.")
    invoiceDate: Optional[str] = Field(None, description="Date of the invoice.")
    lastPaymentDate: Optional[str] = Field(None, description="Date of the last payment.")
    paymentDueDate: Optional[str] = Field(None, description="Date when payment is due.")
    pastDueDays: Optional[str] = Field(None, description="Number of days past due.")
    enrolledInPaperFree: Optional[bool] = Field(None, description="Whether enrolled in paper-free billing.")
    lastPaymentAmount: Optional[str] = Field(None, description="Amount of the last payment.")
    eligibleForPaperFree: Optional[bool] = Field(None, description="Whether eligible for paper-free billing.")
    currentCharges: Optional[str] = Field(None, description="Current charges amount.")
    arPastDueBalance: Optional[str] = Field(None, description="Accounts receivable past due balance.")
    paymentHistory: Optional[List[PaymentHistory]] = Field(None, description="List of payment history entries:")
    pastDueBalance: Optional[str] = Field(None, description="Past due balance amount.")
    outstandingBalance: Optional[str] = Field(None, description="Outstanding balance amount.")


class MtnStatus(BaseModel):
    involuntarySuspendedWithNonPayment: Optional[bool] = Field(None, description="Whether suspended due to non-payment.")
    isActive: Optional[bool] = Field(None, description="Whether the line is currently active.")
    isSuspendedWithBilling: Optional[bool] = Field(None, description="Whether the line is suspended with billing.")
    mtnStatusReasonCode: Optional[str] = Field(None, description="Reason code for the current status.")
    voluntarySuspended: Optional[bool] = Field(None, description="Whether the line is voluntarily suspended.")
    involuntarySuspended: Optional[bool] = Field(None, description="Whether the line is involuntarily suspended.")
    isSuspendedWithoutBilling: Optional[bool] = Field(None, description="Whether the line is suspended without billing.")


class DeviceCategory(BaseModel):
    connectedDevice: Optional[bool] = Field(None, description="Whether it's a connected device.")
    smartwatch: Optional[bool] = Field(None, description="Whether it's a smartwatch.")
    homeSolutions: Optional[bool] = Field(None, description="Whether it's a home solutions device.")
    internetDevice: Optional[bool] = Field(None, description="Whether it's an internet device.")
    basicphone: Optional[bool] = Field(None, description="Whether it's a basic phone.")
    WSOnly: Optional[bool] = Field(None, description="Whether it's a WS-only device.")
    tablet: Optional[bool] = Field(None, description="Whether it's a tablet.")
    homePC: Optional[bool] = Field(None, description="Whether it's a home PC.")
    virtualDevice: Optional[bool] = Field(None, description="Whether it's a virtual device.")
    telematics: Optional[bool] = Field(None, description="Whether it's a telematics device.")
    laptop: Optional[bool] = Field(None, description="Whether it's a laptop.")
    smartphone: Optional[bool] = Field(None, description="Whether it's a smartphone.")


class DeviceType(BaseModel):
    jetPack4G: Optional[bool] = Field(None, description="Whether it's a 4G jetpack.")
    deskphone: Optional[bool] = Field(None, description="Whether it's a desk phone.")
    homeFusionDevice: Optional[bool] = Field(None, description="Whether it's a home fusion device.")
    device3G: Optional[bool] = Field(None, description="Whether it's a 3G device.")
    device5GE: Optional[bool] = Field(None, description="Whether it's a 5G device.")
    backupRouter4G: Optional[bool] = Field(None, description="Whether it's a backup 4G router.")
    autoAttendant: Optional[bool] = Field(None, description="Whether it's an auto attendant.")
    description: Optional[str] = Field(None, description="Description of the device type.")
    device5GA: Optional[bool] = Field(None, description="Whether it's a 5G Advanced device.")
    device4G: Optional[bool] = Field(None, description="Whether it's a 4G device.")
    overTheTop: Optional[bool] = Field(None, description="Whether it's an over-the-top device.")
    antenna5G: Optional[bool] = Field(None, description="Whether it's a 5G antenna.")
    home5G: Optional[bool] = Field(None, description="Whether it's a home 5G device.")
    huntGroup: Optional[bool] = Field(None, description="Whether it's a hunt group device.")
    jetPack5G: Optional[bool] = Field(None, description="Whether it's a 5G jetpack.")
    device4GO: Optional[bool] = Field(None, description="Whether it's a 4G-only device.")


class DeviceInfo(BaseModel):
    displayName: Optional[str] = Field(None, description="Display name of the device.")
    category: Optional[DeviceCategory] = Field(None, description="Device category information:")
    deviceUrl: Optional[str] = Field(None, description="URL to device image.")
    deviceType: Optional[DeviceType] = Field(None, description="Device type information:")


class EquipmentInfo(BaseModel):
    deviceInfo: Optional[DeviceInfo] = Field(None, description="Device information:")


class AccessCharge(BaseModel):
    monthlyAccessCharge: Optional[str] = Field(None, description="Monthly access charge amount.")
    finalPriceWithLACAndDiscount: Optional[str] = Field(None, description="Final price with LAC and discount.")
    discountedCharge: Optional[str] = Field(None, description="Discounted charge amount.")
    finalPriceWithLAC: Optional[str] = Field(None, description="Final price with line access charge.")
    discountedAccessChargeWithPerk: Optional[str] = Field(None, description="Discounted access charge with perk.")


class PricePlanInfo(BaseModel):
    planId: str = Field(..., description="Unique identifier for the plan.")
    effectiveDate: str = Field(..., description="Date when the plan became effective.")
    planDisplayName: str = Field(..., description="Display name of the plan.")
    planCategoryName: Optional[str] = Field(None, description="Category name of the plan.")
    description: Optional[str] = Field(None, description="Description of the plan.")
    planSkuName: Optional[str] = Field(None, description="SKU name of the plan.")
    accessCharge: Optional[AccessCharge] = Field(None, description="Access charge information:")


class EquipmentUpgradeEligibility(BaseModel):
    upgradeEligible: Optional[str] = Field(None, description="Whether upgrade is eligible.")
    buyoutRestricted: Optional[str] = Field(None, description="Whether buyout is restricted.")
    upgradeEligibilityDate: Optional[str] = Field(None, description="Date when upgrade becomes eligible.")
    earlyUpgradeEligible: Optional[str] = Field(None, description="Whether early upgrade is eligible.")
    alwaysUpgradeEligible: Optional[str] = Field(None, description="Whether always upgrade eligible.")
    buyoutEligible: Optional[str] = Field(None, description="Whether buyout is eligible.")


class AccessRoles(BaseModel):
    owner: bool = Field(..., description="Whether the user is the owner.")
    manager: bool = Field(..., description="Whether the user is a manager.")
    member: bool = Field(..., description="Whether the user is a member.")


class MobileInfoAttributes(BaseModel):
    accessRoles: AccessRoles = Field(..., description="Access roles for the line:")


class LaunchUpdatesLink(BaseModel):
    text: Optional[str] = Field(None, description="Link text")


class Introduction(BaseModel):
    headline: Optional[str] = Field(None, description="Introduction headline")
    description: Optional[str] = Field(None, description="Introduction description")
    valueStatement: Optional[str] = Field(None, description="Value statement")
    launchUpdatesLink: Optional[LaunchUpdatesLink] = Field(None, description="Launch updates link")


class NewOffer(BaseModel):
    category: str = Field(..., description="Offer category")
    details: str = Field(..., description="Offer details")


class Note(BaseModel):
    audience: str = Field(..., description="Target audience")
    detail: str = Field(..., description="Note detail")


class SystemUpdateNote(BaseModel):
    title: str = Field(..., description="System update note title")
    period: str = Field(..., description="Update period")
    details: List[str] = Field(..., description="Update details")


class SavingsBreakdownItem(BaseModel):
    area: str = Field(..., description="Savings area")
    description: str = Field(..., description="Area description")


class Guarantee(BaseModel):
    type: str = Field(..., description="Type of guarantee")
    title: str = Field(..., description="Title of the guarantee")
    startDate: Optional[str] = Field(None, description="Start date of the guarantee")
    newOffers: Optional[List[NewOffer]] = Field(None, description="New offers")
    explanation: Optional[List[str]] = Field(None, description="Explanation text")
    exclusions: Optional[str] = Field(None, description="Exclusions text")
    notes: Optional[List[Note]] = Field(None, description="Notes")
    systemUpdateNote: Optional[SystemUpdateNote] = Field(None, description="System update note")
    offer: Optional[str] = Field(None, description="Offer description")
    summary: Optional[str] = Field(None, description="Summary text")
    newFeature: Optional[str] = Field(None, description="New feature description")
    explanationTitle: Optional[str] = Field(None, description="Explanation title")
    savingsBreakdown: Optional[List[SavingsBreakdownItem]] = Field(None, description="Savings breakdown")


class HowItWorks(BaseModel):
    title: Optional[str] = Field(None, description="How it works title")
    guarantees: Optional[List[Guarantee]] = Field(None, description="List of guarantees")


class QuickPitch(BaseModel):
    title: Optional[str] = Field(None, description="Quick pitch title")
    description: Optional[str] = Field(None, description="Quick pitch description")
    pitch: Optional[str] = Field(None, description="Quick pitch text")


class SundayMobileValueProposition(BaseModel):
    title: Optional[str] = Field(None, description="Title of the value proposition")
    lastUpdated: Optional[str] = Field(None, description="Last updated timestamp")
    introduction: Optional[Introduction] = Field(None, description="Introduction information")
    howItWorks: Optional[HowItWorks] = Field(None, description="How it works information")
    quickPitch: Optional[QuickPitch] = Field(None, description="Quick pitch information")


class Line(BaseModel):
    mtn: str = Field(..., description="Mobile telephone number for the line.")
    mtnStatus: MtnStatus = Field(..., description="Status information for the mobile telephone number:")
    equipmentInfos: EquipmentInfo = Field(..., description="Equipment information for the line:")
    autoPayReflected: Optional[bool] = Field(None, description="Whether autopay is reflected.")
    pricePlanInfo: Optional[PricePlanInfo] = Field(None, description="Information about the pricing plan:")
    mobileInfoAttributes: Optional[MobileInfoAttributes] = Field(None, description="Mobile information attributes:")
    equipmentUpgradeEligibility: Optional[EquipmentUpgradeEligibility] = Field(None, description="Equipment upgrade eligibility:")
    autoPayDiscount: Optional[str] = Field(None, description="Autopay discount amount.")
    autoPayEligible: Optional[bool] = Field(None, description="Whether the line is eligible for autopay.")
    subscriptions: Optional[List[Subscription]] = Field(None, description="List of subscription services:")
    enrolledForLoyalty: Optional[bool] = Field(None, description="Whether enrolled for loyalty program.")


class CustomerProfile(BaseModel):
    customerName: str = Field(..., description="The customer's full name.")
    numberOfLines: str = Field(..., description="The number of lines on the account.")
    accountNumber: str = Field(..., description="The customer's account number in format \"XXXXXXXXXXX-XXXXX\" (11 digits, dash, 5 digits).")
    lines: List[Line] = Field(..., description="A list of dictionaries, each representing a line with the following structure:")
    customerRole: Optional[str] = Field(None, description="The customer's role on the account.")
    greetByName: Optional[str] = Field(None, description="The name to greet the customer with.")
    customerFirstName: Optional[str] = Field(None, description="The customer's first name.")
    customerLastName: Optional[str] = Field(None, description="The customer's last name.")
    paymentInfo: Optional[PaymentInfo] = Field(None, description="A dictionary with payment information:")


class LoyaltyOffer(BaseModel):
    OfferDesc: str = Field(..., description="Description of the loyalty offer.")
    offerOrder: str = Field(..., description="Order/priority of the offer.")
    offerType: str = Field(..., description="Type of the offer (e.g., DISCOUNT, PERK).")
    OfferID: str = Field(..., description="Unique identifier for the offer.")


class MyPlanPerk(BaseModel):
    monthly_value: str = Field(..., description="Monthly value of the perk.")
    monthly_cost: str = Field(..., description="Monthly cost of the perk.")
    savings: str = Field(..., description="Savings amount from the perk.")
    description: str = Field(..., description="Description of the perk.")
    perk: str = Field(..., description="Name of the perk.")
    notes: Optional[str] = Field(None, description="Additional notes about the perk.")


class UnlimitedPlanPerkItem(BaseModel):
    monthly_value: Optional[str] = Field(None, description="Monthly value of the perk.")
    perk_id: str = Field(..., description="Unique identifier for the perk.")
    prorate: str = Field(..., description="Proration information for the perk.")
    description: str = Field(..., description="Description of the perk.")
    notes: Optional[str] = Field(None, description="Additional notes about the perk.")
    backdate: str = Field(..., description="Backdate information for the perk.")


class GetPreAuthenticationCallDataParams(BaseModel):
    hasMtnLoyaltyOffers: bool = Field(..., description="Whether the customer has loyalty offers.")
    availablePerks: List[Dict[str, str]] = Field(..., description="A list of dictionaries, each with a single key for the perk name.")
    accountNumber: str = Field(..., description="The customer's account number in format \"XXXXXXXXXXX-XXXXX\" (11 digits, dash, 5 digits).")
    status: str = Field(..., description="The status of the pre-authentication check.")
    statusCode: str = Field(..., description="The status code.")
    customerName: str = Field(..., description="The customer's full name.")
    preferredFirstName: str = Field(..., description="The customer's preferred first name.")
    firstName: str = Field(..., description="The customer's first name.")
    statusMessage: str = Field(..., description="A message describing the status.")
    loyaltyOffersStatusCode: str = Field(..., description="Status code for loyalty offers.")
    loyaltyOffers: List[LoyaltyOffer] = Field(..., description="A list of loyalty offer dictionaries with the following structure:")
    unlimitedPlanPerks: List[List[UnlimitedPlanPerkItem]] = Field(..., description="A list of lists of perk dictionaries with the following structure:")
    sundayMobileValueProposition: SundayMobileValueProposition = Field(..., description="Sunday Mobile value proposition information with the following structure:")
    sundayMobileOST: Dict[str, Any] = Field(..., description="A dictionary with the following structure:")
    autoPayPaperFreeDiscountAmountInfo: Dict[str, Any] = Field(..., description="A dictionary containing details about autopay discounts with the following structure:")
    myPlanPricingDetails: Dict[str, Any] = Field(..., description="A dictionary with plan names as keys, containing pricing details with the following structure:")
    myPlanPerks: Dict[str, List[MyPlanPerk]] = Field(..., description="A dictionary with the following structure:")
    myPlanFeatures: Dict[str, List[str]] = Field(..., description="A dictionary with plan names as keys and lists of feature descriptions with the following structure:")
    lines: Optional[List[Line]] = Field(None, description="A list of line information.")
    paymentInfo: Optional[PaymentInfo] = Field(None, description="Payment information for the customer.")
    numberOfLines: Optional[str] = Field(None, description="The number of lines on the account.")
    eligibleForAutopay: Optional[str] = Field(None, description="Whether the customer is eligible for autopay.")
    autopayDiscountAmount: Optional[str] = Field(None, description="The autopay discount amount.")
    greetByName: Optional[str] = Field(None, description="The name to greet the customer by.")
    customerFirstName: Optional[str] = Field(None, description="The customer's first name.")
    customerLastName: Optional[str] = Field(None, description="The customer's last name.")
    customerRole: Optional[str] = Field(None, description="The customer's role.")


class GetPreAuthenticationCallDataSessionInfo(BaseModel):
    parameters: GetPreAuthenticationCallDataParams = Field(
        ..., 
        description="A dictionary containing pre-authentication parameters with keys:"
    )


class GetPreAuthenticationCallDataResponse(BaseModel):
    sessionInfo: GetPreAuthenticationCallDataSessionInfo = Field(
        ..., 
        description="A dictionary containing session information"
    )


class GetAuthenticatedCustomerProfileResponse(BaseModel):
    customerProfile: CustomerProfile = Field(
        ..., 
        description="A dictionary containing the customer's profile information"
    )

class AdaptiveAuthentication(BaseModel):
    adaptiveAuthentication: Optional[str] = Field(
        None, 
        description="A JSON string containing adaptive authentication data with the following structure: {\"authstatus\": \"ACCEPT|PENDING|REJECT\", \"reason\": \"optional reason string\"}"
    )

class ManageCustomerAuthenticationParams(BaseModel):
    authstate: str = Field(..., description="The current authentication state.")
    sessionId: str = Field(..., description="The session ID.")
    statusMessage: str = Field(..., description="A message describing the status.")
    gotoPage: Optional[str] = Field(None, description="The page to redirect to.")
    error: Optional[str] = Field(None, description="Error message, if any.")
    statusCode: Optional[str] = Field(None, description="The status code.")
    sessionMap: Optional[AdaptiveAuthentication] = Field(None, description="Session data containing adaptive authentication information.")
    noService: Optional[str] = Field(None, description="Indicates if there is no service.")
    authmode: Optional[str] = Field(None, description="The authentication mode used.")


class ManageCustomerAuthenticationSessionInfo(BaseModel):
    parameters: ManageCustomerAuthenticationParams = Field(
        ..., 
        description="A dictionary containing authentication parameters with keys:"
    )


class ManageCustomerAuthenticationResponse(BaseModel):
    sessionInfo: ManageCustomerAuthenticationSessionInfo = Field(
        ..., 
        description="A dictionary containing session information"
    )


class OfferEnrollment(BaseModel):
    accountNumber: str
    offerId: str


class CesLoyaltyAuthDBModel(BaseModel):
    CONVERSATION_STATUS: Optional[Dict[str, Any]] = None
    SESSION_STATUS: Optional[Dict[str, Any]] = None
    AUTH_RESULT: Optional[ManageCustomerAuthenticationResponse] = None
    AUTH_STATUS: Optional[str] = None
    OFFER_ENROLLMENT: Optional[OfferEnrollment] = None
    PROFILE_BEFORE_AUTH: Optional[GetPreAuthenticationCallDataResponse] = None
    PROFILE_AFTER_AUTH: Optional[GetAuthenticatedCustomerProfileResponse] = None
    use_real_datastore: bool
    _end_of_conversation_status: Dict[str, Any]


# ---------------------------
# Tool Input Models
# ---------------------------

class GetAuthenticatedCustomerProfileInput(BaseModel):
    """Input parameters for retrieving authenticated customer profile."""
    authstatus: str = Field(
        default='EMPTY',
        description="""The current authentication status (e.g., 'ACCEPT'). 
Defaults to 'EMPTY' if not provided."""
    )


class ManageCustomerAuthenticationInput(BaseModel):
    """Input parameters for managing customer authentication."""
    authstate: str = Field(
        ...,
        description="The desired authentication state (e.g., 'AUTHENTICATION_INIT', 'AUTHENTICATION_STATUS')."
    )


class GetPreAuthenticationCallDataInput(BaseModel):
    """Input parameters for retrieving pre-authentication call data."""
    pass


class RecordCallOutcomeAndDisconnectInput(BaseModel):
    """Input parameters for recording call outcome and disconnecting."""
    dispositionSequence: str = Field(
        default='',
        description="Disposition sequence for the call."
    )
    callEndState: str = Field(
        default='',
        description="""The primary reason for ending the call (e.g.,
'DISCONNECT', 'DO_NOT_CALL', 'ANSWERING_MACHINE')."""
    )
    dispositionCode: str = Field(
        default='',
        description="""The final, specific status code for the call (e.g.,
'PROMO_DECLINED', 'ANSWERING_MACHINE')."""
    )
    preferredLang: str = Field(
        default='E',
        description="""The customer's preferred language. Defaults to 'E' for
English. Set to 'S' for Spanish."""
    )


class TransferToLiveAgentInput(BaseModel):
    """Input parameters for transferring to a live agent."""
    dispositionSequence: str = Field(
        default='',
        description="Disposition sequence for the call."
    )
    callEndState: str = Field(
        default='',
        description="""The reason for ending the call. MUST be set to
'AGENT_TRANSFER'."""
    )
    dispositionCode: str = Field(
        default='',
        description="""The specific reason for the transfer (e.g.,
'AGENT_TRANSFER', 'AUTH_FAILED')."""
    )
    preferredLang: str = Field(
        default='E',
        description="""The customer's preferred language. Defaults to 'E' for
English. Set to 'S' for Spanish transfers."""
    )


class EnrollInOfferInput(BaseModel):
    """Input parameters for enrolling customer in a loyalty offer."""
    accountNumber: str = Field(
        ...,
        min_length=1,
        description="""The customer's account number in format "XXXXXXXXXXX-XXXXX" (11 digits, dash, 5 digits), which must be retrieved
from the authenticated customer profile.""",
        pattern=r'^\S+$'  # Must not contain whitespace-only strings
    )
    offerId: str = Field(
        ...,
        min_length=1,
        description="""The unique ID for the loyalty offer, retrieved from the
initial get_pre_authentication_call_data action.""",
        pattern=r'^\S+$'  # Must not contain whitespace-only strings
    )


class DoneInput(BaseModel):
    """Input parameters for done action."""
    pass


class FailInput(BaseModel):
    """Input parameters for fail action."""
    summary: Optional[str] = Field(
        default=None,
        description="Summary of the failure reason."
    )


class CancelInput(BaseModel):
    """Input parameters for cancel action."""
    summary: Optional[str] = Field(
        default=None,
        description="Summary of the cancellation reason."
    )


class EscalateInput(BaseModel):
    """Input parameters for escalate action."""
    pass


# ---------------------------
# Tool Output Models
# ---------------------------

class StatusOutput(BaseModel):
    """Output model for simple status responses."""
    status: str = Field(..., description="The status of the operation, 'success' or 'failure'.")


class StringOutput(RootModel[str]):
    """Output model for simple string responses."""
    root: str = Field(..., description="The result message.")


class FailOutput(RootModel[str]):
    """Output model for fail."""
    root: str = Field(..., description="The failure message.")


class CancelOutput(RootModel[str]):
    """Output model for cancel."""
    root: str = Field(..., description="The cancellation message.")
