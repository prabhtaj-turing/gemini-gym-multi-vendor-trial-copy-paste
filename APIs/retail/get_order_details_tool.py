from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict
from pydantic import ValidationError
from retail.SimulationEngine.custom_errors import OrderNotFoundError, InvalidInputError
from retail.SimulationEngine import db
from retail.SimulationEngine.models import (
    GetOrderDetailsInput,
    Order,
)


@tool_spec(
    spec={
        'name': 'get_order_details',
        'description': 'Get the status and details of an order.',
        'parameters': {
            'type': 'object',
            'properties': {
                'order_id': {
                    'type': 'string',
                    'description': """ The order id, such as '#W0000000'. Be careful there is a '#'
                    symbol at the beginning of the order id. """
                }
            },
            'required': [
                'order_id'
            ]
        }
    }
)
def get_order_details(order_id: str) -> Dict[str, Any]:
    """Get the status and details of an order.

    Args:
        order_id (str): The order id, such as '#W0000000'. Be careful there is a '#'
            symbol at the beginning of the order id.

    Returns:
        Dict[str, Any]: A dictionary representing the order with the following fields:
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
            - exchange_items (Optional[List[str]]): A list of the exchanged item IDs (present if order has exchanges).
            - exchange_new_items (Optional[List[str]]): A list of the new item IDs (present if order has exchanges).
            - exchange_payment_method_id (Optional[str]): The payment method ID used for the exchange (present if order has exchanges).
            - exchange_price_difference (Optional[float]): The price difference of the exchange (present if order has exchanges).
            - return_items (Optional[List[str]]): A list of the returned item IDs (present if order has returns).
            - return_payment_method_id (Optional[str]): The payment method ID used for the return (present if order has returns).

    Raises:
        OrderNotFoundError: If the order is not found.
        InvalidInputError: If the input is invalid.
    """
    try:
        GetOrderDetailsInput(order_id=order_id)
    except ValidationError as e:
        raise InvalidInputError(e)

    orders = db.DB["orders"]
    if order_id in orders:
        return Order(**orders[order_id]).model_dump(mode="json")
    raise OrderNotFoundError("Error: order not found")
