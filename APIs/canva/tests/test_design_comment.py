# test_design_comment.py
import pytest
import time
from unittest.mock import patch, MagicMock
from canva.Canva.Design.Comment import create_thread, create_reply, get_thread, get_reply, list_replies
from canva.SimulationEngine.db import DB


class TestCreateThread:
    """Test cases for create_thread function"""
    
    def setup_method(self):
        """Reset DB before each test"""
        DB.clear()
        DB["Designs"] = {
            "design1": {
                "id": "design1",
                "title": "Test Design"
            }
        }
        DB["CommentThreads"] = {}
    
    def test_create_thread_success(self):
        """Test successful thread creation"""
        design_id = "design1"
        message = "This is a test comment"
        
        result = create_thread(design_id, message)
        
        assert "thread" in result
        thread = result["thread"]
        assert "id" in thread
        assert thread["design_id"] == design_id
        assert thread["content"]["plaintext"] == message
        assert thread["thread_type"]["type"] == "comment"
        assert "created_at" in thread
        assert "updated_at" in thread
        assert thread["id"] in DB["CommentThreads"]
    
    def test_create_thread_with_mentions(self):
        """Test thread creation with user mentions"""
        message = "Hey [user123:team456], can you review this?"
        
        result = create_thread("design1", message)
        thread = result["thread"]
        
        assert "mentions" in thread["content"]
        mentions = thread["content"]["mentions"]
        assert "user123:team456" in mentions
        assert mentions["user123:team456"]["tag"] == "@user123"
        assert mentions["user123:team456"]["user"]["user_id"] == "user123"
        assert mentions["user123:team456"]["user"]["team_id"] == "team456"
    
    def test_create_thread_with_assignee(self):
        """Test thread creation with assignee"""
        message = "Please review this [user123:team456]"
        assignee_id = "user123"
        
        result = create_thread("design1", message, assignee_id)
        thread = result["thread"]
        
        assert thread["assignee"] is not None
        assert thread["assignee"]["user_id"] == assignee_id
        assert thread["assignee"]["team_id"] == "default_team"
    
    def test_create_thread_assignee_not_mentioned(self):
        """Test thread creation where assignee is not mentioned in message"""
        message = "This is a comment without mentions"
        assignee_id = "user123"
        
        with pytest.raises(ValueError, match="assignee_id must be mentioned in the comment message"):
            create_thread("design1", message, assignee_id)
    
    def test_create_thread_multiple_mentions(self):
        """Test thread creation with multiple mentions"""
        message = "Hey [user1:team1] and [user2:team2], please review"
        
        result = create_thread("design1", message)
        thread = result["thread"]
        
        mentions = thread["content"]["mentions"]
        assert len(mentions) == 2
        assert "user1:team1" in mentions
        assert "user2:team2" in mentions
    
    def test_create_thread_invalid_design_id_not_string(self):
        """Test thread creation with non-string design_id"""
        with pytest.raises(ValueError, match="design_id must be a non-empty string"):
            create_thread(123, "message")
    
    def test_create_thread_empty_design_id(self):
        """Test thread creation with empty design_id"""
        with pytest.raises(ValueError, match="design_id must be a non-empty string"):
            create_thread("", "message")
    
    def test_create_thread_invalid_message_not_string(self):
        """Test thread creation with non-string message"""
        with pytest.raises(ValueError, match="message must be a non-empty string"):
            create_thread("design1", 123)
    
    def test_create_thread_empty_message(self):
        """Test thread creation with empty message"""
        with pytest.raises(ValueError, match="message must be a non-empty string"):
            create_thread("design1", "")
    
    def test_create_thread_invalid_assignee_id_not_string(self):
        """Test thread creation with non-string assignee_id"""
        with pytest.raises(ValueError, match="assignee_id must be a non-empty string if provided"):
            create_thread("design1", "message", 123)
    
    def test_create_thread_design_not_found(self):
        """Test thread creation with non-existent design"""
        with pytest.raises(ValueError, match="Design with ID nonexistent not found"):
            create_thread("nonexistent", "message")


