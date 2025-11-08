"""
Test suite for calculate tool.
"""
import unittest
from .airline_base_exception import AirlineBaseTestCase
from .. import calculate
from ..SimulationEngine.custom_errors import InvalidExpressionError, ValidationError

class TestCalculate(AirlineBaseTestCase):

    def test_calculate_addition(self):
        """Test simple addition."""
        result = calculate(expression="2 + 2")
        self.assertEqual(result, "4.0")

    def test_calculate_subtraction(self):
        """Test simple subtraction."""
        result = calculate(expression="10 - 5.5")
        self.assertEqual(result, "4.5")

    def test_calculate_multiplication(self):
        """Test simple multiplication."""
        result = calculate(expression="3 * 7")
        self.assertEqual(result, "21.0")

    def test_calculate_division(self):
        """Test simple division."""
        result = calculate(expression="10 / 4")
        self.assertEqual(result, "2.5")

    def test_calculate_complex_expression(self):
        """Test a more complex expression with parentheses."""
        result = calculate(expression="(5 + 5) * 2 - 10 / 2")
        self.assertEqual(result, "15.0")
        
    def test_calculate_rounding(self):
        """Test that the result is rounded to 2 decimal places."""
        result = calculate(expression="10 / 3")
        self.assertEqual(result, "3.33")

    def test_calculate_invalid_characters(self):
        """Test that calculate raises an error for an expression with invalid characters."""
        self.assert_error_behavior(
            calculate,
            InvalidExpressionError,
            "Expression contains invalid characters.",
            None,
            expression="2 + a"
        )

    def test_calculate_empty_expression(self):
        """Test that calculate raises an error for an empty expression."""
        self.assert_error_behavior(
            calculate,
            ValidationError,
            "Expression must be a non-empty string.",
            None,
            expression=""
        )
        
    def test_calculate_whitespace_expression(self):
        """Test that calculate raises an error for a whitespace-only expression."""
        self.assert_error_behavior(
            calculate,
            ValidationError,
            "Expression must be a non-empty string.",
            None,
            expression=" "
        )
        
    def test_calculate_division_by_zero(self):
        """Test that calculate handles division by zero."""
        self.assert_error_behavior(
            calculate,
            ValueError,
            "Error evaluating expression: division by zero",
            None,
            expression="10 / 0"
        )

if __name__ == '__main__':
    unittest.main()
