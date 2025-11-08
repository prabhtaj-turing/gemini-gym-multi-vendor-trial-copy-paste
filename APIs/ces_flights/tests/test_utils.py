import unittest
import sys
import os
from datetime import date

# Add the parent directory to the path to fix imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ces_flights.SimulationEngine.utils import (
    validate_string,
    validate_date,
    current_timestamp,
    ensure_json_serializable,
    convert_city_format,
    validate_date_range,
    validate_booking_date_range,
    validate_date_in_range,
    process_date_without_year,
    validate_workflow_order,
    validate_booking_readiness,
    get_end_of_conversation_status,
    convert_price,
    convert_price_to_usd,
    is_valid_currency,
    get_supported_currencies,
    CURRENCY_EXCHANGE_RATES,
    SUPPORTED_CURRENCIES
)
from ces_flights.SimulationEngine.custom_errors import ValidationError


class TestValidateString(BaseTestCaseWithErrorHandler):
    """Test string validation functionality."""

    def test_validate_string_valid(self):
        self.assertEqual(validate_string(" test ", "field"), "test")

    def test_validate_string_invalid_type(self):
        with self.assertRaises(ValidationError):
            validate_string(123, "field")

    def test_validate_string_empty_not_allowed(self):
        with self.assertRaises(ValidationError):
            validate_string("   ", "field")


class TestValidateDate(BaseTestCaseWithErrorHandler):
    """Test date validation functionality."""

    def test_validate_date_valid(self):
        self.assertEqual(validate_date("2024-04-01", "departure"), date(2024, 4, 1))

    def test_validate_date_invalid(self):
        with self.assertRaises(ValidationError):
            validate_date("not-a-date", "departure")


class TestCurrentTimestamp(BaseTestCaseWithErrorHandler):
    """Test timestamp functionality."""

    def test_current_timestamp_format(self):
        ts = current_timestamp()
        self.assertIn("T", ts)  # ISO-8601


class TestEnsureJsonSerializable(BaseTestCaseWithErrorHandler):
    """Test JSON serialization."""

    def test_ensure_json_serializable_success(self):
        self.assertEqual(ensure_json_serializable({"key": "value"}), {"key": "value"})

    def test_ensure_json_serializable_failure(self):
        class NonSerializable:
            pass
        with self.assertRaises(ValidationError):
            ensure_json_serializable(NonSerializable())


class TestCityFormatConversion(BaseTestCaseWithErrorHandler):
    """Test city format conversion functionality."""

    def test_convert_city_format_us_cities(self):
        """Test conversion of US cities to IATA codes"""
        self.assertEqual(convert_city_format("New York"), "JFK")
        self.assertEqual(convert_city_format("LA"), "LAX")
        self.assertEqual(convert_city_format("Chicago"), "ORD")
        self.assertEqual(convert_city_format("Houston"), "IAH")
        self.assertEqual(convert_city_format("Phoenix"), "PHX")
        self.assertEqual(convert_city_format("Philadelphia"), "PHL")
        self.assertEqual(convert_city_format("San Antonio"), "SAT")
        self.assertEqual(convert_city_format("San Diego"), "SAN")
        self.assertEqual(convert_city_format("Dallas"), "DFW")
        self.assertEqual(convert_city_format("San Jose"), "SJC")

    def test_convert_city_format_international_cities(self):
        """Test conversion of international cities to IATA codes"""
        self.assertEqual(convert_city_format("London"), "LHR")
        self.assertEqual(convert_city_format("Paris"), "CDG")
        self.assertEqual(convert_city_format("Tokyo"), "NRT")
        self.assertEqual(convert_city_format("Sydney"), "SYD")
        self.assertEqual(convert_city_format("Toronto"), "YYZ")
        self.assertEqual(convert_city_format("Vancouver"), "YVR")
        self.assertEqual(convert_city_format("Montreal"), "YUL")
        self.assertEqual(convert_city_format("Mexico City"), "MEX")
        self.assertEqual(convert_city_format("Madrid"), "MAD")
        self.assertEqual(convert_city_format("Rome"), "FCO")

    def test_convert_city_format_case_insensitive(self):
        """Test that city conversion is case insensitive"""
        self.assertEqual(convert_city_format("NEW YORK"), "JFK")
        self.assertEqual(convert_city_format("los angeles"), "LAX")
        self.assertEqual(convert_city_format("LONDON"), "LHR")
        self.assertEqual(convert_city_format("mumbai"), "BOM")

    def test_convert_city_format_already_formatted(self):
        """Test that already formatted cities are returned as uppercase"""
        self.assertEqual(convert_city_format("New York, NY"), "NEW YORK, NY")
        self.assertEqual(convert_city_format("Los Angeles, CA"), "LOS ANGELES, CA")
        self.assertEqual(convert_city_format("London, United Kingdom"), "LONDON, UNITED KINGDOM")
        self.assertEqual(convert_city_format("Mumbai, India"), "MUMBAI, INDIA")

    def test_convert_city_format_unknown_city(self):
        """Test that unknown cities are returned as uppercase"""
        self.assertEqual(convert_city_format("Unknown City"), "UNKNOWN CITY")
        self.assertEqual(convert_city_format("Some Random Place"), "SOME RANDOM PLACE")

    def test_convert_city_format_edge_cases(self):
        """Test edge cases for city conversion"""
        self.assertEqual(convert_city_format(""), "")
        self.assertIsNone(convert_city_format(None))
        self.assertEqual(convert_city_format("   "), "   ")


