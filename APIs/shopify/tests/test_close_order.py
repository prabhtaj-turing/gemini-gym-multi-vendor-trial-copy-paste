import unittest
import copy
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Optional, Dict, Any
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from ..SimulationEngine.utils import _format_datetime
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..orders import shopify_close_an_order

class TestShopifyCloseAnOrder(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        if 'orders' not in DB:
            DB['orders'] = {}
        self.order_number_counter = 1000
        self.now_iso = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
        self.earlier_iso = (datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=1)).isoformat()
        self.even_earlier_iso = (datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=2)).isoformat()
        self.fulfilled_line_item_shippable_1 = {'id': 'li_s1', 'variant_id': 'v_s1', 'product_id': 'p_s1', 'title': 'Shippable Item 1', 'quantity': 1, 'sku': 'SKU_S1', 'price': '10.00', 'requires_shipping': True, 'taxable': True, 'gift_card': False, 'fulfillment_status': 'fulfilled', 'grams': 100, 'fulfillable_quantity': 0, 'admin_graphql_api_id': 'gid://shopify/LineItem/li_s1', 'name': 'Shippable Item 1', 'variant_title': 'Variant S1', 'vendor': 'Vendor S', 'fulfillment_service': 'manual', 'total_discount': '0.00'}
        self.unfulfilled_line_item_shippable_1 = {'id': 'li_us1', 'variant_id': 'v_us1', 'product_id': 'p_us1', 'title': 'Unfulfilled Shippable Item 1', 'quantity': 1, 'sku': 'SKU_US1', 'price': '20.00', 'requires_shipping': True, 'taxable': True, 'gift_card': False, 'fulfillment_status': None, 'grams': 200, 'fulfillable_quantity': 1, 'admin_graphql_api_id': 'gid://shopify/LineItem/li_us1', 'name': 'Unfulfilled Shippable Item 1', 'variant_title': 'Variant US1', 'vendor': 'Vendor US', 'fulfillment_service': 'manual', 'total_discount': '0.00'}
        self.fulfilled_line_item_non_shippable_1 = {'id': 'li_ns1', 'variant_id': 'v_ns1', 'product_id': 'p_ns1', 'title': 'Non-Shippable Item 1', 'quantity': 1, 'sku': 'SKU_NS1', 'price': '5.00', 'requires_shipping': False, 'taxable': False, 'gift_card': True, 'fulfillment_status': 'fulfilled', 'grams': 0, 'fulfillable_quantity': 0, 'admin_graphql_api_id': 'gid://shopify/LineItem/li_ns1', 'name': 'Non-Shippable Item 1', 'variant_title': 'Variant NS1', 'vendor': 'Vendor NS', 'fulfillment_service': 'manual', 'total_discount': '0.00'}
        DB['orders'] = {
            'order_closable_paid_fulfilled': self._create_base_order(order_id='order_closable_paid_fulfilled', financial_status='paid', fulfillment_status='fulfilled', line_items=[copy.deepcopy(self.fulfilled_line_item_shippable_1)], closed_at=None, cancelled_at=None), 
            'order_closable_refunded_fulfilled': self._create_base_order(order_id='order_closable_refunded_fulfilled', financial_status='refunded', fulfillment_status='fulfilled', line_items=[copy.deepcopy(self.fulfilled_line_item_shippable_1)], closed_at=None, cancelled_at=None), 
            'order_closable_no_shippable_items_paid': self._create_base_order(order_id='order_closable_no_shippable_items_paid', financial_status='paid', fulfillment_status=None, line_items=[copy.deepcopy(self.fulfilled_line_item_non_shippable_1)], closed_at=None, cancelled_at=None), 
            'order_already_closed': self._create_base_order(order_id='order_already_closed', financial_status='paid', fulfillment_status='fulfilled', line_items=[copy.deepcopy(self.fulfilled_line_item_shippable_1)], closed_at=self.earlier_iso, cancelled_at=None), 
            'order_cancelled': self._create_base_order(order_id='order_cancelled', financial_status='voided', fulfillment_status=None, line_items=[copy.deepcopy(self.unfulfilled_line_item_shippable_1)], closed_at=None, cancelled_at=self.earlier_iso, cancel_reason='customer'), 
            'order_pending_fulfillment_partial': self._create_base_order(order_id='order_pending_fulfillment_partial', financial_status='paid', fulfillment_status='partial', line_items=[copy.deepcopy(self.unfulfilled_line_item_shippable_1), copy.deepcopy(self.fulfilled_line_item_shippable_1)], closed_at=None, cancelled_at=None), 
            'order_pending_fulfillment_all_unfulfilled': self._create_base_order(order_id='order_pending_fulfillment_all_unfulfilled', financial_status='paid', fulfillment_status='unfulfilled', line_items=[copy.deepcopy(self.unfulfilled_line_item_shippable_1)], closed_at=None, cancelled_at=None), 
            'order_unsuitable_financial_pending': self._create_base_order(order_id='order_unsuitable_financial_pending', financial_status='pending', fulfillment_status='fulfilled', line_items=[copy.deepcopy(self.fulfilled_line_item_shippable_1)], closed_at=None, cancelled_at=None), 
            'order_unsuitable_financial_partially_paid': self._create_base_order(order_id='order_unsuitable_financial_partially_paid', financial_status='partially_paid', fulfillment_status='fulfilled', line_items=[copy.deepcopy(self.fulfilled_line_item_shippable_1)], closed_at=None, cancelled_at=None), 
            'order_unsuitable_financial_none': self._create_base_order(order_id='order_unsuitable_financial_none', financial_status=None, fulfillment_status='fulfilled', line_items=[copy.deepcopy(self.fulfilled_line_item_shippable_1)], closed_at=None, cancelled_at=None)
        }

    def _get_next_order_number(self) -> int:
        self.order_number_counter += 1
        return self.order_number_counter

    def _create_base_order(self, order_id: str, financial_status: Optional[str], fulfillment_status: Optional[str], line_items: list, closed_at: Optional[str], cancelled_at: Optional[str], cancel_reason: Optional[str]=None) -> dict:
        order_num = self._get_next_order_number()
        total_price_decimal = Decimal('0.00')
        for item in line_items:
            try:
                total_price_decimal += Decimal(item.get('price', '0.00')) * Decimal(item.get('quantity', 1))
            except InvalidOperation:
                pass
        
        base_order = {
            'id': order_id, 
            'admin_graphql_api_id': f'gid://shopify/Order/{order_id}', 
            'name': f'#{order_num}', 
            'order_number': order_num, 
            'email': 'customer@example.com', 
            'created_at': self.even_earlier_iso, 
            'updated_at': self.earlier_iso, 
            'cancelled_at': cancelled_at, 
            'cancel_reason': cancel_reason, 
            'closed_at': closed_at, 
            'currency': 'USD', 
            'financial_status': financial_status, 
            'fulfillment_status': fulfillment_status, 
            'total_price': str(total_price_decimal), 
            'subtotal_price': str(total_price_decimal), 
            'total_weight': sum((item.get('grams', 0) * item.get('quantity', 1) for item in line_items)), 
            'total_tax': '0.00', 
            'total_discounts': '0.00', 
            'tags': 'test-order', 
            'note': None, 
            'token': f'token_{order_id}', 
            'line_items': [], 
            'customer': {'id': 'cust_123', 'email': 'customer@example.com', 'first_name': 'Test', 'last_name': 'Customer', 'orders_count': 1, 'total_spent': '100.00'}, 
            'billing_address': {'address1': '123 Billing St', 'city': 'Billville', 'country_code': 'US', 'zip': '12345'}, 
            'shipping_address': {'address1': '123 Shipping St', 'city': 'Shipville', 'country_code': 'US', 'zip': '54321'}, 
            'refunds': [], 
            'transactions': [], 
            'shipping_lines': [], 
            'tax_lines': [], 
            'discount_codes': [],
            'inventory_behaviour': 'decrement_obeying_policy',
            'send_receipt': True
        }
        for li_template in line_items:
            li_copy = copy.deepcopy(li_template)
            li_copy.setdefault('variant_id', 'var_default_' + li_copy.get('id', ''))
            li_copy.setdefault('product_id', 'prod_default_' + li_copy.get('id', ''))
            li_copy.setdefault('variant_title', 'Default Variant for ' + li_copy.get('title', ''))
            li_copy.setdefault('vendor', 'Default Vendor')
            li_copy.setdefault('fulfillment_service', 'manual')
            li_copy.setdefault('name', li_copy.get('title', 'Default Name'))
            li_copy.setdefault('admin_graphql_api_id', f"gid://shopify/LineItem/{li_copy.get('id', 'li_default')}")
            base_order['line_items'].append(li_copy)
        return base_order

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_order_closed_successfully(self, order_id: str, original_order_data: dict):
        initial_updated_at = original_order_data['updated_at']
        response = shopify_close_an_order(order_id=order_id)
        self.assertIsInstance(response, dict, 'Response should be a dictionary.')
        self.assertIn('order', response, "Response should contain an 'order' key.")
        closed_order_data = response['order']
        self.assertEqual(closed_order_data['id'], order_id)
        self.assertIsNotNone(closed_order_data['closed_at'], 'closed_at should be set.')
        try:
            datetime.fromisoformat(closed_order_data['closed_at'].replace('Z', '+00:00'))
        except ValueError:
            self.fail(f"closed_at '{closed_order_data['closed_at']}' is not a valid ISO 8601 datetime string.")
        self.assertTrue(str(closed_order_data['updated_at']) > str(initial_updated_at), f"updated_at ('{closed_order_data['updated_at']}') should be more recent than initial ('{initial_updated_at}').")
        try:
            datetime.fromisoformat(closed_order_data['updated_at'].replace('Z', '+00:00'))
        except ValueError:
            self.fail(f"updated_at '{closed_order_data['updated_at']}' is not a valid ISO 8601 datetime string.")
        self.assertIsNone(closed_order_data['cancelled_at'], 'Order should not be marked as cancelled.')
        expected_order_keys = [
            'id', 'admin_graphql_api_id', 'name', 'order_number', 'email', 'created_at', 
            'updated_at', 'cancelled_at', 'cancel_reason', 'closed_at', 'currency', 
            'financial_status', 'fulfillment_status', 'total_price', 'subtotal_price', 
            'total_weight', 'total_tax', 'total_discounts', 'tags', 'note', 'token', 
            'line_items', 'customer', 'inventory_behaviour', 'send_receipt'
        ]
        for key in expected_order_keys:
            self.assertIn(key, closed_order_data, f"Key '{key}' missing in returned order.")
        for key in [
            'admin_graphql_api_id', 'name', 'order_number', 'email', 'created_at', 'currency', 
            'total_price', 'subtotal_price', 'total_weight', 'total_tax', 'total_discounts', 
            'tags', 'note', 'token', 'inventory_behaviour', 'send_receipt'
        ]:
            self.assertEqual(closed_order_data[key], original_order_data[key], f"Order field '{key}' mismatch.")
        self.assertDictEqual(closed_order_data['customer'], original_order_data['customer'], "Order field 'customer' mismatch.")
        self.assertEqual(closed_order_data['financial_status'], original_order_data['financial_status'])
        expected_fulfillment_status_in_response = original_order_data['fulfillment_status']
        if original_order_data['fulfillment_status'] is None:
            expected_fulfillment_status_in_response = None
        self.assertEqual(closed_order_data['fulfillment_status'], expected_fulfillment_status_in_response, "Order field 'fulfillment_status' mismatch.")
        self.assertIsInstance(closed_order_data['line_items'], list)
        self.assertEqual(len(closed_order_data['line_items']), len(original_order_data['line_items']))
        expected_li_keys = ['id', 'variant_id', 'product_id', 'title', 'quantity', 'sku', 'variant_title', 'vendor', 'fulfillment_service', 'requires_shipping', 'taxable', 'gift_card', 'name', 'price', 'total_discount', 'fulfillment_status', 'grams', 'admin_graphql_api_id', 'fulfillable_quantity']
        for i, returned_li in enumerate(closed_order_data['line_items']):
            original_li = original_order_data['line_items'][i]
            for key in expected_li_keys:
                self.assertIn(key, returned_li, f"Key '{key}' missing in returned line_item {i}.")
            for key_orig_li in original_li:
                if key_orig_li in expected_li_keys:
                    self.assertEqual(returned_li[key_orig_li], original_li[key_orig_li], f"Line item {i} field '{key_orig_li}' mismatch.")
        db_order = DB['orders'][order_id]
        self.assertEqual(_format_datetime(db_order['closed_at']), closed_order_data['closed_at'])
        self.assertEqual(_format_datetime(db_order['updated_at']), closed_order_data['updated_at'])
        self.assertIsNone(db_order['cancelled_at'])
        self.assertEqual(db_order['financial_status'], closed_order_data['financial_status'])
        self.assertEqual(db_order['fulfillment_status'], original_order_data['fulfillment_status'])

    def test_close_order_successfully_paid_fulfilled(self):
        order_id = 'order_closable_paid_fulfilled'
        original_order = copy.deepcopy(DB['orders'][order_id])
        self._assert_order_closed_successfully(order_id, original_order)

    def test_close_order_successfully_refunded_fulfilled(self):
        order_id = 'order_closable_refunded_fulfilled'
        original_order = copy.deepcopy(DB['orders'][order_id])
        self._assert_order_closed_successfully(order_id, original_order)

    def test_close_order_successfully_no_shippable_items_paid(self):
        order_id = 'order_closable_no_shippable_items_paid'
        original_order = copy.deepcopy(DB['orders'][order_id])
        self._assert_order_closed_successfully(order_id, original_order)
        self.assertIsNone(DB['orders'][order_id]['fulfillment_status'], 'Fulfillment status for no shippable items should be None in DB.')

    def test_close_order_not_found_raises_NotFoundError(self):
        self.assert_error_behavior(func_to_call=shopify_close_an_order, order_id='non_existent_order_id', expected_exception_type=custom_errors.NotFoundError, expected_message="Order with ID 'non_existent_order_id' not found.")

    def test_close_order_already_closed_raises_OrderProcessingError(self):
        order_id = 'order_already_closed'
        self.assert_error_behavior(func_to_call=shopify_close_an_order, order_id=order_id, expected_exception_type=custom_errors.OrderProcessingError, expected_message=f"Order '{order_id}' is already closed.")

    def test_close_order_cancelled_raises_OrderProcessingError(self):
        order_id = 'order_cancelled'
        self.assert_error_behavior(func_to_call=shopify_close_an_order, order_id=order_id, expected_exception_type=custom_errors.OrderProcessingError, expected_message=f"Order '{order_id}' is cancelled and cannot be closed.")

    def test_close_order_pending_fulfillment_partial_raises_OrderProcessingError(self):
        order_id = 'order_pending_fulfillment_partial'
        self.assert_error_behavior(func_to_call=shopify_close_an_order, order_id=order_id, expected_exception_type=custom_errors.OrderProcessingError, expected_message=f"Order '{order_id}' has pending fulfillments and cannot be closed.")

    def test_close_order_pending_fulfillment_all_unfulfilled_raises_OrderProcessingError(self):
        order_id = 'order_pending_fulfillment_all_unfulfilled'
        self.assert_error_behavior(func_to_call=shopify_close_an_order, order_id=order_id, expected_exception_type=custom_errors.OrderProcessingError, expected_message=f"Order '{order_id}' has pending fulfillments and cannot be closed.")

    def test_close_order_unsuitable_financial_status_pending_raises_OrderProcessingError(self):
        order_id = 'order_unsuitable_financial_pending'
        self.assert_error_behavior(func_to_call=shopify_close_an_order, order_id=order_id, expected_exception_type=custom_errors.OrderProcessingError, expected_message=f"Order '{order_id}' is not financially settled (e.g., paid, refunded) and cannot be closed.")

    def test_close_order_unsuitable_financial_status_partially_paid_raises_OrderProcessingError(self):
        order_id = 'order_unsuitable_financial_partially_paid'
        self.assert_error_behavior(func_to_call=shopify_close_an_order, order_id=order_id, expected_exception_type=custom_errors.OrderProcessingError, expected_message=f"Order '{order_id}' is not financially settled (e.g., paid, refunded) and cannot be closed.")

    def test_close_order_unsuitable_financial_status_none_raises_OrderProcessingError(self):
        order_id = 'order_unsuitable_financial_none'
        self.assert_error_behavior(func_to_call=shopify_close_an_order, order_id=order_id, expected_exception_type=custom_errors.OrderProcessingError, expected_message=f"Order '{order_id}' is not financially settled (e.g., paid, refunded) and cannot be closed.")

    def test_close_order_invalid_order_id_type_raises_ValidationError(self):
        self.assert_error_behavior(func_to_call=shopify_close_an_order, order_id=12345, expected_exception_type=custom_errors.ValidationError, expected_message='order_id must be a non-empty string.')

if __name__ == '__main__':
    unittest.main()
