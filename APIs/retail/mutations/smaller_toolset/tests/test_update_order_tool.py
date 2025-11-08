import unittest
from unittest.mock import patch, MagicMock

from retail.mutations.smaller_toolset.update_order_tool import update_order

class TestUpdateOrderTool(unittest.TestCase):

    @patch('retail.mutations.smaller_toolset.update_order_tool.cancel_pending_order')
    def test_cancel_order(self, mock_cancel):
        mock_cancel.return_value = {"message": "Order #12345 has been canceled."}
        result = update_order(order_id="12345", cancel=True)
        mock_cancel.assert_called_once_with(order_id="12345")
        self.assertEqual(result, {"message": "Order #12345 has been canceled."})

    @patch('retail.mutations.smaller_toolset.update_order_tool.modify_pending_order_address')
    def test_modify_address(self, mock_modify_address):
        updated_order = {"order_id": "12345", "shipping_address": {"address_id": "addr_new"}}
        mock_modify_address.return_value = updated_order
        result = update_order(order_id="12345", new_address_id="addr_new")
        mock_modify_address.assert_called_once_with(order_id="12345", new_address_id="addr_new")
        self.assertEqual(result, {"order": updated_order})

    @patch('retail.mutations.smaller_toolset.update_order_tool.modify_pending_order_items')
    def test_modify_items(self, mock_modify_items):
        updated_order = {"order_id": "12345", "items": []}
        mock_modify_items.return_value = updated_order
        items_to_add = [{"product_id": "prod1", "quantity": 1}]
        items_to_remove = ["item1"]
        result = update_order(order_id="12345", items_to_add=items_to_add, items_to_remove=items_to_remove)
        mock_modify_items.assert_called_once_with(order_id="12345", items_to_add=items_to_add, items_to_remove=items_to_remove)
        self.assertEqual(result, {"order": updated_order})

    @patch('retail.mutations.smaller_toolset.update_order_tool.modify_pending_order_payment')
    def test_modify_payment(self, mock_modify_payment):
        updated_order = {"order_id": "12345", "payment_history": [{"payment_method_id": "payment_new"}]}
        mock_modify_payment.return_value = updated_order
        result = update_order(order_id="12345", new_payment_method_id="payment_new")
        mock_modify_payment.assert_called_once_with(order_id="12345", payment_method_id="payment_new")
        self.assertEqual(result, {"order": updated_order})

    @patch('retail.mutations.smaller_toolset.update_order_tool.return_delivered_order_items')
    def test_return_items(self, mock_return_items):
        return_details = {"order_id": "12345", "return_id": "return1"}
        mock_return_items.return_value = return_details
        items_to_return = [{"item_id": "item1", "quantity": 1}]
        result = update_order(order_id="12345", items_to_return=items_to_return)
        mock_return_items.assert_called_once_with(order_id="12345", items=items_to_return)
        self.assertEqual(result, return_details)

    @patch('retail.mutations.smaller_toolset.update_order_tool.exchange_delivered_order_items')
    def test_exchange_items(self, mock_exchange_items):
        exchange_details = {"order_id": "12345", "exchange_id": "exchange1"}
        mock_exchange_items.return_value = exchange_details
        items_to_exchange = [{"item_id": "item1", "new_product_id": "prod_new", "quantity": 1}]
        result = update_order(order_id="12345", items_to_exchange=items_to_exchange)
        mock_exchange_items.assert_called_once_with(order_id="12345", items_to_exchange=items_to_exchange)
        self.assertEqual(result, exchange_details)

    def test_no_action(self):
        with self.assertRaisesRegex(ValueError, "No update action specified."):
            update_order(order_id="12345")

    def test_multiple_actions(self):
        with self.assertRaisesRegex(ValueError, "Only one type of update action can be specified at a time."):
            update_order(order_id="12345", cancel=True, new_address_id="addr_new")

    @patch('retail.mutations.smaller_toolset.update_order_tool.cancel_pending_order')
    def test_cancel_order_error(self, mock_cancel):
        mock_cancel.side_effect = Exception("Invalid order_id")
        with self.assertRaises(Exception) as context:
            update_order(order_id="12345", cancel=True)
        self.assertEqual(str(context.exception), "Invalid order_id")

    

