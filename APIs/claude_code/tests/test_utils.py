"""
Comprehensive tests for the claude_code SimulationEngine utils module.
"""

import os
import sys
import unittest
import logging
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.utils import (
    _log_util_message, 
    _get_home_directory, 
    _persist_db_state,
    _is_test_environment,
    _normalize_path_for_db,
    resolve_workspace_path,
    _collect_file_metadata,
    collect_pre_command_metadata_state,
    collect_post_command_metadata_state,
    preserve_unchanged_change_times,
    set_enable_common_file_system,
    update_common_directory,
    with_common_file_system
)

from ..SimulationEngine.db import reset_db, DB
from ..SimulationEngine.custom_errors import InvalidInputError


class TestLogUtilMessage(BaseTestCaseWithErrorHandler):
    """Test suite for the _log_util_message function."""

    def setUp(self):
        """Set up test environment."""
        # Reset any global state
        reset_db()
        # Create a mock logger to capture log calls
        self.mock_logger = MagicMock()

    @patch('claude_code.SimulationEngine.utils.logger')
    def test_log_error_level(self, mock_logger):
        """Test logging at ERROR level with exception info."""
        _log_util_message(logging.ERROR, "Test error message", exc_info=True)
        
        # Verify error was called with exc_info
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        self.assertEqual(kwargs['exc_info'], True)
        self.assertIn("Test error message", args[0])

    @patch('claude_code.SimulationEngine.utils.logger')
    def test_log_error_level_no_exc_info(self, mock_logger):
        """Test logging at ERROR level without exception info."""
        _log_util_message(logging.ERROR, "Test error message", exc_info=False)
        
        # Verify error was called without exc_info
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        self.assertEqual(kwargs['exc_info'], False)
        self.assertIn("Test error message", args[0])

    @patch('claude_code.SimulationEngine.utils.logger')
    def test_log_warning_level(self, mock_logger):
        """Test logging at WARNING level."""
        _log_util_message(logging.WARNING, "Test warning message", exc_info=True)
        
        mock_logger.warning.assert_called_once()
        args, kwargs = mock_logger.warning.call_args
        self.assertEqual(kwargs['exc_info'], True)
        self.assertIn("Test warning message", args[0])

    @patch('claude_code.SimulationEngine.utils.logger')
    def test_log_info_level(self, mock_logger):
        """Test logging at INFO level."""
        _log_util_message(logging.INFO, "Test info message")
        
        mock_logger.info.assert_called_once()
        args, _ = mock_logger.info.call_args
        self.assertIn("Test info message", args[0])

    @patch('claude_code.SimulationEngine.utils.logger')
    def test_log_debug_level(self, mock_logger):
        """Test logging at DEBUG level."""
        _log_util_message(logging.DEBUG, "Test debug message")
        
        mock_logger.debug.assert_called_once()
        args, _ = mock_logger.debug.call_args
        self.assertIn("Test debug message", args[0])

    @patch('claude_code.SimulationEngine.utils.logger')
    def test_log_with_caller_frame_info(self, mock_logger):
        """Test that caller frame information is included in log message."""
        def test_caller_function():
            _log_util_message(logging.INFO, "Test message from caller")
        
        test_caller_function()
        
        mock_logger.info.assert_called_once()
        args, _ = mock_logger.info.call_args
        log_message = args[0]
        
        # Should include function name and line number
        self.assertIn("test_caller_function:", log_message)
        self.assertIn("Test message from caller", log_message)

    @patch('claude_code.SimulationEngine.utils.logger')
    @patch('claude_code.SimulationEngine.utils.inspect.currentframe')
    def test_log_frame_extraction_exception(self, mock_currentframe, mock_logger):
        """Test behavior when frame extraction fails."""
        # Make frame extraction raise an exception
        mock_currentframe.side_effect = Exception("Frame extraction failed")
        
        _log_util_message(logging.INFO, "Test message")
        
        # Should still log the message without frame info
        mock_logger.info.assert_called_once()
        args, _ = mock_logger.info.call_args
        self.assertEqual(args[0], "Test message")

    @patch('claude_code.SimulationEngine.utils.logger')
    def test_log_with_none_caller_frame(self, mock_logger):
        """Test behavior when caller frame is None."""
        with patch('claude_code.SimulationEngine.utils.inspect.currentframe') as mock_frame:
            mock_current_frame = MagicMock()
            mock_current_frame.f_back = None
            mock_frame.return_value = mock_current_frame
            
            _log_util_message(logging.INFO, "Test message")
            
            # Should still log without frame info
            mock_logger.info.assert_called_once()
            args, _ = mock_logger.info.call_args
            self.assertEqual(args[0], "Test message")

    @patch('claude_code.SimulationEngine.utils.logger')
    def test_log_with_invalid_caller_code(self, mock_logger):
        """Test behavior when caller frame code is None."""
        with patch('claude_code.SimulationEngine.utils.inspect.currentframe') as mock_frame:
            mock_current_frame = MagicMock()
            mock_caller_frame = MagicMock()
            mock_caller_frame.f_code = None
            mock_current_frame.f_back = mock_caller_frame
            mock_frame.return_value = mock_current_frame
            
            _log_util_message(logging.INFO, "Test message")
            
            # Should still log without frame info
            mock_logger.info.assert_called_once()
            args, _ = mock_logger.info.call_args
            self.assertEqual(args[0], "Test message")


class TestGetHomeDirectory(BaseTestCaseWithErrorHandler):
    """Test suite for the _get_home_directory function."""

    def setUp(self):
        """Set up test environment."""
        # Reset any global state
        reset_db()

    def test_get_home_directory_with_workspace_root(self):
        """Test _get_home_directory when workspace_root exists in DB."""
        test_workspace = "/test/workspace/path"
        DB["workspace_root"] = test_workspace
        
        result = _get_home_directory()
        
        self.assertEqual(result, test_workspace)

    def test_get_home_directory_without_workspace_root(self):
        """Test _get_home_directory when workspace_root is not in DB."""
        # Ensure workspace_root is not set
        if "workspace_root" in DB:
            del DB["workspace_root"]
        
        result = _get_home_directory()
        
        self.assertEqual(result, "/home/user")

    def test_get_home_directory_with_empty_workspace_root(self):
        """Test _get_home_directory when workspace_root is empty string."""
        DB["workspace_root"] = ""
        
        result = _get_home_directory()
        
        self.assertEqual(result, "/home/user")

    def test_get_home_directory_with_none_workspace_root(self):
        """Test _get_home_directory when workspace_root is None."""
        DB["workspace_root"] = None
        
        result = _get_home_directory()
        
        self.assertEqual(result, "/home/user")

    def test_get_home_directory_with_whitespace_workspace_root(self):
        """Test _get_home_directory when workspace_root is only whitespace."""
        DB["workspace_root"] = "   "
        
        result = _get_home_directory()
        
        # Whitespace string is truthy, so should return it
        self.assertEqual(result, "   ")


