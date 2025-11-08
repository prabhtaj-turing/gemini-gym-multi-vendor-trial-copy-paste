"""Test cases for Supabase organization-related functions."""
import unittest
import copy
from typing import Dict, Any, List

from ..SimulationEngine.db import DB
from ..SimulationEngine import custom_errors
from ..organization import get_organization
from common_utils.base_case import BaseTestCaseWithErrorHandler


# Initial database state for get_organization tests
GET_ORGANIZATION_INITIAL_DB_STATE = {
    "organizations": [  # This key must be present in the database for the test to pass 
        {
            "id": "org_abc123",
            "name": "Acme Corp",
            "created_at": "2023-01-15T10:00:00Z",
            "plan": "pro",
            "opt_in_tags": ["AI_SQL_GENERATOR_OPT_IN", "AI_DATA_GENERATOR_OPT_IN", "AI_LOG_GENERATOR_OPT_IN"],
            "allowed_release_channels": ["internal", "alpha", "beta", "ga", "withdrawn", "preview"]
        },
        {
            "id": "org_xyz789",
            "name": "Innovate Solutions",
            "created_at": "2022-05-20T14:30:00Z",
            "plan": "free",
            "opt_in_tags": ["AI_SQL_GENERATOR_OPT_IN", "AI_DATA_GENERATOR_OPT_IN", "AI_LOG_GENERATOR_OPT_IN"],
            "allowed_release_channels": ["internal", "alpha", "beta", "ga", "withdrawn", "preview"]
           
        },
        {
            "id": "org_special123",
            "name": "Test & Special-Chars Inc!",
            "created_at": "2023-06-10T08:45:00Z",
            "plan": "enterprise",   
            "opt_in_tags": ["AI_SQL_GENERATOR_OPT_IN", "AI_DATA_GENERATOR_OPT_IN", "AI_LOG_GENERATOR_OPT_IN"],
            "allowed_release_channels": ["internal", "alpha", "beta", "ga", "withdrawn", "preview"]
        }
        
    ],
    "projects": [],
    "tables": {},
    "extensions": {},
    "migrations": {},
    "edge_functions": {},
    "branches": {},
    "costs": {},
    "unconfirmed_costs": {},
    "project_urls": {},
    "project_anon_keys": {},
    "project_ts_types": {},
    "logs": {}
}


class TestGetOrganization(BaseTestCaseWithErrorHandler):
    """Test suite for the get_organization function."""

    @classmethod
    def setUpClass(cls):
        """Save original DB state and set up initial test state."""
        cls.original_db_state = copy.deepcopy(DB)
        DB.clear()
        DB.update(copy.deepcopy(GET_ORGANIZATION_INITIAL_DB_STATE))

    @classmethod
    def tearDownClass(cls):
        """Restore original DB state."""
        DB.clear()
        DB.update(cls.original_db_state)

    def test_get_organization_success_pro_plan(self):
        """Test successful retrieval of organization with Pro plan."""
        org_info = get_organization(id='org_abc123')
        expected = {
            'id': 'org_abc123',
            'name': 'Acme Corp',
            'created_at': '2023-01-15T10:00:00Z',
            'plan': 'pro',
            'opt_in_tags': ['AI_SQL_GENERATOR_OPT_IN', 'AI_DATA_GENERATOR_OPT_IN', 'AI_LOG_GENERATOR_OPT_IN'],
            'allowed_release_channels': ['internal', 'alpha', 'beta', 'ga', 'withdrawn', 'preview']
        }
        self.assertEqual(org_info, expected)

    def test_get_organization_success_free_tier(self):
        """Test successful retrieval of organization with Free tier."""
        org_info = get_organization(id='org_xyz789')
        expected = {
            'id': 'org_xyz789',
            'name': 'Innovate Solutions',
            'created_at': '2022-05-20T14:30:00Z',
            'plan': 'free',
            'opt_in_tags': ['AI_SQL_GENERATOR_OPT_IN', 'AI_DATA_GENERATOR_OPT_IN', 'AI_LOG_GENERATOR_OPT_IN'],
            'allowed_release_channels': ['internal', 'alpha', 'beta', 'ga', 'withdrawn', 'preview']
        }
        self.assertEqual(org_info, expected)

    def test_get_organization_special_chars_in_name(self):
        """Test organization name with special characters converts to proper name."""
        org_info = get_organization(id='org_special123')
        self.assertEqual(org_info['name'], 'Test & Special-Chars Inc!')
        
    def test_get_organization_not_found(self):
        """Test error when organization ID does not exist."""
        self.assert_error_behavior(
            get_organization,
            custom_errors.NotFoundError,
            'No organization found against this id: org_nonexistent',
            id='org_nonexistent'
        )

    def test_get_organization_empty_id(self):
        """Test error when ID is empty string."""
        self.assert_error_behavior(
            get_organization,
            custom_errors.ValidationError,
            'The id parameter can not be null or empty',
            id=''
        )

    def test_get_organization_none_id(self):
        """Test error when ID is None."""
        self.assert_error_behavior(
            get_organization,
            custom_errors.ValidationError,
            'The id parameter can not be null or empty',
            id=None
        )

    def test_get_organization_non_string_id(self):
        """Test error when ID is not a string."""
        self.assert_error_behavior(
            get_organization,
            custom_errors.ValidationError,
            'id must be string type',
            id=123
        )

    def test_get_organization_list_id(self):
        """Test error when ID is a list."""
        self.assert_error_behavior(
            get_organization,
            custom_errors.ValidationError,
            'id must be string type',
            id=['org_abc123']
        )

    def test_get_organization_dict_id(self):
        """Test error when ID is a dictionary."""
        self.assert_error_behavior(
            get_organization,
            custom_errors.ValidationError,
            'id must be string type',
            id={'id': 'org_abc123'}
        )

    def test_get_organization_response_structure(self):
        """Test that response matches expected structure with all required fields."""
        org_info = get_organization(id='org_abc123')
        
        # Check top-level keys
        required_keys = {'id', 'name', 'created_at', 'plan', 'opt_in_tags', 'allowed_release_channels'}
        self.assertEqual(set(org_info.keys()), required_keys)
        
        
        # Check data types
        self.assertIsInstance(org_info['id'], str)
        self.assertIsInstance(org_info['name'], str)
        self.assertIsInstance(org_info['created_at'], str)
        self.assertIsInstance(org_info['plan'], str)
        
    def test_get_organization_enterprise_plan(self):
        """Test organization with enterprise plan and complex features."""
        org_info = get_organization(id='org_special123')
        
        # Verify enterprise plan details
        self.assertEqual(org_info['plan'], 'enterprise')
        self.assertEqual(type(org_info['opt_in_tags']), list)
        self.assertEqual(type(org_info['allowed_release_channels']), list)

    def test_get_organization_iso_timestamp_format(self):
        """Test that created_at field is in ISO 8601 format."""
        org_info = get_organization(id='org_abc123')
        created_at = org_info['created_at']
        
        # Should match ISO 8601 format with 'Z' timezone
        self.assertTrue(created_at.endswith('Z'))
        self.assertIn('T', created_at)
        self.assertEqual(len(created_at), 20)  # YYYY-MM-DDTHH:MM:SSZ

    def test_get_organization_float_price_precision(self):
        """Test that price maintains proper decimal precision."""
        org_info = get_organization(id='org_xyz789')
        self.assertEqual(org_info['plan'], 'free')
        
        org_info2 = get_organization(id='org_special123')
        self.assertEqual(org_info2['plan'], 'enterprise')


if __name__ == '__main__':
    unittest.main()