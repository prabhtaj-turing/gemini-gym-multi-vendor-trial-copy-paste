# pylint: skip-file

import sys
import os
import json
from typing import Any, Dict, List, Optional, Union
from pydantic import ValidationError
from common_utils.tool_spec_decorator import tool_spec, ErrorObject

# Add the SimulationEngine directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SimulationEngine'))

from ces_billing.SimulationEngine.db import DB, DEFAULT_DB_PATH, save_state, load_state, get_minified_state
from ces_billing.SimulationEngine.models import (
    GetbillinginfoResponse,
    GetbillinginfoResponseSessioninfo,
    GetbillinginfoResponseSessioninfoParameters,
    GetbillinginfoFulfillmentinfo,
    GetbillinginfoSessioninfo,
    GetbillinginfoSessioninfoParameters,
    GetBillingInfoInputFulfillmentinfo,
    GetBillingInfoInputSessioninfo,
    GetBillingInfoInputSessioninfoParameters,
    # Input Models
    EscalateInput,
    FailInput,
    CancelInput,
    GhostInput,
    AutopayInput,
    BillInput,
    DefaultStartFlowInput,
    GetBillingInfoInput,
    DoneInput,
    # Output Models
    EscalateOutput,
    FailOutput,
    CancelOutput,
    GhostOutput,
    AutopayOutput,
    BillOutput,
    DefaultStartFlowOutput,
    GetBillingInfoOutput,
    DoneOutput
)
from ces_billing.SimulationEngine.utils import (
    _get_current_date,
    _get_next_billing_cycle,
    _validate_call_id,
    _validate_optional_string_input,
    _validate_string_input,
    _validate_mdn,
    _generate_sequential_id
)
from ces_billing.SimulationEngine.custom_errors import (
    InvalidMdnError,
    ValidationError as BillingValidationError,
    EmptyFieldError,
    BillingDataError,
    BillingRequestError,
    AutoPayError,
    EscalationError,
    DatabaseError
)


@tool_spec(
    input_model=EscalateInput,
    output_model=EscalateOutput,
    description="Escalates the call to a human agent. Report a status message.",
    error_model=[
        ErrorObject(ValidationError, [
            "Raised if input is not a string when provided or exceeds 5000 characters."
        ])
    ],
    spec={
        'name': 'escalate',
        'description': 'Escalates the call to a human agent. Report a status message.',
        'parameters': {
            'type': 'object',
            'properties': {
                'input': {
                    'type': 'string',
                    'description': 'Reason or context for the escalation. Maximum 5000 characters.',
                    'nullable': True
                }
            },
            'required': []
        },
        'response': {
            'description': 'An object containing the escalation data.',
            'type': 'object',
            'properties': {
                'action': {
                    'type': 'string',
                    'description': 'The type of action taken.'
                },
                'reason': {
                    'type': 'string',
                    'description': 'Reason for escalation.'
                },
                'status': {
                    'type': 'string',
                    'description': 'Status of the escalation.'
                }
            },
            'required': ['action', 'reason', 'status']
        }
    }
)
def escalate(input: Optional[str] = None) -> Dict[str, str]:
    """Escalates the call to a human agent. Report a status message.

    Args:
        input (Optional[str]): Reason or context for the escalation. Maximum 5000 characters.

    Returns:
        Dict[str, str]: An object containing the escalation data.
            - action (str): The type of action taken.
            - reason (str): Reason for escalation.
            - status (str): Status of the escalation.

    Raises:
        ValidationError: If input is not a string when provided or exceeds 5000 characters
    """
    # Validate and sanitize input
    validated_input = _validate_optional_string_input(input, "input", 5000)
    if validated_input is None:
        validated_input = "You will be connected to a human agent shortly."
    # Prepare escalation data
    escalation_data = {
        "action": "escalate",
        "reason": validated_input,
        "status": "You will be connected to a human agent shortly.",
    }
    
    # Save escalation to database
    if "end_of_conversation_status" not in DB:
        DB["end_of_conversation_status"] = {}
    
    DB["end_of_conversation_status"]["escalate"] = validated_input
    
    return escalation_data


