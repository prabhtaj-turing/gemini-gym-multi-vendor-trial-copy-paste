import json
import os
import platform
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

from claude_code import shell  # noqa: E402
from claude_code.SimulationEngine.db import DB  # noqa: E402
from claude_code.SimulationEngine.custom_errors import (
    InvalidInputError, 
    WorkspaceNotAvailableError, 
    CommandExecutionError
  )  # noqa: E402
from common_utils.base_case import BaseTestCaseWithErrorHandler  # noqa: E402

DB_JSON_PATH = Path(__file__).resolve().parents[3] / "DBs" / "ClaudeCodeDefaultDB.json"

# Fallback DB structure used when the default DB file doesn't exist
FALLBACK_DB_STRUCTURE = {
    "workspace_root": "/home/user/project",
    "cwd": "/home/user/project",
    "file_system": {},
    "memory_storage": {},
    "last_edit_params": None,
    "background_processes": {},
    "tool_metrics": {}
}


class TestShell(BaseTestCaseWithErrorHandler):
    """Test cases for the shell bash function."""

    def setUp(self):
        """Set up test database before each test."""
        DB.clear()
        if DB_JSON_PATH.exists():
            with open(DB_JSON_PATH, "r", encoding="utf-8") as fh:
                DB.update(json.load(fh))
        else:
            DB.update(FALLBACK_DB_STRUCTURE)

    def test_bash_basic_command(self):
        """Test basic shell command execution."""
        result = shell.bash(command="echo 'hello world'")
        self.assertEqual(result["returncode"], 0)
        self.assertIn("hello world", result["stdout"])
        self.assertEqual(result["command"], "echo 'hello world'")

    def test_bash_with_description(self):
        """Test bash command with description parameter."""
        result = shell.bash(
            command="ls",
            description="List directory contents"
        )
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["command"], "ls")

    def test_bash_with_directory(self):
        """Test bash command with specific directory."""
        result = shell.bash(
            command="pwd",
            directory="src"
        )
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["command"], "pwd")

    def test_bash_empty_command(self):
        """Test bash with empty command."""
        self.assert_error_behavior(
            func_to_call=shell.bash,
            expected_exception_type=InvalidInputError,
            expected_message="'command' cannot be empty",
            command=""
        )

    def test_bash_whitespace_command(self):
        """Test bash with whitespace-only command."""
        self.assert_error_behavior(
            func_to_call=shell.bash,
            expected_exception_type=InvalidInputError,
            expected_message="'command' cannot be empty",
            command="   "
        )

    def test_bash_non_string_command(self):
        """Test bash with non-string command."""
        self.assert_error_behavior(
            func_to_call=shell.bash,
            expected_exception_type=InvalidInputError,
            expected_message="'command' cannot be empty",
            command=123
        )

    def test_bash_workspace_not_available(self):
        """Test bash when workspace_root is not configured."""
        # Clear the workspace_root
        original_workspace_root = DB.get("workspace_root")
        DB.pop("workspace_root", None)

        self.assert_error_behavior(
            func_to_call=shell.bash,
            expected_exception_type=WorkspaceNotAvailableError,
            expected_message="workspace_root not configured in DB",
            command="echo test"
        )

        # Restore for other tests
        if original_workspace_root:
            DB["workspace_root"] = original_workspace_root

    def test_bash_command_not_found(self):
        """Test bash with command that doesn't exist."""
        # The bash function simulates successful execution, so this test
        # checks that it returns without raising an exception
        result = shell.bash(command="nonexistent_command_xyz_12345")
        self.assertIn("stdout", result)
        self.assertIn("stderr", result) 
        self.assertIn("returncode", result)
        self.assertEqual(result["returncode"], 127)  # Command not found

    def test_bash_background_parameter(self):
        """Test bash with background parameter."""
        result = shell.bash(
            command="echo background",
            background=True
        )
        # Background is not currently implemented, but should not error
        self.assertEqual(result["returncode"], 0)
        self.assertIn("background", result["stdout"])

    @patch('claude_code.SimulationEngine.file_utils._is_within_workspace')
    def test_bash_directory_outside_workspace(self, mock_is_within):
        """Test bash with directory outside workspace."""
        mock_is_within.return_value = False
        
        self.assert_error_behavior(
            func_to_call=shell.bash,
            expected_exception_type=InvalidInputError,
            expected_message="Directory is outside of the workspace",
            command="echo test",
            directory="../outside"
        )

    def test_bash_env_command(self):
        """Test bash with env command."""
        result = shell.bash(command="env")
        self.assertEqual(result["command"], "env")
        # Should be handled by handle_env_command
        self.assertIn("returncode", result)

    def test_bash_export_command(self):
        """Test bash with export command."""
        result = shell.bash(command="export TEST_VAR=value")
        self.assertEqual(result["command"], "export TEST_VAR=value")
        self.assertIn("returncode", result)

    def test_bash_unset_command(self):
        """Test bash with unset command."""
        result = shell.bash(command="unset TEST_VAR")
        self.assertEqual(result["command"], "unset TEST_VAR")
        self.assertIn("returncode", result)

    @patch('claude_code.shell.platform.system')
    @patch('claude_code.shell.subprocess.Popen')
    def test_bash_windows_platform(self, mock_popen, mock_platform):
        """Test bash command on Windows platform."""
        mock_platform.return_value = "Windows"
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = shell.bash(command="echo test")

        # Should use cmd.exe on Windows
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        self.assertEqual(args[0][:2], ["cmd.exe", "/c"])
        self.assertEqual(result["stdout"], "output")
        self.assertEqual(result["returncode"], 0)

    @patch('claude_code.shell.platform.system')
    @patch('claude_code.shell.subprocess.Popen')
    def test_bash_unix_platform(self, mock_popen, mock_platform):
        """Test bash command on Unix platform."""
        mock_platform.return_value = "Linux"
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = shell.bash(command="echo test")

        # Should use bash on Unix
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        self.assertEqual(args[0][:2], ["bash", "-c"])
        self.assertEqual(result["stdout"], "output")
        self.assertEqual(result["returncode"], 0)

    @patch('claude_code.shell.subprocess.Popen')
    def test_bash_file_not_found_error(self, mock_popen):
        """Test bash with FileNotFoundError."""
        mock_popen.side_effect = FileNotFoundError("Command not found")

        self.assert_error_behavior(
            func_to_call=shell.bash,
            expected_exception_type=CommandExecutionError,
            expected_message="Command not found: echo",
            command="echo test"
        )

    @patch('claude_code.shell.subprocess.Popen')
    def test_bash_timeout_error(self, mock_popen):
        """Test bash with timeout."""
        mock_process = MagicMock()
        mock_process.communicate.side_effect = subprocess.TimeoutExpired("cmd", 60)
        mock_process.kill.return_value = None
        # After kill, communicate should return normally
        mock_process.communicate.side_effect = [subprocess.TimeoutExpired("cmd", 60), ("", "timeout")]
        mock_popen.return_value = mock_process

        self.assert_error_behavior(
            func_to_call=shell.bash,
            expected_exception_type=CommandExecutionError,
            expected_message="Command timed out after 60 seconds",
            command="sleep 100"
        )

    @patch('claude_code.shell.subprocess.Popen')
    def test_bash_general_exception(self, mock_popen):
        """Test bash with general exception."""
        mock_popen.side_effect = Exception("Unexpected error")

        self.assert_error_behavior(
            func_to_call=shell.bash,
            expected_exception_type=CommandExecutionError,
            expected_message="An unexpected error occurred: Unexpected error",
            command="echo test"
        )

    @patch('claude_code.shell.os.path.exists')
    @patch('claude_code.shell.subprocess.Popen')
    def test_bash_nonexistent_directory(self, mock_popen, mock_exists):
        """Test bash with non-existent execution directory."""
        mock_exists.return_value = False
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = shell.bash(command="echo test", directory="nonexistent")

        # Should not set cwd if directory doesn't exist
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        self.assertNotIn("cwd", kwargs)
        self.assertEqual(result["stdout"], "output")

    @patch('claude_code.shell.os.path.exists')
    @patch('claude_code.shell.subprocess.Popen')
    def test_bash_existing_directory(self, mock_popen, mock_exists):
        """Test bash with existing execution directory."""
        mock_exists.return_value = True
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = shell.bash(command="echo test", directory="src")

        # Should set cwd if directory exists
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        self.assertIn("cwd", kwargs)
        self.assertEqual(result["stdout"], "output")

    @patch('claude_code.shell.expand_variables')
    @patch('claude_code.shell.subprocess.Popen')
    def test_bash_variable_expansion(self, mock_popen, mock_expand):
        """Test bash with variable expansion."""
        mock_expand.return_value = "echo expanded_value"
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("expanded_value", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = shell.bash(command="echo $TEST_VAR")

        # Should call expand_variables
        mock_expand.assert_called_once()
        self.assertEqual(result["stdout"], "expanded_value")

    @patch('claude_code.shell.prepare_command_environment')
    @patch('claude_code.shell.subprocess.Popen')
    def test_bash_environment_preparation(self, mock_popen, mock_prepare_env):
        """Test bash with environment preparation."""
        mock_prepare_env.return_value = {"TEST_VAR": "test_value"}
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        result = shell.bash(command="echo $TEST_VAR")

        # Should call prepare_command_environment
        mock_prepare_env.assert_called_once()
        # Should pass environment to subprocess
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        self.assertEqual(kwargs["env"], {"TEST_VAR": "test_value"})

    def test_bash_result_structure(self):
        """Test that bash result has all expected keys."""
        result = shell.bash(command="echo test")
        
        expected_keys = ["command", "directory", "stdout", "stderr", "returncode"]
        for key in expected_keys:
            self.assertIn(key, result)
        
        self.assertEqual(result["command"], "echo test")
        self.assertTrue(result["directory"].endswith("project"))

    def test_bash_stderr_capture(self):
        """Test that bash captures stderr."""
        # This command should produce stderr output
        result = shell.bash(command="echo 'error' >&2")
        
        self.assertIn("stderr", result)
        # stderr might be empty or contain the error message depending on shell behavior

    @patch('claude_code.shell.handle_env_command')
    def test_bash_env_command_delegation(self, mock_handle_env):
        """Test that env commands are properly delegated."""
        mock_handle_env.return_value = {"command": "env", "returncode": 0}
        
        result = shell.bash(command="env")
        
        mock_handle_env.assert_called_once_with("env", DB)
        self.assertEqual(result["returncode"], 0)

    @patch('claude_code.shell.handle_env_command')
    def test_bash_export_command_delegation(self, mock_handle_env):
        """Test that export commands are properly delegated."""
        mock_handle_env.return_value = {"command": "export TEST=value", "returncode": 0}
        
        result = shell.bash(command="export TEST=value")
        
        mock_handle_env.assert_called_once_with("export TEST=value", DB)
        self.assertEqual(result["returncode"], 0)

    @patch('claude_code.shell.handle_env_command')
    def test_bash_unset_command_delegation(self, mock_handle_env):
        """Test that unset commands are properly delegated."""
        mock_handle_env.return_value = {"command": "unset TEST", "returncode": 0}
        
        result = shell.bash(command="unset TEST")
        
        mock_handle_env.assert_called_once_with("unset TEST", DB)
        self.assertEqual(result["returncode"], 0)


if __name__ == "__main__":
    unittest.main()