class TestPersistDbState(BaseTestCaseWithErrorHandler):
    """Test suite for the _persist_db_state function."""

    def setUp(self):
        """Set up test environment."""
        # Reset any global state
        reset_db()

    @patch('claude_code.SimulationEngine.utils._is_test_environment')
    def test_persist_db_state_in_test_environment(self, mock_is_test_env):
        """Test _persist_db_state does nothing when in test environment."""
        mock_is_test_env.return_value = True
        
        # Mock the db module save_state function to ensure it's not called
        with patch('claude_code.SimulationEngine.db.save_state') as mock_save_state:
            _persist_db_state()
            
            # Should not call save_state when in test environment
            mock_save_state.assert_not_called()

    @patch('claude_code.SimulationEngine.utils._is_test_environment')
    @patch('claude_code.SimulationEngine.db.save_state')
    def test_persist_db_state_normal_operation(self, mock_save_state, mock_is_test_env):
        """Test _persist_db_state saves state in normal operation."""
        mock_is_test_env.return_value = False
        
        _persist_db_state()
        
        # Should call save_state with the default path
        mock_save_state.assert_called_once()
        # Check that it was called with some path (the _DEFAULT_DB_PATH)
        args, _ = mock_save_state.call_args
        self.assertEqual(len(args), 1)  # Should have one argument (the path)

    @patch('claude_code.SimulationEngine.utils._is_test_environment')
    @patch('claude_code.SimulationEngine.db.save_state')
    @patch('claude_code.SimulationEngine.utils.print_log')
    def test_persist_db_state_handles_save_exception(self, mock_print_log, mock_save_state, mock_is_test_env):
        """Test _persist_db_state handles exceptions during save."""
        mock_is_test_env.return_value = False
        mock_save_state.side_effect = Exception("Save failed")
        
        _persist_db_state()
        
        # Should call save_state
        mock_save_state.assert_called_once()
        # Should log the warning
        mock_print_log.assert_called_once()
        args, _ = mock_print_log.call_args
        self.assertIn("Warning: Could not persist DB state", args[0])
        self.assertIn("Save failed", args[0])

    @patch('claude_code.SimulationEngine.utils._is_test_environment')
    @patch('claude_code.SimulationEngine.utils.print_log')
    def test_persist_db_state_handles_import_exception(self, mock_print_log, mock_is_test_env):
        """Test _persist_db_state handles import exceptions."""
        mock_is_test_env.return_value = False
        
        # Mock the import to fail by raising an ImportError during the import
        with patch.dict('sys.modules', {'claude_code.SimulationEngine.db': None}):
            _persist_db_state()
            
            # Should log the warning
            mock_print_log.assert_called_once()
            args, _ = mock_print_log.call_args
            self.assertIn("Warning: Could not persist DB state", args[0])


