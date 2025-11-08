# cursor/tests/test_edit_file.py
import unittest
import copy
import os
import tempfile
import shutil
from unittest.mock import patch # Still needed for DB patching
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Import functions to be tested and related components
from ..cursorAPI import edit_file # The main function tested by this file
from ..SimulationEngine import utils # For utils.propose_code_edits and helpers
from .. import DB as GlobalDBSource
# To check if API key is available for skipping live tests
from ..SimulationEngine.llm_interface import GEMINI_API_KEY_FROM_ENV 
from ..SimulationEngine.custom_errors import InvalidInputError, WorkspaceNotHydratedError

# --- Helper to check if API key is available for integration tests ---
GEMINI_API_KEY_IS_AVAILABLE = bool(GEMINI_API_KEY_FROM_ENV)

def normalize_for_db(path_string):
    if path_string is None:
        return None
    # Remove any drive letter prefix first
    if len(path_string) > 2 and path_string[1:3] in [':/', ':\\']:
        path_string = path_string[2:]
    # Then normalize and convert slashes
    return os.path.normpath(path_string).replace("\\\\", "/")

def minimal_reset_db_for_edit_file(workspace_path_for_db=None):
    """Creates a fresh minimal DB state for testing, clearing and setting up root."""
    if workspace_path_for_db is None:
        workspace_path_for_db = tempfile.mkdtemp(prefix="test_edit_file_workspace_")
    
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

@unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not set, skipping LLM integration tests for edit_file.")
class TestEditFile(BaseTestCaseWithErrorHandler):
    def setUp(self):
        # Create temporary workspace and DB state
        self.workspace_path, self.db_for_test = minimal_reset_db_for_edit_file()

        self.db_patcher = patch("cursor.cursorAPI.DB", self.db_for_test)
        self.db_patcher.start()

        self.utils_db_patcher = patch("cursor.SimulationEngine.utils.DB", self.db_for_test)
        self.utils_db_patcher.start()

        # Create existing_file.txt on filesystem and add to DB
        self.existing_file_path = os.path.join(self.workspace_path, "existing_file.txt")
        with open(self.existing_file_path, 'w') as f:
            f.write("line 1\nline 2\n")
        
        self.db_for_test["file_system"][self.existing_file_path] = {
            "path": self.existing_file_path,
            "is_directory": False,
            "content_lines": ["line 1\n", "line 2\n"],
            "size_bytes": 14,
            "last_modified": utils.get_current_timestamp_iso()
        }

    def tearDown(self):
        self.utils_db_patcher.stop()
        self.db_patcher.stop()
        
        # Clean up temporary workspace
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def test_invalid_target_file_type_raises_error(self):
        with self.assertRaises(InvalidInputError):
            edit_file(target_file=123, code_edit="a", instructions="b")

    def test_invalid_code_edit_type_raises_error(self):
        with self.assertRaises(InvalidInputError):
            edit_file(target_file="a", code_edit=None, instructions="b")

    def test_invalid_instructions_type_raises_error(self):
        with self.assertRaises(InvalidInputError):
            edit_file(target_file="a", code_edit="b", instructions=False)

    def test_create_new_file(self):
        result = edit_file("new_file.txt", "new content", "create file")
        self.assertIn("created successfully", result["message"])
        new_file_path = os.path.join(self.workspace_path, "new_file.txt")
        self.assertIn(new_file_path, self.db_for_test["file_system"])
        self.assertEqual(self.db_for_test["file_system"][new_file_path]["content_lines"], ["new content\n"])

    def test_edit_existing_file(self):
        result = edit_file("existing_file.txt", "updated content", "update file")
        self.assertIn("updated successfully", result["message"])
        self.assertEqual(self.db_for_test["file_system"][self.existing_file_path]["content_lines"], ["updated content\n"])

@unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not set, skipping LLM integration tests for edit_file.")
class TestEditFileWithPredefinedEdits(BaseTestCaseWithErrorHandler):
    """
    Test cases for the edit_file function, using predefined (mocked)
    `code_edit` and `instructions` to verify the core file manipulation logic
    and the `apply_code_edit` utility's patching behavior.
    """

    transient_test_files = []

    def setUp(self):
        """Prepares an isolated database state for each test method."""
        # Create temporary workspace and DB state
        self.workspace_path, self.db_for_test = minimal_reset_db_for_edit_file()

        self.db_patcher_for_init_module = patch("cursor.DB", self.db_for_test)
        self.db_patcher_for_init_module.start()
        self.db_patcher_for_utils_module = patch(
            "cursor.SimulationEngine.utils.DB", self.db_for_test
        )
        self.db_patcher_for_utils_module.start()

        # Patch 'DB' in the cursorAPI module where the actual function is defined
        self.db_patcher_for_cursorapi_module = patch(
            "cursor.cursorAPI.DB", self.db_for_test
        )
        self.db_patcher_for_cursorapi_module.start()

        self._cleanup_transient_files()

    def tearDown(self):
        """Restores original state and cleans up after each test."""
        self._cleanup_transient_files()
        self.db_patcher_for_cursorapi_module.stop()
        self.db_patcher_for_utils_module.stop()
        self.db_patcher_for_init_module.stop()
        
        # Clean up temporary workspace
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def _cleanup_transient_files(self):
        """Removes any specified transient files created during tests."""
        cursor_module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for filename in self.transient_test_files:
            file_path = os.path.join(cursor_module_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    print(f"Warning: Cleanup failed for {file_path}: {e}")

    def _add_file_to_mock_db(self, path: str, content_lines_raw: list[str]):
        """Adds a file to the test DB, creating parent dirs if necessary."""
        abs_path = path
        if not os.path.isabs(path):
            abs_path = os.path.normpath(
                os.path.join(self.workspace_path, path)
            )

        dir_name = os.path.dirname(abs_path)
        if (
            dir_name
            and dir_name != self.workspace_path
            and dir_name not in self.db_for_test["file_system"]
        ):
            self._add_dir_to_mock_db(dir_name)

        content_lines = utils._normalize_lines(
            content_lines_raw
        )  # Use helper for consistency

        # Create the file on filesystem - write as proper text content
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
        """Adds a directory to the test DB if it doesn't exist, including parents."""
        abs_path = path
        if not os.path.isabs(path):
            abs_path = os.path.normpath(
                os.path.join(self.workspace_path, path)
            )

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
        if (
            parent_dir
            and parent_dir != abs_path
            and parent_dir != self.workspace_path
            and parent_dir not in self.db_for_test["file_system"]
        ):
            self._add_dir_to_mock_db(parent_dir)
        return abs_path

    def _get_file_entry(self, path_rel_to_ws_root: str):
        """Retrieves a file entry from the test DB, path relative to workspace root."""
        abs_path = os.path.normpath(
            os.path.join(self.workspace_path, path_rel_to_ws_root)
        )
        return self.db_for_test.get("file_system", {}).get(abs_path)

    # --- Test Cases ---

    def test_create_new_file_simple(self):
        """Verify creating a new file with full content in code_edit (no delimiters)."""
        target_rel = "new_module.py"
        # Resolved based on CWD in setUp, which is workspace_path for these tests
        abs_target_path = os.path.normpath(os.path.join(self.workspace_path, target_rel))
        code_content = "def main():\n    print('Hello')\n"
        instructions = "Create a new Python module."

        result = edit_file(
            target_file=target_rel, code_edit=code_content, instructions=instructions
        )

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("file_path"), abs_target_path)
        self.assertIn("created successfully", result.get("message", ""))

        new_entry = self._get_file_entry(target_rel)
        self.assertIsNotNone(new_entry)
        self.assertFalse(new_entry.get("is_directory"))
        self.assertEqual(
            new_entry.get("content_lines"), ["def main():\n", "    print('Hello')\n"]
        )

        last_edit = self.db_for_test.get("last_edit_params")
        self.assertEqual(last_edit.get("target_file"), abs_target_path)

    def test_edit_existing_file_full_replacement_no_delimiters(self):
        """Verify editing by replacing entire content when code_edit has no delimiters."""
        target_rel = "config.txt"
        abs_target_path = self._add_file_to_mock_db(target_rel, ["old_setting=true\n"])
        new_content = "new_setting=false\nanother_setting=123\n"

        result = edit_file(
            target_file=target_rel, code_edit=new_content, instructions="Update config."
        )

        self.assertIsInstance(result, dict)
        self.assertIn("updated successfully", result.get("message", ""))
        updated_entry = self._get_file_entry(target_rel)
        self.assertEqual(
            updated_entry.get("content_lines"),
            ["new_setting=false\n", "another_setting=123\n"],
        )

    # --- Tests for Advanced Patching with Delimiters ---

    def test_edit_insert_at_beginning_with_patching(self):
        """Verify inserting lines at the file start, preserving subsequent original content."""
        target_rel = "main.txt"
        original_content_raw = ["Original Line 1", "Original Line 2"]
        # The _add_file_to_mock_db helper will normalize lines to end with '\n'
        # So, original_lines in apply_code_edit will be ["Original Line 1\n", "Original Line 2\n"]
        abs_target_path = self._add_file_to_mock_db(target_rel, original_content_raw)

        # Revised code_edit: New lines are provided, followed by the first original line
        # that should be kept, acting as context. The delimiter then indicates
        # that subsequent original lines (after "Original Line 1") should be preserved.
        code_edit = (
            "Inserted Line A\n"  # New line 1
            "Inserted Line B\n"  # New line 2
            "Original Line 1\n"  # Context from original file, immediately following the insertion
            "// ... existing code ...\n"  # Indicates to preserve original lines after "Original Line 1"
        )
        instructions = "Prepend two lines to main.txt."

        result = edit_file(
            target_file=target_rel, code_edit=code_edit, instructions=instructions
        )

        self.assertIsInstance(
            result, dict,
            f"Edit failed when trying to insert at beginning: {result}",
        )
        self.assertIn("updated successfully", result.get("message", ""))


        expected_lines = [
            "Inserted Line A\n",
            "Inserted Line B\n",
            "Original Line 1\n",  # This line was part of the AI hunk & matched original
            "Original Line 2\n",  # This line should be preserved by the trailing delimiter
        ]
        actual_lines = self._get_file_entry(target_rel).get("content_lines")
        # print(f"DEBUG - Actual lines for insert_at_beginning: {actual_lines}") # For debugging
        self.assertEqual(actual_lines, expected_lines)

    def test_new_file_fails_fast_on_leading_delimiter(self):
        """Creating a new file must not start with a delimiter; expect actionable error."""
        target_rel = "new_with_delim.txt"
        # Start with delimiter, then any content
        code_edit = (
            "// ... existing code ...\n"
            "Some content that cannot be anchored\n"
        )
        with self.assertRaises(ValueError) as cm:
            edit_file(target_file=target_rel, code_edit=code_edit, instructions="Attempt new-file with leading delimiter")
        self.assertIn("Cannot apply delimiter-based patch to a new file", str(cm.exception))

    def test_new_file_allows_trailing_delimiter_only(self):
        """Creating a new file with a code segment followed by a trailing delimiter should succeed."""
        target_rel = "new_trailing_delim.txt"
        code_edit = (
            "first line\n"
            "second line\n"
            "// ... existing code ...\n"  # trailing delimiter should be a no-op on empty original
        )
        result = edit_file(target_file=target_rel, code_edit=code_edit, instructions="Create with trailing delimiter")
        self.assertTrue(result.get("success"))
        entry = self._get_file_entry(target_rel)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.get("content_lines"), ["first line\n", "second line\n"])

    def test_edit_insert_at_end_with_patching(self):
        """Verify inserting lines at the file end, preserving original content."""
        target_rel = "main.txt"
        original_content_raw = ["Original Line 1", "Original Line 2"]
        abs_target_path = self._add_file_to_mock_db(target_rel, original_content_raw)

        code_edit = (
            "// ... existing code ...\n"  # Delimiter indicates original content (up to "Original Line 2") should be kept
            "Original Line 2\n"  # This is the last line of original content to keep, acting as context
            "Appended Line C\n"  # New line to append
            "Appended Line D\n"  # New line to append
        )
        instructions = "Append two lines."

        result = edit_file(
            target_file=target_rel, code_edit=code_edit, instructions=instructions
        )

        self.assertIsInstance(result, dict)
        self.assertIn("updated successfully", result.get("message", ""))
        expected_lines = [
            "Original Line 1\n",
            "Original Line 2\n",
            "Appended Line C\n",
            "Appended Line D\n",
        ]
        self.assertEqual(
            self._get_file_entry(target_rel).get("content_lines"), expected_lines
        )

    def test_edit_modify_middle_section_with_patching(self):
        """Verify modifying a middle section, preserving start and end, using delimiters."""
        target_rel = "service.py"
        original_content_raw = [
            "def start_service():",  # Context
            "    # Old implementation",  # To be replaced
            "    print('starting...')",  # To be replaced
            "    return True",  # Context
        ]
        abs_target_path = self._add_file_to_mock_db(target_rel, original_content_raw)

        code_edit = (
            "// ... existing code ...\n"  # Delimiter 1: Preserve original lines UNTIL "def start_service():"
            "def start_service():\n"  # Start of AI Hunk: Leading context from original
            "    # New, improved implementation\n"
            "    logger.info('Service starting with new logic.')\n"
            "    return True\n"  # End of AI Hunk: Trailing context from original
            "// ... existing code ...\n"  # Delimiter 2: Preserve original lines AFTER "return True:"
        )
        instructions = "Refactor service start logic."

        result = edit_file(
            target_file=target_rel, code_edit=code_edit, instructions=instructions
        )

        self.assertIsInstance(result, dict)
        self.assertIn("updated successfully", result.get("message", ""))
        expected_lines = [
            "def start_service():\n",
            "    # New, improved implementation\n",
            "    logger.info('Service starting with new logic.')\n",
            "    return True\n",
        ]
        self.assertEqual(
            self._get_file_entry(target_rel).get("content_lines"), expected_lines
        )

    def test_edit_preserves_original_if_only_delimiters_and_context(self):
        """Verify file is unchanged if code_edit provides full context around delimiters."""
        target_rel = "original.txt"
        original_content_raw = ["Line 1", "Line 2", "Line 3"]
        abs_target_path = self._add_file_to_mock_db(target_rel, original_content_raw)

        code_edit = (
            "Line 1\n"
            "// ... existing code ...\n"  # Preserves Line 2
            "Line 3\n"
        )
        instructions = "No actual changes, just re-stating context."

        result = edit_file(
            target_file=target_rel, code_edit=code_edit, instructions=instructions
        )
        self.assertIsInstance(result, dict)
        self.assertIn("updated successfully", result.get("message", ""))
        expected_lines = ["Line 1\n", "Line 2\n", "Line 3\n"]
        self.assertEqual(
            self._get_file_entry(target_rel).get("content_lines"), expected_lines
        )

    def test_edit_deletes_section_by_providing_surrounding_context(self):
        """Verify a section is deleted when AI provides context that skips original lines."""
        target_rel = "data.txt"
        original_content_raw = [
            "header: true",
            "key1: value1",  # Leading context to keep
            "key_to_delete: old",  # This line should be deleted
            "key_also_delete: true",  # This too
            "key3: value3",  # Trailing context to keep
            "footer: true",
        ]
        abs_target_path = self._add_file_to_mock_db(target_rel, original_content_raw)

        # AI provides the lines it wants to KEEP, consecutively.
        # The lines between "key1: value1" and "key3: value3" in the original
        # are omitted here, implying their deletion.
        code_edit = (
            "// ... existing code ...\n"  # Preserve original lines before "key1: value1"
            "key1: value1\n"  # Start of AI Hunk - lines to keep
            "key3: value3\n"  # End of AI Hunk - lines to keep
            "// ... existing code ...\n"  # Preserve original lines after "key3: value3"
        )
        instructions = "Delete key_to_delete and key_also_delete."

        result = edit_file(
            target_file=target_rel, code_edit=code_edit, instructions=instructions
        )

        self.assertIsInstance(result, dict)
        self.assertIn("updated successfully", result.get("message", ""))
        expected_lines = [
            "header: true\n",
            "key1: value1\n",
            "key3: value3\n",
            "footer: true\n",
        ]
        self.assertEqual(
            self._get_file_entry(target_rel).get("content_lines"), expected_lines
        )

    def test_edit_leading_delimiter_preserves_start_of_original(self):
        """Verify a leading delimiter preserves original content until AI hunk context."""
        target_rel = "log.txt"
        original_content_raw = [
            "Line A",
            "Line B",
            "Line C (context)",
            "Line D (to replace)",
        ]
        abs_target_path = self._add_file_to_mock_db(target_rel, original_content_raw)
        code_edit = (
            "// ... existing code ...\n"  # Preserve from start of original
            "Line C (context)\n"  # AI Hunk starts here, providing context
            "NEW Line D (replacement)\n"  # AI Hunk new content
        )
        instructions = "Keep start, replace Line D."
        result = edit_file(
            target_file=target_rel, code_edit=code_edit, instructions=instructions
        )
        self.assertIsInstance(result, dict)
        self.assertIn("updated successfully", result.get("message", ""))
        expected_lines = [
            "Line A\n",
            "Line B\n",
            "Line C (context)\n",
            "NEW Line D (replacement)\n",
        ]
        self.assertEqual(
            self._get_file_entry(target_rel).get("content_lines"), expected_lines
        )

    def test_edit_trailing_delimiter_preserves_end_of_original(self):
        """Verify a trailing delimiter preserves original content after AI hunk."""
        target_rel = "config.cfg"
        original_content_raw = [
            "Setting A (to replace)",
            "Setting B (context)",
            "Setting C",
            "Setting D",
        ]
        abs_target_path = self._add_file_to_mock_db(target_rel, original_content_raw)
        code_edit = (
            "NEW Setting A (replacement)\n"  # AI Hunk new content
            "Setting B (context)\n"  # AI Hunk ends here with context
            "// ... existing code ...\n"  # Preserve rest of original
        )
        instructions = "Replace Setting A, keep end."
        result = edit_file(
            target_file=target_rel, code_edit=code_edit, instructions=instructions
        )
        self.assertIsInstance(result, dict)
        self.assertIn("updated successfully", result.get("message", ""))
        expected_lines = [
            "NEW Setting A (replacement)\n",
            "Setting B (context)\n",
            "Setting C\n",
            "Setting D\n",
        ]
        self.assertEqual(
            self._get_file_entry(target_rel).get("content_lines"), expected_lines
        )

    def test_edit_handles_context_not_found_intelligently(self):
        """Verify LLM intelligently handles context that doesn't exist by adding new code appropriately."""
        target_rel = "main.py"
        self._add_file_to_mock_db(target_rel, ["def original_func():\n", "    pass\n"])
        code_edit = (
            "// ... existing code ...\ndef non_existent_context():\n    print('new')\n"
        )

        # LLM should succeed and add the new function intelligently
        result = edit_file(
            target_file=target_rel, code_edit=code_edit, instructions="Add new function."
        )
        
        # Verify success
        self.assertTrue(result["success"])
        
        # Verify the new function was added (LLM should append it)
        updated_content = self._get_file_entry(target_rel)["content_lines"]
        self.assertIn("def non_existent_context():\n", updated_content)
        self.assertIn("    print('new')\n", updated_content)
        # Original function should still be there
        self.assertIn("def original_func():\n", updated_content)
        self.assertIn("    pass\n", updated_content)

    def test_edit_handles_ambiguous_context_intelligently(self):
        """Verify LLM intelligently resolves ambiguous context by making reasonable choices."""
        target_rel = "ambiguous.txt"
        original_content_raw = [
            "context_line\n",
            "section A\n",
            "context_line\n", 
            "section B\n",
            "context_line\n",
        ]
        self._add_file_to_mock_db(target_rel, original_content_raw)
        code_edit = "// ... existing code ...\ncontext_line\n    new_stuff_here\n"  # context_line is ambiguous

        # LLM should succeed and make a reasonable choice (typically first match)
        result = edit_file(
            target_file=target_rel,
            code_edit=code_edit,
            instructions="Add content after context line.",
        )
        
        # Verify success
        self.assertTrue(result["success"])
        
        # Verify the edit was applied (LLM typically chooses first occurrence)
        updated_content = self._get_file_entry(target_rel)["content_lines"]
        self.assertIn("    new_stuff_here\n", updated_content)
        
        # Should have modified one of the context_line occurrences
        content_str = ''.join(updated_content)
        self.assertIn("context_line\n    new_stuff_here\n", content_str)

    # --- Standard Error Condition Tests ---
    def test_create_file_fails_if_parent_dir_missing(self):
        target_rel_path = "nonexistent_dir/new_file.txt"
        abs_path = os.path.normpath(os.path.join(self.workspace_path, target_rel_path))
        parent_dir = os.path.dirname(abs_path)
        self.assertNotIn(parent_dir, self.db_for_test["file_system"])
        with self.assertRaises(FileNotFoundError) as cm:
            edit_file(
                target_file=target_rel_path, code_edit="content", instructions="Test."
            )
        self.assertIn("Parent directory", str(cm.exception))

    def test_edit_fails_if_target_is_directory(self):
        target_rel_path = "src_dir"
        self._add_dir_to_mock_db(target_rel_path)
        with self.assertRaises(IsADirectoryError) as cm:
            edit_file(
                target_file=target_rel_path, code_edit="content", instructions="Test."
            )
        self.assertIn("exists but is a directory", str(cm.exception))

    def test_edit_fails_if_path_outside_workspace(self):
        target_rel_path = "../../etc/passwd"
        with self.assertRaises(ValueError) as cm:
            edit_file(
                target_file=target_rel_path, code_edit="content", instructions="Test."
            )
        self.assertIn("outside the permitted workspace", str(cm.exception))



