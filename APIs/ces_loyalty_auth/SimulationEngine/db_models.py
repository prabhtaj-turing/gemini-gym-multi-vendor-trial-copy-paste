import datetime as dt
from uuid import UUID, uuid4
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

# ---------------------------
# Enum Types
# ---------------------------

class ConversationStatus(str, Enum):
    """Status of the conversation flow"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    PENDING = "pending"

class SessionStatus(str, Enum):
    """Status of the user session"""
    AUTHENTICATED = "authenticated"
    UNAUTHENTICATED = "unauthenticated"
    EXPIRED = "expired"
    PENDING = "pending"

class AuthResult(str, Enum):
    """Result of authentication attempt"""
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    EXPIRED = "expired"

class AuthStatus(str, Enum):
    """Current authentication status"""
    AUTHENTICATED = "authenticated"
    UNAUTHENTICATED = "unauthenticated"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"
    PENDING = "PENDING"

class OfferEnrollmentStatus(str, Enum):
    """Status of loyalty offer enrollment"""
    ENROLLED = "enrolled"
    NOT_ENROLLED = "not_enrolled"
    PENDING = "pending"
    ELIGIBLE = "eligible"

class DeviceType(str, Enum):
    """Type of device"""
    SMARTPHONE = "smartphone"
    BASIC_PHONE = "basicphone"
    TABLET = "tablet"
    SMARTWATCH = "smartwatch"
    HOME_PC = "homePC"
    TELEMATICS = "telematics"
    LAPTOP = "laptop"

class EntitlementStatus(str, Enum):
    """Entitlement status for perks"""
    ENTITLED = "ENTITLED"
    NOT_ENTITLED = "NOT_ENTITLED"
    PENDING = "PENDING"

class RegistrationStatus(str, Enum):
    """Registration status for perks"""
    REGISTERED = "REGISTERED"
    REGISTRATION_PENDING = "REGISTRATION_PENDING"
    NOT_REGISTERED = "NOT_REGISTERED"

class ServiceStatus(str, Enum):
    """Service status"""
    SUBSCRIBED = "SUBSCRIBED"
    UNSUBSCRIBED = "UNSUBSCRIBED"
    PENDING = "PENDING"

# ---------------------------
# Internal Storage Models
# ---------------------------


class LoyaltyOffer(BaseModel):
    """Loyalty offer information"""
    offer_order: str = Field(..., description="Order of the offer")
    offer_id: str = Field(..., description="Unique identifier for the offer")
    offer_desc: str = Field(..., description="Description of the offer")
    offer_type: str = Field(..., description="Type of offer (e.g., 'Loyalty')")

class SessionInfo(BaseModel):
    """Session information"""
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Session parameters")
    
    class Config:
        allow_population_by_field_name = True

class ProfileBeforeAuth(BaseModel):
    """Customer profile before authentication"""
    sessionInfo: SessionInfo = Field(..., description="Session information")

class AccessCharge(BaseModel):
    """Access charge information"""
    discountedCharge: Optional[str] = Field(None, description="Discounted charge amount")
    monthlyAccessCharge: Optional[str] = Field(None, description="Monthly access charge amount")
    finalPriceWithLAC: Optional[str] = Field(None, description="Final price with LAC")
    finalPriceWithLACAndDiscount: Optional[str] = Field(None, description="Final price with LAC and discount")
    discountedAccessChargeWithPerk: Optional[str] = Field(None, description="Discounted access charge with perk")

class PricePlanInfo(BaseModel):
    """Price plan information"""
    effectiveDate: str = Field(..., description="Effective date of the plan")
    planId: str = Field(..., description="Plan identifier")
    description: Optional[str] = Field(None, description="Plan description")
    planCategoryName: Optional[str] = Field(None, description="Plan category name")
    planDisplayName: str = Field(..., description="Plan display name")
    planSkuName: Optional[str] = Field(None, description="Plan SKU name")
    accessCharge: Optional[AccessCharge] = Field(None, description="Access charge information")

class Subscription(BaseModel):
    """Subscription information"""
    spoId: Optional[str] = Field(None, description="SPO identifier")
    description: Optional[str] = Field(None, description="Subscription description")
    skuName: Optional[str] = Field(None, description="SKU name")
    price: Optional[str] = Field(None, description="Price of the subscription")
    enrolled: Optional[bool] = Field(None, description="Whether enrolled in the subscription")
    onPromo: Optional[bool] = Field(None, description="Whether on promotion")
    promoRedeemed: Optional[bool] = Field(None, description="Whether promotion is redeemed")
    onEligiblePlanAndDevice: Optional[bool] = Field(None, description="Whether on eligible plan and device")
    subscriptionId: Optional[str] = Field(None, description="Subscription identifier")
    entitlementStatus: Optional[EntitlementStatus] = Field(None, description="Entitlement status")
    registrationStatus: Optional[RegistrationStatus] = Field(None, description="Registration status")
    status: Optional[ServiceStatus] = Field(None, description="Service status")
    displayName: Optional[str] = Field(None, description="Display name")
    service: Optional[str] = Field(None, description="Service name")
    isPerk: Optional[bool] = Field(None, description="Whether this is a perk")

class MTNStatus(BaseModel):
    """Mobile Telephone Number status"""
    isActive: Optional[bool] = Field(None, description="Whether the MTN is active")
    isSuspendedWithBilling: Optional[bool] = Field(None, description="Whether suspended with billing")
    isSuspendedWithoutBilling: Optional[bool] = Field(None, description="Whether suspended without billing")
    voluntarySuspended: Optional[bool] = Field(None, description="Whether voluntarily suspended")
    involuntarySuspendedWithNonPayment: Optional[bool] = Field(None, description="Whether involuntarily suspended with non-payment")
    involuntarySuspended: Optional[bool] = Field(None, description="Whether involuntarily suspended")
    mtnStatusReasonCode: Optional[str] = Field(None, description="MTN status reason code")

class DeviceCategory(BaseModel):
    """Device category information"""
    smartphone: Optional[bool] = Field(None, description="Whether it's a smartphone")
    basicphone: Optional[bool] = Field(None, description="Whether it's a basic phone")
    tablet: Optional[bool] = Field(None, description="Whether it's a tablet")
    smartwatch: Optional[bool] = Field(None, description="Whether it's a smartwatch")
    homePC: Optional[bool] = Field(None, description="Whether it's a home PC")
    telematics: Optional[bool] = Field(None, description="Whether it's telematics")
    WSOnly: Optional[bool] = Field(None, description="Whether it's WS only")
    virtualDevice: Optional[bool] = Field(None, description="Whether it's a virtual device")
    connectedDevice: Optional[bool] = Field(None, description="Whether it's a connected device")
    internetDevice: Optional[bool] = Field(None, description="Whether it's an internet device")
    homeSolutions: Optional[bool] = Field(None, description="Whether it's home solutions")
    laptop: Optional[bool] = Field(None, description="Whether it's a laptop")

class DeviceTypeInfo(BaseModel):
    """Device type information"""
    device3G: Optional[bool] = Field(None, description="Whether it's a 3G device")
    device4G: Optional[bool] = Field(None, description="Whether it's a 4G device")
    backupRouter4G: Optional[bool] = Field(None, description="Whether it's a backup router 4G")
    device5GE: Optional[bool] = Field(None, description="Whether it's a 5GE device")
    device5GA: Optional[bool] = Field(None, description="Whether it's a 5GA device")
    antenna5G: Optional[bool] = Field(None, description="Whether it's a 5G antenna")
    homeFusionDevice: Optional[bool] = Field(None, description="Whether it's a home fusion device")
    autoAttendant: Optional[bool] = Field(None, description="Whether it's an auto attendant")
    huntGroup: Optional[bool] = Field(None, description="Whether it's a hunt group")
    overTheTop: Optional[bool] = Field(None, description="Whether it's over the top")
    deskphone: Optional[bool] = Field(None, description="Whether it's a desk phone")
    device4GO: Optional[bool] = Field(None, description="Whether it's a 4GO device")
    description: Optional[str] = Field(None, description="Device type description")
    jetPack5G: Optional[bool] = Field(None, description="Whether it's a 5G jet pack")
    home5G: Optional[bool] = Field(None, description="Whether it's a 5G home device")
    jetPack4G: Optional[bool] = Field(None, description="Whether it's a 4G jet pack")

class DeviceInfo(BaseModel):
    """Device information"""
    deviceUrl: Optional[str] = Field(None, description="URL of the device image")
    displayName: Optional[str] = Field(None, description="Display name of the device")
    category: Optional[DeviceCategory] = Field(None, description="Device category")
    deviceType: Optional[DeviceTypeInfo] = Field(None, description="Device type information")

class EquipmentInfos(BaseModel):
    """Equipment information"""
    deviceInfo: Optional[DeviceInfo] = Field(None, description="Device information")

class AccessRoles(BaseModel):
    """Access roles"""
    owner: Optional[bool] = Field(None, description="Whether the user is an owner")
    manager: Optional[bool] = Field(None, description="Whether the user is a manager")
    member: Optional[bool] = Field(None, description="Whether the user is a member")

class MobileInfoAttributes(BaseModel):
    """Mobile information attributes"""
    accessRoles: Optional[AccessRoles] = Field(None, description="Access roles")

class EquipmentUpgradeEligibility(BaseModel):
    """Equipment upgrade eligibility"""
    upgradeEligible: Optional[str] = Field(None, description="Whether upgrade is eligible")
    buyoutRestricted: Optional[str] = Field(None, description="Whether buyout is restricted")
    upgradeEligibilityDate: Optional[str] = Field(None, description="Upgrade eligibility date")
    earlyUpgradeEligible: Optional[str] = Field(None, description="Whether early upgrade is eligible")
    alwaysUpgradeEligible: Optional[str] = Field(None, description="Whether always upgrade eligible")
    buyoutEligible: Optional[str] = Field(None, description="Whether buyout is eligible")

class Line(BaseModel):
    """Mobile line information"""
    mtn: str = Field(..., description="Mobile Telephone Number")
    pricePlanInfo: Optional[PricePlanInfo] = Field(None, description="Price plan information")
    subscriptions: Optional[List[Subscription]] = Field(None, description="List of subscriptions")
    autoPayEligible: Optional[bool] = Field(None, description="Whether eligible for auto pay")
    autoPayReflected: Optional[bool] = Field(None, description="Whether auto pay is reflected")
    autoPayDiscount: Optional[str] = Field(None, description="Auto pay discount amount")
    enrolledForLoyalty: Optional[bool] = Field(None, description="Whether enrolled for loyalty")
    mtnStatus: MTNStatus = Field(..., description="MTN status")
    equipmentInfos: EquipmentInfos = Field(..., description="Equipment information")
    mobileInfoAttributes: Optional[MobileInfoAttributes] = Field(None, description="Mobile information attributes")
    equipmentUpgradeEligibility: Optional[EquipmentUpgradeEligibility] = Field(None, description="Equipment upgrade eligibility")

class PaymentHistory(BaseModel):
    """Payment history entry"""
    invoiceDate: Optional[str] = Field(None, description="Invoice date")
    totalBalance: Optional[str] = Field(None, description="Total balance")
    adjustedPreviousAmount: Optional[str] = Field(None, description="Adjusted previous amount")
    billCycleStartDate: Optional[str] = Field(None, description="Bill cycle start date")
    billCycleEndDate: Optional[str] = Field(None, description="Bill cycle end date")
    amountPaid: Optional[str] = Field(None, description="Amount paid")

class PaymentInfo(BaseModel):
    """Payment information"""
    lastPaymentDate: Optional[str] = Field(None, description="Last payment date")
    lastPaymentAmount: Optional[str] = Field(None, description="Last payment amount")
    pastDueBalance: Optional[str] = Field(None, description="Past due balance")
    pastDueDays: Optional[str] = Field(None, description="Past due days")
    arPastDueBalance: Optional[str] = Field(None, description="AR past due balance")
    invoiceDate: Optional[str] = Field(None, description="Invoice date")
    outstandingBalance: Optional[str] = Field(None, description="Outstanding balance")
    currentCharges: Optional[str] = Field(None, description="Current charges")
    paymentDueDate: Optional[str] = Field(None, description="Payment due date")
    enrolledInPaperFree: Optional[bool] = Field(None, description="Whether enrolled in paper free")
    eligibleForPaperFree: Optional[bool] = Field(None, description="Whether eligible for paper free")
    enrolledInAutopay: bool = Field(..., description="Whether enrolled in auto pay")
    paymentHistory: Optional[List[PaymentHistory]] = Field(None, description="Payment history")

class CustomerProfile(BaseModel):
    """Customer profile information"""
    accountNumber: str = Field(..., description="Account number")
    eligibleForAutopay: Optional[str] = Field(None, description="Whether eligible for auto pay")
    autopayDiscountAmount: Optional[str] = Field(None, description="Auto pay discount amount")
    greetByName: Optional[str] = Field(None, description="Name to greet by")
    customerName: str = Field(..., description="Customer name")
    customerFirstName: Optional[str] = Field(None, description="Customer first name")
    customerLastName: Optional[str] = Field(None, description="Customer last name")
    lines: List[Line] = Field(default_factory=list, description="List of mobile lines")
    numberOfLines: str = Field(..., description="Number of lines")
    paymentInfo: Optional[PaymentInfo] = Field(None, description="Payment information")
    customerRole: Optional[str] = Field(None, description="Customer role")

class ProfileAfterAuth(BaseModel):
    """Customer profile after authentication"""
    customerProfile: CustomerProfile = Field(..., description="Customer profile")

# ---------------------------
# Root Database Model
# ---------------------------

class CesLoyaltyAuthDB(BaseModel):
    """
    Root model that validates the entire CES Loyalty Auth database structure.
    
    This model ensures all data in the database conforms to the defined schemas
    for conversation status, session status, authentication results, and customer profiles.
    """
    CONVERSATION_STATUS: Optional[ConversationStatus] = Field(
        None,
        description="Current status of the conversation flow."
    )
    SESSION_STATUS: Optional[SessionStatus] = Field(
        None,
        description="Current status of the user session."
    )
    AUTH_RESULT: Optional[AuthResult] = Field(
        None,
        description="Result of the authentication attempt."
    )
    AUTH_STATUS: Optional[AuthStatus] = Field(
        None,
        description="Current authentication status."
    )
    OFFER_ENROLLMENT: Optional[OfferEnrollmentStatus] = Field(
        None,
        description="Status of loyalty offer enrollment."
    )
    PROFILE_BEFORE_AUTH: Optional[ProfileBeforeAuth] = Field(
        None,
        description="Customer profile information before authentication."
    )
    PROFILE_AFTER_AUTH: Optional[ProfileAfterAuth] = Field(
        None,
        description="Customer profile information after authentication."
    )
    use_real_datastore: bool = Field(
        default=False,
        description="Whether to use real datastore or simulation."
    )
    end_of_conversation_status: Dict[str, Any] = Field(
        default_factory=dict,
        alias="_end_of_conversation_status",
        description="End of conversation status information."
    )

    model_config = {"str_strip_whitespace": True}
