import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
import reddit as RedditAPI
from .common import reset_db


class TestMiscMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Misc class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()

    def test_get_scopes(self):
        """Test getting API scopes."""
        scopes = RedditAPI.Misc.get_api_v1_scopes()
        self.assertIn("scopes", scopes)
        self.assertIn("identity", scopes["scopes"])


if __name__ == "__main__":
    unittest.main()
