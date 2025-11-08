from typing import Optional, List, Literal, Dict, Any, Union
from pydantic import BaseModel, Field, conint, ConfigDict, constr, HttpUrl, field_validator
from datetime import datetime

class PydanticTransactionalEmailMessage(BaseModel):
    to: str = Field(..., description="Email address of the recipient.")
    from_: Optional[str] = Field(None, description="Email address of the sender.")
    subject: Optional[str] = Field(None, description="Subject line of the email.")
    htmlBody: Optional[str] = Field(None, description="HTML content of the email.")
    cc: Optional[List[str]] = Field(None, description="CC recipient email address(es).")
    bcc: Optional[List[str]] = Field(None, description="BCC recipient email address(es).")
    replyTo: Optional[str] = Field(None, description="Reply-to email address.")



# Pydantic models for validation
class CommunicationCheckbox(BaseModel):
    """Model for communication checkbox in consent options."""
    subscriptionTypeId: int = Field(..., description="The subscription type ID")
    label: str = Field(..., description="The main label for the form field")
    required: bool = Field(..., description="Whether this checkbox is required")

class ExplicitConsentToProcess(BaseModel):
    """Model for explicit consent to process options."""
    communicationsCheckboxes: List[CommunicationCheckbox] = Field(..., description="List of communication checkboxes")
    communicationConsentText: str = Field(..., description="Communication consent text")
    consentToProcessCheckboxLabel: str = Field(..., description="Label for consent checkbox")
    consentToProcessFooterText: str = Field(..., description="Footer text for consent")
    type: str = Field(..., description="Type of consent")
    privacyText: str = Field(..., description="Privacy text")
    consentToProcessText: str = Field(..., description="Consent to process text")

class ImplicitConsentToProcess(BaseModel):
    """Model for implicit consent to process options."""
    communicationsCheckboxes: List[CommunicationCheckbox] = Field(..., description="List of communication checkboxes")
    communicationConsentText: str = Field(..., description="Communication consent text")
    type: str = Field(..., description="Type of consent")
    privacyText: str = Field(..., description="Privacy text")
    consentToProcessText: str = Field(..., description="Consent to process text")

class LegitimateInterest(BaseModel):
    """Model for legitimate interest options."""
    lawfulBasis: str = Field(..., description="The lawful basis for the consent")
    type: str = Field(..., description="The type of the legitimate interest")
    privacyText: str = Field(..., description="The privacy text of the legitimate interest")

class LegalConsentOptions(BaseModel):
    """Model for legal consent options."""
    explicitConsentToProcess: Optional[ExplicitConsentToProcess] = Field(None, description="Explicit consent options")
    implicitConsentToProcess: Optional[ImplicitConsentToProcess] = Field(None, description="Implicit consent options")
    legitimateInterest: Optional[LegitimateInterest] = Field(None, description="Legitimate interest options")

class FormField(BaseModel):
    """Model for form field validation."""
    fieldType: Literal[
        "email", "phone", "mobile_phone", "single_line_text", "multi_line_text", 
        "number", "single_checkbox", "multiple_checkboxes", "dropdown", "radio", 
        "datepicker", "file", "payment_link_radio"
    ] = Field(..., description="The type of the field")
    name: str = Field(..., description="The name of the field")
    label: str = Field(..., description="The label of the field")
    required: bool = Field(..., description="Whether the field is required")
    placeholder: Optional[str] = Field(None, description="The placeholder text of the field")
    defaultValue: Optional[str] = Field(None, description="The default value of the field")
    options: Optional[List[str]] = Field(None, description="The options of the field")
    hidden: Optional[bool] = Field(False, description="Whether the field is hidden")

class FieldGroup(BaseModel):
    """Model for field group validation."""
    groupType: str = Field(..., description="The type of the field group")
    richTextType: str = Field("text", description="The type of rich text included. The default value is text.")
    richText: str = Field("", description="A block of rich text or an image")
    fields: List[FormField] = Field(..., description="The fields of the field group")

class CreateFormRequest(BaseModel):
    """Model for create form request validation."""
    fieldGroups: List[FieldGroup] = Field(..., description="The field groups of the form")
    legalConsentOptions: Optional[LegalConsentOptions] = Field(None, description="The legal consent options of the form")

class UpdateFormRequest(BaseModel):
    """Model for update form request validation."""
    fieldGroups: Optional[List[FieldGroup]] = Field(None, description="The new field groups of the form")
    legalConsentOptions: Optional[LegalConsentOptions] = Field(None, description="The new legal consent options of the form")

class HubSpotEmailUser(BaseModel):
    email: str = Field(..., description="Email address of the user", min_length=1)
    name: Optional[str] = Field(None, description="Name of the user")

class HubSpotEmailMessage(BaseModel):
    to: List[HubSpotEmailUser] = Field(..., description="List of recipients")
    cc: Optional[List[HubSpotEmailUser]] = Field(None, description="List of CC recipients")
    bcc: Optional[List[HubSpotEmailUser]] = Field(None, description="List of BCC recipients")
    from_: Optional[HubSpotEmailUser] = Field(None, description="Sender")
    replyTo: Optional[List[HubSpotEmailUser]] = Field(None, description="Reply-to address")

class SendSingleEmailRequest(BaseModel):
    """Model for send single email request validation."""
    template_id: str = Field(..., description="The ID of the pre-existing transactional email template to send", min_length=1)
    message: HubSpotEmailMessage = Field(..., description="Email message containing recipient and sender info")
    customProperties: Optional[dict] = Field({}, description="Custom property values for template personalization")
    contactProperties: Optional[dict] = Field({}, description="Contact property values")

