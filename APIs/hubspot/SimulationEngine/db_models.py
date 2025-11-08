from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr, Field, ConfigDict, HttpUrl
from datetime import datetime
from enum import Enum

# =============================================================================
# Database Object Models for HubspotMarketingDefaultDB
# =============================================================================

# -------------------------
# Transactional Emails
# -------------------------

class TransactionalEmailMessage(BaseModel):
    """Model for transactional email message content."""
    to: EmailStr = Field(..., description="Email address of the recipient", min_length=1)
    from_: EmailStr = Field(..., alias="from", description="Email address of the sender", min_length=1)
    subject: str = Field(..., description="Subject line of the email")
    htmlBody: str = Field(..., description="HTML content of the email")


class TransactionalEmailStatusEnum(str, Enum):
    """Represents the current status of a transactional email."""
    SENT = "sent"
    PENDING = "pending"
    SCHEDULED = "scheduled"
    FAILED = "failed"


class CustomProperties(BaseModel):
    """Model for custom properties dictionary."""
    model_config = ConfigDict(extra='allow', validate_assignment=True)


class TransactionalEmail(BaseModel):
    """Model for a transactional email in the database."""
    model_config = ConfigDict(extra='allow')

    message: TransactionalEmailMessage = Field(..., description="The email message content")
    customProperties: Optional[CustomProperties] = Field(
        default=None,
        description="Custom properties for the email (e.g., order_id, priority)"
    )
    status: TransactionalEmailStatusEnum = Field(
        ...,
        description="The current status of the email"
    )
    emailId: str = Field(..., description="Unique identifier for the email", min_length=1)


# -------------------------
# Marketing Emails
# -------------------------

class MarketingEmailStatus(str, Enum):
    """Enum for marketing email statuses."""
    SENT = "sent"
    PENDING = "pending"
    SCHEDULED = "scheduled"
    DRAFT = "draft"

class MarketingEmail(BaseModel):
    """Model for a marketing email in the database."""
    model_config = ConfigDict(extra='allow')

    name: str = Field(..., description="Name of the marketing email", min_length=1)
    subject: str = Field(..., description="Subject line of the email", min_length=1)
    htmlBody: str = Field(..., description="HTML content of the email")
    isTransactional: bool = Field(
        False, description="Whether this is a transactional email"
    )
    status: MarketingEmailStatus = Field(
        ..., description="The current status of the marketing email"
    )

    # Optional fields for specific email types
    discount_code: Optional[str] = Field(None, description="Discount code for promotional emails")
    expiration: Optional[str] = Field(None, description="Expiration date for the discount code (YYYY-MM-DD)")
    launch_date: Optional[str] = Field(None, description="Launch date for product launch emails (YYYY-MM-DD)")
    sale_end_date: Optional[str] = Field(None, description="End date for sale emails (YYYY-MM-DD)")
    reward_points: Optional[int] = Field(None, description="Reward points for loyalty program emails")
    access_code: Optional[str] = Field(None, description="Access code for VIP or early access emails")


# -------------------------
# Events
# -------------------------

class Event(BaseModel):
    """Model for an event in the database."""
    model_config = ConfigDict(extra='forbid')

    event_id: str = Field(..., description="Unique identifier for the event", min_length=1)
    event_name: str = Field(..., description="Name of the event", min_length=1)
    start_time: datetime = Field(
        ...,
        description="Start time of the event in ISO 8601 format"
    )
    end_time: datetime = Field(
        ...,
        description="End time of the event in ISO 8601 format"
    )


# -------------------------
# Attendees
# -------------------------

class AttendeeStatus(str, Enum):
    """Enum for attendee status values."""
    ATTENDED = "Attended"
    REGISTERED = "Registered"
    NO_SHOW = "No-show"
    CANCELLED = "Cancelled"


class Attendee(BaseModel):
    """Model for an event attendee in the database."""
    model_config = ConfigDict(extra='forbid')

    attendee_id: str = Field(..., description="Unique identifier for the attendee", min_length=1)
    event_id: str = Field(..., description="ID of the event the attendee is registered for", min_length=1)
    contact_id: str = Field(..., description="ID of the contact", min_length=1)
    registration_date: datetime = Field(
        ...,
        description="Date when the attendee registered in ISO 8601 format"
    )
    status: AttendeeStatus = Field(
        ...,
        description="Current status of the attendee"
    )


# -------------------------
# Templates
# -------------------------

class TemplateVersion(BaseModel):
    """Model for a template version."""
    source: str = Field(..., description="The source content of the template version")
    version_id: str = Field(..., description="The version identifier", min_length=1)


