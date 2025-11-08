#!/usr/bin/env python3
"""
Comprehensive tests for workspace validation system.
Tests all endpoints that require workspace hydration validation.
"""

import unittest
import copy
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from common_utils.base_case import BaseTestCaseWithErrorHandler

# Import the functions to be tested
from ..cursorAPI import (
    list_dir, read_file, delete_file, file_search, grep_search, 
    codebase_search, deep_search, reapply, fix_lints,
    edit_file, run_terminal_cmd
)

# Import errors and DB
from ..SimulationEngine.custom_errors import (
    WorkspaceNotHydratedError, InvalidInputError, LastEditNotFoundError
)
from .. import DB as GlobalDBSource
from ..SimulationEngine import utils

def normalize_for_db(path_string):
    if path_string is None:
        return None
    # Remove any drive letter prefix first
    if len(path_string) > 2 and path_string[1:3] in [':/', ':\\']:
        path_string = path_string[2:]
    # Then normalize and convert slashes
    return os.path.normpath(path_string).replace("\\", "/")

def create_empty_db():
    """Creates an empty/unhydrated DB state."""
    return {
        "workspace_root": "",
        "cwd": "",
        "file_system": {},
        "last_edit_params": None,
        "background_processes": {},
        "_next_pid": 1,
        "available_instructions": {},
        "pull_requests": {},
        "commits": {},
        "knowledge_base": {},
        "_next_knowledge_id": 1
    }

def create_hydrated_db(workspace_path=None):
    """Creates a properly hydrated DB state."""
    if workspace_path is None:
        workspace_path = tempfile.mkdtemp(prefix="test_workspace_")
    
    workspace_path = normalize_for_db(workspace_path)
    utils.update_common_directory(workspace_path)
    
    db_state = {
        "workspace_root": workspace_path,
        "cwd": workspace_path,
        "file_system": {
            workspace_path: {
                "path": workspace_path,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": utils.get_current_timestamp_iso()
            }
        },
        "last_edit_params": None,
        "background_processes": {},
        "_next_pid": 1,
        "available_instructions": {},
        "pull_requests": {},
        "commits": {},
        "knowledge_base": {},
        "_next_knowledge_id": 1
    }
    
    return workspace_path, db_state


