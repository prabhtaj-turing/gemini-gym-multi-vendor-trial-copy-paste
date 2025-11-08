from pydantic import BaseModel, Field, StrictBool, StrictFloat, StrictInt, EmailStr, StringConstraints
from typing import List, Optional, Dict, Union, Annotated
import random
import string

StrictStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

def generate_numeric_id(length: int) -> str:
    return "".join(random.choices(string.digits, k=length))


class Address(BaseModel):
    address1: StrictStr
    address2: Optional[StrictStr] = None
    city: StrictStr
    country: StrictStr
    state: StrictStr
    zip: StrictStr


class Item(BaseModel):
    name: StrictStr
    product_id: StrictStr
    item_id: StrictStr = Field(default_factory=lambda: generate_numeric_id(10))
    price: StrictFloat
    options: Dict[StrictStr, StrictStr]


class Fulfillment(BaseModel):
    tracking_id: List[StrictStr]
    item_ids: List[StrictStr]


class PaymentHistory(BaseModel):
    transaction_type: StrictStr
    amount: StrictFloat
    payment_method_id: StrictStr


class Order(BaseModel):
    order_id: StrictStr = Field(default_factory=lambda: f"#W{generate_numeric_id(7)}")
    user_id: StrictStr
    address: Address
    items: List[Item]
    fulfillments: List[Fulfillment]
    status: StrictStr
    payment_history: List[PaymentHistory]
    # Optional exchange details (present when an exchange has been requested)
    exchange_items: Optional[List[StrictStr]] = None
    exchange_new_items: Optional[List[StrictStr]] = None
    exchange_payment_method_id: Optional[StrictStr] = None
    exchange_price_difference: Optional[StrictFloat] = None
    # Optional return details (present when a return has been requested)
    return_items: Optional[List[StrictStr]] = None
    return_payment_method_id: Optional[StrictStr] = None


class Orders(BaseModel):
    orders: Dict[StrictStr, Order]


class Variant(BaseModel):
    item_id: StrictStr
    options: Dict[StrictStr, StrictStr]
    available: StrictBool
    price: StrictFloat


class Product(BaseModel):
    name: StrictStr
    product_id: StrictStr = Field(default_factory=lambda: generate_numeric_id(10))
    variants: Dict[StrictStr, Variant]


class Products(BaseModel):
    products: Dict[StrictStr, Product]


class UserName(BaseModel):
    first_name: StrictStr
    last_name: StrictStr


class CreditCard(BaseModel):
    id: StrictStr = Field(default_factory=lambda: f"credit_card_{generate_numeric_id(7)}")
    source: StrictStr = "credit_card"
    brand: StrictStr
    last_four: StrictStr


class GiftCard(BaseModel):
    id: StrictStr = Field(default_factory=lambda: f"gift_card_{generate_numeric_id(7)}")
    source: StrictStr = "gift_card"
    balance: StrictInt


class PayPal(BaseModel):
    id: StrictStr = Field(default_factory=lambda: f"paypal_{generate_numeric_id(7)}")
    source: StrictStr = "paypal"


PaymentMethod = Union[CreditCard, GiftCard, PayPal]


class User(BaseModel):
    name: UserName
    address: Address
    email: StrictStr
    payment_methods: Dict[StrictStr, PaymentMethod]
    orders: List[StrictStr]


class Users(BaseModel):
    users: Dict[StrictStr, User]

class RetailDB(BaseModel):
    orders: Orders
    products: Products
    users: Users


class CancelPendingOrderInput(BaseModel):
    order_id: StrictStr = Field(
        description="The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.")
    reason: StrictStr = Field(
        description="The reason for cancellation, which should be either 'no longer needed' or 'ordered by mistake'.")


class CancelPendingOrderOutput(Order):
    cancel_reason: Optional[StrictStr] = None


class ExchangeDeliveredOrderItemsInput(BaseModel):
    order_id: StrictStr = Field(
        description="The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.")
    item_ids: List[StrictStr] = Field(
        description="The item ids to be exchanged, each such as '1008292230'. There could be duplicate items in the list.")
    new_item_ids: List[StrictStr] = Field(
        description="The item ids to be exchanged for, each such as '1008292230'. There could be duplicate items in the list. Each new item id should match the item id in the same position and be of the same product.")
    payment_method_id: StrictStr = Field(
        description="The payment method id to pay or receive refund for the item price difference, such as 'gift_card_0000000' or 'credit_card_0000000'. These can be looked up from the user or order details.")


