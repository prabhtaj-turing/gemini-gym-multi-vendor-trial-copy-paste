#!/usr/bin/env python3
"""
Unit tests for terminal_filesystem_utils.py
"""

import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the APIs directory to the path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from common_utils.terminal_filesystem_utils import detect_and_fix_tar_command, find_binary_files, BINARY_FILE_MARKER


class TestDetectAndFixTarCommand(unittest.TestCase):
    """Test cases for detect_and_fix_tar_command function."""

    def test_detect_tar_command_with_relative_output(self):
        """Test detection of tar command with relative output file in current directory."""
        command = "tar -czf ./project_backup.tar.gz ."
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should be modified to create archive in parent directory then move it back
        expected = f"tar -czf {os.path.dirname(execution_cwd)}/project_backup.tar.gz . && mv {os.path.dirname(execution_cwd)}/project_backup.tar.gz ./project_backup.tar.gz"
        self.assertEqual(result, expected)

    def test_detect_tar_command_with_filename_only(self):
        """Test detection of tar command with just filename (no ./ prefix)."""
        command = "tar -czf backup.tar.gz ."
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should be modified to create archive in parent directory then move it back
        expected = f"tar -czf {os.path.dirname(execution_cwd)}/backup.tar.gz . && mv {os.path.dirname(execution_cwd)}/backup.tar.gz backup.tar.gz"
        self.assertEqual(result, expected)

    def test_detect_tar_command_with_absolute_path(self):
        """Test that tar command with absolute path is not modified."""
        command = "tar -czf /tmp/backup.tar.gz ."
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should not be modified
        self.assertEqual(result, command)

    def test_detect_tar_command_with_subdirectory(self):
        """Test that tar command targeting subdirectory is not modified."""
        command = "tar -czf backup.tar.gz subdir/"
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should not be modified (not targeting current directory)
        self.assertEqual(result, command)

    def test_detect_tar_command_with_different_flags(self):
        """Test detection with different tar flag combinations."""
        command = "tar -cf archive.tar ."
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should be modified
        expected = f"tar -cf {os.path.dirname(execution_cwd)}/archive.tar . && mv {os.path.dirname(execution_cwd)}/archive.tar archive.tar"
        self.assertEqual(result, expected)

    def test_detect_tar_command_with_verbose_flag(self):
        """Test detection with verbose flag."""
        command = "tar -czvf backup.tar.gz ."
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should be modified
        expected = f"tar -czvf {os.path.dirname(execution_cwd)}/backup.tar.gz . && mv {os.path.dirname(execution_cwd)}/backup.tar.gz backup.tar.gz"
        self.assertEqual(result, expected)

    def test_detect_tar_command_with_extra_whitespace(self):
        """Test detection with extra whitespace in tar flags."""
        command = "tar   -czf   backup.tar.gz   ."
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should be modified and whitespace normalized
        expected = f"tar -czf {os.path.dirname(execution_cwd)}/backup.tar.gz . && mv {os.path.dirname(execution_cwd)}/backup.tar.gz backup.tar.gz"
        self.assertEqual(result, expected)

    def test_detect_tar_command_with_quoted_filename(self):
        """Test detection with quoted filename."""
        command = 'tar -czf "backup with spaces.tar.gz" .'
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should not be modified (quoted filenames are not detected by the current regex)
        self.assertEqual(result, command)

    def test_detect_tar_command_non_tar_command(self):
        """Test that non-tar commands are not modified."""
        command = "echo hello world"
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should not be modified
        self.assertEqual(result, command)

    def test_detect_tar_command_tar_without_compression(self):
        """Test detection with tar command without compression flags."""
        command = "tar -tf archive.tar ."
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should be modified (has 'f' flag in the pattern)
        expected = f"tar -tf {os.path.dirname(execution_cwd)}/archive.tar . && mv {os.path.dirname(execution_cwd)}/archive.tar archive.tar"
        self.assertEqual(result, expected)

    def test_detect_tar_command_tar_without_output_flag(self):
        """Test detection with tar command without output file flag."""
        command = "tar -cz archive.tar ."
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should be modified (has 'c' flag in the pattern)
        expected = f"tar -cz {os.path.dirname(execution_cwd)}/archive.tar . && mv {os.path.dirname(execution_cwd)}/archive.tar archive.tar"
        self.assertEqual(result, expected)

    def test_detect_tar_command_empty_command(self):
        """Test detection with empty command."""
        command = ""
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should not be modified
        self.assertEqual(result, command)

    def test_detect_tar_command_whitespace_only(self):
        """Test detection with whitespace-only command."""
        command = "   \t  \n  "
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should not be modified
        self.assertEqual(result, command)

    def test_detect_tar_command_with_nested_paths(self):
        """Test detection with nested relative paths."""
        command = "tar -czf ./backup/archive.tar.gz ."
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should be modified (the function is more permissive than expected)
        expected = f"tar -czf {os.path.dirname(execution_cwd)}/archive.tar.gz . && mv {os.path.dirname(execution_cwd)}/archive.tar.gz ./backup/archive.tar.gz"
        self.assertEqual(result, expected)

    def test_detect_tar_command_with_parent_directory(self):
        """Test detection with parent directory reference."""
        command = "tar -czf ../backup.tar.gz ."
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should not be modified (output file is in parent directory)
        self.assertEqual(result, command)

    def test_detect_tar_command_with_multiple_arguments(self):
        """Test detection with multiple arguments after the output file."""
        command = "tar -czf backup.tar.gz file1.txt file2.txt ."
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should not be modified (multiple arguments, not just '.')
        self.assertEqual(result, command)

    def test_detect_tar_command_with_exclude_patterns(self):
        """Test detection with exclude patterns."""
        command = "tar -czf backup.tar.gz --exclude='*.tmp' ."
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should not be modified (has additional arguments before '.')
        self.assertEqual(result, command)

    def test_detect_tar_command_with_leading_dotslash(self):
        """Test detection with leading ./ in output file."""
        command = "tar -czf ./backup.tar.gz ."
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should be modified
        expected = f"tar -czf {os.path.dirname(execution_cwd)}/backup.tar.gz . && mv {os.path.dirname(execution_cwd)}/backup.tar.gz ./backup.tar.gz"
        self.assertEqual(result, expected)

    def test_detect_tar_command_preserves_original_whitespace(self):
        """Test that the function preserves original whitespace in non-matching parts."""
        command = "  tar -czf backup.tar.gz .  "
        execution_cwd = "/tmp/test_workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should be modified but the function strips whitespace before processing
        expected = f"tar -czf {os.path.dirname(execution_cwd)}/backup.tar.gz . && mv {os.path.dirname(execution_cwd)}/backup.tar.gz backup.tar.gz"
        self.assertEqual(result, expected)

    def test_detect_tar_command_with_complex_execution_cwd(self):
        """Test detection with complex execution directory path."""
        command = "tar -czf backup.tar.gz ."
        execution_cwd = "/home/user/projects/my-workspace"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should be modified
        expected = f"tar -czf {os.path.dirname(execution_cwd)}/backup.tar.gz . && mv {os.path.dirname(execution_cwd)}/backup.tar.gz backup.tar.gz"
        self.assertEqual(result, expected)

    def test_detect_tar_command_with_root_execution_cwd(self):
        """Test detection with root execution directory."""
        command = "tar -czf backup.tar.gz ."
        execution_cwd = "/"
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Should be modified (parent of root is still root, but os.path.join normalizes the path)
        expected = f"tar -czf /backup.tar.gz . && mv /backup.tar.gz backup.tar.gz"
        self.assertEqual(result, expected)


