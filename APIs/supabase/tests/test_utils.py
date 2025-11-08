import unittest
import copy
from datetime import datetime, timezone
from unittest.mock import patch

from ..SimulationEngine.utils import (
    add_cost_information_to_project,
    create_new_organization,
    get_entity_by_id_from_db,
    generate_unique_id,
    get_cost_parameter,
    update_cost_parameter,
    DB_COST_DEFAULTS,
    name_to_slug,
    get_projects_for_organization,
    update_project_status_and_cascade,
    is_branching_enabled_for_project,
    get_project_postgres_version,
    get_branch_by_id_from_db,
    find_branch_in_db,
)
from ..SimulationEngine.db import DB
from ..SimulationEngine import models
from common_utils.base_case import BaseTestCaseWithErrorHandler


class TestAddCostInformationToProject(BaseTestCaseWithErrorHandler):
    """Test cases for add_cost_information_to_project utility function."""

    @classmethod
    def setUpClass(cls):
        """Set up test data before each test class."""
        cls._original_DB_state = copy.deepcopy(DB)

    def setUp(self):
        """Reset DB state before each test."""
        DB.clear()
        DB.update({
            "organizations": [],
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
        })

        # Add test organizations
        DB['organizations'].append({
            'id': 'org_123',
            'name': 'Test Organization',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'plan': 'free',
            'opt_in_tags': [],
            'allowed_release_channels': []
        })

        # Add test projects
        DB['projects'].append({
            'id': 'proj_1a2b3c',
            'name': 'Test Project 1',
            'organization_id': 'org_123',
            'region': 'us-east-1',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'version': 'PostgreSQL 15'
        })

        DB['projects'].append({
            'id': 'proj_4d5e6f',
            'name': 'Test Project 2',
            'organization_id': 'org_123',
            'region': 'eu-west-1',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'version': 'PostgreSQL 14'
        })

        # Validate DB structure after setup
        self._validate_db_structure()

    def _validate_db_structure(self):
        """Validate that the DB structure conforms to SupabaseDB model."""
        try:
            # Use the actual SupabaseDB model for validation
            supabase_db = models.SupabaseDB(**DB)
            
        except Exception as e:
            raise AssertionError(f"DB structure validation failed using SupabaseDB model: {str(e)}")

    @classmethod
    def tearDownClass(cls):
        """Clean up after each test class."""
        DB.clear()
        DB.update(cls._original_DB_state)

    def test_add_cost_information_success_with_defaults(self):
        """Test adding cost information with default values."""
        project_id = 'proj_1a2b3c'
        
        result = add_cost_information_to_project(DB, project_id)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['type'], 'project')
        self.assertEqual(result['amount'], 10.0)  # Default from DB_COST_DEFAULTS
        self.assertEqual(result['currency'], 'USD')  # Default from DB_COST_DEFAULTS
        self.assertEqual(result['recurrence'], 'monthly')
        self.assertIn('confirmation_id', result)
        self.assertTrue(result['confirmation_id'].startswith('cost_'))
        self.assertIn('description', result)
        self.assertIn('Test Project 1', result['description'])
        
        # Verify cost was added to DB
        self.assertIn(result['confirmation_id'], DB['costs'])
        self.assertEqual(DB['costs'][result['confirmation_id']], result)

    def test_add_cost_information_success_with_custom_values(self):
        """Test adding cost information with custom values."""
        project_id = 'proj_4d5e6f'
        custom_amount = 25.50
        custom_currency = 'EUR'
        custom_recurrence = 'hourly'
        custom_description = 'Custom cost description'
        
        result = add_cost_information_to_project(
            DB, project_id,
            amount=custom_amount,
            currency=custom_currency,
            recurrence=custom_recurrence,
            description=custom_description
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['amount'], custom_amount)
        self.assertEqual(result['currency'], custom_currency)
        self.assertEqual(result['recurrence'], custom_recurrence)
        self.assertEqual(result['description'], custom_description)
        self.assertEqual(result['type'], 'project')

    def test_add_cost_information_branch_type(self):
        """Test adding cost information for branch type."""
        project_id = 'proj_1a2b3c'
        
        result = add_cost_information_to_project(
            DB, project_id,
            cost_type='branch',
            amount=5.0,
            description='Branch cost'
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['type'], 'branch')
        self.assertEqual(result['amount'], 5.0)
        self.assertIn('Branch cost', result['description'])

    def test_add_cost_information_project_not_found(self):
        """Test adding cost information to non-existent project."""
        non_existent_project_id = 'proj_nonexistent'
        
        result = add_cost_information_to_project(DB, non_existent_project_id)
        
        self.assertIsNone(result)

    def test_add_cost_information_multiple_costs_same_project(self):
        """Test adding multiple costs to the same project."""
        project_id = 'proj_1a2b3c'
        
        # Add first cost
        result1 = add_cost_information_to_project(
            DB, project_id,
            amount=10.0,
            description='First cost'
        )
        
        # Add second cost
        result2 = add_cost_information_to_project(
            DB, project_id,
            amount=20.0,
            description='Second cost'
        )
        
        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)
        self.assertNotEqual(result1['confirmation_id'], result2['confirmation_id'])
        self.assertEqual(len(DB['costs']), 2)

    def test_add_cost_information_with_none_values(self):
        """Test adding cost information with None values (should use defaults)."""
        project_id = 'proj_1a2b3c'
        
        result = add_cost_information_to_project(
            DB, project_id,
            amount=None,
            currency=None,
            description=None
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result['amount'], 10.0)  # Default
        self.assertEqual(result['currency'], 'USD')  # Default
        self.assertIn('Test Project 1', result['description'])  # Generated description

    def test_add_cost_information_empty_db_costs(self):
        """Test adding cost information when DB has no costs section."""
        project_id = 'proj_1a2b3c'
        DB.pop('costs', None)  # Remove costs section
        
        result = add_cost_information_to_project(DB, project_id)
        
        self.assertIsNotNone(result)
        self.assertIn('costs', DB)
        self.assertIn(result['confirmation_id'], DB['costs'])


