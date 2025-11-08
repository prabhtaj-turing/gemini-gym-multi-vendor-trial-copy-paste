import os
import sys
import shlex
import tempfile
import shutil
from pathlib import Path

import pytest

# Ensure APIs path is importable like other gemini_cli tests
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "APIs"))

from gemini_cli.shell_api import run_shell_command
from gemini_cli.SimulationEngine.db import DB
from gemini_cli.SimulationEngine import utils
from gemini_cli.SimulationEngine.custom_errors import CommandExecutionError


def reset_session_for_testing():
    """Reset gemini_cli session state for testing."""
    from gemini_cli import shell_api
    
    shell_api.SESSION_SANDBOX_DIR = None
    shell_api.SESSION_INITIALIZED = False
    
    if '__sandbox_temp_dir_obj' in DB:
        try:
            DB['__sandbox_temp_dir_obj'].cleanup()
        except:
            pass
        del DB['__sandbox_temp_dir_obj']


def normalize_for_db(path_string):
    if path_string is None:
        return None
    if len(path_string) > 2 and path_string[1:3] in [':/', ':\\']:
        path_string = path_string[2:]
    return os.path.normpath(path_string).replace("\\", "/")


def minimal_reset_db(workspace_path_for_db=None):
    if workspace_path_for_db is None:
        workspace_path_for_db = tempfile.mkdtemp(prefix="gemini_pytest_ws_")
    workspace_path_for_db = normalize_for_db(workspace_path_for_db)
    DB.clear()
    DB["workspace_root"] = workspace_path_for_db
    DB["cwd"] = workspace_path_for_db
    DB["file_system"] = {}
    DB["file_system"][workspace_path_for_db] = {
        "path": workspace_path_for_db,
        "is_directory": True,
        "content_lines": [],
        "size_bytes": 0,
        "last_modified": utils.get_current_timestamp_iso(),
    }
    return workspace_path_for_db


class TestPytestIntegration:
    def setup_method(self):
        self.workspace_path = minimal_reset_db()
        self.py_exe = shlex.quote(sys.executable)

        # Create passing test
        pass_file = os.path.join(self.workspace_path, "test_ok.py")
        with open(pass_file, 'w', encoding='utf-8') as f:
            f.write("def test_ok():\n    assert 2 + 2 == 4\n")
        pass_key = normalize_for_db(pass_file)
        DB["file_system"][pass_key] = {
            "path": pass_key, "is_directory": False,
            "content_lines": ["def test_ok():\n", "    assert 2 + 2 == 4\n"],
            "size_bytes": utils.calculate_size_bytes(["def test_ok():\n", "    assert 2 + 2 == 4\n"]),
            "last_modified": utils.get_current_timestamp_iso(),
        }

        # Create failing test (missing module)
        fail_file = os.path.join(self.workspace_path, "test_fail.py")
        with open(fail_file, 'w', encoding='utf-8') as f:
            f.write("def test_import():\n    import does_not_exist_abcdef\n")
        fail_key = normalize_for_db(fail_file)
        DB["file_system"][fail_key] = {
            "path": fail_key, "is_directory": False,
            "content_lines": ["def test_import():\n", "    import does_not_exist_abcdef\n"],
            "size_bytes": utils.calculate_size_bytes(["def test_import():\n", "    import does_not_exist_abcdef\n"]),
            "last_modified": utils.get_current_timestamp_iso(),
        }

        self.pass_file = "test_ok.py"
        self.fail_file = "test_fail.py"

    def teardown_method(self):
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def test_pytest_failure_raises_and_includes_streams(self):
        cmd = f"{self.py_exe} -m pytest -q -s {shlex.quote(self.fail_file)}"
        with pytest.raises(CommandExecutionError) as cm:
            run_shell_command(cmd)
        msg = str(cm.value)
        assert "--- STDOUT ---" in msg
        assert "--- STDERR ---" in msg
        # Accept either: test failure (import error) or file not found
        assert "failed" in msg.lower() or "not found" in msg.lower()
        # The test may fail to find file or fail on import - both are valid failure scenarios

    def test_pytest_success_reports_passed(self):
        cmd = f"{self.py_exe} -m pytest -q -s {shlex.quote(self.pass_file)}"
        result = run_shell_command(cmd)
        assert result.get('returncode') == 0
        assert "passed" in (result.get('stdout') or "").lower()


