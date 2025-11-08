# tests/test_users_history.py
import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.utils import reset_db
from .. import DB, list_history_records


class TestUsersHistory(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        # Clear existing history and add our test records
        DB["users"]["me"]["history"].clear()
        DB["users"]["me"]["history"].append({"id": "hist_1", "messages": ["msg_1"]})
        DB["users"]["me"]["history"].append({"id": "hist_2", "labelsAdded": ["INBOX"]})

    def test_history_list(self):
        resp = list_history_records("me")
        self.assertIn("history", resp)
        self.assertEqual(len(resp["history"]), 2)
        self.assertEqual(resp["history"][0]["id"], "hist_1")
        self.assertEqual(resp["history"][1]["id"], "hist_2")


if __name__ == "__main__":
    unittest.main()
