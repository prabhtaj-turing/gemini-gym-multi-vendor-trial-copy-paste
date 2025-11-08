import unittest
import os
import sys
import shlex
import tempfile
import shutil
import copy

from ..cursorAPI import run_terminal_cmd
from .. import DB
from ..SimulationEngine import utils
from ..SimulationEngine.custom_errors import CommandExecutionError
from ..SimulationEngine.db import reset_db
from .test_terminal_commands import reset_session_for_testing, minimal_reset_db_for_terminal_commands


def normalize_for_db(path_string):
    if path_string is None:
        return None
    if len(path_string) > 2 and path_string[1:3] in [':/', ':\\']:
        path_string = path_string[2:]
    return os.path.normpath(path_string).replace("\\", "/")


def minimal_reset_db_for_terminal_commands(workspace_path_for_db=None):
    if workspace_path_for_db is None:
        workspace_path_for_db = tempfile.mkdtemp(prefix="test_run_terminal_cmd_failures_workspace_")

    workspace_path_for_db = normalize_for_db(workspace_path_for_db)
    utils.update_common_directory(workspace_path_for_db)

    DB.clear()
    DB["workspace_root"] = workspace_path_for_db
    DB["cwd"] = workspace_path_for_db
    DB["file_system"] = {}
    DB["last_edit_params"] = None
    DB["background_processes"] = {}
    DB["_next_pid"] = 1

    DB["file_system"][workspace_path_for_db] = {
        "path": workspace_path_for_db,
        "is_directory": True,
        "content_lines": [],
        "size_bytes": 0,
        "last_modified": utils.get_current_timestamp_iso(),
    }

    return workspace_path_for_db


class TestRunTerminalCmdFailureOutputs(unittest.TestCase):
    def setUp(self):
        """Set up test database with clean state"""
        reset_db()
        
        self.workspace_path = minimal_reset_db_for_terminal_commands()
        # Require a bash-like shell for here-doc usage
        self.is_unix_shell = os.name != 'nt' or os.environ.get('SHELL', '').lower() in ('/bin/bash', 'bash', 'zsh', '/bin/zsh', 'sh', '/bin/sh')
        if not self.is_unix_shell:
            self.skipTest("These tests require a bash-like shell")

    def tearDown(self):
        """Clean up after tests"""
        reset_session_for_testing()
        reset_db()
        
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def test_includes_pytest_like_stdout_and_stderr_on_failure(self):
        stdout_sim = (
            "=========================== test session starts ===========================\n"
            "collected 1 item\n\n"
            "sample_test.py F\n\n"
            "=================================== FAILURES ===================================\n"
            "E   ModuleNotFoundError: No module named 'missing_dep'\n\n"
            "========================= 0 passed, 1 failed in 0.01s =========================\n"
        )
        stderr_sim = "ModuleNotFoundError: No module named 'missing_dep'\n"

        command = (
            'cat <<"PYOUT"\n' + stdout_sim + 'PYOUT\n' +
            '>&2 cat <<"PYERR"\n' + stderr_sim + 'PYERR\n' +
            'exit 1'
        )

        with self.assertRaises(CommandExecutionError) as cm:
            run_terminal_cmd(command=command, explanation="Simulate failing pytest output")
        msg = str(cm.exception)

        # Must include both streams and key pytest details verbatim
        self.assertIn("--- STDOUT ---", msg)
        self.assertIn("--- STDERR ---", msg)
        self.assertIn("0 passed, 1 failed", msg)
        self.assertIn("ModuleNotFoundError", msg)

    def test_no_rewrap_and_no_workspace_updated_phrase(self):
        stdout_sim = "sample_test.py F\n"
        stderr_sim = "ImportError: cannot import name 'X' from 'pkg'\n"

        command = (
            'cat <<"PYOUT"\n' + stdout_sim + 'PYOUT\n' +
            '>&2 cat <<"PYERR"\n' + stderr_sim + 'PYERR\n' +
            'exit 1'
        )

        with self.assertRaises(CommandExecutionError) as cm:
            run_terminal_cmd(command=command, explanation="Simulate stderr and stdout with failure")
        msg = str(cm.exception)

        # Ensure message isn't wrapped generically and doesn't claim state updates
        self.assertNotIn("Operation failed unexpectedly", msg)
        self.assertNotIn("Workspace state updated", msg)


class TestRunTerminalCmdPytestIntegration(unittest.TestCase):
    def setUp(self):
        """Set up test database with clean state"""
        reset_session_for_testing()  # Reset any existing session state
        reset_db()
        
        self.workspace_path = minimal_reset_db_for_terminal_commands()
        self.python_cmd = shlex.quote(sys.executable)

        # Create a passing pytest file (in-memory only, no physical file creation)
        pass_file = "test_ok_pytest.py"
        pass_content_lines = [
            "def test_ok():\n",
            "    assert 1 == 1\n",
        ]
        pass_key = normalize_for_db(os.path.join(DB["workspace_root"], pass_file))
        DB["file_system"][pass_key] = {
            "path": pass_key,
            "is_directory": False,
            "content_lines": pass_content_lines,
            "size_bytes": utils.calculate_size_bytes(pass_content_lines),
            "last_modified": utils.get_current_timestamp_iso(),
        }

        # Create a failing pytest file (missing dependency) (in-memory only, no physical file creation)
        fail_file = "test_fail_pytest.py"
        fail_content_lines = [
            "def test_import_error():\n",
            "    import does_not_exist_abcdefg\n",
        ]
        fail_key = normalize_for_db(os.path.join(DB["workspace_root"], fail_file))
        DB["file_system"][fail_key] = {
            "path": fail_key,
            "is_directory": False,
            "content_lines": fail_content_lines,
            "size_bytes": utils.calculate_size_bytes(fail_content_lines),
            "last_modified": utils.get_current_timestamp_iso(),
        }

        self.pass_file = pass_file
        self.fail_file = fail_file
        
        # Force synchronization of DB to physical sandbox
        # This ensures the test files are available in the physical sandbox
        from ..cursorAPI import SESSION_SANDBOX_DIR
        if SESSION_SANDBOX_DIR:
            utils.dehydrate_db_to_directory(DB, SESSION_SANDBOX_DIR)

    def tearDown(self):
        """Clean up after tests"""
        reset_session_for_testing()
        reset_db()
        
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def test_pytest_failure_includes_summary_and_trace(self):
        command = f"{self.python_cmd} -m pytest -q -s {shlex.quote(self.fail_file)}"
        with self.assertRaises(CommandExecutionError) as cm:
            run_terminal_cmd(command=command, explanation="Invoke pytest with failing test")
        msg = str(cm.exception)
        # Expect both sections, summary keywords, and import error presence
        self.assertIn("--- STDOUT ---", msg)
        self.assertIn("--- STDERR ---", msg)
        # Summary typically contains 'failed'
        self.assertIn("failed", msg.lower())
        self.assertTrue("does_not_exist_abcdefg" in msg)

    def test_pytest_success_reports_pass(self):
        command = f"{self.python_cmd} -m pytest -q -s {shlex.quote(self.pass_file)}"
        result = run_terminal_cmd(command=command, explanation="Invoke pytest with passing test")
        self.assertEqual(result.get('returncode'), 0)
        # With -q, stdout usually includes '1 passed'
        self.assertIn("passed", (result.get('stdout') or "").lower())

if __name__ == "__main__":
    unittest.main()


