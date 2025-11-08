from typing import Dict, List, Optional
from pydantic import BaseModel, Field, EmailStr, model_validator
from enum import Enum

# ---------------------------
# Enum Types
# ---------------------------

class OrderStatus(str, Enum):
    """Status of an order"""
    PENDING = "pending"
    PROCESSED = "processed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    EXCHANGE_REQUESTED = "exchange requested"
    RETURN_REQUESTED = "return requested"
    PENDING_ITEM_MODIFIED = "pending (item modified)"
    SHIPPED = "shipped"

class PaymentMethodType(str, Enum):
    """Type of payment method"""
    CREDIT_CARD = "credit_card"
    GIFT_CARD = "gift_card"
    PAYPAL = "paypal"

class TransactionType(str, Enum):
    """Type of payment transaction"""
    PAYMENT = "payment"
    REFUND = "refund"

class CreditCardBrand(str, Enum):
    """Credit card brand"""
    VISA = "visa"
    MASTERCARD = "mastercard"

# ---------------------------
# Internal Storage Models
# ---------------------------

class Address(BaseModel):
    """
    Internal storage model for addresses.
    
    Represents a shipping or billing address.
    """
    address1: str = Field(
        ...,
        description="The first line of the address.",
        min_length=1
    )
    address2: str = Field(
        ...,
        description="The second line of the address (apartment, suite, etc.).",
        min_length=1
    )
    city: str = Field(
        ...,
        description="The city of the address.",
        min_length=1
    )
    country: str = Field(
        ...,
        description="The country of the address.",
        min_length=1
    )
    state: str = Field(
        ...,
        description="The state or province of the address.",
        min_length=1
    )
    zip: str = Field(
        ...,
        description="The postal or zip code of the address.",
        min_length=1
    )

class PaymentMethod(BaseModel):
    """
    Internal storage model for payment methods.
    
    Represents a user's payment method (credit card, gift card, PayPal).
    """
    id: str = Field(
        ...,
        description="The payment method ID (e.g., 'credit_card_7815826').",
        min_length=1
    )
    source: PaymentMethodType = Field(
        ...,
        description="The type of payment method."
    )
    brand: Optional[CreditCardBrand] = Field(
        default=None,
        description="The brand of the credit card."
    )
    last_four: Optional[str] = Field(
        default=None,
        description="The last four digits of the credit card.",
        min_length=4,
        max_length=4
    )
    balance: Optional[int] = Field(
        default=None,
        description="The balance of the gift card in cents.",
        ge=0
    )

    @model_validator(mode='after')
    def validate_payment_method_fields(self):
        """Validate that required fields are present based on payment method source."""
        if self.source == PaymentMethodType.CREDIT_CARD:
            if not self.brand:
                raise ValueError("brand is required for credit_card payment methods")
            if not self.last_four:
                raise ValueError("last_four is required for credit_card payment methods")
            if self.balance is not None:
                raise ValueError("balance should not be set for credit_card payment methods")
        elif self.source == PaymentMethodType.GIFT_CARD:
            if self.balance is None:
                raise ValueError("balance is required for gift_card payment methods")
            if self.brand is not None:
                raise ValueError("brand should not be set for gift_card payment methods")
            if self.last_four is not None:
                raise ValueError("last_four should not be set for gift_card payment methods")
        elif self.source == PaymentMethodType.PAYPAL:
            if self.brand is not None:
                raise ValueError("brand should not be set for paypal payment methods")
            if self.last_four is not None:
                raise ValueError("last_four should not be set for paypal payment methods")
            if self.balance is not None:
                raise ValueError("balance should not be set for paypal payment methods")
        
        return self

class UserName(BaseModel):
    """
    Internal storage model for user names.
    
    Represents a user's name.
    """
    first_name: str = Field(
        ...,
        description="The first name of the user.",
        min_length=1,
        max_length=100
    )
    last_name: str = Field(
        ...,
        description="The last name of the user.",
        min_length=1,
        max_length=100
    )

