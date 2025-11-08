from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict, Optional

from stripe.SimulationEngine.db import DB
from stripe.SimulationEngine import utils
from stripe.SimulationEngine.models import PaymentIntent, Refund
from stripe.SimulationEngine.custom_errors import InvalidRequestError, ResourceNotFoundError

@tool_spec(
    spec={
        'name': 'create_refund',
        'description': """ This tool will refund a payment intent in Stripe.
        
        It takes three arguments:
        - payment_intent (str): The ID of the payment intent to refund.
        - amount (int, optional): The amount to refund in cents. Defaults to None.
        - reason (str, optional): The reason for the refund. Defaults to None. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'payment_intent': {
                    'type': 'string',
                    'description': 'The ID of the PaymentIntent to refund.'
                },
                'amount': {
                    'type': 'integer',
                    'description': 'The amount to refund in cents. Defaults to None.'
                },
                'reason': {
                    'type': 'string',
                    'description': 'The reason for the refund. If provided, must be one of: "duplicate", "fraudulent", "requested_by_customer". Defaults to None.'
                }
            },
            'required': [
                'payment_intent'
            ]
        }
    }
)
def create_refund(payment_intent: str, amount: Optional[int] = None, reason: Optional[str] = None) -> Dict[str, Any]:
    """This tool will refund a payment intent in Stripe.

    It takes three arguments:
    - payment_intent (str): The ID of the payment intent to refund.
    - amount (int, optional): The amount to refund in cents. Defaults to None.
    - reason (str, optional): The reason for the refund. Defaults to None.

    Args:
        payment_intent (str): The ID of the PaymentIntent to refund.
        amount (Optional[int]): The amount to refund in cents. Defaults to None.
        reason (Optional[str]): The reason for the refund. If provided, must be one of: "duplicate", "fraudulent", "requested_by_customer". Defaults to None.

    Returns:
        Dict[str, Any]: Details of the created Stripe refund object, including:
            - id (str): Unique identifier for the refund.
            - object (str): String representing the object's type, typically "refund".
            - payment_intent (str): ID of the PaymentIntent that was refunded.
            - amount (int): Amount refunded, in cents.
            - currency (str): Three-letter ISO currency code for the refund amount.
            - status (str): The status of the refund (e.g., "succeeded", "pending", "failed", "canceled").
            - reason (Optional[str]): The reason for the refund, if provided.
            - created (int): Unix timestamp (seconds since epoch) of when the refund was created.
            - metadata (Optional[Dict[str, str]]): A set of key-value pairs associated with the refund object.

    Raises:
        InvalidRequestError: If the payment_intent ID is invalid or not a string, reason is not a string, amount is invalid (e.g., exceeds chargeable amount), or the payment intent cannot be refunded.
        ResourceNotFoundError: If the specified payment_intent ID does not exist.
    """
    # Validate payment_intent ID is not empty
    if not payment_intent:
        raise InvalidRequestError("Payment intent ID cannot be empty")

    if not isinstance(payment_intent, str):
        raise InvalidRequestError("Payment intent ID must be a string")

    if reason is not None:
        if not isinstance(reason, str):
            raise InvalidRequestError("Reason must be a string")
        VALID_REFUND_REASONS = ["duplicate", "fraudulent", "requested_by_customer"]
        if reason not in VALID_REFUND_REASONS:
            raise InvalidRequestError(f"Invalid reason: '{reason}'. Allowed values are: {', '.join(VALID_REFUND_REASONS)}.")


    # Get all payment intents and find the specific one
    pi_object = utils._get_object_by_id(DB, payment_intent, "payment_intents")

    if not pi_object:
        raise ResourceNotFoundError(f"No such payment_intent: {payment_intent}")

    # Check if the PaymentIntent is in a refundable state
    # Typically, only 'succeeded' PaymentIntents can be refunded.
    if pi_object["status"] != "succeeded":
        raise InvalidRequestError(
            f"PaymentIntent {payment_intent} cannot be refunded in its current state: {pi_object['status']}. "
            "Only succeeded PaymentIntents can be refunded."
        )

    # Calculate total amount already refunded for this PaymentIntent
    # Only count 'succeeded' refunds towards the total previously refunded.
    total_previously_refunded = 0
    refund_objects = utils._get_objects(DB, "refunds")
    for ref_id in refund_objects: # Iterate over keys to avoid potential issues if DB.refunds.values() is a view that changes
        ref = refund_objects[ref_id]
        if ref["payment_intent"] == payment_intent and ref["status"] == "succeeded":
            total_previously_refunded += ref["amount"]

    # Calculate the maximum amount that can be refunded now
    max_refundable_now = pi_object["amount"] - total_previously_refunded

    if max_refundable_now <= 0:
        raise InvalidRequestError(
            f"PaymentIntent {payment_intent} has already been fully refunded or no amount is currently refundable."
        )

    # Determine the amount to refund
    refund_amount_to_process: int
    if amount is not None:
        # Validate provided amount
        if not isinstance(amount, int) or amount <= 0:
            raise InvalidRequestError("Refund amount must be a positive integer and provided in cents.")
        refund_amount_to_process = amount
    else:
        # If no amount is specified, refund the remaining refundable amount
        refund_amount_to_process = max_refundable_now

    # Ensure the determined refund amount is not greater than what's refundable
    if refund_amount_to_process > max_refundable_now:
        raise InvalidRequestError(
            f"Refund amount {refund_amount_to_process} cents exceeds the remaining refundable amount of {max_refundable_now} cents "
            f"for PaymentIntent {payment_intent}."
        )

    # Create the refund object
    refund_id = utils.generate_id("re")
    current_timestamp = utils.get_current_timestamp()

    new_refund = Refund(
        id=refund_id,
        object="refund",
        payment_intent=payment_intent,
        amount=refund_amount_to_process,
        currency=pi_object["currency"],  # Use currency from the PaymentIntent
        status="succeeded",  # Default status for a new refund in this simulation
        reason=reason,
        created=current_timestamp,
        metadata=None  # No metadata support in this simplified version
    )

    # Directly update the DB's refunds collection
    DB["refunds"][refund_id] = new_refund.model_dump()

    return new_refund.model_dump()