class TestIsTestEnvironment(BaseTestCaseWithErrorHandler):
    """Test suite for the _is_test_environment function."""

    def setUp(self):
        """Set up test environment."""
        # Reset any global state
        reset_db()

    def test_is_test_environment_with_pytest_module(self):
        """Test _is_test_environment returns True when pytest is in sys.modules."""
        with patch.dict('sys.modules', {'pytest': MagicMock()}):
            self.assertTrue(_is_test_environment())

    def test_is_test_environment_with_unittest_module(self):
        """Test _is_test_environment returns True when unittest is in sys.modules."""
        with patch.dict('sys.modules', {'unittest': MagicMock()}):
            self.assertTrue(_is_test_environment())

    def test_is_test_environment_with_testing_env_var(self):
        """Test _is_test_environment returns True when TESTING env var is set."""
        with patch.dict('os.environ', {'TESTING': '1'}):
            self.assertTrue(_is_test_environment())

    def test_is_test_environment_with_test_mode_env_var(self):
        """Test _is_test_environment returns True when TEST_MODE env var is set."""
        with patch.dict('os.environ', {'TEST_MODE': 'true'}):
            self.assertTrue(_is_test_environment())

    def test_is_test_environment_with_pytest_current_test_env_var(self):
        """Test _is_test_environment returns True when PYTEST_CURRENT_TEST env var is set."""
        with patch.dict('os.environ', {'PYTEST_CURRENT_TEST': 'test_something.py::TestClass::test_method'}):
            self.assertTrue(_is_test_environment())

    def test_is_test_environment_with_pytest_in_argv(self):
        """Test _is_test_environment returns True when pytest is in sys.argv."""
        with patch.object(sys, 'argv', ['python', '-m', 'pytest', 'test_file.py']):
            self.assertTrue(_is_test_environment())

    def test_is_test_environment_with_test_in_argv(self):
        """Test _is_test_environment returns True when test is in sys.argv."""
        with patch.object(sys, 'argv', ['python', 'run_tests.py']):
            self.assertTrue(_is_test_environment())

    def test_is_test_environment_with_multiple_conditions(self):
        """Test _is_test_environment returns True when multiple conditions are met."""
        with patch.dict('sys.modules', {'pytest': MagicMock()}), \
             patch.dict('os.environ', {'TESTING': '1'}), \
             patch.object(sys, 'argv', ['python', '-m', 'pytest']):
            self.assertTrue(_is_test_environment())

    @patch('builtins.__import__')
    def test_is_test_environment_false_case(self, mock_import):
        """Test _is_test_environment returns False in normal environment."""
        # Mock sys and os modules with clean state
        mock_sys = MagicMock()
        mock_sys.modules = {}
        mock_sys.argv = ['python', 'normal_script.py']
        
        mock_os = MagicMock()
        mock_os.getenv.return_value = None
        
        # Mock the import to return our clean modules
        def side_effect(module_name, *args, **kwargs):
            if module_name == 'sys':
                return mock_sys
            elif module_name == 'os':
                return mock_os
            # For any other imports, use the real import
            return __import__(module_name, *args, **kwargs)
        
        mock_import.side_effect = side_effect
        
        self.assertFalse(_is_test_environment())

    def test_is_test_environment_env_var_empty_values(self):
        """Test _is_test_environment handles empty environment variable values."""
        # Test that empty strings are treated as falsy values
        with patch.dict('os.environ', {'TESTING': '', 'TEST_MODE': '', 'PYTEST_CURRENT_TEST': ''}):
            # Remove test modules from being detected 
            with patch.dict('sys.modules', {}, clear=False):
                # Remove pytest and unittest if they exist
                if 'pytest' in sys.modules:
                    del sys.modules['pytest']
                if 'unittest' in sys.modules:
                    del sys.modules['unittest']
                
                with patch.object(sys, 'argv', ['python', 'normal_script.py']):
                    # Even though env vars are set, they are empty strings (falsy)
                    # But since we're running in pytest, it will still detect test environment
                    # So we need to fully mock the function
                    with patch('builtins.__import__') as mock_import:
                        mock_sys = MagicMock()
                        mock_sys.modules = {}
                        mock_sys.argv = ['python', 'normal_script.py']
                        
                        mock_os = MagicMock()
                        mock_os.getenv.return_value = ''  # Empty string
                        
                        def side_effect(module_name, *args, **kwargs):
                            if module_name == 'sys':
                                return mock_sys
                            elif module_name == 'os':
                                return mock_os
                            return __import__(module_name, *args, **kwargs)
                        
                        mock_import.side_effect = side_effect
                        
                        self.assertFalse(_is_test_environment())

    def test_is_test_environment_case_sensitive_argv(self):
        """Test _is_test_environment is case sensitive for argv matching."""
        # Test that "test" matches even when in different case contexts
        with patch('builtins.__import__') as mock_import:
            mock_sys = MagicMock()
            mock_sys.modules = {}
            mock_sys.argv = ['python', 'PyTest', 'Test']  # Capitalized versions won't match
            
            mock_os = MagicMock()
            mock_os.getenv.return_value = None
            
            def side_effect(module_name, *args, **kwargs):
                if module_name == 'sys':
                    return mock_sys
                elif module_name == 'os':
                    return mock_os
                return __import__(module_name, *args, **kwargs)
            
            mock_import.side_effect = side_effect
            
            # Should return False because case-sensitive matching means "Test" != "test" and "PyTest" != "pytest"  
            self.assertFalse(_is_test_environment())

    def test_is_test_environment_argv_partial_match(self):
        """Test _is_test_environment matches substrings in argv."""
        # Test that "test" matches when it's part of a larger string
        with patch('builtins.__import__') as mock_import:
            mock_sys = MagicMock()
            mock_sys.modules = {}
            mock_sys.argv = ['python', 'run_tests.py', '--testing']  # Contains "test" substring
            
            mock_os = MagicMock()
            mock_os.getenv.return_value = None
            
            def side_effect(module_name, *args, **kwargs):
                if module_name == 'sys':
                    return mock_sys
                elif module_name == 'os':
                    return mock_os
                return __import__(module_name, *args, **kwargs)
            
            mock_import.side_effect = side_effect
            
            # Should return True because "run_tests.py" contains "test" and "--testing" contains "test"
            self.assertTrue(_is_test_environment())

    def test_is_test_environment_no_test_argv(self):
        """Test _is_test_environment returns False when argv has no test-related args."""
        with patch('builtins.__import__') as mock_import:
            mock_sys = MagicMock()
            mock_sys.modules = {}
            mock_sys.argv = ['python', 'myapp.py', '--verbose']  # No test-related args
            
            mock_os = MagicMock()
            mock_os.getenv.return_value = None
            
            def side_effect(module_name, *args, **kwargs):
                if module_name == 'sys':
                    return mock_sys
                elif module_name == 'os':
                    return mock_os
                return __import__(module_name, *args, **kwargs)
            
            mock_import.side_effect = side_effect
            
            self.assertFalse(_is_test_environment())


class TestNormalizePathForDb(BaseTestCaseWithErrorHandler):
    """Test suite for the _normalize_path_for_db function."""

    def setUp(self):
        """Set up test environment."""
        # Reset any global state
        reset_db()

    def test_normalize_path_for_db_none_input(self):
        """Test _normalize_path_for_db returns None for None input."""
        result = _normalize_path_for_db(None)
        self.assertIsNone(result)

    def test_normalize_path_for_db_empty_string(self):
        """Test _normalize_path_for_db with empty string."""
        result = _normalize_path_for_db("")
        self.assertEqual(result, ".")

    def test_normalize_path_for_db_simple_path(self):
        """Test _normalize_path_for_db with simple path."""
        result = _normalize_path_for_db("/home/user/file.txt")
        self.assertEqual(result, "/home/user/file.txt")

    def test_normalize_path_for_db_redundant_separators(self):
        """Test _normalize_path_for_db removes redundant separators."""
        result = _normalize_path_for_db("/home//user///file.txt")
        self.assertEqual(result, "/home/user/file.txt")

    def test_normalize_path_for_db_dot_segments(self):
        """Test _normalize_path_for_db resolves dot segments."""
        result = _normalize_path_for_db("/home/./user/../file.txt")
        self.assertEqual(result, "/home/file.txt")

    def test_normalize_path_for_db_double_backslashes(self):
        """Test _normalize_path_for_db replaces double backslashes with forward slashes."""
        result = _normalize_path_for_db("C:\\\\Users\\\\file.txt")
        self.assertEqual(result, "C:/Users/file.txt")

    def test_normalize_path_for_db_windows_path(self):
        """Test _normalize_path_for_db with Windows-style path."""
        result = _normalize_path_for_db("C:\\Users\\Documents\\file.txt")
        # os.path.normpath behavior depends on OS, but double backslashes should be replaced
        if os.name == 'nt':  # Windows
            expected = "C:\\Users\\Documents\\file.txt"
        else:  # Unix-like
            expected = "C:\\Users\\Documents\\file.txt"
        self.assertEqual(result, expected)

    def test_normalize_path_for_db_mixed_separators(self):
        """Test _normalize_path_for_db with mixed path separators."""
        result = _normalize_path_for_db("/home\\\\user/file.txt")
        # The function should normalize the path and replace double backslashes
        expected = "/home/user/file.txt"
        self.assertEqual(result, expected)

    def test_normalize_path_for_db_trailing_separator(self):
        """Test _normalize_path_for_db with trailing separator."""
        result = _normalize_path_for_db("/home/user/")
        # os.path.normpath typically removes trailing separators
        self.assertEqual(result, "/home/user")

    def test_normalize_path_for_db_root_path(self):
        """Test _normalize_path_for_db with root path."""
        result = _normalize_path_for_db("/")
        self.assertEqual(result, "/")

    def test_normalize_path_for_db_relative_path(self):
        """Test _normalize_path_for_db with relative path."""
        result = _normalize_path_for_db("../file.txt")
        self.assertEqual(result, "../file.txt")

    def test_normalize_path_for_db_multiple_double_backslashes(self):
        """Test _normalize_path_for_db with multiple double backslashes."""
        result = _normalize_path_for_db("C:\\\\Users\\\\Documents\\\\file.txt")
        self.assertEqual(result, "C:/Users/Documents/file.txt")

    def test_normalize_path_for_db_whitespace_path(self):
        """Test _normalize_path_for_db with whitespace in path."""
        result = _normalize_path_for_db("/home/user name/file.txt")
        self.assertEqual(result, "/home/user name/file.txt")

    def test_normalize_path_for_db_special_characters(self):
        """Test _normalize_path_for_db with special characters."""
        result = _normalize_path_for_db("/home/user@domain/file#1.txt")
        self.assertEqual(result, "/home/user@domain/file#1.txt")


