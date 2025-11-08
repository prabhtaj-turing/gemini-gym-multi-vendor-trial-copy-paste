from decimal import Decimal, InvalidOperation
from typing import List, Optional, Any, Dict, Union, Literal
from pydantic import BaseModel, Field, HttpUrl, validator, field_validator, model_validator, EmailStr
from datetime import datetime
from enum import Enum


# --- Common Helper Models ---

class PageInfo(BaseModel):
    next_page_token: Optional[str] = None
    previous_page_token: Optional[str] = None


class ShopifyAddressModel(BaseModel):
    id: Optional[str] = None
    customer_id: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    name: Optional[str] = None
    province_code: Optional[str] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    company: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    default: Optional[bool] = False


# --- Customer Related Models ---

class CustomerDefaultAddress(ShopifyAddressModel):
    pass


class CustomerPaymentMethodModel(BaseModel):
    """Model for customer payment methods to support cross-payment method refunds."""
    id: str
    type: str  # "credit_card", "paypal", "bank_account", "gift_card"
    gateway: str  # "stripe", "paypal", "manual", "shopify_payments"
    last_four: Optional[str] = None
    brand: Optional[str] = None  # "visa", "mastercard", "paypal"
    is_default: bool = False
    created_at: datetime
    updated_at: datetime

    class Config:
        extra = 'forbid'
        strict = True


class ShopifyCustomerModel(BaseModel):
    id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    orders_count: int = 0
    state: Optional[str] = None
    total_spent: Optional[str] = "0.00"
    phone: Optional[str] = None
    tags: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    gift_card_balance: Optional[str] = "0.00"
    default_address: Optional[CustomerDefaultAddress] = None
    addresses: Optional[List[ShopifyAddressModel]] = Field(default_factory=list)
    payment_methods: Optional[List[CustomerPaymentMethodModel]] = Field(default_factory=list)
    default_payment_method_id: Optional[str] = None


# --- Product Related Models ---

class MoneyModel(BaseModel):
    amount: str = Field(description="The price amount as a decimal string")
    currency_code: str = Field(description="ISO 4217 currency code (e.g., 'USD', 'EUR')")


class PresentmentPriceModel(BaseModel):
    price: MoneyModel = Field(description="Price object containing amount and currency code")


class ProductImageModel(BaseModel):
    id: str  # Changed from int to str to match general ID format, assuming GIDs or string IDs are used.
    product_id: str  # Changed from int to str
    position: int
    created_at: datetime
    updated_at: datetime
    alt: Optional[str] = None
    width: int
    height: int
    src: HttpUrl
    variant_ids: List[str] = Field(default_factory=list)  # Assuming variant IDs are strings


class ProductOptionModel(BaseModel):
    id: str  # Changed from int to str
    product_id: str  # Changed from int to str
    name: str
    position: int
    values: List[str] = Field(default_factory=list)


class ProductVariantModel(BaseModel):
    id: str  # Changed from int to str
    product_id: str  # Changed from int to str
    title: str
    price: str
    sku: Optional[str] = None
    position: int
    inventory_policy: Optional[str] = 'deny'
    compare_at_price: Optional[str] = None
    fulfillment_service: Optional[str] = None
    inventory_management: Optional[str] = None
    option1: Optional[str] = None
    option2: Optional[str] = None
    option3: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    taxable: bool = True
    barcode: Optional[str] = None
    grams: int = 0
    image_id: Optional[str] = None  # Assuming image IDs are strings
    weight: float = 0.0
    weight_unit: str = 'kg'
    inventory_item_id: Optional[str] = None  # Assuming inventory item IDs are strings
    inventory_quantity: int = 0
    old_inventory_quantity: Optional[int] = 0
    requires_shipping: bool = True
    admin_graphql_api_id: Optional[str] = None


class ShopifyProductModel(BaseModel):
    id: str  # Changed from int to str
    title: str
    body_html: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    created_at: datetime
    handle: str
    updated_at: datetime
    published_at: Optional[datetime] = None
    template_suffix: Optional[str] = None
    status: str
    published_scope: Optional[str] = 'web'
    tags: Optional[str] = None
    admin_graphql_api_id: Optional[str] = None
    variants: List[ProductVariantModel] = Field(default_factory=list)
    options: List[ProductOptionModel] = Field(default_factory=list)
    images: List[ProductImageModel] = Field(default_factory=list)
    image: Optional[ProductImageModel] = None


class ProductVariantCreateModel(BaseModel):
    title: str
    price: str
    sku: Optional[str] = None
    position: Optional[int] = 1
    inventory_policy: Optional[str] = 'deny'
    compare_at_price: Optional[str] = None
    fulfillment_service: Optional[str] = 'manual'
    inventory_management: Optional[str] = 'shopify'
    option1: Optional[str] = None
    option2: Optional[str] = None
    option3: Optional[str] = None
    taxable: bool = True
    barcode: Optional[str] = None
    grams: int = 0
    image_id: Optional[str] = None
    weight: Optional[float] = 0.0
    weight_unit: Optional[str] = 'kg'
    inventory_quantity: int = 0
    requires_shipping: bool = True


class ProductCreateModel(BaseModel):
    title: str
    body_html: Optional[str] = ""
    vendor: str
    product_type: str
    status: Literal['active', 'archived', 'draft'] = 'active'
    tags: Optional[str] = ""
    variants: Optional[List[ProductVariantCreateModel]] = None
    options: Optional[List[ProductOptionModel]] = None
    images: Optional[List[ProductImageModel]] = None


class ProductVariantUpdateModel(BaseModel):
    id: str  # Required to identify the variant
    title: Optional[str] = None
    price: Optional[str] = None
    sku: Optional[str] = None
    position: Optional[int] = None
    inventory_policy: Optional[str] = None
    compare_at_price: Optional[str] = None
    fulfillment_service: Optional[str] = None
    inventory_management: Optional[str] = None
    option1: Optional[str] = None
    option2: Optional[str] = None
    option3: Optional[str] = None
    taxable: Optional[bool] = None
    barcode: Optional[str] = None
    grams: Optional[int] = None
    image_id: Optional[str] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = None
    inventory_quantity: Optional[int] = None
    old_inventory_quantity: Optional[int] = None
    requires_shipping: Optional[bool] = None


class ProductImageUpdateModel(BaseModel):
    id: str  # Required to identify the image
    position: Optional[int] = None
    alt: Optional[str] = None
    src: Optional[HttpUrl] = None
    variant_ids: Optional[List[str]] = None