class TestCreateNewOrganization(BaseTestCaseWithErrorHandler):
    """Test cases for create_new_organization utility function."""

    @classmethod
    def setUpClass(cls):
        """Set up test data before each test class."""
        cls._original_DB_state = copy.deepcopy(DB)

    def setUp(self):
        """Reset DB state before each test."""
        DB.clear()
        DB.update({
            "organizations": [],
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
        })

        # Add existing organization
        DB['organizations'].append({
            'id': 'org_existing',
            'name': 'Existing Organization',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'plan': 'free',
            'opt_in_tags': [],
            'allowed_release_channels': []
        })

        # Validate DB structure after setup
        self._validate_db_structure()

    def _validate_db_structure(self):
        """Validate that the DB structure conforms to SupabaseDB model."""
        try:
            # Use the actual SupabaseDB model for validation
            supabase_db = models.SupabaseDB(**DB)
            
        except Exception as e:
            raise AssertionError(f"DB structure validation failed using SupabaseDB model: {str(e)}")

    @classmethod
    def tearDownClass(cls):
        """Clean up after each test class."""
        DB.clear()
        DB.update(cls._original_DB_state)

    def test_create_new_organization_success_with_defaults(self):
        """Test creating organization with default subscription plan."""
        org_name = 'New Test Organization'
        
        result = create_new_organization(DB, org_name)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertIn('id', result)
        self.assertTrue(result['id'].startswith('org_'))
        self.assertEqual(result['name'], org_name)
        self.assertIn('created_at', result)
        self.assertIn('plan', result)
        
        # Check default subscription plan
        subscription = result['plan']
        self.assertEqual(subscription, 'free')
        
        # Verify organization was added to DB
        self.assertEqual(len(DB['organizations']), 2)  # Original + new
        db_org = get_entity_by_id_from_db(DB, 'organizations', result['id'])
        self.assertEqual(db_org, result)

    def test_create_new_organization_success_with_custom_id(self):
        """Test creating organization with custom ID."""
        org_name = 'Custom ID Organization'
        custom_id = 'org_custom_123'
        
        result = create_new_organization(DB, org_name, organization_id=custom_id)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], custom_id)
        self.assertEqual(result['name'], org_name)

    def test_create_new_organization_success_with_custom_subscription(self):
        """Test creating organization with custom subscription plan."""
        org_name = 'Pro Organization'
        custom_subscription = "pro"
        result = create_new_organization(DB, org_name, plan=custom_subscription)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['plan'], custom_subscription)

    def test_create_new_organization_duplicate_id(self):
        """Test creating organization with existing ID."""
        org_name = 'Duplicate Organization'
        existing_id = 'org_existing'
        
        result = create_new_organization(DB, org_name, organization_id=existing_id)
        
        self.assertIsNone(result)
        self.assertEqual(len(DB['organizations']), 1)  # Should not add duplicate

    def test_create_new_organization_empty_name(self):
        """Test creating organization with empty name."""
        org_name = ''
        
        result = create_new_organization(DB, org_name)
        
        # Should still work, just with empty name
        self.assertIsNotNone(result)
        self.assertEqual(result['name'], '')

    def test_create_new_organization_multiple_organizations(self):
        """Test creating multiple organizations."""
        org_names = ['Org 1', 'Org 2', 'Org 3']
        created_orgs = []
        
        for name in org_names:
            result = create_new_organization(DB, name)
            self.assertIsNotNone(result)
            created_orgs.append(result)
        
        self.assertEqual(len(DB['organizations']), 4)  # Original + 3 new
        
        # Verify all have unique IDs
        org_ids = [org['id'] for org in created_orgs]
        self.assertEqual(len(set(org_ids)), len(org_ids))

    def test_create_new_organization_empty_db_organizations(self):
        """Test creating organization when DB has no organizations section."""
        org_name = 'First Organization'
        DB.pop('organizations', None)  # Remove organizations section
        
        result = create_new_organization(DB, org_name)
        
        self.assertIsNotNone(result)
        self.assertIn('organizations', DB)
        self.assertEqual(len(DB['organizations']), 1)

    def test_create_new_organization_timestamp_format(self):
        """Test that created_at timestamp is in correct format."""
        org_name = 'Timestamp Test Organization'
        
        result = create_new_organization(DB, org_name)
        
        self.assertIsNotNone(result)
        created_at = result['created_at']
        self.assertIsInstance(created_at, str)
        self.assertTrue(created_at.endswith('+00:00'))  # Should end with +00:00 for UTC
        
        # Try to parse the timestamp
        try:
            datetime.fromisoformat(created_at)
        except ValueError:
            self.fail(f"Invalid timestamp format: {created_at}")

    @patch('supabase.SimulationEngine.utils.generate_unique_id')
    def test_create_new_organization_uses_generate_unique_id(self, mock_generate_id):
        """Test that create_new_organization uses generate_unique_id for ID generation."""
        mock_generate_id.return_value = 'org_mocked_123'
        org_name = 'Mocked ID Organization'
        
        result = create_new_organization(DB, org_name)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 'org_mocked_123')
        mock_generate_id.assert_called_once_with('org_')


