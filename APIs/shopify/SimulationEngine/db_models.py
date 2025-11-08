from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, EmailStr, model_validator
from enum import Enum
from datetime import datetime

# ---------------------------
# Enum Types
# ---------------------------

class FinancialStatus(str, Enum):
    """Financial status of an order"""
    PAID = "paid"
    PARTIALLY_REFUNDED = "partially_refunded"
    VOIDED = "voided"
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PARTIALLY_PAID = "partially_paid"
    REFUNDED = "refunded"
    UNPAID = "unpaid"

class FulfillmentStatus(str, Enum):
    """Fulfillment status of an order"""
    FULFILLED = "fulfilled"
    OPEN = "open"
    CANCELLED = "cancelled"
    PARTIALLY_FULFILLED = "partially_fulfilled"
    UNFULFILLED = "unfulfilled"
    SHIPPED = "shipped"
    PARTIAL = "partial"
    UNSHIPPED = "unshipped"

class CustomerState(str, Enum):
    """Customer account state"""
    ENABLED = "enabled"
    DISABLED = "disabled"

class ProductStatus(str, Enum):
    """Product status"""
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"

class PublishedScope(str, Enum):
    """Product published scope"""
    WEB = "web"
    GLOBAL = "global"

class PaymentMethodType(str, Enum):
    """Type of payment method"""
    CREDIT_CARD = "credit_card"
    PAYPAL = "paypal"
    GIFT_CARD = "gift_card"

class PaymentMethodBrand(str, Enum):
    """Payment method brand"""
    VISA = "visa"
    MASTERCARD = "mastercard"
    PAYPAL = "paypal"
    UNKNOWN = "unknown"
# ---------------------------
# Internal Storage Models
# ---------------------------

class Address(BaseModel):
    """
    Internal storage model for addresses.
    
    Represents a customer address.
    """
    id: str = Field(
        ...,
        description="The address ID.",
        min_length=1
    )
    customer_id: Optional[str] = Field(
        default=None,
        description="The customer ID this address belongs to.",
        min_length=1
    )
    address1: str = Field(
        ...,
        description="The first line of the address.",
        min_length=1
    )
    address2: Optional[str] = Field(
        default=None,
        description="The second line of the address (apartment, suite, etc.)."
    )
    city: str = Field(
        ...,
        description="The city of the address.",
        min_length=1
    )
    province: str = Field(
        ...,
        description="The province or state of the address.",
        min_length=1
    )
    country: str = Field(
        ...,
        description="The country of the address.",
        min_length=1
    )
    zip: str = Field(
        ...,
        description="The postal or zip code of the address.",
        min_length=1
    )
    phone: Optional[str] = Field(
        default=None,
        description="The phone number for this address."
    )
    first_name: str = Field(
        ...,
        description="The first name for this address.",
        min_length=1
    )
    last_name: str = Field(
        ...,
        description="The last name for this address.",
        min_length=1
    )
    province_code: Optional[str] = Field(
        default=None,
        description="The province or state code.",
        min_length=1
    )
    country_code: str = Field(
        ...,
        description="The country code.",
        min_length=1
    )
    country_name: Optional[str] = Field(
        default=None,
        description="The country name."
    )
    company: Optional[str] = Field(
        default=None,
        description="The company name."
    )
    default: bool = Field(
        default=False,
        description="Whether this is the default address."
    )

class PaymentMethod(BaseModel):
    """
    Internal storage model for payment methods.
    
    Represents a customer's payment method.
    """
    id: str = Field(
        ...,
        description="The payment method ID.",
        min_length=1
    )
    type: PaymentMethodType = Field(
        ...,
        description="The type of payment method."
    )
    gateway: str = Field(
        ...,
        description="The payment gateway used.",
        min_length=1
    )
    last_four: Optional[str] = Field(
        default=None,
        description="The last four digits of the payment method.",
        min_length=4,
        max_length=4
    )
    brand: Optional[PaymentMethodBrand] = Field(
        default=None,
        description="The brand of the payment method."
    )
    is_default: bool = Field(
        default=False,
        description="Whether this is the default payment method."
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the payment method was created."
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the payment method was last updated."
    )

    @model_validator(mode='after')
    def validate_payment_method_fields(self):
        """Validate that required fields are present based on payment method type."""
        if self.type == PaymentMethodType.CREDIT_CARD:
            if not self.last_four:
                raise ValueError("last_four is required for credit_card payment methods")
            if not self.brand:
                raise ValueError("brand is required for credit_card payment methods")
            if self.brand not in [PaymentMethodBrand.VISA, PaymentMethodBrand.MASTERCARD]:
                raise ValueError("brand must be a valid credit card brand for credit_card payment methods")
        elif self.type == PaymentMethodType.PAYPAL:
            if self.last_four is not None:
                raise ValueError("last_four should not be set for paypal payment methods")
            if self.brand != PaymentMethodBrand.PAYPAL:
                raise ValueError("brand must be paypal for paypal payment methods")
        elif self.type == PaymentMethodType.GIFT_CARD:
            if self.last_four is not None:
                raise ValueError("last_four should not be set for gift_card payment methods")
            # Gift cards can have brand (unknown) or be null
        
        return self