class TestDateValidation(BaseTestCaseWithErrorHandler):
    """Test date validation functionality."""

    def test_validate_date_range_valid(self):
        """Test valid date range validation"""
        earliest = date(2024, 12, 25)
        latest = date(2024, 12, 30)
        # Should not raise any exception
        validate_date_range(earliest, latest, "departure")

    def test_validate_date_range_invalid(self):
        """Test invalid date range validation (earliest after latest)"""
        earliest = date(2024, 12, 30)
        latest = date(2024, 12, 25)
        
        with self.assertRaises(ValidationError) as exc_info:
            validate_date_range(earliest, latest, "departure")
        
        self.assertIn("Earliest departure date cannot be after latest departure date", str(exc_info.exception))

    def test_validate_booking_date_range_valid(self):
        """Test valid booking date range (return after departure)"""
        departure = date(2024, 12, 25)
        return_date = date(2025, 1, 5)
        # Should not raise any exception
        validate_booking_date_range(departure, return_date)

    def test_validate_booking_date_range_invalid(self):
        """Test invalid booking date range (return before departure)"""
        departure = date(2024, 12, 25)
        return_date = date(2024, 12, 20)
        
        with self.assertRaises(ValidationError) as exc_info:
            validate_booking_date_range(departure, return_date)
        
        self.assertIn("Return date cannot be before departure date", str(exc_info.exception))

    def test_validate_date_in_range_past_date(self):
        """Test validation rejects past dates"""
        past_date = date(2022, 6, 10)
        
        with self.assertRaises(ValidationError) as exc_info:
            validate_date_in_range(past_date, "earliest_departure_date")
        
        self.assertIn("past", str(exc_info.exception).lower())
        self.assertIn("future date", str(exc_info.exception))

    def test_validate_date_in_range_future_too_far(self):
        """Test validation rejects dates too far in the future"""
        from datetime import timedelta
        future_date = date.today() + timedelta(days=400)  # More than 1 year
        
        with self.assertRaises(ValidationError) as exc_info:
            validate_date_in_range(future_date, "earliest_departure_date")
        
        self.assertIn("future", str(exc_info.exception).lower())
        self.assertIn("year", str(exc_info.exception))

    def test_validate_date_in_range_valid(self):
        """Test validation accepts valid future dates"""
        from datetime import timedelta
        valid_future_date = date.today() + timedelta(days=30)  # 30 days in future
        
        # Should not raise any exception
        validate_date_in_range(valid_future_date, "earliest_departure_date")


