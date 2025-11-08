import copy
import unittest

from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from .. import test_search
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestTestSearch(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB['workspace_root'] = '/test_ws'
        DB['cwd'] = '/test_ws'
        DB['file_system'] = {}
        DB['file_system']['/test_ws'] = {'path': '/test_ws', 'is_directory': True, 'content_lines': [], 'size_bytes': 0,
                                         'last_modified': '2023-01-01T12:00:00Z'}

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _add_file_to_db(self, relative_path: str, content: str = '', is_directory: bool = False):
        """
        Adds a file or directory to the DB's file_system.
        relative_path is relative to DB["workspace_root"], e.g., "app.py" or "src/module.py".
        """
        workspace_root = DB['workspace_root']
        _cleaned_relative_path = relative_path.lstrip('/')
        full_path_in_db = f"{workspace_root.rstrip('/')}/{_cleaned_relative_path}"
        path_parts = _cleaned_relative_path.split('/')
        current_parent_dir_path_in_db = workspace_root.rstrip('/')
        for i in range(len(path_parts) - 1):
            part = path_parts[i]
            if not part:
                continue
            current_parent_dir_path_in_db = f'{current_parent_dir_path_in_db}/{part}'
            if current_parent_dir_path_in_db not in DB['file_system']:
                DB['file_system'][current_parent_dir_path_in_db] = {'path': current_parent_dir_path_in_db,
                                                                    'is_directory': True, 'content_lines': [],
                                                                    'size_bytes': 0,
                                                                    'last_modified': '2023-01-01T12:00:00Z'}
        DB['file_system'][full_path_in_db] = {'path': full_path_in_db, 'is_directory': is_directory,
                                              'content_lines': content.splitlines(
                                                  keepends=True) if not is_directory and content is not None else [],
                                              'size_bytes': len(content.encode(
                                                  'utf-8')) if not is_directory and content is not None else 0,
                                              'last_modified': '2023-01-01T12:00:00Z'}

    def test_search_source_to_test_simple_convention(self):
        self._add_file_to_db('app.py', 'source code')
        self._add_file_to_db('test_app.py', 'test code')
        result = test_search(file_path='/test_ws/app.py')
        self.assertEqual(result['input_file_path'], '/test_ws/app.py')
        self.assertEqual(result['related_file_path'], '/test_ws/test_app.py')
        self.assertEqual(result['relationship_type'], 'test_file_for_source')
        self.assertIsInstance(result['confidence_score'], float)
        self.assertTrue(0.0 <= result['confidence_score'] <= 1.0)

    def test_search_test_to_source_simple_convention(self):
        self._add_file_to_db('app.py', 'source code')
        self._add_file_to_db('app_test.py', 'test code for app.py')
        result = test_search(file_path='/test_ws/app_test.py')
        self.assertEqual(result['input_file_path'], '/test_ws/app_test.py')
        self.assertEqual(result['related_file_path'], '/test_ws/app.py')
        self.assertEqual(result['relationship_type'], 'source_file_for_test')
        self.assertIsInstance(result['confidence_score'], float)

    def test_search_source_to_test_suffix_convention(self):
        self._add_file_to_db('module.py', 'source code')
        self._add_file_to_db('module_test.py', 'test code')
        result = test_search(file_path='/test_ws/module.py')
        self.assertEqual(result['input_file_path'], '/test_ws/module.py')
        self.assertEqual(result['related_file_path'], '/test_ws/module_test.py')
        self.assertEqual(result['relationship_type'], 'test_file_for_source')
        self.assertIsInstance(result['confidence_score'], float)

    def test_search_test_to_source_suffix_convention(self):
        self._add_file_to_db('module.py', 'source code')
        self._add_file_to_db('module_test.py', 'test code')
        result = test_search(file_path='/test_ws/module_test.py')
        self.assertEqual(result['related_file_path'], '/test_ws/module.py')
        self.assertEqual(result['relationship_type'], 'source_file_for_test')

    def test_search_source_to_test_in_tests_subdirectory(self):
        self._add_file_to_db('src/utils.py', 'source code')
        self._add_file_to_db('tests/test_utils.py', 'test code')
        result = test_search(file_path='/test_ws/src/utils.py')
        self.assertEqual(result['related_file_path'], '/test_ws/tests/test_utils.py')
        self.assertEqual(result['relationship_type'], 'test_file_for_source')

    def test_search_test_to_source_from_tests_subdirectory(self):
        self._add_file_to_db('src/utils.py', 'source code')
        self._add_file_to_db('tests/test_utils.py', 'test code')
        result = test_search(file_path='/test_ws/tests/test_utils.py')
        self.assertEqual(result['related_file_path'], '/test_ws/src/utils.py')
        self.assertEqual(result['relationship_type'], 'source_file_for_test')

    def test_search_source_to_test_deeply_nested(self):
        self._add_file_to_db('app/core/services/data_processor.py', 'source')
        self._add_file_to_db('tests/core/services/test_data_processor.py', 'test')
        result = test_search(file_path='/test_ws/app/core/services/data_processor.py')
        self.assertEqual(result['input_file_path'], '/test_ws/app/core/services/data_processor.py')
        self.assertEqual(result['related_file_path'], '/test_ws/tests/core/services/test_data_processor.py')
        self.assertEqual(result['relationship_type'], 'test_file_for_source')
        self.assertIsInstance(result['confidence_score'], float)

    def test_search_no_related_file_found_for_source(self):
        self._add_file_to_db('lonely_component.py', 'source code')
        result = test_search(file_path='/test_ws/lonely_component.py')
        self.assertEqual(result['input_file_path'], '/test_ws/lonely_component.py')
        self.assertIsNone(result['related_file_path'])
        self.assertIsNone(result['relationship_type'])
        self.assertIsNone(result['confidence_score'])

    def test_search_no_related_file_found_for_test(self):
        self._add_file_to_db('test_orphaned_feature.py', 'test code')
        result = test_search(file_path='/test_ws/test_orphaned_feature.py')
        self.assertIsNone(result['related_file_path'])
        self.assertIsNone(result['relationship_type'])
        self.assertIsNone(result['confidence_score'])

    def test_search_relative_path_input_resolved_correctly(self):
        DB['cwd'] = '/test_ws/src'
        self._add_file_to_db('src/app.py', 'source code')
        self._add_file_to_db('src/test_app.py', 'test code')
        result = test_search(file_path='app.py')
        self.assertEqual(result['input_file_path'], '/test_ws/src/app.py')
        self.assertEqual(result['related_file_path'], '/test_ws/src/test_app.py')
        self.assertEqual(result['relationship_type'], 'test_file_for_source')

    def test_search_input_path_with_dot_dot_resolved_correctly(self):
        DB['cwd'] = '/test_ws/src/module'
        self._add_file_to_db('src/app.py', 'source code')
        self._add_file_to_db('src/test_app.py', 'test code')
        self._add_file_to_db('src/module/main.py', 'main in module')
        result = test_search(file_path='../app.py')
        self.assertEqual(result['input_file_path'], '/test_ws/src/app.py')
        self.assertEqual(result['related_file_path'], '/test_ws/src/test_app.py')

    def test_search_filename_with_multiple_extensions(self):
        self._add_file_to_db('archive.tar.gz', 'source-like content')
        self._add_file_to_db('test_archive.tar.gz', 'test-like content')
        result = test_search(file_path='/test_ws/archive.tar.gz')
        self.assertEqual(result['related_file_path'], '/test_ws/test_archive.tar.gz')
        self.assertEqual(result['relationship_type'], 'test_file_for_source')

    def test_search_filename_starting_with_test_is_source(self):
        self._add_file_to_db('test_framework_core.py', 'actual source code')
        self._add_file_to_db('test_test_framework_core.py', 'test for the source')
        result = test_search(file_path='/test_ws/test_framework_core.py')
        self.assertEqual(result['related_file_path'], '/test_ws/test_test_framework_core.py')
        self.assertEqual(result['relationship_type'], 'test_file_for_source')
        result_rev = test_search(file_path='/test_ws/test_test_framework_core.py')
        self.assertEqual(result_rev['related_file_path'], '/test_ws/test_framework_core.py')
        self.assertEqual(result_rev['relationship_type'], 'source_file_for_test')

    def test_search_input_file_not_found_raises_file_not_found_error(self):
        self.assert_error_behavior(func_to_call=test_search, expected_exception_type=custom_errors.FileNotFoundError,
                                   expected_message='File not found: /test_ws/non_existent_file.py',
                                   file_path='/test_ws/non_existent_file.py')

    def test_search_input_path_is_directory_raises_project_configuration_error(self):
        self._add_file_to_db('src', is_directory=True)
        self.assert_error_behavior(func_to_call=test_search,
                                   expected_exception_type=custom_errors.ProjectConfigurationError,
                                   expected_message='Input path must be a file, not a directory: /test_ws/src',
                                   file_path='/test_ws/src')

    def test_search_invalid_file_path_type_raises_validation_error(self):
        self.assert_error_behavior(func_to_call=test_search, expected_exception_type=custom_errors.ValidationError,
                                   expected_message="Input 'file_path' must be a string", file_path=12345)

    def test_search_empty_file_path_raises_validation_error(self):
        self.assert_error_behavior(func_to_call=test_search, expected_exception_type=custom_errors.ValidationError,
                                   expected_message="Input 'file_path' cannot be empty", file_path='')

    def test_search_project_config_error_if_workspace_root_missing_in_db(self):
        self._add_file_to_db('app.py', 'source')
        original_ws_root = DB.get('workspace_root')
        if 'workspace_root' in DB:
            del DB['workspace_root']
        try:
            self.assert_error_behavior(func_to_call=test_search,
                                       expected_exception_type=custom_errors.ProjectConfigurationError,
                                       expected_message='Workspace root is not configured.',
                                       file_path='/test_ws/app.py')
        finally:
            if original_ws_root is not None:
                DB['workspace_root'] = original_ws_root

    def test_search_path_outside_workspace_raises_project_config_error(self):
        self.assert_error_behavior(func_to_call=test_search,
                                   expected_exception_type=custom_errors.ProjectConfigurationError,
                                   expected_message="Absolute path '/another_ws/app.py' is outside the configured workspace root '/test_ws'.",
                                   file_path='/another_ws/app.py')

    def test_search_search_logic_error_for_malformed_db_entry(self):
        if DB['workspace_root'] not in DB['file_system']:
            DB['file_system'][DB['workspace_root']] = {'path': DB['workspace_root'], 'is_directory': True,
                                                       'content_lines': [], 'size_bytes': 0, 'last_modified': '...'}
        DB['file_system']['/test_ws/app.py'] = 'this string is not a dictionary'
        self.assert_error_behavior(func_to_call=test_search, expected_exception_type=custom_errors.SearchLogicError,
                                   expected_message='Internal error processing file system data for path /test_ws/app.py',
                                   file_path='/test_ws/app.py')


if __name__ == '__main__':
    unittest.main()