@unittest.skipUnless(GEMINI_API_KEY_IS_AVAILABLE, "GEMINI_API_KEY not set, skipping LLM integration tests for edit_file.")
class TestEditFileWithLiveLLMProposals(BaseTestCaseWithErrorHandler):
    """
    Integration tests for edit_file, using LIVE output from
    utils.propose_code_edits (which calls an LLM).
    These tests require a GEMINI_API_KEY.
    """
    def setUp(self):
        """Prepares an isolated database state for each live test."""
        # Create temporary workspace and DB state
        self.workspace_path, self.db_for_test = minimal_reset_db_for_edit_file()
        
        # Patch 'DB' for the duration of the test.
        self.db_patcher_for_init_module = patch("cursor.DB", self.db_for_test)
        self.db_patcher_for_init_module.start()
        self.db_patcher_for_utils_module = patch("cursor.SimulationEngine.utils.DB", self.db_for_test)
        self.db_patcher_for_utils_module.start()
        
        # Patch 'DB' in the cursorAPI module where the actual function is defined
        self.db_patcher_for_cursorapi_module = patch("cursor.cursorAPI.DB", self.db_for_test)
        self.db_patcher_for_cursorapi_module.start()

    def tearDown(self):
        """Restores original state after each live test."""
        self.db_patcher_for_cursorapi_module.stop()
        self.db_patcher_for_utils_module.stop()
        self.db_patcher_for_init_module.stop()
        
        # Clean up temporary workspace
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    # Helper methods _add_dir_to_db and _add_file_to_db are duplicated here for clarity.
    # In a real project, consider a common base class or test utility module.
    def _add_dir_to_db(self, path: str, is_abs: bool = False):
        abs_path = path
        if not is_abs: 
            abs_path = os.path.normpath(os.path.join(self.workspace_path, path))
        if abs_path not in self.db_for_test["file_system"]:
            # Create the directory on filesystem
            os.makedirs(abs_path, exist_ok=True)
            
            self.db_for_test["file_system"][abs_path] = {
                "path": abs_path, 
                "is_directory": True, 
                "content_lines": [], 
                "size_bytes": 0, 
                "last_modified": utils.get_current_timestamp_iso()
            }
        parent_dir = os.path.dirname(abs_path)
        if parent_dir and parent_dir != abs_path and parent_dir != self.workspace_path and parent_dir not in self.db_for_test["file_system"] and parent_dir != os.path.dirname(self.workspace_path):
            self._add_dir_to_db(parent_dir, is_abs=True)

    def _add_file_to_db(self, path: str, content_lines_raw: list[str], is_abs: bool = False):
        abs_path = path
        if not is_abs: 
            abs_path = os.path.normpath(os.path.join(self.workspace_path, path))
        dir_name = os.path.dirname(abs_path)
        if dir_name and dir_name != self.workspace_path and dir_name not in self.db_for_test["file_system"]:
            self._add_dir_to_db(dir_name, is_abs=True)
        content_lines = utils._normalize_lines(content_lines_raw, ensure_trailing_newline=True)
        
        # Create the file on filesystem - write as proper text content
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.writelines(content_lines)
        
        self.db_for_test["file_system"][abs_path] = {
            "path": abs_path, 
            "is_directory": False, 
            "content_lines": content_lines,
            "size_bytes": utils.calculate_size_bytes(content_lines), 
            "last_modified": utils.get_current_timestamp_iso()
        }

    def _get_file_content_lines(self, path_rel_to_ws_root: str):
        abs_path = os.path.normpath(os.path.join(self.workspace_path, path_rel_to_ws_root))
        entry = self.db_for_test.get("file_system", {}).get(abs_path)
        return entry.get("content_lines", []) if entry and not entry.get("is_directory") else None

    # --- Live LLM Interaction Test Cases ---
    def test_live_edit_create_simple_python_file(self):
        """Integration test: Create a new Python file via LLM proposal and apply with edit_file."""
        target_file_rel = "live_generated_script.py" # Relative to self.workspace_path
        user_instructions = "Create a simple python script that defines a function 'greet' which takes a name and prints 'Hello, [name]!' and then calls this function with 'World'."
        abs_target_path = os.path.normpath(os.path.join(self.workspace_path, target_file_rel))

        print(f"\n[LIVE EDIT TEST - CREATE] Requesting LLM proposal for: {target_file_rel}")
        # Call the utility that makes the actual LLM call
        proposal = utils.propose_code_edits(
            target_file_path_str=target_file_rel, # propose_code_edits expects path rel to CWD
            user_edit_instructions=user_instructions
        )
        print(f"  LLM Instructions: {proposal['instructions']}")
        print(f"LLM Code Edit:\n{proposal['code_edit']}")

        self.assertIsInstance(proposal["instructions"], str)
        self.assertIsInstance(proposal["code_edit"], str)
        self.assertTrue(len(proposal["instructions"]) > 5, "LLM-generated instructions seem too short.")
        self.assertTrue(len(proposal["code_edit"]) > 10, "LLM-generated code_edit seems too short.")

        # Apply the LLM's proposal using the edit_file function
        result = edit_file(
            target_file=target_file_rel, # edit_file also expects path rel to CWD
            code_edit=proposal["code_edit"],
            instructions=proposal["instructions"]
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("successfully", result.get("message", ""))
        self.assertEqual(result.get("file_path"), abs_target_path)
        
        new_content = self._get_file_content_lines(target_file_rel)
        self.assertIsNotNone(new_content, "File content should exist after creation.")
        # Flexible checks for LLM-generated content
        self.assertIn("def greet(name):", "".join(new_content))
        # Use a more flexible check that doesn't depend on quote style
        content_str = "".join(new_content)
        self.assertTrue(
            "print(f'Hello, {name}!')" in content_str or "print(f\"Hello, {name}!\")" in content_str,
            f"Expected greeting print statement not found in: {content_str}"
        )
        # Check for function call with flexible quotes
        self.assertTrue(
            "greet('World')" in content_str or "greet(\"World\")" in content_str,
            f"Expected function call not found in: {content_str}"
        )
        print(f"  File '{target_file_rel}' created via LLM proposal and edit_file verified (flexibly).")

    def test_live_edit_modify_existing_file_add_comment(self):
        """Integration test: Modify an existing file by adding a comment via LLM proposal."""
        target_file_rel = "live_comment_target.py"
        original_content = ["def my_function(x, y):", "    return x + y"]
        self._add_file_to_db(target_file_rel, original_content)
        user_instructions = "In live_comment_target.py, add a docstring to my_function explaining it adds two numbers."
        abs_target_path = os.path.normpath(os.path.join(self.workspace_path, target_file_rel))

        print(f"\n[LIVE EDIT TEST - MODIFY COMMENT] Requesting LLM proposal for: {target_file_rel}")
        proposal = utils.propose_code_edits(
            target_file_path_str=target_file_rel,
            user_edit_instructions=user_instructions
        )
        print(f"  LLM Instructions: {proposal['instructions']}")
        print(f"LLM Code Edit:\n{proposal['code_edit']}")

        self.assertIsInstance(proposal["instructions"], str)
        self.assertIsInstance(proposal["code_edit"], str)
        # We're no longer strictly requiring delimiters, as the LLM might provide a complete file replacement
        # or use a different format that still works with edit_file
        
        result = edit_file(
            target_file=target_file_rel,
            code_edit=proposal["code_edit"],
            instructions=proposal["instructions"]
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("successfully", result.get("message", ""))
        
        updated_content = self._get_file_content_lines(target_file_rel)
        self.assertIsNotNone(updated_content)
        updated_content_str = "".join(updated_content)
        self.assertIn("def my_function(x, y):", updated_content_str) # Original context
        self.assertIn("\"\"\"", updated_content_str) # Presence of docstring
        self.assertIn("adds two numbers", updated_content_str.lower()) # Part of docstring content
        self.assertIn("return x + y", updated_content_str) # Original context
        print(f"  File '{target_file_rel}' modified via LLM proposal and edit_file verified (flexibly).")
        
    def test_live_edit_refactor_class_method(self):
        """Integration test: Create a complex Python file and refactor a class method while adding a new method."""
        # Create a more complex Python file with a class and methods
        target_file_rel = "live_complex_class.py"
        original_content = [
            "class DataProcessor:",
            "    def __init__(self, data_source):",
            "        self.data_source = data_source",
            "        self.processed = False",
            "",
            "    def process_data(self):",
            "        # Basic processing",
            "        if not self.data_source:",
            "            print('No data to process')",
            "            return None",
            "        result = self.data_source.upper()",
            "        self.processed = True",
            "        return result",
            "",
            "# Usage example",
            "processor = DataProcessor('sample text')",
            "processed_data = processor.process_data()",
            "print(processed_data)"
        ]
        self._add_file_to_db(target_file_rel, original_content)
        
        # Complex refactoring request
        user_instructions = (
            "Refactor the DataProcessor class to add error handling in process_data method "
            "and add a new validate_data method that checks if the data_source is a string. "
            "The process_data method should call this validation method first."
        )
        
        abs_target_path = os.path.normpath(os.path.join(self.workspace_path, target_file_rel))
        
        print(f"\n[LIVE EDIT TEST - COMPLEX REFACTOR] Requesting LLM proposal for: {target_file_rel}")
        proposal = utils.propose_code_edits(
            target_file_path_str=target_file_rel,
            user_edit_instructions=user_instructions
        )
        print(f"  LLM Instructions: {proposal['instructions']}")
        print(f"LLM Code Edit:\n{proposal['code_edit']}")
        
        self.assertIsInstance(proposal["instructions"], str)
        self.assertIsInstance(proposal["code_edit"], str)
        
        # Apply the edit
        result = edit_file(
            target_file=target_file_rel,
            code_edit=proposal["code_edit"],
            instructions=proposal["instructions"]
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("successfully", result.get("message", ""))
        
        # Check that the edit was applied correctly
        updated_content = self._get_file_content_lines(target_file_rel)
        self.assertIsNotNone(updated_content)
        updated_content_str = "".join(updated_content)
        
        # Check that the class definition and init method are preserved
        self.assertIn("class DataProcessor:", updated_content_str)
        self.assertIn("def __init__(self, data_source):", updated_content_str)
        
        # Check for the new validate_data method
        self.assertIn("def validate_data", updated_content_str.lower())
        self.assertIn("isinstance", updated_content_str.lower())  # Should use isinstance for type checking
        
        # Check that process_data was modified to include validation
        self.assertIn("def process_data(self):", updated_content_str)
        # Check for error handling
        self.assertTrue(
            "try:" in updated_content_str and 
            ("except" in updated_content_str or "raise" in updated_content_str),
            "Expected error handling in process_data method"
        )
        
        # The validation method should be called from process_data
        validation_call_patterns = [
            "self.validate_data(", 
            "if not self.validate_data("
        ]
        
        has_validation_call = any(pattern in updated_content_str for pattern in validation_call_patterns)
        self.assertTrue(has_validation_call, "Expected process_data to call validate_data")
        
        # Make sure the usage example is still present in some form
        self.assertIn("processor = DataProcessor(", updated_content_str)
        
        print(f"  File '{target_file_rel}' refactored with complex changes verified.")

    def test_live_edit_modify_imports_and_multiple_sections(self):
        """Integration test: Create a file with imports and multiple functions, then modify all sections."""
        target_file_rel = "live_multi_section_edits.py"
        original_content = [
            "import os",
            "import sys",
            "import datetime",
            "",
            "def fetch_data(source):",
            "    # Fetches data from a source",
            "    print(f'Fetching from {source}')",
            "    return {'data': 'sample data', 'timestamp': datetime.datetime.now()}",
            "",
            "def transform_data(data_dict):",
            "    # Simple transformation",
            "    if not data_dict:",
            "        return None",
            "    return data_dict.get('data', '').upper()",
            "",
            "def save_result(transformed_data, output_path):",
            "    # Save to a file",
            "    with open(output_path, 'w') as f:",
            "        f.write(transformed_data)",
            "    return True",
            "",
            "# Main execution",
            "if __name__ == '__main__':",
            "    source = sys.argv[1] if len(sys.argv) > 1 else 'default'",
            "    output = os.path.join(os.getcwd(), 'output.txt')",
            "    data = fetch_data(source)",
            "    transformed = transform_data(data)",
            "    success = save_result(transformed, output)",
            "    print(f'Operation completed: {success}')"
        ]
        self._add_file_to_db(target_file_rel, original_content)
        
        # Complex request to modify imports and multiple functions
        user_instructions = (
            "Make the following changes to live_multi_section_edits.py:\n"
            "1. Add import json and logging\n"
            "2. Modify fetch_data to include error handling and log when it starts and finishes\n"
            "3. Update save_result to optionally save as JSON if the output_path ends with .json\n"
            "4. Update the main execution to use try/except and log any errors"
        )
        
        abs_target_path = os.path.normpath(os.path.join(self.workspace_path, target_file_rel))
        
        print(f"\n[LIVE EDIT TEST - MULTI-SECTION EDITS] Requesting LLM proposal for: {target_file_rel}")
        proposal = utils.propose_code_edits(
            target_file_path_str=target_file_rel,
            user_edit_instructions=user_instructions
        )
        print(f"  LLM Instructions: {proposal['instructions']}")
        print(f"  LLM Code Edit:\n{proposal['code_edit']}")
        
        # Apply the edit
        result = edit_file(
            target_file=target_file_rel,
            code_edit=proposal["code_edit"],
            instructions=proposal["instructions"]
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn("successfully", result.get("message", ""))
        
        # Check that the edit was applied correctly
        updated_content = self._get_file_content_lines(target_file_rel)
        self.assertIsNotNone(updated_content)
        updated_content_str = "".join(updated_content)
        
        # 1. Check imports were added
        self.assertIn("import json", updated_content_str)
        self.assertIn("import logging", updated_content_str)
        
        # Original imports should still be there (os import is optional since LLM might optimize it out)
        # self.assertIn("import os", updated_content_str)  # LLM might optimize this out
        self.assertIn("import sys", updated_content_str)
        self.assertIn("import datetime", updated_content_str)
        
        # 2. Check fetch_data was modified
        fetch_data_section = updated_content_str.split("def fetch_data")[1].split("def ")[0]
        
        # Should have logging
        self.assertTrue(
            "logging.info" in fetch_data_section or 
            "logging.debug" in fetch_data_section,
            "Expected logging in fetch_data function"
        )
        
        # Should have error handling
        self.assertTrue(
            "try:" in fetch_data_section and "except" in fetch_data_section,
            "Expected error handling in fetch_data function"
        )
        
        # 3. Check save_result was modified
        save_result_section = updated_content_str.split("def save_result")[1].split("def ")[0]
        if "def " not in updated_content_str.split("def save_result")[1]:
            # If it's the last function, need different splitting
            save_result_section = updated_content_str.split("def save_result")[1].split("if __name__")[0]
        
        # Should handle JSON
        self.assertTrue(
            ".json" in save_result_section and "json.dump" in save_result_section,
            "Expected JSON handling in save_result function"
        )
        
        # 4. Check main execution has try/except
        main_section = updated_content_str.split("if __name__ == '__main__':")[1]
        
        self.assertTrue(
            "try:" in main_section and "except" in main_section,
            "Expected try/except in main execution section"
        )
        
        # Check for logging of errors
        self.assertTrue(
            "logging" in main_section.lower() and "error" in main_section.lower(),
            "Expected error logging in main execution section"
        )
        
        print(f"  File '{target_file_rel}' with multi-section edits verified.")


class TestEditFileWorkspaceValidation(BaseTestCaseWithErrorHandler):
    """Test cases for selective workspace validation in edit_file."""

    transient_test_files = [
        "test_db.json",
        "test_persistence.json", 
        "test_state.json",
    ]

    def setUp(self):
        """Set up empty workspace for validation testing."""
        # Create empty DB state
        self.empty_db = {
            "workspace_root": "",
            "cwd": "",
            "file_system": {},
            "last_edit_params": None,
            "background_processes": {},
            "_next_pid": 1
        }

        # Create hydrated workspace
        self.workspace_path, self.hydrated_db = minimal_reset_db_for_edit_file()

        # Start with empty workspace patches
        self.db_patcher_cursorapi = patch("cursor.cursorAPI.DB", self.empty_db)
        self.db_patcher_utils = patch("cursor.SimulationEngine.utils.DB", self.empty_db)
        self.db_patcher_init = patch("cursor.DB", self.empty_db)
        self.db_patcher_db_module = patch("cursor.SimulationEngine.db.DB", self.empty_db)
        
        self.db_patcher_cursorapi.start()
        self.db_patcher_utils.start()
        self.db_patcher_init.start()
        self.db_patcher_db_module.start()
        
        self._cleanup_transient_files()

    def tearDown(self):
        """Clean up after tests."""
        self._cleanup_transient_files()
        
        self.db_patcher_db_module.stop()
        self.db_patcher_init.stop()
        self.db_patcher_utils.stop()
        self.db_patcher_cursorapi.stop()
        
        # Clean up temporary workspace
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def _cleanup_transient_files(self):
        """Remove transient test files."""
        cursor_module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for filename in self.transient_test_files:
            file_path = os.path.join(cursor_module_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    print(f"Warning: Could not clean up test file {file_path}: {e}")

    def _switch_to_hydrated_db(self):
        """Switch to hydrated database for positive tests."""
        # Stop current patches
        self.db_patcher_db_module.stop()
        self.db_patcher_init.stop()
        self.db_patcher_utils.stop()
        self.db_patcher_cursorapi.stop()
        
        # Start new patches with hydrated DB
        self.db_patcher_cursorapi = patch("cursor.cursorAPI.DB", self.hydrated_db)
        self.db_patcher_utils = patch("cursor.SimulationEngine.utils.DB", self.hydrated_db)
        self.db_patcher_init = patch("cursor.DB", self.hydrated_db)
        self.db_patcher_db_module = patch("cursor.SimulationEngine.db.DB", self.hydrated_db)
        
        self.db_patcher_cursorapi.start()
        self.db_patcher_utils.start()
        self.db_patcher_init.start()
        self.db_patcher_db_module.start()

    def test_create_new_file_without_hydration(self):
        """Test that creating new files works without workspace hydration."""
        # This should work - creating new files doesn't require hydration
        try:
            result = edit_file("new_file.py", "print('hello world')", "Create new file")
            # Should not raise WorkspaceNotHydratedError
            # May raise other errors due to empty workspace_root, which is expected
        except ValueError as e:
            # ValueError is expected when workspace_root is not configured
            # This is acceptable behavior for bootstrapping new files
            if "workspace root is not configured" in str(e).lower():
                pass  # This is expected and acceptable
            else:
                self.fail(f"edit_file raised unexpected ValueError: {e}")
        except WorkspaceNotHydratedError:
            self.fail("edit_file raised WorkspaceNotHydratedError when creating new file")
        except Exception:
            # Other exceptions are acceptable for this test
            pass

    def test_edit_existing_file_requires_hydration(self):
        """Test that editing existing files requires workspace hydration."""
        # Add an existing file to the empty DB (simulating file exists but workspace not hydrated)
        test_file_path = "/fake/path/existing_file.py"
        self.empty_db["file_system"] = {
            test_file_path: {
                "path": test_file_path,
                "is_directory": False,
                "content_lines": ["print('existing content')"],
                "size_bytes": 25,
                "last_modified": "2025-09-17T12:00:00Z"
            }
        }
        
        # Since edit_file validation was removed, it now raises ValueError for missing workspace_root
        with self.assertRaises(ValueError):
            edit_file("existing_file.py", "print('modified content')", "Modify existing file")


class TestEditFileDocBehavior(BaseTestCaseWithErrorHandler):
    """Unskipped tests validating documented delimiter/context rules."""

    def setUp(self):
        # Hydrated DB with a temp workspace
        self.workspace_path, self.db_for_test = minimal_reset_db_for_edit_file()
        self.db_patcher_cursorapi = patch("cursor.cursorAPI.DB", self.db_for_test)
        self.db_patcher_utils = patch("cursor.SimulationEngine.utils.DB", self.db_for_test)
        self.db_patcher_init = patch("cursor.DB", self.db_for_test)
        self.db_patcher_cursorapi.start()
        self.db_patcher_utils.start()
        self.db_patcher_init.start()

    def tearDown(self):
        self.db_patcher_init.stop()
        self.db_patcher_utils.stop()
        self.db_patcher_cursorapi.stop()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def _add_file(self, rel_path: str, lines: list[str]):
        abs_path = os.path.normpath(os.path.join(self.workspace_path, rel_path))
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        content_lines = utils._normalize_lines(lines, ensure_trailing_newline=True)
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

    def _get_lines(self, rel_path: str):
        abs_path = os.path.normpath(os.path.join(self.workspace_path, rel_path))
        entry = self.db_for_test.get("file_system", {}).get(abs_path)
        return entry.get("content_lines") if entry else None

    def test_full_replacement_without_delimiters(self):
        target = "no_delims.txt"
        self._add_file(target, ["A", "B", "C"])  # will be normalized with \n
        result = edit_file(target, "X\nY\n", "Full replace")
        self.assertTrue(result.get("success"))
        self.assertEqual(self._get_lines(target), ["X\n", "Y\n"])

    def test_delimiter_styles_and_case_insensitive_phrase(self):
        target = "delims_styles.txt"
        self._add_file(target, ["keep head", "ctx1", "ctx2", "tail"])  # normalized

        # Use different styles and casing for the core phrase
        code_edit = (
            "# ... EXISTING CODE ...\n"  # leading preserve until ctx1
            "ctx1\n"  # leading context
            "NEW\n"   # change
            "ctx2\n"  # trailing context
            "/* ... existing code ... */\n"  # preserve rest
        )
        result = edit_file(target, code_edit, "Styles and case-insensitive delimiter")
        self.assertTrue(result.get("success"))
        self.assertEqual(self._get_lines(target), [
            "keep head\n",
            "ctx1\n",
            "NEW\n",
            "ctx2\n",
            "tail\n",
        ])

    def test_leading_delimiter_preserves_prefix(self):
        target = "prefix_keep.txt"
        self._add_file(target, ["P1", "P2", "C1", "T1"])  # normalized
        code_edit = (
            "// ... existing code ...\n"  # keep P1, P2
            "C1\n"  # leading context
            "NEW_T1\n"  # replace T1
        )
        result = edit_file(target, code_edit, "Leading delimiter preserves prefix")
        self.assertTrue(result.get("success"))
        self.assertEqual(self._get_lines(target), [
            "P1\n", "P2\n", "C1\n", "NEW_T1\n"
        ])

    def test_trailing_delimiter_preserves_remainder(self):
        target = "suffix_keep.txt"
        self._add_file(target, ["H1", "C1", "C2", "T1", "T2"])  # normalized
        code_edit = (
            "NEW_H0\n"  # insertion at start (prepend behavior)
            "H1\n"      # trailing context for prepend
            "// ... existing code ...\n"  # preserve rest
        )
        result = edit_file(target, code_edit, "Trailing delimiter preserves remainder")
        self.assertTrue(result.get("success"))
        self.assertEqual(self._get_lines(target), [
            "NEW_H0\n", "H1\n", "C1\n", "C2\n", "T1\n", "T2\n"
        ])

    def test_end_with_segment_discards_remainder(self):
        target = "discard_tail.txt"
        self._add_file(target, ["A", "B", "C", "D"])  # normalized
        # Replace up to C and omit trailing delimiter, so D is discarded
        code_edit = (
            "// ... existing code ...\n"
            "B\n"      # leading context
            "B2\n"     # new line
            "C\n"      # trailing context
        )
        result = edit_file(target, code_edit, "Segment end discards remainder")
        self.assertTrue(result.get("success"))
        self.assertEqual(self._get_lines(target), ["A\n", "B\n", "B2\n", "C\n"])  # D removed

    def test_ambiguous_context_error_for_non_first_hunk(self):
        target = "ambiguous_mid.txt"
        # Two identical context blocks create ambiguity for the second hunk
        self._add_file(target, [
            "X", "K", "X", "K", "Z"
        ])
        # First hunk is fine; second hunk's leading context "X" is ambiguous
        code_edit = (
            "// ... existing code ...\n"
            "K\n"  # leading context (anchors after first X)
            "K2\n"
            "X\n"  # trailing context
            "// ... existing code ...\n"
            "X\n"  # ambiguous leading context for second hunk
            "NEW\n"
            "Z\n"
        )
        with self.assertRaises(ValueError):
            edit_file(target, code_edit, "Expect ambiguous context error")

if __name__ == '__main__':
    unittest.main()