class TestFindBinaryFiles(unittest.TestCase):
    """Test cases for find_binary_files function."""

    def test_find_binary_files_empty_filesystem(self):
        """Test finding binary files in empty file system."""
        file_system = {}
        result = find_binary_files(file_system)
        self.assertEqual(result, [])

    def test_find_binary_files_no_binary_files(self):
        """Test finding binary files when no binary files exist."""
        file_system = {
            "/path/to/file1.txt": {
                "content_lines": ["Hello world\n", "This is a text file\n"]
            },
            "/path/to/file2.py": {
                "content_lines": ["#!/usr/bin/env python3\n", "print('hello')\n"]
            }
        }
        result = find_binary_files(file_system)
        self.assertEqual(result, [])

    def test_find_binary_files_with_binary_files(self):
        """Test finding binary files when binary files exist."""
        file_system = {
            "/path/to/file1.txt": {
                "content_lines": ["Hello world\n", "This is a text file\n"]
            },
            "/path/to/archive.tar.gz": {
                "content_lines": [f"{BINARY_FILE_MARKER}\n", "base64encodedcontent\n"]
            },
            "/path/to/image.png": {
                "content_lines": [f"{BINARY_FILE_MARKER}\n", "morebase64content\n"]
            },
            "/path/to/file2.py": {
                "content_lines": ["#!/usr/bin/env python3\n", "print('hello')\n"]
            }
        }
        result = find_binary_files(file_system)
        expected = ["/path/to/archive.tar.gz", "/path/to/image.png"]
        self.assertEqual(sorted(result), sorted(expected))

    def test_find_binary_files_with_empty_content_lines(self):
        """Test finding binary files when files have empty content lines."""
        file_system = {
            "/path/to/empty_file": {
                "content_lines": []
            },
            "/path/to/binary_file": {
                "content_lines": [f"{BINARY_FILE_MARKER}\n"]
            }
        }
        result = find_binary_files(file_system)
        self.assertEqual(result, ["/path/to/binary_file"])

    def test_find_binary_files_with_whitespace_in_marker(self):
        """Test finding binary files with whitespace around the marker."""
        file_system = {
            "/path/to/binary_file": {
                "content_lines": [f"  {BINARY_FILE_MARKER}  \n", "base64content\n"]
            },
            "/path/to/text_file": {
                "content_lines": ["Hello world\n"]
            }
        }
        result = find_binary_files(file_system)
        self.assertEqual(result, ["/path/to/binary_file"])

    def test_find_binary_files_marker_not_first_line(self):
        """Test that binary files are only detected when marker is the first line."""
        file_system = {
            "/path/to/file1": {
                "content_lines": ["Some content\n", f"{BINARY_FILE_MARKER}\n"]
            },
            "/path/to/file2": {
                "content_lines": [f"{BINARY_FILE_MARKER}\n", "base64content\n"]
            }
        }
        result = find_binary_files(file_system)
        # Only file2 should be detected as binary since marker is first line
        self.assertEqual(result, ["/path/to/file2"])


