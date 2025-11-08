import os
import shutil
import unittest
from unittest.mock import patch

from cursor.cursorAPI import run_terminal_cmd
from cursor.SimulationEngine import utils
from cursor import DB as GlobalDB


def _setup_minimal_db():
    ws = utils.get_common_directory() if utils.get_common_directory() else None
    if not ws:
        ws = os.path.expanduser("~/content/workspace")
        utils.update_common_directory(ws)
    GlobalDB["workspace_root"] = ws
    GlobalDB["cwd"] = ws
    if ws not in GlobalDB.get("file_system", {}):
        GlobalDB.setdefault("file_system", {})[ws] = {
            "path": ws,
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": utils.get_current_timestamp_iso(),
        }


class TestNonErrorExitCodes(unittest.TestCase):
    def setUp(self):
        _setup_minimal_db()
        # Ensure shared session ends between tests
        try:
            from common_utils import session_manager
            session_manager.reset_shared_session()
        except Exception:
            pass

    def tearDown(self):
        try:
            from common_utils import session_manager
            session_manager.reset_shared_session()
        except Exception:
            pass

    def test_grep_no_matches_exit1_treated_success(self):
        # grep returns 1 when no matches; should be treated as success by policy
        result = run_terminal_cmd("grep -R definitely_not_present .")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_diff_files_different_exit1_treated_success(self):
        # Create files inside sandbox via shell to avoid host FS coupling
        run_terminal_cmd("bash -lc 'printf A > a.txt; printf B > b.txt'")
        result = run_terminal_cmd("diff a.txt b.txt")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_cmp_files_different_exit1_treated_success(self):
        # Create files inside sandbox via shell
        run_terminal_cmd("bash -lc 'printf X > ca.bin; printf Y > cb.bin'")
        # We specifically want cmp's exit 1 scenario (files differ)
        result = run_terminal_cmd("cmp -s ca.bin cb.bin")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_test_command_false_exit1_treated_success(self):
        result = run_terminal_cmd("test -f ./nonexistent_file && echo yes || echo no; test -f ./nonexistent_file")
        # The last test returns 1; make sure policy accepts it
        result = run_terminal_cmd("test -f ./nonexistent_file")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_false_exit1_treated_success(self):
        # 'false' returns 1 by definition
        if shutil.which('false') is None:
            self.skipTest("false not available")
        result = run_terminal_cmd("false")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_which_not_found_exit1_treated_success(self):
        if shutil.which('which') is None:
            self.skipTest("which not available")
        result = run_terminal_cmd("which definitely_not_a_real_tool_12345")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_pgrep_no_match_exit1_treated_success(self):
        if shutil.which('pgrep') is None:
            self.skipTest("pgrep not available")
        # Use a more unique pattern that won't match the test process itself
        result = run_terminal_cmd("pgrep '^nonexistent_unique_process_name_xyz123$'")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_timeout_overshoot_exit124_treated_success(self):
        # Only run if timeout is available
        if shutil.which('timeout') is None or shutil.which('sleep') is None:
            self.skipTest("timeout or sleep not available")
        result = run_terminal_cmd("timeout 0.1 sleep 1")
        # GNU timeout returns 124 on timeout
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 124)

    def test_md5sum_verify_fail_exit1_treated_success(self):
        if shutil.which('md5sum') is None:
            self.skipTest("md5sum not available")
        # Create file and checksum in sandbox via shell (wrong checksum)
        # Use single-quoted outer command and escaped double quotes inside
        run_terminal_cmd('bash -lc "printf \"hello\\n\" > x.txt; printf \"00000000000000000000000000000000  x.txt\\n\" > x.txt.md5"')
        result = run_terminal_cmd("md5sum -c x.txt.md5")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_mountpoint_on_regular_dir_exit1_treated_success(self):
        if shutil.which('mountpoint') is None:
            self.skipTest("mountpoint not available")
        ws = GlobalDB["workspace_root"]
        d = os.path.join(ws, "not_a_mount")
        os.makedirs(d, exist_ok=True)
        result = run_terminal_cmd(f"mountpoint {d}")
        self.assertTrue(result.get("success"))
        self.assertIn(result.get("returncode"), (1, 32))

    def test_jq_false_filter_exit1_treated_success(self):
        if shutil.which('jq') is None:
            self.skipTest("jq not available")
        # jq -e returns 1 when filter is false/null
        result = run_terminal_cmd("printf '1' | jq -e false")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_ssh_keygen_F_not_found_exit1_treated_success(self):
        if shutil.which('ssh-keygen') is None:
            self.skipTest("ssh-keygen not available")
        # -f /dev/null forces an empty known_hosts, so -F won't find the host
        result = run_terminal_cmd("ssh-keygen -F definitelynotarealhost.example -f /dev/null")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_rpm_q_not_installed_exit1_treated_success(self):
        if shutil.which('rpm') is None:
            self.skipTest("rpm not available")
        result = run_terminal_cmd("rpm -q package_that_surely_does_not_exist_abc123")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_dpkg_s_not_installed_exit1_treated_success(self):
        if shutil.which('dpkg') is None:
            self.skipTest("dpkg not available")
        result = run_terminal_cmd("dpkg -s package_that_surely_does_not_exist_abc123")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_dpkg_query_W_not_installed_exit1_treated_success(self):
        if shutil.which('dpkg-query') is None:
            self.skipTest("dpkg-query not available")
        result = run_terminal_cmd("dpkg-query -W package_that_surely_does_not_exist_abc123")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_apk_info_e_not_installed_exit1_treated_success(self):
        if shutil.which('apk') is None:
            self.skipTest("apk not available")
        result = run_terminal_cmd("apk info -e package_that_surely_does_not_exist_abc123")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_pacman_Qi_not_installed_exit1_treated_success(self):
        if shutil.which('pacman') is None:
            self.skipTest("pacman not available")
        result = run_terminal_cmd("pacman -Qi package_that_surely_does_not_exist_abc123")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_pip_show_not_installed_exit1_treated_success(self):
        if shutil.which('pip') is None and shutil.which('pip3') is None:
            self.skipTest("pip/pip3 not available")
        tool = 'pip3' if shutil.which('pip3') else 'pip'
        result = run_terminal_cmd(f"{tool} show package_that_surely_does_not_exist_abc123")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_helm_status_unknown_release_exit1_treated_success(self):
        if shutil.which('helm') is None:
            self.skipTest("helm not available")
        result = run_terminal_cmd("helm status release_that_surely_does_not_exist_abc123")
        # Different helm versions may vary; we only assert success=True and non-zero return code
        self.assertTrue(result.get("success"))
        self.assertNotEqual(result.get("returncode"), 0)

    def test_nc_z_closed_port_exit1_treated_success(self):
        if shutil.which('nc') is None:
            self.skipTest("nc not available")
        # Use a likely-closed high port
        result = run_terminal_cmd("nc -z 127.0.0.1 59999")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_host_nonexistent_exit1_treated_success(self):
        if shutil.which('host') is None:
            self.skipTest("host not available")
        result = run_terminal_cmd("host definitelynotarealhost.example")
        self.assertTrue(result.get("success"))
        self.assertEqual(result.get("returncode"), 1)

    def test_systemctl_is_active_unknown_treated_success(self):
        if shutil.which('systemctl') is None:
            self.skipTest("systemctl not available")
        result = run_terminal_cmd("systemctl is-active service_that_surely_does_not_exist_abc123")
        self.assertTrue(result.get("success"))
        # Accept typical inactive/unknown codes per policy {1,3,4}
        self.assertIn(result.get("returncode"), (1, 3, 4))


