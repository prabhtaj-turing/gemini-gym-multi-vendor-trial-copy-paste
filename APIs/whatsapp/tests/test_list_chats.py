import copy
import unittest

from whatsapp.SimulationEngine import custom_errors
from whatsapp.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import list_chats

class TestListChats(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB["current_user_jid"] = "user0@s.whatsapp.net"

        self.chat1_data = {
            "chat_jid": "111@s.whatsapp.net", "name": "Alice Wonderland", "is_group": False,
            "last_active_timestamp": "2023-03-15T10:00:00Z", "unread_count": 2, "is_archived": False, "is_pinned": True,
            "messages": [
                {"message_id": "m1a", "chat_jid": "111@s.whatsapp.net", "sender_jid": "111@s.whatsapp.net",
                 "sender_name": "Alice Wonderland", "timestamp": "2023-03-15T09:59:00Z",
                 "text_content": "Older message", "is_outgoing": False},
                {"message_id": "m1b", "chat_jid": "111@s.whatsapp.net", "sender_jid": "user0@s.whatsapp.net",
                 "sender_name": "Me", "timestamp": "2023-03-15T10:00:00Z", "text_content": "My reply to Alice",
                 "is_outgoing": True}
            ]
        }
        self.chat2_data = {
            "chat_jid": "group1@g.us", "name": "Project Zeta", "is_group": True,
            "last_active_timestamp": "2023-03-14T12:30:00Z", "unread_count": 0, "is_archived": True, "is_pinned": False,
            "messages": [
                {"message_id": "m2a", "chat_jid": "group1@g.us", "sender_jid": "222@s.whatsapp.net",
                 "sender_name": "Bob The Builder", "timestamp": "2023-03-14T12:30:00Z",
                 "media_info": {"media_type": "image", "caption": "Diagram"}, "is_outgoing": False}
            ]
        }
        self.chat3_data = {
            "chat_jid": "222@s.whatsapp.net", "name": "Bob The Builder", "is_group": False,
            "last_active_timestamp": "2023-03-10T08:00:00Z", "unread_count": 5, "is_archived": False,
            "is_pinned": False,
            "messages": [
                {"message_id": "m3a", "chat_jid": "222@s.whatsapp.net", "sender_jid": "222@s.whatsapp.net",
                 "sender_name": "Bob The Builder", "timestamp": "2023-03-10T08:00:00Z", "text_content": "Morning!",
                 "is_outgoing": False}
            ]
        }
        self.chat4_data = {  # No last_active_timestamp, no messages
            "chat_jid": "333@s.whatsapp.net", "name": "Charlie Chaplin", "is_group": False,
            "last_active_timestamp": None, "unread_count": 0, "is_archived": False, "is_pinned": False,
            "messages": []
        }
        self.chat5_data = {  # No name
            "chat_jid": "444@s.whatsapp.net", "name": None, "is_group": False,
            "last_active_timestamp": "2023-03-01T00:00:00Z", "unread_count": 1, "is_archived": False,
            "is_pinned": False,
            "messages": [
                {"message_id": "m5a", "chat_jid": "444@s.whatsapp.net", "sender_jid": "444@s.whatsapp.net",
                 "sender_name": None, "timestamp": "2023-03-01T00:00:00Z", "text_content": "A message from no name",
                 "is_outgoing": False}
            ]
        }
        self.chat6_data = {  # Video
            "chat_jid": "group2@g.us", "name": "Movie Club", "is_group": True,
            "last_active_timestamp": "2023-03-13T18:00:00Z", "unread_count": 3, "is_archived": False, "is_pinned": True,
            "messages": [
                {"message_id": "m6a", "chat_jid": "group2@g.us", "sender_jid": "555@s.whatsapp.net",
                 "sender_name": "Eve", "timestamp": "2023-03-13T18:00:00Z", "media_info": {"media_type": "video"},
                 "is_outgoing": False}
            ]
        }
        self.chat7_data = {  # Audio
            "chat_jid": "555@s.whatsapp.net", "name": "Eve Audio", "is_group": False,
            "last_active_timestamp": "2023-03-12T15:00:00Z", "unread_count": 0, "is_archived": False,
            "is_pinned": False,
            "messages": [
                {"message_id": "m7a", "chat_jid": "555@s.whatsapp.net", "sender_jid": "user0@s.whatsapp.net",
                 "sender_name": "Me", "timestamp": "2023-03-12T15:00:00Z", "media_info": {"media_type": "audio"},
                 "is_outgoing": True}
            ]
        }
        self.chat8_data = {  # Document
            "chat_jid": "666@s.whatsapp.net", "name": "Frank Docs", "is_group": False,
            "last_active_timestamp": "2023-03-11T11:00:00Z", "unread_count": 1, "is_archived": True, "is_pinned": True,
            "messages": [
                {"message_id": "m8a", "chat_jid": "666@s.whatsapp.net", "sender_jid": "666@s.whatsapp.net",
                 "sender_name": "Frank Docs", "timestamp": "2023-03-11T11:00:00Z",
                 "media_info": {"media_type": "document", "file_name": "report.pdf"}, "is_outgoing": False}
            ]
        }
        self.chat9_data = {  # Sticker
            "chat_jid": "777@s.whatsapp.net", "name": "Grace Sticker", "is_group": False,
            "last_active_timestamp": "2023-03-09T09:00:00Z", "unread_count": 0, "is_archived": False,
            "is_pinned": False,
            "messages": [
                {"message_id": "m9a", "chat_jid": "777@s.whatsapp.net", "sender_jid": "777@s.whatsapp.net",
                 "sender_name": "Grace Sticker", "timestamp": "2023-03-09T09:00:00Z",
                 "media_info": {"media_type": "sticker"}, "is_outgoing": False}
            ]
        }
        self.chat10_data = {  # Long text for snippet
            "chat_jid": "888@s.whatsapp.net", "name": "Henry Longtext", "is_group": False,
            "last_active_timestamp": "2023-03-08T14:00:00Z", "unread_count": 0, "is_archived": False,
            "is_pinned": False,
            "messages": [
                {"message_id": "m10a", "chat_jid": "888@s.whatsapp.net", "sender_jid": "888@s.whatsapp.net",
                 "sender_name": "Henry Longtext", "timestamp": "2023-03-08T14:00:00Z",
                 "text_content": "This is a very long text message that might need to be truncated for the preview snippet depending on implementation.",
                 "is_outgoing": False}
            ]
        }

        DB["chats"] = {
            chat["chat_jid"]: chat for chat in [
                self.chat1_data, self.chat2_data, self.chat3_data, self.chat4_data,
                self.chat5_data, self.chat6_data, self.chat7_data, self.chat8_data,
                self.chat9_data, self.chat10_data
            ]
        }
        DB['actions'] = []

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_chat_structure(self, chat_dict, include_last_message=True):
        self.assertIsInstance(chat_dict, dict)
        expected_keys = {"chat_jid", "name", "is_group", "last_active_timestamp",
                         "unread_count", "is_archived", "is_pinned"}
        if include_last_message:
            expected_keys.add("last_message_preview")

        self.assertTrue(expected_keys.issubset(chat_dict.keys()),
                        f"Chat missing keys: {expected_keys - set(chat_dict.keys())}")
        self.assertIsInstance(chat_dict["chat_jid"], str)
        self.assertTrue(isinstance(chat_dict["name"], str) or chat_dict["name"] is None)
        self.assertIsInstance(chat_dict["is_group"], bool)
        self.assertTrue(
            isinstance(chat_dict["last_active_timestamp"], str) or chat_dict["last_active_timestamp"] is None)
        self.assertTrue(
            isinstance(chat_dict["unread_count"], int) or chat_dict["unread_count"] is None)  # Doc says Optional[int]
        self.assertIsInstance(chat_dict["is_archived"], bool)
        self.assertIsInstance(chat_dict["is_pinned"], bool)

        if include_last_message and chat_dict.get("last_message_preview") is not None:
            preview = chat_dict["last_message_preview"]
            self.assertIsInstance(preview, dict)
            preview_keys = {"message_id", "text_snippet", "sender_name", "timestamp", "is_outgoing"}
            self.assertTrue(preview_keys.issubset(preview.keys()),
                            f"Preview missing keys: {preview_keys - set(preview.keys())}")
            self.assertIsInstance(preview["message_id"], str)
            self.assertTrue(isinstance(preview["text_snippet"], str) or preview["text_snippet"] is None)
            self.assertTrue(isinstance(preview["sender_name"], str) or preview["sender_name"] is None)
            self.assertIsInstance(preview["timestamp"], str)
            self.assertIsInstance(preview["is_outgoing"], bool)

    def test_default_parameters_sort_last_active(self):
        result = list_chats()
        self.assertEqual(result["total_chats"], 10)
        self.assertEqual(result["page"], 0)
        self.assertEqual(result["limit"], 20)
        self.assertEqual(len(result["chats"]), 10)

        expected_order_jids = [
            "111@s.whatsapp.net",  # Alice Wonderland (2023-03-15T10:00:00Z)
            "group1@g.us",  # Project Zeta (2023-03-14T12:30:00Z)
            "group2@g.us",  # Movie Club (2023-03-13T18:00:00Z)
            "555@s.whatsapp.net",  # Eve Audio (2023-03-12T15:00:00Z)
            "666@s.whatsapp.net",  # Frank Docs (2023-03-11T11:00:00Z)
            "222@s.whatsapp.net",  # Bob The Builder (2023-03-10T08:00:00Z)
            "777@s.whatsapp.net",  # Grace Sticker (2023-03-09T09:00:00Z)
            "888@s.whatsapp.net",  # Henry Longtext (2023-03-08T14:00:00Z)
            "444@s.whatsapp.net",  # No name (2023-03-01T00:00:00Z)
            "333@s.whatsapp.net"  # Charlie Chaplin (None)
        ]
        actual_order_jids = [chat["chat_jid"] for chat in result["chats"]]
        self.assertEqual(actual_order_jids, expected_order_jids)

        for chat in result["chats"]:
            self._assert_chat_structure(chat, include_last_message=True)

        # Check a specific last message preview
        alice_chat = next(c for c in result["chats"] if c["chat_jid"] == "111@s.whatsapp.net")
        self.assertIsNotNone(alice_chat["last_message_preview"])
        self.assertEqual(alice_chat["last_message_preview"]["message_id"], "m1b")
        self.assertEqual(alice_chat["last_message_preview"]["text_snippet"], "My reply to Alice")
        self.assertEqual(alice_chat["last_message_preview"]["sender_name"], "Me")
        self.assertEqual(alice_chat["last_message_preview"]["timestamp"], "2023-03-15T10:00:00Z")
        self.assertTrue(alice_chat["last_message_preview"]["is_outgoing"])

    def test_sort_by_name(self):
        result = list_chats(sort_by="name")
        self.assertEqual(result["total_chats"], 10)
        self.assertEqual(len(result["chats"]), 10)

        # Assuming None names sort first, then alphabetically
        expected_order_jids_by_name = [
            "444@s.whatsapp.net",  # Name: None
            "111@s.whatsapp.net",  # Alice Wonderland
            "222@s.whatsapp.net",  # Bob The Builder
            "333@s.whatsapp.net",  # Charlie Chaplin
            "555@s.whatsapp.net",  # Eve Audio
            "666@s.whatsapp.net",  # Frank Docs
            "777@s.whatsapp.net",  # Grace Sticker
            "888@s.whatsapp.net",  # Henry Longtext
            "group2@g.us",  # Movie Club
            "group1@g.us",  # Project Zeta
        ]
        actual_order_jids = [chat["chat_jid"] for chat in result["chats"]]
        self.assertEqual(actual_order_jids, expected_order_jids_by_name)
        for chat in result["chats"]:
            self._assert_chat_structure(chat)

    def test_include_last_message_false(self):
        result = list_chats(include_last_message=False)
        self.assertEqual(len(result["chats"]), 10)
        for chat in result["chats"]:
            self._assert_chat_structure(chat, include_last_message=False)
            self.assertIsNone(chat['last_message_preview'])

    def test_query_by_name_alice(self):
        result = list_chats(query="Alice")
        self.assertEqual(result["total_chats"], 1)
        self.assertEqual(len(result["chats"]), 1)
        self.assertEqual(result["chats"][0]["chat_jid"], "111@s.whatsapp.net")
        self._assert_chat_structure(result["chats"][0])

    def test_query_by_name_bob(self):
        result = list_chats(query="Bob The Builder")  # Exact match
        self.assertEqual(result["total_chats"], 1)
        self.assertEqual(len(result["chats"]), 1)
        self.assertEqual(result["chats"][0]["chat_jid"], "222@s.whatsapp.net")

    def test_query_by_name_partial_project(self):
        result = list_chats(query="Project")  # Partial match
        self.assertEqual(result["total_chats"], 1)
        self.assertEqual(len(result["chats"]), 1)
        self.assertEqual(result["chats"][0]["chat_jid"], "group1@g.us")

    def test_query_by_jid(self):
        result = list_chats(query="111@s.whatsapp.net")
        self.assertEqual(result["total_chats"], 1)
        self.assertEqual(len(result["chats"]), 1)
        self.assertEqual(result["chats"][0]["chat_jid"], "111@s.whatsapp.net")

    def test_query_by_group_jid(self):
        result = list_chats(query="group1@g.us")
        self.assertEqual(result["total_chats"], 1)
        self.assertEqual(len(result["chats"]), 1)
        self.assertEqual(result["chats"][0]["chat_jid"], "group1@g.us")

    def test_query_no_match(self):
        result = list_chats(query="NonExistentNameOrJID")
        self.assertEqual(result["total_chats"], 0)
        self.assertEqual(len(result["chats"]), 0)
        self.assertEqual(result["page"], 0)
        self.assertEqual(result["limit"], 20)

    def test_pagination(self):
        result = list_chats(limit=3, page=0)
        self.assertEqual(result["total_chats"], 10)
        self.assertEqual(len(result["chats"]), 3)
        self.assertEqual(result["page"], 0)
        self.assertEqual(result["limit"], 3)
        self.assertEqual(result["chats"][0]["chat_jid"], "111@s.whatsapp.net")
        self.assertEqual(result["chats"][1]["chat_jid"], "group1@g.us")
        self.assertEqual(result["chats"][2]["chat_jid"], "group2@g.us")

        result = list_chats(limit=3, page=1)
        self.assertEqual(result["total_chats"], 10)
        self.assertEqual(len(result["chats"]), 3)
        self.assertEqual(result["page"], 1)
        self.assertEqual(result["limit"], 3)
        self.assertEqual(result["chats"][0]["chat_jid"], "555@s.whatsapp.net")  # Eve Audio
        self.assertEqual(result["chats"][1]["chat_jid"], "666@s.whatsapp.net")  # Frank Docs
        self.assertEqual(result["chats"][2]["chat_jid"], "222@s.whatsapp.net")  # Bob

        result = list_chats(limit=3, page=3)
        self.assertEqual(result["total_chats"], 10)
        self.assertEqual(len(result["chats"]), 1)
        self.assertEqual(result["page"], 3)
        self.assertEqual(result["limit"], 3)
        self.assertEqual(result["chats"][0]["chat_jid"], "333@s.whatsapp.net")  # Charlie (last by last_active)

    def test_pagination_limit_0(self):
        result = list_chats(limit=0)
        self.assertEqual(result["total_chats"], 10)  # Total matching criteria
        self.assertEqual(len(result["chats"]), 0)  # No chats returned due to limit
        self.assertEqual(result["page"], 0)
        self.assertEqual(result["limit"], 0)

    def test_empty_db_chats(self):
        DB["chats"].clear()
        result = list_chats()
        self.assertEqual(result["total_chats"], 0)
        self.assertEqual(len(result["chats"]), 0)
        self.assertEqual(result["page"], 0)
        self.assertEqual(result["limit"], 20)

    def test_chat_with_no_messages_preview_is_none(self):
        result = list_chats(query="Charlie Chaplin")  # Chat4 has no messages
        self.assertEqual(len(result["chats"]), 1)
        chat_data = result["chats"][0]
        self.assertEqual(chat_data["chat_jid"], "333@s.whatsapp.net")
        self.assertIsNone(chat_data.get("last_message_preview"))
        self._assert_chat_structure(chat_data, include_last_message=True)

    def test_chat_with_no_last_active_timestamp_sorts_last_by_default(self):
        result = list_chats(limit=1, page=9)  # Get the 10th chat
        self.assertEqual(len(result["chats"]), 1)
        self.assertEqual(result["chats"][0]["chat_jid"], "333@s.whatsapp.net")

    def test_media_message_previews(self):
        # Image
        result_img = list_chats(query="Project Zeta")  # Chat2
        self.assertEqual(result_img["chats"][0]["last_message_preview"]["text_snippet"], "Photo")
        self.assertEqual(result_img["chats"][0]["last_message_preview"]["message_id"], "m2a")

        # Video
        result_vid = list_chats(query="Movie Club")  # Chat6
        self.assertEqual(result_vid["chats"][0]["last_message_preview"]["text_snippet"], "Video")
        self.assertEqual(result_vid["chats"][0]["last_message_preview"]["message_id"], "m6a")

        # Audio
        result_aud = list_chats(query="Eve Audio")  # Chat7
        self.assertEqual(result_aud["chats"][0]["last_message_preview"]["text_snippet"], "Audio")
        self.assertEqual(result_aud["chats"][0]["last_message_preview"]["message_id"], "m7a")

        # Document
        result_doc = list_chats(query="Frank Docs")  # Chat8
        self.assertEqual(result_doc["chats"][0]["last_message_preview"]["text_snippet"], "Document")
        self.assertEqual(result_doc["chats"][0]["last_message_preview"]["message_id"], "m8a")

        # Sticker
        result_stk = list_chats(query="Grace Sticker")  # Chat9
        self.assertEqual(result_stk["chats"][0]["last_message_preview"]["text_snippet"], "Sticker")
        self.assertEqual(result_stk["chats"][0]["last_message_preview"]["message_id"], "m9a")

    def test_text_message_preview_snippet_long_text(self):
        result = list_chats(query="Henry Longtext")  # Chat10
        preview = result["chats"][0]["last_message_preview"]
        original_text = self.chat10_data["messages"][0]["text_content"]
        self.assertEqual(preview["text_snippet"], original_text)

    def test_error_invalid_sort_by(self):
        self.assert_error_behavior(
            func_to_call=list_chats,
            expected_exception_type=custom_errors.InvalidSortByError,
            expected_message="The specified sort_by parameter is not valid.",
            sort_by="invalid_field"
        )

    def test_error_pagination_page_out_of_range(self):
        self.assert_error_behavior(
            func_to_call=list_chats,
            expected_exception_type=custom_errors.PaginationError,
            expected_message="The requested page number is out of range.",
            page=100
        )

        self.assert_error_behavior(
            func_to_call=list_chats,
            expected_exception_type=custom_errors.PaginationError,
            expected_message="The requested page number is out of range.",
            limit=1,
            page=10
        )

    def test_error_validation_limit_type(self):
        expected_message = "1 validation error for ListChatsFunctionArgs\nlimit\n  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='not_an_int', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/int_parsing"
        self.assert_error_behavior(
            func_to_call=list_chats,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=expected_message,
            limit="not_an_int"
        )

    def test_error_validation_limit_negative(self):
        expected_message = "1 validation error for ListChatsFunctionArgs\nlimit\n  Input should be greater than or equal to 0 [type=greater_than_equal, input_value=-1, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/greater_than_equal"
        self.assert_error_behavior(
            func_to_call=list_chats,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=expected_message,
            limit=-1
        )

    def test_error_validation_page_type(self):
        expected_message = "1 validation error for ListChatsFunctionArgs\npage\n  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='not_an_int', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/int_parsing"
        self.assert_error_behavior(
            func_to_call=list_chats,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=expected_message,
            page="not_an_int"
        )

    def test_error_validation_page_negative(self):
        expected_message = "1 validation error for ListChatsFunctionArgs\npage\n  Input should be greater than or equal to 0 [type=greater_than_equal, input_value=-1, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/greater_than_equal"
        self.assert_error_behavior(
            func_to_call=list_chats,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=expected_message,
            page=-1
        )

    def test_error_validation_query_type(self):
        expected_message = "1 validation error for ListChatsFunctionArgs\nquery\n  Input should be a valid string [type=string_type, input_value=123, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type"
        self.assert_error_behavior(
            func_to_call=list_chats,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=expected_message,
            query=123
        )

    def test_error_validation_include_last_message_type(self):
        expected_message = "1 validation error for ListChatsFunctionArgs\ninclude_last_message\n  Input should be a valid boolean, unable to interpret input [type=bool_parsing, input_value='not_a_bool', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/bool_parsing"
        self.assert_error_behavior(
            func_to_call=list_chats,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=expected_message,
            include_last_message="not_a_bool"
        )

    def test_error_validation_sort_by_type(self):
        expected_message = "1 validation error for ListChatsFunctionArgs\nsort_by\n  Input should be a valid string [type=string_type, input_value=123, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type"
        self.assert_error_behavior(
            func_to_call=list_chats,
            expected_exception_type=custom_errors.InvalidInputError,
            expected_message=expected_message,
            sort_by=123
        )

    def test_archived_and_pinned_status_in_response(self):
        result = list_chats(query="Alice")
        self.assertTrue(result["chats"][0]["is_pinned"])
        self.assertFalse(result["chats"][0]["is_archived"])

        result = list_chats(query="Project Zeta")
        self.assertFalse(result["chats"][0]["is_pinned"])
        self.assertTrue(result["chats"][0]["is_archived"])

        result = list_chats(query="Frank Docs")
        self.assertTrue(result["chats"][0]["is_pinned"])
        self.assertTrue(result["chats"][0]["is_archived"])

    def test_unread_count_in_response(self):
        result = list_chats(query="Alice")
        self.assertEqual(result["chats"][0]["unread_count"], 2)

        result = list_chats(query="Project Zeta")
        self.assertEqual(result["chats"][0]["unread_count"], 0)

        result = list_chats(query="Bob")
        self.assertEqual(result["chats"][0]["unread_count"], 5)


if __name__ == '__main__':
    unittest.main()