@tool_spec(
    input_model=FailInput,
    output_model=FailOutput,
    description="Fails the current task because of being unable to understand the customer.",
    error_model=[
        ErrorObject(ValidationError, [
            "Raised if input is not a string when provided or exceeds 5000 characters."
        ])
    ],
    spec={
        'name': 'fail',
        'description': 'Fails the current task because of being unable to understand the customer.',
        'parameters': {
            'type': 'object',
            'properties': {
                'input': {
                    'type': 'string',
                    'description': 'Reason for the failure. Maximum 5000 characters.',
                    'nullable': True
                }
            },
            'required': []
        },
        'response': {
            'description': 'An object containing the failure data.',
            'type': 'object',
            'properties': {
                'action': {
                    'type': 'string',
                    'description': 'The type of action taken.'
                },
                'reason': {
                    'type': 'string',
                    'description': 'Reason for the failure.'
                },
                'status': {
                    'type': 'string',
                    'description': 'Status of the failure.'
                }
            },
            'required': ['action', 'reason', 'status']
        }
    }
)
def fail(input: Optional[str] = None) -> Dict[str, str]:
    """Fails the current task because of being unable to understand the customer.

    Args:
        input (Optional[str]): Reason for the failure. Maximum 5000 characters.

    Returns:
        Dict[str, str]: An object containing the failure data.
            - action (str): The type of action taken.
            - reason (str): Reason for the failure.
            - status (str): Status of the failure.

    Raises:
        ValidationError: If input is not a string when provided or exceeds 5000 characters
    """
    # Validate and sanitize input
    validated_input = _validate_optional_string_input(input, "input", 5000)
    if validated_input is None:
        validated_input = "I'm sorry, I'm unable to help with that at the moment. Please try again later."
    # Prepare failure data
    failure_data = {
        "action": "fail",
        "reason": validated_input,
        "status": "I'm sorry, I'm unable to help with that at the moment. Please try again later.",
    }
    
    # Save failure to database
    if "end_of_conversation_status" not in DB:
        DB["end_of_conversation_status"] = {}
    
    DB["end_of_conversation_status"]["fail"] = validated_input
    
    return failure_data


@tool_spec(
    input_model=CancelInput,
    output_model=CancelOutput,
    description="Cancels the current task when the customer does not want to proceed with the conversation.",
    error_model=[
        ErrorObject(ValidationError, [
            "Raised if input is not a string when provided or exceeds 5000 characters."
        ])
    ],
    spec={
        'name': 'cancel',
        'description': 'Cancels the current task when the customer does not want to proceed with the conversation.',
        'parameters': {
            'type': 'object',
            'properties': {
                'input': {
                    'type': 'string',
                    'description': 'Optional reason for the cancellation or context about why the customer wants to stop. Maximum 5000 characters.',
                    'nullable': True
                }
            },
            'required': []
        },
        'response': {
            'description': 'An object containing the cancellation data.',
            'type': 'object',
            'properties': {
                'action': {
                    'type': 'string',
                    'description': 'The type of action taken.'
                },
                'reason': {
                    'type': 'string',
                    'description': 'Reason for cancellation.'
                },
                'status': {
                    'type': 'string',
                    'description': 'Status of the cancellation.'
                }
            },
            'required': ['action', 'reason', 'status']
        }
    }
)
def cancel(input: Optional[str] = None) -> Dict[str, str]:
    """Cancels the current task when the customer does not want to proceed with the conversation.

    Args:
        input (Optional[str]): Optional reason for the cancellation or context about why the customer wants to stop. Maximum 5000 characters.

    Returns:
        Dict[str, str]: An object containing the cancellation data.
            - action (str): The type of action taken.
            - reason (str): Reason for cancellation.
            - status (str): Status of the cancellation.

    Raises:
        ValidationError: If input is not a string when provided or exceeds 5000 characters
    """
    validated_input = _validate_optional_string_input(input, "input", 5000)
    if validated_input is None or validated_input == "":
        validated_input = "Okay, I have canceled this request."
    # Prepare cancellation data
    cancellation_data = {
        "action": "cancel",
        "reason": validated_input,
        "status": "Okay, I have canceled this request.",
    }
    
    # Save cancellation to database
    if "end_of_conversation_status" not in DB:
        DB["end_of_conversation_status"] = {}
    
    DB["end_of_conversation_status"]["cancel"] = validated_input
    
    return cancellation_data

@tool_spec(
    input_model=GhostInput,
    output_model=GhostOutput,
    description="Ghost the user when user doesn't say anything for 3 times.",
    error_model=[],
    spec={
        'name': 'ghost',
        'description': "Ghost the user when user doesn't say anything for 3 times.",
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        },
        'response': {
            'description': 'An object containing the ghost data.',
            'type': 'object',
            'properties': {
                'action': {
                    'type': 'string',
                    'description': 'The type of action taken.'
                },
                'reason': {
                    'type': 'string',
                    'description': 'Reason for ghosting the user.'
                },
                'status': {
                    'type': 'string',
                    'description': 'Status of the ghost interaction.'
                }
            },
            'required': ['action', 'reason', 'status']
        }
    }
)
def ghost() -> Dict[str, str]:
    """Ghost the user when user doesn't say anything for 3 times.

    Returns:
        Dict[str, str]: An object containing the ghost data.
            - action (str): The type of action taken.
            - reason (str): Reason for ghosting the user.
            - status (str): Status of the ghost interaction.

    """
    
    # Prepare ghost data
    ghost_data = {
        "action": "ghost",
        "reason": "No user response after 3 attempts",
        "status": "User has been ghosted",
    }
    
    # Save fill to database
    if "end_of_conversation_status" not in DB:
        DB["end_of_conversation_status"] = {}
    
    DB["end_of_conversation_status"]["ghost"] = "No user response after 3 attempts"
    
    return ghost_data
        


