from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any, Literal


# ============================================================================
# BASE MODEL WITH STRICT VALIDATION
# ============================================================================

class StrictBaseModel(BaseModel):
    """Base model with strict validation that forbids extra fields.
    
    All CES Billing input and output models inherit from this base to ensure strict schema validation.
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
# INPUT MODELS - Used for validating function inputs
# ============================================================================

class GetBillingInfoInputSessioninfoParameters(StrictBaseModel):
    """Input parameters for the getBillingInfo tool session info.
    

    """
    callId: str = Field(..., description="Call identifier")
    mdn: str = Field(..., description="The customer's 10 or 11-digit Mobile Directory Number")
    endPageAction: Optional[str] = Field(None, description="End page action")


class GetBillingInfoInputSessioninfo(StrictBaseModel):
    """Input session information for the getBillingInfo tool.
    

    """
    parameters: GetBillingInfoInputSessioninfoParameters = Field(..., description="Parameters related to the session info")
    
    @model_validator(mode='before')
    @classmethod
    def validate_parameters_exist(cls, data: Any) -> Any:
        """Validate that parameters field exists with a clean error message."""
        if isinstance(data, dict) and 'parameters' not in data:
            raise ValueError('sessionInfo.parameters is required')
        return data


class GetBillingInfoInputFulfillmentinfo(StrictBaseModel):
    """Input fulfillment information for the getBillingInfo tool.
    
    This is a simplified model for input validation only.
    """
    tag: Literal["billing.action.initviewbill", "billing.action.nextBillEstimate", "billing.action.error"] = Field(
        ...,
        description="Billing action type. Must be one of: 'billing.action.initviewbill', 'billing.action.nextBillEstimate', 'billing.action.error'"
    )
    event: Optional[Dict[str, Any]] = Field(None, description="The event related to the fulfillment")


class GetBillingInfoInput(StrictBaseModel):
    """Input schema for get_billing_info function."""
    fulfillmentInfo: GetBillingInfoInputFulfillmentinfo = Field(..., description="Fulfillment information for the billing request")
    sessionInfo: GetBillingInfoInputSessioninfo = Field(..., description="Session information for the billing request")


class EscalateInput(StrictBaseModel):
    """Input schema for escalate function."""
    input: Optional[str] = Field(None, max_length=5000, description="Reason or context for the escalation")
    

class FailInput(StrictBaseModel):
    """Input schema for fail function."""
    input: Optional[str] = Field(None, max_length=5000, description="Reason for the failure")


class CancelInput(StrictBaseModel):
    """Input schema for cancel function."""
    input: Optional[str] = Field(None, max_length=5000, description="Optional reason for the cancellation or context about why the customer wants to stop")


class GhostInput(StrictBaseModel):
    """Input schema for ghost function (no parameters)."""
    pass


class AutopayInput(StrictBaseModel):
    """Input schema for autopay function (no parameters)."""
    pass


class BillInput(StrictBaseModel):
    """Input schema for bill function."""
    escalate_reduce_bill: Optional[bool] = Field(None, description="Set to true if the user wants to escalate to a human agent for bill reduction")
    go_to_main_menu: Optional[bool] = Field(None, description="Set to true if the user wants to return to the main menu")
    message: Optional[str] = Field(None, max_length=1000, description="Custom message or request type for billing processing")
    repeat_maxout: Optional[bool] = Field(None, description="Set to true if the user has repeated the request too many times")


class DefaultStartFlowInput(StrictBaseModel):
    """Input schema for default_start_flow function."""
    PasswordType: Optional[str] = Field(None, description="The type of password-related issue the user is facing")
    disambig_op_request: Optional[bool] = Field(None, description="Set to true if the user is requesting to disambiguate between options")
    escalate_reduce_bill: Optional[bool] = Field(None, description="Set to true if the user wants to escalate to a human agent to reduce the bill")
    go_to_main_menu: Optional[bool] = Field(None, description="Set to true if the user wants to go back to the main menu")
    head_intent: Optional[str] = Field(None, description="The initial intent or purpose of the user interaction")
    internet_routing: Optional[bool] = Field(None, description="Set to true if the user is asking about internet service")
    password_loop: Optional[bool] = Field(None, description="Set to true if the user is stuck in a password-related loop")
    repeat_maxout: Optional[bool] = Field(None, description="Set to true if the user has repeated the request too many times")


class DoneInput(StrictBaseModel):
    """Input schema for done function."""
    input: Optional[str] = Field(None, description="Optional summary or details about what was accomplished")


# ============================================================================
# OUTPUT MODELS - Used for structuring function outputs
# ============================================================================

class GetbillinginfoFulfillmentinfo(StrictBaseModel):
    """Fulfillment information for the getBillingInfo tool."""
    event: Optional[Dict[str, Any]] = Field(None, description="The event related to the fulfillment")
    tag: Optional[str] = Field(None, description="A tag associated with the fulfillment")


class GetbillinginfoSessioninfoParameters(StrictBaseModel):
    """Parameters for the getBillingInfo tool session info."""
    accountRole: Optional[str] = Field(None, description="Account type")
    activeMtnCount: Optional[str] = Field(None, description="Indicates the number of active lines in the account")
    additionalContent: Optional[str] = Field(None, description="Additional reasons for the increase in the bill")
    autoPay: Optional[str] = Field(None, description="Indicator to determine if the customer is registered in autoPay")
    billduedate: Optional[str] = Field(None, description="The date by which the next bill payment is due")
    callId: Optional[str] = Field(None, description="Unique identifier for the caller id")
    chargeCounter: Optional[str] = Field(None, description="The total number of new charges on the bill compared to the prior month")
    chargeCounterList: Optional[List[str]] = Field(None, description="A list of new charge types on the bill compared to last month")
    content: Optional[str] = Field(None, description="The top reasons for the increase in the bill")
    endPageAction: Optional[str] = Field(None, description="The page that directed here")
    lastPaidDate: Optional[str] = Field(None, description="A string representing the date of the user's last payment, in MM/DD/YYYY format")
    lastPaymentAmount: Optional[str] = Field(None, description="A string representing the last amount the user paid towards their bill")
    mdn: Optional[str] = Field(None, description="Unique identifier for the user account")
    mileStoneDate: Optional[str] = Field(None, description="The date on which the estimate of the next bill was generated. Only comes back for the billing.action.nextBillEstimate tag")
    nextBillEstimate: Optional[str] = Field(None, description="An estimate of the next bill. Only comes back for the billing.action.nextBillEstimate tag")
    outstandingBalance: Optional[str] = Field(None, description="The user's outstanding balance")
    pastDueBalance: Optional[str] = Field(None, description="The amount of the balance that is past due")
    statusCode: Optional[str] = Field(None, description="The status code of the API response")
    statusMessage: Optional[str] = Field(None, description="A message describing the status code of the API response")


class GetbillinginfoSessioninfo(StrictBaseModel):
    """Session information for the getBillingInfo tool."""
    parameters: Optional[GetbillinginfoSessioninfoParameters] = Field(None, description="Parameters related to the session info")
    session: Optional[str] = Field(None, description="Session for the getBillingInfo tool")


class Session(StrictBaseModel):
    """Session model for billing interactions."""
    id: Dict[str, Dict[str, GetbillinginfoSessioninfoParameters]] = Field(..., description="Session ID mapping")


class GetbillinginfoResponseSessioninfoParameters(StrictBaseModel):
    """Parameters for the getBillingInfo response session info."""

    activeMtnCount: Optional[str] = Field(None, description="Indicates the number of active lines in the account")
    additionalContent: Optional[str] = Field(None, description="Additional reasons for the increase in the bill")
    autoPay: Optional[str] = Field(None, description="Indicator to determine if the customer is registered in autoPay")
    billduedate: Optional[str] = Field(None, description="The date by which the next bill payment is due")
    chargeCounter: Optional[str] = Field(None, description="The total number of new charges on the bill compared to the prior month")
    chargeCounterList: Optional[List[str]] = Field(None, description="A list of new charge types on the bill compared to last month")
    content: Optional[str] = Field(None, description="The top reasons for the increase in the bill")
    lastPaidDate: Optional[str] = Field(None, description="A string representing the date of the user's last payment, in MM/DD/YYYY format")
    lastPaymentAmount: Optional[str] = Field(None, description="A string representing the last amount the user paid towards their bill")
    outstandingBalance: Optional[str] = Field(None, description="The user's outstanding balance")
    pastDueBalance: Optional[str] = Field(None, description="The amount of the balance that is past due")
    statusCode: str = Field(..., description="The status code of the API response")
    statusMessage: str = Field(..., description="A message describing the status code of the API response")


class GetbillinginfoResponseSessioninfo(StrictBaseModel):
    """Session information for the getBillingInfo response."""
    parameters: GetbillinginfoResponseSessioninfoParameters = Field(..., description="Parameters related to the response session info")


class GetbillinginfoResponse(StrictBaseModel):
    """Response from the getBillingInfo tool."""
    sessionInfo: GetbillinginfoResponseSessioninfo = Field(..., description="Session information related to the response")


class EscalateOutput(StrictBaseModel):
    """Output schema for escalate function."""
    action: str = Field(..., description="The type of action taken")
    reason: str = Field(..., description="Reason for escalation")
    status: str = Field(..., description="Status of the escalation")


class FailOutput(StrictBaseModel):
    """Output schema for fail function."""
    action: str = Field(..., description="The type of action taken")
    reason: str = Field(..., description="Reason for the failure")
    status: str = Field(..., description="Status of the failure")


class CancelOutput(StrictBaseModel):
    """Output schema for cancel function."""
    action: str = Field(..., description="The type of action taken")
    reason: str = Field(..., description="Reason for cancellation")
    status: str = Field(..., description="Status of the cancellation")


class GhostOutput(StrictBaseModel):
    """Output schema for ghost function."""
    action: str = Field(..., description="The type of action taken")
    reason: str = Field(..., description="Reason for ghosting the user")
    status: str = Field(..., description="Status of the ghost interaction")


class AutopayOutput(StrictBaseModel):
    """Output schema for autopay function."""
    status: str = Field(..., description="Enrollment status")
    discount_amount: str = Field(..., description="Discount amount applied")
    enrollment_type: str = Field(..., description="Type of enrollment")
    next_billing_cycle: str = Field(..., description="Next billing cycle date")
    timestamp: str = Field(..., description="Enrollment timestamp")


class BillOutput(StrictBaseModel):
    """Output schema for bill function."""
    escalate_reduce_bill: bool = Field(..., description="Whether to escalate for bill reduction")
    go_to_main_menu: bool = Field(..., description="Whether to return to main menu")
    message: str = Field(..., description="Custom billing message")
    repeat_maxout: bool = Field(..., description="Whether repeat maxout reached")
    status_code: str = Field(..., description="Status code of the request")
    status_message: str = Field(..., description="Status message")
    action_type: str = Field(..., description="Type of action performed")
    timestamp: str = Field(..., description="Request timestamp")


class DefaultStartFlowOutput(StrictBaseModel):
    """Output schema for default_start_flow function."""
    password_type: str = Field(..., description="Type of password issue")
    disambig_op_request: bool = Field(..., description="Whether disambiguation requested")
    escalate_reduce_bill: bool = Field(..., description="Whether to escalate for bill reduction")
    go_to_main_menu: bool = Field(..., description="Whether to return to main menu")
    head_intent: str = Field(..., description="Initial user intent")
    internet_routing: bool = Field(..., description="Whether asking about internet service")
    password_loop: bool = Field(..., description="Whether stuck in password loop")
    repeat_maxout: bool = Field(..., description="Whether repeat maxout reached")
    status_code: str = Field(..., description="Status code of the flow")
    status_message: str = Field(..., description="Status message")
    flow_type: str = Field(..., description="Type of flow")
    timestamp: str = Field(..., description="Flow timestamp")


class GetBillingInfoOutput(StrictBaseModel):
    """Output schema for get_billing_info function."""
    sessionInfo: GetbillinginfoResponseSessioninfo = Field(..., description="Session information containing billing details")


class DoneOutput(StrictBaseModel):
    """Output schema for done function."""
    action: str = Field(..., description="The type of action taken")
    reason: str = Field(..., description="Summary of what was accomplished")
    status: str = Field(..., description="Status of the completion")


