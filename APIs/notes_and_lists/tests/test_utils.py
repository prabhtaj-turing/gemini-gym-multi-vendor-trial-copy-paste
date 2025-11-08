# notes_and_lists/tests/test_utils.py
import unittest
import copy
from unittest.mock import patch, MagicMock

# Import the utils module and DB to test
from ..SimulationEngine import utils
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestConsistencyMaintenanceFunctions(BaseTestCaseWithErrorHandler):
    """
    Test suite for consistency maintenance functions in utils.py
    """
    
    def setUp(self):
        """Prepare isolated DB state for each test"""
        # Create a pristine copy of the DB for testing
        self.original_db_state = {
            'notes': copy.deepcopy(DB["notes"]),
            'lists': copy.deepcopy(DB["lists"]),
            'title_index': copy.deepcopy(DB["title_index"]),
            'content_index': copy.deepcopy(DB["content_index"]),
            'operation_log': copy.deepcopy(DB["operation_log"])
        }
        
        # Clear DB for clean test state
        DB["notes"].clear()
        DB["lists"].clear()
        DB["title_index"].clear()
        DB["content_index"].clear()
        DB["operation_log"].clear()
        
    def tearDown(self):
        """Restore original DB state after each test"""
        DB["notes"].clear()
        DB["lists"].clear()
        DB["title_index"].clear()
        DB["content_index"].clear()
        DB["operation_log"].clear()
        
        DB["notes"].update(self.original_db_state['notes'])
        DB["lists"].update(self.original_db_state['lists'])
        DB["title_index"].update(self.original_db_state['title_index'])
        DB["content_index"].update(self.original_db_state['content_index'])
        DB["operation_log"].update(self.original_db_state['operation_log'])
        
    def test_update_title_index_new_title(self):
        """Test updating title index with a new title"""
        title = "My New Note"
        item_id = "note_123"
        
        utils.update_title_index(title, item_id)
        
        self.assertIn(title, DB["title_index"])
        self.assertIn(item_id, DB["title_index"][title])
        self.assertEqual(len(DB["title_index"][title]), 1)
        
    def test_update_title_index_existing_title(self):
        """Test updating title index with an existing title"""
        title = "Existing Title"
        item_id1 = "note_123"
        item_id2 = "note_456"
        
        utils.update_title_index(title, item_id1)
        utils.update_title_index(title, item_id2)
        
        self.assertIn(title, DB["title_index"])
        self.assertIn(item_id1, DB["title_index"][title])
        self.assertIn(item_id2, DB["title_index"][title])
        self.assertEqual(len(DB["title_index"][title]), 2)
        
    def test_update_title_index_remove_old_reference(self):
        """Test that old references are removed when updating title"""
        old_title = "Old Title"
        new_title = "New Title"
        item_id = "note_123"
        
        # Add to old title
        utils.update_title_index(old_title, item_id)
        self.assertIn(item_id, DB["title_index"][old_title])
        
        # Update to new title
        utils.update_title_index(new_title, item_id)
        
        # Old title should be removed if empty
        self.assertNotIn(old_title, DB["title_index"])
        self.assertIn(new_title, DB["title_index"])
        self.assertIn(item_id, DB["title_index"][new_title])
        
    def test_update_title_index_none_title(self):
        """Test updating title index with None title does nothing"""
        item_id = "note_123"
        
        utils.update_title_index(None, item_id)
        
        self.assertEqual(len(DB["title_index"]), 0)
        
    def test_update_content_index(self):
        """Test updating content index with keywords"""
        item_id = "note_123"
        content = "This is a test note about Python programming"
        
        utils.update_content_index(item_id, content)
        
        # Check that keywords are indexed
        self.assertIn("test", DB["content_index"])
        self.assertIn("note", DB["content_index"])
        self.assertIn("python", DB["content_index"])
        self.assertIn("programming", DB["content_index"])
        
        # Check that item_id is in each keyword's list
        self.assertIn(item_id, DB["content_index"]["test"])
        self.assertIn(item_id, DB["content_index"]["note"])
        self.assertIn(item_id, DB["content_index"]["python"])
        self.assertIn(item_id, DB["content_index"]["programming"])
        
    def test_update_content_index_filters_short_words(self):
        """Test that short words are filtered out of content index"""
        item_id = "note_123"
        content = "A is to be or not to be"
        
        utils.update_content_index(item_id, content)
        
        # Short words (2 characters or less) should not be indexed
        self.assertNotIn("a", DB["content_index"])
        self.assertNotIn("is", DB["content_index"])
        self.assertNotIn("to", DB["content_index"])
        self.assertNotIn("be", DB["content_index"])  # Only 2 characters
        self.assertNotIn("or", DB["content_index"])  # Only 2 characters
        
        # Words with 3+ characters should be indexed
        self.assertIn("not", DB["content_index"])  # 3 characters, so it gets indexed
        
    def test_remove_from_indexes(self):
        """Test removing item from all indexes"""
        item_id = "note_123"
        title = "Test Note"
        content = "Test content for indexing"
        
        # Add to indexes
        utils.update_title_index(title, item_id)
        utils.update_content_index(item_id, content)
        
        # Verify it's in indexes
        self.assertIn(item_id, DB["title_index"][title])
        self.assertIn(item_id, DB["content_index"]["test"])
        
        # Remove from indexes
        utils.remove_from_indexes(item_id)
        
        # Verify it's removed
        self.assertNotIn(title, DB["title_index"])
        self.assertNotIn("test", DB["content_index"])
        
    def test_maintain_note_history(self):
        """Test maintaining note content history"""
        note_id = "note_123"
        old_content = "Old content"
        new_content = "New content"
        
        # Create note
        DB["notes"][note_id] = {
            "id": note_id,
            "content": new_content,
            "content_history": []
        }
        
        utils.maintain_note_history(note_id, old_content)
        
        # Check history was maintained
        self.assertEqual(len(DB["notes"][note_id]["content_history"]), 1)
        self.assertEqual(DB["notes"][note_id]["content_history"][0], old_content)
        
    def test_maintain_note_history_max_limit(self):
        """Test that note history is limited to 10 entries"""
        note_id = "note_123"
        
        DB["notes"][note_id] = {
            "id": note_id,
            "content": "current content",
            "content_history": [f"old_content_{i}" for i in range(10)]
        }
        
        utils.maintain_note_history(note_id, "new_old_content")
        
        # Should still be 10 entries, with oldest removed
        self.assertEqual(len(DB["notes"][note_id]["content_history"]), 10)
        self.assertEqual(DB["notes"][note_id]["content_history"][-1], "new_old_content")
        self.assertNotIn("old_content_0", DB["notes"][note_id]["content_history"])
        
    def test_maintain_list_item_history(self):
        """Test maintaining list item history"""
        list_id = "list_123"
        item_id = "item_456"
        old_content = "Old item content"
        new_content = "New item content"
        
        # Create list with item
        DB["lists"][list_id] = {
            "id": list_id,
            "items": {
                item_id: {"content": new_content}
            },
            "item_history": {}
        }
        
        utils.maintain_list_item_history(list_id, item_id, old_content)
        
        # Check history was maintained
        self.assertIn(item_id, DB["lists"][list_id]["item_history"])
        self.assertEqual(len(DB["lists"][list_id]["item_history"][item_id]), 1)
        self.assertEqual(DB["lists"][list_id]["item_history"][item_id][0], old_content)

    def test_maintain_list_item_history_max_limit(self):
        """Test that list item history is limited to 5 entries"""
        list_id = "list_123"
        item_id = "item_456"
        
        DB["lists"][list_id] = {
            "id": list_id,
            "items": {
                item_id: {"content": "current content"}
            },
            "item_history": {
                item_id: [f"old_content_{i}" for i in range(5)]
            }
        }
        
        utils.maintain_list_item_history(list_id, item_id, "new_old_content")
        
        # Should still be 5 entries, with oldest removed
        self.assertEqual(len(DB["lists"][list_id]["item_history"][item_id]), 5)
        self.assertEqual(DB["lists"][list_id]["item_history"][item_id][-1], "new_old_content")
        self.assertNotIn("old_content_0", DB["lists"][list_id]["item_history"][item_id])


