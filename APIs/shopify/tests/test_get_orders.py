import unittest
import copy
from datetime import datetime, timezone, timedelta

from shopify.SimulationEngine import custom_errors
from shopify.SimulationEngine.db import DB
from shopify.orders import shopify_get_orders_list as get_orders # Target function
from shopify.SimulationEngine.models import ShopifyOrderModel, OrderCustomerInfo, OrderLineItemModel
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestGetOrders(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.line_item1_data = OrderLineItemModel(id="li1",product_id="p1", title="Product A", quantity=1, price="10.00").model_dump(mode='json')
        self.line_item2_data = OrderLineItemModel(id="li2",product_id="p2", title="Product B", quantity=2, price="25.00").model_dump(mode='json')
        self.customer1_info = OrderCustomerInfo(id="cust1001", email="customer1@example.com").model_dump(mode='json')
        self.customer2_info = OrderCustomerInfo(id="cust1002", email="customer2@example.com").model_dump(mode='json')

        self.order1 = {
            "id": "1001", "order_number": 1001, "name": "#1001", "customer": self.customer1_info,
            "created_at": datetime(2023, 1, 10, 10, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "updated_at": datetime(2023, 1, 11, 10, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "processed_at": datetime(2023, 1, 10, 11, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "financial_status": "paid", "fulfillment_status": "fulfilled", "status": "closed", 
            "closed_at": datetime(2023, 1, 12, 0, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"), "cancelled_at": None,
            "app_id": "app_A", "line_items": [self.line_item1_data], "total_price": "10.00", "currency": "USD"
        }
        self.order2 = {
            "id": "1002", "order_number": 1002, "name": "#1002", "customer": self.customer1_info,
            "created_at": datetime(2023, 2, 5, 10, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "updated_at": datetime(2023, 2, 6, 10, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "processed_at": datetime(2023, 2, 5, 11, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "financial_status": "pending", "fulfillment_status": "unshipped", "status": "open",
            "closed_at": None, "cancelled_at": None,
            "app_id": "app_B", "line_items": [self.line_item2_data], "total_price": "50.00", "currency": "USD"
        }
        self.order3 = {
            "id": "1003", "order_number": 1003, "name": "#1003", "customer": self.customer2_info,
            "created_at": datetime(2023, 3, 1, 10, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "updated_at": datetime(2023, 3, 2, 10, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "processed_at": datetime(2023, 3, 1, 11, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "financial_status": "paid", "fulfillment_status": "partial", "status": "open",
            "closed_at": None, "cancelled_at": None,
            "app_id": "app_A", "line_items": [self.line_item1_data, self.line_item2_data], "total_price": "60.00", "currency": "USD"
        }
        self.order4_cancelled = {
            "id": "1004", "order_number": 1004, "name": "#1004", "customer": self.customer1_info,
            "created_at": datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "updated_at": datetime(2023, 1, 2, 0, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "processed_at": datetime(2023, 1, 1, 1, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "financial_status": "voided", "fulfillment_status": None, "status": "cancelled", 
            "closed_at": None, "cancelled_at": datetime(2023, 1, 2, 0, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"), 
            "cancel_reason": "customer", "total_price": "5.00", "currency": "USD", "app_id": None
        }
        self.order5_no_app_id = {
            "id": "1005", "order_number": 1005, "name": "#1005", "customer": self.customer1_info,
            "created_at": datetime(2023, 4, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "updated_at": datetime(2023, 4, 2, 0, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "processed_at": datetime(2023, 4, 1, 1, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "financial_status": "paid", "fulfillment_status": "shipped", "status": "closed", 
            "closed_at": datetime(2023, 4, 3, 0, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"), "cancelled_at": None,
            "app_id": None, "total_price": "25.00", "currency": "USD"
        }
        self.order6_non_int_id = {
            "id": "A1006", "order_number": 1006, "name": "#A1006", "customer": self.customer2_info,
            "created_at": datetime(2023, 5, 1, 0,0,0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "updated_at": datetime(2023, 5, 1, 0,0,0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "processed_at": datetime(2023, 5, 1, 0,0,0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "financial_status": "paid", "status": "open", "total_price": "10.00", "currency":"USD",
            "closed_at": None, "cancelled_at": None, "app_id": "app_C"
        }

        DB['orders'] = {
            "1001": self.order1,
            "1002": self.order2,
            "1003": self.order3,
            "1004": self.order4_cancelled,
            "1005": self.order5_no_app_id,
            "A1006": self.order6_non_int_id
        }
        self.all_orders_in_db = list(DB['orders'].values())
        self.all_orders_sorted_by_str_id = sorted(self.all_orders_in_db, key=lambda o: str(o.get('id','')))
        
        def sort_key_for_since_id_comparison(order_dict):
            order_id = order_dict.get('id')
            try: return (0, int(order_id))
            except (ValueError, TypeError): return (1, str(order_id))
        self.all_orders_sorted_for_since_id_logic = sorted(self.all_orders_in_db, key=sort_key_for_since_id_comparison)

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_orders_match(self, result_orders_list, expected_db_order_dicts_list, requested_fields_param=None):
        result_orders_list.sort(key=lambda o: str(o.get('id','')))
        expected_db_order_dicts_list.sort(key=lambda o: str(o.get('id','')))
        
        self.assertEqual(len(result_orders_list), len(expected_db_order_dicts_list),
                         f"Mismatch in number of orders. Expected {len(expected_db_order_dicts_list)}, Got {len(result_orders_list)}."
                         f"\nResult: {result_orders_list}\nExpected: {expected_db_order_dicts_list}")

        for i, result_order_dict in enumerate(result_orders_list):
            expected_order_data_original = expected_db_order_dicts_list[i]
            self.assertEqual(str(result_order_dict.get('id')), str(expected_order_data_original.get('id')))

            all_model_fields = list(ShopifyOrderModel.model_fields.keys())
            fields_expected_in_response: List[str]
            if requested_fields_param is None or not requested_fields_param:
                fields_expected_in_response = all_model_fields
            else:
                seen = set()
                unique_requested = [f for f in requested_fields_param if not (f in seen or seen.add(f))]
                fields_expected_in_response = [f for f in unique_requested if f in all_model_fields]
            
            self.assertCountEqual(list(result_order_dict.keys()), fields_expected_in_response, f"Order ID {result_order_dict.get('id')} keys mismatch.")
            for field in fields_expected_in_response:
                self.assertEqual(result_order_dict.get(field), expected_order_data_original.get(field), f"Order ID {result_order_dict.get('id')}, Field '{field}' mismatch.")

    # --- Basic Filter Tests ---
    def test_get_orders_default_filters(self):
        response = get_orders()
        expected = [o for o in self.all_orders_sorted_by_str_id if not o.get('closed_at') and not o.get('cancelled_at')]
        self._assert_orders_match(response['orders'], expected)

    def test_get_orders_limit(self):
        # Function default sort is by int/str ID key. We compare against that for limit.
        response = get_orders(limit=2, status="any")
        self._assert_orders_match(response['orders'], self.all_orders_sorted_for_since_id_logic[:2])

    def test_get_orders_by_ids(self):
        response = get_orders(ids=["1001", "1003"], status="any")
        self._assert_orders_match(response['orders'], [self.order1, self.order3])

    def test_get_orders_by_name(self):
        response = get_orders(name="#1002", status="any")
        self._assert_orders_match(response['orders'], [self.order2])

    def test_get_orders_by_status_closed(self):
        response = get_orders(status="closed")
        expected = [o for o in self.all_orders_in_db if o.get('closed_at') and not o.get('cancelled_at')]
        self._assert_orders_match(response['orders'], expected)

    def test_get_orders_by_status_cancelled(self):
        response = get_orders(status="cancelled")
        self._assert_orders_match(response['orders'], [self.order4_cancelled])

    def test_get_orders_by_financial_status_paid(self):
        response = get_orders(financial_status="paid", status="any")
        expected = [o for o in self.all_orders_in_db if o.get('financial_status') == "paid"]
        self._assert_orders_match(response['orders'], expected)

    def test_get_orders_by_fulfillment_status_shipped(self):
        response = get_orders(fulfillment_status="shipped", status="any")
        expected = [o for o in self.all_orders_in_db if o.get('fulfillment_status') == "shipped"]
        self._assert_orders_match(response['orders'], expected)
    
    def test_get_orders_by_attribution_app_id(self):
        response = get_orders(attribution_app_id="app_A", status="any")
        self._assert_orders_match(response['orders'], [self.order1, self.order3])

    def test_get_orders_by_attribution_app_id_current(self):
        response = get_orders(attribution_app_id="current", status="any")
        expected = [o for o in self.all_orders_in_db if o.get('app_id') is not None]
        self._assert_orders_match(response['orders'], expected)

    # --- Date Filter Tests ---
    def test_get_orders_by_created_at_min_max(self):
        response = get_orders(created_at_min="2023-01-15T00:00:00Z", created_at_max="2023-02-28T23:59:59Z", status="any")
        self._assert_orders_match(response['orders'], [self.order2])
    
    def test_get_orders_by_processed_at_min(self):
        response = get_orders(processed_at_min="2023-02-01T00:00:00Z", status="any")
        expected = [self.order2, self.order3, self.order5_no_app_id, self.order6_non_int_id]
        self._assert_orders_match(response['orders'], expected)

    def test_get_orders_by_updated_at_range(self):
        response = get_orders(updated_at_min="2023-03-01T00:00:00Z", updated_at_max="2023-03-31T00:00:00Z", status="any")
        self._assert_orders_match(response['orders'], [self.order3])

    def test_date_filter_with_naive_db_date(self):
        DB['orders']["nd100"] = {"id": "nd100", "created_at": "2023-01-15T10:00:00", "customer": self.customer1_info, "name":"#ND100", "order_number":100, "status":"open"}
        response = get_orders(created_at_min="2023-01-15T09:00:00Z", created_at_max="2023-01-15T11:00:00Z", status="any")
        self.assertIn("nd100", [o['id'] for o in response['orders']])

    def test_date_filter_malformed_db_date_is_skipped(self):
        DB['orders']["md101"] = {"id": "md101", "created_at": "totally-not-a-date", "customer": self.customer1_info, "name":"#MD101", "order_number":101, "status":"open"}
        response = get_orders(created_at_min="2000-01-01T00:00:00Z", status="any")
        self.assertNotIn("md101", [o['id'] for o in response['orders']])

    def test_date_filter_none_db_date_is_skipped_for_created_at(self):
        DB['orders']["xnd102"] = {"id": "xnd102", "created_at": None, "customer": self.customer1_info, "name":"#XND102", "order_number":102, "status":"open"}
        response = get_orders(created_at_min="2000-01-01T00:00:00Z", status="any")
        self.assertNotIn("xnd102", [o['id'] for o in response['orders']])

    def test_date_filter_none_processed_at_is_skipped(self):
        DB['orders']["xnd103"] = {"id": "xnd103", "processed_at": None, "customer": self.customer1_info, "name":"#XND103", "order_number":103, "status":"open", "created_at": datetime(2023,1,1, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")}
        response = get_orders(processed_at_min="2000-01-01T00:00:00Z", status="any")
        self.assertNotIn("xnd103", [o['id'] for o in response['orders']])

    def test_date_filter_none_updated_at_is_skipped(self):
        DB['orders']["xnd104"] = {"id": "xnd104", "updated_at": None, "customer": self.customer1_info, "name":"#XND104", "order_number":104, "status":"open", "created_at": datetime(2023,1,1, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")}
        response = get_orders(updated_at_min="2000-01-01T00:00:00Z", status="any")
        self.assertNotIn("xnd104", [o['id'] for o in response['orders']])

    def test_get_orders_input_date_naive_string_parsed_as_utc(self):
        response = get_orders(created_at_min="2023-01-10T10:00:00", status="any") 
        expected_ids = {self.order1['id'], self.order2['id'], self.order3['id'], self.order5_no_app_id['id'], self.order6_non_int_id['id']}
        returned_ids = {o['id'] for o in response['orders']}
        self.assertEqual(returned_ids, expected_ids)

    def test_get_orders_input_date_already_timezone_aware(self):
        # Covers the `else` branch of `if parsed_date.tzinfo is None`
        response = get_orders(created_at_min="2023-01-10T12:00:00+02:00", status="any") # This is 2023-01-10T10:00:00Z
        returned_ids = {o['id'] for o in response['orders']}
        self.assertIn(self.order1['id'], returned_ids)
        self.assertNotIn(self.order4_cancelled['id'], returned_ids) # created Jan 1

    # --- since_id Tests ---
    def test_get_orders_since_id(self):
        response = get_orders(since_id=1002, status="any")
        expected = [o for o in self.all_orders_sorted_for_since_id_logic if ( (str(o.get('id')).isdigit() and int(o.get('id')) > 1002) or (not str(o.get('id')).isdigit()) )]
        self._assert_orders_match(response['orders'], expected)
    
    def test_get_orders_since_id_handles_non_integer_db_ids(self):
        response = get_orders(since_id=1005, status="any") 
        expected = [o for o in self.all_orders_sorted_for_since_id_logic if ( (str(o.get('id')).isdigit() and int(o.get('id')) > 1005) or (not str(o.get('id')).isdigit()) )]
        self._assert_orders_match(response['orders'], expected)

    def test_get_orders_since_id_all_results(self):
        response = get_orders(since_id=0, status="any") 
        expected = [o for o in self.all_orders_sorted_for_since_id_logic if ( (str(o.get('id')).isdigit() and int(o.get('id')) > 0) or (not str(o.get('id')).isdigit()) )]
        self._assert_orders_match(response['orders'], expected)
    
    def test_get_orders_since_id_limit(self):
        response = get_orders(since_id=1001, limit=2, status="any")
        expected_after_since = []
        # Simulate the function's internal logic for since_id based on the pre-sorted list
        for o_data in self.all_orders_sorted_for_since_id_logic:
            o_id_str = str(o_data.get('id'))
            try:
                if int(o_id_str) > 1001:
                    expected_after_since.append(o_data)
            except ValueError: 
                expected_after_since.append(o_data) 
        self._assert_orders_match(response['orders'], expected_after_since[:2])

    def test_complex_filter_combination_with_since_id(self):
        response = get_orders(financial_status="paid", status="open", since_id=1001)
        
        temp_filtered = []
        for o_data in self.all_orders_in_db: # Start with all orders
            is_cancelled = bool(o_data.get('cancelled_at'))
            is_closed = bool(o_data.get('closed_at')) and not is_cancelled
            current_status_open = not (is_cancelled or is_closed)
            if o_data.get('financial_status') == "paid" and current_status_open:
                temp_filtered.append(o_data)
        
        def sort_key_for_since_id_comparison(order_dict):
            order_id = order_dict.get('id')
            try: return (0, int(order_id))
            except (ValueError, TypeError): return (1, str(order_id))
        temp_filtered.sort(key=sort_key_for_since_id_comparison)

        expected_final = []
        for o_data in temp_filtered:
            o_id_str = str(o_data.get('id'))
            try:
                if int(o_id_str) > 1001:
                    expected_final.append(o_data)
            except ValueError: 
                expected_final.append(o_data) 
        self._assert_orders_match(response['orders'], expected_final)

    # --- Field Selection Test ---
    def test_get_orders_with_fields(self):
        fields_to_request = ["id", "order_number", "total_price"]
        response = get_orders(ids=["1001"], fields=fields_to_request, status="any")
        self.assertEqual(len(response['orders']), 1)
        self.assertCountEqual(response['orders'][0].keys(), fields_to_request)

    # --- Error Cases ---
    def test_error_invalid_limit(self):
        self.assert_error_behavior(get_orders, custom_errors.InvalidInputError, "Limit must be an integer between 1 and 250.", limit=300)
    
    def test_error_invalid_ids_type_not_list(self): 
        self.assert_error_behavior(get_orders, custom_errors.InvalidInputError, "Parameter 'ids' must be a list if provided.", ids="1,2,3")

    def test_error_invalid_ids_item_type(self):
         self.assert_error_behavior(get_orders, custom_errors.InvalidInputError, "All items in 'ids' list must be non-empty strings.", ids=["1001", 1002])

    def test_error_invalid_fields_type_not_list(self):
        self.assert_error_behavior(get_orders, custom_errors.InvalidInputError, "Parameter 'fields' must be a list if provided.", fields="id,name")

    def test_error_invalid_fields_item_type(self):
         self.assert_error_behavior(get_orders, custom_errors.InvalidInputError, "All items in 'fields' list must be non-empty strings.", fields=["id", 123])

    def test_error_invalid_since_id_str(self):
        self.assert_error_behavior(get_orders, custom_errors.InvalidInputError, "Parameter 'since_id' must be a non-negative integer.", since_id="abc")
    def test_error_invalid_since_id_negative(self):
        self.assert_error_behavior(get_orders, custom_errors.InvalidInputError, "Parameter 'since_id' must be a non-negative integer.", since_id=-1)
    
    def test_error_invalid_status(self):
        expected_msg = "Invalid status: 'invalid_status'. Must be one of ['open', 'closed', 'cancelled', 'any']."
        self.assert_error_behavior(get_orders, custom_errors.InvalidInputError, expected_msg, status="invalid_status")
    
    def test_error_invalid_financial_status(self):
        expected_msg = "Invalid financial_status: 'invalid_fin_status'. Must be one of ['pending', 'authorized', 'paid', 'partially_paid', 'refunded', 'voided', 'partially_refunded', 'any', 'unpaid']."
        self.assert_error_behavior(get_orders, custom_errors.InvalidInputError, expected_msg, financial_status="invalid_fin_status")
    
    def test_error_invalid_fulfillment_status(self):
        expected_msg = "Invalid fulfillment_status: 'invalid_ful_status'. Must be one of ['shipped', 'partial', 'unshipped', 'any', 'fulfilled']."
        self.assert_error_behavior(get_orders, custom_errors.InvalidInputError, expected_msg, fulfillment_status="invalid_ful_status")
    
    def test_error_invalid_date_format(self):
        expected_msg = "Invalid format for created_at_min: 'bad-date'. Use ISO 8601 format."
        self.assert_error_behavior(get_orders, custom_errors.InvalidDateTimeFormatError, expected_msg, created_at_min="bad-date")
    
    def test_error_invalid_date_type(self):
        self.assert_error_behavior(get_orders, custom_errors.InvalidInputError, "Parameter 'processed_at_max' must be a string.", processed_at_max=123)
    
    def test_error_invalid_name_type(self):
        self.assert_error_behavior(get_orders, custom_errors.InvalidInputError, "Parameter 'name' must be a string if provided.", name=123)
    
    def test_error_invalid_attribution_app_id_type(self):
        self.assert_error_behavior(get_orders, custom_errors.InvalidInputError, "Parameter 'attribution_app_id' must be a string if provided.", attribution_app_id=456)

if __name__ == '__main__':
    unittest.main()
