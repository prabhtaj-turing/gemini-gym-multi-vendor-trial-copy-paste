import copy

from copilot.SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler
from copilot.SimulationEngine.db import DB

from .. import install_extension

class TestInstallExtension(BaseTestCaseWithErrorHandler):
    """
    Test suite for the install_extension function.
    """

    def setUp(self):
        """
        Set up a clean DB state for each test.
        """
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        # Default DB setup for most tests
        DB['vscode_context'] = {'is_new_workspace_creation': True}
        DB['vscode_extensions_marketplace'] = [
            {'id': 'ms-python.python', 'name': 'Python Extension'},
            {'id': 'dbaeumer.vscode-eslint', 'name': 'ESLint'},
            {'id': 'already.installed', 'name': 'Already Installed Extension'},
            {'id': 'will-fail.install', 'name': 'Failing Extension'},
            {'id': 'generic.extension', 'name': 'Generic Extension'},
        ]
        DB['installed_vscode_extensions'] = ['already.installed']
        # This key simulates the outcome of an installation attempt.
        DB['extensions_simulated_install_behavior'] = {
            'ms-python.python': 'success',
            'dbaeumer.vscode-eslint': 'success',
            'already.installed': 'success',
            'will-fail.install': 'fail',
            'generic.extension': 'success',
        }

    def tearDown(self):
        """
        Restore the original DB state after each test.
        """
        DB.clear()
        DB.update(self._original_DB_state)

    # --- Test Cases for ValidationError ---
    def test_validation_error_extension_id_none(self):
        self.assert_error_behavior(
            func_to_call=install_extension,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Extension ID must be a non-empty string.",  # Substring match
            extension_id=None
        )

    def test_validation_error_extension_id_empty(self):
        self.assert_error_behavior(
            func_to_call=install_extension,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Extension ID must be a non-empty string.",  # Substring match
            extension_id=""
        )

    def test_validation_error_extension_id_not_string(self):
        self.assert_error_behavior(
            func_to_call=install_extension,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Extension ID must be a non-empty string.",  # Substring match
            extension_id=12345
        )

    # --- Test Cases for UsageContextError ---
    def test_usage_context_error_not_new_workspace_creation(self):
        DB['vscode_context']['is_new_workspace_creation'] = False
        self.assert_error_behavior(
            func_to_call=install_extension,
            expected_exception_type=custom_errors.UsageContextError,
            expected_message="Extension installation is only allowed during a new workspace creation process.",
            extension_id="ms-python.python"
        )

    def test_usage_context_error_missing_context_key(self):
        del DB['vscode_context']['is_new_workspace_creation']
        self.assert_error_behavior(
            func_to_call=install_extension,
            expected_exception_type=custom_errors.UsageContextError,
            expected_message="Extension installation is only allowed during a new workspace creation process.",
            extension_id="ms-python.python"
        )

    def test_usage_context_error_missing_vscode_context_object(self):
        DB['vscode_context'] = {}
        self.assert_error_behavior(
            func_to_call=install_extension,
            expected_exception_type=custom_errors.UsageContextError,
            expected_message="Extension installation is only allowed during a new workspace creation process.",
            extension_id="ms-python.python"
        )

    # --- Test Cases for ExtensionNotFoundError ---
    def test_extension_not_found_error_id_not_in_marketplace(self):
        self.assert_error_behavior(
            func_to_call=install_extension,
            expected_exception_type=custom_errors.ExtensionNotFoundError,
            expected_message="Extension 'non.existent_id' not found in the marketplace.",
            extension_id="non.existent_id"
        )

    def test_extension_not_found_error_empty_marketplace(self):
        DB['vscode_extensions_marketplace'] = []
        DB['extensions_simulated_install_behavior'] = {}
        self.assert_error_behavior(
            func_to_call=install_extension,
            expected_exception_type=custom_errors.ExtensionNotFoundError,
            expected_message="Extension 'ms-python.python' not found in the marketplace.",
            extension_id="ms-python.python"
        )

    def test_extension_not_found_error_marketplace_not_defined(self):
        del DB['vscode_extensions_marketplace']
        DB['extensions_simulated_install_behavior'] = {}
        self.assert_error_behavior(
            func_to_call=install_extension,
            expected_exception_type=custom_errors.ExtensionNotFoundError,
            expected_message="Extension 'ms-python.python' not found in the marketplace.",
            extension_id="ms-python.python"
        )

    # --- Test Cases for InstallationFailedError ---
    def test_installation_failed_error_simulated_failure(self):
        extension_id_to_fail = "will-fail.install"
        self.assertTrue(any(ext['id'] == extension_id_to_fail for ext in DB['vscode_extensions_marketplace']))
        DB['installed_vscode_extensions'] = [e for e in DB['installed_vscode_extensions'] if
                                             e != extension_id_to_fail]

        self.assert_error_behavior(
            func_to_call=install_extension,
            expected_exception_type=custom_errors.InstallationFailedError,
            expected_message=f"Simulated system error prevented installation of '{extension_id_to_fail}'. This could be due to issues like VS Code CLI unavailability or permission problems.",
            extension_id=extension_id_to_fail
        )

    def test_installation_failed_error_missing_simulation_config_for_installable_extension(self):
        extension_id_missing_config = "generic.extension"
        del DB['extensions_simulated_install_behavior'][extension_id_missing_config]
        DB['installed_vscode_extensions'] = [e for e in DB['installed_vscode_extensions'] if
                                             e != extension_id_missing_config]

        self.assert_error_behavior(
            func_to_call=install_extension,
            expected_exception_type=custom_errors.InstallationFailedError,
            expected_message=f"Simulated system error prevented installation of '{extension_id_missing_config}'. This could be due to issues like VS Code CLI unavailability or permission problems.",
            extension_id=extension_id_missing_config
        )

    # --- Test Cases for Successful Operations ---
    def test_success_new_installation(self):
        extension_id = "ms-python.python"
        DB['installed_vscode_extensions'] = [e for e in DB['installed_vscode_extensions'] if e != extension_id]
        initial_installed_count = len(DB['installed_vscode_extensions'])

        result = install_extension(extension_id=extension_id)

        expected_return = {
            "extension_id": extension_id,
            "status": "success",
            "message": f"Extension '{extension_id}' installed successfully."
        }
        self.assertEqual(result, expected_return)

        self.assertEqual(len(DB['installed_vscode_extensions']), initial_installed_count + 1)
        self.assertIn(extension_id, DB['installed_vscode_extensions'])

    def test_success_already_installed(self):
        extension_id = "already.installed"
        self.assertIn(extension_id, DB['installed_vscode_extensions'])
        initial_installed_count = len(DB['installed_vscode_extensions'])
        result = install_extension(extension_id=extension_id)

        expected_return = {
            "extension_id": extension_id,
            "status": "already_installed",
            "message": f"Extension '{extension_id}' is already installed."
        }
        self.assertEqual(result, expected_return)
        self.assertEqual(len(DB['installed_vscode_extensions']), initial_installed_count)

    def test_success_installation_when_installed_list_initially_empty(self):
        DB['installed_vscode_extensions'] = []
        extension_id = "dbaeumer.vscode-eslint"
        extension_name = "ESLint"

        result = install_extension(extension_id=extension_id)

        expected_return = {
            "extension_id": extension_id,
            "status": "success",
            "message": f"Extension '{extension_id}' installed successfully."
        }
        self.assertEqual(result, expected_return)
        self.assertEqual(len(DB['installed_vscode_extensions']), 1)
        installed_entry = DB['installed_vscode_extensions'][0]
        self.assertEqual(installed_entry, extension_id)

    def test_success_installation_when_installed_list_key_missing(self):
        DB['installed_vscode_extensions'] = []
        extension_id = "ms-python.python"
        extension_name = "Python Extension"

        result = install_extension(extension_id=extension_id)

        expected_return = {
            "extension_id": extension_id,
            "status": "success",
            "message": f"Extension '{extension_id}' installed successfully."
        }
        self.assertEqual(result, expected_return)
        self.assertTrue('installed_vscode_extensions' in DB)
        self.assertEqual(len(DB['installed_vscode_extensions']), 1)
        installed_entry = DB['installed_vscode_extensions'][0]
        self.assertEqual(installed_entry, extension_id)