class ExchangeDeliveredOrderItemsOutput(Order):
    exchange_items: Optional[List[StrictStr]] = None
    exchange_new_items: Optional[List[StrictStr]] = None
    exchange_payment_method_id: Optional[StrictStr] = None
    exchange_price_difference: Optional[StrictFloat] = None


class FindUserIdByEmailInput(BaseModel):
    email: EmailStr = Field(description="The email of the user, such as 'something@example.com'.")


class FindUserIdByNameZipInput(BaseModel):
    first_name: StrictStr = Field(description="The first name of the customer, such as 'John'.")
    last_name: StrictStr = Field(description="The last name of the customer, such as 'Doe'.")
    zip: StrictStr = Field(description="The zip code of the customer, such as '12345'.")


class GetOrderDetailsInput(BaseModel):
    order_id: StrictStr = Field(
        description="The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.")


class GetProductDetailsInput(BaseModel):
    product_id: StrictStr = Field(
        description="The product id, such as '6086499569'. Be careful the product id is different from the item id.")


class GetUserDetailsInput(BaseModel):
    user_id: StrictStr = Field(description="The user id, such as 'sara_doe_496'.")


class ListAllProductTypesOutput(BaseModel):
    products: Dict[StrictStr, StrictStr]


class ModifyPendingOrderAddressInput(BaseModel):
    order_id: StrictStr = Field(
        description="The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.")
    address1: StrictStr = Field(description="The first line of the address, such as '123 Main St'.")
    address2: StrictStr = Field(description="The second line of the address, such as 'Apt 1' or ''.")
    city: StrictStr = Field(description="The city, such as 'San Francisco'.")
    state: StrictStr = Field(description="The state, such as 'CA'.")
    country: StrictStr = Field(description="The country, such as 'USA'.")
    zip: StrictStr = Field(description="The zip code, such as '12345'.")


class ModifyPendingOrderItemsInput(BaseModel):
    order_id: StrictStr = Field(
        description="The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.")
    item_ids: List[StrictStr] = Field(min_length=1,
        description="The item ids to be modified, each such as '1008292230'. There could be duplicate items in the list.")
    new_item_ids: List[StrictStr] = Field(min_length=1,
        description="The item ids to be modified for, each such as '1008292230'. There could be duplicate items in the list. Each new item id should match the item id in the same position and be of the same product.")
    payment_method_id: StrictStr = Field(
        description="The payment method id to pay or receive refund for the item price difference, such as 'gift_card_0000000' or 'credit_card_0000000'. These can be looked up from the user or order details.")


class ModifyPendingOrderPaymentInput(BaseModel):
    order_id: StrictStr = Field(
        description="The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.")
    payment_method_id: StrictStr = Field(
        description="The payment method id to pay or receive refund for the item price difference, such as 'gift_card_0000000' or 'credit_card_0000000'. These can be looked up from the user or order details.")


class ModifyUserAddressInput(BaseModel):
    user_id: StrictStr = Field(description="The user id, such as 'sara_doe_496'.")
    address1: StrictStr = Field(description="The first line of the address, such as '123 Main St'.")
    address2: StrictStr = Field(description="The second line of the address, such as 'Apt 1' or ''.")
    city: StrictStr = Field(description="The city, such as 'San Francisco'.")
    state: StrictStr = Field(description="The state, such as 'CA'.")
    country: StrictStr = Field(description="The country, such as 'USA'.")
    zip: StrictStr = Field(description="The zip code, such as '12345'.")


class ReturnDeliveredOrderItemsInput(BaseModel):
    order_id: StrictStr = Field(
        description="The order id, such as '#W0000000'. Be careful there is a '#' symbol at the beginning of the order id.")
    item_ids: List[StrictStr] = Field(min_length=1,
        description="The item ids to be returned, each such as '1008292230'. There could be duplicate items in the list.")
    payment_method_id: StrictStr = Field(
        description="The payment method id to pay or receive refund for the item price difference, such as 'gift_card_0000000' or 'credit_card_0000000'. These can be looked up from the user or order details.")


class ReturnDeliveredOrderItemsOutput(Order):
    return_items: Optional[List[StrictStr]] = None
    return_payment_method_id: Optional[StrictStr] = None


class CalculateInput(BaseModel):
    expression: StrictStr = Field(
        description="The mathematical expression to calculate, such as '2 + 2'. The expression can contain numbers, operators (+, -, *, /), parentheses, and spaces.")


class ThinkInput(BaseModel):
    thought: StrictStr = Field(description="A thought to think about.")


class TransferToHumanAgentsInput(BaseModel):
    summary: StrictStr = Field(description="A summary of the user's issue.")
