import copy

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from .. import get_project_setup_info

class TestGetProjectSetupInfoWorkspaceChecks(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_workspace_not_initialized_error(self):
        # DB['workspace_root'] is not set by setUp here
        self.assert_error_behavior(
            func_to_call=get_project_setup_info,
            project_type="python_datascience",
            language="python",
            expected_exception_type=custom_errors.WorkspaceNotInitializedError,
            expected_message="Workspace is not initialized. Please create or load a workspace first."
        )


class TestGetProjectSetupInfoMainLogic(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB['workspace_root'] = "/mock_workspace"  # Workspace is initialized

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _validate_recommended_extension(self, ext_item: dict):
        self.assertIsInstance(ext_item, dict)
        self.assertIn("id", ext_item)
        self.assertIsInstance(ext_item["id"], str)
        self.assertTrue(ext_item["id"], "Extension 'id' must be a non-empty string.")
        self.assertIn("name", ext_item)
        self.assertIsInstance(ext_item["name"], str)
        self.assertTrue(ext_item["name"], "Extension 'name' must be a non-empty string.")
        self.assertIn("reason", ext_item)
        self.assertIsInstance(ext_item["reason"], str)
        # 'reason' can be an empty string if desired.

    def _validate_key_configuration_file(self, conf_file_item: dict):
        self.assertIsInstance(conf_file_item, dict)
        self.assertIn("file_name_pattern", conf_file_item)
        self.assertIsInstance(conf_file_item["file_name_pattern"], str)
        self.assertTrue(conf_file_item["file_name_pattern"],
                        "Key configuration file 'file_name_pattern' must be a non-empty string.")
        self.assertIn("purpose", conf_file_item)
        self.assertIsInstance(conf_file_item["purpose"], str)
        self.assertTrue(conf_file_item["purpose"], "Key configuration file 'purpose' must be a non-empty string.")
        self.assertIn("example_content_snippet", conf_file_item)  # Key must be present
        if conf_file_item["example_content_snippet"] is not None:
            self.assertIsInstance(conf_file_item["example_content_snippet"], str)

    def _validate_common_task(self, task_item: dict):
        self.assertIsInstance(task_item, dict)
        self.assertIn("name", task_item)
        self.assertIsInstance(task_item["name"], str)
        self.assertTrue(task_item["name"], "Common task 'name' must be a non-empty string.")
        self.assertIn("command_suggestion", task_item)
        self.assertIsInstance(task_item["command_suggestion"], str)
        self.assertTrue(task_item["command_suggestion"], "Common task 'command_suggestion' must be a non-empty string.")

    def test_successful_retrieval_all_fields_present(self):
        # Assuming "python_datascience", "python" is a valid combination
        # that returns data for all fields, including optional ones populated.
        result = get_project_setup_info(project_type="python_datascience", language="python")

        self.assertIsInstance(result, dict, "Return value must be a dictionary.")
        self.assertEqual(result.get("project_type"), "python_datascience")
        self.assertEqual(result.get("language"), "python")

        # Recommended Extensions (Mandatory list, can be empty)
        self.assertIn("recommended_extensions", result)
        recommended_extensions = result["recommended_extensions"]
        self.assertIsInstance(recommended_extensions, list)
        for ext_item in recommended_extensions:
            self._validate_recommended_extension(ext_item)

        # Key Configuration Files (Mandatory list, can be empty)
        self.assertIn("key_configuration_files", result)
        key_config_files = result["key_configuration_files"]
        self.assertIsInstance(key_config_files, list)
        for conf_file_item in key_config_files:
            self._validate_key_configuration_file(conf_file_item)

        # Common Tasks (Optional: can be None or List)
        self.assertIn("common_tasks", result)  # Key must be present
        common_tasks = result["common_tasks"]
        if common_tasks is not None:
            self.assertIsInstance(common_tasks, list)
            for task_item in common_tasks:
                self._validate_common_task(task_item)

        # Debugging Tips (Optional: can be None or List)
        self.assertIn("debugging_tips", result)  # Key must be present
        debugging_tips = result["debugging_tips"]
        if debugging_tips is not None:
            self.assertIsInstance(debugging_tips, list)
            for tip_item in debugging_tips:
                self.assertIsInstance(tip_item, str)
                self.assertTrue(tip_item, "Debugging tip string must not be empty if present in the list.")

    def test_successful_retrieval_optional_fields_none_or_empty(self):
        # Assuming "typescript_server", "typescript" is a valid combination
        # that might return None or empty lists for optional fields.
        result = get_project_setup_info(project_type="typescript_server", language="typescript")

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("project_type"), "typescript_server")
        self.assertEqual(result.get("language"), "typescript")

        self.assertIn("recommended_extensions", result)
        self.assertIsInstance(result["recommended_extensions"], list)
        for ext_item in result["recommended_extensions"]:
            self._validate_recommended_extension(ext_item)

        self.assertIn("key_configuration_files", result)
        self.assertIsInstance(result["key_configuration_files"], list)
        for conf_file_item in result["key_configuration_files"]:
            self._validate_key_configuration_file(conf_file_item)

        self.assertIn("common_tasks", result)
        if result["common_tasks"] is not None:
            self.assertIsInstance(result["common_tasks"], list)
            for task_item in result["common_tasks"]:
                self._validate_common_task(task_item)

        self.assertIn("debugging_tips", result)
        if result["debugging_tips"] is not None:
            self.assertIsInstance(result["debugging_tips"], list)
            for tip_item in result["debugging_tips"]:
                self.assertIsInstance(tip_item, str)

    def test_project_type_or_language_not_found_error_unknown_type(self):
        self.assert_error_behavior(
            func_to_call=get_project_setup_info,
            project_type="unknown_project_type_xyz",
            language="python",
            expected_exception_type=custom_errors.ProjectTypeOrLanguageNotFoundError,
            expected_message="Setup information for project type 'unknown_project_type_xyz' and language 'python' is not available."
        )

    def test_project_type_or_language_not_found_error_unknown_language(self):
        self.assert_error_behavior(
            func_to_call=get_project_setup_info,
            project_type="python_datascience",  # Assuming this type is generally known
            language="unknown_language_abc",
            expected_exception_type=custom_errors.ProjectTypeOrLanguageNotFoundError,
            expected_message="Setup information for project type 'python_datascience' and language 'unknown_language_abc' is not available."
        )

    def test_validation_error_project_type_empty(self):
        self.assert_error_behavior(
            func_to_call=get_project_setup_info,
            project_type="",
            language="python",
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: 'project_type' must be a non-empty string."
        )

    def test_validation_error_language_empty(self):
        self.assert_error_behavior(
            func_to_call=get_project_setup_info,
            project_type="python_datascience",
            language="",
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: 'language' must be a non-empty string."
        )

    def test_validation_error_project_type_not_string(self):
        self.assert_error_behavior(
            func_to_call=get_project_setup_info,
            project_type=12345,  # Not a string
            language="python",
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: 'project_type' must be a string."
        )

    def test_validation_error_language_not_string(self):
        self.assert_error_behavior(
            func_to_call=get_project_setup_info,
            project_type="python_datascience",
            language=67890,  # Not a string
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input validation failed: 'language' must be a string."
        )