class TestResolveWorkspacePath(BaseTestCaseWithErrorHandler):
    """Test suite for the resolve_workspace_path function."""

    def setUp(self):
        """Set up test environment."""
        # Reset any global state
        reset_db()
        self.workspace_root = "/workspace"

    def test_resolve_workspace_path_invalid_path_type(self):
        """Test resolve_workspace_path raises error for non-string path."""
        self.assert_error_behavior(
            func_to_call=resolve_workspace_path,
            expected_exception_type=InvalidInputError,
            expected_message="'path' must be a string",
            path=123,
            workspace_root=self.workspace_root
        )

    def test_resolve_workspace_path_invalid_workspace_root_type(self):
        """Test resolve_workspace_path raises error for non-string workspace_root."""
        self.assert_error_behavior(
            func_to_call=resolve_workspace_path,
            expected_exception_type=InvalidInputError,
            expected_message="'workspace_root' must be a non-empty string",
            path="test",
            workspace_root=123
        )

    def test_resolve_workspace_path_empty_workspace_root(self):
        """Test resolve_workspace_path raises error for empty workspace_root."""
        self.assert_error_behavior(
            func_to_call=resolve_workspace_path,
            expected_exception_type=InvalidInputError,
            expected_message="'workspace_root' must be a non-empty string",
            path="test",
            workspace_root=""
        )

    def test_resolve_workspace_path_whitespace_workspace_root(self):
        """Test resolve_workspace_path raises error for whitespace-only workspace_root."""
        self.assert_error_behavior(
            func_to_call=resolve_workspace_path,
            expected_exception_type=InvalidInputError,
            expected_message="'workspace_root' must be a non-empty string",
            path="test",
            workspace_root="   "
        )

    def test_resolve_workspace_path_relative_workspace_root(self):
        """Test resolve_workspace_path raises error for relative workspace_root."""
        self.assert_error_behavior(
            func_to_call=resolve_workspace_path,
            expected_exception_type=InvalidInputError,
            expected_message="'workspace_root' must be an absolute path",
            path="test",
            workspace_root="relative/path"
        )

    def test_resolve_workspace_path_empty_path(self):
        """Test resolve_workspace_path returns workspace_root for empty path."""
        result = resolve_workspace_path("", self.workspace_root)
        self.assertEqual(result, self.workspace_root)

    def test_resolve_workspace_path_whitespace_path(self):
        """Test resolve_workspace_path returns workspace_root for whitespace-only path."""
        result = resolve_workspace_path("   ", self.workspace_root)
        self.assertEqual(result, self.workspace_root)

    def test_resolve_workspace_path_dot_path(self):
        """Test resolve_workspace_path returns workspace_root for '.' path."""
        result = resolve_workspace_path(".", self.workspace_root)
        self.assertEqual(result, self.workspace_root)

    def test_resolve_workspace_path_root_separator_path(self):
        """Test resolve_workspace_path returns workspace_root for '/' path."""
        result = resolve_workspace_path("/", self.workspace_root)
        self.assertEqual(result, self.workspace_root)

    def test_resolve_workspace_path_relative_path(self):
        """Test resolve_workspace_path resolves relative path."""
        result = resolve_workspace_path("subdir/file.txt", self.workspace_root)
        expected = os.path.normpath(os.path.join(self.workspace_root, "subdir/file.txt"))
        self.assertEqual(result, expected)

    def test_resolve_workspace_path_relative_with_leading_slash(self):
        """Test resolve_workspace_path treats leading slash path as relative."""
        result = resolve_workspace_path("/subdir/file.txt", self.workspace_root)
        expected = os.path.normpath(os.path.join(self.workspace_root, "subdir/file.txt"))
        self.assertEqual(result, expected)

    def test_resolve_workspace_path_multiple_slashes(self):
        """Test resolve_workspace_path handles multiple leading slashes."""
        result = resolve_workspace_path("///subdir/file.txt", self.workspace_root)
        expected = os.path.normpath(os.path.join(self.workspace_root, "subdir/file.txt"))
        self.assertEqual(result, expected)

    def test_resolve_workspace_path_only_slashes(self):
        """Test resolve_workspace_path returns workspace_root for only slashes."""
        result = resolve_workspace_path("///", self.workspace_root)
        self.assertEqual(result, self.workspace_root)

    @patch('claude_code.SimulationEngine.utils._is_within_workspace')
    def test_resolve_workspace_path_absolute_within_workspace(self, mock_is_within):
        """Test resolve_workspace_path preserves absolute path within workspace."""
        mock_is_within.return_value = True
        absolute_path = "/workspace/subdir/file.txt"
        
        result = resolve_workspace_path(absolute_path, self.workspace_root)
        
        mock_is_within.assert_called_once()
        self.assertEqual(result, os.path.normpath(absolute_path))

    @patch('claude_code.SimulationEngine.utils._is_within_workspace')
    def test_resolve_workspace_path_absolute_outside_workspace(self, mock_is_within):
        """Test resolve_workspace_path treats absolute path outside workspace as relative."""
        mock_is_within.return_value = False
        absolute_path = "/other/path/file.txt"
        
        result = resolve_workspace_path(absolute_path, self.workspace_root)
        
        # Should strip leading slash and treat as relative
        expected = os.path.normpath(os.path.join(self.workspace_root, "other/path/file.txt"))
        self.assertEqual(result, expected)

    @patch('claude_code.SimulationEngine.utils._is_within_workspace')
    def test_resolve_workspace_path_workspace_validation_exception(self, mock_is_within):
        """Test resolve_workspace_path handles _is_within_workspace exceptions."""
        mock_is_within.side_effect = Exception("Validation failed")
        absolute_path = "/workspace/subdir/file.txt"
        
        result = resolve_workspace_path(absolute_path, self.workspace_root)
        
        # Should fall through and treat as relative
        expected = os.path.normpath(os.path.join(self.workspace_root, "workspace/subdir/file.txt"))
        self.assertEqual(result, expected)

    def test_resolve_workspace_path_workspace_root_normalization(self):
        """Test resolve_workspace_path normalizes workspace_root."""
        unnormalized_workspace = "/workspace//subdir/../"
        normalized_workspace = os.path.normpath(unnormalized_workspace)
        
        result = resolve_workspace_path(".", unnormalized_workspace)
        self.assertEqual(result, normalized_workspace)

    def test_resolve_workspace_path_complex_relative(self):
        """Test resolve_workspace_path with complex relative path."""
        result = resolve_workspace_path("../sibling/./file.txt", self.workspace_root)
        expected = os.path.normpath(os.path.join(self.workspace_root, "../sibling/./file.txt"))
        self.assertEqual(result, expected)

    def test_resolve_workspace_path_windows_style(self):
        """Test resolve_workspace_path with Windows-style paths."""
        # Use a proper absolute Windows path on non-Windows systems for testing
        workspace_root = "/c/workspace" if os.name != 'nt' else "C:\\workspace"
        result = resolve_workspace_path("subdir\\file.txt", workspace_root)
        expected = os.path.normpath(os.path.join(workspace_root, "subdir\\file.txt"))
        self.assertEqual(result, expected)


