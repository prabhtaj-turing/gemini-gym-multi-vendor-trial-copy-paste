import copy
import unittest
from unittest.mock import patch, call, PropertyMock

from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from .. import get_changed_files
from .. import run_in_terminal
from common_utils.base_case import BaseTestCaseWithErrorHandler

PATCH_TARGET_RUN_IN_TERMINAL = 'copilot.code_quality_version_control.run_in_terminal'


class TestGetChangedFiles(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB['workspace_root'] = '/test_workspace'
        DB['cwd'] = '/test_workspace'

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_not_a_git_repository_rev_parse_false(self, mock_run_in_terminal):
        mock_run_in_terminal.return_value = {
            'status_message': 'Command executed successfully',
            'terminal_id': None,
            'stdout': 'false\n',
            'stderr': '',
            'exit_code': 0
        }
        self.assert_error_behavior(func_to_call=get_changed_files,
                                   expected_exception_type=custom_errors.GitRepositoryNotFoundError,
                                   expected_message='The current workspace is not a git repository.')
        mock_run_in_terminal.assert_called_once_with('git rev-parse --is-inside-work-tree')

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_not_a_git_repository_rev_parse_fails(self, mock_run_in_terminal):
        mock_run_in_terminal.return_value = {
            'status_message': 'Command failed',
            'terminal_id': None,
            'stdout': '',
            'stderr': 'fatal: not a git repository',
            'exit_code': 128
        }
        self.assert_error_behavior(func_to_call=get_changed_files,
                                   expected_exception_type=custom_errors.GitRepositoryNotFoundError,
                                   expected_message='Failed to confirm git repository status. Git command error: fatal: not a git repository')
        mock_run_in_terminal.assert_called_once_with('git rev-parse --is-inside-work-tree')

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_git_command_not_found_rev_parse(self, mock_run_in_terminal):
        mock_run_in_terminal.side_effect = custom_errors.CommandExecutionError('git: command not found')
        self.assert_error_behavior(func_to_call=get_changed_files,
                                   expected_exception_type=custom_errors.GitRepositoryNotFoundError,
                                   expected_message='Git command not found or failed to execute. Ensure git is installed and in PATH.')
        mock_run_in_terminal.assert_called_once_with('git rev-parse --is-inside-work-tree')

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_empty_diff_no_changes(self, mock_run_in_terminal):
        mock_run_in_terminal.side_effect = [
            {
                'status_message': 'Command executed successfully',
                'terminal_id': None,
                'stdout': 'true\n',
                'stderr': '',
                'exit_code': 0
            },
            {
                'status_message': 'Command executed successfully',
                'terminal_id': None,
                'stdout': '',
                'stderr': '',
                'exit_code': 0
            }
        ]
        result = get_changed_files()
        self.assertEqual(result, [])
        expected_calls = [call('git rev-parse --is-inside-work-tree'), call('git diff --name-status --unified=0 HEAD')]
        self.assertEqual(mock_run_in_terminal.call_args_list, expected_calls)

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_modified_file(self, mock_run_in_terminal):
        mock_run_in_terminal.side_effect = [
            {
                'status_message': 'Command executed successfully',
                'terminal_id': None,
                'stdout': 'true\n',
                'stderr': '',
                'exit_code': 0
            },
            {
                'status_message': 'Command executed successfully',
                'terminal_id': None,
                'stdout': 'M\tfile1.py\n',
                'stderr': '',
                'exit_code': 0
            },
            {
                'status_message': 'Command executed successfully',
                'terminal_id': None,
                'stdout': '--- a/file1.py\n+++ b/file1.py\n@@ -1,1 +1,1 @@\n-old\n+new\n',
                'stderr': '',
                'exit_code': 0
            }
        ]
        result = get_changed_files()
        expected = [{'file_path': 'file1.py', 'status': 'modified',
                     'diff_hunks': '--- a/file1.py\n+++ b/file1.py\n@@ -1,1 +1,1 @@\n-old\n+new\n',
                     'old_file_path': None}]
        self.assertEqual(result, expected)
        expected_diff_call = call(f'git diff --unified=0 HEAD -- file1.py', )
        self.assertEqual(mock_run_in_terminal.call_args_list[2], expected_diff_call)

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_added_file(self, mock_run_in_terminal):
        mock_run_in_terminal.side_effect = [{'stdout': 'true\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': 'A\tnew_file.txt\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': '--- /dev/null\n+++ b/new_file.txt\n@@ -0,0 +1 @@\n+content\n',
                                             'stderr': '', 'exit_code': 0}]
        result = get_changed_files()
        expected = [{'file_path': 'new_file.txt', 'status': 'added',
                     'diff_hunks': '--- /dev/null\n+++ b/new_file.txt\n@@ -0,0 +1 @@\n+content\n',
                     'old_file_path': None}]
        self.assertEqual(result, expected)

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_added_binary_file(self, mock_run_in_terminal):
        mock_run_in_terminal.side_effect = [{'stdout': 'true\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': 'A\timage.png\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': 'Binary files /dev/null and b/image.png differ\n', 'stderr': '',
                                             'exit_code': 0}]
        result = get_changed_files()
        expected = [{'file_path': 'image.png', 'status': 'added', 'diff_hunks': '', 'old_file_path': None}]
        self.assertEqual(result, expected)

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_deleted_file(self, mock_run_in_terminal):
        mock_run_in_terminal.side_effect = [{'stdout': 'true\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': 'D\tdeleted_file.md\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': '--- a/deleted_file.md\n+++ /dev/null\n@@ -1 @@\n-old content\n',
                                             'stderr': '', 'exit_code': 0}]
        result = get_changed_files()
        expected = [{'file_path': 'deleted_file.md', 'status': 'deleted',
                     'diff_hunks': '--- a/deleted_file.md\n+++ /dev/null\n@@ -1 @@\n-old content\n',
                     'old_file_path': None}]
        self.assertEqual(result, expected)
        expected_diff_call = call(f'git diff --unified=0 HEAD -- deleted_file.md', )
        self.assertEqual(mock_run_in_terminal.call_args_list[2], expected_diff_call)

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_renamed_file(self, mock_run_in_terminal):
        mock_run_in_terminal.side_effect = [{'stdout': 'true\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': 'R100\told_name.py\tnew_name.py\n', 'stderr': '',
                                             'exit_code': 0},
                                            {'stdout': '--- a/old_name.py\n+++ b/new_name.py\n@@ -1 +1 @@\n content\n',
                                             'stderr': '', 'exit_code': 0}]
        result = get_changed_files()
        expected = [{'file_path': 'new_name.py', 'status': 'renamed',
                     'diff_hunks': '--- a/old_name.py\n+++ b/new_name.py\n@@ -1 +1 @@\n content\n',
                     'old_file_path': 'old_name.py'}]
        self.assertEqual(result, expected)

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_renamed_file_with_similarity(self, mock_run_in_terminal):
        mock_run_in_terminal.side_effect = [{'stdout': 'true\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': 'R085\tsrc/old.java\tsrc/new.java\n', 'stderr': '',
                                             'exit_code': 0},
                                            {'stdout': 'diff content for new.java', 'stderr': '', 'exit_code': 0}]
        result = get_changed_files()
        expected = [{'file_path': 'src/new.java', 'status': 'renamed', 'diff_hunks': 'diff content for new.java',
                     'old_file_path': 'src/old.java'}]
        self.assertEqual(result, expected)
        expected_diff_call = call(f'git diff --unified=0 HEAD -- src/new.java', )
        self.assertEqual(mock_run_in_terminal.call_args_list[2], expected_diff_call)

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_copied_file(self, mock_run_in_terminal):
        mock_run_in_terminal.side_effect = [{'stdout': 'true\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': 'C090\toriginal.txt\tcopied.txt\n', 'stderr': '',
                                             'exit_code': 0},
                                            {'stdout': 'diff content for copied.txt', 'stderr': '', 'exit_code': 0}]
        result = get_changed_files()
        expected = [{'file_path': 'copied.txt', 'status': 'copied', 'diff_hunks': 'diff content for copied.txt',
                     'old_file_path': 'original.txt'}]
        self.assertEqual(result, expected)

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_multiple_files_different_statuses(self, mock_run_in_terminal):
        mock_run_in_terminal.side_effect = [{'stdout': 'true\n', 'stderr': '', 'exit_code': 0}, {
            'stdout': 'M\tapp/main.py\nA\tdata/new_data.csv\nR100\tutils/old_helper.py\tutils/new_helper.py\nD\tdocs/stale.md\n',
            'stderr': '', 'exit_code': 0}, {'stdout': 'diff for main.py', 'stderr': '', 'exit_code': 0},
                                            {'stdout': 'diff for new_data.csv', 'stderr': '', 'exit_code': 0},
                                            {'stdout': 'diff for new_helper.py', 'stderr': '', 'exit_code': 0},
                                            {'stdout': 'diff for stale.md', 'stderr': '', 'exit_code': 0}]
        result = get_changed_files()
        expected = [
            {'file_path': 'app/main.py', 'status': 'modified', 'diff_hunks': 'diff for main.py', 'old_file_path': None},
            {'file_path': 'data/new_data.csv', 'status': 'added', 'diff_hunks': 'diff for new_data.csv',
             'old_file_path': None},
            {'file_path': 'utils/new_helper.py', 'status': 'renamed', 'diff_hunks': 'diff for new_helper.py',
             'old_file_path': 'utils/old_helper.py'},
            {'file_path': 'docs/stale.md', 'status': 'deleted', 'diff_hunks': 'diff for stale.md',
             'old_file_path': None}]
        self.assertEqual(result, expected)
        expected_calls = [call('git rev-parse --is-inside-work-tree', ),
                          call('git diff --name-status --unified=0 HEAD', ),
                          call('git diff --unified=0 HEAD -- app/main.py', ),
                          call('git diff --unified=0 HEAD -- data/new_data.csv', ),
                          call('git diff --unified=0 HEAD -- utils/new_helper.py', ),
                          call('git diff --unified=0 HEAD -- docs/stale.md', )]
        self.assertEqual(mock_run_in_terminal.call_args_list, expected_calls)

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_name_status_command_fails(self, mock_run_in_terminal):
        mock_run_in_terminal.side_effect = [{'stdout': 'true\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': '', 'stderr': 'git diff failed', 'exit_code': 1}]
        self.assert_error_behavior(func_to_call=get_changed_files,
                                   expected_exception_type=custom_errors.GitCommandError,
                                   expected_message="Error executing 'git diff --name-status --unified=0 HEAD': git diff failed")

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_file_specific_diff_command_fails(self, mock_run_in_terminal):
        mock_run_in_terminal.side_effect = [{'stdout': 'true\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': 'M\tcorrupted_file.json\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': '', 'stderr': 'fatal: unable to read corrupted_file.json',
                                             'exit_code': 128}]
        self.assert_error_behavior(func_to_call=get_changed_files,
                                   expected_exception_type=custom_errors.GitCommandError,
                                   expected_message="Error executing 'git diff --unified=0 HEAD -- corrupted_file.json': fatal: unable to read corrupted_file.json")

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_path_with_spaces(self, mock_run_in_terminal):
        file_with_space = 'my dir/file with spaces.txt'
        mock_run_in_terminal.side_effect = [{'stdout': 'true\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': f'A\t{file_with_space}\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': f'diff for {file_with_space}', 'stderr': '', 'exit_code': 0}]
        result = get_changed_files()
        expected = [{'file_path': file_with_space, 'status': 'added', 'diff_hunks': f'diff for {file_with_space}',
                     'old_file_path': None}]
        self.assertEqual(result, expected)
        self.assertEqual(mock_run_in_terminal.call_args_list[2], call(f'git diff --unified=0 HEAD -- "{file_with_space}"'))

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_unknown_status_line_format_ignored(self, mock_run_in_terminal):
        mock_run_in_terminal.side_effect = [{'stdout': 'true\n', 'stderr': '', 'exit_code': 0},
                                            {'stdout': 'M\tfile1.py\nINVALID_LINE\tfile2.py\n', 'stderr': '',
                                             'exit_code': 0},
                                            {'stdout': 'diff for file1.py', 'stderr': '', 'exit_code': 0}]
        result = get_changed_files()
        expected = [
            {'file_path': 'file1.py', 'status': 'modified', 'diff_hunks': 'diff for file1.py', 'old_file_path': None}]
        self.assertEqual(result, expected)

    @patch(PATCH_TARGET_RUN_IN_TERMINAL)
    def test_status_parsing_various_types(self, mock_run_in_terminal):
        mock_run_in_terminal.side_effect = [{'stdout': 'true\n', 'stderr': '', 'exit_code': 0}, {
            'stdout': 'T\tfile_type_changed.txt\nU\tfile_unmerged.txt\nM\tactual_modified.txt\n', 'stderr': '',
            'exit_code': 0}, {'stdout': 'diff for actual_modified', 'stderr': '', 'exit_code': 0}]
        result = get_changed_files()
        expected = [{'file_path': 'actual_modified.txt', 'status': 'modified', 'diff_hunks': 'diff for actual_modified',
                     'old_file_path': None}]
        self.assertEqual(result, expected)
        expected_calls = [call('git rev-parse --is-inside-work-tree', ),
                          call('git diff --name-status --unified=0 HEAD', ),
                          call('git diff --unified=0 HEAD -- actual_modified.txt', )]
        self.assertEqual(mock_run_in_terminal.call_args_list, expected_calls)


if __name__ == '__main__':
    unittest.main()
