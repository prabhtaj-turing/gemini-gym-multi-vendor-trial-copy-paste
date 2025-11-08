import unittest
import copy
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..SimulationEngine import custom_errors
from ..SimulationEngine.db import DB
from ..users import search_users
from unittest.mock import patch
from .. import users


class TestSearchUsers(BaseTestCaseWithErrorHandler):
    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()

        # More comprehensive data source for testing qualifiers
        self.users_data_source = [
            {'login': "alpha_user", 'id': 1, 'node_id': "N_1", 'type': "User", 'score': 1.0,
             'name': "Alpha Person", 'email': "alpha@example.com", 'location': "San Francisco",
             'followers': 100, 'public_repos': 10, 'created_at': "2020-01-01T00:00:00Z"},
            {'login': "beta_user", 'id': 2, 'node_id': "N_2", 'type': "User", 'score': 0.8,
             'name': "Beta Person", 'email': "beta@example.com", 'location': "New York",
             'followers': 200, 'public_repos': 5, 'created_at': "2021-01-01T00:00:00Z"},
            {'login': "gamma_user_common", 'id': 3, 'node_id': "N_3", 'type': "User", 'score': 0.9,
             'name': "Gamma Something", 'email': "gamma@example.com", 'location': "San Francisco",
             'followers': 50, 'public_repos': 20, 'created_at': "2019-01-01T00:00:00Z"},
            {'login': "delta_another_common", 'id': 4, 'node_id': "N_4", 'type': "User", 'score': 0.7,
             'name': "Delta Person", 'email': "delta@example.com", 'location': "London",
             'followers': 150, 'public_repos': 15, 'created_at': "2022-01-01T00:00:00Z"},
            {'login': "user_zeta", 'id': 5, 'node_id': "N_5", 'type': "User", 'score': 0.5,
             'name': "Zeta Person", 'email': "zeta@example.com", 'location': "Tokyo",
             'followers': 10, 'public_repos': 1, 'created_at': "2023-01-01T00:00:00Z"},
            {'login': "common_epsilon", 'id': 6, 'node_id': "N_6", 'type': "User", 'score': 0.6,
             'name': "Epsilon Guy", 'email': "epsilon@example.com", 'location': "New York",
             'followers': 20, 'public_repos': 2, 'created_at': "2022-06-01T00:00:00Z"},
            {'login': "unique_string", 'id': 7, 'node_id': "N_7", 'type': "User", 'score': 0.4,
             'name': "Unique Human", 'email': "unique@example.com", 'location': "Paris",
             'followers': 5, 'public_repos': 25, 'created_at': "2018-01-01T00:00:00Z"},
            {'login': "GitHub", 'id': 8, 'node_id': "N_8", 'type': "Organization", 'score': 1.0,
             'name': "The GitHub Org", 'email': "org@github.com", 'location': "San Francisco",
             'followers': 9000, 'public_repos': 50, 'created_at': "2008-01-01T00:00:00Z"}
        ]
        DB['Users'] = copy.deepcopy(self.users_data_source)

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _assert_user_item_structure(self, item):
        self.assertIn('login', item)
        self.assertIsInstance(item['login'], str)
        self.assertIn('id', item)
        self.assertIsInstance(item['id'], int)
        self.assertIn('node_id', item)
        self.assertIsInstance(item['node_id'], str)
        self.assertIn('type', item)
        self.assertIsInstance(item['type'], str)
        self.assertIn('score', item)
        self.assertIsInstance(item['score'], (float, int))

    # --- Basic Search and 'in' Qualifier Tests ---

    def test_search_basic_term(self):
        # Searches 'user' in login/name/email. Default sort by score desc.
        results = search_users(q="user")
        self.assertEqual(results['total_count'], 4)
        logins = [item['login'] for item in results['items']]
        self.assertEqual(logins, ["alpha_user", "gamma_user_common", "beta_user", "user_zeta"])

    def test_search_term_in_name(self):
        results = search_users(q="Person")
        self.assertEqual(results['total_count'], 4)
        logins = [item['login'] for item in results['items']]
        self.assertEqual(logins, ["alpha_user", "beta_user", "delta_another_common", "user_zeta"])

    def test_qualifier_in_login(self):
        results = search_users(q="user in:login")
        self.assertEqual(results['total_count'], 4)
        logins = [item['login'] for item in results['items']]
        self.assertEqual(logins, ["alpha_user", "gamma_user_common", "beta_user", "user_zeta"])

    def test_qualifier_in_name(self):
        results = search_users(q="Person in:name")
        self.assertEqual(results['total_count'], 4)
        logins = [item['login'] for item in results['items']]
        self.assertEqual(logins, ["alpha_user", "beta_user", "delta_another_common", "user_zeta"])

    def test_qualifier_in_email(self):
        results = search_users(q="beta in:email")
        self.assertEqual(results['total_count'], 1)
        self.assertEqual(results['items'][0]['login'], 'beta_user')

    def test_qualifier_in_name_and_email(self):
        results = search_users(q="alpha in:name,email")
        self.assertEqual(results['total_count'], 1)
        self.assertEqual(results['items'][0]['login'], 'alpha_user')

    def test_search_case_insensitive(self):
        results = search_users(q="ALPHA in:name")
        self.assertEqual(results['total_count'], 1)
        self.assertEqual(results['items'][0]['login'], 'alpha_user')

    def test_search_no_matches(self):
        results = search_users(q="nonexistentquery")
        self.assertEqual(results['total_count'], 0)
        self.assertEqual(len(results['items']), 0)

    def test_search_db_no_users_key(self):
        DB.pop('Users', None)
        results = search_users(q="user")
        self.assertEqual(results['total_count'], 0)

    # --- Qualifier Tests ---

    def test_qualifier_repos_greater_than(self):
        results = search_users(q="repos:>15")
        logins = {item['login'] for item in results['items']}
        self.assertEqual(results['total_count'], 3)
        self.assertEqual(logins, {"gamma_user_common", "unique_string", "GitHub"})

    def test_qualifier_repos_greater_than_or_equal(self):
        results = search_users(q="repos:>=15")
        logins = {item['login'] for item in results['items']}
        self.assertEqual(results['total_count'], 4)
        self.assertEqual(logins, {"gamma_user_common", "delta_another_common", "unique_string", "GitHub"})

    def test_qualifier_repos_range(self):
        results = search_users(q="repos:5..15")
        logins = {item['login'] for item in results['items']}
        self.assertEqual(results['total_count'], 3)
        self.assertEqual(logins, {"beta_user", "alpha_user", "delta_another_common"})

    def test_qualifier_followers_less_than_equal(self):
        results = search_users(q="followers:<=20")
        logins = {item['login'] for item in results['items']}
        self.assertEqual(results['total_count'], 3)
        self.assertEqual(logins, {"user_zeta", "common_epsilon", "unique_string"})

    def test_qualifier_location(self):
        results = search_users(q='location:"San Francisco"')
        logins = {item['login'] for item in results['items']}
        self.assertEqual(results['total_count'], 3)
        self.assertEqual(logins, {"alpha_user", "gamma_user_common", "GitHub"})

    def test_qualifier_type_organization(self):
        results = search_users(q="type:Organization")
        self.assertEqual(results['total_count'], 1)
        self.assertEqual(results['items'][0]['login'], "GitHub")

    def test_qualifier_created_date_range(self):
        results = search_users(q="created:2020-01-01..2021-12-31")
        logins = {item['login'] for item in results['items']}
        self.assertEqual(results['total_count'], 2)
        self.assertEqual(logins, {"alpha_user", "beta_user"})
    
    def test_qualifier_created_before(self):
        results = search_users(q="created:<2010-01-01")
        self.assertEqual(results['total_count'], 1)
        self.assertEqual(results['items'][0]['login'], "GitHub")

    def test_qualifier_created_after(self):
        results = search_users(q="created:>2022-01-01")
        logins = {item['login'] for item in results['items']}
        self.assertEqual(results['total_count'], 3)
        self.assertEqual(logins, {"delta_another_common", "user_zeta", "common_epsilon"})

    def test_qualifier_created_exact_date(self):
        results = search_users(q="created:2022-01-01")
        self.assertEqual(results['total_count'], 1)
        self.assertEqual(results['items'][0]['login'], "delta_another_common")

    def test_combined_qualifiers_with_term(self):
        # Search for a user with 'delta' in their name, in London, with more than 10 repos
        results = search_users(q="delta in:name location:London repos:>10")
        self.assertEqual(results['total_count'], 1)
        self.assertEqual(results['items'][0]['login'], "delta_another_common")

    def test_complex_query_multiple_qualifiers(self):
        # A complex query that combines multiple qualifiers to find a specific user
        query = (
            'gamma in:login location:"San Francisco" repos:>=20 '
            'followers:50..100 created:>=2019-01-01'
        )
        results = search_users(q=query)
        self.assertEqual(results['total_count'], 1)
        self.assertEqual(results['items'][0]['login'], "gamma_user_common")

    # --- Sorting Tests ---

    def test_sort_default_by_score(self):
        results = search_users(q="user") # Matches alpha, beta, gamma, zeta
        logins = [item['login'] for item in results['items']]
        expected = ["alpha_user", "gamma_user_common", "beta_user", "user_zeta"]
        self.assertEqual(logins, expected)

    def test_sort_followers_asc(self):
        results = search_users(q="user", sort="followers", order="asc")
        logins = [item['login'] for item in results['items']]
        expected = ["user_zeta", "gamma_user_common", "alpha_user", "beta_user"]
        self.assertEqual(logins, expected)

    def test_sort_repositories_desc(self):
        results = search_users(q="user", sort="repositories", order="desc")
        logins = [item['login'] for item in results['items']]
        expected = ["gamma_user_common", "alpha_user", "beta_user", "user_zeta"]
        self.assertEqual(logins, expected)

    def test_sort_joined_desc(self):
        results = search_users(q="user", sort="joined", order="desc")
        logins = [item['login'] for item in results['items']]
        expected = ["user_zeta", "beta_user", "alpha_user", "gamma_user_common"]
        self.assertEqual(logins, expected)

    def test_sort_with_order_none_defaults_to_desc(self):
        results = search_users(q="user", sort="followers") 
        logins = [item['login'] for item in results['items']]
        expected_desc = ["beta_user", "alpha_user", "gamma_user_common", "user_zeta"]
        self.assertEqual(logins, expected_desc)

    # --- Pagination Tests ---

    def test_pagination_first_page_per_page_2(self):
        results = search_users(q="user", page=1, per_page=2) # Default sort: alpha, gamma, beta, zeta
        self.assertEqual(results['total_count'], 4)
        self.assertEqual(len(results['items']), 2)
        self.assertEqual(results['items'][0]['login'], "alpha_user")
        self.assertEqual(results['items'][1]['login'], "gamma_user_common")

    def test_pagination_second_page_per_page_2(self):
        results = search_users(q="user", page=2, per_page=2)
        self.assertEqual(results['total_count'], 4)
        self.assertEqual(len(results['items']), 2)
        self.assertEqual(results['items'][0]['login'], "beta_user")
        self.assertEqual(results['items'][1]['login'], "user_zeta")

    def test_pagination_page_exceeds_results(self):
        results = search_users(q="user", page=3, per_page=2)
        self.assertEqual(results['total_count'], 4)
        self.assertEqual(len(results['items']), 0)

    def test_pagination_per_page_partial_last_page(self):
        results = search_users(q="common", page=2, per_page=2) # Matches gamma, delta, epsilon -> sorted: gamma, delta, epsilon
        self.assertEqual(results['total_count'], 3)
        self.assertEqual(len(results['items']), 1)
        self.assertEqual(results['items'][0]['login'], "common_epsilon")
    
    def test_pagination_per_page_max_value_allowed(self):
        results = search_users(q="user", per_page=100) 
        self.assertEqual(results['total_count'], 4)
        self.assertEqual(len(results['items']), 4)

    # --- Validation and Error Tests ---

    def test_validation_empty_query_error(self):
        self.assert_error_behavior(func_to_call=search_users, q="", expected_exception_type=custom_errors.InvalidInputError, expected_message="Search query 'q' cannot be empty.")


    def test_validation_invalid_sort_field_error(self):
        self.assert_error_behavior(func_to_call=search_users, q="user", sort="nonexistent_field", expected_exception_type=custom_errors.InvalidInputError, expected_message="Invalid 'sort' parameter. Must be one of ['followers', 'repositories', 'joined'].")

    def test_validation_invalid_order_value_error(self):
        self.assert_error_behavior(func_to_call=search_users, q="user", sort="followers", order="sideways", expected_exception_type=custom_errors.InvalidInputError, expected_message="Invalid 'order' parameter. Must be 'asc' or 'desc'.")

    def test_validation_invalid_page_zero(self):
        self.assert_error_behavior(func_to_call=search_users, q="user", page=0, per_page=10, expected_exception_type=custom_errors.InvalidInputError, expected_message="Page number must be a positive integer.")

    def test_validation_invalid_per_page_zero(self):
        self.assert_error_behavior(func_to_call=search_users, q="user", page=1, per_page=0, expected_exception_type=custom_errors.InvalidInputError, expected_message="Results per page must be a positive integer.")
    
    def test_validation_per_page_too_high(self):
        self.assert_error_behavior(func_to_call=search_users, q="user", page=1, per_page=101, expected_exception_type=custom_errors.InvalidInputError, expected_message="Maximum 'per_page' is 100.")

    def test_search_users_mismatched_quotes(self):
        """
        Test that search_users raises InvalidInputError for queries with mismatched quotes.
        """
        self.assert_error_behavior(func_to_call=search_users, q='location:"San Francisco', expected_exception_type=custom_errors.InvalidInputError, expected_message="Invalid query syntax: Mismatched quotes.")

    def test_search_with_multiple_terms_is_and_logic(self):
        """Test that multiple search terms are treated with AND logic."""
        # Search for "Alpha" and "Person" - should only match alpha_user
        results = search_users(q="Alpha Person")
        self.assertEqual(results['total_count'], 1)
        self.assertEqual(results['items'][0]['login'], 'alpha_user')

        # Search for "beta" and "York" - should only match beta_user in New York
        results = search_users(q="beta York")
        self.assertEqual(results['total_count'], 1)
        self.assertEqual(results['items'][0]['login'], 'beta_user')
        
        # Search for terms that do not co-exist in any single item
        results = search_users(q="Alpha Beta")
        self.assertEqual(results['total_count'], 0)

if __name__ == '__main__':
    unittest.main()