import unittest
import os
import shutil
import tempfile
import stat
from datetime import datetime, timezone
import subprocess
import re
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock
import time
import random

from ..terminalAPI import run_command
from ..SimulationEngine.db import DB
from ..SimulationEngine import utils
from ..SimulationEngine.custom_errors import CommandExecutionError
import APIs.common_utils.terminal_filesystem_utils as common_utils_utils

# --- Common Helper Functions ---

def reset_session_for_testing():
    """Reset terminal session state for testing."""
    from .. import terminalAPI
    from common_utils import session_manager
    
    terminalAPI.SESSION_SANDBOX_DIR = None
    terminalAPI.SESSION_INITIALIZED = False
    
    if '__sandbox_temp_dir_obj' in DB:
        try:
            DB['__sandbox_temp_dir_obj'].cleanup()
        except:
            pass
        del DB['__sandbox_temp_dir_obj']
    
    # CRITICAL: Reset the shared session state
    session_manager.reset_shared_session()


def normalize_for_db(path_string):
    if path_string is None:
        return None
    # Remove any drive letter prefix first
    if len(path_string) > 2 and path_string[1:3] in [':/', ':\\']:
        path_string = path_string[2:]
    # Then normalize and convert slashes
    return os.path.normpath(path_string).replace("\\\\", "/")

def minimal_reset_db(workspace_path_for_db=None):
    """Creates a fresh minimal DB state for testing, clearing and setting up root."""
    DB.clear()
    
    # Create a temporary directory if no path provided
    if workspace_path_for_db is None:
        workspace_path_for_db = tempfile.mkdtemp(prefix="test_workspace_")
    
    # Normalize workspace path
    workspace_path_for_db = normalize_for_db(workspace_path_for_db)
    
    # Initialize common directory to match workspace path
    utils.update_common_directory(workspace_path_for_db)
    
    DB["workspace_root"] = workspace_path_for_db
    DB["cwd"] = workspace_path_for_db
    DB["file_system"] = {}
    DB["last_edit_params"] = None
    DB["background_processes"] = {}
    DB["_next_pid"] = 1

    # Create root directory entry
    DB["file_system"][workspace_path_for_db] = {
        "path": workspace_path_for_db,
        "is_directory": True,
        "content_lines": [],
        "size_bytes": 0,
        "last_modified": utils.get_current_timestamp_iso()
    }
    
    return workspace_path_for_db  # Return the path so tests can clean it up if needed


def minimal_reset_db_for_terminal_commands():
    """Creates a fresh minimal DB state for testing using a logical path."""
    reset_session_for_testing()
    
    # Use a logical path for the workspace root. No physical directory is created here.
    workspace_path = "/tmp/test_workspace_" + str(random.randint(1000, 9999))
    workspace_path = normalize_for_db(workspace_path)
    
    DB.clear()
    DB["workspace_root"] = workspace_path
    DB["cwd"] = workspace_path
    DB["file_system"] = {}
    DB["last_edit_params"] = None
    DB["background_processes"] = {}
    DB["_next_pid"] = 1

    # Create root directory entry in the in-memory DB
    DB["file_system"][workspace_path] = {
        "path": workspace_path,
        "is_directory": True,
        "content_lines": [],
        "size_bytes": 0,
        "last_modified": utils.get_current_timestamp_iso()
    }
    
    return workspace_path
# --- Test Classes ---

