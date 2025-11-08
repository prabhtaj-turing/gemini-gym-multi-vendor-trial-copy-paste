import unittest
import copy
import os
import sys
from unittest.mock import patch

# Ensure parent directory is in path for module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ..SimulationEngine import utils
from .. import DB as GlobalDBSource
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestMatchesGlobPatterns(BaseTestCaseWithErrorHandler):
    """
    Focused tests for utils.matches_glob_patterns covering edge pattern syntaxes:
    - Brace expansion like '*.{java,kt}' (supported via wcmatch)
    - Recursive globstar '**' behavior
    - Extglobs like '@(a|b)', '!(a|b)', '+(pat)' (supported)
    - Alternation with '|' outside of brackets (supported by split)
    - POSIX character classes like '[[:alnum:]]' (supported)
    - Tilde and env var expansion (~, $HOME) (supported)
    - Regex features with 're:' prefix such as anchors/lookaheads/groups (supported)
    """

    def setUp(self):
        self.pristine_db_state = copy.deepcopy(GlobalDBSource)
        self.db_for_test = copy.deepcopy(self.pristine_db_state)
        self.db_for_test["workspace_root"] = "/ws"
        self.db_for_test["cwd"] = "/ws"
        self.db_for_test["file_system"] = {}

        # Patch the DB used inside utils
        self.utils_db_patcher = patch('cursor.SimulationEngine.utils.DB', self.db_for_test)
        self.utils_db_patcher.start()

    def tearDown(self):
        self.utils_db_patcher.stop()

    def test_brace_expansion_supported(self):
        java_path = "/ws/project/Main.java"
        kt_path = "/ws/project/Main.kt"

        # Brace expansion is supported
        self.assertTrue(utils.matches_glob_patterns(java_path, include_patterns=['*.{java,kt}']))
        self.assertTrue(utils.matches_glob_patterns(kt_path, include_patterns=['*.{java,kt}']))

        # Using separate patterns DOES work
        self.assertTrue(utils.matches_glob_patterns(java_path, include_patterns=['*.java']))
        self.assertTrue(utils.matches_glob_patterns(kt_path, include_patterns=['*.kt']))
        self.assertTrue(utils.matches_glob_patterns(java_path, include_patterns=['*.java', '*.kt']))
        self.assertTrue(utils.matches_glob_patterns(kt_path, include_patterns=['*.java', '*.kt']))

    def test_recursive_globstar_double_star(self):
        deep_py = "/ws/a/b/c/file.py"
        top_py = "/ws/file.py"

        # '**/*.py' should match files at any depth
        self.assertTrue(utils.matches_glob_patterns(deep_py, include_patterns=['**/*.py']))
        # '*.py' matches top-level by basename candidate
        self.assertTrue(utils.matches_glob_patterns(top_py, include_patterns=['*.py']))

    def test_extglobs_supported(self):
        a_txt = "/ws/a.txt"
        pat_txt = "/ws/pat.txt"

        # Extglob patterns should match accordingly
        self.assertTrue(utils.matches_glob_patterns(a_txt, include_patterns=['@(a|b).txt']))
        self.assertTrue(utils.matches_glob_patterns(pat_txt, include_patterns=['!(a|b).txt']))
        self.assertTrue(utils.matches_glob_patterns(pat_txt, include_patterns=['+(pat).txt']))

    def test_alternation_with_pipe_supported(self):
        js_file = "/ws/app.js"
        ts_file = "/ws/app.ts"

        # Pipe alternation across top-level (split and evaluate patterns)
        self.assertTrue(utils.matches_glob_patterns(js_file, include_patterns=['*.js|*.ts']))
        self.assertTrue(utils.matches_glob_patterns(ts_file, include_patterns=['*.js|*.ts']))

        # Separate patterns do match
        self.assertTrue(utils.matches_glob_patterns(js_file, include_patterns=['*.js', '*.ts']))
        self.assertTrue(utils.matches_glob_patterns(ts_file, include_patterns=['*.js', '*.ts']))

    def test_posix_character_classes_supported(self):
        # POSIX class [[:alnum:]] should be supported
        num_file = "/ws/5.txt"
        alpha_file = "/ws/a.txt"

        self.assertTrue(utils.matches_glob_patterns(num_file, include_patterns=['[[:alnum:]].txt']))
        self.assertTrue(utils.matches_glob_patterns(alpha_file, include_patterns=['[[:alnum:]].txt']))

    def test_tilde_and_env_var_expansion_supported(self):
        try:
            home = os.path.expanduser('~')
        except Exception:
            home = "/home/user"
        target = os.path.normpath(os.path.join(home, 'foo.py'))

        self.assertTrue(utils.matches_glob_patterns(target, include_patterns=['~/*.py']))
        with patch.dict(os.environ, {"HOME": home}, clear=False):
            self.assertTrue(utils.matches_glob_patterns(target, include_patterns=['$HOME/*.py']))

    def test_regex_features_supported_with_prefix(self):
        path = "/ws/file123.txt"

        # Supported via 're:' prefix
        self.assertTrue(utils.matches_glob_patterns(path, include_patterns=['re:.*file\\d+\\.txt$']))
        # Lookahead example (assert then consume):
        self.assertTrue(utils.matches_glob_patterns(path, include_patterns=['re:file(?=123)123\\.txt']))

    def test_exclude_patterns_override_includes(self):
        path = "/ws/node_modules/pkg/index.js"
        self.assertFalse(
            utils.matches_glob_patterns(
                path,
                include_patterns=['**/*.js'],
                exclude_patterns=['**/node_modules/**']
            )
        )



if __name__ == '__main__':
    unittest.main()


