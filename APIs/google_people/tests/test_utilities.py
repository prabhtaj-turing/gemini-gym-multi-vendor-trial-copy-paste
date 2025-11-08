"""
Test cases for utility functions in Google People API.

This module tests all utility functions in the SimulationEngine/utils.py module
to ensure they work correctly and handle edge cases properly.
"""

import unittest
import uuid
from typing import Dict, Any, List

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.utils import generate_id, validate_required_fields


class TestUtilities(BaseTestCaseWithErrorHandler):
    """Test class for utility functions."""

    def test_generate_id_returns_string(self):
        """Test that generate_id returns a string."""
        generated_id = generate_id()
        self.assertIsInstance(generated_id, str)
        self.assertGreater(len(generated_id), 0)

    def test_generate_id_returns_valid_uuid(self):
        """Test that generate_id returns a valid UUID format."""
        generated_id = generate_id()
        
        # Try to parse it as a UUID to verify format
        try:
            uuid_obj = uuid.UUID(generated_id)
            self.assertIsInstance(uuid_obj, uuid.UUID)
        except ValueError:
            self.fail(f"Generated ID '{generated_id}' is not a valid UUID format")

    def test_generate_id_uniqueness(self):
        """Test that generate_id returns unique values."""
        ids = set()
        num_ids = 1000
        
        for _ in range(num_ids):
            new_id = generate_id()
            self.assertNotIn(new_id, ids, "Generated ID is not unique")
            ids.add(new_id)
        
        self.assertEqual(len(ids), num_ids, "Not all generated IDs were unique")

    def test_generate_id_consistency(self):
        """Test that generate_id consistently returns UUID format."""
        for _ in range(100):
            generated_id = generate_id()
            # UUID4 format: 8-4-4-4-12 characters (with hyphens)
            parts = generated_id.split('-')
            self.assertEqual(len(parts), 5, f"UUID format incorrect: {generated_id}")
            self.assertEqual(len(parts[0]), 8, f"First part length incorrect: {generated_id}")
            self.assertEqual(len(parts[1]), 4, f"Second part length incorrect: {generated_id}")
            self.assertEqual(len(parts[2]), 4, f"Third part length incorrect: {generated_id}")
            self.assertEqual(len(parts[3]), 4, f"Fourth part length incorrect: {generated_id}")
            self.assertEqual(len(parts[4]), 12, f"Fifth part length incorrect: {generated_id}")

    def test_validate_required_fields_success(self):
        """Test validate_required_fields with valid data."""
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1-555-123-4567"
        }
        required_fields = ["name", "email"]
        
        # Should not raise any exception
        try:
            validate_required_fields(data, required_fields)
        except Exception as e:
            self.fail(f"validate_required_fields raised exception with valid data: {e}")

    def test_validate_required_fields_missing_field(self):
        """Test validate_required_fields with missing required field."""
        data = {
            "name": "John Doe",
            "phone": "+1-555-123-4567"
        }
        required_fields = ["name", "email"]
        
        with self.assertRaises(ValueError) as context:
            validate_required_fields(data, required_fields)
        
        error_message = str(context.exception)
        self.assertIn("Missing required fields", error_message)
        self.assertIn("email", error_message)

    def test_validate_required_fields_multiple_missing(self):
        """Test validate_required_fields with multiple missing fields."""
        data = {
            "phone": "+1-555-123-4567"
        }
        required_fields = ["name", "email", "address"]
        
        with self.assertRaises(ValueError) as context:
            validate_required_fields(data, required_fields)
        
        error_message = str(context.exception)
        self.assertIn("Missing required fields", error_message)
        self.assertIn("name", error_message)
        self.assertIn("email", error_message)
        self.assertIn("address", error_message)

    def test_validate_required_fields_none_value(self):
        """Test validate_required_fields with None values."""
        data = {
            "name": "John Doe",
            "email": None,
            "phone": "+1-555-123-4567"
        }
        required_fields = ["name", "email"]
        
        with self.assertRaises(ValueError) as context:
            validate_required_fields(data, required_fields)
        
        error_message = str(context.exception)
        self.assertIn("Missing required fields", error_message)
        self.assertIn("email", error_message)

    def test_validate_required_fields_empty_string(self):
        """Test validate_required_fields with empty string values."""
        data = {
            "name": "John Doe",
            "email": "",  # Empty string should be considered valid
            "phone": "+1-555-123-4567"
        }
        required_fields = ["name", "email"]
        
        # Should not raise exception as empty string is a valid value
        try:
            validate_required_fields(data, required_fields)
        except Exception as e:
            self.fail(f"validate_required_fields raised exception with empty string: {e}")

    def test_validate_required_fields_empty_list(self):
        """Test validate_required_fields with empty required fields list."""
        data = {
            "name": "John Doe",
            "email": "john@example.com"
        }
        required_fields = []
        
        # Should not raise any exception
        try:
            validate_required_fields(data, required_fields)
        except Exception as e:
            self.fail(f"validate_required_fields raised exception with empty required fields: {e}")

    def test_validate_required_fields_empty_data(self):
        """Test validate_required_fields with empty data dict."""
        data = {}
        required_fields = ["name", "email"]
        
        with self.assertRaises(ValueError) as context:
            validate_required_fields(data, required_fields)
        
        error_message = str(context.exception)
        self.assertIn("Missing required fields", error_message)
        self.assertIn("name", error_message)
        self.assertIn("email", error_message)

    def test_validate_required_fields_nested_fields(self):
        """Test validate_required_fields with nested data structures."""
        data = {
            "user": {
                "name": "John Doe",
                "email": "john@example.com"
            },
            "metadata": {
                "created": "2023-01-01"
            }
        }
        required_fields = ["user", "metadata"]
        
        # Should not raise exception as top-level fields exist
        try:
            validate_required_fields(data, required_fields)
        except Exception as e:
            self.fail(f"validate_required_fields raised exception with nested data: {e}")

    def test_validate_required_fields_case_sensitivity(self):
        """Test validate_required_fields case sensitivity."""
        data = {
            "Name": "John Doe",
            "EMAIL": "john@example.com"
        }
        required_fields = ["name", "email"]
        
        # Should raise exception as field names are case-sensitive
        with self.assertRaises(ValueError) as context:
            validate_required_fields(data, required_fields)
        
        error_message = str(context.exception)
        self.assertIn("Missing required fields", error_message)

    def test_validate_required_fields_data_types(self):
        """Test validate_required_fields with various data types."""
        data = {
            "string_field": "test",
            "int_field": 42,
            "float_field": 3.14,
            "bool_field": True,
            "list_field": [1, 2, 3],
            "dict_field": {"key": "value"},
            "none_field": None
        }
        required_fields = ["string_field", "int_field", "float_field", "bool_field", "list_field", "dict_field"]
        
        # Should not raise exception for various valid data types
        try:
            validate_required_fields(data, required_fields)
        except Exception as e:
            self.fail(f"validate_required_fields raised exception with various data types: {e}")

    def test_validate_required_fields_zero_values(self):
        """Test validate_required_fields with zero values."""
        data = {
            "count": 0,
            "score": 0.0,
            "enabled": False,
            "items": []
        }
        required_fields = ["count", "score", "enabled", "items"]
        
        # Zero values should be considered valid
        try:
            validate_required_fields(data, required_fields)
        except Exception as e:
            self.fail(f"validate_required_fields raised exception with zero values: {e}")

    def test_validate_required_fields_error_message_format(self):
        """Test validate_required_fields error message format."""
        data = {
            "field1": "value1"
        }
        required_fields = ["field2", "field3", "field4"]
        
        with self.assertRaises(ValueError) as context:
            validate_required_fields(data, required_fields)
        
        error_message = str(context.exception)
        self.assertTrue(error_message.startswith("Missing required fields:"))
        
        # Check that all missing fields are mentioned
        for field in required_fields:
            self.assertIn(field, error_message)

    def test_validate_required_fields_with_special_characters(self):
        """Test validate_required_fields with special characters in field names."""
        data = {
            "field-with-dashes": "value1",
            "field_with_underscores": "value2",
            "field.with.dots": "value3",
            "field with spaces": "value4"
        }
        required_fields = ["field-with-dashes", "field_with_underscores", "field.with.dots", "field with spaces"]
        
        # Should handle special characters in field names
        try:
            validate_required_fields(data, required_fields)
        except Exception as e:
            self.fail(f"validate_required_fields raised exception with special characters: {e}")


if __name__ == '__main__':
    unittest.main()
