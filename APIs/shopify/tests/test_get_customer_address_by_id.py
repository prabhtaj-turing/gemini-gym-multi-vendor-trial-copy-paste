
import unittest
import copy
from datetime import datetime, timezone
from shopify.customers import get_customer_address_by_id
from shopify.SimulationEngine.db import DB
from shopify.SimulationEngine import custom_errors
from shopify.SimulationEngine.models import ShopifyCustomerModel, ShopifyAddressModel
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestGetCustomerAddressById(BaseTestCaseWithErrorHandler):
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
            id="addr_102", customer_id="cust_1", address1="456 Oak Ave", city="Anytown", default=False, # Alphanumeric ID
            country="US", first_name="John", last_name="Doe", phone="555-5678", province="CA", zip="90211"
        ).model_dump(mode='json')

        self.customer1_with_addresses = ShopifyCustomerModel(
            id="cust_1", first_name="John", last_name="Doe", email="john.doe@example.com",
            created_at=self.dummy_timestamp_str, updated_at=self.dummy_timestamp_str,
            orders_count=2, state="enabled", total_spent="100.00",
            phone="555-1111", tags="vip, repeat", default_address=self.addr1_cust1,
            addresses=[self.addr1_cust1, self.addr2_cust1]
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
            phone=None, tags=None, default_address=None, addresses=None
        ).model_dump(mode='json')

        self.customer4_malformed_addresses_field_dict = {
            "id": "cust_4", "first_name": "Alice", "last_name": "Wonder", "email": "alice.wonder@example.com",
            "created_at": self.dummy_timestamp_str, "updated_at": self.dummy_timestamp_str,
            "orders_count": 0, "state": "declined", "total_spent": "0.00",
            "phone": None, "tags": None, "default_address": None,
            "addresses": "not_a_list"
        }
        
        self.address_no_id_cust5_dict = {"customer_id": "cust_5", "address1": "No ID St"}
        self.address_valid_cust5_dict = ShopifyAddressModel(id="valid_addr_501", customer_id="cust_5", address1="501 Valid Ave").model_dump(mode='json')
        self.customer5_mixed_dict = {
            "id": "cust_5", "first_name": "Mixed", "last_name": "List", "email": "mixed.list@example.com",
            "created_at": self.dummy_timestamp_str, "updated_at": self.dummy_timestamp_str,
            "orders_count": 0, "state": "enabled", "total_spent": "0.00",
            "phone": None, "tags": None, "default_address": None,
            "addresses": [self.address_no_id_cust5_dict, self.address_valid_cust5_dict, None, "not_a_dict_address"]
        }

        DB['customers'] = {
            "cust_1": self.customer1_with_addresses,
            "cust_2": self.customer2_no_addresses,
            "cust_3": self.customer3_null_addresses,
            "cust_4": self.customer4_malformed_addresses_field_dict,
            "cust_5": self.customer5_mixed_dict
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_get_address_successfully(self):
        response = get_customer_address_by_id(customer_id="cust_1", address_id="101")
        self.assertIn('customer_address', response)
        self.assertDictEqual(response['customer_address'], self.addr1_cust1)

    def test_get_address_alphanumeric_id_successfully(self):
        response = get_customer_address_by_id(customer_id="cust_1", address_id="addr_102")
        self.assertIn('customer_address', response)
        self.assertDictEqual(response['customer_address'], self.addr2_cust1)
        
    def test_get_address_id_type_consistency(self):
        # Address ID in DB is "101" (string), try fetching with int 101 stringified
        response_int_str_id = get_customer_address_by_id(customer_id="cust_1", address_id="101") # address_id is string "101"
        self.assertDictEqual(response_int_str_id['customer_address'], self.addr1_cust1)

    def test_get_address_is_deep_copy(self):
        response = get_customer_address_by_id(customer_id="cust_1", address_id="101")
        retrieved_address = response['customer_address']
        original_city = str(retrieved_address.get('city'))
        
        retrieved_address['city'] = "MODIFIED_IN_RESPONSE"
        
        original_db_address = None
        # Access the original data from the setup, not from DB directly in test logic
        customer_data_in_setup = self.customer1_with_addresses
        for addr in customer_data_in_setup['addresses']:
            if addr.get('id') == "101":
                original_db_address = addr
                break
        self.assertIsNotNone(original_db_address)
        self.assertEqual(original_db_address.get('city'), original_city)
        self.assertNotEqual(original_db_address.get('city'), "MODIFIED_IN_RESPONSE")

    def test_error_customer_not_found(self):
        self.assert_error_behavior(
            get_customer_address_by_id, 
            custom_errors.NoResultsFoundError, 
            "Customer with ID 'non_existent_cust' not found.", 
            customer_id="non_existent_cust", address_id="101"
        )

    def test_error_address_not_found_for_customer(self):
        self.assert_error_behavior(
            get_customer_address_by_id, 
            custom_errors.NoResultsFoundError, 
            "Address with ID 'non_existent_addr' not found for customer 'cust_1'.", 
            customer_id="cust_1", address_id="non_existent_addr"
        )

    def test_error_address_not_found_customer_has_no_addresses(self):
        self.assert_error_behavior(
            get_customer_address_by_id, 
            custom_errors.NoResultsFoundError, 
            "Address with ID '101' not found for customer 'cust_2'.", 
            customer_id="cust_2", address_id="101"
        )

    def test_error_address_not_found_customer_addresses_is_null(self):
        self.assert_error_behavior(
            get_customer_address_by_id, 
            custom_errors.NoResultsFoundError, 
            "Address with ID '101' not found for customer 'cust_3'.", 
            customer_id="cust_3", address_id="101"
        )

    def test_error_address_not_found_customer_addresses_not_a_list(self):
        self.assert_error_behavior(
            get_customer_address_by_id, 
            custom_errors.NoResultsFoundError, 
            "Address with ID '101' not found for customer 'cust_4'.", 
            customer_id="cust_4", address_id="101"
        )

    def test_error_address_not_found_in_mixed_validity_list(self):
        # cust_5 has addresses = [dict_no_id, valid_dict_with_id, None, string_item]
        self.assert_error_behavior(
            get_customer_address_by_id, 
            custom_errors.NoResultsFoundError, 
            "Address with ID 'addr_id_not_present' not found for customer 'cust_5'.", 
            customer_id="cust_5", address_id="addr_id_not_present"
        )
        # Check that the valid one CAN be found
        response = get_customer_address_by_id(customer_id="cust_5", address_id="valid_addr_501")
        self.assertDictEqual(response['customer_address'], self.address_valid_cust5_dict)

    # Input Validation Error Tests
    def test_error_invalid_customer_id_type(self):
        self.assert_error_behavior(get_customer_address_by_id, custom_errors.InvalidInputError, 
                                   "customer_id must be a non-empty string.", customer_id=123, address_id="101")

    def test_error_empty_customer_id(self):
        self.assert_error_behavior(get_customer_address_by_id, custom_errors.InvalidInputError, 
                                   "customer_id must be a non-empty string.", customer_id="", address_id="101")
        self.assert_error_behavior(get_customer_address_by_id, custom_errors.InvalidInputError, 
                                   "customer_id must be a non-empty string.", customer_id="   ", address_id="101")

    def test_error_invalid_address_id_type(self):
        self.assert_error_behavior(get_customer_address_by_id, custom_errors.InvalidInputError, 
                                   "address_id must be a non-empty string.", customer_id="cust_1", address_id=101)

    def test_error_empty_address_id(self):
        self.assert_error_behavior(get_customer_address_by_id, custom_errors.InvalidInputError, 
                                   "address_id must be a non-empty string.", customer_id="cust_1", address_id="")
        self.assert_error_behavior(get_customer_address_by_id, custom_errors.InvalidInputError, 
                                   "address_id must be a non-empty string.", customer_id="cust_1", address_id="   ")

if __name__ == '__main__':
    unittest.main()