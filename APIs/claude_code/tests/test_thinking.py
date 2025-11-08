import json
import sys
from pathlib import Path

import pytest

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

from claude_code import thinking  # noqa: E402
from claude_code.SimulationEngine.custom_errors import InvalidCodeError  # noqa: E402
from claude_code.SimulationEngine.db import DB  # noqa: E402
from common_utils.base_case import BaseTestCaseWithErrorHandler  # noqa: E402

# Import the custom NotImplementedError from the SimulationEngine  
try:
    from claude_code.SimulationEngine.custom_errors import NotImplementedError
except ImportError:
    # Fall back to built-in if custom doesn't exist
    NotImplementedError = NotImplementedError

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


@pytest.fixture(autouse=True)
def reload_db():
    """Load fresh DB snapshot before each test."""
    DB.clear()
    if DB_JSON_PATH.exists():
        with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
            DB.update(json.load(fh))
    else:
        DB.update(FALLBACK_DB_STRUCTURE)


class TestThinking(BaseTestCaseWithErrorHandler):
    """Test cases for the thinking function."""

    def setUp(self):
        """Set up test database before each test."""
        DB.clear()
        if DB_JSON_PATH.exists():
            with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
                DB.update(json.load(fh))
        else:
            DB.update(FALLBACK_DB_STRUCTURE)

    def test_think_not_implemented(self):
        """Test that think raises NotImplementedError."""
        self.assert_error_behavior(
            func_to_call=thinking.think,
            expected_exception_type=NotImplementedError,
            expected_message="This tool is not implemented.",
            thought="This is a test thought"
        )

    def test_think_different_inputs(self):
        """Test that think raises NotImplementedError with various inputs."""
        test_cases = [
            "Simple thought",
            "",
            "思考中... 🤔 Testing unicode", 
            "This is a very long thought. " * 100
        ]
        
        for test_input in test_cases:
            with self.subTest(thought=test_input[:20] + "..."):
                self.assert_error_behavior(
                    func_to_call=thinking.think,
                    expected_exception_type=NotImplementedError,
                    expected_message="This tool is not implemented.",
                    thought=test_input
                )


class TestCodeReview(BaseTestCaseWithErrorHandler):
    """Test cases for the code_review function."""

    def setUp(self):
        """Set up test database before each test."""
        DB.clear()
        if DB_JSON_PATH.exists():
            with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
                DB.update(json.load(fh))
        else:
            DB.update(FALLBACK_DB_STRUCTURE)

    def test_code_review_not_implemented(self):
        """Test that code_review raises NotImplementedError."""
        self.assert_error_behavior(
            func_to_call=thinking.code_review,
            expected_exception_type=NotImplementedError,
            expected_message="This tool is not implemented.",
            code="def hello(): return 'world'"
        )

    def test_code_review_different_inputs(self):
        """Test that code_review raises NotImplementedError with various inputs."""
        test_cases = [
            "def simple_function(): pass",
            "class TestClass: pass",
            "import os\nprint('hello')",
            "SELECT * FROM users;",
            "function test() { return true; }"
        ]
        
        for test_input in test_cases:
            with self.subTest(code=test_input[:30] + "..."):
                self.assert_error_behavior(
                    func_to_call=thinking.code_review,
                    expected_exception_type=NotImplementedError,
                    expected_message="This tool is not implemented.",
                    code=test_input
                )
