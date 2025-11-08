import unittest
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.utils import reset_db
from ..SimulationEngine.db import DB
from .. import delete_label

class TestDeleteLabel(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        # Add test label for deletion tests
        DB["users"]["me"]["labels"]["LABEL_EXISTING_1"] = {"name": "TestLabel"}
        # Add another user for cross-user tests
        DB["users"]["another_user@example.com"] = {
            "labels": {
                "LABEL_OTHER_USER": {"name": "OtherUserLabel"}
            },
            "profile": {
                "emailAddress": "another_user@example.com",
                "messagesTotal": 0,
                "threadsTotal": 0,
                "historyId": "1"
            },
            "drafts": {},
            "messages": {},
            "threads": {},
            "settings": {
                "imap": {"enabled": False},
                "pop": {"accessWindow": "disabled"},
                "vacation": {"enableAutoReply": False},
                "language": {"displayLanguage": "en"},
                "autoForwarding": {"enabled": False},
                "sendAs": {}
            },
            "history": [],
            "watch": {}
        }

    def test_delete_existing_label_successfully(self):
        user_id = "me"
        label_id_to_delete = "LABEL_EXISTING_1"
        self.assertIn(label_id_to_delete, DB["users"][user_id]["labels"])
        initial_label_count = len(DB["users"][user_id]["labels"])
        delete_label(userId=user_id, id=label_id_to_delete)
        self.assertEqual(len(DB["users"][user_id]["labels"]), initial_label_count - 1)
        self.assertNotIn(label_id_to_delete, DB["users"][user_id]["labels"])

    def test_delete_non_existent_label_id(self):
        user_id = "me"
        non_existent_label_id = "LABEL_NON_EXISTENT"
        initial_label_count = len(DB["users"][user_id]["labels"])
        self.assertNotIn(non_existent_label_id, DB["users"][user_id]["labels"])
        delete_label(userId=user_id, id=non_existent_label_id)
        self.assertEqual(len(DB["users"][user_id]["labels"]), initial_label_count)

    def test_delete_label_invalid_user_id_type(self):
        self.assert_error_behavior(
            func_to_call=delete_label,
            expected_exception_type=TypeError,
            expected_message="userId must be a string, but got int.",
            userId=123,
            id="LABEL_EXISTING_1"
        )

    def test_delete_label_invalid_id_type(self):
        self.assert_error_behavior(
            func_to_call=delete_label,
            expected_exception_type=TypeError,
            expected_message="id must be a string, but got int.",
            userId="me",
            id=456
        )

    def test_delete_label_empty_string_id(self):
        user_id = "me"
        initial_label_count = len(DB["users"][user_id]["labels"])
        delete_label(userId=user_id, id="")
        self.assertEqual(len(DB["users"][user_id]["labels"]), initial_label_count)

    def test_delete_label_user_not_found(self):
        non_existent_user_id = "unknown_user@example.com"
        self.assert_error_behavior(
            func_to_call=delete_label,
            expected_exception_type=ValueError,
            expected_message=f"User '{non_existent_user_id}' does not exist.",
            userId=non_existent_user_id,
            id="LABEL_ANY"
        )

    def test_delete_label_default_user_id(self):
        label_id_to_delete = "LABEL_EXISTING_1"
        self.assertIn(label_id_to_delete, DB["users"]["me"]["labels"])
        initial_label_count = len(DB["users"]["me"]["labels"])
        delete_label(id=label_id_to_delete)  # userId defaults to "me"
        self.assertEqual(len(DB["users"]["me"]["labels"]), initial_label_count - 1)
        self.assertNotIn(label_id_to_delete, DB["users"]["me"]["labels"])

    def test_delete_label_default_id(self):
        user_id = "me"
        initial_label_count = len(DB["users"][user_id]["labels"])
        delete_label(userId=user_id)  # id defaults to ""
        self.assertEqual(len(DB["users"][user_id]["labels"]), initial_label_count)

    def test_error_dict_mode_type_error(self):
        self.assert_error_behavior(
            func_to_call=delete_label,
            expected_exception_type=TypeError,
            expected_message="userId must be a string, but got int.",
            userId=123,
            id="LABEL_EXISTING_1"
        )

    def test_error_dict_mode_key_error(self):
        non_existent_user_id = "unknown_user@example.com"
        self.assert_error_behavior(
            func_to_call=delete_label,
            expected_exception_type=ValueError,
            expected_message=f"User '{non_existent_user_id}' does not exist.",
            userId=non_existent_user_id,
            id="LABEL_ANY"
        )


if __name__ == "__main__":
    unittest.main()