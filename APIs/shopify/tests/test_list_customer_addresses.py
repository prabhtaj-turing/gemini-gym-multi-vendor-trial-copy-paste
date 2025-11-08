
import unittest
import copy
from datetime import datetime, timezone
from shopify.customers import list_customer_addresses
from shopify.SimulationEngine.db import DB
from shopify.SimulationEngine import custom_errors
from shopify.SimulationEngine.models import ShopifyCustomerModel, ShopifyAddressModel
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestListCustomerAddresses(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        dummy_timestamp_dt = datetime.now(timezone.utc)
        self.dummy_timestamp_str = dummy_timestamp_dt.isoformat()

        # --- Test Data Setup ---
        self.addr1_cust1 = ShopifyAddressModel(
            id="101", customer_id="cust_1", address1="123 Main St", city="Anytown", default=True,
            country="US", first_name="John", last_name="Doe", phone="555-1234", province="CA", zip="90210"
        ).model_dump(mode='json')
        self.addr2_cust1 = ShopifyAddressModel(
            id="102", customer_id="cust_1", address1="456 Oak Ave", city="Anytown", default=False,
            country="US", first_name="John", last_name="Doe", phone="555-5678", province="CA", zip="90211"
        ).model_dump(mode='json')
        self.addr3_cust1 = ShopifyAddressModel(
            id="200", customer_id="cust_1", address1="789 Pine Ln", city="Otherville", default=False,
            country="US", first_name="John", last_name="Doe", phone="555-9012", province="NY", zip="10001"
        ).model_dump(mode='json')
        self.addr4_cust1_lex_prefix = ShopifyAddressModel(
            id="addr_300", customer_id="cust_1", address1="Prefixed Rd", city="PrefixTown",
            country="CA", first_name="Johnny", last_name="Doer", phone="555-3000", province="ON", zip="M1M1M1"
        ).model_dump(mode='json')
        self.addr5_cust1_another_prefix = ShopifyAddressModel(
            id="az_test_50", customer_id="cust_1", address1="AZ Road", city="AZ City",
            country="US", first_name="Alpha", last_name="Zed", phone="555-0050", province="AZ", zip="85001"
        ).model_dump(mode='json')

        # Valid ShopifyCustomerModel instantiations
        self.customer1_with_addresses = ShopifyCustomerModel(
            id="cust_1", first_name="John", last_name="Doe", email="john.doe@example.com",
            created_at=self.dummy_timestamp_str, updated_at=self.dummy_timestamp_str,
            orders_count=2, state="enabled", total_spent="100.00",
            phone="555-1111", tags="vip, repeat", default_address=self.addr1_cust1,
            addresses=[self.addr2_cust1, self.addr1_cust1, self.addr4_cust1_lex_prefix, self.addr3_cust1, self.addr5_cust1_another_prefix]
        ).model_dump(mode='json')

        self.customer2_no_addresses = ShopifyCustomerModel(
            id="cust_2", first_name="Jane", last_name="Smith", email="jane.smith@example.com", 
            created_at=self.dummy_timestamp_str, updated_at=self.dummy_timestamp_str, 
            orders_count=0, state="disabled", total_spent="0.00", 
            phone=None, tags=None, default_address=None, addresses=[]
        ).model_dump(mode='json')

        self.customer3_null_addresses = ShopifyCustomerModel(
            id="cust_3", first_name="Peter", last_name="Jones", email="peter.jones@example.com", 
            created_at=self.dummy_timestamp_str, updated_at=self.dummy_timestamp_str, 
            orders_count=1, state="invited", total_spent="20.00", 
            phone=None, tags=None, default_address=None, addresses=None # Addresses can be None
        ).model_dump(mode='json')
        
        # Manually construct dictionaries for DB for intentionally malformed data
        self.customer4_malformed_dict = {
            "id": "cust_4", "first_name": "Alice", "last_name": "Wonder", "email": "alice.wonder@example.com",
            "created_at": self.dummy_timestamp_str, "updated_at": self.dummy_timestamp_str,
            "orders_count": 0, "state": "declined", "total_spent": "0.00",
            "phone": None, "tags": None, "default_address": None,
            "addresses": "not_a_list" # Intentionally malformed for testing list_customer_addresses robustness
        }
        
        self.address_no_id_cust5_dict = {"customer_id": "cust_5", "address1": "No ID St"}
        self.address_valid_cust5_dict = ShopifyAddressModel(id="valid_addr_501", customer_id="cust_5", address1="501 Valid Ave").model_dump(mode='json')
        
        self.customer5_mixed_dict = {
            "id": "cust_5", "first_name": "Mixed", "last_name": "List", "email": "mixed.list@example.com",
            "created_at": self.dummy_timestamp_str, "updated_at": self.dummy_timestamp_str,
            "orders_count": 0, "state": "enabled", "total_spent": "0.00",
            "phone": None, "tags": None, "default_address": None,
            "addresses": [
                self.address_no_id_cust5_dict, 
                self.address_valid_cust5_dict,
                None, 
                "not_a_dict_address" 
            ]
        }

        DB['customers'] = {
            "cust_1": self.customer1_with_addresses,
            "cust_2": self.customer2_no_addresses,
            "cust_3": self.customer3_null_addresses,
            "cust_4": self.customer4_malformed_dict,
            "cust_5": self.customer5_mixed_dict
        }
        
        self.sorted_cust1_addrs = sorted(
            [self.addr1_cust1, self.addr2_cust1, self.addr3_cust1, self.addr4_cust1_lex_prefix, self.addr5_cust1_another_prefix],
            key=lambda addr: str(addr.get('id'))
        )

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_address_lists_match(self, result_addrs, expected_addrs):
        self.assertEqual(len(result_addrs), len(expected_addrs),
                         f"Expected {len(expected_addrs)} addresses, got {len(result_addrs)}."
                         f"\nResult IDs: {[a.get('id') for a in result_addrs]}"
                         f"\nExpected IDs: {[a.get('id') for a in expected_addrs]}")
        
        result_addrs_sorted = sorted(result_addrs, key=lambda x: str(x.get('id', '')))
        expected_addrs_sorted = sorted(expected_addrs, key=lambda x: str(x.get('id', '')))

        for i, res_addr in enumerate(result_addrs_sorted):
            exp_addr = expected_addrs_sorted[i]
            self.assertDictEqual(res_addr, exp_addr, 
                                 f"Dict mismatch for address ID {res_addr.get('id')} at sorted index {i}")

    def test_list_addresses_basic_retrieval(self):
        response = list_customer_addresses(customer_id="cust_1")
        self.assertIn('addresses', response)
        self._assert_address_lists_match(response['addresses'], self.sorted_cust1_addrs)
        
        if response['addresses']:
            original_address_in_response = response['addresses'][0]
            original_city_value = str(original_address_in_response.get('city')) 
            response['addresses'][0]['city'] = "MODIFIED_CITY_TEST"
            
            # Check against the initial model dump, not the DB state which might be complex to re-parse here
            original_model_dump_list = self.customer1_with_addresses.get('addresses', [])            
            original_db_address_dict = None
            for addr_in_db_model_dump in original_model_dump_list:
                if addr_in_db_model_dump.get('id') == original_address_in_response.get('id'):
                    original_db_address_dict = addr_in_db_model_dump
                    break
            
            self.assertIsNotNone(original_db_address_dict, "Original address for deep copy check not found in initial data.")
            self.assertEqual(str(original_db_address_dict.get('city')), original_city_value, 
                             "Deep copy failed; modification of response affected source data representation.")

    def test_list_addresses_with_limit(self):
        response = list_customer_addresses(customer_id="cust_1", limit=2)
        self.assertIn('addresses', response)
        self.assertEqual(len(response['addresses']), 2)
        self._assert_address_lists_match(response['addresses'], self.sorted_cust1_addrs[:2])

    def test_list_addresses_pagination_with_since_id(self):
        response = list_customer_addresses(customer_id="cust_1", since_id=101)
        expected_after_101 = [addr for addr in self.sorted_cust1_addrs if str(addr['id']) > "101"]
        self._assert_address_lists_match(response['addresses'], expected_after_101)

        response_since_200 = list_customer_addresses(customer_id="cust_1", since_id=200)
        expected_after_200 = [addr for addr in self.sorted_cust1_addrs if str(addr['id']) > "200"]
        self._assert_address_lists_match(response_since_200['addresses'], expected_after_200)

        response_since_int_300 = list_customer_addresses(customer_id="cust_1", since_id=300)
        expected_after_300_str = [addr for addr in self.sorted_cust1_addrs if str(addr['id']) > "300"]
        self._assert_address_lists_match(response_since_int_300['addresses'], expected_after_300_str)

        response_since_high_numeric = list_customer_addresses(customer_id="cust_1", since_id=999999)
        expected_after_999999 = [addr for addr in self.sorted_cust1_addrs if str(addr.get('id', '')) > "999999"]
        self._assert_address_lists_match(response_since_high_numeric['addresses'], expected_after_999999)

    def test_list_addresses_since_id_0_or_none_or_default(self):
        response_since_0 = list_customer_addresses(customer_id="cust_1", since_id=0)
        self._assert_address_lists_match(response_since_0['addresses'], self.sorted_cust1_addrs)

        response_since_none = list_customer_addresses(customer_id="cust_1", since_id=None)
        self._assert_address_lists_match(response_since_none['addresses'], self.sorted_cust1_addrs)
        
        response_default_since = list_customer_addresses(customer_id="cust_1") 
        self._assert_address_lists_match(response_default_since['addresses'], self.sorted_cust1_addrs)

    def test_list_addresses_customer_no_addresses(self):
        response = list_customer_addresses(customer_id="cust_2")
        self.assertIn('addresses', response)
        self.assertEqual(len(response['addresses']), 0)

    def test_list_addresses_customer_null_addresses_field(self):
        response = list_customer_addresses(customer_id="cust_3")
        self.assertIn('addresses', response)
        self.assertEqual(len(response['addresses']), 0)
        
    def test_list_addresses_customer_malformed_addresses_field_not_list(self):
        # This customer (cust_4) in DB has its 'addresses' field as a string "not_a_list"
        response = list_customer_addresses(customer_id="cust_4")
        self.assertIn('addresses', response)
        self.assertEqual(len(response['addresses']), 0)
        
    def test_list_addresses_customer_mixed_validity_addresses(self):
        # This customer (cust_5) in DB has a mixed list for 'addresses'
        response = list_customer_addresses(customer_id="cust_5")
        self.assertIn('addresses', response)
        self.assertEqual(len(response['addresses']), 1, "Should only return the one valid address with an ID.")
        if response['addresses']:
            self.assertEqual(response['addresses'][0]['id'], self.address_valid_cust5_dict['id'])
            self._assert_address_lists_match(response['addresses'], [self.address_valid_cust5_dict])
        else:
            self.fail("Expected one address for cust_5 but got none in response list for full match assertion.")

    def test_error_customer_not_found(self):
        self.assert_error_behavior(list_customer_addresses, custom_errors.NoResultsFoundError, 
                                   "Customer with ID 'non_existent_cust' not found.", customer_id="non_existent_cust")

    def test_error_invalid_customer_id_type(self):
        self.assert_error_behavior(list_customer_addresses, custom_errors.InvalidInputError, 
                                   "customer_id must be a non-empty string.", customer_id=123)

    def test_error_empty_customer_id(self):
        self.assert_error_behavior(list_customer_addresses, custom_errors.InvalidInputError, 
                                   "customer_id must be a non-empty string.", customer_id="")
        self.assert_error_behavior(list_customer_addresses, custom_errors.InvalidInputError, 
                                   "customer_id must be a non-empty string.", customer_id="   ")

    def test_error_invalid_limit_type(self):
        self.assert_error_behavior(list_customer_addresses, custom_errors.InvalidInputError, 
                                   "limit must be an integer between 1 and 250.", customer_id="cust_1", limit="abc")

    def test_error_invalid_limit_too_low(self):
        self.assert_error_behavior(list_customer_addresses, custom_errors.InvalidInputError, 
                                   "limit must be an integer between 1 and 250.", customer_id="cust_1", limit=0)

    def test_error_invalid_limit_too_high(self):
        self.assert_error_behavior(list_customer_addresses, custom_errors.InvalidInputError, 
                                   "limit must be an integer between 1 and 250.", customer_id="cust_1", limit=251)

    def test_error_invalid_since_id_type(self):
        self.assert_error_behavior(list_customer_addresses, custom_errors.InvalidInputError, 
                                   "since_id must be a non-negative integer or None.", customer_id="cust_1", since_id="abc")

    def test_error_invalid_since_id_negative(self):
        self.assert_error_behavior(list_customer_addresses, custom_errors.InvalidInputError, 
                                   "since_id must be a non-negative integer or None.", customer_id="cust_1", since_id=-1)

if __name__ == '__main__':
    unittest.main()