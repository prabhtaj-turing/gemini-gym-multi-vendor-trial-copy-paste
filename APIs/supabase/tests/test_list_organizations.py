import unittest
import copy
from datetime import datetime
from typing import Optional
from ..SimulationEngine.db import DB
from common_utils.base_case import BaseTestCaseWithErrorHandler
from ..organization import list_organizations
from ..SimulationEngine import models


class TestListOrganizations(BaseTestCaseWithErrorHandler):

    def setUp(self):
        self._original_DB_state = copy.deepcopy(DB)
        DB.clear()
        DB['organizations'] = []
        DB['projects'] = []
        DB['tables'] = {}
        DB['extensions'] = {}
        DB['migrations'] = {}
        DB['edge_functions'] = {}
        DB['branches'] = {}
        DB['costs'] = {}
        DB['unconfirmed_costs'] = {}
        DB['project_urls'] = {}
        DB['project_anon_keys'] = {}
        DB['project_ts_types'] = {}
        DB['logs'] = {}

    def tearDown(self):
        DB.clear()
        DB.update(self._original_DB_state)

    def _add_organization_to_db(self, org_id: str, name: str, created_at: Optional[datetime]=None) -> dict:
        """Helper to add an organization to the DB with required fields."""
        if created_at is None:
            created_at = datetime(2023, 1, 1, 0, 0, 0)
        org_data_dict = {'id': org_id, 'name': name, 'created_at': created_at.isoformat(), 'subscription_plan': {'id': 'plan_default', 'name': 'Default Plan', 'price': 0, 'currency': 'USD', 'features': []}}
        DB['organizations'].append(org_data_dict)
        return org_data_dict

    def test_list_organizations_empty_db_initially(self):
        """Test listing organizations when the 'organizations' list in DB is empty."""
        result = list_organizations()
        self.assertEqual(result, [], 'Should return an empty list if no organizations exist.')

    def test_list_organizations_no_organizations_key_in_db(self):
        """
        Test listing organizations if the 'organizations' key is entirely missing from DB.
        This tests robustness, assuming the function handles this by returning an empty list.
        """
        if 'organizations' in DB:
            del DB['organizations']
        result = list_organizations()
        self.assertEqual(result, [], "Should return an empty list if 'organizations' key is missing.")
        DB['organizations'] = []

    def test_list_organizations_single_organization(self):
        """Test listing organizations when there is a single organization in DB."""
        self._add_organization_to_db('org_single_test', 'Single Test Org', datetime(2023, 1, 1, 12, 0, 0))
        expected_output = [{'id': 'org_single_test', 'name': 'Single Test Org'}]
        result = list_organizations()
        self.assertEqual(len(result), 1, 'Should return one organization.')
        self.assertEqual(result, expected_output, 'The returned organization data is incorrect.')

    def test_list_organizations_multiple_organizations(self):
        """Test listing organizations when there are multiple organizations in DB."""
        self._add_organization_to_db('org_alpha', 'Alpha Corp', datetime(2023, 2, 1, 10, 0, 0))
        self._add_organization_to_db('org_beta', 'Beta Inc', datetime(2023, 2, 2, 11, 0, 0))
        self._add_organization_to_db('org_gamma', 'Gamma LLC', datetime(2023, 2, 3, 12, 0, 0))
        expected_output = [{'id': 'org_alpha', 'name': 'Alpha Corp'}, {'id': 'org_beta', 'name': 'Beta Inc'}, {'id': 'org_gamma', 'name': 'Gamma LLC'}]
        result = list_organizations()
        self.assertEqual(len(result), 3, 'Should return three organizations.')
        self.assertEqual(result, expected_output, 'The list of organizations or their order is incorrect.')

    def test_list_organizations_data_fields_and_types(self):
        """Test that returned organization data contains correct fields, types, and no extras."""
        self._add_organization_to_db('org_fields_check', 'Fields Check Org', datetime(2023, 3, 1, 10, 0, 0))
        result = list_organizations()
        self.assertEqual(len(result), 1, 'Should return one organization for this test.')
        org_item = result[0]
        self.assertIsInstance(org_item, dict, 'Each item in the list should be a dictionary.')
        self.assertIn('id', org_item, "Organization item must contain an 'id' key.")
        self.assertIn('name', org_item, "Organization item must contain a 'name' key.")
        self.assertEqual(len(org_item.keys()), 2, "Organization item should only contain 'id' and 'name' keys.")
        self.assertIsInstance(org_item['id'], str, 'Organization ID should be a string.')
        self.assertEqual(org_item['id'], 'org_fields_check')
        self.assertIsInstance(org_item['name'], str, 'Organization name should be a string.')
        self.assertEqual(org_item['name'], 'Fields Check Org')

    def test_list_organizations_with_special_characters_in_name(self):
        """Test listing an organization with various special characters in its name."""
        special_name = 'Org Corp & Co. !@#$%^*()_+`-={}|[]\\:";\'<>?,./ End'
        self._add_organization_to_db('org_special_chars', special_name, datetime(2023, 4, 1, 10, 0, 0))
        expected_output = [{'id': 'org_special_chars', 'name': special_name}]
        result = list_organizations()
        self.assertEqual(result, expected_output, 'Organization with special characters in name not handled correctly.')

    def test_list_organizations_db_state_unaffected_by_call(self):
        """Test that calling list_organizations does not modify the DB state."""
        org_data_1 = self._add_organization_to_db('org_immutable_1', 'Immutable Org One', datetime(2023, 5, 1, 10, 0, 0))
        org_data_2 = self._add_organization_to_db('org_immutable_2', 'Immutable Org Two', datetime(2023, 5, 2, 10, 0, 0))
        initial_db_organizations_state = copy.deepcopy(DB['organizations'])
        list_organizations()
        self.assertEqual(DB['organizations'], initial_db_organizations_state, "DB['organizations'] list reference or content should not be modified by list_organizations.")
        self.assertEqual(DB['organizations'][0], org_data_1, 'First organization data in DB was unexpectedly altered.')
        self.assertEqual(DB['organizations'][1], org_data_2, 'Second organization data in DB was unexpectedly altered.')

if __name__ == '__main__':
    unittest.main()