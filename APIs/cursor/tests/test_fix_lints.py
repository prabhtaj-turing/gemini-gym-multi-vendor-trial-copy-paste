# cursor/tests/test_fix_lints.py
import unittest
import copy
import os
import re
import tempfile
import shutil
from unittest.mock import patch

# Import functions to be tested and related components
from ..cursorAPI import fix_lints, edit_file
from ..SimulationEngine import utils
from ..SimulationEngine.db import DB as GlobalDBSource
from ..SimulationEngine.custom_errors import (
    LastEditNotFoundError,
    FileNotInWorkspaceError,
    LintFixingError,
    InvalidInputError,
    FailedToApplyLintFixesError,
)
from common_utils.base_case import BaseTestCaseWithErrorHandler

# To check if API key is available for skipping live tests
from ..SimulationEngine.llm_interface import GEMINI_API_KEY_FROM_ENV

GEMINI_API_KEY_IS_AVAILABLE = bool(GEMINI_API_KEY_FROM_ENV)

def normalize_for_db(path_string):
    if path_string is None:
        return None
    # Remove any drive letter prefix first
    if len(path_string) > 2 and path_string[1:3] in [':/', ':\\']:
        path_string = path_string[2:]
    # Then normalize and convert slashes
    return os.path.normpath(path_string).replace("\\\\", "/")

def minimal_reset_db_for_fix_lints(workspace_path_for_db=None):
    """Creates a fresh minimal DB state for testing, clearing and setting up root."""
    if workspace_path_for_db is None:
        workspace_path_for_db = tempfile.mkdtemp(prefix="test_fix_lints_workspace_")
    
    # Normalize workspace path
    workspace_path_for_db = normalize_for_db(workspace_path_for_db)
    
    # Initialize common directory to match workspace path
    utils.update_common_directory(workspace_path_for_db)
    
    db_state = {
        "workspace_root": workspace_path_for_db,
        "cwd": workspace_path_for_db,
        "file_system": {},
        "last_edit_params": None,
        "background_processes": {},
        "_next_pid": 1
    }

    # Create root directory entry
    db_state["file_system"][workspace_path_for_db] = {
        "path": workspace_path_for_db,
        "is_directory": True,
        "content_lines": [],
        "size_bytes": 0,
        "last_modified": utils.get_current_timestamp_iso()
    }
    
    return workspace_path_for_db, db_state