class User(BaseModel):
    """
    Internal storage model for users.
    
    Represents a customer in the retail system.
    """
    name: UserName = Field(
        ...,
        description="The user's name."
    )
    address: Address = Field(
        ...,
        description="The user's default address."
    )
    email: EmailStr = Field(
        ...,
        description="The email address of the user."
    )
    payment_methods: Dict[str, PaymentMethod] = Field(
        default_factory=dict,
        description="Dictionary of payment methods indexed by their ID."
    )
    orders: List[str] = Field(
        default_factory=list,
        description="List of order IDs associated with this user."
    )

class ProductVariant(BaseModel):
    """
    Internal storage model for product variants.
    
    Represents a specific variant of a product with its options and pricing.
    """
    item_id: str = Field(
        ...,
        description="The item ID for this variant.",
        min_length=1
    )
    options: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary of options for this variant (size, color, etc.)."
    )
    available: bool = Field(
        default=True,
        description="Whether this variant is currently available for purchase."
    )
    price: float = Field(
        ...,
        description="The price of this variant.",
        ge=0
    )

class Product(BaseModel):
    """
    Internal storage model for products.
    
    Represents a product in the retail catalog.
    """
    name: str = Field(
        ...,
        description="The name of the product.",
        min_length=1,
        max_length=200
    )
    product_id: str = Field(
        ...,
        description="The product ID used in the system.",
        min_length=1
    )
    variants: Dict[str, ProductVariant] = Field(
        default_factory=dict,
        description="Dictionary of variants indexed by their item ID."
    )

class OrderItem(BaseModel):
    """
    Internal storage model for order items.
    
    Represents an item within an order.
    """
    name: str = Field(
        ...,
        description="The name of the item.",
        min_length=1
    )
    product_id: str = Field(
        ...,
        description="The product ID this item belongs to.",
        min_length=1
    )
    item_id: str = Field(
        ...,
        description="The specific item ID for this order item.",
        min_length=1
    )
    price: float = Field(
        ...,
        description="The price of this item at the time of order.",
        ge=0
    )
    options: Dict[str, str] = Field(
        default_factory=dict,
        description="The options selected for this item."
    )

class Fulfillment(BaseModel):
    """
    Internal storage model for order fulfillments.
    
    Represents the fulfillment/shipping information for an order.
    """
    tracking_id: List[str] = Field(
        default_factory=list,
        description="List of tracking IDs for this fulfillment."
    )
    item_ids: List[str] = Field(
        default_factory=list,
        description="List of item IDs included in this fulfillment."
    )

class PaymentTransaction(BaseModel):
    """
    Internal storage model for payment transactions.
    
    Represents a payment transaction for an order.
    """
    transaction_type: TransactionType = Field(
        ...,
        description="The type of transaction (payment, refund)."
    )
    amount: float = Field(
        ...,
        description="The amount of the transaction.",
        ge=0
    )
    payment_method_id: str = Field(
        ...,
        description="The payment method ID used for this transaction.",
        min_length=1
    )

class Order(BaseModel):
    """
    Internal storage model for orders.
    
    Represents a customer order in the retail system.
    """
    order_id: str = Field(
        ...,
        description="The order ID used in the system (e.g., '#W1234567').",
        min_length=1
    )
    user_id: str = Field(
        ...,
        description="The user ID who placed this order.",
        min_length=1
    )
    address: Address = Field(
        ...,
        description="The shipping address for this order."
    )
    items: List[OrderItem] = Field(
        default_factory=list,
        description="List of items in this order."
    )
    fulfillments: List[Fulfillment] = Field(
        default_factory=list,
        description="List of fulfillments for this order."
    )
    status: OrderStatus = Field(
        ...,
        description="The current status of this order."
    )
    payment_history: List[PaymentTransaction] = Field(
        default_factory=list,
        description="List of payment transactions for this order."
    )

# ---------------------------
# Root Database Model
# ---------------------------

class RetailDB(BaseModel):
    """
    Root model that validates the entire retail database structure.
    
    This model ensures all data in the database conforms to the defined schemas
    for orders, products, and users.
    """
    orders: Dict[str, Order] = Field(
        default_factory=dict,
        description="Dictionary of orders indexed by their order ID."
    )
    products: Dict[str, Product] = Field(
        default_factory=dict,
        description="Dictionary of products indexed by their product ID."
    )
    users: Dict[str, User] = Field(
        default_factory=dict,
        description="Dictionary of users indexed by their user ID."
    )

    class Config:
        str_strip_whitespace = True