class Template(BaseModel):
    """Model for an email template in the database."""
    model_config = ConfigDict(extra='allow')

    id: str = Field(..., description="Unique identifier for the template", min_length=1)
    category_id: int = Field(..., description="Category ID for the template")
    folder: Optional[str] = Field(None, description="Folder path for the template")
    template_type: int = Field(..., description="Type of the template")
    source: str = Field(..., description="The source content of the template")
    path: Optional[str] = Field(None, description="Path to the template file")
    created: str = Field(..., description="Creation timestamp in milliseconds", min_length=1)
    deleted_at: Optional[str] = Field(None, description="Deletion timestamp if deleted")
    is_available_for_new_content: bool = Field(
        ...,
        description="Whether the template is available for new content"
    )
    archived: bool = Field(..., description="Whether the template is archived")
    versions: List[TemplateVersion] = Field(
        default_factory=list,
        description="List of template versions"
    )


# -------------------------
# Contacts
# -------------------------

class LifecycleStage(str, Enum):
    """Enum for contact lifecycle stages."""
    SUBSCRIBER = "subscriber"
    LEAD = "lead"
    MARKETING_QUALIFIED_LEAD = "marketingqualifiedlead"
    SALES_QUALIFIED_LEAD = "salesqualifiedlead"
    OPPORTUNITY = "opportunity"
    CUSTOMER = "customer"
    EVANGELIST = "evangelist"
    OTHER = "other"


class LeadStatus(str, Enum):
    """Enum for lead status values."""
    NEW = "NEW"
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    OPEN_DEAL = "OPEN_DEAL"
    UNQUALIFIED = "UNQUALIFIED"
    ATTEMPTED_TO_CONTACT = "ATTEMPTED_TO_CONTACT"
    CONNECTED = "CONNECTED"
    BAD_TIMING = "BAD_TIMING"


class Contact(BaseModel):
    """Model for a contact in the database."""
    model_config = ConfigDict(extra='allow')

    contact_id: str = Field(..., description="Unique identifier for the contact", min_length=1)
    first_name: str = Field(..., description="First name of the contact", min_length=1)
    last_name: str = Field(..., description="Last name of the contact", min_length=1)
    email: EmailStr = Field(
        ...,
        description="Email address of the contact",
        min_length=1
    )
    phone_number: Optional[str] = Field(
        None,
        description="Phone number of the contact in international format"
    )
    job_title: Optional[str] = Field(None, description="Job title of the contact")
    company: Optional[str] = Field(None, description="Company name")
    created_at: datetime = Field(
        ...,
        description="Date when the contact was created in ISO 8601 format"
    )
    updated_at: datetime = Field(
        ...,
        description="Date when the contact was last updated in ISO 8601 format"
    )
    lifecycle_stage: LifecycleStage = Field(
        ...,
        description="Current lifecycle stage of the contact"
    )
    lead_status: LeadStatus = Field(..., description="Current lead status")


# -------------------------
# Campaigns
# -------------------------

class CampaignStatus(str, Enum):
    """Enum for campaign status values."""
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class Campaign(BaseModel):
    """Model for a marketing campaign in the database."""
    model_config = ConfigDict(extra='allow')

    campaign_id: str = Field(..., description="Unique identifier for the campaign", min_length=1)
    campaign_name: str = Field(..., description="Name of the campaign", min_length=1)
    start_date: datetime = Field(
        ...,
        description="Start date of the campaign in ISO 8601 format"
    )
    end_date: datetime = Field(
        ...,
        description="End date of the campaign in ISO 8601 format"
    )
    status: CampaignStatus = Field(..., description="Current status of the campaign")
    budget: float = Field(
        ...,
        description="Budget allocated for the campaign",
        ge=0.0
    )
    target_audience: str = Field(..., description="Target audience for the campaign", min_length=1)
    utm_campaign: str = Field(
        ...,
        description="UTM campaign parameter for tracking",
        min_length=1
    )


# -------------------------
# Forms
# -------------------------

class Form(BaseModel):
    """Model for a form in the database."""
    model_config = ConfigDict(extra='allow')

    form_id: str = Field(..., description="Unique identifier for the form", min_length=1)
    form_name: str = Field(..., description="Name of the form", min_length=1)
    fields: List[str] = Field(
        ...,
        description="List of field names in the form",
        min_length=1
    )
    submit_text: str = Field(..., description="Text displayed on the submit button", min_length=1)
    redirect_url: str = Field(..., description="URL to redirect to after form submission", min_length=1)
    created_at: datetime = Field(
        ...,
        description="Date when the form was created in ISO 8601 format"
    )
    updated_at: datetime = Field(
        ...,
        description="Date when the form was last updated in ISO 8601 format"
    )