class Customer(BaseModel):
    """
    Internal storage model for customers.
    
    Represents a customer in the Shopify system.
    """
    id: str = Field(
        ...,
        description="The customer ID.",
        min_length=1
    )
    email: EmailStr = Field(
        ...,
        description="The customer's email address."
    )
    first_name: str = Field(
        ...,
        description="The customer's first name.",
        min_length=1
    )
    last_name: str = Field(
        ...,
        description="The customer's last name.",
        min_length=1
    )
    orders_count: int = Field(
        default=0,
        description="The number of orders this customer has placed.",
        ge=0
    )
    state: CustomerState = Field(
        ...,
        description="The customer's account state."
    )
    total_spent: str = Field(
        ...,
        description="The total amount spent by this customer.",
        min_length=1
    )
    phone: Optional[str] = Field(
        default=None,
        description="The customer's phone number."
    )
    tags: Optional[str] = Field(
        default=None,
        description="Comma-separated list of customer tags."
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the customer was created."
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the customer was last updated."
    )
    gift_card_balance: str = Field(
        ...,
        description="The customer's gift card balance.",
        min_length=1
    )
    payment_methods: List[PaymentMethod] = Field(
        default_factory=list,
        description="List of payment methods for this customer."
    )
    default_payment_method_id: Optional[str] = Field(
        default=None,
        description="The ID of the default payment method."
    )
    default_address: Optional[Address] = Field(
        default=None,
        description="The customer's default address."
    )
    addresses: List[Address] = Field(
        default_factory=list,
        description="List of addresses for this customer."
    )

class ProductImage(BaseModel):
    """
    Internal storage model for product images.
    
    Represents a product image.
    """
    id: str = Field(
        ...,
        description="The image ID.",
        min_length=1
    )
    product_id: str = Field(
        ...,
        description="The product ID this image belongs to.",
        min_length=1
    )
    position: int = Field(
        ...,
        description="The image position.",
        ge=1
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the image was created."
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the image was last updated."
    )
    alt: Optional[str] = Field(
        default=None,
        description="The alt text for this image."
    )
    width: int = Field(
        ...,
        description="The image width in pixels.",
        ge=1
    )
    height: int = Field(
        ...,
        description="The image height in pixels.",
        ge=1
    )
    src: str = Field(
        ...,
        description="The image source URL.",
        min_length=1
    )
    variant_ids: List[str] = Field(
        default_factory=list,
        description="List of variant IDs associated with this image."
    )

class ProductOption(BaseModel):
    """
    Internal storage model for product options.
    
    Represents a product option (e.g., Size, Color, Material).
    """
    id: str = Field(
        ...,
        description="The option ID.",
        min_length=1
    )
    product_id: str = Field(
        ...,
        description="The product ID this option belongs to.",
        min_length=1
    )
    name: str = Field(
        ...,
        description="The option name.",
        min_length=1
    )
    position: int = Field(
        ...,
        description="The option position.",
        ge=1
    )
    values: List[str] = Field(
        ...,
        description="List of possible values for this option.",
        min_length=1
    )

class ProductVariant(BaseModel):
    """
    Internal storage model for product variants.
    
    Represents a specific variant of a product.
    """
    id: str = Field(
        ...,
        description="The variant ID.",
        min_length=1
    )
    product_id: str = Field(
        ...,
        description="The product ID this variant belongs to.",
        min_length=1
    )
    title: str = Field(
        ...,
        description="The variant title.",
        min_length=1
    )
    price: str = Field(
        ...,
        description="The variant price as a string.",
        min_length=1
    )
    sku: str = Field(
        ...,
        description="The variant SKU.",
        min_length=1
    )
    position: int = Field(
        default=1,
        description="The variant position.",
        ge=1
    )
    inventory_policy: str = Field(
        default="deny",
        description="The inventory policy for this variant."
    )
    compare_at_price: Optional[str] = Field(
        default=None,
        description="The compare at price for this variant."
    )
    fulfillment_service: Optional[str] = Field(
        default=None,
        description="The fulfillment service for this variant."
    )
    inventory_management: Optional[str] = Field(
        default=None,
        description="The inventory management system.",
        min_length=1
    )
    option1: Optional[str] = Field(
        default=None,
        description="The first option value."
    )
    option2: Optional[str] = Field(
        default=None,
        description="The second option value."
    )
    option3: Optional[str] = Field(
        default=None,
        description="The third option value."
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the variant was created."
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the variant was last updated."
    )
    taxable: bool = Field(
        default=True,
        description="Whether this variant is taxable."
    )
    barcode: Optional[str] = Field(
        default=None,
        description="The barcode for this variant."
    )
    grams: int = Field(
        default=0,
        description="The weight of this variant in grams.",
        ge=0
    )
    image_id: Optional[str] = Field(
        default=None,
        description="The image ID for this variant."
    )
    weight: float = Field(
        default=0.0,
        description="The weight of this variant.",
        ge=0
    )
    weight_unit: Optional[str] = Field(
        default=None,
        description="The weight unit for this variant."
    )
    inventory_item_id: Optional[str] = Field(
        default=None,
        description="The inventory item ID for this variant."
    )
    inventory_quantity: int = Field(
        default=0,
        description="The inventory quantity for this variant.",
        ge=0
    )
    old_inventory_quantity: int = Field(
        default=0,
        description="The old inventory quantity for this variant.",
        ge=0
    )
    requires_shipping: bool = Field(
        default=True,
        description="Whether this variant requires shipping."
    )
    admin_graphql_api_id: str = Field(
        ...,
        description="The GraphQL API ID for this variant.",
        min_length=1
    )

