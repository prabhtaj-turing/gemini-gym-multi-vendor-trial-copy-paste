import unittest
import copy

# Import following the same pattern as test_list_dir.py
from .. import add_to_memory
from .. import DB
from ..SimulationEngine.custom_errors import InvalidInputError

class TestAddToMemory(unittest.TestCase):
    """Test suite for the add_to_memory function."""

    def setUp(self):
        """Set up a fresh copy of the DB for each test."""
        self.original_db = copy.deepcopy(DB)
        
        # Add some existing knowledge entries for update tests
        DB["knowledge_base"] = {
            "k_001": {
                "title": "Original NVM Guidance",
                "knowledge_to_store": "Use nvm to switch node versions."
            },
            "k_002": {
                "title": "Git Best Practices", 
                "knowledge_to_store": "Always commit with descriptive messages."
            }
        }
        DB["_next_knowledge_id"] = 3  # Next ID will be k_003

    def tearDown(self):
        """Restore the original DB state after each test."""
        DB.clear()
        DB.update(self.original_db)

    def test_add_new_knowledge_success(self):
        """Test successfully adding a new piece of knowledge."""
        title = "New Fact"
        knowledge = "This is a new piece of information for the agent."
        
        # Get the next expected ID before the call (should be k_003 due to setUp)
        next_id = DB.get("_next_knowledge_id", 1)
        expected_id = f"k_{next_id:03d}"

        result = add_to_memory(knowledge_to_store=knowledge, title=title)
        
        self.assertIn("message", result)
        self.assertIn(expected_id, result["message"])
        self.assertIn(expected_id, DB["knowledge_base"])
        self.assertEqual(DB["knowledge_base"][expected_id]["title"], title)
        self.assertEqual(DB["knowledge_base"][expected_id]["knowledge_to_store"], knowledge)
        self.assertEqual(DB["_next_knowledge_id"], next_id + 1)

    def test_update_existing_knowledge_success(self):
        """Test successfully updating an existing piece of knowledge."""
        existing_id = "k_001"
        new_title = "Updated NVM Guidance"
        new_knowledge = "Always run 'nvm use' before any 'npm' or 'node' command to ensure version consistency."
        
        result = add_to_memory(
            knowledge_to_store=new_knowledge,
            title=new_title,
            existing_knowledge_id=existing_id
        )

        self.assertIn("message", result)
        self.assertIn(existing_id, result["message"])
        self.assertEqual(DB["knowledge_base"][existing_id]["title"], new_title)
        self.assertEqual(DB["knowledge_base"][existing_id]["knowledge_to_store"], new_knowledge)

    def test_update_nonexistent_knowledge_fail(self):
        """Test failure when trying to update a non-existent knowledge ID."""
        non_existent_id = "k_999"
        with self.assertRaises(ValueError) as cm:
            add_to_memory(
                knowledge_to_store="some data",
                title="some title",
                existing_knowledge_id=non_existent_id
            )
        self.assertIn("not found", str(cm.exception).lower())

    def test_add_with_empty_knowledge_fail(self):
        """Test failure when knowledge_to_store is empty."""
        with self.assertRaises(ValueError) as cm:
            add_to_memory(knowledge_to_store="", title="some title")
        self.assertEqual(str(cm.exception), "knowledge_to_store cannot be empty.")

    def test_add_with_empty_title_fail(self):
        """Test failure when title is empty (MCP compliance)."""
        knowledge = "A fact without a title."
        
        with self.assertRaises(ValueError) as cm:
            add_to_memory(knowledge_to_store=knowledge, title="")
        self.assertEqual(str(cm.exception), "title cannot be empty.")

    def test_add_with_long_knowledge_fail(self):
        """Test failure when knowledge_to_store exceeds paragraph length."""
        long_knowledge = "A" * 501  # Exceeds 500 character limit
        
        with self.assertRaises(ValueError) as cm:
            add_to_memory(knowledge_to_store=long_knowledge, title="Long Knowledge")
        self.assertIn("paragraph in length", str(cm.exception))
        self.assertIn("max 500 characters", str(cm.exception))

    def test_add_with_max_length_knowledge_success(self):
        """Test success when knowledge_to_store is exactly at the character limit."""
        max_length_knowledge = "A" * 500  # Exactly 500 characters
        
        # Get the next expected ID before the call (should be k_003 due to setUp)
        next_id = DB.get("_next_knowledge_id", 1)
        expected_id = f"k_{next_id:03d}"
        
        result = add_to_memory(knowledge_to_store=max_length_knowledge, title="Max Length Knowledge")
        
        self.assertIn("message", result)
        self.assertIn(expected_id, result["message"])
        self.assertEqual(DB["knowledge_base"][expected_id]["knowledge_to_store"], max_length_knowledge)

    def test_add_with_non_string_knowledge_fail(self):
        """Test failure when knowledge_to_store is not a string."""
        with self.assertRaises(InvalidInputError) as cm:
            add_to_memory(knowledge_to_store=123, title="some title")
        self.assertEqual(str(cm.exception), "knowledge_to_store must be a string")

    def test_add_with_non_string_title_fail(self):
        """Test failure when title is not a string."""
        with self.assertRaises(InvalidInputError) as cm:
            add_to_memory(knowledge_to_store="some knowledge", title=456)
        self.assertEqual(str(cm.exception), "title must be a string")

    def test_add_with_non_string_existing_id_fail(self):
        """Test failure when existing_knowledge_id is not a string."""
        with self.assertRaises(InvalidInputError) as cm:
            add_to_memory(
                knowledge_to_store="some knowledge",
                title="some title",
                existing_knowledge_id=789
            )
        self.assertEqual(str(cm.exception), "existing_knowledge_id must be a string")

    def test_update_with_nonexistent_id_fail(self):
        """Test failure when existing_knowledge_id doesn't exist in database."""
        nonexistent_id = "k_999"  # Valid format but doesn't exist
        with self.assertRaises(ValueError) as cm:
            add_to_memory(
                knowledge_to_store="some knowledge",
                title="some title",
                existing_knowledge_id=nonexistent_id
            )
        self.assertIn("not found", str(cm.exception).lower())

if __name__ == '__main__':
    unittest.main() 