@tool_spec(
    input_model=AutopayInput,
    output_model=AutopayOutput,
    description="Enrolls the customer in AutoPay to automatically pay their bill and receive a discount.",
    error_model=[
        ErrorObject(AutoPayError, [
            "Raised if customer is already enrolled in autopay."
        ])
    ],
    spec={
        'name': 'autopay',
        'description': 'Enrolls the customer in AutoPay to automatically pay their bill and receive a discount.',
        'parameters': {
            'type': 'object',
            'properties': {},
            'required': []
        },
        'response': {
            'description': 'An object containing the AutoPay enrollment data.',
            'type': 'object',
            'properties': {
                'status': {
                    'type': 'string',
                    'description': 'Enrollment status'
                },
                'discount_amount': {
                    'type': 'string',
                    'description': 'Discount amount applied ($10.00)'
                },
                'enrollment_type': {
                    'type': 'string',
                    'description': 'Type of enrollment'
                },
                'next_billing_cycle': {
                    'type': 'string',
                    'description': 'Next billing cycle date'
                },
                'timestamp': {
                    'type': 'string',
                    'description': 'Enrollment timestamp'
                }
            },
            'required': ['status', 'discount_amount', 'enrollment_type', 'next_billing_cycle', 'timestamp']
        }
    }
)
def autopay() -> Dict[str, str]:
    """Enrolls the customer in AutoPay to automatically pay their bill and receive a discount.

    Returns:
        Dict[str, str]: An object containing the AutoPay enrollment data.
            - status (str): Enrollment status
            - discount_amount (str): Discount amount applied ($10.00)
            - enrollment_type (str): Type of enrollment
            - next_billing_cycle (str): Next billing cycle date
            - timestamp (str): Enrollment timestamp

    Raises:
        AutoPayError: If customer is already enrolled in autopay
    """
    if DB.get("end_of_conversation_status", {}).get("autopay"):
        raise AutoPayError("Customer is already enrolled in autopay")

    autopay_data = {
        "status": "Successfully enrolled in Autopay",
        "discount_amount": "$10.00",
        "enrollment_type": "automatic",
        "next_billing_cycle": _get_next_billing_cycle(),
        "timestamp": _get_current_date(),
    }

    if "end_of_conversation_status" not in DB:
        DB["end_of_conversation_status"] = {}
    
    DB["end_of_conversation_status"]["autopay"] = "Successfully enrolled in Autopay"
    
    return autopay_data
        


