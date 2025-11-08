import unittest
import copy
from typing import Optional, Dict, Any, List
from pydantic import ValidationError
# from datetime import datetime # Not used in this test suite
from ..SimulationEngine import custom_errors
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..SimulationEngine.utils import create_project


class TestCreateProject(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        DB['projects'] = []

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_create_project_success(self):
        project_id = "test_project_id_123"
        project_name = "Test Project"
        response = create_project(project_id, project_name)
        self.assertEqual(response['projectId'], project_id)
        self.assertEqual(response['name'], project_name)

    def test_create_project_empty_name_raises_validation_error(self):
        project_id = "test_project_id_123"
        project_name = ""
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=ValueError,
            project_id=project_id,
            name=project_name,
            expected_message="Project name cannot be empty."
        )

    def test_create_project_empty_id_raises_validation_error(self):
        project_id = ""
        project_name = "Test Project"
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=ValueError,
            project_id=project_id,
            name=project_name,
            expected_message="Project ID cannot be empty."
        )

    def test_create_project_id_already_exists_raises_validation_error(self):
        project_id = "test_project_id_123"
        project_name = "Test Project"
        create_project(project_id, project_name)
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=ValueError,
            project_id=project_id,
            name=project_name,
            expected_message="Project with ID 'test_project_id_123' already exists."
        )

    def test_create_project_invalid_id_type_raises_validation_error(self):
        project_id = 12345
        project_name = "Test Project"
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=ValueError,
            project_id=project_id,
            name=project_name,
            expected_message="Project ID must be a string."
        )

    def test_create_project_invalid_name_type_raises_validation_error(self):
        project_id = "test_project_id_123"
        project_name = 12345
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=ValueError,
            project_id=project_id,
            name=project_name,
            expected_message="Project name must be a string."
        )

    def test_create_project_invalid_name_value_raises_validation_error(self):
        project_id = "test_project_id_123"
        project_name = " "
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=ValueError,
            project_id=project_id,
            name=project_name,
            expected_message="Project name cannot be empty."
        )

    def test_create_project_invalid_id_value_raises_validation_error(self):
        project_id = " "
        project_name = "Test Project"
        self.assert_error_behavior(
            func_to_call=create_project,
            expected_exception_type=ValueError,
            project_id=project_id,
            name=project_name,
            expected_message="Project ID cannot be empty."
        )
    
if __name__ == '__main__':
    unittest.main()