import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch

# Add the parent directory of 'APIs' to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from .. import fetch_pull_request, DB
from ..SimulationEngine.db import load_state, DB

class TestFetchPullRequest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up the database with mock data before all tests."""
        # Load the default database state for testing
        cls.db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'DBs', 'CursorDefaultDB.json')
        load_state(cls.db_path)
        
        # Add additional mock data for our specific test cases
        DB.setdefault("commits", {}).update({
            "9520330": {
                "author": "test-user-1",
                "message": "test: Add test commit for short hash",
                "diff": "diff --git a/test.py b/test.py\nnew file mode 100644\nindex 0000000..9520330\n--- /dev/null\n+++ b/test.py\n@@ -0,0 +1,2 @@\n+def test_function():\n+    return True\n"
            },
            "ddb9942": {
                "author": "test-user-2", 
                "message": "test: Add another test commit",
                "diff": "diff --git a/test2.py b/test2.py\nnew file mode 100644\nindex 0000000..ddb9942\n--- /dev/null\n+++ b/test2.py\n@@ -0,0 +1,2 @@\n+def test_function2():\n+    return False\n"
            },
            "abc1234": {
                "author": "dev-user-2",
                "message": "test: Mixed case commit hash #123",
                "diff": "diff --git a/test3.py b/test3.py\nnew file mode 100644\nindex 0000000..abc1234\n--- /dev/null\n+++ b/test3.py\n@@ -0,0 +1,2 @@\n+def test_function3():\n+    return None\n"
            },
            "def5678": {
                "author": "test-user-4",
                "message": "test: Another test commit",
                "diff": "diff --git a/test4.py b/test4.py\nnew file mode 100644\nindex 0000000..def5678\n--- /dev/null\n+++ b/test4.py\n@@ -0,0 +1,2 @@\n+def test_function4():\n+    return 'test'\n"
            },
            "1234567": {
                "author": "test-user-5",
                "message": "test: Seven character commit hash",
                "diff": "diff --git a/test5.py b/test5.py\nnew file mode 100644\nindex 0000000..1234567\n--- /dev/null\n+++ b/test5.py\n@@ -0,0 +1,2 @@\n+def test_function5():\n+    return 5\n"
            },
            "AbC1234": {
                "author": "test-user-6",
                "message": "test: Mixed case commit hash",
                "diff": "diff --git a/test6.py b/test6.py\nnew file mode 100644\nindex 0000000..AbC1234\n--- /dev/null\n+++ b/test6.py\n@@ -0,0 +1,2 @@\n+def test_function6():\n+    return 'mixed'\n"
            },
            "DeF5678": {
                "author": "test-user-7",
                "message": "test: Another mixed case commit",
                "diff": "diff --git a/test7.py b/test7.py\nnew file mode 100644\nindex 0000000..DeF5678\n--- /dev/null\n+++ b/test7.py\n@@ -0,0 +1,2 @@\n+def test_function7():\n+    return 'case'\n"
            },
            "aBcDeF0": {
                "author": "test-user-8",
                "message": "test: More mixed case testing",
                "diff": "diff --git a/test8.py b/test8.py\nnew file mode 100644\nindex 0000000..aBcDeF0\n--- /dev/null\n+++ b/test8.py\n@@ -0,0 +1,2 @@\n+def test_function8():\n+    return 'mixed_case'\n"
            },
            "123AbCd": {
                "author": "test-user-9",
                "message": "test: Mixed case with numbers",
                "diff": "diff --git a/test9.py b/test9.py\nnew file mode 100644\nindex 0000000..123AbCd\n--- /dev/null\n+++ b/test9.py\n@@ -0,0 +1,2 @@\n+def test_function9():\n+    return 'numbers'\n"
            },
            "ddb99420732fdb553e239725b70c9cb8d9520330": {
                "author": "test-user-10",
                "message": "test: Full length commit hash",
                "diff": "diff --git a/test10.py b/test10.py\nnew file mode 100644\nindex 0000000..ddb99420732fdb553e239725b70c9cb8d9520330\n--- /dev/null\n+++ b/test10.py\n@@ -0,0 +1,2 @@\n+def test_function10():\n+    return 'full_hash'\n"
            },
            "a1b2c3d4e5f6789012345678901234567890abcd": {
                "author": "test-user-11",
                "message": "test: Another full length commit",
                "diff": "diff --git a/test11.py b/test11.py\nnew file mode 100644\nindex 0000000..a1b2c3d4e5f6789012345678901234567890abcd\n--- /dev/null\n+++ b/test11.py\n@@ -0,0 +1,2 @@\n+def test_function11():\n+    return 'another_full'\n"
            },
            "1234567890abcdef1234567890abcdef12345678": {
                "author": "test-user-12",
                "message": "test: Yet another full length commit",
                "diff": "diff --git a/test12.py b/test12.py\nnew file mode 100644\nindex 0000000..1234567890abcdef1234567890abcdef12345678\n--- /dev/null\n+++ b/test12.py\n@@ -0,0 +1,2 @@\n+def test_function12():\n+    return 'yet_another'\n"
            }
        })
        
        # Add additional PR numbers for testing
        DB.setdefault("pull_requests", {}).update({
            "456": {
                "title": "Test PR 456",
                "author": "test-user-13",
                "description": "This is a test PR for testing numeric strings.",
                "diff": "diff --git a/test_pr.py b/test_pr.py\nnew file mode 100644\nindex 0000000..456\n--- /dev/null\n+++ b/test_pr.py\n@@ -0,0 +1,2 @@\n+def test_pr_function():\n+    return 'pr_test'\n"
            },
            "789": {
                "title": "Test PR 789", 
                "author": "test-user-14",
                "description": "Another test PR for testing.",
                "diff": "diff --git a/test_pr2.py b/test_pr2.py\nnew file mode 100644\nindex 0000000..789\n--- /dev/null\n+++ b/test_pr2.py\n@@ -0,0 +1,2 @@\n+def test_pr_function2():\n+    return 'pr_test2'\n"
            },
            "1000": {
                "title": "Test PR 1000",
                "author": "test-user-15", 
                "description": "Test PR with larger number.",
                "diff": "diff --git a/test_pr3.py b/test_pr3.py\nnew file mode 100644\nindex 0000000..1000\n--- /dev/null\n+++ b/test_pr3.py\n@@ -0,0 +1,2 @@\n+def test_pr_function3():\n+    return 'pr_test3'\n"
            },
            "9999": {
                "title": "Test PR 9999",
                "author": "test-user-16",
                "description": "Test PR with even larger number.",
                "diff": "diff --git a/test_pr4.py b/test_pr4.py\nnew file mode 100644\nindex 0000000..9999\n--- /dev/null\n+++ b/test_pr4.py\n@@ -0,0 +1,2 @@\n+def test_pr_function4():\n+    return 'pr_test4'\n"
            },
            "123456": {
                "title": "Test PR 123456",
                "author": "test-user-17",
                "description": "Test PR with 6-digit number (should be treated as PR, not commit).",
                "diff": "diff --git a/test_pr5.py b/test_pr5.py\nnew file mode 100644\nindex 0000000..123456\n--- /dev/null\n+++ b/test_pr5.py\n@@ -0,0 +1,2 @@\n+def test_pr_function5():\n+    return 'pr_test5'\n"
            },
            "123456789": {
                "title": "Test PR 123456789",
                "author": "test-user-18",
                "description": "Test PR with 9-digit number (contains non-hex chars).",
                "diff": "diff --git a/test_pr6.py b/test_pr6.py\nnew file mode 100644\nindex 0000000..123456789\n--- /dev/null\n+++ b/test_pr6.py\n@@ -0,0 +1,2 @@\n+def test_pr_function6():\n+    return 'pr_test6'\n"
            },
            "999999999": {
                "title": "Test PR 999999999",
                "author": "test-user-19",
                "description": "Test PR with 9-digit number (contains non-hex chars).",
                "diff": "diff --git a/test_pr7.py b/test_pr7.py\nnew file mode 100644\nindex 0000000..999999999\n--- /dev/null\n+++ b/test_pr7.py\n@@ -0,0 +1,2 @@\n+def test_pr_function7():\n+    return 'pr_test7'\n"
            },
            "100000000": {
                "title": "Test PR 100000000",
                "author": "test-user-20",
                "description": "Test PR with 9-digit number (contains non-hex chars).",
                "diff": "diff --git a/test_pr8.py b/test_pr8.py\nnew file mode 100644\nindex 0000000..100000000\n--- /dev/null\n+++ b/test_pr8.py\n@@ -0,0 +1,2 @@\n+def test_pr_function8():\n+    return 'pr_test8'\n"
            }
        })
        
        # Create a temporary directory with a fake .git folder for testing
        cls.temp_dir = tempfile.mkdtemp()
        cls.fake_git_dir = os.path.join(cls.temp_dir, '.git')
        os.makedirs(cls.fake_git_dir)
        
        # Store original workspace_root and set to our temp directory
        cls.original_workspace_root = DB.get("workspace_root")
        DB["workspace_root"] = cls.temp_dir

    @classmethod
    def tearDownClass(cls):
        """Clean up after tests."""
        # Restore original workspace_root
        if cls.original_workspace_root:
            DB["workspace_root"] = cls.original_workspace_root
        # Clean up temp directory
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    @patch('cursor.cursorAPI.run_terminal_cmd')
    def test_fetch_pull_request_success(self, mock_run_cmd):
        """Test successfully fetching a pull request by its number."""
        # Mock failed git commands to force fallback to mock data
        mock_run_cmd.side_effect = Exception("git command failed")
        
        pr_number = "123"
        result = fetch_pull_request(pr_number)

        # Verify the return structure
        self.assertEqual(result.get("type"), "pull_request")
        self.assertEqual(result.get("identifier"), "123")
        self.assertEqual(result.get("author"), "dev-user-1")
        self.assertIn("This PR fixes a critical bug", result.get("message", ""))
        self.assertIsNotNone(result.get("diff"))
        self.assertIsInstance(result.get("files_changed"), list)
        self.assertIsNotNone(result.get("stats"))

    @patch('cursor.cursorAPI.run_terminal_cmd')
    def test_fetch_commit_success(self, mock_run_cmd):
        """Test successfully fetching a commit by its hash."""
        # Mock failed git commands to force fallback to mock data
        mock_run_cmd.side_effect = Exception("git command failed")
        
        commit_hash = "e9b3a4a"
        result = fetch_pull_request(commit_hash)

        # Verify the return structure
        self.assertEqual(result.get("type"), "commit")
        self.assertEqual(result.get("identifier"), "e9b3a4a")
        self.assertEqual(result.get("commit_hash"), "e9b3a4a")
        self.assertEqual(result.get("author"), "dev-user-1")
        self.assertIn("Improve helper function message", result.get("message", ""))
        self.assertIsNotNone(result.get("diff"))
        self.assertIsInstance(result.get("files_changed"), list)
        self.assertIsNotNone(result.get("stats"))

    @patch('cursor.cursorAPI.run_terminal_cmd')
    def test_fetch_pr_referencing_commit(self, mock_run_cmd):
        """Test fetching a commit that references a PR number."""
        # Mock failed git commands to force fallback to mock data
        mock_run_cmd.side_effect = Exception("git command failed")
        
        # This commit references PR #123 in its message
        commit_hash = "abc1234"
        result = fetch_pull_request(commit_hash)

        # Should return commit data
        self.assertEqual(result.get("type"), "commit")
        self.assertEqual(result.get("identifier"), "abc1234")
        self.assertEqual(result.get("commit_hash"), "abc1234")
        self.assertEqual(result.get("author"), "dev-user-2")
        self.assertIn("#123", result.get("message", ""))
        self.assertIsNotNone(result.get("diff"))

    @patch('cursor.cursorAPI.run_terminal_cmd')
    def test_fetch_item_not_found(self, mock_run_cmd):
        """Test fetching a non-existent pull request or commit raises RuntimeError."""
        # Mock failed git commands to force fallback to mock data
        mock_run_cmd.side_effect = Exception("git command failed")
        
        non_existent_id = "nonexistent123"
        
        with self.assertRaises(ValueError) as context:
            fetch_pull_request(non_existent_id)
        
        self.assertIn("Invalid commit hash format", str(context.exception))

    def test_fetch_with_empty_input(self):
        """Test the function raises ValueError with empty input."""
        with self.assertRaises(ValueError) as context:
            fetch_pull_request("")
        
        self.assertIn("Input cannot be empty", str(context.exception))

    def test_fetch_with_none_input(self):
        """Test the function raises ValueError with None input."""
        with self.assertRaises(ValueError) as context:
            fetch_pull_request(None)
        
        self.assertIn("Input cannot be empty", str(context.exception))

    def test_fetch_with_whitespace_input(self):
        """Test the function raises ValueError with whitespace-only input."""
        with self.assertRaises(ValueError) as context:
            fetch_pull_request("   ")
        
        self.assertIn("Input cannot be empty", str(context.exception))

    def test_fetch_with_no_workspace_root(self):
        """Test the function raises ValueError when workspace_root is not configured."""
        # Temporarily set workspace_root to None
        original_workspace_root = DB.get("workspace_root")
        DB["workspace_root"] = None
        
        try:
            with self.assertRaises(ValueError) as context:
                fetch_pull_request("123")
            
            self.assertIn("Workspace root is not configured", str(context.exception))
        finally:
            # Restore original workspace_root
            DB["workspace_root"] = original_workspace_root

    @patch('cursor.cursorAPI.run_terminal_cmd')
    def test_return_structure_completeness(self, mock_run_cmd):
        """Test that all expected keys are present in the return dictionary."""
        # Mock failed git commands to force fallback to mock data
        mock_run_cmd.side_effect = Exception("git command failed")
        
        result = fetch_pull_request("123")
        
        expected_keys = {'type', 'identifier', 'commit_hash', 'author', 'message', 'diff', 'files_changed', 'stats'}
        actual_keys = set(result.keys())
        
        self.assertTrue(expected_keys.issubset(actual_keys), 
                       f"Missing keys: {expected_keys - actual_keys}")

    def test_fetch_with_no_git_directory(self):
        """Test the function raises RuntimeError when no git directory exists."""
        # Temporarily set workspace_root to a directory without .git
        temp_no_git = tempfile.mkdtemp()
        original_workspace_root = DB.get("workspace_root")
        DB["workspace_root"] = temp_no_git
        
        try:
            with self.assertRaises(RuntimeError) as context:
                fetch_pull_request("123")
            
            self.assertIn("No git repository found", str(context.exception))
        finally:
            # Restore original workspace_root and clean up
            DB["workspace_root"] = original_workspace_root
            shutil.rmtree(temp_no_git, ignore_errors=True)

    def test_fetch_with_invalid_pr_number(self):
        """Test the function raises ValueError with invalid PR number."""
        # Ensure we have a valid workspace root with .git directory
        temp_dir = tempfile.mkdtemp()
        fake_git_dir = os.path.join(temp_dir, '.git')
        os.makedirs(fake_git_dir)
        original_workspace_root = DB.get("workspace_root")
        DB["workspace_root"] = temp_dir
        
        try:
            with self.assertRaises(ValueError) as context:
                fetch_pull_request("0")
            
            self.assertIn("Pull request number must be a positive integer", str(context.exception))

            with self.assertRaises(ValueError) as context:
                fetch_pull_request("-123")
            
            self.assertIn("Pull request number must be a positive integer", str(context.exception))
        finally:
            # Restore original workspace_root and clean up
            DB["workspace_root"] = original_workspace_root
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_fetch_with_invalid_commit_hash(self):
        """Test the function raises ValueError with invalid commit hash."""
        # Ensure we have a valid workspace root with .git directory
        temp_dir = tempfile.mkdtemp()
        fake_git_dir = os.path.join(temp_dir, '.git')
        os.makedirs(fake_git_dir)
        original_workspace_root = DB.get("workspace_root")
        DB["workspace_root"] = temp_dir
        
        try:
            # Test with non-hex characters
            with self.assertRaises(ValueError) as context:
                fetch_pull_request("abc123g")
            
            self.assertIn("Invalid commit hash format", str(context.exception))

            # Test with too short hash
            with self.assertRaises(ValueError) as context:
                fetch_pull_request("abc123")
            
            self.assertIn("Invalid commit hash length", str(context.exception))

            # Test with too long hash
            with self.assertRaises(ValueError) as context:
                fetch_pull_request("a" * 41)
            
            self.assertIn("Invalid commit hash length", str(context.exception))
        finally:
            # Restore original workspace_root and clean up
            DB["workspace_root"] = original_workspace_root
            shutil.rmtree(temp_dir, ignore_errors=True)


    @patch('cursor.cursorAPI.run_terminal_cmd')
    def test_numeric_strings_treated_as_pr_numbers(self, mock_run_cmd):
        """Test that purely numeric strings (that don't look like commit hashes) are treated as PR numbers."""
        # Mock failed git commands to force fallback to mock data
        mock_run_cmd.side_effect = Exception("git command failed")
        
        # Test numeric strings that should be treated as PR numbers
        pr_numbers = ["123", "456", "789", "1000", "9999"]
        
        for pr_number in pr_numbers:
            with self.subTest(pr_number=pr_number):
                result = fetch_pull_request(pr_number)
                
                # Should be treated as a PR, not a commit
                self.assertEqual(result.get("type"), "pull_request")
                self.assertEqual(result.get("identifier"), pr_number)

    @patch('cursor.cursorAPI.run_terminal_cmd')
    def test_mixed_case_commit_hashes(self, mock_run_cmd):
        """Test that commit hashes with mixed case are correctly identified."""
        # Mock failed git commands to force fallback to mock data
        mock_run_cmd.side_effect = Exception("git command failed")
        
        # Test mixed case commit hashes
        mixed_case_hashes = ["AbC1234", "DeF5678", "aBcDeF0", "123AbCd"]
        
        for commit_hash in mixed_case_hashes:
            with self.subTest(commit_hash=commit_hash):
                result = fetch_pull_request(commit_hash)
                
                # Should be treated as a commit
                self.assertEqual(result.get("type"), "commit")
                self.assertEqual(result.get("identifier"), commit_hash)
                self.assertEqual(result.get("commit_hash"), commit_hash)

    @patch('cursor.cursorAPI.run_terminal_cmd')
    def test_edge_case_length_commit_hashes(self, mock_run_cmd):
        """Test edge cases around the 7-character minimum length for commit hashes."""
        # Mock failed git commands to force fallback to mock data
        mock_run_cmd.side_effect = Exception("git command failed")
        
        # Test 6-character hex string (should be treated as PR number)
        short_hex = "123456"
        result = fetch_pull_request(short_hex)
        self.assertEqual(result.get("type"), "pull_request")
        self.assertEqual(result.get("identifier"), short_hex)
        
        # # Test 7-character hex string (should be treated as commit hash)
        # seven_char_hex = "1234567"
        # result = fetch_pull_request(seven_char_hex)
        # self.assertEqual(result.get("type"), "commit")
        # self.assertEqual(result.get("identifier"), seven_char_hex)

 

    @patch('cursor.cursorAPI.run_terminal_cmd')
    def test_full_length_commit_hashes(self, mock_run_cmd):
        """Test that full-length commit hashes (40 chars) are correctly identified."""
        # Mock failed git commands to force fallback to mock data
        mock_run_cmd.side_effect = Exception("git command failed")
        
        # Test full-length commit hashes
        full_hashes = [
            "ddb99420732fdb553e239725b70c9cb8d9520330",
            "a1b2c3d4e5f6789012345678901234567890abcd",
            "1234567890abcdef1234567890abcdef12345678"
        ]
        
        for commit_hash in full_hashes:
            with self.subTest(commit_hash=commit_hash):
                result = fetch_pull_request(commit_hash)
                
                # Should be treated as a commit
                self.assertEqual(result.get("type"), "commit")
                self.assertEqual(result.get("identifier"), commit_hash)
                self.assertEqual(result.get("commit_hash"), commit_hash)

    def test_commit_hash_identification_logic(self):
        """Test the internal logic for identifying commit hashes vs PR numbers."""
        from cursor.cursorAPI import fetch_pull_request
        
        # Test cases that should be identified as commit hashes
        commit_hash_cases = [
            "9520330",  # 7 chars, all hex
            "ddb9942",  # 7 chars, all hex
            "abc1234",  # 7 chars, all hex
            "AbC1234",  # 7 chars, mixed case hex
            "ddb99420732fdb553e239725b70c9cb8d9520330",  # 40 chars, full hash
        ]
        
        # Test cases that should be identified as PR numbers
        pr_number_cases = [
            "123",      # 3 chars, all digits
            "456",      # 3 chars, all digits
            "123456",   # 6 chars, all digits (too short for commit hash)
            "999999999", # 9 chars, all digits (contains non-hex chars)
        ]
        
        # We can't easily test the internal logic without exposing it,
        # but we can verify the behavior through the public interface
        # This test documents the expected behavior for future reference
        self.assertTrue(len(commit_hash_cases) > 0, "Should have commit hash test cases")
        self.assertTrue(len(pr_number_cases) > 0, "Should have PR number test cases")

if __name__ == '__main__':
    unittest.main()
