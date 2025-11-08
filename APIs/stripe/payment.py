from common_utils.tool_spec_decorator import tool_spec
from typing import Dict, Any, Optional, List
from stripe.SimulationEngine import utils
from stripe.SimulationEngine.custom_errors import ResourceNotFoundError, InvalidRequestError
from stripe.SimulationEngine.db import DB
from stripe.SimulationEngine.models import PaymentIntent


@tool_spec(
    spec={
        'name': 'create_payment_link',
        'description': """ Creates a payment link in Stripe.
        
        This function creates a payment link in Stripe. It takes the ID of the price
        to create the payment link for and the quantity of the product to include
        in the payment link. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'price': {
                    'type': 'string',
                    'description': 'The ID of the price to create the payment link for.'
                },
                'quantity': {
                    'type': 'integer',
                    'description': 'The quantity of the product to include.'
                }
            },
            'required': [
                'price',
                'quantity'
            ]
        }
    }
)
def create_payment_link(price: str, quantity: int) -> Dict[str, Any]:
    """Creates a payment link in Stripe.

    This function creates a payment link in Stripe. It takes the ID of the price
    to create the payment link for and the quantity of the product to include
    in the payment link.

    Args:
        price (str): The ID of the price to create the payment link for.
        quantity (int): The quantity of the product to include.

    Returns:
        Dict[str, Any]: A dictionary representing the Stripe payment link object that was created. It contains the following keys:
            id (str): Unique identifier for the payment link.
            object (str): String representing the object's type, typically "payment_link".
            active (bool): Whether the payment link is active and can be used to create new Checkout Sessions.
            livemode (bool): Indicates if the object exists in live mode or test mode.
            metadata (Optional[Dict[str, str]]): A set of key-value pairs that you can attach to an object. It can be useful for storing additional information about the object in a structured format.
            line_items (Dict[str, Any]): A Stripe list object containing the line items for this payment link. This dictionary contains the following keys:
                object (str): String representing the list object's type, typically "list".
                data (List[Dict[str, Any]]): A list of line item objects. Each dictionary in the list represents a line item and contains the following keys:
                    id (str): Unique identifier for the line item.
                    price (Dict[str, Any]): The price object used for this line item. This dictionary contains the following keys:
                        id (str): Unique identifier of the price.
                        product (str): Identifier of the product associated with this price.
                    quantity (int): The quantity of the product for this line item.
                has_more (bool): A flag indicating if there are more line items to be fetched for this list.
            after_completion (Dict[str, Any]): Configuration for behavior after the purchase is complete. This dictionary contains the following keys:
                type (str): The type of an after-completion behavior (e.g., 'redirect', 'hosted_confirmation').
                redirect (Optional[Dict[str, Any]]): If `type` is 'redirect', this hash contains information about the redirect configuration (e.g., a success message).

    Raises:
        InvalidRequestError: If the price ID is invalid, quantity is invalid, or other parameters are malformed.
        ResourceNotFoundError: If the specified price ID does not exist.
    """

    # 1. Input validation
    if not isinstance(price, str):
        raise InvalidRequestError("Price ID must be a string.")
    if not price:  # Check for empty string price ID
        raise InvalidRequestError("Price ID cannot be empty.")

    if not isinstance(quantity, int):
        raise InvalidRequestError("Quantity must be an integer.")
    if quantity <= 0:
        raise InvalidRequestError("Quantity must be greater than 0.")

    # 2. Fetch Price object from DB
    # DB['prices'] is expected to be a Dict[str, Dict[str, Any]] representing Price objects
    price_obj = utils._get_object_by_id(DB, price, "prices")
    if not price_obj:
        raise ResourceNotFoundError(f"No such price: '{price}'")

    # 3. Check if price is active
    # The Price schema indicates 'active' is a boolean field.
    if not price_obj.get('active'):
        raise InvalidRequestError(f"Price '{price}' is not active and cannot be used to create a payment link.")

    # 4. Get product ID from price object
    # The Price schema indicates 'product' is a required string field (Product ID).
    product_id = price_obj.get('product')
    if not product_id:
        # This implies data inconsistency, as 'product' is required by the Price schema.
        raise InvalidRequestError(f"Price '{price}' is malformed: missing product ID.")

    # 5. Construct the PaymentLink object (as a dictionary)
    payment_link_id = utils.generate_id("pl")
    line_item_id = utils.generate_id("sli")  # Simulated Line Item ID

    payment_link_data: Dict[str, Any] = {
        "id": payment_link_id,
        "object": "payment_link",
        "active": True,
        "livemode": False,
        "metadata": None,  # Conforms to Optional[Dict[str, str]] = None in schema
        "line_items": {
            "object": "list",
            "data": [
                {
                    "id": line_item_id,
                    "price": {
                        "id": price,  # The input price ID
                        "product": product_id  # Fetched product ID
                    },
                    "quantity": quantity
                }
            ],
            "has_more": False,
        },
        "after_completion": {
            "type": "hosted_confirmation",
            "redirect": None  # As 'type' is 'hosted_confirmation', 'redirect' is None
        }
    }

    # 6. Store in DB
    # DB['payment_links'] is expected to be Dict[str, Dict[str, Any]]
    # The StripeDB model initializes 'payment_links' as an empty dict if not present.
    DB['payment_links'][payment_link_id] = payment_link_data

    # 7. Return the created object
    return payment_link_data


@tool_spec(
    spec={
        'name': 'create_payment_intent',
        'description': """ Creates a PaymentIntent object in Stripe.
        
        This function creates a PaymentIntent object in Stripe. A PaymentIntent guides you through the process of collecting a payment from your customer. You can reference the PaymentIntent later to see the history of payment attempts for a particular session. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'amount': {
                    'type': 'integer',
                    'description': 'Amount intended to be collected by this PaymentIntent. A positive integer representing how much to charge in the smallest currency unit (e.g., 100 cents to charge $1.00). The minimum amount is $0.50 US or equivalent in charge currency.'
                },
                'currency': {
                    'type': 'string',
                    'description': 'Three-letter ISO currency code, in lowercase. Must be a supported currency.'
                },
                'customer': {
                    'type': 'string',
                    'description': 'ID of the Customer this PaymentIntent belongs to, if one exists. Defaults to None.'
                },
                'payment_method_types': {
                    'type': 'array',
                    'description': 'The list of payment method types (e.g., card) that this PaymentIntent is allowed to use. Defaults to None.',
                    'items': {
                        'type': 'string'
                    }
                },
                'capture_method': {
                    'type': 'string',
                    'description': 'Controls when the funds will be captured from the customer\'s account. Must be one of: "automatic", "automatic_async", "manual". Defaults to "automatic_async".'
                },
                'metadata': {
                    'type': 'object',
                    'description': 'Set of key-value pairs that you can attach to an object. This can be useful for storing additional information about the object in a structured format.',
                    'properties': {},
                    'required': []
                }
            },
            'required': [
                'amount',
                'currency'
            ]
        }
    }
)
def create_payment_intent(
    amount: int, 
    currency: str, 
    customer: Optional[str] = None,
    payment_method_types: Optional[List[str]] = None,
    capture_method: str = "automatic_async",
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Creates a PaymentIntent object in Stripe.

    This function creates a PaymentIntent object in Stripe. A PaymentIntent guides you through the process of collecting a payment from your customer. You can reference the PaymentIntent later to see the history of payment attempts for a particular session.

    Args:
        amount (int): Amount intended to be collected by this PaymentIntent. A positive integer representing how much to charge in the smallest currency unit (e.g., 100 cents to charge $1.00). The minimum amount is $0.50 US or equivalent in charge currency.
        currency (str): Three-letter ISO currency code, in lowercase. Must be a supported currency.
        customer (Optional[str]): ID of the Customer this PaymentIntent belongs to, if one exists. Defaults to None.
        payment_method_types (Optional[List[str]]): The list of payment method types (e.g., card) that this PaymentIntent is allowed to use. Defaults to None.
        capture_method (str): Controls when the funds will be captured from the customer's account. Must be one of: "automatic", "automatic_async", "manual". Defaults to "automatic_async".
        metadata (Optional[Dict[str, str]]): Set of key-value pairs that you can attach to an object. This can be useful for storing additional information about the object in a structured format.

    Returns:
        Dict[str, Any]: A dictionary representing the Stripe PaymentIntent object that was created. It contains the following keys:
            id (str): Unique identifier for the payment intent.
            object (str): String representing the object's type, typically "payment_intent".
            amount (int): Amount intended to be collected by this PaymentIntent.
            currency (str): Three-letter ISO currency code.
            customer (Optional[str]): ID of the customer this PaymentIntent belongs to, if one exists.
            status (str): Status of this PaymentIntent (e.g., "requires_payment_method").
            created (int): Unix timestamp of when the payment intent was created.
            livemode (bool): Indicates if the object exists in live mode or test mode.
            metadata (Optional[Dict[str, str]]): A set of key-value pairs associated with the payment intent.
            payment_method_types (List[str]): The list of payment method types that this PaymentIntent is allowed to use.
            capture_method (str): Controls when the funds will be captured from the customer's account.
            amount_capturable (int): Amount that can be captured from this PaymentIntent.
            amount_received (int): Amount that this PaymentIntent collects.
            client_secret (str): The client secret of this PaymentIntent. Used for client-side retrieval using a publishable key.

    Raises:
        InvalidRequestError: If the amount is invalid, currency is not supported, or other parameters are malformed.
        ResourceNotFoundError: If the specified customer ID does not exist (when provided).
    """

    # 1. Input validation
    if not isinstance(amount, int):
        raise InvalidRequestError("Amount must be an integer.")
    if amount < 50:  # Minimum amount is $0.50 US
        raise InvalidRequestError("Amount must be at least 50 cents (or equivalent in charge currency).")
    if amount > 99999999:  # Maximum 8 digits
        raise InvalidRequestError("Amount value supports up to eight digits.")

    if not isinstance(currency, str):
        raise InvalidRequestError("Currency must be a string.")
    if not currency or len(currency) != 3:
        raise InvalidRequestError("Currency must be a three-letter ISO currency code.")
    
    # Set default payment method types
    if payment_method_types is None:
        payment_method_types = ["card"]
    
    if not isinstance(payment_method_types, list):
        raise InvalidRequestError("Payment method types must be a list.")
    if not payment_method_types:
        raise InvalidRequestError("At least one payment method type must be specified.")
    
    # Validate that all elements in the list are strings
    for i, method_type in enumerate(payment_method_types):
        if not isinstance(method_type, str):
            raise InvalidRequestError(f"Payment method type at index {i} must be a string, got {type(method_type).__name__}.")
        if not method_type.strip():
            raise InvalidRequestError(f"Payment method type at index {i} cannot be empty.")

    # Validate customer if provided
    if customer is not None:
        if not isinstance(customer, str):
            raise InvalidRequestError("Customer ID must be a string.")
        if customer not in DB['customers']:
            raise ResourceNotFoundError(f"No such customer: '{customer}'")

    # Validate capture method
    valid_capture_methods = ["automatic", "automatic_async", "manual"]
    if capture_method not in valid_capture_methods:
        raise InvalidRequestError(f"Capture method must be one of: {', '.join(valid_capture_methods)}")

    # 2. Generate PaymentIntent ID and client secret
    payment_intent_id = utils.generate_id("pi")
    client_secret = f"{payment_intent_id}_secret_{utils.generate_id('')}"

    # 3. Get current timestamp
    import time
    created_timestamp = int(time.time())

    # 4. Construct the PaymentIntent object with only fields defined in PaymentIntent model
    payment_intent_data: Dict[str, Any] = {
        "id": payment_intent_id,
        "object": "payment_intent",
        "amount": amount,
        "currency": currency.lower(),
        "customer": customer,
        "status": "requires_payment_method",
        "created": created_timestamp,
        "livemode": False,
        "metadata": metadata or {}
    }

    # 5. Validate the payment intent data using Pydantic model
    try:
        validated_payment_intent = PaymentIntent(**payment_intent_data)
        # Convert back to dict for storage
        validated_data = validated_payment_intent.model_dump()
    except Exception as e:
        raise InvalidRequestError(f"Payment intent data validation failed: {str(e)}")

    # 6. Store in DB
    # DB['payment_intents'] is expected to be Dict[str, Dict[str, Any]]
    # The StripeDB model initializes 'payment_intents' as an empty dict if not present.
    DB['payment_intents'][payment_intent_id] = validated_data

    # 7. Return the created object
    return validated_data


@tool_spec(
    spec={
        'name': 'list_payment_intents',
        'description': """ This tool will list payment intents in Stripe.
        
        This function lists payment intents in Stripe. It takes an optional customer ID
        to list payment intents for a specific customer, and an optional limit to specify
        the number of payment intents to return. """,
        'parameters': {
            'type': 'object',
            'properties': {
                'customer': {
                    'type': 'string',
                    'description': 'The ID of the customer to list payment intents for. Defaults to None.'
                },
                'limit': {
                    'type': 'integer',
                    'description': 'A limit on the number of objects to be returned. Limit can range between 1 and 100. Defaults to None.'
                },
                'starting_after': {
                    'type': 'string',
                    'description': 'A cursor for use in pagination. starting_after is an object ID that defines your place in the list. Defaults to None.'
                },
                'ending_before': {
                    'type': 'string',
                    'description': 'A cursor for use in pagination. ending_before is an object ID that defines your place in the list. Defaults to None.'
                }
            },
            'required': []
        }
    }
)
def list_payment_intents(customer: Optional[str] = None, limit: Optional[int] = None, starting_after: Optional[str] = None, ending_before: Optional[str] = None) -> Dict[str, Any]:
    """This tool will list payment intents in Stripe.

    This function lists payment intents in Stripe. It takes an optional customer ID
    to list payment intents for a specific customer, and an optional limit to specify
    the number of payment intents to return.

    Args:
        customer (Optional[str]): The ID of the customer to list payment intents for. Defaults to None.
        limit (Optional[int]): A limit on the number of objects to be returned. Limit can range between 1 and 100. Defaults to None.
        starting_after (Optional[str]): A cursor for use in pagination. starting_after is an object ID that defines your place in the list. Defaults to None.
        ending_before (Optional[str]): A cursor for use in pagination. ending_before is an object ID that defines your place in the list. Defaults to None.

    Returns:
        Dict[str, Any]: A dictionary representing the API response for listing payment intents. This dictionary contains the following keys:
            object (str): String representing the object's type, typically "list".
            data (List[Dict[str, Any]]): A list of payment intent objects. Each payment intent dictionary in this list includes the following fields:
                id (str): Unique identifier for the payment intent.
                object (str): String representing the object's type, typically "payment_intent".
                amount (int): Amount intended to be collected, in cents.
                currency (str): Three-letter ISO currency code.
                customer (Optional[str]): ID of the customer this PaymentIntent belongs to, if one exists.
                status (str): Status of this PaymentIntent (e.g., "requires_payment_method", "succeeded").
                created (int): Unix timestamp of when the payment intent was created.
                livemode (bool): Indicates if the object exists in live mode or test mode.
                metadata (Optional[Dict[str, str]]): A set of key-value pairs associated with the payment intent.
            has_more (bool): True if there are more payment intents to retrieve, false otherwise.

    Raises:
        InvalidRequestError: If filter parameters are invalid, or if both starting_after and ending_before are provided.
        ResourceNotFoundError: If the specified customer ID does not exist (when provided), or if the cursor ID does not exist.
    """
    # Validate input parameters
    if limit is not None:
        if not isinstance(limit, int):
            raise InvalidRequestError("Limit must be an integer.")
        if limit < 1:
            raise InvalidRequestError("Limit must be at least 1.")
        if limit > 100:
            raise InvalidRequestError("Limit cannot exceed 100.")
    else:
        limit = 10

    # Validate that starting_after and ending_before are not both provided
    if starting_after is not None and ending_before is not None:
        raise InvalidRequestError("Cannot provide both starting_after and ending_before.")

    # Validate starting_after if provided
    if starting_after is not None:
        if not isinstance(starting_after, str):
            raise InvalidRequestError("starting_after must be a string.")
        if starting_after not in DB['payment_intents']:
            raise ResourceNotFoundError(f"No such payment intent: '{starting_after}'")

    # Validate ending_before if provided
    if ending_before is not None:
        if not isinstance(ending_before, str):
            raise InvalidRequestError("ending_before must be a string.")
        if ending_before not in DB['payment_intents']:
            raise ResourceNotFoundError(f"No such payment intent: '{ending_before}'")

    # Validate customer if provided
    if customer is not None:
        if not isinstance(customer, str):
            raise InvalidRequestError("Customer ID must be a string.")
        if customer not in DB['customers']:
            raise ResourceNotFoundError("Customer not found.")

    # Get payment intents from DB
    all_intents = utils._get_objects(DB, "payment_intents")

    # Get filtered intents as a list and sort in a single step
    intents = sorted(
        [intent for intent in all_intents.values()
         if customer is None or intent.get('customer') == customer],
        key=lambda x: x.get('created', 0),
        reverse=True
    )

    # Apply cursor-based pagination
    if starting_after is not None:
        # Find the index of the starting_after object
        cursor_index = None
        for i, intent in enumerate(intents):
            if intent['id'] == starting_after:
                cursor_index = i
                break
        
        if cursor_index is not None:
            # Return objects after the cursor
            intents = intents[cursor_index + 1:]
    
    elif ending_before is not None:
        # Find the index of the ending_before object
        cursor_index = None
        for i, intent in enumerate(intents):
            if intent['id'] == ending_before:
                cursor_index = i
                break
        
        if cursor_index is not None:
            # Return objects before the cursor
            intents = intents[:cursor_index]
    
    has_more = limit < len(intents)
    intents = intents[:limit]

    # Return formatted response
    return {
        "object": "list",
        "data": intents,
        "has_more": has_more
    }
