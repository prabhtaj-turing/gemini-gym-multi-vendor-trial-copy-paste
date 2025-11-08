from typing import Optional, List, Dict
from retail.cancel_pending_order_tool import cancel_pending_order
from retail.modify_pending_order_address_tool import modify_pending_order_address
from retail.modify_pending_order_items_tool import modify_pending_order_items
from retail.modify_pending_order_payment_tool import modify_pending_order_payment
from retail.return_delivered_order_items_tool import return_delivered_order_items
from retail.exchange_delivered_order_items_tool import exchange_delivered_order_items

def update_order(
    order_id: str,
    cancel: bool = False,
    new_address_id: Optional[str] = None,
    items_to_add: Optional[List[Dict]] = None,
    items_to_remove: Optional[List[str]] = None,
    new_payment_method_id: Optional[str] = None,
    items_to_return: Optional[List[Dict]] = None,
    items_to_exchange: Optional[List[Dict]] = None,
) -> Dict:
    """
    Updates an order by performing one of several actions, such as cancellation,
    modifying address, items, or payment for pending orders, or returning/exchanging
    items for delivered orders.

    Only one action can be performed per call.

    Args:
        order_id (str): The ID of the order to update.
        cancel (bool): If True, cancels the order. The order must be pending.
        new_address_id (Optional[str]): The new address ID for the order. The order must be pending.
        items_to_add (Optional[List[Dict]]): A list of items to add to the order. The order must be pending.
                      Each item is a dictionary with "product_id" and "quantity".
        items_to_remove (Optional[List[str]]): A list of item IDs to remove from the order. The order must be pending.
        new_payment_method_id (Optional[str]): The new payment method ID. The order must be pending.
        items_to_return (Optional[List[Dict]]): A list of items to return. The order must be delivered.
                         Each item is a dictionary with "item_id" and "quantity".
        items_to_exchange (Optional[List[Dict]]): A list of items to exchange. The order must be delivered.
                           Each item is a dictionary with "item_id", "new_product_id", and "quantity".

    Returns:
        Dict: A dictionary containing the result of the update operation.
        The structure of the dictionary varies based on the action performed.

        For `cancel=True`:
            A dictionary with a "message" key confirming the cancellation.
            Example: `{"message": "Order #12345 has been canceled."}`

        For `new_address_id`, `items_to_add`, `items_to_remove`, or `new_payment_method_id`:
            A dictionary containing the updated order information with the following structure:
            - order (dict):
                - order_id (str): The ID of the order.
                - user_id (str): The ID of the user who placed the order.
                - address (dict): The shipping address for the order.
                    - address1 (str): The first line of the address.
                    - address2 (str): The second line of the address.
                    - city (str): The city of the address.
                    - country (str): The country of the address.
                    - state (str): The state of the address.
                    - zip (str): The zip code of the address.
                - items (list): A list of items in the order.
                    - name (str): The name of the item.
                    - product_id (str): The ID of the product.
                    - item_id (str): The ID of the item.
                    - price (float): The price of the item.
                    - options (dict): The options for the item.
                - fulfillments (list): A list of fulfillments for the order.
                    - tracking_id (list): A list of tracking IDs for the fulfillment.
                    - item_ids (list): A list of item IDs in the fulfillment.
                - status (str): The status of the order.
                - payment_history (list): A list of payment transactions for the order.
                    - transaction_type (str): The type of transaction.
                    - amount (float): The amount of the transaction.
                    - payment_method_id (str): The ID of the payment method.

        For `items_to_return`:
            A dictionary containing the updated order and return details:
            - order_id (str): The ID of the order.
            - user_id (str): The ID of the user.
            - ... (other order fields as above)
            - return_items (list): A list of the returned item IDs.
            - return_payment_method_id (str): The payment method ID used for the return.

        For `items_to_exchange`:
            A dictionary containing the updated order and exchange details:
            - order_id (str): The ID of the order.
            - user_id (str): The ID of the user.
            - ... (other order fields as above)
            - exchange_items (list): A list of the exchanged item IDs.
            - exchange_new_items (list): A list of the new item IDs.
            - exchange_payment_method_id (str): The payment method ID used for the exchange.
            - exchange_price_difference (float): The price difference of the exchange.

    Raises:
        ValueError: If multiple actions are specified in a single call or no action is specified.
        Exception: If an error occurs during the update process.
    """
    try:
        action_count = sum(
            [
                cancel,
                new_address_id is not None,
                (items_to_add is not None or items_to_remove is not None),
                new_payment_method_id is not None,
                items_to_return is not None,
                items_to_exchange is not None,
            ]
        )

        if action_count > 1:
            raise ValueError("Only one type of update action can be specified at a time.")
        
        if action_count == 0:
            raise ValueError("No update action specified.")

        if cancel:
            return cancel_pending_order(order_id=order_id)
        if new_address_id:
            return {"order": modify_pending_order_address(order_id=order_id, new_address_id=new_address_id)}
        if items_to_add is not None or items_to_remove is not None:
            return {"order": modify_pending_order_items(order_id=order_id, items_to_add=items_to_add, items_to_remove=items_to_remove)}
        if new_payment_method_id:
            return {"order": modify_pending_order_payment(order_id=order_id, payment_method_id=new_payment_method_id)}
        if items_to_return:
            return return_delivered_order_items(order_id=order_id, items=items_to_return)
        if items_to_exchange:
            return exchange_delivered_order_items(order_id=order_id, items_to_exchange=items_to_exchange)

    except Exception as e:
        raise e
