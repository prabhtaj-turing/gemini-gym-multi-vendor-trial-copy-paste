import json
import sys
import unittest
from pathlib import Path

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

from claude_code import task  # noqa: E402
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
    "tool_metrics": {}
}


class TestTask(BaseTestCaseWithErrorHandler):
    """Test cases for the task delegation function."""

    def setUp(self):
        """Set up test database before each test."""
        DB.clear()
        if DB_JSON_PATH.exists():
            with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
                DB.update(json.load(fh))
        else:
            DB.update(FALLBACK_DB_STRUCTURE)

    def test_task_success(self):
        """Test successful task execution."""
        result = task.task(
            description="Test task",
            prompt="Perform a simple test operation",
            subagent_type="general"
        )
        
        self.assertIn("result", result)
        self.assertIn("Test task", result["result"])
        self.assertIn("general", result["result"])
        self.assertIn("Perform a simple test operation", result["result"])
        self.assertTrue(result["result"].startswith("Task 'Test task' with sub-agent 'general' has been completed."))

    def test_task_with_different_agent_types(self):
        """Test task with different subagent types."""
        agent_types = ["general", "coding", "research", "analysis", "creative"]
        
        for agent_type in agent_types:
            result = task.task(
                description=f"Task for {agent_type}",
                prompt=f"Execute {agent_type} specific operations",
                subagent_type=agent_type
            )
            
            self.assertIn("result", result)
            self.assertIn(agent_type, result["result"])
            self.assertIn(f"Task for {agent_type}", result["result"])

    def test_task_with_complex_prompt(self):
        """Test task with complex, multi-line prompt."""
        complex_prompt = """
        This is a complex task that involves:
        1. Analyzing data
        2. Processing information
        3. Generating reports
        4. Validating results
        
        Please ensure all steps are completed thoroughly.
        """
        
        result = task.task(
            description="Complex multi-step analysis",
            prompt=complex_prompt,
            subagent_type="analysis"
        )
        
        self.assertIn("result", result)
        self.assertIn("Complex multi-step analysis", result["result"])
        self.assertIn("analysis", result["result"])
        self.assertIn(complex_prompt, result["result"])

    def test_task_invalid_description_type(self):
        """Test error handling for invalid description type."""
        self.assert_error_behavior(
            func_to_call=task.task,
            expected_exception_type=TypeError,
            expected_message="All arguments must be strings",
            description=123,
            prompt="Valid prompt",
            subagent_type="general"
        )

    def test_task_invalid_prompt_type(self):
        """Test error handling for invalid prompt type."""
        self.assert_error_behavior(
            func_to_call=task.task,
            expected_exception_type=TypeError,
            expected_message="All arguments must be strings",
            description="Valid description",
            prompt=123,
            subagent_type="general"
        )

    def test_task_invalid_subagent_type(self):
        """Test error handling for invalid subagent_type."""
        self.assert_error_behavior(
            func_to_call=task.task,
            expected_exception_type=TypeError,
            expected_message="All arguments must be strings",
            description="Valid description",
            prompt="Valid prompt",
            subagent_type=123
        )

    def test_task_multiple_invalid_arguments(self):
        """Test error handling when multiple arguments are invalid."""
        self.assert_error_behavior(
            func_to_call=task.task,
            expected_exception_type=TypeError,
            expected_message="All arguments must be strings",
            description=123,
            prompt=456,
            subagent_type=789
        )

    def test_task_empty_strings(self):
        """Test task with empty string arguments."""
        result = task.task(
            description="",
            prompt="",
            subagent_type=""
        )
        
        self.assertIn("result", result)
        self.assertIn("Task '' with sub-agent '' has been completed.", result["result"])

    def test_task_whitespace_strings(self):
        """Test task with whitespace-only strings."""
        result = task.task(
            description="   ",
            prompt="   ",
            subagent_type="   "
        )
        
        self.assertIn("result", result)
        self.assertIn("Task '   ' with sub-agent '   ' has been completed.", result["result"])

    def test_task_special_characters(self):
        """Test task with special characters in arguments."""
        special_chars_desc = "Task with special chars: !@#$%^&*()"
        special_chars_prompt = "Execute task with symbols: <>?{}[]|\\`~"
        special_chars_agent = "agent-type_v2.0"
        
        result = task.task(
            description=special_chars_desc,
            prompt=special_chars_prompt,
            subagent_type=special_chars_agent
        )
        
        self.assertIn("result", result)
        self.assertIn(special_chars_desc, result["result"])
        self.assertIn(special_chars_prompt, result["result"])
        self.assertIn(special_chars_agent, result["result"])

    def test_task_unicode_characters(self):
        """Test task with unicode characters."""
        unicode_desc = "Tâche avec caractères unicodé 世界"
        unicode_prompt = "Exécuter tâche avec émojis 🚀 🌟 ✨"
        unicode_agent = "агент_типа"
        
        result = task.task(
            description=unicode_desc,
            prompt=unicode_prompt,
            subagent_type=unicode_agent
        )
        
        self.assertIn("result", result)
        self.assertIn(unicode_desc, result["result"])
        self.assertIn(unicode_prompt, result["result"])
        self.assertIn(unicode_agent, result["result"])

    def test_task_very_long_strings(self):
        """Test task with very long string arguments."""
        long_description = "x" * 1000
        long_prompt = "y" * 2000
        long_agent_type = "z" * 100
        
        result = task.task(
            description=long_description,
            prompt=long_prompt,
            subagent_type=long_agent_type
        )
        
        self.assertIn("result", result)
        self.assertIn(long_description, result["result"])
        self.assertIn(long_prompt, result["result"])
        self.assertIn(long_agent_type, result["result"])


if __name__ == "__main__":
    unittest.main()