class ProductOptionUpdateModel(BaseModel):
    id: str  # Required to identify the option
    name: Optional[str] = None
    position: Optional[int] = None
    values: Optional[List[str]] = None


class ProductUpdateModel(BaseModel):
    id: str  # Required to identify product
    title: Optional[str] = None
    body_html: Optional[str] = None
    vendor: Optional[str] = None
    product_type: Optional[str] = None
    status: Optional[Literal['active', 'archived', 'draft']] = None
    tags: Optional[str] = None
    handle: Optional[str] = None
    variants: Optional[List[Union[ProductVariantUpdateModel, ProductVariantCreateModel]]] = None
    options: Optional[List[Union[ProductOptionUpdateModel, ProductOptionModel]]] = None
    images: Optional[List[Union[ProductImageUpdateModel, ProductImageModel]]] = None


# --- Order Related Models ---

class OrderLineItemModel(BaseModel):
    id: Optional[str] = None
    variant_id: Optional[str] = None
    product_id: Optional[str] = None
    title: str
    quantity: int
    sku: Optional[str] = None
    variant_title: Optional[str] = None
    vendor: Optional[str] = None
    fulfillment_service: Optional[str] = None
    requires_shipping: Optional[bool] = True
    taxable: Optional[bool] = True
    gift_card: Optional[bool] = False
    name: Optional[str] = None
    properties: Optional[List[Dict[str, str]]] = Field(default_factory=list)
    price: str
    total_discount: Optional[str] = "0.00"
    fulfillment_status: Optional[str] = None
    grams: Optional[int] = 0
    admin_graphql_api_id: Optional[str] = None
    discount_allocations: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    duties: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    origin_location: Optional[Dict[str, Any]] = None
    price_set: Optional[Dict[str, Any]] = None
    product_exists: Optional[bool] = True
    tax_lines: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    total_discount_set: Optional[Dict[str, Any]] = None
    variant_inventory_management: Optional[str] = None
    fulfillable_quantity: Optional[int] = None  # Often an int


class OrderCustomerInfo(BaseModel):
    id: str
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    orders_count: Optional[int] = None
    total_spent: Optional[str] = None
    gift_card_balance: Optional[str] = None
    default_address: Optional[
        CustomerDefaultAddress] = None  # Changed from ShopifyAddressModel to CustomerDefaultAddress for consistency


class ShippingLineModel(BaseModel):
    id: Optional[str] = None
    title: str
    price: str
    code: Optional[str] = None
    source: Optional[str] = 'shopify'
    phone: Optional[str] = None
    requested_fulfillment_service_id: Optional[str] = None
    delivery_category: Optional[str] = None
    carrier_identifier: Optional[str] = None
    price_set: Optional[Dict[str, Any]] = None
    discounted_price: Optional[str] = None
    discounted_price_set: Optional[Dict[str, Any]] = None
    discount_allocations: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    tax_lines: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


class TaxLineModel(BaseModel):
    price: str
    rate: float
    title: str
    channel_liable: Optional[bool] = None
    price_set: Optional[Dict[str, Any]] = None


class DiscountCodeModel(BaseModel):
    code: str
    amount: str
    type: str


class TransactionReceiptModel(BaseModel):  # Added for better typing of receipt
    transaction_id: Optional[str] = None
    card_type: Optional[str] = None
    card_last_four: Optional[str] = None
    # Add other gateway-specific receipt fields if known and consistent


class ShopifyTransactionModel(BaseModel):
    id: Optional[str] = None
    admin_graphql_api_id: Optional[str] = None
    amount: str
    kind: str
    gateway: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    created_at: Optional[datetime] = None
    test: Optional[bool] = False
    parent_id: Optional[str] = None  # Assuming parent transaction ID is also string
    processed_at: Optional[datetime] = None
    device_id: Optional[str] = None
    error_code: Optional[str] = None
    source_name: Optional[str] = 'web'
    currency: Optional[str] = None
    authorization: Optional[str] = None
    payment_details: Optional[Dict[str, Any]] = None
    receipt: Optional[TransactionReceiptModel] = None  # Changed from Dict[str, Any]
    target_payment_method_id: Optional[str] = None  # NEW - for cross-payment refunds
    original_payment_method_id: Optional[str] = None  # NEW - track original payment method

    class Config:
        extra = 'forbid'
        strict = True


class RefundShippingDetail(BaseModel):
    amount: Optional[str] = None
    full_refund: Optional[bool] = None
    tax: Optional[str] = None
    maximum_refundable: Optional[str] = None

    class Config:
        extra = 'forbid'
        strict = True


class RefundDutyItemModel(BaseModel):
    duty_id: str  # Assuming string ID
    amount: Optional[str] = None
    refund_type: Optional[str] = Field(None, enum=["FULL", "PROPORTIONAL"])  #

    class Config:
        extra = 'forbid'
        strict = True


class RefundLineItemModel(BaseModel):
    id: Optional[str] = None  # ID of the refund line item itself
    line_item_id: str  # ID of the original order line item
    quantity: int
    restock_type: str  # 'no_restock', 'cancel', 'return', 'legacy_restock'
    location_id: Optional[str] = None  # Assuming string ID
    price: Optional[str] = None
    subtotal: Optional[str] = None
    total_tax: Optional[str] = None

    # line_item: Optional[OrderLineItemModel] = None # This could cause circular dependencies if not careful, usually populated by tool

    class Config:
        extra = 'forbid'
        strict = True


