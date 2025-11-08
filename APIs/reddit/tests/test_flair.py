import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
import reddit as RedditAPI
from .common import reset_db


class TestFlairMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Flair class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()
        # Set up test data that can be used across multiple tests
        self.test_user = "SomeUser"
        self.test_link = "t3_abc"
        self.test_template_id = "tpl123"
        self.test_flair_text = "Cool flair!"

    def test_clear_flair_templates(self):
        """Test clearing flair templates."""
        cleared = RedditAPI.Flair.post_api_clearflairtemplates(flair_type="USER_FLAIR")
        self.assertEqual(cleared["status"], "cleared")
        self.assertEqual(cleared["flair_type"], "USER_FLAIR")

    def test_delete_flair(self):
        """Test deleting a user's flair."""
        del_flair = RedditAPI.Flair.post_api_deleteflair(name=self.test_user)
        self.assertEqual(del_flair["status"], "flair_deleted")
        self.assertEqual(del_flair["user"], self.test_user)

    def test_delete_flair_template(self):
        """Test deleting a flair template."""
        del_tpl = RedditAPI.Flair.post_api_deleteflairtemplate(
            template_id=self.test_template_id
        )
        self.assertEqual(del_tpl["status"], "flair_template_deleted")
        self.assertEqual(del_tpl["template_id"], self.test_template_id)

    def test_set_flair(self):
        """Test setting a user's flair."""
        flair_set = RedditAPI.Flair.post_api_flair(
            api_type="json", name=self.test_user, text=self.test_flair_text
        )
        self.assertEqual(flair_set["status"], "success")
        self.assertEqual(flair_set["user"], self.test_user)
        self.assertEqual(flair_set["text"], self.test_flair_text)

    def test_reorder_flair_templates(self):
        """Test reordering flair templates."""
        reorder = RedditAPI.Flair.patch_api_flair_template_order(
            flair_type="LINK_FLAIR", template_ids=["tplA", "tplB"]
        )
        self.assertEqual(reorder["status"], "success")
        self.assertEqual(reorder["order"], ["tplA", "tplB"])

    def test_configure_flair(self):
        """Test configuring flair settings."""
        config = RedditAPI.Flair.post_api_flairconfig(
            flair_enabled=True, flair_position="right"
        )
        self.assertEqual(config["status"], "updated")
        self.assertTrue(config["flair_enabled"])
        self.assertEqual(config["flair_position"], "right")

    def test_upload_flair_csv(self):
        """Test uploading flair via CSV."""
        csv_up = RedditAPI.Flair.post_api_flaircsv(flair_csv="user,flair\nu1,hello")
        self.assertEqual(csv_up["status"], "processed_csv")
        self.assertEqual(csv_up["csv_data"], "user,flair\nu1,hello")

    def test_get_flair_list(self):
        """Test getting flair list."""
        fl_list = RedditAPI.Flair.get_api_flairlist(
            after="t2_something", name="u1", limit=50
        )
        self.assertIn("users", fl_list)
        self.assertEqual(fl_list["after"], "t2_something")
        self.assertEqual(fl_list["filter_name"], "u1")

    def test_get_flair_selector(self):
        """Test getting flair selector options."""
        fl_sel = RedditAPI.Flair.post_api_flairselector(link=self.test_link)
        self.assertIn("options", fl_sel)
        self.assertEqual(fl_sel["link"], self.test_link)

    def test_create_flair_template(self):
        """Test creating a flair template."""
        fl_template = RedditAPI.Flair.post_api_flairtemplate(
            flair_type="USER_FLAIR", text="Test Flair"
        )
        self.assertEqual(fl_template["status"], "template_saved")
        self.assertEqual(fl_template["text"], "Test Flair")

    def test_create_flair_template_v2(self):
        """Test creating a flair template using v2 API."""
        fl_template_v2 = RedditAPI.Flair.post_api_flairtemplate_v2(
            flair_type="LINK_FLAIR", text="Another Flair"
        )
        self.assertEqual(fl_template_v2["status"], "template_v2_saved")
        self.assertEqual(fl_template_v2["text"], "Another Flair")

    def test_get_link_flair(self):
        """Test getting link flair."""
        link_flair = RedditAPI.Flair.get_api_link_flair()
        self.assertIsInstance(link_flair, list)

    def test_get_link_flair_v2(self):
        """Test getting link flair using v2 API."""
        link_flair_v2 = RedditAPI.Flair.get_api_link_flair_v2()
        self.assertIsInstance(link_flair_v2, list)

    def test_select_flair(self):
        """Test selecting a flair for a link."""
        select_fl = RedditAPI.Flair.post_api_selectflair(
            link=self.test_link, flair_template_id=self.test_template_id
        )
        self.assertEqual(select_fl["status"], "success")
        self.assertEqual(select_fl["link"], self.test_link)
        self.assertEqual(select_fl["template_id"], self.test_template_id)

    def test_set_flair_enabled(self):
        """Test enabling/disabling flair."""
        set_flair_enabled = RedditAPI.Flair.post_api_setflairenabled(
            api_type="json", flair_enabled=True
        )
        self.assertEqual(set_flair_enabled["status"], "flair_enabled_set")
        self.assertTrue(set_flair_enabled["enabled"])

    def test_get_user_flair(self):
        """Test getting user flair."""
        user_flair = RedditAPI.Flair.get_api_user_flair()
        self.assertIsInstance(user_flair, list)

    def test_get_user_flair_v2(self):
        """Test getting user flair using v2 API."""
        user_flair_v2 = RedditAPI.Flair.get_api_user_flair_v2()
        self.assertIsInstance(user_flair_v2, list)


if __name__ == "__main__":
    unittest.main()