class TestCollectFileMetadata(BaseTestCaseWithErrorHandler):
    """Test suite for the _collect_file_metadata function."""

    def setUp(self):
        """Set up test environment."""
        reset_db()

    def test_collect_file_metadata_regular_file(self):
        """Test _collect_file_metadata with regular file path."""
        file_path = "/test/regular_file.txt"
        
        metadata = _collect_file_metadata(file_path)
        
        # Verify structure
        self.assertIn("attributes", metadata)
        self.assertIn("timestamps", metadata)
        
        # Verify attributes
        attrs = metadata["attributes"]
        self.assertFalse(attrs["is_symlink"])
        self.assertFalse(attrs["is_hidden"])
        self.assertFalse(attrs["is_readonly"])
        self.assertIsNone(attrs["symlink_target"])
        
        # Verify timestamps exist and are ISO format
        timestamps = metadata["timestamps"]
        for time_key in ["access_time", "modify_time", "change_time"]:
            self.assertIn(time_key, timestamps)
            # Check ISO format ends with Z
            self.assertTrue(timestamps[time_key].endswith("Z"))

    def test_collect_file_metadata_hidden_file(self):
        """Test _collect_file_metadata with hidden file (starts with dot)."""
        file_path = "/test/.hidden_file"
        
        metadata = _collect_file_metadata(file_path)
        
        # Hidden file should be detected
        self.assertTrue(metadata["attributes"]["is_hidden"])

    def test_collect_file_metadata_nested_path(self):
        """Test _collect_file_metadata with nested file path."""
        file_path = "/very/deep/nested/path/file.txt"
        
        metadata = _collect_file_metadata(file_path)
        
        # Should work with nested paths
        self.assertIn("attributes", metadata)
        self.assertIn("timestamps", metadata)
        self.assertFalse(metadata["attributes"]["is_hidden"])

    def test_collect_file_metadata_timestamp_consistency(self):
        """Test that timestamps are consistent within single call."""
        file_path = "/test/file.txt"
        
        metadata = _collect_file_metadata(file_path)
        
        timestamps = metadata["timestamps"]
        # All timestamps should be identical for simulation
        self.assertEqual(timestamps["access_time"], timestamps["modify_time"])
        self.assertEqual(timestamps["modify_time"], timestamps["change_time"])


class TestCollectMetadataStates(BaseTestCaseWithErrorHandler):
    """Test suite for collect_pre_command_metadata_state and collect_post_command_metadata_state functions."""

    def setUp(self):
        """Set up test environment."""
        reset_db()

    def test_collect_pre_command_metadata_state_empty_filesystem(self):
        """Test collect_pre_command_metadata_state with empty file system."""
        file_system = {}
        
        result = collect_pre_command_metadata_state(file_system)
        
        self.assertEqual(result, {})

    def test_collect_pre_command_metadata_state_with_files(self):
        """Test collect_pre_command_metadata_state with files."""
        file_system = {
            "/test/file1.txt": {"content": "test1"},
            "/test/file2.txt": {"content": "test2"},
            "/test/.hidden": {"content": "hidden"}
        }
        
        result = collect_pre_command_metadata_state(file_system)
        
        # Should have metadata for each file
        self.assertEqual(len(result), 3)
        for path in file_system.keys():
            self.assertIn(path, result)
            self.assertIn("metadata", result[path])
            self.assertIn("attributes", result[path]["metadata"])
            self.assertIn("timestamps", result[path]["metadata"])

    def test_collect_post_command_metadata_state_empty_filesystem(self):
        """Test collect_post_command_metadata_state with empty file system."""
        file_system = {}
        
        result = collect_post_command_metadata_state(file_system)
        
        self.assertEqual(result, {})

    def test_collect_post_command_metadata_state_with_files(self):
        """Test collect_post_command_metadata_state with files."""
        file_system = {
            "/test/file1.txt": {"content": "test1"},
            "/test/dir/file2.txt": {"content": "test2"}
        }
        
        result = collect_post_command_metadata_state(file_system)
        
        # Should have metadata for each file
        self.assertEqual(len(result), 2)
        for path in file_system.keys():
            self.assertIn(path, result)
            self.assertIn("metadata", result[path])

    def test_metadata_states_consistency(self):
        """Test that pre and post command metadata states have same structure."""
        file_system = {
            "/test/file.txt": {"content": "test"}
        }
        
        pre_result = collect_pre_command_metadata_state(file_system)
        post_result = collect_post_command_metadata_state(file_system)
        
        # Should have same keys
        self.assertEqual(list(pre_result.keys()), list(post_result.keys()))
        # Should have same structure
        for path in file_system.keys():
            self.assertEqual(
                list(pre_result[path].keys()),
                list(post_result[path].keys())
            )