class TestDateProcessing(BaseTestCaseWithErrorHandler):
    """Test date processing functionality."""

    def test_process_date_without_year_basic(self):
        """Test basic date processing functionality"""
        # Test full date (should pass through)
        result = process_date_without_year("2024-12-25")
        self.assertEqual(result, "2024-12-25")
        
        # Test MM-DD format
        from datetime import date, timedelta
        today = date.today()
        future_date = today + timedelta(days=30)
        month_day = f"{future_date.month:02d}-{future_date.day:02d}"
        
        result = process_date_without_year(month_day)
        expected = f"{today.year}-{month_day}"
        self.assertEqual(result, expected)

    def test_process_date_without_year_validation(self):
        """Test date validation and error handling"""
        # Test invalid month
        with self.assertRaises(ValidationError):
            process_date_without_year("13-25")
        
        # Test invalid day
        with self.assertRaises(ValidationError):
            process_date_without_year("12-32")
        
        # Test invalid format
        with self.assertRaises(ValidationError):
            process_date_without_year("12/25")


class TestWorkflowValidation(BaseTestCaseWithErrorHandler):
    """Test workflow validation functionality."""

    def test_validate_workflow_order_valid(self):
        """Test valid workflow order progression"""
        # Complete data for all steps
        complete_data = {
            "origin": "Los Angeles, CA",
            "destination": "New York, NY",
            "earliest_departure_date": "12-25",
            "latest_departure_date": "12-25",
            "earliest_return_date": "12-30",
            "latest_return_date": "12-30",
            "num_adult_passengers": 1,
            "num_child_passengers": 0
        }
        
        # Should not raise any exception
        validate_workflow_order("preferences", complete_data)

    def test_validate_workflow_order_missing_origin(self):
        """Test workflow order validation with missing origin"""
        incomplete_data = {
            "destination": "New York, NY",
            "earliest_departure_date": "12-25",
            "latest_departure_date": "12-25",
            "earliest_return_date": "12-30",
            "latest_return_date": "12-30",
            "num_adult_passengers": 1,
            "num_child_passengers": 0
        }
        
        with self.assertRaises(ValidationError) as exc_info:
            validate_workflow_order("preferences", incomplete_data)
        
        self.assertIn("origin_destination", str(exc_info.exception))

    def test_validate_workflow_order_missing_dates(self):
        """Test workflow order validation with missing dates"""
        incomplete_data = {
            "origin": "Los Angeles, CA",
            "destination": "New York, NY",
            "num_adult_passengers": 1,
            "num_child_passengers": 0
        }
        
        with self.assertRaises(ValidationError) as exc_info:
            validate_workflow_order("preferences", incomplete_data)
        
        self.assertIn("dates", str(exc_info.exception))

    def test_validate_workflow_order_missing_passengers(self):
        """Test workflow order validation with missing passenger counts"""
        incomplete_data = {
            "origin": "Los Angeles, CA",
            "destination": "New York, NY",
            "earliest_departure_date": "12-25",
            "latest_departure_date": "12-25",
            "earliest_return_date": "12-30",
            "latest_return_date": "12-30"
        }
        
        with self.assertRaises(ValidationError) as exc_info:
            validate_workflow_order("preferences", incomplete_data)
        
        self.assertIn("passengers", str(exc_info.exception))

    def test_validate_booking_readiness_valid(self):
        """Test booking readiness validation with complete information"""
        # Should not raise any exception
        validate_booking_readiness(flight_selected=True, travelers_complete=True)

    def test_validate_booking_readiness_no_flight(self):
        """Test booking readiness validation without flight selection"""
        with self.assertRaises(ValidationError) as exc_info:
            validate_booking_readiness(flight_selected=False, travelers_complete=True)
        
        self.assertIn("select a flight", str(exc_info.exception))

    def test_validate_booking_readiness_incomplete_travelers(self):
        """Test booking readiness validation with incomplete traveler info"""
        with self.assertRaises(ValidationError) as exc_info:
            validate_booking_readiness(flight_selected=True, travelers_complete=False)
        
        self.assertIn("traveler information", str(exc_info.exception))


