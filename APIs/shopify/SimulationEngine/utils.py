from common_utils.print_log import print_log
# utils.py

from typing import List, Optional, Tuple, Dict, Any, Union
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone, timezone, date
import json
import re
from . import custom_errors
import base64
import copy

from .models import ShopifyProductModel, ShopifyCustomerModel
from .db import DB



# Remove direct model imports to reduce coupling
# Database operations should be handled by a separate data access layer


# --- Consistency Maintenance Functions ---
def convert_datetimes_to_zulu_string(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = convert_datetimes_to_zulu_string(v)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            obj[i] = convert_datetimes_to_zulu_string(item)
    elif isinstance(obj, datetime):
        return obj.isoformat().replace('+00:00', 'Z')
    return obj


def update_customer_aggregates(
    customer_data: Dict[str, Any],
    customer_orders: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Updates customer aggregate fields based on new order data.

    Recalculates orders_count and total_spent by adding values from newly created orders. Only counts
    non-cancelled orders with valid financial status for aggregate calculations.

    Args:
        customer_data (Dict[str, Any]): Current customer record with keys:
            orders_count (int): Existing order count
            total_spent (str): Existing total spent as decimal string
        customer_orders (List[Dict[str, Any]]): New order objects to add to aggregates.
            Each order dict with keys: cancelled_at, financial_status, total_price

    Returns:
        Dict[str, Any]: Updated customer object with keys:
            orders_count (int): Incremented count including new valid orders
            total_spent (str): Updated total as decimal string
            updated_at (str): ISO 8601 timestamp of update
            (plus all original customer fields)

    Raises:
        None: Returns empty dict if customer_data is invalid.
    """
    if not customer_data:
        # Depending on desired behavior, you might raise an error or return an empty dict.
        # Returning the original data if it's empty might also be an option.
        return {}

    updated_customer = customer_data.copy()


    new_valid_orders_for_count = 0
    for order in customer_orders:
        if order.get('cancelled_at') is None or\
           order.get('financial_status') not in ['voided', None]: # financial_status can be None for pending orders.
            new_valid_orders_for_count += 1
            
    updated_customer['orders_count'] = updated_customer.get('orders_count', 0) + new_valid_orders_for_count

    current_total_spent = Decimal(updated_customer.get('total_spent', "0.00"))
    
    for order in customer_orders: # Iterate only through the NEW orders passed
        financial_status = order.get('financial_status')
        total_price_str = order.get('total_price', "0.00")

        
        should_add_to_spend = False
        if financial_status not in ['voided', 'cancelled', None]:
                 should_add_to_spend = True
        elif financial_status == 'cancelled' and total_price_str != "0.00" and order.get('refunds'):
            should_add_to_spend = True

        if should_add_to_spend:
            try:
                current_total_spent += Decimal(total_price_str)
            except InvalidOperation:
                pass

    updated_customer['total_spent'] = str(current_total_spent.quantize(Decimal("0.01")))
    updated_customer['updated_at'] = datetime.now(timezone.utc).isoformat()

    return updated_customer


def get_next_order_number(existing_orders_map: Dict[str, Any]) -> int:
    """Generates the next sequential order number for customer-facing order identification.
    
    Creates sequential order numbers starting from 1001 for better customer experience
    and order tracking. Scans existing orders to find the highest order number and 
    increments by 1 to ensure uniqueness and proper sequencing.
    
    Args:
        existing_orders_map (Dict[str, Any]): Dictionary of existing orders where keys are 
            order IDs and values are order dictionaries containing order_number fields.
            
    Returns:
        int: Next available order number. Returns 1001 if no orders exist, otherwise
            returns the highest existing order number + 1.
            
    Example:
        >>> orders = {"order1": {"order_number": 1001}, "order2": {"order_number": 1003}}
        >>> get_next_order_number(orders)
        1004
    """
    if not existing_orders_map:
        return 1001
    max_num = 0
    for order_details in existing_orders_map.values():
        if isinstance(order_details, dict) and isinstance(order_details.get("order_number"), int):
            max_num = max(max_num, order_details.get("order_number"))
    return max_num + 1 if max_num > 0 else 1001


def update_customer_gift_card_balance(
    customer_id: str,
    amount: str,
    operation: str = "add"
) -> Dict[str, Any]:
    """Updates a customer's gift card balance by adding or setting a specific amount.
    
    This utility manages customer gift card balances for promotions, refunds, and 
    administrative adjustments. Supports both additive operations (refunds, bonuses) 
    and absolute balance setting for account management. All operations maintain 
    transaction audit trails and prevent negative balances unless explicitly allowed.
    
    Args:
        customer_id (str): Unique identifier of the customer whose gift card balance to update.
            Must be a valid, existing customer ID.
        amount (str): Amount to add to balance or new balance amount as decimal string.
            Examples: "25.50", "100.00", "5.25". Must be positive for add operations.
        operation (str): Type of balance operation to perform.
            - "add": Adds amount to current balance (default, for refunds/bonuses)
            - "set": Sets balance to exact amount (for administrative corrections)
            Default is "add".
    
    Returns:
        Dict[str, Any]: Updated customer information with new gift card balance.
            customer (Dict[str, Any]): Customer object dict with keys:
                id (str): Customer identifier
                email (Optional[str]): Customer's email address
                first_name (Optional[str]): Customer's first name  
                last_name (Optional[str]): Customer's last name
                gift_card_balance (str): Updated gift card balance as decimal string
                updated_at (str): ISO 8601 timestamp when balance was last modified
                [other customer fields as per standard customer model]
    
    Raises:
        NoResultsFoundError: If no customer exists with the specified customer_id.
        InvalidInputError: If customer_id is empty, amount is not a valid decimal string, 
            operation is not 'add' or 'set', or amount would result in negative balance.
        InvalidParameterError: If amount is not a positive decimal for add operations.
    """
    # Import Decimal for precise financial calculations
    from decimal import Decimal, InvalidOperation
    import copy
    
    # Validate customer_id
    if not isinstance(customer_id, str) or not customer_id:
        raise custom_errors.InvalidInputError("customer_id must be a non-empty string.")
    
    # Validate operation
    if operation not in ["add", "set"]:
        raise custom_errors.InvalidInputError("operation must be either 'add' or 'set'.")
    
    # Validate amount format
    if not isinstance(amount, str):
        raise custom_errors.InvalidInputError("amount must be a string.")
    
    try:
        decimal_amount = Decimal(amount)
    except InvalidOperation:
        raise custom_errors.InvalidInputError("amount must be a valid decimal number string.")
    
    # Validate amount is non-negative
    if decimal_amount < Decimal("0"):
        raise custom_errors.InvalidParameterError("amount must be non-negative.")
    
    # Retrieve customer data
    customers_table = DB.get('customers', {})
    customer_data = customers_table.get(customer_id)
    
    if customer_data is None:
        raise custom_errors.NoResultsFoundError(f"Customer with ID '{customer_id}' not found.")
    
    # Calculate new balance
    current_balance = Decimal(customer_data.get('gift_card_balance', '0.00'))
    
    if operation == "add":
        new_balance = current_balance + decimal_amount
    else:  # operation == "set"
        new_balance = decimal_amount
    
    # Prevent negative balances
    if new_balance < Decimal("0"):
        raise custom_errors.InvalidParameterError("Operation would result in negative gift card balance.")
    
    # Update customer data
    customer_data = copy.deepcopy(customer_data)
    customer_data['gift_card_balance'] = str(new_balance.quantize(Decimal('0.01')))
    customer_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Save to database
    DB['customers'][customer_id] = customer_data
    
    return customer_data


def adjust_variant_inventory(
        product_data: Dict[str, Any],
        variant_id: str,
        quantity_delta: int
) -> Optional[Dict[str, Any]]:
    """
    Adjusts the inventory_quantity for a specific product variant.

    Args:
        product_data: Dictionary containing product information with variants
        variant_id: ID of the variant to update
        quantity_delta: Positive for increase (restock), negative for decrease (sale)

    Returns:
        Updated product dictionary or None if variant not found
    """
    if not product_data or 'variants' not in product_data:
        return None

    updated_product = json.loads(json.dumps(product_data))  # Deep copy
    variant_found = False

    for variant in updated_product['variants']:
        if variant.get('id') == variant_id:  # Assumes variant_id is a string for comparison
            if variant.get('inventory_management') == 'shopify':
                current_qty = variant.get('inventory_quantity', 0)
                variant['inventory_quantity'] = current_qty + quantity_delta
                variant['updated_at'] = datetime.utcnow().isoformat()
                updated_product['updated_at'] = datetime.utcnow().isoformat()
                variant_found = True
                break

    return updated_product if variant_found else None


def set_customer_default_address(
        customer_data: Dict[str, Any],
        address_id_to_make_default: str
) -> Optional[Dict[str, Any]]:
    """
    Sets a specific address as the default for a customer.

    Args:
        customer_data: Dictionary containing customer information
        address_id_to_make_default: ID of the address to make default

    Returns:
        Updated customer dictionary or None if address not found
    """
    if not customer_data or not customer_data.get('addresses'):
        return None

    # Get the complete customer data from the database to preserve all fields
    customer_id = customer_data.get('id')
    if not customer_id or customer_id not in DB.get('customers', {}):
        return None
    
    # Start with the complete customer data from DB
    updated_customer = copy.deepcopy(DB['customers'][customer_id])
    found_address_to_make_default = False
    new_default_address_data = None

    # Update the addresses from the input data (in case they were modified)
    if 'addresses' in customer_data:
        updated_customer['addresses'] = copy.deepcopy(customer_data['addresses'])

    for addr in updated_customer['addresses']:
        if addr.get('id') == address_id_to_make_default:  # Assumes address_id_to_make_default is a string
            addr['default'] = True
            new_default_address_data = addr.copy()
            found_address_to_make_default = True
        else:
            addr['default'] = False

    if found_address_to_make_default and new_default_address_data:
        updated_customer['default_address'] = new_default_address_data
        updated_customer['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        # Save the updated customer data to the database
        DB['customers'][customer_id] = updated_customer

    return updated_customer if found_address_to_make_default else None


# --- Utility/Interaction Functions ---

def find_product_variant_by_id(
        product_data: Dict[str, Any],
        variant_id: str  # Parameter is string
) -> Optional[Dict[str, Any]]:
    """
    Finds a specific product variant by its ID.

    Args:
        product_data: Dictionary containing product information
        variant_id: ID of the variant to find (string)

    Returns:
        Variant dictionary or None if not found
    """
    if not product_data or 'variants' not in product_data:
        return None

    for variant in product_data['variants']:
        if variant.get('id') == variant_id:  # Direct string comparison
            return variant
    return None


def find_product_variant_by_sku(
        products_data: List[Dict[str, Any]],
        sku: str
) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Finds a product and its variant by SKU across all products.

    Args:
        products_data: List of product dictionaries
        sku: SKU to search for

    Returns:
        Tuple of (product_dict, variant_dict) if found, None otherwise
    """
    if not sku or not products_data:
        return None

    for product in products_data:
        for variant in product.get('variants', []):
            if variant.get('sku') == sku:
                return product, variant
    return None


def get_new_line_item_id(line_items: List[Dict[str, Any]]) -> str:
    """
    Generates a new unique ID for a line item.
    Assumes IDs are numeric strings.

    Args:
        line_items: List of existing line item dictionaries

    Returns:
        New unique line item ID as string
    """
    if not line_items:
        return "1"

    max_id = 0
    for item in line_items:
        item_id_str = item.get('id')
        if item_id_str is not None:
            try:
                item_id_int = int(item_id_str)  # Handles numeric strings
                if item_id_int > max_id:
                    max_id = item_id_int
            except (ValueError, TypeError):
                continue  # Skip non-numeric string IDs
    return str(max_id + 1)


def get_new_transaction_id(transactions: List[Dict[str, Any]], refund_transactions: List[Dict[str, Any]] = None) -> str:
    """
    Generates a new unique ID for a transaction.
    Assumes IDs are numeric strings.

    Args:
        transactions: List of existing transaction dictionaries
        refund_transactions: Optional list of refund transaction dictionaries

    Returns:
        New unique transaction ID as string
    """
    all_transaction_ids: List[int] = []

    for t_list in [transactions, refund_transactions or []]:
        for t in t_list:
            t_id_str = t.get('id')
            if t_id_str is not None:
                try:
                    all_transaction_ids.append(int(t_id_str))  # Handles numeric strings
                except (ValueError, TypeError):
                    continue

    if not all_transaction_ids:
        return "1"
    return str(max(all_transaction_ids) + 1)


def get_new_refund_id(refunds: List[Dict[str, Any]]) -> str:
    """
    Generates a new unique ID for a refund.
    Assumes IDs are numeric strings.

    Args:
        refunds: List of existing refund dictionaries

    Returns:
        New unique refund ID as string
    """
    if not refunds:
        return "1"

    max_id = 0
    for refund in refunds:
        refund_id_str = refund.get('id')
        if refund_id_str is not None:
            try:
                refund_id_int = int(refund_id_str)  # Handles numeric strings
                if refund_id_int > max_id:
                    max_id = refund_id_int
            except (ValueError, TypeError):
                continue
    return str(max_id + 1)


def get_new_address_id_for_customer(addresses: List[Dict[str, Any]]) -> str:
    """
    Generates a new unique ID for an address.
    Assumes IDs are numeric strings.

    Args:
        addresses: List of existing address dictionaries

    Returns:
        New unique address ID as string
    """
    if not addresses:
        return "1"

    max_id = 0
    for addr in addresses:
        addr_id_str = addr.get('id')
        if addr_id_str is not None:
            try:
                addr_id_int = int(addr_id_str)  # Handles numeric strings
                if addr_id_int > max_id:
                    max_id = addr_id_int
            except (ValueError, TypeError):
                continue
    return str(max_id + 1)


# --- Additional Helper Functions ---

def generate_gid(resource_type: str, local_id: Union[str, int]) -> str:
    """
    Generates a predictable Shopify-like Global ID (GID).

    Args:
        resource_type: Type of resource (e.g., "Product", "Order")
        local_id: Local ID of the resource

    Returns:
        GID string in format "gid://shopify/ResourceType/id"
    """
    return f"gid://shopify/{resource_type}/{local_id}"


def update_order_financial_status(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Updates order financial status based on transaction and refund analysis.

    Analyzes all successful transactions and refunds to determine appropriate financial status. Handles
    authorization, capture, sale, refund, and void transaction types with proper status transitions.

    Args:
        order_data (Dict[str, Any]): Order record with keys:
            total_price (str): Order total as decimal string
            cancelled_at (str|None): Cancellation timestamp if cancelled
            transactions (List[Dict]): Transaction objects with keys: kind, status, amount, parent_id
            refunds (List[Dict]): Refund objects containing transaction arrays

    Returns:
        Dict[str, Any]: Updated order object with keys:
            financial_status (str): Calculated status ("pending", "authorized", "paid", 
                "partially_paid", "refunded", "partially_refunded", "voided")
            updated_at (str): ISO 8601 timestamp of update
            (plus all original order fields)
    """
    updated_order = json.loads(json.dumps(order_data))  # Deep copy

    if updated_order.get('cancelled_at') and not updated_order.get('transactions'):
        updated_order['financial_status'] = "voided"
        updated_order['updated_at'] = datetime.utcnow().isoformat()
        return updated_order

    total_paid = Decimal("0.00")
    total_refunded = Decimal("0.00")
    has_successful_auth = False
    auth_parent_id = None  # String ID
    auth_captured_map: Dict[str, bool] = {}  # Keyed by string transaction ID

    all_transactions_data = list(updated_order.get('transactions', []))
    for refund in updated_order.get('refunds', []):
        all_transactions_data.extend(refund.get('transactions', []))

    # Sort transactions by created_at, handling potential None or string values
    all_transactions_data.sort(key=lambda t: t.get('created_at', datetime.min.isoformat()))

    for trans in all_transactions_data:
        if trans.get('status') == 'success':
            try:
                amount = Decimal(trans.get('amount', '0'))
                kind = trans.get('kind')
                trans_id_str = trans.get('id')  # String ID
                parent_id_str = trans.get('parent_id')  # String ID or None

                if kind == 'sale':
                    total_paid += amount
                elif kind == 'capture':
                    total_paid += amount
                    if parent_id_str:
                        auth_captured_map[parent_id_str] = True
                elif kind == 'refund':
                    total_refunded += amount
                elif kind == 'authorization':
                    has_successful_auth = True
                    if trans_id_str:
                        auth_parent_id = trans_id_str
                        if auth_parent_id not in auth_captured_map:
                            auth_captured_map[auth_parent_id] = False  # Initialize as not captured
                elif kind == 'void':
                    if parent_id_str:
                        auth_captured_map[parent_id_str] = True  # Mark as effectively "handled" or "closed out"
                        if parent_id_str == auth_parent_id:
                            has_successful_auth = False  # Voided the primary auth
            except (InvalidOperation, TypeError, ValueError) as e:
                # Consider logging this error in a real system
                print_log(f"Error processing transaction {trans.get('id')}: {e}")  # Basic logging
                pass

    try:
        original_total_price = Decimal(updated_order.get('total_price', '0'))
    except (InvalidOperation, TypeError):
        original_total_price = Decimal("0.00")

    is_any_auth_pending = False
    if has_successful_auth and auth_parent_id:
        if not auth_captured_map.get(auth_parent_id, False):  # Check if this specific auth ID was captured or voided
            is_any_auth_pending = True

    new_status = updated_order.get('financial_status', 'pending')  # Default to current or pending

    if updated_order.get('cancelled_at') and total_paid == Decimal("0.00") and not is_any_auth_pending:
        new_status = "voided"
    elif total_refunded >= total_paid and total_paid > Decimal("0.00"):  # Must have paid something to be fully refunded
        new_status = "refunded"
    elif total_refunded > Decimal("0.00"):
        new_status = "partially_refunded"
    elif total_paid >= original_total_price and original_total_price > Decimal("0.00"):
        new_status = "paid"
    elif total_paid > Decimal("0.00"):
        new_status = "partially_paid"
    elif is_any_auth_pending:
        new_status = "authorized"
    elif total_paid == Decimal("0.00") and not is_any_auth_pending and not updated_order.get(
            'cancelled_at'):  # Only pending if not cancelled and no payment/auth
        new_status = "pending"

    # Final check for cancelled orders
    if updated_order.get('cancelled_at') and new_status not in ["refunded", "partially_refunded", "voided"]:
        if total_paid == Decimal("0.00") and not is_any_auth_pending:  # No payment, no pending auth
            new_status = "voided"
        # If cancelled with payment/auth, it might stay as paid/partially_paid/authorized until refunded

    updated_order['financial_status'] = new_status
    updated_order['updated_at'] = datetime.utcnow().isoformat()
    return updated_order

def update_order_fulfillment_status(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Updates the fulfillment_status of an order based on its line items.

    Args:
        order_data: Dictionary containing order information with line_items

    Returns:
        Updated order dictionary with new fulfillment_status
    """
    updated_order = order_data.copy()
    line_items = order_data.get('line_items', [])

    shippable_items = [item for item in line_items if item.get('requires_shipping', False)]

    if not shippable_items:
        updated_order['fulfillment_status'] = None
        updated_order['updated_at'] = datetime.utcnow().isoformat()
        return updated_order

    num_shippable = len(shippable_items)
    num_fulfilled = sum(1 for item in shippable_items if item.get('fulfillment_status') == 'fulfilled')
    # num_partially_fulfilled = sum(1 for item in shippable_items if item.get('fulfillment_status') == 'partial') # Not typically a line item status

    new_status = updated_order.get('fulfillment_status')

    # if order is cancelled, fulfillment status might be null or reflect restocked items
    if order_data.get('cancelled_at'):
        # Shopify might set fulfillment_status to null for cancelled orders
        # or it might reflect the state before cancellation if items were already shipped.
        # If items are restocked during cancellation, the line item fulfillment_status might change.
        # For simplicity, if cancelled, let's assume it remains as is or becomes null if nothing was ever fulfilled.
        if num_fulfilled == 0:
            updated_order['fulfillment_status'] = None
        # else: it might retain 'fulfilled' or 'partial' if items were shipped before cancellation.
        # This logic can be complex depending on exact Shopify behavior for cancelled+fulfilled orders.
    elif num_fulfilled == num_shippable and num_shippable > 0:  # All shippable items fulfilled
        new_status = "fulfilled"
    elif num_fulfilled > 0 and num_fulfilled < num_shippable:  # Some, but not all, shippable items fulfilled
        new_status = "partial"
    elif num_fulfilled == 0 and num_shippable > 0:  # No shippable items fulfilled yet
        new_status = "unfulfilled"  # or 'unshipped' based on your enum
    else:  # Should not happen if shippable_items > 0
        new_status = None

    updated_order['fulfillment_status'] = new_status
    updated_order['updated_at'] = datetime.utcnow().isoformat()
    return updated_order


def find_customer_by_email(customers_list: List[Dict[str, Any]], email: str) -> Optional[Dict[str, Any]]:
    """
    Finds a customer by their email address. Case-insensitive.

    Args:
        customers_list: List of customer dictionaries
        email: Email address to search for

    Returns:
        Customer dictionary or None if not found
    """
    if not email or not customers_list:
        return None

    email_lower = email.lower()
    for customer in customers_list:
        customer_email = customer.get('email')
        if customer_email and customer_email.lower() == email_lower:
            return customer
    return None


def find_product_by_handle(products_data: List[Dict[str, Any]], handle: str) -> Optional[Dict[str, Any]]:
    """
    Finds a product by its unique handle.

    Args:
        products_data: List of product dictionaries
        handle: Handle to search for

    Returns:
        Product dictionary or None if not found
    """
    if not handle or not products_data:
        return None

    for product in products_data:
        if product.get('handle') == handle:
            return product
    return None

def _shopify_get_order_by_id_serialize_value(value: Any) -> Any:
    """
    Serializes datetime.datetime or datetime.date objects to ISO 8601 strings.
    Other values are returned as is.
    """
    # Check specifically for datetime.datetime and datetime.date instances
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value
  
def _get_sum_related_transactions(
        order_transactions: List[Dict[str, Any]],
        parent_transaction_id: str,
        kinds: List[str],
        exclude_transaction_id: Optional[str] = None
) -> Decimal:
    """
    Calculates the sum of amounts for transactions related to a parent transaction.
    Optionally excludes a specific transaction ID from the sum.
    """
    total = Decimal("0.00")
    for t in order_transactions:
        if t.get('id') == exclude_transaction_id:
            continue
        if t.get('parent_id') == parent_transaction_id and\
                t.get('kind') in kinds and\
                t.get('status') == 'success':
            try:
                total += Decimal(t.get('amount', "0"))
            except InvalidOperation:
                pass  # Ignore invalid amounts
    return total


# Helper function to find a transaction by ID
def _find_transaction_by_id(
        order_transactions: List[Dict[str, Any]],
        transaction_id: str
) -> Optional[Dict[str, Any]]:
    """Finds a transaction by its ID within a list of transactions."""
    for t in order_transactions:
        if t.get('id') == transaction_id:
            return t
    return None

# --- Search Query Parsing and Evaluation Helpers ---

def _get_nested_value(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    keys = path.split('.')
    current_level = data
    for key in keys:
        if isinstance(current_level, dict):
            current_level = current_level.get(key)
        elif isinstance(current_level, list) and key.isdigit():
            try: current_level = current_level[int(key)]
            except (IndexError, ValueError): return default
        else: return default
        if current_level is None: return default
    return current_level

def _parse_datetime_value(value_str: str) -> Optional[datetime]:
    """
    Parses a datetime value using centralized validation.
    
    Returns a timezone-aware datetime object (UTC) or None if parsing fails.
    """
    try:
        s_val = str(value_str)
        
        # Use centralized datetime validation
        from common_utils.datetime_utils import validate_shopify_datetime, InvalidDateTimeFormatError
        
        try:
            # Validate and normalize the datetime string
            normalized_datetime_str = validate_shopify_datetime(s_val)
            
            # Parse the normalized string to datetime object
            dt_obj = datetime.fromisoformat(normalized_datetime_str.replace("Z", "+00:00"))
            return dt_obj.replace(tzinfo=timezone.utc) if dt_obj.tzinfo is None else dt_obj
            
        except InvalidDateTimeFormatError:
            # Fallback to date-only parsing for backward compatibility
            try: 
                dt_obj = datetime.strptime(s_val, '%Y-%m-%d')
                return dt_obj.replace(tzinfo=timezone.utc)
            except ValueError: 
                return None
        except Exception as e:
            # Fallback to date-only parsing for backward compatibility
            try: 
                dt_obj = datetime.strptime(s_val, '%Y-%m-%d')
                return dt_obj.replace(tzinfo=timezone.utc)
            except ValueError: 
                return None
                
    except TypeError: 
        return None

def _parse_decimal_value(value_str: str) -> Optional[Decimal]:
    try: return Decimal(str(value_str))
    except (InvalidOperation, TypeError): return None

def _parse_shopify_query_term(term_str_input: str) -> Optional[Dict[str, Any]]:
    original_term_for_error = term_str_input
    term_str = term_str_input.strip()
    negated = False

    if term_str.startswith('-'):
        negated = True; term_str = term_str[1:].lstrip()
    elif term_str.lower().startswith('not '):
        if len(term_str) > 4 and term_str[3].isspace() and term_str[4:].strip():
            negated = True; term_str = term_str[4:].lstrip()
    
    if term_str.upper() in ["AND", "OR", "NOT"] and not negated : # Standalone "NOT" is invalid
        # If it was "NOT something_else", negated is True, term_str is "something_else"
        # If term_str itself becomes "NOT" after stripping negation, it's invalid.
        return None

    _FIELD_PART_REGEX = re.compile(
        r"^(?P<field>[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s*:\s*(?P<op_val_part>.*)$"
    )
    _OPERATOR_PREFIX_REGEX = re.compile(r"^(>=|<=|!=|>|<)(.*)$")

    field = "_all_"; comparator = ':'; value_str_from_parser = term_str
    is_default_search = True; is_prefix = False; is_exists = False
    
    raw_op_val_part_from_regex_group = None 

    field_match = _FIELD_PART_REGEX.match(term_str)
    if field_match:
        data = field_match.groupdict()
        potential_field = data['field']
        raw_op_val_part_from_regex_group = data['op_val_part'] 
        op_val_part_stripped = raw_op_val_part_from_regex_group.strip()

        parsed_op = ':'; value_after_op = op_val_part_stripped

        if op_val_part_stripped: 
            op_match_re = _OPERATOR_PREFIX_REGEX.match(op_val_part_stripped) 
            if op_match_re:
                extracted_op = op_match_re.group(1) 
                value_after_extracted_op = op_match_re.group(2).strip()
                if value_after_extracted_op.startswith(('>', '<', '=', '!')) and extracted_op: # Malformed operator sequence
                     raise custom_errors.InvalidInputError(f"Malformed operator sequence in query token: {original_term_for_error}")
                parsed_op = extracted_op 
                value_after_op = value_after_extracted_op
        
        # --- Condition for returning None (invalid term for filtering) ---
        # A field-specific term is invalid if the part after "field:[op]" is empty,
        # unless the original part after "field:" was "*" (exists query) or an explicitly quoted empty string.
        is_asterisk_val_original = (op_val_part_stripped == "*")
        # Check if the op_val_part_stripped was '""' or "''"
        was_explicitly_quoted_empty_original = (op_val_part_stripped == '""' or op_val_part_stripped == "''")
        
        # value_after_op is the final value string (e.g., for "field:opVAL", value_after_op is "VAL")
        # If value_after_op is now empty:
        if value_after_op == "":
            if not is_asterisk_val_original and not was_explicitly_quoted_empty_original:
                # This means original op_val_part was empty (e.g. "field:"), or just an operator (e.g. "field:>")
                return None 
        # If op_val_part_stripped was empty but it wasn't "*", it's invalid (e.g. "field:")
        elif not op_val_part_stripped and not is_asterisk_val_original:
            return None


        field = potential_field
        comparator = parsed_op 
        value_str_from_parser = value_after_op 
        is_default_search = False
    
    if field.lower() == 'tag': field = 'tags'

    value = value_str_from_parser 
    if (value.startswith('"') and value.endswith('"')) or\
       (value.startswith("'") and value.endswith("'")):
        value = value[1:-1] 
    
    if not is_default_search and value == '*' and comparator == ':': 
        is_exists = True
    elif isinstance(value, str) and value.endswith('*') and not value.endswith('\\*') and not is_exists: 
        is_prefix = True
        if not is_default_search: value = value[:-1] 
    
    if is_default_search and is_prefix: comparator = ':*' 
    
    # This final check is likely redundant given the more specific checks above,
    # but retained as a safeguard for now.
    if field_match and not is_default_search and not is_exists and value == "":
        # If value became empty, ensure it was from an original explicitly quoted empty string
        original_op_val_part_check = raw_op_val_part_from_regex_group.strip() if raw_op_val_part_from_regex_group else ""
        if not (original_op_val_part_check == '""' or original_op_val_part_check == "''"):
             # Check if the operator itself implies a value.
             # E.g., for field:opVALUE, if VALUE is empty, then it's tricky.
             # The earlier checks `if value_after_op == ""` should handle this.
             # This path might only be hit if `value_str_from_parser` was `""` or `''` and unquoted to `""`.
             pass # This means value is legitimately an empty string.

    return {'field': field, 'comparator': comparator, 'value': value, 'negated': negated,
            'is_default_search': is_default_search, 'is_prefix': is_prefix and not is_default_search,
            'is_exists': is_exists, 'original_term_for_error': original_term_for_error}

def _tokenize_query(query_string: str) -> List[str]:
    placeholders: Dict[str, str] = {}; idx = 0
    def quote_replacer(match): nonlocal idx; ph = f"__Q_{idx}__"; placeholders[ph]=match.group(0); idx+=1; return ph
    temp_query_no_quotes = re.sub(r'"[^"]*"|\'[^\']*\'', quote_replacer, query_string)
    padded_query = temp_query_no_quotes
    for op in ['AND', 'OR', 'NOT']:
        padded_query = re.sub(r'(\s+|^)(\b' + op + r'\b)(\s+|$)', r' \2 ', padded_query, flags=re.IGNORECASE)
    padded_query = ' '.join(padded_query.split())
    for ph, original_quote in placeholders.items(): padded_query = padded_query.replace(ph, original_quote)
    import shlex
    try: 
        lexer = shlex.shlex(padded_query, posix=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError: tokens = query_string.split() 
    return [token for token in tokens if token.strip()]

def _parse_shopify_query_string(query_string: str) -> List[List[Dict[str, Any]]]:
    if not query_string or not query_string.strip(): return []
    tokens = _tokenize_query(query_string)
    if not tokens: return []
    
    dnf_groups: List[List[Dict[str, Any]]] = []
    current_and_clause_tokens: List[str] = []

    for token in tokens:
        if token.upper() == 'OR':
            if current_and_clause_tokens:
                conditions_in_and_group = []
                term_buffer = []
                for and_token_idx, and_token_val in enumerate(current_and_clause_tokens):
                    if and_token_val.upper() == 'AND':
                        if term_buffer:
                            term_to_parse = " ".join(term_buffer)
                            if term_to_parse.strip(): # Avoid parsing empty string as term
                                parsed = _parse_shopify_query_term(term_to_parse)
                                if parsed: conditions_in_and_group.append(parsed)
                        term_buffer = []
                    else: term_buffer.append(and_token_val)
                if term_buffer:
                    term_to_parse = " ".join(term_buffer)
                    if term_to_parse.strip():
                        parsed = _parse_shopify_query_term(term_to_parse)
                        if parsed: conditions_in_and_group.append(parsed)

                if conditions_in_and_group:
                    expanded_group = []
                    for cond in conditions_in_and_group:
                        if cond['is_default_search'] and isinstance(cond['value'], str) and ' ' in cond['value'] and not (cond['value'].startswith('"') and cond['value'].endswith("'")):
                            sub_terms = cond['value'].split()
                            for k, sub_term_val in enumerate(sub_terms):
                                is_sub_prefix = sub_term_val.endswith('*') and not sub_term_val.endswith('\\*'); sub_val_clean = sub_term_val[:-1] if is_sub_prefix else sub_term_val
                                expanded_group.append({'field': "_all_", 'comparator': ':*' if is_sub_prefix else ':', 'value': sub_term_val if is_sub_prefix else sub_val_clean, 'negated': cond['negated'] if k == 0 else False, 'is_default_search': True, 'is_prefix': False, 'is_exists': False, 'original_term_for_error': cond.get('original_term_for_error', sub_term_val)})
                        else: expanded_group.append(cond)
                    if expanded_group: dnf_groups.append(expanded_group)
                current_and_clause_tokens = [] 
        else:
            current_and_clause_tokens.append(token)
            
    if current_and_clause_tokens:
        conditions_in_and_group = []
        term_buffer = []
        for and_token_idx, and_token_val in enumerate(current_and_clause_tokens):
            if and_token_val.upper() == 'AND':
                if term_buffer:
                    term_to_parse = " ".join(term_buffer)
                    if term_to_parse.strip():
                        parsed = _parse_shopify_query_term(term_to_parse)
                        if parsed: conditions_in_and_group.append(parsed)
                term_buffer = []
            else: term_buffer.append(and_token_val)
        if term_buffer:
            term_to_parse = " ".join(term_buffer)
            if term_to_parse.strip():
                parsed = _parse_shopify_query_term(term_to_parse)
                if parsed: conditions_in_and_group.append(parsed)
        
        if conditions_in_and_group:
            expanded_group = []
            for cond in conditions_in_and_group:
                if cond['is_default_search'] and isinstance(cond['value'], str) and ' ' in cond['value'] and not (cond['value'].startswith('"') and cond['value'].endswith("'")):
                    sub_terms = cond['value'].split()
                    for k, sub_term_val in enumerate(sub_terms):
                        is_sub_prefix = sub_term_val.endswith('*') and not sub_term_val.endswith('\\*'); sub_val_clean = sub_term_val[:-1] if is_sub_prefix else sub_term_val
                        expanded_group.append({'field': "_all_", 'comparator': ':*' if is_sub_prefix else ':', 'value': sub_term_val if is_sub_prefix else sub_val_clean, 'negated': cond['negated'] if k == 0 else False, 'is_default_search': True, 'is_prefix': False, 'is_exists': False, 'original_term_for_error': cond.get('original_term_for_error', sub_term_val)})
                else: expanded_group.append(cond)
            if expanded_group: dnf_groups.append(expanded_group)
            
    return [group for group in dnf_groups if group]


def _evaluate_single_condition(customer: Dict[str, Any], condition: Dict[str, Any]) -> bool:
    field_name = condition['field']; comparator = condition['comparator'] 
    query_value_parsed = condition['value']; negated = condition['negated']
    is_default_search = condition['is_default_search']
    is_prefix_field_val = condition['is_prefix']; is_exists_query = condition['is_exists']
    match_found = False

    if is_default_search:
        search_term_original = str(query_value_parsed); search_term_lower = search_term_original.lower()
        default_fields_to_check = ['first_name', 'last_name', 'email', 'tags', 'phone']
        for default_field in default_fields_to_check:
            customer_val_raw = _get_nested_value(customer, default_field)
            if customer_val_raw is not None:
                customer_val_str = str(customer_val_raw).lower()
                if comparator == ':*': 
                    prefix_to_search = search_term_lower[:-1]
                    if any(word.startswith(prefix_to_search) for word in re.split(r'\W+', customer_val_str) if word):
                        match_found = True; break
                elif search_term_lower in customer_val_str: match_found = True; break
    else: 
        customer_val_raw = _get_nested_value(customer, field_name)
        if is_exists_query: match_found = customer_val_raw is not None and str(customer_val_raw).strip() != ""
        elif customer_val_raw is None: # Actual customer value is None
            is_q_null_empty = (comparator==':' and (str(query_value_parsed)=="" or str(query_value_parsed).lower()=="null" or str(query_value_parsed).lower()=="none"))
            is_q_not_null_empty = (comparator=='!=' and (str(query_value_parsed)=="" or str(query_value_parsed).lower()=="null" or str(query_value_parsed).lower()=="none"))
            if is_q_null_empty: match_found = True 
            elif is_q_not_null_empty: match_found = False 
            else: match_found = False
        
        elif field_name in ['created_at', 'updated_at']:
            cust_dt = _parse_datetime_value(str(customer_val_raw)); cond_dt = _parse_datetime_value(str(query_value_parsed))
            if cust_dt and cond_dt:
                op_map = {':': lambda a,b: (a.date()==b.date() if len(str(query_value_parsed))==10 else a==b), 
                          '!=': lambda a,b: (a.date()!=b.date() if len(str(query_value_parsed))==10 else a!=b), 
                          '>': lambda a,b: a>b, '<': lambda a,b: a<b, 
                          '>=': lambda a,b: a>=b, '<=': lambda a,b: a<=b}
                if comparator in op_map: match_found = op_map[comparator](cust_dt, cond_dt)
            else: match_found = False
        elif field_name == 'orders_count':
            try:
                if customer_val_raw is None: raise ValueError("orders_count is None")
                cust_val_int = int(customer_val_raw) 
                cond_val_int = int(str(query_value_parsed))
                op_map = {':': lambda a,b: a==b, '!=': lambda a,b: a!=b, 
                          '>': lambda a,b: a>b, '<': lambda a,b: a<b, 
                          '>=': lambda a,b: a>=b, '<=': lambda a,b: a<=b}
                if comparator in op_map: match_found = op_map[comparator](cust_val_int, cond_val_int)
            except (ValueError, TypeError): match_found = False
        elif field_name == 'total_spent':
            cust_val_dec = _parse_decimal_value(str(customer_val_raw)) if customer_val_raw is not None else None
            cond_val_dec = _parse_decimal_value(str(query_value_parsed))
            if cust_val_dec is not None and cond_val_dec is not None:
                op_map = {':': lambda a,b: a==b, '!=': lambda a,b: a!=b, 
                          '>': lambda a,b: a>b, '<': lambda a,b: a<b, 
                          '>=': lambda a,b: a>=b, '<=': lambda a,b: a<=b}
                if comparator in op_map: match_found = op_map[comparator](cust_val_dec, cond_val_dec)
            else: match_found = False
        elif field_name == 'tags': 
            raw_tag_string = str(customer_val_raw) if customer_val_raw is not None else ""
            tags_list = [t.strip().lower() for t in raw_tag_string.split(',') if t.strip()]
            search_tag = str(query_value_parsed).lower() 
            if is_prefix_field_val: match_found = any(t.startswith(search_tag) for t in tags_list)
            elif comparator == ':': match_found = search_tag in tags_list 
            elif comparator == '!=': match_found = search_tag not in tags_list
        else: 
            cust_str = str(customer_val_raw).lower() if customer_val_raw is not None else ""
            search_str = str(query_value_parsed).lower()
            if is_prefix_field_val: match_found = cust_str.startswith(search_str)
            elif comparator == ':': match_found = cust_str == search_str
            elif comparator == '!=': match_found = cust_str != search_str
            elif comparator in ['>', '<', '>=', '<='] : 
                 op_map_str = { '>': lambda a,b: a>b, '<': lambda a,b: a<b, 
                                '>=': lambda a,b: a>=b, '<=': lambda a,b: a<=b}
                 if comparator in op_map_str: match_found = op_map_str[comparator](cust_str, search_str)
    return not match_found if negated else match_found

def _filter_customers(all_customers: List[Dict[str, Any]], parsed_dnf_query: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    if not parsed_dnf_query: return all_customers 
    filtered_list: List[Dict[str, Any]] = []
    for customer in all_customers:
        for and_conditions_group in parsed_dnf_query:
            if not and_conditions_group: continue
            all_conditions_true = True
            for condition in and_conditions_group:
                if not _evaluate_single_condition(customer, condition):
                    all_conditions_true = False; break
            if all_conditions_true:
                filtered_list.append(customer); break 
    return filtered_list

_VALID_SORTABLE_FIELDS = ['id', 'email', 'first_name', 'last_name', 'orders_count', 'state', 'total_spent', 'created_at', 'updated_at']
def _sort_customers(customers: List[Dict[str, Any]], order_str: Optional[str]) -> List[Dict[str, Any]]:
    if not order_str or not customers: return customers
    parts = order_str.strip().split(); sort_field = parts[0]; descending = parts[1].upper() == 'DESC'
    def get_sort_key(c: Dict[str, Any]):
        v = _get_nested_value(c, sort_field); is_asc = not descending
        if v is None:
            if sort_field in ['created_at', 'updated_at']: return datetime.min.replace(tzinfo=timezone.utc) if is_asc else datetime.max.replace(tzinfo=timezone.utc)
            if sort_field == 'orders_count': return float('-inf') if is_asc else float('inf')
            if sort_field == 'total_spent': return Decimal('-Infinity') if is_asc else Decimal('Infinity')
            return ""
        if sort_field in ['created_at', 'updated_at']: return _parse_datetime_value(str(v)) or (datetime.min.replace(tzinfo=timezone.utc) if is_asc else datetime.max.replace(tzinfo=timezone.utc))
        if sort_field == 'total_spent': return _parse_decimal_value(str(v)) or (Decimal('-Infinity') if is_asc else Decimal('Infinity'))
        if sort_field == 'orders_count':
            try: return int(v)
            except (ValueError, TypeError): return float('-inf') if is_asc else float('inf')
        return str(v).lower()
    try: return sorted(list(customers), key=get_sort_key, reverse=descending)
    except TypeError as e: raise ValueError(f"Sorting error for '{sort_field}': {e}")

def _encode_page_token(offset: int) -> str: return base64.urlsafe_b64encode(json.dumps({"offset": offset}).encode()).decode()
def _decode_page_token(token: str) -> Optional[int]:
    try:
        if not isinstance(token, str): return None
        token += '=' * (4 - len(token) % 4 if len(token) % 4 != 0 else 0)
        decoded_json = base64.urlsafe_b64decode(token.encode()).decode()
        data = json.loads(decoded_json); offset = data.get("offset")
        return int(offset) if isinstance(offset, (int, float)) else None
    except Exception: return None

def _project_customer_fields(customer_data: Dict[str, Any], requested_fields: Optional[List[str]]) -> Dict[str, Any]:
    if customer_data is None: return {}
    fields_to_project = ShopifyCustomerModel.model_fields.keys() if requested_fields is None else requested_fields
    if not fields_to_project and 'id' in customer_data : return {'id': customer_data['id']} 
    if not fields_to_project and not ('id' in customer_data and not requested_fields) : return {} 
    projected_customer: Dict[str, Any] = {}
    for field_path in fields_to_project:
        keys = field_path.split('.'); current_dest_dict = projected_customer
        value_to_set = _get_nested_value(customer_data, field_path)
        for i, key in enumerate(keys):
            if i == len(keys) - 1: current_dest_dict[key] = value_to_set
            else:
                if key not in current_dest_dict or not isinstance(current_dest_dict[key], dict): current_dest_dict[key] = {}
                current_dest_dict = current_dest_dict[key]
    return projected_customer

def _parse_datetime_param(
    date_str: Optional[str], param_name: str
) -> Optional[datetime]:
    """
    Parses an optional ISO 8601 date string parameter using centralized validation.

    Returns a timezone-aware datetime object (UTC) or None if input is None.
    Raises InvalidDateTimeFormatError if parsing fails for a non-None input.
    """
    if date_str is None:
        return None
    
    if not isinstance(date_str, str):
        raise custom_errors.InvalidParameterError(
            f"Invalid type for {param_name}: '{type(date_str).__name__}'. "
            f"Expected a string in ISO 8601 format or None."
        )
    
    try:
        # Use centralized datetime validation
        from common_utils.datetime_utils import validate_shopify_datetime, InvalidDateTimeFormatError
        
        # Validate and normalize the datetime string
        normalized_datetime_str = validate_shopify_datetime(date_str)
        
        # Parse the normalized string to datetime object
        dt = datetime.fromisoformat(normalized_datetime_str.replace("Z", "+00:00"))
        
        # Normalize to UTC:
        # If naive, assume UTC.
        # If aware, convert to UTC for consistent comparisons.
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:  # Check if naive
            return dt.replace(tzinfo=timezone.utc)
        else:  # Aware
            return dt.astimezone(timezone.utc)
            
    except InvalidDateTimeFormatError as e:
        # Convert to Shopify's local InvalidDateTimeFormatError
        raise custom_errors.InvalidDateTimeFormatError(
            f"Invalid date format for {param_name}: '{date_str}'. "
            f"Expected ISO 8601 format (e.g., YYYY-MM-DDTHH:MM:SSZ)."
        )

def _parse_datetime_from_record(
    date_str: Any, field_name_in_record: str, order_identifier: str
) -> datetime:
    """
    Parses an ISO 8601 date string from a DB record field using centralized validation.

    Returns a timezone-aware datetime object (UTC).
    Raises ShopifyApiError if parsing fails (indicates data corruption in DB).
    """
    if not isinstance(date_str, str):
        raise custom_errors.ShopifyApiError(
            f"Malformed date field '{field_name_in_record}' in order '{order_identifier}': "
            f"expected string, got {type(date_str).__name__}."
        )
    
    try:
        # Use centralized datetime validation
        from common_utils.datetime_utils import validate_shopify_datetime, InvalidDateTimeFormatError
        
        # Validate and normalize the datetime string
        normalized_datetime_str = validate_shopify_datetime(date_str)
        
        # Parse the normalized string to datetime object
        dt = datetime.fromisoformat(normalized_datetime_str.replace("Z", "+00:00"))
        
        # Normalize to UTC:
        # If naive, assume UTC.
        # If aware, convert to UTC for consistent comparisons.
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None: # Naive
            return dt.replace(tzinfo=timezone.utc)
        else: # Aware
            return dt.astimezone(timezone.utc)
            
    except InvalidDateTimeFormatError as e:
        # For DB record parsing, malformed dates indicate data corruption, so raise ShopifyApiError
        raise custom_errors.ShopifyApiError(
            f"Malformed date value '{date_str}' for field '{field_name_in_record}' "
            f"in order '{order_identifier}': not a valid ISO 8601 format."
        )

def _format_datetime_to_iso(dt_value: Optional[datetime]) -> Optional[str]:
    """Converts a datetime object to an ISO 8601 string. Returns None if input is None."""
    if dt_value is None:
        return None
    if isinstance(dt_value, str):  # Handle cases where it might already be a string
        return dt_value
    if isinstance(dt_value, datetime):
        return dt_value.isoformat()
    # Fallback or error for unexpected types if necessary
    return str(dt_value)

def _format_image_response(image_db_data: Dict[str, Any], parent_product_id_int: int) -> Optional[Dict[str, Any]]:
    """Converts a DB image dictionary to the response image dictionary format."""
    if not image_db_data:
        return None

    variant_ids_response = []
    for vid in image_db_data.get('variant_ids', []):
        if vid is not None:  # Should always be true if source is List[str]
            try:
                variant_ids_response.append(int(vid))
            except (ValueError, TypeError):
                # Handle or log error if a variant_id is not convertible to int
                # For now, skip non-convertible IDs
                pass

    return {
        "id": int(image_db_data['id']),
        "product_id": parent_product_id_int,
        "position": image_db_data['position'],
        "created_at": _format_datetime_to_iso(image_db_data.get('created_at')),
        "updated_at": _format_datetime_to_iso(image_db_data.get('updated_at')),
        "alt": image_db_data.get('alt'),
        "width": image_db_data['width'],
        "height": image_db_data['height'],
        "variant_ids": variant_ids_response,
    }

def _format_variant_response(variant_db_data: Dict[str, Any], parent_product_id_int: int) -> Dict[str, Any]:
    """Converts a DB variant dictionary to the response variant dictionary format."""

    inventory_item_id_val = variant_db_data.get('inventory_item_id')
    if inventory_item_id_val is None:
        pass  # Let int(inventory_item_id_val) handle it.
    old_inventory_quantity_val = variant_db_data.get('old_inventory_quantity')
    return {
        "id": int(variant_db_data['id']),
        "product_id": parent_product_id_int,
        "title": variant_db_data['title'],
        "price": variant_db_data['price'],
        "sku": variant_db_data.get('sku'),
        "position": variant_db_data['position'],
        "inventory_policy": variant_db_data.get('inventory_policy'),  # DB: Optional[str], Resp: str
        "compare_at_price": variant_db_data.get('compare_at_price'),
        "fulfillment_service": variant_db_data.get('fulfillment_service'),  # DB: Optional[str], Resp: str
        "inventory_management": variant_db_data.get('inventory_management'),
        "option1": variant_db_data.get('option1'),
        "option2": variant_db_data.get('option2'),
        "option3": variant_db_data.get('option3'),
        "created_at": _format_datetime_to_iso(variant_db_data.get('created_at')),
        "updated_at": _format_datetime_to_iso(variant_db_data.get('updated_at')),
        "taxable": variant_db_data['taxable'],  # DB: bool, Resp: bool
        "barcode": variant_db_data.get('barcode'),
        "grams": variant_db_data['grams'],  # DB: int, Resp: int
        "weight": variant_db_data['weight'],  # DB: float, Resp: float
        "weight_unit": variant_db_data['weight_unit'],  # DB: str, Resp: str
        "inventory_item_id": int(inventory_item_id_val) if inventory_item_id_val is not None else None,
        # Allows None if DB has None, may conflict if spec is strictly non-nullable int
        "inventory_quantity": variant_db_data['inventory_quantity'],  # DB: int, Resp: int
        "old_inventory_quantity": old_inventory_quantity_val,  # DB: Optional[int], Resp: int. If None, output has None.
        "requires_shipping": variant_db_data['requires_shipping'],  # DB: bool, Resp: bool
    }

def _format_option_response(option_db_data: Dict[str, Any], parent_product_id_int: int) -> Dict[str, Any]:
    """Converts a DB option dictionary to the response option dictionary format."""
    return {
        "id": int(option_db_data['id']),
        "product_id": parent_product_id_int,
        "name": option_db_data['name'],
        "position": option_db_data['position'],
        "values": option_db_data.get('values', []),
    }

def _ensure_iso_string_for_response(dt_val: Any) -> Optional[str]:
    """
    Converts a datetime object to an ISO string for response.
    If the value is already a string (assumed ISO format) or None, it's returned as is.
    """
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            return dt_val.replace(tzinfo=timezone.utc).isoformat()
        return dt_val.isoformat()
    return dt_val



def _check_product_in_collection(product_dict: Dict[str, Any], collection_dict: Dict[str, Any]) -> bool:
    """Check if a product belongs to a specific collection.
    
    Supports both manual collections (explicit product lists) and smart collections
    (rule-based automatic inclusion).
    
    Args:
        product_dict: The product dictionary to check
        collection_dict: The collection dictionary with rules/products
        
    Returns:
        bool: True if product belongs to collection, False otherwise
    """
    if not product_dict or not collection_dict:
        return False
    
    product_id = product_dict.get('id')
    if not product_id:
        return False
        
    collection_type = collection_dict.get('collection_type', 'manual')
    
    if collection_type == 'manual':
        # Manual collection: check if product ID is in the products list
        products_list = collection_dict.get('products', [])
        return product_id in products_list
    
    elif collection_type == 'smart':
        # Smart collection: evaluate rules against product
        rules = collection_dict.get('rules', [])
        if not rules:
            return False
            
        # All rules must be satisfied (AND logic)
        for rule in rules:
            if not _evaluate_collection_rule(product_dict, rule):
                return False
        return True
    
    return False


def _evaluate_collection_rule(product_dict: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """Evaluate a single smart collection rule against a product.
    
    Args:
        product_dict: The product dictionary
        rule: Rule dictionary with 'column', 'relation', and 'condition'
        
    Returns:
        bool: True if rule matches, False otherwise
    """
    column = rule.get('column')  # e.g., 'product_type', 'title', 'tag', 'vendor'
    relation = rule.get('relation')  # e.g., 'equals', 'contains', 'starts_with', 'ends_with'
    condition = rule.get('condition', '').lower()  # The value to match against
    
    if not column or not relation:
        return False
        
    # Get the product field value
    product_value = product_dict.get(column, '')
    if product_value is None:
        product_value = ''
    product_value = str(product_value).lower()
    
    # Apply the relation logic
    if relation == 'equals':
        return product_value == condition
    elif relation == 'not_equals':
        return product_value != condition
    elif relation == 'contains':
        return condition in product_value
    elif relation == 'not_contains':
        return condition not in product_value
    elif relation == 'starts_with':
        return product_value.startswith(condition)
    elif relation == 'ends_with':
        return product_value.endswith(condition)
    elif relation == 'greater_than':
        try:
            return float(product_value) > float(condition)
        except (ValueError, TypeError):
            return False
    elif relation == 'less_than':
        try:
            return float(product_value) < float(condition)
        except (ValueError, TypeError):
            return False
    
    return False


def _apply_presentment_currencies(product_dict: Dict[str, Any], currencies: List[str]) -> None:
    """Apply presentment currency formatting to product variants.
    
    This function modifies the product dictionary in-place to add presentment_prices
    to each variant based on the requested currencies. In a real implementation,
    this would use actual exchange rates and store-specific pricing rules.
    
    Args:
        product_dict: The product dictionary to modify
        currencies: List of ISO 4217 currency codes to generate prices for
    """
    if not isinstance(product_dict.get('variants'), list):
        return
    
    # Simple exchange rates for simulation (in real implementation, these would come from a currency service)
    exchange_rates = {
        'USD': 1.0,      # Base currency
        'EUR': 0.85,     # Euro
        'GBP': 0.73,     # British Pound
        'CAD': 1.25,     # Canadian Dollar
        'AUD': 1.35,     # Australian Dollar
        'JPY': 110.0,    # Japanese Yen
    }
    
    for variant in product_dict['variants']:
        if not isinstance(variant, dict) or 'price' not in variant:
            continue
            
        try:
            base_price = float(variant['price'])
            presentment_prices = []
            
            for currency in currencies:
                if currency in exchange_rates:
                    converted_price = base_price * exchange_rates[currency]
                    # Format price appropriately for currency (JPY has no decimals, others have 2)
                    if currency == 'JPY':
                        price_str = f"{converted_price:.0f}"
                    else:
                        price_str = f"{converted_price:.2f}"
                    
                    presentment_prices.append({
                        "price": {
                            "amount": price_str,
                            "currency_code": currency
                        }
                    })
            
            if presentment_prices:
                variant['presentment_prices'] = presentment_prices
                
        except (ValueError, TypeError):
            # Skip variants with invalid price data
            continue


def generate_next_resource_id(collection: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
    """
    Generates the next numeric string ID for a given collection.
    It finds the maximum integer value and returns the next integer as a string.
    - If the collection is a dictionary, it inspects the keys.
    - If the collection is a list of dictionaries, it inspects the 'id' field of each item.
    If the collection is empty or no valid numeric keys/IDs are found, it starts from "1".
    """
    if not collection:
        return "1"

    max_id = 0
    
    items_to_check = []
    if isinstance(collection, dict):
        items_to_check = collection.keys()
    elif isinstance(collection, list):
        items_to_check = [str(item.get('id', '0')) for item in collection]

    for id_str in items_to_check:
        try:
            current_id = int(id_str)
            if current_id > max_id:
                max_id = current_id
        except (ValueError, TypeError):
            continue
            
    return str(max_id + 1)

def _find_product_and_variant_in_db_dicts(
    variant_id_str: str, products_db_dict: Dict[str, Dict[str, Any]]
) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
    if not variant_id_str:
        return None
    for product_id, product_data in products_db_dict.items():
        for variant_data in product_data.get('variants', []):
            if str(variant_data.get('id')) == variant_id_str:
                return product_data, variant_data
    return None


def slugify(text: str) -> str:
    text = text.lower()
    return re.sub(r'[\\s_]+', '-', text)

def create_product(product_data: Dict[str, Any], custom_id: Optional[str] = None) -> Dict[str, Any]:
    """Creates a new product with auto-generated or custom ID, handle, and timestamps.

    Enables agents to create complete product records with variants, options, and images. Automatically generates
    URL-friendly handles from titles and creates default variants when none provided.

    Args:
        product_data (Dict[str, Any]): Product creation data with keys:
            title (str, required): Product name for display and handle generation.
                Example: "Awesome T-Shirt"
            vendor (str, required): Product vendor or brand name.
                Example: "Cool Brand Co"
            product_type (str, required): Product category classification.
                Example: "T-Shirts"
            body_html (str, optional): HTML product description. Defaults to empty string.
            status (str, optional): Product status ("active", "archived", "draft"). Defaults to "active".
            tags (str, optional): Comma-separated tags string. Defaults to empty string.
            variants (List[Dict], optional): Variant objects to create. Auto-creates default if omitted.
                Each variant dict with keys: title, price, sku, inventory_quantity, etc.
            options (List[Dict], optional): Option objects defining product variants.
                Each option dict with keys: name, values (List[str])
            images (List[Dict], optional): Image objects for product gallery.
                Each image dict with keys: src, width, height, alt, position
        custom_id (Optional[str]): Optional custom ID to use for the product.
            If provided, must be a non-empty string and not already exist in the products database.
            If not provided, an ID will be auto-generated.

    Returns:
        Dict[str, Any]: Complete created product object with keys:
            id (str): Custom ID if provided, otherwise auto-generated unique product identifier
            title (str): Product display name
            handle (str): Auto-generated URL-friendly slug from title
            vendor (str): Product vendor name
            product_type (str): Product category
            body_html (str): HTML description content
            status (str): Current product status
            tags (str): Comma-separated tags string
            created_at (str): ISO 8601 creation timestamp
            updated_at (str): ISO 8601 last modified timestamp
            published_at (str|None): ISO 8601 publish timestamp if status is "active", None otherwise
            admin_graphql_api_id (str): GraphQL API identifier
            variants (List[Dict]): Array of variant objects, each dict with keys:
                id (str): Auto-generated variant identifier
                product_id (str): Parent product ID
                title (str): Variant display name
                price (str): Price as decimal string
                sku (str|None): Stock keeping unit
                inventory_quantity (int): Available stock count
                position (int): Display order position
                created_at (str): ISO 8601 creation timestamp
                updated_at (str): ISO 8601 last modified timestamp
                inventory_item_id (str): Auto-generated inventory item ID
                admin_graphql_api_id (str): GraphQL API identifier
            options (List[Dict]): Array of option objects, each dict with keys:
                id (str): Auto-generated option identifier
                product_id (str): Parent product ID
                name (str): Option name (e.g., "Size", "Color")
                values (List[str]): Available option values
                position (int): Display order position
            images (List[Dict]): Array of image objects, each dict with keys:
                id (str): Auto-generated image identifier
                product_id (str): Parent product ID
                position (int): Display order in gallery
                created_at (str): ISO 8601 creation timestamp
                updated_at (str): ISO 8601 last modified timestamp
                alt (str|None): Alternative text description
                width (int): Image width in pixels
                height (int): Image height in pixels
                variant_ids (List[str]): Associated variant IDs
            image (Dict|None): Primary image object (first in images list) or None if no images

    Raises:
        ValidationError: If required fields are missing, product_data format is invalid, or if custom_id is invalid.
        InvalidInputError: If custom_id is already in use.
    """
    # Input validation
    if not isinstance(product_data, dict):
        raise custom_errors.ValidationError("Product data must be a dictionary.")
    
    # Validate custom_id if provided
    if custom_id is not None:
        if not isinstance(custom_id, str) or not custom_id.strip():
            raise custom_errors.ValidationError("custom_id must be a non-empty string.")
        if custom_id in DB.get('products', {}):
            raise custom_errors.InvalidInputError(f"Product with ID '{custom_id}' already exists.")
    
    # Validate required fields
    required_fields = ['title', 'vendor', 'product_type']
    for field in required_fields:
        if not product_data.get(field) or not isinstance(product_data.get(field), str) or not product_data.get(field).strip():
            raise custom_errors.ValidationError(f"Required field '{field}' must be a non-empty string.")
    
    # Validate optional fields
    if 'status' in product_data and product_data['status'] not in ['active', 'archived', 'draft']:
        raise custom_errors.ValidationError("Status must be one of: 'active', 'archived', 'draft'.")
    
    if 'variants' in product_data and product_data['variants'] is not None:
        if not isinstance(product_data['variants'], list):
            raise custom_errors.ValidationError("Variants must be a list if provided.")
        for i, variant in enumerate(product_data['variants']):
            if not isinstance(variant, dict):
                raise custom_errors.ValidationError(f"Variant at index {i} must be a dictionary.")
    
    if 'options' in product_data and product_data['options'] is not None:
        if not isinstance(product_data['options'], list):
            raise custom_errors.ValidationError("Options must be a list if provided.")
        for i, option in enumerate(product_data['options']):
            if not isinstance(option, dict):
                raise custom_errors.ValidationError(f"Option at index {i} must be a dictionary.")
    
    if 'images' in product_data and product_data['images'] is not None:
        if not isinstance(product_data['images'], list):
            raise custom_errors.ValidationError("Images must be a list if provided.")
        for i, image in enumerate(product_data['images']):
            if not isinstance(image, dict):
                raise custom_errors.ValidationError(f"Image at index {i} must be a dictionary.")

    # Use custom_id if provided, otherwise generate one
    product_id = custom_id if custom_id is not None else generate_next_resource_id(DB.get('products', {}))
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat().replace('+00:00', 'Z')

    # Generate unique handle and check for conflicts
    base_handle = slugify(product_data.get('title', ''))
    handle = base_handle
    handle_counter = 1
    existing_handles = {p.get('handle') for p in DB.get('products', {}).values() if isinstance(p, dict)}
    while handle in existing_handles:
        handle = f"{base_handle}-{handle_counter}"
        handle_counter += 1

    variants_to_create = product_data.get('variants', [])

    if not variants_to_create:
        variants_to_create = [{'title': 'Default Title', 'price': '0.00'}]

    variants = []
    all_variants = [variant for p in DB.get('products', {}).values() for variant in p.get('variants', [])]
    
    next_variant_id = int(generate_next_resource_id(all_variants))

    for i, variant_data in enumerate(variants_to_create):
        variant_id = str(next_variant_id + i)
        variant = dict(
            id=variant_id,
            product_id=product_id,
            position=i + 1,
            **variant_data,
            created_at=now,
            updated_at=now,
            inventory_item_id=str(int(variant_id) + 10000), # Simple way to generate inventory_item_id
            admin_graphql_api_id=generate_gid('ProductVariant', variant_id)
        )
        variants.append(variant)

    product_options = []
    all_options = [opt for p in DB.get('products', {}).values() for opt in p.get('options', [])]
    next_option_id = int(generate_next_resource_id(all_options))

    if product_data.get('options'):
        for i, option_data in enumerate(product_data.get('options', [])):
            option_id = str(next_option_id + i)
            option = dict(
                id=option_id,
                product_id=product_id,
                name=option_data.get('name'),
                position=i + 1,
                values=option_data.get('values', [])
            )
            product_options.append(option)

    product_images = []
    all_images = [img for p in DB.get('products', {}).values() for img in p.get('images', [])]
    next_image_id = int(generate_next_resource_id(all_images))

    if product_data.get('images'):
        for i, image_data in enumerate(product_data.get('images', [])):
            image_id = str(next_image_id + i)
            image = dict(
                id=image_id,
                product_id=product_id,
                position=i + 1,
                created_at=now,
                updated_at=now,
                **image_data
            )
            product_images.append(image)

    new_product = ShopifyProductModel(
        id=product_id,
        title=product_data.get('title', ''),
        body_html=product_data.get('body_html', ''),
        vendor=product_data.get('vendor', ''),
        product_type=product_data.get('product_type', ''),
        status=product_data.get('status', 'active'),
        tags=product_data.get('tags', ''),
        created_at=now,
        updated_at=now,
        published_at=now if product_data.get('status', 'active') == 'active' else None,
        handle=handle,
        admin_graphql_api_id=generate_gid('Product', product_id),
        variants=variants,
        options=product_options,
        images=product_images,
        image=product_images[0] if product_images else None
    )

    # Validate the created product using Pydantic model
    try:
        product_dict = new_product.model_dump(by_alias=True)
    except Exception as e:
        raise custom_errors.ValidationError(f"Product creation failed during model validation: {str(e)}")

    # Store in database
    if 'products' not in DB:
        DB['products'] = {}
    DB['products'][product_id] = convert_datetimes_to_zulu_string(product_dict)

    return DB['products'][product_id]

def update_product(product_id: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
    """Updates an existing product with partial field updates and nested resource management.

    Enables modification of product information with flexible update logic for variants, options, and images.
    
    Nested Resource Logic:
    - **Update existing:** Include the item's `id` along with fields to change
    - **Add new:** Provide item data without an `id` (new ID auto-generated)  
    - **Delete existing:** Omit the item from the list entirely (removes from product)

    Args:
        product_id (str): Unique identifier of the product to update.
            Example: "7563847372996"
        product_data (Dict[str, Any]): Dictionary containing fields to update.
            title (str, optional): New product name
            vendor (str, optional): New vendor name  
            product_type (str, optional): New product category
            status (str, optional): New status ("active", "archived", "draft")
            tags (str, optional): Comma-separated tags string
            variants (List[Dict], optional): Variant objects to update/create/delete
            options (List[Dict], optional): Option objects to update/create/delete
            images (List[Dict], optional): Image objects to update/create/delete

    Returns:
        Dict[str, Any]: Complete updated product object with keys:
            id (str): Product unique identifier
            title (str): Product name
            handle (str): URL-friendly product handle
            vendor (str): Product vendor
            product_type (str): Product category
            status (str): Product status
            created_at (str): ISO 8601 creation timestamp
            updated_at (str): ISO 8601 last modified timestamp
            published_at (str|None): ISO 8601 publish timestamp or None if not active
            variants (List[Dict]): Array of variant objects, each dict with keys:
                id (str): Variant unique identifier
                title (str): Variant name
                price (str): Variant price as decimal string
                sku (str|None): Stock keeping unit
                inventory_quantity (int): Available inventory count
                position (int): Display order position
            options (List[Dict]): Array of option objects, each dict with keys:
                id (str): Option unique identifier
                name (str): Option name (e.g., "Size", "Color")
                values (List[str]): Available option values
                position (int): Display order position
            images (List[Dict]): Array of image objects, each dict with keys:
                id (str): Image unique identifier
                alt (str|None): Alternative text description
                position (int): Display order position
                width (int): Image width in pixels
                height (int): Image height in pixels

    Raises:
        NotFoundError: If product with specified product_id does not exist.
        ValidationError: If product_data format is invalid or contains malformed nested structures.
    """
    # Input validation
    if not isinstance(product_data, dict):
        raise custom_errors.ValidationError("Product data must be a dictionary.")
    
    if not isinstance(product_id, str) or not product_id.strip():
        raise custom_errors.ValidationError("Product ID must be a non-empty string.")

    # Check if product exists
    if product_id not in DB.get('products', {}):
        raise custom_errors.NotFoundError(f"Product with id '{product_id}' not found.")

    product_to_update = DB['products'][product_id].copy()  # Work on a copy for safety
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat().replace('+00:00', 'Z')
    
    # Store original status for published_at logic
    original_status = product_to_update.get('status')
    
    # Update top-level fields
    for key, value in product_data.items():
        if key not in ['variants', 'options', 'images', 'id'] and value is not None:
            product_to_update[key] = value

    # Auto-generate handle from title if title updated but handle not provided
    if 'title' in product_data and 'handle' not in product_data and product_data['title']:
        product_to_update['handle'] = slugify(product_data['title'])

    # Handle published_at based on status changes
    new_status = product_to_update.get('status')
    if 'status' in product_data:
        if new_status == 'active' and original_status != 'active':
            product_to_update['published_at'] = now_iso
        elif new_status != 'active' and original_status == 'active':
            product_to_update['published_at'] = None

    product_to_update['updated_at'] = now_iso

    # Handle variants
    if 'variants' in product_data and product_data['variants'] is not None:
        if not isinstance(product_data['variants'], list):
            raise custom_errors.ValidationError("Variants must be a list.")
            
        new_variants_list = []
        existing_variants_map = {str(v['id']): v for v in product_to_update.get('variants', [])}
        
        all_variants = [variant for p in DB['products'].values() for variant in p.get('variants', [])]
        next_variant_id = int(generate_next_resource_id(all_variants))
        new_variant_counter = 0

        for i, variant_data in enumerate(product_data['variants']):
            if not isinstance(variant_data, dict):
                raise custom_errors.ValidationError(f"Variant at index {i} must be a dictionary.")
                
            variant_id = str(variant_data.get('id')) if variant_data.get('id') else None
            if variant_id and variant_id in existing_variants_map:  # Update existing
                variant_to_update = existing_variants_map[variant_id].copy()
                for k, v in variant_data.items():
                    if k != 'id' and v is not None:  # Don't allow ID changes
                        variant_to_update[k] = v
                variant_to_update['updated_at'] = now
                variant_to_update['position'] = i + 1  # Update position based on list order
                new_variants_list.append(variant_to_update)
            elif not variant_id:  # Add new variant only if no ID provided
                new_variant_id = str(next_variant_id + new_variant_counter)
                new_variant = {
                    'id': new_variant_id,
                    'product_id': product_id,
                    'position': i + 1,
                    'title': 'Default Title',  # Default values
                    'price': '0.00',
                    'sku': None,
                    'inventory_quantity': 0,
                    'requires_shipping': True,
                    'taxable': True,
                    'grams': 0,
                    'weight': 0.0,
                    'weight_unit': 'kg',
                    'created_at': now,
                    'updated_at': now,
                    'inventory_item_id': str(int(new_variant_id) + 10000),
                    'admin_graphql_api_id': generate_gid('ProductVariant', new_variant_id)
                }
                # Override with provided data
                for k, v in variant_data.items():
                    if k != 'id' and v is not None:
                        new_variant[k] = v
                new_variants_list.append(new_variant)
                new_variant_counter += 1
        
        product_to_update['variants'] = new_variants_list

    # Handle options
    if 'options' in product_data and product_data['options'] is not None:
        if not isinstance(product_data['options'], list):
            raise custom_errors.ValidationError("Options must be a list.")
            
        new_options_list = []
        existing_options_map = {str(o['id']): o for o in product_to_update.get('options', [])}

        all_options = [opt for p in DB['products'].values() for opt in p.get('options', [])]
        next_option_id = int(generate_next_resource_id(all_options))
        new_option_counter = 0

        for i, option_data in enumerate(product_data['options']):
            if not isinstance(option_data, dict):
                raise custom_errors.ValidationError(f"Option at index {i} must be a dictionary.")
                
            option_id = str(option_data.get('id')) if option_data.get('id') else None
            if option_id and option_id in existing_options_map:  # Update existing
                option_to_update = existing_options_map[option_id].copy()
                for k, v in option_data.items():
                    if k != 'id' and v is not None:
                        option_to_update[k] = v
                option_to_update['position'] = i + 1
                new_options_list.append(option_to_update)
            elif not option_id:  # Add new option only if no ID provided
                new_option_id = str(next_option_id + new_option_counter)
                new_option = {
                    'id': new_option_id,
                    'product_id': product_id,
                    'position': i + 1,
                    'name': option_data.get('name', ''),
                    'values': option_data.get('values', [])
                }
                new_options_list.append(new_option)
                new_option_counter += 1
        
        product_to_update['options'] = new_options_list

    # Handle images
    if 'images' in product_data and product_data['images'] is not None:
        if not isinstance(product_data['images'], list):
            raise custom_errors.ValidationError("Images must be a list.")
            
        new_images_list = []
        existing_images_map = {str(img['id']): img for img in product_to_update.get('images', [])}

        all_images = [img for p in DB['products'].values() for img in p.get('images', [])]
        next_image_id = int(generate_next_resource_id(all_images))
        new_image_counter = 0

        for i, image_data in enumerate(product_data['images']):
            if not isinstance(image_data, dict):
                raise custom_errors.ValidationError(f"Image at index {i} must be a dictionary.")
                
            image_id = str(image_data.get('id')) if image_data.get('id') else None
            if image_id and image_id in existing_images_map:  # Update existing
                image_to_update = existing_images_map[image_id].copy()
                for k, v in image_data.items():
                    if k != 'id' and v is not None:
                        image_to_update[k] = v
                image_to_update['updated_at'] = now
                image_to_update['position'] = i + 1
                new_images_list.append(image_to_update)
            elif not image_id:  # Add new image only if no ID provided
                new_image_id = str(next_image_id + new_image_counter)
                new_image = {
                    'id': new_image_id,
                    'product_id': product_id,
                    'position': i + 1,
                    'created_at': now,
                    'updated_at': now,
                    'src': image_data.get('src'),  # Required field for Pydantic model
                    'alt': image_data.get('alt'),
                    'width': image_data.get('width', 0),
                    'height': image_data.get('height', 0),
                    'variant_ids': image_data.get('variant_ids', [])
                }
                new_images_list.append(new_image)
                new_image_counter += 1
        
        product_to_update['images'] = new_images_list

        # Update primary image field
        if new_images_list:
            product_to_update['image'] = new_images_list[0]
        else:
            product_to_update['image'] = None

    # Validate the updated product using Pydantic model
    try:
        validated_product = ShopifyProductModel.model_validate(product_to_update)
        product_dict = validated_product.model_dump(by_alias=True)
    except Exception as e:
        raise custom_errors.ValidationError(f"Product validation failed: {str(e)}")

    # Convert datetime objects to Zulu strings for database storage
    def convert_datetimes_to_zulu_string(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                obj[k] = convert_datetimes_to_zulu_string(v)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                obj[i] = convert_datetimes_to_zulu_string(item)
        elif isinstance(obj, datetime):
            return obj.isoformat().replace('+00:00', 'Z')
        return obj

    # Update the database
    DB['products'][product_id] = convert_datetimes_to_zulu_string(product_dict)
    
    return DB['products'][product_id]

  
def _format_datetime(dt_val: Optional[Union[datetime, str]]) -> Optional[str]:
    if dt_val is None:
        return None
    if isinstance(dt_val, str):
        # Assume dt_val is already a valid ISO 8601 string if it's a string.
        # This relies on upstream data (like test setup or DB state) providing correct ISO strings.
        return dt_val
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            # If datetime is naive, assume UTC.
            dt_val = dt_val.replace(tzinfo=timezone.utc)
        return dt_val.isoformat()
    # Fallback for unexpected types, though type hints should prevent this.
    # Consider raising TypeError for more robust handling if other types could appear.
    return str(dt_val)

# --- Cross-Payment Method Refund Utilities ---

def validate_customer_payment_method_access(customer_id: str, payment_method_id: str) -> bool:
    """Validate that customer has access to the specified payment method.
    
    This function checks if a customer has a specific payment method registered
    in their account, which is required for cross-payment method refunds to ensure
    security and prevent unauthorized refunds to payment methods not owned by the customer.
    
    Args:
        customer_id (str): The ID of the customer to check payment method access for.
        payment_method_id (str): The ID of the payment method to validate access to.
        
    Returns:
        bool: True if the customer has access to the payment method, False otherwise.
              Returns False if customer_id is empty, customer doesn't exist, or 
              payment method is not found in customer's payment methods list.
    """
    if not customer_id:
        return False
    
    customer_data = DB.get('customers', {}).get(customer_id)
    if not customer_data:
        return False
    
    customer_payment_methods = customer_data.get('payment_methods', [])
    return any(pm.get('id') == payment_method_id for pm in customer_payment_methods)


def get_gateway_for_payment_method(payment_method_id: str) -> str:
    """Get the gateway associated with a payment method.
    
    This function maps payment method IDs to their respective payment gateways
    to enable proper routing of cross-payment method refunds. The mapping is based
    on payment method ID prefixes that indicate the gateway type.
    
    Args:
        payment_method_id (str): The ID of the payment method to get the gateway for.
                                Format examples: "pm_paypal_123", "pm_stripe_456", "pm_manual_789"
        
    Returns:
        str: The gateway name associated with the payment method.
             Returns 'manual' as fallback if no specific gateway is identified.
             Possible values: 'paypal', 'stripe', 'shopify_payments', 'manual'
    """
    if payment_method_id.startswith('pm_paypal_'):
        return 'paypal'
    elif payment_method_id.startswith('pm_stripe_'):
        return 'stripe'
    elif payment_method_id.startswith('pm_shopify_'):
        return 'shopify_payments'
    elif payment_method_id.startswith('pm_manual_'):
        return 'manual'
    else:
        return 'manual'  # fallback


def migrate_existing_transactions_for_cross_payment_support():
    """
    Migrate existing transactions to include original_payment_method_id.
    
    This utility function ensures backward compatibility when adding cross-payment method support
    by updating existing transaction records to include the original_payment_method_id field.
    It also migrates customer data to include payment methods if not present.
    
    This function should be called once during system upgrade to ensure all existing
    transactions and customers have the necessary fields for cross-payment method refunds.
    
    Returns:
        None: Modifies the database in-place.
        
    Side Effects:
        - Updates all existing transactions to include original_payment_method_id
        - Updates all existing customers to include payment_methods list
        - Infers payment methods from customer transaction history
    """
    from datetime import datetime, timezone
    
    # Migrate transactions
    for order_id, order in DB['orders'].items():
        for transaction in order.get('transactions', []):
            if not transaction.get('original_payment_method_id'):
                # Infer original payment method from gateway
                gateway = transaction.get('gateway', 'manual')
                transaction['original_payment_method_id'] = f"pm_{gateway}_{transaction['id']}"
    
    # Migrate customer data to include payment methods if not present
    for customer_id, customer in DB['customers'].items():
        if 'payment_methods' not in customer:
            customer['payment_methods'] = []
            # Infer payment methods from their transaction history
            customer_payment_methods = set()
            for order in DB['orders'].values():
                if order.get('customer', {}).get('id') == customer_id:
                    for transaction in order.get('transactions', []):
                        gateway = transaction.get('gateway', 'manual')
                        if gateway != 'manual':
                            pm_id = f"pm_{gateway}_{customer_id}"
                            customer_payment_methods.add((pm_id, gateway))
            
            # Add inferred payment methods to customer
            for pm_id, gateway in customer_payment_methods:
                payment_method_type = 'credit_card' if gateway in ['stripe', 'shopify_payments'] else gateway
                customer['payment_methods'].append({
                    'id': pm_id,
                    'type': payment_method_type,
                    'gateway': gateway,
                    'is_default': len(customer['payment_methods']) == 0,
                    'created_at': customer.get('created_at'),
                    'updated_at': customer.get('updated_at')
                })
        
        # Add default_payment_method_id if not present
        if 'default_payment_method_id' not in customer:
            payment_methods = customer.get('payment_methods', [])
            default_pm = next((pm for pm in payment_methods if pm.get('is_default')), None)
            customer['default_payment_method_id'] = default_pm['id'] if default_pm else None


def _format_datetime(dt_val: Optional[Union[datetime, str]]) -> Optional[str]:
    if dt_val is None:
        return None
    if isinstance(dt_val, str):
        # Assume dt_val is already a valid ISO 8601 string if it's a string.
        # This relies on upstream data (like test setup or DB state) providing correct ISO strings.
        return dt_val
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            # If datetime is naive, assume UTC.
            dt_val = dt_val.replace(tzinfo=timezone.utc)
        return dt_val.isoformat()
    # Fallback for unexpected types, though type hints should prevent this.
    # Consider raising TypeError for more robust handling if other types could appear.
    return str(dt_val)

def _validate_fulfillment_status_consistency(order_data: Dict[str, Any], order_fulfillment_status: Optional[str]) -> None:
    """Validates that order-level fulfillment status is consistent with line item statuses.
    
    Args:
        order_data: Order dictionary containing line items
        order_fulfillment_status: Proposed order-level fulfillment status (can be None)
        
    Raises:
        InvalidInputError: If the order-level status is inconsistent with line item statuses
    """
    line_items = order_data.get('line_items', [])
    if not line_items:
        return
    
    # Get shippable items and their fulfillment statuses
    shippable_items = [item for item in line_items if item.get('requires_shipping', False)]
    
    if not shippable_items:
        # No shippable items - order status should be None
        if order_fulfillment_status is not None:
            raise custom_errors.InvalidInputError(
                f"Order fulfillment_status should be null when no line items require shipping, "
                f"but '{order_fulfillment_status}' was provided."
            )
        return
    
    # If order status is explicitly set to None but we have shippable items, that's invalid
    if order_fulfillment_status is None:
        raise custom_errors.InvalidInputError(
            f"Order fulfillment_status cannot be null when there are {len(shippable_items)} shippable line items. "
            f"Expected one of: 'fulfilled', 'partial', or 'unfulfilled'."
        )
    
    # Count fulfillment statuses for shippable items
    # Note: None fulfillment_status for shippable items is treated as 'unfulfilled'
    fulfilled_count = 0
    unfulfilled_count = 0
    
    for item in shippable_items:
        item_status = item.get('fulfillment_status')
        if item_status == 'fulfilled':
            fulfilled_count += 1
        elif item_status in [None, 'unfulfilled', 'partial', 'restocked']:
            # None, 'unfulfilled', 'partial', and 'restocked' are all treated as not fulfilled
            unfulfilled_count += 1
        else:
            # Handle any unexpected status values
            unfulfilled_count += 1
    
    total_shippable = len(shippable_items)
    
    # Determine what the calculated status should be
    if fulfilled_count == total_shippable:
        expected_status = "fulfilled"
    elif fulfilled_count > 0:
        expected_status = "partial"
    else:
        expected_status = "unfulfilled"
    
    # Validate consistency
    if order_fulfillment_status != expected_status:
        # Create a helpful error message with detailed breakdown
        status_breakdown = []
        for item in shippable_items:
            item_status = item.get('fulfillment_status', 'None')
            item_id = item.get('id', 'unknown')
            status_breakdown.append(f"item {item_id}: {item_status}")
        
        status_summary = f"{fulfilled_count}/{total_shippable} shippable items fulfilled"
        detailed_breakdown = "; ".join(status_breakdown)
        
        raise custom_errors.InvalidInputError(
            f"Order fulfillment_status '{order_fulfillment_status}' is inconsistent with line item statuses. "
            f"Based on line items ({status_summary}), expected status should be '{expected_status}'. "
            f"Line item breakdown: [{detailed_breakdown}]. "
            f"Either adjust the line item fulfillment statuses or remove the order-level override to use auto-calculation."
        )


def create_order_with_custom_id(order_data: Dict[str, Any], custom_id: str) -> Dict[str, Any]:
    """Creates an order with a specific custom ID and fulfillment status support.
    
    This utility function enables creation of orders with predefined IDs for testing,
    data migration, or integration scenarios where ID consistency is required across systems.
    Also supports setting fulfillment status at both line item and order levels.
    
    Fulfillment Status Behavior:
    - Each line item can have its own fulfillment_status
    - The overall order fulfillment_status is automatically calculated from line item statuses:
      * "fulfilled": All shippable items are fulfilled
      * "partial": Some but not all shippable items are fulfilled
      * "unfulfilled": No shippable items are fulfilled
      * None: No items require shipping (digital/virtual products)
    - If order-level fulfillment_status is provided, it will override the auto-calculation
    - Validation ensures order-level status is consistent with line item statuses
    
    Args:
        order_data (Dict[str, Any]): Complete order creation data with all required fields.
            Must include all fields required by create_order except 'id'.
            See create_order documentation for detailed field specifications.
            
            Additional fulfillment support:
            line_items (List[Dict[str, Any]]): Each line item can include:
                fulfillment_status (str, optional): Individual line item fulfillment status.
                    Options: "fulfilled", "partial", "unfulfilled", "restocked", None
                    Example line item: {
                        "variant_id": "123",
                        "quantity": 2,
                        "fulfillment_status": "fulfilled"
                    }
            fulfillment_status (str, optional): Override order-level fulfillment status.
                Options: "fulfilled", "partial", "unfulfilled", None
                If not provided, automatically calculated from line item statuses.
                
        custom_id (str): Unique identifier to assign to the new order.
            Must be a non-empty string and not already exist in the orders database.
            Examples: "ORDER-2024-001", "MIGRATION-12345", "TEST-ORDER-ABC"
    
    Returns:
        Dict[str, Any]: Created order response from create_order with the custom ID.
            Contains all standard order fields plus the custom ID as specified.
            order (Dict[str, Any]): Order object with keys:
                id (str): The custom ID provided
                fulfillment_status (str|None): Calculated or overridden fulfillment status
                line_items (List[Dict]): Line items with their individual fulfillment statuses and fulfillable_quantities
                [all other standard order fields]
    
    Raises:
        InvalidInputError: If custom_id is empty/invalid or already exists in the database,
            or if order-level fulfillment_status is inconsistent with line item statuses.
        ValidationError: If order_data is invalid or missing required fields.
        ShopifyApiError: If order creation fails due to internal processing errors.
    
    Example:
        >>> order_data = {
        ...     "line_items": [
        ...         {"variant_id": "123", "quantity": 1, "fulfillment_status": "fulfilled"},
        ...         {"variant_id": "456", "quantity": 2, "fulfillment_status": "unfulfilled"}
        ...     ],
        ...     "customer": {"email": "test@example.com"},
        ...     "fulfillment_status": "partial"  # Override auto-calculation
        ... }
        >>> result = create_order_with_custom_id(order_data, "CUSTOM-ORDER-001")
        >>> print(result["order"]["id"])  # "CUSTOM-ORDER-001"
        >>> print(result["order"]["fulfillment_status"])  # "partial"
    """
    # Import here to avoid circular imports
    from ..orders import shopify_create_an_order
    
    # Validate custom_id parameter
    if not isinstance(custom_id, str) or not custom_id.strip():
        raise custom_errors.InvalidInputError("custom_id must be a non-empty string.")
    
    # Check if custom_id already exists
    if custom_id in DB.get('orders', {}):
        raise custom_errors.InvalidInputError(f"Order with ID '{custom_id}' already exists.")
    
    # Validate order_data parameter
    if not isinstance(order_data, dict):
        raise custom_errors.ValidationError("order_data must be a dictionary.")
    
    # Create a copy to avoid modifying the original data
    order_data_clean = order_data.copy()
    
    # Extract fulfillment status override if provided
    # We need to distinguish between "not provided" and "explicitly set to None"
    fulfillment_status_was_provided = 'fulfillment_status' in order_data_clean
    order_level_fulfillment_override = order_data_clean.pop('fulfillment_status', None)
    
    # Remove any existing 'id' field
    if 'id' in order_data_clean:
        del order_data_clean['id']
    
    # Create the order using the existing function (this will generate an auto ID)
    result = shopify_create_an_order(order_data_clean)
    
    # Get the auto-generated ID
    auto_generated_id = result['order']['id']
    
    # Update the database to use our custom ID instead
    # 1. Remove the order with auto-generated ID
    auto_generated_order_data = DB['orders'].pop(auto_generated_id)
    
    # 2. Update line items with any provided fulfillment statuses and fulfillable quantities
    if 'line_items' in order_data and order_data['line_items']:
        for i, line_item_input in enumerate(order_data['line_items']):
            if isinstance(line_item_input, dict) and i < len(auto_generated_order_data['line_items']):
                line_item = auto_generated_order_data['line_items'][i]
                
                # Handle fulfillment_status
                if 'fulfillment_status' in line_item_input:
                    line_item['fulfillment_status'] = line_item_input['fulfillment_status']
                
                # Calculate fulfillable_quantity based on fulfillment_status
                fulfillment_status = line_item.get('fulfillment_status')
                item_quantity = line_item.get('quantity', 0)
                
                if fulfillment_status == 'fulfilled':
                    line_item['fulfillable_quantity'] = 0
                elif fulfillment_status in [None, 'unfulfilled', 'restocked']:
                    line_item['fulfillable_quantity'] = item_quantity
                elif fulfillment_status == 'partially_fulfilled':
                    # For partially fulfilled, keep some fulfillable quantity
                    # Default to half the quantity if not specified
                    line_item['fulfillable_quantity'] = max(1, item_quantity // 2)
                else:
                    # Default case
                    line_item['fulfillable_quantity'] = item_quantity
    
    # 3. Handle order-level fulfillment status
    if fulfillment_status_was_provided:
        # Fulfillment status was explicitly provided (even if it's None)
        # Validate that the override is consistent with line item statuses
        _validate_fulfillment_status_consistency(auto_generated_order_data, order_level_fulfillment_override)
        
        # Override with provided status
        auto_generated_order_data['fulfillment_status'] = order_level_fulfillment_override
    else:
        # No fulfillment status provided, recalculate based on line item statuses
        updated_fulfillment_info = update_order_fulfillment_status(auto_generated_order_data)
        auto_generated_order_data['fulfillment_status'] = updated_fulfillment_info['fulfillment_status']
    
    # 4. Update the order data to use custom ID
    auto_generated_order_data['id'] = custom_id
    auto_generated_order_data['admin_graphql_api_id'] = generate_gid("Order", custom_id)
    auto_generated_order_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # 5. Store the order with custom ID
    DB['orders'][custom_id] = auto_generated_order_data
    
    # 6. Update the response to reflect the custom ID and fulfillment status
    result['order']['id'] = custom_id
    result['order']['admin_graphql_api_id'] = generate_gid("Order", custom_id)
    result['order']['fulfillment_status'] = auto_generated_order_data['fulfillment_status']
    result['order']['updated_at'] = auto_generated_order_data['updated_at']
    
    # 7. Update response line items with fulfillment statuses and fulfillable quantities
    if 'line_items' in result['order']:
        for i, line_item in enumerate(result['order']['line_items']):
            if i < len(auto_generated_order_data['line_items']):
                db_line_item = auto_generated_order_data['line_items'][i]
                line_item['fulfillment_status'] = db_line_item.get('fulfillment_status')
                line_item['fulfillable_quantity'] = db_line_item.get('fulfillable_quantity', 0)
    
    return result

def create_customer(customer_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a new customer from a dictionary of customer information.

    This function validates the input, ensures uniqueness of email, and generates a new customer record
    with all required and optional fields. The returned dictionary contains all customer fields, including
    nested address and payment method information, matching the structure of Shopify's customer API.

    Args:
        customer_data (Dict[str, Any]): Dictionary containing the new customer's information.
            Fields (all are optional unless otherwise noted):
                email (str, optional): Customer's email address. Must be unique if provided.
                first_name (str, optional): The customer's first name.
                last_name (str, optional): The customer's last name.
                orders_count (int, optional): Number of orders for this customer. Defaults to 0 if not provided.
                state (str, optional): Account state (e.g., 'enabled'). Defaults to 'enabled'.
                total_spent (str, optional): Total amount spent by the customer, as a string. Defaults to "0.00".
                phone (str, optional): The customer's phone number.
                tags (str, optional): Comma-separated tags associated with the customer.
                gift_card_balance (str, optional): Gift card balance for the customer. Defaults to "0.00".
                default_address (dict, optional): The default address for the customer. Fields:
                    address1 (str, optional): Primary street address line.
                    address2 (str, optional): Secondary address line (apartment, suite, etc.).
                    city (str, optional): City name.
                    province (str, optional): Province or state name.
                    country (str, optional): Country name.
                    zip (str, optional): Postal or ZIP code.
                    phone (str, optional): Address-specific phone number.
                    first_name (str, optional): Recipient's first name.
                    last_name (str, optional): Recipient's last name.
                    name (str, optional): Full name for the address.
                    province_code (str, optional): Two-letter province code (e.g., 'CA', 'NY').
                    country_code (str, optional): Two-letter country code (e.g., 'US', 'CA').
                    country_name (str, optional): Full country name.
                    company (str, optional): Company name.
                    latitude (float, optional): Geographic latitude.
                    longitude (float, optional): Geographic longitude.
                    default (bool, optional): Whether this is the customer's default address.
                addresses (list of dict, optional): List of address dictionaries, each with the same fields as default_address.
                payment_methods (list of dict, optional): List of payment method dictionaries, each with:
                    type (str): Payment method type ("credit_card", "paypal", "bank_account", "gift_card").
                    gateway (str): Payment gateway ("stripe", "paypal", "manual", "shopify_payments").
                    last_four (str, optional): Last four digits of the payment method.
                    brand (str, optional): Brand of the payment method ("visa", "mastercard", "paypal").
                    is_default (bool, optional): Whether this is the default payment method.
                default_payment_method_id (str, optional): The ID of the default payment method.

    Returns:
        Dict[str, Any]: The newly created customer as a dictionary, with all fields:
            id (str): Unique customer identifier (auto-generated).
            email (str, optional): Customer's email address.
            first_name (str, optional): The customer's first name.
            last_name (str, optional): The customer's last name.
            orders_count (int): Number of orders for this customer.
            state (str, optional): Account state (e.g., 'enabled').
            total_spent (str, optional): Total amount spent by the customer, as a string.
            phone (str, optional): The customer's phone number.
            tags (str, optional): Comma-separated tags associated with the customer.
            created_at (str): ISO 8601 timestamp when the customer was created (auto-generated).
            updated_at (str): ISO 8601 timestamp when the customer was last updated (auto-generated).
            gift_card_balance (str, optional): Gift card balance for the customer.
            default_address (dict, optional): The default address for the customer, with fields:
                id (str, optional): Address unique identifier.
                customer_id (str, optional): Associated customer ID.
                address1 (str, optional): Primary street address line.
                address2 (str, optional): Secondary address line (apartment, suite, etc.).
                city (str, optional): City name.
                province (str, optional): Province or state name.
                country (str, optional): Country name.
                zip (str, optional): Postal or ZIP code.
                phone (str, optional): Address-specific phone number.
                first_name (str, optional): Recipient's first name.
                last_name (str, optional): Recipient's last name.
                name (str, optional): Full name for the address.
                province_code (str, optional): Two-letter province code (e.g., 'CA', 'NY').
                country_code (str, optional): Two-letter country code (e.g., 'US', 'CA').
                country_name (str, optional): Full country name.
                company (str, optional): Company name.
                latitude (float, optional): Geographic latitude.
                longitude (float, optional): Geographic longitude.
                default (bool, optional): Whether this is the customer's default address.
            addresses (list of dict, optional): List of address dictionaries, each with the same fields as default_address.
            payment_methods (list of dict, optional): List of payment method dictionaries, each with:
                id (str): Payment method unique identifier.
                type (str): Payment method type ("credit_card", "paypal", "bank_account", "gift_card").
                gateway (str): Payment gateway ("stripe", "paypal", "manual", "shopify_payments").
                last_four (str, optional): Last four digits of the payment method.
                brand (str, optional): Brand of the payment method ("visa", "mastercard", "paypal").
                is_default (bool): Whether this is the default payment method.
                created_at (str): ISO 8601 timestamp when the payment method was created.
                updated_at (str): ISO 8601 timestamp when the payment method was last updated.
            default_payment_method_id (str, optional): The ID of the default payment method.

    Raises:
        InvalidInputError: If the input is not a dictionary, missing both email and phone, or if the email already exists or if the customer has more than one default address or payment method.
    """
    if not isinstance(customer_data, dict):
        raise custom_errors.InvalidInputError("Input must be a customer dictionary.")

    if not customer_data.get('email') and not customer_data.get('phone'):
        raise custom_errors.InvalidInputError("A customer must have either an 'email' or a 'phone' number.")

    customers_table = DB.get('customers', {})

    if customer_data.get('email'):
        for existing_customer in customers_table.values():
            if existing_customer.get('email') == customer_data.get('email'):
                raise custom_errors.InvalidInputError(
                    f"A customer with the email '{customer_data.get('email')}' already exists."
                )

    now = datetime.now(timezone.utc)
    
    # Pre-process addresses
    if 'addresses' in customer_data:
        addresses = customer_data.get('addresses', [])
        default_addresses = [addr for addr in addresses if addr.get('is_default')]
        if len(default_addresses) > 1:
            raise custom_errors.InvalidInputError("Only one address can be marked as 'is_default'.")
        
        for i, addr in enumerate(addresses):
            if not addr.get('id'):
                addr['id'] = str(i + 1)

    # Pre-process payment methods
    if 'payment_methods' in customer_data:
        payment_methods = customer_data.get('payment_methods', [])
        default_pms = [pm for pm in payment_methods if pm.get('is_default')]
        if len(default_pms) > 1:
            raise custom_errors.InvalidInputError("Only one payment method can be marked as 'is_default'.")

        for i, pm in enumerate(payment_methods):
            if not pm.get('id'):
                pm['id'] = str(i + 1)
            pm['created_at'] = now
            pm['updated_at'] = now

    new_customer_id = generate_next_resource_id(customers_table)

    try:
        new_customer = ShopifyCustomerModel(
            id=new_customer_id,
            state='enabled',
            **customer_data,
            created_at=now,
            updated_at=now,
        )
    except Exception as e:
        raise custom_errors.InvalidInputError(f"Invalid customer data: {str(e)}")

    new_customer_dict = new_customer.model_dump(by_alias=True)
    
    if 'addresses' in new_customer_dict:
        addresses = new_customer_dict.get('addresses', [])
        # Find all addresses marked as default
        default_addresses = [addr for addr in addresses if addr.get('is_default')]
        if len(default_addresses) == 1:
            # Use the passed default as the default_address
            new_customer_dict['default_address'] = default_addresses[0]
        elif addresses:
            # No default specified, set the first as default
            addresses[0]['is_default'] = True
            new_customer_dict['default_address'] = addresses[0]

    if 'payment_methods' in new_customer_dict:
        payment_methods = new_customer_dict.get('payment_methods', [])
        # Find all payment methods marked as default
        default_pms = [pm for pm in payment_methods if pm.get('is_default')]
        if len(default_pms) == 1:
            # Use the passed default as the default_payment_method_id
            new_customer_dict['default_payment_method_id'] = default_pms[0]['id']
        elif payment_methods:
            # No default specified, set the first as default
            payment_methods[0]['is_default'] = True
            new_customer_dict['default_payment_method_id'] = payment_methods[0]['id']

    DB['customers'][new_customer_id] = convert_datetimes_to_zulu_string(new_customer_dict)

    return DB['customers'][new_customer_id]

def modify_pending_order(order_id: str, order_updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Modifies an open order's details.

    Modifies an open order's details such as delivery address, payment information, or line items.
    This function allows modification of open orders whose shipment isn't fulfilled yet.

    The function follows a selective update approach:
    - Only fields included in order_updates will be modified
    - Omitted fields remain unchanged in the order
    - Nested objects (like addresses) are updated selectively - only provided fields are modified
    - Dependent calculations (totals, weights) are automatically updated
    - The updated_at timestamp is always updated regardless of which fields are modified

    List Type Handling:
    1. Line Items (Selective Update Only):
       - Updates existing line items in place using their IDs
       - Cannot add new line items, only modify existing ones
       - Updates individual fields (quantity, price, properties) selectively

    2. Transactions (Update and Add):
       - Can update existing transactions and add new ones
       - Matches transactions by ID for updates
       - Automatically adds metadata for new transactions

    3. Simple Lists (Complete Replacement):
       - Applies to shipping_lines, tax_lines, discount_codes
       - Completely replaces the existing list with the new one
       - No partial updates or individual item validation

    Args:
        order_id (str): The ID of the order to modify.
        order_updates (Dict[str, Any]): Dictionary containing the fields to update.
            Fields that can be modified (all are optional):
                shipping_address (dict): Updated delivery address with fields:
                    address1 (str): Primary street address line.
                    address2 (str, optional): Secondary address line (apartment, suite, etc.).
                    city (str): City name.
                    province (str): Province or state name.
                    province_code (str): Province or state code.
                    country (str): Country name.
                    country_code (str): Country code.
                    zip (str): Postal or ZIP code.
                    phone (str, optional): Address-specific phone number.
                    first_name (str): Recipient's first name.
                    last_name (str): Recipient's last name.
                    company (str, optional): Company name.
                transactions (list): List of transaction updates, each with:
                    id (str): Transaction ID.
                    amount (str): Transaction amount.
                    kind (str): Transaction type (sale, refund, etc.).
                    gateway (str): Payment gateway.
                    status (str): Transaction status.
                    currency (str): Transaction currency.
                    original_payment_method_id (str): Original payment method ID.
                line_items (list): List of line item updates, each with:
                    id (str): Line item ID to update.
                    quantity (int, optional): New quantity.
                    price (str, optional): New price.
                    properties (list, optional): List of item properties.
                shipping_lines (list): Complete list of shipping charges.
                tax_lines (list): Complete list of tax charges.
                discount_codes (list): Complete list of discount codes.

    Returns:
        Dict[str, Any]: The modified order with all fields updated:
            id (str): Unique order identifier.
            email (str): Customer's email address.
            created_at (str): ISO 8601 timestamp when order was created.
            updated_at (str): ISO 8601 timestamp when order was last updated.
            number (int): Sequential order number.
            token (str): Unique order token.
            gateway (str): Payment gateway identifier.
            total_price (str): Total order amount as decimal string.
            subtotal_price (str): Subtotal before shipping/taxes as decimal string.
            total_weight (int): Total weight in grams.
            total_tax (str): Total tax amount as decimal string.
            taxes_included (bool): Whether prices include tax.
            currency (str): Three-letter currency code (e.g., "USD").
            status (str): Order status ("open", "cancelled", "closed").
            fulfillment_status (str): Shipping status ("fulfilled", "partial", "unfulfilled", null).
            financial_status (str): Payment status ("pending", "paid", "refunded", "partially_refunded").
            total_discounts (str): Total discounts as decimal string.
            total_line_items_price (str): Sum of all line items as decimal string.
            line_items (list of dict): List of line item dictionaries, each with:
                id (str): Line item identifier.
                title (str): Product title.
                variant_id (str): Product variant identifier.
                quantity (int): Number of items ordered.
                price (str): Unit price as decimal string.
                sku (str): Stock keeping unit.
                requires_shipping (bool): Whether item needs shipping.
                taxable (bool): Whether item is taxable.
                properties (list of dict): Custom properties list, each with:
                    name (str): Property name.
                    value (str): Property value.
            shipping_address (dict): Delivery address with fields:
                id (str): Address identifier.
                first_name (str): Recipient first name.
                last_name (str): Recipient last name.
                address1 (str): Street address.
                address2 (str, optional): Apartment/Suite.
                city (str): City name.
                province (str): Province/State name.
                province_code (str): Province/State code.
                country (str): Country name.
                country_code (str): Two-letter country code.
                zip (str): Postal/ZIP code.
                phone (str, optional): Phone number.
                company (str, optional): Company name.
            transactions (list of dict): Payment transactions list, each with:
                id (str): Transaction identifier.
                order_id (str): Parent order identifier.
                amount (str): Transaction amount as decimal string.
                kind (str): Transaction type ("sale", "capture", "authorization", "void", "refund").
                gateway (str): Payment gateway identifier.
                status (str): Transaction status ("success", "pending", "failure").
                message (str, optional): Status message.
                created_at (str): ISO 8601 creation timestamp.
                currency (str): Three-letter currency code.
                authorization (str, optional): Authorization code.
                parent_id (str, optional): Parent transaction identifier.
            shipping_lines (list of dict): Shipping charges list, each with:
                title (str): Shipping method name.
                price (str): Shipping cost as decimal string.
                code (str, optional): Shipping method code.
            tax_lines (list of dict): Tax charges list, each with:
                title (str): Tax name.
                price (str): Tax amount as decimal string.
                rate (float): Tax rate.
            discount_codes (list of dict): Applied discount codes, each with:
                code (str): Discount code.
                amount (str): Discount amount as decimal string.
                type (str): Discount type ("fixed_amount", "percentage").

    Raises:
        InvalidInputError: If the order doesn't exist, isn't in an open state,
            is already fulfilled, or if the updates are invalid.
        ResourceNotFoundError: If the order ID is not found.
    """
    # Get the order from DB
    orders_table = DB.get('orders', {})
    if order_id not in orders_table:
        raise custom_errors.ResourceNotFoundError(f"Order with ID '{order_id}' not found.")

    order = orders_table[order_id]
    
    # Check if order is in a modifiable state
    if order.get('cancelled_at') is not None:
        raise custom_errors.InvalidInputError(
            f"Order '{order_id}' cannot be modified as it has been cancelled."
        )
    
    if order.get('closed_at') is not None:
        raise custom_errors.InvalidInputError(
            f"Order '{order_id}' cannot be modified as it has been closed."
        )
    
    fulfillment_status = order.get('fulfillment_status')
    if fulfillment_status and fulfillment_status.lower() == 'fulfilled':
        raise custom_errors.InvalidInputError(
            f"Order '{order_id}' cannot be modified as it has already been fulfilled."
        )

    now = datetime.now(timezone.utc)
    
    # Update shipping address if provided
    if 'shipping_address' in order_updates:
        required_address_fields = ['address1', 'city', 'province', 'country', 'zip', 'first_name', 'last_name']
        shipping_address = order_updates['shipping_address']
        
        for field in required_address_fields:
            if field not in shipping_address:
                raise custom_errors.InvalidInputError(f"Missing required field '{field}' in shipping_address")
        
        order['shipping_address'].update(shipping_address)

    # Update transactions if provided
    if 'transactions' in order_updates:
        required_transaction_fields = ['amount', 'kind', 'status']
        for transaction in order_updates['transactions']:
            for field in required_transaction_fields:
                if field not in transaction:
                    raise custom_errors.InvalidInputError(f"Missing required field '{field}' in transaction")
            
            # Find and update existing transaction or add new one
            existing_transaction = next(
                (t for t in order['transactions'] if t['id'] == transaction['id']),
                None
            )
            
            if existing_transaction:
                existing_transaction.update(transaction)
            else:
                # Add admin_graphql_api_id and created_at for new transactions
                transaction['admin_graphql_api_id'] = f"gid://shopify/OrderTransaction/{transaction['id']}"
                transaction['created_at'] = now.isoformat()
                order['transactions'].append(transaction)

    # Update line items if provided
    if 'line_items' in order_updates:
        existing_line_items = {item['id']: item for item in order['line_items']}
        
        for item_update in order_updates['line_items']:
            item_id = item_update.get('id')
            if not item_id or item_id not in existing_line_items:
                raise custom_errors.InvalidInputError(f"Invalid line item ID: {item_id}")
            
            existing_item = existing_line_items[item_id]
            
            # Update quantity if provided
            if 'quantity' in item_update:
                quantity = item_update['quantity']
                if not isinstance(quantity, int) or quantity < 0:
                    raise custom_errors.InvalidInputError(f"Invalid quantity for line item {item_id}: {quantity}")
                existing_item['quantity'] = quantity
                
                # Update price-related fields
                price = Decimal(existing_item['price'])
                existing_item['total_discount'] = "0.00"
                existing_item['line_price'] = str(price * quantity)

            # Update price if provided
            if 'price' in item_update:
                try:
                    price = Decimal(item_update['price'])
                    if price < 0:
                        raise ValueError("Price cannot be negative")
                    existing_item['price'] = str(price)
                    existing_item['line_price'] = str(price * existing_item['quantity'])
                except (TypeError, ValueError) as e:
                    raise custom_errors.InvalidInputError(f"Invalid price for line item {item_id}: {str(e)}")

            # Update properties if provided
            if 'properties' in item_update:
                existing_item['properties'] = item_update['properties']

    # Update simple fields
    simple_fields = ['note', 'tags']
    for field in simple_fields:
        if field in order_updates:
            order[field] = order_updates[field]

    # Update shipping lines if provided
    if 'shipping_lines' in order_updates:
        order['shipping_lines'] = order_updates['shipping_lines']

    # Update tax lines if provided
    if 'tax_lines' in order_updates:
        order['tax_lines'] = order_updates['tax_lines']

    # Update discount codes if provided
    if 'discount_codes' in order_updates:
        order['discount_codes'] = order_updates['discount_codes']

    # Recalculate order totals
    subtotal = Decimal('0')
    total_tax = Decimal('0')
    total_discounts = Decimal('0')
    total_weight = 0

    for item in order['line_items']:
        line_price = Decimal(item['line_price'])
        subtotal += line_price
        total_weight += int(item.get('grams', 0)) * item['quantity']

    for tax_line in order.get('tax_lines', []):
        total_tax += Decimal(tax_line.get('price', '0.00'))

    for discount in order.get('discount_codes', []):
        total_discounts += Decimal(discount.get('amount', '0.00'))

    shipping_total = sum(Decimal(line.get('price', '0.00')) for line in order.get('shipping_lines', []))

    # Format all decimal values consistently with 2 decimal places
    order['subtotal_price'] = "{:.2f}".format(subtotal)
    order['total_tax'] = "{:.2f}".format(total_tax)
    order['total_discounts'] = "{:.2f}".format(total_discounts)
    order['total_weight'] = total_weight
    order['total_price'] = "{:.2f}".format(subtotal + shipping_total + total_tax - total_discounts)
    order['total_line_items_price'] = "{:.2f}".format(subtotal - total_discounts)  # Added total_line_items_price calculation

    # Update timestamps
    order['updated_at'] = now.isoformat()

    # Save the updated order back to the DB
    orders_table[order_id] = order

    return order

def list_exchanges(order_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Lists all exchanges or exchanges for specific orders.

    Retrieves exchange records from the database. If order_ids is provided, only returns
    exchanges for those specific orders. Otherwise, returns all exchanges. Duplicate
    order IDs are automatically deduplicated.

    Args:
        order_ids (Optional[List[str]]): List of order IDs to filter exchanges by.
            If None, returns all exchanges. Each order ID must be a non-empty string.
            Empty strings, whitespace-only strings, and non-string values will raise
            a ValidationError. Duplicate order IDs are automatically removed.

    Returns:
        List[Dict[str, Any]]: List of exchange objects, each containing:
            id (str): Exchange identifier
            status (str): Exchange status ("COMPLETED")
            order_id (str): Associated order identifier
            name (str): Exchange reference number (e.g., "#EX1001")
            exchange_reason (Optional[str]): Overall exchange reason
            exchange_note (Optional[str]): Additional exchange notes
            price_difference (str): Price difference as decimal string
            created_at (str): ISO 8601 creation timestamp
            updated_at (str): ISO 8601 last update timestamp
            return_line_items (List[Dict[str, Any]]): Items being returned
            new_line_items (List[Dict[str, Any]]): Items being received
            restock_returned_items (bool): Whether returned items were restocked

    Raises:
        ValidationError: If order_ids is provided but:
            - Is not a list
            - Contains non-string values
            - Contains empty strings or whitespace-only strings
    """
    # Validate order_ids if provided
    if order_ids is not None:
        # Check if order_ids is a list
        if not isinstance(order_ids, list):
            raise custom_errors.ValidationError("order_ids must be a list of strings")

        # Validate each order ID and collect valid ones
        valid_order_ids = set()
        for order_id in order_ids:
            # Check type
            if not isinstance(order_id, str):
                raise custom_errors.ValidationError(
                    f"Invalid order ID: {order_id}. All order IDs must be strings."
                )
            
            # Check for empty or whitespace-only strings
            if not order_id.strip():
                raise custom_errors.ValidationError(
                    "Order IDs cannot be empty or whitespace-only strings"
                )
            
            # Add to set for automatic deduplication
            valid_order_ids.add(order_id)

        # Use the deduplicated set for filtering
        order_ids = list(valid_order_ids)

    exchanges = DB.get('exchanges', {})
    
    if not order_ids:
        # Return all exchanges as a list
        return list(exchanges.values())
    
    # Filter exchanges by order IDs
    filtered_exchanges = [
        exchange for exchange in exchanges.values()
        if exchange.get('order_id') in order_ids
    ]
    
    return filtered_exchanges


def list_returns(order_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Lists return objects, optionally filtered by a list of order IDs.

    Args:
        order_ids (Optional[List[str]]): List of order IDs to filter returns. If None or empty, returns all.

    Returns:
        List[Dict[str, Any]]: List of return objects. Each return object contains:
            id (str): Return identifier.
            order_id (str): Associated order identifier.
            status (str): Return status ("OPEN", "REQUESTED", "APPROVED", "REJECTED", "CLOSED").
            name (str): Return reference number (e.g., "#R1001").
            return_line_items (List[Dict[str, Any]]): List of return line items, each with:
                id (str): Return line item identifier.
                line_item_id (str): Original order line item identifier.
                quantity (int): Returned quantity.
                return_reason (Optional[str]): Return reason code. Valid values:
                    "UNKNOWN", "DAMAGED_OR_DEFECTIVE", "NOT_AS_DESCRIBED", 
                    "WRONG_ITEM_SENT", "SIZE_TOO_SMALL", "SIZE_TOO_LARGE", 
                    "STYLE_NOT_AS_EXPECTED", "COLOR_NOT_AS_EXPECTED", 
                    "CHANGED_MIND", "UNWANTED_GIFT", "OTHER"
                return_reason_note (Optional[str]): Additional return notes.
                restock_type (Optional[str]): Restocking behavior ("NO_RESTOCK", "CANCEL", "RETURN").
            created_at (str): ISO 8601 creation timestamp.
            updated_at (str): ISO 8601 last update timestamp.

    Raises:
        ValidationError: If order_ids is provided but:
            - Is not a list
            - Contains non-string values
            - Contains empty strings or whitespace-only strings
    """
    # Validate order_ids if provided
    if order_ids is not None:
        if not isinstance(order_ids, list):
            raise custom_errors.ValidationError("order_ids must be a list of strings")
        valid_order_ids = set()
        for order_id in order_ids:
            if not isinstance(order_id, str):
                raise custom_errors.ValidationError(
                    f"Invalid order ID: {order_id}. All order IDs must be strings."
                )
            if not order_id.strip():
                raise custom_errors.ValidationError(
                    "Order IDs cannot be empty or whitespace-only strings"
                )
            valid_order_ids.add(order_id)
        order_ids = list(valid_order_ids)

    returns = DB.get('returns', {})

    if not order_ids:
        return list(returns.values())

    filtered_returns = [
        ret for ret in returns.values()
        if ret.get('order_id') in order_ids
    ]
    return filtered_returns

def generate_fulfillments_for_order(order_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate fulfillments array for orders that have fulfillment_status 'fulfilled' but no fulfillments.
    
    This function creates realistic fulfillment data based on the order's line items and other properties.
    
    Args:
        order_data (Dict[str, Any]): The order data containing line_items and other order properties
        
    Returns:
        List[Dict[str, Any]]: A list of fulfillment objects that match the Shopify API structure
    """
    if not order_data or not isinstance(order_data, dict):
        return []
    
    # If fulfillments already exist, return them
    if 'fulfillments' in order_data and order_data['fulfillments']:
        return order_data['fulfillments']
    
    # Only generate fulfillments for orders that are fulfilled
    fulfillment_status = order_data.get('fulfillment_status')
    if fulfillment_status not in ['fulfilled', 'partially_fulfilled']:
        return []
    
    line_items = order_data.get('line_items', [])
    if not line_items:
        return []
    
    order_id = order_data.get('id')
    order_name = order_data.get('name', '')
    
    fulfillments = []
    fulfillment_id = 255858046  # Starting ID, will be incremented
    
    # Group line items by fulfillment status
    fulfilled_items = []
    unfulfilled_items = []
    
    for item in line_items:
        if item.get('fulfillment_status') == 'fulfilled' or item.get('current_quantity', 0) == 0:
            fulfilled_items.append(item)
        else:
            unfulfilled_items.append(item)
    
    # Create fulfillment for fulfilled items
    if fulfilled_items:
        fulfillment = {
            "id": fulfillment_id,
            "admin_graphql_api_id": f"gid://shopify/Fulfillment/{fulfillment_id}",
            "created_at": order_data.get('created_at') or datetime.now(timezone.utc).isoformat(),
            "location_id": 655441491,  # Default location ID
            "name": f"{order_name}.0",
            "order_id": order_id,
            "origin_address": {},
            "receipt": {
                "testcase": True,
                "authorization": "123456"
            },
            "service": "manual",
            "shipment_status": "delivered",
            "status": "success",
            "tracking_company": "USPS",
            "tracking_number": "1Z1234512345123456",
            "tracking_numbers": ["1Z1234512345123456"],
            "tracking_url": "https://tools.usps.com/go/TrackConfirmAction_input?qtc_tLabels1=1Z1234512345123456",
            "tracking_urls": ["https://tools.usps.com/go/TrackConfirmAction_input?qtc_tLabels1=1Z1234512345123456"],
            "updated_at": order_data.get('updated_at') or datetime.now(timezone.utc).isoformat(),
            "line_items": fulfilled_items
        }
        fulfillments.append(fulfillment)
        fulfillment_id += 1
    
    # Create partial fulfillment for partially fulfilled orders
    if fulfillment_status == 'partially_fulfilled' and unfulfilled_items:
        partial_fulfillment = {
            "id": fulfillment_id,
            "admin_graphql_api_id": f"gid://shopify/Fulfillment/{fulfillment_id}",
            "created_at": order_data.get('created_at') or datetime.now(timezone.utc).isoformat(),
            "location_id": 655441491,
            "name": f"{order_name}.1",
            "order_id": order_id,
            "origin_address": {},
            "receipt": {
                "testcase": True,
                "authorization": "123456"
            },
            "service": "manual",
            "shipment_status": "in_transit",
            "status": "open",
            "tracking_company": "FedEx",
            "tracking_number": "794698123456",
            "tracking_numbers": ["794698123456"],
            "tracking_url": "https://www.fedex.com/fedextrack/?trknbr=794698123456",
            "tracking_urls": ["https://www.fedex.com/fedextrack/?trknbr=794698123456"],
            "updated_at": order_data.get('updated_at') or datetime.now(timezone.utc).isoformat(),
            "line_items": unfulfilled_items
        }
        fulfillments.append(partial_fulfillment)
    
    return fulfillments


def ensure_order_has_fulfillments(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure that an order has fulfillments if it should have them based on fulfillment_status.
    
    This function checks if an order has fulfillment_status 'fulfilled' or 'partially_fulfilled'
    but no fulfillments array, and generates appropriate fulfillments if needed.
    
    Args:
        order_data (Dict[str, Any]): The order data to check and potentially enhance
        
    Returns:
        Dict[str, Any]: The order data with fulfillments added if needed
    """
    if not order_data or not isinstance(order_data, dict):
        return order_data
    
    # Create a copy to avoid modifying the original
    enhanced_order = order_data.copy()
    
    # Generate fulfillments if needed
    fulfillments = generate_fulfillments_for_order(enhanced_order)
    if fulfillments:
        enhanced_order['fulfillments'] = fulfillments
    
    return enhanced_order


def get_fulfillment_line_item_id(fulfillments: List[Dict[str, Any]], line_item_id: str) -> Optional[str]:
    """Get the fulfillment line item ID for a specific line item.
    
    This function searches through fulfillments to find the fulfillment line item ID
    for a given line item ID, which is needed for creating returns.
    
    Args:
        fulfillments (List[Dict[str, Any]]): List of fulfillment objects
        line_item_id (str): The line item ID to search for
        
    Returns:
        Optional[str]: The fulfillment line item ID if found, None otherwise
    """
    if not fulfillments or not line_item_id:
        return None
    
    for fulfillment in fulfillments:
        line_items = fulfillment.get('line_items', [])
        for item in line_items:
            if str(item.get('id')) == str(line_item_id):
                # In Shopify API, the fulfillment line item ID is typically the line item ID
                # but in some cases it might be a different identifier
                return str(item.get('id'))
    
    return None