class TestPreserveUnchangedChangeTimes(BaseTestCaseWithErrorHandler):
    """Test suite for the preserve_unchanged_change_times function."""

    def setUp(self):
        """Set up test environment."""
        reset_db()

    @patch('os.path.realpath')
    @patch('os.path.commonpath')
    @patch('os.path.relpath')
    def test_preserve_unchanged_change_times_basic(self, mock_relpath, mock_commonpath, mock_realpath):
        """Test preserve_unchanged_change_times basic functionality."""
        # Setup mocks
        mock_realpath.side_effect = lambda x: x  # Return input as-is
        mock_commonpath.return_value = "/workspace"  # Files are in workspace
        mock_relpath.return_value = "file.txt"
        
        # Test data
        original_time = "2023-01-01T00:00:00Z"
        current_time = "2023-01-02T00:00:00Z"
        
        db_file_system = {
            "/workspace/file.txt": {
                "metadata": {
                    "timestamps": {
                        "change_time": current_time
                    }
                }
            }
        }
        
        pre_command_state = {
            "/tmp/exec/file.txt": {
                "metadata": {
                    "timestamps": {
                        "change_time": original_time
                    }
                }
            }
        }
        
        post_command_state = {
            "/tmp/exec/file.txt": {
                "metadata": {
                    "timestamps": {
                        "change_time": original_time  # Same as pre (unchanged)
                    }
                }
            }
        }
        
        original_filesystem_state = {
            "/workspace/file.txt": {
                "metadata": {
                    "timestamps": {
                        "change_time": original_time
                    }
                }
            }
        }
        
        preserve_unchanged_change_times(
            db_file_system,
            pre_command_state,
            post_command_state,
            original_filesystem_state,
            "/workspace",
            "/tmp/exec"
        )
        
        # Should restore original time since file didn't change
        self.assertEqual(
            db_file_system["/workspace/file.txt"]["metadata"]["timestamps"]["change_time"],
            original_time
        )

    def test_preserve_unchanged_change_times_exception_handling(self):
        """Test preserve_unchanged_change_times handles exceptions gracefully."""
        db_file_system = {
            "/invalid/path": {
                "metadata": {
                    "timestamps": {
                        "change_time": "2023-01-02T00:00:00Z"
                    }
                }
            }
        }
        
        # Call with invalid paths that will cause exceptions
        preserve_unchanged_change_times(
            db_file_system,
            {},
            {},
            {},
            "/nonexistent",
            "/also/nonexistent"
        )
        
        # Should not crash and leave data unchanged
        self.assertIn("/invalid/path", db_file_system)

    def test_preserve_unchanged_change_times_missing_metadata(self):
        """Test preserve_unchanged_change_times with missing metadata."""
        db_file_system = {
            "/workspace/file.txt": {}  # No metadata
        }
        
        preserve_unchanged_change_times(
            db_file_system,
            {},
            {},
            {},
            "/workspace",
            "/tmp/exec"
        )
        
        # Should handle missing metadata gracefully
        self.assertEqual(db_file_system["/workspace/file.txt"], {})


class TestCommonFileSystemFunctions(BaseTestCaseWithErrorHandler):
    """Test suite for common file system functions."""

    def setUp(self):
        """Set up test environment."""
        reset_db()
        # Reset global state
        import claude_code.SimulationEngine.utils as utils_module
        utils_module.ENABLE_COMMON_FILE_SYSTEM = False
        utils_module.COMMON_DIRECTORY = None

    def tearDown(self):
        """Clean up test environment."""
        # Reset global state
        import claude_code.SimulationEngine.utils as utils_module
        utils_module.ENABLE_COMMON_FILE_SYSTEM = False
        utils_module.COMMON_DIRECTORY = None

    def test_set_enable_common_file_system_true(self):
        """Test set_enable_common_file_system with True."""
        set_enable_common_file_system(True)
        
        # Check global variable was set
        import claude_code.SimulationEngine.utils as utils_module
        self.assertTrue(utils_module.ENABLE_COMMON_FILE_SYSTEM)

    def test_set_enable_common_file_system_false(self):
        """Test set_enable_common_file_system with False."""
        set_enable_common_file_system(False)
        
        # Check global variable was set
        import claude_code.SimulationEngine.utils as utils_module
        self.assertFalse(utils_module.ENABLE_COMMON_FILE_SYSTEM)

    def test_set_enable_common_file_system_invalid_type(self):
        """Test set_enable_common_file_system with invalid type."""
        self.assert_error_behavior(
            func_to_call=set_enable_common_file_system,
            expected_exception_type=ValueError,
            expected_message="enable must be a boolean",
            enable="invalid"
        )

    @patch('os.makedirs')
    @patch('os.path.expanduser')
    @patch('os.path.isabs')
    def test_update_common_directory_success(self, mock_isabs, mock_expanduser, mock_makedirs):
        """Test update_common_directory with valid directory."""
        mock_expanduser.return_value = "/home/user/test_dir"
        mock_isabs.return_value = True
        
        with patch('claude_code.SimulationEngine.utils._log_util_message') as mock_log:
            update_common_directory("/home/user/test_dir")
        
        mock_makedirs.assert_called_once_with("/home/user/test_dir", exist_ok=True)
        mock_log.assert_called_once()

    @patch('os.path.expanduser')
    @patch('os.path.isabs')
    def test_update_common_directory_not_absolute(self, mock_isabs, mock_expanduser):
        """Test update_common_directory with relative path."""
        mock_expanduser.return_value = "relative/path"
        mock_isabs.return_value = False
        
        self.assert_error_behavior(
            func_to_call=update_common_directory,
            expected_exception_type=ValueError,
            expected_message="Common directory must be an absolute path",
            new_directory="relative/path"
        )

    def test_update_common_directory_empty_path_uses_default(self):
        """Test update_common_directory with empty path uses default."""
        # When empty path is passed, it should use DEFAULT_WORKSPACE
        with patch('os.makedirs'):
            with patch('os.path.expanduser', return_value='/Users/hsn/content/workspace'):
                with patch('os.path.isabs', return_value=True):
                    with patch('claude_code.SimulationEngine.utils._log_util_message') as mock_log:
                        update_common_directory("")
        
        # Should log that common directory was updated (using default)
        mock_log.assert_called_once()
        log_call = mock_log.call_args[0][1]
        self.assertIn("Common directory updated to:", log_call)

    def test_update_common_directory_none_path_uses_default(self):
        """Test update_common_directory with None path uses default."""
        # When None is passed, it should use DEFAULT_WORKSPACE
        with patch('os.makedirs'):
            with patch('os.path.expanduser', return_value='/Users/hsn/content/workspace'):
                with patch('os.path.isabs', return_value=True):
                    with patch('claude_code.SimulationEngine.utils._log_util_message') as mock_log:
                        update_common_directory(None)
        
        # Should log that common directory was updated (using default)
        mock_log.assert_called_once()
        log_call = mock_log.call_args[0][1]
        self.assertIn("Common directory updated to:", log_call)

    @patch('claude_code.SimulationEngine.utils.ENABLE_COMMON_FILE_SYSTEM', False)
    def test_with_common_file_system_disabled(self):
        """Test with_common_file_system decorator when disabled."""
        @with_common_file_system
        def test_func(x, y):
            return x + y
        
        result = test_func(1, 2)
        self.assertEqual(result, 3)

    @patch('claude_code.SimulationEngine.utils.ENABLE_COMMON_FILE_SYSTEM', True)
    @patch('claude_code.SimulationEngine.utils.hydrate_file_system_from_common_directory')
    @patch('claude_code.SimulationEngine.utils.dehydrate_file_system_to_common_directory')
    def test_with_common_file_system_enabled(self, mock_dehydrate, mock_hydrate):
        """Test with_common_file_system decorator when enabled."""
        @with_common_file_system
        def test_func(x, y):
            return x * y
    
        result = test_func(3, 4)
        self.assertEqual(result, 12)
        # Verify the decorator calls hydrate/dehydrate functions
        mock_hydrate.assert_called_once()
        mock_dehydrate.assert_called_once()

    @patch('claude_code.SimulationEngine.utils.ENABLE_COMMON_FILE_SYSTEM', True)
    @patch('claude_code.SimulationEngine.utils.hydrate_file_system_from_common_directory')
    @patch('claude_code.SimulationEngine.utils.dehydrate_file_system_to_common_directory')
    def test_with_common_file_system_exception_handling(self, mock_dehydrate, mock_hydrate):
        """Test with_common_file_system decorator handles exceptions."""
        @with_common_file_system
        def failing_func():
            raise RuntimeError("Test error")
        
        with patch('claude_code.SimulationEngine.utils._log_util_message') as mock_log:
            self.assert_error_behavior(
                func_to_call=failing_func,
                expected_exception_type=RuntimeError,
                expected_message="Test error"
            )
        
            # Verify hydrate was called but dehydrate may not be due to exception
            mock_hydrate.assert_called_once()
            # Check that exception logging was called
            mock_log.assert_called()
            log_call = mock_log.call_args_list[-1]  # Get the last call
            self.assertEqual(log_call[0][0], logging.ERROR)  # First arg is log level
            self.assertIn("Error in common file system wrapper for failing_func", log_call[0][1])  # Second arg is message

    def test_with_common_file_system_preserves_function_metadata(self):
        """Test with_common_file_system decorator preserves function metadata."""
        @with_common_file_system
        def documented_func():
            """This is a test function."""
            return "test"
        
        self.assertEqual(documented_func.__name__, "documented_func")
        self.assertEqual(documented_func.__doc__, "This is a test function.")

    @patch('claude_code.SimulationEngine.utils.ENABLE_COMMON_FILE_SYSTEM', True)
    @patch('claude_code.SimulationEngine.utils.hydrate_file_system_from_common_directory')
    def test_with_common_file_system_filenotfounderror_handling(self, mock_hydrate):
        """Test with_common_file_system decorator handles FileNotFoundError properly."""
        mock_hydrate.side_effect = FileNotFoundError("Common directory not found")
        
        @with_common_file_system
        def test_func():
            return "should not reach here"
        
        with patch('claude_code.SimulationEngine.utils._log_util_message') as mock_log:
            self.assert_error_behavior(
                func_to_call=test_func,
                expected_exception_type=FileNotFoundError,
                expected_message="Common directory not found"
            )
            
            # Verify error was logged and re-raised
            mock_log.assert_called()
            log_call = mock_log.call_args[0]
            self.assertEqual(log_call[0], logging.ERROR)
            self.assertIn("Common directory unavailable for test_func", log_call[1])


