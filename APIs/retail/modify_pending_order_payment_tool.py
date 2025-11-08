from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict
from pydantic import ValidationError
from retail.SimulationEngine.custom_errors import (
    OrderNotFoundError,
    NonPendingOrderError,
    PaymentMethodNotFoundError,
    InvalidPaymentInfoError,
    SamePaymentMethodError,
    InsufficientGiftCardBalanceError,
    InvalidInputError,
)
from retail.SimulationEngine import db
from retail.SimulationEngine.models import (
    ModifyPendingOrderPaymentInput,
    Order,
    PaymentHistory,
)


@tool_spec(
    spec={
        'name': 'modify_pending_order_payment',
        'description': """ Modify the payment method of a pending order.
        
        The agent needs to explain the modification detail and ask for explicit user
        confirmation (yes/no) to proceed. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'order_id': {
                    'type': 'string',
                    'description': """ The order id, such as '#W0000000'. Be careful there is a '#'
                    symbol at the beginning of the order id. """
                },
                'payment_method_id': {
                    'type': 'string',
                    'description': """ The payment method id to pay or receive refund for
                    the item price difference, such as 'gift_card_0000000' or
                    'credit_card_0000000'. These can be looked up from the user or
                    order details. """
                }
            },
            'required': [
                'order_id',
                'payment_method_id'
            ]
        }
    }
)
def modify_pending_order_payment(
    order_id: str,
    payment_method_id: str,
) -> Dict[str, Any]:
    """Modify the payment method of a pending order.

    The agent needs to explain the modification detail and ask for explicit user
    confirmation (yes/no) to proceed.

    Args:
        order_id (str): The order id, such as '#W0000000'. Be careful there is a '#'
            symbol at the beginning of the order id.
        payment_method_id (str): The payment method id to pay or receive refund for
            the item price difference, such as 'gift_card_0000000' or
            'credit_card_0000000'. These can be looked up from the user or
            order details.

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

    Raises:
        OrderNotFoundError: If the order is not found.
        NonPendingOrderError: If the order is not pending.
        PaymentMethodNotFoundError: If the payment method is not found.
        InvalidPaymentInfoError: If the payment history is invalid.
        SamePaymentMethodError: If the new payment method is the same as the old one.
        InsufficientGiftCardBalanceError: If the gift card balance is insufficient.
        InvalidInputError: If the input is invalid.
    """
    try:
        ModifyPendingOrderPaymentInput(
            order_id=order_id,
            payment_method_id=payment_method_id,
        )
    except ValidationError as e:
        raise InvalidInputError(e)

    orders = db.DB["orders"]
    users = db.DB["users"]

    if order_id not in orders:
        raise OrderNotFoundError("Error: order not found")
    order = Order(**orders[order_id])
    if order.status != "pending" and order.status != "pending (item modified)":
        raise NonPendingOrderError("Error: non-pending order cannot be modified")

    if payment_method_id not in users[order.user_id]["payment_methods"]:
        raise PaymentMethodNotFoundError("Error: payment method not found")

    if (
        len(order.payment_history) > 1
        or order.payment_history[0].transaction_type != "payment"
    ):
        raise InvalidPaymentInfoError("Error: there should be exactly one payment for a pending order")

    if order.payment_history[0].payment_method_id == payment_method_id:
        raise SamePaymentMethodError(
            "Error: the new payment method should be different from the current one"
        )

    amount = order.payment_history[0].amount
    payment_method = users[order.user_id]["payment_methods"][payment_method_id]

    if "gift_card" in payment_method_id and payment_method.get("balance", 0) < amount:
        raise InsufficientGiftCardBalanceError(
            "Error: insufficient gift card balance to pay for the order"
        )

    order.payment_history.extend(
        [
            PaymentHistory(
                transaction_type="payment",
                amount=amount,
                payment_method_id=payment_method_id,
            ),
            PaymentHistory(
                transaction_type="refund",
                amount=amount,
                payment_method_id=order.payment_history[0].payment_method_id,
            ),
        ]
    )

    if "gift_card" in payment_method_id:
        payment_method["balance"] -= amount
        payment_method["balance"] = round(payment_method["balance"], 2)

    if "gift_card" in order.payment_history[0].payment_method_id:
        old_payment_method = users[order.user_id]["payment_methods"][
            order.payment_history[0].payment_method_id
        ]
        old_payment_method["balance"] += amount
        old_payment_method["balance"] = round(old_payment_method["balance"], 2)
        
    orders[order_id] = order.model_dump(mode="json")
    db.DB["orders"] = orders

    return order.model_dump(mode="json")
