import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
import reddit as RedditAPI
from .common import reset_db


class TestEmoji(BaseTestCaseWithErrorHandler):
    """
    Test cases for the Emoji class methods.
    Tests emoji-related functionality including adding, retrieving, deleting,
    and customizing emojis.
    """

    def setUp(self):
        """
        Set up the test environment before each test.
        Resets the database to ensure a clean state.
        """
        reset_db()

    def test_add_emoji(self):
        """
        Test adding a new emoji to a subreddit.
        Verifies that the emoji is added successfully and returns the correct status.
        """
        add_e = RedditAPI.Emoji.post_api_v1_subreddit_emoji_json(
            "mysub",
            "joy",
            s3_key="mysub/joy_123456",
            css=".emoji { }",
            mod_flair_only=False,
            post_flair_allowed=True,
            user_flair_allowed=True,
        )
        self.assertEqual(add_e["status"], "success")
        self.assertEqual(add_e["emoji_name"], "joy")
        self.assertEqual(add_e["mod_flair_only"], False)
        self.assertEqual(add_e["post_flair_allowed"], True)
        self.assertEqual(add_e["user_flair_allowed"], True)

    def test_add_emoji_invalid_name(self):
        """
        Test adding an emoji with an invalid name.
        Verifies that the function rejects names with special characters or exceeding length limit.
        """
        # Test name with special character
        result = RedditAPI.Emoji.post_api_v1_subreddit_emoji_json(
            "mysub", "joy!", s3_key="mysub/joy_123456"
        )
        self.assertEqual(result["error"], "Invalid emoji name")

        # Test name exceeding 24 characters
        result = RedditAPI.Emoji.post_api_v1_subreddit_emoji_json(
            "mysub", "a" * 25, s3_key="mysub/joy_123456"
        )
        self.assertEqual(result["error"], "Invalid emoji name")

    def test_add_mod_only_emoji(self):
        """
        Test adding a moderator-only emoji.
        Verifies that the emoji is added with correct permission flags.
        """
        add_e = RedditAPI.Emoji.post_api_v1_subreddit_emoji_json(
            "mysub",
            "verified",
            s3_key="mysub/verified_123456",
            mod_flair_only=True,
            post_flair_allowed=False,
            user_flair_allowed=False,
        )
        self.assertEqual(add_e["status"], "success")
        self.assertEqual(add_e["mod_flair_only"], True)
        self.assertEqual(add_e["post_flair_allowed"], False)
        self.assertEqual(add_e["user_flair_allowed"], False)

    def test_get_all_emojis(self):
        """
        Test retrieving all emojis for a subreddit.
        Verifies that added emojis are included in the returned list with correct attributes.
        """
        # First add an emoji
        RedditAPI.Emoji.post_api_v1_subreddit_emoji_json(
            "mysub", "joy", s3_key="mysub/joy_123456", css=".emoji { }"
        )

        # Then get all emojis
        all_e = RedditAPI.Emoji.get_api_v1_subreddit_emojis_all("mysub")
        self.assertIn("joy", all_e.get("emojis", {}))
        emoji_data = all_e["emojis"]["joy"]
        self.assertEqual(emoji_data["s3_key"], "mysub/joy_123456")
        self.assertEqual(emoji_data["css"], ".emoji { }")
        self.assertEqual(emoji_data["mod_flair_only"], False)
        self.assertEqual(emoji_data["post_flair_allowed"], True)
        self.assertEqual(emoji_data["user_flair_allowed"], True)

    def test_delete_emoji(self):
        """
        Test deleting an emoji from a subreddit.
        Verifies that the emoji is removed successfully and no longer appears in the list.
        """
        # First add an emoji
        RedditAPI.Emoji.post_api_v1_subreddit_emoji_json(
            "mysub", "joy", s3_key="mysub/joy_123456"
        )

        # Then delete it
        del_e = RedditAPI.Emoji.delete_api_v1_subreddit_emoji_emoji_name("mysub", "joy")
        self.assertEqual(del_e["status"], "deleted")
        self.assertEqual(del_e["s3_key"], "mysub/joy_123456")

        # Verify it's gone
        all_e_after_delete = RedditAPI.Emoji.get_api_v1_subreddit_emojis_all("mysub")
        self.assertNotIn("joy", all_e_after_delete.get("emojis", {}))

    def test_upload_emoji_asset(self):
        """
        Test uploading an emoji asset to S3.
        Verifies that the upload lease contains all required credentials and URLs.
        """
        upload = RedditAPI.Emoji.post_api_v1_subreddit_emoji_asset_upload_s3_json(
            "image.png", "image/png"
        )
        self.assertIn("credentials", upload)
        self.assertIn("s3_url", upload)
        self.assertIn("key", upload)
        self.assertTrue(upload["key"].endswith("image.png"))

    def test_custom_emoji_size(self):
        """
        Test setting custom size for an emoji.
        Verifies that the size is updated successfully with the specified dimensions.
        """
        # First add an emoji
        RedditAPI.Emoji.post_api_v1_subreddit_emoji_json(
            "mysub", "happy", s3_key="mysub/happy_123456"
        )

        # Then set custom size
        size = RedditAPI.Emoji.post_api_v1_subreddit_emoji_custom_size("happy", 64, 64)
        self.assertEqual(size["status"], "custom_size_updated")
        self.assertEqual(size["width"], 64)
        self.assertEqual(size["height"], 64)


if __name__ == "__main__":
    unittest.main()
