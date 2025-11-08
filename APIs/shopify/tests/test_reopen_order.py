import unittest
import copy
from datetime import datetime, timedelta, timezone

from ..SimulationEngine import custom_errors
from shopify import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from shopify import reopen_order

class TestShopifyReopenAnOrder(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        now_iso = datetime.now(timezone.utc).isoformat() # Use timezone.utc
        past_iso = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
        closed_time_iso = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        
        # Base order data (used for most tests)
        self.base_order_details = {
            'admin_graphql_api_id': 'gid://shopify/Order/placeholder',
            'name': '#0000', 
            'order_number': 0, 
            'email': 'customer@example.com', 
            'created_at': past_iso, 
            'updated_at': closed_time_iso, 
            'closed_at': closed_time_iso, 
            'cancelled_at': None, 
            'cancel_reason': None, 
            'currency': 'USD', 
            'financial_status': 'paid', 
            'fulfillment_status': 'fulfilled', 
            'total_price': '150.00', 
            'subtotal_price': '140.00', 
            'total_tax': '10.00',
            'line_items': [{
                'id': '100', 'title': 'Product Main', 'variant_title': 'Default', 
                'quantity': 1, 'price': '140.00', 'sku': 'PROD_MAIN', 
                'grams': 200, 'taxable': True, 'requires_shipping': True
            }],
            'customer': {
                'id': '200', 'email': 'customer@example.com', 'first_name': 'Test', 
                'last_name': 'User', 'orders_count': 1, 'total_spent': '150.00'
            }
        }

        DB['orders'] = {
            'closed_order_1': {**self.base_order_details, 'id': 'closed_order_1', 'name': '#1001', 'order_number': 1001, 'email': 'customer1@example.com', 'customer': {**self.base_order_details['customer'], 'id': '201', 'email': 'customer1@example.com'}, 'line_items': [{**self.base_order_details['line_items'][0], 'id': '101'}]},
            'open_order_1': {**self.base_order_details, 'id': 'open_order_1', 'name': '#1002', 'order_number': 1002, 'email': 'customer2@example.com', 'closed_at': None, 'status': 'open', 'updated_at': past_iso, 'customer': {**self.base_order_details['customer'], 'id': '202', 'email': 'customer2@example.com'}, 'line_items': [{**self.base_order_details['line_items'][0], 'id': '102'}]},
            'cancelled_order_1': {**self.base_order_details, 'id': 'cancelled_order_1', 'name': '#1003', 'order_number': 1003, 'email': 'customer3@example.com', 'closed_at': None, 'cancelled_at': closed_time_iso, 'cancel_reason': 'customer', 'status': 'cancelled', 'financial_status': 'voided', 'customer': {**self.base_order_details['customer'], 'id': '203', 'email': 'customer3@example.com'}, 'line_items': [{**self.base_order_details['line_items'][0], 'id': '103'}]},
            'archived_closed_order_1': {**self.base_order_details, 'id': 'archived_closed_order_1', 'name': '#1004', 'order_number': 1004, 'email': 'customer4@example.com', 'tags': 'archived, special', 'status': 'closed', 'customer': {**self.base_order_details['customer'], 'id': '204', 'email': 'customer4@example.com'}, 'line_items': [{**self.base_order_details['line_items'][0], 'id': '104'}]},
            
            # New orders for edge cases
            'order_empty_li': {**self.base_order_details, 'id': 'order_empty_li', 'line_items': []},
            'order_li_no_id': {**self.base_order_details, 'id': 'order_li_no_id', 'line_items': [{'title': 'Product X', 'quantity': 1, 'price': '10.00'}]}, # Missing ID
            'order_li_id_not_int_str': {**self.base_order_details, 'id': 'order_li_id_not_int_str', 'line_items': [{'id': 'abc', 'title': 'Product Y', 'quantity': 1, 'price': '20.00'}]},
            'order_customer_no_id': {**self.base_order_details, 'id': 'order_customer_no_id', 'customer': {'email': 'test@no.id', 'first_name': 'No'}},
            'order_customer_id_not_int_str': {**self.base_order_details, 'id': 'order_customer_id_not_int_str', 'customer': {'id': 'xyz', 'email': 'test@bad.id'}},
            'order_no_status_field': {**{k:v for k,v in self.base_order_details.items() if k != 'status'}, 'id': 'order_no_status_field'},
            'order_extra_fields': {**self.base_order_details, 'id': 'order_extra_fields', 'my_custom_field': 'value123', 'another_one': True},
            'order_created_at_datetime_obj': {**self.base_order_details, 'id': 'order_created_at_datetime_obj', 'created_at': datetime.now(timezone.utc) - timedelta(days=30)},
            'order_minimal_closed': {'id': 'order_minimal_closed', 'closed_at': closed_time_iso, 'updated_at': closed_time_iso, 'created_at': past_iso, 'order_number': 3001, 'name': '#3001', 'currency': 'USD', 'total_price': '1.00', 'line_items': [{'id':'301', 'title':'Min', 'quantity':1, 'price':'1.00'}]},
            'order_missing_optional_fields': {**self.base_order_details, 'id': 'order_missing_optional_fields', 'email': None, 'subtotal_price': None, 'total_tax': None, 'fulfillment_status': None, 'customer': None}
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    # --- Existing Tests (verified for alignment) ---
    def test_reopen_closed_order_success(self):
        order_id_to_reopen = 'closed_order_1'
        original_order_data = copy.deepcopy(DB['orders'][order_id_to_reopen])
        response = reopen_order(order_id=order_id_to_reopen)
        self.assertIn('order', response)
        reopened_order = response['order']
        self.assertEqual(reopened_order['id'], order_id_to_reopen) # Stays string
        self.assertIsNone(reopened_order['closed_at'])
        self.assertIsNotNone(reopened_order['updated_at'])
        self.assertGreater(reopened_order['updated_at'], original_order_data['updated_at'])
        self.assertEqual(reopened_order['name'], original_order_data['name'])
        db_order = DB['orders'][order_id_to_reopen]
        self.assertIsNone(db_order['closed_at'])
        self.assertEqual(db_order['updated_at'], reopened_order['updated_at'])

    def test_reopen_order_not_found_raises_notfounderror(self):
        self.assert_error_behavior(func_to_call=reopen_order, order_id='non_existent_order',
                                   expected_exception_type=custom_errors.NotFoundError, 
                                   expected_message="Order with ID 'non_existent_order' not found.")

    def test_reopen_already_open_order_raises_orderprocessingerror(self):
        self.assert_error_behavior(func_to_call=reopen_order, order_id='open_order_1',
                                   expected_exception_type=custom_errors.OrderProcessingError, 
                                   expected_message="Order 'open_order_1' is already open or was not closed.")

    def test_reopen_cancelled_order_raises_orderprocessingerror(self):
        self.assert_error_behavior(func_to_call=reopen_order, order_id='cancelled_order_1',
                                   expected_exception_type=custom_errors.OrderProcessingError, 
                                   expected_message="Order 'cancelled_order_1' is cancelled and cannot be reopened.")

    def test_reopen_archived_and_closed_order_success_unarchives(self):
        order_id_to_reopen = 'archived_closed_order_1'
        original_order_data = copy.deepcopy(DB['orders'][order_id_to_reopen])
        response = reopen_order(order_id=order_id_to_reopen)
        self.assertIn('order', response)
        reopened_order = response['order']
        self.assertEqual(reopened_order['id'], order_id_to_reopen)
        self.assertIsNone(reopened_order['closed_at'])
        self.assertGreater(reopened_order['updated_at'], original_order_data['updated_at'])
        db_order = DB['orders'][order_id_to_reopen]
        self.assertIsNone(db_order['closed_at'])

    def test_reopen_order_invalid_order_id_type_raises_validationerror(self):
        self.assert_error_behavior(func_to_call=reopen_order, order_id=12345, # type: ignore
                                   expected_exception_type=custom_errors.ValidationError, 
                                   expected_message='Order ID must be a string.')

    def test_reopen_order_empty_order_id_raises_validationerror(self):
        self.assert_error_behavior(func_to_call=reopen_order, order_id='',
                                   expected_exception_type=custom_errors.ValidationError, 
                                   expected_message='Order ID cannot be empty.')
    
    def test_reopen_order_whitespace_order_id_raises_validationerror(self): # New
        self.assert_error_behavior(func_to_call=reopen_order, order_id='   ',
                                   expected_exception_type=custom_errors.ValidationError, 
                                   expected_message='Order ID cannot be empty.')

    def test_reopen_order_response_structure_and_content(self):
        order_id_to_reopen = 'closed_order_1'
        original_order = DB['orders'][order_id_to_reopen]
        response = reopen_order(order_id=order_id_to_reopen)
        self.assertIn('order', response)
        reopened_order = response['order']
        
        self.assertEqual(reopened_order['id'], original_order['id'])
        self.assertEqual(reopened_order['name'], original_order['name'])
        self.assertEqual(reopened_order['email'], original_order['email'])
        self.assertEqual(reopened_order['created_at'], original_order['created_at'])
        self.assertTrue(isinstance(reopened_order['updated_at'], str))
        self.assertIsNone(reopened_order['closed_at'])
        self.assertEqual(reopened_order['financial_status'], original_order['financial_status'])
        self.assertEqual(reopened_order['fulfillment_status'], original_order['fulfillment_status'])
        self.assertEqual(reopened_order['currency'], original_order['currency'])
        self.assertEqual(reopened_order['total_price'], original_order['total_price'])
        self.assertEqual(reopened_order['subtotal_price'], original_order['subtotal_price'])
        self.assertEqual(reopened_order['total_tax'], original_order['total_tax'])
        
        self.assertIsInstance(reopened_order['line_items'], list)
        if reopened_order['line_items'] and original_order.get('line_items'): # Check if original_order has line_items
            self.assertEqual(len(reopened_order['line_items']), len(original_order['line_items']))
            self.assertEqual(reopened_order['line_items'][0]['id'], int(original_order['line_items'][0]['id']))
            self.assertEqual(reopened_order['line_items'][0]['title'], original_order['line_items'][0]['title'])
        
        if original_order.get('customer'):
            self.assertIsNotNone(reopened_order['customer'])
            self.assertEqual(reopened_order['customer']['id'], int(original_order['customer']['id']))
            self.assertEqual(reopened_order['customer']['email'], original_order['customer']['email'])
        else:
            self.assertIsNone(reopened_order.get('customer'))

    # --- New Edge Case Tests ---

    def test_reopen_order_with_empty_line_items_list(self):
        order_id = 'order_empty_li'
        response = reopen_order(order_id=order_id)
        self.assertIn('order', response)
        reopened_order = response['order']
        self.assertIsNone(reopened_order['closed_at'])
        self.assertEqual(reopened_order['line_items'], [])

    def test_reopen_order_line_item_missing_id_raises_error(self):
        order_id = 'order_li_no_id'
        self.assert_error_behavior(
            func_to_call=reopen_order, order_id=order_id,
            expected_exception_type=custom_errors.OrderProcessingError,
            expected_message=f"Invalid or missing line item ID format 'None' for order '{order_id}'."
        )

    def test_reopen_order_line_item_id_not_int_string_raises_error(self):
        order_id = 'order_li_id_not_int_str'
        self.assert_error_behavior(
            func_to_call=reopen_order, order_id=order_id,
            expected_exception_type=custom_errors.OrderProcessingError,
            expected_message=f"Invalid or missing line item ID format 'abc' for order '{order_id}'."
        )

    def test_reopen_order_customer_missing_id_raises_error(self):
        order_id = 'order_customer_no_id'
        self.assert_error_behavior(
            func_to_call=reopen_order, order_id=order_id,
            expected_exception_type=custom_errors.OrderProcessingError,
            expected_message=f"Invalid or missing customer ID format 'None' for order '{order_id}'."
        )

    def test_reopen_order_customer_id_not_int_string_raises_error(self):
        order_id = 'order_customer_id_not_int_str'
        self.assert_error_behavior(
            func_to_call=reopen_order, order_id=order_id,
            expected_exception_type=custom_errors.OrderProcessingError,
            expected_message=f"Invalid or missing customer ID format 'xyz' for order '{order_id}'."
        )

    def test_reopen_order_no_initial_status_field(self):
        order_id = 'order_no_status_field'
        # Function logic: if 'status' in order_data: order_data['status'] = 'open'
        # If not present, it's not added to DB by this logic.
        # The response loop copies existing fields from order_data.
        response = reopen_order(order_id=order_id)
        self.assertNotIn('status', DB['orders'][order_id], "Status should not be added to DB if not initially present")
        self.assertNotIn('status', response['order'], "Status should not be in response if not initially present in DB order_data")
        self.assertIsNone(response['order']['closed_at']) # Core logic check

    def test_reopen_order_preserves_extra_fields(self):
        order_id = 'order_extra_fields'
        response = reopen_order(order_id=order_id)
        self.assertIn('order', response)
        reopened_order = response['order']
        self.assertEqual(reopened_order.get('my_custom_field'), "value123")
        self.assertEqual(reopened_order.get('another_one'), True)
        self.assertIsNone(reopened_order['closed_at']) # Core logic check

    def test_reopen_order_created_at_is_datetime_object_in_db(self):
        order_id = 'order_created_at_datetime_obj'
        # setUp created this order with created_at as a datetime object
        original_db_order_created_at = DB['orders'][order_id]['created_at']
        self.assertIsInstance(original_db_order_created_at, datetime)

        response = reopen_order(order_id=order_id)
        reopened_order = response['order']
        
        self.assertTrue(isinstance(reopened_order['created_at'], str))
        # Check if it's a valid ISO format (helper should ensure UTC 'Z')
        # The helper function `_ensure_iso_string_for_response` handles this.
        # We can check if the string matches the isoformat of the original datetime object.
        expected_iso_created_at = original_db_order_created_at.isoformat()
        if original_db_order_created_at.tzinfo is None: # If naive, helper makes it UTC
             expected_iso_created_at = original_db_order_created_at.replace(tzinfo=timezone.utc).isoformat()
        
        self.assertEqual(reopened_order['created_at'], expected_iso_created_at)


    def test_reopen_order_with_minimal_valid_closed_data(self):
        order_id = 'order_minimal_closed'
        response = reopen_order(order_id=order_id)
        self.assertIn('order', response)
        reopened_order = response['order']
        self.assertEqual(reopened_order['id'], order_id)
        self.assertIsNone(reopened_order['closed_at'])
        self.assertIsNotNone(reopened_order['updated_at'])
        # Check that essential fields are present even if minimal
        self.assertEqual(reopened_order['name'], '#3001')
        self.assertEqual(reopened_order['currency'], 'USD')
        self.assertTrue(len(reopened_order['line_items']) == 1)
        self.assertEqual(reopened_order['line_items'][0]['id'], 301)


    def test_reopen_order_with_missing_optional_fields_in_db(self):
        order_id = 'order_missing_optional_fields'
        # This order was set up with email, subtotal_price, total_tax, fulfillment_status, customer as None
        response = reopen_order(order_id=order_id)
        self.assertIn('order', response)
        reopened_order = response['order']
        
        self.assertIsNone(reopened_order['closed_at']) # Core logic
        self.assertIsNone(reopened_order.get('email'))
        self.assertIsNone(reopened_order.get('subtotal_price'))
        self.assertIsNone(reopened_order.get('total_tax'))
        self.assertIsNone(reopened_order.get('fulfillment_status'))
        self.assertIsNone(reopened_order.get('customer')) # Customer was set to None in DB

if __name__ == '__main__':
    unittest.main()