class TestCreateReply:
    """Test cases for create_reply function"""
    
    def setup_method(self):
        """Setup test data"""
        DB.clear()
        DB["Designs"] = {
            "design1": {"id": "design1", "title": "Test Design"}
        }
        DB["CommentThreads"] = {
            "thread1": {
                "id": "thread1",
                "design_id": "design1",
                "content": {"plaintext": "Original thread"}
            }
        }
        DB["CommentReplies"] = {}
    
    def test_create_reply_success(self):
        """Test successful reply creation"""
        design_id = "design1"
        thread_id = "thread1"
        message = "This is a reply"
        
        result = create_reply(design_id, thread_id, message)
        
        assert "reply" in result
        reply = result["reply"]
        assert "id" in reply
        assert reply["design_id"] == design_id
        assert reply["thread_id"] == thread_id
        assert reply["content"]["plaintext"] == message
        assert "created_at" in reply
        assert "updated_at" in reply
        assert reply["id"] in DB["CommentReplies"]
    
    def test_create_reply_with_mentions(self):
        """Test reply creation with mentions"""
        message = "Thanks [user123:team456] for the feedback"
        
        result = create_reply("design1", "thread1", message)
        reply = result["reply"]
        
        mentions = reply["content"]["mentions"]
        assert "user123:team456" in mentions
        assert mentions["user123:team456"]["tag"] == "@user123"
    
    def test_create_reply_invalid_design_id(self):
        """Test reply creation with invalid design_id"""
        with pytest.raises(ValueError, match="design_id must be a non-empty string"):
            create_reply("", "thread1", "message")
    
    def test_create_reply_invalid_thread_id(self):
        """Test reply creation with invalid thread_id"""
        with pytest.raises(ValueError, match="thread_id must be a non-empty string"):
            create_reply("design1", "", "message")
    
    def test_create_reply_design_not_found(self):
        """Test reply creation with non-existent design"""
        with pytest.raises(ValueError, match="Design with ID nonexistent not found"):
            create_reply("nonexistent", "thread1", "message")
    
    def test_create_reply_thread_not_found(self):
        """Test reply creation with non-existent thread"""
        with pytest.raises(ValueError, match="Thread with ID nonexistent not found"):
            create_reply("design1", "nonexistent", "message")
    
    def test_create_reply_thread_wrong_design(self):
        """Test reply creation when thread belongs to different design"""
        # Add another design and thread
        DB["Designs"]["design2"] = {"id": "design2", "title": "Other Design"}
        DB["CommentThreads"]["thread2"] = {
            "id": "thread2",
            "design_id": "design2",
            "content": {"plaintext": "Other thread"}
        }
        
        with pytest.raises(ValueError, match="Thread thread2 does not belong to design design1"):
            create_reply("design1", "thread2", "message")


class TestGetThread:
    """Test cases for get_thread function"""
    
    def setup_method(self):
        """Setup test data"""
        DB.clear()
        DB["Designs"] = {
            "design1": {"id": "design1", "title": "Test Design"}
        }
        DB["CommentThreads"] = {
            "thread1": {
                "id": "thread1",
                "design_id": "design1",
                "content": {"plaintext": "Test thread"},
                "created_at": 1000000000
            }
        }
    
    def test_get_thread_success(self):
        """Test successful thread retrieval"""
        result = get_thread("design1", "thread1")
        
        assert "thread" in result
        thread = result["thread"]
        assert thread["id"] == "thread1"
        assert thread["design_id"] == "design1"
        assert thread["content"]["plaintext"] == "Test thread"
    
    def test_get_thread_invalid_design_id(self):
        """Test thread retrieval with invalid design_id"""
        with pytest.raises(ValueError, match="design_id must be a non-empty string"):
            get_thread("", "thread1")
    
    def test_get_thread_invalid_thread_id(self):
        """Test thread retrieval with invalid thread_id"""
        with pytest.raises(ValueError, match="thread_id must be a non-empty string"):
            get_thread("design1", "")
    
    def test_get_thread_design_not_found(self):
        """Test thread retrieval with non-existent design"""
        with pytest.raises(ValueError, match="Design with ID nonexistent not found"):
            get_thread("nonexistent", "thread1")
    
    def test_get_thread_thread_not_found(self):
        """Test thread retrieval with non-existent thread"""
        with pytest.raises(ValueError, match="Thread with ID nonexistent not found"):
            get_thread("design1", "nonexistent")
    
    def test_get_thread_thread_wrong_design(self):
        """Test thread retrieval when thread belongs to different design"""
        DB["Designs"]["design2"] = {"id": "design2", "title": "Other Design"}
        DB["CommentThreads"]["thread2"] = {
            "id": "thread2",
            "design_id": "design2",
            "content": {"plaintext": "Other thread"}
        }
        
        with pytest.raises(ValueError, match="Thread thread2 does not belong to design design1"):
            get_thread("design1", "thread2")


