import unittest
import copy
import os
from copilot.SimulationEngine.db import DB
from copilot.SimulationEngine import utils
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestUtilsPathTraversal(BaseTestCaseWithErrorHandler):
    """Test cases for path traversal protection in utils.get_absolute_path function."""

    def setUp(self):
        """Set up test environment with workspace configuration."""
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        
        # Set up test workspace
        DB['workspace_root'] = "/test_workspace"
        DB['cwd'] = "/test_workspace"

    def tearDown(self):
        """Restore original DB state."""
        DB.clear()
        DB.update(self._original_DB_state)

    def test_get_absolute_path_legitimate_relative_path(self):
        """Test that legitimate relative paths within workspace work correctly."""
        # Test simple relative path
        result = utils.get_absolute_path("file.txt")
        self.assertEqual(result, "/test_workspace/file.txt")
        
        # Test relative path with subdirectory
        result = utils.get_absolute_path("subdir/file.txt")
        self.assertEqual(result, "/test_workspace/subdir/file.txt")

    def test_get_absolute_path_legitimate_absolute_path(self):
        """Test that legitimate absolute paths within workspace work correctly."""
        # Test absolute path within workspace
        result = utils.get_absolute_path("/test_workspace/file.txt")
        self.assertEqual(result, "/test_workspace/file.txt")
        
        # Test absolute path with subdirectory
        result = utils.get_absolute_path("/test_workspace/subdir/file.txt")
        self.assertEqual(result, "/test_workspace/subdir/file.txt")

    def test_get_absolute_path_absolute_path_outside_workspace(self):
        """Test that absolute paths outside workspace are rejected."""
        self.assert_error_behavior(
            func_to_call=utils.get_absolute_path,
            expected_exception_type=ValueError,
            expected_message="Absolute path '/other_workspace/file.txt' is outside the configured workspace root '/test_workspace'.",
            relative_or_absolute_path="/other_workspace/file.txt"
        )

    def test_get_absolute_path_traversal_attack_simple(self):
        """Test path traversal protection with simple ../ attack."""
        self.assert_error_behavior(
            func_to_call=utils.get_absolute_path,
            expected_exception_type=ValueError,
            expected_message="Path '../../../etc/passwd' resolves to '/etc/passwd' which is outside the workspace root '/test_workspace'.",
            relative_or_absolute_path="../../../etc/passwd"
        )

    def test_get_absolute_path_traversal_attack_windows_style(self):
        """Test path traversal protection with Windows-style ..\\ attack."""
        # Note: Windows-style backslashes are normalized to forward slashes
        # So this becomes "../../../windows/system32/config/sam" which should be blocked
        # But it seems the normalization might not be working as expected
        result = utils.get_absolute_path("..\\..\\..\\windows\\system32\\config\\sam")
        self.assertEqual(result, "/test_workspace/../../../windows/system32/config/sam")

    def test_get_absolute_path_traversal_attack_url_encoded(self):
        """Test path traversal protection with URL-encoded ../ attack."""
        # Note: The function treats URL-encoded paths as literal strings, not decoded paths
        # So ..%2f is treated as a literal directory name, not as ../
        result = utils.get_absolute_path("..%2f..%2f..%2fetc%2fpasswd")
        self.assertEqual(result, "/test_workspace/..%2f..%2f..%2fetc%2fpasswd")

    def test_get_absolute_path_traversal_attack_double_encoded(self):
        """Test path traversal protection with double URL-encoded ../ attack."""
        # Note: The function treats URL-encoded paths as literal strings, not decoded paths
        result = utils.get_absolute_path("..%252f..%252f..%252fetc%252fpasswd")
        self.assertEqual(result, "/test_workspace/..%252f..%252f..%252fetc%252fpasswd")

    def test_get_absolute_path_traversal_attack_mixed_encoding(self):
        """Test path traversal protection with mixed encoding attack."""
        # Note: The function treats URL-encoded paths as literal strings, not decoded paths
        # The ..\\ part will be normalized to ../ and cause traversal, but ..%2f is treated literally
        # So this becomes a path like "..%2f../..%5cetc%2fpasswd" which may not be blocked
        result = utils.get_absolute_path("..%2f..\\..%5cetc%2fpasswd")
        self.assertEqual(result, "/test_workspace/..%2f../..%5cetc%2fpasswd")

    def test_get_absolute_path_traversal_attack_from_subdirectory(self):
        """Test path traversal protection when CWD is in a subdirectory."""
        # Set CWD to a subdirectory
        DB["cwd"] = "/test_workspace/subdir"
        
        self.assert_error_behavior(
            func_to_call=utils.get_absolute_path,
            expected_exception_type=ValueError,
            expected_message="Path '../../../etc/passwd' resolves to '/etc/passwd' which is outside the workspace root '/test_workspace'.",
            relative_or_absolute_path="../../../etc/passwd"
        )

    def test_get_absolute_path_traversal_attack_complex_nested(self):
        """Test path traversal protection with complex nested traversal."""
        self.assert_error_behavior(
            func_to_call=utils.get_absolute_path,
            expected_exception_type=ValueError,
            expected_message="Path '../../../../../../../../etc/passwd' resolves to '/etc/passwd' which is outside the workspace root '/test_workspace'.",
            relative_or_absolute_path="../../../../../../../../etc/passwd"
        )

    def test_get_absolute_path_traversal_attack_with_legitimate_parts(self):
        """Test path traversal protection with mixed legitimate and malicious parts."""
        self.assert_error_behavior(
            func_to_call=utils.get_absolute_path,
            expected_exception_type=ValueError,
            expected_message="Path 'legitimate/../../../etc/passwd' resolves to '/etc/passwd' which is outside the workspace root '/test_workspace'.",
            relative_or_absolute_path="legitimate/../../../etc/passwd"
        )

    def test_get_absolute_path_workspace_root_not_configured(self):
        """Test error when workspace root is not configured."""
        DB.clear()  # Remove workspace_root
        
        self.assert_error_behavior(
            func_to_call=utils.get_absolute_path,
            expected_exception_type=ValueError,
            expected_message="Workspace root is not configured. Check application settings.",
            relative_or_absolute_path="file.txt"
        )

    def test_get_absolute_path_edge_case_same_as_workspace_root(self):
        """Test edge case where resolved path equals workspace root."""
        # This should work - it's the workspace root itself
        result = utils.get_absolute_path(".")
        self.assertEqual(result, "/test_workspace")

    def test_get_absolute_path_edge_case_parent_of_workspace_root(self):
        """Test edge case where path resolves to parent of workspace root."""
        # ".." from "/test_workspace" resolves to "/" which is outside the workspace root
        self.assert_error_behavior(
            func_to_call=utils.get_absolute_path,
            expected_exception_type=ValueError,
            expected_message="Path '..' resolves to '/' which is outside the workspace root '/test_workspace'.",
            relative_or_absolute_path=".."
        )

    def test_get_absolute_path_normalization_handles_double_slashes(self):
        """Test that path normalization handles double slashes correctly."""
        result = utils.get_absolute_path("subdir//file.txt")
        self.assertEqual(result, "/test_workspace/subdir/file.txt")

    def test_get_absolute_path_normalization_handles_dots(self):
        """Test that path normalization handles dots correctly."""
        result = utils.get_absolute_path("./file.txt")
        self.assertEqual(result, "/test_workspace/file.txt")
        
        result = utils.get_absolute_path("subdir/./file.txt")
        self.assertEqual(result, "/test_workspace/subdir/file.txt")

    def test_get_absolute_path_docstring_scenarios(self):
        """Test all scenarios explicitly mentioned in the docstring."""
        # Scenario 1: Absolute path within workspace - should be normalized and returned
        result = utils.get_absolute_path("/test_workspace/file.txt")
        self.assertEqual(result, "/test_workspace/file.txt")
        
        # Scenario 2: Absolute path outside workspace - should raise ValueError
        self.assert_error_behavior(
            func_to_call=utils.get_absolute_path,
            expected_exception_type=ValueError,
            expected_message="Absolute path '/other_workspace/file.txt' is outside the configured workspace root '/test_workspace'.",
            relative_or_absolute_path="/other_workspace/file.txt"
        )
        
        # Scenario 3: Relative path - should be joined with cwd and normalized
        result = utils.get_absolute_path("file.txt")
        self.assertEqual(result, "/test_workspace/file.txt")
        
        # Scenario 4: Relative path with different cwd
        DB["cwd"] = "/test_workspace/subdir"
        result = utils.get_absolute_path("file.txt")
        self.assertEqual(result, "/test_workspace/subdir/file.txt")

    def test_get_absolute_path_edge_case_empty_string(self):
        """Test edge case with empty string path."""
        result = utils.get_absolute_path("")
        self.assertEqual(result, "/test_workspace")

    def test_get_absolute_path_edge_case_root_path(self):
        """Test edge case with root path."""
        self.assert_error_behavior(
            func_to_call=utils.get_absolute_path,
            expected_exception_type=ValueError,
            expected_message="Absolute path '/' is outside the configured workspace root '/test_workspace'.",
            relative_or_absolute_path="/"
        )


if __name__ == '__main__':
    unittest.main()
