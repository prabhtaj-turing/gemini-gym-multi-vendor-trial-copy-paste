import hashlib
from typing import Dict, Any  # Used by test method type hints
from unittest.mock import patch

from ..SimulationEngine.custom_errors import ChannelNameMissingError, ChannelNameTakenError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import create_channel

# This global DB is for the test environment.
# It simulates the DB the `create_channel` function expects to be in its scope.
DB: Dict[str, Any] = {"channels": {}}


class TestCreateChannelValidation(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset DB state before each test."""
        global DB
        DB["channels"] = {}
        # No specific random seed reset needed here as function's core logic seeds locally if needed.

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_valid_input_public_channel(self, mock_db):
        """Test creating a valid public channel."""
        result = create_channel(name="general", is_private=False, team_id="T123")
        self.assertTrue(result.get("ok"))
        self.assertIn("channel", result)
        channel = result["channel"]
        self.assertEqual(channel["name"], "general")
        self.assertFalse(channel["is_private"])
        self.assertEqual(channel["team_id"], "T123")
        self.assertIn(channel["id"], DB["channels"])

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_valid_input_private_channel_no_team_id(self, mock_db):
        """Test creating a valid private channel without a team ID."""
        result = create_channel(name="secret-project", is_private=True)
        self.assertTrue(result.get("ok"))
        channel = result["channel"]
        self.assertEqual(channel["name"], "secret-project")
        self.assertTrue(channel["is_private"])
        self.assertIsNone(channel["team_id"])
        self.assertIn(channel["id"], DB["channels"])

    def test_invalid_name_type(self):
        """Test that providing a non-string name raises TypeError."""
        self.assert_error_behavior(
            func_to_call=create_channel,
            expected_exception_type=TypeError,
            expected_message="Argument 'name' must be a string.",
            name=12345
        )

    def test_empty_name_raises_channel_name_missing_error(self):
        """Test that an empty string for name raises ChannelNameMissingError."""
        self.assert_error_behavior(
            func_to_call=create_channel,
            expected_exception_type=ChannelNameMissingError,
            expected_message="Argument 'name' cannot be empty or contain only whitespace.",
            name=""
        )

    def test_whitespace_only_name_raises_channel_name_missing_error(self):
        """Test that whitespace-only name raises ChannelNameMissingError."""
        self.assert_error_behavior(
            func_to_call=create_channel,
            expected_exception_type=ChannelNameMissingError,
            expected_message="Argument 'name' cannot be empty or contain only whitespace.",
            name="   "
        )

    def test_mixed_whitespace_only_name_raises_channel_name_missing_error(self):
        """Test that mixed whitespace-only name (tabs, spaces, newlines) raises ChannelNameMissingError."""
        self.assert_error_behavior(
            func_to_call=create_channel,
            expected_exception_type=ChannelNameMissingError,
            expected_message="Argument 'name' cannot be empty or contain only whitespace.",
            name=" \t\n "
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_name_with_whitespace_is_trimmed(self, mock_db):
        """Test that names with leading/trailing whitespace are properly trimmed."""
        result = create_channel(name="  test-channel  ")
        self.assertTrue(result.get("ok"))
        channel = result["channel"]
        self.assertEqual(channel["name"], "test-channel")  # Should be trimmed
        self.assertIn(channel["id"], DB["channels"])

    def test_invalid_is_private_type(self):
        """Test that providing a non-boolean is_private raises TypeError."""
        self.assert_error_behavior(
            func_to_call=create_channel,
            expected_exception_type=TypeError,
            expected_message="Argument 'is_private' must be a boolean.",
            name="valid-name",
            is_private="not-a-boolean"
        )

    def test_invalid_team_id_type(self):
        """Test that providing a non-string team_id (when not None) raises TypeError."""
        self.assert_error_behavior(
            func_to_call=create_channel,
            expected_exception_type=TypeError,
            expected_message="Argument 'team_id' must be a string or None.",
            name="valid-name",
            team_id=123
        )

    def test_team_id_none_is_valid(self):
        """Test that team_id=None is a valid input."""
        result = create_channel(name="channel-no-team", team_id=None)
        self.assertTrue(result.get("ok"))
        self.assertIsNone(result["channel"]["team_id"])

    def test_name_taken_raises_channel_name_taken_error(self):
        """Test that creating a channel with an existing name raises ChannelNameTakenError."""
        create_channel(name="existing-channel")  # Create first channel
        self.assert_error_behavior(
            func_to_call=create_channel,
            expected_exception_type=ChannelNameTakenError,
            expected_message="Channel name 'existing-channel' is already taken.",
            name="existing-channel"
        )

    @patch("slack.Conversations.DB", new_callable=lambda: DB)
    def test_channel_id_generation_and_collision_handling(self, mock_db):
        """Test unique channel ID generation, including simple collision handling."""
        # This test relies on the deterministic nature of hashlib.sha1 and random.seed
        name1 = "testchannel"  # Example: C440A418
        name2 = "anothername"  # Different name, different ID initially

        result1 = create_channel(name=name1)
        channel1_id = result1["channel"]["id"]
        self.assertIn(channel1_id, DB["channels"])

        # Manually create a scenario where the base ID would collide
        # To do this, we need to know what base_id name1 generates
        # Then, make DB["channels"] already contain an entry with C{base_id_of_name1}
        # Let's assume `name1` generates `base_id_name1` leading to `C{base_id_name1}`.
        # If we call `create_channel` with `name1` again, it should trigger `ChannelNameTakenError`.
        # This test is more about the ID suffix logic.
        # If two *different* names fortuitously produce the same initial base_id (unlikely with sha1[:8]):

        # Instead, let's test the suffix directly by populating DB.
        # Forcing a collision on the initial ID (not name)
        initial_id_for_name1 = "C" + hashlib.sha1(name1.encode()).hexdigest()[:8].upper()

        # Simulate this ID already exists but with a *different* name (to pass name check)
        DB["channels"][initial_id_for_name1] = {"name": "some_other_name_for_id_collision_test"}

        result_colliding_id = create_channel(name=name1)  # name1 is unique, but its initial ID clashes
        channel1_colliding_id_actual = result_colliding_id["channel"]["id"]

        self.assertTrue(result_colliding_id.get("ok"))
        self.assertNotEqual(channel1_colliding_id_actual, initial_id_for_name1)
        self.assertTrue(channel1_colliding_id_actual.startswith(initial_id_for_name1))
        self.assertEqual(len(channel1_colliding_id_actual), len(initial_id_for_name1) + 2)  # 2 char suffix
        self.assertIn(channel1_colliding_id_actual, DB["channels"])
