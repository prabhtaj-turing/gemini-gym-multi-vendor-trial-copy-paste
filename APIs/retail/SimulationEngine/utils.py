import random
from typing import Any, Dict, List, Optional
from pydantic import ValidationError
from retail.SimulationEngine import db
from retail.SimulationEngine.models import (
    User,
    Order,
    Product,
)
from retail.SimulationEngine.custom_errors import InvalidInputError, DataConflictError


# User CRUD operations

def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single user by their ID.

    Args:
        user_id (str): The ID of the user to retrieve.

    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the user, or None if not found, with the following structure:
            - name (Dict[str, str]): The name of the user.
                - first_name (str): The first name of the user.
                - last_name (str): The last name of the user.
            - address (Dict[str, str]): The address of the user.
                - address1 (str): The first line of the address.
                - address2 (str): The second line of the address.
                - city (str): The city of the address.
                - country (str): The country of the address.
                - state (str): The state of the address.
                - zip (str): The zip code of the address.
            - email (str): The email of the user.
            - payment_methods (Dict[str, Dict[str, Any]]): A dictionary of payment methods, where the key is the payment method ID.
                - id (str): The ID of the payment method.
                - source (str): The source of the payment method, one of 'credit_card', 'gift_card', or 'paypal'.
                - brand (Optional[str]): The brand of the credit card (if source is 'credit_card').
                - last_four (Optional[str]): The last four digits of the credit card (if source is 'credit_card').
                - balance (Optional[int]): The balance of the gift card (if source is 'gift_card').
            - orders (List[str]): A list of order IDs for the user.
    """
    return db.DB["users"].get(user_id)


def list_users(limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Lists all users with optional pagination.

    Args:
        limit (Optional[int]): The maximum number of users to return.
        offset (int): The number of users to skip.

    Returns:
        List[Dict[str, Any]]: A list of user dictionaries, where each dictionary has the following structure:
            - name (Dict[str, str]): The name of the user.
                - first_name (str): The first name of the user.
                - last_name (str): The last name of the user.
            - address (Dict[str, str]): The address of the user.
                - address1 (str): The first line of the address.
                - address2 (str): The second line of the address.
                - city (str): The city of the address.
                - country (str): The country of the address.
                - state (str): The state of the address.
                - zip (str): The zip code of the address.
            - email (str): The email of the user.
            - payment_methods (Dict[str, Dict[str, Any]]): A dictionary of payment methods, where the key is the payment method ID.
                - id (str): The ID of the payment method.
                - source (str): The source of the payment method, one of 'credit_card', 'gift_card', or 'paypal'.
                - brand (Optional[str]): The brand of the credit card (if source is 'credit_card').
                - last_four (Optional[str]): The last four digits of the credit card (if source is 'credit_card').
                - balance (Optional[int]): The balance of the gift card (if source is 'gift_card').
            - orders (List[str]): A list of order IDs for the user.
    """
    users = list(db.DB["users"].values())
    if limit is None:
        return users[offset:]
    return users[offset: offset + limit]


def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new user.

    Args:
        user_data (Dict[str, Any]): A dictionary containing the user's data, with the following structure:
            - name (Dict[str, str]): The name of the user.
                - first_name (str): The first name of the user.
                - last_name (str): The last name of the user.
            - address (Dict[str, str]): The address of the user.
                - address1 (str): The first line of the address.
                - address2 (str): The second line of the address.
                - city (str): The city of the address.
                - country (str): The country of the address.
                - state (str): The state of the address.
                - zip (str): The zip code of the address.
            - email (str): The email of the user.
            - payment_methods (Dict[str, Dict[str, Any]]): A dictionary of payment methods, where the key is the payment method ID.
                - id (str): The ID of the payment method.
                - source (str): The source of the payment method, one of 'credit_card', 'gift_card', or 'paypal'.
                - brand (Optional[str]): The brand of the credit card (if source is 'credit_card').
                - last_four (Optional[str]): The last four digits of the credit card (if source is 'credit_card').
                - balance (Optional[int]): The balance of the gift card (if source is 'gift_card').
            - orders (List[str]): A list of order IDs for the user.

    Returns:
        Dict[str, Any]: The dictionary of the created user, same as the input data.

    Raises:
        InvalidInputError: If the input data is invalid.
        DataConflictError: If there are data inconsistencies.
    """
    try:
        user = User(**user_data)
        for existing_user in db.DB["users"].values():
            if existing_user["email"] == user.email:
                raise DataConflictError(f"User with email {user.email} already exists.")

        user_id = f"{user.name.first_name.lower()}_{user.name.last_name.lower()}_{random.randint(1000, 9999)}"

        for order_id in user.orders:
            if order_id not in db.DB["orders"]:
                raise DataConflictError(f"Order {order_id} not found.")
            if db.DB["orders"][order_id]["user_id"] != user_id:
                raise DataConflictError(f"Order {order_id} does not belong to user {user_id}.")

        db.DB["users"][user_id] = user.model_dump(mode="json")
        return user.model_dump(mode="json")
    except ValidationError as e:
        raise InvalidInputError(e)


def update_user(user_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Updates an existing user.

    Args:
        user_id (str): The ID of the user to update.
        update_data (Dict[str, Any]): A dictionary with the fields to update. See the `create_user` function for the full structure.

    Returns:
        Optional[Dict[str, Any]]: The updated user dictionary, or None if the user was not found, same as the input data.
    
    Raises:
        InvalidInputError: If the input data is invalid.
        DataConflictError: If there are data inconsistencies.
    """
    if user_id not in db.DB["users"]:
        return None

    user_data = db.DB["users"][user_id]
    user_data.update(update_data)

    try:
        updated_user = User(**user_data)
        for order_id in updated_user.orders:
            if order_id not in db.DB["orders"]:
                raise DataConflictError(f"Order {order_id} not found.")
            if db.DB["orders"][order_id]["user_id"] != user_id:
                raise DataConflictError(f"Order {order_id} does not belong to user {user_id}.")

        db.DB["users"][user_id] = updated_user.model_dump(mode="json")
        return updated_user.model_dump(mode="json")
    except ValidationError as e:
        raise InvalidInputError(e)


