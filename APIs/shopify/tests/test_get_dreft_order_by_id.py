import unittest
import copy
from datetime import datetime, timezone

# CRITICAL IMPORT FOR CUSTOM ERRORS
from ..SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..draft_orders import shopify_get_draft_order_by_id as get_draft_order_by_id
from shopify import DB

# Globals DB, shopify_get_draft_order_by_id, BaseTestCaseWithErrorHandler are assumed to be available
# in the test execution environment.

class TestShopifyGetDraftOrderById(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.fixed_timestamp = datetime(2023, 10, 26, 12, 0, 0, tzinfo=timezone.utc)
        self.fixed_timestamp_iso = self.fixed_timestamp.isoformat()

        self.draft_order_1_id = "do_123"
        # Data as it would be stored in DB (with datetime objects)
        self.draft_order_1_db_data = {
            "id": self.draft_order_1_id,
            "admin_graphql_api_id": f"gid://shopify/DraftOrder/{self.draft_order_1_id}",
            "name": "#D101",
            "status": "open",
            "email": "customer1@example.com",
            "currency": "USD",
            "note": "Test note for DO1",
            "created_at": self.fixed_timestamp_iso,
            "updated_at": self.fixed_timestamp_iso,
            "invoice_sent_at": self.fixed_timestamp_iso,
            "invoice_url": f"https://shop.example.com/invoice/{self.draft_order_1_id}",
            "order_id": "order_linked_123",
            "customer": {
                "id": "cust_abc",
                "email": "customer1@example.com",
                "first_name": "John",
                "last_name": "Doe",
            },
            "line_items": [
                {
                    "product_id": "prod_tshirt", "variant_id": "var_tshirt_s_red", "title": "Premium Shirt",
                    "quantity": 2, "price": "60.00", "applied_discount": None
                },
                {
                    "product_id": "prod_mug", "variant_id": None, "title": "Basic Mug",
                    "quantity": 1, "price": "10.00", 
                    "applied_discount": {"title": "Special Offer", "value": "1.00", "value_type": "fixed_amount", "amount": "1.00"}
                }
            ],
            "shipping_address": {
                "id": "addr_ship_1", "customer_id": "cust_abc",
                "address1": "123 Shipping Ln", "address2": "Apt B", "city": "Shipsville",
                "province": "CA", "country": "US", "zip": "90210",
                "phone": "555-1234", "first_name": "John", "last_name": "Doe",
                "province_code": "CA", "country_code": "US", "country_name": "United States",
                "company": "JD Shipping Co", "latitude": 34.0522, "longitude": -118.2437, "default": False
            },
            "shipping_line": { "title": "Express Shipping", "price": "10.00" },
            "applied_discount": {
                "title": "Grand Opening Sale", "description": "Special discount",
                "value": "5.00", "value_type": "fixed_amount", "amount": "5.00"
            },
            # Consistent pricing:
            # Line Item 1: 2 * 60.00 = 120.00
            # Line Item 2: 1 * 10.00 = 10.00, with discount of 1.00. Effective price = 9.00
            # Subtotal Price = 120.00 + 9.00 = 129.00
            "subtotal_price": "129.00",
            # Order Discount = 5.00
            # Price before tax and shipping, after order discount = 129.00 - 5.00 = 124.00
            # Shipping = 10.00
            # Amount before tax = 124.00 + 10.00 = 134.00
            # Total Tax = 15.00 (example)
            "total_tax": "15.00",
            # Total Price = 134.00 + 15.00 = 149.00
            "total_price": "149.00",
        }

        # Expected output version with ISO date strings
        self.draft_order_1_expected_output = copy.deepcopy(self.draft_order_1_db_data)

        self.draft_order_minimal_id = "do_min_456"
        self.draft_order_minimal_db_data = {
            "id": self.draft_order_minimal_id,
            "admin_graphql_api_id": f"gid://shopify/DraftOrder/{self.draft_order_minimal_id}",
            "name": "#DMinimal", "status": "completed", "email": "minimal@example.com", "currency": "EUR",
            "note": None,
            "created_at": self.fixed_timestamp_iso,
            "updated_at": self.fixed_timestamp_iso,
            "invoice_sent_at": None, "invoice_url": None,
            "order_id": "order_from_minimal_draft",
            "total_price": "75.00", "subtotal_price": "70.00", "total_tax": "5.00",
            "customer": { "id": "cust_xyz", "email": "minimal@example.com", "first_name": "Mini", "last_name": "Malist" },
            "line_items": [{
                "product_id": "prod_simple", "variant_id": "var_simple_any", "title": "Simple Item",
                "quantity": 1, "price": "70.00", "applied_discount": None
            }],
            "shipping_address": None, "shipping_line": None, "applied_discount": None
        }
        self.draft_order_minimal_expected_output = copy.deepcopy(self.draft_order_minimal_db_data)
        self.draft_order_minimal_expected_output["created_at"] = self.fixed_timestamp_iso
        self.draft_order_minimal_expected_output["updated_at"] = self.fixed_timestamp_iso

        DB['draft_orders'] = {
            self.draft_order_1_id: copy.deepcopy(self.draft_order_1_db_data),
            self.draft_order_minimal_id: copy.deepcopy(self.draft_order_minimal_db_data)
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_get_draft_order_by_id_success_all_fields(self):
        draft_order = get_draft_order_by_id(draft_order_id=self.draft_order_1_id)
        
        self.assertEqual(draft_order, self.draft_order_1_expected_output)
        self.assertEqual(draft_order['id'], self.draft_order_1_id)
        self.assertEqual(draft_order['name'], self.draft_order_1_expected_output['name'])
        self.assertEqual(draft_order['created_at'], self.fixed_timestamp_iso)
        self.assertIsNotNone(draft_order['customer'])
        self.assertEqual(draft_order['customer']['first_name'], "John")
        self.assertEqual(len(draft_order['line_items']), 2)
        self.assertIsNotNone(draft_order['shipping_address'])
        self.assertIsNotNone(draft_order['shipping_line'])
        self.assertIsNotNone(draft_order['applied_discount'])

    def test_get_draft_order_by_id_success_minimal_data_all_fields(self):
        draft_order = get_draft_order_by_id(draft_order_id=self.draft_order_minimal_id)
        
        self.assertEqual(draft_order, self.draft_order_minimal_expected_output)
        self.assertEqual(draft_order['id'], self.draft_order_minimal_id)
        self.assertIsNone(draft_order['note'])
        self.assertIsNone(draft_order['shipping_address'])
        self.assertIsNone(draft_order['shipping_line'])
        self.assertIsNone(draft_order['applied_discount'])
        self.assertIsNotNone(draft_order['order_id'])

    def test_get_draft_order_by_id_success_specific_fields(self):
        fields_to_request = ["id", "name", "status", "customer", "created_at"]
        draft_order = get_draft_order_by_id(
            draft_order_id=self.draft_order_1_id,
            fields=fields_to_request
        )
        
        self.assertEqual(len(draft_order.keys()), len(fields_to_request))
        for field in fields_to_request:
            self.assertIn(field, draft_order)
            self.assertEqual(draft_order[field], self.draft_order_1_expected_output[field])
        
        self.assertNotIn('currency', draft_order)
        self.assertNotIn('line_items', draft_order)

    def test_get_draft_order_by_id_success_empty_fields_list_returns_all(self):
        draft_order = get_draft_order_by_id(draft_order_id=self.draft_order_1_id, fields=[])
        self.assertEqual(draft_order, self.draft_order_1_expected_output)

    def test_get_draft_order_by_id_success_fields_with_unknown_field_ignored(self):
        fields_to_request = ["id", "name", "non_existent_field"]
        draft_order = get_draft_order_by_id(
            draft_order_id=self.draft_order_1_id,
            fields=fields_to_request
        )
        self.assertIn('id', draft_order)
        self.assertIn('name', draft_order)
        self.assertNotIn('non_existent_field', draft_order)
        self.assertEqual(len(draft_order.keys()), 2) 

    def test_get_draft_order_by_id_success_fields_with_duplicates(self):
        fields_to_request = ["id", "name", "id", "status", "name"]
        draft_order = get_draft_order_by_id(
            draft_order_id=self.draft_order_1_id,
            fields=fields_to_request
        )
        self.assertEqual(len(draft_order.keys()), 3) 
        self.assertIn('id', draft_order)
        self.assertIn('name', draft_order)
        self.assertIn('status', draft_order)
        self.assertEqual(draft_order['id'], self.draft_order_1_expected_output['id'])
        self.assertEqual(draft_order['name'], self.draft_order_1_expected_output['name'])
        self.assertEqual(draft_order['status'], self.draft_order_1_expected_output['status'])

    def test_get_draft_order_by_id_specific_field_is_none(self):
        fields_to_request = ["id", "note", "invoice_sent_at"] 
        draft_order = get_draft_order_by_id(
            draft_order_id=self.draft_order_minimal_id,
            fields=fields_to_request
        )
        self.assertEqual(len(draft_order.keys()), 3)
        self.assertEqual(draft_order['id'], self.draft_order_minimal_expected_output['id'])
        self.assertIsNone(draft_order['note'])
        self.assertIsNone(draft_order['invoice_sent_at'])

    def test_get_draft_order_by_id_not_found(self):
        self.assert_error_behavior(
            func_to_call=get_draft_order_by_id,
            draft_order_id="non_existent_do_id",
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Draft order with ID 'non_existent_do_id' not found."
        )

    def test_get_draft_order_by_id_invalid_id_type_integer(self):
        self.assert_error_behavior(
            func_to_call=get_draft_order_by_id,
            draft_order_id=12345, 
            expected_exception_type=custom_errors.ValidationError,
            expected_message="draft_order_id must be a non-empty string."
        )

    def test_get_draft_order_by_id_empty_id_string(self):
        self.assert_error_behavior(
            func_to_call=get_draft_order_by_id,
            draft_order_id="",
            expected_exception_type=custom_errors.ValidationError,
            expected_message="draft_order_id must be a non-empty string."
        )

    def test_get_draft_order_by_id_invalid_fields_type_string(self):
        self.assert_error_behavior(
            func_to_call=get_draft_order_by_id,
            draft_order_id=self.draft_order_1_id,
            fields="id,name", 
            expected_exception_type=custom_errors.ValidationError,
            expected_message="fields must be a list of strings or None."
        )

    def test_get_draft_order_by_id_invalid_fields_content_type_int_in_list(self):
        self.assert_error_behavior(
            func_to_call=get_draft_order_by_id,
            draft_order_id=self.draft_order_1_id,
            fields=["id", 123], 
            expected_exception_type=custom_errors.ValidationError,
            expected_message="fields must be a list of strings or None."
        )

    def test_get_draft_order_by_id_internal_data_error_on_missing_required_field(self):
        """
        Tests if an InternalDataError is raised when DB data is corrupt
        and fails Pydantic model validation.
        """
        # Make the data in the DB "corrupt" by removing a required field
        del DB['draft_orders'][self.draft_order_1_id]['name']

        # Expect the function to catch the pydantic.ValidationError and raise our custom internal error
        self.assert_error_behavior(
            func_to_call=get_draft_order_by_id,
            draft_order_id=self.draft_order_1_id,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The data retrieved from the database could not be validated against the response model."
        )

    def test_get_draft_order_when_draft_orders_table_is_missing(self):
        """Tests NotFoundError if the entire 'draft_orders' key is missing from DB."""
        del DB['draft_orders']
        self.assert_error_behavior(
            func_to_call=get_draft_order_by_id,
            draft_order_id=self.draft_order_1_id,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Draft order with ID 'do_123' not found. (Data store not found)"
        )

    def test_get_draft_order_when_order_data_is_not_a_dict(self):
        """Tests NotFoundError if a specific draft order ID points to invalid data type."""
        DB['draft_orders'][self.draft_order_1_id] = "This is not a dictionary"
        self.assert_error_behavior(
            func_to_call=get_draft_order_by_id,
            draft_order_id=self.draft_order_1_id,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Draft order with ID 'do_123' not found."
        )

    def test_data_validation_error_on_missing_nested_required_field(self):
        """Tests validation failure for a required field in a nested object (customer.id)."""
        del DB['draft_orders'][self.draft_order_1_id]['customer']['id']
        self.assert_error_behavior(
            func_to_call=get_draft_order_by_id,
            draft_order_id=self.draft_order_1_id,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The data retrieved from the database could not be validated against the response model."
        )

    def test_data_validation_error_on_incorrect_data_type_in_list(self):
        """Tests validation failure for wrong data type in a nested list (line_items.quantity)."""
        DB['draft_orders'][self.draft_order_1_id]['line_items'][0]['quantity'] = "two" # Should be an int
        self.assert_error_behavior(
            func_to_call=get_draft_order_by_id,
            draft_order_id=self.draft_order_1_id,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The data retrieved from the database could not be validated against the response model."
        )

    def test_data_validation_error_on_list_instead_of_dict(self):
        """Tests validation failure when a nested object is of the wrong container type."""
        DB['draft_orders'][self.draft_order_1_id]['customer'] = ["list", "instead", "of", "dict"]
        self.assert_error_behavior(
            func_to_call=get_draft_order_by_id,
            draft_order_id=self.draft_order_1_id,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The data retrieved from the database could not be validated against the response model."
        )

if __name__ == '__main__':
    unittest.main()