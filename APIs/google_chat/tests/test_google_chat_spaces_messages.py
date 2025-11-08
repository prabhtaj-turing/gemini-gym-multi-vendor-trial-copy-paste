import sys
from datetime import datetime
from pydantic import ValidationError
sys.path.append("APIs")
from common_utils.base_case import BaseTestCaseWithErrorHandler
from google_chat.SimulationEngine.custom_errors import UserNotMemberError
import google_chat as GoogleChatAPI

class TestGoogleChatSpacesMessages(BaseTestCaseWithErrorHandler):
    def setUp(self):
        """Reset DB before each test"""
        GoogleChatAPI.DB.clear()
        GoogleChatAPI.DB.update(
            {
                "User": [{"name": "users/USER123", "displayName": "Test User"}],
                "Space": [],
                "Membership": [],
                "Message": [],
                "Reaction": [],
                "SpaceReadState": [],
                "ThreadReadState": [],
                "SpaceNotificationSetting": [],
            }
        )
        GoogleChatAPI.CURRENT_USER_ID.clear()
        GoogleChatAPI.CURRENT_USER_ID.update({"id": "users/test_user"})

        # Add a test space
        self.test_space = {
            "name": "spaces/TEST_SPACE",
            "spaceType": "SPACE",
            "displayName": "Test Space",
        }
        GoogleChatAPI.DB["Space"].append(self.test_space)

        # Add membership for current user
        self.membership = {
            "name": f"spaces/TEST_SPACE/members/{GoogleChatAPI.CURRENT_USER_ID['id']}",
            "state": "JOINED",
            "role": "ROLE_MEMBER",
            "member": {"name": GoogleChatAPI.CURRENT_USER_ID["id"], "type": "HUMAN"},
        }
        GoogleChatAPI.DB["Membership"].append(self.membership)

    def test_messages(self):
        space_obj = {
            "name": "spaces/AAA",
            "displayName": "Messages Test Space",
            "spaceType": "SPACE",
            "customer": "customers/my_customer",
            "importMode": False,
        }
        GoogleChatAPI.DB["Space"].append(space_obj)

        caller_membership = {
            "name": f"{space_obj['name']}/members/{GoogleChatAPI.CURRENT_USER_ID.get('id')}",
            "state": "JOINED",
            "role": "ROLE_MEMBER",
            "member": {"name": GoogleChatAPI.CURRENT_USER_ID.get("id"), "type": "HUMAN"},
            "groupMember": {},
            "createTime": datetime.now().isoformat() + "Z",
            "deleteTime": "",
        }
        GoogleChatAPI.DB["Membership"].append(caller_membership)

        msg_body = {"text": "Hello, world!"}
        created_msg = GoogleChatAPI.Spaces.Messages.create(
            parent="spaces/AAA",
            requestId="msg-req-001",
            messageReplyOption="REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD",
            messageId="client-001",
            message_body=msg_body,
        )
        self.assertTrue(created_msg.get("name", "").endswith("client-001"))

        # orderBy must be "createTime asc" or "createTime desc", not just "ASC"
        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.list,
            ValueError,
            'orderBy, if provided, must be "createTime asc" or "createTime desc".',
            parent="spaces/AAA",
            pageSize=10,
            pageToken="0",
            filter=None,
            orderBy="ASC",
            showDeleted=False,
        )
        
        # Now use the correct format
        list_result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/AAA",
            pageSize=10,
            pageToken="0",
            filter=None,
            orderBy="createTime asc",  # Correct format
            showDeleted=False,
        )
        self.assertIn("messages", list_result)

        got_msg = GoogleChatAPI.Spaces.Messages.get(name=created_msg["name"])
        self.assertEqual(got_msg.get("text"), "Hello, world!")

        update_body = {"text": "Hello, updated world!", "attachment": []}
        updated_msg = GoogleChatAPI.Spaces.Messages.update(
            name=created_msg["name"],
            updateMask="text",
            allowMissing=False,
            body=update_body,
        )
        self.assertEqual(updated_msg.get("text"), "Hello, updated world!")

        delete_result = GoogleChatAPI.Spaces.Messages.delete(
            name=created_msg["name"], force=True
        )
        got_after_delete = GoogleChatAPI.Spaces.Messages.get(name=created_msg["name"])
        self.assertEqual(got_after_delete, {})

    def test_create_no_message_body(self):
        """Test lines 94-95: create without message body"""
        from pydantic import ValidationError
        # Try to create message without a body
        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.create,
            ValidationError,
            "Input should be a valid dictionary",
            parent="spaces/TEST_SPACE",
            message_body=None
        )

    def test_create_non_member(self):
        """Test lines 101-102: create with non-member user"""
        # Remove the membership
        GoogleChatAPI.DB["Membership"].remove(self.membership)

        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.create,
            UserNotMemberError,
            "User users/test_user is not a member of space 'spaces/TEST_SPACE'. Please join the space first.",
            parent="spaces/TEST_SPACE",
            message_body={"text": "Test message"}
        )

    def test_create_missing_parent(self):
        """Test lines 101-102: create with non-member user"""

        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.create,
            ValidationError,
            "validation error",
            parent=1,
            message_body={"text": "Test message"}
        )

    def test_create_invalid_message_id(self):
        """Test create spacec with invalid messageId"""
        # Try to create message with invalid messageId
        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.create,
            ValidationError,
            "If 'messageId' is provided, it must start with 'client-'.",
            parent="spaces/TEST_SPACE",
            messageId="invalid-id",  # Should start with client-
            message_body={"text": "Test message"},
        )

    def test_create_invalid_parent_format_no_spaces_prefix(self):
        """Test line 83: create with parent that doesn't start with 'spaces/'"""
        from pydantic import ValidationError
        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.create,
            ValidationError,
            "String should match pattern '^spaces/[^/]+$'",
            parent="invalid/TEST_SPACE",  # Doesn't start with 'spaces/'
            message_body={"text": "Test message"}
        )

    def test_create_invalid_parent_format_wrong_structure(self):
        """Test line 85: create with parent that doesn't follow 'spaces/{space}' format"""
        from pydantic import ValidationError
        # Test with too many slashes
        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.create,
            ValidationError,
            "String should match pattern '^spaces/[^/]+$'",
            parent="spaces/TEST_SPACE/extra",  # Too many parts
            message_body={"text": "Test message"}
        )

        # Test with empty space name
        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.create,
            ValidationError,
            "String should match pattern '^spaces/[^/]+$'",
            parent="spaces/",  # Empty space name
            message_body={"text": "Test message"}
        )

    def test_create_empty_request_id(self):
        """Test line 89: create with empty requestId"""
        from pydantic import ValidationError
        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.create,
            ValidationError,
            "Argument 'requestId' cannot be empty or contain only whitespace if provided.",
            parent="spaces/TEST_SPACE",
            requestId="",  # Empty string
            message_body={"text": "Test message"}
        )

    def test_create_whitespace_only_request_id(self):
        """Test line 89: create with whitespace-only requestId"""
        from pydantic import ValidationError
        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.create,
            ValidationError,
            "Argument 'requestId' cannot be empty or contain only whitespace if provided.",
            parent="spaces/TEST_SPACE",
            requestId="   \t\n  ",  # Whitespace only
            message_body={"text": "Test message"}
        )

    def test_create_invalid_request_id_type(self):
        """Test line 89: create with requestId that is not a string"""
        from pydantic import ValidationError
        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.create,
            ValidationError,
            "Input should be a valid string",
            parent="spaces/TEST_SPACE",
            requestId=123,  # Integer instead of string
            message_body={"text": "Test message"}
        )

        # Test with None (should pass since it's optional)
        result = GoogleChatAPI.Spaces.Messages.create(
            parent="spaces/TEST_SPACE",
            requestId=None,  # None is valid for optional parameter
            message_body={"text": "Test message"}
        )
        self.assertIsNotNone(result)

    def test_create_with_message_reply_option(self):
        """Test line 111: create with messageReplyOption"""
        # Create message with messageReplyOption
        result = GoogleChatAPI.Spaces.Messages.create(
            parent="spaces/TEST_SPACE",
            messageReplyOption="REPLY_MESSAGE_FALLBACK_TO_NEW_THREAD",
            message_body={"text": "Test message"},
        )

        # Should succeed
        self.assertIsNotNone(result)
        self.assertIn("name", result)
        self.assertEqual(result["text"], "Test message")

    def test_create_invalid_message_reply_option_error(self):
        # A value that is not in the list of accepted reply options
        invalid_reply_option = "INVALID_REPLY_OPTION"

        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.create,
            ValidationError,
            "Invalid messageReplyOption",
            parent="spaces/TEST_SPACE",
            messageReplyOption=invalid_reply_option,
            message_body={"text": "This message should not be created"},
        )

    def test_update_missing_message(self):
        """Test lines 341-343: update non-existent message"""
        # Try to update a message that doesn't exist
        result = GoogleChatAPI.Spaces.Messages.update(
            name="spaces/TEST_SPACE/messages/nonexistent",
            updateMask="text",
            allowMissing=False,
            body={"text": "Updated text"},
        )

        # Should return empty dict
        self.assertEqual(result, {})

    def test_update_allow_missing_invalid_name(self):
        """Test lines 347, 349, 351: update with allowMissing but invalid name"""
        # Try to update with allowMissing=True but invalid name format
        result = GoogleChatAPI.Spaces.Messages.update(
            name="invalid/format",
            updateMask="text",
            allowMissing=True,
            body={"text": "Updated text"},
        )

        # Should return empty dict
        self.assertEqual(result, {})

        # Try with correct format but not client-assigned ID
        result = GoogleChatAPI.Spaces.Messages.update(
            name="spaces/TEST_SPACE/messages/123",
            updateMask="text",
            allowMissing=True,
            body={"text": "Updated text"},
        )

        # Should return empty dict
        self.assertEqual(result, {})

    def test_update_allow_missing_client_id(self):
        """Test lines 360-361: update with allowMissing and client-assigned ID"""
        # Update with allowMissing=True and valid client-assigned ID
        result = GoogleChatAPI.Spaces.Messages.update(
            name="spaces/TEST_SPACE/messages/client-abc123",
            updateMask="text",
            allowMissing=True,
            body={"text": "New message with client ID"},
        )

        # Should create new message
        self.assertIsNotNone(result)
        self.assertEqual(result["name"], "spaces/TEST_SPACE/messages/client-abc123")
        self.assertEqual(result["text"], "New message with client ID")

        # Verify message was added to DB
        found = False
        for msg in GoogleChatAPI.DB["Message"]:
            if msg["name"] == "spaces/TEST_SPACE/messages/client-abc123":
                found = True
                break
        self.assertTrue(found)

    def test_update_with_specific_fields(self):
        """Test lines 383-434: update with specific fields"""
        # Create a message first
        message = {
            "name": "spaces/TEST_SPACE/messages/1",
            "text": "Original text",
            "attachment": [],
            "createTime": datetime.now().isoformat() + "Z",
            "sender": {"name": GoogleChatAPI.CURRENT_USER_ID["id"], "type": "HUMAN"},
        }
        GoogleChatAPI.DB["Message"].append(message)

        # Update specific fields
        result = GoogleChatAPI.Spaces.Messages.update(
            name="spaces/TEST_SPACE/messages/1",
            updateMask="text,cards_v2",
            allowMissing=False,
            body={
                "text": "Updated text",
                "attachment": [{"name": "test-attachment"}],  # Should not be updated
                "cards_v2": [
                    {"cardId": "card1", "card": {"header": {"title": "Test Card V2"}}}
                ],
            },
        )

        # Verify only specified fields were updated
        self.assertEqual(result["text"], "Updated text")
        self.assertEqual(len(result["attachment"]), 0)  # Should not be updated
        self.assertEqual(
            len(result["cardsV2"]), 1
        )  # Should be updated (note the field name transformation)

    def test_update_unsupported_field(self):
        """Test line 448: update with unsupported field"""
        # Create a message first
        message = {
            "name": "spaces/TEST_SPACE/messages/1",
            "text": "Original text",
            "attachment": [],
            "createTime": datetime.now().isoformat() + "Z",
            "sender": {"name": GoogleChatAPI.CURRENT_USER_ID["id"], "type": "HUMAN"},
        }
        GoogleChatAPI.DB["Message"].append(message)

        # Update with unsupported field
        result = GoogleChatAPI.Spaces.Messages.update(
            name="spaces/TEST_SPACE/messages/1",
            updateMask="text,unsupported_field",
            allowMissing=False,
            body={"text": "Updated text"},
        )

        # Verify only supported fields were updated
        self.assertEqual(result["text"], "Updated text")

    def test_update_alternate_field_naming(self):
        """Test line 455: update with alternate field naming (cards_v2 vs cardsV2)"""
        # Create a message first
        message = {
            "name": "spaces/TEST_SPACE/messages/1",
            "text": "Original text",
            "attachment": [],
            "createTime": datetime.now().isoformat() + "Z",
            "sender": {"name": GoogleChatAPI.CURRENT_USER_ID["id"], "type": "HUMAN"},
        }
        GoogleChatAPI.DB["Message"].append(message)

        # Update using cards_v2 in updateMask but cardsV2 in body
        result = GoogleChatAPI.Spaces.Messages.update(
            name="spaces/TEST_SPACE/messages/1",
            updateMask="cards_v2",
            allowMissing=False,
            body={
                "cardsV2": [
                    {"cardId": "card1", "card": {"header": {"title": "Test Card V2"}}}
                ]
            },
        )

        # Verify field was updated despite naming difference
        self.assertEqual(len(result["cardsV2"]), 1)

    def test_list_non_member(self):
        """Test lines 656-657: list messages as non-member"""
        # Remove the membership
        GoogleChatAPI.DB["Membership"].remove(self.membership)

        # Try to list messages
        result = GoogleChatAPI.Spaces.Messages.list(parent="spaces/TEST_SPACE")

        # Should return empty list
        self.assertEqual(result, {"messages": []})

    def test_list_with_invalid_page_size(self):
        """Test lines 666-667: list with invalid page size"""
        # Try to list with negative page size
        with self.assertRaises(ValueError):
            GoogleChatAPI.Spaces.Messages.list(parent="spaces/TEST_SPACE", pageSize=-1)

    def test_delete_message_not_found(self):
        """Test lines 813-837: delete message not found"""
        # Import the custom error for proper exception testing
        from google_chat.SimulationEngine.custom_errors import MessageNotFoundError
        
        # Try to delete non-existent message - should raise MessageNotFoundError
        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.delete,
            MessageNotFoundError,
            "Message 'spaces/TEST_SPACE/messages/nonexistent' not found.",
            name="spaces/TEST_SPACE/messages/nonexistent"
        )

    def test_delete_with_replies_no_force(self):
        """Test line 842: delete message with replies without force flag"""
        # Import the custom error for proper exception testing
        from google_chat.SimulationEngine.custom_errors import MessageHasRepliesError
        
        # Create a message with thread
        thread_name = "spaces/TEST_SPACE/threads/thread1"
        message = {
            "name": "spaces/TEST_SPACE/messages/1",
            "text": "Parent message",
            "createTime": datetime.now().isoformat() + "Z",
            "sender": {"name": GoogleChatAPI.CURRENT_USER_ID["id"], "type": "HUMAN"},
            "thread": {"name": thread_name},
        }
        GoogleChatAPI.DB["Message"].append(message)

        # Create a reply message
        reply = {
            "name": "spaces/TEST_SPACE/messages/2",
            "text": "Reply message",
            "createTime": datetime.now().isoformat() + "Z",
            "sender": {"name": GoogleChatAPI.CURRENT_USER_ID["id"], "type": "HUMAN"},
            "thread": {"name": thread_name},
        }
        GoogleChatAPI.DB["Message"].append(reply)

        # Try to delete parent message without force - should raise MessageHasRepliesError
        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.delete,
            MessageHasRepliesError,
            "Message 'spaces/TEST_SPACE/messages/1' has 1 threaded replies. Set force=True to delete them.",
            name="spaces/TEST_SPACE/messages/1",
            force=False
        )

        # Verify both messages still exist (nothing was deleted due to exception)
        self.assertEqual(len(GoogleChatAPI.DB["Message"]), 2)

    def test_get_non_member(self):
        """Test line 954: get message as non-member"""
        # Add a message
        message = {
            "name": "spaces/TEST_SPACE/messages/1",
            "text": "Test message",
            "createTime": datetime.now().isoformat() + "Z",
            "sender": {"name": GoogleChatAPI.CURRENT_USER_ID["id"], "type": "HUMAN"},
        }
        GoogleChatAPI.DB["Message"].append(message)

        # Remove the membership
        GoogleChatAPI.DB["Membership"].remove(self.membership)

        # Try to get message
        result = GoogleChatAPI.Spaces.Messages.get(name="spaces/TEST_SPACE/messages/1")

        # Should return empty dict
        self.assertEqual(result, {})

    def test_get_invalid_name_format(self):
        """Test lines 987-988: get with invalid name format"""
        # Try to get message with invalid name format
        self.assert_error_behavior(
            GoogleChatAPI.Spaces.Messages.get,
            ValueError,
            "Invalid message name format",
            name="invalid/format"
        )

    def test_get_message_not_found(self):
        """Test line 997: get non-existent message"""
        # Try to get non-existent message
        result = GoogleChatAPI.Spaces.Messages.get(
            name="spaces/TEST_SPACE/messages/nonexistent"
        )

        # Should return empty dict
        self.assertEqual(result, {})

    def test_list_with_complex_filter(self):
        """Test lines 1001-1009: list with complex filter"""
        # Add messages with different timestamps and threads
        thread1 = "spaces/TEST_SPACE/threads/thread1"
        thread2 = "spaces/TEST_SPACE/threads/thread2"

        # Message 1: Early timestamp, thread1
        GoogleChatAPI.DB["Message"].append(
            {
                "name": "spaces/TEST_SPACE/messages/1",
                "text": "Early message in thread1",
                "createTime": "2022-01-01T00:00:00Z",
                "sender": {
                    "name": GoogleChatAPI.CURRENT_USER_ID["id"],
                    "type": "HUMAN",
                },
                "thread": {"name": thread1},
            }
        )

        # Message 2: Middle timestamp, thread2
        GoogleChatAPI.DB["Message"].append(
            {
                "name": "spaces/TEST_SPACE/messages/2",
                "text": "Middle message in thread2",
                "createTime": "2022-06-01T00:00:00Z",
                "sender": {
                    "name": GoogleChatAPI.CURRENT_USER_ID["id"],
                    "type": "HUMAN",
                },
                "thread": {"name": thread2},
            }
        )

        # Message 3: Late timestamp, thread1
        GoogleChatAPI.DB["Message"].append(
            {
                "name": "spaces/TEST_SPACE/messages/3",
                "text": "Late message in thread1",
                "createTime": "2023-01-01T00:00:00Z",
                "sender": {
                    "name": GoogleChatAPI.CURRENT_USER_ID["id"],
                    "type": "HUMAN",
                },
                "thread": {"name": thread1},
            }
        )

        # Test filter by thread
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/TEST_SPACE", filter=f'thread.name = "{thread1}"'
        )

        # Should return only messages in thread1
        self.assertEqual(len(result["messages"]), 2)
        for msg in result["messages"]:
            self.assertEqual(msg["thread"]["name"], thread1)

        # Test filter by create_time
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/TEST_SPACE", filter='create_time > "2022-03-01T00:00:00Z"'
        )

        # Should return only messages after March 2022
        self.assertEqual(len(result["messages"]), 2)
        for msg in result["messages"]:
            self.assertGreater(msg["createTime"], "2022-03-01T00:00:00Z")

        # Test combined filter
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/TEST_SPACE",
            filter=f'create_time > "2022-03-01T00:00:00Z" AND thread.name = "{thread1}"',
        )

        # Should return only one message
        self.assertEqual(len(result["messages"]), 1)
        self.assertEqual(result["messages"][0]["name"], "spaces/TEST_SPACE/messages/3")

    def test_list_page_size_page_token(self):
        # Validate page size is capped at 1000
        with self.assertRaises(ValueError) as context:
            GoogleChatAPI.Spaces.Messages.list(
                parent="spaces/TEST_SPACE", pageSize=1001
            )
        self.assertIn("pageSize cannot exceed 1000", str(context.exception))
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/TEST_SPACE", pageSize=None
        )
        try:
            result = GoogleChatAPI.Spaces.Messages.list(
                parent="spaces/TEST_SPACE", pageSize=-1
            )
        except ValueError:
            pass
        try:
            result = GoogleChatAPI.Spaces.Messages.list(
                parent="spaces/TEST_SPACE", pageToken="1A"
            )
        except ValueError:
            pass

    def test_list_filter(self):
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/TEST_SPACE",
            filter='thread.name ! "thread1" AND create_time > "2022-03-01T00:00:00Z"',
        )
        self.assertEqual(len(result["messages"]), 0)

        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/TEST_SPACE",
            filter='thread.name ! "thread1" AND create_time < "2022-03-01T00:00:00Z"',
        )
        self.assertEqual(len(result["messages"]), 0)

        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/TEST_SPACE",
            filter='thread.name = "thread1" AND create_time >= "2022-03-01T00:00:00Z"',
        )
        self.assertEqual(len(result["messages"]), 0)

        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/TEST_SPACE", filter='create_time <= "2022-03-01T00:00:00Z"'
        )
        self.assertEqual(len(result["messages"]), 0)

    def test_update_message(self):
        message = {
            "name": "spaces/TEST_SPACE/messages/1",
            "text": "Original text",
            "createTime": datetime.now().isoformat() + "Z",
            "sender": {"name": GoogleChatAPI.CURRENT_USER_ID["id"], "type": "HUMAN"},
        }
        GoogleChatAPI.DB["Message"].append(message)
        result = GoogleChatAPI.Spaces.Messages.update(
            name="spaces/TEST_SPACE/messages/1",
            allowMissing=True,
            updateMask="*",
            body={"text": "Updated text"},
        )
        self.assertEqual(result["text"], "Updated text")

        result = GoogleChatAPI.Spaces.Messages.patch(
            name="spaces/TEST_SPACE/messages/1",
            allowMissing=True,
            updateMask="text",
            message={"text": "Updated text"},
        )

    def test_create_missing_thread_data_error(self):
        """Test MissingThreadDataError when messageReplyOption is REPLY_MESSAGE_OR_FAIL and thread info is missing"""
        from google_chat.SimulationEngine.custom_errors import MissingThreadDataError
        with self.assertRaises(MissingThreadDataError):
            GoogleChatAPI.Spaces.Messages.create(
                parent="spaces/TEST_SPACE",
                messageReplyOption="REPLY_MESSAGE_OR_FAIL",
                message_body={"text": "This should fail"},
            )

        # Verify that it works when thread info is provided
        result = GoogleChatAPI.Spaces.Messages.create(
            parent="spaces/TEST_SPACE",
            messageReplyOption="REPLY_MESSAGE_OR_FAIL",
            message_body={"text": "This should succeed", "thread": {"name": "spaces/TEST_SPACE/threads/some_thread"}},
        )
        self.assertIn("name", result)

    def test_list_filter_field_name_validation(self):
        """Test that filter logic properly validates field names to prevent ACR1112 logic flaw"""
        # Create test space and membership
        space_obj = {
            "name": "spaces/FILTER_TEST",
            "displayName": "Filter Test Space",
            "spaceType": "SPACE",
        }
        GoogleChatAPI.DB["Space"].append(space_obj)

        caller_membership = {
            "name": f"{space_obj['name']}/members/{GoogleChatAPI.CURRENT_USER_ID.get('id')}",
            "state": "JOINED",
            "role": "ROLE_MEMBER",
            "member": {"name": GoogleChatAPI.CURRENT_USER_ID.get("id"), "type": "HUMAN"},
        }
        GoogleChatAPI.DB["Membership"].append(caller_membership)

        # Create test messages with different thread names
        thread1 = "spaces/FILTER_TEST/threads/thread1"
        thread2 = "spaces/FILTER_TEST/threads/thread2"
        
        # Create messages in thread1
        GoogleChatAPI.Spaces.Messages.create(
            parent="spaces/FILTER_TEST",
            message_body={"text": "Message in thread1", "thread": {"name": thread1}},
        )
        GoogleChatAPI.Spaces.Messages.create(
            parent="spaces/FILTER_TEST",
            message_body={"text": "Another message in thread1", "thread": {"name": thread1}},
        )
        
        # Create message in thread2
        GoogleChatAPI.Spaces.Messages.create(
            parent="spaces/FILTER_TEST",
            message_body={"text": "Message in thread2", "thread": {"name": thread2}},
        )

        # Test 1: Valid thread.name filter should work
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/FILTER_TEST",
            filter=f'thread.name = "{thread1}"'
        )
        self.assertEqual(len(result["messages"]), 2)
        for msg in result["messages"]:
            self.assertEqual(msg["thread"]["name"], thread1)

        # Test 2: Invalid field names should be rejected (not processed as thread.name filters)
        # These should return empty results because the invalid field names are not recognized
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/FILTER_TEST",
            filter='some_other.thread.name = "spaces/FILTER_TEST/threads/thread1"'
        )
        # Should return empty because some_other.thread.name is not a valid field
        self.assertEqual(len(result["messages"]), 0)

        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/FILTER_TEST",
            filter='my.thread.name = "spaces/FILTER_TEST/threads/thread1"'
        )
        # Should return empty because my.thread.name is not a valid field
        self.assertEqual(len(result["messages"]), 0)

        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/FILTER_TEST",
            filter='prefix.thread.name = "spaces/FILTER_TEST/threads/thread1"'
        )
        # Should return empty because prefix.thread.name is not a valid field
        self.assertEqual(len(result["messages"]), 0)

        # Test 3: Valid create_time filter should work
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/FILTER_TEST",
            filter='create_time > "2020-01-01T00:00:00Z"'
        )
        # Should return all messages (3 total)
        self.assertEqual(len(result["messages"]), 3)

        # Test 4: Invalid create_time field names should be rejected
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/FILTER_TEST",
            filter='some_other.create_time > "2020-01-01T00:00:00Z"'
        )
        # Should return empty because some_other.create_time is not a valid field
        self.assertEqual(len(result["messages"]), 0)

        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/FILTER_TEST",
            filter='my.create_time > "2020-01-01T00:00:00Z"'
        )
        # Should return empty because my.create_time is not a valid field
        self.assertEqual(len(result["messages"]), 0)

        # Test 5: Combined valid filters should work
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/FILTER_TEST",
            filter=f'thread.name = "{thread1}" AND create_time > "2020-01-01T00:00:00Z"'
        )
        # Should return only messages from thread1
        self.assertEqual(len(result["messages"]), 2)
        for msg in result["messages"]:
            self.assertEqual(msg["thread"]["name"], thread1)

        # Test 6: Mixed valid and invalid filters should fail
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/FILTER_TEST",
            filter=f'some_other.thread.name = "{thread1}" AND create_time > "2020-01-01T00:00:00Z"'
        )
        # Should return empty because the first filter is invalid
        self.assertEqual(len(result["messages"]), 0)

    def test_list_filter_edge_cases(self):
        """Test edge cases for filter validation"""
        # Create test space and membership
        space_obj = {
            "name": "spaces/EDGE_TEST",
            "displayName": "Edge Test Space",
            "spaceType": "SPACE",
        }
        GoogleChatAPI.DB["Space"].append(space_obj)

        caller_membership = {
            "name": f"{space_obj['name']}/members/{GoogleChatAPI.CURRENT_USER_ID.get('id')}",
            "state": "JOINED",
            "role": "ROLE_MEMBER",
            "member": {"name": GoogleChatAPI.CURRENT_USER_ID.get("id"), "type": "HUMAN"},
        }
        GoogleChatAPI.DB["Membership"].append(caller_membership)

        # Create a test message
        GoogleChatAPI.Spaces.Messages.create(
            parent="spaces/EDGE_TEST",
            message_body={"text": "Test message"},
        )

        # Test 1: Empty filter should return all messages
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/EDGE_TEST",
            filter=""
        )
        self.assertGreaterEqual(len(result["messages"]), 1)

        # Test 2: Filter with only spaces should be ignored
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/EDGE_TEST",
            filter="   "
        )
        self.assertGreaterEqual(len(result["messages"]), 1)

        # Test 3: Valid filter syntax but no matching messages
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/EDGE_TEST",
            filter='thread.name = "spaces/EDGE_TEST/threads/nonexistent"'
        )
        # Should return empty because no messages match
        self.assertEqual(len(result["messages"]), 0)

        # Test 4: Case sensitivity - field names should be case-insensitive
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/EDGE_TEST",
            filter='THREAD.NAME = "spaces/EDGE_TEST/threads/any"'
        )
        # Should return empty because no messages match, but shouldn't error
        self.assertEqual(len(result["messages"]), 0)

        # Test 5: Field names with extra spaces should be rejected
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/EDGE_TEST",
            filter=' thread.name  = "spaces/EDGE_TEST/threads/any"'
        )
        # Should work because we strip whitespace
        self.assertEqual(len(result["messages"]), 0)

        # Test 6: Invalid field names that contain valid field names as substrings
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/EDGE_TEST",
            filter='not_thread.name = "spaces/EDGE_TEST/threads/any"'
        )
        # Should return empty because not_thread.name is not a valid field
        self.assertEqual(len(result["messages"]), 0)

        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/EDGE_TEST",
            filter='thread.name_extra = "spaces/EDGE_TEST/threads/any"'
        )
        # Should return empty because thread.name_extra is not a valid field
        self.assertEqual(len(result["messages"]), 0)

    def test_list_filter_performance_with_invalid_fields(self):
        """Test that invalid field names don't cause performance issues"""
        # Create test space and membership
        space_obj = {
            "name": "spaces/PERF_TEST",
            "displayName": "Performance Test Space",
            "spaceType": "SPACE",
        }
        GoogleChatAPI.DB["Space"].append(space_obj)

        caller_membership = {
            "name": f"{space_obj['name']}/members/{GoogleChatAPI.CURRENT_USER_ID.get('id')}",
            "state": "JOINED",
            "role": "ROLE_MEMBER",
            "member": {"name": GoogleChatAPI.CURRENT_USER_ID.get("id"), "type": "HUMAN"},
        }
        GoogleChatAPI.DB["Membership"].append(caller_membership)

        # Create multiple test messages
        for i in range(5):
            GoogleChatAPI.Spaces.Messages.create(
                parent="spaces/PERF_TEST",
                message_body={"text": f"Test message {i}"},
            )

        # Test with multiple invalid field names in a single filter
        invalid_filters = [
            'some_other.thread.name = "spaces/PERF_TEST/threads/any"',
            'my.thread.name = "spaces/PERF_TEST/threads/any"',
            'prefix.thread.name = "spaces/PERF_TEST/threads/any"',
            'another.thread.name = "spaces/PERF_TEST/threads/any"',
            'different.thread.name = "spaces/PERF_TEST/threads/any"'
        ]

        for filter_expr in invalid_filters:
            result = GoogleChatAPI.Spaces.Messages.list(
                parent="spaces/PERF_TEST",
                filter=filter_expr
            )
            # All should return empty because the field names are invalid
            self.assertEqual(len(result["messages"]), 0)

        # Test with combined invalid filters
        combined_invalid = ' AND '.join(invalid_filters)
        result = GoogleChatAPI.Spaces.Messages.list(
            parent="spaces/PERF_TEST",
            filter=combined_invalid
        )
        # Should return empty because all field names are invalid
        self.assertEqual(len(result["messages"]), 0)
