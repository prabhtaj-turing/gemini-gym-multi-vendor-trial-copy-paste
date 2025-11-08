from typing import Dict, Any
from unittest.mock import patch

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import custom_errors
from .. import invite_admin_user 
DB: Dict[str, Any] = {}
from .. import invite_admin_user
DB: Dict[str, Any] = {}

class TestInviteAdminUser(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """Reset test state before each test."""
        global DB  # Use the same DB instance as the function
        DB.clear()
        DB["users"] = {}
        DB["channels"] = {
            "C123": {"name": "general", "conversations": {"members": []}},
            "C456": {"name": "random", "conversations": {"members": []}}
        }

    @patch("slack.AdminUsers.DB", new_callable=lambda: DB)
    def test_valid_invitation(self, mock_db):
        """Test a successful user invitation with minimal valid inputs."""
        result = invite_admin_user(email="test@example.com")
        self.assertTrue(result["ok"])
        self.assertIn("user", result)
        self.assertEqual(result["user"]["profile"]["email"], "test@example.com")
        self.assertIn(result["user"]["id"], DB["users"])
        import base64
        try:
            base64.b64decode(result["user"]["profile"]["image"])
        except Exception:
            self.fail("Profile image should be valid base64 encoded string")

    @patch("slack.AdminUsers.DB", new_callable=lambda: DB)
    def test_valid_invitation_with_all_optional_params(self, mock_db):
        """Test successful invitation with all optional parameters provided."""
        result = invite_admin_user(
            email="full@example.com",
            channel_ids="C123,C456",
            real_name="Full Name",
            team_id="T001"
        )
        self.assertTrue(result["ok"])
        user = result["user"]
        self.assertEqual(user["profile"]["email"], "full@example.com")
        self.assertEqual(user["real_name"], "Full Name")
        self.assertEqual(user["team_id"], "T001")
        self.assertIn(user["id"], DB["users"])
        self.assertIn(user["id"], DB["channels"]["C123"]["conversations"]["members"])
        self.assertIn(user["id"], DB["channels"]["C456"]["conversations"]["members"])
        import base64
        try:
            base64.b64decode(result["user"]["profile"]["image"])
        except Exception:
            self.fail("Profile image should be valid base64 encoded string")

    @patch("slack.AdminUsers.DB", new_callable=lambda: DB)
    def test_email_already_invited(self, mock_db):
        """Test invitation for an email that already exists."""
        DB["users"]["UEXISTING"] = {
            "id": "UEXISTING",
            "profile": {"email": "existing@example.com"}
        }
        self.assert_error_behavior(
            invite_admin_user, custom_errors.UserAlreadyInvitedError, "User with existing@example.com is already invited",
            email="existing@example.com"
        )

    # --- Email Validation Tests ---
    def test_invalid_email_type(self):
        """Test TypeError for non-string email."""
        self.assert_error_behavior(
            invite_admin_user, TypeError, "email must be a string.",
            email=123
        )

    def test_empty_email(self):
        """Test ValueError for empty email string."""
        self.assert_error_behavior(
            invite_admin_user, ValueError, "email cannot be empty.",
            email=""
        )

    def test_invalid_email_format_no_at_sign(self):
        """Test ValueError for email missing '@'."""
        self.assert_error_behavior(
            invite_admin_user, ValueError, "email format is invalid (An email address must have an @-sign)",
            email="testexample.com"
        )

    def test_invalid_email_format_no_domain(self):
        """Test ValueError for email missing domain."""
        self.assert_error_behavior(
            invite_admin_user, ValueError, "email format is invalid (There must be something after the @-sign)",
            email="test@"
        )

    def test_invalid_email_format_no_domain_dot(self):
        """Test ValueError for email domain missing '.'."""
        self.assert_error_behavior(
            invite_admin_user, ValueError, "email format is invalid (The part after the @-sign is not valid. It should have a period)",
            email="test@examplecom"
        )

    def test_invalid_email_format_empty_local_part(self):
        """Test ValueError for email with empty local part."""
        self.assert_error_behavior(
            invite_admin_user, ValueError, "email format is invalid (There must be something before the @-sign)",
            email="@example.com"
        )

    # --- Channel IDs Validation Tests ---
    def test_invalid_channel_ids_type(self):
        """Test TypeError for non-string channel_ids."""
        self.assert_error_behavior(
            invite_admin_user, TypeError, "channel_ids must be a string if provided.",
            email="valid@example.com", channel_ids=123
        )

    def test_valid_none_channel_ids(self):
        """Test that None channel_ids is accepted."""
        result = invite_admin_user(email="nonechannels@example.com", channel_ids=None)
        self.assertTrue(result["ok"])
        self.assertNotIn("members", DB["channels"]["C123"])  # Or check members list is empty if initialized

    # --- Real Name Validation Tests ---
    def test_invalid_real_name_type(self):
        """Test TypeError for non-string real_name."""
        self.assert_error_behavior(
            invite_admin_user, TypeError, "real_name must be a string if provided.",
            email="valid@example.com", real_name=123
        )

    def test_valid_none_real_name(self):
        """Test that None real_name is accepted and name is derived from email."""
        result = invite_admin_user(email="nonerealname@example.com", real_name=None)
        self.assertTrue(result["ok"])
        self.assertEqual(result["user"]["real_name"], "Nonerealname")  # Capitalized email part

    # --- Team ID Validation Tests ---
    def test_invalid_team_id_type(self):
        """Test TypeError for non-string team_id."""
        self.assert_error_behavior(
            invite_admin_user, TypeError, "team_id must be a string if provided.",
            email="valid@example.com", team_id=123
        )

    def test_valid_none_team_id(self):
        """Test that None team_id is accepted."""
        result = invite_admin_user(email="noneteam@example.com", team_id=None)
        self.assertTrue(result["ok"])
        self.assertIsNone(result["user"]["team_id"])

    @patch("slack.AdminUsers.DB", new_callable=lambda: DB)
    def test_invitation_to_non_existent_channel(self, mock_db):
        """Test invitation where channel_ids includes a non-existent channel."""
        result = invite_admin_user(email="newchanneluser@example.com", channel_ids="C_NON_EXISTENT")
        self.assertTrue(result["ok"])
        user_id = result["user"]["id"]
        # The core logic, as modified, should create the channel
        self.assertIn("C_NON_EXISTENT", DB["channels"])
        self.assertIn(user_id, DB["channels"]["C_NON_EXISTENT"]["conversations"]["members"])

    @patch("slack.AdminUsers.DB", new_callable=lambda: DB)
    def test_invitation_to_multiple_channels_some_exist_some_not(self, mock_db):
        """Test invitation to existing and non-existing channels."""
        result = invite_admin_user(email="mixedchannels@example.com", channel_ids="C123,C_NEW_CHANNEL")
        self.assertTrue(result["ok"])
        user_id = result["user"]["id"]
        self.assertIn(user_id, DB["channels"]["C123"]["conversations"]["members"])
        self.assertIn("C_NEW_CHANNEL", DB["channels"])
        self.assertIn(user_id, DB["channels"]["C_NEW_CHANNEL"]["conversations"]["members"])

    @patch("slack.AdminUsers.DB", new_callable=lambda: DB)
    def test_invitation_to_already_invited_user_duplicate_call(self, mock_db):
        """Test that inviting the same user twice raises UserAlreadyInvitedError."""
        # First invitation should succeed
        result = invite_admin_user(email="duplicate@example.com", channel_ids="C123")
        self.assertTrue(result["ok"])
        
        # Second invitation should raise error
        self.assert_error_behavior(
            invite_admin_user, custom_errors.UserAlreadyInvitedError, "User with duplicate@example.com is already invited",
            email="duplicate@example.com"
        )