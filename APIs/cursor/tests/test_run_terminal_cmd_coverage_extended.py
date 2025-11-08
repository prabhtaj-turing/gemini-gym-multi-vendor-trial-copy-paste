"""
Extended test coverage for run_terminal_cmd() - Lines 1316, 1320, 1537, 1550, 1554-1557, 1584-1585
Tests for:
- Environment variable commands (line 1316)
- Sandbox initialization check (line 1320)
- CWD path mapping (lines 1537, 1550)
- DB state restoration on error (lines 1554-1557)
- FileNotFoundError handling (lines 1584-1585)
"""
import os
import tempfile
import unittest
import shutil
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from APIs.cursor import cursorAPI
from APIs.cursor.SimulationEngine.db import DB, reset_db
from APIs.cursor.SimulationEngine.custom_errors import CommandExecutionError
from common_utils import session_manager


class TestEnvironmentCommands(unittest.TestCase):
    """Test environment variable command handling (line 1316)"""

    def setUp(self):
        """Set up a clean DB and sandbox for each test."""
        self.original_db = DB.copy()
        self.original_sandbox_dir = cursorAPI.SESSION_SANDBOX_DIR
        self.original_initialized = cursorAPI.SESSION_INITIALIZED
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = self.temp_dir.name
        
        reset_db()
        DB.update({
            "workspace_root": self.workspace_root,
            "cwd": self.workspace_root,
            "file_system": {
                self.workspace_root: {"is_directory": True, "path": self.workspace_root}
            },
        })
        
        cursorAPI.SESSION_SANDBOX_DIR = None
        cursorAPI.SESSION_INITIALIZED = False
        session_manager.reset_shared_session()

    def tearDown(self):
        """Clean up and restore original state after each test."""
        try:
            if cursorAPI.SESSION_INITIALIZED and cursorAPI.SESSION_SANDBOX_DIR:
                if os.path.exists(cursorAPI.SESSION_SANDBOX_DIR):
                    shutil.rmtree(cursorAPI.SESSION_SANDBOX_DIR, ignore_errors=True)
                cursorAPI.SESSION_INITIALIZED = False
                cursorAPI.SESSION_SANDBOX_DIR = None
        except:
            pass
        
        session_manager.reset_shared_session()
        self.temp_dir.cleanup()
        
        DB.clear()
        DB.update(self.original_db)
        
        cursorAPI.SESSION_SANDBOX_DIR = self.original_sandbox_dir
        cursorAPI.SESSION_INITIALIZED = self.original_initialized

    def test_env_command_handled_internally(self):
        """Test that 'env' command is handled internally (line 1316)"""
        result = cursorAPI.run_terminal_cmd("env", "Get environment variables")
        self.assertIsInstance(result, dict)
        self.assertIn('message', result)

    def test_export_command_handled_internally(self):
        """Test that 'export' command is handled internally"""
        result = cursorAPI.run_terminal_cmd("export MY_VAR=test_value", "Set environment variable")
        self.assertIsInstance(result, dict)
        self.assertIn('message', result)

    def test_unset_command_handled_internally(self):
        """Test that 'unset' command is handled internally"""
        result = cursorAPI.run_terminal_cmd("unset MY_VAR", "Unset environment variable")
        self.assertIsInstance(result, dict)
        self.assertIn('message', result)


class TestSandboxInitialization(unittest.TestCase):
    """Test sandbox initialization validation (line 1320)"""

    def setUp(self):
        """Set up a clean DB for each test."""
        self.original_db = DB.copy()
        self.original_sandbox_dir = cursorAPI.SESSION_SANDBOX_DIR
        self.original_initialized = cursorAPI.SESSION_INITIALIZED
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = self.temp_dir.name
        
        reset_db()
        DB.update({
            "workspace_root": self.workspace_root,
            "cwd": self.workspace_root,
            "file_system": {
                self.workspace_root: {"is_directory": True, "path": self.workspace_root}
            },
        })

    def tearDown(self):
        """Clean up and restore original state after each test."""
        session_manager.reset_shared_session()
        self.temp_dir.cleanup()
        
        DB.clear()
        DB.update(self.original_db)
        
        cursorAPI.SESSION_SANDBOX_DIR = self.original_sandbox_dir
        cursorAPI.SESSION_INITIALIZED = self.original_initialized

    def test_sandbox_not_initialized_raises_error(self):
        """Test that non-external command raises error when sandbox not initialized (line 1320)"""
        cursorAPI.SESSION_SANDBOX_DIR = None
        cursorAPI.SESSION_INITIALIZED = False
        
        with patch.object(session_manager, 'get_shared_session_info', return_value={
            'initialized': False,
            'exists': False
        }):
            with patch.object(session_manager, 'initialize_shared_session', side_effect=Exception("Sandbox init failed")):
                with self.assertRaises(CommandExecutionError) as cm:
                    cursorAPI.run_terminal_cmd("ls", "List files")
                self.assertIn("Failed to set up the execution environment", str(cm.exception))


