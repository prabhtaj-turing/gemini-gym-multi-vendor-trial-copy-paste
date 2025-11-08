# tests/test_users_core.py
import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.utils import reset_db
from .. import stop_mailbox_watch, get_user_profile, watch_user_mailbox


class TestUsersCore(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()

    def test_get_profile(self):
        profile = get_user_profile("me")
        self.assertEqual(profile["emailAddress"], "me@gmail.com")

    def test_get_profile_empty_string(self):
        self.assert_error_behavior(
            func_to_call=get_user_profile,
            expected_exception_type=ValueError,
            expected_message='userId cannot be an empty string.',
            userId = ""
        )
        self.assert_error_behavior(
            func_to_call=get_user_profile,
            expected_exception_type=ValueError,
            expected_message='userId cannot be an empty string.',
            userId=" "
        )

    def test_get_profile_int(self):
        self.assert_error_behavior(
            func_to_call=get_user_profile,
            expected_exception_type=TypeError,
            expected_message='userId must be a string.',
            userId = 123
        )

    def test_watch_and_stop(self):
        resp = watch_user_mailbox(
            "me", {"labelFilterAction": "include", "labelIds": ["INBOX"]}
        )
        self.assertIn("historyId", resp)
        self.assertIn("expiration", resp)
        stop_mailbox_watch("me")
        # Directly check DB (for testing purposes)
        from gmail import DB

        self.assertEqual(DB["users"]["me"]["watch"], {})


if __name__ == "__main__":
    unittest.main()
