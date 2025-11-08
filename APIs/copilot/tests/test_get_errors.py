import copy

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import custom_errors
from .. import get_errors
from ..SimulationEngine.db import DB


class TestGetErrors(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.workspace_root = "/test_workspace"
        DB['workspace_root'] = self.workspace_root
        DB['cwd'] = self.workspace_root  # Default CWD to workspace root
        DB['file_system'] = {}

        # Sample error templates to be used in tests
        # The 'file_path' field will be populated dynamically in tests
        self.error_template_syntax = {
            "line_number": 10,
            "column_number": 5,
            "message": "Syntax Error: unexpected indent",
            "severity": "error",
            "code": "E001",
            "source": "compiler"
        }
        self.error_template_lint_warning = {
            "line_number": 20,
            # column_number is optional
            "message": "Unused variable 'x'",
            "severity": "warning",
            "code": "W002",
            "source": "linter:pylint"
        }
        self.error_template_info_minimal = {
            "line_number": 30,
            "column_number": 1,
            "message": "Type hint missing",
            "severity": "info",
            # code is optional
            # source is optional
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _add_file_to_db(self, relative_path: str, content: str = "Default file content.", diagnostics_data=None):
        # Normalize relative_path to not start with '/' for consistent joining
        _relative_path = relative_path.lstrip('/')

        # Construct absolute path using forward slashes
        abs_path = f"{self.workspace_root}/{_relative_path}"
        # Handle potential double slashes if workspace_root is "/" and _relative_path is empty (e.g. root file)
        # or if _relative_path itself was just "/"
        if self.workspace_root == "/" and not _relative_path:  # File is the root itself
            abs_path = "/"
        else:  # General case, clean up double slashes
            abs_path = abs_path.replace('//', '/')

        # Ensure parent directories exist in DB
        parts = _relative_path.split('/')
        current_dir_path_check = self.workspace_root
        if len(parts) > 1:  # If path has directory components e.g., "dir/file.py"
            for dir_part in parts[:-1]:  # Iterate over directory parts only
                if not dir_part: continue  # Skip empty parts from multiple slashes if any
                current_dir_path_check = f"{current_dir_path_check}/{dir_part}".replace('//', '/')
                if current_dir_path_check not in DB['file_system']:
                    DB['file_system'][current_dir_path_check] = {
                        'path': current_dir_path_check,
                        'is_directory': True,
                        'content_lines': [], 'size_bytes': 0,
                        'last_modified': '2023-01-01T12:00:00Z'
                    }

        file_entry = {
            'path': abs_path,
            'is_directory': False,
            'content_lines': content.splitlines(keepends=True),
            'size_bytes': len(content.encode('utf-8')),
            'last_modified': '2023-01-01T12:00:00Z'
        }
        if diagnostics_data is not None:
            file_entry['simulated_diagnostics'] = diagnostics_data

        DB['file_system'][abs_path] = file_entry
        return abs_path

    def _add_dir_to_db(self, relative_path: str):
        _relative_path = relative_path.lstrip('/')
        abs_path = f"{self.workspace_root}/{_relative_path}".replace('//', '/')
        if self.workspace_root == "/" and not _relative_path:  # Dir is the root itself
            abs_path = "/"

        parts = _relative_path.split('/')
        current_dir_path_build = self.workspace_root
        for dir_part in parts:
            if not dir_part: continue
            current_dir_path_build = f"{current_dir_path_build}/{dir_part}".replace('//', '/')
            if current_dir_path_build not in DB['file_system'] or not DB['file_system'][current_dir_path_build][
                'is_directory']:
                DB['file_system'][current_dir_path_build] = {
                    'path': current_dir_path_build,
                    'is_directory': True,
                    'content_lines': [], 'size_bytes': 0,
                    'last_modified': '2023-01-01T12:00:00Z'
                }
        return abs_path

    def test_get_errors_success_with_multiple_error_types(self):
        file_rel_path = "project/module.py"
        abs_path = self._add_file_to_db(file_rel_path)

        expected_diagnostics = [
            {**self.error_template_syntax, "file_path": abs_path},
            {**self.error_template_lint_warning, "file_path": abs_path},
            {**self.error_template_info_minimal, "file_path": abs_path}
        ]
        # Ensure deep copy for DB state modification
        DB['file_system'][abs_path]['simulated_diagnostics'] = copy.deepcopy(expected_diagnostics)

        result = get_errors(file_path=file_rel_path)
        self.assertEqual(result, expected_diagnostics)

    def test_get_errors_success_no_errors_file_has_no_diagnostics_key(self):
        file_rel_path = "clean_code.js"
        self._add_file_to_db(file_rel_path)  # No 'simulated_diagnostics' key added

        result = get_errors(file_path=file_rel_path)
        # For a file with no simulated_diagnostics, it should fall back to mock generation.
        # If the file content is "Default file content.", mock js errors might be generated.
        # Let's assume default content doesn't trigger mock JS errors relevant to this test.
        # If it does, the test would need to adapt or use content that doesn't trigger errors.
        # Given the current mock JS errors, "Default file content." should result in no errors.
        self.assertEqual(result, [])

    def test_get_errors_success_no_errors_diagnostics_list_is_empty(self):
        file_rel_path = "perfect_file.ts"
        self._add_file_to_db(file_rel_path, diagnostics_data=[])

        result = get_errors(file_path=file_rel_path)
        self.assertEqual(result, [])

    def test_get_errors_success_relative_path_from_subdir_cwd(self):
        self._add_dir_to_db("src/app")
        DB['cwd'] = f"{self.workspace_root}/src/app"  # Set CWD to a subdirectory

        file_rel_to_cwd = "component.jsx" # .jsx is not a handled mock type, so it should return [] if no simulated_diagnostics
        # Full relative path from workspace root for adding to DB
        full_rel_path_for_db = f"src/app/{file_rel_to_cwd}"
        abs_path = self._add_file_to_db(full_rel_path_for_db)

        expected_diagnostic = {**self.error_template_syntax, "file_path": abs_path}
        DB['file_system'][abs_path]['simulated_diagnostics'] = [copy.deepcopy(expected_diagnostic)]

        # Call get_errors with path relative to current CWD
        result = get_errors(file_path=file_rel_to_cwd)
        self.assertEqual(result, [expected_diagnostic])

    def test_get_errors_success_absolute_path_input_within_workspace(self):
        file_rel_path = "config/settings.json"
        abs_path = self._add_file_to_db(file_rel_path)

        expected_diagnostic = {**self.error_template_info_minimal, "file_path": abs_path}
        DB['file_system'][abs_path]['simulated_diagnostics'] = [copy.deepcopy(expected_diagnostic)]

        # Call get_errors with the absolute path
        result = get_errors(file_path=abs_path)
        self.assertEqual(result, [expected_diagnostic])

    def test_get_errors_success_path_with_dot_dot_navigation(self):
        self._add_dir_to_db("outer/inner")
        DB['cwd'] = f"{self.workspace_root}/outer/inner"  # CWD is /test_workspace/outer/inner

        file_in_outer_rel = "sibling_file.txt"
        # Full relative path from workspace root for adding to DB
        abs_path = self._add_file_to_db(f"outer/{file_in_outer_rel}")

        expected_diagnostic = {**self.error_template_lint_warning, "file_path": abs_path}
        DB['file_system'][abs_path]['simulated_diagnostics'] = [copy.deepcopy(expected_diagnostic)]

        # Path from CWD to sibling_file.txt is "../sibling_file.txt"
        result = get_errors(file_path=f"../{file_in_outer_rel}")
        self.assertEqual(result, [expected_diagnostic])

    def test_get_errors_all_optional_fields_combinations(self):
        file_rel_path = "test_optional_fields.py"
        abs_path = self._add_file_to_db(file_rel_path)

        error_all_fields = {
            "file_path": abs_path, "line_number": 1, "column_number": 1,
            "message": "Error with all fields", "severity": "error",
            "code": "C001", "source": "SourceEngine1"
        }
        error_no_optional_fields = {  # column_number, code, source are optional
            "file_path": abs_path, "line_number": 2,
            "message": "Error with minimal fields", "severity": "warning"
        }
        error_some_optional_fields = {
            "file_path": abs_path, "line_number": 3, "column_number": None,  # Explicit None
            "message": "Error with some optional fields", "severity": "info",
            "code": "C003", "source": None  # Explicit None
        }

        diagnostics = [
            copy.deepcopy(error_all_fields),
            copy.deepcopy(error_no_optional_fields),
            copy.deepcopy(error_some_optional_fields)
        ]
        DB['file_system'][abs_path]['simulated_diagnostics'] = diagnostics

        result = get_errors(file_path=file_rel_path)
        self.assertEqual(len(result), 3)
        self.assertDictEqual(result[0], error_all_fields)

        # For error_no_optional_fields, ensure missing keys are not present or are None if Pydantic model defaults to None
        # Based on CodeError model, they are Optional, so they could be absent or None.
        # Assuming if not in simulated_diagnostics, they are not in output dict.
        # If they are None in simulated_diagnostics, they should be None in output.
        # The test data `error_no_optional_fields` has them absent.
        # The test data `error_some_optional_fields` has them as None.
        self.assertDictEqual(result[1], error_no_optional_fields)
        self.assertDictEqual(result[2], error_some_optional_fields)

    def test_get_errors_file_not_found_non_existent_path(self):
        self.assert_error_behavior(
            func_to_call=get_errors,
            expected_exception_type=custom_errors.FileNotFoundError,
            # Updated message to match the function's output
            expected_message=f"File not found: {self.workspace_root}/ghost_file.py",
            file_path="ghost_file.py"
        )

    def test_get_errors_file_not_found_path_is_directory(self):
        dir_rel_path = "src_folder"
        abs_dir_path = self._add_dir_to_db(dir_rel_path)

        self.assert_error_behavior(
            func_to_call=get_errors,
            # Changed expected exception type from FileNotFoundError to AnalysisFailedError
            expected_exception_type=custom_errors.AnalysisFailedError,
            expected_message=f"Path is a directory, not a file: {abs_dir_path}",
            file_path=dir_rel_path
        )

    def test_get_errors_raises_tool_configuration_error(self):
        file_rel_path = "needs_special_linter.cpp"
        # The content "TOOL_CONFIG_ERROR" is now explicitly checked in get_errors
        abs_path = self._add_file_to_db(file_rel_path, diagnostics_data="TOOL_CONFIG_ERROR")

        self.assert_error_behavior(
            func_to_call=get_errors,
            expected_exception_type=custom_errors.ToolConfigurationError,
            # Expected message matches the explicit handling in get_errors
            expected_message=f"Tool configuration error for file: {abs_path}",
            file_path=file_rel_path
        )

    def test_get_errors_raises_analysis_failed_error(self):
        file_rel_path = "complex_analysis_timeout.java"
        # The content "ANALYSIS_FAILED_ERROR" is now explicitly checked in get_errors
        abs_path = self._add_file_to_db(file_rel_path, diagnostics_data="ANALYSIS_FAILED_ERROR")

        self.assert_error_behavior(
            func_to_call=get_errors,
            expected_exception_type=custom_errors.AnalysisFailedError,
            # Expected message matches the explicit handling in get_errors
            expected_message=f"Analysis failed for file: {abs_path}",
            file_path=file_rel_path
        )

    def test_get_errors_validation_error_for_integer_path(self):
        self.assert_error_behavior(
            func_to_call=get_errors,
            expected_exception_type=custom_errors.ValidationError,
            # Message now matches the explicit type check
            expected_message="File path must be a string.",
            file_path=12345
        )

    def test_get_errors_validation_error_for_none_path(self):
        self.assert_error_behavior(
            func_to_call=get_errors,
            expected_exception_type=custom_errors.ValidationError,
            # Message now matches the explicit type check
            expected_message="File path must be a string.",
            file_path=None
        )

    def test_get_errors_validation_error_for_empty_string_path(self):
        self.assert_error_behavior(
            func_to_call=get_errors,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="File path cannot be empty.",
            file_path=""
        )

    def test_get_errors_file_not_found_for_absolute_path_outside_workspace(self):
        # This path is absolute but not under self.workspace_root ("/test_workspace")
        path_outside_workspace = "/another_root/some_file.py"
        self.assert_error_behavior(
            func_to_call=get_errors,
            expected_exception_type=custom_errors.FileNotFoundError,
            # Updated message to match the function's output, including the 'Detail' part
            expected_message=f"File path is invalid or outside the workspace: {path_outside_workspace}. Detail: Absolute path '{path_outside_workspace}' is outside the configured workspace root '{self.workspace_root}'.",
            file_path=path_outside_workspace
        )

    def test_get_errors_normalizes_path_with_double_slashes(self):
        file_rel_path_messy = "dir1//dir2///file.py"
        file_rel_path_clean = "dir1/dir2/file.py"
        abs_path_clean = self._add_file_to_db(file_rel_path_clean)

        expected_diagnostic = {**self.error_template_syntax, "file_path": abs_path_clean}
        DB['file_system'][abs_path_clean]['simulated_diagnostics'] = [copy.deepcopy(expected_diagnostic)]

        result = get_errors(file_path=file_rel_path_messy)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['file_path'], abs_path_clean)  # Check if returned error has normalized path
        self.assertEqual(result, [expected_diagnostic]) # Ensure the content also matches

    def test_get_errors_normalizes_path_with_trailing_slash(self):
        # A file path ending with a slash. os.path.normpath should remove it.
        file_rel_path_with_slash = "my_document.txt/"
        file_rel_path_clean = "my_document.txt"
        abs_path_clean = self._add_file_to_db(file_rel_path_clean)

        expected_diagnostic = {**self.error_template_lint_warning, "file_path": abs_path_clean}
        DB['file_system'][abs_path_clean]['simulated_diagnostics'] = [copy.deepcopy(expected_diagnostic)]

        result = get_errors(file_path=file_rel_path_with_slash)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['file_path'], abs_path_clean)
        self.assertEqual(result, [expected_diagnostic]) # Ensure the content also matches

    def test_get_errors_for_file_at_workspace_root_accessed_by_dot(self):
        # Test accessing workspace_root itself if it's marked as a file.
        # This is an edge case.
        root_file_content = ["root content"]
        root_file_path = self.workspace_root # The root path itself
        DB['file_system'][root_file_path] = {
            'path': root_file_path,
            'is_directory': False,  # Mark workspace_root as a file for this test
            'content_lines': root_file_content, 'size_bytes': len("".join(root_file_content).encode('utf-8')),
            'last_modified': '2023-01-01T12:00:00Z',
        }
        # Explicitly set simulated_diagnostics for the root file
        expected_diagnostic_for_root = {**self.error_template_info_minimal, "file_path": root_file_path}
        DB['file_system'][root_file_path]['simulated_diagnostics'] = [copy.deepcopy(expected_diagnostic_for_root)]

        DB['cwd'] = self.workspace_root  # CWD is the workspace root

        # `.` from CWD should resolve to self.workspace_root
        result = get_errors(file_path=".")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['file_path'], root_file_path)
        self.assertEqual(result, [expected_diagnostic_for_root])

        # Also test by passing the absolute path to the workspace root
        result_abs = get_errors(file_path=root_file_path)
        self.assertEqual(len(result_abs), 1)
        self.assertEqual(result_abs[0]['file_path'], root_file_path)
        self.assertEqual(result_abs, [expected_diagnostic_for_root])

    def test_get_errors_typescript_explicit_any_coverage(self):
        file_rel_path = "src/example.ts"
        content = "let myVar: any = 10; // Explicit any"
        abs_path = self._add_file_to_db(file_rel_path, content=content)

        expected_errors = [
            {
                "file_path": abs_path,
                "line_number": 1,
                "column_number": content.find(": any") + 1,
                "message": "Type 'any' is not recommended. Add a more specific type.",
                "severity": "warning",
                "code": "typescript-eslint(@typescript-eslint/no-explicit-any)",
                "source": "linter:mock-eslint-typescript"
            }
        ]
        result = get_errors(file_path=file_rel_path)
        self.assertEqual(result, expected_errors)

    def test_get_errors_json_valid_coverage(self):
        file_rel_path = "config/settings.json"
        content = '{\n  "version": 1,\n  "enabled": true\n}'
        self._add_file_to_db(file_rel_path, content=content)

        result = get_errors(file_path=file_rel_path)
        self.assertEqual(result, [])

    def test_get_errors_unhandled_lintable_extension_raises_error_coverage(self):
        file_rel_path = "MyClass.java"
        content = "public class MyClass { /* some code */ }"
        abs_path = self._add_file_to_db(file_rel_path, content=content)

        self.assert_error_behavior(
            func_to_call=get_errors,
            expected_exception_type=custom_errors.ToolConfigurationError,
            expected_message=f"No linter or compiler is configured in this environment for file type '.java'.",
            file_path=file_rel_path
        )