class TestGetReply:
    """Test cases for get_reply function"""
    
    def setup_method(self):
        """Setup test data"""
        DB.clear()
        DB["Designs"] = {
            "design1": {"id": "design1", "title": "Test Design"}
        }
        DB["CommentThreads"] = {
            "thread1": {
                "id": "thread1",
                "design_id": "design1",
                "content": {"plaintext": "Test thread"}
            }
        }
        DB["CommentReplies"] = {
            "reply1": {
                "id": "reply1",
                "design_id": "design1",
                "thread_id": "thread1",
                "content": {"plaintext": "Test reply"}
            }
        }
    
    def test_get_reply_success(self):
        """Test successful reply retrieval"""
        result = get_reply("design1", "thread1", "reply1")
        
        assert "reply" in result
        reply = result["reply"]
        assert reply["id"] == "reply1"
        assert reply["design_id"] == "design1"
        assert reply["thread_id"] == "thread1"
    
    def test_get_reply_invalid_ids(self):
        """Test reply retrieval with invalid IDs"""
        with pytest.raises(ValueError, match="design_id must be a non-empty string"):
            get_reply("", "thread1", "reply1")
        
        with pytest.raises(ValueError, match="thread_id must be a non-empty string"):
            get_reply("design1", "", "reply1")
        
        with pytest.raises(ValueError, match="reply_id must be a non-empty string"):
            get_reply("design1", "thread1", "")
    
    def test_get_reply_design_not_found(self):
        """Test reply retrieval with non-existent design"""
        with pytest.raises(ValueError, match="Design with ID nonexistent not found"):
            get_reply("nonexistent", "thread1", "reply1")
    
    def test_get_reply_thread_not_found(self):
        """Test reply retrieval with non-existent thread"""
        with pytest.raises(ValueError, match="Thread with ID nonexistent not found"):
            get_reply("design1", "nonexistent", "reply1")
    
    def test_get_reply_reply_not_found(self):
        """Test reply retrieval with non-existent reply"""
        with pytest.raises(ValueError, match="Reply with ID nonexistent not found"):
            get_reply("design1", "thread1", "nonexistent")
    
    def test_get_reply_reply_wrong_thread(self):
        """Test reply retrieval when reply belongs to different thread"""
        DB["CommentThreads"]["thread2"] = {
            "id": "thread2",
            "design_id": "design1",
            "content": {"plaintext": "Other thread"}
        }
        DB["CommentReplies"]["reply2"] = {
            "id": "reply2",
            "design_id": "design1",
            "thread_id": "thread2",
            "content": {"plaintext": "Other reply"}
        }
        
        with pytest.raises(ValueError, match="Reply reply2 does not belong to thread thread1"):
            get_reply("design1", "thread1", "reply2")


