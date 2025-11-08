# cursor/tests/test_delete_file.py
import unittest
import copy
import os
import tempfile
import shutil
from unittest.mock import patch
from common_utils.base_case import BaseTestCaseWithErrorHandler
from .. import delete_file
from .. import DB as GlobalDBSource
from ..SimulationEngine import utils
from ..SimulationEngine.custom_errors import InvalidInputError

def normalize_for_db(path_string):
    if path_string is None:
        return None
    # Remove any drive letter prefix first
    if len(path_string) > 2 and path_string[1:3] in [':/', ':\\']:
        path_string = path_string[2:]
    # Then normalize and convert slashes
    return os.path.normpath(path_string).replace("\\\\", "/")

def minimal_reset_db_for_delete_file(workspace_path_for_db=None):
    """Creates a fresh minimal DB state for testing, clearing and setting up root."""
    if workspace_path_for_db is None:
        workspace_path_for_db = tempfile.mkdtemp(prefix="test_delete_file_workspace_")
    
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


class TestDeleteFile(BaseTestCaseWithErrorHandler):
    """
    Test cases for the delete_file function, which removes file entries
    from the application's internal file system representation.
    """

    # Define potential transient filenames for cleanup, if needed.
    transient_test_files = (
        []
    )  # Add filenames if delete_file indirectly causes file creation

    def setUp(self):
        """
        Prepares a clean, isolated database state before each test method.
        Patches the DB object used by the application modules.
        """
        # Create temporary workspace and DB state
        self.workspace_path, self.db_for_test = minimal_reset_db_for_delete_file()
        
        # Patch 'DB' in the module where 'delete_file' is defined ('cursor.__init__')
        self.db_patcher_for_init_module = patch("cursor.DB", self.db_for_test)
        self.db_patcher_for_init_module.start()

        # Also patch 'DB' in the 'utils' module, in case delete_file calls utils
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

        # Create test files on the filesystem
        self.test_file_path = os.path.join(self.workspace_path, "file_to_delete.txt")
        self.test_dir_path = os.path.join(self.workspace_path, "a_directory")
        
        # Create the test file
        with open(self.test_file_path, 'w') as f:
            f.write("Test content")
        
        # Create the test directory
        os.makedirs(self.test_dir_path, exist_ok=True)
        
        # Add them to the DB
        self.db_for_test["file_system"][self.test_file_path] = {
            "path": self.test_file_path,
            "is_directory": False,
            "content_lines": ["Test content"],
            "size_bytes": 12,
            "last_modified": utils.get_current_timestamp_iso()
        }
        
        self.db_for_test["file_system"][self.test_dir_path] = {
            "path": self.test_dir_path,
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": utils.get_current_timestamp_iso()
        }

        self._cleanup_transient_files()

    def tearDown(self):
        """
        Restores the original state after each test method and cleans up transient files.
        """
        self._cleanup_transient_files()
        self.db_patcher_for_db_module.stop()
        self.db_patcher_for_cursorapi_module.stop()
        self.db_patcher_for_utils_module.stop()
        self.db_patcher_for_init_module.stop()
        
        # Clean up temporary workspace
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def _cleanup_transient_files(self):
        """Removes any specified transient files created during testing."""
        # Calculate cursor module directory robustly
        cursor_module_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for filename in self.transient_test_files:
            file_path = os.path.join(cursor_module_dir, filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    print(f"Warning: Could not clean up test file {file_path}: {e}")

    # --- Test Cases ---

    def test_invalid_target_file_type_raises_error(self):
        """Verify InvalidInputError is raised for non-string target_file."""
        with self.assertRaises(InvalidInputError):
            delete_file(target_file=12345)

    def test_invalid_explanation_type_raises_error(self):
        """Verify InvalidInputError is raised for non-string explanation."""
        with self.assertRaises(InvalidInputError):
            delete_file(target_file="file.txt", explanation=["invalid"])

    def test_delete_existing_file_succeeds(self):
        """Verify an existing file is deleted successfully."""
        result = delete_file(target_file="file_to_delete.txt")
        self.assertIn("deleted successfully", result.get("message", ""))
        self.assertNotIn("/test_ws/file_to_delete.txt", self.db_for_test["file_system"])

    def test_delete_nonexistent_file_is_idempotent(self):
        """Verify deleting a non-existent file returns a 'not found' message."""
        with self.assertRaises(FileNotFoundError):
            delete_file(target_file="nonexistent.txt")

    def test_delete_directory_raises_is_a_directory_error(self):
        """Verify attempting to delete a directory raises IsADirectoryError."""
        with self.assertRaises(IsADirectoryError):
            delete_file(target_file="a_directory")

    def test_delete_existing_file_success(self):
        """Verify successful deletion of an existing file."""
        # Create a README.md file in the temp workspace
        readme_path = os.path.join(self.workspace_path, "README.md")
        with open(readme_path, 'w') as f:
            f.write("# Test README")
        
        # Add to DB
        self.db_for_test["file_system"][readme_path] = {
            "path": readme_path, 
            "is_directory": False,
            "content_lines": ["# Test README"],
            "size_bytes": 13,
            "last_modified": utils.get_current_timestamp_iso()
        }
        
        # Ensure the file exists initially
        self.assertIn(readme_path, self.db_for_test["file_system"])

        result_dict = delete_file(target_file="README.md")

        self.assertIsInstance(result_dict, dict)
        self.assertTrue(result_dict.get("success"))
        self.assertIn("deleted successfully", result_dict.get("message", ""))
        self.assertEqual(result_dict.get("path_processed"), readme_path)
        # Verify the file is removed from the DB's file_system
        self.assertNotIn(readme_path, self.db_for_test["file_system"])

    def test_delete_nonexistent_file_idempotent_success(self):
        """Verify attempting to delete a non-existent file raises FileNotFoundError."""
        file_path_rel = "nonexistent.txt"
        file_path_abs = os.path.join(self.workspace_path, file_path_rel)
        with self.assertRaises(FileNotFoundError):
            delete_file(target_file=file_path_rel)


    def test_delete_target_is_directory_fails(self):
        """Verify attempting to delete a directory using delete_file raises IsADirectoryError."""
        dir_path_rel = "src"
        dir_path_abs = os.path.join(self.workspace_path, dir_path_rel)
        
        # Create the directory on filesystem
        os.makedirs(dir_path_abs, exist_ok=True)
        
        # Add to DB
        self.db_for_test["file_system"][dir_path_abs] = {
            "path": dir_path_abs, 
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": utils.get_current_timestamp_iso()
        }
        
        # Ensure the directory exists
        self.assertIn(dir_path_abs, self.db_for_test["file_system"])
        self.assertTrue(self.db_for_test["file_system"][dir_path_abs]["is_directory"])

        with self.assertRaises(IsADirectoryError) as cm:
            delete_file(target_file=dir_path_rel)

        self.assertIn("is a directory, not a file", str(cm.exception))

    def test_delete_empty_path_fails(self):
        """Verify attempting to delete with an empty target_file string raises ValueError."""
        with self.assertRaises(InvalidInputError) as cm:
            delete_file(target_file="")

        self.assertIn("cannot be empty", str(cm.exception))

    def test_delete_workspace_root_path_fails(self):
        """Verify attempting to delete the workspace root path raises ValueError."""
        # Test with path that resolves to root ('/' relative to root)
        with self.assertRaises(InvalidInputError) as cm:
            delete_file(target_file="/")

        self.assertIn("not a valid file path for deletion", str(cm.exception))

    def test_delete_path_outside_workspace_fails(self):
        """Verify attempting to delete a path outside the workspace raises ValueError."""
        self.db_for_test["workspace_root"] = "/home/user/project"

        with self.assertRaises(ValueError) as cm:
            delete_file(target_file="../../etc/passwd")

        self.assertIn("outside the permitted workspace", str(cm.exception))

    def test_delete_missing_workspace_root_fails(self):
        """Verify attempting delete raises ValueError if workspace_root is not configured."""
        if "workspace_root" in self.db_for_test:
            del self.db_for_test["workspace_root"]

        initial_fs_state = copy.deepcopy(self.db_for_test.get("file_system", {}))

        # Now raises WorkspaceNotHydratedError due to validation before ValueError
        from ..SimulationEngine.custom_errors import WorkspaceNotHydratedError
        with self.assertRaises(WorkspaceNotHydratedError) as cm:
            delete_file(target_file="some_file.txt")

        self.assertEqual(self.db_for_test.get("file_system", {}), initial_fs_state)

    def test_delete_clears_matching_last_edit_params(self):
        """Verify deleting the file referenced in last_edit_params clears it."""
        # Create src directory and main.py file in temp workspace
        src_dir = os.path.join(self.workspace_path, "src")
        os.makedirs(src_dir, exist_ok=True)
        
        file_to_delete_abs = os.path.join(src_dir, "main.py")
        file_to_delete_rel = "src/main.py"
        
        # Create the file on filesystem
        with open(file_to_delete_abs, 'w') as f:
            f.write("def main():\n    pass\n")
        
        # Add to DB
        self.db_for_test["file_system"][src_dir] = {
            "path": src_dir,
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": utils.get_current_timestamp_iso()
        }
        self.db_for_test["file_system"][file_to_delete_abs] = {
            "path": file_to_delete_abs, 
            "is_directory": False,
            "content_lines": ["def main():\n", "    pass\n"],
            "size_bytes": 20,
            "last_modified": utils.get_current_timestamp_iso()
        }
        
        # Ensure file exists
        self.assertIn(file_to_delete_abs, self.db_for_test["file_system"])
        # Setup last_edit_params to point to the file
        self.db_for_test["last_edit_params"] = {
            "target_file": file_to_delete_abs,
            "code_edit": "...",
            "instructions": "...",
            "explanation": "...",
        }

        result_dict = delete_file(target_file=file_to_delete_rel)

        self.assertIsInstance(result_dict, dict)
        self.assertTrue(result_dict.get("success"))
        self.assertIn("deleted successfully", result_dict.get("message", ""))
        self.assertEqual(result_dict.get("path_processed"), file_to_delete_abs)
        # Verify file is removed
        self.assertNotIn(file_to_delete_abs, self.db_for_test["file_system"])
        # Verify last_edit_params is cleared
        self.assertIsNone(self.db_for_test["last_edit_params"])

    def test_delete_does_not_clear_mismatched_last_edit_params(self):
        """Verify deleting a file doesn't clear last_edit_params if it references a different file."""
        # Create README.md file in temp workspace
        file_to_delete_abs = os.path.join(self.workspace_path, "README.md")
        file_to_delete_rel = "README.md"
        
        # Create src directory and main.py file in temp workspace
        src_dir = os.path.join(self.workspace_path, "src")
        os.makedirs(src_dir, exist_ok=True)
        other_file_abs = os.path.join(src_dir, "main.py")
        
        # Create the files on filesystem
        with open(file_to_delete_abs, 'w') as f:
            f.write("# README")
        with open(other_file_abs, 'w') as f:
            f.write("def main():\n    pass\n")
        
        # Add to DB
        self.db_for_test["file_system"][src_dir] = {
            "path": src_dir,
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": utils.get_current_timestamp_iso()
        }
        self.db_for_test["file_system"][file_to_delete_abs] = {
            "path": file_to_delete_abs, 
            "is_directory": False,
            "content_lines": ["# README"],
            "size_bytes": 8,
            "last_modified": utils.get_current_timestamp_iso()
        }
        self.db_for_test["file_system"][other_file_abs] = {
            "path": other_file_abs, 
            "is_directory": False,
            "content_lines": ["def main():\n", "    pass\n"],
            "size_bytes": 20,
            "last_modified": utils.get_current_timestamp_iso()
        }
        
        # Ensure files exist
        self.assertIn(file_to_delete_abs, self.db_for_test["file_system"])
        self.assertIn(other_file_abs, self.db_for_test["file_system"])
        # Setup last_edit_params to point to the *other* file
        original_last_edit = {
            "target_file": other_file_abs,
            "code_edit": "...",
            "instructions": "...",
            "explanation": "...",
        }
        self.db_for_test["last_edit_params"] = copy.deepcopy(original_last_edit)

        result_dict = delete_file(target_file=file_to_delete_rel)

        self.assertIsInstance(result_dict, dict)
        self.assertTrue(result_dict.get("success"))
        self.assertIn("deleted successfully", result_dict.get("message", ""))
        self.assertEqual(result_dict.get("path_processed"), file_to_delete_abs)
        # Verify target file is removed
        self.assertNotIn(file_to_delete_abs, self.db_for_test["file_system"])
        # Verify last_edit_params remains unchanged
        self.assertEqual(self.db_for_test["last_edit_params"], original_last_edit)

    def test_delete_with_explanation_argument(self):
        """Verify the optional explanation argument is accepted without altering behavior."""
        # Create config.cfg file in temp workspace
        file_path_abs = os.path.join(self.workspace_path, "config.cfg")
        file_path_rel = "config.cfg"
        
        # Create the file on filesystem
        with open(file_path_abs, 'w') as f:
            f.write("setting=value\n")
        
        # Add to DB
        self.db_for_test["file_system"][file_path_abs] = {
            "path": file_path_abs,
            "is_directory": False,
            "content_lines": ["setting=value\n"],
            "size_bytes": 14,
            "last_modified": utils.get_current_timestamp_iso()
        }
        
        self.assertIn(file_path_abs, self.db_for_test["file_system"])

        result_dict = delete_file(
            target_file=file_path_rel, explanation="Removing obsolete config."
        )

        self.assertIsInstance(result_dict, dict)
        self.assertTrue(result_dict.get("success"))
        self.assertIn("deleted successfully", result_dict.get("message", ""))
        self.assertEqual(result_dict.get("path_processed"), file_path_abs)
        self.assertNotIn(file_path_abs, self.db_for_test["file_system"])


if __name__ == "__main__":
    unittest.main()