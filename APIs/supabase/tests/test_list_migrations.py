import unittest
import copy
from datetime import datetime, timezone

# CRITICAL IMPORT FOR CUSTOM ERRORS
from ..SimulationEngine import custom_errors
from ..database import list_migrations
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from pydantic import ValidationError as PydanticValidationError

class TestListMigrations(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        self.project1_id = "proj_with_migrations"
        self.project2_id = "proj_no_migrations_key" 
        self.project3_id = "proj_empty_migrations_list"
        self.project4_id = "proj_all_pending_no_applied_at"
        self.project_with_naive_datetime_id = "proj_with_naive_dt"

        self.non_existent_project_id = "proj_does_not_exist"

        self.dt_aware1 = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        self.dt_naive = datetime(2023, 1, 3, 12, 0, 0) 

        DB['projects'] = [
            {'id': self.project1_id, 'name': 'Project 1', 'organization_id': 'org1', 
             'region': 'us-east-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime(2023,1,1,1,0,0, tzinfo=timezone.utc)},
            {'id': self.project2_id, 'name': 'Project 2', 'organization_id': 'org1',
             'region': 'us-east-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime(2023,1,1,2,0,0, tzinfo=timezone.utc)},
            {'id': self.project3_id, 'name': 'Project 3', 'organization_id': 'org1',
             'region': 'us-east-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime(2023,1,1,3,0,0, tzinfo=timezone.utc)},
            {'id': self.project4_id, 'name': 'Project 4', 'organization_id': 'org1',
             'region': 'us-east-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime(2023,1,1,4,0,0, tzinfo=timezone.utc)},
            {'id': self.project_with_naive_datetime_id, 'name': 'Project Naive DT', 'organization_id': 'org1',
             'region': 'us-east-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime(2023,1,1,5,0,0, tzinfo=timezone.utc)},
        ]

        DB['migrations'] = {
            self.project1_id: [
                {'version': '20230101100000', 'name': 'Initial Schema', 'status': 'applied', 'applied_at': self.dt_aware1, 'query': 'CREATE TABLE...'},
                {'version': '20230102110000', 'name': 'Add Users Table', 'status': 'pending', 'applied_at': None, 'query': 'ALTER TABLE...'},
            ],
            self.project3_id: [], 
            self.project4_id: [
                 {'version': '20230201000000', 'name': 'Feature X - Step 1', 'status': 'pending', 'applied_at': None},
                 {'version': '20230202000000', 'name': 'Feature X - Step 2', 'status': 'failed', 'applied_at': None},
            ],
            self.project_with_naive_datetime_id: [
                {'version': '20230103120000', 'name': 'Naive DT Migration', 'status': 'applied', 'applied_at': self.dt_naive},
            ]
            # self.project2_id is intentionally missing as a key in DB['migrations']
        }

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def test_list_migrations_success_project_with_migrations(self):
        migrations = list_migrations(project_id=self.project1_id)
        self.assertEqual(len(migrations), 2)
        expected_migrations = [
            {'version': '20230101100000', 'name': 'Initial Schema', 'status': 'applied', 'applied_at': self.dt_aware1.isoformat()},
            {'version': '20230102110000', 'name': 'Add Users Table', 'status': 'pending', 'applied_at': None},
        ]
        self.assertEqual(migrations, expected_migrations)

    def test_list_migrations_success_with_naive_datetime_applied_at(self):
        migrations = list_migrations(project_id=self.project_with_naive_datetime_id)
        self.assertEqual(len(migrations), 1)
        expected_migration = {
            'version': '20230103120000', 
            'name': 'Naive DT Migration', 
            'status': 'applied', 
            'applied_at': self.dt_naive.isoformat()
        }
        self.assertEqual(migrations[0], expected_migration)

    def test_list_migrations_success_project_exists_no_migrations_key_in_db(self):
        migrations = list_migrations(project_id=self.project2_id)
        self.assertEqual(migrations, [])

    def test_list_migrations_success_project_exists_empty_migrations_list_in_db(self):
        migrations = list_migrations(project_id=self.project3_id)
        self.assertEqual(migrations, [])
        
    def test_list_migrations_success_project_all_migrations_no_applied_at(self):
        migrations = list_migrations(project_id=self.project4_id)
        self.assertEqual(len(migrations), 2)
        expected_migrations = [
            {'version': '20230201000000', 'name': 'Feature X - Step 1', 'status': 'pending', 'applied_at': None},
            {'version': '20230202000000', 'name': 'Feature X - Step 2', 'status': 'failed', 'applied_at': None},
        ]
        self.assertEqual(migrations, expected_migrations)

    def test_list_migrations_project_not_found_raises_notfounderror(self):
        self.assert_error_behavior(
            func_to_call=list_migrations,
            project_id=self.non_existent_project_id,
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Object not found." 
        )
        
    def test_list_migrations_project_not_found_when_projects_list_is_empty(self):
        DB['projects'] = [] 
        self.assert_error_behavior(
            func_to_call=list_migrations,
            project_id="any_project_id",
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Object not found." 
        )

    def test_list_migrations_invalid_project_id_type_int_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=list_migrations,
            project_id=123, 
            expected_exception_type=PydanticValidationError,
            expected_message="Project ID must be a string" 
        )

    def test_list_migrations_invalid_project_id_type_none_raises_validationerror(self):
        self.assert_error_behavior(
            func_to_call=list_migrations,
            project_id=None, 
            expected_exception_type=PydanticValidationError,
            expected_message="Project ID must be a string"
        )
        
    def test_list_migrations_empty_project_id_string_raises_notfounderror_if_not_exists(self):
        self.assert_error_behavior(
            func_to_call=list_migrations,
            project_id="",
            expected_exception_type=custom_errors.NotFoundError,
            expected_message="Object not found."
        )

    def test_list_migrations_success_if_db_migrations_main_key_is_missing(self):
        temp_project_id = "proj_temp_no_migrations_main_key"
        DB['projects'].append(
            {'id': temp_project_id, 'name': 'Temp Project', 'organization_id': 'org_temp', 
             'region': 'us-east-1', 'status': 'ACTIVE_HEALTHY', 'created_at': datetime(2023,1,1,6,0,0, tzinfo=timezone.utc)}
        )
        
        original_migrations_dict = None
        if 'migrations' in DB:
            original_migrations_dict = DB.pop('migrations')

        try:
            migrations = list_migrations(project_id=temp_project_id)
            self.assertEqual(migrations, [])
        finally:
            if original_migrations_dict is not None:
                 DB['migrations'] = original_migrations_dict
            # If 'migrations' was not in DB, tearDown will handle restoring the DB
            # to its state before setUp, which includes the 'migrations' dict
            # as initialized by setUp.

if __name__ == '__main__':
    unittest.main()