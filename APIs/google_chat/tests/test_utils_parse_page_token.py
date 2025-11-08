import unittest
import sys
import os

# Add the APIs directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from google_chat.SimulationEngine.utils import parse_page_token


class TestUtilsParsePageToken(unittest.TestCase):
    """Test suite for the centralized parse_page_token utility function."""
    
    def test_none_input(self):
        """Test that None input returns 0."""
        result = parse_page_token(None)
        self.assertEqual(result, 0)
        self.assertIsInstance(result, int)

    def test_empty_string_input(self):
        """Test that empty string input returns 0."""
        result = parse_page_token("")
        self.assertEqual(result, 0)
        self.assertIsInstance(result, int)

    def test_valid_positive_integer_string(self):
        """Test that valid positive integer strings are parsed correctly."""
        test_cases = [
            ("0", 0),
            ("1", 1),
            ("10", 10),
            ("100", 100),
            ("999", 999),
            ("+123", 123),  # Positive sign is allowed by Python's int()
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input=input_str):
                result = parse_page_token(input_str)
                self.assertEqual(result, expected)
                self.assertIsInstance(result, int)

    def test_negative_integer_string(self):
        """Test that negative integer strings are clamped to 0."""
        test_cases = [
            ("-1", 0),
            ("-10", 0),
            ("-100", 0),
        ]
        
        for input_str, expected in test_cases:
            with self.subTest(input=input_str):
                result = parse_page_token(input_str)
                self.assertEqual(result, expected)
                self.assertIsInstance(result, int)

    def test_invalid_string_input(self):
        """Test that invalid string inputs return 0."""
        test_cases = [
            "abc",
            "123abc", 
            "12.34",
            "12 34",
            "1e5",
            "infinity",
            "NaN",
        ]
        
        for input_str in test_cases:
            with self.subTest(input=input_str):
                result = parse_page_token(input_str)
                self.assertEqual(result, 0)
                self.assertIsInstance(result, int)

    def test_non_string_input_types(self):
        """Test that non-string input types return 0 due to explicit type checking."""
        test_cases = [
            123,        # int
            123.45,     # float
            True,       # bool
            [],         # list
            {},         # dict
        ]
        
        for input_val in test_cases:
            with self.subTest(input=input_val, type=type(input_val).__name__):
                result = parse_page_token(input_val)
                self.assertEqual(result, 0)
                self.assertIsInstance(result, int)

    def test_type_annotation_enforcement(self):
        """Test that the function properly enforces Optional[str] type annotation."""
        # The function should return 0 for non-string, non-None inputs
        result = parse_page_token(42)
        self.assertEqual(result, 0)
        
        # But valid strings should work
        result = parse_page_token("42")
        self.assertEqual(result, 42)

    def test_integration_with_pagination_flow(self):
        """Test realistic pagination scenarios."""
        # Simulate typical pagination flow
        scenarios = [
            (None, 0, "First page request"),
            ("0", 0, "Explicit first page"),  
            ("20", 20, "Second page"),
            ("40", 40, "Third page"),
            ("invalid", 0, "Invalid token fallback"),
        ]
        
        for token, expected, description in scenarios:
            with self.subTest(scenario=description, token=token):
                result = parse_page_token(token)
                self.assertEqual(result, expected)
                self.assertGreaterEqual(result, 0)


if __name__ == '__main__':
    unittest.main() 