class Product(BaseModel):
    """
    Internal storage model for products.
    
    Represents a product in the Shopify catalog.
    """
    id: str = Field(
        ...,
        description="The product ID.",
        min_length=1
    )
    title: str = Field(
        ...,
        description="The product title.",
        min_length=1
    )
    body_html: str = Field(
        ...,
        description="The product description in HTML.",
        min_length=0
    )
    vendor: str = Field(
        ...,
        description="The product vendor.",
        min_length=1
    )
    product_type: str = Field(
        ...,
        description="The product type.",
        min_length=1
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the product was created."
    )
    handle: str = Field(
        ...,
        description="The product handle (URL-friendly identifier).",
        min_length=1
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the product was last updated."
    )
    published_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the product was published."
    )
    template_suffix: Optional[str] = Field(
        default=None,
        description="The template suffix for this product."
    )
    status: ProductStatus = Field(
        ...,
        description="The product status."
    )
    published_scope: Optional[PublishedScope] = Field(
        default=None,
        description="The published scope for this product."
    )
    tags: str = Field(
        ...,
        description="Comma-separated list of product tags.",
        min_length=0
    )
    admin_graphql_api_id: str = Field(
        ...,
        description="The GraphQL API ID for this product.",
        min_length=1
    )
    variants: List[ProductVariant] = Field(
        default_factory=list,
        description="List of variants for this product."
    )
    options: List[ProductOption] = Field(
        default_factory=list,
        description="List of options for this product."
    )
    images: List[ProductImage] = Field(
        default_factory=list,
        description="List of product images."
    )
    image: Optional[ProductImage] = Field(
        default=None,
        description="The main product image."
    )

class OrderAddress(BaseModel):
    """
    Internal storage model for order addresses.
    
    Represents a simplified address object embedded in orders.
    """
    address1: str = Field(
        ...,
        description="The first line of the address.",
        min_length=1
    )
    city: str = Field(
        ...,
        description="The city of the address.",
        min_length=1
    )
    province_code: Optional[str] = Field(
        default=None,
        description="The province or state code."
    )
    country_code: Optional[str] = Field(
        default=None,
        description="The country code."
    )
    zip: str = Field(
        ...,
        description="The postal or zip code of the address.",
        min_length=1
    )
    first_name: Optional[str] = Field(
        default=None,
        description="The first name for this address."
    )
    last_name: Optional[str] = Field(
        default=None,
        description="The last name for this address."
    )

class RefundLineItem(BaseModel):
    """
    Internal storage model for refund line items.
    
    Represents a line item within a refund.
    """
    line_item_id: str = Field(
        ...,
        description="The line item ID being refunded.",
        min_length=1
    )
    quantity: int = Field(
        ...,
        description="The quantity being refunded.",
        ge=1
    )
    restock_type: str = Field(
        ...,
        description="The restock type for this refund.",
        min_length=1
    )
    location_id: str = Field(
        ...,
        description="The location ID for this refund.",
        min_length=1
    )
    price: str = Field(
        ...,
        description="The price of this refund line item.",
        min_length=1
    )
    subtotal: str = Field(
        ...,
        description="The subtotal of this refund line item.",
        min_length=1
    )
    total_tax: str = Field(
        ...,
        description="The total tax for this refund line item.",
        min_length=1
    )