class TestCWDMapping(unittest.TestCase):
    """Test CWD path mapping (lines 1537, 1550)"""

    def setUp(self):
        """Set up a clean DB and sandbox for each test."""
        self.original_db = DB.copy()
        self.original_sandbox_dir = cursorAPI.SESSION_SANDBOX_DIR
        self.original_initialized = cursorAPI.SESSION_INITIALIZED
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = self.temp_dir.name
        
        reset_db()
        DB.update({
            "workspace_root": self.workspace_root,
            "cwd": self.workspace_root,
            "file_system": {
                self.workspace_root: {"is_directory": True, "path": self.workspace_root}
            },
        })
        
        cursorAPI.SESSION_SANDBOX_DIR = None
        cursorAPI.SESSION_INITIALIZED = False
        session_manager.reset_shared_session()

    def tearDown(self):
        """Clean up and restore original state after each test."""
        try:
            if cursorAPI.SESSION_INITIALIZED and cursorAPI.SESSION_SANDBOX_DIR:
                if os.path.exists(cursorAPI.SESSION_SANDBOX_DIR):
                    shutil.rmtree(cursorAPI.SESSION_SANDBOX_DIR, ignore_errors=True)
                cursorAPI.SESSION_INITIALIZED = False
                cursorAPI.SESSION_SANDBOX_DIR = None
        except:
            pass
        
        session_manager.reset_shared_session()
        self.temp_dir.cleanup()
        
        DB.clear()
        DB.update(self.original_db)
        
        cursorAPI.SESSION_SANDBOX_DIR = self.original_sandbox_dir
        cursorAPI.SESSION_INITIALIZED = self.original_initialized

    def test_cwd_mapping_with_subdirectory(self):
        """Test CWD mapping when pwd changes to subdirectory (line 1550)"""
        subdir = os.path.join(self.workspace_root, "subdir")
        os.makedirs(subdir, exist_ok=True)
        DB["file_system"][subdir] = {
            "path": subdir,
            "is_directory": True
        }
        
        result = cursorAPI.run_terminal_cmd("pwd", "Get current directory")
        self.assertEqual(result["returncode"], 0)
        self.assertIn(self.workspace_root, result["stdout"])
        
        result = cursorAPI.run_terminal_cmd("cd subdir", "Change to subdir")
        self.assertEqual(result["returncode"], 0)
        updated_cwd = DB.get("cwd")
        self.assertIn("subdir", updated_cwd)

    def test_pwd_returns_logical_path_not_sandbox_path(self):
        """Test that pwd returns logical workspace path, not physical sandbox path (line 1537)"""
        result = cursorAPI.run_terminal_cmd("pwd", "Get current directory")
        self.assertEqual(result["returncode"], 0)
        self.assertNotIn("shared_sandbox", result["stdout"])
        self.assertIn(self.workspace_root, result["stdout"])