class TestUtilityFunctionsIntegration(BaseTestCaseWithErrorHandler):
    """Integration tests for utility functions working together."""

    @classmethod
    def setUpClass(cls):
        """Set up test data before each test class."""
        cls._original_DB_state = copy.deepcopy(DB)

    def setUp(self):
        """Reset DB state before each test."""
        DB.clear()
        DB.update({
            "organizations": [],
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
        })

        # Add test organizations
        DB['organizations'].append({
            'id': 'org_123',
            'name': 'Test Organization',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'plan': 'free',
            'opt_in_tags': [],
            'allowed_release_channels': []
        })  
        

        # Add test projects
        DB['projects'].append({
            'id': 'proj_1a2b3c',
            'name': 'Test Project 1',
            'organization_id': 'org_123',
            'region': 'us-east-1',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'version': 'PostgreSQL 15'
        })

        DB['projects'].append({
            'id': 'proj_4d5e6f',
            'name': 'Test Project 2',
            'organization_id': 'org_123',
            'region': 'eu-west-1',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'version': 'PostgreSQL 14'
        })

        # Validate DB structure after setup
        self._validate_db_structure()

    def _validate_db_structure(self):
        """Validate that the DB structure conforms to SupabaseDB model."""
        try:
            # Use the actual SupabaseDB model for validation
            supabase_db = models.SupabaseDB(**DB)
            
        except Exception as e:
            raise AssertionError(f"DB structure validation failed using SupabaseDB model: {str(e)}")

    @classmethod
    def tearDownClass(cls):
        """Clean up after each test class."""
        DB.clear()
        DB.update(cls._original_DB_state)

    def test_create_org_and_add_project_costs(self):
        """Test creating an organization and then adding costs to its projects."""
        # Create organization
        org_result = create_new_organization(DB, 'Test Org')
        self.assertIsNotNone(org_result)
        org_id = org_result['id']
        
        # Add a project manually (since we're testing utils, not project creation)
        project = {
            'id': 'proj_test',
            'name': 'Test Project',
            'organization_id': org_id,
            'region': 'us-east-1',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'version': 'PostgreSQL 15'
        }
        DB['projects'].append(project)
        
        # Add cost information to the project
        cost_result = add_cost_information_to_project(
            DB, 'proj_test',
            amount=15.0,
            description='Test cost for new org project'
        )
        
        self.assertIsNotNone(cost_result)
        self.assertEqual(cost_result['amount'], 15.0)
        self.assertIn('Test cost for new org project', cost_result['description'])

    def test_multiple_organizations_with_costs(self):
        """Test creating multiple organizations and adding costs to their projects."""
        # Create multiple organizations
        org1 = create_new_organization(DB, 'Org 1', plan="pro")
        org2 = create_new_organization(DB, 'Org 2')
        
        self.assertIsNotNone(org1)
        self.assertIsNotNone(org2)
        
        # Add projects for each organization
        project1 = {
            'id': 'proj_1',
            'name': 'Project 1',
            'organization_id': org1['id'],
            'region': 'us-east-1',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'version': 'PostgreSQL 15'
        }
        project2 = {
            'id': 'proj_2',
            'name': 'Project 2',
            'organization_id': org2['id'],
            'region': 'eu-west-1',
            'status': 'ACTIVE_HEALTHY',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'version': 'PostgreSQL 14'
        }
        DB['projects'].extend([project1, project2])
        
        # Add costs to both projects
        cost1 = add_cost_information_to_project(DB, 'proj_1', amount=10.0)
        cost2 = add_cost_information_to_project(DB, 'proj_2', amount=20.0)
        
        self.assertIsNotNone(cost1)
        self.assertIsNotNone(cost2)
        self.assertEqual(len(DB['costs']), 2)
        self.assertNotEqual(cost1['confirmation_id'], cost2['confirmation_id'])


