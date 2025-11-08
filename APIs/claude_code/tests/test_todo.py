import json
import sys
import unittest
from pathlib import Path

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

from claude_code import todo  # noqa: E402
from claude_code.SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler  # noqa: E402

DB_JSON_PATH = Path(__file__).resolve().parents[3] / "DBs" / "ClaudeCodeDefaultDB.json"

# Fallback DB structure used when the default DB file doesn't exist
FALLBACK_DB_STRUCTURE = {
    "workspace_root": "/home/user/project",
    "cwd": "/home/user/project",
    "file_system": {},
    "memory_storage": {},
    "last_edit_params": None,
    "background_processes": {},
    "tool_metrics": {},
    "todos": []
}


class TestTodo(BaseTestCaseWithErrorHandler):
    """Test cases for the todo management function."""

    def setUp(self):
        """Set up test database before each test."""
        DB.clear()
        if DB_JSON_PATH.exists():
            with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
                DB.update(json.load(fh))
        else:
            DB.update(FALLBACK_DB_STRUCTURE)

    def test_todo_write_replace_mode(self):
        """Test replacing entire todo list."""
        test_todos = [
            {"id": "task1", "content": "First task", "status": "pending"},
            {"id": "task2", "content": "Second task", "status": "completed"}
        ]
        
        result = todo.todo_write(merge=False, todos=test_todos)
        
        self.assertEqual(result["status"], "Todos updated successfully.")
        self.assertEqual(len(result["todos"]), 2)
        self.assertEqual(result["todos"][0]["id"], "task1")
        self.assertEqual(result["todos"][1]["id"], "task2")
        self.assertEqual(DB["todos"], test_todos)

    def test_todo_write_merge_mode_empty_db(self):
        """Test merging todos when database is empty."""
        test_todos = [
            {"id": "task1", "content": "First task", "status": "pending"}
        ]
        
        result = todo.todo_write(merge=True, todos=test_todos)
        
        self.assertEqual(result["status"], "Todos updated successfully.")
        self.assertEqual(len(result["todos"]), 1)
        self.assertEqual(result["todos"][0]["id"], "task1")
        self.assertEqual(DB["todos"], test_todos)

    def test_todo_write_merge_mode_existing_data(self):
        """Test merging todos with existing data."""
        # Set up existing todos
        DB["todos"] = [
            {"id": "task1", "content": "Original task", "status": "pending"},
            {"id": "task2", "content": "Second task", "status": "completed"}
        ]
        
        # Merge with new/updated todos
        new_todos = [
            {"id": "task1", "content": "Updated task", "status": "completed"},
            {"id": "task3", "content": "Third task", "status": "pending"}
        ]
        
        result = todo.todo_write(merge=True, todos=new_todos)
        
        self.assertEqual(result["status"], "Todos updated successfully.")
        self.assertEqual(len(result["todos"]), 3)
        
        # Check that task1 was updated
        task1 = next(t for t in result["todos"] if t["id"] == "task1")
        self.assertEqual(task1["content"], "Updated task")
        self.assertEqual(task1["status"], "completed")
        
        # Check that task2 remains unchanged
        task2 = next(t for t in result["todos"] if t["id"] == "task2")
        self.assertEqual(task2["content"], "Second task")
        
        # Check that task3 was added
        task3 = next(t for t in result["todos"] if t["id"] == "task3")
        self.assertEqual(task3["content"], "Third task")

    def test_todo_write_invalid_merge_type(self):
        """Test error handling for invalid merge parameter type."""
        self.assert_error_behavior(
            func_to_call=todo.todo_write,
            expected_exception_type=TypeError,
            expected_message="merge must be a boolean",
            merge="invalid",
            todos=[]
        )

    def test_todo_write_invalid_todos_type(self):
        """Test error handling for invalid todos parameter type."""
        self.assert_error_behavior(
            func_to_call=todo.todo_write,
            expected_exception_type=TypeError,
            expected_message="todos must be a list of dictionaries",
            merge=False,
            todos="invalid"
        )

    def test_todo_write_merge_missing_id(self):
        """Test error handling when merging todos without id."""
        test_todos = [
            {"content": "Task without id", "status": "pending"}
        ]
        
        self.assert_error_behavior(
            func_to_call=todo.todo_write,
            expected_exception_type=ValueError,
            expected_message="Each todo item must have an 'id'",
            merge=True,
            todos=test_todos
        )

    def test_todo_write_empty_list(self):
        """Test handling of empty todo list."""
        result = todo.todo_write(merge=False, todos=[])
        
        self.assertEqual(result["status"], "Todos updated successfully.")
        self.assertEqual(result["todos"], [])
        self.assertEqual(DB["todos"], [])

    def test_todo_write_complex_todo_structure(self):
        """Test with complex todo structures containing multiple fields."""
        complex_todos = [
            {
                "id": "complex1",
                "content": "Complex task with metadata",
                "status": "in_progress",
                "priority": "high",
                "due_date": "2024-12-31",
                "tags": ["important", "urgent"],
                "assignee": "user1"
            }
        ]
        
        result = todo.todo_write(merge=False, todos=complex_todos)
        
        self.assertEqual(result["status"], "Todos updated successfully.")
        self.assertEqual(len(result["todos"]), 1)
        self.assertEqual(result["todos"][0]["priority"], "high")
        self.assertEqual(result["todos"][0]["tags"], ["important", "urgent"])


if __name__ == "__main__":
    unittest.main()