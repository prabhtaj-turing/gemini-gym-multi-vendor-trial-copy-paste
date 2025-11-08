"""
Test cases for phone utility functions
"""

import unittest
from .account_management_base_exception import AccountManagementBaseTestCase
from ..SimulationEngine.phone_utils import is_phone_number_valid, normalize_phone_number


class TestPhoneUtils(AccountManagementBaseTestCase):
    """
    Test suite for phone utility functions.
    Tests phone number validation and normalization functionality.
    """

    def test_phone_validation_comprehensive(self):
        """Test phone validation with various valid and invalid formats."""
        # Valid formats (should return True)
        valid_cases = [
            "123-456-7890",  # Standard format
            "1234567890",  # No separators
            "123 456 7890",  # Spaces
            "123.456.7890",  # Dots
            "(123) 456-7890",  # Parentheses
            " 123-456-7890 ",  # Whitespace
        ]

        # Invalid formats (should return False)
        invalid_cases = [
            None,
            "",
            "123",
            "123-456",
            "123-456-789",
            "123-456-78901",
            "abc-def-ghij",
            "123-456-789a",
            "123456789",
            "12345678901",
            "1-123-456-7890",
            "+1 123 456 7890",
        ]

        for phone in valid_cases:
            with self.subTest(phone=phone, expected=True):
                self.assertTrue(is_phone_number_valid(phone))

        for phone in invalid_cases:
            with self.subTest(phone=phone, expected=False):
                self.assertFalse(is_phone_number_valid(phone))

    def test_phone_normalization_comprehensive(self):
        """Test phone normalization with various input formats."""
        test_cases = [
            # (input, expected_output)
            ("123-456-7890", "123-456-7890"),  # Already correct
            ("1234567890", "123-456-7890"),  # No separators
            ("123 456 7890", "123-456-7890"),  # Spaces
            ("123.456.7890", "123-456-7890"),  # Dots
            ("(123) 456-7890", "123-456-7890"),  # Parentheses
            ("123-456.7890", "123-456-7890"),  # Mixed separators
            ("(123)456-7890", "123-456-7890"),  # No space after parens
            (" 123-456-7890 ", "123-456-7890"),  # Whitespace
            ("123@456#7890", "123-456-7890"),  # Special chars
            ("000-000-0000", "000-000-0000"),  # Edge case: all zeros
        ]

        for phone, expected in test_cases:
            with self.subTest(phone=phone):
                result = normalize_phone_number(phone)
                self.assertEqual(result, expected)

    def test_phone_normalization_invalid_inputs(self):
        """Test normalization returns None for invalid inputs."""
        invalid_inputs = [
            None,
            "",
            "123",
            "123-456",
            "123-456-789",
            "123-456-78901",
            "abc-def-ghij",
            "123-456-789a",
            "123456789",
            "12345678901",
        ]

        for phone in invalid_inputs:
            with self.subTest(phone=phone):
                result = normalize_phone_number(phone)
                self.assertIsNone(result)

    def test_phone_utils_consistency_and_edge_cases(self):
        """Test consistency between validation and normalization, plus edge cases."""
        # Test consistency: valid phones should normalize to valid format
        test_phones = [
            "123-456-7890",
            "1234567890",
            "123 456 7890",
            "123.456.7890",
            "(123) 456-7890",
            "+1 123 456 7890",
        ]

        for phone in test_phones:
            with self.subTest(phone=phone):
                if is_phone_number_valid(phone):
                    normalized = normalize_phone_number(phone)
                    self.assertIsNotNone(normalized)
                    self.assertTrue(is_phone_number_valid(normalized))
                else:
                    normalized = normalize_phone_number(phone)
                    self.assertIsNone(normalized)

        # Test edge cases
        self.assertEqual(
            normalize_phone_number(9999999999), "999-999-9999"
        )  # Integer input
        self.assertTrue(is_phone_number_valid(9999999999))  # Integer validation

        # Test region code parameter (should be ignored)
        phone = "1234567890"
        self.assertEqual(normalize_phone_number(phone, "US"), "123-456-7890")
        self.assertTrue(is_phone_number_valid(phone, "CA"))

    def test_phone_utils_deterministic_behavior(self):
        """Test that functions are deterministic and handle repeated calls."""
        phone = "1234567890"

        # Multiple calls should return same results
        self.assertEqual(is_phone_number_valid(phone), is_phone_number_valid(phone))
        self.assertEqual(normalize_phone_number(phone), normalize_phone_number(phone))


if __name__ == "__main__":
    unittest.main()