class TestCostParameterFunctions(BaseTestCaseWithErrorHandler):
    """Test cases for cost parameter utility functions."""

    @classmethod
    def setUpClass(cls):
        """Set up test data before each test class."""
        cls._original_DB_COST_DEFAULTS = copy.deepcopy(DB_COST_DEFAULTS)

    @classmethod
    def tearDownClass(cls):
        """Clean up after each test class."""
        DB_COST_DEFAULTS.clear()
        DB_COST_DEFAULTS.update(cls._original_DB_COST_DEFAULTS)

    def tearDown(self):
        """Reset DB_COST_DEFAULTS state after each test."""
        DB_COST_DEFAULTS.clear()
        DB_COST_DEFAULTS.update(self.__class__._original_DB_COST_DEFAULTS)
    
    def test_get_cost_parameter_existing(self):
        """Test retrieving an existing cost parameter."""
        self.assertEqual(get_cost_parameter('project_monthly'), 10.0)
        self.assertEqual(get_cost_parameter('default_currency'), 'USD')

    def test_get_cost_parameter_non_existing_with_default(self):
        """Test retrieving a non-existing cost parameter with a default value."""
        self.assertIsNone(get_cost_parameter('non_existing_param'))
        self.assertEqual(get_cost_parameter('non_existing_param', 50.0), 50.0)

    def test_update_cost_parameter_existing(self):
        """Test updating an existing cost parameter."""
        update_cost_parameter('project_monthly', 15.0)
        self.assertEqual(get_cost_parameter('project_monthly'), 15.0)

    def test_update_cost_parameter_new(self):
        """Test adding a new cost parameter."""
        update_cost_parameter('new_param', 'new_value')
        self.assertEqual(get_cost_parameter('new_param'), 'new_value')

    def test_update_cost_parameter_in_empty_costs(self):
        """Test updating cost parameter when 'costs' key is missing."""
        original_costs = DB_COST_DEFAULTS.pop('costs', None)
        self.assertTrue(update_cost_parameter('some_param', 123))
        self.assertEqual(get_cost_parameter('some_param'), 123)
        DB_COST_DEFAULTS['costs'] = original_costs