class RefundTransaction(BaseModel):
    """
    Internal storage model for refund transactions.
    
    Represents a transaction within a refund.
    """
    id: str = Field(
        ...,
        description="The transaction ID.",
        min_length=1
    )
    admin_graphql_api_id: str = Field(
        ...,
        description="The GraphQL API ID for this transaction.",
        min_length=1
    )
    amount: str = Field(
        ...,
        description="The transaction amount.",
        min_length=1
    )
    kind: str = Field(
        ...,
        description="The transaction kind.",
        min_length=1
    )
    gateway: str = Field(
        ...,
        description="The payment gateway.",
        min_length=1
    )
    status: str = Field(
        ...,
        description="The transaction status.",
        min_length=1
    )
    parent_id: str = Field(
        ...,
        description="The parent transaction ID.",
        min_length=1
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the transaction was created."
    )
    currency: str = Field(
        ...,
        description="The transaction currency.",
        min_length=3,
        max_length=3
    )
    original_payment_method_id: str = Field(
        ...,
        description="The original payment method ID.",
        min_length=1
    )

class OrderTransaction(BaseModel):
    """
    Internal storage model for order transactions.
    
    Represents a transaction for an order.
    """
    id: str = Field(
        ...,
        description="The transaction ID.",
        min_length=1
    )
    admin_graphql_api_id: Optional[str] = Field(
        default=None,
        description="The GraphQL API ID for this transaction."
    )
    amount: str = Field(
        ...,
        description="The transaction amount.",
        min_length=1
    )
    kind: str = Field(
        ...,
        description="The transaction kind.",
        min_length=1
    )
    gateway: str = Field(
        ...,
        description="The payment gateway.",
        min_length=1
    )
    status: str = Field(
        ...,
        description="The transaction status.",
        min_length=1
    )
    message: Optional[str] = Field(
        default=None,
        description="The transaction message."
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the transaction was created."
    )
    test: bool = Field(
        default=False,
        description="Whether this is a test transaction."
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="The parent transaction ID."
    )
    processed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the transaction was processed."
    )
    device_id: Optional[str] = Field(
        default=None,
        description="The device ID for this transaction."
    )
    error_code: Optional[str] = Field(
        default=None,
        description="The error code for this transaction."
    )
    source_name: Optional[str] = Field(
        default=None,
        description="The source name for this transaction."
    )
    currency: str = Field(
        ...,
        description="The transaction currency.",
        min_length=3,
        max_length=3
    )
    authorization: Optional[str] = Field(
        default=None,
        description="The authorization for this transaction."
    )
    payment_details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The payment details for this transaction."
    )
    receipt: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The receipt for this transaction."
    )
    target_payment_method_id: Optional[str] = Field(
        default=None,
        description="The target payment method ID."
    )
    original_payment_method_id: str = Field(
        ...,
        description="The original payment method ID.",
        min_length=1
    )

class Refund(BaseModel):
    """
    Internal storage model for refunds.
    
    Represents a refund for an order.
    """
    id: str = Field(
        ...,
        description="The refund ID.",
        min_length=1
    )
    admin_graphql_api_id: str = Field(
        ...,
        description="The GraphQL API ID for this refund.",
        min_length=1
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the refund was created."
    )
    note: Optional[str] = Field(
        default=None,
        description="The refund note."
    )
    order_id: str = Field(
        ...,
        description="The order ID this refund belongs to.",
        min_length=1
    )
    currency: str = Field(
        ...,
        description="The refund currency.",
        min_length=3,
        max_length=3
    )
    shipping: Dict[str, str] = Field(
        default_factory=dict,
        description="The shipping information for this refund."
    )
    refund_line_items: List[RefundLineItem] = Field(
        default_factory=list,
        description="List of line items for this refund."
    )
    transactions: List[RefundTransaction] = Field(
        default_factory=list,
        description="List of transactions for this refund."
    )

class OrderCustomer(BaseModel):
    """
    Internal storage model for order customers.
    
    Represents a simplified customer object embedded in orders.
    """
    id: str = Field(
        ...,
        description="The customer ID.",
        min_length=1
    )
    email: EmailStr = Field(
        ...,
        description="The customer's email address."
    )
    first_name: Optional[str] = Field(
        default=None,
        description="The customer's first name."
    )
    last_name: Optional[str] = Field(
        default=None,
        description="The customer's last name."
    )
    orders_count: Optional[int] = Field(
        default=None,
        description="The number of orders this customer has placed.",
        ge=0
    )
    total_spent: Optional[str] = Field(
        default=None,
        description="The total amount spent by this customer."
    )
    gift_card_balance: Optional[str] = Field(
        default=None,
        description="The customer's gift card balance."
    )
    default_address: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The customer's default address."
    )

