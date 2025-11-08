import copy
from datetime import datetime, timezone
import re

from shopify.SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler
from shopify import DB, create_return


# Helper to extract local ID from input, now just returns the string number
def _get_order_id_from_input(order_id_str: str) -> str:
    return order_id_str


class TestShopifyCreateAReturn(BaseTestCaseWithErrorHandler):
    # Use simple string numbers for order and line item IDs
    ORDER_ID_1 = "1001"
    ORDER_ID_2_NON_EXISTENT = "9999"
    ORDER_ID_3_CANCELLED = "1003"
    ORDER_ID_4_NO_FULFILLABLE = "1004"
    ORDER_ID_5_CLOSED = "1005"

    ORDER_LINE_ITEM_ID_1A = "1A"
    ORDER_LINE_ITEM_ID_1B = "1B"
    ORDER_LINE_ITEM_ID_3A = "3A"
    ORDER_LINE_ITEM_ID_4A = "4A"
    ORDER_LINE_ITEM_ID_5A = "5A"

    VALID_RETURN_REASONS = [
        "UNKNOWN", "DAMAGED_OR_DEFECTIVE", "NOT_AS_DESCRIBED", "WRONG_ITEM_SENT",
        "SIZE_TOO_SMALL", "SIZE_TOO_LARGE", "STYLE_NOT_AS_EXPECTED",
        "COLOR_NOT_AS_EXPECTED", "CHANGED_MIND", "UNWANTED_GIFT", "OTHER"
    ]

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        local_id_1 = _get_order_id_from_input(self.ORDER_ID_1)
        local_id_3_cancelled = _get_order_id_from_input(self.ORDER_ID_3_CANCELLED)
        local_id_4_no_fulfillable = _get_order_id_from_input(self.ORDER_ID_4_NO_FULFILLABLE)
        local_id_5_closed = _get_order_id_from_input(self.ORDER_ID_5_CLOSED)

        DB['orders'] = {
            local_id_1: {
                "id": self.ORDER_ID_1,
                "admin_graphql_api_id": self.ORDER_ID_1,
                "name": "#1001",
                "order_number": 1001,
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
                        # CHANGE: Use ORDER_LINE_ITEM_ID_1A directly as the 'id'
                        "id": self.ORDER_LINE_ITEM_ID_1A,
                        "admin_graphql_api_id": self.ORDER_LINE_ITEM_ID_1A,
                        "title": "Product A", "quantity": 2, "price": "50.00", "sku": "SKU-A",
                        "fulfillable_quantity": 0,
                        "fulfillment_status": "fulfilled", "requires_shipping": True,
                        "variant_id": "VAR1A", "product_id": "PROD1",
                    },
                    {
                        # CHANGE: Use ORDER_LINE_ITEM_ID_1B directly as the 'id'
                        "id": self.ORDER_LINE_ITEM_ID_1B,
                        "admin_graphql_api_id": self.ORDER_LINE_ITEM_ID_1B,
                        "title": "Product B", "quantity": 1, "price": "50.00", "sku": "SKU-B",
                        "fulfillable_quantity": 0,
                        "fulfillment_status": "fulfilled", "requires_shipping": True,
                        "variant_id": "VAR1B", "product_id": "PROD1",
                    }
                ],
                "refunds": [], "transactions": [], "shipping_lines": [], "tax_lines": [], "discount_codes": [],
            },
            local_id_3_cancelled: {
                "id": self.ORDER_ID_3_CANCELLED,
                "admin_graphql_api_id": self.ORDER_ID_3_CANCELLED,
                "name": "#1003", "order_number": 1003, "currency": "USD", "total_price": "75.00",
                "created_at": datetime(2023, 1, 3, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                "updated_at": datetime(2023, 1, 3, 11, 0, 0, tzinfo=timezone.utc).isoformat(),
                "financial_status": "voided", "fulfillment_status": None, "status": "cancelled",
                "cancelled_at": datetime(2023, 1, 3, 11, 0, 0, tzinfo=timezone.utc).isoformat(),
                "cancel_reason": "customer",
                "line_items": [{
                    # CHANGE: Use ORDER_LINE_ITEM_ID_3A directly as the 'id'
                    "id": self.ORDER_LINE_ITEM_ID_3A,
                    "admin_graphql_api_id": self.ORDER_LINE_ITEM_ID_3A,
                    "title": "Product C", "quantity": 1, "price": "75.00", "sku": "SKU-C",
                    "fulfillable_quantity": 1,
                    "fulfillment_status": None, "requires_shipping": True,
                    "variant_id": "VAR3A", "product_id": "PROD3",
                }],
                "refunds": [], "transactions": [], "shipping_lines": [], "tax_lines": [], "discount_codes": [],
            },
            local_id_4_no_fulfillable: {
                "id": self.ORDER_ID_4_NO_FULFILLABLE,
                "admin_graphql_api_id": self.ORDER_ID_4_NO_FULFILLABLE,
                "name": "#1004", "order_number": 1004, "currency": "USD", "total_price": "25.00",
                "created_at": datetime(2023, 1, 4, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                "updated_at": datetime(2023, 1, 4, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                "financial_status": "paid", "fulfillment_status": None,
                "status": "open",
                "line_items": [{
                    # CHANGE: Use ORDER_LINE_ITEM_ID_4A directly as the 'id'
                    "id": self.ORDER_LINE_ITEM_ID_4A,
                    "admin_graphql_api_id": self.ORDER_LINE_ITEM_ID_4A,
                    "title": "Product D", "quantity": 1, "price": "25.00", "sku": "SKU-D",
                    "fulfillable_quantity": 1,
                    "fulfillment_status": None,
                    "requires_shipping": True,
                    "variant_id": "VAR4A", "product_id": "PROD4",
                }],
                "refunds": [], "transactions": [], "shipping_lines": [], "tax_lines": [], "discount_codes": [],
            },
            local_id_5_closed: {
                "id": self.ORDER_ID_5_CLOSED,
                "admin_graphql_api_id": self.ORDER_ID_5_CLOSED,
                "name": "#1005", "order_number": 1005, "currency": "USD", "total_price": "30.00",
                "created_at": datetime(2023, 1, 5, 10, 0, 0, tzinfo=timezone.utc).isoformat(),
                "updated_at": datetime(2023, 1, 5, 11, 0, 0, tzinfo=timezone.utc).isoformat(),
                "financial_status": "paid", "fulfillment_status": "fulfilled", "status": "closed",
                "closed_at": datetime(2023, 1, 5, 11, 0, 0, tzinfo=timezone.utc).isoformat(),
                "line_items": [{
                    # CHANGE: Use ORDER_LINE_ITEM_ID_5A directly as the 'id'
                    "id": self.ORDER_LINE_ITEM_ID_5A,
                    "admin_graphql_api_id": self.ORDER_LINE_ITEM_ID_5A,
                    "title": "Product E", "quantity": 1, "price": "30.00", "sku": "SKU-E",
                    "fulfillable_quantity": 0,
                    "fulfillment_status": "fulfilled", "requires_shipping": True,
                    "variant_id": "VAR5A", "product_id": "PROD5",
                }],
                "refunds": [], "transactions": [], "shipping_lines": [], "tax_lines": [], "discount_codes": [],
            }
        }
        DB['returns'] = {}
        DB['products'] = {}
        DB['customers'] = {}
        DB['draft_orders'] = {}
        DB['calculated_orders'] = {}

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _validate_return_structure(self, return_obj, expected_order_id, num_line_items):
        self.assertIsInstance(return_obj, dict)
        self.assertIn("id", return_obj)
        # Now expect id to be a simple number string, not a gid
        self.assertTrue(isinstance(return_obj["id"], str))
        self.assertEqual(return_obj["order_id"], expected_order_id)
        self.assertIn("status", return_obj)
        self.assertIn(return_obj["status"], ["OPEN", "REQUESTED", "APPROVED", "REJECTED", "CLOSED"])
        self.assertIn("name", return_obj)
        self.assertTrue(return_obj["name"].startswith("#R"))

        self.assertIn("return_line_items", return_obj)
        self.assertIsInstance(return_obj["return_line_items"], list)
        self.assertEqual(len(return_obj["return_line_items"]), num_line_items)

        for item in return_obj["return_line_items"]:
            self.assertIn("id", item)
            self.assertTrue(isinstance(item["id"], str))
            self.assertIn("line_item_id", item)
            self.assertTrue(isinstance(item["line_item_id"], str))
            self.assertIn("quantity", item)
            self.assertIsInstance(item["quantity"], int)
            self.assertTrue(item["quantity"] > 0)
            self.assertIn("return_reason", item)
            self.assertIn("return_reason_note", item)
            self.assertIn("restock_type", item)

        self.assertIn("created_at", return_obj)
        self.assertIn("updated_at", return_obj)
        try:
            # Attempt to parse to validate ISO 8601 format
            datetime.fromisoformat(return_obj["created_at"].replace("Z", "+00:00"))
            datetime.fromisoformat(return_obj["updated_at"].replace("Z", "+00:00"))
        except ValueError as e:
            self.fail(
                f"Timestamp parsing failed: {e}. created_at: {return_obj['created_at']}, updated_at: {return_obj['updated_at']}")

    def test_create_return_success_single_item(self):
        order_id = self.ORDER_ID_1
        return_line_items = [{
            "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A,
            "quantity": 1,
            "return_reason": "DAMAGED_OR_DEFECTIVE",
            "return_reason_note": "Item arrived broken."
        }]
        result = create_return(order_id=order_id, return_line_items=return_line_items)

        self._validate_return_structure(result, self.ORDER_ID_1, 1)
        rli = result["return_line_items"][0]
        self.assertEqual(rli["line_item_id"], self.ORDER_LINE_ITEM_ID_1A)
        self.assertEqual(rli["quantity"], 1)
        self.assertEqual(rli["return_reason"], "DAMAGED_OR_DEFECTIVE")
        self.assertEqual(rli["return_reason_note"], "Item arrived broken.")

        self.assertIn(result["id"], DB['returns'])
        db_return = DB['returns'][result["id"]]
        self.assertEqual(db_return["order_id"], self.ORDER_ID_1)
        self.assertEqual(len(db_return["return_line_items"]), 1)
        self.assertEqual(db_return["return_line_items"][0]["line_item_id"], self.ORDER_LINE_ITEM_ID_1A)

    def test_create_return_success_multiple_items(self):
        order_id = self.ORDER_ID_1
        return_line_items = [
            {"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A, "quantity": 1},
            {"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1B, "quantity": 1,
             "return_reason": "SIZE_TOO_SMALL"}
        ]
        result = create_return(order_id=order_id, return_line_items=return_line_items)

        self._validate_return_structure(result, self.ORDER_ID_1, 2)
        rli1, rli2 = result["return_line_items"]
        self.assertEqual(rli1["line_item_id"], self.ORDER_LINE_ITEM_ID_1A)
        self.assertEqual(rli1["quantity"], 1)
        self.assertIsNone(rli1["return_reason"])
        self.assertIsNone(rli1["return_reason_note"])

        self.assertEqual(rli2["line_item_id"], self.ORDER_LINE_ITEM_ID_1B)
        self.assertEqual(rli2["quantity"], 1)
        self.assertEqual(rli2["return_reason"], "SIZE_TOO_SMALL")
        self.assertIsNone(rli2["return_reason_note"])
        self.assertIn(result["id"], DB['returns'])

    def test_create_return_all_valid_reasons(self):
        for reason in self.VALID_RETURN_REASONS:
            with self.subTest(reason=reason):
                self.tearDown()
                self.setUp()

                order_id = self.ORDER_ID_1
                return_line_items = [{
                    "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A,
                    "quantity": 1,
                    "return_reason": reason
                }]
                result = create_return(order_id=order_id, return_line_items=return_line_items)
                self._validate_return_structure(result, self.ORDER_ID_1, 1)
                self.assertEqual(result["return_line_items"][0]["return_reason"], reason)
                if result and result.get("id") in DB['returns']:
                    del DB['returns'][result['id']]

    def test_error_order_not_found(self):
        order_id = self.ORDER_ID_2_NON_EXISTENT
        return_line_items = [{"fulfillment_line_item_id": "ANY", "quantity": 1}]
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyNotFoundError,
            expected_message=f"Order with ID '{self.ORDER_ID_2_NON_EXISTENT}' not found.",
            order_id=order_id,
            return_line_items=return_line_items
        )

    def test_error_missing_order_id(self):
        # order_id is missing
        return_line_items = [{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A, "quantity": 1}]
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyInvalidInputError,
            expected_message="Invalid input: order_id: Input should be a valid string",
            # order_id is omitted
            return_line_items=return_line_items, 
            order_id=None,
        )

    def test_error_missing_return_line_items_key(self):
        order_id = self.ORDER_ID_1
        # return_line_items is missing
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyInvalidInputError,
            expected_message="Invalid input: return_line_items: Input should be a valid list",
            order_id=order_id,
            return_line_items=None,
        )

    def test_error_empty_return_line_items_list(self):
        order_id = self.ORDER_ID_1
        return_line_items = []
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyInvalidInputError,
            expected_message="Invalid input: return_line_items: List should have at least 1 item after validation, not 0",
            order_id=order_id,
            return_line_items=return_line_items
        )

    def test_error_line_item_missing_fulfillment_id(self):
        order_id = self.ORDER_ID_1
        return_line_items = [{"quantity": 1}]
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyInvalidInputError,
            expected_message="Invalid input: return_line_items.0.fulfillment_line_item_id: Field required",
            order_id=order_id,
            return_line_items=return_line_items
        )

    def test_error_line_item_missing_quantity(self):
        order_id = self.ORDER_ID_1
        return_line_items = [{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A}]
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyInvalidInputError,
            expected_message="Invalid input: return_line_items.0.quantity: Field required",
            order_id=order_id,
            return_line_items=return_line_items
        )

    def test_error_line_item_quantity_zero(self):
        order_id = self.ORDER_ID_1
        return_line_items = [{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A, "quantity": 0}]
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyInvalidInputError,
            expected_message=f"Return quantity for fulfillment line item '{self.ORDER_LINE_ITEM_ID_1A}' must be positive.",
            order_id=order_id,
            return_line_items=return_line_items
        )

    def test_error_line_item_quantity_negative(self):
        order_id = self.ORDER_ID_1
        return_line_items = [{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A, "quantity": -1}]
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyInvalidInputError,
            expected_message=f"Return quantity for fulfillment line item '{self.ORDER_LINE_ITEM_ID_1A}' must be positive.",
            order_id=order_id,
            return_line_items=return_line_items
        )

    def test_error_invalid_return_reason(self):
        order_id = self.ORDER_ID_1
        return_line_items = [{
            "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A,
            "quantity": 1, "return_reason": "INVALID_REASON_CODE"
        }]
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyInvalidInputError,
            expected_message="Invalid input: return_line_items.0.return_reason: Input should be 'UNKNOWN', 'DAMAGED_OR_DEFECTIVE', 'NOT_AS_DESCRIBED', 'WRONG_ITEM_SENT', 'SIZE_TOO_SMALL', 'SIZE_TOO_LARGE', 'STYLE_NOT_AS_EXPECTED', 'COLOR_NOT_AS_EXPECTED', 'CHANGED_MIND', 'UNWANTED_GIFT' or 'OTHER'",
            order_id=order_id,
            return_line_items=return_line_items
        )

    def test_error_fulfillment_line_item_not_on_order(self):
        non_existent_fli_id = "NONEXISTENTFLI"
        order_id = self.ORDER_ID_1
        return_line_items = [{"fulfillment_line_item_id": non_existent_fli_id, "quantity": 1}]
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyInvalidInputError,
            expected_message=f"Fulfillment line item with ID '{non_existent_fli_id}' not found in order '{self.ORDER_ID_1}'.",
            order_id=order_id,
            return_line_items=return_line_items
        )

    def test_error_quantity_exceeds_fulfillable(self):
        order_id = self.ORDER_ID_1
        return_line_items = [{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A, "quantity": 3}]
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyReturnError,
            expected_message=f"Cannot return quantity 3 for line item '{self.ORDER_LINE_ITEM_ID_1A}'. Fulfilled: 2, Already Returned: 0, Available: 2.",
            order_id=order_id,
            return_line_items=return_line_items
        )

    def test_error_quantity_exceeds_available_after_partial_return(self):
        order_id = self.ORDER_ID_1
        initial_return_line_items = [{
            "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A,
            "quantity": 1,
        }]
        create_return(order_id=order_id, return_line_items=initial_return_line_items)

        attempted_return_line_items = [{
            "fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A,
            "quantity": 2,
        }]
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyReturnError,
            expected_message=f"Cannot return quantity 2 for line item '{self.ORDER_LINE_ITEM_ID_1A}'. Fulfilled: 2, Already Returned: 1, Available: 1.",
            order_id=order_id,
            return_line_items=attempted_return_line_items
        )

    def test_error_item_not_fulfillable_for_return(self):
        order_id = self.ORDER_ID_4_NO_FULFILLABLE
        return_line_items = [{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_4A, "quantity": 1}]
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyReturnError,
            expected_message=f"Line item '{self.ORDER_LINE_ITEM_ID_4A}' has not been fulfilled and cannot be returned.",
            order_id=order_id,
            return_line_items=return_line_items
        )

    def test_error_order_cancelled_prevents_return(self):
        order_id = self.ORDER_ID_3_CANCELLED
        return_line_items = [{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_3A, "quantity": 1}]
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyReturnError,
            expected_message=f"Order '{self.ORDER_ID_3_CANCELLED}' is cancelled and cannot have items returned.",
            order_id=order_id,
            return_line_items=return_line_items
        )

    def test_error_order_closed_prevents_return(self):
        order_id = self.ORDER_ID_5_CLOSED
        return_line_items = [{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_5A, "quantity": 1}]
        self.assert_error_behavior(
            func_to_call=create_return,
            expected_exception_type=custom_errors.ShopifyReturnError,
            expected_message=f"Order '{self.ORDER_ID_5_CLOSED}' is closed and cannot have items returned.",
            order_id=order_id,
            return_line_items=return_line_items
        )

    def test_return_status_and_name_generation(self):
        order_id = self.ORDER_ID_1
        return_line_items = [{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A, "quantity": 1}]
        result = create_return(order_id=order_id, return_line_items=return_line_items)
        self.assertIn(result["status"], ["OPEN", "REQUESTED"])
        self.assertTrue(result["name"].startswith("#R"))

        db_return = DB['returns'][result['id']]
        self.assertEqual(db_return['status'], result['status'])
        self.assertEqual(db_return['name'], result['name'])

    def test_return_line_item_restock_type_is_optional_in_response(self):
        order_id = self.ORDER_ID_1
        return_line_items = [{"fulfillment_line_item_id": self.ORDER_LINE_ITEM_ID_1A, "quantity": 1}]
        result = create_return(order_id=order_id, return_line_items=return_line_items)
        self.assertIn("restock_type", result["return_line_items"][0])
        if result["return_line_items"][0]["restock_type"] is not None:
            self.assertIn(result["return_line_items"][0]["restock_type"], ["NO_RESTOCK", "CANCEL", "RETURN"])