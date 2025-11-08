import unittest
import reddit as RedditAPI
from .common import reset_db
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestWidgetsMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Widgets class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()
        # Create a test widget for use across tests
        post_w = RedditAPI.Widgets.post_api_widget(
            widget_data={"type": "text", "content": "Hello"}
        )
        self.widget_id = post_w["widget_id"]
        self.widget_content = "Hello"

    def test_create_widget(self):
        """Test creating a widget."""
        post_w = RedditAPI.Widgets.post_api_widget(
            widget_data={"type": "text", "content": "Hello"}
        )
        self.assertEqual(post_w["status"], "widget_created")
        wid = post_w["widget_id"]
        # Verify creation in DB
        self.assertIn(wid, RedditAPI.DB["widgets"])
        self.assertEqual(RedditAPI.DB["widgets"][wid]["content"], "Hello")

    def test_delete_widget(self):
        """Test deleting a widget."""
        del_w = RedditAPI.Widgets.delete_api_widget_widget_id(self.widget_id)
        self.assertEqual(del_w["status"], "widget_deleted")
        # Verify deletion from DB
        self.assertNotIn(self.widget_id, RedditAPI.DB["widgets"])

    def test_upload_widget_image(self):
        """Test uploading a widget image."""
        img_up = RedditAPI.Widgets.post_api_widget_image_upload_s3(
            "widget.png", "image/png"
        )
        self.assertIn("credentials", img_up)
        self.assertIn("s3_url", img_up)
        self.assertIn("key", img_up)
        self.assertTrue(img_up["key"].endswith("widget.png"))

    def test_patch_widget_order(self):
        """Test patching widget order."""
        patch = RedditAPI.Widgets.patch_api_widget_order_section(
            "sidebar", ["widget_1", "widget_2"]
        )
        self.assertEqual(patch["status"], "widget_order_patched")

    def test_get_widgets(self):
        """Test getting all widgets."""
        get_w = RedditAPI.Widgets.get_api_widgets()
        self.assertIn("widgets", get_w)


if __name__ == "__main__":
    unittest.main()
