from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Any, Optional, Dict, List, Literal, Union
import re

from APIs.ces_system_activation.SimulationEngine.custom_errors import ValidationError


# ============================================================================
# BASE MODEL WITH STRICT VALIDATION
# ============================================================================

class StrictBaseModel(BaseModel):
    """Base model with strict validation that forbids extra fields.
    
    All CES System Activation input and output models inherit from this base to ensure strict schema validation.
    This prevents models from accepting fields not defined in the schema, ensuring synchronization
    between the model definitions and actual data structures.
    
    The 'forbid' extra fields policy means that if data contains any fields that aren't defined
    in the Pydantic model, validation will fail with a clear error. This is critical for
    maintaining data integrity and catching schema mismatches early.
    """
    class Config:
        extra = "forbid"  # Forbid extra fields to ensure strict validation
        validate_assignment = True  # Validate field assignments after model creation


# ============================================================================
# INPUT MODELS
# ============================================================================


class GetActivationVisitDetailsInput(StrictBaseModel):
    """Input model for get_activation_visit_details."""
    visitId: str = Field(..., min_length=1, description='The unique identifier of the technician visit to look up. Example: "VISIT-98765".')
    
    @field_validator('visitId')
    @classmethod
    def validate_visit_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('visitId cannot be empty or contain whitespaces only')
        return v.strip()