class TestNameToSlug(BaseTestCaseWithErrorHandler):
    """Test cases for the name_to_slug utility function."""

    def test_basic_slug(self):
        """Test basic slug conversion."""
        self.assertEqual(name_to_slug("Project Name"), "project-name")

    def test_slug_with_special_characters(self):
        """Test slug conversion with special characters."""
        self.assertEqual(name_to_slug("Project@Name#1!"), "project-name-1")

    def test_slug_with_multiple_spaces_and_hyphens(self):
        """Test slug conversion with multiple spaces and hyphens."""
        self.assertEqual(name_to_slug("Project  -- Name"), "project-name")

    def test_slug_with_leading_trailing_hyphens(self):
        """Test slug with leading/trailing characters that become hyphens."""
        self.assertEqual(name_to_slug("_Project Name_"), "project-name")

    def test_slug_empty_string(self):
        """Test slug conversion with an empty string."""
        self.assertEqual(name_to_slug(""), "")


class TestGetProjectsForOrganization(BaseTestCaseWithErrorHandler):
    """Test cases for get_projects_for_organization utility function."""

    def setUp(self):
        """Set up test data."""
        DB.clear()
        DB.update({
            "organizations": [
                {'id': 'org_1', 'name': 'Org 1'},
                {'id': 'org_2', 'name': 'Org 2'}
            ],
            "projects": [
                {'id': 'proj_1', 'organization_id': 'org_1'},
                {'id': 'proj_2', 'organization_id': 'org_1'},
                {'id': 'proj_3', 'organization_id': 'org_2'}
            ],
            "tables": {}, "extensions": {}, "migrations": {}, "edge_functions": {},
            "branches": {}, "costs": {}, "unconfirmed_costs": {}, "project_urls": {},
            "project_anon_keys": {}, "project_ts_types": {}, "logs": {}
        })

    def test_get_projects_for_organization_success(self):
        """Test retrieving projects for an organization that has projects."""
        projects = get_projects_for_organization(DB, 'org_1')
        self.assertEqual(len(projects), 2)
        project_ids = {p['id'] for p in projects}
        self.assertEqual(project_ids, {'proj_1', 'proj_2'})

    def test_get_projects_for_organization_single_project(self):
        """Test retrieving projects for an organization with a single project."""
        projects = get_projects_for_organization(DB, 'org_2')
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]['id'], 'proj_3')

    def test_get_projects_for_organization_no_projects(self):
        """Test retrieving projects for an organization with no projects."""
        DB['projects'] = [p for p in DB['projects'] if p['organization_id'] != 'org_1']
        projects = get_projects_for_organization(DB, 'org_1')
        self.assertEqual(len(projects), 0)

    def test_get_projects_for_organization_non_existent_org(self):
        """Test retrieving projects for a non-existent organization."""
        projects = get_projects_for_organization(DB, 'org_nonexistent')
        self.assertEqual(len(projects), 0)