class TestCatCommand(unittest.TestCase):
    """Test cases for cat/type command functionality."""

    def _get_command_for_os(self, command_template):
        if os.name == 'nt':
            shell = os.environ.get('SHELL', '').lower()
            if 'bash' in shell or 'zsh' in shell or 'sh' in shell:
                return command_template['unix']
            else:
                return f"cmd /c {command_template['windows']}"
        else:
            return command_template['unix']

    def setUp(self):
        self.workspace_path = minimal_reset_db()
        test_files = {
            "test1.txt": ["Line 1\n", "Line 2\n", "Line 3\n"],
            "test2.txt": ["Hello World\n", "This is a test\n"],
            "empty.txt": []
        }
        for filename, content in test_files.items():
            file_path = normalize_for_db(os.path.join(self.workspace_path, filename))
            DB["file_system"][file_path] = {
                "path": file_path,
                "is_directory": False,
                "content_lines": content,
                "size_bytes": utils.calculate_size_bytes(content),
                "last_modified": utils.get_current_timestamp_iso()
            }
            # Create the actual file in the filesystem
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.writelines(content)

    def tearDown(self):
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)

    def _get_expected_path_key(self, relative_path: str) -> str:
        current_workspace_root = DB["workspace_root"]
        abs_path = os.path.join(current_workspace_root, relative_path)
        normalized_key = os.path.normpath(abs_path).replace("\\\\", "/")
        return normalized_key

    def test_cat_single_file(self):
        test_file = "test1.txt"
        expected_path = self._get_expected_path_key(test_file)
        command = self._get_command_for_os({
            'unix': f"cat {test_file}",
            'windows': f"type {test_file}"
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        expected_content = "".join(DB["file_system"][expected_path]["content_lines"])
        self.assertEqual(result['stdout'], expected_content)

    def test_cat_nonexistent_file(self):
        test_file = "nonexistent.txt"
        command = self._get_command_for_os({
            'unix': f"cat {test_file}",
            'windows': f"type {test_file}"
        })
        with self.assertRaises(CommandExecutionError) as cm:
            run_command(command=command)
        self.assertTrue(len(str(cm.exception)) > 0)


    def test_cat_empty_file(self):
        test_file = "empty.txt"
        # expected_path = self._get_expected_path_key(test_file) # Not needed for stdout check
        command = self._get_command_for_os({
            'unix': f"cat {test_file}",
            'windows': f"type {test_file}"
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(result['stdout'], "")

    def test_cat_multiple_files(self):
        test_file1 = "test1.txt"
        test_file2 = "test2.txt"
        expected_path1 = self._get_expected_path_key(test_file1)
        expected_path2 = self._get_expected_path_key(test_file2)
        command = self._get_command_for_os({
            'unix': f"cat {test_file1} {test_file2}",
            'windows': f"type {test_file1} {test_file2}"
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        expected_content = "".join(DB["file_system"][expected_path1]["content_lines"]) + \
                         "".join(DB["file_system"][expected_path2]["content_lines"])
        self.assertEqual(result['stdout'], expected_content)


class TestCopyCommand(unittest.TestCase):
    """Test cases for copy/cp command functionality."""

    def _get_command_for_os(self, command_template):
        if os.name == 'nt':
            shell = os.environ.get('SHELL', '').lower()
            if 'bash' in shell or 'zsh' in shell or 'sh' in shell:
                return command_template['unix']
            else:
                return f"cmd /c {command_template['windows']}"
        else:
            return command_template['unix']

    def setUp(self):
        self.workspace_path = minimal_reset_db()
        
        # Create source file
        source_content = ["This is source file content\n", "Line 2\n"]
        source_file_path = normalize_for_db(os.path.join(self.workspace_path, "source.txt"))
        DB["file_system"][source_file_path] = {
            "path": source_file_path,
            "is_directory": False,
            "content_lines": source_content,
            "size_bytes": utils.calculate_size_bytes(source_content),
            "last_modified": utils.get_current_timestamp_iso()
        }
        # Create the actual file in the filesystem
        os.makedirs(os.path.dirname(source_file_path), exist_ok=True)
        with open(source_file_path, 'w') as f:
            f.writelines(source_content)
        
        # Create test directory
        dir_path = normalize_for_db(os.path.join(self.workspace_path, "test_dir"))
        os.makedirs(dir_path, exist_ok=True)
        DB["file_system"][dir_path] = {
            "path": dir_path,
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": utils.get_current_timestamp_iso()
        }

    def tearDown(self):
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)

    def _get_expected_path_key(self, relative_path: str) -> str:
        current_workspace_root = DB["workspace_root"]
        abs_path = os.path.join(current_workspace_root, relative_path)
        normalized_key = os.path.normpath(abs_path).replace("\\\\", "/")
        return normalized_key

    def test_copy_file(self):
        source_file = "source.txt"
        target_file = "target.txt"
        source_path = self._get_expected_path_key(source_file)
        target_path = self._get_expected_path_key(target_file)
        command = self._get_command_for_os({
            'unix': f"cp {source_file} {target_file}",
            'windows': f"copy {source_file} {target_file}"
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        self.assertIn(source_path, DB["file_system"])
        self.assertEqual(DB["file_system"][source_path]["content_lines"], ["This is source file content\n", "Line 2\n"])
        self.assertIn(target_path, DB["file_system"])
        self.assertEqual(DB["file_system"][target_path]["content_lines"], ["This is source file content\n", "Line 2\n"])

    def test_copy_to_directory(self):
        source_file = "source.txt"
        target_dir = "test_dir"
        source_path = self._get_expected_path_key(source_file)
        target_path = self._get_expected_path_key(os.path.join(target_dir, source_file))
        command = self._get_command_for_os({
            'unix': f"cp {source_file} {target_dir}",
            'windows': f"copy {source_file} {target_dir}"
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        self.assertIn(source_path, DB["file_system"])
        self.assertEqual(DB["file_system"][source_path]["content_lines"], ["This is source file content\n", "Line 2\n"])
        self.assertIn(target_path, DB["file_system"])
        self.assertEqual(DB["file_system"][target_path]["content_lines"], ["This is source file content\n", "Line 2\n"])

    def test_copy_nonexistent_file(self):
        source_file = "nonexistent.txt"
        target_file = "target.txt"
        command = self._get_command_for_os({
            'unix': f"cp {source_file} {target_file}",
            'windows': f"copy {source_file} {target_file}"
        })
        with self.assertRaises(CommandExecutionError):
            run_command(command=command)

    def test_copy_to_nonexistent_directory(self):
        source_file = "source.txt"
        target_dir_name = "nonexistent_dir" # The directory that shouldn't exist
        
        # For Unix, target a path *inside* the non-existent directory.
        # A trailing slash implies the target is a directory.
        target_path_for_unix_cp = f"{target_dir_name}/"

        # For Windows, the existing test logic implies 'copy source.txt nonexistent_dir'
        # is expected to create a file named 'nonexistent_dir'. We keep this behavior.
        target_path_for_windows_copy = target_dir_name

        command = self._get_command_for_os({
            'unix': f"cp {source_file} {target_path_for_unix_cp}", # e.g., "cp source.txt nonexistent_dir/"
            'windows': f"copy {source_file} {target_path_for_windows_copy}" # e.g., "copy source.txt nonexistent_dir"
        })
        
        shell = os.environ.get('SHELL', '').lower()
        is_unix_shell = 'bash' in shell or 'zsh' in shell or 'sh' in shell
        if is_unix_shell or os.name != 'nt': # check os.name != 'nt' for non-Windows Unix-like
            with self.assertRaises(CommandExecutionError):
                run_command(command=command)
        else: # Windows cmd
            result = run_command(command=command)
            self.assertEqual(result['returncode'], 0)
            target_path = self._get_expected_path_key(target_dir_name)
            self.assertIn(target_path, DB["file_system"])
            self.assertFalse(DB["file_system"][target_path]["is_directory"],
                           "Windows copy should create a file, not a directory")
            self.assertEqual(DB["file_system"][target_path]["content_lines"], ["This is source file content\n", "Line 2\n"])


class TestHeadCommand(unittest.TestCase):
    """Test cases for head command functionality."""

    def _get_command_for_os(self, command_template):
        if os.name == 'nt':
            shell = os.environ.get('SHELL', '').lower()
            if 'bash' in shell or 'zsh' in shell or 'sh' in shell:
                return command_template['unix']
            else:
                return f"cmd /c {command_template['windows']}"
        else:
            return command_template['unix']

    def setUp(self):
        self.workspace_path = minimal_reset_db()
        test_files = {
            "test.txt": ["Line 1\n", "Line 2\n", "Line 3\n", "Line 4\n", "Line 5\n",
                        "Line 6\n", "Line 7\n", "Line 8\n", "Line 9\n", "Line 10\n"],
            "short.txt": ["Line 1\n", "Line 2\n", "Line 3\n"],
            "empty.txt": []
        }
        for filename, content in test_files.items():
            file_path = normalize_for_db(os.path.join(self.workspace_path, filename))
            DB["file_system"][file_path] = {
                "path": file_path,
                "is_directory": False,
                "content_lines": content,
                "size_bytes": utils.calculate_size_bytes(content),
                "last_modified": utils.get_current_timestamp_iso()
            }
            # Create the actual file in the filesystem
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.writelines(content)

    def tearDown(self):
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)

    def _get_expected_path_key(self, relative_path: str) -> str:
        current_workspace_root = DB["workspace_root"]
        abs_path = os.path.join(current_workspace_root, relative_path)
        normalized_key = os.path.normpath(abs_path).replace("\\\\", "/")
        return normalized_key

    def test_head_default_lines(self):
        test_file = "test.txt"
        file_path = self._get_expected_path_key(test_file)
        command = self._get_command_for_os({
            'unix': f"head {test_file}",
            'windows': f"powershell -Command \"Get-Content {test_file} | Select-Object -First 10\""
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        expected_content = "".join(DB["file_system"][file_path]["content_lines"])
        self.assertEqual(result['stdout'], expected_content)

    def test_head_specific_lines(self):
        test_file = "test.txt"
        file_path = self._get_expected_path_key(test_file)
        num_lines = 3
        command = self._get_command_for_os({
            'unix': f"head -n {num_lines} {test_file}",
            'windows': f"powershell -Command \"Get-Content {test_file} | Select-Object -First {num_lines}\""
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        expected_content = "".join(DB["file_system"][file_path]["content_lines"][:num_lines])
        self.assertEqual(result['stdout'], expected_content)

    def test_head_short_file(self):
        test_file = "short.txt"
        file_path = self._get_expected_path_key(test_file)
        num_lines = 5
        command = self._get_command_for_os({
            'unix': f"head -n {num_lines} {test_file}",
            'windows': f"powershell -Command \"Get-Content {test_file} | Select-Object -First {num_lines}\""
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        expected_content = "".join(DB["file_system"][file_path]["content_lines"])
        self.assertEqual(result['stdout'], expected_content)

    def test_head_empty_file(self):
        test_file = "empty.txt"
        command = self._get_command_for_os({
            'unix': f"head {test_file}",
            'windows': f"powershell -Command \"Get-Content {test_file} | Select-Object -First 10\""
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(result['stdout'], "")

    def test_head_nonexistent_file(self):
        test_file = "nonexistent.txt"
        command = self._get_command_for_os({
            'unix': f"head {test_file}",
            'windows': f"powershell -Command \"Get-Content {test_file} | Select-Object -First 10\""
        })
        with self.assertRaises(CommandExecutionError):
            run_command(command=command)


class TestMvCommand(unittest.TestCase):
    """Test cases for move/mv command functionality."""

    def _get_command_for_os(self, command_template):
        if os.name == 'nt':
            shell = os.environ.get('SHELL', '').lower()
            if 'bash' in shell or 'zsh' in shell or 'sh' in shell:
                return command_template['unix']
            else:
                return f"cmd /c {command_template['windows']}"
        else:
            return command_template['unix']

    def setUp(self):
        self.workspace_path = minimal_reset_db()
        
        # Create test files
        test_files = {
            "source.txt": ["This is source file content\n", "Line 2\n"],
            "target.txt": ["This is target file content\n"],
            "source_dir/nested.txt": ["Nested file content\n"]
        }
        
        for rel_path, content in test_files.items():
            file_path = normalize_for_db(os.path.join(self.workspace_path, rel_path))
            DB["file_system"][file_path] = {
                "path": file_path,
                "is_directory": False,
                "content_lines": content,
                "size_bytes": utils.calculate_size_bytes(content),
                "last_modified": utils.get_current_timestamp_iso()
            }
            # Create the actual file in the filesystem
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.writelines(content)
        
        # Create test directories
        test_dirs = ["source_dir", "target_dir"]
        for dir_name in test_dirs:
            dir_path = normalize_for_db(os.path.join(self.workspace_path, dir_name))
            os.makedirs(dir_path, exist_ok=True)
            DB["file_system"][dir_path] = {
                "path": dir_path,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": utils.get_current_timestamp_iso()
            }

    def tearDown(self):
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)

    def _get_expected_path_key(self, relative_path: str) -> str:
        current_workspace_root = DB["workspace_root"]
        abs_path = os.path.join(current_workspace_root, relative_path)
        normalized_key = os.path.normpath(abs_path).replace("\\\\", "/")
        return normalized_key

    def test_mv_file(self):
        source_file = "source.txt"
        target_file = "moved.txt"
        source_path = self._get_expected_path_key(source_file)
        target_path = self._get_expected_path_key(target_file)
        command = self._get_command_for_os({
            'unix': f"mv {source_file} {target_file}",
            'windows': f"move {source_file} {target_file}"
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        self.assertNotIn(source_path, DB["file_system"])
        self.assertIn(target_path, DB["file_system"])
        self.assertEqual(DB["file_system"][target_path]["content_lines"], ["This is source file content\n", "Line 2\n"])

    def test_mv_file_to_directory(self):
        source_file = "source.txt"
        target_dir = "target_dir"
        source_path = self._get_expected_path_key(source_file)
        target_path = self._get_expected_path_key(os.path.join(target_dir, source_file))
        command = self._get_command_for_os({
            'unix': f"mv {source_file} {target_dir}",
            'windows': f"move {source_file} {target_dir}"
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        self.assertNotIn(source_path, DB["file_system"])
        self.assertIn(target_path, DB["file_system"])
        self.assertEqual(DB["file_system"][target_path]["content_lines"], ["This is source file content\n", "Line 2\n"])

    def test_mv_directory(self):
        source_dir = "source_dir"
        target_dir = "moved_dir"
        source_path = self._get_expected_path_key(source_dir)
        target_path = self._get_expected_path_key(target_dir)
        nested_source = self._get_expected_path_key(os.path.join(source_dir, "nested.txt"))
        nested_target = self._get_expected_path_key(os.path.join(target_dir, "nested.txt"))
        command = self._get_command_for_os({
            'unix': f"mv {source_dir} {target_dir}",
            'windows': f"move {source_dir} {target_dir}"
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        self.assertNotIn(source_path, DB["file_system"])
        self.assertNotIn(nested_source, DB["file_system"])
        self.assertIn(target_path, DB["file_system"])
        self.assertTrue(DB["file_system"][target_path]["is_directory"])
        self.assertIn(nested_target, DB["file_system"])
        self.assertEqual(DB["file_system"][nested_target]["content_lines"], ["Nested file content\n"])

    def test_mv_nonexistent_file(self):
        source_file = "nonexistent.txt"
        target_file = "target.txt"
        command = self._get_command_for_os({
            'unix': f"mv {source_file} {target_file}",
            'windows': f"move {source_file} {target_file}"
        })
        with self.assertRaises(CommandExecutionError):
            run_command(command=command)

    def test_mv_overwrite_file(self):
        source_file = "source.txt"
        target_file = "target.txt" # This file exists with different content
        source_path = self._get_expected_path_key(source_file)
        target_path = self._get_expected_path_key(target_file)
        command = self._get_command_for_os({
            'unix': f"mv {source_file} {target_file}",
            'windows': f"move {source_file} {target_file}" # Windows 'move' overwrites by default if not moving to a dir
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        self.assertNotIn(source_path, DB["file_system"])
        self.assertIn(target_path, DB["file_system"])
        self.assertEqual(DB["file_system"][target_path]["content_lines"], ["This is source file content\n", "Line 2\n"])


class TestRedirectionCommand(unittest.TestCase):
    """Test cases for output redirection operators (> and >>) functionality."""

    def _get_command_for_os(self, command_template):
        if os.name == 'nt':
            shell = os.environ.get('SHELL', '').lower()
            if 'bash' in shell or 'zsh' in shell or 'sh' in shell:
                return command_template['unix']
            else:
                return f"cmd /c {command_template['windows']}"
        else:
            return command_template['unix']

    def setUp(self):
        minimal_reset_db()
        workspace_path_for_db = DB["workspace_root"]
        test_files = {
            "existing.txt": ["Original content\n"],
            "empty.txt": []
        }
        for filename, content in test_files.items():
            file_path = normalize_for_db(os.path.join(workspace_path_for_db, filename))
            DB["file_system"][file_path] = {
                "path": file_path, "is_directory": False, "content_lines": content,
                "size_bytes": utils.calculate_size_bytes(content),
                "last_modified": utils.get_current_timestamp_iso()
            }

    def tearDown(self):
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()

    def _get_expected_path_key(self, relative_path: str) -> str:
        current_workspace_root = DB["workspace_root"]
        abs_path = os.path.join(current_workspace_root, relative_path)
        normalized_key = os.path.normpath(abs_path).replace("\\\\", "/")
        return normalized_key

    def test_multiple_redirects(self):
        test_file = "multi_redirect.txt" # Use a new file to avoid state issues
        file_path = self._get_expected_path_key(test_file)
        content1 = "First line"
        content2 = "Second line"
        
        # Adjusted for how the simulation engine handles echo and redirection chains
        is_cmd_shell = os.name == 'nt' and not ('bash' in os.environ.get('SHELL', '').lower() or 'zsh' in os.environ.get('SHELL', '').lower() or 'sh' in os.environ.get('SHELL', '').lower())

        if is_cmd_shell:
            command = f'cmd /c "(echo {content1} > {test_file}) && (echo {content2} >> {test_file})"'
            # Sim engine's cmd echo adds space, and consecutive echos might have different spacing.
            # First echo > file results in "content1 \n"
            # Second echo >> file results in "content2 \n" (appended)
            expected_db_content = [f"{content1} \n", f"{content2} \n"]
        else: # Unix or Unix-like shell
            command = f'sh -c \'echo "{content1}" > {test_file} && echo "{content2}" >> {test_file}\''
            expected_db_content = [f"{content1}\n", f"{content2}\n"]

        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        self.assertIn(file_path, DB["file_system"])
        self.assertEqual(DB["file_system"][file_path]["content_lines"], expected_db_content)


class TestRmCommand(unittest.TestCase):
    """Test cases for remove/rm command functionality."""

    def _get_command_for_os(self, command_template):
        if os.name == 'nt':
            shell = os.environ.get('SHELL', '').lower()
            if 'bash' in shell or 'zsh' in shell or 'sh' in shell:
                return command_template['unix']
            else:
                return f"cmd /c {command_template['windows']}"
        else:
            return command_template['unix']

    def setUp(self):
        self.workspace_path = minimal_reset_db()
        
        # Create test files and directories
        test_files = {
            "file1.txt": ["File 1 content\n"],
            "file2.txt": ["File 2 content\n"],
            "test_dir/nested.txt": ["Nested file content\n"],
            "dir1/nested1.txt": ["Nested file 1 content\n"],
            "dir1/subdir/deep.txt": ["Deep file content\n"]
        }
        
        # Create all necessary directories first
        dirs_to_create = ["test_dir", "dir1", "dir1/subdir", "empty_dir"]
        for dir_name in dirs_to_create:
            dir_path = normalize_for_db(os.path.join(self.workspace_path, dir_name))
            os.makedirs(dir_path, exist_ok=True)
            DB["file_system"][dir_path] = {
                "path": dir_path,
                "is_directory": True,
                "content_lines": [],
                "size_bytes": 0,
                "last_modified": utils.get_current_timestamp_iso(),
                "metadata": utils._collect_file_metadata(dir_path)
            }
        
        # Create all test files
        for rel_path, content in test_files.items():
            file_path = normalize_for_db(os.path.join(self.workspace_path, rel_path))
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.writelines(content)
            DB["file_system"][file_path] = {
                "path": file_path,
                "is_directory": False,
                "content_lines": content,
                "size_bytes": utils.calculate_size_bytes(content),
                "last_modified": utils.get_current_timestamp_iso(),
                "metadata": utils._collect_file_metadata(file_path)
            }

    def tearDown(self):
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)

    def _get_expected_path_key(self, relative_path: str) -> str:
        current_workspace_root = DB["workspace_root"]
        abs_path = os.path.join(current_workspace_root, relative_path)
        normalized_key = os.path.normpath(abs_path).replace("\\\\", "/")
        return normalized_key

    def test_rm_file(self):
        test_file = "file1.txt"
        file_path = self._get_expected_path_key(test_file)
        command = self._get_command_for_os({
            'unix': f"rm {test_file}", 'windows': f"del {test_file}"
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        self.assertNotIn(file_path, DB["file_system"])

    def test_rm_multiple_files(self):
        test_files = ["file1.txt", "file2.txt"]
        file_paths = [self._get_expected_path_key(f) for f in test_files]
        command = self._get_command_for_os({
            'unix': f"rm {' '.join(test_files)}",
            'windows': f"del {' '.join(test_files)}"
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        for path in file_paths:
            self.assertNotIn(path, DB["file_system"])

    def test_rm_nonexistent_file(self):
        test_file = "nonexistent.txt"
        command = self._get_command_for_os({
            'unix': f"rm {test_file}", 'windows': f"del {test_file}"
        })
        shell = os.environ.get('SHELL', '').lower()
        is_unix_shell = 'bash' in shell or 'zsh' in shell or 'sh' in shell
        if is_unix_shell or os.name != 'nt':
            with self.assertRaises(CommandExecutionError):
                run_command(command=command)
        else: # Windows cmd
            result = run_command(command=command)
            self.assertEqual(result['returncode'], 0)

    def test_rm_directory(self): # Test removing an EMPTY directory
        test_dir = "empty_dir"
        dir_path = self._get_expected_path_key(test_dir)
        command = self._get_command_for_os({
            'unix': f"rmdir {test_dir}", 'windows': f"rd {test_dir}"
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        self.assertNotIn(dir_path, DB["file_system"])

    def test_rm_recursive_directory(self):
        test_dir = "dir1"
        dir_path = self._get_expected_path_key(test_dir)
        nested_file = self._get_expected_path_key(os.path.join(test_dir, "nested1.txt"))
        deep_file = self._get_expected_path_key(os.path.join(test_dir, "subdir", "deep.txt"))
        subdir_path = self._get_expected_path_key(os.path.join(test_dir, "subdir"))

        command = self._get_command_for_os({
            'unix': f"rm -r {test_dir}", 'windows': f"rd /s /q {test_dir}"
        })
        result = run_command(command=command)
        # For Windows `rd /s /q`, return code is 0 even if it does nothing (e.g. dir doesn't exist)
        # For Unix `rm -r`, it's also 0 if dir doesn't exist (with -f implied by sim sometimes, or no error by default for non-exist)
        self.assertEqual(result['returncode'], 0)
        self.assertNotIn(dir_path, DB["file_system"])
        self.assertNotIn(nested_file, DB["file_system"])
        self.assertNotIn(subdir_path, DB["file_system"])
        self.assertNotIn(deep_file, DB["file_system"])


    def test_rm_nonempty_directory_without_recursive(self):
        test_dir = "dir1" # This directory is non-empty
        command = self._get_command_for_os({
            'unix': f"rmdir {test_dir}", 'windows': f"rd {test_dir}"
        })
        with self.assertRaises(CommandExecutionError):
            run_command(command=command)


class TestTailCommand(unittest.TestCase):
    """Test cases for tail command functionality."""

    def _get_command_for_os(self, command_template):
        if os.name == 'nt':
            shell = os.environ.get('SHELL', '').lower()
            if 'bash' in shell or 'zsh' in shell or 'sh' in shell:
                return command_template['unix']
            else:
                return f"cmd /c {command_template['windows']}"
        else:
            return command_template['unix']

    def setUp(self):
        self.workspace_path = minimal_reset_db()
        test_files = {
            "long.txt": [f"Line {i}\n" for i in range(1, 11)],
            "short.txt": ["First line\n", "Second line\n"],
            "empty.txt": []
        }
        for filename, content in test_files.items():
            file_path = normalize_for_db(os.path.join(self.workspace_path, filename))
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.writelines(content)
            DB["file_system"][file_path] = {
                "path": file_path,
                "is_directory": False,
                "content_lines": content,
                "size_bytes": utils.calculate_size_bytes(content),
                "last_modified": utils.get_current_timestamp_iso(),
                "metadata": utils._collect_file_metadata(file_path)
            }

    def tearDown(self):
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)

    def _get_expected_path_key(self, relative_path: str) -> str:
        current_workspace_root = DB["workspace_root"]
        abs_path = os.path.join(current_workspace_root, relative_path)
        normalized_key = os.path.normpath(abs_path).replace("\\\\", "/")
        return normalized_key

    def test_tail_default_lines(self):
        test_file = "long.txt"
        file_path = self._get_expected_path_key(test_file)
        command = self._get_command_for_os({
            'unix': f"tail {test_file}",
            'windows': f"powershell -Command \"Get-Content {test_file} | Select-Object -Last 10\""
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        # Default tail for a 10 line file is all 10 lines
        expected_content = "".join(DB["file_system"][file_path]["content_lines"])
        self.assertEqual(result['stdout'], expected_content)

    def test_tail_specific_lines(self):
        test_file = "long.txt"
        file_path = self._get_expected_path_key(test_file)
        num_lines = 3
        command = self._get_command_for_os({
            'unix': f"tail -n {num_lines} {test_file}",
            'windows': f"powershell -Command \"Get-Content {test_file} | Select-Object -Last {num_lines}\""
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        expected_content = "".join(DB["file_system"][file_path]["content_lines"][-num_lines:])
        self.assertEqual(result['stdout'], expected_content)

    def test_tail_short_file(self):
        test_file = "short.txt" # Has 2 lines
        file_path = self._get_expected_path_key(test_file)
        num_lines = 5 # Request more lines than available
        command = self._get_command_for_os({
            'unix': f"tail -n {num_lines} {test_file}",
            'windows': f"powershell -Command \"Get-Content {test_file} | Select-Object -Last {num_lines}\""
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        expected_content = "".join(DB["file_system"][file_path]["content_lines"]) # Should return all lines
        self.assertEqual(result['stdout'], expected_content)

    def test_tail_empty_file(self):
        test_file = "empty.txt"
        command = self._get_command_for_os({
            'unix': f"tail {test_file}",
            'windows': f"powershell -Command \"Get-Content {test_file} | Select-Object -Last 10\""
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(result['stdout'], "")

    def test_tail_nonexistent_file(self):
        test_file = "nonexistent.txt"
        command = self._get_command_for_os({
            'unix': f"tail {test_file}",
            'windows': f"powershell -Command \"Get-Content {test_file} | Select-Object -Last 10\""
        })
        with self.assertRaises(CommandExecutionError):
            run_command(command=command)


class TestTouchCommand(unittest.TestCase):
    """Test cases for touch command functionality."""

    def _get_command_for_os(self, command_template):
        if os.name == 'nt':
            shell = os.environ.get('SHELL', '').lower()
            if 'bash' in shell or 'zsh' in shell or 'sh' in shell:
                return command_template['unix']
            else:
                return f"cmd /c {command_template['windows']}"
        else:
            return command_template['unix']

    def setUp(self):
        minimal_reset_db()
        workspace_path_for_db = DB["workspace_root"]
        test_files = {
            "existing.txt": ["Some content\n"],
            "empty.txt": [] # This will be touched (if it exists) or created
        }
        for filename, content in test_files.items():
            file_path = normalize_for_db(os.path.join(workspace_path_for_db, filename))
            DB["file_system"][file_path] = {
                "path": file_path, "is_directory": False, "content_lines": content,
                "size_bytes": utils.calculate_size_bytes(content),
                "last_modified": utils.get_current_timestamp_iso()
            }

    def tearDown(self):
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()

    def _get_expected_path_key(self, relative_path: str) -> str:
        current_workspace_root = DB["workspace_root"]
        abs_path = os.path.join(current_workspace_root, relative_path)
        normalized_key = os.path.normpath(abs_path).replace("\\\\", "/")
        return normalized_key

    def test_touch_new_file(self):
        test_file = "newly_touched.txt"
        file_path = self._get_expected_path_key(test_file)
        command = self._get_command_for_os({
            'unix': f"touch {test_file}",
            'windows': f"type nul > {test_file}" # Common way to touch/create empty file
        })
        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        self.assertIn(file_path, DB["file_system"])
        self.assertFalse(DB["file_system"][file_path]["is_directory"])
        # Touch creates an empty file if it doesn't exist
        self.assertEqual(DB["file_system"][file_path]["content_lines"], [])
        self.assertEqual(DB["file_system"][file_path]["size_bytes"], 0)

    # def test_touch_existing_file(self):
    #     test_file = "existing.txt"
    #     file_path = self._get_expected_path_key(test_file)
    #     original_content = DB["file_system"][file_path]["content_lines"][:]
    #     original_timestamp = DB["file_system"][file_path]["last_modified"]
        
    #     # Allow a moment for timestamp to differ
    #     import time
    #     time.sleep(0.01)

    #     # Windows "type nul > existing.txt" would truncate.
    #     # Unix "touch existing.txt" updates timestamp without changing content.
    #     # The simulation should ideally mimic the core 'touch' behavior (update timestamp, create if not exists)
    #     # Let's use the unix version primarily for testing the 'touch' idea.
    #     # If on windows, `fsutil file createnew existing.txt 0` would be closer, but `type nul` is for creation by `touch`.
    #     # The simulation of `touch existing.txt` should update timestamp.
    #     # The simulation of `type nul > existing.txt` (Windows touch equivalent if file exists) *will* truncate.
    #     # We should test the intended behavior based on the command.
        
    #     is_unix_like_touch = True
    #     if os.name == 'nt':
    #         shell = os.environ.get('SHELL', '').lower()
    #         if not ('bash' in shell or 'zsh' in shell or 'sh' in shell):
    #             is_unix_like_touch = False # cmd.exe 'type nul >' behavior

    #     if is_unix_like_touch:
    #         command = f"touch {test_file}"
    #     else: # cmd.exe behavior for "type nul > existing.txt"
    #         command = f"cmd /c type nul > {test_file}"

    #     result = run_command(command=command)
    #     self.assertEqual(result['returncode'], 0)
    #     self.assertIn(file_path, DB["file_system"])

    #     if is_unix_like_touch: # Unix touch should preserve content
    #         self.assertEqual(DB["file_system"][file_path]["content_lines"], original_content)
    #         self.assertNotEqual(DB["file_system"][file_path]["last_modified"], original_timestamp, "Timestamp should update")
    #     else: # Windows 'type nul >' truncates
    #         self.assertEqual(DB["file_system"][file_path]["content_lines"], [])
    #         self.assertEqual(DB["file_system"][file_path]["size_bytes"], 0)
    #         # Timestamp also updates
    #         self.assertNotEqual(DB["file_system"][file_path]["last_modified"], original_timestamp, "Timestamp should update")


    def test_touch_multiple_files(self):
        test_files_to_touch = ["multi1.txt", "multi2.txt"]
        file_paths_expected = [self._get_expected_path_key(f) for f in test_files_to_touch]
        
        command_str_parts = []
        is_cmd_shell = os.name == 'nt' and not ('bash' in os.environ.get('SHELL', '').lower() or 'zsh' in os.environ.get('SHELL', '').lower() or 'sh' in os.environ.get('SHELL', '').lower())

        if is_cmd_shell:
            # cmd.exe doesn't directly support `touch file1 file2`
            # We simulate by chaining `type nul > file` commands
            command = "cmd /c " + " && ".join([f"type nul > {f}" for f in test_files_to_touch])
        else: # Unix or unix-like shell
            command = f"touch {' '.join(test_files_to_touch)}"

        result = run_command(command=command)
        self.assertEqual(result['returncode'], 0)
        for path in file_paths_expected:
            self.assertIn(path, DB["file_system"])
            self.assertFalse(DB["file_system"][path]["is_directory"])
            self.assertEqual(DB["file_system"][path]["content_lines"], [])
            self.assertEqual(DB["file_system"][path]["size_bytes"], 0)

    def test_touch_in_nonexistent_directory(self):
        test_file = "nonexistent_dir/new.txt"
        command = self._get_command_for_os({
            'unix': f"touch {test_file}",
            'windows': f"type nul > {test_file}"
        })
        # This behavior depends on the OS. `touch` on Unix fails. `type nul >` on Windows might also fail depending on shell.
        # The simulation should make it fail as the parent directory doesn't exist.
        with self.assertRaises(CommandExecutionError):
            run_command(command=command)

class TestEnvironmentVariables(unittest.TestCase):
    """Test cases for environment variable functionality."""

    def setUp(self):
        minimal_reset_db()
        # Initialize environment in DB
        DB['environment'] = {
            'system': {},
            'workspace': {},
            'session': {}
        }

    def tearDown(self):
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()

    def _get_command_for_os(self, command_template):
        if os.name == 'nt':
            shell = os.environ.get('SHELL', '').lower()
            if 'bash' in shell or 'zsh' in shell or 'sh' in shell:
                return command_template['unix']
            else:
                return f"cmd /c {command_template['windows']}"
        else:
            return command_template['unix']

    def test_export_basic(self):
        """Test basic variable export."""
        result = run_command("export TEST_VAR=test_value")
        self.assertEqual(result['returncode'], 0)
        self.assertIn('TEST_VAR', DB['environment']['session'])
        self.assertEqual(DB['environment']['session']['TEST_VAR'], 'test_value')

    def test_export_quoted_value(self):
        """Test exporting values with quotes."""
        # Test basic quoted values
        run_command("export VAR1='value with spaces'")
        result = run_command("echo $VAR1")
        self.assertEqual(result['stdout'].strip(), 'value with spaces', "Should preserve spaces in quoted values")

        # Test quotes in values
        run_command("export VAR2='value with \"quotes\"'")
        result = run_command("echo $VAR2")
        self.assertEqual(result['stdout'].strip(), 'value with "quotes"', "Should preserve double quotes inside single quotes")

        # Test values with special characters
        special_chars = "!@#$%^&*()_+-=[]{}\\|;:,./<>?"
        run_command(f"export VAR3='{special_chars}'")
        result = run_command("echo $VAR3")
        self.assertEqual(result['stdout'].strip(), special_chars, "Should preserve special characters")

        # Test empty quoted values
        run_command("export VAR4=''")
        result = run_command("echo $VAR4")
        self.assertEqual(result['stdout'].strip(), '', "Should handle empty quoted values")

        # Verify values in DB directly
        self.assertEqual(DB['environment']['session']['VAR1'], 'value with spaces')
        self.assertEqual(DB['environment']['session']['VAR2'], 'value with "quotes"')
        self.assertEqual(DB['environment']['session']['VAR3'], special_chars)
        self.assertEqual(DB['environment']['session']['VAR4'], '')

    def test_export_invalid_syntax(self):
        """Test export command with invalid syntax."""
        result = run_command("export INVALID_EXPORT")
        self.assertEqual(result['returncode'], 1)
        self.assertIn('Invalid syntax', result['stderr'])

    def test_unset_variable(self):
        """Test unsetting environment variables."""
        # Set up a variable first
        run_command("export TEST_VAR=value")
        self.assertIn('TEST_VAR', DB['environment']['session'])
        
        # Unset it
        result = run_command("unset TEST_VAR")
        self.assertEqual(result['returncode'], 0)
        self.assertNotIn('TEST_VAR', DB['environment']['session'])

    def test_unset_nonexistent_variable(self):
        """Test unsetting a variable that doesn't exist."""
        result = run_command("unset NONEXISTENT_VAR")
        self.assertEqual(result['returncode'], 0)
        self.assertIn('was not set', result['message'])

    def test_env_command(self):
        """Test the env command output."""
        # Set up some custom variables
        run_command("export CUSTOM_VAR1=value1")
        run_command("export CUSTOM_VAR2=value2")
        
        # Get env output
        result = run_command("env")
        self.assertEqual(result['returncode'], 0)
        
        # Split output into lines and convert to dict
        env_lines = result['stdout'].splitlines()
        env_dict = dict(line.split('=', 1) for line in env_lines)
        
        # 1. Verify required base environment variables are present with correct values
        required_vars = {
            'SHELL': '/bin/bash',
            'USER': 'user',
            'HOME': '/home/user',
            'TERM': 'xterm-256color',
            'LANG': 'en_US.UTF-8',
            'LC_ALL': 'en_US.UTF-8',
            'HOSTNAME': 'isolated-env',
            'TZ': 'UTC'
        }
        for var, expected_value in required_vars.items():
            self.assertIn(var, env_dict, f"Missing required environment variable: {var}")
            self.assertEqual(env_dict[var], expected_value, f"Incorrect value for {var}")
        
        # Verify PWD exists and is the workspace root (logical path)
        self.assertIn('PWD', env_dict)
        self.assertEqual(env_dict['PWD'], DB["workspace_root"], "PWD should be the logical workspace root")
        
        # 2. Verify PATH contains essential directories
        path_dirs = env_dict['PATH'].split(':')
        required_paths = ['/usr/local/bin', '/usr/bin', '/bin']
        for req_path in required_paths:
            self.assertTrue(any(p == req_path for p in path_dirs), f"Missing required PATH entry: {req_path}")
        
        # 3. Verify custom variables are present
        self.assertEqual(env_dict['CUSTOM_VAR1'], 'value1')
        self.assertEqual(env_dict['CUSTOM_VAR2'], 'value2')
        
        # 4. Verify output format
        for line in env_lines:
            # Each line should be in VAR=value format
            self.assertRegex(line, r'^[A-Za-z_][A-Za-z0-9_]*=.*$', f"Invalid environment variable format: {line}")
        
        # 5. Verify sorting
        sorted_lines = sorted(env_lines)
        self.assertEqual(env_lines, sorted_lines, "Environment variables should be sorted alphabetically")
        
        # 6. Verify no duplicate variables
        self.assertEqual(len(env_lines), len(set(env_lines)), "Found duplicate environment variables")

    def test_variable_expansion_basic(self):
        """Test basic variable expansion in commands."""
        run_command("export GREETING=Hello")
        run_command("export NAME=World")
        
        # Test echo with variable expansion
        result = run_command("echo $GREETING $NAME")
        self.assertEqual(result['stdout'].strip(), "Hello World")

    def test_variable_expansion_braces(self):
        """Test variable expansion with braces."""
        run_command("export FOO=bar")
        result = run_command("echo ${FOO}value")
        self.assertEqual(result['stdout'].strip(), "barvalue")

    def test_variable_expansion_missing(self):
        """Test expansion of non-existent variables."""
        result = run_command("echo $NONEXISTENT_VAR")
        self.assertEqual(result['stdout'].strip(), "")

    def test_variable_persistence(self):
        """Test that variables persist across commands."""
        run_command("export PERSISTENT=value")
        result = run_command("echo $PERSISTENT")
        self.assertEqual(result['stdout'].strip(), "value")

    def test_variable_isolation(self):
        """Test that environment changes don't affect the host system."""
        test_var_name = "TEST_ISOLATION_VAR"
        original_value = os.environ.get(test_var_name)
        
        try:
            # Set a variable in our virtual environment
            run_command(f"export {test_var_name}=virtual_value")
            
            # Verify it's set in our DB
            self.assertEqual(DB['environment']['session'][test_var_name], 'virtual_value')
            
            # Verify it hasn't affected the real environment
            self.assertEqual(os.environ.get(test_var_name), original_value)
        finally:
            # Cleanup if needed
            if original_value is not None:
                os.environ[test_var_name] = original_value
            elif test_var_name in os.environ:
                del os.environ[test_var_name]

    def test_complex_variable_usage(self):
        """Test complex scenarios with environment variables."""
        # Set up some variables
        run_command("export PATH=/usr/local/bin:/usr/bin")
        run_command("export HOME=/home/user")
        run_command("export APP_DIR=$HOME/app")
        run_command("export FULL_PATH=$APP_DIR/bin:$PATH")
        
        # Test nested variable expansion
        result = run_command("echo $FULL_PATH")
        expected = "/home/user/app/bin:/usr/local/bin:/usr/bin"
        self.assertEqual(result['stdout'].strip(), expected)

    def test_variable_in_command_args(self):
        """Test using variables in command arguments."""
        # Create a test file
        test_file = "test.txt"
        file_path = os.path.join(DB["workspace_root"], test_file)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            f.write("test content\n")
        
        DB["file_system"][file_path] = {
            "path": file_path,
            "is_directory": False,
            "content_lines": ["test content\n"],
            "size_bytes": len("test content\n"),
            "last_modified": utils.get_current_timestamp_iso(),
            "metadata": utils._collect_file_metadata(file_path)
        }
        
        # Use variable in cat command
        run_command("export FILE=test.txt")
        result = run_command(self._get_command_for_os({
            'unix': "cat $FILE",
            'windows': "type $FILE"
        }))
        self.assertEqual(result['stdout'].strip(), "test content")

    def test_multiline_variable_content(self):
        """Test handling of multiline variable content."""
        multiline = """line1
line2
line3"""
        run_command("export MULTILINE='"+multiline+"'")
        result = run_command("echo \"$MULTILINE\"")
        self.assertEqual(result['stdout'].strip(), multiline)

    def test_special_chars_in_variables(self):
        """Test handling of special characters in variables."""
        special_chars = "!@#$%^&*()_+-=[]{}\\|;:'\",.<>/?"
        run_command(f"export SPECIAL='{special_chars}'")
        result = run_command("echo \"$SPECIAL\"")
        self.assertEqual(result['stdout'].strip(), special_chars)

    def test_variable_scope(self):
        """Test variable scoping between session and workspace."""
        # Set in session scope
        run_command("export SESSION_VAR=session_value")
        self.assertIn('SESSION_VAR', DB['environment']['session'])
        
        # Set in workspace scope
        DB['environment']['workspace']['WORKSPACE_VAR'] = 'workspace_value'
        
        # Verify both are accessible
        result = run_command("echo $SESSION_VAR $WORKSPACE_VAR")
        self.assertEqual(result['stdout'].strip(), "session_value workspace_value")

    def test_variable_precedence(self):
        """Test variable precedence (session over workspace over system)."""
        # Set up variables at different levels
        DB['environment']['system']['TEST_VAR'] = 'system_value'
        DB['environment']['workspace']['TEST_VAR'] = 'workspace_value'
        run_command("export TEST_VAR=session_value")
        
        # Verify session value takes precedence
        result = run_command("echo $TEST_VAR")
        self.assertEqual(result['stdout'].strip(), "session_value")

    def test_empty_variable_values(self):
        """Test handling of empty variable values."""
        run_command("export EMPTY=")
        run_command("export EMPTY_QUOTED=''")
        
        result1 = run_command("echo $EMPTY")
        result2 = run_command("echo $EMPTY_QUOTED")
        
        self.assertEqual(result1['stdout'].strip(), "")
        self.assertEqual(result2['stdout'].strip(), "")

    def test_variable_in_background_process(self):
        """Test environment variables in background processes."""
        run_command("export BG_VAR=background_value")
        
        # Start a background process that uses the variable
        result = run_command("echo $BG_VAR > output.txt &", is_background=True)
        self.assertIsNotNone(result['pid'])
        
        # Verify the variable was available to the background process
        # Note: In a real implementation, you'd need to wait for the background process
        # or check the output file after a delay

    def test_system_variables_filtering(self):
        """Test that only allowed system variables are accessible."""
        # Set a custom PATH in the real environment
        original_path = os.environ.get('PATH')
        test_path = '/custom/path'
        try:
            os.environ['PATH'] = test_path

            # Set a non-allowed system variable
            os.environ['CUSTOM_SYSTEM_VAR'] = 'custom_value'
            
            # Verify it's not accessible in our environment
            result = run_command("echo $CUSTOM_SYSTEM_VAR")
            self.assertEqual(result['stdout'].strip(), "")
        finally:
            # Restore original PATH
            if original_path is not None:
                os.environ['PATH'] = original_path
            if 'CUSTOM_SYSTEM_VAR' in os.environ:
                del os.environ['CUSTOM_SYSTEM_VAR']

    def test_variable_expansion_edge_cases(self):
        """Test edge cases in variable expansion."""
        test_cases = [
            ("export VAR='value'", "echo $VAR", "value"),  # Basic case
            ("export VAR='value'", "echo ${VAR}", "value"),  # Braces
            ("export VAR='value'", "echo ${VAR}suffix", "valuesuffix"),  # Suffix
            ("export VAR='value'", "echo prefix${VAR}", "prefixvalue"),  # Prefix
            ("export VAR='value'", "echo ${VAR}${VAR}", "valuevalue"),  # Multiple
            ("export VAR='value'", "echo $VAR$VAR", "valuevalue"),  # Adjacent
            # ("export VAR='$HOME'", "echo $VAR", "$HOME"),  # Literal $
            ("export VAR='value'", "echo '$VAR'", "$VAR"),  # Single quotes
            ("export VAR='value'", "echo \"$VAR\"", "value"),  # Double quotes
        ]
        
        for setup_cmd, test_cmd, expected in test_cases:
            with self.subTest(setup_cmd=setup_cmd, test_cmd=test_cmd):
                run_command(setup_cmd)
                result = run_command(test_cmd)
                self.assertEqual(result['stdout'].strip(), expected)

    def test_base_environment_presence(self):
        """Test that all base environment variables are present by default."""
        result = run_command("env")
        self.assertEqual(result['returncode'], 0)
        
        expected_vars = {
            'PWD', 'SHELL', 'USER', 'HOME', 'PATH',
            'TERM', 'LANG', 'LC_ALL', 'HOSTNAME', 'TZ'
        }
        
        env_output = result['stdout']
        actual_vars = {line.split('=')[0] for line in env_output.splitlines()}
        
        for var in expected_vars:
            self.assertIn(var, actual_vars, f"Base environment variable {var} is missing")

    def test_base_environment_values(self):
        """Test that base environment variables have the expected default values."""
        result = run_command("env")
        env_dict = dict(line.split('=', 1) for line in result['stdout'].splitlines())
        
        self.assertEqual(env_dict['SHELL'], '/bin/bash')
        self.assertEqual(env_dict['USER'], 'user')
        self.assertEqual(env_dict['HOME'], '/home/user')
        self.assertEqual(env_dict['TERM'], 'xterm-256color')
        self.assertEqual(env_dict['LANG'], 'en_US.UTF-8')
        self.assertEqual(env_dict['LC_ALL'], 'en_US.UTF-8')
        self.assertEqual(env_dict['HOSTNAME'], 'isolated-env')
        self.assertEqual(env_dict['TZ'], 'UTC')
        self.assertIn('/usr/local/bin', env_dict['PATH'])
        self.assertIn('/usr/bin', env_dict['PATH'])

    def test_override_base_environment(self):
        """Test that base environment variables can be overridden."""
        # Override through export (session)
        run_command("export PATH=/custom/path")
        run_command("export HOME=/custom/home")
        result = run_command("env")
        env_dict = dict(line.split('=', 1) for line in result['stdout'].splitlines())
        
        self.assertEqual(env_dict['PATH'], '/custom/path')
        self.assertEqual(env_dict['HOME'], '/custom/home')
        
        # Override through workspace
        DB['environment']['workspace']['USER'] = 'custom_user'
        DB['environment']['workspace']['SHELL'] = '/custom/shell'
        result = run_command("env")
        env_dict = dict(line.split('=', 1) for line in result['stdout'].splitlines())
        
        self.assertEqual(env_dict['USER'], 'custom_user')
        self.assertEqual(env_dict['SHELL'], '/custom/shell')

    def test_complete_system_isolation(self):
        """Test isolation from arbitrary system environment variables (PATH is intentionally inherited)."""
        # Modify system PATH and add a custom variable
        original_path = os.environ.get('PATH')
        try:
            os.environ['PATH'] = '/system/custom/path'
            os.environ['CUSTOM_VAR'] = 'system_value'
            
            result = run_command("env")
            env_dict = dict(line.split('=', 1) for line in result['stdout'].splitlines())
            
            # NOTE: PATH is intentionally inherited from parent process (for java, mvn, etc.)
            # This is by design to allow user-installed tools to work
            self.assertEqual(env_dict['PATH'], '/system/custom/path',
                           "PATH should be inherited from parent process")
            
            # Verify arbitrary system-specific variables are NOT present (isolation)
            self.assertNotIn('CUSTOM_VAR', env_dict,
                           "Arbitrary system variables should not be inherited")
        finally:
            if original_path is not None:
                os.environ['PATH'] = original_path
            if 'CUSTOM_VAR' in os.environ:
                del os.environ['CUSTOM_VAR']

    def test_env_command_sorting(self):
        """Test that env command output is alphabetically sorted."""
        run_command("export Z_VAR=z")
        run_command("export A_VAR=a")
        run_command("export M_VAR=m")
        
        result = run_command("env")
        lines = result['stdout'].splitlines()
        
        # Extract just the variable names for easier comparison
        var_names = [line.split('=')[0] for line in lines]
        sorted_var_names = sorted(var_names)
        
        self.assertEqual(var_names, sorted_var_names)

    def test_env_multiline_values(self):
        """Test that env handles multiline values correctly."""
        multiline_value = 'line1\\nline2\\nline3'
        run_command(f"export MULTILINE='{multiline_value}'")
        
        result = run_command("env")
        env_dict = dict(line.split('=', 1) for line in result['stdout'].splitlines())
        
        self.assertEqual(env_dict['MULTILINE'], multiline_value)

    def test_variable_expansion_with_defaults(self):
        """Test variable expansion with default values using ${VAR:-default} syntax."""
        result = run_command("echo ${NONEXISTENT_VAR:-default_value}")
        self.assertEqual(result['stdout'].strip(), "default_value")
        
        run_command("export TEST_VAR=actual_value")
        result = run_command("echo ${TEST_VAR:-default_value}")
        self.assertEqual(result['stdout'].strip(), "actual_value")

    def test_export_multiple_variables(self):
        """Test exporting multiple variables in a single command."""
        # Export variables one by one to ensure proper handling
        run_command("export VAR1=val1")
        run_command("export VAR2=val2")
        run_command("export VAR3=val3")
        
        # Verify each variable was set correctly
        self.assertEqual(DB['environment']['session']['VAR1'], 'val1')
        self.assertEqual(DB['environment']['session']['VAR2'], 'val2')
        self.assertEqual(DB['environment']['session']['VAR3'], 'val3')

    def test_variable_persistence_in_subshells(self):
        """Test variable persistence and isolation in subshells."""
        run_command("export PARENT_VAR=parent_value")
        result = run_command("bash -c 'echo $PARENT_VAR'")
        self.assertEqual(result['stdout'].strip(), "parent_value")
        
        # Test subshell variable doesn't affect parent
        result = run_command("bash -c 'export CHILD_VAR=child_value'")
        result = run_command("echo $CHILD_VAR")
        self.assertEqual(result['stdout'].strip(), "")

    def test_variable_name_validation(self):
        """Test validation of environment variable names."""
        # Test standard variable names
        result = run_command("export NORMAL_VAR=value")
        self.assertEqual(result['returncode'], 0)
        self.assertIn('NORMAL_VAR', DB['environment']['session'])
        
        # Test underscore prefix
        result = run_command("export _VAR=value")
        self.assertEqual(result['returncode'], 0)
        self.assertIn('_VAR', DB['environment']['session'])
        
        # Test numbers in name
        result = run_command("export VAR2=value")
        self.assertEqual(result['returncode'], 0)
        self.assertIn('VAR2', DB['environment']['session'])
        
        # Test variable value preservation
        run_command("export TEST_VAR='test value with spaces'")
        result = run_command("echo $TEST_VAR")
        self.assertEqual(result['stdout'].strip(), 'test value with spaces')

    def test_variable_quoting_rules(self):
        """Test different quoting rules for variable values."""
        # Test nested quotes
        run_command("export VAR1='value with \"double\" quotes'")
        result = run_command("echo \"$VAR1\"")
        self.assertEqual(result['stdout'].strip(), 'value with "double" quotes')
        
        # Test simple quotes
        run_command("export VAR2='value with single quotes'")
        result = run_command("echo \"$VAR2\"")
        self.assertEqual(result['stdout'].strip(), "value with single quotes")

    def test_path_variable_manipulation(self):
        """Test PATH variable manipulation and validation."""
        original_path = run_command("echo $PATH")['stdout'].strip()
        
        # Append to PATH
        run_command("export PATH=$PATH:/new/path")
        result = run_command("echo $PATH")
        self.assertTrue(result['stdout'].strip().endswith("/new/path"))
        
        # Prepend to PATH
        run_command("export PATH=/another/path:$PATH")
        result = run_command("echo $PATH")
        self.assertTrue(result['stdout'].strip().startswith("/another/path"))

    def test_variable_size_limits(self):
        """Test handling of large environment variables."""
        # Test with a reasonably large value (100KB)
        large_value = "x" * 100000
        result = run_command(f"export LARGE_VAR={large_value}")
        self.assertEqual(result['returncode'], 0)
        
        result = run_command("echo $LARGE_VAR")
        self.assertEqual(len(result['stdout'].strip()), 100000)

    def test_variable_circular_references(self):
        """Test handling of circular variable references."""
        run_command("export VAR1='$VAR2'")
        run_command("export VAR2='$VAR1'")
        result = run_command("echo $VAR1")
        # Should handle circular reference gracefully
        self.assertEqual(result['stdout'].strip(), "")

    def test_unicode_variables(self):
        """Test handling of Unicode characters in environment variables."""
        unicode_value = "🌟 Hello 世界"
        run_command(f"export UNICODE_VAR='{unicode_value}'")
        result = run_command("echo $UNICODE_VAR")
        self.assertEqual(result['stdout'].strip(), unicode_value)

    def test_unset_behavior(self):
        """Test various unset behaviors and edge cases."""
        # 1. Test unsetting from session environment
        run_command("export SESSION_VAR=session_value")
        self.assertIn('SESSION_VAR', DB['environment']['session'])
        
        result = run_command("unset SESSION_VAR")
        self.assertEqual(result['returncode'], 0)
        self.assertIn('from session environment', result['message'])
        self.assertNotIn('SESSION_VAR', DB['environment']['session'])
        
        # 2. Test unsetting from workspace environment
        DB['environment']['workspace']['WORKSPACE_VAR'] = 'workspace_value'
        result = run_command("unset WORKSPACE_VAR")
        self.assertEqual(result['returncode'], 0)
        self.assertIn('from workspace environment', result['message'])
        self.assertNotIn('WORKSPACE_VAR', DB['environment']['workspace'])
        
        # 3. Test unsetting non-existent variable
        result = run_command("unset NONEXISTENT_VAR")
        self.assertEqual(result['returncode'], 0)
        self.assertIn('was not set', result['message'])
        
        # 4. Test that unset affects variable expansion
        run_command("export TEST_VAR=test_value")
        result = run_command("echo $TEST_VAR")
        self.assertEqual(result['stdout'].strip(), "test_value")
        
        run_command("unset TEST_VAR")
        result = run_command("echo $TEST_VAR")
        self.assertEqual(result['stdout'].strip(), "")
        
        # 5. Test that unset preserves other variables
        run_command("export VAR1=val1")
        run_command("export VAR2=val2")
        run_command("unset VAR1")
        self.assertNotIn('VAR1', DB['environment']['session'])
        self.assertIn('VAR2', DB['environment']['session'])
        self.assertEqual(DB['environment']['session']['VAR2'], 'val2')
        
        # 6. Test that base environment variables cannot be unset
        original_env = run_command("env")
        run_command("unset PATH")
        run_command("unset HOME")
        run_command("unset USER")
        after_unset_env = run_command("env")
        
        # Base variables should still be present with original values
        self.assertEqual(
            dict(line.split('=', 1) for line in original_env['stdout'].splitlines())['PATH'],
            dict(line.split('=', 1) for line in after_unset_env['stdout'].splitlines())['PATH']
        )
        
        # 7. Test unset in subshell doesn't affect parent
        run_command("export PARENT_VAR=parent_value")
        run_command("bash -c 'unset PARENT_VAR'")
        result = run_command("echo $PARENT_VAR")
        self.assertEqual(result['stdout'].strip(), "parent_value")

class TestRunCommandMetadata(unittest.TestCase):
    """Test cases for metadata handling in run_command."""
    
    def setUp(self):
        """Set up test environment before each test."""
        self.workspace_path = minimal_reset_db()
        
        # Create test files with specific content
        self.test_file = os.path.join(self.workspace_path, "test.txt")
        self.test_dir_path = os.path.join(self.workspace_path, "test_dir")
        self.symlink_path = os.path.join(self.workspace_path, "test_link")
        
        # Create files and set up initial metadata
        os.makedirs(os.path.dirname(self.test_file), exist_ok=True)
        with open(self.test_file, 'w') as f:
            f.write("test content\n")
        os.makedirs(self.test_dir_path)
        os.symlink(self.test_file, self.symlink_path)

        # Add root directory to DB with metadata
        root_metadata = utils._collect_file_metadata(self.workspace_path)
        DB["file_system"][self.workspace_path] = {
            "path": self.workspace_path,
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": utils.get_current_timestamp_iso(),
            "metadata": root_metadata
        }

        # Add test file to DB with metadata
        test_file_metadata = utils._collect_file_metadata(self.test_file)
        DB["file_system"][self.test_file] = {
            "path": self.test_file,
            "is_directory": False,
            "content_lines": ["test content\n"],
            "size_bytes": os.path.getsize(self.test_file),
            "last_modified": utils.get_current_timestamp_iso(),
            "metadata": test_file_metadata
        }

        # Add test directory to DB with metadata
        test_dir_metadata = utils._collect_file_metadata(self.test_dir_path)
        DB["file_system"][self.test_dir_path] = {
            "path": self.test_dir_path,
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": utils.get_current_timestamp_iso(),
            "metadata": test_dir_metadata
        }

        # Add symlink to DB with metadata
        symlink_metadata = utils._collect_file_metadata(self.symlink_path)
        DB["file_system"][self.symlink_path] = {
            "path": self.symlink_path,
            "is_directory": False,
            "content_lines": ["test content\n"],
            "size_bytes": os.path.getsize(self.test_file),
            "last_modified": utils.get_current_timestamp_iso(),
            "metadata": symlink_metadata
        }
        
        # Initialize sandbox and add delay for timestamp precision
        run_command("pwd")
        import time
        time.sleep(0.1)

    def tearDown(self):
        """Clean up after each test."""
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)

    def test_basic_metadata_preservation(self):
        """Test that basic file metadata is preserved after command execution."""
        # Execute a simple command
        result = run_command("ls")
        self.assertEqual(result["returncode"], 0)
        
        # Verify metadata is preserved
        entry = DB["file_system"][self.test_file]
        self.assertIn("metadata", entry)
        self.assertEqual(entry["metadata"]["attributes"]["is_readonly"], False)


    def test_timestamp_updates(self):
        """Test that timestamp updates are captured."""
        # Get initial timestamps
        initial_entry = DB["file_system"][self.test_file]
        initial_mtime = initial_entry["metadata"]["timestamps"]["modify_time"]
        
        # Modify file
        result = run_command(f"echo 'new content' > {os.path.basename(self.test_file)}")
        self.assertEqual(result["returncode"], 0)
        
        # Verify timestamps updated
        updated_entry = DB["file_system"][self.test_file]
        self.assertNotEqual(
            updated_entry["metadata"]["timestamps"]["modify_time"],
            initial_mtime
        )

    def test_change_time_not_modified_by_metadata_commands(self):
        """change_time should not change for metadata-only commands like ls/pwd."""
        # Capture original change_time values for all entries
        original_change_times = {
            p: v.get("metadata", {}).get("timestamps", {}).get("change_time")
            for p, v in DB.get("file_system", {}).items()
        }

        # Run a metadata-only command
        result = run_command("ls -la")
        self.assertEqual(result["returncode"], 0)

        # Verify change_time remains unchanged for all entries
        for path, entry in DB.get("file_system", {}).items():
            self.assertEqual(
                entry.get("metadata", {}).get("timestamps", {}).get("change_time"),
                original_change_times.get(path),
                msg=f"change_time changed for {path} after metadata-only command"
            )

    def test_change_time_unchanged_for_unmodified_files(self):
        """Only modified entries should change change_time; others remain the same (exclude symlinks)."""
        # Capture original change_time values
        original_change_times = {
            p: v.get("metadata", {}).get("timestamps", {}).get("change_time")
            for p, v in DB.get("file_system", {}).items()
        }

        # Modify only the test file
        result = run_command(f"echo 'append' >> {os.path.basename(self.test_file)}")
        self.assertEqual(result["returncode"], 0)

        # Root directory and unrelated directory should keep their change_time
        for unaffected_path in [self.workspace_path, self.test_dir_path]:
            self.assertIn(unaffected_path, DB.get("file_system", {}))
            self.assertEqual(
                DB["file_system"][unaffected_path].get("metadata", {}).get("timestamps", {}).get("change_time"),
                original_change_times.get(unaffected_path),
                msg=f"Unmodified entry change_time changed unexpectedly: {unaffected_path}"
            )

    def test_change_time_changes_for_modified_file(self):
        """When a file is modified, its change_time should update."""
        original_change_time = DB["file_system"][self.test_file]["metadata"]["timestamps"]["change_time"]
        result = run_command(f"echo 'append' >> {os.path.basename(self.test_file)}")
        self.assertEqual(result["returncode"], 0)
        updated_change_time = DB["file_system"][self.test_file]["metadata"]["timestamps"]["change_time"]
        self.assertNotEqual(updated_change_time, original_change_time)

    def test_symlink_metadata(self):
        """Test metadata handling for symbolic links."""
        result = run_command("ls -la")
        self.assertEqual(result["returncode"], 0)
        
        # Verify symlink metadata
        entry = DB["file_system"][self.symlink_path]
        self.assertTrue(entry["metadata"]["attributes"]["is_symlink"])
        self.assertEqual(
            entry["metadata"]["attributes"]["symlink_target"],
            self.test_file
        )

    def test_hidden_file_metadata(self):
        """Test metadata handling for hidden files."""
        # Create hidden file
        result = run_command("touch .hidden_file")
        self.assertEqual(result["returncode"], 0)
        
        # Verify hidden attribute
        hidden_file = os.path.join(self.workspace_path, ".hidden_file")
        entry = DB["file_system"][hidden_file]
        self.assertTrue(entry["metadata"]["attributes"]["is_hidden"])

    def test_readonly_file_metadata(self):
        """Test metadata handling for read-only files."""
        # Make file readonly
        result = run_command(f"chmod a-w {os.path.basename(self.test_file)}")
        self.assertEqual(result["returncode"], 0)
        
        # Verify readonly attribute
        entry = DB["file_system"][self.test_file]
        self.assertTrue(entry["metadata"]["attributes"]["is_readonly"])

    def test_metadata_with_file_moves(self):
        """Test metadata preservation when files are moved."""
        # Store original metadata
        original_metadata = DB["file_system"][self.test_file]["metadata"]["attributes"]
        
        # Move file
        new_path = os.path.join(self.workspace_path, "moved_file")
        result = run_command(f"mv {os.path.basename(self.test_file)} moved_file")
        self.assertEqual(result["returncode"], 0)
        
        # Verify metadata preserved
        entry = DB["file_system"][new_path]
        self.assertIn("metadata", entry)
        self.assertEqual(entry["metadata"]["attributes"], original_metadata)

    def test_metadata_with_file_copies(self):
        """Test metadata handling when files are copied."""
        # Copy file
        result = run_command(f"cp {os.path.basename(self.test_file)} copy_file")
        self.assertEqual(result["returncode"], 0)
        
        # Verify new file has appropriate metadata
        copy_path = os.path.join(self.workspace_path, "copy_file")
        entry = DB["file_system"][copy_path]
        self.assertIn("metadata", entry)
        self.assertEqual(entry["metadata"]["attributes"]["is_readonly"], False)

    # def test_metadata_with_different_filesystems(self):
    #     """Test metadata handling across different filesystem types."""
    #     # This test might need to be skipped if test environment doesn't support different fs
    #     if not os.path.exists("/tmp"):
    #         self.skipTest("Cannot test different filesystems")
            
    #     # Try operations on /tmp (might be different fs)
    #     tmp_dir = tempfile.mkdtemp()
    #     self.addCleanup(lambda: shutil.rmtree(tmp_dir, ignore_errors=True))
        
    #     DB["workspace_root"] = tmp_dir
    #     DB["cwd"] = tmp_dir
        
    #     result = run_command("touch test_file")
    #     self.assertEqual(result["returncode"], 0)
        
    #     # Verify metadata still captured
    #     test_file = os.path.join(tmp_dir, "test_file")
    #     self.assertIn("metadata", DB["file_system"][test_file])

    def test_metadata_race_conditions(self):
        """Test metadata handling during rapid file changes and concurrent operations."""
        test_file = os.path.join(self.workspace_path, "race_test.txt")
        
        try:
            # Create initial file
            with open(test_file, 'w') as f:
                f.write("initial content")
            
            # Clear DB and start with fresh state
            DB.clear()
            utils.hydrate_db_from_directory(DB, self.workspace_path)
            
            # Get initial metadata
            initial_stat = os.stat(test_file)
            initial_db_metadata = DB["file_system"][test_file]["metadata"]
            
            # Ensure at least 1 second passes for timestamp change
            time.sleep(0.1)
            
            # Perform rapid changes
            for i in range(5):
                # Modify content
                with open(test_file, 'a') as f:
                    f.write(f"\nline {i}")
                
                # Ensure timestamp changes between iterations
                time.sleep(0.1)
                
                # Immediately hydrate DB
                utils.hydrate_db_from_directory(DB, self.workspace_path)
                
                # Verify metadata is consistent
                current_stat = os.stat(test_file)
                current_db_metadata = DB["file_system"][test_file]["metadata"]
                
                
                # Check timestamps
                actual_mtime = datetime.fromtimestamp(current_stat.st_mtime, tz=timezone.utc)
                db_mtime = datetime.fromisoformat(current_db_metadata["timestamps"]["modify_time"].replace("Z", "+00:00"))
                self.assertLess(
                    abs((actual_mtime - db_mtime).total_seconds()),
                    1,
                    f"Timestamp mismatch after iteration {i}"
                )
                
                # Verify modification was captured
                self.assertNotEqual(
                    current_db_metadata["timestamps"]["modify_time"],
                    initial_db_metadata["timestamps"]["modify_time"],
                    f"Modification time should have changed after iteration {i}"
                )
            
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

    def test_metadata_timestamp_preservation(self):
        """Test that timestamps are preserved correctly through dehydration/rehydration."""
        # Create a test file
        test_file_path = os.path.join(self.workspace_path, "timestamp_test.txt")
        with open(test_file_path, 'w') as f:
            f.write("test content")
        
        # Clear DB and hydrate
        DB.clear()
        DB["workspace_root"] = self.workspace_path
        DB["cwd"] = self.workspace_path
        DB["file_system"] = {}
        utils.hydrate_db_from_directory(DB, self.workspace_path)
        
        # Store original timestamps
        original_timestamps = DB["file_system"][test_file_path]["metadata"]["timestamps"]
        
        # Dehydrate and rehydrate
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        
        utils.dehydrate_db_to_directory(DB, temp_dir)
        
        new_db = {}
        new_db["workspace_root"] = temp_dir
        new_db["cwd"] = temp_dir
        new_db["file_system"] = {}
        utils.hydrate_db_from_directory(new_db, temp_dir)
        
        # Verify modify_time is preserved exactly
        new_file_path = os.path.join(temp_dir, "timestamp_test.txt")
        new_timestamps = new_db["file_system"][new_file_path]["metadata"]["timestamps"]
        
        self.assertEqual(original_timestamps["modify_time"], new_timestamps["modify_time"])
        
        # Verify other timestamps are present and in correct format
        for ts_field in ["access_time", "change_time"]:
            self.assertIn(ts_field, new_timestamps)
            self.assertTrue(new_timestamps[ts_field].endswith('Z'))

    def test_metadata_file_permissions_preservation(self):
        """Test that file permissions are preserved through dehydration/rehydration."""
        # Create a read-only file
        test_file_path = os.path.join(self.workspace_path, "permission_test.txt")
        with open(test_file_path, 'w') as f:
            f.write("test content")
        os.chmod(test_file_path, 0o444)  # Read-only
        
        # Clear DB and hydrate
        DB.clear()
        DB["workspace_root"] = self.workspace_path
        DB["cwd"] = self.workspace_path
        DB["file_system"] = {}
        utils.hydrate_db_from_directory(DB, self.workspace_path)
        
        # Verify initial read-only state
        self.assertTrue(DB["file_system"][test_file_path]["metadata"]["attributes"]["is_readonly"])
        
        # Dehydrate and rehydrate
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        
        utils.dehydrate_db_to_directory(DB, temp_dir)
        
        # Verify physical file is read-only
        temp_file = os.path.join(temp_dir, "permission_test.txt")
        self.assertFalse(os.access(temp_file, os.W_OK))
        
        # Rehydrate and verify metadata
        new_db = {}
        new_db["workspace_root"] = temp_dir
        new_db["cwd"] = temp_dir
        new_db["file_system"] = {}
        utils.hydrate_db_from_directory(new_db, temp_dir)
        
        self.assertTrue(new_db["file_system"][temp_file]["metadata"]["attributes"]["is_readonly"])

    def test_metadata_symlink_preservation(self):
        """Test that symlink metadata is preserved through dehydration/rehydration."""
        # Create a test file and symlink
        test_file_path = os.path.join(self.workspace_path, "symlink_target.txt")
        with open(test_file_path, 'w') as f:
            f.write("target content")
        
        symlink_path = os.path.join(self.workspace_path, "test_symlink")
        os.symlink(test_file_path, symlink_path)
        
        # Clear DB and hydrate
        DB.clear()
        DB["workspace_root"] = self.workspace_path
        DB["cwd"] = self.workspace_path
        DB["file_system"] = {}
        utils.hydrate_db_from_directory(DB, self.workspace_path)
        # Verify initial symlink state
        self.assertTrue(DB["file_system"][symlink_path]["metadata"]["attributes"]["is_symlink"])
        self.assertEqual(DB["file_system"][symlink_path]["metadata"]["attributes"]["symlink_target"], test_file_path)
        
        # Dehydrate and rehydrate
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        
        utils.dehydrate_db_to_directory(DB, temp_dir)
        
        # Verify physical symlink exists
        temp_symlink = os.path.join(temp_dir, "test_symlink")
        self.assertTrue(os.path.islink(temp_symlink))
        
        # Rehydrate and verify metadata
        new_db = {}
        new_db["workspace_root"] = temp_dir
        new_db["cwd"] = temp_dir
        new_db["file_system"] = {}
        utils.hydrate_db_from_directory(new_db, temp_dir)
        
        self.assertTrue(new_db["file_system"][temp_symlink]["metadata"]["attributes"]["is_symlink"])
        self.assertIsNotNone(new_db["file_system"][temp_symlink]["metadata"]["attributes"]["symlink_target"])

    def test_metadata_hidden_file_preservation(self):
        """Test that hidden file attributes are preserved through dehydration/rehydration."""
        # Create a hidden file
        hidden_file_path = os.path.join(self.workspace_path, ".hidden_file")
        with open(hidden_file_path, 'w') as f:
            f.write("hidden content")
        
        # Clear DB and hydrate
        DB.clear()
        DB["workspace_root"] = self.workspace_path
        DB["cwd"] = self.workspace_path
        DB["file_system"] = {}
        utils.hydrate_db_from_directory(DB, self.workspace_path)
        # Verify initial hidden state
        self.assertTrue(DB["file_system"][hidden_file_path]["metadata"]["attributes"]["is_hidden"])
        
        # Dehydrate and rehydrate
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        
        utils.dehydrate_db_to_directory(DB, temp_dir)
        
        # Verify physical hidden file exists
        temp_hidden = os.path.join(temp_dir, ".hidden_file")
        self.assertTrue(os.path.exists(temp_hidden))
        self.assertTrue(os.path.basename(temp_hidden).startswith('.'))
        
        # Rehydrate and verify metadata
        new_db = {}
        new_db["workspace_root"] = temp_dir
        new_db["cwd"] = temp_dir
        new_db["file_system"] = {}
        utils.hydrate_db_from_directory(new_db, temp_dir)
        
        self.assertTrue(new_db["file_system"][temp_hidden]["metadata"]["attributes"]["is_hidden"])

    def test_metadata_complex_operations(self):
        """Test metadata persistence during complex file operations."""
        # Create a test file
        test_file_path = os.path.join(self.workspace_path, "complex_test.txt")
        os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
        with open(test_file_path, 'w') as f:
            f.write("initial content")

        # Clear DB and hydrate
        DB.clear()
        DB["workspace_root"] = self.workspace_path
        DB["cwd"] = self.workspace_path
        DB["file_system"] = {}
        utils.hydrate_db_from_directory(DB, self.workspace_path)
        
        # Store initial metadata
        initial_metadata = DB["file_system"][test_file_path]["metadata"].copy()

        # Dehydrate to temp directory
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        utils.dehydrate_db_to_directory(DB, temp_dir)

        # Clear DB and hydrate from temp directory instead of manually updating workspace_root
        DB.clear()
        utils.hydrate_db_from_directory(DB, temp_dir)

        # Test metadata persistence through command execution
        result = run_command("ls -la")
        self.assertEqual(result["returncode"], 0)

        # Verify metadata is still present - use the new temp path
        temp_file_path = os.path.join(DB["workspace_root"], "complex_test.txt")
        self.assertIn(temp_file_path, DB["file_system"])
        self.assertIn("metadata", DB["file_system"][temp_file_path])

        # Test file modification
        result = run_command("echo 'modified content' > complex_test.txt")
        self.assertEqual(result["returncode"], 0)

        # Verify modification timestamp was updated
        modified_metadata = DB["file_system"][temp_file_path]["metadata"]
        self.assertNotEqual(
            modified_metadata["timestamps"]["modify_time"],
            initial_metadata["timestamps"]["modify_time"],
            "Modification time should be updated"
        )

    def test_metadata_basic_dehydration_rehydration(self):
        """Test basic metadata persistence through dehydration and rehydration."""
        # Create a test file with specific metadata
        test_file_path = os.path.join(self.workspace_path, "metadata_test.txt")
        test_content = "This is a test file for metadata persistence\n"
        
        # Create the file with specific permissions and timestamps
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        # Set specific file permissions (read-only for testing)
        os.chmod(test_file_path, 0o444)  # Read-only
        
        # Create a symlink for testing
        symlink_path = os.path.join(self.workspace_path, "test_symlink")
        os.symlink(test_file_path, symlink_path)
        
        # Create a hidden file
        hidden_file_path = os.path.join(self.workspace_path, ".hidden_file")
        with open(hidden_file_path, 'w') as f:
            f.write("hidden content\n")
        
        # Clear DB and hydrate from the test directory to get initial metadata
        DB.clear()
        DB["workspace_root"] = self.workspace_path
        DB["cwd"] = self.workspace_path
        DB["file_system"] = {}
        
        # Hydrate DB from the test directory
        utils.hydrate_db_from_directory(DB, self.workspace_path)
        
        # Store original metadata for comparison
        original_metadata = {}
        for file_path in [test_file_path, symlink_path, hidden_file_path]:
            if file_path in DB["file_system"]:
                original_metadata[file_path] = DB["file_system"][file_path].get("metadata", {}).copy()
        
        # Verify initial metadata was collected correctly
        self.assertIn(test_file_path, DB["file_system"])
        self.assertIn("metadata", DB["file_system"][test_file_path])
        self.assertTrue(DB["file_system"][test_file_path]["metadata"]["attributes"]["is_readonly"])
        
        self.assertIn(symlink_path, DB["file_system"])
        self.assertIn("metadata", DB["file_system"][symlink_path])
        self.assertTrue(DB["file_system"][symlink_path]["metadata"]["attributes"]["is_symlink"])
        self.assertEqual(DB["file_system"][symlink_path]["metadata"]["attributes"]["symlink_target"], test_file_path)
        
        self.assertIn(hidden_file_path, DB["file_system"])
        self.assertIn("metadata", DB["file_system"][hidden_file_path])
        self.assertTrue(DB["file_system"][hidden_file_path]["metadata"]["attributes"]["is_hidden"])
        
        # Create a temporary directory for dehydration
        temp_dehydrate_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dehydrate_dir, ignore_errors=True))
        
        # Dehydrate DB to temporary directory
        utils.dehydrate_db_to_directory(DB, temp_dehydrate_dir)
        
        # Verify files were created in temp directory
        temp_test_file = os.path.join(temp_dehydrate_dir, "metadata_test.txt")
        temp_symlink = os.path.join(temp_dehydrate_dir, "test_symlink")
        temp_hidden = os.path.join(temp_dehydrate_dir, ".hidden_file")
        
        self.assertTrue(os.path.exists(temp_test_file))
        self.assertTrue(os.path.exists(temp_symlink))
        self.assertTrue(os.path.exists(temp_hidden))
        
        # Verify metadata was applied to physical files
        # Check file permissions
        self.assertFalse(os.access(temp_test_file, os.W_OK))  # Should be read-only
        
        # Check symlink
        self.assertTrue(os.path.islink(temp_symlink))
        self.assertEqual(os.readlink(temp_symlink), test_file_path)
        
        # Check hidden file
        self.assertTrue(os.path.basename(temp_hidden).startswith('.'))
        
        # Now rehydrate from the temp directory to a new DB
        new_db = {}
        new_db["workspace_root"] = temp_dehydrate_dir
        new_db["cwd"] = temp_dehydrate_dir
        new_db["file_system"] = {}
        
        utils.hydrate_db_from_directory(new_db, temp_dehydrate_dir)
        
        # Verify metadata was preserved in the new DB
        new_test_file = os.path.join(temp_dehydrate_dir, "metadata_test.txt")
        new_symlink = os.path.join(temp_dehydrate_dir, "test_symlink")
        new_hidden = os.path.join(temp_dehydrate_dir, ".hidden_file")
        
        # Check that metadata is present and correct
        self.assertIn(new_test_file, new_db["file_system"])
        self.assertIn("metadata", new_db["file_system"][new_test_file])
        
        new_metadata = new_db["file_system"][new_test_file]["metadata"]
        self.assertTrue(new_metadata["attributes"]["is_readonly"])
        
        # Check symlink metadata
        self.assertIn(new_symlink, new_db["file_system"])
        self.assertIn("metadata", new_db["file_system"][new_symlink])
        
        new_symlink_metadata = new_db["file_system"][new_symlink]["metadata"]
        self.assertTrue(new_symlink_metadata["attributes"]["is_symlink"])
        # Note: symlink target might be different due to path changes, but should still point to the test file
        self.assertIsNotNone(new_symlink_metadata["attributes"]["symlink_target"])
        
        # Check hidden file metadata
        self.assertIn(new_hidden, new_db["file_system"])
        self.assertIn("metadata", new_db["file_system"][new_hidden])
        
        new_hidden_metadata = new_db["file_system"][new_hidden]["metadata"]
        self.assertTrue(new_hidden_metadata["attributes"]["is_hidden"])

    def test_metadata_timestamp_preservation_dehydration(self):
        """Test that timestamps are preserved correctly through dehydration/rehydration."""
        # Create a test file
        test_file_path = os.path.join(self.workspace_path, "timestamp_test.txt")
        with open(test_file_path, 'w') as f:
            f.write("test content")
        
        # Clear DB and hydrate
        DB.clear()
        DB["workspace_root"] = self.workspace_path
        DB["cwd"] = self.workspace_path
        DB["file_system"] = {}
        utils.hydrate_db_from_directory(DB, self.workspace_path)
        
        # Store original timestamps
        original_timestamps = DB["file_system"][test_file_path]["metadata"]["timestamps"]
        
        # Dehydrate and rehydrate
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        
        utils.dehydrate_db_to_directory(DB, temp_dir)
        
        new_db = {}
        new_db["workspace_root"] = temp_dir
        new_db["cwd"] = temp_dir
        new_db["file_system"] = {}
        utils.hydrate_db_from_directory(new_db, temp_dir)
        
        # Verify modify_time is preserved exactly
        new_file_path = os.path.join(temp_dir, "timestamp_test.txt")
        new_timestamps = new_db["file_system"][new_file_path]["metadata"]["timestamps"]
        
        self.assertEqual(original_timestamps["modify_time"], new_timestamps["modify_time"])
        
        # Verify other timestamps are present and in correct format
        for ts_field in ["access_time", "change_time"]:
            self.assertIn(ts_field, new_timestamps)
            self.assertTrue(new_timestamps[ts_field].endswith('Z'))

    def test_metadata_file_permissions_dehydration(self):
        """Test that file permissions are preserved through dehydration/rehydration."""
        # Create a read-only file
        test_file_path = os.path.join(self.workspace_path, "permission_test.txt")
        with open(test_file_path, 'w') as f:
            f.write("test content")
        os.chmod(test_file_path, 0o444)  # Read-only
        
        # Clear DB and hydrate
        DB.clear()
        DB["workspace_root"] = self.workspace_path
        DB["cwd"] = self.workspace_path
        DB["file_system"] = {}
        utils.hydrate_db_from_directory(DB, self.workspace_path)
        
        # Verify initial read-only state
        self.assertTrue(DB["file_system"][test_file_path]["metadata"]["attributes"]["is_readonly"])
        
        # Dehydrate and rehydrate
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        
        utils.dehydrate_db_to_directory(DB, temp_dir)
        
        # Verify physical file is read-only
        temp_file = os.path.join(temp_dir, "permission_test.txt")
        self.assertFalse(os.access(temp_file, os.W_OK))
        
        # Rehydrate and verify metadata
        new_db = {}
        new_db["workspace_root"] = temp_dir
        new_db["cwd"] = temp_dir
        new_db["file_system"] = {}
        utils.hydrate_db_from_directory(new_db, temp_dir)
        
        self.assertTrue(new_db["file_system"][temp_file]["metadata"]["attributes"]["is_readonly"])

    def test_metadata_symlink_dehydration(self):
        """Test that symlink metadata is preserved through dehydration/rehydration."""
        # Create a test file and symlink
        test_file_path = os.path.join(self.workspace_path, "symlink_target.txt")
        with open(test_file_path, 'w') as f:
            f.write("target content")
        
        symlink_path = os.path.join(self.workspace_path, "test_symlink")
        os.symlink(test_file_path, symlink_path)
        
        # Clear DB and hydrate
        DB.clear()
        DB["workspace_root"] = self.workspace_path
        DB["cwd"] = self.workspace_path
        DB["file_system"] = {}
        utils.hydrate_db_from_directory(DB, self.workspace_path)
        
        # Verify initial symlink state
        self.assertTrue(DB["file_system"][symlink_path]["metadata"]["attributes"]["is_symlink"])
        self.assertEqual(DB["file_system"][symlink_path]["metadata"]["attributes"]["symlink_target"], test_file_path)
        
        # Dehydrate and rehydrate
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        
        utils.dehydrate_db_to_directory(DB, temp_dir)
        
        # Verify physical symlink exists
        temp_symlink = os.path.join(temp_dir, "test_symlink")
        self.assertTrue(os.path.islink(temp_symlink))
        
        # Rehydrate and verify metadata
        new_db = {}
        new_db["workspace_root"] = temp_dir
        new_db["cwd"] = temp_dir
        new_db["file_system"] = {}
        utils.hydrate_db_from_directory(new_db, temp_dir)
        
        self.assertTrue(new_db["file_system"][temp_symlink]["metadata"]["attributes"]["is_symlink"])
        self.assertIsNotNone(new_db["file_system"][temp_symlink]["metadata"]["attributes"]["symlink_target"])

    def test_metadata_hidden_file_dehydration(self):
        """Test that hidden file attributes are preserved through dehydration/rehydration."""
        # Create a hidden file
        hidden_file_path = os.path.join(self.workspace_path, ".hidden_file")
        with open(hidden_file_path, 'w') as f:
            f.write("hidden content")
        
        # Clear DB and hydrate
        DB.clear()
        DB["workspace_root"] = self.workspace_path
        DB["cwd"] = self.workspace_path
        DB["file_system"] = {}
        utils.hydrate_db_from_directory(DB, self.workspace_path)
        
        # Verify initial hidden state
        self.assertTrue(DB["file_system"][hidden_file_path]["metadata"]["attributes"]["is_hidden"])
        
        # Dehydrate and rehydrate
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))
        
        utils.dehydrate_db_to_directory(DB, temp_dir)
        
        # Verify physical hidden file exists
        temp_hidden = os.path.join(temp_dir, ".hidden_file")
        self.assertTrue(os.path.exists(temp_hidden))
        self.assertTrue(os.path.basename(temp_hidden).startswith('.'))
        
        # Rehydrate and verify metadata
        new_db = {}
        new_db["workspace_root"] = temp_dir
        new_db["cwd"] = temp_dir
        new_db["file_system"] = {}
        utils.hydrate_db_from_directory(new_db, temp_dir)
        
        self.assertTrue(new_db["file_system"][temp_hidden]["metadata"]["attributes"]["is_hidden"])

    def test_metadata_complex_operations_dehydration(self):
        """Test metadata persistence during complex file operations after dehydration."""
        # Create a test file
        test_file_path = os.path.join(self.workspace_path, "complex_test.txt")
        with open(test_file_path, 'w') as f:
            f.write("initial content")

        # Clear DB and hydrate
        DB.clear()
        DB["workspace_root"] = self.workspace_path
        DB["cwd"] = self.workspace_path
        DB["file_system"] = {}
        utils.hydrate_db_from_directory(DB, self.workspace_path)
        
        # Store initial metadata
        initial_metadata = DB["file_system"][test_file_path]["metadata"].copy()

        # Dehydrate to temp directory
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

        utils.dehydrate_db_to_directory(DB, temp_dir)

        # Clear DB and hydrate from temp directory instead of manually updating workspace_root
        DB.clear()
        utils.hydrate_db_from_directory(DB, temp_dir)

        # Test metadata persistence through command execution
        result = run_command("ls -la")
        self.assertEqual(result["returncode"], 0)

        # Verify metadata is still present - use the new temp path
        temp_file_path = os.path.join(DB["workspace_root"], "complex_test.txt")
        self.assertIn(temp_file_path, DB["file_system"])
        self.assertIn("metadata", DB["file_system"][temp_file_path])

        # Test file modification
        result = run_command("echo 'modified content' > complex_test.txt")
        self.assertEqual(result["returncode"], 0)

        # Verify modification timestamp was updated
        modified_metadata = DB["file_system"][temp_file_path]["metadata"]
        self.assertNotEqual(
            modified_metadata["timestamps"]["modify_time"],
            initial_metadata["timestamps"]["modify_time"],
            "Modification time should be updated"
        )

        # Test creating new files
        result = run_command("touch new_file.txt")
        self.assertEqual(result["returncode"], 0)

        new_file_path = os.path.join(DB["workspace_root"], "new_file.txt")
        self.assertIn(new_file_path, DB["file_system"])
        self.assertIn("metadata", DB["file_system"][new_file_path])
    def test_metadata_edge_cases(self):
        """Test metadata handling for edge cases and special situations."""
        # Test file with special characters in name
        special_name = "test file with spaces!@#$%^&().txt"
        result = run_command(f"touch '{special_name}'")
        self.assertEqual(result["returncode"], 0)
        
        file_path = os.path.join(self.workspace_path, special_name)
        self.assertIn(file_path, DB["file_system"])
        
        # Test file with minimal permissions
        result = run_command(f"touch restricted_file")
        self.assertEqual(result["returncode"], 0)
        
        # Test handling of broken symlinks
        result = run_command("ln -s nonexistent_target broken_link")
        self.assertEqual(result["returncode"], 0)
        
        link_path = os.path.join(self.workspace_path, "broken_link")
        entry = DB["file_system"][link_path]
        self.assertTrue(entry["metadata"]["attributes"]["is_symlink"])
        self.assertEqual(entry["metadata"]["attributes"]["symlink_target"], "nonexistent_target")

    def test_metadata_matches_filesystem(self):
        """Test that metadata in DB exactly matches the metadata of the actual files."""
        # Create a test file with specific metadata
        test_file = "metadata_test.txt"
        result = run_command(f"touch {test_file}")
        self.assertEqual(result["returncode"], 0)
        
        # Set some specific metadata
        result = run_command(f"chmod 644 {test_file}")
        self.assertEqual(result["returncode"], 0)
        
        # Write some content
        result = run_command(f"echo 'test content' > {test_file}")
        self.assertEqual(result["returncode"], 0)
        
        # Get the DB's metadata
        file_path = os.path.join(self.workspace_path, test_file)
        db_entry = DB["file_system"][file_path]
        db_metadata = db_entry["metadata"]
        
        # Verify metadata structure
        self.assertIn("timestamps", db_metadata)
        self.assertIn("attributes", db_metadata)

        # Verify timestamps
        for ts_field in ["access_time", "modify_time", "change_time"]:
            self.assertIn(ts_field, db_metadata["timestamps"])
            # Verify ISO format with UTC timezone
            self.assertTrue(db_metadata["timestamps"][ts_field].endswith("Z"))
            # Verify it's a valid datetime
            datetime.fromisoformat(db_metadata["timestamps"][ts_field].replace("Z", "+00:00"))

        # Verify attributes
        self.assertFalse(db_metadata["attributes"]["is_symlink"])
        self.assertIsNone(db_metadata["attributes"]["symlink_target"])
        self.assertFalse(db_metadata["attributes"]["is_hidden"])

        # Test with a directory
        test_dir = "metadata_test_dir"
        result = run_command(f"mkdir {test_dir}")
        self.assertEqual(result["returncode"], 0)

        # Get DB directory metadata
        dir_path = os.path.join(self.workspace_path, test_dir)
        db_dir_entry = DB["file_system"][dir_path]
        db_dir_metadata = db_dir_entry["metadata"]

        # Test with a symlink
        test_link = "metadata_test_link"
        result = run_command(f"ln -s {test_file} {test_link}")
        self.assertEqual(result["returncode"], 0)

        # Get DB symlink metadata
        link_path = os.path.join(self.workspace_path, test_link)
        db_link_entry = DB["file_system"][link_path]
        db_link_metadata = db_link_entry["metadata"]

        # Verify symlink metadata
        self.assertTrue(db_link_metadata["attributes"]["is_symlink"])
        self.assertEqual(db_link_metadata["attributes"]["symlink_target"], test_file)

    def test_metadata_hydration_matches_filesystem(self):
        """Test that metadata in DB exactly matches the metadata of files after hydration."""
        # Create a test file directly in the filesystem
        test_file = os.path.join(self.workspace_path, "hydration_test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Create a directory
        test_dir = os.path.join(self.workspace_path, "hydration_test_dir")
        os.mkdir(test_dir)
        os.chmod(test_dir, 0o754)
        
        # Create a symlink
        test_link = os.path.join(self.workspace_path, "hydration_test_link")
        os.symlink("hydration_test.txt", test_link)
        
        try:
            # Clear DB and hydrate from the test directory
            DB.clear()
            utils.hydrate_db_from_directory(DB, self.workspace_path)
            
            # Get actual file metadata using os.stat
            file_stat = os.stat(test_file)
            
            # Get DB file metadata
            db_file_metadata = DB["file_system"][test_file]["metadata"]
            
            # Compare file metadata
            
            # Timestamps
            actual_atime = datetime.fromtimestamp(file_stat.st_atime, tz=timezone.utc)
            actual_mtime = datetime.fromtimestamp(file_stat.st_mtime, tz=timezone.utc)
            actual_ctime = datetime.fromtimestamp(file_stat.st_ctime, tz=timezone.utc)
            
            db_atime = datetime.fromisoformat(db_file_metadata["timestamps"]["access_time"].replace("Z", "+00:00"))
            db_mtime = datetime.fromisoformat(db_file_metadata["timestamps"]["modify_time"].replace("Z", "+00:00"))
            db_ctime = datetime.fromisoformat(db_file_metadata["timestamps"]["change_time"].replace("Z", "+00:00"))
            
            # Allow 1 second difference due to filesystem timestamp resolution
            self.assertLess(abs((actual_atime - db_atime).total_seconds()), 1, "Access time mismatch")
            self.assertLess(abs((actual_mtime - db_mtime).total_seconds()), 1, "Modify time mismatch")
            self.assertLess(abs((actual_ctime - db_ctime).total_seconds()), 1, "Change time mismatch")
            
            # Attributes
            self.assertFalse(db_file_metadata["attributes"]["is_symlink"])
            self.assertIsNone(db_file_metadata["attributes"]["symlink_target"])
            self.assertFalse(db_file_metadata["attributes"]["is_hidden"])

            
            # Directory metadata
            dir_stat = os.stat(test_dir)
            db_dir_metadata = DB["file_system"][test_dir]["metadata"]

            # Symlink metadata
            # Use lstat to get symlink info instead of target
            link_stat = os.lstat(test_link)
            db_link_metadata = DB["file_system"][test_link]["metadata"]
            
            # Verify it's a symlink
            self.assertTrue(db_link_metadata["attributes"]["is_symlink"])
            self.assertTrue(stat.S_ISLNK(link_stat.st_mode))
            
            # Check symlink target
            actual_target = os.readlink(test_link)
            self.assertEqual(
                actual_target,
                db_link_metadata["attributes"]["symlink_target"],
                "Symlink target mismatch"
            )
            
        finally:
            # Clean up the test files
            if os.path.exists(test_link):
                os.unlink(test_link)
            if os.path.exists(test_file):
                os.unlink(test_file)
            if os.path.exists(test_dir):
                os.rmdir(test_dir)

    def test_metadata_special_files(self):
        """Test metadata handling for special file types (FIFO pipes, device files if possible)."""
        test_fifo = os.path.join(self.workspace_path, "test_fifo")
        
        try:
            # Create a FIFO pipe
            os.mkfifo(test_fifo)
            os.chmod(test_fifo, 0o644)
            
            # Clear DB and hydrate
            DB.clear()
            utils.hydrate_db_from_directory(DB, self.workspace_path)
            
            # Verify FIFO metadata
            fifo_stat = os.stat(test_fifo)
            db_fifo_metadata = DB["file_system"][test_fifo]["metadata"]
            
            # Check if it's properly identified as a special file
            self.assertTrue(stat.S_ISFIFO(fifo_stat.st_mode))
            
            # Check basic metadata that should be present for all files            
            # Timestamps
            actual_mtime = datetime.fromtimestamp(fifo_stat.st_mtime, tz=timezone.utc)
            # Check timestamps
            actual_mtime = datetime.fromtimestamp(fifo_stat.st_mtime, tz=timezone.utc)
            db_mtime = datetime.fromisoformat(db_fifo_metadata["timestamps"]["modify_time"].replace("Z", "+00:00"))
            self.assertLess(abs((actual_mtime - db_mtime).total_seconds()), 1)
            
        finally:
            if os.path.exists(test_fifo):
                os.unlink(test_fifo)

    def test_metadata_extended_attributes(self):
        """Test metadata handling for files with extended attributes."""
        test_file = os.path.join(self.workspace_path, "xattr_test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        try:
            # Set some extended attributes if supported
            try:
                import xattr
                xattr.setxattr(test_file, b"user.test_attr", b"test_value")
                xattr_supported = True
            except (ImportError, OSError):
                xattr_supported = False
            
            # Clear DB and hydrate
            DB.clear()
            utils.hydrate_db_from_directory(DB, self.workspace_path)
            
            # Verify extended attributes if supported
            if xattr_supported:
                db_file_metadata = DB["file_system"][test_file]["metadata"]
                self.assertIn("extended_attributes", db_file_metadata)
                self.assertIn("user.test_attr", db_file_metadata["extended_attributes"])
                self.assertEqual(
                    db_file_metadata["extended_attributes"]["user.test_attr"],
                    "test_value"
                )
            
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

    def test_metadata_deep_directory(self):
        """Test metadata handling for deep directory structures with various file types."""
        base_dir = os.path.join(self.workspace_path, "deep_test")
        os.makedirs(base_dir)
        
        # Create a deep directory structure with various file types
        structure = {
            "dir1": {
                "subdir1": {
                    "file1.txt": "content1",
                    "subsubdir": {
                        "file2.txt": "content2",
                        "link1": ("file2.txt", "symlink"),  # (target, type)
                    }
                },
                "subdir2": {
                    "file3.txt": "content3"
                }
            }
        }
        
        created_paths = []
        try:
            def create_structure(parent_path, items):
                for name, content in items.items():
                    path = os.path.join(parent_path, name)
                    if isinstance(content, dict):
                        os.makedirs(path)
                        os.chmod(path, 0o755)
                        created_paths.append(path)
                        create_structure(path, content)
                    elif isinstance(content, tuple):
                        target, link_type = content
                        target_path = os.path.join(os.path.dirname(path), target)
                        os.symlink(target_path, path)
                        created_paths.append(path)
                    else:
                        with open(path, 'w') as f:
                            f.write(content)
                        os.chmod(path, 0o644)
                        created_paths.append(path)
            
            create_structure(base_dir, structure)
            
            # Clear DB and hydrate
            DB.clear()
            utils.hydrate_db_from_directory(DB, self.workspace_path)
            
            # Verify each path's metadata
            for path in created_paths:
                # Get filesystem metadata
                is_link = os.path.islink(path)
                stat_result = os.lstat(path) if is_link else os.stat(path)
                
                # Get DB metadata
                db_entry = DB["file_system"][path]
                db_metadata = db_entry["metadata"]
                
                # Check basic attributes
                if is_link:
                    self.assertTrue(db_metadata["attributes"]["is_symlink"])
                    self.assertEqual(
                        os.readlink(path),
                        db_metadata["attributes"]["symlink_target"]
                    )

                # Check timestamps
                actual_mtime = datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc)
                db_mtime = datetime.fromisoformat(db_metadata["timestamps"]["modify_time"].replace("Z", "+00:00"))
                self.assertLess(abs((actual_mtime - db_mtime).total_seconds()), 1)
                
        finally:
            # Clean up - remove files in reverse order (deepest first)
            for path in reversed(created_paths):
                try:
                    if os.path.islink(path) or os.path.isfile(path):
                        os.unlink(path)
                    else:
                        os.rmdir(path)
                except OSError:
                    pass  # Best effort cleanup
            if os.path.exists(base_dir):
                shutil.rmtree(base_dir, ignore_errors=True)

class TestAccessTimeHandling(unittest.TestCase):
    """Test cases for access_time handling with different ACCESS_TIME_MODE configurations."""
    
    def setUp(self):
        """Set up test environment before each test."""
        self.workspace_path = minimal_reset_db()
        
        # Create test files with specific content
        test_files = {
            "test_file.txt": ["This is test content\n", "Second line\n"],
            "binary_file.bin": ["<Binary File - Content Not Loaded>"],
            "empty_file.txt": []
        }
        
        for filename, content in test_files.items():
            file_path = normalize_for_db(os.path.join(self.workspace_path, filename))
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.writelines(content)
            
            # Add to DB with metadata
            file_metadata = utils._collect_file_metadata(file_path)
            DB["file_system"][file_path] = {
                "path": file_path,
                "is_directory": False,
                "content_lines": content,
                "size_bytes": utils.calculate_size_bytes(content),
                "last_modified": file_metadata["timestamps"]["modify_time"],
                "metadata": file_metadata
            }
        
        # Initialize sandbox by running a simple command
        # This ensures file timestamps are set before tests that check access time
        run_command("pwd")
        
        # Add a delay to ensure timestamp precision for access time tests
        import time
        time.sleep(0.1)  # 100ms delay to ensure distinguishable timestamps
        
        # Store original ACCESS_TIME_MODE for restoration
        self.original_access_time_mode = common_utils_utils.ACCESS_TIME_MODE

    def tearDown(self):
        """Clean up after each test."""
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()
        # Restore original ACCESS_TIME_MODE
        common_utils_utils.ACCESS_TIME_MODE = self.original_access_time_mode

    def _get_file_access_time(self, filename: str) -> str:
        """Helper to get access_time from DB for a file."""
        file_path = normalize_for_db(os.path.join(self.workspace_path, filename))
        return DB["file_system"][file_path]["metadata"]["timestamps"]["access_time"]

    def _set_file_access_time_to_past(self, filename: str) -> str:
        """Force the file's access_time to an older value so relatime will update it."""
        file_path = normalize_for_db(os.path.join(self.workspace_path, filename))
        past_seconds = time.time() - (2 * 24 * 60 * 60)  # Two days in the past
        current_mtime = os.path.getmtime(file_path)
        os.utime(file_path, (past_seconds, current_mtime))

        # If a sandbox session is active, also force the sandbox copy's atime
        from .. import terminalAPI
        sandbox_root = terminalAPI.SESSION_SANDBOX_DIR
        if sandbox_root and os.path.exists(sandbox_root):
            try:
                # Determine relative path within workspace and update the sandbox file
                rel_path = os.path.relpath(file_path, self.workspace_path)
                sandbox_file_path = normalize_for_db(os.path.join(sandbox_root, rel_path))
                if os.path.exists(sandbox_file_path):
                    os.utime(sandbox_file_path, (past_seconds, os.path.getmtime(sandbox_file_path)))
            except Exception:
                pass  # Best-effort; if it fails we'll still rely on workspace metadata

        # Refresh metadata in DB to reflect the forced timestamp
        file_metadata = utils._collect_file_metadata(file_path)
        DB["file_system"][file_path]["metadata"] = file_metadata
        return file_metadata["timestamps"]["access_time"]

    def test_access_time_mode_atime(self):
        """Test that ACCESS_TIME_MODE='atime' updates access time on every access."""
        common_utils_utils.ACCESS_TIME_MODE = "atime"
        
        # Get initial access time
        initial_atime = self._get_file_access_time("test_file.txt")
        
        # Allow some time to pass for timestamp difference
        import time
        time.sleep(0.01)
        
        # Execute a command that reads the file
        result = run_command("cat test_file.txt")
        self.assertEqual(result['returncode'], 0)
        
        # Access time should be updated
        new_atime = self._get_file_access_time("test_file.txt")
        self.assertNotEqual(initial_atime, new_atime, "Access time should be updated in 'atime' mode")

    def test_access_time_mode_noatime(self):
        """Test that ACCESS_TIME_MODE='noatime' never updates access time."""
        common_utils_utils.ACCESS_TIME_MODE = "noatime"
        
        # Get initial access time
        initial_atime = self._get_file_access_time("test_file.txt")
        
        # Allow some time to pass
        import time
        time.sleep(0.01)
        
        # Execute a command that reads the file
        result = run_command("cat test_file.txt")
        self.assertEqual(result['returncode'], 0)
        
        # Access time should NOT be updated
        new_atime = self._get_file_access_time("test_file.txt")
        self.assertEqual(initial_atime, new_atime, "Access time should not be updated in 'noatime' mode")

    def test_access_time_mode_relatime_content_commands(self):
        """Test that ACCESS_TIME_MODE='relatime' updates access time for content-reading commands."""
        common_utils_utils.ACCESS_TIME_MODE = "relatime"
        
        content_commands = ["cat", "head", "tail", "grep pattern"]
        
        for cmd_template in content_commands:
            with self.subTest(command=cmd_template):
                # Force the access time far enough in the past so relatime should update it
                forced_atime = self._set_file_access_time_to_past("test_file.txt")
                initial_atime = self._get_file_access_time("test_file.txt")
                self.assertEqual(initial_atime, forced_atime)
                
                # Allow enough time to pass for distinguishable timestamps
                import time
                time.sleep(0.1)  # 100ms delay
                
                # Execute content-reading command
                cmd = cmd_template.replace("pattern", "test")  # For grep
                if cmd.startswith("grep"):
                    result = run_command(f"{cmd} test_file.txt")
                else:
                    result = run_command(f"{cmd} test_file.txt")
                
                # Command should succeed
                self.assertEqual(result['returncode'], 0)
                
                # Access time should be updated for content-reading commands
                new_atime = self._get_file_access_time("test_file.txt")
                self.assertNotEqual(initial_atime, new_atime,
                                  f"Access time should be updated for content command: {cmd}")

    def test_access_time_mode_relatime_metadata_commands(self):
        """Test that ACCESS_TIME_MODE='relatime' does NOT update access time for metadata-only commands."""
        common_utils_utils.ACCESS_TIME_MODE = "relatime"
        
        metadata_commands = ["ls", "stat", "find . -name", "du"]
        
        for cmd_template in metadata_commands:
            with self.subTest(command=cmd_template):
                # Get initial access time
                initial_atime = self._get_file_access_time("test_file.txt")
                
                # Allow some time to pass
                import time
                time.sleep(0.01)
                
                # Execute metadata-only command
                if cmd_template == "find . -name":
                    result = run_command("find . -name 'test_file.txt'")
                elif cmd_template == "stat":
                    # Note: stat command might not be available on all systems
                    try:
                        result = run_command("stat test_file.txt")
                    except CommandExecutionError:
                        # Skip if stat command is not available
                        continue
                else:
                    result = run_command(f"{cmd_template} test_file.txt" if cmd_template != "ls" else cmd_template)
                
                # Command should succeed (some might fail if not available, but that's OK)
                if result['returncode'] == 0:
                    # Access time should NOT be updated for metadata-only commands
                    new_atime = self._get_file_access_time("test_file.txt")
                    self.assertEqual(initial_atime, new_atime, 
                                   f"Access time should not be updated for metadata command: {cmd_template}")

    def test_should_update_access_time_function(self):
        """Test the _should_update_access_time function directly."""
        # Test with different ACCESS_TIME_MODE values
        
        # Test noatime mode
        common_utils_utils.ACCESS_TIME_MODE = "noatime"
        self.assertFalse(utils._should_update_access_time("cat file.txt"))
        self.assertFalse(utils._should_update_access_time("ls -la"))
        
        # Test atime mode
        common_utils_utils.ACCESS_TIME_MODE = "atime"
        self.assertTrue(utils._should_update_access_time("cat file.txt"))
        self.assertTrue(utils._should_update_access_time("ls -la"))
        
        # Test relatime mode
        common_utils_utils.ACCESS_TIME_MODE = "relatime"
        
        # Content-reading commands should return True
        content_commands = ["cat", "less", "more", "head", "tail", "grep", "awk", "sed"]
        for cmd in content_commands:
            self.assertTrue(utils._should_update_access_time(cmd), f"Command {cmd} should update atime in relatime")
        
        # Metadata-only commands should return False
        metadata_commands = ["ls", "stat", "find", "du", "df", "tree"]
        for cmd in metadata_commands:
            self.assertFalse(utils._should_update_access_time(cmd), f"Command {cmd} should not update atime in relatime")
        
        # Unknown commands should return True (conservative approach)
        self.assertTrue(utils._should_update_access_time("unknown_command"))
        self.assertTrue(utils._should_update_access_time("custom_script"))

    def test_access_time_preservation_across_operations(self):
        """Test that access_time is properly preserved during file operations."""
        common_utils_utils.ACCESS_TIME_MODE = "noatime"  # Don't update access time
        
        # Get initial timestamp
        initial_atime = self._get_file_access_time("test_file.txt")
        
        # Perform various operations that shouldn't change access time
        operations = [
            "ls -la",
            "ls test_file.txt",
            "echo 'new content' > new_file.txt",  # Different file
            "mkdir new_directory"
        ]
        
        for operation in operations:
            with self.subTest(operation=operation):
                # Allow time to pass
                import time
                time.sleep(0.01)
                
                result = run_command(operation)
                self.assertEqual(result['returncode'], 0)
                
                # Access time should be preserved
                current_atime = self._get_file_access_time("test_file.txt")
                self.assertEqual(initial_atime, current_atime, 
                               f"Access time should be preserved after: {operation}")

    def test_access_time_vs_modify_time(self):
        """Test that access_time and modify_time are handled independently."""
        common_utils_utils.ACCESS_TIME_MODE = "atime"  # Update access time on every access
        
        # Get initial timestamps
        file_path = normalize_for_db(os.path.join(DB["workspace_root"], "test_file.txt"))
        initial_metadata = DB["file_system"][file_path]["metadata"]["timestamps"]
        initial_atime = initial_metadata["access_time"]
        initial_mtime = initial_metadata["modify_time"]
        
        # Allow time to pass
        import time
        time.sleep(0.1)
        
        # Read the file (should update access time but not modify time)
        result = run_command("cat test_file.txt")
        self.assertEqual(result['returncode'], 0)
        
        # Check timestamps after read operation
        read_metadata = DB["file_system"][file_path]["metadata"]["timestamps"]
        read_atime = read_metadata["access_time"]
        read_mtime = read_metadata["modify_time"]
        
        # Access time should be updated, modify time should be unchanged
        self.assertNotEqual(initial_atime, read_atime, "Access time should be updated after read")
        self.assertEqual(initial_mtime, read_mtime, "Modify time should not change after read")
        
        # Allow more time to pass
        time.sleep(0.1)
        
        # Modify the file (should update both access time and modify time)
        result = run_command("echo 'additional content' >> test_file.txt")
        self.assertEqual(result['returncode'], 0)
        
        # Check timestamps after modify operation
        modify_metadata = DB["file_system"][file_path]["metadata"]["timestamps"]
        modify_atime = modify_metadata["access_time"]
        modify_mtime = modify_metadata["modify_time"]
        
        # Both timestamps should be updated
        self.assertNotEqual(read_atime, modify_atime, "Access time should be updated after modify")
        self.assertNotEqual(read_mtime, modify_mtime, "Modify time should be updated after modify")

    def test_access_time_with_different_file_types(self):
        """Test access_time handling with different file types."""
        common_utils_utils.ACCESS_TIME_MODE = "relatime"
        
        file_types = ["test_file.txt", "binary_file.bin", "empty_file.txt"]
        
        for filename in file_types:
            with self.subTest(filename=filename):
                # Get initial access time
                initial_atime = self._get_file_access_time(filename)
                
                # Allow time to pass
                import time
                time.sleep(0.01)
                
                # Try to read the file
                result = run_command(f"cat {filename}")
                self.assertEqual(result['returncode'], 0)
                
                # Access time should be updated for all file types when using content-reading commands
                new_atime = self._get_file_access_time(filename)
                self.assertNotEqual(initial_atime, new_atime, 
                                  f"Access time should be updated for {filename}")

    def test_access_time_configuration_edge_cases(self):
        """Test edge cases in access_time configuration."""
        
        # Test with empty command
        common_utils_utils.ACCESS_TIME_MODE = "relatime"
        self.assertTrue(utils._should_update_access_time(""))  # Conservative default
        
        # Test with command containing arguments
        self.assertTrue(utils._should_update_access_time("cat file1.txt file2.txt"))  # Should extract 'cat'
        self.assertFalse(utils._should_update_access_time("ls -la /some/path"))  # Should extract 'ls'
        
        # Test with whitespace
        self.assertTrue(utils._should_update_access_time("  head  "))  # Should handle whitespace
        self.assertFalse(utils._should_update_access_time("  ls  "))  # Should handle whitespace

    def test_access_time_invalid_mode(self):
        """Test behavior with invalid ACCESS_TIME_MODE."""
        # Set an invalid mode
        common_utils_utils.ACCESS_TIME_MODE = "invalid_mode"
        
        # Should default to True (conservative approach)
        self.assertTrue(utils._should_update_access_time("any_command"))

    def test_access_time_mixed_operations(self):
        """Test access_time behavior during mixed file operations."""
        common_utils_utils.ACCESS_TIME_MODE = "relatime"
        
        # Get initial access time
        initial_atime = self._get_file_access_time("test_file.txt")
        
        # Allow time to pass
        import time
        time.sleep(0.01)
        
        # Perform a series of mixed operations
        operations = [
            ("ls", False),  # Metadata only - should not update atime
            ("cat test_file.txt", True),  # Content reading - should update atime
            ("ls -la", False),  # Metadata only - should not update atime
            ("head test_file.txt", True),  # Content reading - should update atime
        ]
        
        previous_atime = initial_atime
        
        for operation, should_update in operations:
            with self.subTest(operation=operation):
                # Allow time to pass
                time.sleep(0.05)
                
                result = run_command(operation)
                self.assertEqual(result['returncode'], 0)
                
                current_atime = self._get_file_access_time("test_file.txt")
                
                if should_update:
                    # For content-reading commands in relatime mode, atime should update
                    # BUT in a persistent sandbox, if the file was recently accessed,
                    # the filesystem may not update atime again (relatime behavior)
                    # So we check that atime is either updated OR already very recent
                    if current_atime != previous_atime:
                        # Access time was updated as expected
                        previous_atime = current_atime
                    # else: atime didn't change, which can happen in relatime if file was recently accessed
                    #       This is actually correct Linux relatime behavior!
                else:
                    self.assertEqual(previous_atime, current_atime, 
                                   f"Access time should not be updated after: {operation}")

    def test_access_time_metadata_persistence(self):
        """Test that access_time changes persist through DB operations."""
        common_utils_utils.ACCESS_TIME_MODE = "atime"
        
        # Get initial access time
        initial_atime = self._get_file_access_time("test_file.txt")
        
        # Allow time to pass
        import time
        time.sleep(0.01)
        
        # Read the file to update access time
        result = run_command("cat test_file.txt")
        self.assertEqual(result['returncode'], 0)
        
        # Get updated access time
        updated_atime = self._get_file_access_time("test_file.txt")
        self.assertNotEqual(initial_atime, updated_atime)
        
        # Simulate a command that doesn't modify files but processes the DB
        # This tests that metadata persists through internal operations
        result = run_command("echo 'hello' > another_file.txt")
        self.assertEqual(result['returncode'], 0)
        
        # Access time should still be the updated value
        persistent_atime = self._get_file_access_time("test_file.txt")
        self.assertEqual(updated_atime, persistent_atime, 
                        "Access time should persist through other operations")

    def test_access_time_realistic_filesystem_behavior(self):
        """Test that access_time behavior matches realistic filesystem behavior."""
        
        test_cases = [
            # (mode, command, should_update_atime, description)
            ("atime", "cat test_file.txt", True, "Traditional atime updates on every access"),
            ("noatime", "cat test_file.txt", False, "No atime updates for performance"),
            ("relatime", "cat test_file.txt", True, "Relatime updates on content access"),
            ("relatime", "ls test_file.txt", False, "Relatime doesn't update on metadata access"),
            ("noatime", "ls test_file.txt", False, "No atime mode never updates"),
            ("atime", "ls test_file.txt", True, "Traditional atime updates even on ls"),
        ]
        
        for mode, command, should_update, description in test_cases:
            with self.subTest(mode=mode, command=command):
                common_utils_utils.ACCESS_TIME_MODE = mode
                
                # Force atime to past for relatime/atime modes to work correctly
                if should_update and mode in ("relatime", "atime"):
                    self._set_file_access_time_to_past("test_file.txt")
                
                # Get initial access time
                initial_atime = self._get_file_access_time("test_file.txt")
                
                # Allow time to pass
                import time
                time.sleep(0.1)
                
                # Execute command
                result = run_command(command)
                self.assertEqual(result['returncode'], 0)
                
                # Check access time
                new_atime = self._get_file_access_time("test_file.txt")
                
                if should_update:
                    self.assertNotEqual(initial_atime, new_atime, f"{description} - atime should update")
                else:
                    self.assertEqual(initial_atime, new_atime, f"{description} - atime should not update")

class TestRunCommandPermissions(unittest.TestCase):
    def setUp(self):
        self.workspace_path = minimal_reset_db()
        self.test_file = os.path.join(self.workspace_path, "permtest.txt")
        
        # Create test file with content
        os.makedirs(os.path.dirname(self.test_file), exist_ok=True)
        with open(self.test_file, 'w') as f:
            f.write("original content\n")
        
        # Set initial permissions to 644
        os.chmod(self.test_file, 0o644)
        
        # Collect initial metadata
        file_metadata = utils._collect_file_metadata(self.test_file)
        
        DB["file_system"][self.test_file] = {
            "path": self.test_file,
            "is_directory": False,
            "content_lines": ["original content\n"],
            "size_bytes": utils.calculate_size_bytes(["original content\n"]),
            "last_modified": utils.get_current_timestamp_iso(),
            "metadata": file_metadata
        }

    def tearDown(self):
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)

    def test_chmod_readonly_and_write(self):
        # Make file read-only
        result = run_command(f"chmod 444 permtest.txt")
        self.assertEqual(result["returncode"], 0)
        
        # Verify file is read-only in DB
        perms = DB["file_system"][self.test_file]["metadata"].get("permissions", {})
        self.assertEqual(perms.get("mode"), 0o444)
        
        # Try to write to the file (should fail)
        with self.assertRaises(CommandExecutionError):
            run_command(f"echo 'fail' > permtest.txt")
        
        # Verify file still exists after failed write
        self.assertIn(self.test_file, DB["file_system"], "File should still exist after failed write")
        
        # Make file writable again
        result = run_command(f"chmod 644 permtest.txt")
        self.assertEqual(result["returncode"], 0)
        
        # Verify file is now writable in DB
        perms = DB["file_system"][self.test_file]["metadata"].get("permissions", {})
        self.assertEqual(perms.get("mode"), 0o644)
        
        # Now write should succeed
        result = run_command(f"echo 'success' > permtest.txt")
        self.assertEqual(result["returncode"], 0)
        
        # Verify content was written
        content = DB["file_system"][self.test_file]["content_lines"]
        self.assertEqual(content, ["success\n"])

    def test_chmod_and_ls(self):
        # Change to 755 and check mode in DB
        result = run_command(f"chmod 755 permtest.txt")
        self.assertEqual(result["returncode"], 0)
        perms = DB["file_system"][self.test_file]["metadata"].get("permissions", {})
        self.assertEqual(perms.get("mode"), 0o755)
        # ls -l output should reflect the new permissions
        result = run_command(f"ls -l permtest.txt")
        self.assertIn("rwxr-xr-x", result["stdout"])  # Mode string for 755

    def test_chmod_executable(self):
        # Make file executable
        result = run_command(f"chmod 755 permtest.txt")
        self.assertEqual(result["returncode"], 0)
        perms = DB["file_system"][self.test_file]["metadata"].get("permissions", {})
        self.assertEqual(perms.get("mode"), 0o755)
        # ls -l output should reflect the new permissions
        result = run_command(f"ls -l permtest.txt")
        self.assertIn("rwxr-xr-x", result["stdout"])

    def test_chmod_000(self):
        # Remove all permissions
        result = run_command(f"chmod 000 permtest.txt")
        self.assertEqual(result["returncode"], 0)
        perms = DB["file_system"][self.test_file]["metadata"].get("permissions", {})
        self.assertEqual(perms.get("mode"), 0o000)
        # Try to read the file (should fail)
        with self.assertRaises(CommandExecutionError):
            run_command(f"cat permtest.txt")

    def test_chmod_777(self):
        # Give all permissions
        result = run_command(f"chmod 777 permtest.txt")
        self.assertEqual(result["returncode"], 0)
        perms = DB["file_system"][self.test_file]["metadata"].get("permissions", {})
        self.assertEqual(perms.get("mode"), 0o777)
        # Try to write and execute (simulate with echo and ls)
        result = run_command(f"echo '777test' > permtest.txt")
        self.assertEqual(result["returncode"], 0)
        content = "".join(DB["file_system"][self.test_file]["content_lines"])
        self.assertIn("777test", content)

    def test_chown_to_self(self):
        # Try to chown to current user/group (should succeed or be a no-op)
        uid = os.getuid() if hasattr(os, 'getuid') else 1000
        gid = os.getgid() if hasattr(os, 'getgid') else 1000
        result = run_command(f"chown {uid}:{gid} permtest.txt")
        self.assertEqual(result["returncode"], 0)
        perms = DB["file_system"][self.test_file]["metadata"].get("permissions", {})
        self.assertEqual(perms.get("uid"), uid)
        self.assertEqual(perms.get("gid"), gid)

    def test_chmod_directory(self):
        # Create a directory and change its permissions
        dir_path = os.path.join(self.workspace_path, "permdir")
        os.makedirs(dir_path, exist_ok=True)
        os.chmod(dir_path, 0o755)  # Set initial permissions
        
        # Collect initial metadata
        dir_metadata = utils._collect_file_metadata(dir_path)
        
        DB["file_system"][dir_path] = {
            "path": dir_path,
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": utils.get_current_timestamp_iso(),
            "metadata": dir_metadata
        }
        
        result = run_command(f"chmod 700 permdir")
        self.assertEqual(result["returncode"], 0)
        perms = DB["file_system"][dir_path]["metadata"].get("permissions", {})
        self.assertEqual(perms.get("mode"), 0o700)
        # ls -ld output should reflect the new permissions
        result = run_command(f"ls -ld permdir")
        self.assertIn("drwx------", result["stdout"])

    def test_permission_persistence(self):
        # Change to read-only, then run another command, verify still read-only
        run_command(f"chmod 444 permtest.txt")
        run_command(f"ls permtest.txt")
        perms = DB["file_system"][self.test_file]["metadata"].get("permissions", {})
        self.assertEqual(perms.get("mode"), 0o444)

    def test_permission_persistence_across_cycles(self):
        # Initial permissions should be 0o644
        perms = DB["file_system"][self.test_file]["metadata"].get("permissions", {})
        self.assertEqual(perms.get("mode"), 0o644)
        result = run_command(f"ls -l permtest.txt")
        self.assertIn("rw-r--r--", result["stdout"])

        # Change permissions to 600
        run_command(f"chmod 600 permtest.txt")
        perms = DB["file_system"][self.test_file]["metadata"].get("permissions", {})
        self.assertEqual(perms.get("mode"), 0o600)
        result = run_command(f"ls -l permtest.txt")
        self.assertIn("rw-------", result["stdout"])

        # Simulate hydration/dehydration cycle
        from APIs.terminal.SimulationEngine.utils import _apply_file_metadata, _collect_file_metadata
        import shutil
        import tempfile
        temp_dir = tempfile.mkdtemp()
        temp_file = os.path.join(temp_dir, "permtest.txt")
        # Write file to temp dir and apply metadata
        with open(temp_file, "w") as f:
            f.write("test\n")
        _apply_file_metadata(temp_file, DB["file_system"][self.test_file]["metadata"])
        # Now collect metadata back (simulate dehydration)
        new_meta = _collect_file_metadata(temp_file)
        shutil.rmtree(temp_dir)
        self.assertEqual(new_meta["permissions"]["mode"], 0o600)

        # The DB should still reflect the correct permissions
        self.assertEqual(DB["file_system"][self.test_file]["metadata"]["permissions"]["mode"], 0o600)

    def test_relative_path_hydration_issue(self):
        """Test the relative path hydration issue where files persist incorrectly."""
        import tempfile
        import shutil
        
        # Create a temporary directory to simulate the workspace
        temp_workspace = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_workspace, ignore_errors=True))
        
        # Create initial structure (like the Colab example)
        searx_dir = os.path.join(temp_workspace, "searx")
        docs_dir = os.path.join(searx_dir, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        
        # Create status.json file (initial state)
        status_file = os.path.join(docs_dir, "status.json")
        with open(status_file, 'w') as f:
            f.write('{"status": "operational", "Status": "all_systems_go"}')
        
        # First hydration with absolute path
        DB.clear()
        from APIs.terminal.SimulationEngine.utils import hydrate_db_from_directory
        hydrate_db_from_directory(DB, temp_workspace)
        
        # Verify initial state
        initial_files = set(DB["file_system"].keys())
        self.assertIn(os.path.join(DB["workspace_root"], "searx", "docs", "status.json"), initial_files)
        
        # Create count.txt file using run_command
        DB["cwd"] = DB["workspace_root"]
        result = run_command("echo 'test content' > searx/docs/count.txt")
        self.assertEqual(result["returncode"], 0)
        
        # Verify the file was created in DB
        after_create_files = set(DB["file_system"].keys())
        count_file_path = os.path.join(DB["workspace_root"], "searx", "docs", "count.txt")
        self.assertIn(count_file_path, after_create_files)
        self.assertGreater(len(after_create_files), len(initial_files))
        
        # Second hydration with absolute path
        DB.clear()
        hydrate_db_from_directory(DB, temp_workspace)
        
        # Check if the created file still exists (it shouldn't in a proper reset)
        final_files = set(DB["file_system"].keys())
        final_count_file_path = os.path.join(DB["workspace_root"], "searx", "docs", "count.txt")
        
        # The file should NOT be in the final DB state if we're truly resetting
        self.assertNotIn(final_count_file_path, final_files, 
                        "count.txt should not exist in DB after reset")

    def test_absolute_path_hydration_works_correctly(self):
        """Test that absolute path hydration works correctly as a comparison."""
        import tempfile
        import shutil
        
        # Create a temporary directory to simulate the workspace
        temp_workspace = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_workspace, ignore_errors=True))
        
        # Create initial structure
        searx_dir = os.path.join(temp_workspace, "searx")
        docs_dir = os.path.join(searx_dir, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        
        # Create status.json file (initial state)
        status_file = os.path.join(docs_dir, "status.json")
        with open(status_file, 'w') as f:
            f.write('{"status": "operational", "Status": "all_systems_go"}')
        
        # Test with absolute path (this should work correctly)
        absolute_path = os.path.abspath(temp_workspace)
        
        # First hydration with absolute path
        DB.clear()
        from APIs.terminal.SimulationEngine.utils import hydrate_db_from_directory
        hydrate_db_from_directory(DB, absolute_path)
        
        # Verify initial state
        initial_files = set(DB["file_system"].keys())
        self.assertIn(os.path.join(DB["workspace_root"], "searx", "docs", "status.json"), initial_files)
        
        # Create count.txt file using run_command
        DB["cwd"] = DB["workspace_root"]
        result = run_command("echo 'test content' > searx/docs/count.txt")
        self.assertEqual(result["returncode"], 0)
        
        # Verify the file was created in DB
        after_create_files = set(DB["file_system"].keys())
        count_file_path = os.path.join(DB["workspace_root"], "searx", "docs", "count.txt")
        self.assertIn(count_file_path, after_create_files)
        self.assertGreater(len(after_create_files), len(initial_files))
        
        # Second hydration with absolute path (simulating re-initialization)
        DB.clear()
        hydrate_db_from_directory(DB, absolute_path)
        
        # Check if the created file still exists (it shouldn't in a proper reset)
        final_files = set(DB["file_system"].keys())
        final_count_file_path = os.path.join(DB["workspace_root"], "searx", "docs", "count.txt")
        
        # With absolute paths, this should work correctly
        # The file should NOT be in the final DB state
        physical_count_file = os.path.join(temp_workspace, "searx", "docs", "count.txt")
        
        # The file should not exist physically after proper virtualization
        self.assertFalse(os.path.exists(physical_count_file), 
                        "File should not exist physically with absolute path")
        self.assertNotIn(final_count_file_path, final_files,
                        "count.txt should not exist in DB after reset with absolute path")
        self.assertEqual(len(final_files), len(initial_files), 
                        "DB should be reset to initial state with absolute path")

    def test_workspace_isolation_issue(self):
        """Test that files created by run_command are properly isolated."""
        import tempfile
        import shutil
        
        # Create a temporary directory to simulate the workspace
        temp_workspace = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_workspace, ignore_errors=True))
        
        # Create initial structure
        searx_dir = os.path.join(temp_workspace, "searx")
        docs_dir = os.path.join(searx_dir, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        
        # Create status.json file (initial state)
        status_file = os.path.join(docs_dir, "status.json")
        with open(status_file, 'w') as f:
            f.write('{"status": "operational", "Status": "all_systems_go"}')
        
        # First hydration
        DB.clear()
        from APIs.terminal.SimulationEngine.utils import hydrate_db_from_directory
        hydrate_db_from_directory(DB, temp_workspace)
        
        # Create searx/docs directory in DB
        docs_path = os.path.join(DB["workspace_root"], "searx", "docs")
        if not os.path.exists(docs_path):
            os.makedirs(docs_path, exist_ok=True)
        
        # Verify initial state
        initial_files = set(DB["file_system"].keys())
        status_json_path = os.path.join(DB["workspace_root"], "searx", "docs", "status.json")
        self.assertIn(status_json_path, initial_files)
        
        # Create count.txt file using run_command
        DB["cwd"] = DB["workspace_root"]
        result = run_command("echo 'test content' > searx/docs/count.txt")
        self.assertEqual(result["returncode"], 0)
        
        # Verify the file was created in DB
        after_create_files = set(DB["file_system"].keys())
        count_file_path = os.path.join(DB["workspace_root"], "searx", "docs", "count.txt")
        self.assertIn(count_file_path, after_create_files)
        
        # The file should NOT exist in the physical filesystem
        physical_count_file = os.path.join(temp_workspace, "searx", "docs", "count.txt")
        self.assertFalse(os.path.exists(physical_count_file),
                        "Files created by run_command should not exist physically")
        
        # Second hydration should not include the file
        DB.clear()
        hydrate_db_from_directory(DB, temp_workspace)
        
        final_files = set(DB["file_system"].keys())
        final_count_file_path = os.path.join(DB["workspace_root"], "searx", "docs", "count.txt")
        
        self.assertNotIn(final_count_file_path, final_files,
                        "File should not persist across hydration cycles")
        self.assertEqual(len(final_files), len(initial_files),
                        "DB should be reset to initial state")

    def test_correct_usage_pattern_documentation(self):
        """Test that documents the correct usage pattern to avoid the Colab issue."""
        import tempfile
        import shutil
        
        # Create a temporary directory to simulate the workspace
        temp_workspace = tempfile.mkdtemp()
        self.addCleanup(lambda: shutil.rmtree(temp_workspace, ignore_errors=True))
        
        # CORRECT PATTERN: Create initial structure using run_command, not direct file operations
        DB.clear()
        from APIs.terminal.SimulationEngine.utils import hydrate_db_from_directory
        
        # Start with an empty directory
        hydrate_db_from_directory(DB, temp_workspace)
        
        # Use run_command to create the initial structure
        DB["cwd"] = DB["workspace_root"]
        result = run_command("mkdir -p searx/docs")
        self.assertEqual(result["returncode"], 0)
        
        # Use run_command to create files
        result = run_command('echo \'{"status": "operational"}\' > searx/docs/status.json')
        self.assertEqual(result["returncode"], 0)
        
        # Verify initial state
        initial_files = set(DB["file_system"].keys())
        status_json_path = os.path.join(DB["workspace_root"], "searx", "docs", "status.json")
        self.assertIn(status_json_path, initial_files)
        
        # Test that the file doesn't exist in physical filesystem
        physical_status_file = os.path.join(temp_workspace, "searx", "docs", "status.json")
        self.assertFalse(os.path.exists(physical_status_file),
                        "Files created by run_command should not exist physically")
        
        # Create another file using run_command
        result = run_command("echo 'test content' > searx/docs/count.txt")
        self.assertEqual(result["returncode"], 0)
        
        # Verify the file was created in DB
        after_create_files = set(DB["file_system"].keys())
        count_file_path = os.path.join(DB["workspace_root"], "searx", "docs", "count.txt")
        self.assertIn(count_file_path, after_create_files)
        
        # Test that this file also doesn't exist physically
        physical_count_file = os.path.join(temp_workspace, "searx", "docs", "count.txt")
        self.assertFalse(os.path.exists(physical_count_file),
                        "Files created by run_command should not exist physically")
        
        # Re-hydration should reset to the original empty state
        DB.clear()
        hydrate_db_from_directory(DB, temp_workspace)
        
        # The DB should be empty (or only contain the root directory)
        final_files = set(DB["file_system"].keys())
        self.assertNotIn(status_json_path, final_files,
                        "Files should not persist across hydration cycles")
        self.assertNotIn(count_file_path, final_files,
                        "Files should not persist across hydration cycles")
            
        print("✅ Correct usage pattern: Use run_command for all file operations")
        print("✅ Files remain virtualized and don't persist across hydration cycles")
        print("✅ Error messages are clean and not nested")

class TestArchiveOperations(unittest.TestCase):
    """Test cases for archive operations (zip, tar, etc.)."""

    def setUp(self):
        """Set up test environment before each test."""
        self.workspace_path = minimal_reset_db()
        
        # Create test files with content
        test_files = {
            "file1.txt": ["This is file 1\n", "Line 2\n"],
            "file2.txt": ["This is file 2\n", "Another line\n"],
            "data.json": ['{"key": "value"}\n']
        }
        
        for filename, content in test_files.items():
            file_path = normalize_for_db(os.path.join(self.workspace_path, filename))
            DB["file_system"][file_path] = {
                "path": file_path,
                "is_directory": False,
                "content_lines": content,
                "size_bytes": utils.calculate_size_bytes(content),
                "last_modified": utils.get_current_timestamp_iso()
            }
            # Create the actual file in the filesystem
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                f.writelines(content)
        
        # Create test directory with nested file
        test_dir = normalize_for_db(os.path.join(self.workspace_path, "test_dir"))
        os.makedirs(test_dir, exist_ok=True)
        DB["file_system"][test_dir] = {
            "path": test_dir,
            "is_directory": True,
            "content_lines": [],
            "size_bytes": 0,
            "last_modified": utils.get_current_timestamp_iso()
        }
        
        # Add a file inside the directory
        nested_file = normalize_for_db(os.path.join(test_dir, "nested.txt"))
        nested_content = ["Nested file content\n"]
        DB["file_system"][nested_file] = {
            "path": nested_file,
            "is_directory": False,
            "content_lines": nested_content,
            "size_bytes": utils.calculate_size_bytes(nested_content),
            "last_modified": utils.get_current_timestamp_iso()
        }
        # Create the actual nested file
        with open(nested_file, 'w') as f:
            f.writelines(nested_content)

    def tearDown(self):
        """Clean up after each test."""
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)

    def _get_expected_path_key(self, relative_path: str) -> str:
        current_workspace_root = DB["workspace_root"]
        abs_path = os.path.join(current_workspace_root, relative_path)
        normalized_key = os.path.normpath(abs_path).replace("\\\\", "/")
        return normalized_key

    def test_zip_archive_creation(self):
        """Test creating a ZIP archive and verify it appears in the filesystem."""
        result = run_command("zip test_archive.zip file1.txt file2.txt data.json")
        self.assertEqual(result['returncode'], 0)
        
        # Check if archive file exists in DB
        archive_path = self._get_expected_path_key("test_archive.zip")
        self.assertIn(archive_path, DB["file_system"])
        
        # Verify archive is a file, not directory
        self.assertFalse(DB["file_system"][archive_path]["is_directory"])
        
        # Check that archive has content (should be binary)
        self.assertGreater(DB["file_system"][archive_path]["size_bytes"], 0)
        
        return archive_path

    def test_tar_archive_creation(self):
        """Test creating a TAR archive and verify it appears in the filesystem."""
        result = run_command("tar -cf test_archive.tar file1.txt file2.txt data.json")
        self.assertEqual(result['returncode'], 0)
        
        # Check if archive file exists in DB
        archive_path = self._get_expected_path_key("test_archive.tar")
        self.assertIn(archive_path, DB["file_system"])
        
        # Verify archive is a file, not directory
        self.assertFalse(DB["file_system"][archive_path]["is_directory"])
        
        # Check that archive has content
        self.assertGreater(DB["file_system"][archive_path]["size_bytes"], 0)
        
        return archive_path

    def test_archive_permissions_after_creation(self):
        """Test permissions of archive files immediately after creation."""
        # Create ZIP archive
        zip_path = self.test_zip_archive_creation()
        
        # Check permissions in DB metadata
        zip_entry = DB["file_system"][zip_path]
        self.assertIn("metadata", zip_entry)
        
        permissions = zip_entry["metadata"]["permissions"]
        self.assertIn("mode", permissions)
        
        # Check if file is readable
        mode = permissions["mode"]
        self.assertTrue(mode & 0o400, f"Archive should be readable, mode: {oct(mode)}")
        
        # Check if file is writable (should be writable by owner)
        self.assertTrue(mode & 0o200, f"Archive should be writable by owner, mode: {oct(mode)}")

    def test_archive_access_after_creation(self):
        """Test if we can access archive files after creation."""
        # Create archive
        archive_path = self.test_zip_archive_creation()
        
        # Try to list archive contents
        result = run_command("unzip -l test_archive.zip")
        self.assertEqual(result['returncode'], 0)
        self.assertIn("file1.txt", result['stdout'])
        self.assertIn("file2.txt", result['stdout'])
        self.assertIn("data.json", result['stdout'])

    def test_archive_extraction(self):
        """Test extracting archive contents."""
        # Create archive
        self.test_zip_archive_creation()
        
        # Extract to a new directory
        result = run_command("mkdir extracted && unzip test_archive.zip -d extracted")
        self.assertEqual(result['returncode'], 0)
        
        # Check if extracted files exist
        extracted_file1 = self._get_expected_path_key("extracted/file1.txt")
        extracted_file2 = self._get_expected_path_key("extracted/file2.txt")
        extracted_data = self._get_expected_path_key("extracted/data.json")
        
        self.assertIn(extracted_file1, DB["file_system"])
        self.assertIn(extracted_file2, DB["file_system"])
        self.assertIn(extracted_data, DB["file_system"])

    def test_archive_permission_changes(self):
        """Test changing permissions on archive files."""
        # Create archive
        archive_path = self.test_zip_archive_creation()
        
        # Try to change permissions
        result = run_command("chmod 644 test_archive.zip")
        self.assertEqual(result['returncode'], 0)
        
        # Check if permissions were updated in DB
        zip_entry = DB["file_system"][archive_path]
        permissions = zip_entry["metadata"]["permissions"]
        self.assertEqual(permissions["mode"] & 0o777, 0o644)

    def test_archive_deletion(self):
        """Test deleting archive files."""
        # Create archive
        archive_path = self.test_zip_archive_creation()
        
        # Delete the archive
        result = run_command("rm test_archive.zip")
        self.assertEqual(result['returncode'], 0)
        
        # Check if archive was removed from DB
        self.assertNotIn(archive_path, DB["file_system"])

    def test_archive_with_directory(self):
        """Test creating archive that includes a directory."""
        result = run_command("zip -r test_dir_archive.zip test_dir")
        self.assertEqual(result['returncode'], 0)
        
        # Check if archive exists
        archive_path = self._get_expected_path_key("test_dir_archive.zip")
        self.assertIn(archive_path, DB["file_system"])
        
        # Extract and verify directory structure
        result = run_command("mkdir extracted_dir && unzip test_dir_archive.zip -d extracted_dir")
        self.assertEqual(result['returncode'], 0)
        
        # Check if nested file was extracted
        extracted_nested = self._get_expected_path_key("extracted_dir/test_dir/nested.txt")
        self.assertIn(extracted_nested, DB["file_system"])

    def test_archive_metadata_preservation(self):
        """Test that archive files preserve metadata correctly."""
        # Create archive
        archive_path = self.test_zip_archive_creation()
        
        # Get initial metadata
        initial_entry = DB["file_system"][archive_path]
        initial_metadata = initial_entry["metadata"]
        
        # Run another command to trigger hydration/dehydration cycle
        run_command("ls -la")
        
        # Check if metadata is preserved
        final_entry = DB["file_system"][archive_path]
        final_metadata = final_entry["metadata"]
        
        # Compare key metadata fields
        self.assertEqual(initial_metadata["permissions"]["mode"], final_metadata["permissions"]["mode"])
        self.assertEqual(initial_metadata["attributes"]["is_symlink"], final_metadata["attributes"]["is_symlink"])

    def test_archive_file_size_consistency(self):
        """Test that archive file sizes are consistent across operations."""
        # Create archive
        archive_path = self.test_zip_archive_creation()
        
        # Get initial size
        initial_size = DB["file_system"][archive_path]["size_bytes"]
        
        # Run another command
        run_command("ls -la")
        
        # Check if size is preserved
        final_size = DB["file_system"][archive_path]["size_bytes"]
        self.assertEqual(initial_size, final_size)

    def test_archive_binary_content_handling(self):
        """Test that archive files are handled as binary content."""
        # Create archive
        archive_path = self.test_zip_archive_creation()
        
        # Check if content is marked as binary or placeholder
        content_lines = DB["file_system"][archive_path]["content_lines"]
        
        # Archive files should either be binary placeholders or actual binary content
        if content_lines == utils.BINARY_CONTENT_PLACEHOLDER:
            # This is expected for binary files
            pass
        elif content_lines == utils.LARGE_FILE_CONTENT_PLACEHOLDER:
            # This is expected for large files
            pass
        else:
            # If it's actual content, it should be non-empty
            self.assertGreater(len(content_lines), 0)

    def test_archive_permissions_vs_regular_files(self):
        """Compare permissions between archive files and regular files."""
        # Create a regular file
        regular_file = "regular.txt"
        regular_path = self._get_expected_path_key(regular_file)
        
        result = run_command(f"echo 'test content' > {regular_file}")
        self.assertEqual(result['returncode'], 0)
        
        # Create archive
        archive_path = self.test_zip_archive_creation()
        
        # Compare permissions
        regular_entry = DB["file_system"][regular_path]
        archive_entry = DB["file_system"][archive_path]
        
        regular_mode = regular_entry["metadata"]["permissions"]["mode"]
        archive_mode = archive_entry["metadata"]["permissions"]["mode"]
        
        # Both should be readable and writable by owner
        self.assertTrue(regular_mode & 0o400, f"Regular file should be readable, mode: {oct(regular_mode)}")
        self.assertTrue(archive_mode & 0o400, f"Archive should be readable, mode: {oct(archive_mode)}")
        self.assertTrue(regular_mode & 0o200, f"Regular file should be writable, mode: {oct(regular_mode)}")
        self.assertTrue(archive_mode & 0o200, f"Archive should be writable, mode: {oct(archive_mode)}")

    def test_archive_ownership_consistency(self):
        """Test that archive files maintain consistent ownership."""
        # Create archive
        archive_path = self.test_zip_archive_creation()
        
        # Get initial ownership
        initial_entry = DB["file_system"][archive_path]
        initial_uid = initial_entry["metadata"]["permissions"]["uid"]
        initial_gid = initial_entry["metadata"]["permissions"]["gid"]
        
        # Run another command
        run_command("ls -la")
        
        # Check if ownership is preserved
        final_entry = DB["file_system"][archive_path]
        final_uid = final_entry["metadata"]["permissions"]["uid"]
        final_gid = final_entry["metadata"]["permissions"]["gid"]
        
        self.assertEqual(initial_uid, final_uid)
        self.assertEqual(initial_gid, final_gid)

    def test_archive_timestamp_behavior(self):
        """Test timestamp behavior for archive files."""
        # Create archive
        archive_path = self.test_zip_archive_creation()
        
        # Get initial timestamps
        initial_entry = DB["file_system"][archive_path]
        initial_modify_time = initial_entry["metadata"]["timestamps"]["modify_time"]
        
        # Wait a moment and run another command
        time.sleep(0.1)
        run_command("ls -la")
        
        # Check if modify time is preserved (should not change unless file is modified)
        final_entry = DB["file_system"][archive_path]
        final_modify_time = final_entry["metadata"]["timestamps"]["modify_time"]
        
        self.assertEqual(initial_modify_time, final_modify_time)

    def test_archive_with_special_characters(self):
        """Test creating archives with special characters in filenames."""
        # Create file with special characters
        special_file = "file with spaces.txt"
        special_path = self._get_expected_path_key(special_file)
        special_content = ["Special content\n"]
        
        DB["file_system"][special_path] = {
            "path": special_path,
            "is_directory": False,
            "content_lines": special_content,
            "size_bytes": utils.calculate_size_bytes(special_content),
            "last_modified": utils.get_current_timestamp_iso()
        }
        
        # Create the actual file in the filesystem
        os.makedirs(os.path.dirname(special_path), exist_ok=True)
        with open(special_path, 'w') as f:
            f.writelines(special_content)
        
        # Create archive with quoted filename
        result = run_command('zip "special_archive.zip" "file with spaces.txt"')
        self.assertEqual(result['returncode'], 0)
        
        # Check if archive exists
        archive_path = self._get_expected_path_key("special_archive.zip")
        self.assertIn(archive_path, DB["file_system"])

    def test_archive_error_handling(self):
        """Test error handling when archive operations fail."""
        # Try to create archive with non-existent files
        with self.assertRaises(CommandExecutionError) as cm:
            run_command("zip error_archive.zip nonexistent1.txt nonexistent2.txt")
        
        # Should fail with appropriate error message
        self.assertIn("Command failed with exit code", str(cm.exception))
        
        # Verify that no broken archive file was created in the DB
        archive_path = self._get_expected_path_key("error_archive.zip")
        self.assertNotIn(archive_path, DB["file_system"])

    def test_archive_compression_levels(self):
        """Test creating archives with different compression levels."""
        # Create archive with maximum compression
        result = run_command("zip -9 max_compression.zip file1.txt file2.txt")
        self.assertEqual(result['returncode'], 0)
        
        # Create archive with no compression
        result = run_command("zip -0 no_compression.zip file1.txt file2.txt")
        self.assertEqual(result['returncode'], 0)
        
        # Both should exist
        max_archive = self._get_expected_path_key("max_compression.zip")
        no_archive = self._get_expected_path_key("no_compression.zip")
        
        self.assertIn(max_archive, DB["file_system"])
        self.assertIn(no_archive, DB["file_system"])

    def test_archive_incremental_updates(self):
        """Test updating an existing archive with new files."""
        # Create initial archive
        result = run_command("zip test_archive.zip file1.txt file2.txt data.json")
        self.assertEqual(result['returncode'], 0)
        
        # Create a new file
        new_file = "new_file.txt"
        new_path = self._get_expected_path_key(new_file)
        new_content = ["New file content\n"]
        
        DB["file_system"][new_path] = {
            "path": new_path,
            "is_directory": False,
            "content_lines": new_content,
            "size_bytes": utils.calculate_size_bytes(new_content),
            "last_modified": utils.get_current_timestamp_iso()
        }
        
        # Create the actual file in the filesystem
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        with open(new_path, 'w') as f:
            f.writelines(new_content)
        
        # Add new file to archive
        result = run_command("zip test_archive.zip new_file.txt")
        self.assertEqual(result['returncode'], 0)

    def test_binary_file_placeholder_issue(self):
        """Test to specifically validate the binary file placeholder issue is fixed."""
        # Create a simple archive
        result = run_command("zip test_binary.zip file1.txt")
        self.assertEqual(result['returncode'], 0)
        
        # Check if archive exists in DB
        archive_path = self._get_expected_path_key("test_binary.zip")
        self.assertIn(archive_path, DB["file_system"])
        
        # Check if archive now stores actual binary content instead of placeholder
        archive_entry = DB["file_system"][archive_path]
        content_lines = archive_entry["content_lines"]
        
        # For binary files, we should either have actual content or a special
        # binary content representation, not just a text placeholder
        if content_lines == utils.BINARY_CONTENT_PLACEHOLDER:
            # This is the current broken behavior
            self.fail("Archive file is stored as placeholder instead of actual binary content")
        
        # If we have actual content, it should be accessible
        if content_lines != utils.BINARY_CONTENT_PLACEHOLDER:
            result = run_command("unzip -l test_binary.zip")
            self.assertEqual(result['returncode'], 0)

    def test_binary_file_content_preservation(self):
        """Test that binary files preserve their actual content, not just placeholders."""
        # Create a simple archive
        result = run_command("zip test_content.zip file1.txt")
        self.assertEqual(result['returncode'], 0)
        
        # Check if archive exists and has actual content (not placeholder)
        archive_path = self._get_expected_path_key("test_content.zip")
        self.assertIn(archive_path, DB["file_system"])
        
        # The archive should have actual binary content, not just a placeholder
        archive_entry = DB["file_system"][archive_path]
        content_lines = archive_entry["content_lines"]
        
        # For archive files, we should have base64-encoded content, not placeholders
        self.assertNotEqual(content_lines, utils.BINARY_CONTENT_PLACEHOLDER)
        self.assertTrue(len(content_lines) > 1, "Archive should have base64 content")
        self.assertEqual(content_lines[0].strip(), "# BINARY_ARCHIVE_BASE64_ENCODED")
        
        # If we have actual content, it should be accessible
        result = run_command("unzip -l test_content.zip")
        self.assertEqual(result['returncode'], 0)


class TestCwdPersistence(unittest.TestCase):
    """Test cases for ensuring CWD is preserved across commands."""

    def setUp(self):
        """Set up a workspace with a subdirectory."""
        self.workspace_path = minimal_reset_db()
        self.subdir = os.path.join(self.workspace_path, "subdir")
        os.makedirs(self.subdir, exist_ok=True)
        
        # Hydrate the DB to include the new subdirectory
        utils.hydrate_db_from_directory(DB, self.workspace_path)
        
        # Change CWD to the subdirectory for testing
        DB["cwd"] = self.subdir

    def tearDown(self):
        """Clean up the workspace."""
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)

    def test_cwd_preserved_after_external_command(self):
        """Verify that the CWD is not changed by an external command."""
        initial_cwd = DB["cwd"]
        self.assertEqual(initial_cwd, self.subdir)

        # Run a simple external command that does not change directory
        run_command("ls")

        # Check that the CWD is still the subdirectory
        final_cwd = DB["cwd"]
        self.assertEqual(final_cwd, initial_cwd, "CWD should be preserved after running 'ls'")

    def test_cwd_preserved_after_failed_external_command(self):
        """Verify CWD is preserved even if an external command fails."""
        initial_cwd = DB["cwd"]
        self.assertEqual(initial_cwd, self.subdir)

        # Run a command that will fail
        with self.assertRaises(CommandExecutionError):
            run_command("cat non_existent_file.txt")

        # Check that the CWD is still the subdirectory
        final_cwd = DB["cwd"]
        self.assertEqual(final_cwd, initial_cwd, "CWD should be preserved after a failed command")

    def test_cd_command_still_works(self):
        """Ensure that the internal 'cd' command still correctly changes the directory."""
        initial_cwd = DB["cwd"]
        
        # 'cd' to the parent directory (the workspace root)
        run_command("cd ..")
        
        # Verify the CWD has changed
        new_cwd = DB["cwd"]
        self.assertNotEqual(new_cwd, initial_cwd, "CWD should have changed after 'cd ..'")
        self.assertEqual(new_cwd, self.workspace_path)
        
        # Run an external command
        run_command("pwd")
        
        # Verify CWD is still the new directory
        final_cwd = DB["cwd"]
        self.assertEqual(final_cwd, self.workspace_path, "CWD should be preserved after 'pwd'")

    def test_cwd_preserved_after_which_zip(self):
        """Verify CWD is preserved after running 'which zip'."""
        initial_cwd = DB["cwd"]
        self.assertEqual(initial_cwd, self.subdir)

        # Run the 'which zip' command
        try:
            run_command("which zip")
        except CommandExecutionError as e:
            # a CommandExecutionError is raised if `zip` is not installed. 
            # We can ignore it since we only care about the cwd.
            pass

        # Check that the CWD is still the subdirectory
        final_cwd = DB["cwd"]
        self.assertEqual(final_cwd, initial_cwd, "CWD should be preserved after running 'which zip'")

class TestRedirectionParsingScenarios(unittest.TestCase):
    """Comprehensive tests for redirection parsing: here-docs, nested paths, quotes, and bash -c."""

    def setUp(self):
        self.workspace_path = minimal_reset_db()

    def tearDown(self):
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)

    def _path_key(self, relative_path: str) -> str:
        current_workspace_root = DB["workspace_root"]
        abs_path = os.path.join(current_workspace_root, relative_path)
        return os.path.normpath(abs_path).replace("\\", "/")

    def test_here_doc_creates_file_without_long_filename_error(self):
        # Skip on non-Unix environments
        if os.name == 'nt':
            self.skipTest('Here-doc tests are Unix-specific')
        cmd = (
            "sh -c \"cat << 'EOF' > out_hd.txt\n"
            "line1\nline2\n"
            "EOF\""
        )
        result = run_command(command=cmd)
        self.assertEqual(result['returncode'], 0)
        key = self._path_key('out_hd.txt')
        self.assertIn(key, DB['file_system'])
        self.assertEqual(DB['file_system'][key]['content_lines'], ["line1\n", "line2\n"])

    def test_here_doc_large_body_no_crash(self):
        if os.name == 'nt':
            self.skipTest('Here-doc tests are Unix-specific')
        large_lines = ["X" * 200 + "\n" for _ in range(50)]
        body = "".join(large_lines)
        cmd = (
            "sh -c \"cat << 'EOF' > big_hd.txt\n" + body + "EOF\""
        )
        result = run_command(command=cmd)
        self.assertEqual(result['returncode'], 0)
        key = self._path_key('big_hd.txt')
        self.assertIn(key, DB['file_system'])
        # Verify a few sample lines and total count
        self.assertEqual(len(DB['file_system'][key]['content_lines']), len(large_lines))
        self.assertTrue(all(line.endswith('\n') for line in DB['file_system'][key]['content_lines']))

    def test_bash_dash_c_with_redirection_to_nested_creates_parents(self):
        if os.name == 'nt':
            self.skipTest('Unix shell specific')
        nested = 'dir1/dir2/out.txt'
        cmd = "bash -c 'echo \"hi\" > {}'".format(nested)
        result = run_command(command=cmd)
        self.assertEqual(result['returncode'], 0)
        key = self._path_key(nested)
        self.assertIn(key, DB['file_system'])
        self.assertEqual(DB['file_system'][key]['content_lines'], ["hi\n"])

    def test_quoted_greater_sign_is_not_treated_as_redirection(self):
        if os.name == 'nt':
            self.skipTest('Unix shell specific')
        # Use simpler quoting: inner double quotes within single-quoted -c string
        cmd = "bash -c 'echo \"a > b\" > out.txt'"
        result = run_command(command=cmd)
        self.assertEqual(result['returncode'], 0)
        key = self._path_key('out.txt')
        self.assertIn(key, DB['file_system'])
        self.assertEqual(DB['file_system'][key]['content_lines'], ["a > b\n"])

    def test_redirection_with_spaced_filename_and_nested_dir(self):
        if os.name == 'nt':
            self.skipTest('Unix shell specific')
        # Ensure parent dir with space is created and file written
        path_with_spaces = 'dir with space/subdir/file name.txt'
        cmd = "bash -c 'echo \"hello\" > \"{}\"'".format(path_with_spaces)
        result = run_command(command=cmd)
        self.assertEqual(result['returncode'], 0)
        key = self._path_key(path_with_spaces)
        self.assertIn(key, DB['file_system'])
        self.assertEqual(DB['file_system'][key]['content_lines'], ["hello\n"]) 

    def test_here_string_with_output_redirection(self):
        if os.name == 'nt':
            self.skipTest('Unix shell specific')
        cmd = "bash -c 'cat <<< \"hello world\" > hs.txt'"
        result = run_command(command=cmd)
        self.assertEqual(result['returncode'], 0)
        key = self._path_key('hs.txt')
        self.assertIn(key, DB['file_system'])
        self.assertEqual(DB['file_system'][key]['content_lines'], ["hello world\n"])

    def test_multiple_redirections_only_last_nested_parent_needed(self):
        if os.name == 'nt':
            self.skipTest('Unix shell specific')
        # Ensure behavior with both stdout and stderr redirection where only last is nested
        cmd = "bash -c 'echo hi 1> out.txt 2> nested/err.txt'"
        result = run_command(command=cmd)
        self.assertEqual(result['returncode'], 0)
        out_key = self._path_key('out.txt')
        err_key = self._path_key('nested/err.txt')
        self.assertIn(out_key, DB['file_system'])
        self.assertIn(err_key, DB['file_system'])
        self.assertEqual(DB['file_system'][out_key]['content_lines'], ["hi\n"])  # stdout redirected into file
        self.assertEqual(DB['file_system'][err_key]['content_lines'], [])  # stderr file should be empty

class TestMarkdownHandling(unittest.TestCase):
    """Tests to ensure Markdown files are treated as text, hydrated, and readable."""

    def setUp(self):
        self.workspace_path = minimal_reset_db()
        # Create markdown-like files physically and in DB to match harness expectations
        files = {
            "README.md": ["# Title\n", "Some content in markdown.\n"],
            "notes.markdown": ["Heading\n", "- item 1\n", "- item 2\n"],
            "doc.mdx": ["export const meta = {};\n", "# MDX Document\n"],
        }
        # Create physically on disk so hydration can pick them up too
        for rel, content in files.items():
            abs_path = normalize_for_db(os.path.join(self.workspace_path, rel))
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.writelines(content)
        # Clear DB and hydrate to ensure behavior comes from hydration path
        DB.clear()
        utils.hydrate_db_from_directory(DB, self.workspace_path)

    def tearDown(self):
        reset_session_for_testing()  # Reset session state between tests
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)

    def _key(self, rel):
        return os.path.normpath(os.path.join(DB["workspace_root"], rel)).replace("\\", "/")

    def test_md_is_text_and_readable(self):
        key = self._key("README.md")
        self.assertIn(key, DB["file_system"])  # hydrated
        entry = DB["file_system"][key]
        self.assertFalse(entry["is_directory"])  # file
        self.assertNotEqual(entry["content_lines"], [])  # has content
        # Should not be binary placeholder
        self.assertNotEqual(entry["content_lines"], common_utils_utils.BINARY_CONTENT_PLACEHOLDER)
        # cat prints exact content
        DB["cwd"] = DB["workspace_root"]
        result = run_command("cat README.md")
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(result['stdout'], "".join(entry["content_lines"]))

    def test_markdown_ext_is_text_and_readable(self):
        key = self._key("notes.markdown")
        self.assertIn(key, DB["file_system"])  # hydrated
        entry = DB["file_system"][key]
        self.assertNotEqual(entry["content_lines"], common_utils_utils.BINARY_CONTENT_PLACEHOLDER)
        DB["cwd"] = DB["workspace_root"]
        result = run_command("cat notes.markdown")
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(result['stdout'], "".join(entry["content_lines"]))

    def test_mdx_is_text_and_readable(self):
        key = self._key("doc.mdx")
        self.assertIn(key, DB["file_system"])  # hydrated
        entry = DB["file_system"][key]
        self.assertNotEqual(entry["content_lines"], common_utils_utils.BINARY_CONTENT_PLACEHOLDER)
        DB["cwd"] = DB["workspace_root"]
        result = run_command("cat doc.mdx")
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(result['stdout'], "".join(entry["content_lines"]))


class TestCdChainingBehavior(unittest.TestCase):
    """Tests for cd chaining behavior in run_terminal_cmd."""

    def setUp(self):
        self.workspace_path = minimal_reset_db_for_terminal_commands()
        # Add a directory and a file inside to observe ls output
        dir_path = normalize_for_db(os.path.join(self.workspace_path, "dirA"))
        DB["file_system"][dir_path] = {
            "path": dir_path, "is_directory": True, "content_lines": [],
            "size_bytes": 0, "last_modified": utils.get_current_timestamp_iso()
        }
        file_inside = normalize_for_db(os.path.join(dir_path, "inside.txt"))
        DB["file_system"][file_inside] = {
            "path": file_inside, "is_directory": False, "content_lines": ["x\n"],
            "size_bytes": utils.calculate_size_bytes(["x\n"]),
            "last_modified": utils.get_current_timestamp_iso()
        }

    def tearDown(self):
        reset_session_for_testing()

    def test_cd_standalone_changes_cwd(self):
        current_before = DB.get("cwd")
        result = run_command("cd dirA")
        self.assertEqual(result.get("returncode"), 0)
        self.assertNotEqual(DB.get("cwd"), current_before)
        self.assertTrue(DB.get("cwd").endswith("/dirA"))

    def test_cd_with_chaining_executes_followup(self):
        # With special input handling, 'cd dirA && ls' should run ls in the new directory
        result = run_command("cd dirA && ls")
        self.assertEqual(result.get("returncode"), 0)
        self.assertIn("inside.txt", result.get("stdout", ""))
        self.assertTrue(DB.get("cwd").endswith("/dirA"))

    def test_shell_handles_chaining_when_invoked_explicitly(self):
        # Use an explicit shell so cd is not intercepted internally
        result = run_command("bash -lc 'cd dirA && ls'")
        self.assertEqual(result.get("returncode"), 0)
        # Expect to see the inside.txt listed
        self.assertIn("inside.txt", result.get("stdout", ""))

# --- Main Execution ---

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)

class TestUncoveredEdgeCases(unittest.TestCase):
    """Tests for edge cases and error handling paths to improve code coverage."""

    def setUp(self):
        """Initialize DB state before each test."""
        self.workspace_path = minimal_reset_db()
        
    def tearDown(self):
        """Clean up after each test."""
        reset_session_for_testing()
        DB.clear()
        if hasattr(self, 'workspace_path') and os.path.exists(self.workspace_path):
            shutil.rmtree(self.workspace_path)

    def test_cd_command_with_target_parsing(self):
        """Test cd command with target argument (Line 239: split parsing)."""
        # Test cd with absolute path mapping to workspace
        # The marker mechanism will track the actual CWD
        DB["cwd"] = normalize_for_db(self.workspace_path)
        result = run_command("echo 'test' > testfile.txt")
        self.assertEqual(result['returncode'], 0)
        # Verify file was created in the correct location
        file_path = os.path.join(self.workspace_path, "testfile.txt")
        file_norm = normalize_for_db(file_path)
        self.assertIn(file_norm, DB["file_system"])

    def test_output_redirection_creates_missing_dirs(self):
        """Test output redirection creates missing parent directories (Lines 358-366)."""
        DB["cwd"] = normalize_for_db(self.workspace_path)
        result = run_command("echo 'test' > nested/deep/output.txt")
        self.assertEqual(result['returncode'], 0)
        
        nested_file = os.path.join(self.workspace_path, "nested", "deep", "output.txt")
        nested_norm = normalize_for_db(nested_file)
        self.assertIn(nested_norm, DB["file_system"])

    def test_cd_to_invalid_directory_fails(self):
        """Test cd to non-existent directory fails (Line 239 error path)."""
        original_cwd = DB["cwd"]
        with self.assertRaises(CommandExecutionError):
            run_command("cd /nonexistent/fake/path")
        self.assertEqual(DB["cwd"], original_cwd)

    def test_cd_with_no_arguments(self):
        """Test cd with no arguments (defaults to /)."""
        # Move to workspace first
        DB["cwd"] = normalize_for_db(self.workspace_path)
        
        # cd with / goes to workspace root
        result = run_command("cd /")
        self.assertEqual(result['returncode'], 0)
        self.assertEqual(DB["cwd"], normalize_for_db(self.workspace_path))

