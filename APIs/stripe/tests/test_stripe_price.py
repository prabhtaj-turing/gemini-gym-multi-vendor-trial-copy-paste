# Import section
from common_utils.base_case import BaseTestCaseWithErrorHandler
import unittest
from datetime import datetime, timezone
from ..SimulationEngine.custom_errors import InvalidRequestError, ResourceNotFoundError
from ..SimulationEngine.models import _SUPPORTED_CURRENCIES_FOR_MODEL
from ..SimulationEngine.db import DB
from typing import Optional
from .. import create_price, list_prices


def get_current_timestamp_for_test() -> int:
    return int(datetime.now(timezone.utc).timestamp())

class TestCreatePrice(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Set up test environment for each test."""
        self.DB = DB
        if "products" not in self.DB:
            self.DB["products"] = {}
        else:
            self.DB["products"].clear()

        if "prices" not in self.DB:
            self.DB["prices"] = {}
        else:
            self.DB["prices"].clear()

        self.product_id_existing = "prod_existing123"
        self.DB["products"][self.product_id_existing] = {
            "id": self.product_id_existing,
            "object": "product",
            "name": "Test Product",
            # other product fields as needed by tests, if any
        }

    def tearDown(self):
        """Clean up after each test."""
        self.DB["products"].clear()
        self.DB["prices"].clear()

    def test_create_price_successful_one_time(self):
        """Test successful creation of a one-time price."""
        product_id = self.product_id_existing
        unit_amount = 1000
        currency = "usd"

        num_prices_before = len(self.DB["prices"])
        start_time = get_current_timestamp_for_test() -1 # ensure created is >= start_time

        result = create_price(product=product_id, unit_amount=unit_amount, currency=currency)

        self.assertIsInstance(result, dict)
        self.assertEqual(len(self.DB["prices"]), num_prices_before + 1)

        self.assertIn("id", result)
        price_id = result["id"]
        self.assertIsInstance(price_id, str)
        self.assertTrue(price_id.startswith("price_"), "Price ID should start with 'price_'")
        self.assertEqual(result.get("object"), "price")
        self.assertEqual(result.get("livemode"), False) # Default from Price model

        # 'created' is not in the explicit return dict of create_price as per its docstring
        self.assertNotIn("created", result, "'created' should not be in the returned dict unless specified")

        self.assertEqual(result.get("product"), product_id)
        self.assertEqual(result.get("unit_amount"), unit_amount)
        self.assertEqual(result.get("currency"), currency) # Already normalized by model if input was mixed case
        self.assertEqual(result.get("active"), True)    # Default from Price model
        self.assertEqual(result.get("type"), "one_time") # Default from Price model
        self.assertIsNone(result.get("recurring"))     # Default from Price model
        self.assertIsNone(result.get("metadata"))      # Default from Price model

        self.assertIn(price_id, self.DB["prices"])
        stored_price = self.DB["prices"][price_id]
        self.assertIsInstance(stored_price, dict)

        # Verify key fields in the stored self.DB object
        self.assertEqual(stored_price["id"], price_id)
        self.assertEqual(stored_price["product"], product_id)
        self.assertEqual(stored_price["unit_amount"], unit_amount)
        self.assertEqual(stored_price["currency"], currency)
        self.assertEqual(stored_price["active"], True)
        self.assertEqual(stored_price["type"], "one_time")
        self.assertIsNone(stored_price["recurring"])
        self.assertEqual(stored_price["livemode"], False)
        self.assertIsNone(stored_price["metadata"])

        # Check 'created' in the stored object (it's part of the Price model)
        self.assertIn("created", stored_price)
        self.assertIsInstance(stored_price["created"], int)
        self.assertGreaterEqual(stored_price["created"], start_time)


    def test_create_price_successful_currency_normalization(self):
        """Test successful creation with mixed-case currency, expecting normalization."""
        product_id = self.product_id_existing
        unit_amount = 2000
        currency_input = "USD"
        expected_currency_stored = "usd"

        result = create_price(product=product_id, unit_amount=unit_amount, currency=currency_input)

        self.assertEqual(result.get("currency"), expected_currency_stored)
        price_id = result["id"]
        self.assertIn(price_id, self.DB["prices"])
        self.assertEqual(self.DB["prices"][price_id]["currency"], expected_currency_stored)

    def test_create_price_successful_other_supported_currency(self):
        """Test successful creation with another supported currency (eur)."""
        product_id = self.product_id_existing
        unit_amount = 1500
        currency = "eur" # 'eur' is in _SUPPORTED_CURRENCIES_FOR_MODEL

        result = create_price(product=product_id, unit_amount=unit_amount, currency=currency)
        self.assertEqual(result.get("currency"), currency)
        price_id = result["id"]
        self.assertIn(price_id, self.DB["prices"])
        self.assertEqual(self.DB["prices"][price_id]["currency"], currency)

    def test_create_price_successful_unit_amount_zero(self):
        """Test successful creation of a price with unit_amount as zero."""
        product_id = self.product_id_existing
        unit_amount = 0 # Zero is a valid non-negative amount
        currency = "usd"

        result = create_price(product=product_id, unit_amount=unit_amount, currency=currency)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("unit_amount"), unit_amount)
        price_id = result["id"]
        self.assertIn(price_id, self.DB["prices"])
        self.assertEqual(self.DB["prices"][price_id]["unit_amount"], unit_amount)


    # --- InvalidRequestError Tests ---

    def test_create_price_invalid_request_product_id_empty(self):
        """Test create_price with an empty product ID."""
        expected_msg = "Input validation failed: Error in field 'product': Product ID must be a non empty string."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product="", unit_amount=1000, currency="usd"
        )

    def test_create_price_invalid_request_product_id_malformed(self):
        """Test create_price with a malformed product ID (does not start with prod_)."""
        malformed_id = "invalid_prod_id"
        expected_msg = "Product with ID 'invalid_prod_id' not found. A product must be created before a price can be added to it."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=ResourceNotFoundError,
            expected_message=expected_msg,
            product=malformed_id, unit_amount=1000, currency="usd"
        )

    def test_create_price_invalid_request_unit_amount_negative(self):
        """Test create_price with negative unit_amount."""
        expected_msg = "Input validation failed: Error in field 'unit_amount': Unit amount must be a non negative integer."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount=-500, currency="usd"
        )

    def test_create_price_invalid_request_currency_empty(self):
        """Test create_price with an empty currency string."""
        currency_val = ""
        expected_msg = "Input validation failed: Error in field 'currency': Currency must be a non empty string."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount=1000, currency=currency_val
        )

    def test_create_price_invalid_request_currency_invalid_format_short(self):
        currency_val = "us"
        expected_msg = f"Input validation failed: Error in field 'currency': Currency '{currency_val}' must be a 3-letter ISO code (e.g., usd, eur)."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount=1000, currency=currency_val
        )

    def test_create_price_invalid_request_currency_invalid_format_long(self):
        currency_val = "usdollar"
        # The Pydantic validator uses the original 'v' for the message part before normalization
        expected_msg = f"Input validation failed: Error in field 'currency': Currency '{currency_val}' must be a 3-letter ISO code (e.g., usd, eur)."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount=1000, currency=currency_val
        )

    def test_create_price_invalid_request_currency_invalid_format_numbers(self):
        currency_val = "123"
        expected_msg = f"Input validation failed: Error in field 'currency': Currency '{currency_val}' must be a 3-letter ISO code (e.g., usd, eur)."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount=1000, currency=currency_val
        )

    def test_create_price_invalid_request_currency_unsupported(self):
        currency_val = "xyz"
        # Ensure this constant is available and matches the one used by the Price model validator
        Supported_currencies = ", ".join(sorted(list(_SUPPORTED_CURRENCIES_FOR_MODEL)))
        expected_msg = f"Input validation failed: Error in field 'currency': Unsupported currency: '{currency_val}'. Supported currencies are: {Supported_currencies}."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount=1000, currency=currency_val
        )

    # --- ResourceNotFoundError Tests ---
    def test_create_price_resource_not_found_product_id_nonexistent(self):
        """Test create_price with a product ID that does not exist."""
        non_existent_product_id = "prod_nonexistent123"
        expected_msg = f"Product with ID '{non_existent_product_id}' not found. A product must be created before a price can be added to it."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=ResourceNotFoundError,
            expected_message=expected_msg,
            product=non_existent_product_id, unit_amount=1000, currency="usd"
        )

    # --- Type Error like scenarios for None inputs (handled by Pydantic) ---
    def test_create_price_invalid_request_product_id_none(self):
        """Test create_price with product ID as None."""
        expected_msg = "Input validation failed: Error in field 'product': Product ID must be a non empty string."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=None, unit_amount=1000, currency="usd"
        )

    def test_create_price_invalid_request_unit_amount_none(self):
        """Test create_price with unit_amount as None."""
        expected_msg = "Input validation failed: Error in field 'unit_amount': Input should be a valid integer"
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount=None, currency="usd"
        )

    def test_create_price_invalid_request_currency_none(self):
        """Test create_price with currency as None."""
        expected_msg = "Input validation failed: Error in field 'currency': Currency must be a non empty string."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount=1000, currency=None
        )

    # --- Test DB state consistency on failure ---
    def test_create_price_does_not_add_to_db_on_failure_invalid_request(self):
        """Test that no price is added to DB if InvalidRequestError is raised."""
        num_prices_before = len(self.DB["prices"])
        # Using a known invalid input (unit_amount negative)
        with self.assertRaises(InvalidRequestError): # Catch the specific exception
            create_price(product=self.product_id_existing, unit_amount=-100, currency="usd")
        self.assertEqual(len(self.DB["prices"]), num_prices_before, "DB prices count should not change on InvalidRequestError.")

    def test_create_price_does_not_add_to_db_on_failure_resource_not_found(self):
        """Test that no price is added to DB if ResourceNotFoundError is raised."""
        num_prices_before = len(self.DB["prices"])
        with self.assertRaises(ResourceNotFoundError): # Catch the specific exception
            create_price(product="prod_nonexistentXYZ", unit_amount=1000, currency="usd")
        self.assertEqual(len(self.DB["prices"]), num_prices_before, "DB prices count should not change on ResourceNotFoundError.")

    def test_create_price_invalid_request_unit_amount_float(self):
        """Test create_price with unit_amount as float instead of int."""
        expected_msg = "Input validation failed: Error in field 'unit_amount': Unit amount must be a non negative integer."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount=100.5, currency="usd"
        )

    def test_create_price_invalid_request_unit_amount_string(self):
        """Test create_price with unit_amount as string instead of int."""
        expected_msg = "Input validation failed: Error in field 'unit_amount': Unit amount must be a non negative integer."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount="1000", currency="usd"
        )

    def test_create_price_invalid_request_product_id_whitespace_only(self):
        """Test create_price with product ID containing only whitespace."""
        expected_msg = "Input validation failed: Error in field 'product': Product ID must be a non empty string."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product="   ", unit_amount=1000, currency="usd"
        )

    def test_create_price_invalid_request_currency_whitespace_only(self):
        """Test create_price with currency containing only whitespace."""
        expected_msg = "Input validation failed: Error in field 'currency': Currency must be a non empty string."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount=1000, currency="   "
        )

    def test_create_price_invalid_request_currency_mixed_case_unsupported(self):
        """Test create_price with mixed case unsupported currency."""
        currency_val = "XYZ"
        Supported_currencies = ", ".join(sorted(list(_SUPPORTED_CURRENCIES_FOR_MODEL)))
        expected_msg = f"Input validation failed: Error in field 'currency': Unsupported currency: '{currency_val}'. Supported currencies are: {Supported_currencies}."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount=1000, currency=currency_val
        )

    def test_create_price_invalid_request_currency_with_numbers(self):
        """Test create_price with currency containing numbers."""
        currency_val = "us1"
        expected_msg = f"Input validation failed: Error in field 'currency': Currency '{currency_val}' must be a 3-letter ISO code (e.g., usd, eur)."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount=1000, currency=currency_val
        )

    def test_create_price_invalid_request_currency_with_special_chars(self):
        """Test create_price with currency containing special characters."""
        currency_val = "us$"
        expected_msg = f"Input validation failed: Error in field 'currency': Currency '{currency_val}' must be a 3-letter ISO code (e.g., usd, eur)."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount=1000, currency=currency_val
        )

    def test_create_price_invalid_request_product_id_int(self):
        """Test create_price with product ID as integer instead of string."""
        expected_msg = "Input validation failed: Error in field 'product': Product ID must be a non empty string."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=123, unit_amount=1000, currency="usd"
        )

    def test_create_price_invalid_request_currency_int(self):
        """Test create_price with currency as integer instead of string."""
        expected_msg = "Input validation failed: Error in field 'currency': Currency must be a non empty string."
        self.assert_error_behavior(
            func_to_call=create_price,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=self.product_id_existing, unit_amount=1000, currency=123
        )

    def test_create_price_successful_all_supported_currencies(self):
        """Test successful creation with all supported currencies."""
        supported_currencies = list(_SUPPORTED_CURRENCIES_FOR_MODEL)
        unit_amount = 1000
        
        for currency in supported_currencies:
            with self.subTest(currency=currency):
                result = create_price(
                    product=self.product_id_existing, 
                    unit_amount=unit_amount, 
                    currency=currency
                )
                self.assertEqual(result.get("currency"), currency)
                self.assertEqual(result.get("unit_amount"), unit_amount)
                self.assertEqual(result.get("product"), self.product_id_existing)

    def test_create_price_successful_large_unit_amount(self):
        """Test successful creation with a large unit amount."""
        product_id = self.product_id_existing
        unit_amount = 999999999  # Large amount
        currency = "usd"

        result = create_price(product=product_id, unit_amount=unit_amount, currency=currency)
        self.assertEqual(result.get("unit_amount"), unit_amount)
        self.assertEqual(result.get("currency"), currency)
        self.assertEqual(result.get("product"), product_id)

    def test_create_price_successful_product_id_with_underscores(self):
        """Test successful creation with product ID containing underscores."""
        product_id = "prod_test_product_123"
        self.DB["products"][product_id] = {
            "id": product_id,
            "object": "product",
            "name": "Test Product with Underscores",
        }
        
        unit_amount = 1000
        currency = "usd"

        result = create_price(product=product_id, unit_amount=unit_amount, currency=currency)
        self.assertEqual(result.get("product"), product_id)
        self.assertEqual(result.get("unit_amount"), unit_amount)
        self.assertEqual(result.get("currency"), currency)

    def test_create_price_successful_product_id_with_numbers(self):
        """Test successful creation with product ID containing numbers."""
        product_id = "prod_test123"
        self.DB["products"][product_id] = {
            "id": product_id,
            "object": "product",
            "name": "Test Product with Numbers",
        }
        
        unit_amount = 1000
        currency = "usd"

        result = create_price(product=product_id, unit_amount=unit_amount, currency=currency)
        self.assertEqual(result.get("product"), product_id)
        self.assertEqual(result.get("unit_amount"), unit_amount)
        self.assertEqual(result.get("currency"), currency)

    def test_create_price_successful_currency_with_whitespace(self):
        """Test successful creation with currency containing leading/trailing whitespace."""
        product_id = self.product_id_existing
        unit_amount = 1000
        currency_input = "  usd  "
        expected_currency = "usd"

        result = create_price(product=product_id, unit_amount=unit_amount, currency=currency_input)
        self.assertEqual(result.get("currency"), expected_currency)
        price_id = result["id"]
        self.assertEqual(self.DB["prices"][price_id]["currency"], expected_currency)

    def test_create_price_successful_product_id_with_whitespace(self):
        """Test successful creation with product ID containing leading/trailing whitespace."""
        product_id = "  prod_existing123  "
        # The function should handle whitespace in product ID
        self.DB["products"][product_id.strip()] = {
            "id": product_id.strip(),
            "object": "product",
            "name": "Test Product",
        }
        
        unit_amount = 1000
        currency = "usd"

        result = create_price(product=product_id, unit_amount=unit_amount, currency=currency)
        self.assertEqual(result.get("product"), product_id.strip())
        self.assertEqual(result.get("unit_amount"), unit_amount)
        self.assertEqual(result.get("currency"), currency)

    def test_create_price_multiple_prices_same_product(self):
        """Test creating multiple prices for the same product."""
        product_id = self.product_id_existing
        prices_data = [
            {"unit_amount": 1000, "currency": "usd"},
            {"unit_amount": 2000, "currency": "eur"},
            {"unit_amount": 0, "currency": "gbp"},
        ]
        
        created_prices = []
        for price_data in prices_data:
            result = create_price(
                product=product_id,
                unit_amount=price_data["unit_amount"],
                currency=price_data["currency"]
            )
            created_prices.append(result)
        
        # Verify all prices were created
        self.assertEqual(len(created_prices), 3)
        self.assertEqual(len(self.DB["prices"]), 3)
        
        # Verify each price has unique ID
        price_ids = [price["id"] for price in created_prices]
        self.assertEqual(len(set(price_ids)), 3)
        
        # Verify all prices belong to the same product
        for price in created_prices:
            self.assertEqual(price["product"], product_id)

    def test_create_price_verify_return_structure(self):
        """Test that the returned price has the correct structure and all expected fields."""
        product_id = self.product_id_existing
        unit_amount = 1000
        currency = "usd"

        result = create_price(product=product_id, unit_amount=unit_amount, currency=currency)
        
        # Verify all expected fields are present
        expected_fields = [
            "id", "object", "active", "product", "unit_amount", 
            "currency", "type", "recurring", "livemode", "metadata"
        ]
        
        for field in expected_fields:
            self.assertIn(field, result, f"Field '{field}' should be present in the result")
        
        # Verify field types
        self.assertIsInstance(result["id"], str)
        self.assertIsInstance(result["object"], str)
        self.assertIsInstance(result["active"], bool)
        self.assertIsInstance(result["product"], str)
        self.assertIsInstance(result["unit_amount"], int)
        self.assertIsInstance(result["currency"], str)
        self.assertIsInstance(result["type"], str)
        self.assertIsInstance(result["livemode"], bool)
        
        # Verify field values
        self.assertEqual(result["object"], "price")
        self.assertEqual(result["active"], True)
        self.assertEqual(result["product"], product_id)
        self.assertEqual(result["unit_amount"], unit_amount)
        self.assertEqual(result["currency"], currency)
        self.assertEqual(result["type"], "one_time")
        self.assertEqual(result["livemode"], False)
        self.assertIsNone(result["recurring"])
        self.assertIsNone(result["metadata"])

    def test_create_price_verify_db_storage_structure(self):
        """Test that the price is stored in DB with correct structure."""
        product_id = self.product_id_existing
        unit_amount = 1000
        currency = "usd"

        result = create_price(product=product_id, unit_amount=unit_amount, currency=currency)
        price_id = result["id"]
        
        # Verify price is stored in DB
        self.assertIn(price_id, self.DB["prices"])
        stored_price = self.DB["prices"][price_id]
        
        # Verify stored price has all expected fields
        expected_fields = [
            "id", "object", "active", "product", "unit_amount", 
            "currency", "type", "recurring", "livemode", "metadata",
            "billing_scheme", "created", "custom_unit_amount", "lookup_key",
            "nickname", "tax_behavior", "tiers", "tiers_mode", 
            "transform_quantity", "unit_amount_decimal"
        ]
        
        for field in expected_fields:
            self.assertIn(field, stored_price, f"Field '{field}' should be present in stored price")
        
        # Verify key field values match
        self.assertEqual(stored_price["id"], price_id)
        self.assertEqual(stored_price["product"], product_id)
        self.assertEqual(stored_price["unit_amount"], unit_amount)
        self.assertEqual(stored_price["currency"], currency)
        self.assertEqual(stored_price["active"], True)
        self.assertEqual(stored_price["type"], "one_time")
        self.assertEqual(stored_price["livemode"], False)
        self.assertIsInstance(stored_price["created"], int)

    def test_create_price_edge_case_max_int_unit_amount(self):
        """Test creation with maximum integer unit amount."""
        product_id = self.product_id_existing
        unit_amount = 2**31 - 1  # Max 32-bit signed integer
        currency = "usd"

        result = create_price(product=product_id, unit_amount=unit_amount, currency=currency)
        self.assertEqual(result.get("unit_amount"), unit_amount)
        self.assertEqual(result.get("currency"), currency)
        self.assertEqual(result.get("product"), product_id)

    def test_create_price_edge_case_very_long_product_id(self):
        """Test creation with a very long product ID."""
        product_id = "prod_" + "a" * 100  # Very long product ID
        self.DB["products"][product_id] = {
            "id": product_id,
            "object": "product",
            "name": "Test Product with Very Long ID",
        }
        
        unit_amount = 1000
        currency = "usd"

        result = create_price(product=product_id, unit_amount=unit_amount, currency=currency)
        self.assertEqual(result.get("product"), product_id)
        self.assertEqual(result.get("unit_amount"), unit_amount)
        self.assertEqual(result.get("currency"), currency)

# This global variable and helper function are used to generate predictable, sequential timestamps
_test_suite_timestamp_counter = 1672531200  # Start of 2023-01-01 00:00:00 UTC as an integer timestamp

def _get_next_test_timestamp():
    """Generates a sequence of unique integer timestamps for testing."""
    global _test_suite_timestamp_counter
    _test_suite_timestamp_counter += 1
    return _test_suite_timestamp_counter

class TestListPrices(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self.DB = DB
        self.DB.clear()
        self.DB['products'] = {}
        self.DB['prices'] = {}

        global _test_suite_timestamp_counter, _test_suite_timestamp_counter_for_id_factory
        _test_suite_timestamp_counter = 0 # Reset main 'created' timestamp counter
        _test_suite_timestamp_counter_for_id_factory = 0 # Reset ID factory counter

        self.prod1_id = "prod_electronics_1"
        self.prod2_id = "prod_books_1"
        self.prod3_id = "prod_clothing_1"

        self._create_db_product(self.prod1_id, "Electronics Product")
        self._create_db_product(self.prod2_id, "Books Product")
        self._create_db_product(self.prod3_id, "Clothing Product")

    def _create_db_product(self, id: str, name: str, active: bool = True):
        timestamp = _get_next_test_timestamp() # Use main timestamp for product creation as well
        self.DB['products'][id] = {
            "id": id,
            "object": "product",
            "name": name,
            "active": active,
            "created": timestamp, # Product created time
            "updated": timestamp,
            "livemode": False,
            "description": f"Description for {name}",
            "metadata": None,
        }

    def _create_db_price(self, id: str, product_id: str, unit_amount: Optional[int], currency: str, **kwargs):
        price_data = {
            "id": id, # Provided ID
            "object": "price",
            "active": True,
            "product": product_id,
            "unit_amount": unit_amount,
            "currency": currency,
            "type": "one_time",
            "recurring": None,
            "livemode": False,
            "metadata": None,
            "billing_scheme": "per_unit",
            "created": _get_next_test_timestamp(), # Explicitly set 'created' timestamp
            "custom_unit_amount": None,
            "lookup_key": None,
            "nickname": None,
            "tax_behavior": None,
            "tiers": None,
            "tiers_mode": None,
            "transform_quantity": None,
            "unit_amount_decimal": None,
        }

        recurring_details_from_kwargs = kwargs.pop("recurring_details", None)

        for key, value in kwargs.items():
            if key in price_data:
                price_data[key] = value

        if recurring_details_from_kwargs:
            price_data["recurring"] = recurring_details_from_kwargs
            price_data["type"] = "recurring"

        if price_data["type"] == "recurring":
            if price_data["recurring"] is None:
                price_data["recurring"] = {"interval": "month", "interval_count": 1}
            if "interval" not in price_data["recurring"]: # Ensure base fields
                price_data["recurring"]["interval"] = "month"
            if "interval_count" not in price_data["recurring"]:
                price_data["recurring"]["interval_count"] = 1
            if "usage_type" not in price_data["recurring"]:
                price_data["recurring"]['usage_type'] = 'metered' if price_data.get("billing_scheme") == 'tiered' else 'licensed'
        elif price_data["type"] == "one_time":
            price_data["recurring"] = None

        if price_data["billing_scheme"] == "tiered":
            price_data["unit_amount"] = None
            price_data["unit_amount_decimal"] = None

        self.DB['prices'][id] = price_data

    # --- TESTS ---
    # The test assertions below EXPECT newest items first due to 'reverse=True' sort.
    # If these are failing with oldest items first, the 'list_prices' sort is not working as expected
    # in the testing environment.

    def test_list_prices_default_limit_and_no_product_filter(self):
        # Prices created from _0 (oldest) to _11 (newest)
        for i in range(12):
            self._create_db_price(f"price_default_{i}", self.prod1_id, 1000 + i, "usd")
        result = list_prices()
        self.assertEqual(result.get("object"), "list")
        data = result.get("data", [])
        self.assertEqual(len(data), 10)
        self.assertTrue(result.get("has_more"))
        returned_ids = [p['id'] for p in data]
        # Expected: newest 10, so price_default_11, price_default_10, ..., price_default_2
        expected_newest_ids = [f"price_default_{i}" for i in range(11, 1, -1)]
        self.assertEqual(returned_ids, expected_newest_ids)

    def test_list_prices_custom_limit(self):
        # Prices: _0 (oldest) to _4 (newest)
        for i in range(5):
            self._create_db_price(f"price_custom_limit_{i}", self.prod1_id, 1000 + i, "usd")
        result = list_prices(limit=3)
        data = result.get("data", [])
        self.assertEqual(len(data), 3)
        self.assertTrue(result.get("has_more"))
        returned_ids = [p['id'] for p in data]
        # Expected: _4, _3, _2
        expected_ids = [f"price_custom_limit_{i}" for i in range(4, 1, -1)]
        self.assertEqual(returned_ids, expected_ids)

    def test_list_prices_limit_one(self):
        self._create_db_price("price_limit_one_1", self.prod1_id, 1000, "usd") # Older
        self._create_db_price("price_limit_one_2", self.prod1_id, 2000, "usd") # Newer
        result = list_prices(limit=1)
        data = result.get("data", [])
        self.assertEqual(len(data), 1)
        self.assertTrue(result.get("has_more"))
        self.assertEqual(data[0]['id'], "price_limit_one_2") # Expect newest

    def test_list_prices_limit_max_100(self):
        # Prices _0 (oldest) to _104 (newest)
        for i in range(105):
            self._create_db_price(f"price_max_limit_{i}", self.prod1_id, 100 + i, "usd")
        result = list_prices(limit=100)
        data = result.get("data", [])
        self.assertEqual(len(data), 100)
        self.assertTrue(result.get("has_more"))
        returned_ids = [p['id'] for p in data]
        # Expected: _104 down to _5
        expected_ids = [f"price_max_limit_{i}" for i in range(104, 4, -1)]
        self.assertEqual(returned_ids, expected_ids)

    def test_list_prices_limit_exceeds_available(self):
        # Prices _0 (oldest) to _2 (newest)
        for i in range(3):
            self._create_db_price(f"price_limit_exceeds_{i}", self.prod1_id, 1000 + i, "usd")
        result = list_prices(limit=5)
        data = result.get("data", [])
        self.assertEqual(len(data), 3)
        self.assertFalse(result.get("has_more"))
        returned_ids = [p['id'] for p in data]
        # Expected: _2, _1, _0
        expected_ids = [f"price_limit_exceeds_{i}" for i in range(2, -1, -1)]
        self.assertEqual(returned_ids, expected_ids)

    def test_list_prices_no_prices_in_db(self):
        result = list_prices()
        self.assertEqual(result.get("object"), "list")
        self.assertEqual(len(result.get("data", [])), 0)
        self.assertFalse(result.get("has_more"))

    def test_list_prices_filter_by_product_id_success(self):
        self._create_db_price("p2_price1", self.prod2_id, 2000, "usd") # Other product
        self._create_db_price("p1_price1", self.prod1_id, 1000, "usd") # For prod1, older
        self._create_db_price("p1_price2", self.prod1_id, 1100, "usd") # For prod1, newer
        result = list_prices(product=self.prod1_id, limit=5)
        data = result.get("data", [])
        self.assertEqual(len(data), 2)
        self.assertFalse(result.get("has_more"))
        returned_ids = [p['id'] for p in data]
        self.assertEqual(returned_ids, ["p1_price2", "p1_price1"]) # Newest first for prod1
        for price_detail in data:
            self.assertEqual(price_detail['product'], self.prod1_id)

    def test_list_prices_filter_by_product_id_no_prices_for_product(self):
        self._create_db_price("p1_price1", self.prod1_id, 1000, "usd")
        result = list_prices(product=self.prod3_id) # prod3_id has no prices
        self.assertEqual(len(result.get("data", [])), 0)
        self.assertFalse(result.get("has_more"))

    def test_list_prices_filter_by_product_id_with_limit_has_more_true(self):
        # Prices _0 (oldest) to _11 (newest) for prod1_id
        for i in range(12):
            self._create_db_price(f"prod1_price_lim_{i}", self.prod1_id, 1000 + i, "usd")
        self._create_db_price("prod2_price_other", self.prod2_id, 5000, "eur") # Other product
        result = list_prices(product=self.prod1_id, limit=10)
        data = result.get("data", [])
        self.assertEqual(len(data), 10)
        self.assertTrue(result.get("has_more"))
        returned_ids = [p['id'] for p in data]
        # Expected: prod1_price_lim_11 down to prod1_price_lim_2
        expected_ids = [f"prod1_price_lim_{i}" for i in range(11, 1, -1)]
        self.assertEqual(returned_ids, expected_ids)
        for price_detail in data:
            self.assertEqual(price_detail['product'], self.prod1_id)

    def test_list_prices_invalid_limit_too_low(self):
        self.assert_error_behavior(
            func_to_call=list_prices,
            expected_exception_type=InvalidRequestError,
            expected_message="Limit must be between 1 and 100.",
            limit=0)

    def test_list_prices_invalid_limit_too_high(self):
        self.assert_error_behavior(
            func_to_call=list_prices,
            expected_exception_type=InvalidRequestError,
            expected_message="Limit must be between 1 and 100.",
            limit=101)

    def test_list_prices_non_existent_product_id(self):
        self.assert_error_behavior(
            func_to_call=list_prices,
            expected_exception_type=ResourceNotFoundError,
            expected_message="Product with ID 'prod_non_existent_xyz' not found.",
            product="prod_non_existent_xyz")

    def test_list_prices_price_detail_structure_one_time(self):
        price_id = "price_detail_1"
        self._create_db_price(
            price_id, self.prod1_id, 1500, "eur",
            active=True, billing_scheme="per_unit",
            livemode=False, lookup_key="lk_test1", metadata={"order": "123"},
            nickname="Euro Price", tax_behavior="inclusive", type="one_time"
        )
        created_ts = self.DB['prices'][price_id]['created']
        result = list_prices(product=self.prod1_id)
        self.assertEqual(len(result['data']), 1)
        price_detail = result['data'][0]
        self.assertEqual(price_detail['id'], price_id)
        self.assertEqual(price_detail['object'], "price")
        self.assertTrue(price_detail['active'])
        self.assertEqual(price_detail['billing_scheme'], "per_unit")
        self.assertEqual(price_detail['created'], created_ts)
        # ... (rest of assertions from user's test) ...
        self.assertEqual(price_detail['currency'], "eur")
        self.assertFalse(price_detail['livemode'])
        self.assertEqual(price_detail['lookup_key'], "lk_test1")
        self.assertEqual(price_detail['metadata'], {"order": "123"})
        self.assertEqual(price_detail['nickname'], "Euro Price")
        self.assertEqual(price_detail['product'], self.prod1_id)
        self.assertEqual(price_detail['tax_behavior'], "inclusive")
        self.assertEqual(price_detail['type'], "one_time")
        self.assertEqual(price_detail['unit_amount'], 1500)
        self.assertIsNone(price_detail.get('recurring'))
        self.assertIsNone(price_detail.get('custom_unit_amount'))
        self.assertIsNone(price_detail.get('tiers'))
        self.assertIsNone(price_detail.get('tiers_mode'))
        self.assertIsNone(price_detail.get('transform_quantity'))
        self.assertIsNone(price_detail.get('unit_amount_decimal'))


    def test_list_prices_price_detail_structure_recurring(self):
        db_recurring_details = {"interval": "month", "interval_count": 2, "trial_period_days": None}
        self._create_db_price(
            "price_detail_recurring_1", self.prod1_id, 2500, "gbp",
            type="recurring", recurring_details=db_recurring_details
        )
        result = list_prices(product=self.prod1_id)
        self.assertEqual(len(result['data']), 1)
        price_detail = result['data'][0]
        self.assertEqual(price_detail['id'], "price_detail_recurring_1")
        self.assertEqual(price_detail['type'], "recurring")
        self.assertEqual(price_detail['unit_amount'], 2500)
        self.assertIsNotNone(price_detail.get('recurring'))
        recurring_info = price_detail['recurring']
        self.assertEqual(recurring_info['interval'], "month")
        self.assertEqual(recurring_info['interval_count'], 2)
        self.assertEqual(recurring_info['usage_type'], "licensed")
        self.assertIsNone(recurring_info.get('trial_period_days'))

    def test_list_prices_price_detail_with_all_optional_fields(self):
        db_custom_unit_dict = {"minimum": 100, "maximum": 1000, "preset": 200}
        db_tiers_data_dict = [
            {"up_to": 10, "unit_amount": 500}, {"up_to": None, "flat_amount": 5000}
        ]
        db_transform_data_dict = {"divide_by": 10, "round": "up"}

        self._create_db_price( # This is older
            "price_full_opts", self.prod2_id, None, "usd",
            billing_scheme="tiered", tiers_mode="graduated",
            custom_unit_amount=db_custom_unit_dict, tiers=db_tiers_data_dict,
            transform_quantity=db_transform_data_dict, lookup_key="full_price",
            nickname="Fully Optional Price", tax_behavior="exclusive",
            metadata={"complex": "data"}, type="one_time"
        )
        db_recurring_details_tiered = {"interval": "week", "interval_count": 1}
        self._create_db_price( # This is newer
            "price_full_opts_recurring_tiered", self.prod2_id, None, "usd",
            type="recurring", recurring_details=db_recurring_details_tiered,
            billing_scheme="tiered", tiers_mode="graduated",
            custom_unit_amount=db_custom_unit_dict, tiers=db_tiers_data_dict,
            transform_quantity=db_transform_data_dict
        )
        # With limit=1, should get the newest one: "price_full_opts_recurring_tiered"
        result = list_prices(product=self.prod2_id, limit=1)
        self.assertEqual(len(result['data']), 1)
        price_detail = result['data'][0]
        self.assertEqual(price_detail['id'], "price_full_opts_recurring_tiered") # Check if newest is fetched
        self.assertEqual(price_detail['type'], "recurring")
        self.assertEqual(price_detail['billing_scheme'], "tiered")
        self.assertIsNone(price_detail.get('unit_amount'))
        self.assertIsNone(price_detail.get('unit_amount_decimal'))
        recurring_info_rt = price_detail['recurring']
        self.assertEqual(recurring_info_rt.get('usage_type'), "metered")

    def test_sorting_and_pagination_consistency(self):
        all_prod1_price_ids = []
        for i in range(25): # p1_page_0 (oldest) to p1_page_24 (newest)
            price_id = f"p1_page_{i}"
            self._create_db_price(price_id, self.prod1_id, 1000 + i * 10, "usd")
            all_prod1_price_ids.append(price_id)
        expected_all_prod1_ids_sorted_newest_first = list(reversed(all_prod1_price_ids))

        result_p1 = list_prices(product=self.prod1_id)
        self.assertEqual(len(result_p1['data']), 10)
        self.assertTrue(result_p1['has_more'])
        self.assertEqual([p['id'] for p in result_p1['data']], expected_all_prod1_ids_sorted_newest_first[0:10])

        result_p1_limit5 = list_prices(product=self.prod1_id, limit=5)
        self.assertEqual(len(result_p1_limit5['data']), 5)
        self.assertTrue(result_p1_limit5['has_more'])
        self.assertEqual([p['id'] for p in result_p1_limit5['data']], expected_all_prod1_ids_sorted_newest_first[0:5])

        result_p1_limit30 = list_prices(product=self.prod1_id, limit=30)
        self.assertEqual(len(result_p1_limit30['data']), 25)
        self.assertFalse(result_p1_limit30['has_more'])
        self.assertEqual([p['id'] for p in result_p1_limit30['data']], expected_all_prod1_ids_sorted_newest_first)

    def test_list_prices_invalid_product_type(self):
        with self.assertRaisesRegex(TypeError, "Invalid type for 'product'. Expected a string or None."):
            list_prices(product=123)

    def test_list_prices_invalid_limit_type(self):
        with self.assertRaisesRegex(TypeError, "Invalid type for 'limit'. Expected an integer or None."):
            list_prices(limit="abc")

    def test_list_prices_limit_is_none_uses_default(self):
        for i in range(12): # _0 (oldest) to _11 (newest)
            self._create_db_price(f"price_limit_none_{i}", self.prod1_id, 1000 + i, "usd")
        result = list_prices(limit=None)
        self.assertEqual(len(result.get("data", [])), 10)
        self.assertTrue(result.get("has_more"))
        returned_ids = [p['id'] for p in result.get("data", [])]
        expected_newest_ids = [f"price_limit_none_{i}" for i in range(11, 1, -1)] # _11 down to _2
        self.assertEqual(returned_ids, expected_newest_ids)

    def test_list_prices_product_is_none_no_filter(self):
        self._create_db_price("p1_price_prod_none", self.prod1_id, 1000, "usd") # Older
        self._create_db_price("p2_price_prod_none", self.prod2_id, 2000, "eur") # Newer
        result = list_prices(product=None, limit=5)
        data = result.get("data", [])
        self.assertEqual(len(data), 2)
        self.assertFalse(result.get("has_more"))
        returned_ids = [p['id'] for p in data]
        expected_ids = ["p2_price_prod_none", "p1_price_prod_none"] # Newest first
        self.assertEqual(returned_ids, expected_ids)

    def test_list_prices_limit_equals_available_no_product_filter(self):
        for i in range(5): # _0 (oldest) to _4 (newest)
            self._create_db_price(f"price_limit_eq_avail_{i}", self.prod1_id, 1000 + i, "usd")
        result = list_prices(limit=5)
        data = result.get("data", [])
        self.assertEqual(len(data), 5)
        self.assertFalse(result.get("has_more"))
        returned_ids = [p['id'] for p in data]
        expected_ids = [f"price_limit_eq_avail_{i}" for i in range(4, -1, -1)] # _4 down to _0
        self.assertEqual(returned_ids, expected_ids)

    def test_list_prices_limit_equals_available_for_filtered_product(self):
        for i in range(3): # p1_..._0 (oldest) to p1_..._2 (newest) for prod1
            self._create_db_price(f"p1_limit_eq_avail_{i}", self.prod1_id, 1000 + i, "usd")
        for i in range(5): # Prices for another product
            self._create_db_price(f"p2_other_{i}", self.prod2_id, 2000 + i, "eur")
        result = list_prices(product=self.prod1_id, limit=3)
        data = result.get("data", [])
        self.assertEqual(len(data), 3)
        self.assertFalse(result.get("has_more"))
        returned_ids = [p['id'] for p in data]
        expected_ids = [f"p1_limit_eq_avail_{i}" for i in range(2, -1, -1)] # p1_..._2, _1, _0
        self.assertEqual(returned_ids, expected_ids)
        for price_item in data:
            self.assertEqual(price_item['product'], self.prod1_id)

    def test_list_prices_product_id_empty_string_is_invalid_parameter(self): # Renamed for clarity
        empty_prod_id = ""

        expected_msg = "Input validation failed: Error in field 'product': Product ID must be a non-empty string."
        self.assert_error_behavior(
            func_to_call=list_prices,
            expected_exception_type=InvalidRequestError,
            expected_message=expected_msg,
            product=empty_prod_id, # Pass the empty string
            limit=5
        )

    def test_list_prices_recurring_preserves_explicit_db_fields(self):
        recurring_details_dict = {
            "interval": "week", "interval_count": 2,
            "usage_type": "metered", "trial_period_days": 7
        }
        self._create_db_price(
            "r_price_explicit", self.prod2_id, 300, "gbp",
            type="recurring", recurring_details=recurring_details_dict,
            billing_scheme="per_unit"
        )
        result = list_prices(product=self.prod2_id, limit=1)
        price = result['data'][0]
        self.assertEqual(price['id'], "r_price_explicit")
        self.assertIsNotNone(price['recurring'])
        recurring_data = price['recurring']
        self.assertEqual(recurring_data.get('interval'), "week")
        self.assertEqual(recurring_data.get('interval_count'), 2)
        self.assertEqual(recurring_data.get('usage_type'), "metered")
        self.assertEqual(recurring_data.get('trial_period_days'), 7)

    def test_list_prices_active_filter_not_implemented_but_data_present(self):
        active_price_id = "price_is_active"    # Created first (older)
        inactive_price_id = "price_is_inactive" # Created second (newer)
        self._create_db_price(active_price_id, self.prod1_id, 100, "usd", active=True)
        self._create_db_price(inactive_price_id, self.prod1_id, 200, "usd", active=False)
        result = list_prices(product=self.prod1_id, limit=5)
        data = result.get("data", [])
        self.assertEqual(len(data), 2)
        returned_ids_ordered = [p['id'] for p in data]
        expected_ids_ordered = [inactive_price_id, active_price_id] # Newest first
        self.assertEqual(returned_ids_ordered, expected_ids_ordered)
        for p in data:
            if p['id'] == active_price_id: self.assertTrue(p['active'])
            elif p['id'] == inactive_price_id: self.assertFalse(p['active'])

if __name__ == '__main__':
    unittest.main()