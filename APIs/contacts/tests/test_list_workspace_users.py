import unittest
import copy
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..SimulationEngine import custom_errors
from .. import list_workspace_users

class TestListWorkspaceUsers(BaseTestCaseWithErrorHandler):
    """
    Test suite for the list_workspace_users function.
    """

    def setUp(self):
        """
        Set up a clean database state for each test.
        """
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB.update({
            "myContacts": {
                "people/c123": {
                    "resourceName": "people/c123",
                    "names": [{"givenName": "Ignored", "familyName": "Contact"}],
                    "emailAddresses": [{"value": "ignored@example.com"}]
                }
            },
            "otherContacts": {},
            "directory": {
                "people/d001": {
                    "resourceName": "people/d001",
                    "etag": "etag1",
                    "isWorkspaceUser": True,
                    "names": [{"givenName": "Alex", "familyName": "Chen"}],
                    "emailAddresses": [{"value": "alex.chen@yourcompany.com", "primary": True}],
                    "organizations": [{"name": "YourCompany", "title": "Product Manager", "department": "Product", "primary": True}]
                },
                "people/d002": {
                    "resourceName": "people/d002",
                    "etag": "etag2",
                    "isWorkspaceUser": True,
                    "names": [{"givenName": "Maria", "familyName": "Garcia"}],
                    "emailAddresses": [{"value": "maria.garcia@yourcompany.com", "primary": True}],
                    "organizations": [{"name": "YourCompany", "title": "Lead Engineer", "department": "Engineering", "primary": True}],
                    "phoneNumbers": [{"value": "+1-555-1234", "type": "work"}]
                },
                "people/d003": {
                    "resourceName": "people/d003",
                    "etag": "etag3",
                    "isWorkspaceUser": True,
                    "names": [{"givenName": "Chen", "familyName": "Lee"}],
                    "emailAddresses": [{"value": "chen.lee@yourcompany.com", "primary": True}],
                    "organizations": [{"name": "YourCompany", "title": "Data Scientist", "department": "Engineering", "primary": True}]
                }
            }
        })

    def tearDown(self):
        """
        Restore the original database state after each test.
        """
        DB.clear()
        DB.update(self._original_DB_state)

    def test_list_all_users_default_limit(self):
        """
        Test listing all users with the default max_results.
        """
        result = list_workspace_users()
        self.assertIn('users', result)
        self.assertEqual(len(result['users']), 3)
        user_resource_names = {user['resourceName'] for user in result['users']}
        self.assertEqual(user_resource_names, {"people/d001", "people/d002", "people/d003"})

    def test_list_users_with_custom_max_results(self):
        """
        Test listing users with a specified max_results.
        """
        result = list_workspace_users(max_results=2)
        self.assertIn('users', result)
        self.assertEqual(len(result['users']), 2)

    def test_list_users_max_results_exceeds_total(self):
        """
        Test that listing users with max_results greater than the total number
        of users returns all users.
        """
        result = list_workspace_users(max_results=10)
        self.assertIn('users', result)
        self.assertEqual(len(result['users']), 3)

    def test_search_by_query_given_name(self):
        """
        Test searching for a user by their given name.
        """
        result = list_workspace_users(query="Maria")
        self.assertEqual(len(result['users']), 1)
        self.assertEqual(result['users'][0]['resourceName'], 'people/d002')

    def test_search_by_query_family_name_case_insensitive(self):
        """
        Test searching for a user by their family name with different casing.
        """
        result = list_workspace_users(query="garcia")
        self.assertEqual(len(result['users']), 1)
        self.assertEqual(result['users'][0]['resourceName'], 'people/d002')

    def test_search_by_query_email(self):
        """
        Test searching for a user by their email address.
        """
        result = list_workspace_users(query="alex.chen@yourcompany.com")
        self.assertEqual(len(result['users']), 1)
        self.assertEqual(result['users'][0]['resourceName'], 'people/d001')

    def test_search_by_query_phone_number(self):
        """
        Test searching for a user by their phone number.
        """
        result = list_workspace_users(query="555-1234")
        self.assertEqual(len(result['users']), 1)
        self.assertEqual(result['users'][0]['resourceName'], 'people/d002')

    def test_search_by_query_partial_name(self):
        """
        Test searching with a query that matches multiple users.
        """
        result = list_workspace_users(query="Chen")
        self.assertEqual(len(result['users']), 2)
        user_resource_names = {user['resourceName'] for user in result['users']}
        self.assertIn('people/d001', user_resource_names)
        self.assertIn('people/d003', user_resource_names)

    def test_search_by_query_with_max_results(self):
        """
        Test searching with a query and limiting the results.
        """
        result = list_workspace_users(query="Chen", max_results=1)
        self.assertEqual(len(result['users']), 1)

    def test_search_no_matches(self):
        """
        Test a search query that returns no results.
        """
        result = list_workspace_users(query="NonExistentName")
        self.assertEqual(len(result['users']), 0)

    def test_empty_directory(self):
        """
        Test listing users when the directory is empty.
        """
        DB['directory'].clear()
        result = list_workspace_users()
        self.assertEqual(len(result['users']), 0)

    def test_all_returned_users_are_workspace_users(self):
        """
        Test that the 'isWorkspaceUser' flag is always true in the results.
        """
        result = list_workspace_users()
        self.assertTrue(all(u.get('isWorkspaceUser') for u in result['users']))

    def test_invalid_max_results_type(self):
        """
        Test that a non-integer max_results raises a ValidationError.
        """
        self.assert_error_behavior(
            func_to_call=list_workspace_users,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="max_results must be an integer.",
            max_results="not a number"
        )

    def test_invalid_max_results_negative(self):
        """
        Test that a negative max_results raises a ValidationError.
        """
        self.assert_error_behavior(
            func_to_call=list_workspace_users,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="max_results must be a positive integer.",
            max_results=-10
        )

    def test_invalid_max_results_zero(self):
        """
        Test that a max_results of zero raises a ValidationError.
        """
        self.assert_error_behavior(
            func_to_call=list_workspace_users,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="max_results must be a positive integer.",
            max_results=0
        )

    def test_invalid_query_type(self):
        """
        Test that a non-string query raises a ValidationError.
        """
        self.assert_error_behavior(
            func_to_call=list_workspace_users,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="query must be a string.",
            query=12345
        )

if __name__ == '__main__':
    unittest.main()