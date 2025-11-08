import base64
from typing import Dict, Any
from unittest.mock import patch

from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import get_current_user_id


class TestCurrentUserId(BaseTestCaseWithErrorHandler):
    def setUp(self):
        # Prepare a minimal DB with current_user
        self.test_db: Dict[str, Any] = {
            "current_user": {"id": "U999", "name": "tester", "is_admin": False}
        }
        self.patcher = patch("slack.Users.DB", self.test_db)
        self.mock_db = self.patcher.start()
        # Also patch Conversations.DB etc if accessed indirectly (not required here)

    def tearDown(self):
        self.patcher.stop()

    def test_returns_current_user_id(self):
        resp = get_current_user_id()
        self.assertEqual(resp, {"ok": True, "user_id": "U999"})

    def test_no_current_user(self):
        # Remove current_user key
        self.test_db.pop("current_user")
        resp = get_current_user_id()
        self.assertEqual(resp, {"ok": False, "error": "current_user_not_set"}) 