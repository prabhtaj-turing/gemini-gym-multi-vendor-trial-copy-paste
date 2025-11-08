import unittest
import os
import shutil
import logging
import tempfile
import subprocess
from unittest.mock import patch

# Assuming your project structure allows these imports
# You might need to adjust them based on your project's root and PYTHONPATH
from ..SimulationEngine.db import DB
from ..SimulationEngine import utils
from ..SimulationEngine import custom_errors

from .. import run_in_terminal
logger = logging.getLogger("copilot.command_line")

def minimal_reset_db(workspace_path: str):
    """Resets the in-memory DB to a clean state for each test, using a provided path."""
    DB.clear()
    # The provided path is already absolute and normalized from a temp directory
    workspace_path_for_db = utils._normalize_path_for_db(workspace_path)
    
    # Create the physical directory for the mock workspace. This is now in a temp location.
    os.makedirs(workspace_path_for_db, exist_ok=True)
    
    DB["workspace_root"] = workspace_path_for_db
    DB["cwd"] = workspace_path_for_db
    DB["environment"] = {
        "system": {},
        "workspace": {},
        "session": {}
    }
    DB["file_system"] = {
        workspace_path_for_db: {
            "path": workspace_path_for_db,
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": utils.get_current_timestamp_iso()
        }
    }
    DB["background_processes"] = {}
    DB["_next_pid"] = 1
    DB["last_edit_params"] = None