class OrderLineItem(BaseModel):
    """
    Internal storage model for order line items.
    
    Represents an item within an order.
    """
    id: str = Field(
        ...,
        description="The line item ID.",
        min_length=1
    )
    variant_id: Optional[str] = Field(
        default=None,
        description="The variant ID for this line item."
    )
    title: str = Field(
        ...,
        description="The line item title.",
        min_length=1
    )
    quantity: int = Field(
        ...,
        description="The quantity of this line item.",
        ge=1
    )
    sku: Optional[str] = Field(
        default=None,
        description="The SKU for this line item."
    )
    variant_title: Optional[str] = Field(
        default=None,
        description="The variant title for this line item."
    )
    vendor: Optional[str] = Field(
        default=None,
        description="The vendor for this line item."
    )
    fulfillment_service: str = Field(
        default="manual",
        description="The fulfillment service for this line item."
    )
    product_id: str = Field(
        ...,
        description="The product ID for this line item.",
        min_length=1
    )
    requires_shipping: bool = Field(
        default=True,
        description="Whether this line item requires shipping."
    )
    taxable: bool = Field(
        default=True,
        description="Whether this line item is taxable."
    )
    gift_card: bool = Field(
        default=False,
        description="Whether this line item is a gift card."
    )
    name: Optional[str] = Field(
        default=None,
        description="The full name of this line item."
    )
    variant_inventory_management: Optional[str] = Field(
        default=None,
        description="The inventory management for this line item."
    )
    properties: List[Dict[str, str]] = Field(
        default_factory=list,
        description="List of properties for this line item."
    )
    product_exists: bool = Field(
        default=True,
        description="Whether the product for this line item exists."
    )
    fulfillable_quantity: int = Field(
        default=0,
        description="The fulfillable quantity for this line item.",
        ge=0
    )
    grams: int = Field(
        default=0,
        description="The weight of this line item in grams.",
        ge=0
    )
    price: str = Field(
        ...,
        description="The price of this line item as a string.",
        min_length=1
    )
    total_discount: str = Field(
        default="0.00",
        description="The total discount for this line item.",
        min_length=1
    )
    fulfillment_status: Optional[str] = Field(
        default=None,
        description="The fulfillment status for this line item."
    )
    price_set: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The price set for this line item."
    )
    total_discount_set: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The total discount set for this line item."
    )
    discount_allocations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of discount allocations for this line item."
    )
    duties: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of duties for this line item."
    )
    admin_graphql_api_id: Optional[str] = Field(
        default=None,
        description="The GraphQL API ID for this line item."
    )
    tax_lines: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of tax lines for this line item."
    )
    origin_location: Optional[Dict[str, Any]] = Field(
        default=None,
        description="The origin location for this line item."
    )

class Order(BaseModel):
    """
    Internal storage model for orders.
    
    Represents an order in the Shopify system.
    """
    id: str = Field(
        ...,
        description="The order ID.",
        min_length=1
    )
    admin_graphql_api_id: str = Field(
        ...,
        description="The GraphQL API ID for this order.",
        min_length=1
    )
    name: str = Field(
        ...,
        description="The order name (e.g., '#1001').",
        min_length=1
    )
    order_number: int = Field(
        ...,
        description="The order number.",
        ge=1
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="The customer's email address."
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the order was created."
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the order was last updated."
    )
    cancelled_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the order was cancelled."
    )
    cancel_reason: Optional[str] = Field(
        default=None,
        description="The reason for cancellation."
    )
    closed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the order was closed."
    )
    currency: str = Field(
        ...,
        description="The currency code for this order.",
        min_length=3,
        max_length=3
    )
    financial_status: FinancialStatus = Field(
        ...,
        description="The financial status of this order."
    )
    fulfillment_status: Optional[FulfillmentStatus] = Field(
        default=None,
        description="The fulfillment status of this order."
    )
    total_price: str = Field(
        ...,
        description="The total price of this order as a string.",
        min_length=1
    )
    subtotal_price: Optional[str] = Field(
        default=None,
        description="The subtotal price of this order as a string."
    )
    total_weight: Optional[int] = Field(
        default=None,
        description="The total weight of this order in grams.",
        ge=0
    )
    total_tax: Optional[str] = Field(
        default=None,
        description="The total tax for this order as a string."
    )
    total_discounts: Optional[str] = Field(
        default=None,
        description="The total discounts for this order as a string."
    )
    tags: Optional[str] = Field(
        default=None,
        description="Comma-separated list of order tags."
    )
    note: Optional[str] = Field(
        default=None,
        description="The order note."
    )
    token: Optional[str] = Field(
        default=None,
        description="The order token."
    )
    customer: Optional[OrderCustomer] = Field(
        default=None,
        description="The customer information for this order."
    )
    billing_address: Optional[OrderAddress] = Field(
        default=None,
        description="The billing address for this order."
    )
    shipping_address: Optional[OrderAddress] = Field(
        default=None,
        description="The shipping address for this order."
    )
    transactions: List[OrderTransaction] = Field(
        default_factory=list,
        description="List of transactions for this order."
    )
    refunds: List[Refund] = Field(
        default_factory=list,
        description="List of refunds for this order."
    )
    shipping_lines: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of shipping lines for this order."
    )
    tax_lines: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of tax lines for this order."
    )
    discount_codes: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of discount codes for this order."
    )
    customer_locale: Optional[str] = Field(
        default=None,
        description="The customer locale for this order."
    )
    referring_site: Optional[str] = Field(
        default=None,
        description="The referring site for this order."
    )
    app_id: Optional[str] = Field(
        default=None,
        description="The app ID for this order."
    )
    processed_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the order was processed."
    )
    line_items: List[OrderLineItem] = Field(
        default_factory=list,
        description="List of line items in this order."
    )

