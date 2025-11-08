import unittest
from pydantic import ValidationError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.utils import reset_db
from ..SimulationEngine.db import DB
from .. import create_label

class TestCreateLabelValidation(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset test state before each test."""
        reset_db()
        # Set up test users
        DB["users"]["test_user@example.com"] = {
            "labels": {},
            "profile": {
                "emailAddress": "test_user@example.com",
                "messagesTotal": 0,
                "threadsTotal": 0,
                "historyId": "1"
            },
            "drafts": {},
            "messages": {},
            "threads": {},
            "settings": {
                "imap": {"enabled": False},
                "pop": {"accessWindow": "disabled"},
                "vacation": {"enableAutoReply": False},
                "language": {"displayLanguage": "en"},
                "autoForwarding": {"enabled": False},
                "sendAs": {}
            },
            "history": [],
            "watch": {}
        }

    def test_valid_input_minimal(self):
        """Test creating a label with minimal valid input (only userId)."""
        result = create_label(userId="me")
        self.assertIsInstance(result, dict)
        self.assertIn("id", result)
        # Don't check for specific ID since counter has advanced due to existing labels
        self.assertTrue(result["id"].startswith("Label_"))
        # The name should match the generated ID
        self.assertEqual(result["name"], result["id"]) # Default name matches ID
        self.assertEqual(result["messageListVisibility"], "show") # Default
        self.assertEqual(result["labelListVisibility"], "labelShow") # Default
        self.assertEqual(result["type"], "user") # Default
        self.assertEqual(result["color"], {}) # Default color handling

    def test_valid_input_with_label_name(self):
        """Test creating a label with a specified name."""
        label_data = {"name": "MyWork"}
        result = create_label(userId="test_user@example.com", label=label_data)
        self.assertEqual(result["name"], "MyWork")
        # Don't check for specific ID since counter has advanced due to existing labels
        self.assertTrue(result["id"].startswith("Label_"))

    def test_valid_input_all_fields(self):
        """Test creating a label with all valid fields provided."""
        label_data = {
            "name": "Urgent",
            "messageListVisibility": "hide",
            "labelListVisibility": "labelHide",
            "type": "user",
            "color": {"textColor": "#FFFFFF", "backgroundColor": "#FF0000"}
        }
        result = create_label(userId="me", label=label_data)
        self.assertEqual(result["name"], "Urgent")
        self.assertEqual(result["messageListVisibility"], "hide")
        self.assertEqual(result["labelListVisibility"], "labelHide")
        self.assertEqual(result["type"], "user")
        self.assertEqual(result["color"], {"textColor": "#FFFFFF", "backgroundColor": "#FF0000"})

    def test_valid_input_color_explicitly_null(self):
        """Test creating a label with 'color': null returns empty dict."""
        label_data = {"name": "NoColorLabel", "color": None}
        result = create_label(userId="me", label=label_data)
        self.assertEqual(result["name"], "NoColorLabel")
        self.assertEqual(result["color"], {})

    def test_invalid_userid_type(self):
        """Test that invalid userId type raises TypeError."""
        self.assert_error_behavior(
            func_to_call=create_label,
            expected_exception_type=TypeError,
            expected_message="userId must be a string.",
            userId=123,
            label=None
        )

    def test_non_existent_userid(self):
        """Test that a non-existent userId raises ValueError."""
        self.assert_error_behavior(
            func_to_call=create_label,
            expected_exception_type=ValueError,
            expected_message="User 'non_existent_user' does not exist.",
            userId="non_existent_user",
            label=None
        )

    def test_label_name_invalid_type(self):
        """Test label with 'name' of invalid type."""
        invalid_label = {"name": 12345}
        self.assert_error_behavior(
            func_to_call=create_label,
            expected_exception_type=ValidationError,
            expected_message='1 validation error for LabelInputModel\nname\n  Input should be a valid string [type=string_type, input_value=12345, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type',
            userId="me",
            label=invalid_label
        )

    def test_label_message_list_visibility_invalid_value(self):
        """Test label with invalid 'messageListVisibility' value."""
        invalid_label = {"messageListVisibility": "invalid_option"}
        self.assert_error_behavior(
            func_to_call=create_label,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for LabelInputModel\nmessageListVisibility\n  Input should be 'show' or 'hide' [type=literal_error, input_value='invalid_option', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/literal_error",
            userId="me",
            label=invalid_label
        )

    def test_label_list_visibility_invalid_value(self):
        """Test label with invalid 'labelListVisibility' value."""
        invalid_label = {"labelListVisibility": "invalid_option"}
        self.assert_error_behavior(
            func_to_call=create_label,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for LabelInputModel\nlabelListVisibility\n  Input should be 'labelShow', 'labelShowIfUnread' or 'labelHide' [type=literal_error, input_value='invalid_option', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/literal_error",
            userId="me",
            label=invalid_label
        )

    def test_label_type_invalid_value(self):
        """Test label with invalid 'type' value - only 'user' is allowed for creation."""
        invalid_label = {"type": "admin_only"}
        self.assert_error_behavior(
            func_to_call=create_label,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for LabelInputModel\ntype\n  Input should be 'user' [type=literal_error, input_value='admin_only', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/literal_error",
            userId="me",
            label=invalid_label
        )

    def test_label_color_not_a_dict(self):
        """Test label with 'color' being a non-dictionary type."""
        invalid_label = {"color": "not-a-dictionary"}
        self.assert_error_behavior(
            func_to_call=create_label,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for LabelInputModel\ncolor\n  Input should be a valid dictionary or instance of ColorInputModel [type=model_type, input_value='not-a-dictionary', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/model_type",
            userId="me",
            label=invalid_label
        )

    def test_label_color_missing_textcolor(self):
        """Test label 'color' dict missing 'textColor' key."""
        invalid_label = {"color": {"backgroundColor": "#FF0000"}}
        self.assert_error_behavior(
            func_to_call=create_label,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for LabelInputModel\ncolor.textColor\n  Field required [type=missing, input_value={'backgroundColor': '#FF0000'}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.11/v/missing",
            userId="me",
            label=invalid_label
        )

    def test_label_color_missing_backgroundcolor(self):
        """Test label 'color' dict missing 'backgroundColor' key."""
        invalid_label = {"color": {"textColor": "#FFFFFF"}}
        self.assert_error_behavior(
            func_to_call=create_label,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for LabelInputModel\ncolor.backgroundColor\n  Field required [type=missing, input_value={'textColor': '#FFFFFF'}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.11/v/missing",
            userId="me",
            label=invalid_label
        )

    def test_label_color_backgroundcolor_invalid_format(self):
        """Test label 'color' with 'backgroundColor' in invalid hex format."""
        invalid_label = {"color": {"textColor": "#FFFFFF", "backgroundColor": "invalid_hex"}}
        self.assert_error_behavior(
            func_to_call=create_label,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for LabelInputModel\ncolor.backgroundColor\n  String should match pattern '^#[0-9a-fA-F]{6}$' [type=string_pattern_mismatch, input_value='invalid_hex', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_pattern_mismatch",
            userId="me",
            label=invalid_label
        )

    def test_label_color_textcolor_invalid_type(self):
        """Test label 'color' with 'textColor' of invalid type."""
        invalid_label = {"color": {"textColor": 123, "backgroundColor": "#FF0000"}}
        self.assert_error_behavior(
            func_to_call=create_label,
            expected_exception_type=ValidationError,
            expected_message='1 validation error for LabelInputModel\ncolor.textColor\n  Input should be a valid string [type=string_type, input_value=123, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type',
            userId="me",
            label=invalid_label
        )

if __name__ == "__main__":
    unittest.main()