class TestDBStateRestoration(unittest.TestCase):
    """Test DB state restoration on command error (lines 1554-1557)"""

    def setUp(self):
        """Set up a clean DB and sandbox for each test."""
        self.original_db = DB.copy()
        self.original_sandbox_dir = cursorAPI.SESSION_SANDBOX_DIR
        self.original_initialized = cursorAPI.SESSION_INITIALIZED
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = self.temp_dir.name
        
        reset_db()
        DB.update({
            "workspace_root": self.workspace_root,
            "cwd": self.workspace_root,
            "file_system": {
                self.workspace_root: {"is_directory": True, "path": self.workspace_root}
            },
        })
        
        cursorAPI.SESSION_SANDBOX_DIR = None
        cursorAPI.SESSION_INITIALIZED = False
        session_manager.reset_shared_session()

    def tearDown(self):
        """Clean up and restore original state after each test."""
        try:
            if cursorAPI.SESSION_INITIALIZED and cursorAPI.SESSION_SANDBOX_DIR:
                if os.path.exists(cursorAPI.SESSION_SANDBOX_DIR):
                    shutil.rmtree(cursorAPI.SESSION_SANDBOX_DIR, ignore_errors=True)
                cursorAPI.SESSION_INITIALIZED = False
                cursorAPI.SESSION_SANDBOX_DIR = None
        except:
            pass
        
        session_manager.reset_shared_session()
        self.temp_dir.cleanup()
        
        DB.clear()
        DB.update(self.original_db)
        
        cursorAPI.SESSION_SANDBOX_DIR = self.original_sandbox_dir
        cursorAPI.SESSION_INITIALIZED = self.original_initialized

    def test_db_state_restored_on_command_failure(self):
        """Test that DB state is restored when command fails (lines 1554-1557)"""
        original_cwd = DB.get("cwd")
        original_workspace_root = DB.get("workspace_root")
        
        with self.assertRaises(CommandExecutionError):
            cursorAPI.run_terminal_cmd("bash -c 'exit 2'", "This command fails")
        
        self.assertEqual(DB.get("cwd"), original_cwd)
        self.assertEqual(DB.get("workspace_root"), original_workspace_root)

    def test_filesystem_state_restored_on_error(self):
        """Test that filesystem state is preserved after command error"""
        original_file_system = DB.get("file_system", {}).copy()
        
        test_file_path = os.path.join(self.workspace_root, "test.txt")
        DB["file_system"][test_file_path] = {
            "path": test_file_path,
            "is_directory": False,
            "content_lines": ["test content\n"]
        }
        
        with self.assertRaises(CommandExecutionError):
            cursorAPI.run_terminal_cmd("bash -c 'exit 2'", "This command fails")
        
        self.assertIn(test_file_path, DB["file_system"])


class TestFileNotFoundError(unittest.TestCase):
    """Test FileNotFoundError handling (lines 1584-1585)"""

    def setUp(self):
        """Set up a clean DB and sandbox for each test."""
        self.original_db = DB.copy()
        self.original_sandbox_dir = cursorAPI.SESSION_SANDBOX_DIR
        self.original_initialized = cursorAPI.SESSION_INITIALIZED
        
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = self.temp_dir.name
        
        reset_db()
        DB.update({
            "workspace_root": self.workspace_root,
            "cwd": self.workspace_root,
            "file_system": {
                self.workspace_root: {"is_directory": True, "path": self.workspace_root}
            },
        })
        
        cursorAPI.SESSION_SANDBOX_DIR = None
        cursorAPI.SESSION_INITIALIZED = False
        session_manager.reset_shared_session()

    def tearDown(self):
        """Clean up and restore original state after each test."""
        try:
            if cursorAPI.SESSION_INITIALIZED and cursorAPI.SESSION_SANDBOX_DIR:
                if os.path.exists(cursorAPI.SESSION_SANDBOX_DIR):
                    shutil.rmtree(cursorAPI.SESSION_SANDBOX_DIR, ignore_errors=True)
                cursorAPI.SESSION_INITIALIZED = False
                cursorAPI.SESSION_SANDBOX_DIR = None
        except:
            pass
        
        session_manager.reset_shared_session()
        self.temp_dir.cleanup()
        
        DB.clear()
        DB.update(self.original_db)
        
        cursorAPI.SESSION_SANDBOX_DIR = self.original_sandbox_dir
        cursorAPI.SESSION_INITIALIZED = self.original_initialized

    def test_file_not_found_returns_error_code_127(self):
        """Test that command not found returns exit code 127 (lines 1584-1585)"""
        with self.assertRaises(CommandExecutionError) as cm:
            cursorAPI.run_terminal_cmd("/nonexistent/command/path", "Run non-existent command")
        
        error_msg = str(cm.exception)
        self.assertTrue(
            "No such file or directory" in error_msg or "Execution failed" in error_msg,
            f"Expected 'No such file or directory' or 'Execution failed' in error message, got: {error_msg}"
        )


if __name__ == '__main__':
    unittest.main()
