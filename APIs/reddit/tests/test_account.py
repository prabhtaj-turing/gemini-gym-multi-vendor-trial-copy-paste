import unittest
from reddit import Account
from .common import reset_db
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestAccountMethods(BaseTestCaseWithErrorHandler):
    """Tests for methods in the Account class."""

    def setUp(self):
        """Set up the test environment before each test."""
        reset_db()

    def test_get_api_v1_me(self):
        """Test getting user information."""
        me = Account.get_api_v1_me()
        self.assertIn("username", me)

    def test_get_api_v1_me_blocked(self):
        """Test getting blocked users."""
        blocked = Account.get_api_v1_me_blocked()
        self.assertIsInstance(blocked, list)

    def test_get_api_v1_me_friends(self):
        """Test getting friends list."""
        friends = Account.get_api_v1_me_friends()
        self.assertIsInstance(friends, list)

    def test_get_api_v1_me_karma(self):
        """Test getting karma information."""
        karma = Account.get_api_v1_me_karma()
        self.assertIn("total_karma", karma)

    def test_get_api_v1_me_prefs(self):
        """Test getting user preferences."""
        prefs = Account.get_api_v1_me_prefs()
        self.assertIn("nightmode", prefs)

    def test_patch_api_v1_me_prefs(self):
        """Test updating user preferences."""
        patched = Account.patch_api_v1_me_prefs({"nightmode": False})
        self.assertEqual(patched["status"], "success")

    def test_get_api_v1_me_trophies(self):
        """Test getting user trophies."""
        trophies = Account.get_api_v1_me_trophies()
        self.assertIsInstance(trophies, list)

    def test_get_prefs_blocked(self):
        """Test getting blocked users through prefs."""
        blocked_alt = Account.get_prefs_blocked()
        self.assertIsInstance(blocked_alt, list)

    def test_get_prefs_friends(self):
        """Test getting friends through prefs."""
        friends_alt = Account.get_prefs_friends()
        self.assertIsInstance(friends_alt, list)

    def test_get_prefs_messaging(self):
        """Test getting messaging preferences."""
        msg_pref = Account.get_prefs_messaging()
        self.assertIn("allow_pms", msg_pref)

    def test_get_prefs_trusted(self):
        """Test getting trusted users."""
        trusted = Account.get_prefs_trusted()
        self.assertIsInstance(trusted, list)

    def test_get_prefs_where(self):
        """Test getting preferences using where parameter."""
        generic = Account.get_prefs_where("blocked")
        self.assertIsInstance(generic, list)
        self.assertEqual(generic, ["blocked_user_1", "blocked_user_2"])


if __name__ == "__main__":
    unittest.main()
