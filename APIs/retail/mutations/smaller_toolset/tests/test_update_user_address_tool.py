import unittest
from unittest.mock import patch
from retail.mutations.smaller_toolset.update_user_address_tool import update_user_address

class TestUpdateUserAddressTool(unittest.TestCase):

    @patch('retail.mutations.smaller_toolset.update_user_address_tool.modify_user_address')
    def test_update_user_address(self, mock_modify_address):
        mock_modify_address.return_value = {"user_id": "user_123", "address": "new_address"}
        result = update_user_address(user_id="user_123", address1="123 Main St", address2="", city="Anytown", state="CA", country="USA", zip_code="12345")
        mock_modify_address.assert_called_once_with(user_id="user_123", address1="123 Main St", address2="", city="Anytown", state="CA", country="USA", zip_code="12345")
        self.assertEqual(result, {"user_id": "user_123", "address": "new_address"})

    @patch('retail.mutations.smaller_toolset.update_user_address_tool.modify_user_address')
    def test_update_user_address_error(self, mock_modify_address):
        mock_modify_address.side_effect = Exception("Invalid user_id")
        with self.assertRaises(Exception) as context:
            update_user_address(user_id="user_123", address1="123 Main St", address2="", city="Anytown", state="CA", country="USA", zip_code="12345")
        self.assertEqual(str(context.exception), "Invalid user_id")