class MoneySet(BaseModel):
    """
    Internal storage model for money sets with shop and presentment currencies.
    
    Represents a monetary amount in multiple currencies.
    """
    shop_money: Dict[str, str] = Field(
        ...,
        description="Money in shop currency."
    )
    presentment_money: Dict[str, str] = Field(
        ...,
        description="Money in presentment currency."
    )

class PriceAmount(BaseModel):
    """
    Internal storage model for price amounts.
    
    Represents a price with amount and currency.
    """
    amount: str = Field(
        ...,
        description="The price amount.",
        min_length=1
    )
    currency_code: str = Field(
        ...,
        description="The currency code.",
        min_length=3,
        max_length=3
    )

class CalculatedOrderLineItem(BaseModel):
    """
    Internal storage model for calculated order line items.
    
    Represents a line item in a calculated order.
    """
    id: str = Field(
        ...,
        description="The line item ID.",
        min_length=1
    )
    variant_id: Optional[str] = Field(
        default=None,
        description="The variant ID for this line item."
    )
    title: str = Field(
        ...,
        description="The line item title.",
        min_length=1
    )
    quantity: int = Field(
        ...,
        description="The quantity of this line item.",
        ge=1
    )
    original_price_per_unit: PriceAmount = Field(
        ...,
        description="Original price per unit."
    )
    discounted_price_per_unit: PriceAmount = Field(
        ...,
        description="Discounted price per unit."
    )
    subtotal_price: PriceAmount = Field(
        ...,
        description="Subtotal price for this line item."
    )
    total_discount_amount: PriceAmount = Field(
        ...,
        description="Total discount amount."
    )
    taxable: bool = Field(
        ...,
        description="Whether this line item is taxable."
    )
    tax_lines: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Tax lines for this line item."
    )

class CalculatedOrder(BaseModel):
    """
    Internal storage model for calculated orders.
    
    Represents a calculated order for draft or cart operations.
    """
    id: str = Field(
        ...,
        description="The calculated order ID.",
        min_length=1
    )
    original_order_id: str = Field(
        ...,
        description="The original order ID.",
        min_length=1
    )
    currency_code: str = Field(
        ...,
        description="The currency code for this calculated order.",
        min_length=3,
        max_length=3
    )
    line_items: List[CalculatedOrderLineItem] = Field(
        default_factory=list,
        description="List of line items in the calculated order."
    )
    staged_changes_applied_discounts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Applied discounts from staged changes."
    )
    shipping_lines: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Shipping lines for the calculated order."
    )
    subtotal_price_set: MoneySet = Field(
        ...,
        description="Subtotal price in multiple currencies."
    )
    total_discounts_set: MoneySet = Field(
        ...,
        description="Total discounts in multiple currencies."
    )
    total_tax_set: MoneySet = Field(
        ...,
        description="Total tax in multiple currencies."
    )
    total_price_set: MoneySet = Field(
        ...,
        description="Total price in multiple currencies."
    )
    tax_lines: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Tax lines for the calculated order."
    )
    taxes_included: bool = Field(
        ...,
        description="Whether taxes are included in the price."
    )
    payment_terms: Optional[Any] = Field(
        default=None,
        description="Payment terms for the calculated order."
    )
    added_line_items_count: int = Field(
        ...,
        description="Count of line items added.",
        ge=0
    )
    removed_line_items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of removed line items."
    )
    updated_line_items_count: int = Field(
        ...,
        description="Count of line items updated.",
        ge=0
    )
    status: str = Field(
        ...,
        description="The status of the calculated order.",
        min_length=1
    )

class Collection(BaseModel):
    """
    Internal storage model for product collections.
    
    Represents a collection of products in Shopify.
    """
    id: str = Field(
        ...,
        description="The collection ID.",
        min_length=1
    )
    title: str = Field(
        ...,
        description="The collection title.",
        min_length=1
    )
    body_html: str = Field(
        ...,
        description="The collection description in HTML.",
        min_length=0
    )
    handle: str = Field(
        ...,
        description="The collection handle (URL-friendly identifier).",
        min_length=1
    )
    published_at: datetime = Field(
        ...,
        description="Timestamp when the collection was published."
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the collection was last updated."
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the collection was created."
    )
    sort_order: str = Field(
        ...,
        description="The sort order for products in the collection."
    )
    published: bool = Field(
        ...,
        description="Whether the collection is published."
    )
    collection_type: str = Field(
        ...,
        description="The collection type (manual or automatic)."
    )
    rules: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Rules for automatic collections."
    )
    products: List[str] = Field(
        default_factory=list,
        description="List of product IDs in the collection."
    )
    admin_graphql_api_id: str = Field(
        ...,
        description="The GraphQL API ID for this collection.",
        min_length=1
    )

