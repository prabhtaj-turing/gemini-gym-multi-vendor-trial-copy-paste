from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import custom_errors
import copy
from .. import get_vscode_api
from ..SimulationEngine.db import DB


class TestGetVSCodeAPI(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.api_ref1_full = {
            'name': 'window.showInformationMessage',
            'documentation_summary': 'Shows an information message to the user.',
            'module': 'vscode.window',
            'kind': 'function',
            'signature': 'showInformationMessage(message: string, ...items: string[]): Thenable<string | undefined>',
            'example_usage': "vscode.window.showInformationMessage('Hello world!');"
        }
        self.api_ref2_command = {
            'name': 'commands.executeCommand',
            'documentation_summary': 'Executes a command with arguments.',
            'module': 'vscode.commands',
            'kind': 'function',
            'signature': 'executeCommand<T>(command: string, ...rest: any[]): Thenable<T | undefined>',
            'example_usage': "vscode.commands.executeCommand('workbench.action.openGlobalSettings');"
        }
        self.api_ref3_interface_no_optionals = {
            'name': 'TextDocument',
            'documentation_summary': 'Represents a text document, such as a file on disk. Useful for content.',
            'module': 'vscode',  # Top-level module
            'kind': 'interface',
            'signature': None,
            'example_usage': None
        }
        self.api_ref4_config = {
            'name': 'workspace.getConfiguration',
            'documentation_summary': 'Get a workspace configuration object for settings.',
            'module': 'vscode.workspace',
            'kind': 'function',
            'signature': 'getConfiguration(section?: string, scope?: ConfigurationScope): WorkspaceConfiguration',
            'example_usage': "const config = vscode.workspace.getConfiguration('myExtension');"
        }

        DB['vscode_api_references'] = [
            copy.deepcopy(self.api_ref1_full),
            copy.deepcopy(self.api_ref2_command),
            copy.deepcopy(self.api_ref3_interface_no_optionals),
            copy.deepcopy(self.api_ref4_config)
        ]

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_successful_retrieval_specific_name(self):
        query = 'window.showInformationMessage'
        result = get_vscode_api(query=query)
        self.assertIsInstance(result, dict)
        self.assertIn('api_references', result)
        self.assertIsInstance(result['api_references'], list)
        self.assertEqual(len(result['api_references']), 1)
        self.assertEqual(result['api_references'][0], self.api_ref1_full)

    def test_successful_retrieval_partial_summary(self):
        query = 'information message'  # Matches api_ref1_full
        result = get_vscode_api(query=query)
        self.assertEqual(len(result['api_references']), 1)
        self.assertEqual(result['api_references'][0]['name'], self.api_ref1_full['name'])

    def test_successful_retrieval_module_query(self):
        query = 'vscode.commands'  # Matches api_ref2_command
        result = get_vscode_api(query=query)
        self.assertEqual(len(result['api_references']), 1)
        self.assertEqual(result['api_references'][0]['name'], self.api_ref2_command['name'])

    def test_successful_retrieval_case_insensitive(self):
        # Assuming the underlying search logic is case-insensitive as per typical search behavior
        query = 'TEXTDOCUMENT'  # Matches api_ref3_interface_no_optionals
        result = get_vscode_api(query=query)
        self.assertEqual(len(result['api_references']), 1)
        self.assertEqual(result['api_references'][0]['name'], self.api_ref3_interface_no_optionals['name'])

    def test_successful_retrieval_multiple_results(self):
        query = 'vscode'  # Matches all entries by module or name
        result = get_vscode_api(query=query)
        self.assertEqual(len(result['api_references']), 4)
        # Check if all expected items are present, order might not be guaranteed
        returned_names = sorted([item['name'] for item in result['api_references']])
        expected_names = sorted([
            self.api_ref1_full['name'],
            self.api_ref2_command['name'],
            self.api_ref3_interface_no_optionals['name'],
            self.api_ref4_config['name']
        ])
        self.assertEqual(returned_names, expected_names)

    def test_successful_retrieval_no_results(self):
        query = 'nonExistentAPINameXYZ123'
        result = get_vscode_api(query=query)
        self.assertIsInstance(result, dict)
        self.assertIn('api_references', result)
        self.assertIsInstance(result['api_references'], list)
        self.assertEqual(len(result['api_references']), 0)

    def test_successful_retrieval_with_optional_fields_null(self):
        query = 'TextDocument'  # Matches api_ref3_interface_no_optionals
        result = get_vscode_api(query=query)
        self.assertEqual(len(result['api_references']), 1)
        api_item = result['api_references'][0]
        self.assertEqual(api_item['name'], self.api_ref3_interface_no_optionals['name'])
        self.assertIsNone(api_item['signature'])
        self.assertIsNone(api_item['example_usage'])

    def test_successful_retrieval_all_fields_present(self):
        query = 'executeCommand'  # Matches api_ref2_command
        result = get_vscode_api(query=query)
        self.assertEqual(len(result['api_references']), 1)
        api_item = result['api_references'][0]
        self.assertEqual(api_item, self.api_ref2_command)
        self.assertIsNotNone(api_item['signature'])
        self.assertIsNotNone(api_item['example_usage'])

    def test_api_database_exists_but_empty_list_returns_no_results(self):
        DB['vscode_api_references'] = []
        query = 'anything'
        result = get_vscode_api(query=query)
        self.assertEqual(len(result['api_references']), 0)

    def test_error_query_too_broad_empty_string(self):
        self.assert_error_behavior(
            func_to_call=get_vscode_api,
            expected_exception_type=custom_errors.QueryTooBroadError,
            expected_message="Query is empty or too broad.",
            query=""
        )

    def test_error_query_too_broad_whitespace_string(self):
        self.assert_error_behavior(
            func_to_call=get_vscode_api,
            expected_exception_type=custom_errors.QueryTooBroadError,
            expected_message="Query is empty or too broad.",
            query="   "
        )

    def test_error_query_too_broad_specific_term(self):
        # This test depends on the mock implementation's specific "too broad" term.
        self.assert_error_behavior(
            func_to_call=get_vscode_api,
            expected_exception_type=custom_errors.QueryTooBroadError,
            expected_message="Query 'generic term' is too vague.",
            query="generic term"
        )

    def test_error_api_database_not_available(self):
        del DB['vscode_api_references']
        self.assert_error_behavior(
            func_to_call=get_vscode_api,
            expected_exception_type=custom_errors.APIDatabaseNotAvailableError,
            expected_message="VS Code API reference database not available.",
            query="some query"
        )

    def test_error_validation_query_not_string_int(self):
        # Assuming the function (or Pydantic layer) raises custom_errors.ValidationError
        # for type mismatches, as per problem statement guidance on error assertion.
        expected_msg_fragment = "Input should be a valid string"  # Pydantic messages can be complex
        self.assert_error_behavior(
            func_to_call=get_vscode_api,
            expected_exception_type=custom_errors.ValidationError,
            # For custom_errors.ValidationError, if not Pydantic's, message might be exact.
            # If it were Pydantic's, assert_error_behavior would do substring match.
            # Assuming the mock function's specific message for this test.
            expected_message="Input should be a valid string, query: <class 'int'>",
            query=123
        )

    def test_error_validation_query_not_string_list(self):
        expected_msg_fragment = "Input should be a valid string"
        self.assert_error_behavior(
            func_to_call=get_vscode_api,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input should be a valid string, query: <class 'list'>",
            query=[]
        )

    def test_query_matching_multiple_fields(self):
        # Query that could match name in one item and summary in another
        # Add a specific item for this
        specific_item = {
            'name': 'uniqueNameForSearch',
            'documentation_summary': 'This item talks about vscode commands.',
            'module': 'vscode.custom',
            'kind': 'snippet',
            'signature': None,
            'example_usage': None
        }
        DB['vscode_api_references'].append(specific_item)

        query = 'commands'  # Matches api_ref2_command by name/module, and specific_item by summary
        result = get_vscode_api(query=query)

        self.assertTrue(len(result['api_references']) >= 2)

        names_found = [item['name'] for item in result['api_references']]
        self.assertIn(self.api_ref2_command['name'], names_found)
        self.assertIn(specific_item['name'], names_found)