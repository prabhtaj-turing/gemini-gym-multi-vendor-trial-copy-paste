import unittest
import copy
from shopify.SimulationEngine import custom_errors
from shopify.SimulationEngine.db import DB
from shopify.orders import shopify_get_orders_count
from common_utils.base_case import BaseTestCaseWithErrorHandler # Assuming this is correctly located

class TestShopifyGetOrdersCount(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.sample_orders_dict = {
            "1": {"id": "1", "created_at": "2023-01-15T10:00:00Z", "updated_at": "2023-01-16T11:00:00Z", "financial_status": "paid", "fulfillment_status": "unshipped", "status": "open"},
            "2": {"id": "2", "created_at": "2023-02-10T12:00:00Z", "updated_at": "2023-02-11T13:00:00Z", "financial_status": "pending", "fulfillment_status": "unshipped", "status": "open"},
            "3": {"id": "3", "created_at": "2023-03-05T14:00:00Z", "updated_at": "2023-03-06T15:00:00Z", "closed_at": "2023-03-06T16:00:00Z", "financial_status": "paid", "fulfillment_status": "shipped", "status": "closed"},
            "4": {"id": "4", "created_at": "2023-01-20T08:00:00Z", "updated_at": "2023-01-25T09:00:00Z", "closed_at": "2023-01-25T10:00:00Z", "financial_status": "refunded", "fulfillment_status": "fulfilled", "status": "closed"},
            "5": {"id": "5", "created_at": "2022-12-01T00:00:00Z", "updated_at": "2023-04-01T10:00:00Z", "financial_status": "partially_paid", "fulfillment_status": "partial", "status": "open"},
            "6": {"id": "6", "created_at": "2023-03-10T10:00:00Z", "updated_at": "2023-03-10T10:00:00Z", "financial_status": "voided", "fulfillment_status": "unshipped", "status": "open"},
            "7": {"id": "7", "created_at": "2023-03-15T10:00:00Z", "updated_at": "2023-03-15T11:00:00Z", "financial_status": "unpaid", "fulfillment_status": "unshipped", "status": "open"},
            "8": {"id": "8", "created_at": "2023-03-20T10:00:00Z", "updated_at": "2023-03-20T11:00:00Z", "financial_status": "authorized", "fulfillment_status": "unshipped", "status": "open"},
            "9": {"id": "9", "created_at": "2023-03-25T10:00:00Z", "updated_at": "2023-03-25T11:00:00Z", "financial_status": "partially_refunded", "fulfillment_status": "shipped", "status": "open"},
            "10": {"id": "10", "created_at": "2023-04-01T10:00:00Z", "updated_at": "2023-04-01T11:00:00Z", "financial_status": "paid", "fulfillment_status": None, "status": "open"},
            "11": {"id": "11", "updated_at": "2023-04-02T10:00:00Z", "financial_status": "paid", "fulfillment_status": "unshipped", "status": "open"},
            "12": {"id": "12", "created_at": "2023-04-03T10:00:00Z", "financial_status": "paid", "fulfillment_status": "unshipped", "status": "open"},
        }
        DB['orders'] = copy.deepcopy(self.sample_orders_dict)

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_get_count_default_parameters(self):
        result = shopify_get_orders_count()
        self.assertEqual(result, {"count": 10})

    def test_get_count_no_orders_in_db(self):
        DB['orders'] = {}
        result = shopify_get_orders_count()
        self.assertEqual(result, {"count": 0})

    def test_get_count_no_matching_orders(self):
        # This test now correctly checks for the InvalidParameterError
        # The call to shopify_get_orders_count is inside assert_error_behavior
        VALID_FINANCIAL_STATUSES_SORTED = sorted(list({
            "pending", "authorized", "paid", "partially_paid", "refunded",
            "voided", "partially_refunded", "any", "unpaid"
        }))
        expected_msg = (
            f"Invalid financial_status: 'non_existent_status'. "
            f"Allowed values are: {', '.join(VALID_FINANCIAL_STATUSES_SORTED)}."
        )
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.InvalidParameterError,
            expected_message=expected_msg,
            financial_status="non_existent_status"
        )

    def test_get_count_no_matching_orders_valid_filters(self):
        result = shopify_get_orders_count(created_at_min="2099-01-01T00:00:00Z", status="open")
        self.assertEqual(result, {"count": 0})

    def test_filter_by_created_at_min(self):
        result = shopify_get_orders_count(created_at_min="2023-02-01T00:00:00Z", status="any")
        self.assertEqual(result, {"count": 8})

    def test_filter_by_created_at_max(self):
        result = shopify_get_orders_count(created_at_max="2023-01-15T23:59:59Z")
        self.assertEqual(result, {"count": 2})

    def test_filter_by_created_at_range(self):
        result = shopify_get_orders_count(created_at_min="2023-01-01T00:00:00Z", created_at_max="2023-01-31T23:59:59Z")
        self.assertEqual(result, {"count": 1})

    def test_date_filter_exact_boundary_created_at_min(self):
        result = shopify_get_orders_count(created_at_min="2023-01-15T10:00:00Z", status="any")
        self.assertEqual(result, {"count": 10})

    def test_date_filter_exact_boundary_created_at_max(self):
        result = shopify_get_orders_count(created_at_max="2023-01-15T10:00:00Z")
        self.assertEqual(result, {"count": 2})

    def test_filter_created_at_min_greater_than_max(self):
        result = shopify_get_orders_count(created_at_min="2023-03-01T00:00:00Z", created_at_max="2023-02-01T00:00:00Z")
        self.assertEqual(result, {"count": 0})

    def test_filter_order_missing_created_at_with_date_filter(self):
        result = shopify_get_orders_count(created_at_min="2023-01-01T00:00:00Z", status="any")
        self.assertEqual(result, {"count": 10})

    def test_filter_by_updated_at_min(self):
        result = shopify_get_orders_count(updated_at_min="2023-03-01T00:00:00Z", status="any")
        self.assertEqual(result, {"count": 8})

    def test_filter_by_updated_at_max(self):
        result = shopify_get_orders_count(updated_at_max="2023-01-20T23:59:59Z")
        self.assertEqual(result, {"count": 1})

    def test_filter_by_updated_at_range(self):
        result = shopify_get_orders_count(updated_at_min="2023-01-16T00:00:00Z", updated_at_max="2023-02-11T13:00:00Z")
        self.assertEqual(result, {"count": 2})

    def test_date_filter_exact_boundary_updated_at_min(self):
        result = shopify_get_orders_count(updated_at_min="2023-01-16T11:00:00Z", status="any")
        self.assertEqual(result, {"count": 11})

    def test_date_filter_exact_boundary_updated_at_max(self):
        result = shopify_get_orders_count(updated_at_max="2023-01-16T11:00:00Z")
        self.assertEqual(result, {"count": 1})

    def test_filter_updated_at_min_greater_than_max(self):
        result = shopify_get_orders_count(updated_at_min="2023-03-01T00:00:00Z", updated_at_max="2023-02-01T00:00:00Z")
        self.assertEqual(result, {"count": 0})

    def test_filter_order_missing_updated_at_with_date_filter(self):
        result = shopify_get_orders_count(updated_at_min="2023-01-01T00:00:00Z", status="any")
        self.assertEqual(result, {"count": 11})

    def test_filter_by_financial_status_paid(self):
        result = shopify_get_orders_count(financial_status="paid", status="any")
        self.assertEqual(result, {"count": 5})

    def test_filter_by_financial_status_pending(self):
        result = shopify_get_orders_count(financial_status="pending")
        self.assertEqual(result, {"count": 1})

    def test_filter_by_financial_status_partially_paid(self):
        result = shopify_get_orders_count(financial_status="partially_paid")
        self.assertEqual(result, {"count": 1})

    def test_filter_by_financial_status_voided(self):
        result = shopify_get_orders_count(financial_status="voided")
        self.assertEqual(result, {"count": 1})

    def test_filter_by_financial_status_unpaid(self):
        result = shopify_get_orders_count(financial_status="unpaid")
        self.assertEqual(result, {"count": 1})

    def test_filter_by_financial_status_authorized(self):
        result = shopify_get_orders_count(financial_status="authorized")
        self.assertEqual(result, {"count": 1})
        
    def test_filter_by_financial_status_partially_refunded(self):
        result = shopify_get_orders_count(financial_status="partially_refunded", status="open")
        self.assertEqual(result, {"count": 1})

    def test_filter_by_financial_status_any(self):
        result = shopify_get_orders_count(financial_status="any", status="any")
        self.assertEqual(result, {"count": 12})

    def test_filter_by_fulfillment_status_shipped(self):
        result = shopify_get_orders_count(fulfillment_status="shipped")
        self.assertEqual(result, {"count": 1})

    def test_filter_by_fulfillment_status_unshipped(self):
        result = shopify_get_orders_count(fulfillment_status="unshipped")
        self.assertEqual(result, {"count": 7})

    def test_filter_by_fulfillment_status_partial(self):
        result = shopify_get_orders_count(fulfillment_status="partial")
        self.assertEqual(result, {"count": 1})

    def test_filter_by_fulfillment_status_null_in_db_with_unshipped_filter(self):
        DB['orders'] = {"10": self.sample_orders_dict["10"]}
        result = shopify_get_orders_count(fulfillment_status="unshipped")
        self.assertEqual(result, {"count": 0})
        DB['orders'] = copy.deepcopy(self.sample_orders_dict)

    def test_filter_by_fulfillment_status_null_in_db_with_any_filter(self):
        DB['orders'] = {"10": self.sample_orders_dict["10"]}
        result = shopify_get_orders_count(fulfillment_status="any")
        self.assertEqual(result, {"count": 1})
        DB['orders'] = copy.deepcopy(self.sample_orders_dict)

    def test_filter_by_fulfillment_status_any(self):
        result = shopify_get_orders_count(fulfillment_status="any", status="any")
        self.assertEqual(result, {"count": 12})

    def test_filter_by_status_open(self):
        result = shopify_get_orders_count(status="open")
        self.assertEqual(result, {"count": 10})

    def test_filter_by_status_closed(self):
        result = shopify_get_orders_count(status="closed")
        self.assertEqual(result, {"count": 2})

    def test_filter_by_status_any(self):
        result = shopify_get_orders_count(status="any")
        self.assertEqual(result, {"count": 12})

    def test_complex_filter_match_1(self):
        result = shopify_get_orders_count(
            created_at_min="2023-01-01T00:00:00Z",
            financial_status="paid",
            status="open",
            fulfillment_status="unshipped"
        )
        # Orders "1" and "12" match. Order "11" (missing created_at) is skipped by the date filter.
        self.assertEqual(result, {"count": 2})

    def test_complex_filter_match_2(self):
        result = shopify_get_orders_count(status="closed", financial_status="refunded")
        self.assertEqual(result, {"count": 1})

    def test_complex_filter_no_match(self):
        result = shopify_get_orders_count(
            created_at_min="2025-01-01T00:00:00Z",
            status="open"
        )
        self.assertEqual(result, {"count": 0})

    def test_invalid_date_format_created_at_min(self):
        expected_msg = "Invalid date format for created_at_min: 'invalid-date'. Expected ISO 8601 format (e.g., YYYY-MM-DDTHH:MM:SSZ)."
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.InvalidDateTimeFormatError,
            expected_message=expected_msg,
            created_at_min="invalid-date"
        )

    def test_invalid_date_format_created_at_max(self):
        expected_msg = "Invalid date format for created_at_max: 'invalid-date'. Expected ISO 8601 format (e.g., YYYY-MM-DDTHH:MM:SSZ)."
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.InvalidDateTimeFormatError,
            expected_message=expected_msg,
            created_at_max="invalid-date"
        )

    def test_invalid_date_format_updated_at_min(self):
        expected_msg = "Invalid date format for updated_at_min: 'invalid-date'. Expected ISO 8601 format (e.g., YYYY-MM-DDTHH:MM:SSZ)."
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.InvalidDateTimeFormatError,
            expected_message=expected_msg,
            updated_at_min="invalid-date"
        )

    def test_invalid_date_format_updated_at_max(self):
        expected_msg = "Invalid date format for updated_at_max: 'invalid-date'. Expected ISO 8601 format (e.g., YYYY-MM-DDTHH:MM:SSZ)."
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.InvalidDateTimeFormatError,
            expected_message=expected_msg,
            updated_at_max="invalid-date"
        )

    def test_invalid_date_type_created_at_min(self):
        expected_msg = "Invalid type for created_at_min: 'int'. Expected a string in ISO 8601 format or None."
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.InvalidParameterError,
            expected_message=expected_msg,
            created_at_min=12345
        )

    def test_invalid_financial_status_value(self):
        VALID_FINANCIAL_STATUSES_SORTED = sorted(list({
            "pending", "authorized", "paid", "partially_paid", "refunded",
            "voided", "partially_refunded", "any", "unpaid"
        }))
        expected_msg = (
            f"Invalid financial_status: 'unknown_status'. "
            f"Allowed values are: {', '.join(VALID_FINANCIAL_STATUSES_SORTED)}."
        )
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.InvalidParameterError,
            expected_message=expected_msg,
            financial_status="unknown_status"
        )

    def test_invalid_fulfillment_status_value(self):
        VALID_FULFILLMENT_STATUSES_SORTED = sorted(list({
            "shipped", "partial", "unshipped", "any", "fulfilled"
        }))
        expected_msg = (
            f"Invalid fulfillment_status: 'unknown_status'. "
            f"Allowed values are: {', '.join(VALID_FULFILLMENT_STATUSES_SORTED)}."
        )
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.InvalidParameterError,
            expected_message=expected_msg,
            fulfillment_status="unknown_status"
        )

    def test_invalid_status_value(self):
        VALID_ORDER_STATUSES_SORTED = sorted(list({"open", "closed", "any", "cancelled"}))
        expected_msg = (
            f"Invalid status: 'unknown_status'. "
            f"Allowed values are: {', '.join(VALID_ORDER_STATUSES_SORTED)}."
        )
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.InvalidParameterError,
            expected_message=expected_msg,
            status="unknown_status"
        )

    def test_db_orders_key_missing(self):
        del DB['orders']
        expected_msg = "Order data source ('orders' key) not found in DB."
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.ShopifyApiError,
            expected_message=expected_msg
        )

    def test_db_orders_is_none(self):
        DB['orders'] = None
        expected_msg = "Order data source ('orders' key) not found in DB."
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.ShopifyApiError,
            expected_message=expected_msg
        )

    def test_db_orders_not_a_dictionary(self):
        DB['orders'] = [1, 2, 3]
        expected_msg = "Order data source ('orders') is malformed: expected a dictionary of orders, got list."
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.ShopifyApiError,
            expected_message=expected_msg
        )

    def test_db_order_record_not_a_dictionary(self):
        DB['orders'] = {"1": "not_a_dict"}
        expected_msg = "Malformed order entry at_iteration_index_0: expected a dictionary, got str."
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.ShopifyApiError,
            expected_message=expected_msg
        )
    
    def test_db_order_record_not_a_dictionary_with_id_fallback(self):
        DB['orders'] = {"key1" : "not_a_dict_string", "key2": self.sample_orders_dict["1"]}
        expected_msg = "Malformed order entry at_iteration_index_0: expected a dictionary, got str."
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.ShopifyApiError,
            expected_message=expected_msg
        )

    def test_db_order_record_malformed_created_at_date_string(self):
        DB['orders'] = {"1": {"id": "err_order_1", "created_at": "invalid-date-string", "status": "open"}}
        expected_msg = "Malformed date value 'invalid-date-string' for field 'created_at' in order 'err_order_1': not a valid ISO 8601 format."
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.ShopifyApiError,
            expected_message=expected_msg,
            created_at_min="2000-01-01T00:00:00Z"
        )

    def test_db_order_record_malformed_updated_at_date_string(self):
        DB['orders'] = {"1": {"id": "err_order_2", "updated_at": "invalid-date-string-2", "status": "open"}}
        expected_msg = "Malformed date value 'invalid-date-string-2' for field 'updated_at' in order 'err_order_2': not a valid ISO 8601 format."
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.ShopifyApiError,
            expected_message=expected_msg,
            updated_at_min="2000-01-01T00:00:00Z"
        )

    def test_db_order_record_created_at_not_string(self):
        DB['orders'] = {"1": {"id": "err_order_3", "created_at": 12345, "status": "open"}}
        expected_msg = "Malformed date field 'created_at' in order 'err_order_3': expected string, got int."
        self.assert_error_behavior(
            func_to_call=shopify_get_orders_count,
            expected_exception_type=custom_errors.ShopifyApiError,
            expected_message=expected_msg,
            created_at_min="2000-01-01T00:00:00Z"
        )

if __name__ == '__main__':
    unittest.main(verbosity=2)