class DraftOrderCustomer(BaseModel):
    """
    Internal storage model for draft order customers.
    
    Represents customer information in a draft order.
    """
    id: Optional[str] = Field(
        default=None,
        description="The customer ID."
    )
    email: EmailStr = Field(
        ...,
        description="The customer's email address."
    )
    first_name: Optional[str] = Field(
        default=None,
        description="The customer's first name."
    )
    last_name: Optional[str] = Field(
        default=None,
        description="The customer's last name."
    )

class DraftOrderLineItem(BaseModel):
    """
    Internal storage model for draft order line items.
    
    Represents a line item in a draft order.
    """
    variant_id: str = Field(
        ...,
        description="The variant ID for this line item.",
        min_length=1
    )
    product_id: str = Field(
        ...,
        description="The product ID for this line item.",
        min_length=1
    )
    title: str = Field(
        ...,
        description="The line item title.",
        min_length=1
    )
    quantity: int = Field(
        ...,
        description="The quantity of this line item.",
        ge=1
    )
    price: str = Field(
        ...,
        description="The price of this line item.",
        min_length=1
    )

class DraftOrder(BaseModel):
    """
    Internal storage model for draft orders.
    
    Represents a draft order awaiting completion.
    """
    id: str = Field(
        ...,
        description="The draft order ID.",
        min_length=1
    )
    name: Optional[str] = Field(
        default=None,
        description="The draft order name."
    )
    email: EmailStr = Field(
        ...,
        description="The customer's email address."
    )
    currency: str = Field(
        ...,
        description="The currency code for this draft order.",
        min_length=3,
        max_length=3
    )
    invoice_sent_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the invoice was sent."
    )
    invoice_url: Optional[str] = Field(
        default=None,
        description="The invoice URL."
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the draft order was created."
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the draft order was last updated."
    )
    status: str = Field(
        ...,
        description="The draft order status.",
        min_length=1
    )
    note: Optional[str] = Field(
        default=None,
        description="Note for the draft order."
    )
    order_id: Optional[str] = Field(
        default=None,
        description="The order ID if converted from draft."
    )
    customer: DraftOrderCustomer = Field(
        ...,
        description="Customer information for the draft order."
    )
    shipping_address: Optional[Dict[str, str]] = Field(
        default=None,
        description="Shipping address for the draft order."
    )
    line_items: List[DraftOrderLineItem] = Field(
        default_factory=list,
        description="List of line items in the draft order."
    )
    shipping_line: Optional[Dict[str, str]] = Field(
        default=None,
        description="Shipping line information."
    )
    applied_discount: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Applied discount information."
    )
    total_price: str = Field(
        ...,
        description="The total price of the draft order.",
        min_length=1
    )
    subtotal_price: Optional[str] = Field(
        default=None,
        description="The subtotal price of the draft order."
    )
    total_tax: Optional[str] = Field(
        default=None,
        description="The total tax for the draft order."
    )
    admin_graphql_api_id: str = Field(
        ...,
        description="The GraphQL API ID for this draft order.",
        min_length=1
    )

class ExchangeReturnLineItem(BaseModel):
    """
    Internal storage model for exchange return line items.
    
    Represents a line item being returned in an exchange.
    """
    id: str = Field(
        ...,
        description="The line item ID.",
        min_length=1
    )
    original_line_item_id: str = Field(
        ...,
        description="The original line item ID.",
        min_length=1
    )
    quantity: int = Field(
        ...,
        description="The quantity being returned.",
        ge=1
    )
    exchange_reason: Optional[str] = Field(
        default=None,
        description="The reason for the exchange."
    )
    exchange_reason_note: Optional[str] = Field(
        default=None,
        description="Additional notes about the exchange reason."
    )
    restock_type: str = Field(
        ...,
        description="The restock type for this item.",
        min_length=1
    )

class ExchangeNewLineItem(BaseModel):
    """
    Internal storage model for exchange new line items.
    
    Represents a new line item being provided in an exchange.
    """
    id: str = Field(
        ...,
        description="The line item ID.",
        min_length=1
    )
    variant_id: str = Field(
        ...,
        description="The variant ID for the new item.",
        min_length=1
    )
    product_id: str = Field(
        ...,
        description="The product ID for the new item.",
        min_length=1
    )
    title: str = Field(
        ...,
        description="The title of the new item.",
        min_length=1
    )
    quantity: int = Field(
        ...,
        description="The quantity of the new item.",
        ge=1
    )
    price: str = Field(
        ...,
        description="The price of the new item.",
        min_length=1
    )
    sku: Optional[str] = Field(
        default=None,
        description="The SKU of the new item."
    )
    vendor: Optional[str] = Field(
        default=None,
        description="The vendor of the new item."
    )

