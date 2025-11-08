"""
Unit tests for session_manager module.

Tests the shared session management functionality that coordinates sandbox
state across cursor, gemini_cli, and terminal APIs.
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import MagicMock, patch

from .. import session_manager

class TestSessionManager(unittest.TestCase):
    """Test cases for session manager functions."""
    
    def setUp(self):
        """Reset session state before each test."""
        session_manager.reset_shared_session()
    
    def tearDown(self):
        """Clean up after each test."""
        session_manager.reset_shared_session()
    
    def test_get_shared_session_info_no_session(self):
        """Test get_shared_session_info when no session is active."""
        info = session_manager.get_shared_session_info()
        
        self.assertFalse(info['initialized'])
        self.assertIsNone(info['sandbox_dir'])
        self.assertIsNone(info['active_api'])
        self.assertFalse(info['exists'])
    
    def test_get_shared_session_info_active_session(self):
        """Test get_shared_session_info when session is active."""
        # Create a mock DB and dehydrate function
        mock_db = {"workspace_root": "/test", "cwd": "/test", "file_system": {}}
        
        def mock_dehydrate(db, target_dir):
            os.makedirs(target_dir, exist_ok=True)
        
        # Initialize a session
        sandbox_dir = session_manager.initialize_shared_session(
            api_name="test_api",
            workspace_root="/test",
            db_instance=mock_db,
            dehydrate_func=mock_dehydrate
        )
        
        # Check session info
        info = session_manager.get_shared_session_info()
        
        self.assertTrue(info['initialized'])
        self.assertEqual(info['sandbox_dir'], sandbox_dir)
        self.assertEqual(info['active_api'], "test_api")
        self.assertTrue(info['exists'])
        self.assertTrue(os.path.exists(sandbox_dir))
    
    def test_initialize_shared_session_creates_new(self):
        """Test initializing a new shared session."""
        mock_db = {"workspace_root": "/test", "cwd": "/test", "file_system": {}}
        
        def mock_dehydrate(db, target_dir):
            os.makedirs(target_dir, exist_ok=True)
            # Create a test file
            with open(os.path.join(target_dir, "test.txt"), "w") as f:
                f.write("test content")
        
        sandbox_dir = session_manager.initialize_shared_session(
            api_name="cursor",
            workspace_root="/test",
            db_instance=mock_db,
            dehydrate_func=mock_dehydrate
        )
        
        # Verify sandbox was created
        self.assertIsNotNone(sandbox_dir)
        self.assertTrue(os.path.exists(sandbox_dir))
        self.assertTrue(os.path.isdir(sandbox_dir))
        
        # Verify test file was created
        test_file = os.path.join(sandbox_dir, "test.txt")
        self.assertTrue(os.path.exists(test_file))
        
        # Verify shared state was updated
        self.assertEqual(session_manager.SHARED_SANDBOX_DIR, sandbox_dir)
        self.assertTrue(session_manager.SHARED_SESSION_INITIALIZED)
        self.assertEqual(session_manager.SHARED_ACTIVE_API, "cursor")
        self.assertIsNotNone(session_manager._SHARED_SANDBOX_TEMP_DIR_OBJ)
    
    def test_initialize_shared_session_reuses_existing(self):
        """Test that subsequent calls reuse the existing sandbox."""
        mock_db = {"workspace_root": "/test", "cwd": "/test", "file_system": {}}
        
        def mock_dehydrate(db, target_dir):
            os.makedirs(target_dir, exist_ok=True)
        
        # First API initializes
        sandbox_dir_1 = session_manager.initialize_shared_session(
            api_name="cursor",
            workspace_root="/test",
            db_instance=mock_db,
            dehydrate_func=mock_dehydrate
        )
        
        # Second API should reuse
        sandbox_dir_2 = session_manager.initialize_shared_session(
            api_name="gemini_cli",
            workspace_root="/test",
            db_instance=mock_db,
            dehydrate_func=mock_dehydrate
        )
        
        # Should be the same sandbox
        self.assertEqual(sandbox_dir_1, sandbox_dir_2)
        
        # Active API should still be the first one (creator)
        self.assertEqual(session_manager.SHARED_ACTIVE_API, "cursor")
    
    def test_initialize_shared_session_dehydrate_error(self):
        """Test error handling when dehydration fails."""
        mock_db = {"workspace_root": "/test", "cwd": "/test", "file_system": {}}
        
        def mock_dehydrate_fails(db, target_dir):
            raise RuntimeError("Dehydration failed!")
        
        with self.assertRaisesRegex(RuntimeError, "Failed to initialize shared sandbox"):
            session_manager.initialize_shared_session(
                api_name="cursor",
                workspace_root="/test",
                db_instance=mock_db,
                dehydrate_func=mock_dehydrate_fails
            )
        
        # State should not be set on failure
        self.assertIsNone(session_manager.SHARED_SANDBOX_DIR)
        self.assertFalse(session_manager.SHARED_SESSION_INITIALIZED)
    
    def test_end_shared_session_no_active(self):
        """Test ending session when no session is active."""
        mock_db = {"workspace_root": "/test"}
        
        def mock_update(temp_root, original_state, workspace_root, command):
            pass
        
        def mock_normalize(path):
            return path
        
        result = session_manager.end_shared_session(
            api_name="cursor",
            db_instance=mock_db,
            update_func=mock_update,
            normalize_path_func=mock_normalize
        )
        
        self.assertTrue(result['success'])
        self.assertIn("No active session", result['message'])
    
    def test_end_shared_session_success(self):
        """Test successful session cleanup."""
        mock_db = {"workspace_root": "/test", "cwd": "/test", "file_system": {}}
        
        def mock_dehydrate(db, target_dir):
            os.makedirs(target_dir, exist_ok=True)
        
        def mock_update(temp_root, original_state, workspace_root, command):
            pass
        
        def mock_normalize(path):
            return path
        
        # Initialize a session
        sandbox_dir = session_manager.initialize_shared_session(
            api_name="cursor",
            workspace_root="/test",
            db_instance=mock_db,
            dehydrate_func=mock_dehydrate
        )
        
        # Verify it exists
        self.assertTrue(os.path.exists(sandbox_dir))
        
        # End the session
        result = session_manager.end_shared_session(
            api_name="cursor",
            db_instance=mock_db,
            update_func=mock_update,
            normalize_path_func=mock_normalize
        )
        
        self.assertTrue(result['success'])
        self.assertIn("successfully", result['message'].lower())
        
        # Verify cleanup
        self.assertFalse(os.path.exists(sandbox_dir))
        self.assertIsNone(session_manager.SHARED_SANDBOX_DIR)
        self.assertFalse(session_manager.SHARED_SESSION_INITIALIZED)
        self.assertIsNone(session_manager.SHARED_ACTIVE_API)
    
    def test_end_shared_session_no_workspace_root(self):
        """Test end_session when workspace_root is not set."""
        mock_db = {}  # Missing workspace_root
        
        def mock_dehydrate(db, target_dir):
            os.makedirs(target_dir, exist_ok=True)
        
        def mock_update(temp_root, original_state, workspace_root, command):
            pass
        
        def mock_normalize(path):
            return path if path else ""
        
        # Initialize a session
        session_manager.initialize_shared_session(
            api_name="cursor",
            workspace_root="/test",
            db_instance={"workspace_root": "/test"},
            dehydrate_func=mock_dehydrate
        )
        
        # End with empty workspace_root
        result = session_manager.end_shared_session(
            api_name="cursor",
            db_instance=mock_db,
            update_func=mock_update,
            normalize_path_func=mock_normalize
        )
        
        # Should still succeed but skip filesystem sync
        self.assertTrue(result['success'])
    
    def test_end_shared_session_cleanup_error(self):
        """Test end_session error handling during cleanup."""
        mock_db = {"workspace_root": "/test", "cwd": "/test", "file_system": {}}
        
        def mock_dehydrate(db, target_dir):
            os.makedirs(target_dir, exist_ok=True)
        
        def mock_update(temp_root, original_state, workspace_root, command):
            pass
        
        def mock_normalize(path):
            return path
        
        # Initialize a session
        session_manager.initialize_shared_session(
            api_name="cursor",
            workspace_root="/test",
            db_instance=mock_db,
            dehydrate_func=mock_dehydrate
        )
        
        # Patch cleanup to fail
        with patch.object(session_manager._SHARED_SANDBOX_TEMP_DIR_OBJ, 'cleanup', side_effect=OSError("Permission denied")):
            result = session_manager.end_shared_session(
                api_name="cursor",
                db_instance=mock_db,
                update_func=mock_update,
                normalize_path_func=mock_normalize
            )
        
        # Should return error
        self.assertFalse(result['success'])
        self.assertIn("Permission denied", result['message'])
        
        # State should still be reset
        self.assertIsNone(session_manager.SHARED_SANDBOX_DIR)
        self.assertFalse(session_manager.SHARED_SESSION_INITIALIZED)
    
    def test_reset_shared_session(self):
        """Test forceful session reset."""
        mock_db = {"workspace_root": "/test", "cwd": "/test", "file_system": {}}
        
        def mock_dehydrate(db, target_dir):
            os.makedirs(target_dir, exist_ok=True)
        
        # Initialize a session
        sandbox_dir = session_manager.initialize_shared_session(
            api_name="cursor",
            workspace_root="/test",
            db_instance=mock_db,
            dehydrate_func=mock_dehydrate
        )
        
        # Verify session is active
        self.assertTrue(session_manager.SHARED_SESSION_INITIALIZED)
        self.assertTrue(os.path.exists(sandbox_dir))
        
        # Reset
        session_manager.reset_shared_session()
        
        # Verify reset
        self.assertIsNone(session_manager.SHARED_SANDBOX_DIR)
        self.assertFalse(session_manager.SHARED_SESSION_INITIALIZED)
        self.assertIsNone(session_manager.SHARED_ACTIVE_API)
        self.assertIsNone(session_manager._SHARED_SANDBOX_TEMP_DIR_OBJ)
        
        # Sandbox should be cleaned up
        self.assertFalse(os.path.exists(sandbox_dir))
    
    def test_multiple_api_coordination(self):
        """Test that multiple APIs can coordinate properly."""
        mock_db = {"workspace_root": "/test", "cwd": "/test", "file_system": {}}
        
        def mock_dehydrate(db, target_dir):
            os.makedirs(target_dir, exist_ok=True)
            # Create a marker file
            with open(os.path.join(target_dir, f"marker_{db.get('marker', 'none')}.txt"), "w") as f:
                f.write("test")
        
        # cursor API initializes
        mock_db['marker'] = 'cursor'
        sandbox_dir_cursor = session_manager.initialize_shared_session(
            api_name="cursor",
            workspace_root="/test",
            db_instance=mock_db,
            dehydrate_func=mock_dehydrate
        )
        
        # gemini_cli reuses
        mock_db['marker'] = 'gemini'
        sandbox_dir_gemini = session_manager.initialize_shared_session(
            api_name="gemini_cli",
            workspace_root="/test",
            db_instance=mock_db,
            dehydrate_func=mock_dehydrate
        )
        
        # terminal reuses
        mock_db['marker'] = 'terminal'
        sandbox_dir_terminal = session_manager.initialize_shared_session(
            api_name="terminal",
            workspace_root="/test",
            db_instance=mock_db,
            dehydrate_func=mock_dehydrate
        )
        
        # All should use the same sandbox
        self.assertEqual(sandbox_dir_cursor, sandbox_dir_gemini)
        self.assertEqual(sandbox_dir_gemini, sandbox_dir_terminal)
        
        # Only cursor's marker file should exist (dehydrate called only once)
        marker_cursor = os.path.join(sandbox_dir_cursor, "marker_cursor.txt")
        marker_gemini = os.path.join(sandbox_dir_cursor, "marker_gemini.txt")
        marker_terminal = os.path.join(sandbox_dir_cursor, "marker_terminal.txt")
        
        self.assertTrue(os.path.exists(marker_cursor))
        self.assertFalse(os.path.exists(marker_gemini))
        self.assertFalse(os.path.exists(marker_terminal))
        
        # Active API should be the creator (cursor)
        self.assertEqual(session_manager.SHARED_ACTIVE_API, "cursor")


if __name__ == '__main__':
    unittest.main()
