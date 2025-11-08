import unittest
import copy
from datetime import datetime, timezone # Required for model instantiation

from shopify.SimulationEngine import custom_errors
from shopify.SimulationEngine.db import DB
from shopify.customers import shopify_get_customers as get_customers
from shopify.SimulationEngine.models import ShopifyCustomerModel
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestGetCustomers(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.c1_id, self.c2_id, self.c3_id, self.c4_id = "101", "102", "103", "104"
        self.c_non_int_id = "non_int_id_abc"
        self.c_no_created_at_id = "105"
        self.c_no_updated_at_id = "106"

        self.customer1_data = ShopifyCustomerModel(
            id=self.c1_id, email="test1@example.com", first_name="Test1",
            created_at=datetime(2023, 1, 10, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 10, 10, 0, 0, tzinfo=timezone.utc)
        ).model_dump(mode='json')
        self.customer2_data = ShopifyCustomerModel(
            id=self.c2_id, email="test2@example.com", first_name="Test2",
            created_at=datetime(2023, 2, 15, 12, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 2, 18, 12, 0, 0, tzinfo=timezone.utc)
        ).model_dump(mode='json')
        self.customer3_data = ShopifyCustomerModel(
            id=self.c3_id, email="test3@example.com", first_name="Test3",
            created_at=datetime(2023, 3, 20, 14, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 3, 25, 14, 0, 0, tzinfo=timezone.utc)
        ).model_dump(mode='json')
        self.customer4_data = ShopifyCustomerModel(
            id=self.c4_id, email="test4@example.com", first_name="Test4",
            created_at=datetime(2023, 4, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 4, 1, 0, 0, 0, tzinfo=timezone.utc)
        ).model_dump(mode='json')

        self.customer_non_int_id_data = ShopifyCustomerModel(
            id=self.c_non_int_id, email="nonint@example.com",
            created_at=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2023, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        ).model_dump(mode='json')

        self.customer_no_created_at_data = {
            "id": self.c_no_created_at_id, "email": "nocreated@example.com", "first_name": "NoCreate",
            "created_at": None,
            "updated_at": datetime(2023, 1, 2, 0, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "orders_count": 0, "state": None, "total_spent": "0.00", "phone": None, "tags": None,
            "default_address": None, "addresses": []
        }
        self.customer_no_updated_at_data = {
            "id": self.c_no_updated_at_id, "email": "noupdated@example.com", "first_name": "NoUpdate",
            "created_at": datetime(2023, 1, 3, 0, 0, 0, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
            "updated_at": None,
            "orders_count": 0, "state": None, "total_spent": "0.00", "phone": None, "tags": None,
            "default_address": None, "addresses": []
        }

        DB['customers'] = {
            self.c1_id: self.customer1_data,
            self.c2_id: self.customer2_data,
            self.c3_id: self.customer3_data,
            self.c4_id: self.customer4_data,
            self.c_non_int_id: self.customer_non_int_id_data,
            self.c_no_created_at_id: self.customer_no_created_at_data,
            self.c_no_updated_at_id: self.customer_no_updated_at_data,
        }

        # For general tests including non-standard IDs and missing dates
        self.all_db_customers_including_special = [
            self.customer1_data, self.customer2_data, self.customer3_data, self.customer4_data,
            self.customer_non_int_id_data, self.customer_no_created_at_data, self.customer_no_updated_at_data
        ]
        # For tests that rely on numeric ID sorting (e.g. after since_id)
        self.numerically_sortable_customers = [
            self.customer1_data, self.customer2_data, self.customer3_data, self.customer4_data,
            self.customer_no_created_at_data, self.customer_no_updated_at_data
        ]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_customer_lists_match(self, result_customers_list, expected_db_customers_list, requested_fields_param=None):
        self.assertEqual(len(result_customers_list), len(expected_db_customers_list),
                         f"Mismatch in number of customers. Expected {len(expected_db_customers_list)}, Got {len(result_customers_list)}\nResult: {result_customers_list}\nExpected: {expected_db_customers_list}")

        expected_customers_map = {str(cust['id']): cust for cust in expected_db_customers_list}

        for result_cust_dict in result_customers_list:
            result_cust_id_str = str(result_cust_dict['id'])
            self.assertIn(result_cust_id_str, expected_customers_map, f"Returned customer ID {result_cust_id_str} not found in expected list. Expected IDs: {list(expected_customers_map.keys())}")
            
            expected_cust_data_original = expected_customers_map[result_cust_id_str]
            all_model_defined_fields = list(ShopifyCustomerModel.model_fields.keys())
            fields_expected_in_response = []

            if requested_fields_param is None or not requested_fields_param:
                fields_expected_in_response = all_model_defined_fields
            else:
                seen = set()
                unique_requested_fields = [x for x in requested_fields_param if not (x in seen or seen.add(x))]
                fields_expected_in_response = [f for f in unique_requested_fields if f in all_model_defined_fields]
            
            self.assertCountEqual(list(result_cust_dict.keys()), fields_expected_in_response,
                                 f"Customer ID {result_cust_id_str} keys mismatch. Expected: {sorted(fields_expected_in_response)}, Got: {sorted(list(result_cust_dict.keys()))}")

            for field in fields_expected_in_response:
                self.assertIn(field, result_cust_dict, f"Field {field} missing in customer {result_cust_id_str}")
                expected_value = expected_cust_data_original.get(field)
                self.assertEqual(result_cust_dict[field], expected_value, 
                                 f"Customer ID {result_cust_id_str}, Field '{field}' mismatch. Got: {result_cust_dict[field]} (type {type(result_cust_dict[field])}), Expected: {expected_value} (type {type(expected_value)})")

    def test_get_customers_no_filters_default_limit(self):
        response = get_customers()
        self.assertIn('customers', response)
        # Expect all customers, order defined by new sort_key_mixed_types in get_customers
        # (numeric IDs first, then non-numeric)
        def sort_key(customer):
            try: return (0, int(customer['id']))
            except (ValueError, TypeError): return (1, customer['id'])
        expected_sorted_list = sorted(self.all_db_customers_including_special, key=sort_key)
        self._assert_customer_lists_match(response['customers'], expected_sorted_list)

    def test_get_customers_with_limit(self):
        limit = 2
        response = get_customers(limit=limit)
        self.assertIn('customers', response)
        self.assertEqual(len(response['customers']), limit)
        def sort_key(customer):
            try: return (0, int(customer['id']))
            except (ValueError, TypeError): return (1, customer['id'])
        expected_sorted_list = sorted(self.all_db_customers_including_special, key=sort_key)
        self._assert_customer_lists_match(response['customers'], expected_sorted_list[:limit])

    def test_get_customers_filter_by_ids(self):
        ids_to_filter = [self.c1_id, self.c3_id, self.c_non_int_id]
        response = get_customers(ids=ids_to_filter)
        self.assertIn('customers', response)
        expected_customers = [c for c in self.all_db_customers_including_special if c['id'] in ids_to_filter]
        # Sort expected_customers to match the function's output order if necessary
        def sort_key(customer):
            try: return (0, int(customer['id']))
            except (ValueError, TypeError): return (1, customer['id'])
        expected_customers.sort(key=sort_key)        
        self._assert_customer_lists_match(response['customers'], expected_customers)

    def test_get_customers_filter_by_single_id(self):
        ids_to_filter = [self.c2_id]
        response = get_customers(ids=ids_to_filter)
        self.assertIn('customers', response)
        expected_customers = [self.customer2_data]
        self._assert_customer_lists_match(response['customers'], expected_customers)

    def test_get_customers_filter_by_ids_non_existent_id(self):
        ids_to_filter = ["999", self.c1_id]
        response = get_customers(ids=ids_to_filter)
        self.assertIn('customers', response)
        expected_customers = [self.customer1_data]
        self._assert_customer_lists_match(response['customers'], expected_customers)

    def test_get_customers_filter_by_ids_empty_list(self):
        response = get_customers(ids=[]) 
        self.assertIn('customers', response)
        def sort_key(customer):
            try: return (0, int(customer['id']))
            except (ValueError, TypeError): return (1, customer['id'])
        expected_sorted_list = sorted(self.all_db_customers_including_special, key=sort_key)
        self._assert_customer_lists_match(response['customers'], expected_sorted_list)

    def test_get_customers_filter_by_since_id(self):
        response = get_customers(since_id=102) 
        self.assertIn('customers', response)
        expected_customers = [c for c in self.numerically_sortable_customers if int(c['id']) > 102]
        expected_customers.sort(key=lambda c: int(c['id'])) # Ensure sorted for assertion
        self._assert_customer_lists_match(response['customers'], expected_customers)

    def test_get_customers_filter_by_since_id_and_limit(self):
        response = get_customers(since_id=101, limit=1)
        self.assertIn('customers', response)
        # From numerically_sortable_customers, IDs > 101 are 102, 103, 104, 105, 106. Sorted: 102 is first.
        expected_customers = [self.customer2_data]
        self._assert_customer_lists_match(response['customers'], expected_customers)

    def test_get_customers_filter_by_created_at_min(self):
        response = get_customers(created_at_min="2023-02-01T00:00:00Z")
        self.assertIn('customers', response)
        expected_ids = {self.c2_id, self.c3_id, self.c4_id} # c1, non_int, no_upd are before; no_create is None
        returned_ids = {c['id'] for c in response['customers']}
        self.assertEqual(returned_ids, expected_ids)

    def test_get_customers_filter_by_created_at_max(self):
        response = get_customers(created_at_max="2023-02-20T00:00:00Z")
        self.assertIn('customers', response)
        expected_ids = {self.c1_id, self.c2_id, self.c_non_int_id, self.c_no_updated_at_id} # no_create is None
        returned_ids = {c['id'] for c in response['customers']}
        self.assertEqual(returned_ids, expected_ids)

    def test_get_customers_filter_by_created_at_min_and_max(self):
        response = get_customers(created_at_min="2023-02-01T00:00:00Z", created_at_max="2023-03-01T00:00:00Z")
        self.assertIn('customers', response)
        expected_ids = {self.c2_id} # no_create is None
        returned_ids = {c['id'] for c in response['customers']}
        self.assertEqual(returned_ids, expected_ids)

    def test_get_customers_filter_by_updated_at_min(self):
        response = get_customers(updated_at_min="2023-03-01T00:00:00Z")
        self.assertIn('customers', response)
        expected_ids = {self.c3_id, self.c4_id} # no_upd is None
        returned_ids = {c['id'] for c in response['customers']}
        self.assertEqual(returned_ids, expected_ids)

    def test_get_customers_filter_by_updated_at_max(self):
        response = get_customers(updated_at_max="2023-02-20T00:00:00Z")
        self.assertIn('customers', response)
        expected_ids = {self.c1_id, self.c2_id, self.c_non_int_id, self.c_no_created_at_id} # no_upd is None
        returned_ids = {c['id'] for c in response['customers']}
        self.assertEqual(returned_ids, expected_ids)
    
    def test_get_customers_filter_by_updated_at_min_and_max(self):
        response = get_customers(updated_at_min="2023-02-01T00:00:00Z", updated_at_max="2023-03-01T00:00:00Z")
        self.assertIn('customers', response)
        expected_ids = {self.c2_id} # no_upd is None
        returned_ids = {c['id'] for c in response['customers']}
        self.assertEqual(returned_ids, expected_ids)

    def test_get_customers_combined_filters(self):
        response = get_customers(
            created_at_min="2023-02-01T00:00:00Z", 
            ids=[self.c2_id, self.c3_id],
            limit=1
        ) 
        self.assertIn('customers', response)
        expected_customers = [self.customer2_data] 
        self._assert_customer_lists_match(response['customers'], expected_customers)

    def test_get_customers_with_specific_fields(self):
        fields_to_request = ['id', 'email', 'state']
        response = get_customers(limit=2, fields=fields_to_request)
        self.assertIn('customers', response)
        self.assertEqual(len(response['customers']), 2)
        for cust in response['customers']:
            self.assertEqual(set(cust.keys()), set(fields_to_request))

    def test_get_customers_fields_empty_list_returns_all_fields(self):
        response = get_customers(limit=1, fields=[])
        self.assertIn('customers', response)
        self.assertEqual(len(response['customers']), 1)
        for cust in response['customers']:
             self.assertEqual(set(cust.keys()), set(ShopifyCustomerModel.model_fields.keys()))

    def test_get_customers_validation_error_fields_with_invalid_field_names(self):
        fields_to_request = ['id', 'email', 'non_existent_field']
        self.assert_error_behavior(
            func_to_call=get_customers,
            expected_exception_type=custom_errors.InvalidParameterError,
            expected_message="Invalid field names: non_existent_field. Valid fields are: id, email, first_name, last_name, orders_count, state, total_spent, phone, tags, created_at, updated_at, default_address, addresses, payment_methods, default_payment_method_id",
            limit=1,
            fields=fields_to_request
        )

    def test_get_customers_no_results_found_due_to_filters(self):
        response = get_customers(created_at_min="2025-01-01T00:00:00Z")
        self.assertIn('customers', response)
        self.assertEqual(len(response['customers']), 0)

    def test_get_customers_date_format_with_offset(self):
        response = get_customers(created_at_min="2023-02-15T11:00:00+00:00", created_at_max="2023-02-15T13:00:00+00:00")
        self.assertIn('customers', response)
        expected_customers = [self.customer2_data]
        self._assert_customer_lists_match(response['customers'], expected_customers)

    def test_get_customers_sort_with_non_integer_id_no_since_id(self):
        # Ensure non-integer ID is handled by sort_key_mixed_types when since_id is NOT active
        response = get_customers(ids=[self.c_non_int_id, self.c1_id])
        self.assertIn('customers', response)
        returned_ids = {c['id'] for c in response['customers']}
        self.assertIn(self.c_non_int_id, returned_ids)
        self.assertIn(self.c1_id, returned_ids)
        self.assertEqual(len(response['customers']), 2)
        # Check order: c1 (numeric) should come before non_int_id
        self.assertTrue(response['customers'][0]['id'] == self.c1_id or response['customers'][1]['id'] == self.c1_id) # Order can vary based on other sort factors if IDs are same type
        if response['customers'][0]['id'] == self.c1_id : self.assertEqual(response['customers'][1]['id'], self.c_non_int_id)
        else: self.assertEqual(response['customers'][0]['id'], self.c_non_int_id); self.assertEqual(response['customers'][1]['id'], self.c1_id)

    def test_get_customers_filter_created_at_with_missing_created_at_field(self):
        response = get_customers(created_at_min="2023-01-01T00:00:00Z", ids=[self.c_no_created_at_id, self.c1_id])
        self.assertIn('customers', response)
        returned_ids = {c['id'] for c in response['customers']}
        self.assertNotIn(self.c_no_created_at_id, returned_ids)
        self.assertIn(self.c1_id, returned_ids)
        self.assertEqual(len(response['customers']), 1)
        self.assertEqual(response['customers'][0]['id'], self.c1_id)

    def test_get_customers_filter_updated_at_with_missing_updated_at_field(self):
        response = get_customers(updated_at_min="2023-01-01T00:00:00Z", ids=[self.c_no_updated_at_id, self.c1_id])
        self.assertIn('customers', response)
        returned_ids = {c['id'] for c in response['customers']}
        self.assertNotIn(self.c_no_updated_at_id, returned_ids)
        self.assertIn(self.c1_id, returned_ids)
        self.assertEqual(len(response['customers']), 1)
        self.assertEqual(response['customers'][0]['id'], self.c1_id)

    def test_get_customers_filter_created_at_malformed_db_date(self):
        # Add a customer with a malformed created_at date to DB
        malformed_id = "malformed_date_cust"
        DB['customers'][malformed_id] = copy.deepcopy(self.customer1_data)
        DB['customers'][malformed_id]['id'] = malformed_id
        DB['customers'][malformed_id]['created_at'] = "not-a-date"
        
        response = get_customers(created_at_min="2023-01-01T00:00:00Z", ids=[malformed_id, self.c2_id])
        self.assertIn('customers', response)
        returned_ids = {c['id'] for c in response['customers']}
        self.assertNotIn(malformed_id, returned_ids) # Malformed date customer should be filtered out
        self.assertIn(self.c2_id, returned_ids)
        self.assertEqual(len(response['customers']), 1)

    def test_get_customers_filter_updated_at_malformed_db_date(self):
        malformed_id = "malformed_date_cust_upd"
        DB['customers'][malformed_id] = copy.deepcopy(self.customer1_data)
        DB['customers'][malformed_id]['id'] = malformed_id
        DB['customers'][malformed_id]['updated_at'] = " совершенно не дата"

        response = get_customers(updated_at_min="2023-01-01T00:00:00Z", ids=[malformed_id, self.c2_id])
        self.assertIn('customers', response)
        returned_ids = {c['id'] for c in response['customers']}
        self.assertNotIn(malformed_id, returned_ids) # Malformed date customer should be filtered out
        self.assertIn(self.c2_id, returned_ids)
        self.assertEqual(len(response['customers']), 1)

    # --- Error Cases ---
    def test_get_customers_invalid_limit_too_low(self):
        self.assert_error_behavior(get_customers, custom_errors.InvalidParameterError, "Limit must be an integer between 1 and 250.", limit=0)

    def test_get_customers_invalid_limit_too_high(self):
        self.assert_error_behavior(get_customers, custom_errors.InvalidParameterError, "Limit must be an integer between 1 and 250.", limit=251)
        
    def test_get_customers_invalid_limit_type(self):
        self.assert_error_behavior(get_customers, custom_errors.InvalidParameterError, "Limit must be an integer between 1 and 250.", limit="abc")

    def test_get_customers_invalid_ids_type_not_list(self):
        self.assert_error_behavior(get_customers, custom_errors.InvalidParameterError, "'ids' must be a list of non-empty strings.", ids="123,456")

    def test_get_customers_invalid_ids_list_contains_non_string(self):
        self.assert_error_behavior(get_customers, custom_errors.InvalidParameterError, "'ids' must be a list of non-empty strings.", ids=[self.c1_id, 123])
        
    def test_get_customers_invalid_ids_list_contains_empty_string(self):
        self.assert_error_behavior(get_customers, custom_errors.InvalidParameterError, "'ids' must be a list of non-empty strings.", ids=[self.c1_id, ""])

    def test_get_customers_invalid_since_id_type(self):
        self.assert_error_behavior(get_customers, custom_errors.InvalidParameterError, "'since_id' must be a non-negative integer.", since_id="abc")

    def test_get_customers_invalid_since_id_negative(self):
        self.assert_error_behavior(get_customers, custom_errors.InvalidParameterError, "'since_id' must be a non-negative integer.", since_id=-1)

    def test_get_customers_invalid_date_format_created_at_min(self):
        self.assert_error_behavior(get_customers, custom_errors.InvalidDateTimeFormatError, "Invalid format for created_at_min: 'bad-date'. Use ISO 8601 format.", created_at_min="bad-date")

    def test_get_customers_invalid_date_type_created_at_max(self):
        self.assert_error_behavior(get_customers, custom_errors.InvalidParameterError, "created_at_max must be a string.", created_at_max=12345)

    def test_get_customers_invalid_date_format_updated_at_min(self):
        self.assert_error_behavior(get_customers, custom_errors.InvalidDateTimeFormatError, "Invalid format for updated_at_min: '2023/01/01'. Use ISO 8601 format.", updated_at_min="2023/01/01")

    def test_get_customers_invalid_fields_type(self):
        self.assert_error_behavior(get_customers, custom_errors.InvalidParameterError, "fields must be a list.", fields="id,email")

    def test_get_customers_invalid_fields_list_contains_non_string(self):
        self.assert_error_behavior(get_customers, custom_errors.InvalidParameterError, "All items in fields list must be strings.", fields=['id', 123])

    def test_get_customers_invalid_fields_list_contains_empty_string(self):
        self.assert_error_behavior(get_customers, custom_errors.InvalidParameterError, "Field names in fields list cannot be empty.", fields=['id', ''])


if __name__ == '__main__':
    unittest.main()
