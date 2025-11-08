# cursor/tests/test_read_file.py
import copy
import os
import tempfile
import shutil
from unittest.mock import patch
from ..cursorAPI import read_file
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.custom_errors import InvalidInputError, WorkspaceNotHydratedError
from ..SimulationEngine import utils

def normalize_for_db(path_string):
    if path_string is None:
        return None
    # Remove any drive letter prefix first
    if len(path_string) > 2 and path_string[1:3] in [':/', ':\\']:
        path_string = path_string[2:]
    # Then normalize and convert slashes
    return os.path.normpath(path_string).replace("\\", "/")

def minimal_reset_db_for_read_file(workspace_path_for_db=None):
    """Creates a fresh minimal DB state for testing, clearing and setting up root."""
    if workspace_path_for_db is None:
        workspace_path_for_db = tempfile.mkdtemp(prefix="test_read_file_workspace_")
    
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


class TestReadFile(BaseTestCaseWithErrorHandler):
    """
    Test cases for the read_file function, covering all major branches and edge cases.
    """

    def setUp(self):
        # Create temporary workspace and DB state
        self.workspace_path, self.db_for_test = minimal_reset_db_for_read_file()
        
        # Patch 'DB' in relevant modules
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
        
        # CRITICAL: Patch 'DB' in the db module where validate_workspace_hydration is defined
        self.db_patcher_for_db_module = patch("cursor.SimulationEngine.db.DB", self.db_for_test)
        self.db_patcher_for_db_module.start()
        
        # Patch call_llm to return a dummy summary - patch it where it's imported in cursorAPI
        self.llm_patcher = patch("cursor.cursorAPI.call_llm", return_value="Dummy summary")
        self.llm_patcher.start()

    def tearDown(self):
        self.llm_patcher.stop()
        self.db_patcher_for_db_module.stop()
        self.db_patcher_for_cursorapi_module.stop()
        self.db_patcher_for_utils_module.stop()
        self.db_patcher_for_init_module.stop()
        
        # Clean up temporary workspace
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def _add_file(self, path, content_lines=None):
        if content_lines is None:
            content_lines = ["line1\n", "line2\n", "line3\n"]
        
        abs_path = path
        if not os.path.isabs(path):
            abs_path = os.path.normpath(os.path.join(self.workspace_path, path))

        # Create the file on filesystem
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.writelines(content_lines)
        
        self.db_for_test["file_system"][abs_path] = {
            "path": abs_path,
            "is_directory": False,
            "content_lines": content_lines,
            "size_bytes": sum(len(l) for l in content_lines),
            "last_modified": utils.get_current_timestamp_iso(),
        }

    def _add_dir(self, path):
        abs_path = path
        if not os.path.isabs(path):
            abs_path = os.path.normpath(os.path.join(self.workspace_path, path))

        # Create the directory on filesystem
        os.makedirs(abs_path, exist_ok=True)
        
        self.db_for_test["file_system"][abs_path] = {
            "path": abs_path,
            "is_directory": True,
            "size_bytes": 0,
            "last_modified": utils.get_current_timestamp_iso(),
        }

    # --- Test Cases ---

    def test_read_entire_file_success(self):
        """Should read all lines when should_read_entire_file is True."""
        content = ["a\n", "b\n", "c\n"]
        self._add_file("test.txt", content)
        result = read_file("test.txt", 1, 2, should_read_entire_file=True)
        self.assertEqual(result["content"], content)
        self.assertEqual(result["total_lines"], 3)
        self.assertEqual(result["path_processed"], os.path.join(self.workspace_path, "test.txt"))
        self.assertIsNone(result["summary_of_truncated_content"])
        self.assertIn("Successfully read all 3 lines", result["message"])

    def test_read_partial_lines_success(self):
        """Should read a specific line range and return summary."""
        content = ["a\n", "b\n", "c\n", "d\n"]
        self._add_file("test.txt", content)
        result = read_file("test.txt", 2, 3)
        self.assertEqual(result["content"], ["b\n", "c\n"])
        self.assertEqual(result["total_lines"], 4)
        self.assertEqual(result["path_processed"], os.path.join(self.workspace_path, "test.txt"))
        self.assertIn("summary_of_truncated_content", result)
        self.assertEqual(result["summary_of_truncated_content"], "Dummy summary")
        self.assertEqual(result["message"], "Successfully read lines 2-3 from the file.")

    def test_read_with_leading_slash(self):
        """Should raise error in case of invalid absolute path."""
        content = ["x\n", "y\n"]
        self._add_file("foo.txt", content)
        with self.assertRaises(ValueError) as cm:
            read_file("/foo.txt", 1, 2)
        self.assertIn("outside the permitted workspace", str(cm.exception))

    def test_empty_target_file_path(self):
        """Should fail if target_file is empty."""
        with self.assertRaises(InvalidInputError):
            read_file("", 1, 1)

    def test_target_file_is_directory(self):
        """Should fail if the target is a directory."""
        self._add_dir("dir")
        with self.assertRaises(IsADirectoryError):
            read_file("dir", 1, 1)

    def test_file_not_found(self):
        """Should fail if the file does not exist."""
        with self.assertRaises(FileNotFoundError):
            read_file("nofile.txt", 1, 1)

    def test_workspace_root_not_configured(self):
        """Should raise ValueError if workspace_root is missing."""
        # Create a test DB without workspace_root
        invalid_db = {
            "cwd": "/tmp/test",
            "file_system": {},
            "last_edit_params": None,
            "background_processes": {},
            "_next_pid": 1
        }
        
        # Patch the DB to use the invalid state
        with patch("cursor.cursorAPI.DB", invalid_db):
            with self.assertRaises(ValueError):
                read_file("test.txt", 1, 1)

    def test_path_outside_workspace(self):
        """Should raise ValueError if resolved path is outside workspace."""
        # Try to escape workspace with ../
        with self.assertRaises(ValueError) as cm:
            read_file("../outside.txt", 1, 1)
        self.assertIn("outside the permitted workspace", str(cm.exception))

    def test_invalid_path_segment(self):
        """Should fail if path segment is empty after lstrip."""
        with self.assertRaises(ValueError) as cm:
            read_file("/", 1, 1)
        self.assertIn("outside the permitted workspace", str(cm.exception))

    def test_truncation_of_large_content(self):
        """Should truncate content to 250 lines if file is very large."""
        content = [f"line{i}\n" for i in range(300)]
        self._add_file("big.txt", content)
        result = read_file("big.txt", 1, 300)
        self.assertEqual(len(result["content"]), 250)
        self.assertIn("summary_of_truncated_content", result)
        self.assertIn("exceeded the 250-line limit", result["message"])

    def test_empty_file_returns_clean_zero_indices(self):
        """Empty file should return start_line=1, end_line=1, empty content, and helpful message."""
        self._add_file("empty.txt", [])
        result = read_file("empty.txt", 1, 10)
        self.assertTrue(result["success"])
        self.assertEqual(result["start_line"], 1)
        self.assertEqual(result["end_line"], 1)
        self.assertEqual(result["content"], [])
        self.assertEqual(result["total_lines"], 0)
        self.assertIn("is empty. No content to read.", result["message"]) 

    def test_summary_prompt_uses_joined_text_not_list_literal(self):
        """Verify the prompt passes a string of joined lines to the LLM, not a Python list literal."""
        # Create a file that forces summary generation (partial read with content outside range)
        content = [f"line {i}\n" for i in range(1, 30)]
        self._add_file("join.txt", content)

        captured_prompts = []
        def _capture_prompt(prompt_text):
            captured_prompts.append(prompt_text)
            return "Dummy summary"

        # Patch call_llm to capture the prompt used
        with patch("cursor.cursorAPI.call_llm", side_effect=_capture_prompt):
            _ = read_file("join.txt", 10, 12)

        # Ensure we captured exactly one prompt
        self.assertEqual(len(captured_prompts), 1)
        prompt = captured_prompts[0]

        # Extract the tail after the intro line to focus on the code block
        marker = "Here is the code below:\n"
        self.assertIn(marker, prompt)
        code_part = prompt.split(marker, 1)[1]

        # The code part should not look like a Python list literal
        self.assertFalse(code_part.strip().startswith("["))
        self.assertNotIn("', '", code_part)  # typical list join artifact
        # It should contain numbered lines joined contiguously for before/after regions
        # Summary excludes the requested window (10-12), so expect 1..9 and 13..end
        self.assertIn("9:", code_part)
        self.assertIn("13:", code_part)
        self.assertNotIn("10:", code_part)

    def test_type_errors_for_arguments(self):
        """Ensure explicit TypeError branches are exercised."""
        self._add_file("types.txt", ["a\n", "b\n"]) 
        with self.assertRaises(TypeError):
            read_file("types.txt", "1", 2)  # start_line as str
        with self.assertRaises(TypeError):
            read_file("types.txt", 1, "2")  # end_line as str
        with self.assertRaises(TypeError):
            read_file("types.txt", 1, 2, should_read_entire_file="no")  # bool as str

    def test_start_line_out_of_bounds_returns_last_chunk(self):
        """Should return the last 250 lines if the start line is out of bounds."""
        content = [f"line{i}\n" for i in range(300)]
        self._add_file("big.txt", content)
        result = read_file("big.txt", 500, 600)

        self.assertEqual(len(result["content"]), 250)
        self.assertEqual(result["content"][0], "line50\n")  # 300 - 250 = 50
        self.assertEqual(result["start_line"], 51)
        self.assertEqual(result["end_line"], 300)
        self.assertIn("start line was out of bounds", result["message"])

    def test_start_line_out_of_bounds_on_small_file(self):
        """Should return the whole file if start is out of bounds and file is small."""
        content = [f"line{i}\n" for i in range(50)]
        self._add_file("small.txt", content)
        result = read_file("small.txt", 100, 200)

        self.assertEqual(len(result["content"]), 50)
        self.assertEqual(result["start_line"], 1)
        self.assertEqual(result["end_line"], 50)
        self.assertIn("start line was out of bounds", result["message"])

    def test_end_line_out_of_bounds_is_capped(self):
        """Should cap the end line if it's out of bounds but start line is not."""
        content = [f"line{i}\n" for i in range(10)]
        self._add_file("test.txt", content)
        result = read_file("test.txt", 5, 20)

        self.assertEqual(len(result["content"]), 6)  # Lines 5-10
        self.assertEqual(result["start_line"], 5)
        self.assertEqual(result["end_line"], 10)
        self.assertIn("file only has 10 lines", result["message"])

    def test_explanation_argument_is_ignored(self):
        """Should accept explanation argument but not use it in return value."""
        content = ["a\n", "b\n"]
        self._add_file("test.txt", content)
        result = read_file("test.txt", 1, 2, explanation="for audit")
        self.assertIsInstance(result, dict)
        self.assertNotIn("explanation", result)

    def test_start_line_greater_than_end_line(self):
        """Should raise ValueError if start_line > end_line."""
        content = ["a\n", "b\n"]
        self._add_file("test.txt", content)
        with self.assertRaises(ValueError) as cm:
            read_file("test.txt", 3, 2)
        self.assertIn("cannot be greater than end line", str(cm.exception))

    def test_start_line_less_than_one(self):
        """Should raise ValueError if start_line < 1."""
        content = ["a\n", "b\n"]
        self._add_file("test.txt", content)
        with self.assertRaises(ValueError) as cm:
            read_file("test.txt", 0, 1)
        self.assertIn("must be 1 or greater", str(cm.exception))

    def test_unhydrated_workspace_raises_workspace_not_hydrated_error(self):
        """Verify WorkspaceNotHydratedError is raised when workspace is not hydrated."""
        # Create an unhydrated DB state
        empty_db = {
            "workspace_root": "",
            "cwd": "",
            "file_system": {},
            "last_edit_params": None,
            "background_processes": {},
            "_next_pid": 1
        }
        
        with patch("cursor.cursorAPI.DB", empty_db):
            with patch("cursor.SimulationEngine.utils.DB", empty_db):
                with patch("cursor.SimulationEngine.db.DB", empty_db):
                    with patch("cursor.DB", empty_db):
                        with self.assertRaises(WorkspaceNotHydratedError):
                            read_file("test.txt")

    def test_validation_error_message_content(self):
        """Verify that WorkspaceNotHydratedError contains helpful message."""
        empty_db = {
            "workspace_root": "",
            "cwd": "",
            "file_system": {},
            "last_edit_params": None,
            "background_processes": {},
            "_next_pid": 1
        }
        
        with patch("cursor.cursorAPI.DB", empty_db):
            with patch("cursor.SimulationEngine.utils.DB", empty_db):
                with patch("cursor.SimulationEngine.db.DB", empty_db):
                    with patch("cursor.DB", empty_db):
                        try:
                            read_file("test.txt")
                        except WorkspaceNotHydratedError as e:
                            error_msg = str(e).lower()
                            self.assertIn("workspace", error_msg)
                            self.assertIn("hydrat", error_msg)
                            self.assertIn("initialize", error_msg)