class TestGetEndOfConversationStatus(BaseTestCaseWithErrorHandler):
    """Test get_end_of_conversation_status utility function."""
    
    def setUp(self):
        """Set up test database."""
        from ces_flights.SimulationEngine import db
        db.DB.clear()
        db.DB["_end_of_conversation_status"] = {}
    
    def test_get_end_of_conversation_status_empty(self):
        """Test getting status when database is empty"""
        from ces_flights.SimulationEngine import db
        db.DB["_end_of_conversation_status"] = {}
        
        # Get all statuses
        result = get_end_of_conversation_status()
        self.assertEqual(result, {})
        
        # Get specific function status
        result = get_end_of_conversation_status("done")
        self.assertIsNone(result)
    
    def test_get_end_of_conversation_status_specific_function(self):
        """Test getting status for a specific terminal function"""
        from ces_flights.SimulationEngine import db
        test_data = {
            "status": "completed",
            "timestamp": "2025-10-17T12:00:00",
            "input": "test message"
        }
        db.DB["_end_of_conversation_status"]["done"] = test_data
        
        result = get_end_of_conversation_status("done")
        self.assertEqual(result, test_data)
    
    def test_get_end_of_conversation_status_all_functions(self):
        """Test getting status for all terminal functions"""
        from ces_flights.SimulationEngine import db
        test_data = {
            "done": {"status": "completed", "timestamp": "2025-10-17T12:00:00"},
            "escalate": {"status": "escalated", "timestamp": "2025-10-17T12:01:00"},
            "fail": {"status": "failed", "timestamp": "2025-10-17T12:02:00"},
            "cancel": {"status": "cancelled", "timestamp": "2025-10-17T12:03:00"}
        }
        db.DB["_end_of_conversation_status"] = test_data
        
        result = get_end_of_conversation_status()
        self.assertEqual(result, test_data)
    
    def test_get_end_of_conversation_status_nonexistent_function(self):
        """Test getting status for a function that doesn't exist"""
        from ces_flights.SimulationEngine import db
        db.DB["_end_of_conversation_status"]["done"] = {"status": "completed"}
        
        result = get_end_of_conversation_status("nonexistent")
        self.assertIsNone(result)
    
    def test_get_end_of_conversation_status_none_db(self):
        """Test getting status when _end_of_conversation_status key doesn't exist"""
        from ces_flights.SimulationEngine import db
        if "_end_of_conversation_status" in db.DB:
            del db.DB["_end_of_conversation_status"]
        
        result = get_end_of_conversation_status()
        self.assertIsNone(result)


