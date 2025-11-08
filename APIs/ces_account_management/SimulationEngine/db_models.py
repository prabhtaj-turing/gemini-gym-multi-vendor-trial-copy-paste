from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from .models import CommunicationPreferences, Device, Address, ServicePlan



# ---------------------------
# Internal Storage Models
# ---------------------------

class AccountDetails(BaseModel):
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

class ErrorSimulator(BaseModel):
    """Error simulator configuration"""
    example_function_name: List[str] = Field(
        default_factory=list,
        alias="_example_function_name",
        description="List of example function names for error simulation."
    )

class StatusSchema(BaseModel):
    """Common schema for status fields with reason, action, and status"""
    reason: str = Field(
        ...,
        description="Reason for the status.",
        min_length=1,
        max_length=500
    )
    action: str = Field(
        ...,
        description="Action taken.",
        min_length=1,
        max_length=200
    )
    status: str = Field(
        ...,
        description="Current status.",
        min_length=1,
        max_length=100
    )

class EndOfConversationStatus(BaseModel):
    """End of conversation status with structured fields"""
    escalate: Optional[StatusSchema] = Field(
        None,
        description="Escalation status with reason, action, and status."
    )
    fail: Optional[StatusSchema] = Field(
        None,
        description="Failure status at end of conversation."
    )
    cancel: Optional[StatusSchema] = Field(
        None,
        description="Cancellation status at end of conversation."
    )

# ---------------------------
# Root Database Model
# ---------------------------

class CesAccountManagementDB(BaseModel):
    """
    Root model that validates the entire CES Account Management database structure.
    
    This model ensures all data in the database conforms to the defined schemas
    for account details, services, devices, addresses, and communication preferences.
    """
    error_simulator: ErrorSimulator = Field(
        default_factory=ErrorSimulator,
        alias="_error_simulator",
        description="Error simulator configuration for testing purposes."
    )
    end_of_conversation_status: EndOfConversationStatus = Field(
        default_factory=EndOfConversationStatus,
        alias="_end_of_conversation_status",
        description="Status information at the end of conversation."
    )
    use_real_datastore: bool = Field(
        default=False,
        description="Whether to use real datastore or simulation."
    )
    accountDetails: Dict[str, AccountDetails] = Field(
        default_factory=dict,
        description="Dictionary of account details indexed by account ID."
    )

    model_config = {"str_strip_whitespace": True}