class Exchange(BaseModel):
    """
    Internal storage model for order exchanges.
    
    Represents an exchange of items from an order.
    """
    id: str = Field(
        ...,
        description="The exchange ID.",
        min_length=1
    )
    status: str = Field(
        ...,
        description="The exchange status.",
        min_length=1
    )
    order_id: str = Field(
        ...,
        description="The original order ID.",
        min_length=1
    )
    name: str = Field(
        ...,
        description="The exchange name.",
        min_length=1
    )
    exchange_reason: str = Field(
        ...,
        description="The reason for the exchange.",
        min_length=1
    )
    exchange_note: Optional[str] = Field(
        default=None,
        description="Additional notes for the exchange."
    )
    price_difference: str = Field(
        ...,
        description="The price difference for the exchange.",
        min_length=1
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the exchange was created."
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the exchange was last updated."
    )
    return_line_items: List[ExchangeReturnLineItem] = Field(
        default_factory=list,
        description="List of line items being returned."
    )
    new_line_items: List[ExchangeNewLineItem] = Field(
        default_factory=list,
        description="List of new line items being provided."
    )
    restock_returned_items: bool = Field(
        ...,
        description="Whether returned items should be restocked."
    )

class PresentmentPrice(BaseModel):
    """
    Internal storage model for presentment prices.
    
    Represents multi-currency pricing information.
    """
    amount: str = Field(
        ...,
        description="The price amount.",
        min_length=1
    )
    currency_code: str = Field(
        ...,
        description="The currency code.",
        min_length=3,
        max_length=3
    )

class ReturnLineItem(BaseModel):
    """
    Internal storage model for return line items.
    
    Represents a line item being returned.
    """
    id: str = Field(
        ...,
        description="The return line item ID.",
        min_length=1
    )
    line_item_id: str = Field(
        ...,
        description="The original line item ID.",
        min_length=1
    )
    return_reason: str = Field(
        ...,
        description="The reason for the return.",
        min_length=1
    )
    return_reason_note: Optional[str] = Field(
        default=None,
        description="Additional notes about the return reason."
    )
    restock_type: str = Field(
        ...,
        description="The restock type for this item.",
        min_length=1
    )
    quantity: int = Field(
        ...,
        description="The quantity being returned.",
        ge=1
    )

class Return(BaseModel):
    """
    Internal storage model for order returns.
    
    Represents a return of items from an order.
    """
    id: str = Field(
        ...,
        description="The return ID.",
        min_length=1
    )
    status: str = Field(
        ...,
        description="The return status.",
        min_length=1
    )
    order_id: str = Field(
        ...,
        description="The original order ID.",
        min_length=1
    )
    name: str = Field(
        ...,
        description="The return name.",
        min_length=1
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the return was created."
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when the return was last updated."
    )
    return_line_items: List[ReturnLineItem] = Field(
        default_factory=list,
        description="List of line items being returned."
    )

# ---------------------------
# Root Database Model
# ---------------------------

class ShopifyDB(BaseModel):
    """
    Root model that validates the entire Shopify database structure.
    
    This model ensures all data in the database conforms to the defined schemas
    for customers, products, and orders.
    """
    customers: Dict[str, Customer] = Field(
        default_factory=dict,
        description="Dictionary of customers indexed by their ID."
    )
    products: Dict[str, Product] = Field(
        default_factory=dict,
        description="Dictionary of products indexed by their ID."
    )
    orders: Dict[str, Order] = Field(
        default_factory=dict,
        description="Dictionary of orders indexed by their ID."
    )
    calculated_orders: Optional[Dict[str, CalculatedOrder]] = Field(
        default_factory=dict,
        description="Dictionary of calculated orders for draft or cart operations."
    )
    collections: Optional[Dict[str, Collection]] = Field(
        default_factory=dict,
        description="Dictionary of product collections."
    )
    draft_orders: Optional[Dict[str, DraftOrder]] = Field(
        default_factory=dict,
        description="Dictionary of draft orders."
    )
    exchanges: Optional[Dict[str, Exchange]] = Field(
        default_factory=dict,
        description="Dictionary of order exchanges."
    )
    presentment_prices: Optional[Dict[str, Dict[str, PresentmentPrice]]] = Field(
        default_factory=dict,
        description="Dictionary of presentment prices for multi-currency support (product_id -> currency -> price)."
    )
    returns: Optional[Dict[str, Return]] = Field(
        default_factory=dict,
        description="Dictionary of order returns."
    )

    class Config:
        str_strip_whitespace = True