class TestFixLints(BaseTestCaseWithErrorHandler):
    """
    Test cases for the fix_lints function, using mocked LLM responses
    to verify the core logic and error handling.
    """

    def setUp(self):
        """Prepares an isolated database state for each test method."""
        # Create temporary workspace and DB state
        self.workspace_path, self.db_for_test = minimal_reset_db_for_fix_lints()

        # Patch 'DB' in all relevant modules
        self.db_patcher_cursor = patch("cursor.DB", self.db_for_test)
        self.db_patcher_utils = patch("cursor.SimulationEngine.utils.DB", self.db_for_test)
        self.db_patcher_cursorapi = patch("cursor.cursorAPI.DB", self.db_for_test)

        self.db_patcher_cursor.start()
        self.db_patcher_utils.start()
        self.db_patcher_cursorapi.start()

        # CRITICAL: Patch 'DB' in the db module where validate_workspace_hydration is defined
        self.db_patcher_for_db_module = patch("cursor.SimulationEngine.db.DB", self.db_for_test)
        self.db_patcher_for_db_module.start()

    def tearDown(self):
        """Restores original state and cleans up after each test."""
        self.db_patcher_cursorapi.stop()
        self.db_patcher_utils.stop()
        self.db_patcher_cursor.stop()
        
        # Clean up temporary workspace
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def _add_file_to_mock_db(self, path: str, content_lines_raw: list[str]):
        """Adds a file to the test DB."""
        abs_path = path
        if not os.path.isabs(path):
            abs_path = os.path.normpath(os.path.join(self.workspace_path, path))

        dir_name = os.path.dirname(abs_path)
        if dir_name and dir_name != self.workspace_path and dir_name not in self.db_for_test["file_system"]:
            self._add_dir_to_mock_db(dir_name)

        content_lines = utils._normalize_lines(content_lines_raw)
        
        # Create the file on filesystem
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.writelines(content_lines)
        
        self.db_for_test["file_system"][abs_path] = {
            "path": abs_path,
            "is_directory": False,
            "content_lines": content_lines,
            "size_bytes": utils.calculate_size_bytes(content_lines),
            "last_modified": utils.get_current_timestamp_iso(),
        }
        return abs_path

    def _add_dir_to_mock_db(self, path: str):
        """Adds a directory to the test DB."""
        abs_path = path
        if not os.path.isabs(path):
            abs_path = os.path.normpath(os.path.join(self.workspace_path, path))

        if abs_path not in self.db_for_test["file_system"]:
            # Create the directory on filesystem
            os.makedirs(abs_path, exist_ok=True)
            
            self.db_for_test["file_system"][abs_path] = {
                "path": abs_path,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": utils.get_current_timestamp_iso(),
            }
        parent_dir = os.path.dirname(abs_path)
        if parent_dir and parent_dir != abs_path and parent_dir != self.workspace_path and parent_dir not in self.db_for_test["file_system"]:
            self._add_dir_to_mock_db(parent_dir)
        return abs_path

    def _get_file_entry(self, path_rel_to_ws_root: str):
        """Retrieves a file entry from the test DB."""
        abs_path = os.path.normpath(os.path.join(self.workspace_path, path_rel_to_ws_root))
        return self.db_for_test.get("file_system", {}).get(abs_path)

    @patch("cursor.SimulationEngine.utils.propose_code_edits")
    @unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not set, skipping LLM integration tests for edit_file.")
    def test_fix_lints_success(self, mock_propose_edits):
        """Verify fix_lints successfully applies a proposed fix."""
        target_rel = "bad_code.py"
        original_content = ["def my_func():", "  print('hello')"] # Indentation error
        abs_target_path = self._add_file_to_mock_db(target_rel, original_content)

        # Simulate a previous edit that resulted in this state
        self.db_for_test["last_edit_params"] = {
            "target_file": abs_target_path,
            "code_edit": "...",
            "instructions": "Initial creation",
        }

        # Mock the LLM's proposed fix
        fixed_code_edit = "// ... existing code ...\ndef my_func():\n    print('hello')\n"
        mock_propose_edits.return_value = {
            "code_edit": fixed_code_edit,
            "instructions": "Fix indentation.",
        }

        result = fix_lints(run=True)
        self.assertIsInstance(result, dict)
        self.assertIn("successfully", result.get("message", ""))
        self.assertEqual(result.get("file_path"), abs_target_path)

        updated_entry = self._get_file_entry(target_rel)
        expected_lines = ["def my_func():\n", "    print('hello')\n"]
        self.assertEqual(updated_entry.get("content_lines"), expected_lines)
        mock_propose_edits.assert_called_once()

    @patch("cursor.SimulationEngine.utils.propose_code_edits")
    def test_fix_lints_no_changes_needed(self, mock_propose_edits):
        """Verify fix_lints does nothing if no changes are proposed."""
        target_rel = "good_code.py"
        original_content = ["def my_func():", "    print('hello')"]
        abs_target_path = self._add_file_to_mock_db(target_rel, original_content)

        self.db_for_test["last_edit_params"] = {
            "target_file": abs_target_path,
            "code_edit": "...",
            "instructions": "Initial creation",
        }

        # Mock the LLM proposing no changes
        mock_propose_edits.return_value = {"code_edit": "", "instructions": ""}

        result = fix_lints(run=True)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("message"), "Lint fixing model proposed no changes.")
        self.assertEqual(result.get("file_path"), abs_target_path)

        # Content should be unchanged
        entry = self._get_file_entry(target_rel)
        self.assertEqual(entry.get("content_lines"), ["def my_func():\n", "    print('hello')\n"])

    def test_fix_lints_raises_last_edit_not_found(self):
        """Verify fix_lints raises LastEditNotFoundError if no edit params exist."""
        self.db_for_test["last_edit_params"] = None
        with self.assertRaises(LastEditNotFoundError):
            fix_lints(run=True)

    def test_fix_lints_raises_invalid_input_on_incomplete_params(self):
        """Verify fix_lints raises InvalidInputError for incomplete params."""
        self.db_for_test["last_edit_params"] = {"target_file": "/path/to/file"}
        with self.assertRaises(InvalidInputError):
            fix_lints(run=True)

    def test_fix_lints_raises_file_not_in_workspace(self):
        """Verify fix_lints raises FileNotInWorkspaceError if the file is gone."""
        self.db_for_test["last_edit_params"] = {
            "target_file": os.path.join(self.workspace_path, "non_existent_file.py"),
            "code_edit": "...",
            "instructions": "...",
        }
        with self.assertRaises(FileNotInWorkspaceError):
            fix_lints(run=True)

    @patch("cursor.SimulationEngine.utils.propose_code_edits")
    def test_fix_lints_raises_lint_fixing_error_on_proposal_failure(self, mock_propose_edits):
        """Verify fix_lints raises LintFixingError if proposal generation fails."""
        target_rel = "a_file.py"
        self._add_file_to_mock_db(target_rel, ["content"])
        self.db_for_test["last_edit_params"] = {
            "target_file": os.path.join(self.workspace_path, target_rel),
            "code_edit": "...",
            "instructions": "...",
        }
        mock_propose_edits.side_effect = RuntimeError("LLM API is down")

        with self.assertRaises(LintFixingError):
            fix_lints(run=True)

    @patch("cursor.cursorAPI.edit_file")
    @patch("cursor.SimulationEngine.utils.propose_code_edits")
    def test_fix_lints_raises_failed_to_apply_on_edit_failure(
        self, mock_propose_edits, mock_edit_file
    ):
        """Verify fix_lints raises FailedToApplyLintFixesError if edit_file raises an error."""
        target_rel = "a_file.py"
        abs_target_path = self._add_file_to_mock_db(target_rel, ["content"])
        self.db_for_test["last_edit_params"] = {
            "target_file": abs_target_path,
            "code_edit": "...",
            "instructions": "...",
        }
        mock_propose_edits.return_value = {
            "code_edit": "some fix",
            "instructions": "a fix instruction",
        }
        mock_edit_file.side_effect = ValueError("edit file failed")

        with self.assertRaises(FailedToApplyLintFixesError) as cm:
            fix_lints(run=True)
        
        self.assertIn("edit file failed", str(cm.exception))

        mock_edit_file.assert_called_once_with(
            target_file=abs_target_path,
            code_edit="some fix",
            instructions="a fix instruction",
        )


@unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not set, skipping LLM integration tests.")
class TestFixLintsWithLiveLLM(BaseTestCaseWithErrorHandler):
    """
    Integration tests for fix_lints using live LLM calls.
    """
    def setUp(self):
        """Prepares an isolated database state for each live test."""
        # Create temporary workspace and DB state
        self.workspace_path, self.db_for_test = minimal_reset_db_for_fix_lints()

        # Patch 'DB' in all relevant modules
        self.db_patcher_cursor = patch("cursor.DB", self.db_for_test)
        self.db_patcher_utils = patch("cursor.SimulationEngine.utils.DB", self.db_for_test)
        self.db_patcher_cursorapi = patch("cursor.cursorAPI.DB", self.db_for_test)

        self.db_patcher_cursor.start()
        self.db_patcher_utils.start()
        self.db_patcher_cursorapi.start()

        # CRITICAL: Patch 'DB' in the db module where validate_workspace_hydration is defined
        self.db_patcher_for_db_module = patch("cursor.SimulationEngine.db.DB", self.db_for_test)
        self.db_patcher_for_db_module.start()

    def tearDown(self):
        """Restores original state and cleans up after each test."""
        self.db_patcher_for_db_module.stop()
        self.db_patcher_cursorapi.stop()
        self.db_patcher_utils.stop()
        self.db_patcher_cursor.stop()
        
        # Clean up temporary workspace
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def _add_file_to_mock_db(self, path: str, content_lines_raw: list[str]):
        """Adds a file to the test DB."""
        abs_path = path
        if not os.path.isabs(path):
            abs_path = os.path.normpath(os.path.join(self.workspace_path, path))

        dir_name = os.path.dirname(abs_path)
        if dir_name and dir_name != self.workspace_path and dir_name not in self.db_for_test["file_system"]:
            self._add_dir_to_mock_db(dir_name)

        content_lines = utils._normalize_lines(content_lines_raw)
        
        # Create the file on filesystem
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.writelines(content_lines)
        
        self.db_for_test["file_system"][abs_path] = {
            "path": abs_path,
            "is_directory": False,
            "content_lines": content_lines,
            "size_bytes": utils.calculate_size_bytes(content_lines),
            "last_modified": utils.get_current_timestamp_iso(),
        }
        return abs_path

    def _add_dir_to_mock_db(self, path: str):
        """Adds a directory to the test DB."""
        abs_path = path
        if not os.path.isabs(path):
            abs_path = os.path.normpath(os.path.join(self.workspace_path, path))

        if abs_path not in self.db_for_test["file_system"]:
            # Create the directory on filesystem
            os.makedirs(abs_path, exist_ok=True)
            
            self.db_for_test["file_system"][abs_path] = {
                "path": abs_path,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": utils.get_current_timestamp_iso(),
            }
        parent_dir = os.path.dirname(abs_path)
        if parent_dir and parent_dir != abs_path and parent_dir != self.workspace_path and parent_dir not in self.db_for_test["file_system"]:
            self._add_dir_to_mock_db(parent_dir)
        return abs_path

    def _get_file_content_lines(self, path_rel_to_ws_root: str):
        abs_path = os.path.normpath(os.path.join(self.workspace_path, path_rel_to_ws_root))
        entry = self.db_for_test.get("file_system", {}).get(abs_path)
        return entry.get("content_lines", []) if entry and not entry.get("is_directory") else None

    def test_live_fix_lints_adds_missing_import(self):
        """Integration test: Use fix_lints to add a missing import after a bad edit."""
        target_file_rel = "importer.py"
        # Initial file state is empty
        self._add_file_to_mock_db(target_file_rel, [])

        # Step 1: Perform an edit that introduces a linting error (using a module without importing it)
        bad_edit_instructions = "Create a function that uses os.path.join"
        bad_code_edit = "def join_paths(a, b):\n    return os.path.join(a, b)\n"
        edit_result = edit_file(
            target_file=target_file_rel,
            code_edit=bad_code_edit,
            instructions=bad_edit_instructions,
        )
        # Accept both "created successfully" and "updated successfully" in the message
        msg = edit_result.get("message", "")
        self.assertTrue(
            ("created successfully" in msg) or ("updated successfully" in msg),
            f"Expected 'created successfully' or 'updated successfully' in message, got: {msg!r}"
        )

        # Verify the "bad" code is in place
        content_after_edit = self._get_file_content_lines(target_file_rel)
        self.assertNotIn("import os\n", content_after_edit)

        # Step 2: Call fix_lints to repair the code
        print(f"\n[LIVE LINT TEST] Calling fix_lints for: {target_file_rel}")
        fix_result = fix_lints(run=True)
        self.assertIn("successfully", fix_result.get("message", ""))


        # Step 3: Verify the fix
        content_after_fix = self._get_file_content_lines(target_file_rel)
        content_str = "".join(content_after_fix)

        print(f"  Final content after lint fix:\n{content_str}")
        self.assertIn("import os", content_str)
        # The LLM might add type hints or reformat the function signature.
        # This regex checks for 'def join_paths' followed by parentheses containing 'a' and 'b'.
        self.assertTrue(
            re.search(r"def\s+join_paths\s*\(.*a.*,.*b.*\):", content_str),
            f"Could not find function 'join_paths(a, b)' in the fixed code: {content_str}",
        )
        print(f"  File '{target_file_rel}' successfully fixed by adding 'import os'.")


if __name__ == "__main__":
    unittest.main()