class TestGetCommonDirectory(BaseTestCaseWithErrorHandler):
    """Test suite for get_common_directory function."""

    def setUp(self):
        """Set up test environment."""
        reset_db()
        # Store original common_directory value
        import claude_code.SimulationEngine.utils as utils_module
        self.original_common_directory = utils_module.common_directory

    def tearDown(self):
        """Clean up test environment."""
        # Restore original common_directory value
        import claude_code.SimulationEngine.utils as utils_module
        utils_module.common_directory = self.original_common_directory

    def test_get_common_directory_success(self):
        """Test get_common_directory returns current directory."""
        import claude_code.SimulationEngine.utils as utils_module
        utils_module.common_directory = "/test/directory"
        
        from claude_code.SimulationEngine.utils import get_common_directory
        result = get_common_directory()
        self.assertEqual(result, "/test/directory")

    def test_get_common_directory_none_raises_error(self):
        """Test get_common_directory raises RuntimeError when common_directory is None."""
        import claude_code.SimulationEngine.utils as utils_module
        utils_module.common_directory = None
        
        from claude_code.SimulationEngine.utils import get_common_directory
        self.assert_error_behavior(
            func_to_call=get_common_directory,
            expected_exception_type=RuntimeError,
            expected_message="No common directory has been set. Call update_common_directory() first."
        )


