
import unittest
import copy
from datetime import datetime, timezone, timedelta
from typing import List

from shopify.SimulationEngine import custom_errors
from shopify.SimulationEngine.db import DB
from shopify.orders import shopify_get_customer_orders as get_customer_orders # Target function
from shopify.SimulationEngine.models import ShopifyOrderModel, ShopifyCustomerModel, OrderLineItemModel, ShopifyAddressModel, OrderCustomerInfo
from common_utils.base_case import BaseTestCaseWithErrorHandler 


class TestGetCustomerOrders(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.cust1_id = "c1001"
        self.cust2_id = "c1002"
        self.cust_no_orders_id = "c1003"

        self.customer1_data = ShopifyCustomerModel(
            id=self.cust1_id, email="cust1@example.com", created_at=datetime(2023,1,1, tzinfo=timezone.utc), updated_at=datetime(2023,1,1, tzinfo=timezone.utc)
        ).model_dump(mode='json')
        self.customer2_data = ShopifyCustomerModel(
            id=self.cust2_id, email="cust2@example.com", created_at=datetime(2023,1,1, tzinfo=timezone.utc), updated_at=datetime(2023,1,1, tzinfo=timezone.utc)
        ).model_dump(mode='json')
        self.customer_no_orders_data = ShopifyCustomerModel(
            id=self.cust_no_orders_id, email="cust3@example.com", created_at=datetime(2023,1,1, tzinfo=timezone.utc), updated_at=datetime(2023,1,1, tzinfo=timezone.utc)
        ).model_dump(mode='json')

        DB['customers'] = {
            self.cust1_id: self.customer1_data,
            self.cust2_id: self.customer2_data,
            self.cust_no_orders_id: self.customer_no_orders_data
        }

        self.line_item1 = OrderLineItemModel(product_id="p1", title="Product A", quantity=1, price="10.00", sku="SKU_A").model_dump(mode='json')
        self.line_item2 = OrderLineItemModel(product_id="p2", title="Product B", quantity=2, price="20.00", sku="SKU_B").model_dump(mode='json')
        self.line_item3_custom = OrderLineItemModel(title="Custom Item", quantity=1, price="5.00").model_dump(mode='json')

        self.order1_cust1_id = "o2001"
        self.order1_cust1_data = ShopifyOrderModel(
            id=self.order1_cust1_id, order_number=1001,
            customer=OrderCustomerInfo(id=self.cust1_id, email=self.customer1_data['email']),
            created_at=datetime(2024, 1, 10, 10, 0, 0, tzinfo=timezone.utc),
            financial_status="paid", total_price="30.00", currency="USD",
            line_items=[self.line_item1, self.line_item2]
        ).model_dump(mode='json')

        self.order2_cust1_id = "o2002"
        self.order2_cust1_data = ShopifyOrderModel(
            id=self.order2_cust1_id, order_number=1002,
            customer=OrderCustomerInfo(id=self.cust1_id, email=self.customer1_data['email']),
            created_at=datetime(2024, 2, 15, 12, 0, 0, tzinfo=timezone.utc),
            financial_status="pending", total_price="5.00", currency="USD",
            line_items=[self.line_item3_custom]
        ).model_dump(mode='json')

        self.order3_cust1_id = "o2003"
        self.order3_cust1_cancelled_data = ShopifyOrderModel(
            id=self.order3_cust1_id, order_number=1003,
            customer=OrderCustomerInfo(id=self.cust1_id, email=self.customer1_data['email']),
            created_at=datetime(2024, 3, 1, 0, 0, 0, tzinfo=timezone.utc),
            cancelled_at=datetime(2024, 3, 2, 0, 0, 0, tzinfo=timezone.utc),
            financial_status="voided", total_price="10.00", currency="USD",
            line_items=[self.line_item1]
        ).model_dump(mode='json')

        self.order4_cust1_id = "o2004"
        self.order4_cust1_closed_data = ShopifyOrderModel(
            id=self.order4_cust1_id, order_number=1004,
            customer=OrderCustomerInfo(id=self.cust1_id, email=self.customer1_data['email']),
            created_at=datetime(2024, 1, 5, 0, 0, 0, tzinfo=timezone.utc),
            closed_at=datetime(2024, 1, 20, 0, 0, 0, tzinfo=timezone.utc),
            financial_status="paid", total_price="20.00", currency="USD",
            line_items=[self.line_item2]
        ).model_dump(mode='json')

        self.order5_cust2_id = "o2005"
        self.order5_cust2_data = ShopifyOrderModel(
            id=self.order5_cust2_id, order_number=1005,
            customer=OrderCustomerInfo(id=self.cust2_id, email=self.customer2_data['email']),
            created_at=datetime(2024, 2, 20, 0, 0, 0, tzinfo=timezone.utc),
            financial_status="paid", total_price="10.00", currency="USD",
            line_items=[self.line_item1]
        ).model_dump(mode='json')
        
        self.order_malformed_date_id = "o2006"
        self.order_malformed_date_raw = {
            "id": self.order_malformed_date_id, "order_number": 1006,
            "customer": {"id": self.cust1_id, "email": self.customer1_data['email']},
            "created_at": "NOT_A_VALID_DATE", 
            "financial_status": "paid", "total_price": "5.00", "currency": "USD",
            "line_items": [self.line_item3_custom]
        }
        self.order_no_created_at_id = "o2007"
        self.order_no_created_at_raw = {
            "id": self.order_no_created_at_id, "order_number": 1007,
            "customer": {"id": self.cust1_id, "email": self.customer1_data['email']},
            "created_at": None, 
            "financial_status": "paid", "total_price": "5.00", "currency": "USD",
            "line_items": [self.line_item3_custom]
        }
        self.order_no_financial_status_id = "o2008"
        self.order_no_financial_status_raw = {
            "id": self.order_no_financial_status_id, "order_number": 1008,
            "customer": {"id": self.cust1_id, "email": self.customer1_data['email']},
            "created_at": datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z'),
            "financial_status": None, 
            "total_price": "5.00", "currency": "USD",
            "line_items": [self.line_item3_custom]
        }
        self.order_with_naive_datetime_id = "o2009"
        self.order_with_naive_datetime_raw = {
            "id": self.order_with_naive_datetime_id, "order_number": 1009,
            "customer": {"id": self.cust1_id, "email": self.customer1_data['email']},
            "created_at": "2024-01-15T10:00:00", 
            "financial_status": "pending", "total_price": "15.00", "currency": "USD",
            "line_items": [self.line_item1]
        }
        self.order_with_empty_dict_line_item_id = "o2010" # Renamed for clarity
        self.order_with_empty_dict_line_item_raw = {
            "id": self.order_with_empty_dict_line_item_id, "order_number": 1010,
            "customer": {"id": self.cust1_id, "email": self.customer1_data['email']},
            "created_at": datetime(2024, 1, 16, 0, 0, 0, tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z'),
            "financial_status": "paid", "total_price": "25.00", "currency": "USD",
            "line_items": [self.line_item1, {}, self.line_item2]
        }
        self.order_no_customer_field_id = "o2011"
        self.order_no_customer_field_raw = {
            "id": self.order_no_customer_field_id, "order_number": 1011,
            "customer": None,
            "created_at": datetime(2024,1,17, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "line_items": []
        }
        self.order_empty_customer_dict_id = "o2012"
        self.order_empty_customer_dict_raw = {
            "id": self.order_empty_customer_dict_id, "order_number": 1012,
            "customer": {},
            "created_at": datetime(2024,1,18, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "line_items": []
        }

        DB['orders'] = {
            self.order1_cust1_id: self.order1_cust1_data,
            self.order2_cust1_id: self.order2_cust1_data,
            self.order3_cust1_id: self.order3_cust1_cancelled_data,
            self.order4_cust1_id: self.order4_cust1_closed_data,
            self.order5_cust2_id: self.order5_cust2_data,
            self.order_malformed_date_id: self.order_malformed_date_raw,
            self.order_no_created_at_id: self.order_no_created_at_raw,
            self.order_no_financial_status_id: self.order_no_financial_status_raw,
            self.order_with_naive_datetime_id: self.order_with_naive_datetime_raw,
            self.order_with_empty_dict_line_item_id: self.order_with_empty_dict_line_item_raw,
            self.order_no_customer_field_id: self.order_no_customer_field_raw,
            self.order_empty_customer_dict_id: self.order_empty_customer_dict_raw
        }
        
        self.all_cust1_orders_by_id_asc = sorted([
            entry for entry_id, entry in DB['orders'].items()
            if isinstance(entry, dict) and entry.get('customer') and isinstance(entry.get('customer'), dict) and entry.get('customer', {}).get('id') == self.cust1_id
        ], key=lambda o: str(o.get('id', '')))

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_orders_match(self, result_orders_list, expected_db_order_dicts_list, requested_fields_param=None):
        self.assertEqual(len(result_orders_list), len(expected_db_order_dicts_list),
                         f"Mismatch in number of orders. Expected {len(expected_db_order_dicts_list)}, Got {len(result_orders_list)}."
                         f"\nResult: {result_orders_list}\nExpected raw: {expected_db_order_dicts_list}")

        result_orders_list.sort(key=lambda o: str(o.get('id', '')))
        valid_expected_orders = [o for o in expected_db_order_dicts_list if isinstance(o, dict)]
        expected_db_order_dicts_list_sorted = sorted(valid_expected_orders, key=lambda o: str(o.get('id', '')))

        for i, result_order_dict in enumerate(result_orders_list):
            expected_order_data_original = expected_db_order_dicts_list_sorted[i]
            result_order_id_str = str(result_order_dict.get('id'))
            expected_order_id_str = str(expected_order_data_original.get('id'))
            self.assertEqual(result_order_id_str, expected_order_id_str, "Order ID mismatch after sorting.")

            all_model_defined_fields = list(ShopifyOrderModel.model_fields.keys())
            fields_expected_in_response: List[str]

            if requested_fields_param is None or not requested_fields_param:
                fields_expected_in_response = all_model_defined_fields
            else:
                seen = set()
                unique_requested = [f for f in requested_fields_param if not (f in seen or seen.add(f))]
                fields_expected_in_response = [f for f in unique_requested if f in all_model_defined_fields]
            
            self.assertCountEqual(list(result_order_dict.keys()), fields_expected_in_response,
                                 f"Order ID {result_order_id_str} keys mismatch. Expected: {sorted(fields_expected_in_response)}, Got: {sorted(list(result_order_dict.keys()))}")

            for field in fields_expected_in_response:
                self.assertIn(field, result_order_dict, f"Field {field} missing in order {result_order_id_str}")
                expected_value = expected_order_data_original.get(field)
                actual_value = result_order_dict[field]

                if field == 'line_items' and isinstance(actual_value, list):
                    expected_line_items_raw = expected_order_data_original.get(field) 
                    expected_line_items_clean = expected_line_items_raw if expected_line_items_raw is not None else []
                    self.assertEqual(len(actual_value), len(expected_line_items_clean),
                                     f"Order ID {result_order_id_str}, field '{field}': number of line items mismatch. Actual: {actual_value}, Expected (cleaned): {expected_line_items_clean}")
                    default_li_fields = ['id', 'variant_id', 'product_id', 'title', 'quantity', 'price']
                    for idx, li_actual in enumerate(actual_value):
                        li_expected_raw = expected_line_items_clean[idx]
                        self.assertIsInstance(li_actual, dict)
                        self.assertCountEqual(li_actual.keys(), default_li_fields, f"Line item {idx} keys mismatch.")
                        for li_field in default_li_fields:
                            self.assertEqual(li_actual.get(li_field), li_expected_raw.get(li_field),
                                             f"Order ID {result_order_id_str}, LI {idx}, field {li_field} mismatch.")
                else:
                    self.assertEqual(actual_value, expected_value, 
                                     f"Order ID {result_order_id_str}, Field '{field}' mismatch. Got: {actual_value} (type {type(actual_value)}), Expected: {expected_value} (type {type(expected_value)})")

    def test_get_orders_cust1_default_status_open(self):
        response = get_customer_orders(customer_id=self.cust1_id)
        self.assertIn('orders', response)
        expected_open_orders = [
            o for o in self.all_cust1_orders_by_id_asc
            if not o.get('cancelled_at') and not (o.get('closed_at') and not o.get('cancelled_at'))
        ]
        self._assert_orders_match(response['orders'], expected_open_orders)

    def test_get_orders_cust1_status_closed(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="closed")
        self.assertIn('orders', response)
        expected_orders = [self.order4_cust1_closed_data]
        self._assert_orders_match(response['orders'], expected_orders)

    def test_get_orders_cust1_status_cancelled(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="cancelled")
        self.assertIn('orders', response)
        expected_orders = [self.order3_cust1_cancelled_data]
        self._assert_orders_match(response['orders'], expected_orders)

    def test_get_orders_cust1_status_any(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="any")
        self.assertIn('orders', response)
        self._assert_orders_match(response['orders'], self.all_cust1_orders_by_id_asc)

    def test_get_orders_cust2_has_one_order(self):
        response = get_customer_orders(customer_id=self.cust2_id, status="any")
        self.assertIn('orders', response)
        expected_orders = [self.order5_cust2_data]
        self._assert_orders_match(response['orders'], expected_orders)

    def test_get_orders_customer_no_orders(self):
        response = get_customer_orders(customer_id=self.cust_no_orders_id, status="any")
        self.assertIn('orders', response)
        self.assertEqual(len(response['orders']), 0)

    def test_get_orders_with_limit(self):
        limit = 2
        response = get_customer_orders(customer_id=self.cust1_id, status="any", limit=limit)
        self.assertIn('orders', response)
        self.assertEqual(len(response['orders']), limit)
        self._assert_orders_match(response['orders'], self.all_cust1_orders_by_id_asc[:limit])

    def test_get_orders_limit_exceeds_available(self):
        response = get_customer_orders(customer_id=self.cust2_id, status="any", limit=10)
        self.assertIn('orders', response)
        expected_orders = [self.order5_cust2_data]
        self._assert_orders_match(response['orders'], expected_orders)

    def test_get_orders_filter_created_at_min(self):
        min_date = "2024-02-01T00:00:00Z"
        response = get_customer_orders(customer_id=self.cust1_id, status="any", created_at_min=min_date)
        self.assertIn('orders', response)
        expected_orders_corrected = [self.order2_cust1_data, self.order3_cust1_cancelled_data]
        self._assert_orders_match(response['orders'], expected_orders_corrected)

    def test_get_orders_filter_created_at_max(self):
        max_date = "2024-01-20T00:00:00Z"
        response = get_customer_orders(customer_id=self.cust1_id, status="any", created_at_max=max_date)
        self.assertIn('orders', response)
        expected_orders = [self.order1_cust1_data, self.order4_cust1_closed_data, self.order_no_financial_status_raw, self.order_with_naive_datetime_raw, self.order_with_empty_dict_line_item_raw]
        self._assert_orders_match(response['orders'], expected_orders)

    def test_get_orders_filter_created_at_min_max_range(self):
        min_date = "2024-01-08T00:00:00Z"
        max_date = "2024-02-20T00:00:00Z"
        response = get_customer_orders(customer_id=self.cust1_id, status="any", created_at_min=min_date, created_at_max=max_date)
        self.assertIn('orders', response)
        expected_orders = [self.order1_cust1_data, self.order2_cust1_data, self.order_with_naive_datetime_raw, self.order_with_empty_dict_line_item_raw]
        self._assert_orders_match(response['orders'], expected_orders)

    def test_get_orders_filter_financial_status_paid(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="any", financial_status="paid")
        self.assertIn('orders', response)
        expected_orders = [o for o in self.all_cust1_orders_by_id_asc if isinstance(o, dict) and o.get('financial_status') == 'paid']
        self._assert_orders_match(response['orders'], expected_orders)

    def test_get_orders_filter_financial_status_pending(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="any", financial_status="pending")
        self.assertIn('orders', response)
        expected_orders = [self.order2_cust1_data, self.order_with_naive_datetime_raw] 
        self._assert_orders_match(response['orders'], expected_orders)
    
    def test_get_orders_filter_financial_status_case_insensitive(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="any", financial_status="PAID")
        self.assertIn('orders', response)
        expected_orders = [o for o in self.all_cust1_orders_by_id_asc if isinstance(o, dict) and o.get('financial_status') == 'paid']
        self._assert_orders_match(response['orders'], expected_orders)

    def test_get_orders_filter_financial_status_no_match(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="any", financial_status="authorized")
        self.assertIn('orders', response)
        self.assertEqual(len(response['orders']), 0)

    def test_get_orders_with_specific_fields(self):
        fields_to_request = ['id', 'order_number', 'total_price']
        response = get_customer_orders(customer_id=self.cust1_id, status="open", limit=1, fields=fields_to_request)
        self.assertIn('orders', response)
        self.assertEqual(len(response['orders']), 1)
        open_orders_cust1 = sorted([
            o for o in self.all_cust1_orders_by_id_asc 
            if isinstance(o, dict) and not o.get('cancelled_at') and not (o.get('closed_at') and not o.get('cancelled_at'))
        ], key=lambda o: str(o.get('id', '')))
        self._assert_orders_match(response['orders'], open_orders_cust1[:1], requested_fields_param=fields_to_request)

    def test_get_orders_with_fields_including_line_items(self):
        fields_to_request = ['id', 'line_items']
        response = get_customer_orders(customer_id=self.cust1_id, status="open", limit=1, fields=fields_to_request)
        self.assertIn('orders', response)
        self.assertEqual(len(response['orders']), 1)
        open_orders_cust1 = sorted([
            o for o in self.all_cust1_orders_by_id_asc 
            if isinstance(o, dict) and not o.get('cancelled_at') and not (o.get('closed_at') and not o.get('cancelled_at'))
        ], key=lambda o: str(o.get('id', '')))
        self._assert_orders_match(response['orders'], open_orders_cust1[:1], requested_fields_param=fields_to_request)

    def test_get_orders_fields_empty_list_returns_all_fields(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="open", limit=1, fields=[])
        self.assertIn('orders', response)
        self.assertEqual(len(response['orders']), 1)
        open_orders_cust1 = sorted([
            o for o in self.all_cust1_orders_by_id_asc 
            if isinstance(o, dict) and not o.get('cancelled_at') and not (o.get('closed_at') and not o.get('cancelled_at'))
        ], key=lambda o: str(o.get('id', '')))
        self._assert_orders_match(response['orders'], open_orders_cust1[:1], requested_fields_param=None)

    def test_get_orders_fields_with_non_model_field_ignored(self):
        fields_to_request = ['id', 'non_existent_field', 'total_price']
        expected_fields_in_response = ['id', 'total_price']
        response = get_customer_orders(customer_id=self.cust1_id, status="open", limit=1, fields=fields_to_request)
        self.assertIn('orders', response)
        open_orders_cust1 = sorted([
            o for o in self.all_cust1_orders_by_id_asc 
            if isinstance(o, dict) and not o.get('cancelled_at') and not (o.get('closed_at') and not o.get('cancelled_at'))
        ], key=lambda o: str(o.get('id', '')))
        self._assert_orders_match(response['orders'], open_orders_cust1[:1], requested_fields_param=expected_fields_in_response)

    def test_get_orders_malformed_db_date_and_none_db_date_excluded_by_date_filter(self):
        min_date = "2000-01-01T00:00:00Z"
        response = get_customer_orders(customer_id=self.cust1_id, status="any", created_at_min=min_date)
        returned_ids = {o['id'] for o in response['orders']}
        self.assertNotIn(self.order_malformed_date_id, returned_ids, "Order with malformed date should be excluded by date filter.")
        self.assertNotIn(self.order_no_created_at_id, returned_ids, "Order with no created_at date should be excluded by date filter.")

    def test_get_orders_malformed_db_date_when_date_filter_active(self):
        min_date = "2000-01-01T00:00:00Z" 
        response = get_customer_orders(customer_id=self.cust1_id, status="any", created_at_min=min_date)
        returned_ids = {o['id'] for o in response['orders']}
        self.assertNotIn(self.order_malformed_date_id, returned_ids)
        self.assertIn(self.order1_cust1_id, returned_ids)

    def test_get_orders_malformed_db_date_included_if_no_date_filter(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="any")
        returned_ids = {o['id'] for o in response['orders']}
        self.assertIn(self.order_malformed_date_id, returned_ids, "Order with malformed date should be included if no date filter.")

    def test_get_orders_none_db_date_included_if_no_date_filter(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="any")
        returned_ids = {o['id'] for o in response['orders']}
        self.assertIn(self.order_no_created_at_id, returned_ids, "Order with no created_at date should be included if no date filter.")

    def test_get_orders_filter_missing_financial_status_in_db(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="any", financial_status="paid")
        returned_ids = {o['id'] for o in response['orders']}
        self.assertNotIn(self.order_no_financial_status_id, returned_ids)
        response_any_fs = get_customer_orders(customer_id=self.cust1_id, status="any")
        returned_ids_any_fs = {o['id'] for o in response_any_fs['orders']}
        self.assertIn(self.order_no_financial_status_id, returned_ids_any_fs)
        
    def test_input_date_with_explicit_timezone_offset(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="any", created_at_min="2024-01-10T12:00:00+02:00")
        returned_ids = {o['id'] for o in response['orders']}
        self.assertIn(self.order1_cust1_id, returned_ids)
        self.assertIn(self.order_with_naive_datetime_id, returned_ids)
        self.assertIn(self.order_with_empty_dict_line_item_id, returned_ids) # Corrected attribute name
        self.assertIn(self.order2_cust1_id, returned_ids)
        self.assertIn(self.order3_cust1_id, returned_ids)
        self.assertNotIn(self.order4_cust1_id, returned_ids)
        self.assertNotIn(self.order_no_financial_status_id, returned_ids)

    def test_get_orders_input_date_naive_string(self):
        # Covers the if parsed_date.tzinfo is None branch for input date parsing
        response = get_customer_orders(customer_id=self.cust1_id, status="any", created_at_min="2024-01-10T10:00:00")
        returned_ids = {o['id'] for o in response['orders']}
        # Expect orders created at or after 2024-01-10 10:00:00 UTC
        self.assertIn(self.order1_cust1_id, returned_ids) # 2024-01-10 10:00:00Z
        self.assertIn(self.order2_cust1_id, returned_ids) # 2024-02-15 12:00:00Z
        self.assertIn(self.order3_cust1_id, returned_ids) # 2024-03-01 00:00:00Z
        self.assertIn(self.order_with_naive_datetime_id, returned_ids) # DB: 2024-01-15T10:00:00 (parsed as UTC)
        self.assertIn(self.order_with_empty_dict_line_item_id, returned_ids) # 2024-01-16 00:00:00Z
        self.assertNotIn(self.order4_cust1_id, returned_ids) # 2024-01-05
        self.assertNotIn(self.order_no_financial_status_id, returned_ids) # 2024-01-01

    def test_get_orders_with_db_order_having_naive_created_at(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="any", created_at_min="2024-01-15T09:00:00Z")
        returned_ids = {o['id'] for o in response['orders']}
        self.assertIn(self.order_with_naive_datetime_id, returned_ids)
        response = get_customer_orders(customer_id=self.cust1_id, status="any", created_at_min="2024-01-15T11:00:00Z")
        returned_ids = {o['id'] for o in response['orders']}
        self.assertNotIn(self.order_with_naive_datetime_id, returned_ids)
        response = get_customer_orders(customer_id=self.cust1_id, status="any", created_at_max="2024-01-15T11:00:00Z")
        returned_ids = {o['id'] for o in response['orders']}
        self.assertIn(self.order_with_naive_datetime_id, returned_ids)
        response = get_customer_orders(customer_id=self.cust1_id, status="any", created_at_max="2024-01-15T09:00:00Z")
        returned_ids = {o['id'] for o in response['orders']}
        self.assertNotIn(self.order_with_naive_datetime_id, returned_ids)

    def test_get_orders_with_empty_dict_line_item_in_db(self):
        fields_to_request = ['id', 'line_items']
        response = get_customer_orders(customer_id=self.cust1_id, status="any", fields=fields_to_request)
        found_order = None
        for order_dict in response['orders']:
            if order_dict['id'] == self.order_with_empty_dict_line_item_id:
                found_order = order_dict
                break
        self.assertIsNotNone(found_order, "Order with an empty dict line item not found in response.")
        if found_order:
            self.assertIn('line_items', found_order)
            actual_line_items = found_order['line_items']
            self.assertEqual(len(actual_line_items), 3, "Should process all 3 line items, including the empty dict.")
            empty_li_processed = {
                'id': None, 'variant_id': None, 'product_id': None, 'title': None, 'quantity': None, 'price': None
            }
            self.assertIn(empty_li_processed, actual_line_items)
            processed_line_item1_data = {k: self.line_item1.get(k) for k in ['id', 'variant_id', 'product_id', 'title', 'quantity', 'price']}
            processed_line_item2_data = {k: self.line_item2.get(k) for k in ['id', 'variant_id', 'product_id', 'title', 'quantity', 'price']}
            self.assertIn(processed_line_item1_data, actual_line_items)
            self.assertIn(processed_line_item2_data, actual_line_items)

    def test_get_orders_appends_empty_dict_for_all_invalid_fields(self):
        DB['orders'] = { self.order1_cust1_id: self.order1_cust1_data }
        fields_to_request = ["invalid_field_1", "non_existent_field_2"]
        response = get_customer_orders(customer_id=self.cust1_id, status="any", fields=fields_to_request)
        self.assertIn('orders', response)
        self.assertEqual(len(response['orders']), 1, "Should return one order structure even if all fields are invalid.")
        self.assertEqual(response['orders'][0], {}, "Order should be an empty dict if all requested fields were invalid.")

    def test_single_simple_order_processed_and_appended(self):
        DB['orders'] = {
            self.order1_cust1_id: self.order1_cust1_data
        }
        response = get_customer_orders(customer_id=self.cust1_id, status="any")
        self.assertIn('orders', response)
        self.assertEqual(len(response['orders']), 1)
        self.assertEqual(response['orders'][0]['id'], self.order1_cust1_id)
        self._assert_orders_match(response['orders'], [self.order1_cust1_data])

    def test_get_orders_skips_orders_with_invalid_customer_info(self):
        response_cust1 = get_customer_orders(customer_id=self.cust1_id, status="any")
        returned_ids_cust1 = {o['id'] for o in response_cust1['orders']}
        self.assertNotIn(self.order_no_customer_field_id, returned_ids_cust1)
        self.assertNotIn(self.order_empty_customer_dict_id, returned_ids_cust1)
        self.assertIn(self.order1_cust1_id, returned_ids_cust1)

    # --- since_id tests ---
    def test_get_orders_filter_by_since_id(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="any", since_id=self.order2_cust1_id) # o2002
        self.assertIn('orders', response)
        # Expected for cust1, after o2002, sorted: o2003, o2004, o2006, o2007, o2008, o2009, o2010
        # self.all_cust1_orders_by_id_asc is already sorted and filtered for cust1
        expected_orders = [o for o in self.all_cust1_orders_by_id_asc if str(o.get('id')) > self.order2_cust1_id]
        self._assert_orders_match(response['orders'], expected_orders)

    def test_get_orders_filter_by_since_id_and_limit(self):
        response = get_customer_orders(customer_id=self.cust1_id, status="any", since_id=self.order1_cust1_id, limit=2)
        self.assertIn('orders', response)
        self.assertEqual(len(response['orders']), 2)
        expected_orders_after_since = [o for o in self.all_cust1_orders_by_id_asc if str(o.get('id')) > self.order1_cust1_id]
        self._assert_orders_match(response['orders'], expected_orders_after_since[:2])

    def test_get_orders_filter_by_since_id_no_results(self):
        highest_id_cust1 = self.all_cust1_orders_by_id_asc[-1]['id']
        response = get_customer_orders(customer_id=self.cust1_id, status="any", since_id=highest_id_cust1)
        self.assertIn('orders', response)
        self.assertEqual(len(response['orders']), 0)

    def test_get_orders_filter_by_since_id_with_status_filter(self):
        # Open orders for cust1
        open_orders_cust1 = [
            o for o in self.all_cust1_orders_by_id_asc
            if not o.get('cancelled_at') and not (o.get('closed_at') and not o.get('cancelled_at'))
        ]
        open_orders_cust1.sort(key=lambda o: str(o.get('id','')))
        
        since_this_id = self.order1_cust1_id # "o2001" (which is open)
        response = get_customer_orders(customer_id=self.cust1_id, status="open", since_id=since_this_id)
        self.assertIn('orders', response)
        
        expected_orders = [o for o in open_orders_cust1 if str(o.get('id')) > since_this_id]
        self._assert_orders_match(response['orders'], expected_orders)

    def test_error_invalid_since_id_type(self):
        self.assert_error_behavior(get_customer_orders, custom_errors.InvalidInputError, 
                                   "'since_id' must be a non-empty string.", 
                                   customer_id=self.cust1_id, since_id=12345)

    def test_error_invalid_since_id_empty(self):
        self.assert_error_behavior(get_customer_orders, custom_errors.InvalidInputError, 
                                   "'since_id' must be a non-empty string.", 
                                   customer_id=self.cust1_id, since_id="")

    # --- Error Cases ---
    def test_error_customer_not_found(self):
        self.assert_error_behavior(get_customer_orders, custom_errors.NotFoundError, 
                                   "Customer with ID 'nonexistentcust123' not found.",
                                   customer_id="nonexistentcust123")

    def test_error_invalid_customer_id_empty(self):
        self.assert_error_behavior(get_customer_orders, custom_errors.InvalidInputError, 
                                   "customer_id must be a non-empty string.",
                                   customer_id="")
        
    def test_error_invalid_customer_id_type(self):
        self.assert_error_behavior(get_customer_orders, custom_errors.InvalidInputError, 
                                   "customer_id must be a non-empty string.",
                                   customer_id=12345) # type: ignore

    def test_error_invalid_status_value(self):
        self.assert_error_behavior(get_customer_orders, custom_errors.InvalidInputError, 
                                   "Invalid status 'unknown_status'. Must be one of ['open', 'closed', 'cancelled', 'any'].",
                                   customer_id=self.cust1_id, status="unknown_status")

    def test_error_invalid_limit_too_low(self):
        self.assert_error_behavior(get_customer_orders, custom_errors.InvalidInputError, 
                                   "Limit must be an integer between 1 and 250.",
                                   customer_id=self.cust1_id, limit=0)

    def test_error_invalid_limit_too_high(self):
        self.assert_error_behavior(get_customer_orders, custom_errors.InvalidInputError, 
                                   "Limit must be an integer between 1 and 250.",
                                   customer_id=self.cust1_id, limit=251)

    def test_error_invalid_limit_type(self):
        self.assert_error_behavior(get_customer_orders, custom_errors.InvalidInputError, 
                                   "Limit must be an integer between 1 and 250.",
                                   customer_id=self.cust1_id, limit="abc") # type: ignore

    def test_error_invalid_date_format_created_at_min(self):
        self.assert_error_behavior(get_customer_orders, custom_errors.InvalidDateTimeFormatError, 
                                   "Invalid format for created_at_min: 'bad-date'. Use ISO 8601 format.",
                                   customer_id=self.cust1_id, created_at_min="bad-date")

    def test_error_invalid_date_type_created_at_max(self):
        self.assert_error_behavior(get_customer_orders, custom_errors.InvalidInputError, 
                                   "created_at_max must be a string.",
                                   customer_id=self.cust1_id, created_at_max=12345) # type: ignore

    def test_error_invalid_fields_type_not_list(self):
        self.assert_error_behavior(get_customer_orders, custom_errors.InvalidInputError, 
                                   "'fields' must be a list of non-empty strings.",
                                   customer_id=self.cust1_id, fields="id,name") # type: ignore

    def test_error_invalid_fields_list_contains_non_string(self):
        self.assert_error_behavior(get_customer_orders, custom_errors.InvalidInputError, 
                                   "'fields' must be a list of non-empty strings.",
                                   customer_id=self.cust1_id, fields=['id', 123]) # type: ignore
        
    def test_error_invalid_fields_list_contains_empty_string(self):
        self.assert_error_behavior(get_customer_orders, custom_errors.InvalidInputError, 
                                   "'fields' must be a list of non-empty strings.",
                                   customer_id=self.cust1_id, fields=['id', ''])


if __name__ == '__main__':
    unittest.main()
