from pydantic import ValidationError
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.utils import reset_db
from .. import Drafts, Messages, get_draft, create_draft, update_draft, list_drafts, get_draft, delete_draft, send_draft, create_user
from ..SimulationEngine.attachment_utils import create_mime_message_with_attachments

def make_raw(sender=None, recipient=None, subject=None, body=None):
    # Helper to generate a valid raw MIME message
    return create_mime_message_with_attachments(
        to=recipient or "recipient@example.com",
        subject=subject or "Test Subject",
        body=body or "Test Body",
        from_email=sender or "me@example.com"
    )

class TestUsersDraftsUpdateValidation(BaseTestCaseWithErrorHandler): 
    def setUp(self):
        """Reset test state before each test, typically involving DB state."""
        reset_db()
        # Create a user with a valid email address for default sender functionality
        create_user("me", profile={"emailAddress": "me@example.com"})
        
        # Create a default draft to be updated in most tests
        initial_raw = make_raw(body="Initial content")
        self.draft_to_update = create_draft(userId="me", draft={"message": {"raw": initial_raw}})
        self.draft_id = self.draft_to_update["id"]

    def test_update_draft_valid_input(self):
        """Test update_draft with a valid full payload."""
        valid_draft_payload = {
            "message": {
                "raw": make_raw(body="Updated raw content"),
                "labelIds": ["INBOX", "IMPORTANT"],
                "subject": "Updated Subject"
            }
        }
        # The function alias for testing is `update_draft` as per existing suite.
        updated_draft = update_draft(userId="me", id=self.draft_id, draft=valid_draft_payload)
        self.assertIsNotNone(updated_draft)
        self.assertEqual(updated_draft["message"]["raw"], valid_draft_payload["message"]["raw"])
        self.assertEqual(updated_draft["message"]["subject"], "Updated Subject")
        self.assertIn("DRAFT", updated_draft["message"]["labelIds"]) # DRAFT label should be ensured
        self.assertIn("IMPORTANT", updated_draft["message"]["labelIds"]) # IMPORTANT label should be preserved
        self.assertNotIn("INBOX", updated_draft["message"]["labelIds"]) # INBOX label should be removed for drafts

    def test_update_draft_valid_partial_payload(self):
        """Test update_draft with a valid partial payload."""
        partial_draft_payload = {"message": {"snippet": "New snippet"}}
        updated_draft = update_draft(userId="me", id=self.draft_id, draft=partial_draft_payload)
        self.assertIsNotNone(updated_draft)
        self.assertEqual(updated_draft["message"]["snippet"], "New snippet")
        self.assertEqual(updated_draft["message"]["raw"], self.draft_to_update["message"]["raw"]) # Unchanged

    def test_update_draft_with_none_payload(self):
        """Test update_draft when draft payload is None."""
        updated_draft = update_draft(userId="me", id=self.draft_id, draft=None)
        self.assertIsNotNone(updated_draft)
        self.assertEqual(updated_draft["message"]["raw"], self.draft_to_update["message"]["raw"]) # Should remain unchanged

    def test_update_draft_with_empty_dict_payload(self):
        """Test update_draft when draft payload is an empty dictionary."""
        updated_draft = update_draft(userId="me", id=self.draft_id, draft={})
        self.assertIsNotNone(updated_draft)
        self.assertEqual(updated_draft["message"]["raw"], self.draft_to_update["message"]["raw"]) # Should remain unchanged

    def test_update_draft_non_existent_draft_id(self):
        """Test update_draft with a non-existent draft ID."""
        result = update_draft(userId="me", id="non-existent-id", draft={"message": {"raw": "Update"}})
        self.assertIsNone(result)

    def test_update_draft_invalid_userid_type(self):
        """Test update_draft with invalid userId type."""
        self.assert_error_behavior(
            func_to_call=update_draft,
            expected_exception_type=TypeError,
            expected_message="userId must be a string.",
            userId=123, # Invalid type
            id=self.draft_id,
            draft={"message": {"raw": "Update"}}
        )

    def test_update_draft_invalid_id_type(self):
        """Test update_draft with invalid id type."""
        self.assert_error_behavior(
            func_to_call=update_draft,
            expected_exception_type=TypeError,
            expected_message="id must be a string.",
            userId="me",
            id=12345, # Invalid type
            draft={"message": {"raw": "Update"}}
        )

    def test_update_draft_pydantic_invalid_top_level_structure(self):
        """Test update_draft with draft having invalid top-level structure for Pydantic."""
        invalid_payload = {"messages": {"raw": "Test"}} # "messages" instead of "message"
        # Pydantic message for unexpected field if `extra='forbid'`
        # If `extra='ignore'` (default), this might pass Pydantic but `message_update` would be {}
        # Assuming DraftUpdateInputModel implicitly uses extra='ignore' or 'allow'.
        # If DraftUpdateInputModel defines `message: Optional[MessageUpdateInputModel] = None`
        # and input is `{"messages": ...}`, then `DraftUpdateInputModel(**invalid_payload)`
        # results in `DraftUpdateInputModel(message=None)`. This is not a ValidationError.
        # The test should be for an invalid *type* for a known field.
        invalid_payload_type = {"message": 123} # message should be a dict or MessageUpdateInputModel
        self.assert_error_behavior(
            func_to_call=update_draft,
            expected_exception_type=ValidationError,
            # The exact message depends on Pydantic version and model details.
            # For robust testing, one might check for specific parts of the error or omit message check.
            # Here, providing a generic or example message from the prompt's guidelines.
            # However, aiming for a more specific Pydantic message segment:
            expected_message='1 validation error for DraftUpdateInputModel\nmessage\n  Input should be a valid dictionary or instance of MessageUpdateModel [type=model_type, input_value=123, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/model_type',
            userId="me",
            id=self.draft_id,
            draft=invalid_payload_type
        )

    def test_update_draft_pydantic_invalid_message_field_type(self):
        """Test update_draft with draft.message having a field of incorrect type."""
        invalid_payload = {"message": {"raw": 12345}} # raw should be str
        self.assert_error_behavior(
            func_to_call=update_draft,
            expected_exception_type=ValidationError,
            expected_message='1 validation error for DraftUpdateInputModel\nmessage.raw\n  Input should be a valid string [type=string_type, input_value=12345, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type',
            userId="me",
            id=self.draft_id,
            draft=invalid_payload
        )

    def test_update_draft_pydantic_invalid_message_labelids_type(self):
        """Test update_draft with draft.message.labelIds of incorrect type (not a list)."""
        invalid_payload = {"message": {"labelIds": "not-a-list"}} # labelIds should be List[str]
        self.assert_error_behavior(
            func_to_call=update_draft,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for DraftUpdateInputModel\nmessage.labelIds\n  Input should be a valid list [type=list_type, input_value='not-a-list', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/list_type",
            userId="me",
            id=self.draft_id,
            draft=invalid_payload
        )

    def test_update_draft_pydantic_invalid_message_labelids_item_type(self):
        """Test update_draft with draft.message.labelIds containing items of incorrect type."""
        invalid_payload = {"message": {"labelIds": ["valid_label", 123]}} # labelIds items should be str
        self.assert_error_behavior(
            func_to_call=update_draft,
            expected_exception_type=ValidationError,
            expected_message='1 validation error for DraftUpdateInputModel\nmessage.labelIds.1\n  Input should be a valid string [type=string_type, input_value=123, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.11/v/string_type',
            userId="me",
            id=self.draft_id,
            draft=invalid_payload
        )
    
    def test_update_draft_pydantic_message_field_sizeestimate_type(self):
        """Test update_draft with draft.message.sizeEstimate of incorrect type."""
        invalid_payload = {"message": {"sizeEstimate": "not-an-int"}}
        self.assert_error_behavior(
            func_to_call=update_draft,
            expected_exception_type=ValidationError,
            expected_message="1 validation error for DraftUpdateInputModel\nmessage.sizeEstimate\n  Input should be a valid integer, unable to parse string as an integer [type=int_parsing, input_value='not-an-int', input_type=str]\n    For further information visit https://errors.pydantic.dev/2.11/v/int_parsing",
            id=self.draft_id,
            draft=invalid_payload
        )

    def test_update_draft_ValueError_for_unknown_user(self):
        """Test update_draft propagates ValueError when _ensure_user fails for an unknown user."""
        # This test assumes _ensure_user checks against a DB populated by reset_db,
        # and 'unknown_user' is not in it.
        self.assert_error_behavior(
            func_to_call=update_draft,
            expected_exception_type=ValueError, # Propagated from _ensure_user
            # The exact message from _ensure_user might vary. Example:
            expected_message="User 'unknown_user@example.com' does not exist.", # Or similar based on actual _ensure_user
            userId="unknown_user@example.com",
            id=self.draft_id, # A valid draft ID, but user check fails first
            draft={"message": {"raw": "Update attempt"}}
        )

class TestUsersDrafts(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        # Create 2 initial drafts for the 'me' user
        create_draft("me", {"message": {"raw": "Initial draft 1"}})
        create_draft("me", {"message": {"raw": "Initial draft 2"}})

    def test_create_list_get_delete_draft(self):
        # Create
        draft = create_draft("me", {"message": {"raw": "Hello"}})
        self.assertIn("id", draft)
        # List - should have 2 existing drafts + 1 created = 3 total
        drafts_list = Drafts.list("me")
        self.assertEqual(len(drafts_list["drafts"]), 3)
        # Get
        fetched = get_draft("me", draft["id"])
        self.assertEqual(fetched["message"]["raw"], "Hello")
        # Delete
        Drafts.delete("me", draft["id"])
        drafts_list = Drafts.list("me")
        # After deleting our created draft, should have 2 existing drafts
        self.assertEqual(len(drafts_list["drafts"]), 2)

    def test_drafts_send(self):
        # Create a draft
        draft_raw = make_raw(body="Draft Content")
        draft = create_draft("me", {"message": {"raw": draft_raw}})
        # Send it
        sent = send_draft("me", draft)
        self.assertIn("id", sent)
        self.assertEqual(sent["raw"], draft_raw)
        # Check drafts - should have 2 existing drafts (our created draft was sent and removed)
        self.assertEqual(len(Drafts.list("me")["drafts"]), 2)
        # Check the message is present in messages - should have existing messages + 1 sent
        messages_count = len(Messages.list("me")["messages"])
        self.assertGreaterEqual(messages_count, 1)  # At least 1 message (our sent draft)

    def test_drafts_update(self): # Original happy path test for update
        # Create and update a draft
        draft = create_draft("me", {"message": {"raw": "Original Content"}})
        draft_id = draft["id"]
        updated = update_draft(draft_id, "me", {"message": {"raw": "Updated Content"}})
        self.assertIsNotNone(updated)
        self.assertEqual(updated["message"]["raw"], "Updated Content")
        # Confirm in DB
        fetched = get_draft("me", draft_id)
        self.assertEqual(fetched["message"]["raw"], "Updated Content")

    def test_drafts_get_formats(self):
        # Create a draft with all fields
        draft_data = {
            "message": {
                "raw": "SGVsbG8gV29ybGQ=",
                "sender": "me@example.com",
                "recipient": "you@example.com",
                "subject": "Test Subject",
                "body": "Hello World",
                "date": "2024-01-01T00:00:00Z",
                "internalDate": "1234567890000",
                "isRead": False,
                "labelIds": ["DRAFT", "IMPORTANT", "UNREAD"],
                "threadId": "thread-123"
            }
        }
        draft = create_draft("me", draft_data)
        draft_id = draft['id']

        # Test minimal format
        minimal = get_draft("me", draft_id, 'minimal')
        self.assertEqual(minimal['id'], draft_id)
        self.assertEqual(minimal['message']['id'], draft['message']['id'])
        self.assertEqual(minimal['message']['labelIds'], ["DRAFT", "IMPORTANT", "UNREAD"]) # DRAFT is auto-added if not present, IMPORTANT and UNREAD from input
        self.assertNotIn('raw', minimal['message'])
        self.assertNotIn('sender', minimal['message'])
        
        # Test raw format
        raw_fmt = get_draft("me", draft_id, 'raw') # Renamed variable to avoid conflict with raw field
        self.assertEqual(raw_fmt['id'], draft_id)
        self.assertEqual(raw_fmt['message']['id'], draft['message']['id'])
        self.assertEqual(raw_fmt['message']['threadId'], "thread-123")
        self.assertEqual(raw_fmt['message']['labelIds'], ["DRAFT", "IMPORTANT", "UNREAD"])
        self.assertEqual(raw_fmt['message']['raw'], "SGVsbG8gV29ybGQ=")
        self.assertNotIn('body', raw_fmt['message'])

        # Test metadata format
        metadata = get_draft("me", draft_id, 'metadata')
        self.assertEqual(metadata['id'], draft_id)
        self.assertEqual(metadata['message']['id'], draft['message']['id'])
        self.assertEqual(metadata['message']['threadId'], "thread-123")
        self.assertEqual(metadata['message']['labelIds'], ["DRAFT", "IMPORTANT", "UNREAD"])
        self.assertEqual(metadata['message']['sender'], "me@example.com")
        self.assertEqual(metadata['message']['recipient'], "you@example.com")
        self.assertEqual(metadata['message']['subject'], "Test Subject")
        self.assertEqual(metadata['message']['date'], "2024-01-01T00:00:00Z")
        self.assertNotIn('body', metadata['message'])
        self.assertNotIn('raw', metadata['message'])

        # Test full format
        full = get_draft("me", draft_id, 'full')
        self.assertEqual(full['id'], draft_id)
        self.assertEqual(full['message']['id'], draft['message']['id'])
        self.assertEqual(full['message']['threadId'], "thread-123")
        self.assertEqual(full['message']['sender'], "me@example.com")
        self.assertEqual(full['message']['recipient'], "you@example.com")
        self.assertEqual(full['message']['subject'], "Test Subject")
        self.assertEqual(full['message']['body'], "Hello World")
        self.assertEqual(full['message']['date'], "2024-01-01T00:00:00Z")
        self.assertEqual(full['message']['internalDate'], "1234567890000")
        self.assertEqual(full['message']['isRead'], False)
        self.assertEqual(full['message']['labelIds'], ["DRAFT", "IMPORTANT", "UNREAD"])
        self.assertIn('raw', full['message'])

        # Test invalid format (original test used with self.assertRaises)
        # Adapting to use assert_error_behavior if get_draft uses the error handling pattern
        # The original test for get_draft with invalid format:
        # with self.assertRaises(ValueError):
        #     get_draft("me", draft_id, 'invalid_format')
        # This needs to be updated if get_draft uses the error_dict pattern too.
        # The test `test_drafts_get_with_invalid_format` below uses `assert_error_behavior` for `get_draft`.
        # For consistency, this part should also use it if `get_draft` is designed that way.
        # Assuming `get_draft` can raise ValueError directly or return error_dict:
        self.assert_error_behavior(
            func_to_call=get_draft,
            expected_exception_type=ValueError,
            expected_message="Invalid format 'invalid_format'. Must be one of: minimal, full, raw, metadata.",
            userId="me", id=draft_id, format='invalid_format'
        )

        # Test non-existent draft
        non_existent = get_draft("me", "non-existent-id", 'full')
        self.assertIsNone(non_existent)
    
    def test_drafts_get_with_invalid_format(self): # This test was provided
        draft = create_draft("me", {"message": {"raw": "Original Content"}})
        draft_id = draft["id"]

        self.assert_error_behavior(
            func_to_call=get_draft, # Note: Uses get_draft directly, not get_draft
            expected_exception_type=ValueError,
            expected_message="Invalid format 'invalid_format'. Must be one of: minimal, full, raw, metadata.",
            additional_expected_dict_fields={
                "module": "Drafts", # This implies get_draft sets these fields if ERROR_MODE="error_dict"
                "function": "get",
            },
            userId="me", # Assuming get_draft takes userId as first arg. Original code had 'id' first
            id=draft_id,
            format="invalid_format"
        )