@tool_spec(
    input_model=BillInput,
    output_model=BillOutput,
    description="Processes billing-related requests and routes them to appropriate handlers.",
    error_model=[
        ErrorObject(BillingValidationError, [
            "Raised if boolean parameters have invalid types."
        ]),
        ErrorObject(ValidationError, [
            "If input is not a string when provided or exceeds 5000 characters."
        ])
    ],
    spec={
        'name': 'bill',
        'description': 'Processes billing-related requests and routes them to appropriate handlers.',
        'parameters': {
            'type': 'object',
            'properties': {
                'escalate_reduce_bill': {
                    'type': 'boolean',
                    'description': 'Set to true if the user wants to escalate to a human agent for bill reduction.',
                    'nullable': True
                },
                'go_to_main_menu': {
                    'type': 'boolean',
                    'description': 'Set to true if the user wants to return to the main menu.',
                    'nullable': True
                },
                'message': {
                    'type': 'string',
                    'description': 'Custom message or request type for billing processing. Maximum 1000 characters.',
                    'nullable': True
                },
                'repeat_maxout': {
                    'type': 'boolean',
                    'description': 'Set to true if the user has repeated the request too many times.',
                    'nullable': True
                }
            },
            'required': []
        },
        'response': {
            'description': 'An object containing the billing interaction data.',
            'type': 'object',
            'properties': {
                'escalate_reduce_bill': {
                    'type': 'boolean',
                    'description': 'Whether to escalate for bill reduction'
                },
                'go_to_main_menu': {
                    'type': 'boolean',
                    'description': 'Whether to return to main menu'
                },
                'message': {
                    'type': 'string',
                    'description': 'Custom billing message'
                },
                'repeat_maxout': {
                    'type': 'boolean',
                    'description': 'Whether repeat maxout reached'
                },
                'status_code': {
                    'type': 'string',
                    'description': 'Status code of the request'
                },
                'status_message': {
                    'type': 'string',
                    'description': 'Status message'
                },
                'action_type': {
                    'type': 'string',
                    'description': 'Type of action performed'
                },
                'timestamp': {
                    'type': 'string',
                    'description': 'Request timestamp'
                }
            },
            'required': ['escalate_reduce_bill', 'go_to_main_menu', 'message', 'repeat_maxout', 'status_code', 'status_message', 'action_type', 'timestamp']
        }
    }
)
def bill(
    escalate_reduce_bill: Optional[bool] = None,
    go_to_main_menu: Optional[bool] = None,
    message: Optional[str] = None,
    repeat_maxout: Optional[bool] = None,
) -> Dict[str, Union[str, bool]]:
    """Processes billing-related requests and routes them to appropriate handlers.

    Args:
        escalate_reduce_bill (Optional[bool]): Set to true if the user wants to escalate to a human agent for bill reduction.
        go_to_main_menu (Optional[bool]): Set to true if the user wants to return to the main menu.
        message (Optional[str]): Custom message or request type for billing processing. Maximum 1000 characters.
        repeat_maxout (Optional[bool]): Set to true if the user has repeated the request too many times.

    Returns:
        Dict[str, Union[str, bool]]: An object containing the billing interaction data.
            - escalate_reduce_bill (bool): Whether to escalate for bill reduction
            - go_to_main_menu (bool): Whether to return to main menu
            - message (str): Custom billing message
            - repeat_maxout (bool): Whether repeat maxout reached
            - status_code (str): Status code of the request
            - status_message (str): Status message
            - action_type (str): Type of action performed
            - timestamp (str): Request timestamp

    Raises:
        BillingValidationError: If boolean parameters have invalid types
        ValidationError: If input is not a string when provided or exceeds 5000 characters
    """
    # Validate and sanitize input
    if escalate_reduce_bill is not None and not isinstance(escalate_reduce_bill, bool):
        raise BillingValidationError(f"escalate_reduce_bill must be a boolean, got {type(escalate_reduce_bill).__name__}")
    if go_to_main_menu is not None and not isinstance(go_to_main_menu, bool):
        raise BillingValidationError(f"go_to_main_menu must be a boolean, got {type(go_to_main_menu).__name__}")
    if repeat_maxout is not None and not isinstance(repeat_maxout, bool):
        raise BillingValidationError(f"repeat_maxout must be a boolean, got {type(repeat_maxout).__name__}")
    
    # Validate and sanitize string inputs
    validated_message = _validate_optional_string_input(message, "message", 1000)
    
    # Set default message if None (but preserve empty strings)
    if message is None:
        validated_message = "Customer requesting billing information"
    
    # Generate a unique ID for this billing interaction
    interaction_id = _generate_sequential_id("INTERACTION", ["billing_interactions"])
    
    # Determine status based on input parameters
    status_code = "0000"
    status_message = "Billing request processed"
    
    if escalate_reduce_bill:
        status_message = "Escalated to human agent for bill reduction"
        status_code = "0001"
    elif go_to_main_menu:
        status_message = "Returning to main menu"
    elif repeat_maxout:
        status_message = "Repeat maxout reached - escalation triggered"
        status_code = "0001"
    elif message is not None:
        status_message = validated_message
    
    # Prepare billing interaction data
    billing_data = {
        "escalate_reduce_bill": escalate_reduce_bill or False,
        "go_to_main_menu": go_to_main_menu or False,
        "message": validated_message,
        "repeat_maxout": repeat_maxout or False,
        "status_code": status_code,
        "status_message": status_message,
        "action_type": "billing_request",
        "timestamp": _get_current_date(),
    }
    
    # Save billing interaction to database - save to billing_interactions, not bills
    if "billing_interactions" not in DB:
        DB["billing_interactions"] = {}
    
    DB["billing_interactions"][interaction_id] = billing_data
    
    return billing_data
        


