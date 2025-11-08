from typing import Optional, List
from retail.get_order_details_tool import get_order_details
from retail.get_product_details_tool import get_product_details
from retail.get_user_details_tool import get_user_details
from retail.list_all_product_types_tool import list_all_product_types

def get_details(
    order_id: Optional[str] = None,
    product_id: Optional[str] = None,
    user_id: Optional[str] = None,
    list_product_types: bool = False
) -> dict:
    """
    Retrieves details for an order, product, or user, or lists all product types.

    Only one action can be performed per call.

    Args:
        order_id (Optional[str]): The ID of the order to retrieve.
        product_id (Optional[str]): The ID of the product to retrieve.
        user_id (Optional[str]): The ID of the user to retrieve.
        list_product_types (bool): If True, lists all available product types.

    Returns:
        dict: A dictionary containing the requested details. The structure of the dictionary
        varies based on the action performed.

        If `order_id` is provided, returns order details:
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

        If `product_id` is provided, returns product details:
        - name (str): The name of the product.
        - product_id (str): The ID of the product.
        - variants (dict): A dictionary of variants for the product.
            - item_id (str): The ID of the item.
            - options (dict): The options for the item.
            - available (bool): Whether the item is available.
            - price (float): The price of the item.

        If `user_id` is provided, returns user details:
        - name (dict): The name of the user.
            - first_name (str): The first name of the user.
            - last_name (str): The last name of the user.
        - address (dict): The address of the user.
            - address1 (str): The first line of the address.
            - address2 (str): The second line of the address.
            - city (str): The city of the address.
            - country (str): The country of the address.
            - state (str): The state of the address.
            - zip (str): The zip code of the address.
        - email (str): The email of the user.
        - payment_methods (dict): A dictionary of payment methods.
            - id (str): The ID of the payment method.
            - source (str): The source of the payment method.
            - brand (str, optional): The brand of the credit card.
            - last_four (str, optional): The last four digits of the credit card.
            - balance (int, optional): The balance of the gift card.
        - orders (list): A list of order IDs for the user.

        If `list_product_types` is True, returns a dictionary of product types:
        - products (dict): A dictionary where keys are product names and values are product IDs.

    Raises:
        ValueError: If more than one ID is provided or if no action is specified.
        Exception: If the requested resource is not found or another error occurs.
    """
    try:
        action_count = sum([order_id is not None, product_id is not None, user_id is not None, list_product_types])
        if action_count > 1:
            raise ValueError("Only one type of detail can be requested at a time.")

        if order_id:
            return get_order_details(order_id=order_id)
        elif product_id:
            return get_product_details(product_id=product_id)
        elif user_id:
            return get_user_details(user_id=user_id)
        elif list_product_types:
            return list_all_product_types()
        else:
            raise ValueError("No action specified. Provide an ID or set list_product_types to True.")
    except Exception as e:
        raise e
