from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict, List
from pydantic import ValidationError
from retail.SimulationEngine.custom_errors import (
    InvalidCancelReasonError,
    NonPendingOrderError,
    OrderNotFoundError,
    InvalidInputError,
)
from retail.SimulationEngine import db
from retail.SimulationEngine.models import (
    CancelPendingOrderInput,
    CancelPendingOrderOutput,
    Order,
    PaymentHistory,
)


@tool_spec(
    spec={
        'name': 'cancel_pending_order',
        'description': """ Cancel a pending order.
        
        If the order is already processed or delivered, it cannot be cancelled.
        The agent needs to explain the cancellation detail and ask for explicit user
        confirmation (yes/no) to proceed. If the user confirms, the order status
        will be changed to 'cancelled' and the payment will be refunded. The refund
        will be added to the user's gift card balance immediately if the payment
        was made using a gift card, otherwise the refund would take 5-7 business
        days to process. The function returns the order details after the
        cancellation. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'order_id': {
                    'type': 'string',
                    'description': """ The order id, such as '#W0000000'. Be careful there is a '#'
                    symbol at the beginning of the order id. """
                },
                'reason': {
                    'type': 'string',
                    'description': """ The reason for cancellation, which should be either
                    'no longer needed' or 'ordered by mistake'. """
                }
            },
            'required': [
                'order_id',
                'reason'
            ]
        }
    }
)
def cancel_pending_order(order_id: str, reason: str) -> Dict[str, Any]:
    """Cancel a pending order.

    If the order is already processed or delivered, it cannot be cancelled.
    The agent needs to explain the cancellation detail and ask for explicit user
    confirmation (yes/no) to proceed. If the user confirms, the order status
    will be changed to 'cancelled' and the payment will be refunded. The refund
    will be added to the user's gift card balance immediately if the payment
    was made using a gift card, otherwise the refund would take 5-7 business
    days to process. The function returns the order details after the
    cancellation.

    Args:
        order_id (str): The order id, such as '#W0000000'. Be careful there is a '#'
            symbol at the beginning of the order id.
        reason (str): The reason for cancellation, which should be either
            'no longer needed' or 'ordered by mistake'.

    Returns:
        Dict[str, Any]: A dictionary representing the updated order with the following fields:
            - order_id (str): The ID of the order.
            - user_id (str): The ID of the user who placed the order.
            - address (Dict[str, str]): The shipping address for the order.
                - address1 (str): The first line of the address.
                - address2 (str): The second line of the address.
                - city (str): The city of the address.
                - country (str): The country of the address.
                - state (str): The state of the address.
                - zip (str): The zip code of the address.
            - items (List[Dict[str, Any]]): A list of items in the order.
                - name (str): The name of the item.
                - product_id (str): The ID of the product.
                - item_id (str): The ID of the item.
                - price (float): The price of the item.
                - options (Dict[str, str]): The options for the item.
            - fulfillments (List[Dict[str, List[str]]]): A list of fulfillments for the order.
                - tracking_id (List[str]): A list of tracking IDs for the fulfillment.
                - item_ids (List[str]): A list of item IDs in the fulfillment.
            - status (str): The status of the order.
            - payment_history (List[Dict[str, Any]]): A list of payment transactions for the order.
                - transaction_type (str): The type of transaction.
                - amount (float): The amount of the transaction.
                - payment_method_id (str): The ID of the payment method.
            - cancel_reason (Optional[str]): The reason for cancellation.

    Raises:
        OrderNotFoundError: If the order is not found.
        NonPendingOrderError: If the order is not in a 'pending' state.
        InvalidCancelReasonError: If the cancellation reason is invalid.
        InvalidInputError: If the input is invalid.
    """
    try:
        CancelPendingOrderInput(order_id=order_id, reason=reason)
    except ValidationError as e:
        raise InvalidInputError(e)

    orders = db.DB["orders"]
    if order_id not in orders:
        raise OrderNotFoundError("Error: order not found")

    order = Order(**orders[order_id])
    if order.status != "pending" and order.status != "pending (item modified)":
        raise NonPendingOrderError("Error: non-pending order cannot be cancelled")

    if reason not in ["no longer needed", "ordered by mistake"]:
        raise InvalidCancelReasonError("Error: invalid reason")

    refunds: List[PaymentHistory] = []
    for payment in order.payment_history:
        refund = PaymentHistory(
            transaction_type="refund",
            amount=payment.amount,
            payment_method_id=payment.payment_method_id,
        )
        refunds.append(refund)
        if "gift_card" in payment.payment_method_id:
            users = db.DB["users"]
            user = users[order.user_id]
            payment_method = user["payment_methods"][payment.payment_method_id]
            payment_method["balance"] += payment.amount
            payment_method["balance"] = round(payment_method["balance"], 2)
            db.DB["users"] = users

    order.status = "cancelled"
    order.payment_history.extend(refunds)

    orders[order_id] = order.model_dump(mode="json")
    db.DB["orders"] = orders

    output = CancelPendingOrderOutput(**order.model_dump(mode="json"), cancel_reason=reason)
    return output.model_dump(mode="json")
