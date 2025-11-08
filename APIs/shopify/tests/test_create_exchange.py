import copy
from datetime import datetime, timezone
import re

from shopify.SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler
from shopify import DB, create_exchange


# Helper to extract local ID from input, now just returns the string number
def _get_order_id_from_input(order_id_str: str) -> str:
    return order_id_str


class TestShopifyCreateAnExchange(BaseTestCaseWithErrorHandler):
    # Use simple string numbers for order and line item IDs
    ORDER_ID_1 = "2001"
    ORDER_ID_2_NON_EXISTENT = "9999"
    ORDER_ID_3_CANCELLED = "2003"
    ORDER_ID_4_UNPAID = "2004"
    ORDER_ID_5_UNFULFILLED = "2005"

    ORDER_LINE_ITEM_ID_1A = "2A"
    ORDER_LINE_ITEM_ID_1B = "2B"
    ORDER_LINE_ITEM_ID_3A = "3A"
    ORDER_LINE_ITEM_ID_4A = "4A"
    ORDER_LINE_ITEM_ID_5A = "5A"

    PRODUCT_ID_1 = "PROD1"
    PRODUCT_ID_2 = "PROD2"
    VARIANT_ID_1A = "VAR1A"
    VARIANT_ID_1B = "VAR1B"
    VARIANT_ID_2A = "VAR2A"
    VARIANT_ID_2B = "VAR2B"

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        local_id_1 = _get_order_id_from_input(self.ORDER_ID_1)
        local_id_3_cancelled = _get_order_id_from_input(self.ORDER_ID_3_CANCELLED)
        local_id_4_unpaid = _get_order_id_from_input(self.ORDER_ID_4_UNPAID)
        local_id_5_unfulfilled = _get_order_id_from_input(self.ORDER_ID_5_UNFULFILLED)

        DB['orders'] = {
            local_id_1: {
                "id": self.ORDER_ID_1,
                "admin_graphql_api_id": self.ORDER_ID_1,
                "name": "#2001",
                "order_number": 2001,
                "email": "customer@example.com",
                "created_at": datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                "updated_at": datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                "currency": "USD",
                "financial_status": "paid",
                "fulfillment_status": "fulfilled",
                "total_price": "150.00",
                "status": "open",
                "line_items": [
                    {
                        "id": self.ORDER_LINE_ITEM_ID_1A,
                        "admin_graphql_api_id": self.ORDER_LINE_ITEM_ID_1A,
                        "title": "Blue Keyboard", "quantity": 1, "price": "100.00", "sku": "KB-BLUE",
                        "fulfillable_quantity": 0,
                        "fulfillment_status": "fulfilled", "requires_shipping": True,
                        "variant_id": self.VARIANT_ID_1A, "product_id": self.PRODUCT_ID_1,
                    },
                    {
                        "id": self.ORDER_LINE_ITEM_ID_1B,
                        "admin_graphql_api_id": self.ORDER_LINE_ITEM_ID_1B,
                        "title": "Apple Thermostat", "quantity": 1, "price": "50.00", "sku": "THERMO-APPLE",
                        "fulfillable_quantity": 0,
                        "fulfillment_status": "fulfilled", "requires_shipping": True,
                        "variant_id": self.VARIANT_ID_1B, "product_id": self.PRODUCT_ID_1,
                    }
                ],
                "refunds": [], "transactions": [], "shipping_lines": [], "tax_lines": [], "discount_codes": [],
            },
            local_id_3_cancelled: {
                "id": self.ORDER_ID_3_CANCELLED,
                "admin_graphql_api_id": self.ORDER_ID_3_CANCELLED,
                "name": "#2003", "order_number": 2003, "currency": "USD", "total_price": "75.00",
                "created_at": datetime(2023, 1, 3, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                "updated_at": datetime(2023, 1, 3, 11, 0, 0, tzinfo=timezone.utc).isoformat(),
                "financial_status": "voided", "fulfillment_status": None, "status": "cancelled",
                "cancelled_at": datetime(2023, 1, 3, 11, 0, 0, tzinfo=timezone.utc).isoformat(),
                "cancel_reason": "customer",
                "line_items": [{
                    "id": self.ORDER_LINE_ITEM_ID_3A,
                    "admin_graphql_api_id": self.ORDER_LINE_ITEM_ID_3A,
                    "title": "Product C", "quantity": 1, "price": "75.00", "sku": "SKU-C",
                    "fulfillable_quantity": 1,
                    "fulfillment_status": None, "requires_shipping": True,
                    "variant_id": "VAR3A", "product_id": "PROD3",
                }],
                "refunds": [], "transactions": [], "shipping_lines": [], "tax_lines": [], "discount_codes": [],
            },
            local_id_4_unpaid: {
                "id": self.ORDER_ID_4_UNPAID,
                "admin_graphql_api_id": self.ORDER_ID_4_UNPAID,
                "name": "#2004", "order_number": 2004, "currency": "USD", "total_price": "25.00",
                "created_at": datetime(2023, 1, 4, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                "updated_at": datetime(2023, 1, 4, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                "financial_status": "pending", "fulfillment_status": "fulfilled",
                "status": "open",
                "line_items": [{
                    "id": self.ORDER_LINE_ITEM_ID_4A,
                    "admin_graphql_api_id": self.ORDER_LINE_ITEM_ID_4A,
                    "title": "Product D", "quantity": 1, "price": "25.00", "sku": "SKU-D",
                    "fulfillable_quantity": 0,
                    "fulfillment_status": "fulfilled",
                    "requires_shipping": True,
                    "variant_id": "VAR4A", "product_id": "PROD4",
                }],
                "refunds": [], "transactions": [], "shipping_lines": [], "tax_lines": [], "discount_codes": [],
            },
            local_id_5_unfulfilled: {
                "id": self.ORDER_ID_5_UNFULFILLED,
                "admin_graphql_api_id": self.ORDER_ID_5_UNFULFILLED,
                "name": "#2005", "order_number": 2005, "currency": "USD", "total_price": "30.00",
                "created_at": datetime(2023, 1, 5, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                "updated_at": datetime(2023, 1, 5, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                "financial_status": "paid", "fulfillment_status": None, "status": "open",
                "line_items": [{
                    "id": self.ORDER_LINE_ITEM_ID_5A,
                    "admin_graphql_api_id": self.ORDER_LINE_ITEM_ID_5A,
                    "title": "Product E", "quantity": 1, "price": "30.00", "sku": "SKU-E",
                    "fulfillable_quantity": 1,
                    "fulfillment_status": None, "requires_shipping": True,
                    "variant_id": "VAR5A", "product_id": "PROD5",
                }],
                "refunds": [], "transactions": [], "shipping_lines": [], "tax_lines": [], "discount_codes": [],
            }
        }

        DB['products'] = {
            self.PRODUCT_ID_1: {
                "id": self.PRODUCT_ID_1,
                "title": "Tech Products",
                "vendor": "TechCorp",
                "variants": [
                    {
                        "id": self.VARIANT_ID_1A,
                        "title": "Blue Keyboard",
                        "price": "100.00",
                        "sku": "KB-BLUE",
                        "inventory_management": "shopify",
                        "inventory_policy": "deny",
                        "inventory_quantity": 10
                    },
                    {
                        "id": self.VARIANT_ID_1B,
                        "title": "Apple Thermostat",
                        "price": "50.00",
                        "sku": "THERMO-APPLE",
                        "inventory_management": "shopify",
                        "inventory_policy": "deny",
                        "inventory_quantity": 5
                    }
                ]
            },
            self.PRODUCT_ID_2: {
                "id": self.PRODUCT_ID_2,
                "title": "Replacement Products",
                "vendor": "TechCorp",
                "variants": [
                    {
                        "id": self.VARIANT_ID_2A,
                        "title": "Red Keyboard",
                        "price": "120.00",
                        "sku": "KB-RED",
                        "inventory_management": "shopify",
                        "inventory_policy": "deny",
                        "inventory_quantity": 8
                    },
                    {
                        "id": self.VARIANT_ID_2B,
                        "title": "Google Thermostat",
                        "price": "60.00",
                        "sku": "THERMO-GOOGLE",
                        "inventory_management": "shopify",
                        "inventory_policy": "deny",
                        "inventory_quantity": 3
                    }
                ]
            }
        }

        DB['exchanges'] = {}
        DB['returns'] = {}
        DB['customers'] = {}
        DB['draft_orders'] = {}
        DB['calculated_orders'] = {}

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _validate_exchange_structure(self, exchange_obj, expected_order_id, num_return_items, num_new_items):
        self.assertIsInstance(exchange_obj, dict)
        self.assertIn("exchange", exchange_obj)
        
        exchange = exchange_obj["exchange"]
        self.assertIsInstance(exchange, dict)
        
        # Validate basic exchange fields
        self.assertIn("id", exchange)
        self.assertTrue(isinstance(exchange["id"], str))
        self.assertEqual(exchange["order_id"], expected_order_id)
        self.assertIn("status", exchange)
        self.assertEqual(exchange["status"], "COMPLETED")
        self.assertIn("name", exchange)
        self.assertTrue(exchange["name"].startswith("#EX"))
        self.assertIn("price_difference", exchange)
        
        # Validate return line items
        self.assertIn("return_line_items", exchange)
        self.assertIsInstance(exchange["return_line_items"], list)
        self.assertEqual(len(exchange["return_line_items"]), num_return_items)
        
        for item in exchange["return_line_items"]:
            self.assertIn("id", item)
            self.assertTrue(isinstance(item["id"], str))
            self.assertIn("original_line_item_id", item)
            self.assertTrue(isinstance(item["original_line_item_id"], str))
            self.assertIn("quantity", item)
            self.assertIsInstance(item["quantity"], int)
            self.assertTrue(item["quantity"] > 0)
            self.assertIn("restock_type", item)
        
        # Validate new line items
        self.assertIn("new_line_items", exchange)
        self.assertIsInstance(exchange["new_line_items"], list)
        self.assertEqual(len(exchange["new_line_items"]), num_new_items)
        
        for item in exchange["new_line_items"]:
            self.assertIn("id", item)
            self.assertTrue(isinstance(item["id"], str))
            self.assertIn("variant_id", item)
            self.assertIn("product_id", item)
            self.assertIn("title", item)
            self.assertIn("quantity", item)
            self.assertIsInstance(item["quantity"], int)
            self.assertTrue(item["quantity"] > 0)
            self.assertIn("price", item)
        
        # Validate timestamps
        self.assertIn("created_at", exchange)
        self.assertIn("updated_at", exchange)
        try:
            datetime.fromisoformat(exchange["created_at"].replace("Z", "+00:00"))
            datetime.fromisoformat(exchange["updated_at"].replace("Z", "+00:00"))
        except ValueError as e:
            self.fail(f"Timestamp parsing failed: {e}")

    def test_create_exchange_success_single_item(self):
        """Test successful exchange of one item for another"""
        order_id = self.ORDER_ID_1
        return_line_items = [{
            "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A,
            "quantity": 1,
            "exchange_reason": "WRONG_COLOR",
            "exchange_reason_note": "Customer wants red instead of blue"
        }]
        new_line_items = [{
            "variant_id": self.VARIANT_ID_2A,
            "product_id": self.PRODUCT_ID_2,
            "quantity": 1
        }]
        
        result = create_exchange(
            order_id=order_id,
            return_line_items=return_line_items,
            new_line_items=new_line_items,
            exchange_reason="Color preference",
            exchange_note="Customer prefers red keyboard"
        )
        
        self._validate_exchange_structure(result, self.ORDER_ID_1, 1, 1)
        
        exchange = result["exchange"]
        self.assertEqual(exchange["exchange_reason"], "Color preference")
        self.assertEqual(exchange["exchange_note"], "Customer prefers red keyboard")
        
        # Check price difference (Red keyboard $120 - Blue keyboard $100 = $20)
        self.assertEqual(exchange["price_difference"], "20.00")
        
        # Verify return line item details
        return_item = exchange["return_line_items"][0]
        self.assertEqual(return_item["original_line_item_id"], self.ORDER_LINE_ITEM_ID_1A)
        self.assertEqual(return_item["quantity"], 1)
        self.assertEqual(return_item["exchange_reason"], "WRONG_COLOR")
        
        # Verify new line item details
        new_item = exchange["new_line_items"][0]
        self.assertEqual(new_item["variant_id"], self.VARIANT_ID_2A)
        self.assertEqual(new_item["product_id"], self.PRODUCT_ID_2)
        self.assertEqual(new_item["quantity"], 1)
        self.assertEqual(new_item["price"], "120.00")

    def test_create_exchange_success_multiple_items(self):
        """Test successful exchange of multiple items"""
        order_id = self.ORDER_ID_1
        return_line_items = [
            {
                "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A,
                "quantity": 1,
                "exchange_reason": "WRONG_COLOR"
            },
            {
                "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1B,
                "quantity": 1,
                "exchange_reason": "COMPATIBILITY_ISSUE"
            }
        ]
        new_line_items = [
            {
                "variant_id": self.VARIANT_ID_2A,
                "product_id": self.PRODUCT_ID_2,
                "quantity": 1
            },
            {
                "variant_id": self.VARIANT_ID_2B,
                "product_id": self.PRODUCT_ID_2,
                "quantity": 1
            }
        ]
        
        result = create_exchange(
            order_id=order_id,
            return_line_items=return_line_items,
            new_line_items=new_line_items
        )
        
        self._validate_exchange_structure(result, self.ORDER_ID_1, 2, 2)
        
        exchange = result["exchange"]
        # Check price difference (($120 + $60) - ($100 + $50) = $30)
        self.assertEqual(exchange["price_difference"], "30.00")

    def test_create_exchange_negative_price_difference(self):
        """Test exchange where new items cost less than returned items"""
        order_id = self.ORDER_ID_1
        return_line_items = [{
            "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A,
            "quantity": 1
        }]
        new_line_items = [{
            "variant_id": self.VARIANT_ID_1B,  # $50 thermostat
            "product_id": self.PRODUCT_ID_1,
            "quantity": 1
        }]
        
        result = create_exchange(
            order_id=order_id,
            return_line_items=return_line_items,
            new_line_items=new_line_items
        )
        
        exchange = result["exchange"]
        # Check price difference ($50 - $100 = -$50, customer gets refund)
        self.assertEqual(exchange["price_difference"], "-50.00")

    def test_create_exchange_with_custom_price(self):
        """Test exchange with custom pricing for new items"""
        order_id = self.ORDER_ID_1
        return_line_items = [{
            "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A,
            "quantity": 1
        }]
        new_line_items = [{
            "variant_id": self.VARIANT_ID_2A,
            "product_id": self.PRODUCT_ID_2,
            "quantity": 1,
            "price": "110.00"  # Custom price instead of default $120
        }]
        
        result = create_exchange(
            order_id=order_id,
            return_line_items=return_line_items,
            new_line_items=new_line_items
        )
        
        exchange = result["exchange"]
        # Check price difference with custom price ($110 - $100 = $10)
        self.assertEqual(exchange["price_difference"], "10.00")
        
        new_item = exchange["new_line_items"][0]
        self.assertEqual(new_item["price"], "110.00")

    def test_error_order_not_found(self):
        """Test error when order doesn't exist"""
        self.assert_error_behavior(
            create_exchange,
            custom_errors.NotFoundError,
            f"Order with id '{self.ORDER_ID_2_NON_EXISTENT}' not found.",
            order_id=self.ORDER_ID_2_NON_EXISTENT,
            return_line_items=[{"fulfillment_line_item_id": "1", "quantity": 1}],
            new_line_items=[{"variant_id": self.VARIANT_ID_2A, "product_id": self.PRODUCT_ID_2, "quantity": 1}]
        )

    def test_error_cancelled_order(self):
        """Test error when trying to exchange items from cancelled order"""
        self.assert_error_behavior(
            create_exchange,
            custom_errors.ShopifyExchangeError,
            f"Cannot create exchange for cancelled order '{self.ORDER_ID_3_CANCELLED}'.",
            order_id=self.ORDER_ID_3_CANCELLED,
            return_line_items=[{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_3A, "quantity": 1}],
            new_line_items=[{"variant_id": self.VARIANT_ID_2A, "product_id": self.PRODUCT_ID_2, "quantity": 1}]
        )

    def test_error_unpaid_order(self):
        """Test error when trying to exchange items from unpaid order"""
        self.assert_error_behavior(
            create_exchange,
            custom_errors.ShopifyExchangeError,
            f"Order '{self.ORDER_ID_4_UNPAID}' must be paid to create an exchange. Current status: pending",
            order_id=self.ORDER_ID_4_UNPAID,
            return_line_items=[{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_4A, "quantity": 1}],
            new_line_items=[{"variant_id": self.VARIANT_ID_2A, "product_id": self.PRODUCT_ID_2, "quantity": 1}]
        )

    def test_error_line_item_not_found(self):
        """Test error when line item doesn't exist in order"""
        self.assert_error_behavior(
            create_exchange,
            custom_errors.ShopifyInvalidInputError,
            f"Line item with ID 'NONEXISTENT' not found in order '{self.ORDER_ID_1}'.",
            order_id=self.ORDER_ID_1,
            return_line_items=[{"fulfillment_line_item_id": "NONEXISTENT", "quantity": 1}],
            new_line_items=[{"variant_id": self.VARIANT_ID_2A, "product_id": self.PRODUCT_ID_2, "quantity": 1}]
        )

    def test_error_line_item_not_fulfilled(self):
        """Test error when trying to exchange unfulfilled items"""
        self.assert_error_behavior(
            create_exchange,
            custom_errors.ShopifyExchangeError,
            f"Line item '{self.ORDER_LINE_ITEM_ID_5A}' must be fulfilled before it can be exchanged.",
            order_id=self.ORDER_ID_5_UNFULFILLED,
            return_line_items=[{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_5A, "quantity": 1}],
            new_line_items=[{"variant_id": self.VARIANT_ID_2A, "product_id": self.PRODUCT_ID_2, "quantity": 1}]
        )

    def test_error_quantity_exceeds_ordered(self):
        """Test error when exchange quantity exceeds ordered quantity"""
        self.assert_error_behavior(
            create_exchange,
            custom_errors.ShopifyInvalidInputError,
            f"Cannot exchange quantity 2 for line item '{self.ORDER_LINE_ITEM_ID_1A}'. Available for exchange: 1 (Fulfilled: 1, Already Exchanged: 0).",
            order_id=self.ORDER_ID_1,
            return_line_items=[{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A, "quantity": 2}],
            new_line_items=[{"variant_id": self.VARIANT_ID_2A, "product_id": self.PRODUCT_ID_2, "quantity": 1}]
        )

    def test_error_product_not_found(self):
        """Test error when new product doesn't exist"""
        self.assert_error_behavior(
            create_exchange,
            custom_errors.NotFoundError,
            "Product with id 'NONEXISTENT' not found.",
            order_id=self.ORDER_ID_1,
            return_line_items=[{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A, "quantity": 1}],
            new_line_items=[{"variant_id": "VAR_X", "product_id": "NONEXISTENT", "quantity": 1}]
        )

    def test_error_variant_not_found(self):
        """Test error when new variant doesn't exist"""
        self.assert_error_behavior(
            create_exchange,
            custom_errors.NotFoundError,
            f"Variant with id 'NONEXISTENT' not found in product '{self.PRODUCT_ID_2}'.",
            order_id=self.ORDER_ID_1,
            return_line_items=[{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A, "quantity": 1}],
            new_line_items=[{"variant_id": "NONEXISTENT", "product_id": self.PRODUCT_ID_2, "quantity": 1}]
        )

    def test_error_insufficient_inventory(self):
        """Test error when insufficient inventory for new items"""
        # Set inventory to 0 for the variant
        DB['products'][self.PRODUCT_ID_2]['variants'][0]['inventory_quantity'] = 0
        
        self.assert_error_behavior(
            create_exchange,
            custom_errors.ShopifyInvalidInputError,
            f"Insufficient inventory for variant '{self.VARIANT_ID_2A}'. Requested: 1, Available: 0",
            order_id=self.ORDER_ID_1,
            return_line_items=[{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A, "quantity": 1}],
            new_line_items=[{"variant_id": self.VARIANT_ID_2A, "product_id": self.PRODUCT_ID_2, "quantity": 1}]
        )

    def test_error_missing_return_line_items(self):
        """Test error when return_line_items is empty"""
        self.assert_error_behavior(
            create_exchange,
            custom_errors.ShopifyInvalidInputError,
            "Invalid exchange input:",
            order_id=self.ORDER_ID_1,
            return_line_items=[],
            new_line_items=[{"variant_id": self.VARIANT_ID_2A, "product_id": self.PRODUCT_ID_2, "quantity": 1}]
        )

    def test_error_missing_new_line_items(self):
        """Test error when new_line_items is empty"""
        self.assert_error_behavior(
            create_exchange,
            custom_errors.ShopifyInvalidInputError,
            "Invalid exchange input:",
            order_id=self.ORDER_ID_1,
            return_line_items=[{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A, "quantity": 1}],
            new_line_items=[]
        )

    def test_error_zero_quantity_return(self):
        """Test error when return quantity is zero"""
        self.assert_error_behavior(
            create_exchange,
            custom_errors.ShopifyInvalidInputError,
            "Invalid exchange input:",
            order_id=self.ORDER_ID_1,
            return_line_items=[{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A, "quantity": 0}],
            new_line_items=[{"variant_id": self.VARIANT_ID_2A, "product_id": self.PRODUCT_ID_2, "quantity": 1}]
        )

    def test_error_zero_quantity_new(self):
        """Test error when new item quantity is zero"""
        self.assert_error_behavior(
            create_exchange,
            custom_errors.ShopifyInvalidInputError,
            "Invalid exchange input:",
            order_id=self.ORDER_ID_1,
            return_line_items=[{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A, "quantity": 1}],
            new_line_items=[{"variant_id": self.VARIANT_ID_2A, "product_id": self.PRODUCT_ID_2, "quantity": 0}]
        )

    def test_inventory_adjustment_on_exchange(self):
        """Test that inventory is properly adjusted during exchange"""
        # Check initial inventory
        initial_blue_inventory = DB['products'][self.PRODUCT_ID_1]['variants'][0]['inventory_quantity']
        initial_red_inventory = DB['products'][self.PRODUCT_ID_2]['variants'][0]['inventory_quantity']
        
        order_id = self.ORDER_ID_1
        return_line_items = [{
            "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A,
            "quantity": 1
        }]
        new_line_items = [{
            "variant_id": self.VARIANT_ID_2A,
            "product_id": self.PRODUCT_ID_2,
            "quantity": 1
        }]
        
        result = create_exchange(
            order_id=order_id,
            return_line_items=return_line_items,
            new_line_items=new_line_items,
            restock_returned_items=True
        )
        
        # Check that inventory was adjusted
        # Blue keyboard should be restocked (+1)
        final_blue_inventory = DB['products'][self.PRODUCT_ID_1]['variants'][0]['inventory_quantity']
        self.assertEqual(final_blue_inventory, initial_blue_inventory + 1)
        
        # Red keyboard should be decremented (-1)
        final_red_inventory = DB['products'][self.PRODUCT_ID_2]['variants'][0]['inventory_quantity']
        self.assertEqual(final_red_inventory, initial_red_inventory - 1)

    def test_no_restock_option(self):
        """Test exchange with restock_returned_items=False"""
        initial_blue_inventory = DB['products'][self.PRODUCT_ID_1]['variants'][0]['inventory_quantity']
        initial_red_inventory = DB['products'][self.PRODUCT_ID_2]['variants'][0]['inventory_quantity']
        
        order_id = self.ORDER_ID_1
        return_line_items = [{
            "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A,
            "quantity": 1
        }]
        new_line_items = [{
            "variant_id": self.VARIANT_ID_2A,
            "product_id": self.PRODUCT_ID_2,
            "quantity": 1
        }]
        
        result = create_exchange(
            order_id=order_id,
            return_line_items=return_line_items,
            new_line_items=new_line_items,
            restock_returned_items=False
        )
        
        # Check that returned items were NOT restocked
        final_blue_inventory = DB['products'][self.PRODUCT_ID_1]['variants'][0]['inventory_quantity']
        self.assertEqual(final_blue_inventory, initial_blue_inventory)  # No change
        
        # New items should still be decremented
        final_red_inventory = DB['products'][self.PRODUCT_ID_2]['variants'][0]['inventory_quantity']
        self.assertEqual(final_red_inventory, initial_red_inventory - 1)
        
        # Check restock_type in response
        exchange = result["exchange"]
        return_item = exchange["return_line_items"][0]
        self.assertEqual(return_item["restock_type"], "NO_RESTOCK")

    def test_exchange_stored_in_database(self):
        """Test that exchange is properly stored in database"""
        order_id = self.ORDER_ID_1
        return_line_items = [{
            "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A,
            "quantity": 1
        }]
        new_line_items = [{
            "variant_id": self.VARIANT_ID_2A,
            "product_id": self.PRODUCT_ID_2,
            "quantity": 1
        }]
        
        result = create_exchange(
            order_id=order_id,
            return_line_items=return_line_items,
            new_line_items=new_line_items
        )
        
        exchange_id = result["exchange"]["id"]
        
        # Check that exchange is stored in database
        self.assertIn("exchanges", DB)
        self.assertIn(exchange_id, DB["exchanges"])
        
        stored_exchange = DB["exchanges"][exchange_id]
        self.assertEqual(stored_exchange["id"], exchange_id)
        self.assertEqual(stored_exchange["order_id"], order_id)
        self.assertEqual(stored_exchange["status"], "COMPLETED")

    def test_error_exchanging_same_item_twice_in_full(self):
        """Test error when trying to exchange the same item twice if the full quantity was already exchanged."""
        order_id = self.ORDER_ID_1

        # First exchange of the full quantity
        create_exchange(
            order_id=order_id,
            return_line_items=[{
                "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A,
                "quantity": 1
            }],
            new_line_items=[{
                "variant_id": self.VARIANT_ID_2A,
                "product_id": self.PRODUCT_ID_2,
                "quantity": 1
            }]
        )

        # Second attempt to exchange the same item
        self.assert_error_behavior(
            create_exchange,
            custom_errors.ShopifyInvalidInputError,
            
            f"Cannot exchange quantity 1 for line item '{self.ORDER_LINE_ITEM_ID_1A}'. Available for exchange: 0 (Fulfilled: 1, Already Exchanged: 1).",
            order_id=order_id,
            return_line_items=[{
                "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A,
                "quantity": 1
            }],
            new_line_items=[{
                "variant_id": self.VARIANT_ID_2B,
                "product_id": self.PRODUCT_ID_2,
                "quantity": 1
            }]
        )

    def test_successful_partial_then_full_exchange(self):
        """Test a partial exchange followed by an exchange of the remaining quantity."""
        # Setup an order with a line item of quantity 2
        order_id_with_multiple_qty = "2001"
        line_item_id_multiple_qty = "2A"
        DB['orders'][order_id_with_multiple_qty]['line_items'][0]['quantity'] = 2

        # First, exchange 1 out of 2 items
        result1 = create_exchange(
            order_id=order_id_with_multiple_qty,
            return_line_items=[{
                "fulfillment_line_item_id": line_item_id_multiple_qty,
                "quantity": 1
            }],
            new_line_items=[{
                "variant_id": self.VARIANT_ID_2A,
                "product_id": self.PRODUCT_ID_2,
                "quantity": 1
            }]
        )
        self.assertEqual(result1['exchange']['return_line_items'][0]['quantity'], 1)

        # Second, exchange the remaining 1 item
        result2 = create_exchange(
            order_id=order_id_with_multiple_qty,
            return_line_items=[{
                "fulfillment_line_item_id": line_item_id_multiple_qty,
                "quantity": 1
            }],
            new_line_items=[{
                "variant_id": self.VARIANT_ID_2B,
                "product_id": self.PRODUCT_ID_2,
                "quantity": 1
            }]
        )
        self.assertEqual(result2['exchange']['return_line_items'][0]['quantity'], 1)

        # Third, attempt to exchange again and expect an error
        self.assert_error_behavior(
            create_exchange,
            custom_errors.ShopifyInvalidInputError,
            f"Cannot exchange quantity 1 for line item '{line_item_id_multiple_qty}'. Available for exchange: 0 (Fulfilled: 2, Already Exchanged: 2).",
            order_id=order_id_with_multiple_qty,
            return_line_items=[{
                "fulfillment_line_item_id": line_item_id_multiple_qty,
                "quantity": 1
            }],
            new_line_items=[{
                "variant_id": self.VARIANT_ID_2B,
                "product_id": self.PRODUCT_ID_2,
                "quantity": 1
            }]
        ) 