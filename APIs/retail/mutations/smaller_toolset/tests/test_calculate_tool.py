import unittest
from unittest.mock import patch
from retail.mutations.smaller_toolset.calculate_tool import evaluate_expression

class TestCalculateTool(unittest.TestCase):

    @patch('retail.mutations.smaller_toolset.calculate_tool.calculate')
    def test_evaluate_expression(self, mock_calculate):
        mock_calculate.return_value = 4
        result = evaluate_expression(expression="2 + 2")
        mock_calculate.assert_called_once_with(expression="2 + 2")
        self.assertEqual(result, {"result": 4})

    @patch('retail.mutations.smaller_toolset.calculate_tool.calculate')
    def test_evaluate_expression_error(self, mock_calculate):
        mock_calculate.side_effect = Exception("Invalid expression")
        with self.assertRaises(Exception) as context:
            evaluate_expression(expression="2 + 2")
        self.assertEqual(str(context.exception), "Invalid expression")


