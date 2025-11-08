"""
Comprehensive Utilities Test Suite for GitHub Actions Module.

This module tests core utility functions used across the GitHub Actions simulation,
including SHA validation, file operations, base64 encoding/decoding, repository management,
and data validation patterns.
"""

import unittest
import tempfile
import os
import copy
import base64
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from contextlib import contextmanager
from typing import Union, Type

from github_actions.SimulationEngine.utils import (
    is_valid_sha,
    add_repository,
    add_or_update_workflow,
    add_workflow_run,
    get_repository,
    get_workflow_by_id_or_filename,
    get_workflow_run_by_id,
    generate_random_sha,
    _parse_created_filter,
    _ensure_utc_datetime,
)
from github_actions.SimulationEngine.file_utils import (
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
    TEXT_EXTENSIONS,
    BINARY_EXTENSIONS,
)
from github_actions.SimulationEngine.db import DB
from github_actions.SimulationEngine.custom_errors import (
    NotFoundError,
    InvalidInputError,
    WorkflowDisabledError,
    ConflictError,
)


class BaseTestCase(unittest.TestCase):
    """Base test case class with custom assertion methods."""

    @contextmanager
    def assert_error_behaviour(self, expected_exception: Union[Type[Exception], tuple]):
        """Custom assertion method to replace assertRaises."""

        class ExceptionContext:
            def __init__(self):
                self.exception = None

        context = ExceptionContext()

        try:
            yield context
            self.fail(
                f"Expected {expected_exception} to be raised, but no exception was raised"
            )
        except expected_exception as e:
            context.exception = e
        except Exception as e:
            self.fail(
                f"Expected {expected_exception} to be raised, but {type(e).__name__} was raised instead"
            )


class TestSHAValidationAndGeneration(BaseTestCase):
    """Test SHA validation and generation utilities."""

    def test_valid_sha_formats(self):
        """Test validation of valid SHA formats."""
        valid_shas = [
            "da39a3ee5e6b4b0d3255bfef95601890afd80709",  # Empty string SHA-1
            "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d",  # "hello" SHA-1
            "DA39A3EE5E6B4B0D3255BFEF95601890AFD80709",  # Uppercase
            "Da39a3ee5e6b4b0d3255bfef95601890afd80709",  # Mixed case
            "0" * 40,  # All zeros
            "f" * 40,  # All f's
        ]

        for sha in valid_shas:
            with self.subTest(sha=sha):
                self.assertTrue(is_valid_sha(sha), f"SHA {sha} should be valid")

    def test_invalid_sha_formats(self):
        """Test validation of invalid SHA formats."""
        invalid_cases = [
            ("", "Empty string"),
            ("abc", "Too short"),
            ("da39a3ee5e6b4b0d3255bfef95601890afd8070", "39 chars"),
            ("da39a3ee5e6b4b0d3255bfef95601890afd80709a", "41 chars"),
            ("ga39a3ee5e6b4b0d3255bfef95601890afd80709", "Invalid char 'g'"),
            ("da39a3ee5e6b4b0d3255bfef95601890afd8070!", "Invalid char '!'"),
            (None, "None type"),
            (123, "Integer type"),
            (
                "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "SHA-256 not supported",
            ),
        ]

        for invalid_sha, description in invalid_cases:
            with self.subTest(sha=invalid_sha, desc=description):
                if isinstance(invalid_sha, str) or invalid_sha is None:
                    self.assertFalse(
                        is_valid_sha(invalid_sha), f"{description}: {invalid_sha}"
                    )
                else:
                    try:
                        result = is_valid_sha(invalid_sha)
                        self.assertFalse(result, f"{description}: {invalid_sha}")
                    except (TypeError, AttributeError):
                        pass  # Expected for non-string types

    def test_sha_generation(self):
        """Test SHA generation utility."""
        # Generate multiple SHAs and verify they're unique and valid
        generated_shas = set()
        for _ in range(10):
            sha = generate_random_sha()
            self.assertTrue(is_valid_sha(sha), f"Generated SHA {sha} should be valid")
            self.assertNotIn(sha, generated_shas, "Generated SHAs should be unique")
            generated_shas.add(sha)
            self.assertEqual(len(sha), 40, "Generated SHA should be 40 characters")