@tool_spec(
    input_model=DefaultStartFlowInput,
    output_model=DefaultStartFlowOutput,
    description="Handles the initial conversation flow and routes users to appropriate services.",
    error_model=[
        ErrorObject(BillingValidationError, [
            "Raised if any parameter has invalid type."
        ])
    ],
    spec={
        'name': 'default_start_flow',
        'description': 'Handles the initial conversation flow and routes users to appropriate services.',
        'parameters': {
            'type': 'object',
            'properties': {
                'PasswordType': {
                    'type': 'string',
                    'description': 'The type of password-related issue the user is facing.',
                    'nullable': True
                },
                'disambig_op_request': {
                    'type': 'boolean',
                    'description': 'Set to true if the user is requesting to disambiguate between options.',
                    'nullable': True
                },
                'escalate_reduce_bill': {
                    'type': 'boolean',
                    'description': 'Set to true if the user wants to escalate to a human agent to reduce the bill.',
                    'nullable': True
                },
                'go_to_main_menu': {
                    'type': 'boolean',
                    'description': 'Set to true if the user wants to go back to the main menu.',
                    'nullable': True
                },
                'head_intent': {
                    'type': 'string',
                    'description': 'The initial intent or purpose of the user interaction.',
                    'nullable': True
                },
                'internet_routing': {
                    'type': 'boolean',
                    'description': 'Set to true if the user is asking about internet service.',
                    'nullable': True
                },
                'password_loop': {
                    'type': 'boolean',
                    'description': 'Set to true if the user is stuck in a password-related loop.',
                    'nullable': True
                },
                'repeat_maxout': {
                    'type': 'boolean',
                    'description': 'Set to true if the user has repeated the request too many times.',
                    'nullable': True
                }
            },
            'required': []
        },
        'response': {
            'description': 'An object containing the flow data.',
            'type': 'object',
            'properties': {
                'password_type': {
                    'type': 'string',
                    'description': 'Type of password issue'
                },
                'disambig_op_request': {
                    'type': 'boolean',
                    'description': 'Whether disambiguation requested'
                },
                'escalate_reduce_bill': {
                    'type': 'boolean',
                    'description': 'Whether to escalate for bill reduction'
                },
                'go_to_main_menu': {
                    'type': 'boolean',
                    'description': 'Whether to return to main menu'
                },
                'head_intent': {
                    'type': 'string',
                    'description': 'Initial user intent'
                },
                'internet_routing': {
                    'type': 'boolean',
                    'description': 'Whether asking about internet service'
                },
                'password_loop': {
                    'type': 'boolean',
                    'description': 'Whether stuck in password loop'
                },
                'repeat_maxout': {
                    'type': 'boolean',
                    'description': 'Whether repeat maxout reached'
                },
                'status_code': {
                    'type': 'string',
                    'description': 'Status code of the flow'
                },
                'status_message': {
                    'type': 'string',
                    'description': 'Status message'
                },
                'flow_type': {
                    'type': 'string',
                    'description': 'Type of flow'
                },
                'timestamp': {
                    'type': 'string',
                    'description': 'Flow timestamp'
                }
            },
            'required': ['password_type', 'disambig_op_request', 'escalate_reduce_bill', 'go_to_main_menu', 'head_intent', 'internet_routing', 'password_loop', 'repeat_maxout', 'status_code', 'status_message', 'flow_type', 'timestamp']
        }
    }
)
def default_start_flow(
    PasswordType: Optional[str] = None,
    disambig_op_request: Optional[bool] = None,
    escalate_reduce_bill: Optional[bool] = None,
    go_to_main_menu: Optional[bool] = None,
    head_intent: Optional[str] = None,
    internet_routing: Optional[bool] = None,
    password_loop: Optional[bool] = None,
    repeat_maxout: Optional[bool] = None,
) -> Dict[str, Union[str, bool]]:
    """Handles the initial conversation flow and routes users to appropriate services.

    Args:
        PasswordType (Optional[str]): The type of password-related issue the user is facing.
        disambig_op_request (Optional[bool]): Set to true if the user is requesting to disambiguate between options.
        escalate_reduce_bill (Optional[bool]): Set to true if the user wants to escalate to a human agent to reduce the bill.
        go_to_main_menu (Optional[bool]): Set to true if the user wants to go back to the main menu.
        head_intent (Optional[str]): The initial intent or purpose of the user interaction.
        internet_routing (Optional[bool]): Set to true if the user is asking about internet service.
        password_loop (Optional[bool]): Set to true if the user is stuck in a password-related loop.
        repeat_maxout (Optional[bool]): Set to true if the user has repeated the request too many times.

    Returns:
        Dict[str, Union[str, bool]]: An object containing the flow data.
            - password_type (str): Type of password issue
            - disambig_op_request (bool): Whether disambiguation requested
            - escalate_reduce_bill (bool): Whether to escalate for bill reduction
            - go_to_main_menu (bool): Whether to return to main menu
            - head_intent (str): Initial user intent
            - internet_routing (bool): Whether asking about internet service
            - password_loop (bool): Whether stuck in password loop
            - repeat_maxout (bool): Whether repeat maxout reached
            - status_code (str): Status code of the flow
            - status_message (str): Status message
            - flow_type (str): Type of flow
            - timestamp (str): Flow timestamp

    Raises:
        BillingValidationError: If any parameter has invalid type
    """
    # Validate input types
    if PasswordType is not None and not isinstance(PasswordType, str):
        raise BillingValidationError(f"PasswordType must be a string, got {type(PasswordType).__name__}")
    if disambig_op_request is not None and not isinstance(disambig_op_request, bool):
        raise BillingValidationError(f"disambig_op_request must be a boolean, got {type(disambig_op_request).__name__}")
    if escalate_reduce_bill is not None and not isinstance(escalate_reduce_bill, bool):
        raise BillingValidationError(f"escalate_reduce_bill must be a boolean, got {type(escalate_reduce_bill).__name__}")
    if go_to_main_menu is not None and not isinstance(go_to_main_menu, bool):
        raise BillingValidationError(f"go_to_main_menu must be a boolean, got {type(go_to_main_menu).__name__}")
    if head_intent is not None and not isinstance(head_intent, str):
        raise BillingValidationError(f"head_intent must be a string, got {type(head_intent).__name__}")
    if internet_routing is not None and not isinstance(internet_routing, bool):
        raise BillingValidationError(f"internet_routing must be a boolean, got {type(internet_routing).__name__}")
    if password_loop is not None and not isinstance(password_loop, bool):
        raise BillingValidationError(f"password_loop must be a boolean, got {type(password_loop).__name__}")
    if repeat_maxout is not None and not isinstance(repeat_maxout, bool):
        raise BillingValidationError(f"repeat_maxout must be a boolean, got {type(repeat_maxout).__name__}")
    
    # Determine status based on input parameters
    status_code = "0000"
    status_message = "Default start flow initiated"
    
    if escalate_reduce_bill:
        status_message = "Escalated to human agent for bill reduction"
        status_code = "0001"
    elif go_to_main_menu:
        status_message = "Returning to main menu"
    elif repeat_maxout:
        status_message = "Repeat maxout reached - escalation triggered"
        status_code = "0001"
    
    # Prepare default start flow data
    flow_data = {
        "password_type": PasswordType or "voice",
        "disambig_op_request": disambig_op_request or False,
        "escalate_reduce_bill": escalate_reduce_bill or False,
        "go_to_main_menu": go_to_main_menu or False,
        "head_intent": head_intent or "billing_inquiry",
        "internet_routing": internet_routing or False,
        "password_loop": password_loop or False,
        "repeat_maxout": repeat_maxout or False,
        "status_code": status_code,
        "status_message": status_message,
        "flow_type": "default_start",
        "timestamp": _get_current_date()
    }
    
    # Save default start flow to database
    if "default_start_flows" not in DB:
        DB["default_start_flows"] = {}
    
    DB["default_start_flows"] = flow_data
    
    return flow_data
        


