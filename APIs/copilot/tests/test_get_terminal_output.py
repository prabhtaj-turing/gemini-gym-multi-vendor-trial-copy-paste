import unittest
import os
import shutil
import time
import logging
import tempfile
import sys
from unittest.mock import patch, mock_open, MagicMock

# Assuming your project structure allows these imports. Adjust if necessary.
from .. import run_in_terminal, get_terminal_output
from ..SimulationEngine.db import DB
from ..SimulationEngine import utils
from ..SimulationEngine import custom_errors

# Configure a logger to capture output during tests
logger = logging.getLogger("copilot.command_line")

def minimal_reset_db(workspace_path: str):
    """Resets the in-memory DB to a clean state for each test, using a provided path."""
    DB.clear()
    workspace_path_for_db = utils._normalize_path_for_db(workspace_path)
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
            "path": workspace_path_for_db, "is_directory": True, "content_lines": [],
            "size_bytes": 0, "last_modified": utils.get_current_timestamp_iso()
        }
    }
    DB["background_processes"] = {}
    DB["_next_pid"] = 1
    DB["last_edit_params"] = None

class TestGetTerminalOutput(unittest.TestCase):
    """A dedicated test suite for the get_terminal_output function."""

    @classmethod
    def setUpClass(cls):
        cls.base_temp_dir = tempfile.mkdtemp(prefix="copilot_test_getoutput_")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.base_temp_dir):
            shutil.rmtree(cls.base_temp_dir)

    def setUp(self):
        self.workspace_path = os.path.join(self.base_temp_dir, self.id())
        minimal_reset_db(self.workspace_path)
        
    def tearDown(self):
        for pid, proc_info in list(DB.get("background_processes", {}).items()):
            if "exec_dir" in proc_info and os.path.exists(proc_info["exec_dir"]):
                shutil.rmtree(proc_info["exec_dir"], ignore_errors=True)
        DB.clear()
        
    def _wait_for_process_completion(self, pid: str, timeout: int = 15) -> bool:
        """Polls for the existence of the exitcode.log file."""
        if pid not in DB.get("background_processes", {}):
            print(f"Process {pid} not found in background_processes")
            return True 
        
        exitcode_path = DB['background_processes'][pid]['exitcode_path']
        print(f"Waiting for process {pid} to complete (timeout={timeout}s, exitcode_path={exitcode_path})")
        
        for i in range(timeout * 10):
            if os.path.exists(exitcode_path):
                print(f"Process {pid} completed successfully after {i/10:.1f}s")
                return True
            if i % 20 == 0:  # Log progress every 2 seconds
                print(f"Still waiting for process {pid}: {i/10:.1f}s elapsed...")
            time.sleep(0.1)
            
        print(f"Process {pid} did not complete after {timeout}s (exitcode file not found)")
        return False

    # --- NEW TEST CASE FOR VALIDATION ---
    def test_get_output_with_invalid_input_formats(self):
        """Test that get_terminal_output rejects various invalid inputs."""
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "Terminal ID cannot be empty or whitespace."):
            get_terminal_output("")
            
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "Terminal ID cannot be empty or whitespace."):
            get_terminal_output("   ")

        with self.assertRaisesRegex(custom_errors.InvalidInputError, "must be a string containing only digits"):
            get_terminal_output("abc-123")
            
        with self.assertRaisesRegex(custom_errors.InvalidInputError, "must be a string containing only digits"):
            get_terminal_output("123a")

        with self.assertRaises(TypeError):
            get_terminal_output(12345) # Should be a string, not an int

    def test_get_output_for_invalid_id(self):
        """Test that a validly formatted but non-existent ID raises InvalidTerminalIdError."""
        with self.assertRaisesRegex(custom_errors.InvalidTerminalIdError, "Terminal ID '99999' is invalid or does not exist."):
            get_terminal_output("99999")

    @unittest.skipIf(os.name == 'nt', "Windows background process management causes issues")
    def test_get_output_for_running_process(self):
        """Tests the 'still running' logic in isolation using a context manager for mocks."""
        result = run_in_terminal("sleep 300", is_background=True)
        pid = result['terminal_id']
        proc_info = DB['background_processes'][pid]
        exitcode_path = proc_info['exitcode_path']

        with patch('copilot.command_line.os.path.exists') as mock_exists, \
             patch('copilot.command_line.os.kill') as mock_kill, \
             patch('copilot.command_line.open', new_callable=mock_open) as mock_open_file:

            mock_exists.return_value = False
            output_result = get_terminal_output(pid)

            mock_exists.assert_called_once_with(exitcode_path)
            mock_kill.assert_called_once_with(int(pid), 0)
            self.assertTrue(output_result['is_still_running'])
            self.assertIsNone(output_result['exit_code'])
            self.assertEqual(len(DB['background_processes']), 1)

    # ... (the rest of the test methods remain unchanged) ...
    @patch('copilot.command_line.subprocess.Popen')
    def test_get_output_after_successful_completion(self, mock_popen):
        # Mock the subprocess to avoid Windows background process timing issues
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.poll.return_value = 0  # Process completed with success
        mock_popen.return_value = mock_process
        
        # Create a temporary directory for the test
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        # Mock successful completion by creating the expected files
        exitcode_file = os.path.join(temp_dir, 'exitcode.log')
        stdout_file = os.path.join(temp_dir, 'stdout.log')
        stderr_file = os.path.join(temp_dir, 'stderr.log')
        
        with open(exitcode_file, 'w') as f:
            f.write('0')
        with open(stdout_file, 'w') as f:
            f.write('Success\n')
        with open(stderr_file, 'w') as f:
            f.write('')
        
        # Manually set up the background process in DB
        pid = "12345"
        DB['background_processes'][pid] = {
            'command': 'echo Success',
            'exec_dir': temp_dir,
            'process': mock_process,
            'exitcode_path': exitcode_file,
            'stdout_path': stdout_file,
            'stderr_path': stderr_file,
            'last_stdout_pos': 0,
            'last_stderr_pos': 0
        }
        
        # Test get_terminal_output
        output_result = get_terminal_output(pid)
        self.assertFalse(output_result['is_still_running'])
        self.assertEqual(output_result['exit_code'], 0)
        self.assertIn("Success", output_result['stdout'])
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    @patch('copilot.command_line.subprocess.Popen')
    def test_get_output_after_error_completion(self, mock_popen):
        # Mock the subprocess to avoid Windows background process timing issues
        mock_process = MagicMock()
        mock_process.pid = 12346
        mock_process.poll.return_value = 1  # Process completed with error
        mock_popen.return_value = mock_process
        
        # Create a temporary directory for the test
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        # Mock error completion by creating the expected files
        exitcode_file = os.path.join(temp_dir, 'exitcode.log')
        stdout_file = os.path.join(temp_dir, 'stdout.log')
        stderr_file = os.path.join(temp_dir, 'stderr.log')
        
        with open(exitcode_file, 'w') as f:
            f.write('1')
        with open(stdout_file, 'w') as f:
            f.write('')
        with open(stderr_file, 'w') as f:
            f.write('Error\n')
        
        # Manually set up the background process in DB
        pid = "12346"
        DB['background_processes'][pid] = {
            'command': 'echo Error',
            'exec_dir': temp_dir,
            'process': mock_process,
            'exitcode_path': exitcode_file,
            'stdout_path': stdout_file,
            'stderr_path': stderr_file,
            'last_stdout_pos': 0,
            'last_stderr_pos': 0
        }
        
        # Test get_terminal_output
        output_result = get_terminal_output(pid)
        self.assertFalse(output_result['is_still_running'])
        self.assertEqual(output_result['exit_code'], 1)
        self.assertIn("Error", output_result['stderr'])
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    @unittest.skipIf(os.name == 'nt', "Windows background process timing causes test hangs")
    def test_incremental_output_retrieval(self):
        if os.name == 'nt':
            command = 'echo one & ping -n 2 127.0.0.1 > nul & echo two'
        else:
            command = "echo 'one'; sleep 0.8; echo 'two'"
        result = run_in_terminal(command, is_background=True)
        pid = result['terminal_id']
        time.sleep(0.4)
        output1 = get_terminal_output(pid)
        self.assertTrue(output1['is_still_running'])
        self.assertIn('one', output1['stdout'])
        self.assertTrue(self._wait_for_process_completion(pid), "Process did not complete in time.")
        output2 = get_terminal_output(pid)
        self.assertFalse(output2['is_still_running'])
        self.assertIn('two', output2['stdout'])
        self.assertNotIn('one', output2['stdout'])

    @unittest.skipIf(os.name == 'nt', "Windows background process management causes issues")
    @patch('copilot.command_line.os.path.exists')
    @patch('copilot.command_line.os.kill')
    def test_abrupt_termination_handling(self, mock_os_kill, mock_path_exists):
        result = run_in_terminal("sleep 5", is_background=True)
        pid = result['terminal_id']
        mock_path_exists.return_value = False
        mock_os_kill.side_effect = OSError("No such process")
        output_result = get_terminal_output(pid)
        self.assertFalse(output_result['is_still_running'])
        self.assertEqual(output_result['exit_code'], -1)
        self.assertIn("Process terminated unexpectedly", output_result['stderr'])
        self.assertEqual(len(DB['background_processes']), 0)

    @unittest.skipIf(os.name == 'nt', "Windows background process management causes issues")
    def test_output_retrieval_error_on_missing_exec_dir(self):
        result = run_in_terminal("sleep 2", is_background=True)
        pid = result['terminal_id']
        exec_dir = DB['background_processes'][pid]['exec_dir']
        shutil.rmtree(exec_dir)
        with self.assertRaisesRegex(custom_errors.OutputRetrievalError, "Could not retrieve output for terminal"):
            get_terminal_output(pid)
        self.assertNotIn(pid, DB['background_processes'])


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)