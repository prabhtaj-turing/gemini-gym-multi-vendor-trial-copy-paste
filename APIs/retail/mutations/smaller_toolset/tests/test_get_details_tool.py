import unittest
from unittest.mock import patch
from retail.mutations.smaller_toolset.get_details_tool import get_details

class TestGetDetailsTool(unittest.TestCase):

    @patch('retail.mutations.smaller_toolset.get_details_tool.get_order_details')
    def test_get_order_details(self, mock_get_order):
        mock_get_order.return_value = {"order_id": "123", "status": "pending"}
        result = get_details(order_id="123")
        mock_get_order.assert_called_once_with(order_id="123")
        self.assertEqual(result, {"order_id": "123", "status": "pending"})

    @patch('retail.mutations.smaller_toolset.get_details_tool.get_product_details')
    def test_get_product_details(self, mock_get_product):
        mock_get_product.return_value = {"product_id": "prod_123", "name": "Test Product"}
        result = get_details(product_id="prod_123")
        mock_get_product.assert_called_once_with(product_id="prod_123")
        self.assertEqual(result, {"product_id": "prod_123", "name": "Test Product"})

    @patch('retail.mutations.smaller_toolset.get_details_tool.get_user_details')
    def test_get_user_details(self, mock_get_user):
        mock_get_user.return_value = {"user_id": "user_123", "name": "Test User"}
        result = get_details(user_id="user_123")
        mock_get_user.assert_called_once_with(user_id="user_123")
        self.assertEqual(result, {"user_id": "user_123", "name": "Test User"})

    @patch('retail.mutations.smaller_toolset.get_details_tool.list_all_product_types')
    def test_list_product_types(self, mock_list_types):
        mock_list_types.return_value = {"product_types": ["electronics", "clothing"]}
        result = get_details(list_product_types=True)
        mock_list_types.assert_called_once()
        self.assertEqual(result, {"product_types": ["electronics", "clothing"]})

    def test_no_action(self):
        with self.assertRaisesRegex(ValueError, "No action specified."):
            get_details()

    def test_multiple_actions(self):
        with self.assertRaisesRegex(ValueError, "Only one type of detail can be requested at a time."):
            get_details(order_id="123", product_id="prod_123")

    @patch('retail.mutations.smaller_toolset.get_details_tool.get_order_details')
    def test_get_order_details_error(self, mock_get_order):
        mock_get_order.side_effect = Exception("Invalid order_id")
        with self.assertRaises(Exception) as context:
            get_details(order_id="123")
        self.assertEqual(str(context.exception), "Invalid order_id")

    @patch('retail.mutations.smaller_toolset.get_details_tool.get_product_details')
    def test_get_product_details_error(self, mock_get_product):
        mock_get_product.side_effect = Exception("Invalid product_id")
        with self.assertRaises(Exception) as context:
            get_details(product_id="prod_123")
        self.assertEqual(str(context.exception), "Invalid product_id")

    @patch('retail.mutations.smaller_toolset.get_details_tool.get_user_details')
    def test_get_user_details_error(self, mock_get_user):
        mock_get_user.side_effect = Exception("Invalid user_id")
        with self.assertRaises(Exception) as context:
            get_details(user_id="user_123")
        self.assertEqual(str(context.exception), "Invalid user_id")

    @patch('retail.mutations.smaller_toolset.get_details_tool.list_all_product_types')
    def test_list_product_types_error(self, mock_list_types):
        mock_list_types.side_effect = Exception("API error")
        with self.assertRaises(Exception) as context:
            get_details(list_product_types=True)
        self.assertEqual(str(context.exception), "API error")