# -------------------------
# Marketing Events
# -------------------------

class MarketingEventAttendees(BaseModel):
    """Model for marketing event attendees dictionary."""
    model_config = ConfigDict(extra='allow', validate_assignment=True)


class MarketingEventCustomProperty(BaseModel):
    """Model for custom properties of a marketing event."""
    model_config = ConfigDict(extra='allow')

    sourceId: Optional[str] = Field(None, description="The source ID of the property")
    selectedByUser: Optional[bool] = Field(None, description="Whether selected by user")
    sourceLabel: Optional[str] = Field(None, description="Label of the source")
    source: Optional[str] = Field(None, description="Source of the property")
    updatedByUserId: Optional[int] = Field(None, description="ID of the user who updated")
    persistenceTimestamp: Optional[int] = Field(None, description="Persistence timestamp")
    sourceMetadata: Optional[str] = Field(None, description="Metadata of the source")
    dataSensitivity: Optional[str] = Field(None, description="Data sensitivity level")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    requestId: Optional[str] = Field(None, description="Request ID")
    isEncrypted: Optional[bool] = Field(None, description="Whether the value is encrypted")
    name: str = Field(..., description="Name of the custom property", min_length=1)
    useTimestampAsPersistenceTimestamp: Optional[bool] = Field(
        None,
        description="Whether to use timestamp as persistence timestamp"
    )
    value: Optional[str] = Field(None, description="Value of the property")
    selectedByUserTimestamp: Optional[int] = Field(None, description="User selection timestamp")
    timestamp: Optional[int] = Field(None, description="Property timestamp")
    isLargeValue: Optional[bool] = Field(None, description="Whether the value is large")


class MarketingEvent(BaseModel):
    """Model for a marketing event in the database."""
    model_config = ConfigDict(extra='allow')

    customProperties: Optional[List[MarketingEventCustomProperty]] = Field(
        default_factory=list,
        description="Custom properties for the event"
    )
    endDateTime: datetime = Field(
        ...,
        description="End date and time of the event in ISO 8601 format"
    )
    eventDescription: str = Field(..., description="Description of the event")
    eventName: str = Field(..., description="Name of the event", min_length=1)
    eventOrganizer: str = Field(..., description="Organizer of the event", min_length=1)
    eventType: str = Field(..., description="Type of the event", min_length=1)
    eventUrl: HttpUrl = Field(..., description="URL for the event")
    externalAccountId: str = Field(
        ...,
        description="External account identifier",
        min_length=1
    )
    externalEventId: str = Field(
        ...,
        description="External event identifier",
        min_length=1
    )
    startDateTime: datetime = Field(
        ...,
        description="Start date and time of the event in ISO 8601 format"
    )
    attendees: MarketingEventAttendees = Field(
        default_factory=MarketingEventAttendees,
        description="Attendees information for the event"
    )
    # Additional fields for detailed marketing events
    registrants: Optional[int] = Field(None, description="Number of registrants", ge=0)
    eventCancelled: Optional[bool] = Field(None, description="Whether the event is cancelled")
    noShows: Optional[int] = Field(None, description="Number of no-shows", ge=0)
    cancellations: Optional[int] = Field(None, description="Number of cancellations", ge=0)
    id: Optional[str] = Field(None, description="Internal ID of the event")
    objectId: Optional[str] = Field(None, description="Object ID of the event")
    createdAt: Optional[datetime] = Field(None, description="Creation timestamp")
    updatedAt: Optional[datetime] = Field(None, description="Last update timestamp")


# -------------------------
# Subscription Definitions
# -------------------------

class SubscriptionFrequency(str, Enum):
    """Enum for subscription frequency values."""
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    ANNUALLY = "Annually"


class SubscriptionDefinition(BaseModel):
    """Model for a subscription definition in the database."""
    model_config = ConfigDict(extra='allow')

    subscription_id: str = Field(..., description="Unique identifier for the subscription", min_length=1)
    name: str = Field(..., description="Name of the subscription", min_length=1)
    description: str = Field(..., description="Description of the subscription")
    frequency: SubscriptionFrequency = Field(
        ...,
        description="Frequency of the subscription"
    )
    active: bool = Field(..., description="Whether the subscription is active")


# -------------------------
# Subscriptions
# -------------------------