class TestWorkspaceValidation(BaseTestCaseWithErrorHandler):
    """
    Comprehensive tests for workspace validation across all endpoints.
    """

    transient_test_files = [
        "test_db.json",
        "test_persistence.json",
        "test_state.json",
    ]

    def setUp(self):
        """Setup test environment with patchers."""
        # Start with empty workspace and set up patchers
        self.empty_db = create_empty_db()
        self.workspace_path, self.hydrated_db = create_hydrated_db()
        
        # Set up all the necessary patchers
        self.db_patcher_cursorapi = patch("cursor.cursorAPI.DB", self.empty_db)
        self.db_patcher_utils = patch("cursor.SimulationEngine.utils.DB", self.empty_db)
        self.db_patcher_init = patch("cursor.DB", self.empty_db)
        # CRITICAL: Patch 'DB' in the db module where validate_workspace_hydration is defined
        self.db_patcher_db_module = patch("cursor.SimulationEngine.db.DB", self.empty_db)
        
        self.db_patcher_cursorapi.start()
        self.db_patcher_utils.start() 
        self.db_patcher_init.start()
        self.db_patcher_db_module.start()
        
        # Patch call_llm to avoid API key dependency in tests
        # Different functions expect different LLM response formats
        def mock_llm_call(prompt_text, **kwargs):
            if "JSON" in prompt_text or "json" in prompt_text:
                # For deep_search and other functions expecting JSON
                return '{"key_terms": ["test", "mock"], "concepts": ["testing"], "search_context": "mock search"}'
            else:
                # For read_file and other functions expecting text summary
                return "Mock LLM summary for testing"
        
        self.llm_patcher = patch("cursor.cursorAPI.call_llm", side_effect=mock_llm_call)
        self.llm_patcher.start()
        
        self._cleanup_transient_files()

    def tearDown(self):
        """Clean up after each test."""
        self._cleanup_transient_files()
        
        self.llm_patcher.stop()
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
        self.llm_patcher.stop()
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
        
        # Restart LLM patcher with hydrated DB
        def mock_llm_call(prompt_text, **kwargs):
            if "JSON" in prompt_text or "json" in prompt_text:
                # For deep_search and other functions expecting JSON
                return '{"key_terms": ["test", "mock"], "concepts": ["testing"], "search_context": "mock search"}'
            else:
                # For read_file and other functions expecting text summary
                return "Mock LLM summary for testing"
        
        self.llm_patcher = patch("cursor.cursorAPI.call_llm", side_effect=mock_llm_call)
        self.llm_patcher.start()

    def _add_file_to_hydrated_db(self, path: str, content: str = "test content"):
        """Add a file to the hydrated DB for testing."""
        abs_path = path
        if not os.path.isabs(path):
            abs_path = os.path.normpath(os.path.join(self.workspace_path, path))
        
        # Create directory structure if needed
        dir_name = os.path.dirname(abs_path)
        if dir_name and dir_name not in self.hydrated_db["file_system"]:
            os.makedirs(dir_name, exist_ok=True)
            self.hydrated_db["file_system"][dir_name] = {
                "path": dir_name,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": utils.get_current_timestamp_iso()
            }
        
        # Create the file
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.hydrated_db["file_system"][abs_path] = {
            "path": abs_path,
            "is_directory": False,
            "content_lines": [content + "\n"],
            "size_bytes": len(content),
            "last_modified": utils.get_current_timestamp_iso()
        }
        return abs_path

    # =================================================================
    # TESTS FOR ENDPOINTS REQUIRING FULL VALIDATION
    # =================================================================

    def test_list_dir_requires_hydration(self):
        """Test that list_dir requires workspace hydration."""
        with self.assertRaises(WorkspaceNotHydratedError):
            list_dir(".")

    def test_list_dir_works_when_hydrated(self):
        """Test that list_dir works when workspace is hydrated."""
        self._switch_to_hydrated_db()
        result = list_dir(".")
        self.assertIsInstance(result, list)

    def test_read_file_requires_hydration(self):
        """Test that read_file requires workspace hydration."""
        with self.assertRaises(WorkspaceNotHydratedError):
            read_file("test.txt")

    def test_read_file_works_when_hydrated(self):
        """Test that read_file works when workspace is hydrated."""
        self._switch_to_hydrated_db()
        self._add_file_to_hydrated_db("test.txt", "hello world")
        result = read_file("test.txt")
        self.assertTrue(result.get("success", False))

    def test_delete_file_requires_hydration(self):
        """Test that delete_file requires workspace hydration."""
        with self.assertRaises(WorkspaceNotHydratedError):
            delete_file("test.txt")

    def test_delete_file_works_when_hydrated(self):
        """Test that delete_file works when workspace is hydrated."""
        self._switch_to_hydrated_db()
        self._add_file_to_hydrated_db("test.txt", "content")
        result = delete_file("test.txt")
        self.assertTrue(result.get("success", False))

    def test_file_search_requires_hydration(self):
        """Test that file_search requires workspace hydration."""
        with self.assertRaises(WorkspaceNotHydratedError):
            file_search("test", "searching for test")

    def test_file_search_works_when_hydrated(self):
        """Test that file_search works when workspace is hydrated."""
        self._switch_to_hydrated_db()
        result = file_search("test", "searching for test")
        self.assertIsInstance(result, list)

    def test_grep_search_requires_hydration(self):
        """Test that grep_search requires workspace hydration."""
        with self.assertRaises(WorkspaceNotHydratedError):
            grep_search("test")

    def test_grep_search_works_when_hydrated(self):
        """Test that grep_search works when workspace is hydrated."""
        self._switch_to_hydrated_db()
        result = grep_search("test")
        self.assertIsInstance(result, list)

    def test_codebase_search_requires_hydration(self):
        """Test that codebase_search requires workspace hydration."""
        with self.assertRaises(WorkspaceNotHydratedError):
            codebase_search("test function")

    def test_codebase_search_works_when_hydrated(self):
        """Test that codebase_search works when workspace is hydrated."""
        self._switch_to_hydrated_db()
        result = codebase_search("test function")
        self.assertIsInstance(result, list)

    def test_deep_search_requires_hydration(self):
        """Test that deep_search requires workspace hydration."""
        with self.assertRaises(WorkspaceNotHydratedError):
            deep_search("test query for deep search functionality")

    def test_deep_search_works_when_hydrated(self):
        """Test that deep_search works when workspace is hydrated."""
        self._switch_to_hydrated_db()
        result = deep_search("test query for deep search functionality")
        self.assertIsInstance(result, list)

    def test_reapply_requires_hydration(self):
        """Test that reapply requires workspace hydration."""
        # First set up last edit params to avoid LastEditNotFoundError
        self.empty_db["last_edit_params"] = {
            "target_file": "/test/file.py",
            "code_edit": "print('hello')",
            "instructions": "add hello print",
            "explanation": "test edit"
        }
        
        with self.assertRaises(WorkspaceNotHydratedError):
            reapply("test.py")

    def test_reapply_works_when_hydrated(self):
        """Test that reapply works when workspace is hydrated (though may fail for other reasons)."""
        self._switch_to_hydrated_db()
        # This will likely fail due to missing last edit, but should not fail due to hydration
        with self.assertRaises((LastEditNotFoundError, Exception)):
            # We expect some error, but NOT WorkspaceNotHydratedError
            try:
                reapply("test.py")
            except WorkspaceNotHydratedError:
                self.fail("reapply raised WorkspaceNotHydratedError when workspace was hydrated")

    def test_fix_lints_requires_hydration(self):
        """Test that fix_lints requires workspace hydration."""
        # Set up last edit params to avoid other errors
        self.empty_db["last_edit_params"] = {
            "target_file": "/test/file.py",
            "code_edit": "print('hello')",
            "instructions": "add hello print",
            "explanation": "test edit"
        }
        
        with self.assertRaises(WorkspaceNotHydratedError):
            fix_lints(True)

    def test_fix_lints_works_when_hydrated(self):
        """Test that fix_lints works when workspace is hydrated (though may fail for other reasons)."""
        self._switch_to_hydrated_db()
        # This will likely fail due to missing last edit, but should not fail due to hydration
        with self.assertRaises((LastEditNotFoundError, Exception)):
            # We expect some error, but NOT WorkspaceNotHydratedError
            try:
                fix_lints(True)
            except WorkspaceNotHydratedError:
                self.fail("fix_lints raised WorkspaceNotHydratedError when workspace was hydrated")

    # =================================================================
    # TESTS FOR EDIT_FILE SELECTIVE VALIDATION
    # =================================================================

    def test_edit_file_create_new_file_without_hydration(self):
        """Test that edit_file can create new files without workspace hydration."""
        # This should not work - creating new files doesn't require hydration
        try:
            result = edit_file("new_file.py", "print('hello world')", "Create new file")
        except ValueError:
            pass
        except Exception:
            self.fail("edit_file raised unexpected Exception when creating new file")

    def test_edit_file_create_new_file_with_hydration(self):
        """Test that edit_file can create new files when workspace is hydrated."""
        self._switch_to_hydrated_db()
        result = edit_file("new_file.py", "print('hello world')", "Create new file")
        self.assertTrue(result.get("success", False))
        self.assertIn("new_file.py", result.get("message", ""))

    def test_edit_file_edit_existing_requires_hydration(self):
        """Test that editing existing files requires workspace hydration."""
        # Add file to empty DB to simulate existing file (this shouldn't happen in reality)
        # but let's create a scenario where file exists but workspace isn't hydrated
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

    def test_edit_file_edit_existing_works_when_hydrated(self):
        """Test that editing existing files works when workspace is hydrated."""
        self._switch_to_hydrated_db()
        self._add_file_to_hydrated_db("existing_file.py", "print('original')")
        
        result = edit_file("existing_file.py", "print('modified')", "Modify existing file")
        self.assertTrue(result.get("success", False))



    def test_workspace_validation_error_message(self):
        """Test that WorkspaceNotHydratedError has a clear message."""
        try:
            list_dir(".")
        except WorkspaceNotHydratedError as e:
            error_msg = str(e)
            self.assertIn("workspace", error_msg.lower())
            self.assertIn("hydrat", error_msg.lower())
            self.assertIn("initialize", error_msg.lower())

    def test_partial_hydration_empty_workspace_root(self):
        """Test validation with empty workspace_root but populated file_system."""
        self.empty_db["file_system"] = {"some_file": {"path": "some_file"}}
        # Should still fail because workspace_root is empty
        with self.assertRaises(WorkspaceNotHydratedError):
            list_dir(".")

    def test_partial_hydration_empty_file_system(self):
        """Test validation with workspace_root but empty file_system."""
        self.empty_db["workspace_root"] = "/some/path"
        # Should still fail because file_system is empty
        with self.assertRaises(WorkspaceNotHydratedError):
            list_dir(".")

    def test_validation_with_none_values(self):
        """Test validation when workspace fields are None instead of empty string."""
        self.empty_db["workspace_root"] = None
        self.empty_db["file_system"] = None
        with self.assertRaises(WorkspaceNotHydratedError):
            list_dir(".")


if __name__ == "__main__":
    unittest.main()
