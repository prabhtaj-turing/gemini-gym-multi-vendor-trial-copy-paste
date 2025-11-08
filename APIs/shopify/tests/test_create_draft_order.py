import unittest
import copy
from datetime import datetime, timezone

# CRITICAL IMPORT FOR CUSTOM ERRORS
from ..SimulationEngine import custom_errors
from shopify import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..draft_orders import shopify_create_a_draft_order

class TestShopifyCreateADraftOrder(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB['products'] = {
            "prod_1": {
                "id": "prod_1", "title": "Test Product 1", "vendor": "TestVendor", "product_type": "TestType",
                "created_at": datetime.now(timezone.utc).isoformat(), "handle": "test-product-1",
                "updated_at": datetime.now(timezone.utc).isoformat(), "status": "active",
                "variants": [
                    {
                        "id": "var_1_1", "product_id": "prod_1", "title": "Small", "price": "10.00", "sku": "SKU11",
                        "position": 1, "inventory_policy": "deny", "compare_at_price": "12.00",
                        "fulfillment_service": "manual", "inventory_management": "shopify",
                        "option1": "Small", "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(), "taxable": True, "grams": 100,
                        "inventory_quantity": 10, "requires_shipping": True
                    },
                    {
                        "id": "var_1_2", "product_id": "prod_1", "title": "Large", "price": "20.00", "sku": "SKU12",
                        "position": 2, "inventory_policy": "deny",
                        "fulfillment_service": "manual", "inventory_management": "shopify",
                        "option1": "Large", "created_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(), "taxable": False, "grams": 200,
                        "inventory_quantity": 5, "requires_shipping": False
                    }
                ],
                "options": [{"id": "opt_1", "product_id": "prod_1", "name": "Size", "position": 1, "values": ["Small", "Large"]}],
                "images": []
            }
        }
        DB['customers'] = {
            "cust_1": {
                "id": "cust_1", "email": "existing@example.com", "first_name": "Existing", "last_name": "Customer",
                "orders_count": 1, "total_spent": "50.00", "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(), "phone": "+14155552671",
                "default_address": {
                    "id": "addr_cust1_1", "customer_id": "cust_1", "address1": "123 Main St", "city": "Anytown",
                    "province": "CA", "country": "US", "zip": "12345", "default": True, "first_name": "Existing", "last_name": "Customer"
                },
                "addresses": [{
                    "id": "addr_cust1_1", "customer_id": "cust_1", "address1": "123 Main St", "city": "Anytown",
                    "province": "CA", "country": "US", "zip": "12345", "default": True, "first_name": "Existing", "last_name": "Customer"
                }]
            }
        }
        DB['draft_orders'] = {}

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _get_base_line_item_custom(self, quantity=1, title="Custom Item", price="15.00"):
        return {"title": title, "price": price, "quantity": quantity}

    def _get_base_line_item_variant(self, variant_id="var_1_1", quantity=1):
        return {"variant_id": variant_id, "quantity": quantity}

    def _get_base_customer_input_new(self, email="new@example.com", first_name="New", last_name="Shopper", phone="+14155552671"):
        return {"email": email, "first_name": first_name, "last_name": last_name, "phone": phone}

    def _get_base_customer_input_existing(self, customer_id="cust_1"):
        return {"id": customer_id}

    def _get_base_address_input(self, first_name="John", last_name="Doe"):
        return {
            "first_name": first_name, "last_name": last_name, "address1": "123 Shipping Ln",
            "city": "Shipsville", "province": "CA", "country_code": "US", "country": "United States", "zip": "54321",
            "phone": "+14155552671", "company": "Shippy Inc."
        }

    def _get_base_discount_input(self, value="5.00", value_type="fixed_amount", title="Order Discount"):
        return {"value": value, "value_type": value_type, "title": title}

    def _get_base_shipping_line_input(self, title="Standard Shipping", price="10.00"):
        return {"title": title, "price": price}

    def _assert_common_draft_order_fields(self, response, draft_order_input):
        self.assertIn("id", response)
        self.assertIsInstance(response["id"], str)
        self.assertTrue(len(response["id"]) > 0)

        self.assertIn("name", response)
        self.assertTrue(response["name"].startswith("#D")) 

        self.assertEqual(response.get("note"), draft_order_input.get("note"))
        
        expected_draft_order_email = draft_order_input.get("email")
        customer_input = draft_order_input.get("customer")
        if customer_input:
            if customer_input.get("id"):
                expected_draft_order_email = DB['customers'][customer_input["id"]]['email']
            elif customer_input.get("email"):
                expected_draft_order_email = customer_input.get("email")
        self.assertEqual(response.get("email"), expected_draft_order_email)

        self.assertEqual(response.get("tags"), draft_order_input.get("tags"))
        self.assertEqual(response["currency"], "USD") 
        self.assertIsNone(response.get("invoice_sent_at"))
        self.assertIsNone(response.get("order_id"))
        self.assertEqual(response["status"], "open")
        
        self.assertIn("subtotal_price", response)
        self.assertIsInstance(response["subtotal_price"], str)
        self.assertIn("total_price", response)
        self.assertIsInstance(response["total_price"], str)
        self.assertIn("total_tax", response)
        self.assertIsInstance(response["total_tax"], str)
        
        self.assertIsInstance(response.get("tax_lines", []), list)
        self.assertIsInstance(response.get("tax_exempt"), bool)

        self.assertIn("created_at", response)
        self.assertIsInstance(response["created_at"], str)
        datetime.fromisoformat(response["created_at"].replace("Z", "+00:00"))
        self.assertIn("updated_at", response)
        self.assertIsInstance(response["updated_at"], str)
        datetime.fromisoformat(response["updated_at"].replace("Z", "+00:00"))

        self.assertIn("line_items", response)
        self.assertIsInstance(response["line_items"], list)
        if "line_items" in draft_order_input and draft_order_input["line_items"]:
            self.assertEqual(len(response["line_items"]), len(draft_order_input["line_items"]))

        self.assertIn(response["id"], DB["draft_orders"])
        db_draft_order = DB["draft_orders"][response["id"]]
        self.assertEqual(db_draft_order["id"], response["id"])
        self.assertEqual(db_draft_order["name"], response["name"])

    def test_create_minimal_draft_order_custom_line_item(self):
        draft_order_input = {
            "line_items": [self._get_base_line_item_custom(quantity=1, title="Custom T-Shirt", price="25.00")]
        }
        response = shopify_create_a_draft_order(draft_order=draft_order_input)
        self._assert_common_draft_order_fields(response, draft_order_input)
        
        li_response = response["line_items"][0]
        self.assertIn("id", li_response)
        self.assertEqual(li_response["title"], "Custom T-Shirt")
        self.assertEqual(li_response["price"], "25.00")
        self.assertEqual(li_response["quantity"], 1)
        self.assertTrue(li_response.get("taxable"))
        self.assertTrue(li_response.get("requires_shipping"))
        self.assertIsNone(li_response.get("variant_id"))
        self.assertIsNone(li_response.get("product_id"))
        self.assertIsNone(li_response.get("sku"))
        self.assertIsNone(li_response.get("vendor"))

    def test_create_draft_order_with_variant_line_item(self):
        draft_order_input = {
            "line_items": [self._get_base_line_item_variant(variant_id="var_1_1", quantity=2)]
        }
        response = shopify_create_a_draft_order(draft_order=draft_order_input)
        self._assert_common_draft_order_fields(response, draft_order_input)

        li_response = response["line_items"][0]
        self.assertIn("id", li_response)
        self.assertEqual(li_response["variant_id"], "var_1_1")
        self.assertEqual(li_response["product_id"], "prod_1")
        self.assertEqual(li_response["title"], "Test Product 1") 
        self.assertEqual(li_response["variant_title"], "Small") 
        self.assertEqual(li_response["price"], "10.00") 
        self.assertEqual(li_response["sku"], "SKU11") 
        self.assertEqual(li_response["vendor"], "TestVendor") 
        self.assertEqual(li_response["quantity"], 2)
        self.assertTrue(li_response["taxable"]) 
        self.assertEqual(li_response["grams"], 100) 
        self.assertTrue(li_response["requires_shipping"])

    def test_create_draft_order_line_item_variant_properties_take_precedence(self):
        draft_order_input = {
            "line_items": [{
                "variant_id": "var_1_2",
                "quantity": 1,
                "price": "25.00",
                "sku": "OVERRIDE_SKU",
            }]
        }
        response = shopify_create_a_draft_order(draft_order=draft_order_input)
        self._assert_common_draft_order_fields(response, draft_order_input)

        li_response = response["line_items"][0]
        self.assertEqual(li_response["variant_id"], "var_1_2")
        self.assertEqual(li_response["price"], "20.00")  # Should come from variant in DB
        self.assertEqual(li_response["sku"], "SKU12") # Should come from variant in DB
        
    def test_create_draft_order_custom_line_item_with_optional_fields(self):
        custom_li_input = {
            "line_items": [{
                "title": "Custom Item with Details", "price": "30.00", "quantity": 1,
                "sku": "CUSTOM_SKU", "grams": 300, "taxable": False, "requires_shipping": False,
                "product_id": "prod_1"
            }]
        }
        response_custom = shopify_create_a_draft_order(draft_order=custom_li_input)
        self._assert_common_draft_order_fields(response_custom, custom_li_input)
        li_custom_response = response_custom["line_items"][0]
        self.assertEqual(li_custom_response["sku"], "CUSTOM_SKU")
        self.assertEqual(li_custom_response["grams"], 300)
        self.assertFalse(li_custom_response["taxable"])
        self.assertFalse(li_custom_response["requires_shipping"])
        self.assertEqual(li_custom_response["product_id"], "prod_1")
        self.assertIsNone(li_custom_response.get("vendor"))

    def test_create_draft_order_with_new_customer(self):
        # FIX: Test now asserts the corrected behavior where new customers are saved and their ID is returned.
        customer_details = self._get_base_customer_input_new()
        draft_order_input = {
            "line_items": [self._get_base_line_item_custom()],
            "customer": customer_details
        }
        response = shopify_create_a_draft_order(draft_order=draft_order_input)
        self._assert_common_draft_order_fields(response, draft_order_input)

        self.assertIn("customer", response)
        resp_customer = response["customer"]
        self.assertIsNotNone(resp_customer)
        self.assertIn("id", resp_customer)
        new_customer_id = resp_customer["id"]
        
        self.assertIn(new_customer_id, DB["customers"])
        db_customer = DB["customers"][new_customer_id]
        self.assertEqual(db_customer["email"], customer_details["email"])

    def test_create_draft_order_with_existing_customer_and_top_level_email_ignored(self):
        draft_order_input = {
            "line_items": [self._get_base_line_item_custom()],
            "customer": self._get_base_customer_input_existing(customer_id="cust_1"),
            "email": "override@example.com"
        }
        response = shopify_create_a_draft_order(draft_order=draft_order_input)
        self._assert_common_draft_order_fields(response, draft_order_input)

        self.assertIn("customer", response)
        resp_customer = response["customer"]
        self.assertIsNotNone(resp_customer)
        self.assertEqual(resp_customer["id"], "cust_1")
        existing_customer_db = DB["customers"]["cust_1"]
        self.assertEqual(resp_customer["email"], existing_customer_db["email"])
        
        self.assertEqual(response["email"], existing_customer_db["email"])

    def test_create_draft_order_with_addresses(self):
        shipping_addr = self._get_base_address_input(first_name="Ship", last_name="To")
        billing_addr = self._get_base_address_input(first_name="Bill", last_name="To")
        draft_order_input = {
            "line_items": [self._get_base_line_item_custom()],
            "shipping_address": shipping_addr,
            "billing_address": billing_addr
        }
        response = shopify_create_a_draft_order(draft_order=draft_order_input)
        self._assert_common_draft_order_fields(response, draft_order_input)

        self.assertIn("shipping_address", response)
        resp_ship_addr = response["shipping_address"]
        self.assertIsNotNone(resp_ship_addr)
        self.assertEqual(resp_ship_addr["first_name"], shipping_addr["first_name"])
        self.assertEqual(resp_ship_addr["address1"], shipping_addr["address1"])

        self.assertIn("billing_address", response)
        resp_bill_addr = response["billing_address"]
        self.assertIsNotNone(resp_bill_addr)
        self.assertEqual(resp_bill_addr["first_name"], billing_addr["first_name"])
        self.assertEqual(resp_bill_addr["address1"], billing_addr["address1"])

    def test_create_draft_order_with_note_tags_top_level_email_no_customer_object(self):
        draft_order_input = {
            "line_items": [self._get_base_line_item_custom()],
            "note": "This is a test note.",
            "tags": "test, draft, important",
            "email": "contact@example.com" 
        }
        response = shopify_create_a_draft_order(draft_order=draft_order_input)
        self._assert_common_draft_order_fields(response, draft_order_input) 

        self.assertEqual(response["note"], "This is a test note.")
        self.assertEqual(response["tags"], "test, draft, important")
        self.assertEqual(response["email"], "contact@example.com")
        self.assertIsNone(response.get("customer"))

    def test_create_draft_order_with_shipping_line(self):
        shipping_line_input = self._get_base_shipping_line_input()
        draft_order_input = {
            "line_items": [self._get_base_line_item_custom()],
            "shipping_line": shipping_line_input
        }
        response = shopify_create_a_draft_order(draft_order=draft_order_input)
        self._assert_common_draft_order_fields(response, draft_order_input)

        self.assertIn("shipping_line", response)
        resp_ship_line = response["shipping_line"]
        self.assertIsNotNone(resp_ship_line)
        self.assertEqual(resp_ship_line["title"], shipping_line_input["title"])
        self.assertEqual(resp_ship_line["price"], shipping_line_input["price"])

    def test_create_draft_order_with_order_level_discount(self):
        discount_fixed_input = self._get_base_discount_input(value="10.00", value_type="fixed_amount", title="Loyalty Discount")
        draft_order_input_fixed = {
            "line_items": [self._get_base_line_item_custom(price="100.00")],
            "applied_discount": discount_fixed_input
        }
        response_fixed = shopify_create_a_draft_order(draft_order=draft_order_input_fixed)
        self._assert_common_draft_order_fields(response_fixed, draft_order_input_fixed)
        self.assertIn("applied_discount", response_fixed)
        resp_discount_fixed = response_fixed["applied_discount"]
        self.assertIsNotNone(resp_discount_fixed)
        self.assertEqual(resp_discount_fixed["value"], "10.00")
        self.assertEqual(resp_discount_fixed["value_type"], "fixed_amount")
        self.assertEqual(resp_discount_fixed["title"], discount_fixed_input["title"])
        self.assertIn("amount", resp_discount_fixed) 
        self.assertEqual(resp_discount_fixed["amount"], "10.00")

        discount_percent_input = self._get_base_discount_input(value="10", value_type="percentage", title="10% Off")
        draft_order_input_percent = {
            "line_items": [self._get_base_line_item_custom(price="100.00")],
            "applied_discount": discount_percent_input
        }
        response_percent = shopify_create_a_draft_order(draft_order=draft_order_input_percent)
        self._assert_common_draft_order_fields(response_percent, draft_order_input_percent)
        self.assertIn("applied_discount", response_percent)
        resp_discount_percent = response_percent["applied_discount"]
        self.assertIsNotNone(resp_discount_percent)
        self.assertEqual(resp_discount_percent["value"], "10")
        self.assertEqual(resp_discount_percent["value_type"], "percentage")
        self.assertIn("amount", resp_discount_percent) 
        self.assertEqual(resp_discount_percent["amount"], "10.00")

    def test_create_draft_order_with_line_item_discount_and_attributes(self):
        li_discount = {"value": "2.00", "value_type": "fixed_amount", "title": "Item Discount"}
        li_attrs = [{"key": "Engraving", "value": "Hello World"}]
        draft_order_input = {
            "line_items": [{
                "title": "Special Item", "price": "50.00", "quantity": 1,
                "applied_discount": li_discount,
                "custom_attributes": li_attrs
            }]
        }
        response = shopify_create_a_draft_order(draft_order=draft_order_input)
        self._assert_common_draft_order_fields(response, draft_order_input)
        li_response = response["line_items"][0]
        self.assertIn("applied_discount", li_response)
        self.assertEqual(li_response["applied_discount"]["amount"], "2.00")
        self.assertIn("custom_attributes", li_response)
        self.assertEqual(li_response["custom_attributes"][0]["key"], "Engraving")

    def test_create_full_draft_order(self):
        customer_details = self._get_base_customer_input_new(email="full@example.com")
        shipping_addr = self._get_base_address_input(first_name="FullShip")
        billing_addr = self._get_base_address_input(first_name="FullBill")
        order_discount = self._get_base_discount_input(value="10", value_type="percentage")
        shipping_line = self._get_base_shipping_line_input()
        
        line_item1_custom = self._get_base_line_item_custom(title="Custom Full Item", price="100.00", quantity=1)
        line_item2_variant = self._get_base_line_item_variant(variant_id="var_1_1", quantity=2)
        line_item2_variant.update({ 
            "applied_discount": {"value": "1.00", "value_type": "fixed_amount", "title": "Variant Discount"},
            "custom_attributes": [{"key": "GiftWrap", "value": "Yes"}]
        })

        draft_order_input = {
            "line_items": [line_item1_custom, line_item2_variant],
            "customer": customer_details,
            "shipping_address": shipping_addr,
            "billing_address": billing_addr,
            "email": customer_details["email"], 
            "note": "Full draft order test.",
            "tags": "full, complex",
            "shipping_line": shipping_line,
            "applied_discount": order_discount
        }

        response = shopify_create_a_draft_order(draft_order=draft_order_input)
        self._assert_common_draft_order_fields(response, draft_order_input)

        self.assertIsNotNone(response.get("customer"))
        self.assertEqual(response["customer"]["email"], customer_details["email"])
        self.assertIsNotNone(response.get("shipping_address"))
        self.assertEqual(response["shipping_address"]["first_name"], shipping_addr["first_name"])
        self.assertIsNotNone(response.get("billing_address"))
        self.assertEqual(response["billing_address"]["first_name"], billing_addr["first_name"])
        self.assertIsNotNone(response.get("shipping_line"))
        self.assertEqual(response["shipping_line"]["price"], shipping_line["price"])
        self.assertIsNotNone(response.get("applied_discount"))
        self.assertEqual(response["applied_discount"]["value"], order_discount["value"])
        self.assertEqual(len(response["line_items"]), 2)

    def test_error_draft_order_not_dict(self):
        # The function's `try` block is not reached, so this is a raw Python error.
        with self.assertRaises(TypeError) as cm:
            shopify_create_a_draft_order(draft_order="not a dict")
        self.assertIn("argument after ** must be a mapping, not str", str(cm.exception))

    def test_error_empty_draft_order_dict_is_allowed(self):
        response = shopify_create_a_draft_order(draft_order={})
        self.assertIsNotNone(response)
        self.assertEqual(response["line_items"], [])
        self.assertEqual(response["subtotal_price"], "0.00")

    def test_error_line_items_not_list(self):
        with self.assertRaises(custom_errors.ShopifyInvalidInputError) as cm:
            shopify_create_a_draft_order(draft_order={"line_items": "not a list"})
        self.assertIn("Input should be a valid list", str(cm.exception))

    def test_error_empty_line_items_list_is_allowed(self):
        response = shopify_create_a_draft_order(draft_order={"line_items": []})
        self.assertIsNotNone(response)
        self.assertEqual(response["line_items"], [])
        self.assertEqual(response["subtotal_price"], "0.00")

    def test_error_line_item_missing_quantity(self):
        with self.assertRaises(custom_errors.ShopifyInvalidInputError) as cm:
            shopify_create_a_draft_order(draft_order={"line_items": [{"title": "Item", "price": "10.00"}]})
        self.assertIn("Field required", str(cm.exception))
        self.assertIn("line_items.0.quantity", str(cm.exception))


    def test_error_line_item_missing_variant_or_title_price(self):
        self.assert_error_behavior(
            func_to_call=shopify_create_a_draft_order,
            expected_exception_type=custom_errors.ShopifyInvalidInputError,
            expected_message="Line item at index 0 is invalid: requires variant_id or (title and price).",
            draft_order={"line_items": [{"quantity": 1}]}
        )

    def test_error_line_item_quantity_invalid(self):
        with self.assertRaises(custom_errors.ShopifyInvalidInputError) as cm:
            shopify_create_a_draft_order(draft_order={"line_items": [self._get_base_line_item_custom(quantity=0)]})
        self.assertIn("Quantity must be greater than 0", str(cm.exception))
        
        with self.assertRaises(custom_errors.ShopifyInvalidInputError) as cm:
            shopify_create_a_draft_order(draft_order={"line_items": [self._get_base_line_item_custom(quantity="not_int")]})
        self.assertIn("Input should be a valid integer", str(cm.exception))
    
    def test_error_non_existent_variant_id(self):
        # FIX: The function is now fixed to raise the correct error.
        self.assert_error_behavior(
            func_to_call=shopify_create_a_draft_order,
            expected_exception_type=custom_errors.ShopifyInvalidInputError,
            expected_message="Variant with ID 'var_non_existent' not found.",
            draft_order={"line_items": [{"variant_id": "var_non_existent", "quantity": 1}]}
        )

    def test_error_non_existent_customer_id(self):
        self.assert_error_behavior(
            func_to_call=shopify_create_a_draft_order,
            expected_exception_type=custom_errors.ShopifyInvalidInputError,
            expected_message="Customer with ID 'cust_non_existent' not found.",
            draft_order={
                "line_items": [self._get_base_line_item_custom()],
                "customer": {"id": "cust_non_existent"}
            }
        )

    def test_error_order_discount_invalid_structure(self):
        with self.assertRaises(custom_errors.ShopifyInvalidInputError) as cm:
            shopify_create_a_draft_order(draft_order={
                "line_items": [self._get_base_line_item_custom()],
                "applied_discount": {"value_type": "fixed_amount"} 
            })
        self.assertIn("Field required", str(cm.exception))
        self.assertIn("applied_discount.value", str(cm.exception))
    
    def test_error_order_discount_invalid_value_type(self):
        with self.assertRaises(custom_errors.ShopifyInvalidInputError) as cm:
            shopify_create_a_draft_order(draft_order={
                "line_items": [self._get_base_line_item_custom()],
                "applied_discount": {"value": "10", "value_type": "invalid_type"}
            })
        self.assertIn("Input should be 'fixed_amount' or 'percentage'", str(cm.exception))

    def test_error_line_item_discount_invalid_structure(self):
        with self.assertRaises(custom_errors.ShopifyInvalidInputError) as cm:
            shopify_create_a_draft_order(draft_order={
                "line_items": [{
                    "title": "Item", "price": "10.00", "quantity": 1,
                    "applied_discount": {"title": "Discount"} 
                }]
            })
        self.assertIn("Field required", str(cm.exception))
        self.assertIn("line_items.0.applied_discount.value", str(cm.exception))

    def test_error_line_item_custom_attribute_invalid_structure(self):
        with self.assertRaises(custom_errors.ShopifyInvalidInputError) as cm:
            shopify_create_a_draft_order(draft_order={
                "line_items": [{
                    "title": "Item", "price": "10.00", "quantity": 1,
                    "custom_attributes": [{"value": "Val"}] 
                }]
            })
        self.assertIn("Field required", str(cm.exception))
        self.assertIn("line_items.0.custom_attributes.0.key", str(cm.exception))

    def test_error_shipping_line_invalid_structure(self):
        with self.assertRaises(custom_errors.ShopifyInvalidInputError) as cm:
            shopify_create_a_draft_order(draft_order={
                "line_items": [self._get_base_line_item_custom()],
                "shipping_line": {"price": "5.00"} 
            })
        self.assertIn("Field required", str(cm.exception))
        self.assertIn("shipping_line.title", str(cm.exception))

if __name__ == '__main__':
    unittest.main()