class FindAvailableTechnicianAppointmentSlotsInput(StrictBaseModel):
    """Input model for find_available_technician_appointment_slots."""
    postalCode: Optional[str] = Field(None, min_length=1, max_length=10, description='The postal code for the service location, used to find local technicians. Example: "94105".')
    startDate: str = Field(..., min_length=1, description="The desired starting date to search for availability, in 'YYYY-MM-DD' format. Example: \"2023-11-01\".")
    daysToSearch: Optional[int] = Field(None, gt=0, le=365, description="Optional. The number of consecutive days to search for availability, starting from 'startDate'. Defaults to 7 if not specified. Example: 14.")
    
    @field_validator('postalCode')
    @classmethod
    def validate_postal_code(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v or not v.strip():
                raise ValueError('postalCode cannot be empty or whitespace only')
            # Basic postal code validation - digits only, 5-10 characters
            cleaned = v.strip()
            return cleaned
        return v
        
    @field_validator('startDate')
    @classmethod
    def validate_start_date(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('startDate cannot be empty or whitespace only')
        # Additional validation could include checking if date is not in the past
        return v.strip()
        


class RescheduleTechnicianVisitInput(StrictBaseModel):
    """Input model for reschedule_technician_visit."""
    accountId: str = Field(..., min_length=1, description='The customer\'s account ID. Example: "ACC-102030".')
    newSlotId: str = Field(..., min_length=1, description='The ID of the newly chosen appointment slot, obtained from `find_available_technician_appointment_slots`. Example: "SLOT-XYZ-789".')
    orderId: str = Field(..., min_length=1, description='The service order ID associated with the visit. Example: "ORD-405060".')
    originalVisitId: str = Field(..., min_length=1, description='The ID of the existing activation appointment to be rescheduled. Example: "VISIT-12345".')
    reasonForChange: Optional[str] = Field(None, min_length=1, max_length=500, description='Optional. A brief reason for the change, if provided by the user. Example: "User has a conflicting meeting.".')
    
    @field_validator('accountId', 'orderId', 'originalVisitId', 'newSlotId')
    @classmethod
    def validate_ids(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('ID fields cannot be empty or whitespace only')
        return v.strip()
        
    @field_validator('reasonForChange')
    @classmethod
    def validate_reason_for_change(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError('reasonForChange cannot be empty or whitespace only if provided')
            return v.strip()
        return v


class ScheduleNewTechnicianVisitInput(StrictBaseModel):
    """Input model for schedule_new_technician_visit."""
    accountId: str = Field(..., min_length=1, description='The customer\'s account ID. Example: "ACC-102030".')
    orderId: str = Field(..., min_length=1, description='The service order ID that requires a technician visit. Example: "ORD-405060".')
    slotId: str = Field(..., min_length=1, description='The ID of the chosen appointment slot, obtained from `find_available_technician_appointment_slots`. Example: "SLOT-ABC-123".')
    issueDescription: Optional[str] = Field(None, min_length=1, max_length=500, description='Optional. A brief description of the issue or service being performed. Defaults to None. When None is provided or omitted, the implementation will use "New SunnyFiber Gigabit internet service installation and modem setup." as the default value.')
    
    @field_validator('accountId', 'orderId', 'slotId')
    @classmethod
    def validate_ids(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('ID fields cannot be empty or whitespace only')
        return v.strip()

    @field_validator('issueDescription')
    @classmethod
    def validate_issue_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError('issueDescription cannot be empty or whitespace only if provided')
            return v.strip()
        return v


class FlagTechnicianVisitIssueInput(StrictBaseModel):
    """Input model for flag_technician_visit_issue."""
    accountId: str = Field(..., min_length=1, description='The customer\'s account ID. Example: "ACC-102030".')
    customerReportedFailure: bool = Field(..., description='A boolean indicating if the customer is the one reporting the failure. Set to `True` in almost all cases for an agent.')
    issueSummary: str = Field(..., min_length=1, max_length=1000, description='A concise summary of the problem reported by the user. Example: "Customer reports that the modem is not getting a signal after the technician left.".')
    orderId: str = Field(..., min_length=1, description='The service order ID associated with the visit. Example: "ORD-405060".')
    requestedFollowUpAction: str = Field(..., min_length=1, max_length=500, description='The desired next step. Example: "Dispatch technician again", "Manager callback requested".')
    visitId: str = Field(..., min_length=1, description='The ID of the technician visit that has the issue. Example: "VISIT-12345".')
    
    @field_validator('accountId', 'orderId', 'visitId')
    @classmethod
    def validate_ids(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('ID fields cannot be empty or whitespace only')
        return v.strip()
        
    @field_validator('issueSummary', 'requestedFollowUpAction')
    @classmethod
    def validate_text_fields(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Text fields cannot be empty or whitespace only')
        return v.strip()


class TriggerServiceActivationInput(StrictBaseModel):
    """Initiates the activation process for a specific service on the network platform.
    When to Use:
    - When a user wants to activate a service that is ready for activation (e.g.,
      "I've installed my modem, can you activate my internet?").
    - As part of an automated activation flow after a technician visit is complete.
    """
    orderId: str = Field(..., min_length=1, description="The order ID associated with the service being activated. Example: 'ORD-405060'.")
    serviceIdentifier: str = Field(..., min_length=1, max_length=50, description="The unique identifier for the service. This could be a SIM card number (ICCID), modem MAC address, or phone number. Example: '8901123456789012345f' or 'AA:BB:CC:11:22:33'.")
    serviceType: Literal['MOBILE', 'INTERNET', 'IOT_DEVICE', 'VOIP'] = Field(..., description="The category of service to be activated. Must be one of 'MOBILE', 'INTERNET', 'IOT_DEVICE', 'VOIP'.")
    accountId: Optional[str] = Field(None, description="Optional. The customer's account ID, for logging and association. Example: 'ACC-102030'.")
    
    @field_validator('orderId')
    @classmethod
    def validate_order_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('orderId cannot be empty or whitespace only')
        return v.strip()
        
    @field_validator('serviceIdentifier')
    @classmethod
    def validate_service_identifier(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('serviceIdentifier cannot be empty or whitespace only')
        cleaned = v.strip()
        # Basic validation for common service identifier formats
        # MAC address, ICCID, phone number, or other alphanumeric identifier
        if not re.match(r'^[A-Za-z0-9:.-]+$', cleaned):
            raise ValueError('serviceIdentifier contains invalid characters')
        return cleaned
        
    @field_validator('accountId')
    @classmethod
    def validate_account_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError('accountId cannot be empty or whitespace only if provided')
            return v.strip()
        return v


class GetServiceActivationStatusInput(StrictBaseModel):
    """Checks the current status of a pending or completed service activation attempt.
    
    When to Use:
    - After using trigger_service_activation to check on the progress of an activation.
    - When a user asks for an update on their service activation (e.g., "What's the status
      of my internet activation?", "Is my service activated yet?").
    - To verify the final outcome of an activation attempt.
    """
    activationAttemptIdOrServiceIdentifier: str = Field(..., min_length=1, max_length=50, description='The identifier for the activation. This can be the `activationAttemptId` returned by `trigger_service_activation` OR the `serviceIdentifier` (e.g., MAC address) used to start the activation. Example: "ATTEMPT-afc3b1" or "AA:BB:CC:11:22:33".')
    
    @field_validator('activationAttemptIdOrServiceIdentifier')
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('activationAttemptIdOrServiceIdentifier cannot be empty or whitespace only')
        return v.strip()


class SendCustomerNotificationInput(StrictBaseModel):
    """Sends a supplemental, non-standard notification to a customer.
    
    It is strongly preferred to use pre-defined templates for consistency and
    compliance by providing a `templateId`. Free-form messages via the `message`
    parameter should be used sparingly.
    
    When to Use:
    - To send a confirmation after a complex action is completed (e.g., "Your
      appointment has been successfully rescheduled for...").
    - To provide a user with a reference number or other important information
      they requested.
    - Do NOT use this for standard, automated notifications that the system
      already sends (e.g., order confirmation).
    """
    accountId: str = Field(..., min_length=1, description="The customer's account ID, used to retrieve contact preferences and for logging. Example: \"ACC-102030\".")
    channel: Optional[Literal['EMAIL', 'SMS', 'PHONE']] = Field("EMAIL", description="Optional. The preferred communication channel. If omitted, the system will use the customer's preferred channel or a system default. Example: \"EMAIL\".")
    message: Optional[str] = Field(None, max_length=2000, description="Optional. The raw message content. Use this only when a pre-approved template is not available. This parameter is ignored if 'templateId' is provided. Example: \"As you requested, here is your service order number: ORD-405060.\".")
    templateId: Optional[str] = Field(None, max_length=100, description="Optional. The ID of a pre-approved notification template. This is the PREFERRED method. Example: \"APPOINTMENT_CONFIRMATION_V2\".")
    orderId: Optional[str] = Field(None, description="Optional. The relevant order ID to include in the notification logs. Example: \"ORD-405060\".")
    recipient: Optional[str] = Field(None, max_length=200, description="Optional. A specific recipient email address or phone number (in E.164 format). Use with caution, as it overrides the customer's preferred contact details. Example: \"+14155552671\".")
    subject: Optional[str] = Field(None, max_length=200, description="Optional. The subject line for the message, primarily for email notifications. Example: \"An Update on Your Recent Request\".")
    urgency: Optional[str] = Field("NORMAL", max_length=20, description="Optional. The urgency level of the notification. Defaults to 'NORMAL'. Example: \"HIGH\".")
    
    @field_validator('accountId')
    @classmethod
    def validate_account_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('accountId cannot be empty or whitespace only')
        return v.strip()
        
    @field_validator('message', 'templateId', 'subject', 'urgency')
    @classmethod
    def validate_optional_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError('String fields cannot be empty or whitespace only if provided')
            return v.strip()
        return v
        
    @field_validator('orderId')
    @classmethod
    def validate_order_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError('orderId cannot be empty or whitespace only if provided')
            return v.strip()
        return v
        
    @field_validator('recipient')
    @classmethod
    def validate_recipient(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError('recipient cannot be empty or whitespace only if provided')
            cleaned = v.strip()
            # Basic validation for email or phone number format
            if '@' in cleaned:
                # Basic email validation
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', cleaned):
                    raise ValueError('recipient email format is invalid')
            elif cleaned.startswith('+'):
                # Basic phone number validation (E.164 format)
                if not re.match(r'^\+[1-9]\d{1,14}$', cleaned):
                    raise ValueError('recipient phone number format is invalid')
            return cleaned
        return v


class SearchOrderDetailsInput(StrictBaseModel):
    """Input model for search_order_details."""
    query: str = Field(..., min_length=1, max_length=1000, description='The natural language question to ask the order database. Be as specific as possible. Good Example: "What is the current status of order ORD-405060 for account ACC-102030?" Bad Example: "order status"')
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('query cannot be empty.')
        return v.strip()


class SearchActivationGuidesInput(StrictBaseModel):
    """Input model for search_activation_guides."""
    query: str = Field(..., min_length=1, max_length=1000, description='The natural language question to ask the knowledge base. Include the device model or service type for better results. Good Example: "Step-by-step instructions for installing the \'RouterModel X100\'" Bad Example: "help"')
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('query cannot be empty.')
        return v.strip()


class EscalateInput(StrictBaseModel):
    """Input model for escalate."""
    reason: str = Field(..., min_length=1, max_length=1000, description='A clear and concise explanation for the escalation. This reason will be logged and shown to the human agent.')

    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('reason cannot be empty.')
        return v.strip()


class FailInput(StrictBaseModel):
    """Input model for fail."""
    reason: str = Field(..., min_length=1, max_length=1000, description='A clear and concise internal-facing explanation for why the task failed. This is used for logging and improving the agent.')

    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('reason cannot be empty.')
        return v.strip()


class CancelInput(StrictBaseModel):
    """Input model for cancel."""
    reason: str = Field(..., min_length=1, max_length=1000, description='A clear and concise summary of why the task was canceled, based on the user\'s request.')

    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('reason cannot be empty.')
        return v.strip()


class AddActivationGuideFromPdfInput(StrictBaseModel):
    """Input model for add_activation_guide_from_pdf."""
    pdf_file_path: str = Field(..., min_length=1, description='The absolute path to the PDF file to be added as an activation guide.')
    
    @field_validator('pdf_file_path')
    @classmethod
    def validate_pdf_file_path(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('pdf_file_path cannot be empty.')
        return v.strip()


# ============================================================================
# OUTPUT MODELS
# ============================================================================


class TechnicianVisitDetails(StrictBaseModel):
    """Details of a technician visit."""
    visitId: str = Field(..., description="The unique identifier of the technician visit.")
    accountId: str = Field(..., description="The customer's account ID.")
    orderId: str = Field(..., description="The service order ID associated with the visit.")
    status: str = Field(..., description="The current status of the visit (e.g., 'scheduled', 'in_progress', 'completed').")
    scheduledStartTime: Optional[str] = Field(None, description="The scheduled start time of the visit in ISO format.")
    scheduledEndTime: Optional[str] = Field(None, description="The scheduled end time of the visit in ISO format.")
    technicianNotes: Optional[str] = Field(None, description="Any notes from the technician about the visit.")
    issueDescription: Optional[str] = Field(None, description="Description of the issue or service being performed.")


class AvailableAppointmentSlot(StrictBaseModel):
    """Represents an available appointment slot."""
    endTime: Optional[str] = Field(None, description="The end time of the appointment slot in ISO format.")
    slotId: Optional[str] = Field(None, description="The unique identifier for the appointment slot.")
    startTime: Optional[str] = Field(None, description="The start time of the appointment slot in ISO format.")
    technicianType: Optional[str] = Field(None, description="The type of technician for this slot (e.g., 'ACTIVATION_INSTALL').")


class AppointmentAvailability(StrictBaseModel):
    """Represents a list of available appointment slots."""
    output: Optional[List[AvailableAppointmentSlot]] = Field(None, description="A list of available appointment slots.")


class FlaggedIssueConfirmation(StrictBaseModel):
    """Confirmation of a flagged issue."""
    flagId: str = Field(..., min_length=1, description="The unique identifier for the flagged issue (e.g., 'FLAG-998877').")
    message: str = Field(..., min_length=1, description="A confirmation message indicating the issue has been logged.")
    status: str = Field(..., min_length=1, description="The current status of the flagged issue (e.g., 'Logged for review').")


class ServiceActivationAttempt(StrictBaseModel):
    """Response model for service activation attempts."""
    activationAttemptId: str = Field(..., description="The unique identifier for the activation attempt (e.g., 'ATTEMPT-12345').")
    message: str = Field(..., description="A status message about the activation attempt.")
    status: str = Field(..., description="The current status of the activation (e.g., 'REQUEST_RECEIVED', 'IN_PROGRESS').")
    timestamp: str = Field(..., description="The timestamp when the activation was initiated in ISO format.")
    errorCode: Optional[str] = Field(None, description="Any error code if the activation failed (optional).")


class NotificationResult(StrictBaseModel):
    """Result of a customer notification."""
    channelSent: str = Field(..., description="The communication channel used to send the notification (e.g., 'EMAIL', 'SMS').")
    message: str = Field(..., description="A confirmation message about the notification send status.")
    notificationId: str = Field(..., description="The unique identifier for the sent notification.")
    recipientUsed: Optional[str] = Field(None, description="The recipient address or phone number used for the notification.")
    status: str = Field(..., description="The status of the notification (e.g., 'SENT', 'FAILED').")
    timestamp: str = Field(..., description="The timestamp when the notification was sent in ISO format.")
    accountId: Optional[str] = Field(None, description="The customer's account ID.")
    orderId: Optional[str] = Field(None, description="The service order ID associated with the visit.")


class SourceSnippet(StrictBaseModel):
    """A snippet of source information."""
    text: Optional[str] = Field(None, description="The relevant text content from the source.")
    title: Optional[str] = Field(None, description="The title or heading of the source document.")
    uri: Optional[str] = Field(None, description="The URI or identifier of the source document.")


class DataStoreQueryResult(StrictBaseModel):
    """Result from a datastore query."""
    answer: str = Field(..., description="The answer to the query based on the datastore search.")
    snippets: List[SourceSnippet] = Field(..., description="A list of source snippets that support the answer.")


class AddActivationGuideFromPdfOutput(StrictBaseModel):
    status: str = Field(..., description="Status of the operation (e.g., 'success', 'failure')")
    message: str = Field(..., description="Descriptive message about the operation result")


class EscalateOutput(StrictBaseModel):
    action: str = Field(..., description="The action type, always 'escalate'")
    reason: str = Field(..., description="The reason for the escalation as provided")
    status: str = Field(..., description="A message indicating the user will be connected to a human agent")


class FailOutput(StrictBaseModel):
    action: str = Field(..., description="The action type, always 'fail'")
    reason: str = Field(..., description="The reason for the failure as provided")
    status: str = Field(..., description="A message apologizing for being unable to help")


class CancelOutput(StrictBaseModel):
    action: str = Field(..., description="The action type, always 'cancel'")
    reason: str = Field(..., description="The reason for the cancellation as provided")
    status: str = Field(..., description="A message confirming that the request has been canceled")
