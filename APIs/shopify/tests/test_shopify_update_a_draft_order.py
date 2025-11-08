import unittest
import copy
from datetime import datetime, timezone
from shopify.draft_orders import shopify_update_a_draft_order
from shopify.SimulationEngine.db import DB
from shopify.SimulationEngine import custom_errors, models
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestUpdateDraftOrder(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        dummy_timestamp_dt = datetime.now(timezone.utc)
        self.dummy_timestamp_str = dummy_timestamp_dt.isoformat()

        # --- Test Data Setup ---
        self.customer1 = models.ShopifyCustomerModel(
            id="cust_1", first_name="John", last_name="Doe", email="john.doe@example.com",
            created_at=self.dummy_timestamp_str, updated_at=self.dummy_timestamp_str
        ).model_dump(mode='json')

        self.customer2 = models.ShopifyCustomerModel(
            id="cust_2", first_name="Jane", last_name="Smith", email="jane.smith@example.com",
            created_at=self.dummy_timestamp_str, updated_at=self.dummy_timestamp_str
        ).model_dump(mode='json')
        
        self.variant1 = {
            "id": "var_1", "product_id": "prod_1", "title": "Small", "price": "10.00", "sku": "SM-01",
            "grams": 100, "inventory_quantity": 10, "requires_shipping": True
        }
        self.variant2 = {
            "id": "var_2", "product_id": "prod_1", "title": "Medium", "price": "15.00", "sku": "MD-01",
            "grams": 150, "inventory_quantity": 5, "requires_shipping": True
        }
        self.product1 = {
            "id": "prod_1", "title": "Test T-Shirt", "vendor": "TestVendor",
            "product_type": "Shirts", "variants": [self.variant1, self.variant2]
        }

        self.line_item1 = {
            "id": "li_1", "variant_id": "var_1", "product_id": "prod_1", "title": "Test T-Shirt - Small",
            "quantity": 1, "price": "10.00", "grams": 100, "sku": "SM-01", "vendor": "TestVendor",
            "requires_shipping": True, "taxable": True, "gift_card": False
        }

        self.shipping_address = {
            "address1": "123 Main St", "city": "Anytown", "province": "CA", "country": "US", "zip": "90210"
        }
        self.billing_address = {
            "address1": "456 Oak Ave", "city": "Anytown", "province": "CA", "country": "US", "zip": "90210"
        }

        self.draft_order1 = {
            "id": "do_1",
            "note": "Initial note",
            "email": self.customer1['email'],
            "total_price": "10.00",
            "subtotal_price": "10.00",
            "customer": self.customer1,
            "line_items": [self.line_item1],
            "shipping_address": self.shipping_address,
            "billing_address": self.billing_address,
            "created_at": self.dummy_timestamp_str,
            "updated_at": self.dummy_timestamp_str,
            "status": "open",
            "tags": "initial, test"
        }

        DB['customers'] = {"cust_1": self.customer1, "cust_2": self.customer2}
        DB['products'] = {"prod_1": self.product1}
        DB['draft_orders'] = {"do_1": copy.deepcopy(self.draft_order1)}

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_update_simple_fields_success(self):
        update_payload = {
            "note": "This is an updated note.",
            "email": "new.email@example.com",
            "tags": "updated, success"
        }
        response = shopify_update_a_draft_order("do_1", update_payload)
        self.assertEqual(response['id'], "do_1")
        self.assertEqual(response['note'], update_payload['note'])
        self.assertEqual(response['email'], update_payload['email'])
        self.assertEqual(response['tags'], update_payload['tags'])
        self.assertNotEqual(response['updated_at'], self.dummy_timestamp_str)

    def test_update_customer_success(self):
        update_payload = {"customer_id": "cust_2"}
        response = shopify_update_a_draft_order("do_1", update_payload)
        self.assertEqual(response['customer']['id'], "cust_2")
        self.assertEqual(response['customer']['email'], self.customer2['email'])

    def test_update_addresses_success(self):
        update_payload = {
            "shipping_address": {"address1": "999 New Shipping St", "city": "Shiptown"},
            "billing_address": {"address1": "111 New Billing Ave", "city": "Billville"}
        }
        response = shopify_update_a_draft_order("do_1", update_payload)
        self.assertEqual(response['shipping_address']['address1'], update_payload['shipping_address']['address1'])
        self.assertEqual(response['shipping_address']['city'], update_payload['shipping_address']['city'])
        self.assertEqual(response['billing_address']['address1'], update_payload['billing_address']['address1'])
        self.assertEqual(response['billing_address']['city'], update_payload['billing_address']['city'])

    def test_update_line_items_success(self):
        update_payload = {
            "line_items": [
                {
                    "id": "li_2", "variant_id": "var_2", "product_id": "prod_1", "quantity": 2, "title":"New Title", "price": "15.00",
                    "requires_shipping": True, "taxable": True, "grams": 150
                }
            ]
        }
        response = shopify_update_a_draft_order("do_1", update_payload)
        self.assertEqual(len(response['line_items']), 1)
        updated_li = response['line_items'][0]
        self.assertEqual(updated_li['variant_id'], "var_2")
        self.assertEqual(updated_li['product_id'], "prod_1")
        self.assertEqual(updated_li['quantity'], 2)

    def test_deep_copy_on_return(self):
        response = shopify_update_a_draft_order("do_1", {"note": "A change"})
        response['note'] = "Modified in test"
        db_order = DB['draft_orders']['do_1']
        self.assertEqual(db_order['note'], "A change")

    def test_error_invalid_draft_order_id(self):
        self.assert_error_behavior(
            shopify_update_a_draft_order, custom_errors.InvalidInputError,
            "Parameter 'draft_order_id' must be a non-empty string.",
            draft_order_id="", draft_order={}
        )
        self.assert_error_behavior(
            shopify_update_a_draft_order, custom_errors.InvalidInputError,
            "Parameter 'draft_order_id' must be a non-empty string.",
            draft_order_id=123, draft_order={}
        )

    def test_error_draft_order_not_found(self):
        self.assert_error_behavior(
            shopify_update_a_draft_order, custom_errors.NotFoundError,
            "Draft order with id 'do_nonexistent' not found.",
            draft_order_id="do_nonexistent", draft_order={"note": "..."}
        )

    def test_error_invalid_payload_type(self):
        self.assert_error_behavior(
            shopify_update_a_draft_order, custom_errors.InvalidInputError,
            "Parameter 'draft_order' must be a dictionary.",
            draft_order_id="do_1", draft_order="not_a_dict"
        )

    def test_error_invalid_field_in_payload(self):
        with self.assertRaises(custom_errors.InvalidInputError) as cm:
            shopify_update_a_draft_order(draft_order_id="do_1", draft_order={"tax_exempt": "not_a_bool"})
        self.assertIn("Invalid draft_order update fields", str(cm.exception))

    def test_error_customer_not_found(self):
        self.assert_error_behavior(
            shopify_update_a_draft_order, custom_errors.NotFoundError,
            "Customer with id 'cust_nonexistent' not found.",
            draft_order_id="do_1", draft_order={"customer_id": "cust_nonexistent"}
        )

    def test_error_product_not_found(self):
        payload = {"line_items": [{"product_id": "prod_nonexistent", "variant_id": "var_1", "quantity": 1, "title": "t", "price": "10.00", "requires_shipping": True, "taxable": True, "grams": 100}]}
        self.assert_error_behavior(
            shopify_update_a_draft_order, custom_errors.NotFoundError,
            "Product with id 'prod_nonexistent' not found.",
            draft_order_id="do_1", draft_order=payload
        )

    def test_error_variant_not_found(self):
        payload = {"line_items": [{"product_id": "prod_1", "variant_id": "var_nonexistent", "quantity": 1, "title": "t", "price": "10.00", "requires_shipping": True, "taxable": True, "grams": 100}]}
        self.assert_error_behavior(
            shopify_update_a_draft_order, custom_errors.NotFoundError,
            "Variant with id 'var_nonexistent' not found in product with id 'prod_1'.",
            draft_order_id="do_1", draft_order=payload
        )
    
    def test_error_line_item_missing_ids(self):
        payload = {"line_items": [{"quantity": 1, "title": "t"}]}
        with self.assertRaises(custom_errors.InvalidInputError) as cm:
            shopify_update_a_draft_order(draft_order_id="do_1", draft_order=payload)
        self.assertIn("Invalid draft_order update fields", str(cm.exception))

    def test_update_with_null_customer(self):
        update_payload = {
            "customer_id": None,
            "note": "Update with null customer"
        }
        response = shopify_update_a_draft_order("do_1", update_payload)
        self.assertIsNone(response['customer'])
        self.assertEqual(response['note'], "Update with null customer")

    def test_error_line_item_missing_variant_id(self):
        payload = {"line_items": [{"product_id": "prod_1", "quantity": 1, "title": "t", "price": "10.00"}]}
        self.assert_error_behavior(
            shopify_update_a_draft_order, custom_errors.InvalidInputError,
            "Both 'product_id' and 'variant_id' are required for each line item.",
            draft_order_id="do_1", draft_order=payload
        )

    def test_error_final_model_validation(self):
        # Directly place an invalid customer object into the draft order in the DB
        # to ensure it bypasses all other logic and fails on final validation.
        self.draft_order1['customer'] = {"id": "cust_1", "email": 12345}
        DB['draft_orders']['do_1'] = self.draft_order1
        
        update_payload = {
            "note": "Trigger final validation"
        }
        with self.assertRaises(custom_errors.InvalidInputError) as cm:
            shopify_update_a_draft_order("do_1", update_payload)
        self.assertIn("Invalid draft_order update fields", str(cm.exception))

    def test_no_customer_in_db_and_no_id_in_payload(self):
        self.draft_order1['customer'] = None
        DB['draft_orders']['do_1'] = self.draft_order1
        response = shopify_update_a_draft_order("do_1", {"note": "No customer"})
        self.assertIsNone(response['customer'])

    def test_error_final_validation_missing_line_item_id(self):
        update_payload = {
            "line_items": [
                {
                    # "id" is missing, which is not allowed by the final model
                    "variant_id": "var_2", 
                    "product_id": "prod_1", 
                    "quantity": 2, 
                    "title":"New Title", 
                    "price": "15.00",
                }
            ]
        }
        with self.assertRaises(custom_errors.InvalidInputError) as cm:
            shopify_update_a_draft_order("do_1", update_payload)
        
        self.assertIn("Invalid draft_order update fields", str(cm.exception))
        self.assertIn("line_items.0.id", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