class TestProjectStateFunctions(BaseTestCaseWithErrorHandler):
    """Test cases for utility functions related to project state."""

    def setUp(self):
        """Set up test data."""
        DB.clear()
        DB.update({
            "organizations": [
                {
                    'id': 'org_1', 'name': 'Org 1', 'plan': 'pro', 'opt_in_tags': [], 'allowed_release_channels': []    
                },
                {
                    'id': 'org_2', 'name': 'Org 2', 'plan': 'free', 'opt_in_tags': [], 'allowed_release_channels': []
                }
            ],
            "projects": [
                {
                    'id': 'proj_1', 'name': 'Project 1', 'organization_id': 'org_1',
                    'status': 'ACTIVE_HEALTHY', 'version': 'PostgreSQL 15'
                },
                {
                    'id': 'proj_2', 'name': 'Project 2', 'organization_id': 'org_2',
                    'status': 'INACTIVE_HEALTHY', 'version': None
                }
            ],
            "project_urls": {'proj_1': 'some_url'},
            "project_anon_keys": {'proj_1': 'some_key'},
            "tables": {}, "extensions": {}, "migrations": {}, "edge_functions": {},
            "branches": {}, "costs": {}, "unconfirmed_costs": {}, 
            "project_ts_types": {}, "logs": {}
        })

    def test_update_project_status_and_cascade_to_inactive(self):
        """Test updating project status to INACTIVE and cascading effects."""
        update_project_status_and_cascade(DB, 'proj_1', 'INACTIVE')
        project = get_entity_by_id_from_db(DB, 'projects', 'proj_1')
        self.assertEqual(project['status'], 'INACTIVE')
        self.assertNotIn('proj_1', DB['project_urls'])
        self.assertNotIn('proj_1', DB['project_anon_keys'])

    def test_update_project_status_and_cascade_to_active(self):
        """Test updating project status to ACTIVE_HEALTHY and cascading effects."""
        update_project_status_and_cascade(DB, 'proj_2', 'ACTIVE_HEALTHY')
        project = get_entity_by_id_from_db(DB, 'projects', 'proj_2')
        self.assertEqual(project['status'], 'ACTIVE_HEALTHY')
        self.assertIn('proj_2', DB['project_urls'])
        self.assertIn('proj_2', DB['project_anon_keys'])

    def test_is_branching_enabled_for_project_true(self):
        """Test if branching is enabled for a project in an org with the feature."""
        self.assertTrue(is_branching_enabled_for_project(DB, 'proj_1'))

    def test_is_branching_enabled_for_project_false(self):
        """Test if branching is disabled for a project in an org without the feature."""
        self.assertFalse(is_branching_enabled_for_project(DB, 'proj_2'))

    def test_get_project_postgres_version_explicit(self):
        """Test getting an explicit PostgreSQL version from a project."""
        self.assertEqual(get_project_postgres_version(DB, 'proj_1'), 'PostgreSQL 15')

    def test_get_project_postgres_version_default(self):
        """Test getting the default PostgreSQL version when not specified."""
        self.assertEqual(get_project_postgres_version(DB, 'proj_2'), 'PostgreSQL 14')


class TestBranchFunctions(BaseTestCaseWithErrorHandler):
    """Test cases for branch utility functions."""

    def setUp(self):
        DB.clear()
        DB.update({
            "branches": {
                "proj_1": [
                    {"id": "branch_1", "name": "main"},
                    {"id": "branch_2", "name": "dev"}
                ]
            },
            "organizations": [], "projects": [], "tables": {}, "extensions": {},
            "migrations": {}, "edge_functions": {}, "costs": {},
            "unconfirmed_costs": {}, "project_urls": {}, "project_anon_keys": {},
            "project_ts_types": {}, "logs": {}
        })
    
    def test_get_branch_by_id_from_db_found(self):
        """Test finding an existing branch by ID with get_branch_by_id_from_db."""
        branch = get_branch_by_id_from_db(DB, "branch_2")
        self.assertIsNotNone(branch)
        self.assertEqual(branch['name'], 'dev')

    def test_get_branch_by_id_from_db_not_found(self):
        """Test not finding a non-existent branch with get_branch_by_id_from_db."""
        self.assertIsNone(get_branch_by_id_from_db(DB, "branch_nonexistent"))

    def test_find_branch_in_db_found(self):
        """Test finding an existing branch by ID with find_branch_in_db."""
        branch = find_branch_in_db(DB, "branch_1")
        self.assertIsNotNone(branch)
        self.assertEqual(branch['name'], 'main')

    def test_find_branch_in_db_not_found(self):
        """Test not finding a non-existent branch with find_branch_in_db."""
        self.assertIsNone(find_branch_in_db(DB, "branch_nonexistent"))


if __name__ == '__main__':
    unittest.main() 