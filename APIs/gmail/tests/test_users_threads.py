# tests/test_users_threads.py
import unittest

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.utils import reset_db
from .. import utils, DB, get_thread, send_message, get_message, list_threads, get_thread, trash_thread, untrash_thread, modify_thread_labels, delete_thread, create_user
from ..SimulationEngine.custom_errors import InvalidFormatValueError, ValidationError


class TestUsersThreads(BaseTestCaseWithErrorHandler):
    def setUp(self):
        reset_db()
        # Create user with valid email for default sender
        create_user("me", profile={"emailAddress": "me@example.com"})
        
        thread_id = f"thread_{utils._next_counter('thread')}"
        # Use proper message format with sender and recipient
        m1 = send_message("me", {"sender": "me@example.com", "recipient": "other@example.com", "subject": "Thread msg 1", "body": "Thread msg 1", "threadId": thread_id})
        m2 = send_message("me", {"sender": "me@example.com", "recipient": "other@example.com", "subject": "Thread msg 2", "body": "Thread msg 2", "threadId": thread_id})

        DB["users"]["existing_user@example.com"] = {
            "threads": {
                "threadxyz": {"id": "threadxyz", "messageIds": ["msgABC", "msgDEF"]},
            },
            "messages": {
                "msgABC": {"id": "msgABC", "threadId": "threadxyz", "body": "First message content.", "subject": "Hello", "sender": "other@example.com", "recipient":"existing_user@example.com", "date":"2023-10-10", "labelIds": ["SENT"]},
                "msgDEF": {"id": "msgDEF", "threadId": "threadxyz", "body": "Second message content.", "subject": "RE: Hello", "sender": "existing_user@example.com", "recipient":"other@example.com", "date":"2023-10-11", "labelIds": ["SENT"]},
            },
            "profile": {"historyId": "hist_existing_456"}
        }

    def test_list_get_trash_untrash_modify_delete_thread(self):
        threads_list = list_threads("me")
        self.assertEqual(len(threads_list["threads"]), 1)
        thread_id = threads_list["threads"][0]["id"]
        thread = get_thread("me", thread_id)
        self.assertEqual(len(thread["messageIds"]), 2)

        trash_thread("me", thread_id)
        for mid in thread["messageIds"]:
            self.assertIn("TRASH", get_message("me", mid)["labelIds"])

        untrash_thread("me", thread_id)
        for mid in thread["messageIds"]:
            self.assertNotIn("TRASH", get_message("me", mid)["labelIds"])

        modify_thread_labels("me", thread_id, addLabelIds=["IMPORTANT"])
        for mid in thread["messageIds"]:
            self.assertIn("IMPORTANT", get_message("me", mid)["labelIds"])

        delete_thread("me", thread_id)
        self.assertEqual(len(list_threads("me")["threads"]), 0)
        for mid in thread["messageIds"]:
            self.assertIsNone(get_message("me", mid))

    def test_trash_input_validation(self):
        """Test basic input validation for trash function."""
        # Test invalid userId type
        self.assert_error_behavior(
            func_to_call=trash_thread,
            expected_exception_type=TypeError,
            expected_message="userId must be a string, got int",
            userId=123,
            id="thread_1"
        )
        
        # Test invalid thread id type
        self.assert_error_behavior(
            func_to_call=trash_thread,
            expected_exception_type=TypeError,
            expected_message="id must be a string, got int",
            userId="me",
            id=123
        )
    
    def test_trash_nonexistent_thread(self):
        """Test trash function with nonexistent thread."""
        result = trash_thread("me", id="nonexistent_thread")
        self.assertIsNone(result)

    def test_trash_input_validation(self):
        """Test basic input validation for trash function."""
        # Test invalid userId type
        self.assert_error_behavior(
            func_to_call=trash_thread,
            expected_exception_type=TypeError,
            expected_message="userId must be a string, got int",
            userId=123,
            id="thread_1"
        )
        
        # Test invalid thread id type
        self.assert_error_behavior(
            func_to_call=trash_thread,
            expected_exception_type=TypeError,
            expected_message="id must be a string, got int",
            userId="me",
            id=123
        )
    
    def test_trash_nonexistent_thread(self):
        """Test trash function with nonexistent thread."""
        result = trash_thread("me", id="nonexistent_thread")
        self.assertIsNone(result)

    def test_valid_input_all_params(self):
        """Test get_thread with all valid parameters specified."""
        try:
            result = get_thread(
                userId="existing_user@example.com",
                id="threadxyz",
                format="metadata",
                metadata_headers=["Subject", "From"]
            )
            self.assertIsInstance(result, dict)
            self.assertEqual(result["id"], "threadxyz")
            self.assertIn("messages", result)
            self.assertTrue(all("Subject" in msg["headers"] and "From" in msg["headers"] for msg in result["messages"]))
        except (TypeError, InvalidFormatValueError) as e:
            self.fail(f"Validation unexpectedly failed for valid input: {e}")
        except (KeyError, NameError) as e:
            self.fail(f"Core logic failed, ensure test data is correct or mocks are working: {e}")

    def test_untrash_input_validation(self):
        """Test basic input validation for untrash function."""
        # Test invalid userId type
        with self.assertRaises(TypeError) as context:
            untrash_thread(123, "thread_1")
        self.assertIn("userId must be a string, got int", str(context.exception))
        
        # Test invalid thread id type
        with self.assertRaises(TypeError) as context:
            untrash_thread("me", 123)
        self.assertIn("id must be a string, got int", str(context.exception))
    
    def test_untrash_nonexistent_thread(self):
        """Test untrash function with nonexistent thread."""
        result = untrash_thread("me", "nonexistent_thread")
        self.assertIsNone(result)

    def test_valid_input_default_params(self):
        """Test get_thread with default parameters."""
        try:
            result = get_thread(userId="existing_user@example.com", id="threadxyz") # userId defaults to 'me', format to 'full'
            self.assertIsInstance(result, dict)
            self.assertEqual(result["id"], "threadxyz")
        except (TypeError, InvalidFormatValueError) as e:
            self.fail(f"Validation unexpectedly failed for valid default input: {e}")


    def test_invalid_userid_type(self):
        """Test get_thread with invalid userId type."""
        self.assert_error_behavior(
            func_to_call=get_thread,
            expected_exception_type=TypeError,
            expected_message="Argument 'userId' must be a string, but got int.",
            userId=123,
            id="thread1"
        )

    def test_invalid_id_type(self):
        """Test get_thread with invalid id type."""
        self.assert_error_behavior(
            func_to_call=get_thread,
            expected_exception_type=TypeError,
            expected_message="Argument 'id' must be a string, but got int.",
            userId="me",
            id=12345
        )

    def test_invalid_format_type(self):
        """Test get_thread with invalid format type."""
        self.assert_error_behavior(
            func_to_call=get_thread,
            expected_exception_type=TypeError,
            expected_message="Argument 'format' must be a string, but got int.",
            format=123
        )

    def test_invalid_format_value(self):
        """Test get_thread with invalid format value."""
        self.assert_error_behavior(
            func_to_call=get_thread,
            expected_exception_type=InvalidFormatValueError,
            expected_message="Argument 'format' must be one of ['full', 'metadata', 'minimal', 'raw'], but got 'invalid_format'.",
            format="invalid_format"
        )

    def test_invalid_metadata_headers_type(self):
        """Test get_thread with invalid metadata_headers type (not a list)."""
        self.assert_error_behavior(
            func_to_call=get_thread,
            expected_exception_type=TypeError,
            expected_message="Argument 'metadata_headers' must be a list of strings or None, but got str.",
            metadata_headers="not-a-list"
        )

    def test_invalid_metadata_headers_element_type(self):
        """Test get_thread with invalid element type in metadata_headers list."""
        self.assert_error_behavior(
            func_to_call=get_thread,
            expected_exception_type=TypeError,
            expected_message="All elements in 'metadata_headers' must be strings, but found element of type int.",
            metadata_headers=["Subject", 123, "From"]
        )

    def test_valid_metadata_headers_empty_list(self):
        """Test get_thread with metadata_headers as an empty list."""
        try:
            result = get_thread(
                userId="existing_user@example.com",
                id="threadxyz",
                format="metadata",
                metadata_headers=[] # Empty list is valid
            )
            self.assertIsInstance(result, dict)
            # Depending on logic, headers might be empty or default if metadata_headers is empty
            self.assertTrue(all(isinstance(msg.get("headers"), dict) for msg in result["messages"]))
        except (TypeError, InvalidFormatValueError) as e:
            self.fail(f"Validation unexpectedly failed for metadata_headers=[]: {e}")


    def test_valid_metadata_headers_none(self):
        """Test get_thread with metadata_headers as None (default)."""
        try:
            result = get_thread(
                userId="existing_user@example.com",
                id="threadxyz",
                format="metadata",
                metadata_headers=None # Explicitly None
            )
            self.assertIsInstance(result, dict)
            # Default behavior for headers when metadata_headers is None
            self.assertTrue(all("Subject" in msg["headers"] for msg in result["messages"]))
        except (TypeError, InvalidFormatValueError) as e:
            self.fail(f"Validation unexpectedly failed for metadata_headers=None: {e}")

    def test_thread_not_found(self):
        """Test behavior when a thread ID does not exist."""
        # This tests core logic behavior, assuming validation passes.
        result = get_thread(userId="existing_user@example.com", id="non_existent_thread")
        self.assertIsNone(result)

    def test_user_not_found_propagates_valueerror(self):
        """Test that ValueError from _ensure_user is propagated."""
        # This tests that errors from internal helpers are not suppressed by new validation.
        self.assert_error_behavior(
            func_to_call=get_thread,
            expected_exception_type=ValueError, # Propagated from _ensure_user
            expected_message="User 'unknown_user@example.com' does not exist.",
            userId="unknown_user@example.com",
            id="any_thread_id"
        )

    def test_list_valid_input_all_params(self):
        """Test list with all valid parameters specified."""
        try:
            result = list_threads(
                userId="existing_user@example.com",
                max_results=10,
                page_token="",   
                q="",
                labelIds=["SENT"],
                include_spam_trash=False
            )
            self.assertIsInstance(result, dict)
            self.assertEqual(result["resultSizeEstimate"], 1)   
            self.assertEqual(len(result["threads"]), 1)
            self.assertIsNone(result["nextPageToken"])
        except (TypeError, ValueError) as e:
            self.fail(f"Validation unexpectedly failed for valid input: {e}")
        except (KeyError, NameError) as e:
            self.fail(f"Core logic failed, ensure test data is correct or mocks are working: {e}")

    def test_list_valid_input_default_params(self):
        """Test list with default parameters."""
        try:
            result = list_threads(userId="existing_user@example.com")
            self.assertIsInstance(result, dict)
            self.assertEqual(result["resultSizeEstimate"], 1)
            self.assertEqual(len(result["threads"]), 1)
            self.assertIsNone(result["nextPageToken"])
        except (TypeError, ValueError) as e:
            self.fail(f"Validation unexpectedly failed for valid input: {e}")
        except (KeyError, NameError) as e:
            self.fail(f"Core logic failed, ensure test data is correct or mocks are working: {e}")

    def test_list_invalid_userid_type(self):
        """Test list with invalid userId type."""
        self.assert_error_behavior(
            func_to_call=list_threads,
            expected_exception_type=TypeError,
            expected_message="Argument 'userId' must be a string, but got int.",
            userId=123, 
            max_results=100,
            page_token="",
            q="",
            labelIds=["SENT"],
            include_spam_trash=False
        )

    def test_max_results_too_large(self):
        """Test list with maxResults too large."""
        self.assert_error_behavior(
            func_to_call=list_threads,
            expected_exception_type=ValueError,
            expected_message="Argument 'max_results' must be less than or equal to 500, but got 501.",
            max_results=501,
            page_token="",
            q="",
            labelIds=["SENT"],
            include_spam_trash=False
        )
        
    def test_invalid_max_results_type(self):
        """Test list with invalid maxResults type."""
        self.assert_error_behavior(
            func_to_call=list_threads,
            expected_exception_type=TypeError,
            expected_message="Argument 'max_results' must be an integer, but got str.",
            max_results="100",
            page_token="",
            q="",
            labelIds=["SENT"],
            include_spam_trash=False
        )
        
    def test_invalid_page_token_type(self):
        """Test list with invalid pageToken type."""
        self.assert_error_behavior(
            func_to_call=list_threads,
            expected_exception_type=TypeError,
            expected_message="Argument 'page_token' must be a string, but got int.",
            page_token=123,
            max_results=100,
            q="",
            labelIds=["SENT"],
            include_spam_trash=False
        )
        
    def test_invalid_q_type(self):
        """Test list with invalid q type."""
        self.assert_error_behavior(
            func_to_call=list_threads,
            expected_exception_type=TypeError,
            expected_message="Argument 'q' must be a string, but got int.",
            q=123,
            max_results=100,
            page_token="",
            labelIds=["SENT"],
            include_spam_trash=False
        )

    def test_invalid_label_ids_type(self):
        """Test list with invalid labelIds type."""
        self.assert_error_behavior(
            func_to_call=list_threads,
            expected_exception_type=TypeError,
            expected_message="Argument 'labelIds' must be a list of strings or None, but got int.",
            labelIds=123,
            max_results=100,
            page_token="",
            q="",
            include_spam_trash=False
        )

    def test_invalid_label_ids_element_type(self):
        """Test list with invalid element type in labelIds list."""
        self.assert_error_behavior(
            func_to_call=list_threads,
            expected_exception_type=TypeError,
            expected_message="All elements in 'labelIds' must be strings, but found element of type int.",
            labelIds=["SENT", 123, "DRAFTS"]
        )

    def test_invalid_include_spam_trash_type(self):
        """Test list with invalid includeSpamTrash type."""
        self.assert_error_behavior(
            func_to_call=list_threads,
            expected_exception_type=TypeError,
            expected_message="Argument 'include_spam_trash' must be a boolean, but got str.",
            include_spam_trash="True",
            max_results=100,
            page_token="",
            q="",
            labelIds=["SENT"]
        )

    def test_modify_valid_input_all_params(self):
        """Test modify with all valid parameters specified."""
        try:
            result = modify_thread_labels(
                userId="existing_user@example.com",
                id="threadxyz",
                addLabelIds=["IMPORTANT"],
                removeLabelIds=["SENT"]
            )
            self.assertIsInstance(result, dict)
            self.assertEqual(result["id"], "threadxyz")
        except (TypeError, ValueError) as e:
            self.fail(f"Validation unexpectedly failed for valid input: {e}")
        except (KeyError, NameError) as e:
            self.fail(f"Core logic failed, ensure test data is correct or mocks are working: {e}")

    def test_modify_valid_input_default_params(self):
        """Test modify with default parameters."""
        try:
            result = modify_thread_labels(userId="existing_user@example.com", id="threadxyz") # userId defaults to 'me'
            self.assertIsInstance(result, dict)
            self.assertEqual(result["id"], "threadxyz")
        except (TypeError, ValueError) as e:
            self.fail(f"Validation unexpectedly failed for valid input: {e}")
        except (KeyError, NameError) as e:
            self.fail(f"Core logic failed, ensure test data is correct or mocks are working: {e}")

    def test_modify_invalid_userid_type(self):
        """Test modify with invalid userId type."""
        self.assert_error_behavior(
            func_to_call=modify_thread_labels,
            expected_exception_type=TypeError,
            expected_message="Argument 'userId' must be a string, but got int.",
            userId=123,
            id="thread1"
        )

    def test_modify_invalid_id_type(self):
        """Test modify with invalid id type."""
        self.assert_error_behavior(
            func_to_call=modify_thread_labels,
            expected_exception_type=TypeError,
            expected_message="Argument 'id' must be a string, but got int.",
            userId="existing_user@example.com",
            id=12345
        )
        
    def test_modify_invalid_add_label_ids_type(self):
        """Test modify with invalid addLabelIds type."""
        self.assert_error_behavior(
            func_to_call=modify_thread_labels,
            expected_exception_type=TypeError,
            expected_message="Argument 'addLabelIds' must be a list of strings or None, but got int.",
            addLabelIds=123,
            id="thread1"
        )
        
    def test_modify_invalid_remove_label_ids_type(self):
        """Test modify with invalid removeLabelIds type."""
        self.assert_error_behavior(
            func_to_call=modify_thread_labels,
            expected_exception_type=TypeError,
            expected_message="Argument 'removeLabelIds' must be a list of strings or None, but got int.",
            removeLabelIds=123,
            id="thread1"
        )
        
    def test_modify_invalid_add_label_ids_element_type(self):
        """Test modify with invalid element type in addLabelIds list."""
        self.assert_error_behavior(
            func_to_call=modify_thread_labels,
            expected_exception_type=TypeError,
            expected_message="All elements in 'addLabelIds' must be strings, but found element of type int.",
            addLabelIds=["IMPORTANT", 123, "SENT"],
            id="thread1"
        )
        
    def test_modify_invalid_remove_label_ids_element_type(self):
        """Test modify with invalid element type in removeLabelIds list."""
        self.assert_error_behavior(
            func_to_call=modify_thread_labels,
            expected_exception_type=TypeError,
            expected_message="All elements in 'removeLabelIds' must be strings, but found element of type int.",
            removeLabelIds=["IMPORTANT", 123, "SENT"],
            id="thread1"
        )

    def test_modify_invalid_add_label_ids_length(self):
        """Test modify with invalid addLabelIds length."""
        self.assert_error_behavior(
            func_to_call=modify_thread_labels,
            expected_exception_type=ValueError,
            expected_message="Argument 'addLabelIds' cannot have more than 100 elements.",
            addLabelIds=["IMPORTANT"] * 101,
            id="thread1"
        )
        
    def test_modify_invalid_remove_label_ids_length(self):
        """Test modify with invalid removeLabelIds length."""
        self.assert_error_behavior(
            func_to_call=modify_thread_labels,
            expected_exception_type=ValueError,
            expected_message="Argument 'removeLabelIds' cannot have more than 100 elements.",
            removeLabelIds=["IMPORTANT"] * 101,
            id="thread1"
        )
        
    def test_modify_empty_id(self):
        """Test modify with empty id."""
        self.assert_error_behavior(
            func_to_call=modify_thread_labels,
            expected_exception_type=ValueError,
            expected_message="Argument 'id' cannot be empty.",
            userId="existing_user@example.com",
            id=""
        )

    def test_modify_whitespace_only_id(self):
        """Test modify with whitespace-only id that becomes empty after stripping."""
        self.assert_error_behavior(
            func_to_call=modify_thread_labels,
            expected_exception_type=ValueError,
            expected_message="Argument 'id' cannot be empty.",
            userId="existing_user@example.com",
            id="   "
        )

    def test_modify_id_with_leading_trailing_whitespace(self):
        """Test modify with id containing leading/trailing whitespace that gets stripped."""
        try:
            # This should work because after stripping " threadxyz " becomes "threadxyz"
            result = modify_thread_labels(
                userId="existing_user@example.com",
                id=" threadxyz ",
                addLabelIds=["IMPORTANT"]
            )
            self.assertIsInstance(result, dict)
            self.assertEqual(result["id"], "threadxyz")
        except (TypeError, ValueError) as e:
            self.fail(f"Validation unexpectedly failed for id with whitespace that strips to valid value: {e}")
        except (KeyError, NameError) as e:
            self.fail(f"Core logic failed, ensure test data is correct or mocks are working: {e}")

    def test_invalid_thread_id(self):
        """Test modify with invalid thread ID."""
        self.assert_error_behavior(
            func_to_call=modify_thread_labels,
            expected_exception_type=KeyError,
            expected_message="'Thread with ID non_existent_thread not available for user me.'",
            userId="me", 
            id="non_existent_thread"
        )    

    def test_delete_input_validation(self):
        """Test basic input validation for delete function."""
        # Test invalid userId type
        self.assert_error_behavior(
            func_to_call=delete_thread,
            expected_exception_type=TypeError,
            expected_message="userId must be a string, but got int.",
            userId=123,
            id="thread_1"
        )
        
        # Test invalid thread id type
        self.assert_error_behavior(
            func_to_call=delete_thread,
            expected_exception_type=TypeError,
            expected_message="id must be a string, but got int.",
            userId="me",
            id=123
        )
    
    def test_delete_empty_userid(self):
        """Test delete function with empty userId."""
        self.assert_error_behavior(
            func_to_call=delete_thread,
            expected_exception_type=ValidationError,
            expected_message="Argument 'userId' cannot be empty.",
            userId="",
            id="thread_1"
        )
    
    def test_delete_whitespace_userid(self):
        """Test delete function with whitespace-only userId."""
        self.assert_error_behavior(
            func_to_call=delete_thread,
            expected_exception_type=ValidationError,
            expected_message="Argument 'userId' cannot have only whitespace.",
            userId="   ",
            id="thread_1"
        )
    
    def test_delete_userid_with_spaces(self):
        """Test delete function with userId containing spaces."""
        self.assert_error_behavior(
            func_to_call=delete_thread,
            expected_exception_type=ValidationError,
            expected_message="Argument 'userId' cannot have whitespace.",
            userId="user name",
            id="thread_1"
        )
    
    def test_delete_id_with_spaces(self):
        """Test delete function with id containing spaces."""
        self.assert_error_behavior(
            func_to_call=delete_thread,
            expected_exception_type=ValidationError,
            expected_message="Argument 'id' cannot have whitespace.",
            userId="me",
            id="thread 1"
        )
    
    def test_delete_nonexistent_thread(self):
        """Test delete function with nonexistent thread."""
        # Should not raise an error, just return None
        result = delete_thread("me", "nonexistent_thread")
        self.assertIsNone(result)
    
    def test_delete_successful_deletion(self):
        """Test that delete function successfully deletes thread and messages."""
        # First, get a thread to delete
        threads_list = list_threads("me")
        if threads_list["threads"]:
            thread_id = threads_list["threads"][0]["id"]
            thread = get_thread("me", thread_id)
            message_ids = thread["messageIds"]
            
            # Delete the thread
            result = delete_thread("me", thread_id)
            self.assertIsNone(result)
            
            # Verify thread is deleted
            updated_threads = list_threads("me")
            remaining_thread_ids = [t["id"] for t in updated_threads["threads"]]
            self.assertNotIn(thread_id, remaining_thread_ids)
            
            # Verify messages are deleted
            for mid in message_ids:
                self.assertIsNone(get_message("me", mid))

    # ===== NEW TESTS FOR 'q' PARAMETER FUNCTIONALITY =====
    
    def test_list_threads_q_parameter_empty_query(self):
        """Test that empty query returns all threads."""
        result = list_threads("existing_user@example.com", q="")
        self.assertEqual(len(result["threads"]), 1)
        self.assertEqual(result["threads"][0]["id"], "threadxyz")
    
    def test_list_threads_q_parameter_label_search_sent(self):
        """Test label: search finds thread with SENT label."""
        result = list_threads("existing_user@example.com", q="label:SENT")
        self.assertEqual(len(result["threads"]), 1)
        self.assertEqual(result["threads"][0]["id"], "threadxyz")
    
    def test_list_threads_q_parameter_label_search_no_match(self):
        """Test label: search with non-matching label returns no results."""
        result = list_threads("existing_user@example.com", q="label:DRAFT")
        self.assertEqual(len(result["threads"]), 0)
    
    def test_list_threads_q_parameter_label_search_inbox_no_match(self):
        """Test label: search for INBOX returns no results since messages have SENT."""
        result = list_threads("existing_user@example.com", q="label:INBOX")
        self.assertEqual(len(result["threads"]), 0)
    
    # ===== INPUT VALIDATION TESTS FOR 'q' PARAMETER =====
    
    def test_list_threads_q_parameter_whitespace_only_validation(self):
        """Test that whitespace-only query raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_threads,
            expected_exception_type=ValueError,
            expected_message="q cannot be a string with only whitespace",
            userId="existing_user@example.com",
            q="   "
        )
    
    def test_list_threads_q_parameter_mixed_whitespace_validation(self):
        """Test that mixed whitespace-only query raises ValueError."""
        self.assert_error_behavior(
            func_to_call=list_threads,
            expected_exception_type=ValueError,
            expected_message="q cannot be a string with only whitespace",
            userId="existing_user@example.com",
            q="\t\n  \r"
        )
    
    # ===== BASIC FUNCTIONAL TESTS =====
    
    def test_list_threads_q_parameter_basic_functionality(self):
        """Test that q parameter is accepted and processed without errors using safe label queries."""
        # Use label-based query that doesn't require semantic processing
        result = list_threads("existing_user@example.com", q="label:NONEXISTENT")
        # Should return empty results but not crash
        self.assertEqual(len(result["threads"]), 0)
        self.assertIn("threads", result)
        self.assertIn("nextPageToken", result) 
        self.assertIn("resultSizeEstimate", result)
    
    def test_list_threads_q_parameter_with_max_results(self):
        """Test q parameter works with max_results parameter."""
        result = list_threads("existing_user@example.com", q="label:SENT", max_results=50)
        self.assertLessEqual(len(result["threads"]), 50)
        self.assertEqual(len(result["threads"]), 1)  # We have 1 thread with SENT label
    
    def test_list_threads_q_parameter_with_labelids(self):
        """Test q parameter works with labelIds parameter."""
        result = list_threads("existing_user@example.com", q="", labelIds=["SENT"])
        self.assertEqual(len(result["threads"]), 1)
        self.assertEqual(result["threads"][0]["id"], "threadxyz")
    
    def test_list_threads_q_parameter_combined_with_filters(self):
        """Test q parameter combined with other filter parameters."""
        result = list_threads("existing_user@example.com", q="label:SENT", labelIds=["SENT"], max_results=10)
        self.assertEqual(len(result["threads"]), 1)
        self.assertEqual(result["threads"][0]["id"], "threadxyz")

if __name__ == "__main__":
    unittest.main()