class TestFileTypeDetection(BaseTestCase):
    """Test file type detection utilities."""

    def test_file_type_detection_comprehensive(self):
        """Test text and binary file detection."""
        test_cases = [
            # Text files
            ("script.py", True, False),
            ("app.js", True, False),
            ("index.html", True, False),
            ("data.json", True, False),
            ("config.yml", True, False),
            ("README.md", True, False),
            ("FILE.PY", True, False),
            ("Script.JS", True, False),  # Case variations
            # Binary files
            ("image.jpg", False, True),
            ("photo.png", False, True),
            ("document.pdf", False, True),
            ("archive.zip", False, True),
            ("song.mp3", False, True),
            ("IMAGE.JPG", False, True),
            ("DOCUMENT.PDF", False, True),  # Case variations
            # Unknown files
            ("file.unknown", False, False),
            ("README", False, False),
            ("Makefile", False, False),
            ("", False, False),  # Empty filename
        ]

        for file_path, is_text, is_binary in test_cases:
            with self.subTest(file=file_path):
                self.assertEqual(
                    is_text_file(file_path), is_text, f"{file_path} text detection"
                )
                self.assertEqual(
                    is_binary_file(file_path),
                    is_binary,
                    f"{file_path} binary detection",
                )

    def test_mime_type_detection(self):
        """Test MIME type detection."""
        mime_tests = [
            ("file.html", "text/html"),
            ("script.js", "text/javascript"),
            ("style.css", "text/css"),
            ("data.json", "application/json"),
            ("image.jpg", "image/jpeg"),
            ("photo.png", "image/png"),
            ("document.pdf", "application/pdf"),
            ("archive.zip", "application/zip"),
            ("file.unknown", "application/octet-stream"),
            ("README", "application/octet-stream"),
        ]

        for file_path, expected_mime in mime_tests:
            with self.subTest(file=file_path):
                self.assertEqual(get_mime_type(file_path), expected_mime)

    def test_extension_sets_integrity(self):
        """Test file extension sets are properly defined."""
        # Verify expected extensions are present
        expected_text = [".py", ".js", ".html", ".json", ".md", ".yml", ".css", ".txt"]
        expected_binary = [".jpg", ".png", ".pdf", ".zip", ".exe", ".mp3"]

        for ext in expected_text:
            self.assertIn(ext, TEXT_EXTENSIONS, f"{ext} missing from TEXT_EXTENSIONS")

        for ext in expected_binary:
            self.assertIn(
                ext, BINARY_EXTENSIONS, f"{ext} missing from BINARY_EXTENSIONS"
            )

        # Check expected overlap
        overlap = TEXT_EXTENSIONS.intersection(BINARY_EXTENSIONS)
        self.assertEqual(
            overlap, {".svg", ".ts"}, f"Unexpected extension overlap: {overlap}"
        )


