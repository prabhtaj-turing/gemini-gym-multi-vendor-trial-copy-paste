#!/usr/bin/env python3
"""
Coverage tests for gemini_cli shell API focusing on PR-specific line ranges.
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from gemini_cli import shell_api
from gemini_cli.SimulationEngine.db import DB
from gemini_cli.SimulationEngine.custom_errors import CommandExecutionError


class TestShellApiCoverage(unittest.TestCase):
    """Tests for shell API error paths and edge cases (PR coverage)."""

    def setUp(self):
        """Set up a clean DB and sandbox for each test."""
        from common_utils import session_manager
        
        self.original_db = DB.copy()
        self.original_sandbox_dir = shell_api.SESSION_SANDBOX_DIR
        self.original_initialized = shell_api.SESSION_INITIALIZED
        
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
        shell_api.SESSION_SANDBOX_DIR = None
        shell_api.SESSION_INITIALIZED = False
        
        # CRITICAL: Reset the shared session state
        session_manager.reset_shared_session()

    def tearDown(self):
        """Clean up and restore original state after each test."""
        from common_utils import session_manager
        
        # End any active session and clean up its sandbox
        try:
            if shell_api.SESSION_INITIALIZED and shell_api.SESSION_SANDBOX_DIR:
                if os.path.exists(shell_api.SESSION_SANDBOX_DIR):
                    shutil.rmtree(shell_api.SESSION_SANDBOX_DIR, ignore_errors=True)
                shell_api.SESSION_INITIALIZED = False
                shell_api.SESSION_SANDBOX_DIR = None
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
        shell_api.SESSION_SANDBOX_DIR = self.original_sandbox_dir
        shell_api.SESSION_INITIALIZED = self.original_initialized

    def test_end_session_no_active_session(self):
        """Test end_session when no session is active - Lines 94-95"""
        result = shell_api.end_session()
        self.assertTrue(result['success'])
        self.assertIn("No active session", result['message'])

    def test_end_session_workspace_root_not_set(self):
        """Test end_session when workspace_root is not set - Lines 115-116"""
        # Initialize a session first
        shell_api.run_shell_command("pwd")
        
        # Clear workspace_root
        DB["workspace_root"] = ""
        
        result = shell_api.end_session()
        
        # Should skip filesystem sync but still succeed
        self.assertTrue(result['success'])

    def test_end_session_cleanup_error(self):
        """Test end_session error handling - Lines 131-136"""
        from common_utils import session_manager
        
        # Initialize a session
        shell_api.run_shell_command("pwd")
        
        # Make cleanup fail by patching the shared session manager's temp dir object
        # We need to patch the cleanup method of the actual temp dir object stored in session_manager
        if session_manager._SHARED_SANDBOX_TEMP_DIR_OBJ:
            with patch.object(session_manager._SHARED_SANDBOX_TEMP_DIR_OBJ, 'cleanup', side_effect=OSError("Permission denied")):
                result = shell_api.end_session()
            
            # Should return error but still reset state
            self.assertFalse(result['success'])
            self.assertIn("Permission denied", result['message'])
            self.assertFalse(shell_api.SESSION_INITIALIZED)
            self.assertIsNone(shell_api.SESSION_SANDBOX_DIR)
        else:
            # Skip test if no temp dir object exists
            self.skipTest("No shared sandbox temp dir object to test cleanup error")

    def test_db_to_sandbox_sync_file_with_parent_creation(self):
        """Test DB-to-sandbox sync creating parent directories - Line 403"""
        # Add a file in a nested directory that doesn't exist yet
        nested_file = os.path.join(self.workspace_root, "deep/nested/file.txt")
        DB["file_system"][nested_file] = {
            "path": nested_file,
            "is_directory": False,
            "content_lines": ["nested content\n"],
        }
        
        # Run command that should sync this file and create parent dirs
        result = shell_api.run_shell_command("cat deep/nested/file.txt", description="test")
        
        # Should succeed and create parent directories
        self.assertEqual(result['returncode'], 0)
        self.assertIn("nested content", result['stdout'])

    def test_run_shell_command_emergency_restoration(self):
        """Test emergency state restoration on unexpected error - Lines 646-647"""
        original_workspace_root = DB["workspace_root"]
        original_cwd = DB["cwd"]
        original_file_system = DB["file_system"].copy()
        
        # Force an unexpected error by running a failing command
        with self.assertRaises(CommandExecutionError):
            shell_api.run_shell_command("false", description="test")  # Command that returns non-zero
        
        # Verify state was restored
        self.assertEqual(DB["workspace_root"], original_workspace_root)
        self.assertEqual(DB["cwd"], original_cwd)
        # File system should be restored to original
        self.assertEqual(set(DB["file_system"].keys()), set(original_file_system.keys()))


if __name__ == '__main__':
    unittest.main()
