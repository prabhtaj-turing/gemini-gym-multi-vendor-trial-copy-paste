from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict, List
from pydantic import ValidationError
from retail.SimulationEngine.custom_errors import (
    InsufficientGiftCardBalanceError,
    ItemMismatchError,
    ItemNotAvailableError,
    ItemNotFoundError,
    NonDeliveredOrderError,
    OrderNotFoundError,
    PaymentMethodNotFoundError,
    InvalidInputError,
)
from retail.SimulationEngine import db
from retail.SimulationEngine.models import (
    ExchangeDeliveredOrderItemsInput,
    ExchangeDeliveredOrderItemsOutput,
    Order,
)


@tool_spec(
    spec={
        'name': 'exchange_delivered_order_items',
        'description': """ Exchange items in a delivered order to new items of the same product type.
        
        For a delivered order, return or exchange can be only done once by the agent.
        The agent needs to explain the exchange detail and ask for explicit user
        confirmation (yes/no) to proceed. """,
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
                    'description': """ The item ids to be exchanged, each such as '1008292230'.
                    There could be duplicate items in the list. """,
                    'items': {
                        'type': 'string'
                    }
                },
                'new_item_ids': {
                    'type': 'array',
                    'description': """ The item ids to be exchanged for, each such as
                    '1008292230'. There could be duplicate items in the list. Each new
                    item id should match the item id in the same position and be of the
                    same product. """,
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
                'new_item_ids',
                'payment_method_id'
            ]
        }
    }
)
def exchange_delivered_order_items(
    order_id: str,
    item_ids: List[str],
    new_item_ids: List[str],
    payment_method_id: str,
) -> Dict[str, Any]:
    """Exchange items in a delivered order to new items of the same product type.

    For a delivered order, return or exchange can be only done once by the agent.
    The agent needs to explain the exchange detail and ask for explicit user
    confirmation (yes/no) to proceed.

    Args:
        order_id (str): The order id, such as '#W0000000'. Be careful there is a '#'
            symbol at the beginning of the order id.
        item_ids (List[str]): The item ids to be exchanged, each such as '1008292230'.
            There could be duplicate items in the list.
        new_item_ids (List[str]): The item ids to be exchanged for, each such as
            '1008292230'. There could be duplicate items in the list. Each new
            item id should match the item id in the same position and be of the
            same product.
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
            - exchange_items (Optional[List[str]]): A list of the exchanged item IDs.
            - exchange_new_items (Optional[List[str]]): A list of the new item IDs.
            - exchange_payment_method_id (Optional[str]): The payment method ID used for the exchange.
            - exchange_price_difference (Optional[float]): The price difference of the exchange.

    Raises:
        OrderNotFoundError: If the order is not found.
        NonDeliveredOrderError: If the order is not in a 'delivered' state.
        ItemNotFoundError: If an item to be exchanged is not found in the order.
        ItemMismatchError: If the number of items to be exchanged does not match the number of new items.
        ItemNotAvailableError: If a new item is not available.
        PaymentMethodNotFoundError: If the payment method is not found.
        InsufficientGiftCardBalanceError: If the gift card balance is insufficient.
        InvalidInputError: If the input is invalid.
    """
    try:
        ExchangeDeliveredOrderItemsInput(
            order_id=order_id,
            item_ids=item_ids,
            new_item_ids=new_item_ids,
            payment_method_id=payment_method_id,
        )
    except ValidationError as e:
        raise InvalidInputError(e)

    products, orders, users = db.DB["products"], db.DB["orders"], db.DB["users"]

    if order_id not in orders:
        raise OrderNotFoundError("Error: order not found")
    order = Order(**orders[order_id])
    if order.status != "delivered":
        raise NonDeliveredOrderError("Error: non-delivered order cannot be exchanged")

    all_item_ids = [item.item_id for item in order.items]
    for item_id in item_ids:
        if item_ids.count(item_id) > all_item_ids.count(item_id):
            raise ItemNotFoundError(f"Error: {item_id} not found")

    if len(item_ids) != len(new_item_ids):
        raise ItemMismatchError("Error: the number of items to be exchanged should match")

    diff_price = 0.0
    for item_id, new_item_id in zip(item_ids, new_item_ids):
        item = [item for item in order.items if item.item_id == item_id][0]
        product_id = item.product_id
        if not (
            new_item_id in products[product_id]["variants"]
            and products[product_id]["variants"][new_item_id]["available"]
        ):
            raise ItemNotAvailableError(f"Error: new item {new_item_id} not found or available")

        old_price = item.price
        new_price = products[product_id]["variants"][new_item_id]["price"]
        diff_price += new_price - old_price

    diff_price = round(diff_price, 2)

    if payment_method_id not in users[order.user_id]["payment_methods"]:
        raise PaymentMethodNotFoundError("Error: payment method not found")

    payment_method = users[order.user_id]["payment_methods"][payment_method_id]
    if "gift_card" in payment_method_id and payment_method.get("balance", 0) < diff_price:
        raise InsufficientGiftCardBalanceError(
            "Error: insufficient gift card balance to pay for the price difference"
        )

    order.status = "exchange requested"

    orders[order_id] = order.model_dump(mode="json")
    orders[order_id]["exchange_items"] = sorted(item_ids)
    orders[order_id]["exchange_new_items"] = sorted(new_item_ids)
    orders[order_id]["exchange_payment_method_id"] = payment_method_id
    orders[order_id]["exchange_price_difference"] = diff_price
    db.DB["orders"] = orders

    output = ExchangeDeliveredOrderItemsOutput(**orders[order_id])
    return output.model_dump(mode="json")
