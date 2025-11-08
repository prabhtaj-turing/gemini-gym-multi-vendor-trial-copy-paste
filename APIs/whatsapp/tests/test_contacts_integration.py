import unittest
import copy
from whatsapp.SimulationEngine import custom_errors, models, utils
from .. import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from unittest.mock import patch
from pydantic import ValidationError as PydanticValidationError
from .. import search_contacts, get_contact_chats

class TestGetContactChatsBase(unittest.TestCase):
    def setUp(self):
        """Set up the test environment with the new DB structure."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.user_jid = "user@s.whatsapp.net"
        self.contact1_jid = "contact1@s.whatsapp.net"
        self.contact2_jid = "contact2@s.whatsapp.net"
        self.contact3_jid = "contact3@s.whatsapp.net" # Contact with no chats

        DB["current_user_jid"] = self.user_jid
        
        # --- NEW DB STRUCTURE FOR CONTACTS ---
        DB["contacts"] = {
            f"people/{self.user_jid}": {
                "resourceName": f"people/{self.user_jid}", "etag": "etag_user",
                "names": [{"givenName": "Current", "familyName": "User"}],
                "phoneNumbers": [{"value": self.user_jid.split('@')[0], "primary": True}],
                "whatsapp": {"jid": self.user_jid, "profile_name": "Current User", "is_whatsapp_user": True}
            },
            f"people/{self.contact1_jid}": {
                "resourceName": f"people/{self.contact1_jid}", "etag": "etag_c1",
                "names": [{"givenName": "Contact", "familyName": "One"}],
                "phoneNumbers": [{"value": self.contact1_jid.split('@')[0], "primary": True}],
                "whatsapp": {"jid": self.contact1_jid, "profile_name": "Contact One", "name_in_address_book": "C One", "is_whatsapp_user": True}
            },
            f"people/{self.contact2_jid}": {
                "resourceName": f"people/{self.contact2_jid}", "etag": "etag_c2",
                "names": [{"givenName": "Contact", "familyName": "Two"}],
                "phoneNumbers": [{"value": self.contact2_jid.split('@')[0], "primary": True}],
                "whatsapp": {"jid": self.contact2_jid, "profile_name": "Contact Two", "is_whatsapp_user": True}
            },
            f"people/{self.contact3_jid}": {
                "resourceName": f"people/{self.contact3_jid}", "etag": "etag_c3",
                "names": [{"givenName": "Contact", "familyName": "Three"}],
                "phoneNumbers": [{"value": self.contact3_jid.split('@')[0], "primary": True}],
                "whatsapp": {"jid": self.contact3_jid, "profile_name": "Contact Three", "is_whatsapp_user": True}
            }
        }

        # Timestamps for sorting (most recent first)
        self.ts_chat1_msg2 = "2023-01-01T12:00:00Z" # newest overall for contact1
        self.ts_chat1_msg1 = "2023-01-01T11:59:00Z"
        self.ts_chat2_msg1 = "2023-01-01T10:00:00Z"
        self.ts_chat3_msg1 = "2023-01-01T09:00:00Z" # older for contact1
        self.ts_chat_other_contact = "2023-01-01T13:00:00Z"

        self.chat_contact1_direct_messages_jid = self.contact1_jid
        self.chat_contact1_group_messages_jid = "group_contact1_messages@g.us"
        self.chat_contact1_group_no_messages_jid = "group_contact1_no_messages@g.us"
        self.chat_contact1_group_no_timestamp_jid = "group_contact1_no_ts@g.us"

        # Chat structure remains largely the same, no major changes needed here.
        DB["chats"] = {
            self.chat_contact1_direct_messages_jid: {
                "chat_jid": self.chat_contact1_direct_messages_jid, "name": "Contact One", "is_group": False,
                "last_active_timestamp": self.ts_chat1_msg2, "unread_count": 1,
                "is_archived": False, "is_pinned": False, "is_muted_until": None, "messages": [
                    {"message_id": "c1d_msg1", "chat_jid": self.chat_contact1_direct_messages_jid, "sender_jid": self.user_jid, "sender_name": "Current User", "timestamp": self.ts_chat1_msg1, "text_content": "Hi Contact One", "is_outgoing": True},
                    {"message_id": "c1d_msg2", "chat_jid": self.chat_contact1_direct_messages_jid, "sender_jid": self.contact1_jid, "sender_name": "Contact One", "timestamp": self.ts_chat1_msg2, "text_content": "Hello User", "is_outgoing": False, "media_info": {"media_type": "image", "file_name": "image.jpg"}}
                ]
            },
            self.chat_contact1_group_messages_jid: {
                "chat_jid": self.chat_contact1_group_messages_jid, "name": "Test Group C1", "is_group": True,
                "last_active_timestamp": self.ts_chat2_msg1, "unread_count": 0,
                "is_archived": False, "is_pinned": False, "is_muted_until": None,
                "group_metadata": {"participants_count": 2, "participants": [{"jid": self.contact1_jid, "is_admin": False}, {"jid": self.contact2_jid, "is_admin": True}]},
                "messages": [{"message_id": "c1g_msg1", "chat_jid": self.chat_contact1_group_messages_jid, "sender_jid": self.contact2_jid, "sender_name": "Contact Two", "timestamp": self.ts_chat2_msg1, "text_content": "Group message", "is_outgoing": False}]
            },
            self.chat_contact1_group_no_messages_jid: {
                "chat_jid": self.chat_contact1_group_no_messages_jid, "name": "Empty Group C1", "is_group": True,
                "last_active_timestamp": self.ts_chat3_msg1, "unread_count": 0,
                "is_archived": False, "is_pinned": False, "is_muted_until": None,
                "group_metadata": {"participants_count": 1, "participants": [{"jid": self.contact1_jid, "is_admin": False}]},
                "messages": []
            },
            self.chat_contact1_group_no_timestamp_jid: {
                "chat_jid": self.chat_contact1_group_no_timestamp_jid, "name": "Group No Timestamp C1", "is_group": True,
                "last_active_timestamp": None, "unread_count": 0,
                "is_archived": False, "is_pinned": False, "is_muted_until": None,
                "group_metadata": {"participants_count": 1, "participants": [{"jid": self.contact1_jid, "is_admin": False}]},
                "messages": []
            },
            self.contact2_jid: {
                "chat_jid": self.contact2_jid, "name": "Contact Two", "is_group": False,
                "last_active_timestamp": self.ts_chat_other_contact, "unread_count": 0,
                "is_archived": False, "is_pinned": False, "is_muted_until": None,
                "messages": [{"message_id": "c2d_msg1", "chat_jid": self.contact2_jid, "sender_jid": self.contact2_jid, "sender_name": "Contact Two", "timestamp": self.ts_chat_other_contact, "text_content": "DM to user", "is_outgoing": False}]
            },
            "group_other@g.us": {
                "chat_jid": "group_other@g.us", "name": "Other Group", "is_group": True,
                "last_active_timestamp": "2023-01-01T08:00:00Z", "unread_count": 0,
                "is_archived": False, "is_pinned": False, "is_muted_until": None,
                "group_metadata": {"participants_count": 1, "participants": [{"jid": self.contact2_jid, "is_admin": False}]},
                "messages": []
            }
        }
        self.expected_contact1_chat_jids_sorted = [
            self.chat_contact1_direct_messages_jid,
            self.chat_contact1_group_messages_jid,
            self.chat_contact1_group_no_messages_jid,
            self.chat_contact1_group_no_timestamp_jid,
        ]
        self.total_chats_for_contact1 = len(self.expected_contact1_chat_jids_sorted)
        DB['actions'] = []

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)


    def _assert_chat_info_structure(self, chat_info):
        # This helper method is already correct, no changes needed.
        self.assertIsInstance(chat_info, dict)
        self.assertIn("chat_jid", chat_info)
        self.assertIsInstance(chat_info["chat_jid"], str)
        self.assertIn("name", chat_info)
        if chat_info["name"] is not None: self.assertIsInstance(chat_info["name"], str)
        self.assertIn("is_group", chat_info)
        self.assertIsInstance(chat_info["is_group"], bool)
        self.assertIn("last_active_timestamp", chat_info)
        if chat_info["last_active_timestamp"] is not None: self.assertIsInstance(chat_info["last_active_timestamp"], str)
        self.assertIn("unread_count", chat_info)
        self.assertIsInstance(chat_info["unread_count"], int)
        self.assertIn("last_message_preview", chat_info)
        if chat_info["last_message_preview"] is not None:
            self._assert_last_message_preview_structure(chat_info["last_message_preview"])

    def _assert_last_message_preview_structure(self, preview):
        self.assertIsInstance(preview, dict)
        self.assertIn("message_id", preview); self.assertIsInstance(preview["message_id"], str)
        self.assertIn("text_snippet", preview) # Can be None or str
        if preview["text_snippet"] is not None: self.assertIsInstance(preview["text_snippet"], str)
        self.assertIn("sender_name", preview) # Can be None or str
        if preview["sender_name"] is not None: self.assertIsInstance(preview["sender_name"], str)
        self.assertIn("timestamp", preview); self.assertIsInstance(preview["timestamp"], str)
        self.assertIn("is_outgoing", preview); self.assertIsInstance(preview["is_outgoing"], bool)


class TestGetContactChatsSuccess(TestGetContactChatsBase, BaseTestCaseWithErrorHandler):

    def test_get_contact_chats_basic_defaults(self):
        result = get_contact_chats(jid=self.contact1_jid)
        self.assertEqual(result["total_chats"], self.total_chats_for_contact1)
        self.assertEqual(result["limit"], 20)
        self.assertEqual(result["page"], 0)
        self.assertEqual(len(result["chats"]), self.total_chats_for_contact1)

        returned_jids = [c["chat_jid"] for c in result["chats"]]
        self.assertEqual(returned_jids, self.expected_contact1_chat_jids_sorted)
        for chat_info in result["chats"]: self._assert_chat_info_structure(chat_info)

    def test_get_contact_chats_custom_limit_page(self):
        result = get_contact_chats(jid=self.contact1_jid, limit=1, page=1)
        self.assertEqual(result["total_chats"], self.total_chats_for_contact1)
        self.assertEqual(result["limit"], 1)
        self.assertEqual(result["page"], 1)
        self.assertEqual(len(result["chats"]), 1)
        self.assertEqual(result["chats"][0]["chat_jid"], self.expected_contact1_chat_jids_sorted[1])
        self._assert_chat_info_structure(result["chats"][0])

    def test_get_contact_chats_pagination_first_page_limit_2(self):
        result = get_contact_chats(jid=self.contact1_jid, limit=2, page=0)
        self.assertEqual(result["total_chats"], self.total_chats_for_contact1)
        self.assertEqual(len(result["chats"]), 2)
        self.assertEqual(result["chats"][0]["chat_jid"], self.expected_contact1_chat_jids_sorted[0])
        self.assertEqual(result["chats"][1]["chat_jid"], self.expected_contact1_chat_jids_sorted[1])

    def test_get_contact_chats_pagination_second_page_limit_2(self):
        result = get_contact_chats(jid=self.contact1_jid, limit=2, page=1)
        self.assertEqual(result["total_chats"], self.total_chats_for_contact1)
        self.assertEqual(len(result["chats"]), 2) # Now 2 chats on page 1 (items 3 and 4)
        self.assertEqual(result["chats"][0]["chat_jid"], self.expected_contact1_chat_jids_sorted[2])
        self.assertEqual(result["chats"][1]["chat_jid"], self.expected_contact1_chat_jids_sorted[3])

    def test_get_contact_chats_limit_exceeds_total(self):
        result = get_contact_chats(jid=self.contact1_jid, limit=100, page=0)
        self.assertEqual(result["total_chats"], self.total_chats_for_contact1)
        self.assertEqual(len(result["chats"]), self.total_chats_for_contact1)

    def test_get_contact_chats_contact_with_no_chats(self):
        result = get_contact_chats(jid=self.contact3_jid)
        self.assertEqual(result["total_chats"], 0)
        self.assertEqual(len(result["chats"]), 0)

    def test_get_contact_chats_chat_details_direct_chat_with_messages(self):
        result = get_contact_chats(jid=self.contact1_jid, limit=1, page=0)
        chat_info = result["chats"][0]
        self.assertEqual(chat_info["chat_jid"], self.chat_contact1_direct_messages_jid)
        self.assertEqual(chat_info["name"], "Contact One")
        self.assertFalse(chat_info["is_group"])
        self.assertEqual(chat_info["last_active_timestamp"], self.ts_chat1_msg2)
        self.assertEqual(chat_info["unread_count"], 1)
        preview = chat_info["last_message_preview"]
        self.assertIsNotNone(preview)
        self.assertEqual(preview["message_id"], "c1d_msg2")
        self.assertEqual(preview["text_snippet"], "Hello User")
        self.assertEqual(preview["sender_name"], "Contact One")
        self.assertEqual(preview["timestamp"], self.ts_chat1_msg2)
        self.assertFalse(preview["is_outgoing"])

    def test_get_contact_chats_chat_details_group_chat_with_messages(self):
        result = get_contact_chats(jid=self.contact1_jid, limit=1, page=1)
        chat_info = result["chats"][0]
        self.assertEqual(chat_info["chat_jid"], self.chat_contact1_group_messages_jid)
        self.assertEqual(chat_info["name"], "Test Group C1")
        self.assertTrue(chat_info["is_group"])
        preview = chat_info["last_message_preview"]
        self.assertIsNotNone(preview)
        self.assertEqual(preview["text_snippet"], "Group message")

    def test_get_contact_chats_chat_details_group_chat_no_messages(self):
        result = get_contact_chats(jid=self.contact1_jid, limit=1, page=2)
        chat_info = result["chats"][0]
        self.assertEqual(chat_info["chat_jid"], self.chat_contact1_group_no_messages_jid)
        self.assertEqual(chat_info["name"], "Empty Group C1")
        self.assertTrue(chat_info["is_group"])
        self.assertEqual(chat_info["last_active_timestamp"], self.ts_chat3_msg1)
        self.assertIsNone(chat_info["last_message_preview"])

    def test_get_contact_chats_chat_details_group_chat_no_timestamp(self):
        result = get_contact_chats(jid=self.contact1_jid, limit=1, page=3)
        chat_info = result["chats"][0]
        self.assertEqual(chat_info["chat_jid"], self.chat_contact1_group_no_timestamp_jid)
        self.assertEqual(chat_info["name"], "Group No Timestamp C1")
        self.assertTrue(chat_info["is_group"])
        self.assertIsNone(chat_info["last_active_timestamp"])
        self.assertIsNone(chat_info["last_message_preview"])

    def test_get_contact_chats_media_message_preview_caption_used(self):
        chat_target_jid = self.chat_contact1_direct_messages_jid
        original_message = DB["chats"][chat_target_jid]["messages"][-1]
        
        modified_message = original_message.copy()
        modified_message["text_content"] = None
        modified_message["media_info"] = {"media_type": "video", "file_name": "video.mp4", "caption": "Fun times"}
        DB["chats"][chat_target_jid]["messages"][-1] = modified_message

        result = get_contact_chats(jid=self.contact1_jid, limit=1, page=0)
        preview = result["chats"][0]["last_message_preview"]
        self.assertIsNotNone(preview)
        self.assertEqual(preview["text_snippet"], "Fun times")
        
        DB["chats"][chat_target_jid]["messages"][-1] = original_message # Restore

    def test_sender_name_resolution_logic(self):
        """
        Tests sender_name resolution. This test needs to be updated to modify
        the NEW contact structure in the DB.
        """
        chat_target_jid = self.chat_contact1_direct_messages_jid
        contact_resource_name = f"people/{self.contact1_jid}"

        # --- Backup original state ---
        original_message = copy.deepcopy(DB["chats"][chat_target_jid]["messages"][-1])
        original_contact_data = copy.deepcopy(DB["contacts"][contact_resource_name])

        try:
            # Setup for all subtests: Ensure sender_name is None in the message object
            modified_message = original_message.copy()
            modified_message["sender_name"] = None
            DB["chats"][chat_target_jid]["messages"][-1] = modified_message

            # --- Subtest 1: 'name_in_address_book' is prioritized ---
            with self.subTest(case="'name_in_address_book' is used"):
                DB["contacts"][contact_resource_name] = copy.deepcopy(original_contact_data)
                result = get_contact_chats(jid=self.contact1_jid, limit=1, page=0)
                preview = result["chats"][0]["last_message_preview"]
                self.assertIsNotNone(preview)
                self.assertEqual(preview["sender_name"], "C One")

            # --- Subtest 2: 'profile_name' is used as a fallback ---
            with self.subTest(case="'profile_name' is used as fallback"):
                modified_contact = copy.deepcopy(original_contact_data)
                modified_contact["whatsapp"]["name_in_address_book"] = None # Modify new structure
                DB["contacts"][contact_resource_name] = modified_contact
                result = get_contact_chats(jid=self.contact1_jid, limit=1, page=0)
                preview = result["chats"][0]["last_message_preview"]
                self.assertIsNotNone(preview)
                self.assertEqual(preview["sender_name"], "Contact One")

            # --- Subtest 3: No name is available for the contact ---
            with self.subTest(case="No name available for existing contact"):
                modified_contact = copy.deepcopy(original_contact_data)
                modified_contact["whatsapp"]["name_in_address_book"] = None # Modify new structure
                modified_contact["whatsapp"]["profile_name"] = None # Modify new structure
                DB["contacts"][contact_resource_name] = modified_contact
                result = get_contact_chats(jid=self.contact1_jid, limit=1, page=0)
                preview = result["chats"][0]["last_message_preview"]
                self.assertIsNotNone(preview)
                self.assertIsNone(preview["sender_name"])

            # --- Subtest 4: Sender JID does not exist in contacts ---
            with self.subTest(case="Sender JID not in contacts"):
                DB["contacts"][contact_resource_name] = copy.deepcopy(original_contact_data) # Restore contact
                unknown_sender_jid = "unknown@s.whatsapp.net"
                modified_message_unknown_sender = modified_message.copy()
                modified_message_unknown_sender["sender_jid"] = unknown_sender_jid
                DB["chats"][chat_target_jid]["messages"][-1] = modified_message_unknown_sender
                result = get_contact_chats(jid=self.contact1_jid, limit=1, page=0)
                preview = result["chats"][0]["last_message_preview"]
                self.assertIsNotNone(preview)
                self.assertIsNone(preview["sender_name"])

        finally:
            # --- Restore original state ---
            DB["chats"][chat_target_jid]["messages"][-1] = original_message
            DB["contacts"][contact_resource_name] = original_contact_data
    
    def test_get_contact_chats_media_preview_placeholders_non_enum_path(self):
        """
        Tests the media placeholder logic that uses plain strings (the fallback path).
        This is achieved by patching models.MediaType to be a non-Enum class.
        """
        chat_target_jid = self.chat_contact1_direct_messages_jid
        original_message = copy.deepcopy(DB["chats"][chat_target_jid]["messages"][-1])

        # A mock class that is NOT an Enum, to force the 'else' block in utils.py
        class MockMediaType:
            pass

        media_types_to_test = [
            ("image", "Photo"),
            ("video", "Video"),
            ("audio", "Audio"),
            ("document", "Document"),
            ("sticker", "Sticker"),
            ("unknown_type", "Media"),  # Fallback case
        ]
        
        # Patch models.MediaType within the utils module's scope
        with patch('whatsapp.SimulationEngine.utils.models.MediaType', MockMediaType):
            try:
                for media_type, expected_snippet in media_types_to_test:
                    with self.subTest(media_type=media_type):
                        modified_message = original_message.copy()
                        modified_message["text_content"] = None
                        modified_message["media_info"] = {
                            "media_type": media_type,
                            "file_name": f"file.{media_type}",
                            "caption": None
                        }
                        DB["chats"][chat_target_jid]["messages"][-1] = modified_message

                        result = get_contact_chats(jid=self.contact1_jid, limit=1, page=0)
                        preview = result["chats"][0]["last_message_preview"]
                        
                        self.assertIsNotNone(preview)
                        self.assertEqual(preview["text_snippet"], expected_snippet)
            finally:
                # Restore the DB state
                DB["chats"][chat_target_jid]["messages"][-1] = original_message
    
    def test_get_contact_chats_media_message_preview_placeholders(self):
        chat_target_jid = self.chat_contact1_direct_messages_jid
        original_message = copy.deepcopy(DB["chats"][chat_target_jid]["messages"][-1])

        media_types_to_test = [
            (models.MediaType.IMAGE.value, "Photo"),
            (models.MediaType.VIDEO.value, "Video"),
            (models.MediaType.AUDIO.value, "Audio"),
            (models.MediaType.DOCUMENT.value, "Document"),
            (models.MediaType.STICKER.value, "Sticker"),
            ("some_other_media_type", "Media"), # Fallback case
        ]

        for media_type, expected_snippet in media_types_to_test:
            with self.subTest(media_type=media_type):
                # Modify the last message for the specific media type
                modified_message = original_message.copy()
                modified_message["text_content"] = None
                modified_message["media_info"] = {"media_type": media_type, "file_name": f"file.{media_type}", "caption": None}
                DB["chats"][chat_target_jid]["messages"][-1] = modified_message

                # Call the function and get the preview
                result = get_contact_chats(jid=self.contact1_jid, limit=1, page=0)
                preview = result["chats"][0]["last_message_preview"]
                
                # Assertions
                self.assertIsNotNone(preview)
                self.assertEqual(preview["text_snippet"], expected_snippet)

        # Restore the original message after the loop
        DB["chats"][chat_target_jid]["messages"][-1] = original_message
    
    def test_uses_pydantic_model_for_validation(self):
        """
        Verifies that the function uses the ContactChatsResponse Pydantic model
        for validation before returning the final dictionary.
        """
        # The model is imported into the same module as the function being tested,
        # so we patch it in that namespace.
        target_module = get_contact_chats.__module__
        with patch(f'{target_module}.ContactChatsResponse') as MockContactChatsResponse:
            mock_instance = MockContactChatsResponse.return_value
            mock_instance.model_dump.return_value = {"status": "validated_and_dumped"}

            # Call the function we are testing
            result = get_contact_chats(jid=self.contact1_jid)

            # 1. Assert that the Pydantic model was instantiated exactly once.
            MockContactChatsResponse.assert_called_once()

            # 2. Assert that the model was instantiated with the correct data.
            # call_args[1] is the dictionary of keyword arguments passed to the constructor.
            call_kwargs = MockContactChatsResponse.call_args[1]
            
            self.assertEqual(call_kwargs['total_chats'], self.total_chats_for_contact1)
            self.assertEqual(call_kwargs['page'], 0)  # Default page
            self.assertEqual(call_kwargs['limit'], 20) # Default limit
            
            # Verify the chats data passed to the model is correct and sorted.
            self.assertEqual(len(call_kwargs['chats']), self.total_chats_for_contact1)
            returned_jids_for_model = [c["chat_jid"] for c in call_kwargs['chats']]
            self.assertEqual(returned_jids_for_model, self.expected_contact1_chat_jids_sorted)

            # 3. Assert that the model_dump() method was called on the instance.
            mock_instance.model_dump.assert_called_once()

            # 4. Assert that the function returned the result from model_dump().
            self.assertEqual(result, {"status": "validated_and_dumped"})


class TestGetContactChatsErrorHandling(TestGetContactChatsBase, BaseTestCaseWithErrorHandler):

    def test_get_contact_chats_contact_not_found(self):
        self.assert_error_behavior(
            func_to_call=get_contact_chats,
            jid="nonexistent@s.whatsapp.net",
            expected_exception_type=custom_errors.ContactNotFoundError,
            expected_message="The specified contact could not be found."
        )

    def test_get_contact_chats_invalid_jid_format(self):
        self.assert_error_behavior(
            func_to_call=get_contact_chats,
            jid="invalidjid",
            expected_exception_type=custom_errors.InvalidJIDError,
            expected_message="The provided JID has an invalid format."
        )

    def test_get_contact_chats_invalid_limit_negative(self):
        self.assert_error_behavior(
            func_to_call=get_contact_chats,
            jid=self.contact1_jid, limit=-1,
            expected_exception_type=custom_errors.InvalidParameterError,
            expected_message="Input should be greater than 0" # CORRECTED
        )

    def test_get_contact_chats_invalid_limit_zero(self):
        self.assert_error_behavior(
            func_to_call=get_contact_chats,
            jid=self.contact1_jid, limit=0,
            expected_exception_type=custom_errors.InvalidParameterError,
            expected_message="Input should be greater than 0" # CORRECTED
        )

    def test_get_contact_chats_invalid_limit_string(self):
        self.assert_error_behavior(
            func_to_call=get_contact_chats,
            jid=self.contact1_jid, limit="abc",
            expected_exception_type=custom_errors.InvalidParameterError,
            expected_message="Input should be a valid integer, unable to parse string as an integer" # CORRECTED
        )

    def test_get_contact_chats_invalid_page_negative(self):
        self.assert_error_behavior(
            func_to_call=get_contact_chats,
            jid=self.contact1_jid, page=-1,
            expected_exception_type=custom_errors.InvalidParameterError,
            expected_message="Input should be greater than or equal to 0" # CORRECTED
        )

    def test_get_contact_chats_invalid_page_string(self):
        self.assert_error_behavior(
            func_to_call=get_contact_chats,
            jid=self.contact1_jid, page="abc",
            expected_exception_type=custom_errors.InvalidParameterError,
            expected_message="Input should be a valid integer, unable to parse string as an integer" # CORRECTED
        )
    
    def test_get_contact_chats_pagination_page_out_of_bounds(self):
        # Total 4 chats, limit 2. Page 0 (2), Page 1 (2). Page 2 is out of bounds.
        self.assert_error_behavior(
            func_to_call=get_contact_chats,
            jid=self.contact1_jid,
            limit=2,
            page=2,
            expected_exception_type=custom_errors.PaginationError,
            expected_message="Requested page is out of range."
        )


class TestSearchContacts(BaseTestCaseWithErrorHandler):

    def setUp(self):
        """
        Set up the test environment by saving the original DB state and
        populating it with test contacts conforming to the new PersonContact structure.
        """
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        
        # Define contacts using the new, richer PersonContact structure.
        # The key is the 'resourceName' and the value is the contact object.
        DB['contacts'] = {
            '111@s.whatsapp.net': {
                # top‐level flat fields are no longer used by the new impl,
                # everything lives under "whatsapp", plus names/phoneNumbers
                'names': [
                    {'givenName': 'Alice', 'familyName': 'Wonderland'}
                ],
                'phoneNumbers': [
                    {'value': '1112223333', 'type': 'mobile', 'primary': True}
                ],
                'whatsapp': {
                    'jid': '111@s.whatsapp.net',
                    'name_in_address_book': 'Alice Wonderland',
                    'profile_name': 'AliceW',
                    'phone_number': '1112223333',
                    'is_whatsapp_user': True,
                }
            },
            '222@s.whatsapp.net': {
                'names': [
                    {'givenName': 'Bob', 'familyName': 'The Builder'}
                ],
                'phoneNumbers': [
                    {'value': '+44 222-333-4444', 'type': 'mobile', 'primary': True}
                ],
                'whatsapp': {
                    'jid': '222@s.whatsapp.net',
                    'name_in_address_book': 'Bob The Builder',
                    'profile_name': 'BobBuilds',
                    'phone_number': '+44 222-333-4444',
                    'is_whatsapp_user': True,
                }
            },
            '333@s.whatsapp.net': {
                'names': [
                    {'givenName': 'Charlie', 'familyName': 'Chaplin'}
                ],
                'phoneNumbers': [
                    {'value': '3334445555', 'type': 'mobile', 'primary': True}
                ],
                'whatsapp': {
                    'jid': '333@s.whatsapp.net',
                    'name_in_address_book': 'Charlie Chaplin',
                    'profile_name': 'CharlieC',
                    'phone_number': '3334445555',
                    'is_whatsapp_user': False,
                }
            },
            '404@s.whatsapp.net': {
                # no top‐level name_in_address_book
                'names': [], 
                'phoneNumbers': [
                    {'value': '4045056060', 'type': 'mobile', 'primary': True}
                ],
                'whatsapp': {
                    'jid': '404@s.whatsapp.net',
                    # missing name_in_address_book → should default to ""
                    'profile_name': 'Missing ProfileName',
                    'phone_number': '4045056060',
                    'is_whatsapp_user': True,
                }
            },
            '555@s.whatsapp.net': {
                'names': [],
                'phoneNumbers': [],
                'whatsapp': {
                    'jid': '555@s.whatsapp.net',
                    # both name_in_address_book and phone_number missing
                    'profile_name': 'MinimalContact',
                    'is_whatsapp_user': True,
                }
            },
            '666@s.whatsapp.net': {
                'names': [
                    {'givenName': 'Dr.', 'familyName': 'Phone Test-Smith'}
                ],
                'phoneNumbers': [
                    {'value': '+1 (666) 777-8888', 'type': 'mobile', 'primary': True}
                ],
                'whatsapp': {
                    'jid': '666@s.whatsapp.net',
                    'name_in_address_book': 'Dr. Phone Test-Smith',
                    'profile_name': 'PhoneP',
                    'phone_number': '+1 (666) 777-8888',
                    'is_whatsapp_user': True,
                }
            },
            '777@s.whatsapp.net': {
                'names': [
                    {'givenName': 'Alicia', 'familyName': 'Keys'}
                ],
                'phoneNumbers': [
                    {'value': '7778889999', 'type': 'mobile', 'primary': True}
                ],
                'whatsapp': {
                    'jid': '777@s.whatsapp.net',
                    'name_in_address_book': 'Alicia Keys',
                    'profile_name': 'Alice K',
                    'phone_number': '7778889999',
                    'is_whatsapp_user': True,
                }
            }
        }

        DB['actions'] = []

    def tearDown(self):
        """
        Restore the original database state after each test.
        """
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_contact_in_results(self, results, expected_jid, msg_prefix=''):
        found = any((contact['jid'] == expected_jid for contact in results))
        self.assertTrue(found, f'{msg_prefix}Contact with JID {expected_jid} not found in results. Results: {results}')

    def _get_contact_from_results(self, results, jid_to_find):
        for contact in results:
            if contact['jid'] == jid_to_find:
                return contact
        return None

    def _assert_contact_details(self, result_contact, expected_db_contact_data):
        self.assertIsNotNone(
            result_contact,
            f"Expected to find {expected_db_contact_data['whatsapp']['jid']}"
        )
        wa = expected_db_contact_data['whatsapp']
        # missing name_in_address_book should be empty string
        self.assertEqual(result_contact['jid'], wa['jid'])
        self.assertEqual(result_contact.get('name_in_address_book', None), wa.get('name_in_address_book', ''))
        self.assertEqual(result_contact.get('profile_name', None), wa.get('profile_name', None))
        self.assertEqual(result_contact.get('phone_number', None), wa.get('phone_number', None))
        self.assertEqual(result_contact['is_whatsapp_user'], wa['is_whatsapp_user'])


    def test_search_by_full_name_in_address_book(self):
        results = search_contacts(query='Alice Wonderland')
        self.assertEqual(len(results), 1)
        rc = self._get_contact_from_results(results, '111@s.whatsapp.net')
        self._assert_contact_details(rc, DB['contacts']['111@s.whatsapp.net'])

    def test_search_by_partial_name_in_address_book(self):
        results = search_contacts(query='Alice')
        self.assertEqual(len(results), 2)
        self._assert_contact_in_results(results, '111@s.whatsapp.net')
        self._assert_contact_in_results(results, '777@s.whatsapp.net')

    def test_search_by_name_with_hyphen_and_period(self):
        results_full = search_contacts(query='Dr. Phone Test-Smith')
        self.assertEqual(len(results_full), 1)
        self._assert_contact_in_results(results_full, '666@s.whatsapp.net', 'Full name search: ')
        results_partial = search_contacts(query='Phone Test')
        self.assertEqual(len(results_partial), 1)
        self._assert_contact_in_results(results_partial, '666@s.whatsapp.net', 'Partial name search: ')

    def test_search_by_full_profile_name(self):
        results = search_contacts(query='BobBuilds')
        self.assertEqual(len(results), 1)
        self._assert_contact_in_results(results, '222@s.whatsapp.net')

    def test_search_by_partial_profile_name(self):
        results = search_contacts(query='BobB')
        self.assertEqual(len(results), 1)
        self._assert_contact_in_results(results, '222@s.whatsapp.net')

    def test_search_by_full_phone_number_digits_only(self):
        results = search_contacts(query='1112223333')
        self.assertEqual(len(results), 1)
        self._assert_contact_in_results(results, '111@s.whatsapp.net')

    def test_search_by_partial_phone_number_digits_only(self):
        results = search_contacts(query='222333')
        self.assertEqual(len(results), 2)
        self._assert_contact_in_results(results, '111@s.whatsapp.net')
        self._assert_contact_in_results(results, '222@s.whatsapp.net')

    def test_search_by_phone_number_with_symbols_exact_match_after_cleaning(self):
        results = search_contacts(query='+44 222-333-4444')
        self.assertEqual(len(results), 1)
        self._assert_contact_in_results(results, '222@s.whatsapp.net')

    def test_search_by_phone_number_with_us_format_symbols(self):
        results = search_contacts(query='+1 (666) 777-8888')
        self.assertEqual(len(results), 1)
        self._assert_contact_in_results(results, '666@s.whatsapp.net')

    def test_search_by_partial_phone_number_with_symbols_in_db(self):
        results_paren = search_contacts(query='(666)')
        self.assertEqual(len(results_paren), 1)
        self._assert_contact_in_results(results_paren, '666@s.whatsapp.net', 'Paren query: ')
        results_hyphen = search_contacts(query='777-8888')
        self.assertEqual(len(results_hyphen), 1)
        self._assert_contact_in_results(results_hyphen, '666@s.whatsapp.net', 'Hyphen query: ')

    def test_search_case_insensitive_name_in_address_book(self):
        results = search_contacts(query='alice wonderland')
        self.assertEqual(len(results), 1)
        self._assert_contact_in_results(results, '111@s.whatsapp.net')

    def test_search_case_insensitive_profile_name(self):
        results = search_contacts(query='alicew')
        self.assertEqual(len(results), 1)
        self._assert_contact_in_results(results, '111@s.whatsapp.net')
        results_ak = search_contacts(query='alice k')
        self.assertEqual(len(results_ak), 1)
        self._assert_contact_in_results(results_ak, '777@s.whatsapp.net')

    def test_search_query_matches_one_contact_on_name_and_profile(self):
        results = search_contacts(query='Charlie')
        self.assertEqual(len(results), 1)
        self._assert_contact_in_results(results, '333@s.whatsapp.net')

    def test_search_query_matches_multiple_contacts_different_fields(self):
        results = search_contacts(query='Alice')
        self.assertEqual(len(results), 2)
        jids = {contact['jid'] for contact in results}
        self.assertIn('111@s.whatsapp.net', jids)
        self.assertIn('777@s.whatsapp.net', jids)

    def test_search_no_results_for_query(self):
        results = search_contacts(query='NonExistentNameOrNumber')
        self.assertEqual(len(results), 0)

    def test_search_contact_with_missing_name_in_address_book(self):
        results = search_contacts(query='Missing ProfileName')
        self.assertEqual(len(results), 1)
        contact_data = self._get_contact_from_results(results, '404@s.whatsapp.net')
        self.assertIsNotNone(contact_data)
        # Verify the key exists but its value is None, reflecting Pydantic's behavior.
        self.assertIn('name_in_address_book', contact_data)
        self.assertEqual(contact_data['name_in_address_book'], "")
        self.assertEqual(contact_data.get('profile_name'), 'Missing ProfileName')

    def test_search_contact_with_missing_phone_and_address_book_name(self):
        results = search_contacts(query='MinimalContact')
        self.assertEqual(len(results), 1)
        contact_data = self._get_contact_from_results(results, '555@s.whatsapp.net')
        self.assertIsNotNone(contact_data)
        # Verify keys for optional fields now exist with a value of None.
        self.assertEqual(contact_data['name_in_address_book'], "")
        self.assertIsNone(contact_data['phone_number'])
        self.assertEqual(contact_data.get('profile_name'), 'MinimalContact')

    def test_search_returns_correct_is_whatsapp_user_flag(self):
        results_charlie = search_contacts(query='Charlie Chaplin')
        self.assertEqual(len(results_charlie), 1)
        self.assertFalse(results_charlie[0]['is_whatsapp_user'])
        results_alice = search_contacts(query='Alice Wonderland')
        self.assertEqual(len(results_alice), 1)
        self.assertTrue(results_alice[0]['is_whatsapp_user'])

    def test_search_with_single_character_query(self):
        results = search_contacts(query='A')
        self.assertEqual(len(results), 5)
        jids = {contact['jid'] for contact in results}
        self.assertIn('111@s.whatsapp.net', jids) # Alice
        self.assertIn('777@s.whatsapp.net', jids) # Alicia
        self.assertIn('333@s.whatsapp.net', jids) # Charlie
        self.assertIn('404@s.whatsapp.net', jids) # Name
        self.assertIn('555@s.whatsapp.net', jids) # MinimalContact

    def test_search_empty_contacts_db(self):
        DB['contacts'] = {}
        results = search_contacts(query='Alice')
        self.assertEqual(len(results), 0)

    def test_search_contacts_db_is_none_safe(self):
        DB['contacts'] = None
        results = search_contacts(query='Alice')
        self.assertEqual(len(results), 0)

    def test_search_contacts_db_is_list_safe(self):
        DB['contacts'] = []
        results = search_contacts(query='Alice')
        self.assertEqual(len(results), 0)

    def test_search_contact_entry_not_a_dict_safe(self):
        DB['contacts']['888@s.whatsapp.net'] = 'not a dict string'
        results = search_contacts(query='Alice Wonderland')
        self.assertEqual(len(results), 1)
        self._assert_contact_in_results(results, '111@s.whatsapp.net')
        results_alice = search_contacts(query='Alice')
        self.assertEqual(len(results_alice), 2)

    def test_search_invalid_query_empty_string_raises_invalidqueryerror(self):
        self.assert_error_behavior(func_to_call=search_contacts,
                                   expected_exception_type=custom_errors.InvalidQueryError,
                                   expected_message="Input validation failed: String should have at least 1 character",
                                   query='')

    def test_search_invalid_query_whitespace_string_raises_invalidqueryerror(self):
        self.assert_error_behavior(func_to_call=search_contacts,
                                   expected_exception_type=custom_errors.InvalidQueryError,
                                   expected_message="Input validation failed: Value error, Query cannot be empty or contain only whitespace",
                                   query='   ')

    def test_search_query_is_none_raises_validation_error(self):
        self.assert_error_behavior(func_to_call=search_contacts,
                                   expected_exception_type=custom_errors.InvalidQueryError,
                                   expected_message="Input validation failed: Input should be a valid string",
                                   query=None)

    def test_search_query_is_not_string_raises_validation_error(self):
        self.assert_error_behavior(func_to_call=search_contacts,
                                   expected_exception_type=custom_errors.InvalidQueryError,
                                   expected_message="Input validation failed: Input should be a valid string",
                                   query=123)

    def test_search_finds_malformed_contact_raises_pydantic_error(self):
        """
        Tests that Pydantic validation is active on search results.
        This test adds a contact with a malformed 'whatsapp' object (missing
        the required 'jid' field) to the database. When the search function
        finds this contact, the validation step on the result should fail.
        """
        # Arrange: Add a malformed contact using the NEW DB structure.
        malformed_contact_resourcename = 'people/999@s.whatsapp.net'
        DB['contacts'][malformed_contact_resourcename] = {
            'resourceName': malformed_contact_resourcename,
            'names': [{'givenName': 'Malformed', 'familyName': 'Contact Data'}],
            'whatsapp': {
                # 'jid' is intentionally omitted to cause a Pydantic validation error.
                'name_in_address_book': 'Malformed Contact Data',
                'profile_name': 'BadData',
                'is_whatsapp_user': True
            }
        }

        # Act & Assert: The search should find the contact, but validating it
        # against the WhatsappContact model should raise an error.
        with self.assertRaises(PydanticValidationError, msg="A malformed contact from DB should raise a ValidationError during result processing."):
            search_contacts(query='Malformed Contact')
    
    def test_search_skips_contact_with_empty_whatsapp_object(self):
        """Contacts that have an explicitly empty 'whatsapp' object should be skipped."""
        # Arrange: add a contact that would match by name, but with empty whatsapp {}
        empty_wa_resource = 'people/empty-wa-001'
        DB['contacts'][empty_wa_resource] = {
            'resourceName': empty_wa_resource,
            'names': [{'givenName': 'Empty', 'familyName': 'WhatsApp'}],
            'phoneNumbers': [{'value': '+1 999-888-7777'}],
            'whatsapp': {}
        }

        # Act: Search by name and by phone digits
        res_by_name = search_contacts(query='Empty WhatsApp')
        res_by_digits = search_contacts(query='9998887777')

        # Assert: neither search should include this contact
        self.assertEqual(len(res_by_name), 0, f"Should skip contacts with empty whatsapp object. Results: {res_by_name}")
        self.assertEqual(len(res_by_digits), 0, f"Should skip contacts with empty whatsapp object even when phone matches. Results: {res_by_digits}")

    def test_search_skips_contact_with_missing_whatsapp_key(self):
        """Contacts missing the 'whatsapp' key entirely should be skipped."""
        # Arrange: add a contact without a 'whatsapp' key, but with matching name and phone
        no_wa_resource = 'people/no-wa-002'
        DB['contacts'][no_wa_resource] = {
            'resourceName': no_wa_resource,
            'names': [{'givenName': 'No', 'familyName': 'WhatsApp'}],
            'phoneNumbers': [{'value': '+44 123-456-7890'}]
        }

        # Act
        res_by_name = search_contacts(query='No WhatsApp')
        res_by_digits = search_contacts(query='1234567890')

        # Assert
        self.assertEqual(len(res_by_name), 0, f"Should skip contacts missing whatsapp key. Results: {res_by_name}")
        self.assertEqual(len(res_by_digits), 0, f"Should skip contacts missing whatsapp key even when phone matches. Results: {res_by_digits}")
    
    def test_Gemini_Apps_ID_253(self):
        """
        Test for Gemini Apps ID 253: https://colab.research.google.com/drive/1NK_h1cKHesrwfnl3ypXodS1F0mTcicIT#scrollTo=cnnkr2Z4Y905
        """
        DB['contacts']['people/ca1410090-3c7e-480f-8b52-c95264c3caea'] = {'resourceName': 'people/ca1410090-3c7e-480f-8b52-c95264c3caea',
            'etag': 'af51a9898a8b4d97b35a55a86d1eeffb',
            'names': [{'givenName': 'Ily'}],
            'phoneNumbers': [{'value': '0195209634', 'type': 'mobile', 'primary': True}],
            'whatsapp': {'is_whatsapp_user': True,
            'jid': '0195209634@s.whatsapp.net',
            'phone_number': '0195209634',
            'name_in_address_book': 'Ily',
            'profile_name': 'Ily'},
            'phone': {'contact_id': 'people/ca1410090-3c7e-480f-8b52-c95264c3caea',
            'contact_name': 'Ily',
            'recipient_type': 'CONTACT',
            'contact_endpoints': [{'endpoint_type': 'PHONE_NUMBER',
                'endpoint_value': '0195209634',
                'endpoint_label': 'mobile'}]}}
        contacts = search_contacts("Ily")
        self.assertEqual(len(contacts), 1)
        self.assertEqual(contacts[0]['jid'], '0195209634@s.whatsapp.net')
        self.assertEqual(contacts[0]['name_in_address_book'], 'Ily')
        self.assertEqual(contacts[0]['profile_name'], 'Ily')
        self.assertEqual(contacts[0]['phone_number'], '0195209634')
        self.assertEqual(contacts[0]['is_whatsapp_user'], True)


class TestDatabaseUtilityFunctions(BaseTestCaseWithErrorHandler):
    """Test cases for database utility functions in utils.py"""

    def setUp(self):
        super().setUp()
        DB.clear()
        DB['chats'] = {}
        DB['contacts'] = {}

    def test_get_chat_data_success(self):
        """Test successful retrieval of chat data."""
        chat_jid = "1234567890@s.whatsapp.net"
        test_chat_data = {
            "chat_jid": chat_jid,
            "is_group": False,
            "messages": [],
            "is_archived": False,
            "is_pinned": False,
            "unread_count": 0
        }
        
        DB['chats'][chat_jid] = test_chat_data
        
        result = utils.get_chat_data(chat_jid)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["chat_jid"], chat_jid)
        self.assertEqual(result["is_group"], False)

    def test_get_chat_data_not_found(self):
        """Test retrieval of non-existent chat data."""
        result = utils.get_chat_data("nonexistent@s.whatsapp.net")
        self.assertIsNone(result)

    def test_get_chat_data_invalid_db_structure(self):
        """Test handling of invalid database structure."""
        DB['chats'] = "invalid_structure"
        
        result = utils.get_chat_data("1234567890@s.whatsapp.net")
        self.assertIsNone(result)

    def test_list_all_chats_data_success(self):
        """Test successful listing of all chats."""
        chat1 = {"chat_jid": "chat1@s.whatsapp.net", "is_group": False}
        chat2 = {"chat_jid": "chat2@s.whatsapp.net", "is_group": True}
        
        DB['chats'] = {
            "chat1@s.whatsapp.net": chat1,
            "chat2@s.whatsapp.net": chat2
        }
        
        result = utils.list_all_chats_data()
        
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], dict)
        self.assertIsInstance(result[1], dict)

    def test_list_all_chats_data_empty_db(self):
        """Test listing chats when database is empty."""
        DB['chats'] = {}
        
        result = utils.list_all_chats_data()
        self.assertEqual(result, [])

    def test_list_all_chats_data_invalid_structure(self):
        """Test listing chats with invalid database structure."""
        DB['chats'] = "invalid_structure"
        
        result = utils.list_all_chats_data()
        self.assertEqual(result, [])

    def test_add_chat_data_success(self):
        """Test successful addition of chat data."""
        chat_data = {
            "chat_jid": "1234567890@s.whatsapp.net",
            "is_group": False,
            "messages": [],
            "is_archived": False,
            "is_pinned": False,
            "unread_count": 0
        }
        
        result = utils.add_chat_data(chat_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["chat_jid"], "1234567890@s.whatsapp.net")
        self.assertIn("1234567890@s.whatsapp.net", DB['chats'])

    def test_add_chat_data_duplicate(self):
        """Test adding duplicate chat data."""
        chat_data = {
            "chat_jid": "1234567890@s.whatsapp.net",
            "is_group": False
        }
        
        # Add the chat first time
        utils.add_chat_data(chat_data)
        
        # Try to add the same chat again
        result = utils.add_chat_data(chat_data)
        self.assertIsNone(result)

    def test_add_chat_data_invalid_input(self):
        """Test adding chat data with invalid input."""
        # Test with None
        result = utils.add_chat_data(None)
        self.assertIsNone(result)
        
        # Test with dict missing chat_jid
        result = utils.add_chat_data({"invalid": "data"})
        self.assertIsNone(result)

    def test_get_message_data_success(self):
        """Test successful retrieval of message data."""
        chat_jid = "1234567890@s.whatsapp.net"
        message_data = {
            "message_id": "msg_123",
            "chat_jid": chat_jid,
            "sender_jid": "1234567890@s.whatsapp.net",
            "text_content": "Hello World",
            "timestamp": "2024-01-01T12:00:00Z",
            "is_outgoing": False
        }
        
        DB['chats'][chat_jid] = {
            "messages": [message_data]
        }
        
        result = utils.get_message_data(chat_jid, "msg_123")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["message_id"], "msg_123")

    def test_get_message_data_chat_not_found(self):
        """Test message retrieval when chat doesn't exist."""
        result = utils.get_message_data("nonexistent@s.whatsapp.net", "msg_123")
        self.assertIsNone(result)

    def test_get_message_data_message_not_found(self):
        """Test message retrieval when message doesn't exist."""
        chat_jid = "1234567890@s.whatsapp.net"
        DB['chats'][chat_jid] = {
            "messages": [{"message_id": "msg_123", "text_content": "Hello"}]
        }
        
        result = utils.get_message_data(chat_jid, "nonexistent_msg")
        self.assertIsNone(result)

    def test_add_message_to_chat_success(self):
        """Test successful addition of message to chat."""
        chat_jid = "1234567890@s.whatsapp.net"
        message_data = {
            "message_id": "msg_123",
            "chat_jid": chat_jid,
            "sender_jid": "1234567890@s.whatsapp.net",
            "text_content": "Hello World",
            "timestamp": "2024-01-01T12:00:00Z",
            "is_outgoing": False
        }
        
        DB['chats'][chat_jid] = {
            "chat_jid": chat_jid,
            "messages": []
        }
        
        result = utils.add_message_to_chat(chat_jid, message_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["message_id"], "msg_123")
        self.assertEqual(len(DB['chats'][chat_jid]["messages"]), 1)

    def test_add_message_to_chat_invalid_input(self):
        """Test adding message with invalid input."""
        # Test with None
        result = utils.add_message_to_chat("1234567890@s.whatsapp.net", None)
        self.assertIsNone(result)
        
        # Test with dict missing message_id
        result = utils.add_message_to_chat("1234567890@s.whatsapp.net", {"invalid": "data"})
        self.assertIsNone(result)

    def test_get_contact_data_success(self):
        """Test successful retrieval of contact data."""
        contact_jid = "1234567890@s.whatsapp.net"
        contact_data = {
            "resourceName": f"people/{contact_jid}",
            "names": [{"givenName": "John", "familyName": "Doe"}],
            "whatsapp": {
                "jid": contact_jid,
                "is_whatsapp_user": True,
                "name_in_address_book": "John Doe"
            }
        }
        
        DB['contacts'][f"people/{contact_jid}"] = contact_data
        
        result = utils.get_contact_data(contact_jid)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["whatsapp"]["jid"], contact_jid)

    def test_get_contact_data_not_found(self):
        """Test retrieval of non-existent contact data."""
        result = utils.get_contact_data("nonexistent@s.whatsapp.net")
        self.assertIsNone(result)

    def test_add_contact_data_success(self):
        """Test successful addition of contact data."""
        contact_data = {
            "jid": "1234567890@s.whatsapp.net",
            "names": [{"givenName": "John", "familyName": "Doe"}],
            "whatsapp": {
                "is_whatsapp_user": True,
                "name_in_address_book": "John Doe"
            }
        }
        
        result = utils.add_contact_data(contact_data)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["jid"], "1234567890@s.whatsapp.net")
        self.assertIn("1234567890@s.whatsapp.net", DB['contacts'])

    def test_add_contact_data_duplicate(self):
        """Test adding duplicate contact data."""
        contact_data = {
            "jid": "1234567890@s.whatsapp.net",
            "names": [{"givenName": "John", "familyName": "Doe"}]
        }
        
        # Add the contact first time
        utils.add_contact_data(contact_data)
        
        # Try to add the same contact again
        result = utils.add_contact_data(contact_data)
        self.assertIsNone(result)

    def test_add_contact_data_invalid_input(self):
        """Test adding contact data with invalid input."""
        # Test with None
        result = utils.add_contact_data(None)
        self.assertIsNone(result)
        
        # Test with dict missing jid
        result = utils.add_contact_data({"invalid": "data"})
        self.assertIsNone(result)
    
    def test_bug_1235_invalid_jid_format_in_output(self):
        """Bug #1235: Test that invalid JID format in search results raises Pydantic validation error."""
        # Add a contact with invalid JID format (missing @s.whatsapp.net)
        invalid_jid_contact = 'people/invalid-jid-001'
        DB['contacts'][invalid_jid_contact] = {
            'resourceName': invalid_jid_contact,
            'names': [{'givenName': 'Invalid', 'familyName': 'JID'}],
            'whatsapp': {
                'jid': 'invalid-jid-format',  # Invalid JID format
                'name_in_address_book': 'Invalid JID',
                'profile_name': 'InvalidJID',
                'is_whatsapp_user': True
            }
        }
        
        # Act & Assert: The search should find the contact, but validation should fail
        with self.assertRaises(PydanticValidationError):
            search_contacts(query='Invalid JID')
    
    def test_bug_1235_invalid_phone_number_format_in_output(self):
        """Bug #1235: Test that invalid phone number format in search results raises Pydantic validation error."""
        # Add a contact with invalid phone number format
        invalid_phone_contact = 'people/invalid-phone-001'
        DB['contacts'][invalid_phone_contact] = {
            'resourceName': invalid_phone_contact,
            'names': [{'givenName': 'Invalid', 'familyName': 'Phone'}],
            'whatsapp': {
                'jid': '123456789@s.whatsapp.net',
                'name_in_address_book': 'Invalid Phone',
                'profile_name': 'InvalidPhone',
                'phone_number': 'abc123',  # Invalid phone number format (contains letters)
                'is_whatsapp_user': True
            }
        }
        
        # Act & Assert: The search should find the contact, but validation should fail
        with self.assertRaises(PydanticValidationError):
            search_contacts(query='Invalid Phone')
    
    def test_bug_1235_valid_jid_format_passes_validation(self):
        """Bug #1235: Test that valid JID format passes Pydantic validation."""
        # Add a contact with valid JID format
        valid_jid_contact = 'people/valid-jid-001'
        DB['contacts'][valid_jid_contact] = {
            'resourceName': valid_jid_contact,
            'names': [{'givenName': 'Valid', 'familyName': 'JID'}],
            'whatsapp': {
                'jid': '1234567890@s.whatsapp.net',  # Valid JID format
                'name_in_address_book': 'Valid JID',
                'profile_name': 'ValidJID',
                'phone_number': '+1234567890',
                'is_whatsapp_user': True
            }
        }
        
        # Act: Search should succeed without errors
        result = search_contacts(query='Valid JID')
        
        # Assert: Should return the contact without Pydantic validation errors
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name_in_address_book'], 'Valid JID')
    
    def test_bug_1235_empty_jid_raises_validation_error(self):
        """Bug #1235: Test that empty JID raises Pydantic validation error."""
        # Add a contact with empty JID
        empty_jid_contact = 'people/empty-jid-001'
        DB['contacts'][empty_jid_contact] = {
            'resourceName': empty_jid_contact,
            'names': [{'givenName': 'Empty', 'familyName': 'JID'}],
            'whatsapp': {
                'jid': '',  # Empty JID
                'name_in_address_book': 'Empty JID',
                'profile_name': 'EmptyJID',
                'is_whatsapp_user': True
            }
        }
        
        # Act & Assert: Should raise Pydantic validation error for empty JID
        with self.assertRaises(PydanticValidationError) as cm:
            search_contacts(query='Empty JID')
        
        # Verify error message mentions JID cannot be empty
        error_msg = str(cm.exception)
        self.assertIn('JID', error_msg)


if __name__ == '__main__':
    unittest.main()
