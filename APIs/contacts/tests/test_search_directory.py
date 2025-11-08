import unittest
import copy
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine.db import DB
from ..SimulationEngine import custom_errors
from .. import search_directory

class TestSearchDirectory(BaseTestCaseWithErrorHandler):
    """
    Test suite for the search_directory function.
    """

    def setUp(self):
        """
        Set up a clean database state for each test.
        """
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        
        # Populate the DB with test data for the directory
        self.directory_data = {
            "people/d11223344556677889": {
                "resourceName": "people/d11223344556677889",
                "etag": "etag_alex",
                "names": [{"givenName": "Alex", "familyName": "Chen"}],
                "emailAddresses": [{"value": "alex.chen@yourcompany.com", "primary": True}],
                "organizations": [{"name": "YourCompany", "title": "Product Manager", "department": "Product", "primary": True}],
                "isWorkspaceUser": True
            },
            "people/d98765432101234567": {
                "resourceName": "people/d98765432101234567",
                "etag": "etag_maria",
                "names": [{"givenName": "Maria", "familyName": "Garcia"}],
                "emailAddresses": [{"value": "maria.garcia@yourcompany.com", "primary": True}],
                "phoneNumbers": [{"value": "+1-555-0101", "type": "work"}],
                "organizations": [{"name": "YourCompany", "title": "Lead Engineer", "department": "Engineering", "primary": True}],
                "isWorkspaceUser": True
            },
            "people/d55566677788899900": {
                "resourceName": "people/d55566677788899900",
                "etag": "etag_sam_engineer",
                "names": [{"givenName": "Sam", "familyName": "Taylor"}],
                "emailAddresses": [{"value": "sam.taylor@yourcompany.com", "primary": True}],
                "organizations": [{"name": "YourCompany", "title": "Data Analyst", "department": "Engineering", "primary": True}],
                "isWorkspaceUser": True
            }
        }
        DB['directory'] = self.directory_data
        DB['myContacts'] = {}
        DB['otherContacts'] = {}

    def tearDown(self):
        """
        Restore the original database state after each test.
        """
        DB.clear()
        DB.update(self._original_DB_state)

    def _add_bulk_users(self, count):
        """Helper to add many users for pagination tests."""
        for i in range(count):
            user_id = f"people/bulkuser{i}"
            DB['directory'][user_id] = {
                "resourceName": user_id,
                "etag": f"etag_bulk_{i}",
                "names": [{"givenName": "Bulk", "familyName": f"User{i}"}],
                "emailAddresses": [{"value": f"bulk.user.{i}@yourcompany.com", "primary": True}],
                "organizations": [{"name": "YourCompany", "title": "Staff", "department": "BulkDept", "primary": True}],
                "isWorkspaceUser": True
            }

    def test_search_by_full_name(self):
        """Test searching by a full name query."""
        results = search_directory(query="Alex Chen")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['resourceName'], "people/d11223344556677889")

    def test_search_by_first_name_case_insensitive(self):
        """Test searching by a case-insensitive first name."""
        results = search_directory(query="alex")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['names'][0]['givenName'], "Alex")

    def test_search_by_last_name(self):
        """Test searching by a last name."""
        results = search_directory(query="Garcia")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['resourceName'], "people/d98765432101234567")

    def test_search_by_email(self):
        """Test searching by a full email address."""
        results = search_directory(query="maria.garcia@yourcompany.com")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['resourceName'], "people/d98765432101234567")

    def test_search_by_partial_email(self):
        """Test searching by a common part of an email address."""
        results = search_directory(query="yourcompany.com")
        self.assertEqual(len(results), 3)
        resource_names = {r['resourceName'] for r in results}
        self.assertIn("people/d11223344556677889", resource_names)
        self.assertIn("people/d98765432101234567", resource_names)
        self.assertIn("people/d55566677788899900", resource_names)

    def test_search_by_phone_number(self):
        """Test searching by a phone number."""
        results = search_directory(query="+1-555-0101")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['resourceName'], "people/d98765432101234567")

    def test_search_with_max_results_limit(self):
        """Test that max_results correctly limits the number of returned items."""
        results = search_directory(query="yourcompany.com", max_results=2)
        self.assertEqual(len(results), 2)

    def test_search_with_max_results_no_effect(self):
        """Test that max_results doesn't affect results if it's larger than the match count."""
        results = search_directory(query="Alex", max_results=10)
        self.assertEqual(len(results), 1)

    def test_search_no_results_found(self):
        """Test a query that should return no results."""
        results = search_directory(query="nonexistent.user")
        self.assertEqual(len(results), 0)
        self.assertIsInstance(results, list)

    def test_search_unsearchable_field(self):
        """Test searching by a field that is not indexed (e.g., department)."""
        results = search_directory(query="Products")
        self.assertEqual(len(results), 0)

    def test_search_default_max_results(self):
        """Test the default max_results limit of 20."""
        self._add_bulk_users(25) # Total users = 3 + 25 = 28
        results = search_directory(query="yourcompany.com")
        self.assertEqual(len(results), 20)

    def test_search_invalid_query_type_raises_error(self):
        """Test that a non-string query raises a ValidationError."""
        self.assert_error_behavior(
            func_to_call=search_directory,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The 'query' argument must be a non-empty string.",
            query=12345
        )

    def test_search_empty_query_string_raises_error(self):
        """Test that an empty query string raises a custom ValidationError."""
        self.assert_error_behavior(
            func_to_call=search_directory,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The 'query' argument must be a non-empty string.",
            query=""
        )

    def test_search_invalid_max_results_type_raises_error(self):
        """Test that a non-integer max_results raises a ValidationError."""
        self.assert_error_behavior(
            func_to_call=search_directory,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The 'max_results' argument must be a positive integer.",
            query="test",
            max_results="five"
        )
    
    def test_search_negative_max_results_raises_error(self):
        """Test that a negative max_results value raises a custom ValidationError."""
        self.assert_error_behavior(
            func_to_call=search_directory,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The 'max_results' argument must be a positive integer.",
            query="test",
            max_results=-1
        )

    def test_search_zero_max_results_raises_error(self):
        """Test that a max_results value of zero raises a custom ValidationError."""
        self.assert_error_behavior(
            func_to_call=search_directory,
            expected_exception_type=custom_errors.ValidationError,
            expected_message="The 'max_results' argument must be a positive integer.",
            query="test",
            max_results=0
        )

if __name__ == '__main__':
    unittest.main()