class TestUtilityInteractionFunctions(BaseTestCaseWithErrorHandler):
    """
    Test suite for utility and interaction functions in utils.py
    """
    
    def setUp(self):
        """Prepare isolated DB state for each test"""
        # Create a pristine copy of the DB for testing
        self.original_db_state = {
            'notes': copy.deepcopy(DB["notes"]),
            'lists': copy.deepcopy(DB["lists"]),
            'title_index': copy.deepcopy(DB["title_index"]),
            'content_index': copy.deepcopy(DB["content_index"]),
            'operation_log': copy.deepcopy(DB["operation_log"])
        }
        
        # Clear DB for clean test state
        DB["notes"].clear()
        DB["lists"].clear()
        DB["title_index"].clear()
        DB["content_index"].clear()
        DB["operation_log"].clear()
        
        # Add test data
        self.test_note_id = "note_123"
        self.test_list_id = "list_456"
        self.test_item_id = "item_789"
        
        DB["notes"][self.test_note_id] = {
            "id": self.test_note_id,
            "title": "Test Note",
            "content": "This is a test note about Python programming",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "content_history": []
        }
        
        DB["lists"][self.test_list_id] = {
            "id": self.test_list_id,
            "title": "Test List",
            "items": {
                self.test_item_id: {
                    "id": self.test_item_id,
                    "content": "Test item content",
                    "completed": False,
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00"
                }
            },
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "item_history": {}
        }
        
        # Update indexes
        utils.update_title_index("Test Note", self.test_note_id)
        utils.update_title_index("Test List", self.test_list_id)
        utils.update_content_index(self.test_note_id, "This is a test note about Python programming")
        utils.update_content_index(self.test_item_id, "Test item content")
        
    def tearDown(self):
        """Restore original DB state after each test"""
        DB["notes"].clear()
        DB["lists"].clear()
        DB["title_index"].clear()
        DB["content_index"].clear()
        DB["operation_log"].clear()
        
        DB["notes"].update(self.original_db_state['notes'])
        DB["lists"].update(self.original_db_state['lists'])
        DB["title_index"].update(self.original_db_state['title_index'])
        DB["content_index"].update(self.original_db_state['content_index'])
        DB["operation_log"].update(self.original_db_state['operation_log'])
        
    def test_get_note_exists(self):
        """Test getting an existing note"""
        note = utils.get_note(self.test_note_id)
        
        self.assertIsNotNone(note)
        self.assertEqual(note["id"], self.test_note_id)
        self.assertEqual(note["title"], "Test Note")
        
    def test_get_note_not_exists(self):
        """Test getting a non-existent note"""
        note = utils.get_note("non_existent_id")
        
        self.assertIsNone(note)
        
    def test_get_list_exists(self):
        """Test getting an existing list"""
        lst = utils.get_list(self.test_list_id)
        
        self.assertIsNotNone(lst)
        self.assertEqual(lst["id"], self.test_list_id)
        self.assertEqual(lst["title"], "Test List")
        
    def test_get_list_not_exists(self):
        """Test getting a non-existent list"""
        lst = utils.get_list("non_existent_id")
        
        self.assertIsNone(lst)
        
    def test_get_list_item_exists(self):
        """Test getting an existing list item"""
        item = utils.get_list_item(self.test_list_id, self.test_item_id)
        
        self.assertIsNotNone(item)
        self.assertEqual(item["id"], self.test_item_id)
        self.assertEqual(item["content"], "Test item content")
        
    def test_get_list_item_list_not_exists(self):
        """Test getting item from non-existent list"""
        item = utils.get_list_item("non_existent_list", self.test_item_id)
        
        self.assertIsNone(item)
        
    def test_get_list_item_item_not_exists(self):
        """Test getting non-existent item from existing list"""
        item = utils.get_list_item(self.test_list_id, "non_existent_item")
        
        self.assertIsNone(item)
        
    def test_find_by_title_exists(self):
        """Test finding items by exact title match"""
        items = utils.find_by_title("Test Note")
        
        self.assertEqual(len(items), 1)
        self.assertIn(self.test_note_id, items)
        
    def test_find_by_title_not_exists(self):
        """Test finding items by non-existent title"""
        items = utils.find_by_title("Non Existent Title")
        
        self.assertEqual(len(items), 0)
        
    def test_find_by_keyword_exists(self):
        """Test finding items by keyword"""
        items = utils.find_by_keyword("test")
        
        self.assertGreater(len(items), 0)
        self.assertIn(self.test_note_id, items)
        
    def test_find_by_keyword_not_exists(self):
        """Test finding items by non-existent keyword"""
        items = utils.find_by_keyword("nonexistent")
        
        self.assertEqual(len(items), 0)
        
    def test_search_notes_and_lists_matches_note(self):
        """Test searching returns a matching note."""
        results = utils.search_notes_and_lists("Python")
        
        self.assertEqual(len(results["notes"]), 1)
        self.assertEqual(len(results["lists"]), 0)
        self.assertEqual(results["notes"][0]["id"], self.test_note_id)
        
    def test_search_notes_and_lists_matches_list(self):
        """Test searching returns a matching list."""
        results = utils.search_notes_and_lists("item content")
        
        self.assertEqual(len(results["notes"]), 0)
        self.assertEqual(len(results["lists"]), 1)
        self.assertEqual(results["lists"][0]["id"], self.test_list_id)
        
    def test_search_notes_and_lists_matches_both(self):
        """Test searching returns both notes and lists."""
        results = utils.search_notes_and_lists("Test")
        
        self.assertEqual(len(results["notes"]), 1)
        self.assertEqual(len(results["lists"]), 1)
        self.assertEqual(results["notes"][0]["id"], self.test_note_id)
        self.assertEqual(results["lists"][0]["id"], self.test_list_id)

    def test_search_notes_and_lists_no_match(self):
        """Test searching with no matching results."""
        results = utils.search_notes_and_lists("nonexistent")
        
        self.assertEqual(len(results["notes"]), 0)
        self.assertEqual(len(results["lists"]), 0)
        
    def test_search_notes_and_lists_type_error(self):
        """Test that a non-string query raises TypeError"""
        with self.assertRaises(TypeError):
            utils.search_notes_and_lists(12345)
            
    @patch('uuid.uuid4')
    def test_create_note_with_title(self, mock_uuid):
        """Test creating a note with explicit title"""
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = MagicMock(return_value="12345678-1234-1234-1234-123456789012")
        
        title = "New Note Title"
        content = "New note content"
        
        note = utils.create_note(title, content)
        
        self.assertEqual(note["title"], title)
        self.assertEqual(note["content"], content)
        self.assertIn("note_12345678", note["id"])
        self.assertIn(note["id"], DB["notes"])
        
    @patch('uuid.uuid4')
    def test_create_note_auto_title(self, mock_uuid):
        """Test creating a note with automatic title generation"""
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = MagicMock(return_value="12345678-1234-1234-1234-123456789012")
        
        content = "This is a long note content that should be truncated for the title"
        
        note = utils.create_note(None, content)
        
        self.assertEqual(note["title"], content[:50] + "...")
        self.assertEqual(note["content"], content)
        self.assertIn("note_12345678", note["id"])
        
    def test_add_to_list_existing_list(self):
        """Test adding items to an existing list"""
        items_to_add = ["New item 1", "New item 2"]
        
        result = utils.add_to_list(self.test_list_id, items_to_add)
        
        self.assertEqual(result["id"], self.test_list_id)
        # Should have original item plus 2 new items
        self.assertEqual(len(result["items"]), 3)
        
        # Check that new items were added
        item_contents = [item["content"] for item in result["items"].values()]
        self.assertIn("New item 1", item_contents)
        self.assertIn("New item 2", item_contents)
        
    def test_add_to_list_nonexistent_list(self):
        """Test adding items to a non-existent list raises error"""
        items_to_add = ["New item 1"]
        
        self.assert_error_behavior(
            lambda: utils.add_to_list("non_existent_list", items_to_add),
            ValueError,
            "List non_existent_list not found"
        )
        
    @patch('uuid.uuid4')
    def test_log_operation(self, mock_uuid):
        """Test logging an operation"""
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = MagicMock(return_value="12345678-1234-1234-1234-123456789012")
        
        operation_type = "CREATE"
        target_id = self.test_note_id
        parameters = {"title": "Test Note", "content": "Test content"}
        
        op_id = utils.log_operation(operation_type, target_id, parameters)
        
        self.assertIn("op_12345678", op_id)
        self.assertIn(op_id, DB["operation_log"])
        
        logged_op = DB["operation_log"][op_id]
        self.assertEqual(logged_op["operation_type"], operation_type)
        self.assertEqual(logged_op["target_id"], target_id)
        self.assertEqual(logged_op["parameters"], parameters)
        self.assertIsNotNone(logged_op["snapshot"])
        
    def test_get_recent_operations(self):
        """Test getting recent operations"""
        # Add some operations
        for i in range(15):
            op_id = f"op_{i}"
            DB["operation_log"][op_id] = {
                "id": op_id,
                "operation_type": "TEST",
                "target_id": f"target_{i}",
                "parameters": {},
                "timestamp": f"2023-01-01T00:00:{i:02d}",
                "snapshot": {}
            }
        
        # Get recent operations (default limit 10)
        recent_ops = utils.get_recent_operations()
        
        self.assertEqual(len(recent_ops), 10)
        # Should be sorted by timestamp, most recent first
        self.assertEqual(recent_ops[0]["id"], "op_14")
        self.assertEqual(recent_ops[-1]["id"], "op_5")
        
    def test_get_recent_operations_custom_limit(self):
        """Test getting recent operations with custom limit"""
        # Add some operations
        for i in range(10):
            op_id = f"op_{i}"
            DB["operation_log"][op_id] = {
                "id": op_id,
                "operation_type": "TEST",
                "target_id": f"target_{i}",
                "parameters": {},
                "timestamp": f"2023-01-01T00:00:{i:02d}",
                "snapshot": {}
            }
        
        # Get recent operations with limit 5
        recent_ops = utils.get_recent_operations(limit=5)
        
        self.assertEqual(len(recent_ops), 5)
        self.assertEqual(recent_ops[0]["id"], "op_9")
        self.assertEqual(recent_ops[-1]["id"], "op_5")

    def test_filter_items_by_completed(self):
        """Test filtering items by completed status"""
        items = utils.filter_items_by_completed_status(self.test_list_id, completed=False)
        
        self.assertEqual(len(items), 1)
        
    def test_filter_items_by_completed_invalid_list(self):
        """Test filtering items by completed status with invalid list"""
        self.assert_error_behavior(
            lambda: utils.filter_items_by_completed_status("non_existent_list", completed=True),
            ValueError,
            "List non_existent_list not found"
        )
        
    def test_filter_items_by_completed_invalid_completed(self):
        """Test filtering items by completed status with invalid completed"""
        self.assert_error_behavior(
            lambda: utils.filter_items_by_completed_status(self.test_list_id, completed="invalid"),
            TypeError,
            "Argument 'completed' must be a boolean or None."
        )
        
    def test_filter_items_by_completed_invalid_list_id(self):
        """Test filtering items by completed status with invalid list_id"""
        self.assert_error_behavior(
            lambda: utils.filter_items_by_completed_status(123, completed=True),
            TypeError,
            "Argument 'list_id' must be a string."
        )
        
    def test_filter_items_by_completed_status_invalid_completed(self):
        """Test filtering items by completed status with invalid completed"""
        self.assert_error_behavior(
            lambda: utils.filter_items_by_completed_status(self.test_list_id, completed="invalid"),
            TypeError,
            "Argument 'completed' must be a boolean or None."
        )
        
    def test_filter_items_by_completed_empty_list(self):
        """Test filtering items by completed status with empty list"""
        DB["lists"][self.test_list_id] = {
            "id": self.test_list_id,
            "items": {},
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        items = utils.filter_items_by_completed_status(self.test_list_id, completed=True)
        
        self.assertEqual(len(items), 0)
        
    def test_filter_items_by_completed_nonexistent_list(self):
        """Test filtering items by completed status with nonexistent list"""
        self.assert_error_behavior(
            lambda: utils.filter_items_by_completed_status("non_existent_list", completed=True),
            ValueError,
            "List non_existent_list not found"
        )

    def test_mark_item_as_completed(self):
        """Test marking an item as completed"""
        utils.mark_item_as_completed(self.test_list_id, self.test_item_id)

        self.assertEqual(DB["lists"][self.test_list_id]["items"][self.test_item_id]["completed"], True)

    def test_mark_item_as_completed_nonexistent_list(self):
        """Test marking an item as completed with nonexistent list"""
        self.assert_error_behavior(
            lambda: utils.mark_item_as_completed("non_existent_list", self.test_item_id),
            ValueError,
            "List non_existent_list not found"
        )
    
    def test_mark_item_as_completed_invalid_list_id(self):
        """Test marking an item as completed with invalid list_id"""
        self.assert_error_behavior(
            lambda: utils.mark_item_as_completed(123, self.test_item_id),
            TypeError,
            "Argument 'list_id' must be a string."
        )
    
    def test_mark_item_as_completed_invalid_item_id(self):
        """Test marking an item as completed with invalid item_id"""
        self.assert_error_behavior(
            lambda: utils.mark_item_as_completed(self.test_list_id, "invalid_item_id"),
            ValueError,
            "Item invalid_item_id not found in list list_456"
        )
    
    def test_mark_item_as_completed_invalid_item_id_type(self):
        """Test marking an item as completed with invalid item_id type"""
        self.assert_error_behavior(
            lambda: utils.mark_item_as_completed(self.test_list_id, 123),
            TypeError,
            "Argument 'item_id' must be a string."
        )
    
    def test_mark_item_as_completed_invalid_list_id_type(self):
        """Test marking an item as completed with invalid list_id type"""
        self.assert_error_behavior(
            lambda: utils.mark_item_as_completed(123, self.test_item_id),
            TypeError,
            "Argument 'list_id' must be a string."
        )
    def test_find_items_by_search_found(self):
        """Test finding items by search text"""
        found_notes, found_lists = utils.find_items_by_search("Python")
        
        self.assertEqual(len(found_notes), 1)
        self.assertEqual(len(found_lists), 0)
        self.assertIn(self.test_note_id, found_notes)
        
    def test_find_items_by_search_not_found(self):
        """Test search with no matching items"""
        found_notes, found_lists = utils.find_items_by_search("nonexistent")
        
        self.assertEqual(len(found_notes), 0)
        self.assertEqual(len(found_lists), 0)
        
    def test_find_items_by_search_case_insensitive(self):
        """Test that search is case-insensitive"""
        found_notes, found_lists = utils.find_items_by_search("test note")
        
        self.assertEqual(len(found_notes), 1)
        self.assertIn(self.test_note_id, found_notes)

    @patch('notes_and_lists.SimulationEngine.utils.search_engine_manager')
    def test_find_items_by_search_with_fallback_when_engine_is_none(self, mock_search_engine_manager):
        """Test that fallback text search is used when engine is None"""
        # Add test data
        test_note = {
            'fallback_note': {
                'id': 'fallback_note',
                'title': 'Fallback Test Note',
                'content': 'This note should be found by fallback search',
                'created_at': '2023-01-01T00:00:00Z',
                'updated_at': '2023-01-01T00:00:00Z',
                'content_history': []
            }
        }
        test_list = {
            'fallback_list': {
                'id': 'fallback_list',
                'title': 'Fallback Test List',
                'items': {
                    'item_1': {
                        'id': 'item_1',
                        'content': 'Fallback test item',
                        'created_at': '2023-01-01T00:00:00Z',
                        'updated_at': '2023-01-01T00:00:00Z'
                    }
                },
                'created_at': '2023-01-01T00:00:00Z',
                'updated_at': '2023-01-01T00:00:00Z',
                'item_history': {}
            }
        }
        DB["notes"].update(test_note)
        DB["lists"].update(test_list)
        
        # Mock the search engine manager to return None for engine
        mock_engine_manager = MagicMock()
        mock_engine_manager.get_engine.return_value = None
        mock_search_engine_manager.get_engine_manager.return_value = mock_engine_manager
        
        found_notes, found_lists = utils.find_items_by_search("fallback")
        
        # Should use fallback search and find the test data
        self.assertIsInstance(found_notes, set)
        self.assertIsInstance(found_lists, set)
        self.assertEqual(len(found_notes), 1)
        self.assertEqual(len(found_lists), 1)
        self.assertIn("fallback_note", found_notes)
        self.assertIn("fallback_list", found_lists)
        
        # Verify that the engine manager was called
        mock_search_engine_manager.get_engine_manager.assert_called_once_with("notes_and_lists")
        mock_engine_manager.reset_all_engines.assert_called_once()
        mock_engine_manager.get_engine.assert_called_once()

    @patch('notes_and_lists.SimulationEngine.utils.search_engine_manager')
    def test_find_items_by_search_with_metadata_note_results(self, mock_search_engine_manager):
        """Test find_items_by_search with metadata-based note results"""
        # Add test data
        test_note = {
            'metadata_note': {
                'id': 'metadata_note',
                'title': 'Metadata Test Note',
                'content': 'This note should be found via metadata search',
                'created_at': '2023-01-01T00:00:00Z',
                'updated_at': '2023-01-01T00:00:00Z',
                'content_history': []
            }
        }
        DB["notes"].update(test_note)
        
        # Mock search engine to return metadata-based results
        mock_engine = MagicMock()
        mock_engine_manager = MagicMock()
        mock_engine_manager.get_engine.return_value = mock_engine
        mock_search_engine_manager.get_engine_manager.return_value = mock_engine_manager
        
        # Create mock search result with metadata
        mock_result = MagicMock()
        mock_result.metadata = {
            'content_type': 'note',
            'note_id': 'metadata_note'
        }
        mock_engine.search.return_value = [mock_result]
        
        found_notes, found_lists = utils.find_items_by_search("metadata")
        
        # Should find the note via metadata
        self.assertIsInstance(found_notes, set)
        self.assertIsInstance(found_lists, set)
        self.assertEqual(len(found_notes), 1)
        self.assertEqual(len(found_lists), 0)
        self.assertIn("metadata_note", found_notes)

    @patch('notes_and_lists.SimulationEngine.utils.search_engine_manager')
    def test_find_items_by_search_with_metadata_list_results(self, mock_search_engine_manager):
        """Test find_items_by_search with metadata-based list results"""
        # Add test data
        test_list = {
            'metadata_list': {
                'id': 'metadata_list',
                'title': 'Metadata Test List',
                'items': {
                    'item_1': {
                        'id': 'item_1',
                        'content': 'Metadata test item',
                        'created_at': '2023-01-01T00:00:00Z',
                        'updated_at': '2023-01-01T00:00:00Z'
                    }
                },
                'created_at': '2023-01-01T00:00:00Z',
                'updated_at': '2023-01-01T00:00:00Z',
                'item_history': {}
            }
        }
        DB["lists"].update(test_list)
        
        # Mock search engine to return metadata-based results
        mock_engine = MagicMock()
        mock_engine_manager = MagicMock()
        mock_engine_manager.get_engine.return_value = mock_engine
        mock_search_engine_manager.get_engine_manager.return_value = mock_engine_manager
        
        # Create mock search result with metadata
        mock_result = MagicMock()
        mock_result.metadata = {
            'content_type': 'list',
            'list_id': 'metadata_list'
        }
        mock_engine.search.return_value = [mock_result]
        
        found_notes, found_lists = utils.find_items_by_search("metadata")
        
        # Should find the list via metadata
        self.assertIsInstance(found_notes, set)
        self.assertIsInstance(found_lists, set)
        self.assertEqual(len(found_notes), 0)
        self.assertEqual(len(found_lists), 1)
        self.assertIn("metadata_list", found_lists)

    @patch('notes_and_lists.SimulationEngine.utils.search_engine_manager')
    def test_find_items_by_search_with_metadata_missing_note_id(self, mock_search_engine_manager):
        """Test find_items_by_search with metadata but missing note_id"""
        # Mock search engine to return metadata-based results with missing note_id
        mock_engine = MagicMock()
        mock_engine_manager = MagicMock()
        mock_engine_manager.get_engine.return_value = mock_engine
        mock_search_engine_manager.get_engine_manager.return_value = mock_engine_manager
        
        # Create mock search result with metadata but no note_id
        mock_result = MagicMock()
        mock_result.metadata = {
            'content_type': 'note',
            'note_id': None  # Missing note_id
        }
        mock_engine.search.return_value = [mock_result]
        
        found_notes, found_lists = utils.find_items_by_search("test")
        
        # Should return empty results
        self.assertIsInstance(found_notes, set)
        self.assertIsInstance(found_lists, set)
        self.assertEqual(len(found_notes), 0)
        self.assertEqual(len(found_lists), 0)

    @patch('notes_and_lists.SimulationEngine.utils.search_engine_manager')
    def test_find_items_by_search_with_metadata_missing_list_id(self, mock_search_engine_manager):
        """Test find_items_by_search with metadata but missing list_id"""
        # Mock search engine to return metadata-based results with missing list_id
        mock_engine = MagicMock()
        mock_engine_manager = MagicMock()
        mock_engine_manager.get_engine.return_value = mock_engine
        mock_search_engine_manager.get_engine_manager.return_value = mock_engine_manager
        
        # Create mock search result with metadata but no list_id
        mock_result = MagicMock()
        mock_result.metadata = {
            'content_type': 'list',
            'list_id': None  # Missing list_id
        }
        mock_engine.search.return_value = [mock_result]
        
        found_notes, found_lists = utils.find_items_by_search("test")
        
        # Should return empty results
        self.assertIsInstance(found_notes, set)
        self.assertIsInstance(found_lists, set)
        self.assertEqual(len(found_notes), 0)
        self.assertEqual(len(found_lists), 0)

    @patch('notes_and_lists.SimulationEngine.utils.search_engine_manager')
    def test_find_items_by_search_with_original_json_obj_note_results(self, mock_search_engine_manager):
        """Test find_items_by_search with original_json_obj note results"""
        # Add test data
        test_note = {
            'json_note': {
                'id': 'json_note',
                'title': 'JSON Test Note',
                'content': 'This note should be found via original_json_obj',
                'created_at': '2023-01-01T00:00:00Z',
                'updated_at': '2023-01-01T00:00:00Z',
                'content_history': []
            }
        }
        DB["notes"].update(test_note)
        
        # Mock search engine to return original_json_obj results
        mock_engine = MagicMock()
        mock_engine_manager = MagicMock()
        mock_engine_manager.get_engine.return_value = mock_engine
        mock_search_engine_manager.get_engine_manager.return_value = mock_engine_manager
        
        # Create mock search result with original_json_obj
        class MockResult:
            def __init__(self):
                self.original_json_obj = {
                    'id': 'json_note',
                    'content': 'This note should be found via original_json_obj',
                    'title': "JSON Test Note"
                    # Note: no 'title' field to match the condition (title not in obj)
                }
        
        mock_result = MockResult()
        mock_engine.search.return_value = [mock_result]
        
        found_notes, found_lists = utils.find_items_by_search("json")
        
        # Should find the note via original_json_obj
        self.assertIsInstance(found_notes, set)
        self.assertIsInstance(found_lists, set)
        self.assertEqual(len(found_notes), 1)
        self.assertEqual(len(found_lists), 0)
        self.assertIn("json_note", found_notes)

    @patch('notes_and_lists.SimulationEngine.utils.search_engine_manager')
    def test_find_items_by_search_with_original_json_obj_list_results(self, mock_search_engine_manager):
        """Test find_items_by_search with original_json_obj list results"""
        # Add test data
        test_list = {
            'json_list': {
                'id': 'json_list',
                'title': 'JSON Test List',
                'items': {
                    'item_1': {
                        'id': 'item_1',
                        'content': 'JSON test item',
                        'created_at': '2023-01-01T00:00:00Z',
                        'updated_at': '2023-01-01T00:00:00Z'
                    }
                },
                'created_at': '2023-01-01T00:00:00Z',
                'updated_at': '2023-01-01T00:00:00Z',
                'item_history': {}
            }
        }
        DB["lists"].update(test_list)
        
        # Mock search engine to return original_json_obj results
        mock_engine = MagicMock()
        mock_engine_manager = MagicMock()
        mock_engine_manager.get_engine.return_value = mock_engine
        mock_search_engine_manager.get_engine_manager.return_value = mock_engine_manager
        
        # Create mock search result with original_json_obj
        class MockResult:
            def __init__(self):
                self.original_json_obj = {
                    'id': 'json_list',
                    'items': {'item_1': {'id': 'item_1', 'content': 'JSON test item'}}
                }
        
        mock_result = MockResult()
        mock_engine.search.return_value = [mock_result]
        
        found_notes, found_lists = utils.find_items_by_search("json")
        
        # Should find the list via original_json_obj
        self.assertIsInstance(found_notes, set)
        self.assertIsInstance(found_lists, set)
        self.assertEqual(len(found_notes), 0)
        self.assertEqual(len(found_lists), 1)
        self.assertIn("json_list", found_lists)

    @patch('notes_and_lists.SimulationEngine.utils.search_engine_manager')
    def test_find_items_by_search_with_direct_dict_note_results(self, mock_search_engine_manager):
        """Test find_items_by_search with direct dictionary note results"""
        # Add test data
        test_note = {
            'dict_note': {
                'id': 'dict_note',
                'title': 'Dict Test Note',
                'content': 'This note should be found via direct dict',
                'created_at': '2023-01-01T00:00:00Z',
                'updated_at': '2023-01-01T00:00:00Z',
                'content_history': []
            }
        }
        DB["notes"].update(test_note)
        
        # Mock search engine to return direct dictionary results
        mock_engine = MagicMock()
        mock_engine_manager = MagicMock()
        mock_engine_manager.get_engine.return_value = mock_engine
        mock_search_engine_manager.get_engine_manager.return_value = mock_engine_manager
        
        # Create mock search result as direct dictionary
        mock_result = {
            'id': 'dict_note',
            'content': 'This note should be found via direct dict',
            'title': 'Dict Test Note'  # Has title to match the condition
        }
        mock_engine.search.return_value = [mock_result]
        
        found_notes, found_lists = utils.find_items_by_search("dict")
        
        # Should find the note via direct dictionary
        self.assertIsInstance(found_notes, set)
        self.assertIsInstance(found_lists, set)
        self.assertEqual(len(found_notes), 1)
        self.assertEqual(len(found_lists), 0)
        self.assertIn("dict_note", found_notes)

    @patch('notes_and_lists.SimulationEngine.utils.search_engine_manager')
    def test_find_items_by_search_with_direct_dict_list_results(self, mock_search_engine_manager):
        """Test find_items_by_search with direct dictionary list results"""
        # Add test data
        test_list = {
            'dict_list': {
                'id': 'dict_list',
                'title': 'Dict Test List',
                'items': {
                    'item_1': {
                        'id': 'item_1',
                        'content': 'Dict test item',
                        'created_at': '2023-01-01T00:00:00Z',
                        'updated_at': '2023-01-01T00:00:00Z'
                    }
                },
                'created_at': '2023-01-01T00:00:00Z',
                'updated_at': '2023-01-01T00:00:00Z',
                'item_history': {}
            }
        }
        DB["lists"].update(test_list)
        
        # Mock search engine to return direct dictionary results
        mock_engine = MagicMock()
        mock_engine_manager = MagicMock()
        mock_engine_manager.get_engine.return_value = mock_engine
        mock_search_engine_manager.get_engine_manager.return_value = mock_engine_manager
        
        # Create mock search result as direct dictionary
        mock_result = {
            'id': 'dict_list',
            'items': {'item_1': {'id': 'item_1', 'content': 'Dict test item'}}
        }
        mock_engine.search.return_value = [mock_result]
        
        found_notes, found_lists = utils.find_items_by_search("dict")
        
        # Should find the list via direct dictionary
        self.assertIsInstance(found_notes, set)
        self.assertIsInstance(found_lists, set)
        self.assertEqual(len(found_notes), 0)
        self.assertEqual(len(found_lists), 1)
        self.assertIn("dict_list", found_lists)

    @patch('notes_and_lists.SimulationEngine.utils.search_engine_manager')
    def test_find_items_by_search_with_mixed_result_types(self, mock_search_engine_manager):
        """Test find_items_by_search with mixed result types (metadata, original_json_obj, and dict)"""
        # Add test data
        test_note = {
            'mixed_note': {
                'id': 'mixed_note',
                'title': 'Mixed Test Note',
                'content': 'This note should be found via mixed search',
                'created_at': '2023-01-01T00:00:00Z',
                'updated_at': '2023-01-01T00:00:00Z',
                'content_history': []
            }
        }
        test_list = {
            'mixed_list': {
                'id': 'mixed_list',
                'title': 'Mixed Test List',
                'items': {
                    'item_1': {
                        'id': 'item_1',
                        'content': 'Mixed test item',
                        'created_at': '2023-01-01T00:00:00Z',
                        'updated_at': '2023-01-01T00:00:00Z'
                    }
                },
                'created_at': '2023-01-01T00:00:00Z',
                'updated_at': '2023-01-01T00:00:00Z',
                'item_history': {}
            }
        }
        DB["notes"].update(test_note)
        DB["lists"].update(test_list)
        
        # Mock search engine to return mixed result types
        mock_engine = MagicMock()
        mock_engine_manager = MagicMock()
        mock_engine_manager.get_engine.return_value = mock_engine
        mock_search_engine_manager.get_engine_manager.return_value = mock_engine_manager
        
        # Create mixed search results
        mock_result1 = MagicMock()  # Metadata result
        mock_result1.metadata = {
            'content_type': 'note',
            'note_id': 'mixed_note'
        }
        
        class MockResult2:  # original_json_obj result
            def __init__(self):
                self.original_json_obj = {
                    'id': 'mixed_list',
                    'items': {'item_1': {'id': 'item_1', 'content': 'Mixed test item'}}
                }
        
        mock_result2 = MockResult2()
        
        mock_result3 = {  # Direct dictionary result
            'id': 'mixed_note',
            'content': 'This note should be found via mixed search',
            'title': 'Mixed Test Note'
        }
        
        mock_engine.search.return_value = [mock_result1, mock_result2, mock_result3]
        
        found_notes, found_lists = utils.find_items_by_search("mixed")
        
        # Should find both note and list via different result types
        self.assertIsInstance(found_notes, set)
        self.assertIsInstance(found_lists, set)
        # Note: The same note might be found multiple times via different paths
        # This tests that all result processing paths work correctly
        self.assertIn("mixed_note", found_notes)
        self.assertIn("mixed_list", found_lists)


class TestEdgeCases(BaseTestCaseWithErrorHandler):
    """
    Test suite for edge cases and error conditions
    """
    
    def setUp(self):
        """Prepare isolated DB state for each test"""
        # Create a pristine copy of the DB for testing
        self.original_db_state = {
            'notes': copy.deepcopy(DB["notes"]),
            'lists': copy.deepcopy(DB["lists"]),
            'title_index': copy.deepcopy(DB["title_index"]),
            'content_index': copy.deepcopy(DB["content_index"]),
            'operation_log': copy.deepcopy(DB["operation_log"])
        }
        
        # Clear DB for clean test state
        DB["notes"].clear()
        DB["lists"].clear()
        DB["title_index"].clear()
        DB["content_index"].clear()
        DB["operation_log"].clear()
        
    def tearDown(self):
        """Restore original DB state after each test"""
        DB["notes"].clear()
        DB["lists"].clear()
        DB["title_index"].clear()
        DB["content_index"].clear()
        DB["operation_log"].clear()
        
        DB["notes"].update(self.original_db_state['notes'])
        DB["lists"].update(self.original_db_state['lists'])
        DB["title_index"].update(self.original_db_state['title_index'])
        DB["content_index"].update(self.original_db_state['content_index'])
        DB["operation_log"].update(self.original_db_state['operation_log'])
        
    def test_maintain_note_history_nonexistent_note(self):
        """Test maintaining history for non-existent note does nothing"""
        utils.maintain_note_history("non_existent_note", "old_content")
        
        # Should not raise error, just do nothing
        self.assertEqual(len(DB["notes"]), 0)
        
    def test_maintain_list_item_history_nonexistent_list(self):
        """Test maintaining history for non-existent list does nothing"""
        utils.maintain_list_item_history("non_existent_list", "item_id", "old_content")
        
        # Should not raise error, just do nothing
        self.assertEqual(len(DB["lists"]), 0)
        
    def test_maintain_list_item_history_nonexistent_item(self):
        """Test maintaining history for non-existent item does nothing"""
        list_id = "list_123"
        DB["lists"][list_id] = {
            "id": list_id,
            "items": {},
            "item_history": {}
        }
        
        utils.maintain_list_item_history(list_id, "non_existent_item", "old_content")
        
        # Should not raise error, just do nothing
        self.assertEqual(len(DB["lists"][list_id]["item_history"]), 0)
        
    def test_update_content_index_empty_content(self):
        """Test updating content index with empty content"""
        utils.update_content_index("item_123", "")
        
        # Should not add anything to content index
        self.assertEqual(len(DB["content_index"]), 0)
        
    def test_update_content_index_punctuation_only(self):
        """Test updating content index with only punctuation"""
        utils.update_content_index("item_123", "!@#$%^&*()")
        
        # Should not add anything to content index
        self.assertEqual(len(DB["content_index"]), 0)
        
    def test_search_notes_and_lists_empty_query(self):
        """Test searching with empty query"""
        results = utils.search_notes_and_lists("")
        
        # Should return empty results
        self.assertIn("notes", results)
        self.assertIn("lists", results)
        self.assertEqual(len(results["notes"]), 0)
        self.assertEqual(len(results["lists"]), 0)
        
    def test_create_note_empty_content(self):
        """Test creating note with empty content"""
        note = utils.create_note("Title", "")
        
        self.assertEqual(note["title"], "Title")
        self.assertEqual(note["content"], "")
        self.assertIn(note["id"], DB["notes"])
        
    def test_create_note_no_title_empty_content(self):
        """Test creating note with no title and empty content"""
        note = utils.create_note(None, "")
        
        self.assertIsNone(note["title"])
        self.assertEqual(note["content"], "")
        self.assertIn(note["id"], DB["notes"])
        
    def test_add_to_list_empty_items(self):
        """Test adding empty items list to existing list"""
        list_id = "list_123"
        DB["lists"][list_id] = {
            "id": list_id,
            "items": {},
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
        
        result = utils.add_to_list(list_id, [])
        
        self.assertEqual(result["id"], list_id)
        self.assertEqual(len(result["items"]), 0)
        
    def test_log_operation_nonexistent_target(self):
        """Test logging operation for non-existent target"""
        op_id = utils.log_operation("CREATE", "non_existent_target", {})
        
        # Should still create operation log entry, but without snapshot
        self.assertIn(op_id, DB["operation_log"])
        logged_op = DB["operation_log"][op_id]
        self.assertEqual(logged_op["target_id"], "non_existent_target")
        self.assertIsNone(logged_op.get("snapshot"))


if __name__ == '__main__':
    unittest.main() 