"""
Comprehensive tests for the claude_code SimulationEngine file_utils module.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

# Ensure package root is importable when tests run via py.test
sys.path.append(str(Path(__file__).resolve().parents[2]))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from claude_code.SimulationEngine.file_utils import (
    is_text_file, 
    is_binary_file, 
    get_mime_type, 
    read_file, 
    write_file,
    encode_to_base64, 
    decode_from_base64, 
    text_to_base64, 
    base64_to_text,
    file_to_base64, 
    base64_to_file, 
    _is_within_workspace, 
    _create_parent_directories,
    _should_ignore, 
    _is_ignored,
)


class TestIsTextFile(BaseTestCaseWithErrorHandler):
    """Test suite for the is_text_file function."""

    def test_is_text_file_python(self):
        """Test is_text_file with Python files."""
        self.assertTrue(is_text_file("script.py"))
        self.assertTrue(is_text_file("module.py"))
        self.assertTrue(is_text_file("/path/to/file.py"))

    def test_is_text_file_javascript(self):
        """Test is_text_file with JavaScript files."""
        self.assertTrue(is_text_file("app.js"))
        self.assertTrue(is_text_file("component.jsx"))
        self.assertTrue(is_text_file("types.ts"))
        self.assertTrue(is_text_file("component.tsx"))

    def test_is_text_file_markup(self):
        """Test is_text_file with markup files."""
        self.assertTrue(is_text_file("index.html"))
        self.assertTrue(is_text_file("data.xml"))
        self.assertTrue(is_text_file("styles.css"))
        self.assertTrue(is_text_file("config.json"))

    def test_is_text_file_config_files(self):
        """Test is_text_file with configuration files."""
        self.assertTrue(is_text_file("config.yaml"))
        self.assertTrue(is_text_file("docker.yml"))
        self.assertTrue(is_text_file("settings.toml"))
        self.assertTrue(is_text_file("app.ini"))
        # .env extension is not in TEXT_EXTENSIONS, so test the actual behavior
        self.assertFalse(is_text_file(".env"))  # .env has no extension, treated as unknown

    def test_is_text_file_documentation(self):
        """Test is_text_file with documentation files."""
        self.assertTrue(is_text_file("README.md"))
        self.assertTrue(is_text_file("docs.rst"))
        self.assertTrue(is_text_file("notes.txt"))
        self.assertTrue(is_text_file("changelog.log"))

    def test_is_text_file_shell_scripts(self):
        """Test is_text_file with shell scripts."""
        self.assertTrue(is_text_file("script.sh"))
        self.assertTrue(is_text_file("deploy.bash"))
        self.assertTrue(is_text_file("config.rc"))
        self.assertTrue(is_text_file("startup.ps1"))

    def test_is_text_file_case_insensitive(self):
        """Test is_text_file is case insensitive."""
        self.assertTrue(is_text_file("FILE.PY"))
        self.assertTrue(is_text_file("Script.JS"))
        self.assertTrue(is_text_file("Config.JSON"))

    def test_is_text_file_binary_files(self):
        """Test is_text_file returns False for binary files."""
        self.assertFalse(is_text_file("image.jpg"))
        self.assertFalse(is_text_file("document.pdf"))
        self.assertFalse(is_text_file("archive.zip"))
        self.assertFalse(is_text_file("program.exe"))

    def test_is_text_file_unknown_extension(self):
        """Test is_text_file with unknown extensions."""
        self.assertFalse(is_text_file("file.unknown"))
        self.assertFalse(is_text_file("file.xyz"))
        self.assertFalse(is_text_file("file"))  # No extension

    def test_is_text_file_empty_path(self):
        """Test is_text_file with empty path."""
        self.assertFalse(is_text_file(""))

    def test_is_text_file_no_extension(self):
        """Test is_text_file with files without extension."""
        self.assertFalse(is_text_file("Makefile"))
        self.assertFalse(is_text_file("Dockerfile"))
        self.assertFalse(is_text_file("/path/to/file_without_ext"))


class TestIsBinaryFile(BaseTestCaseWithErrorHandler):
    """Test suite for the is_binary_file function."""

    def test_is_binary_file_images(self):
        """Test is_binary_file with image files."""
        self.assertTrue(is_binary_file("photo.jpg"))
        self.assertTrue(is_binary_file("image.png"))
        self.assertTrue(is_binary_file("icon.gif"))
        self.assertTrue(is_binary_file("bitmap.bmp"))
        self.assertTrue(is_binary_file("vector.svg"))

    def test_is_binary_file_documents(self):
        """Test is_binary_file with document files."""
        self.assertTrue(is_binary_file("report.pdf"))
        self.assertTrue(is_binary_file("document.doc"))
        self.assertTrue(is_binary_file("spreadsheet.xlsx"))
        self.assertTrue(is_binary_file("presentation.pptx"))

    def test_is_binary_file_archives(self):
        """Test is_binary_file with archive files."""
        self.assertTrue(is_binary_file("backup.zip"))
        self.assertTrue(is_binary_file("archive.rar"))
        self.assertTrue(is_binary_file("data.tar"))
        self.assertTrue(is_binary_file("compressed.gz"))

    def test_is_binary_file_media(self):
        """Test is_binary_file with media files."""
        self.assertTrue(is_binary_file("song.mp3"))
        self.assertTrue(is_binary_file("video.mp4"))
        self.assertTrue(is_binary_file("audio.wav"))
        self.assertTrue(is_binary_file("movie.avi"))

    def test_is_binary_file_executables(self):
        """Test is_binary_file with executable files."""
        self.assertTrue(is_binary_file("program.exe"))
        self.assertTrue(is_binary_file("library.dll"))
        self.assertTrue(is_binary_file("app.app"))
        self.assertTrue(is_binary_file("installer.msi"))

    def test_is_binary_file_case_insensitive(self):
        """Test is_binary_file is case insensitive."""
        self.assertTrue(is_binary_file("IMAGE.JPG"))
        self.assertTrue(is_binary_file("Document.PDF"))
        self.assertTrue(is_binary_file("Archive.ZIP"))

    def test_is_binary_file_text_files(self):
        """Test is_binary_file returns False for text files."""
        self.assertFalse(is_binary_file("script.py"))
        self.assertFalse(is_binary_file("config.json"))
        self.assertFalse(is_binary_file("readme.md"))

    def test_is_binary_file_unknown_extension(self):
        """Test is_binary_file with unknown extensions."""
        self.assertFalse(is_binary_file("file.unknown"))
        self.assertFalse(is_binary_file("file.xyz"))
        self.assertFalse(is_binary_file("file"))  # No extension


class TestGetMimeType(BaseTestCaseWithErrorHandler):
    """Test suite for the get_mime_type function."""

    def test_get_mime_type_text_files(self):
        """Test get_mime_type with text files."""
        self.assertEqual(get_mime_type("script.py"), "text/x-python")
        self.assertEqual(get_mime_type("index.html"), "text/html")
        self.assertEqual(get_mime_type("style.css"), "text/css")
        self.assertEqual(get_mime_type("data.json"), "application/json")

    def test_get_mime_type_image_files(self):
        """Test get_mime_type with image files."""
        self.assertEqual(get_mime_type("photo.jpg"), "image/jpeg")
        self.assertEqual(get_mime_type("image.png"), "image/png")
        self.assertEqual(get_mime_type("icon.gif"), "image/gif")

    def test_get_mime_type_binary_files(self):
        """Test get_mime_type with binary files."""
        self.assertEqual(get_mime_type("document.pdf"), "application/pdf")
        self.assertEqual(get_mime_type("archive.zip"), "application/zip")

    def test_get_mime_type_unknown_extension(self):
        """Test get_mime_type with unknown extensions."""
        self.assertEqual(get_mime_type("file.unknown"), "application/octet-stream")
        self.assertEqual(get_mime_type("file"), "application/octet-stream")


class TestReadFile(BaseTestCaseWithErrorHandler):
    """Test suite for the read_file function."""

    def test_read_file_not_found(self):
        """Test read_file with non-existent file."""
        self.assert_error_behavior(
            func_to_call=read_file,
            expected_exception_type=FileNotFoundError,
            expected_message="File not found: /nonexistent/file.txt",
            file_path="/nonexistent/file.txt"
        )

    @patch('claude_code.SimulationEngine.file_utils.os.path.getsize')
    def test_read_file_too_large(self, mock_getsize):
        """Test read_file with file exceeding size limit."""
        mock_getsize.return_value = 60 * 1024 * 1024  # 60MB
        
        with patch('claude_code.SimulationEngine.file_utils.os.path.exists', return_value=True):
            self.assert_error_behavior(
                func_to_call=read_file,
                expected_exception_type=ValueError,
                expected_message="File too large: 62914560 bytes (max: 52428800)",
                file_path="/large/file.txt"
            )

    @patch('claude_code.SimulationEngine.file_utils.os.path.getsize')
    @patch('claude_code.SimulationEngine.file_utils.os.path.exists')
    def test_read_text_file_success(self, mock_exists, mock_getsize):
        """Test read_file successfully reading a text file."""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        file_content = "Hello, World!\nThis is a test file."
        
        with patch('builtins.open', mock_open(read_data=file_content)):
            result = read_file("test.py")
            
            self.assertEqual(result['content'], file_content)
            self.assertEqual(result['encoding'], 'text')
            self.assertEqual(result['mime_type'], 'text/x-python')
            self.assertEqual(result['size_bytes'], 1024)

    @patch('claude_code.SimulationEngine.file_utils.os.path.getsize')
    @patch('claude_code.SimulationEngine.file_utils.os.path.exists')
    def test_read_text_file_unicode_error(self, mock_exists, mock_getsize):
        """Test read_file handling UnicodeDecodeError."""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        
        # Mock UnicodeDecodeError for utf-8, then success with latin-1
        content_latin1 = "Caf\xe9"  # Latin-1 encoded café
        
        def side_effect(file, mode='r', encoding='utf-8', **kwargs):
            if encoding == 'utf-8':
                raise UnicodeDecodeError('utf-8', b'', 0, 1, 'invalid start byte')
            elif encoding == 'latin-1':
                return mock_open(read_data=content_latin1)()
            else:
                raise UnicodeDecodeError(encoding, b'', 0, 1, 'invalid')
        
        with patch('builtins.open', side_effect=side_effect):
            result = read_file("test.txt")
            
            self.assertEqual(result['content'], content_latin1)
            self.assertEqual(result['encoding'], 'text')

    @patch('claude_code.SimulationEngine.file_utils.os.path.getsize')
    @patch('claude_code.SimulationEngine.file_utils.os.path.exists')
    def test_read_text_file_all_encodings_fail(self, mock_exists, mock_getsize):
        """Test read_file when all text encodings fail."""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        
        def side_effect(*args, encoding='utf-8', **kwargs):
            raise UnicodeDecodeError(encoding, b'', 0, 1, 'invalid')
        
        with patch('builtins.open', side_effect=side_effect):
            self.assert_error_behavior(
                func_to_call=read_file,
                expected_exception_type=ValueError,
                expected_message="Could not decode file: test.txt",
                file_path="test.txt"
            )

    @patch('claude_code.SimulationEngine.file_utils.os.path.getsize')
    @patch('claude_code.SimulationEngine.file_utils.os.path.exists')
    def test_read_binary_file_success(self, mock_exists, mock_getsize):
        """Test read_file successfully reading a binary file."""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024
        binary_content = b'\x89PNG\r\n\x1a\n'  # PNG header
        expected_b64 = "iVBORw0KGgoAAAANSUhEUgAA"[:len(binary_content) * 4 // 3 + 4]
        
        with patch('builtins.open', mock_open(read_data=binary_content)):
            with patch('claude_code.SimulationEngine.file_utils.base64.b64encode') as mock_b64:
                mock_b64.return_value = b'encoded_content'
                
                result = read_file("image.png")
                
                self.assertEqual(result['content'], 'encoded_content')
                self.assertEqual(result['encoding'], 'base64')
                self.assertEqual(result['mime_type'], 'image/png')
                self.assertEqual(result['size_bytes'], 1024)

    def test_read_file_custom_size_limit(self):
        """Test read_file with custom size limit."""
        with patch('claude_code.SimulationEngine.file_utils.os.path.exists', return_value=True):
            with patch('claude_code.SimulationEngine.file_utils.os.path.getsize', return_value=15 * 1024 * 1024):  # 15MB
                self.assert_error_behavior(
                    func_to_call=read_file,
                    expected_exception_type=ValueError,
                    expected_message="File too large: 15728640 bytes (max: 10485760)",
                    file_path="large_file.txt",
                    max_size_mb=10
                )


class TestWriteFile(BaseTestCaseWithErrorHandler):
    """Test suite for the write_file function."""

    @patch('claude_code.SimulationEngine.file_utils.os.makedirs')
    def test_write_text_file(self, mock_makedirs):
        """Test write_file writing text content."""
        content = "Hello, World!"
        
        with patch('builtins.open', mock_open()) as mock_file:
            write_file("/path/to/file.txt", content, encoding='text')
            
            mock_makedirs.assert_called_once_with("/path/to", exist_ok=True)
            mock_file.assert_called_once_with("/path/to/file.txt", 'w', encoding='utf-8')
            mock_file().write.assert_called_once_with(content)

    @patch('claude_code.SimulationEngine.file_utils.os.makedirs')
    def test_write_text_file_bytes_content(self, mock_makedirs):
        """Test write_file writing bytes as text."""
        content = b"Hello, World!"
        
        with patch('builtins.open', mock_open()) as mock_file:
            write_file("/path/to/file.txt", content, encoding='text')
            
            mock_file.assert_called_once_with("/path/to/file.txt", 'w', encoding='utf-8')
            mock_file().write.assert_called_once_with("Hello, World!")

    @patch('claude_code.SimulationEngine.file_utils.os.makedirs')
    @patch('claude_code.SimulationEngine.file_utils.base64.b64decode')
    def test_write_base64_file_string_content(self, mock_b64decode, mock_makedirs):
        """Test write_file writing base64 string content."""
        content = "SGVsbG8sIFdvcmxkIQ=="  # "Hello, World!" in base64
        decoded_content = b"Hello, World!"
        mock_b64decode.return_value = decoded_content
        
        with patch('builtins.open', mock_open()) as mock_file:
            write_file("/path/to/file.bin", content, encoding='base64')
            
            mock_makedirs.assert_called_once_with("/path/to", exist_ok=True)
            mock_b64decode.assert_called_once_with(content)
            mock_file.assert_called_once_with("/path/to/file.bin", 'wb')
            mock_file().write.assert_called_once_with(decoded_content)

    @patch('claude_code.SimulationEngine.file_utils.os.makedirs')
    def test_write_base64_file_bytes_content(self, mock_makedirs):
        """Test write_file writing bytes as base64."""
        content = b"Hello, World!"
        
        with patch('builtins.open', mock_open()) as mock_file:
            write_file("/path/to/file.bin", content, encoding='base64')
            
            mock_makedirs.assert_called_once_with("/path/to", exist_ok=True)
            mock_file.assert_called_once_with("/path/to/file.bin", 'wb')
            mock_file().write.assert_called_once_with(content)


class TestBase64Utilities(BaseTestCaseWithErrorHandler):
    """Test suite for base64 utility functions."""

    def test_encode_to_base64_string(self):
        """Test encode_to_base64 with string input."""
        result = encode_to_base64("Hello, World!")
        expected = "SGVsbG8sIFdvcmxkIQ=="
        self.assertEqual(result, expected)

    def test_encode_to_base64_bytes(self):
        """Test encode_to_base64 with bytes input."""
        result = encode_to_base64(b"Hello, World!")
        expected = "SGVsbG8sIFdvcmxkIQ=="
        self.assertEqual(result, expected)

    def test_decode_from_base64(self):
        """Test decode_from_base64."""
        result = decode_from_base64("SGVsbG8sIFdvcmxkIQ==")
        expected = b"Hello, World!"
        self.assertEqual(result, expected)

    def test_text_to_base64(self):
        """Test text_to_base64."""
        result = text_to_base64("Hello, World!")
        expected = "SGVsbG8sIFdvcmxkIQ=="
        self.assertEqual(result, expected)

    def test_base64_to_text(self):
        """Test base64_to_text."""
        result = base64_to_text("SGVsbG8sIFdvcmxkIQ==")
        expected = "Hello, World!"
        self.assertEqual(result, expected)

    def test_file_to_base64(self):
        """Test file_to_base64."""
        content = b"Hello, World!"
        expected = "SGVsbG8sIFdvcmxkIQ=="
        
        with patch('builtins.open', mock_open(read_data=content)):
            result = file_to_base64("/path/to/file.txt")
            self.assertEqual(result, expected)

    @patch('claude_code.SimulationEngine.file_utils.os.makedirs')
    @patch('claude_code.SimulationEngine.file_utils.base64.b64decode')
    def test_base64_to_file(self, mock_b64decode, mock_makedirs):
        """Test base64_to_file."""
        base64_content = "SGVsbG8sIFdvcmxkIQ=="
        decoded_content = b"Hello, World!"
        mock_b64decode.return_value = decoded_content
        
        with patch('builtins.open', mock_open()) as mock_file:
            base64_to_file(base64_content, "/path/to/file.txt")
            
            mock_makedirs.assert_called_once_with("/path/to", exist_ok=True)
            mock_b64decode.assert_called_once_with(base64_content)
            mock_file.assert_called_once_with("/path/to/file.txt", 'wb')
            mock_file().write.assert_called_once_with(decoded_content)


class TestIsWithinWorkspace(BaseTestCaseWithErrorHandler):
    """Test suite for the _is_within_workspace function."""

    @patch('claude_code.SimulationEngine.file_utils.os.path.abspath')
    @patch('claude_code.SimulationEngine.file_utils.os.path.realpath')
    @patch('claude_code.SimulationEngine.file_utils.os.path.commonpath')
    def test_is_within_workspace_valid_path(self, mock_commonpath, mock_realpath, mock_abspath):
        """Test _is_within_workspace with valid path."""
        workspace_root = "/workspace"
        path = "/workspace/subdir/file.txt"
        
        mock_abspath.side_effect = lambda x: x
        mock_realpath.side_effect = lambda x: x
        mock_commonpath.return_value = workspace_root
        
        result = _is_within_workspace(path, workspace_root)
        
        self.assertTrue(result)
        mock_commonpath.assert_called_once_with([path, workspace_root])

    @patch('claude_code.SimulationEngine.file_utils.os.path.abspath')
    @patch('claude_code.SimulationEngine.file_utils.os.path.realpath')
    @patch('claude_code.SimulationEngine.file_utils.os.path.commonpath')
    def test_is_within_workspace_invalid_path(self, mock_commonpath, mock_realpath, mock_abspath):
        """Test _is_within_workspace with invalid path."""
        workspace_root = "/workspace"
        path = "/other/directory/file.txt"
        
        mock_abspath.side_effect = lambda x: x
        mock_realpath.side_effect = lambda x: x
        mock_commonpath.return_value = "/other/directory"  # Different from workspace_root
        
        result = _is_within_workspace(path, workspace_root)
        
        self.assertFalse(result)

    @patch('claude_code.SimulationEngine.file_utils.os.path.abspath')
    @patch('claude_code.SimulationEngine.file_utils.os.path.realpath')
    @patch('claude_code.SimulationEngine.file_utils.os.path.commonpath')
    def test_is_within_workspace_value_error(self, mock_commonpath, mock_realpath, mock_abspath):
        """Test _is_within_workspace handling ValueError."""
        workspace_root = "/workspace"
        path = "/other/directory/file.txt"
        
        mock_abspath.side_effect = lambda x: x
        mock_realpath.side_effect = lambda x: x
        mock_commonpath.side_effect = ValueError("No common path")
        
        result = _is_within_workspace(path, workspace_root)
        
        self.assertFalse(result)

    def test_is_within_workspace_real_paths(self):
        """Test _is_within_workspace with real path examples."""
        # Test case where path is within workspace
        result = _is_within_workspace("/workspace/subdir/file.txt", "/workspace")
        self.assertTrue(result)
        
        # Test case where path is outside workspace  
        result = _is_within_workspace("/other/file.txt", "/workspace")
        self.assertFalse(result)
        
        # Test case with relative paths that resolve within workspace
        result = _is_within_workspace("/workspace/subdir/../file.txt", "/workspace")
        self.assertTrue(result)


class TestCreateParentDirectories(BaseTestCaseWithErrorHandler):
    """Test suite for the _create_parent_directories function."""

    def test_create_parent_directories_already_exists(self):
        """Test _create_parent_directories when directory already exists."""
        fs = {"/workspace/subdir": {"path": "/workspace/subdir"}}
        workspace_root = "/workspace"
        
        _create_parent_directories("/workspace/subdir", fs, workspace_root)
        
        # Should not modify fs since directory already exists
        self.assertEqual(len(fs), 1)

    def test_create_parent_directories_workspace_root(self):
        """Test _create_parent_directories at workspace root."""
        fs = {}
        workspace_root = "/workspace"
        
        _create_parent_directories("/workspace", fs, workspace_root)
        
        # Should not create entry for workspace root
        self.assertEqual(len(fs), 0)

    @patch('claude_code.SimulationEngine.file_utils.datetime')
    def test_create_parent_directories_single_level(self, mock_datetime):
        """Test _create_parent_directories creating single directory."""
        mock_datetime.datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        
        fs = {}
        workspace_root = "/workspace"
        
        _create_parent_directories("/workspace/subdir", fs, workspace_root)
        
        expected_entry = {
            'path': '/workspace/subdir',
            'is_directory': True,
            'content_lines': [],
            'size_bytes': 0,
            'last_modified': '2024-01-01T12:00:00',
            'created': '2024-01-01T12:00:00',
        }
        
        self.assertIn('/workspace/subdir', fs)
        self.assertEqual(fs['/workspace/subdir'], expected_entry)

    @patch('claude_code.SimulationEngine.file_utils.datetime')
    def test_create_parent_directories_multiple_levels(self, mock_datetime):
        """Test _create_parent_directories creating nested directories."""
        mock_datetime.datetime.now.return_value.isoformat.return_value = "2024-01-01T12:00:00"
        
        fs = {}
        workspace_root = "/workspace"
        
        _create_parent_directories("/workspace/subdir/deep/nested", fs, workspace_root)
        
        # Should create all intermediate directories
        self.assertIn('/workspace/subdir', fs)
        self.assertIn('/workspace/subdir/deep', fs)
        self.assertIn('/workspace/subdir/deep/nested', fs)
        
        # All should be marked as directories
        for path in ['/workspace/subdir', '/workspace/subdir/deep', '/workspace/subdir/deep/nested']:
            self.assertTrue(fs[path]['is_directory'])
            self.assertEqual(fs[path]['content_lines'], [])
            self.assertEqual(fs[path]['size_bytes'], 0)


class TestShouldIgnore(BaseTestCaseWithErrorHandler):
    """Test suite for the _should_ignore function."""

    def test_should_ignore_no_patterns(self):
        """Test _should_ignore with no patterns."""
        result = _should_ignore("/path/to/file.txt", [])
        self.assertFalse(result)

    def test_should_ignore_matching_pattern(self):
        """Test _should_ignore with matching pattern."""
        patterns = ["*.txt", "*.log"]
        result = _should_ignore("/path/to/file.txt", patterns)
        self.assertTrue(result)

    def test_should_ignore_non_matching_pattern(self):
        """Test _should_ignore with non-matching pattern."""
        patterns = ["*.log", "*.tmp"]
        result = _should_ignore("/path/to/file.txt", patterns)
        self.assertFalse(result)

    def test_should_ignore_complex_patterns(self):
        """Test _should_ignore with complex glob patterns."""
        patterns = ["**/node_modules/**", "*.pyc", "test_*"]
        
        self.assertTrue(_should_ignore("/project/node_modules/package/file.js", patterns))
        self.assertTrue(_should_ignore("module.pyc", patterns))
        self.assertTrue(_should_ignore("test_file.py", patterns))
        self.assertFalse(_should_ignore("src/main.py", patterns))

    def test_should_ignore_directory_patterns(self):
        """Test _should_ignore with directory-specific patterns."""
        patterns = ["__pycache__", "*.egg-info"]
        
        self.assertTrue(_should_ignore("__pycache__", patterns))
        self.assertTrue(_should_ignore("package.egg-info", patterns))
        self.assertFalse(_should_ignore("main.py", patterns))

    def test_should_ignore_case_sensitive(self):
        """Test _should_ignore is case sensitive."""
        patterns = ["*.TXT"]
        
        self.assertTrue(_should_ignore("file.TXT", patterns))
        self.assertFalse(_should_ignore("file.txt", patterns))  # Different case


class TestIsIgnored(BaseTestCaseWithErrorHandler):
    """Test suite for the _is_ignored function."""

    def test_is_ignored_no_gitignore(self):
        """Test _is_ignored when .gitignore doesn't exist."""
        workspace_root = "/workspace"
        path = "/workspace/file.txt"
        
        with patch('claude_code.SimulationEngine.file_utils.os.path.exists', return_value=False):
            result = _is_ignored(path, workspace_root)
            self.assertFalse(result)

    def test_is_ignored_respect_git_ignore_false(self):
        """Test _is_ignored with respect_git_ignore=False."""
        workspace_root = "/workspace"
        path = "/workspace/file.txt"
        
        result = _is_ignored(path, workspace_root, respect_git_ignore=False)
        self.assertFalse(result)

    @patch('claude_code.SimulationEngine.file_utils.os.path.exists')
    def test_is_ignored_with_gitignore_no_match(self, mock_exists):
        """Test _is_ignored with .gitignore but no matching patterns."""
        mock_exists.return_value = True
        workspace_root = "/workspace"
        path = "/workspace/file.txt"
        gitignore_content = "*.log\n*.tmp\n__pycache__\n"
        
        with patch('builtins.open', mock_open(read_data=gitignore_content)):
            with patch('claude_code.SimulationEngine.file_utils._should_ignore', return_value=False):
                result = _is_ignored(path, workspace_root)
                self.assertFalse(result)

    @patch('claude_code.SimulationEngine.file_utils.os.path.exists')
    def test_is_ignored_with_gitignore_match(self, mock_exists):
        """Test _is_ignored with .gitignore matching patterns."""
        mock_exists.return_value = True
        workspace_root = "/workspace"
        path = "/workspace/file.log"
        gitignore_content = "*.log\n*.tmp\n__pycache__\n"
        
        with patch('builtins.open', mock_open(read_data=gitignore_content)):
            with patch('claude_code.SimulationEngine.file_utils._should_ignore', return_value=True):
                result = _is_ignored(path, workspace_root)
                self.assertTrue(result)

    @patch('claude_code.SimulationEngine.file_utils.os.path.exists')
    @patch('builtins.open')
    def test_is_ignored_gitignore_processing(self, mock_open_file, mock_exists):
        """Test _is_ignored processes gitignore patterns correctly."""
        mock_exists.return_value = True
        workspace_root = "/workspace"
        path = "/workspace/build/output.log"
        gitignore_content = "*.log\nbuild/\n__pycache__/\n"
        
        mock_open_file.return_value.__enter__.return_value.read.return_value.splitlines.return_value = [
            "*.log", "build/", "__pycache__/"
        ]
        
        with patch('claude_code.SimulationEngine.file_utils._should_ignore') as mock_should_ignore:
            mock_should_ignore.return_value = True
            
            result = _is_ignored(path, workspace_root)
            
            self.assertTrue(result)
            # Verify _should_ignore was called with workspace-relative patterns
            mock_should_ignore.assert_called_once()
            args = mock_should_ignore.call_args[0]
            self.assertEqual(args[0], path)  # The path being checked
            expected_patterns = ["/workspace/*.log", "/workspace/build/", "/workspace/__pycache__/"]
            self.assertEqual(args[1], expected_patterns)


if __name__ == "__main__":
    unittest.main()