@tool_spec(
    input_model=GetBillingInfoInput,
    output_model=GetBillingInfoOutput,
    description="Retrieves customer billing information including balances, due dates, and payment history.",
    error_model=[
        ErrorObject(ValueError, [
            "Raised if call_id or mdn are None, not strings, or exceed length limits."
        ]),
        ErrorObject(InvalidMdnError, [
            "Raised if mdn format is invalid (not 8-11 digits)."
        ]),
        ErrorObject(BillingValidationError, [
            "Raised if required parameters are missing or have invalid types."
        ]),
        ErrorObject(BillingDataError, [
            "Raised if bill not found for the given callId and mdn."
        ])
    ],
    spec={
        'name': 'get_billing_info',
        'description': 'Retrieves customer billing information including balances, due dates, and payment history.',
        'parameters': {
            'type': 'object',
            'properties': {
                'fulfillmentInfo': {
                    'type': 'object',
                    'description': 'Fulfillment information for the billing request containing tag.',
                    'properties': {
                        'tag': {
                            'type': 'string',
                            'description': 'Billing action type. Must be one of: "billing.action.initviewbill", "billing.action.nextBillEstimate", "billing.action.error"',
                            'enum': [
                                'billing.action.initviewbill',
                                'billing.action.nextBillEstimate',
                                'billing.action.error'
                            ]
                        },
                        'event': {
                            'type': 'object',
                            'description': 'Event information for the billing request',
                            'properties': {},
                            'required': [],
                            'nullable': True
                        }
                    },
                    'required': [
                        'tag'
                    ]
                },
                'sessionInfo': {
                    'type': 'object',
                    'description': 'Session information for the billing request containing callId, mdn, and endPageAction.',
                    'properties': {
                        'parameters': {
                            'type': 'object',
                            'description': 'Session parameters containing billing details',
                            'properties': {
                                'callId': {
                                    'type': 'string',
                                    'description': 'Call identifier'
                                },
                                'mdn': {
                                    'type': 'string',
                                    'description': 'Unique identifier for the user account.'
                                },
                                'endPageAction': {
                                    'type': 'string',
                                    'description': 'End page action',
                                    'nullable': True
                                }
                            },
                            'required': [
                                'callId',
                                'mdn'
                            ]
                        }
                    },
                    'required': [
                        'parameters'
                    ]
                }
            },
            'required': [
                'fulfillmentInfo',
                'sessionInfo'
            ]
        },
        'response': {
            'description': 'An object containing the billing information response.',
            'type': 'object',
            'properties': {
                'sessionInfo': {
                    'type': 'object',
                    'description': 'Session information for the billing request containing callId, mdn, and endPageAction.',
                    'properties': {
                        'parameters': {
                            'type': 'object',
                            'description': 'Session parameters containing billing details',
                            'properties': {
                                'outstandingBalance': {
                                    'type': 'string',
                                    'description': 'Outstanding balance amount.',
                                    'nullable': True
                                },
                                'additionalContent': {
                                    'type': 'string',
                                    'description': 'Additional billing details.',
                                    'nullable': True
                                },
                                'billduedate': {
                                    'type': 'string',
                                    'description': 'Bill due date.',
                                    'nullable': True
                                },
                                'chargeCounter': {
                                    'type': 'string',
                                    'description': 'Number of new charges.',
                                    'nullable': True
                                },
                                'activeMtnCount': {
                                    'type': 'string',
                                    'description': 'Number of active lines.',
                                    'nullable': True
                                },
                                'autoPay': {
                                    'type': 'string',
                                    'description': 'AutoPay enrollment status.',
                                    'nullable': True
                                },
                                'pastDueBalance': {
                                    'type': 'string',
                                    'description': 'Past due balance amount.',
                                    'nullable': True
                                },
                                'chargeCounterList': {
                                    'type': 'array',
                                    'items': {
                                        'type': 'string'
                                    },
                                    'description': 'List of new charge types.',
                                    'nullable': True
                                },
                                'lastPaidDate': {
                                    'type': 'string',
                                    'description': 'Last payment date.',
                                    'nullable': True
                                },
                                'lastPaymentAmount': {
                                    'type': 'string',
                                    'description': 'Last payment amount.',
                                    'nullable': True
                                },
                                'statusCode': {
                                    'type': 'string',
                                    'description': 'Status code.'
                                },
                                'content': {
                                    'type': 'string',
                                    'description': 'Main billing content.',
                                    'nullable': True
                                },
                                'statusMessage': {
                                    'type': 'string',
                                    'description': 'Status message.'
                                }
                            },
                            'required': ['statusCode', 'statusMessage']
                        }
                    },
                    'required': ['parameters']
                }
            },
            'required': ['sessionInfo']
        }
    }
)
def get_billing_info(
    fulfillmentInfo: Dict[str, Union[str, Dict[str, Any]]],
    sessionInfo: Dict[str, Dict[str, Optional[str]]],
) -> Dict[str, Dict[str, Dict[str, Union[str, List[str]]]]]:
    """Retrieves customer billing information including balances, due dates, and payment history.

    Args:
        fulfillmentInfo (Dict[str, Union[str, Dict[str, Any]]]): Fulfillment information for the billing request containing tag.
            - tag (str): Billing action type. Must be one of: "billing.action.initviewbill", "billing.action.nextBillEstimate", "billing.action.error"
            - event (Optional[Dict[str, Any]]): Event information for the billing request
        sessionInfo (Dict[str, Dict[str, Optional[str]]]): Session information for the billing request containing callId, mdn, and endPageAction.
            - parameters (Dict[str, str]): Session parameters containing billing details
                - callId (str): Call identifier
                - mdn (str): Unique identifier for the user account.
                - endPageAction (Optional[str]): End page action

    Returns:
        Dict[str, Dict[str, Dict[str, Union[str, List[str]]]]]: An object containing the billing information response.
            - sessionInfo (Dict[str, Dict[str, Optional[str]]]): Session information for the billing request containing callId, mdn, and endPageAction.
                - parameters (Dict[str, str]): Session parameters containing billing details
                    - outstandingBalance (str): Outstanding balance amount.
                    - additionalContent (str): Additional billing details.
                    - billduedate (str): Bill due date.
                    - chargeCounter (str): Number of new charges.
                    - activeMtnCount (str): Number of active lines.
                    - autoPay (str): AutoPay enrollment status.
                    - pastDueBalance (str): Past due balance amount.
                    - chargeCounterList (List[str]): List of new charge types.
                    - lastPaidDate (str): Last payment date.
                    - lastPaymentAmount (str): Last payment amount.
                    - statusCode (str): Status code.
                    - content (str): Main billing content.
                    - statusMessage (str): Status message.

    Raises:
        ValueError: If call_id or mdn are None, not strings, or exceed length limits
        InvalidMdnError: If mdn format is invalid (not 8-11 digits)
        BillingValidationError: If required parameters are missing or have invalid types
        BillingDataError: If bill not found for the given callId and mdn
    """
    # Validate input types
    if not isinstance(fulfillmentInfo, dict):
        raise BillingValidationError(f"fulfillmentInfo must be a dict, got {type(fulfillmentInfo).__name__}")
    if not isinstance(sessionInfo, dict):
        raise BillingValidationError(f"sessionInfo must be a dict, got {type(sessionInfo).__name__}")
    
    # Validate fulfillmentInfo using simplified input Pydantic model
    try:
        fulfillment_validated = GetBillingInfoInputFulfillmentinfo(**fulfillmentInfo)
    except ValidationError as e:
        raise BillingValidationError(f"Invalid fulfillmentInfo structure: {str(e)}")
    
    # Validate sessionInfo using simplified input Pydantic model
    try:
        session_validated = GetBillingInfoInputSessioninfo(**sessionInfo)
    except ValidationError as e:
        error_str = str(e)
        if "sessionInfo.parameters is required" in error_str:
            raise BillingValidationError("sessionInfo.parameters is required") 
        raise BillingValidationError(f"Invalid sessionInfo structure: {error_str}")
    
    # Extract and validate parameters
    tag = _validate_optional_string_input(fulfillment_validated.tag, "tag", 100) or "billing.action.initviewbill"
    
    session_params = session_validated.parameters
    call_id = session_params.callId
    mdn = session_params.mdn
    end_page_action = _validate_optional_string_input(session_params.endPageAction, "endPageAction", 50) or "BillingGeneral"
    
    # Check if bills table exists
    if "bills" not in DB or not DB["bills"]:
        raise BillingDataError("No bills found in database")
    
    # Validate call_id and mdn
    validated_call_id = _validate_call_id(call_id)
    validated_mdn = _validate_mdn(mdn)
    
    # Check if bills table exists
    if "bills" not in DB or not DB["bills"]:
        raise BillingDataError("No bills found in database")
    
    # Fetch the bill using call_id and mdn
    bill_data = None
    for bill_details in DB['bills'].values():
        if (bill_details.get("call_id") == validated_call_id and
            bill_details.get("mdn") == validated_mdn):
            bill_data = bill_details
            break
    
    if not bill_data:
        raise BillingDataError(f"Bill not found for callId: {validated_call_id} and mdn: {validated_mdn}")
    
    # Save billing interaction
    billing_interaction_data = {
        "tag": tag,
        "end_page_action": end_page_action,
        "timestamp": _get_current_date(),
    }
    
    # Save to billing_interactions
    if "billing_interactions" not in DB:
        DB["billing_interactions"] = {}
    
    interaction_id = _generate_sequential_id("BILLING_INFO", ["billing_interactions"])
    DB["billing_interactions"][interaction_id] = billing_interaction_data
    
    # Helper function to convert values to strings while preserving None
    def _to_string_if_not_none(value: Any) -> Optional[str]:
        """Convert value to string if not None, preserving None."""
        if value is None:
            return None
        return str(value)
    
    # Helper function to convert list items to strings if not None
    def _to_string_list_if_not_none(value: Any) -> Optional[List[str]]:
        """Convert list items to strings if not None, preserving None."""
        if value is None:
            return None
        if isinstance(value, list):
            return [str(item) if item is not None else "" for item in value]
        return None
    
    response = {
        "sessionInfo": {
            "parameters": {
                "outstandingBalance": _to_string_if_not_none(bill_data.get("outstandingBalance")),
                "additionalContent": bill_data.get("additionalContent"),
                "billduedate": bill_data.get("billduedate"),
                "chargeCounter": _to_string_if_not_none(bill_data.get("chargeCounter")),
                "activeMtnCount": _to_string_if_not_none(bill_data.get("activeMtnCount")),
                "autoPay": _to_string_if_not_none(bill_data.get("autoPay")),
                "pastDueBalance": _to_string_if_not_none(bill_data.get("pastDueBalance")),
                "chargeCounterList": _to_string_list_if_not_none(bill_data.get("chargeCounterList")),
                "lastPaidDate": bill_data.get("lastPaidDate"),
                "lastPaymentAmount": _to_string_if_not_none(bill_data.get("lastPaymentAmount")),
                "statusCode": "0000",
                "content": bill_data.get("content"),
                "statusMessage": "Success"
            }
        }
    }
    
    return response



