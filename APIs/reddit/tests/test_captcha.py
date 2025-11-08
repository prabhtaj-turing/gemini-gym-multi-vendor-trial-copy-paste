import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
import reddit as RedditAPI
from .common import reset_db


class TestCaptchaMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Captcha class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()

    def test_get_api_needs_captcha_default(self):
        """Test getting captcha status with default state."""
        self.assertFalse(RedditAPI.Captcha.get_api_needs_captcha())

    def test_get_api_needs_captcha_true(self):
        """Test getting captcha status when captcha is needed."""
        RedditAPI.DB["captcha_needed"] = True
        self.assertTrue(RedditAPI.Captcha.get_api_needs_captcha())


if __name__ == "__main__":
    unittest.main()
