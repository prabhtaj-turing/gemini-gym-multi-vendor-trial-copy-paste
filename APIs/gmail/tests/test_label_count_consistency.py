import copy
import json
import os
import unittest

from ..SimulationEngine.utils import verify_and_optionally_fix_label_counts


class TestLabelCountVerification(unittest.TestCase):
    """Tests for the verify_and_optionally_fix_label_counts helper."""

    def setUp(self):
        self.db_template = {
            "users": {
                "me": {
                    "profile": {
                        "emailAddress": "john.doe@gmail.com",
                        "messagesTotal": 0,
                        "threadsTotal": 0,
                    },
                    "messages": {
                        "msg_1": {
                            "id": "msg_1",
                            "labelIds": ["INBOX", "UNREAD"],
                            "isRead": False,
                        },
                        "msg_2": {
                            "id": "msg_2",
                            "labelIds": ["INBOX"],
                            "isRead": True,
                        },
                        "msg_3": {
                            "id": "msg_3",
                            "labelIds": ["SENT"],
                            "isRead": True,
                        },
                    },
                    "threads": {
                        "thread-1": {"id": "thread-1", "messageIds": ["msg_1"]},
                        "thread-2": {"id": "thread-2", "messageIds": ["msg_2"]},
                        "thread-3": {"id": "thread-3", "messageIds": ["msg_3"]},
                    },
                    "labels": {
                        "INBOX": {
                            "id": "INBOX",
                            "name": "Inbox",
                            "type": "system",
                            "labelListVisibility": "labelShow",
                            "messageListVisibility": "show",
                            "messagesTotal": 99,
                            "messagesUnread": 0,
                            "threadsTotal": 0,
                            "threadsUnread": 0,
                        },
                        "UNREAD": {
                            "id": "UNREAD",
                            "name": "Unread",
                            "type": "system",
                            "labelListVisibility": "labelShow",
                            "messageListVisibility": "show",
                            "messagesTotal": 0,
                            "messagesUnread": 0,
                            "threadsTotal": 0,
                            "threadsUnread": 0,
                        },
                        "SENT": {
                            "id": "SENT",
                            "name": "Sent",
                            "type": "system",
                            "labelListVisibility": "labelHide",
                            "messageListVisibility": "hide",
                            "messagesTotal": 0,
                            "messagesUnread": 0,
                            "threadsTotal": 0,
                            "threadsUnread": 0,
                        },
                    },
                }
            }
        }

    def _get_copy(self):
        return copy.deepcopy(self.db_template)

    def test_detects_differences_without_mutation(self):
        db_copy = self._get_copy()
        result = verify_and_optionally_fix_label_counts(db_copy, apply_changes=False)

        self.assertTrue(result["hasDifferences"])
        inbox_diff = result["users"]["me"]["labels"]["INBOX"]["messagesTotal"]
        self.assertEqual(inbox_diff, {"expected": 2, "actual": 99})
        # ensure original snapshot untouched
        self.assertEqual(self.db_template["users"]["me"]["labels"]["INBOX"]["messagesTotal"], 99)

    def test_updates_counts_when_requested(self):
        db_copy = self._get_copy()
        result = verify_and_optionally_fix_label_counts(db_copy, apply_changes=True)

        self.assertTrue(result["hasDifferences"])
        inbox_label = db_copy["users"]["me"]["labels"]["INBOX"]
        self.assertEqual(inbox_label["messagesTotal"], 2)
        self.assertEqual(inbox_label["messagesUnread"], 1)
        self.assertEqual(inbox_label["threadsTotal"], 2)
        self.assertEqual(inbox_label["threadsUnread"], 1)
        profile = db_copy["users"]["me"]["profile"]
        self.assertEqual(profile["messagesTotal"], 3)
        self.assertEqual(profile["threadsTotal"], 3)

    def test_creates_missing_label_entries(self):
        db_copy = self._get_copy()
        del db_copy["users"]["me"]["labels"]["UNREAD"]

        verify_and_optionally_fix_label_counts(db_copy, apply_changes=True)

        unread_label = db_copy["users"]["me"]["labels"].get("UNREAD")
        self.assertIsNotNone(unread_label)
        self.assertEqual(unread_label["messagesTotal"], 1)
        self.assertEqual(unread_label["messagesUnread"], 1)

    def test_no_differences_after_fix(self):
        db_copy = self._get_copy()
        verify_and_optionally_fix_label_counts(db_copy, apply_changes=True)

        second_pass = verify_and_optionally_fix_label_counts(db_copy, apply_changes=False)
        self.assertFalse(second_pass["hasDifferences"])

    def test_verify_default_database_snapshot(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        default_db_path = os.path.join(project_root, "DBs", "GmailDefaultDB.json")
        with open(default_db_path, "r", encoding="utf-8") as db_file:
            db_data = json.load(db_file)

        result = verify_and_optionally_fix_label_counts(db_data, apply_changes=False)
        self.assertFalse(result["hasDifferences"])


if __name__ == "__main__":
    unittest.main()

