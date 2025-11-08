from common_utils.tool_spec_decorator import tool_spec
from typing import Any, Dict, Optional
from pydantic import ValidationError
from retail.SimulationEngine.custom_errors import (
    OrderNotFoundError,
    NonPendingOrderError,
    InvalidInputError,
)
from retail.SimulationEngine import db
from retail.SimulationEngine.models import (
    ModifyPendingOrderAddressInput,
    Order,
    Address,
)


@tool_spec(
    spec={
        'name': 'modify_pending_order_address',
        'description': """ Modify the shipping address of a pending order.
        
        The agent needs to explain the modification detail and ask for explicit user
        confirmation (yes/no) to proceed. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'order_id': {
                    'type': 'string',
                    'description': "The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id."
                },
                'address1': {
                    'type': 'string',
                    'description': "The first line of the address, such as '123 Main St'."
                },
                'address2': {
                    'type': 'string',
                    'description': "The second line of the address, such as 'Apt 1' or ''."
                },
                'city': {
                    'type': 'string',
                    'description': "The city, such as 'San Francisco'."
                },
                'state': {
                    'type': 'string',
                    'description': "The state, such as 'CA'."
                },
                'country': {
                    'type': 'string',
                    'description': "The country, such as 'USA'."
                },
                'zip_code': {
                    'type': 'string',
                    'description': "The zip code, such as '12345'."
                }
            },
            'required': [
                'order_id',
                'address1',
                'address2',
                'city',
                'state',
                'country',
                'zip_code'
            ]
        }
    }
)
def modify_pending_order_address(
    order_id: str,
    address1: str,
    address2: str,
    city: str,
    state: str,
    country: str,
    zip_code: str,
) -> Dict[str, Any]:
    """Modify the shipping address of a pending order.

    The agent needs to explain the modification detail and ask for explicit user
    confirmation (yes/no) to proceed.

    Args:
        order_id (str): The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.
        address1 (str): The first line of the address, such as '123 Main St'.
        address2 (str): The second line of the address, such as 'Apt 1' or ''.
        city (str): The city, such as 'San Francisco'.
        state (str): The state, such as 'CA'.
        country (str): The country, such as 'USA'.
        zip_code (str): The zip code, such as '12345'.

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
        NonPendingOrderError: If the order is not in a 'pending' state.
        InvalidInputError: If the input is invalid.
    """
    try:
        ModifyPendingOrderAddressInput(
            order_id=order_id,
            address1=address1,
            address2=address2,
            city=city,
            state=state,
            country=country,
            zip=zip_code,
        )
    except ValidationError as e:
        raise InvalidInputError(e)

    orders = db.DB["orders"]
    if order_id not in orders:
        raise OrderNotFoundError("Error: order not found")

    order = Order(**orders[order_id])
    if order.status != "pending" and order.status != "pending (item modified)":
        raise NonPendingOrderError("Error: non-pending order cannot be modified")

    order.address = Address(
        address1=address1,
        address2=address2,
        city=city,
        state=state,
        country=country,
        zip=zip_code,
    )
    
    orders[order_id] = order.model_dump(mode="json")
    db.DB["orders"] = orders

    return order.model_dump(mode="json")