class GetEventsParams(BaseModel):
    occurredAfter: Optional[datetime] = None
    occurredBefore: Optional[datetime] = None
    limit: conint(ge=1, le=100) = 10
    after: Optional[str] = None

    @field_validator('occurredAfter', 'occurredBefore', mode='before')
    def parse_datetime(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value

class SubscriptionDetails(BaseModel):
    model_config = ConfigDict(extra='allow')
    contact_id: Optional[str] = None
    subscribed: Optional[bool] = None
    opt_in_date: Optional[str] = None

class CreateSubscriptionModel(BaseModel):
    model_config = ConfigDict(extra='allow')
    
    endpoint: Optional[str] = Field(None, description="The endpoint of the subscription definition. Optional.")
    subscriptionDetails: Optional[SubscriptionDetails] = Field(None, description="The subscription details of the subscription definition. Optional.") 

class UpdateEventCustomProperties(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
    sourceId: Optional[str] = Field(None, description="The source id of the custom property. Optional.")
    selectedByUser: Optional[bool] = Field(None, description="Whether the property was selected by the user. Optional.")
    sourceLabel: Optional[str] = Field(None, description="The label of the source. Optional.")
    source: Optional[str] = Field(None, description="The source of the property. Optional.")
    updatedByUserId: Optional[int] = Field(None, description="The id of the user who last updated the property. Optional.")
    persistenceTimestamp: Optional[int] = Field(None, description="The timestamp of the property. Optional.")
    sourceMetadata: Optional[str] = Field(None, description="The metadata of the source. Optional.")
    dataSensitivity: Optional[str] = Field(None, description="The data sensitivity of the property. Optional.")
    unit: Optional[str] = Field(None, description="The unit of the property. Optional.")
    requestId: Optional[str] = Field(None, description="The request id of the property. Optional.")
    isEncrypted: Optional[bool] = Field(None, description="Whether the property is encrypted. Optional.")
    name: Optional[str] = Field(None, description="The name of the property. Optional.")
    useTimestampAsPersistenceTimestamp: Optional[bool] = Field(None, description="Whether to use timestamp as persistence timestamp. Optional.")
    value: Optional[str] = Field(None, description="The value of the property. Optional.")
    selectedByUserTimestamp: Optional[int] = Field(None, description="The timestamp of the property. Optional.")
    timestamp: Optional[int] = Field(None, description="The timestamp of the property. Optional.")
    isLargeValue: Optional[bool] = Field(None, description="Whether the property is large. Optional.")
    endpoint: Optional[str] = None
    subscriptionDetails: SubscriptionDetails
    active: bool = True


class CreateEventRequest(BaseModel):
    externalEventId: constr(min_length=1)
    externalAccountId: constr(min_length=1)
    eventName: constr(min_length=1)
    eventType: constr(min_length=1)
    eventOrganizer: constr(min_length=1)
    startDateTime: Optional[datetime] = None
    endDateTime: Optional[datetime] = None
    eventDescription: Optional[str] = None
    eventUrl: Optional[HttpUrl] = None
    customProperties: Optional[List[Dict[str, Union[str, int, bool, float]]]] = None
    
    

    @field_validator('startDateTime', 'endDateTime', mode='before')
    def parse_datetime(cls, value):
        if value:
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        return value


class CancelMarketingEventRequest(BaseModel):
    """Model for cancel marketing event request validation."""
    externalEventId: str = Field(..., description="The unique identifier for the marketing event as per the external system where the event was created", min_length=1)
    externalAccountId: str = Field(..., description="The unique identifier for the account where the event was created", min_length=1)


class GetFormsInputModel(BaseModel):
    """Pydantic model for validating get_forms input parameters."""
    after: Optional[str] = Field(None, description="The ID of the form to start after for pagination")
    limit: Optional[int] = Field(None, ge=1, description="The maximum number of forms to return per page")
    created_at: Optional[str] = Field(None, description="Filter by the exact date the form was created (ISO 8601 format)")
    created_at__gt: Optional[str] = Field(None, description="Filter for forms created after this date (ISO 8601 format)")
    created_at__gte: Optional[str] = Field(None, description="Filter for forms created on or after this date (ISO 8601 format)")
    created_at__lt: Optional[str] = Field(None, description="Filter for forms created before this date (ISO 8601 format)")
    created_at__lte: Optional[str] = Field(None, description="Filter for forms created on or before this date (ISO 8601 format)")
    updated_at: Optional[str] = Field(None, description="Filter by the exact date the form was last updated (ISO 8601 format)")
    updated_at__gt: Optional[str] = Field(None, description="Filter for forms updated after this date (ISO 8601 format)")
    updated_at__gte: Optional[str] = Field(None, description="Filter for forms updated on or after this date (ISO 8601 format)")
    updated_at__lt: Optional[str] = Field(None, description="Filter for forms updated before this date (ISO 8601 format)")
    updated_at__lte: Optional[str] = Field(None, description="Filter for forms updated on or before this date (ISO 8601 format)")
    name: Optional[str] = Field(None, description="Filter by the exact name of the form")
    id: Optional[str] = Field(None, description="Filter by the exact ID of the form")
    archived: Optional[bool] = Field(None, description="Filter by the archived status of the form")


class DeleteAttendeeRequest(BaseModel):
    """Model for delete attendee request validation."""
    externalEventId: str = Field(..., description="The unique identifier for the marketing event as per the external system where the event was created", min_length=1)
    attendeeId: str = Field(..., description="The unique identifier for the attendee", min_length=1)
    externalAccountId: str = Field(..., description="The unique identifier for the account where the event was created", min_length=1)