class TestCurrencyConversion(BaseTestCaseWithErrorHandler):
    """Test currency conversion functionality."""

    def test_currency_exchange_rates_exist(self):
        """Test that currency exchange rates dictionary is properly initialized"""
        self.assertIsNotNone(CURRENCY_EXCHANGE_RATES)
        self.assertEqual(len(CURRENCY_EXCHANGE_RATES), 20)
        self.assertEqual(CURRENCY_EXCHANGE_RATES["USD"], 1.00)

    def test_supported_currencies(self):
        """Test that all 20 currencies are in supported currencies set"""
        self.assertIsNotNone(SUPPORTED_CURRENCIES)
        self.assertEqual(len(SUPPORTED_CURRENCIES), 20)
        expected = {"USD", "EUR", "JPY", "GBP", "CNY", "AUD", "CAD", "CHF", "HKD", "SGD",
                   "SEK", "KRW", "NOK", "NZD", "INR", "MXN", "TWD", "ZAR", "BRL", "DKK"}
        self.assertEqual(SUPPORTED_CURRENCIES, expected)

    def test_is_valid_currency_supported(self):
        """Test is_valid_currency returns True for supported currencies"""
        self.assertTrue(is_valid_currency("USD"))
        self.assertTrue(is_valid_currency("EUR"))
        self.assertTrue(is_valid_currency("JPY"))
        # Test case insensitivity
        self.assertTrue(is_valid_currency("usd"))
        self.assertTrue(is_valid_currency("Eur"))

    def test_is_valid_currency_unsupported(self):
        """Test is_valid_currency returns False for unsupported currencies"""
        self.assertFalse(is_valid_currency("INVALID"))
        self.assertFalse(is_valid_currency("XYZ"))
        self.assertFalse(is_valid_currency(""))

    def test_get_supported_currencies(self):
        """Test get_supported_currencies returns sorted list"""
        currencies = get_supported_currencies()
        self.assertIsInstance(currencies, list)
        self.assertEqual(len(currencies), 20)
        # Check it's sorted
        self.assertEqual(currencies, sorted(currencies))
        # Check it contains expected currencies
        self.assertIn("USD", currencies)
        self.assertIn("EUR", currencies)
        self.assertIn("JPY", currencies)

    def test_convert_price_usd_to_usd(self):
        """Test converting USD to USD returns same amount"""
        result = convert_price(100.0, "USD")
        self.assertEqual(result, 100.0)

    def test_convert_price_usd_to_eur(self):
        """Test converting USD to EUR"""
        result = convert_price(100.0, "EUR")
        # EUR rate is 0.92, so 100 USD = 92 EUR
        self.assertEqual(result, 92.0)

    def test_convert_price_usd_to_jpy(self):
        """Test converting USD to JPY"""
        result = convert_price(100.0, "JPY")
        # JPY rate is 156.12, so 100 USD = 15612 JPY
        self.assertEqual(result, 15612.0)

    def test_convert_price_usd_to_gbp(self):
        """Test converting USD to GBP"""
        result = convert_price(100.0, "GBP")
        # GBP rate is 0.79, so 100 USD = 79 GBP
        self.assertEqual(result, 79.0)

    def test_convert_price_case_insensitive(self):
        """Test that currency codes are case-insensitive"""
        result_lower = convert_price(100.0, "eur")
        result_upper = convert_price(100.0, "EUR")
        self.assertEqual(result_lower, result_upper)
        self.assertEqual(result_lower, 92.0)

    def test_convert_price_rounding(self):
        """Test that prices are rounded to 2 decimal places"""
        result = convert_price(10.5, "EUR")
        # 10.5 * 0.92 = 9.66
        self.assertEqual(result, 9.66)

    def test_convert_price_invalid_currency(self):
        """Test that invalid currency raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            convert_price(100.0, "INVALID")
        self.assertIn("Unsupported currency", str(context.exception))

    def test_convert_price_to_usd_from_usd(self):
        """Test converting USD to USD returns same amount"""
        result = convert_price_to_usd(100.0, "USD")
        self.assertEqual(result, 100.0)

    def test_convert_price_to_usd_from_eur(self):
        """Test converting EUR to USD"""
        result = convert_price_to_usd(92.0, "EUR")
        # 92 EUR / 0.92 = 100 USD
        self.assertEqual(result, 100.0)

    def test_convert_price_to_usd_from_jpy(self):
        """Test converting JPY to USD"""
        result = convert_price_to_usd(15612.0, "JPY")
        # 15612 JPY / 156.12 = 100 USD
        self.assertEqual(result, 100.0)

    def test_convert_price_to_usd_case_insensitive(self):
        """Test that currency codes are case-insensitive for USD conversion"""
        result_lower = convert_price_to_usd(92.0, "eur")
        result_upper = convert_price_to_usd(92.0, "EUR")
        self.assertEqual(result_lower, result_upper)
        self.assertEqual(result_lower, 100.0)

    def test_convert_price_to_usd_invalid_currency(self):
        """Test that invalid currency raises ValidationError"""
        with self.assertRaises(ValidationError) as context:
            convert_price_to_usd(100.0, "INVALID")
        self.assertIn("Unsupported currency", str(context.exception))

    def test_round_trip_conversion(self):
        """Test that converting USD to currency and back yields original amount"""
        original_usd = 123.45
        for currency in ["EUR", "JPY", "GBP", "CAD", "AUD"]:
            converted = convert_price(original_usd, currency)
            back_to_usd = convert_price_to_usd(converted, currency)
            # Allow small rounding differences
            self.assertAlmostEqual(back_to_usd, original_usd, places=1,
                                  msg=f"Round trip conversion failed for {currency}")

    def test_all_currencies_have_exchange_rates(self):
        """Test that all supported currencies have valid exchange rates"""
        for currency in SUPPORTED_CURRENCIES:
            self.assertIn(currency, CURRENCY_EXCHANGE_RATES)
            rate = CURRENCY_EXCHANGE_RATES[currency]
            self.assertGreater(rate, 0, f"{currency} rate should be positive")

    def test_convert_price_all_supported_currencies(self):
        """Test converting to all supported currencies"""
        test_amount = 100.0
        for currency in SUPPORTED_CURRENCIES:
            result = convert_price(test_amount, currency)
            self.assertIsInstance(result, float)
            self.assertGreater(result, 0)
            # Check rounding to 2 decimal places
            self.assertEqual(result, round(result, 2))


if __name__ == "__main__":
    unittest.main()