import unittest
from unittest.mock import patch
from retail.mutations.smaller_toolset.find_user_tool import find_user

class TestFindUserTool(unittest.TestCase):

    @patch('retail.mutations.smaller_toolset.find_user_tool.find_user_id_by_email')
    def test_find_user_by_email(self, mock_find_by_email):
        mock_find_by_email.return_value = {"user_id": "user_123"}
        result = find_user(email="test@example.com")
        mock_find_by_email.assert_called_once_with(email="test@example.com")
        self.assertEqual(result, {"user_id": "user_123"})

    @patch('retail.mutations.smaller_toolset.find_user_tool.find_user_id_by_name_zip')
    def test_find_user_by_name_zip(self, mock_find_by_name_zip):
        mock_find_by_name_zip.return_value = {"user_id": "user_456"}
        result = find_user(user_name="Test User", zip_code="12345")
        mock_find_by_name_zip.assert_called_once_with(user_name="Test User", zip_code="12345")
        self.assertEqual(result, {"user_id": "user_456"})

    def test_no_parameters(self):
        with self.assertRaisesRegex(ValueError, "Either email or both user_name and zip_code must be provided."):
            find_user()

    def test_missing_zip_code(self):
        with self.assertRaisesRegex(ValueError, "Either email or both user_name and zip_code must be provided."):
            find_user(user_name="Test User")

    @patch('retail.mutations.smaller_toolset.find_user_tool.find_user_id_by_email')
    def test_find_user_by_email_error(self, mock_find_by_email):
        mock_find_by_email.side_effect = Exception("Invalid email")
        with self.assertRaises(Exception) as context:
            find_user(email="test@example.com")
        self.assertEqual(str(context.exception), "Invalid email")

    @patch('retail.mutations.smaller_toolset.find_user_tool.find_user_id_by_name_zip')
    def test_find_user_by_name_zip_error(self, mock_find_by_name_zip):
        mock_find_by_name_zip.side_effect = Exception("Invalid user_name or zip_code")
        with self.assertRaises(Exception) as context:
            find_user(user_name="Test User", zip_code="12345")
        self.assertEqual(str(context.exception), "Invalid user_name or zip_code")