class TestRunInTerminal(unittest.TestCase):
    """
    A comprehensive test suite for the run_in_terminal function, covering core logic,
    internal commands, foreground execution, and background process launching.
    """

    @classmethod
    def setUpClass(cls):
        """Create a single temporary directory to be used as the base for all tests."""
        cls.base_temp_dir = tempfile.mkdtemp(prefix="copilot_test_runinterminal_")

    @classmethod
    def tearDownClass(cls):
        """Clean up the temporary directory after all tests in this class are done."""
        if os.path.exists(cls.base_temp_dir):
            shutil.rmtree(cls.base_temp_dir)

    def setUp(self):
        """Set up a clean database and a unique workspace for each test."""
        # Create a unique workspace path for each test to ensure isolation
        self.workspace_path = os.path.join(self.base_temp_dir, self.id())
        minimal_reset_db(self.workspace_path)
        self.workspace_root = DB["workspace_root"]

    def tearDown(self):
        """Clear the database and any leftover background process directories after each test."""
        # Clean up any background processes
        for pid, proc_info in list(DB.get("background_processes", {}).items()):
            if "exec_dir" in proc_info and os.path.exists(proc_info["exec_dir"]):
                shutil.rmtree(proc_info["exec_dir"], ignore_errors=True)
        
        # Clean up persistent session if it exists
        try:
            from common_utils import session_manager
            session_manager.end_shared_session(
                api_name="copilot",
                db_instance=DB,
                update_func=lambda temp_root, original_state, workspace_root, command: None,  # No-op update with correct signature
                normalize_path_func=utils._normalize_path_for_db
            )
        except Exception:
            pass  # Session may not have been initialized
        
        DB.clear()

    def _get_expected_path_key(self, relative_path: str) -> str:
        """Helper to get a normalized absolute path key for the DB."""
        return utils._normalize_path_for_db(os.path.join(self.workspace_root, relative_path))

    # --- Test Input Validation and Setup ---
    def test_empty_or_whitespace_command_string(self):
        """Test that empty or whitespace-only commands raise custom_errors.InvalidInputError."""
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "Command string cannot be empty"):
            run_in_terminal(command="   ")
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "Command string cannot be empty"):
            run_in_terminal(command="")

    # --- Test Type Validation ---
    def test_command_parameter_type_validation(self):
        """Test that command parameter must be a string type."""
        # Test with JSON object (dict)
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "Command parameter must be a string"):
            run_in_terminal(command={'cmd': 'ls', 'args': ['-la']}, is_background=False)
        
        # Test with list
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "Command parameter must be a string"):
            run_in_terminal(command=['echo', 'hello'], is_background=False)
        
        # Test with integer
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "Command parameter must be a string"):
            run_in_terminal(command=123, is_background=False)
        
        # Test with boolean
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "Command parameter must be a string"):
            run_in_terminal(command=True, is_background=False)
        
        # Test with None
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "Command parameter must be a string"):
            run_in_terminal(command=None, is_background=False)

    def test_is_background_parameter_type_validation(self):
        """Test that is_background parameter must be a boolean type."""
        # Test with string 'true' (should not be coerced)
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "is_background parameter must be a boolean"):
            run_in_terminal(command='echo test', is_background='true')
        
        # Test with string 'false' (should not be coerced)
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "is_background parameter must be a boolean"):
            run_in_terminal(command='echo test', is_background='false')
        
        # Test with string '1' (should not be coerced)
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "is_background parameter must be a boolean"):
            run_in_terminal(command='echo test', is_background='1')
        
        # Test with string '0' (should not be coerced)
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "is_background parameter must be a boolean"):
            run_in_terminal(command='echo test', is_background='0')
        
        # Test with integer 1 (should not be coerced)
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "is_background parameter must be a boolean"):
            run_in_terminal(command='echo test', is_background=1)
        
        # Test with integer 0 (should not be coerced)
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "is_background parameter must be a boolean"):
            run_in_terminal(command='echo test', is_background=0)
        
        # Test with list
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "is_background parameter must be a boolean"):
            run_in_terminal(command='echo test', is_background=[True])
        
        # Test with dict
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "is_background parameter must be a boolean"):
            run_in_terminal(command='echo test', is_background={'value': True})
        
        # Test with None
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "is_background parameter must be a boolean"):
            run_in_terminal(command='echo test', is_background=None)

    def test_valid_parameter_types(self):
        """Test that valid parameter types work correctly."""
        # Test with valid string command and boolean is_background
        result = run_in_terminal(command='echo "validation test"', is_background=False)
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('validation test', result['stdout'])
        
        # Test with valid string command and True boolean
        result = run_in_terminal(command='echo "background test"', is_background=True)
        self.assertIsNotNone(result['terminal_id'])
        self.assertIsNone(result['exit_code'])
        
        # Test with valid string command and False boolean (explicit)
        result = run_in_terminal(command='echo "explicit false"', is_background=False)
        self.assertEqual(result['exit_code'], 0)
        self.assertIn('explicit false', result['stdout'])

    def test_type_validation_error_messages(self):
        """Test that type validation error messages are descriptive."""
        # Test command parameter error message
        with self.assertRaises(custom_errors.InvalidInputError) as context:
            run_in_terminal(command={'invalid': 'type'}, is_background=False)
        self.assertIn("Command parameter must be a string", str(context.exception))
        self.assertIn("dict", str(context.exception))  # Should mention the actual type received
        
        # Test is_background parameter error message
        with self.assertRaises(custom_errors.InvalidInputError) as context:
            run_in_terminal(command='echo test', is_background='invalid')
        self.assertIn("is_background parameter must be a boolean", str(context.exception))
        self.assertIn("str", str(context.exception))  # Should mention the actual type received

    def test_workspace_root_not_configured(self):
        """Test that a missing workspace_root raises custom_errors.TerminalNotAvailableError."""
        DB.clear()
        with self.assertRaisesRegex(custom_errors.TerminalNotAvailableError, "Workspace root is not configured"):
            run_in_terminal(command="echo hello")
            
    # --- Test Internal 'cd' and 'pwd' Commands ---
    def test_internal_pwd_command(self):
        """Test the internal 'pwd' command."""
        result = run_in_terminal("pwd")
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(result['stdout'], self.workspace_root)

    def test_internal_cd_to_subdir(self):
        """Test the internal 'cd' command to a subdirectory."""
        subdir_path = self._get_expected_path_key("my_dir")
        DB['file_system'][subdir_path] = {"path": subdir_path, "is_directory": True, "content_lines": [], "size_bytes": 0, "last_modified": ""}
        
        result = run_in_terminal("cd my_dir")
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(DB['cwd'], subdir_path)
        
        pwd_result = run_in_terminal("pwd")
        self.assertEqual(pwd_result['stdout'], subdir_path)

    def test_internal_cd_to_parent(self):
        """Test the internal 'cd ..' command."""
        subdir_path = self._get_expected_path_key("my_dir")
        os.makedirs(subdir_path, exist_ok=True)
        DB['cwd'] = subdir_path
        result = run_in_terminal("cd ..")
        self.assertEqual(result['exit_code'], 0)
        self.assertEqual(DB['cwd'], self.workspace_root)

    def test_internal_cd_failure(self):
        """Test that 'cd' to a non-existent directory fails correctly."""
        with self.assertRaisesRegex(custom_errors.CommandExecutionError, "Failed to change directory"):
            run_in_terminal("cd non_existent_dir")

    # --- Test Error Handling and Mocking ---
    def test_command_shlex_split_error(self):
        """Test that a command with unclosed quotes is passed to bash (which will handle the error)."""
        # Note: We no longer pre-parse commands with shlex.split, so bash itself handles the error
        # This test verifies that such commands still execute and return a non-zero exit code
        result = run_in_terminal(command="echo 'unclosed quote")
        self.assertNotEqual(result['exit_code'], 0)  # Bash will return non-zero for syntax error

    @patch('common_utils.session_manager.tempfile.mkdtemp')
    def test_temp_dir_creation_permission_error(self, mock_mkdtemp):
        """Test that a PermissionError during temp dir creation is handled."""
        # Patch session_manager's mkdtemp call to raise PermissionError
        mock_mkdtemp.side_effect = PermissionError("Permission denied")
        with self.assertRaisesRegex(custom_errors.TerminalNotAvailableError, "Failed to set up the execution environment"):
            run_in_terminal(command="echo hello")

    @patch('subprocess.run')
    def test_foreground_command_timeout(self, mock_subprocess_run):
        """Test that a command timeout is handled correctly."""
        mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd="sleep 5", timeout=1)
        with self.assertRaisesRegex(custom_errors.CommandExecutionError, "timed out"):
            run_in_terminal(command="sleep 5")

    @patch('subprocess.run')
    def test_foreground_command_exception_restores_fs(self, mock_subprocess_run):
        """Test that the filesystem is restored after a generic command execution error."""
        file_path = self._get_expected_path_key('file.txt')
        DB['file_system'][file_path] = {"path": file_path, "is_directory": False, "content_lines": ["original"], "size_bytes": 8, "last_modified": ""}
        
        # Copy filesystem state BEFORE initializing sandbox (which may add sandbox dir to DB)
        # Run a simple command to initialize the session first
        run_in_terminal("echo test")
        
        # Now capture the state after initialization
        original_fs_copy = DB['file_system'].copy()
        mock_subprocess_run.side_effect = RuntimeError("mocked error")

        with self.assertRaisesRegex(custom_errors.CommandExecutionError, "mocked error"):
            run_in_terminal(command="some_failing_command")
        
        # Compare filesystem (excluding any sandbox-related entries that may have been added)
        # Just verify the original file is unchanged
        self.assertIn(file_path, DB["file_system"])
        self.assertEqual(DB["file_system"][file_path], original_fs_copy[file_path])

    def test_command_not_found_logs_warning(self):
        """Test that a warning is logged when a command is not found by the shell."""
        non_existent_cmd = "a_very_unique_and_non_existent_command_123xyz"
        with self.assertLogs(logger, level='WARNING') as log_watcher:
            result = run_in_terminal(command=non_existent_cmd)
        
        self.assertNotEqual(result['exit_code'], 0)
        # Check for the actual warning message format: "Command might not be found or other execution error"
        self.assertTrue(any("Command might not be found" in msg for msg in log_watcher.output))
        
    # --- Test Background Process Launching ---
    def test_background_launch_success(self):
        """Test the successful launch of a background process and its effect on the DB."""
        result = run_in_terminal("echo 'hello bg'", is_background=True)

        self.assertIsNotNone(result['terminal_id'])
        self.assertIsNone(result['exit_code'])
        self.assertIsNone(result['stdout'])
        self.assertIsNone(result['stderr'])
        self.assertEqual(len(DB['background_processes']), 1)
        
        pid = result['terminal_id']
        proc_info = DB['background_processes'][pid]
        self.assertEqual(proc_info['command'], "echo 'hello bg'")
        self.assertTrue(os.path.isdir(proc_info['exec_dir']))
        self.assertEqual(proc_info['last_stdout_pos'], 0)

    @patch('subprocess.Popen')
    def test_background_launch_failure_cleans_up(self, mock_popen):
        """Test that a failed background process launch handles errors correctly."""
        mock_popen.side_effect = OSError("Launch failed")
        
        # With session_manager, the sandbox is persistent and shared across calls
        # So we just verify that the error is raised and no process is left in DB
        with self.assertRaisesRegex(custom_errors.CommandExecutionError, "An unexpected error occurred: OSError - Launch failed"):
            run_in_terminal("some command", is_background=True)
        
        # Ensure no dangling process info was left in the DB
        self.assertEqual(len(DB['background_processes']), 0)

    def test_path_inheritance_from_parent_environment(self):
        """Test that subprocess inherits PATH from parent environment."""
        # This test verifies the fix for bug #1037
        result = run_in_terminal("echo $PATH")
        
        self.assertEqual(result['exit_code'], 0)
        self.assertIsNotNone(result['stdout'])
        # Verify that PATH is not empty and contains some expected directories
        path_output = result['stdout'].strip()
        self.assertNotEqual(path_output, "")
        self.assertIn("/bin", path_output)

    @patch.dict(os.environ, {
        'CONDA_PREFIX': '/opt/conda',
        'CONDA_DEFAULT_ENV': 'test-env',
        'CONDA_EXE': '/opt/conda/bin/conda',
        'PATH': '/opt/conda/bin:/usr/local/bin:/usr/bin'
    })
    def test_conda_environment_inheritance(self):
        """Test that CONDA environment variables are properly inherited."""
        # This test verifies the fix for bug #1037
        result = run_in_terminal("echo $CONDA_PREFIX")
        
        self.assertEqual(result['exit_code'], 0)
        self.assertIsNotNone(result['stdout'])
        # Verify that CONDA_PREFIX is inherited
        conda_prefix = result['stdout'].strip()
        self.assertEqual(conda_prefix, '/opt/conda')
        
        # Also verify PATH is inherited when CONDA is active
        result_path = run_in_terminal("echo $PATH")
        self.assertEqual(result_path['exit_code'], 0)
        self.assertIn('/opt/conda/bin', result_path['stdout'])

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)