def delete_user(user_id: str) -> bool:
    """
    Deletes a user by their ID.

    Args:
        user_id (str): The ID of the user to delete.

    Returns:
        bool: True if the user was deleted, False otherwise.
    """
    if user_id in db.DB["users"]:
        del db.DB["users"][user_id]
        return True
    return False


# Order CRUD operations

def get_order(order_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single order by its ID.

    Args:
        order_id (str): The ID of the order to retrieve.

    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the order, or None if not found, with the following structure:
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
    """
    return db.DB["orders"].get(order_id)


def list_orders(limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Lists all orders with optional pagination.

    Args:
        limit (Optional[int]): The maximum number of orders to return.
        offset (int): The number of orders to skip.

    Returns:
        List[Dict[str, Any]]: A list of order dictionaries, where each dictionary has the following structure:
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
    """
    orders = list(db.DB["orders"].values())
    if limit is None:
        return orders[offset:]
    return orders[offset: offset + limit]


def create_order(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new order.

    Args:
        order_data (Dict[str, Any]): A dictionary containing the order's data, with the following structure:
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

    Returns:
        Dict[str, Any]: The dictionary of the created order, same as the input data with auto-generated order_id.

    Raises:
        InvalidInputError: If the input data is invalid.
        DataConflictError: If there are data inconsistencies.
    """
    try:
        order = Order(**order_data)
        order_id = order.order_id
        if order_id in db.DB["orders"]:
            raise DataConflictError(f"Order with ID {order_id} already exists.")
        if order.user_id not in db.DB["users"]:
            raise DataConflictError(f"User {order.user_id} not found.")

        total_price = sum(item.price for item in order.items)
        total_payment = sum(p.amount for p in order.payment_history if p.transaction_type == 'payment')
        if total_payment > total_price:
            raise DataConflictError("Payment amount cannot exceed total price of items.")

        for item in order.items:
            if item.product_id not in db.DB["products"]:
                raise DataConflictError(f"Product {item.product_id} not found.")
            product = db.DB["products"][item.product_id]
            if item.item_id not in product["variants"]:
                raise DataConflictError(f"Item {item.item_id} not found in product {item.product_id}.")

        db.DB["orders"][order_id] = order.model_dump(mode="json")
        db.DB["users"][order.user_id]["orders"].append(order_id)
        return order.model_dump(mode="json")
    except ValidationError as e:
        raise InvalidInputError(e)


def update_order(order_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Updates an existing order.

    Args:
        order_id (str): The ID of the order to update.
        update_data (Dict[str, Any]): A dictionary with the fields to update. See the `create_order` function for the full structure.

    Returns:
        Optional[Dict[str, Any]]: The updated order dictionary, or None if the order was not found, same as the input data for `update_data` field.
    
    Raises:
        InvalidInputError: If the input data is invalid.
        DataConflictError: If there are data inconsistencies.
    """
    if order_id not in db.DB["orders"]:
        return None

    order_data = db.DB["orders"][order_id]
    order_data.update(update_data)

    try:
        updated_order = Order(**order_data)
        if updated_order.user_id not in db.DB["users"]:
            raise DataConflictError(f"User {updated_order.user_id} not found.")

        total_price = sum(item.price for item in updated_order.items)
        total_payment = sum(p.amount for p in updated_order.payment_history if p.transaction_type == 'payment')
        if total_payment > total_price:
            raise DataConflictError("Payment amount cannot exceed total price of items.")

        for item in updated_order.items:
            if item.product_id not in db.DB["products"]:
                raise DataConflictError(f"Product {item.product_id} not found.")
            product = db.DB["products"][item.product_id]
            if item.item_id not in product["variants"]:
                raise DataConflictError(f"Item {item.item_id} not found in product {item.product_id}.")

        db.DB["orders"][order_id] = updated_order.model_dump(mode="json")
        return updated_order.model_dump(mode="json")
    except ValidationError as e:
        raise InvalidInputError(e)


def delete_order(order_id: str) -> bool:
    """
    Deletes an order by its ID.

    Args:
        order_id (str): The ID of the order to delete.

    Returns:
        bool: True if the order was deleted, False otherwise.
    """
    if order_id in db.DB["orders"]:
        user_id = db.DB["orders"][order_id]["user_id"]
        del db.DB["orders"][order_id]
        if user_id in db.DB["users"]:
            db.DB["users"][user_id]["orders"].remove(order_id)
        return True
    return False


# Product CRUD operations

def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a single product by its ID.

    Args:
        product_id (str): The ID of the product to retrieve.

    Returns:
        Optional[Dict[str, Any]]: A dictionary representing the product, or None if not found, with the following structure:
            - name (str): The name of the product.
            - product_id (str): The ID of the product.
            - variants (Dict[str, Dict[str, Any]]): A dictionary of variants for the product, where the key is the item ID.
                - item_id (str): The ID of the item.
                - options (Dict[str, str]): The options for the item.
                - available (bool): Whether the item is available.
                - price (float): The price of the item.
    """
    return db.DB["products"].get(product_id)


def list_products(limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Lists all products with optional pagination.

    Args:
        limit (Optional[int]): The maximum number of products to return.
        offset (int): The number of products to skip.

    Returns:
        List[Dict[str, Any]]: A list of product dictionaries, where each dictionary has the following structure:
            - name (str): The name of the product.
            - product_id (str): The ID of the product.
            - variants (Dict[str, Dict[str, Any]]): A dictionary of variants for the product, where the key is the item ID.
                - item_id (str): The ID of the item.
                - options (Dict[str, str]): The options for the item.
                - available (bool): Whether the item is available.
                - price (float): The price of the item.
    """
    products = list(db.DB["products"].values())
    if limit is None:
        return products[offset:]
    return products[offset: offset + limit]


def create_product(product_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new product.

    Args:
        product_data (Dict[str, Any]): A dictionary containing the product's data, with the following structure:
            - name (str): The name of the product.
            - variants (Dict[str, Dict[str, Any]]): A dictionary of variants for the product, where the key is the item ID.
                - item_id (str): The ID of the item.
                - options (Dict[str, str]): The options for the item.
                - available (bool): Whether the item is available.
                - price (float): The price of the item.

    Returns:
        Dict[str, Any]: The dictionary of the created product, same as the input data with auto-generated product_id.

    Raises:
        InvalidInputError: If the input data is invalid.
    """
    try:
        product = Product(**product_data)
        product_id = product.product_id
        if product_id in db.DB["products"]:
            raise DataConflictError(f"Product with ID {product_id} already exists.")
        db.DB["products"][product_id] = product.model_dump(mode="json")
        return product.model_dump(mode="json")
    except ValidationError as e:
        raise InvalidInputError(e)


def update_product(product_id: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Updates an existing product.

    Args:
        product_id (str): The ID of the product to update.
        update_data (Dict[str, Any]): A dictionary with the fields to update. See the `create_product` function for the full structure.

    Returns:
        Optional[Dict[str, Any]]: The updated product dictionary, or None if the product was not found, same as the input data for `update_data` field, with auto-generated product_id.
    """
    if product_id in db.DB["products"]:
        product_data = db.DB["products"][product_id]
        product_data.update(update_data)
        try:
            updated_product = Product(**product_data)
            db.DB["products"][product_id] = updated_product.model_dump(mode="json")
            return updated_product.model_dump(mode="json")
        except ValidationError as e:
            raise InvalidInputError(e)
    return None


def delete_product(product_id: str) -> bool:
    """
    Deletes a product by its ID.

    Args:
        product_id (str): The ID of the product to delete.

    Returns:
        bool: True if the product was deleted, False otherwise.
    """
    if product_id in db.DB["products"]:
        del db.DB["products"][product_id]
        return True
    return False