class TestListReplies:
    """Test cases for list_replies function"""
    
    def setup_method(self):
        """Setup test data"""
        DB.clear()
        DB["Designs"] = {
            "design1": {"id": "design1", "title": "Test Design"}
        }
        DB["CommentThreads"] = {
            "thread1": {
                "id": "thread1",
                "design_id": "design1",
                "content": {"plaintext": "Test thread"}
            }
        }
        DB["CommentReplies"] = {
            "reply1": {
                "id": "reply1",
                "design_id": "design1",
                "thread_id": "thread1",
                "content": {"plaintext": "First reply"},
                "created_at": 1000000001
            },
            "reply2": {
                "id": "reply2",
                "design_id": "design1", 
                "thread_id": "thread1",
                "content": {"plaintext": "Second reply"},
                "created_at": 1000000002
            },
            "reply3": {
                "id": "reply3",
                "design_id": "design1",
                "thread_id": "thread1", 
                "content": {"plaintext": "Third reply"},
                "created_at": 1000000003
            },
            "other_reply": {
                "id": "other_reply",
                "design_id": "design1",
                "thread_id": "other_thread",
                "content": {"plaintext": "Other thread reply"},
                "created_at": 1000000004
            }
        }
    
    def test_list_replies_success(self):
        """Test successful reply listing"""
        result = list_replies("design1", "thread1")
        
        assert "items" in result
        items = result["items"]
        assert len(items) == 3  # Only replies for thread1
        
        # Should be sorted by created_at (oldest first)
        timestamps = [item["created_at"] for item in items]
        assert timestamps == sorted(timestamps)
    
    def test_list_replies_with_limit(self):
        """Test reply listing with limit"""
        result = list_replies("design1", "thread1", limit=2)
        
        items = result["items"]
        assert len(items) == 2
        assert "continuation" in result  # Should have more results
    
    def test_list_replies_with_continuation(self):
        """Test reply listing with continuation token"""
        # Get first page
        first_page = list_replies("design1", "thread1", limit=1)
        assert len(first_page["items"]) == 1
        
        # Get second page using continuation
        continuation = first_page["continuation"]
        second_page = list_replies("design1", "thread1", limit=1, continuation=continuation)
        
        assert len(second_page["items"]) == 1
        assert second_page["items"][0]["id"] != first_page["items"][0]["id"]
    
    def test_list_replies_no_replies(self):
        """Test reply listing when no replies exist"""
        # Should fail because thread doesn't exist
        with pytest.raises(ValueError, match="Thread with ID nonexistent_thread not found"):
            list_replies("design1", "nonexistent_thread")
    
    def test_list_replies_empty_thread(self):
        """Test reply listing for thread with no replies"""
        DB["CommentThreads"]["empty_thread"] = {
            "id": "empty_thread",
            "design_id": "design1",
            "content": {"plaintext": "Empty thread"}
        }
        
        result = list_replies("design1", "empty_thread")
        assert result["items"] == []
    
    def test_list_replies_invalid_limit(self):
        """Test reply listing with invalid limit"""
        with pytest.raises(ValueError, match="limit must be an integer between 1 and 100"):
            list_replies("design1", "thread1", limit=0)
        
        with pytest.raises(ValueError, match="limit must be an integer between 1 and 100"):
            list_replies("design1", "thread1", limit=101)
    
    def test_list_replies_invalid_continuation(self):
        """Test reply listing with invalid continuation token"""
        with pytest.raises(ValueError, match="Invalid continuation token"):
            list_replies("design1", "thread1", continuation="invalid_token")
    
    def test_list_replies_invalid_ids(self):
        """Test reply listing with invalid IDs"""
        with pytest.raises(ValueError, match="design_id must be a non-empty string"):
            list_replies("", "thread1")
        
        with pytest.raises(ValueError, match="thread_id must be a non-empty string"):
            list_replies("design1", "")
    
    def test_list_replies_design_not_found(self):
        """Test reply listing with non-existent design"""
        with pytest.raises(ValueError, match="Design with ID nonexistent not found"):
            list_replies("nonexistent", "thread1")
    
    def test_list_replies_thread_not_found(self):
        """Test reply listing with non-existent thread"""
        with pytest.raises(ValueError, match="Thread with ID nonexistent not found"):
            list_replies("design1", "nonexistent")


if __name__ == "__main__":
    pytest.main([__file__])
