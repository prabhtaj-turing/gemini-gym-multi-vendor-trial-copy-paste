import unittest
import os
import sys
import shlex
import tempfile
import shutil

from .. import run_in_terminal
from ..SimulationEngine.db import DB
from ..SimulationEngine import utils


def normalize_for_db(path_string):
    if path_string is None:
        return None
    if len(path_string) > 2 and path_string[1:3] in [':/', ':\\']:
        path_string = path_string[2:]
    return os.path.normpath(path_string).replace("\\", "/")


def minimal_reset_db(workspace_path_for_db=None):
    DB.clear()
    if workspace_path_for_db is None:
        workspace_path_for_db = tempfile.mkdtemp(prefix="copilot_pytest_ws_")
    workspace_path_for_db = normalize_for_db(workspace_path_for_db)
    os.makedirs(workspace_path_for_db, exist_ok=True)
    DB["workspace_root"] = workspace_path_for_db
    DB["cwd"] = workspace_path_for_db
    DB["environment"] = {
        "system": {},
        "workspace": {},
        "session": {}
    }
    DB["file_system"] = {}
    DB["file_system"][workspace_path_for_db] = {
        "path": workspace_path_for_db,
        "is_directory": True,
        "content_lines": [],
        "size_bytes": 0,
        "last_modified": utils.get_current_timestamp_iso(),
    }
    return workspace_path_for_db


class TestPytestIntegrationCopilot(unittest.TestCase):
    def setUp(self):
        self.workspace_path = minimal_reset_db()
        self.py_exe = shlex.quote(sys.executable)

        pass_rel = "test_ok_copilot.py"
        fail_rel = "test_fail_copilot.py"

        pass_abs = os.path.join(self.workspace_path, pass_rel)
        with open(pass_abs, 'w', encoding='utf-8') as f:
            f.write("def test_ok():\n    assert 3 * 3 == 9\n")
        pass_key = normalize_for_db(pass_abs)
        DB["file_system"][pass_key] = {
            "path": pass_key, "is_directory": False,
            "content_lines": ["def test_ok():\n", "    assert 3 * 3 == 9\n"],
            "size_bytes": utils.calculate_size_bytes(["def test_ok():\n", "    assert 3 * 3 == 9\n"]),
            "last_modified": utils.get_current_timestamp_iso(),
        }

        fail_abs = os.path.join(self.workspace_path, fail_rel)
        with open(fail_abs, 'w', encoding='utf-8') as f:
            f.write("def test_import():\n    import does_not_exist_copilot\n")
        fail_key = normalize_for_db(fail_abs)
        DB["file_system"][fail_key] = {
            "path": fail_key, "is_directory": False,
            "content_lines": ["def test_import():\n", "    import does_not_exist_copilot\n"],
            "size_bytes": utils.calculate_size_bytes(["def test_import():\n", "    import does_not_exist_copilot\n"]),
            "last_modified": utils.get_current_timestamp_iso(),
        }

        self.pass_file = pass_rel
        self.fail_file = fail_rel

    def tearDown(self):
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path, ignore_errors=True)

    def test_pytest_failure_returns_streams(self):
        cmd = f"{self.py_exe} -m pytest -q -s {shlex.quote(self.fail_file)}"
        result = run_in_terminal(cmd)
        self.assertNotEqual(result.get('exit_code'), 0)
        self.assertIn("failed", (result.get('stdout') or "").lower())
        self.assertIn("does_not_exist_copilot", (result.get('stdout') or "") + (result.get('stderr') or ""))

    def test_pytest_success_reports_pass(self):
        cmd = f"{self.py_exe} -m pytest -q -s {shlex.quote(self.pass_file)}"
        result = run_in_terminal(cmd)
        self.assertEqual(result.get('exit_code'), 0)
        self.assertIn("passed", (result.get('stdout') or "").lower())


