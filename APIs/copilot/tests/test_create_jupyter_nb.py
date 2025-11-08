import os
import copy
import unittest

from .. import create_new_jupyter_notebook
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from ..SimulationEngine import utils
from common_utils.base_case import BaseTestCaseWithErrorHandler

class TestCreateNewJupyterNotebook(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB.update({
            "workspace_root": "/test_workspace",
            "cwd": "/test_workspace",
            "file_system": {},
            "jupyter_config": {
                "allow_creation": True,
                "environment_ok": True,
            },
            "_next_pid": 1,
        })
        self.mock_timestamp = "2023-01-01T12:00:00Z"
        DB["file_system"]["/test_workspace"] = {
            "path": "/test_workspace",
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": self.mock_timestamp,
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_create_notebook_successful_first_time(self):
        expected_filename = "Untitled.ipynb"
        expected_path = utils._normalize_path_for_db(os.path.join(DB["workspace_root"], expected_filename))
        result = create_new_jupyter_notebook()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["file_path"], expected_path)
        self.assertTrue(isinstance(result.get("message"), str) and len(result.get("message", "")) > 0)
        self.assertIn(expected_path, DB["file_system"])
        file_entry = DB["file_system"][expected_path]
        self.assertFalse(file_entry["is_directory"])
        self.assertEqual(file_entry["content_lines"], [line + '\n' for line in ''.join(file_entry["content_lines"]).splitlines()])
        self.assertEqual(file_entry["size_bytes"], sum(len(line.encode("utf-8")) for line in file_entry["content_lines"]))

    def test_create_notebook_successful_generates_unique_name(self):
        existing_file1_path = utils._normalize_path_for_db(os.path.join(DB["workspace_root"], "Untitled.ipynb"))
        existing_file2_path = utils._normalize_path_for_db(os.path.join(DB["workspace_root"], "Untitled-1.ipynb"))
        DB["file_system"][existing_file1_path] = {"path": existing_file1_path, "is_directory": False, "content_lines": [], "size_bytes": 0, "last_modified": "2022-01-01T00:00:00Z"}
        DB["file_system"][existing_file2_path] = {"path": existing_file2_path, "is_directory": False, "content_lines": [], "size_bytes": 0, "last_modified": "2022-01-01T00:00:00Z"}
        expected_filename = "Untitled-2.ipynb"
        expected_path = utils._normalize_path_for_db(os.path.join(DB["workspace_root"], expected_filename))
        result = create_new_jupyter_notebook()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["file_path"], expected_path)
        self.assertIn(expected_path, DB["file_system"])

    def test_file_creation_error_target_not_directory(self):
        # Make the target path point to a file instead of a directory
        file_path = utils._normalize_path_for_db(os.path.join(DB["workspace_root"], "test_file.txt"))
        DB["file_system"][file_path] = {
            "path": file_path,
            "is_directory": False,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": "2022-01-01T00:00:00Z"
        }
        DB["cwd"] = file_path
        self.assert_error_behavior(
            func_to_call=create_new_jupyter_notebook,
            expected_exception_type=custom_errors.FileCreationError,
            expected_message=f"Cannot create notebook: The target location '{file_path}' is not a directory."
        )

    def test_file_creation_error_invalid_path(self):
        # Set an invalid path that's outside the workspace
        DB["cwd"] = "/invalid/path"
        self.assert_error_behavior(
            func_to_call=create_new_jupyter_notebook,
            expected_exception_type=custom_errors.FileCreationError,
            expected_message="Cannot create notebook: Target directory path '/invalid/path' is invalid: Absolute path '/invalid/path' is outside the configured workspace root '/test_workspace'."
        )

    def test_file_creation_error_max_filename_attempts(self):
        # Simulate all possible names taken
        for i in range(1001):
            if i == 0:
                name = "Untitled.ipynb"
            else:
                name = f"Untitled-{i}.ipynb"
            path = utils._normalize_path_for_db(os.path.join(DB["workspace_root"], name))
            DB["file_system"][path] = {
                "path": path,
                "is_directory": False,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": "2022-01-01T00:00:00Z"
            }
        self.assert_error_behavior(
            func_to_call=create_new_jupyter_notebook,
            expected_exception_type=custom_errors.FileCreationError,
            expected_message=f"Could not determine a unique notebook name after 1000 attempts. Please check the directory '{DB['workspace_root']}'."
        )

    def test_jupyter_environment_error_workspace_root_missing(self):
        DB["workspace_root"] = None
        self.assert_error_behavior(
            func_to_call=create_new_jupyter_notebook,
            expected_exception_type=custom_errors.JupyterEnvironmentError,
            expected_message="Cannot create Jupyter Notebook: Workspace root is not configured."
        )

if __name__ == '__main__':
    unittest.main()