import unittest
from ..SimulationEngine.phone_utils import normalize_phone_number


class TestPhoneUtils(unittest.TestCase):
    """Test cases for phone number normalization and validation."""

    def test_valid_e164_numbers(self):
        """Test that valid E.164 phone numbers are normalized correctly."""
        test_cases = [
            # Basic E.164 numbers
            ("+14155552671", "+14155552671"),
            ("+1234567890", "+1234567890"),
            ("+919876543210", "+919876543210"),

            # E.164 with separators that should be removed
            ("+1 415 555 2671", "+14155552671"),
            ("+1-415-555-2671", "+14155552671"),
            ("+1.415.555.2671", "+14155552671"),
            ("+1 (415) 555-2671", "+14155552671"),

            # E.164 with minimum and maximum valid lengths
            ("+12345678", "+12345678"),  # 8 digits after +
            ("+123456789012345", "+123456789012345"),  # 15 digits after +
        ]

        for input_number, expected in test_cases:
            with self.subTest(input_number=input_number):
                result = normalize_phone_number(input_number)
                self.assertEqual(result, expected, f"Failed for input: {input_number}")

    def test_domestic_numbers_rejected(self):
        """Test that domestic phone numbers without + are rejected."""
        domestic_numbers = [
            "4155552671",      # 10 digits, no +
            "123456789",       # 9 digits, no +
            "1234567890",      # 10 digits, no +
            "123456789012345", # 15 digits, no +
            "12345678",        # 8 digits, no +
        ]

        for number in domestic_numbers:
            with self.subTest(number=number):
                result = normalize_phone_number(number)
                self.assertIsNone(result, f"Should reject domestic number: {number}")

    def test_invalid_formats(self):
        """Test that invalid phone number formats are rejected."""
        invalid_formats = [
            "",                    # Empty string
            "+",                   # Just +
            "+abc",               # Non-digits after +
            "+123",               # Too few digits (3)
            "+1234567890123456",  # Too many digits (16)
            "123+4567890",        # + in middle (invalid)
            "abc123456789",       # Letters at start
            "+123 456 789a",      # Letter in number
        ]

        for invalid_number in invalid_formats:
            with self.subTest(invalid_number=invalid_number):
                result = normalize_phone_number(invalid_number)
                self.assertIsNone(result, f"Should reject invalid format: {invalid_number}")

    def test_multiple_plus_normalized(self):
        """Test that multiple leading + symbols are normalized to single +."""
        # Multiple + symbols should be normalized to single +
        result = normalize_phone_number("++1234567890")
        self.assertEqual(result, "+1234567890")

        result = normalize_phone_number("+++14155552671")
        self.assertEqual(result, "+14155552671")

    def test_whitespace_handling(self):
        """Test that whitespace around valid numbers is handled correctly."""
        # Leading/trailing whitespace should be stripped
        result = normalize_phone_number("  +14155552671  ")
        self.assertEqual(result, "+14155552671")

    def test_none_input(self):
        """Test that None input returns None."""
        result = normalize_phone_number(None)
        self.assertIsNone(result)

    def test_edge_cases(self):
        """Test various edge cases."""
        edge_cases = [
            ("+", None),           # Just +
            ("+1", None),          # + with 1 digit
            ("+12", None),         # + with 2 digits
            ("+123", None),        # + with 3 digits
            ("+1234", None),       # + with 4 digits
            ("+12345", None),      # + with 5 digits
            ("+123456", None),     # + with 6 digits
            ("+1234567", None),    # + with 7 digits (too few)
            ("+1234567890123456", None),  # + with 16 digits (too many)
        ]

        for input_val, expected in edge_cases:
            with self.subTest(input_val=input_val):
                result = normalize_phone_number(input_val)
                self.assertEqual(result, expected, f"Failed for edge case: {input_val}")


if __name__ == '__main__':
    unittest.main()