class SubscriptionDetails(BaseModel):
    """Model for subscription details."""
    model_config = ConfigDict(extra='allow')

    contact_id: Optional[str] = Field(None, description="ID of the contact")
    subscription_id: Optional[str] = Field(None, description="ID of the subscription")
    subscribed: Optional[bool] = Field(None, description="Whether the contact is subscribed")
    opt_in_date: Optional[datetime] = Field(None, description="Date when the contact opted in")
    registration_date: Optional[datetime] = Field(None, description="Registration date")
    status: Optional[str] = Field(None, description="Status of the subscription")


class Subscription(BaseModel):
    """Model for a subscription in the database."""
    model_config = ConfigDict(extra='allow')

    id: str = Field(..., description="Unique identifier for the subscription", min_length=1)
    endpoint: Optional[str] = Field(None, description="Endpoint URL for the subscription")
    subscriptionDetails: SubscriptionDetails = Field(
        ...,
        description="Details of the subscription"
    )
    active: bool = Field(True, description="Whether the subscription is active")


# -------------------------
# Subscription Campaign Details
# -------------------------

class SubscriptionCampaignDetails(BaseModel):
    """Model for detailed campaign information within subscriptions."""
    model_config = ConfigDict(extra='allow')

    id: str = Field(..., description="Campaign ID", min_length=1)
    name: str = Field(..., description="Campaign name", min_length=1)
    slug: str = Field(..., description="URL-friendly campaign slug", min_length=1)
    description: str = Field(..., description="Campaign description")
    start_year: int = Field(..., description="Start year of the campaign", ge=2000, le=2100)
    start_month: int = Field(..., description="Start month (1-12)", ge=1, le=12)
    start_day: int = Field(..., description="Start day (1-31)", ge=1, le=31)
    end_year: int = Field(..., description="End year of the campaign", ge=2000, le=2100)
    end_month: int = Field(..., description="End month (1-12)", ge=1, le=12)
    end_day: int = Field(..., description="End day (1-31)", ge=1, le=31)
    theme: str = Field(..., description="Theme of the campaign", min_length=1)
    resource: str = Field(..., description="Resource name", min_length=1)
    color_label: str = Field(..., description="Color label for the campaign", min_length=1)
    created_at: datetime = Field(
        ...,
        description="Creation timestamp in ISO 8601 format"
    )


# -------------------------
# Subscription Form Details
# -------------------------

class SubscriptionFormField(BaseModel):
    """Model for a field in a subscription form."""
    fieldType: str = Field(..., description="Type of the field", min_length=1)
    name: str = Field(..., description="Name of the field", min_length=1)
    label: str = Field(..., description="Display label for the field", min_length=1)
    required: bool = Field(..., description="Whether the field is required")
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    defaultValue: Optional[str] = Field(None, description="Default value")
    options: Optional[List[str]] = Field(None, description="Options for select/radio fields")
    hidden: Optional[bool] = Field(False, description="Whether the field is hidden")


class SubscriptionFormFieldGroup(BaseModel):
    """Model for a field group in a subscription form."""
    groupType: str = Field(..., description="Type of the field group", min_length=1)
    richTextType: str = Field(..., description="Type of rich text", min_length=1)
    richText: str = Field(..., description="Rich text content")
    fields: List[SubscriptionFormField] = Field(
        ...,
        description="List of fields in the group",
        min_length=1
    )


class SubscriptionFormCommunicationCheckbox(BaseModel):
    """Model for communication checkbox in consent options."""
    subscriptionTypeId: int = Field(..., description="Subscription type ID")
    label: str = Field(..., description="Label for the checkbox", min_length=1)
    required: bool = Field(..., description="Whether the checkbox is required")


class SubscriptionFormExplicitConsent(BaseModel):
    """Model for explicit consent options."""
    communicationsCheckboxes: List[SubscriptionFormCommunicationCheckbox] = Field(
        ...,
        description="List of communication checkboxes"
    )
    communicationConsentText: str = Field(..., description="Communication consent text")
    consentToProcessCheckboxLabel: str = Field(..., description="Consent checkbox label")
    consentToProcessFooterText: str = Field(..., description="Footer text")
    type: str = Field(..., description="Type of consent", min_length=1)
    privacyText: str = Field(..., description="Privacy text")
    consentToProcessText: str = Field(..., description="Consent to process text")


class SubscriptionFormLegalConsent(BaseModel):
    """Model for legal consent options in forms."""
    explicitConsentToProcess: Optional[SubscriptionFormExplicitConsent] = Field(
        None,
        description="Explicit consent options"
    )