class TestFileOperations(BaseTestCase):
    """Test file reading, writing, and base64 operations."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_reading_comprehensive(self):
        """Test file reading with various content types."""
        test_cases = [
            ("Hello, World!\nBasic text", "basic.txt", "text"),
            ("Unicode: 🌍 中文 العربية", "unicode.txt", "text"),
            (bytes([0, 1, 2, 3, 255, 254, 253]), "binary.bin", "base64"),
        ]

        for content, filename, expected_encoding in test_cases:
            test_file = os.path.join(self.temp_dir, filename)

            if isinstance(content, str):
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                with open(test_file, "wb") as f:
                    f.write(content)

            result = read_file(test_file)

            # Group assertions
            read_assertions = [
                (result["encoding"], expected_encoding, "Encoding type"),
                ("content" in result, True, "Content field exists"),
                ("size_bytes" in result, True, "Size field exists"),
            ]

            for actual, expected, msg in read_assertions:
                self.assertEqual(actual, expected, f"{filename}: {msg}")

            # Verify content for text files
            if expected_encoding == "text":
                self.assertEqual(result["content"], content)
            elif expected_encoding == "base64":
                expected_base64 = base64.b64encode(content).decode("utf-8")
                self.assertEqual(result["content"], expected_base64)

    def test_file_writing_comprehensive(self):
        """Test file writing with various content types."""
        test_cases = [
            ("Hello, World!", "text.txt", "text"),
            ("Unicode: 🚀 中文", "unicode.txt", "text"),
            (base64.b64encode(b"binary data").decode("utf-8"), "binary.bin", "base64"),
        ]

        for content, filename, encoding in test_cases:
            test_file = os.path.join(self.temp_dir, filename)
            write_file(test_file, content, encoding=encoding)

            # Verify file exists and has content
            self.assertTrue(os.path.exists(test_file))

            if encoding == "text":
                with open(test_file, "r", encoding="utf-8") as f:
                    self.assertEqual(f.read(), content)
            else:
                with open(test_file, "rb") as f:
                    expected_bytes = base64.b64decode(content.encode("utf-8"))
                    self.assertEqual(f.read(), expected_bytes)

    def test_base64_encoding_operations(self):
        """Test base64 encoding and decoding operations."""
        test_data = [
            "Hello, World!",
            "Unicode: 🚀 中文 العالم",
            "",  # Empty string
            "Special chars: !@#$%^&*()",
            bytes([0, 1, 2, 3, 255, 254, 253]),  # Binary data
            bytes(range(50)),  # Byte range
        ]

        for original in test_data:
            with self.subTest(data=str(original)[:50]):
                if isinstance(original, str):
                    # String to base64 and back
                    encoded = text_to_base64(original)
                    decoded = base64_to_text(encoded)
                    self.assertEqual(decoded, original)

                    # Should match encode_to_base64 result
                    encoded_alt = encode_to_base64(original)
                    self.assertEqual(encoded, encoded_alt)
                else:
                    # Bytes to base64 and back
                    encoded = encode_to_base64(original)
                    decoded = decode_from_base64(encoded)
                    self.assertEqual(decoded, original)

    def test_file_base64_conversion(self):
        """Test file to base64 conversion and back."""
        test_cases = [
            ("text.txt", b"Plain text content"),
            ("binary.dat", bytes([0, 1, 2, 255, 254, 253])),
            ("unicode.txt", "Unicode: 🌍 中文".encode("utf-8")),
            ("empty.txt", b""),  # Empty file
        ]

        for filename, content in test_cases:
            # Create original file
            original_file = os.path.join(self.temp_dir, filename)
            with open(original_file, "wb") as f:
                f.write(content)

            # Convert to base64 and back
            base64_content = file_to_base64(original_file)
            restored_file = os.path.join(self.temp_dir, f"restored_{filename}")
            base64_to_file(base64_content, restored_file)

            # Verify content preserved
            with open(restored_file, "rb") as f:
                self.assertEqual(f.read(), content)

    def test_file_operations_error_handling(self):
        """Test file operation error scenarios."""
        # Test file not found
        with self.assert_error_behaviour(FileNotFoundError):
            read_file("/nonexistent/path.txt")

        with self.assert_error_behaviour(FileNotFoundError):
            file_to_base64("/nonexistent/path.txt")

        # Test file size limits
        large_file = os.path.join(self.temp_dir, "large.txt")
        with open(large_file, "w") as f:
            f.write("a" * (2 * 1024 * 1024))  # 2MB

        with self.assert_error_behaviour(ValueError):
            read_file(large_file, max_size_mb=1)

        # Test invalid UTF-8 decoding
        invalid_utf8_bytes = b"\xff\xfe\x00\x01"
        invalid_base64 = base64.b64encode(invalid_utf8_bytes).decode("utf-8")

        with self.assert_error_behaviour(UnicodeDecodeError):
            base64_to_text(invalid_base64)


class TestRepositoryManagement(BaseTestCase):
    """Test repository management utilities."""

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB.update(
            {
                "repositories": {},
                "next_repo_id": 1,
                "next_workflow_id": 100,
                "next_run_id": 1000,
                "next_job_id": 1,
            }
        )

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_repository_lifecycle_management(self):
        """Test complete repository lifecycle operations."""
        # Add repository
        owner_data = {
            "login": "testowner",
            "id": 1,
            "node_id": "MDQ6VXNlcjE=",
            "type": "User",
            "site_admin": False,
        }

        repo_result = add_repository(owner_data, "testrepo")

        # Verify repository structure
        repo_assertions = [
            (isinstance(repo_result, dict), True, "Repository result is dict"),
            ("id" in repo_result, True, "Repository has ID"),
            ("name" in repo_result, True, "Repository has name"),
            (repo_result["name"], "testrepo", "Repository name matches"),
        ]

        for actual, expected, msg in repo_assertions:
            self.assertEqual(actual, expected, msg)

        # Retrieve repository
        retrieved_repo = get_repository("testowner", "testrepo")
        self.assertIsNotNone(retrieved_repo)
        self.assertEqual(retrieved_repo["name"], "testrepo")

        # Case insensitive retrieval
        retrieved_case = get_repository("TESTOWNER", "testrepo")
        self.assertIsNotNone(retrieved_case)

        # Non-existent repository
        missing_repo = get_repository("nonexistent", "repo")
        self.assertIsNone(missing_repo)

    def test_workflow_management(self):
        """Test workflow management operations."""
        # Setup repository
        owner_data = {
            "login": "testowner",
            "id": 1,
            "node_id": "MDQ6VXNlcjE=",
            "type": "User",
            "site_admin": False,
        }
        add_repository(owner_data, "testrepo")

        # Add workflow
        workflow_data = {
            "name": "Test Workflow",
            "path": ".github/workflows/test.yml",
            "state": "active",
        }

        workflow_result = add_or_update_workflow("testowner", "testrepo", workflow_data)

        # Verify workflow structure
        workflow_assertions = [
            (isinstance(workflow_result, dict), True, "Workflow result is dict"),
            ("id" in workflow_result, True, "Workflow has ID"),
            ("name" in workflow_result, True, "Workflow has name"),
            (workflow_result["name"], "Test Workflow", "Workflow name matches"),
        ]

        for actual, expected, msg in workflow_assertions:
            self.assertEqual(actual, expected, msg)

        # Retrieve workflow by ID
        workflow_id = workflow_result["id"]
        retrieved_by_id = get_workflow_by_id_or_filename(
            "testowner", "testrepo", workflow_id
        )
        if retrieved_by_id is None:
            # Try with string ID if integer doesn't work
            retrieved_by_id = get_workflow_by_id_or_filename(
                "testowner", "testrepo", str(workflow_id)
            )
        self.assertIsNotNone(
            retrieved_by_id, f"Could not retrieve workflow with ID {workflow_id}"
        )
        self.assertEqual(retrieved_by_id["id"], workflow_id)

        # Retrieve workflow by filename
        retrieved_by_filename = get_workflow_by_id_or_filename(
            "testowner", "testrepo", ".github/workflows/test.yml"
        )
        self.assertIsNotNone(retrieved_by_filename)
        self.assertEqual(retrieved_by_filename["path"], ".github/workflows/test.yml")

    def test_workflow_run_management(self):
        """Test workflow run management operations."""
        # Setup repository and workflow
        owner_data = {
            "login": "testowner",
            "id": 1,
            "node_id": "MDQ6VXNlcjE=",
            "type": "User",
            "site_admin": False,
        }
        add_repository(owner_data, "testrepo")

        workflow_data = {
            "name": "Test Workflow",
            "path": ".github/workflows/test.yml",
            "state": "active",
        }
        workflow = add_or_update_workflow("testowner", "testrepo", workflow_data)

        # Add workflow run
        run_data = {
            "workflow_id": workflow["id"],
            "head_branch": "main",
            "head_sha": generate_random_sha(),
            "status": "queued",
            "event": "push",
            "inputs": {"debug": "true"},
        }

        run_result = add_workflow_run("testowner", "testrepo", run_data)

        # Verify run structure
        run_assertions = [
            (isinstance(run_result, dict), True, "Run result is dict"),
            ("id" in run_result, True, "Run has ID"),
            ("workflow_id" in run_result, True, "Run has workflow_id"),
            (run_result["workflow_id"], workflow["id"], "Run workflow_id matches"),
            (run_result["status"], "queued", "Run status matches"),
        ]

        for actual, expected, msg in run_assertions:
            self.assertEqual(actual, expected, msg)

        # Retrieve workflow run
        run_id = run_result["id"]
        retrieved_run = get_workflow_run_by_id("testowner", "testrepo", run_id)
        self.assertIsNotNone(retrieved_run)
        self.assertEqual(retrieved_run["id"], run_id)


class TestDataValidationUtilities(BaseTestCase):
    """Test data validation and normalization utilities."""

    def test_datetime_normalization(self):
        """Test datetime normalization utility."""
        test_cases = [
            # UTC datetime
            (datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc), True),
            # Naive datetime (should get UTC timezone)
            (datetime(2023, 1, 1, 12, 0, 0), True),
            # ISO string formats
            ("2023-01-01T12:00:00Z", True),
            ("2023-01-01T12:00:00+00:00", True),
            ("2023-01-01T12:00:00.000Z", True),
            # Invalid cases
            (None, False),
            ("invalid-date", False),
            (123, False),
        ]

        for input_dt, should_succeed in test_cases:
            with self.subTest(input=str(input_dt)):
                result = _ensure_utc_datetime(input_dt)

                if should_succeed:
                    self.assertIsInstance(result, datetime)
                    self.assertEqual(result.tzinfo, timezone.utc)
                else:
                    self.assertIsNone(result)

    def test_date_filter_parsing(self):
        """Test date filter parsing utility."""
        # Valid single date
        result_single = _parse_created_filter("2023-01-15")
        self.assertIn("start_date", result_single)
        self.assertIn("end_date", result_single)

        # Valid date range
        result_range = _parse_created_filter("2023-01-01..2023-01-31")
        self.assertIn("start_date", result_range)
        self.assertIn("end_date", result_range)

        # Comparison operators
        result_gte = _parse_created_filter(">=2023-01-15")
        self.assertIn("start_date", result_gte)

        result_lte = _parse_created_filter("<=2023-01-15")
        self.assertIn("end_date", result_lte)

        # None/empty cases
        result_none = _parse_created_filter(None)
        self.assertIsNone(result_none)

        result_empty = _parse_created_filter("")
        self.assertIsNone(result_empty)

        # Invalid formats should raise InvalidInputError
        invalid_filters = [
            "invalid-date",
            "2023-01-01..invalid",
            ">>2023-01-01",
            "2023-01-01..2023-01-02..2023-01-03",
        ]

        for invalid_filter in invalid_filters:
            with self.subTest(filter=invalid_filter):
                with self.assert_error_behaviour(InvalidInputError):
                    _parse_created_filter(invalid_filter)

    def test_input_validation_patterns(self):
        """Test common input validation patterns."""

        # String parameter validation
        def validate_string_param(param, param_name):
            if param is None:
                raise InvalidInputError(f"{param_name} cannot be None")
            if not isinstance(param, str):
                raise InvalidInputError(f"{param_name} must be a string")
            if not param.strip():
                raise InvalidInputError(f"{param_name} must be non-empty")
            return param.strip()

        # Valid strings
        valid_inputs = ["test", "valid-string", "user123", "  spaced  "]
        for input_val in valid_inputs:
            result = validate_string_param(input_val, "test_param")
            self.assertEqual(result, input_val.strip())

        # Invalid inputs
        invalid_inputs = [None, 123, [], "", "   ", "\t\n"]
        for input_val in invalid_inputs:
            with self.subTest(input=input_val):
                with self.assert_error_behaviour(InvalidInputError):
                    validate_string_param(input_val, "test_param")

    def test_error_message_consistency(self):
        """Test error message patterns for consistency."""
        # NotFoundError patterns
        error_tests = [
            (
                NotFoundError("Repository 'owner/repo' not found"),
                "Repository",
                "not found",
            ),
            (
                InvalidInputError("Owner must be a non-empty string"),
                "Owner",
                "non-empty",
            ),
            (WorkflowDisabledError("Workflow is disabled"), "disabled", "workflow"),
            (ConflictError("Already exists"), "already", "exists"),
        ]

        for error, keyword1, keyword2 in error_tests:
            error_str = str(error).lower()
            self.assertIn(keyword1.lower(), error_str)
            self.assertIn(keyword2.lower(), error_str)


class TestUtilityIntegration(BaseTestCase):
    """Test integration between different utility functions."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB.update(
            {
                "repositories": {},
                "next_repo_id": 1,
                "next_workflow_id": 100,
                "next_run_id": 1000,
            }
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)
        DB.clear()
        DB.update(self._original_DB_state)

    def test_complete_workflow_with_file_operations(self):
        """Test complete workflow using multiple utility functions together."""
        # Create repository
        owner_data = {
            "login": "testowner",
            "id": 1,
            "node_id": "MDQ6VXNlcjE=",
            "type": "User",
            "site_admin": False,
        }
        repo = add_repository(owner_data, "test-integration")

        # Create workflow file content
        workflow_content = """
name: Test Integration Workflow
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run tests
        run: echo "Testing integration"
"""

        # Write workflow file
        workflow_file = os.path.join(self.temp_dir, "workflow.yml")
        write_file(workflow_file, workflow_content, encoding="text")

        # Verify file operations
        self.assertTrue(is_text_file(workflow_file))
        # MIME type might vary based on system configuration
        mime_type = get_mime_type(workflow_file)
        self.assertIn(
            mime_type,
            [
                "text/x-yaml",
                "text/yaml",
                "application/x-yaml",
                "application/yaml",
                "application/octet-stream",
            ],
        )

        # Read file back and verify
        file_data = read_file(workflow_file)
        self.assertEqual(file_data["encoding"], "text")
        self.assertEqual(file_data["content"], workflow_content)

        # Convert to base64 and back
        base64_content = file_to_base64(workflow_file)
        restored_file = os.path.join(self.temp_dir, "restored_workflow.yml")
        base64_to_file(base64_content, restored_file)

        # Verify restoration
        restored_data = read_file(restored_file)
        self.assertEqual(restored_data["content"], workflow_content)

        # Add workflow to repository
        workflow_data = {
            "name": "Test Integration Workflow",
            "path": ".github/workflows/integration.yml",
            "state": "active",
        }
        workflow = add_or_update_workflow(
            "testowner", "test-integration", workflow_data
        )

        # Create workflow run with generated SHA
        run_sha = generate_random_sha()
        self.assertTrue(is_valid_sha(run_sha))

        run_data = {
            "workflow_id": workflow["id"],
            "head_branch": "main",
            "head_sha": run_sha,
            "status": "completed",
            "event": "push",
        }

        run = add_workflow_run("testowner", "test-integration", run_data)

        # Verify complete integration
        integration_assertions = [
            (repo["name"], "test-integration", "Repository name"),
            (workflow["name"], "Test Integration Workflow", "Workflow name"),
            (run["head_sha"], run_sha, "Run SHA"),
            (is_valid_sha(run["head_sha"]), True, "Run SHA validity"),
            (os.path.exists(workflow_file), True, "Workflow file exists"),
            (os.path.exists(restored_file), True, "Restored file exists"),
        ]

        for actual, expected, msg in integration_assertions:
            self.assertEqual(actual, expected, msg)


if __name__ == "__main__":
    unittest.main()
