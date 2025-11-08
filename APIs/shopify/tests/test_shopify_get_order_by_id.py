import copy
from datetime import datetime, timezone

from shopify.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import custom_errors
from shopify.orders import shopify_get_order_by_id


class TestShopifyGetOrderById(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        self.fixed_time_iso = datetime(2023, 10, 26, 10, 0, 0, tzinfo=timezone.utc).isoformat()
        self.order1_data = {'id': 'order1', 'order_number': 1001, 'name': '#1001', 'created_at': self.fixed_time_iso,
                            'updated_at': self.fixed_time_iso, 'financial_status': 'paid',
                            'fulfillment_status': 'fulfilled', 'currency': 'USD', 'total_price': '199.99',
                            'email': 'customer1@example.com', 'line_items': [
                {'id': 'li1', 'product_id': 'prod_1', 'variant_id': 'var_1_1', 'title': 'Awesome T-Shirt',
                 'quantity': 1, 'price': '25.00', 'sku': 'TSHIRT-AWESOME-S', 'grams': 150,
                 'variant_title': 'Small / Red', 'vendor': 'Some Vendor', 'fulfillment_service': 'manual',
                 'requires_shipping': True, 'taxable': True, 'gift_card': False, 'name': 'Awesome T-Shirt',
                 'properties': [{'name': 'custom_prop', 'value': 'custom_val'}], 'total_discount': '0.00',
                 'fulfillment_status': 'fulfilled'}],
                            'customer': {'id': 'cust_1', 'email': 'customer1@example.com', 'first_name': 'John',
                                         'last_name': 'Doe'}, 'subtotal_price': '175.00', 'total_tax': '24.99',
                            'tags': 'vip, sale', 'admin_graphql_api_id': 'gid://shopify/Order/order1',
                            'cancelled_at': None, 'cancel_reason': None, 'closed_at': None, 'total_weight': 150,
                            'total_discounts': '0.00', 'note': 'Test note', 'token': 'order1_token',
                            'billing_address': {'id': 'addr_bill_1', 'first_name': 'John', 'last_name': 'Doe',
                                                'address1': '123 Billing St', 'city': 'Billville', 'country_code': 'US',
                                                'zip': '12345', 'phone': '555-0100', 'province': 'CA',
                                                'country': 'United States', 'address2': 'Apt 1',
                                                'company': 'Billing Co.', 'latitude': 34.0522, 'longitude': -118.2437,
                                                'province_code': 'CA', 'country_name': 'United States',
                                                'default': False},
                            'shipping_address': {'id': 'addr_ship_1', 'first_name': 'John', 'last_name': 'Doe',
                                                 'address1': '123 Shipping St', 'city': 'Shipville',
                                                 'country_code': 'US', 'zip': '54321', 'phone': '555-0101',
                                                 'province': 'NY', 'country': 'United States', 'address2': 'Suite 2',
                                                 'company': 'Shipping Co.', 'latitude': 40.7128, 'longitude': -74.006,
                                                 'province_code': 'NY', 'country_name': 'United States',
                                                 'default': True}, 'refunds': [], 'transactions': [
                {'id': 'txn_1', 'kind': 'sale', 'status': 'success', 'amount': '199.99',
                 'created_at': self.fixed_time_iso}], 'shipping_lines': [
                {'id': 'sl_1', 'title': 'Standard Shipping', 'price': '10.00', 'code': 'STD_SHIP'}],
                            'tax_lines': [{'title': 'State Tax', 'price': '15.00', 'rate': 0.06}],
                            'discount_codes': [{'code': 'SUMMER10', 'amount': '10.00', 'type': 'fixed_amount'}],
                            'customer_locale': 'en-US', 'referring_site': 'test.com', 'app_id': 'app_12345',
                            'status': 'open', 'processed_at': self.fixed_time_iso}
        self.order2_data_minimal = {'id': 'order2_minimal', 'order_number': 1002, 'name': '#1002',
                                    'created_at': self.fixed_time_iso, 'currency': 'CAD', 'total_price': '50.00',
                                    'line_items': [{'id': 'li2', 'title': 'Basic Item', 'quantity': 2, 'price': '25.00',
                                                    'product_id': None, 'variant_id': None, 'sku': None, 'grams': None,
                                                    'variant_title': None, 'vendor': None, 'fulfillment_service': None,
                                                    'requires_shipping': True, 'taxable': True, 'gift_card': False,
                                                    'name': 'Basic Item', 'properties': [], 'total_discount': '0.00',
                                                    'fulfillment_status': None}], 'updated_at': None,
                                    'financial_status': None, 'fulfillment_status': None, 'email': None,
                                    'customer': None, 'subtotal_price': None, 'total_tax': None, 'tags': '',
                                    'admin_graphql_api_id': None, 'cancelled_at': None, 'cancel_reason': None,
                                    'closed_at': None, 'total_weight': None, 'total_discounts': None, 'note': None,
                                    'token': 'order2_token', 'billing_address': None, 'shipping_address': None,
                                    'refunds': [], 'transactions': [], 'shipping_lines': [], 'tax_lines': [],
                                    'discount_codes': [], 'customer_locale': None, 'referring_site': None,
                                    'app_id': None, 'status': 'open', 'processed_at': None}
        DB['orders'] = {'order1': copy.deepcopy(self.order1_data),
                        'order2_minimal': copy.deepcopy(self.order2_data_minimal)}

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_returned_order_fields(self, retrieved_order, expected_field_keys, all_original_order_data):
        self.assertCountEqual(retrieved_order.keys(), expected_field_keys,
                              'Retrieved order does not have the exact set of expected fields.')
        for key in expected_field_keys:
            self.assertEqual(retrieved_order[key], all_original_order_data[key],
                             f"Field '{key}' mismatch in retrieved order.")

    def test_get_order_success_all_fields(self):
        result = shopify_get_order_by_id(order_id='order1')
        self.assertIsInstance(result, dict)
        self.assertIn('order', result)
        
        # The order should now include fulfillments since it has fulfillment_status 'fulfilled'
        retrieved_order = result['order']
        self.assertIn('fulfillments', retrieved_order)
        self.assertIsInstance(retrieved_order['fulfillments'], list)
        self.assertGreater(len(retrieved_order['fulfillments']), 0)
        
        # Check that the fulfillment has the expected structure
        fulfillment = retrieved_order['fulfillments'][0]
        self.assertIn('id', fulfillment)
        self.assertIn('order_id', fulfillment)
        self.assertIn('line_items', fulfillment)
        self.assertEqual(fulfillment['order_id'], 'order1')
        
        # All other fields should match the original data
        for key, value in self.order1_data.items():
            if key != 'fulfillments':  # Skip fulfillments as we've already checked it
                self.assertEqual(retrieved_order[key], value, f"Field {key} mismatch")

    def test_get_order_success_specific_fields(self):
        fields_to_request = ['id', 'total_price', 'currency', 'name']
        result = shopify_get_order_by_id(order_id='order1', fields=fields_to_request)
        self.assertIsInstance(result, dict)
        self.assertIn('order', result)
        retrieved_order = result['order']
        self._assert_returned_order_fields(retrieved_order, fields_to_request, self.order1_data)

    def test_get_order_success_specific_fields_includes_complex_types(self):
        fields_to_request = ['id', 'line_items', 'customer']
        result = shopify_get_order_by_id(order_id='order1', fields=fields_to_request)
        self.assertIsInstance(result, dict)
        self.assertIn('order', result)
        retrieved_order = result['order']
        self._assert_returned_order_fields(retrieved_order, fields_to_request, self.order1_data)

    def test_get_order_success_empty_fields_list_returns_all_fields(self):
        result = shopify_get_order_by_id(order_id='order1', fields=[])
        self.assertIsInstance(result, dict)
        self.assertIn('order', result)
        
        # The order should now include fulfillments since it has fulfillment_status 'fulfilled'
        retrieved_order = result['order']
        self.assertIn('fulfillments', retrieved_order)
        self.assertIsInstance(retrieved_order['fulfillments'], list)
        self.assertGreater(len(retrieved_order['fulfillments']), 0)
        
        # All other fields should match the original data
        for key, value in self.order1_data.items():
            if key != 'fulfillments':  # Skip fulfillments as we've already checked it
                self.assertEqual(retrieved_order[key], value, f"Field {key} mismatch")

    def test_get_order_not_found_error(self):
        self.assert_error_behavior(func_to_call=shopify_get_order_by_id, expected_exception_type=custom_errors.NotFoundError,
                                   expected_message="Order with ID 'nonexistent_order' not found.",
                                   order_id='nonexistent_order')

    def test_get_order_invalid_order_id_type_raises_validation_error(self):
        self.assert_error_behavior(func_to_call=shopify_get_order_by_id, expected_exception_type=custom_errors.ValidationError,
                                   expected_message='Input should be a valid string', order_id=123)

    def test_get_order_empty_order_id_raises_validation_error(self):
        self.assert_error_behavior(func_to_call=shopify_get_order_by_id, expected_exception_type=custom_errors.ValidationError,
                                   expected_message='Order ID cannot be empty.', order_id='')

    def test_get_order_invalid_fields_type_raises_validation_error(self):
        self.assert_error_behavior(func_to_call=shopify_get_order_by_id, expected_exception_type=custom_errors.ValidationError,
                                   expected_message='Input should be a valid list', order_id='order1', fields='id,name')

    def test_get_order_invalid_fields_content_type_raises_validation_error(self):
        self.assert_error_behavior(func_to_call=shopify_get_order_by_id, expected_exception_type=custom_errors.ValidationError,
                                   expected_message="All items in 'fields' must be strings.", order_id='order1',
                                   fields=['id', 123])

    def test_get_order_fields_includes_non_existent_field_is_ignored(self):
        fields_to_request_with_non_existent = ['id', 'non_existent_field', 'total_price']
        result = shopify_get_order_by_id(order_id='order1', fields=fields_to_request_with_non_existent)
        self.assertIsInstance(result, dict)
        self.assertIn('order', result)
        retrieved_order = result['order']
        expected_existing_fields = ['id', 'total_price']
        self._assert_returned_order_fields(retrieved_order, expected_existing_fields, self.order1_data)

    def test_get_order_success_minimal_data_all_fields(self):
        result = shopify_get_order_by_id(order_id='order2_minimal')
        self.assertIsInstance(result, dict)
        self.assertIn('order', result)
        
        # This order has fulfillment_status None, so it shouldn't have fulfillments
        retrieved_order = result['order']
        self.assertNotIn('fulfillments', retrieved_order)
        
        # All other fields should match the original data
        self.assertEqual(retrieved_order, self.order2_data_minimal)

    def test_get_order_success_minimal_data_specific_fields(self):
        fields_to_request = ['id', 'currency', 'total_price']
        result = shopify_get_order_by_id(order_id='order2_minimal', fields=fields_to_request)
        self.assertIsInstance(result, dict)
        self.assertIn('order', result)
        retrieved_order = result['order']
        self._assert_returned_order_fields(retrieved_order, fields_to_request, self.order2_data_minimal)

    def test_get_order_specific_field_is_none_in_db(self):
        fields_to_request = ['id', 'financial_status', 'customer']
        result = shopify_get_order_by_id(order_id='order2_minimal', fields=fields_to_request)
        self.assertIsInstance(result, dict)
        self.assertIn('order', result)
        retrieved_order = result['order']
        self._assert_returned_order_fields(retrieved_order, fields_to_request, self.order2_data_minimal)

    def test_get_order_fields_with_duplicate_names_processed_correctly(self):
        fields_to_request_with_duplicates = ['id', 'name', 'id', 'currency', 'name']
        result = shopify_get_order_by_id(order_id='order1', fields=fields_to_request_with_duplicates)
        self.assertIsInstance(result, dict)
        self.assertIn('order', result)
        retrieved_order = result['order']
        expected_unique_fields = ['id', 'name', 'currency']
        self._assert_returned_order_fields(retrieved_order, expected_unique_fields, self.order1_data)
