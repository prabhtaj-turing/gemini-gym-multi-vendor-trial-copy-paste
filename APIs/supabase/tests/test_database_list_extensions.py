import unittest
import copy

from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..database import list_extensions
from ..SimulationEngine import custom_errors

class TestListExtensions(BaseTestCaseWithErrorHandler):
    """
    Test suite for the list_extensions function.
    """

    PROJECT_ID_WITH_EXTENSIONS = "proj_valid_with_extensions"
    PROJECT_ID_NO_EXTENSIONS_EMPTY_LIST = "proj_valid_no_extensions_empty_list"
    PROJECT_ID_NO_EXTENSIONS_MISSING_KEY = "proj_valid_no_extensions_missing_key"
    PROJECT_ID_FOR_DB_ERROR_SIM = "proj_for_db_error_sim" 
    NON_EXISTENT_PROJECT_ID = "proj_invalid_non_existent"

    def setUp(self):
        """
        Set up the test environment before each test.
        This involves creating a deep copy of the original DB state,
        clearing the global DB, and populating it with test-specific data.
        """
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB["projects"] = [
            {
                "id": self.PROJECT_ID_WITH_EXTENSIONS,
                "name": "Project With Extensions",
                "organization_id": "org_test_1",
                "region": "us-east-1",
                "status": "ACTIVE_HEALTHY",
                "created_at": "2023-01-01T10:00:00Z",
                "version": "15.1.0.114"
            },
            {
                "id": self.PROJECT_ID_NO_EXTENSIONS_EMPTY_LIST,
                "name": "Project No Extensions (Empty List)",
                "organization_id": "org_test_1",
                "region": "eu-west-2",
                "status": "ACTIVE_HEALTHY",
                "created_at": "2023-01-02T11:00:00Z",
                "version": "15.1.0.114"
            },
            {
                "id": self.PROJECT_ID_NO_EXTENSIONS_MISSING_KEY,
                "name": "Project No Extensions (Missing Key)",
                "organization_id": "org_test_2",
                "region": "ap-southeast-1",
                "status": "ACTIVE_HEALTHY",
                "created_at": "2023-01-03T12:00:00Z",
                "version": "15.1.0.114"
            },
            {
                "id": self.PROJECT_ID_FOR_DB_ERROR_SIM,
                "name": "Project for DB Error Simulation",
                "organization_id": "org_test_3",
                "region": "us-west-1",
                "status": "REQUIRES_SPECIAL_HANDLING", # Hypothetical status for error simulation
                "created_at": "2023-01-04T13:00:00Z",
                "version": "15.1.0.114"
            }
        ]
        DB["extensions"] = {
            self.PROJECT_ID_WITH_EXTENSIONS: [
                {
                    "name": "uuid-ossp",
                    "schema": "public", 
                    "version": "1.1",
                    "description": "generate universally unique identifiers (UUIDs)"
                },
                {
                    "name": "pg_stat_statements",
                    "schema": "public",
                    "version": "1.9",
                    "description": "track execution statistics of all SQL statements executed"
                }
            ],
            self.PROJECT_ID_NO_EXTENSIONS_EMPTY_LIST: []
        }
        DB["organizations"] = []
        DB["tables"] = {}
        DB["migrations"] = {}
        DB["edge_functions"] = {}
        DB["branches"] = {}
        DB["costs"] = {}
        DB["unconfirmed_costs"] = {}
        DB["project_urls"] = {}
        DB["project_anon_keys"] = {}
        DB["project_ts_types"] = {}
        DB["logs"] = {}

    def tearDown(self):
        """
        Clean up the test environment after each test.
        This involves restoring the global DB to its original state.
        """
        DB.clear()
        DB.update(self._original_DB_state)

    def test_list_extensions_success_project_with_extensions(self):
        """
        Test listing extensions for a project that has extensions.
        Ensures returned dictionaries have 'schema' key as per docstring.
        """
        extensions = list_extensions(project_id=self.PROJECT_ID_WITH_EXTENSIONS)
        
        expected_extensions = [
            {
                "name": "uuid-ossp",
                "schema": "public", # Expecting "schema" in output
                "version": "1.1",
                "description": "generate universally unique identifiers (UUIDs)"
            },
            {
                "name": "pg_stat_statements",
                "schema": "public",
                "version": "1.9",
                "description": "track execution statistics of all SQL statements executed"
            }
        ]
        self.assertEqual(len(extensions), 2)
        # Assuming order is preserved from DB setup; otherwise, use assertCountEqual
        self.assertEqual(extensions, expected_extensions)

    def test_list_extensions_success_project_with_no_extensions_in_list(self):
        """
        Test listing extensions for a project that exists but has an empty list of extensions.
        """
        extensions = list_extensions(project_id=self.PROJECT_ID_NO_EXTENSIONS_EMPTY_LIST)
        self.assertIsInstance(extensions, list)
        self.assertEqual(len(extensions), 0)

    def test_list_extensions_success_project_with_extensions_key_missing(self):
        """
        Test listing extensions for a project where the project_id is not a key in DB["extensions"].
        This should result in an empty list of extensions.
        """
        extensions = list_extensions(project_id=self.PROJECT_ID_NO_EXTENSIONS_MISSING_KEY)
        self.assertIsInstance(extensions, list)
        self.assertEqual(len(extensions), 0)

    def test_list_extensions_project_not_found_raises_notfounderror(self):
        """
        Test listing extensions for a project_id that does not exist.
        Should raise custom_errors.NotFoundError.
        """
        self.assert_error_behavior(
            func_to_call=list_extensions,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message=f"Project with id '{self.NON_EXISTENT_PROJECT_ID}' not found.",
            project_id=self.NON_EXISTENT_PROJECT_ID
        )

    def test_list_extensions_invalid_project_id_type_raises_validationerror(self):
        """
        Test listing extensions with a project_id of an invalid type (e.g., integer).
        Should raise custom_errors.ValidationError.
        """
        self.assert_error_behavior(
            func_to_call=list_extensions,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="Input should be a valid string", # Substring match for Pydantic-like errors
            project_id=12345 
        )

    def test_list_extensions_empty_project_id_string_raises_notfounderror(self):
        """
        Test listing extensions with an empty string as project_id.
        Assuming this is treated as a non-existent project, raising NotFoundError.
        """
        self.assert_error_behavior(
            func_to_call=list_extensions,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Project with id '' not found.",
            project_id=""
        )


if __name__ == '__main__':
    unittest.main()