@tool_spec(
    input_model=DoneInput,
    output_model=DoneOutput,
    description="Indicates that the task has been successfully completed.",
    error_model=[
        ErrorObject(ValidationError, [
            "Raised if input is not a string when provided or exceeds 10000000 characters."
        ])
    ],
    spec={
        'name': 'done',
        'description': 'Indicates that the task has been successfully completed.',
        'parameters': {
            'type': 'object',
            'properties': {
                'input': {
                    'type': 'string',
                    'description': 'Optional summary or details about what was accomplished in the conversation.',
                    'nullable': True
                }
            },
            'required': []
        },
        'response': {
            'description': 'An object containing the completion data.',
            'type': 'object',
            'properties': {
                'action': {
                    'type': 'string',
                    'description': 'The type of action taken.'
                },
                'reason': {
                    'type': 'string',
                    'description': 'Summary of what was accomplished.'
                },
                'status': {
                    'type': 'string',
                    'description': 'Status of the completion.'
                }
            },
            'required': ['action', 'reason', 'status']
        }
    }
)
def done(input: Optional[str] = None) -> Dict[str, str]:
    """Indicates that the task has been successfully completed.

    Args:
        input (Optional[str]): Optional summary or details about what was accomplished in the conversation.

    Returns:
        Dict[str, str]: An object containing the completion data.
            - action (str): The type of action taken.
            - reason (str): Summary of what was accomplished.
            - status (str): Status of the completion.

    Raises:
        ValidationError: If input is not a string when provided or exceeds 10000000 characters
    """
    # Validate and sanitize input
    validated_input = _validate_optional_string_input(input, "input", 10000000)  # 10MB limit for large inputs
    if not validated_input:
        validated_input = "completed the task."
    # Prepare completion data
    completion_data = {
        "action": "done",
        "reason": validated_input,
        "status": "Request has been completed",
    }
    
    # Save completion to database (we can store this in a new section or reuse existing)
    if "end_of_conversation_status" not in DB:
        DB["end_of_conversation_status"] = {}
    
    DB["end_of_conversation_status"]["done"] = "completed the task."
    return completion_data
    