class TestHydrateFileSystemFromCommonDirectory(BaseTestCaseWithErrorHandler):
    """Test suite for hydrate_file_system_from_common_directory function."""

    def setUp(self):
        """Set up test environment."""
        reset_db()

    def test_hydrate_file_system_directory_not_exists(self):
        """Test hydrate_file_system_from_common_directory with non-existent directory."""
        from claude_code.SimulationEngine.utils import hydrate_file_system_from_common_directory
        with patch('claude_code.SimulationEngine.utils.get_common_directory', return_value="/nonexistent"):
            with patch('os.path.exists', return_value=False):
                self.assert_error_behavior(
                    func_to_call=hydrate_file_system_from_common_directory,
                    expected_exception_type=FileNotFoundError,
                    expected_message="Common directory not found: /nonexistent"
                )

    def test_hydrate_file_system_path_not_directory(self):
        """Test hydrate_file_system_from_common_directory with file instead of directory."""
        from claude_code.SimulationEngine.utils import hydrate_file_system_from_common_directory
        with patch('claude_code.SimulationEngine.utils.get_common_directory', return_value="/test/file"):
            with patch('os.path.exists', return_value=True):
                with patch('os.path.isdir', return_value=False):
                    self.assert_error_behavior(
                        func_to_call=hydrate_file_system_from_common_directory,
                        expected_exception_type=FileNotFoundError,
                        expected_message="Common directory path is not a directory: /test/file"
                    )

    @patch('claude_code.SimulationEngine.utils.get_common_directory', return_value="/test/common")
    @patch('os.path.exists', return_value=True)
    @patch('os.path.isdir', return_value=True)
    @patch('claude_code.SimulationEngine.utils.common_utils.hydrate_db_from_directory')
    def test_hydrate_file_system_success(self, mock_hydrate_func, mock_isdir, mock_exists, mock_get_common):
        """Test successful hydrate_file_system_from_common_directory."""
        from claude_code.SimulationEngine.utils import hydrate_file_system_from_common_directory
        # Set up initial DB state with preserved data
        DB.update({
            "memory_storage": {"key": "value"},
            "tool_metrics": {"metric": 123},
            "file_system": {"old_file": "old_content"}
        })
        
        # Mock the hydration to set workspace_root and cwd correctly
        def mock_hydration(db_dict, common_dir):
            db_dict.update({
                "workspace_root": common_dir,
                "cwd": common_dir,
                "file_system": {"new_file": "new_content"}
            })
        
        mock_hydrate_func.side_effect = mock_hydration
        
        hydrate_file_system_from_common_directory()
        
        # Verify the function was called correctly
        mock_hydrate_func.assert_called_once_with(DB, "/test/common")
        
        # Verify preserved data is maintained
        self.assertEqual(DB.get("memory_storage"), {"key": "value"})
        self.assertEqual(DB.get("tool_metrics"), {"metric": 123})
        
        # Verify workspace paths are set correctly
        self.assertEqual(DB.get("workspace_root"), "/test/common")
        self.assertEqual(DB.get("cwd"), "/test/common")


class TestDehydrateFileSystemToCommonDirectory(BaseTestCaseWithErrorHandler):
    """Test suite for dehydrate_file_system_to_common_directory function."""

    def setUp(self):
        """Set up test environment."""
        reset_db()

    @patch('claude_code.SimulationEngine.utils.get_common_directory', return_value="/test/common")
    @patch('os.path.exists', return_value=True)
    @patch('os.listdir', return_value=['file1.txt', 'subdir'])
    @patch('os.path.isdir')
    @patch('shutil.rmtree')
    @patch('os.remove')
    @patch('claude_code.SimulationEngine.utils.common_utils.dehydrate_db_to_directory')
    def test_dehydrate_file_system_success(self, mock_dehydrate_func, mock_remove, mock_rmtree, 
                                         mock_isdir, mock_listdir, mock_exists, mock_get_common):
        """Test successful dehydrate_file_system_to_common_directory."""
        from claude_code.SimulationEngine.utils import dehydrate_file_system_to_common_directory
        # Setup mock responses for directory cleanup
        mock_isdir.side_effect = lambda path: path.endswith('subdir')
        
        # Set up DB with file system data
        DB.update({
            "workspace_root": "/old/workspace",
            "cwd": "/old/cwd",
            "file_system": {"test_file": "content"},
            "memory_storage": {"preserve": "this"}
        })
        
        dehydrate_file_system_to_common_directory()
        
        # Verify cleanup was performed (skipping .git)
        mock_rmtree.assert_called_once()
        mock_remove.assert_called_once()
        
        # Verify dehydrate function was called with correct temp_db
        mock_dehydrate_func.assert_called_once()
        temp_db_arg = mock_dehydrate_func.call_args[0][0]
        expected_temp_db = {
            "workspace_root": "/test/common",
            "cwd": "/test/common", 
            "file_system": {"test_file": "content"}
        }
        self.assertEqual(temp_db_arg, expected_temp_db)
        
        # Verify DB workspace paths were updated
        self.assertEqual(DB.get("workspace_root"), "/test/common")
        self.assertEqual(DB.get("cwd"), "/test/common")

    @patch('claude_code.SimulationEngine.utils.get_common_directory', return_value="/test/common")
    @patch('os.path.exists', return_value=True)  
    @patch('os.listdir', return_value=['.git', 'file1.txt'])
    @patch('os.path.isdir', return_value=False)
    @patch('os.remove')
    @patch('claude_code.SimulationEngine.utils._log_util_message')
    @patch('claude_code.SimulationEngine.utils.common_utils.dehydrate_db_to_directory')
    def test_dehydrate_file_system_preserves_git(self, mock_dehydrate_func, mock_log, mock_remove, 
                                                mock_isdir, mock_listdir, mock_exists, mock_get_common):
        """Test dehydrate_file_system_to_common_directory preserves .git directory."""
        from claude_code.SimulationEngine.utils import dehydrate_file_system_to_common_directory
        DB.update({"file_system": {}})
        
        dehydrate_file_system_to_common_directory()
        
        # Verify .git directory preservation was logged
        mock_log.assert_called()
        log_calls = [call[0][1] for call in mock_log.call_args_list]
        git_preserve_logged = any("Preserving .git directory during cleanup" in msg for msg in log_calls)
        self.assertTrue(git_preserve_logged)
        
        # Verify only non-.git files were removed
        mock_remove.assert_called_once_with('/test/common/file1.txt')


class TestMissingCoverageImprovements(BaseTestCaseWithErrorHandler):
    """Test suite for improving coverage of existing functions."""

    def setUp(self):
        """Set up test environment."""
        reset_db()

    def test_update_common_directory_empty_directory_error(self):
        """Test update_common_directory raises ValueError for empty directory after using default."""
        from claude_code.SimulationEngine.utils import update_common_directory
        with patch('claude_code.SimulationEngine.utils.DEFAULT_WORKSPACE', ''):
            self.assert_error_behavior(
                func_to_call=update_common_directory,
                expected_exception_type=ValueError,
                expected_message="Common directory path cannot be empty",
                new_directory=""
            )

    def test_preserve_unchanged_change_times_exception_handling(self):
        """Test preserve_unchanged_change_times handles exceptions during path mapping."""
        from claude_code.SimulationEngine.utils import preserve_unchanged_change_times
        # Set up test data that will cause exceptions during path operations
        db_file_system = {"/invalid/path": {"metadata": {"timestamps": {}}}}
        pre_command_state = {}
        post_command_state = {}
        original_filesystem_state = {}
        
        # Mock os.path.realpath to raise an exception
        with patch('os.path.realpath', side_effect=OSError("Path error")):
            # Should not raise exception, just continue with next file
            preserve_unchanged_change_times(
                db_file_system, pre_command_state, post_command_state, 
                original_filesystem_state, "/workspace", "/exec"
            )
            
        # Verify no changes were made due to exception
        self.assertEqual(db_file_system, {"/invalid/path": {"metadata": {"timestamps": {}}}})


if __name__ == '__main__':
    unittest.main()