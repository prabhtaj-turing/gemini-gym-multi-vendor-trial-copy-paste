#!/usr/bin/env python3
"""
Coverage tests for terminal API focusing on PR-specific line ranges.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from terminal import terminalAPI
from terminal.SimulationEngine.db import DB
from terminal.SimulationEngine.custom_errors import CommandExecutionError


class TestTerminalApiCoverage(unittest.TestCase):
    """Tests for terminal API error paths and edge cases (PR coverage)."""

    def setUp(self):
        """Set up a clean DB and sandbox for each test."""
        from common_utils import session_manager
        
        self.original_db = DB.copy()
        self.original_sandbox_dir = terminalAPI.SESSION_SANDBOX_DIR
        self.original_initialized = terminalAPI.SESSION_INITIALIZED
        
        # Create a temporary directory that will serve as the workspace root
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace_root = self.temp_dir.name
        
        # Reset and configure the database for a clean state
        DB.clear()
        DB.update({
            "workspace_root": self.workspace_root,
            "cwd": self.workspace_root,
            "file_system": {
                self.workspace_root: {"is_directory": True, "path": self.workspace_root}
            },
        })
        
        # Ensure session state is reset
        terminalAPI.SESSION_SANDBOX_DIR = None
        terminalAPI.SESSION_INITIALIZED = False
        
        # CRITICAL: Reset the shared session state
        session_manager.reset_shared_session()

    def tearDown(self):
        """Clean up and restore original state after each test."""
        from common_utils import session_manager
        
        # End any active session and clean up its sandbox
        try:
            if terminalAPI.SESSION_INITIALIZED and terminalAPI.SESSION_SANDBOX_DIR:
                if os.path.exists(terminalAPI.SESSION_SANDBOX_DIR):
                    shutil.rmtree(terminalAPI.SESSION_SANDBOX_DIR, ignore_errors=True)
                terminalAPI.SESSION_INITIALIZED = False
                terminalAPI.SESSION_SANDBOX_DIR = None
        except:
            pass
        
        # CRITICAL: Reset the shared session state
        session_manager.reset_shared_session()
        
        # Clean up the temporary workspace directory
        self.temp_dir.cleanup()
        
        # Restore the original database state
        DB.clear()
        DB.update(self.original_db)
        
        # Restore session state
        terminalAPI.SESSION_SANDBOX_DIR = self.original_sandbox_dir
        terminalAPI.SESSION_INITIALIZED = self.original_initialized

    def test_end_session_no_active_session(self):
        """Test end_session when no session is active - Lines 70-71"""
        result = terminalAPI.end_session()
        self.assertTrue(result['success'])
        self.assertIn("No active session", result['message'])

    def test_end_session_workspace_root_not_set(self):
        """Test end_session when workspace_root is not set - Lines 90-91"""
        # Initialize a session first
        terminalAPI.run_command("pwd")
        
        # Clear workspace_root
        DB["workspace_root"] = ""
        
        result = terminalAPI.end_session()
        
        # Should skip filesystem sync but still succeed
        self.assertTrue(result['success'])

    def test_end_session_cleanup_error(self):
        """Test end_session error handling - Lines 105-110"""
        from common_utils import session_manager
        
        # Initialize a session
        terminalAPI.run_command("pwd")
        
        # Make cleanup fail by patching the shared session manager's temp dir object
        if session_manager._SHARED_SANDBOX_TEMP_DIR_OBJ:
            with patch.object(session_manager._SHARED_SANDBOX_TEMP_DIR_OBJ, 'cleanup', side_effect=OSError("Permission denied")):
                result = terminalAPI.end_session()
            
            # Should return error but still reset state
            self.assertFalse(result['success'])
            self.assertIn("Permission denied", result['message'])
            self.assertFalse(terminalAPI.SESSION_INITIALIZED)
            self.assertIsNone(terminalAPI.SESSION_SANDBOX_DIR)
        else:
            # Skip test if no temp dir object exists
            self.skipTest("No shared sandbox temp dir object to test cleanup error")

    def test_run_command_no_workspace_root(self):
        """Test run_command error when workspace_root not configured - Lines 203-204"""
        DB["workspace_root"] = None
        with self.assertRaisesRegex(ValueError, "workspace_root is not configured"):
            terminalAPI.run_command("ls")

    @patch('tempfile.TemporaryDirectory')
    def test_run_command_sandbox_init_failure(self, mock_tempdir):
        """Test run_command sandbox initialization failure - Lines 222-224"""
        mock_tempdir.side_effect = Exception("Disk full")
        with self.assertRaisesRegex(CommandExecutionError, "Failed to set up the execution environment"):
            terminalAPI.run_command("ls")

    def test_run_command_sandbox_not_initialized(self):
        """Test run_command when sandbox not initialized - Line 274"""
        # This is a difficult edge case to trigger since the function initializes
        # the sandbox automatically. We can test it by manually setting the state
        terminalAPI.SESSION_INITIALIZED = True
        terminalAPI.SESSION_SANDBOX_DIR = "/nonexistent/path"
        
        # Delete the sandbox directory to trigger reinitialization
        with patch('os.path.exists', return_value=False):
            # This should trigger reinitialization
            result = terminalAPI.run_command("pwd")
            self.assertTrue(result['returncode'] == 0)

    def test_db_to_sandbox_sync_directory_with_metadata(self):
        """Test DB-to-sandbox sync for directories with metadata - Lines 298-300"""
        # Add a directory with metadata to DB
        dir_path = os.path.join(self.workspace_root, "test_dir")
        DB["file_system"][dir_path] = {
            "path": dir_path,
            "is_directory": True,
            "content_lines": [],
            "metadata": {
                "timestamps": {
                    "access_time": "2024-01-01T00:00:00Z",
                    "modify_time": "2024-01-01T00:00:00Z",
                    "change_time": "2024-01-01T00:00:00Z"
                },
                "attributes": {
                    "is_symlink": False,
                    "is_hidden": False,
                    "is_readonly": False,
                    "symlink_target": None
                },
                "permissions": {
                    "mode": 0o755,
                    "uid": 1000,
                    "gid": 1000
                }
            }
        }
        
        # Run command that should sync this directory
        result = terminalAPI.run_command("ls test_dir")
        
        # Directory should be synced
        self.assertEqual(result['returncode'], 0)

    def test_db_to_sandbox_sync_file_with_parent_creation(self):
        """Test DB-to-sandbox sync creating parent directories - Line 305"""
        # Add a file in a nested directory that doesn't exist yet
        nested_file = os.path.join(self.workspace_root, "deep/nested/file.txt")
        DB["file_system"][nested_file] = {
            "path": nested_file,
            "is_directory": False,
            "content_lines": ["nested content\n"],
        }
        
        # Run command that should sync this file and create parent dirs
        result = terminalAPI.run_command("cat deep/nested/file.txt")
        
        # Should succeed and create parent directories
        self.assertEqual(result['returncode'], 0)
        self.assertIn("nested content", result['stdout'])

    def test_db_to_sandbox_sync_file_with_metadata(self):
        """Test DB-to-sandbox sync applying file metadata - Lines 315-316"""
        # Add a file with metadata to DB
        file_path = os.path.join(self.workspace_root, "meta_file.txt")
        DB["file_system"][file_path] = {
            "path": file_path,
            "is_directory": False,
            "content_lines": ["data\n"],
            "metadata": {
                "timestamps": {
                    "access_time": "2024-01-01T00:00:00Z",
                    "modify_time": "2024-01-01T00:00:00Z",
                    "change_time": "2024-01-01T00:00:00Z"
                },
                "attributes": {
                    "is_symlink": False,
                    "is_hidden": False,
                    "is_readonly": False,
                    "symlink_target": None
                },
                "permissions": {
                    "mode": 0o644,
                    "uid": 1000,
                    "gid": 1000
                }
            }
        }
        
        # Run command that should sync this file with metadata
        result = terminalAPI.run_command("cat meta_file.txt")
        
        # Should succeed
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(result['stdout'].strip(), "data")

    def test_run_command_emergency_restoration(self):
        """Test emergency state restoration on unexpected error - Line 530"""
        original_workspace_root = DB["workspace_root"]
        original_cwd = DB["cwd"]
        original_file_system = DB["file_system"].copy()
        
        # Force an unexpected error by running a failing command (non-policy exit)
        with self.assertRaises(CommandExecutionError):
            terminalAPI.run_command("bash -c 'exit 2'")
        
        # Verify state was restored
        self.assertEqual(DB["workspace_root"], original_workspace_root)
        self.assertEqual(DB["cwd"], original_cwd)
        # File system should be restored to original
        self.assertEqual(set(DB["file_system"].keys()), set(original_file_system.keys()))


if __name__ == '__main__':
    unittest.main()