class ShopifyRefundModel(BaseModel):
    id: Optional[str] = None
    admin_graphql_api_id: Optional[str] = None
    created_at: Optional[datetime] = None
    note: Optional[str] = None
    order_id: Optional[str] = None
    processed_at: Optional[datetime] = None
    restock: Optional[bool] = None
    user_id: Optional[str] = None
    currency: Optional[str] = None
    shipping: Optional[RefundShippingDetail] = None
    refund_line_items: List[RefundLineItemModel] = Field(default_factory=list)
    transactions: List[ShopifyTransactionModel] = Field(default_factory=list)
    duties: List[RefundDutyItemModel] = Field(default_factory=list)
    order_adjustments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    class Config:
        extra = 'forbid'
        strict = True

    @model_validator(mode='before')
    @classmethod
    def check_for_at_least_one_refund_item(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Check if any of the main refund components are present and not empty
            if (not data.get('shipping') and
                    not data.get('duties') and
                    not data.get('refund_line_items')):

                # If not, check for a valid refund transaction
                is_transaction_refund = False
                if data.get('transactions'):
                    for trans in data.get('transactions'):
                        # 'trans' can be a dict here because of mode='before'
                        if trans.get('kind') == 'refund' and Decimal(trans.get('amount', '0')) > 0:
                            is_transaction_refund = True
                            break

                # If no valid refund component is found, raise an error
                if not is_transaction_refund:
                    raise ValueError(
                        'A refund must contain at least one of: `shipping`, `duties`, `refund_line_items`, or a positive refund `transaction`.')
        return data


class ShopifyOrderModel(BaseModel):
    id: str
    admin_graphql_api_id: Optional[str] = None
    name: Optional[str] = None
    order_number: int
    email: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None
    closed_at: Optional[datetime] = None
    currency: str
    financial_status: Optional[str] = None
    fulfillment_status: Optional[str] = None
    total_price: str
    subtotal_price: Optional[str] = None
    total_weight: Optional[int] = None
    total_tax: Optional[str] = None
    total_discounts: Optional[str] = None
    tags: Optional[str] = ""
    note: Optional[str] = None
    token: Optional[str] = None
    line_items: List[OrderLineItemModel] = Field(default_factory=list)
    customer: Optional[OrderCustomerInfo] = None
    billing_address: Optional[ShopifyAddressModel] = None
    shipping_address: Optional[ShopifyAddressModel] = None
    refunds: List[ShopifyRefundModel] = Field(default_factory=list)
    transactions: List[ShopifyTransactionModel] = Field(default_factory=list)
    shipping_lines: Optional[List[ShippingLineModel]] = Field(default_factory=list)
    tax_lines: Optional[List[TaxLineModel]] = Field(default_factory=list)
    discount_codes: Optional[List[DiscountCodeModel]] = Field(default_factory=list)
    customer_locale: Optional[str] = None
    referring_site: Optional[str] = None
    app_id: Optional[str] = None
    current_total_duties_set: Optional[Dict[str, Any]] = None
    original_total_duties_set: Optional[Dict[str, Any]] = None
    inventory_behaviour: Optional[str] = Field("bypass", json_schema_extra={
        "enum": ["bypass", "decrement_ignoring_policy", "decrement_obeying_policy"]})
    send_receipt: Optional[bool] = False
    send_fulfillment_receipt: Optional[bool] = False
    send_cancellation_receipt: Optional[bool] = False
    processed_at: Optional[datetime] = None
    status: Optional[str] = 'open'


# --- Draft Order Related Models ---

class DraftOrderAppliedDiscountModel(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    value: str
    value_type: Literal['fixed_amount', 'percentage']  # FIX: Enforces correct values
    amount: Optional[str] = None


class DraftOrderShippingLineModel(BaseModel):
    title: str
    price: str
    custom: Optional[bool] = True


class DraftOrderCustomerModel(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class OrderEditCustomAttributeInputModel(
    BaseModel):  # For Order Edits, also usable for DraftOrder line items if structure is identical
    key: str
    value: str


class DraftOrderLineItemModel(BaseModel):
    id: str
    variant_id: str
    product_id: str
    title: str
    quantity: int
    price: Optional[str] = None
    grams: Optional[int] = None
    sku: Optional[str] = None
    vendor: Optional[str] = None
    taxable: Optional[bool] = True
    requires_shipping: Optional[bool] = True
    gift_card: Optional[bool] = False
    applied_discount: Optional[DraftOrderAppliedDiscountModel] = None
    custom_attributes: Optional[List[OrderEditCustomAttributeInputModel]] = Field(default_factory=list)  # Reused model
    fulfillment_service: Optional[str] = None


class DraftOrderInvoiceModel(BaseModel):
    to: Optional[str] = None
    from_address: Optional[str] = None  # Changed from from_email to match API return
    subject: Optional[str] = None
    custom_message: Optional[str] = None
    bcc: Optional[List[str]] = Field(default_factory=list)


class ShopifyDraftOrderModel(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    currency: Optional[str] = None
    invoice_sent_at: Optional[datetime] = None
    invoice_url: Optional[HttpUrl] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    tax_exempt: Optional[bool] = False
    taxes_included: Optional[bool] = False
    total_price: Optional[str] = None
    subtotal_price: Optional[str] = None
    total_tax: Optional[str] = None
    payment_terms: Optional[Any] = None
    status: Optional[str] = 'open'
    note: Optional[str] = None
    tags: Optional[str] = None
    customer: Optional[DraftOrderCustomerModel] = None
    shipping_address: Optional[ShopifyAddressModel] = None
    billing_address: Optional[ShopifyAddressModel] = None
    line_items: List[DraftOrderLineItemModel] = Field(default_factory=list)
    shipping_line: Optional[DraftOrderShippingLineModel] = None
    applied_discount: Optional[DraftOrderAppliedDiscountModel] = None
    order_id: Optional[str] = None
    admin_graphql_api_id: Optional[str] = None


# --- Return Related Models (GraphQL based) ---
class ReturnReasonEnum(str, Enum):
    UNKNOWN = "UNKNOWN"
    DAMAGED_OR_DEFECTIVE = "DAMAGED_OR_DEFECTIVE"
    NOT_AS_DESCRIBED = "NOT_AS_DESCRIBED"
    WRONG_ITEM_SENT = "WRONG_ITEM_SENT"
    SIZE_TOO_SMALL = "SIZE_TOO_SMALL"
    SIZE_TOO_LARGE = "SIZE_TOO_LARGE"
    STYLE_NOT_AS_EXPECTED = "STYLE_NOT_AS_EXPECTED"
    COLOR_NOT_AS_EXPECTED = "COLOR_NOT_AS_EXPECTED"
    CHANGED_MIND = "CHANGED_MIND"
    UNWANTED_GIFT = "UNWANTED_GIFT"
    OTHER = "OTHER"


class ReturnLineItemInputModel(BaseModel):  # Input for creating a return
    fulfillment_line_item_id: str  # GID of the FulfillmentLineItem
    quantity: int
    return_reason: Optional[ReturnReasonEnum] = None
    return_reason_note: Optional[str] = None


# Output model for a return line item, used within ShopifyReturnModel
class ReturnLineItemResponseModel(BaseModel):  # Renamed to avoid clash with input, more descriptive for output
    id: str  # GID of the ReturnLineItem itself
    line_item_id: str  # GID of the original OrderLineItem
    quantity: int
    return_reason: Optional[ReturnReasonEnum] = None
    return_reason_note: Optional[str] = None
    restock_type: Optional[str] = Field(None, json_schema_extra={
        "enum": ["NO_RESTOCK", "CANCEL", "RETURN"]})  # Added based on typical return data


class ReturnInputModel(BaseModel):  # Input for creating a return
    order_id: str  # GID of the Order
    return_line_items: List[ReturnLineItemInputModel] = Field(min_length=1, description="Must contain at least one return line item")


class ShopifyReturnModel(BaseModel):
    id: str  # GID of the Return
    status: str
    order_id: str  # GID of the associated order
    name: str  # e.g. "RMA-1001" or "#R1001"
    created_at: datetime
    updated_at: datetime
    return_line_items: List[ReturnLineItemResponseModel] = Field(default_factory=list)  # Using the response model


# --- Order Edit Related Models (GraphQL based) ---

class CalculatedLineItemModel(BaseModel):
    id: str  # GID
    variant_id: Optional[str] = None  # GID of ProductVariant
    quantity: int
    title: Optional[str] = None
    variant_title: Optional[str] = None  # Added from schema
    custom_attributes: Optional[List[OrderEditCustomAttributeInputModel]] = None  # Added
    original_price_per_unit: Optional[Dict[str, Any]] = None
    discounted_price_per_unit: Optional[Dict[str, Any]] = None
    subtotal_price: Optional[Dict[str, Any]] = None
    total_discount_amount: Optional[Dict[str, Any]] = None
    taxable: Optional[bool] = None
    tax_lines: Optional[List[Dict[str, Any]]] = None


class ShopifyCalculatedOrderModel(BaseModel):
    id: str  # GID
    original_order_id: str  # GID of the original Order
    line_items: Optional[List[CalculatedLineItemModel]] = Field(default_factory=list)
    # Fields from schema for shopify_order_edit_set_quantity and add_variant returns:
    calculated_subtotal_price: Optional[str] = None  # From schema (string)
    calculated_total_price: Optional[str] = None  # From schema (string)
    calculated_total_tax: Optional[str] = None  # From schema (string)
    # Other fields can be added if needed from a full CalculatedOrder object
    currency_code: Optional[str] = None
    staged_changes_applied_discounts: Optional[List[Dict[str, Any]]] = None
    shipping_lines: Optional[List[Dict[str, Any]]] = None
    subtotal_price_set: Optional[Dict[str, Any]] = None
    total_discounts_set: Optional[Dict[str, Any]] = None
    total_tax_set: Optional[Dict[str, Any]] = None
    total_price_set: Optional[Dict[str, Any]] = None
    # tax_lines field directly under calculated order (distinct from line_item tax_lines)
    # taxes_included, payment_terms, added_line_items_count, removed_line_items, updated_line_items_count, status


# --- Exchange Related Models ---

class ExchangeLineItemInputModel(BaseModel):
    """Input model for line items in an exchange request."""
    fulfillment_line_item_id: str  # ID of the original order line item to exchange
    quantity: int
    exchange_reason: Optional[str] = None
    exchange_reason_note: Optional[str] = None
    
    @field_validator('quantity')
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Exchange quantity must be greater than 0.')
        return v


class ExchangeNewLineItemInputModel(BaseModel):
    """Input model for new line items in an exchange request."""
    variant_id: str
    product_id: str
    quantity: int
    title: Optional[str] = None
    price: Optional[str] = None
    
    @field_validator('quantity')
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('New item quantity must be greater than 0.')
        return v


class ExchangeInputModel(BaseModel):
    """Input model for creating an exchange."""
    order_id: str
    return_line_items: List[ExchangeLineItemInputModel] = Field(min_length=1, description="Items to be returned")
    new_line_items: List[ExchangeNewLineItemInputModel] = Field(min_length=1, description="New items to be received")
    exchange_reason: Optional[str] = None
    exchange_note: Optional[str] = None
    restock_returned_items: bool = True


class ExchangeLineItemResponseModel(BaseModel):
    """Response model for exchange line items."""
    id: str
    original_line_item_id: str
    quantity: int
    exchange_reason: Optional[str] = None
    exchange_reason_note: Optional[str] = None
    restock_type: Optional[str] = "RETURN"


class ExchangeNewLineItemResponseModel(BaseModel):
    """Response model for new line items in an exchange."""
    id: str
    variant_id: str
    product_id: str
    title: str
    quantity: int
    price: str
    sku: Optional[str] = None
    vendor: Optional[str] = None


class ShopifyExchangeModel(BaseModel):
    """Model for a Shopify exchange."""
    id: str
    status: str  # "PENDING", "APPROVED", "COMPLETED", "CANCELLED"
    order_id: str
    name: str  # e.g., "EX-001" or "#EX1001"
    exchange_reason: Optional[str] = None
    exchange_note: Optional[str] = None
    price_difference: str  # Positive if customer owes money, negative if refund due
    created_at: datetime
    updated_at: datetime
    return_line_items: List[ExchangeLineItemResponseModel] = Field(default_factory=list)
    new_line_items: List[ExchangeNewLineItemResponseModel] = Field(default_factory=list)
    restock_returned_items: bool = True


# --- Main Database Model ---

class ShopifyCollectionModel(BaseModel):
    id: str
    title: str
    body_html: Optional[str] = None
    handle: str
    published_at: Optional[datetime] = None
    updated_at: datetime
    created_at: datetime
    sort_order: Optional[
        str] = 'manual'  # 'manual', 'best-selling', 'alpha-asc', 'alpha-desc', 'price-asc', 'price-desc', 'created', 'created-desc'
    published: Optional[bool] = True
    collection_type: str = 'manual'  # 'manual' or 'smart'
    rules: Optional[List[Dict[str, Any]]] = Field(default_factory=list)  # Smart collection rules
    products: List[str] = Field(default_factory=list)  # Product IDs for manual collections
    admin_graphql_api_id: Optional[str] = None


class ShopifyDB(BaseModel):
    customers: Dict[str, ShopifyCustomerModel] = Field(default_factory=dict)
    products: Dict[str, ShopifyProductModel] = Field(default_factory=dict)
    orders: Dict[str, ShopifyOrderModel] = Field(default_factory=dict)
    draft_orders: Dict[str, ShopifyDraftOrderModel] = Field(default_factory=dict)
    returns: Dict[str, ShopifyReturnModel] = Field(default_factory=dict)
    calculated_orders: Dict[str, ShopifyCalculatedOrderModel] = Field(default_factory=dict)
    collections: Dict[str, ShopifyCollectionModel] = Field(default_factory=dict)
    exchanges: Dict[str, ShopifyExchangeModel] = Field(default_factory=dict)
    presentment_prices: Dict[str, Dict[str, MoneyModel]] = Field(default_factory=dict)

    def get_next_id(self, resource_type: str, prefix: Optional[str] = None) -> str:
        # A more robust ID generation might be needed for GIDs or complex string IDs.
        # This is a simplified version for numeric string IDs.
        collection = getattr(self, resource_type, {})
        if not collection:
            new_id = "1"
        else:
            max_id = 0
            for k in collection.keys():
                try:
                    # Attempt to extract number if GID or prefixed ID
                    id_part = k.split('/')[-1] if '/' in k else k
                    id_part = id_part.replace(prefix, '') if prefix else id_part
                    num_k = int(id_part)
                    if num_k > max_id:
                        max_id = num_k
                except ValueError:
                    continue  # Skip keys that aren't purely numeric or matching prefix
            new_id = str(max_id + 1)

        return f"{prefix}{new_id}" if prefix else new_id


class ShopifyTransactionInputModel(BaseModel):
    """
    Model for the 'transaction' dictionary argument to create a Shopify order transaction.
    """
    amount: str = Field(description="The amount of the transaction.")
    kind: Literal['authorization', 'capture', 'sale', 'void', 'refund'] = Field(
        description="The kind of transaction."
    )
    gateway: Optional[str] = Field(None, description="The payment gateway used. For manual payments, can be 'manual'.")
    parent_id: Optional[str] = Field(None,
                                     description="The ID of an existing transaction to explicitly void or capture.")
    currency: Optional[str] = Field(None,
                                    description="The currency (ISO 4217 format) of the transaction. Defaults to order currency.")
    test: Optional[bool] = Field(False, description="Whether this is a test transaction.")
    authorization: Optional[str] = Field(None,
                                         description="The authorization code, for external gateways when kind is 'sale' or 'authorization'.")
    payment_details: Optional[Dict[str, Any]] = Field(None,
                                                      description="Additional payment details specific to the gateway.")
    target_payment_method_id: Optional[str] = Field(
        None, 
        description="ID of the payment method to refund to (for cross-payment method refunds)"
    )
    source_name: Optional[str] = Field(None, description="The source of the transaction (e.g., 'web', 'api', 'pos')")

    class Config:
        extra = 'forbid'
        strict = True

    @validator('amount')
    @classmethod
    def amount_must_be_valid_positive_decimal_string(cls, v: str) -> str:
        """
        Validates that the amount is a string representing a positive decimal number.
        """
        try:
            decimal_amount = Decimal(v)
        except InvalidOperation:
            # This message is for test_error_invalid_amount_format
            raise ValueError("Transaction 'amount' must be a valid decimal number string.")

        if decimal_amount <= Decimal("0"):
            # This message is for test_error_zero_amount and test_error_negative_amount
            raise ValueError("Transaction 'amount' must be a positive value.")
        return v


# Update forward refs for all models at the end
ShopifyAddressModel.model_rebuild()
CustomerDefaultAddress.model_rebuild()
MoneyModel.model_rebuild()
PresentmentPriceModel.model_rebuild()
ShopifyCustomerModel.model_rebuild()
ProductImageModel.model_rebuild()
ProductOptionModel.model_rebuild()
ProductVariantModel.model_rebuild()
ShopifyProductModel.model_rebuild()
OrderLineItemModel.model_rebuild()
OrderCustomerInfo.model_rebuild()
ShippingLineModel.model_rebuild()
TaxLineModel.model_rebuild()
DiscountCodeModel.model_rebuild()
TransactionReceiptModel.model_rebuild()
ShopifyTransactionModel.model_rebuild()
RefundShippingDetail.model_rebuild()
RefundDutyItemModel.model_rebuild()
RefundLineItemModel.model_rebuild()
ShopifyRefundModel.model_rebuild()
ShopifyOrderModel.model_rebuild()
DraftOrderAppliedDiscountModel.model_rebuild()
DraftOrderShippingLineModel.model_rebuild()
DraftOrderCustomerModel.model_rebuild()
OrderEditCustomAttributeInputModel.model_rebuild()
DraftOrderLineItemModel.model_rebuild()
DraftOrderInvoiceModel.model_rebuild()
ShopifyDraftOrderModel.model_rebuild()
ReturnLineItemInputModel.model_rebuild()
ReturnLineItemResponseModel.model_rebuild()
ReturnInputModel.model_rebuild()
ShopifyReturnModel.model_rebuild()
CalculatedLineItemModel.model_rebuild()
ShopifyCalculatedOrderModel.model_rebuild()
ShopifyCollectionModel.model_rebuild()
ExchangeLineItemInputModel.model_rebuild()
ExchangeNewLineItemInputModel.model_rebuild()
ExchangeInputModel.model_rebuild()
ExchangeLineItemResponseModel.model_rebuild()
ExchangeNewLineItemResponseModel.model_rebuild()
ShopifyExchangeModel.model_rebuild()
ShopifyDB.model_rebuild()


# To handle forward references if models are defined out of order (Pydantic usually handles this well)
# For example, if OrderModel was defined before OrderLineItemModel:
# OrderLineItemModel.update_forward_refs()
# ShopifyOrderModel.update_forward_refs()
# etc. (Run this at the end of all model definitions if needed)

class ShopifyOrdersCountResponse(BaseModel):
    """
    Pydantic model for the return type of shopify_get_orders_count.
    Represents the dictionary containing the total count of orders.
    """
    count: int = Field(..., description="The total number of orders matching the specified criteria.")


class ShopifyLineItem(BaseModel):
    id: str
    variant_id: Optional[str] = None
    product_id: Optional[str] = None
    title: str
    variant_title: Optional[str] = None
    quantity: int
    price: str
    sku: Optional[str] = None
    grams: int
    taxable: bool
    requires_shipping: bool


class ShopifyCustomer(BaseModel):
    id: int
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    orders_count: int
    total_spent: str


class ShopifyOrder(BaseModel):
    id: str
    name: str
    email: str
    created_at: str  # ISO 8601 timestamp
    updated_at: str  # ISO 8601 timestamp
    closed_at: Optional[str] = None  # ISO 8601 timestamp
    financial_status: str
    fulfillment_status: Optional[str] = None
    currency: str
    total_price: str
    subtotal_price: str
    total_tax: str
    line_items: List[ShopifyLineItem]
    customer: Optional[ShopifyCustomer] = None


class ShopifyReopenOrderResponse(BaseModel):
    order: ShopifyOrder


class ShopifyOrderInventoryBehaviourEnum(str, Enum):
    """
    Valid values for inventory behaviour when creating an order.
    """
    BYPASS = "bypass"
    DECREMENT_IGNORING_POLICY = "decrement_ignoring_policy"
    DECREMENT_OBEYING_POLICY = "decrement_obeying_policy"

    @classmethod
    def values(cls):
        return [cls.BYPASS, cls.DECREMENT_IGNORING_POLICY, cls.DECREMENT_OBEYING_POLICY]


class ShopifyOrderCreateInputLineItem(BaseModel):
    """
    Represents a line item for creating an order.
    This model is specific to the input structure, allowing optional title and price
    which might be derived from variant_id or set for custom items, as suggested
    by the function's docstring ("can also include other fields like 'price', 'title', etc.").
    """
    variant_id: Optional[str] = None
    product_id: Optional[str] = None
    quantity: Optional[int] = None  # Changed from int to Optional[int]
    title: Optional[str] = None
    price: Optional[str] = None
    sku: Optional[str] = None
    grams: Optional[int] = None
    taxable: Optional[bool] = None
    requires_shipping: Optional[bool] = None
    gift_card: Optional[bool] = False
    total_discount_amount: Optional[str] = "0.00"
    # properties: Optional[List[Dict[str, str]]] = Field(default_factory=list) # Not explicitly detailed

    # Removed quantity_must_be_positive validator; this logic is now in the main function
    # to raise InvalidInputError for quantity <= 0.


class ShopifyOrderCreateInputCustomer(BaseModel):
    """
    Represents the customer data that can be passed in the 'customer' field of the order.
    """
    id: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    tags: Optional[str] = None


class ShopifyDiscountCodeModel(BaseModel):
    """
    Represents a discount code applied to an order.
    """
    code: str
    amount: str  # The value of the discount.
    type: str  # e.g., "fixed_amount", "percentage", "shipping"


class ShopifyTaxLineModel(BaseModel):
    """
    Represents a tax line on the order.
    """
    price: str  # The amount of tax to be applied.
    rate: float  # The rate of tax to be applied.
    title: str  # The name of the tax.
    channel_liable: Optional[bool] = None
    # price_set: Optional[Dict[str, Any]] = None # If using money objects


class ShopifyShippingLineModel(BaseModel):
    """
    Represents a shipping line on the order.
    """
    id: Optional[str] = None
    title: str
    price: str  # The price of the shipping method.
    code: Optional[str] = None  # A reference to the shipping method.
    source: Optional[str] = 'shopify'
    # price_set: Optional[Dict[str, Any]] = None # If using money objects
    # discounted_price: Optional[str] = None
    # tax_lines: Optional[List[ShopifyTaxLineModel]] = Field(default_factory=list)


class ShopifyOrderCreateInput(BaseModel):
    """
    Model for the 'order' argument dictionary of the shopify_create_an_order function.
    """
    line_items: List[ShopifyOrderCreateInputLineItem]

    customer: Optional[ShopifyOrderCreateInputCustomer] = None
    billing_address: Optional[ShopifyAddressModel] = None  # Reuses existing ShopifyAddressModel
    shipping_address: Optional[ShopifyAddressModel] = None  # Reuses existing ShopifyAddressModel
    email: Optional[EmailStr] = None  # Order-level email, can be different from customer email
    financial_status: Optional[str] = None  # e.g., "pending", "paid", "partially_paid"
    note: Optional[str] = None
    tags: Optional[str] = None
    transactions: Optional[List[ShopifyTransactionModel]] = Field(
        default_factory=list)  # Reuses existing ShopifyTransactionModel

    inventory_behaviour: Optional[str] = "bypass"  # Validated in function
    send_receipt: Optional[bool] = False
    send_fulfillment_receipt: Optional[bool] = False
    currency: Optional[str] = None  # ISO 4217 currency code

    # Added fields for financial breakdowns
    discount_codes: Optional[List[ShopifyDiscountCodeModel]] = Field(default_factory=list)
    tax_lines: Optional[List[ShopifyTaxLineModel]] = Field(default_factory=list)
    shipping_lines: Optional[List[ShopifyShippingLineModel]] = Field(default_factory=list)

    @validator('line_items')
    @classmethod
    def line_items_cannot_be_empty(cls, v):
        if not v:
            raise ValueError('Order line_items cannot be empty')
        return v
    # Removed line_items_cannot_be_empty validator; this is checked manually in the function
    # to raise InvalidInputError.

    # Removed check_inventory_behaviour_enum validator; this is checked manually in the function
    # to raise InvalidInputError for incorrect string values.


class ShopifyOrderCreateResponse(BaseModel):
    """
    Model for the dictionary returned by the shopify_create_an_order function.
    """
    order: 'ShopifyOrderModel'


ShopifyDiscountCodeModel.model_rebuild()
ShopifyTaxLineModel.model_rebuild()
ShopifyShippingLineModel.model_rebuild()


class ShopifyOrderCreateInputPlaceholder(BaseModel):
    line_items: List[Dict[str, Any]]  # Simplified for this example
    customer: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, Any]] = None  # Simplified
    shipping_address: Optional[Dict[str, Any]] = None  # Simplified
    email: Optional[str] = None
    financial_status: Optional[str] = None
    note: Optional[str] = None
    tags: Optional[str] = None
    transactions: Optional[List[Dict[str, Any]]] = None  # Simplified
    inventory_behaviour: str = "bypass"
    send_receipt: bool = False
    send_fulfillment_receipt: bool = False
    currency: Optional[str] = None
    discount_codes: Optional[List[Dict[str, Any]]] = None  # Added
    tax_lines: Optional[List[Dict[str, Any]]] = None  # Added
    shipping_lines: Optional[List[Dict[str, Any]]] = None  # Added


# --- Input Models for shopify_create_a_draft_order ---
class DraftOrderShopifyAddressModel(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    province_code: Optional[str] = None
    country_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    name: Optional[str] = None


class DraftOrderCustomAttributeInput(BaseModel):
    key: str
    value: str


class DraftOrderLineItemInput(BaseModel):
    variant_id: Optional[str] = None
    product_id: Optional[str] = None
    quantity: int
    title: Optional[str] = None
    price: Optional[str] = None
    sku: Optional[str] = None
    grams: Optional[int] = None
    requires_shipping: Optional[bool] = None
    taxable: Optional[bool] = None
    applied_discount: Optional[DraftOrderAppliedDiscountModel] = None
    custom_attributes: Optional[List[DraftOrderCustomAttributeInput]] = None

    # FIX: Add validator for quantity
    @field_validator('quantity')
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0.')
        return v


class DraftOrderCustomerInput(BaseModel):
    id: Optional[str] = None
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    tags: Optional[str] = None


class ShopifyDraftOrderCreateInput(BaseModel):
    line_items: List[DraftOrderLineItemInput] = Field(default_factory=list)
    customer: Optional[DraftOrderCustomerInput] = None
    shipping_address: Optional[DraftOrderShopifyAddressModel] = None
    billing_address: Optional[DraftOrderShopifyAddressModel] = None
    email: Optional[EmailStr] = None
    note: Optional[str] = None
    tags: Optional[str] = None
    shipping_line: Optional[DraftOrderShippingLineModel] = None
    applied_discount: Optional[DraftOrderAppliedDiscountModel] = None
    tax_exempt: Optional[bool] = False
    taxes_included: Optional[bool] = False


# Response Models
class DraftOrderCustomerResponseModel(BaseModel):
    id: str  # Should always have an ID in response
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class DraftOrderLineItemResponseModel(BaseModel):
    id: str
    variant_id: Optional[str] = None
    product_id: Optional[str] = None
    title: str
    variant_title: Optional[str] = None
    sku: Optional[str] = None
    vendor: Optional[str] = None
    quantity: int
    price: str
    grams: Optional[int] = None
    taxable: bool
    requires_shipping: bool
    applied_discount: Optional[DraftOrderAppliedDiscountModel] = None
    custom_attributes: Optional[List[DraftOrderCustomAttributeInput]] = None


class ShopifyDraftOrderResponseModel(BaseModel):
    id: str
    note: Optional[str] = None
    email: Optional[str] = None
    currency: str
    invoice_sent_at: Optional[str] = None
    invoice_url: Optional[str] = None
    name: str
    order_id: Optional[str] = None
    shipping_line: Optional[DraftOrderShippingLineModel] = None
    status: str
    subtotal_price: str
    tags: Optional[str] = None
    tax_exempt: bool
    tax_lines: List[TaxLineModel] = Field(default_factory=list)
    total_price: str
    total_tax: str
    created_at: str
    updated_at: str
    customer: Optional[DraftOrderCustomerResponseModel] = None
    line_items: List[DraftOrderLineItemResponseModel] = Field(default_factory=list)
    shipping_address: Optional[ShopifyAddressModel] = None
    billing_address: Optional[ShopifyAddressModel] = None
    applied_discount: Optional[DraftOrderAppliedDiscountModel] = None


# Rebuild models to resolve forward references
DraftOrderLineItemInput.model_rebuild()
ShopifyDraftOrderCreateInput.model_rebuild()
ShopifyDraftOrderResponseModel.model_rebuild(force=True)


class DraftOrderGetResponseCustomer(BaseModel):
    """Customer details as returned by the get draft order endpoint."""
    id: str
    email: str
    first_name: str
    last_name: str


class DraftOrderGetResponseLineItem(BaseModel):
    """Line item details as returned by the get draft order endpoint."""
    product_id: str
    variant_id: Optional[str] = None
    title: str
    quantity: int
    price: str
    applied_discount: Optional[Dict[str, str]] = None


class DraftOrderGetResponseShippingLine(BaseModel):
    """Shipping line details as returned by the get draft order endpoint."""
    title: str
    price: str


class ShopifyDraftOrderGetResponse(BaseModel):
    """
    Represents the structure of the dictionary returned by shopify_get_draft_order_by_id.
    """
    id: str
    admin_graphql_api_id: str
    name: str
    status: str
    email: str
    currency: str
    note: Optional[str] = None
    created_at: str  # ISO 8601 format
    updated_at: str  # ISO 8601 format
    invoice_sent_at: Optional[str] = None  # ISO 8601 format
    invoice_url: Optional[str] = None
    order_id: Optional[str] = None
    total_price: str
    subtotal_price: str
    total_tax: str
    customer: DraftOrderGetResponseCustomer
    line_items: List[DraftOrderGetResponseLineItem]
    # ShopifyAddressModel is from the existing schema and assumed to be a good fit
    # for the Dict[str, Any] structure of shipping_address.
    # If its structure is different, a new model would be needed here.
    shipping_address: Optional[
        Any]  # Using Any to represent Dict[str, Any] from docstring, or ideally ShopifyAddressModel
    shipping_line: Optional[DraftOrderGetResponseShippingLine] = None
    applied_discount: Optional[Dict[str, str]] = None


class DraftOrderUpdateAddressInputModel(BaseModel):
    """
    Input model for updating shipping or billing address in a draft order.
    Only includes fields that are updatable via the Shopify API.
    """
    id: Optional[str] = None
    customer_id: Optional[str] = None
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    zip: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    name: Optional[str] = None
    province_code: Optional[str] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    company: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DraftOrderUpdateInputModel(BaseModel):
    """
    Input model for updating a Shopify draft order.
    Only non-read-only fields are allowed.
    """
    customer_id: Optional[str] = Field(
        None, description="The ID of the customer associated with the draft order."
    )
    shipping_address: Optional[DraftOrderUpdateAddressInputModel] = Field(
        None, description="The address to ship the order to."
    )
    billing_address: Optional[DraftOrderUpdateAddressInputModel] = Field(
        None, description="The mailing address associated with the payment method."
    )
    note: Optional[str] = Field(
        None, description="The text of an optional note that a merchant can attach to the draft order."
    )
    email: Optional[EmailStr] = Field(
        None, description="The customer's email address."
    )
    line_items: Optional[List[DraftOrderGetResponseLineItem]] = Field(
        None,
        description="The product variant line item or custom line item(s) associated to the draft order. Each draft order must include at least one line_item."
    )
    shipping_line: Optional[DraftOrderGetResponseShippingLine] = Field(
        None, description="The shipping method used."
    )
    tags: Optional[str] = Field(
        None,
        description="A comma-separated list of additional short descriptors, commonly used for filtering and searching."
    )
    tax_exempt: Optional[bool] = Field(
        None, description="Whether taxes are exempt for the draft order."
    )
    applied_discount: Optional[Dict[str, Any]] = Field(
        None, description="The discount applied to the line item or the draft order resource."
    )
    customer: Optional[DraftOrderCustomerInput] = None


# --- Order Modification Input Models ---

class ModifyPendingOrderAddressInputModel(BaseModel):
    """Input model for modifying pending order address."""
    address1: str = Field(..., description="Primary street address line")
    city: str = Field(..., description="City name")
    province: str = Field(..., description="Province or state name")
    country: str = Field(..., description="Country name")
    zip: str = Field(..., description="Postal or ZIP code")
    first_name: str = Field(..., description="Recipient's first name")
    last_name: str = Field(..., description="Recipient's last name")
    address2: Optional[str] = Field(None, description="Secondary address line (apartment, suite, etc.)")
    province_code: Optional[str] = Field(None, description="Province or state code")
    country_code: Optional[str] = Field(None, description="Country code")
    phone: Optional[str] = Field(None, description="Address-specific phone number")
    company: Optional[str] = Field(None, description="Company name")


class ModifyPendingOrderLineItemInputModel(BaseModel):
    """Input model for line item updates in pending order modification."""
    variant_id: str = Field(..., description="Variant ID of the line item to add, modify or remove.")
    quantity: int = Field(..., ge=0, description="New quantity for the variant. Use 0 to remove the item from the order.")
    payment_method_id: Optional[str] = Field(None, description="Payment method ID to use for the order.")


class ModifyPendingOrderShippingLineInputModel(BaseModel):
    """Input model for shipping lines in pending order modification."""
    title: str = Field(..., description="Shipping method name")
    price: str = Field(..., description="Shipping cost as decimal string")
    code: Optional[str] = Field(None, description="Shipping method code")
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        try:
            price_decimal = Decimal(v)
            if price_decimal < 0:
                raise ValueError("Shipping price cannot be negative")
        except (TypeError, ValueError, InvalidOperation):
            raise ValueError("Shipping price must be a valid decimal string")
        return v


class ModifyPendingOrderTaxLineInputModel(BaseModel):
    """Input model for tax lines in pending order modification."""
    title: str = Field(..., description="Tax name")
    price: str = Field(..., description="Tax amount as decimal string")
    rate: float = Field(..., ge=0, description="Tax rate (must be non-negative)")
    
    @field_validator('price')
    @classmethod
    def validate_price(cls, v):
        try:
            price_decimal = Decimal(v)
            if price_decimal < 0:
                raise ValueError("Tax price cannot be negative")
        except (TypeError, ValueError, InvalidOperation):
            raise ValueError("Tax price must be a valid decimal string")
        return v


class ModifyPendingOrderDiscountCodeInputModel(BaseModel):
    """Input model for discount codes in pending order modification."""
    code: str = Field(..., description="Discount code")
    amount: str = Field(..., description="Discount amount as decimal string")
    type: str = Field(..., description="Discount type")
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        try:
            amount_decimal = Decimal(v)
            if amount_decimal < 0:
                raise ValueError("Discount amount cannot be negative")
        except (TypeError, ValueError, InvalidOperation):
            raise ValueError("Discount amount must be a valid decimal string")
        return v
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        valid_types = ["fixed_amount", "percentage"]
        if v not in valid_types:
            raise ValueError(f"Discount type must be one of: {', '.join(valid_types)}")
        return v


class ModifyPendingOrderItemsInputModel(BaseModel):
    """Input model for modifying pending order items."""
    line_items: Optional[List[ModifyPendingOrderLineItemInputModel]] = Field(None, description="List of line item updates")
    note: Optional[str] = Field(None, description="Order notes")
    tags: Optional[str] = Field(None, description="Order tags")


class ModifyPendingOrderTransactionInputModel(BaseModel):
    """Input model for transaction updates in pending order modification."""
    id: str = Field(..., description="Transaction ID")
    amount: str = Field(..., description="Transaction amount as decimal string")
    kind: str = Field(..., description="Transaction type")
    gateway: Optional[str] = Field(None, description="Payment gateway identifier")
    status: str = Field(..., description="Transaction status")
    currency: Optional[str] = Field(None, description="Three-letter currency code")
    original_payment_method_id: Optional[str] = Field(None, description="Original payment method ID")
    message: Optional[str] = Field(None, description="Status message")
    authorization: Optional[str] = Field(None, description="Authorization code")
    parent_id: Optional[str] = Field(None, description="Parent transaction identifier")
    test: Optional[bool] = Field(None, description="Whether this is a test transaction")
    device_id: Optional[str] = Field(None, description="Device ID")
    source_name: Optional[str] = Field(None, description="Source name")
    receipt: Optional[Dict[str, Any]] = Field(None, description="Receipt information")
    currency_exchange_adjustment: Optional[Dict[str, Any]] = Field(None, description="Currency exchange adjustment")
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        try:
            # Allow negative amounts for refunds - don't validate positivity here
            amount_decimal = Decimal(v)
        except (TypeError, ValueError, InvalidOperation):
            raise ValueError("Transaction amount must be a valid decimal string")
        return v
    
    @field_validator('kind')
    @classmethod
    def validate_kind(cls, v):
        valid_kinds = ["sale", "capture", "authorization", "void", "refund"]
        if v not in valid_kinds:
            raise ValueError(f"Transaction kind must be one of: {', '.join(valid_kinds)}")
        return v
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        # Allow "error" status as tests expect it
        valid_statuses = ["success", "pending", "failure", "error"]
        if v not in valid_statuses:
            raise ValueError(f"Transaction status must be one of: {', '.join(valid_statuses)}")
        return v


class ModifyPendingOrderPaymentInputModel(BaseModel):
    """Input model for modifying pending order payment."""
    transactions: List[ModifyPendingOrderTransactionInputModel] = Field(..., description="List of transaction updates")


# Rebuild models to resolve forward references
ModifyPendingOrderAddressInputModel.model_rebuild()
ModifyPendingOrderLineItemInputModel.model_rebuild()
ModifyPendingOrderShippingLineInputModel.model_rebuild()
ModifyPendingOrderTaxLineInputModel.model_rebuild()
ModifyPendingOrderDiscountCodeInputModel.model_rebuild()
ModifyPendingOrderItemsInputModel.model_rebuild()
ModifyPendingOrderTransactionInputModel.model_rebuild()
ModifyPendingOrderPaymentInputModel.model_rebuild()