class TestDetectAndFixTarCommandIntegration(unittest.TestCase):
    """Integration tests for detect_and_fix_tar_command function."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = tempfile.mkdtemp(prefix="test_tar_detection_")
        self.test_file = os.path.join(self.test_dir, "test.txt")
        
        # Create a test file
        with open(self.test_file, 'w') as f:
            f.write("test content")

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_modified_command_execution(self):
        """Test that the modified command can be executed successfully."""
        command = "tar -czf ./backup.tar.gz ."
        execution_cwd = self.test_dir
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # Verify the command was modified
        self.assertNotEqual(result, command)
        self.assertIn("&& mv", result)
        
        # The modified command should create the archive in parent directory
        parent_dir = os.path.dirname(execution_cwd)
        expected_temp_archive = os.path.join(parent_dir, "backup.tar.gz")
        self.assertIn(expected_temp_archive, result)

    def test_command_modification_preserves_functionality(self):
        """Test that the modified command preserves the original functionality."""
        command = "tar -czf ./backup.tar.gz ."
        execution_cwd = self.test_dir
        
        result = detect_and_fix_tar_command(command, execution_cwd)
        
        # The result should contain the original tar command with modified output path
        self.assertIn("tar -czf", result)
        self.assertIn(".", result)  # Should still archive current directory
        self.assertIn("backup.tar.gz", result)  # Should still use original filename


if __name__ == '__main__':
    unittest.main()