class SubscriptionFormDetails(BaseModel):
    """Model for detailed form information within subscriptions."""
    model_config = ConfigDict(extra='allow')

    id: str = Field(..., description="Form ID", min_length=1)
    name: str = Field(..., description="Form name", min_length=1)
    submitText: str = Field(..., description="Submit button text", min_length=1)
    fieldGroups: List[SubscriptionFormFieldGroup] = Field(
        ...,
        description="List of field groups in the form",
        min_length=1
    )
    legalConsentOptions: Optional[SubscriptionFormLegalConsent] = Field(
        None,
        description="Legal consent options"
    )
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")


# -------------------------
# Subscription Marketing Event Details
# -------------------------

class SubscriptionMarketingEventDetails(BaseModel):
    """Model for detailed marketing event information within subscriptions."""
    model_config = ConfigDict(extra='allow')

    registrants: int = Field(..., description="Number of registrants", ge=0)
    attendees: int = Field(..., description="Number of attendees", ge=0)
    eventOrganizer: str = Field(..., description="Event organizer", min_length=1)
    eventUrl: HttpUrl = Field(..., description="Event URL")
    eventType: str = Field(..., description="Type of event", min_length=1)
    noShows: int = Field(..., description="Number of no-shows", ge=0)
    cancellations: int = Field(..., description="Number of cancellations", ge=0)
    eventDescription: str = Field(..., description="Event description")
    eventName: str = Field(..., description="Event name", min_length=1)
    eventCancelled: Optional[bool] = Field(None, description="Whether event is cancelled")
    customProperties: Optional[List[MarketingEventCustomProperty]] = Field(
        default_factory=list,
        description="Custom properties"
    )
    endDateTime: datetime = Field(..., description="End date and time")
    startDateTime: datetime = Field(..., description="Start date and time")
    externalAccountId: str = Field(..., description="External account ID", min_length=1)
    externalEventId: str = Field(..., description="External event ID", min_length=1)
    id: str = Field(..., description="Event ID", min_length=1)
    objectId: str = Field(..., description="Object ID", min_length=1)
    createdAt: datetime = Field(..., description="Creation timestamp")
    updatedAt: datetime = Field(..., description="Last update timestamp")


# -------------------------
# Subscription Definition in Subscription
# -------------------------

class SubscriptionDefinitionInSubscription(BaseModel):
    """Model for subscription definition within a subscription object."""
    model_config = ConfigDict(extra='allow')

    subscription_id: Optional[str] = Field(None, description="Subscription ID")
    name: Optional[str] = Field(None, description="Name of the subscription")
    description: Optional[str] = Field(None, description="Description")
    frequency: Optional[str] = Field(None, description="Frequency")
    active: Optional[bool] = Field(None, description="Whether active")
    subscribed: Optional[bool] = Field(None, description="Whether subscribed")
    opt_in_date: Optional[datetime] = Field(None, description="Opt-in date")


# =============================================================================
# Complete Database Model
# =============================================================================

class SubscriptionEntry(BaseModel):
    """Model for subscription entry with flexible nested structure."""
    model_config = ConfigDict(extra='allow', validate_assignment=True)


class HubSpotMarketingDatabase(BaseModel):
    """Model for the entire HubSpot Marketing database."""
    model_config = ConfigDict(extra='allow')

    transactional_emails: Dict[str, List[TransactionalEmail]] = Field(
        default_factory=dict,
        description="Dictionary of transactional emails keyed by email ID"
    )
    marketing_emails: Dict[str, MarketingEmail] = Field(
        default_factory=dict,
        description="Dictionary of marketing emails keyed by email ID"
    )
    events: Dict[str, Event] = Field(
        default_factory=dict,
        description="Dictionary of events keyed by event ID"
    )
    attendees: Dict[str, Attendee] = Field(
        default_factory=dict,
        description="Dictionary of attendees keyed by attendee ID"
    )
    templates: Dict[str, Template] = Field(
        default_factory=dict,
        description="Dictionary of templates keyed by template ID"
    )
    contacts: Dict[str, Contact] = Field(
        default_factory=dict,
        description="Dictionary of contacts keyed by contact ID"
    )
    campaigns: Dict[str, Campaign] = Field(
        default_factory=dict,
        description="Dictionary of campaigns keyed by campaign ID"
    )
    forms: Dict[str, Form] = Field(
        default_factory=dict,
        description="Dictionary of forms keyed by form ID"
    )
    marketing_events: Dict[str, MarketingEvent] = Field(
        default_factory=dict,
        description="Dictionary of marketing events keyed by event ID"
    )
    subscription_definitions: List[SubscriptionDefinition] = Field(
        default_factory=list,
        description="List of subscription definitions"
    )
    subscriptions: Dict[str, SubscriptionEntry] = Field(
        default_factory=dict,
        description="Dictionary of subscriptions with nested structure"
    )
