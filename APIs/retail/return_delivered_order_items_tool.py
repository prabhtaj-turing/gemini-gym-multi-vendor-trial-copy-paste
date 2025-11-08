from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict, List
from pydantic import ValidationError
from retail.SimulationEngine.custom_errors import (
    OrderNotFoundError,
    NonDeliveredOrderError,
    PaymentMethodNotFoundError,
    InvalidReturnPaymentMethodError,
    ItemNotFoundError,
    InvalidInputError,
)
from retail.SimulationEngine import db
from retail.SimulationEngine.models import (
    ReturnDeliveredOrderItemsInput,
    ReturnDeliveredOrderItemsOutput,
    Order,
)


@tool_spec(
    spec={
        'name': 'return_delivered_order_items',
        'description': """ Return some items of a delivered order.
        
        The order status will be changed to 'return requested'. The agent needs to
        explain the return detail and ask for explicit user confirmation (yes/no) to
        proceed. The user will receive follow-up email for how and where to return
        the item. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'order_id': {
                    'type': 'string',
                    'description': """ The order id, such as '#W0000000'. Be careful there is a '#'
                    symbol at the beginning of the order id. """
                },
                'item_ids': {
                    'type': 'array',
                    'description': """ The item ids to be returned, each such as '1008292230'.
                    There could be duplicate items in the list. """,
                    'items': {
                        'type': 'string'
                    }
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
                'item_ids',
                'payment_method_id'
            ]
        }
    }
)
def return_delivered_order_items(
    order_id: str, item_ids: List[str], payment_method_id: str
) -> Dict[str, Any]:
    """Return some items of a delivered order.

    The order status will be changed to 'return requested'. The agent needs to
    explain the return detail and ask for explicit user confirmation (yes/no) to
    proceed. The user will receive follow-up email for how and where to return
    the item.

    Args:
        order_id (str): The order id, such as '#W0000000'. Be careful there is a '#'
            symbol at the beginning of the order id.
        item_ids (List[str]): The item ids to be returned, each such as '1008292230'.
            There could be duplicate items in the list.
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
        NonDeliveredOrderError: If the order is not delivered.
        PaymentMethodNotFoundError: If the payment method is not found.
        InvalidReturnPaymentMethodError: If the payment method is not the original or a gift card.
        ItemNotFoundError: If an item to be returned is not found.
        InvalidInputError: If the input is invalid.
    """
    try:
        ReturnDeliveredOrderItemsInput(
            order_id=order_id,
            item_ids=item_ids,
            payment_method_id=payment_method_id,
        )
    except ValidationError as e:
        raise InvalidInputError(e)

    orders = db.DB["orders"]
    users = db.DB["users"]

    if order_id not in orders:
        raise OrderNotFoundError("Error: order not found")
    order = Order(**orders[order_id])
    if order.status != "delivered":
        raise NonDeliveredOrderError("Error: non-delivered order cannot be returned")

    if payment_method_id not in users[order.user_id]["payment_methods"]:
        raise PaymentMethodNotFoundError("Error: payment method not found")
    if (
        "gift_card" not in payment_method_id
        and payment_method_id != order.payment_history[0].payment_method_id
    ):
        raise InvalidReturnPaymentMethodError(
            "Error: payment method should be either the original payment method or a gift card"
        )

    all_item_ids = [item.item_id for item in order.items]
    for item_id in item_ids:
        if item_ids.count(item_id) > all_item_ids.count(item_id):
            raise ItemNotFoundError("Error: some item not found")

    order.status = "return requested"
    
    orders[order_id] = order.model_dump(mode="json")
    orders[order_id]["return_items"] = sorted(item_ids)
    orders[order_id]["return_payment_method_id"] = payment_method_id
    db.DB["orders"] = orders

    output = ReturnDeliveredOrderItemsOutput(**orders[order_id])
    return output.model_dump(mode="json")
